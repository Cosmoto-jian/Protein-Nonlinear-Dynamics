"""Load verification (editor M1, M8a).

For every structure:
  (i)   area operator vs. direct shoelace evaluation from vertex coordinates along the r4 path frames;
  (ii)  finite-difference check of grad A' at a deformed frame;
  (iii) residual in-plane moment M_xy of the original and of the self-equilibrated load, at x0 and along the path;
  (iv)  anchored (6 isostatic supports) vs Eckart solutions at the r4 validity-boundary tension, for both loads.
usage: python load_check.py [names...]      output: results/load_check.json
"""
import sys, os, json, time
import numpy as np
import scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *
from inertia import constrained_inertia

names = sys.argv[1:] or PANEL + EXTRA
outf = os.path.join(RES, 'load_check.json')
out = json.load(open(outf)) if os.path.exists(outf) else {}


def follow(net, area, X0, taus, gauge, fd=None, C=None):
    X = X0.copy()
    for t in taus:
        if gauge == 'eckart':
            X, it, rel, gr, ok = (newton_eckart_fast if net.N > 2000 else newton_eckart)(net, area, X, X0, t, C)
        else:
            X, it, rel, ok = newton_anchored(net, area, X, t, fd)
        if not ok:
            return X, False
    return X, True


for name in names:
    T0 = time.time()
    M = model(name, 10.0); X0 = M['X0']; net = TrussNetwork(X0, M['pairs'], k=1.0)
    raw, ns = make_area(M, equilibrate=False); eq, _ = make_area(M, equilibrate=True)
    C = gauge_C(X0)
    anchor = rigid_anchor_dofs(X0, exclude_nodes=raw.vertices); fd = np.setdiff1d(np.arange(3 * net.N), anchor)
    R4 = json.load(open(raw(f'r4_{name}_rc10.json')))
    Xs = np.load(raw(f'r4_{name}_rc10_Xs.npy')) if raw(f'r4_{name}_rc10_Xs.npy', required=False) else None
    rec = dict(N=int(net.N), n_loaded=int(len(raw.vertices)), n_sector=ns)
    # (i) operator vs direct shoelace, and A'(x) = A(Sx)
    frames = [X0] + ([Xs[i] for i in range(0, len(Xs), max(1, len(Xs) // 6))] if Xs is not None else [])
    e_raw, e_eq = [], []
    for X in frames:
        e_raw.append(abs(raw.area(X) - polygon_area_direct(raw, X)) / abs(polygon_area_direct(raw, X)))
        x = X.ravel(); Sx = x - eq.Q @ (eq.S_B @ (eq.QL.T @ x))
        e_eq.append(abs(eq.area(X) - polygon_area_direct(raw, Sx.reshape(-1, 3))) / abs(eq.area(X)))
    rec['area_operator_vs_direct'] = dict(raw_max=float(max(e_raw)), equilibrated_max=float(max(e_eq)), n_frames=len(frames))
    # (ii) FD gradient at the last frame
    X = frames[-1]; rng = np.random.default_rng(1); errs = []
    for _ in range(5):
        d = rng.normal(size=X.shape); d /= np.linalg.norm(d); h = 1e-4
        fd_ = (eq.area(X + h * d) - eq.area(X - h * d)) / (2 * h)
        errs.append(abs(fd_ - float((eq.grad(X) * d).sum())) / max(abs(fd_), 1e-30))
    rec['grad_fd_rel_max'] = float(max(errs))
    # (iii) resultants
    rec['resultants_x0'] = dict(raw=load_resultants(raw, X0, X0), eq=load_resultants(eq, X0, X0))
    if Xs is not None:
        rec['Mxy_path_max'] = dict(raw=float(max(load_resultants(raw, X, X0)['Mxy'] for X in Xs)),
                                   eq=float(max(load_resultants(eq, X, X0)['Mxy'] for X in Xs)))
    rec['load_change_rel'] = float(np.linalg.norm(eq.grad(X0) - raw.grad(X0)) / np.linalg.norm(raw.grad(X0)))
    # (iv) gauges at the r4 validity-boundary tension: Eckart-6 and six isostatic anchors for the original load (raw)
    # and for the reference-equilibrated load (eq); symmetry gauge (4 exact symmetries, tilt free) for the raw load.
    b = R4['boundary_step'] - 1; taus = [r['tau'] for r in R4['rows'][:b + 1]]
    sp0 = spectrum(net, raw, X0, 0.0, C, k=3)
    rec['lambda1_x0'] = float(sp0['lam'][0])
    has_t = PROTEINS[name]['target'] is not None
    if has_t:
        idx, P0, XE, Delta, info = build_target(name, M); tm = np.isin(idx, M['mem']); unl = ~np.isin(idx, raw.vertices)
    C4 = gauge_C4(X0); sols = {}
    for lab, ar in (('raw', raw), ('eq', eq)):
        Xe, oke = follow(net, ar, X0, taus, 'eckart', C=C)
        Xa, oka = follow(net, ar, X0, taus, 'anchored', fd=fd)
        g = ar.grad(Xe).ravel() * taus[-1]; f = net.internal_forces(Xe).ravel() + g
        mu = np.linalg.lstsq(C.T, -f, rcond=None)[0]
        rec[f'gauge_{lab}'] = dict(tau=taus[-1], converged=bool(oke and oka), rmsd_anchored_vs_eckart=float(rmsd_fit(Xa, Xe)),
                                   eckart_reaction_rel=float(np.linalg.norm(C.T @ mu) / np.linalg.norm(g)),
                                   Mxy_current=load_resultants(ar, Xe, X0)['Mxy'])
        if has_t:
            ma = target_metrics(Xa, idx, XE, P0, Delta, unl, tm); me = target_metrics(Xe, idx, XE, P0, Delta, unl, tm)
            rec[f'gauge_{lab}']['metric_shift_tm'] = float(abs(ma['rmsd_tm'] - me['rmsd_tm']))
        sols[lab] = Xe
        if lab == 'raw':
            # statically determinate support: reactions = -(resultant of the load in the current configuration)
            fa = net.internal_forces(Xa).ravel() + taus[-1] * ar.grad(Xa).ravel()
            Ka = (net.tangent(Xa) - taus[-1] * ar.H).tocsc()[fd][:, fd]
            la = float(spla.eigsh(Ka, k=1, sigma=-1e-6, which='LM', return_eigenvectors=False)[0])
            le = float(spectrum(net, ar, Xe, taus[-1], C, k=1)['lam'][0])
            an = np.unique(anchor // 3); arm = float(max(np.linalg.norm(X0[i] - X0[j]) for i in an for j in an))
            rec['gauge_raw'].update(anchor_reaction_rel=float(np.linalg.norm(fa[anchor]) / np.linalg.norm(g)),
                                    lambda_anchored=la, lambda_eckart=le, anchor_span=arm, n_anchor_nodes=int(len(an)))
    Xs4, ok4 = X0.copy(), True
    for t in taus:
        Xs4, it, rel, gr4, ok = newton_eckart(net, raw, Xs4, X0, t, C4); ok4 &= ok
    Rk, _ = kabsch(X0, Xs4)
    rec['gauge_symmetry'] = dict(converged=bool(ok4), reaction_rel=float(gr4), rmsd_vs_eckart6=float(rmsd_fit(Xs4, sols['raw'])),
                                 tilt_deg=float(np.degrees(np.arccos(np.clip((np.trace(Rk) - 1) / 2, -1, 1)))),
                                 n_neg=int(constrained_inertia(net, raw, Xs4, taus[-1], C4)['n_neg']))
    if has_t:
        m4 = target_metrics(Xs4, idx, XE, P0, Delta, unl, tm); m6 = target_metrics(sols['raw'], idx, XE, P0, Delta, unl, tm)
        rec['gauge_symmetry']['metric_shift_tm'] = float(abs(m4['rmsd_tm'] - m6['rmsd_tm']))
    rec['time_s'] = time.time() - T0
    out[name] = rec
    json.dump(out, open(outf, 'w'), indent=1, default=float)
    print(name, json.dumps({k: rec[k] for k in ('gauge_raw', 'gauge_eq', 'gauge_symmetry', 'lambda1_x0', 'grad_fd_rel_max', 'area_operator_vs_direct')}, default=float), f'{rec["time_s"]:.0f}s', flush=True)
