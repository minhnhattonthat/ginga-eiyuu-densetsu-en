-- Scene list for tools/debug/warp.lua: name -> how to get there from a cold boot.
-- Facts (docs/re/debug.md): $E2 mode (0 attract, 1 title, 2 game), $E3 title menu / game submode,
-- step table $04:8CF4 (8 bytes per step: stage $11CB, chapter $11CC, E3, E4, E5, E6), $11CA = step.
--
-- Fields:
--   side   0 Yang (Alliance), 1 Reinhard (Empire)              (default 0)
--   scen   scenario picked on the select screen (0-2)          (default: the one holding `step`)
--   step   step index written to $11CA after the scenario is confirmed (default: the scenario's first)
--   e5     start the step at this phase (patches the step's E5 byte; 0 briefing .. 5 aftermath)
--   event  run event N (0-255) in place of the first event the step runs (or of event `swap`)
--   flags  story flags set (bit numbers, $1A9D bitfield) when the game starts
--   lose   1 = the battle outcome reads as a loss ($1A62 >= $1A64), 0 = a win
--   arrive what proves the scene: {msg = id} message opened, {ev = id} event started,
--          {ram = {[addr] = value, ...}} all bytes equal; next_msg = true: that only arms it, and the next
--          non-empty message opened is the arrival (events fade in for ~1000 frames before their first box)
--   settle frames to wait after arrival before the proof shot (default 90)
--   mash   press A every `mash` frames in game until arrival
--   title  true = stop in the title menus (no game start); menu = the title submode to stop at; load = pick LOAD
--   attract true = press nothing (attract mode)
--   answers ordered {msg, addr, value}: when that message opens, write the cursor; keys = route after arrival
local S = {}

-- Title menus (E3: 1 LOAD/NEW, 3 players, 4 character, 5 scenario, 7 confirm)
S.title          = { title = true, menu = 0, arrive = { ram = { [0xE2] = 1, [0xE3] = 0 } }, settle = 150 }
-- Attract mode (no input): the opening history, event 14 (msgs 027-030, 105-11F)
S.intro          = { attract = true, arrive = { msg = 0x28 }, settle = 300 }
S.intro_late     = { attract = true, arrive = { msg = 0x2C }, settle = 150 }
S.title_loadnew  = { title = true, menu = 1, arrive = { msg = 0x0A } }
S.title_players  = { title = true, menu = 3, arrive = { msg = 0x0D } }
S.title_char     = { title = true, menu = 4, arrive = { msg = 0x0E } }
S.title_scenario = { title = true, menu = 5, arrive = { msg = 0x0F } }
S.title_confirm  = { title = true, menu = 7, arrive = { msg = 0x0C } }

-- Every campaign step from its start, both sides. Steps with E4=1 are story interludes; step 11 is the ending.
-- Briefing events per stage ($00:DEB9): 15 18 1B 1E 20 21 22.
local first_ev = { [0] = 0x15, 0x18, 0x1B, 0x1E, 0x20, 0x21, 0x22 }
local stage_of = { [0] = 0, 0, 1, 1, 2, 2, 3, 4, 5, 6, 6, 6 }
local battle = { [0] = true, false, true, false, true, false, true, true, true, true, false, false }
for step = 0, 11 do
  for side = 0, 1 do
    local who = side == 0 and "yang" or "rein"
    local name = string.format("step%02d_%s", step, who)
    if battle[step] then
      S[name] = { side = side, step = step, arrive = { ev = first_ev[stage_of[step]], next_msg = true }, settle = 150 }
    elseif step < 11 then
      S[name] = { side = side, step = step, settle = 150,
                  arrive = { ram = { [0xE2] = 2, [0xE3] = 1, [0xE4] = 1, [0x11CA] = step }, next_msg = true } }
    else
      S[name] = { side = side, step = step, arrive = { ram = { [0xE2] = 2, [0xE3] = 2 } }, settle = 240 }
    end
  end
end

S.title_load = { title = true, menu = 2, load = true, arrive = { msg = 0x0B } }   -- DATA 1/2 select

-- Phases of the first battle (Astarte), Yang side, reached by pressing A through the earlier ones
S.astarte_assign  = { side = 0, step = 0, mash = 40, arrive = { msg = 0x10 } }      -- admiral placement
S.astarte_command = { side = 0, step = 0, mash = 40, arrive = { msg = 0x26 } }      -- "operation under way"
S.astarte_battle  = { side = 0, step = 0, mash = 40, arrive = { msg = 0x138 }, settle = 30 }

-- Command menu (first offered in step 2; Yang is not in command at Astarte). Cursor $1A82: 0 map/info,
-- 1 fleet orders, 2 SYS, 3 end turn. SYS cursor $1A83: 0 auto battle, 1 save, 2 battle animation.
-- `answers` = ordered {msg, addr, value}: when that message opens, write the cursor (mash then picks it).
local function cmd(t) t.side = t.side or 0; t.step = 2; t.mash = 40; return t end
S.cmd_menu    = cmd { arrive = { msg = 0x12 } }
S.cmd_info    = cmd { arrive = { msg = 0x12 }, answers = { { 0x12, 0x1A82, 0 } }, keys = "6 a", settle = 120 }
S.cmd_fleet   = cmd { arrive = { msg = 0x1B }, answers = { { 0x12, 0x1A82, 1 } } }
S.cmd_area    = cmd { arrive = { msg = 0x1C }, answers = { { 0x12, 0x1A82, 1 } } }
S.cmd_end     = cmd { arrive = { msg = 0x13 }, answers = { { 0x12, 0x1A82, 3 } } }
S.sys_auto    = cmd { arrive = { msg = 0x15 }, answers = { { 0x12, 0x1A82, 2 }, { 0x12, 0x1A83, 0 } } }
S.sys_save    = cmd { arrive = { msg = 0x16 }, answers = { { 0x12, 0x1A82, 2 }, { 0x12, 0x1A83, 1 } } }
S.sys_anim    = cmd { arrive = { msg = 0x18 }, answers = { { 0x12, 0x1A82, 2 }, { 0x12, 0x1A83, 2 } } }
S.cmd_menu_rein = cmd { side = 1, arrive = { msg = 0x12 } }

-- Battle results: phase E5=4 picks the result event from $00:F2AB by stage*2 + lose ($0B91), then phase 5
-- runs the stage's aftermath event (stages 0-3: 16 19 1C 1F).
local result_ev = { [0] = { 0x2F, 0x2E }, { 0x31, 0x30 }, { 0x33, 0x32 }, { 0x35, 0x34 }, { 0x37, 0x36 },
                    { 0x39, 0x38 }, { 0x25, 0x25 } }
local after_ev = { [0] = 0x16, 0x19, 0x1C, 0x1F }
for step = 0, 9 do
  if battle[step] then
    local st = stage_of[step]
    for side = 0, 1 do
      local who = side == 0 and "yang" or "rein"
      for lose = 0, 1 do
        S[string.format("step%02d_%s_result%d", step, who, lose)] = { side = side, step = step, e5 = 4, lose = lose,
          settle = 150, arrive = { ev = result_ev[st][lose + 1], next_msg = true } }
      end
      if after_ev[st] then
        S[string.format("step%02d_%s_after", step, who)] = { side = side, step = step, e5 = 5, settle = 150,
          arrive = { ev = after_ev[st], next_msg = true } }
      end
    end
  end
end
S.credits = S.step11_yang

-- Endings: step 10 runs event 23, which branches on story flags 10, 11, 14 (none set = the fourth ending).
for _, e in ipairs({ { "ending_f10", { 0x10 } }, { "ending_f11", { 0x11 } }, { "ending_f14", { 0x14 } },
                     { "ending_none", nil } }) do
  for side = 0, 1 do
    S[e[1] .. (side == 0 and "_yang" or "_rein")] = { side = side, step = 10, flags = e[2], settle = 150,
      arrive = { ev = 0x23, next_msg = true } }
  end
end

-- Story events no step scene starts with. 24 (ending part) runs in place of the first briefing (event 15);
-- the in-battle ones (12/13 a battle line, 26-2C battle scenes) need the battle screen, so they run in place
-- of Astarte's first battle event (2A). Not here: 14 (attract-mode screen: `intro_late`) and 2D (leftover debug
-- flag menu, draws nothing outside the debug menu; msgs 209-212 unused in play).
S.ev24 = { side = 0, step = 0, event = 0x24, settle = 150, arrive = { ev = 0x24, next_msg = true } }
for _, ev in ipairs({ 0x12, 0x13, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C }) do
  S[string.format("ev%02X", ev)] = { side = 0, step = 0, mash = 40, event = ev, swap = 0x2A, settle = 60,
    arrive = { ev = ev, next_msg = true } }
end

return S
