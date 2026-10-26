"""batches.py: translation batches (docs/translator-brief.md).

    python -X utf8 tools/batches.py split [--chars 3500] [--max 130]   # untranslated rows -> work/tl/bNNN.tsv + build/terms_bNNN.txt
    python -X utf8 tools/batches.py check bNNN [...]                    # validate work/tl/bNNN.out.tsv; prints OK
    python -X utf8 tools/batches.py merge bNNN [...]                    # checked output -> script/*.json `en`
    python -X utf8 tools/batches.py pairs bNNN OUT.txt                  # reviewer pairs file (>> id | JP / EN, +-2 context)

TSV in: id, speaker, form, limit, jp (JP {nl} shown as ` / `, the YES/NO icons as {yesno}). Out: id<TAB>English in
the authored form of tools/wrap.py (` / ` hard break, everything else wraps to the box).
"""
import argparse
import collections
import functools
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wrap  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "script"
TL = ROOT / "work" / "tl"
TERMS = ROOT / "build"
FILES = ("names", "sub", "main")
JP_YESNO = "ⓎⓈ　　ⓃⒹ"
CODE = re.compile(r"\{[^}]*\}")
KATA = "ァ-ヴー"
ENFORCED = ("Characters", "Places", "Ships")     # glossary sections whose terms must appear in the English
SUB_SPEAKER = {"06": "Oberstein", "07": "Frederica", "08": "Reinhard", "0A": "Kircheis"}


@functools.lru_cache(None)
def BOX_LINES():  # noqa: N802
    return {k: v[1] for k, v in json.loads(wrap.BOXES.read_text(encoding="utf-8")).items()}


def rows():
    out = []
    for name in FILES:
        for r in json.loads((SCRIPT / f"{name}.json").read_text(encoding="utf-8")):
            out.append((name, r))
    return out


def blank(jp):
    return not CODE.sub("", jp).strip()


def show(jp):
    return jp.replace(JP_YESNO, "{yesno}").replace("{nl}", " / ")


def codes(s):
    """Control codes a translation must keep (line breaks are free: the wrap tool makes them)."""
    s = s.replace(JP_YESNO, "{yesno}")
    return collections.Counter(c for c in CODE.findall(s) if c != "{nl}")


