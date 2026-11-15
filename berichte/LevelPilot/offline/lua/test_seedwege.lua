-- Punkt 1/6 (3.12.37): Startwegnetz aus eigenen Koordinatenlisten (Data/Wege.lua) für Mulgore, Brachland, Donnerfels.
-- Nachbau mit echten Zonengrössen (ZONESIZE, Verdacht – im Spiel gelten die Werte des Clients). Prüft:
--  1. Laden im Forever-Client beim Einloggen: Karten, Knoten, Kanten; Rohdaten danach freigegeben; nichts gespeichert
--  2. Wege über die Startwege allein (Graph:PathKnown) in Brachland und Donnerfels
--  3. Classic Era / TBC (andere Karten): kein Startwegnetz
--  4. eigener Knoten an derselben Stelle wird genommen (keine Verdopplung), gespeicherte Kanten unverändert
--  5. Laden in Portionen: kein Stück über 16 ms
--  6. Export der Wegdaten enthält keine Startwege
ZONESIZE = { [1412] = { 5137.5, 3425.0 }, [1413] = { 10133.3, 6756.2 }, [1456] = { 1043.7, 695.8 } }
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
PRE_RUN = function(LP)
  local G, Geo, N, J = LP.Graph, LP.Geo, LP.Nav, LP.Jobs
  local fails = 0
  local function check(ok, text) print((ok and "OK   " or "[FEHLER] ") .. text) if not ok then fails = fails + 1 end end
  local function count(t) local n = 0 for _ in pairs(t or {}) do n = n + 1 end return n end
  -- 1) beim Einloggen geladen
  local st = G.seedWegeStat or {}
  check(st.fertig == true and st.karten == 3 and (st.knoten or 0) > 500 and (st.kanten or 0) > 800,
    ("geladen: fertig %s, Karten %s, Knoten %s, Kanten %s"):format(tostring(st.fertig), tostring(st.karten), tostring(st.knoten), tostring(st.kanten)))
  check(LP.SeedWege == nil, "Rohdaten nach dem Aufbau freigegeben (" .. tostring(LP.SeedWege == nil) .. ")")
  local seedSaved = 0
  for _, e in pairs(LP.db.graph.edges or {}) do if e[3] == "seed" then seedSaved = seedSaved + 1 end end
  check(seedSaved == 0 and count(LP.db.graph.nodes) == 0, ("nichts gespeichert: Startkanten in SavedVariables %d, Knoten %d"):format(seedSaved, count(LP.db.graph.nodes)))
  -- 2) Wege nur über Startwege
  local function known(name, m, x1, y1, x2, y2)
    local a, b, c = Geo:ToWorld(m, x1, y1)
    local d, e, f = Geo:ToWorld(m, x2, y2)
    local p = G:PathKnown(a, b, c, m, d, e, f, m)
    local seed, step, len = 0, 0, 0
    if p then for i = 2, #p do
      local d = Geo:Dist(p[i - 1][2], p[i - 1][3], p[i][2], p[i][3])
      len = len + d
      if p[i].via == "seed" then seed = seed + 1 if d > step then step = d end end
    end end
    -- die Punkte an den Kanten (alle SEED_STEP Yards ein Knoten) kommen lückenlos in den Weg: kein Schritt länger als das
    -- längste Stück der Daten (gerade Strecken bis ~200 yd nach der Vereinfachung, seed_bauen.py prüft die Abweichung)
    check(p and N.Known(p) and seed >= #p - 3 and step <= 210, ("%s: Weg über Startwege %s (%d Punkte, %d über Startwege, längster Schritt %.0f yd, Weg %.0f yd, Luftlinie %.0f yd)"):format(name,
      tostring(p and N.Known(p)), p and #p or 0, seed, step, len, Geo:Dist(b, c, e, f)))
  end
  known("Brachland West -> Ost", 1413, 34.22, 27.53, 65.8, 41.38)
  known("Donnerfels quer", 1456, 25.68, 16.67, 77.8, 28.17)
  known("Mulgore Nord -> Ost", 1412, 32.47, 14.36, 64.55, 63.65)
  -- Daten für die weiteren Teile neu laden (die Rohdaten wurden freigegeben)
  local chunk = loadfile(arg[1] .. "/Data/Wege.lua")
  local function reload() local T = {} chunk("LevelPilot", T) return T.SeedWege end
  -- 3) andere Spielversion: kein Startnetz
  local savedGame = _G.GoldSentinelGame
  _G.GoldSentinelGame = { flavor = "era", IsForever = false }
  G:LoadStatic({}, reload())
  check(G.seedWegeStat == nil, "Classic Era: kein Startwegnetz (" .. tostring(G.seedWegeStat == nil) .. ")")
  _G.GoldSentinelGame = { flavor = "tbc", IsForever = false }
  G:LoadStatic({}, reload())
  check(G.seedWegeStat == nil, "TBC Classic: kein Startwegnetz")
  _G.GoldSentinelGame = savedGame
  -- 4) eigener Knoten an derselben Stelle
  local i1, n1, w1 = Geo:ToWorld(1456, 50, 50)
  local i2, n2, w2 = Geo:ToWorld(1456, 52, 50)
  G:AddPolyline({ { i1, n1, w1, 1456 }, { i2, n2, w2, 1456 } }, "r")
  local edgesBefore = count(LP.db.graph.edges)
  G:LoadStatic({}, { [1456] = { { 3, 50.00, 50.00, 50.00, 53.00 } } })
  local s4 = G.seedWegeStat or {}
  check(s4.eigen == 1 and s4.knoten == 1 and s4.kanten == 1 and count(LP.db.graph.edges) == edgesBefore,
    ("eigener Knoten genommen %s, neue Startknoten %s, Kanten %s, gespeicherte Kanten %d -> %d"):format(tostring(s4.eigen),
      tostring(s4.knoten), tostring(s4.kanten), edgesBefore, count(LP.db.graph.edges)))
  -- 4b) Punkte an der Kante in richtiger Reihenfolge (beide Richtungen gleich lang wie der Weg selbst)
  G:LoadStatic({}, { [1413] = { { 2, 80.00, 80.00, 81.00, 80.00, 82.00, 81.00, 83.00, 80.00, 84.00, 80.00 } } })
  local soll = 0
  do
    local q = { { 80, 80 }, { 81, 80 }, { 82, 81 }, { 83, 80 }, { 84, 80 } }
    for i = 2, #q do
      local _, a1, a2 = Geo:ToWorld(1413, q[i - 1][1], q[i - 1][2])
      local _, b1, b2 = Geo:ToWorld(1413, q[i][1], q[i][2])
      soll = soll + Geo:Dist(a1, a2, b1, b2)
    end
  end
  local function lang(x1, y1, x2, y2)
    local a, b, c = Geo:ToWorld(1413, x1, y1)
    local d, e, f = Geo:ToWorld(1413, x2, y2)
    local p = G:PathKnown(a, b, c, 1413, d, e, f, 1413)
    local l = 0
    if p then for i = 2, #p do l = l + Geo:Dist(p[i - 1][2], p[i - 1][3], p[i][2], p[i][3]) end end
    return p and #p or 0, l
  end
  local nh, lh = lang(80, 80, 84, 80)
  local nr, lr = lang(84, 80, 80, 80)
  check(math.abs(lh - soll) < 1 and math.abs(lr - soll) < 1 and nh == 7 and nr == 7,     -- Start + 5 Punkte des Weges + Ziel
    ("Punkte an der Kante: hin %d Punkte %.1f yd, zurück %d Punkte %.1f yd, Weg selbst %.1f yd"):format(nh, lh, nr, lr, soll))
  -- 5) in Portionen
  J.sync = false
  J.maxSlice = 0
  G:LoadStatic({}, reload())
  local frames = 0
  while J.Running("seedwege") and frames < 100000 do J.Step() frames = frames + 1 end
  local s5 = G.seedWegeStat or {}
  check(s5.fertig == true and frames > 1 and J.maxSlice < 16,
    ("in Portionen: %d Bilder, längstes Stück %.2f ms (< 16), fertig %s"):format(frames, J.maxSlice, tostring(s5.fertig)))
  J.sync = true
  -- 6) Export ohne Startwege
  local d = G:WegeData(nil)
  local pts = 0
  for _, z in ipairs(d.zones or {}) do for _, e in ipairs(z.edges) do pts = pts + #e.p / 2 end end
  check(pts <= 4, "Export enthält nur eigene Wege (" .. pts .. " Punkte, eigener Test-Weg)")
  print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
  os.exit(fails == 0 and 0 or 1)
end
dofile(dir .. "/test40.lua")
