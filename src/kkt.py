"""Bordered-KKT linear algebra with ONE sparse symmetric-indefinite factorisation (MKL PARDISO, mtype=-2).

For the Eckart-bordered tangent  B(K) = [[K, C^T], [C, 0]]  (C: m x n, full row rank)

    In(B) = In(Z^T K Z) + (m, m, 0),       Z = null-space basis of C          (Haynsworth / Sylvester)

so a single LDL^T factorisation of B gives, at the same time,
  * Newton / linear-response solves (with iterative refinement against the bordered operator),
  * the certified inertia of the constrained tangent (counts iparm(22)/iparm(23) of PARDISO),
  * the lowest constrained eigenvalues by shift-invert (OPinv = the held factorisation), warm-started from the
    previous Ritz vectors of the same model.
The sparsity pattern of B is fixed per model (3x3 element blocks of the truss tangent, the area operator H, the full
diagonal and the dense C^T columns), so the symbolic analysis (METIS ordering) is done once per model and every
further factorisation is numeric only.

Zero modes / mechanisms are counted by a shift count, never from pivots at s = 0:
    n_zero = n_neg(K - s I) - n_neg(K + s I),  n_neg = n_neg(K + s I),  s = S_ZERO = 1e-8  (model units, k = 1)
i.e. eigenvalues in (-s, s) are zero modes.  If PARDISO reports perturbed pivots in either shifted factorisation the
count falls back to the dense Bunch-Kaufman count (inertia.bordered_inertia).

If pypardiso / MKL is not importable (or PND_NO_PARDISO=1) AVAILABLE is False and every caller keeps the original
scipy code path (model.py, inertia.py).
"""
import os, ctypes
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

S_ZERO = 1e-8          # zero-mode window for the shift count
SIGMA_LAM = -1e-4      # eigenvalue selection: the k eigenvalues nearest this shift (same as model.spectrum)
EIG_METHOD = os.environ.get('PND_EIG', 'arpack')     # 'arpack' (default) or 'invit'

AVAILABLE = False
_MKL_PARDISO = None
if not os.environ.get('PND_NO_PARDISO'):
    try:
        import pypardiso as _pyp
        _MKL_PARDISO = _pyp.PyPardisoSolver()._mkl_pardiso
        AVAILABLE = True
    except Exception:                                   # pragma: no cover - environment dependent
        AVAILABLE = False

STATS = dict(analyse=0, factor=0, solve=0, dense_fallback=0, second_shift=0, eig_arpack=0, eig_invit=0,
             invit_fallback=0, newton_stall_exit=0, pattern_rebuild=0)


# --------------------------------------------------------------------------------------------- fixed pattern
class Pattern:
    """Upper-triangle CSR pattern (0-based, int32) of B for one model: pattern(Kpat) + diag + C^T columns + m x m diag."""
    def __init__(self, Kpat, C):
        C = np.atleast_2d(np.asarray(C, float))
        n = Kpat.shape[0]; m = C.shape[0] if C.size else 0; N = n + m
        self.n, self.m, self.N = n, m, N
        self.C = C if m else np.zeros((0, n))
        S = sp.csr_matrix(Kpat, copy=True); S.data = np.ones_like(S.data)
        P = sp.triu(S + sp.identity(n, format='csr'), format='coo')
        r = [P.row, np.arange(n, N)]; c = [P.col, np.arange(n, N)]
        if m:
            r.append(np.repeat(np.arange(n), m)); c.append(np.tile(np.arange(n, N), n))
        r = np.concatenate(r); c = np.concatenate(c)
        A = sp.csr_matrix((np.ones(len(r)), (r, c)), shape=(N, N)); A.sum_duplicates(); A.sort_indices()
        self.indptr = A.indptr.astype(np.int32); self.indices = A.indices.astype(np.int32)
        rows = np.repeat(np.arange(N, dtype=np.int64), np.diff(A.indptr))
        self.keys = rows * N + A.indices.astype(np.int64); self.nnz = len(self.keys)
        self.dpos = np.searchsorted(self.keys, np.arange(n, dtype=np.int64) * (N + 1))
        if m:
            ck = np.repeat(np.arange(n, dtype=np.int64), m) * N + np.tile(np.arange(n, N, dtype=np.int64), n)
            self.cpos = np.searchsorted(self.keys, ck); self.cval = self.C.T.ravel().copy()
        self._cache = None                              # (indptr, indices, positions) of the last K structure

    def values(self, K, shift=0.0):
        """data array of B(K - shift I) in the fixed pattern.  Raises KeyError if K has entries outside it."""
        U = sp.triu(sp.csr_matrix(K), format='csr'); U.sum_duplicates()
        ch = self._cache
        if ch is not None and np.array_equal(ch[0], U.indptr) and np.array_equal(ch[1], U.indices):
            pos = ch[2]
        else:
            rows = np.repeat(np.arange(U.shape[0], dtype=np.int64), np.diff(U.indptr))
            k = rows * self.N + U.indices.astype(np.int64)
            pos = np.searchsorted(self.keys, k)
            if len(k) and (pos.max() >= self.nnz or np.any(self.keys[np.minimum(pos, self.nnz - 1)] != k)):
                raise KeyError('entry outside fixed pattern')
            self._cache = (U.indptr.copy(), U.indices.copy(), pos)
        a = np.zeros(self.nnz); a[pos] = U.data
        if shift:
            a[self.dpos] -= shift
        if self.m:
            a[self.cpos] = self.cval
        return a


