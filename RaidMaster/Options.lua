-- RaidMaster - Optionen (ab 3.0.38, OPT-ALLE nach Vorbild AHSentinel OPT-1, Entscheid des Nutzers 18.11.2026 10:27)
-- Eine Seite "Einstellungen": links Suchfeld und Bereiche, rechts nur die Optionen des Bereichs – eine Spalte, höchstens
-- 12 Zeilen, kein Scrollen. Jede Option steht genau EINMAL hier (vorher verteilt auf 7 Reiter, 3 doppelt, 3 ohne Bedienung).
-- Kurze Beschriftung links, rechts der Wert (an/aus = ein Knopf "An/Aus", Auswahl = Knopfreihe, Namen = Menü, Zahlen = Feld),
-- Erklärung nur im Tooltip. Seltenes unter "Weitere" (eingeklappt), "Standard" je Bereich, Optionen-Knöpfe auf den Seiten
-- öffnen den passenden Bereich (UI.OpenOptions). Gespeichert wird in denselben Schlüsseln wie vorher (RM.db.config.*,
-- RM.db.data.settings.*). Bereiche werden erst beim ersten Zeigen gebaut (Leistung: kein Bild über 16 ms).

local ADDON, RM = ...
local L = RM.L
local UI = RM.UI
local COLORS = UI.COLORS

local O = {}
RM.Opt = O

O.NAV_W = 170          -- linke Leiste (Suchfeld, Bereiche)
O.X = 190              -- rechte Spalte (Seiten-Koordinaten)
O.W = 600
O.LABEL_W = 240        -- Beschriftung (kurz, eine Zeile)
O.CTRL_X = 250         -- Wert beginnt immer an derselben Stelle
O.CTRL_W = 350
O.ROW_H = 32           -- Zeile 30 + Abstand 2
O.TOP = -34            -- erste Zeile unter der Überschrift
O.MAX_ROWS = 12
O.MAX_HITS = 12

local function C() return RM.db.config end
local function S() return RM.db.data.settings end

local function NeedOfficer()
	if RM.CanEdit() then return true end
	RM.Print(L["Dafür brauchst du Offiziersrechte."])
	return false
end

-- Namen säubern wie auf der Loot-Seite bisher (gleicher Code wie Pages.lua CapName)
local function CapName(name)
	if RM.G then return RM.G.CleanName(name or "") or "" end
	if RM.GAME.key == "forever" then
		name = (name or ""):gsub("^%s+", ""):gsub("%s+$", ""):gsub("%s+", " ")
	else
		name = (name or ""):gsub("%s", "")
	end
	if name == "" then return "" end
	return (name:gsub("(%S)(%S*)", function(a, b) return a:upper() .. b:lower() end))
end

---------------------------------------------------------------------------
-- Rechte: dieselben wie auf den Seiten, wo die Option vorher stand
--   leader = Seite Einstellungen (Offiziere) · looter = Seite Loot · lead = Seiten Raid/Anmeldungen/Werbung/Einteilung/
--   Skillungen · leaderbank = Einstellungen ODER Gildenbank (Bank-Charakter)
---------------------------------------------------------------------------
function O.AccessOK(access)
	if access == "leaderbank" then return UI.AccessOK("leader") or UI.AccessOK("bank") end
	return UI.AccessOK(access)
end

---------------------------------------------------------------------------
-- Bereiche und Optionen
---------------------------------------------------------------------------
O.AREAS = {
	{ id = "allgemein", title = L["Allgemein"] },
	{ id = "dkp", title = L["DKP-Vergabe"], guild = true },
	{ id = "gebote", title = L["Gebote"], guild = true },
	{ id = "bosse", title = L["Boss-DKP"], guild = true },
	{ id = "beute", title = L["Beute-Regeln"] },
	{ id = "pm", title = L["Plündermeister"] },
	{ id = "ansagen", title = L["Ansagen im Chat"] },
	{ id = "raid", title = L["Raid & Timer"] },
	{ id = "einladen", title = L["Einladen & Werbung"] },
	{ id = "symbole", title = L["Symbole & Leisten"] },
	-- ST1 (3.0.53, Entscheid des Nutzers 27.11. 09:18): Mitmach-Schalter in EINEM Abschnitt unten, verständlich, Schlüssel unverändert
	{ id = "mithelfen", title = L["Mithelfen"] },
}
O.AREA = {}
for _, a in ipairs(O.AREAS) do O.AREA[a.id] = a end

-- Pfad "a.b" in einer Tabelle lesen/schreiben
local function PathGet(t, path)
	for part in path:gmatch("[^%.]+") do
		if type(t) ~= "table" then return nil end
		t = t[part]
	end
	return t
end

