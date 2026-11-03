-- __ADDON__ – Optionen (Einstellungsfenster des Spiels)
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Moderner Client (Forever, Retail, neuere Classic-Clients): Settings-API. Ältere Clients: InterfaceOptions.
-- Eigene Seite als einfaches Fenster ("Canvas"), damit derselbe Code überall läuft.

local ADDON, ns = ...
local L = ns.L

local panel
ns.options = {}             -- Bedienelemente, damit die Testroutine sie findet

local function Checkbox(parent, label, key, y)
    local cb = CreateFrame("CheckButton", nil, parent, "InterfaceOptionsCheckButtonTemplate")
    cb:SetPoint("TOPLEFT", 16, y)
    local text = cb.Text or cb.text
    if text then text:SetText(label) end
    cb:SetScript("OnShow", function(self) self:SetChecked(ns.db and ns.db[key] and true or false) end)
    cb:SetScript("OnClick", function(self)
        if ns.db then ns.db[key] = self:GetChecked() and true or false end
        if ns.OnOptionChanged then ns.OnOptionChanged(key) end
    end)
    ns.options[key] = cb
    return cb
end

local function Build()
    panel = CreateFrame("Frame")
    panel.name = L.TITLE

    local title = panel:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
    title:SetPoint("TOPLEFT", 16, -16)
    title:SetText(L.TITLE .. " " .. tostring(ns.VERSION))

    local hint = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    hint:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -6)
    hint:SetText(L.OPT_HINT)

    Checkbox(panel, L.OPT_ENABLED, "enabled", -70)
    Checkbox(panel, L.OPT_CHAT, "chat", -100)

    if Settings and Settings.RegisterCanvasLayoutCategory and Settings.RegisterAddOnCategory then
        local category = Settings.RegisterCanvasLayoutCategory(panel, L.TITLE)
        Settings.RegisterAddOnCategory(category)
        ns.settingsCategory = category
    elseif InterfaceOptions_AddCategory then
        InterfaceOptions_AddCategory(panel)
    end
    return panel
end

function ns.OpenOptions()
    if not panel then return end
    ns.WhenOutOfCombat(function()
        if ns.settingsCategory and Settings and Settings.OpenToCategory then
            local id = ns.settingsCategory.GetID and ns.settingsCategory:GetID() or ns.settingsCategory.ID
            Settings.OpenToCategory(id)
        elseif InterfaceOptionsFrame_OpenToCategory then
            InterfaceOptionsFrame_OpenToCategory(panel)
            InterfaceOptionsFrame_OpenToCategory(panel)   -- zweimal: bekannter Fehler der alten Clients
        end
    end)
end

-- beim Laden der Einstellungen aufbauen (Core.lua ruft ns.OnInit)
local prevInit = ns.OnInit
function ns.OnInit()
    if prevInit then prevInit() end
    ns.Try("Optionen", Build)
end
