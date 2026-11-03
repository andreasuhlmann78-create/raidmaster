-- __ADDON__ – eingebaute Testroutine (/__SLASH__ test)
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Aufbau nach der Vorgabe der Prüf-Sitzung (Bereiche A–J). Der Bericht wird über GoldSentinelTest in
-- __ADDON__DB.gsTest gespeichert und beim nächsten /reload oder Ausloggen an die Prüfung gemeldet.
--
-- Regeln im Test (die Addon-Prüfung kontrolliert sie):
--   * Nur EIGENE Tabellen ersetzen (ns.API, ns, G-Hilfen) – nie eine Blizzard-Funktion, auch nicht kurz und nicht über Stub().
--   * Aktionen mit Folgen laufen über ns.Act und werden im Test nur mitgeschrieben (ns.testing = true).
--   * Echte Daten (Sandbox): vorher kopieren, im Test eine Kopie benutzen, nachher vergleichen.
--   * Nur ausserhalb des Kampfes starten.
--
-- Neue Funktionen des Addons bekommen hier eigene Fälle (Bereich B), jeder Befund der Prüf-Sitzung einen Fall in J.
-- Aufruf: /__SLASH__ test        alles
--         /__SLASH__ test B      nur Bereich B (Buchstabe A–J)

local ADDON, ns = ...
local L = ns.L
local G = ns.G
local GT = ns.GT

---------------------------------------------------------------------------------------------------------------------
-- Hilfen
---------------------------------------------------------------------------------------------------------------------
local undo = {}

