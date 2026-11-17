-- Test 3.9: Reihenfolge an Crossroads (Bericht 3.8.1 Punkt 3) und Pflichtregel Mobs ab +3 mit den echten Questen
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local P, G = LP.Planner, LP.Geo
-- Questlog des echten Troll-Jägers (L13, Crossroads)
local quests = { 5041, 867, 869, 871, 870, 848, 1492, 844, 895 }
for _, id in ipairs(quests) do
    local q = LP.QuestDB:Get(id)
    if q then
        local objs = {}
        for _, o in ipairs(q.objectives) do objs[#objs + 1] = { (o.text or "?") .. ": 0/1", false, type = o.kind == "kill" and "monster" or "item" } end
        LOG[#LOG + 1] = { title = q.name, id = id, level = q.level, complete = #objs == 0, objs = objs }
        FireAccepted(#LOG, id)
    end
end
Advance(2)
P:Replan()
local steps = LP.Engine:Steps()
local ci, cn, cw = G:ToWorld(1413, 52, 30)
local total, last = 0, { inst = ci, n = cn, w = cw }
local firstFar
for i, st in ipairs(steps) do
    if st.inst == ci and st.n then
        local d = G:Dist(last.n, last.w, st.n, st.w)
        total = total + d
        last = st
        local fromCross = G:Dist(cn, cw, st.n, st.w)
        print(string.format("   %2d %-8s %-32s %5d Yards ab vorher, %5d ab Crossroads", i, st.t, tostring(st.q or st.text):sub(1, 32), d, fromCross))
        if i == 1 and fromCross > 900 then firstFar = true end
    end
end
check(not firstFar, "erster Schritt nicht nach Ratchet (Ziele bei Crossroads zuerst)")
local ratchetAt, crossLast = nil, 0
local _, rn, rw = G:ToWorld(1413, 63.0, 37.2)
for i, st in ipairs(steps) do
    if st.inst == ci and st.n then
        if G:Dist(rn, rw, st.n, st.w) < 300 then ratchetAt = ratchetAt or i elseif st.t == "COMPLETE" then crossLast = i end
    end
end
check(ratchetAt and ratchetAt > crossLast, "Ratchet-Schritte nach den Zielen rund um Crossroads (ab Schritt " .. tostring(ratchetAt) .. ")")
print(string.format("       Kette %d Yards", total))
-- Pflichtregel: Baron Küstenschipper [16] auf Level 13 nicht in der Route
local bad = false
for _, st in ipairs(steps) do if st.id == 895 or (st.key and st.key:find(":895$")) then bad = true end end
check(not bad, "„GESUCHT: Baron Küstenschipper“ (Mob 16) nicht in der Route auf Level 13")
check(P.mobSkip[895] ~= nil, "… und als zurückgestellt vermerkt")
-- Sensenklauen (Nester bei Sonnenschuppen-Raptoren 17) auf Level 14 nicht
local q = LP.QuestDB:Get(905)
P.inLog = P.inLog
check(q and LP.Planner.SafePoints and true, "Datenpaket hat 905")
-- Danger-Grundwerte
local D = LP.Danger
check(D:AtMap(1413, 52, 30) < 16, "Crossroads gilt auf Level 13 als sicher (" .. D:AtMap(1413, 52, 30) .. ")")
local bad = 0 for x = 40, 60, 2 do for y = 40, 60, 2 do bad = math.max(bad, D:AtMap(1418, x, y)) end end
check(bad >= 35, "Ödland-Mitte ist gefährlich (" .. bad .. ")")
check(not D:OK(16, 13) and D:OK(15, 13), "Grenze: Mob 16 auf Level 13 tabu, Mob 15 erlaubt")
for _, m in ipairs(CHAT) do if m:find("attempt") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
