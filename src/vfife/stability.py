"""ANM Hessian, constrained stability analysis, and mode-overlap utilities."""

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.sparse.linalg._eigen.arpack import ArpackError


def anm_hessian(coords0, pairs, gamma=1.0):
    """ANM Hessian (3N x 3N sparse) with uniform spring constant gamma.

    H_pp = sum_e gamma * n n^T ;  H_pq = -gamma * n n^T.
    At the reference configuration this equals the VFIFE tangent K_t(X).
    """
    N = coords0.shape[0]
    d = coords0[pairs[:, 1]] - coords0[pairs[:, 0]]
    l = np.linalg.norm(d, axis=1)
    n = d / l[:, None]
    vals = (gamma * n[:, :, None] * n[:, None, :]).ravel()   # gamma * n n^T
    p, q = pairs[:, 0], pairs[:, 1]

    def block_rows(node):
        rr = 3 * node[:, None] + np.arange(3)[None, :]
        return np.repeat(rr, 3, axis=1).ravel()

    def block_cols(node):
        cc = 3 * node[:, None] + np.arange(3)[None, :]
        return np.tile(cc, (1, 3)).ravel()

    r = np.concatenate([block_rows(p), block_rows(q),
                        block_rows(p), block_rows(q)])
    c = np.concatenate([block_cols(p), block_cols(q),
                        block_cols(q), block_cols(p)])
    v = np.concatenate([vals, vals, -vals, -vals])
    H = sp.coo_matrix((v, (r, c)), shape=(3 * N, 3 * N)).tocsr()
    H.sum_duplicates()
    return H


def rigid_anchor_dofs(coords, exclude_nodes=None):
    """Minimal 6-DOF anchor removing all rigid-body modes, selected by QR
    column pivoting on the rigid-mode basis so that the 6x6 constraint matrix
    is well conditioned (no leakage of near-rigid modes into the spectrum).

    exclude_nodes: node indices whose DOFs must not be used as anchors
    (e.g. membrane nodes under radial displacement control — an anchor at a
    BC-driven node creates a conflicting constraint pair).

    Returns array of 6 constrained DOF indices.
    """
    X = coords
    N = X.shape[0]
    c = X.mean(axis=0)
    B = np.zeros((3 * N, 6))
    B[:, 0:3] = np.tile(np.eye(3), (N, 1))
    for i in range(N):
        r = X[i] - c
        B[3 * i:3 * i + 3, 3] = np.cross([1, 0, 0], r)
        B[3 * i:3 * i + 3, 4] = np.cross([0, 1, 0], r)
        B[3 * i:3 * i + 3, 5] = np.cross([0, 0, 1], r)
    if exclude_nodes is not None and len(exclude_nodes) > 0:
        excl = np.zeros(3 * N, bool)
        excl[np.asarray(exclude_nodes)[:, None] * 3 + np.arange(3)] = True
        B[excl, :] = 0.0
    # pivots select maximally independent rows (DOFs) of B: greedy pivoted Gram-Schmidt (= QR with column
    # pivoting on B.T). LAPACK's pivot choice among near-equal column norms depends on the BLAS/LAPACK build, which
    # made the anchor set (and every anchored result) machine dependent; here norms are compared after rounding to
    # 1e-9 relative and ties go to the lowest DOF index, so the selection is reproducible.
    Rm = B.copy(); piv = []
    for _ in range(6):
        nrm = np.einsum('ij,ij->i', Rm, Rm)
        v = np.round(nrm / nrm.max(), 9)
        i = int(np.flatnonzero(v == v.max())[0]); piv.append(i)
        q = Rm[i] / np.sqrt(nrm[i]); Rm -= np.outer(Rm @ q, q); Rm[i] = 0.0
    anchor = np.sort(np.array(piv))
    return anchor


