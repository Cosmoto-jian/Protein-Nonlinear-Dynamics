# Run audit checklist (inner loop, every run)
- [ ] Input data hashes match data/raw
- [ ] Code commit reproducible; command recorded
- [ ] PREREG locked and unchanged; run parameters match PREREG
- [ ] Holdout used, not the dev data or seeds of exploration
- [ ] Numerics: NaN, convergence, units
- [ ] Positive and negative controls pass
- [ ] Statistics and multiple comparisons (including explore_nodes_tried)
- [ ] Multi-seed reproduction within the pre-registered tolerance
- [ ] Conclusion matches output numbers

Verdict: `pass` | `fix-implementation` | `redesign`
