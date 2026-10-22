"""Provenance manifests:
- every file in data/derived and figure_data is listed in data_manifest.csv, with an existing generator
- every committed figure is listed in figure_manifest.csv; listed scripts and data files exist
- every figure_data CSV column is documented in its folder README.md
- plot/fig*.py read only figure_data (fast chain stays independent of runs and data)"""
import csv, re
from _util import ROOT, rel, read, fail

errors, notes = [], []


def table(name):
    p = ROOT / name
    if not p.exists():
        errors.append(f"{name}: missing")
        return []
    with p.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


dm = table("data_manifest.csv")
listed = {r["file"] for r in dm}
for r in dm:
    g = (r.get("generated_by") or "").split()[0] if r.get("generated_by") else ""
    if g and g != "-" and not (ROOT / g).exists():
        errors.append(f"data_manifest.csv: {r['file']}: generator {g} does not exist")
    if not (ROOT / r["file"]).exists():
        errors.append(f"data_manifest.csv: {r['file']} listed but missing")
for base in ("data/derived", "figure_data"):
    for p in (ROOT / base).rglob("*"):
        if p.is_file() and p.name not in ("README.md", ".gitkeep") and "_TEMPLATE" not in p.parts and "tmp" not in p.parts:
            if rel(p) not in listed:
                errors.append(f"{rel(p)}: not listed in data_manifest.csv")

fm = table("figure_manifest.csv")
figs_listed = {r["figure"] for r in fm}
for r in fm:
    if not (ROOT / r["script"]).exists():
        errors.append(f"figure_manifest.csv: {r['figure']}: script {r['script']} missing")
    if r["data_file"] not in ("", "-") and not (ROOT / r["data_file"]).exists():
        errors.append(f"figure_manifest.csv: {r['figure']}: data file {r['data_file']} missing")
    if r["data_file"] not in ("", "-") and not r["data_file"].startswith("figure_data/"):
        errors.append(f"figure_manifest.csv: {r['figure']}: plotting data must live in figure_data/")
for p in (ROOT / "results/figures").glob("*"):
    if p.suffix in (".pdf", ".svg", ".png") and p.stem not in figs_listed:
        errors.append(f"results/figures/{p.name}: not listed in figure_manifest.csv")

for d in (ROOT / "figure_data").iterdir():
    if not d.is_dir() or d.name == "_TEMPLATE":
        continue
    csvs = list(d.glob("*.csv"))
    readme = d / "README.md"
    if csvs and not readme.exists():
        errors.append(f"{rel(d)}: missing README.md documenting columns")
        continue
    doc = read(readme) if readme.exists() else ""
    for c in csvs:
        if c.name not in doc:
            errors.append(f"{rel(c)}: not described in {rel(readme)}")
        with c.open(newline="", encoding="utf-8") as fh:
            header = next(csv.reader(fh), [])
        for col in header:
            if not re.search(rf"\|\s*`?{re.escape(col)}`?\s*\|", doc):
                errors.append(f"{rel(c)}: column '{col}' not documented in {rel(readme)}")

for p in (ROOT / "plot").glob("fig*.py"):
    for i, line in enumerate(read(p).splitlines(), 1):
        if re.search(r"runs/|data/raw|data/derived", line) and not line.lstrip().startswith("#") and '"""' not in line:
            errors.append(f"{rel(p)}:{i}: figure scripts read only figure_data/ (use plot/extract/)")
fail(errors, "provenance manifests", notes)