O.DEFS = {}
local function Def(area, d)
	d.area = area
	O.DEFS[#O.DEFS + 1] = d
	return d
end
-- an/aus in RM.db.config; on = true: fehlt der Wert, gilt "an" (wie bisher "~= false")
local function CToggle(area, key, label, tip, access, extra)
	local d = { kind = "toggle", key = key, label = label, tip = tip, access = access,
		get = function() if extra and extra.on then return C()[key] ~= false end return C()[key] and true or false end,
		set = function(v) C()[key] = v and true or false end }
	if extra then for k, v in pairs(extra) do if k ~= "on" then d[k] = v end end end
	return Def(area, d)
end
local function CChoice(area, key, label, tip, access, opts, extra)
	local d = { kind = "choice", key = key, label = label, tip = tip, access = access, opts = opts,
		get = function() return C()[key] end, set = function(v) C()[key] = v end }
	if extra then for k, v in pairs(extra) do d[k] = v end end
	return Def(area, d)
end
-- Gilden-Einstellung: Zahl (wirkt erst mit "Speichern und an die Gilde verteilen", wie bisher)
local function SNum(area, key, label, tip, clamp, extra)
	local d = { kind = "num", key = "settings." .. key, skey = key, label = label, tip = tip, access = "leader", guild = true,
		get = function() return S()[key] end,
		set = function(v) S()[key] = clamp and clamp(v) or v end }
	if extra then for k, v in pairs(extra) do d[k] = v end end
	return Def(area, d)
end
-- Gilden-Einstellung: an/aus (sofort lokal, verteilt beim Speichern – wie bisher)
local function SToggle(area, key, label, tip, extra)
	local d = { kind = "toggle", key = "settings." .. key, skey = key, label = label, tip = tip, access = "leader", guild = true,
		get = function() return S()[key] and true or false end, set = function(v) S()[key] = v and true or false end }
	if extra then for k, v in pairs(extra) do d[k] = v end end
	return Def(area, d)
end

-- Allgemein ---------------------------------------------------------------
-- 3.0.40 (Entscheid des Nutzers 18.11. 11:10, Hinweis "Spieler ohne Testbefehle"): die persönlichen Optionen (Minimap-Knopf,
-- Item-Tooltip, Erstkill-Feier, Marktdaten, Befehlsliste, Screenshot, Unterstützen) braucht JEDER Spieler – darum für alle ("all").
-- Vorher nur auf der Offiziers-Seite Einstellungen (Mitglieder kamen nur per /rm minimap bzw. /rm befehlsliste an zwei davon).
Def("allgemein", { kind = "toggle", key = "minimap.hide", invert = true, label = L["Minimap-Knopf"], access = "all",
	tip = L["Zeigt den RaidMaster-Knopf an der Minimap. Aus = ausgeblendet (öffnen dann mit /rm)."],
	get = function() return C().minimap.hide and true or false end,
	set = function(v)
		C().minimap.hide = v and true or false
		local b = _G["RaidMasterMinimapButton"]
		if b then if v then b:Hide() else b:Show() end end
	end })
CToggle("allgemein", "itemTooltip", L["Infos im Item-Tooltip"],
	L["Item-Tooltip ergänzen (Droprate, letzter Preis)"] .. "\n" .. L["Zeigt im Item-Tooltip, wie oft das Item bei euch gedroppt ist und wofür es zuletzt versteigert wurde."],
	"all", { on = true })
CToggle("allgemein", "records", L["Erstkill-Feier & Bestzeiten"],
	L["Erstkill: Fanfare, Schlachtzugwarnung und Screenshot für Discord. Bestzeiten: 'Neuer Rekord!' bei schnelleren Kills."], "all", { on = true })
Def("mithelfen", { kind = "toggle", key = "marktTeilen", label = L["Marktdaten teilen"], access = "all",
	tip = L["Marktdaten teilen (anonym, nur Preise)"] .. "\n" .. L["Liest Auktionshaus-Scans mit, die ohnehin gemacht werden (z. B. von AHSentinel), und teilt nur Preise und Mengen – ohne Namen. Aus = nichts lesen, nichts senden."],
	get = function() return C().marktTeilen ~= false end,
	set = function(v) RM.MarktShareFromUI(v and true or false) end })
CToggle("allgemein", "bankScan", L["Bank-Charakter"],
	L["Bank-Charakter (Bestand an Discord)"] .. "\n" .. L["Beim Öffnen von Bank, Briefkasten (und Gildenbank, falls vorhanden) liest RaidMaster den Bestand aus.\nEr kommt in den Discord (#gildenbank, /bank).\nAuf diesem Charakter erscheint dann der Bereich Gildenbank."],
	"leaderbank", { after = function() if UI.UpdateNav then UI.UpdateNav() end end })
Def("allgemein", { kind = "toggle", key = "cmdHint", label = L["Befehlsliste beim Tippen"], access = "all", def = true,
	tip = L["Tippst du /rm in den Chat, zeigt eine Liste die passenden Befehle (auch: /rm befehlsliste)."],
	get = function() return C().cmdHint ~= false end,
	set = function(v)
		C().cmdHint = v and true or false
		if not v and RM.CmdHint and RM.CmdHint.Hide then RM.CmdHint:Hide() end
	end })
Def("mithelfen", { kind = "donate", label = L["Addon unterstützen"], access = "all",
	tip = L["Öffnet das Fenster zum Unterstützen (PayPal) – nur auf Klick."] })
CToggle("allgemein", "firstKillScreenshot", L["Screenshot beim Erstkill"],
	L["Beim Erstkill macht RaidMaster einen Screenshot; er kommt in den Discord (#ruhmeshalle)."], "all", { on = true, more = true })

-- DKP-Vergabe (Gilde) ------------------------------------------------------
local function Max0(v) return math.max(0, v) end
SNum("dkp", "dkpStart", L["Pünktlich zum Raidstart"], L["DKP für alle, die beim Raidstart dabei sind."])
SNum("dkp", "dkpEnd", L["Raid bis zum Ende"], L["DKP für alle, die beim Raidende dabei sind."])
SNum("dkp", "defaultBossDKP", L["Andere Bosse (Standard)"], L["DKP je Boss, wenn unter Boss-DKP nichts eigenes steht."])
SToggle("dkp", "firstKillDouble", L["Erstkill zählt doppelt"], L["Der erste Kill eines Bosses gibt doppelte DKP."])
SToggle("dkp", "onlyOnline", L["DKP nur für Spieler online"], L["Nur Spieler online erhalten DKP"])
SNum("dkp", "standbyStartDKP", L["Ersatzbank beim Raidstart"],
	L["Spieler auf der Ersatzbank bekommen beim Raidstart einmalig diese DKP – danach keine Boss- oder Endpunkte."], Max0,
	{ get = function() return S().standbyStartDKP or 10 end })
SToggle("dkp", "standbyGetsDKP", L["Ersatzbank erhält DKP"], L["Ersatzbank erhält DKP (nur beim Raidstart)"])
SNum("dkp", "decayPct", L["Decay in %"], L["Um so viel Prozent sinken alle positiven DKP beim Decay."], function(v) return math.max(0, math.min(100, v)) end)
Def("dkp", { kind = "toggle", key = "settings.autoDecay", skey = "autoDecay", label = L["Decay jeden Mittwoch"], access = "leader", guild = true,
	tip = L["Automatisch jeden Mittwoch (Raid-Reset)"] .. "\n" .. L["Einmal pro Woche nach dem Raid-Reset bucht der erste Offizier, der online ist, den Verfall auf alle Raids – nie während eines Raids."],
	get = function() return S().autoDecay ~= false end,
	set = function(v)                 -- wie bisher auf der Seite Raid: sofort verteilt
		if not NeedOfficer() then return end
		S().autoDecay = v and true or false
		RM.DKP.SettingsChanged()
	end })
SNum("dkp", "officerRank", L["Offiziersränge bis Index"],
	L["Gildenrang-Index: 0 = Gildenmeister, 1 = nächster Rang usw. Alle Ränge bis zu diesem Index dürfen DKP ändern."],
	function(v) return math.max(0, math.min(9, v)) end, { more = true })

-- Gebote (Gilde) -----------------------------------------------------------
SNum("gebote", "minBid", L["Mindestgebot"], L["Kleinstes erlaubtes Gebot."], Max0)
SNum("gebote", "bidIncrement", L["Gebotsschritt"], L["Um so viel muss ein Gebot das höchste übertreffen."], function(v) return math.max(1, v) end)
SNum("gebote", "auctionTime", L["Gebotsdauer (Sekunden)"], L["Dauer (Sekunden)"] .. ": 10–120", function(v) return math.max(10, math.min(120, v)) end)
SToggle("gebote", "antiSnipe", L["Späte Gebote verlängern"], L["Verlängern bei späten Geboten (5 Sek.)"] .. "\n" .. L["Kommt in den letzten 5 Sekunden ein Gebot, wird auf 5 Sekunden verlängert."])
SToggle("gebote", "mainBeforeTwink", L["Main vor Twink"], L["Twinks gewinnen eine Versteigerung nur, wenn kein Main bietet.\nEin Main übernimmt ein Twink-Gebot schon ab dem Mindestgebot."])
SToggle("gebote", "allowNegative", L["Negative DKP erlauben"], L["Spieler dürfen mehr bieten, als sie haben."])

-- Boss-DKP (Gilde): Raid wählen, Bosse seitenweise (höchstens 10 je Bild, kein Scrollen)
Def("bosse", { kind = "bosses", key = "settings.bossDKP", label = L["Raid"], access = "leader", guild = true,
	tip = L["Raid wählen, dessen Boss-DKP du einstellen willst."] })

-- Beute-Regeln -------------------------------------------------------------
local AUCT, MAN, DE, BANK, CRAFT = L["Versteigerung"], L["Manuell"], L["Entzauberer"], L["Gildenbank"], L["Handwerker"]
local function Rule(key, label, opts, tip)
	return Def("beute", { kind = "choice", key = "rules." .. key, label = label, access = "looter", opts = opts, tip = tip,
		get = function() return C().rules[key] end, set = function(v) C().rules[key] = v end })
end
Rule("epic", L["Epische Ausrüstung"], { { "auction", AUCT }, { "manual", MAN } }, L["Legendäre Items"] .. ": " .. L["immer nur Hinweis"])
Rule("blue", L["Blaue Ausrüstung"], { { "auction", AUCT }, { "de", DE }, { "bank", BANK }, { "manual", MAN } })
Rule("recipe", L["Rezepte und Pläne"], { { "bank", BANK }, { "crafter", CRAFT }, { "auction", AUCT }, { "manual", MAN } })
Rule("mats", L["Handwerksmaterialien"], { { "bank", BANK }, { "crafter", CRAFT }, { "auction", AUCT }, { "manual", MAN } })
CChoice("beute", "fallback", L["Ohne Gebot an"], L["Keine Gebote"] .. ": " .. L["wer das Item bekommt, wenn niemand bietet."], "looter",
	{ { "de", DE }, { "bank", BANK }, { "manual", MAN } })
CToggle("beute", "autoDistribute", L["Automatisch zuteilen"], L["Mats/Rezepte/Blaues automatisch zuteilen"], "looter")
Def("beute", { kind = "name", key = "bankChar", label = L["Gildenbank-Charakter"], access = "looter", more = true,
	tip = L["Bekommt Items mit Regel Gildenbank."],
	get = function() return C().bankChar or "" end, set = function(v) C().bankChar = CapName(v) end })
Def("beute", { kind = "drop", key = "deChar", label = L["Entzauberer"], access = "looter", more = true,
	tip = L["Bekommt Items, auf die niemand bietet (wenn eingestellt), und blaue Items mit Regel Entzauberer."],
	build = function() return RM.Loot.RecipientChoices("deChar") end,
	get = function() return C().deChar or "" end, set = function(v) C().deChar = v; UI.RefreshCurrent() end })
Def("beute", { kind = "drop", key = "crafterChar", label = L["Handwerker"], access = "looter", more = true,
	tip = L["Bekommt Rezepte und Materialien mit Regel Handwerker."],
	build = function() return RM.Loot.RecipientChoices("crafterChar") end,
	get = function() return C().crafterChar or "" end, set = function(v) C().crafterChar = v; UI.RefreshCurrent() end })

-- Plündermeister -----------------------------------------------------------
Def("pm", { kind = "drop", key = "lootMaster", label = L["Plündermeister"], access = "looter",
	tip = L["Plündermeister wählen – als Raidleiter wird die Plündermethode im Spiel sofort umgestellt."],
	build = function() return RM.Loot.MasterChoices() end,
	get = function() return C().lootMaster or "" end, set = function(v) RM.Loot.SetMaster(v) end })
Def("pm", { kind = "choice", key = "lootThreshold", label = L["Plünderschwelle"], access = "looter",
	tip = L["Empfohlen: Selten (grün) – der Plündermeister verteilt dann schon grüne Items, Kerne und Rezepte sowieso."],
	opts = { { 2, L["Selten (grün)"] }, { 3, L["Rar (blau)"] }, { 4, L["Episch (lila)"] } },
	get = function() return C().lootThreshold end, set = function(v) RM.Loot.SetThreshold(v) end })
CToggle("pm", "setLootOnStart", L["Bei Raidstart einstellen"], L["Loot-Einstellungen bei Raidstart setzen"], "looter")
Def("pm", { kind = "toggle", key = "autoLoot", label = L["Plündermeister absichern"], access = "looter",
	tip = L["Vergessenen Plündermeister automatisch setzen"] .. "\n" .. L["Als Raidleiter: steht die Plündermethode nicht auf Plündermeister, setzt RaidMaster den gespeicherten Plündermeister und die Schwelle."],
	get = function() return C().autoLoot and true or false end,
	set = function(v) C().autoLoot = v and true or false; if v then RM.Loot.EnsureSettings() end end })

-- Ansagen im Chat ----------------------------------------------------------
CToggle("ansagen", "announceLoot", L["Loot im Raidchat ansagen"], L["Loot gesammelt im Raidchat ansagen"], "looter")
CToggle("ansagen", "announceBids", L["Gebote im Raidchat ansagen"], L["Gebote im Raidchat ansagen"], "looter")
CToggle("ansagen", "welcome", L["Begrüßung beim Raidstart"],
	L["Begrüßt den Raid im Raidchat, passend zur Raidzone. Gäste und Spieler von der Ersatzbank werden mit Namen begrüßt."], "lead", { on = true })
CToggle("ansagen", "pullCountdownChat", L["Countdown im Raidchat"], L["Countdown 5-4-3-2-1 im Raidchat"], "lead", { on = true })
CToggle("ansagen", "whisperReplies", L["Auf !dkp-Flüstern antworten"], L["Auf !dkp-Flüstern antworten"], "looter")
CToggle("ansagen", "unlootedReminder", L["Ungeplünderten Boss melden"], L["Erinnern, wenn Boss nicht geplündert"], "looter")
CToggle("ansagen", "tradeFallback", L["Abwesende: an mich + Handel"], L["Bei Abwesenheit an mich + Handelsliste"], "looter")
CToggle("ansagen", "coreHound", L["Kürschner ansagen (Kernhund)"],
	L["Kürschner ansagen, wenn ein Kernhund stirbt"] .. "\n" .. L["Der Raidleiter sagt die Kürschner mit Addon im Raid an (nach Skill sortiert)."], "lead",
	{ cond = function() return RM.Caps.combatLog and true or false end })

-- Raid & Timer -------------------------------------------------------------
CChoice("raid", "pullSeconds", L["Pull-Timer"], L["Pull-Timer mit Countdown – auch für Deadly Boss Mods und BigWigs. Nochmal klicken bricht ab."], "lead",
	{ { 5, "5 s" }, { 8, "8 s" }, { 10, "10 s" }, { 15, "15 s" }, { 20, "20 s" } },
	{ get = function() return C().pullSeconds or 10 end, set = function(v) C().pullSeconds = v; RM.Fire("TIMER_CHANGED") end })
CChoice("raid", "breakMinutes", L["Pause der Boss-Leiste"], L["Knopf 'Pause' der Boss-Leiste: so viele Minuten."], "lead",
	{ { 3, "3 min" }, { 5, "5 min" }, { 10, "10 min" }, { 15, "15 min" } },
	{ get = function() return C().breakMinutes or 5 end, set = function(v) C().breakMinutes = v; RM.Fire("TIMER_CHANGED") end })
CChoice("raid", "timerAddons", L["Timer an Boss-Addons"], L["An welche Boss-Addons die Timer gehen (Pull und Pause)."], "lead",
	{ { "both", L["DBM + BigWigs"] }, { "dbm", L["nur DBM"] }, { "bigwigs", L["nur BigWigs"] }, { "none", L["ohne"] } },
	{ get = function() return C().timerAddons or "both" end })
CChoice("raid", "fireResMin", L["Feuerwiderstand ab"], L["Ab wie viel Feuerwiderstand der Bereitschafts-Check zufrieden ist (z. B. für Ragnaros)."], "lead",
	{ { 0, L["egal"] }, { 100, "100" }, { 150, "150" }, { 200, "200" }, { 250, "250" } },
	{ get = function() return tonumber(C().fireResMin) or 0 end })
CToggle("raid", "readyCheckGame", L["Bereitschaft auch im Spiel"],
	L["Der Bereitschafts-Check von RaidMaster startet auch den Bereitschafts-Check des Spiels (Raidleiter oder Assistent)."], "lead", { on = true })
CToggle("raid", "specScan", L["Skillungen-Scan (5 Min.)"],
	L["Als Raidleiter automatisch alle 5 Minuten scannen"] .. "\n" .. L["Nur für Raidleiter, Assistenten und Offiziere."], "lead")

-- Einladen & Werbung -------------------------------------------------------
CToggle("einladen", "autoInvite", L["Auto-Einladung"],
	L["Lädt automatisch alle Aufgestellten ein, sobald der Raid öffnet, und Nachzügler bis 30 Min. nach Beginn.\nDein Spiel muss dafür laufen."], "lead",
	{ after = function() UI.RefreshCurrent() end })
CChoice("einladen", "autoInviteMinutes", L["Raid öffnet vor Beginn"], L["So viele Minuten vor Raidbeginn öffnet der Raid."], "lead",
	{ { 5, L["5 Min."] }, { 10, L["10 Min."] }, { 15, L["15 Min."] }, { 20, L["20 Min."] }, { 30, L["30 Min."] } },
	{ get = function() return C().autoInviteMinutes or 15 end, after = function() UI.RefreshCurrent() end })
CToggle("einladen", "autoGroups", L["Gruppen sofort sortieren"], L["Jeder, der dem Raid beitritt, kommt sofort in seine feste Gruppe."], "lead")
CToggle("einladen", "adAutoInvite", L["Auf „inv“ einladen"],
	L["Auf geflüstertes \"inv\" automatisch einladen (30 Minuten nach der Werbung)"] .. "\n" .. L["Spieler flüstern dir \"inv\" – RaidMaster lädt sie ein, solange der Raid nicht voll ist.\nAus einer Gruppe wird automatisch ein Schlachtzug."], "lead")
Def("einladen", { kind = "drop", key = "adChannel", label = L["Kanal für die Werbung"], access = "lead",
	tip = L["Kanäle, denen du beigetreten bist. Einem Kanal beitreten: /join Name"],
	build = function()
		local Ad = RM.Ad
		local items, found = {}, false
		local cur = Ad.Target()
		for _, t in ipairs(Ad.Targets()) do items[#items + 1] = { t[1], t[2] }; if t[1] == cur then found = true end end
		if not found then items[#items + 1] = { cur, Ad.TargetLabel(cur) } end
		return { { items = items } }
	end,
	get = function() return RM.Ad.Target() end, set = function(v) C().adChannel = v; UI.RefreshCurrent() end })

-- Symbole & Leisten --------------------------------------------------------
CToggle("symbole", "markerBar", L["Markierungsleiste"], L["Markierungsleiste anzeigen"], "lead",
	{ after = function() RM.Fire("CONFIG_CHANGED") end })
CToggle("symbole", "markerLocked", L["Leiste fixieren"], L["Die Markierungsleiste lässt sich nicht mehr verschieben."], "lead")
Def("symbole", { kind = "drop", key = "markerTemplate", label = L["Vorlage für „Auto“"], access = "lead",
	tip = L["Welche Symbole 'Auto' setzt. Vorlagen der Bosse nach Raid geordnet."],
	build = function()
		local Data = RM.Data
		local groups = { { items = { { "standard", Data.BaseTemplates[1].name } } } }
		for _, key in ipairs(Data.PoolOrder or {}) do
			local items = {}
			for i, t in ipairs(Data.TemplatesForRaid(key)) do if i > 1 then items[#items + 1] = { t.id, t.name } end end
			if items[1] then groups[#groups + 1] = { text = RM.DKP.PoolName(key), items = items } end
		end
		local cur = C().markerTemplate
		local t = cur and Data.GetTemplate(cur)
		if cur and t and t.id == cur and cur ~= "standard" then
			local seen = false
			for _, g in ipairs(groups) do for _, it in ipairs(g.items) do if it[1] == cur then seen = true end end end
			if not seen then table.insert(groups[1].items, { cur, t.name }) end
		end
		return groups
	end,
	get = function() return C().markerTemplate end,
	set = function(v) C().markerTemplate = v; RM.Markers.ResetUsed(); RM.Fire("CONFIG_CHANGED") end })
CToggle("symbole", "autoTemplate", L["Vorlage beim Boss wählen"], L["Vorlage beim Bosskampf automatisch wählen"], "lead")
CToggle("symbole", "bossBar", L["Boss-Leiste bei Boss im Ziel"],
	L["Nimmt der Raidleiter oder ein Assistent einen Boss ins Ziel, erscheint eine Leiste: ein Klick sagt die Taktik als Schlachtzugwarnung an und setzt die Symbole wie im Automatikmodus."],
	"lead", { on = true, after = function() RM.Fire("CONFIG_CHANGED") end })

-- Liste je Bereich
for _, a in ipairs(O.AREAS) do a.defs = {} end
for _, d in ipairs(O.DEFS) do table.insert(O.AREA[d.area].defs, d) end

-- Standardwert einer Option (aus RM.DEFAULT_CONFIG / RM.DEFAULT_SETTINGS, sonst def.def)
function O.DefaultOf(d)
	if d.def ~= nil then return d.def end
	if d.skey then return RM.DEFAULT_SETTINGS[d.skey] end
	if d.key then return PathGet(RM.DEFAULT_CONFIG, d.key) end
end

-- Ist die Option für diesen Spieler da? (Rechte wie vorher + Bedingung, z. B. Kernhunde nur mit Kampflog)
function O.Visible(d)
	if d.cond and not d.cond() then return false end
	return O.AccessOK(d.access)
end
function O.AreaVisible(a)
	for _, d in ipairs(a.defs) do if O.Visible(d) then return true end end
	return false
end
function O.AnyVisible()
	for _, a in ipairs(O.AREAS) do if O.AreaVisible(a) then return true end end
	return false
end

---------------------------------------------------------------------------
-- Bausteine: Knopf "An/Aus", Knopfreihe
---------------------------------------------------------------------------
local function Toggle(parent, d)
	local b
	b = UI.Button(parent, "", 100, 24, function()
		d.set(not d.get())
		if d.after then d.after() end
		b:Refresh()
	end, d.tip)
	function b:Refresh()
		local on = d.get() and true or false
		if d.invert then on = not on end
		self:SetText(on and L["An"] or L["Aus"])
		self:SetAccent(on)
	end
	b:Refresh()
	UI.registry[#UI.registry + 1] = { kind = "check", key = d.key, label = d.label, getter = d.get,
		setter = function(v) d.set(v); if d.after then d.after() end end, frame = b }
	return b
end

local function Choice(parent, d)
	local row = CreateFrame("Frame", nil, parent)
	local n = #d.opts
	local gap = 6
	local w = math.floor((O.CTRL_W - gap * (n - 1)) / n)
	row:SetSize(O.CTRL_W, 24)
	row.buttons = {}
	for i, o in ipairs(d.opts) do
		local b = UI.Button(row, o[2], w, 24, function()
			d.set(o[1])
			if d.after then d.after() end
			row:Refresh()
		end, d.tip)
		b:SetPoint("TOPLEFT", row, "TOPLEFT", (i - 1) * (w + gap), 0)
		b.value = o[1]
		row.buttons[i] = b
	end
	function row:Refresh()
		local cur = d.get()
		for _, b in ipairs(self.buttons) do b:SetAccent(b.value == cur) end
	end
	row:Refresh()
	UI.registry[#UI.registry + 1] = { kind = "cycle", key = d.key, label = d.label, options = d.opts, getter = d.get,
		setter = function(v) d.set(v); if d.after then d.after() end end, frame = row }
	return row
end

---------------------------------------------------------------------------
-- Seite bauen
---------------------------------------------------------------------------
local page, nav, search, searchHint, hitsFrame
local guildFields = {}       -- Zahlenfelder der Gilden-Bereiche (gespeichert mit "Speichern und an die Gilde verteilen")
local bossPending = {}       -- Boss-DKP: noch nicht gespeicherte Eingaben je Boss
O.current = nil
O.built = {}                 -- gebaute Bereiche (je Bereich ein Rahmen)
O.buildMs = {}               -- Bauzeit je Bereich (für die Testroutine)

local function Now() return debugprofilestop and debugprofilestop() or 0 end

-- Tooltip über der ganzen Zeile: Beschriftung + Erklärung
local function RowTip(row, d)
	row:EnableMouse(true)
	row:SetScript("OnEnter", function(self)
		UI.ShowTip(self, function(tt)
			tt:AddLine(d.label, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
			if d.tip then for line in tostring(d.tip):gmatch("[^\n]+") do tt:AddLine(line, 1, 1, 1, true) end end
		end)
	end)
	row:SetScript("OnLeave", function() GameTooltip:Hide() end)
end

local function NewRow(af, d)
	local row = CreateFrame("Frame", nil, af)
	row:SetSize(O.W, 30)
	row.flash = row:CreateTexture(nil, "BACKGROUND")
	row.flash:SetAllPoints()
	row.flash:SetColorTexture(COLORS.accent[1], COLORS.accent[2], COLORS.accent[3], 0.22)
	row.flash:Hide()
	row.label = UI.Text(row, d.label, 12)
	row.label:SetPoint("LEFT", row, "LEFT", 4, 0)
	row.label:SetWidth(O.LABEL_W - 8)
	row.label:SetWordWrap(false)
	UI.FitText(row.label, O.LABEL_W - 8, 12, 9, 1)
	row.def = d
	RowTip(row, d)
	return row
end

-- Gilden-Werte speichern / verwerfen (wie bisher auf der Seite Einstellungen)
function O.SaveGuild()
	if not NeedOfficer() then return false end
	for _, f in ipairs(guildFields) do
		local v = tonumber(f.edit:GetText())
		if v then f.def.set(math.floor(v)) end      -- alle Gilden-Zahlen (Boss-DKP getrennt über bossPending)
	end
	for id, v in pairs(bossPending) do S().bossDKP[id] = math.floor(v) end
	wipe(bossPending)
	RM.DKP.SettingsChanged()
	return true
end
function O.RevertGuild()
	wipe(bossPending)
	for _, f in ipairs(guildFields) do f.edit:SetText(tostring(f.def.get() or 0)) end
	O.RefreshArea()
end

-- Bereich "Boss-DKP": Raid wählen, dann die Bosse seitenweise
local BOSS_PAGE = 10
local function BuildBosses(af, a)
	local st = { pool = "mc", page = 1, list = {} }
	a.bossState = st
	local d = a.defs[1]
	local top = NewRow(af, d)
	local drop = UI.Dropdown(top, 220, function() return UI.PoolGroups(RM.db.data) end, function() return st.pool end,
		function(v) st.pool = v; st.page = 1; O.RefreshArea() end, d.tip)
	drop:SetPoint("LEFT", top, "LEFT", O.CTRL_X, 0)
	top.ctrl = drop
	a.rows = { top }
	st.rows = {}
	for i = 1, BOSS_PAGE do
		local bd = { label = "", tip = L["DKP für diesen Boss (gilt für die ganze Gilde, nach dem Speichern)."] }
		local r = NewRow(af, bd)
		local e = UI.EditBox(r, 70, 24, true)
		e:SetPoint("LEFT", r, "LEFT", O.CTRL_X, 0)
		e:SetScript("OnTextChanged", function(self, user)
			if user and r.bossId then bossPending[r.bossId] = tonumber(self:GetText()) end
		end)
		r.ctrl = e
		st.rows[i] = r
		a.rows[#a.rows + 1] = r
	end
	st.pager = UI.Button(af, "", O.W, 24, function()
		st.page = st.page + 1
		if (st.page - 1) * BOSS_PAGE >= #st.list then st.page = 1 end
		O.RefreshArea()
	end, L["Weitere Bosse dieses Raids"])
	st.note = UI.Text(af, L["Die Bosse dieses Raids werden beim ersten Kill automatisch erkannt. Bis dahin gilt der Standardwert."], 11,
		COLORS.muted[1], COLORS.muted[2], COLORS.muted[3])
	st.note:SetWidth(O.W)
	function a.refreshCustom()
		drop:Refresh()
		st.list = RM.Data.BossesForPool(st.pool, RM.db.data)
		local pages = math.max(1, math.ceil(#st.list / BOSS_PAGE))
		if st.page > pages then st.page = 1 end
		local y = O.TOP - O.ROW_H
		for i, r in ipairs(st.rows) do
			local b = st.list[(st.page - 1) * BOSS_PAGE + i]
			r.bossId = b and b.id or nil
			if b then
				r.label:SetText(b.name)
				UI.FitText(r.label, O.LABEL_W - 8, 12, 9, 1)
				if not r.ctrl:HasFocus() then
					local v = bossPending[b.id] or S().bossDKP[b.id] or b.dkp or S().defaultBossDKP
					r.ctrl:SetText(tostring(v or 0))
				end
				r:ClearAllPoints(); r:SetPoint("TOPLEFT", af, "TOPLEFT", 0, y); r:Show()
				y = y - O.ROW_H
			else
				r:Hide()
			end
		end
		st.pager:ClearAllPoints()
		if pages > 1 then
			local from = st.page * BOSS_PAGE + 1
			if from > #st.list then from = 1 end
			local to = math.min(#st.list, from + BOSS_PAGE - 1)
			st.pager:SetText(string.format(L["Weitere: Bosse %d–%d von %d"], from, to, #st.list))
			st.pager:SetPoint("TOPLEFT", af, "TOPLEFT", 0, y - 2)
			st.pager:Show()
			y = y - O.ROW_H
		else
			st.pager:Hide()
		end
		st.note:ClearAllPoints()
		if #st.list == 0 then st.note:SetPoint("TOPLEFT", af, "TOPLEFT", 4, y - 4); st.note:Show() else st.note:Hide() end
		return y
	end
end

local function BuildControl(row, d)
	local c
	if d.kind == "toggle" then
		c = Toggle(row, d)
	elseif d.kind == "choice" then
		c = Choice(row, d)
	elseif d.kind == "drop" then
		c = UI.Dropdown(row, 220, d.build, d.get, d.set, d.tip)
	elseif d.kind == "num" then
		c = UI.EditBox(row, 70, 24, true)
		c:SetScript("OnEnter", function(self) UI.ShowTip(self, function(tt) tt:AddLine(d.tip or d.label, 1, 1, 1, true) end) end)
		c:SetScript("OnLeave", function() GameTooltip:Hide() end)
		function c:Refresh() if not self:HasFocus() then self:SetText(tostring(d.get() or 0)) end end
		guildFields[#guildFields + 1] = { edit = c, def = d }
	elseif d.kind == "name" then
		c = UI.EditBox(row, 220, 24)
		c:SetScript("OnTextChanged", function(self, user) if user then d.set(self:GetText()) end end)
		c:SetScript("OnEditFocusLost", function(self)
			self:SetBackdropBorderColor(unpack(COLORS.border))
			self:SetText(d.get() or "")
		end)
		function c:Refresh() if not self:HasFocus() then self:SetText(d.get() or "") end end
	elseif d.kind == "donate" then
		c = RM.Donate.CreateButton(row, 120, 24)
	end
	if c then
		c:ClearAllPoints()
		c:SetPoint("LEFT", row, "LEFT", O.CTRL_X, 0)
		if rawget(c, "Refresh") and d.kind ~= "toggle" and d.kind ~= "choice" then c:Refresh() end
	end
	row.ctrl = c
	return c
end

-- Bereich bauen (einmal, beim ersten Zeigen)
function O.BuildArea(a)
	if O.built[a.id] then return O.built[a.id] end
	local t0 = Now()
	local af = CreateFrame("Frame", nil, page)
	af:SetPoint("TOPLEFT", page, "TOPLEFT", O.X, 0)
	af:SetSize(O.W, UI.CONTENT_H)
	af.title = UI.Header(af, a.title)
	af.title:SetPoint("TOPLEFT", af, "TOPLEFT", 0, 0)
	af.title.line:SetWidth(O.W - 120)          -- rechts steht der Knopf "Standard"
	af.std = UI.Button(af, L["Standard"], 110, 22, function()
		UI.Confirm(string.format(L["Standardwerte für '%s' setzen?"], a.title) .. (a.guild and ("\n" .. L["Die Werte gelten für die ganze Gilde und werden sofort verteilt."]) or ""),
			function() O.ResetArea(a.id) end)
	end, L["Setzt alle Optionen dieses Bereichs auf die Standardwerte."])
	af.std:SetPoint("TOPRIGHT", af, "TOPRIGHT", 0, 2)
	a.rows = {}
	a.more = {}
	if a.id == "bosse" then
		BuildBosses(af, a)
	else
		for _, d in ipairs(a.defs) do
			local row = NewRow(af, d)
			BuildControl(row, d)
			if d.more then a.more[#a.more + 1] = row else a.rows[#a.rows + 1] = row end
		end
		if a.more[1] then
			af.moreBtn = UI.Button(af, "", O.W, 24, function()
				a.expanded = not a.expanded
				O.RefreshArea()
			end, L["Selten gebrauchte Optionen dieses Bereichs."])
		end
	end
	if a.guild then
		af.save = UI.Button(af, L["Speichern und an die Gilde verteilen"], 300, 30, function() O.SaveGuild() end)
		af.save:SetAccent(true)
		af.revert = UI.Button(af, L["Verwerfen"], 100, 30, function() O.RevertGuild() end)
		af.note = UI.Text(af, L["Diese Werte gelten für die ganze Gilde und werden mit allen Addon-Nutzern abgeglichen. "]
			.. L["Häkchen werden sofort lokal übernommen und beim Speichern verteilt."], 11, COLORS.muted[1], COLORS.muted[2], COLORS.muted[3])
		af.note:SetWidth(O.W)
	end
	af:Hide()
	O.built[a.id] = af
	O.buildMs[a.id] = Now() - t0
	return af
end

-- Zeilen eines Bereichs legen (nur sichtbare; "Weitere" eingeklappt)
local function Layout(a, af)
	local y = O.TOP
	local n = 0
	if a.refreshCustom then
		y = a.refreshCustom()
		local top = a.rows[1]
		top:ClearAllPoints(); top:SetPoint("TOPLEFT", af, "TOPLEFT", 0, O.TOP); top:Show()
		n = 1
		for _, r in ipairs(a.bossState.rows) do if r:IsShown() then n = n + 1 end end
		if a.bossState.pager:IsShown() then n = n + 1 end
	else
		local function put(row)
			if O.Visible(row.def) then
				row:ClearAllPoints()
				row:SetPoint("TOPLEFT", af, "TOPLEFT", 0, y)
				row:Show()
				y = y - O.ROW_H
				n = n + 1
				local c = rawget(row, "ctrl")
				if c and rawget(c, "Refresh") then c:Refresh() end
			else
				row:Hide()
			end
		end
		for _, row in ipairs(a.rows) do put(row) end
		local visMore = 0
		for _, row in ipairs(a.more) do if O.Visible(row.def) then visMore = visMore + 1 end end
		if rawget(af, "moreBtn") then
			if visMore > 0 then
				af.moreBtn:ClearAllPoints()
				af.moreBtn:SetPoint("TOPLEFT", af, "TOPLEFT", 0, y - 2)
				af.moreBtn:SetText(a.expanded and L["Weitere ausblenden"] or string.format(L["Weitere (%d)"], visMore))
				af.moreBtn:Show()
				y = y - O.ROW_H
				n = n + 1
			else
				af.moreBtn:Hide()
			end
		end
		for _, row in ipairs(a.more) do
			if a.expanded then put(row) else row:Hide() end
		end
	end
	if rawget(af, "save") then
		af.save:ClearAllPoints(); af.save:SetPoint("TOPLEFT", af, "TOPLEFT", 0, y - 10)
		af.revert:ClearAllPoints(); af.revert:SetPoint("TOPLEFT", af, "TOPLEFT", 306, y - 10)
		af.note:ClearAllPoints(); af.note:SetPoint("TOPLEFT", af, "TOPLEFT", 0, y - 48)
		if RM.CanEdit() then af.save:Enable() else af.save:Disable() end
	end
	a.lineCount = n
	return n
end

function O.RefreshArea()
	if not page or not O.current then return end
	local a = O.AREA[O.current]
	local af = a and O.built[a.id]
	if af then Layout(a, af) end
end

-- Standardwerte eines Bereichs (Gilde: sofort verteilt, nach Rückfrage – wie "Speichern")
function O.ResetArea(id)
	local a = O.AREA[id]
	if not a then return false end
	if a.guild and not NeedOfficer() then return false end
	if id == "bosse" then
		local st = a.bossState
		for _, b in ipairs(RM.Data.BossesForPool(st and st.pool or "mc", RM.db.data)) do S().bossDKP[b.id] = nil; bossPending[b.id] = nil end
	else
		for _, d in ipairs(a.defs) do
			if d.set and d.kind ~= "donate" and O.Visible(d) then
				local v = O.DefaultOf(d)
				if d.key == "settings.autoDecay" then S().autoDecay = v
				else d.set(v) end
				if d.after then d.after() end
			end
		end
	end
	if a.guild then RM.DKP.SettingsChanged() end
	for _, f in ipairs(guildFields) do if f.def.area == id then f.edit:SetText(tostring(f.def.get() or 0)) end end
	O.RefreshArea()
	UI.RefreshCurrent()
	return true
end

-- Bereich zeigen (baut ihn beim ersten Mal)
function O.Select(id)
	if not page then return end
	local a = O.AREA[id]
	if not a or not O.AreaVisible(a) then
		a = nil
		for _, x in ipairs(O.AREAS) do if O.AreaVisible(x) then a = x break end end
	end
	if not a then return end
	if search and search:GetText() ~= "" then search:SetText("") end
	local af = O.BuildArea(a)
	for aid, f in pairs(O.built) do if aid ~= a.id then f:Hide() end end
	if hitsFrame then hitsFrame:Hide() end
	O.current = a.id
	af:Show()
	Layout(a, af)
	O.UpdateNav()
	return af
end

function O.UpdateNav()
	if not nav then return end
	local y = -32
	for _, a in ipairs(O.AREAS) do
		local b = nav.buttons[a.id]
		if O.AreaVisible(a) then
			b:ClearAllPoints(); b:SetPoint("TOPLEFT", page, "TOPLEFT", 0, y); b:Show()
			b:SetAccent(a.id == O.current and not (hitsFrame and hitsFrame:IsShown()))
			y = y - 32
		else
			b:Hide()
		end
	end
end

-- Zeile kurz hervorheben (nach einem Suchtreffer)
local function Flash(row)
	if not row then return end
	row.flash:Show()
	C_Timer.After(1.5, function() row.flash:Hide() end)
end
function O.RowOf(d)
	local a = O.AREA[d.area]
	for _, r in ipairs(a.rows or {}) do if r.def == d then return r end end
	for _, r in ipairs(a.more or {}) do if r.def == d then return r end end
end

-- Zu einer Option springen: Bereich öffnen, "Weitere" aufklappen, Zeile hervorheben
function O.Jump(d)
	local a = O.AREA[d.area]
	if d.more then a.expanded = true end
	O.Select(d.area)
	Flash(O.RowOf(d) or (a.rows and a.rows[1]))
end

-- Suche über alle Bereiche (Beschriftung, Erklärung, Bereichsname, Schlüssel)
local function Low(s) return tostring(s or ""):lower() end
function O.Search(q)
	q = Low(q):gsub("^%s+", ""):gsub("%s+$", "")
	local hits = {}
	if q == "" then return hits end
	for _, d in ipairs(O.DEFS) do
		if O.Visible(d) then
			local a = O.AREA[d.area]
			local hay = Low(d.label) .. "\n" .. Low(d.tip) .. "\n" .. Low(a.title) .. "\n" .. Low(d.key)
			if hay:find(q, 1, true) then hits[#hits + 1] = d end
		end
	end
	return hits
end

local function ShowHits(q)
	local hits = O.Search(q)
	if not hitsFrame then
		hitsFrame = CreateFrame("Frame", nil, page)
		hitsFrame:SetPoint("TOPLEFT", page, "TOPLEFT", O.X, 0)
		hitsFrame:SetSize(O.W, UI.CONTENT_H)
		hitsFrame.title = UI.Header(hitsFrame, "")
		hitsFrame.title:SetPoint("TOPLEFT", hitsFrame, "TOPLEFT", 0, 0)
		hitsFrame.title.line:SetWidth(O.W)
		hitsFrame.buttons = {}
		for i = 1, O.MAX_HITS do
			local b = UI.Button(hitsFrame, "", O.W, 28, function(self) if self.def then O.Jump(self.def) end end)
			b.label:ClearAllPoints()
			b.label:SetPoint("LEFT", 10, 0)
			b.label:SetPoint("RIGHT", -10, 0)
			b.label:SetJustifyH("LEFT")
			b:SetPoint("TOPLEFT", hitsFrame, "TOPLEFT", 0, O.TOP - (i - 1) * O.ROW_H)
			hitsFrame.buttons[i] = b
		end
		hitsFrame.more = UI.Text(hitsFrame, "", 11, COLORS.muted[1], COLORS.muted[2], COLORS.muted[3])
		hitsFrame.more:SetPoint("TOPLEFT", hitsFrame, "TOPLEFT", 4, O.TOP - O.MAX_HITS * O.ROW_H - 4)
		hitsFrame.more:SetWidth(O.W)
	end
	hitsFrame.title:SetText(string.format(L["Suche: %d Treffer"], #hits))
	for i, b in ipairs(hitsFrame.buttons) do
		local d = hits[i]
		b.def = d
		if d then
			b:SetText(d.label .. "  |cff9c9ca8· " .. O.AREA[d.area].title .. "|r")
			b.tooltip = d.tip
			b:Show()
		else
			b:Hide()
		end
	end
	hitsFrame.more:SetText(#hits > O.MAX_HITS and string.format(L["… und %d weitere – genauer tippen"], #hits - O.MAX_HITS)
		or (#hits == 0 and L["Nichts gefunden. Anderes Wort versuchen (z. B. Pull, Gebot, Minimap)."] or ""))
	for _, f in pairs(O.built) do f:Hide() end
	hitsFrame:Show()
	O.UpdateNav()
	return hits
end
O.ShowHits = ShowHits

function O.Build(p)
	page = p
	-- Suchfeld oben links
	search = UI.EditBox(page, O.NAV_W, 24)
	search:SetPoint("TOPLEFT", page, "TOPLEFT", 0, 0)
	searchHint = UI.Text(search, L["Option suchen ..."], 11, COLORS.muted[1], COLORS.muted[2], COLORS.muted[3])
	searchHint:SetPoint("LEFT", 8, 0)
	search:SetScript("OnTextChanged", function(self)
		local q = self:GetText()
		if q == "" then
			searchHint:Show()
			if hitsFrame and hitsFrame:IsShown() then O.Select(O.current) end
		else
			searchHint:Hide()
			ShowHits(q)
		end
	end)
	search:SetScript("OnEnterPressed", function(self)
		local hits = O.Search(self:GetText())
		self:ClearFocus()
		if hits[1] then O.Jump(hits[1]) end
	end)
	-- Bereiche
	nav = { buttons = {} }
	for _, a in ipairs(O.AREAS) do
		local b = UI.Button(page, a.title, O.NAV_W, 28, function() O.Select(a.id) end)
		b.label:ClearAllPoints()
		b.label:SetPoint("LEFT", 10, 0)
		b.label:SetPoint("RIGHT", -6, 0)
		b.label:SetJustifyH("LEFT")
		b:SetText(a.title)
		nav.buttons[a.id] = b
	end
	O.UpdateNav()
	return function()
		if hitsFrame and hitsFrame:IsShown() then O.UpdateNav() return end
		local a = O.current and O.AREA[O.current]
		if not a or not O.AreaVisible(a) or not O.built[a.id] then
			O.Select(O.pendingArea or O.current or "allgemein")
			O.pendingArea = nil
		else
			Layout(a, O.built[a.id])
			O.UpdateNav()
		end
	end
end

-- 3.0.40: Einstellungsfenster des Spiels (Esc > Optionen > AddOns > RaidMaster) mit Knopf "Optionen öffnen" – normaler Weg für
-- Spieler, die RaidMaster dort suchen. Moderne API (Settings, Era/Forever) zuerst, sonst die alte (InterfaceOptions_AddCategory).
function O.RegisterGamePanel()
	if O.gamePanel then return O.gamePanel end
	local panel = CreateFrame("Frame")
	panel.name = "RaidMaster"
	local title = UI.Text(panel, "RaidMaster", 16, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
	title:SetPoint("TOPLEFT", panel, "TOPLEFT", 16, -16)
	local text = UI.Text(panel, L["Alle Einstellungen von RaidMaster stehen im eigenen Fenster (auch: /rm optionen)."], 12)
	text:SetPoint("TOPLEFT", panel, "TOPLEFT", 16, -42)
	text:SetWidth(520)
	local btn = UI.Button(panel, L["Optionen öffnen"], 180, 26, function()
		-- RM-TAINT1 (3.0.48): Blizzard-Fenster nie selbst schliessen (HideUIPanel aus Addon-Code verbreitet Taint) – stattdessen
		-- liegt das eigene Fenster, solange es offen ist, über dem Einstellungsfenster des Spiels (Esc schliesst erst RaidMaster)
		UI.OpenOptions("allgemein")
		local main = _G["RaidMasterMainFrame"]
		if main and main.SetFrameStrata then main:SetFrameStrata("DIALOG"); main.raisedOverSettings = true end
	end)
	btn:SetPoint("TOPLEFT", panel, "TOPLEFT", 16, -72)
	panel.openButton = btn
	if Settings and Settings.RegisterCanvasLayoutCategory and Settings.RegisterAddOnCategory then
		local ok, cat = pcall(Settings.RegisterCanvasLayoutCategory, panel, "RaidMaster")
		if ok and cat then pcall(Settings.RegisterAddOnCategory, cat); O.gameCategory = cat; O.gamePanelWay = "Settings" end
	elseif InterfaceOptions_AddCategory then
		pcall(InterfaceOptions_AddCategory, panel)
		O.gamePanelWay = "InterfaceOptions"
	end
	O.gamePanel = panel
	return panel
end
RM.On("PLAYER_LOGIN", function() pcall(O.RegisterGamePanel) end)

-- Optionen-Knopf für die Seiten: öffnet den passenden Bereich
function UI.OpenOptions(areaId)
	O.pendingArea = areaId
	UI.Open("settings")
	if page then O.Select(areaId or O.current) end
	O.pendingArea = nil
end

function UI.OptionsButton(parent, areaId, w, h, text)
	local a = O.AREA[areaId]
	return UI.Button(parent, text or L["Optionen"], w or 110, h or 24, function() UI.OpenOptions(areaId) end,
		string.format(L["Öffnet die Einstellungen im Bereich '%s'."], a and a.title or areaId))
end
