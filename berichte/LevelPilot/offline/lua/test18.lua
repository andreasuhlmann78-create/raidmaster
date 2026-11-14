-- Test: Fehler-Protokoll (3.4.1)
-- Aufruf: PACKDIR=... FOREVER=1 LVL=6 MAP=1411 PX=43.3 PY=68.5 lua51 test18.lua <Addon> 0 Orc WARRIOR Horde
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
-- vor dem Laden: Fehlerbehandlung und Zeitmessung des Spiels
ERRORS_SEEN = {}
local handler = function(msg) ERRORS_SEEN[#ERRORS_SEEN + 1] = msg end
function geterrorhandler() return handler end
function seterrorhandler(fn) handler = fn end
DPS_EXTRA = 0
function debugprofilestop() return os.clock() * 1000 + DPS_EXTRA end
function debugstack() return "Interface/AddOns/LevelPilot/Test.lua:1: in function <Test>" end
ZONE = nil
function GetRealZoneText() return ZONE or ("Zone" .. tostring(P.map)) end
function GetSubZoneText() return "" end
function GetBuildInfo() return "1.16.1", "99999", "Okt 2026", 11601 end
MEM = 1500
function UpdateAddOnMemoryUsage() end
function GetAddOnMemoryUsage() MEM = MEM + 10 return MEM end
dofile(dir .. "/mock2.lua")
local LP = NS
local Pr = LP.Protocol
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local function count(kind) local n = 0 for _, e in ipairs(Pr:Entries()) do if e.k == kind then n = n + (e.n or 1) end end return n end
MOVING = false
function IsPlayerMoving() return MOVING end
local function walk(secs)       -- aktiv: hin und her laufen (Bewegungstasten gedrueckt)
    MOVING = true
    for i = 1, secs do P.x = P.x + (i % 2 == 0 and 0.15 or -0.15) NOW = NOW + 1 Advance(0, 1) Advance(1) end
    MOVING = false
end

check(Pr ~= nil, "Modul geladen")
check(Pr.session and Pr.session.l == P.level, "Sitzung begonnen")
check(Pr:Count() == 0, "frisch: keine Einträge (" .. Pr:Count() .. ")")

-- 1) Zone richtig: nichts
walk(30)

check(count("zone") == 0, "Zone stimmt: kein Eintrag")
-- 2) Zone falsch (wie Durotar/Brachland)
ZONE = "Durotar"
walk(20)
check(count("zone") == 1, "falsche Zone notiert")
local ze for _, e in ipairs(Pr:Entries()) do if e.k == "zone" then ze = e end end
check(ze and ze.msg:find("Durotar") and ze.c.m == 1411 and ze.c.x, "mit Karte, Position und Spiel-Zone: " .. tostring(ze and ze.msg))
walk(30)
check(count("zone") == 1, "nur einmal pro Fehlbild")
ZONE = nil
-- 3) im Flug: keine Pruefung
P.taxi = true ZONE = "Brachland" walk(20) P.taxi = false ZONE = nil
check(count("zone") == 1, "im Flug nicht geprüft")
-- 4) Position unbekannt
local saveMap = P.map
P.map = nil
walk(40)
P.map = saveMap
check(count("nopos") == 1, "Position unbekannt notiert")

-- 5) Fokus in anderer Zone, obwohl hier Aufgaben warten
local origReplan = LP.Planner.Replan
LP.Planner.focus = 1413
LP.Planner.lastTasks = { { t = "ACCEPT", map = 1411 }, { t = "COMPLETE", map = 1411 }, { t = "ACCEPT", map = 1413 } }
local saveRP = LP.Planner._protoWrapped
-- 3.12.8: der Waechter plant zuerst selbst neu; hilft das nicht (Fokus bleibt falsch), wird einmal gemeldet
LP.Planner.Replan = function() LP.Planner.focus = 1413 end
-- 3.12.22: gemeldet wird nur, wenn auch der aktuelle Schritt woanders liegt
local origCur = LP.Engine.Current
LP.Engine.Current = function() return { key = "TEST", t = "ACCEPT", map = 1413 } end
walk(80)
LP.Engine.Current = origCur
check(count("focus") >= 1, "Fokus-Problem notiert")
for _, e in ipairs(Pr:Entries()) do if e.k == "focus" then print("       " .. e.msg) end end
LP.Planner.Replan = origReplan

