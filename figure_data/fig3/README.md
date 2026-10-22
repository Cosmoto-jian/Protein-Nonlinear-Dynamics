# fig3 plotting data

Source: data/derived/paths/<id>_rc10.json and data/derived/summary.json (membrane nodes, r_c = 10 A)

## path.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| step | 1-based step along the path | - | index |
| eps | normalized radial displacement of the membrane nodes | - | value |
| amp | amplitude ratio a = |u_L| / |u_NL| at the same tension | - | value |
| dir | direction error sin(theta) between u_L and u_NL | - | value |
| lam_rel | lowest constrained eigenvalue relative to its reference value | - | value |
| max_e | largest element strain |e|_max | - | value |

## structures.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| eps_star | end of the validity range | - | value |
| step_star | step at eps_star; for Piezo1 the limit point L1, later rows are the unstable continuation | - | index |
| stable_beyond | rows beyond eps_star lie on a stable branch and are drawn thin | - | flag 0/1 |
| a_005 | measured amplitude ratio at eps = 0.05 | - | value |
| sin_005 | measured sin(theta) at eps = 0.05 | - | value |
| kappa_005 | second-order amplitude indicator kappa at eps = 0.05 | - | value |
| chi_005 | second-order direction indicator chi at eps = 0.05 | - | value |
