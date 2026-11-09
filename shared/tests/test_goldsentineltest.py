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
  function f:SetScript(k, fn) if k == 'OnEvent' then self.onevent = fn else self[k] = fn end end
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
check("Umgebung GoldSentinelGame", rep["env"]["gsgame"], 3)
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
check("ältere ersetzt", lua.eval("GoldSentinelTest.version"), 2)
check("Register übernommen", lua.eval("GoldSentinelTest.registry.Alt.version"), "1")

# 7. ohne SavedVariables, ohne GoldSentinelGame, alter Client
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute("function GetBuildInfo() return '1.15.9','1','x',11509 end")
lua.execute(SRC)
text = lua.eval("(function() local T = GoldSentinelTest.Begin('X','1',nil); T:Check('T01','A','x',function() end); local t = T:Finish(); return t end)()")
check("ohne db: Hinweis statt Fehler", "nicht gespeichert" in text, True)
check("ohne GoldSentinelGame", lua.eval("GoldSentinelTest.IsSecret(1)"), False)
check("ohne GoldSentinelGame: Zählzeile da", "OK 1 · FEHLER 0" in text, True)
check("Sprache im Text", "Sprache" in text, True)

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


# 7. Berichte anderer Spieler über GoldSentinelSync 2 (Sammler)
SYNC = (HERE.parent / "GoldSentinelSync.lua").read_text(encoding="utf-8")


def share_client(name):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUB)
    lua.execute(GAME)
    lua.execute(f"""
NOWT = 100
function GetTime() return NOWT end
function UnitName() return "{name}" end
function IsInGuild() return true end
function IsInRaid() return false end
function IsInGroup() return false end
function InCombatLockdown() return false end
OUT = {{}}
CHAT = {{}}
DEFAULT_CHAT_FRAME = {{ AddMessage = function(_, m) CHAT[#CHAT + 1] = m end }}
C_ChatInfo = {{ SendAddonMessage = function(p, m, d, t) OUT[#OUT + 1] = {{ p, m, d, t }}; return true end,
               RegisterAddonMessagePrefix = function() return true end }}
""")
    lua.execute(SYNC)
    lua.execute(SRC)
    lua.execute("DB = {}; GoldSentinelTest.TrackErrors('TestAddon', '1.0', DB)")
    return lua


def flush_out(lua):
    lua.execute("for i = 1, 500 do if not GoldSentinelSync.Pump(true) then break end end")
    out = lua_to_py(lua.eval("OUT")) or []
    lua.execute("OUT = {}")
    return [tuple(list(o) + [None] * (4 - len(o))) for o in out]


def route(src, src_name, others):
    """Gilde: an alle; Flüstern: an das Ziel. others = {Name: lua}"""
    for p, m, d, tgt in flush_out(src):
        for n, l in others.items():
            if d == "GUILD" or (d == "WHISPER" and tgt == n):
                l.globals().Fire("CHAT_MSG_ADDON", p, m, d, src_name)


K, P = share_client("Kai Sammler"), share_client("Pia Spielerin")
check("Teilen: Endpunkt mit Sync 2", P.eval("GoldSentinelTest.Endpoint() ~= nil"), True)
K.execute("SlashCmdList.GOLDSENTINELTEST('sammler an')")
route(K, "Kai Sammler", {"Pia Spielerin": P})
check("Teilen: Sammler bekannt", P.eval("GoldSentinelTest.collectorName"), "Kai Sammler")
check("Teilen: einmal gefragt (ohne Popup im Chat)", P.eval("#CHAT >= 1 and GoldSentinelTest.asked"), True)
# ohne Zustimmung: nichts im Ausgang, nichts gesendet
P.execute("FireError('Interface/AddOns/TestAddon/Core.lua:5: boom'); GoldSentinelTest.Flush()")
check("Teilen: ohne Zustimmung kein Ausgang", P.eval("#DB.gsTest.share.outbox"), 0)
check("Teilen: ohne Zustimmung nichts gesendet", P.eval("GoldSentinelTest.SendPending()"), 0)
# mit Zustimmung
P.execute("SlashCmdList.GOLDSENTINELTEST('teilen an')")
P.execute("FireError('Interface/AddOns/TestAddon/Core.lua:9: kaputt'); GoldSentinelTest.Flush()")
check("Teilen: Kurzfassung im Ausgang", P.eval("#DB.gsTest.share.outbox"), 1)
P.execute("local r = GoldSentinelTest.Begin('TestAddon', '1.0', DB); r:Check('T1', 'A', 'geht', function() return false, 'x', 'y' end); r:Finish()")
check("Teilen: Testlauf auch im Ausgang", P.eval("#DB.gsTest.share.outbox"), 2)
check("Teilen: gesendet", P.eval("GoldSentinelTest.SendPending()"), 2)
out = flush_out(P)
check("Teilen: nur Flüstern an den Sammler", sorted({(d, t) for _, _, d, t in out}), [("WHISPER", "Kai Sammler")])
check("Teilen: keine Namen in den Nachrichten", any("Pia" in m for _, m, _, _ in out), False)
for p_, m, d, tgt in out:
    K.globals().Fire("CHAT_MSG_ADDON", p_, m, d, "Pia Spielerin")
