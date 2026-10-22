## Links
Closes #<issue> | T-xxx / E-xxx / R-xxxx / F-xxx

## What changed and why

## Change type
- [ ] Routine (paths, I/O, environment, docs) - numerically equivalent
- [ ] Scientific (algorithm, threshold, sample selection, normalisation, units, parameters, statistics, figure meaning) - needs owner approval, recorded in CHANGELOG.md

## Failing check first
- [ ] A check reproducing the problem was added first (tools/gates or tests/)
- [ ] It turns green after the fix and stays in the regression suite

## Downstream (make graph)
- To rebuild: figures / descriptions / text sections
- [ ] data_manifest.csv and figure_manifest.csv updated
- [ ] `make validate` result attached (PASS / EXCEPTION / NOT VERIFIED)

## Owner approval needed?
- [ ] Touches aims, writing law, exceptions, or refutes a core theory
