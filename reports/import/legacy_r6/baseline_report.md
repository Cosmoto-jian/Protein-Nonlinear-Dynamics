# Baseline report: legacy_r6

Source: the r6 manuscript project (three packages `code/`, `figure_code/`, `paper_tex/`), read only.
Inventory: `inventory.csv` (325 files, 246.5 MB). Reviewed map: `migration_map.csv`.

## Summary
- Actions: exclude 96, merge 4, move 27, regenerate 140, replace 1, review 54, rewrite 3.
- CJK characters: none in names or text files.
- Absolute paths: 2 log files (`code/results/logs/arclength_6b3r.txt`, `nulls_6b3r.txt`) contain the old project path in tracebacks; logs are not migrated. No code or configuration file contains an absolute path.
- Largest file: `code/results/runs/6b3r_rc10_Xs.npy` (46.1 MB); 55 `.npy` state files, 217.8 MB in total; none exceeds the 100 MB GitHub limit.
- Duplicates: 19 by hash, all caused by `code/tb/` (a stale copy of the r5 paper package left by a build check) and by `paper_tex/figs/` (copies of `figure_code/output/`).

## Original run commands and status
- Full chain: `bash code/run_all.sh` (stages 1-8: paths, continuation, snap, load checks, indicator, VFIFE checks, variants, nulls, physical scale, analysis, `make_tex.py`). Each stage was executed during r5/r6 development; the script as a whole was not run end-to-end in one invocation. Status: stage outputs present; end-to-end run NOT VERIFIED.
- Numbers and tables: `python code/analyze.py && python code/make_tex.py` - executed for r6 (all 127 keys used in the text defined, none missing).
- Figures: `python figure_code/prep.py && python figure_code/plot_figs.py` - executed for r6; overlap report clean for 9 figures.
- Paper: `pdflatex; bibtex; pdflatex x2` in `paper_tex/` - compiles, 21 pages, no undefined references or overfull boxes.

## Environment
- Python 3.11.16, numpy 2.4.6, scipy 1.17.1, matplotlib 3.11.2, biopython 1.88 (macOS, 10 CPU).
- TeX Live 2026 (pdfTeX 1.40.29), `lmodern` required; elsarticle, multirow, placeins shipped in the package.
- The repository requires Python 3.12 and pins numpy 2.5.4 / matplotlib 3.11.2: floating-point differences are expected and need a tolerance fixed before re-running.

## Reference outputs (baseline for equivalence checks)
| File | sha256 |
|---|---|
| paper_tex/generated/numbers.json (144 keys) | 4d6732d8edf39b59fcc34224399ff6bcf83658d4bb0c35abc8b811875515c69e |
| code/results/summary.json | 1a8039126586e7493b3189d56aebc1de3f8aa413c97e63c074666980f8c32317 |
| paper_tex/manuscript.pdf | f599d6f0a4cb3c495cb2d31a0439171af9c0ecc6dd984af8cbb3a79a4d45625f |
All other file hashes are in `inventory.csv`.

## Provenance gaps and conflicts (owner decision needed)
1. `code/data/pdb_closed/*.pdb` (8 files) are already processed: OPM membrane-oriented coordinates reduced to C-alpha atoms (4WFF: biological assembly, rigidly transformed). The extraction script is not in the package, so raw -> model input cannot be rebuilt. Options: fetch the OPM / RCSB originals into `data/raw/` and write an extraction step that reproduces these files (verify coordinates), or register the present files as raw with a documented legacy provenance.
2. `code/data/pdb_targets/*.pdb` (7 files) look like unmodified RCSB entries; hashes must be checked against fresh downloads before registration.
3. `code/data/bfactors/4wff_crystal_frame.pdb` is derived (crystal frame of 4WFF); it needs a pipeline step from the raw entry.
4. `code/results/r4_reference/` is read only by `load_check.py`; proposal: switch the check to the r6 paths and drop the r4 files.
5. None of the analyses was pre-registered; thresholds and margins were fixed during development. Under the template these results are exploration, not evidence, until a locked PREREG with genuine holdout data is run.
6. `STUDY.yaml` (owner only) describes an earlier framing (projected spectrum with Tz/Rz removed; convex-hull vs membrane-facing nodes; stronger null than 8IXO) and does not match the r6 question.

## Review counts by folder
- pdb_closed: 8
- pdb_targets: 7
- r4_reference: 39
