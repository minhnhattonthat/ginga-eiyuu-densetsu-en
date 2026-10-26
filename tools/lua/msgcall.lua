-- Log each call of the message opener $07:97A0 (X = message id) with the JSL return address from the stack,
-- and each box setup $07:9E89 (A = $1185 mode, X = width in JP chars, Y = lines; $11A1 = box variant).
--   emu.py ... --script tools/lua/msgcall.lua
local mem = emu.memType.snesMemory
L.on_exec(0x0797A0, 0x0797A0, function()
  local s = emu.getState()
  local sp = s["cpu.sp"]
  -- $97A0 runs after the PHP at $979F, so sp+1 is P and the JSL return address starts at sp+2
  local ret = emu.read(sp + 2, mem) | (emu.read(sp + 3, mem) << 8) | (emu.read(sp + 4, mem) << 16)
  L.log(string.format("f%d msg %03X ret %06X var %d", L.frame, s["cpu.x"], ret, emu.read(0x11A1, mem)))
end)
L.on_exec(0x079E89, 0x079E89, function()
  local s = emu.getState()
  L.log(string.format("f%d box mode %02X w %d h %d var %d", L.frame, s["cpu.a"] & 0xFF, s["cpu.x"], s["cpu.y"],
    emu.read(0x11A1, mem)))
end)
