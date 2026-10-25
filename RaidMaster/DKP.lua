-- RaidMaster - DKP
-- DKP-Töpfe pro Raid, Punktestände, Log mit Rückgängig, Decay, Ersatzbank, Snapshot und Export

local ADDON, RM = ...
local L = RM.L
local DKP = {}
RM.DKP = DKP

local LOG_LIMIT = 1000
local SNAP_LOG = 60
local entryCounter = 0
DKP.FORMAT = 2   -- Datenformat 2 = DKP-Töpfe pro Raid

DKP.KindNames = {
	start = L["Raidstart"],
	["end"] = L["Raidende"],
	boss = L["Bosskill"],
	item = L["Item"],
	manual = L["Anpassung"],
	decay = L["Decay"],
	undo = L["Rückgängig"],
}

---------------------------------------------------------------------------
-- DKP-Töpfe
---------------------------------------------------------------------------
-- Alte Daten (eine DKP-Zahl pro Spieler) in den Topf "mc" überführen
function DKP.Migrate(data)
	if not data then return end
	data.pools = data.pools or {}
	data.knownBosses = data.knownBosses or {}
	DKP.InitEarned(data)
	for _, p in pairs(data.players or {}) do
		if type(p) == "table" then
			p.d = p.d or {}
			if p.dkp ~= nil then
				p.d.mc = (p.d.mc or 0) + p.dkp
				p.dkp = nil
			end
		end
	end
	-- Früher automatisch angelegte Töpfe "i<Instanz-ID>" dem jetzt bekannten Raid zuordnen
	local remap = {}
	for key in pairs(data.pools) do
		local id = tonumber(tostring(key):match("^i(%d+)$"))
		if id then
			for _, def in ipairs(RM.Data.AllRaids) do
				local ids = def.ids or {}
				if ids[id] == true then remap[key] = def.key end
				for _, v in ipairs(ids) do if v == id then remap[key] = def.key end end
				if remap[key] then break end
			end
		end
	end
	if next(remap) then
		for _, p in pairs(data.players or {}) do
			if type(p) == "table" and p.d then
				for old, new in pairs(remap) do
					if p.d[old] then p.d[new] = RM.Round((p.d[new] or 0) + p.d[old]); p.d[old] = nil end
					if p.e and p.e[old] then p.e[new] = RM.Round((p.e[new] or 0) + p.e[old]); p.e[old] = nil end
				end
			end
		end
		for _, e in ipairs(data.log or {}) do
			if e.pool and remap[e.pool] then e.pool = remap[e.pool]; e.pn = nil end
		end
		for _, b in pairs(data.knownBosses) do
			if b.p and remap[b.p] then b.p = remap[b.p] end
		end
		for old in pairs(remap) do data.pools[old] = nil end
	end
end

function DKP.PoolName(key, data)
	local def = RM.Data.RaidByKey(key)
	if def then return def.name end
	data = data or RM.db.data
	local custom = data and data.pools and data.pools[key]
	return (custom and custom.n) or key
end

function DKP.PoolShort(key, data)
	local def = RM.Data.RaidByKey(key)
	if def then return def.short or def.name end
	return DKP.PoolName(key, data)
end

-- Unbekannten Raid als eigenen Topf anlegen
function DKP.EnsurePool(key, name, data)
	data = data or RM.db.data
	if RM.Data.Pools[key] then return end
	data.pools = data.pools or {}
	if not data.pools[key] then
		data.pools[key] = { n = name or key }
		RM.Print(L["Neuer DKP-Topf angelegt: "] .. (name or key))
	end
end

