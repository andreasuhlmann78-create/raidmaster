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
        self.lua.execute("DEFAULT_CHECK = GoldSentinelMarkt.CHECK_EVERY")   # v10: Zeitmessungen mit der echten Einstellung
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
check("DiagLines ohne Fehler (v8: + Zeile Test-IDs)", x.ev("#GoldSentinelMarkt.DiagLines()"), 5)

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
z.run(SRC.replace("local VERSION = 10", "local VERSION = 11"))
check("neuere Fassung aktiv", z.ev("GoldSentinelMarkt.VERSION"), 11)
check("Daten übernommen", z.ev("GoldSentinelMarkt.Get(2589).preis"), 95)
check("alter Frame still", z.ev("FRAMES[#FRAMES - 1].scripts.OnUpdate == nil"), True)
z.run(SRC)                     # ältere Fassung lädt danach -> bleibt bei 11
check("ältere Fassung übernimmt nicht", z.ev("GoldSentinelMarkt.VERSION"), 11)

# --- 14. Feed: Host-Addon liest selbst und gibt weiter, kein zweites Lesen ---------------------------------------------
h = Client("Testh", 14)
set_auctions(h, rows1)
h.run('GoldSentinelMarkt.FeedStart("ProbeAddon")')
scan(h)                        # Ereignisse des eigenen Scans des Hosts
check("Feed: Scan nicht selbst gelesen", h.ev("GoldSentinelMarkt.Stats().scans"), 0)
h.run('''GoldSentinelMarkt.Feed("ProbeAddon", TIME, 81, {
  [2589] = { preis = 95, menge = 1400, n = 70, abg = 22, abgV = 20 },
  [14047] = { preis = 99, menge = 1, n = 1, abg = 0, abgV = 0 } }, 2400)''')
check("v5: Feed nur angenommen, noch nicht gerechnet", h.ev("GoldSentinelMarkt.Get(2589) == nil and GoldSentinelMarkt.feedJob ~= nil"), True)
h.tick(0.2)
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
check("Version 10", tr.eval("GoldSentinelMarkt.VERSION"), 10)
check("v10: Zeitprüfung alle 20 Einträge (nicht 100)", tr.eval("DEFAULT_CHECK"), 20)

# v4 (MN-S2): geplante Antwort "A:" geht nach dem Ausschalten nicht mehr raus (Tick und SetShare)
for i, via in enumerate(("tick", "setshare")):
    c = Client("Testms" + str(i), 30 + i)
    c.run('DBM = {}; GoldSentinelMarkt.Attach("MSAddon", DBM)')
    c.run("GoldSentinelMarkt.answerAt = GoldSentinelMarkt.api.now() + 1; GoldSentinelMarkt.answerT = 1")
    if via == "tick":
        c.run('DBM.gsMarktAus = true')          # Schalter aus, ohne SetShare (anderes Addon)
    else:
        c.run('GoldSentinelMarkt.SetShare("MSAddon", false)')
    c.clear()
    c.tick(30)
    check("aus: keine Antwort A (" + via + ")", any(":A:" in m[1] for m in c.sent() if m[0] == "GSMARKT1"), False)
    check("aus: answerAt verworfen (" + via + ")", c.ev("GoldSentinelMarkt.answerAt"), None)


# v5: Feed in Portionen (≤ BUDGET_MS je Bild), Abgänge nur für Items mit abg, Export in zwei Zeilen, nichts verloren
fc = Client("Testfp", 40)
fc.run('DBF = {}; GoldSentinelMarkt.Attach("AHSentinel", DBF)')
fc.run("""
ITEMS = {}
for i = 1, 6000 do
  if i % 2 == 0 then ITEMS[100000 + i] = { preis = 100 + i, menge = 5, n = 2, abg = 3, abgV = 2 }
  else ITEMS[100000 + i] = { preis = 100 + i, menge = 5, n = 2 } end
end
GoldSentinelMarkt.Feed("AHSentinel", TIME, 12000, ITEMS, 1800)
""")
check("v5: Feed kehrt sofort zurück (nichts gerechnet)", fc.ev("GoldSentinelMarkt.feedJob.i"), 0)
fc.run("PORTIONS = 0; MAXMS = 0")
for _ in range(200):
    fc.run("""
local j = GoldSentinelMarkt.feedJob
if j then
  local before = MSCLOCK
  GoldSentinelMarkt.FeedPortion(GoldSentinelMarkt.BUDGET_MS)
  PORTIONS = PORTIONS + 1
  local used = MSCLOCK - before
  if used > MAXMS then MAXMS = used end
end""")
    if fc.ev("GoldSentinelMarkt.feedJob") is None:
        break
