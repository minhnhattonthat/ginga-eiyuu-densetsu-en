"""Phase-8 QA tour: from each scene's state, shoot every text box once complete and press A
(tools/lua/tourpress.lua), and write full-size contact sheets to <out>/<scene>/sheet*.png for the visual-QA gate
(qa_gate.py).

    python -X utf8 tools/tour.py [SCENE ..] [--rom ROM] [--states work/states] [--out work/qa/tour]
        [--frames 12000] [--idle 300] [--jobs 4] [--unique]
Full coverage (round 7): story scenes need --frames 60000 (12000 cut most mid-text), battle cut-ins ev3A-evFF
1500 (a second run); --unique drops the repeats within a run (sheets then hold each message/box once);
`--resheet --unique` (no scene names = every state) redoes that across all runs already in --out, no emulator.
Japanese side (same scenes, for reviewers to tell the game's own behaviour from a translation bug):
    python -X utf8 tools/debug/regen.py --rom "rom/Ginga Eiyuu Densetsu (Japan).sfc" --states work/states_jp --qa work/qa/warp_jp
    python -X utf8 tools/tour.py --rom "rom/Ginga Eiyuu Densetsu (Japan).sfc" --states work/states_jp --out work/qa/tour_jp
Exit 1 if any scene's run failed.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

PRESS = os.path.join(ROOT, "tools", "lua", "tourpress.lua")
MSGLOG = os.path.join(ROOT, "tools", "lua", "msgcall.lua")  # log.txt lists the messages shown (coverage)


def dedupe(out, scene, seen):
    """Move to out/dup/ every shot whose run of (message, box) already showed in this or an earlier scene.
    A shot belongs to the last message opened before it (log.txt); shots before the first logged open show the
    message the scene's state was saved on, unique to the scene. Blank m000 (box clear) opens while the last page is
    still up, so it starts no run."""
    opens = [(int(m[1]), (m[2], m[3])) for m in
             re.finditer(r"^f(\d+) msg (\w+) ret \w+ var (\d+)", open(os.path.join(out, "log.txt")).read(), re.M)
             if m[2] != "000"]
    shots = sorted((1 << 30 if f == "final.png" else int(f[1:-4]), f) for f in os.listdir(out)
                   if re.fullmatch(r"f\d+\.png|final\.png", f))
    run, keep = None, False
    for frame, f in shots:
        key = next((k for fr, k in reversed(opens) if fr <= frame), ("first", scene))
        if key != run:
            run, keep = key, key not in seen
            seen.add(key)
        if not keep:
            os.makedirs(os.path.join(out, "dup"), exist_ok=True)
            os.replace(os.path.join(out, f), os.path.join(out, "dup", f))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--rom", default=os.path.join(ROOT, "build", "logh_en.sfc"))
    ap.add_argument("--states", default=os.path.join(ROOT, "work", "states"))
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "qa", "tour"))
    ap.add_argument("--frames", type=int, default=12000)
    ap.add_argument("--idle", type=int, default=300, help="frames with no text wait before pressing A anyway")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--unique", action="store_true",
                    help="keep a shot only the first time its (message, box) shows across the scenes; repeats -> dup/")
    ap.add_argument("--resheet", action="store_true", help="no runs: redo --unique and the sheets of the runs in --out")
    a = ap.parse_args()
    names = a.scenes or sorted(f[:-4] for f in os.listdir(a.states) if f.endswith(".mss"))

    def one(n):
        out = os.path.abspath(os.path.join(a.out, n))
        for _ in range(2):  # one retry: a parallel Mesen run occasionally dies
            shutil.rmtree(out, ignore_errors=True)
            r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"),
                                os.path.abspath(a.rom), "--out", out,
                                "--state-in", os.path.abspath(os.path.join(a.states, n + ".mss")),
                                "--frames", str(a.frames), "--script", PRESS, "--script", MSGLOG,
                                "--var", f"IDLE={a.idle}",
                                "--timeout", "600"], capture_output=True, text=True)
            if r.returncode == 0:
                break
        print(("ok   " if r.returncode == 0 else f"FAIL {r.returncode} ") + n, flush=True)
        return r.returncode == 0

    def restore(n):  # undo an earlier dedupe and its sheets
        out = os.path.join(a.out, n)
        for f in os.listdir(out):
            if f.startswith("sheet"):
                os.remove(os.path.join(out, f))
        dup = os.path.join(out, "dup")
        for f in os.listdir(dup) if os.path.isdir(dup) else []:
            os.replace(os.path.join(dup, f), os.path.join(out, f))
        return os.path.isfile(os.path.join(out, "log.txt"))

    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(restore if a.resheet else one, names))
    bad = [n for n, ok in zip(names, results) if not ok]
    seen = set()
    for n in [n for n in names if n not in bad]:
        out = os.path.join(a.out, n)
        if a.unique:
            dedupe(out, n, seen)
        # --changed 0.02 dropped whole text pages (a page of text is <2% of the pixels)
        subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "sheet.py"), out,
                        "--changed", "0.001", "--div", "1", "--out", os.path.join(out, "sheet.png")],
                       capture_output=True, text=True)
    print(f"{len(names) - len(bad)}/{len(names)} scenes toured" + (": FAILED " + " ".join(bad) if bad else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
