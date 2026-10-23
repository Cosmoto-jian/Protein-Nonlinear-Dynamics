# fig1 plotting data

Source: src/model.py (MscL 2OAR, r_c = 10 A, reference state)

## nodes.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| node | C-alpha node index | - | index |
| x | x minus membrane-axis x | angstrom | value |
| y | y minus membrane-axis y | angstrom | value |
| z | z minus bilayer midplane | angstrom | value |
| membrane | node inside the membrane slab | - | flag 0/1 |
| loaded | node in a loaded outer shell | - | flag 0/1 |
| shell | outer-shell node of the drawn layer | - | flag 0/1 |
| layer | membrane node of the drawn 4 A layer | - | flag 0/1 |
| fx | x component of dA/dx (area gradient) | angstrom | value |
| fy | y component of dA/dx | angstrom | value |

## atoms.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| x | heavy-atom x minus membrane-axis x (OPM 2OAR) | angstrom | value |
| y | heavy-atom y minus axis y | angstrom | value |
| z | heavy-atom z minus bilayer midplane | angstrom | value |

## edges.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| i | first node of a truss element | - | index |
| j | second node of a truss element | - | index |

## polygon.csv
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| vertex | vertex order along the drawn layer polygon | - | index |
| x | vertex x (shell mean) minus axis x | angstrom | value |
| y | vertex y minus axis y | angstrom | value |
