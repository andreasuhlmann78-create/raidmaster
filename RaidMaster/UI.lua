-- RaidMaster - Oberfläche (Grundbausteine, Hauptfenster, Minimap-Knopf, Dialoge)

local ADDON, RM = ...
local L = RM.L
local UI = {}
RM.UI = UI

UI.pages = {}
UI.pageOrder = {}

local COLORS = {
	bg = { 0.05, 0.055, 0.07, 0.97 },
	panel = { 0.085, 0.09, 0.11, 0.96 },
	field = { 0.03, 0.035, 0.045, 1 },
	border = { 0.2, 0.21, 0.25, 1 },
	accent = { 1, 0.55, 0.1 },
	text = { 0.92, 0.92, 0.92 },
	muted = { 0.6, 0.62, 0.66 },
}
UI.COLORS = COLORS

local BACKDROP = { bgFile = "Interface\\Buttons\\WHITE8x8", edgeFile = "Interface\\Buttons\\WHITE8x8", edgeSize = 1 }
local TEMPLATE = BackdropTemplateMixin and "BackdropTemplate" or nil

---------------------------------------------------------------------------
-- Grundbausteine
---------------------------------------------------------------------------
function UI.Frame(parent, w, h)
	local f = CreateFrame("Frame", nil, parent, TEMPLATE)
	if w and h then f:SetSize(w, h) end
	return f
end

function UI.Skin(f, bg, border)
	f:SetBackdrop(BACKDROP)
	local b = bg or COLORS.bg
	f:SetBackdropColor(b[1], b[2], b[3], b[4] or 1)
	local e = border or COLORS.border
	f:SetBackdropBorderColor(e[1], e[2], e[3], e[4] or 1)
end

function UI.Text(parent, text, size, r, g, b, justify)
	local fs = parent:CreateFontString(nil, "OVERLAY")
	fs:SetFont(STANDARD_TEXT_FONT, size or 12, "")
	fs:SetText(text or "")
	fs:SetTextColor(r or COLORS.text[1], g or COLORS.text[2], b or COLORS.text[3])
	fs:SetJustifyH(justify or "LEFT")
	fs:SetWordWrap(true)
	return fs
end

