-- Log every call of a long routine with A/X/Y and the return address on the stack (JSL pushes K, PC+2).
--   emu.py ... --script tools/lua/callx.lua --var CALL_AT=0x008ED4 [--var FROM=600]
local at, from = assert(CALL_AT, "set --var CALL_AT=0x..."), FROM or 0
L.on_exec(at, at, function()
  if L.frame < from then return end
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local function rd(a) return emu.read(a, emu.memType.snesMemory) end
  local ret = (rd(sp + 3) << 16) | (rd(sp + 2) << 8) | rd(sp + 1)
  L.log(string.format("f%d call %06X a=%04X x=%04X y=%04X from %06X", L.frame, at, s["cpu.a"], s["cpu.x"],
    s["cpu.y"], ret - 3 + 1))
end)
