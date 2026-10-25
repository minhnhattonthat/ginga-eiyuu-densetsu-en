# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 3 (identity build) done 2026-10-26. Next: phase 4 (extract roundtrip + coverage test).
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
- **Next:**
  1. Phase 4: `tests/test_roundtrip.py` (encode(decode) per string from the extractor) + coverage test (text ranges
     fully covered: main 0x28476-0x2F882, sub to 0x2FFB7, name tables, no unexplained gaps); `jp_left.py` sweep of
     the original for Japanese runs no extractor table reaches.
  2. Phase 5 engine: VWF in the 12px renderer ($07:9B66-9D9F, canvas at tile $2B0); name tables have zero slack and
     16-byte RAM slots $1F10-$1F6F cap names at 15 bytes (relocate strings to bank $02 tail 0x16DEA+, trap-test);
     graphics text G1-G8, G13, G14 need a small-font plate generator. Trace the 68 message ids no event/direct call
     shows (`tools/events.py --unreached`).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
