"""Common machinery for the r5 calculations: C-alpha truss model, membrane-tension load
(shell-averaged polygon area, exactly self-equilibrated), Eckart gauge, Newton solver,
target mapping and metrics.  All paths are relative to this file."""
import sys, os, json, time, itertools
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
_HERE = os.path.dirname(os.path.abspath(__file__))
HERE = _HERE
sys.path.insert(0, _HERE)
from vfife.preprocess import build_model
from vfife.core import TrussNetwork
from vfife.stability import rigid_anchor_dofs

from paths import DERIVED, raw
import kkt as _kkt                                     # PARDISO bordered-KKT fast path (falls back to scipy)
RES = str(DERIVED)
PDB = os.path.join(RES, 'models')                       # C-alpha model inputs written by src/prepare_models.py
os.makedirs(os.path.join(RES, 'paths'), exist_ok=True)
THREE = {'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E','GLY':'G','HIS':'H','ILE':'I','LEU':'L',
         'LYS':'K','MET':'M','PHE':'F','PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V','MSE':'M'}

# protein -> model file, chains kept, experimental target (None = no tension-related partner)
LABEL = {'6b3r': 'Piezo1', '6pwn': 'MscS', '2oar': 'MscL', '4xdk': 'TREK-2', '4wff': 'TRAAK',
         '6mgv': 'OSCA1.2', '6cq8': '6CQ8', '6vtk': '6VTK'}
PANEL = ['6b3r', '6pwn', '2oar', '4xdk', '4wff', '6mgv']
EXTRA = ['6cq8', '6vtk']

PROTEINS = {
    '2oar': dict(pdb=f'{PDB}/2oar.pdb', chains=None, target=dict(kind='homolog', closed=raw('4Y7K.pdb'), open=raw('4Y7J.pdb'),
                 cut_after='KKVLQEEKVEK', label='MaMscL 4Y7K->4Y7J (homolog, expanded)')),
    '4wff': dict(pdb=f'{PDB}/4wff.pdb', chains=None, target=dict(kind='same', open=raw('4WFE.pdb'), open_chains='AB',
                 label='TRAAK 4WFE (conductive)')),
    '6pwn': dict(pdb=f'{PDB}/6pwn.pdb', chains=None, target=dict(kind='same', open=raw('2VV5.pdb'), label='MscS 2VV5 (open, A106V)')),
    '6b3r': dict(pdb=f'{PDB}/6b3r.pdb', chains=None, target=dict(kind='same', open=raw('8IXO.pdb'), label='mPiezo1 8IXO (intermediate)')),
    '6mgv': dict(pdb=f'{PDB}/6mgv.pdb', chains=None, target=dict(kind='same', open=raw('8XAJ.pdb'), label='OSCA1.2 8XAJ (open, liposome)')),
    '6cq8': dict(pdb=f'{PDB}/6cq8.pdb', chains=None, target=None),
    '4xdk': dict(pdb=f'{PDB}/4xdk.pdb', chains=None, target=dict(kind='same', open=raw('4BW5.pdb'), label='TREK-2 4BW5 (up)')),
    '6vtk': dict(pdb=f'{PDB}/6vtk.pdb', chains=None, target=None),
}


def read_ca(f, chains=None):
    d, order = {}, []
    for l in open(f):
        if l.startswith(('ATOM', 'HETATM')) and l[12:16] == ' CA ' and l[16] in ' A':
            c, r = l[21], int(l[22:26])
            if chains and c not in chains:
                continue
            if (c, r) in d:
                continue
            d[(c, r)] = (THREE.get(l[17:20], 'X'), np.array([float(l[30:38]), float(l[38:46]), float(l[46:54])]))
            order.append((c, r))
    return d, order


def filtered_pdb(name):
    P = PROTEINS[name]
    if not P['chains']:
        return P['pdb']
    out = f'{RES}/models/{name}_chains.pdb'
    if not os.path.exists(out):
        with open(P['pdb']) as f, open(out, 'w') as g:
            for l in f:
                if l.startswith(('ATOM', 'HETATM', 'TER')) and l[21] not in P['chains']:
                    continue
                g.write(l)
    return out


def kabsch(P, Q):
    pc, qc = P.mean(0), Q.mean(0)
    U, S, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    R = Vt.T @ D @ U.T
    return R, qc - R @ pc


def rmsd_fit(P, Q):
    R, t = kabsch(P, Q)
    return float(np.sqrt(((P @ R.T + t - Q) ** 2).sum(1).mean()))


