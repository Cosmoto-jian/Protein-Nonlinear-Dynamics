"""Fig 1a layers: molecular surface and C-alpha truss of MscL, rendered off screen with the same orthographic camera.
  python plot/fig1_render.py   (figure_data/fig1/{nodes,edges,atoms}.csv -> figure_data/fig1_render/)
Needs pyvista with an off-screen OpenGL (OSMesa or EGL). The images are composed with vector annotations by fig1.py plot."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import style

DATA = style.ROOT / "figure_data" / "fig1_render"
W_PX, H_PX = 1800, 2400            # 60 x 80 mm at 760 dpi
SIGMA, GRID, ISO = 1.6, 0.8, 0.06  # Gaussian surface: width (A), grid (A), iso level (fraction of the maximum density)
COLORS = {"surface": "#B9C2CD", "edge": "#8C8C8C", "outside": "#4D4D4D", "membrane": "#56B4E9", "loaded": "#D55E00", "focus": "#1A1A1A"}


def main():
    import pyvista as pv
    from scipy.ndimage import gaussian_filter
    N = style.read_csv("figure_data/fig1/nodes.csv"); E = style.read_csv("figure_data/fig1/edges.csv"); A = style.read_csv("figure_data/fig1/atoms.csv")
    X = np.array([[float(r[k]) for k in "xyz"] for r in N]); P = np.array([[int(r["i"]), int(r["j"])] for r in E])
    mem = np.array([r["membrane"] == "1" for r in N]); lod = np.array([r["loaded"] == "1" for r in N])
    At = np.array([[float(r[k]) for k in "xyz"] for r in A])
    lo = At.min(0) - 6; dims = np.ceil((At.max(0) + 6 - lo) / GRID).astype(int) + 1
    rho = np.zeros(dims); idx = np.round((At - lo) / GRID).astype(int); np.add.at(rho, tuple(idx.T), 1.0)
    rho = gaussian_filter(rho, SIGMA / GRID)
    g = pv.ImageData(dimensions=dims, spacing=(GRID,) * 3, origin=lo); g.point_data["rho"] = rho.ravel(order="F")
    surf = g.contour([ISO * rho.max()], scalars="rho").smooth_taubin(n_iter=40, pass_band=0.05)
    half = 0.5 * 1.08 * max((np.ptp(X[:, 2]) + 12), (np.ptp(X[:, 0]) + 12) * H_PX / W_PX)

    def plotter():
        pl = pv.Plotter(off_screen=True, window_size=(W_PX, H_PX)); pl.set_background("white")
        pl.camera_position = [(0, -500, 0), (0, 0, 0), (0, 0, 1)]; pl.enable_parallel_projection(); pl.camera.parallel_scale = half
        return pl
    DATA.mkdir(parents=True, exist_ok=True)
    pl = plotter()
    pl.add_mesh(surf, color=COLORS["surface"], smooth_shading=True, specular=0.15, ambient=0.35, diffuse=0.75)
    pl.screenshot(str(DATA / "render_surface.png"), transparent_background=True); pl.close()
    pl = plotter(); pl.enable_anti_aliasing("ssaa")
    lines = lambda pp: np.hstack([np.full((len(pp), 1), 2), pp]).ravel()
    pl.add_mesh(pv.PolyData(X, lines=lines(P)), color=COLORS["edge"], opacity=0.7, line_width=2.6, lighting=False)

    def balls(sel, col, r):
        pl.add_mesh(pv.PolyData(X[sel]).glyph(geom=pv.Sphere(radius=r, theta_resolution=24, phi_resolution=24), scale=False, orient=False),
                    color=col, smooth_shading=True, specular=0.3, ambient=0.3)
    balls(~mem, COLORS["outside"], 0.45); balls(mem & ~lod, COLORS["membrane"], 0.48); balls(lod, COLORS["loaded"], 0.52)
    k = int(np.argmax(np.where(lod & (X[:, 1] < 0), X[:, 0], -1e9)))      # outermost loaded node on the viewer's side
    nb = P[(P == k).any(1)]
    pl.add_mesh(pv.PolyData(X, lines=lines(nb)).tube(radius=0.22), color=COLORS["focus"], smooth_shading=True)
    balls(np.arange(len(X)) == k, COLORS["loaded"], 1.0)
    pl.screenshot(str(DATA / "render_network.png"), transparent_background=True); pl.close()
    (DATA / "render_meta.json").write_text(json.dumps(dict(half_height=half, width_px=W_PX, height_px=H_PX, focus_node=k,
                                                           n_focus_elements=int(len(nb)), surface=dict(sigma=SIGMA, grid=GRID, iso=ISO)), indent=1))
    style.write_readme(DATA, "fig1 panel a rendered layers", "plot/fig1_render.py from figure_data/fig1 (nodes.csv, edges.csv, atoms.csv)", {
        "render_surface.png": [("-", "molecular surface (Gaussian density of atoms.csv, iso level ISO of the maximum), orthographic view along +y", "-", "RGBA image")],
        "render_network.png": [("-", "C-alpha truss of nodes.csv and edges.csv, same camera; focus node and its elements drawn dark", "-", "RGBA image")],
        "render_meta.json": [("half_height", "half height of the rendered view (parallel scale); image x maps to model x, image y to model z", "angstrom", "value"),
                             ("width_px, height_px", "image size", "pixel", "value"), ("focus_node", "node whose truss elements are highlighted", "-", "index"),
                             ("n_focus_elements", "number of highlighted elements", "-", "count"), ("surface", "sigma, grid (angstrom) and iso fraction of the surface", "-", "value")]})


if __name__ == "__main__":
    main()
