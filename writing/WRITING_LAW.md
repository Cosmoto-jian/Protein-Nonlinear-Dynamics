# Writing law (owner only; any change triggers a full-text recheck)

1. **Main line**: the paper serves only the question and aims in `STUDY.yaml`.
2. **Theory**: present derivations from `research/theory/` faithfully; no exaggeration, no hidden assumptions.
3. **Evidence**: conclusions come only from audited, judged entries in `research/claims.yaml`; each is traceable to its F-ID.
4. **Numbers**: every number in the text is a macro from `writing/tex/gen/numbers.tex`, never typed.
5. **Figures**: every cited figure exists in `results/figures/` and matches `results/descriptions/`.
6. **Terms and symbols**: only those registered in `law.yaml`, used consistently.
7. **New concepts**: registered in `law.yaml` with novelty check, formal and operational definitions, code, source theory, difference, evidence and first use; otherwise they stay out of the text.
8. **Novelty wording**: "first / novel" only with verdict `novel` and owner spot-check.
9. **Exploration**: numbers from the exploration tree never appear in the text.
10. **Language**: the paper and all non-`_cn` files are English only.
