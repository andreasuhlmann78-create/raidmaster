-- RaidMaster - Pull- und Pausen-Timer
-- Pull-Timer (Standard 10 Sek.) und Pausen-Timer (Standard 5 Min.) per Knopf (Boss-Leiste, Seite Raid).
-- Die Timer gehen auch an Deadly Boss Mods (DBM) und BigWigs: wer eines davon nutzt, sieht den gewohnten
-- Countdown-Balken. Dazu: Schlachtzugwarnung zum Start, auf Wunsch Countdown 5-4-3-2-1 im Raidchat,
-- und bei dir eine kleine Leiste mit der restlichen Zeit. Gibt es den Countdown des Spiels, startet er mit.

local ADDON, RM = ...
local L = RM.L
local TM = {}
RM.Timer = TM

TM.active = nil          -- { kind = "pull" | "break", ends = GetTime() + Sek., total }
local ticker, bar

local function C() return RM.db.config end

local function MapID()
	return GetInstanceInfo and select(8, GetInstanceInfo()) or 0
end

-- an DBM und BigWigs (Format beider Addons, ungefährlich für alle, die sie nicht nutzen)
function TM.SendBossMods(kind, seconds)
	local mode = C().timerAddons or "both"
	if mode == "none" then return end
	local send = RM.SendAddonMessage
	if not send then return end
	seconds = math.max(0, math.floor(seconds))
	if mode == "both" or mode == "dbm" then
		local msg = kind == "pull" and string.format("PT\t%d\t%d", seconds, MapID()) or string.format("BT\t%d", seconds)
		for _, prefix in ipairs({ "D5", "D4C" }) do
			pcall(send, prefix, "1\t" .. msg, "RAID")
		end
	end
	if mode == "both" or mode == "bigwigs" then
		pcall(send, "BigWigs", (kind == "pull" and "P^Pull^" or "P^Break^") .. seconds, "RAID")
	end
end

local function CanStart()
	if not RM.InRaid() then RM.Print(L["Timer gehen nur im Raid."]) return false end
	if not (RM.IsAssist() or RM.CanEdit()) then RM.Print(L["Timer starten Raidleiter und Assistenten."]) return false end
	return true
end

local function Stop()
	if ticker then ticker:Cancel(); ticker = nil end
	TM.active = nil
	if bar then bar:Hide() end
	RM.Fire("TIMER_CHANGED")
end

local function UpdateBar()
	local a = TM.active
	if not a then return end
	if not bar then
		local UI = RM.UI
		bar = UI.Frame(UIParent, 220, 30)
		UI.Skin(bar, nil, UI.COLORS.accent)
		bar:SetFrameStrata("HIGH")
		UI.MakeMovable(bar, "timerBar", "TOP", 0, -140)
		bar.fill = bar:CreateTexture(nil, "ARTWORK")
		bar.fill:SetPoint("TOPLEFT", 2, -2)
		bar.fill:SetPoint("BOTTOMLEFT", 2, 2)
		bar.fill:SetColorTexture(0.8, 0.4, 0.05, 0.6)
		bar.text = UI.Text(bar, "", 13, nil, nil, nil, "CENTER")
		bar.text:SetPoint("CENTER")
	end
	local left = math.max(0, a.ends - GetTime())
	bar.fill:SetWidth(math.max(1, 216 * (left / a.total)))
	local t = left >= 60 and string.format("%d:%02d", math.floor(left / 60), math.floor(left % 60)) or string.format("%.0f", math.ceil(left))
	bar.text:SetText((a.kind == "pull" and L["Pull in "] or L["Pause: "]) .. t)
	bar:Show()
end

local function Tick()
	local a = TM.active
	if not a then return end
	local left = a.ends - GetTime()
	local whole = math.ceil(left)
	if a.kind == "pull" and C().pullCountdownChat ~= false and whole <= 5 and whole >= 1 and whole ~= a.lastSaid then
		a.lastSaid = whole
		RM.RaidChat(tostring(whole), "RAID")
	end
	if a.kind == "break" and whole == 60 and not a.saidMinute then
		a.saidMinute = true
		RM.Announce(L["[RaidMaster] Pause: noch 1 Minute – zurück an die Tastatur!"], true)
	end
	if left <= 0 then
		local kind = a.kind
		Stop()
		if kind == "pull" then RM.Announce(L["PULL!"], true) else RM.Announce(L["[RaidMaster] Pause vorbei – weiter geht's!"], true) end
		RM.Fire("TIMER_FINISHED", kind)
		return
	end
	UpdateBar()
end

local function Begin(kind, seconds)
	if ticker then ticker:Cancel() end
	TM.active = { kind = kind, ends = GetTime() + seconds, total = seconds }
	ticker = C_Timer.NewTicker(0.1, Tick)
	UpdateBar()
	RM.Fire("TIMER_CHANGED")
end

function TM.Pull(seconds)
	if not CanStart() then return end
	seconds = math.max(3, math.min(60, math.floor(tonumber(seconds) or tonumber(C().pullSeconds) or 10)))
	TM.SendBossMods("pull", seconds)
	if C_PartyInfo and C_PartyInfo.DoCountdown and not (RM.Test and RM.Test.active) then pcall(C_PartyInfo.DoCountdown, seconds) end
	RM.Announce(string.format(L["[RaidMaster] Pull in %d Sekunden!"], seconds), true)
	Begin("pull", seconds)
end

-- Pause: dieselbe Pause wie auf der Seite Raid (Fenster bei allen Addon-Nutzern), zusätzlich an DBM/BigWigs
function TM.Break(minutes)
	if not CanStart() then return end
	minutes = math.max(1, math.min(30, math.floor(tonumber(minutes) or tonumber(C().breakMinutes) or 5)))
	RM.Raid.StartPause(minutes * 60)
end

function TM.Cancel()
	if RM.Raid.pauseUntil and not TM.active then
		RM.Raid.StopPause()
		return
	end
	local a = TM.active
	if not a then return end
	TM.SendBossMods(a.kind, 0)
	if C_PartyInfo and C_PartyInfo.DoCountdown and a.kind == "pull" and not (RM.Test and RM.Test.active) then pcall(C_PartyInfo.DoCountdown, 0) end
	Stop()
	RM.Announce(a.kind == "pull" and L["[RaidMaster] Pull abgebrochen!"] or L["[RaidMaster] Pause beendet."], true)
end

function TM.Running(kind)
	if kind == "break" or kind == nil then
		local p = RM.Raid and RM.Raid.pauseUntil
		if p and p > GetTime() then return true end
		if kind == "break" then return false end
	end
	return TM.active ~= nil and (kind == nil or TM.active.kind == kind)
end

-- Pull-Timer endet bei Kampfbeginn sofort (wer zu früh pullt, beendet den Countdown)
RM.On("ENCOUNTER_START", function()
	if TM.active and TM.active.kind == "pull" then Stop() end
end)
