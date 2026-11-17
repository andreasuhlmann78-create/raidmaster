-- 3.0.16: Testroutine einmal komplett im Testaufbau laufen lassen (TOC über Umgebung: 16001 Forever, 11509 Classic Era)
-- Prüft: 0 FEHLER außer solchen, die nur an der Nachbildung liegen (benannt), Sandbox OK, R.running danach false,
-- Spion: keine echte Aktion (Blizzard-Funktionen der Nachbildung werden gezählt).
GAMETOC = ROUTINE_TOC or tonumber(os.getenv("TOC") or "16001"); ADDONDIR = os.getenv("ADDONDIR") or "../../../RaidMaster"
local forever = GAMETOC == 16001
SECRET = {}
if forever then function issecretvalue(v) return SECRET[v] == true end end
-- alter Client: Talentbäume wie Classic Era (vor dem Laden, RM.Caps wird beim Laden berechnet)
if not forever then
	function GetTalentTabInfo(tab) return "Baum" .. tab, nil, ({ 5, 5, 41 })[tab] end
	function GetNumTalentTabs() return 3 end
end
dofile((os.getenv("HARNESS") or "harness.lua"))
local RM = ADDON_NS
-- Nachbildung: registrierte Ereignisse abfragen (RegisterEvent merkt sie in _ev)
RM.frame.IsEventRegistered = function(self, e) return self._ev and self._ev[e] or false end
assert(loadfile(ADDONDIR .. "/Test/LootData.lua"))("RaidMaster", RM)
assert(loadfile(ADDONDIR .. "/Test/Test.lua"))("RaidMaster", RM)

-- Nachbildung ergänzen (nur in dieser Testdatei)
local base = geterrorhandler()
-- RM-TF-1 (3.0.31): der unterste Handler steht für das Fehlerfenster des Spiels ("Fehlerfenster an", scriptErrors = 1).
-- Jeder Aufruf mit einem absichtlichen Testfehler der Routine wäre ein Fenster beim Nutzer -> gezählt, muss 0 sein.
GAME_WINDOW_TESTERRORS, GAME_WINDOW_CALLS = 0, 0
local handler = function(e)
	GAME_WINDOW_CALLS = GAME_WINDOW_CALLS + 1          -- jeder Aufruf hier wäre im Spiel ein Fehlerfenster
	if tostring(e):find("RaidMaster-Testfehler", 1, true) then
		GAME_WINDOW_TESTERRORS = GAME_WINDOW_TESTERRORS + 1
		print("FEHLERFENSTER DES SPIELS: " .. tostring(e))
		return
	end
	return base(e)
end
function seterrorhandler(f) handler = f end
function geterrorhandler() return handler end
local clock = 0
function debugprofilestop() return os.clock() * 1000 end
function IsInGroup() return false end
function UnitIsConnected(u) return u == "player" end
function UnitFactionGroup() return "Horde" end
function StaticPopup_Hide() end
function GetCVar() return "1" end
function GetAddOnMetadata(addon, field)
	for line in io.lines(ADDONDIR .. "/RaidMaster.toc") do
		local v = line:match("^## " .. field .. ": (.+)$")
		if v then return (v:gsub("%s+$", "")) end
	end
end
function UnitCanAttack() return false end
function UnitRace() return "Orc", "Orc" end
REAL_CALLS = {}
local function count(name) return function() REAL_CALLS[name] = (REAL_CALLS[name] or 0) + 1 end end
SendChatMessage = count("SendChatMessage")
SetRaidTarget = count("SetRaidTarget")
GiveMasterLoot = count("GiveMasterLoot")
CastSpellByName = count("CastSpellByName")
NotifyInspect = count("NotifyInspect")
ReloadUI = count("ReloadUI")
DoReadyCheck = count("DoReadyCheck")
Screenshot = count("Screenshot")
InviteUnit = count("InviteUnit")
-- Beute von Onyxia als bekannte Items (für den Durchlauf T43); T43NODATA=1: Client kennt die Beute nicht (Gegenprobe T43)
for key, list in pairs(os.getenv("T43NODATA") == "1" and {} or RaidMasterTestLoot) do
	if tostring(key):match("^249:") then
		for _, b in ipairs(list) do for _, id in ipairs(b.i or {}) do
			ITEMS[id] = ITEMS[id] or { "|cffa335ee|Hitem:" .. id .. "::::::::60:::::|h[Ony " .. id .. "]|h|r", 4, 4, 1, "INVTYPE_HEAD" }
		end end
	end
