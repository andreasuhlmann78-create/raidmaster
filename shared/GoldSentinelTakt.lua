-- GoldSentinelTakt - gemeinsamer Takt fuer schwere Arbeit in Portionen (alle Addons von GoldSentinel)
-- Copyright (C) 2026 GoldSentinel
--
-- Entscheid des Nutzers 17.11.2026 20:42 ("genau go ... und mach ja keinen Fehler"), Wissen: shared/wissen/leistung.md
-- Abschnitt 6 (bewaehrte Muster aus ThreatSentinel B1, BuffSentinel B2, GoldSentinelMarkt B3).
--
-- Diese Datei UNVERAENDERT in jedes Addon kopieren, das sie benutzt, und in der .toc VOR den eigenen Dateien eintragen.
-- Mehrere Addons duerfen sie gleichzeitig mitbringen: die neueste Version gewinnt und uebernimmt laufende Aufgaben.
--
-- WARUM: WoW zeichnet erst das naechste Bild, wenn alle Addons fertig gerechnet haben. Wer 500 ms am Stueck rechnet,
-- laesst das Bild 500 ms stehen (Ruckeln). Der Takt teilt schwere Arbeit in Portionen: je Bild hoechstens BUDGET ms
-- (Standard 2 ms), danach geht es im naechsten Bild weiter. Hoechstens EINE Aufgabe rechnet je Bild.
--
-- BENUTZUNG
--   local job = GoldSentinelTakt.Start({
--       name = "Rezepte neu",            -- erscheint in Messwerten und Fehlern
--       owner = "ProfessionSentinel",    -- Addon (fuer Running/CancelOwner)
--       fn = function(a, b) ... end,     -- die Arbeit; laeuft in einer Coroutine
--       args = { a, b },                 -- optional: Argumente fuer fn
--       budget = 2,                      -- optional: ms je Bild (0.5 .. 8), Standard 2
--       timeout = 300,                   -- optional: Sekunden, danach Abbruch "Zeitlimit" (Standard 300, hoechstens 3600)
--       pauseInCombat = false,           -- optional: im Kampf nicht weiterrechnen (Zeitlimit laeuft weiter)
--       onDone = function(job) end,      -- optional: am Ende (job.state, job.err, job.result, job.stats)
--       onPortion = function(job, ms) end, -- optional: nach jeder Portion
--   })
--   In fn (und allem, was fn aufruft):
--     GoldSentinelTakt.Check("T12")      -- gibt ab, wenn das Budget dieses Bildes verbraucht ist (sonst sofort zurueck).
--                                          Oft aufrufen: in Schleifen alle paar Eintraege. Das Etikett ("T12") steht in
--                                          den Messwerten bei der Portion. Ausserhalb einer Aufgabe: wirkungslos.
--     GoldSentinelTakt.Label("T12")      -- nur Etikett setzen (ohne Abgabe)
--     GoldSentinelTakt.NoYield(f, ...)   -- f ohne Abgabe ausfuehren (z. B. solange Ersatz-Werte gesetzt sind)
--     GoldSentinelTakt.PCall(f, ...)     -- wie pcall, aber f DARF abgeben (pcall selbst darf es in Lua 5.1 nicht)
--     GoldSentinelTakt.Sliced(f, enter, leave, ...)  -- wie PCall; enter() vor und leave() nach JEDEM Stueck von f
--                                          (Ersatz-Zustand nur waehrend f wirkt, nie in fremden Bildern)
--     GoldSentinelTakt.Sleep(sek)        -- warten, ohne zu rechnen (andere Aufgaben laufen weiter)
--     GoldSentinelTakt.WaitFor(pruef, sek) -- warten, bis pruef() true liefert, hoechstens sek Sekunden -> true/false
--   Danach: GoldSentinelTakt.Summary(job) -> eine Zeile fuer Bericht/Protokoll; job.stats fuer eigene Auswertung.
--
-- LUA 5.1 – WICHTIG: In pcall/xpcall, in Vergleichsfunktionen von table.sort, in gsub-Funktionen, in Metamethoden
-- (__index-Funktion ...) und in Iterator-Funktionen einer for-in-Schleife darf NICHT abgegeben werden ("attempt to yield
-- across metamethod/C-call boundary"). Der Takt erkennt pcall/xpcall/sort/gsub im Stapel und gibt dort nicht ab (gezaehlt
-- als "Abgabe nicht moeglich" mit Etikett). In Metamethoden und Iterator-Funktionen ist das im Stapel nicht sichtbar:
-- dort Check NICHT aufrufen (sonst endet die Aufgabe laut mit diesem Fehler). Statt pcall immer GoldSentinelTakt.PCall.
-- Eine Schleife OHNE Check kann der Takt nicht teilen. Geschuetzte Aktionen (Zauber, Kaufen ...) nie in einer Aufgabe.
--
-- GRENZEN (Entscheide des Nutzers): kein Bild ueber 40 ms; Ziel <= 5 ms. Gemessen und in job.stats/Summary ausgewiesen:
-- Bilder, laengstes Bild mit Etikett, Bilder ueber 5/16/40 ms, eigene Rechenzeit, Dauer, Abgaben nicht moeglich.
-- Keine Sperre ohne Zeitlimit: jede Aufgabe endet spaetestens nach timeout Sekunden.
--
-- VERSION 2 (18.11.2026, Hinweis des Nutzers: Tests in Unterstadt mit vielen Spielern und Server-Lag):
--   - Ganze Bilder: Der Takt misst zusaetzlich die Dauer des GANZEN Bildes (OnUpdate elapsed) nach jeder Portion. In job.stats
--     und Summary: "ganze Bilder ueber 40 ms: n, davon durch Spiel/Umgebung m" (m = eigene Portion in diesem Bild <= 16 ms).
--   VERSION 3 (19.11.2026): Speicherbereinigung nur gezaehlt, wenn der Speicher in einem Bild um mehr als 1 MB faellt (v2 zaehlte
--     jeden kleinen Schritt der schrittweisen Bereinigung: im Spiel 254 in 10 s).
--   - Umgebung: GoldSentinelTakt.EnvMeasure(sek, fertig) misst sek Sekunden lang (Standard 10) OHNE eigene Arbeit: Ort, Spieler
--     in Sicht (Namensplaketten), Ping Realm/Welt, Bildrate, Bildzeit in Ruhe (Median/95 %/laengstes), Speicherbereinigungen.
--     GoldSentinelTakt.EnvLine() -> eine Zeile fuer den Testbericht (leer, wenn nichts gemessen). Testroutinen rufen EnvMeasure
--     vor dem Lauf auf (oder Start mit opts.env = 10: misst vor der Arbeit) und schreiben EnvLine in den Bericht.

