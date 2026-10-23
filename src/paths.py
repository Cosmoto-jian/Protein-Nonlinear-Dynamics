"""Project-root-relative locations and the raw-data lookup (data/raw/MANIFEST.yaml)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"
TEX_GEN = ROOT / "writing" / "tex" / "gen"


def _manifest():
    import yaml
    return {e["original_name"]: e["file"] for e in (yaml.safe_load((RAW / "MANIFEST.yaml").read_text(encoding="utf-8")) or {}).get("files") or []}


def raw(original_name: str, required: bool = True):
    """Path of a raw file registered under `original_name`; None if absent and not required."""
    m = _manifest()
    if original_name not in m:
        if required:
            raise FileNotFoundError(f"{original_name} is not registered in data/raw/MANIFEST.yaml")
        return None
    return str(RAW / m[original_name])
