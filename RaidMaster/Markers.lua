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

-- Symbole setzen dürfen nur Raidleiter und Co-Raidleiter (Assistenten),
-- in einer Gruppe der Gruppenleiter. Allein (ohne Gruppe) zum Ausprobieren erlaubt.
function M.IsMarkerLead()
	if RM.InRaid() then return RM.IsAssist() and true or false end
	if IsInGroup and IsInGroup() or (GetNumPartyMembers and GetNumPartyMembers() > 0) then
		return RM.IsLeader() and true or false
	end
	return false
end

local function CanMark()
	if RM.InRaid() or (IsInGroup and IsInGroup()) then return M.IsMarkerLead() end
	return true
end
M.CanMark = CanMark

local NO_RIGHTS = "Nur Raidleiter und Co-Raidleiter (Assistenten) können Schlachtzugsymbole setzen."

-- Symbol auf Maus-Ziel (sonst aktuelles Ziel) setzen; 0 entfernt
function M.Mark(icon)
	local unit = TargetUnit()
	if not unit then return end
	if not CanMark() then RM.Print(L[NO_RIGHTS]) return end
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
	if not CanMark() then RM.Print(L[NO_RIGHTS]) return end
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
	if not CanMark() then RM.Print(L[NO_RIGHTS]) return end
	local step = 0
	for i = 8, 1, -1 do
		step = step + 1
		C_Timer.After(step * 0.12, function() SetRaidTarget("player", i) end)
	end
	C_Timer.After((step + 1) * 0.12 + 0.1, function()
		SetRaidTarget("player", 0)
		RM.Print(L["Alle Schlachtzugsymbole ausgeblendet."])
	end)
	wipe(used)
end

---------------------------------------------------------------------------
-- Adds mit einem Klick markieren (über die Namensplaketten)
-- Sichtbare Gegner bekommen die Symbole der gewählten Vorlage in ihrer Reihenfolge.
-- Kennt die Vorlage die NPCs (z. B. Garrs Feuerschwörer), werden nur diese markiert,
-- sonst alle Gegner außer dem Boss selbst.
---------------------------------------------------------------------------
local function NpcID(guid)
	if type(guid) ~= "string" then return nil end
	local kind, _, _, _, _, id = strsplit("-", guid)
	if kind ~= "Creature" and kind ~= "Vehicle" then return nil end
	return tonumber(id)
end

-- Namen aller Bosse des aktuellen Raids (und des Raids der Vorlage) – die bleiben unmarkiert
local function BossNames(template)
	local names = {}
	local function add(def)
		for _, b in ipairs(def and def.bosses or {}) do
			if b.name then names[b.name] = true end
			for _, n in pairs(b.names or {}) do names[n] = true end
			if b.en then names[b.en] = true end
			if b.de then names[b.de] = true end
		end
	end
	add(RM.Data.Pools[RM.DKP.CurrentInstancePool(true) or ""])
	if template and template.raid then add(RM.Data.Pools[template.raid]) end
	for i = 1, 5 do
		local n = UnitExists("boss" .. i) and UnitName("boss" .. i)
		if n then names[n] = true end
	end
	return names
end

