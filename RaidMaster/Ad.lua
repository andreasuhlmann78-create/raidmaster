-- RaidMaster - Werbung
-- Werbetext für PUG-Raids mit Discord-Link im offenen Chat posten (Welt, Handel, Gruppensuche ...)
-- und auf geflüstertes "inv" automatisch einladen.

local _, RM = ...
local L = RM.L
local Ad = {}
RM.Ad = Ad

Ad.DEFAULT_TEXT = L["[{raid}] PUG {zeit} – {frei}. SR: {softres} · Anmeldung im Discord: {link} – oder /w {name} inv"]
Ad.DEFAULT_TEXT_NOLINK = L["[{raid}] PUG {zeit} – {frei}. SR: {softres} · Einladung: /w {name} inv"]
Ad.COOLDOWN = 30
Ad.lastPost = 0

local WEEKDAYS = { L["So"], L["Mo"], L["Di"], L["Mi"], L["Do"], L["Fr"], L["Sa"] }

---------------------------------------------------------------------------
-- Kanäle
---------------------------------------------------------------------------
-- Liste der Ziele: { key, label }. Kanäle werden über ihren Namen gemerkt,
-- weil sich die Nummern je nach Beitritts-Reihenfolge ändern.
function Ad.Targets()
	local list = {}
	if GetChannelName then
		for i = 1, 20 do
			local id, name = GetChannelName(i)
			if id and id > 0 and name and name ~= "" then
				list[#list + 1] = { "c:" .. name, id .. ". " .. name }
			end
		end
	end
	list[#list + 1] = { "YELL", L["Schreien (/y)"] }
	list[#list + 1] = { "SAY", L["Sagen (/s)"] }
	list[#list + 1] = { "GUILD", L["Gilde"] }
	return list
end

-- Bevorzugt einen Welt-/Gruppensuche-Kanal
function Ad.DefaultTarget()
	local best
	for _, t in ipairs(Ad.Targets()) do
		local n = t[1]:lower()
		if n:find("^c:") then
			if n:find("world") or n:find("welt") or n:find("global") then return t[1] end
			if not best and (n:find("suche") or n:find("looking") or n:find("lfg")) then best = t[1] end
			if not best and (n:find("handel") or n:find("trade")) then best = t[1] end
		end
	end
	return best or "YELL"
end

function Ad.Target()
	local key = RM.db.config.adChannel
	if not key or key == "" then key = Ad.DefaultTarget() end
	return key
end

function Ad.TargetLabel(key)
	for _, t in ipairs(Ad.Targets()) do
		if t[1] == key then return t[2] end
	end
	if key:find("^c:") then return key:sub(3) .. L[" (nicht beigetreten)"] end
	return key
end

---------------------------------------------------------------------------
-- Text
---------------------------------------------------------------------------
local function RaidTitle()
	local su = RM.db.signup
	if su and su.title and su.title ~= "" then return su.title end
	local pool = RM.DKP.CurrentInstancePool() or RM.db.config.activePool
	return pool and RM.DKP.PoolName(pool) or L["Raid"]
end

local function TimeText()
	local su = RM.db.signup
	if su and su.start then
		local d = date("*t", su.start)
		return string.format("%s %s", WEEKDAYS[d.wday] or "", date("%d.%m. %H:%M", su.start))
	end
	if su and su.date and su.date ~= "" then return su.date end
	return "jetzt"
end

local function FreeText()
	local su = RM.db.signup
	local max = su and su.max
	if not max then return "" end
	local have
	if RM.InRaid() then
		have = GetNumGroupMembers()
	else
		have = 0
		for _, e in ipairs(su.list or {}) do if e.status == "an" then have = have + 1 end end
	end
	local free = max - have
	if free <= 0 then return "" end
	return string.format("noch %d %s frei", free, free == 1 and L["Platz"] or L["Plätze"])
end

local function Clean(s)
	s = s:gsub("%s+", " ")
	for _ = 1, 3 do
		s = s:gsub("%s*,%s*,", ",")
		s = s:gsub("%s*,%s*%.", ".")
		s = s:gsub("–%s*,", "–")
		s = s:gsub(",%s*–", " –")
		s = s:gsub("–%s*%.", ".")
		s = s:gsub("%(%s*%)", "")
		s = s:gsub("%[%s*%]", "")
		s = s:gsub(":%s*–", " –")
		s = s:gsub("SR:%s*·%s*", "")
		s = s:gsub(":%s*·", " ·")
		s = s:gsub(":%s*$", "")
		s = s:gsub("%s+([,%.])", "%1")
		s = s:gsub("%s+", " ")
	end
	return (s:gsub("^[%s,%.–]+", ""):gsub("[%s,–]+$", ""))
end

function Ad.Build()
	local cfg = RM.db.config
	local text = cfg.adText
	if not text or text == "" then
		text = (cfg.adLink and cfg.adLink ~= "") and Ad.DEFAULT_TEXT or Ad.DEFAULT_TEXT_NOLINK
	end
	local values = {
		raid = RaidTitle(),
		zeit = TimeText(),
		frei = FreeText(),
		link = cfg.adLink or "",
		softres = cfg.softresLink or "",
		name = RM.Me() or "",
	}
	text = text:gsub("{(%a+)}", function(k) return values[k:lower()] or "" end)
	text = Clean(text)
	if #text > 255 then text = text:sub(1, 252) .. "..." end
	return text
end

---------------------------------------------------------------------------
-- Posten (muss direkt aus einem Mausklick kommen – öffentliche Kanäle
-- erlauben Nachrichten von Addons nur nach einem Klick)
---------------------------------------------------------------------------
function Ad.CooldownLeft()
	return math.max(0, math.ceil(Ad.lastPost + Ad.COOLDOWN - GetTime()))
end

function Ad.Post()
	local left = Ad.CooldownLeft()
	if left > 0 then
		RM.Print(string.format(L["Bitte noch %d Sekunden warten – sonst gilt es als Spam."], left))
		return false
	end
	local text = Ad.Build()
	if text == "" then return false end
	local key = Ad.Target()
	if key:find("^c:") then
		local id = GetChannelName(key:sub(3))
		if not id or id == 0 then
			RM.Print(L["Du bist nicht im Kanal '"] .. key:sub(3) .. L["'. Bitte beitreten (/join "] .. key:sub(3) .. L[") oder einen anderen Kanal wählen."])
			return false
		end
		SendChatMessage(text, "CHANNEL", nil, id)
	else
		SendChatMessage(text, key)
	end
	Ad.lastPost = GetTime()
	RM.Fire("AD_CHANGED")
	return true
end

---------------------------------------------------------------------------
-- Auf "inv" automatisch einladen
---------------------------------------------------------------------------
local INV_WORDS = { inv = true, invite = true, ["inv pls"] = true, ["inv bitte"] = true, ["+"] = true, ["1"] = true }

local function CanInvite()
	if not RM.InRaid() then
		return not IsInGroup() or UnitIsGroupLeader("player")
	end
	return RM.IsAssist() and GetNumGroupMembers() < 40
end

RM.On("CHAT_MSG_WHISPER", function(msg, sender)
	if not RM.db or not RM.db.config.adAutoInvite then return end
	-- nur in den 30 Minuten nach der letzten Werbung
	if Ad.lastPost == 0 or GetTime() - Ad.lastPost > 1800 then return end
	local m = (msg or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
	if not INV_WORDS[m] then return end
	if not CanInvite() then return end
	local name = RM.Short(sender)
	if RM.IsInMyRaid(name) then return end
	local invite = (C_PartyInfo and C_PartyInfo.InviteUnit) or InviteUnit
	if invite then invite(sender) end
end)

-- Aus einer Gruppe automatisch einen Schlachtzug machen, solange geworben wird
RM.On("GROUP_ROSTER_UPDATE", function()
	if not RM.db or not RM.db.config.adAutoInvite then return end
	if Ad.lastPost == 0 or GetTime() - Ad.lastPost > 1800 then return end
	if IsInGroup() and not RM.InRaid() and UnitIsGroupLeader("player") and GetNumGroupMembers() >= 2 then
		local fn = (C_PartyInfo and C_PartyInfo.ConvertToRaid) or ConvertToRaid
		if fn then fn() end
	end
end)
