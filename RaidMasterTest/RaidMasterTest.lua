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
local ROLE_NAMES = { member = "Teilnehmer", lead = "Co-Raidleiter", raidlead = "Raidleiter", officer = "Offizier" }

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
local OVERRIDE = { "InRaid", "RaidMembers", "IsAssist", "IsLeader", "CanEdit", "SendAddonMessage", "RaidChat", "Announce", "Whisper", "IAmMasterLooter", "MasterLooterName" }

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
	saved.Ensure = RM.Loot and RM.Loot.EnsureSettings
	saved.Warn = RM.Loot and RM.Loot.Warn
	saved.CheckMainLeader = RM.CheckMainLeader
	-- im Testraid nichts an der echten Gruppe ändern (Plündermethode, Raidleiter)
	if RM.Loot and RM.Loot.EnsureSettings then RM.Loot.EnsureSettings = function() end end
	if RM.Loot and RM.Loot.Warn then RM.Loot.Warn = function() end end
	if RM.CheckMainLeader then RM.CheckMainLeader = function() end end
	RM.InRaid = function() return true end
	RM.RaidMembers = FakeMembers
	-- Rollen: Teilnehmer (nur bieten), Co-Raidleiter (Assistent), Raidleiter (Gruppenleiter mit allen Rechten),
	-- Offizier (alle Rechte)
	RM.IsAssist = function() return T.role ~= "member" end
	RM.IsLeader = function() return T.role == "raidlead" or T.role == "officer" end
	RM.CanEdit = function() return T.role == "officer" or T.role == "raidlead" end
	-- im Testraid bist du als Raidleiter/Offizier auch der Plündermeister (startet die Versteigerungen)
	RM.IAmMasterLooter = function() return T.role == "officer" or T.role == "raidlead" end
	RM.MasterLooterName = function() return RM.Me() end
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
	-- Markierung für den Discord-Bot: Daten aus dem Testmodus nie als echte DKP übernehmen
	RM.db.testMode = { active = true, started = GetServerTime(), pool = T.pool }
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
		local size = RM.db.config and RM.db.config.mainSize
		Replace(RM.db.data, b.data)
		Replace(RM.db.session, b.session)
		Replace(RM.db.trade, b.trade)
		Replace(RM.db.config, b.config)
		if pos then RM.db.config.positions = pos end
		RM.db.config.mainSize = size
	end
	if RM.db then RM.db.testMode = nil end
	RaidMasterTestDB = nil
	if not silent then RM.Fire("SESSION_CHANGED"); RM.Fire("DATA_CHANGED"); RM.Fire("CONFIG_CHANGED") end
end

