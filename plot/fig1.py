"""Fig 1 - model, load and workflow (MscL C-alpha truss, one polygon layer, formulation boxes).
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
    from matplotlib.lines import Line2D
    from matplotlib.patches import Polygon, FancyBboxPatch
    from style import LW, MS, MEW
    N = style.read_csv(f"figure_data/{NAME}/nodes.csv"); E = style.read_csv(f"figure_data/{NAME}/edges.csv")
    PG = style.read_csv(f"figure_data/{NAME}/polygon.csv")
    a = lambda k, t=float: np.array([t(r[k]) for r in N])
    x, y, z = a("x"), a("y"), a("z"); ism, isl, iss, isy = (a(k, int).astype(bool) for k in ("membrane", "loaded", "shell", "layer"))
    fx, fy = a("fx"), a("fy"); pairs = np.array([[int(r["i"]), int(r["j"])] for r in E]); Vp = np.array([[float(r["x"]), float(r["y"])] for r in PG])
    style.apply()
    import matplotlib.pyplot as plt
    meta = style.read_json(f"figure_data/{NAME}_render/render_meta.json"); hh = meta["half_height"]; hw = hh * meta["width_px"] / meta["height_px"]
    ext = [-hw, hw, -hh, hh]
    RD = style.ROOT / "figure_data" / f"{NAME}_render"; S = plt.imread(str(RD / "render_surface.png")); Nw = plt.imread(str(RD / "render_network.png"))
    # crop panel a to the drawn content (surface silhouette and network), not to the full render canvas
    ys_, xs_ = np.where(np.maximum(S[..., 3], Nw[..., 3]) > 0.02)
    px = 2 * hh / S.shape[0]
    cx0, cx1 = -hw + xs_.min() * px, -hw + (xs_.max() + 1) * px; cy1 = hh - ys_.min() * px
    ylo, yhi = max(-hh, z.min()) - 7.0, cy1 + 2.0                         # 7 A below the content for the scale bar
    xlo, xhi = cx0 - 1.0, cx1 + 27.0                                      # 27 A right of the content for the labels
    Hmm_ax = 54.0; sc = Hmm_ax / (yhi - ylo)                              # mm per angstrom in panel a
    Wa = (xhi - xlo) * sc
    Wfig, Hfig = style.W2 / MM, Hmm_ax + 6.0
    fig = plt.figure(figsize=(style.W2, Hfig * MM))
    box = lambda l, b, w, h: fig.add_axes([l / Wfig, b / Hfig, w / Wfig, h / Hfig])
    Wb = 37.0; gap = 2.5; Wc = Wfig - Wa - Wb - 2 * gap - 1.6
    axa = box(0.0, 0.5, Wa, Hmm_ax); axb = box(Wa + gap, 0.5, Wb, Hmm_ax); axc = box(Wa + Wb + 2 * gap, 0.5, Wc, Hmm_ax)
    ht = float(np.abs(z[ism]).max())
    axa.axhspan(-ht, ht, fc="#FFF1DC", ec="none", zorder=0)
    for yy in (-ht, ht):
        axa.axhline(yy, color="#E69F00", lw=LW["ref"], ls=(0, (3, 2)), zorder=0)
    S2 = S.copy(); S2[..., 3] *= 1 - 0.95                                    # surface layer at transparency 0.95
    axa.imshow(S2, extent=ext, zorder=1, interpolation="antialiased")
    yy_, xx_ = np.linspace(hh, -hh, S.shape[0]), np.linspace(-hw, hw, S.shape[1])
    axa.contour(xx_, yy_, S[..., 3], levels=[0.5], colors="#8E99A6", linewidths=LW["zero"], zorder=1.5)   # its silhouette
    axa.imshow(Nw, extent=ext, zorder=2, interpolation="antialiased")
    k = meta["focus_node"]; xt = cx1 + 2.5
    axa.annotate("elements of\none node", (x[k], z[k]), xytext=(xt, -ht - 4), fontsize=style.FS, color=DARK, ha="left", va="top",
                 arrowprops=dict(arrowstyle="-", color=DARK, lw=LW["zero"], shrinkA=0, shrinkB=3), zorder=4)
    top = z.max(); i_s = int(np.argmax(z))
    axa.annotate("molecular\nsurface", (x[i_s] + 6, top + 2), xytext=(xt, cy1), fontsize=style.FS, color="#5F6B78", ha="left", va="top",
                 arrowprops=dict(arrowstyle="-", color="#8E99A6", lw=LW["zero"], shrinkA=0, shrinkB=0), zorder=4)
    axa.text(xt, 0, "membrane\nslab", fontsize=style.FS, color="#B07800", ha="left", va="center")
    axa.set_aspect("equal"); axa.axis("off"); axa.set_xlim(xlo, xhi); axa.set_ylim(ylo, yhi)
    yb = ylo + 2.5
    axa.plot([xt, xt + 20], [yb] * 2, color=DARK, lw=LW["data"]); axa.text(xt + 10, yb + 1.2, "20 Å", ha="center", va="bottom", fontsize=style.FS)
    axa.set_title("MscL C$\\alpha$ truss, $r_c$ = 10 Å", loc="left")
    axb.add_patch(Polygon(Vp, closed=True, fc="#EAF4FB", ec="#0072B2", lw=LW["sec"], zorder=1))
    axb.scatter(x[isy], y[isy], s=MS["small"] ** 2, c="#56B4E9", lw=0, zorder=2)
    axb.scatter(x[iss], y[iss], s=(MS["small"] + 0.4) ** 2, c="#D55E00", lw=0, zorder=3)
    axb.scatter(Vp[:, 0], Vp[:, 1], s=MS["line"] ** 2, marker="D", c="white", edgecolors="#0072B2", lw=MEW["open"] - 0.1, zorder=4)
    gx, gy = fx[iss], fy[iss]; scl = 7.0 / max(np.abs(gx).max(), np.abs(gy).max())
    axb.quiver(x[iss], y[iss], gx * scl, gy * scl, angles="xy", scale_units="xy", scale=1, color="#D55E00",
               width=0.006, headwidth=3.5, headlength=4, zorder=5)
    axb.set_aspect("equal"); axb.axis("off")
    axb.set_title("One 4 Å layer", loc="left")
    pad = 9; axb.set_xlim(Vp[:, 0].min() - pad, Vp[:, 0].max() + pad); axb.set_ylim(Vp[:, 1].min() - pad, Vp[:, 1].max() + pad)
    axc.axis("off"); axc.set_xlim(0, Wc); axc.set_ylim(0, Hmm_ax); axc.set_title("Formulation and workflow", loc="left")
    items = [("Geometrically nonlinear truss", r"$U=(k/2)\,\Sigma_e(\ell_e-\ell_e^0)^2$, exact kinematics"),
             ("Conservative membrane tension", r"$\Pi=U-\tau A(\mathbf{x})$,  $A=\mathbf{x}^{T}\mathbf{H}\mathbf{x}/2$"),
             ("Gauge from the load symmetries", r"$A$ invariant to 4 rigid motions; tilt has a moment"),
             ("Verified path, stability by inertia", r"Newton = VFIFE; inertia of $\mathbf{K}_t-\tau\mathbf{H}$ each step"),
             ("Departure from linearization", r"stiffening $a$, turning $\sin\theta\approx\chi$, snapping $n_{\rm neg}$"),
             ("Test against partner structures", "TM C$\\alpha$ RMSD vs. linear response, null models")]
    BOXTXT = []; hb = 7.6; g = (Hmm_ax - len(items) * hb) / (len(items) - 1)
    for i, (t1, t2) in enumerate(items):
        yb = Hmm_ax - (i + 1) * hb - i * g
        axc.add_patch(FancyBboxPatch((0.2, yb), Wc - 0.4, hb, boxstyle="round,pad=0,rounding_size=0.8", fc="#F4F4F4", ec="#9E9E9E", lw=LW["ref"]))
        axc.text(1.4, yb + 0.73 * hb, t1, fontsize=style.FS, fontweight="bold", color=DARK, va="center")
        t_ = axc.text(1.4, yb + 0.28 * hb, t2, fontsize=style.FS, color=DARK, va="center"); BOXTXT.append(t_)
        if i < len(items) - 1:
            axc.annotate("", xy=(Wc / 2, yb - g + 0.05), xytext=(Wc / 2, yb - 0.05), arrowprops=dict(arrowstyle="-|>", color=GREY, lw=LW["ref"], mutation_scale=5, shrinkA=0, shrinkB=0))
    for ax_, t in ((axa, "a"), (axb, "b"), (axc, "c")):
        style.letter(ax_, t)
    h = [Line2D([], [], ls="", marker="o", ms=MS["small"] + 0.5, mfc="#4D4D4D", mec="none", label="C$\\alpha$ outside slab"),
         Line2D([], [], ls="", marker="o", ms=MS["small"] + 0.5, mfc="#56B4E9", mec="none", label="membrane C$\\alpha$"),
         Line2D([], [], ls="", marker="o", ms=MS["small"] + 0.5, mfc="#D55E00", mec="none", label="loaded outer-shell node"),
         Line2D([], [], ls="", marker="D", ms=MS["small"] + 0.5, mfc="white", mec="#0072B2", label="polygon vertex"),
         Line2D([], [], color="#D55E00", lw=LW["data"], label=r"nodal force $\tau\,\partial A/\partial\mathbf{x}$")]
    fig.canvas.draw()
    rr = fig.canvas.get_renderer(); xr = axc.transData.transform((Wc - 0.4, 0))[0]
    if any(t_.get_window_extent(rr).x1 > xr - 2 for t_ in BOXTXT):
        print("fig1: flowchart text runs past its box")
    style.top_legend(fig, [h])
    style.save(fig, NAME)
    style.describe(NAME, "Fig. 1 model and load: C-alpha truss of MscL (2OAR, r_c = 10 A) with {{n_nodes}} nodes and {{n_edges}} elements; "
                   "{{n_loaded}} loaded outer-shell nodes inside the membrane slab ({{n_mem}} membrane nodes). One 4 A layer polygon with "
                   "{{n_vert}} vertices and the nodal forces tau dA/dx, which act only on the outer shell. Panel a overlays the C-alpha network on the molecular surface (transparency 0.95); "
                   "the {{n_focus}} elements of one loaded node are drawn dark. Right: formulation and workflow.",
                   dict(n_nodes=len(x), n_edges=len(pairs), n_loaded=int(isl.sum()), n_mem=int(ism.sum()), n_vert=len(Vp), n_focus=meta["n_focus_elements"]),
                   [f"figure_data/{NAME}/nodes.csv", f"figure_data/{NAME}/edges.csv", f"figure_data/{NAME}/polygon.csv", f"figure_data/{NAME}_render/render_meta.json"])


if __name__ == "__main__":
    {"extract": extract, "plot": plot}[sys.argv[1]]()
