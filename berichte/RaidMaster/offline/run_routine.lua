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
-- absichtliche Testfehler der Routine (T120, T122) nicht als Fehler zählen
local handler = function(e)
	if tostring(e):find("RaidMaster-Testfehler", 1, true) then print("absichtlicher Fehler: " .. tostring(e)) return end
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
-- Beute von Onyxia als bekannte Items (für den Durchlauf T43)
for key, list in pairs(RaidMasterTestLoot) do
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
check(RaidMasterDB.routineGuard == nil, "Sicherung (routineGuard) nach dem Ende gelöscht")
print("ERRORS:", ERRORS or 0)
print(fails == 0 and "ALLE OK" or ("FEHLER: " .. fails))
if os.getenv("SHOWALL") then
	for _, e in ipairs(R.t.results) do print(string.format("%-6s %-8s %s %s", e.id, e.status, e.name, e.ergebnis and ("| " .. e.ergebnis) or "")) end
end
