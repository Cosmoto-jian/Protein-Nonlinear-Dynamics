# fig4 plotting data

Source: data/derived/paths/<id>_rc10.json, data/derived/summary.json (validation, nulls)

## nonlinear.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| step | 1-based step along the path | - | index |
| eps | normalized radial displacement | - | value |
| rmsd_tm | TM C-alpha RMSD to the partner structure | angstrom | value |

## linear.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| eps | normalized radial displacement of the scaled linear response | - | value |
| rmsd_tm | TM C-alpha RMSD of the linear response to the partner | angstrom | value |

## channels.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| closed | TM RMSD of the closed structure to the partner | angstrom | value |
| nl_best | best TM RMSD of the nonlinear path within eps <= eps_star | angstrom | value |
| lin_best | best TM RMSD of the best-amplitude linear response | angstrom | value |
| eps_best | eps of the best nonlinear frame | - | value |
| eps_star | end of the validity range | - | value |
| stable_steps | number of rows on the stable branch (Piezo1: up to the limit point L1) | - | count |
| limit_point | the path ends at a limit point | - | flag 0/1 |
| dilation | best TM RMSD of an isotropic in-plane dilation | angstrom | value |
| rewired_min | best TM RMSD over three rewired networks (lowest) | angstrom | value |
| rewired_max | best TM RMSD over three rewired networks (highest) | angstrom | value |