def model(name, rc=10.0):
    f = filtered_pdb(name)
    m = build_model(f, cutoff=rc)
    d, _ = read_ca(f)
    order = [(str(c), int(r)) for c, r in m['config']['chain_residue_map']]
    assert len(order) == len(m['coords0']), (len(order), len(m['coords0']))
    X = m['coords0']
    for i, k in enumerate(order):          # the model's own coordinates are authoritative (altlocs/insertions)
        d[k] = (d[k][0] if k in d else 'X', X[i].copy())
    return dict(m=m, X0=m['coords0'], pairs=m['pairs'], mem=m['mem_idx'], order=order, ca=d, pdb=f)


# ---------------- tension load ----------------
class ShellBoundaryArea:
    """Lipid-facing boundary as a star polygon per slab whose vertices are the MEAN of the outer shell of
    membrane CA in each angular sector (nodes within `shell` A of the sector's outermost radius). Vertices are
    fixed linear combinations of nodal coordinates, so A = 1/2 X^T H X stays an exact quadratic form with a
    constant H, the load stays conservative and self-equilibrated, and tension is spread over the whole outer
    shell instead of single protruding nodes."""
    def __init__(self, X0, mem_idx, axis_xy, z_mid, half_thick, slab=4.0, n_sector=30, shell=4.0, min_vertices=6):
        N = X0.shape[0]; mem = np.asarray(mem_idx, int); c = np.asarray(axis_xy, float)
        edges = np.arange(z_mid - half_thick, z_mid + half_thick + 1e-9, slab)
        rowsB, colsB, valsB, polys, nv = [], [], [], [], 0
        loaded = set()
        for z0, z1 in zip(edges[:-1], edges[1:]):
            sel = mem[(X0[mem, 2] >= z0) & (X0[mem, 2] < z1)]
            if len(sel) < min_vertices:
                continue
            d = X0[sel, :2] - c; ang = np.arctan2(d[:, 1], d[:, 0]); r = np.linalg.norm(d, axis=1)
            sec = np.floor((ang + np.pi) / (2 * np.pi) * n_sector).astype(int) % n_sector
            verts = []
            for s_ in range(n_sector):
                mm = np.where(sec == s_)[0]
                if not len(mm):
                    continue
                sh = mm[r[mm] >= r[mm].max() - shell]
                verts.append((np.arctan2(d[sh, 1].mean(), d[sh, 0].mean()), sel[sh]))
            if len(verts) < min_vertices:
                continue
            verts.sort(key=lambda v: v[0]); poly = []
            for _, nodes in verts:
                w = 1.0 / len(nodes)
                for i in nodes:
                    for comp in (0, 1):
                        rowsB.append(2 * nv + comp); colsB.append(3 * i + comp); valsB.append(w)
                    loaded.add(int(i))
                poly.append(nv); nv += 1
            polys.append(poly)
        Bm = sp.csr_matrix((valsB, (rowsB, colsB)), shape=(2 * nv, 3 * N))
        ws = 1.0 / len(polys); r_, c_, v_ = [], [], []
        for p in polys:
            n = len(p)
            for k in range(n):
                i, j = p[k], p[(k + 1) % n]
                for (a, b, v) in ((2 * i, 2 * j + 1, 0.5), (2 * j, 2 * i + 1, -0.5)):
                    r_ += [a, b]; c_ += [b, a]; v_ += [ws * v, ws * v]
        Hp = sp.csr_matrix((v_, (r_, c_)), shape=(2 * nv, 2 * nv))
        self.H = (Bm.T @ Hp @ Bm).tocsr(); self.polys = polys; self.N = N; self.Bm = Bm
        self.vertices = np.array(sorted(loaded))

    def area(self, X):
        x = X.ravel(); return 0.5 * float(x @ (self.H @ x))

    def grad(self, X):
        return (self.H @ X.ravel()).reshape(-1, 3)


