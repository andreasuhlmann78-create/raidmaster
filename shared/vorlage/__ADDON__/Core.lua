-- __ADDON__ – Kern: Namensraum, Einstellungen, Ereignisse, Fehlerzählung, Befehle
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Grundregeln der GoldSentinel-Addons (gelten für jede Datei):
--   * Spielversion nur über GoldSentinelGame (G.IsModern, G.IsForever …). WoW Forever ist der MODERNE Client
--     (C_*-API, im Kampf "secret values", Kampflog für Addons zu) und darf nie wie Classic Era behandelt werden.
--   * Nie eine Blizzard-Funktion ersetzen (UnitName = …, _G.X = …, Stub(_G, …)): das "taintet" sie bis zum /reload.
--     Blizzard-Funktionen nur über ns.API aufrufen (API.lua); im Test werden nur ns.API-Einträge ersetzt.
--   * Aktionen mit Folgen (Chat, Kaufen, Herstellen, Einladen …) nur über ns.Act (API.lua): im Test nur mitschreiben.
--   * Werte aus dem Kampf (Namen, Lebenspunkte …) vor dem Vergleichen, Zerlegen oder als Schlüssel mit G.IsSecret prüfen.
--   * Fehler abfangen mit ns.Try – sie werden gezählt und über GoldSentinelTest an die Prüf-Sitzung gemeldet.
--   * Alte Clients (Classic Era, TBC …) nie brechen. Texte nur über L (Locales.lua).
--   * Leistung (shared/wissen/leistung.md): kein Bild über 40 ms, Ziel ≤ 5 ms. Schwere Arbeit (Schleifen über viele
--     Einträge, Aufbau grosser Listen, Scans) immer als Aufgabe über ns.Job (GoldSentinelTakt) mit Check in der Schleife.
--   * Testdaten anderer Addons nie lesen oder speichern, solange deren Test läuft (ns.ForeignTestRunning(addon)).
--     Eigener Test sichtbar für andere: __ADDON__API.TestRunning().

local ADDON, ns = ...
local G = GoldSentinelGame
local GT = GoldSentinelTest
local L = ns.L

_G[ADDON] = ns               -- für /dump und andere GoldSentinel-Addons (eigenes Global, kein Blizzard-Name)
ns.name = ADDON
ns.G, ns.GT = G, GT

-- Version aus der .toc (einzige Quelle; die Testroutine prüft das)
local function TocVersion()
    local getMeta = (C_AddOns and C_AddOns.GetAddOnMetadata) or GetAddOnMetadata
    local ok, v = pcall(getMeta, ADDON, "Version")
    return ok and v or "?"
end
ns.VERSION = TocVersion()

---------------------------------------------------------------------------------------------------------------------
-- Einstellungen (SavedVariables __ADDON__DB)
---------------------------------------------------------------------------------------------------------------------
ns.DB_VERSION = 1
ns.DEFAULTS = {
    enabled = true,
    chat = true,
    window = { point = "CENTER", x = 0, y = 0, shown = false },
    minimapButton = true,       -- Button an der Minimap (Minimap.lua)
    minimapAngle = 200,         -- Position um die Minimap in Grad
    diagSend = true,            -- Diagnose-Protokoll beim Ausloggen für den Uploader ablegen (Diag.lua)
    cmdHint = true,             -- Befehlsliste beim Tippen (GoldSentinelCmdHint.lua)
    cmdUse = {},                -- Zähler je Befehl für die Befehlsliste (meistbenutzte oben)
    marketShare = true,         -- Marktdaten-Netz (GoldSentinelMarkt.lua): anonym, nur Preise; Standard an
}

local function CopyDefaults(src, dst)
    for k, v in pairs(src) do
        if type(v) == "table" then
            if type(dst[k]) ~= "table" then dst[k] = {} end
            CopyDefaults(v, dst[k])
        elseif dst[k] == nil then
            dst[k] = v
        end
    end
    return dst
end
ns.CopyDefaults = CopyDefaults

-- Umbauten alter Einstellungen: je Schritt eine Funktion, nie Daten wegwerfen, die ein älterer Stand braucht
ns.MIGRATIONS = {
    -- [2] = function(db) db.neuerName = db.alterName; end,
}

