-- RaidMaster - eigene Beute-Datenbank
-- Merkt sich in Raids jedes Lootfenster: nach einem Bosskill die Beute des Bosses, sonst die zufälligen Drops
-- vom Trash. Jeder Kill zählt – egal wie oft ein Boss im Lauf der Raids getötet wird. So entsteht mit jedem Raid
-- eine eigene Beutetabelle für WoW Forever (welcher Boss droppt was, wie oft, was droppt der Trash) – ohne fremde
-- Datenquelle. Name, Qualität und Symbol (Datei-ID des Spielsymbols) jedes Items werden mitgespeichert.
-- Der Uploader schickt RaidMasterDB.lootdb an den Bot; der Bot führt die Daten aller Uploader zusammen
-- (derselbe Kill bzw. dieselbe Leiche zählt nur einmal) und zeigt die Beutetabelle je Raid im Loot-Kanal.
--
-- Aufbau (bewusst einfach und erweiterbar – neue Felder stören alte Daten nicht):
--   lootdb.v      = 2
--   lootdb.kills  = { { e = Encounter-ID, p = Topf (mc, ony, barrow, hyjal ...), n = Bossname, t = Zeit, z = Instanz,
--                       s = Gruppengröße, g = GUID der Leiche/Truhe, i = { Item-IDs } }, ... }   (neueste zuletzt)
--   lootdb.trash  = { { p = Topf, t = Zeit, z = Instanz, g = GUID der Leiche, m = NPC-ID, i = { Item-IDs } }, ... }
--   lootdb.items  = { [Item-ID] = { n = Name, q = Qualität, ic = Symbol (Datei-ID), cl = Item-Klasse (7 = Handwerkswaren,
--                     5 = Reagenz – daran erkennt der Bot neue Handwerksmaterialien), f = zuerst gesehen, l = zuletzt gesehen } }
--   lootdb.bosses = { [Encounter-ID] = { n = Name, p = Topf, npc = { NPC-IDs der Bossgegner } } }
-- Im Testmodus wird nichts gespeichert.

local ADDON, RM = ...
local L = RM.L
local LDB = {}
RM.LootDB = LDB

LDB.MAX_KILLS = 800        -- so viele Bosskills merkt sich das Addon (der Bot hebt alles auf)
LDB.MAX_TRASH = 2000       -- so viele Trash-Leichen mit Beute
LDB.WINDOW = 1800          -- bis 30 Min. nach dem Kill kann die Beute des Bosses noch geöffnet werden (Sek.)
LDB.MIN_QUALITY = 2        -- ab Grün (graue/weiße Items und Geld zählen nicht)

local pending = {}         -- Bosskills, deren Beute noch nicht geöffnet wurde: { e, p, n, t, at, z, s, npcs = {} }
local engaged = {}         -- NPC-IDs der Bossgegner im laufenden Kampf
local seen = {}            -- schon gespeicherte Leichen/Truhen (GUID) – mehrmals öffnen zählt nicht doppelt

function LDB.Store()
	RM.db.lootdb = RM.db.lootdb or {}
	local s = RM.db.lootdb
	s.v = 2
	s.kills = s.kills or {}
	s.trash = s.trash or {}
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

local function InRaidInstance()
	if LDB.SimInstance ~= nil then return LDB.SimInstance end
	if not IsInInstance then return false end
	local inside, kind = IsInInstance()
	return inside and kind == "raid"
end

local function CurrentPool()
	return (RM.DKP.CurrentInstancePool and RM.DKP.CurrentInstancePool()) or (RM.db.session.active and RM.db.session.pool) or nil
end

local function Zone()
	return GetInstanceInfo and select(8, GetInstanceInfo()) or nil
end

-- "Creature-0-1234-409-5678-11502-0000ABCDEF" -> "Creature", 11502
function LDB.ParseGUID(guid)
	if type(guid) ~= "string" then return nil end
	local kind, _, _, _, _, id = strsplit("-", guid)
	return kind, tonumber(id)
end

---------------------------------------------------------------------------
-- Bosskampf: Bossgegner merken (boss1–boss5), Kill vormerken
---------------------------------------------------------------------------
local function ScanBossUnits()
	if not UnitGUID then return end
	for i = 1, 5 do
		local kind, npc = LDB.ParseGUID(UnitGUID("boss" .. i))
		if kind == "Creature" or kind == "Vehicle" then engaged[npc] = true end
	end
