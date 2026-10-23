"""All VFIFE restarts and the work-energy convergence check, as one pipeline step (single output file).
  python src/batch_vfife_checks.py      output: data/derived/vfife_checks.json
Steps are 1-based Newton step indices on the r_c = 10 A paths (near eps* for every structure; Piezo1 step 60 ends
exactly at the limit point)."""
import subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paths import DERIVED

RESTARTS = {"2oar": [6, 7], "4xdk": [9], "4wff": [7], "6mgv": [22, 44], "6pwn": [7, 14], "6b3r": [26, 59, 60], "6cq8": [13], "6vtk": [5]}

out = DERIVED / "vfife_checks.json"
out.unlink(missing_ok=True)
for name, steps in RESTARTS.items():
    subprocess.run([sys.executable, str(HERE / "vfife_check.py"), "vfife", name, "10", *map(str, steps)], check=True)
subprocess.run([sys.executable, str(HERE / "vfife_check.py"), "work", "2oar", "10", "3.0"], check=True)
