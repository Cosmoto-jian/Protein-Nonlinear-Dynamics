"""Post-processing of the r5 runs into results/summary.json (all numbers quoted in the manuscript come from here).

Definitions
  valid(row)   : P20 <= p20_thr and |e|_max <= emax_thr  (default 5 %, 0.5); optional backbone limit |e|_bb <= bb_thr
  eps*         : eps of the last row of the initial contiguous valid sequence; 'limit' records what ends it
                 (first invalid row: 'P20' / 'max strain' / 'backbone'; otherwise the run stop reason)
  NL best      : min TM-RMSD over valid rows;  linear best: min over the amplitude grid (unrestricted, and with
                 eps <= eps*);  class: NL vs unrestricted linear with margin max(m, 3 % of linear), m = 0.2 A
  approach     : closed - NL > max(m, 5 % of closed) and TM overlap > 0.3
usage: python analyze.py
"""
import sys, os, json, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from paths import DERIVED, TEX_GEN
RES = str(DERIVED)
sys.path.insert(0, HERE)
from model import LABEL, PANEL, EXTRA


def load(tag):
    f = f'{RES}/paths/{tag}.json'
    return json.load(open(f)) if os.path.exists(f) else None


def eps_star(R, p20=0.05, emax=0.5, bb=None):
    rows = R['rows']; last = None; limit = None
    for r in rows:
        bad = []
        if r['p20'] > p20: bad.append('P20')
        if r['max_e'] > emax: bad.append('max strain')
        if bb is not None and r['max_e_bb'] > bb: bad.append('backbone')
        if 'inertia' in r and r['inertia']['n_neg'] > 0:
            limit = 'limit point' if r.get('continuation') else 'negative eigenvalue'; break
        if bad:
            limit = '+'.join(bad); break
        last = r
    if limit is None:
        limit = R['stop']
    return (last['eps'] if last else 0.0), (last['step'] if last else 0), limit


def classify(nl, lin, m=0.2):
    mm = max(m, 0.03 * lin)
    return 'NL better' if lin - nl > mm else ('NL worse' if nl - lin > mm else 'equivalent')


def has_mechanism(R):
    return R['pre'].get('inertia0', {}).get('n_zero', 0) > 0


def validation(R, p20=0.05, emax=0.5, bb=None, m=0.2):
    t = R['pre']['target']
    if t is None or has_mechanism(R):
        return None
    es, ks, limit = eps_star(R, p20, emax, bb)
    rows = [r for r in R['rows'] if r['step'] <= ks]
    c0 = t['rmsd_closed_vs_target_tm']
    grid = t['linear_grid']
    lb = min(grid, key=lambda g: g['rmsd_tm'])
    lbr = min([g for g in grid if g['eps'] <= es + 1e-12] or [grid[0]], key=lambda g: g['rmsd_tm'])
    if rows:
        b = min(rows, key=lambda r: r['nl']['rmsd_tm'])
        nl, onl, eb, lin_same, whole = b['nl']['rmsd_tm'], b['nl']['ovl_tm'], b['eps'], b['lin']['rmsd_tm'], b['nl']['rmsd']
    else:
        nl, onl, eb, lin_same, whole = c0, 0.0, 0.0, c0, t['rmsd_closed_vs_target']
    return dict(closed=c0, nl=nl, ovl_nl=onl, eps_best=eb, eps_star=es, limit=limit, lin=lb['rmsd_tm'], ovl_lin=lb['ovl_tm'],
                eps_lin=lb['eps'], lin_restricted=lbr['rmsd_tm'], lin_same_tau=lin_same, whole_closed=t['rmsd_closed_vs_target'],
                whole_nl=whole, whole_lin=min(g['rmsd'] for g in grid), delta=lb['rmsd_tm'] - nl,
                cls=classify(nl, lb['rmsd_tm'], m),
                approach=bool(c0 - nl > max(m, 0.05 * c0) and onl > 0.3), gain_nl=(c0 - nl) / c0, gain_lin=(c0 - lb['rmsd_tm']) / c0,
                n_tm=t['n_tm_common'], label=t['label'])


def at_eps(R, e, key):
    rows = R['rows']; E = np.array([r['eps'] for r in rows])
    if len(E) == 0 or e > E.max() or e < E.min():
        return None
    i = int(np.searchsorted(E, e)); i = min(max(i, 1), len(E) - 1)
    w = (e - E[i - 1]) / (E[i] - E[i - 1])
    return {k: (1 - w) * rows[i - 1][key][k] + w * rows[i][key][k] for k in rows[i][key]}


