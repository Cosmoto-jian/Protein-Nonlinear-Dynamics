"""Core conservative truss-network mechanics for VFIFE-PN.

Units: coordinates in Angstrom, spring constants k_e in gamma (force/length),
energy in gamma*A^2, forces in gamma*A.  Baseline model: uniform k_e = gamma
so that the initial tangent stiffness equals the ANM Hessian exactly.

Everything is derived from one conservative potential:
    U_e = 1/2 * k_e * (l - l0)^2
    T_e = k_e * (l - l0)              (tension > 0)
    f_int = -grad U
    A_e   = k_e * n n^T + (T_e/l) * (I - n n^T)   (3x3 element tangent)
    K_e   = [[ A_e, -A_e], [-A_e, A_e]]
"""

import numpy as np
import scipy.sparse as sp


class TrussNetwork:
    """Conservative elastic network (Calpha coarse-grained)."""

    def __init__(self, coords0, pairs, k=1.0, l0=None):
        """
        coords0 : (N,3) reference coordinates
        pairs   : (E,2) int, 0-based node indices
        k       : float or (E,) array, element spring constant k_e
        l0      : optional (E,) reference lengths (default: from coords0)
        """
        self.coords0 = np.asarray(coords0, float)
        self.pairs = np.asarray(pairs, int)
        self.N = self.coords0.shape[0]
        self.E = self.pairs.shape[0]
        self.k = np.broadcast_to(np.asarray(k, float), (self.E,)).astype(float).copy()
        if l0 is None:
            self.l0 = self.element_lengths(self.coords0)
        else:
            self.l0 = np.asarray(l0, float).copy()

    # ---------- element state (vectorized) ----------

    def element_lengths(self, coords):
        d = coords[self.pairs[:, 1]] - coords[self.pairs[:, 0]]
        return np.linalg.norm(d, axis=1)

    def element_state(self, coords):
        """Return n (E,3), l (E,), T (E,), U_e (E,)."""
        d = coords[self.pairs[:, 1]] - coords[self.pairs[:, 0]]
        l = np.linalg.norm(d, axis=1)
        n = d / l[:, None]
        T = self.k * (l - self.l0)
        U = 0.5 * self.k * (l - self.l0) ** 2
        return n, l, T, U

    # ---------- energy / internal force / tangent ----------

    def energy(self, coords):
        _, _, _, U = self.element_state(coords)
        return U.sum()

    def internal_forces(self, coords):
        """f_int = -grad U, shape (N,3).  f_int[p] = T*n for element (p,q)."""
        n, l, T, _ = self.element_state(coords)
        fe = T[:, None] * n                      # force on node p (toward q)
        f = np.zeros((self.N, 3))
        for comp in range(3):
            f[:, comp] = (np.bincount(self.pairs[:, 0], weights=fe[:, comp],
                                      minlength=self.N)
                          - np.bincount(self.pairs[:, 1],
                                        weights=fe[:, comp],
                                        minlength=self.N))
        return f

    def tangent(self, coords):
        """Global sparse tangent stiffness K_t (3N x 3N), CSR."""
        n, l, T, _ = self.element_state(coords)
        # A_e = k n n^T + (T/l)(I - n n^T)
        a_diag = (T / l)                          # coefficient of I
        a_nn = self.k - T / l                     # coefficient of n n^T
        p, q = self.pairs[:, 0], self.pairs[:, 1]

        def block_rows(node):
            rr = 3 * node[:, None] + np.arange(3)[None, :]   # (E,3)
            return np.repeat(rr, 3, axis=1).ravel()          # (E*9,)

        def block_cols(node):
            cc = 3 * node[:, None] + np.arange(3)[None, :]   # (E,3)
            return np.tile(cc, (1, 3)).ravel()               # (E*9,)

        # vals[i,j] = a_diag*delta_ij + a_nn*n_i*n_j, i = row dir, j = col dir
        delta = (np.arange(3)[None, :, None] == np.arange(3)[None, None, :])
        vals = (a_diag[:, None, None] * delta
                + a_nn[:, None, None] * n[:, :, None] * n[:, None, :])
        vals = vals.ravel()

        r = np.concatenate([block_rows(p), block_rows(q),
                            block_rows(p), block_rows(q)])
        c = np.concatenate([block_cols(p), block_cols(q),
                            block_cols(q), block_cols(p)])
        v = np.concatenate([vals, vals, -vals, -vals])
        K = sp.coo_matrix((v, (r, c)), shape=(3 * self.N, 3 * self.N)).tocsr()
        K.sum_duplicates()
        return K

    # ---------- convenience ----------

    def dof_indices(self):
        return np.arange(3 * self.N)