local VERSION = 3

local existing = _G.GoldSentinelTakt
if type(existing) == "table" and (tonumber(existing.VERSION) or 0) >= VERSION then return end

-- Dieselbe Tabelle weiterverwenden: Addons, die sich GoldSentinelTakt lokal gemerkt haben, bekommen die neuen Funktionen
local T = type(existing) == "table" and existing or {}
_G.GoldSentinelTakt = T
T.VERSION = VERSION

T.BUDGET_MS = 2          -- Standard-Budget je Bild
T.BUDGET_MIN = 0.5
T.BUDGET_MAX = 8
T.TIMEOUT = 300          -- Standard-Zeitlimit (Sekunden)
T.TIMEOUT_MAX = 3600
T.WORST_MAX = 10         -- so viele laengste Bilder je Aufgabe mit Etikett
T.LIMITS = { 5, 16, 40 } -- gezaehlte Grenzen (ms)
T.WHOLE_LIMIT = 40       -- ganzes Bild: ab hier gezaehlt
T.FOREIGN_OWN = 16       -- eigene Portion bis hier: langes ganzes Bild zaehlt als "Spiel/Umgebung"
T.ENV_SEC = 10           -- Standard-Dauer der Umgebungsmessung
T.ENV_MAX_SAMPLES = 3000
T.ENV_GC_KB = 1024       -- Speicher faellt um mehr als so viele KB in einem Bild = eine Bereinigung