check("v5: Feed fertig gerechnet", fc.ev("GoldSentinelMarkt.feedJob"), None)
check("v5: in mehreren Portionen", fc.ev("PORTIONS") > 5, True)
check("v5: keine Portion über Budget + 2 Prüfschritte", fc.ev("MAXMS") <= fc.ev("GoldSentinelMarkt.BUDGET_MS") + 2, True)
ga = fc.ev("GoldSentinelMarkt.Get(100002)")
gb = fc.ev("GoldSentinelMarkt.Get(100001)")
check("v5: Item mit abg hat Absatz", (gb is not None, ga is not None, round(ga.absatzMax)), (True, True, round(3 * 86400 / 1800)))
check("v5: Item ohne abg hat KEINEN Absatz 0 (unbekannt)", (gb.absatz, gb.absatzMax), (None, None))
ex = [fc.ev("GoldSentinelMarkt.store.export[%d]" % i) for i in range(1, fc.ev("#GoldSentinelMarkt.store.export") + 1)]
check("v5: zwei Export-Zeilen", len(ex), 2)
pa, pb = ex[0].split("|"), ex[1].split("|")
check("v5: Zeile A mit Vergleich, 3000 Items", (pa[3], pa[5], pa[6]), (str(fc.ev("TIME")), "3000", "1800"))
check("v5: Zeile B ohne Vergleich, t+1, 3000 Items", (pb[3], pb[5], pb[6]), (str(fc.ev("TIME") + 1), "3000", "0"))
import importlib.util as _iu
_spec = _iu.spec_from_file_location("market", str(ROOT / "RaidMasterBot/market.py"))
_mk = _iu.module_from_spec(_spec); _spec.loader.exec_module(_mk)
pA, pB = _mk.parse_line(ex[0]), _mk.parse_line(ex[1])
check("v5: Sammelstelle liest beide Zeilen", (pA is not None, pB is not None, len(pA["e"]), len(pB["e"])), (True, True, 3000, 3000))
check("v5: verschiedene Schlüssel (nicht doppelt)", _mk.Store.key(pA) != _mk.Store.key(pB), True)
# zweiter Feed während der erste läuft: erster wird zu Ende gerechnet
fc2 = Client("Testfp2", 41)
fc2.run('DBF = {}; GoldSentinelMarkt.Attach("AHSentinel", DBF)')
fc2.run("""
local A, B = {}, {}
for i = 1, 3000 do A[200000 + i] = { preis = 50, menge = 1, n = 1 } end
for i = 1, 10 do B[300000 + i] = { preis = 70, menge = 1, n = 1 } end
GoldSentinelMarkt.Feed("AHSentinel", TIME, 3000, A, 0)
GoldSentinelMarkt.FeedPortion(GoldSentinelMarkt.BUDGET_MS)
GoldSentinelMarkt.Feed("AHSentinel", TIME + 900, 10, B, 0)
""")
check("v5: erster Feed vollständig vor dem zweiten", fc2.ev("GoldSentinelMarkt.Get(203000) ~= nil and GoldSentinelMarkt.Stats().scans"), 1)
fc2.tick(0.5)
check("v5: zweiter Feed danach", (fc2.ev("GoldSentinelMarkt.Get(300010).preis"), fc2.ev("GoldSentinelMarkt.Stats().scans")), (70, 2))
check("v5: dt 0 = eine Zeile", fc2.ev("#GoldSentinelMarkt.store.export"), 2)
# Kampf: kein Rechnen; Schalter aus: Feed wird nicht angenommen
fc3 = Client("Testfp3", 42)
fc3.run('DBF = {}; GoldSentinelMarkt.Attach("AHSentinel", DBF)')
fc3.run('COMBAT = true; GoldSentinelMarkt.Feed("AHSentinel", TIME, 1, { [5] = { preis = 9, menge = 1, n = 1 } }, 0)')
fc3.tick(1)
check("v5: im Kampf nicht gerechnet", fc3.ev("GoldSentinelMarkt.Get(5)"), None)
fc3.run("COMBAT = false"); fc3.tick(0.2)
check("v5: nach dem Kampf gerechnet", fc3.ev("GoldSentinelMarkt.Get(5).preis"), 9)
fc3.run('GoldSentinelMarkt.SetShare("AHSentinel", false); GoldSentinelMarkt.Feed("AHSentinel", TIME, 1, { [6] = { preis = 9, menge = 1, n = 1 } }, 0)')
check("v5: Schalter aus = kein Feed", fc3.ev("GoldSentinelMarkt.feedJob"), None)


