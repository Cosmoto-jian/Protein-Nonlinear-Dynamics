# E-001 Three-Model Experiment Implementation Plan

> **For agentic workers:** Use this plan task-by-task. Keep development outputs separate from confirmatory runs and claims.

**Goal:** Implement and run standard ANM, LezonLab imANM, and OPM geometric-mask imANM with one shared projected-area load and six-condition Eckart constraint, calibrate P-001/P-002 criteria on 2OAR/6PWN, then run a separately frozen eight-structure OPM confirmation set.

**Architecture:** Preserve the current nonlinear truss model and standard ANM implementation. Add a sparse LezonLab imANM Hessian builder and a geometric-mask variant that differs only in membrane classification, a generic constrained Hessian solver using existing bordered KKT machinery plus SciPy fallback, and a schema-versioned E-001 runner. Pipeline outputs distinguish development/calibration from the confirmatory evidence run.

**Tech Stack:** Python, NumPy, SciPy sparse matrices, existing `BorderedKKT`/PARDISO path when available, YAML preregistration, project pipeline runner, local VEND environment.

**Spec:** `docs/superpowers/specs/2026-10-27-e001-implementation-design.md` and user decisions in this session.

## Global Constraints

- Compare only standard ANM, imANM, and OPM geometric-mask imANM; no membrane-contact probability, MCP predictor, or MCP score is part of the study.
- All three models use the same frozen C-alpha node order, `X0`, full projected-area gradient `f0`, and six-condition `C=gauge_C(X0)`.
- Development/calibration structures are only 2OAR and 6PWN; do not report them as confirmatory evidence.
- The baseline imANM uses LezonLab `membranm` commit `1381eeb022855926ff3de6ed7862f06bd65f7b9f`, full-residue mode, `gamma=1`, `r_c=11 Å`, `MSCL=16`, and same-chain residue-adjacent edge multiplier 100. Its membrane membership uses the same OPM-derived `z_mid` as the geometry variant but the source half-thickness 13.4 Å.
- The geometric-mask imANM uses the same formula and parameters, replacing only the baseline membership rule with the OPM REMARK half-thickness around that same `z_mid`.
- Standard ANM retains the project reference definition: `gamma=1`, 10 Å pair cutoff. Store exact parameter and input hashes.
- Freeze the area-operator settings and nonlinear reference network/cutoff before formal holdout response computation.
- The confirmation set has eight new OPM structures, selected from a frozen OPM catalog snapshot after excluding prior-use structures and applying a declared sequence-family redundancy rule; rank with a fixed public seed plus canonical accession and raw-file SHA-256. Never calculate responses before the selection manifest is frozen.
- P-001 and P-002 thresholds may be calibrated only from 2OAR/6PWN; record and freeze them before holdout responses are computed.
- Never add a regularizing spring, silently drop nodes, or alter the common force by model.
- `data/raw/` is add-only and content-addressed; all generated files must be outputs of `pipeline.yaml` and match `pipeline.lock`.
- Follow `AGENTS.md` role boundaries: experiment may edit implementation, E-001 preregistration/exploration, and pipeline steps; theory/opponent/owner/writing work stays with their roles.
- Set `locked: true` only after the full confirmatory selection, model configuration, metrics, thresholds, tolerance, controls, and novelty prerequisites are frozen.

## Review Focus

- Distinct membrane classes despite nonzero OPM z-centers — test that the two imANM masks use the same center and differ only by 13.4 Å versus the OPM half-thickness.
- Directional imANM spring scaling — test all in-plane/z tensor-component cases against the LezonLab source formula.
- Chain-aware adjacent-residue strengthening — test same-chain sequence-adjacent springs and ensure different chains/residue-number gaps are not strengthened.
- Shared load/gauge identity — runner must hash and pass exactly the same `X0`, `f0`, and `C` to all three models.
- Singular/unstable Hessians and missing PDB atoms — record a model failure with diagnostics; do not add springs or silently change the node set.

---

### Task 1: Implement LezonLab imANM and the OPM-mask variant

