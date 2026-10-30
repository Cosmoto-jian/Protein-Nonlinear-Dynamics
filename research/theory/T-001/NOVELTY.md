---
target: T-001
claim: >-
  Applying one shared initial projected-area-gradient load to established linear
  protein network baselines and comparing their reference-state responses with a
  nonlinear truss path is a useful, potentially distinctive comparison protocol.
proposer_model: "codex/gpt-6-luna"
opponent_model: "codex/gpt-6-luna"
verdict: incremental
user_checked: false
review_status: "Provisional: the available runtime did not provide a distinct opponent model, and publisher records could not be accessed."
---

# Adversarial novelty check

## Search log

| Date | Source / query | Result |
|---|---|---|
| 2026-10-27 | Author repository for MCP-ANM; inspect README and examples | README describes MCP-ANM/MCP-mANM and PRS examples with membrane tension and push/pull forces; 6PWN appears as an example. The README does not document the proposed shared projected-area-gradient comparison or nonlinear truss path. It does not mention 2OAR. [Repository](https://github.com/ComputBiophys/MCP-ANM) |
| 2026-10-27 | DOI and publisher pages for the five works below | Direct fetches were blocked by domain access restrictions. Citation details and article-specific methods from those records are therefore **not independently verified in this review**. Links are supplied so the records can be checked. |
| 2026-10-27 | Targeted WebSearch queries for the named papers | Search was unavailable because the session search budget had already been exhausted. No search hit counts or independent search result records are claimed. |

## 5 closest prior works (opponent agent; goal: prove it is NOT new)

| # | Work (DOI / source) | Overlap | Difference and verification status |
|---|---|---|---|
| 1 | Han Z, Wang L, Song C. “Improved Anisotropic Network Models for Membrane Protein Dynamics and Mechanosensitive Ion Channels.” *PRX Life* 4, 013025 (2026). [DOI](https://doi.org/10.1103/xc5f-xr7n) · [APS record](https://journals.aps.org/prxlife/abstract/10.1103/xc5f-xr7n) · [authors’ repository](https://github.com/ComputBiophys/MCP-ANM) | Closest apparent model-family and application overlap. The accessible author-repository README documents MCP-ANM/MCP-mANM and force-response/PRS examples involving membrane tension and push/pull forces; it gives 6PWN as an example. | The accessible README does not establish that the paper compares all four T-001 baselines, uses 2OAR, applies the same initial area-gradient load to each, or compares with a nonlinear truss path. The full paper and exact citation metadata could not be retrieved here. Claims about the paper beyond the README are **unverified**. |
| 2 | Eyal E, Bahar I. “Toward a Molecular Understanding of the Anisotropic Response of Proteins to External Forces: Insights from Elastic Network Models.” *Biophysical Journal* 94(9), 3424–3435 (2008). [DOI](https://doi.org/10.1529/biophysj.107.120733) · [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC2292382/) | The title and cited subject make this a close precedent for applying external forces to elastic-network models. It challenges any broad claim that force-driven linear network response is itself new. | The paper text was inaccessible during this review. Whether it shares a prescribed load across the T-001 model families, uses a projected-area gradient, or compares to a nonlinear truss path is **unverified**. Citation metadata is listed from the DOI lead and was not checked against the publisher page in this session. |
| 3 | Lezon TR, Bahar I. “Constraints Imposed by the Membrane Selectively Guide the Alternating Access Dynamics of the Glutamate Transporter GltPh.” *Biophysical Journal* 102(6), 1331–1340 (2012). [DOI](https://doi.org/10.1016/j.bpj.2012.02.028) · [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC3309413/) | Relevant membrane-aware ANM precedent for the imANM side of the model comparison. It places membrane constraints and ANM dynamics in an established context. | The primary text was inaccessible. The exact imANM formulation and any relationship to load-response or nonlinear truss comparisons are **unverified** here; no overlap with the specific T-001 protocol is established. Citation metadata was not confirmed against the publisher page in this session. |
| 4 | Atilgan AR et al. “Anisotropy of fluctuation dynamics of proteins with an elastic network model.” *Biophysical Journal* 80(1), 505–515 (2001). [DOI](https://doi.org/10.1016/S0006-3495(01)76033-X) · [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC1301252/) | Foundational ANM precedent: the proposed linear baselines use reference-state elastic-network mechanics. Thus, the linear Hessian response is established methodology. | This is broad methodological prior art, not evidence for the particular projected-area load, cross-model protocol, or nonlinear-truss comparison. The publisher/full-text page could not be read here, so bibliographic metadata and article details remain **unverified in this session**. |
| 5 | Xia K, Opron K, Wei G-W. “Multiscale Gaussian network model (mGNM) and multiscale anisotropic network model (mANM).” *The Journal of Chemical Physics* 143, 204106 (2015). [DOI](https://doi.org/10.1063/1.4936132) · [PubMed record](https://pubmed.ncbi.nlm.nih.gov/26627949/) | Establishes prior work on the multiscale ANM lineage relevant to the mANM component of MCP-mANM. | It is a model-method precedent, not evidence for the shared projected-area-gradient load or comparison against a nonlinear truss path. Its exact relationship to the MCP-mANM implementation and the article metadata were **not verified from the primary record** in this session. |

## Strongest case against novelty

The project combines established linear elastic-network response with an established idea—following a nonlinear mechanical model under load—and applies a common initial forcing vector to compare reference-state responses. Using the same vector is a reasonable control, but by itself is a comparison design choice rather than a new model or theory. The small-load tangent agreement in P-002 is expected from local linearization; departure at finite load is a validation of the nonlinear model’s range, not a surprising prediction unless the departure metric and load interval are specified in advance and produce a non-obvious result.

The two pilot structures and a later eight-structure panel are evaluation scope. The accessible MCP-ANM author repository already uses 6PWN in an example, so that structure alone cannot carry a novelty claim. Reusing established baselines and structures may still be useful, but it makes this look most like a validation/benchmarking exercise. I found no verified evidence that the exact shared-load/nonlinear-path combination has already been published; given the inaccessible full-text sources, absence of evidence here is not evidence of absence.

Fairness is also not established merely by equalizing the initial nodal load. The models can differ in network construction, cutoffs, membrane treatment, stiffness scaling, parameter provenance, and null-space handling. A shared load supports a controlled comparison of responses, but raw amplitudes across independently parameterized Hessians are not an accuracy ranking. T-001 appropriately cautions against that ranking absent preregistered calibration. Node correspondence, frame definition, parameter provenance, rigid-body projection, and response normalization must be reported before claiming the comparison is fair in a stronger sense.

## Narrow residual novelty, if defensible

A narrowly framed contribution may be the **specific protocol**: apply the same initial projected-area gradient to several declared linear baselines on matched C-alpha nodes, compare their reference-state response directions/amplitudes with the nonlinear truss model’s tangent response, then track the nonlinear path as the current area gradient changes. The primary-source records available in this session do not verify that this exact protocol has appeared before. It is therefore a plausible incremental contribution, not a substantiated first-of-its-kind claim.

## Judge verdict and reasons

**Verdict: incremental.** ANM-family reference-state mechanics, membrane-aware variants, multiscale ANM, and force-response analysis have substantial prior-art coverage in the candidate literature above. T-001's possible contribution is the controlled projected-area-load comparison and finite-deformation diagnostic, rather than a new network model, load theory, or biological claim. This review does not verify that the protocol is unprecedented. Do not use “first” or broad novelty language on this evidence.

**Recommendation:** Present T-001 as a preregistered comparative validation of linear-response baselines for the projected-area load. State the narrow protocol distinction, report model-specific parameterization and fairness limits, and reserve any stronger novelty claim until the five primary records—especially the 2026 MCP-ANM paper—have been checked directly against the full methods. Keep the no-gating and no-B-factor scope boundaries stated in THEORY.md.

**Review validity:** The required distinct opponent model was unavailable. The runtime and the requested Sonnet subagent both exposed `codex/gpt-6-luna`, identical to the proposer model. This file records the actual model and does not claim to satisfy the distinct-model rule in `AGENTS.md`. The review is consequently provisional and should be repeated by a genuinely different model before any novelty claim relies on it.
