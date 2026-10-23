"""Plotting style and paired descriptions. Every figure takes fonts, sizes, colours and widths from here.

Elsevier (JMPS) layout: single column 90 mm, 1.5 column 140 mm, double column 190 mm; font ladder 8/7/6 pt
(labels / legends and annotations / ticks), panel letters 9 pt bold; bundled Liberation Sans (Arial metrics); Okabe-Ito colour-blind-safe palette with one
colour and marker per structure in every figure; vector PDF and SVG with text kept as text, 600 dpi PNG."""
from pathlib import Path
import csv, json, re
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
MM = 1 / 25.4
WIDTH = {"single": 90 * MM, "onehalf": 140 * MM, "double": 190 * MM}
W1, W15, W2 = WIDTH["single"], WIDTH["onehalf"], WIDTH["double"]
SIZE = {"label": 9, "axis": 8, "tick": 6, "note": 7, "legend": 7}
CH = ["6b3r", "6pwn", "2oar", "4xdk", "4wff", "6mgv"]             # channels with a partner structure
ALL = CH + ["6cq8", "6vtk"]
LABEL = {"6b3r": "Piezo1", "6pwn": "MscS", "2oar": "MscL", "4xdk": "TREK-2", "4wff": "TRAAK", "6mgv": "OSCA1.2",
         "6cq8": "6CQ8", "6vtk": "6VTK"}
COL = {"6b3r": "#D55E00", "6pwn": "#009E73", "2oar": "#0072B2", "4xdk": "#CC79A7", "4wff": "#E69F00",
       "6mgv": "#56B4E9", "6cq8": "#7F7F7F", "6vtk": "#4D4D4D"}
MK = {"6b3r": "o", "6pwn": "s", "2oar": "D", "4xdk": "^", "4wff": "v", "6mgv": "p", "6cq8": "X", "6vtk": "P"}
GREY = "#8C8C8C"; LIGHT = "#E6E6E6"; DARK = "#333333"
PALETTE = {"vermilion": "#D55E00", "green": "#009E73", "blue": "#0072B2", "purple": "#CC79A7", "orange": "#E69F00",
           "sky": "#56B4E9", "grey": "#7F7F7F", "dark": "#4D4D4D"}
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


FONT_DIR = Path(__file__).with_name("fonts")
FONT = "Liberation Sans"                                  # metric-compatible with Arial; bundled for reproducibility


def _use_bundled_font():
    """Register the bundled Liberation Sans files and remove other copies of that family, so every platform uses the same glyphs."""
    from matplotlib import font_manager as fm
    files = sorted(FONT_DIR.glob("*.ttf"))
    if not files:
        return
    fm.fontManager.ttflist = [f for f in fm.fontManager.ttflist if f.name != FONT]
    for f in files:
        fm.fontManager.addfont(str(f))
    fm.fontManager._findfont_cached.cache_clear()


def apply():
    _use_bundled_font()
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": [FONT, "DejaVu Sans"],
        "mathtext.fontset": "dejavusans",
        "font.size": SIZE["axis"], "axes.labelsize": SIZE["axis"], "axes.titlesize": SIZE["axis"], "legend.fontsize": SIZE["legend"],
        "xtick.labelsize": SIZE["tick"], "ytick.labelsize": SIZE["tick"], "axes.linewidth": 0.6,
        "xtick.direction": "out", "ytick.direction": "out", "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False, "legend.frameon": False,
        "legend.handlelength": 1.6, "legend.borderaxespad": 0.2, "legend.columnspacing": 1.0,
        "figure.dpi": 150, "savefig.dpi": 600, "savefig.pad_inches": 0.02,
        "axes.titleweight": "normal", "axes.titlelocation": "left", "axes.titlepad": 3,
        "lines.linewidth": 1.0, "lines.markersize": 3.5, "patch.linewidth": 0.6,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none", "svg.hashsalt": "fixed", "axes.labelpad": 2,
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


def letter(ax, s, dx=-0.16, dy=1.0):
    ax.text(dx, dy, s, transform=ax.transAxes, fontsize=SIZE["label"], fontweight="bold", va="bottom", ha="left")


