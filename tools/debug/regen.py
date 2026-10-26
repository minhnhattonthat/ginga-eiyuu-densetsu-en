"""Warp to every scene in tools/debug/scenes.lua from a cold boot (or the named ones), save a state per scene
in work/states/<scene>.mss and a proof sheet of the arrival shots in work/qa/warp/proof*.png.
Exit 1 if any scene was not reached.

    python -X utf8 tools/debug/regen.py [SCENE ...] [--rom ROM] [--jobs 3] [--frames 8000]
        [--lua probe.lua ...] [--qa DIR] [--no-states | --states DIR]    (probe runs: trap tests, message/box logs)
"""
import argparse
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

EMU = os.path.join(SKILL, "scripts", "emu.py")
WARP = os.path.join(ROOT, "tools", "debug", "warp.lua")
QA = os.path.join(ROOT, "work", "qa", "warp")


def run(rom, out, scene, frames, state=None, lua=(), settle=None):
    cmd = [sys.executable, "-X", "utf8", EMU, rom, "--out", out, "--script", WARP, "--frames", str(frames),
           "--timeout", "900", "--var", f"SCENE='{scene}'", "--var", "WARP_STOP=true"]
    if settle:
        cmd += ["--var", f"WARP_SETTLE={settle}"]
    for s in lua:
        cmd += ["--script", s]
    if state:
        cmd += ["--var", "WARP_STATE=[[" + state.replace("\\", "/") + "]]"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "emu.out"), "w", encoding="utf-8") as f:  # why a run died
        f.write(f"exit {r.returncode}\n{r.stdout}\n{r.stderr}")
    log = os.path.join(out, "log.txt")
    return open(log, encoding="utf-8", errors="replace").read() if os.path.exists(log) else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenes", nargs="*")
    default = os.path.join(ROOT, "build", "logh_en.sfc")
    if not os.path.exists(default):
        default = os.path.join(ROOT, "rom", "Ginga Eiyuu Densetsu (Japan).sfc")
    ap.add_argument("--rom", default=default)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--frames", type=int, default=22000)  # intro_late arrives ~f15900 (JP), ~10% later in English
    ap.add_argument("--lua", action="append", default=[], help="extra probe script run beside warp.lua")
    ap.add_argument("--qa", default=QA, help="output dir (default work/qa/warp)")
    ap.add_argument("--no-states", action="store_true", help="don't overwrite work/states")
    ap.add_argument("--states", default=os.path.join(ROOT, "work", "states"), help="state dir (JP: work/states_jp)")
    ap.add_argument("--settle", type=int, help="frames from arrival to the shot, for every scene")
    a = ap.parse_args()
    qa = os.path.abspath(a.qa)
    rom = os.path.abspath(a.rom)

    names = a.scenes or [l.split()[1] for l in run(rom, os.path.join(qa, "_list"), "?list", 60).splitlines()
                         if l.startswith("SCENE ")]
    if not names:
        sys.exit(f"no scenes listed (warp.lua failed? see {qa}/_list/log.txt)")
    proof = os.path.join(qa, "_proof")
    if not a.scenes:  # a full run starts the proof sheets afresh; a partial one updates its scenes only
        shutil.rmtree(proof, ignore_errors=True)
    os.makedirs(proof, exist_ok=True)
    os.makedirs(a.states, exist_ok=True)

    def one(n):
        out = os.path.join(qa, n)
        state = None if a.no_states else os.path.join(os.path.abspath(a.states), n + ".mss")
        for _ in range(2):  # one retry: with several parallel Mesen runs one occasionally dies mid-run
            shutil.rmtree(out, ignore_errors=True)
            log = run(rom, out, n, a.frames, state, [os.path.abspath(s) for s in a.lua], a.settle)
            ok = f"WARP {n} reached" in log and os.path.exists(os.path.join(out, "warp.png"))
            if ok or f"WARP {n} NOT reached" in log:
                break
        if ok:
            shutil.copy(os.path.join(out, "warp.png"), os.path.join(proof, n + ".png"))
        print(("ok   " if ok else "FAIL ") + n, flush=True)
        return ok

    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(one, names))
    shots = sorted(os.path.join(proof, f) for f in os.listdir(proof))
    if shots:  # explicit files: sheet.py only globs f<frame>.png in a directory
        subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "sheet.py"), *shots,
                        "--out", os.path.join(qa, "proof.png")])
    bad = [n for n, ok in zip(names, results) if not ok]
    print(f"{len(names) - len(bad)}/{len(names)} scenes reached" + (": FAILED " + " ".join(bad) if bad else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
