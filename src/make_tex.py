"""Write every number and table quoted in the manuscript from results/ (run after analyze.py).

usage: python make_tex.py [OUTDIR=../paper_tex/generated]
writes: numbers.tex (\\V{key} macros), tab_panel.tex, tab_ver.tex, tab_val.tex, tab_nl.tex, tab_phys.tex, numbers.json
Every \\V{key} used in manuscript.tex must be defined here; check_keys() fails otherwise.
"""
import sys, os, json, re
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from paths import DERIVED, TEX_GEN
RES = str(DERIVED)
sys.path.insert(0, HERE)
from model import model, build_target, kabsch, PANEL, EXTRA, LABEL
OUT = sys.argv[1] if len(sys.argv) > 1 else str(TEX_GEN)
os.makedirs(OUT, exist_ok=True)
S = json.load(open(f'{RES}/summary.json'))
R = S['runs']; L = S['load_check']; N = S['nulls']; I = S['indicator']; P = S['physical_scale']; VF = S['vfife_checks']
V = {}


def f(x, d=2):
    return f'{x:.{d}f}'


def sci(x, d=1):
    m, e = f'{x:.{d}e}'.split('e'); return f'{m}\\times10^{{{int(e)}}}'


def val(p, rc=10):
    return R[f'{p}_rc{rc}']['validation']


small = [p for p in PANEL]
# ---------------------------------------------------------------- verification
vf = {p: VF.get(f'vfife_{p}_rc10', []) for p in PANEL + EXTRA}
snapped = [r for v in vf.values() for r in v if r['maxdev'] > 1e-3]          # increment ending exactly at the limit point
V['vf-max'] = '$' + sci(max(r['maxdev'] for v in vf.values() for r in v if r['maxdev'] <= 1e-3)) + '$'
V['vf-piezo'] = '$' + sci(max(r['maxdev'] for r in vf['6b3r'] if r['maxdev'] <= 1e-3)) + '$'
V['vf-snap'] = f(snapped[0]['maxdev'], 1) if snapped else '--'
V['n-vf'] = str(sum(len(v) for v in vf.values()))
V['area-err'] = '$' + sci(max(L[p]['area_operator_vs_direct']['raw_max'] for p in L)) + '$'
V['fd-err'] = '$' + sci(max(L[p]['grad_fd_rel_max'] for p in L)) + '$'
V['we-order'] = f(S['vfife_checks']['work_2oar_rc10']['observed_order'][-1], 2)
V['rot-max'] = sci(max(R[f'{p}_rc10']['rigid_rotation_max_deg'] for p in PANEL), 0) if max(R[f'{p}_rc10']['rigid_rotation_max_deg'] for p in PANEL) < 0.01 else f(max(R[f'{p}_rc10']['rigid_rotation_max_deg'] for p in PANEL), 2)
V['rot-max'] = '$' + V['rot-max'] + '$'
mxy = [L[p]['resultants_x0']['raw']['Mxy'] for p in PANEL]
V['mxy-min'] = '$' + sci(min(mxy)) + '$'; V['mxy-max'] = '$' + sci(max(mxy)) + '$'
nl_ = [R[f'{p}_rc10']['n_loaded'] for p in PANEL]; V['nload-min'] = str(min(nl_)); V['nload-max'] = str(max(nl_))
# ---------------------------------------------------------------- gauge
sym_r = [L[p]['gauge_symmetry']['reaction_rel'] for p in PANEL]
V['sym-react-max'] = '$' + sci(max(sym_r)) + '$'
rho = [L[p]['gauge_raw']['eckart_reaction_rel'] for p in PANEL]; V['rho-min'] = '$' + sci(min(rho)) + '$'; V['rho-max'] = '$' + sci(max(rho)) + '$'
sym = [L[p]['gauge_symmetry']['rmsd_vs_eckart6'] for p in PANEL]; V['sym-min'] = f(min(sym), 3); V['sym-max'] = f(max(sym), 2)
V['tilt-max'] = f(max(L[p]['gauge_symmetry']['tilt_deg'] for p in PANEL), 1)
V['sym-metric-max'] = f(max(L[p]['gauge_symmetry'].get('metric_shift_tm', 0) for p in PANEL), 3)
ar = [L[p]['gauge_raw']['anchor_reaction_rel'] for p in PANEL]; V['anchreac-min'] = '$' + sci(min(ar)) + '$'; V['anchreac-max'] = f(max(ar), 2)
an = [L[p]['gauge_raw']['rmsd_anchored_vs_eckart'] for p in PANEL]; V['anch-min'] = f(min(an), 2); V['anch-max'] = f(max(an), 1)
V['anch-metric-max'] = f(max(L[p]['gauge_raw'].get('metric_shift_tm', 0) for p in PANEL), 2)
lr = [L[p]['gauge_raw']['lambda_eckart'] / L[p]['gauge_raw']['lambda_anchored'] for p in PANEL]
V['lamratio-anch-min'] = f(min(lr), 0); V['lamratio-anch-max'] = f(max(lr), 0)
eqr = [L[p]['gauge_eq']['eckart_reaction_rel'] for p in L]; V['eq-rho-min'] = '$' + sci(min(eqr)) + '$'; V['eq-rho-max'] = '$' + sci(max(eqr)) + '$'
V['eq-worse'] = str(sum(L[p]['gauge_eq']['rmsd_anchored_vs_eckart'] > L[p]['gauge_raw']['rmsd_anchored_vs_eckart'] + 0.01 for p in L))
V['n-gauge-struct'] = str(len(L))
# ---------------------------------------------------------------- stability
n_in = sum(R[k]['n_inertia'] for k in R if R[k]['n_inertia'] and not k.endswith('rc8'))
V['n-inertia'] = f'{n_in:,}'.replace(',', '\\,')
lam_r = {p: R[f'{p}_rc10']['lam_ratio'] for p in PANEL}
five = [lam_r[p] for p in PANEL if p not in ('6pwn', '6b3r')]
pzr = json.load(open(f'{RES}/paths/6b3r_rc10.json'))['rows'][:R['6b3r_rc10']['step_star']]
V['piezo-lam-peak'] = f(max(r['lam'][0] for r in pzr if r.get('lam')) / R['6b3r_rc10']['lam0'], 1)
V['lamratio-min'] = f(min(five), 1); V['lamratio-max'] = f(max(five), 1)
V['mscs-lam-change'] = f(abs(lam_r['6pwn'] - 1) * 100, 0)
V['mech-piezo'] = str(R['6b3r_rc8']['mechanisms_x0']); V['mech-traak'] = str(R['4wff_rc8']['mechanisms_x0']); V['mech-osca'] = str(R['6mgv_rc8']['mechanisms_x0'])
# which element limits first: backbone?
bbfirst = 0
for p in PANEL:
    r = R[f'{p}_rc10']
    if abs(r['max_e_bb_star'] - max(r['max_e_bb_star'], 0)) < 1e-12:
        pass
