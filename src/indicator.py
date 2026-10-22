"""A-priori second-order indicator of geometric nonlinearity (editor M2d).

Equilibrium  grad U(x) - tau H x + C^T mu = 0,  C (x - x0) = 0  is expanded as  x = x0 + tau u1 + tau^2 u2 + O(tau^3):
    O(tau):    K0 u1 = H x0                                  (u1 = linear response per unit tension)
    O(tau^2):  K0 u2 = H u1 - 1/2 D3U[u1, u1]                 (both solves Eckart-bordered)
with D3U[u1,u1] = d^2/dh^2 grad U(x0 + h u1) |_{h=0}, evaluated by a central second difference (grad U(x0) = 0).
At the common load level tau_ref = eps_ref / eps_per_tau the indicator is
    chi = tau_ref ||u2_perp|| / ||u1||,   u2_perp = u2 - (u2.u1/u1.u1) u1,
i.e. the predicted change of DIRECTION of the response, which a best-amplitude linear model cannot absorb,
and kappa = tau_ref (u2.u1)/(u1.u1), the predicted relative change of amplitude.  Both use only the reference
state.  Evaluated for all nodes, the membrane nodes and the validation TM subset.
usage: python indicator.py [names...]   output: results/indicator.json
"""
import sys, os, json, time
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *

names = sys.argv[1:] or PANEL + EXTRA
EPS_REF = (0.05, 0.10)
outf = f'{RES}/indicator.json'
out = json.load(open(outf)) if os.path.exists(outf) else {}
for name in names:
    T0 = time.time()
    M = model(name, 10.0); X0 = M['X0']; mem = M['mem']; net = TrussNetwork(X0, M['pairs'], k=1.0)
    area, _ = make_area(M); C = gauge_C(X0); Cs = sp.csr_matrix(C); n = 3 * net.N
    lu = spla.splu(sp.bmat([[net.tangent(X0).tocsc(), Cs.T], [Cs, None]]).tocsc())
    solve = lambda b: lu.solve(np.concatenate([b, np.zeros(6)]))[:n]
    u1 = solve(area.H @ X0.ravel())
    er = np.zeros((len(mem), 3)); er[:, :2] = M['m']['e_r']; R0 = M['m']['radii'].mean()
    eps_per_tau = float(((u1.reshape(-1, 3)[mem]) * er).sum(1).mean() / R0)
    gU = lambda x: -net.internal_forces(x.reshape(-1, 3)).ravel()
    errs = []
    D3 = None
    for h in (2e-3, 1e-3):
        hh = h / np.abs(u1).max()
        d3 = (gU(X0.ravel() + hh * u1) + gU(X0.ravel() - hh * u1)) / hh ** 2
        if D3 is not None:
            errs.append(float(np.linalg.norm(d3 - D3) / np.linalg.norm(d3)))
        D3 = d3
    u2 = solve(area.H @ u1 - 0.5 * D3)
    sets = dict(all=np.arange(net.N), mem=mem)
    if PROTEINS[name]['target'] is not None:
        idx, P0, XE, Delta, info = build_target(name, M)
        sets['tm'] = idx[np.isin(idx, mem)]
    rec = dict(eps_per_tau=eps_per_tau, fd_rel_change=errs)
    for lab, s in sets.items():
        a1 = u1.reshape(-1, 3)[s].ravel(); a2 = u2.reshape(-1, 3)[s].ravel()
        par = float(a2 @ a1 / (a1 @ a1)); perp = a2 - par * a1
        for e in EPS_REF:
            t = e / eps_per_tau
            rec[f'{lab}_eps{e:.2f}'] = dict(chi=float(t * np.linalg.norm(perp) / np.linalg.norm(a1)), kappa=float(t * par))
    out[name] = rec; json.dump(out, open(outf, 'w'), indent=1, default=float)
    print(name, {k: v for k, v in rec.items() if 'eps0.10' in k}, f'{time.time()-T0:.0f}s', flush=True)
