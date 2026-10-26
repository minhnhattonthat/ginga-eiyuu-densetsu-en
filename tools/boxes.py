"""boxes.py: which text box each message opens in -> script/boxes.json (id -> [w, h, var, how]).

w = JP chars per line, h = lines (the box scrolls, so h is not a limit), var = $11A1 box variant ($07:9E5A).
Canvas width in px = 8 * (w + w // 2 + 1): 17 -> 208, 13 -> 160, 9 -> 112 (docs/re/engine.md, width gate).
how: "seen" (a tour log of tools/lua/msgcall.lua: the box set up after the message opens, or the open one),
"event" (another message of the same event group was seen in it), "call" (the bank of a direct
`LDX #id / JSL $07:979F`), "jp" (no evidence: the narrowest box the JP lines fit).
    python -X utf8 tools/boxes.py [LOGDIR ...]      (default work/qa/probe: the original-ROM probe tour)
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import events  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "script" / "boxes.json"
BOX = {1: (17, 4, 1), 2: (13, 3, 2), 3: (13, 3, 3), 5: (17, 4, 5), 6: (17, 4, 6), 0: (17, 2, 0)}
# Event groups (docs/re/debug.md): battle-start lines, battle speeches, interludes, results; 2D = debug menu.
EVENT_BOX = [(range(0x00, 0x0E), 1), (range(0x12, 0x14), 3), (range(0x14, 0x25), 6), (range(0x26, 0x2D), 3),
             (range(0x2D, 0x2E), 3), (range(0x2E, 0x3A), 5), (range(0x3A, 0x100), 3)]
# Direct calls by caller: title menus (bank $07 $9000-$9700), command menus (bank $04), admiral placement,
# result screen (bank $00 $F2xx-$F4xx).
CALL_BOX = [(lambda a: 0x079000 <= a < 0x079700, 0), (lambda a: a >> 16 == 0x04, 3),
            (lambda a: 0x00E000 <= a < 0x00E900, 2), (lambda a: 0x00F200 <= a < 0x00F500, 5),
            (lambda a: a in (0x00EF5C, 0x07A475, 0x018171), 3)]


def width_px(w):
    return 8 * (w + w // 2 + 1)


def parse(log):
    """[(msg id, (w, h, var))] in log order."""
    out, cur, pending = [], None, []
    for line in log.splitlines():
        m = re.search(r"msg ([0-9A-F]{3}) ret", line)
        if m:
            pending.append(int(m[1], 16))
            continue
        m = re.search(r"box mode \w+ w (\d+) h (\d+) var (\d+)", line)
        if m:
            cur = tuple(map(int, m.groups()))
            out += [(p, cur) for p in pending]
            pending = []
    out += [(p, cur) for p in pending if cur]
    return out


def jp_line_max(jp):
    """Longest JP line in glyphs (name substrings count 0: unknown)."""
    return max(len(re.sub(r"\{[^}]*\}", "", ln)) for ln in re.split(r"\{(?:nl|wait)\}", jp))


def assign(logdirs):
    rom = events.ROM
    d = open(rom, "rb").read()
    jp = {r["id"]: r["jp"] for r in json.loads((ROOT / "script" / "main.json").read_text(encoding="utf-8"))}
    out = {}
    for ld in logdirs:
        for log in sorted(Path(ld).glob("*/log.txt")):
            for mid, box in parse(log.read_text(encoding="utf-8", errors="replace")):
                k = "m%03X" % mid
                if k not in out or box[0] < out[k][0]:    # several boxes: the narrowest binds
                    out[k] = [*box, "seen"]
    for ev in range(256):
        msgs, _ = events.walk(d, ev)
        var = next(v for r, v in EVENT_BOX if ev in r) if any(ev in r for r, _ in EVENT_BOX) else None
        for m in msgs:
            k = "m%03X" % m
            if var is not None and k not in out:
                out[k] = [*BOX[var], "event"]
    for m in re.finditer(rb"\xa2(..)\x22\x9f\x97\x07", d, re.S):
        k = "m%03X" % (m.group(1)[0] | m.group(1)[1] << 8)
        o = m.start()
        addr = (o >> 15) << 16 | 0x8000 | (o & 0x7FFF)
        var = next((v for f, v in CALL_BOX if f(addr)), None)
        if var is not None and k not in out:
            out[k] = [*BOX[var], "call"]
    for k, s in jp.items():
        if k not in out:
            out[k] = [*(BOX[3] if jp_line_max(s) <= 13 else BOX[6]), "jp"]
    return dict(sorted(out.items())), jp


def main():
    out, jp = assign(sys.argv[1:] or [ROOT / "work" / "qa" / "probe"])
    bad = [k for k, v in out.items() if jp_line_max(jp[k]) > v[0]]
    for k in bad:
        print(f"{k}: JP line of {jp_line_max(jp[k])} glyphs in a {out[k][0]}-wide box ({out[k][3]})")
    OUT.write_text("{\n" + ",\n".join(f'"{k}": {json.dumps(v)}' for k, v in out.items()) + "\n}\n",
                   encoding="utf-8", newline="\n")
    from collections import Counter
    print(f"{OUT.relative_to(ROOT)}: {len(out)} messages;", dict(Counter((v[0], v[3]) for v in out.values())))


if __name__ == "__main__":
    main()
