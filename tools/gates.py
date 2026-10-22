"""The 5 gates. `python tools/gates.py` runs all; `python tools/gates.py data evidence` runs some.
  data       raw add-only + hash names; derived / figure_data / runs only from pipeline steps, matching pipeline.lock;
             manifests equal what run_all.py derives
  prereg     locked PREREG unchanged; runs need a locked PREREG with holdout
  evidence   claims.yaml append-only and traceable to pass audits; exploration never evidence; adversarial novelty
  figures    fast steps read only figure_data/ and plot/; figure-description pairs; CSV columns documented
  hygiene    language isolation; portability (absolute paths, symlinks, secrets, os.chdir)"""
import csv, hashlib, importlib.util, os, re, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"}
TEXT_EXT = {".py", ".sh", ".yaml", ".yml", ".json", ".toml", ".cfg", ".ini", ".txt", ".md", ".csv",
            ".tsv", ".lock", ".tex", ".bib", ".ipynb", ".r", ".R", ".m", ".jl", ".c", ".cpp", ".h", ".js", ".ts"}
CODE_EXT = TEXT_EXT - {".md", ".txt", ".csv", ".tsv", ".bib"}


def git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except Exception:
        return ""


def base_ref() -> str:
    """PR target branch; locally compare with origin/main; skip history checks if absent."""
    b = os.environ.get("GITHUB_BASE_REF")
    for ref in ([f"origin/{b}"] if b else []) + ["origin/main"]:
        if git("rev-parse", "--verify", ref).strip():
            return ref
    return ""


def changed(status_filter="ACMRD") -> list[tuple[str, str]]:
    ref = base_ref()
    if not ref:
        return []
    out = git("diff", "--name-status", f"--diff-filter={status_filter}", f"{ref}...HEAD")
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        rows.append((parts[0][0], parts[-1]))
    return rows


def files():
    """Every file in the project (tracked or not), excluding ignored tool directories."""
    for dirpath, dirnames, filenames in os.walk(ROOT, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield Path(dirpath) / name
        for d in dirnames:
            p = Path(dirpath) / d
            if p.is_symlink():
                yield p


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def is_text(p: Path) -> bool:
    return p.suffix in TEXT_EXT or p.name in ("Makefile", "CODEOWNERS", ".gitignore", "Dockerfile")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def report(errors, name, notes=()):
    for n in notes:
        print(f"  note: {n}")
    if errors:
        print(f"FAIL {name}")
        for e in errors:
            print("   -", e)
        return False
    print(f"PASS {name}")
    return True


def load_yaml(p):
    import yaml
    p = Path(p)
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}


def exceptions(rule: str) -> set[str]:
    ex = load_yaml(ROOT / "audit/EXCEPTIONS.yaml").get("exceptions") or []
    return {e.get("path") for e in ex if e.get("rule") == rule}

spec = importlib.util.spec_from_file_location("pipe", ROOT / "run_all.py")
pipe = importlib.util.module_from_spec(spec); spec.loader.exec_module(pipe)
RAW_META = ("MANIFEST.yaml", "README.md", ".gitkeep")
IGNORE = ("README.md", ".gitkeep")


def ledger(text=None):
    import yaml
    t = text if text is not None else read(ROOT / "research/claims.yaml")
    return (yaml.safe_load(t) or {}).get("entries") or []


