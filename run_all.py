"""Pipeline engine. Every formal output is a step in pipeline.yaml.
  python run_all.py            run stale steps, then write pipeline.lock, manifests and graph.json
  python run_all.py --all      run every step
  python run_all.py --fast     run only fast steps (figure_data -> figures)
  python run_all.py --cheap    skip expensive steps
  python run_all.py --status   list stale steps (add --json for tools)
  python run_all.py --derive   only regenerate manifests and graph.json"""
import argparse, csv, hashlib, io, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCK = ROOT / "pipeline.lock"


def load():
    import yaml
    steps = (yaml.safe_load((ROOT / "pipeline.yaml").read_text(encoding="utf-8")) or {}).get("steps") or []
    for s in steps:
        s["outs"] = [o if isinstance(o, dict) else {"path": o} for o in s.get("outs") or []]
        s["deps"] = s.get("deps") or []
    return steps


def digest(rel: str):
    p = ROOT / rel
    if p.is_file():
        return hashlib.sha256(p.read_bytes()).hexdigest()
    if p.is_dir():
        h = hashlib.sha256()
        for q in sorted(x for x in p.rglob("*") if x.is_file() and "__pycache__" not in x.parts):
            h.update(q.relative_to(p).as_posix().encode() + b"\0" + hashlib.sha256(q.read_bytes()).digest())
        return h.hexdigest()
    return None


def read_lock():
    return json.loads(LOCK.read_text(encoding="utf-8") or "{}") if LOCK.exists() else {}


def producer(steps):
    return {o["path"]: s["name"] for s in steps for o in s["outs"]}


def stale(steps, lock):
    """A step is stale if it never ran, its cmd/params/dep hashes changed, an output is missing,
    or a step it depends on is stale."""
    prod, out, bad = producer(steps), {}, set()
    for s in steps:
        e, why = lock.get(s["name"]), []
        if not e:
            why.append("never run")
        else:
            if e.get("cmd") != s["cmd"] or e.get("params") != s.get("params"):
                why.append("cmd or params changed")
            why += [f"dep changed: {d}" for d in s["deps"] if e.get("deps", {}).get(d) != digest(d)]
        why += [f"output missing: {o['path']}" for o in s["outs"] if digest(o["path"]) is None]
        why += [f"upstream stale: {prod[d]}" for d in s["deps"] if prod.get(d) in bad]
        if why:
            bad.add(s["name"]); out[s["name"]] = why
    return out


def run(cmd):
    if cmd.startswith("python "):
        cmd = f'"{sys.executable}" ' + cmd[7:]
    print(f"$ {cmd}", flush=True)
    r = subprocess.run(cmd, shell=True, cwd=ROOT)
    if r.returncode:
        sys.exit(f"step failed ({r.returncode}): {cmd}")


def manifests(steps):
    """data_manifest.csv and figure_manifest.csv text, derived from pipeline.yaml and data/raw/MANIFEST.yaml."""
    import yaml
    prod = {o["path"]: s for s in steps for o in s["outs"]}
    d = io.StringIO(); w = csv.writer(d, lineterminator="\n")
    w.writerow(["file", "role", "generated_by", "inputs", "params", "units", "purpose"])
    raw = yaml.safe_load((ROOT / "data/raw/MANIFEST.yaml").read_text(encoding="utf-8")) or {}
    for e in raw.get("files") or []:
        w.writerow([f"data/raw/{e['file']}", "raw", "-", e.get("source", ""), "-", e.get("units", ""), e.get("purpose", "")])
    for s in steps:
        for o in s["outs"]:
            p = o["path"]
            if p.startswith("results/"):
                continue
            role = "figure_data" if p.startswith("figure_data/") else "run" if "/runs/" in p else "derived"
            w.writerow([p, role, s["cmd"], ";".join(s["deps"]), json.dumps(s.get("params") or {}, sort_keys=True),
                        o.get("units", ""), o.get("purpose", "")])
    fm = io.StringIO(); w = csv.writer(fm, lineterminator="\n")
    w.writerow(["figure", "data_files", "source_runs", "script", "command", "output"])
    for s in steps:
        if not s.get("figure"):
            continue
        data = [x for x in s["deps"] if x.startswith("figure_data/")]
        runs = sorted({y for x in data if x in prod for y in prod[x]["deps"] if "/runs/" in y})
        script = next((x for x in s["deps"] if x.endswith(".py") and x != "plot/style.py"), "-")
        w.writerow([s["figure"], ";".join(data) or "-", ";".join(runs) or "-", script, s["cmd"], f"results/figures/{s['figure']}"])
    return d.getvalue(), fm.getvalue()


