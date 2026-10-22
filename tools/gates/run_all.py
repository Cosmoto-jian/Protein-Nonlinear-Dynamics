import subprocess, sys
from pathlib import Path
here = Path(__file__).parent
GATES = ["check_raw_immutable", "check_prereg_locked", "check_explore_leak", "check_novelty_gate",
         "check_findings", "check_fig_pairs", "check_language", "check_portability", "check_manifests"]
if __name__ == "__main__":
    bad = [g for g in GATES if subprocess.run([sys.executable, str(here / f"{g}.py")], cwd=here).returncode]
    print(f"\n{len(GATES) - len(bad)}/{len(GATES)} gates passed")
    sys.exit(1 if bad else 0)
