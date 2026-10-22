# AI for Science research project template (v3.3)

One research project = one repository = one `main`. Create a project with **Use this template**; it then evolves on its own.

```
issue -> fix/I-xxx -> failing check first -> fix -> PR -> make gates green -> merge main -> rebuild downstream -> recheck -> close
```

Delivery standard: a clean copy of this repository, set up only as documented here, must rebuild its figures and core results without access to any other directory (see `docs/REPRODUCIBILITY_STANDARD.md`).

## Quick start
```bash
pip install -r requirements.txt
make gates          # all 9 gates (same as CI)
make figures-fast   # figure_data/ -> results/figures + results/descriptions
make all            # data/raw -> data/derived -> runs -> figure_data -> figures
make validate       # clean-copy validation -> results/logs/validation_report.md
make graph          # provenance graph -> graph.json
```

## Layout
| Path | Role |
|---|---|
| `STUDY.yaml` | research question, aims, theory and experiment lists |
| `FINDINGS.md`, `DEAD_ENDS.md` | append-only conclusions and failed paths |
| `config/pipeline.yaml` | ordered steps of the full rebuild chain |
| `data/raw/` | immutable source data, hash-named, registered in `MANIFEST.yaml` |
| `data/derived/` | processed data, every file listed in `data_manifest.csv` |
| `src/` | preprocessing and analysis code |
| `research/` | theories (`T-xxx`), experiments (`E-xxx`: explore tree, `PREREG.yaml`, `runs/`), `EVIDENCE.yaml` |
| `audit/` | per-run audit reports, `EXCEPTIONS.yaml` |
| `figure_data/` | stored, documented plotting data per figure (CSV) |
| `plot/` | `extract/` (runs -> figure_data), `fig*.py` (figure_data -> figures), `style/` |
| `results/` | `figures/`, `descriptions/`, `tables/`, `logs/` |
| `writing/` | writing law, `law.yaml`, LaTeX |
| `review/`, `reports/` | full-text review rounds, decisions, self-evaluation, legacy import inventories |
| `tools/` | gates, validation, provenance graph, legacy import |
| `docs/` | reproducibility standard |

Mapping to the generic standard layout: `raw_data/` = `data/raw/`, `processed_data/` = `data/derived/`, `scripts/` = `src/` + `plot/`.

Agent rules: [AGENTS.md](AGENTS.md). Chinese version: [README_cn.md](README_cn.md).
