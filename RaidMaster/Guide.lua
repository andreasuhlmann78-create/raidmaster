-- RaidMaster - Anleitung "Discord automatisch füttern"
-- Schritt-für-Schritt-Anleitung, wie DKP, Loot, Einteilung und Skillungen automatisch im Discord landen
-- (Uploader auf dem PC der Raidleitung -> Discord-Bot). Öffnet sich beim ersten Start für Raidleitung und
-- Offiziere von selbst, danach über die Seite "Discord" oder /rm discord.

local ADDON, RM = ...
local L = RM.L
local UI = RM.UI
local COLORS = UI.COLORS
local G = {}
RM.Guide = G

G.UPLOADER_URL = "https://github.com/andreasuhlmann78-create/raidmaster/raw/main/download/RaidMasterUploader.zip"
local CHECK = "|TInterface\\RaidFrame\\ReadyCheck-Ready:14:14|t "

-- Schritte: group 1 = einmal einrichten, group 2 = bei jedem Raid
G.STEPS = {
	{ group = 1, title = L["So funktioniert es"],
	  text = L["RaidMaster speichert alle Daten (DKP, Loot, Einteilung, Skillungen) in einer Datei auf deinem PC. WoW schreibt diese Datei beim Ausloggen oder nach /reload."] .. "\n\n"
		.. L["Der Uploader auf deinem PC schickt sie dann sofort an den Discord-Bot. Der Bot aktualisiert die DKP- und Loot-Kanäle jedes Raids, #einteilung und schickt Direktnachrichten."] .. "\n\n"
		.. L["Einrichten musst du das nur einmal (Schritte 2 bis 6). Danach reicht nach dem Raid ein Klick."] },
	{ group = 1, title = L["Discord vorbereiten"],
	  text = L["Ein Discord-Admin gibt einmal /raidmaster-einrichten ein."] .. "\n\n"
		.. L["Der Bot legt dann alle Kanäle an: pro Raid einen DKP- und einen Loot-Kanal (z. B. #mc-dkp, #mc-loot), dazu #einteilung und #bot-daten. Ist das schon passiert, einfach weiter."] },
	{ group = 1, title = L["Uploader herunterladen"],
	  text = L["Der Uploader ist ein kleines Programm für den PC, auf dem du WoW spielst. Er braucht Python 3 (kostenlos auf python.org)."] .. "\n\n"
		.. L["Link unten anklicken, mit Strg+C kopieren und im Browser öffnen. Die ZIP entpacken und den Ordner RaidMasterUploader z. B. nach Dokumente legen."],
	  link = G.UPLOADER_URL },
	{ group = 1, title = L["Geheime Verbindung holen"],
	  text = L["Im Discord /uploader eingeben (nur Admins). Der Bot schickt dir die Datei uploader_config.json."] .. "\n\n"
		.. L["Diese Datei in den Ordner RaidMasterUploader legen."] .. "\n\n"
		.. "|cffff5544" .. L["Niemals weitergeben oder posten – sie enthält einen geheimen Link zu eurem Discord."] .. "|r" },
	{ group = 1, title = L["Uploader starten"],
	  text = L["uploader.bat doppelklicken und das Fenster offen lassen. Beim ersten Start sucht er die RaidMaster-Datei von WoW selbst."] .. "\n\n"
		.. L["Automatisch mit Windows starten: Windows-Taste + R, shell:startup eingeben, eine Verknüpfung zu uploader.bat hineinlegen."] .. "\n\n"
		.. L["Test: Knopf unten drücken. Im Uploader-Fenster erscheint \"Hochgeladen\", im Discord zeigt /raidmaster-status den Upload."],
	  reload = true },
	{ group = 1, title = L["Spieler verknüpfen"],
	  text = L["Jeder Spieler registriert sich einmal im Discord: Knopf \"Charakter registrieren\" in der Anmeldung seines Raids oder /charakter."] .. "\n\n"
		.. L["Nur dann bekommt er seine Einteilung und neue Addon-Versionen als Direktnachricht, und /dkp zeigt seine Punkte."] },
	{ group = 2, title = L["Vor dem Raid: Anmeldungen holen"],
	  text = L["Im Discord bei der Aufstellung den Knopf \"Für RaidMaster\" drücken und den Text kopieren."] .. "\n\n"
		.. L["Auf der Seite Anmeldungen einfügen und importieren. RaidMaster lädt dann alle ein und sortiert die Gruppen."],
	  page = "signup" },
	{ group = 2, title = L["Im Raid"],
	  text = L["Auf der Seite Raid den Raid starten. Bosskills, Versteigerungen und Loot erfasst RaidMaster ab dann von selbst."] .. "\n\n"
		.. L["Mehr ist während des Raids nicht zu tun."],
	  page = "raid" },
	{ group = 2, title = L["Einteilung verschicken"],
	  text = L["Auf der Seite Einteilung die Aufgaben verteilen, dann unten \"Jetzt an Discord senden\" drücken."] .. "\n\n"
		.. L["Der Bot postet die Übersicht in #einteilung und schickt jedem verknüpften Spieler seine Aufgabe als Direktnachricht."],
	  page = "assign", reload = true },
	{ group = 2, title = L["Nach dem Raid: DKP an Discord"],
	  text = L["Auf der Seite Raid den Raid beenden. RaidMaster fragt dann, ob die Daten jetzt an Discord gehen sollen – mit Ja wird die Oberfläche kurz neu geladen."] .. "\n\n"
		.. L["Wenige Sekunden später stehen DKP und Loot in den Kanälen des Raids, und jeder kann /dkp im Discord benutzen. Ausloggen schickt die Daten genauso."],
	  page = "raid", reload = true },
}

