-- Trap-test free space: log every distinct PC that reads the ranges below (CPU addresses, both mirrors).
-- Run beside warp.lua on the original ROM; a quiet log means the game never touches the space we fill.
--   emu.py ROM --out DIR --script tools/debug/warp.lua --script tools/lua/trap.lua --var "SCENE='intro'" ...
local ranges = TRAP_RANGES or {
  {0x0F8000, 0x0FFFFF},   -- bank $0F (file 0x78000-0x7FFFF): engine code, font, text
  {0x02EDEA, 0x02FFFF},   -- bank $02 tail (file 0x16DEA-0x17FFF): relocated names
  {0x05F883, 0x05FEFF},   -- bank $05 0xFF run after the main strings (file 0x2F883-0x2FEFF)
  {0x1F8000, 0x1FFFFF},   -- bank $1F (file 0xF8000-0xFFFFF): far text
  {0x08EE38, 0x08FFFF},   -- bank $08 0xFF tail (file 0x46E38-0x47FFF): relocated plates
  {0x09E079, 0x09FFFF},   -- bank $09 0xFF tail (file 0x4E079-0x4FFFF): relocated plates
  {0x0EC084, 0x0EFFFF},   -- bank $0E 0xFF tail (file 0x74084-0x77FFF): relocated labels
}
local seen = {}
for _, r in ipairs(ranges) do
  for _, base in ipairs({0, 0x800000}) do
    emu.addMemoryCallback(L.safe(function(addr, value)
      local s = emu.getState()
      local pc = (s["cpu.k"] << 16) | s["cpu.pc"]
      if seen[pc] then return end
      seen[pc] = true
      L.log(string.format("TRAP f%d pc=%06X read %06X", L.frame, pc, addr))
    end), emu.callbackType.read, r[1] + base, r[2] + base, emu.cpuType.snes, emu.memType.snesMemory)
  end
end
