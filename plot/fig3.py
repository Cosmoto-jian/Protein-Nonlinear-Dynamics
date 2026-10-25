"""Fig 3 - three departures from linearization along the tension path (stiffening, turning, snapping).
  python plot/fig3.py extract   (data/derived -> figure_data/fig3)
  python plot/fig3.py plot      (figure_data/fig3 -> results/figures/fig3.*)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import style
from style import CH, ALL, COL, MK, LABEL, GREY, DARK, MM

NAME = "fig3"
DATA = style.ROOT / "figure_data" / NAME


def extract():
    import derived
    S = derived.summary(); I = S["indicator"]; rows, st = [], []
    for p in ALL:
        R = derived.path(f"{p}_rc10"); lam0 = (R["pre"].get("lam0") or [None])[0]; run = S["runs"][f"{p}_rc10"]
        for i, r in enumerate(R["rows"]):
            q = r.get("enl_mem")
            rows.append(dict(structure=p, step=i + 1, eps=r["eps"], amp=q["amp"] if q else None, dir=q["dir"] if q else None,
                             lam_rel=(r["lam"][0] / lam0) if r.get("lam") else None, max_e=r["max_e"],
                             n_neg=(r.get("inertia") or {}).get("n_neg")))
        st.append(dict(structure=p, eps_star=run["eps_star"], step_star=run["step_star"], stable_beyond=int(p != "6b3r"),
                       a_005=run["enl_mem_0.05"]["amp"], sin_005=run["enl_mem_0.05"]["dir"],
                       kappa_005=I[p]["mem_eps0.05"]["kappa"], chi_005=I[p]["mem_eps0.05"]["chi"]))
    style.write_csv(DATA / "path.csv", rows, ["structure", "step", "eps", "amp", "dir", "lam_rel", "max_e", "n_neg"])
    style.write_csv(DATA / "structures.csv", st, ["structure", "eps_star", "step_star", "stable_beyond", "a_005", "sin_005", "kappa_005", "chi_005"])
    style.write_readme(DATA, "fig3 plotting data", "data/derived/paths/<id>_rc10.json and data/derived/summary.json (membrane nodes, r_c = 10 A)", {
        "path.csv": [("structure", "structure id", "-", "label"), ("step", "1-based step along the path", "-", "index"),
                     ("eps", "normalized radial displacement of the membrane nodes", "-", "value"),
                     ("amp", "amplitude ratio a = |u_L| / |u_NL| at the same tension", "-", "value"),
                     ("dir", "direction error sin(theta) between u_L and u_NL", "-", "value"),
                     ("lam_rel", "lowest constrained eigenvalue relative to its reference value (true lowest: the shift-invert shift is chosen "
                                 "from the inertia count, so it is negative wherever n_neg > 0, i.e. past the Piezo1 limit point)", "-", "value"),
                     ("max_e", "largest element strain |eta|_max", "-", "value"),
                     ("n_neg", "negative eigenvalues of the constrained tangent (inertia count)", "-", "count")],
        "structures.csv": [("structure", "structure id", "-", "label"), ("eps_star", "end of the validity range", "-", "value"),
                           ("step_star", "step at eps_star; for Piezo1 the limit point L1, later rows are the unstable continuation", "-", "index"),
                           ("stable_beyond", "rows beyond eps_star lie on a stable branch and are drawn thin", "-", "flag 0/1"),
                           ("a_005", "measured amplitude ratio at eps = 0.05", "-", "value"), ("sin_005", "measured sin(theta) at eps = 0.05", "-", "value"),
                           ("kappa_005", "second-order amplitude indicator kappa at eps = 0.05", "-", "value"),
                           ("chi_005", "second-order direction indicator chi at eps = 0.05", "-", "value")]})


def plot():
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    from figcommon import logticks, chan_handles, num
    P = style.read_csv(f"figure_data/{NAME}/path.csv"); ST = {r["structure"]: r for r in style.read_csv(f"figure_data/{NAME}/structures.csv")}
    from style import LW, MS, MEW
    fig, ax = style.figure(2, 3, height_mm=88); ax = ax.ravel()
    XM = 0.25

    def curves(p, key):
        rr = [r for r in P if r["structure"] == p]; E = num(rr, "eps"); ks = int(ST[p]["step_star"]); es = float(ST[p]["eps_star"])
        if key in ("amp", "dir"):
            x = np.r_[0.0, E]; y = np.r_[1.0 if key == "amp" else 0.0, num(rr, key)]; n = ks + 1
        elif key == "lam":
            x = E; y = num(rr, "lam_rel"); n = ks
        else:
            x = E; y = num(rr, "max_e"); n = ks
        return x, y, n, es, ST[p]["stable_beyond"] == "1"

    def draw(a, key):
        for p in ALL:
            x, y, n, es, stable = curves(p, key)
            w = LW["data"] if p in CH else LW["sec"]
            v = x[:n] <= es + 1e-12
            a.plot(x[:n][v], y[:n][v], color=COL[p], lw=w, zorder=3 if p == "6b3r" else 2)
            if stable:
                a.plot(x[x >= es - 1e-12], y[x >= es - 1e-12], color=COL[p], lw=LW["thin"], alpha=0.45, zorder=1)
            j = np.where(v)[0][-1]
            a.plot(x[:n][j], y[:n][j], MK[p], color=COL[p], ms=MS["line"], mec="white", mew=MEW["edge"], zorder=4)
        a.set_xlim(0, XM); a.xaxis.set_major_locator(MaxNLocator(5))
        a.set_xlabel(r"$\varepsilon$")

    a = ax[0]; draw(a, "amp"); a.axhline(1, color=GREY, lw=LW["zero"], ls=(0, (2, 2)))
    a.set_ylabel(r"amplitude ratio $a$"); a.set_title("Stiffening", loc="left"); a.set_ylim(0.9, 4.4)
    a.text(0.97, 0.62, "removed by\none scalar", transform=a.transAxes, ha="right", va="top", fontsize=style.FS, color=style.NOTE)
    b = ax[1]; draw(b, "dir")
    b.set_ylabel(r"direction error $\sin\theta$"); b.set_title("Turning", loc="left"); b.set_ylim(0, 0.82)
    b.text(0.03, 0.98, "not removable\nby scaling", transform=b.transAxes, ha="left", va="top", fontsize=style.FS, color=style.NOTE)
    c = ax[2]; draw(c, "lam"); c.axhline(1, color=GREY, lw=LW["zero"], ls=(0, (2, 2))); c.axhline(0, color=DARK, lw=LW["zero"])
    x, y, n, es, _ = curves("6b3r", "lam")
    nn6 = num([r for r in P if r["structure"] == "6b3r"], "n_neg")
    YLO = -0.6; j1 = n
    while j1 < len(nn6) and nn6[j1] > 0 and y[j1 - 1] >= YLO:   # unstable branch past L1 (n_neg > 0): the descent of lambda_1
        j1 += 1                                                  # below zero, drawn until it leaves the axes (clipped)
    c.plot(x[n - 1:j1], y[n - 1:j1], color=COL["6b3r"], lw=LW["sec"], ls=(0, (1, 1.2)), zorder=3)
    c.annotate("L$_1$", (x[n - 1], y[n - 1]), xytext=(10, -6), textcoords="offset points", fontsize=style.FS, ha="left", arrowprops=dict(arrowstyle="-", color="k", lw=LW["zero"]))
    c.set_ylabel(r"$\lambda_1/\lambda_1(0)$"); c.set_title("Snapping", loc="left"); c.set_ylim(YLO, 6.4)
    c.text(0.97, 0.98, "others:\n" + r"$n_{\rm neg}=0$ to the end", transform=c.transAxes, ha="right", va="top", fontsize=style.FS, color=style.NOTE)
    d = ax[3]; d.plot([1, 2], [1, 2], color="#BDBDBD", lw=LW["ref"], zorder=0)
    for p in ALL:
        k5 = float(ST[p]["kappa_005"]); am = float(ST[p]["a_005"])
        if k5 > -1:
            d.plot(am, 1 / (1 + k5), MK[p], color=COL[p], ms=MS["pt"], mec="white", mew=MEW["edge"], zorder=3)
        else:
            d.annotate("", xy=(min(am, 1.98), 1.98), xytext=(min(am, 1.98), 1.80), arrowprops=dict(arrowstyle="-|>", color=COL[p], lw=LW["sec"], mutation_scale=6))
            d.text(min(am, 1.98) - 0.04, 1.89, f"{LABEL[p]}: $\\kappa<-1$", ha="right", va="center", fontsize=style.FS, color=COL[p])
    d.set_xlim(1, 2); d.set_ylim(1, 2)
    d.set_xlabel(r"measured $a$ ($\varepsilon=0.05$)"); d.set_ylabel(r"estimate $1/(1+\kappa)$"); d.set_title("Second-order amplitude", loc="left")
    e_ = ax[4]; mm = np.array([0.012, 1.2]); e_.loglog(mm, mm, color="#BDBDBD", lw=LW["ref"], zorder=0)
    for p in ALL:
        e_.plot(float(ST[p]["sin_005"]), float(ST[p]["chi_005"]), MK[p], color=COL[p], ms=MS["pt"], mec="white", mew=MEW["edge"], zorder=3)
    e_.set_xlim(*mm); e_.set_ylim(*mm); logticks(e_); logticks(e_, "x")
    e_.set_xlabel(r"measured $\sin\theta$ ($\varepsilon=0.05$)"); e_.set_ylabel(r"indicator $\chi$"); e_.set_title("Second-order direction", loc="left")
    xs_ = [float(ST[p]["sin_005"]) for p in ALL]; ys_ = [float(ST[p]["chi_005"]) for p in ALL]
    rk = lambda v: np.argsort(np.argsort(v)); rho = np.corrcoef(rk(xs_), rk(ys_))[0, 1]
    e_.text(0.04, 0.95, f"$\\rho_s$ = {rho:.2f}, $n$ = {len(ALL)}", transform=e_.transAxes, ha="left", va="top", fontsize=style.FS, color=style.NOTE)
    f = ax[5]; draw(f, "maxe"); f.axhline(0.5, color=GREY, lw=LW["ref"], ls=(0, (4, 2)))
    f.set_ylabel(r"$|\eta|_{\max}$"); f.set_ylim(0, 1.05); f.set_title("Largest element strain", loc="left")
    for a_, t in zip(ax, "abcdef"):
        style.letter(a_, t)
    from matplotlib.lines import Line2D
    enc = [Line2D([], [], color=DARK, lw=LW["data"], marker="o", ms=MS["line"], mec="white", mew=MEW["edge"], markevery=[-1], label=r"path to $\varepsilon^*$ (marker: end of validity)"),
           Line2D([], [], color=DARK, lw=LW["thin"], alpha=0.45, label=r"beyond $\varepsilon^*$, still stable")]
    fig.canvas.draw()
    style.top_legend(fig, [chan_handles(ALL), enc])
    style.save(fig, NAME)
    stiff = sum(float(ST[p]["a_005"]) > 1 for p in ALL); kneg = sum(float(ST[p]["kappa_005"]) < 0 for p in ALL)
    style.describe(NAME, "Fig. 3 departures from linearization along the tension path (r_c = 10 A, membrane nodes, {{n}} structures). "
                   "Stiffening: a > 1 at eps = 0.05 in {{n_stiff}} structures and kappa < 0 in {{n_kneg}}. Turning: chi agrees in rank with the measured "
                   "sin(theta) at eps = 0.05 (Spearman {{rho}}). Snapping: only Piezo1 reaches a limit point; its lowest eigenvalue falls to {{lam_l1}} of the "
                   "reference value at L1.",
                   dict(n=len(ALL), n_stiff=stiff, n_kneg=kneg, rho=f"{rho:.2f}", lam_l1=f"{curves('6b3r', 'lam')[1][int(ST['6b3r']['step_star']) - 1]:.2f}"),
                   [f"figure_data/{NAME}/path.csv", f"figure_data/{NAME}/structures.csv"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
