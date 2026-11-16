"""Test TSMess 1.1 (Nachbau): Start/Stop, nur im Kampf je Sekunde, geschützte Werte -> G, Fehler -> F, keine Namen,
Zeitlimit 60 Min., höchstens 6000 Zeilen. python3 -I test_tsmess.py"""
import sys
from lupa.lua51 import LuaRuntime
src = open(__file__.replace("test_tsmess.py", "TSMess.lua"), encoding="utf-8").read()
fails = checks = 0
def check(name, got, exp):
    global fails, checks
    checks += 1
    if got != exp:
        fails += 1
        print("FEHLER", name, repr(got), "erwartet", repr(exp))
MOCK = r'''
NOW = 100; function GetTime() return NOW end
COMBAT = false; TARGET = true; SECRET = false
SECRETV = setmetatable({}, {__tostring = function() error("geschützt") end})
function issecretvalue(v) return v == SECRETV end
EXIST = { player = true, party1 = true }
RAID = false; function IsInRaid() return RAID end
NAMES = { player = "Anna", party1 = "Grimbar" }
function UnitName(u) return NAMES[u] end
function UnitExists(u) if u == "target" then return TARGET end return EXIST[u] == true end
function UnitAffectingCombat() return COMBAT end
function UnitDetailedThreatSituation(u, t)
  if SECRET then return u == "party1", SECRETV, SECRETV, SECRETV, SECRETV end
  if u == "party1" then return true, 3, 100, 100, 14000 end
  return false, 1, 85, 93.5, 12000.25
end
function UnitThreatSituation(u, t) if u == "pet" then error("x") end; if SECRET and t then return SECRETV end; return 1 end
function GetBuildInfo() return "1.15.9", "1", "Nov", 11508 end
function date() return "16.11.2026 05:30:00" end
FR = nil
function CreateFrame() local f = {ev = {}, sc = {}}; function f:RegisterEvent(e) self.ev[e] = true end
  function f:SetScript(k, fn) self.sc[k] = fn end; FR = f; return f end
PRINTS = {}; function print(s) PRINTS[#PRINTS+1] = s end
SlashCmdList = {}
function UPD(dt) NOW = NOW + dt; FR.sc.OnUpdate(FR, dt) end
function EV(e) FR.sc.OnEvent(FR, e) end
function LAST() return TSMessDB.lines[#TSMessDB.lines] end
'''
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCK); L.execute(src)
check("Befehl angemeldet", L.eval("SLASH_TSMESS1"), "/tsmess")
check("Ereignisse angemeldet", L.eval("FR.ev.PLAYER_REGEN_DISABLED and FR.ev.PLAYER_REGEN_ENABLED and FR.ev.PLAYER_TARGET_CHANGED"), True)
L.execute('SlashCmdList.TSMESS("start")')
check("läuft", L.eval("TSMess.Running()"), True)
check("Kopfzeile mit Interface", "Interface 11508" in L.eval("TSMessDB.lines[1]"), True)
n0 = L.eval("#TSMessDB.lines")
L.execute("for i = 1, 10 do UPD(0.5) end")
check("ausserhalb des Kampfs keine Messung", L.eval("#TSMessDB.lines"), n0)
L.execute('COMBAT = true; EV("PLAYER_REGEN_DISABLED"); UPD(0.1)')
check("Kampfbeginn sofort gemessen (2 Einheiten)", L.eval("#TSMessDB.lines"), n0 + 3)
check("Zeile Spieler lesbar", L.eval("TSMessDB.lines[#TSMessDB.lines - 1]").split("|", 1)[1], "U|player|0|1.00|85.00|93.50|12000.25|1.00|1.00|")
L.execute("for i = 1, 4 do UPD(0.5) end")
check("je Sekunde eine Messung", L.eval("#TSMessDB.lines"), n0 + 3 + 4)
L.execute('SECRET = true; UPD(1.0)')
check("geschützt -> G", L.eval("LAST()").split("|", 1)[1], "U|party1|1|G|G|G|G|G|1.00|")
L.execute('EXIST.pet = true; UPD(1.0); EXIST.pet = nil')
pet = [L.eval("TSMessDB.lines[%d]" % i) for i in range(1, L.eval("#TSMessDB.lines") + 1) if "|pet|" in L.eval("TSMessDB.lines[%d]" % i)]
check("API-Fehler -> F, kein Absturz", pet[-1].split("|")[8:10] if pet else None, ["F", "F"])
alltext = "\n".join(L.eval("TSMessDB.lines[%d]" % i) for i in range(1, L.eval("#TSMessDB.lines") + 1))
check("keine Namen in den Zeilen", ("Anna" in alltext) or ("Grimbar" in alltext), False)
L.execute('TARGET = false; UPD(1.0)')
check("ohne Ziel -> Zeile Z", L.eval("LAST()").split("|", 1)[1], "Z|-|kein Ziel")
L.execute('TARGET = true; EV("PLAYER_TARGET_CHANGED")')
check("Zielwechsel im Kampf vermerkt", L.eval("LAST()").endswith("Zielwechsel"), True)
L.execute('COMBAT = false; EV("PLAYER_REGEN_ENABLED")')
check("Kampfende", L.eval("LAST()").endswith("KAMPF Ende"), True)
n1 = L.eval("#TSMessDB.lines")
L.execute("UPD(2.0)")
check("nach dem Kampf keine Messung", L.eval("#TSMessDB.lines"), n1)
L.execute("NOW = NOW + 61*60; UPD(0.1)")
check("Zeitlimit 60 Min. beendet die Messung", L.eval("TSMess.Running()"), False)
check("Stopp-Zeile", "STOP Zeitlimit" in L.eval("LAST()"), True)
L.execute('TSMess.Start(); COMBAT = true; EV("PLAYER_REGEN_DISABLED"); for i = 1, 3100 do UPD(1.0) end')
check("höchstens 6000 Zeilen", L.eval("#TSMessDB.lines"), 6000)
L.execute('SlashCmdList.TSMESS("stop")')
check("Stopp per Befehl", L.eval("TSMess.Running()"), False)
# (a) Reihenfolge in M.Enc: zuerst geschützt, dann nil (in Standard-Lua kann "== nil" nicht werfen – darum Prüfung der Reihenfolge
#     im Quelltext und: issecretvalue wird für jeden Wert zuerst gefragt)
enc = src[src.index("function M.Enc(v)"):]
enc = enc[:enc.index("\nend")]
check("Enc: IsSecret vor dem nil-Vergleich", enc.index("IsSecret(v)") < enc.index("v == nil"), True)
L.execute('ASKED = {}; local orig = issecretvalue; issecretvalue = function(v) ASKED[#ASKED+1] = (v == nil) and "nil" or "x"; return orig(v) end')
check("Enc(nil) fragt zuerst issecretvalue", (L.eval("TSMess.Enc(nil)"), L.eval("ASKED[1]")), ("-", "nil"))
check("Enc(geschützt) = G", L.eval("TSMess.Enc(SECRETV)"), "G")
# (b) Schlachtzug: raid1–40, nur wer tankt
L.execute('TSMessDB.lines = {}; SECRET = false; RAID = true; EXIST = { player = true, party1 = true }')
L.execute('for i = 1, 40 do EXIST["raid" .. i] = true end')
L.execute('UnitDetailedThreatSituation = function(u) if u == "raid7" then return true, 3, 100, 100, 9000 end; if u == "raid9" then return SECRETV, SECRETV, SECRETV, SECRETV, SECRETV end; return false, 1, 50, 55, 4000 end')
L.execute('TSMess.Start(); COMBAT = true; EV("PLAYER_REGEN_DISABLED"); UPD(0.1)')
units = [L.eval("TSMessDB.lines[%d]" % i).split("|")[2] for i in range(1, L.eval("#TSMessDB.lines") + 1) if L.eval("TSMessDB.lines[%d]" % i).split("|")[1] == "U"]
check("Schlachtzug: Spieler + nur die Tanks (raid7 lesbar, raid9 geschützt), kein party1", units, ["player", "raid7", "raid9"])
L.execute('SlashCmdList.TSMESS("stop")')
L.execute('SlashCmdList.TSMESS("")')
check("Stand-Ausgabe", "steht" in L.eval("PRINTS[#PRINTS]"), True)
print("TSMess: %d Prüfungen, %d FEHLER" % (checks, fails))
sys.exit(1 if fails else 0)
