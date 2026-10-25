"""Physical scale (editor M7a, M7b).

(i)  Area change.  dA_exp = A(x_exp) - A(x0) with the SAME area operator, where x_exp is the closed structure
     displaced by the experimental displacement on the mapped C-alpha (unmapped loaded nodes receive the
     inverse-distance-weighted displacement of their 4 nearest mapped neighbours).  Compared with the model dA at
     the best frame and at eps*.
(ii) Spring constant from B-factors.  <|u_i|^2> = kT/gamma (K+)_ii with K+ the Eckart-constrained pseudo-inverse,
     B_i = 8 pi^2 <|u_i|^2> / 3.  gamma = kT sum_i (K+)_ii / sum_i <|u_i|^2>_exp (trace estimator).  (K+)_ii is
     exact (dense) for N <= 2000 and estimated by Hutchinson probing (400 Rademacher probes) otherwise.
     The tension scale follows from  tau_phys = gamma * tau_model  (gamma in pN/A -> tau in pN/A = 10 mN/m).
usage: python physcale.py        output: results/physical_scale.json
"""
import sys, os, json, time
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *

KT = 41.14   # pN*A at 298 K
BFILE = {'4wff': raw('4WFF.pdb')}
METHOD = {'6b3r': 'cryo-EM', '6pwn': 'cryo-EM', '2oar': 'X-ray', '4xdk': 'X-ray', '4wff': 'X-ray', '6mgv': 'cryo-EM'}


def bfactors(name, order):
    f = BFILE.get(name, PROTEINS[name]['pdb']); d = {}
    for l in open(f):
        if l.startswith('ATOM') and l[12:16] == ' CA ' and l[16] in ' A':
            d.setdefault((l[21], int(l[22:26])), float(l[60:66]))
    return np.array([d.get(k, np.nan) for k in order])


out = {}
for name in PANEL:
    T0 = time.time()
    M = model(name, 10.0); X0 = M['X0']; net = TrussNetwork(X0, M['pairs'], k=1.0); area, _ = make_area(M)
    C = gauge_C(X0); Cs = sp.csr_matrix(C); n = 3 * net.N
    rec = dict(method=METHOD[name])
    # (i) experimental area change
    idx, P0, XE, Delta, info = build_target(name, M)
    disp = np.full((net.N, 3), np.nan); disp[idx] = Delta
    mapped = ~np.isnan(disp[:, 0]); tree = cKDTree(X0[mapped]); mi = np.where(mapped)[0]
    ver = area.vertices; miss = ver[~mapped[ver]]
    D = disp.copy()
    if len(miss):
        dd, jj = tree.query(X0[miss], k=4); w = 1 / np.maximum(dd, 1e-6); w /= w.sum(1, keepdims=True)
        D[miss] = (w[:, :, None] * disp[mi[jj]]).sum(1)
    D[np.isnan(D[:, 0])] = 0.0
    rec['A0_nm2'] = area.area(X0) / 100
    rec['dA_exp_nm2'] = (area.area(X0 + D) - area.area(X0)) / 100
    rec['loaded_mapped_frac'] = float(mapped[ver].mean())
    # (ii) B-factor calibration
    B = bfactors(name, M['order']); ok = np.isfinite(B) & (B > 0)
    import kkt
    if kkt.AVAILABLE:                     # bordered K0 by PARDISO (one factorisation), 2 refinement steps per solve
        kk = kkt.get(net, None, C).factor(net.tangent(X0)); bsolve = lambda b: kk.solve(b)[0]
    else:
        lu = spla.splu(sp.bmat([[net.tangent(X0).tocsc(), Cs.T], [Cs, None]]).tocsc())
        bsolve = lambda b: lu.solve(np.concatenate([b, np.zeros(6)]))[:n]
    if net.N <= 2000:
        import scipy.linalg as sla
        Z = sla.null_space(C); Kc = Z.T @ (net.tangent(X0).toarray() @ Z)
        w, V = np.linalg.eigh(0.5 * (Kc + Kc.T)); ZV = Z @ V
        dg = ((ZV ** 2) / w[None, :]).sum(1); est = 'dense'
    else:
        rng = np.random.default_rng(0); acc = np.zeros(n); npb = 400
        for _ in range(npb):
            z = rng.choice([-1.0, 1.0], size=n); acc += z * bsolve(z)
        dg = acc / npb; est = f'hutchinson({npb})'
    Kii = dg.reshape(-1, 3).sum(1)                           # trace of 3x3 block, A^2 per (pN/A)/kT
    u2 = 3 * B / (8 * np.pi ** 2)
    if ok.sum() > 10:
        g_tr = KT * Kii[ok].sum() / u2[ok].sum()
        g_i = KT * Kii[ok] / u2[ok]
        rec.update(gamma_trace_pN_per_A=float(g_tr), gamma_node_median=float(np.median(g_i)),
                   gamma_node_iqr=[float(np.percentile(g_i, 25)), float(np.percentile(g_i, 75))],
                   bfactor_corr=float(np.corrcoef(Kii[ok], B[ok])[0, 1]), n_B=int(ok.sum()), Kdiag_estimator=est)
    else:
        rec.update(note='no usable B-factors')
    rec['time_s'] = time.time() - T0
    out[name] = rec
    print(name, json.dumps(rec, default=float)[:400], flush=True)
json.dump(out, open(f'{RES}/physical_scale.json', 'w'), indent=1, default=float)
