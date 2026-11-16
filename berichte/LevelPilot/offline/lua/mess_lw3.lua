-- LW-3 (16.11.2026): Messung im Nachbau – wie oft entscheidet "Flug nach Zeit" anders als die alte Strecken-Regel?
-- Keine Regression, nur Zahlen für den Bericht. Aufruf wie mess_lw0.lua. Gebiet: Brachland, Mulgore, Donnerfels (echte
-- Zonengrössen wie test_seedwege), Flugmeister der Horde und neutrale aus dem Datenpaket (ServiceNPCs().flight) in diesen Zonen.
-- Je 2000 zufällige Paare Start/Ziel (Luftlinie ab 2000 yd, Flugmeister wie in TravelSteps: bis 2500 yd vom Start, 3000 vom Ziel).
ZONESIZE = { [1412] = { 5137.5, 3425.0 }, [1413] = { 10133.3, 6756.2 }, [1456] = { 1043.7, 695.8 } }
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
PRE_RUN = function(LP)
  local P, Geo = LP.Planner, LP.Geo
  local maps = { 1412, 1413, 1456 }
  local fps = {}
  for _, v in ipairs(LP.QuestDB:ServiceNPCs().flight or {}) do
    if v.map == 1412 or v.map == 1413 or v.map == 1456 then
      local i, n, w = Geo:ToWorld(v.map, v.x, v.y)
      if i then fps[#fps + 1] = { i = i, n = n, w = w, name = v.name } end
    end
  end
  print(("Flugmeister im Gebiet: %d"):format(#fps))
  math.randomseed(20261116)
  local function rnd()
    local m = maps[math.random(2)]                          -- Start/Ziel in Mulgore oder Brachland (Donnerfels ist klein)
    return Geo:ToWorld(m, 5 + math.random() * 90, 5 + math.random() * 90)
  end
  local function nearest(i, n, w, maxD)
    local best, bd
    for _, f in ipairs(fps) do
      if f.i == i then local d = Geo:Dist(n, w, f.n, f.w) if d <= maxD and (not bd or d < bd) then best, bd = f, d end end
    end
    return best, bd
  end
  for _, speed in ipairs({ { 7, "zu Fuss" }, { 11.2, "Reittier 60 %" }, { 14, "Reittier 100 %" } }) do
    local cand, oldFly, newFly, toFly, toWalk = 0, 0, 0, 0, 0
    local tries = 0
    math.randomseed(20261116)
    while cand < 2000 and tries < 200000 do
      tries = tries + 1
      local si, sn, sw = rnd()
      local ti, tn, tw = rnd()
      if si and ti and si == ti then
        local direct = Geo:Dist(sn, sw, tn, tw)
        if direct >= 2000 then
          local a, d1 = nearest(si, sn, sw, 2500)
          local b, d2 = nearest(ti, tn, tw, 3000)
          if a and b and a ~= b then
            cand = cand + 1
            local old = (d1 + d2) * 1.25 + 300 < direct
            local fs = P.FlightSecs(Geo:Dist(a.n, a.w, b.n, b.w))
            local new = P.FlyDecision(direct, d1, d2, fs, speed[1])
            if old then oldFly = oldFly + 1 end
            if new then newFly = newFly + 1 end
            if new and not old then toFly = toFly + 1 end
            if old and not new then toWalk = toWalk + 1 end
          end
        end
      end
    end
    print(("%s: Paare mit zwei Flugmeistern %d · alte Regel Flug %d (%d %%) · nach Zeit Flug %d (%d %%) · neu Flug statt laufen %d · neu laufen statt Flug %d")
      :format(speed[2], cand, oldFly, math.floor(oldFly * 100 / math.max(1, cand) + 0.5), newFly, math.floor(newFly * 100 / math.max(1, cand) + 0.5), toFly, toWalk))
  end
  os.exit(0)
end
dofile(dir .. "/test40.lua")
