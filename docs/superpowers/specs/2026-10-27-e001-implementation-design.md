# E-001 Implementation Design (Draft)

## Intent

Implement a reproducible three-model reference-state response comparison for a confirmatory set of previously unused OPM membrane-protein structures. The user-confirmed models are standard ANM, imANM, and an imANM variant whose membrane-node membership is defined by an OPM geometric mask. For each structure, all models receive the same frozen C-alpha node order and coordinates, the same full projected-area gradient `f0 = grad A(X0)`, the same scalar load, and the same six-condition Eckart matrix `C`. The common full load and six-condition constraint are user-confirmed requirements; together they define the estimand as response on the common constrained subspace. No membrane-contact probabilities, scores, or predictors are part of the model definition.

The exact imANM equation and parameters, the precise way the geometric mask enters the imANM Hessian, confirmatory sampling design, and numerical acceptance criteria remain to be frozen. Candidate implementation details below are proposals, not user-approved scientific decisions; do not treat them as confirmation defaults until the owner confirms them.

The comparison is a full-model comparison: network topology and membrane anisotropy may differ by model. It will not be described as isolating anisotropy alone. The shared six-condition constraint also restrains the whole-protein tilt directions of membrane-anisotropic Hessians; report the constraint multipliers/reactions and interpret responses on the common constrained subspace.

## Candidate Hessian definitions for owner review

The implementation shape is symmetric CSR Hessians of shape `(3N, 3N)` on the exact common node order. Spring contributions follow the existing ANM convention. Do not add regularizing springs or model-specific node removal. The three models are standard ANM, imANM, and an OPM geometric-mask imANM variant. The third model uses the imANM Hessian rule, with OPM geometric membrane membership replacing the baseline imANM membrane-region classification. This definition follows the user's scope clarification. Freeze the exact OPM mask generation rule (including its midplane algorithm and any structure-specific thickness override) and record its node-mask hash.

- **ANM:** use the existing project Hessian and freeze its cutoff and force constant from the selected network/reference configuration.
- **imANM:** the candidate source is LezonLab `membranm` at commit `1381eeb022855926ff3de6ed7862f06bd65f7b9f`, with the previously reviewed settings `gamma=1`, contact cutoff `11 Å`, membrane scale `16`, and same-chain adjacent-residue spring multiplier `100`. These values and the coordinate-component scaling operation still require a controlling source/parameter decision before implementation.
- **OPM geometric-mask imANM variant:** retain the selected imANM equation and parameterization, changing only how membrane membership is assigned: use the frozen OPM geometry mask instead of the baseline imANM membrane-region rule. This is the intended paired comparison; document any unavoidable implementation difference explicitly.

For every model, store its exact equation, source/version, parameter meanings and units, graph/topology, and normalized CSR Hessian hash in the run record. Name the third model **OPM geometric-mask imANM** (or a clearly equivalent name).

## Shared solve and runner

Add an arbitrary-Hessian linear-response entry point that solves

`[[H, C.T], [C, 0]] [u, mu] = [f0, 0]`.

Build `X0`, node identity table, `C=gauge_C(X0)`, area operator, and `f0` once per structure. Use the exact projected-area operator instance and resolved parameters used by the existing nonlinear reference path; freeze those parameters and its `f0` hash in the preregistration and run record. Pass the identical arrays to each model; do not apply MCP weights, model-specific scaling, node filtering, or force redistribution to `f0`. Record SHA-256 values for the node order, `X0`, `C`, `f0`, Hessian and input structures. Candidate diagnostics per model are solver status, constrained inertia/extra mechanism count, response vector, RMS displacement per common load, signed and absolute normalized overlap with the nonlinear reference-tangent response, equilibrium residual, `C u` residual, and KKT multipliers. The owner must confirm which diagnostics are primary validity gates and their numeric tolerances, including whether any negative constrained eigenvalue invalidates a model even when the KKT response is finite. A model with extra unconstrained mechanisms, nonfinite output, or failed residual checks is a recorded failure, not silently regularized.

The E-001 runner writes one schema-versioned JSON result under `research/experiment/E-001/runs/`; `pipeline.yaml` declares the real command, code/input dependencies and output. It must be runnable in local VEND, using the existing SciPy fallback when PARDISO is unavailable. Assess runtime and memory for each approved Hessian on dev structures before the formal run.

## Node identity and input preparation

