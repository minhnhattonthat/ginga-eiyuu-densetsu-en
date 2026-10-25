# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2 (debug tool) done 2026-10-26. Next: phase 3 (identity build). No build yet.
- **Done:**
  - Step 0: MesenCE 2.2.1 in `tools/mesen/`, guard hook proven, pre-commit runs `tools/check.py`, rom.sha1.
  - Recon (`docs/re/text.md`, `docs/re/graphics.md`): encoding + `tbl/jp.tbl`, control codes, main table (571
    msgs, bank $05), substring table (24), bank-$02 name tables, 12x16 font at 0x30000, graphics directory +
    compression (`tools/gfx.py`), graphics-text survey (G1-G15), free space. `tools/extract.py` writes
    `script/{main,sub,names}.json` (jp only).
  - Debug tool (`docs/re/debug.md`): `tools/debug/warp.lua` + `scenes.lua` (100 scenes: title menus, intro,
    every campaign step x side, battle results/aftermaths, 4 endings x 2 sides, credits, command/SYS menus,
    in-battle events), `tools/debug/regen.py` regenerates `work/states/<scene>.mss` and the proof sheets
    `work/qa/warp/proof*.png` (all scenes reached from a cold boot). `tools/events.py` maps event scripts to
    message ids (test: `tests/test_events.py`).
- **Next:**
  1. Phase 3 identity build (`tools/build.py` -> build/logh_en.sfc byte-identical), phase 4 roundtrip test
     (`tests/test_roundtrip.py` over the extractor).
  2. Phase 5 engine: VWF in the 12px renderer ($07:9B66-9D9F, canvas at tile $2B0); 16-byte name slots
     $1F10-$1F6F cap names at 15 bytes; graphics text G1-G8, G13, G14 need a small-font plate generator.
     Trace the 68 message ids no event/direct call shows (`tools/events.py --unreached`): code tables.
- **Open bugs:** none (no build).
- **Waiting on the user:** nothing.
