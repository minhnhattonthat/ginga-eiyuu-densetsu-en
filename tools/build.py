"""build.py: script/*.json -> build/logh_<lang>.sfc (docs/re/text.md for every table it rewrites).

Japanese builds (any lang but en) take each string's `<lang>` field, or `jp` while that is empty, so with no
translation the output is byte-identical to the original (tests/test_identity.py).
English builds apply asm/engine.asm (VWF, F8 far jump, name slots: docs/re/engine.md), encode with tbl/en.tbl and
show `[id] marker text` for every string without `en` (all of them with --marker). Strings that don't fit their
bank get a 4-byte `{far}` stub there and live in FAR_REGIONS.
Every write goes through put() and is logged to build/writes.txt; the build fails if romdiff finds a changed byte
without a write behind it.
    python -X utf8 tools/build.py [--lang en] [--marker] [--qa ID=TEXT ...] [--out FILE]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bps  # noqa: E402
import check_rom  # noqa: E402
import font  # noqa: E402
import gfxtext  # noqa: E402
import romdiff  # noqa: E402
import textdb  # noqa: E402
import wrap  # noqa: E402
from tbl import Table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "script"
GEN = ROOT / "build" / "gen"
ASAR = ROOT / "tools" / "asar" / "asar.exe"
ENGINE = ROOT / "asm" / "engine.asm"
EN_TBL = ROOT / "tbl" / "en.tbl"
MAIN_REGION = (0x28000 + 2 * textdb.MAIN_COUNT, textdb.SUB_TABLE)   # strings + free 0xFF run up to the sub table
SUB_REGION = (0x2FF30, 0x30000)                                     # bank $05 ends here; the font follows
NAME_TAIL = (0x16DEA, gfxtext.RANK_MAPS[0])                         # bank $02 0xFF tail (trap-tested, engine.md)
FAR_REGIONS = [(0x7B000, 0x80000), (0xF8000, 0x100000)]             # bank $0F after the font, bank $1F
SIDE_FAR = {"side_0": 0x78E00, "side_1": 0x78E80}                   # $0F:8E00/8E80, asm/engine.asm points $00:F4D6 here
ALLOWED = [                                                         # every write must land in one (romdiff ranges)
    (0x746B, 0x746F, "hook $00:F46B name_slot"), (0x74D7, 0x74FE, "hooks $00:F4D7-F4E3 + side names"),
    (0x7557, 0x7558, "number digit base $00:F557"),
    (0x39B00, 0x39B06, "speed hook $07:9B00 (cut-ins type at half the delay)"),
    (0x7FDC, 0x7FE0, "checksum"), (0x103BB, 0x1081C, "bank $02 name tables + old strings"), NAME_TAIL + ("names",),
    (0x28000, 0x30000, "bank $05 main/sub tables + strings"), (0x39A39, 0x39A3E, "hook $07:9A39 ff_code"),
    (0x39BBF, 0x39BC3, "hook $07:9BBF vwf_draw"), (0x78000, 0x80000, "bank $0F engine, font, side names, far"),
    (0xF8000, 0x100000, "bank $1F far"),
    (0x40000, 0x401E4, "bank $08 gfx directory"), (0x440CC, 0x4445D, "title buttons 08_30/08_31"),
    (0x44B7A, 0x45178, "rank sheet 08_35"), gfxtext.RANK_MAPS + ("rank maps",),
    (gfxtext.RANK_TABLE + 2 * 29, gfxtext.RANK_TABLE + 2 * 37, "rank map pointers"), (0x4517C, 0x46A56, "wide banners 08_37-08_3C + plates 08_3D-08_70"),
    (0x46C78, 0x46E01, "wide banner 08_74"),
    (0x70000, 0x70100, "bank $0E gfx directory"), (0x73240, 0x73496, "ship-type labels 0E_37-0E_3E"), (0x2705, 0x270D, "hook $00:A705 label_clear"),
    (0x2752, 0x2763, "hook $00:A752 label_draw"), (0x27C6, 0x27C8, "label slot 7 position"),
    (0x48000, 0x480E8, "bank $09 gfx directory"), (0x480E8, 0x49AC9, "plates + banners 09_00-09_2E"),
    (gfxtext.TITLE_LDX + 1, gfxtext.TITLE_LDX + 3, "title tiles pointer"),
    (gfxtext.TITLE_LDY + 1, gfxtext.TITLE_LDY + 3, "title tile count"),
    (gfxtext.TITLE_COPY_MAP, gfxtext.TITLE_COPY_MAP + 512, "title copyright map"),
    gfxtext.TITLE_TAIL + ("title tiles (bank $13 tail)",),
] + [(s, e, "gfxtext tail") for s, e in gfxtext.TAIL.values()]
NAME_SLOT = 16                                                     # RAM $1F10-$1F6F: chars + FF per slot (JP build)
FILLER = "The quick brown fox jumps over the lazy dog. "


class Rom:
    def __init__(self, orig):
        self.orig, self.data, self.writes = bytes(orig), bytearray(orig), []

    def put(self, off, data, by):
        self.writes.append((off, self.orig[off:off + len(data)], bytes(data), by))
        self.data[off:off + len(data)] = data


def rows():
    for name in ("main", "sub", "names"):
        yield from json.loads((SCRIPT / f"{name}.json").read_text(encoding="utf-8"))


def texts(lang):
    """id -> text (lang field, else jp) for every script file."""
    return {r["id"]: r.get(lang) or r["jp"] for r in rows()}


def marker(sid, jp, w):
    """`[id] filler` in the JP string's shape: same control codes, each line's text as wide as the JP line
    (12 px per JP glyph), so the marker shows its id wherever the line is drawn."""
    out, first = [], True
    for tok in re.split(r"(\{[^}]*\})", jp):
        if not tok or tok.startswith("{"):
            out.append(tok)
            continue
        target = 12 * len(tok)
        s = f"[{sid}]" if first else ""
        first = False
        i = 0
        while font.text_width(s + FILLER[i % len(FILLER)], w) <= target:
            s += FILLER[i % len(FILLER)]
            i += 1
        out.append(s)
    return "".join(out)


def blank(jp):
    return not re.sub(r"\{[^}]*\}", "", jp).strip()


def en_texts(marker_all=False, qa=None):
    w = font.widths()
    out = {}
    for r in rows():
        sid = r["id"]
        if blank(r["jp"]):   # control codes only (24 main, 2 empty name slots): not text, kept as is
            out[sid] = r["jp"]
        elif not marker_all and r.get("en"):     # authored form -> {nl} lines fitted to the box (tools/wrap.py)
            out[sid], errs = wrap.wrap(r["en"], wrap.box_px(sid) if sid.startswith("m") else None)
            if errs:
                raise SystemExit(f"{sid}: " + "; ".join(errs))
        elif sid.startswith(("officer_", "ship_", "rank_", "side_")):
            out[sid] = sid + "{end}"
        else:
            out[sid] = marker(sid, r["jp"], w)
    out.update(qa or {})
    # English needs ~2x the glyphs of the JP line: halve each per-glyph delay to keep the JP pacing
    return {k: re.sub(r"\{speed:([0-9A-Fa-f]{2})\}", lambda m: "{speed:%02X}" % ((int(m[1], 16) + 1) // 2), v)
            for k, v in out.items()}


class Far:
    """Allocator over FAR_REGIONS; a string never crosses a bank (the text pointer wraps inside its bank)."""

    def __init__(self, rom, regions=FAR_REGIONS):
        self.rom, self.regions, self.next = rom, regions, [lo for lo, _ in regions]

    def put(self, data, by):
        """First fit."""
        for i, (_, hi) in enumerate(self.regions):
            if self.next[i] + len(data) <= hi:
                off = self.next[i]
                self.next[i] += len(data)
                self.rom.put(off, data, by)
                return off
        raise SystemExit(f"{by}: far text space full ({len(data)} bytes)")

    def fill(self, by):
        for (_, hi), at in zip(self.regions, self.next):
            if at < hi:
                self.rom.put(at, b"\xff" * (hi - at), by)


def far_stub(off):
    a = 0x8000 | (off & 0x7FFF) | (off >> 15) << 16
    return bytes([0xF8, a & 0xFF, a >> 8 & 0xFF, a >> 16])


def pack(rom, region, strings, by, far=None):
    """strings: [(key, bytes)] in output order. Writes them back to back, 0xFF-fills the rest. Returns key -> offset.
    With `far`, the strings that don't fit go far and leave a 4-byte stub in the region (the first k fit)."""
    lo, hi = region
    keep = len(strings)
    if far:
        while keep and sum(len(b) for _, b in strings[:keep]) + 4 * (len(strings) - keep) > hi - lo:
            keep -= 1
    at, where = lo, {}
    for n, (key, b) in enumerate(strings):
        if n >= keep:
            b = far_stub(far.put(b, f"{by}:{key}:far"))
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


