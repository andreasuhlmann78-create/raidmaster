-- RaidMaster - Core
-- Namensraum, Events, gespeicherte Daten, Rechte und Hilfsfunktionen

local ADDON, RM = ...
local L = RM.L
RaidMaster = RM

RM.VERSION = "3.0.25"
RM.VERSION_NUM = 30025
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

-- Gemeinsame Versionserkennung aller GoldSentinel-Addons (GoldSentinelGame.lua, lädt direkt vor dieser Datei).
-- Die Datei nie hier ändern – nur zentral mit höherer VERSION. Fehlt sie, gilt die eigene Erkennung wie bisher.
RM.G = _G.GoldSentinelGame

function RM.DetectGame()
	-- über GoldSentinelGame (gleiche Schlüssel: era, forever, tbc, wrath, titan, cata, mists, retail)
	if RM.G and RM.G.flavor then
		for _, g in ipairs(RM.GAMES) do if g.key == RM.G.flavor then return g end end
	end
	for _, g in ipairs(RM.GAMES) do
		if RM.TOC >= g.from and RM.TOC <= g.to then return g end
	end
	return { key = "unknown", name = L["Unbekannte Version"], from = 0, to = 0, tested = 0 }
end
-- Flaggen der Spielversion. RM.IsClassicEra gilt NUR für echtes Classic Era (Inhalte wie Raids, Klassen, Stufe 60
-- teilen sich Era und Forever über RM.GAME.key/Data.lua). Für die Wahl der API zählt RM.IsModern:
-- WoW Forever und Retail = moderner Client (secret values im Kampf, Kampflog für Addons zu).
function RM.SetGameFlags()
	RM.GAME = RM.DetectGame()
	RM.IsRetail = RM.GAME.key == "retail"
	RM.IsForever = RM.GAME.key == "forever"
	RM.IsClassicEra = RM.GAME.key == "era"
	if RM.G then
		RM.IsModern = RM.G.IsModern and true or false
	else
		RM.IsModern = RM.IsForever or RM.IsRetail or (issecretvalue ~= nil)
	end
end
RM.SetGameFlags()

-- Was kann dieser Client? (wird im ganzen Addon abgefragt statt Versionsnummern zu vergleichen)
RM.Caps = {
	masterLoot = (GiveMasterLoot ~= nil and GetMasterLootCandidate ~= nil) and not RM.IsRetail,
	specs = (GetSpecialization ~= nil and RM.TOC >= 50000),
	talentTrees = (GetTalentTabInfo ~= nil and RM.TOC < 50000),
	-- Combat Log: in WoW Forever und ab Midnight (12.x) für Addons geschlossen
	combatLog = (CombatLogGetCurrentEventInfo ~= nil) and not RM.IsModern and RM.TOC < 120000,
}

-- "Secret values" (moderner Client, im Kampf): anzeigen geht, auswerten nicht
function RM.IsSecret(v)
	if RM.G then return RM.G.IsSecret(v) end
	return issecretvalue ~= nil and v ~= nil and issecretvalue(v) == true
end

-- v, oder nil, wenn v ein secret value ist
function RM.Safe(v)
	if RM.IsSecret(v) then return nil end
	return v
end

-- Serverzeit für RaidMaster. Das Test-Werkzeug verschiebt nur RM.timeOffset (mehrere Raidabende im Abstand
-- von einer Woche); GetServerTime selbst wird nie ersetzt (sonst "Taint" für Blizzard und andere Addons).
RM.timeOffset = 0
function RM.Now()
	return GetServerTime() + (RM.timeOffset or 0)
end