-- Zugang zu Spiel-Funktionen (in Tests ersetzbar; nie Blizzard-Globale beschreiben)
T.api = {
    ms = function()
        local f = _G.debugprofilestop
        if f then return f() end
        local g = _G.GetTime
        return g and g() * 1000 or os.clock() * 1000
    end,
    now = function()
        local g = _G.GetTime
        return g and g() or os.time()
    end,
    combat = function()
        local f = _G.InCombatLockdown
        return f and f() and true or false
    end,
    -- Stapel der laufenden Coroutine als Text, ab dem Aufrufer dieser Funktion (direkt aufgerufen, ohne pcall: ein pcall
    -- haette selbst eine Zeile "[C]" im Stapel). Unsere eigenen Ebenen (stack, CBoundary, Check) sind Lua, ohne "[C]".
    net = function()   -- Ping Realm, Ping Welt (ms) oder nil
        local f = _G.GetNetStats
        if type(f) ~= "function" then return nil end
        local ok, _, _, home, world = pcall(f)
        if not ok then return nil end
        return tonumber(home), tonumber(world)
    end,
    fps = function()
        local f = _G.GetFramerate
        if type(f) ~= "function" then return nil end
        local ok, v = pcall(f)
        return ok and tonumber(v) or nil
    end,
    plates = function()   -- sichtbare Namensplaketten (ungefaehr Spieler/Figuren in Sicht) oder nil
        local np = _G.C_NamePlate
        if type(np) ~= "table" or type(np.GetNamePlates) ~= "function" then return nil end
        local ok, t = pcall(np.GetNamePlates)
        return ok and type(t) == "table" and #t or nil
    end,
    zone = function()
        local z = type(_G.GetRealZoneText) == "function" and _G.GetRealZoneText() or nil
        local s = type(_G.GetSubZoneText) == "function" and _G.GetSubZoneText() or nil
        return z, s
    end,
    mem = function() return collectgarbage("count") end,
    stack = function()
        local d = _G.debugstack
        if type(d) == "function" then
            local s = d(2, 200, 0)
            if type(s) == "string" then return s end
        end
        local dbg = _G.debug
        if type(dbg) == "table" and type(dbg.traceback) == "function" then
            local s = dbg.traceback("", 2)
            if type(s) == "string" then return s end
        end
        return ""
    end,
}

-- Aufgaben (bei neuerer Version uebernommen)
T.jobs = type(T.jobs) == "table" and T.jobs or {}
T.byCo = type(T.byCo) == "table" and T.byCo or setmetatable({}, { __mode = "k" })  -- Coroutine -> Aufgabe (auch PCall/Sliced)
T.rr = tonumber(T.rr) or 0  -- Reihum-Zeiger
T.stats = type(T.stats) == "table" and T.stats
    or { started = 0, done = 0, failed = 0, cancelled = 0, timeouts = 0, cbErrors = 0 }

local unpack = unpack or table.unpack
local function Pack(...) return { n = select("#", ...), ... } end

------------------------------------------------------------------------
-- Hilfen
------------------------------------------------------------------------
local function Clamp(v, lo, hi, def)
    v = tonumber(v)
    if not v or v ~= v then return def end
    if v < lo then return lo end
    if v > hi then return hi end
    return v
end

-- Laeuft gerade eine Aufgabe, die abgeben darf? -> Aufgabe, Coroutine
local function Current()
    local co = coroutine.running()
    if not co then return nil end
    local job = T.byCo[co]
    if not job or job.state ~= "laeuft" then return nil end
    return job, co
end

