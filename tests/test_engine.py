"""English build: engine hooks in place, and every text pointer (through {far} stubs) reaches its own string."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM = ROOT / "rom" / "Ginga Eiyuu Densetsu (Japan).sfc"
pytestmark = pytest.mark.skipif(not ROM.exists(), reason="no ROM")


@pytest.fixture(scope="module")
def marker():
    import build
    tx = build.en_texts(marker_all=True)
    tx["m034"] = "{speed:05}" + "Far " * 4500 + "{end}"   # 18 KB: bank $05 overflows, the rest goes far
    data, _ = build_with(tx)
    return data, tx


def build_with(tx):
    import build, textdb
    from tbl import Table
    build.check_rom.check()
    orig, _ = textdb.load()
    rom = build.Rom(orig)
    build.apply_engine(rom)
    build.build_text(rom, Table.load(build.EN_TBL), tx, build.Far(rom))
    return bytes(rom.data), rom.writes


def file_off(a):
    return ((a >> 16) & 0x7F) << 15 | (a & 0x7FFF)


def read(rom, t, off):
    """Decode a string, following a leading {far} stub."""
    text, _ = t.decode(rom, off, maxlen=1 << 15)
    if text.startswith("{far:"):
        a = bytes.fromhex(text[5:11])
        return t.decode(rom, file_off(a[0] | a[1] << 8 | a[2] << 16), maxlen=1 << 15)[0]
    return text


def test_hooks(marker):
    rom, _ = marker
    assert rom[0x39BBF:0x39BC3] == bytes([0x5C, 0x00, 0x80, 0x0F])     # $07:9BBF JML vwf_draw
    assert rom[0x39A39] == 0x5C and rom[0x0746B] == 0x5C              # FF/F8 code, name slot copy
    assert rom[0x074D7:0x074D9] == bytes([0x00, 0x8E]) and rom[0x074E3] == 0x0F   # side names at $0F:8E00


def test_every_pointer_reaches_its_text(marker):
    import build, textdb
    from tbl import Table
    rom, tx = marker
    t = Table.load(build.EN_TBL)
    orig = textdb.ROM.read_bytes()
    jt = Table.load(textdb.JP_TBL)
    for i in range(textdb.MAIN_COUNT):
        sid = "m%03X" % i
        assert read(rom, t, textdb.bank_off(textdb.MAIN_TABLE, textdb.ptr(rom, textdb.MAIN_TABLE + 2 * i))) == tx[sid]
    for sid, _, _ in textdb.sub_strings(orig, jt):
        i = int(sid[1:], 16)
        assert read(rom, t, textdb.bank_off(textdb.SUB_TABLE, textdb.ptr(rom, textdb.SUB_TABLE + 2 * i))) == tx[sid]
    names = {off: sid for sid, off, _ in textdb.name_strings(orig, jt)}
    for name, table, count in textdb.NAME_TABLES:
        for i in range(count):
            sid = names[textdb.bank_off(table, textdb.ptr(orig, table + 2 * i))]
            off = textdb.bank_off(table, textdb.ptr(rom, table + 2 * i))
            assert t.decode(rom, off + 1)[0] == tx[sid], sid
    for sid, off in build.SIDE_FAR.items():
        assert t.decode(rom, off + 1)[0] == tx[sid]


def test_far_strings_stay_in_their_bank(marker):
    """The text pointer wraps inside its bank, so a far string must end in the bank it starts in."""
    import build, textdb
    from tbl import Table
    rom, _ = marker
    t = Table.load(build.EN_TBL)
    far = 0
    for i in range(textdb.MAIN_COUNT):
        off = textdb.bank_off(textdb.MAIN_TABLE, textdb.ptr(rom, textdb.MAIN_TABLE + 2 * i))
        if rom[off] == 0xF8:
            start = file_off(rom[off + 1] | rom[off + 2] << 8 | rom[off + 3] << 16)
            _, n = t.decode(rom, start, maxlen=1 << 15)
            assert start >> 15 == (start + n - 1) >> 15 and start >> 15 != 0x05
            far += 1
    assert far


def test_blank_strings_kept(marker):
    """Control-code-only strings (empty boxes, empty name slots) are not text: never marked or translated."""
    import build
    _, tx = marker
    blank = [r for r in build.rows() if build.blank(r["jp"])]
    assert len(blank) == 26 and all(tx[r["id"]] == r["jp"] for r in blank)


def test_gfxtext_decodes_through_directory():
    """Every redrawn block, in place or relocated, decompresses through the bank directory to its new tiles, and
    differs from the JP only inside its text rect."""
    import gfx, gfxtext
    orig = ROM.read_bytes()
    rom = bytearray(orig)
    for off, data, _ in gfxtext.writes(orig):
        rom[off:off + len(data)] = data
    for bank, slot, texts, base, new in gfxtext.blocks(orig):
        d = gfx.lorom(bank, 0x8000 + 4 * slot)
        src = orig[d] | orig[d + 1] << 8
        for b, s, o, n in gfx.blocks(orig):     # every slot on this stream (08_30 shares 08_31's)
            e = gfx.lorom(b, 0x8000 + 4 * s)
            if b == bank and orig[e] | orig[e + 1] << 8 == src:
                tiles, _ = gfx.decompress(rom, gfx.lorom(b, rom[e] | rom[e + 1] << 8), n, 2)
                assert tiles == new[:16 * n], (b, s)
        touched = set()
        for kind, _ in texts:
            k, g = gfxtext.KINDS[kind], gfxtext.grid(kind)
            x0, y0, x1, y1 = k["rect"]
            if "frame" in k:
                y0, y1 = y0 - 1, y1 + 1
            a, b = gfxtext.to_pixels(base, g), gfxtext.to_pixels(new, g)
            assert all(a[y][x] == b[y][x] for y in range(len(a)) for x in range(len(a[0]))
                       if not (x0 <= x < x1 and y0 <= y < y1)), (bank, slot, kind)
            touched |= {t for row in g for t in row}
        assert all(base[16 * t:16 * t + 16] == new[16 * t:16 * t + 16]
                   for t in range(len(new) // 16) if t not in touched), (bank, slot)
