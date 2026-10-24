-- RaidMaster - Raidanmeldungen aus Discord
-- Import des Textes vom RaidMaster-Bot, Abgleich mit dem Raid, Einladen, Ersatzbank übernehmen

local ADDON, RM = ...
local L = RM.L
local S = {}
RM.Signup = S

S.ROLE = { tank = L["Tank"], heal = L["Heiler"], melee = L["Nahkampf"], ranged = L["Fernkampf"] }
S.STATUS = { an = L["Angemeldet"], ersatz = L["Ersatzbank"], vielleicht = L["Vielleicht"], ab = L["Abgemeldet"] }

local function Invite(name)
	local fn = (C_PartyInfo and C_PartyInfo.InviteUnit) or InviteUnit
	if fn then fn(name) end
end

local function MakeRaid()
	local fn = (C_PartyInfo and C_PartyInfo.ConvertToRaid) or ConvertToRaid
	if fn then fn() end
end

local function trim(s)
	return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

---------------------------------------------------------------------------
-- Import
---------------------------------------------------------------------------
function S.Parse(text)
	if not text or not text:find("RAIDMASTER%-ANMELDUNG") then
		return nil, L["Das ist kein Anmeldetext vom RaidMaster-Bot."]
	end
	local result = { title = "", date = "", list = {}, mode = "dkp", groups = nil, bench = nil, start = nil }
	for raw in text:gmatch("[^\r\n]+") do
		local line = trim(raw):gsub("`", "")
		local t = line:match("^Raid:%s*(.+)$")
		local d = line:match("^Datum:%s*(.+)$")
		local mode = line:match("^Modus:%s*(%a+)")
		local isSR = line:match("^SR;")   -- ältere Exporte mit Soft Reserve: ignorieren
		local gName, gNum = line:match("^GRP;([^;]+);(%d+)$")
		local bName = line:match("^BANK;([^;]+)$")
		local startTs = line:match("^Start:%s*(%d+)$")
		local poolKey = line:match("^Topf:%s*([%w_]+)$")
		local link = line:match("^Link:%s*(%S+)$")
		local softres = line:match("^SoftRes:%s*(%S+)$")
		local maxN = line:match("^Max:%s*(%d+)$")
		if softres then
			result.softres = softres
		elseif link then
			result.link = link
		elseif maxN then
			result.max = tonumber(maxN)
		elseif poolKey then
			result.pool = poolKey
		elseif gName then
			result.groups = result.groups or {}
			result.groups[RM.Short(trim(gName))] = tonumber(gNum)
		elseif bName then
			result.bench = result.bench or {}
			result.bench[RM.Short(trim(bName))] = true
		elseif startTs then
			result.start = tonumber(startTs)
		elseif t then
			result.title = t
		elseif d then
			result.date = d
		elseif mode then
			result.mode = mode:lower()
		elseif isSR then
			-- nichts
		else
			local n, c, r, s = line:match("^([^;]+);([^;]*);([^;]*);([^;]+)$")
			if n then
				result.list[#result.list + 1] = { name = RM.Short(trim(n)), cls = trim(c), role = trim(r), status = trim(s) }
			end
		end
	end
	if #result.list == 0 then return nil, L["Im Text wurden keine Anmeldungen gefunden."] end
	return result
end

function S.Import(text)
	local result, err = S.Parse(text)
	if not result then RM.Print(err) return false end
	result.imported = GetServerTime()
	RM.db.signup = result
	local counts = {}
	for _, e in ipairs(result.list) do counts[e.status] = (counts[e.status] or 0) + 1 end
	RM.Print(string.format(L["Anmeldungen für '%s' importiert: %d angemeldet, %d Ersatzbank, %d vielleicht, %d abgemeldet."],
		result.title, counts.an or 0, counts.ersatz or 0, counts.vielleicht or 0, counts.ab or 0))
	if result.softres then
		RM.db.config.softresLink = result.softres
		RM.Print(L["softres.it-Link übernommen: "] .. result.softres)
	end
	if result.link then
		RM.db.config.adLink = result.link
		RM.Print(L["Discord-Link für die Werbung übernommen: "] .. result.link)
	end
	if result.pool then
		RM.db.config.activePool = result.pool
		RM.Print(L["DKP-Topf für diesen Raid: "] .. RM.DKP.PoolName(result.pool))
	end
	if result.groups then
		local n = 0
		for _ in pairs(result.groups) do n = n + 1 end
		RM.Print(string.format(L["Aufstellung mit %d Spielern und festen Gruppen übernommen."], n))
	end
	if result.start and RM.db.config.autoInvite then
		RM.Print(string.format("Auto-Einladung: %d Min. vor Raidbeginn (%s).", RM.db.config.autoInviteMinutes or 15, date("%d.%m. %H:%M", result.start)))
	end
	RM.Fire("SIGNUP_CHANGED")
	return true
end

function S.Clear()
	RM.db.signup = nil
	RM.Fire("SIGNUP_CHANGED")
end

---------------------------------------------------------------------------
-- Abgleich mit dem Raid
---------------------------------------------------------------------------
-- Liefert: Einträge mit .inRaid/.online, fehlende Angemeldete, Raidmitglieder ohne Anmeldung
function S.Compare()
	local su = RM.db.signup
	local members = {}
	for _, m in ipairs(RM.RaidMembers()) do members[m.name] = m end
	if not RM.InRaid() and IsInGroup and IsInGroup() then
		members[RM.Me()] = { name = RM.Me(), online = true }
		for i = 1, 4 do
			local n = UnitName("party" .. i)
			if n then members[RM.Short(n)] = { name = RM.Short(n), online = UnitIsConnected("party" .. i) } end
		end
	end
	local rows, missing, extra = {}, {}, {}
	local listed = {}
	if su then
		for _, e in ipairs(su.list) do
			local m = members[e.name]
			listed[e.name] = true
			rows[#rows + 1] = { entry = e, inRaid = m ~= nil, online = m and m.online }
			if e.status == "an" and not m then missing[#missing + 1] = e.name end
		end
		for name in pairs(members) do
			if not listed[name] then extra[#extra + 1] = name end
		end
		table.sort(extra)
	end
	return rows, missing, extra
end

---------------------------------------------------------------------------
-- Einladen
---------------------------------------------------------------------------
local queue = {}
local ticker
local soloInvites = 0
local deadline = 0

local function Stop(msg)
	if ticker then ticker:Cancel(); ticker = nil end
	wipe(queue)
	if msg then RM.Print(msg) end
	RM.Fire("SIGNUP_CHANGED")
end

local function Tick()
	if #queue == 0 then Stop(L["Alle Einladungen verschickt."]) return end
	if GetTime() > deadline then Stop(L["Einladen abgebrochen (Zeitlimit). Nicht eingeladen: "] .. table.concat(queue, ", ")) return end
	if not RM.InRaid() then
		if IsInGroup() then
			if UnitIsGroupLeader("player") then MakeRaid() end
			return -- warten, bis die Gruppe ein Schlachtzug ist
		end
		if soloInvites >= 4 then return end -- warten, bis der Erste annimmt
		soloInvites = soloInvites + 1
	end
	local name = table.remove(queue, 1)
	if not RM.IsInMyRaid(name) then Invite(name) end
end

function S.IsInviting()
	return ticker ~= nil
end

function S.InviteAll(includeBench, silentSkip)
	local su = RM.db.signup
	if not su then RM.Print(L["Zuerst Anmeldungen importieren."]) return end
	if IsInGroup() and not RM.IsAssist() then RM.Print(L["Zum Einladen brauchst du Leiter- oder Assistentenrechte."]) return end
	wipe(queue)
	local me = RM.Me()
	local rows = S.Compare()
	local groups = su.groups
	for _, r in ipairs(rows) do
		local st = r.entry.status
		local wanted
		if groups then
			-- Aufstellung vorhanden: nur aufgestellte Spieler (Ersatzbank auf Wunsch)
			wanted = groups[r.entry.name] ~= nil or (includeBench and (su.bench and su.bench[r.entry.name] or st == "ersatz"))
		else
			wanted = st == "an" or (includeBench and st == "ersatz")
		end
		if not r.inRaid and r.entry.name ~= me and wanted and not (silentSkip and silentSkip[r.entry.name]) then
			queue[#queue + 1] = r.entry.name
		end
	end
	if #queue == 0 then
		if not silentSkip then RM.Print(L["Alle Angemeldeten sind bereits in der Gruppe."]) end
		return 0
	end
	soloInvites = 0
	deadline = GetTime() + 180
	RM.Print(string.format(L["Lade %d Spieler ein ..."], #queue))
	local count = #queue
	if ticker then ticker:Cancel() end
	ticker = C_Timer.NewTicker(0.6, Tick)
	RM.Fire("SIGNUP_CHANGED")
	return count
end

function S.StopInvites()
	Stop(L["Einladen gestoppt."])
end

---------------------------------------------------------------------------
-- Feste Gruppen im Spiel einteilen
---------------------------------------------------------------------------
local arrangeTicker
local arrangeSteps = 0

-- Ein Schritt: einen Spieler in seine Gruppe setzen oder tauschen. true = etwas getan
function S.ArrangeStep()
	local su = RM.db.signup
	local want = su and su.groups
	if not want or not RM.InRaid() or not RM.IsAssist() then return false end
	if InCombatLockdown and InCombatLockdown() then return false end
	local cur, count, index = {}, {}, {}
	for i = 1, GetNumGroupMembers() do
		local name, _, subgroup = GetRaidRosterInfo(i)
		if name then
			name = RM.Short(name)
			cur[name] = subgroup
			index[name] = i
			count[subgroup] = (count[subgroup] or 0) + 1
		end
	end
	for name, g in pairs(want) do
		local i = index[name]
		if i and cur[name] ~= g then
			if (count[g] or 0) < 5 then
				SetRaidSubgroup(i, g)
				return true
			end
			for other, og in pairs(cur) do
				if og == g and want[other] ~= g then
					SwapRaidSubgroup(i, index[other])
					return true
				end
			end
		end
	end
	return false
end

function S.ArrangeGroups(silent)
	local su = RM.db.signup
	if not su or not su.groups then
		if not silent then RM.Print(L["Keine Gruppen-Aufstellung importiert (in Discord: /raid aufstellung, dann Export)."]) end
		return
	end
	if not RM.IsAssist() then
		if not silent then RM.Print(L["Zum Einteilen brauchst du Leiter- oder Assistentenrechte."]) end
		return
	end
	arrangeSteps = 0
	if arrangeTicker then arrangeTicker:Cancel() end
	arrangeTicker = C_Timer.NewTicker(0.4, function()
		arrangeSteps = arrangeSteps + 1
		if not S.ArrangeStep() or arrangeSteps > 60 then
			arrangeTicker:Cancel()
			arrangeTicker = nil
			if not silent then RM.Print(L["Gruppen eingeteilt."]) end
			RM.Fire("SIGNUP_CHANGED")
		end
	end)
end

-- Beim Beitritt neuer Spieler automatisch nachsortieren
local lastArrange = 0
RM.On("GROUP_ROSTER_UPDATE", function()
	if not RM.db or not RM.db.config.autoGroups or arrangeTicker then return end
	if not RM.db.signup or not RM.db.signup.groups then return end
	if not RM.InRaid() or not RM.IsAssist() then return end
	local now = GetTime()
	if now - lastArrange < 2 then return end
	lastArrange = now
	C_Timer.After(1, function() S.ArrangeGroups(true) end)
end)

---------------------------------------------------------------------------
-- Auto-Einladung: X Minuten vor Raidbeginn, Nachzügler bis 30 Min. nach Beginn
---------------------------------------------------------------------------
local lastTry = {}

function S.AutoInviteState()
	local su = RM.db.signup
	local cfg = RM.db.config
	if not cfg.autoInvite then return "aus" end
	if not su or not su.start then return L["kein Raidbeginn im Import"] end
	local openAt = su.start - (cfg.autoInviteMinutes or 15) * 60
	local now = GetServerTime()
	if now < openAt then return L["öffnet "] .. date("%d.%m. %H:%M", openAt) end
	if now > su.start + 1800 then return "beendet" end
	return "aktiv"
end

C_Timer.NewTicker(20, function()
	if not RM.db or S.AutoInviteState() ~= "aktiv" then return end
	if S.IsInviting() then return end
	if IsInGroup() and not RM.IsAssist() then return end
	local su = RM.db.signup
	-- jeden Spieler höchstens alle 2 Minuten erneut einladen
	local now = GetTime()
	local skip = {}
	for name, t in pairs(lastTry) do if now - t < 120 then skip[name] = true end end
	local first = not su.autoInvited
	local n = S.InviteAll(false, skip)
	if n and n > 0 then
		for _, name in ipairs(queue) do lastTry[name] = now end
		if first then
			su.autoInvited = true
			if IsInGroup() or RM.InRaid() then
				RM.Announce(L["[RaidMaster] Raid ist offen – Einladungen gehen raus!"], false)
			end
		end
	end
end)

---------------------------------------------------------------------------
-- Ersatzbank übernehmen
---------------------------------------------------------------------------
function S.ApplyStandby()
	local su = RM.db.signup
	if not su then RM.Print(L["Zuerst Anmeldungen importieren."]) return end
	local n = 0
	for _, e in ipairs(su.list) do
		local bench = e.status == "ersatz" or (su.bench and su.bench[e.name])
		if bench and not RM.db.config.standby[e.name] then
			RM.db.config.standby[e.name] = true
			n = n + 1
		end
	end
	RM.Print(n .. L[" Spieler auf die Ersatzbank übernommen."])
	RM.Fire("DATA_CHANGED")
end
