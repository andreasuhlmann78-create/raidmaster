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

RM.PRUEFPUNKTE = {
	{ id = "TR", title = "Testroutine ohne Fehler", since = "3.0.27",
		todo = "Im Chat /rm testroutine eingeben und warten, bis das Fenster mit dem Bericht erscheint (etwa 1 Minute). Nicht kämpfen.",
		expect = "Im Bericht 0 FEHLER; T180 bis T184 OK; unten die Zeile 'MARKT-NETZ: v7 · an · …'." },
	{ id = "MNT", title = "Markt-Zähler nach der Testroutine sauber", since = "3.0.26",
		todo = "Nichts extra tun – wird mit der Testroutine (Punkt TR) geprüft.",
		expect = "In der Zeile 'MARKT-NETZ' steht kein 'verworfen: aus'; der Zähler 'aus' ist 0." },
	{ id = "TB", title = "Testbericht kommt in #testberichte", since = "3.0.27",
		todo = "Im Berichtsfenster der Testroutine auf 'Neu laden und melden' klicken (oder /reload). Danach im Discord #testberichte nachsehen.",
		expect = "Innert etwa einer Minute ein Bericht 'RaidMaster 3.0.29' mit 0 FEHLER. Dann hier OK drücken." },
	{ id = "MN2", title = "Schalter 'Marktdaten teilen'", since = "3.0.25",
		todo = "/rm öffnen, Reiter Einstellungen: den Haken 'Marktdaten teilen (anonym, nur Preise)' einmal aus- und wieder einschalten, Maus darüber halten.",
		expect = "Der Schalter steht in einer eigenen Zeile über 'Addon unterstützen', überlappt nichts, der Tooltip erklärt ihn." },
	{ id = "MN2B", title = "Aus bleibt nach /reload aus", since = "3.0.25",
		todo = "Haken 'Marktdaten teilen' ausschalten, /reload eingeben. Danach den Haken wieder einschalten.",
		expect = "Nach dem /reload ist der Haken weiter aus (dieser Punkt wird dann von selbst grün)." },
	{ id = "MN1", title = "Vollscan wird mitgelesen", since = "3.0.25",
		todo = "Am Auktionshaus mit AHSentinel einen Vollscan machen ('Marktdaten teilen' an). Danach diese Liste wieder öffnen.",
		expect = "Der Punkt wird grün mit 'Scans n' (n ≥ 1); während des Scans kein Ruckeln, keine Lua-Fehlermeldung." },
	{ id = "BL", title = "Befehlsliste beim Tippen", since = "3.0.24",
		todo = "Im Chat /rm be tippen und in der Liste einen Befehl anklicken. Dann /rm ver tippen und Enter drücken.",
		expect = "Die Liste filtert beim Tippen, ein Klick führt den Befehl aus, Enter führt den oberen Eintrag aus; im Chatfeld bleibt nichts stehen." },
	{ id = "RT", title = "Symbole in Forever ohne Sperre", since = "3.0.16",
		todo = "In einer Gruppe als Leiter vor Gegnern /rm adds eingeben; dann mit /rm bar die Symbol-Leiste zeigen und ein Symbol anklicken.",
		expect = "Im Chat ein Vorschlag, das angeklickte Symbol erscheint am Ziel, keine Meldung 'Aktion blockiert'." },
	{ id = "T54B", title = "Systemmeldung mit geschütztem Text", since = "3.0.16",
		todo = "In WoW Forever im Kampf jemanden in die Gruppe einladen lassen (oder selbst einladen werden), während RaidMaster läuft.",
		expect = "Es kommt keine Lua-Fehlermeldung (Wortlaut Testroutine T54b: echte geschützte Texte lassen sich nicht nachstellen)." },
	{ id = "TT", title = "Tooltips bei anderer UI-Skalierung", since = "3.0.16",
		todo = "Spiel-Einstellungen → UI-Skalierung z. B. auf 0,8 stellen, /rm öffnen und mit der Maus über mehrere Knöpfe fahren.",
		expect = "Jeder Tooltip erscheint direkt neben dem Knopf, nicht verschoben oder abgeschnitten. Danach Skalierung zurück." },
	{ id = "SS", title = "Erstkill-Screenshot an Discord", since = "3.0.16",
		todo = "Einen Boss zum ersten Mal mit RaidMaster legen (Einstellung Erstkill an). Nach dem Kampf /reload.",
		expect = "Fanfare und Ansage im Spiel; im Discord #ruhmeshalle der Screenshot mit dem Boss-Namen." },
	{ id = "SP", title = "Übernahme vor dem Einloggen belegt", since = "3.0.23",
		todo = "Am zweiten Rechner den Uploader laufen lassen, WoW starten, im Anmeldebildschirm warten bis der Uploader 'fertig – du kannst einloggen' meldet, dann einloggen.",
		expect = "Dieser Punkt wird nach dem Einloggen von selbst grün (Prüfblock des Uploaders gelesen)." },
	{ id = "CONS", title = "Frage zur Weitergabe der Testberichte", since = "3.0.21",
		todo = "Mit nur RaidMaster geladen einloggen, während ein Sammler der Gilde online ist, und die Frage zur Weitergabe beantworten.",
		expect = "Die Frage kommt genau einmal; ohne Zustimmung wird nichts gesendet. Der Punkt wird grün, sobald geantwortet ist." },
	{ id = "GS2", title = "Gebote mit AHSentinel und älterem RaidMaster", since = "3.0.20",
		todo = "Mit AHSentinel geladen in einer Gruppe mit jemandem, der eine ältere RaidMaster-Version hat: ein Gebot abgeben, einmal DKP ändern.",
		expect = "Gebot, DKP und Einteilung kommen beim anderen an (nachfragen). Dann OK drücken." },
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
