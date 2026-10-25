"""font_sheet.py: render the 12x16 1bpp text font (bank $06, 32 bytes per glyph) as a labelled PNG sheet.

Glyph layout (docs/re/text.md): bytes 0-15 = left 8 px column, rows 0-15; bytes 16-31 = right column (4 px used).
    python -X utf8 tools/font_sheet.py OUT.png [--rom ROM] [--first 0] [--count 1024] [--zoom 2]
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Ginga Eiyuu Densetsu (Japan).sfc"
FONT = 0x30000


def glyph(data, code):
    """16 rows of 16-bit pixels (MSB = left), from the 32-byte glyph."""
    g = data[FONT + code * 32: FONT + code * 32 + 32]
    return [(g[r] << 8) | g[8 + r] for r in range(8)] + [(g[16 + r] << 8) | g[24 + r] for r in range(8)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--rom", default=str(ROM))
    ap.add_argument("--first", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--count", type=lambda s: int(s, 0), default=1024)
    ap.add_argument("--zoom", type=int, default=2)
    a = ap.parse_args()
    data = Path(a.rom).read_bytes()
    cols, cw, ch = 16, 16 + 22, 16 + 4
    rows = (a.count + cols - 1) // cols
    img = Image.new("RGB", (cols * cw, rows * ch), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for i in range(a.count):
        code = a.first + i
        x, y = (i % cols) * cw, (i // cols) * ch
        d.text((x, y + 4), "%03X" % code, fill=(200, 0, 0))
        for r, bits in enumerate(glyph(data, code)):
            for c in range(16):
                if bits & (0x8000 >> c):
                    img.putpixel((x + 20 + c, y + 2 + r), (0, 0, 0))
    img = img.resize((img.width * a.zoom, img.height * a.zoom), Image.NEAREST)
    img.save(a.out)


if __name__ == "__main__":
    main()
