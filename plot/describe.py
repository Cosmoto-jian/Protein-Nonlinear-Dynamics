"""Paired figure descriptions: {{key}} placeholders are filled from data, numbers are never typed."""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def describe(name: str, template: str, values: dict, sources: list[str]):
    missing = set(re.findall(r"{{(\w+)}}", template)) - set(values)
    if missing:
        raise KeyError(f"{name}: description lacks values {missing}")
    text = re.sub(r"{{(\w+)}}", lambda m: str(values[m.group(1)]), template)
    out = ROOT / "results/descriptions"
    out.mkdir(parents=True, exist_ok=True)
    src = "\n".join(f"- {s}" for s in sources)
    (out / f"{name}.md").write_text(f"# {name}\n\n{text}\n\n## Data sources\n{src}\n", encoding="utf-8")


def read_csv(rel: str) -> list[dict]:
    with (ROOT / rel).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))
