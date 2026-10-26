"""gfxtext.py: English for text drawn as graphics blocks (docs/re/graphics.md G1-G3, G13) for build.py.

Each entry redraws one compressed 2bpp block: the block is decompressed, its text rect cleared to the background
index and the English drawn in Ark Pixel 10px (fonts/, docs/fonts.md; space 3 px), with an outline index where the
JP had one; pixels outside the rect stay as they were. The block is recompressed (gfx.compress) and written over the
old one when it fits, else into its bank's 0xFF tail with the bank directory entry repointed.
    python -X utf8 tools/gfxtext.py [--png out.png]   # check every label fits; sheet of the English blocks
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font  # noqa: E402
import gfx  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BDF = ROOT / "fonts" / "ark-pixel-10px-proportional-latin.bdf"
SPACE = 3
TAIL = {8: (0x46E38, 0x48000), 9: (0x4E079, 0x50000)}     # 0xFF runs at the bank ends (trap-tested, engine.md)

# cols: tiles per row (2 rows); rect: x0, y0, x1, y1 the text may use; margin: left pad, None = centred.
# Plates: the game shows the left 64 px (JP ink spans columns 3-62). Banners: frame 2/1 around a fill of 3,
# glyph ink 1 with an outline of 2.
KINDS = {
    "plate": dict(cols=9, rect=(0, 0, 64, 16), bg=0, ink=1, outline=None, margin=3),
    "banner": dict(cols=15, rect=(2, 2, 118, 14), bg=3, ink=1, outline=2, margin=None, frame=1),
    "wide": dict(cols=26, rect=(2, 2, 206, 14), bg=1, ink=3, outline=2, margin=None, frame=3),   # briefing bar
}
# frame: the JP outlines spill into the frame rows just above and below the rect; those rows are redrawn in it.

# (bank, slot) -> (kind, names.json id or literal). Plate order read off the JP plates.
GFX = {**{(8, 0x3D + i): ("plate", f"officer_emp_{i:02d}") for i in range(19)},
       **{(8, 0x50 + i): ("plate", f"officer_emp_{19 + i:02d}") for i in range(9)},
       (8, 0x59): ("plate", "officer_fpa_00"),
       **{(8, 0x5A + i): ("plate", f"officer_fpa_{2 + i:02d}") for i in range(22)},
       (8, 0x70): ("plate", "Officer")}     # 一般将校: a generic officer
SHIPS = ["emp_00", "emp_01", "emp_02", "emp_03", "emp_04", "emp_05", "emp_06", "emp_09", "emp_10", "emp_07",
         "emp_12", "emp_14", "emp_13", "emp_08", "Wilhelmina", "emp_11", "emp_16", "fpa_10", "fpa_13", "fpa_11",
         "fpa_02", "fpa_12", "fpa_09", "fpa_08", "fpa_07", "fpa_03", "fpa_06", "fpa_04", "fpa_01", "fpa_16",
         "fpa_15", "fpa_17", "fpa_20", "fpa_05", "fpa_14", "fpa_18", "fpa_19"]
GFX.update({(9, i): ("plate", "ship_" + s if "_" in s else s) for i, s in enumerate(SHIPS)})
BANNERS = ["Battle of Astarte", "Battle of Amritsar", "Battle of Geiersburg", "Battle of Rantemario",
           "Battle of Raigal-Tripra", "Battle of Tassili", "Battle of Vermillion",
           "1. In Eternal Night", "2. The Vulture Soars", "3. Twilight of the Gods"]
GFX.update({(9, 0x25 + i): ("banner", t) for i, t in enumerate(BANNERS)})
GFX.update({(8, 0x37 + i): ("wide", t) for i, t in enumerate(BANNERS[1:7])})
GFX[8, 0x74] = ("wide", BANNERS[0])


def names():
    rows = json.loads((ROOT / "script" / "names.json").read_text(encoding="utf-8"))
    return {r["id"]: r["en"].replace("{end}", "") for r in rows if r.get("en")}


def to_pixels(tiles, cols):
    """2bpp tiles (2 rows of cols) -> 16 rows of colour indices."""
    px = [[0] * (cols * 8) for _ in range(16)]
    for t in range(2 * cols):
        for r in range(8):
            p0, p1 = tiles[t * 16 + 2 * r], tiles[t * 16 + 2 * r + 1]
            for c in range(8):
                px[(t // cols) * 8 + r][(t % cols) * 8 + c] = (p0 >> (7 - c) & 1) | (p1 >> (7 - c) & 1) << 1
    return px


def to_tiles(px, cols):
    out = bytearray()
    for t in range(2 * cols):
        for r in range(8):
            row = px[(t // cols) * 8 + r][(t % cols) * 8:(t % cols) * 8 + 8]
            out += bytes([sum((v & 1) << (7 - c) for c, v in enumerate(row)),
                          sum((v >> 1 & 1) << (7 - c) for c, v in enumerate(row))])
    return bytes(out)


def ink(text, glyphs):
    """Set of (x, y) ink pixels, x from 0, y with the cap height of H centred on row 7.5."""
    hrows = [r for r, v in enumerate(glyphs[ord("H")][0]) if v]
    shift = round(7.5 - (hrows[0] + hrows[-1]) / 2)
    pts, x = set(), 0
    for ch in text:
        cell, adv = glyphs[ord(ch)]
        pts |= {(x + c, r + shift) for r, v in enumerate(cell) for c in range(16) if v >> (15 - c) & 1}
        x += SPACE if ch == " " else adv
    return pts


def draw(kind, text, base, glyphs):
    """base tiles -> new tiles with text in the kind's rect; SystemExit if it doesn't fit."""
    k = KINDS[kind]
    x0, y0, x1, y1 = k["rect"]
    px = to_pixels(base, k["cols"])
    pts = ink(text, glyphs)
    pad = 1 if k["outline"] is not None else 0
    w = max(x for x, _ in pts) + 1
    dx = x0 + pad + (min(k["margin"], x1 - x0 - 2 * pad - w) if k["margin"] is not None
                     else (x1 - x0 - 2 * pad - w) // 2)
    pts = {(x + dx, y) for x, y in pts}
    edge = {(x + i, y + j) for x, y in pts for i in (-1, 0, 1) for j in (-1, 0, 1)} if pad else pts
    if w + 2 * pad > x1 - x0 or any(not (x0 <= x < x1 and y0 <= y < y1) for x, y in edge):
        raise SystemExit(f"{kind} {text!r}: {w} px, room for {x1 - x0 - 2 * pad}")
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[y][x] = k["ink"] if (x, y) in pts else k["outline"] if (x, y) in edge else k["bg"]
    if "frame" in k:
        for x in range(x0, x1):
            px[y0 - 1][x] = px[y1][x] = k["frame"]
    return to_tiles(px, k["cols"])


def blocks(orig):
    """[(bank, slot, text, original tiles, new tiles)] for every entry."""
    glyphs, nm = font.load(BDF), names()
    out = []
    for (bank, slot), (kind, src) in GFX.items():
        d = gfx.lorom(bank, 0x8000 + 4 * slot)
        n = orig[d + 2] | orig[d + 3] << 8
        assert n == 2 * KINDS[kind]["cols"], (bank, slot, n)
        base, _ = gfx.decompress(orig, gfx.lorom(bank, orig[d] | orig[d + 1] << 8), n, 2)
        text = nm.get(src, src)
        out.append((bank, slot, text, base, draw(kind, text, base, glyphs)))
    return out


def writes(orig):
    """[(file offset, bytes, by)]: each compressed block, plus its directory entry when relocated."""
    tail = {b: list(r) for b, r in TAIL.items()}
    out = []
    for bank, slot, _, _, new in blocks(orig):
        d = gfx.lorom(bank, 0x8000 + 4 * slot)
        off = gfx.lorom(bank, orig[d] | orig[d + 1] << 8)
        _, used = gfx.decompress(orig, off, len(new) // 16, 2)
        data = gfx.compress(new, 2)
        by = "gfxtext:%02X_%02X" % (bank, slot)
        if len(data) > used:
            off, tail[bank][0] = tail[bank][0], tail[bank][0] + len(data)
            if tail[bank][0] > tail[bank][1]:
                raise SystemExit(f"{by}: bank ${bank:02X} tail full")
            addr = 0x8000 | off & 0x7FFF
            out.append((d, bytes([addr & 0xFF, addr >> 8]), by + ":dir"))
        out.append((off, data, by))
    return out


def main():
    orig = gfx.ROM.read_bytes()
    w = writes(orig)
    print(f"{len(GFX)} blocks, {sum(by.endswith(':dir') for _, _, by in w)} relocated")
    if sys.argv[1:2] == ["--png"]:
        from PIL import Image
        bl = blocks(orig)
        W = max(len(new) // 32 * 8 for *_, new in bl)
        img = Image.new("L", (2 * (W + 8), (len(bl) + 1) // 2 * 40), 128)
        for k, (*_, base, new) in enumerate(bl):
            cols = len(new) // 32
            for j, tiles in enumerate((base, new)):
                for y, row in enumerate(to_pixels(tiles, cols)):
                    for x, v in enumerate(row):
                        img.putpixel(((k % 2) * (W + 8) + x, (k // 2) * 40 + j * 18 + y), 255 - 85 * v)
        img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(sys.argv[2])


if __name__ == "__main__":
    main()
