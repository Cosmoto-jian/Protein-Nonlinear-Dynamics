"""Global plotting theme: every figure script takes fonts, sizes, colours and widths from here."""
from pathlib import Path
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
MM = 1 / 25.4
WIDTH = {"single": 89 * MM, "double": 183 * MM}          # Nature column widths
SIZE = {"label": 16, "axis": 14, "tick": 9, "note": 9, "legend": 8.4}
PALETTE = {
    "navy": "#3C5488", "teal": "#00A087", "vermilion": "#E64B35",
    "plum": "#8E5EA2", "sky": "#4DBBD5", "brown": "#7E6148",
}
_PAL_FILE = Path(__file__).with_name("palette.yaml")


def _load_palette():
    out = {}
    if _PAL_FILE.exists():
        for line in _PAL_FILE.read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip().strip('"')] = v.strip().strip('"')
    return out


OBJECT_COLOR: dict[str, str] = _load_palette()           # persisted in palette.yaml


def apply():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
        "mathtext.fontset": "custom",
        "mathtext.rm": "Liberation Sans", "mathtext.it": "Liberation Sans:italic",
        "mathtext.bf": "Liberation Sans:bold",
        "axes.labelsize": SIZE["axis"], "xtick.labelsize": SIZE["tick"],
        "ytick.labelsize": SIZE["tick"], "legend.fontsize": SIZE["legend"],
        "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
        "xtick.direction": "out", "ytick.direction": "out",
        "lines.linewidth": 1.4, "lines.solid_capstyle": "round",
        "lines.markersize": 3.8, "lines.markeredgecolor": "white", "lines.markeredgewidth": 0.5,
        "axes.prop_cycle": mpl.cycler(color=list(PALETTE.values())),
        "pdf.fonttype": 42, "svg.fonttype": "none", "savefig.dpi": 600,
        "svg.hashsalt": "fixed", "path.simplify": True,
    })


def color(obj: str) -> str:
    """The same research object keeps the same colour in every figure."""
    if obj not in OBJECT_COLOR:
        OBJECT_COLOR[obj] = list(PALETTE.values())[len(OBJECT_COLOR) % len(PALETTE)]
        with _PAL_FILE.open("a", encoding="utf-8") as fh:
            fh.write(f'"{obj}": "{OBJECT_COLOR[obj]}"\n')
    return OBJECT_COLOR[obj]


def figure(nrows, ncols, width="double", height_mm=None, **kw):
    apply()
    w = WIDTH[width]
    h = (height_mm * MM) if height_mm else w * nrows / ncols * 0.8
    fig, axes = plt.subplots(nrows, ncols, figsize=(w, h), squeeze=False, **kw)
    return fig, axes


def ylabel(ax, text):
    ax.set_ylabel(text, rotation=0, ha="right", va="center", labelpad=8)


def label_panels(axes, start="a"):
    for i, ax in enumerate(getattr(axes, "flat", axes)):
        ax.text(-0.30, 1.02, chr(ord(start) + i), transform=ax.transAxes,
                fontsize=SIZE["label"], fontweight="bold", va="bottom")


def top_legend(fig, axes):
    h, l = [], []
    for ax in getattr(axes, "flat", axes):
        for hi, li in zip(*ax.get_legend_handles_labels()):
            if li not in l:
                h.append(hi); l.append(li)
    fig.legend(h, l, loc="upper center", ncol=max(len(l), 1), frameon=False,
               bbox_to_anchor=(0.5, 1.0))


def save(fig, name, outdir=None):
    fig.tight_layout(rect=(0, 0, 1, 0.945), h_pad=0.9, w_pad=1.6)
    out = Path(outdir) if outdir else ROOT / "results/figures"
    out.mkdir(parents=True, exist_ok=True)
    meta = {"pdf": {"CreationDate": None, "ModDate": None}, "svg": {"Date": None}, "png": {"Software": None}}
    for ext in ("pdf", "svg", "png"):
        fig.savefig(out / f"{name}.{ext}", bbox_inches="tight", metadata=meta[ext])
    plt.close(fig)


if __name__ == "__main__":
    import tempfile
    import numpy as np
    fig, axes = figure(1, 2, height_mm=60)
    x = np.linspace(0, 10, 50)
    for obj in ["Channel TMEM175", "Transporter SMCT1"]:
        axes[0, 0].plot(x, np.sin(x + len(obj)), "-o", color=PALETTE["navy"] if "C" in obj else PALETTE["teal"], label=obj, markevery=5)
        axes[0, 1].plot(x, np.cos(x + len(obj)), label=obj)
    ylabel(axes[0, 0], r"$\phi_{xy}$"); ylabel(axes[0, 1], r"$\rho^*_z$")
    label_panels(axes); top_legend(fig, axes)
    d = tempfile.mkdtemp()
    save(fig, "demo", outdir=d)
    print("saved", d)
