"""python tools/new_experiment.py E-001  |  python tools/new_experiment.py T-001 --theory"""
import shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
name, theory = sys.argv[1], "--theory" in sys.argv
kind = "theory" if theory else "experiment"
dst = ROOT / "research" / kind / name
shutil.copytree(ROOT / "research" / kind / "_TEMPLATE", dst)
for p in dst.rglob("*"):
    if p.is_file() and p.suffix in (".md", ".yaml"):
        p.write_text(p.read_text(encoding="utf-8").replace("T-xxx" if theory else "E-xxx", name), encoding="utf-8")
print("created", dst.relative_to(ROOT))
