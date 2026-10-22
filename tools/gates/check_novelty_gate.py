"""Adversarial novelty gate:
- a theory in any locked PREREG needs NOVELTY verdict novel/incremental
- 5 closest prior works; proposer and opponent are different models
- every concept in law.yaml points to a valid NOVELTY and has all definition fields
- without novel + owner check, novelty wording is banned in the paper"""
import re
from pathlib import Path
from _util import ROOT, fail, load_yaml, read


def front(p: Path):
    import yaml
    t = read(p)
    m = re.match(r"---\n(.*?)\n---", t, re.S)
    return (yaml.safe_load(m.group(1)) if m else {}) or {}, t


def check_novelty(p: Path, errors):
    meta, text = front(p)
    v = meta.get("verdict", "pending")
    if v not in ("novel", "incremental"):
        errors.append(f"{p.relative_to(ROOT)}: verdict={v}, cannot enter pre-registration or text")
    if meta.get("proposer_model") and meta.get("proposer_model") == meta.get("opponent_model"):
        errors.append(f"{p.relative_to(ROOT)}: opponent must be a different model")
    table = text.split("5 closest prior works")[-1].split("## Judge")[0]
    rows = [r for r in table.splitlines() if re.match(r"\|\s*\d", r) and len([c for c in r.split("|") if c.strip()]) >= 4]
    if len(rows) < 5:
        errors.append(f"{p.relative_to(ROOT)}: only {len(rows)}/5 closest works filled")
    return meta


errors, metas = [], {}
for exp in (ROOT / "research/experiment").glob("E-*"):
    pre = exp / "PREREG.yaml"
    if pre.exists() and load_yaml(pre).get("locked"):
        for t in load_yaml(pre).get("tests") or []:
            nov = ROOT / "research/theory" / t / "NOVELTY.md"
            if not nov.exists():
                errors.append(f"{exp.name} tests {t}, but {t} has no NOVELTY.md")
            else:
                metas[t] = check_novelty(nov, errors)
law = load_yaml(ROOT / "writing/law.yaml")
for c in law.get("concepts") or []:
    nov = ROOT / str(c.get("novelty", ""))
    if not c.get("novelty") or not nov.is_file():
        errors.append(f"concept {c.get('id')}: missing novelty record")
    else:
        metas[c.get("id")] = check_novelty(nov, errors)
    for k in ("formal_definition", "operational_definition", "code", "source_theory", "evidence", "first_use"):
        if not c.get(k):
            errors.append(f"concept {c.get('id')}: missing {k}")

may_claim = metas and all(m.get("verdict") == "novel" and m.get("user_checked") for m in metas.values())
if not may_claim:
    for p in (ROOT / "writing/tex").rglob("*.tex"):
        for i, line in enumerate(read(p).splitlines(), 1):
            if line.lstrip().startswith("%"):
                continue
            for w in law.get("banned_words_if_not_novel") or []:
                if re.search(rf"(?i)(?<![a-z]){re.escape(w)}(?![a-z])", line):
                    errors.append(f"{p.relative_to(ROOT)}:{i} wording '{w}' needs verdict novel + owner check")
fail(errors, "adversarial novelty")
