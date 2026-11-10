#!/usr/bin/env python3
"""Offline-Test für das Messwerkzeug shared/messtest/GSMesstest (zwei simulierte Clients, Lua 5.1 über lupa).

Prüft: Ablauf "/gsmess alle" läuft ohne Lua-Fehler durch, T1–T4 liefern Ergebnisse, das Ergebnis enthält keine Namen,
GSDIAG1-Zeichenkette ist für addon-check/testberichte.py lesbar.
"""
import pathlib
import sys

try:
    from lupa import lua51 as lupa_mod
except ImportError:  # ältere lupa
    import lupa as lupa_mod

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = (ROOT / "shared/messtest/GSMesstest/GSMesstest.lua").read_text(encoding="utf-8")

NAMES = ("Testalpha", "Testbeta")
OFFLINE = "Testgamma"
clock = {"t": 100.0}
clients = {}
channel_members = set()
ok_count = fail_count = 0


def check(cond, text):
    global ok_count, fail_count
    if cond:
        ok_count += 1
    else:
        fail_count += 1
        print("FEHLER:", text)


MOCK = r"""
local me, py = ...
local frames = {}
filters = {}
outbox = {}
chat = {}
NOW = 100
function GetTime() return NOW end
function UnitName() return me end
function GetBuildInfo() return "1.60.1", "99999", "Nov 1 2026", 16001 end
function InCombatLockdown() return false end
function IsInGuild() return true end
function GetNumGuildMembers() return 3 end
local roster = { { py.name(0), true }, { py.name(1), true }, { py.offline(), false } }
function GetGuildRosterInfo(i) local r = roster[i]; return r[1], "R", 1, 60, "Krieger", "", "", "", r[2] end
function GuildRoster() end
C_ChatInfo = {
  RegisterAddonMessagePrefix = function() return true end,
  SendAddonMessage = function(p, m, d, t) outbox[#outbox + 1] = { "send", me, p, m, d, t }; return 0 end,
}
local repl = {}
for i = 1, 3000 do repl[i] = { "Item" .. i, 1, (i % 20) + 1, 1, true, 1, 0, 50, 5, 100 + i, 0, false, nil, "Besitzername", "Besitzername-Realm", 0, 2000 + (i % 400), true } end
C_AuctionHouse = {
  ReplicateItems = function() outbox[#outbox + 1] = { "repl", me } end,
  GetNumReplicateItems = function() return #repl end,
  GetReplicateItemInfo = function(i) local t = repl[i + 1]; if not t then return nil end return unpack(t, 1, 18) end,
  GetReplicateItemTimeLeft = function(i) return (i % 4) + 1 end,
  SendBrowseQuery = function() end,
}
AuctionHouseFrame = { IsShown = function() return true end }
function JoinTemporaryChannel(n) outbox[#outbox + 1] = { "join", me } end
function LeaveChannelByName(n) outbox[#outbox + 1] = { "leave", me } end
function ListChannelByName(n) outbox[#outbox + 1] = { "list", me } end
function date(f) return "09.11.2026 18:50" end
DEFAULT_CHAT_FRAME = { AddMessage = function(_, s) chat[#chat + 1] = s end }
function ChatFrame_AddMessageEventFilter(ev, fn) filters[ev] = filters[ev] or {}; table.insert(filters[ev], fn) end
SlashCmdList = {}
function CreateFrame()
  local f = { ev = {}, sc = {} }
  function f:RegisterEvent(e) self.ev[e] = true end
  function f:SetScript(k, fn) self.sc[k] = fn end
  frames[#frames + 1] = f
  return f
end
function Fire(ev, ...)
  local hidden = false
  for _, fn in ipairs(filters[ev] or {}) do if fn(nil, ev, ...) then hidden = true end end
  for _, f in ipairs(frames) do if f.ev[ev] and f.sc.OnEvent then f.sc.OnEvent(f, ev, ...) end end
  return hidden
end
function Tick() for _, f in ipairs(frames) do if f.sc.OnUpdate then f.sc.OnUpdate(f, 0.02) end end end
"""


