-- UC-W1 (3.12.35): Weg in Undercity vom Auktionshaus zu Bethor Iceshard (NPC 1498) über bekannte Wege.
-- Lädt die echten Wegdaten (uc_edges.lua) in das Wegnetz des Nachbaus und prüft:
--  1. Gegenprobe (der Fehler bis 3.12.34): die normale Suche nimmt Luftlinien quer über die Ebenen -> "Weg unbekannt"
--  2. Graph:PathKnown findet einen ganz bekannten Weg (Nav.Known) von drei Startpunkten aus
--  3. Navigation nimmt diesen Weg (kein "Weg unbekannt")
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/uc_edges.lua")
PRE_RUN = function(LP)
  local G, Geo, N = LP.Graph, LP.Geo, LP.Nav
  local fails = 0
  local function check(ok, text) print((ok and "OK   " or "[FEHLER] ") .. text) if not ok then fails = fails + 1 end end
  for _, e in ipairs(UC_EDGES) do
    local pts = {}
    for i = 1, #e - 1, 2 do local inst, n, w = Geo:ToWorld(1458, e[i], e[i + 1]) pts[#pts + 1] = { inst, n, w, 1458 } end
    G:AddPolyline(pts, "s")
  end
  local npc = LevelPilotData.N[1498]
  local s = npc and npc.s and npc.s[1]
  check(s and s[1] == 1458, "Bethor Iceshard (1498) im Datenpaket in Undercity: " .. tostring(s and (s[2] .. "," .. s[3])))
  local i2, n2, w2 = Geo:ToWorld(1458, s[2], s[3])
  local i1, n1, w1 = Geo:ToWorld(1458, 64.3, 35.9)
  local p = G:Path(i1, n1, w1, 1458, i2, n2, w2, 1458)
  if G.On and G.On() and G.INDOOR_ZONES and G.INDOOR_ZONES[1458] then
    -- ab W3D: in Unterstadt keine Luftlinien zwischen Knoten mehr -> schon die normale Suche ist bekannt
    check(p and N.Known(p), "W3D: normale Suche vom AH ohne Luftlinien quer über Ebenen (bekannt " .. tostring(p and N.Known(p)) .. ")")
  else
    check(p and not N.Known(p), "Gegenprobe: normale Suche vom AH nutzt Luftlinien (bekannt " .. tostring(p and N.Known(p)) .. ")")
  end
  for _, st in ipairs({ { 64.3, 35.9, "AH (64.3,35.9)" }, { 64.3, 52.5, "64.3,52.5" }, { 75.5, 33.5, "FEST 75.5,33.5" } }) do
    local a, b, c = Geo:ToWorld(1458, st[1], st[2])
    local q = G:PathKnown(a, b, c, 1458, i2, n2, w2, 1458)
    local virt = 0
    if q then for k = 2, #q do if q[k].via == nil or q[k].via == "v" then virt = virt + 1 end end end
    check(q and N.Known(q), ("bekannter Weg von %s: %s Punkte, Luftlinien %d (nur erstes/letztes Stück)"):format(st[3], q and #q or 0, virt))
  end
  -- Navigation: Ziel setzen und Weg berechnen lassen (Jobs laufen im Nachbau sofort)
  P.map, P.x, P.y = 1458, 64.3, 35.9
  N.target = { key = "TURNIN:405", inst = i2, n = n2, w = w2, map = 1458 }
  if N.Recalc then pcall(N.Recalc, N, true) end
  check(N.hasPath and not N.pathUnknown, "Navigation AH -> Bethor: Weg vorhanden " .. tostring(N.hasPath) .. ", „Weg unbekannt“ " .. tostring(N.pathUnknown))
  print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
  os.exit(fails == 0 and 0 or 1)
end
dofile(dir .. "/test40.lua")
