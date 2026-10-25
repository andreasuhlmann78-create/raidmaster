-- RaidMaster - Item-Tooltips für Discord
-- Liest den Tooltip eines Items so, wie er im Spiel erscheint (Werte, Rüstung, Anlegen-Effekte ...),
-- samt Item-Symbol und speichert ihn in RaidMasterDB.itemTips. Der Uploader schickt die Datei an den Bot,
-- der die vergebenen Items im Loot-Kanal wie im Spiel-Tooltip anzeigt (farbig nach Qualität, mit Symbol).

local ADDON, RM = ...
local IT = {}
RM.ItemTip = IT

IT.MAX = 600            -- so viele Items höchstens merken (älteste fliegen raus)

local function Store()
	RM.db.itemTips = RM.db.itemTips or {}
	return RM.db.itemTips
end

local tip
local function ScanTip()
	if tip then return tip end
	local ok, t = pcall(CreateFrame, "GameTooltip", "RaidMasterScanTip", nil, "GameTooltipTemplate")
	if not ok or not t then return nil end
	tip = t
	return tip
end

-- Farbe einer Tooltipzeile grob einordnen: g = grün (Anlegen/Benutzen), r = rot (nicht nutzbar),
-- y = gelb (Beschreibung/Set), d = grau, w = weiß
local function ColorClass(fs)
	if not fs or not fs.GetTextColor then return "w" end
	local r, g, b = fs:GetTextColor()
	r, g, b = r or 1, g or 1, b or 1
	if g > 0.8 and r < 0.3 and b < 0.3 then return "g" end
	if r > 0.8 and g < 0.3 and b < 0.3 then return "r" end
	if r > 0.8 and g > 0.7 and b < 0.3 then return "y" end
	if math.abs(r - g) < 0.05 and math.abs(g - b) < 0.05 and r < 0.7 then return "d" end
	return "w"
end

local function Clean(text)
	if not text then return nil end
	text = text:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("|", "/")
	text = text:gsub("^%s+", ""):gsub("%s+$", "")
	if text == "" then return nil end
	return text
end

-- Tooltip eines Items lesen und merken; false = Item noch nicht vom Server geladen
function IT.Scan(link)
	if type(link) ~= "string" then return false end
	local id = tonumber(link:match("item:(%d+)"))
	if not id then return false end
	local t = ScanTip()
	if not t then return false end
	local ok = pcall(function()
		t:SetOwner(WorldFrame, "ANCHOR_NONE")
		t:ClearLines()
		t:SetHyperlink(link:match("|H(item:[^|]+)|h") or link)
	end)
	if not ok then return false end
	local n = t.NumLines and t:NumLines() or 0
	if type(n) ~= "number" or n < 2 then return false end
	local first = _G["RaidMasterScanTipTextLeft1"]
	local name = first and Clean(first:GetText())
	if not name or (RETRIEVING_ITEM_INFO and name == RETRIEVING_ITEM_INFO) then return false end
	local lines = {}
	for i = 2, math.min(n, 30) do
		local left = _G["RaidMasterScanTipTextLeft" .. i]
		local right = _G["RaidMasterScanTipTextRight" .. i]
		local lt = left and Clean(left:GetText())
		local rt = right and (not right.IsShown or right:IsShown()) and Clean(right:GetText())
		if lt or rt then
			lines[#lines + 1] = ColorClass(left) .. "|" .. (lt or "") .. (rt and ("|" .. rt) or "")
		end
	end
	local quality = select(3, (RM.GetItemInfo or GetItemInfo)(link))
	-- Symbol des Items (Pfad "Interface\Icons\INV_..." oder Datei-ID) – der Bot zeigt damit das echte Spielsymbol
	local icon
	if GetItemIcon then icon = GetItemIcon(id) end
	if not icon then icon = select(5, (RM.GetItemInfoInstant or GetItemInfoInstant or function() end)(id)) end
	if not icon then icon = select(10, (RM.GetItemInfo or GetItemInfo)(link)) end
	local store = Store()
	store[id] = { n = name, q = quality, l = lines, ic = icon, t = time() }
	IT.Prune()
	return true
end

function IT.Has(link)
	local id = type(link) == "string" and tonumber(link:match("item:(%d+)"))
	return id and RM.db and RM.db.itemTips and RM.db.itemTips[id] ~= nil
end

-- merken, bei noch nicht geladenen Items ein paar Mal neu versuchen
function IT.Remember(link, tries)
	if not RM.db or IT.Has(link) then return end
	if IT.Scan(link) then return end
	tries = (tries or 0) + 1
	if tries <= 5 and C_Timer then
		C_Timer.After(1, function() IT.Remember(link, tries) end)
	end
end

function IT.Prune()
	local store = Store()
	local list = {}
	for id, e in pairs(store) do list[#list + 1] = { id = id, t = type(e) == "table" and e.t or 0 } end
	if #list <= IT.MAX then return end
	table.sort(list, function(a, b) return a.t < b.t end)
	for i = 1, #list - IT.MAX do store[list[i].id] = nil end
end

-- vergebene Items: beim Abbuchen merken
if RM.DKP and RM.DKP.ChargeItem then
	local orig = RM.DKP.ChargeItem
	RM.DKP.ChargeItem = function(name, amount, link, pool)
		IT.Remember(link)
		return orig(name, amount, link, pool)
	end
end

-- Items in der Warteschlange und in der laufenden Versteigerung schon vorab lesen
RM.Listen("AUCTION_CHANGED", function()
	local A = RM.Auction
	if not A then return end
	if A.current then IT.Remember(A.current.link) end
	for i, q in ipairs(A.queue or {}) do
		if i > 20 then break end
		IT.Remember(q.link)
	end
end)

-- nach dem Einloggen fehlende Tooltips der letzten Items nachholen
RM.On("PLAYER_LOGIN", function()
	if not C_Timer then return end
	C_Timer.After(10, function()
		local log = RM.db and RM.db.data and RM.db.data.log or {}
		local n = 0
		for i = #log, 1, -1 do
			local e = log[i]
			if type(e) == "table" and e.k == "item" and e.i and not IT.Has(e.i) then
				IT.Remember(e.i)
				n = n + 1
				if n >= 60 then break end
			end
		end
	end)
end)
