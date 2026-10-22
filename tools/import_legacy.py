"""Stage 0-1 of a legacy import (docs/REPRODUCIBILITY_STANDARD.md). READ ONLY on the source.
  python tools/import_legacy.py <legacy_dir> [--name NAME]
Writes reports/import/<NAME>/inventory.csv, migration_map_draft.csv and baseline_report.md.
Nothing is moved, copied or deleted; the owner reviews the draft map before migration."""
import argparse, csv, hashlib, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CJK = re.compile("[\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff00-\uffef]")
ABS = re.compile(r"(?<![\w.])(/(home|Users|mnt|data\d*|root|scratch|work)/[^\s'\"]+|[A-Za-z]:\\[^\s'\"]+)")
IO = re.compile(r"""(?:open|read_csv|read_excel|loadtxt|genfromtxt|np\.load|np\.save|savetxt|to_csv|savefig|torch\.load|pickle\.load)\(\s*[rf]?['"]([^'"]+)['"]""")
CODE = {".py", ".sh", ".ipynb", ".m", ".r", ".R", ".jl", ".c", ".cpp", ".f90"}
CONF = {".yaml", ".yml", ".json", ".toml", ".ini", ".cfg"}
DATA = {".csv", ".tsv", ".xlsx", ".xls", ".npy", ".npz", ".h5", ".hdf5", ".pdb", ".cif", ".dcd", ".xtc", ".mat", ".pkl", ".parquet", ".txt", ".dat"}
FIG = {".png", ".pdf", ".svg", ".tif", ".tiff", ".eps", ".jpg"}
CACHE = {".pyc", ".log", ".tmp", ".bak", ".swp"}
def esc(x) -> str:
    """Keep reports CJK-free (language rule): non-ASCII is written as \\uXXXX escapes."""
    return str(x).encode("ascii", "backslashreplace").decode("ascii")


TARGET = {"code": "src/", "config": "config/", "raw": "data/raw/", "processed": "data/derived/",
          "figure": "results/figures/", "doc": "docs/legacy/", "cache": "(exclude)", "unknown": "(review)"}


def role(p: Path) -> str:
    s, parts = p.suffix.lower(), {x.lower() for x in p.parts}
    if s in CACHE or "__pycache__" in parts or ".ipynb_checkpoints" in parts:
        return "cache"
    if s in CODE: return "code"
    if s in CONF: return "config"
    if s in FIG: return "figure"
    if s in (".md", ".rst", ".docx", ".tex"): return "doc"
    if s in DATA:
        return "raw" if parts & {"raw", "raw_data", "original", "source", "input", "inputs"} else "processed"
    return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--name")
    a = ap.parse_args()
    src = Path(a.src).resolve()
    name = a.name or src.name
    out = ROOT / "reports/import" / name
    out.mkdir(parents=True, exist_ok=True)
    seen, inv, mm = {}, [], []
    for p in sorted(src.rglob("*")):
        if p.is_dir() and not p.is_symlink():
            continue
        relp = p.relative_to(src).as_posix()
        if p.is_symlink():
            inv.append(dict(path=relp, size="", sha256="", role="symlink", has_cjk=bool(CJK.search(relp)),
                            abs_paths="", reads_writes="", duplicate_of="", note=f"-> {p.resolve()}"))
            continue
        b = p.read_bytes()
        h = hashlib.sha256(b).hexdigest()
        r = role(p)
        text = b.decode("utf-8", "ignore") if p.suffix.lower() in CODE | CONF | {".md", ".txt", ".csv", ".tsv"} else ""
        io = sorted(set(IO.findall(text)))[:20] if r == "code" else []
        absp = sorted(set(m[0] for m in ABS.findall(text)))[:10]
        inv.append(dict(path=relp, size=len(b), sha256=h, role=r, has_cjk=bool(CJK.search(relp) or CJK.search(text)),
                        abs_paths=";".join(absp), reads_writes=";".join(io), duplicate_of=seen.get(h, ""),
                        note="binary not parsed" if not text and r not in ("figure", "cache") else ""))
        seen.setdefault(h, relp)
        new = TARGET[r]
        cjk_name = bool(CJK.search(p.name))
        if r == "raw":
            new += f"{h[:16]}__{'file' + p.suffix if cjk_name else p.name}"
        elif not new.startswith("("):
            new += relp
        action = "exclude-candidate" if r == "cache" else ("duplicate-candidate" if inv[-1]["duplicate_of"] else "review")
        reason = f"role guess: {r}" + ("; CJK name: rename, keep original_name in MANIFEST or EXCEPTIONS" if cjk_name else "")
        mm.append(dict(old_path=relp, new_path=new, action=action, reason=reason, sha256=h))
    cols = ["path", "size", "sha256", "role", "has_cjk", "abs_paths", "reads_writes", "duplicate_of", "note"]
    with (out / "inventory.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows({k: esc(v) for k, v in i.items()} for i in inv)
    with (out / "migration_map_draft.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["old_path", "new_path", "action", "reason", "sha256"]); w.writeheader(); w.writerows({k: esc(v) for k, v in m.items()} for m in mm)
    n = lambda k: sum(1 for i in inv if i["role"] == k)
    (out / "baseline_report.md").write_text("\n".join([
        f"# Baseline report: {esc(name)}", "",
        f"- Files: {len(inv)} (code {n('code')}, raw {n('raw')}, processed {n('processed')}, figures {n('figure')}, unknown {n('unknown')}, cache {n('cache')})",
        f"- Files with CJK: {sum(1 for i in inv if i['has_cjk'])}",
        f"- Files with absolute paths: {sum(1 for i in inv if i['abs_paths'])}",
        f"- Duplicates by hash: {sum(1 for i in inv if i['duplicate_of'])}",
        f"- Symlinks: {n('symlink')}", "",
        "## To fill before migration",
        "- Original run commands and whether they succeeded (if not run: BASELINE MISSING)",
        "- Python and external program versions",
        "- Reference outputs (figures, key numbers) and their hashes",
        "- Unknown files and conflicts needing an owner decision", ""]), encoding="utf-8")
    print(f"inventory written to {out.relative_to(ROOT)} ({len(inv)} files); source untouched")


if __name__ == "__main__":
    main()
