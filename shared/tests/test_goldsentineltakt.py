"""Tests für shared/GoldSentinelTakt.lua (gemeinsamer Takt für Arbeit in Portionen) in Lua 5.1 (lupa).
Läuft mit: python3 -I shared/tests/test_goldsentineltakt.py

Geprüft wird (je Punkt mit Gegenprobe, wo sinnvoll): Portionen halten das Budget (nachgebaute Uhr, genau gerechnet),
Ergebnis und Rückgabewerte, nur eine Aufgabe je Bild (reihum), Treiber schläft ohne Aufgaben, Check ausserhalb einer Aufgabe
wirkungslos, Lua-5.1-Grenzen (pcall, xpcall, table.sort, gsub: keine Abgabe, gezählt; Metamethode/Iterator: lauter Fehler statt
stiller), zweite Sicherung "Abgabe gescheitert", PCall/Sliced (Abgabe durch, enter/leave je Stück, Ersatz-Zustand nie in fremden
Bildern, in pcall ohne Abgabe zu Ende), NoYield, Sleep/WaitFor, Zeitlimit, Kampfpause, Fehler in der Arbeit und in Rückrufen,
Abbrechen, Übernahme durch neuere Fassung (gemerkte Verweise bleiben gültig), ältere Fassung ändert nichts, Messwerte
(Grenzen 5/16/40 ms, längste Bilder sortiert), Zusammenfassung, Argumente mit Lücken, Stapel nur bei verbrauchtem Budget gelesen,
echte Uhr (Median aus 3 Läufen) gegen die Arbeit am Stück (Gegenprobe), keine Blizzard-Globale beschrieben.
"""
import statistics
import sys
from pathlib import Path

from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
SRC = (ROOT / "shared/GoldSentinelTakt.lua").read_text(encoding="utf-8")

MOCK = r"""
NOW = 1000          -- GetTime (Sekunden)
CLOCK = 0           -- debugprofilestop (ms), nur durch die Arbeit bewegt
COMBAT = false
FRAMES = {}
function CreateFrame()
  local f = { scripts = {} }
  function f:SetScript(k, fn) self.scripts[k] = fn end
  FRAMES[#FRAMES + 1] = f
  return f
end
function GetTime() return NOW end
function debugprofilestop() return CLOCK end
function InCombatLockdown() return COMBAT end
function WORK(ms) CLOCK = CLOCK + ms end
-- ein Bild des Spiels: OnUpdate aller Rahmen
function FRAME()
  for _, f in ipairs(FRAMES) do local u = f.scripts.OnUpdate; if u then u(f, 0.016) end end
end
function AWAKE() return GoldSentinelTakt.frame ~= nil and GoldSentinelTakt.frame.scripts.OnUpdate ~= nil end
"""

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("OK    " if ok else "FEHLER") + " " + name + ((" – " + str(detail)) if detail else ""))


def fresh(src=SRC):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    lua.execute(src)
    return lua


def run(lua, code):
    return lua.execute(code)


# ---------------------------------------------------------------- 1 Grundlagen
lua = fresh()
check("1a geladen, Version 2, global", run(lua, "return GoldSentinelTakt and GoldSentinelTakt.VERSION") == 2)
check("1b ohne Aufgabe schläft der Treiber", run(lua, "return AWAKE()") is False)
check("1c Check ausserhalb einer Aufgabe: false, kein Fehler", run(lua, "return GoldSentinelTakt.Check('x')") is False)
check("1d Sleep ausserhalb: false", run(lua, "return GoldSentinelTakt.Sleep(1)") is False)
check("1e WaitFor ausserhalb: sofort false", run(lua, "return GoldSentinelTakt.WaitFor(function() return false end, 5)") is False)
check("1f Start ohne fn: Fehler mit Text",
      "fn fehlt" in str(run(lua, "local ok, e = pcall(GoldSentinelTakt.Start, {}) return e")))

# ---------------------------------------------------------------- 2 Portionen halten das Budget (nachgebaute Uhr)
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local done, items = nil, 0
local job = T.Start({ name = "Liste", owner = "A", budget = 2, fn = function(n)
    for i = 1, n do WORK(0.3); items = items + 1; T.Check("i" .. i) end
    return "fertig", items
end, args = { 1000 }, onDone = function(j) done = j.state end })
local awake = AWAKE()
local frames, maxFrame = 0, 0
while job.state == "laeuft" and frames < 10000 do
  local c0 = CLOCK; FRAME(); frames = frames + 1
  if CLOCK - c0 > maxFrame then maxFrame = CLOCK - c0 end
end
return awake, job.state, done, job.result[1], job.result[2], job.result.n, frames, maxFrame, job.stats.frames, AWAKE(),
       job.stats.maxMs, job.stats.over[1]