S = dict(definitions=__doc__)
# ---- production runs
S['runs'] = {}
for p in PANEL + EXTRA:
    for rc in (8, 10, 12):
        R = load(f'{p}_rc{rc}')
        if R is None:
            continue
        es, ks, limit = eps_star(R)
        rows = R['rows']; valid_rows = [r for r in rows if r['step'] <= ks]
        inn = [r['inertia'] for r in valid_rows if 'inertia' in r]
        lam = [r['lam'][0] for r in valid_rows if r.get('lam')]
        rec = dict(N=R['pre']['N'], E=R['pre']['E'], n_bb=R['pre']['n_bb'], n_mem=R['pre']['n_mem'], n_loaded=R['pre']['n_loaded'],
                   n_steps=len(rows), stop=R['stop'], eps_end=rows[-1]['eps'] if rows else 0, eps_star=es, step_star=ks, limit=limit,
                   n_inertia=len(inn), n_neg_max=max([q['n_neg'] for q in inn] + [R['pre'].get('inertia0', {}).get('n_neg', 0)]) if inn else None,
                   n_zero_max=max(q['n_zero'] for q in inn) if inn else None,
                   lam0=R['pre']['lam0'][0] if R['pre'].get('lam0') else None, lam_min=min(lam) if lam else None,
                   lam_star=valid_rows[-1]['lam'][0] if valid_rows and valid_rows[-1].get('lam') else None,
                   lam_ratio=(valid_rows[-1]['lam'][0] / R['pre']['lam0'][0]) if valid_rows and valid_rows[-1].get('lam') and R['pre'].get('lam0') else None,
                   gauge_reaction_max=max([r['gauge_reaction_rel'] for r in valid_rows] or [0]),
                   rigid_rotation_max_deg=max([r['rigid_rotation_deg'] for r in valid_rows] or [0]),
                   work_energy_max=max([r['work_energy_rel'] for r in valid_rows[2:]] or [0]),
                   max_e_bb_star=valid_rows[-1]['max_e_bb'] if valid_rows else 0, eps_per_tau=R['pre']['eps_per_tau'],
                   tau_star=valid_rows[-1]['tau'] if valid_rows else 0, dA_star=valid_rows[-1]['dA'] if valid_rows else 0,
                   wall_s=R['wall_s'])
        rec['mechanisms_x0'] = R['pre'].get('inertia0', {}).get('n_zero', 0)
        rec['validation'] = validation(R)
        for e in (0.05, 0.10):
            rec[f'enl_all_{e:.2f}'] = at_eps(R, e, 'enl_all'); rec[f'enl_mem_{e:.2f}'] = at_eps(R, e, 'enl_mem')
        if valid_rows:
            rec['enl_all_star'] = valid_rows[-1]['enl_all']; rec['enl_mem_star'] = valid_rows[-1]['enl_mem']
            if rec['validation']:
                b = min(valid_rows, key=lambda r: r['nl']['rmsd_tm'])
                rec['validation']['dA_best'] = b['dA']; rec['validation']['tau_best'] = b['tau']
        S['runs'][f'{p}_rc{rc}'] = rec
# ---- cutoff robustness (margin 0.2 A), and threshold / margin sensitivity at rc 10
S['cutoff'] = {p: {rc: ((S['runs'].get(f'{p}_rc{rc}', {}).get('validation') or {}).get('cls')
                       or ('mechanism' if S['runs'].get(f'{p}_rc{rc}', {}).get('mechanisms_x0') else None)) for rc in (8, 10, 12)} for p in PANEL}
S['thresholds'] = {}
for p in PANEL:
    R = load(f'{p}_rc10')
    if R is None: continue
    S['thresholds'][p] = {f'{p20}_{em}': validation(R, p20=p20, emax=em) for p20 in (0.025, 0.05, 0.10) for em in (0.3, 0.5, 0.7)}
    S['thresholds'][p]['backbone_0.05'] = validation(R, bb=0.05)
    S['thresholds'][p]['margins'] = {f'{m:.2f}': validation(R, m=m)['cls'] for m in np.arange(0.1, 0.401, 0.05)}
# ---- variants (sensitivity runs)
S['variants'] = {}
for f in sorted(glob.glob(f'{RES}/paths/*_rc10_*.json')):
    tag = os.path.basename(f)[:-5]
    if tag.endswith('arclength'):
        continue
    R = json.load(open(f))
    if 'rows' not in R or 'pre' not in R:
        continue
    v = validation(R)
    if v: S['variants'][tag] = dict(v, options=R['pre']['options'], eps_per_tau=R['pre']['eps_per_tau'])
for k in ('load_check', 'indicator', 'nulls', 'vfife_checks', 'physical_scale'):
    f = f'{RES}/{k}.json'
    S[k] = json.load(open(f)) if os.path.exists(f) else None
f = f'{RES}/paths/6b3r_rc10_arclength.json'
if os.path.exists(f):
    A = json.load(open(f))
    S['arclength'] = dict(start_step=A['start_step'], n_points=len(A['points']), n_rejected=A['n_rejected'], stop=A['stop'],
                          dlam_ds_min=min(q['dlam_ds'] for q in A['points']), n_neg_max=max(q['inertia']['n_neg'] for q in A['points']),
                          n_zero_max=max(q['inertia']['n_zero'] for q in A['points']), eps_end=A['points'][-1]['eps'],
                          tau_monotone=bool(all(b['tau'] > a['tau'] for a, b in zip(A['points'], A['points'][1:]))))
else:
    S['arclength'] = None
json.dump(S, open(f'{RES}/summary.json', 'w'), indent=1, default=float)
for p in PANEL:
    v = S['runs'].get(f'{p}_rc10', {}).get('validation')
    if v:
        print(f"{LABEL[p]:8s} closed {v['closed']:.2f} NL {v['nl']:.2f}@{v['eps_best']:.3f} lin {v['lin']:.2f} [{v['lin_restricted']:.2f}] same-tau {v['lin_same_tau']:.2f} "
              f"eps* {v['eps_star']:.3f} ({v['limit']}) cls {v['cls']} approach {v['approach']}  cut {S['cutoff'][p]}")
