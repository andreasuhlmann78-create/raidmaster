-- Test: Komfortfunktionen 3.4 (Karte, Tooltips, Vorraete, Sitzung, Hinweise, Gruppe, Leiche, Kompakt, Charakter)
-- Aufruf: PACKDIR=... FOREVER=1 LVL=6 MAP=1411 PX=43.3 PY=68.5 lua51 test17.lua <Addon> 0 Orc HUNTER Horde
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
-- seit 3.12.4 ab Werk aus: fuer diesen Test einschalten
NS.db.autoRepair, NS.db.autoFly, NS.db.restock, NS.db.autoEquipRewards = true, true, true, true
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local function sect(t) print("-- " .. t) end

-- zusaetzliche Spiel-Schnittstellen
MONEY = 50000
function GetMoney() return MONEY end
GetCoinTextureString = function(c) return LP.Session.Money(c) end
ITEMS = {}                       -- [id] = Anzahl im Inventar
C_Item = C_Item or {}
C_Item.GetItemCount = function(id) return ITEMS[id] or 0 end
INSTANT = {}                     -- [id] = { classID, subclassID }
local function instant(id) local e = INSTANT[id] or { 0, 0 } return id, "", "", "", 0, e[1], e[2] end
C_Item.GetItemInfoInstant = function(x) local id = type(x) == "number" and x or tonumber(tostring(x):match("item:(%d+)")) return instant(id) end
GetItemInfoInstant = C_Item.GetItemInfoInstant
UIERR = {}
UIErrorsFrame = { AddMessage = function(_, m) UIERR[#UIERR + 1] = m end }
function UnitPowerType() return 0 end
RANGED = "item:2504"             -- Bogen
INSTANT[2504] = { 2, 2 }
function GetInventoryItemLink(_, slot) if slot == 18 then return RANGED end return nil end
PET = true
local baseExists = UnitExists
function UnitExists(u) if u == "pet" then return PET end return baseExists(u) end
local baseLevel = UnitLevel
function UnitLevel(u) if u == "pet" then return P.level end return baseLevel(u) end
function GetPetFoodTypes() return "Meat", "Fish" end
function GetPetHappiness() return 3 end
-- Haendler
MERCHANT = {}
BOUGHT = {}
MerchantFrame = CreateFrame("Frame") MerchantFrame:Show()
function GetMerchantNumItems() return #MERCHANT end
function GetMerchantItemLink(i) return MERCHANT[i] and ("item:" .. MERCHANT[i].id) end
function GetMerchantItemInfo(i) local m = MERCHANT[i] return m.name, nil, m.price, m.per or 1, -1 end
function BuyMerchantItem(i, n) BOUGHT[#BOUGHT + 1] = { id = MERCHANT[i].id, n = n or 1 } ITEMS[MERCHANT[i].id] = (ITEMS[MERCHANT[i].id] or 0) + (MERCHANT[i].per or 1) * (n or 1) end
-- Sonstiges
REST, RESTING, GHOST, AFK = 0, false, false, false
function GetXPExhaustion() return REST end
function IsResting() return RESTING end
function UnitIsGhost() return GHOST end
function UnitIsAFK() return AFK end
CORPSE = nil
C_DeathInfo = { GetCorpseMapPosition = function(map) if CORPSE and map == CORPSE[1] then return CreateVector2D(CORPSE[2] / 100, CORPSE[3] / 100) end return nil end }
CHATOPEN = nil
function ChatFrame_OpenChat(t) CHATOPEN = t end
function GetChannelList() return 1, "General", false, 4, "SucheNachGruppe", false end
PUSHED = {}
C_QuestLog.IsPushableQuest = function() return true end
C_QuestLog.SetSelectedQuest = function(id) SELQ = id end
function QuestLogPushQuest() PUSHED[#PUSHED + 1] = SELQ end
INVITED = nil
C_PartyInfo = { InviteUnit = function(n) INVITED = n end }
GUILDMSG = nil
function IsInGuild() return true end
function SendChatMessage(t, kind) if kind == "GUILD" then GUILDMSG = t end end
function UnitInParty() return false end

local function addQuest(id, objs, complete)
    LOG[#LOG + 1] = { title = "Q" .. id, id = id, level = 5, complete = complete or false, objs = objs or {} }
    FireAccepted(#LOG, id)
end
local function hint(key)
    LP.Advisor:Run()
    for _, h in ipairs(LP.Advisor.hints) do if h.key == key or h.key:find(key, 1, true) then return h end end
    return nil
end

------------------------------------------------------------------------
sect("Karte & Questgegenstaende")
-- Quest mit Gegenstand aus Objekten: suche in den Daten eine Durotar-Quest mit Objekt-Fundstellen
local objQuest
for _, id in ipairs(LP.QuestDB:AllIds()) do
    local q = LP.QuestDB:Get(id)
    if q and q.starts[1] and q.starts[1][1] == 1411 then
        for _, o in ipairs(q.objectives or {}) do
            for _, p in ipairs(o.spots or {}) do if p.obj and p[1] == 1411 then objQuest = objQuest or { id = id, o = o, p = p } end end
        end
    end
end
check(objQuest ~= nil, "Durotar-Quest mit Fundstellen am Boden gefunden: " .. tostring(objQuest and objQuest.id))
addQuest(objQuest.id, { { "Plan A: 0/1", false, type = "object" }, { "Plan B: 0/1", false, type = "object" }, { "Plan C: 0/1", false, type = "object" } })
addQuest(788, { { "Ebereber getötet: 3/10", false, type = "monster" } })
LP.Planner:Replan()
-- aktueller Schritt: Ziele der Objekt-Quest
local origCurrent = LP.Engine.Current
LP.Engine.Current = function() return { t = "COMPLETE", id = objQuest.id, key = "C:" .. objQuest.id, map = 1411 } end
LP.Pins:Refresh()
check(#LP.Pins.objects > 0, "Fundstellen der laufenden Quest: " .. #LP.Pins.objects)
check(#LP.Pins.areas > 0, "Questgebiete: " .. #LP.Pins.areas)
check(#LP.Pins.avail >= 0, "annehmbare Quests: " .. #LP.Pins.avail)
-- in die Naehe einer Fundstelle gehen
local p = objQuest.p
P.map, P.x, P.y = p[1], p[2] + 0.6, p[3]
NOW = NOW + 1
local t = LP.Pins:NearestObject()
check(t and t.label and t.dist and t.dist < 250, "Pfeil zur nächsten Fundstelle (" .. (t and math.floor(t.dist) or "?") .. " Yards)")
LP.Nav:Recalc(true)
check(LP.Nav.active and LP.Nav.active.key:find("^OBJ:"), "Navigation nutzt die Fundstelle als Ziel")
P.x = p[2] + 0.05 NOW = NOW + 1
UIERR = {}
LP.Pins:CheckAlert()
check(#UIERR == 1 and UIERR[1]:find("0/1"), "Hinweis in der Nähe: " .. tostring(UIERR[1]))
LP.Pins:CheckAlert()
check(#UIERR == 1, "Hinweis nicht wiederholt")
-- angekommen: naechste Fundstelle
P.x = p[2] NOW = NOW + 1
local t2 = LP.Pins:NearestObject()
check(not t2 or t2.entry.p ~= p, "besuchte Fundstelle wird übersprungen")
LP.Pins:UpdateMinimap()
check(true, "Minikarte ohne Fehler")
WorldMapFrame:Show() WorldMapFrame.GetMapID = function() return 1411 end
LP.Pins:UpdateWorldMap()
check(true, "Weltkarte ohne Fehler")
LP.db.objArrow = false
check(LP.Pins:NearestObject() == nil, "Pfeil zur Fundstelle abschaltbar")
LP.db.objArrow = true

------------------------------------------------------------------------
sect("Tooltips & Schutz")
local starter
for _, id in ipairs(LP.QuestDB:AllIds()) do
    local q = LP.QuestDB:Get(id)
    if q and q.itemStart then starter = id break end
end
local idx
for _, id in ipairs(LP.QuestDB:AllIds()) do
    local info = LP.QuestDB:QuickInfo(id)
end
-- Gegenstand, der eine Quest startet
local startItem
for it = 1, 30000 do
    local e = LP.QuestDB:ItemQuests(it)
    if e and e.starts then startItem = it break end
end
check(startItem ~= nil, "Gegenstand, der eine Quest startet: " .. tostring(startItem))
local lines = LP.Tooltips:ItemLines(startItem)
check(lines and lines[1]:find("Startet die Quest"), "Tooltip: " .. tostring(lines and lines[1]))
check(LP.Tooltips:IsProtected(startItem), "Startgegenstand wird nie verkauft")
-- Gegenstand fuer eine laufende Quest
local needItem = objQuest.o.item
if needItem then
    local l2 = LP.Tooltips:ItemLines(needItem)
    check(l2 and l2[1]:find("Für Quest"), "Questgegenstand im Tooltip: " .. tostring(l2 and l2[1]))
    check(LP.Tooltips:IsProtected(needItem), "Questgegenstand geschützt")
end
-- Gegner-Tooltip
strsplit = strsplit or function(sep, s) local t = {} for part in (s .. sep):gmatch("(.-)" .. sep:gsub("%p", "%%%0")) do t[#t + 1] = part end return unpack(t) end
function UnitGUID(u) if u == "mouseover" then return "Creature-0-1-1-1-3098-0000ABCD" end return nil end
local baseName = UnitName
function UnitName(u) if u == "mouseover" then return "Ebereber" end return baseName(u) end
function UnitIsPlayer() return false end
function UnitIsDead() return false end
LP.Plates:Refresh()
local ul = LP.Tooltips:UnitLines("mouseover")
check(ul and ul[1]:find("3/10"), "Gegner-Tooltip: " .. tostring(ul and ul[1]))
-- Objekt-Tooltip an einer Fundstelle
P.map, P.x, P.y = p[1], p[2], p[3] NOW = NOW + 1
LP.Pins:Refresh()
local ol = LP.Tooltips:ObjectLines("Irgendeine Kiste")
check(ol and ol[1], "Objekt-Tooltip an der Fundstelle: " .. tostring(ol and ol[1]))

------------------------------------------------------------------------
sect("Vorraete")
MERCHANT = {
    { id = 159, name = "Erfrischendes Quellwasser", price = 25, per = 1 },
    { id = 1179, name = "Eiskalte Milch", price = 125, per = 1 },
    { id = 117, name = "Zähes Dörrfleisch", price = 25, per = 1 },
    { id = 2287, name = "Fleischkeule", price = 125, per = 1 },
    { id = 4540, name = "Hartes Brot", price = 25, per = 1 },
    { id = 2512, name = "Raue Pfeile", price = 10, per = 200 },
    { id = 5000, name = "Anderes", price = 1, per = 1 },
}
P.level = 6
local plan, spent = LP.Supply:Plan()
local byId = {}
for _, e in ipairs(plan) do byId[e.id] = e end
check(byId[1179] and byId[1179].purchases == 20, "Wasser: beste Stufe (Level 5) ×20")
check(byId[2287] and not byId[117], "Essen: beste Stufe (Fleischkeule)")
check(byId[2512] and byId[2512].purchases == 5, "Pfeile: 5×200 bis 1000")
local petPlan = 0 for _, e in ipairs(plan) do if e.label == "pet" then petPlan = petPlan + 1 end end
check(petPlan == 1, "Tierfutter nach Futterart (Fleisch)")
check(spent <= MONEY * 0.25, "höchstens 25 % des Goldes (" .. spent .. ")")
ITEMS[1179] = 30
local plan2 = LP.Supply:Plan()
local water = false for _, e in ipairs(plan2) do if e.id == 1179 then water = true end end
check(not water, "genug Wasser: nichts nachkaufen")
MONEY = 200
local plan3, spent3 = LP.Supply:Plan()
check(spent3 <= 50, "wenig Gold: Budget eingehalten (" .. spent3 .. ")")
MONEY = 50000
LP.Supply:Restock()
Advance(5)
check(#BOUGHT > 0, "Einkauf ausgeführt (" .. #BOUGHT .. " Käufe)")
-- Magier: kein Wasser
local baseClass = UnitClass
function UnitClass() return "Magier", "MAGE" end
local mplan = LP.Supply:Plan()
local mw = false for _, e in ipairs(mplan) do if e.label == "water" then mw = true end end
check(not mw, "Magier: kein Wasser (zaubert selbst)")
UnitClass = baseClass

------------------------------------------------------------------------
sect("Belohnung anlegen & Taschen")
EQUIPPED = nil
LP.API.Equip = function(link) EQUIPPED = link end
LP.Advisor.UpgradeValue = function(_, link) return link:find("9999") and 10 or nil end
LP.API.IsEquippable = function() return true end
function GetNumQuestChoices() return 2 end
function GetNumQuestRewards() return 0 end
function GetQuestItemLink(kind, i) return kind == "choice" and ("item:" .. (i == 1 and 9999 or 9998)) or nil end
LP.Supply:RememberRewards()
local bagItems = { [0] = { [1] = "item:9999", [2] = "item:9998" } }
LP.API.BagSlots = function(b) return b == 0 and 2 or 0 end
LP.API.BagLink = function(b, s) return bagItems[b] and bagItems[b][s] end
LP.API.BagItem = function(b, s) local l = bagItems[b] and bagItems[b][s] if not l then return nil end return { id = tonumber(l:match("(%d+)")), count = 1, quality = 2, link = l } end
LP.Supply:EquipRewards()
check(EQUIPPED == "item:9999", "Upgrade aus der Belohnung angelegt")
EQUIPPED = nil
LP.Supply:EquipRewards()
check(EQUIPPED == nil, "nur einmal")
-- Taschen: Questgegenstand erledigter Quest
local doneQuest, doneItem
for it = 1, 30000 do
    local e = LP.QuestDB:ItemQuests(it)
    if e and e.needs and not e.starts then doneItem, doneQuest = it, e.needs[1] break end
end
FLAGGED[doneQuest] = true
for _, q in ipairs(LP.QuestDB:ItemQuests(doneItem).needs) do FLAGGED[q] = true end
INSTANT[doneItem] = { 12, 0 }
bagItems[0][2] = "item:" .. doneItem
local junk = LP.Supply:Junk()
check(#junk == 1 and junk[1].kind == "quest", "Taschen: Questgegenstand erledigter Quest erkannt")
check(hint("junk"), "Hinweis „Taschen aufräumen“")

------------------------------------------------------------------------
sect("Zeit, Gold, Sitzung")
for i = 1, 400 do P.x = P.x + (i % 2 == 0 and 0.15 or -0.15) NOW = NOW + 1 Advance(1) end
print("       Uhr vor Schleife?", LP.Session:IsAFK(), UnitIsAFK and UnitIsAFK("player"))
local c1 = LP.Session:Clock()
check(c1 >= 390, "aktive Zeit läuft beim Bewegen (" .. c1 .. ")")
AFK = true
Advance(60)
check(LP.Session:Clock() == c1 + 0 or LP.Session:Clock() <= c1 + 1, "AFK: Zeit steht")
AFK = false
MONEY = MONEY + 12345 FireEvent("PLAYER_MONEY")
for i = 1, 10 do P.x = P.x + (i % 2 == 0 and 0.15 or -0.15) NOW = NOW + 1 Advance(1) end
local gph = LP.Session:GoldPerHour()
check(gph and gph > 0, "Gold pro Stunde: " .. tostring(gph and LP.Session.Money(gph)))
-- Bestzeiten
LP.char.levelTimes = { [6] = 900 }
LP.db.bestLevel = { [6] = { t = 1200, who = "Zwilling" } }
CHAT = {}
P.level = 7 FireEvent("PLAYER_LEVEL_UP", 7) Advance(1)
local best = false for _, m in ipairs(CHAT) do if m:find("neuer Bestwert") then best = true end end
check(best and LP.db.bestLevel[6].t <= 900, "neuer Bestwert gemeldet und gespeichert")
-- Zeit-Schaetzung
local st = LP.Planner.inLog[788]
local eta = LP.Session:QuestETA(788)
check(eta and eta > 0, "Zeit-Schätzung für Ebereber: " .. tostring(eta and LP.Comfort.Dur(eta)))
LOG[2].objs[1][1] = "Ebereber getötet: 5/10" FireEvent("QUEST_LOG_UPDATE") Advance(2)
for i = 1, 120 do P.x = P.x + (i % 2 == 0 and 0.15 or -0.15) NOW = NOW + 1 Advance(1) end
LOG[2].objs[1][1] = "Ebereber getötet: 7/10" FireEvent("QUEST_LOG_UPDATE") Advance(2)
local eta2 = LP.Session:QuestETA(788)
check(eta2 and eta2 > 60 and eta2 < 400, "eigenes Tempo: 3 übrig ≈ " .. tostring(eta2 and math.floor(eta2)) .. " s")
local txt = LP.UI:StepText({ t = "COMPLETE", id = 788, q = "Cutting Teeth", key = "C788", map = 1411 }, true)
check(txt:find("ca%."), "Schätzung im Guide")
-- Erholt, Ruhestein
REST = 4200
ITEMS[6948] = 1
local extra = LP.Session:ExtraText()
check(extra and extra:find("Erholt") and extra:find("Ruhestein"), "Statuszeile: " .. tostring(extra))
RESTING = true REST = 100
check(hint("rested"), "Hinweis: im Gasthaus ausloggen")
RESTING = false
-- Wo war ich?
LP.Engine.Current = origCurrent
LP.Planner:Replan()
local wt = LP.Session:WelcomeText()
check(wt and wt:find("1%)"), "„Wo war ich?“ mit nächsten Schritten")
-- Abgaben-Erinnerung
LOG[1].complete = true FireEvent("QUEST_LOG_UPDATE") Advance(1) LP.Planner:Replan()
local q1 = LP.QuestDB:Get(LOG[1].id)
local endMap = q1.ends[1] and q1.ends[1][1]
local open = LP.Session:OpenTurnins(endMap)
check(#open >= 1, "offene Abgaben in " .. tostring(endMap) .. ": " .. #open)
-- Bilanz
local sum = LP.Session:Summary(true)
check(sum:find("Quests") and GUILDMSG == sum, "Bilanz (auch Gilde): " .. sum)

------------------------------------------------------------------------
sect("Hinweise")
local up = LP.Hints:UpcomingClassQuests()
print("       Klassenquests bald (L" .. P.level .. "): " .. #up)
for _, q in ipairs(up) do print("         L" .. q.level .. " " .. tostring(q.name)) end
P.level = 8
local up8 = LP.Hints:UpcomingClassQuests()
local hunter10 = false for _, q in ipairs(up8) do if q.level == 10 then hunter10 = true end end
check(hunter10, "Jäger L8: Klassenquest ab Level 10 angekündigt (" .. #up8 .. ")")
P.level = 10
PET = false
check(hint("pet"), "Jäger ohne Begleiter: Hinweis")
PET = true
-- Trainer-Kosten lernen
function GetNumTrainerServices() return 3 end
function GetTrainerServiceInfo(i) return "Spell" .. i, "", i == 3 and "used" or "unavailable" end
function GetTrainerServiceLevelReq(i) return i == 1 and 12 or 14 end
function GetTrainerServiceCost(i) return 600 * i end
LP.Hints:LearnTrainerCosts()
local c12, g12 = LP.Hints:TrainerCost(12)
check(c12 == 600 and not g12, "Trainerkosten gelernt (Level 12: " .. tostring(c12) .. ")")
local c20, g20 = LP.Hints:TrainerCost(20)
check(c20 and g20, "Trainerkosten geschätzt (Level 20: " .. LP.Session.Money(c20) .. ")")
-- Reittier
P.level = 38
MONEY = 300000
local mh = hint("mountgold")
check(mh and mh.text:find("fehlen"), "Reittier-Gold: " .. tostring(mh and mh.text:gsub("\n", " ")))
P.level = 40 MONEY = 1200000
local mg = hint("mountgo")
check(mg ~= nil, "genug Gold: ab zum Reitlehrer")
P.level = 6 MONEY = 50000

------------------------------------------------------------------------
sect("Gruppe")
P.group = true
local n = LP.Social:ShareQuests()
Advance(5)
check(n >= 2 and #PUSHED >= 2, "Quests geteilt: " .. #PUSHED)
LP.Engine.Current = function() return { t = "DUNGEON", q = "Der Flammenschlund", quests = { "A", "B" }, key = "DG" } end
local line = LP.Social:OpenGroupChat()
check(line and line:find("^/4 ") and line:find("Flammenschlund"), "Gruppen-Text im Suche-Kanal: " .. tostring(line))
P.group = false
check(hint("lfg"), "Hinweis mit Knopf „Text in den Chat“")
-- Elite-Partner
local eliteId
for _, id in ipairs(LP.QuestDB:AllIds()) do
    local q = LP.QuestDB:Get(id)
    if q and q.elite and not q.dungeon and q.starts[1] then eliteId = id break end
end
addQuest(eliteId, { { "Boss getötet: 0/1", false, type = "monster" } })
LP.Planner:Replan()
local enc = LP.Social:Encode()
check(enc and enc:find("^E\t"), "Elite-Quests werden gemeldet: " .. tostring(enc))
local _, _, _, map = LP.Geo:Player()
LP.Social:OnMessage({ "E", tostring(map), tostring(P.level + 1), tostring(eliteId) }, "Thrall-Forever")
local ph = hint("partner")
check(ph and ph.text:find("Thrall"), "Mitspieler gefunden: " .. tostring(ph and ph.text))
if ph then ph.action() end
check(INVITED == "Thrall", "Einladen-Knopf")
LP.db.findPartners = false
check(not hint("partner"), "abschaltbar")
LP.db.findPartners = true

------------------------------------------------------------------------
sect("Leiche, Kompakt, Charakter")
GHOST = true
CORPSE = { P.map, P.x + 2, P.y }
print("       Leiche:", LP.Session:CorpseTarget() ~= nil, P.map, CORPSE[1])
LP.Nav:Recalc(true)
check(LP.Nav.active and LP.Nav.active.key == "CORPSE", "Pfeil zur Leiche")
GHOST = false
LP.Nav:Recalc(true)
check(not (LP.Nav.active and LP.Nav.active.key == "CORPSE"), "nach der Auferstehung normal weiter")
LP.Engine.Current = origCurrent
LP.db.compactMode = true
LP.UI:Toggle() if not LP.UI:IsShown() then LP.UI:Toggle() end
LP.UI:Refresh()
check(true, "Kompaktmodus ohne Fehler")
LP.db.compactMode = false
-- Einstellungen pro Charakter
LP.db.restockMaxPct = 25
LP.db.ownSettings = true
LP.db.restockMaxPct = 10
check(LevelPilotDB.restockMaxPct == 25 and LP.char.settings.restockMaxPct == 10, "Charakter-Einstellung getrennt vom Account")
check(LP.db.restockMaxPct == 10, "Charakter liest eigenen Wert")
LP.db.ownSettings = false
check(LP.db.restockMaxPct == 25, "wieder Account-Einstellung")
LP.db.qdb[999999] = { n = "Test" }
check(LevelPilotDB.qdb[999999], "Daten bleiben immer accountweit")

-- Zentrale mit neuem Reiter
LP.Center:Toggle("extras") LP.Center:Select("extras") LP.Center:Refresh()
check(true, "Zentrale „Extras“ ohne Fehler")

for _, m in ipairs(CHAT) do if (m:find("Fehler") and not m:find("keiner")) or m:find("attempt") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
