"""Membrane-tension (area) loading for Calpha truss networks.

Lipid-facing boundary: the membrane band is cut into z-slabs; in each slab the
in-plane angle about the pore axis is split into sectors and the outermost
membrane node of every sector becomes a vertex of a star-shaped boundary
polygon (ordered by angle, vertex set frozen at the reference state).

Potential of the load:  W_ext = tau * A(X),  A = sum_s w_s A_s(X),
A_s = shoelace area of slab polygon s, w_s = slab weight (sum w_s = 1, i.e.
A is the mean cross-sectional area of the lipid-facing boundary).
A is a homogeneous quadratic form A = 1/2 X^T H X with a constant sparse H,
so the load is conservative, follower-type, in-plane, translation- and
z-rotation-invariant (self-equilibrated), and its load stiffness is tau*H.
Pore-lining and buried nodes carry no external force: their motion is a
model prediction, not a boundary condition.
"""
import numpy as np
import scipy.sparse as sp


class SlabBoundaryArea:
    def __init__(self, X0, mem_idx, axis_xy, z_mid, half_thick,
                 slab=4.0, n_sector=30, min_vertices=6):
        self.N = X0.shape[0]
        mem = np.asarray(mem_idx, int)
        c = np.asarray(axis_xy, float)
        edges = np.arange(z_mid - half_thick, z_mid + half_thick + 1e-9, slab)
        polys = []
        for z0, z1 in zip(edges[:-1], edges[1:]):
            sel = mem[(X0[mem, 2] >= z0) & (X0[mem, 2] < z1)]
            if len(sel) < min_vertices:
                continue
            d = X0[sel, :2] - c
            ang = np.arctan2(d[:, 1], d[:, 0])
            r = np.linalg.norm(d, axis=1)
            sec = np.floor((ang + np.pi) / (2 * np.pi) * n_sector).astype(int) % n_sector
            verts = []
            for s in range(n_sector):
                m = np.where(sec == s)[0]
                if len(m):
                    verts.append(m[np.argmax(r[m])])
            verts = np.array(verts)
            if len(verts) < min_vertices:
                continue
            order = np.argsort(ang[verts])
            polys.append(sel[verts[order]])
        self.polys = polys
        w = np.ones(len(polys)) / len(polys)
        self.w = w
        rows, cols, vals = [], [], []
        for p, ws in zip(polys, w):
            n = len(p)
            for k in range(n):
                i, j = p[k], p[(k + 1) % n]
                # A_s = 1/2 sum (x_i y_j - x_j y_i);  H entries d2A/dx_i dy_j = +1/2, d2A/dx_j dy_i = -1/2
                for (a, b, v) in ((3 * i, 3 * j + 1, 0.5), (3 * j, 3 * i + 1, -0.5)):
                    rows += [a, b]; cols += [b, a]; vals += [ws * v, ws * v]
        self.H = sp.csr_matrix((vals, (rows, cols)), shape=(3 * self.N, 3 * self.N))
        self.vertices = np.unique(np.concatenate(polys))

    def area(self, X):
        x = X.ravel()
        return 0.5 * float(x @ (self.H @ x))

    def grad(self, X):
        return (self.H @ X.ravel()).reshape(-1, 3)


