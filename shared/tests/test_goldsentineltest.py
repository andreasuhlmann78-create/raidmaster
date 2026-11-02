"""Tests für shared/GoldSentinelTest.lua (läuft mit: python3 -I shared/tests/test_goldsentineltest.py).
Prüft Testlauf, Bericht (JSON, maschinenlesbar), Speichern in den SavedVariables, geschützte Werte, Fehler im Spiel
(Fehler-Handler, BugGrabber, geblockte Aktionen, Ausloggen), "neueste Version gewinnt" und die Auslesbarkeit durch
den Uploader (GSTEST1-Strings im Format der WoW-SavedVariables)."""
import json
import re
import sys
from pathlib import Path

from lupa.lua51 import LuaRuntime

HERE = Path(__file__).resolve().parent
SRC = (HERE.parent / "GoldSentinelTest.lua").read_text(encoding="utf-8")
GAME = (HERE.parent / "GoldSentinelGame.lua").read_text(encoding="utf-8")
fails = 0
checks = 0

STUB = r"""
SlashCmdList = {}; DEFAULT_CHAT_FRAME = {AddMessage=function() end}
function GetLocale() return 'deDE' end
function GetBuildInfo() return '1.60.1','70707','x',16001 end
function UnitClass() return 'Krieger','WARRIOR' end
function UnitLevel() return 23 end
function time() return 1793750400 end
function date(f, t) return '05.11.2026 00:00' end
local clock = 0
function debugprofilestop() clock = clock + 1.5 return clock end
function debugstack() return 'Interface/AddOns/Test/Core.lua:1: in function' end
local handler = function(m) LASTPREV = m end
function geterrorhandler() return handler end
function seterrorhandler(f) handler = f end
function FireError(m) return handler(m) end
FRAMES = {}
function CreateFrame()
  local f = {events = {}}
  function f:RegisterEvent(e) self.events[e] = true end
  function f:SetScript(_, fn) self.onevent = fn end
  FRAMES[#FRAMES + 1] = f
  return f
end
function Fire(ev, ...) for _, f in ipairs(FRAMES) do if f.events[ev] and f.onevent then f.onevent(f, ev, ...) end end end
local SECRET = setmetatable({}, {__tostring=function() error('secret!') end, __eq=function() error('secret!') end,
  __lt=function() error('secret!') end, __concat=function() error('secret!') end, __index=function() error('secret!') end,
  __len=function() error('secret!') end})
S = SECRET
function issecretvalue(v) return rawequal(v, SECRET) end
"""


def new_lua(extra=""):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUB)
    lua.execute(GAME)
    lua.execute(extra)
    lua.execute(SRC)
    return lua


def check(label, got, want):
    global fails, checks
    checks += 1
    ok = got == want
    if not ok:
        fails += 1
    if not ok or "-v" in sys.argv:
        print(f"{'OK ' if ok else 'FEHLER'} [{label}] = {got!r}" + ("" if ok else f" (erwartet {want!r})"))


def lua_to_py(v):
    if hasattr(v, "items"):
        d = dict(v.items())
        if d and all(isinstance(k, int) for k in d):
            return [lua_to_py(d[i]) for i in sorted(d)]
        return {k: lua_to_py(x) for k, x in d.items()}
    return v


def reports(lua, db="DB"):
    raw = lua_to_py(lua.eval(f"{db}.gsTest and {db}.gsTest.reports or {{}}")) or []
    if isinstance(raw, dict):
        raw = []
    out = []
    for s in raw:
        assert s.startswith("GSTEST1"), s[:20]
        out.append(json.loads(s[len("GSTEST1"):]))
    return out


