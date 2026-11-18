-- ============================================================
-- RaidMaster - Pruefliste.lua (ab 3.0.28)
-- Prüfliste im Spiel (Entscheid des Nutzers 16.11.2026 06:47) mit dem gemeinsamen Baustein GoldSentinelPruefliste.lua.
-- Nur im Entwicklermodus: "/rm prüfliste" (auch "/rm pruefliste"). Spieler sehen nichts, es kostet nichts.
-- Punkte = die offenen "IM CLIENT PRÜFEN"-Punkte aus auftraege/RaidMaster/offen-raidmaster.txt (höchstens 14), in der
-- Reihenfolge, in der man sie im Spiel am besten nacheinander macht. Erledigte Punkte nimmt die nächste Version heraus,
-- sobald die Prüf-Sitzung sie abgehakt hat.
--
-- "Merkt selbst": RM.PLHit("ID", "Messwert") an der Stelle, wo die Funktion wirklich benutzt wurde; auto() für Messbares;
-- OK / Nicht OK nur dort, wo nur Hinschauen hilft. Während der Testroutine (und im Testmodus) zählt kein Hit – sonst würde
-- die Routine selbst Punkte abhaken.
-- ============================================================
local ADDON, RM = ...

local function GM() return _G.GoldSentinelMarkt end

