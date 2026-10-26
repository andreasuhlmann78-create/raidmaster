-- RaidMaster - Bestand der Gildenbank
-- Auf dem Bank-Charakter der Gilde: Öffnet er seine Bank (oder – falls es sie gibt – die Gildenbank), liest
-- RaidMaster Taschen, Bankfächer, Gold und die Post (Anhänge im Briefkasten) aus. Der Uploader schickt den Stand
-- an den Bot; der zeigt ihn in #gildenbank und mit /bank <Suche>.
-- Welcher Charakter? Einstellungen > "Bank-Charakter (Bestand an Discord)" (oder der Name unter Loot >
-- Gildenbank-Charakter).
--
--   RaidMasterDB.bank = { c = Name, t = Zeit, g = Gold (Kupfer), gb = Gold der Gildenbank,
--                         i = { [Item-ID] = { n = Name, q = Qualität, c = Anzahl, ic = Symbol, w = { bag = x, bank = y, mail = z, guild = w } } } }

local ADDON, RM = ...
local L = RM.L
local B = {}
RM.Bank = B

local function C() return RM.db.config end

function B.IsBankChar()
	if not RM.db then return false end
	if C().bankScan then return true end
	local bc = C().bankChar
	return type(bc) == "string" and bc ~= "" and RM.SameName(RM.Short(bc), RM.Me())
end

-- Behälter-API (neue Clients: C_Container)
local function NumSlots(bag)
	if C_Container and C_Container.GetContainerNumSlots then return C_Container.GetContainerNumSlots(bag) or 0 end
	return GetContainerNumSlots and GetContainerNumSlots(bag) or 0
end

local function SlotInfo(bag, slot)
	if C_Container and C_Container.GetContainerItemInfo then
		local info = C_Container.GetContainerItemInfo(bag, slot)
		if info then return info.hyperlink, info.stackCount or 1, info.iconFileID end
		return nil
	end
	if GetContainerItemInfo then
		local icon, count, _, _, _, _, link = GetContainerItemInfo(bag, slot)
		link = link or (GetContainerItemLink and GetContainerItemLink(bag, slot))
		return link, count or 1, icon
	end
end

local function ItemID(link)
	return type(link) == "string" and tonumber(link:match("item:(%d+)")) or nil
end

local current        -- wird beim Lesen gefüllt: { [id] = {...} }

local function Add(where, link, count, icon)
	local id = ItemID(link)
	if not id then return end
	local e = current[id]
	if not e then
		local name, _, q = (RM.GetItemInfo or GetItemInfo)(link)
		e = { n = name or link:match("%[(.-)%]"), q = q, c = 0, ic = icon, w = {} }
		current[id] = e
	end
	e.c = e.c + (count or 1)
	e.w[where] = (e.w[where] or 0) + (count or 1)
end

-- vorhandene Teile des Bestands übernehmen (z. B. Post, wenn nur die Bank gelesen wird)
local function Start(keep)
	current = {}
	local old = RM.db.bank and RM.db.bank.c == RM.Me() and RM.db.bank.i or {}
	for id, e in pairs(old) do
		for where, n in pairs(e.w or {}) do
			if keep[where] then
				current[id] = current[id] or { n = e.n, q = e.q, c = 0, ic = e.ic, w = {} }
				current[id].c = current[id].c + n
				current[id].w[where] = n
			end
		end
	end
end

local function Finish(source, quiet)
	local b = RM.db.bank and RM.db.bank.c == RM.Me() and RM.db.bank or {}
	b.c = RM.Me()
	b.t = GetServerTime()
	b.g = GetMoney and GetMoney() or b.g
	b.i = current
	b.src = source
	RM.db.bank = b
	local n = 0
	for _ in pairs(current) do n = n + 1 end
	if not quiet then
		RM.Print(string.format(L["Gildenbank-Bestand gelesen: %d verschiedene Items (%s). Er kommt mit dem nächsten Upload in den Discord."], n, source))
	end
	RM.Fire("BANK_CHANGED")
	current = nil
