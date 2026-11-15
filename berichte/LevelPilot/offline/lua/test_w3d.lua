-- W3D (Entwurf, Konzept shared/wissen/analysen/levelpilot-wegfuehrung-3d.md Abschnitt 7): Ebenen im Wegnetz.
-- Läuft nur mit einer LevelPilot-Fassung, die Graph.LevelKey hat; sonst "== 1 FEHLER (W3D fehlt)".
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
PRE_RUN = function(LP)
  local G, Geo, N, R = LP.Graph, LP.Geo, LP.Nav, LP.Recorder
  local fails = 0
  local function check(ok, text) print((ok and "OK   " or "[FEHLER] ") .. text) if not ok then fails = fails + 1 end end
  if not G.LevelKey then print("[FEHLER] W3D fehlt") print("== 1 FEHLER") os.exit(1) end
  local Z = 1411                                  -- Durotar (Zone draussen); Ebenen kommen nur über die Schlüssel
  local function W(x, y) local i, n, w = Geo:ToWorld(Z, x, y) return i, n, w end
  local function pts(list, key)
    local out = {}
    for _, xy in ipairs(list) do local i, n, w = W(xy[1], xy[2]) out[#out + 1] = { i, n, w, Z, k = key } end
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
  print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
  os.exit(fails == 0 and 0 or 1)
end
dofile(dir .. "/test40.lua")
