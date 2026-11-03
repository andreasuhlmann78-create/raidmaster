-- ============================================================================
-- RaidMaster – Testroutine ("Alles testen", /rmtest testroutine, /rm testroutine)
--
-- Nur für den Entwickler (RM.IsDev), wie das ganze Test-Werkzeug. Prüft RaidMaster automatisch und schreibt einen
-- Bericht über GoldSentinelTest (gemeinsame Datei): OK / FEHLER / ÜBERSPRUNGEN / IM CLIENT PRÜFEN.
-- Der Bericht landet im Kopierfenster und in RaidMasterDB.gsTest; der RaidMasterUploader schickt ihn beim nächsten
-- /reload oder Ausloggen an die Prüfung.
--
-- Regeln (auftraege/RaidMaster/testroutine-raidmaster.txt, nachtrag-testroutinen.txt):
--   * keine Blizzard-Funktion wird ersetzt – auch nicht vorübergehend. Ersetzt werden nur Felder von RaidMaster
--     (z. B. RM.BossBar.ReadTarget, RM.IsSecret, RM.Whisper). Echte Aktionen werden nur über hooksecurefunc GEZÄHLT.
--   * echte Daten unverändert: Sicherung vorher, Tiefenvergleich nachher, bei Abweichung wiederherstellen.
--   * nichts mit echten Folgen: die Fachprüfungen laufen im Testmodus (Umleitung von Chat und Addon-Nachrichten).
--   * die Routine läuft in einem Zug (kein Warten), darum kann währenddessen kein Kampf beginnen.
-- Lädt vor Test\Test.lua (Test.lua muss die letzte Datei bleiben) und benutzt RM.Test erst beim Start.
-- ============================================================================

local ADDON, NS = ...
local RM = (type(NS) == "table" and NS.UI and NS) or RaidMaster
if not RM then return end

local R = { running = false }
RM.TestRoutine = R

local AREAS = { A = "Laden und Erkennung", B = "Funktionen", C = "Forever-Sonderfälle", D = "Alte Clients", E = "Daten",
	F = "Sprachen", G = "Zusammenspiel", H = "Leistung", I = "Fehlerzählung", J = "Regressionstests" }
local AREA_ORDER = { "A", "B", "C", "D", "E", "F", "G", "H", "I", "J" }

