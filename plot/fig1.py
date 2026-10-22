"""Fig 1 - concept schematic. Content only; all style comes from style.theme."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import theme
from describe import describe


def main():
    fig, axes = theme.figure(1, 1, width="single", height_mm=60)
    ax = axes[0, 0]
    ax.text(0.5, 0.5, "<concept schematic>", ha="center", va="center", transform=ax.transAxes)
    ax.axis("off")
    theme.save(fig, "fig1")
    describe("fig1", "Fig. 1 concept schematic: <core mechanism of T-001>.", {}, ["research/theory/T-001/THEORY.md"])


if __name__ == "__main__":
    main()
