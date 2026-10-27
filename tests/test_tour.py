"""tour.py --unique: a run of shots under one (message, box) is kept only the first time it shows."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import tour  # noqa: E402


def scene(d, log, shots):
    d.mkdir()
    (d / "log.txt").write_text(log)
    for f in shots:
        (d / f).write_bytes(b"")


def test_dedupe(tmp_path):
    seen = set()
    a, b = tmp_path / "a", tmp_path / "b"
    scene(a, "f100 msg 054 ret 018168 var 6\nf300 msg 012 ret 04B1FB var 3\nf500 msg 054 ret 018168 var 6\n",
          ["f000050.png", "f000150.png", "f000200.png", "f000350.png", "f000550.png", "final.png"])
    scene(b, "f100 msg 054 ret 018168 var 2\nf300 msg 012 ret 04B1FB var 3\n",
          ["f000050.png", "f000150.png", "f000350.png"])
    tour.dedupe(str(a), "a", seen)
    tour.dedupe(str(b), "b", seen)
    kept = lambda d: sorted(p.name for p in d.glob("*.png"))  # noqa: E731
    # a: state's own message, both pages of 054, 012; 054 again later is a repeat
    assert kept(a) == ["f000050.png", "f000150.png", "f000200.png", "f000350.png"]
    # b: its own first message, 054 in another box variant; 012 in the same box already shown
    assert kept(b) == ["f000050.png", "f000150.png"]
