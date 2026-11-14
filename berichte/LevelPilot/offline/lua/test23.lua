-- Test: Namen aus dem Spiel in der eingestellten Sprache (3.5.0)
-- Aufruf: PACKDIR=... NAMESDIR=... FOREVER=1 LVL=12 MAP=1413 PX=51.5 PY=30.3 lua51 test23.lua <Addon> 0 Orc WARRIOR Horde
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
local NAMESDIR = os.getenv("NAMESDIR")
LOADED = {}
local function load(name)
    local loc = name:match("^LevelPilot_Data_(%a%a%a%a)$")
    if not loc then return false end
    local f = loadfile(NAMESDIR .. "/" .. name .. "/Names.lua")
    if not f then return false end
    f(name, {}) LOADED[#LOADED + 1] = loc
    return true
end
C_AddOns = { LoadAddOn = load }
dofile(dir .. "/mock2.lua")
C_AddOns.LoadAddOn = load
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end

check(LevelPilotNames and LevelPilotNames.deDE, "Namen in der Sprache des Spiels bereit (aus dem Datenpaket)")
-- Deutsch (Spielsprache): Namen auf Deutsch, auch fuer Quests, die noch nicht im Log sind
local q = LP.QuestDB:Get(844)
check(q and q.name ~= "Plainstrider Menace", "Deutsch: Quest 844 nicht mehr englisch: " .. tostring(q and q.name))
LP:SetLanguage("fr")
check(LevelPilotNames.frFR and not LevelPilotNames.ruRU, "Französisch nur bei Bedarf aufgebaut, Russisch nicht")
q = LP.QuestDB:Get(844)
check(q.name == "La menace des trotteurs des plaines", "Französisch: " .. q.name)
local giver = q.starts[1] and q.starts[1][4]
print("       Questgeber: " .. tostring(giver))
-- Ziel-Makro braucht die Namen des Spiels (deutsch)
local q788 = LP.QuestDB:Get(788)
local mob = q788.objectives[1] and q788.objectives[1].mobs and q788.objectives[1].mobs[1]
print("       Gegner für /targetexact: " .. tostring(mob))
check(mob and mob ~= "Mottled Boar" and not mob:find("Sanglier"), "Ziel-Makro behält den Namen des Spiels (deutsch)")
-- Zone
LP.Geo:ResetNames()
check(LP.Geo:MapName(1413) == "Les Tarides", "Zone auf Französisch: " .. LP.Geo:MapName(1413))
-- Questziel im Log: deutsch vom Spiel -> französisch
LOG[#LOG + 1] = { title = "Die Ebenenschreiterbedrohung", id = 844, level = 12, complete = false,
                  objs = { { "Ebenenschreiter-Schnabel: 3/7", false, type = "item" } } }
FireAccepted(#LOG, 844)
Advance(2)
LP.Planner:Replan()
local st = LP.Planner.inLog[844]
print("       Get(844):", LP.QuestDB:Get(844).name, LP.Names:Quest(844), LP:Language())
local step = { t = "COMPLETE", id = 844, q = LP.QuestDB:Get(844).name, key = "C:844", map = 1413 }
local txt = LP.UI:StepText(step, true)
print("       Schritt: " .. txt:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("\n", " / "))
check(txt:find("La menace des trotteurs") and txt:find("3/7") and not txt:find("Ebenenschreiter"), "Schritt komplett französisch")
-- Englisch
LP:SetLanguage("en")
check(LP.QuestDB:Get(844).name == "Plainstrider Menace", "Englisch: Namen aus dem Datenpaket")
LP.Geo:ResetNames()
check(LP.Geo:MapName(1413) == "The Barrens", "Zone auf Englisch")
-- zurueck auf Deutsch
LP:SetLanguage("de")
local de = LP.QuestDB:Get(844).name
check(de == "Die Ebenenschreiterbedrohung", "zurück auf Deutsch: Titel wie im Spiel: " .. de)
check(LP.Geo:MapName(1413) == "Zone1413", "Deutsch = Spielsprache: Zonenname vom Spiel")
local txt2 = LP.UI:StepText(step, true)
check(txt2:find("Ebenenschreiter%-Schnabel: 3/7"), "Deutsch: Questziel wieder vom Spiel")
-- Italienisch: keine Questie-Daten -> Englisch
LP:SetLanguage("it")
check(LP.QuestDB:Get(844).name == "Plainstrider Menace", "Italienisch: englische Namen")
-- ohne Sprachpaket installiert: nichts kaputt
C_AddOns.LoadAddOn = function() return false end
LevelPilotNames.zhCN = nil
LP:SetLanguage("cn")
check(LP.QuestDB:Get(844).name ~= nil, "Sprachpaket fehlt: Namen aus dem Datenpaket, kein Fehler")
for _, m in ipairs(CHAT) do if m:find("attempt") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