""")
awake, st, done, r1, r2, rn, frames, maxf, sframes, awake2, smax, over5 = r
# Rechnung: je Bild wird geprüft, ob ms - Bildbeginn >= 2. Nach 7 Einträgen à 0,3 ms = 2,1 ms -> Abgabe. 1000 / 7 = 142,86 -> 143 Bilder
check("2a Treiber wach nach Start", awake is True)
check("2b fertig, onDone mit Zustand", st == "fertig" and done == "fertig", (st, done))
check("2c Rückgabewerte vollständig", r1 == "fertig" and r2 == 1000 and rn == 2, (r1, r2, rn))
check("2d Bilder genau gerechnet: ceil(1000/7) = 143", frames == 143 and sframes == 143, (frames, sframes))
check("2e längstes Bild = 7 × 0,3 = 2,1 ms (Budget + ein Eintrag)", abs(maxf - 2.1) < 1e-9 and abs(smax - 2.1) < 1e-9, (maxf, smax))
check("2f kein Bild über 5 ms", over5 == 0)
check("2g Treiber schläft nach dem Ende", awake2 is False)

# Budget-Grenzen
r = run(lua, r"""
local T = GoldSentinelTakt
local a = T.Start({ fn = function() end, budget = 100 }); local b = T.Start({ fn = function() end, budget = 0.01 })
local c = T.Start({ fn = function() end, budget = "x" }); local d = T.Start({ fn = function() end, timeout = 99999 })
local r = { a.budget, b.budget, c.budget, d.timeout }
for _ = 1, 10 do FRAME() end
return r[1], r[2], r[3], r[4], #T.jobs
""")
check("2h Budget auf 0,5–8 begrenzt, ungültig = 2, Zeitlimit höchstens 3600", r[:4] == (8, 0.5, 2, 3600), r)
check("2i alle vier fertig", r[4] == 0)

# ---------------------------------------------------------------- 3 Eine Aufgabe je Bild, reihum
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local log = {}
local function mk(tag) return function() for i = 1, 3 do log[#log + 1] = tag; WORK(3); T.Check() end end end
local a = T.Start({ name = "a", fn = mk("a") }); local b = T.Start({ name = "b", fn = mk("b") })
local per = {}
for f = 1, 10 do local n0 = #log; FRAME(); per[#per + 1] = #log - n0 end
return table.concat(log), table.concat(per, ","), a.state, b.state
""")
check("3a je Bild genau eine Aufgabe (reihum a,b,a,b …)", r[0] == "ababab" and r[2] == "fertig" and r[3] == "fertig", r)
check("3b je Bild höchstens eine Portion (1 Eintrag, da 3 ms > Budget)", r[1].startswith("1,1,1,1,1,1"), r[1])

# ---------------------------------------------------------------- 4 Lua-5.1-Grenzen
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local inner = {}
local job = T.Start({ name = "grenzen", fn = function()
    -- in pcall: über Budget, aber keine Abgabe möglich -> gezählt, weiter
    local ok, e = pcall(function() WORK(5); inner.pc = T.Check("im-pcall") end)
    inner.pcok = ok
    local ok2 = xpcall(function() WORK(5); inner.xp = T.Check("im-xpcall") end, function(m) return m end)
    inner.xpok = ok2
    local t = { 3, 1, 2 }
    table.sort(t, function(x, y) WORK(5); T.Check("sort"); return x < y end)
    inner.sorted = table.concat(t, ",")
    inner.g = ("abc"):gsub("%a", function(ch) WORK(5); T.Check("gsub"); return ch:upper() end)
    WORK(5); inner.free = T.Check("frei")       -- hier darf abgegeben werden
    return "ende"
end })
for _ = 1, 10 do FRAME() end
return job.state, inner.pc, inner.pcok, inner.xp, inner.xpok, inner.sorted, inner.g, inner.free, job.stats.blocked,
       table.concat(job.stats.blockedAt or {}, "|"), job.stats.yieldFailed
