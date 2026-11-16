-- ROUTE-Q (3.12.72): Routen-Prüfung über die virtuelle Reise 1–60. R1 Annehmen zuerst, R2 Stufen-Gebiet + Startgebiet verlassen,
-- R3 Richtungswechsel > 120° je Stunde, R4 Sonder-Schritte vor nahem Questgeber. Zählt Verstösse, druckt je Regel bis 4 Beispiele.
-- Aufruf (oder ../mess_route_q.sh): Daten aus PACKDIR; FOREVER=1 oder FLAVOR=era; LVL=1 MAP=… PX PY; lua51 mess_route_q.lua <LevelPilot> 0 <Volk> <Klasse> <Fraktion>
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
local NEAR, SPECIAL_DETOUR = 150, 60
local SPECIAL = { BIND = true, HEARTH = true, FP = true, VENDOR = true, TRAIN = true, REPAIR = true }
local START_IDS = { Human = { 9, 34, 59 }, Dwarf = { 132 }, Gnome = { 132 }, NightElf = { 188, 256, 263 }, Orc = { 363, 638, 639, 640 },
  Troll = { 363, 638, 639, 640 }, Scourge = { 154, 155 }, Tauren = { 220, 221 } }
local ST = { Human = 1429, Dwarf = 1426, Gnome = 1426, NightElf = 1438, Orc = 1411, Troll = 1411, Scourge = 1420, Tauren = 1412 }

local rowCache = {}
local function AreaAt(map, inst, n, w)
  local d = LevelPilotData and LevelPilotData.ORTE
  if not (d and map and n) then return nil end
  local x, y = G:ToMap(map, inst, n, w)
  if not x or x < 0 or y < 0 or x >= 100 or y >= 100 then return nil end
  local era = G.EraFrame and G.EraFrame()
  local str = (era and d.era[map]) or d.forever[map]
  if not str then return nil end
  local key = (era and "e" or "f") .. map .. ":" .. math.floor(y)
  local r = rowCache[key]
  if not r then
    local j = 0
    for row in (str .. ";"):gmatch("([^;]*);") do
      if j == math.floor(y) then
        r = {}
        local xx = 0
        for part in row:gmatch("[^,]+") do
          local id, c = part:match("^(%d+)%*(%d+)$")
          id, c = tonumber(id or part), tonumber(c or 1)
          for _ = 1, c do r[xx] = id xx = xx + 1 end
        end
        break
      end
      j = j + 1
    end
    rowCache[key] = r or {}
  end
  return r and r[math.floor(x)]
end
local function AreaLevel(id)
  local a = LevelPilotData.ORTA and LevelPilotData.ORTA[id]
  return a and a[2] or 0
end
local areaMin
function AreaMin(id)
  if not areaMin then
    areaMin = {}
    for _, qid in ipairs(LP.QuestDB:AllIds()) do
      local q = LP.QuestDB:Get(qid)
      local p = q and q.level and q.level > 0 and q.starts and q.starts[1]
      if p and p[1] and LP.QuestDB:FitsPlayer(q) then
        local i, n, w = G:ToWorld(p[1], p[2], p[3])
        local a = i and AreaAt(p[1], i, n, w)
        if a and (not areaMin[a] or q.level < areaMin[a]) then areaMin[a] = q.level end
      end
    end
  end
  return areaMin[id]
end
local startSet = {}
for _, id in ipairs(START_IDS[race] or {}) do startSet[id] = true end
local function InStart(inst, n, w) return startSet[AreaAt(ST[race], inst, n, w) or -1] == true end

local c = { r1 = 0, r2 = 0, r2e = 0, r3 = 0, r4 = 0, steps = 0 }
local leaveLevel, leaveOpen
local lastKey, prevDir, lastPos
local ex = { r1 = {}, r2 = {}, r3 = {}, r4 = {} }
local function Ex(k, txt) if #ex[k] < 4 then ex[k][#ex[k] + 1] = txt end end
local function Name(st)
  local q = st.id and LP.QuestDB:Get(st.id)
  return tostring(st.t) .. " " .. tostring(st.q or (q and q.name) or st.npc or st.text or st.key):sub(1, 30)