-- Eintrag einer EIGENEN Tabelle vorübergehend ersetzen; Undo() stellt alles wieder her
local function Swap(tbl, key, value)
    undo[#undo + 1] = { tbl, key, rawget(tbl, key) }
    tbl[key] = value
end

local function Undo()
    for i = #undo, 1, -1 do
        local e = undo[i]
        e[1][e[2]] = e[3]
    end
    undo = {}
end

local function DeepCopy(v, seen)
    if type(v) ~= "table" then return v end
    seen = seen or {}
    if seen[v] then return seen[v] end
    local c = {}
    seen[v] = c
    for k, x in pairs(v) do c[DeepCopy(k, seen)] = DeepCopy(x, seen) end
    return c
end

local function Same(a, b)
    if type(a) ~= type(b) then return false end
    if type(a) ~= "table" then return a == b end
    for k, v in pairs(a) do if not Same(v, b[k]) then return false end end
    for k in pairs(b) do if a[k] == nil then return false end end
    return true
end

-- echte Daten ohne den Testbericht selbst (gsTest ändert sich durch den Bericht absichtlich)
local function DataOnly(db)
    local c = DeepCopy(db or {})
    c.gsTest = nil
    return c
end

local function CountPlaceholders(s)
    local n = 0
    for _ in tostring(s):gmatch("%%[%d%.]*[sdfx]") do n = n + 1 end
    return n
end

local SECRET = setmetatable({}, { __tostring = function() return "<geschützt>" end })   -- Attrappe

---------------------------------------------------------------------------------------------------------------------
-- Testfälle
---------------------------------------------------------------------------------------------------------------------
local CASES = {}
local function Case(id, area, name, fn) CASES[#CASES + 1] = { id = id, area = area, name = name, fn = fn } end

-- A. Laden und Erkennung -------------------------------------------------------------------------------------------
Case("T01", "A", "Version in .toc = Code", function()
    local meta = ns.API.GetAddOnMeta and ns.API.GetAddOnMeta(ADDON, "Version")
    return meta == ns.VERSION, tostring(ns.VERSION), tostring(meta)
end)

Case("T02", "A", "GoldSentinelGame mindestens Version 2", function()
    return type(G) == "table" and (G.version or 0) >= 2, tostring(G and G.version), ">= 2"
end)

Case("T03", "A", "GoldSentinelTest vorhanden", function()
    return type(GT) == "table" and type(GT.Begin) == "function", tostring(GT and GT.version), ">= 1"
end)

Case("T04", "A", "Weichen je Client (SetTestFlavor)", function()
    local seen = {}
    for _, f in ipairs({ "forever", "era", "tbc", "retail" }) do
        G.SetTestFlavor(f)
        seen[#seen + 1] = f .. "=" .. (G.IsModern and "modern" or "alt")
        if (f == "forever" or f == "retail") ~= (G.IsModern == true) then
            G.SetTestFlavor(nil)
            return false, table.concat(seen, ","), "forever/retail modern, era/tbc alt"
        end
    end
    G.SetTestFlavor(nil)
    return true, table.concat(seen, ",")
end)

-- B. Funktionen des Addons (für jede neue Funktion hier Fälle ergänzen) --------------------------------------------
Case("T10", "B", "Befehle: alle Unterbefehle ohne Fehler", function()
    local before = ns.errorCount
    for _, cmd in ipairs({ "help", "status", "" }) do SlashCmdList.__SLASH_GROSS__(cmd) end
    SlashCmdList.__SLASH_GROSS__("gibtsnicht")
    if ns.window and ns.window:IsShown() then ns.window:Hide() end
    return ns.errorCount == before, ns.errorCount - before .. " Fehler", "0 Fehler"
end)

Case("T11", "B", "Hauptfenster öffnen und schliessen", function()
    if not ns.window then return false, "kein Fenster", "Fenster" end
    ns.ToggleWindow(); local shown = ns.window:IsShown()
    ns.ToggleWindow(); local hidden = not ns.window:IsShown()
    return shown and hidden, tostring(shown) .. "/" .. tostring(hidden), "true/true"
end)

Case("T12", "B", "Optionen: jede einmal an und aus", function()
    for key, cb in pairs(ns.options) do
        local old = ns.db[key]
        cb:SetChecked(not old); cb:GetScript("OnClick")(cb)
        if ns.db[key] == old then return false, key .. " unverändert", key .. " umgeschaltet" end
        cb:SetChecked(old); cb:GetScript("OnClick")(cb)
    end
    return true
end)

Case("T14", "B", "Minimap-Button: da, aus- und einblenden, Winkel bleibt", function()
    local b = _G[ADDON .. "MinimapButton"]
    if not b then return false, "kein Button", ADDON .. "MinimapButton" end
    local wasOn, wasAngle = ns.db.minimapButton, ns.db.minimapAngle
    ns.db.minimapButton = true; ns.db.minimapAngle = 90; ns.UpdateMinimapButton()
    local shown = b:IsShown()
    ns.ToggleMinimapButton(); local hidden = not b:IsShown()
    ns.ToggleMinimapButton(); local back = b:IsShown()
    local angle = ns.db.minimapAngle
    ns.db.minimapButton, ns.db.minimapAngle = wasOn, wasAngle; ns.UpdateMinimapButton()
    return shown and hidden and back and angle == 90,
        tostring(shown) .. "/" .. tostring(hidden) .. "/" .. tostring(back) .. ", Winkel " .. tostring(angle), "true/true/true, Winkel 90"
end)

Case("T13", "B", "Aktionen laufen nur über ns.Act (im Test nur mitgeschrieben)", function()
    local n = #ns.actLog
    local done = ns.SendChat("Test", "SAY")
    return done == false and #ns.actLog == n + 1, tostring(done) .. ", " .. (#ns.actLog - n) .. " mitgeschrieben",
        "false, 1 mitgeschrieben"
end)

-- C. Forever-Sonderfälle -------------------------------------------------------------------------------------------
Case("T20", "C", "Geschützter Ziel-Name: kein Fehler, nil zurück", function()
    Swap(ns.API, "UnitName", function() return SECRET end)
    Swap(G, "IsSecret", function(v) return v == SECRET end)
    local ok, name = pcall(ns.SafeUnitName, "target")
    Undo()
    return ok and name == nil, ok and tostring(name) or "Lua-Fehler", "nil"
end)

Case("T21", "C", "Fehlende alte Funktionen: moderner Ersatz oder sauber nil", function()
    Swap(ns.API, "GetItemInfo", nil)
    local ok = pcall(function() return ns.API.GetItemInfo and ns.API.GetItemInfo(6948) end)
    Undo()
    return ok, ok and "kein Fehler" or "Lua-Fehler"
end)

Case("T22", "C", "Kampfsperre: geschützte Aktion wird aufgeschoben", function()
    Swap(G, "InCombat", function() return true end)
    local ran = false
    local now = ns.WhenOutOfCombat(function() ran = true end)
    Undo()
    local queued = #ns.afterCombat
    ns.handlers.PLAYER_REGEN_ENABLED[1]()          -- Kampfende nachstellen (eigener Handler)
    return now == false and queued >= 1 and ran, string.format("sofort=%s, wartend=%d, danach=%s", tostring(now), queued, tostring(ran)),
        "sofort=false, wartend>=1, danach=true"
end)

Case("T23", "C", "Kampflog im modernen Client nicht registriert", function()
    if not G.IsModern then return true, "alter Client" end
    local reg = ns.eventFrame.IsEventRegistered and ns.eventFrame:IsEventRegistered("COMBAT_LOG_EVENT_UNFILTERED")
    return not reg, tostring(reg), "false"
end)

-- D. Alte Clients --------------------------------------------------------------------------------------------------
Case("T30", "D", "Auren auf dem alten Weg (ohne C_UnitAuras)", function()
    if C_UnitAuras then return true, "moderner Client – nur in Era/TBC aussagekräftig" end
    local ok = pcall(ns.API.GetAura, "player", 1, "HELPFUL")
    return ok, ok and "kein Fehler" or "Lua-Fehler"
end)

-- E. Daten ---------------------------------------------------------------------------------------------------------
Case("T40", "E", "Neuinstallation: leere Einstellungen bekommen alle Standardwerte", function()
    local db = ns.InitDB(nil)
    return db.enabled == true and type(db.window) == "table" and db.dbVersion == ns.DB_VERSION
end)

Case("T41", "E", "Beschädigte Einträge (falscher Typ) -> kein Fehler, Standard", function()
    local db = ns.InitDB({ window = "kaputt", enabled = nil, dbVersion = "x" })
    return type(db.window) == "table" and db.enabled == true, type(db.window), "table"
end)

Case("T42", "E", "Migration aus älterer Fassung", function()
    local db = ns.InitDB({ dbVersion = 0, chat = false })
    return db.dbVersion == ns.DB_VERSION and db.chat == false, tostring(db.chat), "false (Wert bleibt erhalten)"
end)

-- F. Sprachen ------------------------------------------------------------------------------------------------------
Case("T50", "F", "Jeder Schlüssel auf Deutsch vorhanden, gleiche Platzhalter", function()
    local en, de, bad = ns.LOCALES.enUS, ns.LOCALES.deDE, {}
    for k, v in pairs(en) do
        if de[k] == nil then bad[#bad + 1] = k .. " fehlt"
        elseif CountPlaceholders(v) ~= CountPlaceholders(de[k]) then bad[#bad + 1] = k .. " Platzhalter" end
    end
    return #bad == 0, table.concat(bad, ", "), "alles vorhanden"
end)

Case("T51", "F", "Weitere Sprachen: gleiche Platzhalter wie Englisch", function()
    local en, bad = ns.LOCALES.enUS, {}
    for code, t in pairs(ns.LOCALES) do
        for k, v in pairs(t) do
            if en[k] == nil then bad[#bad + 1] = code .. ":" .. k .. " unbekannt"
            elseif CountPlaceholders(v) ~= CountPlaceholders(en[k]) then bad[#bad + 1] = code .. ":" .. k end
        end
    end
    return #bad == 0, table.concat(bad, ", "), "keine Abweichung"
end)

Case("T52", "F", "Jede Sprache aktivieren und Fenster öffnen", function()
    local active = ns.locale
    for code in pairs(ns.LOCALES) do
        ns.ApplyLocale(code)
        if ns.window then ns.window:Show(); ns.window:Hide() end
    end
    ns.ApplyLocale(active)
    return true
end)

-- G. Zusammenspiel -------------------------------------------------------------------------------------------------
Case("T60", "G", "Eigenes Global zeigt auf den Namensraum", function()
    return _G[ADDON] == ns
end)

-- H. Leistung ------------------------------------------------------------------------------------------------------
Case("T70", "H", "Statuszeile < 2 ms je Aufruf", function()
    if not debugprofilestop then return true, "keine Zeitmessung" end
    local t = debugprofilestop()
    for _ = 1, 50 do ns.StatusText() end
    local per = (debugprofilestop() - t) / 50
    return per < 2, string.format("%.3f ms", per), "< 2 ms"
end)

-- I. Fehlerzählung -------------------------------------------------------------------------------------------------
Case("T80", "I", "Absichtlicher Fehler wird gezählt und gemeldet", function()
    local before = ns.errorCount
    ns.Try("Testroutine-Absicht", function() error("absichtlicher Testfehler", 0) end)
    local counted = ns.errorCount == before + 1
    -- wieder entfernen, damit er nicht als echter Fehler an die Prüfung geht
    ns.errorCount = before
    local s = ns.realDB and ns.realDB.gsTest
    local found = false
    if s and s.errors then
        for key, e in pairs(s.errors) do
            if type(e) == "table" and e.wo == "Testroutine-Absicht" then s.errors[key] = nil; found = true end
        end
    end
    return counted and found, string.format("gezählt=%s, gemeldet=%s", tostring(counted), tostring(found)), "true/true"
end)

-- J. Regressionstests (je Befund der Prüf-Sitzung ein Fall) ---------------------------------------------------------
-- Case("T90", "J", "Befund aus offen-__ADDON_KLEIN__.txt Punkt 1: …", function() ... end)

---------------------------------------------------------------------------------------------------------------------
-- Ablauf
---------------------------------------------------------------------------------------------------------------------
function ns.RunTests(filter)
    if G.InCombat() then ns.Print(L.IN_COMBAT); return end
    filter = (filter or ""):upper():match("^%a?") or ""
    local real = ns.db
    ns.realDB = real
    local before = DataOnly(real)

    -- Sandbox: Testkopie statt echter Daten, Aktionen nur mitschreiben
    ns.testing = true
    ns.printLog = {}
    ns.db = DeepCopy(before)

    local run = GT.Begin(ADDON, ns.VERSION, real)
    for _, c in ipairs(CASES) do
        if filter == "" or c.area == filter then
            run:Check(c.id, c.area, c.name, c.fn)
            Undo()                                   -- falls ein Fall abgebrochen ist
        end
    end
    -- Hinweise für den Launch-Abend: was nur im echten Client prüfbar ist
    if filter == "" or filter == "B" then
        run:Client("T15", "B", "Minimap-Button im Spiel",
            "Button an der Minimap sichtbar, Tooltip in der Sprache des Clients, Ziehen verschiebt ihn, nach /reload am selben Ort")
    end
    if filter == "" or filter == "C" then
        run:Client("T29", "C", "Geschützte Werte im echten Kampf",
            "In WoW Forever einen Kampf mit Ziel führen, danach /__SLASH__ status: Fehler = 0")
    end

    -- Sandbox zurück und vergleichen
    ns.db = real
    ns.testing = false
    ns.realDB = nil
    local sandbox = Same(before, DataOnly(real)) and "OK" or "FEHLER – echte Daten wurden verändert"

    local text, rep = run:Finish({ sandbox = sandbox, filter = filter ~= "" and filter or "alle" })
    local c = rep and rep.counts or run.counts
    ns.lastReport = rep
    ns.Print(L.TEST_DONE:format(c.ok, c.fehler, c.uebersprungen, c.client))
    ns.Print(L.TEST_RELOAD)
    if ns.ShowCopy then ns.ShowCopy(text) end
    return rep
end
