# AI for Science research project template (v4)

One research project = one repository = one `main`. Create a project with **Use this template**.

The project runs a closed loop. `make next` reads the repository state and names the single most useful next task; an agent does it on a branch, opens a PR, and the 5 gates decide whether it merges.

```
make next -> branch -> do the task -> PR -> make gates + make validate -> merge -> make next ...
```

Three files hold the truth; everything else is derived from them:

| File | Truth it holds |
|---|---|
| `STUDY.yaml` | question, aims, loop budget (owner only) |
| `pipeline.yaml` | every formal step: command, inputs, outputs, parameters. `pipeline.lock` records hashes; `data_manifest.csv`, `figure_manifest.csv` and `graph.json` are generated from it |
| `research/claims.yaml` | append-only ledger of judged results: supported, refuted, inconclusive, dead-end |

## This study
Geometrically nonlinear C-alpha truss mechanics of mechanosensitive channels under conservative membrane tension:
how the tension response departs from its linearization (stiffening, turning, snapping), verified with an explicit
VFIFE solver and a bordered Newton method, with stability certified by Sylvester's law of inertia.

| Item | Location |
|---|---|
| Structures (OPM, RCSB) and legacy reference paths | `data/raw/` (`MANIFEST.yaml`) |
| Analysis code and solvers | `src/` (see `src/README.md`) |
| Tension paths, checks, summary | `data/derived/` (pipeline outputs) |
| Figures 1-7, A.1, A.2 | `plot/figN.py` -> `figure_data/figN/` -> `results/figures/` |
| Manuscript (elsarticle) | `writing/tex/main.tex`; numbers and tables in `writing/tex/gen/` |

Full chain (`make all`): about one to two days on a 10-core workstation, dominated by the Piezo1 paths, the
continuation and the rewired-network nulls. Fast chain (`make figures-fast`): seconds. Build the paper with `make paper`.

## Quick start
```bash
pip install -r requirements.txt
make next           # the next task for the loop
make gates          # 5 gates (same as CI)
make status         # which pipeline steps are stale
make all            # rebuild stale steps: data/raw -> data/derived -> runs -> figure_data -> figures
make figures-fast   # figure_data/ -> results/ only
make validate       # clean-copy validation -> results/logs/validation_report.md
```

## Layout
| Path | Role |
|---|---|
| `data/raw/` | immutable source data, hash-named, sources in `MANIFEST.yaml` |
| `data/derived/` | processed data, produced only by pipeline steps |
| `src/` | preprocessing and analysis code |
| `research/theory/T-xxx/` | `THEORY.md` (falsifiable predictions), `NOVELTY.md` (adversarial novelty check) |
| `research/experiment/E-xxx/` | `explore/` (never evidence), `PREREG.yaml` (locked), `runs/` (formal, pipeline-produced) |
| `audit/` | one report per formal run; `EXCEPTIONS.yaml` (owner-approved) |
| `figure_data/figN/` | plotting CSVs + README documenting every column |
| `plot/` | `figN.py` with `extract` (run -> figure_data) and `plot` (figure_data -> figure); `style.py` |
| `results/` | figures, paired descriptions, logs (generated) |
| `writing/` | writing law, `law.yaml`, LaTeX |
| `tools/` | `gates.py`, `next.py`, `validate.py`, `new.py`, `import_legacy.py` |

Generic standard layout: `raw_data/` = `data/raw/`, `processed_data/` = `data/derived/`, `scripts/` = `src/` + `plot/`. See `docs/REPRODUCIBILITY_STANDARD.md`.

Agent rules: [AGENTS.md](AGENTS.md). Chinese: [README_cn.md](README_cn.md).