for p in PANEL:
    run = json.load(open(f'{RES}/paths/{p}_rc10.json'))
    k = R[f'{p}_rc10']['step_star']; row = run['rows'][min(k, len(run['rows']) - 1)]
    bbfirst += int(row['max_e_bb'] >= row['max_e_nonbb'])
V['n-bb-lead'] = ['none', 'one', 'two', 'three', 'four', 'five', 'six'][bbfirst]
# ---------------------------------------------------------------- validation
apps = [p for p in PANEL if val(p)['approach']]
V['n-approach'] = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six'}[len(apps)]
V['approach-list'] = ', '.join(LABEL[p] for p in apps)
for p, k in (('6pwn', 'mscs'), ('2oar', 'mscl'), ('6b3r', 'piezo'), ('4xdk', 'trek')):
    v = val(p); V[f'{k}-gain'] = f(100 * v['gain_nl'], 0); V[f'{k}-nl'] = f(v['nl']); V[f'{k}-closed'] = f(v['closed'])
V['trek-red'] = f(val('4xdk')['closed'] - val('4xdk')['nl'], 2)
V['traak-closed'] = f(val('4wff')['closed'])
V['mscl-dil'] = f(N['2oar']['dilation']['best_tm'])
rew = lambda p: [r['best_tm'] for r in N[p].get('rewired', []) if 'best_tm' in r]
V['mscs-rew-gap'] = f(min(rew('6pwn')) - val('6pwn')['nl'], 2); V['trek-rew-gap'] = f(min(rew('4xdk')) - val('4xdk')['nl'], 2)
V['rewire-frac'] = f(100 * np.mean([r['frac_changed'] for p in N for r in N[p].get('rewired', [])]), 0)
pz = val('6b3r')
V['piezo-nl'] = f(pz['nl']); V['piezo-lin'] = f(pz['lin']); V['piezo-closed'] = f(pz['closed'])
V['piezo-ovl-nl'] = f(pz['ovl_nl']); V['piezo-ovl-lin'] = f(pz['ovl_lin']); V['piezo-whole-nl'] = f(pz['whole_nl']); V['piezo-whole-lin'] = f(pz['whole_lin'])
V['piezo-linsame'] = f(pz['lin_same_tau']); V['piezo-epsbest'] = '$\\eps=' + f(pz['eps_best'], 3) + '$'
V['piezo-dil'] = f(N['6b3r']['dilation']['best_tm']) if '6b3r' in N else '??'
if '6b3r' in N and rew('6b3r'):
    V['piezo-rew-min'] = f(min(rew('6b3r'))); V['piezo-rew-max'] = f(max(rew('6b3r')))
    rw_ = [r for r in N['6b3r']['rewired'] if 'best_tm' in r]
    V['piezo-rewlin-min'] = f(min(r['linear_best_tm'] for r in rw_)); V['piezo-rewlin-max'] = f(max(r['linear_best_tm'] for r in rw_))
    dl = [r['linear_best_tm'] - r['best_tm'] for r in rw_]
    V['piezo-rewd-min'] = f(min(dl), 2); V['piezo-rewd-max'] = f(max(dl), 2)
    V['piezo-dil-gap'] = f(N['6b3r']['dilation']['best_tm'] - pz['nl'], 2)
    V['piezo-dil-ovl'] = f(N['6b3r']['dilation']['ovl'])
