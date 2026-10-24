-- RaidMaster - Skillungen
-- Liest die eigene Skillung aus, teilt sie mit allen Addon-Nutzern und
-- ermittelt bei Raidmitgliedern ohne Addon die Skillung per Betrachten.
-- Die Daten landen in RaidMasterDB.specs und werden vom Discord-Bot gelesen.

local _, RM = ...
local Spec = {}
RM.Spec = Spec

-- Talentbäume in der Reihenfolge des Spiels: Name, Hauptrolle, mögliche Rollen
Spec.TREES = {
	WARRIOR = { { "Waffen", "melee", { "melee", "tank" } }, { "Furor", "melee", { "melee", "tank" } }, { "Schutz", "tank" } },
	PALADIN = { { "Heilig", "heal" }, { "Schutz", "tank" }, { "Vergeltung", "melee" } },
	HUNTER  = { { "Tierherrschaft", "ranged" }, { "Treffsicherheit", "ranged" }, { "Überleben", "ranged" } },
	ROGUE   = { { "Meucheln", "melee" }, { "Kampf", "melee" }, { "Täuschung", "melee" } },
	PRIEST  = { { "Disziplin", "heal" }, { "Heilig", "heal" }, { "Schatten", "ranged" } },
	SHAMAN  = { { "Elementar", "ranged" }, { "Verstärkung", "melee" }, { "Wiederherstellung", "heal" } },
	MAGE    = { { "Arkan", "ranged" }, { "Feuer", "ranged" }, { "Frost", "ranged" } },
	WARLOCK = { { "Gebrechen", "ranged" }, { "Dämonologie", "ranged" }, { "Zerstörung", "ranged" } },
	DRUID   = { { "Gleichgewicht", "ranged" }, { "Wilder Kampf", "melee", { "melee", "tank" } }, { "Wiederherstellung", "heal" } },
}

Spec.ROLE_NAMES = { tank = "Tank", heal = "Heiler", melee = "Nahkampf", ranged = "Fernkampf" }

local MAX_AGE = 90 * 86400        -- ältere Einträge werden gelöscht
local RESCAN_AFTER = 24 * 3600    -- Skillung per Betrachten höchstens einmal am Tag neu holen

---------------------------------------------------------------------------
-- Auslesen
---------------------------------------------------------------------------
local function ActiveGroup(inspect)
	if GetActiveTalentGroup then
		local ok, g = pcall(GetActiveTalentGroup, inspect, false)
		if ok and type(g) == "number" then return g end
	end
	return nil
end

-- Punkte in einem Baum. Unterstützt beide Formate von GetTalentTabInfo:
-- Classic: name, icon, punkte, datei · neuer: id, name, beschreibung, icon, punkte, ...
local function TabPoints(tab, inspect, group)
	local r = { pcall(GetTalentTabInfo, tab, inspect, false, group) }
	if not r[1] then return nil end
	local points
	if type(r[2]) == "number" and type(r[3]) == "string" then
		points = r[6]
	else
		points = r[4]
	end
	if type(points) == "number" then return points end
	-- Notlösung: Ränge der einzelnen Talente zusammenzählen
	if not GetNumTalents or not GetTalentInfo then return nil end
	local okN, n = pcall(GetNumTalents, tab, inspect, false)
	if not okN or type(n) ~= "number" then return nil end
	local sum = 0
	for i = 1, n do
		local t = { pcall(GetTalentInfo, tab, i, inspect, false, group) }
		if t[1] and type(t[6]) == "number" then sum = sum + t[6] end
	end
	return sum
end

-- Liefert { a, b, c } oder nil
function Spec.ReadPoints(inspect)
	if not GetTalentTabInfo then return nil end
	local tabs = 3
	if GetNumTalentTabs then
		local ok, n = pcall(GetNumTalentTabs, inspect, false)
		if ok and type(n) == "number" and n > 0 then tabs = n end
	end
	local group = ActiveGroup(inspect)
	local points, total = {}, 0
	for tab = 1, math.min(tabs, 3) do
		local p = TabPoints(tab, inspect, group)
		if p == nil then return nil end
		points[tab] = p
		total = total + p
	end
	if total <= 0 then return nil end
	return points
