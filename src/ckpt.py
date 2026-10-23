"""Checkpoint/resume for long path steps (I/O only; the computation is unchanged).
A checkpoint is keyed by the step's command line and stored under data/derived/tmp/ckpt/ (git-ignored, not a step
output). It is written atomically after every accepted point and deleted when the step finishes."""
import hashlib, os, pickle, sys
from paths import DERIVED

DIR = DERIVED / "tmp" / "ckpt"


def _file(tag):
    key = hashlib.sha256(" ".join(sys.argv[1:]).encode()).hexdigest()[:12]
    return DIR / f"{tag}_{key}.pkl"


def load(tag):
    f = _file(tag)
    if f.exists():
        with open(f, "rb") as h:
            st = pickle.load(h)
        print("resume", tag, "from checkpoint", flush=True)
        return st
    return None


def save(tag, state):
    DIR.mkdir(parents=True, exist_ok=True)
    f = _file(tag); tmp = f.with_suffix(".tmp")
    with open(tmp, "wb") as h:
        pickle.dump(state, h, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, f)


def clear(tag):
    _file(tag).unlink(missing_ok=True)