def make_area(M, n_sector=None, n_scale=1.0, shell=4.0, slab=4.0, dh=0.0, equilibrate=False):
    """Membrane-tension area operator.  n_scale scales the sector count, shell/slab are the outer-shell width and
    layer thickness (A), dh changes the membrane half-thickness (A).  With equilibrate=True the operator is
    H' = S^T H S (see EquilibratedArea), which makes the nodal load orthogonal to all six reference rigid modes."""
    m, X0, mem = M['m'], M['X0'], M['mem']
    if dh != 0.0:
        ht0 = float(m['config']['bilayer_half_thickness_A'])
        mem = np.where(np.abs(X0[:, 2] - m['z_mid']) <= ht0 + dh)[0]
    ht = float(np.abs(X0[mem, 2] - m['z_mid']).max()) + 0.01
    R = np.linalg.norm(X0[mem, :2] - m['centroid'], axis=1).max()
    if n_sector is None:
        n_sector = int(np.clip(2 * np.pi * R / 6.0 * n_scale, 12, 240))
    a = ShellBoundaryArea(X0, mem, m['centroid'], m['z_mid'], ht, slab=slab, n_sector=n_sector, shell=shell)
    if equilibrate:
        a = EquilibratedArea(a, X0)
    return a, n_sector


def rigid_basis(X0, nodes=None):
    """3N x 6 rigid-body basis about the centroid of X0 (translations, rotations about x, y, z);
    rows outside `nodes` are zeroed when nodes is given."""
    N = len(X0); c = X0.mean(0); r = X0 - c
    Q = np.zeros((N, 3, 6))
    for k in range(3):
        Q[:, k, k] = 1.0
    for a in range(3):
        e = np.zeros(3); e[a] = 1.0
        Q[:, :, 3 + a] = np.cross(e, r)
    Q = Q.reshape(3 * N, 6)
    if nodes is not None:
        mask = np.zeros(N, bool); mask[np.asarray(nodes, int)] = True
        Q = Q * np.repeat(mask, 3)[:, None]
    return Q


class EquilibratedArea:
    """Exactly self-equilibrated version of a quadratic area load A = 1/2 x^T H x.

    A'(x) = A(S x), S = I - Q (Q_L^T Q)^-1 Q_L^T, with Q the reference rigid basis and Q_L its restriction to the
    loaded nodes.  Then S Q = 0, so the load f' = tau S^T H S x satisfies Q^T f' = 0 for every x: zero resultant
    force and zero resultant moment about the reference centroid.  The correction S^T(.) acts only on loaded nodes,
    the operator stays symmetric and constant, so the load remains conservative.  The removed part is the rigid
    (tilting) component of the original load, which arises from the finite thickness of the 4 A layers."""
    def __init__(self, base, X0):
        self.base = base; H = base.H.tocsr(); N = len(X0)
        Q = rigid_basis(X0); QL = rigid_basis(X0, base.vertices)
        B = np.linalg.inv(QL.T @ Q)                      # 6x6
        L = np.unique(np.concatenate([3 * base.vertices[:, None] + np.arange(3)[None, :]]).ravel())
        # S = I - Q B QL^T ; QL^T is supported on loaded dofs L
        HQ = np.asarray(H @ Q)                           # supported on loaded dofs
        G = QL[L] @ B.T                                  # (|L|,6): rows of S^T correction, S^T = I - QL B^T Q^T
        # H' = (I - QL B^T Q^T) H (I - Q B QL^T)
        #    = H - H Q B QL^T - QL B^T Q^T H + QL B^T (Q^T H Q) B QL^T, all corrections on L x L
        QtHQ = Q.T @ HQ
        T1 = HQ[L] @ (B @ QL[L].T)                       # (|L|,|L|)
        T3 = G @ QtHQ @ G.T
        D = -T1 - T1.T + T3
        D = 0.5 * (D + D.T)
        D[np.abs(D) < 1e-14 * max(np.abs(D).max(), 1e-300)] = 0.0
        ii, jj = np.nonzero(D)
        Dsp = sp.csr_matrix((D[ii, jj], (L[ii], L[jj])), shape=(3 * N, 3 * N))
        self.H = (H + Dsp).tocsr(); self.H.eliminate_zeros()
        self.vertices = base.vertices; self.polys = base.polys; self.Bm = base.Bm; self.N = N
        self.Q = Q; self.S_B = B; self.QL = QL

    def area(self, X):
        x = X.ravel(); return 0.5 * float(x @ (self.H @ x))

    def grad(self, X):
        return (self.H @ X.ravel()).reshape(-1, 3)

    def raw_area(self, X):
        return self.base.area(X)


def polygon_area_direct(area, X):
    """Independent area evaluation: rebuild each layer polygon from the vertex coordinates (shell means)
    and apply the shoelace formula directly (used to verify the sparse operator)."""
    base = getattr(area, 'base', area)
    v = (base.Bm @ X.ravel()).reshape(-1, 2)
    tot = 0.0
    for p in base.polys:
        P = v[p]; x, y = P[:, 0], P[:, 1]
        tot += 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
    return tot / len(base.polys)