---------------------------------------------------------------------------
-- Nahtstellen (testroutine-raidmaster.txt, Abschnitt 2.4). Der Weg im Spiel bleibt genau wie vorher; nur die Aufrufe
-- laufen über eigene Tabellen, damit die Testroutine sie fälschen bzw. mitschreiben kann, ohne je eine
-- Blizzard-Funktion zu ersetzen (das gäbe "Taint" bis zum /reload, auch für andere Addons).
---------------------------------------------------------------------------
-- RM.API: Lesezugriffe auf die Spiel-API. RM.API.Get("UnitAura") liefert
--   RM.API.over[name] (Attrappe der Testroutine), nil wenn RM.API.hide[name] (alte Funktion "fehlt"), sonst _G[name].
-- Auch mit Punkt: RM.API.Get("C_UnitAuras.GetAuraDataByIndex") (over/hide für den ganzen Pfad oder die Tabelle).
-- over und hide bleiben im Spiel immer leer; nur die Testroutine füllt sie (und leert sie wieder).
RM.API = { over = {}, hide = {} }
function RM.API.Get(name)
	local API = RM.API
	if next(API.over) or next(API.hide) then
		local o = API.over[name]
		if o ~= nil then return o end
		if API.hide[name] then return nil end
		local tbl, key = name:match("^([^%.]+)%.(.+)$")
		if tbl then
			if API.hide[tbl] then return nil end
			local t = API.over[tbl]
			if t == nil then t = _G[tbl] end
			return type(t) == "table" and t[key] or nil
		end
		return _G[name]
	end
	local tbl, key = name:match("^([^%.]+)%.(.+)$")
	if tbl then
		local t = _G[tbl]
		return type(t) == "table" and t[key] or nil
	end
	return _G[name]
end

-- RM.Act: die EINZIGE Stelle für Aktionen mit Folgen (Chat, Symbole, Einladen, Gruppen, Plündern, Handel,
-- Bereitschafts-Check, Countdown, Screenshot, /reload, Berufe öffnen, Betrachten, Addons abschalten).
-- Jede Funktion ruft die Blizzard-Funktion erst beim Aufruf auf (alter Weg). Die Testroutine ersetzt die Felder von
-- RM.Act durch Zähler (Spion) – nie die Blizzard-Funktionen selbst.
RM.Act = {}
local Act = RM.Act
function Act.SendChat(msg, chatType, language, target) return SendChatMessage(msg, chatType, language, target) end
function Act.SetRaidTarget(unit, icon) return SetRaidTarget(unit, icon) end
function Act.InviteUnit(name)
	local fn = (C_PartyInfo and C_PartyInfo.InviteUnit) or InviteUnit
	if fn then return fn(name) end
end
function Act.ConvertToRaid()
	local fn = (C_PartyInfo and C_PartyInfo.ConvertToRaid) or ConvertToRaid
	if fn then return fn() end
end
function Act.SetRaidSubgroup(index, group) return SetRaidSubgroup(index, group) end
function Act.SwapRaidSubgroup(a, b) return SwapRaidSubgroup(a, b) end
function Act.GiveMasterLoot(slot, index) return GiveMasterLoot(slot, index) end
function Act.ClickTradeButton(slot) return ClickTradeButton(slot) end
function Act.InitiateTrade(unit) return InitiateTrade(unit) end
function Act.PickupContainerItem(bag, slot) return RM.Container.Pickup(bag, slot) end
function Act.DoReadyCheck() return DoReadyCheck() end
function Act.DoCountdown(seconds) return C_PartyInfo.DoCountdown(seconds) end
function Act.Screenshot() return Screenshot() end
function Act.ReloadUI() return ReloadUI() end
function Act.CastSpellByName(name) return CastSpellByName(name) end
function Act.OpenTradeSkill(line) return C_TradeSkillUI.OpenTradeSkill(line) end
function Act.NotifyInspect(unit) return NotifyInspect(unit) end
function Act.DisableAddOn(name)
	local fn = (C_AddOns and C_AddOns.DisableAddOn) or DisableAddOn
	if fn then return fn(name) end
end
-- Liste der Aktionen (für den Spion der Testroutine)
RM.ACT_NAMES = { "SendChat", "SetRaidTarget", "InviteUnit", "ConvertToRaid", "SetRaidSubgroup", "SwapRaidSubgroup",
	"GiveMasterLoot", "ClickTradeButton", "InitiateTrade", "PickupContainerItem", "DoReadyCheck", "DoCountdown",
	"Screenshot", "ReloadUI", "CastSpellByName", "OpenTradeSkill", "NotifyInspect", "DisableAddOn" }

