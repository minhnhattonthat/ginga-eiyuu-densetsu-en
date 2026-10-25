"""Decode the event scripts (runner $01:8000, 256 events, pointer table $01:83F8, all in bank $01).

    python -X utf8 tools/events.py [ROM] [--event N]     # per event: the messages it can show (all branches)
    python -X utf8 tools/events.py [ROM] --unreached     # message ids no event or direct call shows

Opcodes (handlers $01:811C): 00 msg id16, 01 msg 0, 02 if-flag f, else goto a16, 03 set flag, 04 clear flag,
07 goto a16, 08 jump to event n, 0B yes/no: a16 (no), b, a16 (cancel), 11 = 0C, 12 = 0D, FF end.
Argument counts of the rest are from their handlers (ARGS below). Facts: docs/re/debug.md.
"""
import argparse
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = os.path.join(ROOT, "rom", "Ginga Eiyuu Densetsu (Japan).sfc")
ARGS = [2, 0, 3, 1, 1, 1, 1, 2, 1, 1, 1, 4, 4, 2, 1, 1, 1, 4, 2, 3, 1, 1, 1, 1, 1, 1, 0, 4, 2]
TABLE = 0x83F8


def off(a):
    return ((a >> 16 & 0x7F) << 15) | (a & 0x7FFF)


def ptr(d, ev):
    o = off(0x010000 | TABLE) + 2 * ev
    return d[o] | d[o + 1] << 8


def walk(d, ev):
    """Messages and jumped-to events reachable from event ev, following both sides of every branch."""
    msgs, jumps, seen, todo = [], [], set(), [ptr(d, ev)]
    while todo:
        pc = todo.pop()
        while pc not in seen and 0x8000 <= pc <= 0xFFFF:
            seen.add(pc)
            op = d[off(0x010000 | pc)]
            if op == 0xFF or op >= len(ARGS):
                break
            a = d[off(0x010000 | pc) + 1:off(0x010000 | pc) + 1 + ARGS[op]]
            nxt = pc + 1 + ARGS[op]
            if op == 0x00:
                msgs.append(a[0] | a[1] << 8)
            elif op == 0x02:
                todo.append(a[1] | a[2] << 8)
            elif op == 0x07:
                nxt = a[0] | a[1] << 8
            elif op == 0x08:
                jumps.append(a[0])
                break
            elif op == 0x0B:
                todo += [a[0] | a[1] << 8, a[2] | a[3] << 8]
            pc = nxt
    return msgs, jumps


def dump(d, ev):
    """Linear listing of event ev from its start to the first end (FF) or jump."""
    pc = ptr(d, ev)
    while 0x8000 <= pc <= 0xFFFF:
        op = d[off(0x010000 | pc)]
        if op == 0xFF or op >= len(ARGS):
            print(f"  {pc:04X} end ({op:02X})")
            return
        a = d[off(0x010000 | pc) + 1:off(0x010000 | pc) + 1 + ARGS[op]]
        print(f"  {pc:04X} op {op:02X} " + " ".join(f"{b:02X}" for b in a))
        pc += 1 + ARGS[op]


def direct_calls(d):
    return {m.group(1)[0] | m.group(1)[1] << 8 for m in re.finditer(rb"\xa2(..)\x22\x9f\x97\x07", d, re.S)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", default=ROM)
    ap.add_argument("--event", type=lambda s: int(s, 0))
    ap.add_argument("--unreached", action="store_true")
    ap.add_argument("--dump", action="store_true", help="with --event: list its opcodes")
    a = ap.parse_args()
    d = open(a.rom, "rb").read()
    if a.dump and a.event is not None:
        return dump(d, a.event)
    evs = [a.event] if a.event is not None else range(256)
    shown = set()
    for ev in evs:
        msgs, jumps = walk(d, ev)
        shown.update(msgs)
        if not a.unreached and (msgs or jumps):
            print(f"ev {ev:02X}: msgs " + " ".join(f"{m:03X}" for m in msgs)
                  + ("  -> ev " + " ".join(f"{j:02X}" for j in jumps) if jumps else ""))
    if a.unreached:
        left = sorted(set(range(571)) - shown - direct_calls(d))
        print(f"{len(left)} message ids not shown by any event or direct call:")
        print(" ".join(f"{m:03X}" for m in left))


if __name__ == "__main__":
    main()
