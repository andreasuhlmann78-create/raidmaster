-- RaidMaster - Einteilung
-- Erstellt auf Knopfdruck aus den Klassen im Raid: Heilung, Entfluchen, Magie bannen,
-- CC je Boss (Verbannen, Sheep), Unterbrechen, Einlull-Rotation, Furchtschutz, Seelensteine, Anregen.
-- Je Raid eigene Kontexte: Molten Core (alle Bosse), Onyxias Hort, Barrow Deeps und Hyjalgipfel
-- (die Bosse der neuen Raids sind noch nicht bekannt: dort gibt es eine allgemeine Boss-Einteilung).
-- Tanks heißen überall MT (Maintank) und OT1, OT2 ... (Offtanks) in der eingetragenen Reihenfolge.
-- Verteilung: Flüstern (ohne Addon), Addon-Nachricht mit Anzeige beim Pull, Discord (Bot liest nach /reload,
-- jeder Raid hat dort seinen eigenen Einteilungs-Kanal).

local ADDON, RM = ...
local L = RM.L
local A = {}
RM.Assign = A

local ICON = { [1] = "{rt1}", [2] = "{rt2}", [3] = "{rt3}", [4] = "{rt4}", [5] = "{rt5}", [6] = "{rt6}", [7] = "{rt7}", [8] = "{rt8}" }
local ICON_NAME = RM.Data.MarkerNames

-- Kontexte: allgemein + Bosse je Raid (Encounter-ID für die Anzeige beim Pull)
A.Contexts = {
	{ key = "general", name = L["Allgemein"] },
	{ key = "lucifron", name = L["Lucifron"], enc = 663, raid = "mc" },
	{ key = "magmadar", name = L["Magmadar"], enc = 664, raid = "mc" },
	{ key = "gehennas", name = L["Gehennas"], enc = 665, raid = "mc" },
	{ key = "garr", name = L["Garr"], enc = 666, raid = "mc" },
	{ key = "geddon", name = L["Baron Geddon"], enc = 668, raid = "mc" },
	{ key = "shazzrah", name = L["Shazzrah"], enc = 667, raid = "mc" },
	{ key = "sulfuron", name = L["Sulfuronherold"], enc = 669, raid = "mc" },
	{ key = "golemagg", name = L["Golemagg"], enc = 670, raid = "mc" },
	{ key = "majordomo", name = L["Majordomus"], enc = 671, raid = "mc" },
	{ key = "ragnaros", name = L["Ragnaros"], enc = 672, raid = "mc" },
	{ key = "onyxia", name = L["Onyxia"], enc = 1084, raid = "ony" },
	{ key = "barrow_bosses", name = L["Bosse (allgemein)"], raid = "barrow", any = true },
	{ key = "hyjal_bosses", name = L["Bosse (allgemein)"], raid = "hyjal", any = true },
}
A.RAIDS = { "mc", "ony", "barrow", "hyjal" }
local CTX_BY_ENC, CTX_ANY = {}, {}
for _, c in ipairs(A.Contexts) do
	if c.enc then CTX_BY_ENC[c.enc] = c end
	if c.any then CTX_ANY[c.raid] = c end
end

local function ctxName(key)
	for _, c in ipairs(A.Contexts) do if c.key == key then return c.name end end
	return key
end

