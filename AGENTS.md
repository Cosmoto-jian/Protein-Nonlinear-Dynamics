# AGENTS.md - agent navigation

## Research topic
See `STUDY.yaml`. All work must serve its `question` and `aims`; anything off-topic opens a `scope` issue.

## Modules and write access
| Path | Content | Who writes |
|---|---|---|
| `STUDY.yaml` | question, aims, T/E lists | owner only (CODEOWNERS) |
| `FINDINGS.md` | positive conclusions with real run IDs | judge, append-only |
| `DEAD_ENDS.md` | failed methods and why | judge, append-only |
| `data/raw/` | raw data, hash-named, add-only | fetch tool |
| `data/derived/` | processed data, listed in `data_manifest.csv` | pipeline |
| `src/` | preprocessing and analysis code | experiment agent |
| `config/pipeline.yaml` | ordered full-chain steps | experiment agent |
| `research/theory/T-xxx/` | theory, falsifiable predictions, `NOVELTY.md` | theory agent; novelty by opponent agent |
| `research/experiment/E-xxx/` | `explore/` tree, `PREREG.yaml`, `runs/` | experiment agent |
| `research/EVIDENCE.yaml` | T-E evidence links | judge |
| `audit/` | run audits, `EXCEPTIONS.yaml` | audit agent (different model); exceptions owner only |
| `figure_data/` | plotting data (CSV + README with columns) | `plot/extract/` only |
| `plot/` | `extract/`, `fig*.py`, `style/` | plotting agent |
| `results/` | figures, paired descriptions, tables, logs | generated only |
| `writing/` | writing law, `law.yaml`, LaTeX | writing agent; law owner only |
| `review/` | full-text review | outer-loop audit agent |
| `reports/` | self-evaluation, decisions, import inventories | agents write, owner approves |

## Hard rules
1. Conclusions cite only run IDs under `research/experiment/E-xxx/runs/`; results from `explore/` are never evidence.
2. `PREREG.yaml` is committed before the first run and never changed afterwards (checked against git history).
3. `data/raw/` file names start with the content sha256 prefix; files are never modified or deleted.
4. A theory enters pre-registration only with `NOVELTY.md` verdict `novel` or `incremental`.
5. `incremental` work never uses "first / novel / for the first time".
6. Every figure has a same-name description whose numbers are filled from data, never typed.
7. Changing aims, the writing law, or refuting a core theory gets the `needs-user` label and waits for the owner.
8. Language isolation: no Chinese characters in code, config, data, file names or English docs. Chinese only in `*_cn.md` files, each with a Chinese-free English twin.
9. Portability: no machine-specific absolute paths, no symlinks out of the repo, no secrets, no `os.chdir`. Every command runs from the project root.
10. Figure scripts read only `figure_data/`; `plot/extract/` is the only bridge from runs to plotting data. Every plotting CSV is documented (columns, units, error bars, normalisation) in its folder README and listed in `data_manifest.csv` and `figure_manifest.csv`.
11. Scientific equivalence: path, I/O and environment fixes are routine; any change to algorithms, thresholds, sample selection, normalisation, units, model parameters, statistics or figure meaning is a separate PR labelled `needs-user`.
12. Never claim an unrun test passed. Validation labels each item PASS, FAIL, EXCEPTION or NOT VERIFIED.

## Commands
| Command | Effect |
|---|---|
| `make gates` | all gates |
| `make figures-fast` | figure_data -> figures |
| `make all` | full rebuild from raw data |
| `make validate` / `make validate-full` | clean-copy validation (fast chain / both chains) |
| `make graph` | provenance graph |
| `make paper` | compile paper |
| `python tools/import_legacy.py <dir>` | read-only inventory of a legacy project |

## Issue routing
| Label | Root location | Owner |
|---|---|---|
| `data` | data/ | fetch |
| `experiment` | research/experiment, src/ | experiment agent |
| `theory` | research/theory | theory agent |
| `novelty` | NOVELTY.md / law.yaml | opponent agent |
| `figure` | plot/, figure_data/ | plotting agent |
| `writing` | writing/tex | writing agent |
| `law` | writing/WRITING_LAW.md | owner |
| `scope` | STUDY.yaml | owner |
| `import` | reports/import/ | import agent, owner approves |

## Issue states
`triaged -> reproducing -> fixing -> PR -> gates -> merged -> propagating -> rechecked -> closed`
At most 3 automatic fix attempts per issue; the same failure twice or budget exceeded -> `needs-human`.

## Legacy project import (the `import` issue)
Follows `docs/REPRODUCIBILITY_STANDARD.md`. The legacy directory is read-only and is never referenced by code.
1. Inventory PR: `python tools/import_legacy.py <legacy_dir>` writes `reports/import/<name>/inventory.csv`, `migration_map_draft.csv`, `baseline_report.md`. Run the legacy pipeline once if possible and record the baseline. Nothing is moved.
2. Owner reviews the draft map (`needs-user`). Deletions, dataset rewrites and scientific changes need explicit approval.
3. Migration PRs: copy byte-for-byte into the layout, append rows to `file_migration_map.csv`, register raw data, fix paths, fill both manifests, record changes in `CHANGELOG.md`.
4. Language conflicts in raw data are never silently edited: list them in `audit/EXCEPTIONS.yaml` for the owner.
5. Done when `make validate-full` matches the baseline within tolerances fixed in advance.
