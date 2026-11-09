-- RaidMaster - Schlachtzugsymbole
-- Markierungsleiste, Mouseover-Tasten, nächstes freies Symbol nach Vorlage, alle entfernen

local ADDON, RM = ...
local L = RM.L
local M = {}
RM.Markers = M

local used = {}   -- in diesem Kampf vergebene Symbole
local bar

local function C() return RM.db.config end

-- Moderner Client (WoW Forever, Retail): Im Kampf kommen Gegnerdaten als "secret values", und Blizzard will
-- kein automatisches Markieren fremder Einheiten. Dort im Kampf nur noch Mark/SmartMark per Mouseover-Taste.
-- Alte Clients (Classic Era, TBC … MoP Classic) bleiben genau wie bisher.
M.MODERN = RM.IsModern and true or false   -- beim Laden; CombatBlocked fragt RM.IsModern jedes Mal neu
M.simCombat = false        -- Test-Werkzeug: Kampf im modernen Client vorspielen
M.COMBAT_HINT = "Im Kampf bitte per Mouseover-Taste markieren."

function M.CombatBlocked()
	if M.simCombat then return true end
	if not RM.IsModern then return false end
	return RM.InCombat()
end

-- WoW Forever (moderner Client, wie Retail ab Patch 12.0): SetRaidTarget ist geschützt. Aus Addon-Code meldet das
-- Spiel ADDON_ACTION_FORBIDDEN – auch nach einem Klick des Spielers (Testberichte 8. Nov.: Klick auf die Leiste,
-- Markers.lua:304). Erlaubt ist es nur über einen sicheren Knopf (SecureActionButtonTemplate, Makro /tm).
-- Ab 3.0.19 darum dort: Symbol-Leiste und RaidMaster-Tasten als sichere Knöpfe; "Adds markieren", die Boss-Leiste
-- und /rm clear zeigen einen Vorschlag bzw. Hinweis statt selbst zu markieren. Alte Clients bleiben wie bisher.
M.simSecure = nil          -- Test-Werkzeug: nil = echte Erkennung, true/false = vorspielen
function M.SecureOnly()
	if M.simSecure ~= nil then return M.simSecure end
	return RM.IsModern and true or false
end
M.SECURE_HINT = "In WoW Forever setzen nur die Symbol-Leiste und die RaidMaster-Tasten Symbole (Regel des Spiels)."
M.SUGGEST_HINT = "Selbst setzen: Gegner anvisieren oder mit der Maus darauf zeigen, dann Symbol-Leiste oder Mouseover-Taste."

-- Wert nur verwenden, wenn er lesbar ist (secret value → nil)
local function Plain(v)
	if RM.IsSecret(v) then return nil end
	return v
end

-- Spiel-API über RM.API (die Testroutine stellt so Einheiten nach, ohne Blizzard-Funktionen zu ersetzen)
local function API(name) return RM.API.Get(name) end

local function TargetUnit()
	local UnitExists = API("UnitExists")
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
	if M.SecureOnly() then RM.Print(L[M.SECURE_HINT]) return end
	local unit = TargetUnit()
	if not unit then return end
	if not CanMark() then RM.Print(L[NO_RIGHTS]) return end
	local ok = pcall(RM.Act.SetRaidTarget, unit, icon)
	if ok and icon and icon > 0 then used[icon] = true end
end

-- Aktuell sichtbar vergebene Symbole (Ziele der Raidmitglieder)
local function IconsInUse()
	local inUse = {}
	for k in pairs(used) do inUse[k] = true end
	local UnitExists, GetRaidTargetIndex = API("UnitExists"), API("GetRaidTargetIndex")
	local function check(unit)
		if UnitExists(unit) then
			local i = Plain(GetRaidTargetIndex(unit))
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

-- Nächstes freies Symbol der gewählten Vorlage für eine Einheit.
-- Rückgabe: Symbol; nil, "skip" (schon markiert, Spieler, tot); nil, "full" (alle vergeben)
local function NextFreeIcon(unit)
	if Plain(API("GetRaidTargetIndex")(unit)) then return nil, "skip" end
	if Plain(API("UnitIsPlayer")(unit)) or Plain(API("UnitIsDead")(unit)) then return nil, "skip" end
	local template = RM.Data.GetTemplate(C().markerTemplate)
	local inUse = IconsInUse()
	for _, icon in ipairs(template.order) do
		if not inUse[icon] then return icon end
	end
	return nil, "full"
end
M.NextFreeIcon = NextFreeIcon