""")
st, pc, pcok, xp, xpok, sorted_, g, free, blocked, at, yf = r
check("4a pcall: keine Abgabe, pcall erfolgreich", pc is False and pcok is True, (pc, pcok))
check("4b xpcall: keine Abgabe, erfolgreich", xp is False and xpok is True, (xp, xpok))
check("4c table.sort-Vergleich: keine Abgabe, Ergebnis richtig", sorted_ == "1,2,3", sorted_)
check("4d gsub-Funktion: keine Abgabe, Ergebnis richtig", g == "ABC", g)
check("4e ausserhalb der Grenzen wird abgegeben", free is True)
check("4f gezählt mit Etikett und Grund", blocked >= 4 and "im-pcall (pcall)" in at and "im-xpcall (xpcall)" in at
      and "sort" in at and "gsub" in at, (blocked, at))
check("4g Aufgabe fertig, nichts gescheitert", st == "fertig" and yf == 0, (st, yf))

# Gegenprobe zu 4: Stapel-Erkennung aus -> Abgabe in pcall scheitert, pcall fängt sie (still) – zweite Sicherung meldet es
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
T.api.stack = function() return "" end
local inner = {}
local job = T.Start({ name = "gegenprobe", fn = function()
    local ok, e = pcall(function() WORK(5); T.Check("im-pcall") end)
    inner.ok, inner.e = ok, e
    T.Check("danach")
end })
for _ = 1, 5 do FRAME() end
return job.state, inner.ok, tostring(inner.e), job.stats.yieldFailed, table.concat(job.stats.yieldFailedAt or {}, "|")
""")
check("4h Gegenprobe: ohne Erkennung scheitert die Abgabe in pcall still (Lua-5.1-Fehler)",
      r[1] is False and "yield across" in r[2], r[:3])
check("4i zweite Sicherung meldet 'Abgabe gescheitert' mit Etikett", r[3] == 1 and r[4] == "im-pcall", r[3:])

# Metamethode / Iterator: nicht im Stapel sichtbar -> lauter Fehler (nicht still)
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local mt = setmetatable({}, { __index = function(t, k) WORK(5); T.Check("meta"); return 1 end })
local a = T.Start({ name = "meta", fn = function() return mt.x end })
local function it(s, i) i = i + 1; if i > 3 then return nil end; WORK(5); T.Check("iter"); return i end
local b = T.Start({ name = "iter", fn = function() for i in it, nil, 0 do end end })
for _ = 1, 6 do FRAME() end
return a.state, tostring(a.err), b.state, tostring(b.err)
""")
check("4j Check in Metamethode: Aufgabe 'fehler' mit Lua-Meldung (laut, nicht still)",
      r[0] == "fehler" and "yield across" in r[1], r[:2])
check("4k Check in Iterator-Funktion: 'fehler' mit Lua-Meldung", r[2] == "fehler" and "yield across" in r[3], r[2:])

# ---------------------------------------------------------------- 5 PCall / Sliced / NoYield
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local out = {}
local job = T.Start({ name = "pcall", fn = function()
    local f0 = 0
    local ok, a, b = T.PCall(function(x, y) for i = 1, 20 do WORK(1); T.Check("p" .. i) end return x + y, "z" end, 2, 3)
    out.ok, out.a, out.b = ok, a, b
    local ok2, e2 = T.PCall(function() WORK(3); T.Check("vor-fehler"); error("kaputt", 0) end)
    out.ok2, out.e2 = ok2, e2
    out.after = "weiter"
end })
local n = 0
while job.state == "laeuft" and n < 100 do FRAME(); n = n + 1 end
return job.state, out.ok, out.a, out.b, out.ok2, out.e2, out.after, job.stats.frames, job.stats.maxMs, job.stats.blocked
""")
check("5a PCall: Rückgabe wie pcall (true, 5, 'z')", r[1] is True and r[2] == 5 and r[3] == "z", r[1:4])
check("5b PCall: Fehler -> false, Meldung; Aufgabe läuft weiter", r[4] is False and r[5] == "kaputt" and r[6] == "weiter", r[4:7])
check("5c PCall gibt wirklich ab (20 ms Arbeit in mehreren Bildern, längstes ≤ 3 ms)",
      r[7] >= 8 and r[8] <= 3.0 + 1e-9 and r[9] == 0, (r[7], r[8], r[9]))

