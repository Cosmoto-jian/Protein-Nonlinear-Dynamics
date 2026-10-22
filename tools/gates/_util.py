import os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"}
TEXT_EXT = {".py", ".sh", ".yaml", ".yml", ".json", ".toml", ".cfg", ".ini", ".txt", ".md", ".csv",
            ".tsv", ".tex", ".bib", ".ipynb", ".r", ".R", ".m", ".jl", ".c", ".cpp", ".h", ".js", ".ts"}
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


def fail(errors, name, notes=()):
    for n in notes:
        print(f"  note: {n}")
    if errors:
        print(f"FAIL {name}")
        for e in errors:
            print("   -", e)
        sys.exit(1)
    print(f"PASS {name}")


def load_yaml(p):
    import yaml
    p = Path(p)
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}


def exceptions(rule: str) -> set[str]:
    ex = load_yaml(ROOT / "audit/EXCEPTIONS.yaml").get("exceptions") or []
    return {e.get("path") for e in ex if e.get("rule") == rule}
