"""Plotting style and paired descriptions. Every figure takes fonts, sizes, colours and widths from here.

Manuscript layout (a4, 2.5 cm margins): full width 160 mm (= \\textwidth), 1.5 column 120 mm, single column 78 mm; figures are
included at 100 %. Font ladder at print size: axis labels and panel titles 9 pt; tick labels, legends and in-panel annotations
8 pt (never smaller anywhere); panel letters 12 pt bold, aligned per row by save(). Panels are kept as small as the text allows
(compact layout engine, small pads). Legend rule: the structure legend is the first line on top (wrapped onto two rows rather than
shrunk), an encoding shared by several panels the next line on top, an encoding used by one panel sits inside that panel;
experiment drawn in EXP (black), never in a structure colour; bundled Liberation Sans (Arial metrics); Okabe-Ito colour-blind-safe
palette with one colour and marker per structure in every figure; line widths and marker sizes from LW / MS; vector PDF and SVG
with text kept as text, 600 dpi PNG."""
from pathlib import Path
import csv, json, re
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
MM = 1 / 25.4
WIDTH = {"single": 78 * MM, "onehalf": 120 * MM, "double": 160 * MM}
W1, W15, W2 = WIDTH["single"], WIDTH["onehalf"], WIDTH["double"]
SIZE = {"label": 12, "axis": 9, "title": 9, "tick": 8, "note": 8, "legend": 8}
FS = SIZE["note"]                                          # every in-panel annotation (also categorical tick labels)
FS_MIN = 8                                                 # no text below this size, checked by save()
LW = {"data": 1.2, "sec": 0.9, "thin": 0.6, "ref": 0.6, "zero": 0.5, "axis": 0.6, "arrow": 0.7}   # line widths (pt)
MS = {"pt": 4.5, "cat": 4.0, "line": 3.5, "small": 2.5, "dot": 0.9, "star": 7.0}  # marker sizes (pt): scatter points, points on categorical
#     axes, markers on lines/legends, dense series, background cloud, best frame / tick marks
MEW = {"edge": 0.4, "open": 0.8}                           # white edge of filled markers, outline of open markers
EXP = "#1A1A1A"                                            # experimental structure / target, all figures
NOTE = "#555555"                                           # colour of in-panel annotations
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
        "mathtext.fontset": "custom", "mathtext.rm": FONT, "mathtext.it": FONT + ":italic", "mathtext.bf": FONT + ":bold",
        "mathtext.sf": FONT, "mathtext.fallback": "cm",
        "font.size": SIZE["axis"], "axes.labelsize": SIZE["axis"], "axes.titlesize": SIZE["axis"], "legend.fontsize": SIZE["legend"],
        "xtick.labelsize": SIZE["tick"], "ytick.labelsize": SIZE["tick"], "axes.linewidth": LW["axis"],
        "xtick.direction": "out", "ytick.direction": "out", "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
        "xtick.major.width": LW["axis"], "ytick.major.width": LW["axis"], "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False, "legend.frameon": False,
        "legend.handlelength": 1.5, "legend.borderaxespad": 0.2, "legend.columnspacing": 1.0, "legend.handletextpad": 0.3,
        "legend.labelspacing": 0.25, "legend.borderpad": 0.2,
        "figure.dpi": 150, "savefig.dpi": 600, "savefig.pad_inches": 0.02,
        "axes.titleweight": "normal", "axes.titlelocation": "left", "axes.titlepad": 3,
        "lines.linewidth": LW["data"], "lines.markersize": MS["line"], "patch.linewidth": LW["axis"],
        "figure.constrained_layout.w_pad": 2.0 / 72, "figure.constrained_layout.h_pad": 2.5 / 72,
        "figure.constrained_layout.wspace": 0.0, "figure.constrained_layout.hspace": 0.0,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none", "svg.hashsalt": "fixed", "axes.labelpad": 2,
    })