def build_text(rom, t, tx, far=None):
    """far: a Far allocator (English builds) for strings that outgrow their bank, and no name length cap."""
    orig = rom.orig
    # Main messages: packed in their original order (not id order), so an untranslated build is identical.
    main = sorted(textdb.main_strings(orig, t), key=lambda s: s[1])
    where = pack(rom, MAIN_REGION, [(sid, t.encode(tx[sid])) for sid, _, _ in main], "main", far)
    put_ptrs(rom, textdb.MAIN_TABLE, [where["m%03X" % i] for i in range(textdb.MAIN_COUNT)], "main:ptrs")

    sub = list(textdb.sub_strings(orig, t))
    where = pack(rom, SUB_REGION, [(sid, t.encode(tx[sid])) for sid, _, _ in sub], "sub", far)
    put_ptrs(rom, textdb.SUB_TABLE + 2 * textdb.SUB_RAM, [where[sid] for sid, _, _ in sub], "sub:ptrs")

    names = list(textdb.name_strings(orig, t))
    tail = None
    if far:  # all name strings move to the bank $02 tail; the old string areas are blanked
        tail = Far(rom, [NAME_TAIL])
    for name, table, count in textdb.NAME_TABLES:
        rows_ = [(sid, off, n) for sid, off, n in names if sid.startswith(name + "_")]
        region = (table + 2 * count, max(off + n for _, off, n in rows_))
        enc = [(sid, name_bytes(sid, t.encode(tx[sid]), cap=not far)) for sid, _, _ in rows_]
        if tail:
            where = {sid: tail.put(b, f"{name}:{sid}") for sid, b in enc}
            rom.put(region[0], b"\xff" * (region[1] - region[0]), f"{name}:fill")
        else:
            where = pack(rom, region, enc, name)
        by_orig = {off: where[sid] for sid, off, _ in rows_}
        put_ptrs(rom, table, [by_orig[textdb.bank_off(table, textdb.ptr(orig, table + 2 * i))] for i in range(count)],
                 f"{name}:ptrs")
    if tail:
        tail.fill("names:tail-fill")
    for name, off in textdb.FIXED:
        b = name_bytes(name, t.encode(tx[name]), cap=not far)
        if far:     # asm/engine.asm points $00:F4D6 at SIDE_FAR; the bank $00 copies stay as they are
            if len(b) > 0x80:
                raise SystemExit(f"{name}: {len(b)} bytes, room for 128")
            rom.put(SIDE_FAR[name], b, name)
            continue
        if len(b) > orig[off] + 1:
            raise SystemExit(f"{name}: {len(b)} bytes, room for {orig[off] + 1} (embedded in bank $00 code)")
        rom.put(off, b, name)


