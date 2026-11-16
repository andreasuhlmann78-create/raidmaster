-- ST-4 (16.11.2026): Ladezeit und Speicher der Strassen je Kontinent im Nachbau (keine Regression). Aufruf wie test_strassen.lua.
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
PRE_RUN = function(LP)
  local G, Geo, J = LP.Graph, LP.Geo, LP.Jobs
  Geo.ZoneAt = function() return 1413 end
  for _, inst in ipairs({ 1, 0 }) do
    G:LoadStatic({}, nil)
    J.sync = false
    collectgarbage("collect")
    local mem0 = collectgarbage("count")
    local t0 = os.clock()
    G:LoadRoads(inst)
    local frames = 0
    J.maxSlice = 0
    while J.Running("strassen" .. inst) and frames < 100000 do J.Step() frames = frames + 1 end
    local ms = (os.clock() - t0) * 1000
    collectgarbage("collect")
    local kb = collectgarbage("count") - mem0
    local st = G.roadStat[inst]
    print(("Kontinent %d: %d Knoten, %d Kanten · %d Bilder, längste Portion %.2f ms, gesamt %.0f ms · Speicher +%.0f KB")
      :format(inst, st.knoten, st.kanten, frames, J.maxSlice, ms, kb))
  end
  os.exit(0)
end
dofile(dir .. "/test40.lua")
