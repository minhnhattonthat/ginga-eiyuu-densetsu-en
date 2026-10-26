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
    # title character buttons, 08_31 (BG3 tile = block tile + $80): only each label's own tiles; the frame
    # tiles 59/65/66/72 and the blank 76/80 are shared by both buttons
    "btn_rein": dict(grid=[[60, 61, 62, 63, 64], [67, 68, 69, 70, 71]], rect=(0, 2, 40, 14), bg=2, ink=3,
                     outline=1, margin=None),
    "btn_yang": dict(grid=[[73, 74, 75], [77, 78, 79]], rect=(0, 2, 24, 14), bg=2, ink=3, outline=1, margin=None),
}
# grid: rows of block tile numbers (default: cols x 2, the whole block).
# frame: the JP outlines spill into the frame rows just above and below the rect; those rows are redrawn in it.

# (bank, slot) -> [(kind, names.json id or literal)]. Plate order read off the JP plates.
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
GFX = {k: [v] for k, v in GFX.items()}
GFX[8, 0x31] = [("btn_rein", "officer_emp_00"), ("btn_yang", "officer_fpa_00")]


def names():
    rows = json.loads((ROOT / "script" / "names.json").read_text(encoding="utf-8"))
    return {r["id"]: r["en"].replace("{end}", "") for r in rows if r.get("en")}


def grid(kind):
    """Rows of block tile numbers the kind's image is made of."""
    k = KINDS[kind]
    return k.get("grid") or [list(range(k["cols"])), list(range(k["cols"], 2 * k["cols"]))]


def to_pixels(tiles, g):
    """2bpp block tiles -> rows of colour indices of the image laid out by grid g."""
    px = [[0] * (len(g[0]) * 8) for _ in range(8 * len(g))]
    for gy, row in enumerate(g):
        for gx, t in enumerate(row):
            for r in range(8):
                p0, p1 = tiles[t * 16 + 2 * r], tiles[t * 16 + 2 * r + 1]
                for c in range(8):
                    px[gy * 8 + r][gx * 8 + c] = (p0 >> (7 - c) & 1) | (p1 >> (7 - c) & 1) << 1
    return px


def to_tiles(px, g, tiles):
    """Block tiles with the grid's tiles replaced by the image px."""
    out = bytearray(tiles)
    for gy, row in enumerate(g):
        for gx, t in enumerate(row):
            for r in range(8):
                line = px[gy * 8 + r][gx * 8:gx * 8 + 8]
                out[t * 16 + 2 * r] = sum((v & 1) << (7 - c) for c, v in enumerate(line))
                out[t * 16 + 2 * r + 1] = sum((v >> 1 & 1) << (7 - c) for c, v in enumerate(line))
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
    """block tiles -> new block tiles with text in the kind's rect; SystemExit if it doesn't fit."""
    k = KINDS[kind]
    x0, y0, x1, y1 = k["rect"]
    px = to_pixels(base, grid(kind))
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
    return to_tiles(px, grid(kind), base)


def blocks(orig):
    """[(bank, slot, [(kind, text)], original tiles, new tiles)] for every block."""
    glyphs, nm = font.load(BDF), names()
    out = []
    for (bank, slot), labels in GFX.items():
        d = gfx.lorom(bank, 0x8000 + 4 * slot)
        n = orig[d + 2] | orig[d + 3] << 8
        base, _ = gfx.decompress(orig, gfx.lorom(bank, orig[d] | orig[d + 1] << 8), n, 2)
        new, texts = base, []
        for kind, src in labels:
            assert max(map(max, grid(kind))) < n, (bank, slot, n)
            texts.append((kind, nm.get(src, src)))
            new = draw(kind, texts[-1][1], new, glyphs)
        out.append((bank, slot, texts, base, new))
    return out


def writes(orig):
    """[(file offset, bytes, by)]: each compressed block, plus its directory entries (every slot sharing the
    stream, e.g. 08_30 = the first 20 tiles of 08_31) when relocated."""
    tail = {b: list(r) for b, r in TAIL.items()}
    dirs = gfx.blocks(orig)
    out = []
    for bank, slot, _, _, new in blocks(orig):
        d = gfx.lorom(bank, 0x8000 + 4 * slot)
        off = gfx.lorom(bank, orig[d] | orig[d + 1] << 8)
        _, used = gfx.decompress(orig, off, len(new) // 16, 2)
        data = gfx.compress(new, 2)
        by = "gfxtext:%02X_%02X" % (bank, slot)
        if len(data) > used:
            old, (off, tail[bank][0]) = off, (tail[bank][0], tail[bank][0] + len(data))
            if tail[bank][0] > tail[bank][1]:
                raise SystemExit(f"{by}: bank ${bank:02X} tail full")
            addr = 0x8000 | off & 0x7FFF
            for b, s, o, _ in dirs:
                if b == bank and o == old:
                    out.append((gfx.lorom(b, 0x8000 + 4 * s), bytes([addr & 0xFF, addr >> 8]), by + ":dir"))
        out.append((off, data, by))
    return out


def main():
    orig = gfx.ROM.read_bytes()
    w = writes(orig)
    print(f"{len(GFX)} blocks, {sum(by.endswith(':dir') for _, _, by in w)} directory entries repointed")
    if sys.argv[1:2] == ["--png"]:     # JP above English, one image per label
        from PIL import Image
        imgs = [(to_pixels(base, grid(kind)), to_pixels(new, grid(kind)))
                for *_, texts, base, new in blocks(orig) for kind, _ in texts]
        W = max(len(a[0]) for a, _ in imgs)
        img = Image.new("L", (2 * (W + 8), (len(imgs) + 1) // 2 * 40), 128)
        for k, pair in enumerate(imgs):
            for j, px in enumerate(pair):
                for y, row in enumerate(px):
                    for x, v in enumerate(row):
                        img.putpixel(((k % 2) * (W + 8) + x, (k // 2) * 40 + j * 18 + y), 255 - 85 * v)
        img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(sys.argv[2])


if __name__ == "__main__":
    main()
