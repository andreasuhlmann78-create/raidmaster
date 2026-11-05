-- __ADDON__ – Diagnose-Protokoll (Vorbild: LevelPilot-Protokoll)
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Wozu: Fehler, die nur im echten Spiel auftreten (langsame Klicks, Neuaufbauten, verdeckte Fenster, Fehlerschleifen),
-- schreibt das Addon selbst mit. Der Nutzer schickt das Protokoll mit /__SLASH__ protokoll – oder es geht automatisch
-- als "GSDIAG1"-Zeichenkette über die SavedVariables und den RaidMasterUploader nach Discord #testberichte -> GitHub.
--
-- Benutzung im eigenen Code:
--   ns.Diag("KLICK", "Rezept 1234 geöffnet", 120)      -- Art, Text, optional Dauer in ms
--   ns.Timed("Liste aufbauen", fn, ...)                 -- misst fn; über ns.DIAG_SLOW_MS -> Eintrag LANGSAM
--   ns.DiagCount("AUFBAU", "TRADE_SKILL_LIST_UPDATE")    -- zählt gleichartige Ereignisse (ein Eintrag, Zähler ×N)
-- Fehler aus ns.Try landen automatisch als FEHLER (gleicher Text wird nur gezählt, keine Schleife im Protokoll).
--
-- Regeln: KEINE Spieler-, Charakter-, Gilden- oder Realmnamen (das Protokoll landet im öffentlichen Repo).
--         Im Test (ns.testing) schreibt das Protokoll nur in die Sandbox-Datenbank.

local ADDON, ns = ...
local L = ns.L

ns.DIAG_MAX = 200          -- höchstens so viele Einträge, älteste fallen weg
ns.DIAG_SLOW_MS = 16       -- ein Frame bei 60 fps
ns.DIAG_PREFIX = "GSDIAG1"
ns.DIAG_EXPORT_MAX = 60000 -- Zeichen in der SavedVariables-Zeichenkette

local function Now() return (GetTime and GetTime() or 0) end
local function Stamp() return date and date("%d.%m. %H:%M") or "" end
local function Clean(s)
    s = tostring(s or ""):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("[\r\n|]", " ")
    return s
end

local function Store()
    local db = ns.db
    if not db then return nil end
    if type(db.diag) ~= "table" then db.diag = { entries = {}, sessions = {} } end
    db.diag.entries = db.diag.entries or {}
    db.diag.sessions = db.diag.sessions or {}
    return db.diag
end

-- Einen Eintrag schreiben. Gleiche Art + gleicher Text direkt hintereinander -> nur Zähler erhöhen.
function ns.Diag(kind, text, ms)
    local d = Store()
    if not d then return end
    kind, text = Clean(kind):upper(), Clean(text)
    local e = d.entries[1]
    if e and e.k == kind and e.t == text then
        e.n = (e.n or 1) + 1
        e.z = Stamp()
        if ms then e.ms = math.max(e.ms or 0, math.floor(ms + 0.5)) end
        return e
    end
    e = { k = kind, t = text, z = Stamp(), n = 1, ms = ms and math.floor(ms + 0.5) or nil, v = ns.VERSION }
    table.insert(d.entries, 1, e)
    for i = #d.entries, ns.DIAG_MAX + 1, -1 do d.entries[i] = nil end
    return e
end

-- Gleichartige Ereignisse zählen (z. B. jeder Neuaufbau einer Liste)
function ns.DiagCount(kind, what)
    return ns.Diag(kind, what)
end

-- fn messen; ist sie langsamer als ein Frame -> LANGSAM. Gibt die Ergebnisse von fn zurück (Fehler über ns.Try).
function ns.Timed(name, fn, ...)
    local t0 = debugprofilestop and debugprofilestop() or (Now() * 1000)
    local res = { ns.Try(name, fn, ...) }
    local t1 = debugprofilestop and debugprofilestop() or (Now() * 1000)
    local ms = t1 - t0
    if ms > ns.DIAG_SLOW_MS then ns.Diag("LANGSAM", name, ms) end
    return select(2, unpack(res))
end

-- Sitzung beim Einloggen vermerken (nur Stufe und Klasse, kein Name)
function ns.DiagSession()
    local d = Store()
    if not d then return end
    local lvl = UnitLevel and UnitLevel("player") or 0
    local _, class = UnitClass and UnitClass("player")
    table.insert(d.sessions, 1, { z = Stamp(), lvl = lvl, class = class or "?", v = ns.VERSION })
    for i = #d.sessions, 21, -1 do d.sessions[i] = nil end
end

-- Das Protokoll als Text (für das Kopierfenster und die Ausgabe)
function ns.DiagText()
    local d = Store() or { entries = {}, sessions = {} }
    local G = ns.G
    local out = {}
    local function add(s) out[#out + 1] = s end
    add(string.format("%s-Protokoll v%s · %s", ADDON, tostring(ns.VERSION), Stamp()))
    add(string.format("Client %s · %s", tostring(ns.locale), G and G.Status and Clean(G.Status()) or "?"))
    add(string.format("Sitzungen: %d", #d.sessions))
    for i = 1, math.min(#d.sessions, 10) do
        local s = d.sessions[i]
        add(string.format("  %s L%s %s v%s", s.z or "", tostring(s.lvl), tostring(s.class), tostring(s.v)))
    end
    add("")
    add("== Diagnose")
    add(string.format("  Fehler in dieser Sitzung: %d", ns.errorCount or 0))
    if ns.DiagExtra then
        local ok, extra = pcall(ns.DiagExtra)
        if ok and type(extra) == "table" then for _, line in ipairs(extra) do add("  " .. Clean(line)) end end
    end
    add("")
    add(string.format("== Einträge (%d, neueste zuerst)", #d.entries))
    for _, e in ipairs(d.entries) do
        add(string.format("[%s] %s%s %s%s", e.z or "", e.k or "?", (e.n or 1) > 1 and (" ×" .. e.n) or "",
            e.t or "", e.ms and (" · " .. e.ms .. " ms") or ""))
    end
    return table.concat(out, "\n")
end

-- Zeichenkette für den Uploader (wie GSTEST1): Präfix, Addon, Version, dann der Text
function ns.DiagExport()
    local text = ns.DiagText()
    if #text > ns.DIAG_EXPORT_MAX then text = text:sub(1, ns.DIAG_EXPORT_MAX) end
    return ns.DIAG_PREFIX .. "|" .. ADDON .. "|" .. tostring(ns.VERSION) .. "|" .. text
end

function ns.ShowDiag()
    if ns.ShowCopy then ns.ShowCopy(ns.DiagText()) else ns.Print(ns.DiagText()) end
end

-- Beim Ausloggen / /reload die Export-Zeichenkette in die SavedVariables legen (nicht im Test)
if ns.On then
    ns:On("PLAYER_LOGOUT", function()
        if ns.testing or not ns.db or ns.db.diagSend == false then return end
        ns.db.diagExport = ns.DiagExport()
    end)
end
