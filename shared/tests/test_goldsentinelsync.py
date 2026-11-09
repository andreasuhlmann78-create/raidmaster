"""Tests für shared/GoldSentinelSync.lua (gemeinsame Addon-Kommunikation) in Lua 5.1 mit nachgebauten Clients.
Läuft mit: python3 -I shared/tests/test_goldsentinelsync.py

Geprüft wird u. a.: nie über "CHANNEL", Wege Gilde/Gruppe/Flüstern, Dubletten, eigene Nachrichten, Lebenszeichen und
Mitspieler, Ping/Pong, geschützte Absender, alte Nachrichten ohne Kopf, Drossel, Übernahme durch eine neuere Fassung,
alle Spielversionen (C_ChatInfo vorhanden oder nur alte Funktionen)."""
import sys
from pathlib import Path

from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
SRC = (ROOT / "shared/GoldSentinelSync.lua").read_text(encoding="utf-8")

MOCK = r"""
SENT = {}
NOW = 0
IN_GUILD, IN_RAID, IN_GROUP = true, false, false
PLAYER = ...
SECRET = {}
local frames = {}
FRAMES = frames
function CreateFrame()
  local f = { events = {}, scripts = {} }
  function f:RegisterEvent(e) self.events[e] = true end
  function f:UnregisterAllEvents() self.events = {} end
  function f:SetScript(k, fn) self.scripts[k] = fn end
  frames[#frames + 1] = f
  return f
end
function GetTime() return NOW end
TIME = 1794240000
function time() return TIME end
COMBAT = false
function InCombatLockdown() return COMBAT end
ERR_CHAT_PLAYER_NOT_FOUND_S = "Momentan ist kein Spieler mit dem Namen '%s' online."
FILTERS = {}
function ChatFrame_AddMessageEventFilter(ev, fn) FILTERS[#FILTERS + 1] = { ev, fn } end
function IsInGuild() return IN_GUILD end
function IsInRaid() return IN_RAID end
function IsInGroup() return IN_GROUP end
function UnitName() return PLAYER end
issecretvalue = function(v) return SECRET[v] == true end
REG = {}
if not NO_CCHATINFO then
  C_ChatInfo = {
    SendAddonMessage = function(p, m, d, t) SENT[#SENT + 1] = { p, m, d, t }; return true end,
    RegisterAddonMessagePrefix = function(p) REG[p] = true end,
  }
else
  SendAddonMessage = function(p, m, d, t) SENT[#SENT + 1] = { p, m, d, t } end
  RegisterAddonMessagePrefix = function(p) REG[p] = true end
end
math.randomseed(SEED)
function FIRE(event, ...)
  for _, f in ipairs(frames) do
    if f.events[event] and f.scripts.OnEvent then f.scripts.OnEvent(f, event, ...) end
  end
end
function UPDATE(dt)
  for _, f in ipairs(frames) do if f.scripts.OnUpdate then f.scripts.OnUpdate(f, dt) end end
end
"""


class Client:
    def __init__(self, name, seed, old_api=False, src=None):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        g = self.lua.globals()
        g.SEED = seed
        g.NO_CCHATINFO = old_api
        self.lua.execute(MOCK.replace("PLAYER = ...", f'PLAYER = "{name}"'))
        self.lua.execute(src or SRC)
        self.S = g.GoldSentinelSync
        self.name = name

    def run(self, code):
        return self.lua.execute(code)

    def sent(self):
        g = self.lua.globals()
        out = [tuple(g.SENT[i][k] for k in (1, 2, 3, 4)) for i in range(1, len(g.SENT) + 1)]
        return out

    def clear(self):
        self.lua.execute("SENT = {}")

    def pump_all(self):
        self.lua.execute("for i = 1, 500 do if not GoldSentinelSync.Pump(true) then break end end")

    def deliver(self, msgs, sender):
        for p, m, d, _ in msgs:
            self.lua.globals().FIRE("CHAT_MSG_ADDON", p, m, d, sender)


