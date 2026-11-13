"""Tests für shared/GoldSentinelMarkt.lua (Marktdaten-Netz) in Lua 5.1 mit nachgebauten Clients.
Läuft mit: python3 -I shared/tests/test_goldsentinelmarkt.py

Geprüft wird: Mitlesen eines fremd ausgelösten Vollscans (ein Schub aus vielen Ereignissen = ein Lesevorgang), Lesen in
Portionen, nie im Kampf, keine Namen in Speicher/Export/Nachrichten, Zusammenfassung je Item, gemessener Absatz aus zwei
Scans (Abgänge aus Stufe 3/4), Teilen an die Gilde und Empfang beim zweiten Client, eigene frische Werte werden nicht
überschrieben, Ausreisser verworfen, andere Fraktion verworfen, Schalter aus (kein Lesen, kein Senden), Frage
"wer hat Neueres?" mit Antwort, Export für den Uploader, ohne C_AuctionHouse kein Fehler, Übernahme durch neuere Fassung,
Nachrichten nie länger als erlaubt, nie über CHANNEL."""
import sys
from pathlib import Path

from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
SYNC = (ROOT / "shared/GoldSentinelSync.lua").read_text(encoding="utf-8")
SRC = (ROOT / "shared/GoldSentinelMarkt.lua").read_text(encoding="utf-8")

MOCK = r"""
SENT = {}
NOW = 100
TIME = 1794580000
PLAYER = ...
FACTION = "Horde"
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
function time() return TIME end
MSCLOCK = 0
function debugprofilestop() MSCLOCK = MSCLOCK + 1; return MSCLOCK end
COMBAT = false
function InCombatLockdown() return COMBAT end
function IsInGuild() return true end
function IsInRaid() return false end
function IsInGroup() return false end
function UnitName() return PLAYER end
function UnitFactionGroup() return FACTION end
ERR_CHAT_PLAYER_NOT_FOUND_S = "Momentan ist kein Spieler mit dem Namen '%s' online."
function ChatFrame_AddMessageEventFilter() end
C_ChatInfo = {
  SendAddonMessage = function(p, m, d, t) SENT[#SENT + 1] = { p, m, d, t }; return true end,
  RegisterAddonMessagePrefix = function() end,
}
math.randomseed(SEED)
-- Auktionen: { itemID, Menge, Sofortkauf, Restzeit-Stufe }
AUC = {}
NAMES_READ = 0
if not NO_AH then
C_AuctionHouse = {
  GetNumReplicateItems = function() return #AUC end,
  GetReplicateItemInfo = function(i)
    local a = AUC[i + 1]
    if not a then return nil end
    -- Felder wie im Spiel: 1 Name ... 14 Besitzer, 15 Besitzer voll, 17 ItemID
    return "Itemname" .. a[1], 1, a[2], 1, true, 1, 0, 0, 0, a[3], 0, false, "Bietername", "Besitzername",
           "Besitzername-Realm", 0, a[1], true
  end,
  GetReplicateItemTimeLeft = function(i) local a = AUC[i + 1]; return a and a[4] end,
}
end
function FIRE(event, ...)
  for _, f in ipairs(frames) do
    if f.events[event] and f.scripts.OnEvent then f.scripts.OnEvent(f, event, ...) end
  end
end
function UPDATE(dt)
  for _, f in ipairs(frames) do if f.scripts.OnUpdate then f.scripts.OnUpdate(f, dt) end end
end
"""

fails = checks = 0


def check(label, got, want):
    global fails, checks
    checks += 1
    if got != want:
        fails += 1
        print(f"FEHLER [{label}] = {got!r} (erwartet {want!r})")


