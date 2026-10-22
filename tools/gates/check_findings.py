"""FINDINGS and DEAD_ENDS are append-only; every finding cites a run under runs/ with a pass audit."""
import re
from _util import ROOT, git, base_ref, fail, read

def entries(text: str) -> list[str]:
    """The judged entries (## blocks outside comments); headers and templates may be edited."""
    body = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return [b.strip() for b in re.split(r"\n## ", "\n" + body)[1:]]


errors = []
ref = base_ref()
for name in ("FINDINGS.md", "DEAD_ENDS.md"):
    if ref:
        old = git("show", f"{ref}:{name}")
        if old and entries(read(ROOT / name))[:len(entries(old))] != entries(old):
            errors.append(f"{name}: existing entries changed or removed (append-only)")
body = re.sub(r"<!--.*?-->", "", read(ROOT / "FINDINGS.md"), flags=re.S)
for block in re.split(r"\n## ", body)[1:]:
    fid = block.split()[0]
    runs = re.findall(r"(E-\d+)/runs/(R-\d+)", block)
    if not runs:
        errors.append(f"{fid}: cites no run under runs/")
    for e, r in runs:
        rep = ROOT / "audit/reports" / f"{r}.md"
        if not rep.exists() or not re.search(r"(?i)verdict:\s*`?pass`?", read(rep)):
            errors.append(f"{fid}: {r} has no pass audit report")
fail(errors, "findings traceable")
