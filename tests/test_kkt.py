"""Unit tests for src/kkt.py against dense linear algebra on small truss networks.

    python -m pytest -q tests/test_kkt.py        (or: python tests/test_kkt.py)

The PARDISO tests are skipped when pypardiso / MKL is not importable (non-x86 machines); test_bracket_below runs
everywhere.  Small networks: random C-alpha-like point clouds (fixed seeds), springs within a cutoff, constrained by
the six-row Eckart gauge (gauge_C).  Negative eigenvalues are produced by subtracting a multiple of the identity that
lies between two eigenvalues of the constrained tangent.
"""
import os, sys
import numpy as np
import scipy.linalg as sla
import scipy.sparse as sp

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import kkt                                           # noqa: E402
from inertia import bordered_inertia                # noqa: E402
from model import gauge_C                           # noqa: E402
from vfife.core import TrussNetwork                 # noqa: E402

try:
    import pytest
    needs_pardiso = pytest.mark.skipif(not kkt.AVAILABLE, reason='pypardiso / MKL not available')
except ImportError:                                  # plain-script mode
    pytest = None
    needs_pardiso = lambda f: f


def small_net(N=40, seed=0, rc=7.0):
    rng = np.random.default_rng(seed)
    X0 = rng.uniform(0, 14, size=(N, 3))
    d = np.linalg.norm(X0[:, None] - X0[None], axis=2)
    pairs = np.array([(i, j) for i in range(N) for j in range(i + 1, N) if d[i, j] < rc])
    net = TrussNetwork(X0, pairs, k=1.0)
    X = X0 + 0.3 * rng.standard_normal(X0.shape)        # off-reference state: geometric stiffness is non-zero
    K = sp.csr_matrix(net.tangent(X)); K = 0.5 * (K + K.T); C = gauge_C(X0)
    w = constrained_eigs(K, C)                            # shift so that the constrained lambda_1 = 1e-3 (n_neg = 0)
    K = sp.csr_matrix(K + (1e-3 - w[0]) * sp.identity(K.shape[0]))
    return net, X0, K, C


def constrained_eigs(K, C):
    Z = sla.null_space(C); Kc = Z.T @ (K.toarray() @ Z)
    return np.linalg.eigvalsh(0.5 * (Kc + Kc.T))


def make_kkt(K, C):
    pat = sp.csr_matrix(abs(K) + sp.identity(K.shape[0])); pat.data[:] = 1.0
    return kkt.BorderedKKT(pat, C)


def shifted(K, w, j):
    """K - t I with t between the j-th and (j+1)-th constrained eigenvalue (j = 0: below the lowest)."""
    t = 0.5 * (w[j - 1] + w[j]) if j > 0 else w[0] - 0.5 * (w[1] - w[0])
    return sp.csr_matrix(K - t * sp.identity(K.shape[0]))


def test_bracket_below():
    w = np.array([-3e-3, -2e-4, 5e-5, 1.0])
    sig = kkt.bracket_below(lambda s: int(np.sum(w < s)))
    assert sig < w.min() and sig > 4 * w.min() - 1e-12


@needs_pardiso
def test_inertia_matches_dense():
    for seed in (0, 1):
        net, X0, K, C = small_net(seed=seed); w = constrained_eigs(K, C); kk = make_kkt(K, C)
        for j in (0, 1, 3):
            Kj = shifted(K, w, j) if j else K
            wj = constrained_eigs(Kj, C)
            r = kk.inertia(Kj); d = bordered_inertia(Kj, C)
            assert r['n_neg'] == d['n_neg'] == int(np.sum(wj < -kkt.S_ZERO))
            assert r['n_zero'] == d['n_zero'] == 0
            r2, _ = kk.inertia_and_eigs(Kj, k=4)
            assert (r2['n_neg'], r2['n_zero']) == (r['n_neg'], r['n_zero'])


@needs_pardiso
def test_zero_modes_by_shift_count():
    net, X0, _, C = small_net(seed=2)
    K = sp.csr_matrix(net.tangent(X0)); K = 0.5 * (K + K.T)     # reference state: rigid rotations are exact zero modes
    C3 = C[:3]                                                    # translations only -> three rotational zero modes
    w = constrained_eigs(K, C3)
    r = make_kkt(K, C3).inertia(K)
    assert r['n_zero'] == int(np.sum(np.abs(w) < kkt.S_ZERO)) == 3
    assert r['n_neg'] == 0


@needs_pardiso
def test_solve_matches_dense():
    net, X0, K, C = small_net(seed=3); n, m = K.shape[0], C.shape[0]; kk = make_kkt(K, C)
    rng = np.random.default_rng(5); r = rng.standard_normal(n); s = rng.standard_normal(m)
    B = np.block([[K.toarray(), C.T], [C, np.zeros((m, m))]])
    x = np.linalg.solve(B, np.r_[r, s])
    kk.factor(K); dx, mu = kk.solve(r, s)
    assert np.max(np.abs(dx - x[:n])) <= 1e-9 * np.max(np.abs(x[:n]))
    assert np.max(np.abs(mu - x[n:])) <= 1e-8 * max(1.0, np.max(np.abs(x[n:])))


@needs_pardiso
def test_lowest_eigenvalues_including_negative():
    """the returned eigenvalues are the k lowest, with every negative one captured (n_neg = 0, 1, 2)."""
    net, X0, K, C = small_net(seed=4); w = constrained_eigs(K, C); kk = make_kkt(K, C)
    for j in (0, 1, 2):
        Kj = shifted(K, w, j) if j else K
        wj = constrained_eigs(Kj, C)
        inn, lam = kk.inertia_and_eigs(Kj, k=4)
        assert inn['n_neg'] == j
        assert np.allclose(lam, wj[:4], rtol=1e-8, atol=1e-12 * abs(wj).max())
        assert int(np.sum(np.asarray(lam) < -kkt.S_ZERO)) == j


if __name__ == '__main__':
    fails = 0
    for name, f in list(globals().items()):
        if name.startswith('test_') and callable(f):
            if not kkt.AVAILABLE and name != 'test_bracket_below':
                print('skip', name); continue
            try:
                f(); print('ok  ', name)
            except Exception as ex:                  # noqa: BLE001
                fails += 1; print('FAIL', name, repr(ex))
    sys.exit(1 if fails else 0)