local function VisibleEnemies()
	local list, seen = {}, {}
	local function check(unit)
		if not UnitExists(unit) or UnitIsPlayer(unit) or UnitIsDead(unit) then return end
		if not UnitCanAttack("player", unit) then return end
		local ok, guid = pcall(UnitGUID, unit)
		if not ok or type(guid) ~= "string" or seen[guid] then return end
		local ctype = UnitCreatureType and UnitCreatureType(unit)
		if ctype == "Critter" or ctype == "Kleintier" then return end
		seen[guid] = true
		list[#list + 1] = { unit = unit, guid = guid, npc = NpcID(guid), name = UnitName(unit), icon = GetRaidTargetIndex(unit) }
	end
	for i = 1, 40 do check("nameplate" .. i) end
	for _, u in ipairs({ "target", "mouseover", "focus" }) do check(u) end
	table.sort(list, function(a, b) return a.guid < b.guid end)
	return list
end

function M.MarkAdds()
	if not CanMark() then RM.Print(L[NO_RIGHTS]) return end
	local template = RM.Data.GetTemplate(C().markerTemplate)
	local enemies = VisibleEnemies()
	if #enemies == 0 then
		RM.Print(L["Keine Gegner sichtbar. Namensplaketten der Gegner einschalten (Taste V) und näher an die Adds gehen."])
		return
	end
	local bosses = BossNames(template)
	local taken = {}
	for _, e in ipairs(enemies) do if e.icon then taken[e.icon] = true end end
	-- Gruppen: NPC-IDs mit eigener Symbolreihenfolge, sonst alle Gegner außer Bossen
	local groups = template.npcs or { { icons = template.order } }
	local marked = 0
	for _, g in ipairs(groups) do
		local ids
		if g.ids then ids = {}; for _, id in ipairs(g.ids) do ids[id] = true end end
		local icons = g.icons or template.order
		local pos = 1
		for _, e in ipairs(enemies) do
			local fits = not e.icon and not e.done and (ids and e.npc and ids[e.npc] or (not ids and not bosses[e.name or ""]))
			if fits then
				while icons[pos] and taken[icons[pos]] do pos = pos + 1 end
				local icon = icons[pos]
				if not icon then break end
				local ok = pcall(SetRaidTarget, e.unit, icon)
				if ok then
					taken[icon], used[icon], e.done = true, true, true
					marked = marked + 1
				end
				pos = pos + 1
			end
		end
	end
	if marked > 0 then
		RM.Print(string.format(L["%d Gegner markiert (Vorlage: %s)."], marked, template.name))
	else
		RM.Print(L["Keine passenden Gegner gefunden – schon markiert oder nicht sichtbar."])
	end
end

function M.ResetUsed()
	wipe(used)
end

RM.On("PLAYER_REGEN_ENABLED", function() wipe(used) end)

-- Bosskampf beginnt: Bossname übernehmen und die Markierungsvorlage des Bosses wählen
RM.On("ENCOUNTER_START", function(encounterID, encounterName)
	RM.Data.LearnBossName(encounterID, encounterName)
	if not RM.db or not C().autoTemplate then return end
	local boss = RM.Data.Bosses[encounterID]
	if boss and boss.template and C().markerTemplate ~= boss.template then
		C().markerTemplate = boss.template
		wipe(used)
		RM.Fire("CONFIG_CHANGED")
	end
end)

---------------------------------------------------------------------------
-- Markierungsleiste
---------------------------------------------------------------------------
local function IconTexture(i)
	return "Interface\\TargetingFrame\\UI-RaidTargetingIcon_" .. i
end

local ICON_SIZE, GAP, PAD = 22, 3, 5

-- Kleiner Knopf der Leiste: Grafik, weicher Hover, Tooltip
local function BarButton(parent, texture, size, tooltipFn, onClick)
	local b = CreateFrame("Button", nil, parent)
	b:SetSize(size, size)
	b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
	b.icon = b:CreateTexture(nil, "ARTWORK")
	b.icon:SetAllPoints()
	b.icon:SetTexture(texture)
	local hl = b:CreateTexture(nil, "HIGHLIGHT")
	hl:SetPoint("TOPLEFT", -2, 2)
	hl:SetPoint("BOTTOMRIGHT", 2, -2)
	hl:SetTexture("Interface\\Buttons\\ButtonHilight-Square")
	hl:SetBlendMode("ADD")
	b:SetScript("OnMouseDown", function(self) self.icon:SetPoint("TOPLEFT", 1, -1); self.icon:SetPoint("BOTTOMRIGHT", 1, -1) end)
	b:SetScript("OnMouseUp", function(self) self.icon:SetAllPoints() end)
	b:SetScript("OnClick", onClick)
	b:SetScript("OnEnter", function(self)
		GameTooltip:SetOwner(self, "ANCHOR_TOP")
		tooltipFn(GameTooltip)
		GameTooltip:Show()
	end)
	b:SetScript("OnLeave", function() GameTooltip:Hide() end)
	return b
end

local function CreateBar()
	local UI = RM.UI
	local f = UI.Frame(UIParent, 10, ICON_SIZE + PAD * 2)
	f:SetBackdrop({ bgFile = "Interface\\Buttons\\WHITE8x8", edgeFile = "Interface\\Buttons\\WHITE8x8", edgeSize = 1 })
	f:SetBackdropColor(0.03, 0.03, 0.04, 0.72)
	f:SetBackdropBorderColor(0, 0, 0, 0.9)
	f:SetFrameStrata("MEDIUM")
	UI.MakeMovable(f, "markerBar", "CENTER", 0, -220)
	f:SetClampedToScreen(true)

	-- schmaler Akzentstreifen links = Griff zum Verschieben
	local grip = f:CreateTexture(nil, "ARTWORK")
	grip:SetColorTexture(UI.COLORS.accent[1], UI.COLORS.accent[2], UI.COLORS.accent[3], 0.85)
	grip:SetPoint("TOPLEFT", 1, -1)
	grip:SetPoint("BOTTOMLEFT", 1, 1)
	grip:SetWidth(2)

	local x = PAD + 3
	for _, i in ipairs({ 8, 7, 6, 5, 4, 3, 2, 1 }) do
		local b = BarButton(f, IconTexture(i), ICON_SIZE, function(tip)
			tip:AddLine(RM.Data.MarkerNames[i], 1, 0.82, 0)
			tip:AddLine(L["Linksklick: auf Maus-Ziel/Ziel setzen"], 0.85, 0.85, 0.85)
			tip:AddLine(L["Rechtsklick: Symbol entfernen"], 0.85, 0.85, 0.85)
		end, function(_, button)
			if button == "RightButton" then M.Mark(0) else M.Mark(i) end
		end)
		b:SetPoint("LEFT", x, 0)
		x = x + ICON_SIZE + GAP
	end

	local sep = f:CreateTexture(nil, "ARTWORK")
	sep:SetColorTexture(1, 1, 1, 0.15)
	sep:SetSize(1, ICON_SIZE - 4)
	sep:SetPoint("LEFT", x + 1, 0)
	x = x + 5

	local auto = BarButton(f, "Interface\\Buttons\\UI-RefreshButton", ICON_SIZE - 4, function(tip)
		tip:AddLine(L["Auto"], 1, 0.82, 0)
		tip:AddLine(L["Setzt das nächste freie Symbol der gewählten Vorlage.\nAm schnellsten per Tastenbelegung mit Mouseover."], 0.85, 0.85, 0.85, true)
		tip:AddLine(L["Vorlage: "] .. RM.Data.GetTemplate(C().markerTemplate).name, 1, 0.55, 0.1)
	end, function() M.SmartMark() end)
	auto:SetPoint("LEFT", x + 2, 0)
	x = x + ICON_SIZE

	local adds = BarButton(f, "Interface\\Icons\\Ability_Hunter_SniperShot", ICON_SIZE - 2, function(tip)
		tip:AddLine(L["Adds markieren"], 1, 0.82, 0)
		tip:AddLine(L["Markiert alle sichtbaren Adds auf einmal nach der Vorlage des Bosses (z. B. Garrs Feuerschwörer, Sulfurons Priester).\nGegner-Namensplaketten müssen an sein (Taste V)."], 0.85, 0.85, 0.85, true)
		tip:AddLine(L["Vorlage: "] .. RM.Data.GetTemplate(C().markerTemplate).name, 1, 0.55, 0.1)
	end, function() M.MarkAdds() end)
	adds:SetPoint("LEFT", x + 3, 0)
	adds.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	x = x + ICON_SIZE + 1

	local clear = BarButton(f, "Interface\\Buttons\\UI-GroupLoot-Pass-Up", ICON_SIZE - 2, function(tip)
		tip:AddLine(L["Alle aus"], 1, 0.82, 0)
		tip:AddLine(L["Alle Schlachtzugsymbole auf einmal ausblenden (bei allen Gegnern und Spielern).\nAuch per Tastenbelegung oder /rm clear."], 0.85, 0.85, 0.85, true)
	end, function() M.ClearAll() end)
	clear:SetPoint("LEFT", x + 2, 0)
	x = x + ICON_SIZE + 2

	f:SetWidth(x + PAD)
	return f
end

function M.UpdateBar()
	if not RM.db then return end
	-- die kleine Symbolleiste sehen nur Raidleiter und Co-Raidleiter
	local show = C().markerBar and M.IsMarkerLead()
	if show then
		bar = bar or CreateBar()
		bar:Show()
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
RM.On("GROUP_ROSTER_UPDATE", function() M.UpdateBar() end)
RM.On("PARTY_LEADER_CHANGED", function() M.UpdateBar() end)
RM.Listen("CONFIG_CHANGED", function() M.UpdateBar() end)

---------------------------------------------------------------------------
-- Boss-Infos im Raid posten
---------------------------------------------------------------------------
-- Kurzinfo: alle Zeilen als Schlachtzugwarnung (nie im normalen Chat)
function M.PostBossInfo(encounterID, info)
	info = info or RM.Data.BossInfo[encounterID]
	if not info then return end
	local lines = {}
	for _, l in ipairs(info.post or {}) do lines[#lines + 1] = l end
	-- Magmadar: Einlull-Rotation der Jäger gleich mit ansagen
	if encounterID == 664 and RM.Tranq then
		local list = RM.Tranq.Rotation()
		if #list > 0 then
			local parts = {}
			for i, h in ipairs(list) do parts[#parts + 1] = i .. ". " .. h end
			lines[#lines + 1] = L["Einlull-Rotation: "] .. table.concat(parts, " > ")
		end
	end
	RM.RaidWarning(lines)
end