def label_panels(axes, start="a", dx=-0.30, dy=1.02):
    for i, ax in enumerate(getattr(axes, "flat", axes)):
        letter(ax, chr(ord(start) + i), dx=dx, dy=dy)


def _ticklabels_in_view(ax):
    out = set()
    for axis, lim in ((ax.xaxis, ax.get_xlim()), (ax.yaxis, ax.get_ylim())):
        lo, hi = min(lim), max(lim)
        for tk in axis.get_major_ticks() + axis.get_minor_ticks():
            if lo - 1e-12 * abs(hi) <= tk.get_loc() <= hi + 1e-12 * abs(hi):
                out.add(tk.label1)
    return out


def check_overlaps(fig):
    """render-then-verify (figure-style 9.1): overlapping visible text boxes and text crossing foreign spines.
    Tick labels outside the view limits are ignored; rotated tick labels are compared by their rotated footprint
    (approximated by the text's own bbox shrunk to 60 %)."""
    r = fig.canvas.get_renderer()
    shown = set()
    for ax in fig.axes:
        shown |= _ticklabels_in_view(ax)
    alltl = set()
    for ax in fig.axes:
        alltl |= set(ax.get_xticklabels(which='both') + ax.get_yticklabels(which='both'))
    for ax in fig.axes:
        if not ax.axison:
            shown -= set(ax.get_xticklabels(which='both') + ax.get_yticklabels(which='both'))
    texts = []
    for t in fig.findobj(mpl.text.Text):
        if not (t.get_text().strip() and t.get_visible()):
            continue
        if t in alltl and t not in shown:
            continue
        bb = t.get_window_extent(r)
        if t.get_rotation() not in (0, 90, 270) and t.get_rotation() % 90:
            bb = bb.shrunk(0.6, 0.6)
        texts.append((t, bb))
    spines = [(s, s.get_window_extent(r)) for ax in fig.axes for s in ax.spines.values() if s.get_visible()]
    bad = []
    for i, (a, ba) in enumerate(texts):
        for b, bb in texts[i + 1:]:
            if ba.overlaps(bb):
                bad.append(('text-text', a.get_text()[:30], b.get_text()[:30]))
        for s, bs in spines:
            if a.axes is s.axes or a in alltl:
                continue
            if ba.overlaps(bs):
                bad.append(('text-spine', a.get_text()[:30]))
    return bad


def save(fig, name, outdir=None, tight=False):
    """Write <name>.pdf/.svg/.png to results/figures without timestamps; return overlapping text found on the drawn figure."""
    if tight:
        fig.tight_layout(rect=(0, 0, 1, 0.945), h_pad=0.9, w_pad=1.6)
    fig.canvas.draw()
    bad = check_overlaps(fig)
    out = Path(outdir) if outdir else ROOT / "results/figures"
    out.mkdir(parents=True, exist_ok=True)
    meta = {"pdf": {"CreationDate": None, "ModDate": None}, "svg": {"Date": None}, "png": {"Software": None}}
    for ext in ("pdf", "svg", "png"):
        fig.savefig(out / f"{name}.{ext}", bbox_inches="tight", metadata=meta[ext])
    plt.close(fig)
    print(name, "overlaps:", bad if bad else "none")
    return bad


# ---- paired descriptions: {{key}} placeholders are filled from data, numbers are never typed
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


def write_csv(path: Path, rows: list[dict], columns: list[str]):
    """Plotting table with fixed column order; floats written with repr precision (lossless)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in columns})


def write_readme(folder: Path, title: str, source: str, tables: dict):
    """tables: {csv name: [(column, meaning, unit, kind), ...]} -> README.md documenting every column."""
    lines = [f"# {title}", "", f"Source: {source}", ""]
    for name, cols in tables.items():
        lines += [f"## {name}", "| Column | Meaning | Unit | Kind |", "|---|---|---|---|"]
        lines += [f"| {c} | {m} | {u} | {k} |" for c, m, u, k in cols] + [""]
    (folder / "README.md").write_text("\n".join(lines), encoding="utf-8")


def fnum(x, nd=2):
    return f"{float(x):.{nd}f}"