# ---------------------------------------------------------------- 1 data
def gate_data():
    errors = []
    for status, path in changed():
        if path.startswith("data/raw/") and Path(path).name not in RAW_META and status in "MDR":
            errors.append(f"{path}: raw data modified or deleted ({status})")
    manifest = {e["file"] for e in (load_yaml(ROOT / "data/raw/MANIFEST.yaml").get("files") or [])}
    for p in (ROOT / "data/raw").iterdir():
        if p.name in RAW_META:
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if not p.name.startswith(h[:16] + "__"):
            errors.append(f"data/raw/{p.name}: name prefix is not content sha256[:16] ({h[:16]})")
        if p.name not in manifest:
            errors.append(f"data/raw/{p.name}: not registered in data/raw/MANIFEST.yaml")
    steps, lock = pipe.load(), pipe.read_lock()
    outs = {o["path"] for s in steps for o in s["outs"]}
    covered = lambda r: any(r == o or r.startswith(o.rstrip("/") + "/") for o in outs)
    for base in ("data/derived", "figure_data"):
        for p in (ROOT / base).rglob("*"):
            if p.is_file() and p.name not in IGNORE and "tmp" not in p.parts and not covered(rel(p)):
                errors.append(f"{rel(p)}: not produced by any pipeline.yaml step")
    for p in (ROOT / "research/experiment").glob("E-*/runs/*"):
        if p.name != ".gitkeep" and not covered(rel(p)):
            errors.append(f"{rel(p)}: formal run not produced by a pipeline.yaml step")
    for s in steps:
        e = lock.get(s["name"])
        for o in s["outs"]:
            if o["path"].startswith("results/") or not e:
                continue
            if pipe.digest(o["path"]) not in (None, e.get("outs", {}).get(o["path"])):
                errors.append(f"{o['path']}: differs from pipeline.lock (edited by hand, or run `make all`)")
    dm, fm = pipe.manifests(steps)
    for name, text in (("data_manifest.csv", dm), ("figure_manifest.csv", fm)):
        if not (ROOT / name).exists() or read(ROOT / name) != text:
            errors.append(f"{name}: out of date with pipeline.yaml (run `python run_all.py --derive`)")
    notes = [f"stale steps: {sorted(pipe.stale(steps, lock))}"] if pipe.stale(steps, lock) else []
    return report(errors, "data", notes)


# ---------------------------------------------------------------- 2 prereg
def gate_prereg():
    errors, ref = [], base_ref()
    for status, path in changed("M"):
        if path.endswith("PREREG.yaml") and "_TEMPLATE" not in path and "locked: true" in git("show", f"{ref}:{path}"):
            errors.append(f"{path}: locked pre-registration was modified")
    for exp in (ROOT / "research/experiment").glob("E-*"):
        runs = [r for r in (exp / "runs").glob("*") if r.name != ".gitkeep"] if (exp / "runs").exists() else []
        y = load_yaml(exp / "PREREG.yaml")
        if runs and not y.get("locked"):
            errors.append(f"{exp.name}: has runs but PREREG is missing or unlocked")
        h = y.get("holdout") or {}
        if y.get("locked") and not (h.get("data_sha256") or h.get("seeds")):
            errors.append(f"{exp.name}: locked PREREG declares no holdout data or seeds")
    return report(errors, "prereg")


# ---------------------------------------------------------------- 3 evidence
def front(p: Path):
    import yaml
    t = read(p)
    m = re.match(r"---\n(.*?)\n---", t, re.S)
    return (yaml.safe_load(m.group(1)) if m else {}) or {}, t


def check_novelty(p: Path, errors):
    meta, text = front(p)
    v = meta.get("verdict", "pending")
    if v not in ("novel", "incremental"):
        errors.append(f"{rel(p)}: verdict={v}, cannot enter pre-registration or text")
    if meta.get("proposer_model") and meta.get("proposer_model") == meta.get("opponent_model"):
        errors.append(f"{rel(p)}: opponent must be a different model")
    table = text.split("5 closest prior works")[-1].split("## Judge")[0]
    rows = [r for r in table.splitlines() if re.match(r"\|\s*\d", r) and len([c for c in r.split("|") if c.strip()]) >= 4]
    if len(rows) < 5:
        errors.append(f"{rel(p)}: only {len(rows)}/5 closest works filled")
    return meta


LEAK = re.compile(r"explore/|\bN-\d+")


