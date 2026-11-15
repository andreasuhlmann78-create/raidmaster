"""Test GSWegMess 1.0 (Nachbau): Start/Stop/Mark, nur Änderungen, Zeitlimit 30 Min., geschützte Werte, fehlende APIs."""
import sys
from lupa.lua51 import LuaRuntime
src = open(__file__.replace("test_gswegmess.py", "GSWegMess.lua"), encoding="utf-8").read()
fails = checks = 0
def check(name, got, exp):
    global fails, checks
    checks += 1
    if got != exp:
        fails += 1; print("FEHLER", name, got, "erwartet", exp)
MOCK = r'''
NOW = 100; function GetTime() return NOW end
POS = {0.5, 0.5}; MAP = 1458; SUBZ = "Handelsbezirk"; IND = true; FALL = false; SPEED = 7
FR = nil
function CreateFrame() local f = {ev = {}, sc = {}}; function f:RegisterEvent(e) if e == "NEW_WMO_CHUNK" then error("unbekannt") end self.ev[e] = true end
  function f:SetScript(k, fn) self.sc[k] = fn end; FR = f; return f end
C_Map = { GetBestMapForUnit = function() return MAP end,
  GetPlayerMapPosition = function() return { GetXY = function() return POS[1], POS[2] end } end,
  GetMapInfoAtPosition = function() return { mapID = MAP } end }
function GetRealZoneText() return "Unterstadt" end
function GetSubZoneText() return SUBZ end
function GetMinimapZoneText() return SUBZ end
function IsIndoors() return IND end
function IsFalling() return FALL end
function IsSwimming() return false end
function GetUnitSpeed() return SPEED end
function date() return "15.11.2026 20:00:00" end
PRINTS = {}; function print(s) PRINTS[#PRINTS+1] = s end
SlashCmdList = {}
function UPD(dt) NOW = NOW + dt; FR.sc.OnUpdate(FR, dt) end
'''
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCK); L.execute(src)
check("Befehl angemeldet", L.eval("SLASH_GSWEGMESS1"), "/wegmess")
check("NEW_WMO_CHUNK fehlt -> kein Fehler, andere angemeldet", L.eval("FR.ev.ZONE_CHANGED_INDOORS"), True)
L.execute('SlashCmdList.GSWEGMESS("start")')
check("läuft", L.eval("GSWegMess.Running()"), True)
n0 = L.eval("#GSWegMessDB.lines")
L.execute("SPEED = 0; for i = 1, 20 do UPD(0.2) end")
check("stehen ohne Änderung -> keine neuen Zeilen", L.eval("#GSWegMessDB.lines"), n0)
L.execute('SUBZ = "Magieviertel"; UPD(0.2)')
check("Unterzone wechselt -> eine Zeile", L.eval("#GSWegMessDB.lines"), n0 + 1)
check("Zeile enthält Unterzone", "Magieviertel" in L.eval("GSWegMessDB.lines[#GSWegMessDB.lines]"), True)
L.execute("SPEED = 7; for i = 1, 10 do UPD(0.2) end")
check("in Bewegung: etwa 1 Zeile je Sekunde", L.eval("#GSWegMessDB.lines") - (n0 + 1), 2)
L.execute('FR.sc.OnEvent(FR, "ZONE_CHANGED_INDOORS")')
check("Ereignis -> Zeile mit Namen", L.eval("GSWegMessDB.lines[#GSWegMessDB.lines]").endswith("ZONE_CHANGED_INDOORS"), True)
L.execute('SlashCmdList.GSWEGMESS("mark Aufzug unten")')
check("Notiz", L.eval("GSWegMessDB.lines[#GSWegMessDB.lines]").endswith("MARK Aufzug unten"), True)
L.execute('C_Map.GetBestMapForUnit = function() error("geschuetzt") end; UPD(0.2)')
check("Fehler in der API -> weiter, kein Absturz", L.eval("GSWegMess.Running()"), True)
L.execute("C_Map.GetBestMapForUnit = function() return MAP end")
L.execute("NOW = NOW + 31*60; UPD(0.2)")
check("Zeitlimit 30 Min. beendet die Messung", L.eval("GSWegMess.Running()"), False)
check("Stopp-Zeile", "STOP Zeitlimit" in L.eval("GSWegMessDB.lines[#GSWegMessDB.lines]"), True)
L.execute('SlashCmdList.GSWEGMESS("mark x")')
check("Notiz ohne Messung -> Hinweis", "Erst /wegmess start" in L.eval("PRINTS[#PRINTS]"), True)
L.execute('GSWegMess.Start(); for i = 1, 9000 do SUBZ = "Z" .. i; UPD(0.2) end')
check("höchstens 8000 Zeilen", L.eval("#GSWegMessDB.lines"), 8000)
L.execute('SlashCmdList.GSWEGMESS("stop")')
check("Stopp per Befehl", L.eval("GSWegMess.Running()"), False)
print(f"{checks - fails}/{checks} Prüfungen bestanden"); sys.exit(1 if fails else 0)
