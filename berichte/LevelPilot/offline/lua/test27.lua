-- Test: virtuelle Reise in Haeppchen (Coroutine), Stopp waehrend der Fahrt, Fehlerfreiheit (3.7.1)
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
function debugprofilestop() return os.clock() * 1000 end
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local realChar = LP.char
-- Zeitbudget je Bild absichtlich winzig: Planung wird oft unterbrochen
local yields = 0
local cy = coroutine.yield
coroutine.yield = function(...) yields = yields + 1 return cy(...) end
LP.Virtual:Start("start", { maxLevel = 8 })
local orig = LP.Virtual.Start
local frames = 0
while LP.Virtual.active and frames < 20000 do
    LP.sliceBudget = 0.5
    Advance(0.05, 0.05) frames = frames + 1
end
coroutine.yield = cy
local s = LP.Virtual.s
print(string.format("       %d Bilder, %d Unterbrechungen, Level %d, %d Schritte", frames, yields, s.level, s.steps))
check(not LP.Virtual.active and s.level >= 8, "Reise bis Level 8 in Häppchen fertig")
check(yields > 10, "Planung wurde unterbrochen (" .. yields .. "×)")
local errs = 0 for _, e in ipairs(s.problems) do if e.kind == "error" then errs = errs + 1 print("       " .. e.text) end end
check(errs == 0, "keine Fehler beim Unterbrechen")
check(LP.char == realChar, "danach echter Zustand")
-- Stopp waehrend der Fahrt (ohne Pause)
LP.Virtual:Start("start")
for _ = 1, 40 do Advance(0.05, 0.05) end
check(LP.Virtual.active, "läuft")
LP.Virtual:Stop()
Advance(0.2, 0.05)
check(not LP.Virtual.active and LP.char == realChar, "Stopp ohne Pause beendet sofort und stellt alles zurück")
-- Ereignisse des Spiels waehrend der Reise planen nicht dazwischen
LP.Virtual:Start("start")
for _ = 1, 10 do Advance(0.05, 0.05) FireEvent("QUEST_LOG_UPDATE") end
LP.Virtual:Stop() Advance(0.2, 0.05)
check(not LP.Virtual.active, "Spiel-Ereignisse stören nicht")
-- Reise ab hier: echtes Questlog wird übernommen
LOG[#LOG + 1] = { title = "Echt", id = 788, level = 5, complete = false, objs = { { "Eber: 2/10", false, type = "monster" } } }
FireAccepted(#LOG, 788) Advance(2)
LP.Virtual:Start("here")
for _ = 1, 10 do Advance(0.05, 0.05) end   -- seit 3.9.1: Questlog wird im ersten Takt der Reise gelesen
-- die Reise kann die Quest in diesen Takten schon erledigt haben (seit 3.11: gebuendelte Ziele)
local has788 = LP.Virtual.s.done[788]
for _, q in ipairs(LP.Virtual.s.log) do if q.id == 788 then has788 = true end end
check(has788, "Reise ab hier übernimmt das echte Questlog")
LP.Virtual:Stop() Advance(0.2, 0.05)
check(LP.Planner.inLog[788] ~= nil, "echtes Questlog danach wieder aktiv")
for _, m in ipairs(CHAT) do if m:find("attempt") or m:find("yield") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
