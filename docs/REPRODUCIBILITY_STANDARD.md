# Research Project Cleanup and Reproducible Delivery Standard

## 1. The primary acceptance criterion

**A project is not complete merely because its code runs on the developer's computer. Delivery is complete only when another person can rebuild the results from a clean, independent copy of the project by following its documentation.**

This standard governs the use of AI coding tools to reorganize an existing research project. It is not simply a folder-copying or file-renaming exercise. The purpose is to eliminate hidden dependencies, make the data and computational workflow understandable, and independently verify the rebuilt outputs **without silently changing source data, scientific methods, or conclusions**.

A clean copy is a new directory that does not depend on the old project directory, undocumented files elsewhere on the author's machine, external symlinks, hard-coded local paths, or an unexplained software environment. Any genuinely required network services, licensed software, accelerators, clusters, or externally hosted datasets must be documented, along with the precise extent of successful reproduction.

## 2. Mandatory principles

1. **Keep raw data together and immutable.** Place unprocessed source data in `raw_data/`. Never overwrite source files during cleaning, conversion, reformatting, or renaming of columns. Preserve source-content checksums; if names are standardized, retain an old-to-new filename map.
2. **Keep processed data separately.** Store cleaned, filtered, transformed, merged, and normalized datasets in `processed_data/`. Record the generating code, inputs, parameters, and distinction between intermediate and final processed outputs.
3. **Collect usable plotting data.** Put all necessary inputs for every figure and panel under `figure_data/`. Prefer interoperable formats with clear English column names. Explain units, error bars, fitted curves, normalizations, and the meaning of each field. Every figure must be rebuildable without redoing expensive upstream computations.
4. **Ban local absolute paths and hidden dependencies.** Python, shell scripts, configuration files, notebooks, batch files, and their call chains must not contain author-specific local absolute paths. Resolve locations relative to the project root. Never use a symlink to the original directory to disguise an external dependency.
5. **Enforce strict language separation.** Source code, configurations, datasets, filenames, and English documents must contain no Chinese characters. Chinese is permitted only in Markdown documents, each prominently named with `cn`, such as `README_cn.md`, and accompanied by an independent English-only counterpart, `README.md`. Never place Chinese characters inside the English version, even to explain a translation. If a bilingual terminology mapping is essential, put it in `TERMINOLOGY_cn.md` and also provide a Chinese-free `TERMINOLOGY.md`.
6. **Run from the project root.** Every script and documented workflow must execute from the delivered project root without source edits or changes to the developer's machine. Imports, subprocess calls, and output paths must work after relocation.
7. **Preserve data lineage.** Each important dataset must be traceable from source inputs through processing scripts and parameters to analytical and plotting outputs. Supply an English `data_manifest.csv`.
8. **Map every important result to its code and data.** Supply `figure_manifest.csv` connecting figure/panel identifiers, inputs, scripts, commands, and output paths. Do not deliver figures without their generation steps.
9. **Record the complete runtime environment.** Pin or document relevant Python packages, system tools, model weights, and external program versions. Provide `requirements.txt` or `environment.yml` and any required non-Python installation instructions.
10. **Record randomness and selections.** Preserve random seeds, inclusion/exclusion criteria, train/validation/test splits, bootstrap protocols, and relevant parameters. Document tolerances for unavoidable hardware nondeterminism.
11. **Provide a reproducible execution sequence.** Supply a project-level runner such as `run_all.py`, or exact ordered commands. Support both a fast `figure_data/`-to-figures workflow and a full `raw_data/`-to-results workflow. Expensive steps may be run separately.
12. **Protect scientific equivalence.** Path fixes, imports, and I/O refactoring may be necessary. Changes affecting algorithms, thresholds, samples, normalizations, units, parameters, statistical definitions, or scientific interpretation require separate review and explicit approval.
13. **Use stable names and prevent unwanted overwrites.** Use English letters, numerals, underscores, and meaningful version/parameter/seed identifiers for generated outputs. Avoid names such as `final_new2`. Separate temporary files from final outputs and protect prior important outputs.
14. **Log cleanup decisions and avoid unapproved deletion.** Check checksums and code dependencies before consolidating duplicates. Retain old-to-new mappings and documented reasons for every omission, rename, or deletion candidate. The source project must remain unchanged.
15. **Protect confidential material.** Inspect credentials, access tokens, account information, private paths, unpublished or restricted data, and license constraints. Do not upload restricted files to third-party AI services without authorization. Inject secrets through controlled environment settings rather than delivering them in project files.
16. **Require evidence of independent verification.** Retain results of static audits, smoke tests, complete runs, numerical comparisons, figure recreation, and independent clean-copy testing. Report failures honestly. A program finishing without an exception does not by itself establish scientific correctness.

