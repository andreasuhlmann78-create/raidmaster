-- RaidMaster - Raid
-- Raidstart/-ende, Bosskills, Raid-Check, Pausen-Timer, Kernhunde-Hilfe

local ADDON, RM = ...
local L = RM.L
local Raid = {}
RM.Raid = Raid

Raid.lastCheck = {}

local function S() return RM.db.data.settings end

---------------------------------------------------------------------------
-- Raidstart / Raidende
---------------------------------------------------------------------------
function Raid.IsActive()
	return RM.db.session.active
end

function Raid.Start()
	if not RM.CanEdit() then RM.Print(L["Nur Offiziere können einen Raid starten."]) return end
	if not RM.InRaid() then RM.Print(L["Du bist in keinem Schlachtzug."]) return end
	if RM.db.session.active then RM.Print(L["Der Raid läuft bereits."]) return end
	local pool = RM.DKP.CurrentInstancePool() or RM.db.config.activePool or "mc"
	RM.db.session = { active = true, started = GetServerTime(), kills = {}, pool = pool }
	if RM.db.config.setLootOnStart and RM.IsLeader() then
		RM.Loot.ApplySettings()
	end
	C_Timer.After(4, function() RM.Loot.Warn(true) end)
	local amount = S().dkpStart
	local poolName = RM.DKP.PoolName(pool)
	if amount and amount > 0 then
		RM.DKP.AwardRaid(amount, "start", L["Pünktlich zum Raidstart"], nil, pool)
		RM.Announce(string.format(L["[RaidMaster] Raid gestartet (%s) – +%d DKP für Pünktlichkeit. Viel Erfolg!"], poolName, amount), true)
	else
		RM.Announce(L["[RaidMaster] Raid gestartet ("] .. poolName .. L["). Viel Erfolg!"], true)
	end
	C_Timer.After(3, Raid.RunCheck)
	-- Stand an den Raid verteilen, damit gildenfremde Mitspieler ihn sehen
	C_Timer.After(6, function()
		if RM.InRaid() then RM.Comm.Send("SNAP", RM.DKP.MakeSnapshot(20), "RAID") end
	end)
	RM.Fire("SESSION_CHANGED")
end

function Raid.End()
	if not RM.db.session.active then RM.Print(L["Es läuft kein Raid."]) return end
	local amount = S().dkpEnd
	local pool = RM.db.session.lastPool or RM.db.session.pool or "mc"
	if amount and amount > 0 and RM.InRaid() then
		RM.DKP.AwardRaid(amount, "end", L["Raid bis zum Ende"], nil, pool)
		RM.Announce(string.format("[RaidMaster] Raid beendet (%s) – +%d DKP Abschlussbonus. Danke an alle!", RM.DKP.PoolName(pool), amount), true)
	else
		RM.Announce(L["[RaidMaster] Raid beendet. Danke an alle!"], true)
	end
	RM.db.session.active = false
	RM.db.session.ended = GetServerTime()
	RM.Fire("SESSION_CHANGED")
end

---------------------------------------------------------------------------
-- Bosskills
---------------------------------------------------------------------------
RM.On("ENCOUNTER_END", function(encounterID, encounterName, difficulty, groupSize, success)
	RM.Data.LearnBossName(encounterID, encounterName)
	if success ~= 1 and success ~= true then return end
	local boss = RM.Data.Bosses[encounterID]
	local bossName = boss and boss.name or encounterName or L["Boss"]
	RM.Loot.OnBossKilled(bossName)

	local session = RM.db.session
	if not session.active or not RM.CanEdit() then return end
	if session.kills[encounterID] then return end
	session.kills[encounterID] = GetServerTime()

	-- Topf: bekannter Boss -> sein Raid, sonst die aktuelle Instanz, sonst der Raidstart
	local pool = (boss and boss.pool) or RM.DKP.CurrentInstancePool() or session.pool or "mc"
	session.lastPool = pool
	session.names = session.names or {}
	session.names[encounterID] = bossName

	local s = S()
	local amount = s.bossDKP[boss and boss.id or encounterID] or s.bossDKP[encounterID] or (boss and boss.dkp) or s.defaultBossDKP or 0
	if amount <= 0 then RM.Fire("SESSION_CHANGED") return end
	local first = not RM.db.data.firstKills[encounterID]
	local text = bossName
	if first and s.firstKillDouble then
		amount = amount * 2
		text = bossName .. L[" (Erstkill)"]
	end
	RM.DKP.AwardRaid(amount, "boss", text, { b = encounterID, bn = bossName }, pool)
	RM.Announce(string.format(L["[RaidMaster] %s besiegt – +%d %s-DKP für den Raid%s."], bossName, amount, RM.DKP.PoolShort(pool),
		(first and s.firstKillDouble) and L[" (Erstkill doppelt)"] or ""), true)
	RM.Fire("SESSION_CHANGED")
end)

