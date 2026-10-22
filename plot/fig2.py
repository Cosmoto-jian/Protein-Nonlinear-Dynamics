"""Fig 2 - data figure. Reads ONLY figure_data/fig2/ (fast chain); never runs or data/."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import theme
from describe import describe, read_csv, ROOT

DATA = "figure_data/fig2/panel_a.csv"


def main():
    if not (ROOT / DATA).exists():
        print("fig2: no plotting data yet, skipped")
        return
    rows = read_csv(DATA)
    fig, axes = theme.figure(1, 2, height_mm=60)
    # ... plot rows ...
    theme.label_panels(axes); theme.top_legend(fig, axes)
    theme.save(fig, "fig2")
    describe("fig2", "<template; write numbers as {{key}}>", {}, [DATA])


if __name__ == "__main__":
    main()
