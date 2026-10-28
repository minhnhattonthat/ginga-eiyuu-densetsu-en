# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8 (visual QA), round 7 passed (2026-10-28): `qa_gate check` 541/541 (r7c full re-tour with the
  no-wait +2/+4 shots, 16 chunks; r7d 27 sheets after m086/m087 "between two fortresses" and the new intro
  narration shot: tourpress shoots when the next message opens if the last one had no key wait, since the intro
  narration types with $1116 = 1 and never got a text frame). Controller overrides in verdicts/r7c_main.tsv:
  credits/sheet_17 (shot on the title's first mosaic fade step; clean f10199-10229), evFD (emblem is a transient
  frame; portrait up by f68). Next: polish pass, then release (phase 9). Round 6's pass covered only what a 12000-frame tour
  showed: nearly every scene was cut mid-text (event 1A m05A-082, endings, all cut-ins 3A-FF never in a sheet).
  Round 7: cut-in scenes ev3A-evFF, step03_rein_no, ending_f0F11 added; story tours 60000 frames, cut-ins 1500;
  `tour.py --unique` keeps each (message, box) once (`--resheet` redoes it with no emulator). Every event message
  but 2D (debug menu) now reaches a sheet. Round 7a (10 of 16 chunks) found: m213/214/215/219 and ev26/28/29 lines
  open in the 9x5 cut-in in play (boxes.json was from the 12000-frame probe; now from `boxes.py work/qa/probe
  work/qa/tour_jp`), m03A/m03B tightened; and every story state predated the last text commit (a state saved
  mid-message reads another string on a rebuilt ROM: tour.py now refuses states older than the ROM).
  Round 7b/7c: rebuild, regen all, re-tour (`work/qa/r7c_*.log`), `qa_gate init` (identical sheets keep verdicts).
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
    plates (3x5 caps in the sheet's own 50 tiles, maps moved to 0x17F00), G8 ship-type labels (3x5 caps; seen on the
    detach-division panel, warp scene `cmd_detach`, debug.md §Command menu). `tools/debug/vramsweep.py` (VRAM dump of every state + free-tile check),
    `tools/lua/callx.lua` (log a routine's calls with registers).
  - G11 title logo + G16 copyright (2026-10-26): own stream $13:A9F2 with a third codec (`gfx.decompress_title`,
    roundtrip test), redrawn by `gfxtext.title` (LEGEND OF THE / GALACTIC HEROES; copyright in Ark 12px), stream
    moved to the bank $13 tail (trap3: 0 reads), checked in game. States regenerated, warp tour 101/101.
  - Phase 8 QA tour (2026-10-27): `tools/tour.py` (+ `tools/lua/tourpress.lua`: shot per complete box, then A),
    JP side from `work/states_jp` (regen `--states`). Two review rounds (visual-qa agents) found and fixed: result
    scenes crashed at m134 (number digits written as JP $89: `$00:F557` now ASCII), officer plates clipped at 56 px on
    the formation panel, FLEET/SENIOR ADMIRAL rank plates left a 7th tile on screen (now two lines, 4 tiles), m013
    YES/NO (`/{yesno}` typo; lint now fails `/` touching a code), one-word last pages (lint rule `widow`), tour
    artefacts (early press, `--changed 0.02` dropped text pages). Round 3 (r3b, 455 sheets): m03A line 1 under
    the rank plate; SYS bar "nimation" (slot 6 clear wiped the label's first column, engine.md); m017/m06B YES/NO on
    line 2 while the cursor highlight stays on the JP's line 3 (lint rule: `{yesno}` on the JP's line). Round 4
    (452 sheets): battle cut-ins (events 3A-FF) are the 9x5 box at 112 px, not 13x3 (boxes.py; m13A ran off the
    box and never finished); `{speed}` halved in that box by an engine hook (shouts ended 2 frames before the box
    closed; JP ~20); s0B/s0C "the Alliance has"/"the Empire has" (fit 112 px); m146; m0B0 line 1 under the plate.
    Round 6 (473 sheets; after the speaker-turn page lint, 16 msgs padded, m0A7 split, m03B Joint Operational):
    m049/m0BE/m0B8 new paragraph landed mid-page where the JP starts a page (padded/tightened). m13A (long
    fleet-count shout) is closed by the battle timeout before its wait; the JP's is too (probe e29jp), so ok. A lint
    rule for paragraph page starts was tried and dropped: 29 hits, mostly narration where sharing a page is fine.
- **Next:**
  1. After any change that touches text, fonts or the engine: regen, tour, a fresh manifest (old rounds go to
     work/qa/oldN; round 7 is the current one in work/qa/verdicts, round 6 in old6), visual-qa agents, `check` exit 0.
     Controller overrides say why in their note (round 6: verdicts/r6_controller.tsv, m13A timeout). After a tour,
     drop manifest ids whose sheet no longer exists (a shorter run makes fewer sheets).
  2. Translator-flagged in-game items: done. m026/m0D8 seen ok; m0E3, m20A-211, m238 are the debug menu (event 2D)
     only; s0E/s11/s13-s17 are called by no message (dead); m13E (ev40) matches the JP; m13E-163 and m071-073 are
     in round 7's sheets.
  3. Polish pass (m0A7, speaker-turn pages, Joint Operational done): Minors deferred from review (reports were in the session; re-review sampled ~150 before release).
     Round 7 candidates: Kircheis "Yes, Reinhard-sama." (~115 px) wraps in the 112 px cut-in; speaker name on its
     own line vs "Name:" follows the JP (m085, m0BD, m16E), left as is.
  4. Carried over: message ids no event/direct call shows (`tools/events.py --unreached`) and no tour logged keep
     boxes.py's "jp" guess (narrowest box the JP fits); m213-219 were among them and turned out to be 9x5.
- **Open bugs:**
  - none. (Closed: the "empty box after Front" was the Front/All Sides/Focus picker waiting for input; same route
    from `cmd_fleet` gives the same frames and screens in JP, m01C at f378 both, `work/qa/probe/d3.png`.)
- **Waiting on the user:** nothing.
