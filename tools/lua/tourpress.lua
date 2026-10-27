-- QA tour driver (tools/tour.py): shoot each text box once it is complete and waiting for a key ($1116 = 5 end
-- wait, 7 full box; 3 = typing), then press A. With no text wait for IDLE frames (menus, battles; 1200 while
-- typing), press A anyway and shoot, so the run still moves on.
local mem = emu.memType.snesMemory
local IDLE = IDLE or 300
local held, idle, prev, nowait = 0, 0, 0, -100
local waited, opened = true, false
-- intro narration types on with $1116 already 1 (no wait, no box): shoot it when the next message opens, named a
-- frame early so tour.py's dedupe files it under the message it shows. m000 (box clear) opens 5 frames after a cut-in.
L.on_exec(0x0797A0, 0x0797A0, function()
  local id = emu.getState()["cpu.x"]
  if id == 0 then return end
  if opened and not waited then L.shot(string.format("f%06d.png", L.frame - 1)) end
  opened, waited = true, false
end)
L.on_frame(function(n)
  if not L.route_done() then return end
  local s = emu.read(0x7E1116, mem)
  -- 3 -> 1: the text ended with no wait (battle cut-ins' last page closes on a timer): shoot it after the flush
  -- the last glyph lands ~3 frames later (m0B0's period) and the next message clears the box ~5 later: shoot +2, +4
  if prev == 3 and s == 1 then nowait = n end
  prev = s
  if n == nowait + 2 or n == nowait + 4 then L.shot(string.format("f%06d.png", n)) end
  if s == 5 or s == 7 then held = held + 1 else held = 0 end
  idle = idle + 1
  -- held > 0 blocks the idle press: a press 2 frames after the box fills beats the VWF's last-glyph flush
  if held == 10 or (held == 0 and idle >= (s == 3 and 1200 or IDLE)) then  -- narration types ~150 frames a line: don't cut it
    if held == 10 then waited = true end
    L.shot(string.format("f%06d.png", n))
    L.press("a", 6); L.press("-", 20)
    held, idle = 0, 0
  end
end)