**Handling conflicting requirements:** If an original dataset already contains Chinese text, strict raw-data immutability and a Chinese-free delivery package cannot both be satisfied automatically. Do not silently translate or alter original data to claim compliance. Report the conflict as a blocking decision. The supervisor must choose and document an authorized solution, potentially retaining original evidence outside the delivery package and creating an audited normalized working copy. If the original is excluded, check whether the promised independent reconstruction remains possible. For Excel files, inspect sheet names, cells, comments, formulas, and hidden sheets, not merely the visible table.

## 3. Recommended delivery structure

```text
project/
├── README.md
├── README_cn.md
├── requirements.txt             # or environment.yml
├── data_manifest.csv
├── figure_manifest.csv
├── file_migration_map.csv
├── CHANGELOG.md
├── config/
├── raw_data/
├── processed_data/
├── figure_data/
│   ├── fig01/
│   └── fig02/
├── scripts/
│   ├── preprocessing/
│   ├── analysis/
│   └── plotting/
├── results/
│   ├── figures/
│   ├── tables/
│   └── logs/
├── tests/
├── run_all.py
└── validate_project.py
```

This is a reference layout, not a requirement to create empty directories. Small projects may combine subdirectories, but raw inputs, processed datasets, plotting inputs, scripts, and final outputs must remain distinguishable. Do not include source-project backups, verification copies, irrelevant caches, or personal environments in the final package.

## 4. End-to-end workflow for the student and AI agent

### Phase 0: Freeze the original and capture a baseline

- Maintain three distinct copies or locations: a read-only original, a working copy, and later a separate clean verification copy. Never perform destructive operations in the original.
- Record the original directory tree, SHA-256 checksums of important files, known commands, runtime versions, and available reference figures and numerical results.
- If possible, run the old workflow before restructuring. Record both passing and failing steps. If the original baseline cannot be reproduced, say so; do not claim strict equivalence without evidence.

**Deliverables:** initial `inventory.csv`, `baseline_report.md`, relevant input/output checksums.

### Phase 1: Inventory and trace dependencies before moving files

- Recursively classify every file by relative path, type, size, checksum, encoding, purpose, duplicates, temporary status, Chinese content, and local-path references.
- Inspect static code and, when necessary, runtime file accesses: inputs, outputs, parameters, subprocesses, downloads, environment variables, directory changes, symlinks, hard-coded names, and notebook assumptions.
- Inspect Excel sheets, columns, formulas and hidden content. Record formats and loaders for binaries or saved models. Label formats that cannot be reliably inspected as requiring manual review, not as passing.
- Classify resources as raw inputs, processed data, plotting inputs, code, configuration, final results, documentation, temporary/cache, or unknown. Never discard unknown resources automatically.

**Deliverables:** complete inventory, dependency overview, risk register, proposed migration map. **Review the plan before allowing high-impact changes.**

### Phase 2: Build a new directory and migration map

- Create the target folder structure in the working copy and migrate files according to approved roles.
- Populate `file_migration_map.csv` with old path, new path, action (keep/move/rename/regenerate/deletion candidate), reason, and checksums.
- Use content hashes and actual dependency analysis before consolidating duplicates. Similar names are not sufficient evidence of equivalence.
- Copy original files byte-for-byte whenever possible. Never re-save source Excel workbooks merely to move them; avoid unintentional changes to precision, missing values, formulas, or units.

**Deliverables:** proposed final tree, migration map, outstanding conflicts.

### Phase 3: Repair code and remove dependence on the old location

- Centralize resolution of project-root-relative paths, or pass locations through documented configuration or command-line parameters. All inputs and outputs must remain inside the new project or be explicitly declared external resources.
- Repair imports, subprocess calls, execution order, case sensitivity, path separators, output-folder creation, and permissions.
- Centralize versions, essential parameters, seeds, and output conventions, with reasonable defaults that do not require users to edit code.
- Avoid mixing scientific method changes into structural refactoring. Record any numerical behavior change separately, with justification, a comparison, and supervisor approval.

**Deliverables:** working scripts, consistent configuration, documented modifications.

### Phase 4: Establish two reproducible pipelines

- **Full pipeline:** `raw_data/ -> processed_data/ -> figure_data/ -> results/`. Record the inputs, outputs, parameters, generating program, and order for every step.
- **Fast plotting pipeline:** `figure_data/ -> results/figures/`. Every figure and panel should map to its inputs and exact plotting command through `figure_manifest.csv`. Store data or deterministic instructions for error bars, fits, annotations, and other plotted values.
- Maintain `data_manifest.csv` (file, provenance, generator, fields, units, purpose) and `figure_manifest.csv` (figure/panel, data files, plotting code, command, output).
- Prefer broadly readable plotting inputs over environment-specific serialized objects. Expensive intermediates may be regenerated from documented steps, but required plotting inputs should accompany the handoff.

