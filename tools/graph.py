"""Provenance graph: F -> run -> E; F -> raw; T <-> E (EVIDENCE.yaml); C -> T;
figure -> figure_data -> run (figure_manifest.csv); derived file -> generator (data_manifest.csv)."""
import csv, json, re, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
nodes, edges = set(), []


def link(a, b, kind):
    nodes.update([a, b]); edges.append({"from": a, "to": b, "kind": kind})


def rows(name):
    p = ROOT / name
    return list(csv.DictReader(p.open(newline="", encoding="utf-8"))) if p.exists() else []


body = re.sub(r"<!--.*?-->", "", (ROOT / "FINDINGS.md").read_text(encoding="utf-8"), flags=re.S)
for block in re.split(r"\n## ", body)[1:]:
    fid = block.split()[0]
    for e, r in re.findall(r"(E-\d+)/runs/(R-\d+)", block):
        link(fid, r, "supported_by"); link(r, e, "run_of")
    for h in re.findall(r"data/raw/([0-9a-f]{16})", block):
        link(fid, f"raw:{h}", "uses")
ev = yaml.safe_load((ROOT / "research/EVIDENCE.yaml").read_text(encoding="utf-8")) or {}
for l in ev.get("links") or []:
    link(l["theory"], l["experiment"], l.get("verdict", "tests"))
law = yaml.safe_load((ROOT / "writing/law.yaml").read_text(encoding="utf-8")) or {}
for c in law.get("concepts") or []:
    if c.get("source_theory"):
        link(c["id"], c["source_theory"], "derived_from")
for r in rows("figure_manifest.csv"):
    if r["data_file"] not in ("", "-"):
        link(r["figure"], r["data_file"], "plots")
        if r["source_run"] not in ("", "-"):
            link(r["data_file"], r["source_run"], "extracted_from")
for r in rows("data_manifest.csv"):
    if r.get("generated_by") not in (None, "", "-"):
        link(r["file"], r["generated_by"], "generated_by")
    for i in (r.get("inputs") or "").split(";"):
        if i.strip():
            link(r["file"], i.strip(), "input")
(ROOT / "graph.json").write_text(json.dumps({"nodes": sorted(nodes), "edges": edges}, indent=1), encoding="utf-8")
print(f"graph.json: {len(nodes)} nodes, {len(edges)} edges")