V['mscl-seqid'] = f(100 * json.load(open(f'{RES}/paths/2oar_rc10.json'))['pre']['target']['seq_identity'], 0)
# Piezo1 shape descriptors at the best frame
M = model('6b3r', 10.0); idx, P0, XE, Delta, info = build_target('6b3r', M); tm = np.isin(idx, M['mem']); c = M['m']['centroid']
run = json.load(open(f'{RES}/paths/6b3r_rc10.json')); Xs = np.load(f'{RES}/paths/6b3r_rc10_Xs.npy')
kb = int(np.argmin([abs(r['eps'] - pz['eps_best']) + abs(r['nl']['rmsd_tm'] - pz['nl']) for r in run['rows']]))
Xb = Xs[kb][idx]
def desc(Y):
    Rk, t = kabsch(Y[tm], P0[tm]); Y = Y @ Rk.T + t
    return np.linalg.norm(Y[tm, :2] - c[:2], axis=1).mean(), np.sqrt(((Y[:, 2] - Y[:, 2].mean()) ** 2).mean())
r0, z0 = desc(P0); rm, zm_ = desc(Xb); re_, ze = desc(XE)
V['piezo-r-frac'] = f(100 * (rm - r0) / (re_ - r0), 0); V['piezo-z-frac'] = f(100 * (zm_ - z0) / (ze - z0), 0)
V['piezo-r'] = f'{r0:.1f}\\,$\\to$\\,{rm:.1f}\\,\\AA{{}} (8IXO {re_:.1f}\\,\\AA)'
V['piezo-dA-best'] = f(pz['dA_best'] / 100, 1); V['piezo-dA-exp'] = f(P['6b3r']['dA_exp_nm2'], 1)
# ---------------------------------------------------------------- limit point
lc = json.load(open(f'{RES}/paths/6b3r_rc10_loadcontrol.json'))
V['piezo-lc-eps'] = f(lc['rows'][-1]['eps'], 3)
A = json.load(open(f'{RES}/paths/6b3r_rc10_arclength.json')); pts = A['points']
dl = np.array([q['dlam_ds'] for q in pts]); folds = [i for i in range(1, len(dl)) if np.sign(dl[i]) != np.sign(dl[i - 1])]
i1 = folds[0]; k1 = i1 if pts[i1]['tau'] >= pts[i1 - 1]['tau'] else i1 - 1
V['piezo-tauc'] = f(max(q['tau'] for q in pts[:i1 + 1]), 4); V['piezo-epsc'] = f(pts[k1]['eps'], 3)
if len(folds) > 1:
    i2 = folds[1]; V['piezo-tauc2'] = f(pts[i2]['tau'], 4); V['piezo-epsc2'] = f(pts[i2]['eps'], 3)
