-- __ADDON__ – Prüfung der Oberfläche im echten Client (Testfälle T18–T23)
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Anlass (Live-Test 5. Nov. 2026): eigene Tooltips verdeckten Knöpfe, Fenster lagen übereinander, Anzeigen rechneten
-- mit falschen Spielwerten (Fertigkeit 0), ein Fehler kam 588×. Offline sieht man das nicht – darum prüft die
-- Testroutine es im Spiel selbst. Nur lesen, nichts verändern.
--
-- Benutzung im eigenen Code:
--   ns.RegisterUI(frame, "Name")                 -- jedes eigene Fenster anmelden (UI.lua macht das für Haupt-/Kopierfenster)
--   ns.RegisterUI(frame, "Name", "hud")          -- frei verschiebbare Kampfanzeige (Leisten, Symbole, Anker): wird
--                                                   selbst geprüft, kommt aber NICHT in die gemeinsame Liste – andere
--                                                   Addons sollen sich nicht an Kampfanzeigen stossen (wie ThreatSentinel)
--   ns.Plausible("Fertigkeit", function() return skill > 0, skill, "> 0" end)   -- Spielwert-Prüfung für T22
-- Andere GoldSentinel-Addons melden ihre Fenster in der globalen Liste GoldSentinelUIFrames an (T19 prüft gegeneinander).

local ADDON, ns = ...

ns.uiFrames = ns.uiFrames or {}
ns.plausible = ns.plausible or {}
ns.UI_LOOP_LIMIT = 10                       -- dieselbe Fehlermeldung öfter -> Fehlerschleife (T23)

-- Blizzard-Fenster, an die GoldSentinel-Addons andocken (dürfen nicht überdeckt werden)
ns.UI_BLIZZARD = { "ProfessionsFrame", "TradeSkillFrame", "CraftFrame", "MerchantFrame", "AuctionHouseFrame",
                   "AuctionFrame", "MailFrame", "QuestLogFrame", "WorldMapFrame", "CharacterFrame" }

GoldSentinelUIFrames = GoldSentinelUIFrames or {}

