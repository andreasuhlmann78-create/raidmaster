-- Test: erst alle Quests in der Naehe annehmen, dann questen
-- Aufruf: PACKDIR=... LVL=.. MAP=.. PX=.. PY=.. lua51 test14.lua <Addon> 0 <Volk> <KLASSE> <Fraktion>
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local P_ = LP.Planner

local function analyse(tag)
    P_:Replan()
    local steps = LP.Engine:Steps()
    local inst, n, w = LP.Geo:Player()
    -- Annahmen in der Naehe laut Aufgabenliste
    local near = {}
    for _, t in ipairs(P_.lastTasks) do
        if t.t == "ACCEPT" and t.inst == inst and t.n and LP.Geo:Dist(n, w, t.n, t.w) <= P_.GATHER then near[t.id] = true end
    end
    local nNear = 0 for _ in pairs(near) do nNear = nNear + 1 end
    local firstC, lastNearAcc, accBefore = nil, 0, 0
    for i, s in ipairs(steps) do
        if s.t == "COMPLETE" and not firstC then firstC = i end
        if s.t == "ACCEPT" and near[s.id] then lastNearAcc = i end
        if s.t == "ACCEPT" and not firstC then accBefore = accBefore + 1 end
        if s.t == "TURNIN" and not firstC then accBefore = accBefore - 1 end   -- Abgabe schafft Platz
    end
    local seq = {}
    for i = 1, math.min(#steps, 12) do seq[#seq + 1] = steps[i].t:sub(1, 1) .. (steps[i].id or "") end
    print("       " .. tag .. ": " .. table.concat(seq, " "))
    local log = 0 for _ in pairs(P_.inLog) do log = log + 1 end
    local free = LP.API.MaxQuests() - log
    local expect = math.min(nNear, free)
    return nNear, firstC, lastNearAcc, accBefore, expect, steps
end

local nNear, firstC, lastAcc, accBefore, expect = analyse("Start")
check(nNear >= 2, "mehrere Quests in der Nähe annehmbar: " .. nNear)
check(not firstC or accBefore >= expect, "vor dem ersten Questziel angenommen: " .. accBefore .. " (erwartet ≥ " .. expect .. ")")
check(not firstC or lastAcc < firstC, "alle nahen Annahmen liegen vor dem ersten Questziel")

-- nur Quests, die vom Level her schon verfuegbar sind
local bad = 0
for _, s in ipairs(LP.Engine:Steps()) do
    if s.t == "ACCEPT" then
        local q = LP.QuestDB:Get(s.id)
        if q and (q.reqLevel or 0) > UnitLevel("player") then bad = bad + 1 end
    end
end
check(bad == 0, "keine Quest über der Mindeststufe geplant (" .. bad .. ")")

-- wenig Platz im Log: zwei Quests annehmen, Log auf 3 begrenzen -> vor dem Questen nur noch 1 Annahme
local taken = 0
for _, s in ipairs(LP.Engine:Steps()) do
    if s.t == "ACCEPT" and taken < 2 then
        local q = LP.QuestDB:Get(s.id)
        local objs = {}
        for i, o in ipairs(q and q.objectives or {}) do if o.kind ~= "rec" then objs[#objs + 1] = { "Ziel " .. i .. ": 0/1", false } end end
        LOG[#LOG + 1] = { title = s.q or ("Q" .. s.id), id = s.id, level = q and q.level or 1, complete = #objs == 0, objs = objs }
        FireAccepted(#LOG, s.id)
        taken = taken + 1
    end
end
LP.db.questLogMax = 3
local _, firstC2, _, accBefore2 = analyse("Log 3, 2 belegt")
check(LP.API.MaxQuests() == 3, "Questlog-Größe 3 eingestellt")
check(firstC2 ~= nil, "Questziele werden geplant")
check(accBefore2 <= 1, "bei 1 freien Platz höchstens 1 Annahme (abzüglich Abgaben) vor dem Questen: " .. accBefore2)
LP.db.questLogMax = 0
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
