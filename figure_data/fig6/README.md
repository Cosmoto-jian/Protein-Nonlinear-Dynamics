# fig6 plotting data

Source: src/model.py (Piezo1 6B3R -> 8IXO mapping), data/derived/paths/6b3r_rc10 (best frame), data/derived/summary.json

## nodes.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| node | C-alpha node index of the closed model | - | index |
| chain | chain id | - | label |
| resid | residue number | - | index |
| tm | node in the transmembrane validation subset | - | flag 0/1 |
| x0 | closed-state x | angstrom | value |
| y0 | closed-state y | angstrom | value |
| z0 | closed-state z | angstrom | value |
| xm | model best frame x, superposed on the TM subset | angstrom | value |
| ym | model best frame y | angstrom | value |
| zm | model best frame z | angstrom | value |
| xe | 8IXO x, superposed on the TM subset | angstrom | value |
| ye | 8IXO y | angstrom | value |
| ze | 8IXO z | angstrom | value |

## params.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| key | parameter name: axis_x, axis_y (membrane axis, A), z_mid (bilayer midplane, A), best_step, eps_best, A0_nm2, dA_model_nm2, dA_exp_nm2 (outer-shell area, nm^2) | - | label |
| value | parameter value | see key | value |