# --------------------------------------------------------------------------------------------- PARDISO handle
class _Pardiso:
    """MKL PARDISO, real symmetric indefinite (mtype=-2), one handle = one held factorisation."""
    def __init__(self, pat):
        self.pat = pat; self.pt = np.zeros(64, np.int64); ip = np.zeros(64, np.int32); self.ip = ip
        ip[0] = 1          # user-supplied iparm
        ip[1] = 2          # METIS nested dissection
        ip[9] = 8          # pivot perturbation 1e-8
        ip[10] = 1         # symmetric scaling
        ip[12] = 1         # symmetric weighted matching
        ip[17] = -1        # report nnz(L)
        ip[20] = 1         # Bunch-Kaufman 1x1 and 2x2 pivoting
        ip[34] = 1         # zero-based indexing
        self.a = None; self.analysed = False

    def _call(self, phase, b=None):
        N = self.pat.N
        if b is None:
            bb = np.zeros(1); x = np.zeros(1); nrhs = 1
        else:
            bb = np.asfortranarray(b, dtype=float); x = np.zeros_like(bb); nrhs = 1 if bb.ndim == 1 else bb.shape[1]
        err = ctypes.c_int32(0); i32 = ctypes.POINTER(ctypes.c_int32); f64 = ctypes.POINTER(ctypes.c_double)
        a = self.a if self.a is not None else np.zeros(1)
        _MKL_PARDISO(self.pt.ctypes.data_as(ctypes.POINTER(ctypes.c_int64)), ctypes.byref(ctypes.c_int32(1)),
                     ctypes.byref(ctypes.c_int32(1)), ctypes.byref(ctypes.c_int32(-2)), ctypes.byref(ctypes.c_int32(phase)),
                     ctypes.byref(ctypes.c_int32(N)), a.ctypes.data_as(f64), self.pat.indptr.ctypes.data_as(i32),
                     self.pat.indices.ctypes.data_as(i32), None, ctypes.byref(ctypes.c_int32(nrhs)),
                     self.ip.ctypes.data_as(i32), ctypes.byref(ctypes.c_int32(0)), bb.ctypes.data_as(f64),
                     x.ctypes.data_as(f64), ctypes.byref(err))
        if err.value != 0:
            raise RuntimeError(f'pardiso phase {phase} error {err.value}')
        return x

    def factor(self, a):
        self.a = np.ascontiguousarray(a, float)
        if not self.analysed:
            self._call(11); self.analysed = True; STATS['analyse'] += 1
        self._call(22); STATS['factor'] += 1

    def solve(self, b):
        STATS['solve'] += 1
        return self._call(33, b)

    def counts(self):
        """(n_pos, n_neg, n_perturbed) of the factorised bordered matrix."""
        return int(self.ip[21]), int(self.ip[22]), int(self.ip[13])

    def free(self):
        if self.analysed:
            try:
                self._call(-1)
            except Exception:
                pass
            self.analysed = False

    def __del__(self):
        self.free()


