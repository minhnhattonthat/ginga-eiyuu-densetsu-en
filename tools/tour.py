"""Phase-8 QA tour: from each scene's state, shoot every text box once complete and press A
(tools/lua/tourpress.lua), and write full-size contact sheets to <out>/<scene>/sheet*.png for the visual-QA gate
(qa_gate.py).

    python -X utf8 tools/tour.py [SCENE ..] [--rom ROM] [--states work/states] [--out work/qa/tour]
        [--frames 12000] [--idle 300] [--jobs 4]
Japanese side (same scenes, for reviewers to tell the game's own behaviour from a translation bug):
    python -X utf8 tools/debug/regen.py --rom "rom/Ginga Eiyuu Densetsu (Japan).sfc" --states work/states_jp --qa work/qa/warp_jp
    python -X utf8 tools/tour.py --rom "rom/Ginga Eiyuu Densetsu (Japan).sfc" --states work/states_jp --out work/qa/tour_jp
Exit 1 if any scene's run failed.
"""
import argparse
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

PRESS = os.path.join(ROOT, "tools", "lua", "tourpress.lua")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--rom", default=os.path.join(ROOT, "build", "logh_en.sfc"))
    ap.add_argument("--states", default=os.path.join(ROOT, "work", "states"))
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "qa", "tour"))
    ap.add_argument("--frames", type=int, default=12000)
    ap.add_argument("--idle", type=int, default=300, help="frames with no text wait before pressing A anyway")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    names = a.scenes or sorted(f[:-4] for f in os.listdir(a.states) if f.endswith(".mss"))

    def one(n):
        out = os.path.abspath(os.path.join(a.out, n))
        for _ in range(2):  # one retry: a parallel Mesen run occasionally dies
            shutil.rmtree(out, ignore_errors=True)
            r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"),
                                os.path.abspath(a.rom), "--out", out,
                                "--state-in", os.path.abspath(os.path.join(a.states, n + ".mss")),
                                "--frames", str(a.frames), "--script", PRESS, "--var", f"IDLE={a.idle}",
                                "--timeout", "600"], capture_output=True, text=True)
            if r.returncode == 0:
                break
        if r.returncode == 0:  # --changed 0.02 dropped whole text pages (a page of text is <2% of the pixels)
            r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "sheet.py"), out,
                                "--changed", "0.001","--div", "1", "--out", os.path.join(out, "sheet.png")],
                               capture_output=True, text=True)
        print(("ok   " if r.returncode == 0 else f"FAIL {r.returncode} ") + n, flush=True)
        return r.returncode == 0

    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(one, names))
    bad = [n for n, ok in zip(names, results) if not ok]
    print(f"{len(names) - len(bad)}/{len(names)} scenes toured" + (": FAILED " + " ".join(bad) if bad else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