# v6: Enc gleich wie vorher (Base36), Speicher-Müll beim Feed gemessen (6000 Items, 2. Feed): höchstens 3 MB
import random as _r
_r.seed(5)
encs = [0, 1, 35, 36, 1295, 1296, 2147483647] + [_r.randint(0, 10**9) for _ in range(200)]
def _b36(n):
    if n <= 0: return "0"
    d = "0123456789abcdefghijklmnopqrstuvwxyz"; s = ""
    while n: n, r = divmod(n, 36); s = d[r] + s
    return s
check("v6: Enc wie Base36 (207 Werte)", all(trc.lua.eval("GoldSentinelMarkt.Enc(%d)" % n) == _b36(n) for n in encs), True)
mc = Client("Testmem", 50)
mc.run('DBF = {}; GoldSentinelMarkt.Attach("AHSentinel", DBF)')
mc.run("""
ITEMS = {}
for i = 1, 6000 do ITEMS[100000 + i] = { preis = 100 + i, menge = 5, n = 2, abg = (i % 2 == 0) and 3 or nil, abgV = 2 } end
GoldSentinelMarkt.Feed("AHSentinel", TIME, 12000, ITEMS, 1800)
while GoldSentinelMarkt.feedJob do GoldSentinelMarkt.FeedPortion(4) end
collectgarbage("collect"); collectgarbage("stop"); M0 = collectgarbage("count")
GoldSentinelMarkt.Feed("AHSentinel", TIME + 1200, 12000, ITEMS, 1200)
while GoldSentinelMarkt.feedJob do GoldSentinelMarkt.FeedPortion(4) end
NEU = collectgarbage("count") - M0; collectgarbage("restart")
""")
neu = mc.ev("NEU")
print("v6 Feed 6000 Items: neu angelegt %.0f KB" % neu)
check("v6: Feed 6000 Items legt höchstens 3 MB an (v5: 6,6 MB)", neu <= 3072, True)
g6 = mc.ev("GoldSentinelMarkt.Get(100002)")
check("v6: Werte nach 2 Feeds (Absatz aus 2 Vergleichen)", (g6.preis, round(g6.absatzMax)), (100002 - 100000 + 100, round(6 * 86400 / 3000)))


