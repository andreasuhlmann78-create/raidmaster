-- ERA-1 3.12.71: virtuelle Reise bis Stufe 6 ab dem Startplatz; erster Schritt ausserhalb des Startgebiets, Rückkehr, Binden/Flugpunkt,
-- Erledigen mit offenen Questgebern. Aufruf: [ZONEN=1] FOREVER=1|FLAVOR=era LVL=1 MAP=1429 PX=48.2 PY=42.9 PACKDIR=<LevelPilot_Data> lua51 mess_era1_start.lua <LevelPilot> 0 Human WARRIOR Alliance
-- ERA-1 Messung: erster Schritt ausserhalb des Startgebiets, Rückkehr danach, Binden/Flugpunkt vor Stufe 6
-- echte Zonengrössen (HereBeDragons-Classic) für die 6 Startzonen, wenn ZONEN=1
if os.getenv("ZONEN") then
  ZONESIZE = { [1429] = { 3470.84, 2314.62 }, [1426] = { 4924.66, 3283.33 }, [1438] = { 5091.66, 3393.75 },
               [1411] = { 5287.5, 3525.0 }, [1420] = { 4518.75, 3012.5 }, [1412] = { 5137.5, 3425.0 } }
end
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
if os.getenv("FLAVOR") == "era" then
  function GetBuildInfo() return "1.15.7", "61000", "Jun 1 2025", 11507 end
  WOW_PROJECT_ID, WOW_PROJECT_CLASSIC = 2, 2
end
dofile(dir .. "/mock2.lua")
local LP = NS
local G = LP.Geo
local race = arg[3]
local ST = { Human = { 1429, 48.2, 42.9 }, Dwarf = { 1426, 29.9, 71.2 }, NightElf = { 1438, 58.6, 44.6 }, Orc = { 1411, 43.3, 68.5 }, Scourge = { 1420, 30.2, 71.7 }, Tauren = { 1412, 44.2, 76.1 } }
local st0 = ST[race]
local si, sn, sw = G:ToWorld(st0[1], G:FromData(st0[1], st0[2], st0[3]))
local inn, innD
for _, v in ipairs(LP.QuestDB:ServiceNPCs().inn) do
  local i, n, w = G:ToWorld(v.map, v.x, v.y)
  if i == si then local d = G:Dist(sn, sw, n, w) if not innD or d < innD then inn, innD, innName = { n, w }, d, v.name end end
end
local function Inside(i, n, w)
  if i ~= si or not n then return false end
  local d = G:Dist(sn, sw, n, w)
  return d < innD and d < G:Dist(n, w, inn[1], inn[2])
end
compOpen, compN = 0, 0
local lastKey, idx, firstOut, firstOutL, firstOutWhat, backAfter, bindEarly, fpEarly, maxD = nil, 0, nil, nil, nil, 0, 0, 0, 0
local orig = LP.Engine.Current
LP.Engine.Current = function(self)
  local st = orig(self)
  local s = LP.Virtual.s
  if LP.Virtual.active and st and st.key ~= lastKey and st.n then
    lastKey = st.key
    idx = idx + 1
    local inside = Inside(st.inst, st.n, st.w)
    if st.t == "COMPLETE" and inside and s.level < 6 then
      local open = {}
      for _, t in ipairs(LP.Planner.lastTasks or {}) do
        if t.t == "ACCEPT" and Inside(t.inst, t.n, t.w) and not t.pathBlocked then open[#open + 1] = tostring(t.q or t.id) end
      end
      if #open > 0 then compOpen = compOpen + 1 io.stderr:write("OFFEN " .. race .. " L" .. s.level .. " vor " .. tostring(st.q or st.id) .. ": " .. table.concat(open, ", ") .. "\n") end
      compN = compN + 1
    end
    if s.level < 6 then
      if st.t == "BIND" then bindEarly = bindEarly + 1 end
      if st.t == "FP" then fpEarly = fpEarly + 1 end
      if st.inst == si then maxD = math.max(maxD, G:Dist(sn, sw, st.n, st.w)) else maxD = math.huge end
    end
    if not inside and not firstOut then
      firstOut, firstOutL = idx, s.level
      local q = st.id and LP.QuestDB:Get(st.id)
      firstOutWhat = tostring(st.t) .. " " .. tostring(st.q or (q and q.name) or st.npc or st.key):sub(1, 30) .. ", Regel " .. tostring(LP.Planner.diag.startArea)
    elseif inside and firstOut and s.level < 6 then
      backAfter = backAfter + 1
      local q = st.id and LP.QuestDB:Get(st.id)
      io.stderr:write("ZURUECK " .. race .. " L" .. s.level .. " " .. tostring(st.t) .. " " .. tostring(st.q or (q and q.name)) .. "\n")
    end
  end
  return st
end
LP.Virtual:RunAll("start", 6)
print(string.format("%s: Gasthaus " .. tostring(innName) .. " %.0f yd · erster Schritt hinaus: Nr. %s auf Stufe %s (%s) · danach zurück ins Startgebiet (unter Stufe 6): %d · Binden unter 6: %d · Flugpunkt unter 6: %d · weitester Schritt unter 6: %s yd · Erledigen mit offenen Questgebern im Startgebiet: %d von %d",
  race, innD, tostring(firstOut), tostring(firstOutL), tostring(firstOutWhat), backAfter, bindEarly, fpEarly, maxD == math.huge and "anderer Kontinent" or string.format("%.0f", maxD), compOpen, compN))
os.exit(0)
