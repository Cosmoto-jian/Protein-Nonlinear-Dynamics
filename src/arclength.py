"""Pseudo-arclength continuation of the tension path with the Eckart constraints (editor M3a).

Unknowns (x, mu, lam), lam = tau * eps_per_tau (load parameter normalised so that the linear response has eps = lam).
    F(x, mu, lam) = [grad U(x) - tau(lam) H x + C^T mu ;  C (x - x0)] = 0
    N(x, lam)     = t_x . (x - x_k) / s_x^2 + t_lam (lam - lam_k) - ds = 0          (Keller pseudo-arclength)
Newton on the augmented system by block elimination: two solves with the Eckart-bordered tangent
J = [[K_t - tau H, C^T],[C, 0]] per iteration (EckartSolver).  Step control: a step is accepted only if the corrector
converges in <= 12 iterations and successive unit tangents satisfy t_k . t_{k+1} >= 0.98 (otherwise ds is halved), so
that folds are resolved rather than jumped.  Every accepted point carries the same record as run_path.py (strains,
validation metrics, linearisation error, lowest eigenvalues, certified inertia); dlam/ds changes sign at a limit point,
the inertia changes at a bifurcation.

usage: python arclength.py NAME RC START_EPS [max_points] [ds]
output: results/runs/{NAME}_rc{RC}_arclength.json/_Xs.npy, and the merged production path
        results/runs/{NAME}_rc{RC}.json (load control up to START_EPS + continuation); the load-controlled original is
        kept as {NAME}_rc{RC}_loadcontrol.json
"""
import sys, os, json, time, shutil
import numpy as np, scipy.sparse as sp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *
from inertia import constrained_inertia

name, rc, e_start = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
npts = int(sys.argv[4]) if len(sys.argv) > 4 else 300
ds0 = float(sys.argv[5]) if len(sys.argv) > 5 else 0.003
T0 = time.time(); tag = f'{name}_rc{int(rc)}'
lc = f'{RES}/paths/{tag}_loadcontrol.json'
if not os.path.exists(lc):
    shutil.copy(f'{RES}/paths/{tag}.json', lc); shutil.copy(f'{RES}/paths/{tag}_Xs.npy', f'{RES}/paths/{tag}_loadcontrol_Xs.npy')
P = json.load(open(lc)); XsP = np.load(f'{RES}/paths/{tag}_loadcontrol_Xs.npy')
M = model(name, rc); X0, pairs, mem, order = M['X0'], M['pairs'], M['mem'], M['order']
bb = np.array([order[i][0] == order[j][0] and abs(order[i][1] - order[j][1]) == 1 for i, j in pairs])
net = TrussNetwork(X0, pairs, k=1.0); area, _ = make_area(M)
C = gauge_C(X0); n = 3 * net.N; H = area.H.tocsr(); x0 = X0.ravel()
er = np.zeros((len(mem), 3)); er[:, :2] = M['m']['e_r']; R0 = M['m']['radii'].mean()
eps_of = lambda X: float(((X[mem] - X0[mem]) * er).sum(1).mean() / R0)
e = P['pre']['eps_per_tau']
eps_path = np.array([r['eps'] for r in P['rows']])
k0 = int(np.argmin(np.abs(eps_path - e_start)))
x = XsP[k0].ravel().copy(); lam = P['rows'][k0]['tau'] * e
# linear response and target (same as run_path.py)
(uL1, _), = [EckartSolver(net.tangent(X0).tocsc(), C, eckart_pivots(C)).solve(area.H @ x0)]
uL1 = uL1.reshape(-1, 3)
idx, P0, XE, Delta, info = build_target(name, M); unl = ~np.isin(idx, area.vertices); tm = np.isin(idx, mem)


