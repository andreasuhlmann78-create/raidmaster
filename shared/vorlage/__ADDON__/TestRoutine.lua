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
--   * Leistung: Die Routine läuft als Aufgabe von GoldSentinelTakt (Portionen, kein Bild über 40 ms). Zwischen zwei Fällen
--     gibt sie ab. Testdaten (Sandbox, ns.testing) gelten NUR während ihrer Portionen (Takt.Sliced) – in den Bildern
--     dazwischen sieht der übrige Code (Ereignisse, andere Addons) die echten Daten. Ein einzelner Fall läuft am Stück
--     (run:Check benutzt pcall): schwere Fälle in mehrere Fälle teilen.
--   * Absichtliche Testfehler NIE über den Fehler-Handler des Spiels (geterrorhandler) – sonst öffnet sich beim Spieler
--     das Fehlerfenster. Immer über ns.Try (zählt selbst) und danach aus dem Bericht entfernen (siehe T80).
--   * Für andere Addons sichtbar: __ADDON__API.TestRunning() ist während des ganzen Laufs true.
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

-- Felder, die sich während des Laufs von selbst ändern dürfen (Bericht, Protokoll, Zähler, Marktdaten-Netz, Prüfliste).
-- Sie werden weder kopiert noch verglichen – sonst hiesse jede Änderung zwischen zwei Portionen "Sandbox FEHLER", und
-- grosse Marktdaten zu kopieren kostete ein langes Bild.
ns.VOLATILE_KEYS = { gsTest = true, diag = true, diagExport = true, cmdUse = true, gsMarkt = true, pruefliste = true }