-- TR-ALLE (3.0.30, Entscheid des Nutzers 17.11. 07:36): jeder Handpunkt ohne Vorwissen verständlich –
-- Wo / nummerierte Schritte (ein Handgriff je Schritt, Namen wie im Spiel) / was du siehst (wörtlich) / was es kostet.
local function Todo(where, ...)
	local t = { "\nWo: " .. where }
	for i, step in ipairs({ ... }) do t[#t + 1] = i .. ". " .. step end
	return table.concat(t, "\n")
end
local function Expect(see, cost)
	return "\n" .. see .. "\nKosten: " .. cost
end

RM.PRUEFPUNKTE = {
	{ id = "TR", title = "Testroutine: alles Automatische", since = "3.0.31",
		todo = Todo("irgendwo, nicht im Kampf (du musst nicht am PC bleiben – der Lauf wartet nie auf dich)",
			"Tippe in den Chat: /rm testroutine alles",
			"Warte, bis im Chat die Zusammenfassung '… von … bestanden' steht (vorher zählt der Chat '1 von 12 …', '2 von 12 …'). Nicht kämpfen."),
		expect = Expect("Im Chat steht z. B. '133 von 133 bestanden, 28 nicht prüfbar – …' – beide Zahlen vor 'bestanden' sind gleich. Steht dahinter 'Noch offen: Berufe – passiert von selbst …', musst du nichts tun: beim nächsten Berufsfenster (bzw. Bank/Briefkasten) holt RaidMaster das nach und sagt es im Chat. Dieser Punkt wird von selbst grün, sobald alles bestanden ist.",
			"kein Gold, ca. 2 Minuten") },
	{ id = "MNT", title = "Markt-Zähler nach der Testroutine sauber", since = "3.0.26",
		todo = Todo("nichts extra tun", "Wird mit Punkt TR (Testroutine) von selbst geprüft."),
		expect = Expect("Dieser Punkt wird nach der Testroutine von selbst grün.", "nichts") },
	{ id = "TB", title = "Testbericht kommt in Discord an", since = "3.0.27",
		todo = Todo("irgendwo, nach Punkt TR",
			"Klicke im Fenster mit dem Testbericht auf den Knopf 'Neu laden und melden' (oder tippe /reload).",
			"Öffne in Discord den Kanal #testberichte."),
		expect = Expect("In #testberichte steht innert etwa 1 Minute ein Bericht 'RaidMaster 3.0.34' ohne das Wort FEHLER. Dann hier auf 'OK' klicken.",
			"kein Gold, ca. 2 Minuten") },
	{ id = "MN2", title = "Haken 'Marktdaten teilen'", since = "3.0.25",
		todo = Todo("irgendwo",
			"Tippe in den Chat: /rm",
			"Klicke oben auf den Reiter 'Einstellungen'.",
			"Klicke rechts auf den Haken 'Marktdaten teilen (anonym, nur Preise)' (Haken geht weg).",
			"Klicke noch einmal darauf (Haken wieder da).",
			"Halte die Maus kurz über den Haken."),
		expect = Expect("Der Haken steht in einer eigenen Zeile über 'Addon unterstützen', nichts überdeckt ihn; ein Hinweis erklärt ihn ('Liest Auktionshaus-Scans mit …'). Dieser Punkt wird beim Klick von selbst grün.",
			"kein Gold, 1 Minute") },
	{ id = "MN2B", title = "Haken 'Marktdaten teilen' bleibt nach /reload aus", since = "3.0.25",
		todo = Todo("irgendwo",
			"Tippe /rm, Reiter 'Einstellungen', Haken 'Marktdaten teilen (anonym, nur Preise)' ausschalten.",
			"Tippe in den Chat: /reload",
			"Nach dem Laden: /rm, Reiter 'Einstellungen' – der Haken ist weiter aus. Schalte ihn wieder ein."),
		expect = Expect("Nach dem /reload ist der Haken aus. Dieser Punkt wird nach dem Laden von selbst grün.", "kein Gold, 2 Minuten") },
	{ id = "MN1", title = "Auktionshaus-Scan wird mitgelesen", since = "3.0.25",
		todo = Todo("Auktionshaus offen (beim Auktionator), AHSentinel geladen, Haken 'Marktdaten teilen' an",
			"Starte in AHSentinel einen vollständigen Scan (wie gewohnt).",
			"Warte, bis der Scan fertig ist.",
			"Tippe in den Chat: /rm prüfliste"),
		expect = Expect("Dieser Punkt ist grün mit 'Scans 1' (oder mehr). Während des Scans ruckelt das Spiel nicht und es kommt keine rote Lua-Fehlermeldung.",
			"kein Gold (Scannen ist gratis), ca. 3 Minuten") },
	{ id = "BL", title = "Befehlsliste beim Tippen", since = "3.0.24",
		todo = Todo("irgendwo",
			"Tippe in den Chat: /rm be (nicht Enter drücken).",
			"Über dem Chat erscheint eine Liste. Klicke darin auf 'bereit'.",
			"Tippe in den Chat: /rm ver und drücke Enter."),
		expect = Expect("Die Liste zeigt nur passende Befehle; der Klick startet den Befehl; Enter führt den obersten Eintrag aus ('version'); im Chatfeld bleibt nichts stehen. Dieser Punkt wird von selbst grün.",
			"kein Gold, 1 Minute") },
	{ id = "RT", title = "Schlachtzugsymbole in WoW Forever", since = "3.0.16",
		todo = Todo("in einer Gruppe, du bist Leiter, Gegner in der Nähe (z. B. vor einer Instanz)",
			"Tippe in den Chat: /rm adds",
			"Tippe in den Chat: /rm bar",
			"Klicke in der Symbol-Leiste, die erscheint, auf ein Symbol (z. B. Totenkopf), während ein Gegner im Ziel ist."),
		expect = Expect("Im Chat steht 'Vorschlag (Vorlage: …): …'; das angeklickte Symbol erscheint über dem Gegner; keine Meldung 'Aktion blockiert' oder 'AddOn … wurde blockiert'.",
			"kein Gold, ca. 3 Minuten") },
	{ id = "T54B", title = "Einladung im Kampf ohne Fehlermeldung", since = "3.0.16",
		todo = Todo("WoW Forever, während eines Kampfes",
			"Lass dich von jemandem in eine Gruppe einladen (oder lade jemanden ein), während du kämpfst."),
		expect = Expect("Es erscheint keine rote Lua-Fehlermeldung. Dann hier auf 'OK' klicken.", "kein Gold, 2 Minuten (braucht einen zweiten Spieler)") },
	{ id = "TT", title = "Hinweise bei anderer UI-Grösse", since = "3.0.16",
		todo = Todo("irgendwo",
			"Drücke Esc und öffne die Optionen (je nach Client 'Optionen' oder 'System').",
			"Suche den Regler 'UI-Skalierung' (falls nötig vorher den Haken 'UI-Skalierung verwenden' setzen) und stelle ihn auf etwa 0,8. Merke dir den alten Wert.",
			"Tippe in den Chat: /rm",
			"Fahre mit der Maus langsam über mehrere Knöpfe im RaidMaster-Fenster.",
			"Stelle die UI-Skalierung wieder auf den alten Wert."),
		expect = Expect("Jeder Hinweis erscheint direkt neben dem Knopf, nicht verschoben oder abgeschnitten. Dann hier auf 'OK' klicken.",
			"kein Gold, 2 Minuten") },
	{ id = "SS", title = "Erstkill-Bild an Discord", since = "3.0.16",
		todo = Todo("Schlachtzug, beim ersten Kill eines Bosses mit RaidMaster",
			"Prüfe vorher: /rm, Reiter 'Einstellungen', Haken 'Erstkill-Feier und Bestzeiten' ist an.",
			"Legt den Boss.",
			"Nach dem Kampf: Tippe in den Chat: /reload"),
		expect = Expect("Fanfare und Ansage im Spiel; in Discord im Kanal #ruhmeshalle das Bild mit dem Boss-Namen. Dieser Punkt wird beim Kill von selbst grün; das Bild in Discord bitte selbst ansehen.",
			"kein Gold, nur beim nächsten Raid") },
	{ id = "SP", title = "Abgleich vor dem Einloggen", since = "3.0.23",
		todo = Todo("am zweiten Rechner (Laptop), vor dem Spielstart",
			"Starte den Uploader (uploader.bat).",
			"Starte WoW und warte im Anmeldebildschirm, bis im Uploader-Fenster 'fertig – du kannst einloggen' steht.",
			"Logge ein."),
		expect = Expect("Dieser Punkt wird nach dem Einloggen von selbst grün.", "kein Gold, 3 Minuten") },
	{ id = "CONS", title = "Frage zum Teilen der Testberichte", since = "3.0.21",
		todo = Todo("auf einem Rechner, auf dem die Frage noch nie beantwortet wurde (z. B. Laptop), während dein Sammler-Charakter in der Gilde online ist",
			"Logge ein und warte etwa 1 Minute.",
			"Es erscheint ein Fenster 'GoldSentinel-Addons: Fehlermeldungen und Testergebnisse (ohne Namen) an den Sammler der Entwickler schicken? …'.",
			"Klicke auf 'Ja' oder 'Nein'."),
		expect = Expect("Die Frage kommt genau einmal; mit 'Nein' wird nichts geteilt. Dieser Punkt wird nach der Antwort von selbst grün.",
			"kein Gold, 2 Minuten") },
	{ id = "GS2", title = "Gebote mit einer älteren RaidMaster-Version", since = "3.0.20",
		todo = Todo("in einer Gruppe mit jemandem, der eine ältere RaidMaster-Version hat; AHSentinel geladen",
			"Starte eine Versteigerung (/rm, Reiter 'Versteigerung').",
			"Lass den anderen ein Gebot abgeben.",
			"Frag ihn, ob er dein Gebot und die DKP sieht."),
		expect = Expect("Gebote und DKP kommen bei beiden an. Dann hier auf 'OK' klicken.", "kein Gold (DKP nur in einem Test-Topf), ca. 5 Minuten, braucht einen zweiten Spieler") },
}

-- Messbare Punkte
local AUTO = {
	MN1 = function()
		local g = GM()
		local s = g and g.Stats and g.Stats()
		local n = s and tonumber(s.scans) or 0
		if n > 0 then return true, "Scans " .. n end
		return nil
	end,
	SP = function()
		local p = RaidMasterDB and RaidMasterDB.syncProbe
		if p ~= nil then return true, "syncProbe " .. tostring(type(p) == "table" and (p.seq or p.t) or p) end
		return nil
	end,
	CONS = function()
		local t = RaidMasterDB and RaidMasterDB.gsTest
		local sh = type(t) == "table" and t.share
		local c = type(sh) == "table" and sh.consent
		if c == true then return true, "zugestimmt" end
		if c == false then return true, "abgelehnt" end
		return nil
	end,
}
for _, p in ipairs(RM.PRUEFPUNKTE) do p.auto = AUTO[p.id] end

-- Liste anmelden, sobald der Entwicklermodus erkannt ist (Battle.net ist beim Laden manchmal noch nicht bereit)
function RM.GetPL()
	local B = _G.GoldSentinelPruefliste
	if not (B and B.Register) then return nil end
	if RM.PL and RM.PL.addon then return RM.PL end
	if not (B.IsDev and B.IsDev()) then return nil end
	RM.PL = B:Register("RaidMaster", {
		db = function() return RaidMasterDB end,
		version = RM.VERSION,
		points = RM.PRUEFPUNKTE,
	})
	return RM.PL and RM.PL.addon and RM.PL or nil
end

-- Während der Testroutine, ihrer Nachlaufzeit und im Testmodus zählt kein Hit (sonst hakt die Routine selbst Punkte ab)
local function Quiet()
	if RM.plTest then return false end
	local R = RM.TestRoutine
	if R and (R.running or R.graceUntil) then return true end
	if RM.db and RM.db.testMode then return true end
	return false
end

function RM.PLHit(id, note)
	if Quiet() then return false end
	local pl = RM.GetPL()
	if not pl then return false end
	return pl:Hit(id, note) and true or false
end

function RM.PLFail(id, note)
	if Quiet() then return false end
	local pl = RM.GetPL()
	if not pl then return false end
	local s = pl:State(id)
	if s == "ok" or s == "auto" then return false end
	return pl:Set(id, "fehler", note) and true or false
end

-- Haken "Marktdaten teilen" in den Einstellungen (Pages.lua) -> schalten und Punkt MN2
function RM.MarktShareFromUI(v)
	RM.SetMarktShare(v)
	RM.PLHit("MN2", v and "an" or "aus")
end

-- Beim Einloggen: was nur hier messbar ist
function RM.PLLoginChecks()
	if RM.db and RM.db.config and RM.db.config.marktTeilen == false then
		RM.PLHit("MN2B", "nach /reload aus")
	end
	local pl = RM.GetPL()
	if pl then pcall(pl.RunAuto, pl) end
end

function RM.OpenPruefliste()
	if not RM.RequireDev() then return end
	local pl = RM.GetPL()
	if pl then pl:Open() end
end

function RM.PLReportLines()
	local pl = RM.GetPL()
	if not pl then return {} end
	local ok, lines = pcall(pl.ReportLines, pl)
	return ok and type(lines) == "table" and lines or {}
end

RM.On("PLAYER_LOGIN", function()
	C_Timer.After(3, function() pcall(RM.PLLoginChecks) end)
end)
