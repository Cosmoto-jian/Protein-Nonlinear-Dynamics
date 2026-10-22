"""Language isolation:
- no CJK characters in any file or directory name
- no CJK in any text file except *_cn.md; each X_cn.md needs a CJK-free twin X.md
- .xlsx cells, sheet names and comments are scanned too
- raw files may only break the rule when listed in audit/EXCEPTIONS.yaml (rule: language)"""
import re, zipfile
from _util import ROOT, files, rel, is_text, read, fail, exceptions

CJK = re.compile("[\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")
allowed = exceptions("language")
errors, notes, unparsed = [], [], []
for p in files():
    r = rel(p)
    if CJK.search(r):
        errors.append(f"{r}: CJK characters in path")
        continue
    if p.is_symlink() or p.is_dir():
        continue
    hit = False
    if is_text(p):
        hit = bool(CJK.search(read(p)))
    elif p.suffix == ".xlsx":
        with zipfile.ZipFile(p) as z:
            hit = any(CJK.search(z.read(n).decode("utf-8", "replace")) for n in z.namelist() if n.endswith(".xml"))
    elif p.stat().st_size and p.suffix not in (".png", ".pdf", ".svg", ".gz", ".zip", ".npy", ".npz", ".pt", ".h5"):
        unparsed.append(r)
    if r.endswith("_cn.md"):
        twin = p.with_name(p.name[:-6] + ".md")
        if not twin.exists():
            errors.append(f"{r}: missing English twin {rel(twin)}")
        continue
    if hit:
        if r in allowed:
            notes.append(f"{r}: CJK allowed by approved EXCEPTION")
        else:
            errors.append(f"{r}: CJK characters outside a *_cn.md file")
if unparsed:
    notes.append(f"{len(unparsed)} binary files not parsed for language (NOT VERIFIED): {unparsed[:5]}")
fail(errors, "language isolation", notes)
