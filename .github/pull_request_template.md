## Task
`tools/next.py` task id or issue: <id / Closes #n>
Done when: <criterion copied from the task>

## Change type
- [ ] Routine (paths, I/O, environment, docs) - numerically equivalent
- [ ] Scientific (algorithm, threshold, sample, normalisation, units, parameters, statistics, figure meaning) - `needs-user`, line in CHANGELOG.md

## Checks
- [ ] Failing check first (bugs only)
- [ ] `make all` run; `pipeline.lock` and manifests updated
- [ ] `make gates` green; `make validate` result: PASS / EXCEPTION / NOT VERIFIED
