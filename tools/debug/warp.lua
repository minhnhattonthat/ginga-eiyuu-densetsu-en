-- Warp from a cold boot to a scene in tools/debug/scenes.lua. Facts: docs/re/debug.md.
--   emu.py ROM --out DIR --script tools/debug/warp.lua --var "SCENE='step04_rein'" --frames 3000 --sheet
-- Globals (--var): SCENE (name), or ad hoc SIDE STEP E5 E6 EVENT LOSE WMASH MSG (arrive on message id) without SCENE;
--   WARP_STOP=true ends the run at the proof shot; WARP_STATE='abs/path.mss' saves a state there;
--   WARP_SETTLE=n overrides every scene's frames from arrival to the shot;
--   SCENES_FILE overrides the scene list path (default: ../debug/scenes.lua from the emulator dir, the cwd).
-- Writes <out>/warp.png and logs "WARP <scene> reached f<n>" (or "WARP <scene> NOT reached" at the last frame).
local mem, rom = emu.memType.snesMemory, emu.memType.snesPrgRom
local function rd(a) return emu.read(0x7E0000 + a, mem) end
local function wr(a, v) emu.write(0x7E0000 + a, v, mem) end

local scenes = dofile(SCENES_FILE or "../debug/scenes.lua")
if SCENE == "?list" then  -- for tools/debug/regen.py
  local names = {}
  for k in pairs(scenes) do names[#names + 1] = k end
  table.sort(names)
  for _, k in ipairs(names) do L.log("SCENE " .. k) end
  L.finish(0)
  return
end
local name = SCENE or "adhoc"
local sc = SCENE and scenes[SCENE]
if not sc then
  if SCENE then error("unknown SCENE " .. SCENE) end
  sc = { side = SIDE, step = STEP, e5 = E5, e6 = E6, event = EVENT, lose = LOSE, mash = WMASH, answers = ANSWERS,
         arrive = MSG and { msg = MSG } or { ram = { [0xE2] = 2 } } }
end
local side = sc.side or 0
local scen_first = { [0] = 0, 3, 5 }                       -- $07:979C: first step of each scenario
local scen = sc.scen or ((sc.step or 0) >= 5 and 2 or (sc.step or 0) >= 3 and 1 or 0)
local STEP_TBL, EV_TBL = 0x20CF4, 0x83F8                   -- file offsets: $04:8CF4 step table, $01:83F8 events

if sc.e5 then emu.write(STEP_TBL + 8 * sc.step + 4, sc.e5, rom) end
if sc.e6 then emu.write(STEP_TBL + 8 * sc.step + 5, sc.e6, rom) end

-- Title menus: answer each submode by writing its cursor, then pressing A (start on the title itself).
local cursor = { [1] = { 0x1A73, sc.load and 0 or 1 }, [3] = { 0x1A73, 0 }, [4] = { 0x1A73, side }, [5] = { 0x1A72, scen },
                 [7] = { 0x1A73, 0 } }
local wait, arrived_at = 0, nil
L.on_frame(function()
  local e2, e3 = rd(0xE2), rd(0xE3)
  if e2 > 1 then  -- in game: sc.mash presses A every sc.mash frames until arrival
    if sc.mash and not arrived_at and L.route_done() then L.press("a", 6); L.press("-", sc.mash - 6) end
    return
  end
  if sc.attract or (sc.title and e2 == 1 and e3 == sc.menu) then return end
  local c = e2 == 1 and cursor[e3]
  if c then wr(c[1], c[2]) end
  if wait > 0 then wait = wait - 1; return end
  if not L.route_done() then return end
  if e2 == 0 or e3 == 0 then L.press("start", 6) elseif c then L.press("a", 6) end
  L.press("-", 24); wait = 30
end)

-- Confirmed: force the side (1 player) and the step.
L.on_exec(0x079733, 0x079733, function() wr(0x1A04, side); wr(0x1A03, 0); wr(0x1A73, 0) end)
L.on_exec(0x079775, 0x079775, function() if sc.step then wr(0x11CA, sc.step) end end)
-- $00:A56E sets stage/chapter from its own table ($00:A58B), which stops at step 10: take them from the step table
-- at its exit (it runs at the scenario confirm and again at game init $00:D4C2).
L.on_exec(0x00A589, 0x00A589, function()
  if sc.step then wr(0x11CB, emu.read(STEP_TBL + 8 * sc.step, rom)); wr(0x11CC, emu.read(STEP_TBL + 8 * sc.step + 1, rom)) end
end)
-- Game init clears the flags ($00:D4DE) and sets its own; add ours just before it loads the step ($00:D538).
if sc.flags then
  L.on_exec(0x00D538, 0x00D538, function()
    for _, f in ipairs(sc.flags) do wr(0x1A9D + (f >> 3), rd(0x1A9D + (f >> 3)) | (1 << (f & 7))) end
  end)
end

-- Outcome: $00:F296 picks the result event from table $00:F2AB by stage*2 + $0B91 (1 = loss).
if sc.lose ~= nil then L.on_exec(0x00F296, 0x00F296, function() wr(0x0B91, sc.lose) end) end

-- Event runner $01:8000 (A = event id): swap in sc.event the first time, and watch for arrival.
local swapped, done, base, nans = false, false, false, 1
local function arrive(n)  -- with arrive.next_msg the condition only arms it; the next message opened arrives
  if arrived_at then return end
  if sc.arrive.next_msg and not base then base = true; L.log(string.format("WARP %s armed f%d", name, n)); return end
  arrived_at = n; L.log(string.format("WARP %s arrived f%d", name, n))
  for f, b in (sc.keys or ""):gmatch("(%d+)%s+(%S+)") do L.press(b, tonumber(f)) end
end
L.on_exec(0x018000, 0x018000, function()
  local a = emu.getState()["cpu.a"] & 0xFF
  if sc.event and not swapped and rd(0xE2) == 2 and (not sc.swap or sc.swap == a) then
    swapped = true
    emu.write(EV_TBL + 2 * a, emu.read(EV_TBL + 2 * sc.event, rom), rom)
    emu.write(EV_TBL + 2 * a + 1, emu.read(EV_TBL + 2 * sc.event + 1, rom), rom)
    L.log(string.format("WARP event %02X runs in place of %02X", sc.event, a))
    a = sc.event
  end
  L.log(string.format("f%d event %02X", L.frame, a))
  if sc.arrive.ev == a then arrive(L.frame) end
end)
L.on_exec(0x0797A0, 0x0797A0, function()
  local id = emu.getState()["cpu.x"] & 0xFFFF
  L.log(string.format("f%d msg %03X", L.frame, id))
  local ans = sc.answers and sc.answers[nans]
  if ans and ans[1] == id then wr(ans[2], ans[3]); nans = nans + 1 end
  if sc.arrive.msg == id or (base and id ~= 0) then arrive(L.frame) end
end)

L.on_frame(function(n)
  if sc.arrive.ram and not arrived_at and not base then
    local ok = true
    for a, v in pairs(sc.arrive.ram) do if rd(a) ~= v then ok = false end end
    if ok then arrive(n) end
  end
  if arrived_at and not done and n >= arrived_at + (WARP_SETTLE or sc.settle or 90) then
    done = true
    L.shot("warp.png")
    L.log(string.format("WARP %s reached f%d", name, n))
    if WARP_STATE then L.save_state(WARP_STATE, function() if WARP_STOP then L.finish(0) end end)
    elseif WARP_STOP then L.finish(0) end
  end
  if not done and FRAMES and n == FRAMES - 1 then L.log(string.format("WARP %s NOT reached", name)) end
end)
