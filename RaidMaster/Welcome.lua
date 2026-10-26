-- RaidMaster - Begrüßung beim Raidstart
-- Bei "Raid starten" begrüßt RaidMaster den Raid im Raidchat. Der Text passt zum Raid: der Name kommt aus der
-- Raidzone, in der ihr steht (sonst aus dem DKP-Topf), dazu ein Satz passend zum Raid (Molten Core, Onyxia,
-- Barrow Deeps, Hyjal ...). Gäste (nicht in der Gilde) und Spieler von der Ersatzbank werden mit Namen begrüßt.
-- Ein-/ausschalten: Seite Raid ("Begrüßung beim Raidstart").

local ADDON, RM = ...
local L = RM.L
local W = {}
RM.Welcome = W

W.MAX_NAMES = 8           -- mehr Gäste: nur die Anzahl nennen

-- je Raid ein paar Sätze (einer wird zufällig gewählt)
W.FLAVOR = {
	mc = { L["Ragnaros wartet schon – lasst uns das Feuer löschen!"], L["Heiß wird's: Feuerwiderstand an, Kopf kühl, Loot rein!"],
		L["Die Kernhunde bellen schon – auf geht's in die Glut!"] },
	ony = { L["Onyxia hat Hunger – wir bringen das Abendessen: sie selbst!"], L["Tiefe Atemzüge? Nicht bei Onyxia – raus aus dem Feuer und rein in den Kampf!"] },
	barrow = { L["Die Tiefen sind dunkel und voller Spinnen – bleibt zusammen!"], L["Ab in die Barrow Deeps – Fackeln hoch und Augen auf!"] },
	hyjal = { L["Der Weltenbaum ruft – verteidigen wir den Hyjalgipfel!"], L["Hyjal braucht uns – zeigt den Wäldern, wer hier aufräumt!"] },
	bwl = { L["Nefarian lädt zur Audienz – wir kommen pünktlich!"], L["Pechschwingenhort: Drachen, Unterdrücker und ganz viel Beute!"] },
	zg = { L["Zul'Gurub ruft – Hakkar bekommt heute Besuch!"] },
	aq20 = { L["Ab in den Sand – Ossirian wartet nicht ewig!"] },
	aq40 = { L["Der Tempel öffnet sich – C'Thun schaut schon zu!"] },
	naxx = { L["Naxxramas schwebt über uns – Kel'Thuzad, wir kommen!"] },
	default = { L["Viel Erfolg, saubere Kills und gute Beute!"], L["Konzentration, Spaß und dicke Beute – los geht's!"] },
}

local function Pick(list)
	return list[math.random(#list)]
end

-- Name des Raids: Raidzone, in der man steht (Sprache des Spiels), sonst der DKP-Topf
function W.RaidName(pool)
	if GetInstanceInfo then
		local name, kind = GetInstanceInfo()
		if kind == "raid" and name and name ~= "" then return name end
	end
	return RM.DKP.PoolName(pool or RM.db.session.pool or RM.db.config.activePool or "mc")
end

local function InGuild(name)
	if RM.Test and RM.Test.active and RM.Test.IsFake and RM.Test.IsFake(name) then return true end
	return RM.GuildRank and RM.GuildRank(name) ~= nil
end

local function FromBench(name)
	if RM.db.config.standby and RM.db.config.standby[name] then return true end
	local su = RM.db.signup
	if su then
		if su.bench and su.bench[name] then return true end
		for _, e in ipairs(su.list or {}) do
			if e.name == name then return e.status == "ersatz" end
		end
	end
	return false
end

-- Begrüßung: Liste von Zeilen für den Raidchat
-- extra (optional): zusätzliche Spieler { name = ..., bench = true/false } – z. B. für die Vorschau im Testmodus
function W.Lines(pool, extra)
	pool = pool or RM.db.session.pool or "mc"
	local raidName = W.RaidName(pool)
	local lines = {}
	lines[1] = string.format(L["[RaidMaster] Herzlich willkommen zu unserem Raid in %s! %s"], raidName, Pick(W.FLAVOR[pool] or W.FLAVOR.default))
	local guests, bench = {}, {}
	for _, m in ipairs(RM.RaidMembers()) do
		if m.name ~= RM.Me() then
			if FromBench(m.name) then
				bench[#bench + 1] = m.name
			elseif not InGuild(m.name) then
				guests[#guests + 1] = m.name
			end
		end
	end
	for _, x in ipairs(extra or {}) do
		if x.bench or FromBench(x.name) then bench[#bench + 1] = x.name else guests[#guests + 1] = x.name end
	end
	table.sort(guests); table.sort(bench)
	if #guests > 0 then
		if #guests <= W.MAX_NAMES then
			lines[#lines + 1] = string.format(L["Ein besonderes Hallo an unsere Gäste %s – schön, dass ihr heute dabei seid!"], table.concat(guests, ", "))
		else
			lines[#lines + 1] = string.format(L["Ein besonderes Hallo an unsere %d Gäste – schön, dass ihr heute dabei seid!"], #guests)
		end
	end
	if #bench > 0 then
		local names = #bench <= W.MAX_NAMES and table.concat(bench, ", ") or string.format(L["%d Spieler"], #bench)
		lines[#lines + 1] = string.format(L["Danke an %s von der Ersatzbank, dass ihr eingesprungen seid!"], names)
	end
	if #guests > 0 then
		lines[#lines + 1] = string.format(L["Gäste: Fragen zum Ablauf? Einfach im Raidchat melden. Euren DKP-Stand: /w %s !dkp"], RM.Me())
	end
	return lines
end

function W.Send(pool)
	if not RM.db or RM.db.config.welcome == false or not RM.InRaid() then return end
	for i, line in ipairs(W.Lines(pool)) do
		if #line > 250 then line = line:sub(1, 247) .. "..." end
		C_Timer.After(1 + (i - 1) * 0.4, function() RM.RaidChat(line, "RAID") end)
	end
end
