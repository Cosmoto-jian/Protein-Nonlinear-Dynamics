"""Small drawing helpers shared by the figure scripts (no data access)."""
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, NullFormatter
from style import CH, COL, MK, LABEL, LW, MS, MEW


def logticks(ax, axis="y"):
    a = ax.yaxis if axis == "y" else ax.xaxis
    a.set_major_locator(LogLocator(base=10, numticks=12))
    a.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=12)); a.set_minor_formatter(NullFormatter())


def chan_handles(chs=CH, ls="-", lw=None):
    return [Line2D([], [], color=COL[p], marker=MK[p], ms=MS["line"], lw=LW["data"] if lw is None else lw, ls=ls, mec="white", mew=MEW["edge"], label=LABEL[p]) for p in chs]


def mkh(marker, label, filled=True, **kw):
    """Black marker-only legend handle (filled or open) for encodings shared by all structures."""
    d = dict(ls="", marker=marker, color="k", mfc="k" if filled else "white", mec="k", ms=MS["line"], mew=MEW["open"], label=label); d.update(kw)
    return Line2D([], [], **d)


def num(rows, key):
    return np.array([np.nan if r[key] == "" else float(r[key]) for r in rows])