# Sliced: enter/leave je Stück, Ersatz-Zustand nie in einem fremden Bild
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
ENV = "echt"
local seenByOther, enters, leaves = {}, 0, 0
local a = T.Start({ name = "sliced", fn = function()
    return T.Sliced(function()
        local s = {}
        for i = 1, 12 do WORK(1); s[#s + 1] = ENV; T.Check("s" .. i) end
        return table.concat(s, ",")
    end, function() enters = enters + 1; ENV = "ersatz" end, function() leaves = leaves + 1; ENV = "echt" end)
end })
local b = T.Start({ name = "andere", fn = function() for i = 1, 12 do seenByOther[#seenByOther + 1] = ENV; WORK(1); T.Check() end end })
local n = 0
while (a.state == "laeuft" or b.state == "laeuft") and n < 100 do FRAME(); n = n + 1 end
local allErsatz = a.result[2]:gsub("ersatz", ""):gsub(",", "") == ""
local otherEcht = table.concat(seenByOther, ","):gsub("echt", ""):gsub(",", "") == ""
return a.state, a.result[1], allErsatz, otherEcht, enters, leaves, ENV, a.stats.frames
""")
check("5d Sliced: f sieht immer den Ersatz-Zustand", r[1] is True and r[2] is True, r[:3])
check("5e andere Aufgabe sieht nie den Ersatz-Zustand", r[3] is True)
check("5f enter/leave gleich oft und je Stück (> 1), danach echt", r[4] == r[5] and r[4] > 1 and r[6] == "echt", r[4:7])

# Sliced/PCall in pcall: kann nicht nach oben abgeben -> läuft ohne Abgabe zu Ende, gezählt
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local res = {}
local job = T.Start({ name = "gehalten", fn = function()
    local ok, inner_ok, v = pcall(function()
        return T.PCall(function() for i = 1, 10 do WORK(1); T.Check("h" .. i) end return 42 end)
    end)
    res.ok, res.inner, res.v = ok, inner_ok, v
end })
local n = 0
while job.state == "laeuft" and n < 50 do FRAME(); n = n + 1 end
return job.state, res.ok, res.inner, res.v, job.stats.blocked, job.stats.yieldFailed, job.noYield
""")
check("5g PCall in pcall: läuft zu Ende (true, true, 42), nichts gescheitert",
      r[0] == "fertig" and r[1] is True and r[2] is True and r[3] == 42 and r[5] == 0, r)
check("5h dabei 'Abgabe nicht möglich' gezählt, Sperre danach wieder 0", r[4] >= 1 and r[6] == 0, (r[4], r[6]))

# NoYield
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local res = {}
local job = T.Start({ name = "noyield", fn = function()
    local f0 = job_frames
    res.v = T.NoYield(function(a) for i = 1, 10 do WORK(1); assert(T.Check("n" .. i) == false) end return a * 2 end, 21)
    local ok, e = pcall(T.NoYield, function() error("x", 0) end)
    res.ok, res.e = ok, e
    WORK(3); res.after = T.Check("danach")
end })
local n = 0
while job.state == "laeuft" and n < 50 do FRAME(); n = n + 1 end
return job.state, res.v, res.ok, res.e, res.after, job.noYield
""")
check("5i NoYield: keine Abgabe, Rückgabe 42", r[0] == "fertig" and r[1] == 42, r[:2])
check("5j NoYield: Fehler weitergegeben, Zähler danach 0, danach wieder Abgabe", r[2] is False and r[3] == "x" and r[4] is True
      and r[5] == 0, r[2:])

# ---------------------------------------------------------------- 6 Sleep / WaitFor / Zeitlimit / Kampf
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local log = {}
local s = T.Start({ name = "schlaf", fn = function() log[#log + 1] = "s1"; T.Sleep(2); log[#log + 1] = "s2" end })
local o = T.Start({ name = "andere", fn = function() for i = 1, 4 do log[#log + 1] = "o"; WORK(3); T.Check() end end })
for _ = 1, 8 do FRAME() end
local before = table.concat(log, ",")
NOW = NOW + 2.5
for _ = 1, 4 do FRAME() end
return before, table.concat(log, ","), s.state, s.stats.sleepFrames
""")
check("6a Sleep: wartet ohne zu rechnen, die andere Aufgabe läuft weiter", r[0] == "s1,o,o,o,o", r[0])
check("6b nach Ablauf geht es weiter", r[1].endswith("s2") and r[2] == "fertig" and r[3] >= 1, r[1:])

lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local flag, res = false, {}
local a = T.Start({ name = "warte", fn = function() res.a = T.WaitFor(function() return flag end, 10) end })
local b = T.Start({ name = "warte-zeit", fn = function() res.b = T.WaitFor(function() return false end, 3) end })
local c = T.Start({ name = "warte-fehler", fn = function() res.c = T.WaitFor(function() error("p") end, 3) end })
for _ = 1, 3 do FRAME(); NOW = NOW + 0.5 end
flag = true
for _ = 1, 30 do FRAME(); NOW = NOW + 0.5 end
return res.a, res.b, res.c, a.state, b.state, c.state
""")
check("6c WaitFor: Bedingung erfüllt -> true", r[0] is True and r[3] == "fertig", r)
check("6d WaitFor: Zeit um -> false; Fehler in der Prüfung -> false", r[1] is False and r[2] is False and r[4] == "fertig"
      and r[5] == "fertig", r)

lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local endState
local job = T.Start({ name = "endlos", timeout = 5, fn = function() while true do WORK(3); T.Check() end end,
                      onDone = function(j) endState = j.state end })
for _ = 1, 3 do FRAME() end
NOW = NOW + 6
FRAME()
return job.state, tostring(job.err), endState, #T.jobs, AWAKE(), T.stats.timeouts
""")
check("6e Zeitlimit beendet eine endlose Aufgabe (keine Sperre ohne Zeitlimit)",
      r[0] == "zeitlimit" and "5" in r[1] and r[2] == "zeitlimit" and r[3] == 0 and r[4] is False and r[5] == 1, r)

lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local n = 0
local job = T.Start({ name = "kampf", pauseInCombat = true, fn = function() for i = 1, 5 do n = n + 1; WORK(3); T.Check() end end })
COMBAT = true
for _ = 1, 5 do FRAME() end
local inCombat = n
COMBAT = false
for _ = 1, 10 do FRAME() end
local other = T.Start({ name = "ohne-pause", fn = function() WORK(1) end })
COMBAT = true; FRAME(); COMBAT = false
return inCombat, n, job.state, job.stats.combatFrames, other.state
""")
check("6f Kampfpause: im Kampf kein Schritt, danach weiter", r[0] == 0 and r[1] == 5 and r[2] == "fertig" and r[3] == 5, r)
check("6g ohne pauseInCombat läuft es auch im Kampf", r[4] == "fertig", r[4])

# ---------------------------------------------------------------- 7 Fehler, Rückrufe, Abbrechen
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local a = T.Start({ name = "kaputt", fn = function() WORK(1); T.Check(); local x = nil; return x.y end })
local b = T.Start({ name = "gesund", fn = function() for i = 1, 3 do WORK(3); T.Check() end return "ok" end,
                    onDone = function() error("rückruf kaputt") end })
local c = T.Start({ name = "portion-kaputt", fn = function() WORK(1) end, onPortion = function() error("p") end })
local ok = pcall(function() for _ = 1, 20 do FRAME() end end)
return ok, a.state, tostring(a.err):find("index") ~= nil, a.trace ~= nil, b.state, b.result[1], tostring(b.cbError),
       c.state, T.stats.cbErrors, T.stats.failed
""")
check("7a Fehler in der Arbeit: 'fehler' mit Meldung und Stapel, Bild läuft weiter (kein Fehler nach aussen)",
      r[0] is True and r[1] == "fehler" and r[2] is True and r[3] is True, r[:4])
