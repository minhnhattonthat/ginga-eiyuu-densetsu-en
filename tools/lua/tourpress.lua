-- QA tour driver (tools/tour.py): shoot each text box once it is complete and waiting for a key ($1116 = 5 end
-- wait, 7 full box; 3 = typing), then press A. With no text wait for IDLE frames (menus, battles; 1200 while
-- typing), press A anyway and shoot, so the run still moves on.
local mem = emu.memType.snesMemory
local IDLE = IDLE or 300
local held, idle, prev, nowait = 0, 0, 0, nil
L.on_frame(function(n)
  if not L.route_done() then return end
  local s = emu.read(0x7E1116, mem)
  -- 3 -> 1: the text ended with no wait (battle cut-ins' last page closes on a timer): shoot it after the flush
  if prev == 3 and s == 1 then nowait = n + 8 end  -- +3 missed the last glyph (m0B0); the box closes ~20 later
  prev = s
  if n == nowait then L.shot(string.format("f%06d.png", n)) end
  if s == 5 or s == 7 then held = held + 1 else held = 0 end
  idle = idle + 1
  -- held > 0 blocks the idle press: a press 2 frames after the box fills beats the VWF's last-glyph flush
  if held == 10 or (held == 0 and idle >= (s == 3 and 1200 or IDLE)) then  -- narration types ~150 frames a line: don't cut it
    L.shot(string.format("f%06d.png", n))
    L.press("a", 6); L.press("-", 20)
    held, idle = 0, 0
  end
end)