function UI.Header(parent, text)
	local fs = UI.Text(parent, text, 14, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
	return fs
end

local function ShowTooltip(owner, text)
	if not text then return end
	GameTooltip:SetOwner(owner, "ANCHOR_RIGHT")
	for line in tostring(text):gmatch("[^\n]+") do
		GameTooltip:AddLine(line, 1, 1, 1, true)
	end
	GameTooltip:Show()
end

function UI.Button(parent, text, w, h, onClick, tooltip)
	local b = CreateFrame("Button", nil, parent, TEMPLATE)
	b:SetSize(w or 100, h or 24)
	UI.Skin(b, { 0.13, 0.14, 0.17, 1 })
	b.label = UI.Text(b, text, 12, nil, nil, nil, "CENTER")
	b.label:SetPoint("CENTER")
	b.label:SetWordWrap(false)
	b:SetScript("OnClick", function(self, button)
		if onClick then onClick(self, button) end
	end)
	b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
	b:SetScript("OnEnter", function(self)
		if self:IsEnabled() then self:SetBackdropBorderColor(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 1) end
		ShowTooltip(self, self.tooltip)
	end)
	b:SetScript("OnLeave", function(self)
		self:SetBackdropBorderColor(unpack(COLORS.border))
		GameTooltip:Hide()
	end)
	b.tooltip = tooltip
	function b:SetText(t) self.label:SetText(t) end
	function b:SetAccent(on)
		if on then
			self:SetBackdropColor(0.55, 0.28, 0.04, 1)
		else
			self:SetBackdropColor(0.13, 0.14, 0.17, 1)
		end
	end
	hooksecurefunc(b, "Disable", function(self) self.label:SetTextColor(0.4, 0.4, 0.4) end)
	hooksecurefunc(b, "Enable", function(self) self.label:SetTextColor(unpack(COLORS.text)) end)
	return b
end

function UI.CloseButton(parent, onClick)
	local b = UI.Button(parent, "X", 22, 22, onClick)
	b.label:SetFont(STANDARD_TEXT_FONT, 13, "")
	return b
end

function UI.EditBox(parent, w, h, numeric)
	local e = CreateFrame("EditBox", nil, parent, TEMPLATE)
	e:SetSize(w or 120, h or 24)
	UI.Skin(e, COLORS.field)
	e:SetFontObject(ChatFontNormal)
	e:SetTextInsets(6, 6, 0, 0)
	e:SetAutoFocus(false)
	e:SetMaxLetters(255)
	e:SetScript("OnEscapePressed", function(self) self:ClearFocus() end)
	e:SetScript("OnEnterPressed", function(self) self:ClearFocus() end)
	e:SetScript("OnEditFocusGained", function(self) self:SetBackdropBorderColor(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 1) end)
	e:SetScript("OnEditFocusLost", function(self) self:SetBackdropBorderColor(unpack(COLORS.border)) end)
	if numeric then
		e:SetScript("OnChar", function(self)
			local t = self:GetText()
			local clean = t:gsub("[^%d%-]", "")
			if clean ~= t then self:SetText(clean) end
		end)
	end
	return e
end

-- Eingabefeld, in das Shift-Klick-Itemlinks eingefügt werden
function UI.LinkBox(parent, w, h)
	local e = UI.EditBox(parent, w, h)
	e.rmLinkTarget = true
	return e
end

if ChatEdit_InsertLink then
	hooksecurefunc("ChatEdit_InsertLink", function(text)
		local f = GetCurrentKeyBoardFocus and GetCurrentKeyBoardFocus()
		if f and f.rmLinkTarget and text then
			f:SetText(text)
		end
	end)
end

function UI.Check(parent, label, getter, setter, tooltip)
	local c = CreateFrame("CheckButton", nil, parent, TEMPLATE)
	c:SetSize(18, 18)
	UI.Skin(c, COLORS.field)
	local mark = c:CreateTexture(nil, "ARTWORK")
	mark:SetPoint("TOPLEFT", 4, -4)
	mark:SetPoint("BOTTOMRIGHT", -4, 4)
	mark:SetColorTexture(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 1)
	c:SetCheckedTexture(mark)
	c.text = UI.Text(c, label, 12)
	c.text:SetPoint("LEFT", c, "RIGHT", 6, 0)
	c:SetScript("OnClick", function(self) setter(self:GetChecked() and true or false) end)
	c:SetScript("OnEnter", function(self) ShowTooltip(self, tooltip) end)
	c:SetScript("OnLeave", function() GameTooltip:Hide() end)
	function c:Refresh() self:SetChecked(getter() and true or false) end
	c:Refresh()
	return c
end

-- Auswahlknopf: Linksklick vorwärts, Rechtsklick rückwärts
function UI.Cycle(parent, w, options, getter, setter, tooltip)
	local b
	b = UI.Button(parent, "", w, 24, function(_, button)
		local cur = getter()
		local idx = 1
		for i, o in ipairs(options) do if o[1] == cur then idx = i end end
		if button == "RightButton" then idx = idx - 1 else idx = idx + 1 end
		if idx > #options then idx = 1 elseif idx < 1 then idx = #options end
		setter(options[idx][1])
		b:Refresh()
	end, (tooltip and (tooltip .. "\n") or "") .. L["Linksklick: weiter · Rechtsklick: zurück"])
	function b:Refresh()
		local cur = getter()
		for _, o in ipairs(options) do
			if o[1] == cur then self:SetText(o[2]) return end
		end
		self:SetText(tostring(cur))
	end
	b:Refresh()
	return b
end

---------------------------------------------------------------------------
-- Liste mit Spalten, Auswahl, Scrollen und Tooltips
---------------------------------------------------------------------------
function UI.List(parent, width, height, columns, opts)
	opts = opts or {}
	local L = UI.Frame(parent, width, height)
	UI.Skin(L, COLORS.panel)
	L.rowH = opts.rowHeight or 20
	L.offset = 0
	L.data = {}
	L.rows = {}
	L.selectedKey = nil

	local x = 6
	L.headers = {}
	for i, col in ipairs(columns) do
		local h = CreateFrame("Button", nil, L)
		h:SetSize(col.width, 20)
		h:SetPoint("TOPLEFT", x, -3)
		h.text = UI.Text(h, col.title, 11, COLORS.muted[1], COLORS.muted[2], COLORS.muted[3], col.justify or "LEFT")
		h.text:SetAllPoints()
		if opts.onSort then
			h:SetScript("OnClick", function() opts.onSort(i) end)
			h:SetScript("OnEnter", function(self) self.text:SetTextColor(1, 1, 1) end)
			h:SetScript("OnLeave", function(self) self.text:SetTextColor(unpack(COLORS.muted)) end)
		end
		col.x = x
		x = x + col.width + 6
		L.headers[i] = h
	end
	local sep = L:CreateTexture(nil, "ARTWORK")
	sep:SetColorTexture(COLORS.border[1], COLORS.border[2], COLORS.border[3], 1)
	sep:SetPoint("TOPLEFT", 1, -24)
	sep:SetPoint("TOPRIGHT", -1, -24)
	sep:SetHeight(1)

	local visible = math.floor((height - 28) / L.rowH)
	L.visible = visible

	for r = 1, visible do
		local row = CreateFrame("Button", nil, L)
		row:SetSize(width - 18, L.rowH)
		row:SetPoint("TOPLEFT", 1, -26 - (r - 1) * L.rowH)
		row:RegisterForClicks("LeftButtonUp", "RightButtonUp")
		local hl = row:CreateTexture(nil, "HIGHLIGHT")
		hl:SetAllPoints()
		hl:SetColorTexture(1, 1, 1, 0.06)
		row.sel = row:CreateTexture(nil, "BACKGROUND")
		row.sel:SetAllPoints()
		row.sel:SetColorTexture(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 0.22)
		row.sel:Hide()
		if r % 2 == 0 then
			local zebra = row:CreateTexture(nil, "BACKGROUND", nil, -1)
			zebra:SetAllPoints()
			zebra:SetColorTexture(1, 1, 1, 0.025)
		end
		row.cells = {}
		for c, col in ipairs(columns) do
			local fs = UI.Text(row, "", 12, nil, nil, nil, col.justify or "LEFT")
			fs:SetPoint("LEFT", col.x - 1, 0)
			fs:SetWidth(col.width)
			fs:SetWordWrap(false)
			row.cells[c] = fs
		end
		row:SetScript("OnClick", function(self, button)
			local d = L.data[self.index]
			if not d then return end
			L.selectedKey = d.key
			L:Refresh()
			if opts.onSelect then opts.onSelect(d, button) end
		end)
		row:SetScript("OnEnter", function(self)
			local d = L.data[self.index]
			if not d then return end
			if d.link then
				GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
				GameTooltip:SetHyperlink(RM.ItemString(d.link) or d.link)
				GameTooltip:Show()
			elseif d.tooltip then
				GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
				d.tooltip(GameTooltip)
				GameTooltip:Show()
			end
		end)
		row:SetScript("OnLeave", function() GameTooltip:Hide() end)
		L.rows[r] = row
	end

	local slider = CreateFrame("Slider", nil, L, TEMPLATE)
	slider:SetOrientation("VERTICAL")
	slider:SetPoint("TOPRIGHT", -2, -27)
	slider:SetPoint("BOTTOMRIGHT", -2, 3)
	slider:SetWidth(12)
	UI.Skin(slider, COLORS.field)
	local thumb = slider:CreateTexture(nil, "OVERLAY")
	thumb:SetColorTexture(0.35, 0.36, 0.4, 1)
	thumb:SetSize(10, 30)
	slider:SetThumbTexture(thumb)
	slider:SetMinMaxValues(0, 0)
	slider:SetValueStep(1)
	slider:SetValue(0)
	slider:SetScript("OnValueChanged", function(self, value)
		local v = math.floor(value + 0.5)
		if v ~= L.offset then
			L.offset = v
			L:Refresh()
		end
	end)
	L.slider = slider

	L:EnableMouseWheel(true)
	L:SetScript("OnMouseWheel", function(_, delta)
		local mn, mx = slider:GetMinMaxValues()
		local v = math.max(mn, math.min(mx, L.offset - delta * 3))
		slider:SetValue(v)
	end)

	L.empty = UI.Text(L, opts.emptyText or "", 12, COLORS.muted[1], COLORS.muted[2], COLORS.muted[3], "CENTER")
	L.empty:SetPoint("CENTER", 0, -10)

	function L:SetData(data)
		self.data = data or {}
		local mx = math.max(0, #self.data - self.visible)
		self.slider:SetMinMaxValues(0, mx)
		if self.offset > mx then self.offset = mx; self.slider:SetValue(mx) end
		if mx == 0 then self.slider:Hide() else self.slider:Show() end
		self:Refresh()
	end

	function L:Refresh()
		for r, row in ipairs(self.rows) do
			local idx = self.offset + r
			local d = self.data[idx]
			row.index = idx
			if d then
				for c, fs in ipairs(row.cells) do
					fs:SetText(d.cells[c] or "")
					local col = d.colors and d.colors[c]
					if col then fs:SetTextColor(col[1], col[2], col[3]) else fs:SetTextColor(unpack(COLORS.text)) end
				end
				if self.selectedKey ~= nil and d.key == self.selectedKey then row.sel:Show() else row.sel:Hide() end
				row:Show()
			else
				row:Hide()
			end
		end
		if #self.data == 0 then self.empty:Show() else self.empty:Hide() end
	end

	function L:Selected()
		if self.selectedKey == nil then return nil end
		for _, d in ipairs(self.data) do
			if d.key == self.selectedKey then return d end
		end
	end

	function L:ClearSelection()
		self.selectedKey = nil
		self:Refresh()
	end

	return L
end

---------------------------------------------------------------------------
-- Mehrzeiliges Textfeld (Export, Boss-Infos)
---------------------------------------------------------------------------
function UI.Multiline(parent, w, h, readOnly)
	local holder = UI.Frame(parent, w, h)
	UI.Skin(holder, COLORS.field)
	local sf = CreateFrame("ScrollFrame", nil, holder, "UIPanelScrollFrameTemplate")
	sf:SetPoint("TOPLEFT", 6, -6)
	sf:SetPoint("BOTTOMRIGHT", -26, 6)
	local eb = CreateFrame("EditBox", nil, sf)
	eb:SetMultiLine(true)
	eb:SetAutoFocus(false)
	eb:SetFontObject(ChatFontNormal)
	eb:SetWidth(w - 36)
	eb:SetScript("OnEscapePressed", function(self) self:ClearFocus() end)
	sf:SetScrollChild(eb)
	holder.edit = eb
	holder.scroll = sf
	function holder:SetText(t)
		self.text = t or ""
		eb:SetText(self.text)
		eb:SetCursorPosition(0)
		sf:SetVerticalScroll(0)
	end
	if readOnly then
		eb:SetScript("OnTextChanged", function(self, user)
			if user then self:SetText(holder.text or "") end
		end)
	end
	holder:EnableMouse(true)
	holder:SetScript("OnMouseDown", function() eb:SetFocus() end)
	return holder
end

---------------------------------------------------------------------------
-- Verschiebbar mit gespeicherter Position
---------------------------------------------------------------------------
function UI.MakeMovable(f, key, point, x, y)
	f:SetMovable(true)
	f:EnableMouse(true)
	f:RegisterForDrag("LeftButton")
	local pos = RM.db and RM.db.config.positions[key]
	f:ClearAllPoints()
	if pos then
		f:SetPoint(pos[1], UIParent, pos[2], pos[3], pos[4])
	else
		f:SetPoint(point or "CENTER", UIParent, point or "CENTER", x or 0, y or 0)
	end
	f:SetScript("OnDragStart", function(self)
		if key == "markerBar" and RM.db.config.markerLocked then return end
		self:StartMoving()
	end)
	f:SetScript("OnDragStop", function(self)
		self:StopMovingOrSizing()
		local p, _, rp, px, py = self:GetPoint()
		RM.db.config.positions[key] = { p, rp, px, py }
	end)
end

---------------------------------------------------------------------------
-- Bestätigungsdialog
---------------------------------------------------------------------------
StaticPopupDialogs["RAIDMASTER_CONFIRM"] = {
	text = "%s",
	button1 = ACCEPT,
	button2 = CANCEL,
	OnAccept = function(self)
		local d = self.data
		if d and d.ok then d.ok() end
	end,
	OnCancel = function(self, data, reason)
		local d = self.data
		if d and d.cancel and reason == "clicked" then d.cancel() end
	end,
	timeout = 0,
	whileDead = true,
	hideOnEscape = false,
	preferredIndex = 3,
}

function UI.Confirm(text, onAccept, onCancel, acceptText, cancelText)
	local dlg = StaticPopupDialogs["RAIDMASTER_CONFIRM"]
	dlg.button1 = acceptText or ACCEPT
	dlg.button2 = cancelText or CANCEL
	local popup = StaticPopup_Show("RAIDMASTER_CONFIRM", text)
	if popup then popup.data = { ok = onAccept, cancel = onCancel } end
end

---------------------------------------------------------------------------
-- Export-Fenster
---------------------------------------------------------------------------
local exportFrame
function UI.ShowExport(text)
	if not exportFrame then
		local f = UI.Frame(UIParent, 620, 460)
		f:SetFrameStrata("DIALOG")
		UI.Skin(f)
		UI.MakeMovable(f, "export", "CENTER", 0, 0)
		local title = UI.Header(f, L["Export"])
		title:SetPoint("TOPLEFT", 12, -10)
		local hint = UI.Text(f, L["Strg+A markiert alles, Strg+C kopiert. Einfügen z. B. in eine Tabelle oder in Discord."], 11, unpack(COLORS.muted))
		hint:SetPoint("TOPLEFT", 12, -30)
		local close = UI.CloseButton(f, function() f:Hide() end)
		close:SetPoint("TOPRIGHT", -6, -6)
		f.box = UI.Multiline(f, 596, 380, true)
		f.box:SetPoint("TOPLEFT", 12, -50)
		local sel = UI.Button(f, L["Alles markieren"], 140, 24, function()
			f.box.edit:SetFocus()
			f.box.edit:HighlightText()
		end)
		sel:SetPoint("BOTTOMRIGHT", -12, 10)
		exportFrame = f
		tinsert(UISpecialFrames, "RaidMasterExport")
		_G["RaidMasterExport"] = f
	end
	exportFrame.box:SetText(text)
	exportFrame:Show()
	exportFrame.box.edit:SetFocus()
	exportFrame.box.edit:HighlightText()
end

---------------------------------------------------------------------------
-- Hauptfenster
---------------------------------------------------------------------------
function UI.AddPage(id, title, build)
	UI.pages[id] = { id = id, title = title, build = build }
	UI.pageOrder[#UI.pageOrder + 1] = id
end

local main

local function UpdateStatus()
	if not main then return end
	local data = RM.db.data
	local parts = {}
	parts[#parts + 1] = L["Datenstand: "] .. (data.version > 0 and RM.FormatTime(math.min(data.version, GetServerTime())) or "leer")
	parts[#parts + 1] = RM.CanEdit() and L["|cff40ff40Offizier|r"] or L["Nur Ansicht"]
	if RM.db.session.active then
		parts[#parts + 1] = L["|cffff8c1aRaid aktiv seit "] .. date("%H:%M", RM.db.session.started) .. "|r"
	end
	if RM.PUG and RM.PUG.view.active then
		parts[#parts + 1] = L["|cff66ccffPUG-Raid (softres.it)|r"]
	end
	local ml = RM.MasterLooterName()
	if ml then parts[#parts + 1] = L["Plündermeister: "] .. ml end
	parts[#parts + 1] = "v" .. RM.VERSION
	main.status:SetText(table.concat(parts, "   ·   "))
end

function UI.ShowPage(id)
	if not main then return end
	for pid, p in pairs(UI.pages) do
		if p.frame then
			if pid == id then p.frame:Show() else p.frame:Hide() end
		end
		if p.nav then p.nav:SetAccent(pid == id) end
	end
	main.current = id
	UI.RefreshCurrent()
end

function UI.RefreshCurrent()
	if not main or not main:IsShown() then return end
	UpdateStatus()
	local p = UI.pages[main.current]
	if p and p.refresh then
		local ok, err = pcall(p.refresh)
		if not ok then geterrorhandler()(err) end
	end
end

local function CreateMain()
	local f = UI.Frame(UIParent, 980, 640)
	f:SetFrameStrata("HIGH")
	f:SetToplevel(true)
	f:SetClampedToScreen(true)
	UI.Skin(f)
	UI.MakeMovable(f, "main", "CENTER", 0, 20)
	_G["RaidMasterMainFrame"] = f
	tinsert(UISpecialFrames, "RaidMasterMainFrame")

	local titleBar = UI.Frame(f, 980, 40)
	titleBar:SetPoint("TOPLEFT")
	titleBar:SetPoint("TOPRIGHT")
	local tbg = titleBar:CreateTexture(nil, "BACKGROUND")
	tbg:SetAllPoints()
	tbg:SetColorTexture(0.1, 0.06, 0.03, 1)
	local logo = titleBar:CreateTexture(nil, "ARTWORK")
	logo:SetSize(26, 26)
	logo:SetPoint("LEFT", 10, 0)
	logo:SetTexture("Interface\\Icons\\Spell_Fire_Incinerate")
	logo:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	local title = UI.Text(titleBar, "RaidMaster", 17, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
	title:SetPoint("LEFT", logo, "RIGHT", 8, 1)
	local sub = UI.Text(titleBar, L["DKP · Loot · Raidleitung"], 11, unpack(COLORS.muted))
	sub:SetPoint("LEFT", title, "RIGHT", 10, -1)
	local close = UI.CloseButton(titleBar, function() f:Hide() end)
	close:SetPoint("RIGHT", -8, 0)

	local nav = UI.Frame(f, 170, 560)
	nav:SetPoint("TOPLEFT", 0, -40)
	nav:SetPoint("BOTTOMLEFT", 0, 26)
	local nbg = nav:CreateTexture(nil, "BACKGROUND")
	nbg:SetAllPoints()
	nbg:SetColorTexture(0.07, 0.075, 0.09, 1)

	local content = UI.Frame(f, 800, 574)
	content:SetPoint("TOPLEFT", 180, -50)
	content:SetPoint("BOTTOMRIGHT", -10, 34)
	f.content = content

	local footer = UI.Frame(f, 980, 26)
	footer:SetPoint("BOTTOMLEFT")
	footer:SetPoint("BOTTOMRIGHT")
	local fbg = footer:CreateTexture(nil, "BACKGROUND")
	fbg:SetAllPoints()
	fbg:SetColorTexture(0.04, 0.045, 0.055, 1)
	f.status = UI.Text(footer, "", 11, unpack(COLORS.muted))
	f.status:SetPoint("LEFT", 12, 0)

	main = f
	local y = -12
	for _, id in ipairs(UI.pageOrder) do
		local p = UI.pages[id]
		local b = UI.Button(nav, p.title, 150, 32, function() UI.ShowPage(id) end)
		b:SetPoint("TOPLEFT", 10, y)
		b.label:SetJustifyH("LEFT")
		b.label:ClearAllPoints()
		b.label:SetPoint("LEFT", 12, 0)
		p.nav = b
		y = y - 38
		local page = CreateFrame("Frame", nil, content)
		page:SetAllPoints()
		page:Hide()
		p.frame = page
		local ok, refresh = pcall(p.build, page)
		if ok then p.refresh = refresh else geterrorhandler()(refresh) end
	end

	f:SetScript("OnShow", function() UI.RefreshCurrent() end)
	UI.ShowPage(UI.pageOrder[1])
	return f
end

function UI.Toggle()
	if not RM.db then return end
	if not main then
		CreateMain()
		main:Show()
		return
	end
	if main:IsShown() then main:Hide() else main:Show() end
end

function UI.Open(pageId)
	if not main then CreateMain() end
	main:Show()
	if pageId then UI.ShowPage(pageId) end
end

for _, msg in ipairs({ "DATA_CHANGED", "AUCTION_CHANGED", "LOOT_CHANGED", "SESSION_CHANGED", "CHECK_DONE", "CONFIG_CHANGED", "GUILD_CHANGED", "SIGNUP_CHANGED", "PUG_CHANGED", "ASSIGN_CHANGED", "SPEC_CHANGED", "SPEC_SCAN_CHANGED", "AD_CHANGED" }) do
	RM.Listen(msg, function() UI.RefreshCurrent() end)
end
RM.On("GROUP_ROSTER_UPDATE", function() UI.RefreshCurrent() end)
RM.On("PARTY_LOOT_METHOD_CHANGED", function() UI.RefreshCurrent() end)

---------------------------------------------------------------------------
-- Minimap-Knopf
---------------------------------------------------------------------------
-- Position am Rand der Minimap (rund oder eckig, z. B. mit Minimap-Addons)
local function UpdateMinimapPos(btn)
	local angle = math.rad(RM.db.config.minimap.angle or 215)
	local x, y = math.cos(angle), math.sin(angle)
	local r = (Minimap:GetWidth() / 2) + (RM.IsRetail and 10 or 6)
	local shape = GetMinimapShape and GetMinimapShape() or "ROUND"
	if shape == "SQUARE" then
		-- auf dem Rand eines Quadrats entlangführen
		local m = math.max(math.abs(x), math.abs(y))
		x, y = x / m, y / m
		r = (Minimap:GetWidth() / 2) + 2
	end
	btn:ClearAllPoints()
	btn:SetPoint("CENTER", Minimap, "CENTER", x * r, y * r)
end

local function CreateMinimapButton()
	local b = CreateFrame("Button", "RaidMasterMinimapButton", Minimap)
	b:SetSize(31, 31)
	b:SetFrameStrata("MEDIUM")
	b:SetFrameLevel(8)
	local overlay = b:CreateTexture(nil, "OVERLAY")
	overlay:SetSize(53, 53)
	overlay:SetTexture("Interface\\Minimap\\MiniMap-TrackingBorder")
	overlay:SetPoint("TOPLEFT")
	local icon = b:CreateTexture(nil, "BACKGROUND")
	icon:SetSize(20, 20)
	icon:SetTexture("Interface\\Icons\\Spell_Fire_Incinerate")
	icon:SetPoint("CENTER", 0, 1)
	b:SetHighlightTexture("Interface\\Minimap\\UI-Minimap-ZoomButton-Highlight")
	b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
	b:RegisterForDrag("LeftButton")
	b:SetScript("OnClick", function(_, button)
		if button == "RightButton" then RM.Markers.ToggleBar() else UI.Toggle() end
	end)
	b:SetMovable(true)
	b:SetClampedToScreen(true)
	b:SetScript("OnDragStart", function(self)
		self.dragging = true
		GameTooltip:Hide()
		self:SetScript("OnUpdate", function()
			local mx, my = Minimap:GetCenter()
			local cx, cy = GetCursorPosition()
			local scale = Minimap:GetEffectiveScale()
			cx, cy = cx / scale, cy / scale
			RM.db.config.minimap.angle = math.deg(math.atan2(cy - my, cx - mx))
			self:ClearAllPoints()
			UpdateMinimapPos(self)
		end)
	end)
	b:SetScript("OnDragStop", function(self)
		self:SetScript("OnUpdate", nil)
		self.dragging = false
	end)
	b:SetScript("OnEnter", function(self)
		GameTooltip:SetOwner(self, "ANCHOR_LEFT")
		GameTooltip:AddLine("RaidMaster", COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
		if RM.MyGuild() then
			GameTooltip:AddLine(L["Deine DKP: "] .. RM.DKP.Summary(RM.Me()), 1, 1, 1)
		end
		for g, d in pairs(RM.db.foreign) do
			GameTooltip:AddLine(string.format("Deine DKP bei <%s>: %s", g, RM.DKP.Summary(RM.Me(), d)), 1, 0.8, 0.4)
		end
		GameTooltip:AddLine(L["Linksklick: Fenster öffnen"], 0.8, 0.8, 0.8)
		GameTooltip:AddLine(L["Rechtsklick: Markierungsleiste ein/aus"], 0.8, 0.8, 0.8)
		GameTooltip:AddLine(L["Ziehen: um die Minimap verschieben"], 0.8, 0.8, 0.8)
		GameTooltip:AddLine(L["/rm minimap: Knopf ein-/ausblenden"], 0.8, 0.8, 0.8)
		GameTooltip:Show()
	end)
	b:SetScript("OnLeave", function() GameTooltip:Hide() end)
	UpdateMinimapPos(b)
	if RM.db.config.minimap.hide then b:Hide() end
	UI.minimapButton = b
	return b
end

function UI.ToggleMinimapButton()
	local cfg = RM.db.config.minimap
	cfg.hide = not cfg.hide
	if UI.minimapButton then
		if cfg.hide then UI.minimapButton:Hide() else UI.minimapButton:Show() end
	end
	RM.Print(cfg.hide and L["Minimap-Knopf ausgeblendet (/rm minimap zeigt ihn wieder)."] or L["Minimap-Knopf eingeblendet."])
end

RM.Listen("LOGIN", function() CreateMinimapButton() end)