---------------------------------------------------------------------------
-- Echte Aktionen zählen (Sperrgitter T46): nur mitzählen über hooksecurefunc, nie ersetzen
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
		"GiveMasterLoot", "DoReadyCheck", "Screenshot", "SetLootMethod", "InitiateTrade" }
	for _, n in ipairs(globals) do
		if type(_G[n]) == "function" then pcall(hooksecurefunc, n, counter(n)) end
	end
	local tables = {
		{ "C_PartyInfo", { "InviteUnit", "ConvertToRaid", "SetLootMethod", "DoCountdown" } },
		{ "C_ChatInfo", { "SendChatMessage" } },
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
-- Hilfen für die Prüfungen
---------------------------------------------------------------------------
-- Schutzblock: Körper ausführen, danach IMMER aufräumen, Fehler weitergeben
local function Guard(body, cleanup)
	local ok, a, b, c = pcall(body)
	pcall(cleanup)
	if not ok then error(a, 0) end
	return a, b, c
end

-- geschützter Wert: Köder des Test-Werkzeugs (RM.Test.MakeSecret) – RM.IsSecret wird im Schutzblock umhüllt
local function WithSecret(body)
	local SECRET = RM.Test.MakeSecret()
	local orig = RM.IsSecret
	RM.IsSecret = function(v) return rawequal(v, SECRET) or orig(v) end
	return Guard(function() return body(SECRET) end, function() RM.IsSecret = orig end)
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
	return Guard(function()
		G.SetTestFlavor(flavor)
		RM.SetGameFlags()
		return body()
	end, function()
		G.SetTestFlavor(nil)
		RM.SetGameFlags()
	end)
end

local function Count(t) local n = 0; for _ in pairs(t or {}) do n = n + 1 end; return n end

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
-- Die Prüfungen
---------------------------------------------------------------------------
local OPEN = "in 3.0.15 noch nicht umgesetzt (folgt nach dem Launch)"
local ASYNC = "in 3.0.15 noch nicht umgesetzt (asynchrone Prüfung, braucht Koroutine/Wartezeiten)"

local function AreaA(t, G)
	t:Check("T01", "A", "Alle Dateien geladen", function()
		local need = { "Data", "Comm", "Spec", "DKP", "Raid", "Loot", "Auction", "Signup", "PUG", "Ad", "Assign", "Markers",
			"Tranq", "Sheep", "Donate", "UI", "Guide", "Diag", "ItemTip", "BossBar", "Gaps", "LootDB", "Tooltip", "Ready",
			"Timer", "Prof", "Welcome", "Records", "Bank", "Test", "frame", "L", "LOCALE" }
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
			expect("forever", RM.SameName("Rokan Steinwacht", "rokan") and not RM.SameName("Rokan Steinwacht", "Rokan Eisen"), "SameName")
			expect("forever", RM.Markers.CombatBlocked() == G.InCombat(), "CombatBlocked")
		end)
		WithFlavor("era", function()
			expect("era", RM.GAME.key == "era" and RM.IsClassicEra and not RM.IsModern, "Flaggen")
			expect("era", not RM.SameName("Rokan Steinwacht", "Rokan"), "SameName")
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

local function AreaB(t, G)
	local T = RM.Test
	local DKP = RM.DKP
	for _, id in ipairs({ "T10", "T11", "T12", "T13", "T14" }) do t:Skip(id, "B", "Oberfläche/Slash", OPEN) end
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
		DKP.ChargeItem("Tank1", 30, "|cffa335ee|Hitem:16800::::::::60:::::|h[Testgegenstand]|h|r", pool)
		if DKP.Get("Tank1", pool) ~= 120 then return false, DKP.Get("Tank1", pool), 120 end
		local s = DKP.Summary("Tank1")
		if not s:find("120", 1, true) then return false, s, "enthält 120" end
		local sorted = DKP.SortedPlayers(pool)
		for i = 2, #sorted do
			local a, b = sorted[i - 1], sorted[i]
			local va = type(a) == "table" and (a.dkp or a.v or a[2]) or nil
			local vb = type(b) == "table" and (b.dkp or b.v or b[2]) or nil
			if type(va) == "number" and type(vb) == "number" and va < vb then return false, "nicht absteigend", "absteigend" end
		end
		return true, "150/130/150/120"
	end)
	for _, id in ipairs({ "T16", "T17", "T18" }) do t:Skip(id, "B", "DKP/Raid", OPEN) end
	for _, id in ipairs({ "T19", "T20" }) do t:Skip(id, "B", "Versteigerung", ASYNC) end
	t:Skip("T21", "B", "Loot-Regeln und Verteilung", OPEN)
	t:Check("T22", "B", "Anmeldungen importieren (Parse)", function()
		local text = table.concat({ "RAIDMASTER-ANMELDUNG", "Raid: MC", "Datum: 05.11.", "Modus: dkp", "Topf: mc", "Max: 40",
			"Start: 1793901600", "Tank1;WARRIOR;Tank;angemeldet", "Rokan Steinwacht;PRIEST;Heal;angemeldet",
			"Ersatz1;WARRIOR;DD;ersatz", "GRP;Tank1;1", "BANK;Ersatz1", "ALT;Twinky;Tank1" }, "\n")
		local r = RM.Signup.Parse(text)
		if not r then return false, "nil", "Ergebnis" end
		if #r.list ~= 3 then return false, #r.list .. " Einträge", 3 end
		if r.list[2].name ~= "Rokan Steinwacht" then return false, tostring(r.list[2].name), "Rokan Steinwacht" end
		if r.pool ~= "mc" or r.max ~= 40 or r.start ~= 1793901600 then return false, tostring(r.pool) .. "/" .. tostring(r.max), "mc/40/Start" end
		if not (r.groups and r.groups.Tank1 == 1 and r.bench and r.bench.Ersatz1 and r.alts and r.alts.Twinky == "Tank1") then
			return false, "GRP/BANK/ALT fehlen", "vorhanden"
		end
		local none, err = RM.Signup.Parse("Hallo")
		if none ~= nil or type(err) ~= "string" then return false, "kein Fehlertext", "nil + Fehlertext" end
	end)
	for _, id in ipairs({ "T23", "T28", "T29", "T30", "T31" }) do t:Skip(id, "B", "Ablauf mit Wartezeit", ASYNC) end
	for _, id in ipairs({ "T24", "T25", "T26", "T27" }) do t:Skip(id, "B", "Chat/Markierungen", OPEN) end
	t:Check("T32", "B", "Rekorde: Zeitformat", function()
		local s = RM.Records.FormatTime(102)
		if s ~= "1:42" then return false, s, "1:42" end
	end)
	t:Check("T33", "B", "Beute-Datenbank: GUID zerlegen", function()
		local kind, id = RM.LootDB.ParseGUID("Creature-0-1234-409-5678-11502-0000ABCDEF")
		if kind ~= "Creature" or id ~= 11502 then return false, tostring(kind) .. " " .. tostring(id), "Creature 11502" end
	end)
	for _, id in ipairs({ "T34", "T35", "T36" }) do t:Skip(id, "B", "Tooltips/Berufe/Bank", OPEN) end
	t:Check("T37", "B", "Skillungen: Hauptbaum", function()
		if RM.Spec.MainTree({ 5, 5, 41 }) ~= 3 then return false, tostring(RM.Spec.MainTree({ 5, 5, 41 })), 3 end
		if RM.Spec.MainTree({ 0, 0, 0 }) ~= nil then return false, "Baum bei 0 Punkten", "nil" end
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
	for _, id in ipairs({ "T39", "T40", "T41" }) do t:Skip(id, "B", "Kommunikation/Diagnose", OPEN) end
	t:Check("T42", "B", "Raiddaten dieser Version", function()
		local D = RM.Data
		if #D.RaidList == 0 then return false, 0, "> 0 Raids" end
		local noInfo = 0
		for _, id in ipairs(D.BossOrder) do if not D.BossInfo[id] then noInfo = noInfo + 1 end end
		if noInfo > 0 then return false, noInfo .. " Boss-Taktiken fehlen", "vollständig" end
		if not D.GetTemplate("standard") then return false, "Vorlage standard fehlt", "vorhanden" end
		return true, #D.RaidList .. " Raids, " .. #D.BossOrder .. " Bosse"
	end)
	t:Skip("T43", "B", "Test-Werkzeug selbst", ASYNC)
	t:Skip("T44", "B", "Alle Ereignisse einmal", OPEN)
	t:Skip("T45", "B", "Tastenbelegungen", OPEN)
	-- T46: Flüster-Antworten (!dkp) gehen im Testmodus über RM.Whisper, nichts Echtes
	t:Check("T46", "B", "Sperrgitter: !dkp per Flüstern", function()
		local whispers = 0
		local origW = RM.Whisper
		local cfg = RM.db.config
		local was = cfg.whisperReplies
		return Guard(function()
			cfg.whisperReplies = true
			RM.Whisper = function() whispers = whispers + 1 end
			local before = RealTotal()
			local errors, first = CallHandlers("CHAT_MSG_WHISPER", "!dkp", "Tank1")
			if errors > 0 then return false, first, "kein Fehler" end
			errors, first = CallHandlers("CHAT_MSG_WHISPER", "!dkp Tank1", "Krieger1")
			if errors > 0 then return false, first, "kein Fehler" end
			if whispers ~= 2 then return false, whispers .. " Antworten über RM.Whisper", 2 end
			if RealTotal() ~= before then return false, "echte Aktion", "0" end
			if RM.db.testMode and RM.db.testMode.post then return false, "testMode.post gesetzt", "nil" end
		end, function() RM.Whisper = origW; cfg.whisperReplies = was end)
	end)
end

local function AreaC(t, G)
	t:Check("T50", "C", "Simulator für geschützte Werte", function()
		return WithSecret(function(SECRET)
			if not RM.IsSecret(SECRET) then return false, "nicht erkannt", "RM.IsSecret true" end
			if RM.Short(SECRET) ~= nil and not (RM.G and RM.G.Short) then return false, "RM.Short", "nil" end
			if GoldSentinelTest.Str("abc") ~= "abc" then return false, "Str", "abc" end
			local ok = pcall(function() return SECRET:lower() end)
			if ok then return false, "Köder wirft nicht", "Fehler bei Benutzung" end
		end)
	end)
	t:Check("T51", "C", "Addon-Nachricht mit geschütztem Absender", function()
		-- RM.Short liefert für geschützte Namen nil (GoldSentinelGame.Short) – hier über die eigene Hülle nachgestellt
		local origShort = RM.Short
		return WithSecret(function(SECRET)
			return Guard(function()
				RM.Short = function(n) if rawequal(n, SECRET) then return nil end return origShort(n) end
				local e1, f1 = CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, "PING\t{}", "RAID", SECRET)
				local e2, f2 = CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, "~M\t1\t1\t2\tx", "RAID", SECRET)
				if e1 + e2 > 0 then return false, f1 or f2, "verworfen ohne Fehler" end
			end, function() RM.Short = origShort end)
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
	t:Skip("T53", "C", "Bereitschafts-Check mit geschützten Auren", OPEN)
	t:Check("T54", "C", "Systemmeldung geschützt", function()
		return WithSecret(function(SECRET)
			local e, f = CallHandlers("CHAT_MSG_SYSTEM", SECRET)
			if e > 0 then return false, f, "kein Fehler" end
		end)
	end)
	t:Skip("T55", "C", "Fehlende alte Globals: Auren und Zauber", OPEN)
	t:Check("T56", "C", "Bindungen beim Laden", function()
		if C_Item and C_Item.GetItemInfo and RM.GetItemInfo ~= C_Item.GetItemInfo then return false, "RM.GetItemInfo", "C_Item.GetItemInfo" end
		if C_Container and C_Container.GetContainerNumSlots and RM.Container.NumSlots ~= C_Container.GetContainerNumSlots then
			return false, "RM.Container.NumSlots", "C_Container"
		end
	end)
	t:Check("T57", "C", "Kampfsperre simuliert (Markieren)", function()
		local M = RM.Markers
		local was = M.simCombat
		return Guard(function()
			M.simCombat = true
			if not M.CombatBlocked() then return false, "nicht gesperrt", "gesperrt" end
		end, function() M.simCombat = was end)
	end)
	t:Check("T58", "C", "Kampflog gesperrt bzw. offen", function()
		local reg = RM.frame:IsEventRegistered("COMBAT_LOG_EVENT_UNFILTERED") and true or false
		if reg ~= (RM.Caps.combatLog and true or false) then return false, tostring(reg), tostring(RM.Caps.combatLog) end
		if RM.IsModern and reg then return false, "registriert", "nicht registriert (moderner Client)" end
		return true, reg and "registriert" or "nicht registriert"
	end)
end

local function AreaD(t)
	if RM.IsModern then
		for _, id in ipairs({ "T70", "T71", "T72", "T73", "T74", "T75" }) do t:Skip(id, "D", "Alter Client", "nur im alten Client (Era/TBC)") end
		return
	end
	t:Check("T72", "D", "Talentbäume", function()
		if not RM.Caps.talentTrees then return false, "talentTrees false", "true" end
	end)
	t:Check("T73", "D", "Kampflog-Weg unverändert", function()
		if not RM.Caps.combatLog then return false, "combatLog false", "true" end
	end)
	t:Check("T74", "D", "Namen exakt", function()
		if not RM.SameName("Rokan", "rokan") or RM.SameName("Rokan Steinwacht", "Rokan") then return false, "SameName", "nur exakt" end
	end)
	t:Client("T71", "D", "Auren auf dem alten Client", "mit Fläschchen/Elixier: /rm bereit – wird es erkannt?")
	t:Client("T75", "D", "Plündermeister-Weg", "in einer Gruppe mit Plündermeister: /dump RaidMaster.GetLootMethod()")
end

local function AreaE(t)
	for _, id in ipairs({ "T80", "T81", "T82", "T83", "T84" }) do t:Skip(id, "E", "Daten", OPEN) end
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
	t:Skip("T105", "G", "Altes Addon RaidMasterTest", OPEN)
end

local function AreaH(t)
	local ms = debugprofilestop
	if type(ms) ~= "function" then t:Skip("T110", "H", "Leistung", "debugprofilestop fehlt") return end
	t:Check("T110", "H", "Zielwechsel (Boss-Leiste) < 2 ms", function()
		local B = RM.BossBar
		local keep = B.ReadTarget
		return Guard(function()
			B.ReadTarget = function() return true, false, "Ragnaros" end
			B.TargetBoss()                         -- erster Aufbau des Namensverzeichnisses
			local total, max = 0, 0
			for _ = 1, 20 do
				local t0 = ms()
				B.TargetBoss()
				local d = ms() - t0
				total, max = total + d, math.max(max, d)
			end
			local avg = total / 20
			if avg >= 2 then return false, string.format("%.2f ms", avg), "< 2 ms" end
			return true, string.format("Mittel %.3f ms, max %.3f ms", avg, max)
		end, function() B.ReadTarget = keep end)
	end)
	t:Check("T114", "H", "Serializer 500 Spieler < 16 ms", function()
		local data = { players = {} }
		for i = 1, 500 do data.players["Spieler" .. i] = { c = "WARRIOR", d = { mc = i, ony = i * 2 } } end
		local t0 = ms()
		local s = RM.Comm.Serialize(data)
		RM.Comm.Deserialize(s)
		local d = ms() - t0
		if d >= 16 then return false, string.format("%.1f ms", d), "< 16 ms" end
		return true, string.format("%.1f ms", d)
	end)
	for _, id in ipairs({ "T111", "T112", "T113", "T115", "T116" }) do t:Skip(id, "H", "Leistung", OPEN) end
end

local function AreaI(t)
	t:Check("T120", "I", "Absichtlicher Fehler wird gezählt", function()
		local GT = GoldSentinelTest
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
		end, function()
			for i = #D.errors, 1, -1 do if D.errors[i].msg == msg then table.remove(D.errors, i) end end
			for k, e in pairs(s.errors) do if type(e) == "table" and type(e.msg) == "string" and e.msg:find("RaidMaster-Testfehler", 1, true) then s.errors[k] = nil end end
		end)
	end)
	t:Check("T121", "I", "Abgefangene Fehler melden (RM.ReportError)", function()
		local s = RaidMasterDB.gsTest
		return Guard(function()
			RM.ReportError("Diag.provider", "RaidMaster-Testfehler (abgefangen)")
			local found = false
			for _, e in pairs(s.errors) do if type(e) == "table" and e.wo == "Diag.provider" and tostring(e.msg):find("RaidMaster-Testfehler", 1, true) then found = true end end
			if not found then return false, "kein Eintrag", "wo = Diag.provider" end
		end, function()
			for k, e in pairs(s.errors) do if type(e) == "table" and tostring(e.msg):find("RaidMaster-Testfehler", 1, true) then s.errors[k] = nil end end
		end)
	end)
	t:Skip("T122", "I", "Doppelte Fehler", OPEN)
	t:Check("T123", "I", "Testberichte warten auf Versand (Anzeige)", function()
		local n = GoldSentinelTest.Pending(RaidMasterDB)
		if type(n) ~= "number" then return false, type(n), "Zahl" end
		return true, n
	end)
end

local function AreaJ(t, G)
	t:Check("T130", "J", "IsClassicEra nur für echtes Era", function()
		return WithFlavor("forever", function()
			if RM.IsClassicEra or not RM.IsModern then return false, "IsClassicEra/IsModern falsch", "false/true" end
		end)
	end)
	for _, id in ipairs({ "T131", "T132", "T133", "T134" }) do t:Skip(id, "J", "Regression", OPEN) end
	t:Client("T135", "J", "Skillungen in Forever", "/dump GetTalentTabInfo(1) und /dump GetTalentInfo(1,1); Gildenmitglied betrachten")
	t:Client("T136", "J", "Plündermeister vorhanden", "/dump GiveMasterLoot ~= nil, GetMasterLootCandidate ~= nil; /dump C_PartyInfo and C_PartyInfo.GetLootMethod()")
	t:Check("T137", "J", "Namen mit Leerzeichen (Anmeldung)", function()
		local r = RM.Signup.Parse("RAIDMASTER-ANMELDUNG\nRokan Steinwacht;PRIEST;Heal;angemeldet")
		if not r or r.list[1].name ~= "Rokan Steinwacht" then return false, r and tostring(r.list[1].name), "Rokan Steinwacht" end
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
		local keep, tt = B.ReadTarget, B.testTarget
		return WithSecret(function(SECRET)
			return Guard(function()
				B.testTarget = nil
				B.ReadTarget = function() return true, false, SECRET end
				local boss = B.TargetBoss()
				if boss ~= nil then return false, "Boss erkannt", "nil" end
				if B.Update then B.Update() end
			end, function() B.ReadTarget, B.testTarget = keep, tt; if B.Update then pcall(B.Update) end end)
		end)
	end)
	t:Check("T141", "J", "Beute-Datenbank: geschützte GUID", function()
		return WithSecret(function(SECRET)
			if RM.LootDB.ParseGUID(SECRET) ~= nil then return false, "nicht nil", "nil" end
		end)
	end)
	t:Check("T142", "J", "!dkp mit Doppelnamen (Forever-Weg)", function()
		local DKP, cfg = RM.DKP, RM.db.config
		local pool = RM.Test.pool or DKP.ActivePool()
		local replies = {}
		local origW, was = RM.Whisper, cfg.whisperReplies
		return Guard(function()
			cfg.whisperReplies = true
			local p = DKP.EnsurePlayer("Rokan Steinwacht", "PRIEST")
			p.d[pool] = 40
			RM.Whisper = function(msg) replies[#replies + 1] = msg end
			return WithFlavor("forever", function()
				CallHandlers("CHAT_MSG_WHISPER", "!dkp Rokan Steinwacht", "Tank1")
				CallHandlers("CHAT_MSG_WHISPER", "!dkp rokan", "Tank1")
				local s = DKP.Summary("rokan")
				for i = 1, 2 do
					local r = replies[i] or ""
					if not (r:find("Rokan Steinwacht", 1, true) and r:find("40", 1, true)) then return false, r, "Rokan Steinwacht … 40" end
				end
				if not s:find("40", 1, true) then return false, s, "40 über den Vornamen" end
			end)
		end, function() RM.Whisper = origW; cfg.whisperReplies = was end)
	end)
	t:Check("T143", "J", "Betrachten: geschützte GUID", function()
		return WithSecret(function(SECRET)
			local e, f = CallHandlers("INSPECT_READY", SECRET)
			if e > 0 then return false, f, "kein Fehler" end
		end)
	end)
	t:Check("T144", "J", "RM.Short mit geschütztem Namen", function()
		if not (RM.G and RM.G.Short) then return true, "ohne GoldSentinelGame" end
		local origG = RM.G.IsSecret
		local SECRET = RM.Test.MakeSecret()
		return Guard(function()
			-- GoldSentinelGame.IsSecret ist ein Feld der gemeinsamen Tabelle (kein Blizzard-Global)
			RM.G.IsSecret = function(v) return rawequal(v, SECRET) or origG(v) end
			if RM.Short(SECRET) ~= nil then return false, "nicht nil", "nil" end
		end, function() RM.G.IsSecret = origG end)
	end)
	t:Skip("T145", "J", "Berufe: Ausgabe-ID nie nil", OPEN)
	t:Client("T146", "J", "Bereitschafts-Check in alten Clients", "Era/Anniversary mit Fläschchen: /rm bereit – erkannt?")
	t:Skip("T147", "J", "Berufe-Knopf übersetzt", "offline geprüft (Locales)")
	t:Check("T148", "J", "Versionsnummer = Code", function()
		local meta = (C_AddOns and C_AddOns.GetAddOnMetadata) or GetAddOnMetadata
		if meta and meta("RaidMaster", "Version") ~= RM.VERSION then return false, tostring(meta("RaidMaster", "Version")), RM.VERSION end
	end)
	for _, id in ipairs({ "T149", "T150", "T151" }) do t:Skip(id, "J", "Berufe modern", OPEN) end
	t:Client("T152", "J", "Berufe-Knopf im Client", "Knopf 'Meine Berufe einlesen' mehrmals, dann /rm berufe")
	t:Check("T153", "J", "Datenformat für ProfessionSentinel", function()
		if RM.db.prof ~= nil and type(RM.db.prof) ~= "table" then return false, type(RM.db.prof), "Tabelle" end
	end)
	t:Check("T154", "J", "GoldSentinelGame Version", function()
		if not G or (tonumber(G.version) or 0) < 2 then return false, tostring(G and G.version), ">= 2" end
	end)
end

local RUNNERS = { A = AreaA, B = AreaB, C = AreaC, D = AreaD, E = AreaE, F = AreaF, G = AreaG, H = AreaH, I = AreaI, J = AreaJ }

---------------------------------------------------------------------------
-- Start
---------------------------------------------------------------------------
local function Say(msg) RM.Print("Testroutine: " .. msg) end

function R.Run(only)
	local T = RM.Test
	if not RM.IsDev() then RM.RequireDev() return end
	if not (T and RM.db and GoldSentinelTest) then Say("Test-Werkzeug oder GoldSentinelTest fehlt.") return end
	if R.running then Say("läuft schon.") return end
	local inCombat = (InCombatLockdown and InCombatLockdown()) or (IsEncounterInProgress and IsEncounterInProgress())
	if inCombat then Say("nur außerhalb des Kampfes.") return end
	if T.IsRunning and T.IsRunning() then Say("erst den Test-Durchlauf beenden.") return end
	if T.active then Say("erst den Testmodus beenden (die Routine startet ihn selbst und stellt danach alles zurück).") return end
	only = only and only:upper() or nil
	if only == "LANG" then only = nil end
	if only and not RUNNERS[only] then Say("Bereich " .. only .. " gibt es nicht (A … J).") return end

	HookActions()
	wipe(realCount)
	local G = RM.G
	local snap = Snapshot()
	R.testDBnilBefore = snap.testDBnil
	local diagBefore = #RM.Diag.errors
	local keep = { whisper = RM.Whisper, isSecret = RM.IsSecret, short = RM.Short, read = RM.BossBar.ReadTarget,
		tt = RM.BossBar.testTarget, sim = RM.Markers.simCombat, offset = RM.timeOffset,
		gIsSecret = G and G.IsSecret, flavor = G and G.flavor }
	R.running = true
	local unwatch = WatchLocale()
	local t = GoldSentinelTest.Begin("RaidMaster", RM.VERSION, RaidMasterDB)
	local ok, err = pcall(function()
		T.SetAutoSend(false)
		T.SetFollowStart(false)
		T.Start()
		if not T.active then error("Testmodus ließ sich nicht starten") end
		for _, a in ipairs(AREA_ORDER) do
			if not only or only == a then
				local okA, errA = pcall(RUNNERS[a], t, G)
				if not okA then t:Check("X" .. a, a, "Bereich " .. AREAS[a] .. " abgebrochen", function() error(errA, 0) end) end
			end
		end
	end)
	unwatch()
	-- aufräumen, auch nach Fehler
	pcall(T.Stop)
	RM.Whisper, RM.IsSecret, RM.Short = keep.whisper, keep.isSecret, keep.short
	RM.BossBar.ReadTarget, RM.BossBar.testTarget = keep.read, keep.tt
	RM.Markers.simCombat, RM.timeOffset = keep.sim, keep.offset or 0
	if G then
		if keep.gIsSecret then G.IsSecret = keep.gIsSecret end
		if G.SetTestFlavor then G.SetTestFlavor(nil) end
		RM.SetGameFlags()
	end
	RaidMasterTestOptions = snap.opts
	if not ok then t:Check("X0", "A", "Routine abgebrochen", function() error(err, 0) end) end

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

	-- Sandbox
	local diff = Compare(snap)
	local sandbox = "OK"
	if #diff > 0 then
		sandbox = "ABWEICHUNG: " .. table.concat(diff, ", ")
		RestoreSnapshot(snap)
	end
	local blocked = RM.Test.blocked or 0
	t:Check("SB", "A", "echte Daten unverändert", function()
		if #diff > 0 then return false, sandbox, "OK (wiederhergestellt)" end
		if RM.db.testMode ~= nil or RaidMasterTestDB ~= nil then return false, "testMode/RaidMasterTestDB übrig", "nil" end
		if G and G.flavor ~= keep.flavor then return false, "Testflavor " .. tostring(G.flavor), tostring(keep.flavor) end
		if RM.Whisper ~= keep.whisper or RM.IsSecret ~= keep.isSecret or RM.BossBar.ReadTarget ~= keep.read then
			return false, "Funktion nicht zurückgesetzt", "identisch"
		end
	end)
	local realN, realList = RealTotal()
	t:Check("T46b", "B", "Sperrgitter: echte Aktionen während der Routine", function()
		if realN > 0 then return false, realList, "0" end
	end)
	R.running = false

	local text = t:Finish({ sandbox = sandbox, fehlerzaehler = diagBefore .. " -> " .. #RM.Diag.errors, locale = RM.LOCALE,
		testflavor_ende = G and tostring(G.flavor) or "-", blocked = blocked, echte_aktionen = realN, bereich = only or "alle" })
	text = text .. "\n\nBericht gespeichert – wird beim nächsten /reload oder Ausloggen an die Prüfung gemeldet."
		.. "\nNach der Testroutine bitte /reload."
	RM.UI.ShowExport(text)
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
