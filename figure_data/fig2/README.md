# fig2 plotting data

Source: data/derived/summary.json (vfife_checks, load_check), r_c = 10 A

## vfife.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| start_step | 1-based Newton step from which VFIFE is restarted | - | index |
| eps_end | normalized radial displacement at the end of the increment | - | value |
| eps_star | end of the validity range of the structure | - | value |
| max_deviation | maximum nodal distance between the VFIFE rest state and the Newton state | angstrom | value |

## work_energy.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| dtau | tension increment of the Newton path | model units | value |
| mismatch | |U - W| / U at tau = 3.0 (MscL), trapezoidal work | - | value |

## gauge.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| reaction_symmetry | constraint reaction / load, four-symmetry gauge (tilt free) | - | value |
| reaction_eckart | constraint reaction / load, six Eckart conditions | - | value |
| reaction_anchor | support reaction / load, six isostatic anchors | - | value |
| rmsd_symmetry | RMSD of the tilt-free solution from the Eckart solution | angstrom | value |
| rmsd_anchor | RMSD of the anchored solution from the Eckart solution | angstrom | value |
