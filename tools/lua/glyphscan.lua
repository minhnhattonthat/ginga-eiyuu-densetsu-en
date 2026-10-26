-- English builds: log every glyph the VWF ($0F:8000) draws outside printable ASCII, with the text pointer
-- ($1113-$1115, already past the glyph) and the message id. Any hit is Japanese text the script doesn't cover.
--   regen.py --rom build/logh_en.sfc --lua tools/lua/glyphscan.lua      then: grep GLYPH work/qa/warp/*/log.txt
local mem = emu.memType.snesMemory
local seen = {}
L.on_exec(0x0F8000, 0x0F8000, function()
  local g = emu.read(0xBB, mem) | (emu.read(0xBC, mem) << 8)
  if g >= 0x20 and g <= 0x7E then return end
  local p = emu.read(0x1113, mem) | (emu.read(0x1114, mem) << 8) | (emu.read(0x1115, mem) << 16)
  local key = p * 1024 + g
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("GLYPH f%d g=%03X ptr=%06X msg=%03X", L.frame, g, p,
    emu.read(0x1111, mem) // 2 | (emu.read(0x1112, mem) << 7)))
end)
