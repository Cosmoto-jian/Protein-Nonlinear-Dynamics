"""Snap-through at the limit point of the Piezo1 tension path, by explicit VFIFE dynamics (editor M3a).

Under tension control the stable branch ends at the limit point tau_c (dlam/ds = 0, one eigenvalue of the constrained
tangent crosses zero; arclength.py).  For tau slightly above tau_c no nearby equilibrium exists, and the structure
snaps.  The explicit VFIFE solver (central differences, reverse-motion truss forces, damping, Eckart constraint forces)
is started at rest from the limit-point state with tau = (1 + d) tau_c; its rest state is the post-snap equilibrium,
polished by Newton and certified by inertia.  The post-snap branch is compared with the stable branch found by continuation beyond the
second limit point (corrected to the same tension); the elements that carry the snap are listed.

usage: python snap.py NAME RC [d=1e-3]
output: results/runs/{NAME}_rc{RC}_snap.json, _snap_states.npy (limit-point and post-snap states)
"""
import sys, os, json, time
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *
from inertia import constrained_inertia
from vfife.explicit import VFIFETruss, nodal_mass_gershgorin
from vfife.tension import TensionPathSolver

name, rc = sys.argv[1], float(sys.argv[2]); d = float(sys.argv[3]) if len(sys.argv) > 3 else 1e-3
T0 = time.time(); tag = f'{name}_rc{int(rc)}'
A = json.load(open(f'{RES}/paths/{tag}_arclength.json')); XA = np.load(f'{RES}/paths/{tag}_arclength_Xs.npy')
pts = A['points']; kf = int(np.argmax([q['tau'] for q in pts])); tau_c = pts[kf]['tau']; Xf = XA[kf]
M = model(name, rc); X0, pairs, mem, order = M['X0'], M['pairs'], M['mem'], M['order']
bb = np.array([order[i][0] == order[j][0] and abs(order[i][1] - order[j][1]) == 1 for i, j in pairs])
net = TrussNetwork(X0, pairs, k=1.0); area, _ = make_area(M); C = gauge_C(X0); n = 3 * net.N; x0 = X0.ravel()
er = np.zeros((len(mem), 3)); er[:, :2] = M['m']['e_r']; R0 = M['m']['radii'].mean()
eps_of = lambda X: float(((X[mem] - X0[mem]) * er).sum(1).mean() / R0)
uL1 = EckartSolver(net.tangent(X0).tocsc(), C, eckart_pivots(C)).solve(area.H @ x0)[0].reshape(-1, 3)
idx, P0, XE, Delta, info = build_target(name, M); unl = ~np.isin(idx, area.vertices); tm = np.isin(idx, mem)


def strains(X):
    ee = np.abs(net.element_lengths(X) / net.l0 - 1)
    return dict(max_e=float(ee.max()), p10=float((ee > 0.1).mean()), p20=float((ee > 0.2).mean()), max_e_bb=float(ee[bb].max()),
                p05_bb=float((ee[bb] > 0.05).mean()), max_e_nonbb=float(ee[~bb].max())), ee


def enl_parts(X, uL, sel=None):
    Rk, t = kabsch(X, X0); uN = (X @ Rk.T + t - X0)
    Rl, tl = kabsch(X0 + uL, X0); uLr = ((X0 + uL) @ Rl.T + tl - X0)
    if sel is not None:
        uN, uLr = uN[sel], uLr[sel]
    uN, uLr = uN.ravel(), uLr.ravel(); nN, nL = np.linalg.norm(uN), np.linalg.norm(uLr); c = float(uN @ uLr / (nN * nL))
    return dict(E_NL=float(np.linalg.norm(uN - uLr) / nN), amp=float(nL / nN), dir=float(np.sqrt(max(0.0, 1 - c * c))))


def full_record(X, tau):
    st, _ = strains(X); uL = tau * uL1; Aa = area.area(X)
    rec = dict(tau=tau, eps=eps_of(X), U=net.energy(X), A=Aa, dA=Aa - area.area(X0), **st,
               enl_all=enl_parts(X, uL), enl_mem=enl_parts(X, uL, mem),
               nl=target_metrics(X, idx, XE, P0, Delta, unl, tm), lin=target_metrics(X0 + uL, idx, XE, P0, Delta, unl, tm),
               inertia=constrained_inertia(net, area, X, tau, C), lam=spectrum(net, area, X, tau, C, k=4)['lam'])
    f = net.internal_forces(X).ravel() + tau * (area.H @ X.ravel()); mu = np.linalg.lstsq(C.T, -f, rcond=None)[0]
    rec['gauge_reaction_rel'] = float(np.linalg.norm(C.T @ mu) / np.linalg.norm(tau * (area.H @ X.ravel())))
    Rk, _ = kabsch(X0, X); rec['rigid_rotation_deg'] = float(np.degrees(np.arccos(np.clip((np.trace(Rk) - 1) / 2, -1, 1))))
    return rec


class EckartVFIFE(TensionPathSolver):
    def force(self, X, f_int, tau):
        f = (f_int + tau * self.area.grad(X)).ravel(); mi = 1.0 / np.repeat(self.m, 3)
        mu = -np.linalg.solve((C * mi) @ C.T, (C * mi) @ f)
        return (f + C.T @ mu).reshape(-1, 3)


