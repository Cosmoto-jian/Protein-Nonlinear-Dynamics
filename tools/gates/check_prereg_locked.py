"""A locked PREREG.yaml never changes; experiments with runs must be locked and declare a holdout."""
from _util import ROOT, changed, git, base_ref, fail, load_yaml

errors = []
ref = base_ref()
for status, path in changed("M"):
    if path.endswith("PREREG.yaml") and "_TEMPLATE" not in path:
        if "locked: true" in git("show", f"{ref}:{path}"):
            errors.append(f"{path}: locked pre-registration was modified")
for exp in (ROOT / "research/experiment").glob("E-*"):
    runs = [r for r in (exp / "runs").glob("*") if r.name != ".gitkeep"] if (exp / "runs").exists() else []
    pre = exp / "PREREG.yaml"
    if runs and (not pre.exists() or not load_yaml(pre).get("locked")):
        errors.append(f"{exp.name}: has runs but PREREG is missing or unlocked")
    if pre.exists():
        y = load_yaml(pre)
        if y.get("locked") and not ((y.get("holdout") or {}).get("data_sha256") or (y.get("holdout") or {}).get("seeds")):
            errors.append(f"{exp.name}: pre-registration declares no holdout data or seeds")
fail(errors, "pre-registration locked")