**Deliverables:** complete analytical workflow, independent plotting workflow, data and figure manifests.

### Phase 5: Document the environment and enforce the language rule

- Write an English-only `README.md` with the goal, structure, data origins, installation, fastest working command, full workflow, compute requirements, expected outputs, and known limitations.
- Provide the equivalent `README_cn.md` if Chinese documentation is useful; every additional Chinese Markdown document likewise needs an English-only counterpart.
- Audit filenames, code, comments, text, CSV, workbook cells and sheet names, and parseable metadata for Chinese characters. Independently review opaque binary formats.
- Complete the dependency files, external command documentation, and `.gitignore`. Exclude caches, virtual environments, secrets, and irrelevant generated files without excluding essential project data.

**Deliverables:** language-separated documentation, reproducible environment instructions, language/path audit results.

### Phase 6: Test in layers

1. **Static compliance:** verify directory layout, referenced-file existence, Chinese content, absolute paths, external symlinks, exposed secrets, manifest targets, syntax, and dependencies.
2. **Smoke test:** execute a small representative workflow from the project root to verify inputs, computations, writes, and plotting.
3. **Scientific regression test:** run the full supported workflow; compare shapes, sample sizes, units, statistics, fit parameters, random seeds, and figures against the baseline. Prefer exact/checksum comparisons for deterministic outputs. Set numeric tolerances before observing differences for floating-point or GPU outputs.
4. **Independent relocation test:** copy the cleaned project to a different verification location, block accidental access to the original directory, build a fresh documented environment, and rerun. At minimum, the entire fast plotting pipeline must pass. If the full compute pipeline cannot be run due to hardware or time, state exactly which portions remain unverified.

**Deliverables:** English `validation_report.md` (plus `_cn.md` if needed), execution logs, numeric comparison report, and open issues.

### Phase 7: Review, hand off, and preserve evidence

- The student reviews file migration and exclusion decisions, all scientific changes, failures, and differences from reference figures or outputs.
- The AI agent separates claims into **actually executed and verified**, **static inspection only**, **not verified**, and **known failures**. Never describe proposed future tests as completed.
- Preserve the untouched original and restructuring evidence until sign-off. Remove temporary verification resources only after approval and compute checksums for the final handoff files.

**Final handoff:** working project directory, English README and any paired Chinese documentation, environment specifications, data and figure manifests, file migration map, change log, validation report, and directly executable reproduction commands.

## 5. Acceptance criteria

Mark **PASS** only when all applicable requirements have evidence:

- The source project is unmodified; original data are traceable; all delivered resources have explicit roles and no hidden reliance on the old directory.
- Language restrictions, local absolute-path restrictions, external symlinks, and resource dependencies have been audited and resolved.
- Another user can follow the README in a fresh location, install dependencies, run code, and generate outputs without source edits.
- Every final figure has understandable plotting data, source code, and a plotting command; the complete fast plotting workflow has actually passed.
- Critical numerical results reproduce the baseline exactly or within predeclared justified tolerances, with comparison evidence.
- Missing original baselines, non-distributable source files, unrun full computations, or unresolved language/data conflicts must be labeled **EXCEPTION / NOT VERIFIED**, not PASS.

**The final measure is not a tidy folder tree. It is whether someone who did not develop the project can reconstruct the results from a clean relocated copy, following the instructions.**

## 6. Copyable AI coding-agent instruction

> You are a research-project cleanup and reproducibility agent. Create a new deliverable directory outside the designated original project directory, and follow this standard. Treat the original as read-only: do not overwrite, edit, or delete it. Your first step is only to inventory files, trace code and data dependencies, identify risks, and propose a migration plan with complete old-to-new mapping. Do not perform risky mass renaming, deletion, format conversion, or scientific algorithm changes without review. After the plan is approved, migrate incrementally; repair path handling, environment setup, entry points, data lineage, and plotting inputs. No source code, data file, configuration, filename, or English document may contain Chinese characters. Chinese documentation may exist only in Markdown filenames explicitly marked `cn`, each with an English-only counterpart. Test each stage and finally relocate the cleaned project to an unrelated fresh directory, follow the README, rerun the supported pipelines, and compare important data and figures with the baseline. Produce the inventory, migration map, change log, environment specifications, two reproduction workflows, and evidence-backed validation report. Escalate unknown resources, tests that cannot actually run, possible scientific changes, and conflicts between rules. Never claim an unexecuted test has passed.