# ---- explicit snap at tau_s = (1+d) tau_c from rest at the limit point
tau_s = (1 + d) * tau_c
elem = VFIFETruss(X0, pairs)
Hrow = np.abs(area.H).sum(axis=1).A.ravel().reshape(-1, 3).max(axis=1)
mass = nodal_mass_gershgorin(elem, Xf) + tau_s * Hrow
anchor = rigid_anchor_dofs(X0, exclude_nodes=area.vertices); fd = np.setdiff1d(np.arange(n), anchor)
lam_ref = float(json.load(open(f'{RES}/paths/{tag}.json'))['pre']['lam0'][0])
alpha = 2 * np.sqrt(lam_ref / np.median(mass))
S = EckartVFIFE(elem, area, X0, np.array([], int), mass, alpha, tol_R=1e-8, tol_K=1e-14, max_steps=1, check_every=1)
S.X = Xf.copy(); S.V = np.zeros_like(Xf); S.tau = tau_s
elem.start_path_unit(Xf, N_a=elem.k * (np.linalg.norm(Xf[elem.q] - Xf[elem.p], axis=1) - elem.l0))
S.f_int, S.Nax = elem.internal_forces(Xf)
traj, snaps = [], []
nstep, conv = 0, False
while nstep < 600_000:
    for _ in range(500):
        S._step(0.0)
    nstep += 500
    F = S.force(S.X, S.f_int, tau_s); g = area.grad(S.X)
    eta_R = np.linalg.norm(F) / (tau_s * np.linalg.norm(g))
    U = net.energy(S.X); Tk = 0.5 * float(np.sum(S.m[:, None] * S.V ** 2))
    if nstep % 5000 == 0:
        st, _ = strains(S.X)
        traj.append(dict(n=nstep, eps=eps_of(S.X), U=U, T=Tk, Pi=U - tau_s * area.area(S.X), eta_R=float(eta_R), **st,
                         tm=target_metrics(S.X, idx, XE, P0, Delta, unl, tm)['rmsd_tm']))
        if nstep % 50000 == 0:
            snaps.append(S.X.copy())
            print('vfife', nstep, 'eps %.4f maxe %.3f Pi %.4f T/U %.1e eta %.1e' % (traj[-1]['eps'], traj[-1]['max_e'], traj[-1]['Pi'], Tk / U, eta_R),
                  f'{time.time()-T0:.0f}s', flush=True)
    if eta_R < 1e-7 and Tk / U < 1e-14:
        conv = True; break
X, it, rel, react, ok = newton_eckart_fast(net, area, S.X.copy(), X0, tau_s, C)
post = full_record(X, tau_s)
print('post-snap: vfife conv', conv, 'newton', ok, rel, 'polish change %.2e A' % np.abs(X - S.X).max(),
      'eps %.4f maxe %.3f neg %d tm %.3f' % (post['eps'], post['max_e'], post['inertia']['n_neg'], post['nl']['rmsd_tm']), flush=True)
pre = full_record(Xf, tau_c)
# ---- compare with the continuation: the stable branch beyond the second (lower) limit point, corrected to tau_s
dl = np.array([q['dlam_ds'] for q in pts]); taus = np.array([q['tau'] for q in pts])
folds = [i for i in range(1, len(dl)) if np.sign(dl[i]) != np.sign(dl[i - 1])]
cmp = None
if len(folds) >= 2:
    br3 = np.arange(folds[1], len(pts))
    if taus[br3].max() >= tau_s:
        j = br3[int(np.argmin(np.abs(taus[br3] - tau_s)))]
        Xc, itc, relc, _, okc = newton_eckart_fast(net, area, XA[j].copy(), X0, tau_s, C)
        cmp = dict(branch3_index=int(j), newton_ok=bool(okc), rmsd_vfife_vs_branch3=rmsd_fit(X, Xc),
                   maxdev_vfife_vs_branch3=float(np.linalg.norm(X - Xc, axis=1).max()))
print('comparison with continuation branch 3:', cmp, flush=True)
# localisation of the snap: elements whose strain changes most between the limit point and the post-snap state
_, e_pre = strains(Xf); _, e_post = strains(X)
de = e_post - e_pre; top = np.argsort(-np.abs(de))[:20]
loc = [dict(i=order[pairs[k, 0]], j=order[pairs[k, 1]], backbone=bool(bb[k]), e_pre=float(e_pre[k]), e_post=float(e_post[k])) for k in top]
disp = np.linalg.norm(X - Xf, axis=1); pr = float(disp.sum() ** 2 / (len(disp) * (disp ** 2).sum()))
json.dump(dict(tau_c=tau_c, limit_point_index=kf, folds=folds, tau_folds=[float(taus[i]) for i in folds],
               eps_folds=[float(pts[i]['eps']) for i in folds], d=d, tau_s=tau_s, vfife_converged=conv, vfife_steps=nstep, damping=alpha,
               newton_polish=dict(ok=bool(ok), rel=float(rel), max_change=float(np.abs(X - S.X).max())),
               pre_snap=pre, post_snap=post, comparison=cmp, trajectory=traj, snap_participation_ratio=pr,
               snap_max_node_displacement=float(disp.max()), snap_top_elements=loc),
          open(f'{RES}/paths/{tag}_snap.json', 'w'), default=float)
np.save(f'{RES}/paths/{tag}_snap_states.npy', np.array([Xf, X]))
print('DONE', f'{time.time()-T0:.0f}s', flush=True)