def color(obj: str) -> str:
    """The same research object keeps the same colour in every figure."""
    if obj not in OBJECT_COLOR:
        OBJECT_COLOR[obj] = list(PALETTE.values())[len(OBJECT_COLOR) % len(PALETTE)]
        with _PAL_FILE.open("a", encoding="utf-8") as fh:
            fh.write(f'"{obj}": "{OBJECT_COLOR[obj]}"\n')
    return OBJECT_COLOR[obj]


def top_legend(fig, rows, y=None, gap_mm=0.6, ncol=None):
    """Legend block above the panels: rows[0] (the structures) on top, rows[1] (encodings shared by several panels) below.
    y is the lower edge of the block in figure coordinates (1.0 = just above the panels; save() crops tightly). A row that does
    not fit the figure width at the legend font size is wrapped onto two lines instead of being shrunk."""
    out = []; r = fig.canvas.get_renderer(); W, H = fig.bbox.width, fig.bbox.height
    yb = 1.0 + 1.0 * MM * fig.dpi / H if y is None else y
    for h in reversed(rows):
        n = ncol or len(h); h0 = list(h)
        while True:
            lg = fig.legend(handles=h, loc="lower center", ncol=n, bbox_to_anchor=(0.5, yb), handletextpad=0.35,
                            columnspacing=1.1, borderaxespad=0.0, borderpad=0.0)
            bb = lg.get_window_extent(r)
            if bb.width <= W * 0.995 or n <= 1:
                break
            lg.remove(); n = -(-len(h) // 2) if n > -(-len(h) // 2) else n - 1
            nr = -(-len(h) // n)                          # matplotlib fills columns first: reorder so rows read left to right
            h = [h0[r_ * n + c_] for c_ in range(n) for r_ in range(nr) if r_ * n + c_ < len(h0)] if nr > 1 else h0
        out.append(lg); yb += (bb.height + gap_mm * MM * fig.dpi) / H
    return out


def figure(nrows, ncols, width="double", height_mm=None, layout="constrained", **kw):
    """Figure of the given manuscript width; panels packed by the constrained layout engine with small pads."""
    apply()
    w = WIDTH[width] if isinstance(width, str) else width
    h = (height_mm * MM) if height_mm else w * nrows / ncols * 0.8
    fig, axes = plt.subplots(nrows, ncols, figsize=(w, h), squeeze=False, layout=layout, **kw)
    return fig, axes


def catlabels(axis, labels, rotation=90):
    """Categorical tick labels (structure names) at the annotation size, vertical."""
    kw = dict(rotation=rotation, ha="right", va="center", rotation_mode="anchor") if axis.axis_name == "x" else {}
    axis.set_ticklabels(labels, fontsize=FS, **kw)


def letter(ax, s, dx=-0.16, dy=1.0):
    """Panel letter; save() moves it to the left edge of the panel (tick labels and axis title included) and to the
    common top of its row, so dx, dy only matter before alignment."""
    t = ax.text(dx, dy, s, transform=ax.transAxes, fontsize=SIZE["label"], fontweight="bold", va="top", ha="left")
    t.set_in_layout(False)
    t._panel_axes = ax
    LETTERS.append(t)
    return t


LETTERS = []


def _align_titles(fig, axes, r):
    """Left panel titles of one row share one baseline (the highest), also for equal-aspect panels."""
    H = fig.bbox.height; rows = []
    for ax in sorted(axes, key=lambda a: -a.get_window_extent(r).y1):
        for row in rows:
            if abs(row[0].get_window_extent(r).y1 - ax.get_window_extent(r).y1) < 0.08 * H or abs(row[0].get_window_extent(r).y1 - ax.get_window_extent(r).y1) < 0.2 * H and _same_band(row[0], ax, r):
                row.append(ax); break
        else:
            rows.append([ax])
    for row in rows:
        tl = [(ax, tt) for ax in row for tt in (ax.title, ax._left_title) if tt.get_text().strip()]
        if len(tl) < 2:
            continue
        target = max(tt.get_window_extent(r).y0 for _, tt in tl)
        for ax, tt in tl:
            bb = ax.get_window_extent(r); x, y = tt.get_position()
            ax._autotitlepos = False; tt.set_y(y + (target - tt.get_window_extent(r).y0) / bb.height)


def _same_band(a, b, r):
    ba, bb = a.get_window_extent(r), b.get_window_extent(r)
    return min(ba.y1, bb.y1) - max(ba.y0, bb.y0) > 0.5 * min(ba.height, bb.height)


def _align_letters(fig):
    from matplotlib.transforms import Bbox
    mine = [t for t in LETTERS if t.figure is fig]
    if not mine:
        return
    r = fig.canvas.get_renderer(); W, H = fig.bbox.width, fig.bbox.height
    _align_titles(fig, [t._panel_axes for t in mine], r)
    fig.canvas.draw()
    for t in mine:
        t.set_visible(False)
    boxes = []
    for t in mine:
        ax = t._panel_axes
        tb = ax.get_tightbbox(r, bbox_extra_artists=[c for c in ax.texts if c is not t and getattr(c, "_in_layout", True)] )
        pb = ax.get_window_extent(r)
        boxes.append((t, tb, pb))
    rows = []
    for t, tb, pb in sorted(boxes, key=lambda b: -b[2].y1):
        for row in rows:
            if abs(row[0][2].y1 - pb.y1) < 0.08 * H:
                row.append((t, tb, pb)); break
        else:
            rows.append([(t, tb, pb)])
    for row in rows:
        top = max(max(tb.y1, pb.y1) for _, tb, pb in row)
        for t, tb, pb in row:
            t.set_transform(fig.transFigure); t.set_position(((tb.x0) / W, (top + 2) / H)); t.set_ha("left"); t.set_va("top")
            t.set_visible(True); t.set_in_layout(True)        # layout is frozen now; tight cropping must include the letter
            ax = t._panel_axes; lb = t.get_window_extent(r)
            for tt in (ax.title, ax._left_title):
                if tt.get_text().strip():
                    bb = tt.get_window_extent(r)
                    if lb.overlaps(bb):                       # panel without axes: move its title right of the letter
                        x, y = tt.get_position(); pw = ax.get_window_extent(r).width
                        tt.set_x(x + (lb.x1 + 4 - bb.x0) / pw)


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
    for ax in fig.axes:                               # a panel title must not run past its panel
        for tt in (ax.title, ax._left_title, ax._right_title):
            if tt.get_text().strip() and ax.axison and tt.get_window_extent(r).x1 > ax.get_window_extent(r).x1 + 3:
                bad.append(("title-overflow", tt.get_text()[:30]))
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
    try:
        fig.align_ylabels([a for a in fig.axes if a.axison])
    except Exception:
        pass
    fig.canvas.draw()
    if fig.get_layout_engine() is not None:          # freeze the packed positions before letters are placed
        fig.set_layout_engine("none")
    _align_letters(fig)
    fig.canvas.draw()
    bad = check_overlaps(fig)
    small = sorted({round(t.get_fontsize(), 2) for t in fig.findobj(mpl.text.Text) if t.get_text().strip() and t.get_visible() and t.get_fontsize() < FS_MIN - 1e-6})
    if small:
        bad.append(("font-below-min", small))
    out = Path(outdir) if outdir else ROOT / "results/figures"
    out.mkdir(parents=True, exist_ok=True)
    meta = {"pdf": {"CreationDate": None, "ModDate": None}, "svg": {"Date": None}, "png": {"Software": None}}
    for ext in ("pdf", "svg", "png"):
        fig.savefig(out / f"{name}.{ext}", bbox_inches="tight", metadata=meta[ext])
    plt.close(fig)
    import subprocess
    try:
        wpt = float(re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", subprocess.run(["pdfinfo", str(out / f"{name}.pdf")], capture_output=True, text=True).stdout).group(1))
        hpt = float(re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", subprocess.run(["pdfinfo", str(out / f"{name}.pdf")], capture_output=True, text=True).stdout).group(2))
        size = f" size: {wpt / 72 * 25.4:.1f} x {hpt / 72 * 25.4:.1f} mm"
    except Exception:
        size = ""
    print(name, "overlaps:", bad if bad else "none", size)
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
