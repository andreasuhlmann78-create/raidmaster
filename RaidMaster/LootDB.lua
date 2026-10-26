-- RaidMaster - eigene Beute-Datenbank
-- Merkt sich nach jedem Bosskill, welche Items im Lootfenster des Bosses lagen. So entsteht mit jedem Raid eine
-- eigene Beutetabelle für WoW Forever (welcher Boss droppt was, wie oft) – ohne fremde Datenquelle.
-- Der Uploader schickt RaidMasterDB.lootdb an den Bot; der Bot führt die Daten aller Uploader zusammen
-- (derselbe Kill zählt nur einmal) und zeigt die Beutetabelle je Raid im Loot-Kanal.
--
-- Aufbau (bewusst einfach und erweiterbar – neue Felder stören alte Daten nicht):
--   lootdb.v      = 1
--   lootdb.kills  = { { e = Encounter-ID, p = Topf (mc, ony, barrow, hyjal ...), n = Bossname, t = Zeit, z = Instanz,
--                       s = Gruppengröße, i = { Item-IDs } }, ... }   (neueste zuletzt, höchstens MAX_KILLS)
--   lootdb.items  = { [Item-ID] = { n = Name, q = Qualität, ic = Symbol, f = zuerst gesehen, l = zuletzt gesehen } }
--   lootdb.bosses = { [Encounter-ID] = { n = Name, p = Topf } }
-- Im Testmodus wird nichts gespeichert.

local ADDON, RM = ...
local L = RM.L
local LDB = {}
RM.LootDB = LDB

LDB.MAX_KILLS = 600        -- so viele Kills merkt sich das Addon (der Bot hebt alles auf)
LDB.WINDOW = 900           -- so lange nach dem Kill gehört das erste Lootfenster mit Beute zum Boss (Sek.)
LDB.MIN_QUALITY = 2        -- ab Grün (Boss-Beute; graue/weiße Items und Geld zählen nicht)

local lastKill            -- { e, p, n, t, at, done }

function LDB.Store()
	RM.db.lootdb = RM.db.lootdb or {}
	local s = RM.db.lootdb
	s.v = s.v or 1
	s.kills = s.kills or {}
	s.items = s.items or {}
	s.bosses = s.bosses or {}
	return s
end

local function Recording()
	if not RM.db then return false end
	if RM.Test and RM.Test.active then return false end
	if RM.db.config and RM.db.config.lootDB == false then return false end
	return true
end

-- Bosskill merken (das nächste Lootfenster mit Beute gehört zu ihm)
function LDB.OnKill(encounterID, encounterName, groupSize)
	if not Recording() or not encounterID then return end
	local boss = RM.Data.Bosses[encounterID]
	local pool = (boss and boss.pool) or (RM.DKP.CurrentInstancePool and RM.DKP.CurrentInstancePool())
		or (RM.db.session.active and RM.db.session.pool) or nil
	local zone = GetInstanceInfo and select(8, GetInstanceInfo()) or nil
	lastKill = { e = encounterID, p = pool, n = (boss and boss.name) or encounterName, t = GetServerTime(), at = GetTime(),
		z = zone, s = groupSize, done = false }
end

local function ItemIDFromLink(link)
	return type(link) == "string" and tonumber(link:match("item:(%d+)")) or nil
end

