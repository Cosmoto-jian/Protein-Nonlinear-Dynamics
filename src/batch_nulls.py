"""Null models for the six channels as one pipeline step (single output file).
  python src/batch_nulls.py      output: data/derived/nulls.json
Rewired-network paths for Piezo1 are the slow part (about 20 min)."""
import subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paths import DERIVED

out = DERIVED / "nulls.json"
out.unlink(missing_ok=True)
subprocess.run([sys.executable, str(HERE / "nulls.py"), "2oar", "4xdk", "4wff", "6mgv", "6pwn"], check=True)
subprocess.run([sys.executable, str(HERE / "nulls.py"), "6b3r", "--with-piezo-rewire"], check=True)