# 1. Testlauf mit allen Arten von Ergebnissen
lua = new_lua()
text = lua.eval(r"""(function()
  DB = {}
  local T = GoldSentinelTest.Begin('TestAddon', '1.2.3', DB)
  T:Check('T01', 'A', 'gut', function() return true, 'ja' end)
  T:Check('T02', 'A', 'ohne Rückgabe', function() end)
  T:Check('T03', 'B', 'falsch', function() return false, 'ist 1', 'soll 2' end)
  T:Check('T04', 'B', 'Lua-Fehler', function() local x = nil; return x.y end)
  T:Check('T05', 'C', 'geschützt', function() return false, S, 'lesbar' end)
  T:Skip('T06', 'D', 'alter Client', 'nur Era')
  T:Client('T07', 'C', 'Händler', '/dump GetMerchantItemCostInfo')
  local text = T:Finish({ sandbox = 'OK' })
  return text
end)()""")
r = reports(lua)
check("ein Bericht gespeichert", len(r), 1)
rep = r[0]
check("Art", rep["kind"], "test")
check("Addon/Version", (rep["addon"], rep["version"]), ("TestAddon", "1.2.3"))
check("Zählung", rep["counts"], {"ok": 2, "fehler": 3, "uebersprungen": 1, "client": 1})
check("Ergebnisse", len(rep["results"]), 7)
st = {e["id"]: e for e in rep["results"]}
check("T03 Erwartung", (st["T03"]["ergebnis"], st["T03"]["erwartet"]), ("ist 1", "soll 2"))
check("T04 Lua-Meldung", "attempt to index" in st["T04"].get("lua", ""), True)
check("T05 geschützt nie gelesen", st["T05"]["ergebnis"], "<geschützt>")
check("Umgebung Interface", rep["env"]["interface"], 16001)
check("Umgebung Flavor", rep["env"]["flavor"], "forever")
check("Umgebung Klasse/Level", (rep["env"]["class"], rep["env"]["level"]), ("WARRIOR", 23))
check("Umgebung GoldSentinelGame", rep["env"]["gsgame"], 2)
check("Sandbox", rep["sandbox"], "OK")
check("keine Namen im Bericht", "Krieger" in json.dumps(rep, ensure_ascii=False), False)
check("Text: Zählung", "OK 2 · FEHLER 3" in text, True)
check("Text: nur Nicht-OK gelistet", ("T01" in text, "T03" in text), (False, True))
check("id eindeutig", rep["id"].startswith("TestAddon-1793750400-"), True)

# 2. höchstens 10 Berichte, älteste fallen weg
lua.execute("for i = 1, 12 do local T = GoldSentinelTest.Begin('TestAddon', '1.2.'..i, DB); T:Check('T01','A','x',function() end); T:Finish() end")
r = reports(lua)
check("max 10 Berichte", len(r), 10)
check("neuester zuletzt", r[-1]["version"], "1.2.12")
check("ids verschieden", len({x["id"] for x in r}), 10)

# 3. Fehler im Spiel: eigener Handler, fremde Addons, Weitergabe an den alten Handler
lua = new_lua()
lua.execute("DB = {}; GoldSentinelTest.TrackErrors('TestAddon', '1.0', DB); GoldSentinelTest.TrackErrors('Other-Addon', '2.0', {})")
lua.execute("FireError('Interface/AddOns/TestAddon/Core.lua:12: attempt to call nil')")
lua.execute("FireError('Interface/AddOns/TestAddon/Core.lua:12: attempt to call nil')")
lua.execute("FireError('Interface\\\\AddOns\\\\TestAddon_Data\\\\x.lua:3: boom')")
lua.execute("FireError('Interface/AddOns/Fremd/x.lua:1: nicht meins')")
lua.execute("FireError('Interface/AddOns/Other-Addon/x.lua:1: Bindestrich')")
check("Weitergabe an alten Handler", lua.eval("LASTPREV"), "Interface/AddOns/Other-Addon/x.lua:1: Bindestrich")
errs = lua_to_py(lua.eval("DB.gsTest.errors"))
check("2 verschiedene Fehler", len(errs), 2)
e = errs["Lua|Interface/AddOns/TestAddon/Core.lua:12: attempt to call nil"]
check("gezählt", e["count"], 2)
check("Stack dabei", "Core.lua" in e.get("stack", ""), True)
check("Bindestrich-Addon erkannt", len(lua_to_py(lua.eval("GoldSentinelTest.registry['Other-Addon'].db.gsTest.errors")) or {}), 1)
lua.execute("GoldSentinelTest.Error('TestAddon', 'Scan', S)")
check("geschützte Meldung", lua.eval("DB.gsTest.errors['Scan|<geschützt>'].count"), 1)
lua.execute("Fire('ADDON_ACTION_BLOCKED', 'TestAddon', 'CastSpellByName()')")
lua.execute("Fire('ADDON_ACTION_BLOCKED', 'Fremd', 'X()')")
check("geblockte Aktion", lua.eval("DB.gsTest.errors['ADDON_ACTION_BLOCKED|CastSpellByName()'].count"), 1)
lua.execute("Fire('PLAYER_LOGOUT')")
r = reports(lua)
check("beim Ausloggen ein Fehler-Bericht", [x["kind"] for x in r], ["fehler"])
check("Fehler im Bericht", len(r[0]["errors"]), 4)
check("danach geleert", lua.eval("next(DB.gsTest.errors) == nil"), True)
lua.execute("Fire('PLAYER_LOGOUT')")
check("ohne neue Fehler kein weiterer Bericht", len(reports(lua)), 1)
check("nur ein Frame", lua.eval("#FRAMES"), 1)