def gate_evidence():
    errors, ref = [], base_ref()
    try:
        now = ledger()
    except Exception as e:
        return report([f"research/claims.yaml: invalid YAML ({e})"], "evidence")
    if ref:
        old = git("show", f"{ref}:research/claims.yaml")
        if old:
            prev = ledger(old)
            if now[:len(prev)] != prev:
                errors.append("research/claims.yaml: existing entries changed or removed (append-only)")
    ids = [c.get("id") for c in now]
    if len(set(ids)) != len(ids):
        errors.append("research/claims.yaml: duplicate ids")
    for c in now:
        cid, st = c.get("id"), c.get("status")
        if st not in ("supported", "refuted", "inconclusive", "dead-end"):
            errors.append(f"{cid}: unknown status {st}")
            continue
        if st == "dead-end":
            continue
        if any(LEAK.search(str(v)) for v in c.values()):
            errors.append(f"{cid}: cites exploration results")
        m = re.fullmatch(r"(E-\d+)/runs/(R-\d+)", str(c.get("run", "")))
        if not m:
            errors.append(f"{cid}: needs run: E-xxx/runs/R-xxxx")
            continue
        if not (ROOT / "research/experiment" / c["run"]).exists():
            errors.append(f"{cid}: run {c['run']} does not exist")
        rep = ROOT / "audit/reports" / f"{m.group(2)}.md"
        if not rep.exists() or not re.search(r"(?i)verdict:\s*`?pass`?", read(rep)):
            errors.append(f"{cid}: {m.group(2)} has no pass audit report")
    targets = [ROOT / "figure_manifest.csv", ROOT / "pipeline.yaml"]
    targets += list((ROOT / "writing/tex").rglob("*.tex")) + list((ROOT / "results/descriptions").glob("*.md"))
    targets += [p for p in (ROOT / "figure_data").rglob("*") if p.is_file()]
    for p in targets:
        if p.exists():
            for i, line in enumerate(read(p).splitlines(), 1):
                if not line.lstrip().startswith(("#", "%", "<!--")) and LEAK.search(line):
                    errors.append(f"{rel(p)}:{i} references exploration results")
    metas = {}
    for exp in (ROOT / "research/experiment").glob("E-*"):
        y = load_yaml(exp / "PREREG.yaml")
        if y.get("locked"):
            for t in y.get("tests") or []:
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
    if not (metas and all(m.get("verdict") == "novel" and m.get("user_checked") for m in metas.values())):
        for p in (ROOT / "writing/tex").rglob("*.tex"):
            for i, line in enumerate(read(p).splitlines(), 1):
                if line.lstrip().startswith("%"):
                    continue
                for w in law.get("banned_words_if_not_novel") or []:
                    if re.search(rf"(?i)(?<![a-z]){re.escape(w)}(?![a-z])", line):
                        errors.append(f"{rel(p)}:{i} wording '{w}' needs verdict novel + owner check")
    return report(errors, "evidence")


# ---------------------------------------------------------------- 4 figures
def gate_figures():
    errors = []
    for s in pipe.load():
        if s.get("fast"):
            bad = [d for d in s["deps"] if not d.startswith(("figure_data/", "plot/"))]
            if bad:
                errors.append(f"step {s['name']}: fast steps read only figure_data/ and plot/, not {bad}")
        if any(o["path"].startswith("results/figures/") for o in s["outs"]):
            if not s.get("figure"):
                errors.append(f"step {s['name']}: writes a figure but has no `figure:` id")
            elif f"results/descriptions/{s['figure']}.md" not in {o["path"] for o in s["outs"]}:
                errors.append(f"step {s['name']}: must also output results/descriptions/{s['figure']}.md")
    figs = {p.stem for p in (ROOT / "results/figures").glob("*") if p.suffix in (".pdf", ".svg", ".png")}
    descs = {p.stem for p in (ROOT / "results/descriptions").glob("*.md")}
    errors += [f"{n}: figure without description" for n in sorted(figs - descs)]
    errors += [f"{n}: description without figure" for n in sorted(descs - figs)]
    for p in (ROOT / "results/descriptions").glob("*.md"):
        if "{{" in read(p):
            errors.append(f"{p.name}: unfilled number placeholder")
    for d in (ROOT / "figure_data").iterdir():
        csvs = list(d.glob("*.csv")) if d.is_dir() else []
        if not csvs:
            continue
        doc = read(d / "README.md") if (d / "README.md").exists() else ""
        if not doc:
            errors.append(f"{rel(d)}: missing README.md documenting columns")
        for c in csvs:
            with c.open(newline="", encoding="utf-8") as fh:
                header = next(csv.reader(fh), [])
            for col in header:
                if not re.search(rf"\|\s*`?{re.escape(col)}`?\s*\|", doc):
                    errors.append(f"{rel(c)}: column '{col}' not documented in {rel(d)}/README.md")
    return report(errors, "figures")


