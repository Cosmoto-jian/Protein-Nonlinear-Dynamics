# Proposals for owner-only files (not applied)

These files are protected by CODEOWNERS and may be changed only by the owner. The texts below are proposals.

## STUDY.yaml
```yaml
id: S-001
title: "Stiffening, turning and snapping of protein elastic networks under membrane tension"
question: "How does the membrane-tension response of a C-alpha truss network depart from its linearization (ANM), can the departure be predicted from the reference state, and which part of it matters for agreement with tension-related partner structures of mechanosensitive channels?"
aims:
  - id: A1
    text: "Establish a well-posed, verified tension path: gauge derived from the symmetries of the load, VFIFE vs Newton agreement, stability certified by inertia at every step"
    done_when: "Gauge reactions, VFIFE deviations and inertia counts for all structures are pipeline outputs and an audited run supports them"
  - id: A2
    text: "Separate the linearization error into amplitude (stiffening) and direction (turning) and test whether the second-order indicators predict them"
    done_when: "A locked PREREG with held-out structures tests kappa < 0 => a > 1 and the rank agreement of chi with sin(theta); result recorded in claims.yaml"
  - id: A3
    text: "Test whether the turning brings the path closer to the partner structures than the best-amplitude linear response, dilation and rewired networks"
    done_when: "A locked PREREG (Piezo1 advantage replicated on an independent closed Piezo1 structure) is run, audited and recorded"
  - id: A4
    text: "Classify the end of the stable branch (limit point vs strain bound) with continuation and certified inertia"
    done_when: "Limit-point and snap results are pipeline outputs, audited and recorded"
target_journal: "Journal of the Mechanics and Physics of Solids"
figure_width_mm: 190
owner: "Cosmoto-jian"
loop:
  max_open_tasks: 1
  usd_per_month: 50
  reflect_after_dead_ends: 3
```

## writing/law.yaml (terms and symbols used in writing/tex/main.tex)
| Symbol | Term | Definition |
|---|---|---|
| `\tau` | membrane tension | conjugate of the polygon area A in Pi = U - tau A (model units) |
| `\eps` | normalized radial displacement | <(x - x0) . e_r> / <r0> over membrane nodes; a response quantity, not a strain |
| `\eps^*` | end of the validity range | last step with P20 <= 5 % and |e|max <= 0.5, or the end of the stable branch |
| `a` | amplitude ratio | ||u_L|| / ||u_NL|| at the same tension (stiffening if > 1) |
| `\sin\theta` | direction error | residual of the best-amplitude fit of u_L to u_NL (turning) |
| `E_{NL}` | linearization error | ||u_NL - u_L|| / ||u_NL||, Eq. (4) |
| `\kappa` | second-order amplitude indicator | tau u2 . u1 / ||u1||^2 |
| `\chi` | second-order direction indicator | tau ||u2_perp|| / ||u1|| |
| `\Delta_{L-NL}` | nonlinear advantage | best-amplitude linear TM RMSD minus best nonlinear TM RMSD |
| `\lambda_1` | lowest constrained eigenvalue | of Kt - tau H on the Eckart-constrained space |
| `n_{neg}` | negative inertia | number of negative eigenvalues of the constrained tangent |
| `\rho` | gauge reaction ratio | ||C^T mu|| / ||tau H x|| |
| `M_{xy}` | tilting moment | in-plane moment of the load about the membrane axis |
| `\gamma` | spring constant | from crystallographic B-factors (pN/A) |

## Decisions requested (see CHANGELOG.md)
1. TRAAK membrane half-thickness: keep the legacy 15.0 A or use the OPM value 16.1 A (scientific change, rerun of TRAAK).
2. 6CQ8 alternate locations: keep both conformers of Phe A185 as nodes (legacy) or keep altloc A only (rerun of 6CQ8).
3. Load and gauge check: keep the legacy r4 reference frames or switch to the r6 paths (changes the verification numbers slightly).
4. Pre-registration: r1-r6 results are exploration under this template; confirmatory runs need locked PREREG with genuine holdout (new structures).
