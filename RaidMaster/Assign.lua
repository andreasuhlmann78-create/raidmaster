-- RaidMaster - Einteilung
-- Erstellt auf Knopfdruck aus den Klassen im Raid: Heilung, Entfluchen, Magie bannen,
-- CC je Boss (Verbannen, Sheep), Unterbrechen, Einlull-Rotation, Furchtschutz, Seelensteine, Anregen.
-- Verteilung: Flüstern (ohne Addon), Addon-Nachricht mit Anzeige beim Pull, Discord (Bot liest nach /reload).

local ADDON, RM = ...
local A = {}
RM.Assign = A

local ICON = { [1] = "{rt1}", [2] = "{rt2}", [3] = "{rt3}", [4] = "{rt4}", [5] = "{rt5}", [6] = "{rt6}", [7] = "{rt7}", [8] = "{rt8}" }
local ICON_NAME = RM.Data.MarkerNames

-- Kontexte: allgemein + Molten-Core-Bosse (Encounter-ID für die Anzeige beim Pull)
A.Contexts = {
	{ key = "general", name = "Allgemein" },
	{ key = "lucifron", name = "Lucifron", enc = 663 },
	{ key = "magmadar", name = "Magmadar", enc = 664 },
	{ key = "gehennas", name = "Gehennas", enc = 665 },
	{ key = "garr", name = "Garr", enc = 666 },
	{ key = "shazzrah", name = "Shazzrah", enc = 667 },
	{ key = "sulfuron", name = "Sulfuronherold", enc = 669 },
	{ key = "golemagg", name = "Golemagg", enc = 670 },
	{ key = "majordomo", name = "Majordomus", enc = 671 },
	{ key = "ragnaros", name = "Ragnaros", enc = 672 },
}
local CTX_BY_ENC = {}
for _, c in ipairs(A.Contexts) do if c.enc then CTX_BY_ENC[c.enc] = c end end

local function ctxName(key)
	for _, c in ipairs(A.Contexts) do if c.key == key then return c.name end end
	return key
end

---------------------------------------------------------------------------
-- Raid analysieren
---------------------------------------------------------------------------
-- Rolle aus der Discord-Anmeldung, sonst aus der Skillung
local function SignupRole(name)
	local su = RM.db.signup
	if su then
		for _, e in ipairs(su.list) do
			if e.name == name and e.role then return e.role end
		end
	end
	return RM.Spec and RM.Spec.Role(name) or nil
end