function ns.RegisterUI(frame, name, kind)
    if not frame then return end
    for _, e in ipairs(ns.uiFrames) do if e.frame == frame then return end end
    local e = { frame = frame, name = name or (frame.GetName and frame:GetName()) or ADDON, hud = (kind == "hud") }
    ns.uiFrames[#ns.uiFrames + 1] = e
    -- Kampfanzeigen nicht in die gemeinsame Liste (Befund 10.11.: BuffSentinel-Anker galten bei anderen als "überdeckt")
    if not e.hud then
        GoldSentinelUIFrames[#GoldSentinelUIFrames + 1] = { frame = frame, name = e.name, addon = ADDON }
    end
end

function ns.Plausible(name, fn) ns.plausible[#ns.plausible + 1] = { name = name, fn = fn } end

local U = {}
ns.UICheck = U

-- Ist der echte Client da (Rechtecke, Kinder, Tooltip)? Sonst werden die Fälle ehrlich übersprungen.
function U.Available()
    local f = ns.uiFrames[1] and ns.uiFrames[1].frame
    return f and type(f.GetRect) == "function" and type(f.GetChildren) == "function"
        and type(GameTooltip) == "table" and type(GameTooltip.GetRect) == "function"
        and type(UIParent) == "table" and type(UIParent.GetRect) == "function" and true or false
end

function U.Rect(f)
    if not (f and f.GetRect) then return nil end
    local ok, l, b, w, h = pcall(f.GetRect, f)
    if not ok or not l or not w or w <= 0 or h <= 0 then return nil end
    local s = f.GetEffectiveScale and f:GetEffectiveScale() or 1
    return { l = l * s, b = b * s, r = (l + w) * s, t = (b + h) * s }
end

-- Fläche der Überschneidung (0 = keine). Ein Pixel Rand gilt als "angedockt", nicht als Überlappen.
function U.Overlap(a, c)
    if not (a and c) then return 0 end
    local w = math.min(a.r, c.r) - math.max(a.l, c.l) - 1
    local h = math.min(a.t, c.t) - math.max(a.b, c.b) - 1
    return (w > 0 and h > 0) and w * h or 0
end

local function Shown(f) return f and f.IsVisible and f:IsVisible() end

local function Name(f)
    local n = f and f.GetName and f:GetName()
    if n then return n end
    local t = f and f.GetText and f:GetText()
    return t and ("'" .. tostring(t) .. "'") or tostring(f and f.GetObjectType and f:GetObjectType() or "?")
end

-- alle sichtbaren Nachfahren eines Fensters
function U.Descendants(f, out)
    out = out or {}
    if not (f and f.GetChildren) then return out end
    for _, c in ipairs({ f:GetChildren() }) do
        if Shown(c) then out[#out + 1] = c; U.Descendants(c, out) end
    end
    return out
end

local function IsControl(f)
    return f.IsObjectType and (f:IsObjectType("Button") or f:IsObjectType("EditBox") or f:IsObjectType("CheckButton")
        or f:IsObjectType("Slider")) and true or false
end

-- T18: kein eigener Tooltip verdeckt einen Knopf desselben Fensters
function U.TooltipsCoverNothing()
    local problems, tested = {}, 0
    for _, e in ipairs(ns.uiFrames) do
        if Shown(e.frame) then
            local all = U.Descendants(e.frame)
            for _, el in ipairs(all) do
                local enter = el.GetScript and el:GetScript("OnEnter")
                if enter then
                    tested = tested + 1
                    pcall(enter, el)
                    local tip = Shown(GameTooltip) and U.Rect(GameTooltip)
                    if tip then
                        for _, other in ipairs(all) do
                            if other ~= el and IsControl(other) and U.Overlap(tip, U.Rect(other)) > 0 then
                                problems[#problems + 1] = Name(el) .. " verdeckt " .. Name(other)
                                break
                            end
                        end
                    end
                    local leave = el:GetScript("OnLeave")
                    if leave then pcall(leave, el) end
                    if GameTooltip.Hide then GameTooltip:Hide() end
                end
            end
        end
    end
    return problems, tested
end

-- T19: eigene sichtbare Fenster überdecken weder Blizzard-Fenster noch Fenster anderer GoldSentinel-Addons
function U.WindowsOverlapNothing()
    local problems, tested = {}, 0
    for _, e in ipairs(ns.uiFrames) do
        local mine = not e.hud and Shown(e.frame) and U.Rect(e.frame)   -- Kampfanzeigen werden frei platziert
        if mine then
            for _, bn in ipairs(ns.UI_BLIZZARD) do
                local bf = _G[bn]
                if Shown(bf) then
                    tested = tested + 1
                    if U.Overlap(mine, U.Rect(bf)) > 0 then problems[#problems + 1] = e.name .. " überdeckt " .. bn end
                end
            end
            for _, o in ipairs(GoldSentinelUIFrames) do
                if o.addon ~= ADDON and Shown(o.frame) then
                    tested = tested + 1
                    if U.Overlap(mine, U.Rect(o.frame)) > 0 then
                        problems[#problems + 1] = e.name .. " überdeckt " .. o.name .. " (" .. o.addon .. ")"
                    end
                end
            end
        end
    end
    return problems, tested
end

-- T20: sichtbare Fenster liegen ganz im Bildschirm
function U.InsideScreen()
    local problems, tested, screen = {}, 0, U.Rect(UIParent)
    for _, e in ipairs(ns.uiFrames) do
        local r = Shown(e.frame) and U.Rect(e.frame)
        if r and screen then
            tested = tested + 1
            if r.l < screen.l - 1 or r.b < screen.b - 1 or r.r > screen.r + 1 or r.t > screen.t + 1 then
                problems[#problems + 1] = e.name .. " ragt aus dem Bildschirm"
            end
        end
    end
    return problems, tested
end

-- T21: Beschriftungen von Knöpfen sind nicht abgeschnitten (andere Texte nur als Hinweis)
function U.TextFits()
    local problems, hints, tested = {}, {}, 0
    for _, e in ipairs(ns.uiFrames) do
        if Shown(e.frame) then
            for _, el in ipairs(U.Descendants(e.frame)) do
                local fs = el.GetFontString and el:GetFontString()
                if fs and fs.IsTruncated then
                    tested = tested + 1
                    if fs:IsTruncated() then problems[#problems + 1] = Name(el) .. " Beschriftung abgeschnitten" end
                end
                for _, region in ipairs(el.GetRegions and { el:GetRegions() } or {}) do
                    if region.IsObjectType and region:IsObjectType("FontString") and region.IsTruncated and Shown(region) then
                        tested = tested + 1
                        if region:IsTruncated() then hints[#hints + 1] = Name(el) .. ": Text gekürzt" end
                    end
                end
            end
        end
    end
    return problems, tested, hints
end

-- T22: angezeigte Spielwerte plausibel (Prüfungen meldet das Addon mit ns.Plausible an)
function U.ValuesPlausible()
    local problems = {}
    for _, p in ipairs(ns.plausible) do
        local ok, good, got, want = pcall(p.fn)
        if not ok then problems[#problems + 1] = p.name .. ": Lua-Fehler " .. tostring(good)
        elseif good == false then problems[#problems + 1] = p.name .. ": " .. tostring(got) .. " (erwartet " .. tostring(want) .. ")" end
    end
    return problems, #ns.plausible
end

-- T23: keine Fehlerschleife – dieselbe Meldung höchstens UI_LOOP_LIMIT× (Diagnose-Protokoll der echten Daten)
function U.NoErrorLoops()
    local problems = {}
    local db = ns.realDB or ns.db
    local entries = db and db.diag and db.diag.entries or {}
    for _, en in ipairs(entries) do
        if en.k == "FEHLER" and (en.n or 1) > ns.UI_LOOP_LIMIT then
            problems[#problems + 1] = (en.n or 1) .. "× " .. tostring(en.t)
        end
    end
    return problems, #entries
end

-- Beispiel für T22 (ein Wert, den jedes Addon hat): Stufe des Charakters
ns.Plausible("Stufe des Charakters", function()
    local lvl = UnitLevel and UnitLevel("player")
    if type(lvl) ~= "number" or (ns.G and ns.G.IsSecret and ns.G.IsSecret(lvl)) then return true, "nicht lesbar" end
    return lvl >= 1 and lvl <= 100, lvl, "1–100"
end)