fails = checks = 0


def check(label, got, want):
    global fails, checks
    checks += 1
    if got != want:
        fails += 1
        print(f"FEHLER [{label}] = {got!r} (erwartet {want!r})")


def exchange(a, b, rounds=4):
    """Nachrichten hin und her, bis Ruhe ist (Gilde: jeder bekommt alles vom anderen)."""
    for _ in range(rounds):
        a.pump_all(); b.pump_all()
        ma, mb = a.sent(), b.sent()
        a.clear(); b.clear()
        if not ma and not mb:
            break
        b.deliver(ma, a.name)
        a.deliver(mb, b.name)


# --- 1. Nie über CHANNEL, Wege nach Lage -------------------------------------------------------------------------
c = Client("Testa Beispiel", 1)
c.run('EP = GoldSentinelSync.Register("ProbeAddon", "PROBE1", "1.0")')
c.run('EP:Send("hallo")')
c.pump_all()
s = [m for m in c.sent() if m[0] == "PROBE1"]
check("Gilde: genau ein Weg GUILD", [m[2] for m in s], ["GUILD"])
check("nie CHANNEL", any(m[2] == "CHANNEL" for m in c.sent()), False)
c.clear()
c.run('IN_GROUP = true; EP:Send("x")'); c.pump_all()
check("Gilde + Gruppe", sorted(m[2] for m in c.sent() if m[0] == "PROBE1"), ["GUILD", "PARTY"])
c.clear()
c.run('IN_RAID = true; EP:Send("x", { scope = "group" })'); c.pump_all()
check("nur Gruppe im Raid -> RAID", [m[2] for m in c.sent() if m[0] == "PROBE1"], ["RAID"])
c.clear()
c.run('EP:Send("x", { target = "Andere Person" })'); c.pump_all()
check("Flüstern", [(m[2], m[3]) for m in c.sent() if m[0] == "PROBE1"], [("WHISPER", "Andere Person")])
c.clear()
c.run('IN_GUILD, IN_RAID, IN_GROUP = false, false, false; OK, N = EP:Send("x")')
check("ohne Weg: nichts gesendet", (c.lua.globals().OK, c.lua.globals().N, len(c.sent())), (False, 0, 0))
check("ohne Weg gezählt", c.run("return EP:Stats().dropped.nopath"), 1)
c.run('IN_GUILD = true')
check("zu lang abgelehnt", c.run('local ok, why = EP:Send(string.rep("a", 300)); return why'), "zu lang")
check("Kennung registriert", (c.run('return REG["PROBE1"]'), c.run('return REG["GSSYNC1"]')), (True, True))

# --- 2. Zwei Clients: Zustellung, Dubletten, eigene Nachrichten, Mitspieler --------------------------------------
a, b = Client("Spieler Eins", 11), Client("Spieler Zwei", 22)
for x in (a, b):
    x.run('EP = GoldSentinelSync.Register("ProbeAddon", "PROBE1", "1.0"); GOT = {}; '
          'EP:OnMessage(function(m, s, d) GOT[#GOT + 1] = { m, s, d } end); IN_GROUP = true')
a.run('EP:Send("preis:42")')
a.pump_all()
msgs = a.sent(); a.clear()
check("zwei Wege (Gilde+Gruppe)", len([m for m in msgs if m[0] == "PROBE1"]), 2)
b.deliver(msgs, a.name)
check("Dublette nur einmal zugestellt", b.run("return #GOT"), 1)
check("Inhalt ohne Kopf", b.run("return GOT[1][1]"), "preis:42")
check("Absender", b.run("return GOT[1][2]"), "Spieler Eins")
check("Dublette gezählt", b.run("return EP:Stats().dropped.duplicate"), 1)
a.deliver(msgs, a.name)
check("eigene Nachricht nicht zugestellt", a.run("return #GOT"), 0)
# Lebenszeichen nach 10 s
for x in (a, b):
    x.run("NOW = 11; UPDATE(0.2)")
