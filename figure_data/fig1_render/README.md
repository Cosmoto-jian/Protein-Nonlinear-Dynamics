# fig1 panel a rendered layers

Source: plot/fig1_render.py from figure_data/fig1 (nodes.csv, edges.csv, atoms.csv)

## render_surface.png
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| - | molecular surface (Gaussian density of atoms.csv, iso level ISO of the maximum), orthographic view along +y | - | RGBA image |

## render_network.png
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| - | C-alpha truss of nodes.csv and edges.csv, same camera; focus node and its elements drawn dark | - | RGBA image |

## render_meta.json
| Column | Meaning | Unit | Kind |
|---|---|---|---|
| half_height | half height of the rendered view (parallel scale); image x maps to model x, image y to model z | angstrom | value |
| width_px, height_px | image size | pixel | value |
| focus_node | node whose truss elements are highlighted | - | index |
| n_focus_elements | number of highlighted elements | - | count |
| surface | sigma, grid (angstrom) and iso fraction of the surface | - | value |
