import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM = ROOT / "rom" / "Ginga Eiyuu Densetsu (Japan).sfc"


@pytest.mark.skipif(not ROM.exists(), reason="no ROM")
def test_event_messages():
    import events
    d = ROM.read_bytes()
    # message sequences seen in the emulator (msgcall logs in docs/re/debug.md)
    assert events.walk(d, 0x15)[0] == [0x12B]
    assert events.walk(d, 0x16)[0] == [0x3F, 0x40, 0x41, 0x42, 0x43]
    assert events.walk(d, 0x2F)[0] == [0x205, 0x3C, 0x3D, 0x3E]
    assert events.walk(d, 0x2A)[0] == [0x35, 0x36]
    # ending 23 reaches the first message of all four flag branches
    assert {0xC6, 0xC8, 0xC9, 0xCB} <= set(events.walk(d, 0x23)[0])
