-- Test: neue Funktionen 3.0 (Aktionsleiste, Haendler, Fliegen, NEU, Zeit, Ruhestein, echte EP,
-- Gruppe, Dungeon-Uebersicht, Finde naechsten, Sicherer Modus)
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
-- seit 3.12.4 ab Werk aus: fuer diesen Test einschalten
NS.db.autoRepair, NS.db.autoFly, NS.db.restock, NS.db.autoEquipRewards = true, true, true, true
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end

-- Spiel-Funktionen fuer diesen Test
BAGITEMS = {}      -- [bag] = { [slot] = { id, count, quality, price } }
local function count(id) local n = 0 for _, b in pairs(BAGITEMS) do for _, it in pairs(b) do if it[1] == id then n = n + (it[2] or 1) end end end return n end
C_Item = C_Item or {}
C_Item.GetItemCount = count
C_Item.GetItemSpell = function(id) return id == 5000 and "Benutzen" or nil end
C_Item.GetItemIconByID = function() return "icon" end
C_Item.GetItemInfo = function(id) local p = 0 for _, b in pairs(BAGITEMS) do for _, it in pairs(b) do if it[1] == id then p = it[4] or 0 end end end return "Item" .. id, nil, nil, nil, nil, nil, nil, nil, nil, nil, p end
C_Container.GetItemCooldown = function() return 0, 0 end
C_Container.GetContainerItemInfo = function(b, s) local it = BAGITEMS[b] and BAGITEMS[b][s] if not it then return nil end return { itemID = it[1], stackCount = it[2], quality = it[3], hyperlink = "item:" .. it[1] } end
USED = {}
C_Container.UseContainerItem = function(b, s) USED[#USED + 1] = { b, s } end
REPAIRED = false
function CanMerchantRepair() return true end
function GetRepairAllCost() return 1234, true end
function GetMoney() return 100000 end
function RepairAllItems() REPAIRED = true end
MerchantFrame = setmetatable({}, { __index = function() return function() return true end end })
TAXI = {}
function NumTaxiNodes() return #TAXI end
function TaxiNodeName(i) return TAXI[i] end
function TaxiNodeGetType() return "REACHABLE" end
TOOK = nil
function TakeTaxiNode(i) TOOK = i end
function GetBindLocation() return "Goldhain" end

LP.Planner:Replan()

-- 1) Aktionsleiste: Ziel anvisieren
local q7 = LP.QuestDB:Get(7)   -- Kobold Camp Cleanup
LOG[#LOG + 1] = { title = q7.name, id = 7, level = 2, complete = false, objs = { { "Kobold Vermin: 0/10", false } } }
FireAccepted(#LOG, 7)
FireEvent("QUEST_LOG_UPDATE")
NOW = NOW + 1
LP.Planner:Replan()
local step
for _, s in ipairs(LP.Engine:Steps()) do if s.t == "COMPLETE" and s.id == 7 then step = s end end
LP.Planner.steps = { step }
LP.UI:Toggle() if not LP.UI:IsShown() then LP.UI:Toggle() end
LP.Actions:Update()
local mt = LP.Actions.btnTarget.attrs.macrotext or ""
check(mt:find("/targetexact Koboldgezücht", 1, true) or mt:find("/targetexact Kobold Vermin", 1, true), "Ziel-Knopf visiert Questgegner an (Name des Spiels): " .. mt:gsub("\n", " | "):sub(1, 70))
check(#mt <= 255, "Makro passt in 255 Zeichen")

-- 2) Questgegenstand / Ruhestein
BAGITEMS[0] = { [1] = { 6948, 1, 1, 0 } }
LP.Planner.steps = { { t = "HEARTH", text = "Goldhain", item = 6948, key = "HEARTH:x", noNav = true } }
LP.Actions:Update()
check(LP.Actions.btnItem.attrs.item == "item:6948", "Gegenstand-Knopf benutzt den Ruhestein beim Ruhestein-Schritt")

-- 3) Haendler: grau verkaufen + reparieren
BAGITEMS[1] = { [1] = { 1001, 3, 0, 25 }, [2] = { 1002, 1, 2, 500 } }
FireEvent("MERCHANT_SHOW")
Advance(1)
check(REPAIRED, "automatisch repariert")
check(#USED >= 1 and USED[1][1] == 1 and USED[1][2] == 1, "grauer Gegenstand verkauft, grüner nicht (" .. #USED .. ")")

-- 4) Automatisch fliegen
TAXI = { "Sturmwind, Elwynn", "Späherkuppe, Westfall" }
LP.Planner.steps = { { t = "FLY", text = "Späherkuppe, Westfall", key = "FLY:x" } }
LP.Comfort:AutoFly()
check(TOOK == 2, "fliegt automatisch zum geplanten Ziel")

-- 5) NEU-Markierung
LP.db.qdb[123456] = { n = "Neue Forever-Quest", l = 8, s = { 1429, 45, 45, "Bauer" } }
LP.QuestDB:Invalidate(123456)
local nq = LP.QuestDB:Get(123456)
check(nq and nq.isNew, "Quest ohne Classic-Daten gilt als neu")
check(not LP.QuestDB:Get(7).isNew, "Classic-Quest gilt nicht als neu")
local txt = LP.UI:StepText({ t = "ACCEPT", id = 123456, q = "Neue Forever-Quest", isNew = true, key = "A" }, true)
check(txt:find("NEU", 1, true), "Anzeige mit [NEU]")

