-- ============================================================================
-- RaidMaster – Testroutine ("Alles testen", /rmtest testroutine, /rm testroutine)
--
-- Nur für den Entwickler (RM.IsDev), wie das ganze Test-Werkzeug. Prüft RaidMaster automatisch und schreibt einen
-- Bericht über GoldSentinelTest (gemeinsame Datei): OK / FEHLER / ÜBERSPRUNGEN / IM CLIENT PRÜFEN.
-- Der Bericht landet im Kopierfenster und in RaidMasterDB.gsTest; der RaidMasterUploader schickt ihn beim nächsten
-- /reload oder Ausloggen an die Prüfung (Knopf "Neu laden und melden" im Berichtsfenster).
--
-- Regeln (auftraege/RaidMaster/testroutine-raidmaster.txt, nachtrag-testroutinen.txt, hinweis-neue-pruefregeln.txt):
--   * keine Blizzard-Funktion wird ersetzt – auch nicht vorübergehend. Ersetzt werden nur Felder von RaidMaster:
--     RM.Act.* (Spion: Aktionen mit Folgen werden nur gezählt), RM.API.over/hide (gefälschte bzw. "fehlende"
--     Spiel-Funktionen), RM.simCombat (Kampf), RM.IsSecret/GoldSentinelGame.IsSecret (Köder für geschützte Werte),
--     RM.Whisper, RM.BossBar.ReadTarget … Echte Aktionen werden zusätzlich über hooksecurefunc GEZÄHLT (T46b).
--   * echte Daten unverändert: Sicherung vorher, Tiefenvergleich nachher, bei Abweichung wiederherstellen.
--     Die Fachprüfungen laufen im Testmodus (Umleitung von Chat und Addon-Nachrichten); was der Testmodus nicht
--     sichert (Beute-Datenbank, Berufe, Rekorde …), stellt jeder Bereich selbst wieder her (KeepDB).
--   * asynchrone Prüfungen warten mit t:Wait(sek) (Koroutine, C_Timer.After). Gesamtgrenze 120 s (lang: 240 s);
--     wer sie überschreitet, ist ein FEHLER "hängt". Beginnt ein Kampf, bricht die Routine sofort ab.
-- Lädt vor Test\Test.lua (Test.lua muss die letzte Datei bleiben) und benutzt RM.Test erst beim Start.
-- ============================================================================

local ADDON, NS = ...
local RM = (type(NS) == "table" and NS.UI and NS) or RaidMaster
if not RM then return end

local R = { running = false }
RM.TestRoutine = R
R.LIMIT, R.LIMIT_LONG = 120, 240     -- Gesamtgrenze in Sekunden (normal / "lang")
R.GRACE = 10                         -- nach einem Abbruch: so lange werden Aktionen noch abgefangen

local AREAS = { A = "Laden und Erkennung", B = "Funktionen", C = "Forever-Sonderfälle", D = "Alte Clients", E = "Daten",
	F = "Sprachen", G = "Zusammenspiel", H = "Leistung", I = "Fehlerzählung", J = "Regressionstests",
	K = "Oberfläche im Client" }
local AREA_ORDER = { "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K" }

-- Teile von RaidMasterDB, die der Testmodus nicht sichert: jeder Bereich stellt sie selbst wieder her
local EXTRA_KEYS = { "foreign", "pendingAwards", "lootdb", "records", "killlog", "shots", "shotList", "prof", "bank",
	"itemTips", "recipeMats", "assign", "myAssign", "pug" }

local function pack(...) return { n = select("#", ...), ... } end

---------------------------------------------------------------------------
-- Echte Aktionen zählen (Sperrgitter T46b): nur mitzählen über hooksecurefunc, nie ersetzen
---------------------------------------------------------------------------
local realCount = {}
local hooked = false
local function HookActions()
	if hooked or type(hooksecurefunc) ~= "function" then return end
	hooked = true
	local function counter(name)
		return function() if R.running then realCount[name] = (realCount[name] or 0) + 1 end end
	end
	local globals = { "SendChatMessage", "SetRaidTarget", "InviteUnit", "ConvertToRaid", "SetRaidSubgroup", "SwapRaidSubgroup",
		"GiveMasterLoot", "DoReadyCheck", "Screenshot", "SetLootMethod", "InitiateTrade", "ClickTradeButton", "ReloadUI",
		"CastSpellByName", "NotifyInspect" }
	for _, n in ipairs(globals) do
		if type(_G[n]) == "function" then pcall(hooksecurefunc, n, counter(n)) end
	end
	local tables = {
		{ "C_PartyInfo", { "InviteUnit", "ConvertToRaid", "SetLootMethod", "DoCountdown" } },
		{ "C_ChatInfo", { "SendChatMessage" } },
		{ "C_TradeSkillUI", { "OpenTradeSkill" } },
	}
	for _, e in ipairs(tables) do
		local t = _G[e[1]]
		if type(t) == "table" then
			for _, n in ipairs(e[2]) do
				if type(t[n]) == "function" then pcall(hooksecurefunc, t, n, counter(e[1] .. "." .. n)) end
			end
		end
	end
end