class TensionPathSolver:
    """Explicit VFIFE (central difference, fictitious mass, damping) under
    tension loading tau*grad A; 6 rigid-body anchor DOFs on non-loaded nodes."""

    def __init__(self, elem, area, X0, anchor_dofs, mass, alpha_damp, dt=1.0,
                 path_unit=1, tol_R=1e-9, tol_K=1e-14, ramp_steps=200,
                 max_steps=2_000_000, check_every=100):
        self.elem, self.area = elem, area
        self.X = X0.copy(); self.X0 = X0.copy()
        fm = np.ones(3 * X0.shape[0]); fm[np.asarray(anchor_dofs, int)] = 0.0
        self.free = fm.reshape(-1, 3)
        self.m = np.asarray(mass, float); self.alpha = float(alpha_damp); self.dt = dt
        self.path_unit = path_unit; self.tol_R, self.tol_K = tol_R, tol_K
        self.ramp_steps, self.max_steps, self.check_every = ramp_steps, max_steps, check_every
        self.V = np.zeros_like(X0); self.tau = 0.0; self.n_total = 0
        self.f_int, self.Nax = elem.internal_forces(self.X)
        self.W_ext = 0.0; self.D = 0.0

    def force(self, X, f_int, tau):
        return (f_int + tau * self.area.grad(X)) * self.free

    def _step(self, dtau):
        dt, a = self.dt, self.alpha
        c1, c2 = 1 + 0.5 * a * dt, 1 - 0.5 * a * dt
        F = self.force(self.X, self.f_int, self.tau)
        V_new = ((c2 * self.V + dt * F / self.m[:, None]) / c1) * self.free
        X_new = self.X + dt * V_new
        A_old = self.area.area(self.X)
        tau_new = self.tau + dtau
        f_new, N_new = self.elem.internal_forces(X_new)
        # external work of a conservative load with varying tau: dW = tau_mid dA
        self.W_ext += 0.5 * (self.tau + tau_new) * (self.area.area(X_new) - A_old)
        v_mid = 0.5 * (self.V + V_new)
        self.D += a * dt * float(np.sum(self.m[:, None] * v_mid ** 2))
        self.X, self.V, self.f_int, self.Nax, self.tau = X_new, V_new, f_new, N_new, tau_new
        self.n_total += 1
        if self.n_total % self.path_unit == 0:
            self.elem.start_path_unit(self.X, N_a=self.Nax)

    def load_step(self, tau_target):
        t0 = self.tau
        for _ in range(self.ramp_steps):
            self._step((tau_target - t0) / self.ramp_steps)
        self.tau = tau_target
        it, conv = self.ramp_steps, False
        while it < self.max_steps:
            for _ in range(self.check_every):
                self._step(0.0)
            it += self.check_every
            F = self.force(self.X, self.f_int, self.tau)
            g = self.area.grad(self.X)
            scale = max(abs(self.tau) * np.linalg.norm(g), 1e-30)
            eta_R = np.linalg.norm(F) / scale
            U = self.elem.energy(self.X)
            T = 0.5 * float(np.sum(self.m[:, None] * self.V ** 2))
            eta_K = T / max(U, 1e-30)
            if eta_R < self.tol_R and eta_K < self.tol_K:
                conv = True; break
        U = self.elem.energy(self.X); T = 0.5 * float(np.sum(self.m[:, None] * self.V ** 2))
        return dict(tau=tau_target, A=self.area.area(self.X), U=U, T=T, W_ext=self.W_ext,
                    D=self.D, eta_R=eta_R, eta_K=eta_K, steps=it, converged=conv,
                    balance=(self.W_ext - U - T - self.D) / max(abs(self.W_ext), 1e-30))


def newton_tension(net, area, X, tau, free_dofs, max_iter=50, tol=1e-11):
    """Independent implicit solver: f_int(X) + tau H X = 0 on free DOFs,
    consistent Jacobian -(K_t - tau H). Returns coords and min eigenvalue of the
    free-DOF stiffness (stability)."""
    import scipy.sparse.linalg as spla
    X = X.copy()
    fd = np.asarray(free_dofs)
    for it in range(max_iter):
        r = (net.internal_forces(X).ravel() + tau * (area.H @ X.ravel()))[fd]
        if np.linalg.norm(r) < tol * max(1.0, abs(tau) * np.linalg.norm((area.H @ X.ravel())[fd])):
            break
        K = (net.tangent(X) - tau * area.H).tocsc()[fd][:, fd]
        dx = spla.spsolve(K, r)
        x = X.ravel(); x[fd] += dx; X = x.reshape(-1, 3)
    K = (net.tangent(X) - tau * area.H).tocsc()[fd][:, fd]
    lam = spla.eigsh(K, k=1, sigma=-1e-3, which='LM', return_eigenvectors=False)[0]
    return X, it, float(np.linalg.norm(r)), float(lam)
