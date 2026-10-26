-- RaidMaster - Seiten des Hauptfensters
-- DKP, Versteigerung, Loot, Log, Raid, Raidleiter, Einstellungen

local ADDON, RM = ...
local L = RM.L
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
	RM.Print(L["Dafür brauchst du Offiziersrechte."])
	return false
end

-- Namen säubern; nur WoW Forever hat Vor- und Nachnamen ("Rokan Steinwacht"), dort Leerzeichen behalten
local function CapName(name)
	if RM.GAME.key == "forever" then
		name = (name or ""):gsub("^%s+", ""):gsub("%s+$", ""):gsub("%s+", " ")
	else
		name = (name or ""):gsub("%s", "")
	end
	if name == "" then return "" end
	return (name:gsub("(%S)(%S*)", function(a, b) return a:upper() .. b:lower() end))
end

-- Auswahl der angezeigten DKP-Tabelle (eigene Gilde oder Raid-Gilde)
local function ViewCycle(page, x, y)
	local opts = {}
	local function Rebuild()
		wipe(opts)
		local own = RM.MyGuild()
		opts[#opts + 1] = { "__own", own and (L["Gilde: "] .. own) or L["Eigene Daten"] }
		for g in pairs(RM.db.foreign) do opts[#opts + 1] = { g, L["Raid: "] .. g } end
	end
	Rebuild()
	local cyc = UI.Cycle(page, 220, opts, function() return UI.viewGuild or "__own" end, function(v)
		if v == "__own" then UI.viewGuild = nil else UI.viewGuild = v end
		UI.RefreshCurrent()
	end, L["Wechselt zwischen der eigenen Gilde und der DKP-Tabelle der Gilde, mit der du gerade raidest."])
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
	local cyc = UI.Dropdown(page, width or 220, function() return UI.PoolGroups(RM.DKP.View(), withAll) end, function()
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
	end, L["Jeder Raid hat einen eigenen DKP-Topf. Hier wählst du, welchen du siehst."] .. "\n"
		.. L["Raids nach WoW-Erweiterung geordnet; ein grüner Punkt zeigt Raids mit DKP-Ständen."])
	Place(cyc, page, x, y)
	function cyc:Update()
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
UI.AddPage("dkp", L["DKP-Stände"], function(page)
	local sortKey, sortDesc = "dkp", true
	local onlyRaid = false
	local selected

	Section(page, L["DKP-Stände"], 0, 0)
	local poolCycle = PoolCycle(page, 120, 4, 240)
	local totalLabel = Label(page, "", 372, -2, 13)
	totalLabel:SetWidth(420)

	local search = UI.EditBox(page, 180, 24)
	Place(search, page, 0, -30)
	local searchHint = UI.Text(search, L["Suchen ..."], 11, unpack(COLORS.muted))
	searchHint:SetPoint("LEFT", 8, 0)

	local raidCheck = UI.Check(page, L["Nur Raid"], function() return onlyRaid end, function(v) onlyRaid = v; UI.RefreshCurrent() end)
	Place(raidCheck, page, 196, -33)

	local syncBtn = UI.Button(page, L["Sync anfordern"], 120, 24, function() RM.Comm.RequestSync() end,
		L["Fragt Offiziere nach dem neuesten DKP-Stand."])
	Place(syncBtn, page, 316, -30)

	local exportBtn = UI.Button(page, L["Export"], 80, 24, function() UI.ShowExport(RM.DKP.ExportText()) end)
	Place(exportBtn, page, 442, -30)

	local viewCycle = ViewCycle(page, 560, -30)

	local list
	list = UI.List(page, 540, 490, {
		{ title = L["Name"], width = 140 },
		{ title = L["Klasse"], width = 95 },
		{ title = "DKP", width = 80, justify = "RIGHT" },
		{ title = L["Status"], width = 180 },
	}, {
		emptyText = L["Noch keine DKP-Daten. Als Offizier: Raid starten oder Spieler hinzufügen."],
		onSort = function(col)
			-- "Verdient" wird weiter mitgezählt (RM.DKP.Earned), aber nicht angezeigt
			local key = ({ "name", "class", "dkp", "status" })[col]
			if sortKey == key then sortDesc = not sortDesc else sortKey = key; sortDesc = (key == "dkp") end
			UI.RefreshCurrent()
		end,
		onSelect = function(d) selected = d.key; UI.RefreshCurrent() end,
	})
	Place(list, page, 0, -64)
	UI.Fill(list, page)

	-- Offiziersbereich
	local px = 560
	Section(page, L["Buchung"], px, -64)
	local selLabel = Label(page, L["Kein Spieler gewählt"], px, -90)
	selLabel:SetWidth(220)

	Label(page, L["Betrag (+/-)"], px, -118, 11, true)
	local amountBox = UI.EditBox(page, 80, 24, true)
	Place(amountBox, page, px, -134)

	Label(page, L["Grund"], px, -164, 11, true)
	local reasonBox = UI.EditBox(page, 220, 24)
	Place(reasonBox, page, px, -180)

	local bookBtn = UI.Button(page, L["Buchen"], 105, 26, function()
		if not NeedOfficer() then return end
		if not selected then RM.Print(L["Bitte zuerst einen Spieler wählen."]) return end
		local amount = tonumber(amountBox:GetText())
		if not amount or amount == 0 then RM.Print(L["Bitte einen Betrag eingeben, z. B. 10 oder -5."]) return end
		local reason = reasonBox:GetText()
		local pool = ViewPool()
		UI.Confirm(string.format("%s %+d %s-DKP buchen?\nGrund: %s", selected, amount, RM.DKP.PoolName(pool), reason ~= "" and reason or L["Manuelle Anpassung"]), function()
			RM.DKP.Adjust(selected, amount, reason, pool)
			amountBox:SetText("")
			reasonBox:SetText("")
		end)
	end)
	Place(bookBtn, page, px, -214)
	bookBtn:SetAccent(true)

	local standbyBtn = UI.Button(page, L["Ersatzbank an/aus"], 110, 26, function()
		if not selected then RM.Print(L["Bitte zuerst einen Spieler wählen."]) return end
		RM.DKP.ToggleStandby(selected)
	end, L["Spieler auf der Ersatzbank bekommen beim Raidstart einmalig DKP (Standard 10), danach nichts mehr."])
	Place(standbyBtn, page, px + 110, -214)

	Section(page, L["Spieler hinzufügen"], px, -260)
	local addBox = UI.EditBox(page, 140, 24)
	Place(addBox, page, px, -286)
	local addBtn = UI.Button(page, L["Hinzufügen"], 76, 24, function()
		if not NeedOfficer() then return end
		local name = RM.DKP.AddPlayer(addBox:GetText())
		if name then addBox:SetText(""); RM.Print(name .. L[" hinzugefügt."]) end
	end)
	Place(addBtn, page, px + 144, -286)

	-- Twinks: gewählten Spieler mit seinem Main verknüpfen (Loot-Regel "Main vor Twink", Discord)
	Section(page, L["Twink von"], px, -322)
	local mainBox = UI.EditBox(page, 140, 24)
	Place(mainBox, page, px, -348)
	local linkBtn = UI.Button(page, L["Verknüpfen"], 76, 24, function()
		if not NeedOfficer() then return end
		if not selected then RM.Print(L["Bitte zuerst den Twink in der Liste wählen."]) return end
		local main = mainBox:GetText():gsub("^%s+", ""):gsub("%s+$", "")
		if main == "" then RM.Print(L["Namen des Mains eingeben."]) return end
		if RM.DKP.SetMain(selected, main) then mainBox:SetText("") end
	end, L["Der gewählte Spieler wird Twink des eingetragenen Mains.\nMain vor Twink: Twinks gewinnen nur, wenn kein Main bietet."])
	Place(linkBtn, page, px + 144, -348)
	local unlinkBtn = UI.Button(page, L["Twink lösen"], 110, 22, function()
		if not NeedOfficer() then return end
		if selected then RM.DKP.SetMain(selected, nil) end
	end)
	Place(unlinkBtn, page, px, -376)

	local myInfo = Label(page, "", px, -410, 12)
	myInfo:SetWidth(220)
	local help = Label(page, L["Spieler ohne Addon können ihren Stand per Flüstern abfragen: /w <Plündermeister> !dkp"], px, -460, 11, true)
	help:SetWidth(220)

	search:SetScript("OnTextChanged", function(self)
		if self:GetText() == "" then searchHint:Show() else searchHint:Hide() end
		UI.RefreshCurrent()
	end)

	local officerWidgets = { bookBtn, standbyBtn, addBtn, linkBtn, unlinkBtn }

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
				local status = inRaid and L["Im Raid"] or (standby and L["Ersatzbank"] or "")
				if p.m then status = (status ~= "" and (status .. " · ") or "") .. L["Twink von "] .. p.m end
				local dkpColor = value < 0 and { 1, 0.35, 0.35 } or nil
				local earned = RM.DKP.Earned(p, pool)
				rows[#rows + 1] = {
					key = name, name = name, class = class or "", dkp = value, earned = earned, status = status,
					cells = { RM.ClassColor(class, name), ClassName(class), tostring(value), status },
					colors = { nil, { 0.75, 0.75, 0.75 }, dkpColor, inRaid and { 0.5, 1, 0.5 } or { 1, 0.8, 0.3 } },
					tooltip = function(tt)
						tt:AddLine(name)
						tt:AddLine(string.format(L["%s: aktuell %d DKP"], poolName, value), 1, 1, 1, true)
						if p.m then tt:AddLine(L["Twink von "] .. p.m, 0.8, 0.8, 0.8) end
						local tw = RM.DKP.TwinksOf(name, data)
						if #tw > 0 then tt:AddLine(L["Twinks: "] .. table.concat(tw, ", "), 0.8, 0.8, 0.8, true) end
					end,
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
		local total, count = RM.DKP.PoolTotal(data, pool)
		totalLabel:SetText(string.format(L["Gesamt %s: |cffff8c1a%d DKP|r · %d Spieler"], poolName, total, count))

		local function dkpOf(n) return RM.DKP.PoolValue(data.players[n], pool) end
		if selected then
			selLabel:SetText(L["Gewählt: "] .. selected .. " (" .. dkpOf(selected) .. " " .. poolName .. L["-DKP)"] .. (RM.DKP.IsStandby(selected) and L[" – Ersatzbank"] or ""))
		else
			selLabel:SetText(L["Kein Spieler gewählt"])
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
UI.AddPage("auction", L["Versteigerung"], function(page)
	Section(page, L["Laufende Versteigerung"], 0, 0)

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

	local finishBtn = UI.Button(box, L["Jetzt beenden"], 110, 26, function()
		if RM.Auction.AwaitingAward() then RM.Auction.Award() else RM.Auction.FinishNow() end
	end)
	finishBtn:SetPoint("TOPRIGHT", -12, -12)
	local addBtn = UI.Button(box, L["+10 Sek."], 80, 26, function() RM.Auction.AddTime(10) end)
	addBtn:SetPoint("RIGHT", finishBtn, "LEFT", -6, 0)
	local cancelBtn = UI.Button(box, L["Abbrechen"], 100, 26, function()
		if RM.Auction.AwaitingAward() then RM.Auction.NoAward() return end
		UI.Confirm(L["Versteigerung abbrechen? Das Item kommt zurück in die Warteschlange."], function() RM.Auction.Cancel() end)
	end)
	cancelBtn:SetPoint("TOPRIGHT", -12, -46)
	local bidOpenBtn = UI.Button(box, L["Gebotsfenster"], 110, 26, function() RM.Auction.ShowBidFrame() end, L["Öffnet das Gebotsfenster erneut."])
	bidOpenBtn:SetPoint("RIGHT", cancelBtn, "LEFT", -6, 0)

	local bidList = UI.List(page, 790, 190, {
		{ title = L["Bieter"], width = 150 },
		{ title = L["Gebot"], width = 70, justify = "RIGHT" },
		{ title = "DKP", width = 70, justify = "RIGHT" },
		{ title = L["Trägt aktuell"], width = 450 },
	}, { emptyText = L["Noch keine Gebote."] })
	Place(bidList, page, 0, -126)

	Section(page, L["Warteschlange"], 0, -326)
	local queueFrom = Label(page, "", 160, -330, 11, true)
	queueFrom:SetWidth(360)
	local queueList
	queueList = UI.List(page, 520, 196, {
		{ title = "#", width = 24 },
		{ title = L["Item"], width = 460 },
	}, { emptyText = L["Leer. Epische Items kommen beim Öffnen des Bosses automatisch hierher."] })
	Place(queueList, page, 0, -352)

	local qx = 536
	local startBtn = UI.Button(page, L["Gewähltes starten"], 160, 28, function()
		local d = queueList:Selected()
		if not d then
			if #RM.Auction.queue > 0 then RM.Auction.Start(1) else RM.Print(L["Die Warteschlange ist leer."]) end
			return
		end
		RM.Auction.Start(d.index)
		queueList:ClearSelection()
	end, L["Startet das gewählte Item (ohne Auswahl das erste)."])
	Place(startBtn, page, qx, -352)
	startBtn:SetAccent(true)

	local removeBtn = UI.Button(page, L["Entfernen"], 160, 26, function()
		local d = queueList:Selected()
		if d then RM.Auction.Remove(d.index); queueList:ClearSelection() end
	end)
	Place(removeBtn, page, qx, -386)

	Label(page, L["Item hinzufügen (Shift-Klick auf ein Item):"], qx, -426, 11, true):SetWidth(250)
	local linkBox = UI.LinkBox(page, 250, 24)
	Place(linkBox, page, qx, -458)
	local addItemBtn = UI.Button(page, L["Zur Warteschlange"], 160, 26, function()
		local link = linkBox:GetText()
		if link and link:find("item:") then
			RM.Auction.Enqueue(link)
			linkBox:SetText("")
		else
			RM.Print(L["Bitte zuerst einen Itemlink per Shift-Klick einfügen."])
		end
	end)
	Place(addItemBtn, page, qx, -488)
	local directBtn = UI.Button(page, L["Sofort versteigern"], 160, 26, function()
		local link = linkBox:GetText()
		if link and link:find("item:") then
			RM.Auction.Start(link)
			linkBox:SetText("")
		else
			RM.Print(L["Bitte zuerst einen Itemlink per Shift-Klick einfügen."])
		end
	end)
	Place(directBtn, page, qx, -518)

	local function UpdateInfo()
		local c = RM.Auction.current
		local cl = RM.Auction.client
		if c then
			itemText:SetText(c.link)
			local rem = math.max(0, math.ceil(c.endsAt - GetTime()))
			local high = c.highName and string.format("%d DKP (%s)", c.high, c.highName) or L["noch keins"]
			if c.finished then
				infoText:SetText(L["Beendet – wartet auf Bestätigung. Höchstgebot: "] .. high)
			else
				infoText:SetText(string.format(L["Restzeit: %d Sek.  ·  Mindestgebot: %d  ·  Schritt: %d  ·  Höchstgebot: %s"], rem, c.min, c.inc, high))
			end
		elseif cl and not cl.ended then
			itemText:SetText(cl.link)
			local rem = math.max(0, math.ceil(cl.endsAt - GetTime()))
			local high = cl.highName and string.format("%d DKP (%s)", cl.high, cl.highName) or L["noch keins"]
			infoText:SetText(string.format(L["Plündermeister: %s  ·  Restzeit: %d Sek.  ·  Höchstgebot: %s"], cl.ml, rem, high))
		else
			itemText:SetText(L["|cff888888Keine laufende Versteigerung|r"])
			infoText:SetText(RM.CanEdit() and L["Wähle ein Item aus der Warteschlange oder füge eines per Shift-Klick hinzu."] or L["Sobald der Plündermeister ein Item versteigert, öffnet sich das Gebotsfenster."])
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
		local canRun = RM.Auction.CanRun() and true or false
		local isStaff = RM.CanEdit()
		local awaiting = RM.Auction.AwaitingAward()
		finishBtn:SetText(awaiting and L["Vergeben"] or L["Jetzt beenden"])
		cancelBtn:SetText(awaiting and L["Nicht vergeben"] or L["Abbrechen"])
		if awaiting then finishBtn:SetAccent(true) else finishBtn:SetAccent(false) end
		if running or awaiting then finishBtn:Enable(); cancelBtn:Enable() else finishBtn:Disable(); cancelBtn:Disable() end
		if running then addBtn:Enable() else addBtn:Disable() end
		if RM.Auction.client and not RM.Auction.client.ended then bidOpenBtn:Enable() else bidOpenBtn:Disable() end
		for _, b in ipairs({ startBtn, removeBtn, addItemBtn, directBtn }) do
			if canRun then b:Enable() else b:Disable() end
		end
		-- normale Teilnehmer bieten nur: Steuerung der Versteigerung ausblenden
		-- (Offiziere sehen sie, starten kann aber nur der Plündermeister)
		for _, b in ipairs({ startBtn, removeBtn, addItemBtn, directBtn, finishBtn, addBtn, cancelBtn }) do
			if canRun or isStaff then b:Show() else b:Hide() end
		end

		local rows = {}
		for _, b in ipairs(RM.Auction.BidList()) do
			local gear = b.gear or ""
			local gearLinks = {}
			for l in gear:gmatch("|c%x+|Hitem:.-|h.-|h|r") do gearLinks[#gearLinks + 1] = l end
			rows[#rows + 1] = {
				key = b.name,
				cells = { b.name, b.pass and L["Passt"] or tostring(b.amount), tostring(RM.DKP.Get(b.name, RM.Auction.current and RM.Auction.current.pool)), table.concat(gearLinks, "  ") },
				colors = { nil, b.pass and { 0.6, 0.6, 0.6 } or { 1, 0.8, 0.3 } },
				tooltip = (#gearLinks > 0) and function(tt)
					tt:SetHyperlink(RM.ItemString(gearLinks[1]) or gearLinks[1])
				end or nil,
			}
		end
		bidList:SetData(rows)

		local qrows = {}
		local list, from = RM.Auction.ViewQueue()
		for i, q in ipairs(list) do
			qrows[#qrows + 1] = { key = i .. q.link, index = i, link = q.link, cells = { tostring(i), q.link } }
		end
		queueList:SetData(qrows)
		queueFrom:SetText(from and string.format(L["vom Plündermeister %s"], from) or "")
		if from then startBtn:Disable(); removeBtn:Disable() end
		if not canRun and isStaff and not from then
			local _, why = RM.Auction.CanRun()
			queueFrom:SetText(why or "")
		end
	end
end)

---------------------------------------------------------------------------
-- Seite: Loot
---------------------------------------------------------------------------
UI.AddPage("loot", L["Loot"], function(page)
	local cfg = function() return RM.db.config end
	local refreshers = {}

	Section(page, L["Loot-Regeln"], 0, 0)
	local rules = {
		{ key = "epic", label = L["Epische Ausrüstung"], opts = { { "auction", L["Versteigerung"] }, { "manual", L["Manuell"] } } },
		{ key = "blue", label = L["Blaue Ausrüstung"], opts = { { "auction", L["Versteigerung"] }, { "de", L["Entzauberer"] }, { "bank", L["Gildenbank"] }, { "manual", L["Manuell"] } } },
		{ key = "recipe", label = L["Rezepte und Pläne"], opts = { { "bank", L["Gildenbank"] }, { "crafter", L["Handwerker"] }, { "auction", L["Versteigerung"] }, { "manual", L["Manuell"] } } },
		{ key = "mats", label = L["Handwerksmaterialien"], opts = { { "bank", L["Gildenbank"] }, { "crafter", L["Handwerker"] }, { "auction", L["Versteigerung"] }, { "manual", L["Manuell"] } } },
	}
	local y = -28
	for _, r in ipairs(rules) do
		Label(page, r.label, 0, y - 5)
		local cyc = UI.Cycle(page, 150, r.opts, function() return cfg().rules[r.key] end, function(v) cfg().rules[r.key] = v end)
		Place(cyc, page, 170, y)
		refreshers[#refreshers + 1] = cyc
		y = y - 30
	end
	Label(page, L["Legendäre Items"], 0, y - 5)
	Label(page, L["immer nur Hinweis"], 170, y - 5, 12, true)
	y = y - 30
	Label(page, L["Keine Gebote"], 0, y - 5)
	local fb = UI.Cycle(page, 150, { { "de", L["Entzauberer"] }, { "bank", L["Gildenbank"] }, { "manual", L["Manuell"] } },
		function() return cfg().fallback end, function(v) cfg().fallback = v end)
	Place(fb, page, 170, y)
	refreshers[#refreshers + 1] = fb
	y = y - 40

	Section(page, L["Empfänger"], 0, y)
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
	NameField(L["Gildenbank-Charakter"], "bankChar", y); y = y - 30
	-- Entzauberer und Handwerker per Menü aus dem Raid wählen (wie der Plündermeister)
	local function RecipientDrop(label, key, yy, tip)
		Label(page, label, 0, yy - 5)
		local d = UI.Dropdown(page, 150, function() return RM.Loot.RecipientChoices(key) end,
			function() return cfg()[key] or "" end, function(v) cfg()[key] = v; UI.RefreshCurrent() end, tip)
		Place(d, page, 170, yy)
		refreshers[#refreshers + 1] = d
	end
	RecipientDrop(L["Entzauberer"], "deChar", y, L["Bekommt Items, auf die niemand bietet (wenn eingestellt), und blaue Items mit Regel Entzauberer."]); y = y - 30
	RecipientDrop(L["Handwerker"], "crafterChar", y, L["Bekommt Rezepte und Materialien mit Regel Handwerker."]); y = y - 40

	Section(page, L["Plündermeister"], 0, y)
	y = y - 28
	Label(page, L["Plündermeister"], 0, y - 5)
	local mlDrop = UI.Dropdown(page, 150, function() return RM.Loot.MasterChoices() end,
		function() return cfg().lootMaster or "" end, function(v) RM.Loot.SetMaster(v) end,
		L["Plündermeister wählen – als Raidleiter wird die Plündermethode im Spiel sofort umgestellt."])
	Place(mlDrop, page, 170, y)
	refreshers[#refreshers + 1] = mlDrop
	y = y - 30
	Label(page, L["Plünderschwelle"], 0, y - 5)
	local th = UI.Cycle(page, 150, { { 2, L["Selten (grün)"] }, { 3, L["Rar (blau)"] }, { 4, L["Episch (lila)"] } },
		function() return cfg().lootThreshold end, function(v) RM.Loot.SetThreshold(v) end,
		L["Empfohlen: Selten (grün) – der Plündermeister verteilt dann schon grüne Items, Kerne und Rezepte sowieso."])
	Place(th, page, 170, y)
	refreshers[#refreshers + 1] = th
	y = y - 32
	local applyBtn = UI.Button(page, L["Jetzt anwenden"], 150, 26, function() RM.Loot.ApplySettings() end, L["Setzt Plündermeister und Schwelle (nur Raidleiter)."])
	Place(applyBtn, page, 170, y)
	y = y - 30
	local autoLootCheck = UI.Check(page, L["Vergessenen Plündermeister automatisch setzen"], function() return cfg().autoLoot end,
		function(v) cfg().autoLoot = v; if v then RM.Loot.EnsureSettings() end end,
		L["Als Raidleiter: steht die Plündermethode nicht auf Plündermeister, setzt RaidMaster den gespeicherten Plündermeister und die Schwelle."])
	Place(autoLootCheck, page, 0, y)
	refreshers[#refreshers + 1] = autoLootCheck

	-- Optionen
	local ox = 350
	Section(page, L["Optionen"], ox, 0)
	local checks = {
		{ "setLootOnStart", L["Loot-Einstellungen bei Raidstart setzen"] },
		{ "autoDistribute", L["Mats/Rezepte/Blaues automatisch zuteilen"] },
		{ "announceLoot", L["Loot gesammelt im Raidchat ansagen"] },
		{ "announceBids", L["Gebote im Raidchat ansagen"] },
		{ "unlootedReminder", L["Erinnern, wenn Boss nicht geplündert"] },
		{ "tradeFallback", L["Bei Abwesenheit an mich + Handelsliste"] },
		{ "whisperReplies", L["Auf !dkp-Flüstern antworten"] },
	}
	local cy = -30
	for _, c in ipairs(checks) do
		local cb = UI.Check(page, c[2], function() return cfg()[c[1]] end, function(v) cfg()[c[1]] = v end)
		Place(cb, page, ox, cy)
		refreshers[#refreshers + 1] = cb
		cy = cy - 26
	end

	Section(page, L["Offene Zuteilungen und Handel"], ox, -248)
	local openList = UI.List(page, 440, 160, {
		{ title = L["Item"], width = 200 },
		{ title = L["Spieler"], width = 90 },
		{ title = L["Art"], width = 120 },
	}, { emptyText = L["Nichts offen."] })
	Place(openList, page, ox, -274)
	local removeOpen = UI.Button(page, L["Entfernen"], 100, 24, function()
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
	Label(page, L["Handel: Öffne einfach ein Handelsfenster mit dem Spieler – seine Items werden automatisch eingelegt."], ox + 108, -440, 11, true):SetWidth(330)

	Section(page, L["Aktuelles Lootfenster"], ox, -480)
	local lootInfo = Label(page, "", ox, -504, 11, true)
	lootInfo:SetWidth(440)

	return function()
		for _, r in ipairs(refreshers) do r:Refresh() end
		local rows = {}
		for i, p in ipairs(RM.db.pendingAwards) do
			rows[#rows + 1] = { key = "p" .. i .. p.link, kind = "pending", index = i, link = p.link, cells = { p.link, p.name, L["Boss erneut öffnen"] }, colors = { nil, nil, { 1, 0.8, 0.3 } } }
		end
		for i, t in ipairs(RM.db.trade) do
			rows[#rows + 1] = { key = "t" .. i .. t.link, kind = "trade", index = i, link = t.link, cells = { t.link, t.name, L["Handeln"] }, colors = { nil, nil, { 0.5, 0.8, 1 } } }
		end
		openList:SetData(rows)

		if RM.Loot.isOpen and #RM.Loot.items > 0 then
			local parts = {}
			for _, it in ipairs(RM.Loot.items) do
				parts[#parts + 1] = it.link .. " – " .. (RM.Loot.ActionNames[it.action] or it.action) .. (it.done and L[" (erledigt)"] or "")
			end
			lootInfo:SetText(table.concat(parts, "\n"))
		elseif RM.Loot.isOpen then
			lootInfo:SetText(L["Geöffnet – keine Items über der Schwelle."])
		else
			lootInfo:SetText(L["Kein Lootfenster geöffnet."])
		end
	end
end)

---------------------------------------------------------------------------
-- Seite: Log
---------------------------------------------------------------------------
UI.AddPage("log", L["Log"], function(page)
	local filterKind = "all"
	Section(page, L["Buchungsprotokoll"], 0, 0)
	local poolCycle = PoolCycle(page, 180, 4, 240, true)

	local filter = UI.Cycle(page, 150, {
		{ "all", L["Alle Buchungen"] }, { "boss", L["Bosskills"] }, { "item", L["Items"] }, { "manual", L["Anpassungen"] },
		{ "raid", L["Raidstart/-ende"] }, { "decay", L["Decay"] }, { "undo", L["Rückgängig"] },
	}, function() return filterKind end, function(v) filterKind = v; UI.RefreshCurrent() end)
	Place(filter, page, 0, -28)

	local search = UI.EditBox(page, 160, 24)
	Place(search, page, 160, -28)
	local viewCycle = ViewCycle(page, 330, -28)
	local hint = UI.Text(search, L["Spieler suchen ..."], 11, unpack(COLORS.muted))
	hint:SetPoint("LEFT", 8, 0)
	search:SetScript("OnTextChanged", function(self)
		if self:GetText() == "" then hint:Show() else hint:Hide() end
		UI.RefreshCurrent()
	end)

	local list = UI.List(page, 790, 456, {
		{ title = L["Zeit"], width = 80 },
		{ title = L["Von"], width = 85 },
		{ title = L["Raid"], width = 64 },
		{ title = L["Art"], width = 74 },
		{ title = L["Beschreibung"], width = 266 },
		{ title = L["Betrag"], width = 70, justify = "RIGHT" },
		{ title = L["Spieler"], width = 70, justify = "RIGHT" },
	}, { emptyText = L["Noch keine Buchungen."] })
	Place(list, page, 0, -60)
	UI.Fill(list, page, true)

	local undoBtn = UI.Button(page, L["Rückgängig"], 120, 26, function()
		if not NeedOfficer() then return end
		local d = list:Selected()
		if not d then RM.Print(L["Bitte zuerst eine Buchung wählen."]) return end
		UI.Confirm(L["Diese Buchung rückgängig machen?\n"] .. (d.desc or ""), function() RM.DKP.Undo(d.key) end)
	end, L["Erstellt eine Gegenbuchung. Nichts wird gelöscht."])
	UI.PlaceBottom(undoBtn, page, 0, -526)

	local exportBtn = UI.Button(page, L["Export"], 100, 26, function() UI.ShowExport(RM.DKP.ExportText()) end)
	UI.PlaceBottom(exportBtn, page, 128, -526)

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
						desc .. (e.u and L[" (rückgängig)"] or ""),
						count == 1 and string.format("%+d", amount or 0) or (uniform and string.format(L["%+d je"], amount or 0) or "versch."),
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
UI.AddPage("raid", L["Raid"], function(page)
	Section(page, L["Raid-Sitzung"], 0, 0)
	local sessionText = Label(page, "", 0, -28)
	sessionText:SetWidth(380)

	local startBtn = UI.Button(page, L["Raid starten"], 140, 30, function()
		if not NeedOfficer() then return end
		UI.Confirm(L["Raid starten?\nAlle Raidmitglieder (und die Ersatzbank) erhalten den Pünktlichkeitsbonus."], function() RM.Raid.Start() end)
	end)
	Place(startBtn, page, 0, -70)
	startBtn:SetAccent(true)

	local endBtn = UI.Button(page, L["Raid beenden"], 140, 30, function()
		UI.Confirm(L["Raid beenden?\nAlle Raidmitglieder (und die Ersatzbank) erhalten den Abschlussbonus."], function() RM.Raid.End() end)
	end)
	Place(endBtn, page, 150, -70)

	Label(page, L["DKP-Topf"], 0, -115)
	local raidPool = UI.Dropdown(page, 220, function() return UI.PoolGroups(RM.db.data) end, function()
		local s = RM.db.session
		return (s.active and s.pool) or RM.DKP.CurrentInstancePool() or RM.db.config.activePool or "mc"
	end, function(v)
		RM.db.config.activePool = v
		if RM.db.session.active then RM.db.session.pool = v end
		RM.DKP.MapCurrentInstance(v)
		RM.Fire("SESSION_CHANGED")
	end, L["Für welchen Raid Start-/Endbonus und Versteigerungen gebucht werden.\n"]
		.. L["In einer Raid-Instanz wird der Topf automatisch erkannt. Wählst du hier etwas anderes, merkt sich RaidMaster das für diese Instanz."])
	Place(raidPool, page, 75, -110)
	local poolHint = Label(page, "", 0, -140, 11, true)
	poolHint:SetWidth(390)

	local killsText = Label(page, "", 0, -166, 11, true)
	killsText:SetWidth(380)

	Section(page, L["Raid-Check"], 0, -230)
	local checkBtn = UI.Button(page, L["Jetzt prüfen"], 120, 26, function() RM.Raid.RunCheck() end,
		L["Prüft Plündermethode, Schwelle, Rechte und welche Spieler das Addon haben."])
	Place(checkBtn, page, 0, -256)
	local checkText = Label(page, L["Noch nicht geprüft."], 0, -290, 11)
	checkText:SetWidth(390)

	-- Bereitschafts-Check, Pull- und Pausen-Timer (auch in der Boss-Leiste)
	local cfg = function() return RM.db.config end
	Section(page, L["Bereitschaft und Timer"], 0, -392)
	local readyBtn = UI.Button(page, L["Bereitschaft prüfen"], 150, 26, function() RM.Ready.Start() end,
		L["Fläschchen und Elixiere (alle), dazu Feuerwiderstand, Reagenzien und Haltbarkeit (mit RaidMaster).\nWeltbuffs werden nicht geprüft."])
	Place(readyBtn, page, 0, -418)
	local pullBtn = UI.Button(page, L["Pull-Timer"], 100, 26, function()
		if RM.Timer.Running("pull") then RM.Timer.Cancel() else RM.Timer.Pull() end
	end, L["Pull-Timer mit Countdown – auch für Deadly Boss Mods und BigWigs. Nochmal klicken bricht ab."])
	Place(pullBtn, page, 156, -418)
	local pullSec = UI.Cycle(page, 80, { { 5, "5 s" }, { 8, "8 s" }, { 10, "10 s" }, { 15, "15 s" }, { 20, "20 s" } },
		function() return cfg().pullSeconds or 10 end, function(v) cfg().pullSeconds = v; RM.Fire("TIMER_CHANGED") end)
	Place(pullSec, page, 262, -418)
	-- Pausen: Knöpfe rechts unter "Pause" (gehen jetzt auch an DBM/BigWigs); Boss-Leiste: "Pause" = so viele Minuten
	local breakMin = UI.Cycle(page, 150, { { 3, L["Leiste: Pause 3 min"] }, { 5, L["Leiste: Pause 5 min"] }, { 10, L["Leiste: Pause 10 min"] }, { 15, L["Leiste: Pause 15 min"] } },
		function() return cfg().breakMinutes or 5 end, function(v) cfg().breakMinutes = v; RM.Fire("TIMER_CHANGED") end)
	Place(breakMin, page, 0, -450)
	local addons = UI.Cycle(page, 140, { { "both", L["DBM + BigWigs"] }, { "dbm", L["nur DBM"] }, { "bigwigs", L["nur BigWigs"] }, { "none", L["ohne Boss-Addons"] } },
		function() return cfg().timerAddons or "both" end, function(v) cfg().timerAddons = v end,
		L["An welche Boss-Addons die Timer gehen (Pull und Pause)."])
	Place(addons, page, 156, -450)
	local chatCheck = UI.Check(page, L["Countdown 5-4-3-2-1 im Raidchat"], function() return cfg().pullCountdownChat ~= false end,
		function(v) cfg().pullCountdownChat = v end)
	Place(chatCheck, page, 0, -482)
	local welcomeCheck = UI.Check(page, L["Begrüßung beim Raidstart"], function() return cfg().welcome ~= false end,
		function(v) cfg().welcome = v end,
		L["Begrüßt den Raid im Raidchat, passend zur Raidzone. Gäste und Spieler von der Ersatzbank werden mit Namen begrüßt."])
	Place(welcomeCheck, page, 0, -510)
	local frCycle = UI.Cycle(page, 150, { { 0, L["Feuerwid. egal"] }, { 100, L["Feuerwid. ab 100"] }, { 150, L["Feuerwid. ab 150"] },
		{ 200, L["Feuerwid. ab 200"] }, { 250, L["Feuerwid. ab 250"] } },
		function() return tonumber(cfg().fireResMin) or 0 end, function(v) cfg().fireResMin = v end,
		L["Ab wie viel Feuerwiderstand der Bereitschafts-Check zufrieden ist (z. B. für Ragnaros)."])
	Place(frCycle, page, 240, -482)

	-- rechte Spalte
	local rx = 410
	Section(page, L["Ersatzbank"], rx, 0)
	local sbList = UI.List(page, 230, 200, { { title = L["Name"], width = 200 } }, { emptyText = L["Niemand auf der Ersatzbank."] })
	Place(sbList, page, rx, -26)
	local sbBox = UI.EditBox(page, 140, 24)
	Place(sbBox, page, rx + 240, -26)
	local sbAdd = UI.Button(page, L["Hinzufügen"], 130, 24, function()
		local n = CapName(sbBox:GetText())
		if n ~= "" and not RM.DKP.IsStandby(n) then RM.DKP.ToggleStandby(n) end
		sbBox:SetText("")
	end)
	Place(sbAdd, page, rx + 240, -56)
	local sbRemove = UI.Button(page, L["Entfernen"], 130, 24, function()
		local d = sbList:Selected()
		if d then RM.DKP.ToggleStandby(d.key); sbList:ClearSelection() end
	end)
	Place(sbRemove, page, rx + 240, -86)
	local sbClear = UI.Button(page, L["Alle entfernen"], 130, 24, function()
		UI.Confirm(L["Ersatzbank leeren?"], function() wipe(RM.db.config.standby); RM.Fire("DATA_CHANGED") end)
	end)
	Place(sbClear, page, rx + 240, -116)

	Section(page, L["Pausen-Timer"], rx, -246)
	local px = rx
	for _, m in ipairs({ 2, 5, 10, 15 }) do
		local b = UI.Button(page, m .. L[" Min."], 70, 26, function() RM.Raid.StartPause(m * 60) end)
		Place(b, page, px, -272)
		px = px + 76
	end
	local stopBtn = UI.Button(page, L["Pause beenden"], 120, 26, function() RM.Raid.StopPause() end)
	Place(stopBtn, page, rx, -304)

	Section(page, L["Decay"], rx, -350)
	local decayText = Label(page, "", rx, -376, 11)
	decayText:SetWidth(370)
	local decayBtn = UI.Button(page, L["Decay anwenden"], 140, 26, function()
		if not NeedOfficer() then return end
		local pct = RM.db.data.settings.decayPct
		UI.Confirm(string.format(L["Wöchentlichen Decay anwenden?\nAlle positiven DKP in allen Raid-Töpfen werden um %d %% reduziert."], pct), function() RM.DKP.ApplyDecay() end)
	end)
	Place(decayBtn, page, rx, -416)
	local autoDecay = UI.Check(page, L["Automatisch jeden Mittwoch (Raid-Reset)"], function() return RM.db.data.settings.autoDecay ~= false end,
		function(v)
			if not NeedOfficer() then return end
			RM.db.data.settings.autoDecay = v
			RM.DKP.SettingsChanged()
		end, L["Einmal pro Woche nach dem Raid-Reset bucht der erste Offizier, der online ist, den Verfall auf alle Raids – nie während eines Raids."])
	Place(autoDecay, page, rx + 150, -420)

	Section(page, L["Kernhunde"], rx, -462)
	local houndCheck = UI.Check(page, L["Kürschner ansagen, wenn ein Kernhund stirbt"],
		function() return RM.db.config.coreHound end, function(v) RM.db.config.coreHound = v end,
		L["Der Raidleiter sagt die Kürschner mit Addon im Raid an (nach Skill sortiert)."])
	Place(houndCheck, page, rx, -488)

	return function()
		local s = RM.db.session
		if s.active then
			sessionText:SetText(string.format(L["|cff40ff40Raid läuft seit %s.|r\nBosse werden automatisch erkannt und gebucht."], date("%H:%M", s.started)))
			startBtn:Disable()
			endBtn:Enable()
		else
			sessionText:SetText(s.ended and (L["Kein Raid aktiv. Letzter Raid beendet: "] .. RM.FormatTime(s.ended)) or L["Kein Raid aktiv."])
			if RM.CanEdit() then startBtn:Enable() else startBtn:Disable() end
			endBtn:Disable()
		end
		raidPool:Refresh()
		local inst = RM.DKP.CurrentInstancePool()
		if inst then
			poolHint:SetText(L["Erkannt in dieser Instanz: |cffff8c1a"] .. RM.DKP.PoolName(inst) .. "|r")
		else
			poolHint:SetText(L["Außerhalb einer Raid-Instanz – der gewählte Topf gilt."])
		end
		local kills = {}
		local list = {}
		for id, t in pairs(s.kills or {}) do list[#list + 1] = { id = id, t = t } end
		table.sort(list, function(a, b) return a.t < b.t end)
		for _, k in ipairs(list) do
			local b = RM.Data.Bosses[k.id]
			local name = (b and b.name) or (s.names and s.names[k.id]) or (L["Boss "] .. k.id)
			kills[#kills + 1] = "|cff40ff40" .. name .. "|r (" .. date("%H:%M", k.t) .. ")"
		end
		killsText:SetText(#kills > 0 and (L["Besiegt: "] .. table.concat(kills, ", ")) or (s.active and L["Noch kein Boss besiegt."] or ""))

		if #RM.Raid.lastCheck > 0 then checkText:SetText(table.concat(RM.Raid.lastCheck, "\n")) end

		local rows = {}
		for name in pairs(RM.db.config.standby) do rows[#rows + 1] = { key = name, cells = { RM.ClassColor(RM.guild.class[name], name) } } end
		table.sort(rows, function(a, b) return a.key < b.key end)
		sbList:SetData(rows)

		local last = RM.db.data.lastDecay or 0
		local pct = RM.db.data.settings.decayPct
		local nextText = (RM.db.data.settings.autoDecay ~= false)
			and string.format(L["\nAutomatisch %d %% – nächster Verfall: %s"], pct, date("%d.%m. %H:%M", RM.DKP.NextDecay())) or ""
		if last > 0 then
			local days = math.floor((GetServerTime() - last) / 86400)
			local color = days >= 7 and "|cffff6040" or "|cffcccccc"
			decayText:SetText(string.format("%sLetzter Decay: %s (vor %d Tagen).|r Einstellung: %d %% pro Anwendung.", color, RM.FormatTime(last), days, pct) .. nextText)
		else
			decayText:SetText(string.format(L["Noch kein Decay angewendet. Einstellung: %d %% pro Anwendung."], pct) .. nextText)
		end
		autoDecay:Refresh(); chatCheck:Refresh(); welcomeCheck:Refresh(); pullSec:Refresh(); breakMin:Refresh(); addons:Refresh(); frCycle:Refresh()
		pullBtn:SetText(RM.Timer.Running("pull") and L["Pull abbrechen"] or L["Pull-Timer"])
		if RM.CanEdit() then decayBtn:Enable() else decayBtn:Disable() end
		houndCheck:Refresh()
	end
end)

---------------------------------------------------------------------------
-- Seite: Anmeldungen (aus Discord)
---------------------------------------------------------------------------
UI.AddPage("signup", L["Anmeldungen"], function(page)
	Section(page, L["Raidanmeldungen aus Discord"], 0, 0)
	local info = Label(page, "", 0, -26, 12)
	info:SetWidth(520)

	local list = UI.List(page, 520, 316, {
		{ title = L["Name"], width = 115 },
		{ title = L["Klasse"], width = 75 },
		{ title = L["Rolle"], width = 75 },
		{ title = L["Status"], width = 90 },
		{ title = L["Im Raid"], width = 95 },
		{ title = L["Grp."], width = 40, justify = "CENTER" },
	}, { emptyText = L["Noch nichts importiert."] })
	Place(list, page, 0, -50)

	local summary = Label(page, "", 0, -374, 11)
	summary:SetWidth(520)

	-- Lücken füllen: fehlende Tanks/Heiler/Klassen aus Ersatzbank, Gilde oder Gruppensuche
	local gapsBtn = UI.Button(page, L["Lücken füllen ..."], 200, 28, function() if RM.Gaps then RM.Gaps.Open() end end,
		L["Zeigt, welche Rollen und Klassen fehlen, und füllt sie per Klick:\nzuerst Angemeldete, dann passende Ersatzbank, dann Gilde, zuletzt Gruppensuche."])
	Place(gapsBtn, page, 0, -444)
	gapsBtn:SetAccent(true)
	local gapsInfo = Label(page, "", 210, -451, 11, true)
	gapsInfo:SetWidth(310)

	-- rechte Spalte: Import und Aktionen
	local rx = 540
	Section(page, L["Importieren"], rx, 0)
	Label(page, L["Im Discord beim Raid auf 'Für RaidMaster' klicken, den Text kopieren und hier einfügen (Strg+V)."], rx, -26, 11, true):SetWidth(245)
	local box = UI.Multiline(page, 245, 150)
	Place(box, page, rx, -64)
	local importBtn = UI.Button(page, L["Übernehmen"], 120, 26, function()
		if RM.Signup.Import(box.edit:GetText()) then
			box:SetText("")
			box.edit:ClearFocus()
		end
	end)
	Place(importBtn, page, rx, -220)
	importBtn:SetAccent(true)
	local clearBtn = UI.Button(page, L["Liste leeren"], 120, 26, function()
		UI.Confirm(L["Importierte Anmeldungen löschen?"], function() RM.Signup.Clear() end)
	end)
	Place(clearBtn, page, rx + 125, -220)

	Section(page, L["Aktionen"], rx, -266)
	-- nur im Testmodus: Testraid leeren (alle simuliert Eingeladenen raus, die Anmeldungen bleiben)
	local testClearBtn = UI.Button(page, L["Testraid leeren"], 245, 26, function()
		if RM.Test and RM.Test.active then RM.Test.ClearRoster() end
	end, L["Nur im Testmodus: alle Testspieler verlassen den Raid. Die Anmeldungen bleiben – danach erneut einladen."])
	Place(testClearBtn, page, rx, -256)
	testClearBtn:Hide()
	local inviteBtn = UI.Button(page, L["Angemeldete einladen"], 245, 28, function() RM.Signup.InviteAll(false) end,
		L["Lädt alle Angemeldeten ein, die noch nicht in der Gruppe sind.\nAus einer Gruppe wird automatisch ein Schlachtzug."])
	Place(inviteBtn, page, rx, -292)
	local inviteAllBtn = UI.Button(page, L["Inkl. Ersatzbank einladen"], 245, 26, function() RM.Signup.InviteAll(true) end)
	Place(inviteAllBtn, page, rx, -326)
	local stopBtn = UI.Button(page, L["Einladen stoppen"], 245, 26, function() RM.Signup.StopInvites() end)
	Place(stopBtn, page, rx, -358)
	local benchBtn = UI.Button(page, L["Ersatzbank übernehmen"], 245, 26, function() RM.Signup.ApplyStandby() end,
		L["Trägt alle Discord-Ersatzbank-Anmeldungen in die DKP-Ersatzbank ein (Seite Raid)."])
	Place(benchBtn, page, rx, -390)
	local groupBtn = UI.Button(page, L["Gruppen einteilen"], 245, 26, function() RM.Signup.ArrangeGroups() end,
		L["Übernimmt die Gruppen aus Discord (/raid aufstellung). Wer nicht in der Aufstellung steht, kommt auf den Platz\neines Fehlenden derselben Art (Heiler für Heiler, Magier für Magier). Ohne Aufstellung: dieselbe Classic-Einteilung\nwie im Discord. Main-/Offtank immer in Gruppe 1. Nur außerhalb des Kampfes."])
	Place(groupBtn, page, rx, -422)

	local autoInv = UI.Check(page, L["Auto-Einladung"], function() return RM.db.config.autoInvite end,
		function(v) RM.db.config.autoInvite = v; UI.RefreshCurrent() end,
		L["Lädt automatisch alle Aufgestellten ein, sobald der Raid öffnet, und Nachzügler bis 30 Min. nach Beginn.\nDein Spiel muss dafür laufen."])
	Place(autoInv, page, rx, -458)
	local minutes = UI.Cycle(page, 90, { { 5, L["5 Min."] }, { 10, L["10 Min."] }, { 15, L["15 Min."] }, { 20, L["20 Min."] }, { 30, L["30 Min."] } },
		function() return RM.db.config.autoInviteMinutes or 15 end, function(v) RM.db.config.autoInviteMinutes = v; UI.RefreshCurrent() end,
		L["So viele Minuten vor Raidbeginn öffnet der Raid."])
	Place(minutes, page, rx + 150, -454)
	local autoGrp = UI.Check(page, L["Gruppen automatisch sortieren"], function() return RM.db.config.autoGroups end,
		function(v) RM.db.config.autoGroups = v end, L["Jeder, der dem Raid beitritt, kommt sofort in seine feste Gruppe."])
	Place(autoGrp, page, rx, -486)
	local autoState = Label(page, "", rx, -512, 11, true)
	autoState:SetWidth(245)

	local STATUS_COLORS = {
		an = { 0.4, 1, 0.4 }, ersatz = { 1, 0.8, 0.3 }, vielleicht = { 0.6, 0.75, 1 }, ab = { 1, 0.4, 0.4 },
	}
	local ORDER = { an = 1, ersatz = 2, vielleicht = 3, ab = 4 }

	return function()
		if RM.Test and RM.Test.active then testClearBtn:Show() else testClearBtn:Hide() end
		if RM.Gaps then
			local ok, plan = pcall(RM.Gaps.Plan)
			if ok and plan then
				gapsInfo:SetText(plan.complete and ("|cff66ff66" .. L["Aufstellung komplett"] .. "|r")
					or ("|cffffcc00" .. L["Fehlt:"] .. "|r " .. RM.Gaps.NeedsText(plan.needs)))
			else
				gapsInfo:SetText("")
			end
		end
		local su = RM.db.signup
		if su then
			info:SetText(string.format("|cffff8c1a%s|r  ·  %s  ·  importiert %s", su.title ~= "" and su.title or L["Raid"], su.date or "", RM.FormatTime(su.imported or 0)))
		else
			info:SetText(L["Noch keine Anmeldungen importiert."])
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
			local group = r.inRaid and (r.online and "dabei" or "offline") or (r.state and RM.Signup.STATE_TEXT[r.state]) or "-"
			local grp = su and su.groups and su.groups[e.name]
			local grpText = grp and tostring(grp) or ((su and su.bench and su.bench[e.name]) and L["Bank"] or "")
			data[#data + 1] = {
				key = e.name,
				cells = { RM.ClassColor(e.cls, e.name), ClassName(e.cls), RM.Signup.ROLE[e.role] or e.role,
					RM.Signup.STATUS[e.status] or e.status, group, grpText },
				colors = { nil, { 0.75, 0.75, 0.75 }, { 0.75, 0.75, 0.75 }, STATUS_COLORS[e.status],
					r.inRaid and (r.online and { 0.4, 1, 0.4 } or { 1, 0.8, 0.3 })
						or ((r.state == "notfound" or r.state == "declined" or r.state == "ingroup") and { 1, 0.4, 0.4 })
						or (r.state == "invited" and { 0.6, 0.75, 1 }) or { 0.5, 0.5, 0.5 } },
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
			local lines = { RM.Signup.CapacityText(), string.format("Angemeldet: %d  ·  davon in der Gruppe: %d", signed, present) }
			if #missing > 0 then lines[#lines + 1] = L["|cffffcc00Fehlen noch:|r "] .. table.concat(missing, ", ") end
			if #extra > 0 then lines[#lines + 1] = L["|cff99bbffIn der Gruppe ohne Anmeldung:|r "] .. table.concat(extra, ", ") end
			summary:SetText(table.concat(lines, "\n"))
		else
			summary:SetText("")
		end

		local inviting = RM.Signup.IsInviting()
		for _, b in ipairs({ inviteBtn, inviteAllBtn, benchBtn }) do
			if su and not inviting then b:Enable() else b:Disable() end
		end
		if inviting then stopBtn:Enable() else stopBtn:Disable() end
		if next(RM.Signup.WantedGroups()) then groupBtn:Enable() else groupBtn:Disable() end
		autoInv:Refresh()
		autoGrp:Refresh()
		minutes:Refresh()
		autoState:SetText(L["Auto-Einladung: "] .. RM.Signup.AutoInviteState())
	end
end)

---------------------------------------------------------------------------
-- Seite: PUG-Raid (kein DKP, Loot über softres.it)
---------------------------------------------------------------------------
UI.AddPage("pug", L["PUG-Raid"], function(page)
	local PUG = RM.PUG
	local cfg = function() return RM.db.config end
	Section(page, L["PUG-Raid"], 0, 0)
	local status = Label(page, "", 0, -26, 12)
	status:SetWidth(780)
	Label(page, L["Im PUG-Raid gibt es keine DKP und keine Versteigerung. Soft Reserve und Würfeln laufen über softres.it – "]
		.. L["der Plündermeister verteilt den Loot nach der softres.it-Liste."], 0, -50, 11, true):SetWidth(780)

	Section(page, "softres.it", 0, -96)
	Label(page, L["Link"], 0, -126)
	local linkBox = UI.EditBox(page, 520, 24)
	Place(linkBox, page, 60, -122)
	linkBox:SetScript("OnTextChanged", function(self, user)
		if user then cfg().softresLink = self:GetText(); UI.RefreshCurrent() end
	end)
	Label(page, L["z. B. https://softres.it/raid/abcd – wird beim Import eines PUG-Raids aus Discord automatisch übernommen."], 60, -150, 11, true):SetWidth(720)
	local postBtn = UI.Button(page, L["Link im Raid posten"], 185, 26, function() PUG.AnnounceSoftres(true) end,
		L["Postet den softres.it-Link als Schlachtzugswarnung."])
	Place(postBtn, page, 0, -180)

	Section(page, L["Leitung"], 0, -230)
	local startBtn = UI.Button(page, L["PUG-Raid starten"], 185, 28, function()
		UI.Confirm(L["PUG-Raid starten?\nKein DKP, keine Versteigerung – Loot über softres.it."], function() PUG.Start() end)
	end, L["Raidleiter, Assistent oder Plündermeister."])
	Place(startBtn, page, 0, -256)
	startBtn:SetAccent(true)
	local stopBtn = UI.Button(page, L["PUG-Raid beenden"], 185, 28, function()
		UI.Confirm(L["PUG-Raid beenden?"], function() PUG.Stop() end)
	end)
	Place(stopBtn, page, 195, -256)
	Label(page, L["Werbung für den Raid: Seite \"Werbung\"."], 0, -296, 11, true):SetWidth(380)

	return function()
		local v = PUG.view
		if v.active then
			status:SetText(string.format("|cff40ff40PUG-Raid aktiv|r – Leiter: %s", v.leader or "?"))
		else
			status:SetText(L["Kein PUG-Raid aktiv. Der Raidleiter startet ihn unten unter 'Leitung'."])
		end
		if not linkBox:HasFocus() then linkBox:SetText(cfg().softresLink or "") end
		local lead = PUG.IsLeader()
		if PUG.CanLead() and not lead then startBtn:Enable() else startBtn:Disable() end
		if lead then stopBtn:Enable() else stopBtn:Disable() end
		if (cfg().softresLink or "") ~= "" and RM.InRaid() then postBtn:Enable() else postBtn:Disable() end
	end
end)

---------------------------------------------------------------------------
-- Seite: Einteilung (Heilung, Entfluchen, CC)
---------------------------------------------------------------------------
UI.AddPage("ad", L["Werbung"], function(page)
	local Ad = RM.Ad
	local cfg = function() return RM.db.config end

	Section(page, L["Werbung im offenen Chat"], 0, 0)
	Label(page, L["Postet einen Werbetext für deinen Raid mit dem Discord-Link – z. B. in den Welt-, Handels- oder Gruppensuche-Kanal."], 0, -26, 11, true):SetWidth(780)

	Label(page, L["Discord-Link"], 0, -60)
	local linkBox = UI.EditBox(page, 420, 24)
	Place(linkBox, page, 110, -56)
	linkBox:SetScript("OnTextChanged", function(self, user)
		if user then cfg().adLink = self:GetText(); UI.RefreshCurrent() end
	end)
	Label(page, L["Den PUG-Link gibt es im Discord mit /pug-einladung. Beim Import eines PUG-Raids wird er automatisch übernommen."], 0, -86, 11, true):SetWidth(780)

	Label(page, L["Kanal"], 0, -120)
	local targets = {}
	local function RebuildTargets()
		wipe(targets)
		for _, t in ipairs(Ad.Targets()) do targets[#targets + 1] = t end
		local cur = Ad.Target()
		local found = false
		for _, t in ipairs(targets) do if t[1] == cur then found = true end end
		if not found then targets[#targets + 1] = { cur, Ad.TargetLabel(cur) } end
	end
	RebuildTargets()
	local chanCycle = UI.Cycle(page, 260, targets, function() return Ad.Target() end,
		function(v) cfg().adChannel = v; UI.RefreshCurrent() end,
		L["Kanäle, denen du beigetreten bist. Einem Kanal beitreten: /join Name"])
	Place(chanCycle, page, 110, -116)

	Label(page, L["Text"], 0, -158)
	local textBox = UI.EditBox(page, 670, 24)
	Place(textBox, page, 110, -154)
	textBox:SetScript("OnTextChanged", function(self, user)
		if user then cfg().adText = self:GetText(); UI.RefreshCurrent() end
	end)
	Label(page, L["Platzhalter: {raid} Raidname · {zeit} Datum/Uhrzeit · {frei} freie Plätze · {softres} softres.it-Link · {link} Discord-Link · {name} dein Name"], 110, -182, 11, true):SetWidth(670)
	local resetBtn = UI.Button(page, L["Standardtext"], 120, 24, function()
		cfg().adText = ""
		textBox:SetText(Ad.DEFAULT_TEXT)
		UI.RefreshCurrent()
	end)
	Place(resetBtn, page, 110, -204)

	Section(page, L["Vorschau"], 0, -248)
	local preview = Label(page, "", 0, -274, 12)
	preview:SetWidth(780)
	local lenText = Label(page, "", 0, -318, 11, true)

	local postBtn = UI.Button(page, L["Im Chat posten"], 200, 32, function()
		Ad.Post()
		UI.RefreshCurrent()
	end, L["Postet die Vorschau in den gewählten Kanal (höchstens alle 30 Sekunden)."])
	Place(postBtn, page, 0, -350)
	postBtn:SetAccent(true)
	local cdText = Label(page, "", 214, -360, 11, true)

	local invCheck = UI.Check(page, L["Auf geflüstertes \"inv\" automatisch einladen (30 Minuten nach der Werbung)"],
		function() return cfg().adAutoInvite end, function(v) cfg().adAutoInvite = v end,
		L["Spieler flüstern dir \"inv\" – RaidMaster lädt sie ein, solange der Raid nicht voll ist.\nAus einer Gruppe wird automatisch ein Schlachtzug."])
	Place(invCheck, page, 0, -400)

	page.elapsed = 0
	page:SetScript("OnUpdate", function(self, el)
		self.elapsed = self.elapsed + el
		if self.elapsed > 1 and Ad.CooldownLeft() > 0 then self.elapsed = 0; UI.RefreshCurrent() end
	end)

	return function()
		if not linkBox:HasFocus() then linkBox:SetText(cfg().adLink or "") end
		if not textBox:HasFocus() then
			textBox:SetText((cfg().adText and cfg().adText ~= "") and cfg().adText or Ad.DEFAULT_TEXT)
		end
		RebuildTargets()
		chanCycle:Refresh()
		local text = Ad.Build()
		preview:SetText(text)
		lenText:SetText(string.format("%d / 255 Zeichen", #text))
		local left = Ad.CooldownLeft()
		if left > 0 then
			postBtn:Disable()
			cdText:SetText(string.format(L["Nächster Post in %d s"], left))
		else
			postBtn:Enable()
			cdText:SetText(Ad.lastPost > 0 and L["Bereit"] or "")
		end
		if (cfg().adLink or "") == "" then
			lenText:SetText(lenText:GetText() .. L["  ·  |cffff6040Kein Discord-Link eingetragen|r"])
		end
		invCheck:Refresh()
	end
end)

UI.AddPage("assign", L["Einteilung"], function(page)
	local Assign = RM.Assign
	local selected = "general"
	Assign.selectedPool = Assign.selectedPool or Assign.DefaultPool()

	Section(page, L["Einteilung per Knopfdruck"], 0, 0)
	local raidOpts = {}
	for _, k in ipairs(Assign.RAIDS) do raidOpts[#raidOpts + 1] = { k, RM.DKP.PoolName(k) } end
	local opts = {}
	local function RebuildCtx()
		wipe(opts)
		for _, c in ipairs(Assign.ContextsFor(Assign.selectedPool)) do opts[#opts + 1] = { c.key, c.name } end
		local ok = false
		for _, o in ipairs(opts) do if o[1] == selected then ok = true end end
		if not ok then selected = "general" end
	end
	RebuildCtx()
	local raidCycle = UI.Cycle(page, 170, raidOpts, function() return Assign.selectedPool end,
		function(v) Assign.selectedPool = v; RebuildCtx(); UI.RefreshCurrent() end,
		L["Für welchen Raid? Jeder Raid hat eigene Boss-Einteilungen und im Discord einen eigenen Einteilungs-Kanal."])
	Place(raidCycle, page, 210, 4)
	Label(page, L["Tanks in Reihenfolge (MT zuerst, dann OT1, OT2 ...), mit Komma getrennt:"], 0, -28, 11, true):SetWidth(380)
	local tankBox = UI.EditBox(page, 300, 24)
	Place(tankBox, page, 0, -46)
	tankBox:SetScript("OnTextChanged", function(self, user) if user then RM.db.config.assignTanks = self:GetText() end end)
	local autoBtn = UI.Button(page, L["Auto"], 72, 24, function()
		local t = Assign.AutoTanks()
		RM.db.config.assignTanks = table.concat(t, ", ")
		tankBox:SetText(RM.db.config.assignTanks)
	end, L["Tanks aus Haupttank-Markierung, Discord-Rolle 'Tank' oder Kriegern ermitteln."])
	Place(autoBtn, page, 308, -46)

	local buildBtn = UI.Button(page, L["Einteilung erstellen"], 185, 30, function() Assign.Build(Assign.selectedPool) end,
		L["Erstellt Heil-, Entfluch-, Bann- und CC-Einteilung für den gewählten Raid aus den Klassen im Raid (MT und OTs nach der Tank-Reihenfolge)."])
	Place(buildBtn, page, 0, -84)
	buildBtn:SetAccent(true)
	local sendBtn = UI.Button(page, L["An alle senden"], 185, 30, function() Assign.SendAll() end,
		"Spieler mit Addon sehen ihre Aufgabe beim Pull groß auf dem Bildschirm, alle anderen bekommen sie zugeflüstert.\\n"
		.. L["Danach /reload, damit der Discord-Bot jedem eine Direktnachricht schickt."])
	Place(sendBtn, page, 195, -84)
	local info = Label(page, L["Grundlage: Klassen im Raid, Rollen aus der Discord-Anmeldung und die Symbol-Vorlagen der Seite Raidleiter. "]
		.. L["Gruppen für Entfluchen, Bannen und Raidheilung richten sich nach den Raidgruppen."], 0, -124, 11, true)
	info:SetWidth(380)

	Section(page, L["Meine Aufgaben"], 0, -186)
	local mine = UI.Multiline(page, 380, 330, true)
	Place(mine, page, 0, -212)

	local rx = 400
	Section(page, L["Übersicht"], rx, 0)
	local ctxCycle = UI.Cycle(page, 200, opts, function() return selected end, function(v) selected = v; UI.RefreshCurrent() end)
	Place(ctxCycle, page, rx + 90, 4)
	local preview = UI.Multiline(page, 390, 460, true)
	Place(preview, page, rx, -28)
	UI.Fill(preview, page)
	local postBtn = UI.Button(page, L["Im Raid posten"], 185, 28, function() Assign.Post(selected) end,
		L["Postet die gewählte Einteilung in den Raidchat (Symbole werden im Chat als Grafik angezeigt)."])
	UI.PlaceBottom(postBtn, page, rx, -500)

	local function iconize(text)
		return (text:gsub("{rt(%d)}", "|TInterface\\TargetingFrame\\UI-RaidTargetingIcon_%1:0|t"))
	end

	return function()
		if not tankBox:HasFocus() then tankBox:SetText(RM.db.config.assignTanks or "") end
		raidCycle:Refresh()
		ctxCycle:Refresh()
		local store = RM.db.assign
		local ctx = store and store.ctx[selected]
		if ctx then
			local lines = {}
			for _, l in ipairs(ctx.lines) do lines[#lines + 1] = iconize(l) end
			preview:SetText(string.format(L["%s · erstellt %s von %s"], store.raid or RM.DKP.PoolName(store.pool or "mc"), RM.FormatTime(store.v), store.by or "?")
				.. "\n\n" .. table.concat(lines, "\n"))
		else
			preview:SetText(L["Noch keine Einteilung erstellt."])
		end
		local my = RM.db.myAssign
		if not my and store then my = Assign.PersonalTexts(RM.Me()) end
		local parts = {}
		for _, c in ipairs(Assign.Contexts) do
			if my and my[c.key] then parts[#parts + 1] = c.name .. ": " .. iconize(my[c.key]) end
		end
		mine:SetText(#parts > 0 and table.concat(parts, "\n\n") or L["Noch keine Aufgaben erhalten."])
		local lead = RM.InRaid() and (RM.IsAssist() or RM.CanEdit())
		for _, b in ipairs({ buildBtn, sendBtn, autoBtn }) do if lead then b:Enable() else b:Disable() end end
		if store and RM.InRaid() then postBtn:Enable() else postBtn:Disable() end
		if store and lead then sendBtn:Enable() else sendBtn:Disable() end
	end
end)

---------------------------------------------------------------------------
-- Seite: Raidleiter (Boss-Infos und Markierungen)
---------------------------------------------------------------------------
local function BuildLeaderBosses(page)
	local Data = RM.Data
	local MAX_BOSSES = 16
	-- Vorauswahl: Raid der aktuellen Instanz, sonst der erste aktuelle Raid dieser Spielversion
	local function DefaultRaid()
		local inst = RM.DKP.CurrentInstancePool(true)
		local def = (inst and Data.Pools[inst]) or Data.Pools[Data.PoolOrder[1] or ""] or Data.RaidList[1] or Data.AllRaids[1]
		return def and def.idx
	end
	local selectedRaid = DefaultRaid()
	local selectedBoss
	local function Raid() return Data.RaidByIndex(selectedRaid or 0) end
	local function Entry(id)
		local def = Raid()
		for _, e in ipairs(def and def.view or {}) do if e.id == id then return e end end
	end
	local function SelectRaid(idx)
		selectedRaid = idx
		local def = Raid()
		selectedBoss = def and def.view and def.view[1] and def.view[1].id or nil
	end
	SelectRaid(selectedRaid)

	Section(page, L["Boss-Infos"], 0, 0)


	-- Raid wählen: alle bekannten Raids aller Erweiterungen (* = gibt es in dieser Spielversion nicht)
	local raidDrop = UI.Dropdown(page, 190, function() return Data.InfoGroups() end, function() return selectedRaid end, function(v)
		SelectRaid(v)
		UI.RefreshCurrent()
	end, L["Raid wählen – alle Raids von Classic bis Midnight, nach Erweiterung geordnet."] .. "\n"
		.. L["* = Raid gibt es in deiner Spielversion nicht (nur Taktik zum Nachlesen)."])
	Place(raidDrop, page, 0, -28)
	local expLabel = Label(page, "", 0, -58, 11, true)
	expLabel:SetWidth(190)

	local bossButtons = {}
	local y = -76
	for i = 1, MAX_BOSSES do
		local b = UI.Button(page, "", 190, 19, function(self)
			selectedBoss = self.bossID
			local e = Entry(selectedBoss)
			if e and e.template and RM.db.config.autoTemplate then
				RM.db.config.markerTemplate = e.template
				RM.Markers.ResetUsed()
				RM.Fire("CONFIG_CHANGED")
			end
			UI.RefreshCurrent()
		end)
		Place(b, page, 0, y)
		b.label:SetJustifyH("LEFT")
		b.label:ClearAllPoints()
		b.label:SetPoint("LEFT", 8, 0)
		b.label:SetPoint("RIGHT", -4, 0)
		bossButtons[i] = b
		y = y - 20
	end

	local info = UI.Multiline(page, 560, 300, true)
	Place(info, page, 200, -28)

	local postBtn = UI.Button(page, L["Kurzinfo als Raidwarnung"], 200, 28, function() local e = selectedBoss and Entry(selectedBoss) if e then RM.Markers.PostBossInfo(selectedBoss, e.info) end end,
		L["Postet die Kurzinfo als Schlachtzugwarnung (nie im normalen Chat)."])
	Place(postBtn, page, 200, -336)
	postBtn:SetAccent(true)
	local nowBtn = UI.Button(page, L["Aktueller Raid"], 140, 28, function()
		SelectRaid(DefaultRaid())
		UI.RefreshCurrent()
	end, L["Springt zum Raid, in dem du gerade bist."])
	Place(nowBtn, page, 410, -336)
	local addsBtn = UI.Button(page, L["Adds markieren"], 150, 28, function() RM.Markers.MarkAdds() end,
		L["Markiert alle sichtbaren Adds auf einmal nach der Vorlage des Bosses (z. B. Garrs Feuerschwörer, Sulfurons Priester).\nGegner-Namensplaketten müssen an sein (Taste V)."])
	Place(addsBtn, page, 560, -336)

	-- Magmadar: Jäger nach Einlullender Schuss fragen, Rotation posten
	local tq = CreateFrame("Frame", nil, page)
	tq:SetSize(560, 34)
	Place(tq, page, 200, -370)
	local tqAsk = UI.Button(tq, L["Jäger abfragen"], 130, 26, function() RM.Tranq.Ask() end,
		L["Fragt alle Jäger im Raid, ob sie Einlullender Schuss haben (mit Addon automatisch, sonst per Flüstern: ja/nein)."])
	tqAsk:SetPoint("LEFT", 0, 0)
	local tqPost = UI.Button(tq, L["Rotation posten"], 130, 26, function() RM.Tranq.Post() end,
		L["Postet die Einlull-Rotation als Schlachtzugwarnung und flüstert jedem Jäger seine Position."])
	tqPost:SetPoint("LEFT", tqAsk, "RIGHT", 8, 0)
	local tqText = UI.Text(tq, "", 11)
	tqText:SetPoint("LEFT", tqPost, "RIGHT", 10, 0)
	tqText:SetWidth(280)

	-- Majordomus: Sheep-Rotation der Magier (mindestens 3, je ein Symbol)
	local sh = CreateFrame("Frame", nil, page)
	sh:SetSize(560, 34)
	Place(sh, page, 200, -370)
	local shPost = UI.Button(sh, L["Sheep-Rotation posten"], 170, 26, function() RM.Sheep.Post() end,
		L["Sagt als Schlachtzugwarnung an, welcher Magier welchen Heiler sheept (Kreuz, Viereck, Mond), und flüstert jedem Magier sein Symbol."])
	shPost:SetPoint("LEFT", 0, 0)
	local shText = UI.Text(sh, "", 11)
	shText:SetPoint("LEFT", shPost, "RIGHT", 10, 0)
	shText:SetWidth(380)
	shText:SetWordWrap(false)

	-- Markierungen
	Section(page, L["Schlachtzugsymbole"], 0, -412)
	Label(page, L["Vorlage für 'Auto'"], 0, -442)
	local tmplOpts = {}
	local function RebuildTemplates()
		wipe(tmplOpts)
		local seen = {}
		local function add(t) if t and not seen[t.id] then seen[t.id] = true; tmplOpts[#tmplOpts + 1] = { t.id, t.name } end end
		add(Data.GetTemplate("standard"))
		local def = Raid()
		for _, e in ipairs(def and def.view or {}) do if e.template then add(Data.GetTemplate(e.template)) end end
		add(Data.GetTemplate(RM.db.config.markerTemplate))
	end
	RebuildTemplates()
	local tmpl = UI.Cycle(page, 170, tmplOpts, function() return RM.db.config.markerTemplate end, function(v)
		RM.db.config.markerTemplate = v
		RM.Markers.ResetUsed()
		RM.Fire("CONFIG_CHANGED")
	end)
	Place(tmpl, page, 130, -437)
	local note = Label(page, "", 310, -442, 11, true)
	note:SetWidth(460)

	local barCheck = UI.Check(page, L["Markierungsleiste anzeigen"], function() return RM.db.config.markerBar end, function(v)
		RM.db.config.markerBar = v
		RM.Fire("CONFIG_CHANGED")
	end)
	Place(barCheck, page, 0, -472)
	local lockCheck = UI.Check(page, L["Leiste fixieren"], function() return RM.db.config.markerLocked end, function(v) RM.db.config.markerLocked = v end)
	Place(lockCheck, page, 230, -472)
	local autoCheck = UI.Check(page, L["Vorlage beim Bosskampf automatisch wählen"], function() return RM.db.config.autoTemplate end,
		function(v) RM.db.config.autoTemplate = v end)
	Place(autoCheck, page, 420, -472)

	local clearBtn = UI.Button(page, L["Alle Symbole entfernen"], 180, 26, function() RM.Markers.ClearAll() end)
	Place(clearBtn, page, 0, -502)
	local markHint = Label(page, "", 190, -497, 11, true)
	markHint:SetWidth(580)

	-- Boss-Leiste: erscheint, sobald die Raidleitung einen Boss ins Ziel nimmt (Ansage + Symbole per Klick)
	local bossBarCheck = UI.Check(page, L["Boss-Leiste, sobald ein Boss im Ziel ist (Ansage + Symbole per Klick)"],
		function() return RM.db.config.bossBar ~= false end,
		function(v) RM.db.config.bossBar = v; RM.Fire("CONFIG_CHANGED") end,
		L["Nimmt der Raidleiter oder ein Assistent einen Boss ins Ziel, erscheint eine Leiste: ein Klick sagt die Taktik als Schlachtzugwarnung an und setzt die Symbole wie im Automatikmodus."])
	Place(bossBarCheck, page, 0, -532)

	return function()
		if not Raid() then SelectRaid(DefaultRaid()) end
		raidDrop:Refresh()
		local def = Raid()
		local expName = ""
		for _, x in ipairs(Data.Expansions) do if def and x.key == def.exp then expName = x.name end end
		expLabel:SetText(expName .. ((def and not def.available) and (" · " .. L["nicht in dieser Spielversion"]) or ""))
		local view = def and def.view or {}
		local ids = {}
		for i, e in ipairs(view) do ids[i] = e.id end
		for i, b in ipairs(bossButtons) do
			local id = ids[i]
			b.bossID = id
			if id then
				local e = view[i]
				local mark = e.template and " |TInterface\\TargetingFrame\\UI-RaidTargetingIcon_8:0|t" or ""
				b:SetText(e.name .. mark)
				b:SetAccent(id == selectedBoss)
				b:Show()
			else
				b:Hide()
			end
		end
		local cur = selectedBoss and Entry(selectedBoss)
		local i = cur and cur.info
		if i then
			info:SetText(i.text or "")
		elseif def and #ids == 0 then
			info:SetText(L["Für diesen Raid sind keine Bosse hinterlegt. Bosse werden beim ersten Kill automatisch erkannt."])
		else
			info:SetText(L["Für diesen Boss gibt es noch keine Taktik."])
		end
		if i and i.post and i.post[1] then postBtn:Enable() else postBtn:Disable() end
		if selectedBoss == 671 and RM.Sheep then
			sh:Show()
			shText:SetText(RM.Sheep.StatusText())
			if RM.IsAssist() or RM.CanEdit() then shPost:Enable() else shPost:Disable() end
		else
			sh:Hide()
		end
		if selectedBoss == 664 and RM.Tranq then
			tq:Show()
			tqText:SetText(RM.Tranq.StatusText())
		else
			tq:Hide()
		end
		RebuildTemplates()
		tmpl:Refresh()
		local t = Data.GetTemplate(RM.db.config.markerTemplate)
		note:SetText(t.note or "")
		barCheck:Refresh()
		bossBarCheck:Refresh()
		lockCheck:Refresh()
		autoCheck:Refresh()
		local lead = RM.Markers.IsMarkerLead() or not (RM.InRaid() or (IsInGroup and IsInGroup()))
		for _, b in ipairs({ addsBtn, clearBtn }) do if lead then b:Enable() else b:Disable() end end
		markHint:SetText(lead and "" or ("|cffff5544" .. L["Nur Raidleiter und Co-Raidleiter (Assistenten) können Schlachtzugsymbole setzen."] .. "|r " .. L["Die Symbolleiste erscheint nur bei ihnen."]))
	end
end

-- Teil "Raid & Gruppen": Raid starten/beenden, Plündermeister, Gruppenaufstellung, Ersatzbank
local ROLE_SHORT = { tank = { L["T"], 0.45, 0.7, 1 }, heal = { L["H"], 0.35, 1, 0.45 }, melee = { L["N"], 1, 0.6, 0.3 }, ranged = { L["F"], 0.85, 0.55, 1 } }
local function BuildLeaderRaid(page)
	Section(page, L["Raid-Sitzung"], 0, 0)
	local sessionText = Label(page, "", 0, -26, 12)
	sessionText:SetWidth(390)
	local startBtn = UI.Button(page, L["Raid starten"], 140, 28, function()
		if not NeedOfficer() then return end
		UI.Confirm(L["Raid starten?\nAlle Raidmitglieder (und die Ersatzbank) erhalten den Pünktlichkeitsbonus."], function() RM.Raid.Start() end)
	end)
	Place(startBtn, page, 0, -60)
	startBtn:SetAccent(true)
	local endBtn = UI.Button(page, L["Raid beenden"], 140, 28, function()
		UI.Confirm(L["Raid beenden?\nAlle Raidmitglieder (und die Ersatzbank) erhalten den Abschlussbonus."], function() RM.Raid.End() end)
	end)
	Place(endBtn, page, 148, -60)
	Label(page, L["DKP-Topf"], 0, -103)
	local raidPool = UI.Dropdown(page, 220, function() return UI.PoolGroups(RM.db.data) end, function()
		local s = RM.db.session
		return (s.active and s.pool) or RM.DKP.CurrentInstancePool() or RM.db.config.activePool or "mc"
	end, function(v)
		RM.db.config.activePool = v
		if RM.db.session.active then RM.db.session.pool = v end
		RM.DKP.MapCurrentInstance(v)
		RM.Fire("SESSION_CHANGED")
	end, L["Für welchen Raid Start-/Endbonus und Versteigerungen gebucht werden."])
	Place(raidPool, page, 75, -98)

	local rx = 410
	Section(page, L["Plündermeister"], rx, 0)
	local mlDrop = UI.Dropdown(page, 180, function() return RM.Loot.MasterChoices() end,
		function() return RM.db.config.lootMaster or "" end, function(v) RM.Loot.SetMaster(v) end,
		L["Plündermeister wählen – als Raidleiter wird die Plündermethode im Spiel sofort umgestellt."])
	Place(mlDrop, page, rx, -26)
	local th = UI.Cycle(page, 170, { { 2, L["Selten (grün)"] }, { 3, L["Rar (blau)"] }, { 4, L["Episch (lila)"] } },
		function() return RM.db.config.lootThreshold end, function(v) RM.Loot.SetThreshold(v) end, L["Plünderschwelle"])
	Place(th, page, rx + 190, -26)
	local lootState = Label(page, "", rx, -58, 11)
	lootState:SetWidth(380)
	local checkBtn = UI.Button(page, L["Raid-Check"], 120, 26, function() RM.Raid.RunCheck(); UI.RefreshCurrent() end,
		L["Prüft Plündermethode, Schwelle, Rechte und welche Spieler das Addon haben."])
	Place(checkBtn, page, rx, -96)
	local sortBtn = UI.Button(page, L["Gruppen sortieren"], 150, 26, function() if RM.Signup and RM.Signup.ArrangeGroups then RM.Signup.ArrangeGroups() end end,
		L["Setzt alle in die Gruppen der Discord-Aufstellung (Seite Anmeldungen: Import)."])
	Place(sortBtn, page, rx + 128, -96)

	-- Gruppen 1–8
	Section(page, L["Gruppen"], 0, -138)
	local roleSum = Label(page, "", 110, -141, 11, true)
	roleSum:SetWidth(680)
	local boxes = {}
	for g = 1, 8 do
		local col, row = (g - 1) % 4, math.floor((g - 1) / 4)
		local box = UI.Frame(page, 190, 116)
		UI.Skin(box, COLORS.panel)
		Place(box, page, col * 200, -164 - row * 124)
		box.title = UI.Text(box, string.format(L["Gruppe %d"], g), 12, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
		box.title:SetPoint("TOPLEFT", 8, -6)
		box.lines = {}
		for i = 1, 5 do
			local fs = UI.Text(box, "", 12)
			fs:SetPoint("TOPLEFT", 8, -8 - i * 18)
			fs:SetWidth(174)
			fs:SetJustifyH("LEFT")
			fs:SetWordWrap(false)
			box.lines[i] = fs
		end
		boxes[g] = box
	end
	Section(page, L["Ersatzbank"], 0, -420)
	local bench = Label(page, "", 0, -446, 12)
	bench:SetWidth(790)
	local legend = Label(page, L["T = Tank · H = Heiler · N = Nahkampf · F = Fernkampf (aus der Skillung bzw. Discord-Rolle). Ersatzbank verwalten: Seite Raid."], 0, -500, 11, true)
	legend:SetWidth(790)

	local function roleTag(name)
		local r = RM.Spec and RM.Spec.Role(name)
		local t = r and ROLE_SHORT[r]
		if not t then return "" end
		return string.format("|cff%02x%02x%02x%s|r ", t[2] * 255, t[3] * 255, t[4] * 255, t[1])
	end

	return function()
		local s = RM.db.session
		if s.active then
			local n = 0
			for _ in pairs(s.kills or {}) do n = n + 1 end
			sessionText:SetText(string.format(L["|cff40ff40Raid läuft seit %s|r (%s) · %d Bosse besiegt"], date("%H:%M", s.started), RM.DKP.PoolName(s.pool or "mc"), n))
			startBtn:Disable(); endBtn:Enable()
		else
			sessionText:SetText(s.ended and (L["Kein Raid aktiv. Letzter Raid beendet: "] .. RM.FormatTime(s.ended)) or L["Kein Raid aktiv."])
			if RM.CanEdit() then startBtn:Enable() else startBtn:Disable() end
			endBtn:Disable()
		end
		raidPool:Refresh(); mlDrop:Refresh(); th:Refresh()
		local problems = RM.Loot.Problems and RM.Loot.Problems() or {}
		if #problems > 0 then
			lootState:SetText("|cffff5544" .. table.concat(problems, "\n") .. "|r")
		elseif RM.InRaid() and RM.MasterLooterName() then
			lootState:SetText("|cff40ff40" .. L["Plündermeister: "] .. RM.MasterLooterName() .. "|r")
		else
			lootState:SetText("")
		end
		if RM.IsAssist() and RM.db.signup and RM.db.signup.groups then sortBtn:Enable() else sortBtn:Disable() end

		local groups, counts, total = {}, { tank = 0, heal = 0, melee = 0, ranged = 0 }, 0
		for g = 1, 8 do groups[g] = {} end
		for _, m in ipairs(RM.RaidMembers()) do
			local g = m.group or 1
			if groups[g] then table.insert(groups[g], m) end
			local r = RM.Spec and RM.Spec.Role(m.name)
			if r and counts[r] then counts[r] = counts[r] + 1 end
			total = total + 1
		end
		for g = 1, 8 do
			local box = boxes[g]
			table.sort(groups[g], function(a, b) return a.name < b.name end)
			box.title:SetText(string.format(L["Gruppe %d"], g) .. "  |cff888888" .. #groups[g] .. "/5|r")
			for i = 1, 5 do
				local m = groups[g][i]
				if m then
					box.lines[i]:SetText(roleTag(m.name) .. RM.ClassColor(m.class, m.name) .. (m.online == false and " |cff888888(offline)|r" or ""))
				else
					box.lines[i]:SetText("|cff555555–|r")
				end
			end
		end
		roleSum:SetText(total > 0 and string.format(L["%d Spieler · Tanks %d · Heiler %d · Nahkampf %d · Fernkampf %d"], total, counts.tank, counts.heal, counts.melee, counts.ranged)
			or L["Nicht in einem Schlachtzug."])
		local names = {}
		for name in pairs(RM.db.config.standby or {}) do names[#names + 1] = name end
		table.sort(names)
		for i, n in ipairs(names) do
			local p = RM.db.data.players[n]
			names[i] = roleTag(n) .. RM.ClassColor(p and p.c or (RM.guild.class and RM.guild.class[n]), n)
		end
		bench:SetText(#names > 0 and table.concat(names, "   ") or ("|cff888888" .. L["Niemand auf der Ersatzbank."] .. "|r"))
	end
end

-- Raidleiter-Seiten (3.0: eigene Reiter im Bereich Raid statt einer Seite mit Unter-Reitern)
UI.AddPage("lgroups", L["Gruppen"], function(page) return BuildLeaderRaid(page) end)
UI.AddPage("lboss", L["Bosse & Symbole"], function(page) return BuildLeaderBosses(page) end)

-- frühere Unter-Reiter der Seite Raidleiter -> Reiter im Bereich Raid
local LEADER_TABS = { raid = "lgroups", assign = "assign", boss = "lboss" }
function UI.OpenLeaderTab(key)
	UI.Open(LEADER_TABS[key] or key or "lgroups")
end

---------------------------------------------------------------------------
-- Seite: Skillungen
---------------------------------------------------------------------------
UI.AddPage("specs", L["Skillungen"], function(page)
	local Spec = RM.Spec
	local SOURCES = { self = "eigene", addon = L["Addon"], inspect = L["Betrachtet"] }
	local ROLE_COLORS = { tank = { 0.6, 0.8, 1 }, heal = { 0.4, 1, 0.5 }, melee = { 1, 0.75, 0.4 }, ranged = { 1, 0.55, 0.9 } }

	Section(page, L["Skillungen"], 0, 0)
	local info = Label(page, "", 0, -26, 11, true)
	info:SetWidth(780)

	local list = UI.List(page, 780, 380, {
		{ title = L["Name"], width = 150 },
		{ title = L["Klasse"], width = 110 },
		{ title = L["Skillung"], width = 150 },
		{ title = L["Punkte"], width = 80 },
		{ title = L["Rolle"], width = 90 },
		{ title = L["Quelle"], width = 80 },
		{ title = L["Stand"], width = 90 },
	}, { emptyText = L["Noch keine Skillungen bekannt."] })
	Place(list, page, 0, -64)
	UI.Fill(list, page, true)

	local scanBtn = UI.Button(page, L["Raid scannen"], 140, 28, function()
		if Spec.scan.running then Spec.StopScan() else Spec.StartScan(true) end
	end, L["Fragt alle Addon-Nutzer im Raid nach ihrer Skillung und betrachtet Spieler ohne Addon\n"]
		.. L["(in Reichweite, außerhalb des Kampfes)."])
	UI.PlaceBottom(scanBtn, page, 0, -456)
	local sendBtn = UI.Button(page, L["Meine Skillung senden"], 170, 28, function()
		Spec.UpdateMine(true)
		RM.Print(L["Deine Skillung wurde an Gilde und Raid gesendet."])
	end)
	UI.PlaceBottom(sendBtn, page, 150, -456)
	local autoCheck = UI.Check(page, L["Als Raidleiter automatisch alle 5 Minuten scannen"],
		function() return RM.db.config.specScan end, function(v) RM.db.config.specScan = v end,
		L["Nur für Raidleiter, Assistenten und Offiziere."])
	UI.PlaceBottom(autoCheck, page, 340, -460)
	local status = Label(page, "", 0, -496, 11, true)
	UI.PlaceBottom(status, page, 0, -496)
	status:SetWidth(580)
	-- Berufe-Verzeichnis: jeder Klick öffnet und liest den nächsten Beruf (Discord: /handwerk, /berufe)
	local profBtn = UI.Button(page, L["Meine Berufe einlesen"], 180, 28, function() RM.Prof.ReadNext() end,
		L["Öffnet nacheinander deine Berufsfenster (ein Klick pro Beruf) und liest Stufe und Rezepte aus.\n"]
		.. L["Die Liste geht an die Gilde; im Discord zeigt /handwerk, wer was herstellen kann."])
	UI.PlaceBottom(profBtn, page, 600, -492)

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
					r.label or (e and "?" or L["|cff888888unbekannt|r"]),
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
			info:SetText(string.format(L["Skillungen der Raidmitglieder: %d von %d bekannt. Nach /reload übernimmt der Discord-Bot sie in die Profile."], known, #rows))
		else
			info:SetText(string.format(L["%d bekannte Skillungen (Gilde und frühere Raids). Nach /reload übernimmt der Discord-Bot sie in die Profile."], known))
		end
		scanBtn.label:SetText(Spec.scan.running and L["Scan stoppen"] or L["Raid scannen"])
		if Spec.CanScan() then scanBtn:Enable() else scanBtn:Disable() end
		autoCheck:Refresh()
		if Spec.inspectUnsupported then
			status:SetText(L["Dieser Spielclient liefert beim Betrachten keine Talente – Skillungen kommen nur von Spielern mit RaidMaster."])
		elseif Spec.scan.running then
			local cur = Spec.scan.current
			status:SetText(string.format(L["Scan läuft: noch %d Spieler%s"], #Spec.scan.queue, cur and (L[" – betrachte "] .. cur.name) or ""))
		else
			status:SetText(L["Spieler mit RaidMaster senden ihre Skillung selbst. Spieler ohne Addon werden per Betrachten erfasst."])
		end
	end
end)

---------------------------------------------------------------------------
-- Seite: Einstellungen
---------------------------------------------------------------------------
UI.AddPage("settings", L["Einstellungen"], function(page)
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

	Section(page, L["DKP-Vergabe"], 0, 0)
	local y = -28
	NumField(L["Pünktlich zum Raidstart"], 0, y, function() return S().dkpStart end, function(v) S().dkpStart = v end); y = y - 28
	NumField(L["Raid bis zum Ende"], 0, y, function() return S().dkpEnd end, function(v) S().dkpEnd = v end); y = y - 28
	NumField(L["Ersatzbank beim Raidstart"], 0, y, function() return S().standbyStartDKP or 10 end, function(v) S().standbyStartDKP = math.max(0, v) end,
		L["Spieler auf der Ersatzbank bekommen beim Raidstart einmalig diese DKP – danach keine Boss- oder Endpunkte."]); y = y - 28
	NumField(L["Andere Bosse (Standard)"], 0, y, function() return S().defaultBossDKP end, function(v) S().defaultBossDKP = v end); y = y - 36

	-- Boss-DKP je Raid-Topf (neue Bosse erscheinen nach dem ersten Kill)
	Section(page, L["Bosse"], 0, y)
	local settingsPool = "mc"
	local spCycle = UI.Dropdown(page, 190, function() return UI.PoolGroups(RM.db.data) end, function() return settingsPool end, function(v)
		settingsPool = v
		UI.RefreshCurrent()
	end, L["Raid wählen, dessen Boss-DKP du einstellen willst."])
	Place(spCycle, page, 60, y + 4)
	y = y - 28
	local bossRows = {}
	local bossNote = Label(page, "", 0, y - 5, 11, true)
	bossNote:SetWidth(270)
	for i = 1, 16 do
		local row = {}
		row.label = Label(page, "", 0, y - 5)
		row.label:SetWidth(170)
		row.edit = UI.EditBox(page, 60, 21, true)
		Place(row.edit, page, 175, y)
		bossRows[i] = row
		fields[#fields + 1] = {
			edit = row.edit,
			get = function()
				if not row.id then return nil end
				local b = RM.Data.Bosses[row.id]
				return S().bossDKP[row.id] or (b and b.dkp) or S().defaultBossDKP
			end,
			set = function(v) if row.id then S().bossDKP[row.id] = v end end,
		}
		y = y - 23
	end

	local function UpdateBossRows()
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
			bossNote:SetText(L["Die Bosse dieses Raids werden beim ersten Kill automatisch erkannt. Bis dahin gilt der Standardwert."])
			bossNote:Show()
		else
			bossNote:Hide()
		end
	end

	local x2 = 290
	Section(page, L["Gebote"], x2, 0)
	local y2 = -28
	NumField(L["Mindestgebot"], x2, y2, function() return S().minBid end, function(v) S().minBid = math.max(0, v) end); y2 = y2 - 28
	NumField(L["Gebotsschritt"], x2, y2, function() return S().bidIncrement end, function(v) S().bidIncrement = math.max(1, v) end); y2 = y2 - 28
	NumField(L["Dauer (Sekunden)"], x2, y2, function() return S().auctionTime end, function(v) S().auctionTime = math.max(10, math.min(120, v)) end); y2 = y2 - 36

	Section(page, L["System"], x2, y2)
	y2 = y2 - 28
	NumField(L["Decay in %"], x2, y2, function() return S().decayPct end, function(v) S().decayPct = math.max(0, math.min(100, v)) end); y2 = y2 - 28
	NumField(L["Offiziersränge bis Index"], x2, y2, function() return S().officerRank end, function(v) S().officerRank = math.max(0, math.min(9, v)) end,
		L["Gildenrang-Index: 0 = Gildenmeister, 1 = nächster Rang usw. Alle Ränge bis zu diesem Index dürfen DKP ändern."]); y2 = y2 - 36

	local checks = {}
	local function SCheck(label, key, tooltip)
		local cb = UI.Check(page, label, function() return S()[key] end, function(v) S()[key] = v end, tooltip)
		Place(cb, page, x2, y2)
		checks[#checks + 1] = cb
		y2 = y2 - 26
	end
	SCheck(L["Erstkill zählt doppelt"], "firstKillDouble")
	SCheck(L["Verlängern bei späten Geboten (5 Sek.)"], "antiSnipe", L["Kommt in den letzten 5 Sekunden ein Gebot, wird auf 5 Sekunden verlängert."])
	SCheck(L["Negative DKP erlauben"], "allowNegative", L["Spieler dürfen mehr bieten, als sie haben."])
	SCheck(L["Nur Spieler online erhalten DKP"], "onlyOnline")
	SCheck(L["Ersatzbank erhält DKP (nur beim Raidstart)"], "standbyGetsDKP")
	SCheck(L["Main vor Twink"], "mainBeforeTwink", L["Twinks gewinnen eine Versteigerung nur, wenn kein Main bietet.\nEin Main übernimmt ein Twink-Gebot schon ab dem Mindestgebot."])

	local saveBtn = UI.Button(page, L["Speichern und an die Gilde verteilen"], 300, 30, function()
		if not NeedOfficer() then return end
		for _, f in ipairs(fields) do
			local v = tonumber(f.edit:GetText())
			if v and f.edit:IsShown() then f.set(math.floor(v)) end
		end
		RM.DKP.SettingsChanged()
	end)
	Place(saveBtn, page, x2, y2 - 10)
	saveBtn:SetAccent(true)

	local revertBtn = UI.Button(page, L["Verwerfen"], 100, 30, function()
		for _, f in ipairs(fields) do f.edit:SetText(tostring(f.get() or 0)) end
		for _, c in ipairs(checks) do c:Refresh() end
	end)
	Place(revertBtn, page, x2 + 306, y2 - 10)

	local note = Label(page, L["Diese Werte gelten für die ganze Gilde und werden mit allen Addon-Nutzern abgeglichen. "]
		.. L["Häkchen werden sofort lokal übernommen und beim Speichern verteilt."], x2, y2 - 52, 11, true)
	note:SetWidth(480)

	local mmCheck = UI.Check(page, L["Minimap-Knopf ausblenden"], function() return RM.db.config.minimap.hide end, function(v)
		RM.db.config.minimap.hide = v
		local b = _G["RaidMasterMinimapButton"]
		if b then if v then b:Hide() else b:Show() end end
	end)
	Place(mmCheck, page, x2, y2 - 100)
	local ttCheck = UI.Check(page, L["Item-Tooltip ergänzen (Droprate, letzter Preis)"], function() return RM.db.config.itemTooltip ~= false end,
		function(v) RM.db.config.itemTooltip = v end, L["Zeigt im Item-Tooltip, wie oft das Item bei euch gedroppt ist und wofür es zuletzt versteigert wurde."])
	Place(ttCheck, page, x2, y2 - 126)
	local bankCheck = UI.Check(page, L["Bank-Charakter (Bestand an Discord)"], function() return RM.db.config.bankScan end,
		function(v) RM.db.config.bankScan = v end,
		L["Beim Öffnen von Bank, Briefkasten (und Gildenbank, falls vorhanden) liest RaidMaster den Bestand aus.\nDer Uploader schickt ihn an Discord (#gildenbank-bestand, /bank).\nAuf diesem Charakter erscheint dann der Bereich Gildenbank."])
	Place(bankCheck, page, x2 + 250, y2 - 100)
	local recCheck = UI.Check(page, L["Erstkill-Feier und Bestzeiten"], function() return RM.db.config.records ~= false end,
		function(v) RM.db.config.records = v end,
		L["Erstkill: Fanfare, Schlachtzugwarnung und Screenshot für Discord. Bestzeiten: 'Neuer Rekord!' bei schnelleren Kills."])
	Place(recCheck, page, x2 + 250, y2 - 126)

	return function()
		UpdateBossRows()
		for _, f in ipairs(fields) do
			if not f.edit:HasFocus() then f.edit:SetText(tostring(f.get() or 0)) end
		end
		for _, c in ipairs(checks) do c:Refresh() end
		mmCheck:Refresh()
		ttCheck:Refresh(); bankCheck:Refresh(); recCheck:Refresh()
		if RM.CanEdit() then saveBtn:Enable() else saveBtn:Disable() end
	end
end)

---------------------------------------------------------------------------
-- Seite: Gildenbank (nur auf dem Bank-Charakter sichtbar)
---------------------------------------------------------------------------
UI.AddPage("bank", L["Gildenbank"], function(page)
	local B = RM.Bank
	local query = ""
	Section(page, L["Bestand der Gildenbank"], 0, 0)
	local status = Label(page, "", 0, -28)
	status:SetWidth(560)
	status:SetJustifyH("LEFT")
	local hint = Label(page, L["Öffne Bank, Briefkasten oder Gildenbank – RaidMaster liest den Bestand dann von selbst ein."], 0, -48, 11, true)
	hint:SetWidth(560)
	hint:SetJustifyH("LEFT")

	local scanBtn = UI.Button(page, L["Jetzt einlesen"], 130, 26, function()
		if B.bankOpen then B.ScanBank()
		elseif B.mailOpen then B.ScanMail()
		else RM.Print(L["Öffne zuerst die Bank oder den Briefkasten."]) end
	end, L["Liest Taschen und Bank (bei offener Bank) bzw. die Post (bei offenem Briefkasten) neu ein."])
	Place(scanBtn, page, 580, -24)
	local sendBtn = UI.Button(page, L["An Discord senden"], 150, 26, function() RM.Guide.SendNow() end,
		L["Lädt die Oberfläche neu, damit WoW speichert – der Uploader schickt den Bestand nach #gildenbank-bestand."])
	Place(sendBtn, page, 580, -54)
	sendBtn:SetAccent(true)

	local search = UI.EditBox(page, 200, 24)
	Place(search, page, 0, -76)
	local shint = UI.Text(search, L["Item suchen ..."], 11, unpack(COLORS.muted))
	shint:SetPoint("LEFT", 8, 0)
	search:SetScript("OnTextChanged", function(self)
		query = self:GetText():lower()
		if query == "" then shint:Show() else shint:Hide() end
		UI.RefreshCurrent()
	end)
	local check = UI.Check(page, L["Dieser Charakter ist der Bank-Charakter"], function() return RM.db.config.bankScan end,
		function(v) RM.db.config.bankScan = v; UI.RefreshCurrent() end,
		L["Ausschalten, wenn das nicht mehr der Bank-Charakter ist – der Bereich Gildenbank verschwindet dann."])
	Place(check, page, 220, -76)

	local list = UI.List(page, 790, 400, {
		{ title = L["Item"], width = 300 },
		{ title = L["Anzahl"], width = 70, justify = "RIGHT" },
		{ title = L["Taschen"], width = 80, justify = "RIGHT" },
		{ title = L["Bank"], width = 80, justify = "RIGHT" },
		{ title = L["Post"], width = 80, justify = "RIGHT" },
		{ title = L["Gildenbank"], width = 100, justify = "RIGHT" },
	}, { emptyText = L["Noch nichts eingelesen – öffne die Bank oder den Briefkasten."] })
	Place(list, page, 0, -110)
	UI.Fill(list, page, true)

	RM.Listen("BANK_CHANGED", function() if page:IsShown() then UI.RefreshCurrent() end end)

	local function Money(c)
		c = tonumber(c) or 0
		if GetCoinTextureString then return GetCoinTextureString(c) end
		return string.format("%dg %ds %dc", math.floor(c / 10000), math.floor(c / 100) % 100, c % 100)
	end

	return function()
		check:Refresh()
		local b = RM.db.bank
		local rows, total = {}, 0
		if b and b.i then
			for id, e in pairs(b.i) do
				total = total + 1
				if query == "" or (e.n or ""):lower():find(query, 1, true) then
					local col = ITEM_QUALITY_COLORS and e.q and ITEM_QUALITY_COLORS[e.q]
					local w = e.w or {}
					local function n(x) return (x and x > 0) and tostring(x) or "" end
					rows[#rows + 1] = {
						key = id, link = "item:" .. id, name = e.n or ("item:" .. id),
						cells = { (e.ic and ("|T" .. e.ic .. ":14|t ") or "") .. (e.n or ("item:" .. id)), tostring(e.c or 0),
							n(w.bag), n(w.bank), n(w.mail), n(w.guild) },
						colors = { col and { col.r, col.g, col.b } or nil },
					}
				end
			end
		end
		table.sort(rows, function(x, y) return x.name < y.name end)
		list:SetData(rows)
		if b and b.t then
			status:SetText(string.format(L["%s · Stand %s · %d verschiedene Items · Gold: %s"], b.c or RM.Me(),
				date("%d.%m. %H:%M", b.t), total, Money(b.g)) .. (b.gb and (" · " .. L["Gildenbank: "] .. Money(b.gb)) or ""))
		else
			status:SetText(L["Noch kein Bestand eingelesen."])
		end
		if B.bankOpen or B.mailOpen then scanBtn:Enable() else scanBtn:Disable() end
	end
end)