def admissible_basis(coords0, mem_idx, e_r, anchor_dofs):
    """Sparse basis Z (3N x n_adm) of perturbations admissible under
    radial displacement control: all Cartesian DOFs except anchors, with the
    radial direction at each membrane node replaced by its two orthogonal
    directions (e_t = z x e_r and e_z)."""
    N = coords0.shape[0]
    ndof = 3 * N
    mem_idx = np.asarray(mem_idx, int)
    e_r = np.asarray(e_r, float)
    e_t = np.cross([0.0, 0.0, 1.0], e_r)          # (-e_ry, e_rx, 0)
    e_t /= np.linalg.norm(e_t, axis=1)[:, None]
    e_z = np.tile([0.0, 0.0, 1.0], (len(mem_idx), 1))

    anchor = set(int(d) for d in anchor_dofs)
    mem_set = set(int(i) for i in mem_idx)
    mem_pos = {int(i): k for k, i in enumerate(mem_idx)}
    cols = []
    rows = []
    vals = []
    j = 0
    for i in range(N):
        if i in mem_set:
            k = mem_pos[i]
            for e in (e_t[k], e_z[k]):
                nz = np.nonzero(e)[0]
                for d in nz:
                    cols.append(j)
                    rows.append(3 * i + int(d))
                    vals.append(float(e[d]))
                j += 1
        else:
            for d in range(3):
                dof = 3 * i + d
                if dof in anchor:
                    continue
                cols.append(j)
                rows.append(dof)
                vals.append(1.0)
                j += 1
    Z = sp.coo_matrix((vals, (rows, cols)), shape=(ndof, j)).tocsr()
    return Z


def constrained_stability(K_t, Z, k=8, sigma=-1e-3):
    """Smallest eigenvalues of K_adm = Z^T K_t Z via shift-invert Lanczos.

    Returns (eigvals ascending, eigvecs in admissible coordinates y).
    Full-DOF mode vectors: delta_u = Z @ y.
    """
    Kadm = (Z.T @ K_t @ Z).tocsc()
    try:
        vals, vecs = spla.eigsh(Kadm, k=k, sigma=sigma, which='LM')
    except RuntimeError:
        try:
            v0 = np.random.default_rng(0).standard_normal(Kadm.shape[0])
            vals, vecs = spla.eigsh(Kadm, k=k, which='SA', v0=v0,
                                    maxiter=20000, tol=1e-10)
        except ArpackError:
            # last resort: dense spectrum of a banded subset is too costly;
            # retry shift-invert with a different shift
            vals, vecs = spla.eigsh(Kadm, k=k, sigma=-1.0, which='LM')
    order = np.argsort(vals)
    return vals[order], vecs[:, order]


def mode_overlap(phi_dof, du_dof):
    """|phi . du| / (|phi| |du|) with full-DOF vectors."""
    phi = np.asarray(phi_dof).ravel()
    du = np.asarray(du_dof).ravel()
    return abs(float(phi @ du)) / (np.linalg.norm(phi) * np.linalg.norm(du))


def random_direction_null(Z, du_adm, n_null=200, seed=0):
    """Null distribution: overlap of du with random unit vectors drawn in the
    admissible subspace (columns of Z)."""
    rng = np.random.default_rng(seed)
    du = np.asarray(du_adm).ravel()
    null = np.empty(n_null)
    for s in range(n_null):
        y = rng.normal(size=Z.shape[1])
        v = Z @ y
        nv = np.linalg.norm(v)
        if nv < 1e-30:
            null[s] = 0.0
        else:
            null[s] = abs(float(du @ v)) / (np.linalg.norm(du) * nv)
    return null


def direction_shuffled_null(Z, du_full, node_groups_adm, n_null=200, seed=0):
    """Null preserving per-node displacement magnitude, randomizing direction.
    node_groups_adm: list of admissible-column index arrays, one per node.
    """
    rng = np.random.default_rng(seed)
    du_adm = np.asarray(Z.T @ np.asarray(du_full).ravel())
    null = np.empty(n_null)
    for s in range(n_null):
        sim = np.zeros_like(du_adm)
        for g in node_groups_adm:
            v = rng.normal(size=len(g))
            v /= np.linalg.norm(v)
            mag = np.linalg.norm(du_adm[g])
            sim[g] = v * mag
        null[s] = abs(float(du_adm @ sim)) / (
            np.linalg.norm(du_adm) * np.linalg.norm(sim) + 1e-30)
    return null


# ---------------------------------------------------------------------------
# Anchor-invariant (rigid-subspace-projected) spectrum  [Round 3, Major 1]
# ---------------------------------------------------------------------------

