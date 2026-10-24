-- RaidMaster - Loot
-- Loot-Einstellungen, Loot-Regeln, automatische Verteilung, Sammelansage,
-- offene Zuteilungen, Handelshelfer, Erinnerung an nicht geplünderte Bosse

local ADDON, RM = ...
local L = RM.L
local Loot = {}
RM.Loot = Loot

Loot.isOpen = false
Loot.items = {}          -- aktuelles Lootfenster: { slot, link, quality, action, done }
local announced = {}
local queuedFromSource = {}

local function C() return RM.db.config end

Loot.ActionNames = {
	auction = L["Versteigerung"],
	bank = L["Gildenbank"],
	de = L["Entzauberer"],
	crafter = L["Handwerker"],
	manual = L["Manuell"],
	notify = L["Hinweis (legendär)"],
}

---------------------------------------------------------------------------
-- Loot-Einstellungen setzen
---------------------------------------------------------------------------
function Loot.ApplySettings()
	if not RM.InRaid() then RM.Print(L["Du bist in keinem Schlachtzug."]) return end
	if not RM.IsLeader() then RM.Print(L["Nur der Raidleiter kann die Plündermethode ändern."]) return end
	if not RM.Caps.masterLoot then
		RM.Print(L["Diese Spielversion hat keinen Plündermeister – Plündermethode bleibt unverändert."])
		return
	end
	local ml = C().lootMaster
	if not ml or ml == "" then ml = RM.Me() end
	RM.SetLootMethod("master", ml)
	C_Timer.After(1.5, function()
		RM.SetLootThreshold(C().lootThreshold)
		RM.Print(string.format(L["Plündermeister: %s, Schwelle: %s"], ml, RM.Raid.THRESHOLD_NAMES[C().lootThreshold] or C().lootThreshold))
	end)
end

---------------------------------------------------------------------------
-- Einordnung eines Items
---------------------------------------------------------------------------
function Loot.Classify(link, quality)
	local itemID, _, _, _, _, classID = RM.GetItemInfoInstant(link)
	local rules = C().rules
	if itemID and RM.Data.Legendary[itemID] then return "notify" end
	if quality and quality >= 5 then return "notify" end
	if classID == 9 then return rules.recipe end
	if classID == 7 or classID == 5 then return rules.mats end
	if classID == 12 then return "manual" end
	if quality and quality >= 4 then return rules.epic end
	if quality == 3 and (classID == 2 or classID == 4) then return rules.blue end
	return "manual"
end

function Loot.RecipientFor(action)
	local c = C()
	if action == "bank" then return c.bankChar
	elseif action == "de" then return c.deChar
	elseif action == "crafter" then return c.crafterChar
	end
end

---------------------------------------------------------------------------
-- Plündermeister-Zuteilung
---------------------------------------------------------------------------
local function CandidateIndex(slot, name)
	name = RM.Short(name)
	for i = 1, 40 do
		local cand = GetMasterLootCandidate(slot, i)
		if cand and RM.Short(cand) == name then return i end
	end
end

local function FindSlot(link)
	local id = RM.ItemID(link)
	for slot = 1, GetNumLootItems() do
		local l = GetLootSlotLink(slot)
		if l and (l == link or RM.ItemID(l) == id) then return slot end
	end
end

-- Item direkt aus dem offenen Lootfenster zuteilen
function Loot.GiveFromWindow(link, name)
	if not Loot.isOpen or not RM.IAmMasterLooter() then return false, "closed" end
	local slot = FindSlot(link)
	if not slot then return false, "noslot" end
	local idx = CandidateIndex(slot, name)
	if idx then
		GiveMasterLoot(slot, idx)
		return true
	end
	return false, "nocandidate", slot
end

