-- RaidMaster - Core
-- Namensraum, Events, gespeicherte Daten, Rechte und Hilfsfunktionen

local ADDON, RM = ...
local L = RM.L
RaidMaster = RM

RM.VERSION = "1.7.2"
RM.VERSION_NUM = 10702
RM.PREFIX = "RaidMstr"

---------------------------------------------------------------------------
-- Spielversion erkennen (Classic Era, WoW Forever, TBC, Wrath, Cata, MoP, Retail)
---------------------------------------------------------------------------
do
	local version, build, _, toc = GetBuildInfo()
	RM.GAME_VERSION = version or "?"
	RM.GAME_BUILD = build or "?"
	RM.TOC = tonumber(toc) or 0
end

-- Bekannte Spielversionen: Schlüssel, Name, TOC von/bis, zuletzt getestete Interface-Nummer
RM.GAMES = {
	{ key = "retail",  name = L["Retail"],                       from = 100000, to = 999999, tested = 120105 },
	{ key = "mists",   name = L["Mists of Pandaria Classic"],    from = 50000,  to = 59999,  tested = 50504 },
	{ key = "cata",    name = L["Cataclysm Classic"],            from = 40000,  to = 49999,  tested = 40402 },
	{ key = "titan",   name = L["Wrath of the Lich King (Titan Reforged)"], from = 38000, to = 38999, tested = 38002 },
	{ key = "wrath",   name = L["Wrath of the Lich King Classic"], from = 30000, to = 37999, tested = 30405 },
	{ key = "tbc",     name = L["The Burning Crusade Classic"],  from = 20000,  to = 29999,  tested = 20506 },
	{ key = "forever", name = L["WoW Forever"],                  from = 16000,  to = 16999,  tested = 16001 },
	{ key = "era",     name = L["Classic Era"],                  from = 10000,  to = 15999,  tested = 11509 },
}

function RM.DetectGame()
	for _, g in ipairs(RM.GAMES) do
		if RM.TOC >= g.from and RM.TOC <= g.to then return g end
	end
	return { key = "unknown", name = L["Unbekannte Version"], from = 0, to = 0, tested = 0 }
end
RM.GAME = RM.DetectGame()
RM.IsRetail = RM.GAME.key == "retail"
RM.IsClassicEra = RM.GAME.key == "era" or RM.GAME.key == "forever"

-- Was kann dieser Client? (wird im ganzen Addon abgefragt statt Versionsnummern zu vergleichen)
RM.Caps = {
	masterLoot = (GiveMasterLoot ~= nil and GetMasterLootCandidate ~= nil) and not RM.IsRetail,
	specs = (GetSpecialization ~= nil and RM.TOC >= 50000),
	talentTrees = (GetTalentTabInfo ~= nil and RM.TOC < 50000),
}

---------------------------------------------------------------------------
-- Kompatibilität (Classic-Client, verschiedene API-Stände)
---------------------------------------------------------------------------
RM.GetItemInfo = (C_Item and C_Item.GetItemInfo) or GetItemInfo
RM.GetItemInfoInstant = (C_Item and C_Item.GetItemInfoInstant) or GetItemInfoInstant
RM.SendAddonMessage = (C_ChatInfo and C_ChatInfo.SendAddonMessage) or SendAddonMessage
local RegisterPrefix = (C_ChatInfo and C_ChatInfo.RegisterAddonMessagePrefix) or RegisterAddonMessagePrefix

RM.Container = {
	NumSlots = (C_Container and C_Container.GetContainerNumSlots) or GetContainerNumSlots,
	ItemLink = (C_Container and C_Container.GetContainerItemLink) or GetContainerItemLink,
	Pickup = (C_Container and C_Container.PickupContainerItem) or PickupContainerItem,
}

local LOOT_METHOD_BY_ENUM = { [0] = "freeforall", [1] = "roundrobin", [2] = "master", [3] = "group", [4] = "needbeforegreed", [5] = "personal" }