def load_resultants(area, X, X0):
    """resultant force and moment of the nodal load tau*grad A (tau = 1) about the reference centroid,
    using current positions, normalised by sum|f| and by sum|f| * max radius."""
    g = area.grad(X); c = X0.mean(0)
    F = g.sum(0); Mo = np.cross(X - c, g).sum(0)
    s = np.abs(g).sum(); Rm = np.linalg.norm(X0 - c, axis=1).max()
    return dict(F=(F / s).tolist(), M=(Mo / (s * Rm)).tolist(), Mxy=float(np.hypot(Mo[0], Mo[1]) / (s * Rm)),
                Mz=float(abs(Mo[2]) / (s * Rm)))


def gauge_C4(X0):
    """the four exact symmetries of the tension potential (x, y, z translation, rotation about the membrane
    normal).  A(x) is invariant under these for every configuration, so the constraint reaction vanishes
    identically; the two tilts are left free and are stabilised by the load stiffness -tau*H."""
    G = rigid_basis(X0)[:, [0, 1, 2, 5]].T
    return G / np.linalg.norm(G, axis=1)[:, None]


def gauge_C(X0):
    N = len(X0); c = X0.mean(0); G = []
    for k in range(3):
        g = np.zeros((N, 3)); g[:, k] = 1; G.append(g.ravel())
    for (a, b) in ((0, 1), (1, 2), (2, 0)):
        g = np.zeros((N, 3)); g[:, a] = -(X0[:, b] - c[b]); g[:, b] = X0[:, a] - c[a]; G.append(g.ravel())
    G = np.array(G); return G / np.linalg.norm(G, axis=1)[:, None]


def _pi(net, area, X, tau):
    return net.energy(X) - tau * area.area(X)


def newton_anchored(net, area, X, tau, fd, max_iter=40, tol=1e-9, stall=3):
    """Newton with backtracking on the potential Pi = U - tau*A (6 minimal anchors).  Early exit (not converged)
    after `stall` consecutive line searches that hit the step floor."""
    if _kkt.AVAILABLE:
        return _kkt.newton_anchored(net, area, X, tau, fd, max_iter, tol, stall)
    floor = 0
    for it in range(max_iter):
        f = net.internal_forces(X).ravel() + tau * (area.H @ X.ravel())
        rel = np.linalg.norm(f[fd]) / max(1.0, tau * np.linalg.norm((area.H @ X.ravel())[fd]))
        if rel < tol:
            return X, it, rel, True
        K = (net.tangent(X) - tau * area.H).tocsc()[fd][:, fd]
        dx = np.zeros(3 * net.N); dx[fd] = spla.spsolve(K, f[fd])
        p0 = _pi(net, area, X, tau); a = 1.0; hit = True
        while a > 1e-4:
            Xn = X + a * dx.reshape(-1, 3)
            if np.all(np.isfinite(Xn)) and _pi(net, area, Xn, tau) <= p0 + 1e-12 * abs(p0):
                hit = False; break
            a *= 0.5
        X = Xn
        if not np.all(np.isfinite(X)):
            return X, it, rel, False
        floor = floor + 1 if hit else 0
        if stall and floor >= stall:
            return X, it, rel, False
    return X, it, rel, False


def newton_eckart(net, area, X, X0, tau, C, max_iter=40, tol=1e-9, stall=3):
    """Anchor-free Newton (bordered system with the 6 Eckart conditions) with backtracking on Pi.  Early exit
    (ok=False) after `stall` consecutive line searches that hit the step floor.  Linear algebra by kkt (PARDISO,
    fixed pattern) when available, otherwise scipy spsolve on the bordered matrix."""
    if _kkt.AVAILABLE:
        return _kkt.newton(net, area, X, X0, tau, C, max_iter, tol, stall)
    n = 3 * net.N; Cs = sp.csr_matrix(C); ok = False; floor = 0
    for it in range(max_iter):
        f = net.internal_forces(X).ravel() + tau * (area.H @ X.ravel())
        mu = np.linalg.lstsq(C.T, -f, rcond=None)[0]; r = f + C.T @ mu
        rel = np.linalg.norm(r) / max(1.0, tau * np.linalg.norm(area.H @ X.ravel()))
        if rel < tol:
            ok = True; break
        K = (net.tangent(X) - tau * area.H).tocsc()
        A = sp.bmat([[K, Cs.T], [Cs, None]]).tocsc()
        dx = spla.spsolve(A, np.concatenate([f, -C @ (X - X0).ravel()]))[:n].reshape(-1, 3)
        p0 = _pi(net, area, X, tau); a = 1.0; hit = True
        while a > 1e-4:
            Xn = X + a * dx
            if np.all(np.isfinite(Xn)) and _pi(net, area, Xn, tau) <= p0 + 1e-12 * abs(p0):
                hit = False; break
            a *= 0.5
        X = Xn
        floor = floor + 1 if hit else 0
        if stall and floor >= stall:
            break
    g = tau * (area.H @ X.ravel())
    return X, it, rel, float(np.linalg.norm(C.T @ mu) / max(np.linalg.norm(g), 1e-30)), ok


