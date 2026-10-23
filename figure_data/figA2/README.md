# figA2 plotting data

Source: data/derived/summary.json (load_check)

## anchors.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| anchor_reaction | support reaction of six isostatic anchors relative to the load | - | value |
| rmsd_raw | RMSD of the anchored solution from the Eckart solution, original load | angstrom | value |
| rmsd_equilibrated | the same for the reference-equilibrated load A' | angstrom | value |
| lambda_eckart | lowest constrained eigenvalue with the Eckart conditions | model units | value |
| lambda_anchored | lowest constrained eigenvalue with the anchors | model units | value |
