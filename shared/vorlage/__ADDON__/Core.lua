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
    if ns.OnInit then ns.OnInit() end
end)

ns:On("PLAYER_LOGIN", function()
    if ns.db and ns.db.chat then ns.Print(L.LOADED:format(ns.VERSION)) end
    if ns.OnLogin then ns.OnLogin() end
end)

---------------------------------------------------------------------------------------------------------------------
-- Befehle: /__SLASH__
---------------------------------------------------------------------------------------------------------------------
function ns.Help()
    ns.Print(L.HELP_HEADER)
    ns.Print(L.HELP_TOGGLE)
    ns.Print(L.HELP_CONFIG)
    ns.Print(L.HELP_STATUS)
    ns.Print(L.HELP_TEST)
end

function ns.StatusText()
    return G.Status() .. "\n" .. L.STATUS_ERRORS:format(ns.errorCount)
end

ns.COMMANDS = {
    [""]     = function() if ns.ToggleWindow then ns.ToggleWindow() end end,
    help     = ns.Help,
    config   = function() if ns.OpenOptions then ns.OpenOptions() end end,
    status   = function() for line in ns.StatusText():gmatch("[^\n]+") do ns.Print(line) end end,
    test     = function(rest) if ns.RunTests then ns.RunTests(rest) end end,
}

SLASH___SLASH_GROSS__1 = "/__SLASH__"
SlashCmdList.__SLASH_GROSS__ = function(msg)
    local cmd, rest = (msg or ""):match("^%s*(%S*)%s*(.-)%s*$")
    cmd = (cmd or ""):lower()
    local fn = ns.COMMANDS[cmd]
    if fn then ns.Try("/__SLASH__ " .. cmd, fn, rest) else ns.Print(L.UNKNOWN_CMD) end
end