-- Im Kampf? RM.simCombat ist der simulierte Kampf der Testroutine, RM.Markers.simCombat der Knopf "Adds markieren im
-- Kampf" des Test-Werkzeugs (beide nur im Test gesetzt), sonst die Kampfsperre des Spiels.
RM.simCombat = false
function RM.InCombat()
	if RM.simCombat or (RM.Markers and RM.Markers.simCombat) then return true end
	if RM.G and RM.G.InCombat then return RM.G.InCombat() end
	return (InCombatLockdown and InCombatLockdown()) and true or false
end

-- Selbst abgefangenen Fehler an die Prüfung melden (GoldSentinelTest.lua, gemeinsame Datei): nur Ort und Lua-Meldung,
-- nie Namen. Fehler, die schon an geterrorhandler gehen, hier NICHT melden (sonst doppelt gezählt).
function RM.ReportError(where, err)
	local GT = _G.GoldSentinelTest
	if GT and GT.Error then pcall(GT.Error, "RaidMaster", where, err) end
end

---------------------------------------------------------------------------
-- Kompatibilität (Classic-Client, verschiedene API-Stände)
---------------------------------------------------------------------------
RM.GetItemInfo = (C_Item and C_Item.GetItemInfo) or GetItemInfo
RM.GetItemInfoInstant = (C_Item and C_Item.GetItemInfoInstant) or GetItemInfoInstant
-- Alte API (Classic Era, TBC …): zuerst die alte Funktion wie vor 3.0.7 – auch wenn C_Item dort schon existiert
RM.GetItemCount = (not RM.IsModern and GetItemCount) or (C_Item and C_Item.GetItemCount) or GetItemCount

-- Name eines Zaubers (moderner Client: C_Spell.GetSpellName, alt: GetSpellInfo)
-- (Zugriffe über RM.API.Get, damit die Testroutine fehlende alte bzw. moderne Funktionen nachstellen kann)
function RM.GetSpellName(id)
	local API = RM.API.Get
	local GetSpellInfo = API("GetSpellInfo")
	if not RM.IsModern and GetSpellInfo then          -- alte API: Weg wie vor 3.0.7
		local ok, n = pcall(GetSpellInfo, id)
		if ok and n then return n end
	end
	local GetSpellName = API("C_Spell.GetSpellName")
	if GetSpellName then
		local ok, n = pcall(GetSpellName, id)
		if ok and n then return n end
	end
	if GetSpellInfo then
		local ok, n = pcall(GetSpellInfo, id)
		if ok then return n end
	end
end

-- Hilfreicher Buff Nr. i einer Einheit: name, spellId (nil = keiner mehr).
-- Moderner Client: C_UnitAuras. Alte API (Classic Era 1.15, TBC Anniversary …): zuerst UnitAura wie vor 3.0.7,
-- auch wenn C_UnitAuras dort schon existiert. RM.CanReadAuras() sagt, ob dieser Client Buffs überhaupt liefert.
function RM.GetBuff(unit, i)
	local API = RM.API.Get
	local UnitAura = API("UnitAura")
	if not RM.IsModern and UnitAura then
		local name, _, _, _, _, _, _, _, _, spellId = UnitAura(unit, i, "HELPFUL")
		return name, spellId
	end
	local byIndex, buffByIndex = API("C_UnitAuras.GetAuraDataByIndex"), API("C_UnitAuras.GetBuffDataByIndex")
	if byIndex then
		local ok, a = pcall(byIndex, unit, i, "HELPFUL")
		if not ok or not a then return nil end
		return a.name, a.spellId
	elseif buffByIndex then
		local ok, a = pcall(buffByIndex, unit, i)
		if not ok or not a then return nil end
		return a.name, a.spellId
	elseif UnitAura then
		local name, _, _, _, _, _, _, _, _, spellId = UnitAura(unit, i, "HELPFUL")
		return name, spellId
	else
		local UnitBuff = API("UnitBuff")
		if UnitBuff then
			local name, _, _, _, _, _, _, _, _, spellId = UnitBuff(unit, i)
			return name, spellId
		end
	end
