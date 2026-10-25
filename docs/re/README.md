# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| text.md | encoding, control codes, message/substring/name tables, 12x16 font, renderer | verified (decode + disassembly); renderer layout partly guessed |
| debug.md | game state machine, campaign steps, events, command menu, the warp tool | verified (regen.py, all scenes reached) |
| graphics.md | resource directory, tile compression, graphics-text survey, free space | directory/compression verified; survey preliminary |