exchange(a, b)
check("Mitspieler A sieht B", a.run("return EP:Peers(3600)"), 1)
check("Mitspieler B sieht A", b.run("return EP:Peers(3600)"), 1)
# später Hinzukommender lernt den anderen sofort kennen (Antwort auf sein Lebenszeichen)
l = Client("Spaet Dazu", 33)
l.run('EP = GoldSentinelSync.Register("ProbeAddon", "PROBE1", "1.0"); NOW = 50; UPDATE(0.2)')
a.run("NOW = 50")
exchange(a, l)
check("später Dazugekommener sieht A sofort", l.run("return EP:Peers(3600)"), 1)
check("A sieht jetzt 2", a.run("return EP:Peers(3600)"), 2)
check("Mitspieler nach 2 Std. weg", a.run("NOW = 11 + 7300; return EP:Peers(3600)"), 0)

# --- 3. Ping / Pong ----------------------------------------------------------------------------------------------
a.run("NOW = 100; RES = nil; GoldSentinelSync.Ping('ProbeAddon', function(r) RES = r end)")
b.run("NOW = 100")
exchange(a, b)
a.run("NOW = 106; UPDATE(0.2)")
check("Ping: 1 Antwort", a.run("return RES and RES.total"), 1)
check("Ping: über Gilde gezählt", a.run("return RES and RES.guild"), 1)
c2 = Client("Allein", 5)
c2.run("IN_GUILD = false; RES = nil; GoldSentinelSync.Ping('X', function(r) RES = r end)")
check("Ping ohne Weg sofort", c2.run("return RES and RES.nopath"), True)

# --- 4. Geschützte Absender, alte Nachrichten ohne Kopf ---------------------------------------------------------
b.run('GOT = {}; SECRET["Geheim"] = true')
b.deliver([("PROBE1", "#S1:zzzzz:1:wert", "GUILD", None)], "Geheim")
check("geschützter Absender: zugestellt ohne Namen", (b.run("return #GOT"), b.run("return GOT[1] and GOT[1][2]")), (1, None))
b.run('SECRET["#S1:zzzzz:2:x"] = true')
b.deliver([("PROBE1", "#S1:zzzzz:2:x", "GUILD", None)], "Jemand")
check("geschützte Nachricht verworfen", b.run("return GoldSentinelSync.stats.dropped.secret"), 1)
b.run("GOT = {}")
b.deliver([("PROBE1", "altes:format", "GUILD", None)], "Alter Client")
check("alte Nachricht ohne Kopf zugestellt", b.run("return GOT[1] and GOT[1][1]"), "altes:format")
b.deliver([("PROBE1", "altes:eigen", "GUILD", None)], "Spieler Zwei")
check("alte eigene Nachricht nicht zugestellt", b.run("return #GOT"), 1)
b.deliver([("FREMD", "#S1:aaaaa:1:x", "GUILD", None)], "X")
check("fremde Kennung ignoriert", b.run("return #GOT"), 1)

# --- 5. Drossel und Warteschlange --------------------------------------------------------------------------------
d = Client("Drossel", 7)
d.run('EP = GoldSentinelSync.Register("ProbeAddon", "PROBE1", "1.0"); for i = 1, 5 do EP:Send("m" .. i) end')
d.run("NOW = 0; GoldSentinelSync.lastSend = -100; GoldSentinelSync.Pump(); GoldSentinelSync.Pump()")
check("Drossel: im selben Moment nur 1", len(d.sent()), 1)
d.run("NOW = 0.25; GoldSentinelSync.Pump()")
check("Drossel: nach 0,25 s die nächste", len(d.sent()), 2)
d.run("GoldSentinelSync.QUEUE_MAX = 3; for i = 1, 5 do EP:Send('q' .. i) end")
check("volle Warteschlange: älteste weg", d.run("return GoldSentinelSync.stats.dropped.queue ~= nil"), True)

