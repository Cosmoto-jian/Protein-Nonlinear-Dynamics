"""data/raw is add-only; file name prefix must equal content sha256[:16]; every file registered."""
import hashlib
from _util import ROOT, changed, fail, load_yaml

errors = []
for status, path in changed():
    if path.startswith("data/raw/") and path not in ("data/raw/MANIFEST.yaml", "data/raw/README.md"):
        if status in "MDR":
            errors.append(f"{path}: raw data modified or deleted ({status})")
manifest = {e["file"] for e in (load_yaml(ROOT / "data/raw/MANIFEST.yaml").get("files") or [])}
for p in (ROOT / "data/raw").iterdir():
    if p.name in ("MANIFEST.yaml", "README.md", ".gitkeep"):
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if not p.name.startswith(h[:16] + "__"):
        errors.append(f"{p.name}: name prefix is not content sha256[:16] ({h[:16]})")
    if p.name not in manifest:
        errors.append(f"{p.name}: not registered in MANIFEST.yaml")
fail(errors, "raw data immutable")
