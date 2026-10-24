"""Null models for the validation (editor M5a).  All metrics on the pre-specified transmembrane (TM) subset.

(i)   dilation : best-amplitude isotropic in-plane dilation of the closed structure about the membrane axis
                 (one parameter, like the best-amplitude linear null);
(ii)  anm_k    : best least-squares combination of the k lowest Eckart-constrained ANM modes (k = 1, 3, 10, 30),
                 an upper bound for any linear model built on these modes (it uses the target to choose k amplitudes);
(iii) rewired  : degree-preserving, length-limited double-edge-swap rewiring of the non-backbone elements
                 (stress-free rest lengths); the nonlinear tension path of the rewired network is computed with the
                 same load, gauge and validity criterion, best TM frame within its own validity range (3 seeds).
usage: python nulls.py [names...]        output: results/nulls.json
"""
import sys, os, json, time
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *
from model import _rmsd_ovl

names = [a for a in sys.argv[1:] if not a.startswith("--")] or PANEL
outf = f'{RES}/nulls.json'
out = json.load(open(outf)) if os.path.exists(outf) else {}
SEEDS = (11, 12, 13)


def rewire(pairs, X0, bb, seed, rmax, target=3.0):
    """double-edge swaps (a,b),(c,d) -> (a,d),(c,b) between spatially neighbouring non-backbone elements; node
    degrees are preserved exactly, new elements are limited to length rmax; stops after target*E_free swaps."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    P = [tuple(sorted(p)) for p in pairs]; S = set(P)
    free = np.array([i for i in range(len(P)) if not bb[i]])
    acc = 0; tries = 0
    while acc < target * len(free) and tries < 40 * len(free):
        mid = np.array([0.5 * (X0[P[i][0]] + X0[P[i][1]]) for i in free]); tree = cKDTree(mid)
        for _ in range(len(free)):
            tries += 1
            ii = rng.integers(len(free)); nb = tree.query_ball_point(mid[ii], 8.0, return_sorted=True)  # fixed order: seed -> same network
            if len(nb) < 2: continue
            jj = nb[rng.integers(len(nb))]
            if jj == ii: continue
            i, j = free[ii], free[jj]
            (a, b), (c, d) = P[i], P[j]
            if rng.random() < 0.5: c, d = d, c
            e1, e2 = tuple(sorted((a, d))), tuple(sorted((c, b)))
            if len({a, b, c, d}) < 4 or e1 in S or e2 in S: continue
            if np.linalg.norm(X0[e1[0]] - X0[e1[1]]) > rmax or np.linalg.norm(X0[e2[0]] - X0[e2[1]]) > rmax: continue
            S.discard(P[i]); S.discard(P[j]); S.add(e1); S.add(e2); P[i], P[j] = e1, e2; acc += 1
            if acc >= target * len(free): break
    changed = len(set(tuple(sorted(p)) for p in pairs) - S)
    return np.array(P), dict(swaps=acc, frac_changed=changed / len(free))


def tm_metric(X, idx, XE, P0, tm):
    return _rmsd_ovl(X[idx][tm], XE[tm], P0[tm])


def best_path(net, area, X0, C, mem, er, R0, idx, XE, P0, tm, eps_cap=0.4):
    eps_of = lambda X: float(((X[mem] - X0[mem]) * er).sum(1).mean() / R0)
    Cs = sp.csr_matrix(C); n = 3 * net.N
    g0 = area.grad(X0)
    u1 = EckartSolver(net.tangent(X0).tocsc(), C, eckart_pivots(C)).solve(g0.ravel())[0].reshape(-1, 3)
    ept = eps_of(X0 + u1)
    lin = min(tm_metric(X0 + s * u1, idx, XE, P0, tm)[0] for s in np.linspace(0, 0.6 / ept, 121))
    X = X0.copy(); tau = 0.0; dt = 0.01 / ept; best = (tm_metric(X0, idx, XE, P0, tm)[0], 0.0); steps = 0; eps_star = 0.0
    while steps < 80:
        Xn, it, rel, gr, ok = (newton_eckart_fast if net.N > 2000 else newton_eckart)(net, area, X, X0, tau + min(dt, 0.02 / ept), C)
        if not ok:
            dt *= 0.5
            if dt < 1e-3 * 0.01 / ept: break
            continue
        tau += min(dt, 0.02 / ept); X = Xn; steps += 1
        l = net.element_lengths(X); e = np.abs(l / net.l0 - 1)
        if (e > 0.2).mean() > 0.05 or e.max() > 0.5: break
        eps_star = eps_of(X)
        r = tm_metric(X, idx, XE, P0, tm)[0]
        if r < best[0]: best = (r, eps_star)
        if it <= 5: dt *= 1.25
        if eps_star > eps_cap: break
    return dict(best_tm=best[0], eps_best=best[1], eps_star=eps_star, linear_best_tm=lin, steps=steps, eps_per_tau=ept)


for name in names:
    T0 = time.time()
    M = model(name, 10.0); X0 = M['X0']; mem = M['mem']; order = M['order']
    net = TrussNetwork(X0, M['pairs'], k=1.0); area, _ = make_area(M); C = gauge_C(X0); Cs = sp.csr_matrix(C); n = 3 * net.N
    idx, P0, XE, Delta, info = build_target(name, M); tm = np.isin(idx, mem)
    er = np.zeros((len(mem), 3)); er[:, :2] = M['m']['e_r']; R0 = M['m']['radii'].mean()
    rec = dict(closed_tm=tm_metric(X0, idx, XE, P0, tm)[0])
    # (i) dilation
    c = M['m']['centroid']; best = (1e9, 0, 0)
    for s in np.linspace(-0.1, 0.4, 501):
        X = X0.copy(); X[:, :2] = c + (1 + s) * (X0[:, :2] - c)
        r, o = tm_metric(X, idx, XE, P0, tm)
        if r < best[0]: best = (r, s, o)
    rec['dilation'] = dict(best_tm=best[0], scale=best[1], ovl=best[2])
    # (ii) ANM subspace
    K0 = net.tangent(X0).tocsc()
    kmax = 36
    w, V = spla.eigsh(K0, k=kmax + 6, sigma=-1e-6, which='LM')
    o = np.argsort(w); w, V = w[o][6:], V[:, o][:, 6:]           # drop the six rigid modes
    sel = idx[tm]
    R1, t1 = kabsch(XE[tm], P0[tm]); D = (XE[tm] @ R1.T + t1 - P0[tm]).ravel()
    for k in (1, 3, 10, 30):
        B = V[:, :k].reshape(net.N, 3, k)[sel].reshape(-1, k)
        cf = np.linalg.lstsq(B, D, rcond=None)[0]
        X = X0.copy(); X += (V[:, :k] @ cf).reshape(-1, 3)
        rec[f'anm_{k}'] = dict(best_tm=tm_metric(X, idx, XE, P0, tm)[0], ovl=tm_metric(X, idx, XE, P0, tm)[1])
    # reference: same procedure on the real network, then rewired networks
    bb = np.array([order[i][0] == order[j][0] and abs(order[i][1] - order[j][1]) == 1 for i, j in M['pairs']])
    if name != '6b3r' or '--with-piezo-rewire' in sys.argv:
        rec['real_path'] = best_path(net, area, X0, C, mem, er, R0, idx, XE, P0, tm)
        rw = []
        for sd in SEEDS:
            pr, acc = rewire(M['pairs'], X0, bb, sd, rmax=1.5 * 10.0)
            netr = TrussNetwork(X0, pr, k=1.0)
            lam = spectrum(netr, area, X0, 0.0, C, k=2)['lam'][0]
            if lam < 1e-8:
                rw.append(dict(seed=sd, lambda1=lam, note='mechanism, skipped', **acc)); continue
            r = best_path(netr, area, X0, C, mem, er, R0, idx, XE, P0, tm); r.update(seed=sd, lambda1=lam, **acc); rw.append(r)
        rec['rewired'] = rw
    rec['time_s'] = time.time() - T0
    out[name] = rec; json.dump(out, open(outf, 'w'), indent=1, default=float)
    print(name, json.dumps({k: v for k, v in rec.items()}, default=lambda x: round(float(x), 3))[:900], flush=True)