check("7b andere Aufgabe unberührt; Fehler im onDone gefangen", r[4] == "fertig" and r[5] == "ok" and "rückruf" in r[6], r[4:7])
check("7c Fehler in onPortion gefangen; Zähler stimmen", r[7] == "fertig" and r[8] == 2 and r[9] == 1, r[7:])

lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local mk = function(owner) return T.Start({ owner = owner, fn = function() while true do WORK(3); T.Check() end end }) end
local a1, a2, b1 = mk("A"), mk("A"), mk("B")
FRAME()
local runA = #T.Running("A")
local n = T.CancelOwner("A", "weg")
local self_
local s = T.Start({ owner = "C", fn = function() WORK(1); T.Cancel(self_, "selbst"); WORK(1); T.Check(); return "nie" end })
self_ = s
for _ = 1, 4 do FRAME() end
local again = T.Cancel(a1)
T.Cancel(b1)
return runA, n, a1.state, a2.state, a1.err, b1.state, s.state, s.err, s.result == nil, again, #T.jobs
""")
check("7d Running/CancelOwner: 2 von A abgebrochen, Grund gesetzt", r[0] == 2 and r[1] == 2 and r[2] == "abgebrochen"
      and r[3] == "abgebrochen" and r[4] == "weg", r[:5])
check("7e Selbst-Abbruch in der Arbeit: endet sofort, kein Ergebnis", r[6] == "abgebrochen" and r[7] == "selbst" and r[8] is True, r[6:9])
check("7f zweites Cancel = false; am Ende keine Aufgaben", r[9] is False and r[10] == 0 and r[5] == "abgebrochen", r[9:])

# ---------------------------------------------------------------- 8 Fassungen
OLD = (ROOT / "shared/tests/variants/GoldSentinelTakt-v1.lua").read_text(encoding="utf-8")
NEWER = SRC
assert "local VERSION = 1\n" in OLD and "local VERSION = 2\n" in SRC
lua = fresh(OLD)
r = run(lua, r"""
local cached = GoldSentinelTakt          -- ein Addon hat sich den Takt gemerkt
local n = 0
JOB = cached.Start({ name = "lang", fn = function() for i = 1, 20 do n = n + 1; WORK(3); cached.Check() end return "durch" end })
for _ = 1, 3 do FRAME() end
CACHED, NBEFORE = cached, n
""")
lua.execute(NEWER)
r = run(lua, r"""
local T = GoldSentinelTakt
for _ = 1, 40 do FRAME() end
return T == CACHED, T.VERSION, JOB.state, JOB.result[1], NBEFORE
""")
check("8a neuere Fassung (v1 -> v2): gleiche Tabelle (gemerkte Verweise gültig), Version 2", r[0] is True and r[1] == 2, r[:2])
check("8b laufende Aufgabe übernommen und zu Ende geführt", r[2] == "fertig" and r[3] == "durch" and r[4] == 3, r[2:])
lua.execute(OLD)
check("8c ältere Fassung danach ändert nichts", run(lua, "return GoldSentinelTakt.VERSION") == 2)
check("8d nur ein Treiber-Rahmen (kein zweiter)", run(lua, "return #FRAMES") == 1)

# ---------------------------------------------------------------- 9 Messwerte und Zusammenfassung
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
-- Bilder genau gebaut: Arbeit je Schritt 1, 6, 17, 41, 3 ms (jeder Schritt über Budget -> ein Bild je Schritt)
local costs = { 1, 6, 17, 41, 3 }
local job = T.Start({ name = "mess", fn = function()
    for i, c in ipairs(costs) do WORK(c); T.Check("S" .. i); if c < 2 then WORK(2); T.Check("S" .. i .. "b") end end
end })
for _ = 1, 20 do FRAME() end
local w = {}
for _, v in ipairs(job.stats.worst) do w[#w + 1] = v.at .. "=" .. v.ms end
return job.stats.frames, job.stats.maxMs, job.stats.maxAt, job.stats.over[1], job.stats.over[2], job.stats.over[3],
       table.concat(w, ","), job.stats.ownMs, T.Summary(job)
""")
frames, mx, mxat, o5, o16, o40, worst, own, summ = r
# Bilder: [1+2 (S1,S1b)] = 3 · [6] · [17] · [41] · [3] · [Rest bis zum Ende, 0 ms] -> 6 Bilder (nach der letzten Abgabe
# braucht es ein Bild, in dem die Arbeit endet); über 5: 6,17,41 = 3; über 16: 17,41 = 2; über 40: 41 = 1.
# Etikett eines Bildes: Etikett beim Beginn – Etikett beim Ende (erstes Bild beginnt ohne Etikett "-").
check("9a 6 Bilder, längstes 41 ms, Etikett S3–S4", frames == 6 and mx == 41 and mxat == "S3–S4", (frames, mx, mxat))
check("9b Grenzen gezählt: über 5 = 3, über 16 = 2, über 40 = 1", (o5, o16, o40) == (3, 2, 1), (o5, o16, o40))
check("9c längste Bilder absteigend mit Etikett (gleiche Dauer: frühere zuerst)",
      worst == "S3–S4=41,S2–S3=17,S1b–S2=6,-–S1b=3,S4–S5=3,S5=0", worst)