# v7: volles Teilen an die Gilde (hoechstens 1x je Stunde) ohne Hilfstabellen; Ergebnis gleich, Speicher-Muell klein
mc7 = Client("Testmem7", 51)
mc7.run('DBF = {}; GoldSentinelMarkt.Attach("AHSentinel", DBF)')
mc7.run("""
math.randomseed(7)
ITEMS = {}
for i = 1, 6108 do ITEMS[2000 + i*3] = { preis = math.random(5, 2000000), menge = math.random(1,200), n = math.random(1,40), abg = (i % 2 == 0) and math.random(0,30) or nil, abgV = 2 } end
GoldSentinelMarkt.Feed("AHSentinel", TIME, 21102, ITEMS, 1800)
while GoldSentinelMarkt.feedJob do GoldSentinelMarkt.FeedPortion(4) end
while GoldSentinelMarkt.queueJobs[1] do GoldSentinelMarkt.QueuePortion(4) end   -- v9: Teilen in Portionen
N1 = #GoldSentinelMarkt.outbox
GoldSentinelMarkt.lastFull = nil
collectgarbage("collect"); collectgarbage("stop"); M0 = collectgarbage("count")
GoldSentinelMarkt.Feed("AHSentinel", TIME + 1200, 21102, ITEMS, 1200)
while GoldSentinelMarkt.feedJob do GoldSentinelMarkt.FeedPortion(4) end
while GoldSentinelMarkt.queueJobs[1] do GoldSentinelMarkt.QueuePortion(4) end
NEU7 = collectgarbage("count") - M0; collectgarbage("restart")
N2 = #GoldSentinelMarkt.outbox - N1
local f = GoldSentinelMarkt.store.f
local fac = next(f)
local id, v = next(f[fac].i)
E1 = GoldSentinelMarkt.EntryFromText(id, v)
local e = GoldSentinelMarkt.Unpack(v)
E2 = GoldSentinelMarkt.Enc(id) .. "," .. GoldSentinelMarkt.Enc(e.p) .. "," .. GoldSentinelMarkt.Enc(e.q) .. "," .. GoldSentinelMarkt.Enc(e.n)
""")
neu7 = mc7.ev("NEU7")
print("v7 Feed 6108 Items mit vollem Teilen: neu angelegt %.0f KB" % neu7)
check("v7: Feed mit vollem Teilen höchstens 3,5 MB (v6: 7,5 MB; Grenze AHS 4 MB)", neu7 <= 3584, True)
check("v7: volles Teilen schickt alle Items (Nachrichten > 600)", mc7.ev("N2") > 600, True)
check("v7: Eintrag aus dem Text = Eintrag aus den Werten", mc7.ev("E1"), mc7.ev("E2"))
check("v7: Export-Zeile beginnt mit dem Kopf", mc7.ev('GoldSentinelMarkt.store.export[#GoldSentinelMarkt.store.export]:sub(1, 11)'), "GSMARKT1|1|")

# v8 (SANDBOX-2): Test-IDs (ab 990000000) nie annehmen, speichern, exportieren, senden; beim Anmelden aus dem Speicher entfernen
import subprocess as _sp
OLD7 = _sp.run(["git", "-C", str(ROOT), "show", "07ba5716:shared/GoldSentinelMarkt.lua"], capture_output=True, text=True).stdout
FEED8 = """
ITEMS = {}
for i = 1, 1050 do ITEMS[990018000 + i] = { preis = 1, menge = 1, n = 1 } end
ITEMS[2589] = { preis = 500, menge = 4, n = 2 }
GoldSentinelMarkt.Feed("AHSentinel", TIME, 1052, ITEMS, 0)
while GoldSentinelMarkt.feedJob do GoldSentinelMarkt.FeedPortion(4) end
EX = table.concat(GoldSentinelMarkt.store.export, "\\n")
"""
def _testid_in(text):
    import re
    return any(990000000 <= int(t, 36) <= 999999999 for t in re.findall(r"(?:^|[|;])([0-9a-z]{6,}),", text))
for name, src, want in (("v8", None, False), ("Gegenprobe v7", OLD7, True)):
    c8 = Client("Testv8" + name[:2], 61, src=src)
    c8.run('DBF = {}; GoldSentinelMarkt.Attach("AHSentinel", DBF)')
    c8.run(FEED8)
    check(name + ": Feed – Test-ID im Speicher", c8.ev("GoldSentinelMarkt.Get(990018001) ~= nil"), want)
    check(name + ": Feed – Test-ID im Export", _testid_in(c8.ev("EX")), want)
    check(name + ": Feed – echtes Item bleibt", c8.ev("GoldSentinelMarkt.Get(2589).preis"), 500)
    c8.tick(5)                          # v9: Teilen in Portionen (Nachbau-Uhr: jeder Zeitaufruf +1 ms)
    msgs = [m for m in c8.sent() if m[0] == "GSMARKT1"]
    import re as _re
    sent_ids = [int(t, 36) for m in msgs for t in _re.findall(r"[:;]([0-9a-z]+),[0-9a-z]+,[0-9a-z]+,[0-9a-z]+(?=;|$)", m[1])]
    check(name + ": Feed – Nachrichten an die Gilde (echtes Item gesendet)", 2589 in sent_ids, True)
    check(name + ": Feed – Test-ID gesendet", any(x >= 990000000 for x in sent_ids), want)