# --- 6. Kanal-Hinweis, Diagnose ohne Namen ------------------------------------------------------------------------
d.run('FIRE("CHAT_MSG_CHANNEL_NOTICE", "NOT_ALLOWED_IN_CHANNEL")')
check("Kanal verweigert gezählt", d.run("return GoldSentinelSync.stats.channelRefused"), 1)
lines = d.run("return table.concat(GoldSentinelSync.DiagLines(), '\\n')")
check("Diagnose nennt Wege", "Wege: GUILD" in lines, True)
check("Diagnose ohne Spielernamen", "Drossel" in lines, False)

# --- 7. Alte Spielversion ohne C_ChatInfo --------------------------------------------------------------------------
e = Client("Era Spieler", 9, old_api=True)
e.run('EP = GoldSentinelSync.Register("ProbeAddon", "PROBE1", "1.0"); EP:Send("x")')
e.pump_all()
check("alte API: gesendet über GUILD", [m[2] for m in e.sent() if m[0] == "PROBE1"], ["GUILD"])
check("alte API: Kennung registriert", e.run('return REG["PROBE1"]'), True)

# --- 8. Übernahme durch eine neuere Fassung -----------------------------------------------------------------------
u = Client("Update", 3)
u.run('EP = GoldSentinelSync.Register("ProbeAddon", "PROBE1", "1.0"); GOT = {}; EP:OnMessage(function(m) GOT[#GOT+1] = m end)')
sid_before = u.run("return GoldSentinelSync.sid")
newer = SRC.replace("local VERSION = 2", "local VERSION = 3")
u.run(newer)
check("neuere Fassung übernimmt", u.run("return GoldSentinelSync.VERSION"), 3)
check("Anmeldung bleibt", u.run("return GoldSentinelSync.endpoints.PROBE1 == EP"), True)
check("Kennung bleibt", u.run("return GoldSentinelSync.sid"), sid_before)
u.deliver([("PROBE1", "#S1:qqqqq:1:neu", "GUILD", None)], "X")
check("nach Übernahme genau einmal zugestellt", u.run("return #GOT"), 1)
u.run(SRC)
check("ältere Fassung danach weicht", u.run("return GoldSentinelSync.VERSION"), 3)


# --- 9. Flüster-Netz ---------------------------------------------------------------------------------------------
# Welt: Gilde GA (A1, A2), Gilde GB (B1, B2), C1 ohne Gilde. Namen mit Leerzeichen wie in Forever.
class World:
    def __init__(self):
        self.clients, self.guild, self.group = {}, {}, set()
        self.whispers = []

    def add(self, name, seed, guild=None):
        c = Client(name, seed)
        c.run('EP = GoldSentinelSync.Register("ProbeAddon", "PROBE1", "1.0"); GOT = {}; '
              'EP:OnMessage(function(m, s, d) GOT[#GOT + 1] = { m, s, d } end); NOW = 20')
        c.run("IN_GUILD = %s" % ("true" if guild else "false"))
        self.clients[name], self.guild[name] = c, guild
        return c

    def set_group(self, names):
        self.group = set(names)
        for n, c in self.clients.items():
            c.run("IN_GROUP = %s" % ("true" if n in self.group and len(self.group) > 1 else "false"))

    def at(self, t):
        for c in self.clients.values():
            c.run("NOW = %s; TIME = 1794240000 + %s" % (t, t))

    def tick(self):
        for c in self.clients.values():
            c.run("GoldSentinelSync.Tick()")

    def route(self, rounds=12):
        for _ in range(rounds):
            out = []
            for n, c in self.clients.items():
                c.run("for i = 1, 500 do if not GoldSentinelSync.Pump(true) then break end end")
                out += [(n, m) for m in c.sent()]
                c.clear()
            if not out:
                return
            for sender, (p, m, d, t) in out:
                if d == "GUILD":
                    for n, c in self.clients.items():
                        if n != sender and self.guild[n] and self.guild[n] == self.guild[sender]:
                            c.lua.globals().FIRE("CHAT_MSG_ADDON", p, m, d, sender)
                elif d in ("PARTY", "RAID"):
                    for n in self.group:
                        if n != sender:
                            self.clients[n].lua.globals().FIRE("CHAT_MSG_ADDON", p, m, d, sender)
                elif d == "WHISPER":
                    self.whispers.append((sender, t, m))
                    if t in self.clients:
                        self.clients[t].lua.globals().FIRE("CHAT_MSG_ADDON", p, m, d, sender)
                    else:
                        self.clients[sender].lua.globals().FIRE(
                            "CHAT_MSG_SYSTEM", "Momentan ist kein Spieler mit dem Namen '%s' online." % t)
                elif d == "CHANNEL":
                    raise AssertionError("CHANNEL gesendet")

    def got(self, name):
        return self.clients[name].run("return #GOT")


