"""Extract plotting data for Fig 3: research/experiment/E-xxx/runs/R-xxxx -> figure_data/fig3/*.csv.
The only place where a figure touches run outputs. Also update figure_data/fig3/README.md,
data_manifest.csv and figure_manifest.csv when columns change."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = None   # e.g. "research/experiment/E-001/runs/R-0001/metrics.json"
OUT = ROOT / "figure_data/fig3"


def main():
    if RUN is None:
        print("extract fig3: no run bound, skipped")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []   # build rows from ROOT / RUN
    with (OUT / "panel_a.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["x", "y", "y_err"])
        w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
