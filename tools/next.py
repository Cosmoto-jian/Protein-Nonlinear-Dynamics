"""The loop scheduler: reads the repository and prints the single most useful next task.
  python tools/next.py            the next task (markdown)
  python tools/next.py --all      every pending task in priority order
  python tools/next.py --json     machine-readable
Priority: stale pipeline > red gates > open issues > novelty > experiment design > lock > run >
audit > judge > figure/text > reflect. Tasks waiting on the owner (needs-user) are skipped."""
import json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def y(p):
    import yaml
    p = ROOT / p
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}


def front(p):
    import yaml
    m = re.match(r"---\n(.*?)\n---", p.read_text(encoding="utf-8"), re.S)
    return (yaml.safe_load(m.group(1)) if m else {}) or {}


def task(tid, role, do, done_when, files=()):
    return {"id": tid, "role": role, "do": do, "done_when": done_when, "files": list(files)}


def tasks():
    out = []
    import run_all
    st = run_all.stale(run_all.load(), run_all.read_lock())
    # 1 stale pipeline (rebuilding also clears lock and manifest mismatches)
    if st:
        out.append(task("rebuild", "engineer", "Rebuild stale steps with `make all`: " + ", ".join(sorted(st)),
                        "`python run_all.py --status` reports all steps up to date and gates pass", ["pipeline.lock"]))
    # 2 red gates
    r = subprocess.run([sys.executable, str(ROOT / "tools/gates.py")], cwd=ROOT, capture_output=True, text=True)
    for block in ([] if st else re.findall(r"FAIL (\w+)\n((?:   - .*\n?)+)", r.stdout)):
        out.append(task(f"gate-{block[0]}", "engineer", f"Fix the red gate `{block[0]}`:\n{block[1].rstrip()}",
                        f"`python tools/gates.py {block[0]}` passes"))
    # 3 open issues (when the GitHub CLI is available)
    if shutil.which("gh"):
        q = subprocess.run(["gh", "issue", "list", "--state", "open", "--json", "number,title,labels", "--limit", "50"],
                           cwd=ROOT, capture_output=True, text=True)
        try:
            for i in json.loads(q.stdout or "[]"):
                labels = {l["name"] for l in i["labels"]}
                if not labels & {"needs-user", "loop"}:
                    out.append(task(f"I-{i['number']:03d}", "by label", f"Resolve issue #{i['number']}: {i['title']}",
                                    "failing check added first, then green; PR closes the issue"))
        except Exception:
            pass
    ledger = y("research/claims.yaml").get("entries") or []
    judged_runs = {c.get("run") for c in ledger}
    tested = {(c.get("theory"), c.get("prediction")) for c in ledger if c.get("status") != "dead-end"}
    # 4-6 theories -> novelty -> experiment design -> lock
    for th in sorted((ROOT / "research/theory").glob("T-*")):
        t = th.name
        nov = th / "NOVELTY.md"
        meta = front(nov) if nov.exists() else {}
        if meta.get("verdict", "pending") == "pending":
            out.append(task(f"{t}-novelty", "opponent (different model)", f"Adversarial novelty check of {t}: find the 5 closest prior works and argue it is not new.",
                            "NOVELTY.md verdict is novel, incremental or prior-art", [f"research/theory/{t}/NOVELTY.md"]))
            continue
        if meta.get("verdict") == "prior-art":
            continue
        preds = re.findall(r"^\|\s*(P-\d+)\s*\|.*\|\s*(E-\d+)\s*\|\s*$", (th / "THEORY.md").read_text(encoding="utf-8"), re.M)
        for p, e in preds:
            if (t, p) in tested:
                continue
            ed = ROOT / "research/experiment" / e
            pre = y(f"research/experiment/{e}/PREREG.yaml") if ed.exists() else {}
            if not ed.exists():
                out.append(task(f"{e}-create", "experiment", f"Create {e} to test {t} {p}: `python tools/new.py {e}`, then run the exploration tree on dev data.",
                                "explore/explore.yaml has nodes and a selected node", [f"research/experiment/{e}/"]))
            elif not pre.get("locked"):
                sel = y(f"research/experiment/{e}/explore/explore.yaml").get("selected")
                if not sel:
                    out.append(task(f"{e}-explore", "experiment", f"Continue the exploration tree of {e} until one node is selected.",
                                    "explore.yaml `selected` is set with a reason"))
                else:
                    out.append(task(f"{e}-lock", "experiment", f"Write and lock PREREG for {e} from node {sel}: holdout data or seeds, support/refute criteria, tolerance, explore_nodes_tried. Add the run step to pipeline.yaml.",
                                    "PREREG.yaml committed with locked: true; gates pass"))
            else:
                runs = [r for r in (ed / "runs").glob("R-*")] if (ed / "runs").exists() else []
                if not runs:
                    out.append(task(f"{e}-run", "experiment", f"Run the pre-registered experiment {e} through its pipeline step (`make all`).",
                                    f"research/experiment/{e}/runs/R-xxxx exists and is in pipeline.lock"))
    # 7-8 audit and judge
    for run in sorted((ROOT / "research/experiment").glob("E-*/runs/R-*")):
        rid, key = run.name, f"{run.parent.parent.name}/runs/{run.name}"
        rep = ROOT / "audit/reports" / f"{rid}.md"
        if not rep.exists():
            out.append(task(f"{rid}-audit", "auditor (different model)", f"Audit {key} with the AGENTS.md checklist.",
                            f"audit/reports/{rid}.md ends with a Verdict line", [f"audit/reports/{rid}.md"]))
        elif key not in judged_runs:
            v = re.search(r"(?i)verdict:\s*`?([\w-]+)", rep.read_text(encoding="utf-8"))
            v = v.group(1).lower() if v else "missing"
            if v == "pass":
                out.append(task(f"{rid}-judge", "judge", f"Judge {key} against its PREREG criteria and append one entry to research/claims.yaml.",
                                "a new claims.yaml entry cites this run", ["research/claims.yaml"]))
            else:
                out.append(task(f"{rid}-fix", "experiment", f"Audit verdict for {key} is `{v}`: fix the implementation or redesign (new run id, never overwrite).",
                                "a new run passes audit"))
    # 9 figures and text for supported results
    tex = " ".join(p.read_text(encoding="utf-8") for p in (ROOT / "writing/tex").rglob("*.tex"))
    for c in ledger:
        if c.get("status") in ("supported", "refuted") and c.get("id") not in tex:
            out.append(task(f"{c['id']}-write", "plotting + writing", f"Bring {c['id']} into a figure and the paper (cite `% {c['id']}` beside the sentence).",
                            f"{c['id']} appears in writing/tex and its figure step is in pipeline.yaml"))
    # 10 reflect
    if not out:
        study = y("STUDY.yaml")
        n = int((study.get("loop") or {}).get("reflect_after_dead_ends", 3))
        recent = [c.get("status") for c in ledger][-n:]
        why = "the last results were dead-ends or refutations" if recent and all(s in ("dead-end", "refuted") for s in recent) else "nothing is pending"
        out.append(task("reflect", "theory", f"Reflect ({why}): compare claims.yaml with each aim's done_when in STUDY.yaml. If an aim is met, propose the paper outline; otherwise propose one new theory T-xxx with falsifiable predictions, grounded in refuted and dead-end entries.",
                        "a new THEORY.md, or a `needs-user` issue proposing to stop or change aims"))
    return out


if __name__ == "__main__":
    ts = tasks()
    if "--json" in sys.argv:
        print(json.dumps(ts if "--all" in sys.argv else ts[:1], indent=1))
    else:
        for t in (ts if "--all" in sys.argv else ts[:1]):
            print(f"## next: {t['id']}  (role: {t['role']})\n\n{t['do']}\n\n**Done when:** {t['done_when']}\n")
            if t["files"]:
                print("Files: " + ", ".join(f"`{x}`" for x in t["files"]) + "\n")
        if "--all" not in sys.argv and len(ts) > 1:
            print(f"({len(ts) - 1} more pending; `python tools/next.py --all`)")
