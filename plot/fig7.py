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
    pts = [dict(point=k, eps=q["eps"], tau=q["tau"], dlam_ds=q["dlam_ds"], n_neg=q["inertia"]["n_neg"], lam1=(q["lam"][0] if q["lam"] else None), max_e=q["max_e"])
           for k, q in enumerate(A["points"])]
    style.write_csv(DATA / "continuation.csv", pts, ["point", "eps", "tau", "dlam_ds", "n_neg", "lam1", "max_e"])
    top = [dict(rank=k + 1, chain=q["i"][0], res_i=q["i"][1], res_j=q["j"][1], e_pre=q["e_pre"], e_post=q["e_post"], backbone=int(bool(q["backbone"])))
           for k, q in enumerate(SN["snap_top_elements"][:10])]
    style.write_csv(DATA / "snap_elements.csv", top, ["rank", "chain", "res_i", "res_j", "e_pre", "e_post", "backbone"])
    style.write_readme(DATA, "fig7 plotting data", "data/derived/paths/6b3r_rc10_loadcontrol.json, _arclength.json, _snap.json", {
        "load_control.csv": [("eps", "normalized radial displacement, load-controlled Newton path", "-", "value"), ("tau", "membrane tension", "model units", "value")],
        "continuation.csv": [("point", "continuation point index", "-", "index"), ("eps", "normalized radial displacement", "-", "value"),
                             ("tau", "membrane tension", "model units", "value"), ("dlam_ds", "load-parameter component of the unit tangent", "-", "value"),
                             ("n_neg", "negative eigenvalues of the constrained tangent (inertia count)", "-", "count"),
                             ("lam1", "lowest eigenvalue returned by shift-invert Lanczos (sigma = -1e-4)", "model units", "value"),
                             ("max_e", "largest element strain", "-", "value")],
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
    style.apply()
    fig = plt.figure(figsize=(style.W2, 62 * MM))
    axa = fig.add_axes([0.06, 0.18, 0.18, 0.66]); axb = fig.add_axes([0.31, 0.18, 0.18, 0.66])
    axc = fig.add_axes([0.57, 0.18, 0.17, 0.66]); axd = fig.add_axes([0.86, 0.18, 0.14, 0.66])
    col = COL["6b3r"]
    e = num(A, "eps"); t = num(A, "tau"); nn = num(A, "n_neg").astype(int); dl = num(A, "dlam_ds")
    folds = [i for i in range(1, len(dl)) if np.sign(dl[i]) != np.sign(dl[i - 1])]
    axa.plot(num(L, "eps"), num(L, "tau"), "o-", color=col, mfc="white", ms=2.2, mew=0.5, lw=0.6)
    axa.plot(e[folds[0]], t[folds[0]], "v", color="k", ms=4); axa.annotate("L$_1$", (e[folds[0]], t[folds[0]]), xytext=(-12, 2), textcoords="offset points", fontsize=style.FS)
    axa.set_xlabel(r"normalised radial displacement $\varepsilon$"); axa.set_ylabel(r"tension $\tau$"); axa.set_title("Load control stops", loc="left")
    k = np.arange(len(t))
    for i in range(len(t) - 1):
        axb.plot(k[i:i + 2], t[i:i + 2], color=col if nn[i + 1] == 0 else "#7F7F7F", lw=1.0, ls="-" if nn[i + 1] == 0 else (0, (2, 1.2)))
    for j, i in enumerate(folds):
        axb.plot(k[i], t[i], "v" if dl[i - 1] > 0 else "^", color="k", ms=3.5, zorder=4)
        axb.annotate(f"L$_{j + 1}$", (k[i], t[i]), xytext=(3, 2 if dl[i - 1] > 0 else -9), textcoords="offset points", fontsize=style.FS)
    axb.set_xlabel("continuation point"); axb.set_ylabel(r"tension $\tau$"); axb.set_title("Continuation", loc="left"); axb.margins(y=0.12)
    axb.legend(handles=[Line2D([], [], color=col, lw=1.0, label="stable"), Line2D([], [], color="#7F7F7F", lw=1.0, ls=(0, (2, 1.2)), label="$n_{\\rm neg}$ = 1")],
               loc="lower left", fontsize=style.FS)
    i1 = folds[0]; w = np.arange(max(0, i1 - 10), min(len(A), i1 + 12))
    lam = num(A, "lam1")[w]
    axc.bar(w - i1, np.where(nn[w] > 0, 49, 0), bottom=-36, width=1.0, color="#E0E0E0", lw=0, zorder=0)
    axc.plot(w - i1, lam * 1e5, "o-", color=col, ms=2.4, lw=0.9, mec="white", mew=0.3, zorder=3)
    axc.axhline(0, color=DARK, lw=0.5)
    axc.set_ylim(-36, 13); axc.set_xlabel("continuation step from L$_1$"); axc.set_ylabel(r"shift-invert $\lambda_1$ ($10^{-5}$)")
    axc.text(0.97, 0.06, "grey: inertia\n$n_{\\rm neg}$ = 1", transform=axc.transAxes, ha="right", va="bottom", fontsize=style.FS, color="#555555")
    axc.set_title("Monitor misses the fold", loc="left")
    de = num(tp, "e_post") - num(tp, "e_pre"); bb = num(tp, "backbone").astype(bool)
    axd.barh(np.arange(len(tp))[::-1], de, color=[col if b else "#9E9E9E" for b in bb], height=0.7)
    axd.set_yticks(np.arange(len(tp))[::-1]); axd.set_yticklabels([f"{q['res_i']}–{q['res_j']}" for q in tp], fontsize=style.FS)
    axd.axvline(0, color=DARK, lw=0.5); axd.set_ylim(-2.2, len(tp) - 0.4)
    axd.set_xlabel(r"$\Delta e$ in the snap"); axd.set_title("Local snap (" + tp[0]["chain"] + ")", loc="left")
    axd.legend(handles=[Patch(color=col, label="backbone"), Patch(color="#9E9E9E", label="contact")], loc="lower right", fontsize=style.FS, handlelength=0.9, borderaxespad=0.1)
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
