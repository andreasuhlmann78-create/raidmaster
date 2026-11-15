-- W3D (Entwurf, Konzept shared/wissen/analysen/levelpilot-wegfuehrung-3d.md Abschnitt 7): Ebenen im Wegnetz.
-- Läuft nur mit einer LevelPilot-Fassung, die Graph.LevelKey hat; sonst "== 1 FEHLER (W3D fehlt)".
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
PRE_RUN = function(LP)
  local G, Geo, N, R = LP.Graph, LP.Geo, LP.Nav, LP.Recorder
  local fails = 0
  local function check(ok, text) print((ok and "OK   " or "[FEHLER] ") .. text) if not ok then fails = fails + 1 end end
  if not (G.LevelKey and G.On) then print("[FEHLER] W3D fehlt") print("== 1 FEHLER") os.exit(1) end
  local Z = 1411                                  -- Durotar (Zone draussen); Ebenen kommen nur über die Schlüssel
  local function W(x, y) local i, n, w = Geo:ToWorld(Z, x, y) return i, n, w end
  -- 0) Schalter AUS (Standard): wie 3.12.35 – Ebenen werden NICHT getrennt, die Ebenen-Angabe wird aber gespeichert
  check(LP.W3D == false, "Schalter LP.W3D ist ab Werk aus (" .. tostring(LP.W3D) .. ")")
  do
    local i0, n0, w0 = W(20, 20)
    local x1 = G:AddNode(i0, n0, w0, Z, false, "i:A", "1411|d|A")
    local x2 = G:AddNode(i0, n0, w0, Z, false, "i:B", "1411|d|B")
    check(x1 == x2 and G.LvName(G:NodeById(x1)) == "1411|d|A" and type(G:NodeById(x1).lv) == "number" and G:NodeById(x1).k == nil,
      "aus: gleiche Stelle = ein Knoten wie bisher, Ebenen-Angabe gespeichert (" .. tostring(G.LvName(G:NodeById(x1))) .. ", Nr. " .. tostring(G:NodeById(x1).lv) .. ")")
  end
  do -- Neustart: Liste der Ebenen-Angaben bleibt, Nummern bleiben gleich, nichts doppelt
    local n0 = #LP.db.graph.lvs
    G:Init()
    check(G.LvId("1411|d|A") == 1 and #LP.db.graph.lvs == n0 and G.LvName(G:NodeById(1) or {}) ~= false,
      ("Neustart: Ebenen-Liste %d Einträge, \"1411|d|A\" = Nr. %s"):format(#LP.db.graph.lvs, tostring(G.LvId("1411|d|A"))))
    local saved = LP.db.graph.lvs
    LP.db.graph.lvs = "kaputt"
    G:Init()
    check(type(LP.db.graph.lvs) == "table" and #LP.db.graph.lvs == 0, "beschädigte Ebenen-Liste wird ersetzt statt Fehler")
    LP.db.graph.lvs = saved
    G:Init()
  end
  LP.W3D = true
  local function pts(list, key)
    local out = {}
    for _, xy in ipairs(list) do local i, n, w = W(xy[1], xy[2]) out[#out + 1] = { i, n, w, Z, k = key, lv = key and ("1411|d|" .. key) or nil } end
    return out
  end
  -- 1) SNAP legt Punkte verschiedener Ebenen nie zusammen
  local i, n, w = W(50, 50)
  local a1 = G:AddNode(i, n, w, Z, false, "i:A")
  local b1 = G:AddNode(i, n, w, Z, false, "i:B")
  local a2 = G:AddNode(i, n + 3, w, Z, false, "i:A")
  check(a1 and b1 and a1 ~= b1 and a2 == a1, ("SNAP nur in derselben Ebene: A %s, B %s, A+3 yd %s"):format(tostring(a1), tostring(b1), tostring(a2)))
  -- 2) zwei Ebenen mit gleichen 2D-Koordinaten, Tor nur am Ostende (Ebene A -> B)
  local line = {}
  for k = 0, 10 do line[#line + 1] = { 40 + k * 0.5, 30 } end
  G:AddPolyline(pts(line, "i:A"), "r")
  G:AddPolyline(pts(line, "i:B"), "r")
  local gate = pts({ { 45, 30 }, { 45.3, 30.2 } }, "i:A")
  gate[2].k = "i:B"
  G:AddPolyline(gate, "r")
  -- Start Westende auf A, Ziel Westende auf B (gleiche 2D-Stelle wie der Start!)
  local si, sn, sw = W(40, 30)
  local p = G:PathRaw(si, sn, sw, Z, si, sn, sw, Z, nil, false, "i:A", "i:B")
  local viaGate, maxX = false, 0
  if p then for k = 1, #p do local x = Geo:ToMap(Z, p[k][1], p[k][2], p[k][3]) if x and x > maxX then maxX = x end end end
  viaGate = maxX >= 44.9
  check(p and viaGate, ("Weg von Ebene A nach B führt über das Tor (östlichster Punkt %.1f, Tor bei 45)"):format(maxX))
  -- Gegenprobe: ohne Ebenen-Angabe (wie bisher) ist das Ziel am Start (Luftlinie 0)
  local q, kind = G:PathRaw(si, sn, sw, Z, si, sn, sw, Z)
  check(q and kind == "direct", "Gegenprobe ohne Ebenen: direkt (" .. tostring(kind) .. ")")
  -- 3) drinnen keine Luftlinie zwischen Knoten: zwei getrennte Stücke derselben Ebene ohne Verbindung
  local s1 = pts({ { 60, 60 }, { 60.5, 60 } }, "i:C")
  local s2 = pts({ { 68, 60 }, { 68.5, 60 } }, "i:C")
  G:AddPolyline(s1, "r") G:AddPolyline(s2, "r")
  local ai, an, aw = W(60, 60)
  local ti, tn, tw = W(68.5, 60)
  local gap = Geo:Dist(select(2, W(60.5, 60)), select(3, W(60.5, 60)), select(2, W(68, 60)), select(3, W(68, 60)))
  local r = G:PathRaw(ai, an, aw, Z, ti, tn, tw, Z, nil, true, "i:C", "i:C")
  check(gap > 40 and r == nil, ("drinnen: keine Luftlinie über die Lücke von %.0f yd (nur bekannte Wege: %s)"):format(gap, tostring(r ~= nil)))
  local r2 = G:PathRaw(ai, an, aw, Z, ti, tn, tw, Z, nil, false, "i:C", "i:C")
  local virtInside = false
  if r2 then for k = 3, #r2 - 1 do if r2[k].via == "v" then virtInside = true end end end
  check(not virtInside, "drinnen: normale Suche nutzt keine Luftlinie zwischen Knoten (" .. tostring(virtInside) .. ")")
  -- 4) draussen wie bisher: Luftlinie zwischen zwei Stücken ohne Schlüssel erlaubt
  local o1 = pts({ { 30, 70 }, { 30.5, 70 } }, nil)
  local o2 = pts({ { 31.5, 70 }, { 32, 70 } }, nil)
  G:AddPolyline(o1, "r") G:AddPolyline(o2, "r")
  local bi, bn, bw = W(30, 70)
  local ci, cn, cw = W(32, 70)
  local o = G:PathRaw(bi, bn, bw, Z, ci, cn, cw, Z)
  check(o ~= nil, "draussen: Weg mit Luftlinie wie bisher (" .. tostring(o ~= nil) .. ")")
  -- 5) Tor-Kante ist markiert
  local gates = 0
  for _, e in pairs(LP.db.graph.edges or {}) do if e.g then gates = gates + 1 end end
  check(gates == 1, "genau ein Tor markiert (" .. gates .. ")")
  -- 6) Aufzeichnung glättet einen Ebenenwechsel nicht weg
  local trail = {}
  for k = 0, 20 do trail[#trail + 1] = { 0, k * 2, 0, Z, k = (k < 10) and "i:A" or "i:B" } end
  local kp = R.KeyPoints(trail)
  local keepA, keepB = false, false
  for _, x in ipairs(kp) do if x == trail[10] then keepA = true end if x == trail[11] then keepB = true end end
  check(keepA and keepB, "Aufzeichnung: beide Punkte am Ebenenwechsel bleiben (" .. tostring(keepA) .. "/" .. tostring(keepB) .. ")")
  -- 7) Sturz-Tor nur nach unten (Einbahn)
  local fallPts = pts({ { 70, 20 }, { 70.5, 20 }, { 70.6, 20.1 }, { 71.1, 20.1 } }, "i:OBEN")
  fallPts[3].k, fallPts[4].k = "i:UNTEN", "i:UNTEN"
  fallPts[3].fall = true
  G:AddPolyline(fallPts, "r")
  local ui, un, uw = W(70, 20)
  local di, dn, dw = W(71.1, 20.1)
  local down = G:PathRaw(ui, un, uw, Z, di, dn, dw, Z, nil, true, "i:OBEN", "i:UNTEN")
  local up = G:PathRaw(di, dn, dw, Z, ui, un, uw, Z, nil, true, "i:UNTEN", "i:OBEN")
  check(down ~= nil and up == nil, "Sturz: hinunter Weg " .. tostring(down ~= nil) .. ", hinauf kein Weg " .. tostring(up == nil))
  -- 8) Aufzug: 2D still, 5 s, Ebene wechselt -> Aufzug-Tor mit Wartezeit (Unterstadt 8,4 s; hier Standard 15 s)
  local liftPts = pts({ { 75, 40 }, { 75.5, 40 }, { 75.5, 40 }, { 76, 40 } }, "i:L1")
  liftPts[1][5], liftPts[2][5], liftPts[3][5], liftPts[4][5] = 100, 103, 108, 111
  liftPts[3].k, liftPts[4].k = "i:L2", "i:L2"
  G:AddPolyline(liftPts, "r")
  local lifts, liftEdge = 0, nil
  for _, e in pairs(LP.db.graph.edges or {}) do if e.lift then lifts = lifts + 1 liftEdge = e end end
  local li, ln, lw = W(75, 40)
  local mi, mn, mw = W(76, 40)
  local lp, _, lcost = G:PathRaw(li, ln, lw, Z, mi, mn, mw, Z, nil, true, "i:L1", "i:L2")
  check(lifts == 1 and liftEdge.wait == 15 and lp and lcost and lcost >= 15 * 7,
    ("Aufzug erkannt %d, Wartezeit %s s, Kosten %.0f (>= 105)"):format(lifts, tostring(liftEdge and liftEdge.wait), lcost or -1))
  -- 9) Klartext je Tor
  local tLift = N.GateText({ lift = true }, { lv = "1458|d|Magieviertel" })
  local tFall = N.GateText({ ow = 1 }, { lv = "1458|d|Die Kanäle" })
  local tGate = N.GateText({ g = true }, { lv = "1458|d|" })
  check(tLift:find("Magieviertel", 1, true) and tFall:find("Die Kanäle", 1, true) and tGate ~= "",
    ("Texte: „%s“ · „%s“ · „%s“"):format(tLift, tFall, tGate))
  -- 10) Export: Ebenen-Angabe je Punkt in den Wegdaten
  local d = G:WegeData(nil)
  local withLv = 0
  for _, z in ipairs(d.zones) do for _, e in ipairs(z.edges) do if e.lv then withLv = withLv + 1 end end end
  check(withLv > 0, "Wegdaten enthalten die Ebenen-Angabe (" .. withLv .. " Wegstücke)")
  -- 11) sprachfrei (3.12.38, Supervisor 21:48): deDE- und enUS-Name derselben Unterzone -> derselbe Schlüssel
  if G.SubKey then
    local saved = LP.AreaNames
    -- a) echte Tabelle (Data/AreaNames.lua, wowf 1.60.1.70938): beide Unterstadt-Gebäude und Englisch -> ein Schlüssel
    local r1, r2, r3 = G.SubKey("Magieviertel"), G.SubKey("Das Magieviertel"), G.SubKey("Magic Quarter")
    check(saved ~= nil and r1 == "#1497:Magic Quarter" and r2 == r1 and r3 == r1,
      ("echte Tabelle: „Magieviertel“ %s · „Das Magieviertel“ %s · „Magic Quarter“ %s"):format(r1, r2, r3))
    local k1, k2 = G.SubKey("Die Abwasserkanäle"), G.SubKey("Sewers")
    check(k1 == k2 and k1:sub(1, 1) == "#", ("echte Tabelle: „Die Abwasserkanäle“ %s = „Sewers“ %s"):format(k1, k2))
    -- b) Testtabelle: Umschlüsseln gespeicherter Angaben und Anzeige
    LP.AreaNames = { ["9001:The Magic Quarter"] = { deDE = "Magieviertel", enUS = "The Magic Quarter", alt = { "Le quartier de la Magie" } } }
    G.ResetSubIndex()
    local kd, ke, ku = G.SubKey("Magieviertel"), G.SubKey("The Magic Quarter"), G.SubKey("Unbekannter Ort")
    local ka = G.SubKey("Le quartier de la Magie")
    check(kd == "#9001:The Magic Quarter" and ke == kd and ka == kd and ku == "Unbekannter Ort",
      ("sprachfrei: deDE %s, enUS %s, unbekannt bleibt „%s“"):format(kd, ke, ku))
    LP.db.graph.lvs[#LP.db.graph.lvs + 1] = "1458|d|The Magic Quarter"
    local nAlt = #LP.db.graph.lvs
    G:Init()
    check(LP.db.graph.lvs[nAlt] == "1458|d|#9001:The Magic Quarter" and G.LvId("1458|d|#9001:The Magic Quarter") == nAlt,
      "gespeicherte Angabe beim Laden umgeschlüsselt: " .. tostring(LP.db.graph.lvs[nAlt]))
    local loc = GetLocale()
    local tShow = N.GateText({ lift = true }, { lv = "1458|d|#9001:The Magic Quarter" })
    check(tShow:find(loc == "deDE" and "Magieviertel" or "The Magic Quarter", 1, true) ~= nil and not tShow:find("#9001:The Magic Quarter", 1, true),
      "Anzeige in der Spielsprache (" .. tostring(loc) .. "): „" .. tShow .. "“")
    LP.AreaNames = saved
    G.ResetSubIndex()
  else
    print("SKIP sprachfreier Schlüssel: erst ab 3.12.38 (diese Fassung hat Graph.SubKey nicht)")
  end
  LP.W3D = false
  print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
  os.exit(fails == 0 and 0 or 1)
end
dofile(dir .. "/test40.lua")