V['n-folds'] = str(len(folds))
pre_rows = [q for q in pts[:k1 + 1]]
e_ = np.array([q['eps'] for q in pre_rows]); me = np.array([q['max_e'] for q in pre_rows])
j0 = int(np.searchsorted(e_, pts[k1]['eps'] - 0.004))
V['piezo-maxe-pre'] = f(me[j0], 2); V['piezo-maxe-post'] = f(me[-1], 2)
snapf = f'{RES}/paths/6b3r_rc10_snap.json'
if os.path.exists(snapf):
    SN = json.load(open(snapf)); top = SN['snap_top_elements'][:10]; po = SN['post_snap']; pr_ = SN['pre_snap']
    V['snap-cmp'] = (f"is stable ($n_{{\\mathrm{{neg}}}}=0$ by the inertia count) and lies at $\\eps=${po['eps']:.3f}; the snap lowers the largest strain "
                     f"from {pr_['max_e']:.2f} to {po['max_e']:.2f}, moves no node by more than {SN['snap_max_node_displacement']:.1f}\\,\\AA{{}} and changes the TM RMSD "
                     f"from {pr_['nl']['rmsd_tm']:.2f} to {po['nl']['rmsd_tm']:.2f}\\,\\AA")
    chains = sorted({q[k][0] for q in top for k in ('i', 'j')}); res = [q[k][1] for q in top for k in ('i', 'j')]
    nbb = sum(q['backbone'] for q in top)
    V['piezo-snap-elems'] = (f"residues {min(res)}--{max(res)} of {'one subunit (chain ' + chains[0] + ')' if len(chains) == 1 else 'chains ' + ', '.join(chains)}, "
                             f"which carry all ten elements whose strain changes most in the snap ({nbb} of them backbone bonds)")
    V['snap-steps'] = f"{SN['vfife_steps']:,}".replace(',', '\\,')
# ---------------------------------------------------------------- nonlinearity measures
for p, k in (('6b3r', 'piezo'),):
    q = R[f'{p}_rc10']['enl_mem_0.10']; V[f'amp-{k}10'] = f(q['amp'], 2); V[f'enl-{k}10'] = f(q['E_NL'], 2); V[f'dir-{k}10'] = f(q['dir'], 2)
