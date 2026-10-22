"""Explicit VFIFE cross-check in the nonlinear regime (editor M3b) and work-energy convergence (M8c).

vfife mode: the explicit VFIFE path solver (central differences, reverse-motion truss forces, Gershgorin masses,
damping 2*omega_min, Eckart constraint forces) is restarted from the converged Newton state at load step k and
driven to the tension of step k+1; its rest state is compared with the Newton state k+1.
    usage: python vfife_check.py vfife NAME RC k1 [k2 ...]        (k = 1-based Newton step index of the start)
work mode: Newton paths with fixed load increments h, h/2, h/4, h/8 up to the same tension; the trapezoidal
work-energy mismatch |U - W|/U must decrease as h^2.
    usage: python vfife_check.py work NAME RC TAU_END
output: results/vfife_checks.json (merged by key)
"""
import sys, os, json, time
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *
from vfife.explicit import VFIFETruss, nodal_mass_gershgorin
from vfife.tension import TensionPathSolver

mode, name, rc = sys.argv[1], sys.argv[2], float(sys.argv[3])
outf = f'{RES}/vfife_checks.json'
M = model(name, rc); X0 = M['X0']; net = TrussNetwork(X0, M['pairs'], k=1.0)
area, _ = make_area(M); C = gauge_C(X0)
tag = f'{name}_rc{int(rc)}'


class EckartVFIFE(TensionPathSolver):
    """f_c = f + C^T mu, mu = -(C M^-1 C^T)^-1 C M^-1 f  =>  C a = C v = C (x - x0) = 0 exactly."""
    def force(self, X, f_int, tau):
        f = (f_int + tau * self.area.grad(X)).ravel()
        mi = 1.0 / np.repeat(self.m, 3)
        A = (C * mi) @ C.T
        mu = -np.linalg.solve(A, (C * mi) @ f)
        return (f + C.T @ mu).reshape(-1, 3)


def merge(key, val):
    out = json.load(open(outf)) if os.path.exists(outf) else {}
    out[key] = val
    json.dump(out, open(outf, 'w'), indent=1, default=float)


if mode == 'vfife':
    P = json.load(open(f'{RES}/paths/{tag}.json')); Xs = np.load(f'{RES}/paths/{tag}_Xs.npy')
    res = []
    for k in map(int, sys.argv[4:]):
        T0 = time.time()
        Xk, Xk1 = Xs[k - 1], Xs[k]; tk, tk1 = P['rows'][k - 1]['tau'], P['rows'][k]['tau']
        elem = VFIFETruss(X0, M['pairs'])
        Hrow = np.abs(area.H).sum(axis=1).A.ravel().reshape(-1, 3).max(axis=1)
        mass = nodal_mass_gershgorin(elem, Xk) + tk1 * Hrow
        anchor = rigid_anchor_dofs(X0, exclude_nodes=area.vertices); fd = np.setdiff1d(np.arange(3 * net.N), anchor)
        Kf = (net.tangent(Xk) - tk * area.H).tocsc()[fd][:, fd]; Mf = np.repeat(mass, 3)[fd]
        lam = spla.eigsh(Kf, k=1, M=sp.diags(Mf).tocsc(), sigma=-1e-7, which='LM', return_eigenvectors=False)[0]
        S = EckartVFIFE(elem, area, X0, np.array([], int), mass, 2 * np.sqrt(max(lam, 1e-12)), tol_R=1e-8, tol_K=1e-13,
                        max_steps=600000, check_every=200)
        # restart the explicit solver from the converged Newton state k (exact axial forces, zero velocity)
        S.X = Xk.copy(); S.V = np.zeros_like(Xk); S.tau = tk
        Nax = elem.k * (np.linalg.norm(Xk[elem.q] - Xk[elem.p], axis=1) - elem.l0)
        elem.start_path_unit(Xk, N_a=Nax)
        S.f_int, S.Nax = elem.internal_forces(Xk)
        r = S.load_step(tk1)
        d = np.linalg.norm(S.X - Xk1, axis=1)
        rec = dict(start_step=k, eps_start=P['rows'][k - 1]['eps'], eps_end=P['rows'][k]['eps'], tau_end=tk1,
                   converged=r['converged'], explicit_steps=r['steps'], eta_R=r['eta_R'], eta_K=r['eta_K'],
                   maxdev=float(d.max()), rmsdev=float(np.sqrt((d ** 2).mean())),
                   incr_max=float(np.linalg.norm(Xk1 - Xk, axis=1).max()), wall_s=time.time() - T0)
        res.append(rec); print(name, rec, flush=True)
        prev = json.load(open(outf)).get(f'vfife_{tag}', []) if os.path.exists(outf) else []
        merge(f'vfife_{tag}', [p for p in prev if p['start_step'] != k] + [rec])
elif mode == 'work':
    tau_end = float(sys.argv[4]); out = []
    for m_ in (4, 8, 16, 32):
        h = tau_end / m_; X = X0.copy(); A_prev = area.area(X0); W = 0.0; tau = 0.0
        for i in range(m_):
            tn = tau + h
            X, it, rel, gr, ok = newton_eckart(net, area, X, X0, tn, C)
            A = area.area(X); W += 0.5 * (tau + tn) * (A - A_prev); A_prev, tau = A, tn
        U = net.energy(X)
        out.append(dict(n_steps=m_, h=h, U=U, W=W, rel=abs(U - W) / U))
        print(out[-1], flush=True)
    rates = [np.log2(out[i]['rel'] / out[i + 1]['rel']) for i in range(len(out) - 1)]
    merge(f'work_{tag}', dict(tau_end=tau_end, rows=out, observed_order=rates))
    print('orders', rates)