w = World()
A1, A2 = w.add("Anna Eins", 101, "GA"), w.add("Arno Zwei", 102, "GA")
B1, B2 = w.add("Bea Drei", 103, "GB"), w.add("Bert Vier", 104, "GB")
C1 = w.add("Cleo Fuenf", 105, None)
# Lebenszeichen in den Gilden, dann A1 und B1 kurz in einer Gruppe
w.at(20); w.tick(); w.route()
w.set_group(["Anna Eins", "Bea Drei"]); w.at(40)
for c in (A1, B1):
    c.run("GoldSentinelSync.Hello()")
w.route()
w.set_group([])
check("Netz: A1 kennt B1 (Gruppe, Sync 2)", A1.run('local e = GoldSentinelSync.book["Bea Drei"]; return e and e.v'), 2)
check("Netz: voller Name mit Leerzeichen gespeichert", A1.run('return GoldSentinelSync.book["Bea"] == nil'), True)
check("Netz: A1 kennt A2 als Gilde", A1.run('local e = GoldSentinelSync.book["Arno Zwei"]; return e and e.src'), "guild")
# A1 sendet: A2 über Gilde, B1 per Flüstern, B2 über die Gilde von B1
for n in w.clients:
    w.clients[n].run("GOT = {}")
w.whispers = []
A1.run('EP:Send("preis:7")')
w.route()
check("Netz: A2 (Gilde) bekommt es", w.got("Arno Zwei"), 1)
check("Netz: B1 (Flüstern) bekommt es", w.got("Bea Drei"), 1)
check("Netz: B2 (Gilde von B1) bekommt es", w.got("Bert Vier"), 1)
check("Netz: Inhalt ohne Kopf", B2.run("return GOT[1][1]"), "preis:7")
check("Netz: kein Flüstern an Gildenmitglieder", [t for s_, t, m in w.whispers if s_ == "Anna Eins" and t == "Arno Zwei"], [])
check("Netz: C1 (unbekannt) bekommt nichts", w.got("Cleo Fuenf"), 0)
check("Netz: weitergegeben gezählt", B1.run("return GoldSentinelSync.stats.net.relayed"), 1)
# nochmals dieselbe Nachricht auf anderem Weg -> Dublette
B2.deliver([("PROBE1", "#S2:" + A1.run("return GoldSentinelSync.sid") + ":" +
             A1.run("return GoldSentinelSync.Enc(GoldSentinelSync.counter)") + ":1:preis:7", "WHISPER", None)], "Anna Eins")
check("Netz: Dublette über Flüstern verworfen", w.got("Bert Vier"), 1)

# Listen: C1 trifft A1 in einer Gruppe, bekommt später A1s Liste und stellt sich B1 vor
w.set_group(["Anna Eins", "Cleo Fuenf"]); w.at(60)
for c in (A1, C1):
    c.run("GoldSentinelSync.Hello()")
