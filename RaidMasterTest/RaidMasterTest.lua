-- ============================================================================
-- RaidMaster Test – kleines Werkzeug, um RaidMaster im Spiel auszuprobieren
--
-- Testmodus: alles, was du hier machst, bleibt bei dir:
--   * Raid-, DKP- und Lootdaten werden beim Start gesichert und beim Beenden
--     (oder beim nächsten Einloggen) wiederhergestellt
--   * keine Addon-Nachrichten an Gilde/Raid, Raidchat-Texte erscheinen nur bei dir
--   * ein Testraid mit 10 Testspielern wird vorgespielt
-- Öffnen: /rmtest
-- ============================================================================

local RM = RaidMaster
if not RM or not RM.UI then
	print("|cffff5544RaidMaster Test:|r RaidMaster ist nicht geladen.")
	return
end
local UI = RM.UI
local COLORS = UI.COLORS
local T = { active = false, role = "officer", log = {} }
RaidMasterTest = T

local FAKE = {
	{ "Testkrieger", "WARRIOR" }, { "Testpriester", "PRIEST" }, { "Testmagier", "MAGE" }, { "Testjaegerin", "HUNTER" },
	{ "Testschurke", "ROGUE" }, { "Testjaeger", "HUNTER" }, { "Testhexer", "WARLOCK" },
	{ "Testdruide", "DRUID" }, { "Testpaladin", "PALADIN" }, { "Testschamane", "SHAMAN" },
}
local ROLE_NAMES = { member = "Teilnehmer", lead = "Co-Raidleiter", officer = "Offizier" }

local function Log(msg)
	local line = date("%H:%M:%S") .. "  " .. msg
	table.insert(T.log, 1, line)
	while #T.log > 60 do table.remove(T.log) end
	print("|cffff8c1a[RM-Test]|r " .. msg)
	if T.Refresh then T.Refresh() end
end

local function Copy(v)
	if type(v) ~= "table" then return v end
	local c = {}
	for k, x in pairs(v) do c[k] = Copy(x) end
	return c
end

---------------------------------------------------------------------------
-- Testmodus: Daten sichern, RaidMaster-Funktionen umleiten
---------------------------------------------------------------------------
local saved = {}
local OVERRIDE = { "InRaid", "RaidMembers", "IsAssist", "IsLeader", "CanEdit", "SendAddonMessage", "RaidChat", "Announce", "Whisper" }