-- echte Daten ohne die Felder oben
local function DataOnly(db)
    local c = {}
    for k, v in pairs(db or {}) do
        if not ns.VOLATILE_KEYS[k] then c[k] = DeepCopy(v) end
    end
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
-- wait (optional): vor dem Fall warten, bis wait() true liefert (höchstens 10 s, ohne zu rechnen) – z. B. auf eine Aufgabe
local function Case(id, area, name, fn, wait) CASES[#CASES + 1] = { id = id, area = area, name = name, fn = fn, wait = wait } end

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

Case("T12", "B", "Optionen: jede Option in ihrem Bereich erreichbar, an/aus wirkt, zurück wie vorher", function()
    if not ns.optionsWindow then return false, "kein Optionen-Fenster", ADDON .. "OptionsFrame" end
    local seen, n = {}, 0
    for _, sec in ipairs(ns.OPTION_SECTIONS) do
        ns.ShowOptionSectionAll(sec.id)
        for key, ctl in pairs(ns.options) do
            seen[key] = true
            local o = ns.OptionByKey(key)
            if o and o.kind == "toggle" then
                local old = ns.db[key]
                ctl:SetChecked(not old); ctl:GetScript("OnClick")(ctl)
                if ns.db[key] == old then return false, key .. " unverändert", key .. " umgeschaltet" end
                ctl:SetChecked(old and true or false); ctl:GetScript("OnClick")(ctl)
                if (ns.db[key] and true or false) ~= (old and true or false) then return false, key .. " nicht zurück", "wie vorher" end
                n = n + 1
            end
        end
    end
    ns.CloseOptions()
    local missing = {}
    for _, o in ipairs(ns.OPTIONS) do if not seen[o.key] then missing[#missing + 1] = o.key end end
    return #missing == 0, n .. " umgeschaltet, fehlt: " .. (#missing == 0 and "nichts" or table.concat(missing, ",")), "alle erreichbar"
end)

Case("T24", "B", "Optionen: jede genau einmal, Standardwert, Bereich, Text ≤ Grenze in allen Sprachen, ≤ Zeilen je Bereich", function()
    local bad, keys, perSec, secs = {}, {}, {}, {}
    for _, sec in ipairs(ns.OPTION_SECTIONS) do secs[sec.id] = true end
    for _, o in ipairs(ns.OPTIONS) do
        if keys[o.key] then bad[#bad + 1] = o.key .. " doppelt" end
        keys[o.key] = true
        if ns.DEFAULTS[o.key] == nil then bad[#bad + 1] = o.key .. " ohne Standardwert" end
        if not secs[o.section] then bad[#bad + 1] = o.key .. " Bereich " .. tostring(o.section) end
        perSec[o.section] = (perSec[o.section] or 0) + 1
        for code, t in pairs(ns.LOCALES) do
            local txt = t[o.label] or ns.LOCALES.enUS[o.label]
            local len = txt and #txt:gsub("[\128-\191]", "") or 0          -- Zeichen, nicht Bytes (UTF-8)
            if not txt then bad[#bad + 1] = o.key .. " ohne Text"
            elseif len > ns.OPT_MAX_LABEL then bad[#bad + 1] = code .. ":" .. o.key .. " " .. len .. " Zeichen" end
        end
        for _, code in ipairs({ "enUS", "deDE" }) do
            if not ns.LOCALES[code][o.label .. "_TIP"] then bad[#bad + 1] = code .. ":" .. o.key .. " ohne Tooltip" end
        end
    end
    for id, cnt in pairs(perSec) do
        if cnt + 1 > ns.OPT_MAX_ROWS then bad[#bad + 1] = id .. " " .. cnt .. " Zeilen" end   -- +1 für "Weitere"
    end
    for _, sec in ipairs(ns.OPTION_SECTIONS) do
        if not perSec[sec.id] then bad[#bad + 1] = sec.id .. " leer" end
    end
    return #bad == 0, #ns.OPTIONS .. " Optionen in " .. #ns.OPTION_SECTIONS .. " Bereichen · " ..
        (#bad == 0 and "ok" or table.concat(bad, "; ")), "jede genau einmal, alles vorhanden"
end)

Case("T25", "B", "Optionen: Suche über alle Bereiche, Gegenprobe ohne Treffer", function()
    local hit = ns.FindOptions(ns.LOCALES[ns.locale] and ns.LOCALES[ns.locale].OPT_MARKET or L.OPT_MARKET)
    local byKey = ns.FindOptions("minimapbutton")
    local none = ns.FindOptions("xqzxqz")
    local empty = ns.FindOptions("")
    local ok = #hit >= 1 and hit[1].key == "marketShare" and #byKey == 1 and #none == 0 and #empty == 0
    return ok, string.format("Text %d (%s), Schlüssel %d, Unsinn %d, leer %d", #hit, hit[1] and hit[1].key or "-",
        #byKey, #none, #empty), "1+ marketShare, 1, 0, 0"
end)

Case("T26", "B", "Optionen: Standard setzt NUR den eigenen Bereich zurück; Weitere eingeklappt", function()
    local d, g = ns.DEFAULTS
    ns.SetOption("chat", not d.chat)
    ns.SetOption("marketShare", not d.marketShare)
    ns.ResetSection("general")
    local back = ns.db.chat == d.chat
    local other = ns.db.marketShare == (not d.marketShare)
    ns.SetOption("marketShare", d.marketShare)
    local closed = ns.VisibleOptions("data", "", false)
    local open = ns.VisibleOptions("data", "", true)
    local hasMore = closed[#closed] and closed[#closed].more == true
    return back and other and hasMore and #open == #closed + 1,
        string.format("zurück %s, anderer Bereich bleibt %s, Weitere %s, auf %d/zu %d", tostring(back), tostring(other),
        tostring(hasMore), #open, #closed), "true, true, true, auf = zu + 1"
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

Case("T16", "B", "Diagnose-Protokoll: Einträge, Zähler statt Schleife, Export GSDIAG1, keine Namen", function()
    if not (ns.Diag and ns.DiagText and ns.DiagExport) then return false, "Diag.lua fehlt", "ns.Diag/DiagText/DiagExport" end
    ns.db.diag = nil
    ns.Diag("KLICK", "Testeintrag", 12.4)
    for _ = 1, 50 do ns.Diag("FEHLER", "gleicher Fehler") end
    ns.Timed("Test langsam", function() local t = (debugprofilestop and debugprofilestop() or 0) + 17   -- knapp über 16 ms
        while debugprofilestop and debugprofilestop() < t do end end)
    if ns.GT then Swap(ns.GT, "Error", function() end) end   -- absichtlicher Fehler nicht in den echten Fehlerbericht
    ns.Try("T16 absichtlich", function() error("Testfehler (absichtlich)") end)
    Undo()
    local e = ns.db.diag.entries
    local fehler
    for _, x in ipairs(e) do if x.t == "gleicher Fehler" then fehler = x end end
    local text, exp = ns.DiagText(), ns.DiagExport()
    local who = UnitName and UnitName("player")
    local noName = not (type(who) == "string" and who ~= "" and text:find(who, 1, true))
    local slow = not debugprofilestop or text:find("LANGSAM", 1, true) ~= nil
    local ok = fehler and fehler.n == 50 and #e <= 5 and exp:sub(1, 8) == "GSDIAG1|" and noName and slow
        and text:find("T16 absichtlich", 1, true) ~= nil
    return ok and true or false, string.format("%d Einträge, Zähler %s, Export %s, Name %s, langsam %s",
        #e, fehler and fehler.n or "-", exp:sub(1, 8), noName and "nein" or "JA", tostring(slow)),
        "≤5 Einträge, Zähler 50, Export GSDIAG1|, Name nein, langsam true"
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

Case("T61", "G", "Testdaten-Regel: eigener Test sichtbar, fremder Test erkannt (Gegenprobe)", function()
    local api = _G[ADDON .. "API"]
    local mine = api and api.TestRunning and api.TestRunning()
    local fake = ADDON .. "FremdTestAPI"                   -- eigener Name, kein Blizzard-Global
    rawset(_G, fake, { TestRunning = function() return true end })
    local foreign = ns.ForeignTestRunning(ADDON .. "FremdTest")
    rawset(_G, fake, { TestRunning = function() return false end })
    local idle = ns.ForeignTestRunning(ADDON .. "FremdTest")
    rawset(_G, fake, nil)
    local none = ns.ForeignTestRunning("GibtEsNicht")
    return mine == true and foreign and not idle and not none,
        string.format("eigen %s, fremd läuft %s, fremd ruht %s, unbekannt %s", tostring(mine), tostring(foreign),
        tostring(idle), tostring(none)), "true, true, false, false"
end)

Case("T62", "G", "Gemeinsame Bausteine geladen (Game, Test, Sync, Dev, Prüfliste, Markt, Takt, Befehlsliste)", function()
    local miss = {}
    local want = { GoldSentinelGame = "version", GoldSentinelTest = "version", GoldSentinelSync = "version",
        GoldSentinelDev = "version", GoldSentinelPruefliste = "version", GoldSentinelMarkt = "VERSION",
        GoldSentinelTakt = "VERSION", GoldSentinelCmdHint = "VERSION" }
    for name, field in pairs(want) do
        local t = rawget(_G, name)
        if type(t) ~= "table" then miss[#miss + 1] = name end
    end
    table.sort(miss)
    return #miss == 0, #miss == 0 and "alle 8" or ("fehlt: " .. table.concat(miss, ", ")), "alle 8"
end)

-- H. Leistung ------------------------------------------------------------------------------------------------------
-- T71/T72: ns.Job rechnet in Portionen. T71 startet eine Aufgabe, T72 (läuft einige Bilder später) prüft das Ergebnis.
local jobProbe
Case("T71", "H", "ns.Job: Aufgabe startet (GoldSentinelTakt)", function()
    if not (ns.Takt and ns.Takt.Start) then return false, "kein GoldSentinelTakt", "Takt" end
    jobProbe = { sum = 0 }
    jobProbe.job = ns.Job("Testaufgabe", function()
        for i = 1, 2000 do
            jobProbe.sum = jobProbe.sum + i
            if i % 100 == 0 then ns.Check("T71 Schleife") end
        end
    end, { budget = 1, timeout = 30 })
    return jobProbe.job ~= nil, jobProbe.job and tostring(jobProbe.job.state) or "nil", "Aufgabe angelegt"
end)
Case("T70", "H", "Statuszeile < 2 ms je Aufruf", function()
    if not debugprofilestop then return true, "keine Zeitmessung" end
    local t = debugprofilestop()
    for _ = 1, 50 do ns.StatusText() end
    local per = (debugprofilestop() - t) / 50
    return per < 2, string.format("%.3f ms", per), "< 2 ms"
end)

Case("T72", "H", "ns.Job: Aufgabe fertig, richtiges Ergebnis, Messwerte vorhanden", function()
    if not (jobProbe and jobProbe.job) then return false, "T71 lief nicht", "T71 zuerst" end
    local j = jobProbe.job
    local st = j.stats or {}
    return j.state == "fertig" and jobProbe.sum == 2001000 and (st.frames or 0) >= 1,
        string.format("%s, Summe %d, Bilder %s", tostring(j.state), jobProbe.sum, tostring(st.frames)),
        "fertig, Summe 2001000, Bilder >= 1"
end, function() return not (jobProbe and jobProbe.job) or jobProbe.job.state ~= "laeuft" end)

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
-- Ein Lauf: alle Fälle (gefiltert), Oberfläche, Hinweise für den echten Client. Läuft in Portionen (Takt.Sliced).
local function Body(run, filter)
    for _, c in ipairs(CASES) do
        if filter == "" or c.area == filter then
            if c.wait and ns.Takt and ns.Takt.WaitFor then ns.Takt.WaitFor(c.wait, 10) end
            if ns.Takt and ns.Takt.Label then ns.Takt.Label(c.id) end   -- Etikett: lange Bilder nennen den Fall
            run:Check(c.id, c.area, c.name, c.fn)
            Undo()                                   -- falls ein Fall abgebrochen ist
            ns.Check(c.id)                           -- Abgabe zwischen zwei Fällen, wenn das Budget verbraucht ist
        end
    end
    -- Oberfläche im echten Client (UICheck.lua): ohne echten Client ehrlich übersprungen, nie als OK gezählt
    if (filter == "" or filter == "K") and ns.UICheck then
        local U = ns.UICheck
        local wasShown = ns.window and ns.window:IsShown()
        if ns.window and not wasShown and ns.ToggleWindow then ns.ToggleWindow() end   -- eigenes Fenster zum Prüfen öffnen
        local function List(problems) return #problems == 0 and "keine" or table.concat(problems, "; ") end
        local ui = {
            { "TK18", "Eigene Tooltips verdecken keine Knöpfe", U.TooltipsCoverNothing },
            { "TK19", "Kein Überlappen mit Blizzard- oder GoldSentinel-Fenstern", U.WindowsOverlapNothing },
            { "TK20", "Fenster ganz im Bildschirm", U.InsideScreen },
            { "TK21", "Beschriftungen von Knöpfen nicht abgeschnitten", U.TextFits },
            { "TK22", "Angezeigte Spielwerte plausibel", U.ValuesPlausible, true },
            { "TK23", "Keine Fehlerschleife (gleiche Meldung > 10×)", U.NoErrorLoops, true },
        }
        for _, c in ipairs(ui) do
            if not c[4] and not U.Available() then
                run:Skip(c[1], "K", c[2], "nur im echten Client (Fenster, Rechtecke, Tooltip)")
            else
                run:Check(c[1], "K", c[2], function()
                    local problems, tested, hints = c[3]()
                    local info = List(problems) .. " · geprüft " .. tostring(tested)
                        .. (hints and #hints > 0 and (" · Hinweise: " .. table.concat(hints, "; ")) or "")
                    return #problems == 0, info, "keine"
                end)
            end
            ns.Check(c[1])
        end
        if ns.window and not wasShown and ns.window:IsShown() and ns.ToggleWindow then ns.ToggleWindow() end
    end
    -- Hinweise für den Launch-Abend: was nur im echten Client prüfbar ist
    if filter == "" or filter == "B" then
        run:Client("T17", "B", "Diagnose-Protokoll im Spiel",
            "/__SLASH__ protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt __ADDON__DB.diagExport (beginnt mit GSDIAG1) in den SavedVariables")
        run:Client("T15", "B", "Minimap-Button im Spiel",
            "Button an der Minimap sichtbar, Tooltip in der Sprache des Clients, Ziehen verschiebt ihn, nach /reload am selben Ort")
        run:Client("T27", "B", "Optionen am Bild",
            "/__SLASH__ config: jeden Bereich anklicken, Suche ausprobieren, nichts überlappt, nichts abgeschnitten (Prüfliste OPT)")
    end
    if filter == "" or filter == "C" then
        run:Client("T29", "C", "Geschützte Werte im echten Kampf",
            "In WoW Forever einen Kampf mit Ziel führen, danach /__SLASH__ status: Fehler = 0")
    end
end

function ns.RunTests(filter)
    if G.InCombat() then ns.Print(L.IN_COMBAT); return end
    if ns.testRunning then ns.Print(L.TEST_BUSY); return end
    filter = (filter or ""):upper():match("^%a?") or ""
    local real = ns.db
    local before = DataOnly(real)
    local sandbox = DeepCopy(before)
    for k in pairs(ns.VOLATILE_KEYS) do sandbox[k] = DeepCopy(real[k]) end   -- Tests dürfen sie benutzen (nur Kopie)
    sandbox.gsMarkt = nil                                                     -- Marktdaten nie kopieren (gross)

    ns.realDB = real
    ns.testRunning = true
    ns.printLog = {}
    local run = GT.Begin(ADDON, ns.VERSION, real)

    -- Testdaten nur während der eigenen Portionen; dazwischen sieht der übrige Code die echten Daten
    local function Enter() ns.testing = true; ns.db = sandbox end
    local function Leave() ns.testing = false; ns.db = real end

    local function Done(job)
        Leave()
        ns.testRunning = false
        ns.realDB = nil
        local sb = Same(before, DataOnly(real)) and "OK" or "FEHLER – echte Daten wurden verändert"
        local extra = { sandbox = sb, filter = filter ~= "" and filter or "alle" }
        local takt = job and ns.Takt and ns.Takt.Summary and ns.Takt.Summary(job) or nil
        if takt then extra.takt = takt end
        if job and job.state ~= "fertig" then extra.abbruch = tostring(job.state) .. ": " .. tostring(job.err) end
        local text, rep = run:Finish(extra)
        if takt then text = text .. "\nTakt: " .. takt end
        local env = ns.Takt and ns.Takt.EnvLine and ns.Takt.EnvLine() or ""
        if env ~= "" then text = text .. "\n" .. env end          -- Ort, Spieler in Sicht, Ping, Bildzeit in Ruhe (Takt v2)
        if extra.abbruch then text = text .. "\nABBRUCH: " .. extra.abbruch end
        local c = rep and rep.counts or run.counts
        ns.lastReport = rep
        ns.testJob = nil
        if ns.pruefliste and ns.pruefliste.Hit and job and job.stats and job.stats.over and job.stats.over[3] == 0 then
            ns.pruefliste:Hit("TEST", takt)
        end
        ns.Print(L.TEST_DONE:format(c.ok, c.fehler, c.uebersprungen, c.client))
        ns.Print(L.TEST_RELOAD)
        if ns.ShowCopy then ns.ShowCopy(text) end
    end

    local T = ns.Takt
    if T and T.Start and T.Sliced then
        ns.Print(L.TEST_RUNNING)
        ns.testJob = T.Start({
            name = "Testroutine", owner = ADDON, budget = 4, timeout = 600,
            env = 10,                                                   -- erst 10 s Umgebung messen (Takt v2; v1: ohne Wirkung)
            fn = function()
                local ok, err = T.Sliced(Body, Enter, Leave, run, filter)
                if ok == false then error(err, 0) end                  -- Abbruch im Bericht (ABBRUCH), nie still
            end,
            onDone = function(job) ns.Try("Testroutine Ende", Done, job) end,
        })
    else
        -- ohne GoldSentinelTakt (sollte nie vorkommen): am Stück
        Enter()
        ns.Try("Testroutine", Body, run, filter)
        Done(nil)
    end
    return ns.testJob
end
