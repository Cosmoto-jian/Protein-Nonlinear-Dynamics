"""Vector Form Intrinsic Finite Element (VFIFE) explicit path solver.

Formulation (Ting, Shih & Wang 2004; Shih, Wang & Ting 2004), specialised to
2-node truss (spring) elements of a C-alpha network:

  * Point-value description: the structure is a set of mass points.  Each
    point obeys Newton's 2nd law with fictitious mass m_i and mass-
    proportional damping alpha:
          m_i a_i + alpha m_i v_i = f_i^ext + f_i^int
    and is integrated by the explicit central-difference scheme.
  * Path units: the motion is cut into path units [t_a, t_b].  Within one
    unit the element reference configuration (x_a, l_a, e_a, N_a) is frozen.
  * Fictitious reverse motion: in each step the element's rigid translation
    (node p) and rigid rotation (e_a -> e) are removed; the remaining pure
    deformation gives the axial-force increment dN = k * dl; the force is
    then rotated forward to the current configuration.
  * No global stiffness matrix is ever assembled or inverted.

For a truss element the reverse-motion deformation is exactly l - l_a, so the
accumulated force N = N_a + k (l - l_a) equals the total-Lagrangian value
k (l - l0); this identity is itself a verification test (V0).

Loading: membrane nodes carry a prescribed radial displacement
u_i . e_r,i = alpha_i q(t); tangential and vertical motion stay free.
Anchor DOFs (optional) are held fixed.  The prescribed radial DOFs are
massless actuators; kinetic energy and damping act on the admissible
(free) motion only, so the discrete work balance reads
          W_act = U + T + D.
"""

import time
import numpy as np


# --------------------------------------------------------------------------
# element kinematics with explicit fictitious reverse motion
# --------------------------------------------------------------------------

def _rodrigues_rotate(v, axis, cos_t, sin_t):
    """Rotate row vectors v about unit axes by angle (cos_t, sin_t)."""
    kxv = np.cross(axis, v)
    kdv = np.sum(axis * v, axis=1)[:, None]
    return v * cos_t[:, None] + kxv * sin_t[:, None] + axis * kdv * (1 - cos_t)[:, None]


class VFIFETruss:
    """Truss-element internal forces by VFIFE reverse motion."""

    def __init__(self, coords0, pairs, k=1.0, l0=None):
        self.pairs = np.asarray(pairs, int)
        self.p, self.q = self.pairs[:, 0], self.pairs[:, 1]
        self.N = coords0.shape[0]
        self.E = len(self.pairs)
        self.k = np.broadcast_to(np.asarray(k, float), (self.E,)).copy()
        d0 = coords0[self.q] - coords0[self.p]
        self.l0 = np.linalg.norm(d0, axis=1) if l0 is None else np.asarray(l0, float)
        # path-unit reference state (starts at the stress-free reference)
        self.start_path_unit(coords0, N_a=self.k * (np.linalg.norm(d0, axis=1) - self.l0))

    def start_path_unit(self, coords, N_a=None):
        d = coords[self.q] - coords[self.p]
        self.l_a = np.linalg.norm(d, axis=1)
        self.e_a = d / self.l_a[:, None]
        if N_a is not None:
            self.N_a = np.asarray(N_a, float).copy()
        else:
            self.N_a = self.axial_force(coords)

    def axial_force(self, coords):
        """Axial force via fictitious reverse motion relative to path unit a."""
        d = coords[self.q] - coords[self.p]            # after removing translation of p
        l = np.linalg.norm(d, axis=1)
        e = d / l[:, None]
        # rigid rotation e_a -> e : axis w = e_a x e, angle theta
        w = np.cross(self.e_a, e)
        s = np.linalg.norm(w, axis=1)
        c = np.sum(self.e_a * e, axis=1)
        axis = np.zeros_like(w)
        ok = s > 1e-14
        axis[ok] = w[ok] / s[ok, None]
        # reverse rotation (-theta) brings the current element vector back
        d_rev = _rodrigues_rotate(d, axis, c, -s)
        # pure deformation displacement in the reference frame of unit a
        eta = d_rev - self.l_a[:, None] * self.e_a
        dl = np.sum(eta * self.e_a, axis=1)            # axial deformation
        return self.N_a + self.k * dl, e, l

    def internal_forces(self, coords):
        """f_int (N,3): force on node p is +N e (towards q), on q is -N e."""
        Nax, e, _ = self.axial_force(coords)
        fe = Nax[:, None] * e                          # forward rotation: along current e
        f = np.zeros((self.N, 3))
        for c in range(3):
            f[:, c] = (np.bincount(self.p, weights=fe[:, c], minlength=self.N)
                       - np.bincount(self.q, weights=fe[:, c], minlength=self.N))
        return f, Nax

    def energy(self, coords):
        d = coords[self.q] - coords[self.p]
        l = np.linalg.norm(d, axis=1)
        return 0.5 * float(np.sum(self.k * (l - self.l0) ** 2))


