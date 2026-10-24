-- RaidMaster - Schlachtzugsymbole
-- Markierungsleiste, Mouseover-Tasten, nächstes freies Symbol nach Vorlage, alle entfernen

local ADDON, RM = ...
local L = RM.L
local M = {}
RM.Markers = M

local used = {}   -- in diesem Kampf vergebene Symbole
local bar

local function C() return RM.db.config end

local function TargetUnit()
	if UnitExists("mouseover") then return "mouseover" end
	if UnitExists("target") then return "target" end
end

local function CanMark()
	if RM.InRaid() then return RM.IsAssist() end
	return true
end

-- Symbol auf Maus-Ziel (sonst aktuelles Ziel) setzen; 0 entfernt
function M.Mark(icon)
	local unit = TargetUnit()
	if not unit then return end
	if not CanMark() then RM.Print(L["Im Schlachtzug brauchst du Leiter- oder Assistentenrechte zum Markieren."]) return end
	SetRaidTarget(unit, icon)
	if icon and icon > 0 then used[icon] = true end
end

-- Aktuell sichtbar vergebene Symbole (Ziele der Raidmitglieder)
local function IconsInUse()
	local inUse = {}
	for k in pairs(used) do inUse[k] = true end
	local function check(unit)
		if UnitExists(unit) then
			local i = GetRaidTargetIndex(unit)
			if i then inUse[i] = true end
		end
	end
	check("target")
	if RM.InRaid() then
		for i = 1, GetNumGroupMembers() do check("raid" .. i .. "target") end
	else
		for i = 1, 4 do check("party" .. i .. "target") end
	end
	return inUse
end

-- Nächstes freies Symbol aus der gewählten Vorlage
function M.SmartMark()
	local unit = TargetUnit()
	if not unit then return end
	if not CanMark() then RM.Print(L["Im Schlachtzug brauchst du Leiter- oder Assistentenrechte zum Markieren."]) return end
	if GetRaidTargetIndex(unit) then return end
	if UnitIsPlayer(unit) or UnitIsDead(unit) then return end
	local template = RM.Data.GetTemplate(C().markerTemplate)
	local inUse = IconsInUse()
	for _, icon in ipairs(template.order) do
		if not inUse[icon] then
			SetRaidTarget(unit, icon)
			used[icon] = true
			return
		end
	end
	RM.Print(L["Alle Symbole der Vorlage '"] .. template.name .. L["' sind vergeben."])
end

-- Alle Symbole entfernen: jedes Symbol kurz auf sich selbst setzen, dann löschen
function M.ClearAll()
	if not CanMark() then RM.Print(L["Im Schlachtzug brauchst du Leiter- oder Assistentenrechte zum Markieren."]) return end
	local step = 0
	for i = 8, 1, -1 do
		step = step + 1
		C_Timer.After(step * 0.12, function() SetRaidTarget("player", i) end)
	end
	C_Timer.After((step + 1) * 0.12 + 0.1, function() SetRaidTarget("player", 0) end)
	wipe(used)
end

function M.ResetUsed()
	wipe(used)
end

RM.On("PLAYER_REGEN_ENABLED", function() wipe(used) end)

---------------------------------------------------------------------------
-- Markierungsleiste
---------------------------------------------------------------------------
local function IconTexture(i)
	return "Interface\\TargetingFrame\\UI-RaidTargetingIcon_" .. i
end

local function CreateBar()
	local UI = RM.UI
	local f = UI.Frame(UIParent, 10, 34)
	UI.Skin(f)
	f:SetFrameStrata("MEDIUM")
	UI.MakeMovable(f, "markerBar", "CENTER", 0, -220)
	f:SetClampedToScreen(true)

	local x = 5
	local order = { 8, 7, 6, 5, 4, 3, 2, 1 }
	for _, i in ipairs(order) do
		local b = CreateFrame("Button", nil, f)
		b:SetSize(26, 26)
		b:SetPoint("LEFT", x, 0)
		local t = b:CreateTexture(nil, "ARTWORK")
		t:SetAllPoints()
		t:SetTexture(IconTexture(i))
		local h = b:CreateTexture(nil, "HIGHLIGHT")
		h:SetAllPoints()
		h:SetColorTexture(1, 1, 1, 0.25)
		b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
		b:SetScript("OnClick", function(_, button)
			if button == "RightButton" then M.Mark(0) else M.Mark(i) end
		end)
		b:SetScript("OnEnter", function(self)
			GameTooltip:SetOwner(self, "ANCHOR_TOP")
			GameTooltip:AddLine(RM.Data.MarkerNames[i])
			GameTooltip:AddLine(L["Linksklick: auf Maus-Ziel/Ziel setzen"], 0.8, 0.8, 0.8)
			GameTooltip:AddLine(L["Rechtsklick: Symbol entfernen"], 0.8, 0.8, 0.8)
			GameTooltip:Show()
		end)
		b:SetScript("OnLeave", function() GameTooltip:Hide() end)
		x = x + 28
	end

	local smart = UI.Button(f, L["Auto"], 42, 26, function() M.SmartMark() end,
		L["Setzt das nächste freie Symbol der gewählten Vorlage.\nAm schnellsten per Tastenbelegung mit Mouseover."])
	smart:SetPoint("LEFT", x + 2, 0)
	x = x + 46

	local clear = UI.Button(f, "X", 26, 26, function() M.ClearAll() end, L["Alle Symbole entfernen"])
	clear:SetPoint("LEFT", x, 0)
	x = x + 30

	f.templateText = UI.Text(f, "", 10, 0.8, 0.8, 0.8)
	f.templateText:SetPoint("TOPLEFT", f, "BOTTOMLEFT", 2, -2)

	f:SetWidth(x + 2)
	return f
end

function M.UpdateBar()
	if not RM.db then return end
	local show = C().markerBar
	if show then
		bar = bar or CreateBar()
		bar:Show()
		local t = RM.Data.GetTemplate(C().markerTemplate)
		bar.templateText:SetText(L["Vorlage: "] .. t.name)
	elseif bar then
		bar:Hide()
	end
end

function M.ToggleBar()
	C().markerBar = not C().markerBar
	M.UpdateBar()
	RM.Fire("CONFIG_CHANGED")
end

RM.Listen("LOGIN", function() M.UpdateBar() end)
RM.Listen("CONFIG_CHANGED", function() M.UpdateBar() end)

---------------------------------------------------------------------------
-- Boss-Infos im Raid posten
---------------------------------------------------------------------------
function M.PostBossInfo(encounterID)
	local info = RM.Data.BossInfo[encounterID]
	if not info then return end
	if not RM.InRaid() then
		for _, l in ipairs(info.post) do RM.Print(l) end
		return
	end
	for i, l in ipairs(info.post) do
		RM.Announce(l, i == 1)
	end
end