# --------------------------------------------------------------------------------------------- bordered KKT
class BorderedKKT:
    """B(K) = [[K, C^T],[C, 0]] for one model, fixed pattern, one held factorisation."""
    def __init__(self, Kpat, C, seed=0):
        C = np.atleast_2d(np.asarray(C, float))
        self.Kpat = sp.csr_matrix(Kpat); self.C = C; self.m = C.shape[0]; self.n = Kpat.shape[0]
        self.pat = Pattern(self.Kpat, C); self.pd = _Pardiso(self.pat)
        self.Q = np.linalg.qr(C.T)[0] if self.m else np.zeros((self.n, 0))
        self.K = None; self.shift = 0.0; self.V = None; self.seed = seed

    # -- factorisation
    def factor(self, K, shift=0.0):
        """factorise B(K - shift I).  K: sparse symmetric n x n."""
        K = sp.csr_matrix(K)
        try:
            a = self.pat.values(K, shift)
        except KeyError:                                      # pattern grew: rebuild once and re-analyse
            STATS['pattern_rebuild'] += 1
            S = abs(self.Kpat) + abs(K); self.Kpat = sp.csr_matrix(S)
            self.pd.free(); self.pat = Pattern(self.Kpat, self.C); self.pd = _Pardiso(self.pat)
            a = self.pat.values(K, shift)
        self.pd.factor(a); self.K = K; self.shift = float(shift)
        return self

    def counts(self):
        return self.pd.counts()

    def _op(self, x):
        """the factorised bordered operator applied to x = [dx; mu] (columns allowed)."""
        n = self.n; d = x[:n]; mu = x[n:]
        top = self.K @ d - self.shift * d + (self.C.T @ mu if self.m else 0.0)
        if not self.m:
            return top
        return np.concatenate([top, self.C @ d], axis=0)

    def solve(self, r, s=None, refine=2):
        """[[K - shift I, C^T],[C, 0]] [dx; mu] = [r; s], iterative refinement against the bordered operator.
        r may be n or n x p (block)."""
        r = np.asarray(r, float)
        if self.m:
            if s is None:
                s = np.zeros((self.m,) + r.shape[1:])
            b = np.concatenate([r, s], axis=0)
        else:
            b = r
        x = self.pd.solve(b)
        for _ in range(refine):
            x = x + self.pd.solve(b - self._op(x))
        return x[:self.n], x[self.n:]

    # -- inertia
    def _dense(self, K, rtol):
        from inertia import bordered_inertia
        STATS['dense_fallback'] += 1
        return bordered_inertia(sp.csr_matrix(K), self.C, rtol)

    @staticmethod
    def _rec(n, m, n_neg, n_zero):
        n_pos = n - m - n_neg - n_zero
        return dict(bordered=(n_pos + m, n_neg + m, n_zero), n_pos=n_pos, n_neg=n_neg, n_zero=n_zero,
                    certified_pd=(n_neg == 0 and n_zero == 0))

    def inertia(self, K, rtol=1e-13, s=S_ZERO):
        """certified inertia of K on {C dx = 0} by the shift count (two numeric factorisations).  Leaves the
        factorisation of B(K + s I) held (usable as shift-invert operator at sigma = -s).  Dense fallback if PARDISO
        perturbed any pivot."""
        n, m = self.n, self.m
        self.factor(K, shift=s); _, neg_m, pert_m = self.counts()           # eigenvalues < +s
        self.factor(K, shift=-s); _, neg_p, pert_p = self.counts()          # eigenvalues < -s
        if pert_m or pert_p:
            return self._dense(K, rtol)
        return self._rec(n, m, neg_p - m, neg_m - neg_p)

    def inertia_and_eigs(self, K, k=4, rtol=1e-13, s=S_ZERO, with_inertia=True):
        """Scheme B: ONE factorisation of B(K + s I) gives n_neg (eigenvalues < -s) and the k eigenvalues nearest
        SIGMA_LAM.  The zero count is read from the converged eigenvalues when they certify it (every eigenvalue
        within 2s of the shift has been found and none lies in (-s, s)); otherwise the second shifted factorisation
        is done (full shift count).  Returns (inertia or None, lam or None)."""
        n, m = self.n, self.m
        self.factor(K, shift=-s); _, neg_p, pert_p = self.counts()
        try:
            lam, allw = self.eigs(k, return_all=True)
        except Exception:
            lam, allw = None, None
        if not with_inertia:
            return None, lam
        if pert_p:
            return self._dense(K, rtol), lam
        if allw is not None and np.max(np.abs(np.asarray(allw) + s)) >= 2 * s and not np.any(np.abs(allw) < s):
            return self._rec(n, m, neg_p - m, 0), lam
        STATS['second_shift'] += 1
        self.factor(K, shift=s); _, neg_m, pert_m = self.counts()
        if pert_m:
            r = self._dense(K, rtol)
        else:
            r = self._rec(n, m, neg_p - m, neg_m - neg_p)
        self.factor(K, shift=-s)                                       # restore the held factorisation
        return r, lam

    # -- eigenvalues (shift-invert on the held factorisation, sigma_f = held shift)
    def _proj(self, X):
        return X - self.Q @ (self.Q.T @ X) if self.m else X

    def _v0(self):
        if self.V is not None:
            v = self._proj(self.V.sum(axis=1))
        else:
            v = self._proj(np.random.default_rng(self.seed).standard_normal(self.n))
        return v / np.linalg.norm(v)

    def eigs(self, k=4, return_all=False, sigma_sel=SIGMA_LAM):
        """k eigenvalues of K on {C dx = 0} nearest sigma_sel (ascending), computed as the k+2 eigenvalues nearest the
        held shift and selected; warm-started from the previous Ritz vectors (deterministic)."""
        nev = min(k + 2, self.n - self.m - 1)
        if EIG_METHOD == 'invit' and self.V is not None:
            w, V = self._invit(nev)
        else:
            w, V = self._arpack(nev)
        self.V = V
        o = np.argsort(np.abs(w - sigma_sel), kind='stable')[:k]
        lam = np.sort(w[o]).tolist()
        return (lam, w) if return_all else lam

    def _arpack(self, nev):
        n = self.n; sig = self.shift                      # B(K - shift I) held: shift-invert at sigma = shift
        op = spla.LinearOperator((n, n), matvec=lambda x: self._proj(self.solve(self._proj(x), refine=1)[0]), dtype=float)
        A = spla.LinearOperator((n, n), matvec=lambda x: self._proj(self.K @ self._proj(x)), dtype=float)
        w, V = spla.eigsh(A, k=nev, sigma=sig, OPinv=op, which='LM', v0=self._v0())
        STATS['eig_arpack'] += 1
        return w, V

    def _invit(self, nev, extra=4, tol=1e-10, maxit=40):
        """warm-started block inverse iteration + Rayleigh-Ritz on the held factorisation; converged when every
        wanted Ritz pair has residual <= tol * ||K||_1-estimate; falls back to ARPACK otherwise."""
        p = nev + extra; V = self.V
        if V.shape[1] < p:
            V = np.hstack([V, np.random.default_rng(self.seed + 1).standard_normal((self.n, p - V.shape[1]))])
        W = self._proj(V[:, :p]); kn = abs(self.K).sum(axis=0).max()
        for _ in range(maxit):
            W = self._proj(self.solve(W, refine=1)[0]); W, _ = np.linalg.qr(W)
            KW = self._proj(self.K @ W); Hs = W.T @ KW; th, U = np.linalg.eigh(0.5 * (Hs + Hs.T))
            Vn = W @ U; R = KW @ U - Vn * th
            o = np.argsort(np.abs(th - self.shift))[:nev]
            if np.max(np.linalg.norm(R[:, o], axis=0)) <= tol * kn:
                STATS['eig_invit'] += 1
                return th[o], Vn[:, o]
            W = Vn
        STATS['invit_fallback'] += 1
        return self._arpack(nev)