---------------------------------------------------------------------------
-- Speicherstand: WoW schreibt die Datei bei /reload und beim Ausloggen
---------------------------------------------------------------------------
RM.On("PLAYER_LOGOUT", function()
	if RM.db then RM.db.lastSave = GetServerTime() end
end)

function G.StatusText()
	local last = RM.db and RM.db.lastSave
	local ver = RM.db and RM.db.data and RM.db.data.version or 0
	local parts = {}
	if last then
		parts[#parts + 1] = L["Zuletzt gespeichert: "] .. date("%d.%m. %H:%M", last)
	else
		parts[#parts + 1] = L["Noch nie gespeichert."]
	end
	if ver > 0 and (not last or ver > last) then
		parts[#parts + 1] = "|cffffaa33" .. L["Neue DKP-Daten sind noch nicht im Discord – \"Jetzt an Discord senden\" drücken."] .. "|r"
	elseif last then
		parts[#parts + 1] = "|cff40ff40" .. L["Alles gespeichert – läuft der Uploader, ist Discord aktuell."] .. "|r"
	end
	return table.concat(parts, "   ·   ")
end

function G.SendNow()
	if InCombatLockdown and InCombatLockdown() then
		RM.Print(L["Im Kampf nicht möglich – nach dem Kampf noch einmal."])
		return
	end
	UI.Confirm(L["Jetzt an Discord senden?\nDie Oberfläche wird dafür kurz neu geladen (/reload)."], function() ReloadUI() end)
end

---------------------------------------------------------------------------
-- Inhalt (für die Seite und das Fenster)
---------------------------------------------------------------------------
local function Text(parent, text, size, r, g, b)
	local fs = UI.Text(parent, text, size or 13, r, g, b)
	fs:SetJustifyH("LEFT")
	fs:SetJustifyV("TOP")
	return fs
end

function G.Build(parent)
	RM.db.config.guideDone = RM.db.config.guideDone or {}
	local cur = 1
	local ui = {}

	local head = UI.Header(parent, L["Discord automatisch füttern"])
	head:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, 0)

	local status = Text(parent, "", 11, unpack(COLORS.muted))
	status:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, -28)
	status:SetWidth(780)
	status:SetWordWrap(false)

	-- Schrittliste links
	local buttons = {}
	local y = -58
	for i, s in ipairs(G.STEPS) do
		if i == 1 or G.STEPS[i - 1].group ~= s.group then
			local gl = Text(parent, s.group == 1 and L["Einmal einrichten"] or L["Bei jedem Raid"], 12, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
			gl:SetPoint("TOPLEFT", parent, "TOPLEFT", 2, y)
			y = y - 20
		end
		local b = UI.Button(parent, "", 236, 26, function() cur = i; ui.Refresh() end)
		b:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, y)
		b.label:ClearAllPoints()
		b.label:SetPoint("LEFT", 8, 0)
		b.label:SetPoint("RIGHT", -6, 0)
		b.label:SetJustifyH("LEFT")
		b.label:SetWordWrap(false)
		buttons[i] = b
		y = y - 30
	end

	-- Schritt rechts
	local panel = UI.Frame(parent, 540, 404)
	panel:SetPoint("TOPLEFT", parent, "TOPLEFT", 250, -58)
	UI.Skin(panel, COLORS.panel)
	local num = Text(panel, "", 11, unpack(COLORS.muted))
	num:SetPoint("TOPLEFT", 18, -14)
	local title = Text(panel, "", 17, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
	title:SetPoint("TOPLEFT", 18, -32)
	title:SetWidth(504)
	local body = Text(panel, "", 13)
	body:SetPoint("TOPLEFT", 18, -66)
	body:SetWidth(504)
	if body.SetSpacing then body:SetSpacing(3) end

	local linkLabel = Text(panel, L["Link (anklicken, Strg+A, Strg+C):"], 11, unpack(COLORS.muted))
	linkLabel:SetPoint("BOTTOMLEFT", 18, 92)
	local link = UI.EditBox(panel, 504, 24)
	link:SetPoint("BOTTOMLEFT", 18, 62)
	link:SetScript("OnTextChanged", function(self, user) if user then self:SetText(self.fixed or "") end end)
	link:SetScript("OnEditFocusGained", function(self) self:HighlightText() end)

	local pageBtn = UI.Button(panel, "", 200, 28, function()
		local s = G.STEPS[cur]
		if s.page then
			if G.window then G.window:Hide() end
			UI.Open(s.page)
		end
	end)
	pageBtn:SetPoint("BOTTOMLEFT", 18, 18)
	local sendBtn = UI.Button(panel, L["Jetzt an Discord senden"], 220, 28, function() G.SendNow() end,
		L["Lädt die Oberfläche neu (/reload). Dabei schreibt WoW die Daten, der Uploader schickt sie an den Bot."])
	sendBtn:SetPoint("BOTTOMRIGHT", -18, 18)
	sendBtn:SetAccent(true)

	-- Fuß: erledigt, zurück, weiter
	local done = UI.Check(parent, L["Erledigt"], function() return RM.db.config.guideDone[cur] end,
		function(v) RM.db.config.guideDone[cur] = v or nil; ui.Refresh() end)
	done:SetPoint("TOPLEFT", parent, "TOPLEFT", 252, -478)
	local prev = UI.Button(parent, L["Zurück"], 110, 28, function() if cur > 1 then cur = cur - 1; ui.Refresh() end end)
	prev:SetPoint("TOPLEFT", parent, "TOPLEFT", 562, -474)
	local nextBtn = UI.Button(parent, L["Weiter"], 110, 28, function()
		if cur < #G.STEPS then cur = cur + 1; ui.Refresh() elseif G.window then G.window:Hide() end
	end)
	nextBtn:SetPoint("TOPLEFT", parent, "TOPLEFT", 680, -474)
	nextBtn:SetAccent(true)

	local hint = Text(parent, L["Jederzeit wieder: Seite Discord oder /rm discord."], 11, unpack(COLORS.muted))
	hint:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, -482)
	hint:SetWidth(240)

	function ui.Refresh()
		local doneT = RM.db.config.guideDone
		for i, b in ipairs(buttons) do
			b:SetText((doneT[i] and CHECK or "|cff888888" .. i .. ".|r ") .. G.STEPS[i].title)
			if b.SetAccent then b:SetAccent(i == cur) end
		end
		local s = G.STEPS[cur]
		num:SetText(string.format(L["Schritt %d von %d"], cur, #G.STEPS))
		title:SetText(s.title)
		body:SetText(s.text)
		if s.link then
			link.fixed = s.link
			link:SetText(s.link)
			link:Show(); linkLabel:Show()
		else
			link:Hide(); linkLabel:Hide()
		end
		if s.page and UI.CanSeePage(s.page) and UI.pages[s.page] then
			pageBtn:SetText(L["Seite öffnen: "] .. UI.pages[s.page].title)
			pageBtn:Show()
		else
			pageBtn:Hide()
		end
		if s.reload then sendBtn:Show() else sendBtn:Hide() end
		done:Refresh()
		if cur > 1 then prev:Enable() else prev:Disable() end
		nextBtn:SetText(cur < #G.STEPS and L["Weiter"] or L["Fertig"])
		status:SetText(G.StatusText())
	end
	ui.Refresh()
	return ui.Refresh
end

---------------------------------------------------------------------------
-- Seite "Discord" (Raidleitung und Offiziere) – vor den Einstellungen einordnen
---------------------------------------------------------------------------
UI.AddPage("discord", L["Discord"], function(page) return G.Build(page) end)
do
	local order = UI.pageOrder
	for i, id in ipairs(order) do
		if id == "discord" then table.remove(order, i) break end
	end
	local pos = #order + 1
	for i, id in ipairs(order) do if id == "settings" then pos = i break end end
	table.insert(order, pos, "discord")
end
UI.PAGE_ICONS.discord = "Interface\\Icons\\INV_Letter_15"

---------------------------------------------------------------------------
-- Eigenes Fenster (öffnet sich beim ersten Start)
---------------------------------------------------------------------------
function G.Show()
	if not G.window then
		local f = UI.Frame(UIParent, 830, 620)
		f:SetFrameStrata("DIALOG")
		f:SetToplevel(true)
		f:SetClampedToScreen(true)
		UI.Skin(f)
		UI.MakeMovable(f, "guide", "CENTER", 0, 30)
		_G["RaidMasterGuideFrame"] = f
		tinsert(UISpecialFrames, "RaidMasterGuideFrame")
		local t = UI.Text(f, "RaidMaster · " .. L["Anleitung"], 15, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
		t:SetPoint("TOPLEFT", 20, -14)
		local close = UI.CloseButton(f, function() f:Hide() end)
		close:SetPoint("TOPRIGHT", -8, -8)
		local content = UI.Frame(f, 790, 556)
		content:SetPoint("TOPLEFT", 20, -46)
		f.refresh = G.Build(content)
		f:SetScript("OnShow", function() if f.refresh then f.refresh() end end)
		G.window = f
	end
	G.window:Show()
	if G.window.refresh then G.window.refresh() end
end

function G.Toggle()
	if G.window and G.window:IsShown() then G.window:Hide() else G.Show() end
end

-- Erster Start: Raidleitung und Offizieren die Anleitung einmal zeigen (Gildenränge brauchen etwas)
RM.On("PLAYER_LOGIN", function()
	if not RM.db then return end
	RM.db.config.guideDone = RM.db.config.guideDone or {}
	C_Timer.After(10, function()
		if RM.db.config.guideSeen then return end
		if RaidMasterTestDB then return end
		if RM.CanEdit() or RM.IsMainLeader() or UI.IsRaidLead() then
			RM.db.config.guideSeen = true
			G.Show()
		end
	end)
end)

-- Nach dem Raid: Daten gleich an Discord senden?
if RM.Raid and RM.Raid.End then
	local origEnd = RM.Raid.End
	RM.Raid.End = function(...)
		local was = RM.db and RM.db.session and RM.db.session.active
		local r = origEnd(...)
		if was and not RM.db.session.active and RM.CanEdit() and not RaidMasterTestDB then
			C_Timer.After(1.5, function()
				UI.Confirm(L["Raid beendet. DKP und Loot jetzt an Discord senden?\nDie Oberfläche wird dafür kurz neu geladen (/reload)."], function() ReloadUI() end)
			end)
		end
		return r
	end
end
