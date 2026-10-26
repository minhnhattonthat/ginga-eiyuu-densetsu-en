"""font.py: the English VWF font (a BDF in fonts/) -> engine data, and pixel widths for wrap/lint.

Code = ASCII byte (tbl/en.tbl). Each glyph is placed in a 16-row cell (BDF ascent at row ASCENT), ink shifted to
column 0, and stored like the JP font (32 bytes: 8x8 tiles TL, TR, BL, BR, 1bpp). Advance = the BDF's DWIDTH
(its own spacing); the engine (asm/engine.asm) draws glyphs up to 16 px wide.
    python -X utf8 tools/font.py [--png out.png] [--bdf FILE]   # writes build/gen/en_font.bin, en_width.bin
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BDF = ROOT / "fonts" / "ark-pixel-12px-proportional-latin.bdf"
GEN = ROOT / "build" / "gen"
CELL = 16
SPACE = 4       # the BDF's 6 px space reads loose next to 1 px letter gaps
SAMPLE = ["Reinhard von Lohengramm: \"Yang Wen-li, again?\"",
          "The quick brown fox jumps over the lazy dog. 0123456789",
          "Free Planets Alliance, 13th Fleet! (Iserlohn) ~@#$%&*+=/"]


def load(path=BDF):
    """code -> (16 rows of 16-bit ints, MSB = left, ink at column 0..; advance)."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    asc = next(int(l.split()[1]) for l in lines if l.startswith("FONT_ASCENT"))
    out, cur, i = {}, None, 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("ENCODING"):
            cur = {"enc": int(l.split()[1])}
        elif cur is not None and l.startswith("DWIDTH"):
            cur["dw"] = int(l.split()[1])
        elif cur is not None and l.startswith("BBX"):
            cur["bbx"] = list(map(int, l.split()[1:]))
        elif cur is not None and l == "BITMAP" and 0x20 <= cur["enc"] <= 0x7E:
            rows = []
            i += 1
            while lines[i] != "ENDCHAR":
                rows.append(int(lines[i], 16))
                i += 1
            w, h, ox, oy = cur["bbx"]
            nb = len(lines[i - 1]) * 4 if rows else 8
            top = asc - (h + oy)
            cell = [0] * CELL
            for r, v in enumerate(rows):
                assert 0 <= top + r < CELL, (cur["enc"], top + r)
                cell[top + r] = (v >> (nb - w)) << (16 - w)        # ink left-aligned (BBX x offset dropped)
            out[cur["enc"]] = (cell, SPACE if cur["enc"] == 0x20 else cur["dw"] - max(ox, 0))
            cur = None
        i += 1
    return out


def widths(path=BDF):
    return {code: w for code, (_, w) in load(path).items()}


def text_width(s, w=None):
    """Pixel width of plain ASCII text (no control codes)."""
    w = w or widths()
    return sum(w[ord(c)] for c in s)


def data(path=BDF):
    """(font bytes for codes 00-FF, width bytes)."""
    font, wid = bytearray(256 * 32), bytearray(256)
    for code, (rows, adv) in load(path).items():
        for r, v in enumerate(rows):
            base = (0 if r < 8 else 16) + (r & 7)
            font[code * 32 + base] = v >> 8           # left 8 px
            font[code * 32 + base + 8] = v & 0xFF     # right 8 px
        wid[code] = adv
    return bytes(font), bytes(wid)


def write(path=BDF):
    GEN.mkdir(parents=True, exist_ok=True)
    font, wid = data(path)
    (GEN / "en_font.bin").write_bytes(font)
    (GEN / "en_width.bin").write_bytes(wid)


def png(out, path=BDF, lines=SAMPLE):
    from PIL import Image
    g = load(path)
    img = Image.new("L", (340, 18 * len(lines)), 255)
    for li, t in enumerate(lines):
        x = 2
        for ch in t:
            rows, adv = g[ord(ch)]
            for r, v in enumerate(rows):
                for b in range(16):
                    if v >> (15 - b) & 1:
                        img.putpixel((x + b, li * 18 + r), 0)
            x += adv
        print(f"{x - 2:4d} px  {t}")
    img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(out)


if __name__ == "__main__":
    bdf = sys.argv[sys.argv.index("--bdf") + 1] if "--bdf" in sys.argv else BDF
    w = widths(bdf)
    assert set(w) == set(range(0x20, 0x7F)), "font must cover printable ASCII"
    assert all(1 <= v <= 16 for v in w.values()), w     # the engine spans at most 3 columns per glyph
    if "--png" in sys.argv:
        png(sys.argv[sys.argv.index("--png") + 1], bdf)
    else:
        write(bdf)
    print("font ok:", " ".join(f"{chr(c)}{v}" for c, v in sorted(w.items())))
