"""Fig 4 - validation against the partner structures (r_c = 10 A).
  python plot/fig4.py extract   (data/derived -> figure_data/fig4)
  python plot/fig4.py plot      (figure_data/fig4 -> results/figures/fig4.*)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import style
from style import CH, COL, LABEL, GREY, LIGHT, DARK, MM

NAME = "fig4"
DATA = style.ROOT / "figure_data" / NAME


def extract():
    import derived
    S = derived.summary(); N = S["nulls"]; nl, lin, ch = [], [], []
    for p in CH:
        R = derived.path(f"{p}_rc10"); run = S["runs"][f"{p}_rc10"]; v = run["validation"]
        for i, r in enumerate(R["rows"]):
            nl.append(dict(structure=p, step=i + 1, eps=r["eps"], rmsd_tm=r["nl"]["rmsd_tm"]))
        for g in R["pre"]["target"]["linear_grid"]:
            lin.append(dict(structure=p, eps=g["eps"], rmsd_tm=g["rmsd_tm"]))
        rw = [r["best_tm"] for r in N.get(p, {}).get("rewired", []) if "best_tm" in r]
        ch.append(dict(structure=p, closed=v["closed"], nl_best=v["nl"], lin_best=v["lin"], eps_best=v["eps_best"], eps_star=run["eps_star"],
                       stable_steps=run["step_star"] if p == "6b3r" else len(R["rows"]), limit_point=int(p == "6b3r" and bool(S.get("arclength"))),
                       dilation=N[p]["dilation"]["best_tm"] if p in N else None, rewired_min=min(rw) if rw else None, rewired_max=max(rw) if rw else None))
    style.write_csv(DATA / "nonlinear.csv", nl, ["structure", "step", "eps", "rmsd_tm"])
    style.write_csv(DATA / "linear.csv", lin, ["structure", "eps", "rmsd_tm"])
    style.write_csv(DATA / "channels.csv", ch, ["structure", "closed", "nl_best", "lin_best", "eps_best", "eps_star", "stable_steps", "limit_point", "dilation", "rewired_min", "rewired_max"])
    style.write_readme(DATA, "fig4 plotting data", "data/derived/paths/<id>_rc10.json, data/derived/summary.json (validation, nulls)", {
        "nonlinear.csv": [("structure", "structure id", "-", "label"), ("step", "1-based step along the path", "-", "index"),
                          ("eps", "normalized radial displacement", "-", "value"), ("rmsd_tm", "TM C-alpha RMSD to the partner structure", "angstrom", "value")],
        "linear.csv": [("structure", "structure id", "-", "label"), ("eps", "normalized radial displacement of the scaled linear response", "-", "value"),
                       ("rmsd_tm", "TM C-alpha RMSD of the linear response to the partner", "angstrom", "value")],
        "channels.csv": [("structure", "structure id", "-", "label"), ("closed", "TM RMSD of the closed structure to the partner", "angstrom", "value"),
                         ("nl_best", "best TM RMSD of the nonlinear path within eps <= eps_star", "angstrom", "value"),
                         ("lin_best", "best TM RMSD of the best-amplitude linear response", "angstrom", "value"),
                         ("eps_best", "eps of the best nonlinear frame", "-", "value"), ("eps_star", "end of the validity range", "-", "value"),
                         ("stable_steps", "number of rows on the stable branch (Piezo1: up to the limit point L1)", "-", "count"),
                         ("limit_point", "the path ends at a limit point", "-", "flag 0/1"),
                         ("dilation", "best TM RMSD of an isotropic in-plane dilation", "angstrom", "value"),
                         ("rewired_min", "best TM RMSD over three rewired networks (lowest)", "angstrom", "value"),
                         ("rewired_max", "best TM RMSD over three rewired networks (highest)", "angstrom", "value")]})


def plot():
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.ticker import MaxNLocator
    from figcommon import num
    NL = style.read_csv(f"figure_data/{NAME}/nonlinear.csv"); LI = style.read_csv(f"figure_data/{NAME}/linear.csv")
    C = {r["structure"]: r for r in style.read_csv(f"figure_data/{NAME}/channels.csv")}
    style.apply()
    fig, axs = plt.subplots(2, 3, figsize=(style.W2, 104 * MM), gridspec_kw=dict(wspace=0.30, hspace=0.50, left=0.07, right=0.99, top=0.86))
    f = lambda r, k: float(r[k]) if r[k] != "" else None
    for a, p, t in zip(axs.ravel(), CH, "abcdef"):
        c = C[p]; rr = [r for r in NL if r["structure"] == p]; E = num(rr, "eps"); T = num(rr, "rmsd_tm")
        ll = [r for r in LI if r["structure"] == p]; ge, gt = num(ll, "eps"), num(ll, "rmsd_tm"); es = f(c, "eps_star")
        xmax = min(max(E.max(), es) * 1.04, 0.42, max(2.2 * es, 0.06) if p in ("4xdk", "4wff") else 1)
        a.axvspan(es, xmax * 1.2, color=LIGHT, lw=0, zorder=0)
        a.axhline(f(c, "closed"), color=GREY, lw=0.6, ls=(0, (4, 2)), zorder=1)
        if c["dilation"] != "":
            a.axhline(f(c, "dilation"), color="#7F7F7F", lw=0.7, ls=(0, (1, 1.5)), zorder=1)
            if c["rewired_min"] != "":
                a.axhspan(f(c, "rewired_min"), f(c, "rewired_max"), color=COL[p], alpha=0.18, lw=0, zorder=1)
        m = ge <= xmax
        a.plot(ge[m], gt[m], color=COL[p], lw=0.9, ls=(0, (3, 1.6)), zorder=2)
        ks = int(c["stable_steps"])
        if ks < len(E):
            a.plot(E[ks - 1:], T[ks - 1:], color="#9E9E9E", lw=0.5, zorder=2)
        a.plot(E[:ks], T[:ks], color=COL[p], lw=1.2, zorder=3)
        a.plot(f(c, "eps_best"), f(c, "nl_best"), marker="*", color="k", ms=7, mec="white", mew=0.4, zorder=5, ls="")
        if c["limit_point"] == "1":
            k = ks - 1; a.plot(E[k], T[k], marker="|", color="k", ms=8, mew=1.0, zorder=5)
            a.annotate("L$_1$", (E[k], T[k]), xytext=(-10, 6), textcoords="offset points", fontsize=style.FS)
        a.set_xlim(0, xmax); a.set_title(LABEL[p], color=COL[p], fontweight="bold", loc="left")
        lo = min(T.min(), gt[m].min(), f(c, "closed"), f(c, "dilation") if c["dilation"] != "" else 1e9)
        hi = max(f(c, "closed"), max(T[:ks][E[:ks] <= xmax]))
        pad = 0.10 * (hi - lo + 0.2); a.set_ylim(lo - pad, hi + pad)
        a.yaxis.set_major_locator(MaxNLocator(4)); a.xaxis.set_major_locator(MaxNLocator(4))
        a.set_title(f"{f(c, 'closed'):.2f}→{f(c, 'nl_best'):.2f} Å, lin. {f(c, 'lin_best'):.2f}", loc="right", fontsize=style.FS, color=style.NOTE)
        if t in "ad": a.set_ylabel(r"RMSD$_{\rm TM}$ to partner (Å)")
        if t in "def": a.set_xlabel(r"normalised radial displacement $\varepsilon$")
        style.letter(a, t)
    h = [Line2D([], [], color="k", lw=1.2, label="nonlinear tension path"),
         Line2D([], [], color="k", lw=0.9, ls=(0, (3, 1.6)), label="linear response (own $\\varepsilon$)"),
         Line2D([], [], color="#7F7F7F", lw=0.7, ls=(0, (1, 1.5)), label="best isotropic dilation"),
         Patch(color="k", alpha=0.18, label="rewired networks (3 seeds)"),
         Line2D([], [], color=GREY, lw=0.6, ls=(0, (4, 2)), label="closed state"),
         Line2D([], [], ls="", marker="*", color="k", ms=6, label=r"best frame, $\varepsilon\leq\varepsilon^*$"),
         Patch(color=LIGHT, label=r"$\varepsilon>\varepsilon^*$")]
    fig.legend(handles=h, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.0), handletextpad=0.4)
    style.save(fig, NAME)
    pz = C["6b3r"]
    style.describe(NAME, "Fig. 4 validation against the partner structures (TM C-alpha RMSD, r_c = 10 A) for {{n}} channels. Piezo1: closed {{pz_closed}} A, "
                   "nonlinear path {{pz_nl}} A, best-amplitude linear response {{pz_lin}} A, isotropic dilation {{pz_dil}} A, rewired networks {{pz_rmin}} to {{pz_rmax}} A; "
                   "its stable branch ends at the limit point L1.",
                   dict(n=len(CH), pz_closed=style.fnum(pz["closed"]), pz_nl=style.fnum(pz["nl_best"]), pz_lin=style.fnum(pz["lin_best"]),
                        pz_dil=style.fnum(pz["dilation"]), pz_rmin=style.fnum(pz["rewired_min"]), pz_rmax=style.fnum(pz["rewired_max"])),
                   [f"figure_data/{NAME}/nonlinear.csv", f"figure_data/{NAME}/linear.csv", f"figure_data/{NAME}/channels.csv"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