def graph(steps):
    import yaml
    nodes, edges = set(), []
    def link(a, b, kind):
        nodes.update([a, b]); edges.append({"from": a, "to": b, "kind": kind})
    for s in steps:
        for d in s["deps"]:
            link(d, s["name"], "input")
        for o in s["outs"]:
            link(s["name"], o["path"], "output")
    led = yaml.safe_load((ROOT / "research/claims.yaml").read_text(encoding="utf-8")) or {}
    for c in led.get("entries") or []:
        for k in ("theory", "experiment"):
            if c.get(k):
                link(c["id"], c[k], k)
        if c.get("run"):
            link(c["id"], f"research/experiment/{c['run']}", c.get("status", "cites"))
    return {"nodes": sorted(nodes), "edges": edges}


def derive(steps):
    dm, fm = manifests(steps)
    (ROOT / "data_manifest.csv").write_text(dm, encoding="utf-8")
    (ROOT / "figure_manifest.csv").write_text(fm, encoding="utf-8")
    (ROOT / "graph.json").write_text(json.dumps(graph(steps), indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    for a in ("all", "fast", "status", "derive"):
        g.add_argument(f"--{a}", action="store_true")
    ap.add_argument("--cheap", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    steps, lock = load(), read_lock()
    names = [s["name"] for s in steps]
    if len(set(names)) != len(names):
        sys.exit("pipeline.yaml: duplicate step names")
    seen = set()
    for s in steps:
        later = [d for d in s["deps"] if producer(steps).get(d) and producer(steps)[d] not in seen and producer(steps)[d] != s["name"]]
        if later:
            sys.exit(f"step {s['name']}: depends on outputs of later steps {later}; reorder pipeline.yaml")
        seen.add(s["name"])
    if a.status:
        st = stale(steps, lock)
        print(json.dumps(st, indent=1) if a.json else ("\n".join(f"STALE {k}: {'; '.join(v)}" for k, v in st.items()) or "all steps up to date"))
        return
    if not a.derive:
        todo = stale(steps, lock)
        for s in steps:
            if a.fast and not s.get("fast"):
                continue
            if a.cheap and s.get("expensive"):
                print(f"skip expensive step {s['name']}"); continue
            if not (a.all or a.fast) and s["name"] not in stale(steps, lock):
                continue
            missing = [d for d in s["deps"] if digest(d) is None]
            if missing:
                sys.exit(f"step {s['name']}: missing inputs {missing}")
            run(s["cmd"])
            absent = [o["path"] for o in s["outs"] if digest(o["path"]) is None]
            if absent:
                sys.exit(f"step {s['name']}: outputs not produced {absent}")
            lock[s["name"]] = {"cmd": s["cmd"], "params": s.get("params"),
                               "deps": {d: digest(d) for d in s["deps"]},
                               "outs": {o["path"]: digest(o["path"]) for o in s["outs"]}}
            LOCK.write_text(json.dumps(lock, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        lock = {k: v for k, v in lock.items() if k in names}
        LOCK.write_text(json.dumps(lock, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    derive(steps)
    left = stale(steps, read_lock())
    print("pipeline up to date" if not left else f"{len(left)} step(s) still stale: {sorted(left)}")


if __name__ == "__main__":
    main()
