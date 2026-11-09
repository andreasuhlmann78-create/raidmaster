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
    def __init__(self, name, seed, old_api=False):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        g = self.lua.globals()
        g.SEED = seed
        g.NO_CCHATINFO = old_api
        self.lua.execute(MOCK.replace("PLAYER = ...", f'PLAYER = "{name}"'))
        self.lua.execute(SRC)
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
newer = SRC.replace("local VERSION = 1", "local VERSION = 2")
u.run(newer)
check("neuere Fassung übernimmt", u.run("return GoldSentinelSync.VERSION"), 2)
check("Anmeldung bleibt", u.run("return GoldSentinelSync.endpoints.PROBE1 == EP"), True)
check("Kennung bleibt", u.run("return GoldSentinelSync.sid"), sid_before)
u.deliver([("PROBE1", "#S1:qqqqq:1:neu", "GUILD", None)], "X")
check("nach Übernahme genau einmal zugestellt", u.run("return #GOT"), 1)
u.run(SRC)
check("ältere Fassung danach weicht", u.run("return GoldSentinelSync.VERSION"), 2)

print(f"GoldSentinelSync-Tests: {'bestanden' if fails == 0 else 'FEHLGESCHLAGEN'} ({checks - fails}/{checks})")
sys.exit(1 if fails else 0)
