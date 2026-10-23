"""Perturbation-response scanning (PRS) null on the transmembrane (TM) subset.

For every node i, the linear response to a unit force on i is the 3-column block G[:, i] of the Eckart-constrained
pseudo-inverse of the tangent stiffness at the closed structure.  The three force components are fitted by least
squares to the TM displacement closed -> target (target superposed on the closed TM subset), and the node whose fitted
response gives the lowest TM RMSD is reported.  Single-node scan only: this is not a multi-node or multi-mode PRS.
The fit uses the target to choose the node and three amplitudes, so the result is a target-informed reference, not a
prediction.  G is symmetric, so only the columns of the TM rows are solved.
The node ranking uses the residual of the least-squares fit; the exact TM RMSD (_rmsd_ovl) is evaluated on the
N_TOP best-ranked nodes.
usage: python src/prs.py [names...]        output: data/derived/prs.json
"""
import sys, os, json, time
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *
from model import _rmsd_ovl

RC = 10.0
N_TOP = 30
BLOCK = 600
names = [a for a in sys.argv[1:] if not a.startswith("--")] or PANEL
outf = f'{RES}/prs.json'
out = {}
for name in names:
    T0 = time.time()
    M = model(name, RC); X0 = M['X0']; net = TrussNetwork(X0, M['pairs'], k=1.0); N = net.N; n = 3 * N
    idx, P0, XE, Delta, info = build_target(name, M)
    tm = np.isin(idx, M['mem']); itm = idx[tm]
    R, t = kabsch(XE[tm], P0[tm]); D = ((XE[tm] @ R.T + t) - P0[tm]).ravel()
    C = sp.csr_matrix(gauge_C(X0))
    lu = spla.splu(sp.bmat([[net.tangent(X0).tocsc(), C.T], [C, None]]).tocsc())
    rows = (3 * itm[:, None] + np.arange(3)).ravel()
    G = np.zeros((n, len(rows)))
    for s in range(0, len(rows), BLOCK):
        r = rows[s:s + BLOCK]; F = np.zeros((n + 6, len(r))); F[r, np.arange(len(r))] = 1.0
        G[:, s:s + len(r)] = lu.solve(F)[:n]
    rank = []
    for i in range(N):
        Gi = G[3 * i:3 * i + 3].T
        f = np.linalg.lstsq(Gi, D, rcond=None)[0]
        rank.append((float(np.linalg.norm(D - Gi @ f)), i, f))
    rank.sort(key=lambda x: x[0])
    res = []
    for _, i, f in rank[:N_TOP]:
        Xi = P0[tm] + (G[3 * i:3 * i + 3].T @ f).reshape(-1, 3)
        r, o = _rmsd_ovl(Xi, XE[tm], P0[tm]); res.append((int(i), float(r), float(o)))
    res.sort(key=lambda x: x[1])
    i, r, o = res[0]
    out[name] = dict(closed_tm=float(_rmsd_ovl(P0[tm], XE[tm], P0[tm])[0]), prs_best_tm=r, prs_ovl=o, prs_node=i,
                     prs_node_is_membrane=bool(np.isin(i, M['mem'])), n_tm=int(tm.sum()), rc=RC,
                     time_s=time.time() - T0)
    json.dump(out, open(outf, 'w'), indent=1)
    print(name, json.dumps(out[name]), flush=True)
