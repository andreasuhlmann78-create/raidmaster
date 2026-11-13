-- ============================================================
-- RaidMaster - Commands.lua (ab 3.0.24, Auftrag BL)
-- EINE Befehlstabelle RM.COMMANDS für beides: der Slash-Handler /rm führt aus ihr aus, die Befehlsliste beim Tippen
-- (CmdHint.lua) zeigt aus ihr an. Neue Befehle nur hier eintragen – dann stehen sie automatisch in der Liste (T-BL1).
--
-- Eintrag: { "<deutsches Wort [Zusatz]>", "<englisches Wort [Zusatz]>", "<Beschreibung (deutscher Text, übersetzt
--            in den Locale-Dateien)>", words = { genaue Wörter }, pats = { Lua-Muster }, dev = nur Entwickler,
--            run = function(msg) end }
-- Treffer: msg (klein geschrieben) ist eines der words oder passt auf eines der pats; der ERSTE passende Eintrag
-- gewinnt (Reihenfolge wie im bisherigen Handler bis 3.0.23). Kein Treffer -> Hauptfenster.
-- ============================================================
local ADDON, RM = ...
local L = RM.L

local function Rest(msg) return (msg:match("^%S+%s*(.*)$")) end

RM.COMMANDS = {
	{ "bar", "bar", "Symbol-Leiste ein- oder ausblenden", words = { "bar" },
		run = function() RM.Markers.ToggleBar() end },
	{ "reset", "reset", "Fensterpositionen zurücksetzen (lädt die Oberfläche neu)", words = { "reset" },
		run = function() RM.db.config.positions = {}; RM.Act.ReloadUI() end },
	{ "adds", "mark", "Adds markieren (alle sichtbaren, nach Vorlage)", words = { "adds", "mark" },
		run = function() RM.Markers.MarkAdds() end },
	{ "aus", "clear", "Alle Symbole entfernen", words = { "clear", "aus" },
		run = function() RM.Markers.ClearAll() end },
	{ "sync", "sync", "Daten vom Raid anfordern (DKP, Einteilung)", words = { "sync" },
		run = function() RM.Comm.RequestSync() end },
	{ "test", "test", "Test-Werkzeug öffnen (Entwickler)", words = { "test" }, dev = true,
		run = function() if RM.Test then RM.Test.Toggle() end end },
	{ "testroutine", "testroutine", "Testroutine ausführen (Entwickler)", pats = { "^testroutine" }, dev = true,
		run = function(msg) if RM.Test and RM.Test.Slash then RM.Test.Slash(msg) end end },
	{ "beute <Boss>", "loot <boss>", "Beute eines Bosses aus der eigenen Beute-Datenbank", words = { "loot" },
		pats = { "^beute", "^loot%s" },
		run = function(msg) if RM.LootDB then RM.LootDB.PrintBoss(Rest(msg)) end end },
	{ "berufe", "professions", "Eigene Berufe einlesen", pats = { "^berufe", "^professions" },
		run = function() if RM.Prof then RM.Prof.ReadNext() end end },
	{ "handwerk <Gegenstand>", "craft <item>", "Wer kann diesen Gegenstand herstellen?", pats = { "^handwerk", "^craft" },
		run = function(msg)
			if not RM.Prof then return end
			local q = msg:match("^%S+%s+(.+)$")
			if q then RM.Prof.PrintFind(q) else RM.Prof.ReadNext() end
		end },
	{ "rekorde", "records", "Gilden-Rekorde anzeigen", words = { "rekorde", "records" },
		run = function() if RM.Records then RM.Records.Print() end end },
	{ "bank <Gegenstand>", "bank <item>", "Gildenbank durchsuchen", pats = { "^bank" },
		run = function(msg) if RM.Bank then RM.Bank.PrintFind(Rest(msg)) end end },
	{ "bereit", "ready", "Bereitschaftscheck starten", words = { "bereit", "ready" },
		run = function() if RM.Ready then RM.Ready.Start() end end },
	{ "pull <Sekunden>", "pull <seconds>", "Pull-Countdown (Standard 10 Sekunden)", pats = { "^pull" },
		run = function(msg) if RM.Timer then RM.Timer.Pull(tonumber(msg:match("(%d+)"))) end end },
	{ "pause <Minuten>", "break <minutes>", "Pause-Timer für den Raid", pats = { "^pause", "^break" },
		run = function(msg) if RM.Timer then RM.Timer.Break(tonumber(msg:match("(%d+)"))) end end },
	{ "lücken", "gaps", "Lücken im Raid anzeigen (fehlende Rollen, Buffs)", words = { "luecken", "lücken", "gaps" },
		run = function() if RM.Gaps then RM.Gaps.Open() end end },
	{ "diag", "diagnose", "Diagnose-Fenster ein/aus", words = { "diag", "diagnose" },
		run = function() RM.Diag.Toggle() end },
	{ "fix", "fix", "Bekannte Probleme automatisch beheben", words = { "fix" },
		run = function() RM.Diag.Fix() end },
	{ "anleitung", "guide", "Anleitung und Discord-Verbindung", words = { "discord", "anleitung", "guide" },
		run = function() RM.Guide.Toggle() end },
	{ "spenden", "donate", "Entwicklung unterstützen", words = { "spenden", "donate", "support" },
		run = function() RM.Donate.Show() end },
	{ "minimap", "minimap", "Minikarten-Knopf ein/aus", words = { "minimap" },
		run = function() RM.UI.ToggleMinimapButton() end },
	{ "version", "info", "Version und Spielversion anzeigen", words = { "version", "info" },
		run = function()
			RM.Print("v" .. RM.VERSION .. " – " .. RM.GameInfoText() .. " · " .. (RM.LANGUAGES[RM.LOCALE] or RM.LOCALE) ..
				" (" .. RM.GAME_LOCALE .. ")")
		end },
	{ "befehlsliste", "commandlist", "Befehlsliste beim Tippen ein/aus", words = { "befehlsliste", "commandlist" },
		run = function()
			RM.db.config.cmdHint = (RM.db.config.cmdHint == false)
			RM.Print(RM.db.config.cmdHint and L["Befehlsliste beim Tippen: an"] or L["Befehlsliste beim Tippen: aus"])
			if not RM.db.config.cmdHint and RM.CmdHint then RM.CmdHint:Hide() end
		end },
}

