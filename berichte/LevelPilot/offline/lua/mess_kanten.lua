-- 3.12.51: Kantenzahl der Strassen je Grund (Antwort Prüfung 08:58). Aufruf wie test_strassen.lua.
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
PRE_RUN = function(LP)
  local G = LP.Graph
  LP.Geo.ZoneAt = function() return 1413 end
  for _, inst in ipairs({ 1, 0 }) do
    G:LoadStatic({}, nil)
    LP.Jobs.sync = true
    G:LoadRoads(inst)
    local st = G.roadStat[inst]
    print(("Kontinent %d: Stücke %d = Kanten %d + Ring %d + doppelt %d (%s), davon kürzer ersetzt %d"):format(inst, st.stuecke, st.kanten, st.gleich, st.doppelt,
      tostring(st.stuecke == st.kanten + st.gleich + st.doppelt), st.kuerzer or 0))
  end
  os.exit(0)
end
dofile(dir .. "/test40.lua")