c8 = Client("Testv8b", 62)
check("v8: Feed – Test-IDs gezählt (verworfen)", c8.ev('GoldSentinelMarkt.Stats().dropped["test-id"]'), None)
c8.run('DBF = {}; GoldSentinelMarkt.Attach("AHSentinel", DBF)')
c8.run(FEED8)
check("v8: Feed – 1050 Test-IDs verworfen (gezählt)", c8.ev('GoldSentinelMarkt.Stats().dropped["test-id"]'), 1050)
check("v8: Feed – Export-Kopf zählt nur das echte Item", c8.ev("EX").split("|")[5], "1")
# Empfang: eine Nachricht eines aelteren Clients mit Test-ID wird nicht angenommen, das echte Item schon
e = lambda n: c8.ev("GoldSentinelMarkt.Enc(%d)" % n)
msg = "S:H:%s:%s,1,1,1;%s,%s,1,1" % (e(c8.ev("TIME") + 10), e(990018005), e(4444), e(77))
c8.run('GoldSentinelMarkt.OnMessage("%s", "Andere")' % msg)
check("v8: Empfang – Test-ID nicht angenommen", c8.ev("GoldSentinelMarkt.Get(990018005)"), None)
check("v8: Empfang – echtes Item angenommen", c8.ev("GoldSentinelMarkt.Get(4444).preis"), 77)
# Aufräumen beim Anmelden: Speicher wie in BuffSentinel.lua (1050 Test-Items + echte), Export rein-Test, gemischt, sauber
cp = Client("Testv8p", 63)
cp.run("""
local E = GoldSentinelMarkt.Enc
local i = {}
for k = 1, 1050 do i[990018000 + k] = "1,1,1,tol2yb,0,0,0,0" end
i[2589] = "dw,4,2,tol2yb,0,0,0,0"
local pure, mixed = {}, { E(2589) .. ",dw,4,2,0,0" }
for k = 1, 1050 do pure[k] = E(990018000 + k) .. ",1,1,1,0,0" end
for k = 1, 3 do mixed[#mixed + 1] = E(999990117 + k) .. ",1,1,5,0,0" end
DBP = { gsMarkt = { f = { H = { t = 1794813492, i = i }, A = { t = 1, i = { [999990118] = "1,1,1,1,0,0,0,0", [25] = "2,1,1,1,0,0,0,0" } } },
  export = { "GSMARKT1|1|H|1794813492|1050|1050|0|" .. table.concat(pure, ";"),
             "GSMARKT1|1|H|1794813600|40|4|0|" .. table.concat(mixed, ";"),
             "GSMARKT1|1|H|1794813700|2|1|0|" .. E(2589) .. ",dw,4,2,0,0",
             "GSMARKT1|1|H|1794813800|0|0|0|" } } }
SAUBER = DBP.gsMarkt.export[3]
LEER = DBP.gsMarkt.export[4]
GoldSentinelMarkt.Attach("BuffSentinel", DBP)
""")
cnt = lambda fac: cp.ev('(function() local n = 0 for _ in pairs(DBP.gsMarkt.f.%s.i) do n = n + 1 end return n end)()' % fac)
check("v8: Aufräumen – Horde: nur echtes Item übrig", (cnt("H"), cp.ev("DBP.gsMarkt.f.H.i[2589]")), (1, "dw,4,2,tol2yb,0,0,0,0"))
check("v8: Aufräumen – Allianz: Test-ID weg, echtes bleibt", (cnt("A"), cp.ev("DBP.gsMarkt.f.A.i[999990118]")), (1, None))
exl = [cp.ev("DBP.gsMarkt.export[%d]" % k) for k in range(1, cp.ev("#DBP.gsMarkt.export") + 1)]
check("v8: Aufräumen – reine Test-Zeile weg, 3 Zeilen bleiben", len(exl), 3)
check("v8: Aufräumen – gemischte Zeile: 1 Item, 40−15 = 25 Auktionen", exl[0].split("|")[4:6], ["25", "1"])
check("v8: Aufräumen – saubere und leere Zeile byte-gleich", (exl[1], exl[2]), (cp.ev("SAUBER"), cp.ev("LEER")))
check("v8: Aufräumen – keine Test-ID mehr im Export", any(_testid_in(x) for x in exl), False)
check("v8: Aufräumen – gezählt (1051 Items + 1053 Export)", cp.ev("GoldSentinelMarkt.Stats().testIds"), 1051 + 1053)
check("v8: Aufräumen – Sammelstelle liest die gemischte Zeile", len(_mk.parse_line(exl[0])["e"]), 1)
check("v8: Diagnose-Zeile Test-IDs", cp.ev("GoldSentinelMarkt.DiagLines()[5]"), "MARKT-NETZ Test-IDs entfernt: 2104")
cp.run("GoldSentinelMarkt.Attach('BuffSentinel', DBP)")
check("v8: zweites Anmelden – nichts mehr zu entfernen", cp.ev("GoldSentinelMarkt.Stats().testIds"), 2104)
# Tempo: Aufräumen eines grossen Speichers ohne Test-IDs (20000 Items, Export 1,5 MB)
import time as _t
ct = Client("Testv8t", 64)
ct.run("""
local i, parts = {}, {}
for k = 1, 20000 do i[k * 7] = "dw,4,2,tol2yb,0,0,0,0"; parts[k] = GoldSentinelMarkt.Enc(k * 7) .. ",dw,4,2,0,0" end
local line = "GSMARKT1|1|H|1794813700|40000|20000|0|" .. table.concat(parts, ";")
DBT = { gsMarkt = { f = { H = { t = 1, i = i } }, export = { line, line, line, line, line, line } } }
""")
_pt = []
for _ in range(3):                      # maschinenunabhängig (Entscheid T126): Median aus 3 Messungen, CPU-Zeit der Lua-Seite
    ct.run('collectgarbage("collect"); local t0 = os.clock(); GoldSentinelMarkt.PurgeTestIDs(DBT.gsMarkt); PT = (os.clock() - t0) * 1000')
    _pt.append(ct.ev("PT"))
