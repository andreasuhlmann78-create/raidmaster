-- __ADDON__ – Texte in allen Sprachen
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Regeln:
--   * Jeder Text im Code steht hier als Schlüssel: L.SCHLUESSEL. Nie Text direkt in den Code schreiben.
--   * Englisch ist der Standard (gilt für alle Sprachen ohne eigene Übersetzung), Deutsch ist Pflicht.
--   * Weitere Sprachen unten in ihrem Block ergänzen; fehlende Schlüssel fallen automatisch auf Englisch zurück.
--   * Die Testroutine (TestRoutine.lua, Bereich F) prüft, dass jeder englische Schlüssel auch deutsch vorhanden ist.

local ADDON, ns = ...

local L = {}
ns.L = L
ns.locale = GetLocale and GetLocale() or "enUS"
ns.isGerman = (ns.locale == "deDE")

-- Englisch (Standard) --------------------------------------------------------------------------------------------
local enUS = {
    TITLE          = "__ADDON__",
    LOADED         = "Version %s loaded. Type /__SLASH__ for help.",
    HELP_HEADER    = "Commands:",
    HELP_TOGGLE    = "/__SLASH__ – show or hide the window",
    HELP_CONFIG    = "/__SLASH__ config – open the options",
    HELP_STATUS    = "/__SLASH__ status – game version and diagnostics",
    HELP_TEST      = "/__SLASH__ test – run the built-in test routine",
    STATUS_ERRORS  = "Errors recorded in this session: %d",
    OPT_ENABLED    = "Enabled",
    OPT_CHAT       = "Show messages in chat",
    OPT_HINT       = "Changes take effect immediately.",
    IN_COMBAT      = "Not possible in combat – will be done after the fight.",
    TEST_RUNNING   = "Test routine running …",
    TEST_DONE      = "Test routine finished: %d OK, %d errors, %d skipped, %d to check in the client.",
    TEST_RELOAD    = "Please type /reload after the test so that the report is saved.",
    COPY_HINT      = "Ctrl+C to copy, Esc to close",
    CLOSE          = "Close",
    UNKNOWN_CMD    = "Unknown command. Type /__SLASH__ help.",
}

-- Deutsch (Pflicht) ----------------------------------------------------------------------------------------------
local deDE = {
    TITLE          = "__ADDON__",
    LOADED         = "Version %s geladen. Hilfe mit /__SLASH__.",
    HELP_HEADER    = "Befehle:",
    HELP_TOGGLE    = "/__SLASH__ – Fenster zeigen oder ausblenden",
    HELP_CONFIG    = "/__SLASH__ config – Optionen öffnen",
    HELP_STATUS    = "/__SLASH__ status – Spielversion und Diagnose",
    HELP_TEST      = "/__SLASH__ test – eingebaute Testroutine starten",
    STATUS_ERRORS  = "Fehler in dieser Sitzung: %d",
    OPT_ENABLED    = "Aktiviert",
    OPT_CHAT       = "Meldungen im Chat zeigen",
    OPT_HINT       = "Änderungen gelten sofort.",
    IN_COMBAT      = "Im Kampf nicht möglich – wird nach dem Kampf erledigt.",
    TEST_RUNNING   = "Testroutine läuft …",
    TEST_DONE      = "Testroutine fertig: %d OK, %d Fehler, %d übersprungen, %d im Client prüfen.",
    TEST_RELOAD    = "Bitte nach dem Test /reload eingeben, damit der Bericht gespeichert wird.",
    COPY_HINT      = "Strg+C zum Kopieren, Esc zum Schliessen",
    CLOSE          = "Schliessen",
    UNKNOWN_CMD    = "Unbekannter Befehl. Hilfe mit /__SLASH__ help.",
}

-- Weitere Sprachen: hier ergänzen (fehlende Schlüssel nehmen Englisch) -------------------------------------------
local others = {
    frFR = {}, esES = {}, esMX = {}, itIT = {}, ptBR = {}, ruRU = {}, koKR = {}, zhCN = {}, zhTW = {},
}

-- Für die Testroutine: alle Tabellen zugänglich (Bereich F prüft Vollständigkeit)
ns.LOCALES = { enUS = enUS, deDE = deDE }
for k, v in pairs(others) do ns.LOCALES[k] = v end

-- L mit der aktiven Sprache füllen. Die anderen Dateien behalten "local L = ns.L": die Testroutine tauscht den
-- INHALT dieser Tabelle (ns.ApplyLocale), nie die Tabelle selbst.
function ns.ApplyLocale(code)
    for k in pairs(L) do L[k] = nil end
    for k, v in pairs(enUS) do L[k] = v end
    local t = ns.LOCALES[code]
    if t and t ~= enUS then
        for k, v in pairs(t) do L[k] = v end
    end
end

ns.ApplyLocale(ns.locale)

-- Unbekannter Schlüssel: den Schlüssel selbst zeigen statt eines Lua-Fehlers (fällt in der Testroutine auf)
setmetatable(L, { __index = function(_, key) return tostring(key) end })
