"""Test GoldSentinelPruefliste.lua (lupa, Nachbau der nötigen WoW-Funktionen). Aufruf: python3 -I shared/pruefliste/test_pruefliste.py"""
import sys
from pathlib import Path
from lupa.lua51 import LuaRuntime

HERE = Path(__file__).resolve().parent
SRC = (HERE.parent / "GoldSentinelPruefliste.lua").read_text(encoding="utf-8")
ok = fail = 0


def check(name, cond):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
        print("FEHLT:", name)


STUB = r"""
CHAT = {}
DEFAULT_CHAT_FRAME = { AddMessage = function(_, t) CHAT[#CHAT + 1] = t end }
NOW = 1794800000
function time() return NOW end
function date(f, t) return "16.11. 07:00" end
COMBAT = false
function InCombatLockdown() return COMBAT end
local function W()
  local w = { shown = false, scripts = {}, children = {} }
  local mt = {}
  mt.__index = function(t, k)
    if k == "Show" then return function(s) s.shown = true end end
    if k == "Hide" then return function(s) s.shown = false end end
    if k == "IsShown" then return function(s) return s.shown end end
    if k == "SetScript" then return function(s, n, f) s.scripts[n] = f end end
    if k == "SetText" then return function(s, x) s.txt = x end end
    if k == "GetText" then return function(s) return s.txt end end
    if k == "CreateFontString" then return function() return W() end end
    return function() end
  end
  return setmetatable(w, mt)
end
function CreateFrame() return W() end
UIParent = W()
DEV = true
GoldSentinelDev = { IsDev = function() return DEV end }
DB = {}
"""

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(STUB)
lua.execute(SRC)
G = lua.globals()
lua.execute("""
AUTO_R = nil
L = GoldSentinelPruefliste:Register("Test", { db = function() return DB end, version = "1.0", points = {
  { id = "P1", title = "Kaufen", since = "1.0", todo = "Klick", expect = "1 Kauf" },
  { id = "P2", title = "Auto", since = "1.0", auto = function() return AUTO_R, "gemessen" end },
  { id = "P3", title = "Kaputt", since = "1.0", auto = function() error("boom") end },
} })
""")
L = G.L
check("Liste registriert (Entwicklermodus)", G.GoldSentinelPruefliste.Get(G.GoldSentinelPruefliste, "Test") is not None)
check("Anfang 0 von 3", tuple(L.Count(L)) == (0, 3))
check("nächster offener Punkt P1", L.NextOpen(L) == "P1")
check("Hit markiert erledigt", L.Hit(L, "P1", "1 Kauf 8s50") is True and L.State(L, "P1")[0] == "auto")
check("Chat-Meldung bei Erkennung", any("P1 erledigt" in str(m) for m in G.CHAT.values()))
check("zweiter Hit ändert nichts", L.Hit(L, "P1") is False)
L.RunAuto(L)
check("auto nil -> offen", L.State(L, "P2")[0] == "offen")
check("auto mit Lua-Fehler -> fehler mit Notiz", L.State(L, "P3")[0] == "fehler" and "boom" in L.State(L, "P3")[1].n)
lua.execute("AUTO_R = true")
lua.execute("COMBAT = true")
check("im Kampf keine Prüfung", L.RunAuto(L) == 0 and L.State(L, "P2")[0] == "offen")
lua.execute("COMBAT = false")
L.RunAuto(L)
check("auto true -> erledigt", L.State(L, "P2")[0] == "auto")
check("2 von 3", tuple(L.Count(L)) == (2, 3))
check("nächster offener jetzt P3 (Fehler zählt als offen)", L.NextOpen(L) == "P3")
L.Set(L, "P3", "nok", "sieht falsch aus")
check("nicht OK bleibt offen für NextOpen", L.NextOpen(L) == "P3" and L.State(L, "P3")[0] == "nok")
check("Hit überschreibt nicht OK des Spielers nicht", L.Hit(L, "P3") is False)
L.Set(L, "P3", "ok")
check("3 von 3, nichts mehr offen", tuple(L.Count(L)) == (3, 3) and L.NextOpen(L) is None)
rep = list(L.ReportLines(L).values())
check("Bericht: Kopfzeile + 3 Zeilen", len(rep) == 4 and rep[0] == "PRÜFLISTE Test: 3 von 3 erledigt" and "P1 auto" in rep[1])
check("gespeichert in DB.pruefliste.p", G.DB.pruefliste.p.P1.s == "auto" and G.DB.pruefliste.p.P1.v == "1.0")
# neue Fassung eines Punkts -> wieder offen
lua.execute("""
L2 = GoldSentinelPruefliste:Register("Test", { db = function() return DB end, points = {
  { id = "P1", title = "Kaufen", since = "1.1" } } })
""")
check("neue since-Fassung -> wieder offen", G.L2.State(G.L2, "P1")[0] == "offen")
# Fenster: öffnet, wählt den nächsten offenen Punkt, Anweisung sichtbar
check("Open im Entwicklermodus", G.L2.Open(G.L2) is True and G.L2.sel == "P1")
txt = G.L2.frame.detail.txt
check("Anweisung sichtbar (Das tust du / Das musst du sehen)", "Das tust du" in txt and "Das musst du sehen" in txt and "Schritt 1 von 1" in txt)
G.L2.Hit(G.L2, "P1")
check("nach Erledigung: Fertig-Text mit /reload", "Alle Punkte erledigt" in G.L2.frame.detail.txt)
# angeklickter (erledigter) Punkt bleibt gewählt, bis OK/Erledigung
lua.execute("""
L4 = GoldSentinelPruefliste:Register("T4", { db = function() return DB end, points = { { id = "A", since = "1" }, { id = "B", since = "1" } } })
L4:Hit("A"); L4:Open(); L4.sel, L4.pin = "A", true; L4:Refresh()
""")
check("angeklickter erledigter Punkt bleibt gewählt", G.L4.sel == "A")
lua.execute('L4:Hit("B")')
check("nach Erledigung springt die Auswahl weiter (alles fertig -> nil)", G.L4.sel is None)
# ohne Entwicklermodus: nichts
lua.execute("DEV = false; L3 = GoldSentinelPruefliste:Register('Spieler', { db = function() return DB end, points = { { id = 'X' } } })")
L3 = G.L3
check("ohne Entwicklermodus: Open/Hit tun nichts", L3.Open(L3) is None and L3.Hit(L3, "X") is None and len(list(L3.ReportLines(L3).values())) == 0)
check("ohne Entwicklermodus nicht registriert", G.GoldSentinelPruefliste.Get(G.GoldSentinelPruefliste, "Spieler") is None)
# ältere Version überschreibt neuere nicht
lua.execute("DEV = true; GoldSentinelPruefliste.version = 9")
lua.execute(SRC)
check("neuere Version bleibt", G.GoldSentinelPruefliste.version == 9)
print(f"{ok}/{ok + fail} Prüfungen bestanden")
sys.exit(1 if fail else 0)