**Files:**
- Create: `src/vfife/hessians.py`
- Create: `tests/test_hessians.py`
- Modify: `pipeline.yaml` only if a dedicated unit-check step is part of the repository pipeline convention; do not create model-data outputs here.

**Interfaces:**
- Consumes: `coords0: (N,3)`, pair list `(E,2)`, boolean membrane mask `(N,)`, chain IDs `(N,)`, author residue numbers `(N,)`.
- Produces: `imanm_hessian(coords0, pairs, mem_idx, chain_ids, residue_ids, gamma=1.0, mscl=16.0, backbone_scale=100.0) -> scipy.sparse.csr_matrix`.
- The geometric variant calls the same builder with the OPM-thickness mask; it must not introduce a separate formula.

- [ ] Add failing formula tests for a two-node single edge: outside/outside, inside/inside, and mixed membrane membership; check the exact directional 3x3 block factors from LezonLab `hess_superrow_mem` and `scalefunc0`.
- [ ] Add failing tests for symmetry, zero row-sum/translation modes, gamma scaling, `MSCL=1` equivalence to the standard ANM edge Hessian, strict distance cutoff, and same-chain adjacent-residue multiplier 100.
- [ ] Implement `imanm_hessian` using pairwise displacement direction and per-coordinate scales `p_i=p_j=MSCL**0.25` for membrane nodes, `1` otherwise; multiply component `(alpha,beta)` by `p_i*p_j` only when each corresponding axis is x/y; assemble positive diagonal blocks and negative off-diagonal blocks.
- [ ] Validate input shapes, duplicate/self pairs, zero-length edges, finite parameters, and symmetric CSR output; fail clearly rather than regularizing invalid edges.
- [ ] Run `python -m pytest -q tests/test_hessians.py` and record the result.

### Task 2: Add generic constrained sparse-Hessian response

**Files:**
- Modify: `src/kkt.py`
- Modify: `tests/test_kkt.py`

**Interfaces:**
- Consumes: arbitrary symmetric CSR `H`, common full-row-rank `C`, and full nodal `f0`.
- Produces: `linear_response_hessian(H, C, f0, refine=2) -> (u, mu, diagnostics)`; diagnostics include solver backend and relative equilibrium/gauge residuals.

- [ ] Add failing tests comparing the arbitrary-Hessian solution to a dense bordered KKT solve for deterministic small matrices.
- [ ] Add failing tests for the common six-row gauge, nonzero multipliers, zero RHS negative control, an extra constrained mechanism, and nonfinite/asymmetric invalid Hessians.
- [ ] Implement a sparse SciPy `splu`/`spsolve` fallback when PARDISO is unavailable; when available, create a pattern from `H`, factor it, solve `[f0, 0]`, and retain `mu`.
- [ ] Compute and report `||H u + C.T mu - f0|| / max(1, ||f0||)` and `||C u|| / max(1, ||u||)`; report constrained inertia or explicitly mark it unavailable when its method cannot certify it.
- [ ] Keep existing `linear_response(net, area, C, X0, rhs)` behavior intact as a compatibility wrapper.
- [ ] Run `python -m pytest -q tests/test_kkt.py` and record the result.

### Task 3: Build a shared-input E-001 development runner

**Files:**
- Create: `src/run_e001.py`
- Create: `tests/test_e001_runner.py`
- Modify: `pipeline.yaml`
- Modify: `research/experiment/E-001/explore/explore.yaml`

**Interfaces:**
- Consumes: structure IDs, project model inputs, fixed model configuration, and `stage=dev`.
- Produces: development result JSON under `research/experiment/E-001/explore/`, never under formal `runs/`.
- Per structure: construct one `X0`, stable dev node mapping, area operator, `f0`, and six-row `C`; pass identical values to all three Hessians.

