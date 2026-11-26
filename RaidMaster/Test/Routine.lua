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
	K = "Oberfläche im Client", L = "Umfassend (TU1–TU8)" }
local AREA_ORDER = { "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L" }

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
-- gsMarkt/gsMarktAus (ab 3.0.25): laufende Daten des gemeinsamen Marktdaten-Netzes (GoldSentinelMarkt.lua) – sie ändern
-- sich im Hintergrund (Scans mitlesen, Netz) und werden weder verglichen noch zurückgedreht.
local SB_SKIP = { gsTest = true, lastSave = true, gsMarkt = true, gsMarktAus = true, pruefliste = true, routineGuard = true,
	routinePending = true }

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

-- 3.0.34 (BEFUND HOCH SOFORT 18.11.): was andere Addons über RaidMaster.db sehen, solange getestet wird.
-- Testroutine: der Schnappschuss vom Start (echte Daten; was die Sandbox nicht sichert, live aus RM.db).
-- Testmodus ohne Routine: die Kopie, die der Testmodus beim Start von den echten Daten anlegt (RaidMasterTestDB), sonst live.
-- Nie Testdaten. Ausserhalb von Tests: nil (dann liefert RaidMaster.db das echte RM.db).
local realView, realViewFor
function RM.RealDBView()
	if R.running and R.snap and type(R.snap.db) == "table" then
		if realViewFor ~= R.snap then
			local sdb = R.snap.db
			realView = setmetatable({}, { __index = function(_, k)
				local v = sdb[k]
				if v ~= nil then return v end
				if SB_SKIP[k] then return RM.db and RM.db[k] end
				return nil
			end })
			realViewFor = R.snap
		end
		return realView
	end
	local T = RM.Test
	if T and T.active and type(RaidMasterTestDB) == "table" then
		local real = RaidMasterTestDB
		if realViewFor ~= real then
			realView = setmetatable({}, { __index = function(_, k)
				if k == "signup" then return real.hasSignup and real.signup or nil end
				if k == "data" or k == "session" or k == "trade" or k == "config" or k == "specs" then return real[k] end
				return RM.db and RM.db[k]
			end })
			realViewFor = real
		end
		return realView
	end
	return nil
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

-- 3.0.41 (Hinweis 20.11. 08:40, Nutzer "darf nicht mehr passieren, dass der Ingame-Test Livedaten verändert"): auch das
-- GEMEINSAME Adressbuch von GoldSentinelSync (alle GoldSentinel-Addons lesen es; Anlass AHSentinel T913: Fehlzähler/Pause).
-- Verglichen werden je vorhandenem Eintrag fail, pause, v, src – "seen" und neue Einträge entstehen im Hintergrund (echte
-- Nachrichten anderer Spieler) und gehören nicht der Routine. Im Bericht nur Nummern, nie Namen.
local SYNC_FIELDS = { "fail", "pause", "v", "src" }
local function SyncPrint(book)
	book = book or (_G.GoldSentinelSync and _G.GoldSentinelSync.book)
	if type(book) ~= "table" then return nil end
	local out = {}
	for name, e in pairs(book) do
		if type(name) == "string" and type(e) == "table" then
			local c = {}
			for _, f in ipairs(SYNC_FIELDS) do c[f] = e[f] end
			out[name] = c
		end
	end
	return out
end

local function SyncDiff(before, book, restore)
	local out = {}
	if type(before) ~= "table" or type(book) ~= "table" then return out end
	local names = {}
	for name in pairs(before) do names[#names + 1] = name end
	table.sort(names)
	for i, name in ipairs(names) do
		local e, b = book[name], before[name]
		if type(e) ~= "table" then
			out[#out + 1] = "Adressbuch Eintrag " .. i .. " fehlt"
			if restore then book[name] = Deep(b) end
		else
			for _, f in ipairs(SYNC_FIELDS) do
				if e[f] ~= b[f] then
					out[#out + 1] = "Adressbuch Eintrag " .. i .. "." .. f
					if restore then e[f] = b[f] end
				end
			end
		end
	end
	return out
end
R.SyncPrint, R.SyncDiff = SyncPrint, SyncDiff

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

-- TR-ALLE (3.0.30): Portionen ≤ 5 ms je Bild. Nach jeder Prüfung: ist die laufende Portion länger als R.PORTION_MS, gibt die
-- Routine das Bild ab (wartet 0 s = nächstes Bild). Eine einzelne Prüfung, die selbst länger dauert, kann nicht geteilt
-- werden – sie steht dann in R.slow und im Bericht ("länger als 5 ms").
R.PORTION_MS = 5
R.PRE_MS = 1           -- vor jeder Prüfung: ist das Bild schon mehr als 1 ms belegt, erst das nächste Bild abwarten
-- NP-RM30-1: einzeln gemessen (erster Aufbau des Hauptfensters und der Seiten) – zählt nicht zu "über 5 ms"
R.SINGLE = { Aufbau = true, T10 = true, T12 = true }
-- 3.0.33: "Aufbau <Seite>" zählt auch als einzeln gemessen (Ingame 19:38: Aufbau 38,3 ms – welche Seite, zeigt jetzt der Name)
function R.IsSingle(at) return R.SINGLE[at] or tostring(at):find("^Aufbau") ~= nil end
function R.Breathe(limit)
	if not (debugprofilestop and R.running and R.portionStart and coroutine.running()) then return end
	if (R.noYield or 0) > 0 then return end                 -- unter pcall (Körper von t:Check): kein Bild abgeben
	local d = debugprofilestop() - R.portionStart
	if d > (R.maxPortion or 0) and not R.IsSingle(tostring(R.current or "?")) then R.maxPortion, R.maxPortionAt, R.maxPortionMem = d, tostring(R.current or "?"), nil end
	if d > (limit or R.PORTION_MS) then coroutine.yield("wait", 0) end
end

-- vollständige Speicherbereinigung in kleinen Schritten über mehrere Bilder (statt collectgarbage("collect") am Stück):
-- zwei abgeschlossene Durchgänge, damit sicher ein ganzer Durchgang von vorn dabei ist
-- 3.0.34 (Supervisor 17.11. 21:30): die Dauer jedes Schritts wird gemessen (längster -> R.gcStepMax, Anzahl -> R.gcSteps);
-- ein Schritt kann den unteilbaren Abschluss eines Durchgangs enthalten
local function CollectInSteps()
	for _ = 1, 2 do
		local guard = 0
		repeat
			local t0 = debugprofilestop and debugprofilestop()
			local done = collectgarbage("step", 16)
			if R.env then R.env.gcMark = true end                 -- RM-UMG1: Bereinigung in diesem Bild
			if t0 then
				local d = debugprofilestop() - t0
				R.gcStepMax, R.gcSteps = math.max(R.gcStepMax or 0, d), (R.gcSteps or 0) + 1
			end
			guard = guard + 1
			R.Breathe(R.PRE_MS)
		until done or guard > 100000
	end
end

-- Warten (nur im Ablauf der Routine, nicht innerhalb von t:Check – dort AsyncCheck benutzen)
---------------------------------------------------------------------------
-- RM-UMG1 (3.0.44, Entscheid des Nutzers 24.11.2026 20:04): Umgebung und Bedienung erkennen – NUR LESEN, nur in der Testroutine.
-- a) jedes Bild des Laufs (OnUpdate) je Sekunde zusammengefasst: Zahl, Summe, längstes, eigene Arbeit (Portionen der Routine),
--    Ladebildschirm, Speicherbereinigung; Bild-Verteilung (1-ms-Fächer) vorher (1 s Ruhe vor dem ersten Bereich), im Lauf, nachher.
--    Alle Felder werden beim Start angelegt (kein Zuwachs im Messfenster von T116).
--    Hintergrund: eine Sekunde mit mindestens 5 Bildern, deren Mittel bei der Bildgrenze für den Hintergrund liegt (CVar
--    maxFPSBk; Standard 30 = 33,3 ms, ±3,5 ms) oder mindestens doppelt so lang ist wie das Ruhe-Mittel vorher und über 25 ms.
-- b) Bilder über 40 ms: eigene Arbeit, Rest, Ladebildschirm, Speicherbereinigung (höchstens 30 gemerkt).
-- c) Speicher je Addon einmal am Ende (nach der letzten Messung; UpdateAddOnMemoryUsage ist teuer) – nur wenn es ein Bild über
--    40 ms gab.
-- d) Leistungsprüfungen (Bereich H) über ihrer Grenze: lag in ihrer Zeit Hintergrund, Ladebildschirm oder Speicherbereinigung
--    vor -> "im Client prüfen" mit Grund "Bedienung/Umgebung möglich" statt FEHLER. NICHT übernommen: "Rest grösser als eigene
--    Arbeit" – die Grenzen von Bereich H messen nur die eigene Arbeit (debugprofilestop um den eigenen Code); der Rest des Bildes
--    (Zeichnen, andere Addons) ist darin nicht enthalten und in fast jedem Bild grösser (begründet im Bericht).
---------------------------------------------------------------------------
local ENV_SECONDS = R.LIMIT_LONG + 60
local ENV_LONG_MS, ENV_LONG_KEEP = 40, 30

function R.NewEnv()
	local e = { cnt = {}, sum = {}, max = {}, own = {}, load = {}, gc = {}, long = {}, hist = {},
		phase = "vorher", ownAcc = 0, gcMark = false, loading = false, maxMs = 0, maxAt = "-", maxOwn = 0, nLong = 0 }
	for i = 1, ENV_SECONDS do e.cnt[i], e.sum[i], e.max[i], e.own[i], e.load[i], e.gc[i] = 0, 0, 0, 0, false, false end
	for _, ph in ipairs({ "vorher", "Lauf", "nachher" }) do
		local h = {}
		for i = 1, 201 do h[i] = 0 end
		e.hist[ph] = h
	end
	local bk = tonumber(GetCVar and GetCVar("maxFPSBk") or nil)
	local fg = tonumber(GetCVar and GetCVar("maxFPS") or nil)
	e.capBk = (bk and bk > 0 and bk ~= fg) and (1000 / bk) or nil     -- gleiche Grenze vorn/hinten: nicht unterscheidbar
	return e
end

function R.EnvStart(e, now)
	e.t0 = now
	e.lastCount = collectgarbage("count")
	if GetNetStats then e.ping0 = select(3, GetNetStats()) end
	e.fps0 = GetFramerate and GetFramerate() or nil
end