-- Lootfenster lesen: Items der Boss-Beute (ab Grün)
function LDB.ReadLootWindow()
	local ids, info = {}, {}
	if not GetNumLootItems then return ids, info end
	for slot = 1, GetNumLootItems() do
		local link = GetLootSlotLink and GetLootSlotLink(slot)
		local id = ItemIDFromLink(link)
		if id then
			local name, _, quality = (RM.GetItemInfo or GetItemInfo)(link)
			quality = quality or (RM.ItemQuality and RM.ItemQuality(link)) or 0
			if quality >= LDB.MIN_QUALITY then
				local icon = GetItemIcon and GetItemIcon(id)
				if not icon and GetLootSlotInfo then icon = (GetLootSlotInfo(slot)) end
				ids[#ids + 1] = id
				info[id] = { n = name or (link:match("%[(.-)%]")), q = quality, ic = icon }
			end
		end
	end
	return ids, info
end

-- einen Kill mit seiner Beute speichern (auch für Tests und den Import von außen)
function LDB.Record(kill, ids, info)
	if not kill or not kill.e or not ids or #ids == 0 then return false end
	local s = LDB.Store()
	local now = kill.t or GetServerTime()
	table.sort(ids)
	s.kills[#s.kills + 1] = { e = kill.e, p = kill.p, n = kill.n, t = now, z = kill.z, s = kill.s, i = ids }
	while #s.kills > LDB.MAX_KILLS do table.remove(s.kills, 1) end
	s.bosses[kill.e] = { n = kill.n, p = kill.p }
	for _, id in ipairs(ids) do
		local e = s.items[id] or {}
		local x = info and info[id] or {}
		e.n = x.n or e.n
		e.q = x.q or e.q
		e.ic = x.ic or e.ic
		e.f = e.f or now
		e.l = now
		s.items[id] = e
	end
	RM.Fire("LOOTDB_CHANGED", kill.e)
	return true
end

function LDB.OnLootOpened()
	if not Recording() or not lastKill or lastKill.done then return end
	if GetTime() - lastKill.at > LDB.WINDOW then lastKill = nil return end
	local ids, info = LDB.ReadLootWindow()
	if #ids == 0 then return end           -- leeres Fenster (z. B. Trash ohne Beute): auf die Boss-Leiche warten
	lastKill.done = true
	LDB.Record(lastKill, ids, info)
end

RM.On("ENCOUNTER_END", function(encounterID, encounterName, difficulty, groupSize, success)
	if success == 1 or success == true then LDB.OnKill(encounterID, encounterName, groupSize) end
end)
RM.On("LOOT_OPENED", function() LDB.OnLootOpened() end)

---------------------------------------------------------------------------
-- Abfragen
---------------------------------------------------------------------------
-- Beute eines Bosses: { {id, n, q, c = so oft gedroppt, rate = Anteil der Kills}, ... }, Anzahl Kills
function LDB.BossLoot(encounterID)
	local s = RM.db and RM.db.lootdb
	if not s then return {}, 0 end
	local count, kills = {}, 0
	for _, k in ipairs(s.kills or {}) do
		if k.e == encounterID then
			kills = kills + 1
			for _, id in ipairs(k.i or {}) do count[id] = (count[id] or 0) + 1 end
		end
	end
	local list = {}
	for id, c in pairs(count) do
		local it = (s.items or {})[id] or {}
		list[#list + 1] = { id = id, n = it.n, q = it.q, c = c, rate = kills > 0 and c / kills or 0 }
	end
	table.sort(list, function(a, b)
		if a.c ~= b.c then return a.c > b.c end
		return a.id < b.id
	end)
	return list, kills
end

-- nur die Item-IDs (für den Testmodus)
function LDB.ItemIDs(encounterID)
	local list, kills = LDB.BossLoot(encounterID)
	local ids = {}
	for _, x in ipairs(list) do ids[#ids + 1] = x.id end
	return ids, kills
end

-- bekannte Bosse eines Raids (Reihenfolge des ersten Kills)
function LDB.BossesForPool(pool)
	local s = RM.db and RM.db.lootdb
	local out, seen = {}, {}
	for _, k in ipairs((s and s.kills) or {}) do
		if k.p == pool and not seen[k.e] then
			seen[k.e] = true
			out[#out + 1] = { id = k.e, name = (s.bosses[k.e] and s.bosses[k.e].n) or k.n or ("Boss " .. k.e) }
		end
	end
	return out
end

function LDB.Stats()
	local s = RM.db and RM.db.lootdb
	if not s then return 0, 0, 0 end
	local bosses, items = 0, 0
	for _ in pairs(s.bosses or {}) do bosses = bosses + 1 end
	for _ in pairs(s.items or {}) do items = items + 1 end
	return #(s.kills or {}), bosses, items
end

-- Text für den Chat: "/rm beute <Boss>"
function LDB.PrintBoss(query)
	local s = RM.db and RM.db.lootdb
	if not s or not next(s.bosses or {}) then
		RM.Print(L["Die Beute-Datenbank ist noch leer – sie füllt sich mit jedem Bosskill."])
		return
	end
	query = (query or ""):lower()
	local found = 0
	for id, b in pairs(s.bosses) do
		if query == "" or (b.n and b.n:lower():find(query, 1, true)) then
			local list, kills = LDB.BossLoot(id)
			RM.Print(string.format(L["%s: %d Kills, %d verschiedene Items"], b.n or ("Boss " .. id), kills, #list))
			for i, x in ipairs(list) do
				if i > 12 then break end
				local _, link = (RM.GetItemInfo or GetItemInfo)(x.id)
				RM.Print(string.format("  %s  %d/%d (%d%%)", link or x.n or ("item:" .. x.id), x.c, kills, math.floor(x.rate * 100 + 0.5)))
			end
			found = found + 1
		end
	end
	if found == 0 then RM.Print(string.format(L["Kein Boss mit '%s' in der Beute-Datenbank."], query)) end
end
