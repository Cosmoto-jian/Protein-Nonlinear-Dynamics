"""Project entry point. Run from anywhere; paths resolve from this file.
  python run_all.py --fast   figure_data/ -> results/figures + results/descriptions
  python run_all.py --full   config/pipeline.yaml steps -> plot/extract -> --fast"""
import argparse, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sh(cmd: str):
    print(f"$ {cmd}", flush=True)
    r = subprocess.run(cmd, shell=True, cwd=ROOT)
    if r.returncode:
        sys.exit(f"step failed ({r.returncode}): {cmd}")


def fast():
    for p in sorted((ROOT / "plot").glob("fig*.py"), key=lambda p: int(p.stem[3:] or 0)):
        sh(f'"{sys.executable}" {p.relative_to(ROOT).as_posix()}')


def full(skip_expensive: bool):
    import yaml
    cfg = yaml.safe_load((ROOT / "config/pipeline.yaml").read_text(encoding="utf-8")) or {}
    for st in cfg.get("steps") or []:
        if skip_expensive and st.get("expensive"):
            print(f"skip expensive step {st['name']}")
            continue
        missing = [i for i in st.get("inputs") or [] if not (ROOT / i).exists()]
        if missing:
            sys.exit(f"step {st['name']}: missing inputs {missing}")
        sh(st["cmd"].replace("python ", f'"{sys.executable}" ', 1) if st["cmd"].startswith("python ") else st["cmd"])
        absent = [o for o in st.get("outputs") or [] if not (ROOT / o).exists()]
        if absent:
            sys.exit(f"step {st['name']}: outputs not produced {absent}")
    for p in sorted((ROOT / "plot/extract").glob("fig*.py")):
        sh(f'"{sys.executable}" {p.relative_to(ROOT).as_posix()}')
    fast()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--fast", action="store_true")
    g.add_argument("--full", action="store_true")
    ap.add_argument("--skip-expensive", action="store_true")
    a = ap.parse_args()
    full(a.skip_expensive) if a.full else fast()
