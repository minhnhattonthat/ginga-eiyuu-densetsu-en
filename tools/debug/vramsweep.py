"""Dump PPU state (VRAM, CGRAM, OAM, registers) for every savestate in work/states, then report which BG3 tiles in a
range are drawn or non-blank in scenes that also show a given tile (a free-VRAM check before growing a block).

    python -X utf8 tools/debug/vramsweep.py dump [--rom build/logh_en.sfc] [--out work/qa/vram] [--jobs 3]
    python -X utf8 tools/debug/vramsweep.py check LO HI [--with TILE] [--out work/qa/vram]     (hex BG3 tile numbers)
"""
import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

STATES = os.path.join(ROOT, "work", "states")


def dump(rom, out, name):
    d = os.path.join(out, name)
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), rom, "--out", d,
                    "--state-in", os.path.join(STATES, name + ".mss"), "--frames", "6", "--var", "DUMP_AT=5",
                    "--script", os.path.join(SKILL, "scripts", "lua", "probes", "ppudump.lua"), "--timeout", "120"],
                   capture_output=True)
    return name, os.path.exists(os.path.join(d, "ppu_000005.vram.bin"))


def layer(ppu, n, key):
    return int(ppu[f"ppu.layers[{n}].{key}"])


def check(out, lo, hi, with_tile):
    for name in sorted(os.listdir(out)):
        pre = os.path.join(out, name, "ppu_000005")
        if not os.path.exists(pre + ".vram.bin"):
            continue
        vram = open(pre + ".vram.bin", "rb").read()
        ppu = dict(l.split("=", 1) for l in open(pre + ".ppu.txt").read().split("\n") if "=" in l)
        tm, chr_ = layer(ppu, 2, "tilemapAddress"), layer(ppu, 2, "chrAddress")
        size = 0x400 << (ppu[f"ppu.layers[2].doubleWidth"] == "true") << (ppu[f"ppu.layers[2].doubleHeight"] == "true")
        drawn = {(vram[2 * (w & 0x7FFF)] | vram[2 * (w & 0x7FFF) + 1] << 8) & 0x3FF for w in range(tm, tm + size)}
        if with_tile is not None and with_tile not in drawn:
            continue
        busy = [t for t in range(lo, hi + 1) if t in drawn or any(vram[2 * chr_ + 16 * t:2 * chr_ + 16 * t + 16])]
        print(f"{name:24s} {'busy ' + ' '.join('%03X' % t for t in busy[:12]) if busy else 'free'}"
              f"{' ...' if len(busy) > 12 else ''}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["dump", "check"])
    ap.add_argument("range", nargs="*")
    ap.add_argument("--rom", default=os.path.join(ROOT, "build", "logh_en.sfc"))
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "qa", "vram"))
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--with", dest="with_tile")
    a = ap.parse_args()
    if a.cmd == "dump":
        names = sorted(f[:-4] for f in os.listdir(STATES) if f.endswith(".mss"))
        with ThreadPoolExecutor(a.jobs) as ex:
            bad = [n for n, ok in ex.map(lambda n: dump(a.rom, a.out, n), names) if not ok]
        print(f"{len(names) - len(bad)}/{len(names)} dumped", *bad)
    else:
        check(a.out, int(a.range[0], 16), int(a.range[1], 16), int(a.with_tile, 16) if a.with_tile else None)


if __name__ == "__main__":
    main()
