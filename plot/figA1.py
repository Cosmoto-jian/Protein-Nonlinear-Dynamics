"""Fig A.1 - sensitivity of the comparison to validity thresholds, margin and load construction.
  python plot/figA1.py extract   (data/derived -> figure_data/figA1)
  python plot/figA1.py plot      (figure_data/figA1 -> results/figures/figA1.*)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import style
from style import CH, COL, MK, LABEL, LIGHT, DARK, MM

NAME = "figA1"
DATA = style.ROOT / "figure_data" / NAME
KEYS = [f"{a}_{b}" for a in (0.025, 0.05, 0.1) for b in (0.3, 0.5, 0.7)] + ["backbone_0.05"]


def extract():
    import derived
    S = derived.summary(); T = S["thresholds"]
    th = [dict(structure=p, criterion=k, delta=(T[p][k]["delta"] if T[p][k] else None)) for p in CH for k in KEYS]
    mg = [dict(structure=p, margin=float(m), cls=T[p]["margins"][m]) for p in CH for m in sorted(T[p]["margins"], key=float)]
    lv = []
    for p in ("6b3r", "6pwn"):
        lv.append(dict(structure=p, variant="reference", delta=S["runs"][f"{p}_rc10"]["validation"]["delta"]))
        lv += [dict(structure=p, variant=k.split("_rc10_")[1], delta=v["delta"]) for k, v in S["variants"].items()
               if k.startswith(p + "_rc10_") and "kbb" not in k and "loadcontrol" not in k]
    style.write_csv(DATA / "thresholds.csv", th, ["structure", "criterion", "delta"])
    style.write_csv(DATA / "margins.csv", mg, ["structure", "margin", "cls"])
    style.write_csv(DATA / "load_variants.csv", lv, ["structure", "variant", "delta"])
    style.write_readme(DATA, "figA1 plotting data", "data/derived/summary.json (thresholds, variants, runs)", {
        "thresholds.csv": [("structure", "structure id", "-", "label"), ("criterion", "validity thresholds P20_|eta|max, or backbone_0.05 (|eta|_bb <= 5 %)", "-", "label"),
                           ("delta", "advantage Delta_L-NL under that criterion", "angstrom", "value")],
        "margins.csv": [("structure", "structure id", "-", "label"), ("margin", "absolute equivalence margin", "angstrom", "value"),
                        ("cls", "class: NL better, equivalent or NL worse", "-", "label")],
        "load_variants.csv": [("structure", "structure id", "-", "label"), ("variant", "reference or load-construction variant tag", "-", "label"),
                              ("delta", "advantage Delta_L-NL", "angstrom", "value")]})


def plot():
    import matplotlib.pyplot as plt
    from figcommon import chan_handles, num
    TH = style.read_csv(f"figure_data/{NAME}/thresholds.csv"); MG = style.read_csv(f"figure_data/{NAME}/margins.csv"); LV = style.read_csv(f"figure_data/{NAME}/load_variants.csv")
    from style import LW, MS, MEW
    from figcommon import mkh
    fig, ax = style.figure(1, 2, height_mm=56, gridspec_kw=dict(width_ratios=[1.45, 1.05])); axa, axb = ax[0]
    lab = [f"{float(a) * 100:g}% / {b}" for a, b in (k.split("_") for k in KEYS[:-1])] + ["bb 5%"]
    d = {(r["structure"], r["criterion"]): (np.nan if r["delta"] == "" else float(r["delta"])) for r in TH}
    M = np.array([[d[(p, k)] for k in KEYS] for p in CH])
    lim = np.nanmax(np.abs(M))
    # vector cells (pcolormesh) instead of imshow: an embedded raster makes the SVG depend on the PNG encoder
    MT = M.T                                           # criteria as rows, structures as columns
    im = axa.pcolormesh(np.arange(MT.shape[1] + 1) - 0.5, np.arange(MT.shape[0] + 1) - 0.5, np.ma.masked_invalid(MT),
                        cmap="RdBu_r", vmin=-lim, vmax=lim, edgecolors="face", linewidth=0)
    axa.set_xlim(-0.5, MT.shape[1] - 0.5); axa.set_ylim(MT.shape[0] - 0.5, -0.5)
    for i in range(MT.shape[0]):
        for j in range(MT.shape[1]):
            axa.text(j, i, f"{MT[i, j]:.2f}".replace("-", "\u2212"), ha="center", va="center", fontsize=style.FS, color="white" if abs(MT[i, j]) > 0.6 * lim else DARK)
    axa.set_yticks(range(len(KEYS))); style.catlabels(axa.yaxis, lab)
    axa.set_xticks(range(len(CH))); style.catlabels(axa.xaxis, [LABEL[p] for p in CH])
    axa.tick_params(length=0)
    axa.set_ylabel(r"$P_{20}$ / $|\eta|_{\max}$"); axa.set_title("Validity thresholds", loc="left")
    for sp_ in axa.spines.values(): sp_.set_visible(False)
    cb = fig.colorbar(im, ax=axa, fraction=0.05, pad=0.02, aspect=20); cb.ax.tick_params(labelsize=style.SIZE["tick"]); cb.outline.set_linewidth(LW["zero"]); cb.set_label(r"$\Delta_{\mathrm{L-NL}}$ (Å)")
    cb.solids.set_rasterized(False)                    # keep the colour bar vector (reproducible SVG)
    cl = {"NL better": 1, "equivalent": 0, "NL worse": -1}
    for i, p in enumerate(CH):
        rr = [r for r in MG if r["structure"] == p]
        axb.plot(num(rr, "margin"), np.array([cl[r["cls"]] for r in rr]) + (i - 2.5) * 0.09, MK[p] + "-", color=COL[p], ms=MS["line"], lw=LW["thin"], mec="white", mew=MEW["edge"])
    axb.set_yticks([-1, 0, 1]); style.catlabels(axb.yaxis, ["NL worse", "equiv.", "NL better"]); axb.set_xlabel("margin (Å)")
    axb.set_title("Class vs. margin", loc="left"); axb.set_ylim(-1.5, 1.5)
    fig.canvas.draw()
    style.top_legend(fig, [chan_handles()])
    for a_, tt, dx in ((axa, "a", -0.18), (axb, "b", -0.55)):
        style.letter(a_, tt)
    style.save(fig, NAME)
    pz = M[0, :-1]
    style.describe(NAME, "Fig. A.1 sensitivity (r_c = 10 A). Piezo1 Delta_L-NL over the nine validity-threshold combinations: {{pmin}} to {{pmax}} A; "
                   "with the backbone criterion: {{pbb}} A.",
                   dict(pmin=f"{np.nanmin(pz):.2f}", pmax=f"{np.nanmax(pz):.2f}", pbb=f"{M[0, -1]:.2f}",
                        lpmin=f"{min(float(r['delta']) for r in LV if r['structure'] == '6b3r'):.2f}", lpmax=f"{max(float(r['delta']) for r in LV if r['structure'] == '6b3r'):.2f}",
                        lsmin=f"{min(float(r['delta']) for r in LV if r['structure'] == '6pwn'):.2f}", lsmax=f"{max(float(r['delta']) for r in LV if r['structure'] == '6pwn'):.2f}"),
                   [f"figure_data/{NAME}/thresholds.csv", f"figure_data/{NAME}/margins.csv", f"figure_data/{NAME}/load_variants.csv"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
