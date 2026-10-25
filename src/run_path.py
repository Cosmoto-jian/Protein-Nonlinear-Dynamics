"""Tension path of one channel (r5 production).

Eckart gauge (six linearised conditions) for every channel, bordered Newton with backtracking on
Pi = U - tau*A, certified inertia (inertia.py) at every accepted load step, lowest constrained eigenvalues by
shift-invert, element-strain statistics (all / backbone), validation metrics against the partner structure for the
nonlinear path and for the linear response at the same tension, and the amplitude/direction decomposition of the
linearisation error.

usage: python run_path.py NAME RC [--refine] [--nscale s] [--shell w] [--slab t] [--dh h] [--kbb k] [--tag T]
       [--no-inertia]
output: results/runs/{NAME}_rc{RC}{T}.json and _Xs.npy
"""
import sys, os, json, time, argparse
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *
from inertia import constrained_inertia
import ckpt
import kkt

ap = argparse.ArgumentParser()
ap.add_argument('name'); ap.add_argument('rc', type=float)
ap.add_argument('--refine', action='store_true', help='quarter load step for eps > 0.08')
ap.add_argument('--nscale', type=float, default=1.0); ap.add_argument('--shell', type=float, default=4.0)
ap.add_argument('--slab', type=float, default=4.0); ap.add_argument('--dh', type=float, default=0.0)
ap.add_argument('--kbb', type=float, default=1.0, help='stiffness factor of backbone (i,i+1) elements')
ap.add_argument('--tag', default=''); ap.add_argument('--no-inertia', action='store_true')
ap.add_argument('--eps-max', type=float, default=0.40); ap.add_argument('--max-steps', type=int, default=150)
a = ap.parse_args()
name, rc = a.name, a.rc
T0 = time.time(); tag = f'{name}_rc{int(rc)}{a.tag}'
M = model(name, rc); X0, pairs, mem = M['X0'], M['pairs'], M['mem']
order = M['order']
bb = np.array([order[i][0] == order[j][0] and abs(order[i][1] - order[j][1]) == 1 for i, j in pairs])
kvec = np.where(bb, a.kbb, 1.0)
net = TrussNetwork(X0, pairs, k=kvec)
area, n_sector = make_area(M, n_scale=a.nscale, shell=a.shell, slab=a.slab, dh=a.dh)
C = gauge_C(X0); Cs = sp.csr_matrix(C); n = 3 * net.N
er = np.zeros((len(mem), 3)); er[:, :2] = M['m']['e_r']; R0 = M['m']['radii'].mean()
eps_of = lambda X: float(((X[mem] - X0[mem]) * er).sum(1).mean() / R0)


def strain_stats(X):
    l0 = net.l0; l = net.element_lengths(X); e = np.abs(l / l0 - 1)
    return dict(max_e=float(e.max()), p10=float((e > 0.1).mean()), p20=float((e > 0.2).mean()),
                max_e_bb=float(e[bb].max()), p05_bb=float((e[bb] > 0.05).mean()), max_e_nonbb=float(e[~bb].max()))


def rigid_angle(X):
    Rk, _ = kabsch(X0, X)
    return float(np.degrees(np.arccos(np.clip((np.trace(Rk) - 1) / 2, -1, 1))))


def enl_parts(X, uL, sel=None):
    """amplitude ratio and direction error of the linear vs nonlinear displacement (rigid motion removed)."""
    Rk, t = kabsch(X, X0); uN = (X @ Rk.T + t - X0)
    Rl, tl = kabsch(X0 + uL, X0); uLr = ((X0 + uL) @ Rl.T + tl - X0)
    if sel is not None:
        uN, uLr = uN[sel], uLr[sel]
    uN, uLr = uN.ravel(), uLr.ravel(); nN, nL = np.linalg.norm(uN), np.linalg.norm(uLr)
    c = float(uN @ uLr / (nN * nL)) if nN > 0 and nL > 0 else 1.0
    return dict(E_NL=float(np.linalg.norm(uN - uLr) / nN) if nN > 0 else 0.0, amp=float(nL / nN) if nN > 0 else 1.0,
                dir=float(np.sqrt(max(0.0, 1 - c * c))))


