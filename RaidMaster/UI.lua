-- RaidMaster - Oberfläche (Grundbausteine, Hauptfenster, Minimap-Knopf, Dialoge)

local ADDON, RM = ...
local L = RM.L
local UI = {}
RM.UI = UI

UI.pages = {}
UI.pageOrder = {}

local COLORS = {
	bg = { 0.045, 0.048, 0.06, 0.96 },
	panel = { 0.075, 0.08, 0.098, 0.95 },
	field = { 0.025, 0.028, 0.036, 1 },
	border = { 0.16, 0.17, 0.21, 1 },
	accent = { 1, 0.56, 0.12 },
	text = { 0.93, 0.93, 0.94 },
	muted = { 0.58, 0.6, 0.66 },
	button = { 0.12, 0.125, 0.15, 1 },
	buttonHover = { 0.16, 0.165, 0.2, 1 },
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
	fs:SetShadowOffset(1, -1)
	fs:SetShadowColor(0, 0, 0, 0.85)
	fs:SetText(text or "")
	fs:SetTextColor(r or COLORS.text[1], g or COLORS.text[2], b or COLORS.text[3])
	fs:SetJustifyH(justify or "LEFT")
	fs:SetWordWrap(true)
	return fs
end

function UI.Header(parent, text)
	local fs = UI.Text(parent, text, 14, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
	local line = parent:CreateTexture(nil, "ARTWORK")
	line:SetColorTexture(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 0.35)
	line:SetHeight(1)
	line:SetPoint("TOPLEFT", fs, "BOTTOMLEFT", 0, -4)
	line:SetWidth(240)
	fs.line = line
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
	UI.Skin(b, COLORS.button)
	local shine = b:CreateTexture(nil, "ARTWORK")
	shine:SetColorTexture(1, 1, 1, 0.06)
	shine:SetPoint("TOPLEFT", 1, -1)
	shine:SetPoint("TOPRIGHT", -1, -1)
	shine:SetHeight(1)
	b.label = UI.Text(b, text, 12, nil, nil, nil, "CENTER")
	b.label:SetPoint("CENTER")
	b.label:SetWordWrap(false)
	b:SetScript("OnClick", function(self, button)
		if onClick then onClick(self, button) end
	end)
	b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
	b:SetScript("OnEnter", function(self)
		if self:IsEnabled() then
			self:SetBackdropBorderColor(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 1)
			if not self.accent then self:SetBackdropColor(unpack(COLORS.buttonHover)) end
		end
		ShowTooltip(self, self.tooltip)
	end)
	b:SetScript("OnLeave", function(self)
		self:SetBackdropBorderColor(unpack(COLORS.border))
		if not self.accent then self:SetBackdropColor(unpack(COLORS.button)) end
		GameTooltip:Hide()
	end)
	b.tooltip = tooltip
	function b:SetText(t) self.label:SetText(t) end
	function b:SetAccent(on)
		self.accent = on and true or nil
		if on then
			self:SetBackdropColor(0.6, 0.3, 0.05, 1)
		else
			self:SetBackdropColor(unpack(COLORS.button))
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
-- Aufklappmenü mit Gruppen (z. B. Raids nach WoW-Erweiterung)
-- build() liefert { { text = "Gruppe", items = { {value, text, mark} } }, ... };
-- eine Gruppe ohne text zeigt ihre Einträge direkt in der ersten Spalte.
---------------------------------------------------------------------------
local menu, sub
local ROW_H = 20

local function MenuFrame(level)
	local f = CreateFrame("Frame", nil, UIParent, TEMPLATE)
	UI.Skin(f, COLORS.panel, COLORS.accent)
	f:SetFrameStrata("FULLSCREEN_DIALOG")
	f:SetClampedToScreen(true)
	f:EnableMouse(true)
	f.rows = {}
	f.level = level
	f:Hide()
	return f
end

local function MenuRow(f, i)
	local r = f.rows[i]
	if r then return r end
	r = CreateFrame("Button", nil, f)
	r:SetHeight(ROW_H)
	r:SetPoint("TOPLEFT", 4, -4 - (i - 1) * ROW_H)
	r:SetPoint("TOPRIGHT", -4, -4 - (i - 1) * ROW_H)
	local hl = r:CreateTexture(nil, "HIGHLIGHT")
	hl:SetAllPoints()
	hl:SetColorTexture(1, 1, 1, 0.08)
	r.sel = r:CreateTexture(nil, "BACKGROUND")
	r.sel:SetAllPoints()
	r.sel:SetColorTexture(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 0.25)
	r.text = UI.Text(r, "", 12)
	r.text:SetPoint("LEFT", 6, 0)
	r.text:SetPoint("RIGHT", -16, 0)
	r.text:SetWordWrap(false)
	r.arrow = UI.Text(r, ">", 12, COLORS.muted[1], COLORS.muted[2], COLORS.muted[3], "RIGHT")
	r.arrow:SetPoint("RIGHT", -4, 0)
	f.rows[i] = r
	return r
end

local function CloseMenus()
	if sub then sub:Hide() end
	if menu then menu:Hide() end
end
UI.CloseMenus = CloseMenus

-- Einträge in ein Menüfenster füllen; Gruppen öffnen beim Überfahren die zweite Spalte
local function FillMenu(f, entries, owner, width)
	for _, r in ipairs(f.rows) do r:Hide() end
	local cur = owner.getter()
	for i, e in ipairs(entries) do
		local r = MenuRow(f, i)
		r.entry = e
		r.text:SetText(e.text .. ((e.mark and " |cff40ff40•|r") or ""))
		if e.group then
			r.text:SetTextColor(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
			r.arrow:Show()
			local has = false
			for _, it in ipairs(e.group.items) do if it[1] == cur then has = true end end
			if has then r.sel:Show() else r.sel:Hide() end
		else
			r.text:SetTextColor(unpack(COLORS.text))
			r.arrow:Hide()
			if e.value == cur then r.sel:Show() else r.sel:Hide() end
		end
		r:SetScript("OnEnter", function(self)
			if f.level == 1 then
				if self.entry.group then
					local items = {}
					for _, it in ipairs(self.entry.group.items) do items[#items + 1] = { value = it[1], text = it[2], mark = it[3] } end
					sub = sub or MenuFrame(2)
					FillMenu(sub, items, owner, width)
					sub:ClearAllPoints()
					sub:SetPoint("TOPLEFT", self, "TOPRIGHT", 6, 4)
					sub:Show()
				elseif sub then
					sub:Hide()
				end
			end
		end)
		r:SetScript("OnClick", function(self)
			if self.entry.group then return end
			CloseMenus()
			owner.setter(self.entry.value)
			owner:Refresh()
		end)
		r:Show()
	end
	f:SetSize(width, #entries * ROW_H + 8)
end

function UI.Dropdown(parent, w, build, getter, setter, tooltip)
	local b = UI.Button(parent, "", w, 24, nil, tooltip)
	b.label:ClearAllPoints()
	b.label:SetPoint("LEFT", 8, 0)
	b.label:SetPoint("RIGHT", -18, 0)
	b.label:SetJustifyH("LEFT")
	local arrow = UI.Text(b, "v", 11, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], "RIGHT")
	arrow:SetPoint("RIGHT", -6, 0)
	b.getter, b.setter, b.build = getter, setter, build
	b:SetScript("OnClick", function(self)
		if menu and menu:IsShown() and menu.owner == self then CloseMenus() return end
		menu = menu or MenuFrame(1)
		menu.owner = self
		local entries = {}
		for _, g in ipairs(self.build()) do
			if g.text then
				if g.items[1] then entries[#entries + 1] = { text = g.text, group = g } end
			else
				for _, it in ipairs(g.items) do entries[#entries + 1] = { value = it[1], text = it[2], mark = it[3] } end
			end
		end
		if sub then sub:Hide() end
		FillMenu(menu, entries, self, math.max(w, 180))
		menu:ClearAllPoints()
		menu:SetPoint("TOPLEFT", self, "BOTTOMLEFT", 0, -2)
		menu:Show()
	end)
	-- Menü schließen, wenn die Maus es länger verlässt oder die Seite verschwindet
	b:HookScript("OnHide", function(self) if menu and menu.owner == self then CloseMenus() end end)
	function b:Refresh()
		local cur = getter()
		for _, g in ipairs(self.build()) do
			for _, it in ipairs(g.items) do
				if it[1] == cur then self:SetText(it[2]) return end
			end
		end
		self:SetText(tostring(cur or ""))
	end
	b:Refresh()
	return b
end

do
	local idle = 0
	local watcher = CreateFrame("Frame")
	watcher:SetScript("OnUpdate", function(_, dt)
		if not (menu and menu:IsShown()) then idle = 0 return end
		local over = menu:IsMouseOver() or (sub and sub:IsShown() and sub:IsMouseOver()) or (menu.owner and menu.owner:IsMouseOver())
		if over then idle = 0 else idle = idle + (dt or 0) end
		if idle > 1.5 then CloseMenus() end
	end)
end

-- Raids nach WoW-Erweiterung für das Aufklappmenü der DKP-Töpfe.
-- withAll: zusätzlicher Eintrag "Alle Raids"; Raids mit DKP-Ständen bekommen einen Punkt
function UI.PoolGroups(data, withAll)
	local Data, DKP = RM.Data, RM.DKP
	data = data or RM.db.data
	local used = {}
	for _, p in pairs(data.players or {}) do
		for key, v in pairs(p.d or {}) do if v ~= 0 then used[key] = true end end
	end
	local groups = {}
	if withAll then groups[#groups + 1] = { items = { { "__all", L["Alle Raids"] } } } end
	local seen = {}
	for _, x in ipairs(Data.Expansions) do
		local items = {}
		for _, def in ipairs(Data.RaidList) do
			local exp = (RM.GAME.key == "forever" and def.key == "hyjal") and "custom" or def.exp
			if exp == x.key then
				items[#items + 1] = { def.key, def.name, used[def.key] }
				seen[def.key] = true
			end
		end
		if items[1] then groups[#groups + 1] = { text = x.name, items = items } end
	end
	local other = {}
	for _, key in ipairs(DKP.PoolList(data)) do
		if not seen[key] then other[#other + 1] = { key, DKP.PoolName(key, data), used[key] }; seen[key] = true end
	end
	if other[1] then groups[#groups + 1] = { text = L["Weitere Raids"], items = other } end
	return groups
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
	local headBg = L:CreateTexture(nil, "BACKGROUND")
	headBg:SetColorTexture(1, 1, 1, 0.035)
	headBg:SetPoint("TOPLEFT", 1, -1)
	headBg:SetPoint("TOPRIGHT", -1, -1)
	headBg:SetHeight(23)
	local sep = L:CreateTexture(nil, "ARTWORK")
	sep:SetColorTexture(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 0.3)
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
-- Wer sieht welche Seite:
--   alle Teilnehmer: DKP-Stände und Versteigerung (bieten)
--   Raidleiter/Co-Raidleiter und Offiziere: alle Raid-Seiten
--   Einstellungen: nur Offiziere
UI.PAGE_ACCESS = { dkp = "all", auction = "all", settings = "officer" }

function UI.IsRaidLead()
	local grouped = RM.InRaid() or (IsInGroup and IsInGroup())
	return grouped and RM.IsAssist() and true or false
end

function UI.CanSeePage(id)
	local access = UI.PAGE_ACCESS[id] or "lead"
	if access == "all" then return true end
	if RM.CanEdit() then return true end
	if access == "lead" then return UI.IsRaidLead() end
	return false
end

function UI.AddPage(id, title, build)
	UI.pages[id] = { id = id, title = title, build = build }
	UI.pageOrder[#UI.pageOrder + 1] = id
end

local main

-- Symbole der Seiten in der Navigation (alle in jeder WoW-Version vorhanden)
UI.PAGE_ICONS = {
	dkp = "Interface\\Icons\\INV_Misc_Coin_01", auction = "Interface\\Icons\\INV_Hammer_15",
	loot = "Interface\\Icons\\INV_Box_01", log = "Interface\\Icons\\INV_Misc_Note_01",
	raid = "Interface\\Icons\\Ability_Warrior_BattleShout", signup = "Interface\\Icons\\INV_Scroll_03",
	pug = "Interface\\Icons\\Spell_Holy_PrayerOfHealing02", ad = "Interface\\Icons\\INV_Scroll_05",
	assign = "Interface\\Icons\\Ability_Warrior_DefensiveStance", leader = "Interface\\Icons\\INV_Misc_Head_Dragon_01",
	specs = "Interface\\Icons\\INV_Misc_Book_11", settings = "Interface\\Icons\\INV_Misc_Gear_01",
}

-- Eintrag der Navigation: Symbol, Text, Akzentbalken links für die aktive Seite
function UI.NavButton(parent, text, icon, onClick)
	local b = CreateFrame("Button", nil, parent)
	b:SetSize(158, 34)
	b.bg = b:CreateTexture(nil, "BACKGROUND")
	b.bg:SetAllPoints()
	b.bg:SetColorTexture(1, 1, 1, 0)
	local hl = b:CreateTexture(nil, "HIGHLIGHT")
	hl:SetAllPoints()
	hl:SetColorTexture(1, 1, 1, 0.05)
	b.bar = b:CreateTexture(nil, "ARTWORK")
	b.bar:SetPoint("TOPLEFT", 0, -4)
	b.bar:SetPoint("BOTTOMLEFT", 0, 4)
	b.bar:SetWidth(3)
	b.bar:SetColorTexture(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 1)
	b.bar:Hide()
	b.icon = b:CreateTexture(nil, "ARTWORK")
	b.icon:SetSize(22, 22)
	b.icon:SetPoint("LEFT", 12, 0)
	b.icon:SetTexture(icon or "Interface\\Icons\\INV_Misc_QuestionMark")
	b.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	b.label = UI.Text(b, text, 13, COLORS.muted[1], COLORS.muted[2], COLORS.muted[3])
	b.label:SetPoint("LEFT", b.icon, "RIGHT", 10, 0)
	b.label:SetPoint("RIGHT", -6, 0)
	b.label:SetWordWrap(false)
	b:SetScript("OnClick", onClick)
	function b:SetAccent(on)
		if on then
			self.bar:Show()
			self.bg:SetColorTexture(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 0.12)
			self.label:SetTextColor(1, 1, 1)
			self.icon:SetDesaturated(false)
			self.icon:SetAlpha(1)
		else
			self.bar:Hide()
			self.bg:SetColorTexture(1, 1, 1, 0)
			self.label:SetTextColor(unpack(COLORS.muted))
			self.icon:SetAlpha(0.75)
		end
	end
	b:SetAccent(false)
	return b
end

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

-- Navigation: nur erlaubte Seiten, lückenlos untereinander
local function UpdateNav()
	if not main then return end
	local y = -10
	for _, pid in ipairs(UI.pageOrder) do
		local p = UI.pages[pid]
		if p.nav then
			if UI.CanSeePage(pid) then
				p.nav:ClearAllPoints()
				p.nav:SetPoint("TOPLEFT", main.nav, "TOPLEFT", 6, y)
				p.nav:Show()
				y = y - 40
			else
				p.nav:Hide()
			end
		end
	end
	if main.current and not UI.CanSeePage(main.current) then
		main.current = nil
		UI.ShowPage(UI.pageOrder[1])
	end
end
UI.UpdateNav = UpdateNav

function UI.ShowPage(id)
	if not main then return end
	if not UI.CanSeePage(id) then id = UI.pageOrder[1] end
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
	UpdateNav()
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
	tbg:SetColorTexture(0.085, 0.06, 0.04, 1)
	local tshade = titleBar:CreateTexture(nil, "BACKGROUND", nil, 1)
	tshade:SetPoint("TOPLEFT")
	tshade:SetPoint("TOPRIGHT")
	tshade:SetHeight(20)
	tshade:SetColorTexture(1, 0.7, 0.4, 0.04)
	local tline = titleBar:CreateTexture(nil, "ARTWORK")
	tline:SetPoint("BOTTOMLEFT")
	tline:SetPoint("BOTTOMRIGHT")
	tline:SetHeight(1)
	tline:SetColorTexture(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 0.6)
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
	f.nav = nav
	nav:SetPoint("TOPLEFT", 0, -40)
	nav:SetPoint("BOTTOMLEFT", 0, 26)
	local nbg = nav:CreateTexture(nil, "BACKGROUND")
	nbg:SetAllPoints()
	nbg:SetColorTexture(0.06, 0.064, 0.078, 1)
	local nline = nav:CreateTexture(nil, "ARTWORK")
	nline:SetPoint("TOPRIGHT")
	nline:SetPoint("BOTTOMRIGHT")
	nline:SetWidth(1)
	nline:SetColorTexture(COLORS.border[1], COLORS.border[2], COLORS.border[3], 1)

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
	local y = -10
	for _, id in ipairs(UI.pageOrder) do
		local p = UI.pages[id]
		local b = UI.NavButton(nav, p.title, UI.PAGE_ICONS[id], function() UI.ShowPage(id) end)
		b:SetPoint("TOPLEFT", 6, y)
		p.nav = b
		y = y - 40
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
