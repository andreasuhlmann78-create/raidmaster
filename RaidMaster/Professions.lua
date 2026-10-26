-- RaidMaster - Berufe-Verzeichnis
-- Knopf "Meine Berufe einlesen" (Seite Skillungen oder /rm berufe): öffnet nacheinander deine Berufsfenster und
-- liest Stufe und alle Rezepte aus. Öffnest du ein Berufsfenster selbst, wird es ebenfalls gelesen.
-- Die Liste geht an die Gilde (Addon-Nachricht), so hat der Uploader die Berufe aller Addon-Nutzer.
-- Der Discord-Bot zeigt daraus: /handwerk <Item> (wer kann es herstellen), /berufe <Name>.
--
--   RaidMasterDB.prof[Name] = { c = Klasse, t = Zeit, p = { [Beruf] = { r = Stufe, m = max, i = { Item-IDs }, n = { Namen } } } }
--   (i und n gehören zusammen: n[k] ist der Name zu i[k]; Rezepte ohne Item, z. B. Verzauberungen, haben i[k] = 0)

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

-- Stufen aller Berufe aus der Fertigkeitenliste (auch Sammelberufe)
function P.ReadSkillLines()
	local out = {}
	if not GetNumSkillLines then return out end
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

-- offenes Berufsfenster lesen (Fertigkeiten-Fenster oder – für Verzauberkunst in Classic – Handwerksfenster)
function P.ScanOpen(kind)
	if not RM.db then return nil end
	local profName, rank, max
	local ids, names = {}, {}
	if kind == "craft" then
		if not GetCraftDisplaySkillLine then return nil end
		profName, rank, max = GetCraftDisplaySkillLine()
		for i = 1, (GetNumCrafts and GetNumCrafts() or 0) do
			local name, _, ctype = GetCraftInfo(i)
			if name and ctype ~= "header" then
				ids[#ids + 1] = ItemIDFromLink(GetCraftItemLink and GetCraftItemLink(i))
				names[#names + 1] = name
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
			end
		end
	end
	if not profName or profName == "" or profName == "UNKNOWN" then return nil end
	local me = Mine()
	me.p[profName] = { r = rank, m = max, i = ids, n = names }
	me.t = GetServerTime()
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
function P.Openable()
	local list = {}
	local skills = P.ReadSkillLines()
	for _, id in ipairs(P.CRAFT_SPELLS) do
		local name = GetSpellInfo and GetSpellInfo(id)
		if name then
			-- Verhüttung gehört zu Bergbau; die anderen heißen wie der Beruf
			local skill = (id == 2656) and (GetSpellInfo(2575) or L["Bergbau"]) or name
			if skills[skill] or skills[name] then list[#list + 1] = name end
		end
	end
	return list
end

P.pendingScan = nil
function P.ReadNext()
	if InCombatLockdown and InCombatLockdown() then RM.Print(L["Im Kampf geht das nicht."]) return end
	P.scanned = P.scanned or {}
	local list = P.Openable()
	if #list == 0 then
		-- keine Berufsfenster: nur Stufen speichern
		local me = Mine()
		for name, v in pairs(P.ReadSkillLines()) do me.p[name] = { r = v.r, m = v.m } end
		me.t = GetServerTime()
		RM.Print(L["Keine Berufe mit Rezepten gefunden – Stufen gespeichert."])
		P.ScheduleSend()
		return
	end
	for _, name in ipairs(list) do
		if not P.scanned[name] then
			P.pendingScan = name
			if CastSpellByName then CastSpellByName(name) end
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
		P.pendingScan = nil
		RM.Print(string.format(L["%s eingelesen (%d Rezepte). Nochmal klicken für den nächsten Beruf."], name, n))
		C_Timer.After(0.2, function()
			if kind == "craft" and CloseCraft then CloseCraft() elseif CloseTradeSkill then CloseTradeSkill() end
		end)
	end
end
RM.On("TRADE_SKILL_SHOW", function() C_Timer.After(0.3, function() AfterScan("trade") end) end)
RM.On("CRAFT_SHOW", function() C_Timer.After(0.3, function() AfterScan("craft") end) end)

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
end

RM.Comm.Register("PROF", function(sender, d, channel)
	if type(d.p) ~= "table" then return end
	if channel ~= "WHISPER" and channel ~= "GUILD" then return end
	local s = Store()
	local old = s[sender]
	if old and (old.t or 0) > (d.t or 0) then return end
	s[sender] = { c = d.c, t = d.t or GetServerTime(), p = d.p }
	RM.Fire("PROF_CHANGED", sender)
end)

-- einmal am Tag nach dem Einloggen die eigenen Berufe verteilen
RM.On("PLAYER_LOGIN", function()
	if not C_Timer then return end
	C_Timer.After(40, function()
		local me = RM.db and RM.db.prof and RM.db.prof[RM.Me()]
		if me and (RM.db.config.profSent or 0) < GetServerTime() - 86400 then
			RM.db.config.profSent = GetServerTime()
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
