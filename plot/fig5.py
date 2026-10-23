"""Fig 5 - turning and experiment (null models, advantage against the turning indicator, robustness).
  python plot/fig5.py extract   (data/derived -> figure_data/fig5)
  python plot/fig5.py plot      (figure_data/fig5 -> results/figures/fig5.*)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import style
from style import CH, COL, MK, LABEL, LIGHT, DARK, MM

NAME = "fig5"
DATA = style.ROOT / "figure_data" / NAME


def extract():
    import derived
    S = derived.summary(); N = S["nulls"]; I = S["indicator"]; ap, chi, rob = [], [], []
    for p in CH:
        v = S["runs"][f"{p}_rc10"]["validation"]; rw = [r["best_tm"] for r in N.get(p, {}).get("rewired", []) if "best_tm" in r]
        ap.append(dict(structure=p, closed=v["closed"], nl=v["nl"], lin=v["lin"], dilation=N[p]["dilation"]["best_tm"] if p in N else None,
                       rewired_best=min(rw) if rw else None))
        chi.append(dict(structure=p, chi_010=I[p]["mem_eps0.10"]["chi"], delta=v["delta"]))
        pts = [("rc10", "rc10", v["delta"])]
        if f"{p}_rc12" in S["runs"] and S["runs"][f"{p}_rc12"].get("validation"):
            pts.append(("rc12", "rc12", S["runs"][f"{p}_rc12"]["validation"]["delta"]))
        for k, vv in S["variants"].items():
            if k.startswith(p + "_rc10_") and not k.endswith("loadcontrol"):
                pts.append(("backbone" if "kbb" in k else "load", k.split("_rc10_")[1], vv["delta"]))
        rob += [dict(structure=p, order=j, kind=kd, variant=nm, delta=d) for j, (kd, nm, d) in enumerate(pts)]
    for p in ("6cq8", "6vtk"):
        chi.append(dict(structure=p, chi_010=I[p]["mem_eps0.10"]["chi"], delta=None))
    style.write_csv(DATA / "approach.csv", ap, ["structure", "closed", "nl", "lin", "dilation", "rewired_best"])
    style.write_csv(DATA / "turning.csv", chi, ["structure", "chi_010", "delta"])
    style.write_csv(DATA / "robustness.csv", rob, ["structure", "order", "kind", "variant", "delta"])
    style.write_readme(DATA, "fig5 plotting data", "data/derived/summary.json (validation, nulls, indicator, variants)", {
        "approach.csv": [("structure", "structure id", "-", "label"), ("closed", "TM RMSD of the closed structure to the partner", "angstrom", "value"),
                         ("nl", "best TM RMSD of the nonlinear path", "angstrom", "value"), ("lin", "best TM RMSD of the best-amplitude linear response", "angstrom", "value"),
                         ("dilation", "best TM RMSD of an isotropic in-plane dilation", "angstrom", "value"),
                         ("rewired_best", "best TM RMSD over three rewired networks", "angstrom", "value")],
        "turning.csv": [("structure", "structure id", "-", "label"), ("chi_010", "second-order direction indicator chi at eps = 0.10 (membrane nodes)", "-", "value"),
                        ("delta", "advantage of the nonlinear path over the best-amplitude linear response (empty: no partner)", "angstrom", "value")],
        "robustness.csv": [("structure", "structure id", "-", "label"), ("order", "plotting order within the structure (jitter position)", "-", "index"),
                           ("kind", "rc10, rc12, load (load-construction variant) or backbone (stiffened backbone)", "-", "label"),
                           ("variant", "variant tag", "-", "label"), ("delta", "advantage Delta_L-NL", "angstrom", "value")]})


def plot():
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from figcommon import chan_handles
    AP = {r["structure"]: r for r in style.read_csv(f"figure_data/{NAME}/approach.csv")}
    TU = {r["structure"]: r for r in style.read_csv(f"figure_data/{NAME}/turning.csv")}
    RB = style.read_csv(f"figure_data/{NAME}/robustness.csv")
    style.apply()
    fig, ax = plt.subplots(1, 3, figsize=(style.W2, 70 * MM), gridspec_kw=dict(wspace=0.38, width_ratios=[1.25, 1, 1], left=0.07, right=0.99, bottom=0.22, top=0.80))
    xs = np.arange(len(CH)); a = ax[0]
    for i, p in enumerate(CH):
        r = AP[p]; c0 = float(r["closed"])
        g = dict(nl=(c0 - float(r["nl"])) / c0, lin=(c0 - float(r["lin"])) / c0)
        if r["dilation"] != "":
            g["dil"] = (c0 - float(r["dilation"])) / c0
            if r["rewired_best"] != "": g["rew"] = (c0 - float(r["rewired_best"])) / c0
        for key, mk, fc, off in (("nl", "o", COL[p], -0.27), ("lin", "o", "white", -0.09), ("dil", "D", "white", 0.09), ("rew", "s", "white", 0.27)):
            if key in g:
                a.vlines(i + off, 0, 100 * g[key], color=COL[p], lw=0.8)
                a.plot(i + off, 100 * g[key], mk, color=COL[p], mfc=fc, ms=3.8, mew=0.8)
    a.axhline(0, color=DARK, lw=0.5)
    a.set_xticks(xs); a.set_xticklabels([LABEL[p] for p in CH], rotation=40, ha="right"); a.set_xlim(-0.6, len(CH) - 0.4)
    a.set_ylabel("TM RMSD reduction (%)"); a.set_title("What explains the approach?")
    a.legend(handles=[Line2D([], [], ls="", marker="o", mfc="k", mec="k", ms=4, label="nonlinear path"),
                      Line2D([], [], ls="", marker="o", mfc="white", mec="k", ms=4, label="best-amplitude linear"),
                      Line2D([], [], ls="", marker="D", mfc="white", mec="k", ms=4, label="isotropic dilation"),
                      Line2D([], [], ls="", marker="s", mfc="white", mec="k", ms=4, label="best rewired network")], loc="upper right", fontsize=6, handletextpad=0.2)
    c = ax[1]
    c.axhspan(-0.2, 0.2, color=LIGHT, lw=0, zorder=0)
    for p in CH:
        chi, d = float(TU[p]["chi_010"]), float(TU[p]["delta"])
        c.plot(chi, d, MK[p], color=COL[p], ms=5, mec="white", mew=0.4, zorder=3)
        c.annotate(LABEL[p], (chi, d), xytext=(4, {"6pwn": -8, "4wff": -9}.get(p, 3)), textcoords="offset points", fontsize=6, color=COL[p])
    for p in ("6cq8", "6vtk"):
        chi = float(TU[p]["chi_010"]); c.plot(chi, -0.62, "|", color=COL[p], ms=8, mew=1.2)
        c.annotate(LABEL[p], (chi, -0.62), xytext=(3, 4), textcoords="offset points", fontsize=6, color=COL[p])
    c.axhline(0, color=DARK, lw=0.5)
    c.set_xlabel(r"a-priori indicator $\chi$ ($\varepsilon=0.10$, membrane nodes)"); c.set_ylabel(r"$\Delta_{L-NL}$ (Å)")
    c.set_title("Only the largest turning pays off"); c.set_xscale("log"); c.set_ylim(-0.7, 1.0)
    d = ax[2]
    d.axhspan(-0.2, 0.2, color=LIGHT, lw=0, zorder=0)
    for i, p in enumerate(CH):
        pts = [r for r in RB if r["structure"] == p]
        for r in pts:
            j = int(r["order"]); jit = (j - (len(pts) - 1) / 2) * 0.05
            mk = {"rc10": "o", "rc12": "s", "backbone": "^", "load": "x"}[r["kind"]]; fc = "white" if r["kind"] == "rc12" else COL[p]
            d.plot(i + jit, float(r["delta"]), mk, color=COL[p], mfc=fc, ms=3.6 if mk != "x" else 3.0, mew=0.8)
    d.axhline(0, color=DARK, lw=0.5)
    d.set_xticks(xs); d.set_xticklabels([LABEL[p] for p in CH], rotation=40, ha="right"); d.set_xlim(-0.6, len(CH) - 0.4)
    d.set_ylabel(r"$\Delta_{L-NL}$ (Å)"); d.set_title("Only Piezo1 stays above the margin")
    d.legend(handles=[Line2D([], [], ls="", marker="o", mfc="k", mec="k", ms=4, label="$r_c$ = 10 Å"), Line2D([], [], ls="", marker="s", mfc="white", mec="k", ms=4, label="$r_c$ = 12 Å"),
                      Line2D([], [], ls="", marker="x", color="k", ms=4, label="load construction"), Line2D([], [], ls="", marker="^", mfc="k", mec="k", ms=4, label="stiff backbone")],
             loc="upper right", fontsize=6, handletextpad=0.2)
    for a_, t in zip(ax, "abc"):
        style.letter(a_, t, dx=-0.22, dy=1.04)
    fig.legend(handles=chan_handles(CH + ["6cq8", "6vtk"], ls=""), loc="upper center", ncol=8, bbox_to_anchor=(0.5, 1.0))
    style.save(fig, NAME)
    pzr = [float(r["delta"]) for r in RB if r["structure"] == "6b3r"]
    style.describe(NAME, "Fig. 5 turning and experiment. Advantage of the nonlinear path over the best-amplitude linear response: Piezo1 {{pz}} A "
                   "(chi = {{pz_chi}}), the other channels {{o_min}} to {{o_max}} A. Across cutoffs and variants the Piezo1 advantage ranges over {{r_min}} to {{r_max}} A.",
                   dict(pz=style.fnum(TU["6b3r"]["delta"]), pz_chi=style.fnum(TU["6b3r"]["chi_010"]),
                        o_min=style.fnum(min(float(TU[p]["delta"]) for p in CH[1:])), o_max=style.fnum(max(float(TU[p]["delta"]) for p in CH[1:])),
                        r_min=style.fnum(min(pzr)), r_max=style.fnum(max(pzr))),
                   [f"figure_data/{NAME}/approach.csv", f"figure_data/{NAME}/turning.csv", f"figure_data/{NAME}/robustness.csv"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
