# fig5 plotting data

Source: data/derived/summary.json (validation, nulls, indicator, variants)

## approach.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| closed | TM RMSD of the closed structure to the partner | angstrom | value |
| nl | best TM RMSD of the nonlinear path | angstrom | value |
| lin | best TM RMSD of the best-amplitude linear response | angstrom | value |
| dilation | best TM RMSD of an isotropic in-plane dilation | angstrom | value |
| rewired_best | best TM RMSD over three rewired networks | angstrom | value |

## turning.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| chi_010 | second-order direction indicator chi at eps = 0.10 (membrane nodes) | - | value |
| delta | advantage of the nonlinear path over the best-amplitude linear response (empty: no partner) | angstrom | value |

## robustness.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| order | plotting order within the structure (jitter position) | - | index |
| kind | rc10, rc12, load (load-construction variant) or backbone (stiffened backbone) | - | label |
| variant | variant tag | - | label |
| delta | advantage Delta_L-NL | angstrom | value |
