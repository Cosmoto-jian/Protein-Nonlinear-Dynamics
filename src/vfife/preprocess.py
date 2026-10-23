"""Reproducible preprocessing: PDB -> Calpha network -> membrane nodes ->
loading frame -> config.  All parameters recorded in a JSON config.

Membrane-node rule (frozen, deterministic): the bilayer midplane z_mid is
the z-position that maximizes the hydrophobic-residue fraction inside a slab
of half-thickness h_tm (h_tm read from the OPM REMARK '1/2 of bilayer
thickness'; fallback 15.0 A).  Membrane nodes = CA atoms with
|z - z_mid| <= h_tm.  Hydrophobic set: VAL LEU ILE PHE MET ALA GLY TRP PRO.
"""

import json
import hashlib
import numpy as np
from scipy.spatial import cKDTree

HYDRO_RESNAMES = {'VAL', 'LEU', 'ILE', 'PHE', 'MET', 'ALA', 'GLY', 'TRP', 'PRO'}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def parse_ca_atoms(pdb_path):
    """Parse CA atoms: returns list of (resname, chain, resseq, coord)."""
    atoms = []
    with open(pdb_path) as f:
        for line in f:
            if line.startswith('ATOM') and line[12:16].strip() == 'CA':
                atoms.append({
                    'resname': line[17:20].strip(),
                    'chain': line[21],
                    'resseq': int(line[22:26]),
                    'coord': [float(line[30:38]), float(line[38:46]),
                              float(line[46:54])],
                })
    return atoms


def bilayer_half_thickness(pdb_path, default=15.0):
    """Read '1/2 of bilayer thickness' from OPM PDB REMARK (Angstrom)."""
    with open(pdb_path) as f:
        for line in f:
            if line.startswith('REMARK') and 'bilayer thickness' in line:
                try:
                    return float(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
    return default


def find_midplane(coords, resnames, half_thickness, dz=0.5, min_nodes=20):
    """Deterministic midplane: maximize hydrophobic fraction in the slab."""
    z = coords[:, 2]
    hyd = np.array([r in HYDRO_RESNAMES for r in resnames])
    zs = np.arange(z.min(), z.max() + dz, dz)
    best, best_z = -1.0, float(z.mean())
    for zm in zs:
        m = np.abs(z - zm) <= half_thickness
        if m.sum() < min_nodes:
            continue
        frac = hyd[m].mean()
        if frac > best:
            best, best_z = frac, float(zm)
    return best_z, best


def build_pairs(coords, cutoff):
    """All CA-CA pairs with distance < cutoff (Angstrom)."""
    tree = cKDTree(coords)
    pairs = np.array(sorted(tree.query_pairs(cutoff)), dtype=int)
    return pairs


def loading_frame(mem_coords_xy):
    """Radial unit vectors e_r (in-plane) about the membrane-node centroid."""
    c = mem_coords_xy.mean(axis=0)
    d = mem_coords_xy - c
    r = np.linalg.norm(d, axis=1)
    ok = r > 1e-6
    e_r = np.zeros_like(d)
    e_r[ok] = d[ok] / r[ok, None]
    return c, e_r, r


def build_model(pdb_path, cutoff=10.0, gamma=1.0, out_config=None):
    """Full preprocessing chain. Returns model dict + config dict."""
    atoms = parse_ca_atoms(pdb_path)
    coords = np.array([a['coord'] for a in atoms])
    resnames = [a['resname'] for a in atoms]
    pairs = build_pairs(coords, cutoff)
    ht = bilayer_half_thickness(pdb_path)
    z_mid, hyd_frac = find_midplane(coords, resnames, ht)
    mem_idx = np.where(np.abs(coords[:, 2] - z_mid) <= ht)[0]
    centroid, e_r, radii = loading_frame(coords[mem_idx][:, :2])

    config = {
        'pdb_path': pdb_path,
        'pdb_sha256': sha256_file(pdb_path),
        'n_atoms_ca': len(atoms),
        'cutoff_A': cutoff,
        'gamma': gamma,
        'spring_model': 'uniform_k',
        'bilayer_half_thickness_A': ht,
        'membrane_midplane_z_A': z_mid,
        'midplane_hydrophobic_fraction': hyd_frac,
        'n_nodes': len(atoms),
        'n_elements': len(pairs),
        'n_membrane_nodes': len(mem_idx),
        'membrane_selection': '|z - z_mid| <= h_tm, z_mid by max hydrophobic fraction',
        'loading': 'displacement-controlled in-plane radial expansion, alpha_i = 1',
        'chain_residue_map': [
            [a['chain'], a['resseq']] for a in atoms
        ],
    }
    model = {
        'coords0': coords,
        'pairs': pairs,
        'mem_idx': mem_idx,
        'z_mid': z_mid,
        'centroid': centroid,
        'e_r': e_r,
        'radii': radii,
        'config': config,
    }
    if out_config is not None:
        with open(out_config, 'w') as f:
            json.dump(config, f, indent=1)
    return model
