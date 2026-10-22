"""Fig 1 - concept schematic (no data).
  python plot/fig1.py plot"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import style


def plot():
    fig, axes = style.figure(1, 1, width="single", height_mm=60)
    ax = axes[0, 0]
    ax.text(0.5, 0.5, "<concept schematic>", ha="center", va="center", transform=ax.transAxes)
    ax.axis("off")
    style.save(fig, "fig1")
    style.describe("fig1", "Fig. 1 concept schematic: <core mechanism of T-001>.", {}, ["research/theory/T-001/THEORY.md"])


if __name__ == "__main__":
    {"plot": plot}[sys.argv[1]]()
