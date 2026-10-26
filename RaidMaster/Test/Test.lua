-- ============================================================================
-- RaidMaster Test – Werkzeug, um RaidMaster im Spiel auszuprobieren (fest in RaidMaster eingebaut)
--
-- Testmodus: alles, was du hier machst, bleibt bei dir:
--   * Raid-, DKP- und Lootdaten werden beim Start gesichert und beim Beenden
--     (oder beim nächsten Einloggen) wiederhergestellt
--   * keine Addon-Nachrichten an Gilde/Raid, Raidchat-Texte erscheinen nur bei dir
--   * ein Testraid mit 40 Spielern (MC-Aufstellung) wird vorgespielt
-- Öffnen: Knopf "Test" oben im RaidMaster-Fenster, /rmtest oder /rm test
-- ============================================================================

local ADDON, NS = ...
local RM = (type(NS) == "table" and NS.UI and NS) or RaidMaster
if not RM or not RM.UI then return end
local UI = RM.UI
local COLORS = UI.COLORS
local T = { active = false, role = "raidlead", log = {}, integrated = true }
RaidMasterTest = T
RM.Test = T

-- Testraid: 39 Testspieler + du = 40, aufgestellt wie für Molten Core üblich:
-- 4 Tanks, 6 Furor-Krieger, 6 Priester (5 Heilig, 1 Schatten), 5 Paladine (Allianz) bzw. Schamanen (Horde),
-- 3 Druiden (2 Wiederherstellung, 1 Wildheit), 4 Schurken, 5 Frostmagier (Entfluchen bei Lucifron, Feuer ist
-- in MC nutzlos), 3 Hexenmeister (Verbannen bei Garr), 3 Jäger (Einlullender Schuss bei Magmadar).
-- Talentpunkte je Baum (Classic-Reihenfolge), damit Einteilung und Skillungen echte Rollen sehen.
local FAKE = {}
-- Ersatzbank: nicht im Raid, bekommen aber (je nach Einstellung) die Raid-DKP mit
local BENCH = {
	{ "Testersatz1", "WARRIOR", { 5, 5, 41 } }, { "Testersatz2", "PRIEST", { 21, 30, 0 } },
	{ "Testersatz3", "MAGE", { 21, 0, 30 } }, { "Testersatz4", "ROGUE", { 19, 32, 0 } },
	{ "Testersatz5", "DRUID", { 11, 0, 40 } },
}
local function BuildFake()
	wipe(FAKE)
	local horde = (UnitFactionGroup and UnitFactionGroup("player")) == "Horde"
	local function add(name, class, points) FAKE[#FAKE + 1] = { name, class, points } end
	for i = 1, 4 do add("Testtank" .. i, "WARRIOR", { 5, 5, 41 }) end
	for i = 1, 6 do add("Testkrieger" .. i, "WARRIOR", { 17, 34, 0 }) end
	for i = 1, 5 do add("Testpriester" .. i, "PRIEST", { 21, 30, 0 }) end
	add("Testschatten", "PRIEST", { 13, 0, 38 })
	if horde then
		for i = 1, 5 do add("Testschamane" .. i, "SHAMAN", { 0, 5, 46 }) end
	else
		for i = 1, 5 do add("Testpaladin" .. i, "PALADIN", { 31, 20, 0 }) end
	end
	add("Testdruide1", "DRUID", { 11, 0, 40 }); add("Testdruide2", "DRUID", { 11, 0, 40 })
	add("Testbaer", "DRUID", { 0, 31, 20 })
	for i = 1, 4 do add("Testschurke" .. i, "ROGUE", { 19, 32, 0 }) end
	for i = 1, 5 do add("Testmagier" .. i, "MAGE", { 21, 0, 30 }) end
	for i = 1, 3 do add("Testhexer" .. i, "WARLOCK", { 17, 0, 34 }) end
	add("Testjaeger", "HUNTER", { 21, 30, 0 }); add("Testjaegerin", "HUNTER", { 21, 30, 0 }); add("Testjaeger2", "HUNTER", { 0, 31, 20 })
end
BuildFake()
-- Im Raid gibt es Raidleiter, Plündermeister, Assistenten und Raidmitglieder (keine Offiziere)
local ROLE_NAMES = { member = "Raidmitglied", lead = "Assistent", looter = "Plündermeister", raidlead = "Raidleiter" }

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
-- Tempo: wie lange eine Test-Versteigerung läuft (gespeichert in RaidMasterTestOptions)
---------------------------------------------------------------------------
T.SPEEDS = { 3, 5, 8, 10, 15, 20, 30 }
function T.AuctionSec()
	local o = RaidMasterTestOptions
	local v = type(o) == "table" and tonumber(o.auctionSec)
	return v or 3
end
-- kurze Pausen zwischen den Schritten passend zum Tempo (schnell = kürzer)
local function Pause(sec)
	return sec * math.min(1, T.AuctionSec() / 20)
end
-- im Testmodus die Versteigerungsdauer von RaidMaster setzen (echte Einstellung kommt beim Beenden zurück)
-- Gebote möglichst vor den letzten 5 Sekunden, damit der Schutz gegen Last-Second-Gebote nicht verlängert
function T.BidWindow()
	local d = T.AuctionSec()
	return math.max(d * 0.5, d - 5.5)
end
function T.ApplySpeed()
	if T.active and RM.db and RM.db.data and RM.db.data.settings then
		RM.db.data.settings.auctionTime = T.AuctionSec()
		-- im Test keine Verlängerung bei späten Geboten (echte Einstellung kommt beim Beenden zurück)
		RM.db.data.settings.antiSnipe = false
	end
end

-- Haben alle Testspieler geboten, läuft die Restzeit nur noch kurz (nur im Testmodus)
T.REST_AFTER_BIDS = 1
function T.ShortenRest(c)
	local A = RM.Auction
	if not T.active or not c or A.current ~= c or c.finished then return end
	local now = GetTime()
	if c.endsAt - now <= T.REST_AFTER_BIDS then return end
	c.endsAt = now + T.REST_AFTER_BIDS
	if A.OnBid and c.aid then
		pcall(A.OnBid, RM.Me(), { a = c.aid, n = c.highName or "", v = c.high or 0, r = T.REST_AFTER_BIDS })
	end
	RM.Fire("AUCTION_CHANGED")
end
-- Ergebnis automatisch an Discord senden (Standard an)
function T.AutoSendOn()
	local o = RaidMasterTestOptions
	return not (type(o) == "table" and o.autoSend == false)
end
function T.SetAutoSend(v)
	if type(RaidMasterTestOptions) ~= "table" then RaidMasterTestOptions = {} end
	RaidMasterTestOptions.autoSend = v and true or false
end

-- "Raid starten" in RaidMaster spielt im Testmodus den ganzen Raid durch (Standard an)
function T.FollowStartOn()
	local o = RaidMasterTestOptions
	return not (type(o) == "table" and o.followStart == false)
end
function T.SetFollowStart(v)
	if type(RaidMasterTestOptions) ~= "table" then RaidMasterTestOptions = {} end
	RaidMasterTestOptions.followStart = v and true or false
end

-- Im Test vergibt RaidMaster jedes versteigerte Item sofort an den Höchstbieter (ohne "Vergeben"-Abfrage)
function T.AutoAwardOn()
	local o = RaidMasterTestOptions
	return not (type(o) == "table" and o.autoAward == false)
end
function T.SetAutoAward(v)
	if type(RaidMasterTestOptions) ~= "table" then RaidMasterTestOptions = {} end
	RaidMasterTestOptions.autoAward = v and true or false
end

function T.SetAuctionSec(v)
	if type(RaidMasterTestOptions) ~= "table" then RaidMasterTestOptions = {} end
	RaidMasterTestOptions.auctionSec = tonumber(v) or 8
	T.ApplySpeed()
	Log(string.format("Test-Versteigerungen dauern jetzt %d Sek.", T.AuctionSec()))
end

---------------------------------------------------------------------------
-- Testmodus: Daten sichern, RaidMaster-Funktionen umleiten
---------------------------------------------------------------------------
local saved = {}
-- echte RaidMaster-Funktionen beim Laden merken: "Testmodus beenden" stellt immer genau diese wieder her
-- (auch wenn ein anderes Addon, z. B. das alte RaidMasterTest, sie zwischendurch ersetzt hat)
local REAL = {}
local OVERRIDE = { "InRaid", "RaidMembers", "IsAssist", "IsLeader", "CanEdit", "SendAddonMessage", "RaidChat", "Announce", "Whisper", "IAmMasterLooter", "MasterLooterName" }

local function CaptureReal()
	if REAL.captured then return end
	for _, k in ipairs(OVERRIDE) do REAL[k] = RM[k] end
	REAL.Deliver = RM.Loot and RM.Loot.Deliver
	REAL.Ensure = RM.Loot and RM.Loot.EnsureSettings
	REAL.Warn = RM.Loot and RM.Loot.Warn
	REAL.CheckMainLeader = RM.CheckMainLeader
	REAL.RaidStart, REAL.RaidEnd = RM.Raid.Start, RM.Raid.End
	REAL.captured = true
end
CaptureReal()   -- Test.lua lädt als letzte Datei von RaidMaster, alles ist schon da

-- Testgruppe: entweder die 39 Testspieler oder – nach dem Import von Anmeldungen – nur, wer (simuliert)
-- eingeladen wurde und angenommen hat (T.roster)
T.roster = nil
local function FakeMembers()
	local list = { { name = RM.Me(), class = select(2, UnitClass("player")), online = true, rank = 2, index = 1, group = T.myGroup or 1 } }
	if T.roster then
		for i, m in ipairs(T.roster) do
			list[#list + 1] = { name = m.name, class = m.class, online = m.online ~= false, rank = 0, index = i + 1, group = m.group or 1 }
		end
		return list
	end
	for i, f in ipairs(FAKE) do list[#list + 1] = { name = f[1], class = f[2], online = true, rank = 0, index = i + 1, group = math.floor(i / 5) + 1 } end
	return list
end

-- gehört der Name zu den 39 Testspielern bzw. zur Testersatzbank? (zählen als Gildenmitglieder)
function T.IsFake(name)
	for _, f in ipairs(FAKE) do if f[1] == name then return true end end
	for _, f in ipairs(BENCH) do if f[1] == name then return true end end
	return false
end

-- Namen der Testspieler, die gerade im Testraid sind (für Testgebote)
function T.MemberNames()
	local out = {}
	if T.roster then
		for _, m in ipairs(T.roster) do if m.online ~= false then out[#out + 1] = m.name end end
	else
		for _, f in ipairs(FAKE) do out[#out + 1] = f[1] end
	end
	return out
end

function T.Start()
	if T.active then return end
	CaptureReal()
	local db = RM.db
	BuildFake()
	T.pool = T.pool or RM.DKP.ActivePool()
	db.specs = db.specs or {}
	RaidMasterTestDB = { data = Copy(db.data), session = Copy(db.session), trade = Copy(db.trade), config = Copy(db.config), specs = Copy(db.specs),
		signup = Copy(db.signup), hasSignup = db.signup ~= nil }
	for _, k in ipairs(OVERRIDE) do saved[k] = REAL[k] end
	saved.Deliver = REAL.Deliver
	saved.Ensure = REAL.Ensure
	saved.Warn = REAL.Warn
	saved.CheckMainLeader = REAL.CheckMainLeader
	-- im Testraid nichts an der echten Gruppe ändern (Plündermethode, Raidleiter)
	if RM.Loot and RM.Loot.EnsureSettings then RM.Loot.EnsureSettings = function() end end
	if RM.Loot and RM.Loot.Warn then RM.Loot.Warn = function() end end
	if RM.CheckMainLeader then RM.CheckMainLeader = function() end end
	-- Raid starten/beenden in RaidMaster steuert den Test-Durchlauf
	saved.RaidStart, saved.RaidEnd = REAL.RaidStart, REAL.RaidEnd
	RM.Raid.Start = function(...)
		-- "Raid starten" in RaidMaster hat Vorrang: alles, was das Test-Tool gerade macht, wird abgebrochen
		if T.active and not T.manualStart then T.Override("Raid starten") end
		local was = RM.db.session.active
		local r = saved.RaidStart(...)
		if T.active and not was and RM.db.session.active and not T.manualStart and not T.IsRunning() and T.FollowStartOn() and T.RosterEmpty() then
			-- leerer Testraid: nichts automatisch füllen, nur die Sitzung läuft
			Log("Raid in RaidMaster gestartet – der Testraid ist leer, darum spielt das Test-Tool nichts durch. "
				.. "Erst \"Raid füllen\" klicken oder Anmeldungen einladen, dann im Test-Fenster \"Ganzen Raid durchspielen\".")
		elseif T.active and not was and RM.db.session.active and not T.manualStart and not T.IsRunning() and T.FollowStartOn() then
			local pool = RM.db.session.pool
			if pool and RM.Data.Pools[pool] and RM.Data.Pools[pool].bosses[1] then T.pool = pool end
			Log("Raid in RaidMaster gestartet – das Test-Tool spielt jetzt " .. RM.DKP.PoolName(T.pool) .. " durch.")
			C_Timer.After(1, function() if T.active and not T.IsRunning() then T.RunRaids(T.runs) end end)
		end
		return r
	end
	RM.Raid.End = function(...)
		-- "Raid beenden" in RaidMaster hat Vorrang: Durchlauf, Versteigerung und Warteschlange des Test-Tools abbrechen
		if T.active and not T.runEnding then T.Override("Raid beenden", true) end
		local was = RM.db.session.active
		local r = saved.RaidEnd(...)
		if T.active and was and not RM.db.session.active and not T.runEnding then
			T.AutoSend("Raid beendet.")
		end
		return r
	end
	RM.InRaid = function() return true end
	RM.RaidMembers = FakeMembers
	-- Rollen: Teilnehmer (nur bieten), Co-Raidleiter (Assistent), Raidleiter (Gruppenleiter mit allen Rechten),
	-- (früher zusätzlich "Offizier" – im Raid gibt es nur Raidleiter, Assistenten und Mitglieder)
	RM.IsAssist = function() return T.role == "lead" or T.role == "raidlead" end
	RM.IsLeader = function() return T.role == "raidlead" end
	RM.CanEdit = function() return T.role == "raidlead" end
	-- im Testraid bist du als Raidleiter auch der Plündermeister (startet die Versteigerungen)
	RM.IAmMasterLooter = function() return T.role == "raidlead" or T.role == "looter" end
	RM.MasterLooterName = function() return RM.Me() end
	RM.SendAddonMessage = function() T.blocked = (T.blocked or 0) + 1 end
	-- Ansagen sehen wie im echten Raid (Raidchat-Farbe, Schlachtzugwarnung in der Bildschirmmitte), gehen aber an niemanden
	RM.RaidChat = function(msg, ch) T.ShowChat(ch or "RAID", msg) end
	RM.Whisper = function(msg, target) T.ShowChat("WHISPER_INFORM", msg, target) end
	RM.Announce = function(msg, warning) T.ShowChat(warning and "RAID_WARNING" or "RAID", msg) end
	if RM.Loot then RM.Loot.Deliver = function(link, name) Log("Item würde übergeben: " .. tostring(link) .. " -> " .. tostring(name)) end end
	-- Skillungen der Testspieler (nur im Test, werden beim Beenden zurückgesetzt)
	if RM.Spec and RM.Spec.Store then
		for _, f in ipairs(FAKE) do pcall(RM.Spec.Store, f[1], f[2], f[3], "addon") end
		for _, f in ipairs(BENCH) do pcall(RM.Spec.Store, f[1], f[2], f[3], "addon") end
	end
	-- Ersatzbank mit 5 Testspielern
	RM.db.config.standby = RM.db.config.standby or {}
	for _, f in ipairs(BENCH) do
		local p = RM.DKP.EnsurePlayer(f[1], f[2])
		p.d = p.d or {}
		p.d[RM.DKP.ActivePool()] = 100
		RM.db.config.standby[f[1]] = true
	end
	-- Testspieler mit 100 DKP im aktuellen Topf
	local pool = RM.DKP.ActivePool()
	for _, f in ipairs(FAKE) do
		local p = RM.DKP.EnsurePlayer(f[1], f[2])
		p.d = p.d or {}
		p.d[pool] = 100
	end
	T.active = true
	T.blocked = 0
	-- der Testraid startet leer (nur du) – gefüllt wird nur auf Wunsch: "Raid füllen" oder Anmeldungen einladen
	T.roster = {}; T.myGroup = nil
	T.InstallSimulations()
	-- Markierung für den Discord-Bot: Daten aus dem Testmodus nie als echte DKP übernehmen
	-- post = true: jedes Speichern (/reload, Ausloggen) schickt das Testergebnis an Discord (DKP- und Loot-Kanal)
	RM.db.testMode = { active = true, started = GetServerTime(), pool = T.pool, post = T.AutoSendOn() or nil }
	C_Timer.After(0.2, function() if T.active then T.UpdateBars() end end)
	T.ApplySpeed()
	Log("Testmodus AN – Daten gesichert, keine Nachrichten an Gilde/Raid. Der Testraid ist leer (nur du), " .. #BENCH .. " Testspieler auf der Ersatzbank. "
		.. "Füllen nur auf Wunsch: \"Raid füllen\" (39 Testspieler) oder in RaidMaster Anmeldungen einladen.")
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
		local size = RM.db.config and RM.db.config.mainSize
		Replace(RM.db.data, b.data)
		Replace(RM.db.session, b.session)
		Replace(RM.db.trade, b.trade)
		Replace(RM.db.config, b.config)
		if b.specs and RM.db.specs then Replace(RM.db.specs, b.specs) end
		if b.hasSignup ~= nil then RM.db.signup = b.hasSignup and b.signup or nil end
		if pos then RM.db.config.positions = pos end
		RM.db.config.mainSize = size
	end
	if RM.db then RM.db.testMode = nil end
	RaidMasterTestDB = nil
	if not silent then RM.Fire("SESSION_CHANGED"); RM.Fire("DATA_CHANGED"); RM.Fire("CONFIG_CHANGED") end
end

---------------------------------------------------------------------------
-- Simulationen im Testmodus: Einladen, Gruppen, Plündermeister, Werbung, Boss im Ziel
---------------------------------------------------------------------------
local sim = {}

-- Testmodus: Nachricht so zeigen, wie sie im Spiel erscheinen würde – nur bei dir, mit [Test] davor
local CHAT_LABEL = { RAID = "Schlachtzug", RAID_WARNING = "Schlachtzugwarnung", PARTY = "Gruppe", GUILD = "Gilde",
	SAY = "Sagen", YELL = "Schreien", WHISPER_INFORM = "Flüstern" }
function T.ShowChat(ch, msg, target)
	msg = tostring(msg or "")
	T.lastChat = T.lastChat or {}
	table.insert(T.lastChat, 1, (CHAT_LABEL[ch] or ch) .. ": " .. msg)
	while #T.lastChat > 30 do table.remove(T.lastChat) end
	local info = ChatTypeInfo and (ChatTypeInfo[ch] or ChatTypeInfo.RAID) or nil
	local r, g, b = 1, 0.5, 0
	if info then r, g, b = info.r or r, info.g or g, info.b or b end
	local text
	if ch == "WHISPER_INFORM" then
		text = string.format("|cff999999[Test]|r An [%s] flüstern: %s", tostring(target), msg)
	else
		text = string.format("|cff999999[Test]|r [%s] [%s]: %s", CHAT_LABEL[ch] or ch, RM.Me(), msg)
	end
	local frame = DEFAULT_CHAT_FRAME
	if frame and frame.AddMessage then frame:AddMessage(text, r, g, b) else print(text) end
	-- Schlachtzugwarnung wie im Spiel groß in der Bildschirmmitte (mit Warnton)
	if ch == "RAID_WARNING" and RaidNotice_AddMessage and RaidWarningFrame then
		pcall(RaidNotice_AddMessage, RaidWarningFrame, msg, ChatTypeInfo and ChatTypeInfo.RAID_WARNING or { r = 1, g = 0.28, b = 0 })
		if PlaySound and SOUNDKIT and SOUNDKIT.RAID_WARNING then pcall(PlaySound, SOUNDKIT.RAID_WARNING) end
	end
	RM.Fire("TEST_CHAT", ch, msg)
	if T.Refresh then pcall(T.Refresh) end
end

local function SignupEntry(name)
	for _, e in ipairs((RM.db.signup and RM.db.signup.list) or {}) do
		if e.name == name then return e end
	end
end

local RANDOM_CLASSES = { "WARRIOR", "PRIEST", "MAGE", "ROGUE", "HUNTER", "WARLOCK", "DRUID" }

-- Testgilde: Mitglieder, die online, aber nicht angemeldet sind (für "Lücken füllen" > Gilde fragen)
-- { Name, Klasse, Skillung (Punkte) oder nil = unbekannt }
local GUILD_FAKE = {
	{ "Brannok", "WARRIOR", { 5, 5, 41 } }, { "Seluna", "PRIEST", { 21, 30, 0 } }, { "Mirella", "PRIEST", nil },
	{ "Thalor", "MAGE", { 10, 0, 41 } }, { "Varis", "ROGUE", { 21, 30, 0 } }, { "Elowen", "DRUID", { 11, 0, 40 } },
	{ "Korgath", "WARLOCK", { 0, 21, 30 } }, { "Hargrim", "HUNTER", { 0, 31, 20 } }, { "Torvik", "WARRIOR", nil },
}
local function GuildClass(name)
	for _, g in ipairs(GUILD_FAKE) do if g[1] == name then return g[2] end end
end
-- Fremde, die sich im Test auf die Gruppensuche melden: { Name, Klasse, Flüstertext }
local STRANGERS = {
	{ "Kaldor", "PRIEST", "inv heal" }, { "Freyja", "SHAMAN", "inv resto" }, { "Grumbash", "WARRIOR", "inv tank" },
	{ "Lyrana", "MAGE", "inv" }, { "Tobrin", "ROGUE", "inv" }, { "Mareike", "PALADIN", "inv holy" },
	{ "Orrik", "WARLOCK", "inv" }, { "Zelda", "HUNTER", "inv" }, { "Bram", "DRUID", "inv heal" }, { "Ysolde", "PRIEST", "inv shadow" },
}

-- nächste Gruppe mit freiem Platz (je 5)
local function FreeGroup()
	local count = {}
	for _, m in ipairs(T.roster or {}) do count[m.group or 1] = (count[m.group or 1] or 0) + 1 end
	local mine = T.myGroup or 1
	count[mine] = (count[mine] or 0) + 1      -- du selbst
	for g = 1, 8 do if (count[g] or 0) < 5 then return g end end
	return 8
end

local function RosterUpdated()
	RM.SimulateEvent("GROUP_ROSTER_UPDATE")
	RM.Fire("SESSION_CHANGED")
	if T.Refresh then T.Refresh() end
end

-- Einladung: die meisten nehmen nach 1–3 Sek. an, manche lehnen ab, manche sind offline
function T.SimInvite(name)
	name = RM.Short(name)
	if not T.active or name == RM.Me() then return end
	T.roster = T.roster or {}
	for _, m in ipairs(T.roster) do if m.name == name then return end end
	local e = SignupEntry(name)
	local S = RM.Signup
	if S and S.MarkInvite then S.MarkInvite(name, "invited") end
	-- wer im Test schon zugesagt hat (Gilde, Gruppensuche), nimmt sicher an
	local sure = RM.Gaps and ((RM.Gaps.asked[name] and RM.Gaps.asked[name].state == "yes") or RM.Gaps.answered[name])
	local roll = sure and 100 or math.random(100)
	if roll <= 7 then
		C_Timer.After(1 + math.random(), function()
			Log(name .. " hat die Einladung abgelehnt (Test).")
			if S and S.MarkInvite then S.MarkInvite(name, "declined") end
		end)
		return
	elseif roll <= 15 then
		Log(name .. " ist offline – nicht gefunden (Test).")
		if S and S.MarkInvite then S.MarkInvite(name, "notfound") end
		return
	end
	C_Timer.After(1 + math.random() * 2, function()
		if not T.active then return end
		for _, m in ipairs(T.roster) do if m.name == name then return end end
		-- wie im Spiel: ein voller Schlachtzug nimmt niemanden mehr auf
		local size = (S and S.RaidSize and S.RaidSize()) or 40
		if #FakeMembers() >= size then
			Log(string.format("%s kann nicht beitreten – der Raid ist voll (%d/%d, Test).", name, #FakeMembers(), size))
			if S and S.MarkInvite then S.MarkInvite(name, "full") end
			return
		end
		local class = (e and (e.cls or e.class)) or (RM.Gaps and RM.Gaps.knownClass[name]) or (GuildClass and GuildClass(name))
			or RANDOM_CLASSES[math.random(#RANDOM_CLASSES)]
		local p = RM.DKP.EnsurePlayer(name, class)
		p.d = p.d or {}
		local pool = RM.DKP.ActivePool()
		if not p.d[pool] or p.d[pool] == 0 then p.d[pool] = 100 end
		T.roster[#T.roster + 1] = { name = name, class = class, group = FreeGroup(), online = true }
		Log(string.format("%s ist dem Raid beigetreten (Test, Gruppe %d).", name, T.roster[#T.roster].group))
		RosterUpdated()
	end)
end

-- Gruppen nach der Aufstellung aus Discord einteilen (ohne echtes Verschieben)
function T.SimArrange(silent)
	-- Aufstellung aus Discord, Main- und Offtank immer in Gruppe 1 (wie im echten Raid)
	local want = RM.Signup.WantedGroups and RM.Signup.WantedGroups() or ((RM.db.signup and RM.db.signup.groups) or {})
	if not next(want) then
		if not silent then Log("Keine Gruppen-Aufstellung importiert (in Discord: /raid aufstellung, dann Export).") end
		return
	end
	local moved = 0
	for _, m in ipairs(T.roster or {}) do
		local g = want[m.name]
		if g and m.group ~= g then m.group = g; moved = moved + 1 end
	end
	local me = want[RM.Me()]
	if me and me ~= (T.myGroup or 1) then T.myGroup = me; moved = moved + 1 end
	local mts = RM.Signup.MainTanks and RM.Signup.MainTanks() or {}
	if not silent or moved > 0 then
		Log(string.format("Gruppen eingeteilt (Test): %d Spieler verschoben.%s", moved,
			#mts > 0 and (" Main-/Offtank in Gruppe 1: " .. table.concat(mts, ", ")) or ""))
	end
	RM.Fire("SESSION_CHANGED")
	if T.Refresh then T.Refresh() end
end

-- Anmeldungen importiert: Testraid startet leer, die Gruppe entsteht durch (simuliertes) Einladen
function T.UseSignupRoster()
	if not T.active then return end
	T.roster = {}; T.myGroup = nil
	local n = #((RM.db.signup and RM.db.signup.list) or {})
	Log(string.format("Anmeldungen im Test: %d Einträge. Testraid ist jetzt leer – lade ein (RaidMaster, Seite Anmeldungen: \"Alle einladen\").", n))
	RosterUpdated()
end

-- Testraid leeren: alle (simuliert) Eingeladenen verlassen den Raid, die Anmeldungen bleiben
function T.ClearRoster()
	if not T.active then return end
	if RM.Signup and RM.Signup.StopInvites and RM.Signup.IsInviting() then RM.Signup.StopInvites() end
	T.roster = {}; T.myGroup = nil
	Log("Testraid geleert – nur du bist noch drin. Die Anmeldungen bleiben, du kannst erneut einladen.")
	RosterUpdated()
end

function T.UseFakeRoster()
	if not T.active then T.Start() end
	-- als echte Liste, damit "Gruppen einteilen" die Testspieler verschieben kann
	T.roster = {}; T.myGroup = nil
	T.myGroup = 1
	for i, f in ipairs(FAKE) do T.roster[#T.roster + 1] = { name = f[1], class = f[2], group = math.floor(i / 5) + 1, online = true } end
	Log("Testraid gefüllt: du + " .. #FAKE .. " Testspieler (MC-Aufstellung).")
	RosterUpdated()
end
T.FillRoster = T.UseFakeRoster

-- Ist der Testraid leer (nur du drin)?
function T.RosterEmpty()
	if not T.roster then return false end
	for _, m in ipairs(T.roster) do if m.online ~= false then return false end end
	return true
end

-- Durchläufe brauchen Mitspieler: ist der Testraid leer, nichts automatisch füllen, nur Bescheid sagen
local function NeedRoster()
	if not T.RosterEmpty() then return true end
	local msg = "Der Testraid ist leer – erst \"Raid füllen\" klicken (39 Testspieler) oder in RaidMaster Anmeldungen einladen."
	Log(msg)
	RM.Print("|cffff8c1a[Test]|r " .. msg)
	if T.Refresh then T.Refresh() end
	return false
end
T.NeedRoster = NeedRoster

function T.InstallSimulations()
	local S = RM.Signup
	if S then
		sim.invite, sim.makeRaid, sim.arrange = S.DoInvite, S.DoMakeRaid, S.ArrangeGroups
		S.DoInvite = function(name) T.SimInvite(name) end
		S.DoMakeRaid = function() end
		S.ArrangeGroups = function(silent) T.SimArrange(silent) end
	end
	sim.lootMethod, sim.lootThreshold = RM.SetLootMethod, RM.SetLootThreshold
	RM.SetLootMethod = function(method, name)
		Log(string.format("Plündermethode würde gesetzt: %s%s (Test – im Spiel nichts geändert).", tostring(method), name and (", Plündermeister " .. name) or ""))
	end
	RM.SetLootThreshold = function(v)
		Log(string.format("Plünderschwelle würde gesetzt: %s (Test).", tostring(v)))
	end
	-- Bereitschafts-Check: die Testspieler antworten (mal fehlt ein Fläschchen, mal sind Reagenzien knapp)
	if RM.Ready then
		RM.Ready.SimulateAnswers = function(id)
			for i, m in ipairs(FakeMembers()) do
				if m.name ~= RM.Me() then
					C_Timer.After(0.5 + (i % 10) * 0.2, function()
						if not T.active then return end
						local r = math.random(100)
						local reag = {}
						for _, x in ipairs(RM.Ready.REAGENTS[m.class] or {}) do
							reag[#reag + 1] = { x[2], (r % 4 == 0) and 0 or x[3] * 2, x[3] }
						end
						RM.Ready.OnAnswer(m.name, { id = id, s = { f = (r > 15) and "Fläschchen der Titanen" or nil, e = (r > 25) and 2 or 0,
							fr = 40 + (r % 5) * 40, rg = reag, du = (r % 9 == 0) and 12 or 85 } })
					end)
				end
			end
			Log("Bereitschafts-Check (Test): die Testspieler antworten.")
		end
	end
	local Gp = RM.Gaps
	if Gp then
		Gp.SimGuild = function()
			local out = {}
			for _, g in ipairs(GUILD_FAKE) do
				if g[3] and RM.Spec and RM.Spec.Store and not (RM.db.specs and RM.db.specs[g[1]]) then pcall(RM.Spec.Store, g[1], g[2], g[3], "addon") end
				out[#out + 1] = { name = g[1], class = g[2] }
			end
			return out
		end
		-- gefragte Gildenmitglieder antworten nach 2–4 Sek.: meist "inv", manchmal keine Zeit
		Gp.SimulateAsk = function(name)
			C_Timer.After(2 + math.random() * 2, function()
				if not T.active then return end
				local yes = math.random(100) <= 75
				local msg = yes and "inv" or "sorry, heute nicht"
				Log(name .. " flüstert: " .. msg .. " (Test)")
				RM.SimulateEvent("CHAT_MSG_WHISPER", msg, name)
			end)
		end
	end
	if RM.Ad then
		RM.Ad.SimulatePost = function(text, key)
			Log("Werbung (Test, nicht gepostet) in " .. tostring(key) .. ": " .. text)
			if Gp and Gp.Searching() then
				-- Gruppensuche: passende und unpassende Fremde melden sich
				local list = {}
				for _, st in ipairs(STRANGERS) do list[#list + 1] = st end
				for i = #list, 2, -1 do local j = math.random(i); list[i], list[j] = list[j], list[i] end
				for i = 1, math.min(#list, 6) do
					local st = list[i]
					local who = st[1] .. math.random(10, 99)
					Gp.knownClass[who] = st[2]
					C_Timer.After(1.5 + i * 1.5, function()
						if not T.active then return end
						Log(who .. " (" .. st[2] .. ") flüstert: " .. st[3] .. " (Test)")
						RM.SimulateEvent("CHAT_MSG_WHISPER", st[3], who)
					end)
				end
				return
			end
			-- ein paar Fremde melden sich mit "inv"
			for i = 1, math.random(2, 4) do
				local who = ({ "Kaldor", "Freyja", "Grumbash", "Lyrana", "Tobrin", "Zuljin", "Mareike", "Orrik" })[math.random(8)] .. i
				C_Timer.After(2 + i * 2, function()
					if not T.active then return end
					Log(who .. " flüstert: inv (Test)")
					RM.SimulateEvent("CHAT_MSG_WHISPER", "inv", who)
				end)
			end
		end
	end
	sim.listener = sim.listener or true
end

function T.RemoveSimulations()
	local S = RM.Signup
	if S and sim.invite then S.DoInvite, S.DoMakeRaid, S.ArrangeGroups = sim.invite, sim.makeRaid, sim.arrange end
	if sim.lootMethod then RM.SetLootMethod, RM.SetLootThreshold = sim.lootMethod, sim.lootThreshold end
	if RM.Ad then RM.Ad.SimulatePost = nil end
	if RM.Ready then RM.Ready.SimulateAnswers = nil end
	if RM.Gaps then
		RM.Gaps.SimGuild, RM.Gaps.SimulateAsk = nil, nil
		wipe(RM.Gaps.asked); wipe(RM.Gaps.answered); wipe(RM.Gaps.knownClass)
		RM.Gaps.search, RM.Gaps.searchUntil = nil, 0
	end
	if RM.Signup and RM.Signup.inviteState then wipe(RM.Signup.inviteState) end
	if RM.BossBar then RM.BossBar.SetTestTarget(nil) end
	sim.invite, sim.lootMethod = nil, nil
end

RM.Listen("SIGNUP_CHANGED", function()
	if T.active and RM.db and RM.db.signup and RM.db.signup.imported and RM.db.signup.imported ~= T.signupSeen then
		T.signupSeen = RM.db.signup.imported
		T.UseSignupRoster()
	end
end)

-- Boss im Ziel simulieren (für die Boss-Leiste der Raidleitung)
function T.TargetBoss(id)
	if not RM.BossBar then return end
	if not T.active then T.Start() end
	RM.BossBar.SetTestTarget(id)
	local b = id and RM.Data.Bosses[id]
	Log(b and ("Ziel: " .. b.name .. " (Test) – die Boss-Leiste ist da: \"Ansage + Symbole\" klicken.") or "Ziel gelöscht (Test).")
end

function T.Stop()
	if not T.active then return end
	if RM.Auction and RM.Auction.current then pcall(RM.Auction.Cancel) end
	for _, k in ipairs(OVERRIDE) do RM[k] = saved[k] end
	if RM.Auction and RM.Auction.queue then wipe(RM.Auction.queue) end   -- Test-Items nicht im echten Raid lassen
	if T.StopRun then T.StopRun() end
	if RM.Loot then RM.Loot.isOpen = false; wipe(RM.Loot.items) end
	if RM.Loot and saved.Deliver then RM.Loot.Deliver = saved.Deliver end
	if RM.Loot and saved.Ensure then RM.Loot.EnsureSettings = saved.Ensure end
	if RM.Loot and saved.Warn then RM.Loot.Warn = saved.Warn end
	if saved.CheckMainLeader then RM.CheckMainLeader = saved.CheckMainLeader end
	if saved.RaidStart then RM.Raid.Start, RM.Raid.End = saved.RaidStart, saved.RaidEnd; saved.RaidStart, saved.RaidEnd = nil, nil end
	T.active = false
	if RM.BossBar and RM.BossBar.testTarget then RM.BossBar.testTarget = nil end
	T.UpdateBars()
	T.HideAutoSend()
	T.RemoveSimulations()
	T.roster = nil
	Restore()
	Log(string.format("Testmodus AUS – alle Daten wiederhergestellt (%d Addon-Nachrichten wurden zurückgehalten).", T.blocked or 0))
end

-- Testdaten an Discord: WoW speichert beim /reload, der Uploader schickt die Datei, der Bot postet
-- DKP-Stand, Teilnehmer und Loot des Tests (mit TEST markiert) und löscht alles nach 10 Minuten.
-- Nach dem Neuladen ist der Testmodus beendet und deine echten Daten sind wieder da.
function T.SendToDiscord()
	if not T.active then Log("Erst den Testmodus starten und einen Raid simulieren.") return end
	RM.db.testMode = RM.db.testMode or { active = true, started = GetServerTime() }
	RM.db.testMode.post = true
	RM.db.testMode.pool = T.pool
	RM.UI.Confirm("Testdaten an Discord senden?\nDie Oberfläche wird neu geladen. Der Bot postet DKP, Teilnehmer und Loot des Tests "
		.. "(mit TEST markiert) und löscht sie nach 10 Minuten. Danach ist der Testmodus beendet, deine echten Daten sind wieder da.",
		function() ReloadUI() end, function() RM.db.testMode.post = nil end)
end

-- Gibt es im Test schon ein Ergebnis (Raid, Bosse, DKP, Loot)?
function T.HasResults()
	local since = RM.db.testMode and RM.db.testMode.started or 0
	for _, e in ipairs(RM.db.data.log or {}) do
		if type(e) == "table" and not e.u and (e.t or 0) >= since then return true end
	end
	return false
end

-- Nach dem Raid: Ergebnis mit Countdown automatisch senden (lädt die Oberfläche neu)
local sendFrame, sendTicker
local sendState = {}
local SEND_DELAY = 10
function T.HideAutoSend()
	if sendFrame then sendFrame:Hide() end
end
function T.AutoSend(reason)
	if not T.active or not T.AutoSendOn() then return end
	RM.db.testMode = RM.db.testMode or { active = true, started = GetServerTime() }
	RM.db.testMode.post = true
	RM.db.testMode.pool = T.pool
	if not sendFrame then
		local f = UI.Frame(UIParent, 440, 112)
		f:SetFrameStrata("FULLSCREEN_DIALOG")
		f:SetToplevel(true)
		f:SetClampedToScreen(true)
		UI.Skin(f, nil, COLORS.accent)
		UI.MakeMovable(f, "testSend", "TOP", 0, -150)
		f.text = UI.Text(f, "", 13)
		f.text:SetPoint("TOPLEFT", 14, -12)
		f.text:SetWidth(412)
		f.text:SetJustifyH("LEFT")
		local now = UI.Button(f, "Jetzt senden", 130, 28, function() f:Hide(); ReloadUI() end)
		now:SetPoint("BOTTOMLEFT", 14, 12)
		now:SetAccent(true)
		local later = UI.Button(f, "Später", 130, 28, function()
			f:Hide()
			Log("Ergebnis wird beim nächsten /reload oder Ausloggen an Discord gesendet (oder 'Test an Discord senden').")
		end)
		later:SetPoint("LEFT", now, "RIGHT", 8, 0)
		sendFrame = f
		function f.Tick()
			if not f:IsShown() then return end
			local left = sendState.endsAt - GetTime()
			if left <= 0 then
				f:Hide()
				if T.active then ReloadUI() end
				return
			end
			f.text:SetText((sendState.reason or "Test fertig.") .. "\n" .. string.format(
				"Ergebnis (DKP, Teilnehmer, Loot) geht in |cffffd200%d Sek.|r an Discord – die Oberfläche lädt dafür neu.\n"
				.. "Danach ist der Testmodus beendet, deine echten Daten sind wieder da.", math.ceil(left)))
		end
		f:SetScript("OnHide", function() if sendTicker then sendTicker:Cancel(); sendTicker = nil end end)
	end
	sendState.reason = reason
	sendState.endsAt = GetTime() + SEND_DELAY
	sendFrame:Show()
	sendFrame:Raise()
	if sendTicker then sendTicker:Cancel() end
	sendTicker = C_Timer.NewTicker(0.25, sendFrame.Tick)
	sendFrame.Tick()
	Log((reason or "Test fertig.") .. " Ergebnis geht in " .. SEND_DELAY .. " Sek. an Discord.")
end

-- Raid starten/beenden in RaidMaster überschreibt alle laufenden Befehle des Test-Tools:
-- Durchlauf (auch mehrere Raidabende), laufende Versteigerung, Warteschlange, Vergabe-Fenster, Sende-Countdown.
-- Beim Starten wird ein noch offener Test-Raid still geschlossen (ohne Bonus), damit der neue Start gilt.
function T.Override(what, keepSession)
	local A = RM.Auction
	local did = false
	if T.IsRunning() then T.StopRun(); did = true end
	T.series = nil
	if A.current then pcall(A.Cancel); A.current = nil; did = true end
	if #A.queue > 0 then wipe(A.queue); did = true end
	if A.HideAward then A.HideAward() end
	if RM.Loot then RM.Loot.isOpen = false; wipe(RM.Loot.items) end
	if sendFrame and sendFrame:IsShown() then T.HideAutoSend(); did = true end
	if not keepSession and RM.db.session.active then
		RM.db.session.active = false
		RM.db.session.ended = GetServerTime()
		did = true
	end
	RM.Fire("AUCTION_CHANGED"); RM.Fire("SESSION_CHANGED")
	if did then Log("\"" .. what .. "\" in RaidMaster – laufende Befehle des Test-Tools abgebrochen.") end
end

-- Im Test: fertige Versteigerung sofort vergeben (keine "Vergeben"-Abfrage)
RM.Listen("AUCTION_CHANGED", function()
	if not (T.active and T.AutoAwardOn()) then return end
	local A = RM.Auction
	if not A.AwaitingAward() then return end
	local c = A.current
	C_Timer.After(0.2, function()
		if T.active and A.current == c and A.AwaitingAward() then
			if A.HideAward then A.HideAward() end
			A.Award()
		end
	end)
end)

-- "Testmodus beenden": ein vorhandenes Ergebnis vorher an Discord senden?
function T.StopAsk()
	if not T.active then return end
	if T.AutoSendOn() and T.HasResults() then
		RM.UI.Confirm("Das Testergebnis vorher an Discord senden (DKP-, Teilnehmer- und Loot-Kanal)?\n"
			.. "Ja: die Oberfläche lädt neu, danach ist der Testmodus beendet. Nein: alles verwerfen.",
			function() T.HideAutoSend(); RM.db.testMode.post = true; ReloadUI() end,
			function() T.HideAutoSend(); T.Stop() end, "Senden", "Verwerfen")
	else
		T.Stop()
	end
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

function T.RoleName() return ROLE_NAMES[T.role] or "?" end

function T.SetRole(role)
	if role == "officer" then role = "raidlead" end      -- frühere Ansicht "Offizier" = Raidleiter
	if not ROLE_NAMES[role] then role = "raidlead" end
	T.role = role
	if not T.active then T.Start() end
	Log("Ansicht als " .. ROLE_NAMES[role] .. ".")
	RM.Fire("CONFIG_CHANGED"); RM.Fire("SESSION_CHANGED")
	T.UpdateBars()
	if RM.UI.RefreshCurrent then RM.UI.RefreshCurrent() end
end

-- Leisten (Markierungen, Boss-Leiste) passend zur Ansicht zeigen
function T.UpdateBars()
	if RM.Markers and RM.Markers.UpdateBar then pcall(RM.Markers.UpdateBar) end
	if RM.BossBar and RM.BossBar.Update then pcall(RM.BossBar.Update) end
end

---------------------------------------------------------------------------
-- Reiter "Ansagen": alle Ansagen und Leisten im Testmodus ausprobieren (nichts geht an andere)
---------------------------------------------------------------------------
local function NeedActive()
	if not T.active then T.Start() end
	if T.role ~= "raidlead" then T.SetRole("raidlead") end
end

function T.TryBossBar()
	NeedActive()
	local def = RM.Data.Pools[T.pool]
	local id = T.boss or (def and def.bossIDs and def.bossIDs[1])
	if not id then Log("Für diesen Raid sind noch keine Bosse bekannt.") return end
	T.TargetBoss(id)
end

function T.TryMarkerBar()
	NeedActive()
	RM.db.config.markerBar = true
	T.UpdateBars()
	Log("Markierungsleiste an – Symbole per Klick (im Test ohne echtes Ziel nur angezeigt).")
end

function T.TryPull() NeedActive() RM.Timer.Pull(tonumber(RM.db.config.pullSeconds) or 10) end
function T.TryBreak() NeedActive() RM.Raid.StartPause(60) end
function T.TryReady() NeedActive() RM.Ready.Start() end

function T.TryWelcome()
	NeedActive()
	-- mit einem Testgast und einem Spieler von der Ersatzbank, damit alle Zeilen zu sehen sind
	local extra = { { name = "Gastino" } }
	if BENCH[1] then extra[#extra + 1] = { name = BENCH[1][1], bench = true } end
	for i, line in ipairs(RM.Welcome.Lines(T.pool, extra)) do
		C_Timer.After((i - 1) * 0.4, function() RM.RaidChat(line, "RAID") end)
	end
end

function T.TryFirstKill()
	NeedActive()
	local def = RM.Data.Pools[T.pool]
	local id = T.boss or (def and def.bossIDs and def.bossIDs[#def.bossIDs]) or 672
	local b = RM.Data.Bosses[id]
	RM.Records.Celebrate(id, b and b.name or "Ragnaros", 3, GetServerTime(), true)
end

function T.TryRecord()
	NeedActive()
	local def = RM.Data.Pools[T.pool]
	local id = T.boss or (def and def.bossIDs and def.bossIDs[1]) or 663
	local b = RM.Data.Bosses[id]
	RM.Announce(string.format(RM.L["[RaidMaster] NEUER REKORD: %s in %s (vorher %s)!"],
		b and b.name or "Lucifron", "1:42", "2:05"), true)
end

function T.TryBossInfo()
	NeedActive()
	local def = RM.Data.Pools[T.pool]
	local id = T.boss or (def and def.bossIDs and def.bossIDs[1])
	local boss = id and RM.Data.Bosses[id]
	if boss then RM.BossBar.Announce({ id = id, name = boss.name, pool = boss.pool, template = boss.template }) else Log("Kein Boss gewählt.") end
end

---------------------------------------------------------------------------
-- Simulationen (Testraid: 39 Testspieler + du)
---------------------------------------------------------------------------
local function Need()
	if not T.active then T.Start() end
	if T.role ~= "raidlead" and T.role ~= "looter" then
		Log("Für Raid, Bosskill und Versteigerung bitte 'Ansicht als: Raidleiter' wählen.")
		return false
	end
	return true
end

-- DKP für dich selbst (beliebige Menge, auch negativ) im gewählten Raid – nur im Testmodus
function T.GiveMeDKP(amount)
	amount = tonumber(amount)
	if not amount or amount == 0 then Log("Bitte eine Zahl eingeben (z. B. 500 oder -50).") return end
	amount = math.floor(amount)
	if not T.active then T.Start() end
	local pool = T.pool or RM.DKP.ActivePool()
	RM.DKP.EnsurePlayer(RM.Me(), select(2, UnitClass("player")))
	-- im Test immer erlaubt, unabhängig von der gewählten Ansicht
	local canEdit = RM.CanEdit
	RM.CanEdit = function() return true end
	local ok = pcall(RM.DKP.Adjust, RM.Me(), amount, "Test: DKP selbst vergeben", pool)
	RM.CanEdit = canEdit
	Log(string.format("%s%d DKP für dich (%s) – jetzt %d.", amount > 0 and "+" or "", amount, RM.DKP.PoolName(pool), RM.DKP.Get(RM.Me(), pool)))
	if not ok then Log("DKP konnten nicht gebucht werden.") end
	RM.Fire("DATA_CHANGED")
	if RM.UI.RefreshCurrent then RM.UI.RefreshCurrent() end
end

function T.StartRaid()
	if not Need() then return end
	RM.db.config.activePool = T.pool
	T.manualStart = true
	local ok, err = pcall(RM.Raid.Start)
	T.manualStart = nil
	if not ok then error(err) end
	Log("Raid gestartet (" .. RM.DKP.PoolName(T.pool) .. ").")
end

function T.EndRaid()
	if not Need() then return end
	RM.Raid.End()      -- sendet das Ergebnis (siehe Raid.End im Testmodus)
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
	T.ApplySpeed()
	RM.Auction.Start(link)
	if not RM.Auction.current then Log("Versteigerung konnte nicht starten.") return end
	Log("Versteigerung gestartet: " .. link .. " – Testspieler bieten gleich.")
	local amounts = { 10, 15, 25, 30 }
	local step = math.min(2, math.max(0.4, (T.BidWindow() - 0.5) / #amounts))
	for i, amount in ipairs(amounts) do
		local who = FAKE[(i % #FAKE) + 1][1]
		C_Timer.After(0.5 + i * step, function()
			local ok, err = RM.Auction.ReceiveBid(who, amount, "")
			Log(who .. " bietet " .. amount .. " DKP" .. (ok and "" or (" – abgelehnt: " .. tostring(err))))
			if i == #amounts then T.ShortenRest(RM.Auction.current) end
		end)
	end
end

-- Magmadar: Jäger nach Einlullender Schuss fragen; die Testjäger antworten per Flüstern
function T.TranqTest()
	if not T.active then T.Start() end
	if T.role ~= "lead" and T.role ~= "raidlead" then Log("Die Jäger-Abfrage gibt es nur für Raidleiter und Assistenten.") return end
	RM.Tranq.Ask()
	Log("Jäger-Abfrage gestartet – Testjaeger und Testjaeger2 antworten 'ja', Testjaegerin 'nein'.")
	C_Timer.After(5, function()
		RM.SimulateEvent("CHAT_MSG_WHISPER", "ja", "Testjaeger")
		RM.SimulateEvent("CHAT_MSG_WHISPER", "nein", "Testjaegerin")
		RM.SimulateEvent("CHAT_MSG_WHISPER", "ja", "Testjaeger2")
		Log("Antworten: " .. RM.Tranq.StatusText():gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""))
		RM.Tranq.Post()
		Log("Einlull-Rotation als Schlachtzugwarnung gepostet (im Test nur bei dir).")
	end)
end

---------------------------------------------------------------------------
-- Ganzen Raid durchspielen: alle Bosse nacheinander, Beute aus der echten Beutetabelle
-- (Classic, TBC, Wrath), Versteigerungen mit Testgeboten, Trash-Beute zwischendurch
---------------------------------------------------------------------------
local run
function T.IsRunning() return run ~= nil or T.series ~= nil end

T.OWN_LOOT_MIN_KILLS = 2   -- ab so vielen erfassten Kills nimmt der Test die eigene Beute-Datenbank

local function LootTable(def)
	if not (def and RaidMasterTestLoot) then return nil end
	for id in pairs(def.ids or {}) do
		local t = RaidMasterTestLoot[id .. ":" .. tostring(def.exp)]
		if t then return t end
		for key, v in pairs(RaidMasterTestLoot) do
			if key:match("^" .. id .. ":") then return v end
		end
	end
end

local function BossLoot(lt, boss, index)
	local en = (boss.en or ""):lower()
	for _, b in ipairs(lt) do if b.n:lower() == en then return b.i end end
	if en ~= "" then
		for _, b in ipairs(lt) do
			local n = b.n:lower()
			if n:find(en, 1, true) or en:find(n, 1, true) then return b.i end
		end
	end
	return lt[index] and lt[index].i
end

local function ItemInfo(id)
	local name, link, quality = (RM.GetItemInfo or GetItemInfo)(id)
	return link, quality
end

-- n zufällige Items, die das Spiel schon kennt (sonst beim nächsten Mal)
local function Pick(ids, n)
	local pool, out = {}, {}
	for _, id in ipairs(ids or {}) do if ItemInfo(id) then pool[#pool + 1] = id end end
	for _ = 1, n do
		if #pool == 0 then break end
		out[#out + 1] = table.remove(pool, math.random(#pool))
	end
	return out
end

local RULE_NAMES = { auction = "Versteigerung", bank = "Gildenbank", de = "Entzauberer", crafter = "Handwerker",
	manual = "von Hand verteilen", notify = "Hinweis (legendär) – nie automatisch", roll = "Würfeln" }

-- ein Item wie im echten Raid behandeln: Regel prüfen, versteigern oder zuteilen
local function HandleItem(id, source)
	local link, quality = ItemInfo(id)
	if not link then return end
	local action = RM.Loot.Classify(link, quality)
	-- wie ein offenes Lootfenster beim Plündermeister (Seite Loot: "Aktuelles Lootfenster")
	RM.Loot.isOpen = true
	RM.Loot.items[#RM.Loot.items + 1] = { link = link, quality = quality, action = action, done = action ~= "auction" and action ~= "manual" and action ~= "notify" }
	RM.Fire("LOOT_CHANGED")
	if action == "auction" then
		-- wie im echten Raid in die Warteschlange von RaidMaster (Seite Versteigerung)
		RM.Auction.Enqueue(link)
		Log(source .. ": " .. link .. " -> Warteschlange (Versteigerung)")
	else
		local who = RM.Loot.RecipientFor and RM.Loot.RecipientFor(action)
		Log(source .. ": " .. link .. " -> " .. (RULE_NAMES[action] or tostring(action)) .. (who and who ~= "" and (" (" .. who .. ")") or ""))
		run.other = run.other + 1
	end
end

-- Testspieler bieten auf die laufende Versteigerung (2–4 Gebote, jeder höchstens seine DKP)
local function AddFakeBids(c)
	if not c or c.testBids then return end
	c.testBids = true
	local bidders = {}
	for _, n in ipairs(T.MemberNames()) do bidders[#bidders + 1] = n end
	if #bidders == 0 then return end
	local count = math.random(2, 4)
	local amount = c.min
	-- Gebote gleichmäßig auf den Anfang der Versteigerung verteilen
	local step = math.min(1.5, math.max(0.4, (T.BidWindow() - 0.5) / count))
	for i = 1, count do
		local who = table.remove(bidders, math.random(#bidders))
		amount = amount + math.random(0, 3) * (c.inc or 5)
		local a = amount
		local last = (i == count)
		C_Timer.After(0.5 + i * step, function()
			if RM.Auction.current == c and not c.finished then
				local have = RM.DKP.Get(who, c.pool)
				local bid = math.min(a, have)
				if bid >= ((c.highName and (c.high + c.inc)) or c.min) then RM.Auction.ReceiveBid(who, bid, "") end
				if last then T.ShortenRest(c) end
			end
		end)
		amount = amount + (c.inc or 5)
	end
end

-- nächstes Item aus der Warteschlange von RaidMaster versteigern
local function StartFromQueue()
	if RM.Auction.current or #RM.Auction.queue == 0 then return false end
	RM.Auction.Start(1)
	AddFakeBids(RM.Auction.current)
	return RM.Auction.current ~= nil
end

local function RunStep()
	if not run or not T.active then return end
	local now = GetTime()
	if now < run.waitUntil then return end
	local c = RM.Auction.current
	-- Versteigerung fertig: wie die Raidleitung "Vergeben" klicken
	if c and c.finished then
		-- selbst versteigern: du klickst "Vergeben" / "Nicht vergeben" wie im echten Raid
		-- (im Test standardmäßig automatisch vergeben, siehe T.AutoAwardOn)
		if not (T.autoAuction or T.AutoAwardOn()) then return end
		if c.highName then
			if RM.Auction.HideAward then RM.Auction.HideAward() end
			RM.Auction.Award()
		else
			RM.Auction.current = nil
		end
		run.waitUntil = now + Pause(1.5)
		return
	end
	-- läuft eine Versteigerung (von dir gestartet), bieten die Testspieler mit
	if c then AddFakeBids(c) return end
	if #RM.Auction.queue > 0 then
		if T.autoAuction then
			if not StartFromQueue() then Log("Versteigerung aus der Warteschlange nicht möglich."); wipe(RM.Auction.queue) end
			run.waitUntil = now + 1
		elseif not run.told then
			run.told = true
			Log(string.format("%d Item(s) in der Warteschlange – starte jede Versteigerung selbst auf der Seite Versteigerung "
				.. "(Item wählen, \"Gewähltes starten\"). Testspieler bieten mit, \"Vergeben\" klickst du. Danach geht es zum nächsten Boss.", #RM.Auction.queue))
			RM.UI.Open("auction")
		end
		return
	end
	run.told = false
	-- nächster Boss
	run.index = run.index + 1
	local boss = run.def.bosses[run.index]
	if not boss then
		if RM.BossBar then RM.BossBar.SetTestTarget(nil) end
		RM.Auction.Award = run.origAward
		RM.Loot.isOpen = false; wipe(RM.Loot.items)
		T.runEnding = true
		local ok, err = pcall(RM.Raid.End)
		T.runEnding = nil
		if not ok then Log("Fehler beim Raidende: " .. tostring(err)) end
		Log(string.format("Raid-Durchlauf fertig: %d Bosse, %d Items versteigert, %d nach Regel verteilt.", #run.def.bosses, #run.awarded, run.other))
		if T.stress then
			T.stress.items = T.stress.items + #run.awarded
			T.stress.other = T.stress.other + run.other
			T.stress.bosses = T.stress.bosses + #run.def.bosses
		end
		for _, a in ipairs(run.awarded) do Log("  " .. a) end
		Log("Alles im Testmodus – 'Testmodus beenden' setzt deine echten Daten zurück.")
		run.ticker:Cancel()
		run = nil
		if T.series and T.series.left > 0 then
			C_Timer.After(T.stress and 0.5 or 3, function() if T.active and T.series then T.NextSeriesRun() end end)
		else
			if T.series and T.series.total > 1 then
				Log(string.format("Alle %d Raidabende fertig – 'Test an Discord senden' zeigt die Raid-Abrechnungen im Discord.", T.series.total))
			end
			local total = T.series and T.series.total or 1
			T.series = nil
			T.SetTimeOffset(0)
			if T.stress then T.FinishStress() end
			T.AutoSend(total > 1 and string.format("Alle %d Raidabende fertig.", total) or "Raid-Durchlauf fertig.")
		end
		if T.Refresh then T.Refresh() end
		return
	end
	-- Trash vor jedem zweiten Boss
	if run.index > 1 and run.index % 2 == 0 then
		-- Trash: eigene Drops aus der Beute-Datenbank (ab 5 erfassten Leichen), sonst die mitgelieferte Tabelle
		local own, n = {}, 0
		if RM.LootDB then own, n = RM.LootDB.TrashIDs(run.def.key) end
		local trash = (n >= 5 and #own > 0) and own or (run.loot and run.loot.trash)
		if trash then for _, id in ipairs(Pick(trash, 1)) do HandleItem(id, "Trash") end end
	end
	local ids = boss.e
	wipe(RM.Loot.items)
	-- Boss ins Ziel: die Boss-Leiste erscheint (Ansage + Symbole per Klick)
	if RM.BossBar then RM.BossBar.SetTestTarget(boss.id or ids[#ids]) end
	RM.SimulateEvent("ENCOUNTER_START", ids[#ids], boss.name, 9, 40)
	RM.SimulateEvent("ENCOUNTER_END", ids[#ids], boss.name, 9, 40, 1)
	Log(string.format("Boss %d/%d besiegt: %s", run.index, #run.def.bosses, boss.name))
	-- Beute: zuerst die eigene Beute-Datenbank (ab 2 erfassten Kills), sonst die mitgelieferten Beutetabellen
	local own, ownKills = {}, 0
	if RM.LootDB then own, ownKills = RM.LootDB.ItemIDs(boss.id or ids[#ids]) end
	local drops
	if ownKills >= T.OWN_LOOT_MIN_KILLS and #own > 0 then
		drops = own
		Log(string.format("  Beute aus eurer Datenbank (%d Kills, %d Items)", ownKills, #own))
	elseif run.loot then
		drops = BossLoot(run.loot, boss, run.index)
	end
	if drops then
		local n = (#run.def.bosses == 1 or run.index == #run.def.bosses) and 3 or 2
		local picked = Pick(drops, n)
		if #picked == 0 then Log("  (keine Beute bekannt oder noch nicht vom Server geladen)") end
		for _, id in ipairs(picked) do HandleItem(id, boss.name) end
	end
	run.waitUntil = now + Pause(2)
end

-- Mehrere Raidabende hintereinander: auf Wunsch je eine Woche auseinander datiert
-- (GetServerTime wird nur im Testmodus verschoben und danach zurückgesetzt)
T.runs, T.weekly = 1, true
local realServerTime
local function SetTimeOffset(sec)
	if not realServerTime then realServerTime = GetServerTime end
	if sec == 0 then
		GetServerTime = realServerTime
	else
		GetServerTime = function() return realServerTime() + sec end
	end
end
T.SetTimeOffset = SetTimeOffset

function T.RunRaids(n)
	n = math.max(1, math.min(10, math.floor(tonumber(n) or 1)))
	if run then Log("Es läuft schon ein Durchlauf.") return end
	if not T.active then T.Start() end
	if not NeedRoster() then return end
	T.series = { total = n, left = n }
	T.NextSeriesRun()
end

function T.NextSeriesRun()
	local sr = T.series
	if not sr or sr.left <= 0 then return end
	local idx = sr.total - sr.left + 1
	T.SetTimeOffset(T.weekly and -(sr.left - 1) * 7 * 86400 or 0)
	Log(string.format("Raidabend %d von %d%s", idx, sr.total,
		(T.weekly and sr.total > 1) and (" – datiert auf " .. date("%d.%m.%Y", GetServerTime())) or ""))
	sr.left = sr.left - 1
	-- zurückdatierte Abende gehören auch zu den Testdaten für Discord
	if RM.db.testMode then RM.db.testMode.started = math.min(RM.db.testMode.started or GetServerTime(), GetServerTime() - 60) end
	T.RunRaid()
end

function T.RunRaid()
	if run then Log("Es läuft schon ein Durchlauf.") return end
	if not T.active then T.Start() end
	if not NeedRoster() then T.series = nil; return end
	if T.role ~= "raidlead" and T.role ~= "looter" then T.SetRole("raidlead") end
	local def = RM.Data.Pools[T.pool]
	if def and not def.bosses[1] then
		-- eigene Raids (WoW Forever): Bosse aus der eigenen Beute-Datenbank bzw. aus schon gelernten Bossen
		local list = {}
		local seen = {}
		for _, b in ipairs(RM.LootDB and RM.LootDB.BossesForPool(T.pool) or {}) do
			seen[b.id] = true
			list[#list + 1] = { e = { b.id }, id = b.id, name = b.name, en = b.name }
		end
		for _, b in ipairs(RM.Data.BossesForPool(T.pool, RM.db.data)) do
			if not seen[b.id] then list[#list + 1] = { e = { b.id }, id = b.id, name = b.name, en = b.name } end
		end
		if list[1] then
			local copy = {}
			for k, v in pairs(def) do copy[k] = v end
			copy.bosses = list
			def = copy
			Log(string.format("%s: %d Bosse aus euren eigenen Raids (Beute-Datenbank).", def.name, #list))
		end
	end
	if not def or not def.bosses[1] then
		Log("Für diesen Raid sind noch keine Bosse bekannt – sie kommen nach dem ersten echten Raid aus der Beute-Datenbank.")
		return
	end
	local loot = LootTable(def)
	-- eigene Beute-Datenbank: Items beim Server anfragen
	if RM.LootDB then
		for _, b in ipairs(def.bosses) do
			for _, id in ipairs((RM.LootDB.ItemIDs(b.id or b.e[#b.e]))) do ItemInfo(id) end
		end
	end
	-- Items beim Server anfragen, damit Namen/Qualität bereitstehen
	if loot then
		for _, b in ipairs(loot) do for _, id in ipairs(b.i) do ItemInfo(id) end end
		for _, id in ipairs(loot.trash or {}) do ItemInfo(id) end
	end
	run = { def = def, loot = loot, index = 0, queue = {}, awarded = {}, other = 0, waitUntil = GetTime() + 2 }
	T.ApplySpeed()      -- Tempo aus dem Test-Fenster (Dauer der Versteigerungen)
	-- Vergaben mitschreiben (egal ob du oder der automatische Durchlauf "Vergeben" klickt)
	local origAward = RM.Auction.Award
	run.origAward = origAward
	RM.Auction.Award = function(...)
		local c = RM.Auction.current
		if run and c and c.highName then
			run.awarded[#run.awarded + 1] = c.highName .. " " .. c.link .. " (" .. c.high .. " DKP)"
			Log("Vergeben: " .. c.link .. " an " .. c.highName .. " für " .. c.high .. " DKP")
		end
		return origAward(...)
	end
	RM.db.config.activePool = def.key
	if not RM.db.session.active then
		T.manualStart = true
		local ok, err = pcall(RM.Raid.Start)
		T.manualStart = nil
		if not ok then Log("Fehler beim Raidstart: " .. tostring(err)) end
	end
	Log("Raid-Durchlauf gestartet: " .. def.name .. " (" .. #def.bosses .. " Bosse)" ..
		(loot and ", Beute aus der Beutetabelle" or ", keine Beutetabelle für diesen Raid (nur Classic/TBC/Wrath)") ..
		". Versteigerungen laufen je " .. T.AuctionSec() .. " Sek.")
	run.ticker = C_Timer.NewTicker(0.5, RunStep)
	if T.Refresh then T.Refresh() end
end

---------------------------------------------------------------------------
-- Stresstest: 3–10 Wochen (zufällig) hintereinander, alles automatisch, ohne Abfragen
---------------------------------------------------------------------------
function T.StressTest(weeks)
	if T.IsRunning() then Log("Es läuft schon ein Durchlauf.") return end
	if not T.active then T.Start() end
	if not NeedRoster() then return end
	T.SetRole("raidlead")
	local n = tonumber(weeks) or math.random(3, 10)
	local diagErrors = RM.Diag and #RM.Diag.errors or 0
	T.stress = { weeks = n, t0 = GetTime(), oldAuto = T.autoAuction, oldWeekly = T.weekly,
		errors = diagErrors, items = 0, other = 0, bosses = 0 }
	T.autoAuction = true
	T.weekly = true
	if RM.Auction.HideAward then RM.Auction.HideAward() end
	Log(string.format("Stresstest: %d Wochen (%s) werden automatisch durchgespielt – ohne Abfragen.", n, RM.DKP.PoolName(T.pool)))
	T.RunRaids(n)
end

function T.FinishStress(aborted)
	local st = T.stress
	if not st then return end
	T.stress = nil
	T.autoAuction = st.oldAuto
	T.weekly = st.oldWeekly
	local neg, total, players = 0, 0, 0
	for _, p in pairs(RM.db.data.players) do
		local v = p.d and p.d[T.pool] or 0
		players = players + 1
		total = total + v
		if v < 0 then neg = neg + 1 end
	end
	local errs = (RM.Diag and #RM.Diag.errors or 0) - st.errors
	Log(string.format("Stresstest %s: %d Wochen, %d Bosse, %d Items versteigert, %d nach Regel verteilt, %.0f Sek.",
		aborted and "abgebrochen" or "fertig", st.weeks, st.bosses, st.items, st.other, GetTime() - st.t0))
	Log(string.format("  DKP %s: %d Spieler, gesamt %d, negativ: %d · neue Fehler: %d%s", RM.DKP.PoolName(T.pool), players, total, neg,
		math.max(0, errs), (errs > 0) and " – siehe Diagnose" or " – alles in Ordnung"))
end

function T.StopRun()
	T.series = nil
	T.SetTimeOffset(0)
	if T.stress then T.FinishStress(true) end
	if not run then return end
	run.ticker:Cancel()
	if run.origAward then RM.Auction.Award = run.origAward end
	RM.Loot.isOpen = false; wipe(RM.Loot.items)
	if RM.Auction.current then pcall(RM.Auction.Cancel) end
	wipe(RM.Auction.queue)
	RM.Fire("AUCTION_CHANGED")
	if RM.Auction.HideAward then RM.Auction.HideAward() end
	run = nil
	Log("Raid-Durchlauf abgebrochen.")
end

function T.TrashLoot()
	if not T.active then T.Start() end
	local loot = LootTable(RM.Data.Pools[T.pool])
	if not (loot and loot.trash and loot.trash[1]) then Log("Keine Trash-Beute für diesen Raid bekannt (nur Classic/TBC/Wrath).") return end
	for _, id in ipairs(loot.trash) do ItemInfo(id) end
	local picked = Pick(loot.trash, 1)
	if not picked[1] then Log("Items werden noch vom Server geladen – gleich nochmal klicken.") return end
	local own = not run
	if own then run = { queue = {}, awarded = {}, other = 0 } end
	HandleItem(picked[1], "Trash")
	if own then
		run = nil
		-- ohne Raid-Durchlauf: Item steht in der Warteschlange; gleich versteigern, falls nichts läuft
		if StartFromQueue() then Log("Versteigerung gestartet – Testspieler bieten gleich.") end
	end
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
	line(nil, "Deine Rechte: " .. (edit and "volle Rechte (DKP ändern, versteigern)" or "keine Raidleiter-Rechte"))
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

-- kurzer Stand des Durchlaufs für die Startseite
function T.RunStatus()
	if not T.active then return "|cff999999Testmodus aus – oben \"Testmodus starten\" klicken.|r" end
	local A = RM.Auction
	local parts = {}
	local n = T.roster and 0 or #FAKE
	for _, m in ipairs(T.roster or {}) do if m.online ~= false then n = n + 1 end end
	parts[#parts + 1] = n == 0 and "|cffffaa33Raid leer (nur du)|r" or string.format("Raid: %d Spieler", n + 1)
	if T.stress then parts[#parts + 1] = string.format("|cffff8c1aStresstest läuft|r (%d Wochen)", T.stress.weeks) end
	if T.series and T.series.total > 1 then
		parts[#parts + 1] = string.format("Raidabend %d von %d", T.series.total - T.series.left, T.series.total)
	end
	if run then
		parts[#parts + 1] = string.format("%s – Boss %d von %d", run.def and run.def.name or "?", run.index or 0, run.def and #run.def.bosses or 0)
		if A.current and A.AwaitingAward() then parts[#parts + 1] = "|cffffaa33wartet auf \"Vergeben\"|r"
		elseif A.current then parts[#parts + 1] = "Versteigerung läuft"
		elseif #A.queue > 0 and not T.autoAuction then parts[#parts + 1] = "|cffffaa33" .. #A.queue .. " Item(s) warten – Versteigerung in RaidMaster starten|r" end
	elseif RM.db.session.active then
		parts[#parts + 1] = "Raid-Sitzung läuft (" .. RM.DKP.PoolName(RM.db.session.pool or T.pool) .. ")"
	else
		parts[#parts + 1] = "bereit"
	end
	return table.concat(parts, " · ")
end

local function CreateWindow()
	local W = 560
	local f = UI.Frame(UIParent, W, 740)
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

	-- Kopf: Testmodus, Ansicht, Raid
	f.status = UI.Text(f, "", 12)
	f.status:SetPoint("TOPLEFT", 14, -38)
	f.status:SetWidth(W - 28)
	local toggle = UI.Button(f, "", 300, 30, function() if T.active then T.StopAsk() else T.Start() end end,
		"Testmodus: Daten werden gesichert und beim Beenden wiederhergestellt.\nKeine Nachrichten an Gilde oder Raid.")
	toggle:SetPoint("TOPLEFT", 14, -60)
	local openBtn = UI.Button(f, "RaidMaster öffnen", 218, 30, function() RM.UI.Open() end)
	openBtn:SetPoint("LEFT", toggle, "RIGHT", 14, 0)

	local roleLabel = UI.Text(f, "Ansicht als:", 12, unpack(COLORS.muted))
	roleLabel:SetPoint("TOPLEFT", 14, -104)
	local roleBtns = {}
	local x = 100
	for _, role in ipairs({ "member", "lead", "looter", "raidlead" }) do
		local b = UI.Button(f, ROLE_NAMES[role], 108, 24, function() T.SetRole(role) end,
			role == "member" and "Raidmitglied: sieht nur DKP-Stände und Versteigerung (bieten), keine Rechte." or
			role == "lead" and "Assistent: Raid-Seiten und Symbolleiste (z. B. Mobs markieren), kein DKP ändern." or
			role == "looter" and "Plündermeister (nicht Raidleiter): sieht nur DKP, Versteigerung und Loot,\nstartet und vergibt die Versteigerungen." or
			"Raidleiter: alle Rechte – Raid starten/beenden, Plündermeister, DKP, Versteigerung, Einstellungen.")
		b:SetPoint("TOPLEFT", x, -98)
		roleBtns[role] = b
		x = x + 112
	end

	local raidLabel = UI.Text(f, "Raid:", 12, unpack(COLORS.muted))
	raidLabel:SetPoint("TOPLEFT", 14, -138)
	T.pool = RM.DKP.ActivePool()
	local raidDrop = UI.Dropdown(f, 230, function() return UI.PoolGroups(RM.db.data) end, function() return T.pool end, function(v)
		T.pool = v
		local def = RM.Data.Pools[v]
		T.boss = def and def.bossIDs and def.bossIDs[1]
		T.Refresh()
	end, "Raid für den Test")
	raidDrop:SetPoint("TOPLEFT", 100, -132)
	local def0 = RM.Data.Pools[T.pool]
	T.boss = def0 and def0.bossIDs and def0.bossIDs[1]

	-- Reiter
	local TABS = {
		{ key = "start", name = "Schnellstart" },
		{ key = "single", name = "Einzeln testen" },
		{ key = "say", name = "Ansagen" },
		{ key = "options", name = "Einstellungen" },
		{ key = "log", name = "Protokoll" },
	}
	local tabBtns, panes = {}, {}
	T.tab = T.tab or "start"
	for i, t in ipairs(TABS) do
		local b = UI.Button(f, t.name, 128, 26, function() T.tab = t.key; T.Refresh() end)
		b:SetWidth(102)
		b:SetPoint("TOPLEFT", 14 + (i - 1) * 107, -172)
		tabBtns[t.key] = b
		local p = CreateFrame("Frame", nil, f)
		p:SetPoint("TOPLEFT", 0, -206)
		p:SetPoint("BOTTOMRIGHT", 0, 0)
		p:Hide()
		panes[t.key] = p
	end
	local line = f:CreateTexture(nil, "ARTWORK")
	line:SetPoint("TOPLEFT", 14, -201)
	line:SetPoint("TOPRIGHT", -14, -201)
	line:SetHeight(1)
	line:SetColorTexture(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 0.5)

	local function Desc(parent, text, anchor)
		local d = UI.Text(parent, text, 11, unpack(COLORS.muted))
		d:SetPoint("TOPLEFT", anchor, "BOTTOMLEFT", 2, -4)
		d:SetWidth(W - 40)
		d:SetJustifyH("LEFT")
		return d
	end

	-------------------------------------------------------------------
	-- Reiter Schnellstart: die drei Hauptaktionen groß und erklärt
	-------------------------------------------------------------------
	local ps = panes.start
	f.runStatus = UI.Text(ps, "", 12)
	f.runStatus:SetPoint("TOPLEFT", 14, -8)
	f.runStatus:SetWidth(W - 28)
	f.runStatus:SetJustifyH("LEFT")

	-- Raid füllen / leeren: der Testraid startet leer, gefüllt wird nur auf Wunsch
	local fillBtn = UI.Button(ps, "Raid füllen (39 Testspieler)", 300, 30, function()
		if T.RosterEmpty() then T.FillRoster() else T.ClearRoster() end
	end)
	fillBtn:SetPoint("TOPLEFT", 14, -34)
	f.fillBtn = fillBtn
	local d0 = Desc(ps, "Der Testraid startet leer. Füllen nur auf Wunsch – mit den 39 Testspielern oder in RaidMaster\n"
		.. "über Anmeldungen > Einladen (simuliert). Nochmal klicken leert den Raid wieder.", fillBtn)

	local runBtn = UI.Button(ps, "Ganzen Raid durchspielen", 300, 34, function() T.RunRaids(T.runs) end)
	runBtn:SetPoint("TOPLEFT", d0, "BOTTOMLEFT", -2, -14)
	runBtn:SetAccent(true)
	local runsLabel = UI.Text(ps, "Raidabende:", 12)
	runsLabel:SetPoint("LEFT", runBtn, "RIGHT", 16, 0)
	local runsBox = UI.EditBox(ps, 44, 26)
	runsBox:SetPoint("LEFT", runsLabel, "RIGHT", 8, 0)
	runsBox:SetText(tostring(T.runs or 1))
	runsBox:SetScript("OnTextChanged", function(self, user)
		if user then T.runs = math.max(1, math.min(10, math.floor(tonumber(self:GetText()) or 1))) end
	end)
	runsBox:SetScript("OnEnterPressed", function(self) self:ClearFocus(); self:SetText(tostring(T.runs)) end)
	local d1 = Desc(ps, "Alle Bosse des gewählten Raids: Bosskill, Beute, Testgebote. Du startest die Versteigerungen in RaidMaster selbst\n"
		.. "(oder unter Einstellungen \"Automatisch versteigern\"). Tipp: \"Raid starten\" in RaidMaster macht dasselbe.", runBtn)

	local stressBtn = UI.Button(ps, "Stresstest (3–10 Wochen)", 300, 34, function() T.StressTest() end)
	stressBtn:SetPoint("TOPLEFT", d1, "BOTTOMLEFT", -2, -14)
	stressBtn:SetAccent(true)
	local d2 = Desc(ps, "Zufällig 3 bis 10 Wochen am Stück, alles automatisch und ohne Abfragen (ca. 1,5 Min. pro Woche).\n"
		.. "Am Ende: Zusammenfassung im Protokoll, Ergebnis geht an Discord (DKP- und Loot-Kanal).", stressBtn)

	local sendBtn = UI.Button(ps, "Ergebnis jetzt an Discord senden", 300, 30, function() T.SendToDiscord() end)
	sendBtn:SetPoint("TOPLEFT", d2, "BOTTOMLEFT", -2, -14)
	local d3 = Desc(ps, "Lädt die Oberfläche neu, der Uploader schickt die Daten, der Bot postet mit TEST markiert (nach 10 Min. gelöscht).", sendBtn)

	local stopRunBtn = UI.Button(ps, "Durchlauf abbrechen", 300, 30, function() T.StopRun() end)
	stopRunBtn:SetPoint("TOPLEFT", d3, "BOTTOMLEFT", -2, -14)

	local lastHead = UI.Text(ps, "Letzte Meldungen", 12, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
	lastHead:SetPoint("TOPLEFT", stopRunBtn, "BOTTOMLEFT", 0, -16)
	f.lastLog = UI.Text(ps, "", 11)
	f.lastLog:SetPoint("TOPLEFT", lastHead, "BOTTOMLEFT", 0, -4)
	f.lastLog:SetWidth(W - 28)
	f.lastLog:SetJustifyH("LEFT")

	-------------------------------------------------------------------
	-- Reiter Einzeln testen
	-------------------------------------------------------------------
	local pe = panes.single
	Section(pe, "Raid", -4)
	local bossDrop = UI.Dropdown(pe, 230, function()
		local def = RM.Data.Pools[T.pool]
		local items = {}
		for _, id in ipairs(def and def.bossIDs or {}) do items[#items + 1] = { id, RM.Data.Bosses[id].name } end
		return { { items = items } }
	end, function() return T.boss end, function(v) T.boss = v end, "Boss für den Bosskill")
	bossDrop:SetPoint("TOPLEFT", 14, -28)
	local startBtn = UI.Button(pe, "Raid starten", 126, 26, function() T.StartRaid() end, "Startet nur die Raid-Sitzung (Pünktlichkeitsbonus, Ersatzbank).")
	startBtn:SetPoint("TOPLEFT", 14, -60)
	local killBtn = UI.Button(pe, "Bosskill", 126, 26, function() T.BossKill() end,
		"Spielt Bosskampf-Beginn und -Ende vor: Boss-DKP, Erstkill, automatische Markierungsvorlage.")
	killBtn:SetPoint("LEFT", startBtn, "RIGHT", 8, 0)
	killBtn:SetAccent(true)
	local endBtn = UI.Button(pe, "Raid beenden", 126, 26, function() T.EndRaid() end, "Beendet die Sitzung mit Abschlussbonus.")
	endBtn:SetPoint("LEFT", killBtn, "RIGHT", 8, 0)
	local trashBtn = UI.Button(pe, "Trash-Loot", 126, 26, function() T.TrashLoot() end, "Ein zufälliges Trash-Item des Raids droppen lassen.")
	trashBtn:SetPoint("TOPLEFT", 14, -92)
	local tqBtn = UI.Button(pe, "Jäger-Abfrage", 126, 26, function() T.TranqTest() end,
		"Magmadar: fragt die Jäger nach Einlullender Schuss und postet die Rotation (Testjäger antworten selbst).")
	tqBtn:SetPoint("LEFT", trashBtn, "RIGHT", 8, 0)
	local targetBtn = UI.Button(pe, "Boss ins Ziel", 126, 26, function() T.TargetBoss(T.boss) end,
		"Simuliert, dass du den gewählten Boss ins Ziel nimmst: die Boss-Leiste erscheint\n(Ansage + Symbole per Klick, nur bei dir angezeigt).")
	targetBtn:SetPoint("LEFT", tqBtn, "RIGHT", 8, 0)
	targetBtn:SetAccent(true)
	local untargetBtn = UI.Button(pe, "Ziel löschen", 110, 26, function() T.TargetBoss(nil) end)
	untargetBtn:SetPoint("LEFT", bossDrop, "RIGHT", 8, 0)
	local rosterBtn = UI.Button(pe, "Raid füllen", 110, 26, function() T.FillRoster() end,
		"Testraid mit den 39 Testspielern füllen (MC-Aufstellung). Ohne diesen Klick bleibt der Testraid leer.")
	rosterBtn:SetPoint("LEFT", untargetBtn, "RIGHT", 8, 0)

	Section(pe, "Versteigerung", -132)
	local itemBox = UI.LinkBox(pe, 300, 26)
	itemBox:SetPoint("TOPLEFT", 14, -156)
	local hint = UI.Text(itemBox, "Item per Shift-Klick (leer = Ruhestein)", 11, unpack(COLORS.muted))
	hint:SetPoint("LEFT", 8, 0)
	itemBox:HookScript("OnTextChanged", function(self) if self:GetText() == "" then hint:Show() else hint:Hide() end end)
	itemBox:HookScript("OnEditFocusGained", function() hint:Hide() end)
	local aucBtn = UI.Button(pe, "Mit Testgeboten versteigern", 210, 26, function() T.Auction(itemBox:GetText()) end,
		"Startet eine Versteigerung; 4 Testspieler bieten nacheinander.")
	aucBtn:SetPoint("LEFT", itemBox, "RIGHT", 8, 0)
	local dkpBox = UI.EditBox(pe, 100, 26)
	dkpBox:SetPoint("TOPLEFT", 14, -190)
	dkpBox:SetText("1000")
	dkpBox:SetScript("OnEnterPressed", function(self) T.GiveMeDKP(self:GetText()); self:ClearFocus() end)
	local dkpBtn = UI.Button(pe, "DKP an mich (gewählter Raid)", 220, 26, function() T.GiveMeDKP(dkpBox:GetText()) end,
		"Bucht dir beliebig viele DKP im gewählten Raid (negativ = abziehen). Nur im Testmodus.")
	dkpBtn:SetPoint("LEFT", dkpBox, "RIGHT", 8, 0)

	Section(pe, "Schlachtzugsymbole (echt, z. B. an Trainingspuppen)", -232)
	local m1 = UI.Button(pe, "Totenkopf aufs Ziel", 160, 26, function() RM.Markers.Mark(8) end)
	m1:SetPoint("TOPLEFT", 14, -256)
	local m2 = UI.Button(pe, "Adds markieren", 160, 26, function() RM.Markers.MarkAdds() end, "Markiert alle sichtbaren Gegner nach der gewählten Vorlage.")
	m2:SetPoint("LEFT", m1, "RIGHT", 8, 0)
	local m3 = UI.Button(pe, "Alle aus", 120, 26, function() RM.Markers.ClearAll() end)
	m3:SetPoint("LEFT", m2, "RIGHT", 8, 0)

	-------------------------------------------------------------------
	-- Reiter Einstellungen
	-------------------------------------------------------------------
	-------------------------------------------------------------------
	-- Reiter Ansagen: Ansagen und Mini-Leisten ausprobieren
	-------------------------------------------------------------------
	local pa = panes.say
	local intro = UI.Text(pa, "Alles wie im echten Raid – nur bei dir sichtbar (Chat mit [Test], Schlachtzugwarnung in der Bildschirmmitte).\n"
		.. "Boss: den Raid oben wählen, den Boss im Reiter \"Einzeln testen\".", 11, unpack(COLORS.muted))
	intro:SetPoint("TOPLEFT", 14, -6)
	intro:SetWidth(W - 28)
	intro:SetJustifyH("LEFT")
	local SAY = {
		{ "Boss-Leiste", T.TryBossBar, "Boss ins Ziel: die Leiste mit Ansage + Symbole, Pull, Pause, Bereitschaft erscheint." },
		{ "Markierungsleiste", T.TryMarkerBar, "Die kleine Leiste mit den Schlachtzugsymbolen einblenden." },
		{ "Boss-Ansage", T.TryBossInfo, "Taktik des Bosses als Schlachtzugwarnung (wie Knopf \"Ansage\")." },
		{ "Pull-Timer", T.TryPull, "Countdown mit 5-4-3-2-1 und PULL! (auch an DBM/BigWigs – im Test nicht gesendet)." },
		{ "Pause (1 Min.)", T.TryBreak, "Pausenfenster mit Countdown wie bei allen im Raid." },
		{ "Bereitschafts-Check", T.TryReady, "Die Testspieler antworten, danach erscheint die Liste." },
		{ "Begrüßung", T.TryWelcome, "Begrüßung beim Raidstart – mit Testgast und Spieler von der Ersatzbank." },
		{ "Erstkill-Feier", T.TryFirstKill, "Fanfare und Schlachtzugwarnung (im Test ohne Screenshot)." },
		{ "Neuer Rekord", T.TryRecord, "So sieht die Ansage bei einer neuen Bestzeit aus." },
		{ "Lücken füllen", function() NeedActive() RM.Gaps.Open() end, "Fenster mit Bedarf, Ersatzbank, Gilde und Gruppensuche." },
	}
	for i, x in ipairs(SAY) do
		local col, row = (i - 1) % 2, math.floor((i - 1) / 2)
		local b = UI.Button(pa, x[1], 160, 26, x[2], x[3])
		b:SetPoint("TOPLEFT", 14 + col * 270, -48 - row * 58)
		local d = UI.Text(pa, x[3], 10, unpack(COLORS.muted))
		d:SetPoint("TOPLEFT", b, "BOTTOMLEFT", 2, -2)
		d:SetWidth(255)
		d:SetJustifyH("LEFT")
	end
	local chatHead = UI.Text(pa, "Zuletzt angesagt (Test)", 12, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
	chatHead:SetPoint("TOPLEFT", 14, -48 - 5 * 58 - 6)
	f.chatLog = UI.Text(pa, "", 11)
	f.chatLog:SetPoint("TOPLEFT", chatHead, "BOTTOMLEFT", 0, -4)
	f.chatLog:SetWidth(W - 28)
	f.chatLog:SetJustifyH("LEFT")

	local po = panes.options
	local checks = {}
	local oy = -8
	local function Opt(label, getter, setter, tip)
		local c = UI.Check(po, label, getter, setter, tip)
		c:SetPoint("TOPLEFT", 14, oy)
		checks[#checks + 1] = c
		oy = oy - 30
		return c
	end
	Opt("Items automatisch vergeben (keine \"Vergeben\"-Abfrage)", function() return T.AutoAwardOn() end, function(v) T.SetAutoAward(v) end,
		"An (Standard): jedes versteigerte Item geht sofort an den Höchstbieter. Aus: du klickst \"Vergeben\" wie im echten Raid.")
	Opt("Automatisch versteigern (Durchlauf ohne Klicken)", function() return T.autoAuction end, function(v) T.autoAuction = v end,
		"Aus (Standard): die Beute liegt in der Warteschlange, du startest jede Versteigerung in RaidMaster selbst.\nAn: der Durchlauf versteigert alles von selbst.")
	Opt("Raidabende je eine Woche auseinander datieren", function() return T.weekly end, function(v) T.weekly = v end,
		"Die Raidabende bekommen Daten im Wochenabstand (der letzte heute) – wie nach mehreren Wochen im Discord.")
	Opt("Ergebnis nach dem Raid automatisch an Discord senden", function() return T.AutoSendOn() end,
		function(v)
			T.SetAutoSend(v)
			if T.active and RM.db.testMode then RM.db.testMode.post = v or nil end
		end,
		"Nach \"Raid beenden\" bzw. am Ende des Durchlaufs wird das Ergebnis nach 10 Sek. gesendet (lädt die Oberfläche neu).")
	Opt("\"Raid starten\" in RaidMaster spielt den ganzen Raid durch", function() return T.FollowStartOn() end, function(v) T.SetFollowStart(v) end,
		"Startest du im Testmodus den Raid in RaidMaster, startet das Test-Tool den Durchlauf für diesen Raid.")
	local speedLabel = UI.Text(po, "Dauer je Versteigerung im Test:", 12)
	speedLabel:SetPoint("TOPLEFT", 16, oy - 6)
	local speedOpts = {}
	for _, v in ipairs(T.SPEEDS) do speedOpts[#speedOpts + 1] = { v, v .. " Sek." } end
	local speed = UI.Cycle(po, 100, speedOpts, function() return T.AuctionSec() end, function(v) T.SetAuctionSec(v) end,
		"Klick = nächster Wert. Haben alle Testspieler geboten, läuft die Restzeit nur noch 1 Sek. Nur im Testmodus.")
	speed:SetPoint("TOPLEFT", 240, oy)

	-------------------------------------------------------------------
	-- Reiter Protokoll
	-------------------------------------------------------------------
	local pl = panes.log
	local selfBtn = UI.Button(pl, "Selbsttest", 120, 26, function() T.SelfTest() end, "Prüft Spielversion, Daten, Rechte und Einstellungen.")
	selfBtn:SetPoint("TOPLEFT", 14, -4)
	local diagBtn = UI.Button(pl, "Diagnose", 120, 26, function() if RM.Diag then RM.Diag.Toggle() end end,
		"Zeigt Fehler und Hänger von RaidMaster und vom Test-Durchlauf und kann sie lösen.")
	diagBtn:SetPoint("LEFT", selfBtn, "RIGHT", 8, 0)
	local box = UI.Multiline(pl, W - 28, 380, true)
	box:SetPoint("TOPLEFT", 14, -38)

	function T.Refresh()
		if not f:IsShown() then return end
		f.status:SetText(T.active and ("|cffff8c1aTestmodus AN|r – Ansicht als |cffffffff" .. ROLE_NAMES[T.role] .. "|r. Deine echten Daten sind gesichert.")
			or "|cff999999Testmodus aus.|r Starte ihn, um gefahrlos zu testen – beim Beenden wird alles zurückgesetzt.")
		toggle:SetText(T.active and "Testmodus beenden (alles zurücksetzen)" or "Testmodus starten")
		toggle:SetAccent(not T.active)
		for role, b in pairs(roleBtns) do b:SetAccent(T.active and T.role == role) end
		raidDrop:Refresh(); bossDrop:Refresh()
		for _, c in ipairs(checks) do c:Refresh() end
		local cur = panes[T.tab] and T.tab or "start"
		for key, p in pairs(panes) do
			if key == cur then p:Show() else p:Hide() end
			tabBtns[key]:SetAccent(key == cur)
		end
		f.runStatus:SetText("Stand: " .. T.RunStatus())
		local said = {}
		for i = 1, math.min(8, #(T.lastChat or {})) do said[#said + 1] = T.lastChat[i] end
		f.chatLog:SetText(#said > 0 and table.concat(said, "\n") or "|cff999999Noch nichts angesagt.|r")
		f.fillBtn:SetText(T.RosterEmpty() and "Raid füllen (39 Testspieler)" or "Raid leeren")
		f.fillBtn:SetAccent(T.active and T.RosterEmpty())
		local last = {}
		for i = 1, math.min(6, #T.log) do last[#last + 1] = T.log[i] end
		f.lastLog:SetText(table.concat(last, "\n"))
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
function T.Slash(msg)
	msg = (msg or ""):lower()
	if msg == "start" then T.Start()
	elseif msg == "stop" or msg == "ende" then T.StopAsk()
	elseif msg == "check" or msg == "selbsttest" then T.SelfTest(); if not (win and win:IsShown()) then print((T.selfTest or ""):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")) end
	else T.Toggle() end
end
SlashCmdList["RAIDMASTERTEST"] = T.Slash

-- Diagnose von RaidMaster: Zustand des Test-Durchlaufs anzeigen und Hänger lösen
if RM.Diag then
	table.insert(RM.Diag.providers, function()
		local lines = { "|cffffd200Test-Tool|r" }
		lines[#lines + 1] = "  Testmodus: " .. (T.active and ("an, Ansicht als " .. ROLE_NAMES[T.role]) or "aus")
		if run then
			local A = RM.Auction
			local why
			if A.current and A.AwaitingAward() then why = "wartet auf DICH: Vergeben / Nicht vergeben / Neu versteigern"
			elseif A.current then why = "Versteigerung läuft"
			elseif #A.queue > 0 then why = (T.autoAuction and "startet gleich die nächste Versteigerung" or ("wartet auf DICH: " .. #A.queue .. " Item(s) in der Warteschlange – Seite Versteigerung, \"Gewähltes starten\""))
			else why = "nächster Boss kommt gleich" end
			lines[#lines + 1] = string.format("  Durchlauf: %s, Boss %d von %d – %s", run.def and run.def.name or "?", run.index or 0, run.def and #run.def.bosses or 0, why)
			if T.series then lines[#lines + 1] = string.format("  Raidabend %d von %d", T.series.total - T.series.left, T.series.total) end
		else
			lines[#lines + 1] = "  Kein Durchlauf aktiv."
		end
		return lines
	end)
	table.insert(RM.Diag.fixers, function()
		if run then
			run.told = false
			run.waitUntil = math.min(run.waitUntil or 0, GetTime())
			if run.ticker == nil or (run.ticker.IsCancelled and run.ticker:IsCancelled()) then
				run.ticker = C_Timer.NewTicker(0.5, RunStep)
				return { "Test-Durchlauf neu angestoßen." }
			end
		end
	end)
end

-- Früher gab es das Test-Tool als eigenes Addon "RaidMasterTest" – das alte wird abgeschaltet
do
	RM.On("PLAYER_LOGIN", function()
		local loaded = (C_AddOns and C_AddOns.IsAddOnLoaded and C_AddOns.IsAddOnLoaded("RaidMasterTest"))
			or (IsAddOnLoaded and IsAddOnLoaded("RaidMasterTest"))
		if loaded or (RaidMasterTest and RaidMasterTest ~= T) then
			-- das alte Addon hat sich beim Laden über das eingebaute gelegt: stoppen und stilllegen
			local old = RaidMasterTest
			if old and old ~= T then
				if old.active and old.Stop then pcall(old.Stop) end
				for k, v in pairs(old) do
					if type(v) == "function" then
						old[k] = function() print("|cffff8c1a[RaidMaster]|r Altes RaidMasterTest ist abgeschaltet – bitte /reload.") end
					end
				end
				old.active = false
				RaidMasterTest = T
			end
			SlashCmdList["RAIDMASTERTEST"] = T.Slash
			-- falls das alte Addon RaidMaster-Funktionen umgebogen hat: echte wiederherstellen
			if not T.active and REAL.captured then
				for _, k in ipairs(OVERRIDE) do RM[k] = REAL[k] end
			end
			RM.Fire("CONFIG_CHANGED"); RM.Fire("SESSION_CHANGED")
			local disable = (C_AddOns and C_AddOns.DisableAddOn) or DisableAddOn
			if disable then pcall(disable, "RaidMasterTest") end
			print("|cffff8c1a[RaidMaster]|r Das Test-Tool ist jetzt in RaidMaster eingebaut. Das alte Addon \"RaidMasterTest\" "
				.. "wurde abgeschaltet – bitte einmal /reload und den Ordner Interface\\AddOns\\RaidMasterTest löschen.")
		end
	end)
end