function ns.InitDB(db)
    db = type(db) == "table" and db or {}
    local from = tonumber(db.dbVersion) or 0
    for v = from + 1, ns.DB_VERSION do
        local step = ns.MIGRATIONS[v]
        if step then ns.Try("Migration " .. v, step, db) end
    end
    db.dbVersion = ns.DB_VERSION
    return CopyDefaults(ns.DEFAULTS, db)
end

---------------------------------------------------------------------------------------------------------------------
-- Fehler abfangen und melden
---------------------------------------------------------------------------------------------------------------------
ns.errorCount = 0

-- ns.Try("Wo", fn, ...) -> ok, Ergebnis …   Fehler werden gezählt und an GoldSentinelTest gemeldet, nie verschluckt.
function ns.Try(where, fn, ...)
    local res = { pcall(fn, ...) }
    if not res[1] then
        ns.errorCount = ns.errorCount + 1
        if GT and GT.Error then GT.Error(ADDON, where, res[2]) end
        if ns.Diag then ns.Diag("FEHLER", tostring(where) .. ": " .. tostring(res[2])) end
        if ns.db and ns.db.chat and not ns.testing then ns.Print("|cffff5555" .. tostring(where) .. ":|r " .. tostring(res[2])) end
    end
    return unpack(res)
end

function ns.Print(msg)
    if ns.testing then
        ns.printLog = ns.printLog or {}
        table.insert(ns.printLog, tostring(msg))
        return
    end
    if DEFAULT_CHAT_FRAME then DEFAULT_CHAT_FRAME:AddMessage("|cff__FARBE____ADDON__|r: " .. tostring(msg)) end
end

---------------------------------------------------------------------------------------------------------------------
-- Schwere Arbeit in Portionen: ns.Job("Name", fn, ...) (GoldSentinelTakt, shared/wissen/leistung.md)
--   In fn (und allem, was fn aufruft) in jeder Schleife oft ns.Check("Etikett") aufrufen; statt pcall ns.PCall.
--   Nie in einer Aufgabe: geschützte Aktionen (Zauber, Kaufen …), Abgabe in sort/gsub/Metamethoden/for-in-Iteratoren.
--   Ohne GoldSentinelTakt (sollte nie vorkommen) läuft fn am Stück über ns.Try.
---------------------------------------------------------------------------------------------------------------------
local Takt = GoldSentinelTakt
ns.Takt = Takt

function ns.Job(name, fn, opts)
    opts = opts or {}
    if not (Takt and Takt.Start) then
        local ok, res = ns.Try(name, fn)
        if opts.onDone then opts.onDone({ state = ok and "fertig" or "fehler", result = res }) end
        return nil
    end
    return Takt.Start({
        name = name, owner = ADDON, fn = fn, args = opts.args,
        budget = opts.budget or 2, timeout = opts.timeout or 300, pauseInCombat = opts.pauseInCombat,
        onDone = function(job)
            if job.state ~= "fertig" and job.err then
                ns.errorCount = ns.errorCount + 1
                if GT and GT.Error then GT.Error(ADDON, "Aufgabe " .. tostring(name), job.err) end
                if ns.Diag then ns.Diag("FEHLER", "Aufgabe " .. tostring(name) .. ": " .. tostring(job.err)) end
            end
            if opts.onDone then ns.Try("Aufgabe " .. tostring(name) .. " fertig", opts.onDone, job) end
        end,
    })
end
function ns.Check(label) if Takt and Takt.Check then Takt.Check(label) end end
function ns.PCall(f, ...) if Takt and Takt.PCall then return Takt.PCall(f, ...) end return pcall(f, ...) end

---------------------------------------------------------------------------------------------------------------------
-- Testdaten-Regel (Entscheid 18.11.): eigener Test für andere Addons sichtbar, fremde Tests respektieren
---------------------------------------------------------------------------------------------------------------------
ns.testRunning = false        -- true vom Start bis zum Ende der eigenen Testroutine (auch zwischen den Portionen)
__ADDON__API = {
    version = 1,
    TestRunning = function() return ns.testRunning == true end,
}
-- Läuft gerade der Test eines anderen GoldSentinel-Addons? Dann dessen Daten weder lesen noch speichern noch melden.
function ns.ForeignTestRunning(addon)
    local api = _G[tostring(addon) .. "API"]
    if type(api) ~= "table" or type(api.TestRunning) ~= "function" then return false end
    local ok, running = pcall(api.TestRunning)
    return ok and running == true
