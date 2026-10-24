-- RaidMaster - Seiten des Hauptfensters
-- DKP, Versteigerung, Loot, Log, Raid, Raidleiter, Einstellungen

local ADDON, RM = ...
local UI = RM.UI
local COLORS = UI.COLORS

local function Place(w, parent, x, y)
	w:ClearAllPoints()
	w:SetPoint("TOPLEFT", parent, "TOPLEFT", x, y)
	return w
end

local function Label(parent, text, x, y, size, muted)
	local fs
	if muted then
		fs = UI.Text(parent, text, size or 12, COLORS.muted[1], COLORS.muted[2], COLORS.muted[3])
	else
		fs = UI.Text(parent, text, size or 12)
	end
	return Place(fs, parent, x, y)
end

local function Section(parent, text, x, y)
	local h = UI.Header(parent, text)
	return Place(h, parent, x, y)
end

local function ClassName(class)
	return (class and LOCALIZED_CLASS_NAMES_MALE and LOCALIZED_CLASS_NAMES_MALE[class]) or class or ""
end

local function NeedOfficer()
	if RM.CanEdit() then return true end
	RM.Print("Dafür brauchst du Offiziersrechte.")
	return false
end

local function CapName(name)
	name = (name or ""):gsub("%s", "")
	if name == "" then return "" end
	return name:sub(1, 1):upper() .. name:sub(2):lower()
end