def lowest_eigs(X, tau, k=4):
    try:
        return spectrum(net, area, X, tau, C, dense_max=700, k=k)['lam']
    except Exception as ex:
        return None


def stability(X, tau, k=4):
    """(certified inertia or None, lowest eigenvalues) at an accepted state.  With kkt (PARDISO) and N > 700 both come
    from ONE factorisation of the bordered tangent (scheme B); otherwise the separate calls."""
    if kkt.AVAILABLE and net.N > 700:
        return kkt.get(net, area, C).inertia_and_eigs(net.tangent(X) - tau * area.H, k=k, with_inertia=not a.no_inertia)
    lam = lowest_eigs(X, tau, k=k)
    return (None if a.no_inertia else constrained_inertia(net, area, X, tau, C)), lam


# ---------- reference quantities
# Mechanism guard: if the constrained tangent at X0 has zero eigenvalues beyond the six rigid modes (Eckart gauge),
# the bordered KKT system below is singular, the linear response uL1 (and hence eps_per_tau and the load step) is
# round-off and the path is not defined.  Such runs are recorded as stop='mechanism' with no path.
inertia0 = None if a.no_inertia else constrained_inertia(net, area, X0, 0.0, C)
mechanism = inertia0 is not None and inertia0['n_zero'] > 0
g0 = area.grad(X0)
if mechanism:
    uL1, eps_per_tau = None, None
else:
    if kkt.AVAILABLE:
        uL1 = kkt.linear_response(net, area, C, X0, g0).reshape(-1, 3)
    else:
        KKT0 = sp.bmat([[net.tangent(X0).tocsc(), Cs.T], [Cs, None]]).tocsc()
        uL1 = spla.spsolve(KKT0, np.concatenate([g0.ravel(), np.zeros(6)]))[:n].reshape(-1, 3)
    eps_per_tau = eps_of(X0 + uL1)
pre = dict(name=name, rc=rc, gauge='eckart', N=int(net.N), E=int(net.E), n_bb=int(bb.sum()), n_mem=int(len(mem)),
           options=vars(a), n_sector=n_sector, n_loaded=int(len(area.vertices)), n_slabs=len(area.polys),
           eps_per_tau=eps_per_tau, A0=area.area(X0), load_resultants_x0=load_resultants(area, X0, X0),
           lam0=None if mechanism else lowest_eigs(X0, 0.0, k=6))
if inertia0 is not None:
    pre['inertia0'] = inertia0
tgt = None
if PROTEINS[name]['target'] is not None and not mechanism:
    idx, P0, XE, Delta, info = build_target(name, M)
    unl = ~np.isin(idx, area.vertices); tm = np.isin(idx, mem)
    s_grid = np.linspace(0, 0.6 / eps_per_tau, 121)
    lin = []
    for s in s_grid:
        mtr = target_metrics(X0 + s * uL1, idx, XE, P0, Delta, unl, tm)
        lin.append(dict(s=float(s), eps=float(eps_of(X0 + s * uL1)), **mtr))
    info['linear_grid'] = lin
    info['n_tm_common'] = int(tm.sum()); info['n_loaded_common'] = int((~unl).sum())
    info['rmsd_closed_vs_target_tm'] = target_metrics(X0, idx, XE, P0, Delta, unl, tm)['rmsd_tm']
    # experimental area change with the same operator on the mapped nodes (closed nodes replaced by partner)
    tgt = dict(idx=idx, P0=P0, XE=XE, Delta=Delta, unl=unl, tm=tm)
    pre['target'] = info
else:
    pre['target'] = None
print('pre', tag, 'N', net.N, 'mechanism n_zero=%d' % inertia0['n_zero'] if mechanism else 'eps/tau %.4g' % eps_per_tau,
      f'{time.time()-T0:.0f}s', flush=True)
if mechanism:
    np.save(f'{RES}/paths/{tag}_Xs.npy', np.array([]))
    json.dump(dict(pre=pre, rows=[], stop='mechanism', n_fail=0, wall_s=time.time() - T0), open(f'{RES}/paths/{tag}.json', 'w'),
              default=float)
    ckpt.clear(tag)
    print('DONE', tag, 'mechanism', f'{time.time()-T0:.0f}s', flush=True)
    sys.exit(0)

