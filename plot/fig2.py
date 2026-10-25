"""Fig 2 - a verified path and a gauge that follows the load.
  python plot/fig2.py extract   (data/derived -> figure_data/fig2)
  python plot/fig2.py plot      (figure_data/fig2 -> results/figures/fig2.*)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import style
from style import CH, COL, MK, LABEL, GREY, MM

NAME = "fig2"
DATA = style.ROOT / "figure_data" / NAME


def extract():
    import derived
    S = derived.summary(); V = S["vfife_checks"]; L = S["load_check"]
    rows = []
    for p in CH:
        for r in V.get(f"vfife_{p}_rc10", []):
            rows.append(dict(structure=p, start_step=r["start_step"], eps_end=r["eps_end"], eps_star=S["runs"][f"{p}_rc10"]["eps_star"], max_deviation=r["maxdev"]))
    style.write_csv(DATA / "vfife.csv", rows, ["structure", "start_step", "eps_end", "eps_star", "max_deviation"])
    W = V["work_2oar_rc10"]
    style.write_csv(DATA / "work_energy.csv", [dict(dtau=r["h"], mismatch=r["rel"]) for r in W["rows"]], ["dtau", "mismatch"])
    g = [dict(structure=p, reaction_symmetry=L[p]["gauge_symmetry"]["reaction_rel"], reaction_eckart=L[p]["gauge_raw"]["eckart_reaction_rel"],
              reaction_anchor=L[p]["gauge_raw"]["anchor_reaction_rel"], rmsd_symmetry=L[p]["gauge_symmetry"]["rmsd_vs_eckart6"],
              rmsd_anchor=L[p]["gauge_raw"]["rmsd_anchored_vs_eckart"]) for p in CH]
    style.write_csv(DATA / "gauge.csv", g, ["structure", "reaction_symmetry", "reaction_eckart", "reaction_anchor", "rmsd_symmetry", "rmsd_anchor"])
    style.write_readme(DATA, "fig2 plotting data", "data/derived/summary.json (vfife_checks, load_check), r_c = 10 A", {
        "vfife.csv": [("structure", "structure id", "-", "label"), ("start_step", "1-based Newton step from which VFIFE is restarted", "-", "index"),
                      ("eps_end", "normalized radial displacement at the end of the increment", "-", "value"),
                      ("eps_star", "end of the validity range of the structure", "-", "value"),
                      ("max_deviation", "maximum nodal distance between the VFIFE rest state and the Newton state", "angstrom", "value")],
        "work_energy.csv": [("dtau", "tension increment of the Newton path", "model units", "value"),
                            ("mismatch", "|U - W| / U at tau = 3.0 (MscL), trapezoidal work", "-", "value")],
        "gauge.csv": [("structure", "structure id", "-", "label"), ("reaction_symmetry", "constraint reaction / load, four-symmetry gauge (tilt free)", "-", "value"),
                      ("reaction_eckart", "constraint reaction / load, six Eckart conditions", "-", "value"),
                      ("reaction_anchor", "support reaction / load, six isostatic anchors", "-", "value"),
                      ("rmsd_symmetry", "RMSD of the tilt-free solution from the Eckart solution", "angstrom", "value"),
                      ("rmsd_anchor", "RMSD of the anchored solution from the Eckart solution", "angstrom", "value")]})


def plot():
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter
    from figcommon import logticks, chan_handles, mkh
    from style import LW, MS, MEW
    Vf = style.read_csv(f"figure_data/{NAME}/vfife.csv"); W = style.read_csv(f"figure_data/{NAME}/work_energy.csv")
    G = {r["structure"]: r for r in style.read_csv(f"figure_data/{NAME}/gauge.csv")}
    fig, ax = style.figure(1, 4, height_mm=50); ax = ax[0]
    xs = np.arange(len(CH)); names = [LABEL[p] for p in CH]
    a = ax[0]
    for r in Vf:
        p = r["structure"]; i = CH.index(p); dev = float(r["max_deviation"]); near = float(r["eps_end"]) >= 0.8 * float(r["eps_star"])
        if dev > 1e-3:          # the increment that ends exactly at the limit point snaps
            a.annotate("", xy=(i, 9e-5), xytext=(i, 2.5e-5), arrowprops=dict(arrowstyle="-|>", color=COL[p], lw=LW["sec"], mutation_scale=6))
            a.text(i + 0.25, 4.7e-5, f"snap at L$_1$ ({dev:.1f} Å)", fontsize=style.FS, color=COL[p], va="center")
            continue
        a.plot(i + (0.12 if near else -0.12), dev, MK[p], color=COL[p], mfc=COL[p] if near else "white", ms=MS["cat"], mew=MEW["open"], zorder=3)
    a.axhline(1e-5, color=GREY, lw=LW["ref"], ls=(0, (4, 2)))
    a.text(len(CH) - 0.5, 7e-6, "tolerance", ha="right", va="top", fontsize=style.FS, color=style.NOTE)
    a.set_yscale("log"); logticks(a); a.set_ylim(1e-9, 1e-4)
    a.set_xticks(xs); style.catlabels(a.xaxis, names); a.set_xlim(-0.6, len(CH) - 0.4)
    a.set_ylabel("max. deviation (Å)"); a.set_title("VFIFE vs. Newton", loc="left")
    a.legend(handles=[mkh("o", "mid-path", filled=False), mkh("o", r"near $\varepsilon^*$")], loc="lower left", handletextpad=0.1, borderaxespad=0.1)
    b = ax[1]
    h = np.array([float(r["dtau"]) for r in W]); e = np.array([float(r["mismatch"]) for r in W])
    b.loglog(h, e, "o-", color=COL["2oar"], ms=MS["line"], mec="white", mew=MEW["edge"])
    ref = e[-1] * (h / h[-1]) ** 2; b.loglog(h, ref, color=GREY, lw=LW["ref"], ls=(0, (4, 2)))
    b.text(h[1] * 1.15, ref[1] * 0.75, "slope 2", fontsize=style.FS, color=style.NOTE, ha="left", va="top")
    b.xaxis.set_minor_formatter(NullFormatter())
    xt = [v for v in (0.1, 0.2, 0.5, 1.0) if h.min() * 0.95 <= v <= h.max() * 1.05]; b.xaxis.set_major_locator(FixedLocator(xt)); b.xaxis.set_major_formatter(FixedFormatter([f"{v:g}" for v in xt]))
    b.set_xlabel(r"$\Delta\tau$"); b.set_ylabel(r"$|U-W|/U$"); b.set_title("Work–energy", loc="left")
    b.text(0.97, 0.04, "MscL, $\\tau$ = 3", transform=b.transAxes, ha="right", fontsize=style.FS, color=style.NOTE)
    c = ax[2]
    for i, p in enumerate(CH):
        g = G[p]
        for k, (v, mk, fc) in enumerate(((g["reaction_symmetry"], "o", "white"), (g["reaction_eckart"], "s", COL[p]), (g["reaction_anchor"], "^", COL[p]))):
            c.plot(i + (k - 1) * 0.22, max(float(v), 1e-18), mk, color=COL[p], mfc=fc, ms=MS["cat"], mew=MEW["open"])
    c.set_yscale("log"); c.set_ylim(1e-19, 3); c.yaxis.set_major_locator(FixedLocator([1e-18, 1e-14, 1e-10, 1e-6, 1e-2])); c.yaxis.set_minor_formatter(NullFormatter())
    c.set_xticks(xs); style.catlabels(c.xaxis, names); c.set_xlim(-0.6, len(CH) - 0.4)
    c.set_ylabel("reaction / load"); c.set_title("Gauge reactions", loc="left")
    d = ax[3]
    for i, p in enumerate(CH):
        d.plot(i - 0.12, float(G[p]["rmsd_symmetry"]), "o", color=COL[p], mfc="white", ms=MS["cat"], mew=MEW["open"])
        d.plot(i + 0.12, float(G[p]["rmsd_anchor"]), "^", color=COL[p], ms=MS["cat"], mew=MEW["open"])
    d.set_yscale("log"); logticks(d); d.set_ylim(1e-3, 3)
    d.set_xticks(xs); style.catlabels(d.xaxis, names); d.set_xlim(-0.6, len(CH) - 0.4)
    d.set_ylabel("RMSD to Eckart (Å)"); d.set_title("Gauge distortion", loc="left")
    gh = [mkh("o", "4 symmetry constraints (tilt free)", filled=False), mkh("s", "6 Eckart conditions"), mkh("^", "6 isostatic anchors")]
    for a_, t in zip(ax, "abcd"):
        style.letter(a_, t)
    fig.canvas.draw()
    style.top_legend(fig, [chan_handles(), gh])
    style.save(fig, NAME)
    devs = [float(r["max_deviation"]) for r in Vf if float(r["max_deviation"]) <= 1e-3]
    order = float(np.log(e[-2] / e[-1]) / np.log(h[-2] / h[-1]))      # observed order between the two finest increments
    style.describe(NAME, "Fig. 2 verification and gauge (r_c = 10 A). VFIFE restarted from Newton states agrees to at most {{vf_max}} A over {{n_vf}} increments; "
                   "the increment ending at the Piezo1 limit point snaps by {{snap}} A. Work-energy mismatch converges with observed order {{order}} between the two finest increments. "
                   "Gauge reactions relative to the load: four-symmetry gauge at most {{sym_max}}, Eckart {{eck_min}} to {{eck_max}}, anchors {{anc_min}} to {{anc_max}}; "
                   "anchored solutions differ from Eckart by up to {{anc_rmsd}} A.",
                   dict(vf_max=f"{max(devs):.1e}", n_vf=len(devs), snap=f"{max(float(r['max_deviation']) for r in Vf):.1f}", order=f"{order:.2f}",
                        sym_max=f"{max(float(g['reaction_symmetry']) for g in G.values()):.1e}",
                        eck_min=f"{min(float(g['reaction_eckart']) for g in G.values()):.1e}", eck_max=f"{max(float(g['reaction_eckart']) for g in G.values()):.1e}",
                        anc_min=f"{min(float(g['reaction_anchor']) for g in G.values()):.1e}", anc_max=f"{max(float(g['reaction_anchor']) for g in G.values()):.2f}",
                        anc_rmsd=f"{max(float(g['rmsd_anchor']) for g in G.values()):.2f}"),
                   [f"figure_data/{NAME}/vfife.csv", f"figure_data/{NAME}/work_energy.csv", f"figure_data/{NAME}/gauge.csv"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