-- Auswahl der angezeigten DKP-Tabelle (eigene Gilde oder Raid-Gilde)
local function ViewCycle(page, x, y)
	local opts = {}
	local function Rebuild()
		wipe(opts)
		local own = RM.MyGuild()
		opts[#opts + 1] = { "__own", own and ("Gilde: " .. own) or "Eigene Daten" }
		for g in pairs(RM.db.foreign) do opts[#opts + 1] = { g, "Raid: " .. g } end
	end
	Rebuild()
	local cyc = UI.Cycle(page, 220, opts, function() return UI.viewGuild or "__own" end, function(v)
		if v == "__own" then UI.viewGuild = nil else UI.viewGuild = v end
		UI.RefreshCurrent()
	end, "Wechselt zwischen der eigenen Gilde und der DKP-Tabelle der Gilde, mit der du gerade raidest.")
	Place(cyc, page, x, y)
	function cyc:Update()
		Rebuild()
		if UI.viewGuild and not RM.db.foreign[UI.viewGuild] then UI.viewGuild = nil end
		if #opts > 1 then self:Show() else self:Hide() end
		self:Refresh()
	end
	return cyc
end

-- Auswahl des DKP-Topfes (Raid), gemeinsam für DKP- und Log-Seite
-- withAll = zusätzliche Option "Alle Raids"
local function PoolCycle(page, x, y, width, withAll)
	local opts = {}
	local function Rebuild()
		wipe(opts)
		local data = RM.DKP.View()
		if withAll then opts[#opts + 1] = { "__all", "Alle Raids" } end
		for _, key in ipairs(RM.DKP.PoolList(data)) do
			opts[#opts + 1] = { key, "Raid: " .. RM.DKP.PoolName(key, data) }
		end
	end
	Rebuild()
	local cyc = UI.Cycle(page, width or 220, opts, function()
		if withAll and UI.logAllPools then return "__all" end
		return UI.viewPool or RM.DKP.DefaultViewPool()
	end, function(v)
		if v == "__all" then
			UI.logAllPools = true
		else
			UI.logAllPools = false
			UI.viewPool = v
		end
		UI.RefreshCurrent()
	end, "Jeder Raid hat einen eigenen DKP-Topf. Hier wählst du, welchen du siehst.")
	Place(cyc, page, x, y)
	function cyc:Update()
		Rebuild()
		self:Refresh()
	end
	return cyc
end

-- Aktuell angezeigter Topf
local function ViewPool()
	return UI.viewPool or RM.DKP.DefaultViewPool()
end

---------------------------------------------------------------------------
-- Seite: DKP-Stände
---------------------------------------------------------------------------
UI.AddPage("dkp", "DKP-Stände", function(page)
	local sortKey, sortDesc = "dkp", true
	local onlyRaid = false
	local selected

	Section(page, "DKP-Stände", 0, 0)
	local poolCycle = PoolCycle(page, 120, 4, 240)

	local search = UI.EditBox(page, 180, 24)
	Place(search, page, 0, -30)
	local searchHint = UI.Text(search, "Suchen ...", 11, unpack(COLORS.muted))
	searchHint:SetPoint("LEFT", 8, 0)

	local raidCheck = UI.Check(page, "Nur Raid", function() return onlyRaid end, function(v) onlyRaid = v; UI.RefreshCurrent() end)
	Place(raidCheck, page, 196, -33)

	local syncBtn = UI.Button(page, "Sync anfordern", 120, 24, function() RM.Comm.RequestSync() end,
		"Fragt Offiziere nach dem neuesten DKP-Stand.")
	Place(syncBtn, page, 316, -30)

	local exportBtn = UI.Button(page, "Export", 80, 24, function() UI.ShowExport(RM.DKP.ExportText()) end)
	Place(exportBtn, page, 442, -30)

	local viewCycle = ViewCycle(page, 560, -30)

	local list
	list = UI.List(page, 540, 490, {
		{ title = "Name", width = 170 },
		{ title = "Klasse", width = 100 },
		{ title = "DKP", width = 70, justify = "RIGHT" },
		{ title = "Status", width = 150 },
	}, {
		emptyText = "Noch keine DKP-Daten. Als Offizier: Raid starten oder Spieler hinzufügen.",
		onSort = function(col)
			local key = ({ "name", "class", "dkp", "status" })[col]
			if sortKey == key then sortDesc = not sortDesc else sortKey = key; sortDesc = (key == "dkp") end
			UI.RefreshCurrent()
		end,
		onSelect = function(d) selected = d.key; UI.RefreshCurrent() end,
	})
	Place(list, page, 0, -64)

	-- Offiziersbereich
	local px = 560
	Section(page, "Buchung", px, -64)
	local selLabel = Label(page, "Kein Spieler gewählt", px, -90)
	selLabel:SetWidth(220)

	Label(page, "Betrag (+/-)", px, -118, 11, true)
	local amountBox = UI.EditBox(page, 80, 24, true)
	Place(amountBox, page, px, -134)

	Label(page, "Grund", px, -164, 11, true)
	local reasonBox = UI.EditBox(page, 220, 24)
	Place(reasonBox, page, px, -180)

	local bookBtn = UI.Button(page, "Buchen", 105, 26, function()
		if not NeedOfficer() then return end
		if not selected then RM.Print("Bitte zuerst einen Spieler wählen.") return end
		local amount = tonumber(amountBox:GetText())
		if not amount or amount == 0 then RM.Print("Bitte einen Betrag eingeben, z. B. 10 oder -5.") return end
		local reason = reasonBox:GetText()
		local pool = ViewPool()
		UI.Confirm(string.format("%s %+d %s-DKP buchen?\nGrund: %s", selected, amount, RM.DKP.PoolName(pool), reason ~= "" and reason or "Manuelle Anpassung"), function()
			RM.DKP.Adjust(selected, amount, reason, pool)
			amountBox:SetText("")
			reasonBox:SetText("")
		end)
	end)
	Place(bookBtn, page, px, -214)
	bookBtn:SetAccent(true)

	local standbyBtn = UI.Button(page, "Ersatzbank an/aus", 110, 26, function()
		if not selected then RM.Print("Bitte zuerst einen Spieler wählen.") return end
		RM.DKP.ToggleStandby(selected)
	end, "Spieler auf der Ersatzbank erhalten bei Raid-Buchungen ebenfalls DKP (einstellbar).")
	Place(standbyBtn, page, px + 110, -214)

	Section(page, "Spieler hinzufügen", px, -260)
	local addBox = UI.EditBox(page, 140, 24)
	Place(addBox, page, px, -286)
	local addBtn = UI.Button(page, "Hinzufügen", 76, 24, function()
		if not NeedOfficer() then return end
		local name = RM.DKP.AddPlayer(addBox:GetText())
		if name then addBox:SetText(""); RM.Print(name .. " hinzugefügt.") end
	end)
	Place(addBtn, page, px + 144, -286)

	local myInfo = Label(page, "", px, -330, 12)
	myInfo:SetWidth(220)
	local help = Label(page, "Spieler ohne Addon können ihren Stand per Flüstern abfragen: /w <Plündermeister> !dkp", px, -380, 11, true)
	help:SetWidth(220)

	search:SetScript("OnTextChanged", function(self)
		if self:GetText() == "" then searchHint:Show() else searchHint:Hide() end
		UI.RefreshCurrent()
	end)

	local officerWidgets = { bookBtn, standbyBtn, addBtn }

	return function()
		viewCycle:Update()
		poolCycle:Update()
		local data, isMain = RM.DKP.View()
		local pool = ViewPool()
		local poolName = RM.DKP.PoolName(pool, data)
		local filter = search:GetText():lower()
		local raidSet = {}
		for _, m in ipairs(RM.RaidMembers()) do raidSet[m.name] = m end
		local rows = {}
		local names = {}
		for name in pairs(data.players) do names[name] = true end
		if onlyRaid then
			for name in pairs(raidSet) do names[name] = true end
		end
		for name in pairs(names) do
			local p = data.players[name] or { d = {} }
			local value = RM.DKP.PoolValue(p, pool)
			local inRaid = raidSet[name]
			local standby = RM.DKP.IsStandby(name)
			if (not onlyRaid or inRaid or standby) and (filter == "" or name:lower():find(filter, 1, true)) then
				local class = p.c or (inRaid and inRaid.class) or RM.guild.class[name]
				local status = inRaid and "Im Raid" or (standby and "Ersatzbank" or "")
				local dkpColor = value < 0 and { 1, 0.35, 0.35 } or nil
				rows[#rows + 1] = {
					key = name, name = name, class = class or "", dkp = value, status = status,
					cells = { RM.ClassColor(class, name), ClassName(class), tostring(value), status },
					colors = { nil, { 0.75, 0.75, 0.75 }, dkpColor, inRaid and { 0.5, 1, 0.5 } or { 1, 0.8, 0.3 } },
				}
			end
		end
		table.sort(rows, function(a, b)
			local x, y = a[sortKey], b[sortKey]
			if x == y then return a.name < b.name end
			if sortDesc then return x > y end
			return x < y
		end)
		list:SetData(rows)

		local function dkpOf(n) return RM.DKP.PoolValue(data.players[n], pool) end
		if selected then
			selLabel:SetText("Gewählt: " .. selected .. " (" .. dkpOf(selected) .. " " .. poolName .. "-DKP)" .. (RM.DKP.IsStandby(selected) and " – Ersatzbank" or ""))
		else
			selLabel:SetText("Kein Spieler gewählt")
		end
		if isMain then
			myInfo:SetText(string.format("Deine DKP: |cffff8c1a%s|r", RM.DKP.Summary(RM.Me(), data)))
		else
			myInfo:SetText(string.format("Deine DKP bei <%s>: |cffff8c1a%s|r\n|cff999999Nur Ansicht – Quelle: %s, Stand %s|r",
				UI.viewGuild, RM.DKP.Summary(RM.Me(), data), data.source or "?", data.received and RM.FormatTime(data.received) or "?"))
		end
		local canEdit = RM.CanEdit() and isMain
		for _, w in ipairs(officerWidgets) do
			if canEdit then w:Enable() else w:Disable() end
		end
	end
end)

---------------------------------------------------------------------------
-- Seite: Versteigerung
---------------------------------------------------------------------------
UI.AddPage("auction", "Versteigerung", function(page)
	Section(page, "Laufende Versteigerung", 0, 0)

	local box = UI.Frame(page, 790, 92)
	UI.Skin(box, COLORS.panel)
	Place(box, page, 0, -26)

	local itemText = UI.Text(box, "", 15)
	itemText:SetPoint("TOPLEFT", 12, -12)
	itemText:SetWidth(460)
	itemText:SetWordWrap(false)
	local infoText = UI.Text(box, "", 12, unpack(COLORS.muted))
	infoText:SetPoint("TOPLEFT", 12, -38)
	infoText:SetWidth(460)

	local itemHover = CreateFrame("Frame", nil, box)
	itemHover:SetPoint("TOPLEFT", itemText, "TOPLEFT")
	itemHover:SetSize(460, 20)
	itemHover:EnableMouse(true)
	itemHover:SetScript("OnEnter", function(self)
		local link = RM.Auction.current and RM.Auction.current.link or (RM.Auction.client and RM.Auction.client.link)
		if link then
			GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
			GameTooltip:SetHyperlink(RM.ItemString(link) or link)
			GameTooltip:Show()
		end
	end)
	itemHover:SetScript("OnLeave", function() GameTooltip:Hide() end)

	local finishBtn = UI.Button(box, "Jetzt beenden", 110, 26, function() RM.Auction.FinishNow() end)
	finishBtn:SetPoint("TOPRIGHT", -12, -12)
	local addBtn = UI.Button(box, "+10 Sek.", 80, 26, function() RM.Auction.AddTime(10) end)
	addBtn:SetPoint("RIGHT", finishBtn, "LEFT", -6, 0)
	local cancelBtn = UI.Button(box, "Abbrechen", 100, 26, function()
		UI.Confirm("Versteigerung abbrechen? Das Item kommt zurück in die Warteschlange.", function() RM.Auction.Cancel() end)
	end)
	cancelBtn:SetPoint("TOPRIGHT", -12, -46)
	local bidOpenBtn = UI.Button(box, "Gebotsfenster", 110, 26, function() RM.Auction.ShowBidFrame() end, "Öffnet das Gebotsfenster erneut.")
	bidOpenBtn:SetPoint("RIGHT", cancelBtn, "LEFT", -6, 0)

	local bidList = UI.List(page, 790, 190, {
		{ title = "Bieter", width = 150 },
		{ title = "Gebot", width = 70, justify = "RIGHT" },
		{ title = "DKP", width = 70, justify = "RIGHT" },
		{ title = "Trägt aktuell", width = 450 },
	}, { emptyText = "Noch keine Gebote." })
	Place(bidList, page, 0, -126)

	Section(page, "Warteschlange", 0, -326)
	local queueList
	queueList = UI.List(page, 520, 196, {
		{ title = "#", width = 24 },
		{ title = "Item", width = 460 },
	}, { emptyText = "Leer. Epische Items kommen beim Öffnen des Bosses automatisch hierher." })
	Place(queueList, page, 0, -352)

	local qx = 536
	local startBtn = UI.Button(page, "Gewähltes starten", 160, 28, function()
		local d = queueList:Selected()
		if not d then
			if #RM.Auction.queue > 0 then RM.Auction.Start(1) else RM.Print("Die Warteschlange ist leer.") end
			return
		end
		RM.Auction.Start(d.index)
		queueList:ClearSelection()
	end, "Startet das gewählte Item (ohne Auswahl das erste).")
	Place(startBtn, page, qx, -352)
	startBtn:SetAccent(true)

	local removeBtn = UI.Button(page, "Entfernen", 160, 26, function()
		local d = queueList:Selected()
		if d then RM.Auction.Remove(d.index); queueList:ClearSelection() end
	end)
	Place(removeBtn, page, qx, -386)

	Label(page, "Item hinzufügen (Shift-Klick auf ein Item):", qx, -426, 11, true):SetWidth(250)
	local linkBox = UI.LinkBox(page, 250, 24)
	Place(linkBox, page, qx, -458)
	local addItemBtn = UI.Button(page, "Zur Warteschlange", 160, 26, function()
		local link = linkBox:GetText()
		if link and link:find("item:") then
			RM.Auction.Enqueue(link)
			linkBox:SetText("")
		else
			RM.Print("Bitte zuerst einen Itemlink per Shift-Klick einfügen.")
		end
	end)
	Place(addItemBtn, page, qx, -488)
	local directBtn = UI.Button(page, "Sofort versteigern", 160, 26, function()
		local link = linkBox:GetText()
		if link and link:find("item:") then
			RM.Auction.Start(link)
			linkBox:SetText("")
		else
			RM.Print("Bitte zuerst einen Itemlink per Shift-Klick einfügen.")
		end
	end)
	Place(directBtn, page, qx, -518)

	local function UpdateInfo()
		local c = RM.Auction.current
		local cl = RM.Auction.client
		if c then
			itemText:SetText(c.link)
			local rem = math.max(0, math.ceil(c.endsAt - GetTime()))
			local high = c.highName and string.format("%d DKP (%s)", c.high, c.highName) or "noch keins"
			if c.finished then
				infoText:SetText("Beendet – wartet auf Bestätigung. Höchstgebot: " .. high)
			else
				infoText:SetText(string.format("Restzeit: %d Sek.  ·  Mindestgebot: %d  ·  Schritt: %d  ·  Höchstgebot: %s", rem, c.min, c.inc, high))
			end
		elseif cl and not cl.ended then
			itemText:SetText(cl.link)
			local rem = math.max(0, math.ceil(cl.endsAt - GetTime()))
			local high = cl.highName and string.format("%d DKP (%s)", cl.high, cl.highName) or "noch keins"
			infoText:SetText(string.format("Plündermeister: %s  ·  Restzeit: %d Sek.  ·  Höchstgebot: %s", cl.ml, rem, high))
		else
			itemText:SetText("|cff888888Keine laufende Versteigerung|r")
			infoText:SetText(RM.CanEdit() and "Wähle ein Item aus der Warteschlange oder füge eines per Shift-Klick hinzu." or "Sobald der Plündermeister ein Item versteigert, öffnet sich das Gebotsfenster.")
		end
	end

	page.elapsed = 0
	page:SetScript("OnUpdate", function(self, el)
		self.elapsed = self.elapsed + el
		if self.elapsed > 0.5 then self.elapsed = 0; UpdateInfo() end
	end)

	return function()
		UpdateInfo()
		local c = RM.Auction.current
		local running = c and not c.finished
		local canRun = RM.CanEdit()
		if running then finishBtn:Enable(); addBtn:Enable(); cancelBtn:Enable() else finishBtn:Disable(); addBtn:Disable(); cancelBtn:Disable() end
		if RM.Auction.client and not RM.Auction.client.ended then bidOpenBtn:Enable() else bidOpenBtn:Disable() end
		for _, b in ipairs({ startBtn, removeBtn, addItemBtn, directBtn }) do
			if canRun then b:Enable() else b:Disable() end
		end

		local rows = {}
		for _, b in ipairs(RM.Auction.BidList()) do
			local gear = b.gear or ""
			local gearLinks = {}
			for l in gear:gmatch("|c%x+|Hitem:.-|h.-|h|r") do gearLinks[#gearLinks + 1] = l end
			rows[#rows + 1] = {
				key = b.name,
				cells = { b.name, b.pass and "Passt" or tostring(b.amount), tostring(RM.DKP.Get(b.name, RM.Auction.current and RM.Auction.current.pool)), table.concat(gearLinks, "  ") },
				colors = { nil, b.pass and { 0.6, 0.6, 0.6 } or { 1, 0.8, 0.3 } },
				tooltip = (#gearLinks > 0) and function(tt)
					tt:SetHyperlink(RM.ItemString(gearLinks[1]) or gearLinks[1])
				end or nil,
			}
		end
		bidList:SetData(rows)

		local qrows = {}
		for i, q in ipairs(RM.Auction.queue) do
			qrows[#qrows + 1] = { key = i .. q.link, index = i, link = q.link, cells = { tostring(i), q.link } }
		end
		queueList:SetData(qrows)
	end
end)

---------------------------------------------------------------------------
-- Seite: Loot
---------------------------------------------------------------------------
UI.AddPage("loot", "Loot", function(page)
	local cfg = function() return RM.db.config end
	local refreshers = {}

	Section(page, "Loot-Regeln", 0, 0)
	local rules = {
		{ key = "epic", label = "Epische Ausrüstung", opts = { { "auction", "Versteigerung" }, { "manual", "Manuell" } } },
		{ key = "blue", label = "Blaue Ausrüstung", opts = { { "auction", "Versteigerung" }, { "de", "Entzauberer" }, { "bank", "Gildenbank" }, { "manual", "Manuell" } } },
		{ key = "recipe", label = "Rezepte und Pläne", opts = { { "bank", "Gildenbank" }, { "crafter", "Handwerker" }, { "auction", "Versteigerung" }, { "manual", "Manuell" } } },
		{ key = "mats", label = "Handwerksmaterialien", opts = { { "bank", "Gildenbank" }, { "crafter", "Handwerker" }, { "auction", "Versteigerung" }, { "manual", "Manuell" } } },
	}
	local y = -28
	for _, r in ipairs(rules) do
		Label(page, r.label, 0, y - 5)
		local cyc = UI.Cycle(page, 150, r.opts, function() return cfg().rules[r.key] end, function(v) cfg().rules[r.key] = v end)
		Place(cyc, page, 170, y)
		refreshers[#refreshers + 1] = cyc
		y = y - 30
	end
	Label(page, "Legendäre Items", 0, y - 5)
	Label(page, "immer nur Hinweis", 170, y - 5, 12, true)
	y = y - 30
	Label(page, "Keine Gebote", 0, y - 5)
	local fb = UI.Cycle(page, 150, { { "de", "Entzauberer" }, { "bank", "Gildenbank" }, { "manual", "Manuell" } },
		function() return cfg().fallback end, function(v) cfg().fallback = v end)
	Place(fb, page, 170, y)
	refreshers[#refreshers + 1] = fb
	y = y - 40

	Section(page, "Empfänger", 0, y)
	y = y - 28
	local function NameField(label, key, yy)
		Label(page, label, 0, yy - 5)
		local e = UI.EditBox(page, 150, 24)
		Place(e, page, 170, yy)
		e:SetScript("OnTextChanged", function(self, user) if user then cfg()[key] = CapName(self:GetText()) end end)
		e:SetScript("OnEditFocusLost", function(self)
			self:SetBackdropBorderColor(unpack(COLORS.border))
			self:SetText(cfg()[key] or "")
		end)
		refreshers[#refreshers + 1] = { Refresh = function() if not e:HasFocus() then e:SetText(cfg()[key] or "") end end }
		return e
	end
	NameField("Gildenbank-Charakter", "bankChar", y); y = y - 30
	NameField("Entzauberer", "deChar", y); y = y - 30
	NameField("Handwerker", "crafterChar", y); y = y - 40

	Section(page, "Plündermeister", 0, y)
	y = y - 28
	NameField("Name (leer = du selbst)", "lootMaster", y); y = y - 30
	Label(page, "Plünderschwelle", 0, y - 5)
	local th = UI.Cycle(page, 150, { { 2, "Selten (grün)" }, { 3, "Rar (blau)" }, { 4, "Episch (lila)" } },
		function() return cfg().lootThreshold end, function(v) cfg().lootThreshold = v end,
		"In Molten Core sind Kerne und Rezepte blau – daher wird Rar empfohlen.")
	Place(th, page, 170, y)
	refreshers[#refreshers + 1] = th
	y = y - 32
	local applyBtn = UI.Button(page, "Jetzt anwenden", 150, 26, function() RM.Loot.ApplySettings() end, "Setzt Plündermeister und Schwelle (nur Raidleiter).")
	Place(applyBtn, page, 170, y)

	-- Optionen
	local ox = 350
	Section(page, "Optionen", ox, 0)
	local checks = {
		{ "setLootOnStart", "Loot-Einstellungen bei Raidstart setzen" },
		{ "autoDistribute", "Mats/Rezepte/Blaues automatisch zuteilen" },
		{ "announceLoot", "Loot gesammelt im Raidchat ansagen" },
		{ "autoNext", "Nächste Versteigerung automatisch starten" },
		{ "announceBids", "Gebote im Raidchat ansagen" },
		{ "unlootedReminder", "Erinnern, wenn Boss nicht geplündert" },
		{ "tradeFallback", "Bei Abwesenheit an mich + Handelsliste" },
		{ "whisperReplies", "Auf !dkp-Flüstern antworten" },
	}
	local cy = -30
	for _, c in ipairs(checks) do
		local cb = UI.Check(page, c[2], function() return cfg()[c[1]] end, function(v) cfg()[c[1]] = v end)
		Place(cb, page, ox, cy)
		refreshers[#refreshers + 1] = cb
		cy = cy - 26
	end

	Section(page, "Offene Zuteilungen und Handel", ox, -248)
	local openList = UI.List(page, 440, 160, {
		{ title = "Item", width = 200 },
		{ title = "Spieler", width = 90 },
		{ title = "Art", width = 120 },
	}, { emptyText = "Nichts offen." })
	Place(openList, page, ox, -274)
	local removeOpen = UI.Button(page, "Entfernen", 100, 24, function()
		local d = openList:Selected()
		if not d then return end
		if d.kind == "trade" then
			RM.Loot.RemoveTrade(d.index)
		else
			table.remove(RM.db.pendingAwards, d.index)
			RM.Fire("LOOT_CHANGED")
		end
		openList:ClearSelection()
	end)
	Place(removeOpen, page, ox, -440)
	Label(page, "Handel: Öffne einfach ein Handelsfenster mit dem Spieler – seine Items werden automatisch eingelegt.", ox + 108, -440, 11, true):SetWidth(330)

	Section(page, "Aktuelles Lootfenster", ox, -480)
	local lootInfo = Label(page, "", ox, -504, 11, true)
	lootInfo:SetWidth(440)

	return function()
		for _, r in ipairs(refreshers) do r:Refresh() end
		local rows = {}
		for i, p in ipairs(RM.db.pendingAwards) do
			rows[#rows + 1] = { key = "p" .. i .. p.link, kind = "pending", index = i, link = p.link, cells = { p.link, p.name, "Boss erneut öffnen" }, colors = { nil, nil, { 1, 0.8, 0.3 } } }
		end
		for i, t in ipairs(RM.db.trade) do
			rows[#rows + 1] = { key = "t" .. i .. t.link, kind = "trade", index = i, link = t.link, cells = { t.link, t.name, "Handeln" }, colors = { nil, nil, { 0.5, 0.8, 1 } } }
		end
		openList:SetData(rows)

		if RM.Loot.isOpen and #RM.Loot.items > 0 then
			local parts = {}
			for _, it in ipairs(RM.Loot.items) do
				parts[#parts + 1] = it.link .. " – " .. (RM.Loot.ActionNames[it.action] or it.action) .. (it.done and " (erledigt)" or "")
			end
			lootInfo:SetText(table.concat(parts, "\n"))
		elseif RM.Loot.isOpen then
			lootInfo:SetText("Geöffnet – keine Items über der Schwelle.")
		else
			lootInfo:SetText("Kein Lootfenster geöffnet.")
		end
	end
end)

---------------------------------------------------------------------------
-- Seite: Log
---------------------------------------------------------------------------
UI.AddPage("log", "Log", function(page)
	local filterKind = "all"
	Section(page, "Buchungsprotokoll", 0, 0)
	local poolCycle = PoolCycle(page, 180, 4, 240, true)

	local filter = UI.Cycle(page, 150, {
		{ "all", "Alle Buchungen" }, { "boss", "Bosskills" }, { "item", "Items" }, { "manual", "Anpassungen" },
		{ "raid", "Raidstart/-ende" }, { "decay", "Decay" }, { "undo", "Rückgängig" },
	}, function() return filterKind end, function(v) filterKind = v; UI.RefreshCurrent() end)
	Place(filter, page, 0, -28)

	local search = UI.EditBox(page, 160, 24)
	Place(search, page, 160, -28)
	local viewCycle = ViewCycle(page, 330, -28)
	local hint = UI.Text(search, "Spieler suchen ...", 11, unpack(COLORS.muted))
	hint:SetPoint("LEFT", 8, 0)
	search:SetScript("OnTextChanged", function(self)
		if self:GetText() == "" then hint:Show() else hint:Hide() end
		UI.RefreshCurrent()
	end)

	local list = UI.List(page, 790, 456, {
		{ title = "Zeit", width = 80 },
		{ title = "Von", width = 85 },
		{ title = "Raid", width = 64 },
		{ title = "Art", width = 74 },
		{ title = "Beschreibung", width = 266 },
		{ title = "Betrag", width = 70, justify = "RIGHT" },
		{ title = "Spieler", width = 70, justify = "RIGHT" },
	}, { emptyText = "Noch keine Buchungen." })
	Place(list, page, 0, -60)

	local undoBtn = UI.Button(page, "Rückgängig", 120, 26, function()
		if not NeedOfficer() then return end
		local d = list:Selected()
		if not d then RM.Print("Bitte zuerst eine Buchung wählen.") return end
		UI.Confirm("Diese Buchung rückgängig machen?\n" .. (d.desc or ""), function() RM.DKP.Undo(d.key) end)
	end, "Erstellt eine Gegenbuchung. Nichts wird gelöscht.")
	Place(undoBtn, page, 0, -526)

	local exportBtn = UI.Button(page, "Export", 100, 26, function() UI.ShowExport(RM.DKP.ExportText()) end)
	Place(exportBtn, page, 128, -526)

	return function()
		viewCycle:Update()
		poolCycle:Update()
		local data, isMain = RM.DKP.View()
		local poolFilter = (not UI.logAllPools) and ViewPool() or nil
		local q = search:GetText():lower()
		local rows = {}
		local log = data.log
		for i = #log, 1, -1 do
			local e = log[i]
			local epool = e.pool or "mc"
			local kindOK = (filterKind == "all" or e.k == filterKind or (filterKind == "raid" and (e.k == "start" or e.k == "end")))
				and (not poolFilter or epool == poolFilter)
			local nameOK = q == ""
			local count, amount, uniform = 0, nil, true
			local names = {}
			for name, d in pairs(e.d or {}) do
				count = count + 1
				if amount and amount ~= d then uniform = false end
				amount = amount or d
				names[#names + 1] = { name = name, d = d }
				if not nameOK and name:lower():find(q, 1, true) then nameOK = true end
			end
			if kindOK and nameOK then
				table.sort(names, function(a, b) return a.name < b.name end)
				local desc = e.x or ""
				if e.i then desc = desc .. " " .. e.i end
				if count == 1 then desc = names[1].name .. ": " .. desc end
				local grey = e.u and { 0.5, 0.5, 0.5 } or nil
				local amountColor = grey or ((amount or 0) < 0 and { 1, 0.4, 0.4 } or { 0.4, 1, 0.4 })
				rows[#rows + 1] = {
					key = e.id, desc = desc,
					cells = {
						date("%d.%m. %H:%M", e.t or 0), e.by or "", RM.DKP.PoolShort(epool, data), RM.DKP.KindNames[e.k] or e.k or "",
						desc .. (e.u and " (rückgängig)" or ""),
						count == 1 and string.format("%+d", amount or 0) or (uniform and string.format("%+d je", amount or 0) or "versch."),
						tostring(count),
					},
					colors = { grey, grey, grey, grey, grey, amountColor, grey },
					tooltip = function(tt)
						tt:AddLine((RM.DKP.KindNames[e.k] or e.k) .. " · " .. RM.DKP.PoolName(epool, data), 1, 0.55, 0.1)
						tt:AddLine(e.x or "", 1, 1, 1, true)
						if e.i then tt:AddLine(e.i) end
						tt:AddLine(" ")
						for n, entry in ipairs(names) do
							if n > 40 then tt:AddLine("...") break end
							tt:AddDoubleLine(entry.name, string.format("%+d", entry.d), 1, 1, 1, 1, 0.8, 0.3)
						end
					end,
				}
			end
		end
		list:SetData(rows)
		if RM.CanEdit() and isMain then undoBtn:Enable() else undoBtn:Disable() end
	end
end)

---------------------------------------------------------------------------
-- Seite: Raid
---------------------------------------------------------------------------
UI.AddPage("raid", "Raid", function(page)
	Section(page, "Raid-Sitzung", 0, 0)
	local sessionText = Label(page, "", 0, -28)
	sessionText:SetWidth(380)

	local startBtn = UI.Button(page, "Raid starten", 140, 30, function()
		if not NeedOfficer() then return end
		UI.Confirm("Raid starten?\nAlle Raidmitglieder (und die Ersatzbank) erhalten den Pünktlichkeitsbonus.", function() RM.Raid.Start() end)
	end)
	Place(startBtn, page, 0, -70)
	startBtn:SetAccent(true)

	local endBtn = UI.Button(page, "Raid beenden", 140, 30, function()
		UI.Confirm("Raid beenden?\nAlle Raidmitglieder (und die Ersatzbank) erhalten den Abschlussbonus.", function() RM.Raid.End() end)
	end)
	Place(endBtn, page, 150, -70)

	Label(page, "DKP-Topf", 0, -115)
	local poolOpts = {}
	local function RebuildPools()
		wipe(poolOpts)
		for _, key in ipairs(RM.DKP.PoolList(RM.db.data)) do poolOpts[#poolOpts + 1] = { key, RM.DKP.PoolName(key) } end
	end
	RebuildPools()
	local raidPool = UI.Cycle(page, 200, poolOpts, function()
		local s = RM.db.session
		return (s.active and s.pool) or RM.DKP.CurrentInstancePool() or RM.db.config.activePool or "mc"
	end, function(v)
		RM.db.config.activePool = v
		if RM.db.session.active then RM.db.session.pool = v end
		RM.DKP.MapCurrentInstance(v)
		RM.Fire("SESSION_CHANGED")
	end, "Für welchen Raid Start-/Endbonus und Versteigerungen gebucht werden.\n"
		.. "In einer Raid-Instanz wird der Topf automatisch erkannt. Wählst du hier etwas anderes, merkt sich RaidMaster das für diese Instanz.")
	Place(raidPool, page, 75, -110)
	local poolHint = Label(page, "", 0, -140, 11, true)
	poolHint:SetWidth(390)

	local killsText = Label(page, "", 0, -166, 11, true)
	killsText:SetWidth(380)

	Section(page, "Raid-Check", 0, -230)
	local checkBtn = UI.Button(page, "Jetzt prüfen", 120, 26, function() RM.Raid.RunCheck() end,
		"Prüft Plündermethode, Schwelle, Rechte und welche Spieler das Addon haben.")
	Place(checkBtn, page, 0, -256)
	local checkText = Label(page, "Noch nicht geprüft.", 0, -290, 11)
	checkText:SetWidth(390)

	-- rechte Spalte
	local rx = 410
	Section(page, "Ersatzbank", rx, 0)
	local sbList = UI.List(page, 230, 200, { { title = "Name", width = 200 } }, { emptyText = "Niemand auf der Ersatzbank." })
	Place(sbList, page, rx, -26)
	local sbBox = UI.EditBox(page, 140, 24)
	Place(sbBox, page, rx + 240, -26)
	local sbAdd = UI.Button(page, "Hinzufügen", 130, 24, function()
		local n = CapName(sbBox:GetText())
		if n ~= "" and not RM.DKP.IsStandby(n) then RM.DKP.ToggleStandby(n) end
		sbBox:SetText("")
	end)
	Place(sbAdd, page, rx + 240, -56)
	local sbRemove = UI.Button(page, "Entfernen", 130, 24, function()
		local d = sbList:Selected()
		if d then RM.DKP.ToggleStandby(d.key); sbList:ClearSelection() end
	end)
	Place(sbRemove, page, rx + 240, -86)
	local sbClear = UI.Button(page, "Alle entfernen", 130, 24, function()
		UI.Confirm("Ersatzbank leeren?", function() wipe(RM.db.config.standby); RM.Fire("DATA_CHANGED") end)
	end)
	Place(sbClear, page, rx + 240, -116)

	Section(page, "Pausen-Timer", rx, -246)
	local px = rx
	for _, m in ipairs({ 2, 5, 10, 15 }) do
		local b = UI.Button(page, m .. " Min.", 70, 26, function() RM.Raid.StartPause(m * 60) end)
		Place(b, page, px, -272)
		px = px + 76
	end
	local stopBtn = UI.Button(page, "Pause beenden", 120, 26, function() RM.Raid.StopPause() end)
	Place(stopBtn, page, rx, -304)

	Section(page, "Decay", rx, -350)
	local decayText = Label(page, "", rx, -376, 11)
	decayText:SetWidth(370)
	local decayBtn = UI.Button(page, "Decay anwenden", 140, 26, function()
		if not NeedOfficer() then return end
		local pct = RM.db.data.settings.decayPct
		UI.Confirm(string.format("Wöchentlichen Decay anwenden?\nAlle positiven DKP in allen Raid-Töpfen werden um %d %% reduziert.", pct), function() RM.DKP.ApplyDecay() end)
	end)
	Place(decayBtn, page, rx, -416)

	Section(page, "Kernhunde", rx, -462)
	local houndCheck = UI.Check(page, "Kürschner ansagen, wenn ein Kernhund stirbt",
		function() return RM.db.config.coreHound end, function(v) RM.db.config.coreHound = v end,
		"Der Raidleiter sagt die Kürschner mit Addon im Raid an (nach Skill sortiert).")
	Place(houndCheck, page, rx, -488)

	return function()
		local s = RM.db.session
		if s.active then
			sessionText:SetText(string.format("|cff40ff40Raid läuft seit %s.|r\nBosse werden automatisch erkannt und gebucht.", date("%H:%M", s.started)))
			startBtn:Disable()
			endBtn:Enable()
		else
			sessionText:SetText(s.ended and ("Kein Raid aktiv. Letzter Raid beendet: " .. RM.FormatTime(s.ended)) or "Kein Raid aktiv.")
			if RM.CanEdit() then startBtn:Enable() else startBtn:Disable() end
			endBtn:Disable()
		end
		RebuildPools()
		raidPool:Refresh()
		local inst = RM.DKP.CurrentInstancePool()
		if inst then
			poolHint:SetText("Erkannt in dieser Instanz: |cffff8c1a" .. RM.DKP.PoolName(inst) .. "|r")
		else
			poolHint:SetText("Außerhalb einer Raid-Instanz – der gewählte Topf gilt.")
		end
		local kills = {}
		local list = {}
		for id, t in pairs(s.kills or {}) do list[#list + 1] = { id = id, t = t } end
		table.sort(list, function(a, b) return a.t < b.t end)
		for _, k in ipairs(list) do
			local b = RM.Data.Bosses[k.id]
			local name = (b and b.name) or (s.names and s.names[k.id]) or ("Boss " .. k.id)
			kills[#kills + 1] = "|cff40ff40" .. name .. "|r (" .. date("%H:%M", k.t) .. ")"
		end
		killsText:SetText(#kills > 0 and ("Besiegt: " .. table.concat(kills, ", ")) or (s.active and "Noch kein Boss besiegt." or ""))

		if #RM.Raid.lastCheck > 0 then checkText:SetText(table.concat(RM.Raid.lastCheck, "\n")) end

		local rows = {}
		for name in pairs(RM.db.config.standby) do rows[#rows + 1] = { key = name, cells = { RM.ClassColor(RM.guild.class[name], name) } } end
		table.sort(rows, function(a, b) return a.key < b.key end)
		sbList:SetData(rows)

		local last = RM.db.data.lastDecay or 0
		local pct = RM.db.data.settings.decayPct
		if last > 0 then
			local days = math.floor((GetServerTime() - last) / 86400)
			local color = days >= 7 and "|cffff6040" or "|cffcccccc"
			decayText:SetText(string.format("%sLetzter Decay: %s (vor %d Tagen).|r Einstellung: %d %% pro Anwendung.", color, RM.FormatTime(last), days, pct))
		else
			decayText:SetText(string.format("Noch kein Decay angewendet. Einstellung: %d %% pro Anwendung.", pct))
		end
		if RM.CanEdit() then decayBtn:Enable() else decayBtn:Disable() end
		houndCheck:Refresh()
	end
end)

---------------------------------------------------------------------------
-- Seite: Anmeldungen (aus Discord)
---------------------------------------------------------------------------
UI.AddPage("signup", "Anmeldungen", function(page)
	Section(page, "Raidanmeldungen aus Discord", 0, 0)
	local info = Label(page, "", 0, -26, 12)
	info:SetWidth(520)

	local list = UI.List(page, 520, 330, {
		{ title = "Name", width = 115 },
		{ title = "Klasse", width = 85 },
		{ title = "Rolle", width = 80 },
		{ title = "Status", width = 90 },
		{ title = "Im Raid", width = 60 },
		{ title = "Grp.", width = 40, justify = "CENTER" },
	}, { emptyText = "Noch nichts importiert." })
	Place(list, page, 0, -50)

	local summary = Label(page, "", 0, -390, 11)
	summary:SetWidth(520)

	-- rechte Spalte: Import und Aktionen
	local rx = 540
	Section(page, "Importieren", rx, 0)
	Label(page, "Im Discord beim Raid auf 'Für RaidMaster' klicken, den Text kopieren und hier einfügen (Strg+V).", rx, -26, 11, true):SetWidth(245)
	local box = UI.Multiline(page, 245, 150)
	Place(box, page, rx, -64)
	local importBtn = UI.Button(page, "Übernehmen", 120, 26, function()
		if RM.Signup.Import(box.edit:GetText()) then
			box:SetText("")
			box.edit:ClearFocus()
		end
	end)
	Place(importBtn, page, rx, -220)
	importBtn:SetAccent(true)
	local clearBtn = UI.Button(page, "Liste leeren", 120, 26, function()
		UI.Confirm("Importierte Anmeldungen löschen?", function() RM.Signup.Clear() end)
	end)
	Place(clearBtn, page, rx + 125, -220)

	Section(page, "Aktionen", rx, -266)
	local inviteBtn = UI.Button(page, "Angemeldete einladen", 245, 28, function() RM.Signup.InviteAll(false) end,
		"Lädt alle Angemeldeten ein, die noch nicht in der Gruppe sind.\nAus einer Gruppe wird automatisch ein Schlachtzug.")
	Place(inviteBtn, page, rx, -292)
	local inviteAllBtn = UI.Button(page, "Inkl. Ersatzbank einladen", 245, 26, function() RM.Signup.InviteAll(true) end)
	Place(inviteAllBtn, page, rx, -326)
	local stopBtn = UI.Button(page, "Einladen stoppen", 245, 26, function() RM.Signup.StopInvites() end)
	Place(stopBtn, page, rx, -358)
	local benchBtn = UI.Button(page, "Ersatzbank übernehmen", 245, 26, function() RM.Signup.ApplyStandby() end,
		"Trägt alle Discord-Ersatzbank-Anmeldungen in die DKP-Ersatzbank ein (Seite Raid).")
	Place(benchBtn, page, rx, -390)
	local groupBtn = UI.Button(page, "Gruppen einteilen", 245, 26, function() RM.Signup.ArrangeGroups() end,
		"Sortiert den Schlachtzug in die festen Gruppen aus Discord (/raid aufstellung).\nNur außerhalb des Kampfes.")
	Place(groupBtn, page, rx, -422)

	local autoInv = UI.Check(page, "Auto-Einladung", function() return RM.db.config.autoInvite end,
		function(v) RM.db.config.autoInvite = v; UI.RefreshCurrent() end,
		"Lädt automatisch alle Aufgestellten ein, sobald der Raid öffnet, und Nachzügler bis 30 Min. nach Beginn.\nDein Spiel muss dafür laufen.")
	Place(autoInv, page, rx, -458)
	local minutes = UI.Cycle(page, 90, { { 5, "5 Min." }, { 10, "10 Min." }, { 15, "15 Min." }, { 20, "20 Min." }, { 30, "30 Min." } },
		function() return RM.db.config.autoInviteMinutes or 15 end, function(v) RM.db.config.autoInviteMinutes = v; UI.RefreshCurrent() end,
		"So viele Minuten vor Raidbeginn öffnet der Raid.")
	Place(minutes, page, rx + 150, -454)
	local autoGrp = UI.Check(page, "Gruppen automatisch sortieren", function() return RM.db.config.autoGroups end,
		function(v) RM.db.config.autoGroups = v end, "Jeder, der dem Raid beitritt, kommt sofort in seine feste Gruppe.")
	Place(autoGrp, page, rx, -486)
	local autoState = Label(page, "", rx, -512, 11, true)
	autoState:SetWidth(245)

	local STATUS_COLORS = {
		an = { 0.4, 1, 0.4 }, ersatz = { 1, 0.8, 0.3 }, vielleicht = { 0.6, 0.75, 1 }, ab = { 1, 0.4, 0.4 },
	}
	local ORDER = { an = 1, ersatz = 2, vielleicht = 3, ab = 4 }

	return function()
		local su = RM.db.signup
		if su then
			info:SetText(string.format("|cffff8c1a%s|r  ·  %s  ·  importiert %s", su.title ~= "" and su.title or "Raid", su.date or "", RM.FormatTime(su.imported or 0)))
		else
			info:SetText("Noch keine Anmeldungen importiert.")
		end
		local rows, missing, extra = RM.Signup.Compare()
		table.sort(rows, function(a, b)
			local x, y = ORDER[a.entry.status] or 9, ORDER[b.entry.status] or 9
			if x == y then return a.entry.name < b.entry.name end
			return x < y
		end)
		local data = {}
		for _, r in ipairs(rows) do
			local e = r.entry
			local group = r.inRaid and (r.online and "dabei" or "offline") or "-"
			local grp = su and su.groups and su.groups[e.name]
			local grpText = grp and tostring(grp) or ((su and su.bench and su.bench[e.name]) and "Bank" or "")
			data[#data + 1] = {
				key = e.name,
				cells = { RM.ClassColor(e.cls, e.name), ClassName(e.cls), RM.Signup.ROLE[e.role] or e.role,
					RM.Signup.STATUS[e.status] or e.status, group, grpText },
				colors = { nil, { 0.75, 0.75, 0.75 }, { 0.75, 0.75, 0.75 }, STATUS_COLORS[e.status],
					r.inRaid and (r.online and { 0.4, 1, 0.4 } or { 1, 0.8, 0.3 }) or { 0.5, 0.5, 0.5 } },
			}
		end
		list:SetData(data)

		if su then
			local signed, present = 0, 0
			for _, r in ipairs(rows) do
				if r.entry.status == "an" then
					signed = signed + 1
					if r.inRaid then present = present + 1 end
				end
			end
			local lines = { string.format("Angemeldet: %d  ·  davon in der Gruppe: %d", signed, present) }
			if #missing > 0 then lines[#lines + 1] = "|cffffcc00Fehlen noch:|r " .. table.concat(missing, ", ") end
			if #extra > 0 then lines[#lines + 1] = "|cff99bbffIn der Gruppe ohne Anmeldung:|r " .. table.concat(extra, ", ") end
			summary:SetText(table.concat(lines, "\n"))
		else
			summary:SetText("")
		end

		local inviting = RM.Signup.IsInviting()
		for _, b in ipairs({ inviteBtn, inviteAllBtn, benchBtn }) do
			if su and not inviting then b:Enable() else b:Disable() end
		end
		if inviting then stopBtn:Enable() else stopBtn:Disable() end
		if su and su.groups then groupBtn:Enable() else groupBtn:Disable() end
		autoInv:Refresh()
		autoGrp:Refresh()
		minutes:Refresh()
		autoState:SetText("Auto-Einladung: " .. RM.Signup.AutoInviteState())
	end
end)

---------------------------------------------------------------------------
-- Seite: Soft Reserve (PUG-Raids)
---------------------------------------------------------------------------
UI.AddPage("softreserve", "Soft Reserve", function(page)
	local PUG = RM.PUG
	Section(page, "PUG-Raid mit Soft Reserve", 0, 0)
	local status = Label(page, "", 0, -26, 12)
	status:SetWidth(380)

	-- Eigene Reservierungen
	Section(page, "Meine Reservierungen", 0, -74)
	local myList = UI.List(page, 380, 110, {
		{ title = "Item", width = 280 },
		{ title = "ID", width = 70, justify = "RIGHT" },
	}, { emptyText = "Noch nichts reserviert." })
	Place(myList, page, 0, -100)

	local idBox = UI.LinkBox(page, 250, 24)
	Place(idBox, page, 0, -218)
	local idHint = UI.Text(idBox, "Item-ID oder Shift-Klick auf Item", 11, unpack(COLORS.muted))
	idHint:SetPoint("LEFT", 8, 0)
	idBox:SetScript("OnTextChanged", function(self) if self:GetText() == "" then idHint:Show() else idHint:Hide() end end)
	local function AddMine()
		PUG.AddMine(idBox:GetText())
		idBox:SetText("")
		idBox:ClearFocus()
	end
	idBox:SetScript("OnEnterPressed", AddMine)
	local addBtn = UI.Button(page, "Reservieren", 122, 24, AddMine)
	Place(addBtn, page, 258, -218)
	addBtn:SetAccent(true)
	local removeBtn = UI.Button(page, "Ausgewähltes entfernen", 180, 24, function()
		local d = myList:Selected()
		if d then PUG.RemoveMine(d.id); myList:ClearSelection() end
	end)
	Place(removeBtn, page, 0, -248)
	local help = Label(page, "Die Item-ID steht z. B. bei Wowhead in der Adresse (item=12345). Ohne Addon: /w <Leiter> !sr 12345", 0, -280, 11, true)
	help:SetWidth(380)

	-- Alle Reservierungen
	local rx = 400
	Section(page, "Alle Reservierungen", rx, 0)
	local allList = UI.List(page, 390, 262, {
		{ title = "Item", width = 210 },
		{ title = "Reserviert von", width = 150 },
	}, { emptyText = "Keine Reservierungen." })
	Place(allList, page, rx, -26)
	local removeEntry = UI.Button(page, "Reservierung entfernen", 180, 24, function()
		local d = allList:Selected()
		if not d then return end
		for _, n in ipairs(d.names) do PUG.RemoveReserve(n, d.id) end
		allList:ClearSelection()
	end, "Leiter: entfernt die gewählte Reservierung (alle Spieler dieses Items).")
	Place(removeEntry, page, rx, -294)

	-- Leitung
	Section(page, "Leitung", 0, -326)
	Label(page, "SR pro Spieler", 0, -357)
	local limit = 1
	local limitCycle = UI.Cycle(page, 80, { { 1, "1" }, { 2, "2" }, { 3, "3" } }, function() return limit end, function(v) limit = v end)
	Place(limitCycle, page, 110, -352)
	local startBtn = UI.Button(page, "PUG-Raid starten", 185, 26, function()
		UI.Confirm(string.format("PUG-Raid mit Soft Reserve starten?\nJe %d Item(s) pro Spieler. Epische Items werden ausgewürfelt statt versteigert.", limit),
			function() PUG.Start(limit) end)
	end)
	Place(startBtn, page, 0, -386)
	startBtn:SetAccent(true)
	local stopBtn = UI.Button(page, "PUG-Raid beenden", 185, 26, function()
		UI.Confirm("PUG-Raid beenden?", function() PUG.Stop() end)
	end)
	Place(stopBtn, page, 195, -386)
	local lockBtn = UI.Button(page, "SR sperren", 185, 26, function() PUG.SetLocked(not RM.db.pug.locked) end,
		"Nach dem Sperren kann niemand mehr reservieren oder ändern.")
	Place(lockBtn, page, 0, -418)
	local postBtn = UI.Button(page, "SR-Liste im Raid posten", 185, 26, function() PUG.PostList() end)
	Place(postBtn, page, 195, -418)
	local importBtn = UI.Button(page, "SR aus Discord übernehmen", 185, 26, function() PUG.ImportFromSignup() end,
		"Übernimmt die Soft Reserves aus dem Discord-Import (Seite Anmeldungen).")
	Place(importBtn, page, 0, -450)
	local clearBtn = UI.Button(page, "Alle SR löschen", 185, 26, function()
		UI.Confirm("Alle Soft Reserves löschen?", function() PUG.ClearAll() end)
	end)
	Place(clearBtn, page, 195, -450)

	-- Würfeln
	Section(page, "Würfeln", rx, -326)
	local rollText = Label(page, "", rx, -350, 12)
	rollText:SetWidth(390)
	local rollList = UI.List(page, 390, 100, {
		{ title = "Spieler", width = 150 },
		{ title = "Art", width = 100 },
		{ title = "Wurf", width = 100, justify = "RIGHT" },
	}, { emptyText = "Noch keine Würfe." })
	Place(rollList, page, rx, -372)
	local nextBtn = UI.Button(page, "Nächstes würfeln", 125, 24, function()
		if #PUG.queue > 0 then PUG.StartRoll(1) else RM.Print("Die Würfel-Warteschlange ist leer.") end
	end)
	Place(nextBtn, page, rx, -478)
	local finishBtn = UI.Button(page, "Jetzt beenden", 125, 24, function() PUG.FinishRoll() end)
	Place(finishBtn, page, rx + 132, -478)
	local cancelBtn = UI.Button(page, "Abbrechen", 125, 24, function() PUG.CancelRoll() end)
	Place(cancelBtn, page, rx + 264, -478)
	local rollBox = UI.LinkBox(page, 250, 24)
	Place(rollBox, page, rx, -510)
	local rollHint = UI.Text(rollBox, "Item per Shift-Klick würfeln lassen", 11, unpack(COLORS.muted))
	rollHint:SetPoint("LEFT", 8, 0)
	rollBox:SetScript("OnTextChanged", function(self) if self:GetText() == "" then rollHint:Show() else rollHint:Hide() end end)
	local rollBtn = UI.Button(page, "Würfeln", 132, 24, function()
		local link = rollBox:GetText()
		if link and link:find("item:") then PUG.StartRoll(link); rollBox:SetText("") else RM.Print("Bitte ein Item per Shift-Klick einfügen.") end
	end)
	Place(rollBtn, page, rx + 258, -510)

	page.elapsed = 0
	page:SetScript("OnUpdate", function(self, el)
		self.elapsed = self.elapsed + el
		if self.elapsed > 0.5 and PUG.current then self.elapsed = 0; UI.RefreshCurrent() end
	end)

	local KIND = { sr = "Soft Reserve", need = "Bedarf", greed = "Gier" }

	return function()
		local v = PUG.view
		if v.active then
			status:SetText(string.format("|cff40ff40PUG-Raid aktiv|r – Leiter: %s · je %d Item(s)%s",
				v.leader or "?", v.limit or 1, v.locked and " · |cffff6040gesperrt|r" or ""))
		else
			status:SetText("Kein PUG-Raid aktiv. Der Raidleiter startet ihn unten unter 'Leitung'.")
		end

		local mine = {}
		for _, id in ipairs(PUG.MyReserves()) do
			mine[#mine + 1] = { key = id, id = id, cells = { PUG.ItemLabel(id), tostring(id) }, tooltip = function(tt) tt:SetHyperlink("item:" .. id) end }
		end
		myList:SetData(mine)
		local canReserve = v.active and not v.locked
		if canReserve and #mine < (v.limit or 1) then addBtn:Enable() else addBtn:Disable() end
		if canReserve and #mine > 0 then removeBtn:Enable() else removeBtn:Disable() end

		local byItem = {}
		for name, ids in pairs(v.reserves or {}) do
			for _, id in ipairs(ids) do
				byItem[id] = byItem[id] or {}
				table.insert(byItem[id], name)
			end
		end
		local all = {}
		for id, names in pairs(byItem) do
			table.sort(names)
			all[#all + 1] = { key = id, id = id, names = names, cells = { PUG.ItemLabel(id), table.concat(names, ", ") },
				colors = { nil, #names > 1 and { 1, 0.8, 0.3 } or nil },
				tooltip = function(tt) tt:SetHyperlink("item:" .. id) end }
		end
		table.sort(all, function(a, b) return PUG.ItemName(a.id) < PUG.ItemName(b.id) end)
		allList:SetData(all)

		local lead = PUG.IsLeader()
		if PUG.CanLead() and not lead then startBtn:Enable() else startBtn:Disable() end
		for _, b in ipairs({ stopBtn, lockBtn, postBtn, importBtn, clearBtn, removeEntry, nextBtn, rollBtn }) do
			if lead then b:Enable() else b:Disable() end
		end
		lockBtn:SetText(RM.db.pug and RM.db.pug.locked and "SR entsperren" or "SR sperren")
		limitCycle:Refresh()

		local c = PUG.current
		if c then
			local rem = math.max(0, math.ceil(c.endsAt - GetTime()))
			local who = c.allowed and ("nur SR: " .. table.concat(c.sr, ", ")) or "Bedarf /roll · Gier /roll 99"
			rollText:SetText(c.link .. "\n" .. (c.finished and "Beendet" or (rem .. " Sek. – " .. who)))
			finishBtn:Enable(); cancelBtn:Enable()
		else
			rollText:SetText(string.format("Kein Würfeln aktiv. Warteschlange: %d Item(s).", #PUG.queue))
			finishBtn:Disable(); cancelBtn:Disable()
		end
		local rows = {}
		for _, r in ipairs(PUG.RollList()) do
			rows[#rows + 1] = { key = r.name, cells = { r.name, KIND[r.kind] or r.kind, tostring(r.v) } }
		end
		rollList:SetData(rows)
	end
end)

---------------------------------------------------------------------------
-- Seite: Einteilung (Heilung, Entfluchen, CC)
---------------------------------------------------------------------------
UI.AddPage("assign", "Einteilung", function(page)
	local Assign = RM.Assign
	local selected = "general"

	Section(page, "Einteilung per Knopfdruck", 0, 0)
	Label(page, "Tanks in Reihenfolge (MT zuerst), mit Komma getrennt:", 0, -28, 11, true):SetWidth(380)
	local tankBox = UI.EditBox(page, 300, 24)
	Place(tankBox, page, 0, -46)
	tankBox:SetScript("OnTextChanged", function(self, user) if user then RM.db.config.assignTanks = self:GetText() end end)
	local autoBtn = UI.Button(page, "Auto", 72, 24, function()
		local t = Assign.AutoTanks()
		RM.db.config.assignTanks = table.concat(t, ", ")
		tankBox:SetText(RM.db.config.assignTanks)
	end, "Tanks aus Haupttank-Markierung, Discord-Rolle 'Tank' oder Kriegern ermitteln.")
	Place(autoBtn, page, 308, -46)

	local buildBtn = UI.Button(page, "Einteilung erstellen", 185, 30, function() Assign.Build() end,
		"Erstellt Heil-, Entfluch-, Bann- und CC-Einteilung für alle Molten-Core-Bosse aus den Klassen im Raid.")
	Place(buildBtn, page, 0, -84)
	buildBtn:SetAccent(true)
	local sendBtn = UI.Button(page, "An alle senden", 185, 30, function() Assign.SendAll() end,
		"Spieler mit Addon sehen ihre Aufgabe beim Pull groß auf dem Bildschirm, alle anderen bekommen sie zugeflüstert.\\n"
		.. "Danach /reload, damit der Discord-Bot jedem eine Direktnachricht schickt.")
	Place(sendBtn, page, 195, -84)
	local info = Label(page, "Grundlage: Klassen im Raid, Rollen aus der Discord-Anmeldung und die Symbol-Vorlagen der Seite Raidleiter. "
		.. "Gruppen für Entfluchen, Bannen und Raidheilung richten sich nach den Raidgruppen.", 0, -124, 11, true)
	info:SetWidth(380)

	Section(page, "Meine Aufgaben", 0, -186)
	local mine = UI.Multiline(page, 380, 330, true)
	Place(mine, page, 0, -212)

	local rx = 400
	Section(page, "Übersicht", rx, 0)
	local opts = {}
	for _, c in ipairs(Assign.Contexts) do opts[#opts + 1] = { c.key, c.name } end
	local ctxCycle = UI.Cycle(page, 200, opts, function() return selected end, function(v) selected = v; UI.RefreshCurrent() end)
	Place(ctxCycle, page, rx + 90, 4)
	local preview = UI.Multiline(page, 390, 460, true)
	Place(preview, page, rx, -28)
	local postBtn = UI.Button(page, "Im Raid posten", 185, 28, function() Assign.Post(selected) end,
		"Postet die gewählte Einteilung in den Raidchat (Symbole werden im Chat als Grafik angezeigt).")
	Place(postBtn, page, rx, -500)

	local function iconize(text)
		return (text:gsub("{rt(%d)}", "|TInterface\\TargetingFrame\\UI-RaidTargetingIcon_%1:0|t"))
	end

	return function()
		if not tankBox:HasFocus() then tankBox:SetText(RM.db.config.assignTanks or "") end
		ctxCycle:Refresh()
		local store = RM.db.assign
		local ctx = store and store.ctx[selected]
		if ctx then
			local lines = {}
			for _, l in ipairs(ctx.lines) do lines[#lines + 1] = iconize(l) end
			preview:SetText(string.format("Erstellt %s von %s\n\n", RM.FormatTime(store.v), store.by or "?") .. table.concat(lines, "\n"))
		else
			preview:SetText("Noch keine Einteilung erstellt.")
		end
		local my = RM.db.myAssign
		if not my and store then my = Assign.PersonalTexts(RM.Me()) end
		local parts = {}
		for _, c in ipairs(Assign.Contexts) do
			if my and my[c.key] then parts[#parts + 1] = c.name .. ": " .. iconize(my[c.key]) end
		end
		mine:SetText(#parts > 0 and table.concat(parts, "\n\n") or "Noch keine Aufgaben erhalten.")
		local lead = RM.InRaid() and (RM.IsAssist() or RM.CanEdit())
		for _, b in ipairs({ buildBtn, sendBtn, autoBtn }) do if lead then b:Enable() else b:Disable() end end
		if store and RM.InRaid() then postBtn:Enable() else postBtn:Disable() end
		if store and lead then sendBtn:Enable() else sendBtn:Disable() end
	end
end)

---------------------------------------------------------------------------
-- Seite: Raidleiter (Boss-Infos und Markierungen)
---------------------------------------------------------------------------
UI.AddPage("leader", "Raidleiter", function(page)
	local selectedBoss = RM.Data.InfoBossOrder[1]
	Section(page, "Molten Core – Boss-Infos", 0, 0)

	local bossButtons = {}
	local info = UI.Multiline(page, 560, 300, true)
	Place(info, page, 200, -28)

	local y = -28
	for _, id in ipairs(RM.Data.InfoBossOrder) do
		local b = UI.Button(page, RM.Data.Bosses[id].name, 190, 26, function()
			selectedBoss = id
			UI.RefreshCurrent()
		end)
		Place(b, page, 0, y)
		b.label:SetJustifyH("LEFT")
		b.label:ClearAllPoints()
		b.label:SetPoint("LEFT", 10, 0)
		bossButtons[id] = b
		y = y - 30
	end

	local postBtn = UI.Button(page, "Kurzinfo im Raid posten", 200, 28, function() RM.Markers.PostBossInfo(selectedBoss) end,
		"Postet zwei kurze Zeilen (erste als Raidwarnung).")
	Place(postBtn, page, 200, -336)
	postBtn:SetAccent(true)

	-- Markierungen
	Section(page, "Schlachtzugsymbole", 0, -382)
	Label(page, "Vorlage für 'Auto'", 0, -412)
	local opts = {}
	for _, t in ipairs(RM.Data.MarkerTemplates) do opts[#opts + 1] = { t.id, t.name } end
	local tmpl = UI.Cycle(page, 170, opts, function() return RM.db.config.markerTemplate end, function(v)
		RM.db.config.markerTemplate = v
		RM.Markers.ResetUsed()
		RM.Fire("CONFIG_CHANGED")
	end)
	Place(tmpl, page, 130, -407)
	local note = Label(page, "", 310, -412, 11, true)
	note:SetWidth(460)

	local barCheck = UI.Check(page, "Markierungsleiste anzeigen", function() return RM.db.config.markerBar end, function(v)
		RM.db.config.markerBar = v
		RM.Fire("CONFIG_CHANGED")
	end)
	Place(barCheck, page, 0, -446)
	local lockCheck = UI.Check(page, "Leiste fixieren", function() return RM.db.config.markerLocked end, function(v) RM.db.config.markerLocked = v end)
	Place(lockCheck, page, 230, -446)

	local clearBtn = UI.Button(page, "Alle Symbole entfernen", 180, 26, function() RM.Markers.ClearAll() end)
	Place(clearBtn, page, 0, -478)

	local keyHint = Label(page, "Am schnellsten: Esc > Tastaturbelegung > RaidMaster. Dort z. B. eine Taste für 'Nächstes freies Symbol' "
		.. "belegen, dann mit der Maus über die Gegner fahren und die Taste drücken – ohne sie anzuklicken.", 0, -514, 11, true)
	keyHint:SetWidth(770)

	return function()
		local i = RM.Data.BossInfo[selectedBoss]
		info:SetText(i and i.text or "")
		for id, b in pairs(bossButtons) do b:SetAccent(id == selectedBoss) end
		tmpl:Refresh()
		local t = RM.Data.GetTemplate(RM.db.config.markerTemplate)
		note:SetText(t.note)
		barCheck:Refresh()
		lockCheck:Refresh()
	end
end)

---------------------------------------------------------------------------
-- Seite: Skillungen
---------------------------------------------------------------------------
UI.AddPage("specs", "Skillungen", function(page)
	local Spec = RM.Spec
	local SOURCES = { self = "eigene", addon = "Addon", inspect = "Betrachtet" }
	local ROLE_COLORS = { tank = { 0.6, 0.8, 1 }, heal = { 0.4, 1, 0.5 }, melee = { 1, 0.75, 0.4 }, ranged = { 1, 0.55, 0.9 } }

	Section(page, "Skillungen", 0, 0)
	local info = Label(page, "", 0, -26, 11, true)
	info:SetWidth(780)

	local list = UI.List(page, 780, 380, {
		{ title = "Name", width = 150 },
		{ title = "Klasse", width = 110 },
		{ title = "Skillung", width = 150 },
		{ title = "Punkte", width = 80 },
		{ title = "Rolle", width = 90 },
		{ title = "Quelle", width = 80 },
		{ title = "Stand", width = 90 },
	}, { emptyText = "Noch keine Skillungen bekannt." })
	Place(list, page, 0, -64)

	local scanBtn = UI.Button(page, "Raid scannen", 140, 28, function()
		if Spec.scan.running then Spec.StopScan() else Spec.StartScan(true) end
	end, "Fragt alle Addon-Nutzer im Raid nach ihrer Skillung und betrachtet Spieler ohne Addon\n"
		.. "(in Reichweite, außerhalb des Kampfes).")
	Place(scanBtn, page, 0, -456)
	local sendBtn = UI.Button(page, "Meine Skillung senden", 170, 28, function()
		Spec.UpdateMine(true)
		RM.Print("Deine Skillung wurde an Gilde und Raid gesendet.")
	end)
	Place(sendBtn, page, 150, -456)
	local autoCheck = UI.Check(page, "Als Raidleiter automatisch alle 5 Minuten scannen",
		function() return RM.db.config.specScan end, function(v) RM.db.config.specScan = v end,
		"Nur für Raidleiter, Assistenten und Offiziere.")
	Place(autoCheck, page, 340, -460)
	local status = Label(page, "", 0, -496, 11, true)
	status:SetWidth(780)

	return function()
		local rows = Spec.List()
		local data = {}
		local known = 0
		for _, r in ipairs(rows) do
			local e = r.entry
			if e then known = known + 1 end
			data[#data + 1] = {
				key = r.name,
				cells = {
					RM.ClassColor(r.class, r.name),
					ClassName(r.class),
					r.label or (e and "?" or "|cff888888unbekannt|r"),
					e and Spec.PointsText(e) or "",
					r.role and Spec.ROLE_NAMES[r.role] or "",
					e and (SOURCES[e.s] or e.s or "") or "",
					e and RM.FormatTime(e.t or 0) or "",
				},
				colors = { nil, nil, nil, nil, r.role and ROLE_COLORS[r.role] or nil },
			}
		end
		list:SetData(data)
		if RM.InRaid() then
			info:SetText(string.format("Skillungen der Raidmitglieder: %d von %d bekannt. Nach /reload übernimmt der Discord-Bot sie in die Profile.", known, #rows))
		else
			info:SetText(string.format("%d bekannte Skillungen (Gilde und frühere Raids). Nach /reload übernimmt der Discord-Bot sie in die Profile.", known))
		end
		scanBtn.label:SetText(Spec.scan.running and "Scan stoppen" or "Raid scannen")
		if Spec.CanScan() then scanBtn:Enable() else scanBtn:Disable() end
		autoCheck:Refresh()
		if Spec.inspectUnsupported then
			status:SetText("Dieser Spielclient liefert beim Betrachten keine Talente – Skillungen kommen nur von Spielern mit RaidMaster.")
		elseif Spec.scan.running then
			local cur = Spec.scan.current
			status:SetText(string.format("Scan läuft: noch %d Spieler%s", #Spec.scan.queue, cur and (" – betrachte " .. cur.name) or ""))
		else
			status:SetText("Spieler mit RaidMaster senden ihre Skillung selbst. Spieler ohne Addon werden per Betrachten erfasst.")
		end
	end
end)

---------------------------------------------------------------------------
-- Seite: Einstellungen
---------------------------------------------------------------------------
UI.AddPage("settings", "Einstellungen", function(page)
	local fields = {}
	local function S() return RM.db.data.settings end

	local function NumField(label, x, y, getter, setter, tooltip)
		local fs = Label(page, label, x, y - 5)
		fs:SetWidth(170)
		local e = UI.EditBox(page, 60, 24, true)
		Place(e, page, x + 175, y)
		if tooltip then
			e:SetScript("OnEnter", function(self) GameTooltip:SetOwner(self, "ANCHOR_RIGHT"); GameTooltip:AddLine(tooltip, 1, 1, 1, true); GameTooltip:Show() end)
			e:SetScript("OnLeave", function() GameTooltip:Hide() end)
		end
		fields[#fields + 1] = { edit = e, get = getter, set = setter }
		return e
	end

	Section(page, "DKP-Vergabe", 0, 0)
	local y = -28
	NumField("Pünktlich zum Raidstart", 0, y, function() return S().dkpStart end, function(v) S().dkpStart = v end); y = y - 28
	NumField("Raid bis zum Ende", 0, y, function() return S().dkpEnd end, function(v) S().dkpEnd = v end); y = y - 28
	NumField("Andere Bosse (Standard)", 0, y, function() return S().defaultBossDKP end, function(v) S().defaultBossDKP = v end); y = y - 36

	-- Boss-DKP je Raid-Topf (neue Bosse erscheinen nach dem ersten Kill)
	Section(page, "Bosse", 0, y)
	local settingsPool = "mc"
	local spOpts = {}
	local function RebuildSP()
		wipe(spOpts)
		for _, key in ipairs(RM.DKP.PoolList(RM.db.data)) do spOpts[#spOpts + 1] = { key, RM.DKP.PoolName(key) } end
	end
	RebuildSP()
	local spCycle = UI.Cycle(page, 170, spOpts, function() return settingsPool end, function(v)
		settingsPool = v
		UI.RefreshCurrent()
	end, "Raid wählen, dessen Boss-DKP du einstellen willst.")
	Place(spCycle, page, 60, y + 4)
	y = y - 28
	local bossRows = {}
	local bossNote = Label(page, "", 0, y - 5, 11, true)
	bossNote:SetWidth(270)
	for i = 1, 13 do
		local row = {}
		row.label = Label(page, "", 0, y - 5)
		row.label:SetWidth(170)
		row.edit = UI.EditBox(page, 60, 24, true)
		Place(row.edit, page, 175, y)
		bossRows[i] = row
		fields[#fields + 1] = {
			edit = row.edit,
			get = function() return row.id and (S().bossDKP[row.id] or S().defaultBossDKP) or nil end,
			set = function(v) if row.id then S().bossDKP[row.id] = v end end,
		}
		y = y - 26
	end

	local function UpdateBossRows()
		RebuildSP()
		spCycle:Refresh()
		local list = RM.Data.BossesForPool(settingsPool, RM.db.data)
		for i, row in ipairs(bossRows) do
			local b = list[i]
			row.id = b and b.id or nil
			if b then
				row.label:SetText(b.name)
				row.label:Show()
				row.edit:Show()
			else
				row.label:Hide()
				row.edit:Hide()
			end
		end
		if #list == 0 then
			bossNote:SetText("Die Bosse dieses Raids werden beim ersten Kill automatisch erkannt. Bis dahin gilt der Standardwert.")
			bossNote:Show()
		else
			bossNote:Hide()
		end
	end

	local x2 = 290
	Section(page, "Gebote", x2, 0)
	local y2 = -28
	NumField("Mindestgebot", x2, y2, function() return S().minBid end, function(v) S().minBid = math.max(0, v) end); y2 = y2 - 28
	NumField("Gebotsschritt", x2, y2, function() return S().bidIncrement end, function(v) S().bidIncrement = math.max(1, v) end); y2 = y2 - 28
	NumField("Dauer (Sekunden)", x2, y2, function() return S().auctionTime end, function(v) S().auctionTime = math.max(10, math.min(120, v)) end); y2 = y2 - 36

	Section(page, "System", x2, y2)
	y2 = y2 - 28
	NumField("Decay in %", x2, y2, function() return S().decayPct end, function(v) S().decayPct = math.max(0, math.min(100, v)) end); y2 = y2 - 28
	NumField("Offiziersränge bis Index", x2, y2, function() return S().officerRank end, function(v) S().officerRank = math.max(0, math.min(9, v)) end,
		"Gildenrang-Index: 0 = Gildenmeister, 1 = nächster Rang usw. Alle Ränge bis zu diesem Index dürfen DKP ändern."); y2 = y2 - 36

	local checks = {}
	local function SCheck(label, key, tooltip)
		local cb = UI.Check(page, label, function() return S()[key] end, function(v) S()[key] = v end, tooltip)
		Place(cb, page, x2, y2)
		checks[#checks + 1] = cb
		y2 = y2 - 26
	end
	SCheck("Erstkill zählt doppelt", "firstKillDouble")
	SCheck("Verlängern bei späten Geboten (5 Sek.)", "antiSnipe", "Kommt in den letzten 5 Sekunden ein Gebot, wird auf 5 Sekunden verlängert.")
	SCheck("Negative DKP erlauben", "allowNegative", "Spieler dürfen mehr bieten, als sie haben.")
	SCheck("Nur Spieler online erhalten DKP", "onlyOnline")
	SCheck("Ersatzbank erhält DKP", "standbyGetsDKP")

	local saveBtn = UI.Button(page, "Speichern und an die Gilde verteilen", 300, 30, function()
		if not NeedOfficer() then return end
		for _, f in ipairs(fields) do
			local v = tonumber(f.edit:GetText())
			if v and f.edit:IsShown() then f.set(math.floor(v)) end
		end
		RM.DKP.SettingsChanged()
	end)
	Place(saveBtn, page, x2, y2 - 10)
	saveBtn:SetAccent(true)

	local revertBtn = UI.Button(page, "Verwerfen", 100, 30, function()
		for _, f in ipairs(fields) do f.edit:SetText(tostring(f.get() or 0)) end
		for _, c in ipairs(checks) do c:Refresh() end
	end)
	Place(revertBtn, page, x2 + 306, y2 - 10)

	local note = Label(page, "Diese Werte gelten für die ganze Gilde und werden mit allen Addon-Nutzern abgeglichen. "
		.. "Häkchen werden sofort lokal übernommen und beim Speichern verteilt.", x2, y2 - 52, 11, true)
	note:SetWidth(480)

	local mmCheck = UI.Check(page, "Minimap-Knopf ausblenden", function() return RM.db.config.minimap.hide end, function(v)
		RM.db.config.minimap.hide = v
		local b = _G["RaidMasterMinimapButton"]
		if b then if v then b:Hide() else b:Show() end end
	end)
	Place(mmCheck, page, x2, y2 - 100)

	return function()
		UpdateBossRows()
		for _, f in ipairs(fields) do
			if not f.edit:HasFocus() then f.edit:SetText(tostring(f.get() or 0)) end
		end
		for _, c in ipairs(checks) do c:Refresh() end
		mmCheck:Refresh()
		if RM.CanEdit() then saveBtn:Enable() else saveBtn:Disable() end
	end
end)