dirs = [R[f'{p}_rc10']['enl_mem_0.10']['dir'] for p in PANEL if p != '6b3r' and R[f'{p}_rc10'].get('enl_mem_0.10')]
V['dir-min10'] = f(min(dirs), 2); V['dir-max10'] = f(max(dirs), 2)
V['dir-cq8-10'] = f(R['6cq8_rc10']['enl_mem_0.10']['dir'], 2); V['dir-vtk-10'] = f(R['6vtk_rc10']['enl_mem_0.10']['dir'], 2)
chi = {p: I[p]['mem_eps0.10']['chi'] for p in PANEL + EXTRA}
V['chi-piezo'] = f(chi['6b3r'], 2); oth = [chi[p] for p in PANEL if p != '6b3r']; V['chi-min'] = f(min(oth), 2); V['chi-max'] = f(max(oth), 2)
V['chi-cq8'] = f(chi['6cq8'], 2); V['chi-vtk'] = f(chi['6vtk'], 2)
from scipy.stats import spearmanr
meas = [R[f'{p}_rc10']['enl_mem_0.05']['dir'] for p in PANEL + EXTRA]; pred = [I[p]['mem_eps0.05']['chi'] for p in PANEL + EXTRA]
rs = spearmanr(pred, meas); V['chi-rank'] = f(rs.correlation, 2); V['chi-rank-n'] = str(len(meas))
# stiffening: amplitude ratio and its second-order prediction (membrane nodes)
ALL8 = PANEL + EXTRA
a05 = {p: R[f'{p}_rc10']['enl_mem_0.05']['amp'] for p in ALL8}; k05 = {p: I[p]['mem_eps0.05']['kappa'] for p in ALL8}
V['n-stiff'] = {8: 'all eight'}.get(sum(a05[p] > 1 for p in ALL8), str(sum(a05[p] > 1 for p in ALL8)))
V['n-kappa-neg'] = {8: 'all eight'}.get(sum(k05[p] < 0 for p in ALL8), str(sum(k05[p] < 0 for p in ALL8)))
dev = [abs(1 / (1 + k05[p]) / a05[p] - 1) for p in PANEL]; V['kappa-dev-max'] = f(100 * max(dev), 0)
ok = [p for p in ALL8 if k05[p] > -1]; V['kappa-rank'] = f(spearmanr([a05[p] for p in ok], [1 / (1 + k05[p]) for p in ok]).correlation, 2); V['kappa-rank-n'] = str(len(ok))
V['kappa-cq8'] = f(k05['6cq8'], 2)
amps10 = [R[f'{p}_rc10']['enl_mem_0.10']['amp'] for p in PANEL if p != '6b3r']; V['amp-min10'] = f(min(amps10), 2); V['amp-max10'] = f(max(amps10), 2)
# snapping: only Piezo1 loses stability; the others stay certified stable to the end of their computed paths
stab = [p for p in ALL8 if R[f'{p}_rc10']['n_neg_max'] == 0 and R[f'{p}_rc10']['limit'] != 'limit point']
V['n-stable'] = {7: 'seven'}.get(len(stab), str(len(stab)))
ee = [R[f'{p}_rc10']['eps_end'] for p in stab]; V['stable-eps-min'] = f(min(ee), 2); V['stable-eps-max'] = f(max(ee), 2)
V['piezo12-stall'] = f(R['6b3r_rc12']['eps_end'], 3); V['piezo12-epsstar'] = f(R['6b3r_rc12']['eps_star'], 3)
V['chi-abs'] = f'{np.median(np.array(pred) / np.array(meas)):.2f}'
# ---------------------------------------------------------------- robustness
VR = S['variants']
pv = [v['delta'] for k, v in VR.items() if k.startswith('6b3r_rc10_') and 'kbb' not in k and 'loadcontrol' not in k]
V['piezo-var-min'] = f(min(pv)); V['piezo-var-max'] = f(max(pv)); V['n-var'] = str(len(pv))
V['piezo-rc12-delta'] = f(val('6b3r', 12)['delta'])
for kb_ in (10, 100):
    v = VR.get(f'6b3r_rc10_kbb{kb_}')
    if v:
        V[f'piezo-kbb{kb_}-delta'] = f(v['delta'])
        rr = json.load(open(f'{RES}/paths/6b3r_rc10_kbb{kb_}.json'))['rows']
        b = min([r for r in rr if r['eps'] <= v['eps_star'] + 1e-12], key=lambda r: r['nl']['rmsd_tm'])
        V[f'piezo-kbb{kb_}-bb'] = f(100 * b['max_e_bb'], 1)
bbv = S['thresholds']['6b3r']['backbone_0.05']; V['piezo-bb-epsstar'] = f(bbv['eps_star'], 3)
V['piezo-thr-all'] = str(all(S['thresholds']['6b3r'][k]['cls'] == 'NL better' for k in S['thresholds']['6b3r'] if k not in ('margins', 'backbone_0.05')))
mv = [v['delta'] for k, v in VR.items() if k.startswith('6pwn_rc10_') and 'kbb' not in k]
V['mscs-var-min'] = f(min(mv)); V['mscs-var-max'] = f(max(mv)); V['mscs-rc12-delta'] = f(val('6pwn', 12)['delta'])
# ---------------------------------------------------------------- physical scale
xr = [p for p in PANEL if P[p]['method'] == 'X-ray']
g = [P[p]['gamma_trace_pN_per_A'] for p in xr]; gmin, gmax = min(g), max(g)
V['gamma-min'] = f(gmin, 0); V['gamma-max'] = f(gmax, 0)
bc = [P[p]['bfactor_corr'] for p in xr]; V['bcorr-min'] = f(min(bc), 2); V['bcorr-max'] = f(max(bc), 2)
def tp(t):
    lo, hi = 10 * gmin * t, 10 * gmax * t
    g = lambda x: f'{x:.1f}' if x < 9.95 else f'{x:.0f}'
    return f'{g(lo)}--{g(hi)}'
V['piezo-tphys-best'] = tp(pz['tau_best']); V['piezo-tphys-c'] = tp(float(V['piezo-tauc']))
V['mscs-tphys-best'] = tp(val('6pwn')['tau_best']); V['mscl-tphys-best'] = tp(val('2oar')['tau_best'])
ept = {p: R[f'{p}_rc10']['eps_per_tau'] for p in PANEL}
V['piezo-ept'] = f(ept['6b3r'], 1); o = [ept[p] for p in PANEL if p not in ('6b3r', '6mgv')]; V['ept-min'] = f(min(o), 2); V['ept-max'] = f(max(o), 2)