-- 6) Navigation: kein Weg / kommt nicht naeher
local origRecalc = LP.Nav.Recalc
LP.Nav.Recalc = function() end
local pi, pn, pw = LP.Geo:Player()
LP.Nav.target = { inst = pi, n = pn + 800, w = pw, key = "T:test", label = "Testziel" }
LP.Nav.hasPath = false
LP.Nav.pathError = "Graph.lua:1: Testfehler"
walk(30)
check(count("nopath") == 1, "kein Weg notiert")
for _, e in ipairs(Pr:Entries()) do if e.k == "nopath" then check(e.x and e.x:find("Testfehler"), "mit Fehlertext der Wegsuche: " .. tostring(e.x)) end end
LP.Nav.hasPath, LP.Nav.pathKind = true, "terrain"
walk(260)
check(count("stuck") == 1, "kommt nicht näher: notiert")
for _, e in ipairs(Pr:Entries()) do if e.k == "stuck" then print("       " .. e.msg) end end
-- naeherkommen: kein neuer Eintrag fuer ein anderes Ziel
LP.Nav.target = { inst = pi, n = pn + 300, w = pw, key = "T:zwei", label = "Zweites" }
for i = 1, 100 do P.y = P.y - 0.1 NOW = NOW + 1 Advance(1) end
check(count("stuck") == 1, "beim Näherkommen kein Eintrag")
-- AFK: zaehlt nicht
LP.Nav.target = { inst = pi, n = pn + 900, w = pw, key = "T:afk", label = "AFK-Ziel" }
for _ = 1, 400 do NOW = NOW + 1 Advance(1) end
check(count("stuck") == 1, "AFK (keine Bewegung) gilt nicht als festgesteckt")
-- Stillstehen, aber aktiv (Bericht 3.9.0: Tester tippt Befehle, Charakter steht) - kein Eintrag
LP.Nav.target = { inst = pi, n = pn + 1100, w = pw, key = "T:steht", label = "Ratchet-Ziel" }
for _ = 1, 400 do NOW = NOW + 1 Advance(0, 1) Advance(1) end
check(count("stuck") == 1, "Stillstehen beim Testen (aktiv, ohne Bewegung) gilt nicht als festgesteckt")
LP.Nav.target = nil
LP.Nav.Recalc = origRecalc

-- 7) Schritt dauert sehr lange
local origCurrent = LP.Engine.Current
LP.Engine.Current = function() return { t = "COMPLETE", key = "C:999", q = "Ewige Quest", id = 999 } end
walk(1520)
check(count("step") == 1, "langer Schritt notiert")
LP.Engine.Current = origCurrent

-- 8) Fehler
LP:Error("Testmodul", "boom")
LP:Error("Testmodul", "boom")
check(count("error") >= 1, "eigene Fehlermeldung notiert")
local er for _, e in ipairs(Pr:Entries()) do if e.k == "error" and e.msg:find("boom") then er = e end end
check(er and er.x and er.x:find("Test.lua"), "mit Aufrufliste")
geterrorhandler()("Interface/AddOns/LevelPilot/Pins.lua:42: attempt to index nil")
geterrorhandler()("Interface/AddOns/OtherAddon/x.lua:1: fremd")
check(#ERRORS_SEEN == 2, "Fehler gehen weiter an die normale Anzeige")
local own, other = false, false
for _, e in ipairs(Pr:Entries()) do
    if e.msg:find("Pins.lua:42") then own = true end
    if e.msg:find("OtherAddon") then other = true end
end
check(own and not other, "nur LevelPilot-Fehler werden notiert")
FireEvent("ADDON_ACTION_BLOCKED", "LevelPilot", "UseAction()")
FireEvent("ADDON_ACTION_BLOCKED", "Fremd", "Something()")
check(count("blocked") == 1, "blockierte Aktion notiert")

-- 9) Tod
FireEvent("PLAYER_DEAD")
check(count("death") == 1, "Tod notiert")

