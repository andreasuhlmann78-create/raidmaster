-- Test 3.11: Messroutine /lp messen (nur lesen) und Flugdauer aus echten Fluegen lernen
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
-- fehlende Spiel-Funktionen nachbilden
GetBuildInfo = GetBuildInfo or function() return "1.16.1", "54000", "Jan 1 2026", 11601 end
GetXPExhaustion = GetXPExhaustion or function() return 1200 end
GetZoneText = GetZoneText or function() return "Durotar" end
GetSubZoneText = GetSubZoneText or function() return "" end
GetRealZoneText = GetRealZoneText or function() return "Durotar" end
GetBindLocation = GetBindLocation or function() return "Klingenhügel" end
local TGT = { guid = "Creature-0-1-2-3-3098-0000", name = "Narbenrücken-Eber", level = 2 }
local oldExists = UnitExists
function UnitExists(u) if u == "target" then return true end return oldExists(u) end
local oldName = UnitName
function UnitName(u) if u == "target" then return TGT.name end return oldName(u) end
local oldLevel = UnitLevel
function UnitLevel(u) if u == "target" then return TGT.level end return oldLevel(u) end
function UnitGUID(u) if u == "target" then return TGT.guid end return nil end
function UnitIsPlayer(u) return u == "player" end
function UnitClassification() return "normal" end
function UnitCanAttack() return true end
C_NamePlate = { GetNamePlates = function() return { { namePlateUnitToken = "target" } } end }

check(LP.Measure ~= nil, "Modul Measure geladen")
-- Fingerabdruck vorher (nur lesen!)
local function snap()
    local n = 0
    for _ in pairs(LevelPilotDB.qdb or {}) do n = n + 1 end
    local t = 0
    for _ in pairs(LevelPilotDB.taxi or {}) do t = t + 1 end
    local ig = 0
    for _ in pairs(LP.char.ignored or {}) do ig = ig + 1 end
    return n .. "/" .. t .. "/" .. ig .. "/" .. #(LP.Planner.steps or {})
end
Advance(1, 0.1)
local before = snap()
local text = LP.Measure:Text()
check(type(text) == "string" and #text > 500, "Bericht erstellt (" .. #text .. " Zeichen)")
for _, h in ipairs({ "== Spieler", "== Gefahrenkarte", "== Gegner in Sichtweite", "== Questlog", "== Route", "== Flugpunkte", "== Karten", "== Ruhestein", "== Gelernte Werte" }) do
    check(text:find(h, 1, true), "Abschnitt " .. h)
end
check(text:find("npc 3098", 1, true) and text:find("Paket", 1, true), "Ziel mit NPC-ID und Datenpaket-Level")
check(text:find("Karte 1411", 1, true), "Position mit Karten-ID")
check(not text:find("|c", 1, true), "keine Farbcodes im Text")
check(snap() == before, "nichts verändert (" .. before .. ")")
-- abweichendes Level erkennen
TGT.level = 9
check(LP.Measure:Text():find("ABWEICHUNG", 1, true), "abweichendes Mob-Level wird markiert")
TGT.level = 2
-- Fenster
local shown
local orig = LP.Backup.ShowText
LP.Backup.ShowText = function(_, title, hint, t) shown = t end
SlashCmdList["LEVELPILOT"]("messen")
LP.Backup.ShowText = orig
check(shown and shown:find("Messung", 1, true), "/lp messen öffnet das Fenster")
-- Fluege lernen: 3 Fluege, je 3000 Yards in 150 s (50 s je 1000 Yards)
check(LP.Calib:FlightSecs(3000) == nil, "ohne Messungen: Annahme")
for i = 1, 3 do
    P.taxi = false
    FireEvent("PLAYER_CONTROL_LOST")
    P.taxi = true
    Advance(2, 0.5)
    local inst, n, w = LP.Geo:Player()
    -- 3000 Yards nach Norden fliegen
    local _, n2 = inst, n + (i % 2 == 1 and -3000 or 3000)
    local x, y = LP.Geo:ToMap(P.map, inst, n2, w)
    local lim = x and y and x > 0 and x < 100 and y > 0 and y < 100
    if not lim then -- auf eine groessere Karte wechseln: einfach Kalimdor
        P.map = 1414 x, y = LP.Geo:ToMap(1414, inst, n2, w)
    end
    Advance(148, 1)
    P.x, P.y = x, y
    P.taxi = false
    FireEvent("PLAYER_CONTROL_GAINED")
    Advance(2, 0.5)
end
local fs = LP.Calib:FlightSecs(1000)
check(fs and math.abs(fs - 50) < 2, string.format("gelernt: %.1f s je 1000 Yards (Ziel 50)", fs or -1))
check(LP.Calib:FlightText():find("3 gemessen", 1, true), "Flüge im Statustext: " .. LP.Calib:FlightText())
-- Reise lernt nichts
local n0 = LevelPilotDB.calib.flights.n
LP.Virtual:Start("start") for _ = 1, 20 do Advance(0.05, 0.05) end
FireEvent("PLAYER_CONTROL_LOST") P.taxi = true Advance(60, 1) P.taxi = false FireEvent("PLAYER_CONTROL_GAINED") Advance(2, 0.5)
LP.Virtual:Stop() Advance(0.2, 0.05)
check(LevelPilotDB.calib.flights.n == n0, "während der virtuellen Reise wird kein Flug gemessen")
for _, m in ipairs(CHAT) do if m:find("attempt") or m:find("Fehler") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