end

local function ScanBags(where, from, to)
	for bag = from, to do
		for slot = 1, NumSlots(bag) do
			local link, count, icon = SlotInfo(bag, slot)
			if link then Add(where, link, count, icon) end
		end
	end
end

-- Taschen + Bank (beim Öffnen der Bank)
function B.ScanBank()
	if not B.IsBankChar() then return end
	Start({ mail = true, guild = true })
	ScanBags("bag", 0, NUM_BAG_SLOTS or 4)
	ScanBags("bank", BANK_CONTAINER or -1, BANK_CONTAINER or -1)
	local first = (NUM_BAG_SLOTS or 4) + 1
	ScanBags("bank", first, first + (NUM_BANKBAGSLOTS or 6) - 1)
	Finish(L["Taschen und Bank"])
end

-- Post: Anhänge im Briefkasten (Spenden)
function B.ScanMail()
	if not B.IsBankChar() or not GetInboxNumItems then return end
	Start({ bag = true, bank = true, guild = true })
	for i = 1, GetInboxNumItems() do
		for j = 1, (ATTACHMENTS_MAX_RECEIVE or 16) do
			local link = GetInboxItemLink and GetInboxItemLink(i, j)
			if link then
				local _, _, icon, count = GetInboxItem(i, j)
				Add("mail", link, count or 1, icon)
			end
		end
	end
	Finish(L["Post"], true)
end

-- Gildenbank (falls die Spielversion sie hat)
local guildPending
function B.ScanGuildBank()
	if not B.IsBankChar() or not GetNumGuildBankTabs then return end
	Start({ bag = true, bank = true, mail = true })
	for tab = 1, GetNumGuildBankTabs() do
		for slot = 1, (MAX_GUILDBANK_SLOTS_PER_TAB or 98) do
			local link = GetGuildBankItemLink and GetGuildBankItemLink(tab, slot)
			if link then
				local icon, count = GetGuildBankItemInfo(tab, slot)
				Add("guild", link, count or 1, icon)
			end
		end
	end
	if RM.db.bank then RM.db.bank.gb = GetGuildBankMoney and GetGuildBankMoney() or nil end
	Finish(L["Gildenbank"])
end

RM.On("BANKFRAME_OPENED", function() C_Timer.After(0.5, B.ScanBank) end)
RM.On("MAIL_INBOX_UPDATE", function()
	if guildPending == "mail" then return end
	guildPending = "mail"
	C_Timer.After(1, function() guildPending = nil; B.ScanMail() end)
end)
RM.On("GUILDBANKFRAME_OPENED", function()
	if not B.IsBankChar() or not GetNumGuildBankTabs then return end
	-- alle Fächer beim Server anfragen, dann lesen
	for tab = 1, GetNumGuildBankTabs() do if QueryGuildBankTab then QueryGuildBankTab(tab) end end
	C_Timer.After(2, B.ScanGuildBank)
end)

-- Suche im Spiel: /rm bank <Name>
function B.Find(query)
	query = (query or ""):lower()
	local out = {}
	for id, e in pairs((RM.db.bank and RM.db.bank.i) or {}) do
		if query == "" or (e.n and e.n:lower():find(query, 1, true)) then out[#out + 1] = { id = id, e = e } end
	end
	table.sort(out, function(a, b) return (a.e.n or "") < (b.e.n or "") end)
	return out
end

function B.PrintFind(query)
	local list = B.Find(query)
	if #list == 0 then RM.Print(L["Nichts davon in der Gildenbank."]) return end
	for i, x in ipairs(list) do
		if i > 15 then RM.Print(string.format(L["… und %d weitere"], #list - 15)) break end
		RM.Print(string.format("%s ×%d", x.e.n or ("item:" .. x.id), x.e.c))
	end
end
