"""All VFIFE restarts and the work-energy convergence check, as one pipeline step (single output file).
  python src/batch_vfife_checks.py                output: data/derived/vfife_checks.json (serial)
  python src/batch_vfife_checks.py --part NAME:K  one restart  -> data/derived/vfife_checks/NAME_K.json
  python src/batch_vfife_checks.py --part work    work-energy check -> data/derived/vfife_checks/work.json
  python src/batch_vfife_checks.py --merge        parts -> data/derived/vfife_checks.json (same format and order as serial)
Steps are 1-based Newton step indices on the r_c = 10 A paths (near eps* for every structure; Piezo1 step 60 ends
exactly at the limit point)."""
import json, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paths import DERIVED

RESTARTS = {"2oar": [6, 7], "4xdk": [9], "4wff": [7], "6mgv": [22, 44], "6pwn": [7, 14], "6b3r": [26, 59, 60], "6cq8": [13], "6vtk": [5]}
WORK = ["2oar", "10", "3.0"]

out = DERIVED / "vfife_checks.json"; PARTS = DERIVED / "vfife_checks"
a = sys.argv[1:]
if a[:1] == ["--part"]:
    PARTS.mkdir(parents=True, exist_ok=True)
    if a[1] == "work":
        f = PARTS / "work.json"; f.unlink(missing_ok=True)
        subprocess.run([sys.executable, str(HERE / "vfife_check.py"), "work", *WORK], check=True, env=dict(os.environ, VFIFE_OUT=str(f)))
    else:
        name, k = a[1].split(":"); f = PARTS / f"{name}_{k}.json"; f.unlink(missing_ok=True)
        subprocess.run([sys.executable, str(HERE / "vfife_check.py"), "vfife", name, "10", k], check=True, env=dict(os.environ, VFIFE_OUT=str(f)))
elif a[:1] == ["--merge"]:
    res = {}
    for name, steps in RESTARTS.items():
        key = f"vfife_{name}_rc10"
        res[key] = [json.load(open(PARTS / f"{name}_{k}.json"))[key][0] for k in steps]
    res["work_2oar_rc10"] = json.load(open(PARTS / "work.json"))["work_2oar_rc10"]
    json.dump(res, open(out, "w"), indent=1, default=float)
    print("merged", list(res))
else:
    out.unlink(missing_ok=True)
    for name, steps in RESTARTS.items():
        subprocess.run([sys.executable, str(HERE / "vfife_check.py"), "vfife", name, "10", *map(str, steps)], check=True)
    subprocess.run([sys.executable, str(HERE / "vfife_check.py"), "work", *WORK], check=True)
