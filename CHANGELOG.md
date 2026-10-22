# CHANGELOG

Structural, environment and scientific changes with their PR. Routine work is in the PR history.

| Date | PR | Type (routine / scientific) | Change | Approved by |
|---|---|---|---|---|
| 2026-10-22 | loop/import-r6 | routine | Import of the r6 manuscript project: raw structures (OPM, RCSB) and legacy r4 reference paths registered by hash; code moved to `src/` with root-relative paths; `run_all.sh` replaced by 72 pipeline steps; figures rebuilt from documented CSV in `figure_data/`; manuscript moved to `writing/tex/` | pending |
| 2026-10-22 | loop/import-r6 | scientific (needs-user) | TRAAK (4WFF) C-alpha input now taken from the OPM file (chains A, B) instead of the legacy assembly transformed to the OPM frame: coordinates differ by at most 1.0e-3 A, reported quantities by at most 2e-5 | pending |
| 2026-10-22 | loop/import-r6 | scientific (needs-user) | Legacy behaviour kept for equivalence, owner decision requested: TRAAK membrane half-thickness 15.0 A (legacy reader missed the upper-case REMARK; OPM gives 16.1 A); 6CQ8 keeps both alternate locations of Phe A185 as two nodes; the load and gauge check uses the legacy r4 paths as reference frames | pending |