# --------------------------------------------------------------------------------------------- per-model cache
_CACHE = {}


def tangent_pattern(net, area=None):
    """structural pattern of K_t(X) - tau H: full 3x3 blocks of every element and node, plus H."""
    p, q = net.pairs[:, 0], net.pairs[:, 1]; N = net.N
    pr = np.concatenate([p, q, p, q, np.arange(N)]); qc = np.concatenate([p, q, q, p, np.arange(N)])
    r = (3 * pr[:, None, None] + np.arange(3)[None, :, None] + 0 * np.arange(3)[None, None, :]).ravel()
    c = (3 * qc[:, None, None] + 0 * np.arange(3)[None, :, None] + np.arange(3)[None, None, :]).ravel()
    S = sp.csr_matrix((np.ones(len(r)), (r, c)), shape=(3 * N, 3 * N))
    if area is not None:
        H = abs(sp.csr_matrix(area.H)); S = S + H
    S.sum_duplicates(); S.data[:] = 1.0
    return S


def get(net, area, C, dofs=None):
    """the BorderedKKT of (net, area, C) for this process (symbolic analysis shared by every caller).
    dofs: restrict K to these dofs (anchored formulation, no border)."""
    C = np.atleast_2d(np.asarray(C, float)) if C is not None else np.zeros((0, 3 * net.N))
    key = (os.getpid(), id(net), id(area), C.shape, hash(C.tobytes()), None if dofs is None else hash(np.asarray(dofs).tobytes()))
    kk = _CACHE.get(key)
    if kk is None:
        S = tangent_pattern(net, area)
        if dofs is not None:
            S = S[dofs][:, dofs]
        kk = BorderedKKT(S, C); kk._refs = (net, area)                 # keep ids alive
        _CACHE[key] = kk
    return kk


