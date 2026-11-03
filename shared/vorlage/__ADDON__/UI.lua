-- __ADDON__ – Hauptfenster und Kopierfenster
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Das Hauptfenster ist absichtlich schlicht: Titel, Statuszeile, Inhaltsbereich (ns.content) für das eigentliche Addon.
-- Position und Sichtbarkeit werden in __ADDON__DB.window gespeichert. Esc schliesst das Fenster.

local ADDON, ns = ...
local L = ns.L
local G = ns.G

local win

local function SavePosition(f)
    if not ns.db then return end
    local point, _, _, x, y = f:GetPoint(1)
    ns.db.window.point, ns.db.window.x, ns.db.window.y = point or "CENTER", x or 0, y or 0
end

local function Build()
    win = CreateFrame("Frame", ADDON .. "MainFrame", UIParent, "BackdropTemplate")
    win:SetSize(420, 300)
    win:SetFrameStrata("MEDIUM")
    win:SetClampedToScreen(true)
    win:SetMovable(true)
    win:EnableMouse(true)
    win:RegisterForDrag("LeftButton")
    win:SetScript("OnDragStart", win.StartMoving)
    win:SetScript("OnDragStop", function(f) f:StopMovingOrSizing(); SavePosition(f) end)
    if win.SetBackdrop then
        win:SetBackdrop({ bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background",
                          edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border",
                          tile = true, tileSize = 32, edgeSize = 32,
                          insets = { left = 8, right = 8, top = 8, bottom = 8 } })
    end

    local title = win:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
    title:SetPoint("TOP", 0, -16)
    title:SetText(L.TITLE)

    local close = CreateFrame("Button", nil, win, "UIPanelCloseButton")
    close:SetPoint("TOPRIGHT", -6, -6)

    win.status = win:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    win.status:SetPoint("BOTTOMLEFT", 16, 14)
    win.status:SetPoint("BOTTOMRIGHT", -16, 14)
    win.status:SetJustifyH("LEFT")

    ns.content = CreateFrame("Frame", nil, win)
    ns.content:SetPoint("TOPLEFT", 16, -44)
    ns.content:SetPoint("BOTTOMRIGHT", -16, 34)

    win:SetScript("OnShow", function(f)
        f.status:SetText(G.FlavorName() .. " · " .. tostring(ns.VERSION))
        if ns.db then ns.db.window.shown = true end
        if ns.OnWindowShow then ns.OnWindowShow(f) end
    end)
    win:SetScript("OnHide", function() if ns.db then ns.db.window.shown = false end end)

    local p = ns.db and ns.db.window or ns.DEFAULTS.window
    win:ClearAllPoints()
    win:SetPoint(p.point or "CENTER", UIParent, p.point or "CENTER", p.x or 0, p.y or 0)
    win:Hide()
    if UISpecialFrames then table.insert(UISpecialFrames, win:GetName()) end   -- Esc schliesst
    ns.window = win
end

function ns.ToggleWindow()
    if not win then return end
    if win:IsShown() then win:Hide() else win:Show() end
end

-- Kopierfenster: Text zum Markieren und Kopieren (z. B. Testbericht, Diagnose)
local copy
function ns.ShowCopy(text)
    if not copy then
        copy = CreateFrame("Frame", ADDON .. "CopyFrame", UIParent, "BackdropTemplate")
        copy:SetSize(560, 360)
        copy:SetPoint("CENTER")
        copy:SetFrameStrata("DIALOG")
        if copy.SetBackdrop then
            copy:SetBackdrop({ bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background",
                               edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border",
                               tile = true, tileSize = 32, edgeSize = 32,
                               insets = { left = 8, right = 8, top = 8, bottom = 8 } })
        end
        local scroll = CreateFrame("ScrollFrame", nil, copy, "UIPanelScrollFrameTemplate")
        scroll:SetPoint("TOPLEFT", 16, -16)
        scroll:SetPoint("BOTTOMRIGHT", -34, 40)
        local edit = CreateFrame("EditBox", nil, scroll)
        edit:SetMultiLine(true)
        edit:SetFontObject(ChatFontNormal)
        edit:SetWidth(500)
        edit:SetAutoFocus(true)
        edit:SetScript("OnEscapePressed", function() copy:Hide() end)
        scroll:SetScrollChild(edit)
        copy.edit = edit
        local hint = copy:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
        hint:SetPoint("BOTTOMLEFT", 16, 16)
        hint:SetText(L.COPY_HINT)
        local btn = CreateFrame("Button", nil, copy, "UIPanelButtonTemplate")
        btn:SetSize(100, 22)
        btn:SetPoint("BOTTOMRIGHT", -16, 12)
        btn:SetText(L.CLOSE)
        btn:SetScript("OnClick", function() copy:Hide() end)
        if UISpecialFrames then table.insert(UISpecialFrames, copy:GetName()) end
    end
    copy.edit:SetText(text or "")
    copy.edit:HighlightText()
    copy:Show()
end

local prevInit = ns.OnInit
function ns.OnInit()
    if prevInit then prevInit() end
    ns.Try("Fenster", Build)
end
