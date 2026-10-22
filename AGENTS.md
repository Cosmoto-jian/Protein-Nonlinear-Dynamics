# AGENTS.md - rules for every agent

## The loop
1. Run `python tools/next.py`. Do exactly the one task it prints, nothing else.
2. Work on branch `loop/<task-id>` (or `fix/I-xxx` for an issue). For a bug, write the failing check first.
3. If the task changes code or data, add or update its step in `pipeline.yaml` and run `make all`.
4. `make gates` must pass. Open a PR that states the task and its `done_when` criterion.
5. Stop and label `needs-user` instead of guessing when the task touches aims, the writing law, exceptions, a scientific change to merged work, or refutes a core theory.

## Roles (use a different model for the opponent and the auditor than for the proposer)
| Role | Writes | Never writes |
|---|---|---|
| theory | `research/theory/T-xxx/THEORY.md` | claims, runs |
| opponent | `research/theory/T-xxx/NOVELTY.md` (goal: prove it is NOT new) | THEORY.md |
| experiment | `src/`, `research/experiment/E-xxx/` (explore, PREREG, pipeline steps for runs) | claims, audits |
| auditor | `audit/reports/R-xxxx.md` | the code it audits |
| judge | appends to `research/claims.yaml` | anything else |
| plotting | `plot/`, figure steps in `pipeline.yaml` | `figure_data/` by hand |
| writing | `writing/tex/` | `writing/WRITING_LAW*.md`, `law.yaml` terms (owner) |
| owner | `STUDY.yaml`, `WRITING_LAW*.md`, `audit/EXCEPTIONS.yaml` | - |

## Hard rules (enforced by `make gates`)
1. **Data**: `data/raw/` is add-only; names start with content sha256[:16]; sources in `MANIFEST.yaml`. Files in `data/derived/`, `figure_data/` and `runs/` exist only as outputs of `pipeline.yaml` steps, and match `pipeline.lock`.
2. **Pre-registration**: a run needs a locked `PREREG.yaml` with holdout data or seeds; a locked PREREG never changes.
3. **Evidence**: `claims.yaml` is append-only. Every supported / refuted / inconclusive entry cites a formal run with a `pass` audit. Exploration (`explore/`, `N-xxx`) is never evidence and never reaches figures or text; only dead-end entries may cite it. A theory in a locked PREREG needs a NOVELTY verdict `novel` or `incremental`, 5 closest works, opponent model != proposer model. Without `novel` + owner check, novelty words are banned in the paper.
4. **Figures**: `fast` steps read only `figure_data/` and `plot/`. Every figure has a same-name description with numbers filled from data. Every plotting CSV column is documented in its folder README.
5. **Hygiene**: no Chinese outside `*_cn.md` (each with an English twin); no machine-specific absolute paths, external symlinks, secrets or `os.chdir`; all commands run from the project root.

## Other rules
- Scientific equivalence: path, I/O and environment fixes are routine. Algorithm, threshold, sample selection, normalisation, units, parameters, statistics or figure meaning changes are a separate PR labelled `needs-user`.
- Never report an unrun check as passed. Validation marks each item PASS, FAIL, EXCEPTION or NOT VERIFIED.
- Every number in the paper comes from `writing/tex/gen/numbers.tex`, produced by a pipeline step.

## Audit checklist (auditor, one report per run: `audit/reports/R-xxxx.md`)
Input hashes match `pipeline.lock`; run parameters match the locked PREREG; holdout used, not exploration data or seeds; no NaN, convergence and units checked; positive and negative controls pass; statistics corrected for multiple comparisons including `explore_nodes_tried`; seeds reproduce within the pre-registered tolerance; the stated result matches the output numbers.
End the report with `Verdict: pass`, `Verdict: fix-implementation` or `Verdict: redesign`.

## Legacy import
`python tools/import_legacy.py <dir>` writes a read-only inventory, a draft `file_migration_map.csv` and a baseline report to `reports/import/<name>/`. The owner approves the map (`needs-user`) before any file is copied. Raw files that break the language rule are recorded in `audit/EXCEPTIONS.yaml`, never edited.
