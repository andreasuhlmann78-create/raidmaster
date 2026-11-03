-- RaidMaster - Berufe-Verzeichnis
-- Knopf "Meine Berufe einlesen" (Seite Skillungen oder /rm berufe): öffnet nacheinander deine Berufsfenster und
-- liest Stufe und alle Rezepte aus. Öffnest du ein Berufsfenster selbst, wird es ebenfalls gelesen.
-- Die Liste geht an die Gilde (Addon-Nachricht), so hat der Uploader die Berufe aller Addon-Nutzer.
-- Der Discord-Bot zeigt daraus: /handwerk <Item> (wer kann es herstellen), /berufe <Name>.
--
--   RaidMasterDB.prof[Name] = { c = Klasse, t = Zeit, p = { [Beruf] = { r = Stufe, m = max, i = { Item-IDs }, n = { Namen } } } }
--   (i und n gehören zusammen: n[k] ist der Name zu i[k]; Rezepte ohne Item, z. B. Verzauberungen, haben i[k] = 0)
--   RaidMasterDB.recipeMats[Rezeptname] = { p = Beruf, r = { { id = Item-ID, n = Name, c = Anzahl }, ... } }
--   – nur besondere Zutaten (ab Grün, z. B. Raid-Materialien wie Lavakern). Daraus zeigt der Bot in #regeln,
--   wofür die Materialien aus den Raids gebraucht werden. Geht wie die Berufe an die Gilde.

local ADDON, RM = ...
local L = RM.L
local P = {}
RM.Prof = P

-- Berufe mit Fenster: Zauber-ID zum Öffnen (Name kommt aus dem Spiel, also in jeder Sprache richtig)
P.CRAFT_SPELLS = { 2259, 2018, 7411, 4036, 2108, 3908, 2550, 3273, 2656 }   -- Alchimie … Erste Hilfe, Verhüttung (Bergbau)
P.GATHERING = {}   -- Kräuterkunde, Bergbau, Kürschnerei: nur Stufe (aus der Fertigkeitenliste)

local function Store()
	RM.db.prof = RM.db.prof or {}
	return RM.db.prof
end

local function Mine()
	local s = Store()
	local me = RM.Me()
	s[me] = s[me] or { p = {} }
	s[me].c = select(2, UnitClass("player"))
	return s[me]
end

-- Stufen aller Berufe aus der Fertigkeitenliste (auch Sammelberufe).
-- Moderner Client (WoW Forever, Retail) ohne Fertigkeitenliste: über GetProfessions/GetProfessionInfo.
local function ReadProfessionSlots()
	local out = {}
	local GetProfessions, GetProfessionInfo = RM.API.Get("GetProfessions"), RM.API.Get("GetProfessionInfo")
	if not (GetProfessions and GetProfessionInfo) then return out end
	local slots = { pcall(GetProfessions) }
	if not table.remove(slots, 1) then return out end
	for i = 1, 6 do
		local idx = slots[i]
		if idx then
			local ok, name, _, rank, max, _, _, skillLine = pcall(GetProfessionInfo, idx)
			-- l = Fertigkeitslinie (zum Öffnen des Fensters); wird nicht in RaidMasterDB.prof gespeichert
			if ok and type(name) == "string" and name ~= "" then out[name] = { r = rank or 0, m = max or 0, l = skillLine } end
		end
	end
	return out
end
P.ReadProfessionSlots = ReadProfessionSlots

function P.ReadSkillLines()
	local out = {}
	if not GetNumSkillLines then
		if RM.IsModern then return ReadProfessionSlots() end
		return out
	end
	local section
	for i = 1, GetNumSkillLines() do
		local name, isHeader, _, rank, _, _, max = GetSkillLineInfo(i)
		if isHeader then
			section = name
		elseif name and (section == TRADE_SKILLS or section == SECONDARY_SKILLS or section == L["Berufe"] or section == L["Sekundäre Fertigkeiten"]) then
			out[name] = { r = rank, m = max }
		end
	end
	return out
end

local function ItemIDFromLink(link)
	return type(link) == "string" and tonumber(link:match("item:(%d+)")) or 0
end

P.MAT_QUALITY = 2          -- Zutaten ab Grün merken (Raid-Materialien), einfache Stoffe/Kräuter nicht

local function Mats()
	RM.db.recipeMats = RM.db.recipeMats or {}
	return RM.db.recipeMats