For each frozen OPM input, save a stable node table with node index, chain, residue name, auth residue number, insertion code, polymer index when available, and chosen altloc. Resolve one C-alpha per physical residue using a locked altloc rule; unresolved or duplicate mappings fail closed. Do not infer a score mapping. All model Hessians and loads use this same table and coordinate array.

A confirmation holdout must be a new OPM coordinate bundle outside the repository's existing eight-structure panel and outside the N-001 dev structures. Freeze the source snapshot, assembly/chains, raw coordinate hash, sequence and node-map hashes, membrane metadata, and all preprocessing rules before calculating any holdout Hessian or response. Select units outcome-blind from a frozen eligible OPM population using a public seed and a hash-ranked accession/file hash after the owner locks the target population, sample count, family-exclusion rule and eligibility limits. Existing structures may be used only for implementation/debug checks, never represented as untouched confirmation data.

## Preregistration and scientific reporting

The preregistration fixes the three equations, source versions, all parameters, node and altloc rules, projected-area functional/settings defining common `f0`, the common `C`, holdout selection algorithm, nonlinear reference network/cutoff defining any tangent comparator, primary endpoint(s), support/refute/inconclusive criteria, numerical tolerances, positive and negative controls with expected outcomes, numerical-repeat interpretation, statistics and `explore_nodes_tried`. Numerical restarts are reproducibility checks, not independent biological samples. Results are interpreted as a constrained full-model response comparison, not a standalone measure of membrane anisotropy. The negative control must be specified before locking; it cannot be selected after observing holdout responses. Linear amplitudes are reported per unit common scalar load unless a pre-registered load value is explicitly selected; P-002 requires its finite-load points and validity interval to be fixed in advance.

E-001 may evaluate P-001 reference-state linear responses and P-002 nonlinear-path convergence only if both endpoints, load points and validity limits are explicitly included before holdout unsealing. The existing nonlinear path machinery supplies the nonlinear tangent/path; no claim is supported until the formal run has a passing audit. T-001 wording and its independent novelty review must be updated through the repository's theory/opponent roles before a locked preregistration cites it.

## Delivery boundaries

This draft defines the eventual implementation. The current repository task selector names `E-001-lock`, whose narrow task is to write/lock a preregistration and register a run step; it does not itself authorize implementing the new Hessians/runner. Under `AGENTS.md`, code implementation needs its own selected experiment task. The design review identified scientific and protocol decisions that prevent a defensible confirmation lock at this point. No implementation code, data, PREREG, or pipeline step has been changed for this draft.

## Owner decisions to settle before locking confirmation

1. Confirm the scientific estimand: compare the three user-selected methods under the same full projected-area load and six-condition Eckart constraint on the common constrained subspace.
2. Identify the exact projected-area functional and settings defining `A` and `f0`, tied to the nonlinear reference path; select the nonlinear reference network/cutoff that defines its tangent comparator.
3. Approve or replace the exact equations and settings for standard ANM, imANM, and the OPM geometric-mask imANM variant. Define operationally the OPM-derived membrane mask (including midplane and any thickness overrides), the imANM membrane-coordinate/scaling rule, adjacent-residue handling, and exactly how the geometric mask changes the imANM Hessian. Do not use MCP terminology or MCP Hessian forms as a substitute for this definition.
4. Fix the confirmatory population, sampling unit, sample count, family independence/exclusion rule, source snapshot, and eligibility limits; then freeze and hash the selected OPM bundle before response runs.
5. Choose the primary endpoint(s), statistics, numeric support/refute/inconclusive thresholds, validity tolerances including treatment of negative constrained modes, and positive/negative controls with expected outcomes; state whether E-001 includes both P-001 and P-002.
6. Confirm the shared load convention and, if P-002 is included, its finite load points and valid comparison interval.
7. Confirm a deterministic one-altloc-per-residue rule, missing-residue/insertion-code handling, and confirmatory repeat policy.
8. Resolve T-001 wording and independent novelty review through the appropriate theory/opponent roles before locking a preregistration that cites it.

## Builder-check findings

The independent builder review found these consequential omissions, now reflected above: exact area functional/settings, nonlinear reference network/cutoff, negative-mode validity rule, operational definition of OPM geometric membrane membership, negative control and expected outcome, common scalar-load convention, finite-load points if P-002 is included, numerical tolerances and repeat metric, and a valid independent novelty reviewer before a preregistration cites T-001. These items change the stimulus, comparator, model matrix, or decision rule and must not be filled in silently by an implementer. The user's subsequent scope clarification reduced the comparison from four candidate methods to the three methods stated in the Intent section; the model definitions above reflect that correction.
