-- RaidMaster - Daten
-- Molten-Core-Bosse, Boss-Infos, Markierungsvorlagen, Klassen-Ausrüstung

local ADDON, RM = ...
local L = RM.L
local Data = {}
RM.Data = Data

---------------------------------------------------------------------------
-- Raids aller WoW-Versionen
-- Jeder Raid ist ein eigener DKP-Topf. Welche Raids es gibt, hängt von der
-- erkannten Spielversion ab (RM.GAME.key): Classic Era/WoW Forever, TBC, Wrath,
-- Cataclysm, Mists of Pandaria, Retail. Die Raid- und Bossdaten selbst stehen in
-- RaidData.lua (Taktiken, Raidchat-Zeilen, Markierungsvorlagen).
--
-- Felder eines Raids: key (Topf), exp (Erweiterung), games (Spielversionen),
--   name (übersetzt), en (englisch), short, ids (Instanz-IDs), ji (Dungeon-Journal-ID),
--   bosses = { { e = {Encounter-IDs}, j = Journal-ID, name/de/en/names, text, post, marker, dkp } }
-- Unbekannte Raids bekommen beim ersten Betreten automatisch einen eigenen Topf.
---------------------------------------------------------------------------
Data.Expansions = {
	{ key = "classic", name = L["Classic"] },
	{ key = "tbc", name = L["The Burning Crusade"] },
	{ key = "wrath", name = L["Wrath of the Lich King"] },
	{ key = "cata", name = L["Cataclysm"] },
	{ key = "mop", name = L["Mists of Pandaria"] },
	{ key = "wod", name = L["Warlords of Draenor"] },
	{ key = "legion", name = L["Legion"] },
	{ key = "bfa", name = L["Battle for Azeroth"] },
	{ key = "sl", name = L["Shadowlands"] },
	{ key = "df", name = L["Dragonflight"] },
	{ key = "tww", name = L["The War Within"] },
	{ key = "midnight", name = L["Midnight"] },
	{ key = "custom", name = L["WoW Forever"] },
}

-- Raids, die in der Auswahl der DKP-Töpfe immer stehen (die "aktuellen" Raids der Spielversion).
-- Alle anderen erscheinen, sobald man sie betritt oder DKP darin vergeben wurden.
Data.HomeRaids = {
	era = { "mc", "ony", "bwl", "zg", "aq20", "aq40", "naxx" },
	forever = { "mc", "ony", "barrow", "hyjal" },
	tbc = { "kara", "gruul", "mag", "ssc", "tk", "hyjal", "bt", "za", "swp" },
	wrath = { "naxx", "os", "eoe", "voa", "uld", "toc", "ony", "icc", "rs" },
	titan = { "naxx", "os", "eoe", "voa", "uld", "toc", "ony", "icc", "rs" },
	cata = { "bh", "bwd", "bot", "tofw", "fl", "ds" },
	mists = { "msv", "hof", "toes", "tot", "soo" },
	retail = { "vs", "dr", "mqd", "va" },
	unknown = { "mc", "ony" },
}

local ALL_RAIDS = {}
Data.AllRaids = ALL_RAIDS

-- Spielversionen als Menge: "era forever tbc" -> { era = true, ... }
local function GameSet(s)
	local set = {}
	for k in tostring(s or ""):gmatch("%S+") do set[k] = true end
	return set
end