end

-- Hauptbaum (meiste Punkte)
function Spec.MainTree(points)
	if not points then return nil end
	local best, bestPts = nil, -1
	for i = 1, 3 do
		local p = points[i] or 0
		if p > bestPts then best, bestPts = i, p end
	end
	if bestPts <= 0 then return nil end
	return best
end

---------------------------------------------------------------------------
-- Abfragen
---------------------------------------------------------------------------
-- Eintrag + Baum-Infos: entry, treeIndex, label, role, roles
function Spec.Get(name)
	if not RM.db or not name then return nil end
	local e = RM.db.specs[RM.Short(name)]
	if not e then return nil end
	local tree = Spec.MainTree(e.p)
	local info = tree and Spec.TREES[e.c] and Spec.TREES[e.c][tree]
	if not info then return e end
	return e, tree, info[1], info[2], info[3] or { info[2] }
end

function Spec.Role(name)
	local _, _, _, role = Spec.Get(name)
	return role
end

function Spec.CanRole(name, role)
	local _, _, _, _, roles = Spec.Get(name)
	if not roles then return nil end
	for _, r in ipairs(roles) do if r == role then return true end end
	return false
end

function Spec.PointsText(e)
	if not e or not e.p then return "" end
	return string.format("%d/%d/%d", e.p[1] or 0, e.p[2] or 0, e.p[3] or 0)
end

-- "Feuer (0/31/20)"
function Spec.Text(name)
	local e, _, label = Spec.Get(name)
	if not e then return nil end
	return (label or "?") .. " (" .. Spec.PointsText(e) .. ")"
end

---------------------------------------------------------------------------
-- Speichern
---------------------------------------------------------------------------
local function SamePoints(a, b)
	if not a or not b then return false end
	return a[1] == b[1] and a[2] == b[2] and a[3] == b[3]
end

-- Speichert eine Skillung. src: "self", "addon" oder "inspect"
function Spec.Store(name, class, points, src, at)
	if not RM.db or not name or not class or not points then return false end
	if not Spec.TREES[class] then return false end
	name = RM.Short(name)
	at = at or GetServerTime()
	local old = RM.db.specs[name]
	-- eigene Angaben eines Spielers sind verlässlicher als ein alter Scan
	if old and old.t and old.t > at then return false end
	local changed = not old or not SamePoints(old.p, points) or old.c ~= class
	RM.db.specs[name] = { c = class, p = { points[1] or 0, points[2] or 0, points[3] or 0 }, t = at, s = src }
	if changed then RM.Fire("SPEC_CHANGED", name) end
	return changed
end

function Spec.Prune()
	if not RM.db then return end
	local limit = GetServerTime() - MAX_AGE
	for name, e in pairs(RM.db.specs) do
		if type(e) ~= "table" or (e.t or 0) < limit then RM.db.specs[name] = nil end
	end
end

---------------------------------------------------------------------------
-- Eigene Skillung
---------------------------------------------------------------------------
local lastSent

function Spec.SendMine(channel)
	local e = RM.db and RM.db.specs[RM.Me()]
	if not e then return end
	local payload = { c = e.c, p = e.p, t = e.t }
	if channel then
		RM.Comm.Send("SPEC", payload, channel)
		return
	end
	if RM.MyGuild() then RM.Comm.Send("SPEC", payload, "GUILD") end
	if RM.InRaid() then RM.Comm.Send("SPEC", payload, "RAID") end
end

function Spec.UpdateMine(forceSend)
	if not RM.db then return end
	local points = Spec.ReadPoints(false)
	if not points then return end
	local _, class = UnitClass("player")
	local changed = Spec.Store(RM.Me(), class, points, "self")
	local key = Spec.PointsText(RM.db.specs[RM.Me()])
	if changed or forceSend or lastSent ~= key then
		lastSent = key
		Spec.SendMine()
	end
end

local pendingUpdate
local function ScheduleUpdate()
	if pendingUpdate then return end
	pendingUpdate = true
	C_Timer.After(3, function()
		pendingUpdate = nil
		Spec.UpdateMine()
	end)
end

