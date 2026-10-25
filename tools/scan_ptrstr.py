"""scan_ptrstr.py: recon sweep for FF-terminated Japanese strings that something in the same bank points at.

A candidate starts after a non-glyph byte, decodes through tbl/jp.tbl (glyphs and known control codes only) up to FF,
holds 2+ characters with at least one kana/kanji, and its 16-bit LoROM address (or address-1, for length-prefixed
strings) appears as a little-endian word somewhere in its bank. Prints one line per hit, grouped by bank.
    python -X utf8 tools/scan_ptrstr.py [--skip 28000-30000,30000-38000]
"""
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tbl import Table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
JP = re.compile(r"[ぁ-ヿ一-鿿]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip", default="28000-30000,30000-38000")
    ap.add_argument("--rom", default=str(ROOT / "rom" / "Ginga Eiyuu Densetsu (Japan).sfc"))
    a = ap.parse_args()
    data = Path(a.rom).read_bytes()
    t = Table.load(ROOT / "tbl" / "jp.tbl")
    skip = [tuple(int(x, 16) for x in r.split("-")) for r in a.skip.split(",") if r]
    words = defaultdict(set)
    for bank in range(len(data) // 0x8000):
        b = data[bank * 0x8000:(bank + 1) * 0x8000]
        words[bank] = {b[i] | b[i + 1] << 8 for i in range(len(b) - 1)}
    hits = []
    for off in range(1, len(data)):
        if any(lo <= off < hi for lo, hi in skip):
            continue
        try:
            text, n = t.decode(data, off, maxlen=200)
        except ValueError:
            continue
        if "[" in text or not text.endswith("{end}") or n < 3:
            continue
        body = text[:-5]
        if len(JP.findall(body)) < 2:
            continue
        bank, addr = off >> 15, (off & 0x7FFF) | 0x8000
        if addr in words[bank]:
            hits.append((off, "ptr", body))
        elif (addr - 1) in words[bank] and data[off - 1] == n:
            hits.append((off, "len", body))
    seen_end = 0
    for off, kind, body in hits:
        if off < seen_end:
            continue  # suffix of a string already listed
        seen_end = off + len(body)
        print("%06X %s %s" % (off, kind, body[:100]))


if __name__ == "__main__":
    main()