pending, pending_sys, pending_list, pending_repl = [], [], [], []


def boot():
    for i, n in enumerate(NAMES):
        rt = lupa_mod.LuaRuntime(unpack_returned_tuples=True)

        class Py:
            pass
        py = Py()
        py.name = lambda i: NAMES[int(i)]
        py.offline = lambda: OFFLINE

        loader = rt.eval("function(src, me, py) local f = assert(loadstring(src)); return f(me, py) end")
        loader(MOCK, n, py)
        rt.execute(SRC)
        rt.globals().Fire("PLAYER_LOGIN")
        clients[n] = rt


def drain():
    for n, rt in clients.items():
        box = rt.globals().outbox
        items = [box[i] for i in range(1, len(box) + 1)]
        rt.execute("outbox = {}")
        for it in items:
            kind, who = it[1], str(it[2])
            if kind == "send" and str(it[5]) in ("YELL", "SAY"):
                for c in clients:          # Rufweite: alle simulierten Clients, auch der Sender selbst (Echo)
                    pending.append((c, it[3], it[4], str(it[5]), who))
            elif kind == "send":
                prefix, msg, target = it[3], it[4], str(it[6])
                if target in clients:
                    pending.append((target, prefix, msg, "WHISPER", who))
                else:
                    pending_sys.append((who, "Kein Spieler namens '%s' ist momentan online." % target))
            elif kind == "join":
                channel_members.add(who)
            elif kind == "leave":
                channel_members.discard(who)
            elif kind == "repl":
                pending_repl.append(who)
            elif kind == "list":
                pending_list.append((who, ", ".join(sorted(channel_members))))


def pump(seconds):
    end = clock["t"] + seconds
    while clock["t"] < end:
        clock["t"] = round(clock["t"] + 0.02, 4)
        for rt in clients.values():
            rt.globals().NOW = clock["t"]
            rt.globals().Tick()
        drain()
        while pending_repl:
            who = pending_repl.pop(0)
            clients[who].globals().Fire("REPLICATE_ITEM_LIST_UPDATE")
        while pending or pending_sys or pending_list:
            if pending:
                target, prefix, msg, dist, sender = pending.pop(0)
                clients[target].globals().Fire("CHAT_MSG_ADDON", prefix, msg, dist, sender)
            if pending_sys:
                who, text = pending_sys.pop(0)
                clients[who].globals().Fire("CHAT_MSG_SYSTEM", text)
            if pending_list:
                who, text = pending_list.pop(0)
                hidden = clients[who].globals().Fire("CHAT_MSG_CHANNEL_LIST", text, "", "", "5. GSMessRealm",
                                                     "", "", 0, 5, "GSMessRealm")
                check(hidden, "Kanalliste nicht ausgeblendet")
            drain()