# ---------- path
rows, Xs = [], []
X, tau, A_prev, W = X0.copy(), 0.0, area.area(X0), 0.0
dtau0 = 0.01 / eps_per_tau; dtau = dtau0; n_fail = 0; stop = None; wall_prev = 0.0
st = ckpt.load(tag)
if st is not None:
    rows, Xs, X, tau, A_prev, W, dtau, n_fail, wall_prev = (st[k] for k in ('rows', 'Xs', 'X', 'tau', 'A_prev', 'W', 'dtau', 'n_fail', 'wall'))
    T0 = time.time() - wall_prev
while True:
    cap = 0.02 / eps_per_tau
    eps_now = eps_of(X)
    if a.refine and eps_now > 0.08:
        cap = 0.0025 / eps_per_tau
    dtau = min(dtau, cap)
    t_new = tau + dtau
    Xn, it, rel, react, ok = (newton_eckart_fast if net.N > 2000 else newton_eckart)(net, area, X, X0, t_new, C)
    if not ok:
        dtau *= 0.5; n_fail += 1
        if dtau < 1e-3 * dtau0:
            stop = 'newton stalled'; break
        continue
    A = area.area(Xn); W += 0.5 * (tau + t_new) * (A - A_prev)
    U = net.energy(Xn)
    rec = dict(step=len(rows) + 1, tau=t_new, eps=eps_of(Xn), newton_iters=it, newton_rel=rel, gauge_reaction_rel=react,
               U=U, W=W, work_energy_rel=abs(U - W) / max(U, 1e-30), A=A, dA=A - pre['A0'],
               rigid_rotation_deg=rigid_angle(Xn), **strain_stats(Xn))
    uL = t_new * uL1
    rec['enl_all'] = enl_parts(Xn, uL)
    rec['enl_mem'] = enl_parts(Xn, uL, mem)
    if tgt:
        rec['nl'] = target_metrics(Xn, tgt['idx'], tgt['XE'], tgt['P0'], tgt['Delta'], tgt['unl'], tgt['tm'])
        rec['lin'] = target_metrics(X0 + uL, tgt['idx'], tgt['XE'], tgt['P0'], tgt['Delta'], tgt['unl'], tgt['tm'])
    _in, rec['lam'] = stability(Xn, t_new, k=4)
    if not a.no_inertia:
        rec['inertia'] = _in
    rows.append(rec); Xs.append(Xn.copy())
    X, tau, A_prev = Xn, t_new, A
    if it <= 5:
        dtau *= 1.25
    ckpt.save(tag, dict(rows=rows, Xs=Xs, X=X, tau=tau, A_prev=A_prev, W=W, dtau=dtau, n_fail=n_fail, wall=time.time() - T0))
    print(tag, rec['step'], 'eps %.4f tau %.4g it %d p20 %.4f maxe %.3f bb %.3f' % (rec['eps'], t_new, it, rec['p20'], rec['max_e'], rec['max_e_bb']),
          ('tm %.3f/%.3f' % (rec['nl']['rmsd_tm'], rec['lin']['rmsd_tm'])) if tgt else '',
          'neg %s' % (rec['inertia']['n_neg'] if 'inertia' in rec else '-'), 'lam %.2e' % (rec['lam'][0] if rec['lam'] else np.nan),
          f'{time.time()-T0:.0f}s', flush=True)
    if rec['eps'] >= a.eps_max: stop = f'eps>={a.eps_max}'; break
    if rec['p20'] > 0.12: stop = 'p20>0.12'; break
    if rec['max_e'] > 1.0: stop = 'max_e>1.0'; break
    if len(rows) >= a.max_steps: stop = 'max steps'; break
    if 'inertia' in rec and rec['inertia']['n_neg'] > 0: stop = 'negative eigenvalue'; break

np.save(f'{RES}/paths/{tag}_Xs.npy', np.array(Xs))
res = dict(pre=pre, rows=rows, stop=stop, n_fail=n_fail, wall_s=time.time() - T0)
json.dump(res, open(f'{RES}/paths/{tag}.json', 'w'), default=float)
ckpt.clear(tag)
print('DONE', tag, stop, f'{time.time()-T0:.0f}s', kkt.stats_line() if kkt.AVAILABLE else 'scipy', flush=True)
