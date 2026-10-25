"""extract.py: dump every string of the original ROM into script/*.json (jp + empty en).

Never clobbers English: an existing file keeps its en/notes/status; only jp, off and len are refreshed.
    python -X utf8 tools/extract.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import textdb  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "script"


def entries(rom, t):
    files = {"main": [], "sub": [], "names": []}
    for sid, off, n in textdb.main_strings(rom, t):
        files["main"].append({"id": sid, "off": "%06X" % off, "jp": t.decode(rom, off, n)[0]})
    for sid, off, n in textdb.sub_strings(rom, t):
        files["sub"].append({"id": sid, "off": "%06X" % off, "jp": t.decode(rom, off, n)[0]})
    for sid, off, n in textdb.name_strings(rom, t):
        files["names"].append({"id": sid, "off": "%06X" % off, "jp": t.decode(rom, off + 1, n - 1)[0]})
    return files


def main():
    rom, t = textdb.load()
    SCRIPT.mkdir(exist_ok=True)
    for name, rows in entries(rom, t).items():
        p = SCRIPT / f"{name}.json"
        old = {r["id"]: r for r in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}
        out = []
        for r in rows:
            o = old.get(r["id"], {})
            if o and o.get("jp") != r["jp"] and o.get("en"):
                print(f"{name}/{r['id']}: jp changed, en kept but marked for review")
                o["status"] = "jp-changed"
            out.append({**r, "en": o.get("en", ""), **{k: v for k, v in o.items() if k not in r and k != "en"}})
        p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"{p.relative_to(ROOT)}: {len(out)} strings")


if __name__ == "__main__":
    main()