-- 6) Zeitanzeige
P.xp = 0
FireEvent("PLAYER_XP_UPDATE")
for _ = 1, 10 do P.x = P.x + 0.2 NOW = NOW + 60 Advance(60) end   -- 10 Minuten unterwegs (nicht AFK)
P.xp = 300
FireEvent("PLAYER_XP_UPDATE")
local rate = LP.Comfort:XPPerHour()
check(rate and rate > 500 and rate < 3000, "EP pro Stunde: " .. tostring(rate and math.floor(rate)))
check(LP.Comfort:TimerText(), "Kopfzeile zeigt " .. tostring(LP.Comfort:TimerText()))
check(LP.Comfort:TimeTo60(), "Schätzung bis 60: " .. LP.Comfort.Dur(LP.Comfort:TimeTo60() or 0))

-- 7) Ruhestein einplanen
LP.char.bind = { map = 1429, x = 42, y = 65, name = "Goldhain" }
local bi, bn, bw = LP.Geo:ToWorld(1429, 42, 66)
local target = { inst = bi, n = bn, w = bw, key = "T", map = 1429 }
local pi, pn, pw = LP.Geo:ToWorld(1436, 40, 90)     -- weit weg im Sueden von Westfall
local hs = LP.Planner:HearthStep(target, pi, pn, pw)
check(hs and hs.t == "HEARTH", "Ruhestein wird eingeplant, wenn das Ziel am Bindeort liegt")
local near = LP.Planner:HearthStep(target, LP.Geo:ToWorld(1429, 45, 62))
check(not near, "in der Nähe kein Ruhestein")

-- 8) Echte EP bei der Abgabe
FireEvent("QUEST_TURNED_IN", 7, 210, 0)
LP.QuestDB:Invalidate(7)
check(LP.db.qdb[7] and LP.db.qdb[7].x == 210, "Abgabe-EP aufgezeichnet")
local xp, measured = LP.Planner.BaseXP(LP.QuestDB:Get(7))
check(xp == 210 and measured, "Planer nutzt die gemessene EP (" .. tostring(xp) .. ")")

-- 9) Gruppe
P.group = true
LP.db.groupSync = true
local function Msg(...) if GoldSentinelSync then GoldSentinelSync.OnAddonMessage(...) else FireEvent("CHAT_MSG_ADDON", ...) end end
Msg("LvPilotG", "S\t3\t40\tACCEPT\t783\tAnnehmen: A Threat Within", "PARTY", "Anna-Realm")
Msg("LvPilotG", "L\t1\t783,7", "PARTY", "Anna-Realm")
local shared = LP.Group:SharedQuests()
check(shared and shared[7] == 1 and shared[783] == 1, "gemeinsame Quests erkannt")
check(#LP.Group:Active() == 1 and LP.Group:Status(LP.Group.members.Anna), "Mitspieler Anna: " .. tostring(LP.Group:Status(LP.Group.members.Anna)))
SENT = {}
LP.Group:Broadcast()
if GoldSentinelSync then for _ = 1, 10 do GoldSentinelSync.Pump(true) end end
local sentS = false
for _, m in ipairs(SENT) do if m[1] == "LvPilotG" and (m[2]:sub(1, 1) == "S" or m[2]:find(":S\t")) then sentS = true end end
check(sentS, "eigener Stand wird an die Gruppe gesendet")

-- 10) Dungeon-Uebersicht
local ov = LP.Planner:DungeonOverview()
check(#ov == 19, "Übersicht mit 19 Dungeons")
local rfc
for _, d in ipairs(ov) do if d.area == 2437 then rfc = d end end
check(rfc and not rfc.allowed, "Flammenschlund für Allianz gesperrt")

-- 11) Finde naechsten
LP.Planner.priority = nil
LP.Comfort:Find("repair")
check(LP.Planner.priority and LP.Planner.priority.t == "GOTO", "Nächster Reparatur-Händler: " .. tostring(LP.Planner.priority and LP.Planner.priority.text))
LP.Planner.priority = nil
LP.Comfort:Find("trainer")
check(LP.Planner.priority and LP.Planner.priority.text:find("Klassentrainer", 1, true), "Klassentrainer gefunden: " .. tostring(LP.Planner.priority and LP.Planner.priority.text))
LP.Planner.priority = nil
LP.Comfort:Find("mailbox")
check(LP.Planner.priority, "Briefkasten gefunden")
LP.Planner.priority = nil

-- 12) Sicherer Modus
P.level = 10
LP.Planner:BuildCandidates()
LP.db.safeMode = false
LP.Planner:Replan()
LP.db.safeMode = true
LP.Planner:Replan()
local skipped = 0 for _ in pairs(LP.Planner.safeSkip) do skipped = skipped + 1 end
check(skipped > 0, "Sicherer Modus lässt gefährliche Quests aus: " .. skipped)
LP.db.safeMode = false

-- 13) Zentrale-Seiten
local okUI, err = pcall(function()
    LP.Center:Toggle("dungeons") LP.Center:Select("dungeons") LP.Center:Refresh()
    LP.Center:Select("comfort") LP.Center:Refresh()
end)
check(okUI, "Reiter Dungeons und Komfort: " .. tostring(err or "ok"))

for _, m in ipairs(CHAT) do if (m:find("Fehler") and not m:find("Letzter Fehler: keiner")) or m:find("konnte nicht") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
