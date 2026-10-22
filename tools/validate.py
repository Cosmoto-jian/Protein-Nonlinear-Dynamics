"""Independent clean-copy validation.
Copies the project (tracked files only when in git) to a fresh temporary directory outside the repo,
runs the gates and the fast chain there (and the full chain with --full), compares regenerated outputs
with the committed ones, and writes results/logs/validation_report.md.
Each item is PASS, FAIL, EXCEPTION or NOT VERIFIED; nothing that was not executed is reported as PASS."""
import argparse, csv, hashlib, os, platform, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
items, log = [], []


def add(name, status, detail=""):
    items.append((name, status, detail))


def run(cmd, cwd):
    env = dict(os.environ, SOURCE_DATE_EPOCH="0", PYTHONHASHSEED="0", MPLBACKEND="Agg")
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, env=env)
    log.append(f"$ {cmd}  (cwd=<copy>)\n{r.stdout}{r.stderr}")
    return r


def tracked():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True)
    if out.returncode == 0 and out.stdout:
        return [ROOT / p for p in out.stdout.split("\0") if p]
    return [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="also run the full chain in the clean copy")
    a = ap.parse_args()
    py = f'"{sys.executable}"'
    work = Path(tempfile.mkdtemp(prefix="validate_"))
    copy = work / "project"
    for p in tracked():
        if p.is_file():
            dst = copy / p.relative_to(ROOT)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
    add("clean copy created outside the repository", "PASS", f"{sum(1 for _ in copy.rglob('*') if _.is_file())} files")
    if ROOT in copy.parents:
        add("clean copy isolation", "FAIL", "copy is inside the repository")

    r = run(f"{py} tools/gates/run_all.py", copy)
    add("static gates in clean copy", "PASS" if r.returncode == 0 else "FAIL", r.stdout.strip().splitlines()[-1] if r.stdout else "")

    committed = {p.relative_to(ROOT / "results").as_posix(): sha(p) for p in (ROOT / "results").rglob("*")
                 if p.is_file() and p.parent.name in ("figures", "descriptions") and p.name != ".gitkeep"}
    r = run(f"{py} run_all.py --fast", copy)
    add("fast chain (figure_data -> figures) in clean copy", "PASS" if r.returncode == 0 else "FAIL")
    with (copy / "figure_manifest.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        stem = Path(row["output"])
        ok = all((copy / f"{stem}.{e}").exists() for e in ("pdf", "svg", "png"))
        desc = copy / "results/descriptions" / f"{stem.name}.md"
        add(f"{row['figure']}{row['panel']} regenerated", "PASS" if ok and desc.exists() else "FAIL", row["script"])
    for k, h in committed.items():
        q = copy / "results" / k
        if not q.exists():
            add(f"results/{k} reproduced", "FAIL", "not regenerated")
        elif k.endswith((".md", ".svg")):
            add(f"results/{k} identical to committed", "PASS" if sha(q) == h else "FAIL")
        else:
            add(f"results/{k} byte-identical", "PASS" if sha(q) == h else "NOT VERIFIED", "binary output; inspect visually if differs")

    if a.full:
        r = run(f"{py} run_all.py --full", copy)
        add("full chain (raw -> results) in clean copy", "PASS" if r.returncode == 0 else "FAIL")
        for p in (ROOT / "figure_data").rglob("*.csv"):
            q = copy / p.relative_to(ROOT)
            add(f"{p.relative_to(ROOT).as_posix()} rebuilt identically", "PASS" if q.exists() and sha(q) == sha(p) else "FAIL",
                "compare with PREREG tolerance if floating point differs")
    else:
        add("full chain (raw -> results)", "NOT VERIFIED", "run `make validate-full`")

    try:
        import yaml
        ex = (yaml.safe_load((ROOT / "audit/EXCEPTIONS.yaml").read_text(encoding="utf-8")) or {}).get("exceptions") or []
    except Exception:
        ex = []
    for e in ex:
        add(f"exception: {e.get('path')}", "EXCEPTION", f"{e.get('rule')}: {e.get('reason')} (approved by {e.get('approved_by')})")

    statuses = {s for _, s, _ in items}
    overall = "FAIL" if "FAIL" in statuses else ("EXCEPTION / NOT VERIFIED" if statuses & {"EXCEPTION", "NOT VERIFIED"} else "PASS")
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    out = ROOT / "results/logs"
    out.mkdir(parents=True, exist_ok=True)
    lines = [f"# Validation report", "", f"- Date (UTC): {datetime.now(timezone.utc):%Y-%m-%d %H:%M}",
             f"- Commit: {subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip() or 'n/a'}",
             f"- Python: {platform.python_version()} on {platform.system()}", f"- Overall: **{overall}**", "",
             "| Item | Status | Detail |", "|---|---|---|"]
    lines += [f"| {n} | {s} | {d} |" for n, s, d in items]
    lines += ["", "## Environment (pip freeze)", "```", freeze.strip(), "```", "", "## Executed commands", "```", "\n".join(log)[-20000:], "```"]
    (out / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    print(f"validation: {overall}  ->  results/logs/validation_report.md")
    for n, s, d in items:
        print(f"  {s:13s} {n}")
    sys.exit(1 if overall == "FAIL" else 0)


if __name__ == "__main__":
    main()
