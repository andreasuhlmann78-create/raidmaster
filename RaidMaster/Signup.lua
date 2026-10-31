-- RaidMaster - Raidanmeldungen aus Discord
-- Import des Textes vom RaidMaster-Bot, Abgleich mit dem Raid, Einladen, Ersatzbank übernehmen

local ADDON, RM = ...
local L = RM.L
local S = {}
RM.Signup = S

S.ROLE = { tank = L["Tank"], heal = L["Heiler"], melee = L["Nahkampf"], ranged = L["Fernkampf"] }
S.STATUS = { an = L["Angemeldet"], ersatz = L["Ersatzbank"], vielleicht = L["Vielleicht"], ab = L["Abgemeldet"] }

-- Ist das ein Testraid aus Discord (/raid testraid, erfundene Namen)?
function S.IsTestSignup(su)
	su = su or RM.db.signup
	return su ~= nil and (su.test == true or (type(su.title) == "string" and su.title:find("^TEST ") ~= nil))
end

local function InTestSignup(name)
	local su = RM.db and RM.db.signup
	if not S.IsTestSignup(su) then return false end
	name = RM.Short(name)
	for _, e in ipairs(su.list or {}) do if e.name == name then return true end end
	return false
end

-- Einladen / Schlachtzug bilden (im Testmodus ersetzt das Test-Tool beides durch eine Simulation)
function S.DoInvite(name)
	-- Testanmeldungen (erfundene Namen) nie wirklich einladen – das geht nur im Testmodus (simuliert)
	if InTestSignup(name) then
		if not S.warnedTest then
			S.warnedTest = true
			RM.Print(L["Das sind Testanmeldungen (erfundene Namen) – sie werden nie wirklich eingeladen. Testmodus starten, dann wird das Einladen simuliert."])
		end
		return false
	end
	S.MarkInvite(name, "invited")
	local fn = (C_PartyInfo and C_PartyInfo.InviteUnit) or InviteUnit
	if fn then fn(name) end
end

---------------------------------------------------------------------------
-- Antworten auf Einladungen: nicht gefunden/offline, abgelehnt, schon in einer Gruppe
---------------------------------------------------------------------------
S.inviteState = {}       -- Name -> { s = "invited" | "notfound" | "declined" | "ingroup", t = GetTime() }
S.STATE_TEXT = { invited = L["eingeladen"], notfound = L["nicht gefunden"], declined = L["abgelehnt"], ingroup = L["in Gruppe"], full = L["Raid voll"] }
S.RETRY_AFTER = 600      -- so lange lädt die Auto-Einladung "nicht gefunden"/"abgelehnt" nicht erneut ein

function S.MarkInvite(name, state)
	if not name then return end
	name = RM.Short(name)
	local old = S.inviteState[name]
	S.inviteState[name] = { s = state, t = GetTime() }
	if not old or old.s ~= state then RM.Fire("SIGNUP_CHANGED") end
end

-- aktueller Stand einer Einladung (nil, wenn nichts bekannt oder schon lange her)
function S.InviteState(name)
	local st = name and S.inviteState[RM.Short(name)]
	if not st then return nil end
	if GetTime() - st.t > 3600 then return nil end
	return st.s, GetTime() - st.t
end

-- lohnt sich eine (automatische) Einladung gerade nicht?
function S.RecentlyFailed(name)
	local st, age = S.InviteState(name)
	return (st == "notfound" or st == "declined" or st == "ingroup") and age < S.RETRY_AFTER
end

local function Pattern(fmt)
	if type(fmt) ~= "string" or not fmt:find("%%s") then return nil end
	local p = fmt:gsub("([%(%)%.%+%-%*%?%[%]%^%$])", "%%%1")
	p = p:gsub("%%%d?%%?%$?s", "(.+)")
	return "^" .. p .. "$"
