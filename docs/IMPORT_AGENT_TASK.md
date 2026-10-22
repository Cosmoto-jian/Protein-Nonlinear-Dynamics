# AI Agent Task: Research Project Cleanup

Follow `PROJECT_CLEANUP_STANDARD.md` in full. Your goal is a clean, portable, independently reproducible project handoff, not a cosmetically tidy folder.

Input locations are to be supplied by the student:
- Original project directory (READ ONLY)
- New working/deliverable directory (WRITE ACCESS)
- Independent verification directory (WRITE ACCESS; must be separate)

## Work stages and gates

1. **Inventory only.** Enumerate and classify all files, hashes, locations, languages, code inputs and outputs, runtime dependencies, external paths, secrets, and potential duplicates. Record a baseline run and reference outputs if possible. Do not move or delete anything yet.
2. **Propose a migration.** Prepare old-to-new file mapping, data dependency graph, intended commands, exceptions, and risk list. Ask for approval before high-impact operations, including deletions, rewrites of datasets, and scientific changes.
3. **Reorganize a copy.** Keep all original data content unchanged; separate raw, processed, plotting data, scripts, configs, and results. Keep source files and every important output traceable.
4. **Repair portability.** Eliminate machine-specific absolute paths and hidden access to the original. Make execution from the project root work. Document dependencies and random seeds. Keep algorithm changes out of routine cleanup.
5. **Make figure recreation independent.** Supply a manifest and stored, readable plotting data for all final figures. Support quick plotting and full analysis pathways.
6. **Audit language.** Chinese must not appear in source code, datasets, configuration, filenames, or English docs. Chinese is allowed only in clearly `cn`-marked Markdown, with a corresponding Chinese-free English Markdown document. Flag conflicting raw data; never silently edit it.
7. **Test incrementally.** Perform static, smoke, scientific regression, and independent clean-copy tests, including numeric and figure comparisons. Record exactly what was executed.
8. **Deliver evidence.** Provide README, dependency specification, manifests, migration map, change log, validation report, command sequence, and issues requiring a human decision.

## Hard restrictions

- Never modify the original directory.
- Never delete unknown resources, silently overwrite raw data, or claim unrun tests passed.
- Never alter research choices or numerical methods solely to make code run.
- Do not hide dependencies with symlinks into the old directory.
- Do not expose secrets or upload restricted project data without permission.
- Label incomplete, conflicting, or unverified work explicitly.

Success means the project can be copied to an unrelated new location, configured as documented, and used to rebuild its figures and essential results without access to the old directory.
