"""build.py: script/*.json -> build/logh_<lang>.sfc (docs/re/text.md for every table it rewrites).

Each string takes its `<lang>` field, or `jp` while that is empty, so with no translation the output is
byte-identical to the original (tests/test_identity.py). Every write goes through put() and is logged to
build/writes.txt; the build fails if romdiff finds a changed byte without a write behind it.
    python -X utf8 tools/build.py [--lang en] [--out FILE]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bps  # noqa: E402
import check_rom  # noqa: E402
import romdiff  # noqa: E402
import textdb  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "script"
MAIN_REGION = (0x28000 + 2 * textdb.MAIN_COUNT, textdb.SUB_TABLE)   # strings + free 0xFF run up to the sub table
SUB_REGION = (0x2FF30, 0x30000)                                     # bank $05 ends here; the font follows
NAME_SLOT = 16                                                      # RAM $1F10-$1F6F: chars + FF per slot


class Rom:
    def __init__(self, orig):
        self.orig, self.data, self.writes = bytes(orig), bytearray(orig), []

    def put(self, off, data, by):
        self.writes.append((off, self.orig[off:off + len(data)], bytes(data), by))
        self.data[off:off + len(data)] = data


def texts(lang):
    """id -> text (lang field, else jp) for every script file."""
    out = {}
    for p in sorted(SCRIPT.glob("*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            out[r["id"]] = r.get(lang) or r["jp"]
    return out


def pack(rom, region, strings, by):
    """strings: [(key, bytes)] in output order. Writes them back to back, 0xFF-fills the rest. Returns key -> offset."""
    lo, hi = region
    at, where = lo, {}
    for key, b in strings:
        if at + len(b) > hi:
            raise SystemExit(f"{by}: {key} overflows {lo:06X}-{hi:06X} by {at + len(b) - hi} bytes")
        rom.put(at, b, f"{by}:{key}")
        where[key] = at
        at += len(b)
    if at < hi:
        rom.put(at, b"\xff" * (hi - at), f"{by}:fill")
    return where


def put_ptrs(rom, table, offs, by):
    rom.put(table, b"".join(textdb.lorom(o).to_bytes(2, "little") for o in offs), by)


def build_text(rom, t, tx):
    orig = rom.orig
    # Main messages: packed in their original order (not id order), so an untranslated build is identical.
    main = sorted(textdb.main_strings(orig, t), key=lambda s: s[1])
    where = pack(rom, MAIN_REGION, [(sid, t.encode(tx[sid])) for sid, _, _ in main], "main")
    put_ptrs(rom, textdb.MAIN_TABLE, [where["m%03X" % i] for i in range(textdb.MAIN_COUNT)], "main:ptrs")

    sub = list(textdb.sub_strings(orig, t))
    where = pack(rom, SUB_REGION, [(sid, t.encode(tx[sid])) for sid, _, _ in sub], "sub")
    put_ptrs(rom, textdb.SUB_TABLE + 2 * textdb.SUB_RAM, [where[sid] for sid, _, _ in sub], "sub:ptrs")

    names = list(textdb.name_strings(orig, t))
    for name, table, count in textdb.NAME_TABLES:
        rows = [(sid, off, n) for sid, off, n in names if sid.startswith(name + "_")]
        region = (table + 2 * count, max(off + n for _, off, n in rows))
        enc = [(sid, name_bytes(sid, t.encode(tx[sid]))) for sid, _, _ in rows]
        where = pack(rom, region, enc, name)
        by_orig = {off: where[sid] for sid, off, _ in rows}
        put_ptrs(rom, table, [by_orig[textdb.bank_off(table, textdb.ptr(orig, table + 2 * i))] for i in range(count)],
                 f"{name}:ptrs")
    for name, off in textdb.FIXED:
        b = name_bytes(name, t.encode(tx[name]))
        if len(b) > orig[off] + 1:
            raise SystemExit(f"{name}: {len(b)} bytes, room for {orig[off] + 1} (embedded in bank $00 code)")
        rom.put(off, b, name)


def name_bytes(sid, enc):
    if len(enc) > NAME_SLOT:
        raise SystemExit(f"{sid}: {len(enc)} bytes with FF, the RAM name slot holds {NAME_SLOT}")
    return bytes([len(enc)]) + enc


def build(lang="en"):
    """Returns (built ROM bytes, write log)."""
    check_rom.check()
    orig, t = textdb.load()
    rom = Rom(orig)
    build_text(rom, t, texts(lang))
    fixed, _ = bps.snes_checksum(rom.data)
    rom.put(0x7FDC, fixed[0x7FDC:0x7FE0], "checksum")
    errs, _ = romdiff.check(rom.orig, bytes(rom.data), set(), rom.writes)
    if errs:
        raise SystemExit("romdiff:\n" + "\n".join(errs[:20]))
    return bytes(rom.data), rom.writes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    ap.add_argument("--out")
    a = ap.parse_args()
    out = Path(a.out) if a.out else ROOT / "build" / f"logh_{a.lang}.sfc"
    data, writes = build(a.lang)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    (out.parent / "writes.txt").write_text("".join("%X %s %s %s\n" % (o, a_.hex(), b.hex(), by)
                                                   for o, a_, b, by in writes), encoding="utf-8")
    changed = sum(x != y for x, y in zip(data, textdb.ROM.read_bytes()))
    print(f"{out.relative_to(ROOT)}: {changed} bytes differ from the original, {len(writes)} writes")


if __name__ == "__main__":
    main()