local function FullHint()
	RM.Print(L["Alle Symbole der Vorlage '"] .. RM.Data.GetTemplate(C().markerTemplate).name .. L["' sind vergeben."])
end

-- Nächstes freies Symbol aus der gewählten Vorlage
function M.SmartMark()
	if M.SecureOnly() then RM.Print(L[M.SECURE_HINT]) return end
	local unit = TargetUnit()
	if not unit then return end
	if not CanMark() then RM.Print(L[NO_RIGHTS]) return end
	local icon, why = NextFreeIcon(unit)
	if icon then
		if pcall(RM.Act.SetRaidTarget, unit, icon) then used[icon] = true end
	elseif why == "full" then
		FullHint()
	end
end

-- Alle Symbole entfernen: jedes Symbol kurz auf sich selbst setzen, dann löschen
function M.ClearAll()
	if M.SecureOnly() then RM.Print(L[M.SECURE_HINT]) return end
	if not CanMark() then RM.Print(L[NO_RIGHTS]) return end
	local step = 0
	for i = 8, 1, -1 do
		step = step + 1
		C_Timer.After(step * 0.12, function() RM.Act.SetRaidTarget("player", i) end)
	end
	C_Timer.After((step + 1) * 0.12 + 0.1, function()
		RM.Act.SetRaidTarget("player", 0)
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
	local UnitExists, UnitName = API("UnitExists"), API("UnitName")
	for i = 1, 5 do
		local n = UnitExists("boss" .. i) and UnitName("boss" .. i)
		if n and not RM.IsSecret(n) then names[n] = true end
	end
	return names
end

-- Sichtbare Gegner. Zweiter Rückgabewert: Anzahl Gegner, deren Daten der Client sperrt
-- ("secret values" im Kampf, WoW Forever/Midnight) – die lassen sich nur per Symbolknopf markieren.
local function VisibleEnemies()
	local list, seen, blocked = {}, {}, 0
	local UnitExists, UnitIsPlayer, UnitIsDead = API("UnitExists"), API("UnitIsPlayer"), API("UnitIsDead")
	local UnitCanAttack, UnitGUID, UnitName = API("UnitCanAttack"), API("UnitGUID"), API("UnitName")
	local UnitCreatureType, GetRaidTargetIndex = API("UnitCreatureType"), API("GetRaidTargetIndex")
	local function check(unit)
		if not UnitExists(unit) or UnitIsPlayer(unit) or UnitIsDead(unit) then return end
		if not UnitCanAttack("player", unit) then return end
		local ok, guid = pcall(UnitGUID, unit)
		if ok and RM.IsSecret(guid) then blocked = blocked + 1 return end
		if not ok or type(guid) ~= "string" or seen[guid] then return end
		local ctype = UnitCreatureType and Plain(UnitCreatureType(unit))
		if ctype == "Critter" or ctype == "Kleintier" then return end
		seen[guid] = true
		local name = UnitName(unit)
		if RM.IsSecret(name) then name = nil end
		list[#list + 1] = { unit = unit, guid = guid, npc = NpcID(guid), name = name, icon = Plain(GetRaidTargetIndex(unit)) }
	end
	for i = 1, 40 do check("nameplate" .. i) end
	for _, u in ipairs({ "target", "mouseover", "focus" }) do check(u) end
	table.sort(list, function(a, b) return a.guid < b.guid end)
	return list, blocked
end

function M.MarkAdds()
	if not CanMark() then RM.Print(L[NO_RIGHTS]) return end
	if M.CombatBlocked() then RM.Print(L[M.COMBAT_HINT]) return end
	local template = RM.Data.GetTemplate(C().markerTemplate)
	local enemies, blocked = VisibleEnemies()
	if #enemies == 0 and blocked > 0 then
		RM.Print(L[M.COMBAT_HINT])
		return
	end
	if #enemies == 0 then
		RM.Print(L["Keine Gegner sichtbar. Namensplaketten der Gegner einschalten (Taste V) und näher an die Adds gehen."])
		return
	end
	local bosses = BossNames(template)
	local secure = M.SecureOnly()
	local plan = {}
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
				local ok
				if secure then
					-- WoW Forever: nur Vorschlag, setzen kann nur ein sicherer Knopf
					plan[#plan + 1] = (RM.Data.MarkerNames[icon] or icon) .. ": " .. (e.name or L["Gegner"])
					ok = true
				else
					ok = pcall(RM.Act.SetRaidTarget, e.unit, icon)
				end
				if ok then
					taken[icon], used[icon], e.done = true, true, true
					marked = marked + 1
				end
				pos = pos + 1
			end
		end
	end
	if secure and marked > 0 then
		wipe(used)              -- nichts gesetzt: Symbole bleiben frei
		RM.Print(string.format(L["Vorschlag (Vorlage: %s): %s"], template.name, table.concat(plan, ", ")))
		RM.Print(L[M.SUGGEST_HINT])
		M.lastPlan = plan
	elseif marked > 0 then
		RM.Print(string.format(L["%d Gegner markiert (Vorlage: %s)."], marked, template.name))
	else
		RM.Print(L["Keine passenden Gegner gefunden – schon markiert oder nicht sichtbar."])
	end
end

function M.ResetUsed()
	wipe(used)
end

RM.On("PLAYER_REGEN_ENABLED", function() wipe(used) end)   -- (WoW Forever: sichere Knöpfe siehe unten)

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

---------------------------------------------------------------------------
-- Sichere Knöpfe (nur WoW Forever / moderner Client, siehe M.SecureOnly)
-- Makro "/tm": Maus-Ziel, sonst Ziel. Attribute nur ausserhalb des Kampfs ändern (sonst blockiert das Spiel).
---------------------------------------------------------------------------
local SECURE = "SecureActionButtonTemplate"
local function MarkMacro(icon) return "/tm [@mouseover,exists][] " .. icon end
M.MarkMacro = MarkMacro
local CLEAR_ALL_MACRO = (function()
	local lines = {}
	for i = 8, 1, -1 do lines[#lines + 1] = "/tm [@player] " .. i end
	lines[#lines + 1] = "/tm [@player] 0"
	return table.concat(lines, "\n")
end)()
M.CLEAR_ALL_MACRO = CLEAR_ALL_MACRO

local function Locked() return RM.InCombat() end

-- Sicherer Knopf mit Makro; left = Makro für Linksklick/Taste, right = Makro für Rechtsklick (optional)
local function SecureButton(name, parent, left, right)
	local b = CreateFrame("Button", name, parent, SECURE)
	b:RegisterForClicks("AnyUp", "AnyDown")
	b:SetAttribute("type", "macro")
	b:SetAttribute("macrotext", left)
	if right then
		b:SetAttribute("type2", "macro")
		b:SetAttribute("macrotext2", right)
	end
	return b
end

-- "Auto" als sicherer Knopf: ausserhalb des Kampfs genau das nächste freie Symbol (wie SmartMark); im Kampf
-- kann nur ein gesicherter Ablauf das Makro ändern – dann der Reihe nach die Symbole der Vorlage.
local smartButtons = {}
local header
local SMART_PRE = [[
	if self:GetAttribute("rm-fixed") then return end
	local n = (self:GetAttribute("rm-n") or 0) + 1
	local icon = self:GetAttribute("rm-icon" .. n)
	if not icon then n = 1; icon = self:GetAttribute("rm-icon1") end
	self:SetAttribute("rm-n", n)
	if icon then self:SetAttribute("macrotext", "/tm [@mouseover,exists][] " .. icon) end
]]

local function PrepareSmart(b)
	if Locked() then return end
	local order = RM.Data.GetTemplate(C().markerTemplate).order or {}
	for i = 1, 8 do b:SetAttribute("rm-icon" .. i, order[i]) end
	b:SetAttribute("rm-n", 0)
	b:SetAttribute("rm-fixed", nil)
end

local function SmartButton(name, parent)
	local b = SecureButton(name, parent, "")
	b:SetScript("PreClick", function(self)
		if Locked() then return end
		local unit = TargetUnit()
		local icon, why = nil, nil
		if unit and CanMark() then icon, why = NextFreeIcon(unit) end
		self:SetAttribute("macrotext", icon and MarkMacro(icon) or "")
		self:SetAttribute("rm-fixed", 1)
		self.rmIcon = icon
		if why == "full" then FullHint() end
	end)
	b:SetScript("PostClick", function(self)
		if self.rmIcon then used[self.rmIcon] = true end
		self.rmIcon = nil
		if not Locked() then self:SetAttribute("rm-fixed", nil) end
	end)
	if SecureHandlerWrapScript and CreateFrame then
		header = header or CreateFrame("Frame", nil, UIParent, "SecureHandlerBaseTemplate")
		pcall(SecureHandlerWrapScript, b, "OnClick", header, SMART_PRE)
	end
	smartButtons[#smartButtons + 1] = b
	PrepareSmart(b)
	return b
end

-- Unsichtbare Knöpfe für die RaidMaster-Tasten. Die Tasten aus den Tastenbelegungen werden auf sie umgelenkt
-- (Override), die Belegung selbst bleibt beim Spieler.
local keyOwner, keyButtons, keySignature
local KEY_MAP = { RAIDMASTER_SMARTMARK = "Smart", RAIDMASTER_CLEARMARK = "Clear", RAIDMASTER_CLEARALL = "ClearAll" }
for i = 1, 8 do KEY_MAP["RAIDMASTER_MARK" .. i] = "Mark" .. i end
M.KEY_MAP = KEY_MAP

local function KeyButtons()
	if keyButtons then return keyButtons end
	keyButtons = {}
	for i = 1, 8 do keyButtons["Mark" .. i] = SecureButton("RaidMasterKeyMark" .. i, UIParent, MarkMacro(i)) end
	keyButtons.Clear = SecureButton("RaidMasterKeyClear", UIParent, MarkMacro(0))
	keyButtons.ClearAll = SecureButton("RaidMasterKeyClearAll", UIParent, CLEAR_ALL_MACRO)
	keyButtons.Smart = SmartButton("RaidMasterKeySmart", UIParent)
	for _, b in pairs(keyButtons) do b:Hide() end
	return keyButtons
end

function M.ApplyKeys()
	if not M.SecureOnly() or Locked() then return end
	if not (SetOverrideBindingClick and ClearOverrideBindings and ((GetNumBindings and GetBinding) or GetBindingKey)) then return end
	-- Tasten aus der normalen Belegung lesen (GetBinding: ohne unsere Overrides, sonst Wechselspiel bei UPDATE_BINDINGS)
	local list = {}
	if GetNumBindings and GetBinding then
		for i = 1, GetNumBindings() do
			local cmd, _, k1, k2 = GetBinding(i)
			local id = cmd and KEY_MAP[cmd]
			if id then
				if type(k1) == "string" and k1 ~= "" then list[#list + 1] = k1 .. "\t" .. id end
				if type(k2) == "string" and k2 ~= "" then list[#list + 1] = k2 .. "\t" .. id end
			end
		end
	else
		for binding, id in pairs(KEY_MAP) do
			for _, key in ipairs({ GetBindingKey(binding) }) do list[#list + 1] = key .. "\t" .. id end
		end
	end
	table.sort(list)
	local sig = table.concat(list, ",")
	if sig == keySignature then return end
	keySignature = sig
	keyOwner = keyOwner or CreateFrame("Frame")
	local buttons = KeyButtons()
	ClearOverrideBindings(keyOwner)
	for _, entry in ipairs(list) do
		local key, id = entry:match("^(.-)\t(%w+)$")
		if key and buttons[id] then SetOverrideBindingClick(keyOwner, true, key, buttons[id]:GetName(), "LeftButton") end
	end
end

local function RefreshSecure()
	if Locked() then return end
	for _, b in ipairs(smartButtons) do PrepareSmart(b) end
	M.ApplyKeys()
end
M.RefreshSecure = RefreshSecure

-- Knopf der Leiste aussehen lassen wie BarButton (Grafik, Hover, Tooltip)
local function Dress(b, parent, texture, size, tooltipFn)
	b:SetParent(parent)
	b:SetSize(size, size)
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
	b:SetScript("OnEnter", function(self)
		GameTooltip:SetOwner(self, "ANCHOR_TOP")
		tooltipFn(GameTooltip)
		GameTooltip:Show()
	end)
	b:SetScript("OnLeave", function() GameTooltip:Hide() end)
	return b
end

-- Knopf der Leiste: alte Clients wie bisher, WoW Forever sicher (secure = { left, right } oder "smart")
local function LeisteButton(parent, texture, size, tooltipFn, onClick, secure)
	if not M.SecureOnly() or not secure then return BarButton(parent, texture, size, tooltipFn, onClick) end
	local b
	if secure == "smart" then b = SmartButton(nil, parent) else b = SecureButton(nil, parent, secure[1], secure[2]) end
	b.secure = true
	return Dress(b, parent, texture, size, tooltipFn)
end

local function CreateBar()
	local UI = RM.UI
	local f = UI.Frame(UIParent, 10, ICON_SIZE + PAD * 2, "Markierungsleiste")
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
		local b = LeisteButton(f, IconTexture(i), ICON_SIZE, function(tip)
			tip:AddLine(RM.Data.MarkerNames[i], 1, 0.82, 0)
			tip:AddLine(L["Linksklick: auf Maus-Ziel/Ziel setzen"], 0.85, 0.85, 0.85)
			tip:AddLine(L["Rechtsklick: Symbol entfernen"], 0.85, 0.85, 0.85)
		end, function(_, button)
			if button == "RightButton" then M.Mark(0) else M.Mark(i) end
		end, { MarkMacro(i), MarkMacro(0) })
		b:SetPoint("LEFT", x, 0)
		x = x + ICON_SIZE + GAP
	end

	local sep = f:CreateTexture(nil, "ARTWORK")
	sep:SetColorTexture(1, 1, 1, 0.15)
	sep:SetSize(1, ICON_SIZE - 4)
	sep:SetPoint("LEFT", x + 1, 0)
	x = x + 5

	local auto = LeisteButton(f, "Interface\\Buttons\\UI-RefreshButton", ICON_SIZE - 4, function(tip)
		tip:AddLine(L["Auto"], 1, 0.82, 0)
		tip:AddLine(L["Setzt das nächste freie Symbol der gewählten Vorlage.\nAm schnellsten per Tastenbelegung mit Mouseover."], 0.85, 0.85, 0.85, true)
		tip:AddLine(L["Vorlage: "] .. RM.Data.GetTemplate(C().markerTemplate).name, 1, 0.55, 0.1)
	end, function() M.SmartMark() end, "smart")
	auto:SetPoint("LEFT", x + 2, 0)
	x = x + ICON_SIZE

	local adds = BarButton(f, "Interface\\Icons\\Ability_Hunter_SniperShot", ICON_SIZE - 2, function(tip)
		tip:AddLine(L["Adds markieren"], 1, 0.82, 0)
		tip:AddLine(L["Markiert alle sichtbaren Adds auf einmal nach der Vorlage des Bosses (z. B. Garrs Feuerschwörer, Sulfurons Priester).\nGegner-Namensplaketten müssen an sein (Taste V)."], 0.85, 0.85, 0.85, true)
		tip:AddLine(L["Vorlage: "] .. RM.Data.GetTemplate(C().markerTemplate).name, 1, 0.55, 0.1)
		-- moderner Client im Kampf: Knopf wirkt nicht, Hinweis auf die Mouseover-Tasten
		if M.CombatBlocked() then tip:AddLine(L[M.COMBAT_HINT], 1, 0.3, 0.3, true) end
	end, function() M.MarkAdds() end)
	M.addsButton = adds
	adds:SetPoint("LEFT", x + 3, 0)
	adds.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	x = x + ICON_SIZE + 1

	local clear = LeisteButton(f, "Interface\\Buttons\\UI-GroupLoot-Pass-Up", ICON_SIZE - 2, function(tip)
		tip:AddLine(L["Alle aus"], 1, 0.82, 0)
		tip:AddLine(L["Alle Schlachtzugsymbole auf einmal ausblenden (bei allen Gegnern und Spielern).\nAuch per Tastenbelegung oder /rm clear."], 0.85, 0.85, 0.85, true)
	end, function() M.ClearAll() end, { CLEAR_ALL_MACRO })
	clear:SetPoint("LEFT", x + 2, 0)
	x = x + ICON_SIZE + 2

	f:SetWidth(x + PAD)
	return f
end

function M.UpdateBar()
	if not RM.db then return end
	-- WoW Forever: die Leiste hat sichere Knöpfe – im Kampf weder anlegen noch zeigen/verstecken (blockiert),
	-- sondern nach dem Kampf nachholen
	if M.SecureOnly() and Locked() then M.pendingBar = true return end
	M.pendingBar = nil
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

RM.Listen("LOGIN", function() M.UpdateBar(); if M.SecureOnly() then RefreshSecure() end end)
RM.On("GROUP_ROSTER_UPDATE", function() M.UpdateBar() end)
RM.On("PARTY_LEADER_CHANGED", function() M.UpdateBar() end)
RM.Listen("CONFIG_CHANGED", function() M.UpdateBar(); if M.SecureOnly() then RefreshSecure() end end)
RM.On("UPDATE_BINDINGS", function() if M.SecureOnly() then M.ApplyKeys() end end)
RM.On("PLAYER_REGEN_ENABLED", function()
	if not M.SecureOnly() then return end
	if M.pendingBar then M.UpdateBar() end
	RefreshSecure()
end)

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
	-- Majordomus: Sheep-Rotation der Magier gleich mit ansagen
	if encounterID == 671 and RM.Sheep then
		local line = RM.Sheep.Line()
		if line then lines[#lines + 1] = line end
	end
	RM.RaidWarning(lines)
end