dt_ms = sorted(_pt)[1]
print("v8 Aufräumen ohne Test-IDs (20000 Items, Export %d KB): Median %.1f ms (höchster %.1f ms, nur beim Laden)" % (ct.ev("#DBT.gsMarkt.export[1]") * 6 // 1024, dt_ms, max(_pt)))
check("v8: Aufräumen ohne Test-IDs unter 15 ms (Median aus 3)", dt_ms < 15, True)

# v9: Teilen in Portionen – echte Uhr (os.clock); kein Bild des Bausteins über Budget + 1 ms; Nachrichten byte-gleich wie v8
OLD8 = _sp.run(["git", "-C", str(ROOT), "show", "55542918:shared/GoldSentinelMarkt.lua"], capture_output=True, text=True).stdout
RUN9 = """
function debugprofilestop() return os.clock() * 1000 end
math.randomseed(9)
ITEMS = {}
for i = 1, 6000 do ITEMS[2000 + i*3] = { preis = math.random(5, 2000000), menge = math.random(1,200), n = math.random(1,40), abg = (i % 2 == 0) and math.random(0,30) or nil, abgV = 2 } end
-- Speicher wie nach vielen Netz-Empfängen: 14000 fremde Items dazu
local f = GoldSentinelMarkt.store
GoldSentinelMarkt.Feed("AHSentinel", TIME, 1, { [1] = { preis = 1, menge = 1, n = 1 } }, 0)
while GoldSentinelMarkt.feedJob do GoldSentinelMarkt.FeedPortion(4) end
if GoldSentinelMarkt.queueJobs then while GoldSentinelMarkt.queueJobs[1] do GoldSentinelMarkt.QueuePortion(4) end end
local fac = next(f.f)
for i = 1, 14000 do f.f[fac].i[500000 + i] = "dw,4,2,1,1,0,0,0" end
GoldSentinelMarkt.outbox = {}
GoldSentinelMarkt.lastFull = nil
MAXMS, FRAMES = 0, 0
local function frame()
  local t0 = os.clock()
  GoldSentinelMarkt.Tick()
  local ms = (os.clock() - t0) * 1000
  FRAMES = FRAMES + 1
  if ms > MAXMS then MAXMS = ms end
end
GoldSentinelMarkt.Feed("AHSentinel", TIME + 1200, 21102, ITEMS, 1200)
COMBAT = false
NOW = NOW + 1
for k = 1, 400 do
  frame()
  if not GoldSentinelMarkt.feedJob and not (GoldSentinelMarkt.queueJobs and GoldSentinelMarkt.queueJobs[1]) then break end
end
-- Antwort-Weg (volles Teilen ohne Item-Liste, 20000 Items im Speicher)
GoldSentinelMarkt.answerAt = NOW - 1
MAXA = 0
for k = 1, 400 do
  local t0 = os.clock(); GoldSentinelMarkt.Tick(); local ms = (os.clock() - t0) * 1000
  if ms > MAXA then MAXA = ms end
  if not (GoldSentinelMarkt.queueJobs and GoldSentinelMarkt.queueJobs[1]) then break end
end
OUT = {}
for i, m in ipairs(GoldSentinelMarkt.outbox) do OUT[i] = m[1] .. "#" .. ((m[2] and m[2].net) and "net" or "guild") end
OUTS = table.concat(OUT, "\\n")
"""
def run9(src):
    c = Client("Testv9", 71, src=src)
    c.run('DBF = {}; GoldSentinelMarkt.Attach("AHSentinel", DBF); GoldSentinelMarkt.Pump = function() end; GoldSentinelMarkt.CHECK_EVERY = DEFAULT_CHECK')
    c.run(RUN9)
    return c
import statistics as _st
c9s = [run9(None) for _ in range(3)]          # maschinenunabhängig (Entscheid T126): Median aus 3 Läufen
c9, c8o = c9s[0], run9(OLD8)
mf, ma = _st.median(x.ev("MAXMS") for x in c9s), _st.median(x.ev("MAXA") for x in c9s)
print("v9 längstes Bild Feed+Teilen Median %.1f ms (höchster %.1f; v8: %.1f ms), Antwort-Weg Median %.1f ms (höchster %.1f; v8: %.1f ms), %d Bilder"
      % (mf, max(x.ev("MAXMS") for x in c9s), c8o.ev("MAXMS"), ma, max(x.ev("MAXA") for x in c9s), c8o.ev("MAXA"), c9.ev("FRAMES")))
budget = c9.ev("GoldSentinelMarkt.BUDGET_MS")
# Grenze im Nachbau Budget + 2 ms (Messrauschen der Maschine bis ~1,5 ms gemessen, 25 Läufe); Ziel im Spiel ≤ 5 ms je Bild
check("v9: kein Bild über Budget + 2 ms (Feed + Teilen, 6000 Items, Median aus 3)", mf <= budget + 2, True)
check("v9: Antwort-Weg ohne Item-Liste (20000 Items) höchstens Budget + 2 ms (Median aus 3)", ma <= budget + 2, True)
check("v9: Gegenprobe v8 – Teilen am Stück über 5 ms", c8o.ev("MAXMS") > 5, True)
OLD9 = (ROOT / "shared/tests/variants/GoldSentinelMarkt-v9.lua").read_text(encoding="utf-8")
def _checks(src):
    """deterministisch: wie oft prüft eine Feed-Portion die Zeit bei 1000 Items (Budget nie erreicht)?"""
    c = Client("Testv10", 73, src=src)
    c.run('DBF = {}; GoldSentinelMarkt.Attach("AHSentinel", DBF); GoldSentinelMarkt.CHECK_EVERY = DEFAULT_CHECK')
    c.run("""local I = {} for i = 1, 1000 do I[5000 + i] = { preis = 10, menge = 1, n = 1 } end
GoldSentinelMarkt.Feed("AHSentinel", TIME, 1000, I, 0)
NCHK = 0
local real = GoldSentinelMarkt.api.ms
GoldSentinelMarkt.api.ms = function() NCHK = NCHK + 1; return 0 end
GoldSentinelMarkt.FeedPortion(4)
GoldSentinelMarkt.api.ms = real""")
    return c.ev("NCHK")
n10, n9 = _checks(None), _checks(OLD9)
print("v10 Zeitprüfungen je Feed-Portion mit 1000 Items: v10 %d, v9 %d" % (n10, n9))
check("v10: Feed prüft die Zeit mindestens alle 20 Items (1000 Items -> ≥ 50 Prüfungen); Gegenprobe v9 ≤ 12", (n10 >= 50, n9 <= 12), (True, True))
check("v9: Nachrichten byte-gleich wie v8 (Reihenfolge, Inhalt, Weg)", c9.ev("OUTS") == c8o.ev("OUTS") and len(c9.ev("OUTS")) > 1000, True)

# v9: eigenes Lesen (ohne AHSentinel) – Auswertung in Portionen: 20000 Auktionen, zweiter Scan mit Vergleich.
# Echte Uhr, Speicherbereinigung während der Messung aus (sie ist im Spiel global und gehört nicht dem Baustein).
# Maschinenunabhängig (Entscheid T126): Median der längsten Bilder aus 3 Läufen; höchster Wert als Auskunft.
import random as _rnd, hashlib as _hl, statistics as _st
def _read_run(src, seed):
    _rnd.seed(seed)
    c = Client("Testv9r", 72, src=src)
    rows = [(2000 + _rnd.randint(0, 5999) * 3, _rnd.randint(1, 20), _rnd.randint(100, 900000), _rnd.randint(1, 4)) for _ in range(20000)]
    set_auctions(c, rows)
    c.run('function debugprofilestop() return os.clock() * 1000 end; collectgarbage("stop"); GoldSentinelMarkt.CHECK_EVERY = DEFAULT_CHECK')
    c.run("""MAXT = 0
_U9 = UPDATE
function UPDATE(dt) local t0 = os.clock(); _U9(dt); local ms = (os.clock() - t0) * 1000; if ms > MAXT then MAXT = ms end end""")
    for _ in range(50): c.lua.globals().FIRE("REPLICATE_ITEM_LIST_UPDATE")
    c.tick(40)
    rows2 = rows[2000:] + [(2000 + _rnd.randint(0, 5999) * 3, _rnd.randint(1, 20), _rnd.randint(100, 900000), 4) for _ in range(1500)]
    set_auctions(c, rows2)
    c.run("TIME = TIME + 1200; NOW = NOW + 1200")
    for _ in range(50): c.lua.globals().FIRE("REPLICATE_ITEM_LIST_UPDATE")
    c.tick(40)
    c.run('collectgarbage("restart")')
    ex = "\n".join(c.ev("GoldSentinelMarkt.store.export[%d]" % i) for i in range(1, c.ev("#GoldSentinelMarkt.store.export") + 1))
    fi = c.ev("GoldSentinelMarkt.store.f.H.i")
    mem = repr(sorted((k, fi[k]) for k in fi.keys()))
    return c.ev("MAXT"), _hl.sha1((ex + mem).encode()).hexdigest(), c.ev("GoldSentinelMarkt.Stats().compared")
r9 = [_read_run(None, 5) for _ in range(3)]
r8 = _read_run(OLD8, 5)
m9 = _st.median(x[0] for x in r9)
print("v9 eigenes Lesen 20000 Auktionen: längstes Bild Median %.1f ms (höchster %.1f ms) – v8: %.1f ms" % (m9, max(x[0] for x in r9), r8[0]))
check("v9: eigenes Lesen – längstes Bild (Median aus 3) höchstens Budget + 2 ms", m9 <= budget + 2, True)
check("v9: eigenes Lesen – Gegenprobe v8 am Stück über 20 ms", r8[0] > 20, True)
check("v9: eigenes Lesen – Speicher und Export byte-gleich wie v8 (mit Vergleich)", (r9[0][1] == r8[1], r9[0][2], r8[2]), (True, 1, 1))

print(f"{checks - fails}/{checks} Prüfungen bestanden")
sys.exit(1 if fails else 0)
