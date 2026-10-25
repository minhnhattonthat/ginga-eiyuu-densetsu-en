"""pack_pages.py: stack labelled PNGs from a directory into pages for review (graphics survey).
    python -X utf8 tools/pack_pages.py SRCDIR OUTDIR [--height 1100] [--cols 2]
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--height", type=int, default=1100)
    ap.add_argument("--cols", type=int, default=2)
    a = ap.parse_args()
    files = sorted(Path(a.src).glob("*.png"))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    colw = max(Image.open(f).width for f in files) + 8
    pages, cur, col, y = [], [], 0, 0
    for f in files:
        im = Image.open(f)
        h = im.height + 12
        if y + h > a.height and y > 0:
            col, y = col + 1, 0
            if col == a.cols:
                pages.append(cur); cur, col = [], 0
        cur.append((f, col * colw, y)); y += h
    if cur:
        pages.append(cur)
    for n, page in enumerate(pages):
        img = Image.new("RGB", (colw * a.cols, a.height), (60, 0, 60))
        d = ImageDraw.Draw(img)
        for f, x, y in page:
            d.text((x, y), f.stem, fill=(255, 255, 0))
            img.paste(Image.open(f).convert("RGB"), (x, y + 11))
        img.save(out / ("page_%02d.png" % n))
        print(out / ("page_%02d.png" % n), " ".join(f.stem[:5] for f, _, _ in page))


if __name__ == "__main__":
    main()