end

function RM.CanReadAuras()
	local API = RM.API.Get
	return (API("C_UnitAuras.GetAuraDataByIndex") ~= nil or API("C_UnitAuras.GetBuffDataByIndex") ~= nil)
		or API("UnitAura") ~= nil or API("UnitBuff") ~= nil
end
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
	local old, modern = RM.API.Get("GetLootMethod"), RM.API.Get("C_PartyInfo.GetLootMethod")
	if old then
		return old()
	elseif modern then
		local m, partyIndex, raidIndex = modern()
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
	standbyGetsDKP = true,     -- Ersatzbank bekommt beim Raidstart einmalig DKP ...
	standbyStartDKP = 10,      -- ... so viele (danach nichts mehr: keine Boss- oder Endpunkte)
	autoDecay = true,          -- 2.8.0: Verfall automatisch einmal pro Woche zum Raid-Reset (Mittwoch)
	mainBeforeTwink = true,    -- 2.8.0: Twinks gewinnen nur, wenn kein Main bietet
}

-- Zahl-Einstellung der Gilde: fehlt sie oder ist sie keine Zahl (z. B. Daten einer älteren Version per Sync), gilt der
-- Standardwert (ab 3.0.24, TU3). Der Verfall (decayPct) nutzt das bewusst NICHT: fehlt er, bleibt er 0 %.
function RM.SettingNum(key)
	local s = RM.db and RM.db.data and RM.db.data.settings or {}
	local v = tonumber(s[key])
	if v == nil then v = tonumber(RM.DEFAULT_SETTINGS[key]) end
	return v
end