-- Item an den Gewinner bringen (direkt, beim nächsten Öffnen oder per Handel)
function Loot.Deliver(link, name)
	if not RM.Caps.masterLoot then
		-- Persönliche Beute (z. B. Retail): Wer das Item hat, gibt es per Handel weiter
		Loot.AddTrade(link, name)
		RM.Announce(string.format(L["[RaidMaster] %s geht an %s – bitte per Handel übergeben."], link, name), false)
		return true
	end
	local ok, reason, slot = Loot.GiveFromWindow(link, name)
	if ok then return true end
	if reason == "nocandidate" and C().tradeFallback and slot then
		local myIdx = CandidateIndex(slot, RM.Me())
		if myIdx then
			GiveMasterLoot(slot, myIdx)
			Loot.AddTrade(link, name)
			RM.Print(string.format(L["%s ist nicht erreichbar – %s an dich vergeben und in die Handelsliste gelegt."], name, link))
			return true
		end
	end
	if reason == "closed" or reason == "noslot" then
		local pa = RM.db.pendingAwards
		pa[#pa + 1] = { link = link, name = name, t = GetServerTime() }
		RM.Print(string.format(L["Öffne den Boss erneut – %s wird dann automatisch an %s vergeben."], link, name))
		RM.Fire("LOOT_CHANGED")
		return false
	end
	RM.Print(string.format(L["%s konnte nicht an %s vergeben werden. Bitte manuell zuteilen."], link, name))
	return false
end

-- Was passiert, wenn niemand bietet
function Loot.ApplyFallback(link)
	local action = C().fallback
	local name = Loot.RecipientFor(action)
	if action == "manual" or not name or name == "" then
		RM.Print(L["Keine Gebote für "] .. link .. L[" – bitte manuell entscheiden."])
		return
	end
	RM.Announce(string.format(L["[RaidMaster] Keine Gebote für %s – geht an %s (%s)."], link, name, Loot.ActionNames[action] or action), false)
	Loot.Deliver(link, name)
end

---------------------------------------------------------------------------
-- Handelshelfer
---------------------------------------------------------------------------
function Loot.AddTrade(link, name)
	local t = RM.db.trade
	t[#t + 1] = { link = link, name = RM.Short(name), t = GetServerTime() }
	RM.Fire("LOOT_CHANGED")
end

function Loot.RemoveTrade(index)
	table.remove(RM.db.trade, index)
	RM.Fire("LOOT_CHANGED")
end

local placedInTrade = {}

local function FindInBags(link)
	local id = RM.ItemID(link)
	for bag = 0, 4 do
		local n = RM.Container.NumSlots(bag) or 0
		for slot = 1, n do
			local l = RM.Container.ItemLink(bag, slot)
			if l and RM.ItemID(l) == id then return bag, slot end
		end
	end
end

RM.On("TRADE_SHOW", function()
	wipe(placedInTrade)
	local partner = RM.Short(UnitName("NPC"))
	if not partner then return end
	local todo = {}
	for i, e in ipairs(RM.db.trade) do
		if e.name == partner then todo[#todo + 1] = i end
	end
	if #todo == 0 then return end
	local tradeSlot = 1
	for n, idx in ipairs(todo) do
		C_Timer.After(0.3 * n, function()
			local e = RM.db.trade[idx]
			if not e then return end
			while tradeSlot <= 6 and GetTradePlayerItemLink(tradeSlot) do tradeSlot = tradeSlot + 1 end
			if tradeSlot > 6 then return end
			local bag, slot = FindInBags(e.link)
			if bag then
				ClearCursor()
				RM.Container.Pickup(bag, slot)
				ClickTradeButton(tradeSlot)
				placedInTrade[#placedInTrade + 1] = e
				tradeSlot = tradeSlot + 1
			end
		end)
	end
	RM.Print(string.format(L["Handel mit %s: %d Item(s) aus der Handelsliste werden eingelegt."], partner, #todo))
end)

RM.On("UI_INFO_MESSAGE", function(a, b)
	if a ~= ERR_TRADE_COMPLETE and b ~= ERR_TRADE_COMPLETE then return end
	if #placedInTrade == 0 then return end
	for _, e in ipairs(placedInTrade) do
		for i, t in ipairs(RM.db.trade) do
			if t == e then table.remove(RM.db.trade, i) break end
		end
	end
	wipe(placedInTrade)
	RM.Fire("LOOT_CHANGED")
end)

---------------------------------------------------------------------------
-- Lootfenster
---------------------------------------------------------------------------
local function SourceKey()
	if GetLootSourceInfo then
		local guid = GetLootSourceInfo(1)
		if guid then return guid end
	end
	local parts = {}
	for slot = 1, GetNumLootItems() do
		local l = GetLootSlotLink(slot)
		if l then parts[#parts + 1] = RM.ItemID(l) or "" end
	end
	return table.concat(parts, ":")
end

local function GiveDelayed(link, name, delay)
	C_Timer.After(delay, function()
		local ok = Loot.GiveFromWindow(link, name)
		if ok then
			RM.Print(string.format("%s -> %s", link, name))
		else
			RM.Print(string.format(L["%s konnte nicht automatisch an %s gegeben werden (nicht in Reichweite?)."], link, name))
		end
	end)
end

RM.On("LOOT_OPENED", function()
	Loot.isOpen = true
	wipe(Loot.items)
	if not RM.IAmMasterLooter() then RM.Fire("LOOT_CHANGED") return end
	Loot.pendingBoss = nil

	local cfg = C()
	local threshold = cfg.lootThreshold or 3
	local key = SourceKey()
	local announceParts = {}
	local delay = 0.3

	-- offene Zuteilungen aus früheren Versteigerungen zuerst
	local pa = RM.db.pendingAwards
	for i = #pa, 1, -1 do
		local p = pa[i]
		if FindSlot(p.link) then
			table.remove(pa, i)
			GiveDelayed(p.link, p.name, delay)
			delay = delay + 0.3
		end
	end

	for slot = 1, GetNumLootItems() do
		local link = GetLootSlotLink(slot)
		if link then
			local quality = RM.ItemQuality(link)
			if quality >= threshold then
				local action = Loot.Classify(link, quality)
				local item = { slot = slot, link = link, quality = quality, action = action }
				Loot.items[#Loot.items + 1] = item
				announceParts[#announceParts + 1] = link

				local firstTime = not queuedFromSource[key .. ":" .. slot]
				queuedFromSource[key .. ":" .. slot] = true

				if action == "notify" then
					if firstTime then
						PlaySound(SOUNDKIT and SOUNDKIT.RAID_WARNING or 8959)
						RaidNotice_AddMessage(RaidWarningFrame, L["Legendärer Gegenstand: "] .. link, ChatTypeInfo["RAID_WARNING"])
						RM.Print(L["Legendärer Gegenstand im Loot: "] .. link .. L[" – bitte nach Gildenregel vergeben."])
					end
				elseif action == "auction" then
					-- PUG-Raid: keine Versteigerung – der Loot läuft über softres.it, der Plündermeister verteilt von Hand
					if firstTime and not RM.PUG.IsLeader() then RM.Auction.Enqueue(link) end
				elseif action == "bank" or action == "de" or action == "crafter" then
					local name = Loot.RecipientFor(action)
					if cfg.autoDistribute and firstTime and name and name ~= "" then
						GiveDelayed(link, name, delay)
						delay = delay + 0.3
						item.done = true
					elseif firstTime and (not name or name == "") then
						RM.Print(string.format(L["%s: Kein Empfänger für '%s' eingestellt – bitte manuell zuteilen."], link, Loot.ActionNames[action]))
					end
				end
			end
		end
	end

	if cfg.announceLoot and #announceParts > 0 and not announced[key] then
		announced[key] = true
		RM.AnnounceLines(L["[RaidMaster] Loot: "], announceParts, RM.PUG.IsLeader() and 2 or 3)
	end

	RM.Fire("LOOT_CHANGED")
	if not RM.PUG.IsLeader() then RM.Auction.StartNextIfIdle() end
end)

RM.On("LOOT_SLOT_CLEARED", function(slot)
	for _, item in ipairs(Loot.items) do
		if item.slot == slot then item.done = true end
	end
	RM.Fire("LOOT_CHANGED")
end)

RM.On("LOOT_CLOSED", function()
	local wasOpen = Loot.isOpen
	Loot.isOpen = false
	if wasOpen and C().unlootedReminder then
		local left = 0
		for _, item in ipairs(Loot.items) do
			if not item.done and item.action ~= "auction" then left = left + 1 end
		end
		if left > 0 then
			RM.Print(string.format(L["Achtung: Es liegen noch %d Item(s) ohne Versteigerung im Loot."], left))
		end
	end
	RM.Fire("LOOT_CHANGED")
end)

---------------------------------------------------------------------------
-- Erinnerung: Boss noch nicht geplündert
---------------------------------------------------------------------------
function Loot.OnBossKilled(bossName)
	if not C().unlootedReminder then return end
	local token = { name = bossName, t = GetTime() }
	Loot.pendingBoss = token
	C_Timer.After(90, function()
		if Loot.pendingBoss == token and RM.IAmMasterLooter() then
			PlaySound(SOUNDKIT and SOUNDKIT.RAID_WARNING or 8959)
			RaidNotice_AddMessage(RaidWarningFrame, "RaidMaster: " .. bossName .. L[" wurde noch nicht geplündert!"], ChatTypeInfo["RAID_WARNING"])
			RM.Print(bossName .. L[" wurde noch nicht geplündert!"])
			Loot.pendingBoss = nil
		end
	end)
end

RM.On("PLAYER_ENTERING_WORLD", function()
	wipe(announced)
	wipe(queuedFromSource)
end)