def glossary():
    """[(section, [jp forms], [en forms], [avoid])]"""
    out, sec = [], ""
    for line in (ROOT / "glossary.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            sec = line[3:]
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.startswith("|") or len(cells) < 5 or cells[0] in ("JP", "") or set(cells[0]) <= set("-"):
            continue
        out.append((sec, [j.strip() for j in cells[0].split(" / ")], [e.strip() for e in cells[1].split(" / ")],
                    [a.strip() for a in cells[4].split(",") if a.strip()]))
    return out


def has_term(jp, term):
    """Whole-run match: a katakana term must not sit inside a longer katakana run."""
    for m in re.finditer(re.escape(term), jp):
        a, b = m.start(), m.end()
        if term[0] in KATA_SET and a and jp[a - 1] in KATA_SET:
            continue
        if term[-1] in KATA_SET and b < len(jp) and jp[b] in KATA_SET:
            continue
        return True
    return False


KATA_SET = {chr(c) for c in range(0x30A1, 0x30FB)} | {"ー"}


def speaker(jp):
    body = CODE.sub(lambda m: m[0] if m[0].startswith("{sub0") else "", jp)
    m = re.match(r"([ァ-ヴー・．]+|\{sub0:([0-9A-F]{2})\})(?:「|\{nl\}「| / 「|\{nl\}\{sub0:0D\})", body)
    if not m:
        return ""
    if m[2]:
        return SUB_SPEAKER.get(m[2], "")
    for _, jps, ens, _ in glossary():
        if m[1] in jps:
            return ens[0]
    return m[1]


def form(name, sid, jp):
    if name == "names":
        return "name"
    if name == "sub":
        return "fragment"
    if JP_YESNO in jp:
        return "choice"
    if speaker(jp):
        return "dlg"
    box = json.loads(wrap.BOXES.read_text(encoding="utf-8")).get(sid)
    return "menu" if box and box[2] in (0, 2, 3) and "{speed:00}" in jp else "narration"


def limit(name, sid):
    px = wrap.box_px(sid) if name == "main" else None
    return f"{px}px" if px else "-"


def split(a):
    TL.mkdir(parents=True, exist_ok=True)
    TERMS.mkdir(parents=True, exist_ok=True)
    todo = [(n, r) for n, r in rows() if not blank(r["jp"]) and not r.get("en")]
    if not todo:
        sys.exit("nothing to translate")
    existing = sorted(TL.glob("b[0-9][0-9][0-9].tsv"))
    num = int(existing[-1].stem[1:]) + 1 if existing else 1
    batches, cur, size = [], [], 0
    for n, r in todo:
        c = len(CODE.sub("", r["jp"]))
        # names + sub strings make one batch (short glossary entries); main splits by size
        if cur and (n == "main" and (size + c > a.chars or len(cur) >= a.max) or (cur[-1][0] == "main") != (n == "main")):
            batches.append(cur)
            cur, size = [], 0
        cur.append((n, r))
        size += c
    batches.append(cur)
    gl = glossary()
    for b in batches:
        bid = f"b{num:03d}"
        num += 1
        p = TL / f"{bid}.tsv"
        if p.exists():
            sys.exit(f"{p} exists: refusing to overwrite")
        p.write_text("".join(f"{r['id']}\t{speaker(r['jp'])}\t{form(n, r['id'], r['jp'])}\t{limit(n, r['id'])}\t"
                             f"{show(r['jp'])}\n" for n, r in b), encoding="utf-8", newline="\n")
        text = " ".join(r["jp"] for _, r in b)
        terms = [f"{' / '.join(j)} = {' / '.join(e)}" + (f"  (avoid: {', '.join(av)})" if av else "")
                 for _, j, e, av in gl if any(has_term(text, x) for x in j)]
        (TERMS / f"terms_{bid}.txt").write_text("\n".join(terms) + "\n", encoding="utf-8", newline="\n")
        print(f"{bid}: {len(b)} entries, {sum(len(CODE.sub('', r['jp'])) for _, r in b)} JP chars, {len(terms)} terms")


def read_out(bid):
    p = TL / f"{bid}.out.tsv"
    if not p.exists():
        return None, [f"{p.name} missing"]
    out, errs = [], []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        if line.count("\t") != 1:
            errs.append(f"line {i}: want id<TAB>English (one tab), got {line.count(chr(9))} tabs")
            continue
        out.append(tuple(line.split("\t")))
    return out, errs


def check_one(bid):
    src = {r["id"]: (n, r) for n, r in rows()}
    ids = [l.split("\t")[0] for l in (TL / f"{bid}.tsv").read_text(encoding="utf-8").splitlines() if l]
    out, errs = read_out(bid)
    if out is None:
        return errs
    got = [i for i, _ in out]
    dup = [i for i, c in collections.Counter(got).items() if c > 1]
    if dup:
        errs.append(f"duplicate ids: {' '.join(dup)}")
    if set(got) != set(ids):
        errs += [f"missing ids: {' '.join(sorted(set(ids) - set(got)))}"] * bool(set(ids) - set(got))
        errs += [f"extra ids: {' '.join(sorted(set(got) - set(ids)))}"] * bool(set(got) - set(ids))
    return errs + lint(out, src)


def widow(game, h):
    """the text of the last page when a box of h lines pages to one holding <= 2 words, else '' (a full box clears
    on A, so the last h-line page shows alone)"""
    lines = [re.sub(r"\{sub0:..\}", "X", l) for l in game.split("{nl}")]
    lines = [CODE.sub("", l).strip() for l in lines]
    while lines and not lines[-1]:
        lines.pop()
    last = " ".join(lines[(len(lines) - 1) // h * h:]).split() if len(lines) > h else []
    return " ".join(last) if 0 < len(last) <= 2 else ""


def lint(out, src=None):
    """Per-entry rules for [(id, authored English)]; also tools/lint.py over the whole script."""
    src = src or {r["id"]: (n, r) for n, r in rows()}
    errs = []
    gl = glossary()
    for sid, en in out:
        if sid not in src:
            continue
        name, r = src[sid]
        jp = r["jp"]
        e = []
        if not en.strip():
            e.append("empty")
        bad = sorted({c for c in CODE.sub("", en) if not (0x20 <= ord(c) <= 0x7E)} - {"{", "}", "⇕"})
        if bad or "{" in CODE.sub("", en) or "}" in CODE.sub("", en):
            e.append(f"characters outside plain ASCII / stray braces: {''.join(bad)!r}")
        if "\\u" in en or "\\n" in en:
            e.append("escape sequence in the text (use ` / ` for a line break)")
        if re.search(r"/\{|\}/", en):  # " /{yesno}" drew a literal "/" and kept the icons on the text line
            e.append("'/' touching a {code}: a line break is ' / ' with spaces")
        if codes(jp) != codes(en):
            want, have = codes(jp), codes(en)
            e.append(f"control codes differ: missing {dict(want - have)} extra {dict(have - want)}")
        game, werr = wrap.wrap(en, wrap.box_px(sid) if name == "main" else None)
        e += werr
        h = BOX_LINES().get(sid)
        # a full box waits for A before it scrolls ($07:9DC0): the attract demo presses nothing and stalls
        if h and jp.count("{nl}") < h < game.count("{nl}") + 1:
            e.append(f"{game.count('{nl}') + 1} lines in a {h}-line box the JP fits in: tighten it "
                     f"(an extra line waits for a key press; the attract demo hangs)")
        if h and widow(game, h) and not widow(jp, h):
            e.append(f"last page of the {h}-line box holds only {widow(game, h)!r}: rewrap or tighten")
        # the YES cursor highlight is drawn on the JP's icon line, wherever the text puts the icons
        if "Ⓨ" in jp and game.split("Ⓨ")[0].count("{nl}") != jp.split("Ⓨ")[0].count("{nl}"):
            e.append(f"{{yesno}} must be on line {jp.split('Ⓨ')[0].count('{nl}') + 1} as in the JP "
                     "(the cursor highlight stays there)")
        if re.search(r"\{sub0:[0-9A-F]{2}\}(st|nd|rd|th)\b", en):
            e.append("ordinal suffix glued onto a variable")
        if re.search(r"\b(a|an)\s+\{sub0", en, re.I):
            e.append("a/an before a variable")
        if re.search(rf"[{KATA}]様|\{{sub0:..\}}様", jp.replace("{nl}", "")) and "-sama" not in en:
            e.append("様 after a name -> -sama (D1)")
        for sec, jps, ens, avoid in gl:
            present = any(has_term(jp, x) for x in jps)
            if present and sec.startswith(ENFORCED) and not any(x.lower() in en.lower() for x in ens):
                e.append(f"glossary: {'/'.join(jps)} -> {' / '.join(ens)}")
            for av in avoid:   # names: a wrong spelling anywhere; terms: only where the JP term is
                if (present or sec.startswith(ENFORCED)) and re.search(rf"\b{re.escape(av)}\b", en):
                    e.append(f"glossary: avoid {av!r} (use {ens[0]})")
        errs += [f"{sid}: {x}" for x in e]
    return errs


def check(a):
    bad = False
    for bid in a.batches:
        errs = check_one(bid)
        if errs:
            bad = True
            print(f"{bid}: {len(errs)} errors")
            for x in errs:
                print("  " + x)
        else:
            print(f"{bid}: OK")
    sys.exit(1 if bad else 0)


def merge(a):
    for bid in a.batches:
        errs = check_one(bid)
        if errs:
            sys.exit(f"{bid}: check fails ({len(errs)} errors); not merged")
    en = {}
    for bid in a.batches:
        en.update(dict(read_out(bid)[0]))
    for name in FILES:
        p = SCRIPT / f"{name}.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        n = 0
        for r in data:
            if r["id"] in en:
                r["en"] = en[r["id"]]
                n += 1
        if n:
            p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
            print(f"{p.relative_to(ROOT)}: {n} merged")


def pairs(a):
    src = [(n, r) for n, r in rows()]
    pos = {r["id"]: i for i, (_, r) in enumerate(src)}
    out, _ = read_out(a.batch)
    en = dict(out or [])
    lines = []
    idx = sorted(pos[s] for s in en)
    for j in range(max(0, idx[0] - 2), min(len(src), idx[-1] + 3)):   # the batch in order, +-2 context lines
        r = src[j][1]
        if blank(r["jp"]):
            continue
        mark = ">>" if r["id"] in en else "  "
        lines.append(f"{mark} {r['id']} | {show(r['jp'])}\n      EN: {en.get(r['id']) or r.get('en') or ''}")
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"{a.out}: {len(en)} entries")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("split")
    s.add_argument("--chars", type=int, default=3500)
    s.add_argument("--max", type=int, default=130)
    for c in ("check", "merge"):
        sp.add_parser(c).add_argument("batches", nargs="+")
    p = sp.add_parser("pairs")
    p.add_argument("batch")
    p.add_argument("out")
    a = ap.parse_args()
    {"split": split, "check": check, "merge": merge, "pairs": pairs}[a.cmd](a)


if __name__ == "__main__":
    main()