-- Raid registrieren (RaidData.lua); Reihenfolge = Reihenfolge in den Auswahlen
function Data.AddRaid(def)
	def.games = type(def.games) == "string" and GameSet(def.games) or def.games or {}
	def.idx = #ALL_RAIDS + 1
	ALL_RAIDS[#ALL_RAIDS + 1] = def
	return def
end

Data.Pools = {}       -- [Topf] = Raid (nur Raids dieser Spielversion)
Data.Bosses = {}      -- [Encounter-ID] = Boss (alle IDs eines Bosses zeigen auf dieselbe Tabelle)
Data.BossOrder = {}   -- Haupt-IDs in Raid-Reihenfolge
Data.RaidList = {}    -- Raids dieser Spielversion in Reihenfolge
Data.PoolOrder = {}

-- Gibt es den Raid in dieser Spielversion?
function Data.Available(def)
	local g = RM.GAME and RM.GAME.key or "unknown"
	if g == "unknown" then return def.exp == "classic" end
	return def.games[g] == true
end

-- Bosse in Cataclysm-Classic und neuer haben für alte Raids teils andere Encounter-IDs
local function PrimaryID(ids)
	if #ids == 1 then return ids[1] end
	local lo, hi = ids[1], ids[1]
	for _, v in ipairs(ids) do
		if v < lo then lo = v end
		if v > hi then hi = v end
	end
	return ((RM.TOC or 0) >= 40000) and hi or lo
end

-- Bossname in der Sprache des Spiels
local function BossName(b)
	if b.names and b.names[RM.LOCALE] then return b.names[RM.LOCALE] end
	if b.j and EJ_GetEncounterInfo then
		local ok, n = pcall(EJ_GetEncounterInfo, b.j)
		if ok and type(n) == "string" and n ~= "" then return n end
	end
	if b.name then return b.name end
	if RM.LOCALE == "deDE" then return b.de or b.en or "?" end
	return b.en or b.de or "?"
end
Data.BossName = BossName

local function RaidMatch(def)
	local m = {}
	for _, s in ipairs(def.match or {}) do m[#m + 1] = s end
	for _, s in ipairs({ def.name, def.en, def.de }) do
		if type(s) == "string" and s ~= "" then m[#m + 1] = s:lower() end
	end
	return m
end

Data.MarkerTemplates = {}

-- Alles für die erkannte Spielversion zusammenstellen
function Data.Build()
	wipe(Data.Pools); wipe(Data.Bosses); wipe(Data.BossOrder); wipe(Data.RaidList); wipe(Data.PoolOrder)
	wipe(Data.MarkerTemplates)
	for _, t in ipairs(Data.BaseTemplates) do Data.MarkerTemplates[#Data.MarkerTemplates + 1] = t end
	for _, def in ipairs(ALL_RAIDS) do
		if Data.Available(def) and not Data.Pools[def.key] then
			Data.Pools[def.key] = def
			Data.RaidList[#Data.RaidList + 1] = def
			if type(def.ids) == "table" and def.ids[1] then
				local set = {}
				for _, id in ipairs(def.ids) do set[id] = true end
				def.ids = set
			end
			def.match = RaidMatch(def)
			def.bossIDs = {}
			local n = #def.bosses
			for i, b in ipairs(def.bosses) do
				b.id = PrimaryID(b.e)
				b.pool = def.key
				b.raid = def
				b.name = BossName(b)
				b.dkp = b.dkp or ((i == n and n > 1) and 20 or (i == n - 1 and n > 4) and 15 or 10)
				if n == 1 then b.dkp = def.soloDKP or 20 end
				for _, e in ipairs(b.e) do Data.Bosses[e] = b end
				Data.BossOrder[#Data.BossOrder + 1] = b.id
				def.bossIDs[#def.bossIDs + 1] = b.id
				if b.text and not Data.BossInfo[b.id] then
					local info = { text = table.concat(b.text, "\n"), post = b.post or {} }
					if b.wichtig then info.text = info.text .. "\n\n" .. b.wichtig end
					for _, e in ipairs(b.e) do Data.BossInfo[e] = info end
				elseif Data.BossInfo[b.id] then
					local info = Data.BossInfo[b.id]
					if b.wichtig and not info.wichtig then
						info.wichtig = true
						info.text = info.text .. "\n\n" .. b.wichtig
					end
					for _, e in ipairs(b.e) do Data.BossInfo[e] = info end
				end
				if b.marker and not b.template then
					b.template = "b" .. b.id
					Data.MarkerTemplates[#Data.MarkerTemplates + 1] = {
						id = b.template, name = b.marker.name or b.name, order = b.marker.order, note = b.marker.note or "", raid = def.key,
					}
				end
			end
		end
	end
	-- Boss-Infos ALLER Raids (auch anderer Spielversionen) für die Raidleiter-Seite
	for _, def in ipairs(ALL_RAIDS) do
		def.view = {}
		def.available = Data.Pools[def.key] == def
		for _, b in ipairs(def.bosses) do
			local id = b.id or PrimaryID(b.e)
			local entry = { id = id, name = b.name or BossName(b), template = b.template, boss = b }
			if def.available then
				entry.info = Data.BossInfo[id]
			elseif b.text then
				entry.info = { text = table.concat(b.text, "\n") .. (b.wichtig and ("\n\n" .. b.wichtig) or ""), post = b.post or {} }
			else
				entry.info = Data.BossInfo[id]
			end
			if b.marker and not entry.template then
				entry.template = "x" .. def.idx .. "_" .. id
				Data.MarkerTemplates[#Data.MarkerTemplates + 1] = {
					id = entry.template, name = b.marker.name or entry.name, order = b.marker.order, note = b.marker.note or "", raid = def.key,
				}
			end
			def.view[#def.view + 1] = entry
		end
	end
	local g = RM.GAME and RM.GAME.key or "unknown"
	for _, key in ipairs(Data.HomeRaids[g] or Data.HomeRaids.unknown) do
		if Data.Pools[key] then Data.PoolOrder[#Data.PoolOrder + 1] = key end
	end
	if not Data.PoolOrder[1] and Data.RaidList[1] then Data.PoolOrder[1] = Data.RaidList[1].key end
end

-- Raid zu einem Topf (auch Raids anderer Versionen, z. B. aus fremden Daten)
function Data.RaidByKey(key)
	if Data.Pools[key] then return Data.Pools[key] end
	for _, def in ipairs(ALL_RAIDS) do if def.key == key then return def end end
end

-- Raids dieser Spielversion zu einer Erweiterung
function Data.RaidsOfExpansion(exp)
	local list = {}
	for _, def in ipairs(Data.RaidList) do if def.exp == exp then list[#list + 1] = def end end
	return list
end

-- Alle bekannten Raids nach Erweiterung (für die Boss-Infos, unabhängig von der Spielversion)
function Data.InfoGroups()
	local groups = {}
	for _, x in ipairs(Data.Expansions) do
		local items = {}
		for _, def in ipairs(ALL_RAIDS) do
			if def.exp == x.key and def.view and def.view[1] then
				items[#items + 1] = { def.idx, def.name .. (def.available and "" or " |cff888888*|r") }
			end
		end
		if items[1] then groups[#groups + 1] = { text = x.name, items = items } end
	end
	return groups
end

function Data.RaidByIndex(idx) return ALL_RAIDS[idx] end

-- Erweiterungen, zu denen es in dieser Spielversion Raids gibt
function Data.AvailableExpansions()
	local list = {}
	for _, x in ipairs(Data.Expansions) do
		if Data.RaidsOfExpansion(x.key)[1] then list[#list + 1] = x end
	end
	return list
end

-- Name eines im Kampf gemeldeten Bosses übernehmen (immer in der Sprache des Spiels)
function Data.LearnBossName(encounterID, name)
	local b = Data.Bosses[encounterID]
	if b and type(name) == "string" and name ~= "" then b.name = name end
end

-- Alle bekannten Bosse eines Topfes: { {id=, name=} }
function Data.BossesForPool(pool, data)
	local list = {}
	local def = Data.Pools[pool]
	for _, id in ipairs(def and def.bossIDs or {}) do
		list[#list + 1] = { id = id, name = Data.Bosses[id].name }
	end
	local learned = {}
	for id, b in pairs((data and data.knownBosses) or {}) do
		if b.p == pool and not Data.Bosses[id] then learned[#learned + 1] = { id = id, name = b.n } end
	end
	table.sort(learned, function(a, b) return a.id < b.id end)
	for _, b in ipairs(learned) do list[#list + 1] = b end
	return list
end

-- Molten Core (Taktiken unten in Data.BossInfo, bereits in alle Sprachen übersetzt)
Data.AddRaid({
	key = "mc", exp = "classic", games = "era forever tbc wrath titan cata mists retail",
	name = L["Molten Core"], en = "Molten Core", de = "Geschmolzener Kern", short = "MC", ids = { 409 }, match = { "molten", "geschmolzen" },
	bosses = {
		{ e = { 663 }, name = L["Lucifron"], template = "lucifron" },
		{ e = { 664 }, name = L["Magmadar"] },
		{ e = { 665 }, name = L["Gehennas"], template = "gehennas" },
		{ e = { 666 }, name = L["Garr"], template = "garr" },
		{ e = { 667 }, name = L["Shazzrah"] },
		{ e = { 668 }, name = L["Baron Geddon"] },
		{ e = { 669 }, name = L["Sulfuronherold"], template = "sulfuron" },
		{ e = { 670 }, name = L["Golemagg der Verbrenner"], template = "golemagg" },
		{ e = { 671 }, name = L["Majordomus Exekutus"], template = "majordomo", dkp = 15 },
		{ e = { 672 }, name = L["Ragnaros"], dkp = 20 },
	},
})

-- Eigene Raids von WoW Forever
-- Ab 9. Dezember 2026: Barrow Deeps (10 Spieler), Hyjalgipfel (20 Spieler, eigene Bosse – nicht der TBC-Raid),
-- Onyxias Hort (40). Die Bosse lernt das Addon beim ersten Kampf (Name und Encounter-ID aus dem Spiel),
-- die Beute füllt die eigene Beute-Datenbank (LootDB.lua).
Data.AddRaid({ key = "barrow", exp = "custom", games = "forever", size = 10, name = L["Barrow Deeps"], en = "Barrow Deeps", short = L["Barrow"], match = { "barrow" }, bosses = {} })
Data.AddRaid({ key = "hyjal", exp = "custom", games = "forever", size = 20, name = L["Hyjalgipfel"], en = "Hyjal Summit", de = "Hyjalgipfel", short = "Hyjal", match = { "hyjal" }, bosses = {} })

---------------------------------------------------------------------------
-- Boss-Infos für den Raidleiter
-- post = kurze Zeilen für den Raidchat (erste Zeile als Raidwarnung)
---------------------------------------------------------------------------
Data.BossInfo = {
	[663] = {
		text = L["Lucifron + 2 Beschützer der Flammenschuppen\n\nFähigkeiten:\n- Fluch des Lucifron: verdoppelt Kosten für Mana, Wut und Energie -> sofort entfluchen\n- Drohende Verdammnis: Magie-Debuff, nach 10 Sek. hoher Schattenschaden -> bannen\n- Schattenschock: Schaden in der Nähe\n- Beschützer: Gedankenkontrolle und Spalten\n\nTaktik:\n- 3 Tanks: Lucifron und je ein Beschützer, Adds vom Boss weg tanken\n- Erst die beiden Beschützer töten, dann Lucifron\n- Gedankenkontrollierte Spieler kurz verwandeln oder festhalten, nicht töten\n- Entflucher und Banner arbeiten durchgehend"],
		post = {
			L["LUCIFRON: Adds zuerst! Flüche sofort entfernen, Magie bannen!"],
			L["Adds weg vom Boss tanken. Gedankenkontrolle beachten."],
		},
	},
	[664] = {
		text = L["Magmadar\n\nFähigkeiten:\n- Panik: Furcht auf den ganzen Raid\n- Raserei: stark erhöhter Schaden auf den Tank\n- Lavabombe: Feuerflächen am Boden\n- Lavaatem: Feuerkegel nach vorne\n\nTaktik:\n- Tank mit Furchtschutz (Zwergenpriester), Horde: Erdbebentotem (Tremor)\n- Krieger nutzen Berserkerwut gegen die Furcht\n- Jäger-Rotation: Bei Raserei sofort Einlullender Schuss – feste Reihenfolge ansagen\n- Boss vom Raid wegdrehen, niemand steht vor ihm\n- Sofort aus Lavabomben herauslaufen\n- Ersatztank in Bereitschaft, falls der Haupttank in Furcht gerät"],
		post = {
			L["MAGMADAR: Jäger -> Einlullender Schuss bei Raserei! Raus aus dem Feuer!"],
			L["Furchtschutz auf die Tanks. Niemand vor den Boss."],
		},
	},
	[665] = {
		text = L["Gehennas + 2 Flammenschuppen\n\nFähigkeiten:\n- Fluch des Gehennas: stark reduzierte erhaltene Heilung -> sofort entfluchen\n- Feuerregen: Feuerflächen -> herauslaufen\n- Schattenblitz: Schaden auf zufällige Ziele\n- Adds: Betäubung und Rüstungsreduktion auf den Tank\n\nTaktik:\n- 3 Tanks, Adds zuerst töten\n- Entflucher haben höchste Priorität – verfluchte Spieler sind kaum heilbar\n- Fernkämpfer verteilt stehen, damit der Feuerregen wenige trifft"],
		post = {
			L["GEHENNAS: Adds zuerst! Fluch sofort entfernen (Heilung reduziert)!"],
			L["Raus aus dem Feuerregen."],
		},
	},
	[666] = {
		text = L["Garr + 8 Feuerschwörer\n\nFähigkeiten:\n- Garr: Antimagischer Impuls (entfernt Buffs), Magmafesseln (verlangsamt)\n- Feuerschwörer: Feuerbrand, beim Tod Eruption (Explosion mit Rückstoß)\n- Feuerschwörer, die zu weit von Garr weg sind, werden wütend\n\nTaktik:\n- Jeder Feuerschwörer bekommt ein Symbol (RaidMaster-Vorlage „Garr“)\n- Hexer verbannen ihre zugewiesenen Adds (Elementare), Krieger tanken den Rest\n- Garr wird separat getankt, nicht zu weit von den Adds\n- Adds einzeln nacheinander töten, dann Garr\n- Nahkämpfer weg, wenn ein Add stirbt (Explosion)\n- Verbannung rechtzeitig erneuern – Hexer achten auf die Laufzeit"],
		post = {
			L["GARR: Hexer verbannen ihre Symbole! Tanks übernehmen die restlichen Adds."],
			L["Nahkampf weg von sterbenden Adds (Explosion). Adds einzeln töten."],
		},
	},
	[667] = {
		text = L["Shazzrah\n\nFähigkeiten:\n- Arkane Explosion: starker Flächenschaden um ihn herum\n- Blinzeln: teleportiert sich und setzt die Bedrohung zurück\n- Fluch des Shazzrah: erhöhter Arkanschaden -> entfluchen\n- Gegenzauber: unterbricht Zauberer in der Nähe\n- Magiedämpfung: Schutz auf dem Boss -> bannen bzw. reinigen\n\nTaktik:\n- Mehrere Tanks im Raum verteilen – nach dem Blinzeln übernimmt der nächste\n- Fernkämpfer und Heiler auf maximale Distanz\n- Nur Nahkämpfer mit guter Heilung am Boss, nach Arkaner Explosion kurz zurück\n- Der Kampf ist kurz: voller Schaden, Flüche weg, Buff vom Boss bannen"],
		post = {
			L["SHAZZRAH: Tanks verteilen (Blinzeln)! Fernkämpfer auf Abstand!"],
			L["Flüche entfernen, Buff vom Boss bannen."],
		},
	},
	[668] = {
		text = L["Baron Geddon\n\nFähigkeiten:\n- Lebende Bombe: Spieler explodiert nach kurzer Zeit und trifft alle in der Nähe\n- Inferno: starker Flächenschaden um den Boss\n- Mana entzünden: verbrennt Mana und verursacht Schaden -> bannen\n- Kurz vor dem Tod: große Explosion\n\nTaktik:\n- Lebende Bombe -> SOFORT aus dem Raid laufen zu einem vorher festgelegten Platz\n- Inferno -> Nahkämpfer raus, danach wieder rein\n- Raid weit verteilt aufstellen\n- Mana entzünden bannen\n- Bei wenig Leben: alle weg vom Boss\n- Kann Bindungen des Windsuchers droppen (legendär)"],
		post = {
			L["GEDDON: Lebende Bombe -> SOFORT aus dem Raid laufen! Inferno -> Nahkampf raus!"],
			L["Mana entzünden bannen. Am Ende Explosion -> weg vom Boss."],
		},
	},
	[669] = {
		text = L["Sulfuronherold + 4 Priester der Flammenschuppen\n\nFähigkeiten:\n- Priester: Dunkle Besserung (Heilung), Schattenwort: Schmerz, Feuerbrand\n- Sulfuron: Inspiration (stärkt die Adds), Hand des Ragnaros (Betäubung und Rückstoß), Flammenspeer, Demoralisierungsruf\n\nTaktik:\n- Jeder Priester bekommt ein Symbol und einen Tank\n- Priester einzeln töten, Heilungen konsequent unterbrechen\n- Sulfuron separat tanken und zuletzt töten\n- Schattenwort: Schmerz bannen"],
		post = {
			L["SULFURON: Priester zuerst und UNTERBRECHEN (Heilung)!"],
			L["Sulfuron separat tanken. Schattenwort: Schmerz bannen."],
		},
	},
	[670] = {
		text = L["Golemagg der Verbrenner + 2 Kernwüter\n\nFähigkeiten:\n- Magmaspritzer: stapelnder Debuff auf dem Tank\n- Pyroschlag: Feuerschaden auf zufällige Spieler\n- Erdbeben bei wenig Leben: Schaden für Nahkämpfer\n- Kernwüter: können nicht sterben, solange Golemagg lebt\n\nTaktik:\n- Die beiden Kernwüter abseits tanken und ignorieren – sie sterben mit Golemagg\n- Alle Schaden auf Golemagg\n- Bei vielen Stapeln Magmaspritzer Tank wechseln\n- Gegen Ende Nahkämpfer mit wenig Leben zurückziehen"],
		post = {
			L["GOLEMAGG: Kernwüter abseits tanken und NICHT töten! Fokus auf Golemagg."],
			L["Tankwechsel bei hohen Magmaspritzer-Stapeln."],
		},
	},
	[671] = {
		text = L["Majordomus Exekutus + 4 Heiler + 4 Elite\n\nErscheint erst, wenn alle 7 Runen gelöscht sind.\n\nFähigkeiten:\n- Magiereflexion: Zauber werden zurückgeworfen -> Zauberer hören auf\n- Schadensschild: Nahkampftreffer schaden dem Angreifer -> Nahkämpfer hören auf\n- Teleport: wirft Spieler in die Feuergrube\n- Heiler: Große Heilung, Schattenblitz · Elite: Feuerschlag, Druckwelle\n\nTaktik:\n- Majordomus wird nicht angegriffen – der Kampf endet, wenn alle 8 Adds tot sind\n- Symbole: zuerst die Heiler, dann die Elite (RaidMaster-Vorlage „Majordomus“)\n- Heiler zuerst, Heilungen unterbrechen; Magier können Heiler verwandeln\n- Bei Schild oder Reflexion sofort aufhören – der Raidleiter sagt es an\n- Teleportierte Spieler schnell aus dem Feuer und gegenheilen\n- Danach: Truhe des Feuerfürsten plündern, später Majordomus ansprechen -> Ragnaros"],
		post = {
			L["MAJORDOMUS: Heiler zuerst und unterbrechen! Bei Schild SOFORT aufhören!"],
			L["Symbole beachten, Elite separat tanken."],
		},
	},
	[672] = {
		text = L["Ragnaros\n\nFähigkeiten:\n- Zorn des Ragnaros: schleudert alle Nahkämpfer weg\n- Lavaschlag: wenn niemand in Nahkampfreichweite ist – sehr gefährlich\n- Elementarfeuer: Feuerschaden über Zeit auf dem Tank\n- Lavaeruption: schleudert Spieler hoch\n- Waffe schmelzen: Haltbarkeit der Nahkampfwaffen sinkt\n- Abtauchen: nach einiger Zeit taucht er ab – Söhne der Flamme erscheinen\n\nTaktik:\n- Tanks mit möglichst viel Feuerresistenz, Ersatztank steht bereit und spottet nach dem Rückstoß\n- Immer jemand in Nahkampfreichweite – sonst Lavaschlag auf den Raid\n- Kleine Nahkampfgruppe, vor dem Zorn kurz heraus\n- Fernkämpfer und Heiler verteilt im Halbkreis\n- Söhne der Flamme: alle Kräfte darauf, schnell töten, Mana-Klassen auf Abstand\n- Feuerschutztränke trinken, Ersatzwaffe für Nahkämpfer mitnehmen"],
		post = {
			L["RAGNAROS: Nahkampf vor dem Rückstoß raus! Immer ein Tank in Reichweite!"],
			L["Bei Abtauchen: Söhne der Flamme schnell töten. Feuerresistenz an!"],
		},
	},
}

---------------------------------------------------------------------------
-- Markierungsvorlagen (Reihenfolge für "Nächstes freies Symbol")
-- 8 Totenkopf, 7 Kreuz, 6 Viereck, 5 Mond, 4 Dreieck, 3 Diamant, 2 Kreis, 1 Stern
---------------------------------------------------------------------------
Data.MarkerNames = { [1] = L["Stern"], [2] = L["Kreis"], [3] = L["Diamant"], [4] = L["Dreieck"], [5] = L["Mond"], [6] = L["Viereck"], [7] = L["Kreuz"], [8] = L["Totenkopf"] }

Data.BaseTemplates = {
	{ id = "standard", name = L["Standard"], order = { 8, 7, 6, 5, 4, 3, 2, 1 }, note = L["Totenkopf, Kreuz, Viereck, Mond, Dreieck, Diamant, Kreis, Stern."] },
	{ id = "lucifron", npcs = { { ids = { 12119 } } }, name = L["Lucifron"], order = { 8, 7 }, note = L["Totenkopf und Kreuz auf die zwei Beschützer."] },
	{ id = "gehennas", npcs = { { ids = { 11661 } } }, name = L["Gehennas"], order = { 8, 7 }, note = L["Totenkopf und Kreuz auf die zwei Adds."] },
	{ id = "garr", npcs = { { ids = { 12099 } } }, name = L["Garr (Verbannen)"], order = { 1, 2, 3, 4, 5, 6, 7, 8 }, note = L["Jedes Add ein Symbol. Hexer verbannen ihr zugewiesenes Symbol (Stern zuerst)."] },
	{ id = "sulfuron", npcs = { { ids = { 11662 } } }, name = L["Sulfuron"], order = { 8, 7, 6, 5 }, note = L["Vier Priester: Totenkopf, Kreuz, Viereck, Mond in Tötungsreihenfolge."] },
	{ id = "golemagg", npcs = { { ids = { 11672 } } }, name = L["Golemagg"], order = { 6, 5 }, note = L["Viereck und Mond auf die Kernwüter (nicht töten)."] },
	{ id = "majordomo", npcs = { { ids = { 11663 }, icons = { 8, 7, 6, 5 } }, { ids = { 11664 }, icons = { 4, 3, 2, 1 } } }, name = L["Majordomus"], order = { 8, 7, 6, 5, 4, 3, 2, 1 }, note = L["Zuerst die 4 Heiler (Totenkopf, Kreuz, Viereck, Mond), dann die 4 Elite (Dreieck, Diamant, Kreis, Stern)."] },
}

function Data.GetTemplate(id)
	for _, t in ipairs(Data.MarkerTemplates) do
		if t.id == id then return t end
	end
	for _, t in ipairs(Data.BaseTemplates) do
		if t.id == id then return t end
	end
	return Data.BaseTemplates[1]
end

-- Vorlagen für einen Raid (Standard + die Vorlagen seiner Bosse)
function Data.TemplatesForRaid(key)
	local list = { Data.BaseTemplates[1] }
	local def = Data.Pools[key]
	if not def then return list end
	local seen = { standard = true }
	for _, b in ipairs(def.bosses) do
		if b.template and not seen[b.template] then
			seen[b.template] = true
			list[#list + 1] = Data.GetTemplate(b.template)
		end
	end
	return list
end

---------------------------------------------------------------------------
-- Legendäre Gegenstände: nie automatisch verteilen, immer Hinweis
---------------------------------------------------------------------------
Data.Legendary = {
	[18563] = true, -- Bindungen des Windsuchers (links)
	[18564] = true, -- Bindungen des Windsuchers (rechts)
	[17204] = true, -- Auge des Sulfuras
}

-- NPC-IDs für die Kernhunde-Hilfe
Data.CoreHounds = {
	[11673] = L["Uralter Kernhund"],
	[11671] = L["Kernhund"],
}

---------------------------------------------------------------------------
-- Welche Klasse kann welche Waffen/Rüstung tragen (Classic)
-- Rüstung (Klasse 4): 0 Sonstiges, 1 Stoff, 2 Leder, 3 Kette, 4 Platte, 6 Schild, 7 Buchband, 8 Götze, 9 Totem
-- Waffen (Klasse 2): 0 Axt 1H, 1 Axt 2H, 2 Bogen, 3 Gewehr, 4 Streitkolben 1H, 5 Streitkolben 2H, 6 Stangenwaffe,
--   7 Schwert 1H, 8 Schwert 2H, 10 Stab, 13 Faustwaffe, 14 Sonstiges, 15 Dolch, 16 Wurfwaffe, 18 Armbrust, 19 Zauberstab
---------------------------------------------------------------------------
local function set(...)
	local t = {}
	for i = 1, select("#", ...) do t[select(i, ...)] = true end
	return t
end

Data.Proficiency = {
	WARRIOR = { armor = set(0, 1, 2, 3, 4, 6), weapon = set(0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 13, 14, 15, 16, 18) },
	PALADIN = { armor = set(0, 1, 2, 3, 4, 6, 7), weapon = set(0, 1, 4, 5, 6, 7, 8, 14) },
	HUNTER = { armor = set(0, 1, 2, 3), weapon = set(0, 1, 2, 3, 6, 7, 8, 10, 13, 14, 15, 16, 18) },
	ROGUE = { armor = set(0, 1, 2), weapon = set(2, 3, 4, 7, 13, 14, 15, 16, 18) },
	PRIEST = { armor = set(0, 1), weapon = set(4, 10, 14, 15, 19) },
	SHAMAN = { armor = set(0, 1, 2, 3, 6, 9), weapon = set(0, 1, 4, 5, 10, 13, 14, 15) },
	MAGE = { armor = set(0, 1), weapon = set(7, 10, 14, 15, 19) },
	WARLOCK = { armor = set(0, 1), weapon = set(7, 10, 14, 15, 19) },
	DRUID = { armor = set(0, 1, 2, 8), weapon = set(4, 5, 10, 13, 14, 15) },
}

-- true, wenn die Klasse das Item ausrüsten kann (oder es keine Ausrüstung ist)
function Data.CanEquip(classFile, link)
	local prof = Data.Proficiency[classFile]
	if not prof or not link then return true end
	local _, _, _, equipLoc, _, classID, subClassID = RM.GetItemInfoInstant(link)
	if not classID then return true end
	if equipLoc == "INVTYPE_CLOAK" then return true end
	if classID == 4 then
		return prof.armor[subClassID] and true or false
	elseif classID == 2 then
		return prof.weapon[subClassID] and true or false
	end
	return true
end

-- Ausrüstungsplatz -> Inventar-Slots (für die Anzeige der getragenen Ausrüstung)
Data.EquipSlots = {
	INVTYPE_HEAD = { 1 }, INVTYPE_NECK = { 2 }, INVTYPE_SHOULDER = { 3 }, INVTYPE_BODY = { 4 },
	INVTYPE_CHEST = { 5 }, INVTYPE_ROBE = { 5 }, INVTYPE_WAIST = { 6 }, INVTYPE_LEGS = { 7 },
	INVTYPE_FEET = { 8 }, INVTYPE_WRIST = { 9 }, INVTYPE_HAND = { 10 }, INVTYPE_FINGER = { 11, 12 },
	INVTYPE_TRINKET = { 13, 14 }, INVTYPE_CLOAK = { 15 }, INVTYPE_WEAPON = { 16, 17 },
	INVTYPE_SHIELD = { 17 }, INVTYPE_2HWEAPON = { 16 }, INVTYPE_WEAPONMAINHAND = { 16 },
	INVTYPE_WEAPONOFFHAND = { 17 }, INVTYPE_HOLDABLE = { 17 }, INVTYPE_RANGED = { 18 },
	INVTYPE_RANGEDRIGHT = { 18 }, INVTYPE_THROWN = { 18 }, INVTYPE_RELIC = { 18 },
}

-- Getragene Ausrüstung für den passenden Slot als Linkliste
function Data.EquippedFor(link)
	local _, _, _, equipLoc = RM.GetItemInfoInstant(link)
	local slots = equipLoc and Data.EquipSlots[equipLoc]
	if not slots then return "" end
	local out = {}
	for _, s in ipairs(slots) do
		local l = GetInventoryItemLink("player", s)
		if l then out[#out + 1] = l end
	end
	return table.concat(out, " ")
end