RM.On("CHARACTER_POINTS_CHANGED", ScheduleUpdate)
RM.On("PLAYER_TALENT_UPDATE", ScheduleUpdate)
RM.On("ACTIVE_TALENT_GROUP_CHANGED", ScheduleUpdate)

RM.Listen("DB_READY", function() Spec.Prune() end)

RM.Listen("LOGIN", function()
	C_Timer.After(10, function() Spec.UpdateMine(true) end)
end)

---------------------------------------------------------------------------
-- Empfang
---------------------------------------------------------------------------
RM.Comm.Register("SPEC", function(sender, d)
	if type(d.p) ~= "table" or type(d.c) ~= "string" then return end
	local p = { tonumber(d.p[1]) or 0, tonumber(d.p[2]) or 0, tonumber(d.p[3]) or 0 }
	if p[1] + p[2] + p[3] <= 0 or p[1] + p[2] + p[3] > 100 then return end
	local at = tonumber(d.t) or GetServerTime()
	if at > GetServerTime() + 300 then at = GetServerTime() end
	Spec.Store(sender, d.c, p, "addon", at)
end)

-- Raidleiter fragt alle Skillungen im Raid ab
RM.Comm.Register("SPECREQ", function(sender, d, channel)
	C_Timer.After(math.random() * 3, function() Spec.SendMine("RAID") end)
end)

function Spec.RequestRaid()
	if RM.InRaid() then RM.Comm.Send("SPECREQ", {}, "RAID") end
end

-- Beim Betreten eines Raids die eigene Skillung mitteilen
local wasInRaid = false
RM.On("GROUP_ROSTER_UPDATE", function()
	local inRaid = RM.InRaid()
	if inRaid and not wasInRaid then
		C_Timer.After(4, function() Spec.SendMine("RAID") end)
	end
	wasInRaid = inRaid
end)

---------------------------------------------------------------------------
-- Betrachten (für Raidmitglieder ohne Addon)
---------------------------------------------------------------------------
local scan = { queue = {}, current = nil, running = false, zeros = 0 }
Spec.scan = scan
Spec.inspectUnsupported = false

local function HasAddon(name)
	local v = RM.Comm.versions and RM.Comm.versions[name]
	return v and (v.num or 0) >= 10500
end

local function NeedsScan(name)
	if name == RM.Me() then return false end
	if HasAddon(name) then return false end
	local e = RM.db.specs[name]
	if not e then return true end
	return GetServerTime() - (e.t or 0) > RESCAN_AFTER
end

local function UnitFor(name)
	for _, m in ipairs(RM.RaidMembers()) do
		if m.name == name then return "raid" .. m.index, m end
	end
end

local function InspectAllowed()
	if InCombatLockdown and InCombatLockdown() then return false end
	if InspectFrame and InspectFrame:IsShown() then return false end
	return true
end

function Spec.CanScan()
	return RM.InRaid() and (RM.IsAssist() or RM.CanEdit())
end

local function FinishCurrent()
	if scan.current and ClearInspectPlayer then pcall(ClearInspectPlayer) end
	scan.current = nil
end

local function ReadInspect()
	local cur = scan.current
	if not cur then return end
	local points = Spec.ReadPoints(true)
	if points then
		scan.zeros = 0
		Spec.Store(cur.name, cur.class, points, "inspect")
	elseif (UnitLevel(cur.unit) or 0) >= 60 then
		-- Stufe 60 ohne Punkte: Der Client liefert beim Betrachten keine Talente
		scan.zeros = scan.zeros + 1
		if scan.zeros >= 3 and not Spec.inspectUnsupported then
			Spec.inspectUnsupported = true
			RM.Print("Dieser Spielclient zeigt beim Betrachten keine Talente. Skillungen kommen nur von Spielern mit RaidMaster.")
		end
	end
	FinishCurrent()
	RM.Fire("SPEC_SCAN_CHANGED")
end

local function OnInspectReady(guid)
	local cur = scan.current
	if not cur then return end
	if guid and UnitGUID and UnitGUID(cur.unit) and UnitGUID(cur.unit) ~= guid then return end
	ReadInspect()
