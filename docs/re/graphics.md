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
| G8 | Ship-type labels (戦艦 巡航艦 空母 駆逐艦 要塞 輸送艦 隕石 高速戦艦) | 0E_37-0E_3E = gfx ids $184-$18B -> BG3 $210, 6x2 map by $00:CCD6 (A = type, X = position; $CCDE, hooked by earlier runs, is mid-instruction), called only from $04:D430 (fleet panel routine that also draws the rank via $00:A5C4; type = $7E2F2B + 7*fleet); screen: fleet orders -> 3rd icon (detach division, menu state $11BC=0E -> $04:C0C9) | 2bpp | yes (`cmd_detach`) | **English** (gfxtext.py `shiptype`, 3x5 caps; BATTLESHIP checked in game, other types same tiles/path) |
| G9 | Staff credits font | 0E_36 | 2bpp | no | romaji already (NOBUAKI IKEUCHI ...): check the credits screen |
| G10 | Unclear text-like blocks | 08_2F, 09_2F-09_31, 09_33, 10_06, 10_2F, 0D_0F, 0D_1B | mixed | no | **ruled out**: no text. 08_2F = big digit/segment font; 09_2F-31 (one stream), 09_33, 0D_0F = portrait art (3 planes); 0D_1B illustration; 10_06, 10_2F ship/machinery parts. None of 09_33/0D_0F/0D_1B/10_06/10_2F is in any warp scene's VRAM |
| G11 | Title logo 銀河英雄伝説 | own stream $13:A9F2 (0x13D tiles, BG1 VRAM 0; loaded at $13:8602 by $00:86AD, a third codec: `gfx.decompress_title`), tiles 1-$91, raw map $13:BD39 | 3 planes in 4bpp | yes (boot route, start at f600; logo f650-f850) | **English** (gfxtext.py `title`: LEGEND OF THE / GALACTIC HEROES, JP row gradient + green extrusion); stream moved to the bank $13 tail, checked in game |
| G16 | Copyright lines under the logo (©1991 田中芳樹・徳間書店 / 徳間ジャパンコミュニケーションズ / キティフィルム・テレビ東京 / ©1992 徳間書店インターメディア) | same stream, tiles $92-$127 (shared across lines), raw map $13:BE79 (BG1 rows 19-26, palette 4) | | yes (same screen as G11) | **English** (Ark Pixel 12px, JP © kept; new tiles also at $13D+, unused VRAM there, tile count raised at $13:860F), checked in game |
| G12 | Council screen header bar | = G3 26x2 briefing bar | | yes (`astarte_brief`, "Battle of Astarte") | **English** via G3 |
| G13 | Scenario title bars (1. 永遠の夜の中で, 2. はばたく禿鷹, 3. 神々の黄昏) | 09_2C-09_2E (15x2, same style as G3) | 2bpp | yes (`title_scenario`) | **English** (gfxtext.py): In Eternal Night / The Vulture Soars / Twilight of the Gods |
| G14 | Command menu icons + 終了 button | = G7 | | yes (`cmd_menu`) | 終了 is a G7 label; icons have no text |
| G15 | Credits logo "Heldensagen vom Kosmosinsel" + staff names | ? | ? | yes (`credits`) | already German/English |

## Free space candidates (0xFF runs at bank ends; trap-test before use, docs: pipeline.md §Recon)

Banks $0F and $1F all 0xFF (32 KB each), $12 0x090635-0x097FFF, $06 0x034400-0x037FFF (after the font, glyph
0x220+), $0E 0x074084-0x077FFF, $1C 0x0E386E-0x0E7FFF, $1E 0x0F3F6C-0x0F7FFF, $05 0x02F883-0x02FEFF, plus 1-11 KB
at the end of most other banks (`python -X utf8 tools/gfx.py list` and the bank-tail scan in git history).