check("9d eigene Rechenzeit = Summe = 70 ms", own == 70, own)
check("9e Zusammenfassung nennt alles", "Portionen: 6 Bilder, längstes Bild 41.0 ms (S3–S4)" in summ
      and "über 5 ms: 3 · über 16 ms: 2 · über 40 ms: 1" in summ and "S3–S4 41.0 ms, S2–S3 17.0 ms" in summ
      and "eigene Rechenzeit 70.0 ms" in summ, summ)

lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local job = T.Start({ name = "viele", fn = function() for i = 1, 30 do WORK(i); T.Check("x" .. i) end end })
for _ = 1, 40 do FRAME() end
local w = job.stats.worst
local sorted = true
for i = 2, #w do if w[i].ms > w[i - 1].ms then sorted = false end end
return #w, sorted, w[1].ms, w[#w].ms
""")
check("9f höchstens 10 längste Bilder, sortiert, die grössten (30 … 21)", r == (10, True, 30, 21), r)

# ---------------------------------------------------------------- 10 Argumente, Stapel nur bei Bedarf, keine Globale
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
local got
local job = T.Start({ fn = function(a, b, c, d) got = { a, b, c, d } end, args = { n = 4, 1, nil, 3, nil } })
FRAME()
local calls = 0
local orig = T.api.stack
T.api.stack = function() calls = calls + 1; return orig() end
local j2 = T.Start({ fn = function() for i = 1, 1000 do WORK(0.001); T.Check() end end })
for _ = 1, 5 do FRAME() end
return got[1], got[2], got[3], got[4], calls, j2.state
""")
check("10a Argumente mit Lücken (n) vollständig", r[:4] == (1, None, 3, None), r[:4])
check("10b Stapel nur einmal beim Start (Eichung), unter dem Budget nie (1000 Checks)", r[4] == 1 and r[5] == "fertig", r[4:])

