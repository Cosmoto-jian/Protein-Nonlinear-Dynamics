# fig7 plotting data

Source: data/derived/paths/6b3r_rc10_loadcontrol.json, _arclength.json, _snap.json

## load_control.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| eps | normalized radial displacement, load-controlled Newton path | - | value |
| tau | membrane tension | model units | value |

## continuation.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| point | continuation point index | - | index |
| eps | normalized radial displacement | - | value |
| tau | membrane tension | model units | value |
| dlam_ds | load-parameter component of the unit tangent | - | value |
| n_neg | negative eigenvalues of the constrained tangent (inertia count) | - | count |
| lam1 | lowest eigenvalue of the constrained tangent (shift-invert with the shift chosen from the inertia count: sigma = -1e-4 when n_neg = 0, sigma below the lowest eigenvalue when n_neg > 0); negative wherever n_neg = 1 | model units | value |
| lam2 | second-lowest eigenvalue of the constrained tangent (same solve) | model units | value |
| lam3 | third-lowest eigenvalue of the constrained tangent (same solve) | model units | value |
| lam0 | lowest constrained eigenvalue at the reference state x0 (rc10 path) | model units | value |
| max_e | largest element strain | - | value |

## post_snap.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| eps | normalized radial displacement of the post-snap equilibrium (explicit VFIFE from L1) | - | value |
| tau | membrane tension of the post-snap equilibrium | model units | value |
| max_e | largest element strain | - | value |

## snap_elements.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| rank | rank by strain change in the snap | - | index |
| chain | chain of both residues | - | label |
| res_i | first residue of the element | - | index |
| res_j | second residue of the element | - | index |
| e_pre | element strain at the limit point | - | value |
| e_post | element strain at the post-snap equilibrium | - | value |
| backbone | virtual backbone bond | - | flag 0/1 |
