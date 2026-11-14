-- Test: Speedrun-Modus (Umschalten, Klassenquests geschuetzt, Automatik, Anzeige)
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
LP.Planner.BUNDLE_CUT = 1   -- Test der Auslass-Mechanik: Buendeln ohne Sonderregel
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local function count(t) local n = 0 for _ in pairs(t) do n = n + 1 end return n end

LP.Planner:Replan()
check(not LP.Planner:IsSpeed() and count(LP.Planner.speedSkip) == 0, "Start im normalen Modus, nichts ausgelassen")
local normalSteps = #LP.Engine:Steps()

-- Umschalten per Knopf im Guide-Fenster
LP.UI:Toggle() LP.UI:Toggle()
local f = LevelPilotFrame
rawget(f.bMode, "_scripts").OnClick(f.bMode)
check(LP.Planner:IsSpeed(), "Knopf schaltet auf Speedrun")
LP.UI:Refresh()
check(tostring(rawget(f.bMode.label, "_text")):find("Speedrun"), "Knopf zeigt Speedrun an")
local skipped = count(LP.Planner.speedSkip)
check(skipped > 0, "Speedrun lässt Quests aus: " .. skipped)

-- Klassenquests nie auslassen
local bad = 0
for id in pairs(LP.Planner.speedSkip) do
    local q = LP.QuestDB:Get(id)
    if q and LP.Planner.IsClassQuest(q.classes) then bad = bad + 1 end
end
check(bad == 0, "keine Klassenquest ausgelassen")
local classSeen = 0
for _, id in ipairs(LP.QuestDB:AllIds()) do
    local q = LP.QuestDB:Get(id)
    if q and LP.Planner.IsClassQuest(q.classes) and LP.QuestDB:FitsPlayer(q) and (q.level or 0) <= P.level + 3 and (q.level or 0) >= P.level - 3 then
        classSeen = classSeen + 1
        check(LP.Planner:IsProtected(id) and not LP.Planner.speedSkip[id], "Klassenquest geschützt: " .. q.name)
    end
end
print("       Klassenquests im Levelbereich: " .. classSeen)

-- Automatik nimmt ausgelassene Quests nicht an
local anyId = next(LP.Planner.speedSkip)
check(anyId and not LP.Engine:WantQuest(anyId), "ausgelassene Quest wird nicht automatisch angenommen (" .. tostring(anyId) .. ": " .. tostring(LP.Planner.speedSkip[anyId]) .. ")")

-- Strenge
LP.db.speedLevel = 1 LP.Planner:Replan()
local loose = count(LP.Planner.speedSkip)
LP.db.speedLevel = 3 LP.Planner:Replan()
local strict = count(LP.Planner.speedSkip)
check(strict >= loose, "streng lässt mindestens so viel aus wie locker (" .. strict .. " / " .. loose .. ")")

-- Zurueck per Befehl
SlashCmdList["LEVELPILOT"]("normal")
check(not LP.Planner:IsSpeed() and count(LP.Planner.speedSkip) == 0, "/lp normal schaltet zurück, nichts mehr ausgelassen")
check(anyId and LP.Engine:WantQuest(anyId), "im normalen Modus wird die Quest wieder angenommen")
SlashCmdList["LEVELPILOT"]("speed")
check(LP.Planner:IsSpeed(), "/lp speed schaltet ein")
LP.Planner:Diagnose()
local diag = false
for _, m in ipairs(CHAT) do if m:find("Modus: Speedrun streng") then diag = true end end
check(diag, "Diagnose zeigt den Modus")

for _, m in ipairs(CHAT) do if (m:find("Fehler") and not m:find("Letzter Fehler: keiner")) or m:find("konnte nicht") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