# ---------------------------------------------------------------- 12 Eichung: hängt das Spiel unter der Coroutine Zeilen an
WOWSTACK = r"""
local T = GoldSentinelTakt
local orig = T.api.stack
T.api.stack = function() return orig() .. "\n[C]: ?\n[C]: in function `resume'" end
"""
lua = fresh()
lua.execute(WOWSTACK)
r = run(lua, r"""
local T = GoldSentinelTakt
local res = {}
local job = T.Start({ name = "wow", fn = function()
    WORK(3); res.free = T.Check("frei")
    pcall(function() WORK(3); res.pc = T.Check("pc") end)
    res.sub = select(2, T.PCall(function() WORK(3); return T.Check("sub") end))
end })
for _ = 1, 10 do FRAME() end
return job.state, res.free, res.pc, res.sub, job.stats.blocked, T.extra[job.co]
""")
check("12a angehängte Zeilen unter der Coroutine: frei wird weiter abgegeben (auch in PCall)",
      r[0] == "fertig" and r[1] is True and r[3] is True, r)
check("12b pcall wird trotzdem erkannt (genau 1× nicht möglich)", r[2] is False and r[4] == 1, r)
lua = fresh()
lua.execute(WOWSTACK)
r = run(lua, r"""
local T = GoldSentinelTakt
T.Calibrate = function() end          -- Gegenprobe: ohne Eichung
local res = {}
local job = T.Start({ name = "wow-ohne", fn = function() WORK(3); res.free = T.Check("frei") end })
for _ = 1, 5 do FRAME() end
return res.free, job.stats.blocked
""")
check("12c Gegenprobe ohne Eichung: nie mehr abgegeben (alles 'nicht möglich')", r[0] is False and r[1] == 1, r)

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(MOCK)
before = set(lua.execute("local t = {} for k in pairs(_G) do t[#t + 1] = k end return table.concat(t, ',')").split(","))
lua.execute(SRC)
after = set(lua.execute("local t = {} for k in pairs(_G) do t[#t + 1] = k end return table.concat(t, ',')").split(","))
check("10c beim Laden nur GoldSentinelTakt neu in _G (keine Blizzard-Globale beschrieben)", after - before == {"GoldSentinelTakt"},
      after - before)
src_lines = [l for l in SRC.splitlines() if not l.strip().startswith("--")]
writes = [l for l in src_lines if ("_G." in l and "=" in l.split("_G.")[1].split("(")[0] and "==" not in l and "_G.GoldSentinelTakt = T" not in l
                                   and "local" not in l.split("_G.")[0][-12:])]
check("10d im Code keine Zuweisung an _G ausser GoldSentinelTakt", writes == [], writes)

# ---------------------------------------------------------------- 11 echte Uhr: Takt gegen Arbeit am Stück (Median aus 3)
REAL = r"""
CLOCKREAL = true
function debugprofilestop() return os.clock() * 1000 end
local function heavy(n) local s = 0 for i = 1, n do s = s + math.sin(i) * math.cos(i) end return s end
function NAIVE()
  local t0 = debugprofilestop(); local s = 0
  for k = 1, 400 do s = s + heavy(2000) end
  return debugprofilestop() - t0
end
function TAKT()
  local T = GoldSentinelTakt
  local job = T.Start({ name = "echt", budget = 2, fn = function()
      local s = 0 for k = 1, 400 do s = s + heavy(2000); T.Check("k" .. k) end return s end })
  local n = 0
  while job.state == "laeuft" and n < 100000 do T.Tick(); n = n + 1 end
  return job.stats.maxMs, job.stats.frames, job.state
end
"""
naive, takt = [], []
for _ in range(3):
    lua = fresh()
    lua.execute(REAL)
    naive.append(lua.execute("return NAIVE()"))
    mx, fr, st = lua.execute("return TAKT()")
    takt.append(mx)
    assert st == "fertig"
mn, mt = statistics.median(naive), statistics.median(takt)
step = mn / 400
check("11a Gegenprobe: Arbeit am Stück ist ein langes Bild (Median > 20 ms)", mn > 20, f"{mn:.1f} ms")
check("11b mit Takt: längstes Bild ≤ Budget + ein Schritt + 2 ms (Median aus 3)", mt <= 2 + step + 2,
      f"{mt:.2f} ms (Schritt {step:.2f} ms)")