# ---------------------------------------------------------------- 5 hygiene
CJK = re.compile("[\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")
S = "/"
ABS = re.compile("|".join([
    S + "home" + S, S + "Users" + S, S + "workspace" + S, S + "mnt" + S, S + "root" + S,
    S + "data" + "1" + S, r"\b[A-Za-z]:" + r"\\\\", r"~" + S]))
SECRET = re.compile("|".join([
    "gh" + "p_[A-Za-z0-9]{30,}", "github" + "_pat_[A-Za-z0-9_]{20,}", "s" + "k-[A-Za-z0-9_-]{20,}",
    "AK" + "IA[0-9A-Z]{16}", "xox" + "[bpas]-[A-Za-z0-9-]{10,}", "-----BEGIN [A-Z ]*PRIVATE " + "KEY-----"]))
CHDIR = re.compile(r"\bos\." + r"chdir\(")


def gate_hygiene():
    allowed = exceptions("language")
    errors, notes, unparsed = [], [], []
    for p in files():
        r = rel(p)
        if CJK.search(r):
            errors.append(f"{r}: CJK characters in path"); continue
        if p.is_symlink():
            if ROOT not in p.resolve().parents:
                errors.append(f"{r}: symlink points outside the repository")
            continue
        if p.is_dir():
            continue
        hit = False
        if is_text(p):
            text = read(p)
            hit = bool(CJK.search(text))
            for i, line in enumerate(text.splitlines(), 1):
                if SECRET.search(line):
                    errors.append(f"{r}:{i}: looks like a secret")
                if p.suffix in CODE_EXT or p.name == "Makefile":
                    if ABS.search(line):
                        errors.append(f"{r}:{i}: machine-specific absolute path")
                    if p.suffix == ".py" and CHDIR.search(line):
                        errors.append(f"{r}:{i}: os.chdir breaks root-relative execution")
        elif p.suffix == ".xlsx":
            with zipfile.ZipFile(p) as z:
                hit = any(CJK.search(z.read(n).decode("utf-8", "replace")) for n in z.namelist() if n.endswith(".xml"))
        elif p.stat().st_size and p.suffix not in (".png", ".pdf", ".svg", ".gz", ".zip", ".npy", ".npz", ".pt", ".h5"):
            unparsed.append(r)
        if r.endswith("_cn.md"):
            if not p.with_name(p.name[:-6] + ".md").exists():
                errors.append(f"{r}: missing English twin")
            continue
        if hit:
            (notes.append(f"{r}: CJK allowed by approved EXCEPTION") if r in allowed
             else errors.append(f"{r}: CJK characters outside a *_cn.md file"))
    if unparsed:
        notes.append(f"{len(unparsed)} binary files not parsed for language (NOT VERIFIED): {unparsed[:5]}")
    return report(errors, "hygiene", notes)


GATES = {"data": gate_data, "prereg": gate_prereg, "evidence": gate_evidence, "figures": gate_figures, "hygiene": gate_hygiene}

if __name__ == "__main__":
    pick = [a for a in sys.argv[1:] if a in GATES] or list(GATES)
    ok = [GATES[g]() for g in pick]
    print(f"\n{sum(ok)}/{len(ok)} gates passed")
    sys.exit(0 if all(ok) else 1)
