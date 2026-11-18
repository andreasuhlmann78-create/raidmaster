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
    HELP_MINIMAP   = "/__SLASH__ minimap – show or hide the minimap button",
    HELP_STATUS    = "/__SLASH__ status – game version and diagnostics",
    HELP_PROTOKOLL = "/__SLASH__ protokoll – diagnostic log to copy and send",
    OPT_DIAG       = "Send diagnostic log",
    OPT_DIAG_TIP   = "Store the diagnostic log at logout so that the uploader sends it to the test team (no names).",
    HELP_TEST      = "/__SLASH__ test – run the built-in test routine",
    STATUS_ERRORS  = "Errors recorded in this session: %d",
    OPT_ENABLED    = "Enabled",
    OPT_ENABLED_TIP = "Switch the addon on or off.",
    OPT_CHAT       = "Chat messages",
    OPT_CHAT_TIP   = "Show messages of the addon in the chat window.",
    OPT_MINIMAP    = "Minimap button",
    OPT_MINIMAP_TIP = "Show the button at the minimap (left-click window, right-click options).",
    OPT_CMDHINT    = "Command list while typing",
    OPT_CMDHINT_TIP = "Show the commands above the chat box while you type /__SLASH__.",
    OPT_MARKET     = "Share market data",
    OPT_MARKET_TIP = "Share auction prices anonymously with other GoldSentinel addons (no names). Off in one addon = off for all.",
    OPT_TITLE      = "Options",
    OPT_SEARCH     = "Search",
    OPT_DEFAULTS   = "Defaults",
    OPT_MORE       = "More",
    OPT_OPEN       = "Open options",
    OPT_NO_HITS    = "No matching option.",
    SEC_GENERAL    = "General",
    SEC_DATA       = "Data & sharing",
    HELP_PRUEFLISTE = "/__SLASH__ prüfliste – checklist (developer only)",
    CMD_TOGGLE     = "Show or hide the window",
    CMD_CONFIG     = "Open the options",
    CMD_MINIMAP    = "Minimap button on/off",
    CMD_STATUS     = "Game version and diagnostics",
    CMD_PROTOKOLL  = "Diagnostic log to copy",
    CMD_TEST       = "Run the test routine",
    CMD_HELP       = "Show the commands",
    CMD_PRUEFLISTE = "Checklist (developer)",
    CMD_NOMATCH    = "No command – /__SLASH__ help",
    CMD_ENTER      = "Enter = %s",
    PL_OPT_TITLE   = "Options at a glance",
    PL_OPT_TODO    = "Type /__SLASH__ config, click every area, search for one option, press Defaults once.",
    PL_OPT_EXPECT  = "Every option found in under 5 seconds, nothing overlaps or is cut off.",
    PL_TEST_TITLE  = "Test routine without stutter",
    PL_TEST_TODO   = "Type /__SLASH__ test and keep playing while it runs.",
    PL_TEST_EXPECT = "No stutter; report line Takt: no frame over 40 ms.",
    DEV_ONLY       = "Only in developer mode (/gsdev).",
    MINIMAP_LEFT   = "Left-click: open or close the window",
    MINIMAP_RIGHT  = "Right-click: options",
    MINIMAP_DRAG   = "Drag: move around the minimap",
    IN_COMBAT      = "Not possible in combat – will be done after the fight.",
    TEST_RUNNING   = "Test routine running …",
    TEST_DONE      = "Test routine finished: %d OK, %d errors, %d skipped, %d to check in the client.",
    TEST_BUSY      = "The test routine is already running.",
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
    HELP_MINIMAP   = "/__SLASH__ minimap – Minimap-Button zeigen oder ausblenden",
    HELP_STATUS    = "/__SLASH__ status – Spielversion und Diagnose",
    HELP_PROTOKOLL = "/__SLASH__ protokoll – Diagnose-Protokoll zum Kopieren und Senden",
    OPT_DIAG       = "Diagnose senden",
    OPT_DIAG_TIP   = "Diagnose-Protokoll beim Ausloggen ablegen, damit der Uploader es an die Prüfung schickt (ohne Namen).",
    HELP_TEST      = "/__SLASH__ test – eingebaute Testroutine starten",
    STATUS_ERRORS  = "Fehler in dieser Sitzung: %d",
    OPT_ENABLED    = "Aktiviert",
    OPT_ENABLED_TIP = "Addon ein- oder ausschalten.",
    OPT_CHAT       = "Meldungen im Chat",
    OPT_CHAT_TIP   = "Meldungen des Addons im Chatfenster zeigen.",
    OPT_MINIMAP    = "Minimap-Knopf",
    OPT_MINIMAP_TIP = "Knopf an der Minimap zeigen (Linksklick Fenster, Rechtsklick Optionen).",
    OPT_CMDHINT    = "Befehlsliste beim Tippen",
    OPT_CMDHINT_TIP = "Beim Tippen von /__SLASH__ die Befehle über dem Chat-Eingabefeld zeigen.",
    OPT_MARKET     = "Marktdaten teilen",
    OPT_MARKET_TIP = "Auktionspreise anonym mit anderen GoldSentinel-Addons teilen (keine Namen). In einem Addon aus = in allen aus.",
    OPT_TITLE      = "Optionen",
    OPT_SEARCH     = "Suchen",
    OPT_DEFAULTS   = "Standard",
    OPT_MORE       = "Weitere",
    OPT_OPEN       = "Optionen öffnen",
    OPT_NO_HITS    = "Keine passende Option.",
    SEC_GENERAL    = "Allgemein",
    SEC_DATA       = "Daten & Teilen",
    HELP_PRUEFLISTE = "/__SLASH__ prüfliste – Prüfliste (nur Entwickler)",
    CMD_TOGGLE     = "Fenster zeigen oder ausblenden",
    CMD_CONFIG     = "Optionen öffnen",
    CMD_MINIMAP    = "Minimap-Knopf an/aus",
    CMD_STATUS     = "Spielversion und Diagnose",
    CMD_PROTOKOLL  = "Diagnose-Protokoll zum Kopieren",
    CMD_TEST       = "Testroutine starten",
    CMD_HELP       = "Befehle anzeigen",
    CMD_PRUEFLISTE = "Prüfliste (Entwickler)",
    CMD_NOMATCH    = "Kein Befehl – /__SLASH__ help",
    CMD_ENTER      = "Enter = %s",
    PL_OPT_TITLE   = "Optionen am Bild",
    PL_OPT_TODO    = "/__SLASH__ config eingeben, jeden Bereich anklicken, eine Option suchen, einmal Standard drücken.",
    PL_OPT_EXPECT  = "Jede Option in unter 5 Sekunden gefunden, nichts überlappt oder ist abgeschnitten.",
    PL_TEST_TITLE  = "Testroutine ohne Ruckeln",
    PL_TEST_TODO   = "/__SLASH__ test eingeben und weiterspielen, während sie läuft.",
    PL_TEST_EXPECT = "Kein Ruckeln; Berichtszeile Takt: kein Bild über 40 ms.",
    DEV_ONLY       = "Nur im Entwicklermodus (/gsdev).",
    MINIMAP_LEFT   = "Linksklick: Fenster öffnen oder schliessen",
    MINIMAP_RIGHT  = "Rechtsklick: Optionen",
    MINIMAP_DRAG   = "Ziehen: um die Minimap verschieben",
    IN_COMBAT      = "Im Kampf nicht möglich – wird nach dem Kampf erledigt.",
    TEST_RUNNING   = "Testroutine läuft …",
    TEST_DONE      = "Testroutine fertig: %d OK, %d Fehler, %d übersprungen, %d im Client prüfen.",
    TEST_BUSY      = "Die Testroutine läuft schon.",
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
