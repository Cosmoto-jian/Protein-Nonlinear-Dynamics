# T-001 Shared-load linear baselines for nonlinear truss response
- Status: proposed
- Tier: auxiliary

## Motivation and cross-disciplinary source

ANM, imANM, MCP-ANM, and MCP-mANM provide established or literature-derived reference-state network models for protein flexibility. The present study asks how elastic networks deform under a specified projected-area load and follows the primary truss model into finite deformation. Applying the same initial area-gradient nodal load to each linear model isolates differences in reference-state stiffness response; comparing those responses with the nonlinear path tests where the initial linear approximation ceases to describe the modeled deformation.

This comparison is about elastic-network mechanics under the projected-area-load assumption. It does not model or infer channel opening or electrochemical gating. No B-factor analysis is included in this experiment.

## Derivation

For a structure with initial coordinates $X_0$, the current area operator supplies the common load vector $f_0=\nabla A(X_0)$. For each linear baseline with reference Hessian $H_m$, compute the projected pseudoinverse response $u_m=H_m^+ f_0$ after removing rigid-body modes using the same Eckart subspace. Report (a) the response amplitude per unit load under the declared model parameters and (b) normalized overlap $|u_m^T u_{NL,1}|/(\|u_m\|\|u_{NL,1}\|)$ with the primary nonlinear model's tangent response. The nonlinear model separately solves $\nabla U(X)-\tau\nabla A(X)=0$ with the current area gradient at every state; it remains the primary method and is not relabeled as linear.

The initial pilot uses 2OAR and 6PWN, then expands to the full eight-structure panel after model mapping and runtime are reviewed. A model must use the same C-alpha node correspondence, membrane frame, and load vector for a structure. Model-specific parameterization and its provenance are recorded; differing raw amplitudes are reported without ranking them as accuracy unless a separate, preregistered calibration supports that claim.

## Falsifiable predictions
| ID | Prediction | Observation if false | Test experiment |
|---|---|---|---|
| P-001 | For each pilot structure and each declared linear baseline with a stable projected Hessian, the response to the common initial area-gradient load is finite, reproducible, and has a measurable normalized overlap with the nonlinear model's reference-state tangent response. | A baseline has extra unconstrained mechanisms, cannot be mapped to the shared nodes, fails numerical reproduction, or yields a non-finite response; record a model-specific failure rather than silently changing the model. | E-001 |
| P-002 | At sufficiently small load, the nonlinear path displacement approaches its own reference-state tangent response; as load increases, at least one of amplitude ratio, direction overlap, or normalized path displacement changes measurably for at least one pilot structure before its preregistered validity limit. | The small-load response does not converge to the tangent response within tolerance, or the selected finite-load interval shows no change beyond numerical tolerance in any preregistered nonlinearity metric. | E-001 |

## Competing theories

- The reference-state linear response remains an adequate description throughout the stable range examined; any apparent path differences arise only from model-specific stiffness scaling.
- Differences among baseline models are dominated by network construction and membrane anisotropy, while the finite-deformation correction is negligible within the registered range.