end
local orig = LP.Engine.Current
LP.Engine.Current = function(self)
  local st = orig(self)
  local s = LP.Virtual.s
  if not (LP.Virtual.active and st and st.key ~= lastKey and st.n) then return st end
  lastKey = st.key
  c.steps = c.steps + 1
  local pi, pn, pw = G:Player()
  if not pi then return st end
  local d = (st.inst == pi) and G:Dist(pn, pw, st.n, st.w) or math.huge
  -- offene Questgeber <= 150 yd
  local open
  for _, t in ipairs(LP.Planner.lastTasks or {}) do
    if t.t == "ACCEPT" and t.inst == pi and t.n and not t.pathBlocked and t.key ~= st.key and G:Dist(pn, pw, t.n, t.w) <= NEAR then open = t break end
  end
  -- R1: Ziel > 150 yd, obwohl ein Questgeber <= 150 yd offen ist
  if d > NEAR and open and st.t ~= "ACCEPT" then
    c.r1 = c.r1 + 1
    Ex("r1", ("L%d %s (%.0f yd), offen: %s"):format(s.level, Name(st), d, tostring(open.q or open.id)))
  end
  -- R2: Gebiet, dessen Mindeststufe > Stufe + 2. Mindeststufe = kleinstes Questlevel der Quests, deren Questgeber in diesem Gebiet
  -- steht (für dieses Volk/diese Klasse). Die Erkundungsstufe der AreaTable ist KEINE Mindeststufe (Späherkuppe 15, Gol'Bolar 10 –
  -- dort beginnen Quests ab 7–10); sie wird nur zur Information mitgezählt (R2e).
  local aid = st.map and AreaAt(st.map, st.inst, st.n, st.w)
  -- nur Teilgebiete (Orte: Eltern ~= 0); das allgemeine Zonengebiet (z. B. 1 Dun Morogh) hat keine Mindeststufe
  local par = aid and LevelPilotData.ORTA[aid] and LevelPilotData.ORTA[aid][1] or 0
  local am = aid and par ~= 0 and AreaMin(aid)
  if am and am > s.level + 2 then
    c.r2 = c.r2 + 1
    Ex("r2", ("L%d %s Gebiet %d (Mindeststufe %d)"):format(s.level, Name(st), aid, am))
  end
  if aid and AreaLevel(aid) > s.level + 2 then c.r2e = c.r2e + 1 end
  -- Startgebiet verlassen: erster Schritt ausserhalb, ausser einer Annahme gleich am Weg (<= 150 yd, ORT-1 O5)
  if not leaveLevel and InStart(pi, pn, pw) and not InStart(st.inst, st.n, st.w) and not (st.t == "ACCEPT" and d <= NEAR) then
    local inside = 0
    for _, t in ipairs(LP.Planner.lastTasks or {}) do if t.n and InStart(t.inst, t.n, t.w) and not t.pathBlocked then inside = inside + 1 end end
    leaveLevel, leaveOpen = s.level, inside
  end
  -- R3: Richtungswechsel > 120° zwischen aufeinanderfolgenden Zielen (nur am selben Ort weitergehen, Abstand > 30 yd)
  if st.inst == pi and d > 30 then
    local dir = { (st.n - pn) / d, (st.w - pw) / d }
    if prevDir and lastPos and G:Dist(lastPos[1], lastPos[2], pn, pw) < 1 then
      -- Spieler steht noch am selben Ort: das Ziel wechselte, ohne dass er gelaufen ist
    elseif prevDir and dir[1] * prevDir[1] + dir[2] * prevDir[2] < -0.5 then
      c.r3 = c.r3 + 1
      Ex("r3", ("L%d %s"):format(s.level, Name(st)))
    end
    prevDir, lastPos = dir, { pn, pw }
  end
  -- R4: Sonder-Schritt, obwohl ein Questgeber <= 150 yd offen ist
  if SPECIAL[st.t] and open then
    c.r4 = c.r4 + 1
    Ex("r4", ("L%d %s, offen: %s"):format(s.level, Name(st), tostring(open.q or open.id)))
  end
  return st
end
local t0 = os.clock()
LP.Virtual:RunAll("start", tonumber(os.getenv("MAXL") or "60"))
local s = LP.Virtual.s
local h = (s.clock or 0) / 3600     -- Uhr der Reise (mit Ruhezeiten); die Spielzeit steht im Reisebericht
print(("%s %s: R1 %d · R2 %d (Erkundungsstufe: %d) · R3 %d (%.1f je h) · R4 %d · Startgebiet verlassen auf Stufe %s (drinnen offen %s) · %d Schritte · %.0f h · Stufe %d")
  :format(race, os.getenv("FLAVOR") == "era" and "Era" or "Forever", c.r1, c.r2, c.r2e, c.r3, h > 0 and c.r3 / h or 0, c.r4,
  tostring(leaveLevel), tostring(leaveOpen), c.steps, h, s.level))
for _, k in ipairs({ "r1", "r2", "r3", "r4" }) do for _, e in ipairs(ex[k]) do print("  " .. k:upper() .. " " .. e) end end
os.exit(0)