fremd = lua_to_py(K.eval("DB.gsTest.fremd")) or []
check("Sammler: 2 fremde Berichte", len(fremd), 2)
reps = [json.loads(f[len("GSTEST1"):]) for f in fremd]
check("Sammler: fremd markiert", [r.get("fremd") for r in reps], [True, True])
check("Sammler: Fehlertext da", any("kaputt" in (e.get("msg") or "") for r in reps for e in r.get("errors", [])), True)
check("Sammler: FEHLER-Zeile aus Testlauf", any(x.get("id") == "T1" for r in reps for x in r.get("results", [])), True)
check("Sammler: keine Namen gespeichert", any(n in "".join(fremd) for n in ("Pia", "Kai")), False)
sys.path.insert(0, str(HERE.parents[1] / "addon-check"))
import testberichte  # noqa: E402
lua_text = 'DB = { gsTest = { fremd = { "%s" } } }' % fremd[0].replace("\\", "\\\\").replace('"', '\\"')
found = [testberichte.clean(r) for r in testberichte.from_text(lua_text)]
check("Uploader/Auswertung liest fremden Bericht", bool(found and found[0] and found[0].get("fremd")), True)
# Bestätigung leert den Ausgang
route(K, "Kai Sammler", {"Pia Spielerin": P})
check("Teilen: Bestätigung leert den Ausgang", P.eval("#DB.gsTest.share.outbox"), 0)
# gleicher Fehler nicht nochmals in 7 Tagen; höchstens 3 je Tag
P.execute("FireError('Interface/AddOns/TestAddon/Core.lua:9: kaputt'); GoldSentinelTest.Flush()")
check("Teilen: gleicher Fehler nicht nochmals", P.eval("#DB.gsTest.share.outbox"), 0)
for i in range(4):
    P.execute(f"FireError('Interface/AddOns/TestAddon/Core.lua:{20 + i}: neu{i}'); GoldSentinelTest.Flush()")
check("Teilen: höchstens 1 weiterer heute (3 je Tag)", P.eval("GoldSentinelTest.SendPending()"), 1)
# Sammler schickt eigene Berichte nicht
K.execute("FireError('Interface/AddOns/TestAddon/Core.lua:1: eigen'); GoldSentinelTest.Flush()")
check("Sammler: eigene Fehler nicht im Ausgang", K.eval("#(DB.gsTest.share.outbox or {})"), 0)
# ohne GoldSentinelSync ruht es
lua = new_lua("DB = {}")
lua.execute("GoldSentinelTest.TrackErrors('TestAddon', '1.0', DB)")
check("ohne Sync: kein Endpunkt", lua.eval("GoldSentinelTest.Endpoint() == nil"), True)
check("ohne Sync: Status sagt es", "ruht" in "".join(lua_to_py(lua.eval("GoldSentinelTest.ShareStatus()"))), True)

print(f"GoldSentinelTest-Tests: {'bestanden' if fails == 0 else 'FEHLGESCHLAGEN'} ({checks - fails}/{checks})")
sys.exit(1 if fails else 0)