# ================================================================ tables
PART = {'6b3r': ('Piezo1 (mouse)', '6B3R', 'EM', '8IXO', 'S2472E, intermediate open (EM)', 'guo2017,liu2025'),
        '6pwn': ('MscS (\\textit{E.\\,coli})', '6PWN', 'EM, nanodisc', '2VV5', 'A106V, open (X-ray)', 'reddy2019,wang2008'),
        '2oar': ('MscL (\\textit{M.\\,tb})', '2OAR', 'X-ray', '4Y7K$\\to$4Y7J', 'homologue, expanded (X-ray)', 'steinbacher2007,li2015'),
        '4xdk': ('TREK-2 (human)', '4XDK', 'X-ray, norfluoxetine', '4BW5', 'TM4 up (X-ray)', 'dong2015,dong2015'),
        '4wff': ('TRAAK (human)', '4WFF', 'X-ray', '4WFE', 'K$^+$-bound, conductive (X-ray)', 'brohawn2014,brohawn2014'),
        '6mgv': ('OSCA1.2 (\\textit{A.\\,thaliana})', '6MGV', 'EM', '8XAJ', 'open, liposome (EM)', 'jojoacruz2018,han2024')}
T = ['\\begin{table}[t]', '\\centering\\small',
     '\\caption{Channel panel. $N$, $E$: nodes and elements at $r_c=10$\\,\\AA; $N_{\\mathrm{TM}}$: mapped transmembrane C$\\alpha$ used for validation; $N_{\\mathrm{load}}$: loaded outer-shell nodes.}',
     '\\label{tab:panel}', '\\footnotesize\\setlength{\\tabcolsep}{3pt}', '\\begin{tabular}{@{}l>{\\raggedright\\arraybackslash}p{2.45cm}l>{\\raggedright\\arraybackslash}p{2.7cm}rrrr@{}}', '\\toprule',
     'Channel & Closed & Partner & Partner state & $N$ & $E$ & $N_{\\mathrm{TM}}$ & $N_{\\mathrm{load}}$\\\\', '\\midrule']
for p in PANEL:
    a, b, m, c_, s_, ref = PART[p]; r = R[f'{p}_rc10']; refs = ref.split(',')
    cite2 = ('~\\citep{' + refs[-1] + '}') if len(refs) > 1 else ''
    T.append(f"{a} & {b}~\\citep{{{refs[0]}}} ({m}) & {c_}{cite2} & {s_} & {r['N']} & {r['E']} & {val(p)['n_tm']} & {r['n_loaded']}\\\\")
T[2] = T[2].replace('loaded outer-shell nodes.}', 'loaded outer-shell nodes; EM: cryo-electron microscopy.}')
T += ['\\bottomrule', '\\end{tabular}', '\\end{table}']
open(f'{OUT}/tab_panel.tex', 'w').write('\n'.join(T) + '\n')

LIM = {'max strain': '$|e|_{\\max}$', 'P20': '$P_{20}$', 'eps>=0.4': 'end of range', 'newton stalled': 'solver stall', 'limit point': 'limit point', 'negative eigenvalue': 'loss of stability'}
T = ['\\begin{table}[t]', '\\centering\\small',
     '\\caption{Verification, gauge and stability ($r_c=10$\\,\\AA). $\\delta_{\\mathrm{VF}}$: largest VFIFE--Newton nodal deviation over the restarted increments (number in brackets). $M_{xy}$: tilting moment of the load at $\\x_0$. $\\rho$: Eckart reaction/load at $\\eps^*$. $\\delta_{\\mathrm{sym}}$, $\\delta_{\\mathrm{anch}}$: RMSD of the tilt-free and anchored solutions from the Eckart solution. $\\lambda_1(\\eps^*)/\\lambda_1(0)$: lowest constrained eigenvalue; $n_{\\mathrm{neg}}=0$ at every step by the inertia count. Last column: condition that ends the validity range.}',
     '\\label{tab:ver}', '\\setlength{\\tabcolsep}{3pt}\\resizebox{\\textwidth}{!}{%', '\\begin{tabular}{lcccccccl}', '\\toprule',
     'Channel & $\\delta_{\\mathrm{VF}}$ (\\AA) & $M_{xy}$ & $\\rho$ & $\\delta_{\\mathrm{sym}}$ (\\AA) & $\\delta_{\\mathrm{anch}}$ (\\AA) & $\\lambda_1(\\eps^*)/\\lambda_1(0)$ & $\\eps^*$ & ended by\\\\', '\\midrule']
