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
TAIL = {8: (0x46E38, 0x48000), 9: (0x4E079, 0x50000), 0xE: (0x74084, 0x78000)}   # 0xFF bank ends (trap-tested)

# cols: tiles per row (2 rows); rect: x0, y0, x1, y1 the text may use; margin: left pad, None = centred.
# Plates: the fleet panel shows the left 64 px (JP ink spans columns 3-62), the formation panel only 56: text keeps
# to 56 (a name wider than that is drawn 1 px tighter per letter). Banners: frame 2/1 around a fill of 3,
# glyph ink 1 with an outline of 2.
KINDS = {
    "plate": dict(cols=9, rect=(0, 0, 56, 16), bg=0, ink=1, outline=None, margin=3, squeeze=True),
    "banner": dict(cols=15, rect=(2, 2, 118, 14), bg=3, ink=1, outline=2, margin=None, frame=1),
    "wide": dict(cols=26, rect=(2, 2, 206, 14), bg=1, ink=3, outline=2, margin=None, frame=3),   # briefing bar
    # title character buttons, 08_31 (BG3 tile = block tile + $80): only each label's own tiles; the frame
    # tiles 59/65/66/72 and the blank 76/80 are shared by both buttons
    "btn_rein": dict(grid=[[60, 61, 62, 63, 64], [67, 68, 69, 70, 71]], rect=(0, 2, 40, 14), bg=2, ink=3,
                     outline=1, margin=None),
    "btn_yang": dict(grid=[[73, 74, 75], [77, 78, 79]], rect=(0, 2, 24, 14), bg=2, ink=3, outline=1, margin=None),
    # command help label: the JP block is 3x2; asm/engine.asm shows slot 7 as 6x2, so the block is rebuilt at
    # 12 tiles (border: 1 px frame of that index, the rest bg) and its directory tile count raised
    "label": dict(cols=6, rect=(1, 1, 47, 15), bg=3, ink=2, outline=None, margin=None, border=2),
    "shiptype": dict(cols=6, rect=(0, 0, 48, 16), bg=0, ink=1, outline=None, margin=1, tiny=True),
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
LABELS = {0x0F: "Defend", 0x10: "Join", 0x11: "Move", 0x12: "End", 0x13: "System", 0x14: "Fleet", 0x15: "Save",
          0x16: "All Sides", 0x17: "Focus", 0x18: "Retreat", 0x27: "Attack", 0x28: "Detach", 0x29: "Deploy",
          0x2A: "Info", 0x2B: "Continue", 0x2C: "Group", 0x2D: "Auto", 0x2E: "Animation", 0x2F: "Front",
          0x30: "Standby", 0x31: "Priority"}
GFX.update({(0xE, s): [("label", t)] for s, t in LABELS.items()})

# Ranks (G4): bank-$02 maps 29-36 ($02:8054 pointer table: width byte + 2 rows of map words $0900 + n = BG3 tile
# $100 + n) draw tiles 0-49 of 08_35 (loaded at $100; the rest of the sheet is icons). English won't fit 50 tiles
# at two tile rows, so each rank is one tile row of 3x5 caps (TINY, ink 1) over a shared blank tile, and the maps
# move to RANK_MAPS (end of the bank $02 tail) with their new widths. VRAM after the sheet is not free (result
# screens draw at $1BB+), so the tile count stays 178.
RANK_SHEET, RANK_TILES, RANK_ROW = (8, 0x35), 50, 3        # glyph rows 3-7 of the top tile
RANK_TABLE, RANK_MAPS = 0x10054, (0x17F00, 0x18000)
RANKS = {29: "COMMANDER", 30: "FLEET/ADMIRAL", 31: "SENIOR/ADMIRAL", 32: "ADMIRAL", 33: "VICE ADMIRAL",
         34: "REAR ADMIRAL", 35: "COMMODORE", 36: "LIEUTENANT"}
TINY = {"A": "010 101 111 101 101", "C": "011 100 100 100 011", "D": "110 101 101 101 110",
        "E": "111 100 110 100 111", "F": "111 100 110 100 100", "I": "1 1 1 1 1", "L": "100 100 100 100 111",
        "M": "10001 11011 10101 10001 10001", "N": "1001 1101 1011 1001 1001", "O": "010 101 101 101 010",
        "R": "110 101 110 101 101", "S": "011 100 010 001 110", "T": "111 010 010 010 010",
        "U": "101 101 101 101 111", "V": "101 101 101 101 010", " ": "00 00 00 00 00",
        "B": "110 101 110 101 110", "H": "101 101 111 101 101", "P": "110 101 110 100 100",
        "Y": "101 101 010 010 010"}
# Ship-type labels (G8): ids $184-$18B, each 6x2 tiles loaded at BG3 $210 and drawn by $00:CD0E; $21C+ is used
# by other screens, so they stay 48 px: 3x5 caps, "/" = second line.
SHIPTYPES = ["BATTLESHIP", "CRUISER", "CARRIER", "DESTROYER", "FORTRESS", "TRANSPORT", "ASTEROID",
             "FAST/BATTLESHIP"]
GFX.update({(0xE, 0x37 + i): [("shiptype", t)] for i, t in enumerate(SHIPTYPES)})


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


def ink(text, glyphs, tight=0):
    """Set of (x, y) ink pixels, x from 0, y with the cap height of H centred on row 7.5; tight = px less per advance."""
    hrows = [r for r, v in enumerate(glyphs[ord("H")][0]) if v]
    shift = round(7.5 - (hrows[0] + hrows[-1]) / 2)
    pts, x = set(), 0
    for ch in text:
        cell, adv = glyphs[ord(ch)]
        pts |= {(x + c, r + shift) for r, v in enumerate(cell) for c in range(16) if v >> (15 - c) & 1}
        x += SPACE if ch == " " else adv - tight
    return pts


def draw(kind, text, base, glyphs):
    """block tiles -> new block tiles with text in the kind's rect; SystemExit if it doesn't fit."""
    k = KINDS[kind]
    x0, y0, x1, y1 = k["rect"]
    px = to_pixels(base, grid(kind))
    pts = tiny_ink(text) if k.get("tiny") else ink(text, glyphs)
    pad = 1 if k["outline"] is not None else 0
    w = max(x for x, _ in pts) + 1
    if k.get("squeeze") and w > x1 - x0:
        pts = ink(text, glyphs, 1)
        w = max(x for x, _ in pts) + 1
    dx =x0 + pad + (min(k["margin"], x1 - x0 - 2 * pad - w) if k["margin"] is not None
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
            k = KINDS[kind]
            if "border" in k:       # a fresh block: frame + fill
                w, b = 8 * k["cols"], k["border"]
                px = [[b if y in (0, 15) or x in (0, w - 1) else k["bg"] for x in range(w)] for y in range(16)]
                new = to_tiles(px, grid(kind), bytes(32 * k["cols"]))
                n = 2 * k["cols"]
            assert max(map(max, grid(kind))) < n, (bank, slot, n)
            texts.append((kind, nm.get(src, src)))
            new = draw(kind, texts[-1][1], new, glyphs)
        out.append((bank, slot, texts, base, new))
    return out


def tiny_ink(text):
    """Ink points for TINY caps, lines split at "/", each centred on the widest, the block centred on row 7.5."""
    lines = [tiny(t, pad=0) for t in text.split("/")]
    wide = max(w for _, w in lines)
    top = round(7.5 - (7 * len(lines) - 3) / 2)
    return {(x + (wide - w) // 2, top + 7 * n + r) for n, (rows, w) in enumerate(lines)
            for r, xs in enumerate(rows) for x in xs}


def tiny(text, pad=2):
    """Rows (5) of ink columns for TINY caps text, 1 px between letters; pad = left margin (ranks: 2 px clear of
    the rank icon on their left)."""
    rows, x = [[] for _ in range(5)], pad
    for ch in text:
        g = TINY[ch].split()
        for r, bits in enumerate(g):
            rows[r] += [x + c for c, b in enumerate(bits) if b == "1"]
        x += len(g[0]) + 1
    return rows, x - 1


def ranks(orig):
    """(new 08_35 tiles, {map id: template bytes}) for RANKS: one tile row each, tile RANK_TILES - 1 blank."""
    d = gfx.lorom(RANK_SHEET[0], 0x8000 + 4 * RANK_SHEET[1])
    n = orig[d + 2] | orig[d + 3] << 8
    tiles, _ = gfx.decompress(orig, gfx.lorom(RANK_SHEET[0], orig[d] | orig[d + 1] << 8), n, 2)
    tiles, blank, maps, done = bytearray(tiles), RANK_TILES - 1, {}, {}
    tiles[16 * blank:16 * blank + 16] = bytes(16)

    def put(text, row):
        """tile ids holding text at glyph rows row..row+4 of their tile (same text and row share tiles)"""
        if (text, row) not in done:
            rows, w = tiny(text)
            nxt = sum(map(len, done.values()))
            ids = list(range(nxt, nxt + (w + 7) // 8))
            if ids and ids[-1] >= blank:
                raise SystemExit(f"ranks need {ids[-1] + 2} tiles, the sheet has {RANK_TILES}")
            for k, t in enumerate(ids):
                tiles[16 * t:16 * t + 16] = bytes(16)
                for r, xs in enumerate(rows):
                    tiles[16 * t + 2 * (row + r)] = sum(0x80 >> (x - 8 * k) for x in xs if 8 * k <= x < 8 * k + 8)
            done[text, row] = ids
        return done[text, row]

    for i, text in RANKS.items():
        top, _, bot = text.partition("/")   # two lines: rows 2-6 of the top tile, 1-5 of the bottom one
        t, b = (put(top, 2), put(bot, 1)) if bot else (put(top, RANK_ROW), [])
        cols = max(len(t), len(b))
        if cols > 6:   # the panel clears 6 columns from the plate's start: a 7th is left on screen
            raise SystemExit(f"rank {text!r}: {cols} tiles, room for 6")
        t, b = t + [blank] * (cols - len(t)), b + [blank] * (cols - len(b))
        maps[i] = bytes([cols]) + b"".join((0x0900 | n).to_bytes(2, "little") for n in t + b)
    return bytes(tiles), maps


# Title screen (G11 logo, G16 copyright): $13:8602 loads TITLE_COUNT tiles from $13:A9F2 to BG1 VRAM 0 with
# $00:86AD (gfx.decompress_title); raw 32-word map rows follow: logo $13:BD39 (rows 4-8, tiles 1-$91 in order,
# cols 1-29), copyright $13:BE79 (rows 19-26, tiles $92-$127 reused across lines, palette 4), BG2 stars $13:C079
# (tiles $128-$13C). The copyright needs more tiles than it had, so the new ones go after the stars (VRAM tiles
# $13D-$1EF are unused there) and the stream moves to the bank $13 0xFF tail.
TITLE_TILES, TITLE_COUNT, TITLE_COPY_MAP, TITLE_TAIL = 0x9A9F2, 0x13D, 0x9BE79, (0x9D30E, 0xA0000)
TITLE_LDX, TITLE_LDY = 0x98602, 0x9860E          # LDX #$A9F2 / LDY #$013D at $13:8602 / $13:860E
LOGO = ("LEGEND OF THE", "GALACTIC HEROES")
COPYRIGHT = ["\x001991 Yoshiki Tanaka, Tokuma Shoten,", "Tokuma Japan Communications,", "Kitty Film, TV Tokyo",
             "\x001992 Tokuma Shoten Intermedia"]    # \x00 = the JP © (16x16, tiles $F6/$F7 over $F8/$F9)


def title_px(tiles, t):
    """Rows of colour indices of 4bpp tile t."""
    b = tiles[32 * t:32 * t + 32]
    return [[(b[2 * y] >> 7 - x & 1) | (b[2 * y + 1] >> 7 - x & 1) << 1 | (b[16 + 2 * y] >> 7 - x & 1) << 2
             for x in range(8)] for y in range(8)]


def title_tile(px, x0, y0):
    """The 8x8 block of image px at (x0, y0) as a 4bpp tile (indices < 8)."""
    out = bytearray(32)
    for y in range(8):
        for x in range(8):
            v = px[y0 + y][x0 + x]
            out[2 * y] |= (v & 1) << 7 - x
            out[2 * y + 1] |= (v >> 1 & 1) << 7 - x
            out[16 + 2 * y] |= (v >> 2 & 1) << 7 - x
    return bytes(out)


def fit_pts(pts):
    """pts moved to x, y >= 0; (pts, width, height)."""
    mx, my = min(x for x, _ in pts), min(y for _, y in pts)
    pts = {(x - mx, y - my) for x, y in pts}
    return pts, max(x for x, _ in pts) + 1, max(y for _, y in pts) + 1


def logo_image(base):
    """232x40 image for logo tiles 1-$91: LOGO in Ark Pixel 10px over 12px doubled, both emboldened 1 px, each ink
    row in the fill index (1-3) the JP logo used most on that row, with a green extrusion down-right (small line 1 px
    of 4, big line 4 then 5)."""
    jp = [[v for row in range(29) for v in title_px(base, 1 + 29 * (y // 8) + row)[y % 8]] for y in range(40)]
    fill = [max((1, 2, 3), key=[sum(1 for v in r if v == i) for i in range(4)].__getitem__) for r in jp]
    small, sw, sh = fit_pts({(x + dx, y) for x, y in ink(LOGO[0], font.load(BDF)) for dx in (0, 1)})
    big, bw, bh = fit_pts({(2 * x + dx, 2 * y + dy) for x, y in ink(LOGO[1], font.load())
                           for dx in (0, 1, 2) for dy in (0, 1)})
    gap = 3
    top = (40 - (sh + gap + bh + 2)) // 2
    if max(sw, bw) + 2 > 232 or top < 1:
        raise SystemExit(f"logo: {max(sw, bw)}x{sh + gap + bh} px, room for 230x37")
    small = {(x + (232 - sw) // 2, y + top) for x, y in small}
    big = {(x + (232 - bw) // 2, y + top + sh + gap) for x, y in big}
    px = [[0] * 232 for _ in range(40)]
    for pts, steps in ((big, ((2, 5), (1, 4))), (small, ((1, 4),))):
        for d, idx in steps:
            for x, y in pts:
                px[y + d][x + d] = idx
    for x, y in small | big:
        px[y][x] = fill[y]
    return px


def copyright_image(base):
    """224x64 image of COPYRIGHT, one 16 px line each, Ark Pixel 12px ink 1; lines 2-3 indented past the ©."""
    glyphs = font.load()
    cmark = [a + b for t in (0xF6, 0xF8) for a, b in zip(title_px(base, t), title_px(base, t + 1))]
    px = [[0] * 224 for _ in range(64)]
    for n, line in enumerate(COPYRIGHT):
        x = 16
        if line.startswith("\x00"):
            for y in range(16):
                px[16 * n + y][:16] = cmark[y]
            x, line = 17, line[1:]
        pts = ink(line, glyphs)
        if x + max(p for p, _ in pts) >= 224:
            raise SystemExit(f"copyright line {n + 1} too wide")
        for p, y in pts:
            px[16 * n + y][x + p] = 1
    return px


def title(orig):
    """[(file offset, bytes, by)] for the title screen."""
    assert orig[TITLE_LDX:TITLE_LDX + 3] == b"\xa2\xf2\xa9" and orig[TITLE_LDY:TITLE_LDY + 3] == b"\xa0\x3d\x01"
    base, used = gfx.decompress_title(orig, TITLE_TILES, TITLE_COUNT)
    assert TITLE_TILES + used == 0x9BD39     # the logo map follows the stream
    tiles = bytearray(base) + bytes(32 * (0x1F0 - TITLE_COUNT))
    logo = logo_image(base)
    for t in range(1, 0x92):
        tiles[32 * t:32 * t + 32] = title_tile(logo, 8 * ((t - 1) % 29), 8 * ((t - 1) // 29))
    cp = copyright_image(base)
    free = list(range(0x92, 0x128)) + list(range(TITLE_COUNT, 0x1F0))
    tiles[32 * 0x92:32 * 0x128] = bytes(32 * (0x128 - 0x92))
    ids, cmap = {}, bytearray()
    for row in range(8):
        words = [0x1000] * 2
        for col in range(28):
            tile = title_tile(cp, 8 * col, 8 * row)
            if any(tile):
                if tile not in ids:
                    if not free:
                        raise SystemExit("copyright: out of VRAM tiles ($92-$127, $13D-$1EF)")
                    ids[tile] = t = free.pop(0)
                    tiles[32 * t:32 * t + 32] = tile
                words.append(0x1000 | ids[tile])
            else:
                words.append(0x1000)
        cmap += b"".join(w.to_bytes(2, "little") for w in words + [0x1000] * 2)
    count = max([TITLE_COUNT - 1] + list(ids.values())) + 1
    data = gfx.compress_title(bytes(tiles[:32 * count]))
    if TITLE_TAIL[0] + len(data) > TITLE_TAIL[1]:
        raise SystemExit("title tiles overflow the bank $13 tail")
    addr = 0x8000 | TITLE_TAIL[0] & 0x7FFF
    return [(TITLE_TAIL[0], data, "title:tiles"), (TITLE_LDX + 1, addr.to_bytes(2, "little"), "title:ptr"),
            (TITLE_LDY + 1, count.to_bytes(2, "little"), "title:count"), (TITLE_COPY_MAP, bytes(cmap), "title:map")]


def writes(orig):
    """[(file offset, bytes, by)]: each compressed block, plus its directory entries (every slot sharing the
    stream, e.g. 08_30 = the first 20 tiles of 08_31) when relocated."""
    tail = {b: list(r) for b, r in TAIL.items()}
    dirs = gfx.blocks(orig)
    sheet, maps = ranks(orig)
    out = []
    at = RANK_MAPS[0]
    for i, m in maps.items():
        out.append((at, m, "rank:map%d" % i))
        addr = 0x8000 | at & 0x7FFF
        out.append((RANK_TABLE + 2 * i, bytes([addr & 0xFF, addr >> 8]), "rank:ptr%d" % i))
        at += len(m)
    if at > RANK_MAPS[1]:
        raise SystemExit("rank maps overflow RANK_MAPS")
    for bank, slot, _, _, new in blocks(orig) + [(*RANK_SHEET, None, None, sheet)]:
        d = gfx.lorom(bank, 0x8000 + 4 * slot)
        off = gfx.lorom(bank, orig[d] | orig[d + 1] << 8)
        n, count = orig[d + 2] | orig[d + 3] << 8, len(new) // 16
        _, used = gfx.decompress(orig, off, n, 2)
        data = gfx.compress(new, 2)
        by = "gfxtext:%02X_%02X" % (bank, slot)
        if len(data) > used or count != n:
            old, (off, tail[bank][0]) = off, (tail[bank][0], tail[bank][0] + len(data))
            if tail[bank][0] > tail[bank][1]:
                raise SystemExit(f"{by}: bank ${bank:02X} tail full")
            addr = 0x8000 | off & 0x7FFF
            for b, s, o, _ in dirs:
                if b == bank and o == old:
                    e = bytes([addr & 0xFF, addr >> 8] + ([count & 0xFF, count >> 8] if s == slot and count != n else []))
                    out.append((gfx.lorom(b, 0x8000 + 4 * s), e, by + ":dir"))
        out.append((off, data, by))
    return out + title(orig)


def main():
    orig = gfx.ROM.read_bytes()
    w = writes(orig)
    print(f"{len(GFX)} blocks, {sum(by.endswith(':dir') for _, _, by in w)} directory entries repointed")
    if sys.argv[1:2] == ["--png"]:     # JP above English, one image per label
        from PIL import Image
        imgs = [(to_pixels(base.ljust(len(new), b"\0"), grid(kind)), to_pixels(new, grid(kind)))
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
