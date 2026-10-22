# Equivalence of the rebuilt pipeline with the legacy r6 results

Full chain `python run_all.py` (72 steps) rebuilt every derived file from `data/raw/`. Each output was compared field by field with the legacy r6 result
(table: `equivalence_table.tsv`; numeric fields, excluding wall-clock times).

## Path files (47)

| Group | Files | Largest difference |
|---|---|---|
| 2OAR, 4XDK, 6CQ8 (all cutoffs); 6B3R rc8 | 10 | bit-identical |
| 6PWN, 6MGV, 6VTK (all cutoffs); 6B3R rc10, rc12, load control, arclength; 20 variants | 33 | 9.8e-16 absolute (Lanczos eigenvalues) |
| 6B3R snap | 1 | 2.05e-12 absolute in U (1.6e-14 relative); tau_c, tau_s, limit-point index and VFIFE step count bit-identical; the Newton residual itself is 5.17e-13 vs 5.22e-13 |
| 4WFF rc10, rc12 | 2 | 5e-6 relative in RMSD_TM, eps, tau, U, A (input coordinates moved by up to 1.0e-3 A); the overlap at the eps = 0 grid point is undefined (zero displacement) and differs |
| 4WFF rc8 | 1 | network with 2 mechanisms; both runs stop with "newton stalled"; legacy kept one noise step (tau = -3e-10), the rebuild keeps none; classified "mechanism" in both |

Metadata only: the merged 6B3R rc10 file now records `options/tag = _loadcontrol` and `continuation/ds0`.

## Check and summary files

* All structures except 4WFF: load_check <= 5.6e-17, nulls <= 1.2e-11, indicator and physical scale identical.
  The two 2OAR VFIFE restarts are stored in the order [6, 7] instead of [7, 6]; matched by step they agree to 1e-7 relative (explicit integration error).
  6MGV rc8 `lam_ratio` divides by lambda0 ~ 1e-17 (4 mechanisms) and is not meaningful in either run.
* 4WFF: the anchor DOFs are chosen by QR column pivoting on the rigid-mode basis; the 1e-3 A input change switches the sixth anchor (node 407 -> 402).
  The anchored lowest eigenvalue moves from 1.25e-4 to 2.07e-4 (Eckart value unchanged to 4e-6), so lambda_Eckart / lambda_anchored goes 45.9 -> 27.6.
  The VFIFE check reaches its residual tolerance after 3400 instead of 4400 explicit steps (max deviation 6.7e-7 -> 1.6e-6 A, tolerance 1e-5 A).
  The best-amplitude linear overlap (closed and partner states almost coincide, RMSD_TM 0.64 A) moves 0.079 -> 0.075.

## Manuscript (`writing/tex/gen/`)

tab_panel, tab_nl, tab_phys identical. Changed values, all TRAAK:

| Key / cell | Legacy | Rebuilt |
|---|---|---|
| `lamratio-anch-max` | 46 | 28 |
| tab_ver TRAAK VFIFE max deviation | 6.7e-7 | 1.6e-6 |
| tab_val TRAAK overlap NL/linear | 0.03/0.08 | 0.03/0.07 |

Renamed key: `n-bb-first` -> `n-bb-lead` (wording rule). No classification, limit point or headline number changed.
