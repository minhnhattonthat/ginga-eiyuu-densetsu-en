# Game flow, scene warps and the debug tool

Everything here is **verified** by `tools/debug/regen.py` (every scene in `tools/debug/scenes.lua` reached from a
cold boot, proof sheet `work/qa/warp/proof.png`) unless marked guess. Disassembly: `dis65816.py`.

## Main state ($00:D343)

- `$E2` mode: 0 attract/intro ($13:8000), 1 title ($07:8FB4), 2 game ($00:D4AB), 3 a leftover debug menu
  ($00:D7A1: 5 items via $D87B, item 1 = event viewer $00:D90E that runs event `$1A62`). Forcing `$E2=3` at boot
  enters it but the screen is garbage (VRAM not set up), so the warp does not use it.
- Title submodes `$E3`: 0 title, 1 LOAD/NEW (`$1A73`, saved in `$1A02`), 2 DATA select (LOAD path), 3 players
  (`$1A73`, 0 = 1PLAY; `$1A03` = 2-player flag), 4 character (`$1A73` → `$1A04`, 0 Yang, 1 Reinhard), 5 scenario
  (`$1A72` → `$1A05`, 3 scenarios: 1. 永遠の夜の中で, 2. はばたく禿鷹, 3. 神々の黄昏), 7 yes/no (`$1A73`, 0 yes).
- Menus share `$00:A15F`: joypad in `$26/$27` (from `$08D4`), result `$1A79` (1 A, 2 B, 3 X, 4 Y, $80/$81
  up/down, $82/$83 left/right), cursors `$1A72` (vertical, limits `$1A74/$1A75`) and `$1A73` (horizontal).
- Controllers: `$11BE` Alliance, `$11BF` Empire (0 player 1, 1 player 2, 2 CPU), set at `$07:973E`.

## Campaign steps

- `$11CA` = step. Scenario start step table `$07:979C` = 00 03 05 (08 unused).
- Step table `$04:8CF4` (file 0x20CF4), 8 bytes per step: stage `$11CB`, chapter `$11CC`, `$E3`, `$E4`, `$E5`,
  `$E6`. Loaded by `$04:8CAE` at game init (`$00:D538`) and after each step (`$00:D586`/`D592`).
  Steps 0-11: 0 battle s0 (Astarte), 1 interlude, 2 battle s1, 3 interlude (scenario 2 start), 4 battle s2,
  5 interlude (scenario 3 start), 6-9 battles s3-s6, 10 interlude (ending), 11 = `$E3=2` staff credits.
- `$00:A56E` sets `$11CB/$11CC` from its own table `$00:A58B`, which ends after step 10: a warp to step 11
  must override them at `$00:A589` (else the game resets).
- Game submode `$E3`: 0 init ($00:D4C2, clears story flags, sets defaults), 1 campaign, 2 credits ($00:D59A).
  In `$E3=1`: `$E4` 0 battle step, 1 interlude ($00:F5B1: events by chapter). Battle phases `$E5`:
  0 briefing ($00:DEAD, events 15 18 1B 1E 20 21 22 by stage), 1 opening speeches ($00:DF14),
  2 admiral placement ($00:E094, msgs 010/011), 3 strategy map + real-time battle ($00:EE43; command menu
  msg 012 from step 2 on), 4 result ($00:F10F; `$E6` sub-phases), 5 aftermath ($00:F564, events 16 19 1C 1F).
- Result event: `$00:F2AB[stage*2 + $0B91]` (2F/2E, 31/30, 33/32, 35/34, 37/36, 39/38, 25/25), `$0B91` = 1 when
  `$1A62 >= $1A64` (losses compared, $00:F269).
- Story flags: bitfield `$1A9D` (32 bytes, bit = 1 << (n & 7)); set `$00:9515`, clear `$00:9538`, test
  `$00:94F8`. Ending event 23 branches on flags 10, 11, 14.

## Events (tools/events.py)

- Runner `JSL $01:8000` (A = event id), pointer table `$01:83F8` (256 entries, bank $01). Opcodes in
  `tools/events.py`. Event 14 = the long opening history, 23/24 endings, 2D a leftover debug flag menu
  (msgs 20A-212: "Lapp? dead/alive", "inquiry? go/don't" ...), 3A+ one-line battle speeches.
- Events draw on whatever screen is up: 14 only renders on the attract-mode screen (cold boot, no input), the
  battle ones (12 13 26-2C, 3A+) only inside a battle (the warp swaps them in for Astarte's event 2A), 2D draws
  nothing outside the debug menu.
- 68 message ids are shown by neither an event nor a direct `LDX #id / JSL $07:979F`
  (`tools/events.py --unreached`); some are empty, the rest come from code tables (to trace in phase 5).

## Command menu (bank $04)

- Top menu `$04:B1F5` (msg 012), cursor `$1A82`: 0 map/info, 1 fleet orders (msg 01B, then attack area 01C),
  2 SYS, 3 end turn (msg 013). SYS cursor `$1A83`: 0 auto battle (015), 1 save (016, 017), 2 animation (018).
- Menu state `$11BC` dispatches through `$04:B163` (word table). After picking a fleet (09 -> 0A) the icon bar
  cursor `$1A83` (left/right) maps via `$04:BC43` to 0B attack area, 0D, 0E detach division (`$04:C0C9`, panel
  with ship types, G8; needs `$1AC1` > 1 divisions), 0F, 10, 11.
- Mashing A in SYS → save writes `tools/mesen/Saves/*.srm` (the save confirm defaults to yes).

## The warp (tools/debug/warp.lua)

Drives the real title menus by writing each submode's cursor and pressing A (gated on `$E2/$E3`, not frame
counts), forces side and 1 player at `$07:9733`, the step at `$07:9775`, stage/chapter at `$00:A589`; patches the
step table in PRG ROM for a start phase (`e5`/`e6`), the event table for an event swap, `$0B91` at `$00:F296`
for the result, flags at `$00:D538`. Arrival is a message open, an event start or RAM bytes.
Scene groups: title menus, `intro`, `stepNN_<side>` (every step from its start), `stepNN_<side>_result0/1` and
`_after` (battle outcomes and aftermaths), `ending_*` (4 flag branches x 2 sides), `credits`, `astarte_*`
phases, `cmd_*`/`sys_*` command menus (step 2), `evNN` (events no step starts with).
