-- RaidMaster - PUG-Raids mit Soft Reserve
-- Kein DKP: Spieler reservieren Items (Item-ID oder Shift-Klick), gewürfelt wird automatisch.
-- SR-Items: nur die Reservierer würfeln. Andere Items: Bedarf /roll, Gier /roll 99.

local ADDON, RM = ...
local P = {}
RM.PUG = P

P.queue = {}         -- Würfel-Warteschlange (nur Leiter)
P.current = nil      -- laufendes Würfeln (nur Leiter)
P.view = { active = false, leader = nil, limit = 1, locked = false, reserves = {} } -- Ansicht für alle
P.ROLL_TIME = 20

local function DB()
	RM.db.pug = RM.db.pug or { active = false, limit = 1, locked = false, reserves = {} }
	return RM.db.pug
end

---------------------------------------------------------------------------
-- Hilfen
---------------------------------------------------------------------------
-- Item-IDs aus Text lesen: Itemlinks, "item:123" oder Zahlen (Komma/Leerzeichen getrennt)
function P.ParseIDs(text)
	local ids, seen = {}, {}
	text = tostring(text or "")
	for id in text:gmatch("item:(%d+)") do
		id = tonumber(id)
		if id and not seen[id] then seen[id] = true; ids[#ids + 1] = id end
	end
	local rest = text:gsub("|c%x+|Hitem:[^|]+|h.-|h|r", ""):gsub("item:%d+", "")
	for id in rest:gmatch("(%d+)") do
		id = tonumber(id)
		if id and id > 0 and not seen[id] then seen[id] = true; ids[#ids + 1] = id end
	end
	return ids
end

function P.ItemLabel(id)
	local _, link = RM.GetItemInfo(id)
	if link then return link end
	if C_Item and C_Item.RequestLoadItemDataByID then pcall(C_Item.RequestLoadItemDataByID, id) end
	return "Item #" .. id
end

function P.ItemName(id)
	local name = RM.GetItemInfo(id)
	return name or ("Item #" .. id)
end

function P.IsLeader()
	local d = DB()
	return d.active and d.leader == RM.Me()
end

function P.IsActive()
	return P.view.active
end

function P.CanLead()
	return RM.InRaid() and (RM.IsLeader() or RM.IsAssist() or RM.IAmMasterLooter())
end

-- Wer hat dieses Item reserviert?
function P.ReserversOf(itemID, reserves)
	reserves = reserves or P.view.reserves
	local list = {}
	for name, ids in pairs(reserves or {}) do
		for _, id in ipairs(ids) do
			if id == itemID then list[#list + 1] = name break end
		end
	end
	table.sort(list)
	return list
end

---------------------------------------------------------------------------
-- Leiter: PUG starten / beenden / Liste verteilen
---------------------------------------------------------------------------
local broadcastPending = false

function P.BroadcastList()
	if not P.IsLeader() then return end
	if broadcastPending then return end
	broadcastPending = true
	C_Timer.After(1.5, function()
		broadcastPending = false
		local d = DB()
		if not d.active then return end
		RM.Comm.Send("SRL", { r = d.reserves, l = d.limit, lk = d.locked, t = d.title }, "RAID")
	end)
	P.SyncView()
end

function P.SyncView()
	local d = DB()
	if d.active and d.leader == RM.Me() then
		P.view = { active = true, leader = RM.Me(), limit = d.limit, locked = d.locked, reserves = d.reserves, title = d.title }
	end
	RM.Fire("PUG_CHANGED")
end

function P.Start(limit, title)
	if not P.CanLead() then RM.Print("PUG-Raids kann der Raidleiter, ein Assistent oder der Plündermeister starten.") return end
	local d = DB()
	d.active = true
	d.leader = RM.Me()
	d.limit = math.max(1, math.min(5, tonumber(limit) or d.limit or 1))
	d.locked = false
	d.title = title or (RM.db.signup and RM.db.signup.title) or "PUG-Raid"
	d.reserves = d.reserves or {}
	-- Reservierungen aus Discord übernehmen
	P.ImportFromSignup(true)
	RM.Comm.Send("PS", { l = d.limit, t = d.title }, "RAID", nil, true)
	P.BroadcastList()
	RM.Announce(string.format("[RaidMaster] PUG-Raid mit Soft Reserve: je %d Item(s). Reservieren im Addon (Seite Soft Reserve) oder /w %s !sr <Item-ID oder Link>",
		d.limit, RM.Me()), true)
	-- in diesem Modus werden epische Items ausgewürfelt statt versteigert
	if RM.InRaid() and RM.IsLeader() and RM.db.config.setLootOnStart then RM.Loot.ApplySettings() end
	RM.Fire("PUG_CHANGED")
end

function P.Stop()
	local d = DB()
	if not d.active then return end
	d.active = false
	RM.Comm.Send("PE", {}, "RAID", nil, true)
	P.view = { active = false, reserves = {}, limit = 1 }
	RM.Announce("[RaidMaster] PUG-Raid beendet. Danke fürs Mitspielen!", false)
	RM.Fire("PUG_CHANGED")
end

function P.SetLocked(locked)
	local d = DB()
	if not P.IsLeader() then return end
	d.locked = locked and true or false
	RM.Announce(locked and "[RaidMaster] Soft Reserves sind jetzt gesperrt." or "[RaidMaster] Soft Reserves sind wieder offen.", false)
	P.BroadcastList()
end

function P.ClearAll()
	if not P.IsLeader() then return end
	DB().reserves = {}
	P.BroadcastList()
end

-- Reservierung eines Spielers setzen (nur Leiter). Liefert ok, Meldung
function P.SetReserve(name, ids)
	local d = DB()
	if not P.IsLeader() then return false, "Kein aktiver PUG-Raid." end
	name = RM.Short(name)
	if d.locked then return false, "Soft Reserves sind gesperrt." end
	if #ids > d.limit then return false, string.format("Maximal %d Item(s) erlaubt.", d.limit) end
	if not RM.IsInMyRaid(name) and not (RM.db.signup and RM.db.signup.sr and RM.db.signup.sr[name]) then
		return false, "Nur Raidmitglieder können reservieren."
	end
	if #ids == 0 then
		d.reserves[name] = nil
	else
		d.reserves[name] = ids
	end
	P.BroadcastList()
	return true
end

function P.RemoveReserve(name, itemID)
	local d = DB()
	if not P.IsLeader() then return end
	local ids = d.reserves[name]
	if not ids then return end
	for i = #ids, 1, -1 do if ids[i] == itemID then table.remove(ids, i) end end
	if #ids == 0 then d.reserves[name] = nil end
	P.BroadcastList()
end

-- SR-Liste aus dem Discord-Import übernehmen
function P.ImportFromSignup(silent)
	local su = RM.db.signup
	if not su or not su.sr then
		if not silent then RM.Print("Im Discord-Import sind keine Soft Reserves enthalten.") end
		return 0
	end
	local d = DB()
	local n = 0
	for name, ids in pairs(su.sr) do
		if not d.reserves[name] then
			local list = {}
			for i = 1, math.min(#ids, d.limit or 1) do list[#list + 1] = ids[i] end
			d.reserves[name] = list
			n = n + 1
		end
	end
	if n > 0 and not silent then RM.Print(n .. " Soft Reserves aus Discord übernommen.") end
	if P.IsLeader() then P.BroadcastList() end
	return n
end

function P.PostList()
	local d = DB()
	local byItem = {}
	for name, ids in pairs(d.reserves or {}) do
		for _, id in ipairs(ids) do
			byItem[id] = byItem[id] or {}
			table.insert(byItem[id], name)
		end
	end
	local lines = {}
	for id, names in pairs(byItem) do
		table.sort(names)
		lines[#lines + 1] = P.ItemLabel(id) .. ": " .. table.concat(names, ", ")
	end
	table.sort(lines)
	if #lines == 0 then RM.Announce("[RaidMaster] Noch keine Soft Reserves.", false) return end
	RM.Announce("[RaidMaster] Soft Reserves:", false)
	for _, l in ipairs(lines) do RM.Announce(l, false) end
end

---------------------------------------------------------------------------
-- Spieler: eigene Reservierung
---------------------------------------------------------------------------
function P.MyReserves()
	return (P.view.reserves and P.view.reserves[RM.Me()]) or {}
end

function P.SendMyReserves(ids)
	if not P.view.active then RM.Print("Es läuft gerade kein PUG-Raid mit Soft Reserve.") return end
	if P.view.leader == RM.Me() then
		local ok, err = P.SetReserve(RM.Me(), ids)
		if not ok then RM.Print(err) end
	else
		RM.Comm.Send("SR", { ids = ids }, "WHISPER", P.view.leader, true)
	end
end

function P.AddMine(text)
	local add = P.ParseIDs(text)
	if #add == 0 then RM.Print("Bitte eine Item-ID eingeben oder ein Item per Shift-Klick einfügen.") return end
	local ids = {}
	for _, id in ipairs(P.MyReserves()) do ids[#ids + 1] = id end
	for _, id in ipairs(add) do
		local dup = false
		for _, x in ipairs(ids) do if x == id then dup = true end end
		if not dup then ids[#ids + 1] = id end
	end
	if #ids > (P.view.limit or 1) then
		RM.Print(string.format("Maximal %d Item(s) – entferne zuerst eine Reservierung.", P.view.limit or 1))
		return
	end
	P.SendMyReserves(ids)
end

function P.RemoveMine(itemID)
	local ids = {}
	for _, id in ipairs(P.MyReserves()) do if id ~= itemID then ids[#ids + 1] = id end end
	P.SendMyReserves(ids)
end

---------------------------------------------------------------------------
-- Nachrichten
---------------------------------------------------------------------------
RM.Comm.Register("PS", function(sender, d)
	P.view = { active = true, leader = sender, limit = d.l or 1, locked = false, reserves = {}, title = d.t }
	RM.Print(string.format("PUG-Raid mit Soft Reserve gestartet von %s – je %d Item(s). Seite 'Soft Reserve' im RaidMaster-Fenster.", sender, d.l or 1))
	RM.Fire("PUG_CHANGED")
end)

RM.Comm.Register("PE", function(sender)
	if P.view.leader == sender then
		P.view = { active = false, reserves = {}, limit = 1 }
		RM.Fire("PUG_CHANGED")
	end
end)

RM.Comm.Register("SRL", function(sender, d)
	if P.view.leader and P.view.leader ~= sender and P.view.active then return end
	P.view = { active = true, leader = sender, limit = d.l or 1, locked = d.lk, reserves = d.r or {}, title = d.t }
	RM.Fire("PUG_CHANGED")
end)

RM.Comm.Register("SR", function(sender, d)
	if not P.IsLeader() then return end
	local ids = {}
	for _, id in ipairs(d.ids or {}) do if tonumber(id) then ids[#ids + 1] = tonumber(id) end end
	local ok, err = P.SetReserve(sender, ids)
	if not ok then RM.Comm.Send("SRERR", { m = err }, "WHISPER", sender, true) end
end)

RM.Comm.Register("SRERR", function(sender, d)
	RM.Print("Soft Reserve: " .. tostring(d.m))
	RM.Fire("PUG_CHANGED")
end)

-- Flüstern: "!sr 12345", "!sr [Itemlink]", "!sr" (anzeigen), "!sr löschen"
RM.On("CHAT_MSG_WHISPER", function(msg, sender)
	if not RM.db or not P.IsLeader() then return end
	local text = msg or ""
	local lower = text:lower()
	if not lower:match("^%s*!sr") then return end
	local name = RM.Short(sender)
	local arg = text:gsub("^%s*![sS][rR]%s*", "")
	if arg == "" then
		local ids = DB().reserves[name] or {}
		local parts = {}
		for _, id in ipairs(ids) do parts[#parts + 1] = P.ItemName(id) .. " (" .. id .. ")" end
		SendChatMessage("[RaidMaster] Deine Soft Reserves: " .. (#parts > 0 and table.concat(parts, ", ") or "keine"), "WHISPER", nil, sender)
		return
	end
	if arg:lower():match("^l[öo]schen") or arg:lower():match("^clear") then
		local ok, err = P.SetReserve(name, {})
		SendChatMessage("[RaidMaster] " .. (ok and "Soft Reserves gelöscht." or err), "WHISPER", nil, sender)
		return
	end
	local ids = P.ParseIDs(arg)
	if #ids == 0 then
		SendChatMessage("[RaidMaster] Bitte Item-ID oder Itemlink angeben, z. B. !sr 16800", "WHISPER", nil, sender)
		return
	end
	local ok, err = P.SetReserve(name, ids)
	if ok then
		local parts = {}
		for _, id in ipairs(ids) do parts[#parts + 1] = P.ItemName(id) .. " (" .. id .. ")" end
		SendChatMessage("[RaidMaster] Soft Reserve gespeichert: " .. table.concat(parts, ", "), "WHISPER", nil, sender)
	else
		SendChatMessage("[RaidMaster] " .. err, "WHISPER", nil, sender)
	end
end)

---------------------------------------------------------------------------
-- Würfeln (Leiter / Plündermeister)
---------------------------------------------------------------------------
local rollPattern
local function RollPattern()
	if rollPattern then return rollPattern end
	local fmt = RANDOM_ROLL_RESULT or "%s rolls %d (%d-%d)"
	fmt = fmt:gsub("%%%d?%$?", "%%")             -- "%1$s" -> "%s"
	local pat = fmt:gsub("([%(%)%.%+%-%*%?%[%]%^%$])", "%%%1")
	pat = pat:gsub("%%s", "(.+)"):gsub("%%d", "(%%d+)")
	rollPattern = "^" .. pat .. "$"
	return rollPattern
end
P.RollPattern = RollPattern

function P.EnqueueRoll(link)
	P.queue[#P.queue + 1] = { link = link }
	RM.Fire("PUG_CHANGED")
end

function P.RemoveRoll(index)
	table.remove(P.queue, index)
	RM.Fire("PUG_CHANGED")
end

local rollTicker

function P.StartRoll(indexOrLink, onlyNames)
	if not P.IsLeader() then RM.Print("Nur der Leiter des PUG-Raids kann würfeln lassen.") return end
	if P.current then RM.Print("Es läuft bereits ein Würfeln.") return end
	local link
	if type(indexOrLink) == "number" then
		local item = table.remove(P.queue, indexOrLink)
		link = item and item.link
	else
		link = indexOrLink
	end
	if not link then return end
	local itemID = RM.ItemID(link)
	local sr = onlyNames or P.ReserversOf(itemID, DB().reserves)
	local allowed = nil
	if #sr > 0 then
		allowed = {}
		for _, n in ipairs(sr) do allowed[n] = true end
	end
	P.current = { link = link, id = itemID, sr = sr, allowed = allowed, rolls = {}, endsAt = GetTime() + P.ROLL_TIME, tie = onlyNames ~= nil }
	if allowed and onlyNames then
		RM.Announce(string.format("[Stechen] %s – nur %s würfeln: /roll (%d Sek.)", link, table.concat(sr, ", "), P.ROLL_TIME), true)
	elseif allowed then
		RM.Announce(string.format("[SR] %s – nur %s würfeln: /roll (%d Sek.)", link, table.concat(sr, ", "), P.ROLL_TIME), true)
	else
		RM.Announce(string.format("Würfeln: %s – Bedarf /roll · Gier /roll 99 (%d Sek.)", link, P.ROLL_TIME), true)
	end
	if rollTicker then rollTicker:Cancel() end
	rollTicker = C_Timer.NewTicker(0.5, function()
		local c = P.current
		if not c then rollTicker:Cancel(); rollTicker = nil return end
		local rem = math.ceil(c.endsAt - GetTime())
		if rem <= 0 then P.FinishRoll() return end
		if rem == 5 and not c.warned then
			c.warned = true
			SendChatMessage(string.format("%s – noch 5 Sek. würfeln!", c.link), "RAID")
		end
	end)
	RM.Fire("PUG_CHANGED")
end

RM.On("CHAT_MSG_SYSTEM", function(msg)
	local c = P.current
	if not c or c.finished or not msg then return end
	local who, value, low, high = msg:match(RollPattern())
	if not who then return end
	who = RM.Short(who)
	value, low, high = tonumber(value), tonumber(low), tonumber(high)
	if c.rolls[who] then return end                         -- nur der erste Wurf zählt
	if not RM.IsInMyRaid(who) then return end
	if low ~= 1 then return end
	local kind
	if c.allowed then
		if not c.allowed[who] or high ~= 100 then return end
		kind = "sr"
	elseif high == 100 then
		kind = "need"
	elseif high == 99 then
		kind = "greed"
	else
		return
	end
	c.rolls[who] = { v = value, kind = kind, t = GetTime() }
	RM.Fire("PUG_CHANGED")
end)

-- Sortierte Würfe: SR/Bedarf vor Gier, dann Höhe
function P.RollList()
	local c = P.current
	local list = {}
	if not c then return list end
	for name, r in pairs(c.rolls) do list[#list + 1] = { name = name, v = r.v, kind = r.kind } end
	local rank = { sr = 1, need = 1, greed = 2 }
	table.sort(list, function(a, b)
		if rank[a.kind] ~= rank[b.kind] then return rank[a.kind] < rank[b.kind] end
		if a.v == b.v then return a.name < b.name end
		return a.v > b.v
	end)
	return list
end

function P.FinishRoll()
	local c = P.current
	if not c or c.finished then return end
	if rollTicker then rollTicker:Cancel(); rollTicker = nil end
	c.finished = true
	local list = P.RollList()
	if #list == 0 then
		P.current = nil
		RM.Announce("[RaidMaster] Niemand hat für " .. c.link .. " gewürfelt.", false)
		RM.Loot.ApplyFallback(c.link)
		RM.Fire("PUG_CHANGED")
		P.StartNextIfIdle()
		return
	end
	local best = list[1]
	local tied = {}
	for _, r in ipairs(list) do
		if r.kind == best.kind or (r.kind ~= "greed" and best.kind ~= "greed") then
			if r.v == best.v then tied[#tied + 1] = r.name end
		end
	end
	if #tied > 1 then
		P.current = nil
		RM.Announce(string.format("[RaidMaster] Gleichstand (%d) zwischen %s – bitte erneut würfeln.", best.v, table.concat(tied, ", ")), true)
		C_Timer.After(2, function() P.StartRoll(c.link, tied) end)
		RM.Fire("PUG_CHANGED")
		return
	end
	local label = c.tie and "Stechen" or (best.kind == "sr" and "SR" or (best.kind == "need" and "Bedarf" or "Gier"))
	RM.UI.Confirm(string.format("%s an %s vergeben? (%s, Wurf %d)", c.link, best.name, label, best.v),
		function()
			RM.Announce(string.format("[RaidMaster] %s gewinnt %s (%s, %d).", best.name, c.link, label, best.v), true)
			RM.Loot.Deliver(c.link, best.name)
			P.current = nil
			RM.Fire("PUG_CHANGED")
			P.StartNextIfIdle()
		end,
		function()
			P.current = nil
			table.insert(P.queue, 1, { link = c.link })
			RM.Fire("PUG_CHANGED")
		end, "Vergeben", "Nicht vergeben")
	RM.Fire("PUG_CHANGED")
end

function P.CancelRoll()
	local c = P.current
	if not c then return end
	if rollTicker then rollTicker:Cancel(); rollTicker = nil end
	P.current = nil
	table.insert(P.queue, 1, { link = c.link })
	RM.Announce("[RaidMaster] Würfeln für " .. c.link .. " abgebrochen.", false)
	RM.Fire("PUG_CHANGED")
end

function P.StartNextIfIdle()
	if P.current or #P.queue == 0 or not RM.db.config.autoNext or not P.IsLeader() then return end
	C_Timer.After(1.5, function()
		if not P.current and #P.queue > 0 then P.StartRoll(1) end
	end)
end

RM.Listen("LOGIN", function()
	-- Nach /reload den eigenen PUG-Raid wieder aufnehmen
	local d = DB()
	if d.active and d.leader == RM.Me() then
		if RM.InRaid() then P.SyncView() else d.active = false end
	end
end)