-- Liefert Methode als Text ("master" ...), Gruppenindex, Raidindex
function RM.GetLootMethod()
	if GetLootMethod then
		return GetLootMethod()
	elseif C_PartyInfo and C_PartyInfo.GetLootMethod then
		local m, partyIndex, raidIndex = C_PartyInfo.GetLootMethod()
		return LOOT_METHOD_BY_ENUM[m] or tostring(m), partyIndex, raidIndex
	end
end

function RM.SetLootMethod(method, name)
	if SetLootMethod then
		SetLootMethod(method, name)
	elseif C_PartyInfo and C_PartyInfo.SetLootMethod then
		local enum = 2
		for k, v in pairs(LOOT_METHOD_BY_ENUM) do if v == method then enum = k end end
		C_PartyInfo.SetLootMethod(enum, name)
	end
end

function RM.GetLootThreshold()
	if GetLootThreshold then return GetLootThreshold() end
	if C_PartyInfo and C_PartyInfo.GetLootThreshold then return C_PartyInfo.GetLootThreshold() end
end

function RM.SetLootThreshold(n)
	if SetLootThreshold then SetLootThreshold(n)
	elseif C_PartyInfo and C_PartyInfo.SetLootThreshold then C_PartyInfo.SetLootThreshold(n) end
end

---------------------------------------------------------------------------
-- Standardwerte
---------------------------------------------------------------------------
-- Synchronisierte Einstellungen (gelten für die ganze Gilde)
RM.DEFAULT_SETTINGS = {
	dkpStart = 10,
	dkpEnd = 10,
	defaultBossDKP = 10,
	bossDKP = {},             -- [encounterID] = Punkte (sonst Standard aus Data/RaidData)
	firstKillDouble = true,
	decayPct = 10,
	minBid = 10,
	bidIncrement = 5,
	auctionTime = 30,
	antiSnipe = true,
	officerRank = 1,          -- Gildenränge 0..officerRank dürfen DKP ändern
	allowNegative = false,
	onlyOnline = false,
	standbyGetsDKP = true,
}

-- Lokale Einstellungen (nur dieser Spieler)
RM.DEFAULT_CONFIG = {
	lootMaster = "",
	lootThreshold = 3,        -- 3 = Rar (blau), 4 = Episch
	setLootOnStart = true,
	autoDistribute = true,
	announceLoot = true,
	autoNext = true,
	announceBids = true,
	whisperReplies = true,
	tradeFallback = true,
	rules = { epic = "auction", blue = "auction", recipe = "bank", mats = "bank" },
	fallback = "de",
	bankChar = "",
	deChar = "",
	crafterChar = "",
	coreHound = true,
	unlootedReminder = true,
	markerBar = true,
	markerTemplate = "standard",
	autoTemplate = true,       -- beim Bosskampf automatisch die Vorlage des Bosses
	markerLocked = false,
	standby = {},
	activePool = "mc",
	autoInvite = true,
	autoInviteMinutes = 15,
	autoGroups = true,
	assignTanks = "",
	instanceMap = {},
	specScan = true,
	adLink = "",
	adChannel = "",
	adText = "",
	adAutoInvite = true,
	softresLink = "",
	minimap = { angle = 215, hide = false },
	positions = {},
}

---------------------------------------------------------------------------
-- Hilfsfunktionen
---------------------------------------------------------------------------
local function FillDefaults(t, defaults)
	for k, v in pairs(defaults) do
		if t[k] == nil then
			if type(v) == "table" then
				t[k] = {}
				FillDefaults(t[k], v)
			else
				t[k] = v
			end
		elseif type(v) == "table" and type(t[k]) == "table" then
			FillDefaults(t[k], v)
		end
	end
	return t
end
RM.FillDefaults = FillDefaults

function RM.CopyTable(t)
	if type(t) ~= "table" then return t end
	local c = {}
	for k, v in pairs(t) do c[k] = RM.CopyTable(v) end
	return c
end

function RM.Short(name)
	if not name then return nil end
	return (name:gsub("%-.*$", ""))
end

function RM.Me()
	return RM.Short(UnitName("player"))
end

function RM.Round(x)
	if x >= 0 then return math.floor(x + 0.5) end
	return -math.floor(-x + 0.5)
end

function RM.Print(msg)
	DEFAULT_CHAT_FRAME:AddMessage("|cffff8c1aRaidMaster:|r " .. tostring(msg))
