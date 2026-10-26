import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM = ROOT / "rom" / "Ginga Eiyuu Densetsu (Japan).sfc"
pytestmark = pytest.mark.skipif(not ROM.exists(), reason="no ROM")


def test_identity_build():
    import build
    data, _ = build.build("identity-no-such-field")
    assert data == ROM.read_bytes()


def test_repack_moves_strings():
    """Longer strings shift everything after them; every pointer must still reach its own text."""
    import build, textdb
    orig, t = textdb.load()
    tx = build.texts("identity-no-such-field")
    # Name tables have no slack yet (relocation is phase 5), so their edits keep the table's total size.
    edits = {"m000": "ＡＢＣ" * 20 + "{end}", "s06": "ＡＢ{end}", "officer_fpa_00": "ＡＢＣＤ{end}",
             "officer_fpa_01": "ＡＢＣ{end}", "rank_00": "Ａ{end}"}
    tx.update(edits)
    rom = build.Rom(orig)
    build.build_text(rom, t, tx)
    new = bytes(rom.data)
    got = {sid: t.decode(new, off)[0] for sid, off, _ in textdb.main_strings(new, t)}
    got.update({sid: t.decode(new, off)[0] for sid, off, _ in textdb.sub_strings(new, t)})
    got.update({sid: t.decode(new, off + 1, n - 1)[0] for sid, off, n in textdb.name_strings(new, t)})
    assert got == tx


def test_gfx_compressor_roundtrip():
    import gfx
    rom = ROM.read_bytes()
    exact = 0
    for (bank, slot, off, n), p in zip(gfx.blocks(rom), gfx.planes_of(rom, gfx.blocks(rom))):
        for q in ([p] if p else [2, 3]):
            tiles, used = gfx.decompress(rom, off, n, q)
            packed = gfx.compress(tiles, q)
            assert gfx.decompress(packed, 0, n, q) == (tiles, len(packed))
            exact += packed == rom[off:off + used]
    assert exact >= 355   # 0D_0A stores a redundant zero row; every other block recompresses byte for byte


def test_title_compressor_roundtrip():
    import gfx
    import gfxtext
    rom = ROM.read_bytes()
    tiles, used = gfx.decompress_title(rom, gfxtext.TITLE_TILES, gfxtext.TITLE_COUNT)
    assert gfx.compress_title(tiles) == rom[gfxtext.TITLE_TILES:gfxtext.TITLE_TILES + used]