end

function LDB.OnEncounterStart()
	wipe(engaged)
	ScanBossUnits()
end

function LDB.OnKill(encounterID, encounterName, groupSize)
	if not Recording() or not encounterID then return end
	ScanBossUnits()
	local boss = RM.Data.Bosses[encounterID]
	local npcs = {}
	for npc in pairs(engaged) do npcs[npc] = true end
	local known = RM.db.lootdb and RM.db.lootdb.bosses and RM.db.lootdb.bosses[encounterID]
	for _, npc in ipairs((known and known.npc) or {}) do npcs[npc] = true end
	pending[#pending + 1] = { e = encounterID, p = (boss and boss.pool) or CurrentPool(), n = (boss and boss.name) or encounterName,
		t = GetServerTime(), at = GetTime(), z = Zone(), s = groupSize, npcs = npcs }
	wipe(engaged)
end

---------------------------------------------------------------------------
-- Lootfenster
---------------------------------------------------------------------------
local function ItemIDFromLink(link)
	return type(link) == "string" and tonumber(link:match("item:(%d+)")) or nil
end

local function IconOf(id, slot)
	local icon
	if C_Item and C_Item.GetItemIconByID then icon = C_Item.GetItemIconByID(id) end
	if not icon and GetItemIcon then icon = GetItemIcon(id) end
	if not icon and slot and GetLootSlotInfo then icon = (GetLootSlotInfo(slot)) end
	if not icon then icon = select(10, (RM.GetItemInfo or GetItemInfo)(id)) end
	return icon
end

