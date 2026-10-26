"""wrap.py: authored English -> game text with {nl} line breaks fitted to the box's pixel width.

Authored form (script/*.json `en`, translator output): ` / ` = a hard line break (an empty segment = a blank line),
`{yesno}` = the YES/NO icon pair, every other {code} as in the JP. Lines wrap greedily at spaces; a word wider
than the line is an error. Width per box: script/boxes.json (docs/re/engine.md width gate).
    python -X utf8 tools/wrap.py "Paetta: \"Commodore Yang!\" / ..." [--px 160]   # dry run: px per line
"""
import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BOXES = ROOT / "script" / "boxes.json"
YESNO = "ⓎⓈ      ⓃⒹ"          # icons at 0 and 12 px, 6 spaces (4 px) put NO at 48 px like the JP
WIDE = 12                       # glyphs >= U+0100 are drawn from the JP font at 12 px
CURSOR_VARS = (0, 1)            # the {wait} blink cursor covers the last 8 px of the bottom line here
TOKEN = re.compile(r"(\{[^}]*\})")


@lru_cache(None)
def widths():
    return font.widths()


@lru_cache(None)
def sub_widths():
    """{sub0:XX} id -> widest English it can expand to: 00-05 are RAM name slots (ship, officer, rank, a number,
    unused, side), 06-17 the fixed substrings."""
    rows = {}
    for name in ("sub", "names"):
        for r in json.loads((ROOT / "script" / f"{name}.json").read_text(encoding="utf-8")):
            rows[r["id"]] = r.get("en") or ""
    w = lambda s: text_px(s.replace("{end}", ""), {})  # noqa: E731
    slot = lambda p: max([w(v) for k, v in rows.items() if k.startswith(p)] + [0])  # noqa: E731
    out = {0: slot("ship_"), 1: slot("officer_"), 2: slot("rank_"), 3: w("000000"), 4: 0, 5: slot("side_")}
    for k, v in rows.items():
        if re.fullmatch(r"s[0-9A-F]{2}", k):
            out[int(k[1:], 16)] = w(v)
    return out


def text_px(s, subs=None):
    subs = sub_widths() if subs is None else subs
    px = 0
    for tok in TOKEN.split(s):
        m = re.fullmatch(r"\{sub0:([0-9A-F]{2})\}", tok)
        if m:
            px += subs.get(int(m[1], 16), 0)
        elif not tok.startswith("{"):
            px += sum(WIDE if ord(c) > 0xFF else widths().get(ord(c), 0) for c in tok)
    return px


def box_px(sid):
    """Line width for a message id (narrowest box it shows in); None for names and unknown ids."""
    b = json.loads(BOXES.read_text(encoding="utf-8")).get(sid)
    if not b:
        return None
    w, _, var = b[0], b[1], b[2]
    return 8 * (w + w // 2 + 1) - (8 if var in CURSOR_VARS else 0)


def wrap(text, px):
    """-> (game text, [problems]). px None = no wrapping (names)."""
    text = text.replace("{yesno}", YESNO)
    if px is None:
        return text, []
    out, errs = [], []
    for seg in segments(text):
        lines, cur = [], None
        for word in seg.split(" "):    # runs of spaces survive as empty words
            cand = word if cur is None else cur + " " + word
            if cur is None or text_px(cand) <= px:
                cur = cand
            else:
                lines.append(cur)
                cur = word
            if text_px(word) > px:
                errs.append(f"word {word!r} is {text_px(word)} px, line is {px}")
        lines.append(cur)
        out.append("{nl}".join(lines))
    return "{nl}".join(out), errs


def segments(text):
    """Split at ` / ` hard breaks: a `/` with a space or the text edge on both sides ("ON/OFF" stays)."""
    return [s.removeprefix(" ").removesuffix(" ") for s in re.split(r"(?<![^ ])/(?![^ ])", text)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text")
    ap.add_argument("--px", type=int, default=208)
    a = ap.parse_args()
    s, errs = wrap(a.text, a.px)
    for line in s.split("{nl}"):
        print(f"{text_px(line):4d} | {line}")
    for e in errs:
        print("ERROR", e)
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
