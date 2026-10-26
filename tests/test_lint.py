"""Lint rules on made-up text (no ROM needed)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import batches  # noqa: E402
import wrap  # noqa: E402


def test_no_one_word_last_line():
    game, _ = wrap.wrap("Yang declared that this was the work of Reinhard von Lohengramm of the Empire.", 208)
    lines = game.split("{nl}")
    assert len(lines) == 3 and lines[-1] == "the Empire."
    assert wrap.wrap("Short. / Yes.", 208)[0] == "Short.{nl}Yes."     # a one-word paragraph stays


def test_widow():
    assert batches.widow("a b{nl}c{nl}d{nl}e{nl}me.\"", 4) == "me.\""
    assert batches.widow("a{nl}b{nl}c{nl}d{nl}two words", 4) == "two words"
    assert batches.widow("a{nl}b{nl}c{nl}d{nl}three whole words", 4) == ""
    assert batches.widow("a{nl}b{nl}c{nl}d{nl}{wait}{nl}", 4) == ""       # trailing blank lines don't page
    assert batches.widow("a{nl}{sub0:08}.", 1) == "X."
    assert batches.widow("one{nl}two", 3) == ""