-- Tanks: eingetragene Liste, sonst Haupttank-Markierung, Discord-Rolle "tank", sonst Krieger
function A.AutoTanks()
	local tanks, seen = {}, {}
	local members = RM.RaidMembers()
	for _, m in ipairs(members) do
		local role = select(10, GetRaidRosterInfo(m.index))
		if role == "MAINTANK" and not seen[m.name] then tanks[#tanks + 1] = m.name; seen[m.name] = true end
	end
	for _, m in ipairs(members) do
		if SignupRole(m.name) == "tank" and not seen[m.name] then tanks[#tanks + 1] = m.name; seen[m.name] = true end
	end
	if #tanks < 2 then
		-- Krieger ohne bekannte Rolle, danach Krieger/Druiden, deren Skillung tanken kann
		for _, m in ipairs(members) do
			if #tanks >= 3 then break end
			if m.class == "WARRIOR" and not seen[m.name] and SignupRole(m.name) == nil then
				tanks[#tanks + 1] = m.name; seen[m.name] = true
			end
		end
		for _, m in ipairs(members) do
			if #tanks >= 2 then break end
			if not seen[m.name] and RM.Spec and RM.Spec.CanRole(m.name, "tank") then
				tanks[#tanks + 1] = m.name; seen[m.name] = true
			end
		end
	end
	return tanks
end

function A.Tanks()
	local text = RM.db.config.assignTanks or ""
	local list = {}
	for name in text:gmatch("[^,%s]+") do
		name = name:sub(1, 1):upper() .. name:sub(2):lower()
		if RM.IsInMyRaid(name) then list[#list + 1] = name end
	end
	if #list == 0 then list = A.AutoTanks() end
	return list
end

-- Mitglieder nach Aufgabe gruppieren
function A.Analyze()
	local r = { tanks = A.Tanks(), healers = {}, byClass = {}, groups = {}, dwarfPriests = {}, interrupt = {}, members = {} }
	local isTank = {}
	for _, t in ipairs(r.tanks) do isTank[t] = true end
	for _, m in ipairs(RM.RaidMembers()) do
		r.members[#r.members + 1] = m
		local _, _, subgroup = GetRaidRosterInfo(m.index)
		r.groups[m.name] = subgroup or 1
		r.byClass[m.class] = r.byClass[m.class] or {}
		table.insert(r.byClass[m.class], m.name)
		local role = SignupRole(m.name)
		local healClass = m.class == "PRIEST" or m.class == "PALADIN" or m.class == "DRUID" or m.class == "SHAMAN"
		if not isTank[m.name] and ((role == "heal") or (role == nil and healClass)) then
			r.healers[#r.healers + 1] = { name = m.name, class = m.class }
		end
		if m.class == "PRIEST" then
			local _, race = UnitRace("raid" .. m.index)
			if race == "Dwarf" then r.dwarfPriests[#r.dwarfPriests + 1] = m.name end
		end
		if not isTank[m.name] and (m.class == "ROGUE" or m.class == "WARRIOR" or (m.class == "SHAMAN" and role ~= "heal")) then
			r.interrupt[#r.interrupt + 1] = m.name
		end
	end
	for _, list in pairs(r.byClass) do table.sort(list) end
	local order = { PRIEST = 1, PALADIN = 2, SHAMAN = 3, DRUID = 4 }
	table.sort(r.healers, function(a, b)
		if order[a.class] ~= order[b.class] then return (order[a.class] or 9) < (order[b.class] or 9) end
		return a.name < b.name
	end)
	table.sort(r.interrupt)
	return r
end

---------------------------------------------------------------------------
-- Erzeugen
---------------------------------------------------------------------------
local function newCtx()
	return { lines = {}, p = {} }
end

local function addPersonal(ctx, name, text)
	if not name then return end
	ctx.p[name] = ctx.p[name] and (ctx.p[name] .. " · " .. text) or text
end

-- Gruppen 1–8 gleichmäßig auf Spieler verteilen
local function splitGroups(names, groupCount)
	local out = {}
	if #names == 0 then return out end
	for g = 1, groupCount do
		local who = names[((g - 1) % #names) + 1]
		out[who] = out[who] or {}
		table.insert(out[who], g)
	end
	return out
end

local function groupCount()
	local maxGroup = 1
	for _, m in ipairs(RM.RaidMembers()) do
		local _, _, sg = GetRaidRosterInfo(m.index)
		if sg and sg > maxGroup then maxGroup = sg end
	end
	return maxGroup
end

local function list(t) return t or {} end

function A.Build()
	if not RM.InRaid() then RM.Print("Du bist in keinem Schlachtzug.") return end
	local r = A.Analyze()
	local T = r.tanks
	local G = groupCount()
	local result = {}

	-------------------------------------------------------------------
	-- Allgemein: Heilung, Entfluchen, Bannen, Furchtschutz, Seelensteine, Anregen
	-------------------------------------------------------------------
	local c = newCtx()
	result.general = c
	local H = r.healers
	if #T > 0 and #H > 0 then
		local tankHealers = math.max(1, math.ceil(#H / 2))
		local mtShare = math.max(1, math.ceil(tankHealers * 0.4))
		local idx = 1
		local perTank = {}
		for i = 1, mtShare do
			if H[idx] then perTank[T[1]] = perTank[T[1]] or {}; table.insert(perTank[T[1]], H[idx].name); idx = idx + 1 end
		end
		local t = 2
		while idx <= tankHealers and H[idx] do
			local tank = T[t] or T[1]
			perTank[tank] = perTank[tank] or {}
			table.insert(perTank[tank], H[idx].name)
			idx = idx + 1
			t = t + 1
			if t > #T then t = 2 end
			if #T == 1 then t = 1 end
		end
		for i, tank in ipairs(T) do
			local hs = perTank[tank]
			if hs then
				c.lines[#c.lines + 1] = string.format("Heilung %s (%s): %s", tank, i == 1 and "MT" or ("OT" .. (i - 1)), table.concat(hs, ", "))
				for _, h in ipairs(hs) do addPersonal(c, h, "Heile " .. tank .. (i == 1 and " (MT)" or "")) end
			end
		end
		local raidHealers = {}
		for i = idx, #H do raidHealers[#raidHealers + 1] = H[i].name end
		local split = splitGroups(raidHealers, G)
		local parts = {}
		for _, h in ipairs(raidHealers) do
			if split[h] then
				parts[#parts + 1] = h .. " G" .. table.concat(split[h], "+")
				addPersonal(c, h, "Raidheilung Gruppe " .. table.concat(split[h], ", "))
			end
		end
		if #parts > 0 then c.lines[#c.lines + 1] = "Raidheilung: " .. table.concat(parts, ", ") end
	end
	-- Entfluchen
	local decurse = {}
	for _, n in ipairs(list(r.byClass.MAGE)) do decurse[#decurse + 1] = n end
	for _, n in ipairs(list(r.byClass.DRUID)) do decurse[#decurse + 1] = n end
	local dsplit = splitGroups(decurse, G)
	local dparts = {}
	for _, n in ipairs(decurse) do
		if dsplit[n] then
			dparts[#dparts + 1] = n .. " G" .. table.concat(dsplit[n], "+")
			addPersonal(c, n, "Entfluchen Gruppe " .. table.concat(dsplit[n], ", "))
		end
	end
	if #dparts > 0 then c.lines[#c.lines + 1] = "Entfluchen: " .. table.concat(dparts, ", ") end
	-- Magie bannen
	local dispel = {}
	for _, n in ipairs(list(r.byClass.PRIEST)) do dispel[#dispel + 1] = n end
	for _, n in ipairs(list(r.byClass.PALADIN)) do dispel[#dispel + 1] = n end
	local bsplit = splitGroups(dispel, G)
	local bparts = {}
	for _, n in ipairs(dispel) do
		if bsplit[n] then
			bparts[#bparts + 1] = n .. " G" .. table.concat(bsplit[n], "+")
			addPersonal(c, n, "Magie bannen Gruppe " .. table.concat(bsplit[n], ", "))
		end
	end
	if #bparts > 0 then c.lines[#c.lines + 1] = "Bannen: " .. table.concat(bparts, ", ") end
	-- Furchtschutz (Zwergenpriester) auf die Tanks
	for i, p in ipairs(r.dwarfPriests) do
		local tank = T[i]
		if tank then
			c.lines[#c.lines + 1] = "Furchtschutz: " .. p .. " -> " .. tank
			addPersonal(c, p, "Furchtschutz auf " .. tank)
		end
	end
	-- Seelensteine: Hexer -> Heiler, die wiederbeleben können
	local rezzers = {}
	for _, h in ipairs(H) do if h.class ~= "DRUID" then rezzers[#rezzers + 1] = h.name end end
	for i, w in ipairs(list(r.byClass.WARLOCK)) do
		local target = rezzers[i]
		if target then
			c.lines[#c.lines + 1] = "Seelenstein: " .. w .. " -> " .. target
			addPersonal(c, w, "Seelenstein auf " .. target)
		end
	end
	-- Anregen: Druiden -> Priester
	local priests = list(r.byClass.PRIEST)
	for i, d in ipairs(list(r.byClass.DRUID)) do
		local target = priests[i]
		if target then
			c.lines[#c.lines + 1] = "Anregen: " .. d .. " -> " .. target
			addPersonal(c, d, "Anregen auf " .. target)
		end
	end

	-------------------------------------------------------------------
	-- Bosse
	-------------------------------------------------------------------
	-- Lucifron / Gehennas: Boss + 2 Adds
	for _, key in ipairs({ "lucifron", "gehennas" }) do
		local b = newCtx()
		result[key] = b
		if T[1] then b.lines[#b.lines + 1] = "Boss: " .. T[1]; addPersonal(b, T[1], "Tanke den Boss") end
		for i, icon in ipairs({ 8, 7 }) do
			local tank = T[i + 1]
			if tank then
				b.lines[#b.lines + 1] = string.format("Add %s: %s", ICON[icon], tank)
				addPersonal(b, tank, "Tanke Add " .. ICON[icon] .. " (" .. ICON_NAME[icon] .. ")")
			end
		end
		b.lines[#b.lines + 1] = "Adds zuerst! Entfluchen nach allgemeiner Einteilung."
	end

	-- Magmadar: Einlull-Rotation, Furchtschutz auf MT
	local mg = newCtx()
	result.magmadar = mg
	local hunters = list(r.byClass.HUNTER)
	if #hunters > 0 then
		local parts = {}
		for i, h in ipairs(hunters) do
			parts[#parts + 1] = i .. ". " .. h
			addPersonal(mg, h, string.format("Einlullender Schuss: Position %d von %d", i, #hunters))
		end
		mg.lines[#mg.lines + 1] = "Einlull-Rotation: " .. table.concat(parts, ", ")
	end
	if r.dwarfPriests[1] and T[1] then
		mg.lines[#mg.lines + 1] = "Furchtschutz auf MT " .. T[1] .. ": " .. r.dwarfPriests[1]
		addPersonal(mg, r.dwarfPriests[1], "Furchtschutz auf " .. T[1] .. " erneuern!")
	end
	if T[1] then addPersonal(mg, T[1], "Tanke Magmadar, Furcht beachten") end

	-- Garr: Hexer verbannen, Tanks auf den Rest
	local ga = newCtx()
	result.garr = ga
	local order = RM.Data.GetTemplate("garr").order
	local warlocks = list(r.byClass.WARLOCK)
	if T[1] then ga.lines[#ga.lines + 1] = "Garr: " .. T[1]; addPersonal(ga, T[1], "Tanke Garr") end
	local used = 0
	local banish = {}
	for i, w in ipairs(warlocks) do
		local icon = order[i]
		if not icon then break end
		banish[#banish + 1] = ICON[icon] .. " " .. w
		addPersonal(ga, w, "Verbanne " .. ICON[icon] .. " (" .. ICON_NAME[icon] .. ")")
		used = i
	end
	if #banish > 0 then ga.lines[#ga.lines + 1] = "Verbannen: " .. table.concat(banish, ", ") end
	local tankParts = {}
	local t = 2
	for i = used + 1, #order do
		local tank = T[t]
		if not tank then break end
		tankParts[#tankParts + 1] = ICON[order[i]] .. " " .. tank
		addPersonal(ga, tank, "Tanke Add " .. ICON[order[i]] .. " (" .. ICON_NAME[order[i]] .. ")")
		t = t + 1
	end
	if #tankParts > 0 then ga.lines[#ga.lines + 1] = "Adds tanken: " .. table.concat(tankParts, ", ") end
	ga.lines[#ga.lines + 1] = "Adds einzeln töten, Nahkampf weg bei Explosion."

	-- Shazzrah: Tank-Reihenfolge nach Blinzeln
	local sh = newCtx()
	result.shazzrah = sh
	if #T > 0 then
		sh.lines[#sh.lines + 1] = "Tanks verteilt im Raum, Reihenfolge nach Blinzeln: " .. table.concat(T, " > ")
		for i, tank in ipairs(T) do addPersonal(sh, tank, "Tank Nr. " .. i .. " – nach Blinzeln sofort spotten") end
	end

	-- Sulfuron: Tanks auf Priester, Unterbrecher je Priester
	local su = newCtx()
	result.sulfuron = su
	if T[1] then su.lines[#su.lines + 1] = "Sulfuron: " .. T[1]; addPersonal(su, T[1], "Tanke Sulfuron") end
	local priestIcons = { 8, 7, 6, 5 }
	for i, icon in ipairs(priestIcons) do
		local tank = T[i + 1]
		if tank then
			su.lines[#su.lines + 1] = string.format("Priester %s: %s", ICON[icon], tank)
			addPersonal(su, tank, "Tanke Priester " .. ICON[icon] .. " (" .. ICON_NAME[icon] .. ")")
		end
	end
	local ip = {}
	for i, n in ipairs(r.interrupt) do
		local icon = priestIcons[((i - 1) % 4) + 1]
		ip[icon] = ip[icon] or {}
		table.insert(ip[icon], n)
		addPersonal(su, n, "Unterbrich Priester " .. ICON[icon] .. " (" .. ICON_NAME[icon] .. ")")
	end
	for _, icon in ipairs(priestIcons) do
		if ip[icon] then su.lines[#su.lines + 1] = "Unterbrechen " .. ICON[icon] .. ": " .. table.concat(ip[icon], ", ") end
	end

	-- Golemagg: zwei Tanks im Wechsel, Kernwüter abseits
	local go = newCtx()
	result.golemagg = go
	if T[1] then go.lines[#go.lines + 1] = "Golemagg: " .. T[1] .. (T[2] and (" / Wechsel " .. T[2]) or "") end
	if T[1] then addPersonal(go, T[1], "Tanke Golemagg") end
	if T[2] then addPersonal(go, T[2], "Golemagg übernehmen bei vielen Magmaspritzer-Stapeln") end
	for i, icon in ipairs({ 6, 5 }) do
		local tank = T[i + 2]
		if tank then
			go.lines[#go.lines + 1] = string.format("Kernwüter %s: %s (nicht töten)", ICON[icon], tank)
			addPersonal(go, tank, "Tanke Kernwüter " .. ICON[icon] .. " abseits (nicht töten)")
		end
	end

	-- Majordomus: Heiler 8/7/6/5 (8 zuerst töten, Rest sheepen), Elite 4/3/2/1 tanken, Unterbrecher
	local mj = newCtx()
	result.majordomo = mj
	mj.lines[#mj.lines + 1] = "Tötungsreihenfolge: Heiler " .. ICON[8] .. " " .. ICON[7] .. " " .. ICON[6] .. " " .. ICON[5] .. ", dann Elite"
	local mages = list(r.byClass.MAGE)
	local sheepIcons = { 7, 6, 5 }
	local sheepParts = {}
	for i, mage in ipairs(mages) do
		local icon = sheepIcons[((i - 1) % #sheepIcons) + 1]
		local backup = i > #sheepIcons
		sheepParts[#sheepParts + 1] = ICON[icon] .. " " .. mage .. (backup and " (Ersatz)" or "")
		addPersonal(mj, mage, (backup and "Ersatz-Sheep auf " or "Sheep auf ") .. ICON[icon] .. " (" .. ICON_NAME[icon] .. ")")
	end
	if #sheepParts > 0 then mj.lines[#mj.lines + 1] = "Sheep: " .. table.concat(sheepParts, ", ") end
	local eliteIcons = { 4, 3, 2, 1 }
	local eparts = {}
	for i, icon in ipairs(eliteIcons) do
		local tank = T[i]
		if tank then
			eparts[#eparts + 1] = ICON[icon] .. " " .. tank
			addPersonal(mj, tank, "Tanke Elite " .. ICON[icon] .. " (" .. ICON_NAME[icon] .. ")")
		end
	end
	if #eparts > 0 then mj.lines[#mj.lines + 1] = "Elite tanken: " .. table.concat(eparts, ", ") end
	local kick = {}
	for i, n in ipairs(r.interrupt) do
		if i > 4 then break end
		kick[#kick + 1] = n
		addPersonal(mj, n, "Unterbrich Heiler " .. ICON[8] .. " (Totenkopf)")
	end
	if #kick > 0 then mj.lines[#mj.lines + 1] = "Unterbrechen " .. ICON[8] .. ": " .. table.concat(kick, ", ") end
	mj.lines[#mj.lines + 1] = "Bei Schild/Reflexion SOFORT aufhören!"

	-- Ragnaros: MT, Ersatztank spottet nach dem Rückstoß
	local rg = newCtx()
	result.ragnaros = rg
	if T[1] then rg.lines[#rg.lines + 1] = "MT: " .. T[1]; addPersonal(rg, T[1], "Tanke Ragnaros (Feuerresistenz!)") end
	if T[2] then rg.lines[#rg.lines + 1] = "Ersatztank: " .. T[2]; addPersonal(rg, T[2], "Nach Zorn des Ragnaros sofort spotten") end
	rg.lines[#rg.lines + 1] = "Söhne der Flamme: alle Schaden darauf!"

	-------------------------------------------------------------------
	-- Speichern (auch für den Discord-Bot)
	-------------------------------------------------------------------
	local store = { v = GetServerTime(), by = RM.Me(), title = (RM.db.signup and RM.db.signup.title) or "Raid", ctx = {} }
	for _, cdef in ipairs(A.Contexts) do
		local d = result[cdef.key]
		if d then store.ctx[cdef.key] = { n = cdef.name, lines = d.lines, p = d.p } end
	end
	RM.db.assign = store
	RM.Fire("ASSIGN_CHANGED")
	RM.Print("Einteilung erstellt. Mit 'An alle senden' verschicken – für Discord danach /reload.")
	return store
end

---------------------------------------------------------------------------
-- Verteilen
---------------------------------------------------------------------------
function A.Post(key)
	local store = RM.db.assign
	local ctx = store and store.ctx[key]
	if not ctx then RM.Print("Zuerst die Einteilung erstellen.") return end
	RM.Announce("[RaidMaster] Einteilung " .. ctxName(key) .. ":", true)
	for _, line in ipairs(ctx.lines) do RM.Announce(line, false) end
end

-- Persönlicher Text eines Spielers über alle Kontexte
function A.PersonalTexts(name)
	local out = {}
	local store = RM.db.assign
	if not store then return out end
	for _, cdef in ipairs(A.Contexts) do
		local ctx = store.ctx[cdef.key]
		if ctx and ctx.p[name] then out[cdef.key] = ctx.p[name] end
	end
	return out
end

local function chunks(text, size)
	local parts = {}
	while #text > size do
		local cut = text:sub(1, size):match("^.*() · ") or size
		parts[#parts + 1] = text:sub(1, cut - 1)
		text = text:sub(cut):gsub("^ · ", "")
	end
	if #text > 0 then parts[#parts + 1] = text end
	return parts
end

function A.SendAll()
	local store = RM.db.assign
	if not store then RM.Print("Zuerst die Einteilung erstellen.") return end
	local delay = 0
	local sent = 0
	for _, m in ipairs(RM.RaidMembers()) do
		local texts = A.PersonalTexts(m.name)
		if next(texts) then
			sent = sent + 1
			local v = RM.Comm.versions[m.name]
			if m.name == RM.Me() then
				A.Receive(texts)
			elseif v and v.num >= 10300 then
				RM.Comm.Send("ASG", { c = texts }, "WHISPER", m.name)
			elseif m.online then
				local parts = {}
				for _, cdef in ipairs(A.Contexts) do
					if texts[cdef.key] then parts[#parts + 1] = cdef.name .. ": " .. texts[cdef.key] end
				end
				for _, msg in ipairs(chunks("[RaidMaster] Deine Aufgaben – " .. table.concat(parts, " · "), 240)) do
					local target, text = m.name, msg
					C_Timer.After(delay, function() SendChatMessage(text, "WHISPER", nil, target) end)
					delay = delay + 0.3
				end
			end
		end
	end
	RM.Print(string.format("Einteilung an %d Spieler verschickt. Für Discord-Nachrichten jetzt /reload eingeben.", sent))
end

---------------------------------------------------------------------------
-- Empfang und Anzeige beim Pull
---------------------------------------------------------------------------
function A.Receive(texts)
	RM.db.myAssign = texts
	local general = texts.general
	if general then RM.Print("|cffffcc00Deine Aufgabe (allgemein):|r " .. general) end
	local n = 0
	for key in pairs(texts) do if key ~= "general" then n = n + 1 end end
	if n > 0 then RM.Print(string.format("Du hast Aufgaben bei %d Boss(en) – sie erscheinen beim Pull.", n)) end
	RM.Fire("ASSIGN_CHANGED")
end

RM.Comm.Register("ASG", function(sender, d)
	if type(d.c) ~= "table" then return end
	if RM.IsRaidAuthority(sender) or RM.IsOfficer(sender) then
		A.Receive(d.c)
	end
end)

RM.On("ENCOUNTER_START", function(encounterID)
	local cdef = CTX_BY_ENC[encounterID]
	local mine = RM.db and RM.db.myAssign
	if not cdef or not mine or not mine[cdef.key] then return end
	local text = cdef.name .. ": " .. mine[cdef.key]
	-- Symbole im Bildschirmtext als Grafik zeigen
	local shown = text:gsub("{rt(%d)}", "|TInterface\\TargetingFrame\\UI-RaidTargetingIcon_%1:0|t")
	RaidNotice_AddMessage(RaidWarningFrame, "Deine Aufgabe – " .. shown, ChatTypeInfo["RAID_WARNING"])
	PlaySound(SOUNDKIT and SOUNDKIT.RAID_WARNING or 8959)
	RM.Print("|cffffcc00Deine Aufgabe:|r " .. shown)
end)
