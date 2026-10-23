"""Fig 6 - what the Piezo1 turning delivers (in-plane expansion, axial displacement, global shape).
  python plot/fig6.py extract   (data/derived + src model -> figure_data/fig6)
  python plot/fig6.py plot      (figure_data/fig6 -> results/figures/fig6.*)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import style
from style import COL, GREY, DARK, MM

NAME = "fig6"
DATA = style.ROOT / "figure_data" / NAME


def extract():
    import derived
    from model import model, build_target, kabsch
    S = derived.summary(); p = "6b3r"; M = model(p, 10.0); idx, P0, XE, Delta, info = build_target(p, M)
    Xs = derived.states(f"{p}_rc10"); v = S["runs"][f"{p}_rc10"]["validation"]; R = derived.path(f"{p}_rc10")
    kb = int(np.argmin([abs(r["eps"] - v["eps_best"]) + (0 if r["nl"]["rmsd_tm"] == v["nl"] else 1) for r in R["rows"]]))
    tm = np.isin(idx, M["mem"])
    Xb = Xs[kb][idx]; Rb, tb = kabsch(Xb[tm], P0[tm]); Xb = Xb @ Rb.T + tb
    Re, te = kabsch(XE[tm], P0[tm]); XEs = XE @ Re.T + te
    rows = [dict(node=int(i), chain=M["order"][i][0], resid=int(M["order"][i][1]), tm=int(t), x0=a[0], y0=a[1], z0=a[2], xm=b[0], ym=b[1], zm=b[2], xe=e[0], ye=e[1], ze=e[2])
            for i, t, a, b, e in zip(idx, tm, P0, Xb, XEs)]
    style.write_csv(DATA / "nodes.csv", rows, ["node", "chain", "resid", "tm", "x0", "y0", "z0", "xm", "ym", "zm", "xe", "ye", "ze"])
    A = S["physical_scale"][p]; c = M["m"]["centroid"]
    par = [dict(key="axis_x", value=c[0]), dict(key="axis_y", value=c[1]), dict(key="z_mid", value=M["m"]["z_mid"]), dict(key="best_step", value=kb + 1),
           dict(key="eps_best", value=v["eps_best"]), dict(key="A0_nm2", value=A["A0_nm2"]), dict(key="dA_model_nm2", value=v["dA_best"] / 100),
           dict(key="dA_exp_nm2", value=A["dA_exp_nm2"])]
    style.write_csv(DATA / "params.csv", par, ["key", "value"])
    style.write_readme(DATA, "fig6 plotting data", "src/model.py (Piezo1 6B3R -> 8IXO mapping), data/derived/paths/6b3r_rc10 (best frame), data/derived/summary.json", {
        "nodes.csv": [("node", "C-alpha node index of the closed model", "-", "index"), ("chain", "chain id", "-", "label"), ("resid", "residue number", "-", "index"),
                      ("tm", "node in the transmembrane validation subset", "-", "flag 0/1"),
                      ("x0", "closed-state x", "angstrom", "value"), ("y0", "closed-state y", "angstrom", "value"), ("z0", "closed-state z", "angstrom", "value"),
                      ("xm", "model best frame x, superposed on the TM subset", "angstrom", "value"), ("ym", "model best frame y", "angstrom", "value"),
                      ("zm", "model best frame z", "angstrom", "value"), ("xe", "8IXO x, superposed on the TM subset", "angstrom", "value"),
                      ("ye", "8IXO y", "angstrom", "value"), ("ze", "8IXO z", "angstrom", "value")],
        "params.csv": [("key", "parameter name: axis_x, axis_y (membrane axis, A), z_mid (bilayer midplane, A), best_step, eps_best, A0_nm2, dA_model_nm2, dA_exp_nm2 (outer-shell area, nm^2)", "-", "label"),
                       ("value", "parameter value", "see key", "value")]})


def plot():
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from figcommon import num
    N = style.read_csv(f"figure_data/{NAME}/nodes.csv"); PR = {r["key"]: float(r["value"]) for r in style.read_csv(f"figure_data/{NAME}/params.csv")}
    P0 = np.c_[num(N, "x0"), num(N, "y0"), num(N, "z0")]; X = np.c_[num(N, "xm"), num(N, "ym"), num(N, "zm")]; XE = np.c_[num(N, "xe"), num(N, "ye"), num(N, "ze")]
    tm = num(N, "tm").astype(bool); c = np.array([PR["axis_x"], PR["axis_y"]])
    style.apply()
    fig = plt.figure(figsize=(style.W2, 70 * MM))
    axa = fig.add_axes([0.0, 0.02, 0.33, 0.86]); axb = fig.add_axes([0.42, 0.15, 0.30, 0.70]); axc = fig.add_axes([0.81, 0.15, 0.19, 0.70])
    q = np.where(tm)[0][::3]
    xy0 = P0[q, :2] - c[:2]
    axa.scatter(P0[tm, 0] - c[0], P0[tm, 1] - c[1], s=0.8, c="#BDBDBD", lw=0, zorder=1)
    dm = (X[q, :2] - P0[q, :2]); de = (XE[q, :2] - P0[q, :2])
    axa.quiver(xy0[:, 0], xy0[:, 1], de[:, 0], de[:, 1], angles="xy", scale_units="xy", scale=1, color=style.EXP, width=0.0035, headwidth=3, headlength=3.5, zorder=2, alpha=0.9)
    axa.quiver(xy0[:, 0], xy0[:, 1], dm[:, 0], dm[:, 1], angles="xy", scale_units="xy", scale=1, color=COL["6b3r"], width=0.0035, headwidth=3, headlength=3.5, zorder=3, alpha=0.9)
    axa.set_aspect("equal"); axa.axis("off")
    xmn = (P0[tm, 0] - c[0]).min(); ymn = (P0[tm, 1] - c[1]).min()
    axa.plot([xmn, xmn + 20], [ymn - 6] * 2, color=DARK, lw=1.0); axa.text(xmn + 10, ymn - 8, "20 Å", ha="center", va="top", fontsize=style.FS)

    axa.set_title("In-plane displacement, TM C$\\alpha$", loc="left")
    r0 = np.linalg.norm(P0[:, :2] - c[:2], axis=1); bins = np.arange(0, r0.max() + 8, 8)
    for Y, col, lab in ((X, COL["6b3r"], "model"), (XE, style.EXP, "8IXO")):
        dz = Y[:, 2] - P0[:, 2]; k = np.digitize(r0, bins)
        mids, med, q1, q3 = [], [], [], []
        for b_ in range(1, len(bins)):
            m = k == b_
            if m.sum() >= 15:
                mids.append(0.5 * (bins[b_ - 1] + bins[b_])); v = dz[m]; med.append(np.median(v)); q1.append(np.percentile(v, 25)); q3.append(np.percentile(v, 75))
        axb.fill_between(mids, q1, q3, color=col, alpha=0.18, lw=0); axb.plot(mids, med, color=col, lw=1.2, marker="o", ms=2.5, mec="white", mew=0.3, label=lab)
    axb.axhline(0, color=GREY, lw=0.5, ls=(0, (2, 2)))
    axb.set_xlabel("in-plane radius $r$ in closed state (Å)"); axb.set_ylabel(r"axial displacement $\Delta z$ (Å)")
    axb.set_title("Axial flattening not reproduced", loc="left")

    def desc(Y):
        rr = np.linalg.norm(Y[tm, :2] - c[:2], axis=1); return rr.mean(), np.sqrt(((Y[:, 2] - Y[:, 2].mean()) ** 2).mean())
    r_0, z_0 = desc(P0); r_m, z_m = desc(X); r_e, z_e = desc(XE); A0 = PR["A0_nm2"]
    groups = [("mean $r$\n(TM)", r_0, r_m, r_e), ("axial RMS", z_0, z_m, z_e), ("shell area", A0, A0 + PR["dA_model_nm2"], A0 + PR["dA_exp_nm2"])]
    for i, (lab, a0, am, ae) in enumerate(groups):
        for j, (val_, col) in enumerate(((am / a0, COL["6b3r"]), (ae / a0, style.EXP))):
            axc.bar(i + (j - 0.5) * 0.36, val_ - 1, width=0.34, bottom=1, color=col, lw=0)
            axc.text(i + (j - 0.5) * 0.36, max(val_, 1) + 0.006, f"{(am if j == 0 else ae):.0f}", ha="center", va="bottom", fontsize=style.FS, rotation=90)
    axc.axhline(1, color=DARK, lw=0.6)
    axc.set_xticks(range(3)); axc.set_xticklabels([g[0] for g in groups], fontsize=style.FS)
    axc.set_ylabel("relative to closed"); axc.set_ylim(0.85, 1.32); axc.set_xlim(-0.6, 2.6)
    axc.set_title("Global shape", loc="left")
    for a_, t, dx in ((axa, "a", 0.0), (axb, "b", -0.2), (axc, "c", -0.38)):
        style.letter(a_, t)
    style.top_legend(fig, [[Line2D([], [], color=COL["6b3r"], lw=1.4, label="Piezo1 model, best frame"),
                            Line2D([], [], color=style.EXP, lw=1.4, label="experiment, closed → 8IXO")]], y=0.93)
    style.save(fig, NAME)
    style.describe(NAME, "Fig. 6 Piezo1 at its best frame (eps = {{eps}}). Mean in-plane TM radius {{r0}} -> {{rm}} A in the model and {{re}} A in 8IXO "
                   "({{rfrac}} % of the experimental increase); axial RMS spread {{z0}} -> {{zm}} A (8IXO {{ze}} A); outer-shell area change "
                   "{{dam}} nm^2 (model) vs {{dae}} nm^2 (8IXO).",
                   dict(eps=f"{PR['eps_best']:.3f}", r0=f"{r_0:.1f}", rm=f"{r_m:.1f}", re=f"{r_e:.1f}", rfrac=f"{100 * (r_m - r_0) / (r_e - r_0):.0f}",
                        z0=f"{z_0:.1f}", zm=f"{z_m:.1f}", ze=f"{z_e:.1f}", dam=f"{PR['dA_model_nm2']:.1f}", dae=f"{PR['dA_exp_nm2']:.1f}"),
                   [f"figure_data/{NAME}/nodes.csv", f"figure_data/{NAME}/params.csv"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