# --------------------------------------------------------------------------
# radial displacement control
# --------------------------------------------------------------------------

class RadialControl:
    def __init__(self, coords0, mem_idx, e_r3, alpha=None, anchor_dofs=()):
        self.N = coords0.shape[0]
        self.coords0 = coords0
        self.mem = np.asarray(mem_idx, int)
        self.e_r = np.asarray(e_r3, float)
        self.alpha = np.ones(len(self.mem)) if alpha is None else np.asarray(alpha, float)
        self.anchor = np.asarray(anchor_dofs, int)
        fm = np.ones(3 * self.N)
        fm[self.anchor] = 0.0
        self.free_mask = fm.reshape(self.N, 3)

    def project_free(self, v):
        """Project a nodal field (N,3) onto admissible (free) directions."""
        v = v * self.free_mask
        vr = np.sum(v[self.mem] * self.e_r, axis=1)
        v[self.mem] -= vr[:, None] * self.e_r
        return v

    def radial_field(self):
        u = np.zeros((self.N, 3))
        u[self.mem] = self.alpha[:, None] * self.e_r
        return u

    def reaction(self, f_int):
        """Generalised reaction Q = -sum f_int . (alpha e_r) on membrane nodes."""
        return float(-np.sum(f_int[self.mem] * (self.alpha[:, None] * self.e_r)))

    def enforce(self, X, q):
        u = X[self.mem] - self.coords0[self.mem]
        ur = np.sum(u * self.e_r, axis=1)
        X[self.mem] += ((self.alpha * q) - ur)[:, None] * self.e_r
        if len(self.anchor):
            Xf = X.ravel()
            Xf[self.anchor] = self.coords0.ravel()[self.anchor]
        return X


# --------------------------------------------------------------------------
# fictitious mass
# --------------------------------------------------------------------------

def nodal_mass_gershgorin(elem, coords, safety=1.0):
    """Isotropic point mass m_i = 0.5 * max_d rowsum_d |K_t| at node i.
    With dt <= 1 this keeps every point below its Gershgorin critical step."""
    d = coords[elem.q] - coords[elem.p]
    l = np.linalg.norm(d, axis=1)
    n = d / l[:, None]
    T = elem.k * (l - elem.l0)
    # |A_e| row sums: A = k nn^T + (T/l)(I - nn^T)
    A = (elem.k - T / l)[:, None, None] * n[:, :, None] * n[:, None, :] \
        + (T / l)[:, None, None] * np.eye(3)[None]
    rs = np.abs(A).sum(axis=2)                      # (E,3)
    row = np.zeros((elem.N, 3))
    for c in range(3):
        row[:, c] = (np.bincount(elem.p, weights=rs[:, c], minlength=elem.N)
                     + np.bincount(elem.q, weights=rs[:, c], minlength=elem.N))
    m = 0.5 * 2.0 * row.max(axis=1)     # factor 2: block |A| appears in diag and off-diag
    m[m <= 0] = 1.0
    return safety * m


# --------------------------------------------------------------------------
# path solver
# --------------------------------------------------------------------------

