# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6 (translate) done 2026-10-26. Next: phase 7 (insert, fit, check).
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
  - Phase 6 setup: `glossary.md` (official names, ASCII, ranks), `docs/synopsis.md`, `docs/style-reference.md`
    (pilot m00A-m031 by the controller, checked in game), `docs/translator-brief.md`, `docs/reviewer-brief.md`.
    `tools/wrap.py` (authored ` / ` breaks -> {nl} lines at box px; build wraps every `en`), `tools/batches.py`
    split/check/merge/pairs. Names + fragments (b001) merged. YES/NO icons in en.tbl (`{yesno}`).
  - Phase 6 translate (2026-10-26): every non-blank string has `en` (main 545, sub 18, names 113). 3 translator
    agents (b002-b008), reviewer pass per batch + pilot: no Critical; Important fixed (星域/宙域 terms, m098, m057,
    m110...). Fit pass fit1: 16 messages that grew past their box's line count while the JP fit (a full box waits
    for A: the attract demo hung on m110; rule now in lint). `tools/lint.py` runs in check.py (0 errors).
    English warp tour 101/101 scenes (regen default frames 22000).
- **Next:**
  1. Phase 7 (insert/fit/check): romdiff ranges check in build, overflow lint already clean; confirm far text space
     and the bank $1F trap test; graphics text G1-G8, G13, G14 (small-font plates, docs/re/graphics.md).
  2. Phase 8 QA, items flagged by translators to see in game: m0E3 "Alliance    Empire" and m20A-m211/m238
     two-option menus (cursor columns), m13E-m163 `{sub0:0D}` joined to the next line, m071-m073 {speed} after the
     speaker colon, m026 indent, s0E ",000 ships" / s11 "Supply" / s13-s17 (where are they drawn?), m0D8 4th line
     exactly 208 px with {sub0:09}.
  3. Polish pass (Minors deferred from review; reports were in the session, re-review sampled ~150 before release).
  2. Carried over: graphics text G1-G8, G13, G14 need a small-font plate generator (phase 7/8); 68 message ids
     no event/direct call shows (`tools/events.py --unreached`) bind to the 17x4 box by default; bank $1F not
     trap-tested yet. work/states are from the marker build before the blank-string change (text only).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