-- Kontexte eines Raids (allgemein zuerst)
function A.ContextsFor(pool)
	local out = {}
	for _, c in ipairs(A.Contexts) do
		if not c.raid or c.raid == pool then out[#out + 1] = c end
	end
	return out
end

-- Raid der Einteilung: aktuelle Instanz, sonst laufende Sitzung, sonst Molten Core
function A.DefaultPool()
	local inst = RM.DKP and RM.DKP.CurrentInstancePool and RM.DKP.CurrentInstancePool(true)
	local pool = inst or (RM.db and RM.db.session and RM.db.session.pool) or "mc"
	for _, k in ipairs(A.RAIDS) do if k == pool then return pool end end
	return "mc"
end

-- MT, OT1, OT2 ...
local function TL(i) return i == 1 and L["MT"] or (L["OT"] .. (i - 1)) end
A.TankLabel = TL

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
	for name in text:gmatch("[^,]+") do
		name = name:gsub("^%s+", ""):gsub("%s+$", "")
		if name ~= "" then
			name = name:sub(1, 1):upper() .. name:sub(2)
			if RM.IsInMyRaid(name) then list[#list + 1] = name end
		end
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

local function addLine(ctx, text) ctx.lines[#ctx.lines + 1] = text end

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

-- Schamane in der Gruppe des MT (Erdstoß-Totem gegen Furcht), sonst der erste Schamane
local function TremorShaman(r)
	local shamans = list(r.byClass.SHAMAN)
	local mt = r.tanks[1]
	local g = mt and r.groups[mt]
	for _, s in ipairs(shamans) do if g and r.groups[s] == g then return s end end
	return shamans[1]
end

-- Allgemein: Heilung, Entfluchen, Bannen, Furchtschutz, Seelensteine, Anregen (für jeden Raid)
local function BuildGeneral(r, G)
	local c = newCtx()
	local T, H = r.tanks, r.healers
	if #T > 0 then
		local parts = {}
		for i, t in ipairs(T) do parts[#parts + 1] = TL(i) .. " " .. t end
		addLine(c, L["Tanks: "] .. table.concat(parts, " · "))
		for i, t in ipairs(T) do addPersonal(c, t, string.format(L["Du bist %s"], TL(i) == L["MT"] and L["Maintank (MT)"] or (L["Offtank "] .. TL(i)))) end
	end
	if #T > 0 and #H > 0 then
		local tankHealers = math.max(1, math.ceil(#H / 2))
		local mtShare = math.max(1, math.ceil(tankHealers * 0.4))
		local idx = 1
		local perTank = {}
		for _ = 1, mtShare do
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
				addLine(c, string.format(L["Heilung %s %s: %s"], TL(i), tank, table.concat(hs, ", ")))
				for _, h in ipairs(hs) do addPersonal(c, h, string.format(L["Heile %s %s"], TL(i), tank)) end
			end
		end
		local raidHealers = {}
		for i = idx, #H do raidHealers[#raidHealers + 1] = H[i].name end
		local split = splitGroups(raidHealers, G)
		local parts = {}
		for _, h in ipairs(raidHealers) do
			if split[h] then
				parts[#parts + 1] = h .. " G" .. table.concat(split[h], "+")
				addPersonal(c, h, L["Raidheilung Gruppe "] .. table.concat(split[h], ", "))
			end
		end
		if #parts > 0 then addLine(c, L["Raidheilung: "] .. table.concat(parts, ", ")) end
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
			addPersonal(c, n, L["Entfluchen Gruppe "] .. table.concat(dsplit[n], ", "))
		end
	end
	if #dparts > 0 then addLine(c, L["Entfluchen: "] .. table.concat(dparts, ", ")) end
	-- Magie bannen
	local dispel = {}
	for _, n in ipairs(list(r.byClass.PRIEST)) do dispel[#dispel + 1] = n end
	for _, n in ipairs(list(r.byClass.PALADIN)) do dispel[#dispel + 1] = n end
	local bsplit = splitGroups(dispel, G)
	local bparts = {}
	for _, n in ipairs(dispel) do
		if bsplit[n] then
			bparts[#bparts + 1] = n .. " G" .. table.concat(bsplit[n], "+")
			addPersonal(c, n, L["Magie bannen Gruppe "] .. table.concat(bsplit[n], ", "))
		end
	end
	if #bparts > 0 then addLine(c, L["Bannen: "] .. table.concat(bparts, ", ")) end
	-- Furchtschutz (Zwergenpriester) auf die Tanks
	for i, p in ipairs(r.dwarfPriests) do
		local tank = T[i]
		if tank then
			addLine(c, L["Furchtschutz: "] .. p .. " -> " .. TL(i) .. " " .. tank)
			addPersonal(c, p, L["Furchtschutz auf "] .. TL(i) .. " " .. tank)
		end
	end
	-- Seelensteine: Hexer -> Heiler, die wiederbeleben können
	local rezzers = {}
	for _, h in ipairs(H) do if h.class ~= "DRUID" then rezzers[#rezzers + 1] = h.name end end
	for i, w in ipairs(list(r.byClass.WARLOCK)) do
		local target = rezzers[i]
		if target then
			addLine(c, L["Seelenstein: "] .. w .. " -> " .. target)
			addPersonal(c, w, L["Seelenstein auf "] .. target)
		end
	end
	-- Anregen: Druiden -> Priester
	local priests = list(r.byClass.PRIEST)
	for i, d in ipairs(list(r.byClass.DRUID)) do
		local target = priests[i]
		if target then
			addLine(c, L["Anregen: "] .. d .. " -> " .. target)
			addPersonal(c, d, L["Anregen auf "] .. target)
		end
	end
	return c
end

---------------------------------------------------------------------------
-- Molten Core (geprüft mit gängigen MC-Guides: Tanks auf Boss und Adds, Bannen/Entfluchen,
-- Einlull-Rotation, Verbannen, Unterbrechen, Sheep, Tankwechsel)
---------------------------------------------------------------------------
local function BuildMC(r, result)
	local T = r.tanks
	local function tankBoss(ctx, name, extra)
		if T[1] then
			addLine(ctx, string.format(L["%s: MT %s"], name, T[1]))
			addPersonal(ctx, T[1], string.format(L["MT – tanke %s"], name) .. (extra and (", " .. extra) or ""))
		end
	end

	-- Lucifron / Gehennas: Boss + 2 Flamewaker-Adds
	for _, key in ipairs({ "lucifron", "gehennas" }) do
		local b = newCtx()
		result[key] = b
		tankBoss(b, ctxName(key), L["vom Raid weg drehen"])
		for i, icon in ipairs({ 8, 7 }) do
			local tank = T[i + 1]
			if tank then
				addLine(b, string.format(L["Add %s: %s %s"], ICON[icon], TL(i + 1), tank))
				addPersonal(b, tank, string.format(L["%s – tanke Add %s (%s)"], TL(i + 1), ICON[icon], ICON_NAME[icon]))
			end
		end
		addLine(b, L["Adds zuerst, dann der Boss. Entfluchen nach allgemeiner Einteilung (Heiler und Tanks zuerst)."])
		if key == "lucifron" then
			addLine(b, L["Priester: Gedankenkontrolle sofort bannen, danach Drohende Verdammnis (Tanks zuerst)."])
		end
	end

	-- Magmadar: Einlull-Rotation, OT hält Bedrohung, Furcht
	local mg = newCtx()
	result.magmadar = mg
	tankBoss(mg, ctxName("magmadar"), L["vom Raid weg drehen"])
	if T[2] then
		addLine(mg, string.format(L["OT1 %s: hohe Bedrohung halten, übernimmt bei Raserei"], T[2]))
		addPersonal(mg, T[2], L["OT1 – hohe Bedrohung auf Magmadar halten, übernehmen falls der MT stirbt"])
	end
	local hunters = list(r.byClass.HUNTER)
	if RM.Tranq then
		local rot, asked = RM.Tranq.Rotation()
		if asked then hunters = rot end
	end
	if #hunters > 0 then
		local parts = {}
		for i, h in ipairs(hunters) do
			parts[#parts + 1] = i .. ". " .. h
			addPersonal(mg, h, string.format(L["Einlullender Schuss: Position %d von %d"], i, #hunters))
		end
		addLine(mg, L["Einlull-Rotation: "] .. table.concat(parts, ", "))
	end
	if r.dwarfPriests[1] and T[1] then
		addLine(mg, string.format(L["Furchtschutz auf MT %s: %s"], T[1], r.dwarfPriests[1]))
		addPersonal(mg, r.dwarfPriests[1], string.format(L["Furchtschutz auf MT %s erneuern!"], T[1]))
	end
	local tremor = TremorShaman(r)
	if tremor then
		addLine(mg, L["Erdstoß-Totem: "] .. tremor)
		addPersonal(mg, tremor, L["Erdstoß-Totem gegen Panik (Furcht) stellen"])
	end
	addLine(mg, L["Fernkampf und Heiler auf maximale Reichweite, Nahkampf hinter den Boss, raus aus dem Feuer."])

	-- Garr: Hexer verbannen, Tanks auf den Rest
	local ga = newCtx()
	result.garr = ga
	local order = RM.Data.GetTemplate("garr").order
	local warlocks = list(r.byClass.WARLOCK)
	tankBoss(ga, ctxName("garr"))
	local used = 0
	local banish = {}
	for i, w in ipairs(warlocks) do
		local icon = order[i]
		if not icon then break end
		banish[#banish + 1] = ICON[icon] .. " " .. w
		addPersonal(ga, w, L["Verbanne "] .. ICON[icon] .. " (" .. ICON_NAME[icon] .. ")")
		used = i
	end
	if #banish > 0 then addLine(ga, L["Verbannen: "] .. table.concat(banish, ", ")) end
	local tankParts = {}
	local t = 2
	for i = used + 1, #order do
		local tank = T[t]
		if not tank then break end
		tankParts[#tankParts + 1] = ICON[order[i]] .. " " .. TL(t) .. " " .. tank
		addPersonal(ga, tank, string.format(L["%s – tanke Add %s (%s)"], TL(t), ICON[order[i]], ICON_NAME[order[i]]))
		t = t + 1
	end
	if #tankParts > 0 then addLine(ga, L["Adds tanken: "] .. table.concat(tankParts, ", ")) end
	addLine(ga, L["Ablauf nach Ansage. Feuergeschworene einzeln und mit Abstand töten – Nahkampf weg bei der Explosion."])

	-- Baron Geddon: MT, Lebende Bombe raus, Mana entzünden bannen
	local gd = newCtx()
	result.geddon = gd
	tankBoss(gd, ctxName("geddon"), L["bei Inferno weglaufen"])
	addLine(gd, L["Lebende Bombe: sofort raus aus dem Raid, erst nach der Explosion zurück."])
	addLine(gd, L["Inferno: Nahkampf und MT laufen weg."])
	local pr = list(r.byClass.PRIEST)
	if #pr > 0 then
		addLine(gd, L["Mana entzünden bannen (Heiler zuerst): "] .. table.concat(pr, ", "))
		for _, p in ipairs(pr) do addPersonal(gd, p, L["Mana entzünden bannen, Lebende Bombe mit Schild schützen"]) end
	end
	addLine(gd, L["Fernkampf und Heiler zusammen in einer Ecke auf maximaler Reichweite."])

	-- Shazzrah: MT in der Mitte, OTs verteilt (Blinzeln), Entfluchen, Magie dämpfen
	local sh = newCtx()
	result.shazzrah = sh
	if #T > 0 then
		local parts = {}
		for i, tank in ipairs(T) do parts[#parts + 1] = TL(i) .. " " .. tank end
		addLine(sh, L["MT in der Mitte, OTs im Bogen verteilt – nach Blinzeln übernimmt der nächste: "] .. table.concat(parts, " > "))
		for i, tank in ipairs(T) do
			addPersonal(sh, tank, i == 1 and L["MT – tanke Shazzrah in der Mitte, vom Raid weg drehen"]
				or string.format(L["%s – nach Blinzeln sofort spotten"], TL(i)))
		end
	end
	addLine(sh, L["Entfluchen: Shazzrahs Fluch (Tanks zuerst)."])
	local purge = {}
	for _, n in ipairs(list(r.byClass.PRIEST)) do purge[#purge + 1] = n end
	for _, n in ipairs(list(r.byClass.SHAMAN)) do purge[#purge + 1] = n end
	if #purge > 0 then
		addLine(sh, L["Magie dämpfen auf Shazzrah bannen/reinigen: "] .. table.concat(purge, ", "))
		for _, n in ipairs(purge) do addPersonal(sh, n, L["Magie dämpfen auf Shazzrah entfernen"]) end
	end
	addLine(sh, L["Nach Blinzeln: Schaden kurz stoppen, bis der neue Tank ihn hat."])

	-- Sulfuron: Tanks auf die Priester, Unterbrecher je Priester, Bannen
	local su = newCtx()
	result.sulfuron = su
	tankBoss(su, ctxName("sulfuron"))
	local priestIcons = { 8, 7, 6, 5 }
	for i, icon in ipairs(priestIcons) do
		local tank = T[i + 1]
		if tank then
			addLine(su, string.format(L["Priester %s: %s %s"], ICON[icon], TL(i + 1), tank))
			addPersonal(su, tank, string.format(L["%s – tanke Priester %s (%s)"], TL(i + 1), ICON[icon], ICON_NAME[icon]))
		end
	end
	local ip = {}
	for i, n in ipairs(r.interrupt) do
		local icon = priestIcons[((i - 1) % 4) + 1]
		ip[icon] = ip[icon] or {}
		table.insert(ip[icon], n)
		addPersonal(su, n, L["Unterbrich Dunkle Besserung bei Priester "] .. ICON[icon] .. " (" .. ICON_NAME[icon] .. ")")
	end
	for _, icon in ipairs(priestIcons) do
		if ip[icon] then addLine(su, L["Unterbrechen "] .. ICON[icon] .. ": " .. table.concat(ip[icon], ", ")) end
	end
	addLine(su, L["Priester zuerst. Bannen: Schattenwort: Schmerz und Feuerbrand."])

	-- Golemagg: MT, OT1 für den Tankwechsel, OT2/OT3 auf die Kernwüter
	local go = newCtx()
	result.golemagg = go
	tankBoss(go, ctxName("golemagg"))
	if T[2] then
		addLine(go, string.format(L["Tankwechsel bei vielen Magmaspritzern: OT1 %s"], T[2]))
		addPersonal(go, T[2], L["OT1 – Golemagg bei vielen Magmaspritzer-Stapeln übernehmen"])
	end
	for i, icon in ipairs({ 6, 5 }) do
		local tank = T[i + 2]
		if tank then
			addLine(go, string.format(L["Kernwüter %s: %s %s (nicht töten)"], ICON[icon], TL(i + 2), tank))
			addPersonal(go, tank, string.format(L["%s – tanke Kernwüter %s abseits (nicht töten)"], TL(i + 2), ICON[icon]))
		end
	end
	addLine(go, L["Alles auf Golemagg, die Hunde ignorieren. Bei 10 % Erdbeben: Heiler bereit."])

	-- Majordomus: Heiler 8/7/6/5 (8 zuerst töten, Rest sheepen), Elite 4/3/2/1 tanken, Unterbrecher
	local mj = newCtx()
	result.majordomo = mj
	addLine(mj, L["Tötungsreihenfolge: Heiler "] .. ICON[8] .. " " .. ICON[7] .. " " .. ICON[6] .. " " .. ICON[5] .. L[", dann Elite"])
	local mages = list(r.byClass.MAGE)
	local sheepIcons = { 7, 6, 5 }
	local sheepParts = {}
	for i, mage in ipairs(mages) do
		local icon = sheepIcons[((i - 1) % #sheepIcons) + 1]
		local backup = i > #sheepIcons
		sheepParts[#sheepParts + 1] = ICON[icon] .. " " .. mage .. (backup and L[" (Ersatz)"] or "")
		addPersonal(mj, mage, (backup and L["Ersatz-Sheep auf "] or L["Sheep auf "]) .. ICON[icon] .. " (" .. ICON_NAME[icon] .. ")")
	end
	if #sheepParts > 0 then addLine(mj, L["Sheep: "] .. table.concat(sheepParts, ", ")) end
	local eliteIcons = { 4, 3, 2, 1 }
	local eparts = {}
	for i, icon in ipairs(eliteIcons) do
		local tank = T[i]
		if tank then
			eparts[#eparts + 1] = ICON[icon] .. " " .. TL(i) .. " " .. tank
			addPersonal(mj, tank, string.format(L["%s – tanke Elite %s (%s)"], TL(i), ICON[icon], ICON_NAME[icon]))
		end
	end
	if #eparts > 0 then addLine(mj, L["Elite tanken: "] .. table.concat(eparts, ", ")) end
	local kick = {}
	for i, n in ipairs(r.interrupt) do
		if i > 4 then break end
		kick[#kick + 1] = n
		addPersonal(mj, n, L["Unterbrich Schattenblitz und Feuerball, zuerst Heiler "] .. ICON[8])
	end
	if #kick > 0 then addLine(mj, L["Unterbrechen (Schattenblitz/Feuerball): "] .. table.concat(kick, ", ")) end
	addLine(mj, L["Priester: Schattenschutz auf den Raid. Bei Schild bzw. Magiereflexion SOFORT aufhören!"])

	-- Ragnaros: MT, OT1 übernimmt nach dem Rückstoß
	local rg = newCtx()
	result.ragnaros = rg
	tankBoss(rg, ctxName("ragnaros"), L["Feuerresistenz!"])
	if T[2] then
		addLine(rg, string.format(L["OT1 %s: übernimmt nach Zorn des Ragnaros"], T[2]))
		addPersonal(rg, T[2], L["OT1 – nach Zorn des Ragnaros sofort übernehmen (Feuerresistenz!)"])
	end
	addLine(rg, L["Nahkampf bei Zorn des Ragnaros raus. Fernkampf verteilt (Lavaeruption)."])
	addLine(rg, L["Söhne der Flamme: alle Schaden darauf, Manabenutzer Abstand halten!"])
end

---------------------------------------------------------------------------
-- Onyxias Hort
---------------------------------------------------------------------------
local function BuildOnyxia(r, result)
	local T = r.tanks
	local o = newCtx()
	result.onyxia = o
	if T[1] then
		addLine(o, string.format(L["Phase 1: MT %s tankt Onyxia, Kopf zur Wand, Raid an den Seiten – nie vor oder hinter ihr."], T[1]))
		addPersonal(o, T[1], L["MT – Phase 1 und 3: Onyxia tanken, Kopf zur Wand"])
	end
	addLine(o, L["Phase 1: Nahkampf an der Flanke (Feueratem vorne, Schwanzhieb hinten), Fernkampf und Heiler auf Abstand."])
	local sides = { L["linke Seite"], L["rechte Seite"], L["Eingang"] }
	local wparts = {}
	for i = 2, math.min(#T, 4) do
		local side = sides[i - 1]
		wparts[#wparts + 1] = TL(i) .. " " .. T[i] .. " (" .. side .. ")"
		addPersonal(o, T[i], string.format(L["%s – Phase 2: Welpen sammeln (%s)"], TL(i), side))
	end
	if #wparts > 0 then addLine(o, L["Phase 2 Welpen: "] .. table.concat(wparts, ", ")) end
	local aoe = list(r.byClass.MAGE)
	if #aoe > 0 then
		addLine(o, L["Phase 2 Welpen mit Flächenschaden: "] .. table.concat(aoe, ", "))
		for _, m in ipairs(aoe) do addPersonal(o, m, L["Phase 2: Welpen mit Flächenschaden (Arkane Explosion) bei den OTs wegputzen"]) end
	end
	addLine(o, L["Phase 2 (ab 65 %): Fernkampf auf Onyxia, verteilt stehen (Feuerball), bei Tiefem Atem aus der Flugbahn laufen."])
	if T[1] then addLine(o, string.format(L["Phase 3 (ab 40 %%): MT %s übernimmt sofort, Furcht beachten."], T[1])) end
	if r.dwarfPriests[1] and T[1] then
		addLine(o, string.format(L["Furchtschutz auf MT %s: %s"], T[1], r.dwarfPriests[1]))
		addPersonal(o, r.dwarfPriests[1], string.format(L["Furchtschutz auf MT %s in Phase 3"], T[1]))
	end
	local tremor = TremorShaman(r)
	if tremor then
		addLine(o, L["Erdstoß-Totem: "] .. tremor)
		addPersonal(o, tremor, L["Erdstoß-Totem in Phase 3 (Furcht)"])
	end
	addLine(o, L["Nicht in die Lavaspalten treten, Eier in Phase 3 nicht aufwecken."])
end

---------------------------------------------------------------------------
-- Neue Raids (Barrow Deeps 10, Hyjalgipfel 20): die Bosse sind noch nicht bekannt.
-- Allgemeine Boss-Einteilung: MT/OTs, Unterbrecher-Reihenfolge, wer was kontrollieren kann.
---------------------------------------------------------------------------
local function BuildGeneric(r, result, key)
	local T = r.tanks
	local b = newCtx()
	result[key] = b
	if #T > 0 then
		local parts = {}
		for i, tank in ipairs(T) do parts[#parts + 1] = TL(i) .. " " .. tank end
		addLine(b, L["Tanks: "] .. table.concat(parts, " · ") .. L[" – MT auf den Boss, OTs auf Adds und für den Tankwechsel."])
		addPersonal(b, T[1], L["MT – zieh und tanke den Boss"])
		for i = 2, #T do addPersonal(b, T[i], string.format(L["%s – Adds übernehmen, bereit für den Tankwechsel"], TL(i))) end
	end
	if #r.interrupt > 0 then
		addLine(b, L["Unterbrechen der Reihe nach: "] .. table.concat(r.interrupt, " > "))
		for i, n in ipairs(r.interrupt) do addPersonal(b, n, string.format(L["Unterbrechen: Platz %d"], i)) end
	end
	local cc = {}
	local function add(class, what)
		for _, n in ipairs(list(r.byClass[class])) do
			cc[#cc + 1] = n .. " (" .. what .. ")"
			addPersonal(b, n, string.format(L["Kontrolle bei Adds: %s"], what))
		end
	end
	add("MAGE", L["Sheep"]); add("WARLOCK", L["Verbannen/Furcht"]); add("HUNTER", L["Eiskältefalle"]); add("PRIEST", L["Fesseln (Untote)"])
	if #cc > 0 then addLine(b, L["Kontrolle (CC), falls Adds kommen: "] .. table.concat(cc, ", ")) end
	addLine(b, L["Die Taktik je Boss sagt die Raidleitung an – RaidMaster lernt die Bosse beim ersten Kampf."])
end

function A.Build(pool)
	if not RM.InRaid() then RM.Print(L["Du bist in keinem Schlachtzug."]) return end
	pool = pool or A.selectedPool or A.DefaultPool()
	local r = A.Analyze()
	local G = groupCount()
	local result = { general = BuildGeneral(r, G) }
	if pool == "mc" then BuildMC(r, result)
	elseif pool == "ony" then BuildOnyxia(r, result)
	elseif CTX_ANY[pool] then BuildGeneric(r, result, CTX_ANY[pool].key) end

	-- Speichern (auch für den Discord-Bot: jeder Raid hat dort seinen eigenen Einteilungs-Kanal)
	local store = { v = GetServerTime(), by = RM.Me(), pool = pool, raid = RM.DKP and RM.DKP.PoolName and RM.DKP.PoolName(pool) or pool,
		title = (RM.db.signup and RM.db.signup.title) or L["Raid"], ctx = {} }
	for _, cdef in ipairs(A.ContextsFor(pool)) do
		local d = result[cdef.key]
		if d then store.ctx[cdef.key] = { n = cdef.name, lines = d.lines, p = d.p } end
	end
	RM.db.assign = store
	RM.Fire("ASSIGN_CHANGED")
	RM.Print(L["Einteilung erstellt. Mit 'An alle senden' verschicken – für Discord danach /reload."])
	return store
end

---------------------------------------------------------------------------
-- Verteilen
---------------------------------------------------------------------------
function A.Post(key)
	local store = RM.db.assign
	local ctx = store and store.ctx[key]
	if not ctx then RM.Print(L["Zuerst die Einteilung erstellen."]) return end
	RM.Announce(L["[RaidMaster] Einteilung "] .. ctxName(key) .. ":", true)
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
	if not store then RM.Print(L["Zuerst die Einteilung erstellen."]) return end
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
				for _, msg in ipairs(chunks(L["[RaidMaster] Deine Aufgaben – "] .. table.concat(parts, " · "), 240)) do
					local target, text = m.name, msg
					C_Timer.After(delay, function() SendChatMessage(text, "WHISPER", nil, target) end)
					delay = delay + 0.3
				end
			end
		end
	end
	RM.Print(string.format(L["Einteilung an %d Spieler verschickt. Für Discord-Nachrichten jetzt /reload eingeben."], sent))
end

---------------------------------------------------------------------------
-- Empfang und Anzeige beim Pull
---------------------------------------------------------------------------
function A.Receive(texts)
	RM.db.myAssign = texts
	local general = texts.general
	if general then RM.Print(L["|cffffcc00Deine Aufgabe (allgemein):|r "] .. general) end
	local n = 0
	for key in pairs(texts) do if key ~= "general" then n = n + 1 end end
	if n > 0 then RM.Print(string.format(L["Du hast Aufgaben bei %d Boss(en) – sie erscheinen beim Pull."], n)) end
	RM.Fire("ASSIGN_CHANGED")
end

RM.Comm.Register("ASG", function(sender, d)
	if type(d.c) ~= "table" then return end
	if RM.IsRaidAuthority(sender) or RM.IsOfficer(sender) then
		A.Receive(d.c)
	end
end)

-- Kontext zu einem Bosskampf: bekannter Boss, sonst die allgemeine Boss-Einteilung des Raids
function A.ContextForEncounter(encounterID)
	local cdef = CTX_BY_ENC[encounterID]
	if cdef then return cdef end
	local pool = RM.DKP and RM.DKP.CurrentInstancePool and RM.DKP.CurrentInstancePool(true)
	return pool and CTX_ANY[pool] or nil
end

RM.On("ENCOUNTER_START", function(encounterID)
	local cdef = A.ContextForEncounter(encounterID)
	local mine = RM.db and RM.db.myAssign
	if not cdef or not mine or not mine[cdef.key] then return end
	local text = cdef.name .. ": " .. mine[cdef.key]
	-- Symbole im Bildschirmtext als Grafik zeigen
	local shown = text:gsub("{rt(%d)}", "|TInterface\\TargetingFrame\\UI-RaidTargetingIcon_%1:0|t")
	RaidNotice_AddMessage(RaidWarningFrame, L["Deine Aufgabe – "] .. shown, ChatTypeInfo["RAID_WARNING"])
	PlaySound(SOUNDKIT and SOUNDKIT.RAID_WARNING or 8959)
	RM.Print(L["|cffffcc00Deine Aufgabe:|r "] .. shown)
end)
