-- Test: Dungeon-Quests (Fraktionssperren, Lauf-Schritt, Instanz-Ansicht, Einstellungen)
-- Aufruf: PACKDIR=... FOREVER=1 LVL=22 MAP=1436 PX=42 PY=70 lua51 test8.lua <Addon> 0 Human WARRIOR Alliance
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local horde = LP:PlayerFaction() == "Horde"
local QDB = LP.QuestDB

-- Fraktionssperren
check(QDB:DungeonAllowed(2437) == horde, "Flammenschlund (Orgrimmar) " .. (horde and "erlaubt" or "gesperrt"))
check(QDB:DungeonAllowed(717) == not horde, "Verlies (Sturmwind) " .. (horde and "gesperrt" or "erlaubt"))
check(QDB:DungeonAllowed(718), "Höhlen des Wehklagens für beide offen")
check(QDB:DungeonAllowed(721) and QDB:DungeonHostile(721) == horde, "Gnomeregan offen" .. (horde and ", aber Feindgebiet" or ""))
local d = QDB:Dungeon(717)
check(d and d.e[1][1] == 1453 and math.abs(d.e[1][2] - 52.4) < 0.2, "Verlies-Eingang aus Datenpaket (Forever-Karte): " .. (d and (d.e[1][2] .. ", " .. d.e[1][3]) or "?"))
check(QDB:QuestDungeon(168) == 1581 and QDB:QuestDungeon(5761) == 2437 and QDB:QuestDungeon(386) == 717, "Quest-Dungeon-Zuordnung (168, 5761, 386)")

-- Kandidaten: keine Quests gesperrter Dungeons
LP.Planner:BuildCandidates()
local forbidden = 0
local blocked = horde and 717 or 2437
for _, id in ipairs(QDB:AllIds()) do
    if QDB:QuestDungeon(id) == blocked and LP.Engine:WantQuest(id) then forbidden = forbidden + 1 end
end
check(forbidden == 0, "keine Quest für den gesperrten Dungeon wird angenommen (" .. forbidden .. ")")

-- Dungeon-Lauf planen
local q1, q2, area, inst
local q3, q4
if horde then q1, q2, q3, q4, area, inst = 5761, 5728, 5723, 5725, 2437, 389 else q1, q2, q3, q4, area, inst = 168, 167, 2040, 166, 1581, 36 end
for _, id in ipairs({ q1, q2, q3, q4 }) do
    local q = QDB:Get(id)
    LOG[#LOG + 1] = { title = q.name, id = id, level = q.level, complete = false, objs = { { "Ziel 1: 0/1", false } } }
    FireAccepted(#LOG, id)
end
NOW = NOW + 1
-- WoW Forever: 70 % weniger Monster-EP, aber ca. doppelte Quest-EP im Dungeon
check(math.abs(LP.Planner:DungeonXPFactor() - 0.36) < 0.001 and LP.Planner:DungeonQuestFactor() == 1.5, "Forever: Monster-EP 36 %, Dungeon-Quest-EP 150 % (Stand 3.12.2)")
-- ohne den Quest-Bonus lohnt sich der Lauf nicht
LP.db.dungeonQuestXP = 100
LP.Planner:Replan()
local none = true
for _, s in ipairs(LP.Engine:Steps()) do if s.t == "DUNGEON" then none = false end end
check(none and (LP.Planner.dungeonWorth[area] or ""):find("lohnt nicht"), "nur -70 % Monster-EP: kein Lauf, " .. tostring(LP.Planner.dungeonWorth[area]))
-- mit den echten Forever-Werten (Quest-EP x2) lohnt er sich
LP.db.dungeonQuestXP = 0
NOW = NOW + 1
LP.Planner:Replan()
local dg
for _, s in ipairs(LP.Engine:Steps()) do if s.t == "DUNGEON" then dg = s end end
print("       Forever-Werte: " .. tostring(LP.Planner.dungeonWorth[area]))
check(dg and dg.area == area and #dg.quests == 4, "Dungeon-Lauf geplant: " .. (dg and (dg.q .. " mit " .. #dg.quests .. " Quests") or "keiner"))
if dg then
    local txt = LP.UI:StepText(dg, true)
    check(txt:find("Dungeon") and txt:find("Gruppe"), "Anzeige: " .. txt:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("\n", " / "))
end

-- Zurueckstellen per Rechtsklick
LP.Engine:Skip(dg)
local still = false
for _, s in ipairs(LP.Engine:Steps()) do if s.t == "DUNGEON" then still = true end end
check(not still and LP.char.dungeonRun[area], "Zurückstellen entfernt den Lauf für 3 Stufen")
LP.char.dungeonRun[area] = nil

-- Instanz betreten
P.instance, P.instanceID = true, inst
FireEvent("PLAYER_ENTERING_WORLD")
Advance(3)
local st = LP.Engine:Steps()
check(st[1] and st[1].t == "DUNGEON" and st[1].inside, "Dungeon-Ansicht in der Instanz")
local ids = {}
for _, s in ipairs(st) do if s.t == "COMPLETE" then ids[s.id] = true end end
check(ids[q1] and ids[q2], "Questziele in der Instanz angezeigt")
LP.Engine:Skip(st[1])
check(LP.Engine:Steps()[1].key == "DGIN", "Dungeon-Kopf lässt sich nicht wegklicken")
for _, e in ipairs(LOG) do e.objs[1][2] = true e.objs[1][1] = "Ziel 1: 1/1" e.complete = true end
FireEvent("QUEST_LOG_UPDATE")
Advance(3)
LP.Planner:Replan()
check(LP.Engine:Steps()[2] and LP.Engine:Steps()[2].key == "DGDONE", "Alles erledigt erkannt")

-- Instanz verlassen
P.instance = false
FireEvent("PLAYER_ENTERING_WORLD")
Advance(3)
LP.Planner:Replan()
check(LP.char.dungeonRun[area] == P.level, "Lauf gemerkt (Level " .. tostring(LP.char.dungeonRun[area]) .. ")")
local turn = 0
local inst0, n0, w0 = LP.Geo:Player()
for _, t in ipairs(LP.Planner:CollectTasks(inst0, n0, w0, P.level)) do if t.t == "TURNIN" and (t.id == q1 or t.id == q2) then turn = turn + 1 end end
-- (Abgaben koennen in einer anderen Zone liegen: Aufgabenliste pruefen)
check(turn >= 1, "danach Abgaben als Aufgaben vorhanden (" .. turn .. ")")

-- Einstellung aus
LP.db.dungeons = false
LP.Planner:BuildCandidates()
check(not LP.Engine:WantQuest(horde and 5723 or 2040), "Dungeons aus: Dungeon-Quests werden nicht angenommen")
LP.db.dungeons = true

for _, m in ipairs(CHAT) do if m:find("Fehler") or m:find("konnte nicht") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
