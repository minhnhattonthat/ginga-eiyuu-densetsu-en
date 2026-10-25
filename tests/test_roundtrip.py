"""Phase 4: every extracted string re-encodes to its original bytes, and the text ranges are covered with no gaps."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM = ROOT / "rom" / "Ginga Eiyuu Densetsu (Japan).sfc"
pytestmark = pytest.mark.skipif(not ROM.exists(), reason="no ROM")


@pytest.fixture(scope="module")
def db():
    import textdb
    return textdb.load()


def strings(rom, t):
    """(id, first text byte, text length) for every source; name strings skip their length byte."""
    import textdb
    yield from textdb.main_strings(rom, t)
    yield from textdb.sub_strings(rom, t)
    for sid, off, n in textdb.name_strings(rom, t):
        yield sid, off + 1, n - 1


def test_roundtrip(db):
    rom, t = db
    for sid, off, n in strings(rom, t):
        text, used = t.decode(rom, off, n)
        assert used == n and t.encode(text) == rom[off:off + n], sid


def test_script_json_matches_rom(db):
    """script/*.json jp fields are what the ROM holds (a stale or hand-edited jp would build wrong bytes)."""
    rom, t = db
    want = {sid: rom[off:off + n] for sid, off, n in strings(rom, t)}
    got = {}
    for f in ("main", "sub", "names"):
        for r in json.loads((ROOT / "script" / f"{f}.json").read_text(encoding="utf-8")):
            got[r["id"]] = t.encode(r["jp"])
    assert got == want


def contiguous(spans, start):
    """End of the run of spans starting at `start`; fails on any gap or overlap."""
    pos = start
    for a, b, sid in sorted(spans):
        assert a == pos, "gap/overlap before %s: %06X -> %06X" % (sid, pos, a)
        pos = b
    return pos


def test_coverage(db):
    """Text ranges (docs/re/text.md) are fully covered: pointer table, then strings back to back, then free space."""
    import textdb
    rom, t = db
    main = [(o, o + n, s) for s, o, n in textdb.main_strings(rom, t)]
    end = contiguous(main, textdb.MAIN_TABLE + 2 * textdb.MAIN_COUNT)
    assert end == 0x2F883 and set(rom[end:textdb.SUB_TABLE]) == {0xFF}
    sub = [(o, o + n, s) for s, o, n in textdb.sub_strings(rom, t)]
    end = contiguous(sub, textdb.SUB_TABLE + 2 * textdb.SUB_COUNT)
    assert end == 0x2FFB8 and set(rom[end:0x30000]) == {0xFF}
    names = list(textdb.name_strings(rom, t))
    pos = textdb.NAME_TABLES[0][1]
    for name, table, count in textdb.NAME_TABLES:   # the five tables sit back to back: 0x103BB-0x1081C
        assert table == pos, name
        pos = contiguous([(o, o + n, s) for s, o, n in names if s.startswith(name)], table + 2 * count)
    assert pos == 0x1081C


def test_text_pointer_writers(db):
    """The renderer's string pointer $1113-$1115 is written only by the opener (main table), the substring call and
    return, and the byte-advance: no text source outside main/sub exists for it (docs/re/text.md)."""
    rom, _ = db
    hits = []
    for i in range(len(rom) - 2):
        if rom[i] in (0x8C, 0x8D, 0x8E, 0x9C) and rom[i + 2] == 0x11 and rom[i + 1] in (0x13, 0x14, 0x15):
            hits.append("%02X:%04X" % (i >> 15, 0x8000 | (i & 0x7FFF)))
    assert hits == ["07:97D0", "07:97D6", "07:97DC", "07:9A41", "07:9A47", "07:9A4D", "07:9B4C", "07:9B54",
                    "07:9B5A", "07:9E0C", "07:9E14"]
