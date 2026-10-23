"""Fig 1 - model, load and line of the paper (MscL C-alpha truss, one polygon layer, formulation boxes).
  python plot/fig1.py extract   (src model -> figure_data/fig1)
  python plot/fig1.py plot      (figure_data/fig1 -> results/figures/fig1.*)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import style
from style import MM, DARK, GREY

NAME = "fig1"
DATA = style.ROOT / "figure_data" / NAME


def extract():
    import derived  # noqa: F401  (puts src/ on the path)
    from model import model, make_area
    M = model("2oar", 10.0); area, ns = make_area(M); X0 = M["X0"]
    g = area.grad(X0).reshape(-1, 3); V = (area.Bm @ X0.ravel()).reshape(-1, 2)
    kmid = len(area.polys) // 2; poly = np.array(area.polys[kmid], int)
    shell = np.unique(area.Bm[2 * poly].nonzero()[1] // 3)
    c = M["m"]["centroid"]; zm = M["m"]["z_mid"]; mem = M["mem"]; loaded = area.vertices
    zr = X0[shell, 2]; lay = mem[(X0[mem, 2] >= zr.min() - 0.3) & (X0[mem, 2] <= zr.max() + 0.3)]
    n = len(X0); f = lambda idx: np.isin(np.arange(n), idx).astype(int)
    ism, isl, iss, isy = f(mem), f(loaded), f(shell), f(lay)
    nodes = [dict(node=i, x=X0[i, 0] - c[0], y=X0[i, 1] - c[1], z=X0[i, 2] - zm, membrane=ism[i], loaded=isl[i],
                  shell=iss[i], layer=isy[i], fx=g[i, 0], fy=g[i, 1]) for i in range(n)]
    style.write_csv(DATA / "nodes.csv", nodes, ["node", "x", "y", "z", "membrane", "loaded", "shell", "layer", "fx", "fy"])
    style.write_csv(DATA / "edges.csv", [dict(i=int(a), j=int(b)) for a, b in M["pairs"]], ["i", "j"])
    from paths import raw
    atoms = [dict(x=float(l[30:38]) - c[0], y=float(l[38:46]) - c[1], z=float(l[46:54]) - zm) for l in open(raw("opm_2oar.pdb"), encoding="utf-8")
             if l.startswith("ATOM") and l[76:78].strip() != "H"]
    style.write_csv(DATA / "atoms.csv", atoms, ["x", "y", "z"])
    style.write_csv(DATA / "polygon.csv", [dict(vertex=k, x=V[v, 0] - c[0], y=V[v, 1] - c[1]) for k, v in enumerate(poly)], ["vertex", "x", "y"])
    style.write_readme(DATA, "fig1 plotting data", "src/model.py (MscL 2OAR, r_c = 10 A, reference state)", {
        "nodes.csv": [("node", "C-alpha node index", "-", "index"), ("x", "x minus membrane-axis x", "angstrom", "value"),
                      ("y", "y minus membrane-axis y", "angstrom", "value"), ("z", "z minus bilayer midplane", "angstrom", "value"),
                      ("membrane", "node inside the membrane slab", "-", "flag 0/1"), ("loaded", "node in a loaded outer shell", "-", "flag 0/1"),
                      ("shell", "outer-shell node of the drawn layer", "-", "flag 0/1"), ("layer", "membrane node of the drawn 4 A layer", "-", "flag 0/1"),
                      ("fx", "x component of dA/dx (area gradient)", "angstrom", "value"), ("fy", "y component of dA/dx", "angstrom", "value")],
        "atoms.csv": [("x", "heavy-atom x minus membrane-axis x (OPM 2OAR)", "angstrom", "value"), ("y", "heavy-atom y minus axis y", "angstrom", "value"),
                      ("z", "heavy-atom z minus bilayer midplane", "angstrom", "value")],
        "edges.csv": [("i", "first node of a truss element", "-", "index"), ("j", "second node of a truss element", "-", "index")],
        "polygon.csv": [("vertex", "vertex order along the drawn layer polygon", "-", "index"), ("x", "vertex x (shell mean) minus axis x", "angstrom", "value"),
                        ("y", "vertex y minus axis y", "angstrom", "value")]})


def plot():
    from matplotlib.collections import LineCollection
    from matplotlib.lines import Line2D
    from matplotlib.patches import Polygon, FancyBboxPatch, Rectangle
    N = style.read_csv(f"figure_data/{NAME}/nodes.csv"); E = style.read_csv(f"figure_data/{NAME}/edges.csv")
    PG = style.read_csv(f"figure_data/{NAME}/polygon.csv")
    a = lambda k, t=float: np.array([t(r[k]) for r in N])
    x, y, z = a("x"), a("y"), a("z"); ism, isl, iss, isy = (a(k, int).astype(bool) for k in ("membrane", "loaded", "shell", "layer"))
    fx, fy = a("fx"), a("fy"); pairs = np.array([[int(r["i"]), int(r["j"])] for r in E]); Vp = np.array([[float(r["x"]), float(r["y"])] for r in PG])
    style.apply()
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(style.W2, 72 * MM))
    axa = fig.add_axes([0.00, 0.05, 0.27, 0.80]); axb = fig.add_axes([0.29, 0.05, 0.29, 0.80]); axc = fig.add_axes([0.61, 0.02, 0.39, 0.86])
    ht = float(np.abs(z[ism]).max())
    meta = style.read_json(f"figure_data/{NAME}_render/render_meta.json"); hh = meta["half_height"]; hw = hh * meta["width_px"] / meta["height_px"]
    ext = [-hw, hw, -hh, hh]
    axa.axhspan(-ht, ht, fc="#FFF1DC", ec="none", zorder=0)
    for yy in (-ht, ht):
        axa.axhline(yy, color="#E69F00", lw=0.6, ls=(0, (3, 2)), zorder=0)
    RD = style.ROOT / "figure_data" / f"{NAME}_render"; S = plt.imread(str(RD / "render_surface.png")); Nw = plt.imread(str(RD / "render_network.png"))
    S2 = S.copy(); S2[..., 3] *= 1 - 0.95                                    # surface layer at transparency 0.95
    axa.imshow(S2, extent=ext, zorder=1, interpolation="antialiased")
    yy_, xx_ = np.linspace(hh, -hh, S.shape[0]), np.linspace(-hw, hw, S.shape[1])
    axa.contour(xx_, yy_, S[..., 3], levels=[0.5], colors="#8E99A6", linewidths=0.45, zorder=1.5)   # its silhouette
    axa.imshow(Nw, extent=ext, zorder=2, interpolation="antialiased")
    k = meta["focus_node"]
    axa.annotate("elements of\none node", (x[k], z[k]), xytext=(x.max() + 9, -ht - 3), fontsize=style.FS, color=DARK, ha="left", va="top",
                 arrowprops=dict(arrowstyle="-", color=DARK, lw=0.5, shrinkA=0, shrinkB=3), zorder=4)
    top = z.max(); i_s = int(np.argmax(z))
    axa.annotate("molecular\nsurface", (x[i_s] + 6, top + 2), xytext=(x.max() + 9, top + 4), fontsize=style.FS, color="#5F6B78", ha="left", va="top",
                 arrowprops=dict(arrowstyle="-", color="#8E99A6", lw=0.5, shrinkA=0, shrinkB=0), zorder=4)
    axa.text(x.max() + 9, 0, "membrane\nslab", fontsize=style.FS, color="#B07800", ha="left", va="center")
    axa.set_aspect("equal"); axa.axis("off"); axa.set_xlim(x.min() - 12, x.max() + 34); axa.set_ylim(z.min() - 12, z.max() + 10)
    axa.plot([x.min(), x.min() + 20], [z.min() - 6] * 2, color=DARK, lw=1.0); axa.text(x.min() + 10, z.min() - 8, "20 Å", ha="center", va="top", fontsize=style.FS)
    axa.set_title("MscL C$\\alpha$ truss, $r_c$ = 10 Å", loc="left")
    axb.add_patch(Polygon(Vp, closed=True, fc="#EAF4FB", ec="#0072B2", lw=0.9, zorder=1))
    axb.scatter(x[isy], y[isy], s=4, c="#56B4E9", lw=0, zorder=2)
    axb.scatter(x[iss], y[iss], s=5, c="#D55E00", lw=0, zorder=3)
    axb.scatter(Vp[:, 0], Vp[:, 1], s=10, marker="D", c="white", edgecolors="#0072B2", lw=0.7, zorder=4)
    gx, gy = fx[iss], fy[iss]; sc = 7.0 / max(np.abs(gx).max(), np.abs(gy).max())
    axb.quiver(x[iss], y[iss], gx * sc, gy * sc, angles="xy", scale_units="xy", scale=1, color="#D55E00",
               width=0.005, headwidth=3.5, headlength=4, zorder=5)
    axb.set_aspect("equal"); axb.axis("off")
    axb.set_title("One 4 Å layer, extracellular view", loc="left")
    pad = 9; axb.set_xlim(Vp[:, 0].min() - pad, Vp[:, 0].max() + pad); axb.set_ylim(Vp[:, 1].min() - pad, Vp[:, 1].max() + pad)
    axc.axis("off"); axc.set_xlim(0, 1); axc.set_ylim(0, 1); axc.set_title("Formulation and line of the paper", loc="left")
    items = [("Geometrically nonlinear truss", r"$U=\frac{k}{2}\sum_e(\ell_e-\ell_e^0)^2$,  exact kinematics"),
             ("Conservative membrane tension", r"$\Pi=U-\tau A(\mathbf{x})$,  $A=\frac{1}{2}\mathbf{x}^{T}\mathbf{H}\mathbf{x}$"),
             ("Gauge from the symmetries of the load", r"$A$ invariant under 4 rigid motions; tilt carries a moment"),
             ("Verified, certified path", r"Newton = VFIFE;  inertia of $\mathbf{K}_t-\tau\mathbf{H}$ at every step"),
             ("Departure from linearization", r"stiffening $a$,  turning $\sin\theta\approx\chi$,  snapping $n_{\rm neg}$"),
             ("Test against partner structures", "TM C$\\alpha$ RMSD vs. linear response and null models")]
    hb = 0.145; gap = (1 - len(items) * hb) / (len(items) - 1)
    for i, (t1, t2) in enumerate(items):
        yb = 1 - (i + 1) * hb - i * gap
        axc.add_patch(FancyBboxPatch((0.02, yb), 0.96, hb, boxstyle="round,pad=0,rounding_size=0.02", fc="#F4F4F4", ec="#9E9E9E", lw=0.6))
        axc.text(0.05, yb + 0.74 * hb, t1, fontsize=style.FS, fontweight="bold", color=DARK, va="center")
        axc.text(0.05, yb + 0.27 * hb, t2, fontsize=style.FS, color=DARK, va="center")
        if i < len(items) - 1:
            axc.annotate("", xy=(0.5, yb - gap + 0.004), xytext=(0.5, yb - 0.004), arrowprops=dict(arrowstyle="-|>", color=GREY, lw=0.6, mutation_scale=6))
    for ax_, t in ((axa, "a"), (axb, "b"), (axc, "c")):
        style.letter(ax_, t)
    h = [Line2D([], [], ls="", marker="o", ms=3, mfc="#4D4D4D", mec="none", label="C$\\alpha$ outside the slab"),
         Line2D([], [], ls="", marker="o", ms=3, mfc="#56B4E9", mec="none", label="membrane C$\\alpha$"),
         Line2D([], [], ls="", marker="o", ms=3, mfc="#D55E00", mec="none", label="loaded node (outer shell)"),
         Line2D([], [], ls="", marker="D", ms=3, mfc="white", mec="#0072B2", label="polygon vertex (shell mean)"),
         Line2D([], [], color="#D55E00", lw=1.0, label=r"nodal force $\tau\,\partial A/\partial\mathbf{x}$")]
    fig.legend(handles=h, loc="lower center", ncol=5, bbox_to_anchor=(0.5, 0.99), handletextpad=0.3, columnspacing=1.2)
    style.save(fig, NAME)
    style.describe(NAME, "Fig. 1 model and load: C-alpha truss of MscL (2OAR, r_c = 10 A) with {{n_nodes}} nodes and {{n_edges}} elements; "
                   "{{n_loaded}} loaded outer-shell nodes inside the membrane slab ({{n_mem}} membrane nodes). One 4 A layer polygon with "
                   "{{n_vert}} vertices and the nodal forces tau dA/dx, which act only on the outer shell. Panel a overlays the C-alpha network on the molecular surface (transparency 0.95); "
                   "the {{n_focus}} elements of one loaded node are drawn dark. Right: formulation and line of the paper.",
                   dict(n_nodes=len(x), n_edges=len(pairs), n_loaded=int(isl.sum()), n_mem=int(ism.sum()), n_vert=len(Vp), n_focus=meta["n_focus_elements"]),
                   [f"figure_data/{NAME}/nodes.csv", f"figure_data/{NAME}/edges.csv", f"figure_data/{NAME}/polygon.csv", f"figure_data/{NAME}_render/render_meta.json"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