-- ein Bild (ms = Dauer, now = GetTime())
function R.EnvFrame(e, ms, now)
	local s = math.floor(now - (e.t0 or now)) + 1
	if s < 1 then s = 1 elseif s > ENV_SECONDS then s = ENV_SECONDS end
	local own = e.ownAcc
	e.ownAcc = 0
	local c = collectgarbage("count")
	local gc = e.gcMark or ((e.lastCount or c) - c) > 512
	e.gcMark, e.lastCount = false, c
	e.cnt[s], e.sum[s], e.own[s] = e.cnt[s] + 1, e.sum[s] + ms, e.own[s] + own
	if ms > e.max[s] then e.max[s] = ms end
	if e.loading then e.load[s] = true end
	if gc then e.gc[s] = true end
	local h = e.hist[e.phase]
	local b = math.floor(ms) + 1
	if b > 201 then b = 201 elseif b < 1 then b = 1 end
	h[b] = h[b] + 1
	if ms > e.maxMs then e.maxMs, e.maxAt, e.maxOwn, e.maxGc, e.maxLoad = ms, tostring(R.current or "-"), own, gc, e.loading end
	if ms > ENV_LONG_MS then
		e.nLong = e.nLong + 1
		if #e.long < ENV_LONG_KEEP then
			e.long[#e.long + 1] = { at = tostring(R.current or "-"), ms = ms, own = own, gc = gc, load = e.loading, s = s }
		end
	end
end

local function HistStat(h)
	local n = 0
	for i = 1, 201 do n = n + h[i] end
	if n == 0 then return 0, nil, nil end
	local med, p95, acc = nil, nil, 0
	for i = 1, 201 do
		acc = acc + h[i]
		if not med and acc >= n * 0.5 then med = i - 1 end
		if not p95 and acc >= n * 0.95 then p95 = i - 1 end
	end
	return n, med, p95                                         -- in ganzen ms (Fächer 1 ms; 200 = 200 ms und mehr)
end
R.EnvHist = HistStat

function R.EnvIsBack(e, s)
	local n = e.cnt[s]
	if n < 5 then return false end
	local mean = e.sum[s] / n
	if e.capBk and math.abs(mean - e.capBk) <= 3.5 then return true end
	local _, med = HistStat(e.hist["vorher"])
	return med ~= nil and med > 0 and mean > 25 and mean >= 2 * (med + 1)
end

-- Grund, warum eine Überschreitung zwischen t0 und t1 von aussen kommen kann, sonst nil
function R.EnvJudge(e, t0, t1)
	if not (e and e.t0) then return nil end
	local a = math.max(1, math.floor(t0 - e.t0) + 1)
	local b = math.min(ENV_SECONDS, math.floor(t1 - e.t0) + 1)
	local why = {}
	local back, load, gc = 0, false, false
	for s = a, b do
		if R.EnvIsBack(e, s) then back = back + 1 end
		load = load or e.load[s]
		gc = gc or e.gc[s]
	end
	if back > 0 then why[#why + 1] = string.format("Spiel im Hintergrund/Fensterwechsel möglich (%d Sek.)", back) end
	if load then why[#why + 1] = "Ladebildschirm" end
	if gc then why[#why + 1] = "Speicherbereinigung in der Messzeit" end
	return #why > 0 and table.concat(why, ", ") or nil
end

function R.EnvLine(e, memTop)
	if not (e and e.t0) then return "UMGEBUNG: nicht gemessen" end
	local backS, first, last, lastS = 0, nil, nil, 1
	for s = 1, ENV_SECONDS do
		if e.cnt[s] > 0 then lastS = s end
		if R.EnvIsBack(e, s) then backS = backS + 1; first = first or s; last = s end
	end
	local parts = {}
	parts[#parts + 1] = backS > 0 and string.format("Hintergrund möglich (Sek. %d–%d, %d Sek. von %d)", first, last, backS, lastS)
		or string.format("Vordergrund (%d Sek.)", lastS)
	for _, ph in ipairs({ "vorher", "Lauf", "nachher" }) do
		local n, med, p95 = HistStat(e.hist[ph])
		parts[#parts + 1] = n > 0 and string.format("Bild %s Median %d ms / 95 %% %d ms (%d Bilder)", ph, med, p95, n)
			or string.format("Bild %s: keine Bilder", ph)
	end
	if e.fps0 or e.fps1 then parts[#parts + 1] = string.format("Bilder/s %.0f -> %.0f", e.fps0 or 0, e.fps1 or 0) end
	if e.ping0 or e.ping1 then parts[#parts + 1] = string.format("Ping %s -> %s ms", tostring(e.ping0 or "?"), tostring(e.ping1 or "?")) end
	parts[#parts + 1] = string.format("längstes Bild %.1f ms bei %s (eigene Arbeit %.1f ms, Rest %.1f ms%s%s)", e.maxMs, e.maxAt,
		e.maxOwn, math.max(0, e.maxMs - e.maxOwn), e.maxGc and ", Speicherbereinigung" or "", e.maxLoad and ", Ladebildschirm" or "")
	local long = {}
	table.sort(e.long, function(x, y) return x.ms > y.ms end)
	for i = 1, math.min(5, #e.long) do
		local l = e.long[i]
		long[i] = string.format("%s %.0f ms (eigen %.1f%s%s)", l.at, l.ms, l.own, l.gc and ", Bereinigung" or "", l.load and ", Laden" or "")
	end
	parts[#parts + 1] = string.format("Bilder über %d ms: %d%s", ENV_LONG_MS, e.nLong, #long > 0 and (" – " .. table.concat(long, ", ")) or "")
	parts[#parts + 1] = "Speicher je Addon (am Ende): " .. (memTop or "nicht gelesen")
	if not e.capBk then parts[#parts + 1] = "Hintergrund-Bildgrenze = Vordergrund-Grenze (maxFPSBk) – nur über den Sprung erkennbar" end
	return "UMGEBUNG: " .. table.concat(parts, " · ")
end

local function Wait(sec)
	if not coroutine.running() then error("Wait außerhalb des Ablaufs der Routine", 2) end
	coroutine.yield("wait", tonumber(sec) or 0)
end

-- asynchrone Prüfung: der Körper darf warten; Ergebnis wie bei t:Check
-- Ein Fall darf "ASYNC_SKIP", Grund liefern: dann ehrlich übersprungen statt OK (ab 3.0.18, z. B. T43 ohne Beute)
local ASYNC_SKIP = {}
local function AsyncCheck(t, id, area, name, fn)
	R.current = id
	R.Breathe(R.PRE_MS)
	local r = pack(Run(fn))
	if r[1] and r[2] == ASYNC_SKIP then return t:Skip(id, area, name, tostring(r[3])) end
	return t:Check(id, area, name, function()
		if not r[1] then error(r[2], 0) end
		return unpack(r, 2, r.n)
	end)
end

-- RM-UMG1 d): Leistungsprüfung – über der Grenze UND Umgebung auffällig -> "im Client prüfen" mit Grund statt FEHLER
function R.PerfVerdict(e, t0, t1, ok, a)
	if not (ok and a == false) then return nil end
	return R.EnvJudge(e, t0, t1)
end

local function PerfAdd(t, id, area, name, t0, r)
	local why = R.PerfVerdict(R.env, t0, GetTime(), r[1], r[2])
	if why then
		return t:Client(id, area, name, string.format("Bedienung/Umgebung möglich: %s · gemessen %s (Grenze %s) – Lauf mit WoW im "
			.. "Vordergrund wiederholen", why, tostring(r[3]), tostring(r[4])))
	end
	return t:Check(id, area, name, function()
		if not r[1] then error(r[2], 0) end
		return unpack(r, 2, r.n)
	end)
end

local function PerfCheck(t, id, area, name, fn)
	R.Breathe(R.PRE_MS)
	R.current = id
	local t0, p0 = GetTime(), debugprofilestop and debugprofilestop()
	R.noYield = (R.noYield or 0) + 1                        -- wie t:Check: unter pcall kein Bild abgeben
	local r = pack(pcall(fn))
	R.noYield = R.noYield - 1
	if p0 then
		local d = debugprofilestop() - p0
		if d > R.PORTION_MS and R.slow then R.slow[#R.slow + 1] = { id = id, ms = d } end
	end
	return PerfAdd(t, id, area, name, t0, r)
end

local function PerfAsync(t, id, area, name, fn)
	R.current = id
	R.Breathe(R.PRE_MS)
	local t0 = GetTime()
	local r = pack(Run(fn))
	if r[1] and r[2] == ASYNC_SKIP then return t:Skip(id, area, name, tostring(r[3])) end
	return PerfAdd(t, id, area, name, t0, r)
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
-- NP-RM30-1 (3.0.31): tiefe Kopie in Portionen – gibt alle 200 Einträge das Bild ab, wenn die Portion voll ist. Die Schlüssel
-- einer Tabelle werden vorher in einer Liste gesammelt (kein "next" über eine Tabelle, die sich zwischen zwei Bildern ändert).
-- Ausserhalb der Koroutine (oder unter pcall) wie Deep am Stück.
local function DeepPortions(v, seen, n)
	if type(v) ~= "table" then return v end
	seen, n = seen or {}, n or { 0 }
	if seen[v] then return seen[v] end
	local c = {}
	seen[v] = c
	local keys = {}
	for k in pairs(v) do
		keys[#keys + 1] = k
		if #keys % 200 == 0 then R.Breathe(R.PRE_MS) end   -- RM-P1 (3.0.50): auch das Sammeln grosser Tabellen in Portionen
	end
	for _, k in ipairs(keys) do
		local x = v[k]
		if x ~= nil then c[Deep(k, seen)] = DeepPortions(x, seen, n) end
		n[1] = n[1] + 1
		if n[1] % 10 == 0 then R.Breathe(R.PRE_MS) end      -- 3.0.33: alle 20; RM-P1 (3.0.50): alle 10 Einträge prüfen
	end
	return c
end

local function KeepDB(keys, body)
	local db = RM.db
	local saved = {}
	local where = R.current
	for _, k in ipairs(keys) do
		R.current = tostring(where) .. " Daten sichern"
		saved[k] = { had = db[k] ~= nil, tbl = db[k], copy = DeepPortions(db[k]) }
		R.Breathe(R.PRE_MS)                            -- NP-RM30-1: jeder Bereich der Daten in eigenen Portionen
	end
	-- Zurückschreiben: der Inhalt wird übernommen (die Kopie gehört nur hier hin, kein zweites Kopieren nötig); je Schlüssel in
	-- pcall, damit ein Fehler die übrigen nicht verhindert. Nicht im Aufräumteil von Guard (der läuft unter pcall und dürfte
	-- kein Bild abgeben) – sondern danach, mit derselben Garantie: es läuft immer, Fehler des Körpers werden danach weitergegeben.
	local r = pack(Run(body))
	where = R.current
	for _, k in ipairs(keys) do
		R.current = tostring(where) .. " Daten zurück"
		local s = saved[k]
		pcall(function()
			if not s.had then
				db[k] = nil
			elseif type(s.tbl) == "table" then
				db[k] = s.tbl
				for key in pairs(s.tbl) do s.tbl[key] = nil end
				for key, val in pairs(s.copy) do s.tbl[key] = val end
			else
				db[k] = s.copy
			end
		end)
		R.Breathe(R.PRE_MS)
	end
	if not r[1] then error(r[2], 0) end
	return unpack(r, 2, r.n)
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
		if RaidMaster ~= RM.GLOBAL or RaidMaster.VERSION ~= RM.VERSION then miss[#miss + 1] = "RaidMaster" end   -- 3.0.34: Durchreiche
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

	AsyncCheck(t, "T10", "B", "Slash /rm mit allen Unterbefehlen", function()
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
				R.Breathe(R.PRE_MS)                   -- TR-ALLE: ein paar Befehle je Bild
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

	AsyncCheck(t, "T12", "B", "Hauptfenster und alle Seiten je Ansicht", function()
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
						R.Breathe(R.PRE_MS)               -- TR-ALLE: eine Seite je Bild
					end
				end
			end
			if errors > 0 then return false, errors .. " Fehler, zuerst " .. tostring(first), "0" end
			for _, id in ipairs({ "assign", "signup" }) do
				if seen.member[id] then return false, "Mitglied sieht " .. id, "nicht sichtbar" end
			end
			-- 3.0.40 (Entscheid 18.11. 11:10): Mitglieder sehen die Einstellungen – aber nur den Bereich Allgemein (persönliche Optionen)
			if not seen.member.settings then return false, "Mitglied sieht die Einstellungen nicht", "sichtbar (Allgemein)" end
			return true, Count(seen.raidlead) .. " Seiten (Raidleiter), " .. Count(seen.member) .. " (Mitglied)"
		end, function()
			Undo(u)
			T.role = "raidlead"
			pcall(UI.ResetMainSize)
			RM.db.config.mainSize = size
			if Shown(MainFrame()) then UI.Toggle() end
		end)
	end)

	-- 3.0.33 (leistung.md, Ingame 19:38: 4,9–6 ms am Stück): eine Option je Bild, wenn das Bild schon belegt ist
	AsyncCheck(t, "T13", "B", "Jede Option einmal an und aus", function()
		local checks, cycles, bad = 0, 0, {}
		local function label(e) return tostring(e.label or (e.options and e.options[1] and e.options[1][2]) or "?"):sub(1, 40) end
		for _, e in ipairs(UI.registry or {}) do
			R.Breathe(R.PRE_MS)
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

	-- NP-RM30-1 (3.0.31): jedes Nebenfenster in einem eigenen Bild (Ingametest: 11 ms am Stück)
	AsyncCheck(t, "T14", "B", "Nebenfenster und Esc", function()
		local errs = {}
		local function try(what, fn, ...)
			R.Breathe(R.PRE_MS)
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

	AsyncCheck(t, "T20", "B", "Versteigerung Regeln", function()   -- 3.0.33: zwei Teile in eigenen Bildern (Ingame 5,1 ms)
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
			R.Breathe(R.PRE_MS)
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
	R.WindowStep(t, "T35b")          -- TR-ALLE D (3.0.31): wartet nie, wird beim nächsten Berufsfenster nachgeholt

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
	R.WindowStep(t, "T36b")          -- TR-ALLE D: Bank (nur Bank-Charakter)
	R.WindowStep(t, "T36c")          -- TR-ALLE D: Post (nur Bank-Charakter)

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
				for i = #parts, 1, -1 do RM.SimulateEvent("CHAT_MSG_ADDON", RM.PREFIX, parts[i], "RAID", "Tank1"); R.Breathe(R.PRE_MS) end
				if got ~= 1 then return false, "Handler " .. got .. "x", "genau 1x" end
				R.Breathe(R.PRE_MS)                               -- NP-RM30-1: Schritte in eigenen Bildern
				local e = CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, "UNBEKANNT\t{}", "RAID", "Tank1")
				if e > 0 then return false, "unbekannter Typ", "ignoriert" end
				-- HELLO mit höherer Version: Hinweis höchstens einmal
				local hello = { av = RM.VERSION_NUM + 1, at = "9.9.9", dv = 0, sk = 0 }
				CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, "HELLO\t" .. C.Serialize(hello), "RAID", "Tank1")
				if not (C.versions.Tank1 and C.versions.Tank1.num == RM.VERSION_NUM + 1) then return false, "HELLO nicht gemerkt", "Version gemerkt" end
				-- SNAP einer fremden Gilde: von Nicht-Leitung ignoriert, von Raidleitung übernommen
				R.Breathe(R.PRE_MS)
				local snap = DKP.MakeSnapshot(5)
				R.Breathe(R.PRE_MS)
				snap.g, snap.v = "Fremdgilde", (snap.v or 0) + 1
				CallHandlers("CHAT_MSG_ADDON", RM.PREFIX, "SNAP\t" .. C.Serialize(snap), "RAID", "Fremd1")
				if RM.db.foreign and RM.db.foreign.Fremdgilde then return false, "SNAP von Nicht-Leitung übernommen", "ignoriert" end
				R.Breathe(R.PRE_MS)
				local origAuth = RM.IsRaidAuthority
				Swap(u, RM, "IsRaidAuthority", function(n) return n == "Tank1" or origAuth(n) end)
				Swap(u, RM.UI, "viewGuild", RM.UI.viewGuild)
				C.handlers.SNAP("Tank1", snap, "RAID")
				if not (RM.db.foreign and RM.db.foreign.Fremdgilde) then return false, "SNAP der Raidleitung", "übernommen (Ansicht)" end
				R.Breathe(R.PRE_MS)
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
			-- 3.0.31 (Ingametest 17.11.: "Beute geladen 10/26"): bis 30 s warten (alle 0,5 s nachfragen; GET_ITEM_INFO_RECEIVED
			-- kommt in dieser Zeit an), früher aufhören, wenn alles da ist oder 8 s lang nichts Neues mehr kam (Items, die es in
			-- diesem Client nicht gibt, laden nie)
			-- 3.0.36 (Supervisor 09:47, Ingame zweimal "versteigerbar 0"): die ECHTEN Beute-Regeln des Nutzers versteigern Onyxia-
			-- Beute nicht (Classify liest RM.db.config.rules). T43 prüft das Werkzeug, nicht die Regeln (das tun T21 …): für seinen
			-- Durchlauf eigene Test-Regeln "Versteigerung" für alle Arten, danach zurück (Swap/Undo; config liegt zusätzlich in der
			-- Sandbox des Testmodus). Vorher die Einstufung mit den echten Regeln festhalten – fürs Ergebnis.
			local realRules = T.DescribeLoot and T.DescribeLoot(T.pool, 12) or {}
			local rules = RM.db.config.rules
			for _, kind in ipairs({ "epic", "blue", "recipe", "mats" }) do Swap(u, rules, kind, "auction") end
			local known, total, auct = 0, 0, 0
			if T.PreloadLoot then
				known, total, auct = T.PreloadLoot(T.pool)
				local w, lastGain, lastKnown = 0, 0, known
				while total > 0 and known < total and w < 30 and (w - lastGain) < 8 do
					Wait(0.5); w = w + 0.5
					known, total, auct = T.PreloadLoot(T.pool)
					if known > lastKnown then lastKnown, lastGain = known, w end
				end
			end
			auct = auct or 0
			-- 3.0.36: Messung mit den echten Daten des Nutzers zeigt "Episch -> Versteigerung" – die Regeln waren es also nicht allein.
			-- Bleibt Onyxia ohne versteigerbares Item (z. B. nur Quest-/Taschen-Items geladen), nimmt T43 den Geschmolzenen Kern
			-- (fast nur epische Rüstung/Waffen) – eigener Topf, ebenfalls nur mit geladenen Items.
			if auct == 0 and not R.long and T.PreloadLoot then
				local onyText = table.concat(T.DescribeLoot and T.DescribeLoot(T.pool, 12) or {}, ", ")
				Swap(u, T, "pool", "mc")
				known, total, auct = T.PreloadLoot("mc")
				local w = 0
				while (auct or 0) == 0 and known < total and w < 15 do
					Wait(0.5); w = w + 0.5
					known, total, auct = T.PreloadLoot("mc")
				end
				auct = auct or 0
				realRules = T.DescribeLoot and T.DescribeLoot("mc", 12) or realRules
				realRules[#realRules + 1] = "(Onyxia: " .. onyText .. ")"
			end
			-- 3.0.35 (Ingametest 18.11.: 3 gezogene Items, alle "andere Regel"): ohne ein einziges versteigerbares geladenes Item
			-- kann diese Prüfung nichts vergeben -> nicht prüfbar mit Zahl, nie FEHLER aus Zufall
			if auct == 0 then
				return ASYNC_SKIP, string.format("Beute (%s) geladen %d/%d, auch mit Test-Regeln versteigerbar 0; mit Test-Regeln: %s; echte Regeln: %s – beim nächsten Lauf wieder",
					tostring(T.pool), known, total, table.concat(T.DescribeLoot and T.DescribeLoot(T.pool, 12) or {}, ", "), table.concat(realRules, ", "))
			end
			Swap(u, T, "preferAuction", true)               -- der Durchlauf zieht nur versteigerbare Items (Test/Test.lua Pick)
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
			-- 3.0.32: Zähler JETZT festhalten – der zweite T.RunRaids unten (Abbruch-Prüfung) setzt sie zurück (in 3.0.31 stand darum
			-- im Ingametest "0 Items behandelt", obwohl 10 Items geladen waren)
			local st = {}
			for k, v in pairs(T.stats or {}) do st[k] = v end
			-- "Raid starten" in RaidMaster bricht einen laufenden Durchlauf ab
			T.preferAuction = nil
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
			-- 3.0.32: gezählt wird, was DIESER Durchlauf vergeben hat (st.awarded). Die Zählung im Log (n) nahm auch Items aus früheren
			-- Prüfungen mit (Nachbau: "2 Items vergeben" ohne eine einzige geladene Ony-Beute) – sie steht nur noch als Zusatz da.
			if (st.awarded or 0) < 1 then
				local detail = string.format("Beute geladen %d/%d (mit Test-Regeln versteigerbar %d); im Durchlauf %d Items behandelt (%d Versteigerung, %d andere Regel), %d ohne Daten; "
					.. "Versteigerungen gestartet %d, Start nicht möglich %d, vergeben %d, ohne Gebot %d; Regeln: %s; mit deinen echten Regeln: %s",
					known, total, auct, st.handled or 0, st.auction or 0, st.other or 0, st.noInfo or 0,
					st.started or 0, st.startFail or 0, st.awarded or 0, st.noBid or 0, table.concat(st.items or {}, ", "), table.concat(realRules, ", "))
				-- 3.0.32 (Supervisor 19:42): "nicht prüfbar" NUR, wenn belegt ist, dass die Daten fehlen – kein einziges Item hatte
				-- Daten (behandelt 0 und Beute nicht geladen bzw. Items ohne Daten). Alles andere ist FEHLER, mit allen Zahlen.
				if (st.handled or 0) == 0 and (known == 0 or (st.noInfo or 0) > 0) then
					return ASYNC_SKIP, "Item-Daten fehlen: " .. detail .. " – beim nächsten Lauf wieder"
				end
				return false, "kein Item vergeben (" .. detail .. "; im Log seit Start " .. n .. ")", ">= 1"
			end
			if RM.db.testMode and RM.db.testMode.post then return false, "testMode.post gesetzt", "nil" end
			return true, string.format("%d Items vergeben in %d s (Beute geladen %d/%d, mit Test-Regeln versteigerbar %d; behandelt %d, Versteigerung %d, ohne Gebot %d; Regeln: %s; mit deinen echten Regeln: %s)%s",
				st.awarded, waited, known, total, auct, st.handled or 0, st.auction or 0, st.noBid or 0, table.concat(st.items or {}, ", "), table.concat(realRules, ", "), stress)
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
	-- 3.0.33 (Ingame 19:38: 5,4 ms): Kopie der echten Daten in Portionen, danach je Aufruf ein Bild
	AsyncCheck(t, "T82", "E", "Beschädigte Einträge", function()
		local db = DeepPortions(RM.db)
		R.Breathe(R.PRE_MS)
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
			R.Breathe(R.PRE_MS)
			local ok, err = pcall(fn, ...)
			if not ok then errs[#errs + 1] = what .. ": " .. tostring(err) end
		end
		try("InitDB", RM.InitDB, db)
		try("SortedPlayers", RM.DKP.SortedPlayers, "mc", db.data)
		try("Summary", RM.DKP.Summary, "Y", db.data)
		R.Breathe(R.PRE_MS)
		WithDB(db, function()                              -- getauscht nur in diesem einen Bild (R.noYield: try gibt hier kein Bild ab)
			R.noYield = (R.noYield or 0) + 1
			try("Spec.List", RM.Spec.List)
			try("LDB.Stats", RM.LootDB.Stats)
			R.noYield = R.noYield - 1
		end)
		if #errs > 0 then return false, table.concat(errs, " | "):sub(1, 250), "kein Lua-Fehler" end
		return true
	end)
	-- 3.0.33 (Ingame 19:38: 6,1 ms): Kopien in Portionen; der Teil mit getauschtem RM.db bleibt in einem Bild
	AsyncCheck(t, "T83", "E", "Absturz mitten im Test", function()
		local T = RM.Test
		local copy = DeepPortions(RM.db)
		copy.testMode = { active = true }
		local backup = DeepPortions(RaidMasterTestDB)
		local known = { data = DeepPortions(copy.data), session = { active = false, kills = {} }, trade = {}, config = DeepPortions(copy.config),
			specs = {}, hasSignup = false }
		R.Breathe(0)
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
	-- TR-ALLE (3.0.30): frische Testtabelle statt Kopie der echten Daten (Grösse unabhängig vom Spieler) und Aufbau in Portionen;
	-- nur der Teil mit getauschtem RM.db läuft am Stück (in einem Bild, damit kein echtes Ereignis in der Testtabelle landet)
	AsyncCheck(t, "T84", "E", "Große Datenmengen", function()
		local db = RM.InitDB({})
		-- Aufbau in kleinen Portionen (Bild abgeben ab 0,5 ms): das Anlegen vieler Tabellen löst Schritte der Speicherbereinigung
		-- aus, deren unteilbarer Schluss im Nachbau bis ~4 ms dauert (gemessen) – darum bleibt für die eigene Arbeit wenig
		for i = 1, 500 do
			db.data.players["Spieler" .. i] = { c = "WARRIOR", d = { mc = i } }
			if i % 5 == 0 then R.Breathe(0.5) end   -- viele neue Tabellen: die Speicherbereinigung (bis ~4 ms) läuft mit
		end
		local D1 = { Spieler1 = 1 }   -- eine gemeinsame Buchungstabelle (nur gelesen): halb so viele neue Tabellen
		for i = 1, 5000 do
			db.data.log[#db.data.log + 1] = { id = "t" .. i, t = i, k = "manual", x = "Test", d = D1, pool = "mc" }
			if i % 5 == 0 then R.Breathe(0.5) end   -- viele neue Tabellen: die Speicherbereinigung (bis ~4 ms) läuft mit
		end
		db.specs = db.specs or {}
		for i = 1, 300 do
			db.specs["Spieler" .. i] = { c = "WARRIOR", p = { 5, 5, 41 }, t = RM.Now() }
			if i % 5 == 0 then R.Breathe(0.5) end   -- viele neue Tabellen: die Speicherbereinigung (bis ~4 ms) läuft mit
		end
		db.itemTips = {}
		for i = 1, (RM.ItemTip.MAX or 600) + 50 do
			db.itemTips[100000 + i] = { n = "x", t = i }
			if i % 5 == 0 then R.Breathe(0.5) end   -- viele neue Tabellen: die Speicherbereinigung (bis ~4 ms) läuft mit
		end
		-- NP-RM30-1 (3.0.31): jeder Schritt mit getauschtem RM.db in einem eigenen Bild – getauscht und zurück im selben Bild,
		-- dazwischen ist RM.db immer die echte Tabelle (kein echtes Ereignis landet in der Testtabelle)
		local total, list, snap = 0, nil, nil
		local steps = {
			function() list = RM.DKP.SortedPlayers("mc") end,
			function() snap = RM.DKP.MakeSnapshot() end,
			function() RM.Spec.Prune() end,
			function() RM.ItemTip.Prune() end,
		}
		for _, step in ipairs(steps) do
			R.Breathe(0)
			local t0 = Ms()
			local ok, err = WithDB(db, function() step() return true end)
			total = total + (Ms() - t0)
			if not ok then return false, tostring(err), "kein Fehler" end
		end
		if #list < 500 then return false, #list .. " Spieler", ">= 500" end
		if #snap.l > 60 then return false, #snap.l .. " Log-Einträge im Snapshot", "<= 60" end
		if Count(db.itemTips) > (RM.ItemTip.MAX or 600) then return false, Count(db.itemTips) .. " Item-Tooltips", "<= " .. (RM.ItemTip.MAX or 600) end
		if RM.Records.MAX_LOG ~= 400 then return false, "Records.MAX_LOG " .. tostring(RM.Records.MAX_LOG), 400 end
		return true, string.format("%.0f ms in 4 Bildern", total)
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
		if RaidMaster ~= RM.GLOBAL or RaidMaster.UI ~= RM.UI then bad[#bad + 1] = "RaidMaster" end   -- 3.0.34: Durchreiche auf RM
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
	PerfCheck(t, "T110", "H", "Zielwechsel (Boss-Leiste) < 2 ms", function()
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
	PerfAsync(t, "T111", "H", "Gruppenwechsel: Handler < 2 ms, zusammen < 16 ms", function()
		TestRaid()
		RM.UI.Open("dkp")
		local list = RM.HandlersFor("GROUP_ROSTER_UPDATE") or {}
		local slow, total = {}, 0
		-- 3.0.44 (belegt im Nachbau zhCN: mit angehaltener Speicherbereinigung 3.0.43 und 3.0.44 gleich 0,4–0,9 ms, ohne bis
		-- 4 ms): angesammelte Bereinigungsarbeit früherer Prüfungen fiel in die Messung von Handler #10. Darum vorher eine
		-- vollständige Bereinigung in Schritten (über mehrere Bilder, wie T116); die Grenze bleibt 2 ms je Handler.
		CollectInSteps()
		return Guard(function()
			for i, fn in ipairs(list) do
				local avg = Measure(function() pcall(fn) end, 5)   -- TR-ALLE: 5 statt 20 Messungen, damit ein Bild unter 5 ms bleibt
				total = total + avg
				if avg >= 2 then slow[#slow + 1] = string.format("#%d %.2f ms", i, avg) end
				R.Breathe(R.PRE_MS)                   -- TR-ALLE: ein Handler je Bild (20 Messungen)
			end
			Settle(10)
			if #slow > 0 then return false, table.concat(slow, ", "), "< 2 ms je Handler" end
			if total >= 16 then return false, string.format("%.1f ms", total), "< 16 ms" end
			return true, string.format("%d Handler, zusammen %.2f ms", #list, total)
		end, function() if Shown(MainFrame()) then RM.UI.Toggle() end end)
	end)
	PerfCheck(t, "T112", "H", "Addon-Nachrichten: BID < 2 ms, SNAP 500 < 16 ms", function()
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
	PerfCheck(t, "T113", "H", "Ticker < 1 ms, D.Text mit 20 Fehlern < 16 ms", function()
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
	-- NP-RM30-1 (3.0.31): 500 Spieler in 5 Teilen à 100, jeder Teil in einem eigenen Bild; Grenze für die Summe wie bisher
	PerfAsync(t, "T114", "H", "Serializer 500 Spieler < 16 ms (5 Teile à 100)", function()
		local sum, worst = 0, 0
		for part = 0, 4 do
			local data = { players = {} }
			for i = part * 100 + 1, part * 100 + 100 do data.players["Spieler" .. i] = { c = "WARRIOR", d = { mc = i, ony = i * 2 } } end
			R.Breathe(0)
			local t0 = debugprofilestop()
			local s = RM.Comm.Serialize(data)
			local back = RM.Comm.Deserialize(s)
			local d = debugprofilestop() - t0
			if type(back) ~= "table" or type(back.players) ~= "table" or not back.players["Spieler" .. (part * 100 + 1)] then
				return false, "Teil " .. (part + 1) .. " nicht zurückgelesen", "gleiche Daten"
			end
			sum, worst = sum + d, math.max(worst, d)
		end
		if sum >= 16 then return false, string.format("%.1f ms", sum), "< 16 ms" end
		return true, string.format("zusammen %.1f ms, teuerster Teil %.1f ms", sum, worst)
	end)
	PerfCheck(t, "T115", "H", "Tooltip < 2 ms, erster Aufbau < 16 ms", function()
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
	-- TR-ALLE (3.0.30): Bereinigung und Last in Portionen über mehrere Bilder.
	-- RM-I1 (3.0.42, Ingametest 3.0.41: 15 086 KB): collectgarbage("count") ist der Speicher des GANZEN Spiels; was andere
	-- Addons in den rund 40 000 Bildern dauerhaft anlegen, zählte als Zuwachs von RaidMaster. Die Nachbildung (nur RaidMaster)
	-- misst für 3.0.40 und 3.0.41 dasselbe (45 / 43 KB). Darum jetzt zusätzlich der Speicher JE ADDON
	-- (UpdateAddOnMemoryUsage/GetAddOnMemoryUsage): Grenze 256 KB gilt für RaidMaster selbst; der Zuwachs des ganzen Spiels
	-- und die drei Addons mit dem grössten Zuwachs stehen im Ergebnis (Beleg statt Vermutung). Ohne diese Funktionen gilt
	-- wie bisher der Zähler des ganzen Spiels.
	local function AddonMemory()
		local upd, get = _G.UpdateAddOnMemoryUsage, _G.GetAddOnMemoryUsage
		local num = (C_AddOns and C_AddOns.GetNumAddOns) or _G.GetNumAddOns
		local info = (C_AddOns and C_AddOns.GetAddOnInfo) or _G.GetAddOnInfo
		if not (upd and get and num and info) then return nil end
		local t0 = debugprofilestop()
		local ok = pcall(upd)
		local ms = debugprofilestop() - t0
		if not ok then return nil end
		local out = {}
		for i = 1, num() or 0 do
			local name = info(i)
			local kb = name and tonumber((get(i)))
			if kb and kb > 0 then out[name] = kb end
		end
		return out, ms
	end
	R.AddonMemory = AddonMemory

	AsyncCheck(t, "T116", "H", "Speicher: Zuwachs RaidMaster < 256 KB", function()
		TestRaid()
		local TT = RM.Tooltip
		local fake = { GetItem = function() return "x", LINK_EPIC end, AddLine = function() end, Show = function() end }
		R.gcStepMax, R.gcSteps = 0, 0
		CollectInSteps()
		-- 3.0.48 (Ingametest 3.0.47: T116 längstes Bild 50 ms – eigene Arbeit?): Speicher lesen = Blizzard UpdateAddOnMemoryUsage
		-- (rechnet alle Addons). Eigenes Bild mit eigenem Namen, damit die Portionen-Zeile es von der Arbeit von T116 trennt.
		local function ReadMem()
			R.Breathe(0)
			R.current = "T116 Speicher lesen (Blizzard)"
			local m, ms = AddonMemory()
			R.Breathe(0)
			R.current = "T116"
			return m, ms
		end
		local memA, msA = ReadMem()
		local before = collectgarbage("count")
		for _ = 1, 100 do CallHandlers("GROUP_ROSTER_UPDATE"); R.Breathe(R.PRE_MS) end
		for _ = 1, 100 do CallHandlers("PLAYER_TARGET_CHANGED"); R.Breathe(R.PRE_MS) end
		for i = 1, 50 do TT.OnItem(fake); if i % 10 == 0 then R.Breathe(R.PRE_MS) end end
		if R.leakProbe then R.leakProbe() end                -- nur Gegenprobe der Nachbildung (absichtliches Leck)
		CollectInSteps()
		local grow = collectgarbage("count") - before
		local memB, msB = ReadMem()
		Settle(10)
		local steps = string.format("%d Bereinigungsschritte, längster %.1f ms", R.gcSteps or 0, R.gcStepMax or 0)
		if not (memA and memB and memA.RaidMaster and memB.RaidMaster) then
			if grow >= 256 then return false, string.format("ganzes Spiel %.0f KB (Speicher je Addon nicht lesbar); %s", grow, steps), "< 256 KB" end
			return true, string.format("ganzes Spiel %.0f KB (Speicher je Addon nicht lesbar); %s", grow, steps)
		end
		local own = memB.RaidMaster - memA.RaidMaster
		local others = {}
		for name, kb in pairs(memB) do
			if name ~= "RaidMaster" then others[#others + 1] = { name, kb - (memA[name] or 0) } end
		end
		table.sort(others, function(a, b) return a[2] > b[2] end)
		local top = {}
		for i = 1, math.min(3, #others) do
			if others[i][2] >= 1 then top[#top + 1] = string.format("%s %.0f KB", others[i][1], others[i][2]) end
		end
		local text = string.format("RaidMaster %.0f KB · ganzes Spiel %.0f KB · grösster Zuwachs anderer: %s · Speicher lesen %.1f/%.1f ms; %s",
			own, grow, #top > 0 and table.concat(top, ", ") or "keiner", msA or 0, msB or 0, steps)
		if own >= 256 then return false, text, "RaidMaster < 256 KB" end
		return true, text
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
			-- 3.0.31 (RM-TF-1): NICHT über geterrorhandler() – am Ende der Kette steht das Fehlerfenster des Spiels, das der Nutzer
			-- sonst sieht. Stattdessen genau das, was die beiden Glieder der Kette tun: Diagnose (D.OnError) und der gemeinsame
			-- Abgriff von GoldSentinelTest (Record über GoldSentinelTest.Error mit "Lua"); dass beide eingeklinkt sind, prüft T120 getrennt.
			if not (D.IsHooked and D.IsHooked()) then return false, "Diagnose nicht eingeklinkt", "D.IsHooked" end
			if not _G.GoldSentinelTestHooked then return false, "GoldSentinelTest-Abgriff fehlt", "eingeklinkt" end
			D.OnError(msg)
			GoldSentinelTest.Error("RaidMaster", "Lua", msg)
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
			for _ = 1, 3 do D.OnError(msg); GoldSentinelTest.Error("RaidMaster", "Lua", msg) end   -- RM-TF-1: ohne Fehlerfenster
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
		-- 3.0.38: der Haken steht im Optionen-Fenster (Ansagen im Chat) und erscheint nur mit Kampflog
		local check = false
		for _, d in ipairs(RM.Opt and RM.Opt.DEFS or {}) do
			if d.key == "coreHound" and (not d.cond or d.cond()) then check = true end
		end
		if RM.IsModern then
			if RM.Caps.combatLog then return false, "Kampflog an", "aus (moderner Client)" end
			if check then return false, "Haken statt Knopf", "Knopf \"Kürschner ansagen\"" end
			if type(RM.Raid.AnnounceSkinners) ~= "function" then return false, "AnnounceSkinners fehlt", "Funktion" end
			return true, "Knopf (Seite Raid)"
		end
		if RM.Caps.combatLog and not check then
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

	-- 3.0.25 (MN4): Marktdaten-Netz – lädt mit/ohne Datei, Schalter aus = kein Lesen/Senden, kein Fehler ohne AH-API
	-- 3.0.26 (MN-T): auch die Zähler (GM.stats inkl. dropped) sichern und zurückschreiben – sonst zeigt die Diagnose
	-- nach jeder Testroutine "verworfen: aus 1", obwohl der Spieler nichts ausgeschaltet hat
	local function CopyStats(v)
		if type(v) ~= "table" then return v end
		local c = {}
		for k, x in pairs(v) do c[k] = CopyStats(x) end
		return c
	end
	local function MarktState(GM)
		return { lastEv = GM.lastEv, readAt = GM.readAt, reader = GM.reader, askAt = GM.askAt, feedUntil = GM.feedUntil,
			share = RM.db.config.marktTeilen, aus = (GM.stats.dropped or {}).aus or 0, sent = GM.stats.sent or 0,
			stats = CopyStats(GM.stats) }
	end
	local function MarktRestore(GM, st)
		GM.lastEv, GM.readAt, GM.reader, GM.askAt, GM.feedUntil = st.lastEv, st.readAt, st.reader, st.askAt, st.feedUntil
		RM.SetMarktShare(st.share ~= false)
		-- dieselbe Tabelle behalten (andere Addons halten evtl. einen Verweis), nur den Inhalt zurückschreiben
		local live = GM.stats
		for k in pairs(live) do live[k] = nil end
		for k, x in pairs(st.stats or {}) do live[k] = CopyStats(x) end
	end
	-- Vergleich zweier Zähler-Tabellen (für MN-T)
	local function SameStats(a, b)
		if type(a) ~= type(b) then return false end
		if type(a) ~= "table" then return a == b end
		for k, x in pairs(a) do if not SameStats(x, b[k]) then return false end end
		for k in pairs(b) do if a[k] == nil then return false end end
		return true
	end
	t:Check("T180", "J", "MN4 RaidMaster lädt mit und ohne GoldSentinelMarkt", function()
		local GM = _G.GoldSentinelMarkt
		if type(GM) ~= "table" then return false, "GoldSentinelMarkt fehlt", "in der TOC (nach GoldSentinelSync)" end
		if (tonumber(GM.VERSION) or 0) < 1 then return false, tostring(GM.VERSION), ">= 1" end
		-- 3.0.26 (MN1-K): aktuelle Fassung aus shared/ mit FeedStart/Feed (Addons mit eigenem Vollscan geben ihn weiter)
		if type(GM.FeedStart) ~= "function" or type(GM.Feed) ~= "function" then
			return false, "FeedStart/Feed fehlen (v" .. tostring(GM.VERSION) .. ")", "aktuelle GoldSentinelMarkt.lua aus shared/"
		end
		_G.GoldSentinelMarkt = nil
		local okNo, resNo = pcall(RM.AttachMarkt)
		local okLine, line = pcall(RM.MarktLine)
		_G.GoldSentinelMarkt = GM
		if not (okNo and resNo == false and okLine and line:find("nicht geladen", 1, true)) then
			return false, "ohne Datei: " .. tostring(resNo) .. " / " .. tostring(line), "still, kein Fehler"
		end
		local okWith, resWith = pcall(RM.AttachMarkt)
		if not (okWith and resWith and GM.hosts and GM.hosts.RaidMaster == RaidMasterDB and type(RaidMasterDB.gsMarkt) == "table") then
			return false, "mit Datei: " .. tostring(resWith), "angemeldet, Daten in RaidMasterDB.gsMarkt"
		end
		return true, "v" .. GM.VERSION .. " angemeldet (FeedStart/Feed da); ohne Datei still"
	end)

	t:Check("T181", "J", "MN4 Schalter aus: kein Lesen, kein Senden", function()
		local GM = _G.GoldSentinelMarkt
		if type(GM) ~= "table" then return false, "fehlt", "GoldSentinelMarkt" end
		local st = MarktState(GM)
		local res = "ok"
		local okRun, err = pcall(function()
			RM.SetMarktShare(false)
			if GM.IsShareOn() then res = "IsShareOn trotz Schalter aus"; return end
			if RM.db.config.marktTeilen ~= false then res = "Schalter nicht gespeichert"; return end
			GM.lastEv = nil
			GM.OnReplicate()                                  -- neuer Scan-Schub
			if GM.readAt or GM.reader then res = "liest trotz Schalter aus"; return end
			if ((GM.stats.dropped or {}).aus or 0) ~= st.aus + 1 then res = "nicht als 'aus' verworfen"; return end
			GM.askAt = 0
			GM.Tick()
			if (GM.stats.sent or 0) ~= st.sent then res = "sendet trotz Schalter aus"; return end
			RM.SetMarktShare(true)
			if not GM.IsShareOn() then res = "Schalter an wirkt nicht" end
		end)
		MarktRestore(GM, st)
		if not okRun then return false, "Lua: " .. tostring(err), "kein Fehler" end
		if res ~= "ok" then return false, res, "aus = nichts" end
		if not SameStats(GM.stats, st.stats) then return false, "Zähler nach dem Test verändert", "unverändert (MN-T)" end
		return true, "aus: nichts gelesen/gesendet; an: wieder an; Zähler unverändert"
	end)

	-- NP-RM30-1 (3.0.31): jeder Schritt in einem eigenen Bild (Ingametest: 21 ms am Stück); Run statt pcall, damit der Körper
	-- Bilder abgeben kann – Schnittstelle und Zähler kommen garantiert zurück (auch bei Fehler oder Abbruch des Laufs: KeepDB/Sicherung)
	AsyncCheck(t, "T182", "J", "MN4 kein Lua-Fehler ohne Auktionshaus-Schnittstelle", function()
		local GM = _G.GoldSentinelMarkt
		if type(GM) ~= "table" then return false, "fehlt", "GoldSentinelMarkt" end
		local st = MarktState(GM)
		local errs = {}
		-- NP-RM30-1 (3.0.31): jeder Schritt in einem eigenen Bild (Ingametest: 21 ms am Stück). Jeder Schritt tauscht die
		-- Schnittstelle und schaltet Teilen ein, ruft genau eine Funktion und stellt danach ALLES zurück – im selben Bild.
		-- Zwischen den Bildern ist also nie etwas getauscht (kein Teilen, keine fremde Schnittstelle für andere Addons).
		local function Step(what, prepare, fn, ...)
			R.Breathe(0)
			R.current = "T182 " .. what            -- 3.0.33: Ingame 21,6 ms in EINEM Schritt – welcher, zeigt die Portionen-Zeile
			local origAh = GM.api.ah
			GM.api.ah = function() return nil end           -- alter Client: kein C_AuctionHouse
			RM.SetMarktShare(true)
			if prepare then pcall(prepare) end
			local ok, e = pcall(fn, ...)
			GM.api.ah = origAh
			GM.reader = nil
			MarktRestore(GM, st)
			if not ok then errs[#errs + 1] = what .. ": " .. tostring(e) end
		end
		Step("OnReplicate", function() GM.lastEv = nil end, GM.OnReplicate)
		for i = 1, 3 do
			Step("Tick " .. i, function() GM.lastEv = GetTime and GetTime() or 0; GM.readAt = 0 end, GM.Tick)
		end
		Step("Get", nil, GM.Get, 2589)
		Step("DiagLines", nil, GM.DiagLines)
		R.current = "T182"
		if #errs > 0 then return false, errs[1], "kein Fehler" end
		if not SameStats(GM.stats, st.stats) then return false, "Zähler nach dem Test verändert", "unverändert (MN-T)" end
		if RM.db.config.marktTeilen ~= st.share then return false, "Teilen nicht zurückgestellt", tostring(st.share) end
		return true, "ohne AH-API still (6 Schritte in eigenen Bildern); Zähler und Teilen unverändert"
	end)

	t:Check("T183", "J", "MN3 Testbericht-Zeile MARKT-NETZ", function()
		local ok, line = pcall(RM.MarktLine)
		if not ok then return false, "Lua: " .. tostring(line), "Zeile" end
		for _, part in ipairs({ "MARKT-NETZ", "v", "Scans", "gesendet", "empfangen", "Speicher" }) do
			if not line:find(part, 1, true) then return false, line, "mit " .. part end
		end
		return true, line
	end)

	-- 3.0.28: Prüfliste im Spiel (Entscheid des Nutzers 16.11. 06:47) – nur im Entwicklermodus; jede Stelle, die einen
	-- Punkt "merkt", löst ihn wirklich aus. Eigene Testliste mit eigener Tabelle – RaidMasterDB bleibt unberührt.
	t:Check("T185", "J", "Prüfliste: nur Entwickler, jede Stelle löst ihren Punkt aus", function()
		local B, D = _G.GoldSentinelPruefliste, _G.GoldSentinelDev
		if not (B and B.Register and D) then return false, "Baustein fehlt", "GoldSentinelPruefliste + GoldSentinelDev" end
		local pts = RM.PRUEFPUNKTE or {}
		if #pts < 1 or #pts > 14 then return false, #pts .. " Punkte", "1 bis 14" end
		local seen = {}
		for _, p in ipairs(pts) do
			if seen[p.id] then return false, "doppelt " .. tostring(p.id), "eindeutige id" end
			seen[p.id] = true
			for _, f in ipairs({ "title", "since", "todo", "expect" }) do
				if type(p[f]) ~= "string" or p[f] == "" then return false, tostring(p.id) .. " ohne " .. f, "alle Felder" end
			end
		end
		local savedIsDev, savedPL, savedTest = D.IsDev, RM.PL, RM.plTest
		local cfg, savedShare = RM.db.config, RM.db.config.marktTeilen
		local res, why, want = true, nil, nil
		local ok, err = pcall(function()
			-- ohne Entwicklermodus: wirkungslos
			D.IsDev = function() return false end
			RM.PL = nil
			if RM.GetPL() ~= nil then res, why, want = false, "Liste ohne Entwicklermodus", "nil"; return end
			if RM.PLHit("TR", "x") then res, why, want = false, "Hit ohne Entwicklermodus", "false"; return end
			-- mit Entwicklermodus: Testliste mit eigener Tabelle
			D.IsDev = function() return true end
			local fake = {}
			local list = B:Register("RaidMasterT185", { db = function() return fake end, version = RM.VERSION, points = pts })
			if not (list and list.addon) then res, why, want = false, "Register gab keine Liste", "Liste"; return end
			RM.PL, RM.plTest = list, true
			local function hit(id, fn)
				fn()
				local st = list:State(id)
				if st ~= "auto" and st ~= "fehler" then error(id .. " nicht ausgelöst (" .. tostring(st) .. ")", 0) end
			end
			hit("BL", function() RM.CmdHint.run("version") end)                       -- Klick in der Befehlsliste
			hit("MN2B", function() cfg.marktTeilen = false; RM.PLLoginChecks(); cfg.marktTeilen = savedShare end)
			hit("RT", function() RM.Markers.NoteSuggest(2) end)                        -- Vorschlag in Forever
			hit("SS", function() RM.Records.NoteShot("Testboss") end)                  -- Erstkill-Screenshot
			-- 3.0.33 (Nachbau mit echten Daten): eine echte Vormerkung (TR-ALLE D) hält TR zu Recht offen – hier ohne Vormerkung prüfen
			hit("TR", function()
				local pend = RaidMasterDB and RaidMasterDB.routinePending
				if RaidMasterDB then RaidMasterDB.routinePending = nil end
				local ok, err = pcall(R.NotePruefliste, { results = { { id = "X", status = "OK" } } }, nil)
				if RaidMasterDB then RaidMasterDB.routinePending = pend end
				if not ok then error(err, 0) end
			end)
			hit("MNT", function() end)                                                 -- mit TR gesetzt
			-- auto(): Vorgabe nil = noch nicht; mit Daten -> true
			local probe = RaidMasterDB.syncProbe
			RaidMasterDB.syncProbe = probe or { seq = 1, t = 0 }
			local sp
			for _, p in ipairs(pts) do if p.id == "SP" then sp = p end end
			local r1 = sp and sp.auto and sp.auto()
			RaidMasterDB.syncProbe = probe
			if r1 ~= true then error("SP auto nicht true", 0) end
			-- Hit während der Testroutine (ohne plTest) zählt nicht
			RM.plTest = nil
			list:Set("BL", "offen")
			RM.PLHit("BL", "x")
			if list:State("BL") ~= "offen" then error("Hit während der Routine gezählt", 0) end
			local lines = list:ReportLines()
			if #lines ~= #pts + 1 then error("ReportLines " .. #lines, 0) end
			why = (#pts) .. " Punkte; Hit-Stellen BL, MN2B, RT, SS, TR, MNT, auto SP; OPT sagt der Nutzer; ohne Dev wirkungslos"
		end)
		D.IsDev, RM.PL, RM.plTest = savedIsDev, savedPL, savedTest
		cfg.marktTeilen = savedShare
		if B.lists then B.lists.RaidMasterT185 = nil end
		if not ok then return false, tostring(err), "alle Stellen" end
		if not res then return false, why, want end
		return true, why
	end)

	-- 3.0.29 (RM-DIAG-1): Fehlerflut darf Diag.lua nicht über die Ausführungsgrenze treiben. Gemessen (ab 3.0.30 in Portionen, damit die
	-- Routine selbst nicht ruckelt – TR-ALLE): je Bild 100 Fehler, 10 Bilder (ohne Fenster), und 100 bei offenem Diagnose-Fenster; das Fenster wird dabei kein einziges Mal neu gesetzt,
	-- danach höchstens 1x pro Sekunde und nur bei Änderung. Die Meldung über die Ausführungsgrenze selbst zählt nur hoch.
	AsyncCheck(t, "T186", "J", "RM-DIAG-1 Fehlerflut: Diag bleibt billig", function()
		local D = RM.Diag
		if not (D and D.OnError and D.Record and debugprofilestop) then return false, "Diag.OnError fehlt", "3.0.29" end
		local saved, savedDropped, savedDirty = {}, D.dropped, D.dirty
		for i, e in ipairs(D.errors) do saved[i] = { t = e.t, msg = e.msg, n = e.n } end
		local wasShown = D.window and D.window:IsShown()
		local res, why, want = true, nil, nil
		local ok, err = Run(function()   -- Run statt pcall: der Körper gibt zwischendurch Bilder ab
			wipe(D.errors); D.dropped = 0; D.ResetRate()
			local pad = string.rep("x", 1000)
			-- 1) Flut ohne Fenster
			if D.window then D.window:Hide() end
			-- 1000 Fehler in 10 Bildern; gemessen wird nur der Handler (nicht der Aufbau der Testtexte), das teuerste Bild zählt.
			-- Die Erfassung ist je Sekunde begrenzt: liegen die Bilder in k Sekunden, sind höchstens 20*k einzeln erfasst
			local ms1, worst, secs = 0, 0, {}
			for chunk = 0, 9 do
				local msgs = {}
				for i = 1, 100 do local n = chunk * 100 + i; msgs[i] = "Interface/AddOns/RaidMaster/Test.lua:" .. n .. ": Flut " .. n .. " " .. pad end
				R.Breathe(0)
				secs[time()] = true
				local t0 = debugprofilestop()
				for i = 1, 100 do D.OnError(msgs[i]) end
				local d = debugprofilestop() - t0
				secs[time()] = true
				ms1, worst = ms1 + d, math.max(worst, d)
			end
			local nsec = 0
			for _ in pairs(secs) do nsec = nsec + 1 end
			local n1, d1 = #D.errors, D.dropped
			if #D.errors > 20 then res, why, want = false, #D.errors .. " Einträge", "<= 20"; return end
			if 1000 - d1 > D.MAX_PER_SEC * nsec then res, why, want = false, (1000 - d1) .. " einzeln in " .. nsec .. " s", "<= " .. D.MAX_PER_SEC * nsec; return end
			if D.dropped < 1 then res, why, want = false, "keine Flut erkannt", "dropped > 0"; return end
			if #D.errors[1].msg > D.MAX_MSG + 4 then res, why, want = false, "Text " .. #D.errors[1].msg, "gekürzt"; return end
			if worst > 5 then res, why, want = false, string.format("%.1f ms für 100 Fehler", worst), "<= 5 ms je Bild"; return end
			R.Breathe(0)
			-- 2) die Meldung über die Ausführungsgrenze selbst: ein Eintrag, nur hochgezählt
			wipe(D.errors); D.dropped = 0; D.ResetRate()
			local lim = "Interface/AddOns/RaidMaster/Diag.lua:-1: insecure scripts exceeded execution limit for addon RaidMaster"
			for _ = 1, 300 do D.OnError(lim) end
			R.Breathe(0)
			if #D.errors ~= 1 or D.errors[1].n ~= 300 then
				res, why, want = false, #D.errors .. " Einträge / n=" .. tostring(D.errors[1] and D.errors[1].n), "1 / 300"; return
			end
			-- 3) Fenster offen: kein Neuaufbau je Fehler, danach 1x pro Sekunde und nur bei Änderung
			D.ResetRate()
			D.Show()
			local box, calls = D.window.box, 0
			local orig = box.SetText
			box.SetText = function(self, txt) calls = calls + 1; return orig(self, txt) end
			local t1 = debugprofilestop()
			for i = 1, 100 do D.OnError("Interface/AddOns/RaidMaster/X.lua:1: offen " .. (i % 50)) end
			local ms2 = debugprofilestop() - t1
			local upd = D.window:GetScript("OnUpdate")
			local afterFlood = calls
			upd(D.window, 1.1)
			local afterTick = calls
			upd(D.window, 1.1)
			local afterIdle = calls
			box.SetText = orig
			if afterFlood ~= 0 then res, why, want = false, afterFlood .. "x SetText während der Flut", "0"; return end
			if afterTick ~= 1 then res, why, want = false, afterTick .. "x SetText nach 1 s", "1"; return end
			if afterIdle ~= 1 then res, why, want = false, (afterIdle - 1) .. "x SetText ohne Änderung", "0"; return end
			if ms2 > 5 then res, why, want = false, string.format("%.1f ms bei offenem Fenster", ms2), "<= 5 ms"; return end
			why = string.format("1000 Fehler in 10 Bildern %.1f ms, teuerstes Bild %.1f ms (%d einzeln erfasst in %d s, Liste hält %d; %d nur gezählt), Grenzmeldung 1 Eintrag n=300, offenes Fenster 100 Fehler %.1f ms ohne Neuaufbau",
				ms1, worst, 1000 - d1, nsec, n1, d1, ms2)
		end)
		wipe(D.errors)
		for i, e in ipairs(saved) do D.errors[i] = e end
		D.dropped, D.dirty = savedDropped or 0, savedDirty
		D.ResetRate()
		if D.window then
			if wasShown then D.window:Show(); D.Refresh() else D.window:Hide() end
		end
		if not ok then return false, "Lua: " .. tostring(err), "kein Fehler" end
		if not res then return false, why, want end
		return true, why
	end)

	-- 3.0.30 (RM-DIAG-1 Messung): Fehler je Quell-Addon zählen, nur Zahlen (kein Text im Bericht)
	t:Check("T187", "J", "RM-DIAG-1 Fehlerquellen je Addon", function()
		local D = RM.Diag
		if not (D and D.SourceOf and D.SourcesLine and D.CountSource) then return false, "fehlt", "3.0.30" end
		local cases = {
			{ "Interface/AddOns/AHSentinel/Sniper.lua:12: attempt to index nil", "AHSentinel" },
			{ "Interface\\AddOns\\RaidMaster\\Diag.lua:-1: insecure scripts exceeded execution limit for addon RaidMaster", "RaidMaster" },
			{ "Interface/AddOns/RaidMaster/X.lua:1: AddOn 'AHSentinel' tried to call the protected function for addon 'AHSentinel'", "AHSentinel" },
			{ "[string \"x\"]:1: attempt to call a nil value", "?" },
		}
		for _, c in ipairs(cases) do
			local got = D.SourceOf(c[1])
			if got ~= c[2] then return false, c[1]:sub(1, 40) .. " -> " .. tostring(got), c[2] end
		end
		local saved = { src = D.sources, total = D.sourcesTotal, first = D.firstSource }
		D.sources, D.sourcesTotal, D.firstSource = {}, 0, nil
		local ok, res, info = pcall(function()
			for _ = 1, 5 do D.OnError("Interface/AddOns/AHSentinel/A.lua:1: x") end
			D.OnError("Interface/AddOns/RaidMaster/B.lua:1: y")
			for i = 1, 40 do D.CountSource("Interface/AddOns/Fremd" .. i .. "/C.lua:1: z") end
			local line = D.SourcesLine()
			if D.sourcesTotal ~= 46 then return false, "gesamt " .. D.sourcesTotal, "46" end
			-- 30 Quellen einzeln (AHSentinel, RaidMaster, Fremd1 … Fremd28), der Rest (12) als "andere"
			if D.sources.AHSentinel ~= 5 or D.sources.RaidMaster ~= 1 or D.sources.andere ~= 12 then
				return false, string.format("AHS %s RM %s andere %s", tostring(D.sources.AHSentinel), tostring(D.sources.RaidMaster),
					tostring(D.sources.andere)), "5 / 1 / 12"
			end
			if not line:find("^FEHLERQUELLEN: 46 · andere 12, AHSentinel 5, ") then return false, line:sub(1, 80), "nach Anzahl sortiert" end
			local n = 0
			for _ in pairs(D.sources) do n = n + 1 end
			if n > 31 then return false, n .. " Quellen", "<= 31" end
			if not line:find("zuerst AHSentinel", 1, true) then return false, line:sub(-40), "zuerst AHSentinel" end
			if line:find("attempt", 1, true) or line:find("lua", 1, true) then return false, "Text im Bericht", "nur Zahlen" end
			return true, line:sub(1, 90)
		end)
		D.sources, D.sourcesTotal, D.firstSource = saved.src, saved.total, saved.first
		if not ok then return false, "Lua: " .. tostring(res), "kein Fehler" end
		return res, info
	end)

	-- 3.0.30 (RM-API-RAIDS): kommende Raid-Termine für andere Addons – nur Zeit und Name, ≤ 20, aufsteigend, fehlerfest
	t:Check("T188", "J", "RM-API-RAIDS RaidMasterAPI.UpcomingRaids", function()
		local API, S = _G.RaidMasterAPI, RM.Signup
		if not (API and API.UpcomingRaids and (API.VERSION or 0) >= 1 and API.TestRunning and S and S.KnownRaids) then return false, "fehlt", "VERSION >= 1, TestRunning" end
		local now = RM.Now()
		local savedKnown, savedSignup = S.KnownRaids, RM.db.signup
		local ok, res, info = pcall(function()
			-- gestern, heute früher, heute später, morgen + 25 weitere (mit Feldern, die nie hinaus dürfen)
			S.KnownRaids = function()
				local l = {
					{ t = now - 86400, name = "Gestern", player = "Testa" },
					{ t = now - 600, name = "Heute früher", player = "Bob" },
					{ t = now + 7200, name = "Heute später", player = "Cleo", list = { { name = "Offi" } }, id = 7 },
					{ t = now + 86400, name = "Morgen", player = "Echt1" },
				}
				for i = 1, 25 do l[#l + 1] = { t = now + 2 * 86400 + i * 3600, name = "Raid " .. i, player = "Testa" } end
				return l
			end
			local r = API.UpcomingRaids()
			if #r ~= 20 then return false, #r .. " Termine", "20" end
			if r[1].name ~= "Heute später" or r[2].name ~= "Morgen" then return false, tostring(r[1].name) .. ", " .. tostring(r[2].name), "Heute später, Morgen" end
			for i, e in ipairs(r) do
				if e.t < now then return false, "vergangen: " .. e.name, "nur kommende" end
				if i > 1 and e.t < r[i - 1].t then return false, "nicht aufsteigend", "aufsteigend" end
				for k in pairs(e) do if k ~= "t" and k ~= "name" then return false, "Feld " .. tostring(k), "nur t und name" end end
			end
			-- fehlerfest: Quelle wirft / liefert Unsinn -> leere Liste, kein Fehler
			S.KnownRaids = function() error("kaputt") end
			if type(API.UpcomingRaids()) ~= "table" or #API.UpcomingRaids() ~= 0 then return false, "nicht leer bei Fehler", "{}" end
			S.KnownRaids = function() return { "x", { t = "morgen" }, { name = 5, t = now + 60 } } end
			local r2 = API.UpcomingRaids()
			if #r2 ~= 1 or r2[1].name ~= "" then return false, #r2 .. " bei Unsinn", "1 mit leerem Namen" end
			-- echte Quelle: Anmeldung aus Discord, Testraid nie
			S.KnownRaids = savedKnown
			RM.db.signup = { title = "MC Donnerstag", start = now + 3600, list = { { name = "Testa" } } }
			local r3 = API.UpcomingRaids()
			if #r3 ~= 1 or r3[1].name ~= "MC Donnerstag" or r3[1].list then return false, #r3 .. " aus Anmeldung", "1, ohne Liste" end
			RM.db.signup = { title = "TEST Raid", test = true, start = now + 3600, list = {} }
			if #API.UpcomingRaids() ~= 0 then return false, "Testraid geliefert", "0" end
			RM.db.signup = { title = "Vorbei", start = now - 3600, list = {} }
			if #API.UpcomingRaids() ~= 0 then return false, "vergangener Raid geliefert", "0" end
			return true, "20 von 29 (gestern/heute früher weg), nur t+name, Fehler -> {}, Anmeldung 1, Testraid 0"
		end)
		S.KnownRaids, RM.db.signup = savedKnown, savedSignup
		if not ok then return false, "Lua: " .. tostring(res), "kein Fehler" end
		return res, info
	end)

	-- 3.0.30 (TR-ALLE): /reload mitten im Lauf -> beim nächsten Einloggen alles zurück; Sicherung liegt während des Laufs vor
	t:Check("T189", "J", "TR-ALLE sauber nach /reload (Sicherung)", function()
		if not (R.SetGuard and R.RestoreGuard and R.ClearGuard) then return false, "fehlt", "3.0.30" end
		if type(RaidMasterDB.routineGuard) ~= "table" then return false, "keine Sicherung während des Laufs", "RaidMasterDB.routineGuard" end
		local fake = { lootdb = { a = 1, b = { c = 2 } }, records = { x = 1 }, keep = "bleibt" }
		local lootRef = fake.lootdb
		R.SetGuard(fake)
		fake.lootdb.a = 99; fake.lootdb.b = nil; fake.records = nil; fake.foreign = { neu = true }
		if not R.RestoreGuard(fake) then return false, "nicht wiederhergestellt", "true" end
		if fake.lootdb ~= lootRef or fake.lootdb.a ~= 1 or not (fake.lootdb.b and fake.lootdb.b.c == 2) then return false, "lootdb", "wie vorher (gleiche Tabelle)" end
		if not (fake.records and fake.records.x == 1) then return false, "records", "zurück" end
		if fake.foreign ~= nil then return false, "foreign noch da", "nil (gab es vorher nicht)" end
		if fake.routineGuard ~= nil or fake.keep ~= "bleibt" then return false, "Sicherung/fremder Schlüssel", "weg / unverändert" end
		if R.RestoreGuard(fake) then return false, "zweimal", "nur einmal" end
		return true, "Sicherung im Lauf da; nach Abbruch: Inhalt zurück (gleiche Tabellen), Neues weg, nur einmal"
	end)

	-- 3.0.41 (Hinweis 20.11. 08:40, Regel 4): Gegenprobe – eine absichtlich geänderte Zahl MUSS erkannt werden. Nur an KOPIEN
	-- (eigene SavedVariables und gemeinsames Adressbuch), nie an echten Daten.
	t:Check("T198", "J", "Livedaten-Wächter: absichtlich geänderte Felder werden erkannt (Kopien)", function()
		-- eigene SavedVariables: Schnappschuss-Vergleich
		local saved = RaidMasterDB
		local copy = Deep(RaidMasterDB or {})
		copy.data = type(copy.data) == "table" and copy.data or {}
		local fakeSnap = { db = {} }
		for k, v in pairs(copy) do if not SB_SKIP[k] then fakeSnap.db[k] = Deep(v) end end
		if type(fakeSnap.db.config) == "table" then fakeSnap.db.config.positions, fakeSnap.db.config.mainSize = nil, nil end   -- wie Snapshot()
		copy.data.gegenprobe = (copy.data.gegenprobe or 0) + 1
		RaidMasterDB = copy
		local ok, d1 = pcall(Compare, fakeSnap)
		RaidMasterDB = saved
		if not ok then return false, tostring(d1), "Vergleich läuft" end
		if #d1 ~= 1 or not tostring(d1[1]):find("gegenprobe", 1, true) then
			return false, "eigene Daten: " .. table.concat(d1, ", "), "genau 1 Abweichung data.gegenprobe"
		end
		if RaidMasterDB ~= saved then return false, "RaidMasterDB vertauscht", "unverändert" end
		-- gemeinsames Adressbuch: Kopie, ein Fehlzähler und eine Pause geändert
		local fakeBook = { A = { fail = 0, pause = 0, v = 3, src = "RM", seen = 1 }, B = { fail = 1, pause = 0, v = 3, seen = 2 } }
		local before = SyncPrint(fakeBook)
		fakeBook.B.seen = 99                                    -- Hintergrund: gehört nicht der Routine -> kein Befund
		fakeBook.C = { fail = 0, v = 3 }                        -- neuer Kontakt im Hintergrund -> kein Befund
		if #SyncDiff(before, fakeBook) ~= 0 then return false, "seen/neuer Eintrag als Befund", "0" end
		fakeBook.A.fail, fakeBook.B.pause = 1, 600
		local d2 = SyncDiff(before, fakeBook, true)
		if #d2 ~= 2 then return false, "Adressbuch: " .. table.concat(d2, ", "), "2 Abweichungen" end
		if fakeBook.A.fail ~= 0 or fakeBook.B.pause ~= 0 then return false, "nicht zurückgesetzt", "zurückgesetzt" end
		for _, x in ipairs(d2) do if x:find("[AB]$") or x:find(" [AB]%.") then return false, x, "ohne Namen" end end
		return true, "eigene Daten 1/1 erkannt · Adressbuch 2/2 erkannt und zurückgesetzt, seen/neue Einträge kein Befund"
	end)

	-- 3.0.41 (L1/L8): Gegenprobe der Lesbarkeits-Prüfung mit nachgebauten Texten (dunkelgraue Zahl -> Befund)
	t:Check("T200", "J", "Lesbarkeit: Gegenprobe – dunkelgraue Zahl, kleine Schrift werden erkannt", function()
		local U = RM.UICheck
		if not (U and U.CheckReadable) then return false, "UICheck fehlt", "vorhanden" end
		local function FS(text, r, g, b, size)
			return { GetText = function() return text end, GetTextColor = function() return r, g, b, 1 end,
				GetFont = function() return "x", size end }
		end
		local bg = { 0.08, 0.08, 0.1 }
		local cases = {
			{ "weisse Zahl", FS("1250", 1, 1, 1, 12), 0 },
			{ "gelb (Gold)", FS("|cffffd100Gold|r", 1, 1, 1, 12), 0 },
			{ "dunkelgraue Zahl", FS("1250", 0.35, 0.35, 0.35, 12), 1 },
			{ "graue Zahl im Farbcode", FS("DKP |cff555555250|r", 1, 1, 1, 12), 1 },
			{ "Schrift 8", FS("Text", 1, 1, 1, 8), 1 },
		}
		for _, c in ipairs(cases) do
			local p = U.CheckReadable(c[2], c[1], bg, 10)
			if #p ~= c[3] then return false, c[1] .. ": " .. #p .. " Befund(e) " .. table.concat(p, "; "), c[3] .. " Befund(e)" end
		end
		local w = U.Contrast({ 1, 1, 1 }, { 0, 0, 0 })
		if math.abs(w - 21) > 0.01 then return false, string.format("Weiss/Schwarz %.2f", w), "21:1" end
		return true, "5 Fälle richtig (2 lesbar, 2 Kontrast-Befunde, 1 Schrift-Befund), Weiss/Schwarz 21:1"
	end)

	-- RM-I2 (3.0.42): Klassenfarben in Namen lesbar (ab 4,5:1 auch auf dem überfahrenen Knopf); Gegenprobe: Rohfarbe Schamane
	t:Check("T201", "J", "Klassenfarben lesbar (ab 4,5:1 auf Knopf-Hintergrund, Gegenprobe Schamane roh)", function()
		local C = RAID_CLASS_COLORS
		if type(C) ~= "table" or not RM.Contrast then return false, "RAID_CLASS_COLORS/RM.Contrast fehlt", "vorhanden" end
		local bgs = { UI_BG = { 0.12, 0.125, 0.15 }, HOVER = { 0.16, 0.165, 0.2 } }
		local worst, wname, n = 99, "", 0
		for class, c in pairs(C) do
			local hex = RM.ClassColor(class, "x"):match("|cff(%x%x%x%x%x%x)")
			if hex and c.r then
				n = n + 1
				local r, g, b = tonumber(hex:sub(1, 2), 16) / 255, tonumber(hex:sub(3, 4), 16) / 255, tonumber(hex:sub(5, 6), 16) / 255
				for _, bg in pairs(bgs) do
					local k = RM.Contrast(r, g, b, bg[1], bg[2], bg[3])
					if k < worst then worst, wname = k, class end
				end
			end
		end
		if n == 0 then return false, "keine Klassenfarbe", "> 0" end
		if worst < 4.5 then return false, string.format("%s %.2f:1", wname, worst), "ab 4,5:1" end
		-- Gegenprobe: dieselbe Prüfung findet die Rohfarbe (ohne Aufhellen) des Schamanen
		local raw = RM.Contrast(0, 0.44, 0.87, 0.16, 0.165, 0.2)
		if raw >= 4.5 then return false, string.format("Rohfarbe Schamane %.2f:1", raw), "unter 4,5:1 (Gegenprobe)" end
		return true, string.format("%d Klassen, schlechteste %s %.2f:1 · Gegenprobe Rohfarbe Schamane %.2f:1 erkannt", n, wname, worst, raw)
	end)

	-- RM-I2 Rest (3.0.43): Qualitätsfarben in Item-Links lesbar (nur Anzeige), Link selbst unverändert; Gegenprobe Rohfarben
	t:Check("T202", "J", "Item-Qualitätsfarben in Anzeige lesbar, Link-Teil unverändert (Gegenprobe Episch/Selten roh)", function()
		if not RM.ReadableText then return false, "RM.ReadableText fehlt", "vorhanden" end
		local function C(hex) return tonumber(hex:sub(1, 2), 16) / 255, tonumber(hex:sub(3, 4), 16) / 255, tonumber(hex:sub(5, 6), 16) / 255 end
		local worst, raw = 99, 99
		for _, hex in ipairs({ "9d9d9d", "ffffff", "1eff00", "0070dd", "a335ee", "ff8000" }) do
			local link = "|cff" .. hex .. "|Hitem:16800::::::::60:::::|h[Test]|h|r"
			local out = RM.ReadableText(link)
			if out:gsub("^|cff%x%x%x%x%x%x", "") ~= link:gsub("^|cff%x%x%x%x%x%x", "") then return false, "Link verändert: " .. out, "nur Farbe" end
			local r, g, b = C(out:match("^|cff(%x%x%x%x%x%x)"))
			worst = math.min(worst, RM.Contrast(r, g, b, 0.16, 0.165, 0.2), RM.Contrast(r, g, b, 0.12, 0.125, 0.15))
			local r0, g0, b0 = C(hex)                       -- (mitten in einer Argumentliste gäbe C() nur einen Wert)
			raw = math.min(raw, RM.Contrast(r0, g0, b0, 0.16, 0.165, 0.2))
			if hex == "ffffff" and out ~= link then return false, "lesbare Farbe geändert", "unverändert" end
		end
		if worst < 4.5 then return false, string.format("schlechteste %.2f:1", worst), "ab 4,5:1" end
		if raw >= 4.5 then return false, string.format("Rohfarben %.2f:1", raw), "unter 4,5:1 (Gegenprobe)" end
		if RM.ReadableText("ohne Farbe") ~= "ohne Farbe" then return false, "Text ohne Farbe verändert", "unverändert" end
		return true, string.format("6 Qualitäten, schlechteste %.2f:1 · Gegenprobe roh %.2f:1 erkannt · Link-Teil gleich", worst, raw)
	end)

	-- RM-UMG1 d) Gegenprobe (Nachbau der Bilder): dieselbe Überschreitung ohne Hintergrund -> FEHLER; mit Hintergrund (Bildgrenze
	-- 33 ms oder Sprung auf das Doppelte), Ladebildschirm oder Speicherbereinigung -> "Bedienung/Umgebung möglich"
	t:Check("T203", "J", "Umgebung: Überschreitung ohne Hintergrund FEHLER, mit Hintergrund/Laden/Bereinigung Hinweis (Gegenprobe)", function()
		local function Sim(cap, frames)
			local e = R.NewEnv()
			e.capBk = cap
			R.EnvStart(e, 100)
			for _, f in ipairs(frames) do
				e.phase = f[1] < 101 and "vorher" or "Lauf"
				if f[3] == "laden" then e.loading = true else e.loading = false end
				if f[3] == "gc" then e.gcMark = true end
				R.EnvFrame(e, f[2], f[1])
			end
			return e
		end
		local function Frames(from, to, ms, tag)
			local out, t = {}, from
			while t < to do out[#out + 1] = { t, ms, tag }; t = t + ms / 1000 end
			return out
		end
		local function Join(...)
			local out = {}
			for _, l in ipairs({ ... }) do for _, f in ipairs(l) do out[#out + 1] = f end end
			return out
		end
		local fail = { true, false, "12.0 ms", "< 2 ms" }              -- wie pcall(Prüfung): ok, false, Ergebnis, Grenze
		local pass = { true, true, "0.5 ms" }
		-- Vordergrund (9 ms) -> FEHLER bleibt
		local fg = Sim(1000 / 30, Join(Frames(100, 101, 9), Frames(101, 106, 9)))
		if R.PerfVerdict(fg, 103.2, 103.8, fail[1], fail[2]) ~= nil then return false, "Vordergrund als Umgebung", "FEHLER bleibt" end
		-- Hintergrund über die Bildgrenze (33 ms) in Sek. 3–4
		local bg = Sim(1000 / 30, Join(Frames(100, 101, 9), Frames(101, 102, 9), Frames(102, 104, 33.3), Frames(104, 106, 9)))
		local w1 = R.PerfVerdict(bg, 102.2, 102.9, fail[1], fail[2])
		if not (w1 and w1:find("Hintergrund", 1, true)) then return false, "Hintergrund (Grenze) nicht erkannt: " .. tostring(w1), "Hinweis" end
		if R.PerfVerdict(bg, 104.2, 104.9, fail[1], fail[2]) ~= nil then return false, "nach dem Hintergrund noch Umgebung", "FEHLER" end
		if R.PerfVerdict(bg, 102.2, 102.9, pass[1], pass[2]) ~= nil then return false, "bestandene Prüfung verändert", "OK bleibt" end
		-- ohne bekannte Bildgrenze: Sprung auf mehr als das Doppelte
		local jump = Sim(nil, Join(Frames(100, 101, 9), Frames(101, 103, 28)))
		local w2 = R.PerfVerdict(jump, 101.2, 101.8, fail[1], fail[2])
		if not (w2 and w2:find("Hintergrund", 1, true)) then return false, "Sprung nicht erkannt: " .. tostring(w2), "Hinweis" end
		-- langsamer Rechner (immer 28 ms, auch vorher) -> kein Hintergrund -> FEHLER bleibt
		local slow = Sim(nil, Join(Frames(100, 101, 28), Frames(101, 103, 28)))
		if R.PerfVerdict(slow, 101.2, 101.8, fail[1], fail[2]) ~= nil then return false, "gleichmässig langsam als Umgebung", "FEHLER" end
		-- Ladebildschirm, Speicherbereinigung
		local ld = Sim(1000 / 30, Join(Frames(100, 101, 9), { { 101.5, 300, "laden" } }, Frames(101.8, 103, 9)))
		local w3 = R.PerfVerdict(ld, 101.1, 101.9, fail[1], fail[2])
		if not (w3 and w3:find("Ladebildschirm", 1, true)) then return false, "Laden nicht erkannt: " .. tostring(w3), "Hinweis" end
		local gc = Sim(1000 / 30, Join(Frames(100, 101, 9), { { 101.5, 12, "gc" } }, Frames(101.6, 103, 9)))
		local w4 = R.PerfVerdict(gc, 101.1, 101.9, fail[1], fail[2])
		if not (w4 and w4:find("Speicherbereinigung", 1, true)) then return false, "Bereinigung nicht erkannt: " .. tostring(w4), "Hinweis" end
		-- Kopfzeile
		local l1, l2 = R.EnvLine(fg), R.EnvLine(bg)
		if not (l1:find("Vordergrund", 1, true) and l2:find("Hintergrund möglich (Sek. 3–4", 1, true)) then
			return false, l2:sub(1, 120), "Vordergrund / Hintergrund möglich (Sek. 3–4 …)"
		end
		return true, "Vordergrund FEHLER · Bildgrenze/Sprung/Laden/Bereinigung Hinweis · gleichmässig langsam FEHLER · Kopfzeile richtig"
	end)

	-- 3.0.45 (Lesbarkeit L4, Hinweis 20.11. 13:50): Summen gehen auf – Stand = Summe der Buchungen, Kopfsumme = Summe der Zeilen,
	-- "verdient" = Gutschriften ohne Rückgängiges; eigener Nachbau-Datensatz (nie echte Daten), Erwartung von Hand gerechnet
	local function SumCheck(data)
		local bad, sum = {}, {}
		for _, e in ipairs(data.log) do
			local pool = e.pool or "mc"
			for n, d in pairs(e.d or {}) do sum[n .. "|" .. pool] = (sum[n .. "|" .. pool] or 0) + d end
		end
		for n, p in pairs(data.players) do
			for pool, v in pairs(p.d or {}) do
				if v ~= (sum[n .. "|" .. pool] or 0) then bad[#bad + 1] = n .. " " .. pool .. " Stand " .. v .. " ≠ Buchungen " .. (sum[n .. "|" .. pool] or 0) end
				sum[n .. "|" .. pool] = nil
			end
		end
		for k, v in pairs(sum) do if v ~= 0 then bad[#bad + 1] = k .. " Buchungen " .. v .. " ohne Stand" end end
		table.sort(bad)
		return bad
	end
	t:Check("T204", "J", "L4 Summen gehen auf: Stand = Buchungen, Gesamt = Zeilen, verdient ohne Rückgängiges (Gegenprobe)", function()
		local DKP = RM.DKP
		local data = { version = 0, players = {}, log = {}, firstKills = {}, lastDecay = 0, pools = {}, knownBosses = {}, earnedInit = true }
		local A, B, C, D = "Testa", "Bob", "Cleo", "Offi"
		local list = {
			{ id = "t1", k = "start", pool = "mc", d = { [A] = 10, [B] = 10, [C] = 10 } },
			{ id = "t2", k = "boss", pool = "mc", d = { [A] = 15, [B] = 15, [C] = 15 } },
			{ id = "t3", k = "item", pool = "mc", d = { [A] = -40 } },
			{ id = "t4", k = "manual", pool = "mc", d = { [B] = 7 } },
			{ id = "t5", k = "undo", r = "t4", pool = "mc", d = { [B] = -7 } },
			{ id = "t6", k = "decay", pool = "mc", d = { [B] = -3, [C] = -3 }, t = 1 },
			{ id = "t7", k = "bench", pool = "ony", d = { [D] = 10 } },
			{ id = "t8", k = "manual", pool = "ony", d = { [A] = 20 } },
		}
		for _, e in ipairs(list) do
			if not DKP.ApplyEntryTo(data, e, false) then return false, "Buchung " .. e.id .. " nicht angewendet", "angewendet" end
		end
		if DKP.ApplyEntryTo(data, list[2], false) then return false, "Buchung t2 doppelt angewendet", "nur einmal" end
		-- von Hand: mc Testa 10+15-40 = -15, Bob 10+15+7-7-3 = 22, Cleo 10+15-3 = 22; ony Offi 10, Testa 20
		local want = { [A .. "|mc"] = -15, [B .. "|mc"] = 22, [C .. "|mc"] = 22, [D .. "|ony"] = 10, [A .. "|ony"] = 20 }
		for k, v in pairs(want) do
			local n, pool = k:match("^(.-)|(.+)$")
			if DKP.PoolValue(data.players[n], pool) ~= v then return false, k .. " = " .. DKP.PoolValue(data.players[n], pool), v end
		end
		local bad = SumCheck(data)
		if #bad > 0 then return false, table.concat(bad, "; "), "Stand = Summe der Buchungen" end
		-- Kopfsumme = Summe der Zeilen (wie die Liste), Zahl der Spieler mit Stand, "verdient" ohne Abzüge und ohne Rückgängiges
		local hand = { mc = { 29, 3, 75 }, ony = { 30, 2, 30 } }
		for pool, h in pairs(hand) do
			local total, count, earned = DKP.PoolTotal(data, pool)
			local rows, rsum, rcount = DKP.SortedPlayers(pool, data), 0, 0
			for i, r in ipairs(rows) do
				rsum = rsum + r.dkp
				if r.dkp ~= 0 then rcount = rcount + 1 end
				if i > 1 and rows[i - 1].dkp < r.dkp then return false, pool .. " Reihenfolge", "absteigend" end
			end
			if total ~= rsum or count ~= rcount then return false, string.format("%s Gesamt %d/%d, Zeilen %d/%d", pool, total, count, rsum, rcount), "gleich" end
			if total ~= h[1] or count ~= h[2] or earned ~= h[3] then
				return false, string.format("%s %d DKP · %d Spieler · %d verdient", pool, total, count, earned), string.format("%d · %d · %d (von Hand)", h[1], h[2], h[3])
			end
		end
		-- "verdient" nachgerechnet aus dem Log (wie bei alten Daten) = laufend mitgezählt
		local copy = Deep(data)
		copy.earnedInit = nil
		DKP.InitEarned(copy)
		for n, p in pairs(data.players) do
			for pool, v in pairs(p.e or {}) do
				if DKP.Earned(copy.players[n], pool) ~= v then return false, n .. " " .. pool .. " verdient " .. v .. " / nachgerechnet " .. DKP.Earned(copy.players[n], pool), "gleich" end
			end
		end
		-- Gegenprobe: ein um 1 verfälschter Stand und eine verfälschte Buchung werden erkannt (je genau 1 Befund)
		local g1 = Deep(data)
		g1.players[A].d.mc = g1.players[A].d.mc + 1
		local b1 = SumCheck(g1)
		if #b1 ~= 1 or not b1[1]:find(A .. " mc", 1, true) then return false, "Gegenprobe Stand: " .. table.concat(b1, "; "), "1 Befund " .. A .. " mc" end
		local g2 = Deep(data)
		g2.log[7].d[D] = 11
		local b2 = SumCheck(g2)
		if #b2 ~= 1 or not b2[1]:find(D .. " ony", 1, true) then return false, "Gegenprobe Buchung: " .. table.concat(b2, "; "), "1 Befund " .. D .. " ony" end
		return true, "8 Buchungen (mit Rückgängig und Verfall): Stände = von Hand, Gesamt mc 29/3/75 und ony 30/2/30 = Zeilen, verdient nachgerechnet gleich · Gegenprobe 2/2 erkannt"
	end)

	-- RM-TAINT1 / T156 (3.0.48): eigene Fenster weichen offenen Blizzard-Fenstern aus – Rechnung (BestPlace) und Verschieben an
	-- nachgebauten Fenstern (keine echten Blizzard-Fenster, nichts öffnen); Gegenproben: kein Platz -> Rest-Überdeckung, verdecktes
	-- Fenster nicht sichtbar -> kein Verschieben, im Kampf -> kein Verschieben
	t:Check("T206", "J", "Fenster weichen Blizzard-Fenstern aus (Rechnung und Verschieben, Gegenproben)", function()
		local U = RM.UICheck
		if not (U and U.BestPlace and RM.UIAvoidOthers) then return false, "fehlt", "U.BestPlace, RM.UIAvoidOthers" end
		-- Rechnung: Bildschirm 1920x1080, Charakterfenster links oben (0..400, oben 1000..400), eigenes Fenster 600x500 bei (100, 900)
		local char = { l = 0, r = 400, t = 1000, b = 400, name = "CharacterFrame" }
		local best, cover = U.BestPlace(100, 900, 600, 500, 1920, 1080, { char })
		if cover ~= 0 then return false, "Überdeckung " .. cover, "0" end
		if U.Overlap({ l = best.l, r = best.l + 600, t = best.t, b = best.t - 500 }, char) > 0 then return false, "überdeckt noch", "frei" end
		if best.l ~= 408 or best.t ~= 900 then return false, best.l .. "/" .. best.t, "408/900 (8 Pixel rechts daneben, gleiche Höhe)" end
		local _, full = U.BestPlace(100, 900, 600, 500, 1920, 1080, { { l = 0, r = 1920, t = 1080, b = 0 } })
		if full <= 0 then return false, "kein Platz nicht erkannt", "> 0" end
		-- Verschieben an nachgebauten Fenstern
		local function Fake(l, b, w, h, shown)
			local f = { pts = {} }
			function f:IsVisible() return shown end
			function f:GetRect() return l, b, w, h end
			function f:GetEffectiveScale() return 1 end
			function f:ClearAllPoints() self.pts = {} end
			function f:SetPoint(...) self.pts = { ... } end
			return f
		end
		local ui = { GetWidth = function() return 1920 end, GetHeight = function() return 1080 end, GetEffectiveScale = function() return 1 end }
		local char = Fake(0, 400, 400, 600, true)
		local fighting = false
		-- nachgebaute Umgebung statt Blizzard-Namen zu ersetzen (UIParent/InCombatLockdown ersetzen taintet sie bis /reload)
		local env = { parent = ui, blizzard = { "Char" }, lookup = function(n) return n == "Char" and char or nil end, others = {},
			combat = function() return fighting end }
		local mine = Fake(100, 400, 600, 500, true)
		if not RM.UIAvoidOthers(mine, env) then return false, "nicht verschoben", "verschoben" end
		if not (mine.pts[1] == "TOPLEFT" and mine.pts[2] == ui and mine.pts[4] == 408 and mine.pts[5] == 900 and RM.UIAvoidLast.free) then
			return false, table.concat({ tostring(mine.pts[1]), tostring(mine.pts[4]), tostring(mine.pts[5]) }, " "), "TOPLEFT 408 900, frei"
		end
		-- Gegenproben
		local m2 = Fake(1000, 400, 600, 500, true)
		if RM.UIAvoidOthers(m2, env) or #m2.pts > 0 then return false, "ohne Überdeckung verschoben", "bleibt" end
		char = Fake(0, 400, 400, 600, false)
		local m3 = Fake(100, 400, 600, 500, true)
		if RM.UIAvoidOthers(m3, env) then return false, "unsichtbares Fenster als Hindernis", "bleibt" end
		char = Fake(0, 400, 400, 600, true)
		fighting = true
		local m4 = Fake(100, 400, 600, 500, true)
		if RM.UIAvoidOthers(m4, env) then return false, "im Kampf verschoben", "nie im Kampf" end
		-- anderes GoldSentinel-Fenster ist Hindernis, dessen HUD nicht
		fighting = false
		char = Fake(0, 400, 400, 600, false)
		env.others = { { addon = "AHSentinel", name = "Hauptfenster", frame = Fake(0, 400, 400, 600, true) } }
		if not RM.UIAvoidOthers(Fake(100, 400, 600, 500, true), env) then return false, "GoldSentinel-Fenster nicht ausgewichen", "verschoben" end
		env.others = { { addon = "ThreatSentinel", name = "HUD", frame = Fake(0, 400, 400, 600, true) } }
		if RM.UIAvoidOthers(Fake(100, 400, 600, 500, true), env) then return false, "HUD als Hindernis", "bleibt" end
		return true, "rechts daneben (408/900) · kein Platz erkannt · GoldSentinel-Fenster ja, HUD nein · Gegenproben: frei/unsichtbar/Kampf -> bleibt"
	end)

	-- RM-K2 (3.0.49, Ingametest 3.0.48: Hauptfenster wich nicht aus): Ausweichen im ECHTEN Ablauf – richtige OnShow-Handler an allen
	-- eigenen Fenstern (ein späteres SetScript würde das Ausweichen löschen), Fenster zeigen + Ansicht wechseln, neu gebautes Fenster
	-- (sichtbar ohne OnShow). Hindernis = nachgebautes Fenster über RM.UIAvoidEnv (kein Blizzard-Fenster öffnen, keinen Namen ersetzen).
	local function BadHandlers(list)
		local bad = {}
		for _, o in ipairs(list) do
			if o.addon == "RaidMaster" and type(o.frame) == "table" and rawget(o.frame, "rmAvoid") and not RM.UI.avoidHandlers[o.frame:GetScript("OnShow") or 0] then
				bad[#bad + 1] = tostring(o.name)
			end
		end
		return bad
	end
	AsyncCheck(t, "T208", "J", "RM-K2 Fenster weichen im echten Ablauf aus (Zeigen, Ansicht, Neubau; Gegenproben)", function()
		local UI, U = RM.UI, RM.UICheck
		if InCombatLockdown and InCombatLockdown() then return ASYNC_SKIP, "im Kampf (Ausweichen ist im Kampf aus)" end
		local wasShown = Shown(MainFrame())
		local wasPage = UI.main and UI.main.current
		local probe, result
		local function Restore()
			RM.UIAvoidEnv = nil
			local m = MainFrame()
			if m then
				local pos = RM.db.config.positions.main
				m:ClearAllPoints()
				if pos then m:SetPoint(pos[1], UIParent, pos[2], pos[3], pos[4]) else m:SetPoint("CENTER", UIParent, "CENTER", 0, 20) end
				if wasPage then pcall(UI.ShowPage, wasPage) end
				if not wasShown then m:Hide() end
			end
			if probe then
				probe:Hide()
				for i = #GoldSentinelUIFrames, 1, -1 do if GoldSentinelUIFrames[i].frame == probe then table.remove(GoldSentinelUIFrames, i) end end
			end
		end
		local ok, a, b, c = pcall(function()
			UI.Open("dkp")
			local main = MainFrame()
			-- 1. alle eigenen Fenster: OnShow = Ausweich-Handler (Gegenprobe: ein einfaches SetScript wird erkannt)
			local bad = BadHandlers(GoldSentinelUIFrames)
			if #bad > 0 then return false, "OnShow ohne Ausweichen: " .. table.concat(bad, ", "), "alle über UI.OnShow" end
			local fake = { addon = "RaidMaster", name = "Gegenprobe", frame = { rmAvoid = true, GetScript = function() return function() end end } }
			if #BadHandlers({ fake }) ~= 1 then return false, "Gegenprobe SetScript nicht erkannt", "erkannt" end
			-- 2. Hauptfenster: Hindernis über seine linken 40 % -> verbergen, öffnen, Ansicht wechseln
			local mine = U.Rect(main)
			if not mine then return ASYNC_SKIP, "Lage des Hauptfensters nicht messbar" end
			local w = mine.r - mine.l
			local charShown = true
			local char = { l = mine.l - 10, r = mine.l + math.floor(w * 0.4), t = mine.t + 10, b = mine.b - 10 }
			local obj = { IsVisible = function() return charShown end, GetEffectiveScale = function() return 1 end,
				GetRect = function() return char.l, char.b, char.r - char.l, char.t - char.b end }
			RM.UIAvoidEnv = { blizzard = { "T208Char" }, lookup = function(n) return n == "T208Char" and obj or nil end, others = {} }
			main:Hide()
			UI.Open("auction")
			local after = U.Rect(main)
			if not RM.UIAvoidLast then return false, "Ausweichen nicht aufgerufen (OnShow)", "aufgerufen" end
			if not RM.UIAvoidLast.free then return ASYNC_SKIP, "kein freier Platz auf diesem Bildschirm" end
			local ov = U.Overlap(after, char)
			if ov > 0 then return false, string.format("überdeckt nach dem Öffnen: %d px²", ov), "0" end
			UI.ShowPage("loot")
			local ov2 = U.Overlap(U.Rect(main), char)
			if ov2 > 0 then return false, "nach Ansichtswechsel wieder überdeckt", "bleibt frei" end
			-- Gegenprobe: Hindernis unsichtbar -> öffnen verschiebt nicht
			charShown = false
			local before = U.Rect(main)
			main:Hide(); UI.Open("dkp")
			local now = U.Rect(main)
			if now.l ~= before.l or now.t ~= before.t then return false, "ohne Hindernis verschoben", "bleibt" end
			charShown = true
			-- 3. neu gebautes Fenster (sichtbar ohne OnShow) weicht im nächsten Bild aus
			local cw, ch = 300, 200
			probe = UI.Frame(UIParent, cw, ch, "T208 Prüffenster")
			local es = probe:GetEffectiveScale() or 1
			probe:ClearAllPoints()
			probe:SetPoint("TOPLEFT", UIParent, "BOTTOMLEFT", (char.l + 20) / es, (char.t - 20) / es)
			char = { l = char.l, r = char.r, t = char.t, b = char.b }
			return "wait"
		end)
		if not ok then Restore(); error(a, 0) end
		if a ~= "wait" then Restore(); if a == ASYNC_SKIP then return ASYNC_SKIP, b end return a, b, c end
		for _ = 1, 3 do R.Breathe(0) end
		Settle(0.1)
		R.Breathe(0)
		local pr = probe and U.Rect(probe)
		local charRect = RM.UIAvoidEnv and RM.UIAvoidEnv.lookup("T208Char")
		local cl, cb, cw2, ch2 = charRect:GetRect()
		local ov3 = pr and U.Overlap(pr, { l = cl, b = cb, r = cl + cw2, t = cb + ch2 }) or -1
		Restore()
		if ov3 ~= 0 then return false, "neu gebautes Fenster überdeckt: " .. ov3, "0 (weicht im nächsten Bild aus)" end
		return true, "alle eigenen Fenster mit Ausweich-Handler · Öffnen + Ansichtswechsel frei · Neubau weicht aus · Gegenproben: SetScript erkannt, ohne Hindernis bleibt"
	end)

	-- 3.0.45 (Lesbarkeit L3): dieselbe DKP-Zahl in der Liste, im Tooltip der Zeile, in der Antwort auf "!dkp" und in DKP.Get;
	-- die Kopfzeile "Gesamt" = Summe der Zeilen (L4 an der echten Anzeige). Testmodus-Daten, Flüstern nur über RM.Whisper.
	local function SameNumber(rows, tipOf, chatOf, getOf)
		local bad = {}
		for _, r in ipairs(rows) do
			R.Breathe(R.PRE_MS)                    -- Ingametest 3.0.47: eine Portion 6 ms -> je Zeile ein eigenes Bild, wenn nötig
			local tip, chat, get = tipOf(r), chatOf(r), getOf(r)
			if tip ~= r.dkp or chat ~= r.dkp or get ~= r.dkp then
				bad[#bad + 1] = string.format("%s Liste %s · Tooltip %s · !dkp %s · Stand %s", r.name, tostring(r.dkp), tostring(tip), tostring(chat), tostring(get))
			end
		end
		return bad
	end
	t:Check("T205", "J", "L3 gleiche DKP-Zahl in Liste, Tooltip, !dkp und Stand; Gesamt = Zeilen (Gegenprobe)", function()
		local UI, DKP, L = RM.UI, RM.DKP, RM.L
		TestRaid()
		local u = {}
		local wasShown, wasPage = Shown(MainFrame()), UI.main and UI.main.current
		local said = {}
		return Guard(function()
			Swap(u, RM.db.config, "whisperReplies", true)
			Swap(u, RM, "Whisper", function(text) said[#said + 1] = tostring(text) end)
			Swap(u, UI, "viewGuild", nil)
			local data = RM.db.data
			local pool = UI.viewPool or DKP.DefaultViewPool()
			-- genug verschiedene Zahlen: zwei Spieler mit Stand (einer negativ), falls die Testdaten noch keine haben
			local nonzero = 0
			for _, p in pairs(data.players) do if DKP.PoolValue(p, pool) ~= 0 then nonzero = nonzero + 1 end end
			if nonzero < 2 then
				local m = RM.RaidMembers()
				if #m < 2 then return false, #m .. " Spieler im Testraid", "≥ 2" end
				DKP.EnsurePlayer(m[1].name, m[1].class); DKP.Adjust(m[1].name, 37, "T205", pool)
				DKP.EnsurePlayer(m[2].name, m[2].class); DKP.Adjust(m[2].name, -12, "T205", pool)
			end
			if not Shown(MainFrame()) then UI.Toggle() end
			UI.ShowPage("dkp")
			UI.RefreshCurrent()
			local page = UI.pages.dkp
			local list, labels = page and page.frame and page.frame.list, {}
			local head = page and page.frame and page.frame.totalLabel
			if head and head.GetText then labels[1] = head:GetText() end
			local function Scan(fr, depth)
				if not fr or depth > 6 then return end
				if not list and type(fr.data) == "table" and fr.SetData and fr.data[1] and fr.data[1].dkp ~= nil then list = fr end
				for _, rg in ipairs({ fr.GetRegions and fr:GetRegions() or nil }) do
					if rg and rg.GetText and rg:GetText() then labels[#labels + 1] = rg:GetText() end
				end
				for _, c in ipairs({ fr.GetChildren and fr:GetChildren() or nil }) do Scan(c, depth + 1) end
			end
			if not (list and head) then Scan(page and page.frame, 0) end
			if not list then return false, "DKP-Liste ohne Zeilen", "Zeilen" end
			local rows = list.data
			-- Kopfzeile: Gesamt = Summe der Zeilen, Spieler = Zeilen mit Stand
			local sum, cnt = 0, 0
			for _, r in ipairs(rows) do sum = sum + r.dkp; if r.dkp ~= 0 then cnt = cnt + 1 end end
			local poolName = DKP.PoolName(pool, data)
			local wantHead = string.format(L["Gesamt %s: |cffff8c1a%d DKP|r · %d Spieler"], poolName, sum, cnt)
			local headOk = false
			for _, x in ipairs(labels) do if x == wantHead then headOk = true end end
			if not headOk then
				local seen = ""
				for _, x in ipairs(labels) do if x:find(poolName, 1, true) and x:find("DKP", 1, true) then seen = x end end
				return false, "Kopfzeile: " .. seen, wantHead
			end
			-- Zeilen prüfen: höchste, niedrigste und bis zu 10 weitere (Zeit)
			local pick = {}
			for i, r in ipairs(rows) do if i <= 6 or i > #rows - 6 then pick[#pick + 1] = r end end
			local short = DKP.PoolShort(pool, data)
			local function tipOf(r)
				local lines = {}
				local tt = { AddLine = function(_, s) lines[#lines + 1] = tostring(s) end, AddDoubleLine = function(_, a) lines[#lines + 1] = tostring(a) end }
				if type(r.tooltip) ~= "function" then return "kein Tooltip" end
				r.tooltip(tt)
				for _, s in ipairs(lines) do
					local want = string.format(L["%s: aktuell %d DKP"], poolName, r.dkp)
					if s == want then return r.dkp end
				end
				return table.concat(lines, " / ")
			end
			local function chatOf(r)
				wipe(said)
				local errors, first = CallHandlers("CHAT_MSG_WHISPER", "!dkp " .. r.name, RM.Me())
				if errors > 0 then return "Fehler " .. tostring(first) end
				local text = said[#said]
				if not text then return "keine Antwort" end
				local body = text:match("^%[RaidMaster%] .-: (.*)$") or text
				for part in (body .. " · "):gmatch("(.-) · ") do
					if part:sub(1, #short + 1) == short .. " " then return tonumber(part:sub(#short + 2)) end
				end
				return 0                                   -- Topf ohne Stand steht nicht in der Antwort (= 0)
			end
			local function getOf(r) return DKP.Get(r.name, pool) end
			local bad = SameNumber(pick, tipOf, chatOf, getOf)
			if #bad > 0 then return false, table.concat(bad, " | "), "überall dieselbe Zahl" end
			-- Gegenprobe: eine um 1 verfälschte Listenzahl und eine verfälschte Antwort werden erkannt
			local fake = { { name = pick[1].name, dkp = pick[1].dkp + 1 } }
			local g1 = SameNumber(fake, function() return pick[1].dkp end, function() return pick[1].dkp end, function() return pick[1].dkp end)
			local g2 = SameNumber({ pick[1] }, function() return pick[1].dkp end, function() return pick[1].dkp - 1 end, getOf)
			if #g1 ~= 1 or #g2 ~= 1 then return false, "Gegenprobe " .. #g1 .. "/" .. #g2, "1/1" end
			return true, string.format("%d Zeilen von %d: Liste = Tooltip = !dkp = Stand (%s) · Gesamt %d DKP · %d Spieler = Zeilen · Gegenprobe 2/2 erkannt",
				#pick, #rows, poolName, sum, cnt)
		end, function()
			Undo(u)
			if UI.main then
				if wasPage then pcall(UI.ShowPage, wasPage) end
				if Shown(MainFrame()) ~= wasShown then pcall(UI.Toggle) end
			end
		end)
	end)

	-- 3.0.31 (Ingametest 17.11., T155): Tooltips verdecken keine Knöpfe – Platzierung neben, über, unter dem Fenster.
	-- Nachgebaute Rahmen (Bildschirm 1000 x 800, Skala 1); geprüft wird, wohin UI.PlaceTooltip den Tooltip setzt.
	t:Check("T190", "J", "Tooltip neben/über/unter dem Fenster (nie über Knöpfen)", function()
		local function Fake(l, b, w, h, parent)
			local f = { l = l, b = b, w = w, h = h, parent = parent, shown = true }
			function f:GetLeft() return self.l end
			function f:GetRight() return self.l + self.w end
			function f:GetBottom() return self.b end
			function f:GetTop() return self.b + self.h end
			function f:GetWidth() return self.w end
			function f:GetHeight() return self.h end
			function f:GetEffectiveScale() return 1 end
			function f:GetParent() return self.parent end
			function f:IsShown() return self.shown end
			function f:ClearAllPoints() self.point = nil end
			function f:SetPoint(p, rel, rp, x, y) self.point = { p, rel, rp, x or 0, y or 0 } end
			return f
		end
		local screen = Fake(0, 0, 1000, 800, nil)
		local cases = {
			-- Fenster l, b, w, h ; erwartet Punkt, Bezug (win/owner), Bezugspunkt
			{ "Platz rechts", { 100, 300, 400, 300 }, "TOPLEFT", "win", "TOPRIGHT" },
			{ "nur links", { 600, 300, 380, 300 }, "TOPRIGHT", "win", "TOPLEFT" },
			{ "breit, Platz oben", { 50, 100, 900, 400 }, "BOTTOMLEFT", "win", "TOPLEFT" },
			{ "breit oben, Platz unten", { 50, 450, 900, 340 }, "TOPLEFT", "win", "BOTTOMLEFT" },
			{ "Leiste am oberen Rand rechts", { 820, 770, 170, 30 }, "TOPRIGHT", "win", "TOPLEFT" },
			{ "kein Platz", { 10, 10, 980, 780 }, "BOTTOMLEFT", "owner", "TOPRIGHT" },
		}
		local bad = {}
		for _, c in ipairs(cases) do
			local w = c[2]
			local win = Fake(w[1], w[2], w[3], w[4], screen)
			local owner = Fake(w[1] + 10, w[2] + 5, 20, 20, win)
			local tip = Fake(0, 0, 250, 120, nil)
			RM.UI.PlaceTooltip(owner, tip, screen)
			local p = tip.point
			local rel = p and (p[2] == win and "win" or (p[2] == owner and "owner") or "?")
			if not (p and p[1] == c[3] and rel == c[4] and p[3] == c[5]) then
				bad[#bad + 1] = c[1] .. ": " .. (p and (p[1] .. " an " .. rel .. " " .. p[3]) or "kein Punkt")
			end
		end
		if #bad > 0 then return false, table.concat(bad, "; "), "jeder Fall richtig" end
		return true, #cases .. " Lagen richtig (rechts, links, über, unter, Leiste oben, sonst am Element)"
	end)

	-- 3.0.31 (Entscheid Supervisor 17.11., Ingametest T156): HUD-Anzeigen anderer Addons (LevelPilot-Pfeil, ThreatSentinel-
	-- Aggrometer …) zählen in der Überlappungs-Prüfung nicht; echte Fenster anderer GoldSentinel-Addons schon.
	-- Nachgebaute Rahmen; GoldSentinelUIFrames und RM.uiFrames werden nur in diesem einen Aufruf (ohne Bildwechsel) getauscht.
	t:Check("T191", "J", "Überlappung: HUD anderer Addons ausgenommen, Fenster nicht", function()
		local U = RM.UICheck
		if not (U and U.WindowsOverlapNothing and RM.IsForeignHUD) then return false, "fehlt", "UICheck mit HUD-Liste" end
		local function Fake(l, b, w, h)
			local f = {}
			function f:GetRect() return l, b, w, h end
			function f:IsVisible() return true end
			function f:GetEffectiveScale() return 1 end
			return f
		end
		local mine = Fake(100, 100, 400, 300)
		local tested, hudHints = 0, {}
		local savedMine, savedAll = RM.uiFrames, _G.GoldSentinelUIFrames
		local ok, problems = pcall(function()
			RM.uiFrames = { { frame = mine, name = "Hauptfenster" } }
			_G.GoldSentinelUIFrames = {
				{ frame = Fake(150, 150, 40, 40), name = "Pfeil", addon = "LevelPilot" },
				{ frame = Fake(200, 200, 60, 20), name = "Aggrometer", addon = "ThreatSentinel" },
				{ frame = Fake(300, 300, 80, 80), name = "Einstellungen", addon = "ThreatSentinel" },
				{ frame = Fake(120, 120, 30, 30), name = "Neu", addon = "AnderesAddon", kind = "hud" },
			}
			local pr, n, h = U.WindowsOverlapNothing()
			tested, hudHints = n, h
			return pr
		end)
		RM.uiFrames, _G.GoldSentinelUIFrames = savedMine, savedAll
		if not ok then return false, "Lua-Fehler " .. tostring(problems), "kein Fehler" end
		local text = table.concat(problems or {}, "; ")
		if #(problems or {}) ~= 1 or not text:find("Einstellungen", 1, true) then
			return false, (#(problems or {}) .. ": " .. text), "genau 1 (ThreatSentinel-Einstellungen)"
		end
		-- 3.0.32: HUD wird gemessen (zählt als geprüft) und als erlaubter Hinweis genannt – T156 ist so nie "nichts geprüft"
		if tested ~= 4 then return false, tested .. " gemessen", "4 (auch HUD)" end
		local h = table.concat(hudHints or {}, "; ")
		if #(hudHints or {}) ~= 3 or not h:find("Pfeil (LevelPilot) – HUD, erlaubt", 1, true) then return false, "Hinweise: " .. h, "3 HUD-Hinweise" end
		return true, "Pfeil, Aggrometer und Art 'hud' gemessen, aber erlaubt (4 gemessen, 3 Hinweise); echtes Fenster gemeldet"
	end)

	-- 3.0.32 (Ingametest 19:38, T158): Knopf-Beschriftungen passen sich an (Schrift kleiner, notfalls zwei Zeilen) – in jeder
	-- Sprache, weil gemessen wird. Nachgebaute Schrift: Breite = Zeichen x Grösse x 0,55 (wie STANDARD_TEXT_FONT ungefähr).
	t:Check("T192", "J", "Knopf-Beschriftungen passen (Schrift kleiner, notfalls zwei Zeilen)", function()
		if not RM.UI.FitText then return false, "fehlt", "UI.FitText" end
		local function FakeFS(text)
			local fs = { text = text, size = 12, wrap = false, lines = 1 }
			function fs:GetFont() return "Fonts\\FRIZQT__.TTF", self.size, "" end
			function fs:SetFont(_, size) self.size = size end
			function fs:GetStringWidth()
				local icons = 0
				local plain = self.text:gsub("|T.-|t", function() icons = icons + 1 return "" end)
				plain = plain:gsub("[\128-\191]", "")                  -- Zeichen zählen, nicht Bytes (UTF-8)
				return #plain * self.size * 0.6 + icons * self.size
			end
			function fs:SetWordWrap(w) self.wrap = w end
			function fs:SetMaxLines(n) self.lines = n end
			return fs
		end
		local cases = {
			-- Text, verfügbare Breite, Zeilen erlaubt, erwartet: passt in 1 Zeile? / 2 Zeilen?
			{ "Golemagg der Verbrenner |TInterface\\TargetingFrame\\UI-RaidTargetingIcon_8:0|t", 178, 1, "eine" },   -- Bosse & Symbole (190 x 19, mit Symbol)
			{ "7. Vor dem Raid: Anmeldungen holen", 222, 2, "eine" },     -- Discord-Anleitung (Knopf 236 x 26)
			{ "7. Перед рейдом: получить записи на рейд из Discord", 222, 2, "zwei" },
			{ "OK", 100, 1, "eine" },
		}
		local bad = {}
		for _, c in ipairs(cases) do
			local fs = FakeFS(c[1])
			RM.UI.FitText(fs, c[2], 12, 9, c[3])
			local width = fs:GetStringWidth()
			local fits = (not fs.wrap and width <= c[2]) or (fs.wrap and fs.lines == 2 and width <= c[2] * 2)
			local how = fs.wrap and "zwei" or "eine"
			if not fits or how ~= c[4] then bad[#bad + 1] = string.format("%s: %s Zeile(n), %.0f von %d px, Grösse %d", c[1], how, width, c[2], fs.size) end
			if c[1] == "OK" and fs.size ~= 12 then bad[#bad + 1] = "kurzer Text verkleinert (" .. fs.size .. ")" end
		end
		-- Gegenprobe: ohne Anpassung wären die beiden Knöpfe aus dem Ingametest abgeschnitten
		local g1, g2 = FakeFS("Golemagg der Verbrenner |TInterface\\TargetingFrame\\UI-RaidTargetingIcon_8:0|t"), FakeFS("7. Vor dem Raid: Anmeldungen holen")
		if not (g1:GetStringWidth() > 178 and g2:GetStringWidth() > 222) then bad[#bad + 1] = "Gegenprobe greift nicht" end
		if #bad > 0 then return false, table.concat(bad, "; "), "alle passen" end
		return true, #cases .. " Beschriftungen passen (Boss-Knopf und Anleitung aus dem Ingametest, Russisch zweizeilig)"
	end)

	-- 3.0.34 (BEFUND HOCH SOFORT 18.11.): andere Addons (GuildSentinel) lesen RaidMaster.db – während der Routine die ECHTEN Daten
	t:Check("T193", "J", "Fremde Leser sehen während der Routine keine Testdaten", function()
		local G = _G.RaidMaster
		if G == RM then return false, "RaidMaster ist RM selbst", "Durchreiche" end
		if not (RaidMasterAPI and RaidMasterAPI.TestRunning and RaidMasterAPI.TestRunning()) then return false, "TestRunning() false", "true während der Routine" end
		if not (R.snap and G.db.data == R.snap.db.data) then return false, "RaidMaster.db.data ist nicht die Kopie vom Start", "echte Daten" end
		if G.db.data == RM.db.data then return false, "RaidMaster.db.data = Testdaten", "echte Daten" end
		if G.UI ~= RM.UI or G.VERSION ~= RM.VERSION then return false, "Durchreiche unvollständig", "wie RM" end
		return true, "RaidMaster.db = Schnappschuss vom Start, TestRunning() true, Funktionen wie RM"
	end)

	-- 3.0.38 (OPT-ALLE, Entscheid des Nutzers 18.11. 10:27): neues Optionen-Fenster. Jede alte Option genau einmal (n alt = n neu),
	-- erreichbar mit denselben Rechten wie auf ihrer alten Seite, wirkt auf DENSELBEN Schlüssel wie vorher (Gegenprobe: gelesen wird
	-- direkt in RaidMasterDB, nicht über die Option), höchstens 12 Zeilen je Bereich, Suche findet jede Option, Optionen-Knöpfe öffnen
	-- den Bereich, "Standard" setzt die Standardwerte, Beschriftungen passen, Aufbau je Bereich unter 16 ms.
	-- Alte Liste = Bestandsaufnahme Schritt 1 (Bericht 18.11. 10:29): Schlüssel -> alte Seite (Rechte); nil = vorher ohne Schalter
	local OPT_OLD = {
		{ "settings.dkpStart", "settings" }, { "settings.dkpEnd", "settings" }, { "settings.standbyStartDKP", "settings" },
		{ "settings.defaultBossDKP", "settings" }, { "settings.bossDKP", "settings" }, { "settings.minBid", "settings" },
		{ "settings.bidIncrement", "settings" }, { "settings.auctionTime", "settings" }, { "settings.decayPct", "settings" },
		{ "settings.officerRank", "settings" }, { "settings.firstKillDouble", "settings" }, { "settings.antiSnipe", "settings" },
		{ "settings.allowNegative", "settings" }, { "settings.onlyOnline", "settings" }, { "settings.standbyGetsDKP", "settings" },
		{ "settings.mainBeforeTwink", "settings" }, { "settings.autoDecay", "raid", officer = true },
		{ "minimap.hide", "settings", all = true }, { "itemTooltip", "settings", all = true }, { "bankScan", "settings+bank" }, { "records", "settings", all = true },
		{ "marktTeilen", "settings", all = true },
		{ "rules.epic", "loot" }, { "rules.blue", "loot" }, { "rules.recipe", "loot" }, { "rules.mats", "loot" }, { "fallback", "loot" },
		{ "bankChar", "loot" }, { "deChar", "loot" }, { "crafterChar", "loot" }, { "lootMaster", "loot" }, { "lootThreshold", "loot" },
		{ "autoLoot", "loot" }, { "setLootOnStart", "loot" }, { "autoDistribute", "loot" }, { "announceLoot", "loot" },
		{ "announceBids", "loot" }, { "unlootedReminder", "loot" }, { "tradeFallback", "loot" }, { "whisperReplies", "loot" },
		{ "pullSeconds", "raid" }, { "breakMinutes", "raid" }, { "timerAddons", "raid" }, { "pullCountdownChat", "raid" },
		{ "welcome", "raid" }, { "fireResMin", "raid" }, { "coreHound", "raid" },
		{ "autoInvite", "signup" }, { "autoInviteMinutes", "signup" }, { "autoGroups", "signup" },
		{ "adChannel", "ad" }, { "adAutoInvite", "ad" },
		{ "markerTemplate", "lboss" }, { "markerBar", "lboss" }, { "markerLocked", "lboss" }, { "autoTemplate", "lboss" }, { "bossBar", "lboss" },
		{ "specScan", "specs" },
		{ "cmdHint" }, { "readyCheckGame" }, { "firstKillScreenshot" },
	}
	R.OPT_OLD = OPT_OLD
	local function OptPath(key)
		local base, path = RM.db.config, key
		if key:find("^settings%.") then base, path = RM.db.data.settings, key:sub(10) end
		return base, path
	end
	local function OptRaw(key)
		local t, path = OptPath(key)
		for part in path:gmatch("[^%.]+") do
			if type(t) ~= "table" then return nil end
			t = t[part]
		end
		return t
	end
	local function OptSetRaw(key, v)
		local t, path = OptPath(key)
		local parts = {}
		for part in path:gmatch("[^%.]+") do parts[#parts + 1] = part end
		for i = 1, #parts - 1 do t = t[parts[i]] end
		t[parts[#parts]] = v
	end
	local function Click(b)
		local f = b and b.GetScript and b:GetScript("OnClick")
		if type(f) ~= "function" then error("Knopf ohne OnClick") end
		f(b, "LeftButton")
	end
	local function OldVisible(page)
		local A = RM.UI.AccessOK
		if page == "settings+bank" then return A("leader") or A("bank") end
		return A(RM.UI.PAGE_ACCESS[page] or "lead")
	end
	AsyncCheck(t, "T194", "J", "OPT: Optionen-Fenster – jede alte Option genau einmal, wirkt wie vorher", function()
		local O, UI, T = RM.Opt, RM.UI, RM.Test
		if not (O and O.DEFS and UI.OpenOptions) then return false, "Options.lua fehlt", "RM.Opt" end
		TestRaid()
		local u = {}
		local bad = {}
		local function Bad(s) if #bad < 12 then bad[#bad + 1] = s end end
		local saved = 0
		local wasShown = Shown(MainFrame())
		local wasPage = UI.main and UI.main.current
		return Guard(function()
			-- (a) n alt = n neu, jede Option genau einmal
			local count, oldPage = {}, {}
			local officerOnly, forAll = {}, {}
			for _, o in ipairs(OPT_OLD) do oldPage[o[1]] = o[2] or false; officerOnly[o[1]] = o.officer; forAll[o[1]] = o.all end
			local nNew = 0
			for _, d in ipairs(O.DEFS) do
				if d.key then
					nNew = nNew + 1
					count[d.key] = (count[d.key] or 0) + 1
					if oldPage[d.key] == nil then Bad("neu, nicht in der alten Liste: " .. d.key) end
				end
			end
			for _, o in ipairs(OPT_OLD) do
				local c = count[o[1]] or 0
				if c ~= 1 then Bad(o[1] .. " " .. c .. "x") end
			end
			if nNew ~= #OPT_OLD then Bad("n neu " .. nNew .. " ≠ n alt " .. #OPT_OLD) end
			-- Rechte wie auf der alten Seite (je Rolle)
			local roleOld = T.role
			for _, role in ipairs({ "member", "lead", "looter", "raidlead" }) do
				T.role = role
				for _, d in ipairs(O.DEFS) do
					local pg = d.key and oldPage[d.key]
					if pg then
						-- officer: Schalter war für alle der Seite sichtbar, schalten durften nur Offiziere (NeedOfficer) -> wer
						-- ihn bedienen konnte, sieht ihn jetzt (autoDecay auf der Seite Raid)
						-- all: 3.0.40 bewusst für alle Spieler geöffnet (Entscheid 18.11. 11:10 – persönliche Optionen braucht jeder)
						local want = (forAll[d.key] or OldVisible(pg)) and not (d.cond and not d.cond()) and (not officerOnly[d.key] or RM.UI.AccessOK("leader"))
						if O.Visible(d) ~= want then Bad(role .. "/" .. d.key .. " sichtbar " .. tostring(O.Visible(d)) .. " (vorher " .. tostring(want) .. ")") end
					end
				end
			end
			T.role = roleOld
			-- gegen SettingsChanged (verteilt sonst an die Gilde – im Testmodus ohnehin zurückgehalten)
			Swap(u, RM.DKP, "SettingsChanged", function() saved = saved + 1 end)
			UI.Open("settings")
			local perArea, skipped = {}, {}
			for _, a in ipairs(O.AREAS) do
				R.Breathe(R.PRE_MS)
				-- (e) Optionen-Knopf öffnet den Bereich
				UI.OpenOptions(a.id)
				if O.current ~= a.id or not (UI.main and UI.main.current == "settings") then Bad("Knopf öffnet nicht " .. a.id) end
				a.expanded = true
				O.RefreshArea()
				if (a.lineCount or 99) > O.MAX_ROWS then Bad(a.id .. ": " .. tostring(a.lineCount) .. " Zeilen") end
				perArea[#perArea + 1] = a.id .. " " .. tostring(a.lineCount)
				if (O.buildMs[a.id] or 0) > 16 then Bad(string.format("Aufbau %s %.1f ms", a.id, O.buildMs[a.id])) end
				for _, d in ipairs(a.defs) do
					R.Breathe(R.PRE_MS)
					if not O.Visible(d) then
						skipped[#skipped + 1] = d.key or d.label
					elseif d.kind ~= "donate" then
						local row = O.RowOf(d) or (d.kind == "bosses" and a.rows[1])
						local ctrl = row and rawget(row, "ctrl")
						if not (row and row:IsShown() and ctrl) then Bad(tostring(d.key) .. ": Zeile nicht sichtbar")
						else
							-- (c) kurze Beschriftung: höchstens 28 Zeichen in der Sprache des Clients (UTF-8: Zeichen, nicht Bytes)
							local chars = #(tostring(d.label):gsub("[\128-\191]", ""))
							if chars > 28 then Bad(d.key .. ": " .. chars .. " Zeichen") end
							-- Beschriftung passt (eine Zeile, Breite gemessen)
							local w = row.label.GetStringWidth and row.label:GetStringWidth() or 0
							if type(w) == "number" and w > O.LABEL_W - 8 + 0.5 then Bad(d.key .. ": Text " .. math.floor(w) .. " px") end
							-- Suche findet die Option
							local found = false
							for _, h in ipairs(O.Search(d.label)) do if h == d then found = true end end
							if not found then Bad(d.key .. ": Suche findet sie nicht") end
							-- Wirkung auf den alten Schlüssel (direkt gelesen)
							local raw0 = OptRaw(d.key)
							local ok, err = pcall(function()
								if d.kind == "toggle" then
									local g0 = d.get() and true or false
									Click(ctrl)
									local r1 = OptRaw(d.key)
									if (r1 and true or false) ~= (not g0) or (r1 == nil) then Bad(d.key .. ": Schlüssel " .. tostring(raw0) .. " -> " .. tostring(r1)) end
									Click(ctrl)
									if (d.get() and true or false) ~= g0 then Bad(d.key .. ": zweiter Klick nicht zurück") end
								elseif d.kind == "choice" then
									for _, b in ipairs(ctrl.buttons) do
										Click(b)
										if OptRaw(d.key) ~= b.value then Bad(d.key .. "=" .. tostring(b.value) .. ": Schlüssel " .. tostring(OptRaw(d.key))) break end
									end
								elseif d.kind == "drop" then
									local item
									for _, g in ipairs(ctrl.build()) do for _, it in ipairs(g.items) do if it[1] ~= raw0 and it[1] ~= "" then item = item or it end end end
									if item then
										ctrl.setter(item[1])
										if OptRaw(d.key) ~= item[1] then Bad(d.key .. ": Schlüssel " .. tostring(OptRaw(d.key)) .. " statt " .. tostring(item[1])) end
									end
								elseif d.kind == "name" then
									ctrl:SetText("testbank")
									ctrl:GetScript("OnTextChanged")(ctrl, true)
									if OptRaw(d.key) == raw0 or OptRaw(d.key) ~= d.get() then Bad(d.key .. ": Schlüssel " .. tostring(OptRaw(d.key))) end
								elseif d.kind == "num" then
									local n0 = saved
									ctrl:SetText(tostring((tonumber(raw0) or 0) + 1))
									O.SaveGuild()
									if OptRaw(d.key) == raw0 then Bad(d.key .. ": Schlüssel unverändert " .. tostring(raw0)) end
									if saved ~= n0 + 1 then Bad(d.key .. ": nicht verteilt") end
								elseif d.kind == "bosses" then
									local st = a.bossState
									st.pool, st.page = "mc", 1
									O.RefreshArea()
									local br = st.rows[1]
									if not br.bossId then Bad("Boss-DKP: keine Bosse (mc)") else
										local id = br.bossId
										local b0 = RM.db.data.settings.bossDKP[id]
										br.ctrl:SetText("37")
										br.ctrl:GetScript("OnTextChanged")(br.ctrl, true)
										O.SaveGuild()
										if RM.db.data.settings.bossDKP[id] ~= 37 then Bad("Boss-DKP: " .. tostring(RM.db.data.settings.bossDKP[id])) end
										RM.db.data.settings.bossDKP[id] = b0
									end
								end
							end)
							if not ok then Bad(tostring(d.key) .. ": " .. tostring(err)) end
							if d.kind ~= "bosses" then OptSetRaw(d.key, raw0) end
						end
					end
				end
				a.expanded = nil
				O.RefreshArea()
			end
			-- (d) Standard: Wert verstellen, "Standard" -> Standardwert; NUR der eigene Bereich (Gegenprobe: Ansagen bleibt verstellt)
			local wel0 = RM.db.config.welcome
			RM.db.config.pullSeconds = 20
			RM.db.config.readyCheckGame = false
			RM.db.config.welcome = false
			O.ResetArea("raid")
			if RM.db.config.pullSeconds ~= RM.DEFAULT_CONFIG.pullSeconds or RM.db.config.readyCheckGame ~= true then
				Bad("Standard: Pull " .. tostring(RM.db.config.pullSeconds) .. ", Bereitschaft " .. tostring(RM.db.config.readyCheckGame))
			end
			if RM.db.config.welcome ~= false then Bad("Standard 'Raid & Timer' hat 'Begrüßung' (Ansagen) zurückgesetzt") end
			RM.db.config.welcome = wel0
			-- (b) Suche: Schlüssel findet genau seine Option, Unsinn und leer finden nichts
			local byKey = O.Search("pullseconds")
			if not (#byKey == 1 and byKey[1].key == "pullSeconds") then Bad("Suche 'pullseconds': " .. #byKey .. " Treffer") end
			if #O.Search("xqzxqz") ~= 0 or #O.Search("") ~= 0 then Bad("Suche Unsinn/leer findet etwas") end
			if #bad > 0 then return false, #bad .. ": " .. table.concat(bad, " | "):sub(1, 300), "jede Option genau einmal, wirkt auf ihren Schlüssel" end
			local maxMs = 0
			for _, v in pairs(O.buildMs) do if v > maxMs then maxMs = v end end
			return true, string.format("n alt %d = n neu %d, %d Bereiche (%s), Aufbau je Bereich höchstens %.1f ms, nicht für diesen Client: %s",
				#OPT_OLD, nNew, #O.AREAS, table.concat(perArea, ", "), maxMs, #skipped > 0 and table.concat(skipped, ", ") or "–")
		end, function()
			Undo(u)
			T.role = "raidlead"
			if UI.main then
				if wasPage then pcall(UI.ShowPage, wasPage) end
				if not wasShown then UI.main:Hide() end
			end
		end)
	end)

	-- 3.0.40 (Entscheid des Nutzers 18.11. 11:10, auftraege/hinweis-spieler-ohne-testbefehle): jede Spieler-Funktion ist OHNE
	-- Entwicklermodus über den normalen Weg erreichbar (Minimap, Fenster, /rm …, Einstellungsfenster des Spiels). Geprüft als normales
	-- Raidmitglied mit ausgeschaltetem Entwicklermodus (GoldSentinelDev.IsDev -> false).
	R.PLAYER_WAYS = {
		"Hauptfenster: /rm und Minimap-Linksklick", "Markierungsleiste: Minimap-Rechtsklick und /rm bar",
		"Einstellungen (Allgemein): /rm optionen, Einstellungsfenster des Spiels (Knopf 'Optionen öffnen'), Seite Einstellungen",
		"Persönliche Optionen für jeden: Minimap-Knopf, Item-Tooltip, Erstkill-Feier, Marktdaten, Befehlsliste, Screenshot, Unterstützen",
		"Alle /rm-Befehle ausser test, testroutine, prüfliste (Entwickler)",
	}
	AsyncCheck(t, "T195", "J", "Spieler-Funktionen ohne Entwicklermodus erreichbar (normaler Weg)", function()
		local O, UI, T = RM.Opt, RM.UI, RM.Test
		local GD = _G.GoldSentinelDev
		if not (O and UI.OpenOptions and GD) then return false, "Options.lua/GoldSentinelDev fehlt", "vorhanden" end
		local u, bad = {}, {}
		local function Bad(x) if #bad < 10 then bad[#bad + 1] = x end end
		local wasShown = Shown(MainFrame())
		local wasPage = UI.main and UI.main.current
		local bar0 = RM.db.config.markerBar
		return Guard(function()
			Swap(u, GD, "IsDev", function() return false end)
			if RM.IsDev() then return false, "Entwicklermodus liess sich nicht ausschalten", "aus" end
			Swap(u, T, "role", "member")
			-- Hauptfenster: /rm
			if Shown(MainFrame()) then UI.Toggle() end
			SlashCmdList["RAIDMASTER"]("")
			if not Shown(MainFrame()) then Bad("/rm öffnet das Fenster nicht") end
			R.Breathe(R.PRE_MS)
			-- Minimap: Linksklick schliesst/öffnet, Rechtsklick Markierungsleiste
			local mm = _G.RaidMasterMinimapButton
			local click = mm and mm.GetScript and mm:GetScript("OnClick")
			if type(click) ~= "function" then Bad("Minimap-Knopf ohne Klick")
			else
				click(mm, "LeftButton")
				if Shown(MainFrame()) then Bad("Minimap-Linksklick schliesst nicht") end
				click(mm, "LeftButton")
				if not Shown(MainFrame()) then Bad("Minimap-Linksklick öffnet nicht") end
				local b0 = RM.db.config.markerBar
				click(mm, "RightButton")
				if RM.db.config.markerBar == b0 then Bad("Minimap-Rechtsklick schaltet die Leiste nicht") end
				RM.db.config.markerBar = bar0
			end
			R.Breathe(R.PRE_MS)
			-- Einstellungen als Mitglied: nur Allgemein, mit allen persönlichen Optionen
			if not UI.CanSeePage("settings") then Bad("Mitglied sieht die Einstellungen nicht") end
			for _, a in ipairs(O.AREAS) do
				if O.AreaVisible(a) ~= (a.id == "allgemein") then Bad("Bereich " .. a.id .. (O.AreaVisible(a) and " sichtbar" or " fehlt")) end
			end
			local need = { "minimap.hide", "itemTooltip", "records", "marktTeilen", "cmdHint", "firstKillScreenshot" }
			for _, key in ipairs(need) do
				local found
				for _, d in ipairs(O.DEFS) do if d.key == key then found = d end end
				if not (found and O.Visible(found)) then Bad(key .. " für Mitglied nicht da") end
			end
			-- /rm optionen
			UI.ShowPage("dkp")
			SlashCmdList["RAIDMASTER"]("optionen")
			if not (UI.main and UI.main.current == "settings" and O.current == "allgemein") then Bad("/rm optionen öffnet nicht Allgemein") end
			R.Breathe(R.PRE_MS)
			-- Einstellungsfenster des Spiels: angemeldet, Knopf öffnet die Optionen
			local panel = O.gamePanel or O.RegisterGamePanel()
			if not O.gamePanelWay then Bad("nicht im Einstellungsfenster des Spiels angemeldet")
			else
				UI.ShowPage("dkp")
				local oc = panel.openButton and panel.openButton:GetScript("OnClick")
				if type(oc) ~= "function" then Bad("Knopf 'Optionen öffnen' fehlt") else
					oc(panel.openButton, "LeftButton")
					if not (UI.main and UI.main.current == "settings") then Bad("'Optionen öffnen' öffnet nicht die Einstellungen") end
				end
			end
			-- Befehle: nur test, testroutine, prüfliste sind Entwickler-Befehle; jeder andere ist ohne Entwickler da
			local devCmds = {}
			for _, c in ipairs(RM.COMMANDS) do
				if c.dev then devCmds[#devCmds + 1] = c[1] end
				local w = (c.words and c.words[1]) or c[1]:match("^(%S+)")
				if not c.dev and RM.FindCommand(w) ~= c then Bad("Befehl " .. c[1] .. " nicht erreichbar") end
			end
			table.sort(devCmds)
			if table.concat(devCmds, ",") ~= "prüfliste,test,testroutine" then Bad("Entwickler-Befehle: " .. table.concat(devCmds, ",")) end
			if #bad > 0 then return false, table.concat(bad, " | "), "alles ohne Entwicklermodus erreichbar" end
			return true, string.format("ohne Entwicklermodus als Mitglied: /rm, Minimap links/rechts, /rm optionen, Einstellungsfenster des Spiels (%s), %d persönliche Optionen; Entwickler-Befehle nur %s",
				tostring(O.gamePanelWay), #need, table.concat(devCmds, ", "))
		end, function()
			Undo(u)
			RM.db.config.markerBar = bar0
			if UI.main then
				if wasPage then pcall(UI.ShowPage, wasPage) end
				if Shown(MainFrame()) ~= wasShown then pcall(UI.Toggle) end
			end
		end)
	end)

	-- 3.0.24 (BL): Befehlsliste beim Tippen – eine Tabelle für Handler und Liste (T-BL1 … T-BL6)
	local function HintWith(dev, german)
		local H = RM.CmdHint
		local saved = { dev = H.dev, german = H.german, store = H.store, commands = H.commands, prefixes = H.prefixes,
			display = H.display, L = H.L, run = H.run, selected = H.selected }
		H.commands, H.prefixes, H.display, H.L = RM.COMMANDS, { "/raidmaster", "/rm" }, "/rm", RM.L
		H.dev = function() return dev end
		H.german = function() return german end
		local counts = {}
		H.store = function() return counts end
		return H, function() for k, v in pairs(saved) do H[k] = v end end
	end
	t:Check("T166", "J", "T-BL1 Befehlsliste: jeder Befehl des Handlers steht in der Liste", function()
		if not (RM.COMMANDS and RM.CmdHint and RM.FindCommand) then return false, "fehlt", "RM.COMMANDS/CmdHint" end
		local H, restore = HintWith(true, true)
		local ok, why = true, nil
		for _, german in ipairs({ true, false }) do
			H.german = function() return german end
			local list = H:List("")
			local shown = {}
			for _, it in ipairs(list) do shown[it.entry] = it end
			for i, c in ipairs(RM.COMMANDS) do
				if not shown[c] then ok, why = false, "fehlt in der Liste: " .. c[1] end
				-- angezeigtes Wort (de UND en) führt genau diesen Eintrag aus
				for _, form in ipairs({ c[1], c[2] }) do
					local run = H.RunWords(form)
					if RM.FindCommand(run) ~= c then ok, why = false, "'" .. form .. "' führt nicht " .. c[1] .. " aus" end
				end
				-- jedes Wort/Muster des Handlers gehört zu einem Eintrag der Liste (keine Befehle ausserhalb der Tabelle)
				for _, w in ipairs(c.words or {}) do
					if RM.FindCommand(w) == nil then ok, why = false, "Wort ohne Eintrag: " .. w end
				end
				if not c.run or not c[3] or c[3] == "" then ok, why = false, "Eintrag " .. i .. " ohne run/Beschreibung" end
			end
		end
		-- Der Slash-Handler liest aus derselben Tabelle: ein neuer Eintrag ist sofort ausführbar UND sichtbar
		local hit = 0
		local probe = { "zzprobe", "zzprobe", "Probe", words = { "zzprobe" }, run = function() hit = hit + 1 end }
		RM.COMMANDS[#RM.COMMANDS + 1] = probe
		local okRun = pcall(SlashCmdList["RAIDMASTER"], "zzprobe")
		local inList = false
		for _, it in ipairs(H:List("zz")) do if it.entry == probe then inList = true end end
		table.remove(RM.COMMANDS)
		restore()
		if not (okRun and hit == 1 and inList) then return false, "Probe: run " .. hit .. ", Liste " .. tostring(inList), "1 / true" end
		if not ok then return false, why, "vollständig" end
		return true, #RM.COMMANDS .. " Befehle, de und en ausführbar"
	end)

	t:Check("T167", "J", "T-BL2 Filter: genau die passenden Befehle, meistbenutzte oben", function()
		local H, restore = HintWith(false, true)
		local bad
		for _, rest in ipairs({ "", "b", "be", "ber", "p", "pu", "x", "lo", "gap" }) do
			local got = {}
			for _, it in ipairs(H:List(rest)) do got[it.entry] = true end
			for _, c in ipairs(RM.COMMANDS) do
				local want = not c.dev and (rest == "" or c[1]:lower():sub(1, #rest) == rest or c[2]:lower():sub(1, #rest) == rest)
				if (got[c] or false) ~= want then bad = "'" .. rest .. "': " .. c[1] .. " " .. tostring(got[c]) end
			end
		end
		H.store()["rekorde"] = 5
		local first = H:List("")[1]
		restore()
		if bad then return false, bad, "genau die passenden" end
		if not (first and first.key == "rekorde") then return false, first and first.key or "nil", "rekorde (meistbenutzt) oben" end
		return true, "Filter genau, Zähler sortiert"
	end)

	t:Check("T168", "J", "T-BL3 Klick wählt aus, Enter führt den gewählten Befehl aus", function()
		local H, restore = HintWith(false, false)
		local list = H:List("pu")                                   -- englisch: "pull <seconds>"
		local item = list[1]
		local ran = {}
		local orig = item and item.entry.run
		if not item or item.entry[1] ~= "pull <Sekunden>" then restore(); return false, item and item.cmd or "nil", "/rm pull <seconds>" end
		item.entry.run = function(msg) ran[#ran + 1] = msg end
		H:Select(item, true)                                        -- Klick = nur auswählen
		local before = #ran
		local okA = pcall(SlashCmdList["RAIDMASTER"], "pu")          -- Enter mit unvollständigem Wort
		local okB = pcall(SlashCmdList["RAIDMASTER"], "pull 15")     -- ohne Auswahl: getippter Befehl gilt
		item.entry.run = orig
		restore()
		if before ~= 0 then return false, "Klick führte aus", "nur auswählen" end
		if not (okA and okB and ran[1] == "pull" and ran[2] == "pull 15") then
			return false, tostring(ran[1]) .. " / " .. tostring(ran[2]), "pull / pull 15"
		end
		return true, "Auswahl -> Enter führt 'pull' aus"
	end)

	t:Check("T169", "J", "T-BL4 Chatfeld wird nie beschrieben", function()
		local H, restore = HintWith(false, true)
		local writes, focus = 0, 0
		-- 3.0.31: ein ECHTES (unsichtbares) Eingabefeld – CmdHint verankert seinen Rahmen daran, und SetPoint verlangt im Spiel
		-- einen echten Rahmen (Ingametest 17.11.: "SetPoint(): Wrong object type" mit einer Lua-Tabelle). Die Methoden, die zählen,
		-- sind nur auf diesem Feld überschrieben; es bekommt nie den Tastatur-Fokus (SetFocus ist ersetzt) und wird wiederverwendet.
		local box = R.t169Box
		if not box then
			box = CreateFrame("EditBox", nil, UIParent)
			box:SetAutoFocus(false)
			box:SetSize(400, 20)
			box:SetPoint("TOPLEFT", UIParent, "BOTTOMRIGHT", 100, -100)   -- ausserhalb des Bildschirms
			box:SetAlpha(0)
			box:EnableMouse(false)
			box:Hide()
			R.t169Box = box
		end
		box.GetText = function() return "/rm be" end
		box.SetText = function() writes = writes + 1 end
		box.Insert = function() writes = writes + 1 end
		box.SetCursorPosition = function() writes = writes + 1 end
		box.SetFocus = function() focus = focus + 1 end
		box.IsShown = function() return true end
		box.GetWidth = function() return 400 end
		local lastBox = H.lastBox
		local okAll, errAll = pcall(function()
			H:OnText(box)
			H:SelectNext(1)
			H:SelectNext(1)
			H:Select((H.items or {})[1], true)
			H.instantClose = true
			H:OnFocusLost(box)
			H.instantClose = nil
			H:Resolve("be")
			H:Hide()
		end)
		restore()
		H.lastBox, H.editBox = lastBox, nil                  -- das Testfeld nie als "letztes Chatfeld" behalten
		box:Hide()
		-- Quelltext-Regel: CmdHint benutzt nur HookScript, nie SetScript auf dem Chatfeld
		if not okAll then return false, "Lua-Fehler: " .. tostring(errAll):sub(1, 120), "kein Fehler" end
		if writes ~= 0 then return false, writes .. " Schreibzugriffe", "0" end
		if focus < 1 then return false, "kein SetFocus", "Fokus zurück" end
		return true, "0 Schreibzugriffe, Fokus zurück"
	end)

	t:Check("T170", "J", "T-BL5 Entwickler-Befehle nur für den Entwickler", function()
		local H, restore = HintWith(false, true)
		local devSeen = false
		for _, it in ipairs(H:List("")) do if it.entry.dev then devSeen = true end end
		H.dev = function() return true end
		local devAll = 0
		for _, it in ipairs(H:List("test")) do if it.entry.dev then devAll = devAll + 1 end end
		restore()
		if devSeen then return false, "Entwickler-Befehl sichtbar", "versteckt" end
		if devAll < 2 then return false, devAll, ">= 2 (test, testroutine)" end
		return true, "versteckt / für Entwickler " .. devAll
	end)

	-- 3.0.41 (Entscheid des Nutzers 19.11. 09:06): Entwickler-Befehle und -Knöpfe nur im Entwicklermodus; Gegenprobe: dev an -> alle
	t:Check("T196", "J", "DEV-SICHT: Entwickler-Befehle/-Knopf nur im Entwicklermodus (Gegenprobe dev an)", function()
		local f = MainFrame()
		if not (f and f.testButton and f.testVisible and RM.Test) then return false, "Hauptfenster/Testknopf fehlt", "vorhanden" end
		local GD = _G.GoldSentinelDev
		if not GD then return false, "GoldSentinelDev fehlt", "vorhanden" end
		local u, res = {}, {}
		return Guard(function()
			Swap(u, RM.Test, "active", false)                  -- ohne laufenden Testmodus (der Knopf bleibt sonst zum Beenden)
			for _, dev in ipairs({ false, true }) do
				Swap(u, GD, "IsDev", function() return dev end)
				local H, restore = HintWith(dev, true)
				local names = {}
				for _, it in ipairs(H:List("")) do if it.entry.dev then names[#names + 1] = it.entry[1] end end
				restore()
				table.sort(names)
				f.testVisible()
				res[dev] = { list = table.concat(names, ","), btn = f.testButton:IsShown() and true or false }
			end
			if res[false].list ~= "" then return false, "dev aus, Liste: " .. res[false].list, "keine Entwickler-Zeile" end
			if res[false].btn then return false, "dev aus: Test-Knopf sichtbar", "versteckt" end
			if res[true].list ~= "prüfliste,test,testroutine" then return false, "dev an, Liste: " .. res[true].list, "prüfliste,test,testroutine" end
			if not res[true].btn then return false, "dev an: Test-Knopf fehlt", "sichtbar" end
			return true, "dev aus: 0 Zeilen, Knopf weg · dev an: prüfliste, test, testroutine, Knopf da"
		end, function() Undo(u); f.testVisible() end)
	end)

	-- 3.0.41 (Befund 19.11. 09:10): Werbung – Platzhalter nur als "?" mit Tooltip, keine dauerhafte Zeile mehr
	t:Check("T197", "J", "Werbung: Platzhalter als \"?\" mit Tooltip, keine sichtbare Platzhalter-Zeile", function()
		local UI = RM.UI
		local p = UI.pages and UI.pages.ad
		if not (p and UI.BuildPage) then return false, "Seite Werbung fehlt", "vorhanden" end
		if p.frame and not p.built then UI.BuildPage(p) end
		local btn = UI.adPlaceholderHelp
		if not btn then return false, "kein ?-Knopf", "?-Knopf" end
		-- Gegenprobe: kein FontString der Seite zeigt die Liste der Platzhalter dauerhaft
		local visible = 0
		local function Scan(fr, depth)
			if depth > 6 or not fr then return end
			for _, r in ipairs({ fr.GetRegions and fr:GetRegions() or nil }) do
				if r and r.GetText and r.GetObjectType and r:GetObjectType() == "FontString" then
					local tx = r:GetText()
					if type(tx) == "string" and tx:find("{raid}", 1, true) and tx:find("{zeit}", 1, true) then visible = visible + 1 end
				end
			end
			for _, c in ipairs({ fr.GetChildren and fr:GetChildren() or nil }) do Scan(c, depth + 1) end
		end
		Scan(p.frame, 0)
		if visible > 0 then return false, visible .. " Zeile(n) mit Platzhaltern sichtbar", "0" end
		if type(btn:GetScript("OnEnter")) ~= "function" then return false, "kein Überfahren", "OnEnter" end
		local tip = type(btn.tooltip) == "string" and btn.tooltip or ""      -- genau der Text, den UI.Button beim Überfahren zeigt
		local all = {}
		for line in tip:gmatch("[^\n]+") do all[#all + 1] = line end
		local n = #all
		local joined = table.concat(all, "\n")
		for _, k in ipairs({ "{raid}", "{zeit}", "{frei}", "{softres}", "{link}", "{name}" }) do
			if not joined:find(k, 1, true) then return false, "Tooltip ohne " .. k .. " (" .. n .. " Zeilen)", "alle 6 Platzhalter" end
		end
		if n ~= 7 then return false, n .. " Zeilen", "7 (Titel + 6 Platzhalter)" end
		return true, "?-Knopf, Tooltip 7 Zeilen, 0 sichtbare Platzhalter-Zeilen"
	end)

	t:Check("T171", "J", "T-BL6 Beschreibungen in der Spielsprache ohne Platzhalter-Fehler", function()
		local bad
		for _, c in ipairs(RM.COMMANDS) do
			local txt = RM.L[c[3]]
			if type(txt) ~= "string" or txt == "" then bad = c[3] end
			local _, nKey = c[3]:gsub("%%", "")
			local _, nTxt = tostring(txt):gsub("%%", "")
			if nKey ~= nTxt then bad = "Platzhalter: " .. c[3] end
		end
		local enter = RM.L["Enter = %s"]
		local okFmt = pcall(string.format, enter, "/rm bar")
		if bad then return false, bad, "übersetzt, gleiche Platzhalter" end
		if not okFmt then return false, enter, "Enter = %s formatierbar" end
		return true, (RM.LOCALE or "?") .. ": alle " .. #RM.COMMANDS .. " Beschreibungen"
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
---------------------------------------------------------------------------
-- Bereich L (ab 3.0.24): umfassende Tests nach anweisung-tests-umfassend.txt (TU1–TU8)
-- TU1 Lagen x Funktionen (Tabelle), TU2 Abläufe, TU3 Standardwerte, TU4 Grundregeln mit 1000 Zufallsfällen (Startwert
-- 4711, in Portionen), TU5 echte Daten nur lesen (Kopie aus der Sandbox), TU6 Regressionen, TU7 Formen, TU8 Bericht.
---------------------------------------------------------------------------
local TU_SEED = 4711
local TU = { rows = {} }
local function TUAdd(area, ok, line)
	local r = TU.rows[area] or { ok = 0, fehler = 0, skip = 0, lines = {} }
	TU.rows[area] = r
	if ok == "skip" then r.skip = r.skip + 1 elseif ok then r.ok = r.ok + 1 else r.fehler = r.fehler + 1 end
	if ok ~= true then r.lines[#r.lines + 1] = line end
end

-- kleiner Zufall mit festem Startwert (gleich in jedem Client, unabhängig von math.random)
local function Rng(seed)
	local x = seed % 2147483647
	if x <= 0 then x = x + 2147483646 end
	return function(a, b)
		x = (x * 16807) % 2147483647
		if not a then return x / 2147483647 end
		return a + (x % (b - a + 1))
	end
end

local function SetDKP(name, pool, v)
	local p = RM.DKP.EnsurePlayer(name)
	p.d = p.d or {}
	p.d[pool] = v
end

local function PoolSum(data, pool)
	local sum = 0
	for _, p in pairs(data.players or {}) do sum = sum + ((p.d and p.d[pool]) or 0) end
	return sum
end

local function AreaL(t, G)
	local DKP, A = RM.DKP, RM.Auction
	TU.rows = {}

	-- TU1: Lagen x Funktionen. Erwartung je Zeile; Abweichung = FEHLER mit Zeilenname
	-- 3.0.33 (Ingame 19:38: 6,1 ms am Stück): jede Lage in einem eigenen Bild
	AsyncCheck(t, "T172", "L", "TU1 Lagen-Katalog: Gebote, DKP, Raid-Buchung", function()
		TestRaid()
		ClearAuction()
		local s = RM.db.data.settings
		local pool = DKP.ActivePool()
		local u = {}
		local fails = {}
		local function Row(name, want, fn)
			R.Breathe(R.PRE_MS)
			local ok, got = pcall(fn)
			got = ok and got or ("Lua-Fehler: " .. tostring(got))
			TUAdd("TU1", got == want, name .. ": " .. tostring(got) .. " (erwartet " .. tostring(want) .. ")")
			if got ~= want then fails[#fails + 1] = name .. "=" .. tostring(got) end
		end
		local function Fresh()
			ClearAuction()
			A.Start(LINK_STONE)
			return A.current ~= nil
		end
		Guard(function()
			Swap(u, s, "minBid", 10); Swap(u, s, "bidIncrement", 5); Swap(u, s, "allowNegative", false)
			Swap(u, s, "mainBeforeTwink", true); Swap(u, s, "onlyOnline", false)
			Row("DKP 0, Gebot 10", "abgelehnt", function()
				SetDKP("Krieger1", pool, 0); Fresh()
				return A.ReceiveBid("Krieger1", 10) and "angenommen" or "abgelehnt"
			end)
			Row("DKP negativ, Gebot 10", "abgelehnt", function()
				SetDKP("Krieger1", pool, -20); Fresh()
				return A.ReceiveBid("Krieger1", 10) and "angenommen" or "abgelehnt"
			end)
			Row("Gebot über Kontostand", "abgelehnt", function()
				SetDKP("Krieger1", pool, 40); Fresh()
				return A.ReceiveBid("Krieger1", 45) and "angenommen" or "abgelehnt"
			end)
			Row("Gebot über Kontostand, Minus erlaubt", "angenommen", function()
				s.allowNegative = true
				SetDKP("Krieger1", pool, 0); Fresh()
				local r = A.ReceiveBid("Krieger1", 10) and "angenommen" or "abgelehnt"
				s.allowNegative = false
				return r
			end)
			Row("Gebot unter Mindestgebot", "abgelehnt", function()
				SetDKP("Krieger1", pool, 100); Fresh()
				return A.ReceiveBid("Krieger1", 5) and "angenommen" or "abgelehnt"
			end)
			Row("gleiche Gebote: erstes gewinnt", "Krieger1 20", function()
				SetDKP("Krieger1", pool, 50); SetDKP("Krieger2", pool, 50); Fresh()
				A.ReceiveBid("Krieger1", 20)
				local second = A.ReceiveBid("Krieger2", 20)
				if second then return "zweites gleiches Gebot angenommen" end
				return tostring(A.current.highName) .. " " .. tostring(A.current.high)
			end)
			Row("nicht im Raid", "abgelehnt", function()
				Fresh()
				return A.ReceiveBid("Fremder Spieler", 50) and "angenommen" or "abgelehnt"
			end)
			Row("Boss-Kill während Gebotsrunde", "angenommen", function()
				SetDKP("Krieger3", pool, 0); Fresh()
				DKP.NewEntry("boss", "Test-Boss", { Krieger3 = 10 }, nil, nil, { pool = pool })
				return A.ReceiveBid("Krieger3", 10) and "angenommen" or "abgelehnt"
			end)
			Row("Forever: gleiche Vornamen getrennt", "10 / 20", function()
				local data = { players = {}, log = {}, firstKills = {} }
				DKP.ApplyEntryTo(data, { id = "tu1-a", k = "manual", pool = pool, d = { ["Testa Beispiel"] = 10 } }, false)
				DKP.ApplyEntryTo(data, { id = "tu1-b", k = "manual", pool = pool, d = { ["Testa Muster"] = 20 } }, false)
				return data.players["Testa Beispiel"].d[pool] .. " / " .. data.players["Testa Muster"].d[pool]
			end)
			Row("Raid: Spieler offline, nur Online-Wertung", "offline ausgenommen", function()
				local T = RM.Test
				local off = {}
				for i, m in ipairs(T.roster or {}) do
					if i <= 3 and m.online ~= false then off[#off + 1] = m; m.online = false end
				end
				local all = 0
				for _ in pairs(DKP.RaidRecipients()) do all = all + 1 end
				s.onlyOnline = true
				local online = 0
				for _ in pairs(DKP.RaidRecipients()) do online = online + 1 end
				s.onlyOnline = false
				for _, m in ipairs(off) do m.online = true end
				return (all - online == #off and #off > 0) and "offline ausgenommen" or (all .. "/" .. online)
			end)
			Row("Raid-Buchung: Summe = Anzahl x Betrag", "stimmt", function()
				local before = PoolSum(RM.db.data, pool)
				local n = 0
				for _ in pairs(DKP.RaidRecipients()) do n = n + 1 end
				DKP.AwardRaid(7, "manual", "TU1", nil, pool)
				return (PoolSum(RM.db.data, pool) - before == 7 * n) and "stimmt" or ((PoolSum(RM.db.data, pool) - before) .. " statt " .. 7 * n)
			end)
		end, function() ClearAuction(); for _, f in ipairs(u) do f() end end)
		if #fails > 0 then return false, table.concat(fails, "; "), "Tabelle" end
		return true, "11 Lagen wie erwartet"
	end)

	-- TU2: Abläufe wie ein Spieler (inkl. Sync-Reihenfolge)
	t:Check("T173", "L", "TU2 Abläufe: zwei Gebote zugleich, Vergabe, Sync doppelt/vertauscht", function()
		TestRaid()
		ClearAuction()
		local s = RM.db.data.settings
		local pool = DKP.ActivePool()
		local u = {}
		local res = Guard(function()
			Swap(u, s, "minBid", 10); Swap(u, s, "bidIncrement", 5); Swap(u, s, "allowNegative", false)
			SetDKP("Krieger1", pool, 100); SetDKP("Krieger2", pool, 100)
			local before = PoolSum(RM.db.data, pool)
			A.Start(LINK_STONE)
			local a = A.ReceiveBid("Krieger1", 30)
			local b = A.ReceiveBid("Krieger2", 30)          -- dieselbe Sekunde, gleicher Betrag
			A.FinishNow()
			if not A.AwaitingAward() then return "keine Vergabe offen" end
			A.Award()
			local diff = PoolSum(RM.db.data, pool) - before
			if not (a and not b) then return "Gebote " .. tostring(a) .. "/" .. tostring(b) end
			if diff ~= -30 or DKP.Get("Krieger1", pool) ~= 70 or DKP.Get("Krieger2", pool) ~= 100 then
				return "Buchung " .. diff
			end
			TUAdd("TU2", true, "Gebot -> Ende -> Vergabe, zwei Gebote zugleich")
			-- Sync: dieselbe Buchung zweimal, Reihenfolge vertauscht -> gleicher Stand
			local e1 = { id = "tu2-1", k = "boss", pool = pool, d = { X = 10, Y = 10 } }
			local e2 = { id = "tu2-2", k = "item", pool = pool, d = { X = -15 } }
			local e3 = { id = "tu2-3", k = "undo", pool = pool, r = "tu2-1", d = { X = -10, Y = -10 } }
			local d1 = { players = {}, log = {}, firstKills = {} }
			local d2 = { players = {}, log = {}, firstKills = {} }
			for _, e in ipairs({ e1, e2, e1, e3, e2 }) do DKP.ApplyEntryTo(d1, e, false) end
			for _, e in ipairs({ e3, e2, e1, e1 }) do DKP.ApplyEntryTo(d2, e, false) end
			local x1, x2 = d1.players.X.d[pool], d2.players.X.d[pool]
			if not (x1 == -15 and x2 == -15 and #d1.log == 3 and #d2.log == 3) then
				return "Sync " .. tostring(x1) .. "/" .. tostring(x2) .. " Log " .. #d1.log .. "/" .. #d2.log
			end
			TUAdd("TU2", true, "Sync: doppelt empfangen und vertauscht -> gleicher Stand")
			return "ok"
		end, function() ClearAuction(); for _, f in ipairs(u) do f() end end)
		TUAdd("TU2", "skip", "SKIP /reload mitten im Bieten, Einteilung von zwei Offizieren: im Client prüfen")
		if res ~= "ok" then TUAdd("TU2", false, tostring(res)); return false, res, "ok" end
		return true, "Vergabe genau einmal, Sync-Reihenfolge egal"
	end)

	-- TU3: Standardwerte – fehlende/leere Werte ergeben, was der Spieler meint
	t:Check("T174", "L", "TU3 Standardwerte und fehlende Einstellungen", function()
		local want = { dkpStart = 10, dkpEnd = 10, defaultBossDKP = 10, decayPct = 10, minBid = 10, bidIncrement = 5,
			auctionTime = 30, allowNegative = false, onlyOnline = false, standbyStartDKP = 10, mainBeforeTwink = true,
			antiSnipe = true, autoDecay = true }
		local bad = {}
		for k, v in pairs(want) do
			local got = RM.DEFAULT_SETTINGS[k]
			TUAdd("TU3", got == v, k .. " = " .. tostring(got))
			if got ~= v then bad[#bad + 1] = k end
		end
		-- Befehlsliste ab Werk an
		TUAdd("TU3", RM.db.config.cmdHint ~= false or RM.DEFAULT_CONFIG.cmdHint == nil, "Befehlsliste ab Werk an")
		-- fehlende Zahl-Einstellungen (z. B. aus einer älteren Version per Sync): Versteigerung startet trotzdem
		TestRaid()
		ClearAuction()
		local s = RM.db.data.settings
		local u = {}
		local res = Guard(function()
			Swap(u, s, "minBid", nil); Swap(u, s, "bidIncrement", nil); Swap(u, s, "auctionTime", "")
			local ok = pcall(A.Start, LINK_STONE)
			if not (ok and A.current and A.current.min == 10 and A.current.inc == 5) then
				return "Start ohne Werte: " .. tostring(ok) .. " " .. tostring(A.current and A.current.min)
			end
			if RM.SettingNum("dkpStart") ~= (tonumber(s.dkpStart) or 10) then return "dkpStart" end
			return "ok"
		end, function() ClearAuction(); for _, f in ipairs(u) do f() end end)
		TUAdd("TU3", res == "ok", "fehlende Einstellungen -> Standard (Versteigerung startet): " .. tostring(res))
		if #bad > 0 then return false, table.concat(bad, ", "), "Standardwerte" end
		if res ~= "ok" then return false, res, "Standard" end
		return true, "13 Standardwerte, fehlende Werte -> Standard"
	end)

	-- TU4: Grundregeln mit 1000 Zufallsfällen, in Portionen (je Bild höchstens 8 ms)
	AsyncCheck(t, "T175", "L", "TU4 Grundregeln: 1000 Zufallsfälle", function()
		local rnd = Rng(TU_SEED)
		local pool = "mc"
		local names = { "A1", "A2", "A3", "B1", "B2", "Testa Beispiel", "Testa Muster" }
		local data = { players = {}, log = {}, firstKills = {} }
		local applied, booked = {}, 0
		local viol = {}
		local n = 0
		for case = 1, 1000 do
			local kind = rnd(1, 4)
			local e
			if kind <= 2 or #applied == 0 then
				local d = {}
				for _, nm in ipairs(names) do if rnd() < 0.5 then d[nm] = rnd(-30, 40) end end
				if not next(d) then d[names[rnd(1, #names)]] = rnd(1, 20) end
				e = { id = "tu4-" .. case, k = (kind == 1) and "boss" or "manual", pool = pool, d = d }
			elseif kind == 3 then
				e = applied[rnd(1, #applied)]                      -- dieselbe Buchung nochmals (Sync doppelt)
			else
				local target = applied[rnd(1, #applied)]
				local d = {}
				for nm, v in pairs(target.d) do d[nm] = -v end
				e = { id = "tu4-u" .. case, k = "undo", pool = pool, r = target.id, d = d }
			end
			local before = PoolSum(data, pool)
			local isNew = DKP.ApplyEntryTo(data, e, false)
			local delta = 0
			if isNew then
				for _, v in pairs(e.d) do delta = delta + v end
				applied[#applied + 1] = e
				booked = booked + delta
			end
			local after = PoolSum(data, pool)
			-- G1 Summe nachher = vorher + Buchungen (doppelt empfangene zählen nicht)
			if after ~= before + delta then
				viol[#viol + 1] = string.format("Fall %d (Startwert %d): Summe %d -> %d, Buchung %d", case, TU_SEED, before, after, delta)
			end
			-- G2 jede Buchungs-ID genau einmal im Log – 3.0.31 (NP-RM30-1): ganzer Durchgang alle 50 Fälle und beim letzten
			-- (vorher bei jedem Fall: 1000 Fälle x bis 1000 Einträge, viel Abfall für die Speicherbereinigung)
			if #viol < 5 and (case % 50 == 0 or case == 1000) then
				local seen = {}
				for i, x in ipairs(data.log) do
					if seen[x.id] then viol[#viol + 1] = string.format("Fall %d: Buchung %s doppelt im Log", case, x.id) end
					seen[x.id] = true
					if i % 250 == 0 then R.Breathe(R.PRE_MS) end
				end
			end
			n = n + 1
			R.Breathe(R.PRE_MS)                                    -- TR-ALLE: Bild abgeben, bevor 5 ms voll sind
			if #viol >= 5 then break end
		end
		if PoolSum(data, pool) ~= booked then viol[#viol + 1] = "Endsumme " .. PoolSum(data, pool) .. " statt " .. booked end
		-- G3 nie zwei Gewinner: zufällige Gebotsrunden über die echte Gebotsprüfung
		TestRaid()
		ClearAuction()
		local s = RM.db.data.settings
		local u = {}
		local roster = { "Krieger1", "Krieger2", "Krieger3", "Tank1" }
		local auctions = 0
		Guard(function()
			Swap(u, s, "minBid", 10); Swap(u, s, "bidIncrement", 5); Swap(u, s, "allowNegative", false)
			Swap(u, s, "mainBeforeTwink", false)
			local apool = DKP.ActivePool()
			for round = 1, 40 do
				for _, nm in ipairs(roster) do SetDKP(nm, apool, rnd(0, 80)) end
				ClearAuction()
				R.Breathe(R.PRE_MS)                                  -- TR-ALLE: zwischen zwei Runden (keine laufende Versteigerung)
				A.Start(LINK_STONE)
				local c = A.current
				if not c then viol[#viol + 1] = "Runde " .. round .. ": startet nicht" break end
				local best, bestName = 0, nil
				for _ = 1, 12 do
					-- 3.0.31 (NP-RM30-1): jedes Gebot in einem eigenen Bild, wenn das Bild schon belegt ist (die Versteigerung
					-- läuft 3 s im Testmodus – 13 Bilder reichen auch bei wenigen Bildern pro Sekunde)
					R.Breathe(R.PRE_MS)
					local nm = roster[rnd(1, #roster)]
					local amt = rnd(0, 90)
					local okBid = A.ReceiveBid(nm, amt)
					local need = bestName and (best + 5) or 10
					local should = amt >= need and amt <= DKP.Get(nm, apool)
					if (okBid and true or false) ~= should then
						viol[#viol + 1] = string.format("Runde %d (Startwert %d): %s %d bei Bedarf %d, Konto %d -> %s",
							round, TU_SEED, nm, amt, need, DKP.Get(nm, apool), tostring(okBid))
					end
					if okBid then best, bestName = amt, nm end
				end
				if c.highName ~= bestName or (bestName and c.high ~= best) then
					viol[#viol + 1] = string.format("Runde %d: Gewinner %s %s statt %s %s", round, tostring(c.highName),
						tostring(c.high), tostring(bestName), tostring(best))
				end
				auctions = auctions + 1
				if #viol >= 5 then break end
			end
		end, function() ClearAuction(); for _, f in ipairs(u) do f() end end)
		TUAdd("TU4", #viol == 0, string.format("%d DKP-Fälle + %d Gebotsrunden, Startwert %d: %d Verletzungen", n, auctions,
			TU_SEED, #viol))
		for _, v in ipairs(viol) do TUAdd("TU4", false, v) end
		if #viol > 0 then return false, viol[1], "keine Verletzung" end
		return true, string.format("%d Fälle + %d Gebotsrunden, Startwert %d", n, auctions, TU_SEED)
	end)

	-- TU5: echte Daten (KOPIE aus der Sandbox) nur lesen; Verletzungen ins Diagnose-Protokoll, ohne Namen
	-- 3.0.31 (NP-RM30-1): die Kopie der echten Daten kann gross sein – in Portionen lesen (die Kopie ändert sich nicht)
	AsyncCheck(t, "T176", "L", "TU5 echte Daten (Kopie) erfüllen die Grundregeln", function()
		local real = R.snap and R.snap.db and R.snap.db.data
		if type(real) ~= "table" then
			TUAdd("TU5", "skip", "SKIP keine gesicherte Kopie der echten Daten")
			return true, "keine echten Daten"
		end
		local viol = {}
		local ids = {}
		for i, e in ipairs(real.log or {}) do
			if i % 200 == 0 then R.Breathe(R.PRE_MS) end
			if type(e) ~= "table" or not e.id then viol[#viol + 1] = "Log-Eintrag " .. i .. " ohne ID"
			elseif ids[e.id] then viol[#viol + 1] = "Buchung doppelt im Log (Nr. " .. i .. ")"
			else ids[e.id] = true end
			if type(e) == "table" then
				for _, v in pairs(e.d or {}) do
					if type(v) ~= "number" or v ~= v then viol[#viol + 1] = "Buchung Nr. " .. i .. " mit ungültigem Betrag" end
				end
				if e.k == "undo" and e.r and ids[e.r] == nil then
					-- Ziel kann vor der Log-Grenze liegen: nur zählen, nicht als Verletzung
				end
			end
		end
		local nPlayers = 0
		for _, p in pairs(real.players or {}) do
			nPlayers = nPlayers + 1
			if nPlayers % 200 == 0 then R.Breathe(R.PRE_MS) end
			for _, v in pairs((type(p) == "table" and p.d) or {}) do
				if type(v) ~= "number" or v ~= v or v == math.huge or v == -math.huge then
					viol[#viol + 1] = "Spieler Nr. " .. nPlayers .. ": ungültiger DKP-Stand"
				end
			end
		end
		for _, v in ipairs(viol) do
			if RM.Diag and RM.Diag.Record then RM.Diag.Record("GRUNDREGEL VERLETZT (DKP): " .. v) end
		end
		TUAdd("TU5", #viol == 0, string.format("echte Daten: %d Buchungen, %d Spieler, %d Verletzungen", #(real.log or {}),
			nPlayers, #viol))
		if #viol > 0 then return false, viol[1], "keine Verletzung" end
		return true, string.format("%d Buchungen, %d Spieler geprüft", #(real.log or {}), nPlayers)
	end)

	-- TU6: Regressionen – jeder Befund seit dem 1.11. hat eine bleibende Prüfung, die in diesem Lauf vorkam
	t:Check("T177", "L", "TU6 Regressionen vorhanden", function()
		local REG = { { "T-142 !dkp Vor-/Nachname", "T142" }, { "T-122 Fehler genau einmal gezählt", "T122" },
			{ "T-43 Beute vorgeladen", "T43" }, { "SetRaidTarget FORBIDDEN (Forever)", "T133" },
			{ "sichere Symbol-Knöpfe", "T161" }, { "GoldSentinelTest 2", "T162" }, { "Zustimmung Sammler", "T163" },
			{ "GoldSentinelSync mitgebracht", "T164" }, { "Prüfblock Uploader", "T165" },
			{ "BL1 Befehlsliste vollständig", "T166" }, { "BL2 Filter", "T167" }, { "BL3 Klick/Enter", "T168" },
			{ "BL4 Chatfeld nie beschrieben", "T169" }, { "BL5 Entwickler", "T170" }, { "BL6 Sprachen", "T171" },
			{ "Oberfläche: Tooltips", "T155" }, { "Oberfläche: Fenster", "T156" }, { "Oberfläche: Bildschirm", "T157" },
			{ "Oberfläche: Text passt", "T158" }, { "Oberfläche: Werte", "T159" }, { "Oberfläche: Fehler-Schleifen", "T160" },
			{ "TU3 fehlende Einstellungen", "T174" }, { "MN4 mit/ohne GoldSentinelMarkt", "T180" },
			{ "MN1-K FeedStart/Feed", "T180" }, { "MN-T Zähler unverändert", "T181" },
			{ "MN4 Schalter aus", "T181" }, { "MN4 ohne AH-API", "T182" }, { "MN3 Testbericht-Zeile", "T183" },
			{ "Prüfliste im Spiel", "T185" }, { "RM-DIAG-1 Fehlerflut", "T186" },
			{ "RM-DIAG-1 Fehlerquellen", "T187" }, { "RM-API-RAIDS", "T188" },
			{ "TR-ALLE Sicherung", "T189" }, { "Tooltip-Platzierung (Ingame T155)", "T190" }, { "HUD-Ausnahme (Ingame T156)", "T191" }, { "Beschriftungen passen (Ingame T158)", "T192" }, { "Testdaten nie für andere Addons", "T193" },
			{ "OPT-ALLE Optionen-Fenster", "T194" }, { "Spieler ohne Testbefehle", "T195" },
			{ "DEV-SICHT Entwickler nur im Entwicklermodus", "T196" }, { "Werbung Platzhalter als ?", "T197" },
			{ "Livedaten-Wächter Gegenprobe", "T198" }, { "Lesbarkeit L1/L8", "T199" }, { "Lesbarkeit Gegenprobe", "T200" }, { "RM-I2 Klassenfarben lesbar", "T201" }, { "RM-I2 Item-Qualitätsfarben lesbar", "T202" }, { "RM-UMG1 Umgebung erkennen (Gegenprobe)", "T203" }, { "L4 Summen gehen auf", "T204" }, { "L3 gleiche DKP-Zahl überall", "T205" }, { "RM-TAINT1 Fenster weichen aus", "T206" }, { "RM-K2 Ausweichen im Ablauf", "T208" }, { "RM-I1 Speicher je Addon", "T116" },
			{ "RM-TF-1 kein Fehlerfenster", "T120" }, { "T-BL4 echtes Eingabefeld", "T169" } }
		local only = R.only
		local have, missing = 0, {}
		for _, r in ipairs(REG) do
			if R.seen[r[2]] or R.seen[r[2]:lower()] then have = have + 1
			elseif r[2] == "T174" and R.seen.T174 == nil then missing[#missing + 1] = r[1]
			else missing[#missing + 1] = r[1] .. " (" .. r[2] .. ")" end
		end
		local text = string.format("Regressionen: %d von %d vorhanden", have, #REG)
		if only and only ~= "L" then return true, text end
		if only == "L" then
			TUAdd("TU6", "skip", "SKIP nur Bereich L gelaufen – Regressionen nur im ganzen Lauf zählbar")
			return true, text .. " (nur Bereich L)"
		end
		TUAdd("TU6", #missing == 0, text)
		if #missing > 0 then return false, text .. ": fehlt " .. table.concat(missing, ", "), "alle" end
		return true, text
	end)

	-- TU7: Formen des Spiels – dieselben Prüfungen laufen in jedem Client; hier: Client, Sprache, geschützte Werte
	t:Check("T178", "L", "TU7 Formen des Spiels", function()
		local G2 = _G.GoldSentinelGame
		local flavor = (G2 and G2.flavor) or "?"
		local secrets = (RM.Caps and RM.Caps.secrets) and "ja" or "nein"
		TUAdd("TU7", true, string.format("Client %s, Sprache %s, geschützte Werte %s: TU1–TU4 gelaufen", tostring(flavor),
			tostring(RM.LOCALE), secrets))
		TUAdd("TU7", "skip", "SKIP Fenster bei Skalierung ≠ 100 %: Bereich K im Client")
		return true, tostring(flavor) .. " / " .. tostring(RM.LOCALE)
	end)

	-- TU8: Bericht je Bereich
	t:Check("T179", "L", "TU8 Testbericht je Bereich", function()
		local lines, empty = {}, {}
		for _, a in ipairs({ "TU1", "TU2", "TU3", "TU4", "TU5", "TU6", "TU7" }) do
			local r = TU.rows[a] or { ok = 0, fehler = 0, skip = 0, lines = {} }
			lines[#lines + 1] = string.format("%s OK %d · FEHLER %d · SKIP %d", a, r.ok, r.fehler, r.skip)
			if r.ok + r.fehler == 0 and a ~= "TU6" then empty[#empty + 1] = a end
		end
		R.tuReport = lines
		for _, l in ipairs(lines) do RM.Print("Testroutine: " .. l) end
		if #empty > 0 then return false, "ohne Ergebnis: " .. table.concat(empty, ", "), "alle Bereiche" end
		return true, table.concat(lines, " | ")
	end)
end

local function AreaK(t)
	local U, UI = RM.UICheck, RM.UI
	local ui = {
		{ "T155", "Eigene Tooltips verdecken keine Knöpfe", "TooltipsCoverNothing" },
		{ "T156", "Kein Überlappen mit Blizzard- oder GoldSentinel-Fenstern", "WindowsOverlapNothing" },
		{ "T157", "Fenster und Tooltips ganz im Bildschirm", "InsideScreen" },
		{ "T158", "Beschriftungen von Knöpfen nicht abgeschnitten", "TextFits" },
		{ "T159", "Angezeigte Spielwerte plausibel", "ValuesPlausible", true },
		{ "T160", "Keine Fehlerschleife (gleiche Meldung > 10×)", "NoErrorLoops", true },
		{ "T199", "Lesbarkeit L1 Kontrast ab 4,5:1 und L8 Schrift nicht kleiner als GameFontNormalSmall", "Readable" },
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
				R.Breathe(R.PRE_MS)                        -- TR-ALLE: Seite aufbauen und je Prüfung ein eigenes Bild
				pcall(UI.ShowPage, id)
				for _, c in ipairs(ui) do if not c[4] then R.Breathe(R.PRE_MS); Collect(c, id) end end
			end
		end
	end
	for _, c in ipairs(ui) do if c[4] then R.Breathe(R.PRE_MS); Collect(c) end end
	-- RM-TAINT1 (3.0.48, Lua-Fehler im Spiel 25.11. 08:58 "execution tainted by 'RaidMaster'"): die Testroutine öffnet NIE ein
	-- Blizzard-Fenster selbst (bis 3.0.47 öffnete sie das Charakterfenster -> dessen Code lief "tainted" und verglich geschützte
	-- Werte). T156 misst nur gegen Fenster, die der Spieler schon offen hat; sonst "im Client prüfen" mit Anleitung.
	-- Seite und Fenster wie vorher
	if main then
		if wasPage then pcall(UI.ShowPage, wasPage) end
		if not wasShown then main:Hide() end
	end
	if GameTooltip and GameTooltip.Hide then GameTooltip:Hide() end
	for _, c in ipairs(ui) do
		if not c[4] and not available then
			t:Skip(c[1], "K", c[2], "nur im echten Client (Fenster, Rechtecke, Tooltip)")
		elseif c[1] == "T156" and tested.T156 == 0 and #found.T156 == 0 then
			t:Client("T156", "K", c[2], "kein Blizzard-Fenster offen – Charakterfenster (Taste C) öffnen, dann /rm testroutine k; " ..
				"die Routine öffnet selbst keine Blizzard-Fenster (RM-TAINT1)")
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

local RUNNERS = { A = AreaA, B = AreaB, C = AreaC, D = AreaD, E = AreaE, F = AreaF, G = AreaG, H = AreaH, I = AreaI, J = AreaJ, K = AreaK,
	L = AreaL }

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
	R.portionStart = debugprofilestop and debugprofilestop() or nil
	R.portions = (R.portions or 0) + 1
	local mem0 = collectgarbage("count")
	local res = pack(coroutine.resume(R.co, ...))
	if R.portionStart and debugprofilestop then
		local d = debugprofilestop() - R.portionStart
		-- RM-P1 (3.0.50, Ingametest 3.0.49: "K Daten sichern" 28 ms): Speicher vor/nach dem Bild. Sinkt er, obwohl die Routine nur
		-- Speicher belegt, hat die Speicherbereinigung von Lua in diesem Bild gearbeitet (ihr Schritt läuft in unserer Zeit mit).
		local memDelta = collectgarbage("count") - mem0
		if R.env then R.env.ownAcc = R.env.ownAcc + d end      -- RM-UMG1: eigene Arbeit in diesem Bild
		local at = tostring(R.current or "?")
		-- leistung.md Regel 8: Gesamtdauer je Schritt getrennt vom längsten Bild
		if R.stepTotal then
			local st = R.stepTotal[at] or { ms = 0, frames = 0 }
			st.ms, st.frames = st.ms + d, st.frames + 1
			R.stepTotal[at] = st
		end
		if R.IsSingle(at) then
			-- NP-RM30-1 (Entscheid Supervisor 17.11.): erster Aufbau von Fenster/Seiten wird einzeln gemessen und getrennt genannt
			if R.singlePortions then R.singlePortions[at] = math.max(R.singlePortions[at] or 0, d) end
		else
			if d > (R.maxPortion or 0) then R.maxPortion, R.maxPortionAt, R.maxPortionMem = d, at, memDelta end
			if d > R.PORTION_MS and R.bigPortions then R.bigPortions[at] = math.max(R.bigPortions[at] or 0, d) end
		end
	end
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
	if job.area then                                         -- TR-ALLE: Fortschritt (nur Bereiche zählen)
		R.areaNo = (R.areaNo or 0) + 1
		Say(string.format("%d von %d: %s …", R.areaNo, R.areaCount or #R.jobs, job.name))
	end
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
	local word = only and only:upper() or nil
	-- TR-ALLE (3.0.30): "/rm testroutine stop" bricht ab (alles wird wiederhergestellt), "alles" = ganze Routine
	if word == "STOP" or word == "ABBRECHEN" then
		if R.running then R.Abort("vom Nutzer abgebrochen") else Say("läuft nicht.") end
		return
	end
	if word == "ALLES" then only = nil end
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
	if only and not RUNNERS[only] then Say("Bereich " .. only .. " gibt es nicht (A … L oder alles).") return end

	HookActions()
	wipe(realCount)
	local G = RM.G
	local snap = Snapshot()
	R.snap = snap
	R.SetGuard(RaidMasterDB)            -- TR-ALLE: /reload mitten im Lauf -> beim nächsten Einloggen alles zurück
	R.syncBefore = SyncPrint()          -- 3.0.41: gemeinsames Adressbuch (GoldSentinelSync) vor dem Lauf
	R.only = only
	R.testDBnilBefore = snap.testDBnil
	R.profTable = RM.db.prof
	R.diagBefore = #RM.Diag.errors
	-- RM-DIAG-1 (3.0.30): Fehlerzähler je Quelle gehören dem Spiel, nicht der Routine (T122/T186 erzeugen Testfehler)
	R.diagSources = { src = Deep(RM.Diag.sources or {}), total = RM.Diag.sourcesTotal or 0, first = Deep(RM.Diag.firstSource) }
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
	R.noYield = 0
	R.pendingNow = {}
	R.finished = false
	R.unwatch = WatchLocale()
	R.t = GoldSentinelTest.Begin("RaidMaster", RM.VERSION, RaidMasterDB)
	local t = R.t
	t.Wait = function(_, sec) return Wait(sec) end          -- T:Wait (asynchrones Warten) für die Prüfungen
	-- 3.0.24 (TU6): welche Prüfungen in diesem Lauf vorkamen (für "Regressionen: n von m")
	R.seen = {}
	R.slow, R.maxPortion, R.portions, R.maxPortionAt, R.bigPortions, R.singlePortions, R.stepTotal = {}, 0, 0, nil, {}, {}, {}
	R.maxPortionMem = nil
	do
		local oCheck, oSkip, oClient = t.Check, t.Skip, t.Client
		t.Check = function(self, id, ...)
			R.seen[id] = "run"
			R.Breathe(R.PRE_MS)
			R.current = id
			local t0 = debugprofilestop and debugprofilestop()
			-- der Körper einer t:Check-Prüfung läuft unter pcall (GoldSentinelTest): dort darf kein Bild abgegeben werden
			R.noYield = (R.noYield or 0) + 1
			local r = pack(pcall(oCheck, self, id, ...))
			R.noYield = R.noYield - 1
			if not r[1] then error(r[2], 0) end
			r = pack(unpack(r, 2, r.n))
			if t0 then
				local d = debugprofilestop() - t0
				if d > R.PORTION_MS then R.slow[#R.slow + 1] = { id = id, ms = d } end
			end
			R.Breathe()
			return unpack(r, 1, r.n)
		end
		if oSkip then t.Skip = function(self, id, ...) R.seen[id] = "skip"; return oSkip(self, id, ...) end end
		if oClient then t.Client = function(self, id, ...) R.seen[id] = "client"; return oClient(self, id, ...) end end
	end
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
	-- RM-UMG1 a): Umgebung messen – 1 s Ruhe vorher, dann jedes Bild des Laufs (nur lesen)
	R.env = R.NewEnv()
	R.EnvStart(R.env, GetTime())
	R.envFrame = R.envFrame or CreateFrame("Frame")
	R.envFrame:SetScript("OnUpdate", function(_, elapsed)
		if R.env and R.running then R.EnvFrame(R.env, (tonumber(elapsed) or 0) * 1000, GetTime()) end
	end)
	R.envFrame:RegisterEvent("LOADING_SCREEN_ENABLED")
	R.envFrame:RegisterEvent("LOADING_SCREEN_DISABLED")
	R.envFrame:SetScript("OnEvent", function(_, ev) if R.env then R.env.loading = ev == "LOADING_SCREEN_ENABLED" end end)
	R.jobs[#R.jobs + 1] = { name = "Umgebung vorher", fn = function()
		Wait(1)
		R.env.phase = "Lauf"
	end }
	R.areaCount, R.areaNo = 0, 0
	if ok then
		-- NP-RM30-1 (Entscheid Supervisor 17.11.): Hauptfenster und alle Seiten einmal VOR den Prüfungen aufbauen, eine Seite je
		-- Bild, einzeln gemessen ("Aufbau") – T10/T12 messen danach nicht mehr den ersten Aufbau
		R.jobs[#R.jobs + 1] = { name = "Aufbau", fn = function()
			R.current = "Aufbau"
			local UI = RM.UI
			local main = UI.main
			local wasShown = main and main:IsShown()
			local wasPage = main and main.current
			coroutine.yield("wait", 0)
			R.current = "Aufbau Fenster"
			pcall(UI.Open)
			for _, id in ipairs(UI.pageOrder or {}) do
				if UI.CanSeePage(id) and not RM.InCombat() then
					coroutine.yield("wait", 0)
					R.current = "Aufbau " .. id
					pcall(UI.ShowPage, id)
				end
			end
			-- 3.0.38 (OPT-ALLE i): jeder Bereich des Optionen-Fensters in einem eigenen Bild, einzeln gemessen
			if RM.Opt and UI.pages.settings and UI.pages.settings.built then
				for _, a in ipairs(RM.Opt.AREAS) do
					if RM.Opt.AreaVisible(a) and not RM.Opt.built[a.id] and not RM.InCombat() then
						coroutine.yield("wait", 0)
						R.current = "Aufbau Optionen " .. a.id
						pcall(UI.OpenOptions, a.id)
					end
				end
			end
			coroutine.yield("wait", 0)
			R.current = "Aufbau"
			main = UI.main
			if main then
				if wasPage then pcall(UI.ShowPage, wasPage) end
				if not wasShown then main:Hide() end
			end
		end }
		for _, a in ipairs(AREA_ORDER) do
			if not only or only == a then R.areaCount = R.areaCount + 1 end
		end
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
		if R.env then R.env.phase = "nachher" end            -- RM-UMG1: Bilder nach dem letzten Bereich
		Wait(1)
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
-- Prüfliste (3.0.28): nach einem ganzen Lauf ohne Abbruch Punkt TR (0 FEHLER) und MNT (Zähler "aus" = 0) setzen
---------------------------------------------------------------------------
-- TR-ALLE Nachtrag D (3.0.31, Supervisor 17.11. 14:00): der Lauf wartet NIE auf den Nutzer. Schritte, die ein Fenster
-- brauchen, werden geprüft, wenn das Fenster gerade offen ist; sonst vorgemerkt ("wartet auf Fenster", kein FEHLER) und von
-- selbst nachgeholt, wenn der Spieler das Fenster beim normalen Spielen öffnet – nur im Entwicklermodus, höchstens 7 Tage
-- nach dem Lauf, nie im Kampf und nie während einer Testroutine. Die Prüfungen lesen nur, was RaidMaster beim Öffnen
-- ohnehin speichert (keine Sandbox nötig, nichts wird verändert).
---------------------------------------------------------------------------
R.PENDING_DAYS = 7
local function Visible(name) local f = _G[name] return type(f) == "table" and f.IsShown and f:IsShown() and true or false end
local function BankFresh(since, src)
	local b = RM.db and RM.db.bank
	if not (b and b.c == RM.Me() and (b.t or 0) >= since) then return false, "nach dem Öffnen nicht gelesen", "Bestand neu gelesen" end
	if src and b.src ~= src then return false, "zuletzt gelesen: " .. tostring(b.src), src end
	local n = 0
	for _ in pairs(b.i or {}) do n = n + 1 end
	return true, n
end
R.WINDOW_STEPS = {
	T35b = { area = "B", name = "Berufe: Fenster wird eingelesen", what = "Berufe",
		later = "passiert von selbst, wenn du das nächste Mal ein Berufsfenster öffnest",
		events = { "TRADE_SKILL_SHOW", "CRAFT_SHOW" }, delay = 2,
		isOpen = function() return Visible("TradeSkillFrame") or Visible("ProfessionsFrame") or Visible("CraftFrame") end,
		check = function(since)
			local me = RM.db and RM.db.prof and RM.db.prof[RM.Me()]
			if not (me and (me.t or 0) >= since) then return false, "nach dem Öffnen nicht eingelesen", "Berufe-Daten neu" end
			local best = 0
			for _, p in pairs(me.p or {}) do if type(p) == "table" and type(p.n) == "table" then best = math.max(best, #p.n) end end
			if best < 1 then return false, "0 Rezepte", ">= 1 Rezept" end
			return true, best .. " Rezepte eingelesen"
		end },
	T36b = { area = "B", name = "Bank-Charakter: Bank wird gelesen", what = "Bank",
		later = "passiert von selbst beim nächsten Bankbesuch",
		need = function() return RM.Bank and RM.Bank.IsBankChar() end, needWhy = "kein Bank-Charakter (Einstellungen)",
		events = { "BANKFRAME_OPENED" }, delay = 2,
		isOpen = function() return RM.Bank and RM.Bank.bankOpen end,
		check = function(since)
			local ok, n, want = BankFresh(since)
			if not ok then return false, n, want end
			if n < 1 then return false, "0 Einträge", "> 0 Einträge" end
			return true, n .. " Einträge"
		end },
	T36c = { area = "B", name = "Bank-Charakter: Post wird gelesen", what = "Post",
		later = "passiert von selbst, wenn du das nächste Mal den Briefkasten öffnest",
		need = function() return RM.Bank and RM.Bank.IsBankChar() end, needWhy = "kein Bank-Charakter (Einstellungen)",
		events = { "MAIL_SHOW" }, delay = 3,
		isOpen = function() return RM.Bank and RM.Bank.mailOpen end,
		check = function(since)
			local ok, n, want = BankFresh(since, RM.L["Post"])
			if not ok then return false, n, want end
			return true, "Post gelesen (" .. n .. " Einträge im Bestand)"
		end },
}
R.WINDOW_ORDER = { "T35b", "T36b", "T36c" }
R.windowSeen, R.pendingNow = {}, {}

-- im Lauf: offen -> sofort prüfen; sonst vormerken
function R.WindowStep(t, id)
	local st = R.WINDOW_STEPS[id]
	if st.need and not st.need() then t:Skip(id, st.area, st.name, st.needWhy) return end
	if st.isOpen() then
		t:Check(id, st.area, st.name, function() return st.check(R.windowSeen[id] or 0) end)
		return
	end
	R.pendingNow[id] = st
	t:Skip(id, st.area, st.name, "wartet auf Fenster: " .. st.what .. " – " .. st.later)
end

-- am Ende des Laufs: Vorgemerktes speichern (nur Entwickler); ein neuer Lauf ersetzt einen alten Stand
function R.SavePending(t)
	if not (RaidMasterDB and RM.IsDev and RM.IsDev()) then return end
	local items, n = {}, 0
	for id in pairs(R.pendingNow or {}) do items[id] = true; n = n + 1 end
	if n == 0 then RaidMasterDB.routinePending = nil return end
	RaidMasterDB.routinePending = { t = time(), items = items, clean = ((t and t.counts and t.counts.fehler) or 0) == 0 }
end

function R.PendingExpired(p) return type(p) ~= "table" or (time() - (tonumber(p.t) or 0)) > R.PENDING_DAYS * 86400 end

-- Fenster geöffnet (normales Spielen)
function R.OnWindow(id)
	R.windowSeen[id] = RM.Now()
	local p = RaidMasterDB and RaidMasterDB.routinePending
	if not (p and type(p.items) == "table" and p.items[id]) then return end
	if R.PendingExpired(p) then RaidMasterDB.routinePending = nil return end       -- keine Sperre ohne Zeitlimit
	if R.running or not (RM.IsDev and RM.IsDev()) then return end
	local since = RM.Now()
	C_Timer.After(R.WINDOW_STEPS[id].delay, function() pcall(R.CatchUp, id, since) end)
end

function R.CatchUp(id, since)
	local p = RaidMasterDB and RaidMasterDB.routinePending
	if not (p and type(p.items) == "table" and p.items[id]) or R.running then return end
	if (InCombatLockdown and InCombatLockdown()) or RM.InCombat() then return end      -- bleibt vorgemerkt
	local st = R.WINDOW_STEPS[id]
	R.catchingUp = true                                          -- RaidMasterAPI.TestRunning() (3.0.34)
	local T = GoldSentinelTest.Begin("RaidMaster", RM.VERSION, RaidMasterDB)
	local passed = false
	T:Check(id, st.area, st.name .. " (nachgeholt)", function()
		local ok, a, b = st.check(since)
		passed = ok and true or false
		return ok, a, b
	end)
	R.catchingUp = false
	T:Finish({ bereich = "nachgeholt", nachgeholt = id, lauf = date and date("%d.%m.%Y %H:%M", p.t) or tostring(p.t) })
	p.items[id] = nil
	if not passed then p.failed = true end
	Say(string.format("%s-Prüfung nachgeholt – %s", st.what, passed and "bestanden" or "FEHLER"))
	if not next(p.items) then
		RaidMasterDB.routinePending = nil
		if p.clean and not p.failed then
			if RM.PLHit then RM.PLHit("TR", "Lauf 0 FEHLER, nachgeholte Fenster-Schritte bestanden") end
		elseif p.failed and RM.PLFail then
			RM.PLFail("TR", "nachgeholter Fenster-Schritt FEHLER")
		end
	end
end

for _, id in ipairs(R.WINDOW_ORDER) do
	for _, ev in ipairs(R.WINDOW_STEPS[id].events) do RM.On(ev, function() R.OnWindow(id) end) end
end
RM.On("PLAYER_LOGIN", function()
	local p = RaidMasterDB and RaidMasterDB.routinePending
	if p and R.PendingExpired(p) then RaidMasterDB.routinePending = nil end
end)

function R.NotePruefliste(t, only)
	if only or not (RM.PLHit and t and t.results) then return end
	local bad = {}
	for _, e in ipairs(t.results) do if e.status == "FEHLER" then bad[#bad + 1] = e.id end end
	local pending = RaidMasterDB and RaidMasterDB.routinePending
	if #bad == 0 and pending and pending.items and next(pending.items) then
		-- TR-ALLE D2: erst abhaken, wenn auch die nachgeholten Fenster-Schritte bestanden sind (R.CatchUp)
	elseif #bad == 0 then
		RM.PLHit("TR", #t.results .. " Prüfungen, 0 FEHLER")
	else
		RM.PLFail("TR", #bad .. " FEHLER: " .. table.concat(bad, ", "):sub(1, 120))
	end
	local g = _G.GoldSentinelMarkt
	local s = g and g.Stats and g.Stats()
	local aus = s and type(s.dropped) == "table" and tonumber(s.dropped.aus) or 0
	if aus == 0 then RM.PLHit("MNT", "verworfen aus 0") else RM.PLFail("MNT", "verworfen aus " .. aus) end
end

-- TR-ALLE (3.0.30): sauber nach /reload. Die Bereiche ändern einige echte Tabellen kurz (EXTRA_KEYS, KeepDB stellt sie am
-- Ende des Bereichs zurück; der Testmodus sichert seine eigenen in RaidMasterTestDB). Ein /reload mitten in einem Bereich
-- liesse diese Änderungen stehen. Darum beim Start eine Sicherung in RaidMasterDB.routineGuard, beim Ende gelöscht; ist sie
-- beim Einloggen noch da, wird alles daraus zurückgeschrieben.
function R.SetGuard(db)
	if type(db) ~= "table" then return end
	local g = { t = time(), version = RM.VERSION, keys = {}, had = {} }
	for _, k in ipairs(EXTRA_KEYS) do
		g.had[k] = db[k] ~= nil
		if db[k] ~= nil then g.keys[k] = Deep(db[k]) end
	end
	g.opts = Deep(RaidMasterTestOptions)
	db.routineGuard = g
end

function R.ClearGuard(db)
	if type(db) == "table" then db.routineGuard = nil end
end

function R.RestoreGuard(db)
	local g = type(db) == "table" and db.routineGuard
	if type(g) ~= "table" then return false end
	for _, k in ipairs(EXTRA_KEYS) do
		if g.had and g.had[k] then
			local v = g.keys and g.keys[k]
			if type(v) == "table" and type(db[k]) == "table" then Replace(db[k], v) else db[k] = Deep(v) end
		else
			db[k] = nil
		end
	end
	if g.opts ~= nil and db == RaidMasterDB then RaidMasterTestOptions = Deep(g.opts) end
	db.routineGuard = nil
	return true
end

RM.On("PLAYER_LOGIN", function()
	if R.running then return end
	if RaidMasterDB and RaidMasterDB.routineGuard and R.RestoreGuard(RaidMasterDB) then
		Say("war beim letzten Mal unterbrochen (/reload oder Ausloggen) – deine Daten sind wiederhergestellt.")
	end
end)

-- TR-ALLE (3.0.30): EINE Zusammenfassung "x von y bestanden, z nicht prüfbar – Grund" und die Portionen
function R.Summary(t)
	local c = (t and t.counts) or {}
	local ok, bad = c.ok or 0, c.fehler or 0
	local skip, hand = c.uebersprungen or 0, c.client or 0
	local why = {}
	local inList = {}
	for _, p in ipairs(RM.PRUEFPUNKTE or {}) do inList[string.upper(tostring(p.id))] = true end
	for _, e in ipairs((t and t.results) or {}) do
		if e.status == "SKIP" then
			local g = tostring(e.grund or "?"):gsub("%s*%(.*", ""):sub(1, 50)
			if g:find("^wartet auf Fenster") then g = "wartet auf Fenster (passiert von selbst)" end
			why[g] = (why[g] or 0) + 1
		elseif e.status == "CLIENT" then
			-- ehrlich: "Prüfliste" nur, wenn der Punkt wirklich in /rm prüfliste steht; sonst offene Handprüfung im echten Client
			local g = inList[string.upper(tostring(e.id or ""))] and "nur von Hand (/rm prüfliste)" or "nur im echten Client (nicht in der Prüfliste)"
			why[g] = (why[g] or 0) + 1
		end
	end
	local list = {}
	for g, n in pairs(why) do list[#list + 1] = { g = g, n = n } end
	table.sort(list, function(a, b) if a.n ~= b.n then return a.n > b.n end return a.g < b.g end)
	local parts = {}
	for i = 1, math.min(3, #list) do parts[i] = list[i].n .. "x " .. list[i].g end
	local summary = string.format("%d von %d bestanden", ok, ok + bad)
	if skip + hand > 0 then
		summary = summary .. string.format(", %d nicht prüfbar – %s", skip + hand, table.concat(parts, "; "))
	end
	-- TR-ALLE D3: was noch fehlt, in Alltagssprache
	local open = {}
	for _, id in ipairs(R.WINDOW_ORDER) do
		local st = R.pendingNow and R.pendingNow[id]
		if st then open[#open + 1] = st.what .. " – " .. st.later end
	end
	if #open > 0 then summary = summary .. ". Noch offen: " .. table.concat(open, "; ") end
	table.sort(R.slow or {}, function(a, b) return a.ms > b.ms end)
	local slow = {}
	for i = 1, math.min(6, #(R.slow or {})) do slow[i] = string.format("%s %.0f ms", R.slow[i].id, R.slow[i].ms) end
	local big = {}
	for at, ms in pairs(R.bigPortions or {}) do big[#big + 1] = { at = at, ms = ms } end
	table.sort(big, function(a, b) return a.ms > b.ms end)
	local bigParts = {}
	for i = 1, math.min(8, #big) do bigParts[i] = string.format("%s %.0f ms", big[i].at, big[i].ms) end
	-- NP-RM30-1: "längste Portion x ms (Prüfung), über 5 ms: n (ohne einzeln gemessene)", einzeln gemessene getrennt
	local single = {}
	local sl = {}
	for at, ms in pairs(R.singlePortions or {}) do sl[#sl + 1] = { at = at, ms = ms } end
	table.sort(sl, function(a, b) return a.ms > b.ms end)
	for i = 1, math.min(6, #sl) do single[#single + 1] = string.format("%s %.1f ms", sl[i].at, sl[i].ms) end
	-- leistung.md Regel 8: Schritte, die zusammen über 16 ms brauchen, mit Gesamtdauer und Zahl der Bilder (nicht mit dem längsten Bild
	-- verwechseln: ein Schritt kann 300 ms dauern und trotzdem nie über 5 ms je Bild liegen)
	local steps = {}
	for at, st in pairs(R.stepTotal or {}) do if st.ms > 16 then steps[#steps + 1] = { at = at, ms = st.ms, frames = st.frames } end end
	table.sort(steps, function(a, b) return a.ms > b.ms end)
	local stepParts = {}
	for i = 1, math.min(8, #steps) do stepParts[i] = string.format("%s %.0f ms in %d Bildern", steps[i].at, steps[i].ms, steps[i].frames) end
	-- RM-P1 (3.0.50): beim längsten Bild die Speicheränderung – negativ = die Speicherbereinigung lief in diesem Bild mit
	local memNote = R.maxPortionMem and string.format(" · Speicher %+.0f KB%s", R.maxPortionMem,
		R.maxPortionMem < 0 and " = Speicherbereinigung im Bild" or "") or ""
	local portionLine = string.format("PORTIONEN: %d Bilder, längstes Bild %.1f ms (%s%s), über %d ms: %d (ohne einzeln gemessene)%s; einzeln gemessen: %s; Prüfungen länger als %d ms am Stück: %s; Schritte über 16 ms gesamt: %s",
		R.portions or 0, R.maxPortion or 0, R.maxPortionAt or "-", memNote, R.PORTION_MS, #big,
		#big > 0 and (" – " .. table.concat(bigParts, ", ")) or "",
		#single > 0 and table.concat(single, ", ") or "keine", R.PORTION_MS, #slow > 0 and table.concat(slow, ", ") or "keine",
		#stepParts > 0 and table.concat(stepParts, ", ") or "keine")
	return summary, portionLine
end

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
	-- RM-UMG1: Umgebung abschliessen (nur lesen); Speicher je Addon EINMAL, nach der letzten Messung, nur bei Bildern über 40 ms
	local envLine = "UMGEBUNG: nicht gemessen"
	if R.envFrame then R.envFrame:SetScript("OnUpdate", nil); R.envFrame:UnregisterAllEvents() end
	if R.env then
		local e = R.env
		if GetNetStats then e.ping1 = select(3, GetNetStats()) end
		e.fps1 = GetFramerate and GetFramerate() or nil
		local memTop
		if e.nLong > 0 and R.AddonMemory then
			local ok, mem, ms = pcall(R.AddonMemory)
			if ok and mem then
				local list = {}
				for name, kb in pairs(mem) do list[#list + 1] = { name, kb } end
				table.sort(list, function(x, y) return x[2] > y[2] end)
				local top = {}
				for i = 1, math.min(4, #list) do top[i] = string.format("%s %.1f MB", list[i][1], list[i][2] / 1024) end
				memTop = table.concat(top, ", ") .. string.format(" (Lesen %.0f ms, nicht in den Messungen)", ms or 0)
			end
		end
		local okL, line = pcall(R.EnvLine, e, memTop)
		envLine = okL and line or ("UMGEBUNG: " .. tostring(line))
	end
	R.envLine = envLine
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

		-- T184 (3.0.27): Platzhalter jeder geladenen Übersetzung in derselben Reihenfolge wie im deutschen Text. Lua 5.1
		-- kennt kein "%1$s" – vertauschte Platzhalter (zhCN bis 3.0.26: "%s … %d … %s") liessen string.format abbrechen
		-- (DKP-Vergabe fragte nicht mehr nach). Prozentzeichen mit Leerzeichen ("30 % …") sind Text, keine Platzhalter.
		if not only or only == "F" then
			if RM.LOCALE == "deDE" then
				t:Skip("T184", "F", "Platzhalter der Übersetzungen", "Grundsprache")
			else
				t:Check("T184", "F", "Platzhalter der Übersetzungen", function()
					local function specs(str)
						local out = {}
						for sp in str:gsub("%%%%", ""):gmatch("%%[-+#0]*%d*%.?%d*[sdifgxXcq]") do out[#out + 1] = sp end
						return table.concat(out, ",")
					end
					local bad, n = {}, 0
					for k, v in pairs(RM.L) do
						if type(k) == "string" and type(v) == "string" then
							n = n + 1
							if specs(k) ~= specs(v) then bad[#bad + 1] = k end
						end
					end
					table.sort(bad)
					if #bad > 0 then return false, #bad .. " von " .. n .. ": " .. table.concat(bad, " | "):sub(1, 200), "0" end
					return true, n .. " Übersetzungen, alle Platzhalter gleich"
				end)
			end
		end

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
		-- 3.0.41: gemeinsame Daten anderer Addons (GoldSentinelSync-Adressbuch) – Abweichung = FEHLER, zurückgesetzt
		local book = _G.GoldSentinelSync and _G.GoldSentinelSync.book
		local sdiff = SyncDiff(R.syncBefore, book, true)
		t:Check("SB2", "A", "gemeinsame Daten unverändert (GoldSentinelSync-Adressbuch: fail, pause, v, src)", function()
			if R.syncBefore == nil then return true, "kein gemeinsames Adressbuch geladen" end
			local n = 0
			for _ in pairs(R.syncBefore) do n = n + 1 end
			if #sdiff > 0 then return false, table.concat(sdiff, ", ", 1, math.min(#sdiff, 5)) .. " (zurückgesetzt)", "unverändert" end
			return true, n .. " Einträge unverändert"
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

	local marktLine = RM.MarktLine and RM.MarktLine() or "MARKT-NETZ: -"
	if R.diagSources and RM.Diag.sources then
		Replace(RM.Diag.sources, R.diagSources.src)
		RM.Diag.sourcesTotal, RM.Diag.firstSource = R.diagSources.total, R.diagSources.first
	end
	local srcLine = RM.Diag.SourcesLine and RM.Diag.SourcesLine() or nil
	local plLines = RM.PLReportLines and RM.PLReportLines() or {}            -- Prüfliste (3.0.28, nur Entwickler)
	local summary, portionLine = R.Summary(t)
	if not aborted then pcall(R.SavePending, t) end           -- TR-ALLE D: Fenster-Schritte vormerken (nur Entwickler)
	local text = t:Finish({ sandbox = sandbox, fehlerzaehler = R.diagBefore .. " -> " .. #RM.Diag.errors, locale = RM.LOCALE,
		markt = marktLine, pruefliste = #plLines > 0 and table.concat(plLines, " | ") or nil, fehlerquellen = srcLine,
		zusammenfassung = summary, portionen = portionLine, umgebung = R.envLine,
		testflavor_ende = G and tostring(G.flavor) or "-", blocked = blocked, echte_aktionen = realN, abgefangen = actList,
		bereich = only or (R.long and "alle (lang)" or "alle"), abbruch = aborted and "ja" or nil })
	text = text .. "\n" .. marktLine                       -- MN3
	text = text .. "\n" .. (R.envLine or "UMGEBUNG: -") .. "\n" .. summary .. "\n" .. portionLine     -- TR-ALLE; RM-UMG1 e)
	text = text .. "\n\nBericht gespeichert – wird beim nächsten /reload oder Ausloggen an die Prüfung gemeldet."
		.. "\nNach der Testroutine bitte /reload (Knopf \"Neu laden und melden\")."
	R.lastText = text
	R.running = false
	pcall(R.ClearGuard, RaidMasterDB)
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
		pcall(R.NotePruefliste, t, only)                 -- Prüfliste (3.0.28): ganze Routine -> Punkte TR und MNT
	end
	pcall(RM.UI.ShowExport, text, { "Neu laden und melden", function() RM.Act.ReloadUI() end })
	Say(summary)
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
