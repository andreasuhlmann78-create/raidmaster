-- ROUTE-Q (3.12.87): Routen-Prüfung über die virtuelle Reise 1–60. R1 Annehmen zuerst, R2 Questlevel > Stufe + 2, Startgebiet verlassen,
-- R3W Weg-Ebene wie das Navi, R4 Sonder-Schritte, R6 Ort zu früh verlassen, O5 Questgeber am Weg verpasst, R7 Zonen-/Kontinentwechsel (Zahl).
-- Aufruf (oder ../mess_route_q.sh): Daten aus PACKDIR; FOREVER=1 oder FLAVOR=era; echte Kartengrenzen mit WORLDHOOK/SIMDIR; lua51 mess_route_q.lua <LevelPilot> 0 <Volk> <Klasse> <Fraktion>
-- 2026-11-17 EULA: Orte und Startgebiet ohne Spieldateien (Häufung der Questgeber, Gasthaus-Regel). Debug: DBG3/DBG5/DBG6/DBGC/DBGF/DBGW.
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
local ST = { Human = 1429, Dwarf = 1426, Gnome = 1426, NightElf = 1438, Orc = 1411, Troll = 1411, Scourge = 1420, Tauren = 1412 }
-- 2026-11-17 EULA (Nutzer 06:22): keine Gebiets-IDs aus den Spieldateien mehr, auch nicht in der Messung. Ort = Häufung der
-- Questgeber/Abgeber aus den Questdaten (eigene Umsetzung, unabhängig von der Addon-Fassung: Kette <= 100 yd, mind. 3 Punkte,
-- Rand +40 yd). Startgebiet = Punkte näher am Startplatz als am nächsten Gasthaus und innerhalb des Kreises Startplatz–Gasthaus.
local HUB_LINK, HUB_MIN, HUB_MARGIN = 100, 3, 40
local hubs
local function BuildHubs()
  hubs = {}
  local per, seen = {}, {}
  for _, qid in ipairs(LP.QuestDB:AllIds()) do
    local q = LP.QuestDB:Get(qid)
    if q then
      for _, list in ipairs({ q.starts or {}, q.ends or {} }) do
        for _, pt in ipairs(list) do
          if pt[1] and pt[2] and pt[3] and not pt.obj then
            local key = ("%d:%.1f:%.1f"):format(pt[1], pt[2], pt[3])
            if not seen[key] then
              seen[key] = true
              local i, n, w = G:ToWorld(pt[1], pt[2], pt[3])
              if i then per[pt[1]] = per[pt[1]] or {} table.insert(per[pt[1]], { i, n, w }) end
            end
          end
        end
      end
    end
  end
  for map, pts in pairs(per) do
    local out, used = {}, {}
    for a = 1, #pts do
      if not used[a] then
        used[a] = true
        local mem, k = { pts[a] }, 1
        while k <= #mem do
          local m = mem[k]
          for b = 1, #pts do
            if not used[b] and pts[b][1] == m[1] and (pts[b][2] - m[2]) ^ 2 + (pts[b][3] - m[3]) ^ 2 <= HUB_LINK * HUB_LINK then
              used[b] = true mem[#mem + 1] = pts[b]
            end
          end
          k = k + 1
        end
        if #mem >= HUB_MIN then
          local sn, sw = 0, 0
          for _, p in ipairs(mem) do sn, sw = sn + p[2], sw + p[3] end
          local cn, cw, r = sn / #mem, sw / #mem, 0
          for _, p in ipairs(mem) do r = math.max(r, math.sqrt((p[2] - cn) ^ 2 + (p[3] - cw) ^ 2)) end
          out[#out + 1] = { id = map * 1000 + #out + 1, inst = mem[1][1], n = cn, w = cw, r = r + HUB_MARGIN }
        end
      end
    end
    hubs[map] = out
  end
end
local function AreaAt(map, inst, n, w)
  if not (map and inst and n) then return nil end
  if not hubs then BuildHubs() end
  local best, bd
  for _, h in ipairs(hubs[map] or {}) do
    if h.inst == inst then
      local d = math.sqrt((n - h.n) ^ 2 + (w - h.w) ^ 2)
      if d <= h.r and (not bd or d < bd) then best, bd = h, d end
    end
  end
  return best and best.id or nil
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
local RS = { Human = { 1429, 48.2, 42.9 }, Dwarf = { 1426, 29.9, 71.2 }, Gnome = { 1426, 29.9, 71.2 }, NightElf = { 1438, 58.6, 44.6 },
  Orc = { 1411, 43.3, 68.5 }, Troll = { 1411, 43.3, 68.5 }, Scourge = { 1420, 30.2, 71.7 }, Tauren = { 1412, 44.2, 76.1 } }
local startA
local function InStart(inst, n, w)
  if startA == nil then
    startA = false
    local st = RS[race]
    local si, sn, sw = st and G:ToWorld(st[1], G:FromData(st[1], st[2], st[3]))
    if si then
      local best, bn, bw
      for _, v in ipairs(LP.QuestDB:ServiceNPCs().inn or {}) do
        local vi, vn, vw = G:ToWorld(v.map, v.x, v.y)
        if vi == si then local d = G:Dist(sn, sw, vn, vw) if not best or d < best then best, bn, bw = d, vn, vw end end
      end
      if best then startA = { si, sn, sw, best, bn, bw } end
    end
  end
  if not startA or inst ~= startA[1] or not n then return false end
  local d = G:Dist(n, w, startA[2], startA[3])
  return d < startA[4] and d < G:Dist(n, w, startA[5], startA[6])
end

local c = { r1 = 0, r2 = 0, r2e = 0, r3 = 0, r3w = 0, r3wn = 0, r3small = 0, r3back = 0, kept = 0, r3better = 0, r6 = 0, o5 = 0, zoneCh = 0, zoneCh30 = 0, contCh = 0, contCh30 = 0, r4 = 0, steps = 0 }
local leaveLevel, leaveOpen
local lastKey, prevDir, lastPos
local ex = { r1 = {}, r2 = {}, r3 = {}, r3w = {}, r4 = {}, r6 = {}, o5 = {}, r7 = {} }
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
  if os.getenv("DBGW") and s.level <= 30 and st.inst == pi and d > 1500 then
    local lt = LP.Planner.lastTravel
    local kn = 0 for _ in pairs(LP.char.taxiKnown or {}) do kn = kn + 1 end
    io.stderr:write(("DBGW L%d %s %.0f yd von %s nach %s · Flug bekannt %d · letzte Flugprüfung: %s\n"):format(s.level, Name(st), d, tostring(select(4, G:Player())), tostring(st.map), kn,
      lt and ("laufen %.0f s, Flug %.0f s, genommen %s, nach %s"):format(lt.walk or -1, lt.fly or -1, tostring(lt.took), tostring(lt.to)) or "keine"))
    LP.Planner.lastTravel = nil
  end
  if os.getenv("DBGF") and ({ FLY = true, FP = true, HEARTH = true, BIND = true, GOTO = true })[st.t] and s.level <= 30 then
    io.stderr:write(("DBGF L%d %s %s %.0f yd\n"):format(s.level, st.t, Name(st), d))
  end
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
  -- R2 (Supervisor 18:58): Questlevel des Schritts > Stufe + 2 (orange/rote Quest). Zur Information: Ort mit Erkundungsstufe > Stufe + 2.
  local q = st.id and LP.QuestDB:Get(st.id)
  local ql = q and q.level
  if ql and ql > 0 and ql > s.level + 2 then
    c.r2 = c.r2 + 1
    Ex("r2", ("L%d %s (Questlevel %d)"):format(s.level, Name(st), ql))
  end
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
  -- R3W (Weg-Ebene, wie mess_era1_weg): Weg zum Ziel jetzt und nach 30 yd entlang dieses Weges neu rechnen. Verstoss, wenn der
  -- Restweg um > 20 yd STEIGT oder der erste Wegpunkt danach entgegen der Laufrichtung liegt (Skalarprodukt < -0,5).
  if st.inst == pi and d > 60 and d < 3000 and LP.Graph and LP.Graph.Path then
    local function Calc(n0, w0)
      local ok, raw = pcall(LP.Graph.Path, LP.Graph, pi, n0, w0, st.map, st.inst, st.n, st.w, st.map)
      if not ok or not raw then return nil end
      local ok2, rp = pcall(LP.Terrain.Refine, LP.Terrain, raw)
      local p = (ok2 and rp) or raw
      -- wie das Navi: Abkürzung am Wegbeginn (ab 3.12.75), wenn vorhanden
      if LP.Graph.RemoveLoops then p = LP.Graph.RemoveLoops(p) end
      if LP.Graph.ShortcutStart then p = LP.Graph.ShortcutStart(p) end
      return p
    end
    local function Len(p, i0, n0, w0)
      local L = G:Dist(n0, w0, p[i0][2], p[i0][3])
      for i = i0 + 1, #p do L = L + G:Dist(p[i - 1][2], p[i - 1][3], p[i][2], p[i][3]) end
      return L
    end
    -- bis zu 4 Teilstrecken à 30 yd (120 yd) – die Umschaltung kam in Nordhain erst nach 60 yd
    local p0, qn, qw = Calc(pn, pw), pn, pw
    local bad, why = false, nil
    for _ = 1, tonumber(os.getenv("R3W_STEPS") or 4) do
      if not (p0 and #p0 >= 2) then break end
      local rem0 = Len(p0, 2, qn, qw)
      if rem0 < 40 then break end
      local left, i, hn, hw = 30, 2, 0, 0
      while left > 0 and p0[i] do
        local dd = G:Dist(qn, qw, p0[i][2], p0[i][3])
        if dd > 0 then hn, hw = (p0[i][2] - qn) / dd, (p0[i][3] - qw) / dd end
        if dd <= left then qn, qw, left, i = p0[i][2], p0[i][3], left - dd, i + 1
        else qn, qw, left = qn + (p0[i][2] - qn) * left / dd, qw + (p0[i][3] - qw) * left / dd, 0 end
      end
      local p1 = Calc(qn, qw)
      if not (p1 and #p1 >= 2) then break end
      local rem1 = Len(p1, 2, qn, qw)
      -- wie das Navi ab 3.12.75: alten Weg behalten, solange der neue nicht deutlich kürzer ist (N.KeepOld)
      local remOld = p0[i] and Len(p0, i, qn, qw) or 0
      if LP.Nav and LP.Nav.KeepOld and p0[i] and LP.Nav.KeepOld(remOld, rem1) then
        p1 = { { pi, qn, qw, st.map } }
        for j = i, #p0 do p1[#p1 + 1] = p0[j] end
        -- wie das Navi ab 3.12.76 (N.TrimKept): behaltenen Rest am Anfang abkürzen
        if LP.Nav.TrimKept and LP.Graph.ShortcutStart then p1 = LP.Graph.ShortcutStart(p1) end
        rem1 = Len(p1, 2, qn, qw)
        c.kept = c.kept + 1
      end
      local k = 2
      -- wie das Navi (CurrentWaypoint): erreichte (< 10 yd) und überschrittene Wegpunkte (N.Passed, wenn vorhanden) überspringen
      local passed = LP.Nav and LP.Nav.Passed
      while p1[k + 1] and (G:Dist(qn, qw, p1[k][2], p1[k][3]) < 10 or (passed and passed(p1, k, qn, qw))) do k = k + 1 end
      local dn, dw = p1[k][2] - qn, p1[k][3] - qw
      local dl = math.sqrt(dn * dn + dw * dw)
      -- Vergleichsrichtung: der alte Weg 30 yd voraus (nicht die letzte Laufrichtung) – sonst zählt ein abgekürzter Knick des alten
      -- Weges als "zurück" (Auf der Heimreise, Steinkrallen: alter Weg SW, dann O; neuer Pfeil O = Knick abgekürzt)
      do
        local ln, lw, need, jj = qn, qw, 30, i
        while need > 0 and p0[jj] do
          local dd = G:Dist(ln, lw, p0[jj][2], p0[jj][3])
          if dd <= need then ln, lw, need, jj = p0[jj][2], p0[jj][3], need - dd, jj + 1
          else ln, lw, need = ln + (p0[jj][2] - ln) * need / dd, lw + (p0[jj][3] - lw) * need / dd, 0 end
        end
        local an, aw = ln - qn, lw - qw
        local al = math.sqrt(an * an + aw * aw)
        if al > 1 then hn, hw = an / al, aw / al end
      end
      local back = dl > 1 and (dn / dl * hn + dw / dl * hw) < -0.5
      -- Zuwachs gegenüber dem alten Weg (30 yd gelaufen): > 50 yd = Umschaltung, 5–50 yd = kleine Änderung (Zahl)
      local grow = rem1 - (rem0 - 30)
      if grow > 5 and grow <= 50 then c.r3small = c.r3small + 1 end
      -- Pfeil zurück auf einen deutlich kürzeren Weg (mind. max(30 yd, 10 %) kürzer als der Rest des alten) ist berechtigt:
      -- der alte Weg war schlecht. Gezählt wird er getrennt (r3better), nicht als Verstoss.
      local better = back and grow <= 0 and remOld - rem1 >= math.max(30, remOld * 0.1)
      if better then c.r3better = c.r3better + 1 back = false end
      if grow > 50 or back then
        bad, why = true, ("Restweg %.0f -> %.0f yd nach 30 yd%s"):format(rem0, rem1, back and ", Pfeil zurück" or "")
        if os.getenv("DBG3") then
          local function P(p, n0, w0) local o = {} for ii = 1, math.min(#p, 8) do o[#o + 1] = ("%.0f/%.0f%s"):format(p[ii][2] - n0, p[ii][3] - w0, p[ii].via and ("(" .. tostring(p[ii].via) .. ")") or "") end return table.concat(o, " ") end
          io.stderr:write(("DBG3 %s Spieler %.1f/%.1f Ziel %s %.1f/%.1f k=%d\n  alt: %s\n  neu: %s\n"):format(Name(st), qn, qw, tostring(st.map), st.n, st.w, k, P(p0, qn, qw), P(p1, qn, qw)))
        end
        if back then c.r3back = c.r3back + 1 end
        break
      end
      p0 = p1
    end
    c.r3wn = c.r3wn + 1
    if bad then
      c.r3w = c.r3w + 1
      Ex("r3w", ("L%d %s %s"):format(s.level, Name(st), why))
    end
  end
  -- R6 (ORT-1 O2): Ort zu früh verlassen – Ziel in einem ANDEREN Ort mit Questgebern, obwohl im Ort des Spielers noch eine
  -- Annahme oder eine abgabebereite Quest offen ist (Gebiets-ID, Teilgebiete mit Eltern ~= 0)
  do
    local pm = select(4, G:Player())
    local ha = pm and AreaAt(pm, pi, pn, pw)
    local hp = ha and math.floor(ha / 1000) or 0
    local ta = st.map and AreaAt(st.map, st.inst, st.n, st.w)
    local tp = ta and math.floor(ta / 1000) or 0
    -- nur echtes Weggehen (Ziel > 150 yd) und nur Offenes im Ort bis 400 yd (P.HUB_RADIUS)
    if d > NEAR and ha and hp ~= 0 and ta and tp ~= 0 and ta ~= ha and AreaMin(ta) and AreaMin(ha) then
      for _, t in ipairs(LP.Planner.lastTasks or {}) do
        if (t.t == "ACCEPT" or t.t == "TURNIN") and t.n and not t.pathBlocked and t.inst == pi
           and G:Dist(pn, pw, t.n, t.w) <= 400 and t.map and AreaAt(t.map, t.inst, t.n, t.w) == ha
           -- liegt das Ziel auf dem Weg zu diesem offenen Punkt (<= 60 yd Umweg), ist es kein Verlassen des Ortes
           and G:Dist(pn, pw, st.n, st.w) + G:Dist(st.n, st.w, t.n, t.w) - G:Dist(pn, pw, t.n, t.w) > 60
           -- 2026-11-17: das Ziel liegt näher als der offene Punkt (nächstes zuerst, der offene Punkt folgt) – kein Verlassen
           -- (Fall "Kim'jael, fürwahr!" 186 yd im Nachbar-Teilgebiet vor "Verraten" 264 yd im Ort: diese Reihenfolge ist 78 yd kürzer)
           and G:Dist(pn, pw, st.n, st.w) > G:Dist(pn, pw, t.n, t.w) then
          c.r6 = c.r6 + 1
          Ex("r6", ("L%d %s (Ort %d -> %d), offen im Ort: %s %s"):format(s.level, Name(st), ha, ta, t.t, tostring(t.q or t.id)))
          if os.getenv("DBG6") then
            local R = LP.Planner.steps or {}
            local parts = {}
            for i = 1, math.min(#R, 8) do local r = R[i]; parts[#parts+1] = ("%d:%s %.0fyd%s"):format(i, Name(r), r.n and G:Dist(pn, pw, r.n, r.w) or -1, r.blocked and " blk" or "") end
            io.stderr:write(("DBG6 Ziel %s %.0f yd; offen %s key=%s %.0f yd, val=%s, Zeilen: %s\n"):format(Name(st), d, tostring(t.q or t.id), tostring(t.key),
              G:Dist(pn, pw, t.n, t.w), tostring(t.value), table.concat(parts, " | ")))
            for k, v in pairs(t) do if type(v) ~= "table" then io.stderr:write(("   t.%s=%s\n"):format(k, tostring(v))) end end
          end
          break
        end
      end
    end
  end
  -- O5: Questgeber am Weg verpasst – Ziel > 150 yd, und eine annehmbare Quest liegt mit <= 60 yd Umweg auf der Strecke dorthin
  -- nur Laufstrecken bis 1500 yd (P.ONWAY_RANGE); weitere Ziele gehen über Flug/Ruhestein/Reise
  if d > NEAR and d <= 1500 and st.inst == pi and not ({ HEARTH = true, FLY = true, GOTO = true })[st.t] then
    for _, t in ipairs(LP.Planner.lastTasks or {}) do
      if t.t == "ACCEPT" and t.n and t.inst == pi and not t.pathBlocked and t.key ~= st.key then
        local det = G:Dist(pn, pw, t.n, t.w) + G:Dist(t.n, t.w, st.n, st.w) - d
        -- nur echt "unterwegs": nicht beim Ziel selbst (dort ist annehmen nach dem Ziel genauso gut)
        if det <= 60 and G:Dist(t.n, t.w, st.n, st.w) > 60 then
          c.o5 = c.o5 + 1
          Ex("o5", ("L%d %s (%.0f yd), am Weg: %s (+%.0f yd)"):format(s.level, Name(st), d, tostring(t.q or t.id), det))
          if os.getenv("DBG5") then
            local R = LP.Planner.steps or {}
            local parts = {}
            for i = 1, math.min(#R, 8) do local r = R[i]; parts[#parts+1] = ("%d:%s %s %.0fyd"):format(i, r.t, Name(r), r.n and G:Dist(pn, pw, r.n, r.w) or -1) end
            io.stderr:write(("DBG5 O5 Spieler %.1f/%.1f, am Weg %s key=%s %.1f/%.1f (%.0f yd vom Spieler, %.0f yd vom Ziel) val=%s\n  Route: %s\n"):format(
              pn, pw, tostring(t.q or t.id), tostring(t.key), t.n, t.w, G:Dist(pn, pw, t.n, t.w), G:Dist(t.n, t.w, st.n, st.w), tostring(t.value), table.concat(parts, " | ")))
            local dg = LP.Planner.diag or {}
            io.stderr:write(("  diag onWay=%s near=%s explicit1=%s\n"):format(tostring(dg.onWayAccepts), tostring(dg.nearAccepts), tostring(R[1] and R[1].explicit)))
            io.stderr:write(("  geplant bei %.1f/%.1f, Planer-Erste: %s, jetzt-Erste: %s\n"):format(dg.pn or 0, dg.pw or 0, tostring(dg.first), tostring(R[1] and R[1].key)))
            local sv = {}; for i, r in ipairs(R) do sv[i] = r end
            local cnt = LP.Planner.OnWayAccepts(sv, LP.Planner.lastTasks, pi, pn, pw)
            io.stderr:write(("  OnWay jetzt: %d, erster: %s\n"):format(cnt, Name(sv[1])))
          end
          break
        end
      end
    end
  end
  -- R7 (OPT-ROUTE): Kontinent- und Zonenwechsel der Ziele (Zahl; Vergleich Factoruide Mensch 1–30: 40 Zonenwechsel)
  if st.map then
    local zone = LP.Planner.ZoneOf and LP.Planner.ZoneOf(st.map) or st.map
    if c.lastZone and zone ~= c.lastZone then
      c.zoneCh = c.zoneCh + 1
      if s.level < 30 then c.zoneCh30 = c.zoneCh30 + 1 end
    end
    if c.lastInst and st.inst ~= c.lastInst then
      c.contCh = c.contCh + 1
      if s.level < 30 then c.contCh30 = c.contCh30 + 1 Ex("r7", ("L%d Kontinentwechsel zu %s"):format(s.level, Name(st))) end
      if os.getenv("DBGC") and s.level < 30 then
        local P = LP.Planner
        local parts = {}
        for map, z in pairs(P.lastZones or {}) do parts[#parts+1] = ("%d:%s v%.1f n%d near%.0f"):format(map, z.inst == pi and "H" or "A", z.value, z.cnt, z.near or -1) end
        table.sort(parts)
        io.stderr:write(("DBGC L%d Wechsel zu %s (%s), Fokus %s why=%s\n  %s\n"):format(s.level, Name(st), tostring(st.t), tostring(P.focus), tostring(P.focusWhy), table.concat(parts, " | ")))
      end
    end
    c.lastZone, c.lastInst = zone, st.inst
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
print(("%s %s: R1 %d · R2 %d (entfällt: %d) · R3 %d (%.1f je h) · R3W %d von %d Wegen (davon Pfeil zurück %d; kleine Änderungen 5–50 yd: %d; alter Weg behalten: %d; Wechsel auf deutlich kürzeren Weg: %d) · R4 %d · R6 %d · O5 %d · R7 Zonenwechsel %d (bis 30: %d), Kontinentwechsel %d (bis 30: %d) · Startgebiet verlassen auf Stufe %s (drinnen offen %s) · %d Schritte · %.0f h · Stufe %d")
  :format(race, os.getenv("FLAVOR") == "era" and "Era" or "Forever", c.r1, c.r2, c.r2e, c.r3, h > 0 and c.r3 / h or 0, c.r3w, c.r3wn, c.r3back, c.r3small, c.kept, c.r3better, c.r4, c.r6, c.o5, c.zoneCh, c.zoneCh30, c.contCh, c.contCh30,
  tostring(leaveLevel), tostring(leaveOpen), c.steps, h, s.level))
for _, k in ipairs({ "r1", "r2", "r3", "r3w", "r4", "r6", "o5", "r7" }) do for _, e in ipairs(ex[k]) do print("  " .. k:upper() .. " " .. e) end end
os.exit(0)