# --------------------------------------------------------------------------------------------- algorithms
def _pi(net, area, X, tau):
    return net.energy(X) - tau * area.area(X)


def newton(net, area, X, X0, tau, C, max_iter=40, tol=1e-9, stall=3):
    """bordered Newton with backtracking on Pi = U - tau A (identical iteration to model.newton_eckart[_fast]),
    linear algebra by the fixed-pattern PARDISO factorisation.  Early exit (ok=False) after `stall` consecutive
    line searches that hit the step floor (alpha <= 1e-4)."""
    kk = get(net, area, C); ok = False; floor = 0; C = kk.C
    for it in range(max_iter):
        f = net.internal_forces(X).ravel() + tau * (area.H @ X.ravel())
        mu = np.linalg.lstsq(C.T, -f, rcond=None)[0]; r = f + C.T @ mu
        rel = np.linalg.norm(r) / max(1.0, tau * np.linalg.norm(area.H @ X.ravel()))
        if rel < tol:
            ok = True; break
        kk.factor(net.tangent(X) - tau * area.H)
        dx, _ = kk.solve(f, -C @ (X - X0).ravel())
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
            STATS['newton_stall_exit'] += 1; break
    g = tau * (area.H @ X.ravel())
    return X, it, rel, float(np.linalg.norm(C.T @ mu) / max(np.linalg.norm(g), 1e-30)), ok


def newton_anchored(net, area, X, tau, fd, max_iter=40, tol=1e-9, stall=3):
    """model.newton_anchored with the PARDISO factorisation of K restricted to the free dofs."""
    kk = get(net, area, None, dofs=fd); floor = 0
    for it in range(max_iter):
        f = net.internal_forces(X).ravel() + tau * (area.H @ X.ravel())
        rel = np.linalg.norm(f[fd]) / max(1.0, tau * np.linalg.norm((area.H @ X.ravel())[fd]))
        if rel < tol:
            return X, it, rel, True
        K = (net.tangent(X) - tau * area.H).tocsr()[fd][:, fd]
        kk.factor(K); dx = np.zeros(3 * net.N); dx[fd] = kk.solve(f[fd])[0]
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
            STATS['newton_stall_exit'] += 1
            return X, it, rel, False
    return X, it, rel, False


def spectrum(net, area, X, tau, C, k=3):
    """k constrained eigenvalues nearest SIGMA_LAM (model.spectrum semantics for N > dense_max)."""
    kk = get(net, area, C)
    kk.factor(net.tangent(X) - tau * area.H, shift=-S_ZERO)
    w = np.asarray(kk.eigs(k))
    return dict(method='eckart-shift-invert' if kk.m == 6 else 'kkt-shift-invert', lam=w.tolist(), n_neg=int((w < 0).sum()))


def constrained_inertia(net, area, X, tau, C, rtol=1e-13):
    return get(net, area, C).inertia(net.tangent(X) - tau * area.H, rtol)


def linear_response(net, area, C, X0, rhs):
    """solve [[K_t(X0), C^T],[C, 0]] [u; mu] = [rhs; 0] (the uL1 / u1 solve), K factorised at shift 0."""
    kk = get(net, area, C); kk.factor(net.tangent(X0)); return kk.solve(np.asarray(rhs, float).ravel())[0]


def stats_line():
    return 'kkt ' + ' '.join(f'{k}={v}' for k, v in STATS.items() if v)
