-- Test: Questfortschritt ueber den Namensplaketten
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end

-- Spiel-Schnittstellen fuer Namensplaketten nachbilden
strsplit = strsplit or function(sep, s) local t = {} for part in (s .. sep):gmatch("(.-)" .. sep:gsub("%p", "%%%0")) do t[#t + 1] = part end return unpack(t) end
UNITS = {}      -- [unit] = { npc = id, name = "...", player = bool, dead = bool }
function UnitGUID(u) local d = UNITS[u] if not d then return nil end if d.player then return "Player-1-0000ABCD" end return "Creature-0-1-1-1-" .. d.npc .. "-0000ABCD" end
local oldName = UnitName
function UnitName(u) if UNITS[u] then return UNITS[u].name end return oldName(u) end
function UnitIsPlayer(u) return UNITS[u] and UNITS[u].player or false end
function UnitIsDead(u) return UNITS[u] and UNITS[u].dead or false end
local plates = {}
C_NamePlate = {
    GetNamePlateForUnit = function(u) if not UNITS[u] then return nil end plates[u] = plates[u] or CreateFrame("Frame") plates[u].namePlateUnitToken = u return plates[u] end,
    GetNamePlates = function() local out = {} for u in pairs(UNITS) do out[#out + 1] = C_NamePlate.GetNamePlateForUnit(u) end return out end,
}
ITEMNAMES = { [4892] = "Durotar-Tigerfell", [4887] = "Unbeschädigtes Makruraauge", [4888] = "Krabblerschleim" }
C_Item = C_Item or {}
C_Item.GetItemNameByID = function(id) return ITEMNAMES[id] end
-- Questziele mit Art (wie der moderne Client)
local baseObj = C_QuestLog.GetQuestObjectives
C_QuestLog.GetQuestObjectives = function(id)
    local out = baseObj(id)
    for _, q in ipairs(LOG) do if q.id == id then for i, ob in ipairs(q.objs) do if out[i] then out[i].type = ob.type end end end end
    return out
end
local function holderText(u)
    return LP.Plates:Shown(C_NamePlate.GetNamePlateForUnit(u))
end
local function addQuest(id, objs)
    LOG[#LOG + 1] = { title = "Q" .. id, id = id, level = 3, complete = false, objs = objs }
    FireAccepted(#LOG, id)
end
-- deutsche Questziele (Spielsprache), Daten aus dem Datenpaket sind englisch
addQuest(788, { { "Ebereber getötet: 3/10", false, type = "monster" } })
addQuest(817, { { "Durotar-Tigerfell: 2/4", false, type = "item" } })
addQuest(818, { { "Unbeschädigtes Makruraauge: 1/4", false, type = "item" }, { "Krabblerschleim: 4/4", true, type = "item" } })
LP.Planner:Replan()
local P = LP.Plates
check(P ~= nil, "Modul geladen")

UNITS.nameplate1 = { npc = 3098, name = "Ebereber" }
UNITS.nameplate2 = { npc = 3121, name = "Durotartiger" }
UNITS.nameplate3 = { npc = 3103, name = "Makrura-Panzerkrebs" }
UNITS.nameplate4 = { npc = 3106, name = "Brandungskrabbler" }
UNITS.nameplate5 = { npc = 3101, name = "Wichtel" }
UNITS.nameplate6 = { player = true, name = "Anderer" }

-- 1) alle offenen Quests
LP.db.platesAll = true
P:Refresh()
check(holderText("nameplate1") == "3/10", "Ebereber (Toeten): " .. tostring(holderText("nameplate1")))
check(holderText("nameplate2") == "2/4", "Durotartiger (Fell fallen lassen): " .. tostring(holderText("nameplate2")))
check(holderText("nameplate3") == "1/4", "Makrura (Auge): " .. tostring(holderText("nameplate3")))
check(holderText("nameplate4") == nil, "Krabbler: Ziel schon erfüllt, keine Anzeige")
check(holderText("nameplate5") == nil, "Gegner ohne Quest: keine Anzeige")
check(holderText("nameplate6") == nil, "Spieler: keine Anzeige")

-- 2) Fortschritt aktualisiert sich
LOG[1].objs[1][1] = "Ebereber getötet: 4/10"
FireEvent("QUEST_LOG_UPDATE") Advance(1)
check(holderText("nameplate1") == "4/10", "nach einem Kill: " .. tostring(holderText("nameplate1")))

-- 3) nur aktueller Schritt
LP.db.platesAll = false
P:Refresh()
local cur = LP.Engine:Current()
local shown = 0
for u in pairs(UNITS) do if holderText(u) then shown = shown + 1 end end
if cur and cur.t == "COMPLETE" then
    check(shown >= 1, "nur aktueller Schritt (" .. tostring(cur.id) .. "): " .. shown .. " Gegner markiert")
else
    check(shown == 0, "aktueller Schritt ist kein Questziel (" .. tostring(cur and cur.t) .. "): nichts markiert")
end
-- ein Questziel als aktuellen Schritt erzwingen
LP.Engine.Current = function() return { t = "COMPLETE", id = 788 } end
P:Refresh()
check(holderText("nameplate1") == "4/10" and holderText("nameplate2") == nil, "nur die laufende Quest wird gezeigt")

-- 4) ohne Art (aeltere Schnittstelle) und Namenszuordnung
for _, q in ipairs(LOG) do for _, ob in ipairs(q.objs) do ob.type = nil end end
LP.db.platesAll = true
P:Refresh()
check(holderText("nameplate1") == "4/10", "ohne Ziel-Art: Ebereber über den Namen erkannt")
check(holderText("nameplate2") == "2/4", "ohne Ziel-Art: Tigerfell über Gegenstandsname erkannt")

-- 5) abschaltbar, tote Gegner
UNITS.nameplate1.dead = true
P:Refresh()
check(holderText("nameplate1") == nil, "toter Gegner: keine Anzeige")
LP.db.platesQuest = false
P:Refresh()
local any = false for u in pairs(UNITS) do if holderText(u) then any = true end end
check(not any, "ausgeschaltet: nichts angezeigt")

for _, m in ipairs(CHAT) do if m:find("Fehler") and not m:find("keiner") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