w.route()
w.set_group([])
w.at(60 + 700); w.tick(); w.route()
check("Liste: C1 kennt B1 aus A1s Liste", C1.run('local e = GoldSentinelSync.book["Bea Drei"]; return e ~= nil'), True)
w.at(60 + 740); w.tick(); w.route()
check("Vorstellung: B1 kennt C1 (Flüstern, Sync 2)", B1.run('local e = GoldSentinelSync.book["Cleo Fuenf"]; return e and e.v'), 2)
check("Vorstellung: C1 kennt B1 direkt", C1.run('return GoldSentinelSync.book["Bea Drei"].src') in ("whisper", "net"), True)
for n in w.clients:
    w.clients[n].run("GOT = {}")
C1.run('EP:Send("von:cleo")')
w.route()
check("C1 ohne Gilde erreicht alle", [w.got(n) for n in ("Anna Eins", "Arno Zwei", "Bea Drei", "Bert Vier")], [1, 1, 1, 1])

# Offline: ein bekannter Spieler ist nicht da
A1.run('GoldSentinelSync.Learn("Otto Offline", "group", 2)')
A1.run('GoldSentinelSync.NET_FANOUT = 10')
w.whispers = []
A1.run('EP:Send("x1")')
w.route()
check("Offline: angeflüstert", any(t == "Otto Offline" for _, t, _ in w.whispers), True)
check("Offline: gezählt", A1.run("return GoldSentinelSync.stats.net.offline"), 1)
check("Offline: pausiert", A1.run('return GoldSentinelSync.book["Otto Offline"].pause > NOW'), True)
f_hide = A1.run('local f = FILTERS[1][2]; GoldSentinelSync.whispered["Otto Offline"] = NOW; '
                'return f(nil, "CHAT_MSG_SYSTEM", "Momentan ist kein Spieler mit dem Namen \'Otto Offline\' online.")')
check("Offline: Meldung ausgeblendet", f_hide, True)
f_keep = A1.run('local f = FILTERS[1][2]; return f(nil, "CHAT_MSG_SYSTEM", '
                '"Momentan ist kein Spieler mit dem Namen \'Fremd Name\' online.")')
check("Offline: fremde Meldung bleibt sichtbar", f_keep[0] if isinstance(f_keep, tuple) else f_keep, False)
w.whispers = []
A1.run('EP:Send("x2")')
w.route()
check("Offline: in der Pause nicht angeflüstert", any(t == "Otto Offline" for _, t, _ in w.whispers), False)
A1.run('for i = 1, 5 do GoldSentinelSync.book["Otto Offline"].fail = 5 end; GoldSentinelSync.TrimBook()')
check("Offline: nach 5 Fehlschlägen vergessen", A1.run('return GoldSentinelSync.book["Otto Offline"] == nil'), True)

# Nur an Sync 2: ein Spieler ohne Sync-Version bekommt nie "#S2"
A1.run('GoldSentinelSync.Learn("Alt Version", "group", nil)')
check("Netz: alte Version nie Ziel", A1.run('for _, n in ipairs(GoldSentinelSync.NetTargets(50)) do '
                                           'if n == "Alt Version" then return true end end return false'), False)
