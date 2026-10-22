"""Every figure has a same-name description and vice versa; no unfilled {{key}} placeholders."""
from _util import ROOT, fail, read

figs = {p.stem for p in (ROOT / "results/figures").glob("*") if p.suffix in (".pdf", ".svg", ".png")}
descs = {p.stem for p in (ROOT / "results/descriptions").glob("*.md")}
errors = [f"{n}: figure without description" for n in sorted(figs - descs)]
errors += [f"{n}: description without figure" for n in sorted(descs - figs)]
for p in (ROOT / "results/descriptions").glob("*.md"):
    if "{{" in read(p):
        errors.append(f"{p.name}: unfilled number placeholder")
fail(errors, "figure and description pairs")
