-- Log the game-state bytes whenever any of them changes (with the frame), to map the flow.
--   emu.py ... --script tools/lua/state.lua
-- $E2 mode (0 attract, 1 title, 2 game, 3 debug menu), $E3 game submode, $E4/$E5 phase, $E6,
-- $1A05 scenario, $1A62 event id, $11CA/$11CB counters, $1A02 side (guess).
local mem = emu.memType.snesMemory
local addrs = {0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0x1A05, 0x1A62, 0x11CA, 0x11CB, 0x1A02, 0x1A64}
local last = ""
L.on_frame(function(n)
  local t = {}
  for _, a in ipairs(addrs) do t[#t + 1] = string.format("%X=%02X", a, emu.read(0x7E0000 + a, mem)) end
  local s = table.concat(t, " ")
  if s ~= last then L.log(string.format("f%d %s", n, s)); last = s end
end)