end
local SYSTEM_PATTERNS
local function SystemPatterns()
	if SYSTEM_PATTERNS then return SYSTEM_PATTERNS end
	SYSTEM_PATTERNS = {}
	for _, v in ipairs({ { "ERR_BAD_PLAYER_NAME_S", "notfound" }, { "ERR_PLAYER_NOT_FOUND_S", "notfound" },
		{ "ERR_DECLINE_GROUP_S", "declined" }, { "ERR_ALREADY_IN_GROUP_S", "ingroup" }, { "ERR_INVITE_PLAYER_S", "invited" } }) do
		local p = Pattern(_G[v[1]])
		if p then SYSTEM_PATTERNS[#SYSTEM_PATTERNS + 1] = { p, v[2] } end
	end
	return SYSTEM_PATTERNS
end

function S.OnSystemMessage(msg)
	if type(msg) ~= "string" then return end
	for _, v in ipairs(SystemPatterns()) do
		local name = msg:match(v[1])
		if name then
			name = name:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("|H[^|]+|h", ""):gsub("|h", "")
			S.MarkInvite(name, v[2])
			return v[2], RM.Short(name)
		end
	end
end
RM.On("CHAT_MSG_SYSTEM", function(msg) S.OnSystemMessage(msg) end)
RM.On("GROUP_ROSTER_UPDATE", function()
	-- wer jetzt im Raid ist, hat angenommen
	for name, st in pairs(S.inviteState) do
		if st.s == "invited" and RM.IsInMyRaid(name) then S.inviteState[name] = nil end
	end
end)

function S.DoMakeRaid()
	local fn = (C_PartyInfo and C_PartyInfo.ConvertToRaid) or ConvertToRaid
	if fn then fn() end
end

local function Invite(name) S.DoInvite(name) end
local function MakeRaid() S.DoMakeRaid() end

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
		local isSR = line:match("^SR;")
		local testFlag = line:match("^Test:%s*(%d)")   -- ältere Exporte mit Soft Reserve: ignorieren
		local gName, gNum = line:match("^GRP;([^;]+);(%d+)$")
		local bName = line:match("^BANK;([^;]+)$")
		local altName, altMain = line:match("^ALT;([^;]+);([^;]+)$")
		local startTs = line:match("^Start:%s*(%d+)$")
		local poolKey = line:match("^Topf:%s*([%w_]+)$")
		local link = line:match("^Link:%s*(%S+)$")
		local softres = line:match("^SoftRes:%s*(%S+)$")
		local maxN = line:match("^Max:%s*(%d+)$")
		if testFlag then
			result.test = testFlag == "1"
		elseif softres then
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
		elseif altName then
			result.alts = result.alts or {}
			result.alts[RM.Short(trim(altName))] = RM.Short(trim(altMain))
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
	-- Testraid aus Discord: nur im Testmodus (Einladen wird simuliert, nichts geht an echte Spieler)
	if S.IsTestSignup(result) and not RM.IsDev() then
		-- Testraids aus Discord gehören zum Testmodus – nur für den Entwickler
		RM.RequireDev()
		return false
	end
	if S.IsTestSignup(result) and RM.Test and not RM.Test.active and RM.Test.Start then
		RM.Test.Start()
		RM.Print(L["Testanmeldungen erkannt – der Testmodus wurde gestartet. Einladungen werden nur simuliert."])
	end
	RM.db.signup = result
	S.warnedTest = nil
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
	-- Twinks aus Discord (/twink) mit ihrem Main verknüpfen (nur Offiziere/Raidleitung)
	if result.alts and RM.CanEdit() and RM.DKP.SetMain then
		local linked = 0
		for twink, main in pairs(result.alts) do
			if RM.DKP.MainOf(twink) ~= main and RM.DKP.SetMain(twink, main, true) then linked = linked + 1 end
		end
		if linked > 0 then RM.Print(string.format(L["%d Twinks aus Discord mit ihrem Main verknüpft."], linked)) end
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
			rows[#rows + 1] = { entry = e, inRaid = m ~= nil, online = m and m.online, state = (not m) and S.InviteState(e.name) or nil }
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

---------------------------------------------------------------------------
-- Platz im Raid: nie mehr einladen, als hineinpassen (höchstens 40)
---------------------------------------------------------------------------
S.MAX_RAID = 40
S.PENDING_SECONDS = 90   -- so lange zählt eine verschickte, noch offene Einladung als belegter Platz

function S.RaidSize()
	local size = (RM.Gaps and RM.Gaps.RaidSize and RM.Gaps.RaidSize()) or tonumber(RM.db.signup and RM.db.signup.max) or S.MAX_RAID
	return math.max(1, math.min(S.MAX_RAID, size))
end

-- wie viele sind schon da (inkl. dir)?
function S.MemberCount()
	local n = #RM.RaidMembers()
	if n > 0 then return n end
	if IsInGroup and IsInGroup() and GetNumGroupMembers then return math.max(1, GetNumGroupMembers()) end
	return 1
end

-- verschickte Einladungen, auf die noch keine Antwort kam
function S.PendingInvites()
	local n = 0
	for name, st in pairs(S.inviteState) do
		if st.s == "invited" and GetTime() - st.t < S.PENDING_SECONDS and not RM.IsInMyRaid(name) then n = n + 1 end
	end
	return n
end

-- freie Plätze: Raidgröße minus Anwesende minus offene Einladungen
function S.Capacity()
	return S.RaidSize() - S.MemberCount() - S.PendingInvites()
end

-- Text für die Anzeige: "Raid 35/40 · 3 Einladungen offen · frei: 2"
function S.CapacityText()
	local size, have, pending = S.RaidSize(), S.MemberCount(), S.PendingInvites()
	local free = math.max(0, size - have - pending)
	local color = free == 0 and "|cffff6666" or "|cff66ff66"
	return string.format(L["Raid %d/%d · %d Einladungen offen · %sfrei: %d|r"], have, size, pending, color, free)
end

local function Tick()
	if #queue == 0 then Stop(L["Alle Einladungen verschickt."]) return end
	if S.Capacity() <= 0 then
		Stop(string.format(L["Raid ist voll (%d/%d) – nicht mehr eingeladen: %s"], S.MemberCount() + S.PendingInvites(), S.RaidSize(), table.concat(queue, ", ")))
		return
	end
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

-- steht der Spieler gerade in der Einladeliste?
function S.IsQueued(name)
	name = RM.Short(name)
	for _, n in ipairs(queue) do if n == name then return true end end
	return false
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
	return S.StartQueue()
end

-- Bestimmte Spieler einladen (z. B. aus "Lücken füllen")
function S.InviteNames(names)
	if IsInGroup() and not RM.IsAssist() then RM.Print(L["Zum Einladen brauchst du Leiter- oder Assistentenrechte."]) return 0 end
	local seen = {}
	for _, n in ipairs(queue) do seen[n] = true end
	local added = 0
	for _, name in ipairs(names or {}) do
		name = RM.Short(name)
		if name ~= RM.Me() and not seen[name] and not RM.IsInMyRaid(name) then
			queue[#queue + 1] = name
			seen[name] = true
			added = added + 1
		end
	end
	if added == 0 then return 0 end
	if ticker then
		deadline = math.max(deadline, GetTime() + 180)
		RM.Fire("SIGNUP_CHANGED")
		return added
	end
	return S.StartQueue()
end

function S.StartQueue()
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

local function IsTank(name)
	local su = RM.db.signup
	for _, e in ipairs((su and su.list) or {}) do
		if e.name == name and e.role and e.role ~= "" then return e.role == "tank" end
	end
	return RM.Spec and RM.Spec.Role(name) == "tank" or false
end

-- Main- und Offtank: Haupttank-Markierung im Raid, dann Tanks, die Discord schon in Gruppe 1 hat, dann übrige Tanks
function S.MainTanks()
	local su = RM.db.signup
	local groups = su and su.groups or {}
	local list, seen = {}, {}
	local members = RM.RaidMembers()
	local function add(name) if #list < 2 and not seen[name] then list[#list + 1] = name; seen[name] = true end end
	if not (RM.Test and RM.Test.active) and GetRaidRosterInfo then
		for _, m in ipairs(members) do
			local ok, role = pcall(function() return select(10, GetRaidRosterInfo(m.index)) end)
			if ok and role == "MAINTANK" then add(m.name) end
		end
	end
	local tanks = {}
	for _, m in ipairs(members) do if IsTank(m.name) then tanks[#tanks + 1] = m.name end end
	table.sort(tanks, function(a, b)
		local x, y = groups[a] == 1 and 0 or 1, groups[b] == 1 and 0 or 1
		if x ~= y then return x < y end
		return a < b
	end)
	for _, n in ipairs(tanks) do add(n) end
	return list
end

-- Wunschgruppen: Aufstellung aus Discord, Main- und Offtank immer in Gruppe 1
---------------------------------------------------------------------------
-- Gruppen wie im Discord: Aufstellung übernehmen, Nachrücker sinnvoll einsortieren,
-- ohne Aufstellung dieselbe Classic-Einteilung wie der Bot (Gruppe 1 Tanks, Nahkampf-, Hexer-,
-- Fernkampf-, Jäger- und Heilergruppen, je Kampfgruppe ein Schamane bzw. Paladin)
---------------------------------------------------------------------------
local DEFAULT_ROLE = { WARRIOR = "melee", ROGUE = "melee", DEATHKNIGHT = "melee", MAGE = "ranged", WARLOCK = "ranged",
	HUNTER = "ranged", PRIEST = "heal", PALADIN = "heal", SHAMAN = "heal", DRUID = "heal" }

local function Entry(name)
	local su = RM.db.signup
	for _, e in ipairs((su and su.list) or {}) do if e.name == name then return e end end
end

local function RoleOf(name, class)
	local e = Entry(name)
	if RM.Gaps and RM.Gaps.RoleOf then return (RM.Gaps.RoleOf(name, class, e and e.role)) end
	if e and e.role and e.role ~= "" then return e.role end
	return (RM.Spec and RM.Spec.Role(name)) or DEFAULT_ROLE[class] or "melee"
end

-- Schamane (Horde) bzw. Paladin (Allianz): Totems/Auren wirken nur in der eigenen Gruppe
function S.SupportClass(players)
	for _, p in ipairs(players or {}) do if p.class == "SHAMAN" then return "SHAMAN" end end
	local f = UnitFactionGroup and UnitFactionGroup("player")
	if f == "Horde" then return "SHAMAN" end
	return "PALADIN"
end

-- Einordnung wie beim Bot: tank, melee, lock, caster, hunter, heal (+ support = Schamane/Paladin ohne Tank-Rolle)
function S.PlayerKind(p, supportCls)
	if p.role == "tank" then return "tank" end
	if supportCls and p.class == supportCls then return "support" end
	if p.role == "heal" then return "heal" end
	if p.class == "HUNTER" then return "hunter" end
	if p.class == "WARLOCK" or (p.class == "PRIEST" and p.role == "ranged") then return "lock" end
	if p.role == "ranged" then return "caster" end
	return "melee"
end

-- Classic-Einteilung (wie arrange_groups im Bot). players: { name, class, role } -> { {name, ...}, ... }
function S.ClassicGroups(players)
	local n = #players
	if n == 0 then return {} end
	local nGroups = math.min(8, math.ceil(n / 5))
	local supportCls = S.SupportClass(players)
	local supports, byKind = {}, {}
	local sorted = {}
	for _, p in ipairs(players) do sorted[#sorted + 1] = p end
	table.sort(sorted, function(a, b) return a.name:lower() < b.name:lower() end)
	for _, p in ipairs(sorted) do
		if p.class == supportCls and p.role ~= "tank" then
			supports[#supports + 1] = p
		else
			local k = S.PlayerKind(p, nil)
			byKind[k] = byKind[k] or {}
			table.insert(byKind[k], p)
		end
	end
	-- Unterstützer: zuerst die ohne Heiler-Rolle (Verstärker/Vergelter) in die Kampfgruppen
	table.sort(supports, function(a, b)
		local x, y = a.role ~= "heal" and 0 or 1, b.role ~= "heal" and 0 or 1
		if x ~= y then return x < y end
		return a.name:lower() < b.name:lower()
	end)
	byKind.melee = byKind.melee or {}
	local MELEE_ORDER = { WARRIOR = 0, DRUID = 1 }
	table.sort(byKind.melee, function(a, b)
		local x, y = MELEE_ORDER[a.class] or 2, MELEE_ORDER[b.class] or 2
		if x ~= y then return x < y end
		return a.name:lower() < b.name:lower()
	end)
	local function groupsFor(k) return math.ceil(#(byKind[k] or {}) / 4) end
	local plan = {}
	local function addPlan(k, c) for _ = 1, c do plan[#plan + 1] = k end end
	local function countPlan(k) local c = 0 for _, x in ipairs(plan) do if x == k then c = c + 1 end end return c end
	local function moveTo(from, to)
		byKind[to] = byKind[to] or {}
		for _, p in ipairs(byKind[from] or {}) do table.insert(byKind[to], p) end
		byKind[from] = nil
	end
	if byKind.tank and #byKind.tank > 0 then addPlan("tank", groupsFor("tank")) end
	addPlan("melee", groupsFor("melee"))
	addPlan("lock", groupsFor("lock"))
	addPlan("caster", groupsFor("caster"))
	if #(byKind.hunter or {}) >= 2 then addPlan("hunter", groupsFor("hunter")) else moveTo("hunter", "caster") end
	local coreCap = 4
	if #plan > nGroups then
		coreCap = 5     -- zu wenig Gruppen: Kampfgruppen voll, Unterstützer zu den Heilern
		while #plan > nGroups do
			local removed = false
			for _, k in ipairs({ "caster", "hunter", "lock", "melee", "tank" }) do
				local c = countPlan(k)
				if c > 1 or ((k == "hunter" or k == "lock") and c > 0) then
					for i, x in ipairs(plan) do if x == k then table.remove(plan, i) break end end
					if k == "hunter" or k == "lock" then
						moveTo(k, "caster")
						if countPlan("caster") == 0 then plan[#plan + 1] = "caster" end
					end
					removed = true
					break
				end
			end
			if not removed then break end
		end
		while #plan > nGroups do table.remove(plan) end
	end
	while #plan < nGroups do plan[#plan + 1] = "heal" end
	local groups = {}
	for i = 1, #plan do groups[i] = {} end
	local function place(p, idxs, cap)
		for _, i in ipairs(idxs) do
			if #groups[i] < cap then table.insert(groups[i], p) return true end
		end
		return false
	end
	local leftovers = {}
	for _, kind in ipairs({ "tank", "melee", "lock", "caster", "hunter" }) do
		local idxs = {}
		for i, k in ipairs(plan) do if k == kind then idxs[#idxs + 1] = i end end
		for j, p in ipairs(byKind[kind] or {}) do
			if #idxs == 0 then
				leftovers[#leftovers + 1] = p
			elseif kind == "tank" then
				-- Main- und Offtank zusammen in Gruppe 1, weitere Tanks danach
				if not place(p, idxs, coreCap) then leftovers[#leftovers + 1] = p end
			else
				-- gleichmäßig verteilen (z. B. 11 Nahkämpfer -> 4/4/3)
				local target = { idxs[((j - 1) % #idxs) + 1] }
				for _, i in ipairs(idxs) do target[#target + 1] = i end
				if not place(p, target, coreCap) then leftovers[#leftovers + 1] = p end
			end
		end
	end
	-- je Kampfgruppe ein Unterstützer
	local sup = {}
	for _, p in ipairs(supports) do sup[#sup + 1] = p end
	for i, k in ipairs(plan) do
		if k ~= "heal" and #sup > 0 and #groups[i] < 5 then table.insert(groups[i], table.remove(sup, 1)) end
	end
	-- Heiler: zuerst Heilergruppen, dann freie Plätze (Gruppen ohne Heiler zuerst)
	local healers = {}
	for _, p in ipairs(byKind.heal or {}) do healers[#healers + 1] = p end
	for _, p in ipairs(sup) do healers[#healers + 1] = p end
	for _, p in ipairs(leftovers) do healers[#healers + 1] = p end
	local healIdx = {}
	for i, k in ipairs(plan) do if k == "heal" then healIdx[#healIdx + 1] = i end end
	for _, p in ipairs(healers) do
		if not place(p, healIdx, 5) then
			local free = {}
			for i = 1, #groups do free[#free + 1] = i end
			table.sort(free, function(a, b)
				local function hasHeal(i)
					for _, x in ipairs(groups[i]) do if x.role == "heal" or x.class == supportCls then return 1 end end
					return 0
				end
				local x, y = hasHeal(a), hasHeal(b)
				if x ~= y then return x < y end
				if #groups[a] ~= #groups[b] then return #groups[a] < #groups[b] end
				return a < b
			end)
			place(p, free, 5)
		end
	end
	return groups
end

-- Anwesende mit Klasse und Rolle
local function PresentPlayers()
	local out = {}
	for _, m in ipairs(RM.RaidMembers()) do
		if m.name and m.class then out[#out + 1] = { name = m.name, class = m.class, role = RoleOf(m.name, m.class) } end
	end
	return out
end

-- Gruppen ohne Main-/Offtank-Regel: Discord-Aufstellung + Nachrücker, sonst Classic-Einteilung
function S.BaseGroups()
	local su = RM.db.signup
	local lineup = su and su.groups
	local players = PresentPlayers()
	local want = {}
	if #players == 0 then
		for n, g in pairs(lineup or {}) do want[n] = g end
		return want
	end
	local present = {}
	for _, p in ipairs(players) do present[p.name] = p end
	local hasLineup = false
	if lineup then for n in pairs(lineup) do if present[n] then hasLineup = true break end end end
	if not hasLineup then
		for g, list in ipairs(S.ClassicGroups(players)) do
			for _, p in ipairs(list) do want[p.name] = g end
		end
		return want
	end
	-- 1. Aufstellung aus Discord für alle, die da sind
	local supportCls = S.SupportClass(players)
	local count, openKind, kindIn = {}, {}, {}
	for name, g in pairs(lineup) do
		local p = present[name]
		local e = Entry(name)
		local kind = S.PlayerKind(p or { name = name, class = e and e.cls, role = RoleOf(name, e and e.cls) }, supportCls)
		kindIn[g] = kindIn[g] or {}
		kindIn[g][kind] = (kindIn[g][kind] or 0) + 1
		if p then
			want[name] = g
			count[g] = (count[g] or 0) + 1
		else
			-- Platz eines Fehlenden: hier gehört ein Nachrücker derselben Art hin
			openKind[g] = openKind[g] or {}
			openKind[g][kind] = (openKind[g][kind] or 0) + 1
		end
	end
	-- 2. Nachrücker (nicht in der Aufstellung): Tanks, Heiler, Unterstützer zuerst
	local ORDER = { tank = 1, heal = 2, support = 3, melee = 4, lock = 5, caster = 6, hunter = 7 }
	local extra = {}
	for _, p in ipairs(players) do
		if not want[p.name] then
			p.kind = S.PlayerKind(p, supportCls)
			extra[#extra + 1] = p
		end
	end
	table.sort(extra, function(a, b)
		if ORDER[a.kind] ~= ORDER[b.kind] then return ORDER[a.kind] < ORDER[b.kind] end
		return a.name < b.name
	end)
	local function free(g) return (count[g] or 0) < 5 end
	for _, p in ipairs(extra) do
		local best
		-- a) freier Platz eines Fehlenden derselben Art
		for g = 1, 8 do
			if free(g) and openKind[g] and (openKind[g][p.kind] or 0) > 0 then best = g break end
		end
		-- b) Gruppe, in der diese Art laut Aufstellung schon spielt (die meisten zuerst)
		if not best then
			local most = 0
			for g = 1, 8 do
				local c = kindIn[g] and kindIn[g][p.kind] or 0
				if free(g) and c > most then best, most = g, c end
			end
		end
		-- c) Heiler/Unterstützer: Gruppe ohne Heiler; sonst die leerste Gruppe
		if not best then
			local fewest = 6
			for g = 1, 8 do
				if free(g) then
					local c = count[g] or 0
					local healers = kindIn[g] and ((kindIn[g].heal or 0) + (kindIn[g].support or 0)) or 0
					local score = c + ((p.kind == "heal" or p.kind == "support") and healers or 0)
					if score < fewest then best, fewest = g, score end
				end
			end
		end
		if best then
			want[p.name] = best
			count[best] = (count[best] or 0) + 1
			if openKind[best] and (openKind[best][p.kind] or 0) > 0 then openKind[best][p.kind] = openKind[best][p.kind] - 1 end
			kindIn[best] = kindIn[best] or {}
			kindIn[best][p.kind] = (kindIn[best][p.kind] or 0) + 1
		end
	end
	return want
end

function S.WantedGroups()
	local want = S.BaseGroups()
	local mts = S.MainTanks()
	local isMT = {}
	for _, n in ipairs(mts) do isMT[n] = true end
	for _, n in ipairs(mts) do
		if want[n] ~= 1 then
			local old = want[n]
			local inOne, victim = 0, nil
			local names = {}
			for o, g in pairs(want) do if g == 1 then names[#names + 1] = o end end
			table.sort(names)
			for _, o in ipairs(names) do
				inOne = inOne + 1
				-- Platz machen: lieber ein Nicht-Tank als ein weiterer Tank
				if not isMT[o] and (not victim or (IsTank(victim) and not IsTank(o))) then victim = o end
			end
			if inOne >= 5 and victim then
				if not old then
					local count = {}
					for _, g in pairs(want) do count[g] = (count[g] or 0) + 1 end
					old = 8
					for g = 2, 8 do if (count[g] or 0) < 5 then old = g break end end
				end
				want[victim] = old
			end
			want[n] = 1
		end
	end
	return want
end

-- Ein Schritt: einen Spieler in seine Gruppe setzen oder tauschen. true = etwas getan
-- state.tries merkt sich jeden Zug: derselbe Zug wird nie mehrfach geschickt. Wichtig bei vollem Raid:
-- dort geht nur Tauschen, und ein doppelt geschickter Tausch macht sich selbst rückgängig (Hin und Her,
-- viele Anfragen an den Server in kurzer Zeit -> Verbindungsabbruch).
function S.ArrangeStep(state)
	state = state or { tries = {} }
	local want = S.WantedGroups()
	if not next(want) or not RM.InRaid() or not RM.IsAssist() then return false end
	if InCombatLockdown and InCombatLockdown() then return false end
	local cur, count, index = {}, {}, {}
	for i = 1, GetNumGroupMembers() do
		local name, _, subgroup = GetRaidRosterInfo(i)
		if name and subgroup then
			name = RM.Short(name)
			cur[name] = subgroup
			index[name] = i
			count[subgroup] = (count[subgroup] or 0) + 1
		end
	end
	-- feste Reihenfolge (Main-/Offtank zuerst, dann alphabetisch), damit jeder Lauf gleich entscheidet
	local names = {}
	for name in pairs(want) do if index[name] and cur[name] ~= want[name] then names[#names + 1] = name end end
	local first = {}
	for _, n in ipairs(S.MainTanks()) do first[n] = true end
	table.sort(names, function(a, b)
		if (first[a] or false) ~= (first[b] or false) then return first[a] and true or false end
		return a < b
	end)
	for _, name in ipairs(names) do
		local g = want[name]
		local i = index[name]
		if (count[g] or 0) < 5 then
			local key = name .. ">" .. g
			if (state.tries[key] or 0) < 2 then
				state.tries[key] = (state.tries[key] or 0) + 1
				SetRaidSubgroup(i, g)
				return true
			end
		else
			-- Tauschpartner: jemand in der Zielgruppe, der dort nicht hingehört – am liebsten einer, der in unsere Gruppe will
			local best
			for other, og in pairs(cur) do
				if og == g and want[other] ~= g then
					local a, b = name < other and name or other, name < other and other or name
					local key = a .. "<>" .. b
					if not state.tries[key] then
						if not best or want[other] == cur[name] then best = other end
					end
				end
			end
			if best then
				local a, b = name < best and name or best, name < best and best or name
				state.tries[a .. "<>" .. b] = 1
				SwapRaidSubgroup(i, index[best])
				return true
			end
		end
	end
	return false
end

S.ARRANGE_MAX_MOVES = 45   -- mehr Züge braucht ein 40er-Raid nie
local arrangeState

function S.IsArranging() return arrangeTicker ~= nil end

local function FinishArrange(silent, msg)
	if arrangeTicker then arrangeTicker:Cancel() end
	arrangeTicker = nil
	arrangeState = nil
	if not silent then RM.Print(msg or L["Gruppen eingeteilt."]) end
	RM.Fire("SIGNUP_CHANGED")
end

function S.ArrangeGroups(silent)
	if not next(S.WantedGroups()) then
		if not silent then RM.Print(L["Keine Gruppen-Aufstellung importiert (in Discord: /raid aufstellung, dann Export)."]) end
		return
	end
	if not RM.IsAssist() then
		if not silent then RM.Print(L["Zum Einteilen brauchst du Leiter- oder Assistentenrechte."]) end
		return
	end
	if arrangeTicker then return end      -- läuft schon: kein zweiter Durchgang parallel
	arrangeSteps = 0
	arrangeState = { tries = {}, waitUntil = 0, silent = silent }
	arrangeTicker = C_Timer.NewTicker(0.5, function()
		local st = arrangeState
		if not st then return end
		-- nach jedem Zug auf die Bestätigung vom Server warten (neue Gruppenliste), höchstens 3 Sek.
		if GetTime() < st.waitUntil then return end
		if InCombatLockdown and InCombatLockdown() then
			FinishArrange(silent, L["Gruppen einteilen abgebrochen – im Kampf geht das nicht."])
			return
		end
		if arrangeSteps >= S.ARRANGE_MAX_MOVES or not S.ArrangeStep(st) then
			FinishArrange(silent)
			return
		end
		arrangeSteps = arrangeSteps + 1
		st.waiting = true
		st.waitUntil = GetTime() + 3
	end)
end

-- neue Gruppenliste vom Server: der nächste Zug darf gleich kommen
RM.On("GROUP_ROSTER_UPDATE", function()
	local st = arrangeState
	if st and st.waiting then
		st.waiting = false
		st.waitUntil = GetTime() + 0.3
	end
end)

-- Beim Beitritt neuer Spieler automatisch nachsortieren
local lastArrange = 0
RM.On("GROUP_ROSTER_UPDATE", function()
	if not RM.db or not RM.db.config.autoGroups or arrangeTicker then return end
	if not next(S.WantedGroups()) then return end
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
	-- nicht gefunden / offline / abgelehnt: erst nach 10 Min. wieder versuchen
	for _, e in ipairs(su.list or {}) do if S.RecentlyFailed(e.name) then skip[e.name] = true end end
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