end

---------------------------------------------------------------------------------------------------------------------
-- Ereignisse: ns:On("EREIGNIS", function(...) end)
---------------------------------------------------------------------------------------------------------------------
local frame = CreateFrame("Frame")
ns.eventFrame = frame
ns.handlers = {}

function ns:On(event, fn)
    if not ns.handlers[event] then
        ns.handlers[event] = {}
        frame:RegisterEvent(event)
    end
    table.insert(ns.handlers[event], fn)
end

frame:SetScript("OnEvent", function(_, event, ...)
    local list = ns.handlers[event]
    if not list then return end
    for i = 1, #list do ns.Try(event, list[i], ...) end
end)

-- Geschützte Aktionen (Fenster mit Sicherheits-Vorlagen, Bindings …) im Kampf aufschieben
ns.afterCombat = {}
function ns.WhenOutOfCombat(fn)
    if G.InCombat() then
        table.insert(ns.afterCombat, fn)
        return false
    end
    fn()
    return true
end

ns:On("PLAYER_REGEN_ENABLED", function()
    local list = ns.afterCombat
    ns.afterCombat = {}
    for i = 1, #list do ns.Try("Nach dem Kampf", list[i]) end
end)

---------------------------------------------------------------------------------------------------------------------
-- Start
---------------------------------------------------------------------------------------------------------------------
ns:On("ADDON_LOADED", function(name)
    if name ~= ADDON then return end
    __ADDON__DB = ns.InitDB(__ADDON__DB)
    ns.db = __ADDON__DB
    if GT and GT.TrackErrors then GT.TrackErrors(ADDON, ns.VERSION, ns.db) end
    ns.AttachMarket()
    if ns.OnInit then ns.OnInit() end
end)

-- Marktdaten-Netz (GoldSentinelMarkt.lua): das Addon ist nur Gastgeber; Schalter "Marktdaten teilen" in den Optionen
function ns.AttachMarket()
    local GM = rawget(_G, "GoldSentinelMarkt")
    if type(GM) ~= "table" or type(GM.Attach) ~= "function" or type(ns.db) ~= "table" then return false end
    ns.Try("Marktdaten-Netz", GM.Attach, ADDON, __ADDON__DB)
    if type(GM.SetShare) == "function" then ns.Try("Marktdaten teilen", GM.SetShare, ADDON, ns.db.marketShare ~= false) end
    return true
end

local prevChanged = ns.OnOptionChanged
function ns.OnOptionChanged(key)
    if prevChanged then prevChanged(key) end
    if key == "marketShare" then
        local GM = rawget(_G, "GoldSentinelMarkt")
        if type(GM) == "table" and type(GM.SetShare) == "function" then
            ns.Try("Marktdaten teilen", GM.SetShare, ADDON, ns.db.marketShare ~= false)
        end
    end
end

ns:On("PLAYER_LOGIN", function()
    if ns.db and ns.db.chat then ns.Print(L.LOADED:format(ns.VERSION)) end
    ns.Try("Befehlsliste", ns.RegisterCmdHint)
    ns.Try("Prüfliste", ns.RegisterPruefliste)
    if ns.DiagSession and not ns.testing then ns.DiagSession() end
    if ns.OnLogin then ns.OnLogin() end
end)

---------------------------------------------------------------------------------------------------------------------
-- Befehle: /__SLASH__
---------------------------------------------------------------------------------------------------------------------
-- Entwicklermodus (GoldSentinelDev.lua, /gsdev): Test- und Entwicklerfunktionen nur für den Entwickler sichtbar
function ns.IsDev()
    local d = rawget(_G, "GoldSentinelDev")
    if type(d) ~= "table" or type(d.IsDev) ~= "function" then return false end
    local ok, dev = pcall(d.IsDev, d)
    return ok and dev == true
end

