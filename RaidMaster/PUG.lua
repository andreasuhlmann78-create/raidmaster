-- RaidMaster - PUG-Raids
-- Kein DKP: Epische Items werden ausgewürfelt – Bedarf /roll, Gier /roll 99.
-- Gleichstand: Stechen zwischen den Gleichen. Der Leiter bestätigt, dann wird das Item direkt zugeteilt.

local ADDON, RM = ...
local P = {}
RM.PUG = P

P.queue = {}         -- Würfel-Warteschlange (nur Leiter)
P.current = nil      -- laufendes Würfeln (nur Leiter)
P.view = { active = false, leader = nil }   -- Ansicht für alle
P.ROLL_TIME = 20

local function DB()
	RM.db.pug = RM.db.pug or { active = false }
	RM.db.pug.reserves = nil   -- Soft Reserve gibt es nicht mehr
	return RM.db.pug
end

---------------------------------------------------------------------------
-- Hilfen
---------------------------------------------------------------------------
function P.ItemLabel(id)
	local _, link = RM.GetItemInfo(id)
	if link then return link end
	if C_Item and C_Item.RequestLoadItemDataByID then pcall(C_Item.RequestLoadItemDataByID, id) end
	return "Item #" .. id
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

---------------------------------------------------------------------------
-- Leiter: PUG-Raid starten / beenden
---------------------------------------------------------------------------
function P.SyncView()
	local d = DB()
	if d.active and d.leader == RM.Me() then
		P.view = { active = true, leader = RM.Me(), title = d.title }
	end
	RM.Fire("PUG_CHANGED")
end

function P.Start(title)
	if not P.CanLead() then RM.Print("PUG-Raids kann der Raidleiter, ein Assistent oder der Plündermeister starten.") return end
	local d = DB()
	d.active = true
	d.leader = RM.Me()
	d.title = (type(title) == "string" and title) or (RM.db.signup and RM.db.signup.title) or "PUG-Raid"
	RM.Comm.Send("PS", { t = d.title }, "RAID", nil, true)
	P.SyncView()
	RM.Announce("[RaidMaster] PUG-Raid: Epische Items werden ausgewürfelt – Bedarf /roll, Gier /roll 99.", true)
	-- in diesem Modus werden epische Items ausgewürfelt statt versteigert
	if RM.InRaid() and RM.IsLeader() and RM.db.config.setLootOnStart then RM.Loot.ApplySettings() end
	RM.Fire("PUG_CHANGED")
end

function P.Stop()
	local d = DB()
	if not d.active then return end
	d.active = false
	RM.Comm.Send("PE", {}, "RAID", nil, true)
	P.view = { active = false }
	RM.Announce("[RaidMaster] PUG-Raid beendet. Danke fürs Mitspielen!", false)
	RM.Fire("PUG_CHANGED")
end

---------------------------------------------------------------------------
-- Nachrichten
---------------------------------------------------------------------------
RM.Comm.Register("PS", function(sender, d)
	P.view = { active = true, leader = sender, title = d.t }
	RM.Print(string.format("PUG-Raid gestartet von %s – epische Items werden ausgewürfelt (Bedarf /roll, Gier /roll 99).", sender))
	RM.Fire("PUG_CHANGED")
end)

RM.Comm.Register("PE", function(sender)
	if P.view.leader == sender then
		P.view = { active = false }
		RM.Fire("PUG_CHANGED")
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

-- onlyNames: Stechen nur zwischen diesen Spielern
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
	local allowed = nil
	if onlyNames and #onlyNames > 0 then
		allowed = {}
		for _, n in ipairs(onlyNames) do allowed[n] = true end
	end
	P.current = { link = link, id = itemID, only = onlyNames, allowed = allowed, rolls = {}, endsAt = GetTime() + P.ROLL_TIME, tie = onlyNames ~= nil }
	if allowed then
		RM.Announce(string.format("[Stechen] %s – nur %s würfeln: /roll (%d Sek.)", link, table.concat(onlyNames, ", "), P.ROLL_TIME), true)
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
		kind = "tie"
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

-- Sortierte Würfe: Bedarf/Stechen vor Gier, dann Höhe
function P.RollList()
	local c = P.current
	local list = {}
	if not c then return list end
	for name, r in pairs(c.rolls) do list[#list + 1] = { name = name, v = r.v, kind = r.kind } end
	local rank = { tie = 1, need = 1, greed = 2 }
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
	local label = c.tie and "Stechen" or (best.kind == "need" and "Bedarf" or "Gier")
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