class Client:
    def __init__(self, name, seed, no_ah=False, src=None):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        g = self.lua.globals()
        g.SEED = seed
        g.NO_AH = no_ah
        self.lua.execute(MOCK.replace("PLAYER = ...", f'PLAYER = "{name}"'))
        self.lua.execute(SYNC)
        self.lua.execute(src or SRC)
        self.name = name
        self.run('DB = {}; GoldSentinelMarkt.Attach("ProbeAddon", DB); GoldSentinelMarkt.CHECK_EVERY = 10')
        self.tick(0.5)               # anmelden (wie im Spiel nach dem Laden)
        self.clear()

    def run(self, code):
        return self.lua.execute(code)

    def ev(self, code):
        return self.lua.eval(code)

    def tick(self, seconds, step=0.1):
        n = int(round(seconds / step))
        for _ in range(n):
            self.run(f"NOW = NOW + {step}; UPDATE({step})")

    def sent(self):
        g = self.lua.globals()
        return [tuple(g.SENT[i][k] for k in (1, 2, 3, 4)) for i in range(1, len(g.SENT) + 1)]

    def clear(self):
        self.run("SENT = {}")

    def deliver(self, msgs, sender):
        for p, m, d, _ in msgs:
            if d == "GUILD":
                self.lua.globals().FIRE("CHAT_MSG_ADDON", p, m, d, sender)


def set_auctions(c, rows):
    lua_rows = ",".join("{%d,%d,%d,%d}" % r for r in rows)
    c.run("AUC = {" + lua_rows + "}")


def scan(c, events=200):
    """ein fremdes Addon ruft ReplicateItems: viele Ereignisse hintereinander, dann lesen"""
    for _ in range(events):
        c.lua.globals().FIRE("REPLICATE_ITEM_LIST_UPDATE")
    c.tick(6)


# Markt 1: 3 Items; Item 2589 mit vielen gleichen Stapeln
rows1 = []
for k in range(40):
    rows1.append((2589, 20, 2000 + k, 3))                # 40 verschiedene Preise, Stufe 3
for k in range(30):
    rows1.append((2589, 20, 1900, 4))                    # 30 gleiche Stapel, Stufe 4
for k in range(10):
    rows1.append((11083, 5, 1500, 1 + (k % 2)))          # kurze Restzeit
rows1.append((14047, 1, 99, 2))

a = Client("Testa", 1)
b = Client("Testb", 2)
set_auctions(a, rows1)

