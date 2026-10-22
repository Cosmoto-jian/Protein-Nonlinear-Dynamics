# figure_data - stored plotting data

One folder per figure (`fig2/`, ...), produced only by a `figN-data` step in `pipeline.yaml` (`python plot/figN.py extract`).

- CSV with English column names; no pickle.
- Each folder has a `README.md` with a table row for every column of every CSV:

| Column | Meaning | Unit | Kind |
|---|---|---|---|
| x | residue index | - | value |
| y_err | standard deviation over 3 seeds | nm | error bar (SD) |

- `make figures-fast` rebuilds every figure from these files alone.
