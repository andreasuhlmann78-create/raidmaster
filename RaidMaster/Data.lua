-- RaidMaster - Daten
-- Molten-Core-Bosse, Boss-Infos, Markierungsvorlagen, Klassen-Ausrüstung

local ADDON, RM = ...
local L = RM.L
local Data = {}
RM.Data = Data

---------------------------------------------------------------------------
-- DKP-Töpfe: jeder Raid sammelt und zahlt eigene DKP
-- ids = Instanz-IDs (GetInstanceInfo), match = Teil des Instanznamens (klein geschrieben)
-- Unbekannte Raids bekommen beim ersten Betreten automatisch einen eigenen Topf.
---------------------------------------------------------------------------
Data.PoolOrder = { "mc", "ony", "barrow", "hyjal" }

Data.Pools = {
	mc = { name = L["Molten Core"], short = "MC", ids = { [409] = true }, match = { "molten", "geschmolzen" } },
	ony = { name = L["Onyxias Hort"], short = L["Ony"], ids = { [249] = true }, match = { "onyxia" } },
	barrow = { name = L["Barrow Deeps"], short = L["Barrow"], match = { "barrow" } },
	hyjal = { name = L["Hyjalgipfel"], short = L["Hyjal"], match = { "hyjal" } },
}

---------------------------------------------------------------------------
-- Bekannte Bosse: Encounter-IDs (ENCOUNTER_END), Standard-DKP und Topf
-- Bosse der neuen Raids werden beim ersten Kill automatisch erkannt.
---------------------------------------------------------------------------
Data.BossOrder = { 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 1084 }

Data.Bosses = {
	[663] = { name = L["Lucifron"], dkp = 10, pool = "mc" },
	[664] = { name = L["Magmadar"], dkp = 10, pool = "mc" },
	[665] = { name = L["Gehennas"], dkp = 10, pool = "mc" },
	[666] = { name = L["Garr"], dkp = 10, pool = "mc" },
	[667] = { name = L["Shazzrah"], dkp = 10, pool = "mc" },
	[668] = { name = L["Baron Geddon"], dkp = 10, pool = "mc" },
	[669] = { name = L["Sulfuronherold"], dkp = 10, pool = "mc" },
	[670] = { name = L["Golemagg der Verbrenner"], dkp = 10, pool = "mc" },
	[671] = { name = L["Majordomus Exekutus"], dkp = 15, pool = "mc" },
	[672] = { name = L["Ragnaros"], dkp = 20, pool = "mc" },
	[1084] = { name = L["Onyxia"], dkp = 20, pool = "ony" },
}

-- Molten-Core-Bosse für die Boss-Infos des Raidleiters
Data.InfoBossOrder = { 663, 664, 665, 666, 667, 668, 669, 670, 671, 672 }

