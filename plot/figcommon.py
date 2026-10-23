"""Small drawing helpers shared by the figure scripts (no data access)."""
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, NullFormatter
from style import CH, COL, MK, LABEL


def logticks(ax, axis="y"):
    a = ax.yaxis if axis == "y" else ax.xaxis
    a.set_major_locator(LogLocator(base=10, numticks=12))
    a.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=12)); a.set_minor_formatter(NullFormatter())


def chan_handles(chs=CH, ls="-", lw=1.0):
    return [Line2D([], [], color=COL[p], marker=MK[p], ms=3.5, lw=lw, ls=ls, mec="white", mew=0.4, label=LABEL[p]) for p in chs]


def num(rows, key):
    return np.array([np.nan if r[key] == "" else float(r[key]) for r in rows])
