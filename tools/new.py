"""Create a theory or experiment from its template.
  python tools/new.py T-001      research/theory/T-001
  python tools/new.py E-001      research/experiment/E-001"""
import shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
name = sys.argv[1]
kind = {"T": "theory", "E": "experiment"}[name[0]]
dst = ROOT / "research" / kind / name
if dst.exists():
    sys.exit(f"{dst.relative_to(ROOT)} already exists")
shutil.copytree(ROOT / "research" / kind / "_TEMPLATE", dst)
for p in dst.rglob("*"):
    if p.is_file() and p.suffix in (".md", ".yaml"):
        p.write_text(p.read_text(encoding="utf-8").replace(f"{name[0]}-xxx", name), encoding="utf-8")
print("created", dst.relative_to(ROOT).as_posix())
