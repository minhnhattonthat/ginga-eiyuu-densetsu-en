"""widthgate.py: measure every text box variant in game (pipeline width gate).

Builds build/qa_width.sfc with one message per box variant replaced by: a ruler line exactly as wide as the
variant's canvas (8 * (w + w//2 + 1) px, ending in `|`), then chunks of the glyph torture line (all printable
ASCII, double spaces). Warps to each scene (tools/debug/regen.py) and writes zoomed crops of the box to
work/qa/width/<variant>.png. Read them: the ruler's final `|` must show whole, every glyph must be distinct.
    python -X utf8 tools/widthgate.py [--no-run]
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boxes  # noqa: E402
import build  # noqa: E402
import font  # noqa: E402
from skill import SKILL  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "build" / "qa_width.sfc"
QA = ROOT / "work" / "qa" / "width"
# variant: (message, scene that opens it, box chars, lines, frames from arrival to the shot: battle screens type
# slower)
CASES = {
    "v0_17x2": ("m00A", "title_loadnew", 17, 2, 150),
    "v1_17x4": ("m034", "astarte_brief", 17, 4, 210),   # the briefing closes by itself ~240 frames in
    "v2_13x3": ("m010", "astarte_assign", 13, 3, 150),
    "v3_13x3": ("m012", "cmd_menu", 13, 3, 150),
    # results type slowly ({speed} ignored) and m205 has no {wait}: stress m03C after it too, shot on m03C
    "v5_17x4": ("m205+m03C", "step00_yang_result0", 17, 4, 405),   # m03C full ~f+400, m03D at f+414
    "v6_17x4": ("m028", "intro", 17, 4, 150),
}
TORTURE = "".join(chr(c) for c in range(0x21, 0x7F) if chr(c) not in "{}") + "  a  b   c"


def ruler(px, w):
    """A line exactly px wide: `[px]`, o's (6 px) with some r's (5 px) to land exactly, then `|`."""
    head, tail = f"[{px}]", "|"
    rest = px - font.text_width(head + tail, w)
    k = -(-rest // w[ord("o")])
    excess = k * w[ord("o")] - rest
    body = "r" * excess + "o" * (k - excess)
    s = head + body + tail
    assert font.text_width(s, w) == px, (s, font.text_width(s, w), px)
    return s


def chunks(text, px, w):
    out, cur = [], ""
    for ch in text:
        if font.text_width(cur + ch, w) > px:
            out.append(cur)
            cur = ""
        cur += ch
    return out + [cur]


def stress(chars, lines, part, w):
    """Full-width ruler, torture chunks, and a full-width ruler on the last line: the {wait} blink cursor
    (one tilemap cell, $07:9E76) hides the end of the last line in some variants."""
    px = boxes.width_px(chars)
    t = chunks(TORTURE, px, w)
    mid = [t[(part + j) % len(t)] for j in range(lines - 2)]
    return "{speed:00}" + "{nl}".join([ruler(px, w)] + mid + [ruler(px, w)]) + "{wait}{end}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-run", action="store_true")
    a = ap.parse_args()
    w = font.widths()
    qa = {}
    for i, (var, (mids, _, chars, lines, _)) in enumerate(CASES.items()):
        for mid in mids.split("+"):
            qa[mid] = stress(chars, lines, 2 * i, w)
    data, _ = build.build("en", True, qa)
    ROM.write_bytes(data)
    print(f"{ROM.relative_to(ROOT)} built")
    if a.no_run:
        return
    for settle in sorted({c[4] for c in CASES.values()}):
        scenes = [c[1] for c in CASES.values() if c[4] == settle]
        subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "debug" / "regen.py"), *scenes, "--rom",
                        str(ROM), "--qa", str(QA), "--no-states", "--jobs", "3", "--settle", str(settle)])
    sheet = os.path.join(SKILL, "scripts", "sheet.py")
    for var, (_, scene, _, _, _) in CASES.items():
        shot = QA / scene / "warp.png"
        if shot.exists():
            subprocess.run([sys.executable, "-X", "utf8", sheet, str(shot), "--crop", "0,120,256,104", "--zoom", "3",
                            "--out", str(QA / f"{var}.png")], capture_output=True)
            print(f"{var}: {QA / (var + '.png')}")
        else:
            print(f"{var}: {scene} not reached")


if __name__ == "__main__":
    main()