def rigid_basis(coords):
    """Orthonormal basis Q (3N x 6) of the rigid-body subspace:
    3 translations + 3 rotations about the centroid (Eckart frame)."""
    coords = np.asarray(coords, float)
    n = coords.shape[0]
    c = coords.mean(axis=0)
    x = coords - c
    cols = np.zeros((3 * n, 6))
    for d in range(3):
        cols[d::3, d] = 1.0                       # translations
    for a in range(3):                            # rotations: omega_a x x
        i, j = (1, 2) if a == 0 else ((2, 0) if a == 1 else (0, 1))
        v = np.zeros((n, 3))
        v[:, i] = x[:, j]
        v[:, j] = -x[:, i]
        cols[:, 3 + a] = v.ravel()
    q, _ = np.linalg.qr(cols)
    return q                                      # (3N, 6), orthonormal


def _pkp_operator(K, Q):
    """LinearOperator P K P with P = I - Q Q^T (exact, via Woodbury form
    P K P = K - U M U^T, U = [Q, KQ], M = [[Q^T K Q, -I], [-I, 0]])."""
    KQ = K @ Q
    QtKQ = Q.T @ KQ
    M = np.zeros((12, 12))
    M[:6, :6] = -QtKQ
    M[:6, 6:] = np.eye(6)
    M[6:, :6] = np.eye(6)
    U = sp.hstack([sp.csc_matrix(Q), sp.csc_matrix(KQ)], format='csc')
    n = K.shape[0]

    def matvec(x):
        return K @ x - U @ (M @ (U.T @ x))

    return spla.LinearOperator((n, n), matvec=matvec), U, M


def projected_spectrum(K, coords, k=12, sigma=None, ncv=None):
    """Lowest eigenvalues of the tangent stiffness restricted to the
    orthogonal complement of the rigid-body subspace (anchor-invariant
    spectrum; Eckart-style projection).

    Exact shift-invert via Woodbury: with W = K - sigma I (sparse LU) and
    A = P K P = K - U M U^T,
        (A - sigma I)^{-1} = W^{-1} + W^{-1} U (M^{-1} - U^T W^{-1} U)^{-1} U^T W^{-1}.

    Returns (eigvals ascending, eigvecs full-DOF).
    """
    n = K.shape[0]
    Q = rigid_basis(coords)
    scale = float(np.median(K.diagonal()))
    if sigma is None:
        sigma = -1e-4 * scale
    A_op, U, M = _pkp_operator(K, Q)
    W = (K - sigma * sp.eye(n, format='csc')).tocsc()
    lu = spla.splu(W)

    Minv = np.linalg.inv(M)
    WU = np.asarray(lu.solve(U.todense()))         # (n, 12) = W^{-1} U
    S = Minv - U.T @ WU                            # (12, 12)
    Sinv = np.linalg.inv(S)

    def opinv_matvec(x):
        y = lu.solve(x)
        return y + WU @ (Sinv @ (U.T @ y))

    OPinv = spla.LinearOperator((n, n), matvec=opinv_matvec, dtype=float)

    def amatvec(x):
        return A_op @ x

    A_lin = spla.LinearOperator((n, n), matvec=amatvec, dtype=float)
    v0 = np.ones(n) / np.sqrt(n)
    # P K P has exactly 6 zero eigenvalues (the rigid directions); request
    # k+6 and drop the rigid zeros so near-mechanism modes are not crowded
    # out by them in the shift-invert window.
    kk = k + 6
    ncv_use = ncv if ncv is not None else max(2 * k + 8, 36)
    vals = vecs = None
    for attempt, (ncv_a, tol_a, mi) in enumerate(
            [(ncv_use, 1e-10, 100000), (4 * kk, 1e-8, 300000),
             (8 * kk, 1e-6, 500000)]):
        try:
            vals, vecs = spla.eigsh(A_lin, k=kk, sigma=sigma, which='LM',
                                    OPinv=OPinv, v0=v0, ncv=ncv_a,
                                    tol=tol_a, maxiter=mi)
            break
        except (ArpackError, RuntimeError) as e:
            if attempt == 2:
                # dense fallback for small systems; penalty fallback otherwise
                if n <= 6000:
                    Qd = rigid_basis(coords)
                    P = np.eye(n) - Qd @ Qd.T
                    Kp = P @ K.toarray() @ P
                    ev, V = np.linalg.eigh(Kp)
                    mask = np.abs(ev) > 1e-9 * max(abs(ev).max(), 1)
                    vals, vecs = ev[mask], V[:, mask]
                    order = np.argsort(vals)
                    vals, vecs = vals[order], vecs[:, order]
                    return vals[:k], vecs[:, :k]
                raise
    order = np.argsort(vals)
    vals, vecs = vals[order], vecs[:, order]
    return vals[6:], vecs[:, 6:]