---------------------------------------------------------------------------
-- Raid-Check: Loot-Einstellungen und Addon-Versionen
---------------------------------------------------------------------------
local THRESHOLD_NAMES = { [2] = L["Selten (grün)"], [3] = L["Rar (blau)"], [4] = L["Episch (lila)"], [5] = L["Legendär"] }
Raid.THRESHOLD_NAMES = THRESHOLD_NAMES

function Raid.RunCheck()
	if not RM.InRaid() then RM.Print(L["Du bist in keinem Schlachtzug."]) return end
	wipe(Raid.lastCheck)
	local cfg = RM.db.config
	local lines = Raid.lastCheck

	local method = RM.GetLootMethod()
	local ml = RM.MasterLooterName()
	local wantML = (cfg.lootMaster ~= "" and cfg.lootMaster) or nil
	if method ~= "master" then
		lines[#lines + 1] = L["|cffff4040Plündermethode ist nicht Plündermeister.|r"]
	elseif wantML and ml ~= wantML then
		lines[#lines + 1] = L["|cffffcc00Plündermeister ist "] .. tostring(ml) .. L[", eingestellt ist "] .. wantML .. ".|r"
	else
		lines[#lines + 1] = L["|cff40ff40Plündermeister: "] .. tostring(ml) .. "|r"
	end
	local th = RM.GetLootThreshold()
	if th and th ~= cfg.lootThreshold then
		lines[#lines + 1] = L["|cffffcc00Plünderschwelle ist "] .. (THRESHOLD_NAMES[th] or th) .. L[", eingestellt ist "] .. (THRESHOLD_NAMES[cfg.lootThreshold] or cfg.lootThreshold) .. ".|r"
	elseif th then
		lines[#lines + 1] = L["|cff40ff40Plünderschwelle: "] .. (THRESHOLD_NAMES[th] or th) .. "|r"
	end
	if RM.CanEdit() then
		lines[#lines + 1] = L["|cff40ff40Du hast Offiziersrechte (DKP-Buchungen möglich).|r"]
	else
		lines[#lines + 1] = L["|cffff4040Du hast keine Offiziersrechte – DKP-Buchungen nicht möglich.|r"]
	end
	lines[#lines + 1] = L["Prüfe Addon-Versionen ..."]
	RM.Fire("CHECK_DONE")

	local started = GetTime()
	RM.Comm.PingRaid()
	C_Timer.After(4, function()
		lines[#lines] = nil
		local missing, old = {}, {}
		for _, m in ipairs(RM.RaidMembers()) do
			if m.name ~= RM.Me() then
				local v = RM.Comm.versions[m.name]
				if not v or v.t < started - 600 then
					missing[#missing + 1] = m.name .. (m.online and "" or L[" (offline)"])
				elseif v.num < RM.VERSION_NUM then
					old[#old + 1] = m.name .. " (" .. v.text .. ")"
				end
			end
		end
		if #missing == 0 and #old == 0 then
			lines[#lines + 1] = L["|cff40ff40Alle Raidmitglieder haben RaidMaster in der aktuellen Version.|r"]
		end
		if #missing > 0 then
			lines[#lines + 1] = L["|cffffcc00Ohne Addon ("] .. #missing .. "):|r " .. table.concat(missing, ", ")
			lines[#lines + 1] = L["   -> Diese Spieler können per Flüstern bieten: /w <Plündermeister> !bid <Zahl>"]
		end
		if #old > 0 then
			lines[#lines + 1] = L["|cffffcc00Ältere Version ("] .. #old .. "):|r " .. table.concat(old, ", ")
		end
		for _, l in ipairs(lines) do RM.Print(l) end
		RM.Fire("CHECK_DONE")
	end)
end

---------------------------------------------------------------------------
-- Pausen-Timer
---------------------------------------------------------------------------
local pauseBar
local pauseTimer
local pauseOwner

local function CreatePauseBar()
	local f = CreateFrame("Frame", "RaidMasterPauseBar", UIParent, BackdropTemplateMixin and "BackdropTemplate")
	f:SetSize(300, 34)
	f:SetPoint("TOP", UIParent, "TOP", 0, -140)
	f:SetBackdrop({ bgFile = "Interface\\Buttons\\WHITE8x8", edgeFile = "Interface\\Buttons\\WHITE8x8", edgeSize = 1 })
	f:SetBackdropColor(0.06, 0.07, 0.09, 0.92)
	f:SetBackdropBorderColor(1, 0.55, 0.1, 0.9)
	f:SetMovable(true)
	f:EnableMouse(true)
	f:RegisterForDrag("LeftButton")
	f:SetScript("OnDragStart", f.StartMoving)
	f:SetScript("OnDragStop", f.StopMovingOrSizing)
	local bar = CreateFrame("StatusBar", nil, f)
	bar:SetPoint("TOPLEFT", 4, -4)
	bar:SetPoint("BOTTOMRIGHT", -4, 4)
	bar:SetStatusBarTexture("Interface\\Buttons\\WHITE8x8")
	bar:SetStatusBarColor(1, 0.55, 0.1, 0.6)
	f.bar = bar
	local text = bar:CreateFontString(nil, "OVERLAY")
	text:SetFont(STANDARD_TEXT_FONT, 14, "OUTLINE")
	text:SetPoint("CENTER")
	f.text = text
	f:Hide()
	return f
end

function Raid.ShowPause(seconds, owner)
	pauseBar = pauseBar or CreatePauseBar()
	pauseOwner = owner
	local total = seconds
	local endsAt = GetTime() + seconds
	pauseBar.bar:SetMinMaxValues(0, total)
	pauseBar:Show()
	if pauseTimer then pauseTimer:Cancel() end
	local function Update()
		local rem = endsAt - GetTime()
		if rem <= 0 then
			pauseTimer:Cancel()
			pauseTimer = nil
			pauseBar:Hide()
			PlaySound(SOUNDKIT and SOUNDKIT.RAID_WARNING or 8959)
			if pauseOwner == RM.Me() then
				RM.Announce(L["[RaidMaster] Pause vorbei – weiter geht's!"], true)
			end
			return
		end
		pauseBar.bar:SetValue(rem)
		pauseBar.text:SetText(string.format("Pause: %d:%02d", math.floor(rem / 60), math.floor(rem % 60)))
	end
	pauseTimer = C_Timer.NewTicker(0.2, Update)
	Update()
end

function Raid.StopPause(silent)
	if pauseTimer then pauseTimer:Cancel(); pauseTimer = nil end
	if pauseBar then pauseBar:Hide() end
	if not silent then
		RM.Comm.Send("PTX", {}, "RAID", nil, true)
		RM.Announce(L["[RaidMaster] Pause beendet – weiter geht's!"], true)
	end
end

function Raid.StartPause(seconds)
	if not RM.InRaid() then RM.Print(L["Du bist in keinem Schlachtzug."]) return end
	if not (RM.IsAssist() or RM.CanEdit()) then RM.Print(L["Nur Raidleiter, Assistenten oder Offiziere können eine Pause starten."]) return end
	RM.Comm.Send("PT", { s = seconds }, "RAID", nil, true)
	Raid.ShowPause(seconds, RM.Me())
	RM.Announce(string.format("[RaidMaster] Pause: %d Minuten.", math.floor(seconds / 60)), true)
end

RM.Comm.Register("PT", function(sender, d)
	if d.s and d.s > 0 and d.s <= 3600 then Raid.ShowPause(d.s, sender) end
end)

RM.Comm.Register("PTX", function()
	Raid.StopPause(true)
end)

---------------------------------------------------------------------------
-- Kernhunde-Hilfe: Kürschner im Raid ansagen
---------------------------------------------------------------------------
local lastHound = 0

RM.On("COMBAT_LOG_EVENT_UNFILTERED", function()
	if not RM.db or not RM.db.config.coreHound then return end
	local _, subEvent, _, _, _, _, _, destGUID, destName = CombatLogGetCurrentEventInfo()
	if subEvent ~= "UNIT_DIED" or not destGUID then return end
	local npcID = tonumber((select(6, strsplit("-", destGUID))))
	if not npcID or not RM.Data.CoreHounds[npcID] then return end
	-- Nur der Raidleiter sagt an (sonst der Plündermeister, wenn der Leiter kein Addon hat)
	if not (RM.IsLeader() or RM.IAmMasterLooter()) then return end
	local now = GetTime()
	if now - lastHound < 20 then return end
	lastHound = now
	local list = {}
	local own = RM.Comm.MySkinning()
	if own > 0 then list[#list + 1] = { name = RM.Me(), skill = own } end
	for _, m in ipairs(RM.RaidMembers()) do
		local sk = RM.Comm.skinners[m.name]
		if m.online and m.name ~= RM.Me() and sk and sk > 0 then
			list[#list + 1] = { name = m.name, skill = sk }
		end
	end
	table.sort(list, function(a, b) return a.skill > b.skill end)
	local parts = {}
	for i = 1, math.min(5, #list) do parts[#parts + 1] = list[i].name .. " (" .. list[i].skill .. ")" end
	local hound = destName or RM.Data.CoreHounds[npcID]
	if #parts > 0 then
		RM.Announce(L["[RaidMaster] "] .. hound .. L[" tot – Kürschner bitte häuten: "] .. table.concat(parts, ", "), false)
	else
		RM.Announce(L["[RaidMaster] "] .. hound .. L[" tot – Kürschner bitte häuten!"], false)
	end
end)