def main():
    boot()
    a = clients[NAMES[0]].globals()
    a.SlashCmdList.GSMESSTEST("")
    a.SlashCmdList.GSMESSTEST("alle")
    check(any("Zuerst" in str(s) for s in a.chat.values()), "ohne Partner kein Hinweis")
    a.SlashCmdList.GSMESSTEST("partner " + NAMES[1] + "-Forever")
    a.SlashCmdList.GSMESSTEST("alle")
    pump(70)
    export = a.GSMesstestDB.export
    check(export is not None, "kein Export")
    export = str(export or "")
    print(export)
    check(export.startswith("GSDIAG1|GSMesstest|4|"), "Kopf GSDIAG1 falsch")
    for n in NAMES + (OFFLINE,):
        check(n not in export, "Name im Ergebnis: " + n)
    check("T1 hin: gesendet 10" in export and "angekommen 10/10" in export, "T1 nicht vollständig")
    check("Rückweg angekommen 10/10" in export, "T1 Rückweg fehlt")
    check("T2 20/s: gesendet 50" in export and "T2 Stoss 30: gesendet 30" in export, "T2 fehlt")
    check("T3 Systemmeldung" in export and "<Offline>" in export and "<Unbekannt>" in export, "T3 fehlt")
    check("ausblendbar): ja" in export, "T3 Filter")
    check("gleicher interner Realm" in export, "T4 Realm")
    check(not channel_members, "Kanal nicht verlassen")
    check("Lua-Fehler" not in export, "Lua-Fehler im Ablauf")
    # zweiter Lauf: der Empfänger zählt je Lauf neu (Befund 9.11.: 20/10 nach zwei Läufen)
    a.SlashCmdList.GSMESSTEST("t1")
    pump(15)
    a.SlashCmdList.GSMESSTEST("bericht")
    second = str(a.GSMesstestDB.export)
    check("angekommen 10/10" in second and "20/10" not in second, "zweiter Lauf zählt doppelt")
    check(not a.GSMesstest.busy, "busy bleibt gesetzt")
    # A1 Auktionen (Messauftrag M1): ohne Partner, nur Existenz, dann holen
    a.SlashCmdList.GSMESSTEST("auktionen")
    e1 = str(a.GSMesstestDB.export)
    check("ReplicateItems=ja" in e1 and "GetReplicateItemTimeLeft=ja" in e1, "A1 Funktionen nicht erkannt")
    a.SlashCmdList.GSMESSTEST("auktionen holen")
    pump(5)
    e2 = str(a.GSMesstestDB.export)
    print(e2)
    check("Einzelauktionen 3000" in e2, "A1 Anzahl fehlt")
    check("Restzeit-Stufen" in e2 and "1:" in e2, "A1 Restzeit fehlt")
    check("Besitzername" not in e2 and "Item1 " not in e2, "A1 Name im Ergebnis")
    check("Besitzer bekannt ja" in e2, "A1 Besitzer-Feld nicht gemeldet")
    check(not a.GSMesstest.busy, "A1 busy bleibt gesetzt")
    # A2 Rufen (Messauftrag M5): YELL/SAY, Antwort per Flüstern, fremde Präfixe passiv
    b = clients[NAMES[1]].globals()
    b.Fire("CHAT_MSG_ADDON", "FremdAddon", "hallo", "YELL", NAMES[0] + "-Forever")
    a.Fire("CHAT_MSG_ADDON", "FremdAddon", "hallo", "SAY", NAMES[1])
    a.SlashCmdList.GSMESSTEST("rufen")
    pump(35)
    e3 = str(a.GSMesstestDB.export)
    print(e3)
    check("A2 YELL: gesendet (Rückgabe 0), eigenes Echo: ja, Antworten von 1 Spieler(n)" in e3, "A2 YELL fehlt")
    check("A2 SAY: gesendet (Rückgabe 0), eigenes Echo: ja, Antworten von 1 Spieler(n)" in e3, "A2 SAY fehlt")
    check("SAY 1, YELL 0, Präfixe: FremdAddon" in e3, "A2 fremde Nachrichten falsch")
    check("(belegt)" in e3, "A2 Ergebnis fehlt")
    for n in NAMES:
        check(n not in e3, "A2 Name im Ergebnis: " + n)
    check(not a.GSMesstest.busy, "A2 busy bleibt gesetzt")
    # ohne Antwort: B ist nicht in Rufweite (Antworten verschluckt)
    a.SlashCmdList.GSMESSTEST("rufen")
    clients[NAMES[1]].execute("C_ChatInfo.SendAddonMessage = function() return 9 end")
    pump(35)
    e4 = str(a.GSMesstestDB.export)
    check("Antworten von 0 Spieler(n)" in e4 and "niemand mit GSMesstest hat geantwortet" in e4, "A2 ohne Antwort falsch")
    check("Lua-Fehler" not in e4, "A2 Lua-Fehler")
    # testberichte.py liest es
    sys.path.insert(0, str(ROOT / "addon-check"))
    import testberichte
    lua_text = 'GSMesstestDB = { ["export"] = "%s" }' % export.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    diags, _ = testberichte.extras_from_text(lua_text)
    if diags is not None:
        check(len(diags) == 1 and diags[0]["addon"] == "GSMesstest", "testberichte.py liest GSDIAG1 nicht")
    print(f"OK {ok_count} / FEHLER {fail_count}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