local function FakeMembers()
	local list = { { name = RM.Me(), class = select(2, UnitClass("player")), online = true, rank = 2, index = 1 } }
	for i, f in ipairs(FAKE) do list[#list + 1] = { name = f[1], class = f[2], online = true, rank = 0, index = i + 1 } end
	return list
end

function T.Start()
	if T.active then return end
	local db = RM.db
	RaidMasterTestDB = { data = Copy(db.data), session = Copy(db.session), trade = Copy(db.trade), config = Copy(db.config) }
	for _, k in ipairs(OVERRIDE) do saved[k] = RM[k] end
	saved.Deliver = RM.Loot and RM.Loot.Deliver
	RM.InRaid = function() return true end
	RM.RaidMembers = FakeMembers
	RM.IsAssist = function() return T.role ~= "member" end
	RM.IsLeader = function() return T.role ~= "member" end
	RM.CanEdit = function() return T.role == "officer" end
	RM.SendAddonMessage = function() T.blocked = (T.blocked or 0) + 1 end
	RM.RaidChat = function(msg, ch) print("|cffff7f00[Test-" .. (ch or "RAID") .. "]|r " .. msg) end
	RM.Whisper = function(msg, target) print("|cffff80ff[Test-Flüstern an " .. tostring(target) .. "]|r " .. msg) end
	RM.Announce = function(msg, warning) print("|cffff4800[Test-" .. (warning and "Raidwarnung" or "Raid") .. "]|r " .. msg) end
	if RM.Loot then RM.Loot.Deliver = function(link, name) Log("Item würde übergeben: " .. tostring(link) .. " -> " .. tostring(name)) end end
	-- Testspieler mit 100 DKP im aktuellen Topf
	local pool = RM.DKP.ActivePool()
	for _, f in ipairs(FAKE) do
		local p = RM.DKP.EnsurePlayer(f[1], f[2])
		p.d = p.d or {}
		p.d[pool] = 100
	end
	T.active = true
	T.blocked = 0
	Log("Testmodus AN – Daten gesichert, keine Nachrichten an Gilde/Raid. Testraid mit 10 Testspielern.")
	RM.Fire("SESSION_CHANGED"); RM.Fire("DATA_CHANGED")
end

-- Inhalt einer Tabelle ersetzen, ohne die Tabelle selbst zu tauschen (andere Teile halten Verweise)
local function Replace(target, source)
	if type(target) ~= "table" or type(source) ~= "table" then return end
	for k in pairs(target) do target[k] = nil end
	for k, v in pairs(source) do target[k] = v end
end

local function Restore(silent)
	local b = RaidMasterTestDB
	if b and RM.db then
		local pos = RM.db.config and RM.db.config.positions
		Replace(RM.db.data, b.data)
		Replace(RM.db.session, b.session)
		Replace(RM.db.trade, b.trade)
		Replace(RM.db.config, b.config)
		if pos then RM.db.config.positions = pos end
	end
	RaidMasterTestDB = nil
	if not silent then RM.Fire("SESSION_CHANGED"); RM.Fire("DATA_CHANGED"); RM.Fire("CONFIG_CHANGED") end
end

function T.Stop()
	if not T.active then return end
	if RM.Auction and RM.Auction.current then pcall(RM.Auction.Cancel) end
	for _, k in ipairs(OVERRIDE) do RM[k] = saved[k] end
	if RM.Loot and saved.Deliver then RM.Loot.Deliver = saved.Deliver end
	T.active = false
	Restore()
	Log(string.format("Testmodus AUS – alle Daten wiederhergestellt (%d Addon-Nachrichten wurden zurückgehalten).", T.blocked or 0))
end

-- Abgestürzt/ausgeloggt mitten im Test: beim nächsten Laden zurücksetzen
local loader = CreateFrame("Frame")
loader:RegisterEvent("PLAYER_LOGIN")
loader:SetScript("OnEvent", function()
	if RaidMasterTestDB then
		Restore(true)
		print("|cffff8c1a[RM-Test]|r Testdaten vom letzten Mal entfernt – deine echten Daten sind wiederhergestellt.")
	end
end)

function T.SetRole(role)
	T.role = role
	if not T.active then T.Start() end
	Log("Ansicht als " .. ROLE_NAMES[role] .. ".")
	RM.Fire("CONFIG_CHANGED"); RM.Fire("SESSION_CHANGED")
	if RM.Markers and RM.Markers.UpdateBar then RM.Markers.UpdateBar() end
	if RM.UI.RefreshCurrent then RM.UI.RefreshCurrent() end
end

---------------------------------------------------------------------------
-- Simulationen (Testraid: 10 Testspieler + du)
---------------------------------------------------------------------------
local function Need()
	if not T.active then T.Start() end
	if T.role ~= "officer" then
		Log("Für Raid, Bosskill und Versteigerung bitte 'Ansicht als: Offizier' wählen.")
		return false
	end
	return true
end

function T.StartRaid()
	if not Need() then return end
	RM.db.config.activePool = T.pool
	RM.Raid.Start()
	Log("Raid gestartet (" .. RM.DKP.PoolName(T.pool) .. ").")
end

function T.EndRaid()
	if not Need() then return end
	RM.Raid.End()
	Log("Raid beendet.")
end

function T.BossKill()
	if not Need() then return end
	local b = T.boss and RM.Data.Bosses[T.boss]
	if not b then Log("Bitte zuerst einen Boss wählen.") return end
	if not RM.db.session.active then RM.db.config.activePool = b.pool; RM.Raid.Start() end
	local id = b.e[#b.e]
	RM.SimulateEvent("ENCOUNTER_START", id, b.name, 14, 10)
	C_Timer.After(1, function()
		RM.SimulateEvent("ENCOUNTER_END", id, b.name, 14, 10, 1)
		Log("Bosskill simuliert: " .. b.name .. " (Vorlage: " .. RM.Data.GetTemplate(RM.db.config.markerTemplate).name .. ").")
	end)
end

function T.Auction(link)
	if not Need() then return end
	if not link or not link:find("item:") then
		link = select(2, (RM.GetItemInfo or GetItemInfo)(6948)) or "|cffffffff|Hitem:6948::::::::60:::::|h[Ruhestein]|h|r"
	end
	RM.Auction.Start(link)
	if not RM.Auction.current then Log("Versteigerung konnte nicht starten.") return end
	Log("Versteigerung gestartet: " .. link .. " – Testspieler bieten gleich.")
	local amounts = { 10, 15, 25, 30 }
	for i, amount in ipairs(amounts) do
		local who = FAKE[(i % #FAKE) + 1][1]
		C_Timer.After(2 + i * 2, function()
			local ok, err = RM.Auction.ReceiveBid(who, amount, "")
			Log(who .. " bietet " .. amount .. " DKP" .. (ok and "" or (" – abgelehnt: " .. tostring(err))))
		end)
	end
end

-- Magmadar: Jäger nach Einlullender Schuss fragen; die Testjäger antworten per Flüstern
function T.TranqTest()
	if not T.active then T.Start() end
	if T.role == "member" then Log("Die Jäger-Abfrage gibt es nur für Raidleiter/Co-Raidleiter/Offiziere.") return end
	RM.Tranq.Ask()
	Log("Jäger-Abfrage gestartet – Testjaeger antwortet 'ja', Testjaegerin 'nein'.")
	C_Timer.After(5, function()
		RM.SimulateEvent("CHAT_MSG_WHISPER", "ja", "Testjaeger")
		RM.SimulateEvent("CHAT_MSG_WHISPER", "nein", "Testjaegerin")
		Log("Antworten: " .. RM.Tranq.StatusText():gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""))
		RM.Tranq.Post()
		Log("Einlull-Rotation als Schlachtzugwarnung gepostet (im Test nur bei dir).")
	end)
end

---------------------------------------------------------------------------
-- Selbsttest: was kann dieser Client, ist RaidMaster richtig eingestellt?
---------------------------------------------------------------------------
function T.SelfTest()
	local out = {}
	local function line(ok, text) out[#out + 1] = (ok == nil and "|cffbbbbbb•|r " or ok and "|cff40ff40OK|r  " or "|cffff5544!!|r  ") .. text end
	line(true, "RaidMaster " .. RM.VERSION .. " – " .. RM.GameInfoText())
	line(true, "Sprache: " .. (RM.LANGUAGES[RM.LOCALE] or RM.LOCALE) .. " (Client " .. tostring(RM.GAME_LOCALE) .. ")")
	line(#RM.Data.RaidList > 0, string.format("Raids dieser Version: %d mit %d Bossen, %d Markierungsvorlagen", #RM.Data.RaidList, #RM.Data.BossOrder, #RM.Data.MarkerTemplates))
	local noInfo = 0
	for _, id in ipairs(RM.Data.BossOrder) do if not RM.Data.BossInfo[id] then noInfo = noInfo + 1 end end
	line(noInfo == 0, "Boss-Taktiken: " .. (noInfo == 0 and "alle vorhanden" or (noInfo .. " fehlen")))
	line(RM.Caps.masterLoot, "Plündermeister: " .. (RM.Caps.masterLoot and "verfügbar" or "nicht verfügbar (Retail: Handel statt Verteilen)"))
	line(RM.Caps.specs or RM.Caps.talentTrees, "Skillungen: " .. (RM.Caps.specs and "Spezialisierungen" or RM.Caps.talentTrees and "Talentbäume" or "nicht lesbar"))
	line(C_ChatInfo ~= nil or SendAddonMessage ~= nil, "Addon-Nachrichten (Sync, Gebote): " .. ((C_ChatInfo or SendAddonMessage) and "ok" or "fehlt"))
	local plates = GetCVar and GetCVar("nameplateShowEnemies")
	line(plates == "1", "Gegner-Namensplaketten: " .. (plates == "1" and "an" or "AUS – für 'Adds markieren' Taste V drücken"))
	line(IsInGuild(), "Gilde: " .. (RM.MyGuild() or "keine"))
	local edit = (saved.CanEdit or RM.CanEdit)()
	line(nil, "Deine Rechte: " .. (edit and "Offizier (DKP ändern, versteigern)" or "keine Offiziersrechte"))
	local inRaid = (saved.InRaid or RM.InRaid)()
	line(nil, "Gruppe: " .. (inRaid and ("im Raid" .. (((saved.IsAssist or RM.IsAssist)()) and ", Raidleiter/Assistent" or "")) or "kein Raid"))
	if inRaid then
		local m = RM.GetLootMethod and RM.GetLootMethod()
		line(m == "master" or not RM.Caps.masterLoot, "Plündermethode: " .. tostring(m))
	end
	local d = RM.db.data
	local players = 0
	for _ in pairs(d.players or {}) do players = players + 1 end
	line(true, string.format("Daten: %d Spieler, %d Log-Einträge, Stand %s", players, #(d.log or {}), d.version > 0 and RM.FormatTime(math.min(d.version, GetServerTime())) or "leer"))
	line(nil, "Testmodus: " .. (T.active and ("AN, Ansicht als " .. ROLE_NAMES[T.role]) or "aus"))
	T.selfTest = table.concat(out, "\n")
	Log("Selbsttest ausgeführt.")
end

---------------------------------------------------------------------------
-- Fenster
---------------------------------------------------------------------------
local win
local function Section(parent, text, y)
	local h = UI.Header(parent, text)
	h:SetPoint("TOPLEFT", 14, y)
	return h
end

local function CreateWindow()
	local f = UI.Frame(UIParent, 560, 640)
	UI.Skin(f)
	f:SetFrameStrata("HIGH")
	f:SetClampedToScreen(true)
	UI.MakeMovable(f, "testTool", "CENTER", 300, 0)
	_G.RaidMasterTestFrame = f
	tinsert(UISpecialFrames, "RaidMasterTestFrame")

	local title = UI.Text(f, "RaidMaster |cffffffffTest|r", 16, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
	title:SetPoint("TOPLEFT", 14, -12)
	local close = UI.CloseButton(f, function() f:Hide() end)
	close:SetPoint("TOPRIGHT", -8, -8)

	f.status = UI.Text(f, "", 12)
	f.status:SetPoint("TOPLEFT", 14, -40)
	f.status:SetWidth(530)
	local toggle = UI.Button(f, "", 260, 28, function() if T.active then T.Stop() else T.Start() end end,
		"Testmodus: Daten werden gesichert und beim Beenden wiederhergestellt.\nKeine Nachrichten an Gilde oder Raid.")
	toggle:SetPoint("TOPLEFT", 14, -62)
	local selfBtn = UI.Button(f, "Selbsttest", 120, 28, function() T.SelfTest() end, "Prüft Spielversion, Daten, Rechte und Einstellungen.")
	selfBtn:SetPoint("LEFT", toggle, "RIGHT", 8, 0)
	local openBtn = UI.Button(f, "RaidMaster öffnen", 130, 28, function() RM.UI.Open() end)
	openBtn:SetPoint("LEFT", selfBtn, "RIGHT", 8, 0)

	Section(f, "Ansicht als", -104)
	local roleBtns = {}
	local x = 14
	for _, role in ipairs({ "member", "lead", "officer" }) do
		local b = UI.Button(f, ROLE_NAMES[role], 140, 26, function() T.SetRole(role) end,
			role == "member" and "Sieht nur DKP-Stände und Versteigerung, keine Symbolleiste." or
			role == "lead" and "Raidleiter/Assistent: Raid-Seiten und Symbolleiste, kein DKP ändern." or
			"Offizier: alles, auch DKP, Versteigerung und Einstellungen.")
		b:SetPoint("TOPLEFT", x, -128)
		roleBtns[role] = b
		x = x + 148
	end

	Section(f, "Raid simulieren", -170)
	T.pool = RM.DKP.ActivePool()
	local raidDrop = UI.Dropdown(f, 230, function() return UI.PoolGroups(RM.db.data) end, function() return T.pool end, function(v)
		T.pool = v
		local def = RM.Data.Pools[v]
		T.boss = def and def.bossIDs and def.bossIDs[1]
		T.Refresh()
	end, "Raid für den Test")
	raidDrop:SetPoint("TOPLEFT", 14, -194)
	local def0 = RM.Data.Pools[T.pool]
	T.boss = def0 and def0.bossIDs and def0.bossIDs[1]
	local bossDrop = UI.Dropdown(f, 230, function()
		local def = RM.Data.Pools[T.pool]
		local items = {}
		for _, id in ipairs(def and def.bossIDs or {}) do items[#items + 1] = { id, RM.Data.Bosses[id].name } end
		return { { items = items } }
	end, function() return T.boss end, function(v) T.boss = v end, "Boss für den Bosskill")
	bossDrop:SetPoint("LEFT", raidDrop, "RIGHT", 10, 0)
	local startBtn = UI.Button(f, "Raid starten", 126, 26, function() T.StartRaid() end, "Startet eine Raid-Sitzung mit Pünktlichkeitsbonus.")
	startBtn:SetPoint("TOPLEFT", 14, -226)
	local killBtn = UI.Button(f, "Bosskill", 126, 26, function() T.BossKill() end,
		"Spielt Bosskampf-Beginn und -Ende vor: Boss-DKP, Erstkill, automatische Markierungsvorlage.")
	killBtn:SetPoint("LEFT", startBtn, "RIGHT", 8, 0)
	killBtn:SetAccent(true)
	local endBtn = UI.Button(f, "Raid beenden", 126, 26, function() T.EndRaid() end, "Beendet die Sitzung mit Abschlussbonus.")
	endBtn:SetPoint("LEFT", killBtn, "RIGHT", 8, 0)
	local tqBtn = UI.Button(f, "Jäger-Abfrage", 120, 26, function() T.TranqTest() end,
		"Magmadar: fragt die Jäger nach Einlullender Schuss und postet die Rotation (Testjäger antworten selbst).")
	tqBtn:SetPoint("LEFT", endBtn, "RIGHT", 8, 0)

	Section(f, "Versteigerung", -268)
	local itemBox = UI.LinkBox(f, 300, 26)
	itemBox:SetPoint("TOPLEFT", 14, -292)
	local hint = UI.Text(itemBox, "Item per Shift-Klick (leer = Ruhestein)", 11, unpack(COLORS.muted))
	hint:SetPoint("LEFT", 8, 0)
	itemBox:HookScript("OnTextChanged", function(self) if self:GetText() == "" then hint:Show() else hint:Hide() end end)
	itemBox:HookScript("OnEditFocusGained", function() hint:Hide() end)
	local aucBtn = UI.Button(f, "Mit Testgeboten versteigern", 220, 26, function() T.Auction(itemBox:GetText()) end,
		"Startet eine Versteigerung; 4 Testspieler bieten nacheinander. Danach fragt RaidMaster wie im echten Raid, ob vergeben wird.")
	aucBtn:SetPoint("LEFT", itemBox, "RIGHT", 8, 0)

	Section(f, "Schlachtzugsymbole (echt, z. B. an Trainingspuppen)", -334)
	local m1 = UI.Button(f, "Totenkopf aufs Ziel", 160, 26, function() RM.Markers.Mark(8) end)
	m1:SetPoint("TOPLEFT", 14, -358)
	local m2 = UI.Button(f, "Adds markieren", 160, 26, function() RM.Markers.MarkAdds() end, "Markiert alle sichtbaren Gegner nach der gewählten Vorlage.")
	m2:SetPoint("LEFT", m1, "RIGHT", 8, 0)
	local m3 = UI.Button(f, "Alle aus", 120, 26, function() RM.Markers.ClearAll() end)
	m3:SetPoint("LEFT", m2, "RIGHT", 8, 0)

	Section(f, "Protokoll", -400)
	local box = UI.Multiline(f, 532, 210, true)
	box:SetPoint("TOPLEFT", 14, -424)

	function T.Refresh()
		if not f:IsShown() then return end
		f.status:SetText(T.active and ("|cffff8c1aTestmodus AN|r – Ansicht als |cffffffff" .. ROLE_NAMES[T.role] .. "|r. Deine echten Daten sind gesichert.")
			or "|cff999999Testmodus aus.|r Starte ihn, um gefahrlos zu testen – beim Beenden wird alles zurückgesetzt.")
		toggle:SetText(T.active and "Testmodus beenden (alles zurücksetzen)" or "Testmodus starten")
		toggle:SetAccent(not T.active)
		for role, b in pairs(roleBtns) do b:SetAccent(T.active and T.role == role) end
		raidDrop:Refresh(); bossDrop:Refresh()
		local text = T.selfTest and (T.selfTest .. "\n\n") or ""
		box:SetText(text .. table.concat(T.log, "\n"))
	end
	f:SetScript("OnShow", function() T.Refresh() end)
	return f
end

function T.Toggle()
	win = win or CreateWindow()
	if win:IsShown() then win:Hide() else win:Show(); T.Refresh() end
end

SLASH_RAIDMASTERTEST1 = "/rmtest"
SlashCmdList["RAIDMASTERTEST"] = function(msg)
	msg = (msg or ""):lower()
	if msg == "start" then T.Start()
	elseif msg == "stop" or msg == "ende" then T.Stop()
	elseif msg == "check" or msg == "selbsttest" then T.SelfTest(); if not (win and win:IsShown()) then print((T.selfTest or ""):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")) end
	else T.Toggle() end
end
