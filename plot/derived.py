"""Readers of data/derived used only by the `extract` functions (never by `plot`)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DER = ROOT / "data" / "derived"
sys.path.insert(0, str(ROOT / "src"))


def summary():
    return json.loads((DER / "summary.json").read_text(encoding="utf-8"))


def path(tag):
    return json.loads((DER / "paths" / f"{tag}.json").read_text(encoding="utf-8"))


def states(tag):
    import numpy as np
    return np.load(DER / "paths" / f"{tag}_Xs.npy")
