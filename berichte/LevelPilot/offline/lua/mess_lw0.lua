-- LW-0 (16.11.2026): Messung im Nachbau – Luftlinie gegen Weg über das Startwegnetz (Data/Wege.lua) und Rechenzeit der
-- Wegsuche. Keine Regression (nicht in run_offline.py), nur Zahlen für den Bericht.
-- Aufruf (wie test_seedwege): PACKDIR=<LevelPilot_Data> FOREVER=1 LVL=10 MAP=1411 PX=43.3 PY=68.5 lua5.1 mess_lw0.lua <LevelPilot> 0 Tauren WARRIOR Horde
-- Paare: zufällige Punkte des Startnetzes (fester Startwert), Luftlinie 300–2000 Yards, dieselbe Zone, höchstens 300 je Zone.
-- Nachbau mit echten Zonengrössen (ZONESIZE wie test_seedwege; im Spiel gelten die Werte des Clients).
ZONESIZE = { [1412] = { 5137.5, 3425.0 }, [1413] = { 10133.3, 6756.2 }, [1456] = { 1043.7, 695.8 } }
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
PRE_RUN = function(LP)
  local G, Geo = LP.Graph, LP.Geo
  local chunk = loadfile(arg[1] .. "/Data/Wege.lua")
  local T = {} chunk("LevelPilot", T)
  local wege = T.SeedWege
  local names = { [1412] = "Mulgore", [1413] = "Brachland", [1456] = "Donnerfels" }
  math.randomseed(20261116)
  local function q(list, p) if #list == 0 then return 0 end table.sort(list) return list[math.max(1, math.floor(#list * p + 0.5))] end
  local allMs = {}
  for _, map in ipairs({ 1412, 1413, 1456 }) do
    local pts = {}
    for _, seg in ipairs(wege[map] or {}) do
      for i = 2, #seg - 1, 2 do pts[#pts + 1] = { seg[i], seg[i + 1] } end
    end
    local facs, ms, nopath, tries, pairsN, over = {}, {}, 0, 0, 0, 0
    while pairsN < 300 and tries < 20000 do
      tries = tries + 1
      local a, b = pts[math.random(#pts)], pts[math.random(#pts)]
      local ai, an, aw = Geo:ToWorld(map, a[1], a[2])
      local bi, bn, bw = Geo:ToWorld(map, b[1], b[2])
      local d = Geo:Dist(an, aw, bn, bw)
      if d >= 300 and d <= 2000 then
        pairsN = pairsN + 1
        local t0 = os.clock()
        local p = G:PathKnown(ai, an, aw, map, bi, bn, bw, map)
        local dt = (os.clock() - t0) * 1000
        ms[#ms + 1] = dt allMs[#allMs + 1] = dt
        if p then
          local len = 0
          for i = 2, #p do len = len + Geo:Dist(p[i - 1][2], p[i - 1][3], p[i][2], p[i][3]) end
          local f = len / d
          facs[#facs + 1] = f
          if f > 1.5 then over = over + 1 end
        else
          nopath = nopath + 1
        end
      end
    end
    print(("%s (%d): Paare %d, mit Weg %d, ohne Weg %d · Umweg-Faktor Median %.2f · 90 %% %.2f · Anteil > 1,5 %d %% · Wegsuche ms Median %.2f · 90 %% %.2f · max %.2f")
      :format(names[map], map, pairsN, #facs, nopath, q(facs, 0.5), q(facs, 0.9), #facs > 0 and math.floor(over * 100 / #facs + 0.5) or 0,
        q(ms, 0.5), q(ms, 0.9), q(ms, 1.0)))
  end
  print(("ALLE: Wegsuche ms Median %.2f · 90 %% %.2f · max %.2f (%d Suchen)"):format(q(allMs, 0.5), q(allMs, 0.9), q(allMs, 1.0), #allMs))
  os.exit(0)
end
dofile(dir .. "/test40.lua")