end
RM.On("INSPECT_READY", OnInspectReady)
RM.On("INSPECT_TALENT_READY", function() OnInspectReady(nil) end)

-- Raid nach fehlenden Skillungen durchsuchen. manual = per Knopf gestartet
function Spec.BuildQueue()
	wipe(scan.queue)
	for _, m in ipairs(RM.RaidMembers()) do
		if m.online and NeedsScan(m.name) then scan.queue[#scan.queue + 1] = m.name end
	end
	return #scan.queue
end

local function Step()
	if not scan.running then return end
	if scan.current then
		-- Zeitüberschreitung: weiter mit dem Nächsten
		if GetTime() - scan.current.started > 4 then
			FinishCurrent()
		else
			return
		end
	end
	if not RM.InRaid() or Spec.inspectUnsupported then
		scan.running = false
		RM.Fire("SPEC_SCAN_CHANGED")
		return
	end
	if not InspectAllowed() then return end
	while #scan.queue > 0 do
		local name = table.remove(scan.queue, 1)
		local unit, m = UnitFor(name)
		if unit and m.online and NeedsScan(name) and UnitIsConnected(unit)
			and (not CanInspect or CanInspect(unit))
			and (not CheckInteractDistance or CheckInteractDistance(unit, 1)) then
			scan.current = { name = name, class = m.class, unit = unit, started = GetTime() }
			NotifyInspect(unit)
			RM.Fire("SPEC_SCAN_CHANGED")
			return
		end
	end
	scan.running = false
	RM.Fire("SPEC_SCAN_CHANGED")
end

function Spec.StartScan(manual)
	if not Spec.CanScan() then
		if manual then RM.Print("Skillungen scannen dürfen Raidleiter, Assistenten und Offiziere.") end
		return
	end
	if Spec.inspectUnsupported then
		if manual then RM.Print("Dieser Spielclient zeigt beim Betrachten keine Talente.") end
		return
	end
	Spec.RequestRaid()
	local n = Spec.BuildQueue()
	if n == 0 then
		if manual then RM.Print("Alle Skillungen im Raid sind aktuell.") end
		return
	end
	scan.running = true
	if manual then RM.Print(n .. " Spieler ohne aktuelle Skillung werden betrachtet (nur in Reichweite, außerhalb des Kampfes).") end
	RM.Fire("SPEC_SCAN_CHANGED")
end

function Spec.StopScan()
	scan.running = false
	wipe(scan.queue)
	FinishCurrent()
	RM.Fire("SPEC_SCAN_CHANGED")
end

-- Ticker: ein Spieler alle 1,5 Sekunden; automatischer Scan alle 5 Minuten
local autoAt = 0
local function Tick()
	if not RM.db then return end
	if scan.running then
		Step()
	elseif RM.db.config.specScan and Spec.CanScan() and GetTime() >= autoAt then
		autoAt = GetTime() + 300
		Spec.StartScan(false)
	end
end
C_Timer.NewTicker(1.5, function()
	local ok, err = pcall(Tick)
	if not ok then
		-- bei einem Fehler den Scan beenden statt alle 1,5 Sekunden zu melden
		scan.running = false
		Spec.inspectUnsupported = true
		geterrorhandler()(err)
	end
end)

---------------------------------------------------------------------------
-- Liste für die Anzeige
---------------------------------------------------------------------------
-- Im Raid: alle Raidmitglieder, sonst alle bekannten Skillungen
function Spec.List()
	local rows = {}
	if RM.InRaid() then
		for _, m in ipairs(RM.RaidMembers()) do
			local e, tree, label, role = Spec.Get(m.name)
			rows[#rows + 1] = { name = m.name, class = m.class, entry = e, tree = tree, label = label, role = role }
		end
	else
		for name in pairs(RM.db.specs) do
			local e, tree, label, role = Spec.Get(name)
			rows[#rows + 1] = { name = name, class = e and e.c, entry = e, tree = tree, label = label, role = role }
		end
	end
	table.sort(rows, function(a, b)
		if (a.class or "") ~= (b.class or "") then return (a.class or "") < (b.class or "") end
		return a.name < b.name
	end)
	return rows
end
