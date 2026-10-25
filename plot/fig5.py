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
                         ("rewired_best", "best TM RMSD over all rewired networks", "angstrom", "value")],
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
    from figcommon import mkh
    from style import LW, MS, MEW
    fig, ax = style.figure(1, 3, height_mm=54, gridspec_kw=dict(width_ratios=[1.45, 1, 1])); ax = ax[0]
    xs = np.arange(len(CH)); a = ax[0]
    for i, p in enumerate(CH):
        r = AP[p]; c0 = float(r["closed"])
        g = dict(nl=(c0 - float(r["nl"])) / c0, lin=(c0 - float(r["lin"])) / c0)
        if r["dilation"] != "":
            g["dil"] = (c0 - float(r["dilation"])) / c0
            if r["rewired_best"] != "": g["rew"] = (c0 - float(r["rewired_best"])) / c0
        for key, mk, fc, off in (("nl", "o", COL[p], -0.27), ("lin", "o", "white", -0.09), ("dil", "D", "white", 0.09), ("rew", "s", "white", 0.27)):
            if key in g:
                a.vlines(i + off, 0, 100 * g[key], color=COL[p], lw=LW["sec"])
                a.plot(i + off, 100 * g[key], mk, color=COL[p], mfc=fc, ms=MS["cat"], mew=MEW["open"])
    a.axhline(0, color=DARK, lw=LW["zero"])
    a.set_xticks(xs); style.catlabels(a.xaxis, [LABEL[p] for p in CH]); a.set_xlim(-0.6, len(CH) - 0.4)
    a.set_ylabel("RMSD reduction (%)"); a.set_ylim(-9, 45); a.set_title("Comparison with null models", loc="left")
    a.legend(handles=[mkh("o", "nonlinear path"), mkh("D", "isotropic dilation", filled=False), mkh("o", "best-amp. linear", filled=False),
                      mkh("s", "best rewired", filled=False)], loc="upper center", ncol=2, handletextpad=0.1, columnspacing=0.6, borderaxespad=0.1)
    c = ax[1]
    c.axhspan(-0.2, 0.2, color=LIGHT, lw=0, zorder=0)
    for p in CH:
        chi, d = float(TU[p]["chi_010"]), float(TU[p]["delta"])
        c.plot(chi, d, MK[p], color=COL[p], ms=MS["pt"], mec="white", mew=MEW["edge"], zorder=3)
        dx, dy, ha = {"6pwn": (4, -9, "left"), "4wff": (4, 4, "left"), "6mgv": (3, 4, "left"), "4xdk": (4, -9, "left"), "2oar": (-5, -4, "right")}.get(p, (4, 3, "left"))
        c.annotate(LABEL[p], (chi, d), xytext=(dx, dy), ha=ha, textcoords="offset points", fontsize=style.FS, color=COL[p])
    for p in ("6cq8", "6vtk"):
        chi = float(TU[p]["chi_010"]); c.plot(chi, -0.85, "|", color=COL[p], ms=MS["star"], mew=LW["data"])
        c.annotate(LABEL[p], (chi, -0.85), xytext=({"6cq8": 3, "6vtk": -3}[p], 4), ha={"6cq8": "left", "6vtk": "right"}[p], textcoords="offset points", fontsize=style.FS, color=COL[p])
    c.axhline(0, color=DARK, lw=LW["zero"])
    c.set_xlabel(r"$\chi$ ($\varepsilon=0.10$)"); c.set_ylabel(r"$\Delta_{\mathrm{L-NL}}$ (Å)")
    c.set_title(r"$\Delta_{\mathrm{L-NL}}$ vs. $\chi$", loc="left"); c.set_xscale("log"); c.set_ylim(-0.95, 1.0)
    d = ax[2]
    d.axhspan(-0.2, 0.2, color=LIGHT, lw=0, zorder=0)
    for i, p in enumerate(CH):
        pts = [r for r in RB if r["structure"] == p]
        for r in pts:
            j = int(r["order"]); jit = (j - (len(pts) - 1) / 2) * 0.05
            mk = {"rc10": "o", "rc12": "s", "backbone": "^", "load": "x"}[r["kind"]]; fc = "white" if r["kind"] == "rc12" else COL[p]
            d.plot(i + jit, float(r["delta"]), mk, color=COL[p], mfc=fc, ms=MS["line"] if mk != "x" else MS["line"] - 0.5, mew=MEW["open"])
    d.axhline(0, color=DARK, lw=LW["zero"])
    d.set_xticks(xs); style.catlabels(d.xaxis, [LABEL[p] for p in CH]); d.set_xlim(-0.6, len(CH) - 0.4)
    d.set_ylabel(r"$\Delta_{\mathrm{L-NL}}$ (Å)"); d.set_title("Variants", loc="left"); d.set_ylim(-1.0, 1.35)
    d.legend(handles=[mkh("o", "$r_c$ = 10 Å"), mkh("s", "$r_c$ = 12 Å", filled=False), mkh("x", "load construction"), mkh("^", "stiff backbone")],
             loc="upper right", handletextpad=0.1, borderaxespad=0.1)
    for a_, t in zip(ax, "abc"):
        style.letter(a_, t)
    fig.canvas.draw()
    style.top_legend(fig, [chan_handles(CH + ["6cq8", "6vtk"])])
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