for p in PANEL:
    r = R[f'{p}_rc10']; lc_ = L[p]
    lim = LIM.get(r['limit'], r['limit'])
    T.append(f"{LABEL[p]} & ${sci(max(x['maxdev'] for x in vf[p] if x['maxdev'] <= 1e-3))}$ ({len([x for x in vf[p] if x['maxdev'] <= 1e-3])}) & ${sci(lc_['resultants_x0']['raw']['Mxy'])}$ & ${sci(r['gauge_reaction_max'])}$ & "
             f"{lc_['gauge_symmetry']['rmsd_vs_eckart6']:.3f} & {lc_['gauge_raw']['rmsd_anchored_vs_eckart']:.2f} & {r['lam_ratio']:.2f}{'$^a$' if r['limit'] == 'limit point' else ''} & {r['eps_star']:.3f} & {lim}\\\\")
T += ['\\bottomrule', '\\multicolumn{9}{l}{\\footnotesize $^a$At the limit point the eigenvalue tends to zero; maximum along the stable branch ' + V['piezo-lam-peak'] + '.}', '\\end{tabular}}', '\\end{table}']
open(f'{OUT}/tab_ver.tex', 'w').write('\n'.join(T) + '\n')

T = ['\\begin{table}[t]', '\\centering\\small',
     '\\caption{Validation (TM subset, $r_c=10$\\,\\AA; RMSD in \\AA). NL: best frame of the nonlinear path within $\\eps\\le\\eps^*$ (at $\\eps$). Linear: best-amplitude linear response, unrestricted [restricted to $\\eps\\le\\eps^*$]; same $\\tau$: linear response at the tension of the NL frame. Dilation, rewired (best of three), ANM$_{10}$: null models of Section~\\ref{sec:nulls}. Class: NL vs.\\ unrestricted linear with margin $\\max(0.2\\,\\text{\\AA},3\\%)$; $\\checkmark$: approaches the partner.}',
     '\\label{tab:val}', '\\setlength{\\tabcolsep}{2.6pt}\\resizebox{\\textwidth}{!}{%', '\\begin{tabular}{lccccccccccl}', '\\toprule',
     'Channel & closed & NL & $\\eps$ & linear & same $\\tau$ & ovl NL/L & dilation & rewired & ANM$_{10}$ & whole: closed$\\to$NL & class\\\\', '\\midrule']
for p in PANEL:
    v = val(p); n = N.get(p, {}); rw = rew(p) if p in N else []
    nlt = ('\\textbf{' + f(v['nl']) + '}') if v['cls'] == 'NL better' else f(v['nl'])
    nulls_ = f"{n['dilation']['best_tm']:.2f} & {min(rw):.2f} & {n['anm_10']['best_tm']:.2f}" if (n and rw) else '-- & -- & --'
    tick = ' $\\checkmark$' if v['approach'] else ''
    T.append(f"{LABEL[p]} & {v['closed']:.2f} & {nlt} & {v['eps_best']:.3f} & {v['lin']:.2f} [{v['lin_restricted']:.2f}] & {v['lin_same_tau']:.2f} & "
             f"{v['ovl_nl']:.2f}/{v['ovl_lin']:.2f} & {nulls_} & {v['whole_closed']:.2f}$\\to${v['whole_nl']:.2f} & {v['cls']}{tick}\\\\")
T += ['\\bottomrule', '\\end{tabular}}', '\\end{table}']
open(f'{OUT}/tab_val.tex', 'w').write('\n'.join(T) + '\n')

T = ['\\begin{table}[t]', '\\centering\\small',
     '\\caption{Measures of nonlinearity on the membrane nodes. $a$: amplitude ratio $\\|\\mathbf{u}_L\\|/\\|\\mathbf{u}_{NL}\\|$; $\\sin\\theta$: direction error; $E_{NL}$: linearization error, Eq.~\\eqref{eq:enl}, at $\\eps=0.10$. $\\chi$, $\\kappa$: a-priori second-order indicators at the tension for which the linear response reaches $\\eps=0.10$. $\\Delta_{L-NL}$: advantage of the NL path over the best-amplitude linear response (\\AA) at $r_c=10$ and 12\\,\\AA.}',
     '\\label{tab:nl}', '\\setlength{\\tabcolsep}{4pt}', '\\begin{tabular}{lccccccc}', '\\toprule',
     'Structure & $a$ & $\\sin\\theta$ & $E_{NL}$ & $\\chi$ & $\\kappa$ & $\\Delta_{L-NL}^{10}$ & $\\Delta_{L-NL}^{12}$\\\\', '\\midrule']