-- 10) langsame Planung
local realDps = debugprofilestop
local calls = 0
debugprofilestop = function() calls = calls + 1 return realDps() + calls * 900 end
LP.Planner:Replan()
debugprofilestop = realDps
check(count("slow") == 1, "langsame Planung notiert")

-- 11) Text zum Kopieren
local txt = Pr:Text()
check(txt:find("LevelPilot%-Protokoll v" .. LP.version:gsub("%.", "%%.")), "Kopfzeile")
check(txt:find("== Diagnose") and txt:find("Position"), "Diagnose enthalten")
check(txt:find("%[.-%] ZONE") and txt:find("FEST") and txt:find("KEINWEG") and txt:find("SCHRITT") and txt:find("FEHLER") and txt:find("TOD"), "alle Arten im Text")
check(not txt:find("|c%x%x%x%x%x%x%x%x"), "ohne Farbcodes")
check(not txt:find(UnitName("player"), 1, true), "ohne Charakternamen")
check(txt:find("Sitzungen: 1"), "Sitzungen im Kopf")
print("------ Auszug ------")
local nl = 0 for line in txt:gmatch("[^\n]+") do nl = nl + 1 if nl <= 40 then print("   " .. line) end end
print("------ (" .. nl .. " Zeilen) ------")

-- 12) Anzeigen, neu-Zaehler
local n0 = Pr:Count(true)
check(n0 >= 8, "neue Auffälligkeiten: " .. n0)
NOW = NOW + 2
SlashCmdList["LEVELPILOT"]("protokoll")
check(Pr:Count(true) == 0, "nach dem Anzeigen nichts mehr neu")
check(LevelPilotBackupFrame and LevelPilotBackupFrame:IsShown(), "Fenster zum Kopieren offen")

-- 13) abschaltbar, Obergrenze, leeren
LP.db.protocol = false
LP:Error("Aus", "nicht notieren")
local found = false for _, e in ipairs(Pr:Entries()) do if e.msg:find("nicht notieren") then found = true end end
check(not found, "abgeschaltet: nichts notiert")
LP.db.protocol = true
for i = 1, 350 do Pr:Add("error", "Massentest " .. i) end
check(#Pr:Entries() == 300, "höchstens 300 Einträge")
SlashCmdList["LEVELPILOT"]("protokoll leeren")
check(#Pr:Entries() == 0, "geleert")

-- 14) Ausloggen und Wiedereinloggen mit Pause
FireEvent("PLAYER_LOGOUT")
check(LP.char.lastLogout and Pr.session.e, "Ausloggen gespeichert")
NOW = NOW + 1200
LP.Protocol.session = nil
local s = LevelPilotDB.protocolLog
local before = #s.sessions
-- Neustart der Sitzung simulieren
for _, m in ipairs(LP.modules) do if m.name == "Protocol" then end end
local lastOut = LP.char.lastLogout
local _, class = UnitClass("player")
-- StartSession ist lokal: ueber Init erneut aufrufen
Pr:Init()
check(#s.sessions == before + 1 and s.sessions[#s.sessions].gap and s.sessions[#s.sessions].gap >= 1200, "neue Sitzung mit Pause " .. tostring(s.sessions[#s.sessions].gap) .. " s")
local t2 = Pr:Text()
check(t2:find("Pause 20min"), "Pause im Text")

-- Zentrale
LP.Center:Toggle("data") LP.Center:Select("data") LP.Center:Refresh()
LP.Center:Toggle("extras") LP.Center:Select("extras") LP.Center:Refresh()
check(true, "Zentrale ohne Fehler")
for _, m in ipairs(CHAT) do if m:find("attempt") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
