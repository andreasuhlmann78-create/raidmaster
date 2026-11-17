-- EULA-Austausch Schritt 2 (3.12.88, Entscheid des Nutzers 17.11.2026 06:22): das Strassennetz aus den Spieldateien
-- (Data/Strassen.lua, Data/StrassenEra.lua, ST-2 bis ST-5) ist ENTFERNT. Vorher prüfte diese Datei das Laden der Strassen;
-- jetzt prüft sie, dass nichts davon mehr da ist und das Wegnetz trotzdem funktioniert:
--  1. Keine Strassen-Daten geladen (GoldSentinelStrassen / GoldSentinelStrassenEra fehlen)
--  2. Für WoW Forever, Classic Era und TBC Classic: RoadsAktiv false, LoadRoads lädt nichts, Diagnose sagt "entfernt"
--  3. Keine Strassen im Wegnetz geladen (Ladestand je Kontinent leer), keine Kante "road" gespeichert
--  4. Das Wegnetz aus gelaufenen Wegen (Startwegnetz) ist für WoW Forever weiter da und liefert einen bekannten Weg
-- Gegenprobe: mit 3.12.87 (Strassen noch drin) schlagen 1 und 2 fehl.
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
PRE_RUN = function(LP)
  local G = LP.Graph
  local fails = 0
  local function check(ok, text) print((ok and "OK   " or "[FEHLER] ") .. text) if not ok then fails = fails + 1 end end
  check(_G.GoldSentinelStrassen == nil and _G.GoldSentinelStrassenEra == nil,
    "keine Strassen-Daten aus den Spieldateien geladen (GoldSentinelStrassen/-Era fehlen)")
  local savedGame = _G.GoldSentinelGame
  for _, fl in ipairs({ { "forever", true, "WoW Forever" }, { "era", false, "Classic Era" }, { "tbc", false, "TBC Classic" } }) do
    _G.GoldSentinelGame = { flavor = fl[1], IsForever = fl[2] }
    local aktiv = G.RoadsAktiv()
    local l0, l1 = G:LoadRoads(0), G:LoadRoads(1)
    local text = tostring(G.RoadText())
    check(not aktiv and l0 == false and l1 == false and text:find("entfernt", 1, true) ~= nil,
      ("%s: keine Strassen (RoadsAktiv %s, laden %s/%s, Diagnose „%s“)"):format(fl[3], tostring(aktiv), tostring(l0), tostring(l1), text))
  end
  _G.GoldSentinelGame = savedGame
  -- Kanten liegen lokal in Graph.lua: der Ladestand je Kontinent (roadStat) ist leer, wenn nie Strassen geladen wurden
  local loaded = 0
  for _ in pairs(G.roadStat or {}) do loaded = loaded + 1 end
  local saved = 0
  for _, e in pairs(LP.db.graph and LP.db.graph.edges or {}) do if type(e) == "table" and e[3] == "road" then saved = saved + 1 end end
  check(loaded == 0 and saved == 0, ("keine Strassen im Wegnetz geladen (Kontinente %d) und nichts gespeichert (%d)"):format(loaded, saved))
  -- Startwegnetz (gelaufene Wege) für WoW Forever weiter da
  local seedOn = G.SeedWegeAktiv and G.SeedWegeAktiv()
  local st = G.seedWegeStat or {}
  check(seedOn and st.fertig == true and (st.knoten or 0) > 0 and (st.kanten or 0) > 0,
    ("Wegnetz aus gelaufenen Wegen vorhanden (Startwegnetz aktiv %s, fertig %s, %s Knoten, %s Kanten)"):format(tostring(seedOn),
      tostring(st.fertig), tostring(st.knoten), tostring(st.kanten)))
  print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
  os.exit(fails == 0 and 0 or 1)
end
dofile(dir .. "/test40.lua")
