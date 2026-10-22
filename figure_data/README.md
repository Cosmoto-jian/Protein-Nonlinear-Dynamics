# figure_data - stored plotting data

One folder per figure (`fig2/`, `fig3/`, ...), written only by `plot/extract/figN.py`.

- Format: CSV with explicit English column names; no pickle.
- Each folder has a `README.md` that lists every CSV and, for every column: meaning, unit, and whether it is a value, an error bar (and which: SD, SEM, 95% CI), a fit curve, or a normalised quantity.
- Every CSV is listed in `data_manifest.csv` (role `figure_data`) and in `figure_manifest.csv`.
- `make figures-fast` rebuilds all figures from these files without upstream computation.
