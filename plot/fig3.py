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
                             lam_rel=(r["lam"][0] / lam0) if r.get("lam") else None, max_e=r["max_e"]))
        st.append(dict(structure=p, eps_star=run["eps_star"], step_star=run["step_star"], stable_beyond=int(p != "6b3r"),
                       a_005=run["enl_mem_0.05"]["amp"], sin_005=run["enl_mem_0.05"]["dir"],
                       kappa_005=I[p]["mem_eps0.05"]["kappa"], chi_005=I[p]["mem_eps0.05"]["chi"]))
    style.write_csv(DATA / "path.csv", rows, ["structure", "step", "eps", "amp", "dir", "lam_rel", "max_e"])
    style.write_csv(DATA / "structures.csv", st, ["structure", "eps_star", "step_star", "stable_beyond", "a_005", "sin_005", "kappa_005", "chi_005"])
    style.write_readme(DATA, "fig3 plotting data", "data/derived/paths/<id>_rc10.json and data/derived/summary.json (membrane nodes, r_c = 10 A)", {
        "path.csv": [("structure", "structure id", "-", "label"), ("step", "1-based step along the path", "-", "index"),
                     ("eps", "normalized radial displacement of the membrane nodes", "-", "value"),
                     ("amp", "amplitude ratio a = |u_L| / |u_NL| at the same tension", "-", "value"),
                     ("dir", "direction error sin(theta) between u_L and u_NL", "-", "value"),
                     ("lam_rel", "lowest constrained eigenvalue relative to its reference value", "-", "value"),
                     ("max_e", "largest element strain |e|_max", "-", "value")],
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
    style.apply()
    fig, ax = plt.subplots(2, 3, figsize=(style.W2, 116 * MM), gridspec_kw=dict(wspace=0.42, hspace=0.58, left=0.07, right=0.99, bottom=0.08, top=0.86)); ax = ax.ravel()
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
            w = 1.1 if p in CH else 0.8
            v = x[:n] <= es + 1e-12
            a.plot(x[:n][v], y[:n][v], color=COL[p], lw=w, zorder=3 if p == "6b3r" else 2)
            if stable:
                a.plot(x[x >= es - 1e-12], y[x >= es - 1e-12], color=COL[p], lw=0.5, alpha=0.45, zorder=1)
            j = np.where(v)[0][-1]
            a.plot(x[:n][j], y[:n][j], MK[p], color=COL[p], ms=3.6, mec="white", mew=0.4, zorder=4)
        a.set_xlim(0, XM); a.xaxis.set_major_locator(MaxNLocator(5))
        a.set_xlabel(r"normalised radial displacement $\varepsilon$")

    a = ax[0]; draw(a, "amp"); a.axhline(1, color=GREY, lw=0.5, ls=(0, (2, 2)))
    a.set_ylabel(r"amplitude ratio $a=\|\mathbf{u}_L\|/\|\mathbf{u}_{NL}\|$"); a.set_title("Stiffening"); a.set_ylim(0.9, 4.4)
    a.text(0.97, 0.55, "removed by one scalar", transform=a.transAxes, ha="right", va="top", fontsize=6, color="#555555")
    b = ax[1]; draw(b, "dir")
    b.set_ylabel(r"direction error $\sin\theta$"); b.set_title("Turning"); b.set_ylim(0, 0.75)
    b.text(0.03, 0.94, "not removable by scaling", transform=b.transAxes, ha="left", va="top", fontsize=6, color="#555555")
    c = ax[2]; draw(c, "lam"); c.axhline(1, color=GREY, lw=0.5, ls=(0, (2, 2))); c.axhline(0, color=DARK, lw=0.5)
    x, y, n, es, _ = curves("6b3r", "lam")
    c.annotate("L$_1$", (x[n - 1], y[n - 1]), xytext=(-14, -6), textcoords="offset points", fontsize=6, ha="right", arrowprops=dict(arrowstyle="-", color="k", lw=0.5))
    c.set_ylabel(r"lowest eigenvalue $\lambda_1/\lambda_1(0)$"); c.set_title("Snapping"); c.set_ylim(-0.15, 5.4)
    c.text(0.97, 0.94, r"others: $n_{\rm neg}=0$ to the end", transform=c.transAxes, ha="right", va="top", fontsize=6, color="#555555")
    d = ax[3]; d.plot([1, 2], [1, 2], color="#BDBDBD", lw=0.6, zorder=0)
    for p in ALL:
        k5 = float(ST[p]["kappa_005"]); am = float(ST[p]["a_005"])
        if k5 > -1:
            d.plot(am, 1 / (1 + k5), MK[p], color=COL[p], ms=4.5, mec="white", mew=0.4, zorder=3)
        else:
            d.annotate("", xy=(min(am, 1.98), 1.98), xytext=(min(am, 1.98), 1.80), arrowprops=dict(arrowstyle="-|>", color=COL[p], lw=0.8, mutation_scale=6))
            d.text(min(am, 1.98) - 0.04, 1.95, f"{LABEL[p]}: $\\kappa<-1$", ha="right", va="center", fontsize=5.5, color=COL[p])
    d.set_xlim(1, 2); d.set_ylim(1, 2); d.set_aspect("equal", adjustable="box")
    d.set_xlabel(r"measured $a$ ($\varepsilon=0.05$)"); d.set_ylabel(r"predicted $1/(1+\kappa)$"); d.set_title("Second order predicts stiffening")
    e_ = ax[4]; mm = np.array([0.012, 1.2]); e_.loglog(mm, mm, color="#BDBDBD", lw=0.6, zorder=0)
    for p in ALL:
        e_.plot(float(ST[p]["sin_005"]), float(ST[p]["chi_005"]), MK[p], color=COL[p], ms=4.5, mec="white", mew=0.4, zorder=3)
    e_.set_xlim(*mm); e_.set_ylim(*mm); e_.set_aspect("equal", adjustable="box"); logticks(e_); logticks(e_, "x")
    e_.set_xlabel(r"measured $\sin\theta$ ($\varepsilon=0.05$)"); e_.set_ylabel(r"predicted $\chi$"); e_.set_title("Turning is predictable")
    xs_ = [float(ST[p]["sin_005"]) for p in ALL]; ys_ = [float(ST[p]["chi_005"]) for p in ALL]
    rk = lambda v: np.argsort(np.argsort(v)); rho = np.corrcoef(rk(xs_), rk(ys_))[0, 1]
    e_.text(0.96, 0.05, f"Spearman $\\rho_s$ = {rho:.2f}, $n$ = {len(ALL)}", transform=e_.transAxes, ha="right", va="bottom", fontsize=6, color="#555555")
    f = ax[5]; draw(f, "maxe"); f.axhline(0.5, color=GREY, lw=0.6, ls=(0, (4, 2)))
    f.text(0.03, 0.52, r"$|e|_{\max}=0.5$", transform=f.get_yaxis_transform(), fontsize=6, va="bottom", color="#555555")
    f.set_ylabel(r"max. element strain $|e|_{\max}$"); f.set_ylim(0, 1.05); f.set_title("Strain bounds the others")
    for a_, t in zip(ax, "abcdef"):
        style.letter(a_, t, dx=-0.30, dy=1.05)
    fig.legend(handles=chan_handles(ALL, lw=1.0), loc="upper center", ncol=8, bbox_to_anchor=(0.5, 1.0))
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
