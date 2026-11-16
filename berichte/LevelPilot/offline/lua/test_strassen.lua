-- ST-2/ST-4 (3.12.50): Strassennetz aus den Spieldateien (Data/Strassen.lua) im Wegnetz. Nachbau – die Zone eines
-- Weltpunkts liefert im Spiel C_Map.GetMapInfoAtPosition; hier ersetzt (alles = Zone 1413), weil der Nachbau keine echten
-- Kartengrenzen kennt (die Strassen liegen in echten Welt-Yards). Prüft:
--  1. Laden in Portionen (keine Portion über 16 ms), Zahlen gegen die Rohdaten unabhängig nachgezählt
--  2. Nur der verlangte Kontinent; zweimal laden = nichts doppelt
--  3. Weg entlang einer Strasse: Kantenart "road", Länge = Länge der Strasse (±1 %), bekannt (Nav.Known)
--  4. Nichts gespeichert (SavedVariables), Export enthält keine Strassen
--  5. Neuaufbau (LoadStatic) entfernt die Strassen; danach neu ladbar
--  6. Kosten Strasse = Länge × ROAD_COST; Luftlinie daneben teurer (1,45)
--  7. Speicher und Zeit (ST-4)
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
PRE_RUN = function(LP)
  local G, Geo, N, J = LP.Graph, LP.Geo, LP.Nav, LP.Jobs
  local fails = 0
  local function check(ok, text) print((ok and "OK   " or "[FEHLER] ") .. text) if not ok then fails = fails + 1 end end
  local R = _G.GoldSentinelStrassen
  check(type(R) == "table" and R.karten and R.karten[1] and R.karten[0], "Data/Strassen.lua geladen (Kalimdor und Östl. Königreiche)")
  Geo.ZoneAt = function() return 1413 end
  -- erwartete Zahlen unabhängig: Knoten = Enden der Linienzüge (verschiedene Punkte) + Zwischenknoten alle SEED_STEP Yards
  local k = R.karten[1]
  local ends, inner, yards = {}, 0, 0
  for _, line in ipairs(k.e) do
    ends[line[1]], ends[line[#line]] = true, true
    local acc = 0
    for j = 2, #line do
      local a, b = line[j - 1], line[j]
      local d = math.sqrt((k.p[2 * b - 1] - k.p[2 * a - 1]) ^ 2 + (k.p[2 * b] - k.p[2 * a]) ^ 2)
      acc, yards = acc + d, yards + d
      if j < #line and acc >= G.SEED_STEP then inner, acc = inner + 1, 0 end
    end
  end
  local nEnds = 0 for _ in pairs(ends) do nEnds = nEnds + 1 end
  -- beim Einloggen lädt der Nachbau den Kontinent seiner Fantasie-Welt (Durotar im Nachbau = Welt 0, keine echte Lage):
  -- vorher alles Feste entfernen, damit nur der Test lädt
  G:LoadStatic({}, nil)
  -- 1) in Portionen laden
  J.sync = false
  collectgarbage("collect")
  local mem0 = collectgarbage("count")
  local t0 = os.clock()
  local started = G:LoadRoads(1)
  local frames = 0
  J.maxSlice = 0
  while J.Running("strassen1") and frames < 100000 do J.Step() frames = frames + 1 end
  local ms = (os.clock() - t0) * 1000
  collectgarbage("collect")
  local memKB = collectgarbage("count") - mem0
  J.sync = true
  local st = G.roadStat[1] or {}
  check(started and st.fertig and frames > 1 and J.maxSlice < 16,
    ("in Portionen geladen: %d Bilder, längste Portion %.2f ms (< 16), gesamt %.0f ms, fertig %s"):format(frames, J.maxSlice, ms, tostring(st.fertig)))
  check(st.knoten + st.eigen == nEnds + inner,
    ("Knoten %d (+%d an vorhandenen) = Enden %d + Zwischenknoten %d"):format(st.knoten, st.eigen, nEnds, inner))
  check(math.abs(st.yards - yards) < 1, ("Länge %.0f yd = Rohdaten %.0f yd"):format(st.yards, yards))
  check(st.kanten >= #k.e and st.ohneZone == 0 and st.innen > 0,
    ("Kanten %d (Linienzüge %d), ohne Zone %d, innere Knoten %d"):format(st.kanten, #k.e, st.ohneZone, st.innen))
  print(("ST-4 Speicher nach dem Aufbau Kalimdor: +%.0f KB (Lua 5.1, Nachbau)"):format(memKB))
  -- 3.12.51 (Prüfung 08:58): Kanten-Bilanz je Grund – Stücke = Kanten + Ring (Anfang = Ende) + doppelt (Paar schon verbunden)
  check(st.stuecke == st.kanten + st.gleich + st.doppelt and st.stuecke == 654,
    ("Stücke %d = Kanten %d + Ring %d + doppelt %d (davon kürzer ersetzt %d)"):format(st.stuecke, st.kanten, st.gleich, st.doppelt, st.kuerzer or 0))
  -- 2) nur dieser Kontinent, doppelt laden = nichts
  check(G.roadStat[0] == nil, "Östliche Königreiche nicht geladen (Spieler auf Kalimdor)")
  check(G:LoadRoads(1) == false, "zweites Laden desselben Kontinents tut nichts")
  -- 3) Weg entlang der längsten Strasse: Start 3. Punkt, Ziel drittletzter Punkt
  local best, bl
  for _, line in ipairs(k.e) do
    local l = 0
    for j = 2, #line do l = l + math.sqrt((k.p[2 * line[j] - 1] - k.p[2 * line[j - 1] - 1]) ^ 2 + (k.p[2 * line[j]] - k.p[2 * line[j - 1]]) ^ 2) end
    if #line >= 8 and (not bl or l > bl) then best, bl = line, l end
  end
  local a, b = best[3], best[#best - 2]
  local an, aw, bn, bw = k.p[2 * a - 1], k.p[2 * a], k.p[2 * b - 1], k.p[2 * b]
  local roadLen = 0
  for j = 4, #best - 2 do
    roadLen = roadLen + math.sqrt((k.p[2 * best[j] - 1] - k.p[2 * best[j - 1] - 1]) ^ 2 + (k.p[2 * best[j]] - k.p[2 * best[j - 1]]) ^ 2)
  end
  local p = G:Path(1, an, aw, 1413, 1, bn, bw, 1413)
  local len, road = 0, 0
  if p then for i = 2, #p do
    local d = Geo:Dist(p[i - 1][2], p[i - 1][3], p[i][2], p[i][3])
    len = len + d
    if p[i].via == "road" then road = road + d end
  end end
  -- Anschluss an Start und Ziel über Luftlinie bis VIRT_RANGE (260 yd) wie beim Startnetz; dazwischen Strasse
  check(p and road >= 0.8 * len and len <= roadLen + 2 * N.ARRIVE,
    ("Weg auf der längsten Strasse (%.0f yd): Weg %.0f yd (nicht länger), davon Strasse %.0f yd (%d %%), Luftlinie Start-Ziel %.0f yd"):format(roadLen, len, road,
      len > 0 and math.floor(road * 100 / len + 0.5) or 0, Geo:Dist(an, aw, bn, bw)))
  -- 4) nichts gespeichert, Export ohne Strassen
  local saved = 0
  for _, e in pairs(LP.db.graph.edges or {}) do if e[3] == "road" then saved = saved + 1 end end
  local nsaved = 0
  for id in pairs(LP.db.graph.nodes or {}) do if id >= 20000000 then nsaved = nsaved + 1 end end
  check(saved == 0 and nsaved == 0, ("nichts gespeichert: Strassenkanten %d, Strassenknoten %d"):format(saved, nsaved))
  local d = G:WegeData(nil)
  local pts = 0
  for _, z in ipairs(d.zones or {}) do for _, e in ipairs(z.edges) do pts = pts + #e.p / 2 end end
  check(pts == 0, "Export enthält keine Strassen (" .. pts .. " Punkte)")
  -- 6) Kosten: Strasse = Länge × ROAD_COST, Luftlinie 1,45
  check(G.ROAD_COST == 1.0, "Kosten Strasse = Länge × " .. tostring(G.ROAD_COST) .. " (Luftlinie × 1,45 + Gelände)")
  -- 7) Text für das Protokoll
  local t = G.RoadText()
  check(t:find("^STRASSEN Kontinent 1 ") ~= nil, "Protokoll: " .. t)
  -- LW-1 (3.12.51): Umweg-Faktor der Zone messen (alle Strassenknoten haben hier Zone 1413), Median im erlaubten Bereich
  J.sync = true
  G.detour = {}
  G:MeasureDetour(1413)
  local dt = G.detour[1413] or {}
  check(dt.f and dt.f >= G.DETOUR_MIN and dt.f <= G.DETOUR_MAX and (dt.n or 0) >= G.DETOUR_MIN_PAIRS,
    ("Umweg Zone 1413 gemessen: Faktor %s aus %s Paaren (%s Versuche, %s Knoten)"):format(tostring(dt.f and ("%.2f"):format(dt.f)),
      tostring(dt.n), tostring(dt.versuche), tostring(dt.knoten)))
  print("  " .. G.DetourText())
  -- 5) Neuaufbau entfernt die Strassen, danach neu ladbar
  local chunk = loadfile(arg[1] .. "/Data/Wege.lua")
  local T = {} chunk("LevelPilot", T)
  G:LoadStatic({}, T.SeedWege)
  local left = 0
  for i = 1, 200 do if G:NodeById(25000000 + i) then left = left + 1 end end
  check(left == 0 and next(G.roadStat) == nil, ("nach Neuaufbau: Strassenknoten übrig %d, Stand leer %s"):format(left, tostring(next(G.roadStat) == nil)))
  check(G:LoadRoads(1) == true and G.roadStat[1].fertig, "danach neu geladen (fertig " .. tostring(G.roadStat[1] and G.roadStat[1].fertig) .. ")")
  -- Era/TBC: keine Strassen
  local savedGame = _G.GoldSentinelGame
  _G.GoldSentinelGame = { flavor = "era", IsForever = false }
  G:LoadStatic({}, nil)
  check(G:LoadRoads(1) == false, "Classic Era: keine Strassen (Daten aus dem Forever-Client)")
  _G.GoldSentinelGame = savedGame
  print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
  os.exit(fails == 0 and 0 or 1)
end
dofile(dir .. "/test40.lua")