class VFIFEPathSolver:
    """Quasi-static radial loading path by explicit VFIFE dynamics."""

    def __init__(self, elem, ctrl, mass, alpha_damp, dt=1.0, path_unit=1,
                 tol_R=1e-9, tol_K=1e-12, ramp_steps=200, max_steps=400000,
                 check_every=50):
        self.elem, self.ctrl = elem, ctrl
        self.m = np.asarray(mass, float)
        self.alpha = float(alpha_damp)
        self.dt = float(dt)
        self.path_unit = int(path_unit)
        self.tol_R, self.tol_K = tol_R, tol_K
        self.ramp_steps, self.max_steps = ramp_steps, max_steps
        self.check_every = check_every
        N = elem.N
        self.X = ctrl.coords0.copy()
        self.V = np.zeros((N, 3))               # v_{n-1/2}
        self.q = 0.0
        self.n_total = 0
        self.f, self.Nax = elem.internal_forces(self.X)
        # energy book-keeping
        self.W_act = 0.0
        self.D = 0.0
        self.history = []

    def kinetic(self, V=None):
        V = self.V if V is None else V
        return 0.5 * float(np.sum(self.m[:, None] * V ** 2))

    def _step(self, dq):
        dt, a = self.dt, self.alpha
        c1, c2 = 1.0 + 0.5 * a * dt, 1.0 - 0.5 * a * dt
        acc = self.ctrl.project_free(self.f) / self.m[:, None]
        V_old = self.V
        V_new = (c2 * V_old + dt * acc) / c1
        V_new = self.ctrl.project_free(V_new)
        X_new = self.X + dt * V_new
        X_new = self.ctrl.enforce(X_new, self.q + dq)     # actuator moves radial DOFs
        # path-unit bookkeeping (reference frame of reverse motion)
        self.n_total += 1
        f_new, N_new = self.elem.internal_forces(X_new)
        # actuator work (trapezoid on prescribed radial increment)
        du_act = dq * self.ctrl.radial_field()
        self.W_act += -0.5 * float(np.sum((self.f + f_new) * du_act))
        # damping dissipation with mid-step velocity estimate
        v_mid = 0.5 * (V_old + V_new)
        self.D += a * dt * float(np.sum(self.m[:, None] * v_mid ** 2))
        self.X, self.V, self.f, self.Nax = X_new, V_new, f_new, N_new
        self.q += dq
        if self.n_total % self.path_unit == 0:
            self.elem.start_path_unit(self.X, N_a=self.Nax)

    def residual(self):
        r = self.ctrl.project_free(self.f)
        return float(np.linalg.norm(r))

    def load_step(self, q_target):
        """Ramp q to q_target over ramp_steps, then hold until quasi-static."""
        q0 = self.q
        n_r = self.ramp_steps
        for i in range(n_r):
            self._step((q_target - q0) / n_r)
        self.q = q_target
        it = n_r
        conv = False
        while it < self.max_steps:
            for _ in range(self.check_every):
                self._step(0.0)
            it += self.check_every
            Q = self.ctrl.reaction(self.f)
            eta_R = self.residual() / max(abs(Q), 1e-30)
            U = self.elem.energy(self.X)
            eta_K = self.kinetic() / max(U, 1e-30)
            if eta_R < self.tol_R and eta_K < self.tol_K:
                conv = True
                break
        U = self.elem.energy(self.X)
        T = self.kinetic()
        rec = dict(q=q_target, Q=self.ctrl.reaction(self.f), U=U, T=T,
                   W_act=self.W_act, D=self.D, eta_R=eta_R, eta_K=eta_K,
                   steps=it, converged=conv,
                   balance=(self.W_act - U - T - self.D) / max(self.W_act, 1e-30))
        self.history.append(rec)
        return rec


def critical_damping(elem, ctrl, mass, coords, Z, K_t):
    """alpha = 2 * omega_min of the admissible generalized eigenproblem."""
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    Mfull = np.repeat(mass, 3)
    Madm = sp.diags(Z.T @ Mfull) if False else (Z.T @ sp.diags(Mfull) @ Z).tocsc()
    Kadm = (Z.T @ K_t @ Z).tocsc()
    lam = spla.eigsh(Kadm, k=1, M=Madm, sigma=-1e-6, which='LM',
                     return_eigenvectors=False)[0]
    w_min = np.sqrt(max(lam, 1e-30))
    return 2.0 * w_min, w_min
