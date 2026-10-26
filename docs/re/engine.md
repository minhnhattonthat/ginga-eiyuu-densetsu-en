# English engine (asm/engine.asm)

Applied by `tools/build.py` to every `--lang en` build (asar 1.91 in `tools/asar/`, committed with its licences,
from https://github.com/RPGHacker/asar/releases v1.91). Asar sizes immediates by value, not by REP/SEP: write
`.w`/`.b` on every immediate (an unsized `ldx #46` under X16 hung the first build). Verified: `tests/test_engine.py` (hook bytes, every pointer
reaches its string through `{far}` stubs, far strings stay in their bank) and the marker tour (every scene).

## Hooks (each asserts the original bytes)

| Site | Was | Now | Why |
|---|---|---|---|
| $07:9BBF | glyph address calc + 12px pitch draw | `JML vwf_draw` ($0F:8000) | VWF |
| $07:9A39 | FF handler (`LDA $117E`) | `JML ff_code` | F8 = far jump; F9-FB/FF as before |
| $00:F46B | copy a name into its 16-byte RAM slot | `JML name_slot` | slot gets `F8 <24-bit ptr>`: no name length cap |
| $00:F4D7/F4DE/F4E3 | side name source $00:F4EE/F4F6 | $0F:8E00/8E80 | 同盟軍/帝国軍 lived inside code (8 bytes) |

## VWF (verified: title box in the marker build, `work/qa/warp/proof*.png`)

- The canvas is unchanged: linear 2bpp tiles from `$1118` (VRAM word $6000 + 8*tile), row stride `$117F - 2`
  tiles, a text line = a top tile row + the row below. `$1167` = canvas column of the pen (as before), `$111E` =
  pen pixel offset in that column (was: odd/even glyph flag). Every line start (opener, `{nl}`, message end) sets
  both to 0, so the VWF clears its buffer when `$111E` is 0.
- Buffer `$1127-$1156`: 3 tile columns x 16 rows; scratch `$1157-$1165`, long glyph pointer `$C1-$C3`. All of
  `$1125-$1166` was private to the old drawer (every reader is in $07:9BBF-9D91).
- Glyphs < $100: English font at $0F:9000 (32 bytes each, JP layout), advance table $0F:8F00. Glyphs >= $100
  (D0/D1 xx): the JP kanji at 12 px. Up to 16 px wide; tiles touched are queued through the game's DMA queue
  ($00:8B60: four 256-byte blocks at $0231-$0531; entry `80 lo hi 08` + 8 x (plane 0, plane 1 = `$116B`), `FF`).
- Font: `fonts/ark-pixel-12px-proportional-latin.bdf` (Ark Pixel 12px proportional, OFL 1.1, docs/fonts.md),
  converted by `tools/font.py` (space forced to 4 px). Average ~5.8 px per char: ~36 chars in a 208 px line.

## Text layout (build.py)

- `{far:XXXXXX}` (F8 + 24-bit address): main and sub strings that don't fit bank $05 leave a 4-byte stub there;
  the string goes to FAR_REGIONS (bank $0F $B000-$FFFF, bank $1F). The byte fetch ($07:9DE3) increments only
  the 16-bit address, so no string may cross a bank (the allocator never splits one).
- Names: all five bank-$02 tables' strings move to the bank $02 tail 0x16DEA-0x17FFF (pointer tables stay put).
- Free space trap-tested (tools/lua/trap.lua over all 100 warp scenes on the original ROM, no reads): bank $0F,
  bank $02 tail, bank $05 0x2F883-0x2FEFF. Bank $1F: not trap-tested yet (all 0xFF, no directory entry).

## Boxes (width gate; `tools/boxes.py` -> `script/boxes.json`, `tools/widthgate.py`)

- Box setup $07:9E84: X = width in JP chars (w), Y = lines (h); `$117F` = w + w/2 + 3 tiles with the frame, so
  the canvas is 8 * (w + w/2 + 1) px wide: 17 -> 208 px, 13 -> 160 px, 9 -> 112 px. Variants ($11A1, table
  $07:9E5A: x, y, w, h): 0 17x2 title, 1 17x4 battle start lines, 2 13x3 admiral placement, 3 13x3 battle /
  command menu, 4 9x5 (not seen), 5 17x4 results, 6 17x4 story.
- Boxes scroll ($07:99D1 newline: past h lines it scrolls), so the line count is no limit; only the width is.
- Measured in game (`tools/widthgate.py`, 2026-10-26; ruler `[px]ooo|` ends whole, every torture glyph distinct):

| Var | Box | Line px | Lines | Seen at | Notes |
|---|---|---|---|---|---|
| 0 | 17x2 title / menus | 208 | 2 | title_loadnew | {wait} blink cursor covers the last ~8 px of the bottom line |
| 1 | 17x4 battle briefing | 208 | 4 | astarte_brief | same cursor; box closes by itself ~240 frames in |
| 2 | 13x3 admiral placement | 160 | 3 | astarte_assign | |
| 3 | 13x3 battle / command | 160 | 3 | cmd_menu | portrait left of the text |
| 4 | 9x5 | 112 | 5 | never seen | no message binds to it (`script/boxes.json`) |
| 5 | 17x4 results | 208 | 4 | step00_yang_result0 | types slowly, `{speed}` ignored |
| 6 | 17x4 story | 208 | 4 | intro | |

- Translation limit: line px from `script/boxes.json` (narrowest box a message was seen in); a line that ends at a
  `{wait}` in var 0/1 keeps 8 px clear. Control-code-only strings (24 main, 2 empty name slots) are not text:
  `build.blank()` keeps them as JP bytes.
