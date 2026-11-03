-- __ADDON__ – Button an der Minimap
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Wie bei allen GoldSentinel-Addons: Linksklick = Fenster, Rechtsklick = Optionen, Ziehen = um die Minimap schieben.
-- Winkel und Sichtbarkeit stehen in __ADDON__DB (minimapButton, minimapAngle). Keine Bibliothek nötig, läuft in allen
-- Clients. Der Button ist kein geschützter Frame: Ein- und Ausblenden geht auch im Kampf.

local ADDON, ns = ...
local L = ns.L

local btn

function ns.UpdateMinimapButton()
    if not btn then return end
    if not (ns.db and ns.db.minimapButton) then btn:Hide() return end
    local map = _G.Minimap
    if not map then btn:Hide() return end
    local angle = math.rad(tonumber(ns.db.minimapAngle) or ns.DEFAULTS.minimapAngle)
    local radius = (tonumber(map.GetWidth and map:GetWidth()) or 140) / 2 + 6
    btn:ClearAllPoints()
    btn:SetPoint("CENTER", map, "CENTER", math.cos(angle) * radius, math.sin(angle) * radius)
    btn:Show()
end

function ns.ToggleMinimapButton()
    if not ns.db then return end
    ns.db.minimapButton = not ns.db.minimapButton
    ns.UpdateMinimapButton()
    if ns.options and ns.options.minimapButton then ns.options.minimapButton:SetChecked(ns.db.minimapButton) end
end

-- Winkel aus der Mausposition (auch von der Testroutine benutzt)
function ns.MinimapAngleFromCursor(cx, cy)
    local map = _G.Minimap
    local mx, my = map:GetCenter()
    mx, my = tonumber(mx) or 0, tonumber(my) or 0
    local scale = tonumber(map:GetEffectiveScale()) or 1
    return math.deg(math.atan2(cy / scale - my, cx / scale - mx))
end

local function Build()
    local map = _G.Minimap
    if not map then return end
    btn = CreateFrame("Button", ADDON .. "MinimapButton", map)
    btn:SetSize(31, 31)
    btn:SetFrameStrata("MEDIUM")
    btn:SetFrameLevel(8)
    btn:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    btn:RegisterForDrag("LeftButton")
    btn:SetHighlightTexture("Interface\\Minimap\\UI-Minimap-ZoomButton-Highlight")

    local icon = btn:CreateTexture(nil, "BACKGROUND")
    icon:SetTexture("__ICON__")
    icon:SetSize(20, 20)
    icon:SetPoint("TOPLEFT", 7, -6)
    icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
    local border = btn:CreateTexture(nil, "OVERLAY")
    border:SetTexture("Interface\\Minimap\\MiniMap-TrackingBorder")
    border:SetSize(53, 53)
    border:SetPoint("TOPLEFT")

    btn:SetScript("OnClick", function(_, button)
        if button == "RightButton" then
            if ns.OpenOptions then ns.OpenOptions() end
        elseif ns.ToggleWindow then
            ns.ToggleWindow()
        end
    end)
    btn:SetScript("OnDragStart", function(self)
        self:SetScript("OnUpdate", function()
            local cx, cy = GetCursorPosition()
            ns.db.minimapAngle = ns.MinimapAngleFromCursor(cx, cy)
            ns.UpdateMinimapButton()
        end)
    end)
    btn:SetScript("OnDragStop", function(self) self:SetScript("OnUpdate", nil) end)
    btn:SetScript("OnEnter", function(self)
        if not GameTooltip then return end
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        GameTooltip:SetText(L.TITLE)
        GameTooltip:AddLine(L.MINIMAP_LEFT, 1, 1, 1)
        GameTooltip:AddLine(L.MINIMAP_RIGHT, 1, 1, 1)
        GameTooltip:AddLine(L.MINIMAP_DRAG, 0.7, 0.7, 0.7)
        GameTooltip:Show()
    end)
    btn:SetScript("OnLeave", function() if GameTooltip then GameTooltip:Hide() end end)

    ns.minimapButton = btn
    ns.UpdateMinimapButton()
end

-- Option in den Einstellungen umgeschaltet -> Button sofort nachführen
local prevChanged = ns.OnOptionChanged
function ns.OnOptionChanged(key)
    if prevChanged then prevChanged(key) end
    if key == "minimapButton" then ns.UpdateMinimapButton() end
end

local prevInit = ns.OnInit
function ns.OnInit()
    if prevInit then prevInit() end
    ns.Try("Minimap-Button", Build)
end
