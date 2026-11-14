-- Szenario-Tests LevelPilot 2.x
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(cond, msg)
    if cond then print("OK     " .. msg) else fails = fails + 1 print("FEHLER " .. msg) end
end
local function errorsInChat()
    local errs = {}
    for _, m in ipairs(CHAT) do if m:find("Fehler") or m:find("konnte nicht") then errs[#errs + 1] = m end end
    return errs
end
local function stepTypes()
    local out = {}
    for _, s in ipairs(LP.Engine:Steps()) do out[#out + 1] = s.t .. (s.id and (":" .. s.id) or "") end
    return table.concat(out, " ")
end
local function hasStep(t, id)
    for _, s in ipairs(LP.Engine:Steps()) do if s.t == t and s.id == id then return true end end
    return false
end
local withQuestie = (arg[2] or "1") == "1"

print("== Start (Questie " .. (withQuestie and "an" or "aus") .. ", " .. (FOREVER and "Forever-Client" or "Classic-Client") .. ")")
local e0 = errorsInChat()
check(#e0 == 0, "keine Fehler beim Start " .. table.concat(e0, " | "))
check(#LP.modules == 31 and LP.API ~= nil and LP.Seed ~= nil, "31 Module geladen (" .. #LP.modules .. ")")
check(LP.QuestDB.questie == withQuestie, "Questie-Erkennung: " .. LP.QuestDB.questieInfo)

LP.Planner:Replan()
print("       Plan: " .. stepTypes())

if withQuestie then
    -- 1) Planung
    check(hasStep("ACCEPT", 783), "Quest 'A Threat Within' wird angeboten")
    check(hasStep("ACCEPT", 5261), "Quest 'Eagan Peltskinner' wird angeboten")
    check(not hasStep("ACCEPT", 7), "Folgequest 7 noch gesperrt (Vorquest fehlt)")
    check(not hasStep("ACCEPT", 4641), "Horde-Quest wird nicht angeboten")
    check(not hasStep("ACCEPT", 9000), "Quest Level 30 wird nicht angeboten")
    check(not hasStep("ACCEPT", 9002), "Magier-Quest nicht fuer Krieger")
    local first = LP.Engine:Current()
    check(first and first.map == 1429 and first.x, "erster Schritt hat Ort in Elwynn")

    -- 2) Annehmen ueber die Automatik
    NPCNAME = "Deputy Willem"
    CUR_QUEST = 783
    FireEvent("QUEST_DETAIL")
    check(ACCEPTED[#ACCEPTED] == 783, "Quest automatisch angenommen")
    table.insert(LOG, { title = "A Threat Within", id = 783, level = 1, complete = true, objs = {} })
    FireAccepted(#LOG, 783)
    Advance(3)
    check(hasStep("TURNIN", 783), "nach Annehmen: Abgabe geplant")
    check(LP.db.qdb[783] and LP.db.qdb[783].s, "Questgeber aufgezeichnet")

    -- 3) Abgeben -> Folgequest frei
    NPCNAME = "Marshal McBride"
    FireEvent("QUEST_COMPLETE")
    table.remove(LOG, 1)
    FLAGGED[783] = true
    FireEvent("QUEST_TURNED_IN", 783)
    Advance(3)
    check(hasStep("ACCEPT", 7), "Folgequest 7 nach Abgabe frei: " .. stepTypes())
    check(LP.db.qdb[783].e, "Abgabe-NPC aufgezeichnet")

    -- 4) Ziel-Fortschritt -> Hotspot
    table.insert(LOG, { title = "Kobold Camp Cleanup", id = 7, level = 2, complete = false, objs = { { "Koboldungeziefer: 0/8", false } } })
    FireAccepted(#LOG, 7)
    Advance(3)
    check(hasStep("COMPLETE", 7), "offenes Ziel geplant")
    P.x, P.y = 47.2, 34.6
    LOG[#LOG].objs[1][1] = "Koboldungeziefer: 3/8"
    FireEvent("QUEST_LOG_UPDATE")
    Advance(3)
    local o = LP.db.qdb[7] and LP.db.qdb[7].o
    check(o and o[1] and #o[1] >= 1, "Zielort aus Fortschritt aufgezeichnet")

    -- 5) Ignorieren
    LP.Engine:Skip({ t = "COMPLETE", id = 7, q = "Kobold Camp Cleanup" })
    check(not hasStep("COMPLETE", 7), "uebersprungene Quest nicht mehr geplant")
    LP.Engine:ResetIgnored()
    check(hasStep("COMPLETE", 7), "nach Zuruecksetzen wieder geplant")
else
    local s = LP.Engine:Current()
    check(s and s.key == "NODATA", "ohne Daten: Hinweis statt Route")
    -- Quest annehmen -> wird gelernt
    NPCNAME = "Fremder NPC"
    CUR_QUEST = 91741
    FireEvent("QUEST_DETAIL")
    check(ACCEPTED[#ACCEPTED] == 91741, "unbekannte (Forever-)Quest wird angenommen")
    table.insert(LOG, { title = "Neue Forever-Quest", id = 91741, level = 2, complete = false, objs = { { "Ding: 0/5", false } } })
    FireAccepted(#LOG, 91741)
    Advance(3)
    check(LP.db.qdb[91741] and LP.db.qdb[91741].n == "Neue Forever-Quest", "Quest aufgezeichnet")
end

-- 6) Weg-Aufzeichnung
local before = LP.Graph:Stats().nodes
P.map, P.x, P.y = 1429, 40.0, 60.0
for i = 1, 30 do
    P.x = 40.0 + i * 0.8         -- 16 Yards pro Schritt
    P.y = 60.0 + (i % 5) * 0.3
    Advance(1)
end
Advance(8)
local after = LP.Graph:Stats()
check(after.nodes > before, "Weg aufgezeichnet: " .. before .. " -> " .. after.nodes .. " Punkte, " .. after.edges .. " Stuecke")

-- Sturz: Tod direkt nach dem Weg verwirft das Stueck
local n1 = LP.Graph:Stats().nodes
for i = 1, 5 do P.y = 70 + i Advance(1) end
P.dead = true
FireEvent("PLAYER_DEAD")
Advance(2)
P.dead = false
check(LP.Graph:Stats().nodes == n1, "Wegstueck vor dem Tod verworfen")

-- 7) Wegfindung ueber einen Zonenuebergang
P.map, P.x, P.y = 1429, 30.0, 70.0
local pi, pn, pw, pmap = LP.Geo:Player()
local ti, tn, tw = LP.Geo:ToWorld(1436, 56, 31)
local path, kind = LP.Graph:Path(pi, pn, pw, pmap, ti, tn, tw, 1436)
local usesGateway = false
for _, p in ipairs(path or {}) do if p.gw then usesGateway = true end end
check(path and kind == "graph" and usesGateway, "Weg nach Westfall fuehrt ueber Zonenuebergang (" .. tostring(kind) .. ", " .. (path and #path or 0) .. " Punkte)")
-- innerhalb derselben Zone darf es Luftlinie sein
local ti2, tn2, tw2 = LP.Geo:ToWorld(1429, 35, 72)
local path2, kind2 = LP.Graph:Path(pi, pn, pw, pmap, ti2, tn2, tw2, 1429)
check(path2 and #path2 >= 2, "Weg innerhalb der Zone gefunden (" .. tostring(kind2) .. ")")

-- 8) Austausch: senden und empfangen
P.group = true
SENT = {}
LP.Comm:Hello("PARTY")
Advance(2)
if GoldSentinelSync then for _ = 1, 5 do GoldSentinelSync.Pump(true) end end
local hello = false
for _, m in ipairs(SENT) do if m[1] == "LvPilot2" and (m[2]:sub(1, 1) == "H" or m[2]:find(":H\t")) then hello = true end end
check(hello, "Hallo-Nachricht gesendet")
local recvBefore = LP.db.qdb[5555]
LP.Comm:Receive("Q\t5555\t12\tA\t1429,50,50\t1429,51,51\tGeteilte Quest", "Freund-Server")
check(LP.db.qdb[5555] and LP.db.qdb[5555].net, "fremde Quest uebernommen (als fremd markiert)")
LP.Comm:Receive("Q\t5556\t12\tA\t1429,500,50\t\tKaputt", "Boese")
check(LP.db.qdb[5556] and not LP.db.qdb[5556].s, "ungueltige Koordinate verworfen")
LP.Comm:Receive("Q\t5557\t99\tA\t\t\tLevel 99", "Boese")
check(not LP.db.qdb[5557], "ungueltiges Level verworfen")
LP.Comm:Receive("Q\t5558\t5\tX\t\t\tFalsche Fraktion", "Boese")
check(not LP.db.qdb[5558], "ungueltige Fraktion verworfen")
LP.Comm:Receive("Q\t5559\t5\tA\t\t\t" .. string.rep("x", 200), "Boese")
check(not LP.db.qdb[5559], "zu langer Name verworfen")
local own = LP.db.qdb[783] or LP.db.qdb[91741]
local ownId = LP.db.qdb[783] and 783 or 91741
local ownName = own and own.n
LP.Comm:Receive("Q\t" .. ownId .. "\t5\tA\t1429,1,1\t\tUeberschrieben", "Boese")
check(LP.db.qdb[ownId].n == ownName and not LP.db.qdb[ownId].net, "eigene Daten werden nicht ueberschrieben")
local g0 = LP.Graph:Stats().nodes
LP.Comm:Receive("P\t0\t-100,-100,1429;-110,-105,1429;-120,-112,1429", "Freund")
check(LP.Graph:Stats().nodes > g0, "geteilter Weg uebernommen")
local g1 = LP.Graph:Stats().nodes
LP.Comm:Receive("P\t0\t-100,-100,1429;-900,-900,1429", "Boese")
check(LP.Graph:Stats().nodes == g1, "Weg mit unmoeglichem Sprung verworfen")
-- Flut-Schutz
local floodOk = true
for i = 1, 100 do LP.Comm:Receive("H\t2.0\t1\t1", "Flut") end
check(floodOk, "Flut ohne Absturz verarbeitet")

-- 9) Assistent
P.level = 10
DUR[5] = { 10, 100 }
BAGS[1][2] = 0 BAGS[2][2] = 0 BAGS[0][2] = 1
P.talents = 2
LP.Advisor:Run()
local keys = {}
for _, h in ipairs(LP.Advisor.hints) do keys[h.key] = h end
check(keys.dur, "Haltbarkeit-Warnung")
if withQuestie then
    check(keys.dur and keys.dur.action and keys.dur.text:find("Schmied"), "Reparatur-Haendler gefunden: " .. (keys.dur and keys.dur.text or ""))
    keys.dur.action()
    check(LP.Engine:Current() and LP.Engine:Current().key:find("^PRIO:"), "Navigation zum Haendler als erster Schritt")
end
check(keys.bags, "Taschen-Warnung")
check(keys.bagslots, "leere Taschenplaetze erkannt")
if not FOREVER then check(keys.talents, "freie Talentpunkte erkannt") end
DUR[5] = { 90, 100 }
BAGS[0][2] = 10
P.talents = 0
LP.Advisor:Run()
local stillDur = false
for _, h in ipairs(LP.Advisor.hints) do if h.key == "dur" then stillDur = true end end
check(not stillDur, "Warnung verschwindet nach Reparatur")

-- 10) Oberflaeche, Navigation, Zentrale
local ok, err = pcall(function()
    LP.UI:Toggle() LP.UI:Toggle()
    for _, tab in ipairs({ "route", "data", "share", "assist", "settings" }) do LP.Center:Toggle(tab) LP.Center:Refresh() end
    WorldMapFrame:Show()
    LINES_DRAWN = 0
    LP.Nav:Refresh()
    Advance(1, 0.1)
end)
check(ok, "UI, Zentrale, Navigation ohne Fehler " .. tostring(err or ""))
local cur = LP.Engine:Current()
if cur and cur.map then
    check((LINES_DRAWN or 0) > 0, "Pfadlinien gezeichnet: " .. tostring(LINES_DRAWN))
else
    check((LINES_DRAWN or 0) == 0, "ohne Zielort keine Pfadlinie (Schritt " .. (cur and cur.t or "-") .. ")")
end

local e1 = errorsInChat()
check(#e1 == 0, "keine Laufzeitfehler im Chat " .. table.concat(e1, " | "))
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
os.exit(fails == 0 and 0 or 1)