for p in PANEL + EXTRA:
    q = R[f'{p}_rc10'].get('enl_mem_0.10'); ii = I[p]['mem_eps0.10']
    d10 = f(val(p)['delta']) if R[f'{p}_rc10']['validation'] else '--'
    d12 = f(val(p, 12)['delta']) if f'{p}_rc12' in R and R[f'{p}_rc12']['validation'] else '--'
    T.append(f"{LABEL[p]} & {q['amp']:.2f} & {q['dir']:.2f} & {q['E_NL']:.2f} & {ii['chi']:.2f} & {ii['kappa']:.2f} & {d10} & {d12}\\\\" if q else
             f"{LABEL[p]} & -- & -- & -- & {ii['chi']:.2f} & {ii['kappa']:.2f} & {d10} & {d12}\\\\")
T += ['\\bottomrule', '\\end{tabular}', '\\end{table}']
open(f'{OUT}/tab_nl.tex', 'w').write('\n'.join(T) + '\n')

T = ['\\begin{table}[!h]', '\\centering\\small',
     f'\\caption{{Physical scale. $\\gamma$: spring constant from B-factors (trace estimate; node median in brackets), with correlation between predicted and measured B-factors. $A_0$: outer-shell area of the closed structure; $\\Delta A$: change at the best NL frame and between the closed and partner structures, same operator. $\\tau_{{\\mathrm{{phys}}}}$: tension at the best frame for $\\gamma$ = {gmin:.0f}--{gmax:.0f}\\,pN\\,\\AA$^{{-1}}$ (crystal-structure range).}}',
     '\\label{tab:phys}', '\\setlength{\\tabcolsep}{4pt}', '\\begin{tabular}{llcccccc}', '\\toprule',
     'Channel & B-factors & $\\gamma$ (pN\\,\\AA$^{-1}$) & corr. & $A_0$ (nm$^2$) & $\\Delta A_{\\mathrm{model}}$ & $\\Delta A_{\\mathrm{exp}}$ & $\\tau_{\\mathrm{phys}}$ (mN\\,m$^{-1}$)\\\\', '\\midrule']
for p in PANEL:
    q = P[p]; v = val(p)
    T.append(f"{LABEL[p]} & {q['method']} & {q['gamma_trace_pN_per_A']:.0f} [{q['gamma_node_median']:.0f}] & {q['bfactor_corr']:.2f} & {q['A0_nm2']:.1f} & {v['dA_best'] / 100:.1f} & {q['dA_exp_nm2']:.1f} & {tp(v['tau_best'])}\\\\")
T += ['\\bottomrule', '\\end{tabular}', '\\end{table}']
open(f'{OUT}/tab_phys.tex', 'w').write('\n'.join(T) + '\n')

# ================================================================ numbers.tex
lines = ['% generated by code/make_tex.py from code/results -- do not edit',
         '\\makeatletter', '\\newcommand{\\V}[1]{\\@ifundefined{v@#1}{\\textbf{??#1??}}{\\@nameuse{v@#1}}}']
for k, v in sorted(V.items()):
    lines.append(f'\\@namedef{{v@{k}}}{{{v}}}')
lines.append('\\makeatother')
open(f'{OUT}/numbers.tex', 'w').write('\n'.join(lines) + '\n')
json.dump(V, open(f'{OUT}/numbers.json', 'w'), indent=1)


def check_keys():
    tex = open(os.path.join(OUT, '..', 'main.tex')).read()
    used = set(re.findall(r'\\V\{([^}]+)\}', tex)); miss = sorted(used - set(V))
    print('keys used', len(used), 'defined', len(V), 'missing', miss)
    return miss


if __name__ == '__main__':
    miss = check_keys()
    for k in ('n-approach', 'approach-list', 'piezo-nl', 'piezo-lin', 'piezo-tauc', 'piezo-epsc', 'chi-piezo', 'chi-min', 'chi-max', 'chi-rank'):
        print(k, '=', V.get(k))
