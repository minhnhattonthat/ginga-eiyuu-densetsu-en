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
  - Phase 7 (2026-10-26): build fails on any write outside `ALLOWED` (build.py); lint fails on jp without en;
    bank $1F + gfx bank tails trap-tested (0 reads); jp_left on text regions: nothing unchanged left (only the
    dead bank-$00 side-name copies). Graphics text via `tools/gfxtext.py` (Ark Pixel 10px): G1 officer plates,
    G2 flagship plates, G3 battle banners (both styles), G13 scenario bars, checked in game.
  - Graphics text (2026-10-26, all in `tools/gfxtext.py`, checked in game unless noted): G6 title buttons, G7/G14
    command help labels widened 3x2 -> 6x2 by engine hooks ($00:A705/A752, engine.md §Command buttons), G4 rank
    plates (3x5 caps in the sheet's own 50 tiles, maps moved to 0x17F00), G8 ship-type labels (3x5 caps, in ROM
    and tested; screen not found yet). `tools/debug/vramsweep.py` (VRAM dump of every state + free-tile check),
    `tools/lua/callx.lua` (log a routine's calls with registers). States regenerated on the current build.
- **Next:**
  1. Graphics text left: G11 title logo + G16 copyright lines (boot route, after start, f650-f850; graphics.md),
     G8 in-game check (find the screen: 15000-frame A-mash runs from sys_auto, astarte_command and cmd_menu
     never called $00:CCDE; trace the indirect caller, or it may be unused), G10/G12 unconfirmed blocks. Then regen states and run the full warp tour.
  2. Phase 8 QA, items flagged by translators to see in game: m0E3 "Alliance    Empire" and m20A-m211/m238
     two-option menus (cursor columns), m13E-m163 `{sub0:0D}` joined to the next line, m071-m073 {speed} after the
     speaker colon, m026 indent, s0E ",000 ships" / s11 "Supply" / s13-s17 (where are they drawn?), m0D8 4th line
     exactly 208 px with {sub0:09}.
  3. Polish pass (Minors deferred from review; reports were in the session, re-review sampled ~150 before release).
  4. Carried over: 68 message ids no event/direct call shows (`tools/events.py --unreached`) bind to the 17x4 box
     by default.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
