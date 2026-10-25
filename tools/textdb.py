"""textdb.py: where every string lives in the original ROM (docs/re/text.md). Shared by extract, build and tests.

Each source yields (id, offset, length) for the original ROM; ids are stable (table + index).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tbl import Table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Ginga Eiyuu Densetsu (Japan).sfc"
JP_TBL = ROOT / "tbl" / "jp.tbl"

MAIN_TABLE, MAIN_COUNT = 0x28000, 571      # $05:8000, 16-bit pointers into bank $05
SUB_TABLE, SUB_COUNT = 0x2FF00, 24         # $05:FF00; ids 0-5 point at RAM slots $1F10-$1F60
SUB_RAM = 6
# Length-prefixed name tables in bank $02: (name, table offset, count). Strings: len (chars + FF), chars, FF.
NAME_TABLES = [
    ("officer_fpa", 0x103BB, 31),
    ("officer_emp", 0x104D8, 36),
    ("ship_fpa", 0x10649, 22),      # flagships
    ("ship_emp", 0x10725, 17),
    ("rank", 0x107D4, 13),          # $87D4 alliance (6) and $87E0 empire (7), shared strings
]
# Length-prefixed strings embedded in bank $00 code ($00:F4D6 picks one by side).
FIXED = [("side_0", 0x074EE), ("side_1", 0x074F6)]


def lorom(off):
    return 0x8000 | (off & 0x7FFF)


def bank_off(off, addr):
    """File offset of a 16-bit pointer `addr` in the bank holding `off`."""
    return (off & ~0x7FFF) | (addr & 0x7FFF)


def ptr(rom, at):
    return rom[at] | rom[at + 1] << 8


def main_strings(rom, t):
    for i in range(MAIN_COUNT):
        off = bank_off(MAIN_TABLE, ptr(rom, MAIN_TABLE + 2 * i))
        _, n = t.decode(rom, off)
        yield "m%03X" % i, off, n


def sub_strings(rom, t):
    for i in range(SUB_RAM, SUB_COUNT):
        off = bank_off(SUB_TABLE, ptr(rom, SUB_TABLE + 2 * i))
        _, n = t.decode(rom, off)
        yield "s%02X" % i, off, n


def name_strings(rom, t):
    """Yields (id, offset of the length byte, total bytes incl. length byte). Duplicate pointers share one id."""
    for name, table, count in NAME_TABLES:
        seen = {}
        for i in range(count):
            off = bank_off(table, ptr(rom, table + 2 * i))
            if off in seen:
                continue
            seen[off] = i
            yield "%s_%02d" % (name, i), off, rom[off] + 1
    for name, off in FIXED:
        yield name, off, rom[off] + 1


def load():
    return bytearray(ROM.read_bytes()), Table.load(JP_TBL)
