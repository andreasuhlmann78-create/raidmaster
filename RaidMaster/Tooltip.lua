-- RaidMaster - Zusatzzeilen im Item-Tooltip
-- Fährt man im Spiel über ein Item, steht darunter (wenn bekannt):
--   * Droprate aus eurer eigenen Beute-Datenbank (Boss: so oft gedroppt / so oft getötet; Trash: so oft gesehen)
--   * Preisverlauf: wofür es zuletzt versteigert wurde, an wen, und der Durchschnitt
-- Ein-/ausschalten: Einstellungen ("Item-Tooltip ergänzen") – Standard an.

local ADDON, RM = ...
local L = RM.L
local TT = {}
RM.Tooltip = TT

local index           -- [itemID] = { drops = { {boss, c, kills} }, trash = n, sales = { {t, name, amount} } }

function TT.Invalidate() index = nil end
RM.Listen("DATA_CHANGED", TT.Invalidate)
RM.Listen("LOOTDB_CHANGED", TT.Invalidate)
RM.Listen("DB_READY", TT.Invalidate)

local function ItemID(link)
	return type(link) == "string" and tonumber(link:match("item:(%d+)")) or tonumber(link)
end

local function Build()
	index = {}
	local function E(id)
		index[id] = index[id] or { drops = {}, trash = 0, sales = {} }
		return index[id]
	end
	-- Beute-Datenbank
	local s = RM.db and RM.db.lootdb
	if s then
		local kills, count = {}, {}
		for _, k in ipairs(s.kills or {}) do
			kills[k.e] = (kills[k.e] or 0) + 1
			for _, id in ipairs(k.i or {}) do
				count[id] = count[id] or {}
				count[id][k.e] = (count[id][k.e] or 0) + 1
			end
		end
		for id, per in pairs(count) do
			for e, c in pairs(per) do
				local b = s.bosses and s.bosses[e]
				table.insert(E(id).drops, { boss = (b and b.n) or ("Boss " .. e), c = c, kills = kills[e] or c })
			end
			table.sort(E(id).drops, function(a, b) return a.c / a.kills > b.c / b.kills end)
		end
		for _, x in ipairs(s.trash or {}) do
			for _, id in ipairs(x.i or {}) do E(id).trash = E(id).trash + 1 end
		end
	end
	-- Preisverlauf aus den DKP-Buchungen (nicht rückgängig gemachte Item-Käufe)
	local log = RM.db and RM.db.data and RM.db.data.log or {}
	for seq, e in ipairs(log) do
		if e.k == "item" and not e.u and e.i then
			local id = ItemID(e.i)
			if id then
				for name, delta in pairs(e.d or {}) do
					if delta < 0 then table.insert(E(id).sales, { t = e.t or 0, seq = seq, name = name, amount = -delta, pool = e.pool }) end
				end
			end
		end
	end
	for _, x in pairs(index) do
		table.sort(x.sales, function(a, b)
			if a.t ~= b.t then return a.t > b.t end
			return (a.seq or 0) > (b.seq or 0)
		end)
	end
end

-- Infos zu einem Item (für Tooltip und Tests)
function TT.Info(link)
	if not RM.db then return nil end
	if not index then Build() end
	local id = ItemID(link)
	return id and index[id] or nil
end

-- Zeilen für den Tooltip: { {text, r, g, b}, ... }
function TT.Lines(link)
	local x = TT.Info(link)
	if not x then return {} end
	local out = {}
	local head = "|cffff8c1aRaidMaster|r  "
	for i, d in ipairs(x.drops) do
		if i > 2 then break end
		out[#out + 1] = head .. string.format(L["%s: %d/%d Kills (%d %%)"], d.boss, d.c, d.kills, math.floor(d.c / d.kills * 100 + 0.5))
		head = "            "
	end
	if x.trash > 0 then
		out[#out + 1] = head .. string.format(L["Trash: %d× gesehen"], x.trash)
		head = "            "
	end
	if x.sales[1] then
		local last = x.sales[1]
		local sum = 0
		for _, sale in ipairs(x.sales) do sum = sum + sale.amount end
		local avg = math.floor(sum / #x.sales + 0.5)
		local text = string.format(L["Zuletzt %d DKP an %s (%s)"], last.amount, last.name, date("%d.%m.", last.t))
		if #x.sales > 1 then text = text .. string.format(L[" · Ø %d DKP (%d×)"], avg, #x.sales) end
		out[#out + 1] = head .. text
	end
	return out
end

local function OnItem(tt)
	if not RM.db or RM.db.config.itemTooltip == false then return end
	if not tt.GetItem then return end
	local _, link = tt:GetItem()
	if not link then return end
	local lines = TT.Lines(link)
	if #lines == 0 then return end
	for _, line in ipairs(lines) do tt:AddLine(line, 0.85, 0.85, 0.85) end
	tt:Show()
end

local hooked = {}
local function Hook(tt)
	if not tt or hooked[tt] or not tt.HookScript then return end
	hooked[tt] = true
	pcall(tt.HookScript, tt, "OnTooltipSetItem", OnItem)
end

RM.On("PLAYER_LOGIN", function()
	Hook(_G.GameTooltip)
	Hook(_G.ItemRefTooltip)
	Hook(_G.ShoppingTooltip1)
end)