class EckartSolver:
    """Fast solve of the Eckart-bordered system [[K, C^T],[C, 0]] [dx; mu] = [r; s] by elimination of six isostatic
    pivot dofs A (C_A invertible) and a rank-12 Woodbury correction of the sparse factorisation of K_FF.  Exact
    (identical to the bordered solve up to round-off) but avoids factorising the dense border rows."""
    def __init__(self, K, C, A):
        n = K.shape[0]; self.n = n; self.A = np.asarray(A); self.F = np.setdiff1d(np.arange(n), self.A)
        K = K.tocsc(); F, A = self.F, self.A; self.K = K; self.C = C
        self.KFF = K[F][:, F].tocsc(); self.KFA = K[F][:, A].toarray(); self.KAF = self.KFA.T; self.KAA = K[A][:, A].toarray()
        self.CA = C[:, A]; self.CF = C[:, F]; self.CAi = np.linalg.inv(self.CA)
        self.G = self.CAi @ self.CF                                  # 6 x nF
        self.lu = spla.splu(self.KFF)
        U = np.hstack([self.KFA, self.G.T])                          # nF x 12
        I6 = np.eye(len(A)); Z6 = np.zeros((len(A), len(A)))
        Minv = np.block([[-self.KAA, -I6], [-I6, Z6]])
        self.U = U; self.Y = self.lu.solve(U)
        self.S = np.linalg.inv(Minv + U.T @ self.Y)

    def solve(self, r, s=None, refine=2):
        s = np.zeros(len(self.A)) if s is None else s
        dx, mu = self._solve(r, s)
        for _ in range(refine):                      # iterative refinement against the full bordered operator
            d, m = self._solve(r - self.K @ dx - self.C.T @ mu, s - self.C @ dx)
            dx, mu = dx + d, mu + m
        return dx, mu

    def _solve(self, r, s=None):
        F, A = self.F, self.A
        s = np.zeros(len(A)) if s is None else s
        rF, rA = r[F], r[A]
        w = self.CAi @ s
        b = rF - self.G.T @ rA - self.KFA @ w + self.G.T @ (self.KAA @ w)
        y = self.lu.solve(b); dxF = y - self.Y @ (self.S @ (self.U.T @ y))
        dxA = w - self.G @ dxF
        dx = np.empty(self.n); dx[F] = dxF; dx[A] = dxA
        mu = np.linalg.solve(self.CA.T, rA - self.KAF @ dxF - self.KAA @ dxA)
        return dx, mu


_PIVOTS = {}


def eckart_pivots(C):
    from scipy.linalg import qr
    key = (C.shape, float(C[:, :30].sum()))
    if key not in _PIVOTS:
        _, _, piv = qr(C, pivoting=True); _PIVOTS[key] = np.sort(piv[:C.shape[0]])
    return _PIVOTS[key]


def newton_eckart_fast(net, area, X, X0, tau, C, max_iter=40, tol=1e-9, stall=3):
    """same iteration as newton_eckart (bordered Newton, backtracking on Pi), linear algebra by kkt (PARDISO) when
    available, otherwise by EckartSolver."""
    if _kkt.AVAILABLE:
        return _kkt.newton(net, area, X, X0, tau, C, max_iter, tol, stall)
    A_ = eckart_pivots(C); ok = False; floor = 0
    for it in range(max_iter):
        f = net.internal_forces(X).ravel() + tau * (area.H @ X.ravel())
        mu = np.linalg.lstsq(C.T, -f, rcond=None)[0]; r = f + C.T @ mu
        rel = np.linalg.norm(r) / max(1.0, tau * np.linalg.norm(area.H @ X.ravel()))
        if rel < tol:
            ok = True; break
        K = (net.tangent(X) - tau * area.H).tocsc()
        dx, _ = EckartSolver(K, C, A_).solve(f, -C @ (X - X0).ravel())
        dx = dx.reshape(-1, 3)
        p0 = _pi(net, area, X, tau); a = 1.0; hit = True
        while a > 1e-4:
            Xn = X + a * dx
            if np.all(np.isfinite(Xn)) and _pi(net, area, Xn, tau) <= p0 + 1e-12 * abs(p0):
                hit = False; break
            a *= 0.5
        X = Xn
        floor = floor + 1 if hit else 0
        if stall and floor >= stall:
            break
    g = tau * (area.H @ X.ravel())
    return X, it, rel, float(np.linalg.norm(C.T @ mu) / max(np.linalg.norm(g), 1e-30)), ok