end

-- vorhandene echte Daten (Sandbox muss sie unverändert lassen)
RaidMasterDB = { data = { players = { Echt1 = { c = "WARRIOR", d = { mc = 77 } } }, log = {}, version = 5 }, prof = { Testa = { p = {} } },
	lootdb = { v = 2, kills = {}, trash = {}, items = {}, bosses = {} } }
Fire("ADDON_LOADED", "RaidMaster"); Fire("PLAYER_LOGIN")
Advance(6)
local before = { players = RM.db.data.players.Echt1.d.mc, prof = RM.db.prof }
RaidMasterDB.gsTest.errors = {}

local R = RM.TestRoutine
local only = ROUTINE_AREA or os.getenv("AREA")
R.Run(only)
local waited = 0
-- STOPAT=<Sekunden>: "/rm testroutine stop" nach so vielen Sekunden (Abbruch muss alles zurückstellen)
local stopAt = tonumber(os.getenv("STOPAT") or "")
while R.running and waited < 400 do
	Advance(0.5); waited = waited + 0.5
	if stopAt and waited >= stopAt and R.running then SlashCmdList["RAIDMASTER"]("testroutine stop"); stopAt = nil end
end
Advance(15)

local fails = 0
local function check(c, msg) if not c then fails = fails + 1; print("FAIL: " .. msg) else print("ok: " .. msg) end end
local text = R.lastText or ""
print(text)
-- Fehler, die nur an der Nachbildung liegen (kein echtes Spiel): hier mit Grund benennen
local EMU = {}
local emuText = os.getenv("EMU") or ""
for id in emuText:gmatch("[^,]+") do EMU[id] = true end
local real = {}
for line in text:gmatch("[^\n]+") do
	local id = line:match("^%s+%[FEHLER%] (%S+)")
	if id and not EMU[id] then real[#real + 1] = line end
end
check(#real == 0, "keine FEHLER außer Nachbildung (" .. #real .. ")")
for _, l in ipairs(real) do print("  ->" .. l) end
check(text:find("Sandbox (echte Daten unverändert): OK", 1, true) ~= nil, "Sandbox OK")
check(not R.running, "R.running danach false (" .. waited .. " s)")
check(RM.db.data.players.Echt1 and RM.db.data.players.Echt1.d.mc == before.players, "echte DKP unverändert")
check(RM.db.prof == before.prof, "RM.db.prof gleiche Tabelle")
check(RM.db.testMode == nil and RaidMasterTestDB == nil, "Testmodus beendet")
local rc = 0
for k, v in pairs(REAL_CALLS) do rc = rc + v; print("  echt: " .. k .. " " .. v) end
check(rc == 0, "keine echte Aktion (Blizzard-Funktionen der Nachbildung)")
check(next(RM.API.over) == nil and next(RM.API.hide) == nil, "RM.API leer")
check(GAME_WINDOW_CALLS == 0, "Fehlerfenster des Spiels insgesamt 0 (" .. GAME_WINDOW_CALLS .. ")")
check(GAME_WINDOW_TESTERRORS == 0, "kein Fehlerfenster des Spiels durch absichtliche Testfehler (" .. GAME_WINDOW_TESTERRORS .. ")")
check(RaidMasterDB.routineGuard == nil, "Sicherung (routineGuard) nach dem Ende gelöscht")
print("ERRORS:", ERRORS or 0)
-- TR-ALLE Nachtrag D (3.0.31): Fenster-Schritte warten nie, werden vorgemerkt und beim nächsten Öffnen nachgeholt
if not only and not os.getenv("STOPAT") then
	local p = RaidMasterDB.routinePending
	check(RM.IsDev() == true, "Nachbildung im Entwicklermodus")
	check(text:find("T35b", 1, true) and text:find("wartet auf Fenster", 1, true) ~= nil, "Lauf ohne Berufsfenster: T35b 'wartet auf Fenster'")
	check(text:find("Noch offen: Berufe", 1, true) ~= nil, "Zusammenfassung nennt 'Noch offen: Berufe'")
	check(p and p.items and p.items.T35b == true, "T35b vorgemerkt")
	local reports = #RaidMasterDB.gsTest.reports
	-- im Kampf: nichts nachholen, bleibt vorgemerkt
	local oldCombat = InCombatLockdown
	InCombatLockdown = function() return true end
	Fire("TRADE_SKILL_SHOW"); Advance(0.5)
	RaidMasterDB.prof.Testa = { p = { Alchimie = { n = { "Trank" }, i = { 1 } } }, t = RM.Now() + 1 }
	Advance(3)
	InCombatLockdown = oldCombat
	check(RaidMasterDB.routinePending and RaidMasterDB.routinePending.items.T35b == true, "im Kampf nicht nachgeholt (bleibt vorgemerkt)")
	-- Fenster öffnen ausserhalb des Kampfs: läuft von selbst, eigener Bericht, Vormerkung weg
	Fire("TRADE_SKILL_SHOW"); Advance(0.5)
	RaidMasterDB.prof.Testa = { p = { Alchimie = { n = { "Trank", "Elixier" }, i = { 1, 2 } } }, t = RM.Now() + 1 }
	Advance(3)
	check(RaidMasterDB.routinePending == nil, "Berufsfenster geöffnet: nachgeholt, Vormerkung weg")
	check(#RaidMasterDB.gsTest.reports == math.min(reports + 1, GoldSentinelTest.MAX_REPORTS or 10), "eigener kleiner Bericht gespeichert")
	local last = RaidMasterDB.gsTest.reports[#RaidMasterDB.gsTest.reports] or ""
	check(last:find("GSTEST1", 1, true) == 1, "Bericht im GSTEST-Format")
	-- Verfall nach 7 Tagen (keine Sperre ohne Zeitlimit)
	RaidMasterDB.routinePending = { t = time() - 8 * 86400, items = { T35b = true }, clean = true }
	Fire("TRADE_SKILL_SHOW"); Advance(3)
	check(RaidMasterDB.routinePending == nil, "nach 7 Tagen verfallen")
	local n2 = #RaidMasterDB.gsTest.reports
	check(n2 == math.min(reports + 1, GoldSentinelTest.MAX_REPORTS or 10), "verfallen: kein weiterer Bericht")
end
-- Hinweis 17.11. 19:37: "/rmtest testroutine alles" und "/rm testroutine alles" müssen beide den ganzen Lauf starten
if not only and not os.getenv("STOPAT") then
	for _, cmd in ipairs({ { "RAIDMASTERTEST", "testroutine alles" }, { "RAIDMASTER", "testroutine alles" }, { "RAIDMASTERTEST", "testroutine Alles" } }) do
		local said = {}
		local oldSay = DEFAULT_CHAT_FRAME.AddMessage
		DEFAULT_CHAT_FRAME.AddMessage = function(self, m, ...) said[#said + 1] = tostring(m); return oldSay(self, m, ...) end
		SlashCmdList[cmd[1]](cmd[2])
		DEFAULT_CHAT_FRAME.AddMessage = oldSay
		local started = R.running and not R.only
		check(started and not table.concat(said, " "):find("gibt es nicht", 1, true), (cmd[1] == "RAIDMASTER" and "/rm " or "/rmtest ") .. cmd[2] .. " startet den ganzen Lauf")
		if R.running then SlashCmdList["RAIDMASTER"]("testroutine stop") end
		local w = 0
		while R.running and w < 60 do Advance(0.5); w = w + 0.5 end
		Advance(15)
	end
end
print(fails == 0 and "ALLE OK" or ("FEHLER: " .. fails))
if os.getenv("SHOWALL") then
	for _, e in ipairs(R.t.results) do print(string.format("%-6s %-8s %s %s", e.id, e.status, e.name, e.ergebnis and ("| " .. e.ergebnis) or "")) end
end