-- Alle Töpfe eines Datensatzes in fester Reihenfolge
function DKP.PoolList(data)
	data = data or RM.db.data
	local list, seen = {}, {}
	for _, key in ipairs(RM.Data.PoolOrder) do
		list[#list + 1] = key
		seen[key] = true
	end
	local extra = {}
	for key in pairs(data.pools or {}) do
		if not seen[key] then extra[#extra + 1] = key; seen[key] = true end
	end
	for _, p in pairs(data.players or {}) do
		for key in pairs(p.d or {}) do
			if not seen[key] then extra[#extra + 1] = key; seen[key] = true end
		end
	end
	-- aktueller Raid (Instanz oder laufende Sitzung) immer mit anbieten
	local cur = (RM.db and RM.db.session and RM.db.session.active and RM.db.session.pool) or nil
	for _, key in ipairs({ DKP.CurrentInstancePool and DKP.CurrentInstancePool(true), cur }) do
		if key and not seen[key] then extra[#extra + 1] = key; seen[key] = true end
	end
	local function idx(key)
		local def = RM.Data.RaidByKey(key)
		return def and def.idx or 100000
	end
	table.sort(extra, function(a, b)
		local ia, ib = idx(a), idx(b)
		if ia ~= ib then return ia < ib end
		return a < b
	end)
	for _, key in ipairs(extra) do list[#list + 1] = key end
	return list
end

-- Topf der aktuellen Raid-Instanz (nil außerhalb eines Raids)
-- noCreate = true: unbekannten Raid nicht als neuen Topf anlegen
function DKP.CurrentInstancePool(noCreate)
	if not GetInstanceInfo then return nil end
	local name, instanceType, _, _, _, _, _, instanceID = GetInstanceInfo()
	if instanceType ~= "raid" then return nil end
	local map = RM.db.config.instanceMap
	if instanceID and map[instanceID] then return map[instanceID] end
	local lname = (name or ""):lower()
	for key, def in pairs(RM.Data.Pools) do
		if def.ids and instanceID and def.ids[instanceID] then return key end
		for _, m in ipairs(def.match or {}) do
			if lname:find(m, 1, true) then return key end
		end
		-- übersetzter Raidname (für Spielclients in anderen Sprachen)
		if def.name and def.name ~= "" and lname:find(def.name:lower(), 1, true) then return key end
	end
	if not instanceID then return nil end
	local key = "i" .. instanceID
	if noCreate then return (RM.db.data.pools or {})[key] and key or nil end
	DKP.EnsurePool(key, name)
	return key
end

-- Topf für Buchungen des Offiziers
function DKP.ActivePool()
	local inst = DKP.CurrentInstancePool()
	if inst then return inst end
	local s = RM.db.session
	if s.active and s.pool then return s.pool end
	return RM.db.config.activePool or "mc"
end

-- Topf, der beim Öffnen der Anzeige vorausgewählt ist
function DKP.DefaultViewPool()
	return DKP.CurrentInstancePool() or (RM.db.session.active and RM.db.session.pool) or RM.db.config.activePool or "mc"
end

-- Aktuelle Instanz fest einem Topf zuordnen (z. B. wenn der Raidname nicht erkannt wurde)
function DKP.MapCurrentInstance(key)
	if not GetInstanceInfo then return end
	local _, instanceType, _, _, _, _, _, instanceID = GetInstanceInfo()
	if instanceType == "raid" and instanceID then
		RM.db.config.instanceMap[instanceID] = key
	end
end

---------------------------------------------------------------------------
-- Stände lesen
---------------------------------------------------------------------------
local function PoolValue(p, pool)
	if not p then return 0 end
	return (p.d and p.d[pool]) or 0
end
DKP.PoolValue = PoolValue

-- Insgesamt verdiente DKP je Spieler und Raid (Raidstart, Bosskills, Raidende, Gutschriften) –
-- ohne Abzüge für Items und Decay. Wird bei jeder Buchung mitgezählt (p.e[Topf]).
DKP.EARN_KINDS = { start = true, ["end"] = true, boss = true, manual = true }
function DKP.Earned(p, pool)
	if not p then return 0 end
	return (p.e and p.e[pool]) or 0
end

local function AddEarned(p, pool, amount)
	if not amount or amount == 0 then return end
	p.e = p.e or {}
	p.e[pool] = math.max(0, RM.Round((p.e[pool] or 0) + amount))
end

-- Einmalig aus dem vorhandenen Log nachrechnen (ältere Daten ohne Zähler)
function DKP.InitEarned(data)
	if not data or data.earnedInit then return end
	for _, p in pairs(data.players or {}) do
		if type(p) == "table" then p.e = {} end
	end
	for _, e in ipairs(data.log or {}) do
		if DKP.EARN_KINDS[e.k] and not e.u then
			local pool = e.pool or "mc"
			for name, delta in pairs(e.d or {}) do
				local p = data.players[name]
				if type(p) == "table" and delta > 0 then AddEarned(p, pool, delta) end
			end
		end
	end
	data.earnedInit = true
end

-- Gesamtpunkte eines Raid-Topfes: Summe aller DKP-Stände und Zahl der Spieler mit Stand
function DKP.PoolTotal(data, pool)
	data = data or RM.db.data
	local total, count, earned = 0, 0, 0
	for _, p in pairs(data.players or {}) do
		local v = PoolValue(p, pool)
		if v and v ~= 0 then
			total = total + v
			count = count + 1
		end
		earned = earned + DKP.Earned(p, pool)
	end
	return total, count, earned
end

function DKP.Get(name, pool)
	return PoolValue(RM.db.data.players[RM.Short(name)], pool or DKP.ActivePool())
end

---------------------------------------------------------------------------
-- Datensätze: eigene Gilde (RM.db.data) und fremde Raid-Gilden (nur Ansicht)
---------------------------------------------------------------------------
local FOREIGN_LIMIT = 3

-- Liefert Datensatz und ob es der eigene ist
function DKP.Dataset(guild)
	if not guild or guild == "" or guild == RM.MyGuild() then return RM.db.data, true end
	return RM.db.foreign[guild], false
end

function DKP.GetFor(guild, name, pool)
	local data = DKP.Dataset(guild)
	local p = data and data.players[RM.Short(name)]
	return PoolValue(p, pool or "mc")
end

function DKP.ForeignStore(guild)
	local f = RM.db.foreign
	if not f[guild] then
		f[guild] = { version = 0, players = {}, log = {}, firstKills = {}, lastDecay = 0, received = 0, pools = {}, knownBosses = {} }
		-- nur die letzten Gilden behalten
		local list = {}
		for g, d in pairs(f) do list[#list + 1] = { g = g, t = d.received or 0 } end
		table.sort(list, function(a, b) return a.t > b.t end)
		for i = FOREIGN_LIMIT + 1, #list do
			if list[i].g ~= guild then f[list[i].g] = nil end
		end
	end
	return f[guild]
end

-- Datensatz für die Anzeige (eigene Gilde oder gewählte Raid-Gilde)
function DKP.View()
	local g = RM.UI and RM.UI.viewGuild
	if g and RM.db.foreign[g] then return RM.db.foreign[g], false, g end
	return RM.db.data, true, RM.MyGuild()
end

function DKP.EnsurePlayer(name, class)
	name = RM.Short(name)
	local players = RM.db.data.players
	local p = players[name]
	if not p then
		p = { d = {} }
		players[name] = p
	end
	p.d = p.d or {}
	class = class or RM.guild.class[name]
	if class and p.c ~= class then p.c = class end
	return p
end

local function FindIn(data, id)
	for i, e in ipairs(data.log) do
		if e.id == id then return e, i end
	end
end

function DKP.FindEntry(id)
	return FindIn(RM.db.data, id)
end

-- Eintrag auf einen Datensatz anwenden (lokal erzeugt oder per Sync empfangen)
function DKP.ApplyEntryTo(data, e, isMain)
	if FindIn(data, e.id) then return false end
	local pool = e.pool or "mc"
	if e.pn and not RM.Data.Pools[pool] then
		data.pools = data.pools or {}
		data.pools[pool] = data.pools[pool] or { n = e.pn }
	end
	for name, delta in pairs(e.d or {}) do
		local p
		if isMain then
			p = DKP.EnsurePlayer(name)
		else
			p = data.players[name]
			if not p then p = { d = {} }; data.players[name] = p end
			p.d = p.d or {}
		end
		p.d[pool] = RM.Round((p.d[pool] or 0) + delta)
		if DKP.EARN_KINDS[e.k] and delta > 0 then AddEarned(p, pool, delta) end
	end
	if e.k == "undo" and e.r then
		local target = FindIn(data, e.r)
		if target then
			-- rückgängig gemachte Gutschrift zählt nicht mehr als verdient
			if DKP.EARN_KINDS[target.k] and not target.u then
				for name, delta in pairs(target.d or {}) do
					local p = data.players[name]
					if p and delta > 0 then AddEarned(p, target.pool or pool, -delta) end
				end
			end
			target.u = true
		end
	elseif e.k == "decay" then
		data.lastDecay = e.t
	elseif e.k == "boss" and e.b then
		data.firstKills[e.b] = true
		data.knownBosses = data.knownBosses or {}
		if not RM.Data.Bosses[e.b] then
			data.knownBosses[e.b] = { n = e.bn or (L["Boss "] .. e.b), p = pool }
		end
	end
	table.insert(data.log, e)
	while #data.log > LOG_LIMIT do table.remove(data.log, 1) end
	return true
end

function DKP.ApplyEntry(e)
	return DKP.ApplyEntryTo(RM.db.data, e, true)
end

-- Neue Buchung erstellen (nur Offiziere)
function DKP.NewEntry(kind, text, deltas, item, ref, extra)
	if not RM.CanEdit() then
		RM.Print(L["Keine Berechtigung: Nur Offiziere dürfen DKP ändern."])
		return nil
	end
	if not deltas or not next(deltas) then return nil end
	entryCounter = entryCounter + 1
	local now = GetServerTime()
	local e = { id = now .. "-" .. RM.Me() .. "-" .. entryCounter, t = now, by = RM.Me(), k = kind, x = text, d = deltas, i = item, r = ref }
	if extra then
		for k, v in pairs(extra) do e[k] = v end
	end
	e.pool = e.pool or DKP.ActivePool()
	if not RM.Data.Pools[e.pool] then e.pn = DKP.PoolName(e.pool) end
	local data = RM.db.data
	local pv = data.version
	local v = math.max(pv + 1, now)
	DKP.ApplyEntry(e)
	data.version = v
	local msg = { pv = pv, v = v, e = e, g = RM.MyGuild() }
	RM.Comm.Send("ENTRY", msg, "GUILD")
	-- auch an den Raid, damit gildenfremde Mitspieler den Stand sehen
	if RM.InRaid() then RM.Comm.Send("ENTRY", msg, "RAID") end
	RM.Fire("DATA_CHANGED")
	return e
end

---------------------------------------------------------------------------
-- Buchungen
---------------------------------------------------------------------------
-- Namen, die bei Raid-Buchungen Punkte erhalten (Raid + Ersatzbank)
function DKP.RaidRecipients()
	local s = RM.db.data.settings
	local names = {}
	for _, m in ipairs(RM.RaidMembers()) do
		if m.online or not s.onlyOnline then
			names[m.name] = m.class or true
		end
	end
	if s.standbyGetsDKP then
		for name in pairs(RM.db.config.standby) do
			if not names[name] then names[name] = true end
		end
	end
	return names
end

function DKP.AwardRaid(amount, kind, text, extra, pool)
	if not amount or amount == 0 then return end
	local deltas = {}
	for name, class in pairs(DKP.RaidRecipients()) do
		if type(class) == "string" then DKP.EnsurePlayer(name, class) end
		deltas[name] = amount
	end
	extra = extra or {}
	extra.pool = pool or extra.pool
	return DKP.NewEntry(kind, text, deltas, nil, nil, extra)
end

function DKP.Adjust(name, amount, reason, pool)
	name = RM.Short(name)
	if not name or name == "" or not amount or amount == 0 then return end
	return DKP.NewEntry("manual", (reason and reason ~= "") and reason or L["Manuelle Anpassung"], { [name] = amount }, nil, nil, { pool = pool })
end

function DKP.ChargeItem(name, amount, link, pool)
	return DKP.NewEntry("item", L["Item gewonnen"], { [RM.Short(name)] = -amount }, link, nil, { pool = pool })
end

function DKP.Undo(id)
	local e = DKP.FindEntry(id)
	if not e then return end
	if e.u then RM.Print(L["Diese Buchung wurde bereits rückgängig gemacht."]) return end
	if e.k == "undo" then RM.Print(L["Eine Rückgängig-Buchung kann nicht rückgängig gemacht werden."]) return end
	local deltas = {}
	for name, delta in pairs(e.d or {}) do deltas[name] = -delta end
	local label = (DKP.KindNames[e.k] or e.k) .. ": " .. (e.x or "")
	return DKP.NewEntry("undo", L["Rückgängig – "] .. label, deltas, e.i, e.id, { pool = e.pool or "mc" })
end

-- Decay für einen Topf oder (pool = nil) für alle Töpfe
function DKP.ApplyDecay(pool)
	local pct = RM.db.data.settings.decayPct or 0
	if pct <= 0 then RM.Print(L["Decay ist auf 0 % eingestellt."]) return end
	local pools = pool and { pool } or DKP.PoolList()
	local count = 0
	for _, key in ipairs(pools) do
		local deltas = {}
		for name, p in pairs(RM.db.data.players) do
			local v = PoolValue(p, key)
			if v > 0 then
				local cut = RM.Round(v * pct / 100)
				if cut > 0 then deltas[name] = -cut end
			end
		end
		if next(deltas) then
			DKP.NewEntry("decay", pct .. L[" % Decay"], deltas, nil, nil, { pool = key })
			count = count + 1
		end
	end
	if count == 0 then RM.Print(L["Niemand hat positive DKP."]) end
end

function DKP.AddPlayer(name)
	name = RM.Short(name)
	if not name or name == "" then return end
	name = name:sub(1, 1):upper() .. name:sub(2):lower()
	if RM.db.data.players[name] then return name end
	-- Spieler mit 0 DKP anlegen, über eine 0-Buchung nicht möglich -> Snapshot verteilen
	DKP.EnsurePlayer(name)
	if RM.CanEdit() then
		RM.db.data.version = math.max(RM.db.data.version + 1, GetServerTime())
		RM.Comm.BroadcastSnapshot()
	end
	RM.Fire("DATA_CHANGED")
	return name
end

---------------------------------------------------------------------------
-- Ersatzbank (lokal beim Raidleiter/Offizier)
---------------------------------------------------------------------------
function DKP.ToggleStandby(name)
	name = RM.Short(name)
	if not name or name == "" then return end
	local sb = RM.db.config.standby
	if sb[name] then sb[name] = nil else sb[name] = true end
	RM.Fire("DATA_CHANGED")
end

function DKP.IsStandby(name)
	return RM.db.config.standby[RM.Short(name)] and true or false
end

---------------------------------------------------------------------------
-- Einstellungen verteilen
---------------------------------------------------------------------------
function DKP.SettingsChanged()
	if not RM.CanEdit() then
		RM.Print(L["Nur Offiziere können die gemeinsamen DKP-Einstellungen ändern."])
		return
	end
	RM.db.data.version = math.max(RM.db.data.version + 1, GetServerTime())
	RM.Comm.BroadcastSnapshot()
	RM.Fire("DATA_CHANGED")
	RM.Print(L["Einstellungen gespeichert und an die Gilde verteilt."])
end

---------------------------------------------------------------------------
-- Snapshot
---------------------------------------------------------------------------
function DKP.MakeSnapshot(logCount)
	local data = RM.db.data
	local log = {}
	local first = math.max(1, #data.log - (logCount or SNAP_LOG) + 1)
	for i = first, #data.log do log[#log + 1] = data.log[i] end
	return {
		v = data.version, g = RM.MyGuild(), fmt = DKP.FORMAT, p = data.players, s = data.settings,
		f = data.firstKills, ld = data.lastDecay, l = log, po = data.pools, kb = data.knownBosses,
	}
end

function DKP.ImportSnapshot(s)
	DKP.ImportSnapshotTo(RM.db.data, s, true)
end

-- Fremden Raid-Datensatz übernehmen (nur Ansicht)
function DKP.ImportForeign(s, sender)
	local store = DKP.ForeignStore(s.g)
	local isNew = (store.version or 0) == 0
	DKP.ImportSnapshotTo(store, s, false)
	store.received = GetServerTime()
	store.source = sender
	if RM.UI and not RM.UI.viewGuild and (not RM.MyGuild() or RM.InRaid()) then
		RM.UI.viewGuild = s.g
	end
	if isNew then
		RM.Print(string.format(L["DKP-Tabelle der Gilde <%s> empfangen (von %s). Auf der DKP-Seite umschaltbar."], s.g, sender))
	end
	RM.Fire("DATA_CHANGED")
end

function DKP.ImportSnapshotTo(data, s, isMain)
	if type(s.p) == "table" then data.players = s.p end
	if type(s.s) == "table" then
		data.settings = s.s
		if isMain then RM.FillDefaults(data.settings, RM.DEFAULT_SETTINGS) end
	end
	if type(s.f) == "table" then data.firstKills = s.f end
	if type(s.po) == "table" then data.pools = s.po end
	if type(s.kb) == "table" then data.knownBosses = s.kb end
	data.lastDecay = s.ld or data.lastDecay
	if type(s.l) == "table" then
		local byId = {}
		local merged = {}
		for _, e in ipairs(data.log) do
			if not byId[e.id] then byId[e.id] = true; merged[#merged + 1] = e end
		end
		for _, e in ipairs(s.l) do
			if e.id and not byId[e.id] then
				byId[e.id] = true
				merged[#merged + 1] = e
			elseif e.id and e.u then
				for _, m in ipairs(merged) do if m.id == e.id then m.u = true end end
			end
		end
		table.sort(merged, function(a, b)
			if a.t == b.t then return a.id < b.id end
			return (a.t or 0) < (b.t or 0)
		end)
		while #merged > LOG_LIMIT do table.remove(merged, 1) end
		data.log = merged
	end
	data.version = s.v or data.version
	-- Stand von älteren Versionen (ohne Töpfe) umwandeln
	DKP.Migrate(data)
	RM.Fire("DATA_CHANGED")
end

---------------------------------------------------------------------------
-- Export
---------------------------------------------------------------------------
function DKP.SortedPlayers(pool, data)
	data = data or RM.db.data
	local list = {}
	for name, p in pairs(data.players) do
		list[#list + 1] = { name = name, dkp = PoolValue(p, pool), class = p.c }
	end
	table.sort(list, function(a, b)
		if a.dkp == b.dkp then return a.name < b.name end
		return a.dkp > b.dkp
	end)
	return list
end

function DKP.ExportText()
	local data = RM.db.data
	local pools = DKP.PoolList(data)
	local lines = { L["RaidMaster DKP-Export "] .. date("%d.%m.%Y %H:%M"), "" }
	local header = { L["Name"], L["Klasse"] }
	for _, key in ipairs(pools) do header[#header + 1] = DKP.PoolName(key, data) end
	lines[#lines + 1] = table.concat(header, ";")
	local names = {}
	for name in pairs(data.players) do names[#names + 1] = name end
	table.sort(names)
	for _, name in ipairs(names) do
		local p = data.players[name]
		local row = { name, p.c or "" }
		for _, key in ipairs(pools) do row[#row + 1] = tostring(PoolValue(p, key)) end
		lines[#lines + 1] = table.concat(row, ";")
	end
	lines[#lines + 1] = ""
	lines[#lines + 1] = L["Datum;Von;Topf;Art;Text;Item;Betrag;Spieler;Rückgängig"]
	local log = data.log
	for i = #log, 1, -1 do
		local e = log[i]
		local count, amount, uniform = 0, nil, true
		local entryNames = {}
		for name, d in pairs(e.d or {}) do
			count = count + 1
			if amount and amount ~= d then uniform = false end
			amount = amount or d
			entryNames[#entryNames + 1] = name
		end
		table.sort(entryNames)
		local amountText
		if count == 1 then
			amountText = tostring(amount)
		elseif uniform then
			amountText = tostring(amount) .. L[" (je)"]
		else
			amountText = "verschieden"
			wipe(entryNames)
			for name, d in pairs(e.d or {}) do entryNames[#entryNames + 1] = name .. " " .. d end
			table.sort(entryNames)
		end
		local item = e.i and (e.i:match("|h%[(.-)%]|h") or e.i) or ""
		lines[#lines + 1] = string.format("%s;%s;%s;%s;%s;%s;%s;%s;%s",
			date("%d.%m.%Y %H:%M", e.t or 0), e.by or "", DKP.PoolName(e.pool or "mc", data), DKP.KindNames[e.k] or e.k or "",
			e.x or "", item, amountText, table.concat(entryNames, ","), e.u and "ja" or "")
	end
	return table.concat(lines, "\n")
end

-- Kurzüberblick aller Töpfe eines Spielers, z. B. "MC 40 · Ony 20"
function DKP.Summary(name, data)
	data = data or RM.db.data
	local p = data.players[RM.Short(name)]
	local parts = {}
	for _, key in ipairs(DKP.PoolList(data)) do
		local v = PoolValue(p, key)
		if v ~= 0 then parts[#parts + 1] = DKP.PoolShort(key, data) .. " " .. v end
	end
	if #parts == 0 then return L["0 DKP"] end
	return table.concat(parts, " · ")
end

---------------------------------------------------------------------------
-- Klassen aktuell halten
---------------------------------------------------------------------------
RM.On("GROUP_ROSTER_UPDATE", function()
	if not RM.db then return end
	for _, m in ipairs(RM.RaidMembers()) do
		local p = RM.db.data.players[m.name]
		if p and m.class and p.c ~= m.class then p.c = m.class end
	end
end)

---------------------------------------------------------------------------
-- Antwort auf "!dkp" per Flüstern
---------------------------------------------------------------------------
RM.On("CHAT_MSG_WHISPER", function(msg, sender)
	if not RM.db or not RM.db.config.whisperReplies then return end
	local m = (msg or ""):lower()
	if not m:match("^%s*!dkp") then return end
	if not RM.CanEdit() then return end
	-- Nur einer soll antworten: Plündermeister oder wer den Raid gestartet hat
	if not (RM.IAmMasterLooter() or RM.db.session.active) then return end
	local name = RM.Short(sender)
	local target = m:match("^%s*!dkp%s+(%S+)")
	if target then
		target = target:sub(1, 1):upper() .. target:sub(2)
		SendChatMessage(string.format("[RaidMaster] %s: %s", target, DKP.Summary(target)), "WHISPER", nil, sender)
	else
		SendChatMessage(string.format("[RaidMaster] Deine DKP: %s", DKP.Summary(name)), "WHISPER", nil, sender)
	end
end)
