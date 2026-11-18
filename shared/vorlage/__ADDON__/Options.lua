-- __ADDON__ – Optionen (eigenes Fenster nach Vorbild AHSentinel OPT-1, Entscheid des Nutzers 18.11.2026 10:27)
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Ziel: jede Einstellung in unter 5 Sekunden finden.
--   * Links eine Leiste mit Bereichen (Themen), rechts NUR die Optionen dieses Bereichs: eine Spalte, höchstens
--     ns.OPT_MAX_ROWS Zeilen, kein Scrollen.
--   * Oben ein Suchfeld: Tippen filtert über alle Bereiche (mit Bereichsname davor).
--   * Jede Zeile: kurze Beschriftung (höchstens ns.OPT_MAX_LABEL Zeichen, kein Umbruch), Erklärung nur im Tooltip.
--   * Selten gebrauchte Optionen (advanced = true) stehen eingeklappt unter "Weitere".
--   * Je Bereich ein Knopf "Standard" (setzt nur die Optionen dieses Bereichs auf ns.DEFAULTS zurück).
--   * Jede Option genau EINMAL (die Testroutine prüft das). Gespeicherte Werte (Schlüssel in ns.db) ändern sich nie,
--     wenn die Anzeige umgebaut wird – nur die Liste unten.
--   * Bereiche werden erst beim ersten Zeigen gebaut (Leistung: kein Bild über 16 ms beim Öffnen).
-- Im Einstellungsfenster des Spiels (Settings-API bzw. InterfaceOptions in alten Clients) steht nur eine kleine Seite mit
-- einem Knopf, der dieses Fenster öffnet – so findet man das Addon auch dort.
--
-- NEUE OPTION: Standardwert in ns.DEFAULTS (Core.lua), Zeile in ns.OPTIONS (unten), Texte OPT_<NAME> und OPT_<NAME>_TIP in
-- Locales.lua (Englisch + Deutsch). Arten: "toggle" (an/aus), "choice" (values = { {wert, L-Schlüssel}, … }),
-- "number" (min, max, step). Wirkung: ns.OnOptionChanged(key) (andere Dateien hängen sich dort an).

local ADDON, ns = ...
local L = ns.L

ns.OPT_MAX_ROWS = 12        -- Zeilen je Bereich (inkl. "Weitere"), sonst neuen Bereich anlegen
ns.OPT_MAX_LABEL = 28       -- Zeichen je Beschriftung (alle Sprachen)

-- Bereiche in der Reihenfolge der Leiste. Häufig gebraucht zuerst.
ns.OPTION_SECTIONS = {
    { id = "general", label = "SEC_GENERAL" },
    { id = "data",    label = "SEC_DATA" },
}

-- Jede Option genau einmal. key = Feld in ns.db (und ns.DEFAULTS).
ns.OPTIONS = {
    { key = "enabled",       section = "general", kind = "toggle", label = "OPT_ENABLED" },
    { key = "chat",          section = "general", kind = "toggle", label = "OPT_CHAT" },
    { key = "minimapButton", section = "general", kind = "toggle", label = "OPT_MINIMAP" },
    { key = "cmdHint",       section = "general", kind = "toggle", label = "OPT_CMDHINT" },
    { key = "marketShare",   section = "data",    kind = "toggle", label = "OPT_MARKET" },
    { key = "diagSend",      section = "data",    kind = "toggle", label = "OPT_DIAG", advanced = true },
}

ns.options = {}             -- key -> Bedienelement der gerade SICHTBAREN Zeilen (für die Testroutine)

local ROW_H, LIST_W, WIN_W, WIN_H = 24, 150, 560, 420
local win, settingsPanel
local rows = {}             -- wiederverwendete Zeilen (höchstens OPT_MAX_ROWS + 1)
local sectionButtons = {}
local current = "general"
local showAdvanced = false

local function Label(o) return L[o.label] end
local function Tip(o) return L[o.label .. "_TIP"] end

function ns.OptionByKey(key)
    for _, o in ipairs(ns.OPTIONS) do if o.key == key then return o end end
    return nil
end

local function SectionLabel(id)
    for _, s in ipairs(ns.OPTION_SECTIONS) do if s.id == id then return L[s.label] end end
    return tostring(id)
end