-- Stapel als Zeilen (ohne Kopfzeile "stack traceback:")
local function StackLines()
    local out = {}
    for line in T.api.stack():gmatch("[^\n]+") do
        if not line:find("^%s*stack traceback") then out[#out + 1] = line end
    end
    return out
end

-- Eichung je Coroutine: wie viele Zeilen stehen im Stapel UNTER der Startfunktion der Coroutine? (In Lua 5.1 keine; falls
-- das Spiel dort eigene Zeilen anhaengt, z. B. "[C]: ?", werden sie so nie als C-Grenze gewertet.)
T.extra = type(T.extra) == "table" and T.extra or setmetatable({}, { __mode = "k" })
function T.Calibrate()
    local co = coroutine.running()
    if not co then return end
    local n = #StackLines() - 3          -- 3 = StackLines + diese Funktion + Startfunktion der Coroutine
    T.extra[co] = n > 0 and n or 0
end

-- Ist im Stapel (dieser Coroutine) eine C-Grenze sichtbar, ueber die Lua 5.1 nicht abgeben kann? (pcall, xpcall, sort,
-- gsub ...) Zeilen unter der Startfunktion der Coroutine zaehlen nicht (Eichung).
local function CBoundary()
    local lines = StackLines()
    local co = coroutine.running()
    local last = #lines - ((co and T.extra[co]) or 0)
    for i = 1, last do
        local line = lines[i]
        if line:find("[C]", 1, true) then
            local fn = line:match("in function [`'\"]?([%w_%.:]+)") or "?"
            if fn ~= "debugstack" and fn ~= "traceback" then return true, fn end
        end
    end
    return false
end

local function Note(job, key, label)
    local st = job.stats
    st[key] = (st[key] or 0) + 1
    local list = st[key .. "At"]
    if not list then list = {}; st[key .. "At"] = list end
    label = label or job.label or "-"
    if #list < 10 then
        local dup = false
        for _, v in ipairs(list) do if v == label then dup = true break end end
        if not dup then list[#list + 1] = label end
    end
end

-- Abgabe ausfuehren (mit Merker: scheitert sie in einer nicht sichtbaren C-Grenze, faellt das danach auf)
local function DoYield(job, label)
    if job.pending then Note(job, "yieldFailed", job.pending); job.pending = nil end
    job.pending = label or job.label or "-"
    coroutine.yield()
    job.pending = nil
end

------------------------------------------------------------------------
-- In der Aufgabe
------------------------------------------------------------------------
function T.Label(label)
    local job = Current()
    if job and label ~= nil then job.label = tostring(label) end
end

-- Gibt ab, wenn das Budget dieses Bildes verbraucht ist. true = abgegeben.
function T.Check(label)
    local job = Current()
    if not job then return false end
    if label ~= nil then job.label = tostring(label) end
    if job.pending then Note(job, "yieldFailed", job.pending); job.pending = nil end
    if (job.noYield or 0) > 0 then return false end
    if T.api.ms() - (job.frameStart or 0) < job.budget then return false end
    local blocked, fn = CBoundary()
    if blocked then
        Note(job, "blocked", (job.label or "-") .. " (" .. fn .. ")")
        return false
    end
    DoYield(job, job.label)
    return true
end

-- f ohne Abgabe ausfuehren; Fehler werden weitergegeben (wie ein normaler Aufruf)
function T.NoYield(f, ...)
    local job = Current()
    if not job then return f(...) end
    job.noYield = (job.noYield or 0) + 1
    local res = Pack(pcall(f, ...))
    job.noYield = job.noYield - 1
    if not res[1] then error(res[2], 0) end
    return unpack(res, 2, res.n)
end

-- Wie pcall, aber f darf abgeben. enter/leave (optional) laufen vor und nach jedem Stueck von f.
function T.Sliced(f, enter, leave, ...)
    local job, parent = Current()
    local args = Pack(...)
    local co = coroutine.create(function() T.Calibrate(); return f(unpack(args, 1, args.n)) end)
    if job then T.byCo[co] = job end
    local res
    local held = false          -- nach oben abgeben nicht moeglich: Rest von f ohne Abgabe
    while true do
        if enter then
            local ok, e = pcall(enter)
            if not ok then res = { n = 2, false, e } break end
        end
        res = Pack(coroutine.resume(co))
        local suspended = coroutine.status(co) == "suspended"
        if job then
            -- Abgabe von f ist bei uns angekommen (nicht gescheitert); stirbt f mit offenem Merker, ist sie gescheitert
            if job.pending and not suspended then Note(job, "yieldFailed", job.pending) end
            job.pending = nil
        end
        if leave then
            local ok, e = pcall(leave)
            if not ok then
                if res[1] then res = { n = 2, false, e } end
                break
            end
        end
        if not suspended then break end
        -- f hat abgegeben: nach oben weitergeben, wenn moeglich; sonst f ohne Abgabe zu Ende laufen lassen (nie haengen)
        if job and not held then
            local blocked, fn = false, nil
            if coroutine.running() ~= parent or (job.noYield or 0) > 0 then
                blocked = true
            else
                blocked, fn = CBoundary()
                if blocked then Note(job, "blocked", (job.label or "-") .. " (" .. tostring(fn) .. ")") end
            end
            if blocked then
                held = true
                job.noYield = (job.noYield or 0) + 1
            else
                DoYield(job, job.label)
            end
        end
        if job and job.state ~= "laeuft" then
            -- Aufgabe wurde waehrend der Abgabe abgebrochen: f nicht weiterfuehren
            res = { n = 2, false, job.err or "abgebrochen" }
            break
        end
    end
    if job then
        if held then job.noYield = job.noYield - 1 end
        T.byCo[co] = nil
    end
    if not res[1] then return false, res[2] end
    return unpack(res, 1, res.n)
end

function T.PCall(f, ...)
    return T.Sliced(f, nil, nil, ...)
end

-- Warten ohne zu rechnen (nur in einer Aufgabe; sonst false)
function T.Sleep(sec)
    local job = Current()
    if not job or (job.noYield or 0) > 0 then return false end
    local blocked, fn = CBoundary()
    if blocked then Note(job, "blocked", (job.label or "-") .. " (" .. fn .. ")"); return false end
    job.sleepUntil = T.api.now() + Clamp(sec, 0, T.TIMEOUT_MAX, 0)
    DoYield(job, job.label)
    return true
end

-- Warten, bis pruef() true liefert (hoechstens sec Sekunden). -> true (erfuellt) / false (Zeit um, Fehler oder nicht in Aufgabe)
function T.WaitFor(pruef, sec, step)
    local job = Current()
    local limit = T.api.now() + Clamp(sec, 0, T.TIMEOUT_MAX, 10)
    step = Clamp(step, 0, 60, 0.1)
    while true do
        local ok, v = pcall(pruef)
        if ok and v then return true end
        if not ok then return false end
        if T.api.now() >= limit then return false end
        if not job or not T.Sleep(step) then return false end
    end
end

------------------------------------------------------------------------
-- Aufgaben starten / abbrechen
------------------------------------------------------------------------
local function Finish(job, state, err)
    if job.state ~= "laeuft" then return end
    job.state = state
    job.err = err
    job.ended = T.api.now()
    job.stats.wallSec = job.ended - job.started
    for i = #T.jobs, 1, -1 do if T.jobs[i] == job then table.remove(T.jobs, i) end end
    if job.co then T.byCo[job.co] = nil end
    if state == "fertig" then T.stats.done = T.stats.done + 1
    elseif state == "fehler" then T.stats.failed = T.stats.failed + 1
    else T.stats.cancelled = T.stats.cancelled + 1 end
    if state == "zeitlimit" then T.stats.timeouts = T.stats.timeouts + 1 end
    if job.onDone then
        local ok, e = pcall(job.onDone, job)
        if not ok then T.stats.cbErrors = T.stats.cbErrors + 1; job.cbError = e end
    end
end

function T.Start(opts)
    if type(opts) ~= "table" or type(opts.fn) ~= "function" then
        error("GoldSentinelTakt.Start: fn fehlt", 2)
    end
    local job = {
        name = tostring(opts.name or "?"),
        owner = tostring(opts.owner or "?"),
        budget = Clamp(opts.budget, T.BUDGET_MIN, T.BUDGET_MAX, T.BUDGET_MS),
        timeout = Clamp(opts.timeout, 1, T.TIMEOUT_MAX, T.TIMEOUT),
        pauseInCombat = opts.pauseInCombat and true or false,
        onDone = type(opts.onDone) == "function" and opts.onDone or nil,
        onPortion = type(opts.onPortion) == "function" and opts.onPortion or nil,
        state = "laeuft",
        started = T.api.now(),
        noYield = 0,
        stats = { frames = 0, ownMs = 0, maxMs = 0, maxAt = nil, over = { 0, 0, 0 }, worst = {},
                  blocked = 0, yieldFailed = 0, combatFrames = 0, sleepFrames = 0, whole = 0, wholeMax = 0,
                  wholeOver = 0, wholeForeign = 0 },
    }
    local a = type(opts.args) == "table" and opts.args or {}
    local an = tonumber(a.n) or #a
    local args = { n = an, unpack(a, 1, an) }
    local fn = opts.fn
    local envSec = tonumber(opts.env)
    job.co = coroutine.create(function()
        if envSec and envSec > 0 then
            local done = false
            T.EnvMeasure(envSec, function() done = true end)
            T.WaitFor(function() return done end, envSec + 5)
        end
        T.Calibrate(); return fn(unpack(args, 1, args.n))
    end)
    T.byCo[job.co] = job
    T.jobs[#T.jobs + 1] = job
    T.stats.started = T.stats.started + 1
    T.Wake()
    return job
end

function T.Cancel(job, reason)
    if type(job) ~= "table" or job.state ~= "laeuft" then return false end
    Finish(job, "abgebrochen", reason or "abgebrochen")
    return true
end

function T.CancelOwner(owner, reason)
    local n = 0
    for i = #T.jobs, 1, -1 do
        local job = T.jobs[i]
        if job and job.owner == owner and T.Cancel(job, reason) then n = n + 1 end
    end
    return n
end

function T.Running(owner)
    local out = {}
    for _, job in ipairs(T.jobs) do
        if owner == nil or job.owner == owner then out[#out + 1] = job end
    end
    return out
end

------------------------------------------------------------------------
-- Treiber: je Bild hoechstens eine Aufgabe, reihum
------------------------------------------------------------------------
local function Record(job, ms, labelFrom, labelTo)
    local st = job.stats
    st.frames = st.frames + 1
    st.ownMs = st.ownMs + ms
    local at = labelFrom == labelTo and (labelTo or "-") or ((labelFrom or "-") .. "–" .. (labelTo or "-"))
    if ms > st.maxMs then st.maxMs = ms; st.maxAt = at end
    for i, lim in ipairs(T.LIMITS) do if ms > lim then st.over[i] = st.over[i] + 1 end end
    -- laengste Bilder mit Etikett (sortiert absteigend, hoechstens WORST_MAX)
    local w = st.worst
    if #w < T.WORST_MAX or ms > w[#w].ms then
        local pos = #w + 1
        for i = 1, #w do if ms > w[i].ms then pos = i break end end
        table.insert(w, pos, { ms = ms, at = at })
        if #w > T.WORST_MAX then w[#w] = nil end
    end
end

local function RunSlice(job)
    local now = T.api.now()
    if now - job.started > job.timeout then
        Finish(job, "zeitlimit", string.format("Zeitlimit %d s", job.timeout))
        return
    end
    if job.sleepUntil then
        if now < job.sleepUntil then job.stats.sleepFrames = job.stats.sleepFrames + 1 return end
        job.sleepUntil = nil
    end
    if job.pauseInCombat and T.api.combat() then
        job.stats.combatFrames = job.stats.combatFrames + 1
        return
    end
    local labelFrom = job.label
    job.frameStart = T.api.ms()
    job.pending = nil
    local res = Pack(coroutine.resume(job.co))
    local ms = T.api.ms() - job.frameStart
    if ms < 0 then ms = 0 end
    Record(job, ms, labelFrom, job.label)
    T.lastJob, T.lastOwn = job, ms
    local status = coroutine.status(job.co)
    if status == "dead" and job.pending then
        Note(job, "yieldFailed", job.pending); job.pending = nil
    end
    if job.onPortion then
        local ok, e = pcall(job.onPortion, job, ms)
        if not ok then T.stats.cbErrors = T.stats.cbErrors + 1; job.cbError = e end
    end
    if job.state ~= "laeuft" then return end          -- waehrend der Portion abgebrochen
    if not res[1] then
        local tb
        local dbg = _G.debug
        if type(dbg) == "table" and type(dbg.traceback) == "function" then
            local ok, s = pcall(dbg.traceback, job.co, tostring(res[2]))
            if ok then tb = s end
        end
        job.trace = tb
        Finish(job, "fehler", tostring(res[2]))
        return
    end
    if status == "dead" then
        job.result = { n = res.n - 1, unpack(res, 2, res.n) }
        Finish(job, "fertig", nil)
    end
end

-- elapsed (Sekunden) = Dauer des letzten ganzen Bildes; gehoert zur Portion, die im letzten Bild lief
local function Whole(elapsed)
    local job, own = T.lastJob, T.lastOwn
    T.lastJob, T.lastOwn = nil, nil
    local ms = tonumber(elapsed)
    if not job or not ms or type(job.stats) ~= "table" then return end
    ms = ms * 1000
    local st = job.stats
    st.whole = (st.whole or 0) + 1
    if ms > (st.wholeMax or 0) then st.wholeMax = ms end
    if ms > T.WHOLE_LIMIT then
        st.wholeOver = (st.wholeOver or 0) + 1
        if (own or 0) <= T.FOREIGN_OWN then st.wholeForeign = (st.wholeForeign or 0) + 1 end
    end
end

function T.Tick(elapsed)
    Whole(elapsed)
    local n = #T.jobs
    if n == 0 then T.Sleepy() return end
    T.rr = T.rr % n + 1
    local job = T.jobs[T.rr]
    if job then
        local ok, e = pcall(RunSlice, job)
        if not ok then
            -- Fehler im Takt selbst: Aufgabe beenden, nie haengen bleiben
            T.stats.cbErrors = T.stats.cbErrors + 1
            if job.state == "laeuft" then Finish(job, "fehler", "Takt: " .. tostring(e)) end
        end
    end
    if #T.jobs == 0 then T.Sleepy() end
end

-- Treiber-Rahmen: nur wach, solange Aufgaben da sind
function T.Wake()
    if not T.frame then
        local cf = _G.CreateFrame
        if not cf then return end
        T.frame = cf("Frame")
    end
    T.frame:SetScript("OnUpdate", function(_, elapsed) _G.GoldSentinelTakt.Tick(elapsed) end)
    T.awake = true
end

function T.Sleepy()
    if T.frame and T.awake then T.frame:SetScript("OnUpdate", nil) end
    T.awake = false
end

------------------------------------------------------------------------
-- Auswertung
------------------------------------------------------------------------
local function Fmt(ms) return string.format("%.1f", ms or 0) end

function T.Summary(job)
    if type(job) ~= "table" or type(job.stats) ~= "table" then return "" end
    local st = job.stats
    local parts = {}
    parts[#parts + 1] = string.format("Portionen: %d Bilder, längstes Bild %s ms (%s)", st.frames, Fmt(st.maxMs), st.maxAt or "-")
    parts[#parts + 1] = string.format("über 5 ms: %d · über 16 ms: %d · über 40 ms: %d", st.over[1], st.over[2], st.over[3])
    if st.over[2] > 0 then
        local w = {}
        for _, v in ipairs(st.worst) do if v.ms > 16 then w[#w + 1] = v.at .. " " .. Fmt(v.ms) .. " ms" end end
        if #w > 0 then parts[#parts + 1] = "längste: " .. table.concat(w, ", ") end
    end
    parts[#parts + 1] = string.format("eigene Rechenzeit %s ms · Dauer %s s", Fmt(st.ownMs), Fmt(st.wallSec or (T.api.now() - job.started)))
    if (st.wholeOver or 0) > 0 then
        parts[#parts + 1] = string.format("ganze Bilder über 40 ms: %d, davon durch Spiel/Umgebung (eigene Portion ≤ %d ms): %d · längstes ganzes Bild %s ms",
            st.wholeOver, T.FOREIGN_OWN, st.wholeForeign or 0, Fmt(st.wholeMax))
    end
    if st.blocked > 0 then parts[#parts + 1] = string.format("Abgabe nicht möglich: %d (%s)", st.blocked, table.concat(st.blockedAt or {}, ", ")) end
    if st.yieldFailed > 0 then parts[#parts + 1] = string.format("Abgabe gescheitert: %d (%s)", st.yieldFailed, table.concat(st.yieldFailedAt or {}, ", ")) end
    if job.state ~= "laeuft" and job.state ~= "fertig" then parts[#parts + 1] = "Ende: " .. job.state .. (job.err and (" – " .. tostring(job.err)) or "") end
    return table.concat(parts, " · ")
end

------------------------------------------------------------------------
-- Umgebung (Version 2): Ort, Spieler in Sicht, Ping, Bildzeit in Ruhe
------------------------------------------------------------------------
-- Misst sek Sekunden lang mit einem eigenen Rahmen (keine Arbeit), dann fertig(env). Laeuft schon eine Messung: nur
-- fertig anhaengen. Ergebnis in T.env (bleibt bis zur naechsten Messung).
function T.EnvMeasure(sek, fertig)
    sek = Clamp(sek, 1, 60, T.ENV_SEC)
    T.envWaiters = type(T.envWaiters) == "table" and T.envWaiters or {}
    if type(fertig) == "function" then T.envWaiters[#T.envWaiters + 1] = fertig end
    if T.envRun then return end
    local cf = _G.CreateFrame
    if not cf then
        T.env = nil
        local w = T.envWaiters; T.envWaiters = {}
        for _, f in ipairs(w) do pcall(f, nil) end
        return
    end
    local run = { started = T.api.now(), sek = sek, samples = {}, plates = 0, gc = 0, fpsSum = 0, fpsN = 0,
                  mem = T.api.mem() }
    T.envRun = run
    T.envFrame = T.envFrame or cf("Frame")
    T.envFrame:SetScript("OnUpdate", function(_, elapsed)
        local ok, e = pcall(T.EnvStep, elapsed)
        if not ok then T.stats.cbErrors = T.stats.cbErrors + 1; T.EnvFinish("Fehler: " .. tostring(e)) end
    end)
end

function T.EnvStep(elapsed)
    local run = T.envRun
    if not run then return end
    local ms = tonumber(elapsed)
    if ms and #run.samples < T.ENV_MAX_SAMPLES then run.samples[#run.samples + 1] = ms * 1000 end
    local p = T.api.plates()
    if p and p > run.plates then run.plates = p end
    if p then run.platesSeen = true end
    local f = T.api.fps()
    if f then run.fpsSum = run.fpsSum + f; run.fpsN = run.fpsN + 1 end
    local m = T.api.mem()
    if m < run.mem - T.ENV_GC_KB then run.gc = run.gc + 1 end   -- nur echte Bereinigung (Abfall > 1 MB weg), nicht jeder kleine Schritt
    run.mem = m
    if T.api.now() - run.started >= run.sek then T.EnvFinish() end
end

function T.EnvFinish(err)
    local run = T.envRun
    T.envRun = nil
    if T.envFrame then T.envFrame:SetScript("OnUpdate", nil) end
    if not run then return end
    local s = {}
    for i, v in ipairs(run.samples) do s[i] = v end
    table.sort(s)
    local function At(q) if #s == 0 then return nil end return s[math.max(1, math.min(#s, math.floor(q * #s + 0.5)))] end
    local home, world = T.api.net()
    local z, sub = T.api.zone()
    T.env = {
        t = T.api.now(), sek = run.sek, n = #s, zone = z, sub = sub,
        plates = run.platesSeen and run.plates or nil,
        home = home, world = world,
        fps = run.fpsN > 0 and run.fpsSum / run.fpsN or nil,
        median = At(0.5), p95 = At(0.95), max = s[#s], gc = run.gc, err = err,
    }
    local w = T.envWaiters or {}
    T.envWaiters = {}
    for _, f in ipairs(w) do pcall(f, T.env) end
end

-- Eine Zeile fuer den Testbericht; leer, wenn noch nicht gemessen
function T.EnvLine()
    local e = T.env
    if type(e) ~= "table" then return "" end
    local parts = {}
    local ort = e.zone and e.zone ~= "" and e.zone or "?"
    if e.sub and e.sub ~= "" and e.sub ~= e.zone then ort = ort .. " (" .. e.sub .. ")" end
    parts[#parts + 1] = "Umgebung: " .. ort
    if e.plates then parts[#parts + 1] = string.format("in Sicht %d Namensplaketten", e.plates) end
    if e.home or e.world then
        parts[#parts + 1] = string.format("Ping Realm %s ms / Welt %s ms", e.home and tostring(math.floor(e.home + 0.5)) or "?",
            e.world and tostring(math.floor(e.world + 0.5)) or "?")
    end
    if e.fps then parts[#parts + 1] = string.format("%.0f Bilder/s", e.fps) end
    if e.median then
        parts[#parts + 1] = string.format("Bild in Ruhe Median %s ms, 95 %% %s ms, längstes %s ms (%d Bilder in %d s)",
            Fmt(e.median), Fmt(e.p95), Fmt(e.max), e.n, e.sek)
    end
    parts[#parts + 1] = string.format("Speicherbereinigungen %d", e.gc or 0)
    if e.err then parts[#parts + 1] = "Messung abgebrochen: " .. tostring(e.err) end
    return table.concat(parts, " · ")
end