function T.Stop()
	if not T.active then return end
	if RM.Auction and RM.Auction.current then pcall(RM.Auction.Cancel) end
	for _, k in ipairs(OVERRIDE) do RM[k] = saved[k] end
	if RM.Auction and RM.Auction.queue then wipe(RM.Auction.queue) end   -- Test-Items nicht im echten Raid lassen
	if RM.Loot and saved.Deliver then RM.Loot.Deliver = saved.Deliver end
	if RM.Loot and saved.Ensure then RM.Loot.EnsureSettings = saved.Ensure end
	if RM.Loot and saved.Warn then RM.Loot.Warn = saved.Warn end
	if saved.CheckMainLeader then RM.CheckMainLeader = saved.CheckMainLeader end
	T.active = false
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
	if T.role ~= "officer" and T.role ~= "raidlead" then
		Log("Für Raid, Bosskill und Versteigerung bitte 'Ansicht als: Raidleiter' oder 'Offizier' wählen.")
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
-- Ganzen Raid durchspielen: alle Bosse nacheinander, Beute aus der echten Beutetabelle
-- (Classic, TBC, Wrath), Versteigerungen mit Testgeboten, Trash-Beute zwischendurch
---------------------------------------------------------------------------
local run
local CONFIRM = "RAIDMASTER_CONFIRM"

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
	for _, f in ipairs(FAKE) do bidders[#bidders + 1] = f[1] end
	local count = math.random(2, 4)
	local amount = c.min
	for i = 1, count do
		local who = table.remove(bidders, math.random(#bidders))
		amount = amount + math.random(0, 3) * (c.inc or 5)
		local a = amount
		C_Timer.After(1 + i * 1.5, function()
			if RM.Auction.current == c and not c.finished then
				local have = RM.DKP.Get(who, c.pool)
				local bid = math.min(a, have)
				if bid >= ((c.highName and (c.high + c.inc)) or c.min) then RM.Auction.ReceiveBid(who, bid, "") end
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
		if c.highName then
			StaticPopup_Hide(CONFIRM)
			local who, amount, link = c.highName, c.high, c.link
			RM.Auction.Award()
			run.awarded[#run.awarded + 1] = who .. " " .. link .. " (" .. amount .. " DKP)"
			Log("Vergeben: " .. link .. " an " .. who .. " für " .. amount .. " DKP")
		else
			RM.Auction.current = nil
		end
		run.waitUntil = now + 1.5
		return
	end
	-- läuft eine Versteigerung (auch automatisch gestartet), bieten die Testspieler mit
	if c then AddFakeBids(c) return end
	if #RM.Auction.queue > 0 then
		if not StartFromQueue() then Log("Versteigerung aus der Warteschlange nicht möglich."); wipe(RM.Auction.queue) end
		run.waitUntil = now + 1
		return
	end
	-- nächster Boss
	run.index = run.index + 1
	local boss = run.def.bosses[run.index]
	if not boss then
		RM.Raid.End()
		Log(string.format("Raid-Durchlauf fertig: %d Bosse, %d Items versteigert, %d nach Regel verteilt.", #run.def.bosses, #run.awarded, run.other))
		for _, a in ipairs(run.awarded) do Log("  " .. a) end
		Log("Alles im Testmodus – 'Testmodus beenden' setzt deine echten Daten zurück.")
		RM.db.data.settings.auctionTime = run.oldTime
		run.ticker:Cancel()
		run = nil
		if T.Refresh then T.Refresh() end
		return
	end
	-- Trash vor jedem zweiten Boss
	if run.loot and run.index > 1 and run.index % 2 == 0 and run.loot.trash then
		for _, id in ipairs(Pick(run.loot.trash, 1)) do HandleItem(id, "Trash") end
	end
	local ids = boss.e
	RM.SimulateEvent("ENCOUNTER_START", ids[#ids], boss.name, 9, 40)
	RM.SimulateEvent("ENCOUNTER_END", ids[#ids], boss.name, 9, 40, 1)
	Log(string.format("Boss %d/%d besiegt: %s", run.index, #run.def.bosses, boss.name))
	if run.loot then
		local drops = BossLoot(run.loot, boss, run.index)
		local n = (#run.def.bosses == 1 or run.index == #run.def.bosses) and 3 or 2
		local picked = Pick(drops, n)
		if #picked == 0 then Log("  (keine Beute bekannt oder noch nicht vom Server geladen)") end
		for _, id in ipairs(picked) do HandleItem(id, boss.name) end
	end
	run.waitUntil = now + 2
end

function T.RunRaid()
	if run then Log("Es läuft schon ein Durchlauf.") return end
	if not T.active then T.Start() end
	if T.role ~= "officer" and T.role ~= "raidlead" then T.SetRole("raidlead") end
	local def = RM.Data.Pools[T.pool]
	if not def or not def.bosses[1] then Log("Für diesen Raid sind keine Bosse hinterlegt.") return end
	local loot = LootTable(def)
	-- Items beim Server anfragen, damit Namen/Qualität bereitstehen
	if loot then
		for _, b in ipairs(loot) do for _, id in ipairs(b.i) do ItemInfo(id) end end
		for _, id in ipairs(loot.trash or {}) do ItemInfo(id) end
	end
	run = { def = def, loot = loot, index = 0, queue = {}, awarded = {}, other = 0, waitUntil = GetTime() + 2,
		oldTime = RM.db.data.settings.auctionTime }
	RM.db.data.settings.auctionTime = 10      -- im Test schneller versteigern
	RM.db.config.activePool = def.key
	if not RM.db.session.active then RM.Raid.Start() end
	Log("Raid-Durchlauf gestartet: " .. def.name .. " (" .. #def.bosses .. " Bosse)" ..
		(loot and ", Beute aus der Beutetabelle" or ", keine Beutetabelle für diesen Raid (nur Classic/TBC/Wrath)") ..
		". Versteigerungen laufen je 10 Sek.")
	run.ticker = C_Timer.NewTicker(0.5, RunStep)
	if T.Refresh then T.Refresh() end
end

function T.StopRun()
	if not run then return end
	run.ticker:Cancel()
	if RM.Auction.current then pcall(RM.Auction.Cancel) end
	wipe(RM.Auction.queue)
	RM.Fire("AUCTION_CHANGED")
	StaticPopup_Hide(CONFIRM)
	RM.db.data.settings.auctionTime = run.oldTime
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
	local f = UI.Frame(UIParent, 560, 724)
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
	for _, role in ipairs({ "member", "lead", "raidlead", "officer" }) do
		local b = UI.Button(f, ROLE_NAMES[role], 126, 26, function() T.SetRole(role) end,
			role == "member" and "Sieht nur DKP-Stände und Versteigerung, keine Symbolleiste." or
			role == "lead" and "Co-Raidleiter (Assistent): Raid-Seiten und Symbolleiste, kein DKP ändern." or
			role == "raidlead" and "Raidleiter des Raids: alle Raid-Seiten, Symbolleiste, Plündermeister, DKP und Versteigerung." or
			"Offizier: alles, auch DKP, Versteigerung und Einstellungen.")
		b:SetPoint("TOPLEFT", x, -128)
		roleBtns[role] = b
		x = x + 133
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

	local runBtn = UI.Button(f, "Ganzen Raid durchspielen", 200, 26, function() T.RunRaid() end,
		"Alle Bosse des gewählten Raids nacheinander: Bosskill, Beute aus der echten Beutetabelle (Classic/TBC/Wrath),\n"
		.. "Regeln (Versteigerung, Gildenbank, Entzauberer ...), Versteigerungen mit Testgeboten, Trash-Beute zwischendurch.")
	runBtn:SetPoint("TOPLEFT", 14, -258)
	runBtn:SetAccent(true)
	local trashBtn = UI.Button(f, "Trash-Loot", 120, 26, function() T.TrashLoot() end, "Ein zufälliges Trash-Item des Raids droppen lassen.")
	trashBtn:SetPoint("LEFT", runBtn, "RIGHT", 8, 0)
	local stopRunBtn = UI.Button(f, "Durchlauf abbrechen", 160, 26, function() T.StopRun() end)
	stopRunBtn:SetPoint("LEFT", trashBtn, "RIGHT", 8, 0)

	Section(f, "Versteigerung", -298)
	local itemBox = UI.LinkBox(f, 300, 26)
	itemBox:SetPoint("TOPLEFT", 14, -322)
	local hint = UI.Text(itemBox, "Item per Shift-Klick (leer = Ruhestein)", 11, unpack(COLORS.muted))
	hint:SetPoint("LEFT", 8, 0)
	itemBox:HookScript("OnTextChanged", function(self) if self:GetText() == "" then hint:Show() else hint:Hide() end end)
	itemBox:HookScript("OnEditFocusGained", function() hint:Hide() end)
	local aucBtn = UI.Button(f, "Mit Testgeboten versteigern", 220, 26, function() T.Auction(itemBox:GetText()) end,
		"Startet eine Versteigerung; 4 Testspieler bieten nacheinander. Danach fragt RaidMaster wie im echten Raid, ob vergeben wird.")
	aucBtn:SetPoint("LEFT", itemBox, "RIGHT", 8, 0)
	local dkpBox = UI.EditBox(f, 120, 26)
	dkpBox:SetPoint("TOPLEFT", 14, -356)
	dkpBox:SetText("1000")
	dkpBox:SetScript("OnEnterPressed", function(self) T.GiveMeDKP(self:GetText()); self:ClearFocus() end)
	local dkpBtn = UI.Button(f, "DKP an mich (gewählter Raid)", 220, 26, function() T.GiveMeDKP(dkpBox:GetText()) end,
		"Bucht dir beliebig viele DKP im oben gewählten Raid (negativ = abziehen). Nur im Testmodus – wird beim Beenden zurückgesetzt.")
	dkpBtn:SetPoint("LEFT", dkpBox, "RIGHT", 8, 0)
	local discordBtn = UI.Button(f, "Test an Discord senden", 168, 26, function() T.SendToDiscord() end,
		"DKP-Stand, Teilnehmer und Loot dieses Tests im Discord posten (mit TEST markiert, nach 10 Minuten gelöscht).\n"
		.. "Lädt die Oberfläche neu – danach ist der Testmodus beendet. Der Uploader muss laufen.")
	discordBtn:SetPoint("LEFT", dkpBtn, "RIGHT", 8, 0)

	Section(f, "Schlachtzugsymbole (echt, z. B. an Trainingspuppen)", -398)
	local m1 = UI.Button(f, "Totenkopf aufs Ziel", 160, 26, function() RM.Markers.Mark(8) end)
	m1:SetPoint("TOPLEFT", 14, -422)
	local m2 = UI.Button(f, "Adds markieren", 160, 26, function() RM.Markers.MarkAdds() end, "Markiert alle sichtbaren Gegner nach der gewählten Vorlage.")
	m2:SetPoint("LEFT", m1, "RIGHT", 8, 0)
	local m3 = UI.Button(f, "Alle aus", 120, 26, function() RM.Markers.ClearAll() end)
	m3:SetPoint("LEFT", m2, "RIGHT", 8, 0)

	Section(f, "Protokoll", -464)
	local box = UI.Multiline(f, 532, 220, true)
	box:SetPoint("TOPLEFT", 14, -488)

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