def enl_parts(X, uL, sel=None):
    Rk, t = kabsch(X, X0); uN = (X @ Rk.T + t - X0)
    Rl, tl = kabsch(X0 + uL, X0); uLr = ((X0 + uL) @ Rl.T + tl - X0)
    if sel is not None:
        uN, uLr = uN[sel], uLr[sel]
    uN, uLr = uN.ravel(), uLr.ravel(); nN, nL = np.linalg.norm(uN), np.linalg.norm(uLr)
    c = float(uN @ uLr / (nN * nL))
    return dict(E_NL=float(np.linalg.norm(uN - uLr) / nN), amp=float(nL / nN), dir=float(np.sqrt(max(0.0, 1 - c * c))))


def residual(x, mu, lam):
    r1 = -net.internal_forces(x.reshape(-1, 3)).ravel() - (lam / e) * (H @ x) + C.T @ mu
    return r1, C @ (x - x0)


def jac(x, lam):
    return (net.tangent(x.reshape(-1, 3)) - (lam / e) * H).tocsc(), -(H @ x) / e


def tangent(x, lam, prev, sx2):
    K, Fl = jac(x, lam)
    b, _ = EckartSolver(K, C, eckart_pivots(C)).solve(-Fl)
    nrm = np.sqrt(b @ b / sx2 + 1.0); tx, tl = b / nrm, 1.0 / nrm
    if prev is not None and (tx @ prev[0] / sx2 + tl * prev[1]) < 0:
        tx, tl = -tx, -tl
    return tx, tl


def record(x, lam, t, it, ds):
    X = x.reshape(-1, 3); tau = lam / e
    l = net.element_lengths(X); ee = np.abs(l / net.l0 - 1)
    A = area.area(X); U = net.energy(X); uL = tau * uL1
    rec = dict(tau=tau, eps=eps_of(X), dlam_ds=float(t[1]), ds=ds, newton_iters=it, U=U, A=A, dA=A - area.area(X0),
               max_e=float(ee.max()), p10=float((ee > 0.1).mean()), p20=float((ee > 0.2).mean()),
               max_e_bb=float(ee[bb].max()), p05_bb=float((ee[bb] > 0.05).mean()), max_e_nonbb=float(ee[~bb].max()),
               enl_all=enl_parts(X, uL), enl_mem=enl_parts(X, uL, mem),
               nl=target_metrics(X, idx, XE, P0, Delta, unl, tm), lin=target_metrics(X0 + uL, idx, XE, P0, Delta, unl, tm),
               inertia=constrained_inertia(net, area, X, tau, C))
    try:
        rec['lam'] = spectrum(net, area, X, tau, C, k=4)['lam']
    except Exception:
        rec['lam'] = None
    f = net.internal_forces(X).ravel() + tau * (H @ x)
    mu = np.linalg.lstsq(C.T, -f, rcond=None)[0]
    rec['gauge_reaction_rel'] = float(np.linalg.norm(C.T @ mu) / np.linalg.norm(tau * (H @ x)))
    Rk, _ = kabsch(X0, X); rec['rigid_rotation_deg'] = float(np.degrees(np.arccos(np.clip((np.trace(Rk) - 1) / 2, -1, 1))))
    return rec


