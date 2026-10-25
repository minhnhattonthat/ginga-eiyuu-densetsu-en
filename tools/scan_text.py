"""scan_text.py: list ROM runs that decode as Japanese text through tbl/jp.tbl (recon: find text outside bank $05).

A run = 3+ consecutive glyph codes containing kana, ended by any byte that isn't a glyph. Prints runs grouped into
regions (runs closer than --gap bytes merge).
    python -X utf8 tools/scan_text.py [--min 3] [--gap 64] [--skip 28000-30000,30000-38000]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tbl import Table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
KANA = re.compile(r"[ぁ-ヿ]")


def runs(data, t, minlen):
    pos, n = 0, len(data)
    while pos < n:
        start, chars = pos, []
        while pos < n:
            b = data[pos]
            if b < 0xD0 and bytes([b]) in t.dec and b != 0:
                chars.append(t.dec[bytes([b])]); pos += 1
            elif b in (0xD0, 0xD1) and pos + 1 < n and bytes(data[pos:pos + 2]) in t.dec:
                chars.append(t.dec[bytes(data[pos:pos + 2])]); pos += 2
            else:
                break
        s = "".join(chars)
        if len(chars) >= minlen and len(KANA.findall(s)) * 2 >= len(chars):
            yield start, pos, s
        pos = max(pos, start + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=3)
    ap.add_argument("--gap", type=int, default=64)
    ap.add_argument("--skip", default="28000-30000,30000-38000")
    ap.add_argument("--rom", default=str(ROOT / "rom" / "Ginga Eiyuu Densetsu (Japan).sfc"))
    a = ap.parse_args()
    data = Path(a.rom).read_bytes()
    t = Table.load(ROOT / "tbl" / "jp.tbl")
    skip = [tuple(int(x, 16) for x in r.split("-")) for r in a.skip.split(",") if r]
    regions = []
    for s, e, txt in runs(data, t, a.min):
        if any(lo <= s < hi for lo, hi in skip):
            continue
        if regions and s - regions[-1][1] <= a.gap:
            regions[-1][1] = e; regions[-1][2].append(txt)
        else:
            regions.append([s, e, [txt]])
    for s, e, txts in regions:
        print("%06X-%06X %4d runs  %s" % (s, e, len(txts), " | ".join(txts[:6])[:150]))


if __name__ == "__main__":
    main()
