"""Fig N - data figure. Copy to plot/figN.py and add two steps to pipeline.yaml:
  figN-data: python plot/figN.py extract   deps: [plot/figN.py, <run dir>]          outs: [figure_data/figN]
  figN:      python plot/figN.py plot      deps: [plot/figN.py, plot/style.py, figure_data/figN]  fast: true
extract() is the only code that reads a run; plot() reads only figure_data/."""
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import style

NAME = Path(__file__).stem
RUN = "research/experiment/E-001/runs/R-0001"
DATA = style.ROOT / "figure_data" / NAME


def extract():
    metrics = json.loads((style.ROOT / RUN / "metrics.json").read_text(encoding="utf-8"))
    DATA.mkdir(parents=True, exist_ok=True)
    rows = [{"x": i, "y": v, "y_err": 0.0} for i, v in enumerate(metrics.get("values", []))]
    with (DATA / "panel_a.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["x", "y", "y_err"], lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    (DATA / "README.md").write_text(
        f"# {NAME} plotting data\n\nSource run: {RUN}\n\n## panel_a.csv\n"
        "| Column | Meaning | Unit | Kind |\n|---|---|---|---|\n"
        "| x | <meaning> | - | value |\n| y | <meaning> | <unit> | value |\n| y_err | <meaning> | <unit> | error bar (SD) |\n",
        encoding="utf-8")


def plot():
    rows = style.read_csv(f"figure_data/{NAME}/panel_a.csv")
    fig, axes = style.figure(1, 1, width="single", height_mm=60)
    ax = axes[0, 0]
    ax.errorbar([float(r["x"]) for r in rows], [float(r["y"]) for r in rows],
                yerr=[float(r["y_err"]) for r in rows], color=style.color("<object>"), label="<object>")
    style.label_panels(axes); style.top_legend(fig, axes)
    style.save(fig, NAME)
    style.describe(NAME, "<template with {{n}} points>", {"n": len(rows)}, [f"figure_data/{NAME}/panel_a.csv"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
