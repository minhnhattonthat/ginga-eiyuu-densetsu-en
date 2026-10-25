-- Log each call of the message opener $07:97A0 (X = message id) with the JSL return address from the stack.
--   emu.py ... --script tools/lua/msgcall.lua
local mem = emu.memType.snesMemory
L.on_exec(0x0797A0, 0x0797A0, function()
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local ret = emu.read(sp + 1, mem) | (emu.read(sp + 2, mem) << 8) | (emu.read(sp + 3, mem) << 16)
  L.log(string.format("f%d msg %03X ret %06X", L.frame, s["cpu.x"], ret))
end)