-- Alle bekannten Bosse eines Topfes: { {id=, name=} }
function Data.BossesForPool(pool, data)
	local list = {}
	for _, id in ipairs(Data.BossOrder) do
		if Data.Bosses[id].pool == pool then list[#list + 1] = { id = id, name = Data.Bosses[id].name } end
	end
	local learned = {}
	for id, b in pairs((data and data.knownBosses) or {}) do
		if b.p == pool and not Data.Bosses[id] then learned[#learned + 1] = { id = id, name = b.n } end
	end
	table.sort(learned, function(a, b) return a.id < b.id end)
	for _, b in ipairs(learned) do list[#list + 1] = b end
	return list
end

---------------------------------------------------------------------------
-- Boss-Infos für den Raidleiter
-- post = kurze Zeilen für den Raidchat (erste Zeile als Raidwarnung)
---------------------------------------------------------------------------
Data.BossInfo = {
	[663] = {
		text = L["Lucifron + 2 Beschützer der Flammenschuppen\n\n"]
			.. L["- Fluch des Lucifron: verdoppelt Mana-/Wut-/Energiekosten -> sofort entfluchen (Magier, Druiden).\n"]
			.. L["- Drohende Verdammnis: Magie-Debuff, nach 10 Sek. hoher Schattenschaden -> bannen (Priester, Paladine).\n"]
			.. L["- Schattenschock: Schattenschaden in der Nähe.\n"]
			.. L["- Beschützer: Gedankenkontrolle und Spalten -> Adds zuerst töten, gedankenkontrollierte Spieler kurz kontrollieren.\n\n"]
			.. L["Taktik: Adds von Lucifron weg tanken, Adds zuerst, Decurser und Banner fest einteilen."],
		post = {
			L["LUCIFRON: Adds zuerst! Flüche sofort entfernen, Magie bannen!"],
			L["Adds weg vom Boss tanken. Gedankenkontrolle beachten."],
		},
	},
	[664] = {
		text = L["Magmadar\n\n"]
			.. L["- Panik: Massenfurcht für den ganzen Raid -> Furchtschutz auf Tanks, Tremor-Totem (Horde), Berserkerwut.\n"]
			.. L["- Raserei: stark erhöhter Schaden -> Jäger nutzen Einlullenden Schuss.\n"]
			.. L["- Lavabombe: Feuerflächen am Boden -> sofort heraus laufen.\n"]
			.. L["- Lavaodem: frontaler Feuerschaden -> Boss vom Raid wegdrehen.\n\n"]
			.. L["Taktik: Tank mit Furchtschutz, Jäger-Rotation für Einlullenden Schuss, alle seitlich oder hinter dem Boss."],
		post = {
			L["MAGMADAR: Jäger -> Einlullender Schuss bei Raserei! Raus aus dem Feuer!"],
			L["Furchtschutz auf die Tanks. Niemand vor den Boss."],
		},
	},
	[665] = {
		text = L["Gehennas + 2 Flammenschuppen-Adds\n\n"]
			.. L["- Fluch des Gehennas: stark reduzierte erhaltene Heilung -> sofort entfluchen.\n"]
			.. L["- Feuerregen: Feuerflächen -> heraus laufen.\n"]
			.. L["- Schattenblitz: Schaden auf zufällige Ziele.\n\n"]
			.. L["Taktik: Adds zuerst töten, Decurser einteilen, Heiler achten auf verfluchte Ziele."],
		post = {
			L["GEHENNAS: Adds zuerst! Fluch sofort entfernen (Heilung reduziert)!"],
			L["Raus aus dem Feuerregen."],
		},
	},
	[666] = {
		text = L["Garr + 8 Feuerschwörer\n\n"]
			.. L["- Antimagischer Impuls: entfernt Buffs bei Spielern in der Nähe.\n"]
			.. L["- Magmafesseln: verlangsamt Spieler in der Nähe.\n"]
			.. L["- Feuerschwörer: explodieren beim Tod (Eruption) -> Nahkämpfer weg von sterbenden Adds.\n"]
			.. L["- Feuerschwörer sind Elementare -> Hexer können sie verbannen.\n\n"]
			.. L["Taktik: Jedem Add ein Symbol geben, Hexer verbannen zugewiesene Adds, Krieger tanken den Rest. Adds einzeln töten."],
		post = {
			L["GARR: Hexer verbannen ihre Symbole! Tanks übernehmen die restlichen Adds."],
			L["Nahkampf weg von sterbenden Adds (Explosion). Adds einzeln töten."],
		},
	},
	[667] = {
		text = L["Shazzrah\n\n"]
			.. L["- Arkane Explosion: Flächenschaden um den Boss -> Nahkämpfer vorsichtig, Fernkämpfer auf Abstand.\n"]
			.. L["- Blinzeln: teleportiert sich und setzt die Bedrohung zurück -> Tanks im Raum verteilen.\n"]
			.. L["- Fluch des Shazzrah: erhöhter Magieschaden -> entfluchen.\n"]
			.. L["- Gegenzauber: unterbricht Zauberer in der Nähe.\n"]
			.. L["- Magiedämpfung: Schutzbuff auf dem Boss -> Magie bannen / läutern.\n\n"]
			.. L["Taktik: Mehrere Tanks verteilen, Fernkämpfer auf maximaler Distanz, Flüche entfernen, Buff vom Boss bannen."],
		post = {
			L["SHAZZRAH: Tanks verteilen (Blinzeln)! Fernkämpfer auf Abstand!"],
			L["Flüche entfernen, Buff vom Boss bannen."],
		},
	},
	[668] = {
		text = L["Baron Geddon\n\n"]
			.. L["- Lebende Bombe: Spieler explodiert nach kurzer Zeit -> SOFORT aus dem Raid laufen.\n"]
			.. L["- Inferno: starker Flächenschaden um den Boss -> Nahkämpfer heraus.\n"]
			.. L["- Mana entzünden: verbrennt Mana -> bannen.\n"]
			.. L["- Am Ende des Kampfes explodiert er -> Nahkämpfer weg.\n\n"]
			.. L["Taktik: Raid verteilt aufstellen, Bomben-Träger laufen zu einem festen Platz, Mana entzünden bannen.\n"]
			.. L["Kann Bindungen des Windsuchers droppen (legendär)."],
		post = {
			L["GEDDON: Lebende Bombe -> SOFORT aus dem Raid laufen! Inferno -> Nahkampf raus!"],
			L["Mana entzünden bannen. Am Ende Explosion -> weg vom Boss."],
		},
	},
	[669] = {
		text = L["Sulfuronherold + 4 Priester der Flammenschuppen\n\n"]
			.. L["- Priester: heilen (Dunkle Besserung) -> UNTERBRECHEN!\n"]
			.. L["- Schattenwort: Schmerz -> bannen.\n"]
			.. L["- Inspiration: verstärkt die Adds.\n"]
			.. L["- Hand des Ragnaros: Betäubung und Rückstoß in der Nähe.\n"]
			.. L["- Flammenspeer: Feuerschaden auf Gruppen.\n\n"]
			.. L["Taktik: Priester einzeln töten und konsequent unterbrechen, Sulfuron separat tanken, zuletzt töten."],
		post = {
			L["SULFURON: Priester zuerst und UNTERBRECHEN (Heilung)!"],
			L["Sulfuron separat tanken. Schattenwort: Schmerz bannen."],
		},
	},
	[670] = {
		text = L["Golemagg der Verbrenner + 2 Kernwüter\n\n"]
			.. L["- Kernwüter: werden separat getankt und müssen nicht getötet werden.\n"]
			.. L["- Magmaspritzer: stapelnder Debuff auf dem Tank -> Tankwechsel bei vielen Stapeln.\n"]
			.. L["- Pyroschlag: Feuerschaden auf zufällige Ziele.\n"]
			.. L["- Erdbeben bei wenig Leben: Schaden für Nahkämpfer.\n\n"]
			.. L["Taktik: Hunde abseits tanken, Golemagg mit zwei Tanks im Wechsel, gegen Ende Nahkampf vorsichtig."],
		post = {
			L["GOLEMAGG: Kernwüter abseits tanken und NICHT töten! Fokus auf Golemagg."],
			L["Tankwechsel bei hohen Magmaspritzer-Stapeln."],
		},
	},
	[671] = {
		text = L["Majordomus Exekutus + 4 Heiler + 4 Elite der Flammenschuppen\n\n"]
			.. L["- Majordomus selbst wird nicht getötet; der Kampf endet, wenn alle Adds tot sind.\n"]
			.. L["- Magiereflexion / Schadensschild: bei aktivem Schild Angriffe stoppen!\n"]
			.. L["- Teleport: wirft Spieler in die Feuergrube.\n"]
			.. L["- Heiler: heilen und Schattenblitz -> unterbrechen.\n"]
			.. L["- Elite: Großer Feuerball und Explosion.\n\n"]
			.. L["Taktik: Heiler zuerst, Adds mit Symbolen verteilen, beim Schild sofort aufhören. Danach erscheint Ragnaros."],
		post = {
			L["MAJORDOMUS: Heiler zuerst und unterbrechen! Bei Schild SOFORT aufhören!"],
			L["Symbole beachten, Elite separat tanken."],
		},
	},
	[672] = {
		text = L["Ragnaros\n\n"]
			.. L["- Zorn des Ragnaros: Rückstoß aller Nahkämpfer -> Nahkämpfer laufen kurz vorher heraus.\n"]
			.. L["- Lavaschlag: wenn niemand in Nahkampfreichweite ist -> immer ein Tank in Reichweite!\n"]
			.. L["- Elementarfeuer: Feuerschaden über Zeit auf dem Tank.\n"]
			.. L["- Nach einiger Zeit taucht er ab -> Söhne der Flamme erscheinen und müssen schnell getötet werden.\n\n"]
			.. L["Taktik: Feuerresistenz für Tanks und Nahkämpfer, Ersatztank bereit, Fernkämpfer verteilt, Söhne mit allen Kräften töten."],
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

Data.MarkerTemplates = {
	{ id = "standard", name = L["Standard"], order = { 8, 7, 6, 5, 4, 3, 2, 1 }, note = L["Totenkopf, Kreuz, Viereck, Mond, Dreieck, Diamant, Kreis, Stern."] },
	{ id = "lucifron", name = L["Lucifron"], order = { 8, 7 }, note = L["Totenkopf und Kreuz auf die zwei Beschützer."] },
	{ id = "gehennas", name = L["Gehennas"], order = { 8, 7 }, note = L["Totenkopf und Kreuz auf die zwei Adds."] },
	{ id = "garr", name = L["Garr (Verbannen)"], order = { 1, 2, 3, 4, 5, 6, 7, 8 }, note = L["Jedes Add ein Symbol. Hexer verbannen ihr zugewiesenes Symbol (Stern zuerst)."] },
	{ id = "sulfuron", name = L["Sulfuron"], order = { 8, 7, 6, 5 }, note = L["Vier Priester: Totenkopf, Kreuz, Viereck, Mond in Tötungsreihenfolge."] },
	{ id = "golemagg", name = L["Golemagg"], order = { 6, 5 }, note = L["Viereck und Mond auf die Kernwüter (nicht töten)."] },
	{ id = "majordomo", name = L["Majordomus"], order = { 8, 7, 6, 5, 4, 3, 2, 1 }, note = L["Zuerst die 4 Heiler (Totenkopf, Kreuz, Viereck, Mond), dann die 4 Elite (Dreieck, Diamant, Kreis, Stern)."] },
}

function Data.GetTemplate(id)
	for _, t in ipairs(Data.MarkerTemplates) do
		if t.id == id then return t end
	end
	return Data.MarkerTemplates[1]
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