- [ ] Add failing runner tests asserting byte-identical `X0`, `f0`, `C`, and node-order hashes across the three model records.
- [ ] Implement dev model construction on 2OAR/6PWN: ANM cutoff 10 Å; imANM pair cutoff 11 Å and `|z-z_mid|<13.4 Å`; geometric-mask imANM with same pairs/parameters and `|z-z_mid|<h_OPM`.
- [ ] Record parameter dictionaries and SHA-256 hashes for raw source PDB, node table, coordinates, membrane mask, load, gauge, Hessians, and response vectors; include KKT residuals, inertia/mechanism status, amplitudes per unit `tau`, and overlap to the nonlinear reference tangent.
- [ ] Mark every output `stage: development-calibration`, with an explicit non-evidence flag.
- [ ] Add a pipeline step with exact command, dependencies, params, and output; keep outputs outside `runs/` so preregistration gates do not interpret them as formal evidence.
- [ ] Run the development step in local VEND on 2OAR and 6PWN; record failures exactly and do not create a formal run record.

### Task 4: Run and calibrate P-001/P-002 on development structures

**Files:**
- Modify: `src/run_e001.py`
- Modify: `research/experiment/E-001/PREREG.yaml`
- Modify: `research/experiment/E-001/explore/explore.yaml`
- Modify: `pipeline.yaml`

- [ ] Define P-001 from the existing theory statement: finite, reproducible response for each declared Hessian; response amplitude per unit load; normalized overlap with the nonlinear reference tangent.
- [ ] Define P-002 on the project nonlinear truss reference path: report small-load tangent convergence and preregistered finite-load change metric up to the path's fixed validity stop.
- [ ] Run the P-002 nonlinear paths for 2OAR/6PWN under one frozen reference-network cutoff and area-operator configuration; do not mix path cutoffs or load scaling.
- [ ] Use only the two development structures to set numeric outcome thresholds by the predeclared calibration rule, and save the calibration outputs and resulting threshold table before holdout response runs.
- [ ] Check that `explore_nodes_tried` equals the actual E-001 development nodes tried, including N-001, and freeze it before confirmation.

### Task 5: Freeze the eight-structure OPM holdout and confirmatory preregistration

**Files:**
- Modify: `research/experiment/E-001/PREREG.yaml`
- Modify: `data/raw/MANIFEST.yaml`
- Create: hash-prefixed OPM inputs and frozen node tables in their declared raw-input locations
- Modify: `pipeline.yaml`

- [ ] Freeze an OPM catalog snapshot and candidate/exclusion manifest; exclude the existing eight-structure panel, 2OAR/6PWN development structures, and all inputs with recorded prior use.
- [ ] Apply the owner-approved family redundancy rule, rank eligible independent entries by the frozen public seed, canonical accession, and raw PDB SHA-256, and select exactly eight before any response calculations.
- [ ] Add selected OPM files as hash-prefixed add-only raw files with verified sources and checksums; freeze the node mapping, altloc policy, membrane metadata, model parameters, area settings, `f0`/`C` definitions, nonlinear reference cutoff, and all hashes.
- [ ] Fill P-001/P-002 metrics and support/refute/inconclusive thresholds using only the stored development calibration; freeze reproduction/residual tolerances, positive/negative controls, repetitions, statistics, and multiplicity rule.
- [ ] Resolve/update T-001 through the theory role and obtain a valid distinct-model opponent review before a locked PREREG cites T-001.
- [ ] Add the real confirmatory pipeline step only after its runner and frozen inputs exist; set `locked: true` only when every prereg field and gate prerequisite is complete.

### Task 6: Run the confirmatory comparison and audit

**Files:**
- Create: `research/experiment/E-001/runs/R-xxxx.json` via pipeline
- Create: `audit/reports/R-xxxx.md` via a distinct auditor model

- [ ] Run `make all` in local VEND and verify the formal run output hashes match `pipeline.lock`.
- [ ] Verify exactly eight holdout structures, common `X0`/`f0`/`C` hashes, no NaNs, residual/inertia validity, P-001/P-002 criteria, controls, and recorded failure handling.
- [ ] Request an independent auditor pass; do not append claims unless the audit ends `Verdict: pass`.
- [ ] Run `make gates` and record each check as PASS/FAIL/EXCEPTION/NOT VERIFIED; never report unrun checks as passed.