# 4. Testlauf schickt offene Fehler mit
lua.execute("GoldSentinelTest.Error('TestAddon', 'UI', 'kaputt'); local T = GoldSentinelTest.Begin('TestAddon','1.0',DB); T:Finish()")
r = reports(lua)
check("Testbericht enthält Spielfehler", (r[-1]["kind"], len(r[-1]["errors"])), ("test", 1))

# 5. BugGrabber übernimmt den Handler
lua = new_lua("BugGrabber = { RegisterCallback = function(obj, ev, fn) BG_FN = fn end }; function seterrorhandler() end")
lua.execute("DB = {}; GoldSentinelTest.TrackErrors('TestAddon', '1.0', DB)")
lua.execute("BG_FN('BugGrabber_BugGrabbed', { message = 'Interface/AddOns/TestAddon/a.lua:1: x', stack = 'st' })")
check("BugGrabber-Fehler gezählt", lua.eval("DB.gsTest.errors['Lua|Interface/AddOns/TestAddon/a.lua:1: x'].count"), 1)

# 6. neueste Version gewinnt, Register bleibt
lua = new_lua("GoldSentinelTest = { version = 5, marker = 'neu' }")
check("neuere bleibt", lua.eval("GoldSentinelTest.marker"), "neu")
lua = new_lua("GoldSentinelTest = { version = 0, registry = { Alt = { version = '1', db = {} } } }")
check("ältere ersetzt", lua.eval("GoldSentinelTest.version"), 1)
check("Register übernommen", lua.eval("GoldSentinelTest.registry.Alt.version"), "1")

# 7. ohne SavedVariables, ohne GoldSentinelGame, alter Client
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute("function GetBuildInfo() return '1.15.9','1','x',11509 end")
lua.execute(SRC)
text = lua.eval("(function() local T = GoldSentinelTest.Begin('X','1',nil); T:Check('T01','A','x',function() end); local t = T:Finish(); return t end)()")
check("ohne db: Hinweis statt Fehler", "nicht gespeichert" in text, True)
check("ohne GoldSentinelGame", lua.eval("GoldSentinelTest.IsSecret(1)"), False)

# 8. Uploader-Sicht: so schreibt WoW die SavedVariables – String finden und zurückwandeln
lua = new_lua()
lua.execute(r"""DB = {}; local T = GoldSentinelTest.Begin('TestAddon','1.0',DB)
T:Check('T01','A','Zeichen "x" \\ und'..string.char(10)..'Zeile', function() return false, 'ä ö ü – €', '%s %d' end); T:Finish()""")
raw = lua.eval("DB.gsTest.reports[1]")
# WoW-Serialisierung: "..." mit \" \\ \n
saved = '["reports"] = {\n"' + raw.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '", -- [1]\n}'
m = re.search(r'"(GSTEST1(?:[^"\\]|\\.)*)"', saved)
back = re.sub(r'\\(.)', lambda x: {"n": "\n", "\\": "\\", '"': '"'}.get(x.group(1), x.group(1)), m.group(1))
check("Uploader findet den Bericht", back == raw, True)
rep = json.loads(back[len("GSTEST1"):])
check("Sonderzeichen unverändert", (rep["results"][0]["name"], rep["results"][0]["ergebnis"]),
      ('Zeichen "x" \\ und\nZeile', "ä ö ü – €"))

print(f"GoldSentinelTest-Tests: {'bestanden' if fails == 0 else 'FEHLGESCHLAGEN'} ({checks - fails}/{checks})")
sys.exit(1 if fails else 0)