# ---------------------------------------------------------------- 12 Version 2: ganze Bilder und Umgebung
lua = fresh()
r = run(lua, r"""
local T = GoldSentinelTakt
-- Bilder: eigene Portion 3 ms; ganze Bilder: 20, 80 (Spiel), 60 (Spiel), 30
local wholes = { 0.020, 0.080, 0.060, 0.030 }
local i = 0
local job = T.Start({ name = "ganz", fn = function() for k = 1, 5 do WORK(3); T.Check("k" .. k) end end })
local f = T.frame.scripts.OnUpdate
for _ = 1, 10 do i = i + 1; f(T.frame, wholes[i] or 0.016) end
return job.stats.whole, job.stats.wholeOver, job.stats.wholeForeign, job.stats.wholeMax, T.Summary(job)
""")
check("12a ganze Bilder gezählt: über 40 ms 2, beide Spiel/Umgebung (eigene 3 ms)", r[1] == 2 and r[2] == 2, r[:4])
check("12b längstes ganzes Bild 80 ms", abs(r[3] - 80) < 0.01, r[3])
check("12c Zusammenfassung nennt es", "ganze Bilder über 40 ms: 2, davon durch Spiel/Umgebung" in r[4], r[4])
r = run(lua, r"""
local T = GoldSentinelTakt
-- Gegenprobe: eigene Portion 45 ms, ganzes Bild 60 ms -> nicht Spiel/Umgebung
local job = T.Start({ name = "selbst", fn = function() WORK(45); T.Check("x"); WORK(1) end })
local f = T.frame.scripts.OnUpdate
f(T.frame, 0.016); f(T.frame, 0.060); f(T.frame, 0.016)
return job.stats.wholeOver, job.stats.wholeForeign
""")
check("12d Gegenprobe: eigene Portion 45 ms -> ganzes Bild zählt NICHT als Umgebung", r[0] == 1 and r[1] == 0, r)
r = run(lua, r"""
local T = GoldSentinelTakt
local job = T.Start({ name = "ohne", fn = function() WORK(1) end })
for _ = 1, 3 do FRAME() end
return job.stats.wholeOver, string.find(T.Summary(job), "ganze Bilder", 1, true) == nil
""")
check("12e ohne lange ganze Bilder: keine Zeile", r[0] == 0 and r[1] is True, r)

lua = fresh()
r = run(lua, r"""
function GetNetStats() return 1, 2, 180.4, 95.6 end
function GetFramerate() return 30 end
PLATES = 0
C_NamePlate = { GetNamePlates = function() local t = {} for k = 1, PLATES do t[k] = k end return t end }
function GetRealZoneText() return "Unterstadt" end
function GetSubZoneText() return "Handelsviertel" end
local T = GoldSentinelTakt
T.api.mem = function() return MEM end
MEM = 1000
local got
T.EnvMeasure(2, function(e) got = e end)
local f = T.envFrame.scripts.OnUpdate
local steps = { 0.030, 0.034, 0.120, 0.033 }
for k = 1, 4 do PLATES = 10 * k; if k == 3 then MEM = 500 end; f(T.envFrame, steps[k]); NOW = NOW + 0.5 end
NOW = NOW + 1; f(T.envFrame, 0.032)
return got ~= nil, T.env and T.env.plates, T.env and T.env.n, T.env and T.env.max, T.env and T.env.gc, T.EnvLine(),
       T.envFrame.scripts.OnUpdate == nil
""")
check("12f Umgebung gemessen und Rückruf", r[0] is True, r)
check("12g Spieler in Sicht = Höchstwert 40, 5 Bilder, längstes 120 ms, 1 Bereinigung", r[1] == 40 and r[2] == 5 and abs(r[3] - 120) < 0.01 and r[4] == 1, r[1:5])
check("12h Zeile: Ort, Ping, Ruhe-Bildzeit", "Umgebung: Unterstadt (Handelsviertel)" in r[5] and "Ping Realm 180 ms / Welt 96 ms" in r[5]
      and "Bild in Ruhe Median" in r[5] and "40 Namensplaketten" in r[5], r[5])
check("12i Messrahmen schläft danach", r[6] is True)
lua = fresh()
check("12j ohne Messung: Zeile leer", run(lua, "return GoldSentinelTakt.EnvLine()") == "")
r = run(lua, r"""
local T = GoldSentinelTakt
local ran = false
local job = T.Start({ name = "mitenv", env = 1, fn = function() ran = true end })
for _ = 1, 3 do FRAME() end
local before = ran
NOW = NOW + 2
for _ = 1, 10 do NOW = NOW + 0.5; FRAME() end
return before, ran, job.state, T.env ~= nil
""")
check("12k Start mit env: Arbeit erst nach der Messung", r[0] is False and r[1] is True and r[2] == "fertig" and r[3] is True, r)
r = run(lua, r"""
local G = {}
for k, v in pairs(_G) do G[k] = v end
GoldSentinelTakt.EnvMeasure(1); NOW = NOW + 2; FRAME()
local changed = {}
for _, k in ipairs({ "GetNetStats", "GetFramerate", "C_NamePlate", "GetRealZoneText", "CreateFrame" }) do
  if rawget(_G, k) ~= G[k] then changed[#changed + 1] = k end end
return #changed
""")
check("12l keine Blizzard-Globale beschrieben", r == 0, r)

# ---------------------------------------------------------------- Ergebnis
bad = [n for n, ok, _ in results if not ok]
print()
print(f"{len(results) - len(bad)}/{len(results)} Prüfungen bestanden")
if bad:
    print("FEHLER: " + ", ".join(bad))
sys.exit(1 if bad else 0)