-- Prüfliste im Spiel (GoldSentinelPruefliste.lua, nur Entwicklermodus): Punkte, die nur im echten Spiel prüfbar sind
function ns.RegisterPruefliste()
    local P = rawget(_G, "GoldSentinelPruefliste")
    if type(P) ~= "table" or type(P.Register) ~= "function" then return end
    ns.pruefliste = P:Register(ADDON, {
        db = function() return __ADDON__DB end,
        version = ns.VERSION,
        points = {
            { id = "OPT", title = L.PL_OPT_TITLE, since = "0.1.0", todo = L.PL_OPT_TODO, expect = L.PL_OPT_EXPECT },
            { id = "TEST", title = L.PL_TEST_TITLE, since = "0.1.0", todo = L.PL_TEST_TODO, expect = L.PL_TEST_EXPECT },
        },
    })
end

-- Befehlsliste beim Tippen (GoldSentinelCmdHint.lua): { deutsches Wort, englisches Wort, Beschreibung (L-Schlüssel) }
ns.CMD_LIST = {
    { "", "", "CMD_TOGGLE" },
    { "config", "config", "CMD_CONFIG" },
    { "status", "status", "CMD_STATUS" },
    { "minimap", "minimap", "CMD_MINIMAP" },
    { "protokoll", "protokoll", "CMD_PROTOKOLL" },
    { "help", "help", "CMD_HELP" },
    { "test", "test", "CMD_TEST" },
    { "prüfliste", "pruefliste", "CMD_PRUEFLISTE", dev = true },
}
function ns.RegisterCmdHint()
    local CH = rawget(_G, "GoldSentinelCmdHint")
    if type(CH) ~= "table" or type(CH.Register) ~= "function" then return end
    ns.cmdHint = CH.Register({
        id = ADDON, prefixes = { "/__SLASH__" }, display = "/__SLASH__", commands = ns.CMD_LIST,
        store = function() return ns.db and ns.db.cmdUse end,
        enabled = function() return ns.db and ns.db.cmdHint ~= false end,
        L = L, german = function() return ns.isGerman end, dev = ns.IsDev,
        noMatch = L.CMD_NOMATCH, enterText = L.CMD_ENTER,
    })
end

function ns.Help()
    ns.Print(L.HELP_HEADER)
    ns.Print(L.HELP_TOGGLE)
    ns.Print(L.HELP_CONFIG)
    ns.Print(L.HELP_MINIMAP)
    ns.Print(L.HELP_STATUS)
    ns.Print(L.HELP_PROTOKOLL)
    ns.Print(L.HELP_TEST)
    if ns.IsDev() then ns.Print(L.HELP_PRUEFLISTE) end
end

local function OpenPruefliste()
    if not ns.IsDev() then ns.Print(L.DEV_ONLY) return end
    if ns.pruefliste and ns.pruefliste.Open then ns.pruefliste:Open() end
end

function ns.StatusText()
    return G.Status() .. "\n" .. L.STATUS_ERRORS:format(ns.errorCount)
end

ns.COMMANDS = {
    [""]     = function() if ns.ToggleWindow then ns.ToggleWindow() end end,
    help     = ns.Help,
    config   = function() if ns.OpenOptions then ns.OpenOptions() end end,
    minimap  = function() if ns.ToggleMinimapButton then ns.ToggleMinimapButton() end end,
    protokoll = function() if ns.ShowDiag then ns.ShowDiag() end end,
    status   = function() for line in ns.StatusText():gmatch("[^\n]+") do ns.Print(line) end end,
    test     = function(rest) if ns.RunTests then ns.RunTests(rest) end end,
    ["prüfliste"] = OpenPruefliste,
    pruefliste = OpenPruefliste,
}

SLASH___SLASH_GROSS__1 = "/__SLASH__"
SlashCmdList.__SLASH_GROSS__ = function(msg)
    if ns.cmdHint then msg = ns.cmdHint:Resolve(msg); ns.cmdHint:Count(msg) end   -- Auswahl aus der Befehlsliste
    local cmd, rest = (msg or ""):match("^%s*(%S*)%s*(.-)%s*$")
    cmd = (cmd or ""):lower()
    local fn = ns.COMMANDS[cmd]
    if fn then ns.Try("/__SLASH__ " .. cmd, fn, rest) else ns.Print(L.UNKNOWN_CMD) end
end