def spectrum(net, area, X, tau, C, dense_max=700, k=3):
    """the k lowest eigenvalues of K_t - tau H on the constrained space {C dx = 0}.  Dense null-space basis for
    N <= dense_max, otherwise shift-invert Lanczos (kkt.spectrum with PARDISO, else the scipy path below) with the shift
    chosen from the inertia: sigma = -1e-4 when n_neg = 0, sigma below lambda_min (shift-count bracket) when n_neg > 0."""
    N = net.N; n = 3 * N
    K = (net.tangent(X) - tau * area.H)
    if N <= dense_max:
        import scipy.linalg as sla
        Z = sla.null_space(C)
        Kc = Z.T @ (K @ Z)
        w = np.linalg.eigvalsh(0.5 * (Kc + Kc.T))
        return dict(method='dense', lam=w[:k].tolist(), n_neg=int((w < -1e-10 * abs(w[-1])).sum()))
    if _kkt.AVAILABLE:                     # one PARDISO factorisation at sigma=-1e-8, warm-started shift-invert
        return _kkt.spectrum(net, area, X, tau, C, k=k)
    # scipy fallback (no PARDISO): the k eigenvalues nearest sigma = -1e-4 (= the k lowest when n_neg = 0); n_neg from a
    # dense Bunch-Kaufman count at -1e-8; when n_neg > 0, sigma below lambda_min is bracketed by dense shift counts.
    from inertia import bordered_inertia
    I_ = sp.identity(n, format='csr')
    count = lambda sg: bordered_inertia((K - sg * I_).tocsr(), C)['n_neg']
    nn = count(-_kkt.S_ZERO)
    sigma = -1e-4 if nn == 0 else _kkt.bracket_below(count)
    kk = k if nn == 0 else min(k + 2, n - C.shape[0] - 1)
    if C.shape[0] == 6:
        Sv = EckartSolver((K - sigma * sp.identity(n)).tocsc(), C, eckart_pivots(C))
        Q, _ = np.linalg.qr(C.T)
        def opinv(x):
            y = Sv.solve(x - Q @ (Q.T @ x), refine=1)[0]
            return y - Q @ (Q.T @ y)
        op = spla.LinearOperator((n, n), matvec=opinv)
        Kp = spla.LinearOperator((n, n), matvec=lambda x: (lambda z: z - Q @ (Q.T @ z))(K @ (x - Q @ (Q.T @ x))))
        v0 = Q[:, 0] * 0 + 1.0; v0 = v0 - Q @ (Q.T @ v0)               # deterministic start vector
        w = np.sort(spla.eigsh(Kp, k=kk, sigma=sigma, OPinv=op, which='LM', return_eigenvectors=False, v0=v0))[:k]
        method = 'eckart-shift-invert'
    else:
        Cs = sp.csr_matrix(C); m_ = C.shape[0]
        lu = spla.splu(sp.bmat([[(K - sigma * sp.identity(n)).tocsc(), Cs.T], [Cs, None]]).tocsc())
        op = spla.LinearOperator((n, n), matvec=lambda x: lu.solve(np.concatenate([x, np.zeros(m_)]))[:n])
        w = np.sort(spla.eigsh(K.tocsc(), k=kk, sigma=sigma, OPinv=op, which='LM', return_eigenvectors=False, v0=np.ones(n)))[:k]
        method = 'kkt-shift-invert'
    if nn > 0:
        _kkt.check_negatives(w, nn)
    return dict(method=method, lam=w.tolist(), n_neg=int(nn))