local function RealTotal()
	local n, parts = 0, {}
	for k, v in pairs(realCount) do n = n + v; parts[#parts + 1] = k .. " " .. v end
	table.sort(parts)
	return n, table.concat(parts, ", ")
end

---------------------------------------------------------------------------
-- Spion auf RM.Act: während der Routine wird jede Aktion mit Folgen nur gezählt (nie ausgeführt).
-- R.actHook[name] kann eine Attrappe einhängen (z. B. OpenTradeSkill wirft, T150).
---------------------------------------------------------------------------
R.act, R.actHook, R.actUnits, R.allowed = {}, {}, {}, {}
local realAct

local function InstallSpies()
	realAct = {}
	R.act, R.actHook, R.actUnits, R.allowed = {}, {}, {}, {}
	for _, n in ipairs(RM.ACT_NAMES) do
		realAct[n] = RM.Act[n]
		RM.Act[n] = function(...)
			R.act[n] = (R.act[n] or 0) + 1
			if n == "SetRaidTarget" then
				local unit = ...
				R.actUnits[#R.actUnits + 1] = tostring(unit)
			end
			local h = R.actHook[n]
			if h then return h(...) end
		end
	end
end

local function RemoveSpies()
	if not realAct then return end
	for n, f in pairs(realAct) do RM.Act[n] = f end
end

local function SpiesRemoved()
	if not realAct then return true end
	for n, f in pairs(realAct) do if RM.Act[n] ~= f then return false end end
	return true
end

local function ActCount(name) return R.act[name] or 0 end

-- gezielt erlaubte Aufrufe (z. B. T10 "reset" -> ReloadUI über den Spion) zählen nicht als Verstoß
local function Allow(names, body)
	local before = {}
	for _, n in ipairs(names) do before[n] = ActCount(n) end
	local r = pack(body())
	for _, n in ipairs(names) do R.allowed[n] = (R.allowed[n] or 0) + ActCount(n) - before[n] end
	return unpack(r, 1, r.n)
end

---------------------------------------------------------------------------
-- Sandbox: echte SavedVariables sichern, vergleichen, wiederherstellen
---------------------------------------------------------------------------
local SB_SKIP = { gsTest = true, lastSave = true }

local function Deep(v, seen)
	if type(v) ~= "table" then return v end
	seen = seen or {}
	if seen[v] then return seen[v] end
	local c = {}
	seen[v] = c
	for k, x in pairs(v) do c[Deep(k, seen)] = Deep(x, seen) end
	return c
end

local function Diff(a, b, path, out)
	if #out >= 5 then return end
	if type(a) ~= type(b) then out[#out + 1] = path; return end
	if type(a) ~= "table" then
		if a ~= b then out[#out + 1] = path end
		return
	end
	for k, v in pairs(a) do
		if #out >= 5 then return end
		Diff(v, b[k], path .. "." .. tostring(k), out)
	end
	for k in pairs(b) do
		if #out >= 5 then return end
		if a[k] == nil then out[#out + 1] = path .. "." .. tostring(k) end
	end
end

-- Inhalt ersetzen, Tabelle behalten (ProfessionSentinel hält Verweise auf RaidMaster.db.prof)
local function Replace(target, source)
	for k in pairs(target) do target[k] = nil end
	for k, v in pairs(source) do target[k] = Deep(v) end
end

local function Snapshot()
	local db = RaidMasterDB
	local s = { db = {}, opts = Deep(RaidMasterTestOptions), testDBnil = RaidMasterTestDB == nil }
	for k, v in pairs(db or {}) do
		if not SB_SKIP[k] then s.db[k] = Deep(v) end
	end
	-- Fensterpositionen und Größe setzt das Test-Werkzeug bewusst nicht zurück
	if type(s.db.config) == "table" then s.db.config.positions, s.db.config.mainSize = nil, nil end
	return s
end

local function Compare(s)
	local db = RaidMasterDB or {}
	local cur = {}
	for k, v in pairs(db) do if not SB_SKIP[k] then cur[k] = v end end
	local out = {}
	for k, v in pairs(s.db) do
		if k == "config" and type(v) == "table" and type(cur.config) == "table" then
			local c = {}
			for ck, cv in pairs(cur.config) do if ck ~= "positions" and ck ~= "mainSize" then c[ck] = cv end end
			Diff(v, c, "config", out)
		else
			Diff(v, cur[k], tostring(k), out)
		end
	end
	for k in pairs(cur) do
		if s.db[k] == nil and #out < 5 then out[#out + 1] = tostring(k) end
	end
	return out
end

local function RestoreSnapshot(s)
	local db = RaidMasterDB
	if type(db) ~= "table" then return end
	for k in pairs(db) do
		if not SB_SKIP[k] and s.db[k] == nil then db[k] = nil end
	end
	for k, v in pairs(s.db) do
		if k == "config" and type(db.config) == "table" then
			local pos, size = db.config.positions, db.config.mainSize
			Replace(db.config, v)
			db.config.positions, db.config.mainSize = pos, size
		elseif type(v) == "table" and type(db[k]) == "table" then
			Replace(db[k], v)
		else
			db[k] = Deep(v)
		end
	end
end

---------------------------------------------------------------------------
-- Ablauf: Koroutinen statt pcall, damit Prüfungen warten können (Lua 5.1 kann nicht über pcall hinweg warten)
---------------------------------------------------------------------------
-- Körper in eigener Koroutine: Fehler werden wie mit pcall aufgefangen, Wartezeiten (t:Wait) an den Ablauf weitergereicht.
local function Run(body, ...)
	local co = coroutine.create(body)
	local res = pack(coroutine.resume(co, ...))
	while true do
		if not res[1] then return false, res[2] end
		if coroutine.status(co) == "dead" then return true, unpack(res, 2, res.n) end
		local back = pack(coroutine.yield(unpack(res, 2, res.n)))
		res = pack(coroutine.resume(co, unpack(back, 1, back.n)))
	end
end

-- Schutzblock: Körper ausführen, danach IMMER aufräumen, Fehler weitergeben
local function Guard(body, cleanup)
	local r = pack(Run(body))
	pcall(cleanup)
	if not r[1] then error(r[2], 0) end
	return unpack(r, 2, r.n)
end

-- Warten (nur im Ablauf der Routine, nicht innerhalb von t:Check – dort AsyncCheck benutzen)
local function Wait(sec)
	if not coroutine.running() then error("Wait außerhalb des Ablaufs der Routine", 2) end
	coroutine.yield("wait", tonumber(sec) or 0)
end

-- asynchrone Prüfung: der Körper darf warten; Ergebnis wie bei t:Check
-- Ein Fall darf "ASYNC_SKIP", Grund liefern: dann ehrlich übersprungen statt OK (ab 3.0.18, z. B. T43 ohne Beute)
local ASYNC_SKIP = {}
local function AsyncCheck(t, id, area, name, fn)
	R.current = id
	local r = pack(Run(fn))
	if r[1] and r[2] == ASYNC_SKIP then return t:Skip(id, area, name, tostring(r[3])) end
	return t:Check(id, area, name, function()
		if not r[1] then error(r[2], 0) end
		return unpack(r, 2, r.n)
	end)
end

-- Nachlauf: verzögerte Aktionen (C_Timer) müssen vor dem Ende der Routine durch sein
local function Settle(sec)
	R.settleUntil = math.max(R.settleUntil or 0, GetTime() + sec)
end

---------------------------------------------------------------------------
-- Hilfen für die Prüfungen
---------------------------------------------------------------------------
local function Swap(undo, tbl, key, value)
	undo[#undo + 1] = { tbl, key, tbl[key] }
	tbl[key] = value
end
local function Undo(undo)
	for i = #undo, 1, -1 do local e = undo[i]; e[1][e[2]] = e[3] end
	wipe(undo)
end

-- geschützter Wert: Köder des Test-Werkzeugs (RM.Test.MakeSecret) – RM.IsSecret und GoldSentinelGame.IsSecret werden im
-- Schutzblock umhüllt (beides Tabellenfelder, keine Blizzard-Funktionen)
local function WithSecret(body)
	local SECRET = RM.Test.MakeSecret()
	local u = {}
	local orig = RM.IsSecret
	Swap(u, RM, "IsSecret", function(v) return rawequal(v, SECRET) or orig(v) end)
	if RM.G and RM.G.IsSecret then
		local origG = RM.G.IsSecret
		Swap(u, RM.G, "IsSecret", function(v) return rawequal(v, SECRET) or origG(v) end)
	end
	return Guard(function() return body(SECRET) end, function() Undo(u) end)
end

-- Spiel-API fälschen bzw. "fehlen" lassen (nur RM.API.over/hide, eigene Tabellen)
local function WithAPI(over, hide, body)
	local A = RM.API
	for k, v in pairs(over or {}) do A.over[k] = v end
	for _, k in ipairs(hide or {}) do A.hide[k] = true end
	return Guard(body, function() wipe(A.over); wipe(A.hide) end)
end

-- Teile von RaidMasterDB nach dem Körper wiederherstellen (gleiche Tabellen, Inhalt ersetzt)
local function KeepDB(keys, body)
	local db = RM.db
	local saved = {}
	for _, k in ipairs(keys) do saved[k] = { had = db[k] ~= nil, tbl = db[k], copy = Deep(db[k]) } end
	return Guard(body, function()
		for _, k in ipairs(keys) do
			local s = saved[k]
			if not s.had then
				db[k] = nil
			elseif type(s.tbl) == "table" then
				db[k] = s.tbl
				Replace(s.tbl, s.copy)
			else
				db[k] = s.copy
			end
		end
	end)
end

-- alle Handler eines Ereignisses einzeln mit pcall aufrufen (nicht über geterrorhandler)
local function CallHandlers(event, ...)
	local list = RM.HandlersFor and RM.HandlersFor(event)
	if not list then return 0, nil end
	local errors, first = 0, nil
	for _, fn in ipairs(list) do
		local ok, err = pcall(fn, ...)
		if not ok then errors = errors + 1; first = first or tostring(err) end
	end
	return errors, first
end

-- simulierten Client einstellen und danach wieder echt
local function WithFlavor(flavor, body)
	local G = RM.G
	if not (G and G.SetTestFlavor) then return body() end
	return Guard(function()
		G.SetTestFlavor(flavor)
		RM.SetGameFlags()
		return body()
	end, function()
		G.SetTestFlavor(nil)
		RM.SetGameFlags()
	end)
end

-- Chatausgaben von RaidMaster mitlesen (RM.Print ist ein eigenes Feld)
local function WithPrints(body)
	local lines = {}
	local u = {}
	local orig = RM.Print
	Swap(u, RM, "Print", function(msg) lines[#lines + 1] = tostring(msg); return orig(msg) end)
	return Guard(function() return body(lines) end, function() Undo(u) end)
end
local function Printed(lines, text)
	for _, l in ipairs(lines) do if l:find(text, 1, true) then return true end end
	return false
end

-- Gegner/Einheiten für Markierungen nachstellen: units = { [unit] = { guid =, name =, icon = } }
local function FakeUnits(units)
	return {
		UnitExists = function(u) return units[u] ~= nil end,
		UnitIsPlayer = function() return false end,
		UnitIsDead = function() return false end,
		UnitCanAttack = function(_, u) return units[u] ~= nil end,
		UnitGUID = function(u) return units[u] and units[u].guid end,
		UnitName = function(u) return units[u] and units[u].name end,
		GetRaidTargetIndex = function(u) return units[u] and units[u].icon end,
		UnitCreatureType = function() return nil end,
	}
end

local function Count(t) local n = 0; for _ in pairs(t or {}) do n = n + 1 end; return n end
local function Ms() return debugprofilestop and debugprofilestop() or (GetTime() * 1000) end

local LINK_EPIC = "|cffa335ee|Hitem:16800::::::::60:::::|h[Testgegenstand]|h|r"
local LINK_STONE = "|cffffffff|Hitem:6948::::::::60:::::|h[Ruhestein]|h|r"

-- Testraid: 39 Testspieler, Ansicht Raidleiter
local function TestRaid()
	local T = RM.Test
	if not T.active then T.Start() end
	T.role = "raidlead"
	if T.RosterEmpty() then T.FillRoster() end
end

-- Versteigerung des Tests aufräumen
local function ClearAuction()
	local A = RM.Auction
	if A.current then pcall(A.Cancel) end
	A.current = nil
	wipe(A.queue)
	if A.HideAward then A.HideAward() end
	if A.HideBidFrame then pcall(A.HideBidFrame) end
end

-- Beute einer Raidtabelle beim Server anfragen (für T43: Items sollen geladen sein, wenn der Durchlauf beginnt)
local function Precache(poolKey)
	local def = RM.Data.Pools[poolKey]
	if not (def and RaidMasterTestLoot) then return end
	for k, v in pairs(def.ids or {}) do
		local id = (v == true) and k or v
		for key, list in pairs(RaidMasterTestLoot) do
			if tostring(key):match("^" .. tostring(id) .. ":") then
				for _, b in ipairs(list) do for _, iid in ipairs(b.i or {}) do pcall(RM.GetItemInfo, iid) end end
				for _, iid in ipairs(list.trash or {}) do pcall(RM.GetItemInfo, iid) end
			end
		end
	end
end

---------------------------------------------------------------------------
-- Fehlende Übersetzungen während der Routine sammeln (T90)
---------------------------------------------------------------------------
local missing
local function WatchLocale()
	missing = {}
	local mt = getmetatable(RM.L)
	if not mt then return function() end end
	local orig = mt.__index
	mt.__index = function(t, key)
		if missing and type(key) == "string" then missing[key] = true end
		if type(orig) == "function" then return orig(t, key) end
		if type(orig) == "table" then return orig[key] end
		return key
	end
	return function() mt.__index = orig end
end

---------------------------------------------------------------------------
-- A. Laden und Erkennung
---------------------------------------------------------------------------
local function AreaA(t, G)
	t:Check("T01", "A", "Alle Dateien geladen", function()
		local need = { "Data", "Comm", "Spec", "DKP", "Raid", "Loot", "Auction", "Signup", "PUG", "Ad", "Assign", "Markers",
			"Tranq", "Sheep", "Donate", "UI", "Guide", "Diag", "ItemTip", "BossBar", "Gaps", "LootDB", "Tooltip", "Ready",
			"Timer", "Prof", "Welcome", "Records", "Bank", "Test", "frame", "L", "LOCALE", "API", "Act" }
		local miss = {}
		for _, k in ipairs(need) do if RM[k] == nil then miss[#miss + 1] = k end end
		if RaidMaster ~= RM then miss[#miss + 1] = "RaidMaster" end
		if not RaidMasterTestLoot then miss[#miss + 1] = "RaidMasterTestLoot" end
		if not (RM.LANGUAGES and RM.LANGUAGES[RM.LOCALE]) then miss[#miss + 1] = "LANGUAGES[LOCALE]" end
		if #miss > 0 then return false, table.concat(miss, ", "), "alle vorhanden" end
	end)
	t:Check("T02", "A", "Version .toc = Code", function()
		local meta = (C_AddOns and C_AddOns.GetAddOnMetadata) or GetAddOnMetadata
		local toc = meta and meta("RaidMaster", "Version")
		local a, b, c = RM.VERSION:match("^(%d+)%.(%d+)%.(%d+)$")
		local num = tonumber(a) * 10000 + tonumber(b) * 100 + tonumber(c)
		if toc ~= RM.VERSION or num ~= RM.VERSION_NUM then
			return false, tostring(toc) .. " / " .. RM.VERSION .. " / " .. RM.VERSION_NUM, "gleich"
		end
		return true, RM.VERSION
	end)
	t:Check("T03", "A", "Gemeinsame Dateien", function()
		local GT = GoldSentinelTest
		local ok = G and (tonumber(G.version) or 0) >= 2 and RM.G == _G.GoldSentinelGame
			and GoldSentinelDev and (tonumber(GoldSentinelDev.version) or 0) >= 1
			and GT and (tonumber(GT.version) or 0) >= 1 and GT.registry and GT.registry.RaidMaster ~= nil
			and type(G.Status()) == "string"
		if not ok then return false, "Game " .. tostring(G and G.version) .. ", Dev " .. tostring(GoldSentinelDev and GoldSentinelDev.version)
			.. ", Test " .. tostring(GT and GT.version), "Game>=2, Dev>=1, Test>=1 mit RaidMaster" end
	end)
	t:Check("T04", "A", "Spielversion erkannt", function()
		RM.GameInfoText()
		if RM.GAME.key == "unknown" then return false, "unknown", "bekannte Version" end
		if G and G.flavor and RM.GAME.key ~= G.flavor then return false, RM.GAME.key, tostring(G.flavor) end
		return true, RM.GAME.key .. (RM.IsModern and " (modern)" or " (alte API)")
	end)
	t:Check("T05", "A", "Weichen für jeden Client simuliert", function()
		if not (G and G.SetTestFlavor) then return false, "G.SetTestFlavor fehlt", "vorhanden" end
		local before = { key = RM.GAME.key, modern = RM.IsModern, era = RM.IsClassicEra, flavor = G.flavor }
		local errs = {}
		local function expect(f, cond, what) if not cond then errs[#errs + 1] = f .. ": " .. what end end
		WithFlavor("forever", function()
			expect("forever", RM.GAME.key == "forever" and RM.IsForever and RM.IsModern and not RM.IsClassicEra and not RM.IsRetail, "Flaggen")
			expect("forever", RM.SameName("Testa Beispiel", "testa") and not RM.SameName("Testa Beispiel", "Testa Eisen"), "SameName")
			expect("forever", RM.Markers.CombatBlocked() == G.InCombat(), "CombatBlocked")
		end)
		WithFlavor("era", function()
			expect("era", RM.GAME.key == "era" and RM.IsClassicEra and not RM.IsModern, "Flaggen")
			expect("era", not RM.SameName("Testa Beispiel", "Testa"), "SameName")
			expect("era", RM.Markers.CombatBlocked() == false, "CombatBlocked")
		end)
		WithFlavor("tbc", function()
			expect("tbc", RM.GAME.key == "tbc" and not RM.IsModern and not RM.IsClassicEra, "Flaggen")
			expect("tbc", RM.Markers.CombatBlocked() == false, "CombatBlocked")
		end)
		WithFlavor("retail", function()
			expect("retail", RM.GAME.key == "retail" and RM.IsRetail and RM.IsModern, "Flaggen")
		end)
		expect("nil", RM.GAME.key == before.key and RM.IsModern == before.modern and RM.IsClassicEra == before.era, "nicht wie vorher")
		expect("nil", G.flavor == before.flavor, "Testflavor bleibt")
		if #errs > 0 then return false, table.concat(errs, "; "), "alle Weichen richtig" end
	end)
	t:Skip("T06", "A", "Fähigkeiten folgen der Weiche", "Caps nur beim Laden berechnet")
	t:Check("T07", "A", "Ladereihenfolge", function()
		if not (RM.Test.RealCaptured and RM.Test.RealCaptured()) then return false, "echte Funktionen nicht gemerkt", "Test.lua lädt zuletzt" end
	end)
	t:Check("T08", "A", "SavedVariables-Grundzustand", function()
		-- RaidMasterTestDB vor dem Start der Routine (währenddessen läuft der Testmodus)
		local ok = type(RaidMasterDB) == "table" and R.testDBnilBefore
			and (RaidMasterTestOptions == nil or type(RaidMasterTestOptions) == "table")
		if not ok then return false, "Absturzrest RaidMasterTestDB", "Tabelle, kein Absturzrest" end
		if RM.db.game and RM.db.game.key and RM.db.game.key ~= RM.GAME.key then return false, tostring(RM.db.game.key), RM.GAME.key end
	end)
	t:Check("T09", "A", "Diagnose zeigt Erkennung", function()
		local text = RM.Diag.Text()
		if G and not text:find(G.Status(), 1, true) then return false, "GoldSentinelGame-Zeile fehlt", "enthalten" end
		if GoldSentinelDev and GoldSentinelDev.Status and not text:find(GoldSentinelDev:Status(), 1, true) then
			return false, "GoldSentinelDev-Zeile fehlt", "enthalten"
		end
		for _, fn in ipairs(RM.Diag.providers) do
			local ok, lines = pcall(fn)
			if not ok or type(lines) ~= "table" then return false, "Provider liefert keine Tabelle", "Tabelle" end
		end
	end)
end

---------------------------------------------------------------------------
-- B. Jede Funktion (im Testmodus, Sperrgitter aktiv, Testdaten)
---------------------------------------------------------------------------
local function MainFrame() return _G["RaidMasterMainFrame"] end
local function Shown(f) return f and f.IsShown and f:IsShown() and true or false end

local function AreaB(t, G)
	local T = RM.Test
	local DKP = RM.DKP
	local UI = RM.UI
	Precache(R.long and "mc" or "ony")

	t:Check("T10", "B", "Slash /rm mit allen Unterbefehlen", function()
		local cfg = RM.db.config
		local pos = Deep(cfg.positions)
		local errs, first = 0, nil
		local cmds = { "", "", "bar", "bar", "adds", "clear", "sync", "test", "test", "beute", "beute ragnaros", "berufe",
			"handwerk arkanit", "rekorde", "bank", "bank arkanitbarren", "bereit", "pull 10", "pause 5", "luecken", "diag", "diag",
			"fix", "discord", "discord", "spenden", "minimap", "minimap", "version", "info", "unbekannt", "unbekannt" }
		local before = { ready = ActCount("DoReadyCheck"), cd = ActCount("DoCountdown"), reload = ActCount("ReloadUI"), chat = ActCount("SendChat") }
		Allow({ "OpenTradeSkill", "CastSpellByName", "SetRaidTarget" }, function()
			for _, c in ipairs(cmds) do
				local ok, err = pcall(SlashCmdList.RAIDMASTER, c)
				if not ok then errs = errs + 1; first = first or (c .. ": " .. tostring(err)) end
				if c == "pull 10" or c == "pause 5" then pcall(RM.Timer.Cancel) end
			end
		end)
		RM.Prof.pendingScan = nil
		if RM.Prof.scanned then wipe(RM.Prof.scanned) end
		Settle(6)
		-- "reset" nur mit Spion auf RM.Act.ReloadUI (läuft ohnehin) und gesicherten Positionen
		Allow({ "ReloadUI" }, function() pcall(SlashCmdList.RAIDMASTER, "reset") end)
		cfg.positions = pos
		local resetReload = ActCount("ReloadUI") - before.reload
		-- Fenster wieder zu
		if Shown(MainFrame()) then UI.Toggle() end
		if Shown(RM.Diag.window) then RM.Diag.Toggle() end
		if Shown(_G.RaidMasterGapsFrame) then _G.RaidMasterGapsFrame:Hide() end
		if RM.Donate.Hide then RM.Donate.Hide() end
		if Shown(_G.RaidMasterTestFrame) then T.Toggle() end
		if errs > 0 then return false, errs .. " Fehler, zuerst " .. first, "kein Lua-Fehler" end
		if ActCount("DoReadyCheck") ~= before.ready or ActCount("DoCountdown") ~= before.cd or ActCount("SendChat") ~= before.chat then
			return false, "Bereitschaft/Countdown/Chat ausgelöst", "0"
		end
		if resetReload ~= 1 then return false, "ReloadUI " .. resetReload, "1 (nur über den Spion)" end
		if Shown(MainFrame()) or Shown(RM.Diag.window) then return false, "Fenster offen geblieben", "alle zu" end
		return true, #cmds + 1 .. " Befehle"
	end)

	t:Check("T11", "B", "Slash /rmtest und Dev-Sperre", function()
		local u = {}
		return Guard(function()
			T.Slash("start")
			if not T.active then return false, "Testmodus aus", "an" end
			T.Slash("check")
			T.Slash("")
			local opened = Shown(_G.RaidMasterTestFrame)
			T.Slash("")
			T.Slash("stop")
			if T.active then return false, "stop beendet nicht", "Testmodus aus" end
			T.Start()
			if not T.active then return false, "Neustart des Testmodus", "an" end
			-- ohne Entwickler: laufender Testmodus lässt sich beenden; danach öffnet nichts, Hinweis von GoldSentinelDev
			local hints = 0
			local origReq = RM.RequireDev
			Swap(u, RM, "IsDev", function() return false end)
			Swap(u, RM, "RequireDev", function(...) hints = hints + 1; return origReq(...) end)
			T.Slash("stop")
			local stopped = not T.active
			if Shown(_G.RaidMasterTestFrame) then _G.RaidMasterTestFrame:Hide() end
			T.Slash("")
			T.Toggle()
			local openedNoDev = Shown(_G.RaidMasterTestFrame)
			Undo(u)
			T.Start()
			if not stopped then return false, "stop ohne Entwickler", "Testmodus aus" end
			if openedNoDev then return false, "Fenster ohne Entwickler offen", "zu" end
			if hints < 2 then return false, hints .. " Hinweise", "Hinweis von GoldSentinelDev (2x)" end
			return true, "Fenster " .. (opened and "öffnet" or "–") .. ", Sperre ok"
		end, function() Undo(u); if not T.active then T.Start() end end)
	end)

	t:Check("T12", "B", "Hauptfenster und alle Seiten je Ansicht", function()
		TestRaid()
		local pages = { "dkp", "auction", "loot", "log", "raid", "signup", "pug", "ad", "assign", "lgroups", "lboss", "specs",
			"settings", "bank", "discord" }
		local u = {}
		local errors, first = 0, nil
		local size = RM.db.config.mainSize
		local seen = {}
		local origReport = UI.ReportError
		return Guard(function()
			Swap(u, UI, "ReportError", function(err) errors = errors + 1; first = first or tostring(err); return origReport(err) end)
			UI.Open("dkp")
			for _, role in ipairs({ "member", "lead", "looter", "raidlead" }) do
				T.role = role
				seen[role] = {}
				for _, id in ipairs(pages) do
					if UI.CanSeePage(id) then
						seen[role][id] = true
						local ok, err = pcall(UI.ShowPage, id)
						if not ok then errors = errors + 1; first = first or (role .. "/" .. id .. ": " .. tostring(err)) end
						pcall(UI.RefreshCurrent)
					end
				end
			end
			if errors > 0 then return false, errors .. " Fehler, zuerst " .. tostring(first), "0" end
			for _, id in ipairs({ "settings", "assign", "signup" }) do
				if seen.member[id] then return false, "Mitglied sieht " .. id, "nicht sichtbar" end
			end
			return true, Count(seen.raidlead) .. " Seiten (Raidleiter), " .. Count(seen.member) .. " (Mitglied)"
		end, function()
			Undo(u)
			T.role = "raidlead"
			pcall(UI.ResetMainSize)
			RM.db.config.mainSize = size
			if Shown(MainFrame()) then UI.Toggle() end
		end)
	end)

	t:Check("T13", "B", "Jede Option einmal an und aus", function()
		local checks, cycles, bad = 0, 0, {}
		local function label(e) return tostring(e.label or (e.options and e.options[1] and e.options[1][2]) or "?"):sub(1, 40) end
		for _, e in ipairs(UI.registry or {}) do
			local ok, err = pcall(function()
				if e.kind == "check" then
					local v0 = e.getter() and true or false
					e.setter(not v0)
					local v1 = e.getter() and true or false
					e.setter(v0)
					local v2 = e.getter() and true or false
					checks = checks + 1
					if v1 == v0 or v2 ~= v0 then bad[#bad + 1] = label(e) end
				elseif e.kind == "cycle" then
					local v0 = e.getter()
					for _, o in ipairs(e.options or {}) do
						e.setter(o[1])
						if e.getter() ~= o[1] then bad[#bad + 1] = label(e) .. "=" .. tostring(o[1]); break end
					end
					e.setter(v0)
					if e.getter() ~= v0 then bad[#bad + 1] = label(e) .. " zurück" end
					cycles = cycles + 1
				end
				if e.frame and e.frame.Refresh then e.frame:Refresh() end
			end)
			if not ok then bad[#bad + 1] = label(e) .. ": " .. tostring(err) end
		end
		if checks + cycles == 0 then return false, "keine Optionen registriert", "> 0 (nach T12)" end
		if #bad > 0 then return false, #bad .. ": " .. table.concat(bad, " | "):sub(1, 250), "jede schaltet und kommt zurück" end
		return true, checks .. " Haken, " .. cycles .. " Auswahl"
	end)

	t:Check("T14", "B", "Nebenfenster und Esc", function()
		local errs = {}
		local function try(what, fn, ...)
			local ok, err = pcall(fn, ...)
			if not ok then errs[#errs + 1] = what .. ": " .. tostring(err) end
		end
		try("Diag", RM.Diag.Toggle); try("Diag zu", RM.Diag.Toggle)
		try("Gaps", RM.Gaps.Open)
		if _G.RaidMasterGapsFrame then _G.RaidMasterGapsFrame:Hide() end
		try("Guide", RM.Guide.Toggle); try("Guide zu", RM.Guide.Toggle)
		try("Spenden", RM.Donate.Show); try("Spenden zu", RM.Donate.Hide)
		try("Bereitschaft", RM.Ready.Show)
		if RM.Ready.window then RM.Ready.window:Hide() end
		try("Leiste", RM.Markers.ToggleBar); try("Leiste zurück", RM.Markers.ToggleBar)
		try("Minimap", UI.ToggleMinimapButton); try("Minimap zurück", UI.ToggleMinimapButton)
		try("Test", T.Toggle); try("Test zu", T.Toggle)
		try("Export", UI.ShowExport, "x")
		if _G.RaidMasterExport then _G.RaidMasterExport:Hide() end
		-- Abfrage: Abbrechen-Pfad (wie ein Klick auf "Abbrechen")
		local okCalled, cancelCalled = false, false
		try("Confirm", UI.Confirm, "x", function() okCalled = true end, function() cancelCalled = true end)
		local dlg = StaticPopupDialogs and StaticPopupDialogs["RAIDMASTER_CONFIRM"]
		if dlg and dlg.OnCancel then
			try("Abbrechen", dlg.OnCancel, { data = { ok = function() okCalled = true end, cancel = function() cancelCalled = true end } }, nil, "clicked")
		end
		if StaticPopup_Hide then pcall(StaticPopup_Hide, "RAIDMASTER_CONFIRM") end
		if #errs > 0 then return false, table.concat(errs, "; "):sub(1, 250), "kein Fehler" end
		if not cancelCalled or okCalled then return false, "Abbrechen-Pfad", "nur cancel" end
		local esc = {}
		for _, n in ipairs(UISpecialFrames or {}) do esc[n] = true end
		local miss = {}
		for _, n in ipairs({ "RaidMasterDiag", "RaidMasterDonate", "RaidMasterTestFrame", "RaidMasterMainFrame" }) do
			if not esc[n] then miss[#miss + 1] = n end
		end
		if #miss > 0 then return false, "Esc fehlt: " .. table.concat(miss, ", "), "alle in UISpecialFrames" end
		if RM.Donate.URL ~= "https://www.paypal.com/ncp/payment/46R68N2BF7BTY" then return false, "Link", "PayPal-Link exakt" end
	end)

	t:Check("T14b", "B", "Spenden-Knopf (aus dem Selbsttest)", function()
		local D = RM.Donate
		UI.Open("dkp")
		local mainF = MainFrame()
		local btn = mainF and mainF.donateButton
		return Guard(function()
			if D.URL ~= "https://www.paypal.com/ncp/payment/46R68N2BF7BTY" then return false, "Link falsch", "PayPal-Link exakt" end
			if not btn then return false, "Knopf fehlt in der Titelleiste", "Knopf" end
			local click = btn.GetScript and btn:GetScript("OnClick")
			if click then click(btn, "LeftButton") else btn:Click() end
			local f = D.Frame()
			if not (f and f:IsShown()) then return false, "Klick öffnet das Fenster nicht", "Fenster offen" end
			if f.edit:GetText() ~= D.URL then return false, "Feld enthält nicht genau den Link", "Link" end
			local esc = false
			for _, n in ipairs(UISpecialFrames or {}) do if n == "RaidMasterDonate" then esc = true end end
			if not esc then return false, "Esc schließt das Fenster nicht", "in UISpecialFrames" end
		end, function() D.Hide(); if Shown(MainFrame()) then UI.Toggle() end end)
	end)

	t:Check("T15", "B", "DKP Grundfunktionen (Testmodus)", function()
		local pool = T.pool or DKP.ActivePool()
		DKP.EnsurePlayer("Tank1", "WARRIOR")
		RM.db.data.players.Tank1.d[pool] = 100
		DKP.Adjust("Tank1", 50, "Test", pool)
		if DKP.Get("Tank1", pool) ~= 150 then return false, DKP.Get("Tank1", pool), 150 end
		local e = DKP.Adjust("Tank1", -20, "Test", pool)
		if DKP.Get("Tank1", pool) ~= 130 then return false, DKP.Get("Tank1", pool), 130 end
		DKP.Undo(e and e.id)
		if DKP.Get("Tank1", pool) ~= 150 then return false, DKP.Get("Tank1", pool), "150 nach Rückgängig" end
		DKP.ChargeItem("Tank1", 30, LINK_EPIC, pool)
		if DKP.Get("Tank1", pool) ~= 120 then return false, DKP.Get("Tank1", pool), 120 end
		local s = DKP.Summary("Tank1")
		if not s:find("120", 1, true) then return false, s, "enthält 120" end
		if not (DKP.PoolName("mc") and DKP.PoolShort("mc")) then return false, "PoolName/PoolShort", "Text" end
		local inList = false
		for _, k in ipairs(DKP.PoolList()) do if k == "mc" then inList = true end end
		if not inList then return false, "PoolList ohne mc", "mc enthalten" end
		local sorted = DKP.SortedPlayers(pool)
		for i = 2, #sorted do
			if sorted[i - 1].dkp < sorted[i].dkp then return false, "nicht absteigend", "absteigend" end
		end
		return true, "150/130/150/120"
	end)

	t:Check("T16", "B", "Verfall, Ersatzbank, Twinks", function()
		TestRaid()
		local pool = T.pool or DKP.ActivePool()
		local s = RM.db.data.settings
		s.decayPct = 10
		local p = DKP.EnsurePlayer("Krieger1", "WARRIOR")
		p.d[pool] = 100
		DKP.ApplyDecay(pool)
		if DKP.Get("Krieger1", pool) ~= 90 then return false, "Verfall " .. tostring(DKP.Get("Krieger1", pool)), 90 end
		local ws, nd = DKP.WeekStart(), DKP.NextDecay()
		if nd - ws ~= 7 * 86400 or nd <= RM.Now() or ws > RM.Now() then return false, "WeekStart/NextDecay", "Woche, nächster Reset in der Zukunft" end
		-- im Testmodus gesperrt (DKP.lua: kein automatischer Verfall auf Testdaten)
		local logN = #RM.db.data.log
		if DKP.CheckAutoDecay() or DKP.CheckAutoDecay() or #RM.db.data.log ~= logN then return false, "Auto-Verfall im Testmodus", "gesperrt" end
		local sb = DKP.IsStandby("Ersatz1")
		DKP.ToggleStandby("Ersatz1"); DKP.ToggleStandby("Ersatz1")
		if DKP.IsStandby("Ersatz1") ~= sb then return false, "Ersatzbank umschalten", "zweimal = wie vorher" end
		RM.db.config.standby.Ersatz1 = true
		local e1 = DKP.Get("Ersatz1", pool)
		local _, n, amount = DKP.AwardStandby(pool)
		if not n or n < 1 or DKP.Get("Ersatz1", pool) ~= e1 + (tonumber(s.standbyStartDKP) or 10) then
			return false, "Ersatzbank " .. tostring(n) .. " / " .. tostring(DKP.Get("Ersatz1", pool) - e1), "+" .. tostring(amount)
		end
		if not DKP.SetMain("Twinky", "Tank1", true) then return false, "SetMain", "true" end
		local ok = DKP.IsTwink("Twinky") and DKP.MainOf("Twinky") == "Tank1"
		local tw = DKP.TwinksOf("Tank1")
		DKP.SetMain("Twinky", nil, true)
		if not ok or tw[1] ~= "Twinky" then return false, "Twink-Verknüpfung", "Twinky -> Tank1" end
		if DKP.IsTwink("Twinky") then return false, "Verknüpfung nicht gelöst", "gelöst" end
	end)

	t:Check("T17", "B", "Snapshot, Export, Abgleich", function()
		return KeepDB({ "foreign" }, function()
			local u = {}
			return Guard(function()
				local s = DKP.MakeSnapshot(50)
				local copy = { players = {}, log = {}, settings = {} }
				DKP.ImportSnapshotTo(copy, s, false)
				local diff = {}
				Diff(RM.db.data.players, copy.players, "players", diff)
				if #diff > 0 or copy.version ~= RM.db.data.version then return false, "Kopie weicht ab: " .. table.concat(diff, ","), "gleiche Spieler und DKP" end
				local text = DKP.ExportText()
				if not text:find("Tank1", 1, true) or not text:find(RM.L["RaidMaster DKP-Export "], 1, true) then
					return false, "Export ohne Kopf/Tank1", "enthalten"
				end
				Swap(u, RM.UI, "viewGuild", RM.UI.viewGuild)
				s.g = "Testgilde"
				DKP.ImportForeign(s, "Fremd")
				if not (RM.db.foreign and RM.db.foreign.Testgilde) then return false, "foreign fehlt", "Datensatz der Testgilde" end
			end, function() Undo(u) end)
		end)
	end)

	t:Check("T18", "B", "Raid starten, Bosskill, beenden, Pause", function()
		TestRaid()
		local s = RM.db.data.settings
		if RM.db.session.active then T.runEnding = true; pcall(RM.Raid.End); T.runEnding = nil end
		local pool = RM.DKP.CurrentInstancePool() or RM.db.config.activePool or "mc"
		local chat = ActCount("SendChat")
		local d0 = DKP.Get("Tank1", pool)
		T.manualStart = true
		local ok, err = pcall(RM.Raid.Start)
		T.manualStart = nil
		Settle(7)
		if not ok then error(err, 0) end
		if not RM.db.session.active then return false, "Sitzung nicht aktiv", "aktiv" end
		pool = RM.db.session.pool
		local d1 = DKP.Get("Tank1", pool)
		if d1 - d0 ~= (s.dkpStart or 0) then return false, "Start " .. (d1 - d0), s.dkpStart end
		local boss = RM.Data.Bosses[663]
		local first = not RM.db.data.firstKills[663]
		local amount = s.bossDKP[663] or (boss and boss.dkp) or s.defaultBossDKP or 0
		if first and s.firstKillDouble then amount = amount * 2 end
		RM.db.session.kills[663] = nil
		local bpool = (boss and boss.pool) or pool
		local b0 = DKP.Get("Tank1", bpool)
		RM.SimulateEvent("ENCOUNTER_END", 663, "Lucifron", 9, 40, 1)
		local d2 = DKP.Get("Tank1", bpool)
		local got = d2 - b0
		RM.SimulateEvent("ENCOUNTER_END", 664, "Magmadar", 9, 40, 0)
		RM.Loot.pendingBoss = nil          -- keine Plünder-Erinnerung für den Testboss
		local d3 = DKP.Get("Tank1", bpool)
		T.runEnding = true
		local okE, errE = pcall(RM.Raid.End)
		T.runEnding = nil
		if not okE then error(errE, 0) end
		local d4 = DKP.Get("Tank1", RM.db.session.lastPool or pool)
		if RM.db.session.active then return false, "Sitzung läuft noch", "beendet" end
		if got ~= amount then return false, "Boss " .. got, amount end
		if d3 ~= d2 then return false, "Fehlversuch gebucht", "keine DKP" end
		if d4 - d3 ~= (s.dkpEnd or 0) then return false, "Ende " .. (d4 - d3), s.dkpEnd end
		RM.Raid.StartPause(60); RM.Raid.StopPause(true)
		RM.Raid.RunCheck()
		RM.Raid.AnnounceSkinners()
		if ActCount("SendChat") ~= chat then return false, "echte Chatnachricht", "nur Testanzeige" end
		return true, string.format("Tank1 %d -> %d (Start +%d, Boss +%d, Ende +%d)", d0, d4, d1 - d0, amount, d4 - d3)
	end)

	-- T19: Versteigerung mit echter Wartezeit (Ablauf über den Ticker von RaidMaster)
	AsyncCheck(t, "T19", "B", "Versteigerung Ablauf", function()
		TestRaid()
		ClearAuction()
		local A = RM.Auction
		local pool = DKP.ActivePool()
		local before = DKP.Get("Tank1", pool)
		local logN = #RM.db.data.log
		A.Enqueue(LINK_STONE)
		A.Start(1)
		if not A.current then return false, "Versteigerung startet nicht", "läuft" end
		local ok1 = A.ReceiveBid("Tank1", 10)
		local ok2 = A.ReceiveBid("Krieger1", 15)
		local ok3 = A.ReceiveBid("Tank1", 20)
		if not (ok1 and ok2 and ok3) then return false, "Gebote abgelehnt", "10/15/20 angenommen" end
		A.BidList()
		Wait((A.current.endsAt - GetTime()) + 1)
		if not A.AwaitingAward() then return false, "nach Ablauf nicht beendet", "wartet auf Vergabe" end
		if A.current.highName ~= "Tank1" or A.current.high ~= 20 then return false, tostring(A.current.highName) .. " " .. tostring(A.current.high), "Tank1 20" end
		A.Award()
		if DKP.Get("Tank1", pool) ~= before - 20 then return false, "DKP " .. (DKP.Get("Tank1", pool) - before), -20 end
		if #RM.db.data.log <= logN then return false, "kein Log-Eintrag", "Eintrag" end
		-- zweite Runde: nicht vergeben
		A.Start(LINK_STONE)
		A.ReceiveBid("Krieger1", 10)
		A.FinishNow()
		A.NoAward()
		if A.current then return false, "NoAward", "current nil" end
		-- dritte Runde: abbrechen, Zeit, entfernen
		A.Start(LINK_STONE)
		A.AddTime(5)
		A.Cancel()
		if A.queue[1] == nil then return false, "abgebrochenes Item nicht in der Warteschlange", "vorne in der Schlange" end
		A.Remove(1)
		A.SendQueue()
		-- Gebotsfenster der Spieler
		A.OnStart("Tank1", { a = "test-aid", l = LINK_STONE, m = 10, i = 5, d = 3, p = pool, pn = DKP.PoolName(pool) })
		if A.UpdateBidFrame then A.UpdateBidFrame() end
		if A.HideBidFrame then A.HideBidFrame() end
		A.client = nil
		if #A.queue ~= 0 or A.current ~= nil then return false, "Schlange/current übrig", "leer" end
		return true, "Tank1 zu 20"
	end)
	ClearAuction()

	t:Check("T20", "B", "Versteigerung Regeln", function()
		TestRaid()
		ClearAuction()
		local A = RM.Auction
		local s = RM.db.data.settings
		local u = {}
		return Guard(function()
			Swap(u, s, "minBid", 10); Swap(u, s, "bidIncrement", 5); Swap(u, s, "allowNegative", false); Swap(u, s, "mainBeforeTwink", true)
			T.ApplySpeed()
			if s.antiSnipe ~= false then return false, "antiSnipe im Test an", "aus" end
			A.Start(LINK_STONE)
			if A.ReceiveBid("Krieger2", 5) then return false, "Gebot 5 angenommen", "abgelehnt" end
			if not A.ReceiveBid("Krieger2", 10) then return false, "Gebot 10 abgelehnt", "angenommen" end
			local okLow, errLow = A.ReceiveBid("Krieger3", 12)
			if okLow or type(errLow) ~= "string" then return false, "Gebot 12 nach 10", "abgelehnt mit Text" end
			if not A.ReceiveBid("Krieger3", 15) then return false, "Gebot 15", "angenommen" end
			if A.ReceiveBid("Krieger4", 5000) then return false, "Gebot über DKP angenommen", "abgelehnt" end
			ClearAuction()
			-- Main vor Twink
			DKP.SetMain("Schurke1", "Schurke2", true)
			A.Start(LINK_STONE)
			if not A.ReceiveBid("Schurke1", 30) then return false, "Twink-Gebot", "angenommen" end
			if not A.ReceiveBid("Schurke2", 15) then return false, "Main 15 nach Twink 30", "angenommen" end
			if A.ReceiveBid("Schurke1", 40) then return false, "Twink nach Main", "abgelehnt" end
			local c = A.current
			T.ShortenRest(c)
			if c.endsAt - GetTime() > (T.REST_AFTER_BIDS or 1) + 0.05 then return false, "Restzeit " .. (c.endsAt - GetTime()), "<= 1 s" end
			A.FinishNow()
			if c.highName ~= "Schurke2" then return false, tostring(c.highName), "Schurke2 (Main)" end
			A.CancelAward()
		end, function()
			Undo(u)
			DKP.SetMain("Schurke1", nil, true)
			ClearAuction()
		end)
	end)

	t:Check("T21", "B", "Loot-Regeln und Verteilung", function()
		TestRaid()
		local L = RM.Loot
		local cfg = RM.db.config
		local rules = cfg.rules
		local u = {}
		local give, trade = ActCount("GiveMasterLoot"), ActCount("ClickTradeButton")
		return Guard(function()
			local function classOf(link) return select(6, RM.GetItemInfoInstant(link)) end
			local checks = {
				{ "|cffa335ee|Hitem:16800::::::::60:::::|h[Episch]|h|r", 4, rules.epic },
				{ "|cffff8000|Hitem:18563::::::::60:::::|h[Legendär]|h|r", 5, "notify" },
				{ "|cff0070dd|Hitem:17010::::::::60:::::|h[Material]|h|r", 3, rules.mats },
				{ "|cff0070dd|Hitem:18257::::::::60:::::|h[Rezept]|h|r", 3, rules.recipe },
				{ "|cff0070dd|Hitem:13965::::::::60:::::|h[Blau]|h|r", 3, rules.blue },
			}
			local skipped = 0
			for _, c in ipairs(checks) do
				if classOf(c[1]) == nil and c[2] < 5 then
					skipped = skipped + 1          -- Item dem Client unbekannt: Klasse nicht prüfbar
				else
					local got = L.Classify(c[1], c[2])
					if got ~= c[3] then return false, "Item " .. RM.ItemID(c[1]) .. ": " .. tostring(got), c[3] end
				end
			end
			if L.Classify("|cffffffff|Hitem:6948::::::::60:::::|h[x]|h|r", 1) ~= "manual" then return false, "einfaches Item", "manual" end
			if L.RecipientFor("bank") ~= cfg.bankChar or L.RecipientFor("de") ~= cfg.deChar or L.RecipientFor("crafter") ~= cfg.crafterChar then
				return false, "RecipientFor", "Namen aus den Einstellungen"
			end
			-- Testmodus: Deliver nur im Protokoll
			if L.Deliver == T.Real("Deliver") then return false, "Deliver nicht umgeleitet", "Testmodus-Ersatz" end
			L.Deliver(LINK_EPIC, "Tank1")
			-- ohne Plündermeister: Handelsliste (echte Funktion, Caps simuliert)
			local tn = #RM.db.trade
			Swap(u, RM.Caps, "masterLoot", false)
			T.Real("Deliver")(LINK_EPIC, "Tank1")
			if #RM.db.trade ~= tn + 1 then return false, "keine Handelsliste", "AddTrade" end
			L.RemoveTrade(#RM.db.trade)
			Undo(u)
			if type(L.Problems()) ~= "table" then return false, "Problems", "Liste" end
			L.ApplySettings()
			L.EnsureSettings(); L.Warn(true)
			L.ExplainNoQueue()
			L.OnBossKilled("Lucifron")
			L.pendingBoss = nil
			Settle(2)
			if ActCount("GiveMasterLoot") ~= give or ActCount("ClickTradeButton") ~= trade then return false, "echte Verteilung", "0" end
			return true, skipped > 0 and (skipped .. " Items dem Client unbekannt") or nil
		end, function() Undo(u) end)
	end)

	t:Check("T22", "B", "Anmeldungen importieren (Parse)", function()
		local text = table.concat({ "RAIDMASTER-ANMELDUNG", "Raid: MC", "Datum: 05.11.", "Modus: dkp", "Topf: mc", "Max: 40",
			"Start: 1793901600", "Tank1;WARRIOR;Tank;angemeldet", "Testa Beispiel;PRIEST;Heal;angemeldet",
			"Ersatz1;WARRIOR;DD;ersatz", "GRP;Tank1;1", "BANK;Ersatz1", "ALT;Twinky;Tank1" }, "\n")
		local r = RM.Signup.Parse(text)
		if not r then return false, "nil", "Ergebnis" end
		if #r.list ~= 3 then return false, #r.list .. " Einträge", 3 end
		if r.list[2].name ~= "Testa Beispiel" then return false, tostring(r.list[2].name), "Testa Beispiel" end
		if r.pool ~= "mc" or r.max ~= 40 or r.start ~= 1793901600 then return false, tostring(r.pool) .. "/" .. tostring(r.max), "mc/40/Start" end
		if not (r.groups and r.groups.Tank1 == 1 and r.bench and r.bench.Ersatz1 and r.alts and r.alts.Twinky == "Tank1") then
			return false, "GRP/BANK/ALT fehlen", "vorhanden"
		end
		local none, err = RM.Signup.Parse("Hallo")
		if none ~= nil or type(err) ~= "string" then return false, "kein Fehlertext", "nil + Fehlertext" end
	end)

	-- T23: Einladen (simuliert, mit Wartezeit)
	AsyncCheck(t, "T23", "B", "Einladen und Gruppen (simuliert)", function()
		local S = RM.Signup
		local spy = { inv = ActCount("InviteUnit"), conv = ActCount("ConvertToRaid"), set = ActCount("SetRaidSubgroup"), swap = ActCount("SwapRaidSubgroup") }
		local lines = { "RAIDMASTER-ANMELDUNG", "Raid: MC", "Topf: mc", "Max: 40" }
		local names = { "Tank1", "Tank2", "Priester1", "Priester2", "Magier1", "Schurke1", "Jäger1" }
		for i, n in ipairs(names) do
			lines[#lines + 1] = n .. ";WARRIOR;DD;angemeldet"
			lines[#lines + 1] = "GRP;" .. n .. ";" .. (1 + i % 3)
		end
		S.Import(table.concat(lines, "\n"))
		if not RM.db.signup then return false, "Import", "Anmeldungen" end
		T.UseSignupRoster()
		local n = S.InviteAll(false)
		Wait(#names * 0.6 + 4)
		local states = 0
		for _, nm in ipairs(names) do if S.InviteState(nm) or RM.IsInMyRaid(nm) then states = states + 1 end end
		local size, have, cap = S.RaidSize(), S.MemberCount(), S.Capacity()
		if type(S.CapacityText()) ~= "string" or type(size) ~= "number" or type(have) ~= "number" or type(cap) ~= "number" then
			return false, "RaidSize/MemberCount/Capacity", "Zahlen"
		end
		S.ArrangeGroups()
		S.StopInvites()
		local players = {}
		for i = 1, 40 do players[i] = { name = "Spieler" .. i, class = ({ "WARRIOR", "PRIEST", "MAGE", "ROGUE" })[i % 4 + 1], role = "melee" } end
		local groups = S.ClassicGroups(players)
		for _, g in ipairs(groups) do if #g > 5 then return false, "Gruppe mit " .. #g, "<= 5" end end
		if #groups > 8 then return false, #groups .. " Gruppen", "<= 8" end
		S.MainTanks()
		if ActCount("InviteUnit") ~= spy.inv or ActCount("ConvertToRaid") ~= spy.conv or ActCount("SetRaidSubgroup") ~= spy.set
			or ActCount("SwapRaidSubgroup") ~= spy.swap then
			return false, "echte Einladung/Gruppe", "0"
		end
		if states == 0 then return false, "keine Einladung beantwortet", "eingeladen/abgelehnt/nicht gefunden" end
		return true, string.format("%s eingeladen, %d mit Status, Raid %d/%d", tostring(n), states, have, size)
	end)
	RM.Signup.StopInvites()
	RM.Test.FillRoster()

	t:Check("T24", "B", "PUG und Werbung", function()
		TestRaid()
		local P, Ad = RM.PUG, RM.Ad
		local chat = ActCount("SendChat")
		local u = {}
		return KeepDB({ "pug" }, function()
			return Guard(function()
				P.Start("Test-MC")
				if not P.IsActive() then return false, "PUG nicht aktiv", "aktiv" end
				P.SoftresLink()
				P.AnnounceSoftres(false)
				P.Stop()
				local text = Ad.Build()
				if type(text) ~= "string" or #text > 255 then return false, "Werbetext " .. tostring(text and #text), "<= 255 Zeichen" end
				Swap(u, Ad, "lastPost", 0)
				if not Ad.SimulatePost then return false, "Werbung nicht simuliert", "Testmodus-Ersatz" end
				Ad.Post()
				if Ad.CooldownLeft() <= 0 then return false, "keine Wartezeit", "> 0" end
				Ad.Targets(); Ad.DefaultTarget(); Ad.TargetLabel(Ad.Target())
				RM.Signup.inviteState.Kaldor12 = nil
				RM.Test.ClearRoster()            -- volle Gruppe lädt niemanden ein
				local e, f = CallHandlers("CHAT_MSG_WHISPER", "inv", "Kaldor12")
				RM.Test.FillRoster()
				if e > 0 then return false, f, "kein Fehler" end
				if not (RM.Signup.InviteState("Kaldor12") or RM.IsInMyRaid("Kaldor12")) then return false, "Kaldor12 nicht eingeladen", "SimInvite" end
				Settle(9)
				if ActCount("SendChat") ~= chat then return false, "echte Chatnachricht", "0" end
			end, function() Undo(u) end)
		end)
	end)

	t:Check("T25", "B", "Einteilung", function()
		TestRaid()
		local A = RM.Assign
		local chat = ActCount("SendChat")
		return KeepDB({ "assign", "myAssign" }, function()
			local built = {}
			for _, p in ipairs({ "mc", "ony", "barrow", "hyjal" }) do
				local store = A.Build(p)
				if not (store and store.ctx and store.ctx.general and #(store.ctx.general.lines or {}) > 0) then
					return false, "Einteilung " .. p .. " leer", "Kontexte mit Zeilen"
				end
				built[#built + 1] = p .. " " .. Count(store.ctx)
			end
			if #A.AutoTanks() == 0 then return false, "keine Tanks", "MT/OT aus AutoTanks" end
			A.Build("mc")
			A.Post("general")
			if type(A.PersonalTexts("Priester1")) ~= "table" then return false, "PersonalTexts", "Tabelle" end
			-- An alle senden: nur ein kleiner Testraid, damit die verzögerten Flüsternachrichten im Testmodus bleiben
			local T = RM.Test
			local roster = T.roster
			T.roster = { { name = "Priester1", class = "PRIEST", group = 1 }, { name = "Tank1", class = "WARRIOR", group = 1 } }
			local ok, err = pcall(A.SendAll)
			T.roster = roster
			if not ok then error(err, 0) end
			Settle(3)
			A.Receive({ general = "Test" })
			if not A.ContextForEncounter(663) then return false, "ContextForEncounter(663)", "Lucifron" end
			if ActCount("SendChat") ~= chat then return false, "echte Flüsternachricht", "0" end
			return true, table.concat(built, ", ")
		end)
	end)

	AsyncCheck(t, "T26", "B", "Markierungen ohne echte Symbole", function()
		TestRaid()
		local M = RM.Markers
		local n0, units0 = ActCount("SetRaidTarget"), #R.actUnits
		local units = {
			mouseover = { guid = "Creature-0-1-2-3-11111-0000000001", name = "Testgegner A" },
			nameplate1 = { guid = "Creature-0-1-2-3-11111-0000000002", name = "Testgegner B" },
			nameplate2 = { guid = "Creature-0-1-2-3-11111-0000000003", name = "Testgegner C" },
		}
		local cfg = RM.db.config
		local tpl = cfg.markerTemplate
		cfg.markerTemplate = "standard"          -- Vorlage ohne NPC-Filter (Testmodus-Einstellung)
		-- Weg der alten Clients (Aufrufe über RM.Act, abgefangen); WoW Forever prüft T161
		local secWas = M.simSecure
		M.simSecure = false
		return Guard(function() return Allow({ "SetRaidTarget" }, function()
			return WithAPI(FakeUnits(units), nil, function()
				if not (M.IsMarkerLead() and M.CanMark()) then return false, "keine Markierrechte im Test", "Raidleiter" end
				M.ResetUsed()
				M.Mark(8)
				M.SmartMark()
				M.MarkAdds()
				M.ClearAll()
				Wait(1.6)
				M.ResetUsed(); M.UpdateBar()
				M.PostBossInfo(663)
				Settle(3)
				local onPlayer, bad = 0, {}
				for i = units0 + 1, #R.actUnits do
					local un = R.actUnits[i]
					if un == "player" then onPlayer = onPlayer + 1
					elseif not units[un] then bad[#bad + 1] = un end
				end
				if #bad > 0 then return false, "fremde Einheiten: " .. table.concat(bad, ","), "nur Testeinheiten" end
				if onPlayer ~= 9 then return false, "ClearAll " .. onPlayer, "8 + 1 auf player" end
				cfg.markerTemplate = tpl
				return true, (ActCount("SetRaidTarget") - n0) .. " Aufrufe über RM.Act (gezählt, nicht ausgeführt)"
			end)
		end) end, function() M.simSecure = secWas; cfg.markerTemplate = tpl end)
	end)

	t:Check("T27", "B", "Boss-Leiste", function()
		TestRaid()
		local B = RM.BossBar
		local mark, chat = ActCount("SetRaidTarget"), ActCount("SendChat")
		return Guard(function()
			B.SetTestTarget(663)
			if B.current ~= 663 then return false, "Leiste nicht da", "Boss 663" end
			local boss = B.TargetBoss()
			if not boss or boss.id ~= 663 then return false, "TargetBoss", 663 end
			B.Announce()
			B.AnnounceAndMark()
			B.PostAssignment()
			Settle(3)
			B.SetTestTarget(nil)
			if B.current ~= nil then return false, "Leiste bleibt", "weg" end
			if ActCount("SetRaidTarget") ~= mark or ActCount("SendChat") ~= chat then return false, "echte Aktion", "0" end
		end, function() B.SetTestTarget(nil) end)
	end)

	AsyncCheck(t, "T28", "B", "Einlull- und Schaf-Rotation", function()
		TestRaid()
		local Q = RM.Tranq
		T.TranqTest()
		Wait(6)
		Settle(3)
		local okA = Q.answers["Jäger1"] == true and Q.answers["Jäger2"] == true and Q.answers["Jägerin"] == false
		local status = Q.StatusText()
		local okS = status:find("✔|r Jäger1", 1, true) and status:find("✔|r Jäger2", 1, true) and status:find("✘|r Jägerin", 1, true)
		local inRot = {}
		for _, h in ipairs((Q.Rotation())) do inRot[h] = true end
		local Sh = RM.Sheep
		Sh.Mages(); Sh.Rotation(); Sh.Line(); Sh.StatusText(); Sh.Post()
		wipe(Q.answers); wipe(Q.asked); Q.running = false
		if not okA then return false, "Antworten falsch zugeordnet", "Jäger1/Jäger2 ja, Jägerin nein" end
		if not okS then return false, "Statustext", "2x ja (Jäger1, Jäger2), 1x nein (Jägerin)" end
		if not (inRot["Jäger1"] and inRot["Jäger2"]) or inRot["Jägerin"] then return false, "Rotation", "Jäger1, Jäger2 ohne Jägerin" end
	end)

	AsyncCheck(t, "T29", "B", "Lücken füllen", function()
		local Gp, S, Ad = RM.Gaps, RM.Signup, RM.Ad
		local T = RM.Test
		T.ClearRoster()
		local u = {}
		return Guard(function()
			if Gp.RoleHint("inv heal") ~= "heal" or Gp.RoleHint("inv tank") ~= "tank" then return false, "RoleHint", "heal/tank" end
			for _, size in ipairs({ 10, 20, 40 }) do
				if type(Gp.Requirement("mc", size)) ~= "table" then return false, "Requirement " .. size, "Tabelle" end
			end
			if not Gp.CanDo("PRIEST", "heal") or Gp.CanDo("ROGUE", "heal") then return false, "CanDo", "Priester heilt, Schurke nicht" end
			Gp.RoleOf("Tank1", "WARRIOR")
			local plan = Gp.Plan()
			Gp.NeedsText(plan.search)
			local needs = Deep(plan.search)
			if #needs == 0 then return false, "leerer Raid ohne Bedarf", "Bedarf" end
			Gp.AskGuild(plan)
			Swap(u, Ad, "lastPost", 0)
			if not Gp.PostSearch(plan) then return false, "Gruppensuche nicht gepostet", "gepostet (simuliert)" end
			Gp.OnWhisper("inv tank", "Grumbash11")
			Wait(11.5)
			local invited, wrong, answered = 0, {}, 0
			for name, class in pairs(Gp.knownClass) do
				if name:match("%d%d$") then
					if Gp.answered[name] then answered = answered + 1 end
					if S.InviteState(name) or S.IsQueued(name) or RM.IsInMyRaid(name) then
						invited = invited + 1
						local fits = false
						for _, n in ipairs(needs) do if not n.classes or n.classes[class] then fits = true end end
						if not fits then wrong[#wrong + 1] = class end
					end
				end
			end
			Gp.StopSearch()
			S.StopInvites()
			Gp.Open(); Gp.Refresh()
			if _G.RaidMasterGapsFrame then _G.RaidMasterGapsFrame:Hide() end
			if #wrong > 0 then return false, "unpassend eingeladen: " .. table.concat(wrong, ","), "nur passende Klassen" end
			if invited == 0 then return false, "niemand eingeladen", "passende Fremde eingeladen" end
			return true, string.format("%d Fremde geantwortet, %d eingeladen", answered, invited)
		end, function() Undo(u); Gp.StopSearch(); S.StopInvites() end)
	end)
	RM.Test.FillRoster()

	AsyncCheck(t, "T30", "B", "Bereitschafts-Check", function()
		TestRaid()
		local Rd = RM.Ready
		local rc = ActCount("DoReadyCheck")
		Rd.Start()
		Wait(3)
		Settle(3)
		local n, answered = 0, 0
		for name, r in pairs(Rd.results) do
			n = n + 1
			if r.addon then answered = answered + 1 end
			if type(Rd.Problems(name, r)) ~= "table" then return false, "Problems", "Liste" end
		end
		Rd.Summary()
		Rd.Announce()
		local my = Rd.MyStatus()
		if type(my) ~= "table" or my.e == nil or my.au == nil or my.du == nil then return false, "MyStatus", "f/e/au/fr/du" end
		if ActCount("DoReadyCheck") ~= rc then return false, "DoReadyCheck", "0" end
		local want = #RM.RaidMembers()
		if n < want or answered < want then return false, n .. " Ergebnisse, " .. answered .. " Antworten", want end
		return true, n .. " Ergebnisse"
	end)

	AsyncCheck(t, "T31", "B", "Pull- und Pausen-Timer", function()
		TestRaid()
		local TM = RM.Timer
		local cd = ActCount("DoCountdown")
		local sent = {}
		local u = {}
		return Guard(function()
			local orig = RM.SendAddonMessage
			Swap(u, RM, "SendAddonMessage", function(prefix, ...)
				if prefix ~= RM.PREFIX then sent[prefix] = (sent[prefix] or 0) + 1 end
				return orig(prefix, ...)
			end)
			Swap(u, RM.db.config, "timerAddons", "both")
			TM.Pull(10)
			if not TM.Running("pull") then return false, "Pull läuft nicht", "läuft" end
			Wait(1)
			if not TM.Running("pull") then return false, "Pull nach 1 s vorbei", "läuft noch" end
			TM.Cancel()
			if TM.Running("pull") then return false, "Pull läuft weiter", "abgebrochen" end
			TM.Break(5)
			if not TM.Running("break") then return false, "Pause läuft nicht", "läuft" end
			TM.Cancel()
			if TM.Running("break") then return false, "Pause läuft weiter", "beendet" end
			if ActCount("DoCountdown") ~= cd then return false, "DoCountdown", "0" end
			for _, p in ipairs({ "D5", "D4C", "BigWigs" }) do
				if (sent[p] or 0) < 3 then return false, p .. " " .. tostring(sent[p]), "je Start/Abbruch ein Aufruf" end
			end
			return true, string.format("D5 %d, D4C %d, BigWigs %d (alle zurückgehalten)", sent.D5, sent.D4C, sent.BigWigs)
		end, function() Undo(u); pcall(TM.Cancel); pcall(RM.Raid.StopPause, true) end)
	end)

	t:Check("T32", "B", "Rekorde", function()
		return KeepDB({ "records", "killlog", "shots", "shotList" }, function()
			local Rc = RM.Records
			if Rc.FormatTime(102) ~= "1:42" then return false, Rc.FormatTime(102), "1:42" end
			local shots = ActCount("Screenshot")
			local kl = Deep(RM.db.killlog)
			CallHandlers("ENCOUNTER_START", 663, "Lucifron", 9, 40)
			CallHandlers("ENCOUNTER_END", 663, "Lucifron", 9, 40, 0)
			Rc.Celebrate(663, "Lucifron", 3, RM.Now(), true)
			Rc.Best(663)
			Rc.CheckRecord(663, "Lucifron", 600, RM.Now())
			Rc.Print()
			Settle(2)
			local diff = {}
			Diff(kl, RM.db.killlog, "killlog", diff)
			if #diff > 0 then return false, "Kill-Protokoll im Test geändert", "unverändert" end
			if ActCount("Screenshot") ~= shots then return false, "Screenshot", "0" end
		end)
	end)

	t:Check("T33", "B", "Beute-Datenbank", function()
		local LDB = RM.LootDB
		local kind, id = LDB.ParseGUID("Creature-0-1234-409-5678-11502-0000ABCDEF")
		if kind ~= "Creature" or id ~= 11502 then return false, tostring(kind) .. " " .. tostring(id), "Creature 11502" end
		return KeepDB({ "lootdb" }, function()
			RM.db.lootdb = nil
			LDB.Record({ e = 663, p = "mc", n = "Lucifron", t = RM.Now() }, { 16800, 17010 }, {}, "Creature-0-1-409-1-12118-0001")
			LDB.Record({ e = 663, p = "mc", n = "Lucifron", t = RM.Now() }, { 16800 }, {}, "Creature-0-1-409-1-12118-0002")
			LDB.RecordTrash({ 17010 }, {}, "Creature-0-1-409-1-11666-0003", "mc")
			local list, kills = LDB.BossLoot(663)
			local ids = LDB.ItemIDs(663)
			local tids, tn = LDB.TrashIDs("mc")
			local kc, bosses = LDB.Stats()
			LDB.BossesForPool("mc"); LDB.TrashLoot("mc"); LDB.PrintBoss("lucifron")
			if kills ~= 2 or #ids ~= 2 or tn ~= 1 or kc ~= 2 or bosses ~= 1 then
				return false, string.format("Kills %s, Items %d, Trash %s, Stats %s/%s", tostring(kills), #ids, tostring(tn), tostring(kc), tostring(bosses)), "2/2/1/2/1"
			end
			for _, x in ipairs(list) do if x.id == 16800 and x.c ~= 2 then return false, "16800 " .. x.c .. "x", "2x" end end
		end)
	end)

	t:Check("T34", "B", "Item-Tooltips", function()
		return KeepDB({ "itemTips" }, function()
			local TT, IT = RM.Tooltip, RM.ItemTip
			TT.Invalidate()
			local lines = TT.Lines(LINK_EPIC)
			TT.Info(LINK_EPIC)
			local n = 0
			local fake = { GetItem = function() return "x", LINK_EPIC end, AddLine = function() n = n + 1 end, Show = function() end }
			local cfg = RM.db.config
			local was = cfg.itemTooltip
			cfg.itemTooltip = true
			TT.OnItem(fake)
			local on = n
			n = 0
			cfg.itemTooltip = false
			TT.OnItem(fake)
			local off = n
			cfg.itemTooltip = was
			IT.Scan(LINK_EPIC); IT.Has(LINK_EPIC); IT.Remember(LINK_EPIC, 5); IT.Prune()
			if off ~= 0 then return false, "Zeilen trotz aus", 0 end
			if on ~= #lines then return false, on .. " Zeilen", #lines end
			return true, #lines .. " Zusatzzeilen (Test-Verkauf aus T15)"
		end)
	end)

	t:Check("T35", "B", "Berufe", function()
		local P = RM.Prof
		return KeepDB({ "prof", "recipeMats" }, function()
			local TS = RM.API.Get("C_TradeSkillUI")
			local modern = RM.IsModern and TS ~= nil and TS.GetAllRecipeIDs ~= nil and TS.GetRecipeInfo ~= nil
			if P.HasModernAPI() ~= (modern and true or false) then return false, tostring(P.HasModernAPI()), tostring(modern) end
			P.ReadSkillLines()
			P.Openable()
			P.StoreScan("Testberuf", 300, 300, { 1, 2 }, { "A", "B" }, {})
			local e = RM.db.prof[RM.Me()].p.Testberuf
			if not (e and e.r == 300 and e.m == 300 and #e.i == 2 and #e.n == 2 and e.i[1] == 1 and e.n[2] == "B") then
				return false, "Format", "{r=300, m=300, i={1,2}, n={A,B}}"
			end
			P.Find("A"); P.PrintFind("A")
			P.SendMine()
			Allow({ "OpenTradeSkill", "CastSpellByName" }, function() P.ReadNext() end)
			P.pendingScan = nil
			if P.scanned then wipe(P.scanned) end
			Settle(6)
		end)
	end)
	t:Client("T35b", "B", "Berufe (Fenster echt öffnen)", "siehe T152: Knopf 'Meine Berufe einlesen' mehrmals, dann /rm berufe")

	t:Check("T36", "B", "Gildenbank", function()
		local Bk = RM.Bank
		return KeepDB({ "bank" }, function()
			if type(Bk.IsBankChar()) ~= "boolean" then return false, "IsBankChar", "true/false" end
			RM.db.bank = { i = { [12360] = { n = "Arkanitbarren", c = 5 }, [7078] = { n = "Essenz des Feuers", c = 2 } } }
			local list = Bk.Find("arkanit")
			Bk.PrintFind("arkanit")
			if #list ~= 1 or list[1].id ~= 12360 then return false, #list .. " Treffer", "1 Treffer (Testbestand)" end
		end)
	end)
	t:Client("T36b", "B", "Gildenbank echt", "Bank-Charakter: Bank öffnen, Post öffnen, dann /rm bank – Bestand > 0 Einträge?")

	t:Check("T37", "B", "Skillungen", function()
		local Sp = RM.Spec
		if Sp.MainTree({ 5, 5, 41 }) ~= 3 then return false, tostring(Sp.MainTree({ 5, 5, 41 })), 3 end
		if Sp.MainTree({ 0, 0, 0 }) ~= nil then return false, "Baum bei 0 Punkten", "nil" end
		if Sp.Role("Tank1") ~= "tank" then return false, tostring(Sp.Role("Tank1")), "tank (Test-Skillung)" end
		Sp.CanRole("Tank1", "tank"); Sp.Text("Tank1"); Sp.PointsText(RM.db.specs.Tank1)
		local insp = ActCount("NotifyInspect")
		Sp.BuildQueue(); Sp.StopScan()
		Sp.List()
		if ActCount("NotifyInspect") ~= insp then return false, "NotifyInspect", "0 für Testnamen" end
	end)

	t:Check("T38", "B", "Kommunikation: Serializer", function()
		local C = RM.Comm
		local v = { s = "Tab\tZeile\nStrich|Tilde~Umlaut äöü " .. string.rep("x", 300), n = -12.5, z = 0, b = true, f = false,
			e = {}, l = { 1, 2, { a = "b" } } }
		local back = C.Deserialize(C.Serialize(v))
		local diff = {}
		if type(back) ~= "table" then return false, type(back), "Tabelle" end
		Diff(v, back, "v", diff)
		if #diff > 0 then return false, table.concat(diff, ", "), "identisch" end
		for _, bad in ipairs({ "", "x\t{" }) do
			local ok, r = pcall(C.Deserialize, bad)
			if not ok then return false, "Lua-Fehler bei kaputtem Text", "nil ohne Fehler" end
			if type(r) == "table" and next(r) ~= nil then return false, "Daten aus kaputtem Text", "nil" end
		end
		local bytes = {}
		for i = 1, 2000 do bytes[i] = string.char(math.random(0, 255)) end
		local ok = pcall(C.Deserialize, table.concat(bytes))
		if not ok then return false, "Lua-Fehler bei Zufallsbytes", "kein Fehler" end
	end)

	AsyncCheck(t, "T39", "B", "Kommunikation: Mehrteil, Sync, Vertrauen", function()
		TestRaid()
		local C = RM.Comm
		local u = {}
		local parts, got = {}, 0
		return KeepDB({ "foreign" }, function()
			return Guard(function()
				local orig = RM.SendAddonMessage
				Swap(u, RM, "SendAddonMessage", function(prefix, msg, ...)
					if prefix == RM.PREFIX and type(msg) == "string" and msg:find("^~M\t") then parts[#parts + 1] = msg end
					return orig(prefix, msg, ...)
				end)
				Swap(u, C.handlers, "GSTEST", function() got = got + 1 end)
				local big = { s = string.rep("RaidMaster-Test ", 60) }
				C.Send("GSTEST", big, "RAID")
				Wait(math.max(1, C.Pending() * 0.15 + 0.5))
				if #parts < 2 then return false, #parts .. " Teile", "Mehrteil-Nachricht (~M)" end
				for i = #parts, 1, -1 do RM.SimulateEvent("CHAT_MSG_ADDON", RM.PREFIX, parts[i], "RAID", "Tank1") end
				if got ~= 1 then return false, "Handler " .. got .. "x", "genau 1x" end
				local e = CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, "UNBEKANNT\t{}", "RAID", "Tank1")
				if e > 0 then return false, "unbekannter Typ", "ignoriert" end
				-- HELLO mit höherer Version: Hinweis höchstens einmal
				local hello = { av = RM.VERSION_NUM + 1, at = "9.9.9", dv = 0, sk = 0 }
				CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, "HELLO\t" .. C.Serialize(hello), "RAID", "Tank1")
				if not (C.versions.Tank1 and C.versions.Tank1.num == RM.VERSION_NUM + 1) then return false, "HELLO nicht gemerkt", "Version gemerkt" end
				-- SNAP einer fremden Gilde: von Nicht-Leitung ignoriert, von Raidleitung übernommen
				local snap = DKP.MakeSnapshot(5)
				snap.g, snap.v = "Fremdgilde", (snap.v or 0) + 1
				CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, "SNAP\t" .. C.Serialize(snap), "RAID", "Fremd1")
				if RM.db.foreign and RM.db.foreign.Fremdgilde then return false, "SNAP von Nicht-Leitung übernommen", "ignoriert" end
				local origAuth = RM.IsRaidAuthority
				Swap(u, RM, "IsRaidAuthority", function(n) return n == "Tank1" or origAuth(n) end)
				Swap(u, RM.UI, "viewGuild", RM.UI.viewGuild)
				C.handlers.SNAP("Tank1", snap, "RAID")
				if not (RM.db.foreign and RM.db.foreign.Fremdgilde) then return false, "SNAP der Raidleitung", "übernommen (Ansicht)" end
				local blocked = RM.Test.blocked or 0
				CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, "PING\t{}", "RAID", "Tank1")
				local w = 0
				repeat Wait(0.3); w = w + 1 until C.Pending() == 0 or w > 15
				if (RM.Test.blocked or 0) <= blocked then return false, "PONG nicht zurückgehalten", "T.blocked steigt" end
				return true, #parts .. " Teile"
			end, function() Undo(u); C.versions.Tank1 = nil end)
		end)
	end)

	t:Check("T40", "B", "Begrüßung, Discord-Anleitung", function()
		TestRaid()
		local W, Gd = RM.Welcome, RM.Guide
		local reload = ActCount("ReloadUI")
		local lines = W.Lines("mc", { { name = "Gastino" }, { name = "Ersatz1", bench = true } })
		local all = table.concat(lines, "\n")
		if #lines < 2 or not all:find("Gastino", 1, true) or not all:find("Ersatz1", 1, true) then
			return false, #lines .. " Zeilen", ">= 2, Gast und Ersatzbank genannt"
		end
		local chat = #(RM.Test.lastChat or {})
		W.Send("mc")
		Settle(3)
		if type(Gd.StatusText()) ~= "string" then return false, "StatusText", "Text" end
		Gd.SendNow()
		if StaticPopup_Hide then pcall(StaticPopup_Hide, "RAIDMASTER_CONFIRM") end
		if not tostring(Gd.UPLOADER_URL):find("download/RaidMasterUploader%.zip$") then return false, "Uploader-Link", "…/download/RaidMasterUploader.zip" end
		if ActCount("ReloadUI") ~= reload then return false, "ReloadUI", "0 (nur nach Klick)" end
		if #(RM.Test.lastChat or {}) < chat then return false, "Begrüßung nicht im Testchat", "Raidchat-Umleitung" end
	end)

	t:Check("T41", "B", "Diagnose und Hänger lösen", function()
		TestRaid()
		local A, D = RM.Auction, RM.Diag
		local L = RM.L
		local client = A.client
		return Guard(function()
			ClearAuction()
			local function fix(want, what)
				local done = D.Fix()
				for _, l in ipairs(done) do if l == want then return true end end
				error(what .. ": " .. table.concat(done, " / "), 0)
			end
			local base = { aid = "test-aid", link = LINK_STONE, min = 10, inc = 5, pool = "mc", bids = {}, passes = {}, high = 0 }
			local c = Deep(base); c.finished = true; c.highName = "Tank1"; c.high = 10
			A.current = c
			fix(L["Vergabe-Fenster wieder angezeigt (Vergeben / Nicht vergeben / Neu versteigern)."], "(a) wartet auf Vergabe")
			A.HideAward(); A.current = nil
			c = Deep(base); c.endsAt = GetTime() - 5
			A.current = c
			fix(L["Abgelaufene Versteigerung beendet."], "(b) abgelaufen")
			if A.current then return false, "(b) current bleibt", "nil" end
			c = Deep(base); c.finished = true
			A.current = c
			fix(L["Beendete Versteigerung ohne Gebote aufgeräumt."], "(c) ohne Gebot")
			if A.current then return false, "(c) current bleibt", "nil" end
			A.client = { ended = true }
			fix(L["Altes Gebotsfenster geschlossen."], "(d) altes Gebotsfenster")
			Settle(2)
		end, function() A.client = client; ClearAuction() end)
	end)

	t:Check("T42", "B", "Raiddaten dieser Version", function()
		local D = RM.Data
		if #D.RaidList == 0 then return false, 0, "> 0 Raids" end
		local noInfo = 0
		for _, id in ipairs(D.BossOrder) do if not D.BossInfo[id] then noInfo = noInfo + 1 end end
		if noInfo > 0 then return false, noInfo .. " Boss-Taktiken fehlen", "vollständig" end
		if not D.GetTemplate("standard") then return false, "Vorlage standard fehlt", "vorhanden" end
		return true, #D.RaidList .. " Raids, " .. #D.BossOrder .. " Bosse"
	end)

	AsyncCheck(t, "T43", "B", "Test-Werkzeug selbst" .. (R.long and " (lang: mc + Stresstest)" or " (ony)"), function()
		local T = RM.Test
		local gst = GetServerTime
		local u = {}
		return Guard(function()
			T.FillRoster()
			if #RM.RaidMembers() ~= 40 then return false, #RM.RaidMembers() .. " im Testraid", 40 end
			T.ClearRoster()
			if #RM.RaidMembers() ~= 1 then return false, #RM.RaidMembers() .. " nach Leeren", 1 end
			T.FillRoster()
			-- Uhr: nur RM.Now wird verschoben, GetServerTime bleibt unangetastet
			T.SetTimeOffset(-7 * 86400)
			local shifted = GetServerTime() - RM.Now()
			T.SetTimeOffset(0)
			if math.abs(shifted - 7 * 86400) > 2 or GetServerTime ~= gst then return false, "Zeitversatz " .. shifted, "7 Tage, GetServerTime unverändert" end
			-- Durchlauf mit automatischer Versteigerung
			if RM.db.session.active then T.runEnding = true; pcall(RM.Raid.End); T.runEnding = nil end
			ClearAuction()
			Swap(u, T, "autoAuction", true)
			Swap(u, T, "pool", R.long and "mc" or "ony")
			-- Beute vorher beim Server anfordern und warten, bis der Client sie kennt (höchstens 10 s, ab 3.0.18):
			-- kurz nach dem ersten Einloggen war GetItemInfo leer und der Durchlauf vergab nichts
			local known, total = 0, 0
			if T.PreloadLoot then
				known, total = T.PreloadLoot(T.pool)
				local w = 0
				while total > 0 and known < total and w < 10 do Wait(1); w = w + 1; known, total = T.PreloadLoot(T.pool) end
			end
			local since = RM.Now() - 1
			local function items()
				local n = 0
				for _, e in ipairs(RM.db.data.log) do if type(e) == "table" and e.k == "item" and (e.t or 0) >= since then n = n + 1 end end
				return n
			end
			T.RunRaids(1)
			if not T.IsRunning() then return false, "Durchlauf startet nicht", "läuft" end
			local waited = 0
			while T.IsRunning() and waited < (R.long and 150 or 45) do Wait(1); waited = waited + 1 end
			Settle(7)
			if T.IsRunning() then T.StopRun(); return false, "Durchlauf hängt nach " .. waited .. " s", "fertig" end
			local n = items()
			-- "Raid starten" in RaidMaster bricht einen laufenden Durchlauf ab
			T.RunRaids(1)
			local was = T.IsRunning()
			pcall(RM.Raid.Start)
			local stopped = not T.IsRunning()
			if RM.db.session.active then T.runEnding = true; pcall(RM.Raid.End); T.runEnding = nil end
			if T.IsRunning() then T.StopRun() end
			ClearAuction()
			if not (was and stopped) then return false, "Override", "\"Raid starten\" bricht ab" end
			local stress = ""
			if R.long then
				local logN = #T.log
				T.pool = "ony"                      -- Stresstest eine Woche Onyxia (passt in die Grenze von 240 s)
				T.StressTest(1)
				local w = 0
				while T.IsRunning() and w < 60 do Wait(1); w = w + 1 end
				if T.IsRunning() then T.StopRun(); return false, "Stresstest hängt", "fertig" end
				local okStress = false
				for i = 1, math.max(1, #T.log - logN + 1) do
					if tostring(T.log[i]):find("neue Fehler: 0", 1, true) then okStress = true end
				end
				if not okStress then return false, "Stresstest mit neuen Fehlern", "neue Fehler: 0" end
				stress = ", Stresstest: neue Fehler 0"
			end
			if n < 1 then
				if total > 0 and known == 0 then return ASYNC_SKIP, "Beute noch nicht vom Server geladen (" .. known .. "/" .. total .. ") – Fall später wiederholen" end
				return false, "kein Item vergeben (Beute geladen " .. known .. "/" .. total .. ")", ">= 1"
			end
			if RM.db.testMode and RM.db.testMode.post then return false, "testMode.post gesetzt", "nil" end
			return true, n .. " Items vergeben in " .. waited .. " s" .. stress
		end, function() Undo(u); if T.IsRunning() then T.StopRun() end; T.SetTimeOffset(0); T.FillRoster(); RM.Loot.pendingBoss = nil end)
	end)

	t:Check("T44", "B", "Alle Ereignisse einmal", function()
		TestRaid()
		local cfg = RM.db.config
		cfg.bankScan, cfg.bankChar = false, ""          -- Testmodus-Einstellung: kein Bank-Scan aus diesem Test
		local before = {}
		for _, n in ipairs(RM.ACT_NAMES) do before[n] = ActCount(n) end
		local events = {
			{ "ACTIVE_TALENT_GROUP_CHANGED", 1, 2 }, { "BANKFRAME_OPENED" }, { "BANKFRAME_CLOSED" }, { "CHARACTER_POINTS_CHANGED", 0 },
			{ "CHAT_MSG_ADDON", RM.PREFIX, "PING\t{}", "RAID", "Tank1" }, { "CHAT_MSG_SYSTEM", "Testsystemmeldung" },
			{ "CHAT_MSG_WHISPER", "hallo", "Tank1" }, { "CRAFT_SHOW" }, { "ENCOUNTER_START", 663, "Lucifron", 9, 40 },
			{ "ENCOUNTER_END", 663, "Lucifron", 9, 40, 0 }, { "GROUP_ROSTER_UPDATE" }, { "GUILDBANKFRAME_OPENED" },
			{ "GUILD_ROSTER_UPDATE" }, { "INSPECT_READY", nil }, { "INSPECT_TALENT_READY" }, { "INSTANCE_ENCOUNTER_ENGAGE_UNIT" },
			{ "LOOT_OPENED" }, { "LOOT_SLOT_CLEARED", 1 }, { "LOOT_CLOSED" }, { "MAIL_SHOW" }, { "MAIL_INBOX_UPDATE" }, { "MAIL_CLOSED" },
			{ "PARTY_LEADER_CHANGED" }, { "PARTY_LOOT_METHOD_CHANGED" }, { "PLAYER_ENTERING_WORLD", false, false },
			{ "PLAYER_GUILD_UPDATE", "player" }, { "PLAYER_REGEN_ENABLED" }, { "PLAYER_SPECIALIZATION_CHANGED", "player" },
			{ "PLAYER_TALENT_UPDATE" }, { "PLAYER_TARGET_CHANGED" }, { "TRADE_SHOW" }, { "TRADE_SKILL_LIST_UPDATE" },
			{ "TRADE_SKILL_SHOW" }, { "UI_INFO_MESSAGE", 0, "Test" },
		}
		local errs, first = 0, nil
		for _, ev in ipairs(events) do
			local e, f = CallHandlers(unpack(ev, 1, 6))
			if e > 0 then errs = errs + e; first = first or (ev[1] .. ": " .. tostring(f)) end
		end
		Settle(10)
		if errs > 0 then return false, errs .. " Fehler, zuerst " .. first, "0" end
		local acted = {}
		for _, n in ipairs(RM.ACT_NAMES) do if ActCount(n) ~= before[n] then acted[#acted + 1] = n end end
		if #acted > 0 then return false, "Aktion: " .. table.concat(acted, ", "), "0" end
		return true, #events .. " Ereignisse"
	end)

	t:Check("T45", "B", "Tastenbelegungen", function()
		TestRaid()
		local M = RM.Markers
		local fns = { RaidMaster.UI.Toggle, M.SmartMark, M.Mark, M.MarkAdds, M.ClearAll }
		for i, f in ipairs(fns) do if type(f) ~= "function" then return false, "Funktion " .. i .. " fehlt", "alle aus Bindings.xml" end end
		local miss = {}
		for _, b in ipairs({ "TOGGLE", "SMARTMARK", "MARK8", "MARK7", "MARK6", "MARK5", "MARK4", "MARK3", "MARK2", "MARK1", "CLEARMARK", "MARKADDS", "CLEARALL" }) do
			if type(_G["BINDING_NAME_RAIDMASTER_" .. b]) ~= "string" then miss[#miss + 1] = b end
		end
		if #miss > 0 then return false, "BINDING_NAME fehlt: " .. table.concat(miss, ","), "alle gesetzt" end
		local units = { mouseover = { guid = "Creature-0-1-2-3-11111-0000000009", name = "Testgegner" } }
		return Allow({ "SetRaidTarget" }, function()
			return WithAPI(FakeUnits(units), nil, function()
				for i = 0, 8 do M.Mark(i) end
				M.SmartMark(); M.MarkAdds(); M.ClearAll()
				RaidMaster.UI.Toggle(); RaidMaster.UI.Toggle()
				M.ResetUsed()
				Settle(2)
			end)
		end)
	end)

	-- T46: Sperrgitter – Flüster-Antworten (!dkp, !bid) gehen im Testmodus über RM.Whisper, nichts Echtes
	t:Check("T46", "B", "Sperrgitter: !dkp/!bid per Flüstern, Zähler je RM.Act", function()
		TestRaid()
		local whispers = 0
		local cfg = RM.db.config
		local u = {}
		return Guard(function()
			Swap(u, cfg, "whisperReplies", true)
			Swap(u, RM, "Whisper", function() whispers = whispers + 1 end)
			local before = RealTotal()
			local errors, first = CallHandlers("CHAT_MSG_WHISPER", "!dkp", "Tank1")
			if errors > 0 then return false, first, "kein Fehler" end
			errors, first = CallHandlers("CHAT_MSG_WHISPER", "!dkp Tank1", "Krieger1")
			if errors > 0 then return false, first, "kein Fehler" end
			ClearAuction()
			RM.Auction.Start(LINK_STONE)
			errors, first = CallHandlers("CHAT_MSG_WHISPER", "!bid 20", "Tank1")
			ClearAuction()
			if errors > 0 then return false, first, "kein Fehler" end
			if whispers ~= 3 then return false, whispers .. " Antworten über RM.Whisper", 3 end
			if RealTotal() ~= before then return false, "echte Aktion", "0" end
			if RM.db.testMode and RM.db.testMode.post then return false, "testMode.post gesetzt", "nil" end
			local bad = {}
			for _, n in ipairs(RM.ACT_NAMES) do
				if n ~= "SetRaidTarget" and ActCount(n) - (R.allowed[n] or 0) > 0 then bad[#bad + 1] = n .. " " .. (ActCount(n) - (R.allowed[n] or 0)) end
			end
			if #bad > 0 then return false, table.concat(bad, ", "), "0 (außer erlaubten Testaufrufen)" end
		end, function() Undo(u) end)
	end)
end

---------------------------------------------------------------------------
-- C. Forever-Sonderfälle (simuliert)
---------------------------------------------------------------------------
local function AreaC(t, G)
	t:Check("T50", "C", "Simulator für geschützte Werte", function()
		local origG = RM.G and RM.G.IsSecret
		local r = pack(WithSecret(function(SECRET)
			if not RM.IsSecret(SECRET) then return false, "nicht erkannt", "RM.IsSecret true" end
			if RM.G and RM.G.Short and RM.G.Short(SECRET) ~= nil then return false, "G.Short", "nil" end
			if GoldSentinelTest.Str(SECRET) ~= "<geschützt>" then return false, "Str", "<geschützt>" end
			local ok = pcall(function() return SECRET:lower() end)
			if ok then return false, "Köder wirft nicht", "Fehler bei Benutzung" end
		end))
		if RM.G and RM.G.IsSecret ~= origG then return false, "G.IsSecret nicht zurück", "wie vorher" end
		return unpack(r, 1, r.n)
	end)
	t:Check("T51", "C", "Addon-Nachricht mit geschütztem Absender", function()
		return WithSecret(function(SECRET)
			local e1, f1 = CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, "PING\t{}", "RAID", SECRET)
			local e2, f2 = CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, "~M\t1\t1\t2\tx", "RAID", SECRET)
			if e1 + e2 > 0 then return false, f1 or f2, "verworfen ohne Fehler" end
		end)
	end)
	t:Client("T51b", "C", "Absender von Addon-Nachrichten im Kampf geschützt?",
		"Forever, im Kampf mit Mitspieler: /rm sync – kommt keine Lua-Meldung, ist alles gut")
	t:Check("T52", "C", "Flüstern mit geschütztem Text oder Absender", function()
		return WithSecret(function(SECRET)
			local errs, first = 0, nil
			for _, args in ipairs({ { SECRET, "Tank1" }, { "!bid 20", SECRET }, { SECRET, SECRET } }) do
				local e, f = CallHandlers("CHAT_MSG_WHISPER", args[1], args[2])
				errs = errs + e; first = first or f
			end
			if errs > 0 then return false, first, "kein Fehler in den 5 Handlern" end
		end)
	end)
	t:Check("T53", "C", "Bereitschafts-Check mit geschützten Auren", function()
		local Rd = RM.Ready
		local L = RM.L
		return WithSecret(function(SECRET)
			local fake = { GetAuraDataByIndex = function(_, i) if i == 1 then return { name = SECRET, spellId = 17626 } end end }
			return WithAPI({ C_UnitAuras = fake }, { "UnitAura", "UnitBuff" }, function()
				local flask, elixirs, readable = Rd.AuraInfo("player")
				if readable ~= false then return false, "lesbar", "readable false" end
				local p = Rd.Problems("Test", { flask = flask, elixirs = elixirs, noAura = not readable })
				local txt = table.concat(p, " | ")
				if not txt:find(L["Buffs nicht lesbar"], 1, true) or txt:find(L["kein Fläschchen"], 1, true) then
					return false, txt, "\"Buffs nicht lesbar\", nicht \"kein Fläschchen\""
				end
			end)
		end)
	end)
	t:Check("T54", "C", "Systemmeldung geschützt", function()
		return WithSecret(function(SECRET)
			local e, f = CallHandlers("CHAT_MSG_SYSTEM", SECRET)
			if e > 0 then return false, f, "kein Fehler" end
			-- auch direkt: S.OnSystemMessage prüft RM.IsSecret vor allem anderen
			if RM.Signup.OnSystemMessage(SECRET) ~= nil then return false, "ausgewertet", "nil" end
			local okG, cls = pcall(RM.Gaps.ClassOf, "X", SECRET, "inv")
			if not okG then return false, "G.ClassOf: " .. tostring(cls), "kein Fehler" end
		end)
	end)
	t:Client("T54b", "C", "Systemmeldung mit geschütztem Text",
		"Forever, im Kampf jemanden einladen lassen: kommt keine Lua-Meldung, ist alles gut (echte geschützte Strings lassen sich nicht nachstellen)")
	t:Check("T55", "C", "Fehlende alte Globals: Auren und Zauber", function()
		local Rd = RM.Ready
		local fakeAura = { GetAuraDataByIndex = function(_, i) if i == 1 then return { name = "Testbuff", spellId = 1 } end end }
		local r = pack(WithAPI({ C_UnitAuras = fakeAura }, { "UnitAura", "UnitBuff" }, function()
			local n = RM.GetBuff("player", 1)
			if n ~= "Testbuff" then return false, "GetBuff " .. tostring(n), "über C_UnitAuras" end
		end))
		if r[1] == false then return unpack(r, 1, r.n) end
		r = pack(WithAPI(nil, { "UnitAura", "UnitBuff", "C_UnitAuras" }, function()
			if RM.CanReadAuras() then return false, "CanReadAuras true", "false ohne jede Aura-API" end
			local _, _, readable = Rd.AuraInfo("player")
			if readable ~= false then return false, "readable", "false" end
		end))
		if r[1] == false then return unpack(r, 1, r.n) end
		r = pack(WithAPI({ C_Spell = { GetSpellName = function(id) return "Zauber" .. id end } }, { "GetSpellInfo" }, function()
			if RM.GetSpellName(2575) ~= "Zauber2575" then return false, tostring(RM.GetSpellName(2575)), "über C_Spell" end
		end))
		if r[1] == false then return unpack(r, 1, r.n) end
		r = pack(WithAPI(nil, { "GetSpellInfo", "C_Spell" }, function()
			local ok, n = pcall(RM.GetSpellName, 2575)
			if not ok or n ~= nil then return false, tostring(n), "nil ohne Fehler" end
		end))
		if r[1] == false then return unpack(r, 1, r.n) end
		if next(RM.API.hide) or next(RM.API.over) then return false, "hide/over nicht leer", "leer" end
	end)
	t:Check("T56", "C", "Bindungen beim Laden und Laufzeitwahl", function()
		if C_Item and C_Item.GetItemInfo and RM.GetItemInfo ~= C_Item.GetItemInfo then return false, "RM.GetItemInfo", "C_Item.GetItemInfo" end
		if C_Container and C_Container.GetContainerNumSlots and RM.Container.NumSlots ~= C_Container.GetContainerNumSlots then
			return false, "RM.Container.NumSlots", "C_Container"
		end
		return WithAPI({ C_PartyInfo = { GetLootMethod = function() return 2, 0, nil end } }, { "GetLootMethod" }, function()
			local m = RM.GetLootMethod()
			if m ~= "master" then return false, "GetLootMethod " .. tostring(m), "master über C_PartyInfo" end
		end)
	end)
	t:Check("T57", "C", "Kampfsperre simuliert", function()
		TestRaid()
		local M = RM.Markers
		local L = RM.L
		local u = {}
		local acts = {}
		for _, n in ipairs(RM.ACT_NAMES) do acts[n] = ActCount(n) end
		return Guard(function()
			Swap(u, RM, "simCombat", true)
			if not RM.InCombat() then return false, "RM.InCombat", "true" end
			return WithPrints(function(lines)
				RM.Prof.ReadNext()
				if not Printed(lines, L["Im Kampf geht das nicht."]) then return false, "Berufe ohne Hinweis", "Hinweis" end
				local id = RM.Ready.checkId
				RM.Ready.Start()
				if RM.Ready.checkId ~= id or not Printed(lines, L["Den Bereitschafts-Check bitte außerhalb des Kampfes starten."]) then
					return false, "Bereitschafts-Check im Kampf", "Hinweis, kein Start"
				end
				if RM.Signup.ArrangeStep() ~= false then return false, "ArrangeStep", "false" end
				RM.Guide.SendNow()
				local okF = WithFlavor("forever", function()
					M.MarkAdds()
					return M.CombatBlocked()
				end)
				if not okF then return false, "CombatBlocked (Forever)", "true" end
				if not Printed(lines, L[M.COMBAT_HINT]) then return false, "MarkAdds ohne Hinweis", "COMBAT_HINT" end
				for _, n in ipairs(RM.ACT_NAMES) do
					if ActCount(n) ~= acts[n] then return false, "Aktion " .. n, "keine im Kampf" end
				end
			end)
		end, function() Undo(u) end)
	end)
	t:Check("T58", "C", "Kampflog gesperrt bzw. offen", function()
		local reg = RM.frame:IsEventRegistered("COMBAT_LOG_EVENT_UNFILTERED") and true or false
		if reg ~= (RM.Caps.combatLog and true or false) then return false, tostring(reg), tostring(RM.Caps.combatLog) end
		if RM.IsModern and reg then return false, "registriert", "nicht registriert (moderner Client)" end
		return true, reg and "registriert" or "nicht registriert"
	end)
	-- T59 (gesperrte Aktionen im Spiel) wird am Ende der Routine geprüft
end

---------------------------------------------------------------------------
-- D. Alte Clients (T70 wird am Ende der Routine ausgewertet)
---------------------------------------------------------------------------
local function AreaD(t)
	if RM.IsModern then
		for _, id in ipairs({ "T71", "T72", "T73", "T74", "T75" }) do t:Skip(id, "D", "Alter Client", "nur im alten Client (Era/TBC)") end
		return
	end
	t:Check("T72", "D", "Talentbäume", function()
		if not RM.Caps.talentTrees then return false, "talentTrees false", "true" end
		local p = RM.Spec.ReadPoints()
		local lvl = UnitLevel("player") or 0
		-- verteilte Punkte höchstens Stufe - 9 (nicht verteilte Punkte sind erlaubt)
		local sum = p and ((p[1] or 0) + (p[2] or 0) + (p[3] or 0)) or 0
		if p and lvl >= 10 and sum > lvl - 9 then return false, "Punkte " .. sum, "<= " .. (lvl - 9) end
		return true, p and (sum .. " Punkte in drei Bäumen") or "keine Punkte verteilt"
	end)
	t:Check("T73", "D", "Kampflog-Weg unverändert", function()
		if not RM.Caps.combatLog then return false, "combatLog false", "true" end
	end)
	t:Check("T74", "D", "Namen exakt", function()
		if not RM.SameName("Testa", "testa") or RM.SameName("Testa Beispiel", "Testa") then return false, "SameName", "nur exakt" end
	end)
	t:Client("T71", "D", "Auren auf dem alten Client", "mit Fläschchen/Elixier: /rm bereit – wird es erkannt?")
	t:Client("T75", "D", "Plündermeister-Weg", "in einer Gruppe mit Plündermeister: /dump RaidMaster.GetLootMethod()")
end

---------------------------------------------------------------------------
-- E. Daten (alles mit Kopien; RM.db bleibt die echte Tabelle)
---------------------------------------------------------------------------
local function WithDB(copy, body)
	local u = {}
	Swap(u, RM, "db", copy)
	return Guard(body, function() Undo(u) end)
end

local function AreaE(t)
	t:Check("T80", "E", "Neuinstallation", function()
		local real = RM.db
		local db = RM.InitDB({})
		if RM.db ~= real then return false, "RM.db getauscht", "echte Tabelle" end
		local d, s, c = db.data, db.data.settings, db.config
		local ok = d.version == 0 and next(d.players) == nil and next(d.log) == nil
			and s.auctionTime == 30 and s.minBid == 10 and s.bidIncrement == 5 and s.decayPct == 10
			and c.activePool == "mc" and c.autoInvite == false and db.session.active == false
			and next(db.pendingAwards) == nil and next(db.specs) == nil
		if not ok then return false, "Standardwerte", "DEFAULT_SETTINGS/DEFAULT_CONFIG" end
	end)
	t:Check("T81", "E", "Migration älterer Fassungen", function()
		local db = {
			data = { players = { Alt = { dkp = 40, c = "WARRIOR" }, Inst = { d = { i409 = 7 } } }, pools = { i409 = {} },
				settings = { raidLeader = "X" } },
			config = { lootThreshold = 3 },
			foreign = { Fremd = { players = { F1 = { dkp = 5 } } } },
		}
		RM.InitDB(db)
		local e = {}
		if not (db.data.players.Alt.d.mc == 40 and db.data.players.Alt.dkp == nil) then e[#e + 1] = "(a) dkp" end
		if not (db.data.players.Inst.d.mc == 7 and db.data.pools.i409 == nil) then e[#e + 1] = "(b) i409" end
		if db.config.lootThreshold ~= 2 then e[#e + 1] = "(c) Schwelle" end
		if not (db.config.autoInvite == false and db.config.autoGroups == false and db.config.autoLoot == false) then e[#e + 1] = "(d) manual250" end
		if db.data.settings.raidLeader ~= nil then e[#e + 1] = "(e) raidLeader" end
		if not (db.foreign.Fremd.players.F1.d and db.foreign.Fremd.players.F1.d.mc == 5) then e[#e + 1] = "(f) foreign" end
		local again = Deep(db)
		RM.InitDB(again)
		local diff = {}
		Diff(db, again, "db", diff)
		if #diff > 0 then e[#e + 1] = "zweiter Lauf ändert " .. table.concat(diff, ",") end
		if #e > 0 then return false, table.concat(e, "; "), "alle Umstellungen, zweiter Lauf ohne Änderung" end
	end)
	t:Check("T82", "E", "Beschädigte Einträge", function()
		local db = Deep(RM.db)
		db.data.players.X = "kaputt"
		db.data.players.Y = { d = "x" }
		db.data.log = { 5, { t = "a" } }
		db.specs = db.specs or {}
		db.specs.Z = 7
		db.signup = { list = "x" }
		db.lootdb = 1
		db.prof = { A = { p = 3 } }
		db.killlog = { "x" }
		db.config.positions = 5
		db.config.standby = nil
		db.gsTest = "x"
		local errs = {}
		local function try(what, fn, ...)
			local ok, err = pcall(fn, ...)
			if not ok then errs[#errs + 1] = what .. ": " .. tostring(err) end
		end
		try("InitDB", RM.InitDB, db)
		try("SortedPlayers", RM.DKP.SortedPlayers, "mc", db.data)
		try("Summary", RM.DKP.Summary, "Y", db.data)
		WithDB(db, function()
			try("Spec.List", RM.Spec.List)
			try("LDB.Stats", RM.LootDB.Stats)
		end)
		if #errs > 0 then return false, table.concat(errs, " | "):sub(1, 250), "kein Lua-Fehler" end
	end)
	t:Check("T83", "E", "Absturz mitten im Test", function()
		local T = RM.Test
		local copy = Deep(RM.db)
		copy.testMode = { active = true }
		local backup = Deep(RaidMasterTestDB)
		local known = { data = Deep(copy.data), session = { active = false, kills = {} }, trade = {}, config = Deep(copy.config),
			specs = {}, hasSignup = false }
		known.data.version = 424242
		local gs = copy.gsTest
		local u = {}
		local real = RaidMasterTestDB
		return Guard(function()
			Swap(u, RM, "db", copy)
			RaidMasterTestDB = known
			local did = T.RestoreAfterCrash()
			if not did then return false, "Lade-Handler tut nichts", "wiederhergestellt" end
			if copy.data.version ~= 424242 then return false, "Daten", "wie die Sicherung" end
			if copy.testMode ~= nil or RaidMasterTestDB ~= nil then return false, "testMode/RaidMasterTestDB übrig", "nil" end
			if copy.gsTest ~= gs then return false, "gsTest geändert", "unverändert" end
		end, function()
			Undo(u)
			RaidMasterTestDB = real
			local diff = {}
			Diff(backup, RaidMasterTestDB, "RaidMasterTestDB", diff)
		end)
	end)
	t:Check("T84", "E", "Große Datenmengen", function()
		local db = Deep(RM.db)
		for i = 1, 500 do db.data.players["Spieler" .. i] = { c = "WARRIOR", d = { mc = i } } end
		for i = 1, 5000 do db.data.log[#db.data.log + 1] = { id = "t" .. i, t = i, k = "manual", x = "Test", d = { Spieler1 = 1 }, pool = "mc" } end
		db.specs = db.specs or {}
		for i = 1, 300 do db.specs["Spieler" .. i] = { c = "WARRIOR", p = { 5, 5, 41 }, t = RM.Now() } end
		db.itemTips = {}
		for i = 1, (RM.ItemTip.MAX or 600) + 50 do db.itemTips[100000 + i] = { n = "x", t = i } end
		local t0 = Ms()
		return WithDB(db, function()
			local list = RM.DKP.SortedPlayers("mc")
			local snap = RM.DKP.MakeSnapshot()
			RM.Spec.Prune()
			RM.ItemTip.Prune()
			if #list < 500 then return false, #list .. " Spieler", ">= 500" end
			if #snap.l > 60 then return false, #snap.l .. " Log-Einträge im Snapshot", "<= 60" end
			if Count(db.itemTips) > (RM.ItemTip.MAX or 600) then return false, Count(db.itemTips) .. " Item-Tooltips", "<= " .. (RM.ItemTip.MAX or 600) end
			if RM.Records.MAX_LOG ~= 400 then return false, "Records.MAX_LOG " .. tostring(RM.Records.MAX_LOG), 400 end
			return true, string.format("%.0f ms", Ms() - t0)
		end)
	end)
	t:Check("T85", "E", "Berichte in den SavedVariables", function()
		local s = RaidMasterDB.gsTest
		if type(s) ~= "table" or type(s.reports) ~= "table" then return false, "gsTest fehlt", "Tabelle" end
		if #s.reports > (GoldSentinelTest.MAX_REPORTS or 10) then return false, #s.reports, "höchstens 10" end
		for _, r in ipairs(s.reports) do
			if type(r) ~= "string" or r:sub(1, 7) ~= "GSTEST1" then return false, "Eintrag ohne GSTEST1", "GSTEST1…" end
		end
		return true, #s.reports .. " vorhandene Berichte"
	end)
end

---------------------------------------------------------------------------
-- F. Sprachen (T90 am Ende der Routine)
---------------------------------------------------------------------------
local function AreaF(t)
	t:Check("T93", "F", "Sprache im Bericht", function()
		local loc = GetLocale and GetLocale()
		local exp = (loc == "enGB") and "enUS" or loc
		if RM.LANGUAGES[exp] and RM.LOCALE ~= exp then return false, RM.LOCALE, exp end
		return true, RM.LOCALE
	end)
	t:Skip("T91", "F", "Formatplatzhalter", "offline geprüft (Lua 5.1 mit lupa)")
	t:Client("T92", "F", "Jede Sprache einmal aktiv", "einmal mit englischem Client /rmtest testroutine F")
end

---------------------------------------------------------------------------
-- G. Zusammenspiel
---------------------------------------------------------------------------
local function AreaG(t)
	t:Check("T100", "G", "Mehrere GoldSentinel-Addons", function()
		local ok = type(GoldSentinelGame) == "table" and type(GoldSentinelDev) == "table" and type(GoldSentinelTest) == "table"
		if not ok then return false, "gemeinsame Tabelle fehlt", "alle drei" end
		local list = {}
		for name in pairs(GoldSentinelTest.registry or {}) do list[#list + 1] = name end
		table.sort(list)
		return true, table.concat(list, ", ")
	end)
	t:Check("T101", "G", "Keine globalen Namen überschrieben", function()
		local bad = {}
		if RaidMaster ~= RM then bad[#bad + 1] = "RaidMaster" end
		if RaidMasterTest ~= RM.Test then bad[#bad + 1] = "RaidMasterTest" end
		if SLASH_RAIDMASTER1 ~= "/rm" then bad[#bad + 1] = "SLASH_RAIDMASTER1" end
		if SlashCmdList.RAIDMASTERTEST ~= RM.Test.Slash then bad[#bad + 1] = "RAIDMASTERTEST" end
		if type(SlashCmdList.RAIDMASTER) ~= "function" then bad[#bad + 1] = "RAIDMASTER" end
		if #bad > 0 then return false, table.concat(bad, ", "), "eigene" end
	end)
	t:Check("T102", "G", "Datenformat RaidMaster.db.prof", function()
		local prof = RM.db.prof
		if prof == nil then return true, "noch keine Berufe gespeichert" end
		if prof ~= R.profTable then return false, "Tabelle RM.db.prof ersetzt", "gleiche Identität wie vor dem Test" end
		for _, e in pairs(prof) do
			if type(e) == "table" and type(e.p) == "table" then
				for _, b in pairs(e.p) do
					if type(b) == "table" and type(b.i) == "table" and type(b.n) == "table" and #b.i ~= #b.n then
						return false, "#i ~= #n", "gleich lang"
					end
				end
			end
		end
	end)
	t:Client("T103", "G", "DBM und BigWigs", "Pull-Timer aus der Boss-Leiste: Balken bei DBM/BigWigs sichtbar?")
	t:Client("T104", "G", "BugSack/BugGrabber", "mit BugSack: /rmtest testroutine I – Testfehler in BugSack und Diagnose?")
	t:Check("T105", "G", "Altes Addon RaidMasterTest", function()
		local T = RM.Test
		local fooCalled = false
		local function foo() fooCalled = true end
		local dummy = { active = false, Stop = function() end, Foo = foo }
		local before = { inRaid = RM.InRaid, whisper = RM.Whisper }
		local slash = SlashCmdList.RAIDMASTERTEST
		return Allow({ "DisableAddOn" }, function()
			return Guard(function()
				local dis = ActCount("DisableAddOn")
				RaidMasterTest = dummy
				local did = T.RetireOldAddon()
				if not did then return false, "Attrappe nicht erkannt", "stillgelegt" end
				if RaidMasterTest ~= T then return false, "RaidMasterTest", "eingebautes Test-Werkzeug" end
				if dummy.Foo == foo then return false, "Funktion der Attrappe aktiv", "ersetzt" end
				if ActCount("DisableAddOn") ~= dis + 1 then return false, "DisableAddOn " .. (ActCount("DisableAddOn") - dis), "1 über RM.Act" end
				if RM.InRaid ~= before.inRaid or RM.Whisper ~= before.whisper then return false, "RM-Funktionen im Testmodus geändert", "unverändert" end
				if fooCalled then return false, "Attrappe ausgeführt", "nicht" end
			end, function() RaidMasterTest = T; SlashCmdList.RAIDMASTERTEST = slash end)
		end)
	end)
end

---------------------------------------------------------------------------
-- H. Leistung (debugprofilestop, je 20 Läufe, Mittelwert und Maximum)
---------------------------------------------------------------------------
local function Measure(fn, n)
	n = n or 20
	local total, max = 0, 0
	for _ = 1, n do
		local t0 = debugprofilestop()
		fn()
		local d = debugprofilestop() - t0
		total, max = total + d, math.max(max, d)
	end
	return total / n, max
end

local function AreaH(t)
	if type(debugprofilestop) ~= "function" then
		for _, id in ipairs({ "T110", "T111", "T112", "T113", "T114", "T115", "T116" }) do t:Skip(id, "H", "Leistung", "debugprofilestop fehlt") end
		return
	end
	t:Check("T110", "H", "Zielwechsel (Boss-Leiste) < 2 ms", function()
		local B = RM.BossBar
		local u = {}
		return Guard(function()
			Swap(u, B, "ReadTarget", function() return true, false, "Ragnaros" end)
			Swap(u, B, "testTarget", nil)
			B.TargetBoss()                         -- erster Aufbau des Namensverzeichnisses
			local avg, max = Measure(B.TargetBoss)
			if avg >= 2 then return false, string.format("%.2f ms", avg), "< 2 ms" end
			return true, string.format("Mittel %.3f ms, max %.3f ms", avg, max)
		end, function() Undo(u) end)
	end)
	t:Check("T111", "H", "Gruppenwechsel: Handler < 2 ms, zusammen < 16 ms", function()
		TestRaid()
		RM.UI.Open("dkp")
		local list = RM.HandlersFor("GROUP_ROSTER_UPDATE") or {}
		local slow, total = {}, 0
		return Guard(function()
			for i, fn in ipairs(list) do
				local avg = Measure(function() pcall(fn) end)
				total = total + avg
				if avg >= 2 then slow[#slow + 1] = string.format("#%d %.2f ms", i, avg) end
			end
			Settle(10)
			if #slow > 0 then return false, table.concat(slow, ", "), "< 2 ms je Handler" end
			if total >= 16 then return false, string.format("%.1f ms", total), "< 16 ms" end
			return true, string.format("%d Handler, zusammen %.2f ms", #list, total)
		end, function() if Shown(MainFrame()) then RM.UI.Toggle() end end)
	end)
	t:Check("T112", "H", "Addon-Nachrichten: BID < 2 ms, SNAP 500 < 16 ms", function()
		TestRaid()
		local C = RM.Comm
		local msg = "BID\t" .. C.Serialize({ a = "kein-aid", v = 20, g = "" })
		local avg = Measure(function() CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, msg, "WHISPER", "Tank1") end)
		local players = {}
		for i = 1, 500 do players["Spieler" .. i] = { c = "WARRIOR", d = { mc = i } } end
		local snap = { v = 1, p = players, s = Deep(RM.db.data.settings), l = {} }
		local avgS = Measure(function() RM.DKP.ImportSnapshotTo({ log = {} }, snap, false) end, 5)
		if avg >= 2 then return false, string.format("BID %.2f ms", avg), "< 2 ms" end
		if avgS >= 16 then return false, string.format("SNAP %.1f ms", avgS), "< 16 ms (sonst auf Ticker verteilen)" end
		return true, string.format("BID %.3f ms, SNAP %.2f ms", avg, avgS)
	end)
	t:Check("T113", "H", "Ticker < 1 ms, D.Text mit 20 Fehlern < 16 ms", function()
		local D = RM.Diag
		local saved = {}
		for i, e in ipairs(D.errors) do saved[i] = e end
		return Guard(function()
			local tick = Measure(RM.Auction.Tick)
			for i = 1, 20 do table.insert(D.errors, { t = time(), msg = "RaidMaster-Testfehler " .. i, n = 1 }) end
			local txt = Measure(D.Text, 5)
			if tick >= 1 then return false, string.format("Auction.Tick %.2f ms", tick), "< 1 ms" end
			if txt >= 16 then return false, string.format("D.Text %.1f ms", txt), "< 16 ms" end
			return true, string.format("Tick %.3f ms, D.Text %.2f ms", tick, txt)
		end, function() wipe(D.errors); for i, e in ipairs(saved) do D.errors[i] = e end end)
	end)
	t:Check("T114", "H", "Serializer 500 Spieler < 16 ms", function()
		local data = { players = {} }
		for i = 1, 500 do data.players["Spieler" .. i] = { c = "WARRIOR", d = { mc = i, ony = i * 2 } } end
		local t0 = debugprofilestop()
		local s = RM.Comm.Serialize(data)
		RM.Comm.Deserialize(s)
		local d = debugprofilestop() - t0
		if d >= 16 then return false, string.format("%.1f ms", d), "< 16 ms" end
		return true, string.format("%.1f ms", d)
	end)
	t:Check("T115", "H", "Tooltip < 2 ms, erster Aufbau < 16 ms", function()
		local TT = RM.Tooltip
		local fake = { GetItem = function() return "x", LINK_EPIC end, AddLine = function() end, Show = function() end }
		TT.Invalidate()
		local t0 = debugprofilestop()
		TT.OnItem(fake)
		local first = debugprofilestop() - t0
		local avg = Measure(function() for _ = 1, 50 do TT.OnItem(fake) end end, 1) / 50
		if first >= 16 then return false, string.format("Aufbau %.1f ms", first), "< 16 ms" end
		if avg >= 2 then return false, string.format("%.2f ms", avg), "< 2 ms" end
		return true, string.format("Aufbau %.2f ms, je Tooltip %.3f ms", first, avg)
	end)
	t:Check("T116", "H", "Speicher: Zuwachs < 256 KB", function()
		TestRaid()
		local TT = RM.Tooltip
		local fake = { GetItem = function() return "x", LINK_EPIC end, AddLine = function() end, Show = function() end }
		collectgarbage("collect")
		local before = collectgarbage("count")
		for _ = 1, 100 do CallHandlers("GROUP_ROSTER_UPDATE") end
		for _ = 1, 100 do CallHandlers("PLAYER_TARGET_CHANGED") end
		for _ = 1, 50 do TT.OnItem(fake) end
		collectgarbage("collect")
		local grow = collectgarbage("count") - before
		Settle(10)
		if grow >= 256 then return false, string.format("%.0f KB", grow), "< 256 KB" end
		return true, string.format("%.0f KB", grow)
	end)
end

---------------------------------------------------------------------------
-- I. Fehlerzählung und Diagnose
---------------------------------------------------------------------------
local function AreaI(t)
	local function cleanErrors(text)
		local D, s = RM.Diag, RaidMasterDB.gsTest
		for i = #D.errors, 1, -1 do if tostring(D.errors[i].msg):find(text, 1, true) then table.remove(D.errors, i) end end
		for k, e in pairs(s.errors or {}) do if type(e) == "table" and tostring(e.msg):find(text, 1, true) then s.errors[k] = nil end end
	end
	t:Check("T120", "I", "Absichtlicher Fehler wird gezählt", function()
		local s = RaidMasterDB.gsTest
		local D = RM.Diag
		local before = #D.errors
		local msg = "Interface\\AddOns\\RaidMaster\\Test\\Routine.lua:1: RaidMaster-Testfehler"
		local function count()
			local n = 0
			for _, e in pairs(s.errors) do if type(e) == "table" and type(e.msg) == "string" and e.msg:find("RaidMaster-Testfehler", 1, true) then n = n + (e.count or 0) end end
			return n
		end
		return Guard(function()
			-- über den Fehler-Handler des Spiels wie ein echter Fehler (ohne Fehlerfenster: BugSack/Diagnose nehmen ihn auf)
			geterrorhandler()(msg)
			if #D.errors ~= before + 1 and not (D.errors[1] and D.errors[1].msg == msg) then return false, "Diagnose nicht erhöht", "+1" end
			if count() < 1 then return false, "gsTest.errors ohne Eintrag", "1 Eintrag" end
		end, function() cleanErrors("RaidMaster-Testfehler") end)
	end)
	t:Check("T121", "I", "Abgefangene Fehler melden (RM.ReportError)", function()
		local s = RaidMasterDB.gsTest
		return Guard(function()
			RM.ReportError("Diag.provider", "RaidMaster-Testfehler (abgefangen)")
			local found = false
			for _, e in pairs(s.errors) do if type(e) == "table" and e.wo == "Diag.provider" and tostring(e.msg):find("RaidMaster-Testfehler", 1, true) then found = true end end
			if not found then return false, "kein Eintrag", "wo = Diag.provider" end
		end, function() cleanErrors("RaidMaster-Testfehler") end)
	end)
	t:Check("T122", "I", "Doppelte Fehler", function()
		local s = RaidMasterDB.gsTest
		local D = RM.Diag
		local msg = "Interface\\AddOns\\RaidMaster\\Test\\Routine.lua:2: RaidMaster-Testfehler-doppelt"
		return Guard(function()
			for _ = 1, 3 do geterrorhandler()(msg) end
			local inDiag, n = 0, 0
			for _, e in ipairs(D.errors) do if e.msg == msg then inDiag = inDiag + 1; n = e.n end end
			local inGS, count = 0, 0
			for _, e in pairs(s.errors) do
				if type(e) == "table" and tostring(e.msg):find("RaidMaster-Testfehler-doppelt", 1, true) then inGS = inGS + 1; count = e.count or 0 end
			end
			if inDiag ~= 1 or n ~= 3 then return false, "Diagnose " .. inDiag .. " Einträge, n = " .. tostring(n), "1 Eintrag, n = 3" end
			if inGS ~= 1 or count ~= 3 then return false, "gsTest " .. inGS .. " Einträge, count = " .. count, "1 Eintrag, count = 3" end
		end, function() cleanErrors("RaidMaster-Testfehler-doppelt") end)
	end)
	t:Check("T123", "I", "Testberichte warten auf Versand (Anzeige)", function()
		local n = GoldSentinelTest.Pending(RaidMasterDB)
		if type(n) ~= "number" then return false, type(n), "Zahl" end
		return true, n
	end)
end

---------------------------------------------------------------------------
-- J. Regressionstests
---------------------------------------------------------------------------
-- Attrappe für C_TradeSkillUI (moderne Berufe-API) und GetProfessions
local function FakeTradeSkill(window, outputs)
	return {
		IsTradeSkillLinked = function() return false end, IsTradeSkillGuild = function() return false end,
		IsNPCCrafting = function() return false end,
		GetChildProfessionInfo = function() return { professionName = window, skillLevel = 150, maxSkillLevel = 300 } end,
		GetBaseProfessionInfo = function() return { professionName = window } end,
		GetAllRecipeIDs = function() return { 1, 2, 3 } end,
		GetRecipeInfo = function(id) return { name = "Testrezept " .. id, learned = true } end,
		GetRecipeOutputItemData = function(id) return outputs[id] end,
		GetRecipeItemLink = function() return nil end,
		OpenTradeSkill = function() return true end,
		CloseTradeSkill = function() end,
	}
end
local function FakeProfessions(lines)
	local names = { [171] = "Alchimie", [197] = "Schneiderei", [2944] = "Kräuterkunde", [2947] = "Kürschnerei",
		[2943] = "Angeln", [182] = "Kräuterkunde (alt)", [393] = "Kürschnerei (alt)", [356] = "Angeln (alt)", [794] = "Archäologie" }
	return {
		GetProfessions = function() return 1, 2, 3, 4, 5, 6 end,
		GetProfessionInfo = function(i)
			local l = lines[i]
			if l then return names[l] or ("Linie " .. l), "", 150, 300, 0, 0, l end
		end,
	}
end

local function AreaJ(t, G)
	t:Check("T130", "J", "IsClassicEra nur für echtes Era", function()
		return WithFlavor("forever", function()
			if RM.IsClassicEra or not RM.IsModern then return false, "IsClassicEra/IsModern falsch", "false/true" end
		end)
	end)
	t:Check("T131", "J", "Bereitschafts-Check liest Auren modern", function()
		local Rd, L = RM.Ready, RM.L
		local fakeAura = { GetAuraDataByIndex = function(_, i) if i == 1 then return { name = "Fläschchen der Titanen", spellId = 17626 } end end }
		local r = pack(WithFlavor("forever", function()
			return WithAPI({ C_UnitAuras = fakeAura }, { "UnitAura", "UnitBuff" }, function()
				local flask, _, readable = Rd.AuraInfo("player")
				if not readable or not flask then return false, "Fläschchen nicht erkannt", "über C_UnitAuras" end
			end)
		end))
		if r[1] == false then return unpack(r, 1, r.n) end
		return WithAPI(nil, { "UnitAura", "UnitBuff", "C_UnitAuras" }, function()
			local flask, elixirs, readable = Rd.AuraInfo("player")
			local p = table.concat(Rd.Problems("Test", { flask = flask, elixirs = elixirs, noAura = not readable }), " | ")
			if not p:find(L["Buffs nicht lesbar"], 1, true) or p:find(L["kein Fläschchen"], 1, true) then
				return false, p, "\"Buffs nicht lesbar\" (kein stilles return)"
			end
		end)
	end)
	t:Check("T132", "J", "MarkAdds/MarkBoss im Kampf auf modernem Weg", function()
		TestRaid()
		local M, B, L = RM.Markers, RM.BossBar, RM.L
		local u = {}
		local mark0 = ActCount("SetRaidTarget")
		return WithFlavor("forever", function()
			return Guard(function()
				Swap(u, M, "simCombat", true)
				Swap(u, B, "testTarget", nil)
				local hinted = WithPrints(function(lines)
					M.MarkAdds()
					B.MarkBoss(RM.Data.Bosses[663])
					local n = 0
					for _, l in ipairs(lines) do if l == L[M.COMBAT_HINT] then n = n + 1 end end
					return n
				end)
				if hinted < 2 then return false, hinted .. " Hinweise", "2x COMBAT_HINT" end
				if ActCount("SetRaidTarget") ~= mark0 then return false, "Symbol im Kampf gesetzt", "0" end
				Undo(u)
				-- ohne Kampf: gefälschte Namensplaketten mit geschützter GUID bzw. geschütztem Namen
				return WithSecret(function(SECRET)
					local units = {
						nameplate1 = { guid = SECRET, name = "Geheim A" },
						nameplate2 = { guid = "Creature-0-1-2-3-22222-0000000002", name = SECRET },
						nameplate3 = { guid = "Creature-0-1-2-3-22222-0000000003", name = "Normal B" },
						nameplate4 = { guid = "Creature-0-1-2-3-22222-0000000004", name = "Normal C" },
					}
					local start = #R.actUnits
					Swap(u, RM.db.config, "markerTemplate", "standard")    -- Vorlage ohne NPC-Filter
					Swap(u, M, "simSecure", false)                          -- Weg mit RM.Act (WoW Forever: T161)
					return Allow({ "SetRaidTarget" }, function()
						return WithAPI(FakeUnits(units), nil, function()
							M.ResetUsed()
							M.MarkAdds()
							local marked = {}
							for i = start + 1, #R.actUnits do marked[R.actUnits[i]] = true end
							if marked.nameplate1 then return false, "geschützte GUID markiert", "übersprungen (blocked)" end
							if not (marked.nameplate3 and marked.nameplate4) then return false, "lesbare Gegner nicht markiert", "markiert" end
							M.ResetUsed()
						end)
					end)
				end)
			end, function() Undo(u) end)
		end)
	end)
	-- ab 3.0.19: In WoW Forever gehen die RaidMaster-Tasten auf sichere Knöpfe (Makro /tm). Mark/SmartMark aus
	-- Addon-Code setzen dort nie selbst ein Symbol (sonst ADDON_ACTION_FORBIDDEN), sondern geben einen Hinweis.
	t:Check("T133", "J", "Mark/SmartMark im Kampf (Forever: nur sichere Tasten)", function()
		TestRaid()
		local M, L = RM.Markers, RM.L
		local u = {}
		return WithSecret(function(SECRET)
			local units = { mouseover = { guid = "Creature-0-1-2-3-33333-0000000001", name = "Testgegner", icon = SECRET } }
			local fake = FakeUnits(units)
			return Allow({ "SetRaidTarget" }, function()
				return WithFlavor("forever", function()
					return WithAPI(fake, nil, function()
						return Guard(function()
							Swap(u, M, "simCombat", true)
							Swap(u, M, "simSecure", nil)
							if not M.SecureOnly() then return false, "SecureOnly", "true in Forever" end
							local n0 = ActCount("SetRaidTarget")
							M.ResetUsed()
							local hints = WithPrints(function(lines)
								M.Mark(8)
								M.SmartMark()
								local n = 0
								for _, l in ipairs(lines) do if l == L[M.SECURE_HINT] then n = n + 1 end end
								return n
							end)
							local n = ActCount("SetRaidTarget") - n0
							if n ~= 0 then return false, n .. " Aufrufe", "0 (nur sichere Knöpfe)" end
							if hints ~= 2 then return false, hints .. " Hinweise", "2" end
							if M.MarkMacro(8) ~= "/tm [@mouseover,exists][] 8" then return false, M.MarkMacro(8), "/tm-Makro" end
						end, function() Undo(u); M.ResetUsed() end)
					end)
				end)
			end)
		end)
	end)
	t:Client("T133b", "J", "Mouseover-Tasten und Symbol-Leiste im echten Kampf", "Forever: Mob im Kampf per RaidMaster-Taste (Mouseover) und per Klick auf die Symbol-Leiste markieren, Rechtsklick entfernt, 'Alle aus' – Symbol da, Fehlerliste leer, kein 'Aktion blockiert'?")
	t:Check("T134", "J", "Kernhunde-Hilfe ohne Kampflog", function()
		local L = RM.L
		local check = false
		for _, e in ipairs(RM.UI.registry or {}) do
			if e.label == L["Kürschner ansagen, wenn ein Kernhund stirbt"] then check = true end
		end
		if RM.IsModern then
			if RM.Caps.combatLog then return false, "Kampflog an", "aus (moderner Client)" end
			if check then return false, "Haken statt Knopf", "Knopf \"Kürschner ansagen\"" end
			if type(RM.Raid.AnnounceSkinners) ~= "function" then return false, "AnnounceSkinners fehlt", "Funktion" end
			return true, "Knopf (Seite Raid)"
		end
		if RM.Caps.combatLog and not check and RM.UI.pages.raid and RM.UI.pages.raid.frame then
			return false, "Haken fehlt", "Haken (alter Client)"
		end
		return true, "alter Client: Haken"
	end)
	t:Client("T135", "J", "Skillungen in Forever", "/dump GetTalentTabInfo(1) und /dump GetTalentInfo(1,1); Gildenmitglied betrachten")
	t:Check("T136", "J", "Plündermeister fehlt: Tauschliste", function()
		TestRaid()
		local u = {}
		return Guard(function()
			local n = #RM.db.trade
			Swap(u, RM.Caps, "masterLoot", false)
			RM.Test.Real("Deliver")(LINK_EPIC, "Tank1")
			if #RM.db.trade ~= n + 1 then return false, "keine Handelsliste", "AddTrade" end
			RM.Loot.RemoveTrade(#RM.db.trade)
		end, function() Undo(u) end)
	end)
	t:Client("T136b", "J", "Plündermeister vorhanden", "/dump GiveMasterLoot ~= nil, GetMasterLootCandidate ~= nil; /dump C_PartyInfo and C_PartyInfo.GetLootMethod()")
	t:Check("T137", "J", "Namen mit Leerzeichen (Anmeldung)", function()
		local r = RM.Signup.Parse("RAIDMASTER-ANMELDUNG\nTesta Beispiel;PRIEST;Heal;angemeldet")
		if not r or r.list[1].name ~= "Testa Beispiel" then return false, r and tostring(r.list[1].name), "Testa Beispiel" end
	end)
	t:Check("T138", "J", "Bosse Barrow Deeps und Hyjalgipfel", function()
		local due = RM.Now() >= time({ year = 2026, month = 12, day = 9, hour = 0 })
		local P = RM.Data.Pools
		local n = (P.barrow and #(P.barrow.bosses or {}) or 0) + (P.hyjal and #(P.hyjal.bosses or {}) or 0)
		if not due then return true, "vor dem 9. Dezember (" .. n .. " Bosse)" end
		if n == 0 then return false, "8.7 fällig", "Bosse eingetragen" end
	end)
	t:Check("T139", "J", "Interface-Nummer getestet", function()
		if RM.GAME.tested and RM.TOC > RM.GAME.tested then
			return false, "neuere Interface-Nummer als getestet: " .. RM.TOC, ".toc und RM.GAMES ergänzen"
		end
	end)
	t:Check("T140", "J", "Bossleiste: geschützter Zielname", function()
		local B = RM.BossBar
		local tt = B.testTarget
		return WithSecret(function(SECRET)
			return WithAPI({ UnitExists = function(u) return u == "target" end, UnitIsPlayer = function() return false end,
				UnitName = function(u) if u == "target" then return SECRET end end }, nil, function()
				return Guard(function()
					B.testTarget = nil
					local boss = B.TargetBoss()
					if boss ~= nil then return false, "Boss erkannt", "nil" end
					if B.Update then B.Update() end
				end, function() B.testTarget = tt; if B.Update then pcall(B.Update) end end)
			end)
		end)
	end)
	t:Check("T141", "J", "Beute-Datenbank: geschützte GUID", function()
		return WithSecret(function(SECRET)
			if RM.LootDB.ParseGUID(SECRET) ~= nil then return false, "nicht nil", "nil" end
			return WithAPI({ UnitGUID = function(u) if u:find("^boss") then return SECRET end end }, nil, function()
				local ok, err = pcall(RM.LootDB.OnEncounterStart)
				if not ok then return false, tostring(err), "kein Fehler, engaged leer" end
			end)
		end)
	end)
	-- 3.0.18: eigene, sicher unbenutzte Namen. Im Spiel (5. Nov.) gab es in den Daten schon einen Spieler mit genau
	-- dem Vornamen des Testnamens – "!dkp <Vorname>" antwortete darum richtig für genau diesen (gleicher Name geht vor).
	-- Jetzt geprüft: Doppelname ganz, Vorname allein (eindeutig) und gleicher Name geht vor.
	t:Check("T142", "J", "!dkp mit Doppelnamen (Forever-Weg)", function()
		local DKP, cfg = RM.DKP, RM.db.config
		local pool = RM.Test.pool or DKP.ActivePool()
		local players = RM.db.data.players
		local FULL, FIRST = "Zorvak Felsgrund", "Zorvak"
		local saved = { [FULL] = players[FULL], [FIRST] = players[FIRST] }
		for k in pairs(players) do
			if type(k) == "string" and k:lower():match("^(%S+)") == "zorvak" and saved[k] == nil then saved[k] = players[k] end
		end
		local replies = {}
		local origW, was = RM.Whisper, cfg.whisperReplies
		local function Ask(text)
			wipe(replies)
			CallHandlers("CHAT_MSG_WHISPER", text, "Tank1")
			return replies[1] or ""
		end
		return Guard(function()
			cfg.whisperReplies = true
			for k in pairs(saved) do players[k] = nil end
			DKP.EnsurePlayer(FULL, "PRIEST").d[pool] = 40
			RM.Whisper = function(msg) replies[#replies + 1] = msg end
			return WithFlavor("forever", function()
				for _, q in ipairs({ "!dkp Zorvak Felsgrund", "!dkp zorvak felsgrund", "!dkp zorvak" }) do
					local r = Ask(q)
					if not (r:find(FULL, 1, true) and r:find("40", 1, true)) then return false, q .. " -> " .. r, FULL .. " … 40" end
				end
				local s = DKP.Summary("zorvak")
				if not s:find("40", 1, true) then return false, s, "40 über den Vornamen" end
				-- es gibt zusätzlich genau "Zorvak": gleicher Name geht vor, der Doppelname bleibt erreichbar
				DKP.EnsurePlayer(FIRST, "WARRIOR").d[pool] = 25
				local r1, r2 = Ask("!dkp zorvak"), Ask("!dkp Zorvak Felsgrund")
				if not (r1:find("[RaidMaster] Zorvak:", 1, true) and r1:find("25", 1, true)) then return false, r1, "Zorvak … 25" end
				if not (r2:find(FULL, 1, true) and r2:find("40", 1, true)) then return false, r2, FULL .. " … 40" end
				return true, "Doppelname, Vorname, gleicher Name: ok"
			end)
		end, function()
			RM.Whisper = origW; cfg.whisperReplies = was
			players[FULL], players[FIRST] = nil, nil
			for k, v in pairs(saved) do players[k] = v end
		end)
	end)
	t:Check("T143", "J", "Betrachten: geschützte GUID", function()
		TestRaid()
		local Sp = RM.Spec
		return WithSecret(function(SECRET)
			local e, f = CallHandlers("INSPECT_READY", SECRET)
			if e > 0 then return false, f, "kein Fehler" end
			return WithAPI({ UnitGUID = function() return SECRET end }, nil, function()
				for _, g in ipairs({ "Player-1", SECRET }) do
					Sp.scan.current = { name = "Tank1", class = "WARRIOR", unit = "raid2", started = GetTime() }
					local e2, f2 = CallHandlers("INSPECT_READY", g)
					if e2 > 0 then return false, f2, "kein Fehler" end
					if Sp.scan.current ~= nil then return false, "ReadInspect nicht gelaufen", "gelesen und fertig" end
				end
			end)
		end)
	end)
	t:Check("T144", "J", "RM.Short mit geschütztem Namen", function()
		if not (RM.G and RM.G.Short) then return true, "ohne GoldSentinelGame" end
		return WithSecret(function(SECRET)
			if RM.Short(SECRET) ~= nil then return false, "nicht nil", "nil" end
			local ok, err = pcall(function()
				RM.IsRaidLooter(SECRET); RM.GroupUnit(SECRET); RM.IsInMyRaid(SECRET)
			end)
			if not ok then return false, tostring(err), "kein Fehler" end
		end)
	end)
	t:Check("T145", "J", "Berufe: Ausgabe-ID nie nil", function()
		local P = RM.Prof
		local outputs = { [1] = {}, [2] = { hyperlink = "kaputt" } }
		local over = FakeProfessions({ 171 })
		over.C_TradeSkillUI = FakeTradeSkill("Alchimie", outputs)
		return WithFlavor("forever", function()
			return WithAPI(over, nil, function()
				local name, _, _, ids, names = P.ScanModern()
				if not name then return false, "ScanModern nil", "Beruf" end
				if #ids ~= #names or #ids ~= 3 then return false, #ids .. "/" .. #names, "3/3" end
				for i = 1, 3 do if ids[i] ~= 0 then return false, "ID " .. tostring(ids[i]), 0 end end
			end)
		end)
	end)
	t:Client("T146", "J", "Bereitschafts-Check in alten Clients", "Era/Anniversary mit Fläschchen: /rm bereit – erkannt?")
	t:Skip("T147", "J", "Berufe-Knopf übersetzt", "offline geprüft (Locales)")
	t:Check("T148", "J", "Versionsnummer = Code", function()
		local meta = (C_AddOns and C_AddOns.GetAddOnMetadata) or GetAddOnMetadata
		if meta and meta("RaidMaster", "Version") ~= RM.VERSION then return false, tostring(meta("RaidMaster", "Version")), RM.VERSION end
	end)
	t:Check("T149", "J", "Berufe modern aus GetProfessions", function()
		local P = RM.Prof
		local over = FakeProfessions({ 171, 2944, 2947, 2943, 182, 794 })
		over.C_TradeSkillUI = FakeTradeSkill("Alchimie", {})
		return WithFlavor("forever", function()
			return WithAPI(over, nil, function()
				local list = P.Openable()
				if #list ~= 1 or list[1] ~= "Alchimie" then return false, table.concat(list, ", "), "nur Alchimie" end
			end)
		end)
	end)
	t:Check("T150", "J", "Berufe öffnen: OpenTradeSkill zuerst", function()
		local P = RM.Prof
		local over = FakeProfessions({ 171 })
		over.C_TradeSkillUI = FakeTradeSkill("Alchimie", {})
		return Allow({ "OpenTradeSkill", "CastSpellByName" }, function()
			return WithFlavor("forever", function()
				return WithAPI(over, nil, function()
					return Guard(function()
						local cast = ActCount("CastSpellByName")
						P.scanned = {}
						R.actHook.OpenTradeSkill = function() return true end
						P.ReadNext()
						if ActCount("CastSpellByName") ~= cast then return false, "CastSpellByName trotz OpenTradeSkill", 0 end
						P.scanned = {}
						R.actHook.OpenTradeSkill = function() error("OpenTradeSkill geht nicht (Test)") end
						P.ReadNext()
						if CastSpellByName and ActCount("CastSpellByName") ~= cast + 1 then return false, "kein Rückfall", "CastSpellByName 1" end
					end, function() R.actHook.OpenTradeSkill = nil; P.pendingScan = nil; P.scanned = {} end)
				end)
			end)
		end)
	end)
	AsyncCheck(t, "T151", "J", "Listenname als gelesen markieren", function()
		local P = RM.Prof
		local over = FakeProfessions({ 171, 197 })
		over.C_TradeSkillUI = FakeTradeSkill("Alchemy", {})
		local lines = {}
		return KeepDB({ "prof", "recipeMats" }, function()
			return Allow({ "OpenTradeSkill", "CastSpellByName" }, function()
				return WithFlavor("forever", function()
					return WithAPI(over, nil, function()
						return Guard(function()
							P.scanned = {}
							R.actHook.OpenTradeSkill = function(line) lines[#lines + 1] = line; return true end
							P.ReadNext()
							if P.pendingScan ~= "Alchimie" then return false, tostring(P.pendingScan), "Alchimie" end
							CallHandlers("TRADE_SKILL_SHOW")
							Wait(0.8)
							Settle(6)
							if not P.scanned["Alchimie"] then return false, "Alchimie nicht als gelesen gemerkt", "gelesen (Fenster \"Alchemy\")" end
							P.ReadNext()
							if lines[2] ~= 197 then return false, "nächster Klick öffnet " .. tostring(lines[2]), "197 (nächster Beruf)" end
						end, function() R.actHook.OpenTradeSkill = nil; P.pendingScan = nil; P.scanned = {} end)
					end)
				end)
			end)
		end)
	end)
	t:Client("T152", "J", "Berufe-Knopf im Client", "Knopf 'Meine Berufe einlesen' mehrmals, dann /rm berufe")
	t:Check("T153", "J", "Datenformat für ProfessionSentinel", function()
		if RM.db.prof ~= nil and type(RM.db.prof) ~= "table" then return false, type(RM.db.prof), "Tabelle" end
	end)
	t:Check("T154", "J", "GoldSentinelGame Version", function()
		if not G or (tonumber(G.version) or 0) < 2 then return false, tostring(G and G.version), ">= 2" end
	end)
	-- 3.0.21: GoldSentinelTest 2 (Berichte an den Sammler nur mit Zustimmung, anweisung-test-version2.txt)
	t:Check("T162", "J", "GoldSentinelTest Version 2 geladen (T-GT1)", function()
		local v = GoldSentinelTest and GoldSentinelTest.version
		if v ~= 2 and not ((tonumber(v) or 0) > 2) then return false, tostring(v), "2" end
		return true, "Version " .. tostring(v)
	end)
	t:Check("T163", "J", "Ohne Zustimmung nichts im Ausgang (T-GT2)", function()
		local GT = GoldSentinelTest
		if not (GT and GT.Outbox and GT.registry) then return false, "Outbox fehlt", "GoldSentinelTest 2" end
		-- Zustimmung in allen angemeldeten Datenbanken kurz auf "nein", danach wie vorher
		local saved = {}
		for name, reg in pairs(GT.registry) do
			local st = type(reg.db) == "table" and type(reg.db.gsTest) == "table" and reg.db.gsTest.share
			if type(st) == "table" then saved[name] = { st, st.consent } end
		end
		local share = RaidMasterDB.gsTest and RaidMasterDB.gsTest.share
		local before = share and share.outbox and #share.outbox or 0
		return Guard(function()
			for _, v in pairs(saved) do v[1].consent = false end
			if GT.Setting("consent") == true then return false, "Zustimmung noch da", "aus" end
			GT.Outbox(RaidMasterDB, { kind = "fehler", addon = "RaidMaster", version = RM.VERSION, time = 0, env = {},
				errors = { { wo = "Lua", msg = "RaidMaster-Testfehler T163", count = 1 } } })
			local sh = RaidMasterDB.gsTest and RaidMasterDB.gsTest.share
			local after = sh and sh.outbox and #sh.outbox or 0
			if after ~= before then return false, after .. " im Ausgang", before .. " (unverändert)" end
			return true, "Ausgang unverändert (" .. after .. ")"
		end, function()
			for _, v in pairs(saved) do v[1].consent = v[2] end
		end)
	end)

	-- 3.0.23 (Uploader 2.2.0, S8 c): Prüfblock des Uploaders wird beim Laden festgehalten (Beleg für die Übernahme
	-- vor dem Einloggen); falsche Formen werden ignoriert
	t:Check("T165", "J", "Prüfblock des Uploaders wird gelesen (Beleg Abgleich)", function()
		if type(RM.ReadSyncProbe) ~= "function" then return false, "fehlt", "RM.ReadSyncProbe" end
		local db = {}
		local got = RM.ReadSyncProbe(db, { seq = 7, von = "PC", t = 1794380000 })
		if not (got and db.syncProbe and db.syncProbe.seq == 7 and db.syncProbe.von == "PC") then
			return false, tostring(db.syncProbe and db.syncProbe.seq), "seq 7 von PC"
		end
		if math.abs((db.syncProbe.geladen or 0) - time()) > 5 then return false, tostring(db.syncProbe.geladen), "jetzt" end
		local db2 = {}
		if RM.ReadSyncProbe(db2, nil) or RM.ReadSyncProbe(db2, { seq = "x" }) or RM.ReadSyncProbe(db2, "kaputt")
			or db2.syncProbe then
			return false, "falsche Form übernommen", "ignoriert"
		end
		if RaidMasterSyncProbe ~= nil then return false, "Prüfblock noch gesetzt", "nil nach dem Laden" end
		return true, "seq 7 übernommen, falsche Formen ignoriert"
	end)

	-- 3.0.22 (Entscheid des Nutzers 9. Nov.): GoldSentinelSync wird nur mitgebracht (für GoldSentinelTest 2);
	-- RaidMaster meldet nichts an, Gebote/DKP laufen weiter über den eigenen Weg (RAID/GUILD/WHISPER, eigener Takt)
	AsyncCheck(t, "T164", "J", "GoldSentinelSync nur mitgebracht, RaidMaster-Daten wie bisher", function()
		local S = GoldSentinelSync
		if type(S) ~= "table" or (tonumber(S.VERSION) or 0) < 2 then return false, tostring(S and S.VERSION), ">= 2" end
		for prefix, ep in pairs(S.endpoints or {}) do
			if prefix == RM.PREFIX or (type(ep) == "table" and ep.addon == "RaidMaster") then
				return false, "angemeldet: " .. tostring(prefix), "keine RaidMaster-Kennung"
			end
		end
		local u, sent = {}, {}
		local q0 = #(S.queue or {})
		return Guard(function()
			-- nur mitschreiben, nichts wirklich senden
			Swap(u, RM, "SendAddonMessage", function(prefix, msg, dist, target)
				sent[#sent + 1] = { prefix = prefix, msg = msg, dist = dist }
				return true
			end)
			RM.Comm.Send("BID", { a = 0, v = 1, g = 0 }, "WHISPER", "Tank1", true)
			Wait(math.max(0.5, RM.Comm.Pending() * 0.15 + 0.3))
			local ok = false
			for _, m in ipairs(sent) do
				if m.prefix == RM.PREFIX and m.dist == "WHISPER" and tostring(m.msg):find("^BID\t") then ok = true end
			end
			if not ok then return false, #sent .. " gesendet", "BID über RaidMstr/WHISPER" end
			for _, item in ipairs(S.queue or {}) do
				if item.prefix == RM.PREFIX then return false, "Gebot in GoldSentinelSync.queue", "eigener Weg" end
			end
			return true, "Sync " .. S.VERSION .. ", keine Anmeldung, Gebot über RaidMstr (Warteschlange Sync " .. q0 .. ")"
		end, function() Undo(u) end)
	end)

	-- 3.0.19 (Testberichte 8. Nov.: 2× ADDON_ACTION_FORBIDDEN SetRaidTarget nach Klick auf die Leiste): In WoW Forever
	-- ist SetRaidTarget geschützt. Kein Weg aus Addon-Code darf es dort aufrufen; Adds/Boss nur als Vorschlag.
	t:Check("T161", "J", "Symbole in WoW Forever nur über sichere Knöpfe", function()
		TestRaid()
		local M, B, L = RM.Markers, RM.BossBar, RM.L
		local u = {}
		local units = {
			target = { guid = "Creature-0-1-2-3-44444-0000000001", name = "Testboss" },
			nameplate1 = { guid = "Creature-0-1-2-3-44444-0000000002", name = "Testgegner A" },
			nameplate2 = { guid = "Creature-0-1-2-3-44444-0000000003", name = "Testgegner B" },
		}
		local mark0 = ActCount("SetRaidTarget")
		return Allow({ "SetRaidTarget" }, function()
			return WithAPI(FakeUnits(units), nil, function()
				return Guard(function()
					Swap(u, M, "simSecure", true)
					Swap(u, B, "testTarget", nil)
					Swap(u, RM.db.config, "markerTemplate", "standard")
					local lines = WithPrints(function(l)
						M.Mark(8); M.Mark(0); M.SmartMark(); M.ClearAll()
						M.MarkAdds()
						B.MarkBoss(RM.Data.Bosses[663])
						return l
					end)
					Settle(1)
					if ActCount("SetRaidTarget") ~= mark0 then return false, (ActCount("SetRaidTarget") - mark0) .. " Aufrufe", "0" end
					local hint, suggest = 0, 0
					local prefix = string.format(L["Vorschlag (Vorlage: %s): %s"], "\001", ""):match("^(.-)\001") or "?"
					for _, l in ipairs(lines) do
						if l == L[M.SECURE_HINT] then hint = hint + 1 end
						if l:sub(1, #prefix) == prefix then suggest = suggest + 1 end
					end
					if hint ~= 4 then return false, hint .. " Hinweise", "4 (Mark, Entfernen, Auto, Alle aus)" end
					if suggest < 1 then return false, suggest .. " Vorschläge", ">= 1 (Adds markieren)" end
					local lines9 = select(2, M.CLEAR_ALL_MACRO:gsub("\n", "\n")) + 1
					if lines9 ~= 9 or not M.CLEAR_ALL_MACRO:find("/tm [@player] 0", 1, true) then return false, "Alle-aus-Makro", "9 Zeilen, endet mit 0" end
					local n = 0
					for binding in pairs(M.KEY_MAP) do
						n = n + 1
						if type(_G["BINDING_NAME_" .. binding]) ~= "string" then return false, "Taste " .. binding, "in Bindings.xml" end
					end
					if n ~= 11 then return false, n .. " Tasten", "11 (8 Symbole, Entfernen, Auto, Alle aus)" end
					-- im echten Forever-Client: die unsichtbaren Tasten-Knöpfe gibt es nach dem Einloggen
					local kb = RM.IsModern and _G.RaidMasterKeyMark8
					if type(kb) == "table" and type(kb.GetAttribute) == "function" then
						local mt = kb:GetAttribute("macrotext")
						if mt ~= nil and mt ~= M.MarkMacro(8) then return false, tostring(mt), M.MarkMacro(8) end
					end
					return true, "0 Aufrufe, " .. hint .. " Hinweise, " .. suggest .. " Vorschläge"
				end, function() Undo(u); M.ResetUsed() end)
			end)
		end)
	end)
end

---------------------------------------------------------------------------
-- K. Oberfläche im echten Client (UICheck.lua, ab 3.0.18) – nur lesen, nichts verändern
-- Öffnet das Hauptfenster und zeigt jede erlaubte Seite einmal, damit ihre Knöpfe und Tooltips geprüft werden;
-- danach Seite und Fenster wie vorher. Ohne echten Client ehrlich übersprungen, nie als OK gezählt.
---------------------------------------------------------------------------
local function AreaK(t)
	local U, UI = RM.UICheck, RM.UI
	local ui = {
		{ "T155", "Eigene Tooltips verdecken keine Knöpfe", "TooltipsCoverNothing" },
		{ "T156", "Kein Überlappen mit Blizzard- oder GoldSentinel-Fenstern", "WindowsOverlapNothing" },
		{ "T157", "Fenster und Tooltips ganz im Bildschirm", "InsideScreen" },
		{ "T158", "Beschriftungen von Knöpfen nicht abgeschnitten", "TextFits" },
		{ "T159", "Angezeigte Spielwerte plausibel", "ValuesPlausible", true },
		{ "T160", "Keine Fehlerschleife (gleiche Meldung > 10×)", "NoErrorLoops", true },
	}
	if not U then
		for _, c in ipairs(ui) do t:Skip(c[1], "K", c[2], "UICheck.lua fehlt") end
		return
	end
	local main = UI.main
	local wasShown = main and main:IsShown()
	local wasPage = main and main.current
	if not wasShown then pcall(UI.Open) end
	main = UI.main
	-- alle Seiten, die du sehen darfst: Probleme sammeln (je Fall), danach eine Zeile je Fall
	local found, tested, hints, infos = {}, {}, {}, {}
	for _, c in ipairs(ui) do found[c[1]], tested[c[1]], hints[c[1]] = {}, 0, {} end
	local function Collect(c, prefix)
		local ok, problems, n, extra = pcall(U[c[3]])
		if not ok then problems, n = { "Lua-Fehler " .. tostring(problems) }, 0 end
		for _, p in ipairs(problems or {}) do
			local line = (prefix and (prefix .. ": ") or "") .. p
			local dup = false
			for _, q in ipairs(found[c[1]]) do if q == line then dup = true break end end
			if not dup and #found[c[1]] < 25 then found[c[1]][#found[c[1]] + 1] = line end
		end
		tested[c[1]] = tested[c[1]] + (tonumber(n) or 0)
		for _, h in ipairs(c[4] and {} or (extra or {})) do if #hints[c[1]] < 10 then hints[c[1]][#hints[c[1]] + 1] = h end end
		if c[4] and extra then infos[c[1]] = extra end
	end
	local available = U.Available()
	if available and main and UI.pageOrder then
		for _, id in ipairs(UI.pageOrder) do
			if UI.CanSeePage(id) and not RM.InCombat() then
				pcall(UI.ShowPage, id)
				for _, c in ipairs(ui) do if not c[4] then Collect(c, id) end end
			end
		end
	end
	for _, c in ipairs(ui) do if c[4] then Collect(c) end end
	-- Seite und Fenster wie vorher
	if main then
		if wasPage then pcall(UI.ShowPage, wasPage) end
		if not wasShown then main:Hide() end
	end
	if GameTooltip and GameTooltip.Hide then GameTooltip:Hide() end
	for _, c in ipairs(ui) do
		if not c[4] and not available then
			t:Skip(c[1], "K", c[2], "nur im echten Client (Fenster, Rechtecke, Tooltip)")
		elseif not c[4] and tested[c[1]] == 0 and #found[c[1]] == 0 then
			t:Skip(c[1], "K", c[2], "nichts geprüft (kein sichtbares Fenster mit messbaren Rechtecken)")
		else
			t:Check(c[1], "K", c[2], function()
				local p = found[c[1]]
				local info = (#p == 0 and "keine" or table.concat(p, "; ")) .. " · geprüft " .. tested[c[1]]
				if #hints[c[1]] > 0 then info = info .. " · Hinweise: " .. table.concat(hints[c[1]], "; ") end
				if infos[c[1]] and #infos[c[1]] > 0 then info = info .. " · " .. table.concat(infos[c[1]], ", ") end
				return #p == 0, info, "keine"
			end)
		end
	end
end

local RUNNERS = { A = AreaA, B = AreaB, C = AreaC, D = AreaD, E = AreaE, F = AreaF, G = AreaG, H = AreaH, I = AreaI, J = AreaJ, K = AreaK }

---------------------------------------------------------------------------
-- Ablauf
---------------------------------------------------------------------------
local function Say(msg) RM.Print("Testroutine: " .. msg) end

-- kurzer Zustand für "hängt" (ohne Namen)
local function DiagShort()
	local T, A = RM.Test, RM.Auction
	return string.format("Testmodus %s, Durchlauf %s, Versteigerung %s, Warteschlange %d, Comm %d",
		T.active and "an" or "aus", T.IsRunning() and "läuft" or "nein", A.current and (A.current.finished and "fertig" or "läuft") or "keine",
		#A.queue, RM.Comm.Pending and RM.Comm.Pending() or 0)
end

local StartJob

local function NextAfterError(token, job, err)
	R.t:Check("X" .. job.area, job.area, "Bereich " .. job.name .. " abgebrochen", function() error(err, 0) end)
end

local function Resume(token, ...)
	if R.token ~= token then return end
	local res = pack(coroutine.resume(R.co, ...))
	if R.token ~= token then return end
	local job = R.jobs[R.jobIndex]
	if not res[1] then
		NextAfterError(token, job, res[2])
		return StartJob(token, R.jobIndex + 1)
	end
	if coroutine.status(R.co) == "dead" then return StartJob(token, R.jobIndex + 1) end
	local sec = (res[2] == "wait") and tonumber(res[3]) or 0
	C_Timer.After(math.max(0, sec), function() Resume(token) end)
end

function StartJob(token, i)
	if R.token ~= token then return end
	R.jobIndex = i
	local job = R.jobs[i]
	if not job then return R.Finish() end
	R.current = job.area
	R.co = coroutine.create(job.fn)
	return Resume(token)
end

-- Kampf begonnen oder Zeit überschritten: sofort abbrechen, alles zurücksetzen
function R.Abort(reason, timeout)
	if not R.running or not R.token then return end
	R.token = nil
	local job = R.jobs and R.jobs[R.jobIndex]
	if timeout then
		local where = tostring(R.current)
		R.t:Check("XT", job and job.area or "A", "Routine hängt", function()
			return false, "hängt bei " .. where .. " – " .. DiagShort(), "fertig in " .. (R.long and R.LIMIT_LONG or R.LIMIT) .. " s"
		end)
	end
	-- offene Wartezeiten aufräumen; was der abgebrochene Bereich selbst wiederhergestellt hätte (KeepDB), kommt aus der
	-- Sicherung vom Start (gleiche Tabellen, Inhalt ersetzt)
	pcall(function() wipe(RM.API.over); wipe(RM.API.hide) end)
	pcall(function()
		local db = RaidMasterDB
		for _, k in ipairs(EXTRA_KEYS) do
			local v = R.snap.db[k]
			if v == nil then db[k] = nil
			elseif type(v) == "table" and type(db[k]) == "table" then Replace(db[k], v)
			else db[k] = Deep(v) end
		end
	end)
	RM.simCombat = false
	R.actHook = {}
	for i = R.jobIndex or 1, #(R.jobs or {}) do
		local j = R.jobs[i]
		if j.area then R.t:Skip("R" .. j.area, j.area, "Rest von Bereich " .. j.name, reason) end
	end
	R.Finish(true)
end

RM.On("PLAYER_REGEN_DISABLED", function()
	if R.running then R.Abort("Kampf begonnen") end
end)

function R.Run(only)
	local T = RM.Test
	if not RM.IsDev() then RM.RequireDev() return end
	if not (T and RM.db and GoldSentinelTest) then Say("Test-Werkzeug oder GoldSentinelTest fehlt.") return end
	if R.running then Say("läuft schon.") return end
	if R.graceUntil and GetTime() < R.graceUntil then Say("bitte noch einen Moment warten (Nachlauf des letzten Abbruchs).") return end
	local inCombat = RM.InCombat() or (IsEncounterInProgress and IsEncounterInProgress())
	if inCombat then Say("nur außerhalb des Kampfes.") return end
	if T.IsRunning and T.IsRunning() then Say("erst den Test-Durchlauf beenden.") return end
	if T.active then Say("erst den Testmodus beenden (die Routine startet ihn selbst und stellt danach alles zurück).") return end
	only = only and only:upper() or nil
	R.long = only == "LANG"
	if only == "LANG" then only = nil end
	if only and not RUNNERS[only] then Say("Bereich " .. only .. " gibt es nicht (A … K).") return end

	HookActions()
	wipe(realCount)
	local G = RM.G
	local snap = Snapshot()
	R.snap = snap
	R.only = only
	R.testDBnilBefore = snap.testDBnil
	R.profTable = RM.db.prof
	R.diagBefore = #RM.Diag.errors
	R.settleUntil = 0
	R.blockedErrors = {}
	for k, e in pairs((RaidMasterDB.gsTest and RaidMasterDB.gsTest.errors) or {}) do
		if type(e) == "table" and (e.wo == "ADDON_ACTION_BLOCKED" or e.wo == "ADDON_ACTION_FORBIDDEN") then R.blockedErrors[k] = e.count or 0 end
	end
	R.keep = { whisper = RM.Whisper, isSecret = RM.IsSecret, short = RM.Short, read = RM.BossBar.ReadTarget,
		tt = RM.BossBar.testTarget, sim = RM.Markers.simCombat, offset = RM.timeOffset, print = RM.Print,
		gIsSecret = G and G.IsSecret, flavor = G and G.flavor, isDev = RM.IsDev, db = RM.db, caps = Deep(RM.Caps),
		sendAddon = RM.SendAddonMessage, raidAuth = RM.IsRaidAuthority, report = RM.UI.ReportError, gst = GetServerTime,
		adLast = RM.Ad.lastPost, viewGuild = RM.UI.viewGuild, role = T.role, pool = T.pool, autoAuction = T.autoAuction,
		weekly = T.weekly }
	R.lastText = nil
	R.running = true
	R.finished = false
	R.unwatch = WatchLocale()
	R.t = GoldSentinelTest.Begin("RaidMaster", RM.VERSION, RaidMasterDB)
	local t = R.t
	t.Wait = function(_, sec) return Wait(sec) end          -- T:Wait (asynchrones Warten) für die Prüfungen
	InstallSpies()

	-- Vorbereitung: Testmodus ohne Countdown, ohne automatischen Durchlauf, ohne automatische Vergabe
	local ok, err = pcall(function()
		T.SetAutoSend(false)
		T.SetFollowStart(false)
		T.SetAutoAward(false)
		if type(RaidMasterTestOptions) == "table" then RaidMasterTestOptions.auctionSec = 3 end
		T.Start()
		if not T.active then error("Testmodus ließ sich nicht starten") end
	end)
	R.jobs = {}
	if ok then
		for _, a in ipairs(AREA_ORDER) do
			if not only or only == a then
				R.jobs[#R.jobs + 1] = { area = a, name = AREAS[a], fn = function()
					-- was der Testmodus nicht sichert, stellt jeder Bereich selbst wieder her
					return KeepDB(EXTRA_KEYS, function() return RUNNERS[a](t, G) end)
				end }
			end
		end
	else
		t:Check("X0", "A", "Routine abgebrochen", function() error(err, 0) end)
	end
	-- Nachlauf: verzögerte Aktionen (Timer von Raidstart, Ansagen, Berufe …) laufen noch im Testmodus ab
	R.jobs[#R.jobs + 1] = { name = "Nachlauf", fn = function()
		local left = (R.settleUntil or 0) - GetTime()
		if left > 0 then Wait(left + 0.5) end
		local n = 0
		while RM.Comm.Pending and RM.Comm.Pending() > 0 and n < 20 do Wait(0.5); n = n + 1 end
	end }

	local token = {}
	R.token = token
	local limit = R.long and R.LIMIT_LONG or R.LIMIT
	C_Timer.After(limit, function() if R.token == token then R.Abort("Zeitüberschreitung", true) end end)
	Say(string.format("läuft (höchstens %d s) …", limit))
	StartJob(token, 1)
	return R.lastText
end

-- Abschluss: Testmodus beenden, Sandbox prüfen, Bericht. Geschützt: wirft etwas, bleibt R.running nie gesetzt.
function R.Finish(aborted)
	if R.finished then return end
	R.finished = true
	R.token = nil
	local T = RM.Test
	local G = RM.G
	local t = R.t
	local keep = R.keep
	local snap = R.snap
	local only = R.only
	pcall(R.unwatch)
	-- aufräumen, auch nach Fehler (laufende Einladungen, Suche, Timer zuerst – danach wären sie echt)
	if RM.Signup.IsInviting() then pcall(RM.Signup.StopInvites) end
	if RM.Gaps.search then pcall(RM.Gaps.StopSearch) end
	if T.IsRunning() then pcall(T.StopRun) end
	if RM.Timer.active or RM.Raid.pauseUntil then pcall(RM.Timer.Cancel) end
	pcall(RM.Spec.StopScan)
	pcall(T.Stop)
	RM.Ad.lastPost, RM.UI.viewGuild = keep.adLast, keep.viewGuild
	T.role, T.pool, T.autoAuction, T.weekly = keep.role, keep.pool, keep.autoAuction, keep.weekly
	RM.Comm.handlers.GSTEST = nil
	RM.Comm.versions.Tank1 = nil
	RM.Whisper, RM.IsSecret, RM.Short, RM.Print = keep.whisper, keep.isSecret, keep.short, keep.print
	RM.BossBar.ReadTarget, RM.BossBar.testTarget = keep.read, keep.tt
	RM.Markers.simCombat, RM.timeOffset = keep.sim, keep.offset or 0
	RM.IsDev, RM.db, RM.IsRaidAuthority, RM.UI.ReportError = keep.isDev, keep.db, keep.raidAuth, keep.report
	RM.simCombat = false
	wipe(RM.API.over); wipe(RM.API.hide)
	for k, v in pairs(keep.caps) do RM.Caps[k] = v end
	RM.Loot.pendingBoss = nil              -- keine "noch nicht geplündert"-Erinnerung für Testbosse
	if RM.Ready.window then pcall(RM.Ready.window.Hide, RM.Ready.window) end   -- Ergebnisliste der Testspieler
	if RaidMasterTest ~= T then RaidMasterTest = T end
	if G then
		if keep.gIsSecret then G.IsSecret = keep.gIsSecret end
		if G.SetTestFlavor then G.SetTestFlavor(nil) end
		RM.SetGameFlags()
	end
	RaidMasterTestOptions = snap.opts

	local blocked, realN, actList = RM.Test.blocked or 0, 0, ""
	local sandbox = "?"
	local okEnd, errEnd = pcall(function()
		-- Sprache: Schlüssel, die auf Deutsch zurückfielen
		if not only or only == "F" then
			if RM.LOCALE == "deDE" or GetLocale() == "deDE" then
				t:Skip("T90", "F", "Fehlende Übersetzungen", "Grundsprache")
			else
				local list = {}
				for k in pairs(missing or {}) do if k:find("[%z\128-\255]") or k:find(" ") then list[#list + 1] = k end end
				table.sort(list)
				t:Check("T90", "F", "Fehlende Übersetzungen", function()
					if #list > 0 then return false, #list .. ": " .. table.concat(list, " | "):sub(1, 250), "0" end
				end)
			end
		end
		missing = nil

		-- T59: gesperrte Aktionen des Spiels während der Routine (GoldSentinelTest zählt ADDON_ACTION_BLOCKED/FORBIDDEN)
		if not only or only == "C" then
			t:Check("T59", "C", "Gesperrte Aktionen im Spiel", function()
				local new = 0
				for k, e in pairs((RaidMasterDB.gsTest and RaidMasterDB.gsTest.errors) or {}) do
					if type(e) == "table" and (e.wo == "ADDON_ACTION_BLOCKED" or e.wo == "ADDON_ACTION_FORBIDDEN") then
						new = new + (e.count or 0) - (R.blockedErrors[k] or 0)
					end
				end
				if new > 0 then return false, new .. " neue Einträge", "0" end
			end)
		end

		-- T70: ganze Routine im alten Client (0 FEHLER in A, B, E, F, G, I)
		if not only or only == "D" then
			if RM.IsModern then
				t:Skip("T70", "D", "Ganze Routine im alten Client", "nur im alten Client (Era/TBC): dort /rmtest testroutine")
			elseif only == "D" then
				t:Client("T70", "D", "Ganze Routine im alten Client", "/rmtest testroutine ohne Bereich im alten Client laufen lassen")
			else
				local bad = {}
				for _, e in ipairs(t.results or {}) do
					if e.status == "FEHLER" and ({ A = true, B = true, E = true, F = true, G = true, I = true })[e.bereich] then bad[#bad + 1] = e.id end
				end
				t:Check("T70", "D", "Ganze Routine im alten Client", function()
					if #bad > 0 then return false, table.concat(bad, ", "), "0 FEHLER in A, B, E, F, G, I" end
				end)
			end
		end

		-- Sandbox
		local diff = Compare(snap)
		sandbox = "OK"
		if #diff > 0 then
			sandbox = "ABWEICHUNG: " .. table.concat(diff, ", ")
			RestoreSnapshot(snap)
		end
		blocked = RM.Test.blocked or 0
		t:Check("SB", "A", "echte Daten unverändert", function()
			if #diff > 0 then return false, sandbox, "OK (wiederhergestellt)" end
			if RM.db ~= RaidMasterDB then return false, "RM.db getauscht", "RaidMasterDB" end
			if RM.db.testMode ~= nil then return false, "testMode übrig", "nil" end
			-- RaidMasterTestDB nur prüfen, wenn es vor dem Lauf nil war (sonst falscher FEHLER)
			if R.testDBnilBefore and RaidMasterTestDB ~= nil then return false, "RaidMasterTestDB übrig", "nil" end
			if G and G.flavor ~= keep.flavor then return false, "Testflavor " .. tostring(G.flavor), tostring(keep.flavor) end
			if RM.Whisper ~= keep.whisper or RM.IsSecret ~= keep.isSecret or RM.BossBar.ReadTarget ~= keep.read
				or RM.SendAddonMessage ~= keep.sendAddon or GetServerTime ~= keep.gst then
				return false, "Funktion nicht zurückgesetzt", "identisch"
			end
			if next(RM.API.over) or next(RM.API.hide) or RM.simCombat then return false, "RM.API/simCombat übrig", "leer" end
			if R.profTable and RM.db.prof ~= R.profTable then return false, "RM.db.prof ersetzt", "gleiche Tabelle" end
		end)
		local realList
		realN, realList = RealTotal()
		local parts = {}
		for _, n in ipairs(RM.ACT_NAMES) do if (R.act[n] or 0) > 0 then parts[#parts + 1] = n .. " " .. R.act[n] end end
		actList = table.concat(parts, ", ")
		t:Check("T46b", "B", "Sperrgitter: echte Aktionen während der Routine", function()
			if realN > 0 then return false, realList, "0" end
			local bad = {}
			for _, n in ipairs(RM.ACT_NAMES) do
				local extra = (R.act[n] or 0) - (R.allowed[n] or 0)
				if n ~= "SetRaidTarget" and extra > 0 then bad[#bad + 1] = n .. " " .. extra end
			end
			if #bad > 0 then return false, "über RM.Act ohne Testmodus-Umleitung: " .. table.concat(bad, ", "), "0" end
			-- Schlachtzugsymbole nur auf Testeinheiten (und nur gezählt, nie gesetzt)
			for _, unit in ipairs(R.actUnits) do
				if not (unit == "player" or unit == "mouseover" or unit == "target" or unit:match("^nameplate%d+$")) then
					return false, "Symbol auf " .. unit, "nur player/mouseover/target/nameplateN"
				end
			end
			return true, actList ~= "" and ("über RM.Act abgefangen: " .. actList) or "keine"
		end)
	end)
	if not okEnd then
		sandbox = "Abschluss abgebrochen: " .. tostring(errEnd)
		t:Check("X1", "A", "Abschluss der Routine", function() error(errEnd, 0) end)
	end

	local text = t:Finish({ sandbox = sandbox, fehlerzaehler = R.diagBefore .. " -> " .. #RM.Diag.errors, locale = RM.LOCALE,
		testflavor_ende = G and tostring(G.flavor) or "-", blocked = blocked, echte_aktionen = realN, abgefangen = actList,
		bereich = only or (R.long and "alle (lang)" or "alle"), abbruch = aborted and "ja" or nil })
	text = text .. "\n\nBericht gespeichert – wird beim nächsten /reload oder Ausloggen an die Prüfung gemeldet."
		.. "\nNach der Testroutine bitte /reload (Knopf \"Neu laden und melden\")."
	R.lastText = text
	R.running = false
	-- Spion abbauen; nach einem Abbruch erst nach einer Nachlaufzeit (verzögerte Aktionen bleiben abgefangen)
	if aborted then
		R.graceUntil = GetTime() + R.GRACE
		local origSend = RM.SendAddonMessage
		RM.SendAddonMessage = function() end
		C_Timer.After(R.GRACE, function()
			if RM.SendAddonMessage ~= origSend then RM.SendAddonMessage = origSend end
			RemoveSpies()
			R.graceUntil = nil
		end)
	else
		RemoveSpies()
	end
	pcall(RM.UI.ShowExport, text, { "Neu laden und melden", function() RM.Act.ReloadUI() end })
	Say("fertig. Bericht gespeichert – wird beim nächsten /reload oder Ausloggen an die Prüfung gemeldet. Bitte /reload.")
	return text
end

-- Diagnose: Anzahl der Berichte, die auf den Uploader warten (nur für den Entwickler)
if RM.Diag and RM.Diag.providers then
	table.insert(RM.Diag.providers, function()
		if not (RM.IsDev() and GoldSentinelTest and GoldSentinelTest.Pending and RaidMasterDB) then return {} end
		return { "Testberichte warten auf Versand: " .. GoldSentinelTest.Pending(RaidMasterDB) }
	end)
end