end

function RM.ClassColor(class, text)
	local c = class and RAID_CLASS_COLORS and RAID_CLASS_COLORS[class]
	if c then
		return string.format("|cff%02x%02x%02x%s|r", c.r * 255, c.g * 255, c.b * 255, text)
	end
	return text
end

function RM.ItemString(link)
	return link and link:match("|H(item:[^|]+)|h")
end

function RM.ItemID(link)
	return link and tonumber(link:match("item:(%d+)"))
end

local QUALITY_BY_COLOR = { ["9d9d9d"] = 0, ["ffffff"] = 1, ["1eff00"] = 2, ["0070dd"] = 3, ["a335ee"] = 4, ["ff8000"] = 5, ["e6cc80"] = 6 }
function RM.ItemQuality(link)
	if not link then return 0 end
	local _, _, q = RM.GetItemInfo(link)
	if q then return q end
	local hex = link:match("|cff(%x%x%x%x%x%x)")
	return hex and QUALITY_BY_COLOR[hex:lower()] or 1
end

function RM.FormatTime(t)
	return date("%d.%m. %H:%M", t)
end

---------------------------------------------------------------------------
-- Gruppe / Raid
---------------------------------------------------------------------------
function RM.InRaid()
	return IsInRaid and IsInRaid() or (GetNumRaidMembers and GetNumRaidMembers() > 0)
end

function RM.IsLeader()
	return UnitIsGroupLeader("player")
end

function RM.IsAssist()
	return UnitIsGroupLeader("player") or UnitIsGroupAssistant("player")
end

