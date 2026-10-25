"""Certified stability by Sylvester's law of inertia (editor M4).

For the bordered (KKT) matrix  B = [[K, C^T], [C, 0]]  with C (m x n) of full row rank,
    In(B) = In(Z^T K Z) + (m, m, 0),       Z = null-space basis of C.
Hence the constrained tangent Z^T K Z is positive definite iff B has exactly m negative and no zero eigenvalues.
The inertia of B is read from a symmetric-indefinite Bunch-Kaufman factorisation P B P^T = L D L^T (LAPACK
dsytrf): each 1x1 pivot contributes the sign of d, each 2x2 pivot contributes one positive and one negative
eigenvalue when det < 0, or two of the sign of its trace when det > 0.  Unlike a shift-invert Lanczos window,
this counts ALL negative eigenvalues.
"""
import numpy as np
import scipy.sparse as sp
from scipy.linalg import lapack


def _count(Af, ipiv, rtol):
    n = Af.shape[0]
    d1 = []; pos = neg = zero = 0; i = 0
    dmax = 0.0
    blocks = []
    while i < n:
        if ipiv[i] > 0:
            blocks.append((Af[i, i],)); i += 1
        else:
            blocks.append((Af[i, i], Af[i + 1, i], Af[i + 1, i + 1])); i += 2
    for b in blocks:
        dmax = max(dmax, max(abs(x) for x in b))
    tol = rtol * dmax
    for b in blocks:
        if len(b) == 1:
            d = b[0]
            if abs(d) <= tol: zero += 1
            elif d > 0: pos += 1
            else: neg += 1
        else:
            a, c, e = b
            ev = np.linalg.eigvalsh(np.array([[a, c], [c, e]]))
            for x in ev:
                if abs(x) <= tol: zero += 1
                elif x > 0: pos += 1
                else: neg += 1
    return pos, neg, zero


def bordered_inertia(K, C, rtol=1e-13):
    """K: sparse or dense symmetric (n x n); C: dense (m x n).  Returns dict with the inertia of the bordered matrix
    and the implied inertia of the constrained tangent (n_pos, n_neg, n_zero on the admissible space)."""
    n = K.shape[0]; m = C.shape[0]
    A = np.zeros((n + m, n + m), order='F')
    if sp.issparse(K):
        Kc = K.tocoo(); np.add.at(A, (Kc.row, Kc.col), Kc.data)
    else:
        A[:n, :n] = K
    A[n:, :n] = C; A[:n, n:] = C.T
    lu, ipiv, info = lapack.dsytrf(A, lower=1, overwrite_a=1)
    if info < 0:
        raise RuntimeError(f'dsytrf illegal argument {info}')
    pos, neg, zero = _count(lu, ipiv, rtol)
    del lu, A
    return dict(bordered=(pos, neg, zero), n_pos=pos - m, n_neg=neg - m, n_zero=zero, certified_pd=(neg == m and zero == 0))


def constrained_inertia(net, area, X, tau, C, rtol=1e-13):
    """certified inertia of K_t(X) - tau*H on the admissible space {C dx = 0}.  With MKL PARDISO available (kkt.py):
    shift count n_neg = n_neg(B(K + sI)), n_zero = n_neg(B(K - sI)) - n_neg(B(K + sI)), s = 1e-8, from the sparse
    LDL^T of the bordered matrix; dense Bunch-Kaufman count below if PARDISO perturbed a pivot or is unavailable."""
    import kkt
    if kkt.AVAILABLE:
        return kkt.constrained_inertia(net, area, X, tau, C, rtol)
    K = (net.tangent(X) - tau * area.H).tocsr()
    return bordered_inertia(K, C, rtol)
