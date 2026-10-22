"""Portability: no machine-specific absolute paths or os.chdir in code/config, no symlinks leaving
the repo, no committed secrets. Patterns are assembled so this file does not match itself."""
import re
from _util import ROOT, files, rel, is_text, read, fail, CODE_EXT

S = "/"
ABS = re.compile("|".join([
    S + "home" + S, S + "Users" + S, S + "workspace" + S, S + "mnt" + S, S + "root" + S,
    S + "data" + "1" + S, r"\b[A-Za-z]:" + r"\\\\", r"~" + S]))
SECRET = re.compile("|".join([
    "gh" + "p_[A-Za-z0-9]{30,}", "github" + "_pat_[A-Za-z0-9_]{20,}", "s" + "k-[A-Za-z0-9_-]{20,}",
    "AK" + "IA[0-9A-Z]{16}", "xox" + "[bpas]-[A-Za-z0-9-]{10,}", "-----BEGIN [A-Z ]*PRIVATE " + "KEY-----"]))
CHDIR = re.compile(r"\bos\." + r"chdir\(")
errors = []
for p in files():
    r = rel(p)
    if p.is_symlink():
        target = p.resolve()
        if ROOT not in target.parents and target != ROOT:
            errors.append(f"{r}: symlink points outside the repository")
        continue
    if not is_text(p):
        continue
    text = read(p)
    for i, line in enumerate(text.splitlines(), 1):
        if SECRET.search(line):
            errors.append(f"{r}:{i}: looks like a secret")
        if p.suffix in CODE_EXT or p.name == "Makefile":
            if ABS.search(line):
                errors.append(f"{r}:{i}: machine-specific absolute path: {line.strip()[:80]}")
            if p.suffix == ".py" and CHDIR.search(line):
                errors.append(f"{r}:{i}: os.chdir breaks root-relative execution")
fail(errors, "portability")
