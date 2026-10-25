"""Fig 7 - the Piezo1 tension path ends at a limit point.
  python plot/fig7.py extract   (data/derived -> figure_data/fig7)
  python plot/fig7.py plot      (figure_data/fig7 -> results/figures/fig7.*)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import style
from style import COL, DARK, MM

NAME = "fig7"
DATA = style.ROOT / "figure_data" / NAME


def extract():
    import derived
    L = derived.path("6b3r_rc10_loadcontrol"); A = derived.path("6b3r_rc10_arclength"); SN = derived.path("6b3r_rc10_snap")
    style.write_csv(DATA / "load_control.csv", [dict(eps=r["eps"], tau=r["tau"]) for r in L["rows"]], ["eps", "tau"])
    lam0 = derived.path("6b3r_rc10")["pre"]["lam0"][0]
    lk = lambda q, i: (q["lam"][i] if q["lam"] and len(q["lam"]) > i else None)
    pts = [dict(point=k, eps=q["eps"], tau=q["tau"], dlam_ds=q["dlam_ds"], n_neg=q["inertia"]["n_neg"], lam1=lk(q, 0), lam2=lk(q, 1), lam3=lk(q, 2),
                lam0=lam0, max_e=q["max_e"]) for k, q in enumerate(A["points"])]
    style.write_csv(DATA / "continuation.csv", pts, ["point", "eps", "tau", "dlam_ds", "n_neg", "lam1", "lam2", "lam3", "lam0", "max_e"])
    po = SN["post_snap"]
    style.write_csv(DATA / "post_snap.csv", [dict(eps=po["eps"], tau=po["tau"], max_e=po["max_e"])], ["eps", "tau", "max_e"])
    top = [dict(rank=k + 1, chain=q["i"][0], res_i=q["i"][1], res_j=q["j"][1], e_pre=q["e_pre"], e_post=q["e_post"], backbone=int(bool(q["backbone"])))
           for k, q in enumerate(SN["snap_top_elements"][:10])]
    style.write_csv(DATA / "snap_elements.csv", top, ["rank", "chain", "res_i", "res_j", "e_pre", "e_post", "backbone"])
    style.write_readme(DATA, "fig7 plotting data", "data/derived/paths/6b3r_rc10_loadcontrol.json, _arclength.json, _snap.json", {
        "load_control.csv": [("eps", "normalized radial displacement, load-controlled Newton path", "-", "value"), ("tau", "membrane tension", "model units", "value")],
        "continuation.csv": [("point", "continuation point index", "-", "index"), ("eps", "normalized radial displacement", "-", "value"),
                             ("tau", "membrane tension", "model units", "value"), ("dlam_ds", "load-parameter component of the unit tangent", "-", "value"),
                             ("n_neg", "negative eigenvalues of the constrained tangent (inertia count)", "-", "count"),
                             ("lam1", "lowest eigenvalue returned by shift-invert Lanczos (sigma = -1e-4)", "model units", "value"),
                             ("lam2", "second eigenvalue returned by the same solve", "model units", "value"),
                             ("lam3", "third eigenvalue returned by the same solve", "model units", "value"),
                             ("lam0", "lowest constrained eigenvalue at the reference state x0 (rc10 path)", "model units", "value"),
                             ("max_e", "largest element strain", "-", "value")],
        "post_snap.csv": [("eps", "normalized radial displacement of the post-snap equilibrium (explicit VFIFE from L1)", "-", "value"),
                          ("tau", "membrane tension of the post-snap equilibrium", "model units", "value"), ("max_e", "largest element strain", "-", "value")],
        "snap_elements.csv": [("rank", "rank by strain change in the snap", "-", "index"), ("chain", "chain of both residues", "-", "label"),
                              ("res_i", "first residue of the element", "-", "index"), ("res_j", "second residue of the element", "-", "index"),
                              ("e_pre", "element strain at the limit point", "-", "value"), ("e_post", "element strain at the post-snap equilibrium", "-", "value"),
                              ("backbone", "virtual backbone bond", "-", "flag 0/1")]})


def plot():
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from figcommon import num
    L = style.read_csv(f"figure_data/{NAME}/load_control.csv"); A = style.read_csv(f"figure_data/{NAME}/continuation.csv")
    tp = style.read_csv(f"figure_data/{NAME}/snap_elements.csv")
    from style import LW, MS, MEW
    fig, ax = style.figure(1, 4, height_mm=54, gridspec_kw=dict(width_ratios=[1.05, 1.1, 1.0, 0.95])); axa, axb, axc, axd = ax[0]
    col = COL["6b3r"]
    e = num(A, "eps"); t = num(A, "tau"); nn = num(A, "n_neg").astype(int); dl = num(A, "dlam_ds")
    folds = [i for i in range(1, len(dl)) if np.sign(dl[i]) != np.sign(dl[i - 1])]
    axa.plot(num(L, "eps"), num(L, "tau"), "o-", color=col, mfc="white", ms=MS["small"], mew=MEW["edge"] + 0.2, lw=LW["thin"])
    axa.plot(e[folds[0]], t[folds[0]], "v", color="k", ms=MS["cat"]); axa.annotate("L$_1$", (e[folds[0]], t[folds[0]]), xytext=(-12, -2), ha="right", va="center", textcoords="offset points", fontsize=style.FS)
    axa.set_xlabel(r"$\varepsilon$"); axa.set_ylabel(r"$\tau$"); axa.set_title("Load control", loc="left")
    PS = style.read_csv(f"figure_data/{NAME}/post_snap.csv")[0]
    st = np.r_[nn[1:] == 0, nn[-1] == 0]          # segment i -> i+1 is stable when node i+1 is
    i0 = 0
    for i in range(1, len(t)):                     # one line per contiguous run, so the dash pattern is visible
        if i == len(t) - 1 or st[i] != st[i0]:
            j = i + 1
            axb.plot(e[i0:j], t[i0:j], color=col if st[i0] else "#7F7F7F", lw=LW["data"] if st[i0] else LW["sec"], ls="-" if st[i0] else (0, (2, 1.2)),
                     zorder=2 if st[i0] else 3)
            i0 = i
    off = {0: (4, 1, "left", "bottom"), 1: (-4, 2, "right", "bottom"), 2: (5, -3, "left", "top"), 3: (-4, 2, "right", "bottom")}
    for j, i in enumerate(folds):
        axb.plot(e[i], t[i], "v" if dl[i - 1] > 0 else "^", color="k", ms=MS["line"], zorder=4)
        dx, dy, ha, va = off.get(j, (3, 2, "left", "bottom"))
        axb.annotate(f"L$_{j + 1}$", (e[i], t[i]), xytext=(dx, dy), textcoords="offset points", fontsize=style.FS, ha=ha, va=va)
    axb.plot(float(PS["eps"]), float(PS["tau"]), "*", color="k", mfc="white", ms=MS["star"], mew=MEW["open"], zorder=5)
    axb.set_xlabel(r"$\varepsilon$"); axb.set_ylabel(r"$\tau$"); axb.set_title("Continuation", loc="left"); axb.margins(y=0.12)
    axb.legend(handles=[Line2D([], [], color=col, lw=LW["data"], label="stable"), Line2D([], [], color="#7F7F7F", lw=LW["sec"], ls=(0, (2, 1.2)), label="$n_{\\rm neg}$ = 1"),
                        Line2D([], [], ls="", marker="*", color="k", mfc="white", ms=MS["star"] - 1, mew=MEW["open"], label="post-snap")],
               loc="upper left", borderaxespad=0.1)
    i1 = folds[0]; w = np.arange(max(0, i1 - 10), min(len(A), i1 + 12)); l0 = float(A[0]["lam0"])
    lo, hi = -8.0, 7.5
    axc.bar(w - i1, np.where(nn[w] > 0, hi - lo, 0), bottom=lo, width=1.0, color="#E0E0E0", lw=0, zorder=0)
    for key, ls_, mk in (("lam1", "-", "o"), ("lam2", (0, (2, 1)), "s"), ("lam3", (0, (1, 1)), "D")):
        axc.plot(w - i1, num(A, key)[w] / l0, marker=mk, ls=ls_, color=col, ms=MS["small"], lw=LW["sec"], mec="white", mew=MEW["edge"], zorder=3)
    axc.axhline(0, color=DARK, lw=LW["zero"])
    axc.set_ylim(lo, hi); axc.set_xlabel("step from L$_1$"); axc.set_ylabel(r"$\lambda_k/\lambda_1(0)$")
    axc.legend(handles=[Line2D([], [], color=col, marker=m_, ls=l_, ms=MS["small"], lw=LW["sec"], label=lb) for m_, l_, lb in
                        (("o", "-", "$k$ = 1"), ("s", (0, (2, 1)), "2"), ("D", (0, (1, 1)), "3"))], loc="lower left", ncol=3, borderaxespad=0.1,
               handlelength=1.4, columnspacing=0.6)
    axc.set_title("Near L$_1$", loc="left")
    de = num(tp, "e_post") - num(tp, "e_pre"); bb = num(tp, "backbone").astype(bool)
    axd.barh(np.arange(len(tp))[::-1], de, color=[col if b else "#9E9E9E" for b in bb], height=0.7)
    axd.set_yticks(np.arange(len(tp))[::-1]); axd.set_yticklabels([f"{q['res_i']}–{q['res_j']}" for q in tp], fontsize=style.FS)
    axd.axvline(0, color=DARK, lw=LW["zero"]); axd.set_ylim(-2.7, len(tp) - 0.4)
    axd.set_xlabel(r"$\Delta\eta$"); axd.set_title("Local snap (" + tp[0]["chain"] + ")", loc="left")
    axd.legend(handles=[Patch(color=col, label="backbone"), Patch(color="#9E9E9E", label="contact")], loc="lower right", handlelength=0.9, borderaxespad=0.1)
    for a_, tt, dx in ((axa, "a", -0.36), (axb, "b", -0.30), (axc, "c", -0.42), (axd, "d", -0.75)):
        style.letter(a_, tt)
    style.save(fig, NAME)
    style.describe(NAME, "Fig. 7 the Piezo1 tension path ends at a limit point. Continuation over {{n}} points shows {{nf}} folds; L1 at tau = {{t1}} "
                   "(eps = {{e1}}), where the inertia count changes from 0 to 1. The ten elements whose strain changes most in the snap lie in chain {{ch}} "
                   "(residues {{rmin}} to {{rmax}}), {{nbb}} of them backbone bonds.",
                   dict(n=len(A), nf=len(folds), t1=f"{t[folds[0]]:.4f}", e1=f"{e[folds[0]]:.3f}", ch=tp[0]["chain"],
                        rmin=min(min(int(q["res_i"]), int(q["res_j"])) for q in tp), rmax=max(max(int(q["res_i"]), int(q["res_j"])) for q in tp), nbb=int(bb.sum())),
                   [f"figure_data/{NAME}/load_control.csv", f"figure_data/{NAME}/continuation.csv", f"figure_data/{NAME}/snap_elements.csv"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