# Drossel je Minute und Kampf
d2 = Client("Drossel Netz", 77)
d2.run('EP = GoldSentinelSync.Register("ProbeAddon", "PROBE1", "1.0"); IN_GUILD = false; NOW = 500')
d2.run('for i = 1, 60 do GoldSentinelSync.Learn("Ziel " .. i, "group", 2) end; GoldSentinelSync.NET_FANOUT = 60')
d2.run('EP:Send("viel")')
d2.run('COMBAT = true'); d2.pump_all()
check("Netz: im Kampf nichts", len(d2.sent()), 0)
d2.run('COMBAT = false'); d2.pump_all()
check("Netz: höchstens 40 pro Minute", len(d2.sent()), 40)
d2.clear(); d2.run('NOW = 561'); d2.pump_all()
check("Netz: nächste Minute der Rest", len(d2.sent()), 20)
d2.run('GoldSentinelSync.NET = false; NOW = 700'); d2.clear()
check("Netz aus: ohne Gilde kein Weg", d2.run('local ok = EP:Send("x"); return ok'), False)
d2.run('GoldSentinelSync.NET = true')
check("opts.net = false: nicht ins Netz", d2.run('local ok, n = EP:Send("x", { net = false }); return n'), 0)

# Speichern über /reload
st = Client("Speicher Test", 88)
st.run('DB = {}; EP = GoldSentinelSync.Register("ProbeAddon", "PROBE1", "1.0"); EP:UseStorage(DB); '
       'GoldSentinelSync.Learn("Weit Weg", "whisper", 2)')
check("Speicher: Name in der Tabelle", st.run('return DB.gsSync.book["Weit Weg"].v'), 2)
st2 = Client("Speicher Test", 89)
st2.run('DB = { gsSync = { book = { ["Weit Weg"] = { seen = TIME, v = 2, src = "whisper", fail = 0 } } } }; '
        'EP = GoldSentinelSync.Register("ProbeAddon", "PROBE1", "1.0"); EP:UseStorage(DB)')
check("Speicher: nach /reload bekannt", st2.run('return GoldSentinelSync.book["Weit Weg"].v'), 2)
st2.run('DB2 = { gsSync = { book = { ["Noch Wer"] = { seen = TIME, v = 2 } } } }; GoldSentinelSync.UseStorage(DB2.gsSync)')
check("Speicher: zweites Addon wird eingelesen", st2.run('return DB.gsSync.book["Noch Wer"] ~= nil'), True)
st2.run('TIME = TIME + 31 * 86400; GoldSentinelSync.TrimBook()')
check("Speicher: nach 30 Tagen vergessen", st2.run('return GoldSentinelSync.book["Weit Weg"] == nil'), True)

# Diagnose ohne Namen
lines = A1.run("return table.concat(GoldSentinelSync.DiagLines(), '\\n')")
check("Diagnose: Netz-Zeile", "NETZ an" in lines, True)
check("Diagnose: keine Namen", any(n in lines for n in ("Anna", "Bea Drei", "Otto", "Cleo")), False)

# Übernahme von Version 1: Zähler läuft weiter (sonst gelten neue Nachrichten als Dubletten)
import subprocess
v1 = (ROOT / "shared/tests/variants/GoldSentinelSync-v1.lua").read_text(encoding="utf-8")

if "local VERSION = 1" in v1:
    t1 = Client("Wechsel Test", 55, src=v1)
    t1.run('EP = GoldSentinelSync.Register("ProbeAddon", "PROBE1", "1.0"); for i = 1, 3 do EP:Send("a" .. i) end')
    before = t1.run("return GoldSentinelSync.counter")
    t1.run(SRC)
    check("Übernahme v1->v2: Version", t1.run("return GoldSentinelSync.VERSION"), 2)
    check("Übernahme v1->v2: Zähler läuft weiter", t1.run("return GoldSentinelSync.counter") >= before, True)
    check("Übernahme v1->v2: Netz-Zähler da", t1.run("return GoldSentinelSync.stats.net.sent"), 0)
    t1.run('EP:Send("nach")')
    t1.pump_all()
    check("Übernahme v1->v2: senden geht", any("nach" in m[1] for m in t1.sent()), True)
else:
    check("Version 1 aus Git gefunden", False, True)

print(f"GoldSentinelSync-Tests: {'bestanden' if fails == 0 else 'FEHLGESCHLAGEN'} ({checks - fails}/{checks})")
sys.exit(1 if fails else 0)
