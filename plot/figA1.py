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
        "thresholds.csv": [("structure", "structure id", "-", "label"), ("criterion", "validity thresholds P20_|e|max, or backbone_0.05 (|e|_bb <= 5 %)", "-", "label"),
                           ("delta", "advantage Delta_L-NL under that criterion", "angstrom", "value")],
        "margins.csv": [("structure", "structure id", "-", "label"), ("margin", "absolute equivalence margin", "angstrom", "value"),
                        ("cls", "class: NL better, equivalent or NL worse", "-", "label")],
        "load_variants.csv": [("structure", "structure id", "-", "label"), ("variant", "reference or load-construction variant tag", "-", "label"),
                              ("delta", "advantage Delta_L-NL", "angstrom", "value")]})


def plot():
    import matplotlib.pyplot as plt
    from figcommon import chan_handles, num
    TH = style.read_csv(f"figure_data/{NAME}/thresholds.csv"); MG = style.read_csv(f"figure_data/{NAME}/margins.csv"); LV = style.read_csv(f"figure_data/{NAME}/load_variants.csv")
    style.apply()
    fig = plt.figure(figsize=(style.W2, 72 * MM))
    axa = fig.add_axes([0.05, 0.22, 0.40, 0.66]); axb = fig.add_axes([0.55, 0.22, 0.18, 0.66]); axc = fig.add_axes([0.82, 0.22, 0.18, 0.66])
    lab = [f"{float(a) * 100:g}% / {b}" for a, b in (k.split("_") for k in KEYS[:-1])] + ["bb 5%"]
    d = {(r["structure"], r["criterion"]): (np.nan if r["delta"] == "" else float(r["delta"])) for r in TH}
    M = np.array([[d[(p, k)] for k in KEYS] for p in CH])
    lim = np.nanmax(np.abs(M)); im = axa.imshow(M, cmap="RdBu_r", vmin=-lim, vmax=lim, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            axa.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=5.5, color="white" if abs(M[i, j]) > 0.6 * lim else DARK)
    axa.set_xticks(range(len(KEYS))); axa.set_xticklabels(lab, rotation=55, ha="right", fontsize=5.5)
    axa.set_yticks(range(len(CH))); axa.set_yticklabels([LABEL[p] for p in CH])
    axa.set_xlabel(r"validity thresholds $P_{20}$ / $|e|_{\max}$"); axa.set_title(r"$\Delta_{L-NL}$ (Å)")
    for sp_ in axa.spines.values(): sp_.set_visible(False)
    cb = fig.colorbar(im, ax=axa, fraction=0.04, pad=0.02); cb.ax.tick_params(labelsize=6); cb.outline.set_linewidth(0.4)
    cl = {"NL better": 1, "equivalent": 0, "NL worse": -1}
    for i, p in enumerate(CH):
        rr = [r for r in MG if r["structure"] == p]
        axb.plot(num(rr, "margin"), np.array([cl[r["cls"]] for r in rr]) + (i - 2.5) * 0.06, MK[p] + "-", color=COL[p], ms=3, lw=0.7, mec="white", mew=0.3)
    axb.set_yticks([-1, 0, 1]); axb.set_yticklabels(["NL worse", "equiv.", "NL better"]); axb.set_xlabel("equivalence margin (Å)")
    axb.set_title("class vs. margin"); axb.set_ylim(-1.5, 1.5)
    for i, p in enumerate(("6b3r", "6pwn")):
        y = [float(r["delta"]) for r in LV if r["structure"] == p and r["variant"] != "reference"]
        ref = [float(r["delta"]) for r in LV if r["structure"] == p and r["variant"] == "reference"][0]
        axc.plot(np.full(len(y), i) + np.linspace(-0.15, 0.15, len(y)), y, "x", color=COL[p], ms=3.5, mew=0.8)
        axc.plot(i, ref, MK[p], color=COL[p], ms=5, mec="white", mew=0.4)
    axc.axhspan(-0.2, 0.2, color=LIGHT, lw=0, zorder=0); axc.axhline(0, color=DARK, lw=0.5)
    axc.set_xticks([0, 1]); axc.set_xticklabels(["Piezo1", "MscS"]); axc.set_xlim(-0.6, 1.6); axc.set_ylabel(r"$\Delta_{L-NL}$ (Å)")
    axc.set_title("load construction")
    fig.legend(handles=chan_handles(ls="-"), loc="upper center", ncol=6, bbox_to_anchor=(0.66, 1.07), fontsize=6)
    for a_, tt, dx in ((axa, "a", -0.18), (axb, "b", -0.55), (axc, "c", -0.5)):
        a_.text(dx, 1.04, tt, transform=a_.transAxes, fontsize=9, fontweight="bold", va="bottom")
    style.save(fig, NAME)
    pz = M[0, :-1]
    style.describe(NAME, "Fig. A.1 sensitivity (r_c = 10 A). Piezo1 Delta_L-NL over the nine validity-threshold combinations: {{pmin}} to {{pmax}} A; "
                   "with the backbone criterion: {{pbb}} A. Load-construction variants: Piezo1 {{lpmin}} to {{lpmax}} A, MscS {{lsmin}} to {{lsmax}} A.",
                   dict(pmin=f"{np.nanmin(pz):.2f}", pmax=f"{np.nanmax(pz):.2f}", pbb=f"{M[0, -1]:.2f}",
                        lpmin=f"{min(float(r['delta']) for r in LV if r['structure'] == '6b3r'):.2f}", lpmax=f"{max(float(r['delta']) for r in LV if r['structure'] == '6b3r'):.2f}",
                        lsmin=f"{min(float(r['delta']) for r in LV if r['structure'] == '6pwn'):.2f}", lsmax=f"{max(float(r['delta']) for r in LV if r['structure'] == '6pwn'):.2f}"),
                   [f"figure_data/{NAME}/thresholds.csv", f"figure_data/{NAME}/margins.csv", f"figure_data/{NAME}/load_variants.csv"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
