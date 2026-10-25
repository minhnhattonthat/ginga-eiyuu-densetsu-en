import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM = ROOT / "rom" / "Ginga Eiyuu Densetsu (Japan).sfc"


@pytest.mark.skipif(not ROM.exists(), reason="no ROM")
def test_rom_hash():
    import check_rom
    check_rom.check()
