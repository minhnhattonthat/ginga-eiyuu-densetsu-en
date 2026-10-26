# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5 (engine spike + marker build) done 2026-10-26. Next: phase 6 (translate).
- **Done:**
  - Step 0: MesenCE 2.2.1 in `tools/mesen/`, guard hook proven, pre-commit runs `tools/check.py`, rom.sha1.
  - Recon (`docs/re/text.md`, `docs/re/graphics.md`): encoding + `tbl/jp.tbl`, control codes, main table (571
    msgs, bank $05), substring table (24), bank-$02 name tables, 12x16 font at 0x30000, graphics directory +
    compression (`tools/gfx.py`), graphics-text survey (G1-G15), free space. `tools/extract.py` writes
    `script/{main,sub,names}.json` (jp only).
  - Debug tool (`docs/re/debug.md`): `tools/debug/warp.lua` + `scenes.lua` (100 scenes), `tools/debug/regen.py`,
    `tools/events.py` (event scripts -> message ids).
  - Identity build: `tools/build.py` repacks main/sub/name strings from `script/*.json` (field `--lang`, falls back
    to `jp`), rewrites every pointer, fixes the checksum, logs writes to `build/writes.txt` and self-checks with
    romdiff. Output byte-identical; smoke ok. `tests/test_identity.py`: identity, a lengthened-string repack whose
    pointers all decode back, gfx compressor roundtrip (355/356 exact). Rebuild regions in `docs/re/text.md`.
  - Extract: `tests/test_roundtrip.py`: per-string roundtrip, script/*.json jp == ROM, coverage (main, sub, the five
    name tables back to back, no gaps), and the renderer's string pointer has only the four known writers (no other
    text source; whole-ROM jp_left is noise with a 1-byte encoding). `docs/re/text.md` §Extraction coverage.
  - Engine + marker (`docs/re/engine.md`): `asm/engine.asm` (asar) = VWF (Ark Pixel 12px proportional,
    `tools/font.py`), F8 far-text jump (strings overflow bank $05 into bank $0F/$1F), name slots hold a 24-bit
    pointer (no 15-byte cap), names relocated to bank $02 tail. `build.py --marker`: every string `[id] filler` in
    its JP shape; blank (control-code-only) strings kept. Marker tour: 100/100 scenes reached (regen default
    frames now 18000). Width gate: all 6 seen box variants measured in game (table in engine.md; 208/160 px);
    `script/boxes.json` maps each message to its box. `tests/test_engine.py`.
- **Next:**
  1. Phase 6: set up translator batches (work/tl/*.tsv from script/*.json + boxes.json px limits, glossary
     names per D2), batch check (line px <= box px, var 0/1 bottom line before {wait} -8 px), dispatch
     translator agents, reviewer pass.
  2. Carried over: graphics text G1-G8, G13, G14 need a small-font plate generator (phase 7/8); 68 message ids
     no event/direct call shows (`tools/events.py --unreached`) bind to the 17x4 box by default; bank $1F not
     trap-tested yet. work/states are from the marker build before the blank-string change (text only).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
