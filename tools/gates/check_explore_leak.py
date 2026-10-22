"""Exploration results are never evidence: FINDINGS, EVIDENCE, extraction, figure data, figures,
descriptions and the paper must not reference explore/ or nodes N-xxx."""
import re
from _util import ROOT, fail, read

PAT = re.compile(r"explore/|\bN-\d+")
targets = [ROOT / "FINDINGS.md", ROOT / "research/EVIDENCE.yaml", ROOT / "figure_manifest.csv"]
targets += list((ROOT / "plot").glob("fig*.py")) + list((ROOT / "plot/extract").glob("fig*.py"))
targets += list((ROOT / "writing/tex").rglob("*.tex")) + list((ROOT / "results/descriptions").glob("*.md"))
targets += [p for p in (ROOT / "figure_data").rglob("*") if p.is_file() and "_TEMPLATE" not in p.parts]
errors = []
for p in targets:
    if not p.exists():
        continue
    for i, line in enumerate(read(p).splitlines(), 1):
        if line.lstrip().startswith(("#", "%", "<!--")):
            continue
        if PAT.search(line):
            errors.append(f"{p.relative_to(ROOT)}:{i} references exploration results: {line.strip()[:80]}")
fail(errors, "exploration results kept out of evidence")
