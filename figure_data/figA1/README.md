# figA1 plotting data

Source: data/derived/summary.json (thresholds, variants, runs)

## thresholds.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| criterion | validity thresholds P20_|e|max, or backbone_0.05 (|e|_bb <= 5 %) | - | label |
| delta | advantage Delta_L-NL under that criterion | angstrom | value |

## margins.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| margin | absolute equivalence margin | angstrom | value |
| cls | class: NL better, equivalent or NL worse | - | label |

## load_variants.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| structure | structure id | - | label |
| variant | reference or load-construction variant tag | - | label |
| delta | advantage Delta_L-NL | angstrom | value |