# --- 1. Mitlesen: ein Schub = ein Lesevorgang, in Portionen -------------------------------------------------------
scan(a)
st = a.ev("GoldSentinelMarkt.Stats()")
check("ein Scan aus 200 Ereignissen", st.scans, 1)
check("alle Auktionen gelesen", st.read, len(rows1))
check("Items", st["items"], 3)
check("in mehreren Bildern gelesen (Budget)", st.lastFrames > 1, True)
g = a.ev("GoldSentinelMarkt.Get(2589)")
check("tiefster Stückpreis 2589", g.preis, 1900 // 20)
check("Menge 2589", g.menge, 70 * 20)
check("Auktionen 2589", g.n, 70)
check("Quelle eigen", g.quelle, "eigen")
check("Absatz noch nicht gemessen", g.absatz, None)

# --- 2. keine Namen ---------------------------------------------------------------------------------------------------
blob = a.ev("(function() local out = {} for k, v in pairs(DB.gsMarkt.f.H.i) do out[#out+1] = tostring(k)..'='..v end "
            "for _, x in ipairs(DB.gsMarkt.export) do out[#out+1] = x end return table.concat(out, '|') end)()")
for n in ("Besitzername", "Bietername", "Itemname", "Testa"):
    check("kein Name im Speicher: " + n, n in blob, False)

# --- 3. Export für den Uploader ---------------------------------------------------------------------------------------
exp = a.ev("DB.gsMarkt.export[1]")
check("Export-Kopf", exp.startswith("GSMARKT1|1|H|1794580000|81|3|0|"), True)

# --- 4. Teilen an die Gilde, Empfang beim zweiten Client --------------------------------------------------------------
a.tick(30)
msgs = a.sent()
mk = [m for m in msgs if m[0] == "GSMARKT1"]
check("Scan an die Gilde gesendet", any(m[2] == "GUILD" for m in mk), True)
check("nie CHANNEL", any(m[2] == "CHANNEL" for m in msgs), False)
check("Nachrichten <= 255 Zeichen", all(len(m[1]) <= 255 for m in msgs), True)
check("keine Namen in Nachrichten", any("Besitzername" in m[1] or "Itemname" in m[1] for m in msgs), False)
b.deliver(msgs, "Testa")
gb = b.ev("GoldSentinelMarkt.Get(2589)")
check("B hat 2589 vom Netz", (gb and gb.preis, gb and gb.quelle), (95, "netz"))
check("B angenommen 3", b.ev("GoldSentinelMarkt.Stats().accepted"), 3)

# --- 5. eigener frischer Wert wird nicht überschrieben, Ausreisser verworfen ------------------------------------------
c = Client("Testc", 3)
set_auctions(c, [(2589, 20, 1000, 3)])
c.run("TIME = TIME - 600")
scan(c)
c.run("TIME = TIME + 600")
c.deliver(msgs, "Testa")      # A: 95c je Stück, C eigen: 50c (vor 10 Min.) -> innerhalb x3 -> angenommen (neuer)
check("neuerer fremder Wert ersetzt älteren eigenen", c.ev("GoldSentinelMarkt.Get(2589).quelle"), "netz")
d = Client("Testd", 4)
set_auctions(d, [(2589, 20, 100, 3)])                    # eigen 5c je Stück
d.run("TIME = TIME - 600")
scan(d)
d.run("TIME = TIME + 600")
d.deliver(msgs, "Testa")      # 95c ist > 3x 5c -> Ausreisser
check("Ausreisser verworfen", d.ev("GoldSentinelMarkt.Get(2589).quelle"), "eigen")
check("Ausreisser gezählt", d.ev("GoldSentinelMarkt.Stats().dropped.ausreisser"), 1)
check("Gilde bekommt jedes Item nur einmal", sum(m[1].count(",") for m in mk if m[2] == "GUILD") // 3, 3)
e = Client("Teste", 5)
set_auctions(e, [(2589, 20, 1900, 3)])
scan(e)                       # eigener Scan JETZT (gleiche Zeit) -> fremder nicht neuer
e.deliver(msgs, "Testa")
check("gleich alter fremder Wert nicht übernommen", e.ev("GoldSentinelMarkt.Get(2589).quelle"), "eigen")

# --- 6. andere Fraktion ------------------------------------------------------------------------------------------------
f = Client("Testf", 6)
f.run('FACTION = "Alliance"')
f.deliver(msgs, "Testa")
check("andere Fraktion verworfen", f.ev("GoldSentinelMarkt.Get(2589)"), None)

# --- 7. Absatz aus zwei Scans ------------------------------------------------------------------------------------------
# 40 Min. später: von den 30 gleichen Stapeln (Stufe 4) sind 12 weg, 10 der 40 Einzelpreise (Stufe 3) weg,
# alle 10 kurzen (11083) weg (gelten als abgelaufen), 14047 bleibt
rows2 = [r for r in rows1[:30]] + [(2589, 20, 1900, 3)] * 18 + [(14047, 1, 99, 2)]
rows2 += [(2589, 20, 1850, 4)] * 2                       # 2 neu eingestellt (abgebrochen und billiger neu?)
a.run("TIME = TIME + 2400")
set_auctions(a, rows2)
scan(a)
g2 = a.ev("GoldSentinelMarkt.Get(2589)")
check("Vergleich gezählt", a.ev("GoldSentinelMarkt.Stats().compared"), 1)
check("Absatz höchstens 2589 = 22 Abgänge in 40 Min. je Tag", round(g2.absatzMax), round(22 * 86400 / 2400))
check("Absatz vorsichtig = 22 - 2 neue", round(g2.absatz), round(20 * 86400 / 2400))
check("Abdeckung 40 Min.", round(g2.abdeckung * 60), 40)
g3 = a.ev("GoldSentinelMarkt.Get(11083)")
check("kurze Restzeit zählt nicht als Absatz", g3.absatz, 0)
check("verschwundenes Item: Angebot jetzt 0", (g3.menge, g3.n), (0, 0))
exp2 = a.ev("DB.gsMarkt.export[2]")
check("Export mit Vergleichsdauer", "|2400|" in exp2, True)
check("Export behält beide Scans (bis 6)", a.ev("#DB.gsMarkt.export"), 2)
vx = Client("Testvx", 18)
set_auctions(vx, rows1 + [(7070, 1, 500, 4)] * 3)
scan(vx)
vx.run("TIME = TIME + 1800; NOW = NOW + 100")
set_auctions(vx, rows1)
scan(vx)
ex = vx.ev("DB.gsMarkt.export[2]").split("|")[-1]
check("ausverkauftes Item im Export mit Menge 0 und 3 Abgängen (D-MN7b)", (";" + ex + ";").find(";" + vx.ev("GoldSentinelMarkt.Enc(7070)") + ",0,0,0,3,3;") >= 0, True)
check("Item ohne lange Abgänge nicht als 0-Eintrag", ",0,0,0,0,0" in ex, False)

# --- 8. Kampf: nicht lesen ---------------------------------------------------------------------------------------------
k = Client("Testk", 7)
set_auctions(k, rows1)
k.run("COMBAT = true")
scan(k)
check("im Kampf nicht gelesen", k.ev("GoldSentinelMarkt.Stats().scans"), 0)
k.run("COMBAT = false")
k.tick(3)
check("nach dem Kampf gelesen", k.ev("GoldSentinelMarkt.Stats().scans"), 1)

# --- 9. Schalter aus: kein Lesen, kein Senden, kein Annehmen ------------------------------------------------------------
o = Client("Testo", 8)
o.run('DB2 = {}; GoldSentinelMarkt.Attach("ZweitesAddon", DB2); GoldSentinelMarkt.SetShare("ZweitesAddon", false)')
check("ein Schalter aus = aus", o.ev("GoldSentinelMarkt.IsShareOn()"), False)
set_auctions(o, rows1)
scan(o)
o.tick(70)
check("aus: nicht gelesen", o.ev("GoldSentinelMarkt.Stats().scans"), 0)
check("aus: nichts gesendet", [m for m in o.sent() if m[0] == "GSMARKT1"], [])
o.deliver(msgs, "Testa")
check("aus: nichts angenommen", o.ev("GoldSentinelMarkt.Get(2589)"), None)
check("Schalter gespeichert", o.ev("DB2.gsMarktAus"), True)
o.run('GoldSentinelMarkt.SetShare("ZweitesAddon", true)')
check("wieder an", o.ev("GoldSentinelMarkt.IsShareOn()"), True)

# --- 10. Speichern und Weitergeben: Frage und Antwort ------------------------------------------------------------------
n = Client("Testn", 9)        # neu eingeloggt, keine Daten
n.run("TIME = TIME + 2400")   # gleiche Uhr wie A
a.clear(); n.clear()
n.tick(65)                    # fragt nach ASK_DELAY
q = [m for m in n.sent() if m[0] == "GSMARKT1" and ":Q:" in m[1]]
check("Frage an die Gilde", len(q) == 1 and q[0][2] == "GUILD", True)
a.deliver(n.sent(), "Testn")
a.clear()
a.tick(30)
ans = a.sent()
check("A antwortet", any(":A:H:" in m[1] for m in ans if m[0] == "GSMARKT1"), True)
n.deliver(ans, "Testa")
check("N hat die Daten nach der Antwort", n.ev("GoldSentinelMarkt.Get(14047) ~= nil"), True)
# zweiter Antworter schweigt, wenn schon geantwortet wurde
b2 = Client("Testb2", 10)
b2.run("TIME = TIME + 2300")
set_auctions(b2, rows2)
scan(b2)
b2.deliver(n.sent(), "Testn")       # Frage
b2.deliver(ans, "Testa")            # Antwort von A kommt zuerst
b2.clear()
b2.tick(30)
check("zweiter Antworter schweigt", any(":A:H:" in m[1] for m in b2.sent() if m[0] == "GSMARKT1"), False)

# --- 11. ohne Auktionshaus-API: kein Fehler -----------------------------------------------------------------------------
x = Client("Testx", 11, no_ah=True)
x.lua.globals().FIRE("REPLICATE_ITEM_LIST_UPDATE")
x.tick(5)
check("ohne C_AuctionHouse: nichts gelesen, kein Fehler", x.ev("GoldSentinelMarkt.Stats().scans"), 0)
check("DiagLines ohne Fehler", x.ev("#GoldSentinelMarkt.DiagLines()"), 4)

# --- 12. Liste ändert sich während des Lesens -> Abbruch ---------------------------------------------------------------
y = Client("Testy", 12)
set_auctions(y, rows1 * 20)
for _ in range(5):
    y.lua.globals().FIRE("REPLICATE_ITEM_LIST_UPDATE")
y.tick(2.1)
y.run("UPDATE(0.1)")
set_auctions(y, rows1)
y.tick(3)
check("Abbruch bei geänderter Liste", y.ev("GoldSentinelMarkt.Stats().aborted"), 1)

# --- 13. Übernahme durch eine neuere Fassung ---------------------------------------------------------------------------
z = Client("Testz", 13)
set_auctions(z, rows1)
scan(z)
z.run(SRC.replace("local VERSION = 3", "local VERSION = 4"))
check("neuere Fassung aktiv", z.ev("GoldSentinelMarkt.VERSION"), 4)
check("Daten übernommen", z.ev("GoldSentinelMarkt.Get(2589).preis"), 95)
check("alter Frame still", z.ev("FRAMES[#FRAMES - 1].scripts.OnUpdate == nil"), True)
z.run(SRC)                     # ältere Fassung lädt danach -> bleibt bei 4
check("ältere Fassung übernimmt nicht", z.ev("GoldSentinelMarkt.VERSION"), 4)

# --- 14. Feed: Host-Addon liest selbst und gibt weiter, kein zweites Lesen ---------------------------------------------
h = Client("Testh", 14)
set_auctions(h, rows1)
h.run('GoldSentinelMarkt.FeedStart("ProbeAddon")')
scan(h)                        # Ereignisse des eigenen Scans des Hosts
check("Feed: Scan nicht selbst gelesen", h.ev("GoldSentinelMarkt.Stats().scans"), 0)
h.run('''GoldSentinelMarkt.Feed("ProbeAddon", TIME, 81, {
  [2589] = { preis = 95, menge = 1400, n = 70, abg = 22, abgV = 20 },
  [14047] = { preis = 99, menge = 1, n = 1, abg = 0, abgV = 0 } }, 2400)''')
gh = h.ev("GoldSentinelMarkt.Get(2589)")
check("Feed übernommen", (gh.preis, gh.menge, gh.n, gh.quelle), (95, 1400, 70, "eigen"))
check("Feed: Absatz Unter-/Obergrenze", (round(gh.absatz), round(gh.absatzMax)), (round(20 * 86400 / 2400), round(22 * 86400 / 2400)))
check("Feed gezählt", h.ev("GoldSentinelMarkt.Stats().fed"), 1)
check("Feed: Export", h.ev("DB.gsMarkt.export[1]").startswith("GSMARKT1|1|H|"), True)
h.tick(30)
check("Feed: an die Gilde gesendet", any(m[2] == "GUILD" and ":S:H:" in m[1] for m in h.sent() if m[0] == "GSMARKT1"), True)
h.run("NOW = NOW + 400")
scan(h)                        # später ein fremder Scan: wieder selbst lesen
check("nach Ablauf des Feeds wieder selbst gelesen", h.ev("GoldSentinelMarkt.Stats().scans"), 2)
h2 = Client("Testh2", 15)
h2.run('GoldSentinelMarkt.Feed("FremdesAddon", TIME, 1, { [1] = { preis = 1, menge = 1, n = 1 } }, 0)')
check("Feed nur von angemeldeten Addons", h2.ev("GoldSentinelMarkt.Get(1)"), None)

# --- 15. Version 2: AHSentinel geladen -> nicht selbst lesen; Schalter aus leert die Warteschlange; Gilde nur Änderungen
v = Client("Testv", 16)
v.run('C_AddOns = { IsAddOnLoaded = function(n) return n == "AHSentinel" end }')
set_auctions(v, rows1)
scan(v)
check("AHSentinel geladen: nicht selbst gelesen", v.ev("GoldSentinelMarkt.Stats().scans"), 0)
check("AHSentinel geladen: gezählt", v.ev("GoldSentinelMarkt.Stats().dropped['ahsentinel liest selbst']"), 1)
w = Client("Testw", 17)
set_auctions(w, rows1)
scan(w)
check("Warteschlange gefüllt", w.ev("#GoldSentinelMarkt.outbox") + len([m for m in w.sent() if m[0] == "GSMARKT1"]) > 0, True)
w.run('GoldSentinelMarkt.outbox[#GoldSentinelMarkt.outbox + 1] = { "S:H:1:1,1,1,1", {} }')
w.run('GoldSentinelMarkt.SetShare("ProbeAddon", false)')
w.clear()
w.tick(5)
check("Schalter aus: Warteschlange geleert", w.ev("#GoldSentinelMarkt.outbox"), 0)
check("Schalter aus: nichts gesendet", [m for m in w.sent() if m[0] == "GSMARKT1"], [])
w.run('GoldSentinelMarkt.SetShare("ProbeAddon", true)')
w.tick(60)
w.clear()
w.run("TIME = TIME + 1200")
set_auctions(w, rows1 + [(14047, 1, 50, 3)])          # nur 14047 billiger
scan(w)
w.tick(30)
g2m = [m for m in w.sent() if m[0] == "GSMARKT1" and m[2] == "GUILD" and ":S:H:" in m[1]]
check("innerhalb einer Stunde nur Änderungen an die Gilde", (len(g2m), "2589" in "".join(m[1] for m in g2m)), (1, False))
check("Sync-Warteschlange höchstens 10 durch GSMarkt", w.ev("GoldSentinelMarkt.QUEUE_HIGH"), 10)

# --- 16. Base36 und Packen ----------------------------------------------------------------------------------------------
check("Base36 hin und zurück", z.ev("GoldSentinelMarkt.Dec(GoldSentinelMarkt.Enc(2147483647))"), 2147483647)


# v3: Export hält höchstens 6 Scans und höchstens 1,5 MB zusammen (Ruckeln/SavedVariables klein halten)
trc = Client("Testtr", 21)
tr = trc.lua
tr.execute("L = {} for i = 1, 9 do L[#L+1] = 'scan' .. i end GoldSentinelMarkt.TrimExport(L)")
check("Export: höchstens 6 Scans, die neuesten", (tr.eval("#L"), tr.eval("L[1]"), tr.eval("L[6]")), (6, "scan4", "scan9"))
tr.execute("B = {} for i = 1, 4 do B[#B+1] = string.rep('x', 600 * 1024) end GoldSentinelMarkt.TrimExport(B)")
check("Export: höchstens 1,5 MB zusammen", tr.eval("#B"), 2)
tr.execute("C = { string.rep('y', 2 * 1024 * 1024) } GoldSentinelMarkt.TrimExport(C)")
check("Export: neuester Scan bleibt immer", tr.eval("#C"), 1)
check("Version 3", tr.eval("GoldSentinelMarkt.VERSION"), 3)

print(f"{checks - fails}/{checks} Prüfungen bestanden")
sys.exit(1 if fails else 0)
