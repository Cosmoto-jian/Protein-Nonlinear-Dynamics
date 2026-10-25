"""Fig A.2 - gauge diagnostics for all eight structures.
  python plot/figA2.py extract   (data/derived -> figure_data/figA2)
  python plot/figA2.py plot      (figure_data/figA2 -> results/figures/figA2.*)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import style
from style import COL, MK, MM

NAME = "figA2"
DATA = style.ROOT / "figure_data" / NAME


def extract():
    import derived
    L = derived.summary()["load_check"]
    rows = [dict(structure=p, anchor_reaction=r["gauge_raw"]["anchor_reaction_rel"], rmsd_raw=r["gauge_raw"]["rmsd_anchored_vs_eckart"],
                 rmsd_equilibrated=r["gauge_eq"]["rmsd_anchored_vs_eckart"], lambda_eckart=r["gauge_raw"]["lambda_eckart"],
                 lambda_anchored=r["gauge_raw"]["lambda_anchored"]) for p, r in L.items()]
    style.write_csv(DATA / "anchors.csv", rows, ["structure", "anchor_reaction", "rmsd_raw", "rmsd_equilibrated", "lambda_eckart", "lambda_anchored"])
    style.write_readme(DATA, "figA2 plotting data", "data/derived/summary.json (load_check)", {
        "anchors.csv": [("structure", "structure id", "-", "label"), ("anchor_reaction", "support reaction of six isostatic anchors relative to the load", "-", "value"),
                        ("rmsd_raw", "RMSD of the anchored solution from the Eckart solution, original load", "angstrom", "value"),
                        ("rmsd_equilibrated", "the same for the reference-equilibrated load A'", "angstrom", "value"),
                        ("lambda_eckart", "lowest constrained eigenvalue with the Eckart conditions", "model units", "value"),
                        ("lambda_anchored", "lowest constrained eigenvalue with the anchors", "model units", "value")]})


def plot():
    import matplotlib.pyplot as plt
    from figcommon import chan_handles
    R = style.read_csv(f"figure_data/{NAME}/anchors.csv")
    from style import LW, MS, MEW
    from figcommon import mkh
    fig, ax = style.figure(1, 2, width="onehalf", height_mm=50); ax = ax[0]
    for r in R:
        p = r["structure"]; x = float(r["anchor_reaction"]); a, b = float(r["rmsd_raw"]), float(r["rmsd_equilibrated"])
        ax[0].plot(x, a, MK[p], color=COL[p], ms=MS["pt"], mec="white", mew=MEW["edge"])
        ax[0].plot(x, b, MK[p], color=COL[p], mfc="white", ms=MS["pt"], mew=MEW["open"])
        ax[0].plot([x] * 2, [a, b], color=COL[p], lw=LW["thin"])
        ax[1].plot(float(r["lambda_eckart"]), float(r["lambda_anchored"]), MK[p], color=COL[p], ms=MS["pt"], mec="white", mew=MEW["edge"])
    ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("anchor reaction / load"); ax[0].set_ylabel("RMSD to Eckart (Å)")
    ax[0].set_title("Anchor distortion", loc="left")
    ax[0].legend(handles=[mkh("o", "load $A$"), mkh("o", "equilibrated $A'$", filled=False)], loc="lower right", handletextpad=0.1, borderaxespad=0.1)
    xx = np.logspace(-5.5, -1.5, 10)
    for f_ in (1, 0.1, 0.01):
        ax[1].plot(xx, xx * f_, color="#BDBDBD", lw=LW["ref"], ls=(0, (1, 1.5)), zorder=0)
        ax[1].text(xx[-1], xx[-1] * f_, {1: "1", 0.1: "1/10", 0.01: "1/100"}[f_], fontsize=style.FS, color=style.NOTE, ha="left", va="center")
    ax[1].set_xscale("log"); ax[1].set_yscale("log"); ax[1].set_xlabel(r"$\lambda_1$, Eckart"); ax[1].set_ylabel(r"$\lambda_1$, anchored")
    ax[1].set_title("Lowest eigenvalue", loc="left")
    for a_, tt in zip(ax, "ab"):
        style.letter(a_, tt)
    fig.canvas.draw()
    style.top_legend(fig, [chan_handles(style.ALL)])
    style.save(fig, NAME)
    ratio = [float(r["lambda_eckart"]) / float(r["lambda_anchored"]) for r in R]
    worse = sum(float(r["rmsd_equilibrated"]) > float(r["rmsd_raw"]) + 0.01 for r in R)      # same rule as src/make_tex.py (eq-worse)
    style.describe(NAME, "Fig. A.2 gauge diagnostics for {{n}} structures. Six isostatic anchors carry reactions of {{rmin}} to {{rmax}} of the load and distort "
                   "the solution by up to {{dmax}} A; the reference-equilibrated load increases the distortion by more than 0.01 A in {{worse}} structures. The anchored tangent is "
                   "{{lmin}} to {{lmax}} times softer than with the Eckart conditions.",
                   dict(n=len(R), rmin=f"{min(float(r['anchor_reaction']) for r in R):.1e}", rmax=f"{max(float(r['anchor_reaction']) for r in R):.2f}",
                        dmax=f"{max(float(r['rmsd_raw']) for r in R):.2f}", worse=worse, lmin=f"{min(ratio):.0f}", lmax=f"{max(ratio):.0f}"),
                   [f"figure_data/{NAME}/anchors.csv"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