-- Passt msg (klein) auf den Eintrag c?
function RM.CommandMatches(c, msg)
	for _, w in ipairs(c.words or {}) do if msg == w then return true end end
	for _, p in ipairs(c.pats or {}) do if msg:match(p) then return true end end
	return false
end

function RM.FindCommand(msg)
	msg = (msg or ""):lower()
	for _, c in ipairs(RM.COMMANDS) do
		if RM.CommandMatches(c, msg) then return c end
	end
	return nil
end

-- Ausführen (auch von der Testroutine benutzt). Entwickler-Befehle prüfen selbst, ob der Entwickler spielt.
function RM.RunCommand(msg)
	msg = (msg or ""):lower()
	local c = RM.FindCommand(msg)
	if c then return c.run(msg) end
	RM.UI.Toggle()
end

SLASH_RAIDMASTER1 = "/rm"
SLASH_RAIDMASTER2 = "/raidmaster"
SlashCmdList["RAIDMASTER"] = function(msg)
	local H = RM.CmdHint
	if H then
		msg = H:Resolve(msg)                          -- frische Auswahl aus der Liste statt des unvollständigen Worts
		if RM.db and RM.db.config then
			RM.db.config.cmdUse = RM.db.config.cmdUse or {}
			pcall(H.Count, H, msg)
		end
	end
	return RM.RunCommand(msg)
end

-- Befehlsliste beim Tippen anbinden
RM.On("PLAYER_LOGIN", function()
	if not (RM.CmdHint and RM.db and RM.db.config) then return end
	RM.db.config.cmdUse = RM.db.config.cmdUse or {}
	RM.CmdHint.Setup({
		commands = RM.COMMANDS,
		prefixes = { "/raidmaster", "/rm" },             -- längstes zuerst prüfen
		display = "/rm",
		run = function(word) SlashCmdList["RAIDMASTER"](word) end,
		store = function() return RM.db and RM.db.config.cmdUse end,
		enabled = function() return RM.db and RM.db.config.cmdHint ~= false end,
		L = L,
		german = function() return RM.LOCALE == "deDE" end,
		dev = function() return RM.IsDev() end,
		noMatch = L["Kein Befehl – /rm öffnet das Fenster"],
		enterText = L["Enter = %s"],
		global = "RaidMasterCmdHint",
	})
end)