-- Items im Lootfenster (ab Grün) und die GUID der Leiche/Truhe
function LDB.ReadLootWindow()
	local ids, info = {}, {}
	if not GetNumLootItems then return ids, info end
	local guid
	for slot = 1, GetNumLootItems() do
		local link = GetLootSlotLink and GetLootSlotLink(slot)
		local id = ItemIDFromLink(link)
		if id then
			if not guid and GetLootSourceInfo then guid = GetLootSourceInfo(slot) end
			local name, _, quality = (RM.GetItemInfo or GetItemInfo)(link)
			quality = quality or (RM.ItemQuality and RM.ItemQuality(link)) or 0
			if quality >= LDB.MIN_QUALITY then
				ids[#ids + 1] = id
				local classID = RM.GetItemInfoInstant and select(6, RM.GetItemInfoInstant(link)) or nil
				info[id] = { n = name or (link:match("%[(.-)%]")), q = quality, ic = IconOf(id, slot), cl = classID }
			end
		end
	end
	return ids, info, guid
end

local function RememberItems(s, ids, info, now)
	for _, id in ipairs(ids) do
		local e = s.items[id] or {}
		local x = info and info[id] or {}
		e.n = x.n or e.n
		e.q = x.q or e.q
		e.ic = x.ic or e.ic
		e.cl = x.cl or e.cl
		e.f = e.f or now
		e.l = now
		s.items[id] = e
	end
end

-- einen Bosskill mit seiner Beute speichern
function LDB.Record(kill, ids, info, guid)
	if not kill or not kill.e or not ids or #ids == 0 then return false end
	local s = LDB.Store()
	local now = kill.t or GetServerTime()
	table.sort(ids)
	s.kills[#s.kills + 1] = { e = kill.e, p = kill.p, n = kill.n, t = now, z = kill.z, s = kill.s, g = guid, i = ids }
	while #s.kills > LDB.MAX_KILLS do table.remove(s.kills, 1) end
	local b = s.bosses[kill.e] or {}
	b.n = kill.n or b.n
	b.p = kill.p or b.p
	-- NPC-IDs der Bossgegner merken: beim nächsten Kill erkennt das Addon die Boss-Leiche sicher
	local _, npc = LDB.ParseGUID(guid)
	local npcs = {}
	for n in pairs(kill.npcs or {}) do npcs[n] = true end
	if npc then npcs[npc] = true end
	local list = {}
	for _, n in ipairs(b.npc or {}) do npcs[n] = true end
	for n in pairs(npcs) do list[#list + 1] = n end
	table.sort(list)
	b.npc = list[1] and list or nil
	s.bosses[kill.e] = b
	RememberItems(s, ids, info, now)
	RM.Fire("LOOTDB_CHANGED", kill.e)
	return true
end

-- zufällige Drops vom Trash speichern
function LDB.RecordTrash(ids, info, guid, pool)
	if not ids or #ids == 0 then return false end
	local s = LDB.Store()
	local now = GetServerTime()
	table.sort(ids)
	local _, npc = LDB.ParseGUID(guid)
	s.trash[#s.trash + 1] = { p = pool, t = now, z = Zone(), g = guid, m = npc, i = ids }
	while #s.trash > LDB.MAX_TRASH do table.remove(s.trash, 1) end
	RememberItems(s, ids, info, now)
	RM.Fire("LOOTDB_CHANGED", "trash")
	return true
end

-- gehört dieses Lootfenster zu einem gerade getöteten Boss? -> Index in pending
local function MatchKill(guid, ids, info)
	local kind, npc = LDB.ParseGUID(guid)
	local now = GetTime()
	for i = #pending, 1, -1 do
		if now - pending[i].at > LDB.WINDOW then table.remove(pending, i) end
	end
	if #pending == 0 then return nil end
	-- 1. Leiche eines Bossgegners (NPC-ID aus dem Kampf oder von früheren Kills)
	if npc then
		for i, k in ipairs(pending) do if k.npcs[npc] then return i end end
	end
	-- 2. Truhe nach dem Kill (z. B. Majordomus): gehört zum letzten Kill
	if kind == "GameObject" then return #pending end
	-- 3. Kill ohne bekannte Bossgegner (keine Bossanzeige): erstes Fenster mit mindestens blauer Beute
	-- (ohne Angabe zur Leiche – ältere Spielversionen – gilt das für jeden offenen Kill)
	for i, k in ipairs(pending) do
		if not next(k.npcs) or not guid then
			for _, id in ipairs(ids) do
				if ((info[id] or {}).q or 0) >= 3 then return i end
			end
		end
	end
	return nil
end

function LDB.OnLootOpened()
	if not Recording() then return end
	local ids, info, guid = LDB.ReadLootWindow()
	if #ids == 0 then return end
	if guid and seen[guid] then return end      -- dieselbe Leiche/Truhe nochmal geöffnet
	local idx = MatchKill(guid, ids, info)
	if idx then
		local kill = table.remove(pending, idx)
		if guid then seen[guid] = true end
		LDB.Record(kill, ids, info, guid)
		return
	end
	-- Trash: nur in Raids, nur mit eindeutiger Leiche (sonst ließe sich doppeltes Öffnen nicht erkennen)
	if guid and InRaidInstance() then
		local kind = LDB.ParseGUID(guid)
		if kind == "Creature" or kind == "GameObject" then
			seen[guid] = true
			LDB.RecordTrash(ids, info, guid, CurrentPool())
		end
	end
end

RM.On("ENCOUNTER_START", function() LDB.OnEncounterStart() end)
RM.On("INSTANCE_ENCOUNTER_ENGAGE_UNIT", function() ScanBossUnits() end)
RM.On("ENCOUNTER_END", function(encounterID, encounterName, difficulty, groupSize, success)
	if success == 1 or success == true then LDB.OnKill(encounterID, encounterName, groupSize) else wipe(engaged) end
end)
RM.On("LOOT_OPENED", function() LDB.OnLootOpened() end)
RM.On("PLAYER_LOGIN", function()
	-- nach /reload: schon gespeicherte Leichen der letzten Stunde nicht nochmal zählen
	local s = RM.db and RM.db.lootdb
	if not s then return end
	local since = GetServerTime() - 3600
	for _, list in ipairs({ s.kills or {}, s.trash or {} }) do
		for i = #list, 1, -1 do
			local e = list[i]
			if (e.t or 0) < since then break end
			if e.g then seen[e.g] = true end
		end
	end
end)

---------------------------------------------------------------------------
-- Abfragen
---------------------------------------------------------------------------
local function Count(entries, filter)
	local count, n = {}, 0
	for _, k in ipairs(entries or {}) do
		if filter(k) then
			n = n + 1
			for _, id in ipairs(k.i or {}) do count[id] = (count[id] or 0) + 1 end
		end
	end
	return count, n
end

local function ToList(s, count, n)
	local list = {}
	for id, c in pairs(count) do
		local it = (s.items or {})[id] or {}
		list[#list + 1] = { id = id, n = it.n, q = it.q, ic = it.ic, c = c, rate = n > 0 and c / n or 0 }
	end
	table.sort(list, function(a, b)
		if a.c ~= b.c then return a.c > b.c end
		return a.id < b.id
	end)
	return list
end

-- Beute eines Bosses: { {id, n, q, ic, c = so oft gedroppt, rate = Anteil der Kills}, ... }, Anzahl Kills
function LDB.BossLoot(encounterID)
	local s = RM.db and RM.db.lootdb
	if not s then return {}, 0 end
	local count, kills = Count(s.kills, function(k) return k.e == encounterID end)
	return ToList(s, count, kills), kills
end

-- zufällige Drops vom Trash eines Raids: Liste wie oben, Anzahl Leichen mit Beute
function LDB.TrashLoot(pool)
	local s = RM.db and RM.db.lootdb
	if not s then return {}, 0 end
	local count, n = Count(s.trash, function(k) return pool == nil or k.p == pool end)
	return ToList(s, count, n), n
end

-- nur die Item-IDs (für den Testmodus)
function LDB.ItemIDs(encounterID)
	local list, kills = LDB.BossLoot(encounterID)
	local ids = {}
	for _, x in ipairs(list) do ids[#ids + 1] = x.id end
	return ids, kills
end

function LDB.TrashIDs(pool)
	local list, n = LDB.TrashLoot(pool)
	local ids = {}
	for _, x in ipairs(list) do ids[#ids + 1] = x.id end
	return ids, n
end

-- bekannte Bosse eines Raids (Reihenfolge des ersten Kills)
function LDB.BossesForPool(pool)
	local s = RM.db and RM.db.lootdb
	local out, done = {}, {}
	for _, k in ipairs((s and s.kills) or {}) do
		if k.p == pool and not done[k.e] then
			done[k.e] = true
			out[#out + 1] = { id = k.e, name = (s.bosses[k.e] and s.bosses[k.e].n) or k.n or ("Boss " .. k.e) }
		end
	end
	return out
end

function LDB.Stats()
	local s = RM.db and RM.db.lootdb
	if not s then return 0, 0, 0, 0 end
	local bosses, items = 0, 0
	for _ in pairs(s.bosses or {}) do bosses = bosses + 1 end
	for _ in pairs(s.items or {}) do items = items + 1 end
	return #(s.kills or {}), bosses, items, #(s.trash or {})
end

-- Text für den Chat: "/rm beute <Boss>" bzw. "/rm beute trash"
function LDB.PrintBoss(query)
	local s = RM.db and RM.db.lootdb
	if not s or (not next(s.bosses or {}) and not (s.trash and s.trash[1])) then
		RM.Print(L["Die Beute-Datenbank ist noch leer – sie füllt sich mit jedem Bosskill."])
		return
	end
	query = (query or ""):lower()
	local function Lines(list, n)
		for i, x in ipairs(list) do
			if i > 12 then break end
			local _, link = (RM.GetItemInfo or GetItemInfo)(x.id)
			RM.Print(string.format("  %s  %d/%d (%d%%)", link or x.n or ("item:" .. x.id), x.c, n, math.floor(x.rate * 100 + 0.5)))
		end
	end
	local found = 0
	if query == "trash" then
		local list, n = LDB.TrashLoot(CurrentPool())
		RM.Print(string.format(L["Trash: %d Leichen mit Beute, %d verschiedene Items"], n, #list))
		Lines(list, n)
		return
	end
	for id, b in pairs(s.bosses) do
		if query == "" or (b.n and b.n:lower():find(query, 1, true)) then
			local list, kills = LDB.BossLoot(id)
			RM.Print(string.format(L["%s: %d Kills, %d verschiedene Items"], b.n or ("Boss " .. id), kills, #list))
			Lines(list, kills)
			found = found + 1
		end
	end
	if found == 0 then RM.Print(string.format(L["Kein Boss mit '%s' in der Beute-Datenbank."], query)) end
end
