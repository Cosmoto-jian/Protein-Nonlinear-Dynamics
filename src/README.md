# src - analysis code
Scripts read `data/raw` (through `paths.raw`) or `data/derived` and write `data/derived`. Every script that produces a
formal output is a step in `pipeline.yaml`. Files are located from the project root (`paths.ROOT`), never by absolute paths.

| Module / script | Role | Pipeline steps |
|---|---|---|
| `paths.py` | project-root locations; raw files looked up by original name in `data/raw/MANIFEST.yaml` | - |
| `prepare_models.py` | C-alpha model inputs from the OPM membrane-oriented structures | `models` |
| `vfife/` | truss network, explicit VFIFE solver, tension load, preprocessing (membrane nodes, midplane), stability helpers | - |
| `model.py` | C-alpha truss, shell-averaged polygon area load, Eckart gauge and fast bordered solver, symmetry gauge, partner mapping, metrics | - |
| `inertia.py` | inertia of the bordered tangent (Bunch-Kaufman LDL^T, Sylvester's law) | - |
| `run_path.py` | load-controlled Newton tension path with certified inertia at every step; load and backbone variants | `path-*`, `variant-*` |
| `arclength.py` | pseudo-arclength continuation of the Piezo1 path; writes the merged production path | `arclength-6b3r` |
| `snap.py` | explicit VFIFE snap-through at the Piezo1 limit point | `snap-6b3r` |
| `load_check.py` | area operator vs shoelace, gradient check, tilting moment, gauges, anchors, equilibrated load | `load-check` |
| `indicator.py` | second-order indicators chi and kappa | `indicator` |
| `vfife_check.py`, `batch_vfife_checks.py` | VFIFE restarts against Newton states; work-energy order | `vfife-checks` |
| `nulls.py`, `batch_nulls.py` | dilation, ANM-subspace and rewired-network nulls | `nulls` |
| `prs.py` | single-node perturbation-response scanning null (target-informed reference) | `prs` |
| `physcale.py` | spring constant from crystallographic B-factors, area changes | `physical-scale` |
| `analyze.py` | validity ranges, validation classes, sensitivity summary | `summary` |
| `make_tex.py` | every number (`\V{key}`) and table of the manuscript into `writing/tex/gen/` | `numbers` |

Conventions: model units (k = 1) and angstrom; eps is the normalized radial displacement of the membrane nodes;
validity range P20 <= 5 % and |e|max <= 0.5, ending at the first negative eigenvalue if earlier; production gauge:
six Eckart conditions; 8 A networks with mechanisms are excluded from the comparison.