end

-- besondere Zutaten eines Rezepts: { { id, n, c } } (leer = nur einfache Zutaten)
local function ReadReagents(kind, i)
	local out = {}
	local num = kind == "craft" and (GetCraftNumReagents and GetCraftNumReagents(i)) or (GetTradeSkillNumReagents and GetTradeSkillNumReagents(i))
	for j = 1, (num or 0) do
		local name, _, count
		local link
		if kind == "craft" then
			if GetCraftReagentInfo then name, _, count = GetCraftReagentInfo(i, j) end
			link = GetCraftReagentItemLink and GetCraftReagentItemLink(i, j)
		else
			if GetTradeSkillReagentInfo then name, _, count = GetTradeSkillReagentInfo(i, j) end
			link = GetTradeSkillReagentItemLink and GetTradeSkillReagentItemLink(i, j)
		end
		local id = ItemIDFromLink(link)
		local quality = link and RM.ItemQuality and RM.ItemQuality(link) or 0
		if id > 0 and quality >= P.MAT_QUALITY then out[#out + 1] = { id = id, n = name, c = count or 1 } end
	end
	return out
end

---------------------------------------------------------------------------
-- Moderne Berufe-API (WoW Forever, Retail): C_TradeSkillUI. Gleiches Datenformat wie der alte Weg.
-- Vorbild: Scan.lua in ProfessionSentinel. IM CLIENT TESTEN (Forever 1.60.1).
---------------------------------------------------------------------------
-- C_TradeSkillUI über RM.API (die Testroutine stellt so Rezeptdaten nach, ohne Blizzard-Funktionen zu ersetzen)
local function TradeSkillAPI() return RM.API.Get("C_TradeSkillUI") end

function P.HasModernAPI()
	local TS = TradeSkillAPI()
	return RM.IsModern and TS ~= nil and TS.GetAllRecipeIDs ~= nil and TS.GetRecipeInfo ~= nil
end

-- eigenes Fenster? (nicht verlinkt, nicht Gilde, nicht NPC)
local function IsOwnModern()
	local TS = TradeSkillAPI()
	for _, f in ipairs({ "IsTradeSkillLinked", "IsTradeSkillGuild", "IsNPCCrafting" }) do
		if TS[f] then
			local ok, r = pcall(TS[f])
			if ok and r then return false end
		end
	end
	return true
end

-- Name und Stufe des offenen Berufs: Basisberuf (z. B. "Lederverarbeitung"), Stufe der aktuellen Linie
local function ModernProfession()
	local TS = TradeSkillAPI()
	local name, rank, max
	for _, f in ipairs({ "GetChildProfessionInfo", "GetBaseProfessionInfo" }) do
		if TS[f] then
			local ok, info = pcall(TS[f])
			if ok and type(info) == "table" then
				name = name or info.parentProfessionName or info.professionName
				if (info.maxSkillLevel or 0) > 0 and not rank then rank, max = info.skillLevel or 0, info.maxSkillLevel end
			end
		end
	end
	if type(name) ~= "string" or name == "" then return nil end
	-- gleiche Schreibweise wie in der Fertigkeitenliste, falls dort vorhanden
	local slots = ReadProfessionSlots()
	if slots[name] and not rank then rank, max = slots[name].r, slots[name].m end
	return name, rank or 0, max or 0
end

-- hergestelltes Item eines Rezepts (0 = keins, z. B. Verzauberung)
local function ModernOutput(id)
	local TS = TradeSkillAPI()
	if TS.GetRecipeOutputItemData then
		local ok, d = pcall(TS.GetRecipeOutputItemData, id)
		if ok and type(d) == "table" then
			if tonumber(d.itemID) then return tonumber(d.itemID) end
			if d.hyperlink then return ItemIDFromLink(d.hyperlink) end
		end
	end
	if TS.GetRecipeItemLink then
		local ok, link = pcall(TS.GetRecipeItemLink, id)
		if ok then return ItemIDFromLink(link) end
	end
	return 0
end

-- besondere Zutaten (ab Grün) eines Rezepts
local function ModernReagents(id)
	local TS = TradeSkillAPI()
	local out = {}
	local function add(itemID, count)
		itemID = tonumber(itemID)
		if not itemID or itemID <= 0 then return end
		local name, link, quality = RM.GetItemInfo(itemID)
		quality = quality or (link and RM.ItemQuality(link)) or 0
		if quality >= P.MAT_QUALITY then out[#out + 1] = { id = itemID, n = name, c = count or 1 } end
	end
	if TS.GetRecipeSchematic then
		local ok, sch = pcall(TS.GetRecipeSchematic, id, false)
		if ok and type(sch) == "table" and type(sch.reagentSlotSchematics) == "table" then
			for _, slot in ipairs(sch.reagentSlotSchematics) do
				local r = type(slot.reagents) == "table" and slot.reagents[1]
				if r then add(r.itemID, slot.quantityRequired) end
			end
			return out
		end
	end
	if TS.GetRecipeNumReagents and TS.GetRecipeReagentItemLink then
		local ok, num = pcall(TS.GetRecipeNumReagents, id)
		for j = 1, (ok and num or 0) do
			local okL, link = pcall(TS.GetRecipeReagentItemLink, id, j)
			local count = 1
			if TS.GetRecipeReagentInfo then
				local okI, _, _, c = pcall(TS.GetRecipeReagentInfo, id, j)
				if okI and c then count = c end
			end
			if okL then add(ItemIDFromLink(link), count) end
		end
	end
	return out
end

function P.ScanModern()
	local TS = TradeSkillAPI()
	if not RM.db or not P.HasModernAPI() or not IsOwnModern() then return nil end
	local profName, rank, max = ModernProfession()
	if not profName then return nil end
	local okIds, recipeIDs = pcall(TS.GetAllRecipeIDs)
	if not okIds or type(recipeIDs) ~= "table" then return nil end
	local ids, names, mats = {}, {}, {}
	for _, id in ipairs(recipeIDs) do
		local ok, info = pcall(TS.GetRecipeInfo, id)
		if ok and type(info) == "table" and info.learned and type(info.name) == "string" and not info.isDummyRecipe then
			ids[#ids + 1] = ModernOutput(id)
			names[#names + 1] = info.name
			local rg = ModernReagents(id)
			if #rg > 0 then mats[info.name] = rg end
		end
	end
	if #names == 0 then return nil end   -- Liste noch nicht geladen: TRADE_SKILL_LIST_UPDATE versucht es erneut
	return profName, rank, max, ids, names, mats
end

-- offenes Berufsfenster lesen (Fertigkeiten-Fenster oder – für Verzauberkunst in Classic – Handwerksfenster)
function P.ScanOpen(kind)
	if not RM.db then return nil end
	-- moderner Client: eigener Weg, gleiche Daten
	if kind == "trade" and P.HasModernAPI() then
		local profName, rank, max, ids, names, mats = P.ScanModern()
		if not profName then return nil end
		return P.StoreScan(profName, rank, max, ids, names, mats)
	end
	local profName, rank, max
	local ids, names, mats = {}, {}, {}
	if kind == "craft" then
		if not GetCraftDisplaySkillLine then return nil end
		profName, rank, max = GetCraftDisplaySkillLine()
		for i = 1, (GetNumCrafts and GetNumCrafts() or 0) do
			local name, _, ctype = GetCraftInfo(i)
			if name and ctype ~= "header" then
				ids[#ids + 1] = ItemIDFromLink(GetCraftItemLink and GetCraftItemLink(i))
				names[#names + 1] = name
				local rg = ReadReagents("craft", i)
				if #rg > 0 then mats[name] = rg end
			end
		end
	else
		if not GetTradeSkillLine then return nil end
		profName, rank, max = GetTradeSkillLine()
		for i = 1, (GetNumTradeSkills and GetNumTradeSkills() or 0) do
			local name, ttype = GetTradeSkillInfo(i)
			if name and ttype ~= "header" then
				ids[#ids + 1] = ItemIDFromLink(GetTradeSkillItemLink and GetTradeSkillItemLink(i))
				names[#names + 1] = name
				local rg = ReadReagents("trade", i)
				if #rg > 0 then mats[name] = rg end
			end
		end
	end
	if not profName or profName == "" or profName == "UNKNOWN" then return nil end
	return P.StoreScan(profName, rank, max, ids, names, mats)
end

-- Ergebnis speichern (für alten und modernen Weg gleich; Format von RaidMasterDB.prof nicht ändern)
function P.StoreScan(profName, rank, max, ids, names, mats)
	local me = Mine()
	me.p[profName] = { r = rank, m = max, i = ids, n = names }
	local store = Mats()
	for recipe, rg in pairs(mats) do store[recipe] = { p = profName, r = rg } end
	me.t = RM.Now()
	-- Sammelberufe und Stufen ergänzen
	for name, v in pairs(P.ReadSkillLines()) do
		me.p[name] = me.p[name] or {}
		me.p[name].r, me.p[name].m = v.r, v.m
	end
	P.scanned = P.scanned or {}
	P.scanned[profName] = true
	RM.Fire("PROF_CHANGED", RM.Me())
	P.ScheduleSend()
	return profName, #names
end

---------------------------------------------------------------------------
-- Knopf: nacheinander die Berufsfenster öffnen (jeder Klick öffnet den nächsten)
---------------------------------------------------------------------------
-- Moderner Client: Berufe sind keine Zauber im Zauberbuch mehr. Die Liste kommt aus GetProfessions, geöffnet
-- wird über die Fertigkeitslinie (C_TradeSkillUI.OpenTradeSkill). Ohne Rezepte: Kräuterkunde, Kürschnerei,
-- Angeln, Archäologie (klassische Linien und die Kindlinien von WoW Forever).
P.NO_RECIPE_LINES = { [182] = true, [393] = true, [356] = true, [794] = true, [2944] = true, [2947] = true, [2943] = true }
P.lineByName = {}

local function ModernOpenable()
	local list = {}
	wipe(P.lineByName)
	for name, v in pairs(ReadProfessionSlots()) do
		if v.l and not P.NO_RECIPE_LINES[v.l] then
			list[#list + 1] = name
			P.lineByName[name] = v.l
		end
	end
	table.sort(list)
	return list
end

-- Berufsfenster öffnen: moderner Client über die Fertigkeitslinie, sonst (und als Rückfall) über den Zauber
local function OpenProfession(name)
	local TS = TradeSkillAPI()
	local line = P.lineByName[name]
	if line and TS and TS.OpenTradeSkill then
		local ok = pcall(RM.Act.OpenTradeSkill, line)
		if ok then return end
	end
	if CastSpellByName then RM.Act.CastSpellByName(name) end
end

function P.Openable()
	if P.HasModernAPI() and RM.API.Get("GetProfessions") and RM.API.Get("GetProfessionInfo") then
		local list = ModernOpenable()
		if #list > 0 then return list end
	end
	local list = {}
	local skills = P.ReadSkillLines()
	for _, id in ipairs(P.CRAFT_SPELLS) do
		local name = RM.GetSpellName(id)
		if name then
			-- Verhüttung gehört zu Bergbau; die anderen heißen wie der Beruf
			local skill = (id == 2656) and (RM.GetSpellName(2575) or L["Bergbau"]) or name
			if skills[skill] or skills[name] then list[#list + 1] = name end
		end
	end
	return list
end

P.pendingScan = nil
function P.ReadNext()
	if RM.InCombat() then RM.Print(L["Im Kampf geht das nicht."]) return end
	P.scanned = P.scanned or {}
	local list = P.Openable()
	if #list == 0 then
		-- keine Berufsfenster: nur Stufen speichern
		local me = Mine()
		for name, v in pairs(P.ReadSkillLines()) do me.p[name] = { r = v.r, m = v.m } end
		me.t = RM.Now()
		RM.Print(L["Keine Berufe mit Rezepten gefunden – Stufen gespeichert."])
		P.ScheduleSend()
		return
	end
	for _, name in ipairs(list) do
		if not P.scanned[name] then
			P.pendingScan = name
			OpenProfession(name)
			return
		end
	end
	wipe(P.scanned)
	RM.Print(string.format(L["Alle Berufe eingelesen (%d). Die Liste geht an die Gilde und an Discord."], #list))
end

local function AfterScan(kind)
	local name, n = P.ScanOpen(kind)
	if not name then return end
	if P.pendingScan then
		-- moderner Client: der Listenname (aus GetProfessions) kann vom Fensternamen abweichen –
		-- als gelesen merken, sonst öffnet der nächste Klick denselben Beruf erneut
		if P.HasModernAPI() then P.scanned[P.pendingScan] = true end
		P.pendingScan = nil
		RM.Print(string.format(L["%s eingelesen (%d Rezepte). Nochmal klicken für den nächsten Beruf."], name, n))
		C_Timer.After(0.2, function()
			local TS = TradeSkillAPI()
			if kind == "craft" and CloseCraft then CloseCraft()
			elseif CloseTradeSkill then CloseTradeSkill()
			elseif TS and TS.CloseTradeSkill then pcall(TS.CloseTradeSkill) end
		end)
	end
end
RM.On("TRADE_SKILL_SHOW", function() C_Timer.After(0.3, function() AfterScan("trade") end) end)
RM.On("CRAFT_SHOW", function() C_Timer.After(0.3, function() AfterScan("craft") end) end)
-- moderner Client: die Rezeptliste kommt oft erst nach dem Öffnen – dann noch einmal lesen
local listPending
RM.On("TRADE_SKILL_LIST_UPDATE", function()
	if not P.HasModernAPI() or listPending then return end
	listPending = true
	C_Timer.After(0.5, function() listPending = false; AfterScan("trade") end)
end)

---------------------------------------------------------------------------
-- An die Gilde (die Berufe aller Addon-Nutzer landen so beim Uploader)
---------------------------------------------------------------------------
local sendPending
function P.ScheduleSend()
	if sendPending or not C_Timer then return end
	sendPending = true
	C_Timer.After(5, function()
		sendPending = false
		P.SendMine()
	end)
end

function P.SendMine(channel)
	local me = RM.db and RM.db.prof and RM.db.prof[RM.Me()]
	if not me or not RM.MyGuild() then return end
	RM.Comm.Send("PROF", { c = me.c, t = me.t, p = me.p }, channel or "GUILD")
	-- besondere Zutaten der eigenen Rezepte (für "Wofür braucht man Lavakern?" im Discord)
	local mine = {}
	local n = 0
	for _, v in pairs(me.p or {}) do
		for _, recipe in ipairs(v.n or {}) do
			local m = RM.db.recipeMats and RM.db.recipeMats[recipe]
			if m then mine[recipe] = m; n = n + 1 end
		end
	end
	if n > 0 then RM.Comm.Send("RCP", { m = mine }, channel or "GUILD") end
end

RM.Comm.Register("RCP", function(sender, d, channel)
	if type(d.m) ~= "table" or (channel ~= "WHISPER" and channel ~= "GUILD") then return end
	local store = Mats()
	for recipe, m in pairs(d.m) do
		if type(recipe) == "string" and type(m) == "table" and type(m.r) == "table" then store[recipe] = { p = m.p, r = m.r } end
	end
end)

RM.Comm.Register("PROF", function(sender, d, channel)
	if type(d.p) ~= "table" then return end
	if channel ~= "WHISPER" and channel ~= "GUILD" then return end
	local s = Store()
	local old = s[sender]
	if old and (old.t or 0) > (d.t or 0) then return end
	s[sender] = { c = d.c, t = d.t or RM.Now(), p = d.p }
	RM.Fire("PROF_CHANGED", sender)
end)

-- einmal am Tag nach dem Einloggen die eigenen Berufe verteilen
RM.On("PLAYER_LOGIN", function()
	if not C_Timer then return end
	C_Timer.After(40, function()
		local me = RM.db and RM.db.prof and RM.db.prof[RM.Me()]
		if me and (RM.db.config.profSent or 0) < RM.Now() - 86400 then
			RM.db.config.profSent = RM.Now()
			P.SendMine()
		end
	end)
end)

-- Wer kann das herstellen? (Teil des Namens) -> { {name, prof, recipe}, ... }
function P.Find(query)
	query = (query or ""):lower()
	local out = {}
	if query == "" then return out end
	for who, e in pairs((RM.db and RM.db.prof) or {}) do
		for prof, v in pairs(e.p or {}) do
			for _, n in ipairs(v.n or {}) do
				if n:lower():find(query, 1, true) then out[#out + 1] = { name = who, prof = prof, recipe = n } end
			end
		end
	end
	table.sort(out, function(a, b) return a.recipe == b.recipe and a.name < b.name or a.recipe < b.recipe end)
	return out
end

function P.PrintFind(query)
	local list = P.Find(query)
	if #list == 0 then RM.Print(string.format(L["Niemand mit RaidMaster kann '%s' herstellen (oder hat seine Berufe noch nicht eingelesen)."], query or "")) return end
	for i, x in ipairs(list) do
		if i > 15 then RM.Print(string.format(L["… und %d weitere"], #list - 15)) break end
		RM.Print(string.format("%s – %s (%s)", x.recipe, x.name, x.prof))
	end
end
