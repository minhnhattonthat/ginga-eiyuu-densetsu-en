-- Log hits of the addresses in TRACE (CPU addresses; default: the engine entry points in bank $0F) with registers,
-- the first N of each, plus the PC every 30 frames (finds hangs).
--   emu.py ROM --out DIR --script tools/lua/pctrace.lua [--var "TRACE={0x0F8000}"] [--var N=20]
local mem = emu.memType.snesMemory
local list = TRACE or {0x0F8000, 0x00F46B, 0x079A39}
local cap = N or 20
for _, a in ipairs(list) do
  local n = 0
  L.on_exec(a, a, function()
    n = n + 1
    if n > cap then return end
    local s = emu.getState()
    L.log(string.format("f%d hit %06X A=%04X X=%04X Y=%04X P=%02X S=%04X DB=%02X D=%04X", L.frame, a, s["cpu.a"],
      s["cpu.x"], s["cpu.y"], s["cpu.ps"], s["cpu.sp"], s["cpu.dbr"], s["cpu.d"]))
  end)
end
L.on_frame(function()
  if L.frame % 30 == 0 then
    local s = emu.getState()
    L.log(string.format("f%d pc %02X:%04X", L.frame, s["cpu.k"], s["cpu.pc"]))
  end
end)