# ---------------- experimental mapping ----------------
def _align_pairs(seqA, resA, seqB, resB):
    from Bio import Align
    from Bio.Align import substitution_matrices
    al = Align.PairwiseAligner(mode='global', substitution_matrix=substitution_matrices.load('BLOSUM62'),
                               open_gap_score=-10, extend_gap_score=-0.5, end_gap_score=0)
    a = al.align(seqA, seqB)[0]
    out, ident = [], 0
    for (a0, a1), (b0, b1) in zip(*a.aligned):
        for i, j in zip(range(a0, a1), range(b0, b1)):
            out.append((resA[i], resB[j])); ident += seqA[i] == seqB[j]
    return out, ident


def chain_seq(d, c, cut_after=None):
    rs = sorted(r for (cc, r) in d if cc == c)
    s = ''.join(d[(c, r)][0] for r in rs)
    if cut_after and cut_after in s:
        k = s.index(cut_after) + len(cut_after); rs, s = rs[:k], s[:k]
    return s, rs


def _chain_orders(mch, tch, Xm, Xt):
    """candidate injective chain maps: all permutations for small oligomers, else cyclic/reflected orders by angle."""
    if len(mch) <= 4 or len(tch) <= 4:
        for p in itertools.permutations(tch, len(mch)):
            yield dict(zip(mch, p))
        return
    def ang_order(chs, X):
        cen = {c: X[c].mean(0) for c in chs}; cc = np.mean(list(cen.values()), 0)
        A = np.array([cen[c] - cc for c in chs]); _, _, Vt = np.linalg.svd(A); e1, e2 = Vt[0], Vt[1]
        return [c for _, c in sorted(((np.arctan2((cen[c] - cc) @ e2, (cen[c] - cc) @ e1), c) for c in chs))]
    mo, to = ang_order(mch, Xm), ang_order(tch, Xt)
    for s in range(len(to)):
        for d in (1, -1):
            yield {mo[i]: to[(s + d * i) % len(to)] for i in range(len(mo))}


