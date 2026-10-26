# Graphics and graphics text

## Resource system (verified: disassembly of $00:93FC, every block decompresses to tiles, `tools/gfx.py`)

- Graphics id X -> $07:82C8 + 4*X = (entry index, VRAM dest/2); entry -> $07:8000 + 2*entry = (bank, slot);
  directory at `bank:$8000` + 4*slot = (src addr in that bank, tile count). 356 (bank, slot) blocks in banks
  $08-$0E, $10.
- Compression: per tile one mask byte per plane, bit = 1 read a new row byte / 0 repeat the previous row.
  `$00:9272` 2bpp, `$00:92DD` 3 planes into 4bpp (plane 3 = 0).
- Tilemaps: `$00:8F66` loads map X from the directory at $16:8000 (8 bytes per entry: src, dest, size; bank $16
  = file 0xB0000); `$00:911E`/`$00:9157` fill a map rectangle with one word (table $00:9183). `$00:9043` and
  `$00:90EA` not read yet.
- Everything is unpacked into the WRAM VRAM shadow $7F:0000-FFFF and DMAd from there ($00:815E).
- Survey: `python -X utf8 tools/gfx.py sheets work/gfx` then `tools/pack_pages.py work/gfx work/gfx_pages`.

## Graphics-text survey (static sweep of all 356 blocks + the first tour; ids are bank_slot)

| # | Element | Blocks | Format | Seen in game | Notes |
|---|---|---|---|---|---|
| G1 | Officer name plates (fleet panel, assignment) | 08_3D-08_70 (52) | 2bpp, 9x2 tiles (left 64 px shown) | yes (パエッタ, メルカッツ) | **English** (tools/gfxtext.py, Ark Pixel 10px; seen in `astarte_assign`, `cmd_fleet`) |
| G2 | Flagship name plates (no place names) | 09_00-09_24 (37) | 2bpp, 9x2 | not yet | **English** (gfxtext.py; ship order differs from the name tables, mapped by eye) |
| G3 | Battle title banners (アスターテ会戦, アムリッツァ星域会戦 ...) | 09_25-09_2B (15x2), 08_37-08_3C + 08_74 (26x2 briefing bar) | 2bpp | yes (`astarte_brief`) | **English** (gfxtext.py; JP outlines spill into the frame rows, redrawn) |
| G4 | Rank plates (司令官 元帥 上級 大将 中将 少将 准将 大尉) | 08_35 tiles 0-49 (sheet at BG3 $100) via bank-$02 maps 29-36 ($02:8054; drawn by $00:A5C4) | 2bpp | yes | **English** (gfxtext.py `ranks`: 3x5 caps, one tile row; maps moved to 0x17F00). 一般将校 is plate 08_70 (G1). VRAM after the sheet is used by result screens: don't grow it |
| G5 | Title menu buttons (LOAD NEW DATA 1PLAY 2PLAY ON OFF), NO DATA | 08_30, 08_31, 08_71 | 2bpp | yes | already English |
| G6 | Title character buttons (ヤン, ラインハルト) | 08_31 tiles 60-80 (BG3 tile = block tile + $80; 09_32 is only portraits) | 2bpp | yes | **English** (gfxtext.py btn_rein/btn_yang) |
| G7 | Command help labels (攻撃 移動 終了 艦隊 ...) | 0E_0F-0E_18, 0E_27-0E_31 (icons: the rest of 0E_00-0E_31, no text) | 2bpp, 3x2 -> 6x2 | yes (`cmd_menu`, `cmd_fleet`, `cmd_area`) | **English** (gfxtext.py `label` + engine.md §Command buttons) |
| G8 | Battle UI labels (戦艦 巡航艦 ...?) | 0E_37-0E_3E | 2bpp | not yet | |
| G9 | Staff credits font | 0E_36 | 2bpp | no | romaji already (NOBUAKI IKEUCHI ...): check the credits screen |
| G10 | Unclear text-like blocks | 08_2F, 09_2F-09_31, 09_33, 10_06, 10_2F, 0D_0F, 0D_1B | mixed | no | confirm in game or rule out |
| G11 | Title logo 銀河英雄伝説 | not in the directory | ? | yes | official English title exists (D5): add it |
| G12 | Council screen header bar | ? | ? | yes (first council) | source unknown |
| G13 | Scenario title bars (1. 永遠の夜の中で, 2. はばたく禿鷹, 3. 神々の黄昏) | 09_2C-09_2E (15x2, same style as G3) | 2bpp | yes (`title_scenario`) | **English** (gfxtext.py): In Eternal Night / The Vulture Soars / Twilight of the Gods |
| G14 | Command menu icons + 終了 button | = G7 | | yes (`cmd_menu`) | 終了 is a G7 label; icons have no text |
| G15 | Credits logo "Heldensagen vom Kosmosinsel" + staff names | ? | ? | yes (`credits`) | already German/English |

## Free space candidates (0xFF runs at bank ends; trap-test before use, docs: pipeline.md §Recon)

Banks $0F and $1F all 0xFF (32 KB each), $12 0x090635-0x097FFF, $06 0x034400-0x037FFF (after the font, glyph
0x220+), $0E 0x074084-0x077FFF, $1C 0x0E386E-0x0E7FFF, $1E 0x0F3F6C-0x0F7FFF, $05 0x02F883-0x02FEFF, plus 1-11 KB
at the end of most other banks (`python -X utf8 tools/gfx.py list` and the bank-tail scan in git history).
