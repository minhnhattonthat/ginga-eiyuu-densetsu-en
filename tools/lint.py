"""lint.py: every `en` in script/*.json passes the batch check rules (tools/batches.py): control codes match the JP,
plain ASCII, every word fits its box line, glossary spellings. Run by tools/check.py; exit 1 on any error."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches  # noqa: E402

errs = batches.lint([(r["id"], r["en"]) for _, r in batches.rows() if r.get("en")])
errs += [f"{r['id']}: jp without en" for _, r in batches.rows() if not r.get("en") and not batches.blank(r["jp"])]
for e in errs:
    print(e)
print(f"lint: {len(errs)} errors")
sys.exit(1 if errs else 0)