def build_target(name, M):
    """returns idx (model nodes), P0, XE (target superposed onto P0), Delta, info."""
    T = PROTEINS[name]['target']
    d, order = M['ca'], M['order']
    mch = sorted({c for c, r in order})
    src = T['closed'] if T['kind'] == 'homolog' else T['open']
    Ds, _ = read_ca(src, T.get('open_chains'))
    tch = sorted({c for c, r in Ds})
    cut = T.get('cut_after')
    # residue maps. Building sequences from resolved residues only misaligns across unresolved gaps, so:
    # same species -> map by residue number (checked by residue identity); homolog -> one alignment between
    # the most complete chains, converted to a residue-number map and applied to every chain pair.
    maps, idents = {}, {}
    if T['kind'] == 'same':
        for a in mch:
            for b in tch:
                pr = {r: r for (c, r) in d if c == a and (b, r) in Ds}
                idt = np.mean([d[(a, r)][0] == Ds[(b, r)][0] for r in pr]) if pr else 0.0
                maps[(a, b)] = pr; idents[(a, b)] = float(idt)
    else:
        a0 = max(mch, key=lambda c: sum(1 for k in d if k[0] == c)); b0 = max(tch, key=lambda c: sum(1 for k in Ds if k[0] == c))
        sa, ra = chain_seq(d, a0); sb, rb = chain_seq(Ds, b0, cut)
        pr, idt = _align_pairs(sa, ra, sb, rb); rmap = dict(pr)
        for a in mch:
            for b in tch:
                maps[(a, b)] = {r: rmap[r] for (c, r) in d if c == a and r in rmap and (b, rmap[r]) in Ds}
                idents[(a, b)] = idt / max(len(pr), 1)
    Xm = {a: np.array([d[(a, r)][1] for r in sorted(r for (c, r) in d if c == a)]) for a in mch}
    Xt = {b: np.array([Ds[(b, r)][1] for r in sorted(r for (c, r) in Ds if c == b)]) for b in tch}
    best = None
    idx_of = {cr: i for i, cr in enumerate(order)}
    for cm in _chain_orders(mch, tch, Xm, Xt):
        keys = [(c, r) for (c, r) in order if r in maps[(c, cm[c])]]
        P = np.array([d[k][1] for k in keys]); Q = np.array([Ds[(cm[k[0]], maps[(k[0], cm[k[0]])][k[1]])][1] for k in keys])
        g = rmsd_fit(Q, P)
        if best is None or g < best[0]:
            best = (g, cm, keys, Q)
    g, cm, keys, Q = best
    # symmetric common set: residue numbers mapped in every model chain (all models are homo-oligomers)
    common = set.intersection(*[{r for (c, r) in keys if c == a} for a in mch])
    sel = [i for i, k in enumerate(keys) if k[1] in common]
    keys, Q = [keys[i] for i in sel], Q[sel]
    idx = np.array([idx_of[k] for k in keys]); P0 = M['X0'][idx]
    if T['kind'] == 'homolog':
        Do, _ = read_ca(T['open'])
        # same residue numbering scheme in closed/open homolog structures; map target chains closed->open by global fit
        och = sorted({c for c, r in Do})
        keepK = [(cm[k[0]], maps[(k[0], cm[k[0]])][k[1]]) for k in keys]
        bestJ = None
        tmp_closed = {c: np.array([Ds[k][1] for k in keepK if k[0] == c]) for c in tch}
        for cmJ in _chain_orders(tch, och, tmp_closed, {c: np.array([v[1] for kk, v in Do.items() if kk[0] == c]) for c in och}):
            ok = [i for i, k in enumerate(keepK) if (cmJ[k[0]], k[1]) in Do]
            if len(ok) < 0.8 * len(keepK):
                continue
            J = np.array([Do[(cmJ[keepK[i][0]], keepK[i][1])][1] for i in ok])
            gj = rmsd_fit(J, Q[ok])
            if bestJ is None or gj < bestJ[0]:
                bestJ = (gj, cmJ, ok, J)
        gj, cmJ, ok, J = bestJ
        okres = set.intersection(*[{keys[i][1] for i in ok if keys[i][0] == a} for a in mch])
        ok = [i for i in ok if keys[i][1] in okres]
        J = np.array([Do[(cmJ[keepK[i][0]], keepK[i][1])][1] for i in ok]); gj = rmsd_fit(J, Q[ok])
        idx, P0, Q = idx[ok], P0[ok], Q[ok]
        R1, _ = kabsch(Q, P0); R2, t2 = kabsch(J, Q)
        Delta = ((J @ R2.T + t2) - Q) @ R1.T
        XE = P0 + Delta
        info = dict(kind='homolog', closed_closed_rmsd=rmsd_fit(Q, P0), closed_open_homolog_rmsd=gj)
    else:
        R, t = kabsch(Q, P0); XE = Q @ R.T + t; Delta = XE - P0
        info = dict(kind='same')
    info.update(label=T['label'], chain_map=cm, n_common=int(len(idx)), frac_common=len(idx) / len(order),
                seq_identity=float(np.mean([idents[(a, cm[a])] for a in mch])),
                rmsd_closed_vs_target=float(np.sqrt((Delta ** 2).sum(1).mean())),
                chain_map_rule='global-RMSD minimum over injective chain maps')
    return idx, P0, XE, Delta, info


def _rmsd_ovl(Xi, XE, P0):
    R, t = kabsch(Xi, XE); d = Xi @ R.T + t - XE
    R0, t0 = kabsch(Xi, P0); u = Xi @ R0.T + t0 - P0
    R1, t1 = kabsch(XE, P0); D = XE @ R1.T + t1 - P0
    nu = np.linalg.norm(u)
    return float(np.sqrt((d ** 2).sum(1).mean())), (float(abs(u.ravel() @ D.ravel()) / (nu * np.linalg.norm(D))) if nu > 0 else 0.0)


def target_metrics(X, idx, XE, P0, Delta, unl, tm=None):
    """whole common set, unloaded subset, and (pre-specified) transmembrane subset = common nodes inside the
    membrane slab, each superposed on its own subset."""
    Xi = X[idx]
    r, o = _rmsd_ovl(Xi, XE, P0)
    out = dict(rmsd=r, ovl=o)
    R, t = kabsch(Xi, XE); d = Xi @ R.T + t - XE
    out['rmsd_unl'] = float(np.sqrt((d[unl] ** 2).sum(1).mean())) if unl.any() else None
    if tm is not None and tm.sum() >= 10:
        out['rmsd_tm'], out['ovl_tm'] = _rmsd_ovl(Xi[tm], XE[tm], P0[tm])
    return out


def strains(X, X0, pairs):
    pi, pj = pairs[:, 0], pairs[:, 1]
    l0 = np.linalg.norm(X0[pj] - X0[pi], axis=1)
    a = np.abs(np.linalg.norm(X[pj] - X[pi], axis=1) / l0 - 1)
    return dict(max_e=float(a.max()), p10=float((a > 0.1).mean()), p20=float((a > 0.2).mean()))