-- Lokale Einstellungen (nur dieser Spieler)
RM.DEFAULT_CONFIG = {
	lootMaster = "",
	lootThreshold = 2,        -- 2 = Selten (grün), 3 = Rar (blau), 4 = Episch
	autoLoot = false,         -- als Raidleiter vergessenen Plündermeister automatisch setzen (sonst nur Warnung)
	setLootOnStart = true,
	autoDistribute = true,
	announceLoot = true,
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
	bossBar = true,            -- Boss-Leiste für die Raidleitung, sobald ein Boss im Ziel ist
	pullSeconds = 10,          -- 2.8.0: Pull-Timer
	breakMinutes = 5,          -- 2.8.0: Pausen-Timer
	pullCountdownChat = true,  -- Countdown 5-4-3-2-1 im Raidchat
	timerAddons = "both",      -- Timer an DBM und BigWigs: both | dbm | bigwigs | none
	readyCheckGame = true,     -- Bereitschafts-Check startet auch den des Spiels
	fireResMin = 0,            -- Feuerwiderstand mindestens (0 = nicht prüfen)
	itemTooltip = true,        -- Droprate und Preisverlauf im Item-Tooltip
	welcome = true,            -- Begrüßung im Raidchat beim Raidstart
	records = true,            -- 2.9.0: Erstkill-Feier, Bestzeiten, Kill-Protokoll
	firstKillScreenshot = true, -- Screenshot beim Erstkill (der Uploader schickt ihn an Discord)
	bankScan = false,          -- dieser Charakter ist der Bank-Charakter (Bestand an Discord)
	markerLocked = false,
	standby = {},
	activePool = "mc",
	autoInvite = false,       -- 2.5.0: Einladen, Gruppen und Plündermeister macht die Raidleitung per Knopf
	autoInviteMinutes = 15,
	autoGroups = false,
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
	-- geschützter Name (secret value, moderner Client im Kampf) -> nil, nie damit rechnen
	if RM.G and RM.G.Short then return RM.G.Short(name) end
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

-- Test- und Entwicklerfunktionen (Test-Werkzeug, Testmodus) nur für den Entwickler GoldSentinel (GoldSentinelDev.lua)
function RM.IsDev()
	return (GoldSentinelDev and GoldSentinelDev.IsDev and GoldSentinelDev:IsDev()) and true or false
end

function RM.RequireDev()
	if GoldSentinelDev and GoldSentinelDev.Require then return GoldSentinelDev:Require("RaidMaster") end
	return false
end

function RM.IsAssist()
	return UnitIsGroupLeader("player") or UnitIsGroupAssistant("player")
end

-- Liste der Raidmitglieder: { {name=, class=, online=, rank=} }
function RM.RaidMembers()
	local list = {}
	if not RM.InRaid() then return list end
	for i = 1, GetNumGroupMembers() do
		local name, rank, subgroup, _, _, class, _, online = GetRaidRosterInfo(i)
		if name then
			list[#list + 1] = { name = RM.Short(name), class = class, online = online and true or false, rank = rank, index = i, group = subgroup or 1 }
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

-- Text in den Raidchat (eigene Funktion, damit das Test-Tool sie umleiten kann)
function RM.RaidChat(msg, channel)
	RM.Act.SendChat(msg, channel or "RAID")
end

-- Flüstern (eigene Funktion, damit das Test-Tool sie umleiten kann)
function RM.Whisper(msg, target)
	RM.Act.SendChat(msg, "WHISPER", nil, target)
end

-- Zeilen IMMER als Schlachtzugwarnung, nie in den normalen Chat.
-- Ohne Leiter-/Assistentenrechte (oder außerhalb eines Raids) erscheinen sie nur bei dir.
function RM.RaidWarning(lines)
	if type(lines) == "string" then lines = { lines } end
	local can = RM.InRaid() and RM.IsAssist()
	if not can then
		RM.Print(L["Schlachtzugwarnungen können nur Raidleiter und Co-Raidleiter im Raid senden – nur bei dir angezeigt:"])
	end
	for i, l in ipairs(lines) do
		if can then
			C_Timer.After((i - 1) * 0.3, function() RM.RaidChat(l, "RAID_WARNING") end)
		else
			RM.Print("|cffff4800" .. l .. "|r")
		end
	end
end

-- Ein Spiel-Ereignis an alle RaidMaster-Handler geben (für das Test-Tool RaidMasterTest)
function RM.SimulateEvent(event, ...)
	local fn = RM.frame and RM.frame:GetScript("OnEvent")
	if fn then fn(RM.frame, event, ...) end
end

-- Nachricht an den Raid (Raidwarnung wenn möglich)
function RM.Announce(msg, warning)
	if RM.InRaid() then
		if warning and RM.IsAssist() then
			RM.Act.SendChat(msg, "RAID_WARNING")
		else
			RM.Act.SendChat(msg, "RAID")
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

-- Rechte:
--   im Raid / in der Gruppe: volle Rechte hat nur der Raidleiter (Gruppenleiter) – keine Offiziere
--   der Plündermeister darf versteigern und Items buchen (RM.CanLoot), Assistenten markieren usw.
--   ohne Gruppe: du bist dein eigener Raidleiter (volle Rechte auf deinem Client)
local function Grouped()
	return RM.InRaid() or (IsInGroup and IsInGroup()) and true or false
end

function RM.IsOfficer(name)
	name = RM.Short(name)
	-- der Raidleiter des aktuellen Raids hat alle Rechte (wenn er in der eigenen Gilde ist)
	if RM.IsMainLeader(name) and (name == RM.Me() or RM.guild.rank[name] ~= nil) then return true end
	-- im Raid/in der Gruppe hast DU nur als Raidleiter volle Rechte (Gildenrang zählt dann nicht);
	-- Daten anderer Offiziere (Abgleich in der Gilde) werden weiterhin angenommen
	if name == RM.Me() and Grouped() then return false end
	local rank = RM.GuildRank(name)
	if rank == nil then return false end
	local limit = (RM.db and RM.db.data.settings.officerRank) or 1
	return rank <= limit
end

-- Gildenrang (0 = Gildenmeister) – auch wenn die Gildenliste den Namen anders schreibt
-- (WoW Forever: Vor- und Nachname)
function RM.GuildRank(name)
	name = RM.Short(name)
	local rank = RM.guild.rank[name]
	if rank == nil then
		for n, r in pairs(RM.guild.rank) do
			if RM.SameName(n, name) then rank = r break end
		end
	end
	if rank == nil and RM.SameName(name, RM.Me()) then
		local _, _, rankIndex = GetGuildInfo("player")
		rank = rankIndex
	end
	return rank
end

-- Warum habe ich (keine) Rechte? Für die Diagnose
function RM.RightsInfo()
	local me = RM.Me()
	local rank = RM.GuildRank(me)
	local rankName = select(2, GetGuildInfo("player"))
	local limit = (RM.db and RM.db.data.settings.officerRank) or 1
	return {
		me = me, inGuild = IsInGuild() and true or false, rank = rank, rankName = rankName, limit = limit,
		byRank = rank ~= nil and rank <= limit, leader = RM.MainLeader(), isLeader = RM.IsMainLeader(),
		looter = RM.IAmMasterLooter(), assist = RM.IsAssist(), grouped = Grouped(),
	}
end

-- Leiter ist immer der Raidleiter des aktuellen Raids (bzw. Gruppenleiter)
function RM.MainLeader()
	if not (IsInGroup and IsInGroup()) and not RM.InRaid() then return nil end
	if UnitIsGroupLeader("player") then return RM.Me() end
	if RM.InRaid() then
		for i = 1, GetNumGroupMembers() do
			local name, rank = GetRaidRosterInfo(i)
			if name and rank == 2 then return RM.Short(name) end
		end
	else
		for i = 1, 4 do
			local u = "party" .. i
			if UnitExists(u) and UnitIsGroupLeader(u) then return RM.Short(UnitName(u)) end
		end
	end
end

-- Namen vergleichen. Nur im Client WoW Forever haben Charaktere Vor- und Nachnamen
-- ("Testa Beispiel"); dort passt der Name auch, wenn eine Seite nur den Vornamen kennt.
-- In allen anderen Versionen gilt nur der exakte Name.
function RM.SameName(a, b)
	if RM.G then return RM.G.SameName(a, b) end
	-- ohne GoldSentinelGame: bisherige Prüfung
	if not a or not b then return false end
	a = a:lower():gsub("^%s+", ""):gsub("%s+$", "")
	b = b:lower():gsub("^%s+", ""):gsub("%s+$", "")
	if a == b then return true end
	if RM.GAME.key ~= "forever" then return false end
	local fa, fb = a:match("^(%S+)"), b:match("^(%S+)")
	if (not a:find(" ") or not b:find(" ")) and fa == fb then return true end
	return false
end

function RM.IsMainLeader(name)
	local m = RM.MainLeader()
	if not m then return false end
	name = RM.Short(name or RM.Me())
	return RM.SameName(name, m)
end

-- Darf dieser Spieler DKP verändern? (Offiziere und der Raidleiter des aktuellen Raids)
function RM.CanEdit()
	-- ohne Gruppe bist du dein eigener Raidleiter (eigener Client; andere übernehmen deine Daten
	-- trotzdem nur, wenn du Raidleiter ihres Raids bist oder einen Offiziersrang hast)
	if not Grouped() then return true end
	return RM.IsOfficer(RM.Me()) or RM.IsMainLeader()
end

-- Plündermeister (auch wenn er nicht Raidleiter ist): Versteigerungen durchführen und Items buchen
function RM.CanLoot()
	if RM.CanEdit() then return true end
	return RM.InRaid() and RM.IAmMasterLooter() and true or false
end

-- Ist name der Plündermeister unseres Raids? (für Item-Buchungen von ihm)
function RM.IsRaidLooter(name)
	local ml = RM.MasterLooterName()
	return ml and name and RM.InRaid() and RM.SameName(RM.Short(name), RM.Short(ml)) or false
end

-- Einheit (raidN/partyN) eines Gruppenmitglieds
function RM.GroupUnit(name)
	name = RM.Short(name)
	if not name then return nil end
	if RM.InRaid() then
		for i = 1, 40 do
			local u = "raid" .. i
			if UnitExists(u) and RM.SameName(RM.Short(UnitName(u)), name) then return u end
		end
	else
		for i = 1, 4 do
			local u = "party" .. i
			if UnitExists(u) and RM.SameName(RM.Short(UnitName(u)), name) then return u end
		end
	end
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

-- Handler eines Ereignisses (für die Testroutine: einzeln mit pcall aufrufen)
function RM.HandlersFor(event)
	return handlers[event]
end

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

-- Gespeicherte Daten einrichten und ältere Fassungen umstellen (Rumpf von ADDON_LOADED, ausgelagert für die
-- Testroutine T80–T82: sie ruft RM.InitDB mit einer Kopie auf, RM.db bleibt dabei die echte Tabelle).
-- Falsche Typen (beschädigte Datei) werden durch leere Tabellen ersetzt statt mit einem Lua-Fehler abzubrechen.
function RM.InitDB(db)
	-- beschädigte Einträge (falscher Typ) nicht übernehmen; bei gültigen Daten ändert sich hier nichts
	for _, k in ipairs({ "data", "config", "session", "trade", "foreign", "pendingAwards", "specs", "signup", "lootdb", "prof",
		"records", "killlog", "shots", "bank", "itemTips", "recipeMats", "assign", "myAssign", "pug", "syncProbe" }) do
		if db[k] ~= nil and type(db[k]) ~= "table" then db[k] = nil end
	end
	db.data = db.data or {}
	for _, k in ipairs({ "players", "log", "firstKills", "settings" }) do
		if db.data[k] ~= nil and type(db.data[k]) ~= "table" then db.data[k] = nil end
	end
	FillDefaults(db.data, { version = 0, players = {}, log = {}, firstKills = {}, lastDecay = 0, settings = {} })
	FillDefaults(db.data.settings, RM.DEFAULT_SETTINGS)
	db.config = db.config or {}
	for _, k in ipairs({ "standby", "positions", "rules", "minimap", "instanceMap" }) do
		if db.config[k] ~= nil and type(db.config[k]) ~= "table" then db.config[k] = nil end
	end
	FillDefaults(db.config, RM.DEFAULT_CONFIG)
	-- 1.8.8: kein fester Raidleiter mehr – Leiter ist der Raidleiter des Raids
	db.data.settings.raidLeader = nil
	db.config.autoPromote = nil
	-- 1.8.5: Plündermeister schon ab grünen Items (alte Standardeinstellung "blau" umstellen)
	if not db.config.threshold2 then
		if db.config.lootThreshold == 3 then db.config.lootThreshold = 2 end
		db.config.threshold2 = true
	end
	-- 2.5.0: Automatiken aus – die Raidleitung lädt ein, teilt Gruppen ein und setzt den Plündermeister per Knopf
	if not db.config.manual250 then
		db.config.autoInvite = false
		db.config.autoGroups = false
		db.config.autoLoot = false
		db.config.manual250 = true
	end
	db.session = db.session or { active = false, kills = {} }
	db.trade = db.trade or {}
	db.foreign = db.foreign or {}
	-- Umstellung auf DKP-Töpfe (bisherige DKP gehören zu Molten Core)
	RM.DKP.Migrate(db.data)
	for _, f in pairs(db.foreign) do if type(f) == "table" then RM.DKP.Migrate(f) end end
	db.pendingAwards = db.pendingAwards or {}
	db.specs = db.specs or {}
	return db
end

-- 3.0.25 (MN1/MN2): gemeinsames Marktdaten-Netz GoldSentinelMarkt.lua (unverändert aus shared/). RaidMaster meldet
-- sich nur an und reicht den Schalter "Marktdaten teilen" durch (Standard an, RaidMasterDB.config.marktTeilen).
-- Fehlt die Datei oder die Auktionshaus-Schnittstelle (alte Clients), passiert nichts.
function RM.AttachMarkt()
	local GM = _G.GoldSentinelMarkt
	if type(GM) ~= "table" or type(GM.Attach) ~= "function" or type(RaidMasterDB) ~= "table" then return false end
	pcall(GM.Attach, "RaidMaster", RaidMasterDB)
	RM.SetMarktShare(not (RM.db and RM.db.config and RM.db.config.marktTeilen == false))
	return true
end

function RM.SetMarktShare(on)
	if RM.db and RM.db.config then RM.db.config.marktTeilen = on and true or false end
	local GM = _G.GoldSentinelMarkt
	if type(GM) == "table" and type(GM.SetShare) == "function" then pcall(GM.SetShare, "RaidMaster", on and true or false) end
end

-- MN3: eine Zeile für den Testbericht (Version, an/aus, mitgelesene Scans, gesendet/empfangen, Speicher), ohne Namen
function RM.MarktLine()
	local GM = _G.GoldSentinelMarkt
	if type(GM) ~= "table" or type(GM.Stats) ~= "function" then return "MARKT-NETZ: nicht geladen" end
	local s = GM.Stats() or {}
	local bytes = 0
	local function size(v, depth)
		if depth > 6 then return end
		if type(v) == "string" then bytes = bytes + #v
		elseif type(v) == "number" then bytes = bytes + 8
		elseif type(v) == "table" then for k, x in pairs(v) do size(k, depth + 1); size(x, depth + 1) end end
	end
	size(RaidMasterDB and RaidMasterDB.gsMarkt, 0)
	return string.format("MARKT-NETZ: v%s · %s · mitgelesene Scans %d · gesendet %d / empfangen %d · Speicher %.0f KB",
		tostring(GM.VERSION), (GM.IsShareOn and GM.IsShareOn()) and "an" or "aus", tonumber(s.scans) or 0,
		tonumber(s.sent) or 0, tonumber(s.received) or 0, bytes / 1024)
end

-- 3.0.23: Beleg für den Abgleich PC/Laptop (RaidMaster-Uploader 2.2.0, S8 c). Übernimmt der Uploader einen neueren
-- Stand im Anmelde-/Charakterbildschirm, hängt er einen Prüfblock RaidMasterSyncProbe = { seq, von, t } an
-- RaidMaster.lua. Hier wird beim Laden nur festgehalten, welcher Prüfblock gelesen wurde und wann (Unix-Zeit);
-- nach dem nächsten Speichern sieht der Uploader daran, dass WoW den übernommenen Stand wirklich gelesen hat.
-- Der Prüfblock selbst wird danach verworfen. Keine Namen, nichts wird gesendet.
function RM.ReadSyncProbe(db, probe)
	if type(probe) ~= "table" then return nil end
	local seq = tonumber(probe.seq)
	if not seq then return nil end
	local von = type(probe.von) == "string" and probe.von:sub(1, 40) or ""
	db.syncProbe = { seq = seq, von = von, t = tonumber(probe.t) or 0, geladen = time() }
	return db.syncProbe
end

RM.On("ADDON_LOADED", function(name)
	if name ~= ADDON then return end
	RaidMasterDB = RaidMasterDB or {}
	local db = RM.InitDB(RaidMasterDB)
	RM.db = db
	RM.ReadSyncProbe(db, RaidMasterSyncProbe)
	RaidMasterSyncProbe = nil
	RM.AttachMarkt()
	-- Testberichte und Lua-Fehler für die Prüfung sammeln (RaidMasterDB.gsTest; der Uploader schickt sie an Discord)
	if GoldSentinelTest then GoldSentinelTest.TrackErrors("RaidMaster", RM.VERSION, db) end
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
BINDING_NAME_RAIDMASTER_MARKADDS = L["Adds markieren (alle sichtbaren, nach Vorlage)"]
BINDING_NAME_RAIDMASTER_CLEARALL = L["Alle Symbole entfernen"]

---------------------------------------------------------------------------
-- Slash-Befehle: ab 3.0.24 in Commands.lua (eine Tabelle RM.COMMANDS für den Handler UND die Befehlsliste, Auftrag BL)
---------------------------------------------------------------------------