K, Fl = jac(x, lam)
dxdl, _ = EckartSolver(K, C, eckart_pivots(C)).solve(-Fl)
sx2 = float(dxdl @ dxdl)
t = tangent(x, lam, (dxdl, 1.0), sx2)
mu = np.linalg.lstsq(C.T, -residual(x, np.zeros(6), lam)[0], rcond=None)[0]
pts = [record(x, lam, t, 0, 0.0)]; Xs = [x.reshape(-1, 3).copy()]
ds = ds0; n_rej = 0
print('start', tag, 'step', k0 + 1, 'eps %.4f' % pts[0]['eps'], flush=True)
while len(pts) < npts:
    xk, lk = x.copy(), lam
    xi, li, mui = x + ds * t[0], lam + ds * t[1], mu.copy(); ok = False
    for it in range(12):
        r1, r2 = residual(xi, mui, li)
        rN = (t[0] @ (xi - xk)) / sx2 + t[1] * (li - lk) - ds
        nr = np.linalg.norm(r1) / max(1.0, np.linalg.norm((li / e) * (H @ xi)))
        if nr < 1e-9 and np.linalg.norm(r2) < 1e-9 and abs(rN) < 1e-10:
            ok = True; break
        K, Fl = jac(xi, li)
        S = EckartSolver(K, C, eckart_pivots(C))
        a_x, a_m = S.solve(-r1, -r2); b_x, b_m = S.solve(-Fl)
        dl = (-rN - t[0] @ a_x / sx2) / (t[0] @ b_x / sx2 + t[1])
        xi += a_x + dl * b_x; mui += a_m + dl * b_m; li += dl
    tn = tangent(xi, li, t, sx2) if ok else None
    if not ok or (tn[0] @ t[0] / sx2 + tn[1] * t[1]) < 0.98:
        ds *= 0.5; n_rej += 1
        if ds < 1e-6:
            print('continuation failed', flush=True); break
        continue
    x, lam, mu, t = xi, li, mui, tn
    q = record(x, lam, t, it, ds); pts.append(q); Xs.append(x.reshape(-1, 3).copy())
    print(len(pts), 'eps %.5f tau %.6f dlam/ds %+.3f neg %d zero %d lam1 %.2e maxe %.3f p20 %.4f tm %.3f it %d ds %.1e' % (
        q['eps'], q['tau'], q['dlam_ds'], q['inertia']['n_neg'], q['inertia']['n_zero'], q['lam'][0] if q['lam'] else np.nan,
        q['max_e'], q['p20'], q['nl']['rmsd_tm'], it, ds), f'{time.time()-T0:.0f}s', flush=True)
    if it <= 4:
        ds = min(ds * 1.25, ds0)
    if q['p20'] > 0.12 or q['max_e'] > 1.0 or q['eps'] > 0.40:
        break
stop = 'p20>0.12' if pts[-1]['p20'] > 0.12 else ('max_e>1.0' if pts[-1]['max_e'] > 1.0 else ('eps>0.40' if pts[-1]['eps'] > 0.40 else 'max points'))
json.dump(dict(name=name, rc=rc, start_step=k0 + 1, sx2=sx2, n_rejected=n_rej, stop=stop, points=pts),
          open(f'{RES}/paths/{tag}_arclength.json', 'w'), default=float)
np.save(f'{RES}/paths/{tag}_arclength_Xs.npy', np.array(Xs))
# merged production path: load control up to the start point, continuation afterwards
rows = [dict(r) for r in P['rows'][:k0 + 1]]
for q in pts[1:]:
    r = dict(q); r['step'] = len(rows) + 1; r['continuation'] = True; rows.append(r)
W = rows[k0]['W']; tp, Ap = rows[k0]['tau'], rows[k0]['A']
for r in rows[k0 + 1:]:
    W += 0.5 * (tp + r['tau']) * (r['A'] - Ap); tp, Ap = r['tau'], r['A']
    r['W'] = W; r['work_energy_rel'] = abs(r['U'] - W) / r['U']
merged = dict(pre=dict(P['pre'], continuation=dict(start_step=k0 + 1, ds0=ds0, n_points=len(pts) - 1, n_rejected=n_rej)),
              rows=rows, stop=stop, n_fail=P['n_fail'], wall_s=P['wall_s'] + time.time() - T0,
              loadcontrol_stop=dict(reason=P['stop'], eps=P['rows'][-1]['eps'], tau=P['rows'][-1]['tau']))
json.dump(merged, open(f'{RES}/paths/{tag}.json', 'w'), default=float)
np.save(f'{RES}/paths/{tag}_Xs.npy', np.concatenate([XsP[:k0 + 1], np.array(Xs[1:])]))
print('DONE', tag, stop, f'{time.time()-T0:.0f}s', flush=True)