def name_bytes(sid, enc, cap=True):
    if cap and len(enc) > NAME_SLOT:
        raise SystemExit(f"{sid}: {len(enc)} bytes with FF, the RAM name slot holds {NAME_SLOT}")
    return bytes([min(len(enc), 0xFF)]) + enc


def apply_engine(rom):
    """Assemble asm/engine.asm onto a copy of the original; log every changed run as an asm write."""
    font.write()
    tmp = GEN / "engine.sfc"
    tmp.write_bytes(rom.orig)
    r = subprocess.run([str(ASAR), "--fix-checksum=off", str(ENGINE), str(tmp)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("asar:\n" + r.stdout + r.stderr)
    new = tmp.read_bytes()
    assert len(new) == len(rom.orig), "asar changed the ROM size"
    i = 0
    while i < len(new):
        if new[i] != rom.orig[i]:
            j = i
            while j < len(new) and new[j] != rom.orig[j]:
                j += 1
            rom.put(i, new[i:j], "asm")
            i = j
        else:
            i += 1


def build(lang="en", marker_all=False, qa=None):
    """Returns (built ROM bytes, write log)."""
    check_rom.check()
    orig, t = textdb.load()
    rom = Rom(orig)
    if lang == "en":
        apply_engine(rom)
        build_text(rom, Table.load(EN_TBL), en_texts(marker_all, qa), Far(rom))
        for off, data, by in gfxtext.writes(rom.orig):
            rom.put(off, data, by)
    else:
        build_text(rom, t, texts(lang))
    fixed, _ = bps.snes_checksum(rom.data)
    rom.put(0x7FDC, fixed[0x7FDC:0x7FE0], "checksum")
    errs, _ = romdiff.check(rom.orig, bytes(rom.data), set(), rom.writes)
    errs += ["0x%06X+%d: %s outside ALLOWED" % (o, len(b), by) for o, _, b, by in rom.writes
             if not any(s <= o and o + len(b) <= e for s, e, _ in ALLOWED)]
    if errs:
        raise SystemExit("romdiff:\n" + "\n".join(errs[:20]))
    return bytes(rom.data), rom.writes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    ap.add_argument("--marker", action="store_true", help="every string shows its [id] marker")
    ap.add_argument("--qa", action="append", default=[], metavar="ID=TEXT", help="override one string")
    ap.add_argument("--out")
    a = ap.parse_args()
    out = Path(a.out).resolve() if a.out else ROOT / "build" / f"logh_{a.lang}.sfc"
    qa = dict(q.split("=", 1) for q in a.qa)
    data, writes = build(a.lang, a.marker, qa)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    (out.parent / "writes.txt").write_text("".join("%X %s %s %s\n" % (o, a_.hex(), b.hex(), by)
                                                   for o, a_, b, by in writes), encoding="utf-8")
    changed = sum(x != y for x, y in zip(data, textdb.ROM.read_bytes()))
    print(f"{out.relative_to(ROOT)}: {changed} bytes differ from the original, {len(writes)} writes")


if __name__ == "__main__":
    main()