-- Wert setzen (einzige Stelle, die ns.db für Optionen schreibt)
function ns.SetOption(key, value)
    if not ns.db then return end
    ns.db[key] = value
    if ns.OnOptionChanged then ns.OnOptionChanged(key) end
end

-- Optionen eines Bereichs auf den Standard zurücksetzen
function ns.ResetSection(section)
    for _, o in ipairs(ns.OPTIONS) do
        if o.section == section and ns.DEFAULTS[o.key] ~= nil then ns.SetOption(o.key, ns.DEFAULTS[o.key]) end
    end
    if win and win:IsShown() then ns.RefreshOptions() end
end

-- Suche: Beschriftung, Tooltip oder Bereichsname enthält den Text (ohne Gross/Klein, ohne Muster)
function ns.FindOptions(text)
    local q = tostring(text or ""):lower()
    local out = {}
    if q == "" then return out end
    for _, o in ipairs(ns.OPTIONS) do
        local hay = (Label(o) .. " " .. (Tip(o) or "") .. " " .. SectionLabel(o.section) .. " " .. o.key):lower()
        if hay:find(q, 1, true) then out[#out + 1] = o end
    end
    return out
end

-- Zeilen, die gerade zu zeigen sind: Suche oder Bereich (mit eingeklappten "Weitere")
function ns.VisibleOptions(section, search, advancedOpen)
    if search and search ~= "" then return ns.FindOptions(search), false end
    local basic, adv = {}, {}
    for _, o in ipairs(ns.OPTIONS) do
        if o.section == section then
            if o.advanced then adv[#adv + 1] = o else basic[#basic + 1] = o end
        end
    end
    local list = {}
    for _, o in ipairs(basic) do list[#list + 1] = o end
    if #adv > 0 then
        list[#list + 1] = { more = true, n = #adv }
        if advancedOpen then for _, o in ipairs(adv) do list[#list + 1] = o end end
    end
    return list, #adv > 0
end

---------------------------------------------------------------------------------------------------------------------
-- Zeilen
---------------------------------------------------------------------------------------------------------------------
local function ShowTip(self)
    if not (GameTooltip and self.tip) then return end
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:SetText(self.title or "", 1, 1, 1)
    GameTooltip:AddLine(self.tip, nil, nil, nil, true)
    GameTooltip:Show()
end
local function HideTip() if GameTooltip then GameTooltip:Hide() end end

local function Row(i)
    if rows[i] then return rows[i] end
    local r = CreateFrame("Frame", nil, win.right)
    r:SetSize(WIN_W - LIST_W - 48, ROW_H)
    r:SetPoint("TOPLEFT", 0, -(i - 1) * ROW_H)
    r:EnableMouse(true)
    r:SetScript("OnEnter", ShowTip)
    r:SetScript("OnLeave", HideTip)
    r.text = r:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    r.text:SetPoint("LEFT", 4, 0)
    r.text:SetJustifyH("LEFT")
    if r.text.SetWordWrap then r.text:SetWordWrap(false) end
    r.check = CreateFrame("CheckButton", nil, r, "UICheckButtonTemplate")
    r.check:SetSize(24, 24)
    r.check:SetPoint("RIGHT", -4, 0)
    r.check:SetScript("OnClick", function(self)
        if self.key then ns.SetOption(self.key, self:GetChecked() and true or false) end
    end)
    r.check:SetScript("OnEnter", function(self) ShowTip(r) end)
    r.check:SetScript("OnLeave", HideTip)
    r.button = CreateFrame("Button", nil, r, "UIPanelButtonTemplate")
    r.button:SetSize(110, 20)
    r.button:SetPoint("RIGHT", -4, 0)
    rows[i] = r
    return r
end

local function ChoiceText(o)
    local v = ns.db and ns.db[o.key]
    for _, c in ipairs(o.values or {}) do if c[1] == v then return L[c[2]] end end
    return tostring(v)
end

local function FillRow(r, o, withSection)
    r.check:Hide(); r.button:Hide()
    r.check.key = nil
    r.title, r.tip = nil, nil
    if o.more then
        r.text:SetText(L.OPT_MORE .. " (" .. o.n .. ")")
        r.button:SetText(showAdvanced and "-" or "+")
        r.button:SetScript("OnClick", function() showAdvanced = not showAdvanced; ns.RefreshOptions() end)
        r.button:Show()
        r:Show()
        return
    end
    local label = Label(o)
    r.title, r.tip = label, Tip(o)
    r.text:SetText(withSection and (SectionLabel(o.section) .. ": " .. label) or label)
    if o.kind == "toggle" then
        r.check.key = o.key
        r.check:SetChecked(ns.db and ns.db[o.key] and true or false)
        r.check:Show()
        ns.options[o.key] = r.check
    elseif o.kind == "choice" then
        r.button:SetText(ChoiceText(o))
        r.button:SetScript("OnClick", function()
            local vals, cur = o.values or {}, ns.db and ns.db[o.key]
            local idx = 1
            for i, c in ipairs(vals) do if c[1] == cur then idx = i % #vals + 1 end end
            if vals[idx] then ns.SetOption(o.key, vals[idx][1]) end
            ns.RefreshOptions()
        end)
        r.button:Show()
        ns.options[o.key] = r.button
    elseif o.kind == "number" then
        r.button:SetText(tostring(ns.db and ns.db[o.key]))
        r.button:SetScript("OnClick", function(_, mouse)
            local v = tonumber(ns.db and ns.db[o.key]) or o.min or 0
            local step = (mouse == "RightButton") and -(o.step or 1) or (o.step or 1)
            v = math.max(o.min or v, math.min(o.max or v, v + step))
            ns.SetOption(o.key, v)
            ns.RefreshOptions()
        end)
        r.button:Show()
        ns.options[o.key] = r.button
    end
    r:Show()
end

function ns.RefreshOptions()
    if not win then return end
    local search = win.search and win.search:GetText() or ""
    local list = ns.VisibleOptions(current, search, showAdvanced)
    for k in pairs(ns.options) do ns.options[k] = nil end      -- nur die gerade sichtbaren Bedienelemente
    local n = math.min(#list, ns.OPT_MAX_ROWS)
    for i = 1, n do FillRow(Row(i), list[i], search ~= "") end
    for i = n + 1, #rows do rows[i]:Hide() end
    win.empty:SetText((#list == 0) and L.OPT_NO_HITS or "")
    win.header:SetText(search ~= "" and L.OPT_SEARCH or SectionLabel(current))
    for _, b in ipairs(sectionButtons) do
        if b.LockHighlight then if b.id == current and search == "" then b:LockHighlight() else b:UnlockHighlight() end end
    end
    win.defaults:SetShown(search == "")
end

function ns.ShowOptionSection(id)
    current = id or current
    showAdvanced = false
    if win and win.search then win.search:SetText("") end
    ns.RefreshOptions()
end

---------------------------------------------------------------------------------------------------------------------
-- Fenster
---------------------------------------------------------------------------------------------------------------------
local function BuildWindow()
    win = CreateFrame("Frame", ADDON .. "OptionsFrame", UIParent, "BackdropTemplate")
    win:SetSize(WIN_W, WIN_H)
    win:SetPoint("CENTER")
    win:SetFrameStrata("DIALOG")
    win:SetClampedToScreen(true)
    win:SetMovable(true)
    win:EnableMouse(true)
    win:RegisterForDrag("LeftButton")
    win:SetScript("OnDragStart", win.StartMoving)
    win:SetScript("OnDragStop", win.StopMovingOrSizing)
    if win.SetBackdrop then
        win:SetBackdrop({ bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background",
                          edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border",
                          tile = true, tileSize = 32, edgeSize = 32,
                          insets = { left = 8, right = 8, top = 8, bottom = 8 } })
    end
    local title = win:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
    title:SetPoint("TOPLEFT", 18, -16)
    title:SetText(L.TITLE .. " – " .. L.OPT_TITLE)
    local close = CreateFrame("Button", nil, win, "UIPanelCloseButton")
    close:SetPoint("TOPRIGHT", -6, -6)

    -- Suchfeld oben
    local search = CreateFrame("EditBox", ADDON .. "OptionsSearch", win, "InputBoxTemplate")
    search:SetSize(200, 20)
    search:SetPoint("TOPRIGHT", -40, -16)
    search:SetAutoFocus(false)
    search:SetScript("OnTextChanged", function() ns.RefreshOptions() end)
    search:SetScript("OnEscapePressed", function(self) self:SetText(""); self:ClearFocus() end)
    win.search = search
    local hint = win:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
    hint:SetPoint("RIGHT", search, "LEFT", -8, 0)
    hint:SetText(L.OPT_SEARCH)

    -- Leiste mit Bereichen links
    for i, s in ipairs(ns.OPTION_SECTIONS) do
        local b = CreateFrame("Button", nil, win, "UIPanelButtonTemplate")
        b:SetSize(LIST_W - 10, 22)
        b:SetPoint("TOPLEFT", 16, -48 - (i - 1) * 26)
        b:SetText(L[s.label])
        b.id = s.id
        b:SetScript("OnClick", function() ns.ShowOptionSection(s.id) end)
        sectionButtons[#sectionButtons + 1] = b
    end

    -- rechts: Überschrift und eine Spalte Zeilen
    win.header = win:CreateFontString(nil, "ARTWORK", "GameFontNormal")
    win.header:SetPoint("TOPLEFT", LIST_W + 20, -50)
    win.right = CreateFrame("Frame", nil, win)
    win.right:SetPoint("TOPLEFT", LIST_W + 16, -70)
    win.right:SetSize(WIN_W - LIST_W - 40, ns.OPT_MAX_ROWS * ROW_H)
    win.empty = win:CreateFontString(nil, "ARTWORK", "GameFontDisable")
    win.empty:SetPoint("TOPLEFT", LIST_W + 20, -74)

    win.defaults = CreateFrame("Button", nil, win, "UIPanelButtonTemplate")
    win.defaults:SetSize(110, 22)
    win.defaults:SetPoint("BOTTOMRIGHT", -16, 14)
    win.defaults:SetText(L.OPT_DEFAULTS)
    win.defaults:SetScript("OnClick", function() ns.ResetSection(current) end)

    win:SetScript("OnShow", function() ns.RefreshOptions() end)
    win:Hide()
    if UISpecialFrames then table.insert(UISpecialFrames, win:GetName()) end   -- Esc schliesst
    ns.optionsWindow = win
    if ns.RegisterUI then ns.RegisterUI(win, ADDON .. " – Optionen") end
end

-- kleine Seite im Einstellungsfenster des Spiels: Titel, Hinweis, Knopf zum eigenen Fenster
local function BuildSettingsPage()
    settingsPanel = CreateFrame("Frame")
    settingsPanel.name = L.TITLE
    local title = settingsPanel:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
    title:SetPoint("TOPLEFT", 16, -16)
    title:SetText(L.TITLE .. " " .. tostring(ns.VERSION))
    local btn = CreateFrame("Button", nil, settingsPanel, "UIPanelButtonTemplate")
    btn:SetSize(180, 24)
    btn:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -12)
    btn:SetText(L.OPT_OPEN)
    btn:SetScript("OnClick", function()
        if HideUIPanel and SettingsPanel and SettingsPanel.IsShown and SettingsPanel:IsShown() then HideUIPanel(SettingsPanel) end
        ns.OpenOptions()
    end)
    if Settings and Settings.RegisterCanvasLayoutCategory and Settings.RegisterAddOnCategory then
        local category = Settings.RegisterCanvasLayoutCategory(settingsPanel, L.TITLE)
        Settings.RegisterAddOnCategory(category)
        ns.settingsCategory = category
    elseif InterfaceOptions_AddCategory then
        InterfaceOptions_AddCategory(settingsPanel)
    end
end

-- ns.OpenOptions([Bereich]) – öffnet das eigene Fenster (auch im Kampf: kein geschütztes Fenster)
function ns.OpenOptions(section)
    if not win then return end
    if section then current = section end
    win:Show()
    ns.ShowOptionSection(current)
end

function ns.CloseOptions() if win then win:Hide() end end

-- Für die Testroutine: Bereich mit aufgeklapptem "Weitere" zeigen; ns.options enthält danach dessen Bedienelemente
function ns.ShowOptionSectionAll(id)
    current = id or current
    showAdvanced = true
    if win and win.search then win.search:SetText("") end
    ns.RefreshOptions()
end

-- beim Laden der Einstellungen aufbauen (Core.lua ruft ns.OnInit)
local prevInit = ns.OnInit
function ns.OnInit()
    if prevInit then prevInit() end
    ns.Try("Optionen", BuildWindow)
    ns.Try("Optionen (Spiel)", BuildSettingsPage)
end