-- Liste der Raidmitglieder: { {name=, class=, online=, rank=} }
function RM.RaidMembers()
	local list = {}
	if not RM.InRaid() then return list end
	for i = 1, GetNumGroupMembers() do
		local name, rank, _, _, _, class, _, online = GetRaidRosterInfo(i)
		if name then
			list[#list + 1] = { name = RM.Short(name), class = class, online = online and true or false, rank = rank, index = i }
		end
	end
	return list
end

function RM.IsInMyRaid(name)
	name = RM.Short(name)
	if name == RM.Me() and RM.InRaid() then return true end
	for _, m in ipairs(RM.RaidMembers()) do
		if m.name == name then return true, m end
	end
	return false
end

function RM.IAmMasterLooter()
	if not RM.Caps.masterLoot then return false end
	local method, partyIndex, raidIndex = RM.GetLootMethod()
	if method ~= "master" then return false end
	if RM.InRaid() and raidIndex then
		local name = GetRaidRosterInfo(raidIndex)
		return RM.Short(name) == RM.Me()
	end
	return partyIndex == 0
end

function RM.MasterLooterName()
	local method, partyIndex, raidIndex = RM.GetLootMethod()
	if method ~= "master" then return nil end
	if RM.InRaid() and raidIndex then
		return RM.Short((GetRaidRosterInfo(raidIndex)))
	elseif partyIndex == 0 then
		return RM.Me()
	elseif partyIndex then
		return RM.Short(UnitName("party" .. partyIndex))
	end
end

-- Nachricht an den Raid (Raidwarnung wenn möglich)
function RM.Announce(msg, warning)
	if RM.InRaid() then
		if warning and RM.IsAssist() then
			SendChatMessage(msg, "RAID_WARNING")
		else
			SendChatMessage(msg, "RAID")
		end
	else
		RM.Print(msg)
	end
end

-- Lange Texte in mehrere Chatnachrichten aufteilen
function RM.AnnounceLines(prefix, parts, perLine)
	perLine = perLine or 3
	local line = {}
	local first = true
	for i, p in ipairs(parts) do
		line[#line + 1] = p
		if #line >= perLine or i == #parts then
			local text = table.concat(line, " ")
			if first then text = prefix .. text; first = false end
			RM.Announce(text, false)
			wipe(line)
		end
	end
end

---------------------------------------------------------------------------
-- Gilde und Rechte
---------------------------------------------------------------------------
RM.guild = { rank = {}, class = {}, loaded = false }

local function RebuildGuild()
	if not IsInGuild() then return end
	wipe(RM.guild.rank)
	wipe(RM.guild.class)
	local n = GetNumGuildMembers()
	for i = 1, n do
		local name, _, rankIndex, _, _, _, _, _, _, _, classFile = GetGuildRosterInfo(i)
		if name then
			name = RM.Short(name)
			RM.guild.rank[name] = rankIndex
			RM.guild.class[name] = classFile
		end
	end
	if n > 0 then RM.guild.loaded = true end
	RM.Fire("GUILD_CHANGED")
end

function RM.RequestGuildRoster()
	if not IsInGuild() then return end
	if C_GuildInfo and C_GuildInfo.GuildRoster then C_GuildInfo.GuildRoster() elseif GuildRoster then GuildRoster() end
end

function RM.IsOfficer(name)
	name = RM.Short(name)
	local rank = RM.guild.rank[name]
	if rank == nil and name == RM.Me() then
		local _, _, rankIndex = GetGuildInfo("player")
		rank = rankIndex
	end
	if rank == nil then return false end
	local limit = (RM.db and RM.db.data.settings.officerRank) or 1
	return rank <= limit
end

-- Darf dieser Spieler DKP verändern?
function RM.CanEdit()
	return RM.IsOfficer(RM.Me())
end

-- Name der eigenen Gilde (nil ohne Gilde)
function RM.MyGuild()
	if not IsInGuild() then return nil end
	local g = GetGuildInfo("player")
	if g and g ~= "" then return g end
	return nil
end

-- Vertrauenswürdige Quelle für fremde Raid-Daten:
-- Raidleiter, Assistent oder Plündermeister im eigenen Raid
function RM.IsRaidAuthority(name)
	name = RM.Short(name)
	if not RM.InRaid() then return false end
	local inRaid, m = RM.IsInMyRaid(name)
	if not inRaid or not m then return false end
	if (m.rank or 0) >= 1 then return true end
	return RM.MasterLooterName() == name
end

---------------------------------------------------------------------------
-- Interne Nachrichten (UI-Aktualisierung usw.)
---------------------------------------------------------------------------
local listeners = {}
function RM.Listen(msg, fn)
	listeners[msg] = listeners[msg] or {}
	table.insert(listeners[msg], fn)
end

function RM.Fire(msg, ...)
	local l = listeners[msg]
	if not l then return end
	for _, fn in ipairs(l) do
		local ok, err = pcall(fn, ...)
		if not ok then geterrorhandler()(err) end
	end
end

---------------------------------------------------------------------------
-- Events
---------------------------------------------------------------------------
local frame = CreateFrame("Frame")
RM.frame = frame
local handlers = {}

function RM.On(event, fn)
	if not handlers[event] then
		-- Events, die es in diesem Client nicht gibt, still überspringen
		if not pcall(frame.RegisterEvent, frame, event) then return false end
		handlers[event] = {}
	end
	table.insert(handlers[event], fn)
end

frame:SetScript("OnEvent", function(_, event, ...)
	local list = handlers[event]
	if not list then return end
	for _, fn in ipairs(list) do
		local ok, err = pcall(fn, ...)
		if not ok then geterrorhandler()(err) end
	end
end)

RM.On("ADDON_LOADED", function(name)
	if name ~= ADDON then return end
	RaidMasterDB = RaidMasterDB or {}
	local db = RaidMasterDB
	db.data = db.data or {}
	FillDefaults(db.data, { version = 0, players = {}, log = {}, firstKills = {}, lastDecay = 0, settings = {} })
	FillDefaults(db.data.settings, RM.DEFAULT_SETTINGS)
	db.config = db.config or {}
	FillDefaults(db.config, RM.DEFAULT_CONFIG)
	db.session = db.session or { active = false, kills = {} }
	db.trade = db.trade or {}
	db.foreign = db.foreign or {}
	-- Umstellung auf DKP-Töpfe (bisherige DKP gehören zu Molten Core)
	RM.DKP.Migrate(db.data)
	for _, f in pairs(db.foreign) do RM.DKP.Migrate(f) end
	db.pendingAwards = db.pendingAwards or {}
	db.specs = db.specs or {}
	RM.db = db
	if RegisterPrefix then RegisterPrefix(RM.PREFIX) end
	RM.Fire("DB_READY")
end)

function RM.GameInfoText()
	return string.format("%s (WoW %s, Build %s, Interface %d)", RM.GAME.name, RM.GAME_VERSION, RM.GAME_BUILD, RM.TOC)
end

RM.On("PLAYER_LOGIN", function()
	RM.RequestGuildRoster()
	RM.Fire("LOGIN")
	RM.db.game = { key = RM.GAME.key, toc = RM.TOC, version = RM.GAME_VERSION, locale = RM.GAME_LOCALE }
	RM.Print("v" .. RM.VERSION .. L[" geladen – "] .. RM.GameInfoText() .. " · " .. (RM.LANGUAGES[RM.LOCALE] or RM.LOCALE) .. L[". /rm öffnet das Fenster."])
	if RM.GAME.key == "unknown" then
		RM.Print(L["|cffffcc00Diese Spielversion kennt RaidMaster noch nicht. Bitte im Discord unter #addon-hilfe melden.|r"])
	elseif RM.TOC > RM.GAME.tested then
		RM.Print(L["|cffffcc00Neuere Spielversion als getestet – falls etwas nicht klappt, bitte im Discord unter #addon-hilfe melden.|r"])
	end
	if not RM.Caps.masterLoot then
		RM.Print(L["Diese Spielversion hat keinen Plündermeister: Ersteigerte Items werden per Handel übergeben."])
	end
end)

RM.On("GUILD_ROSTER_UPDATE", RebuildGuild)
RM.On("PLAYER_GUILD_UPDATE", function() RM.RequestGuildRoster() end)

---------------------------------------------------------------------------
-- Tastenbelegungen (Texte)
---------------------------------------------------------------------------
BINDING_HEADER_RAIDMASTER = "RaidMaster"
BINDING_NAME_RAIDMASTER_TOGGLE = L["Fenster öffnen/schließen"]
BINDING_NAME_RAIDMASTER_SMARTMARK = L["Nächstes freies Symbol (Maus/Ziel)"]
BINDING_NAME_RAIDMASTER_MARK8 = L["Totenkopf (Maus/Ziel)"]
BINDING_NAME_RAIDMASTER_MARK7 = L["Kreuz (Maus/Ziel)"]
BINDING_NAME_RAIDMASTER_MARK6 = L["Viereck (Maus/Ziel)"]
BINDING_NAME_RAIDMASTER_MARK5 = L["Mond (Maus/Ziel)"]
BINDING_NAME_RAIDMASTER_MARK4 = L["Dreieck (Maus/Ziel)"]
BINDING_NAME_RAIDMASTER_MARK3 = L["Diamant (Maus/Ziel)"]
BINDING_NAME_RAIDMASTER_MARK2 = L["Kreis (Maus/Ziel)"]
BINDING_NAME_RAIDMASTER_MARK1 = L["Stern (Maus/Ziel)"]
BINDING_NAME_RAIDMASTER_CLEARMARK = L["Symbol entfernen (Maus/Ziel)"]
BINDING_NAME_RAIDMASTER_CLEARALL = L["Alle Symbole entfernen"]

---------------------------------------------------------------------------
-- Slash-Befehle (Bedienung erfolgt sonst per Maus)
---------------------------------------------------------------------------
SLASH_RAIDMASTER1 = "/rm"
SLASH_RAIDMASTER2 = "/raidmaster"
SlashCmdList["RAIDMASTER"] = function(msg)
	msg = (msg or ""):lower()
	if msg == "bar" then
		RM.Markers.ToggleBar()
	elseif msg == "reset" then
		RM.db.config.positions = {}
		ReloadUI()
	elseif msg == "sync" then
		RM.Comm.RequestSync()
	elseif msg == "minimap" then
		RM.UI.ToggleMinimapButton()
	elseif msg == "version" or msg == "info" then
		RM.Print("v" .. RM.VERSION .. " – " .. RM.GameInfoText() .. " · " .. (RM.LANGUAGES[RM.LOCALE] or RM.LOCALE) .. " (" .. RM.GAME_LOCALE .. ")")
	else
		RM.UI.Toggle()
	end
end
