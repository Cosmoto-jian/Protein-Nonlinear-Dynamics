"""C-alpha model inputs from the raw OPM membrane-oriented structures.
  python src/prepare_models.py
For each structure: every CA record (ATOM and HETATM, all alternate locations, as in the legacy inputs; placeholder
residues 'UNK' removed), restricted to the chains of the channel, and the OPM membrane half-thickness
REMARK in the form read by src/vfife/preprocess.py. Output: data/derived/models/<id>.pdb."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DERIVED, raw

STRUCTURES = ["6b3r", "6pwn", "2oar", "4xdk", "4wff", "6mgv", "6cq8", "6vtk"]
CHAINS = {"4wff": "AB"}            # TRAAK dimer; the other entries contain only the channel
# Membrane half-thickness used by the legacy (r1-r6) analysis. For 4WFF the legacy input carried an upper-case
# REMARK that the reader did not parse, so the default 15.0 A was used instead of the OPM value 16.1 A. Kept for
# numerical equivalence; see CHANGELOG.md (owner decision pending).
HALF_THICKNESS_OVERRIDE = {"4wff": 15.0}


def opm_half_thickness(lines):
    for line in lines:
        if line.startswith("REMARK") and "bilayer thickness" in line.lower():
            return float(line.split(":")[1].split()[0])
    raise ValueError("no OPM half-thickness REMARK")


def main():
    out = DERIVED / "models"
    out.mkdir(parents=True, exist_ok=True)
    for pid in STRUCTURES:
        lines = Path(raw(f"opm_{pid}.pdb")).read_text().splitlines()
        ht = HALF_THICKNESS_OVERRIDE.get(pid, opm_half_thickness(lines))
        keep = [f"REMARK      1/2 of bilayer thickness:   {ht}"]
        for line in lines:
            if not line.startswith(("ATOM", "HETATM")) or line[12:16] != " CA ":
                continue
            if line[17:20] == "UNK" or (pid in CHAINS and line[21] not in CHAINS[pid]):
                continue
            keep.append(line)
        (out / f"{pid}.pdb").write_text("\n".join(keep) + "\nEND\n")
        print(pid, len(keep) - 1, "CA, half-thickness", ht)


if __name__ == "__main__":
    main()
