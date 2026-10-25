-- RaidMaster - Lücken füllen
-- Vergleicht den Raid (plus die Angemeldeten, die noch kommen) mit der Mindestaufstellung des Raids
-- (Tanks, Heiler nach Klasse, wichtige Klassen wie Magier/Hexer/Jäger in MC) und schlägt vor, wie die
-- Lücken gefüllt werden – in dieser Reihenfolge:
--   1. Angemeldete, die noch fehlen, einladen
--   2. Ersatzbank (und "vielleicht"), aber nur wer eine Lücke füllt
--   3. Gildenmitglieder, die online sind und passen, anflüstern ("inv" = Einladung)
--   4. Gruppensuche posten (z. B. "LFM 1 Heiler (Priester)"); wer flüstert, wird nach Klasse/Rolle geprüft
--   5. Kurz vor Raidbeginn: Platzfüller von der Ersatzbank, auch wenn sie keine Lücke füllen
-- Nichts davon läuft von selbst – die Raidleitung entscheidet per Klick (Fenster "Lücken füllen").
-- Im Testmodus wird alles simuliert (Test-Tool).

local ADDON, RM = ...
local L = RM.L
local G = {}
RM.Gaps = G

G.FILLER_MINUTES = 5     -- so viele Minuten vor Raidbeginn dürfen Platzfüller von der Ersatzbank rein
G.ASK_TIMEOUT = 180      -- so lange wartet eine Gilden-Anfrage auf Antwort
G.SEARCH_TIME = 1800     -- so lange gilt eine Gruppensuche

G.asked = {}             -- Name -> { t, class, role, label, state = "pending" | "yes" | "no" }
G.answered = {}          -- Fremde, die auf die Gruppensuche schon eine Antwort bekommen haben
G.knownClass = {}        -- Name -> Klasse (aus Flüstern/Gilde/Test)
G.search = nil           -- offene Gesuche der Gruppensuche
G.searchUntil = 0

---------------------------------------------------------------------------
-- Mindestaufstellung
---------------------------------------------------------------------------
G.SIZE = { zg = 20, aq20 = 20, kara = 10, za = 10, ony10 = 10 }
-- healClass: so viele Heiler dieser Klasse mindestens (HYBRID = Paladin oder Schamane)
-- class: so viele Spieler dieser Klasse mindestens (egal welche Rolle)
G.BASE = {
	[40] = { tank = 4, heal = 12, healClass = { PRIEST = 4, HYBRID = 4, DRUID = 1 }, class = { MAGE = 2, WARLOCK = 2, HUNTER = 2 } },
	[25] = { tank = 3, heal = 6, healClass = { PRIEST = 1 }, class = {} },
	[20] = { tank = 2, heal = 5, healClass = { PRIEST = 2 }, class = { MAGE = 1 } },
	[10] = { tank = 2, heal = 3, healClass = {}, class = {} },
}
-- Abweichungen je Raid (nur die genannten Werte)
G.POOL = {
	mc   = { class = { MAGE = 3, WARLOCK = 2, HUNTER = 2 } },          -- Lucifron (Entfluchen), Garr (Verbannen), Magmadar (Einlullen)
	bwl  = { class = { MAGE = 2, WARLOCK = 2, HUNTER = 3 } },          -- Flammenmaul/Chromaggus (Einlullen)
	aq40 = { tank = 5 },
	naxx = { tank = 6, heal = 13 },
	ony  = { tank = 3 },
}

local DEFAULT_ROLE = { WARRIOR = "melee", ROGUE = "melee", DEATHKNIGHT = "melee", MAGE = "ranged", WARLOCK = "ranged",
	HUNTER = "ranged", PRIEST = "heal", PALADIN = "heal", SHAMAN = "heal", DRUID = "heal" }

local function Copy(t)
	if type(t) ~= "table" then return t end
	local o = {}
	for k, v in pairs(t) do o[k] = Copy(v) end
	return o
end

function G.PoolKey()
	local su = RM.db.signup
	return (su and su.pool) or (RM.db.session.active and RM.db.session.pool) or RM.db.config.activePool or "mc"
end

function G.RaidSize(pool)
	local su = RM.db.signup
	if su and tonumber(su.max) then return math.min(40, tonumber(su.max)) end
	pool = pool or G.PoolKey()
	if G.SIZE[pool] then return G.SIZE[pool] end
	local def = RM.Data.Pools[pool]
	if def and def.exp and def.exp ~= "classic" then return 25 end
	return 40
end

function G.Requirement(pool, size)
	pool = pool or G.PoolKey()
	size = size or G.RaidSize(pool)
	local key = size >= 40 and 40 or size >= 25 and 25 or size >= 20 and 20 or 10
	local req = Copy(G.BASE[key])
	local o = G.POOL[pool]
	if o and key == 40 then
		for k, v in pairs(o) do req[k] = Copy(v) end
	end
	return req
end

---------------------------------------------------------------------------
-- Klassen, Rollen
---------------------------------------------------------------------------
local function ClassName(class)
	return (class and LOCALIZED_CLASS_NAMES_MALE and LOCALIZED_CLASS_NAMES_MALE[class]) or class or "?"
end

-- Paladin (Allianz) oder Schamane (Horde)
local function HybridClasses()
	local f = UnitFactionGroup and UnitFactionGroup("player")
	if f == "Alliance" then return { PALADIN = true } end
	if f == "Horde" then return { SHAMAN = true } end
	return { PALADIN = true, SHAMAN = true }
end

local function ClassSet(key)
	if key == "HYBRID" then return HybridClasses() end
	return { [key] = true }
end

-- kann die Klasse diese Rolle überhaupt spielen?
function G.CanDo(class, role)
	local trees = RM.Spec and RM.Spec.TREES[class]
	if not trees then return DEFAULT_ROLE[class] == role end
	for _, t in ipairs(trees) do
		if t[2] == role then return true end
		for _, r in ipairs(t[3] or {}) do if r == role then return true end end
	end
	return false
end

-- Rolle eines Spielers: Skillung (bekannt) > Angabe in der Anmeldung > typische Rolle der Klasse (unsicher)
function G.RoleOf(name, class, hint)
	local r = RM.Spec and name and RM.Spec.Role(name)
	if r then return r, true end
	if hint and RM.Signup.ROLE[hint] then return hint, true end
	return DEFAULT_ROLE[class] or "melee", false
end

local ROLE_WORDS = {
	heal = { "heal", "heil", "holy", "resto", "disc", "wiederherst", "healer" },
	tank = { "tank", "prot", "schutz", "bear", "bär", "baer" },
	melee = { "melee", "nahkampf", "fury", "furor", "combat", "kampf", "feral", "enh", "verstärk", "ret" },
	ranged = { "ranged", "fernkampf", "caster", "shadow", "schatten", "balance", "eule", "boomkin", "ele" },
}
local CLASS_WORDS = {
	PRIEST = { "priest", "priester" }, MAGE = { "mage", "magier" }, WARLOCK = { "warlock", "hexer", "lock" },
	HUNTER = { "hunter", "jäger", "jaeger", "jager" }, ROGUE = { "rogue", "schurke" }, WARRIOR = { "warrior", "krieger", "warri" },
	DRUID = { "druid", "druide", "dudu" }, PALADIN = { "paladin", "pala" }, SHAMAN = { "shaman", "schamane", "shamy", "schami" },
}

function G.RoleHint(msg)
	msg = (msg or ""):lower()
	if msg:find("dps") or msg:find("%f[%w]dd%f[%W]") then
		-- "dps": Nah- oder Fernkampf – genauer geht es nur mit der Klasse
		for _, w in ipairs(ROLE_WORDS.ranged) do if msg:find(w, 1, true) then return "ranged" end end
		for _, w in ipairs(ROLE_WORDS.melee) do if msg:find(w, 1, true) then return "melee" end end
		return "dps"
	end
	for _, role in ipairs({ "heal", "tank", "ranged", "melee" }) do
		for _, w in ipairs(ROLE_WORDS[role]) do if msg:find(w, 1, true) then return role end end
	end
	return nil
end

local function ClassFromText(msg)
	msg = (msg or ""):lower()
	for class, words in pairs(CLASS_WORDS) do
		for _, w in ipairs(words) do if msg:find(w, 1, true) then return class end end
	end
end

-- Klasse eines Spielers: bekannt (Flüstern, Test) > Spielerinfo zum Flüstern (GUID) > Gilde > Text
function G.ClassOf(name, guid, msg)
	name = RM.Short(name)
	if G.knownClass[name] then return G.knownClass[name] end
	if guid and GetPlayerInfoByGUID then
		local ok, _, class = pcall(GetPlayerInfoByGUID, guid)
		if ok and class then G.knownClass[name] = class return class end
	end
	for _, g in ipairs(G.GuildOnline(true)) do
		if g.name == name then return g.class end
	end
	return ClassFromText(msg)
end

---------------------------------------------------------------------------
-- Wer ist da, wer kommt noch?
---------------------------------------------------------------------------
function G.Members()
	local list = {}
	for _, m in ipairs(RM.RaidMembers()) do list[#list + 1] = { name = m.name, class = m.class } end
	if #list == 0 then
		list[1] = { name = RM.Me(), class = select(2, UnitClass("player")) }
		if IsInGroup and IsInGroup() then
			for i = 1, 4 do
				local u = "party" .. i
				if UnitExists(u) then list[#list + 1] = { name = RM.Short(UnitName(u)), class = select(2, UnitClass(u)) } end
			end
		end
	end
	return list
end

local function SignupEntry(name)
	for _, e in ipairs((RM.db.signup and RM.db.signup.list) or {}) do if e.name == name then return e end end
end

local function Pending(name)
	local S = RM.Signup
	if S.IsQueued and S.IsQueued(name) then return true end
	local st, age = S.InviteState(name)
	if st == "invited" and age < 120 then return true end
	local a = G.asked[name]
	if a and (a.state == "yes" or (a.state == "pending" and GetTime() - a.t < G.ASK_TIMEOUT)) then return true end
	return false
end

-- Online-Gildenmitglieder auf Höchststufe (im Testmodus ersetzt das Test-Tool die Liste)
function G.GuildOnline(all)
	if G.SimGuild then return G.SimGuild() end
	local out = {}
	if not (IsInGuild and IsInGuild()) or not GetNumGuildMembers or not GetGuildRosterInfo then return out end
	local maxLvl = (GetMaxPlayerLevel and GetMaxPlayerLevel()) or 60
	for i = 1, GetNumGuildMembers() do
		local name, _, _, level, _, _, _, _, online, _, class = GetGuildRosterInfo(i)
		if name and (all or (online and (level or 0) >= maxLvl)) then
			out[#out + 1] = { name = RM.Short(name), class = class }
		end
	end
	return out
end

---------------------------------------------------------------------------
-- Zusammensetzung und Lücken
---------------------------------------------------------------------------
local function NewComp()
	return { total = 0, tank = 0, heal = 0, healBy = {}, byClass = {} }
end

local function Count(comp, class, role)
	comp.total = comp.total + 1
	comp.byClass[class] = (comp.byClass[class] or 0) + 1
	if role == "tank" then comp.tank = comp.tank + 1 end
	if role == "heal" then
		comp.heal = comp.heal + 1
		comp.healBy[class] = (comp.healBy[class] or 0) + 1
	end
end

local function CountIn(map, set)
	local n = 0
	for cls in pairs(set) do n = n + (map[cls] or 0) end
	return n
end

function G.NeedLabel(need, n)
	n = n or need.n
	local cls
	if need.classes then
		local names = {}
		for c in pairs(need.classes) do names[#names + 1] = ClassName(c) end
		table.sort(names)
		cls = table.concat(names, "/")
	end
	if need.role == "tank" then
		return n .. " " .. (n == 1 and L["Tank"] or L["Tanks"]) .. (cls and (" (" .. cls .. ")") or "")
	elseif need.role == "heal" then
		return n .. " " .. L["Heiler"] .. (cls and (" (" .. cls .. ")") or "")
	end
	return n .. " " .. (cls or "?")
end

-- Lücken der Zusammensetzung gegen die Mindestaufstellung
function G.Needs(comp, req)
	local needs = {}
	local function add(role, classes, n, key)
		if n > 0 then needs[#needs + 1] = { role = role, classes = classes, n = n, key = key } end
	end
	add("tank", nil, req.tank - comp.tank, "tank")
	local classHeal = 0
	local keys = {}
	for k in pairs(req.healClass or {}) do keys[#keys + 1] = k end
	table.sort(keys)
	for _, k in ipairs(keys) do
		local set = ClassSet(k)
		local miss = req.healClass[k] - CountIn(comp.healBy, set)
		if miss > 0 then
			add("heal", set, miss, "heal:" .. k)
			classHeal = classHeal + miss
		end
	end
	add("heal", nil, (req.heal - comp.heal) - classHeal, "heal")
	keys = {}
	for k in pairs(req.class or {}) do keys[#keys + 1] = k end
	table.sort(keys)
	for _, k in ipairs(keys) do
		local set = ClassSet(k)
		add(nil, set, req.class[k] - CountIn(comp.byClass, set), "class:" .. k)
	end
	return needs
end

-- passt ein Kandidat zu einem Gesuch? (true = sicher, "maybe" = Skillung unbekannt)
function G.Fits(need, c)
	if need.classes and not need.classes[c.class] then return false end
	if not need.role then return true end
	if c.role == need.role then return true end
	if not c.roleKnown and G.CanDo(c.class, need.role) then return "maybe" end
	return false
end

local function Candidate(name, class, hint, source)
	local role, known = G.RoleOf(name, class, hint)
	return { name = name, class = class, role = role, roleKnown = known, source = source }
end

function G.NearStart()
	if RM.db.session.active then return true end
	local su = RM.db.signup
	return su ~= nil and su.start ~= nil and GetServerTime() >= su.start - G.FILLER_MINUTES * 60
end

-- Vorschlag berechnen
function G.Plan()
	local S = RM.Signup
	local su = RM.db.signup
	local pool = G.PoolKey()
	local size = G.RaidSize(pool)
	local req = G.Requirement(pool, size)
	local plan = { pool = pool, size = size, signed = {}, bench = {}, guild = {}, filler = {}, search = {} }
	local comp = NewComp()
	local inRaid = {}
	for _, m in ipairs(G.Members()) do
		inRaid[m.name] = true
		local e = SignupEntry(m.name)
		local role = G.RoleOf(m.name, m.class, e and e.role)
		Count(comp, m.class, role)
	end
	plan.have = comp.total
	-- wer sicher noch kommt: Angemeldete (nicht "nicht gefunden"/"abgelehnt"), laufende Einladungen, zugesagte Gildenmitglieder
	local expected = 0
	local counted = {}
	for _, e in ipairs((su and su.list) or {}) do
		if not inRaid[e.name] and e.name ~= RM.Me() then
			if e.status == "an" and not S.RecentlyFailed(e.name) then
				local role = G.RoleOf(e.name, e.cls, e.role)
				Count(comp, e.cls, role)
				counted[e.name] = true
				expected = expected + 1
				if not Pending(e.name) then plan.signed[#plan.signed + 1] = e.name end
			elseif Pending(e.name) then
				Count(comp, e.cls, (G.RoleOf(e.name, e.cls, e.role)))
				counted[e.name] = true
				expected = expected + 1
			end
		end
	end
	for name, a in pairs(G.asked) do
		if not inRaid[name] and not counted[name] and Pending(name) then
			Count(comp, a.class, a.role)
			counted[name] = true
			expected = expected + 1
		end
	end
	plan.expected = expected
	plan.free = math.max(0, size - comp.total)
	-- nie mehr vorschlagen, als wirklich Platz ist (Anwesende + offene Einladungen, höchstens 40)
	if RM.Signup.Capacity then plan.free = math.max(0, math.min(plan.free, RM.Signup.Capacity())) end
	plan.needs = G.Needs(comp, req)
	plan.complete = #plan.needs == 0

	local slots = plan.free
	local open = Copy(plan.needs)
	local used = {}
	local function Usable(name)
		return not inRaid[name] and not counted[name] and not used[name] and name ~= RM.Me()
			and not S.RecentlyFailed(name) and not Pending(name)
	end
	local function Assign(cands, out)
		-- sichere Treffer zuerst, dann "Skillung unbekannt"
		for pass = 1, 2 do
			for _, need in ipairs(open) do
				for _, c in ipairs(cands) do
					if slots <= 0 or need.n <= 0 then break end
					if Usable(c.name) then
						local fit = G.Fits(need, c)
						if (pass == 1 and fit == true) or (pass == 2 and fit == "maybe") then
							used[c.name] = true
							need.n = need.n - 1
							slots = slots - 1
							c.need = need
							c.label = G.NeedLabel(need, 1):gsub("^1 ", "")
							c.maybe = fit == "maybe"
							out[#out + 1] = c
						end
					end
				end
			end
		end
	end
	-- Ersatzbank, dann "vielleicht"
	local bench, maybe = {}, {}
	for _, e in ipairs((su and su.list) or {}) do
		if e.status == "ersatz" or (su.bench and su.bench[e.name]) then
			bench[#bench + 1] = Candidate(e.name, e.cls, e.role, "bench")
		elseif e.status == "vielleicht" then
			maybe[#maybe + 1] = Candidate(e.name, e.cls, e.role, "maybe")
		end
	end
	Assign(bench, plan.bench)
	Assign(maybe, plan.bench)
	-- Gilde (nicht angemeldet, nicht abgemeldet, nicht schon gefragt und abgelehnt)
	local guild = {}
	for _, g in ipairs(G.GuildOnline()) do
		local a = G.asked[g.name]
		if not SignupEntry(g.name) and not (a and a.state == "no" and GetTime() - a.t < 3600) and g.class then
			guild[#guild + 1] = Candidate(g.name, g.class, nil, "guild")
		end
	end
	Assign(guild, plan.guild)
	-- was übrig bleibt: Gruppensuche
	for _, need in ipairs(open) do
		if need.n > 0 then plan.search[#plan.search + 1] = need end
	end
	-- Platzfüller kurz vor Beginn (Ersatzbank/vielleicht, auch ohne Lücke)
	plan.fillerAllowed = G.NearStart()
	plan.fillerAt = su and su.start and (su.start - G.FILLER_MINUTES * 60) or nil
	local rest = slots
	for _, list in ipairs({ bench, maybe }) do
		for _, c in ipairs(list) do
			if rest > 0 and Usable(c.name) then
				plan.filler[#plan.filler + 1] = c
				used[c.name] = true
				rest = rest - 1
			end
		end
	end
	plan.slotsAfter = slots
	return plan
end

function G.NeedsText(needs)
	local parts = {}
	for _, n in ipairs(needs) do if n.n > 0 then parts[#parts + 1] = G.NeedLabel(n) end end
	return table.concat(parts, ", ")
end

---------------------------------------------------------------------------
-- Aktionen
---------------------------------------------------------------------------
local function Names(list)
	local out = {}
	for _, c in ipairs(list) do out[#out + 1] = c.name end
	return out
end

local function RaidName(pool)
	local su = RM.db.signup
	if su and su.title and su.title ~= "" then return (su.title:gsub("^TEST ", "")) end
	return RM.DKP.PoolName(pool or G.PoolKey())
end

function G.InviteSigned(plan)
	plan = plan or G.Plan()
	if #plan.signed == 0 then RM.Print(L["Alle Angemeldeten sind schon im Raid oder eingeladen."]) return 0 end
	return RM.Signup.InviteNames(plan.signed)
end

function G.InviteBench(plan)
	plan = plan or G.Plan()
	if #plan.bench == 0 then RM.Print(L["Auf der Ersatzbank ist niemand, der eine Lücke füllt."]) return 0 end
	for _, c in ipairs(plan.bench) do
		RM.Print(string.format(L["Lücken füllen: %s von der Ersatzbank (%s)."], c.name, c.label))
	end
	return RM.Signup.InviteNames(Names(plan.bench))
end

function G.InviteFiller(plan)
	plan = plan or G.Plan()
	if not plan.fillerAllowed then
		RM.Print(string.format(L["Platzfüller erst ab %d Min. vor Raidbeginn oder nach dem Raidstart."], G.FILLER_MINUTES))
		return 0
	end
	if #plan.filler == 0 then RM.Print(L["Keine Platzfüller auf der Ersatzbank."]) return 0 end
	return RM.Signup.InviteNames(Names(plan.filler))
end

function G.AskGuild(plan)
	plan = plan or G.Plan()
	if #plan.guild == 0 then RM.Print(L["In der Gilde ist gerade niemand online, der eine Lücke füllt."]) return 0 end
	local raid = RaidName(plan.pool)
	for _, c in ipairs(plan.guild) do
		G.asked[c.name] = { t = GetTime(), class = c.class, role = c.need and c.need.role or c.role, label = c.label, state = "pending" }
		RM.Whisper(string.format(L["Hallo %s! Wir starten %s und suchen noch: %s. Hast du Zeit? Antworte mit 'inv', dann lade ich dich ein."],
			c.name, raid, c.label), c.name)
		if G.SimulateAsk then G.SimulateAsk(c.name, c) end
	end
	RM.Print(string.format(L["%d Gildenmitglieder gefragt – wer mit 'inv' antwortet, wird eingeladen."], #plan.guild))
	RM.Fire("GAPS_CHANGED")
	return #plan.guild
end

function G.SearchText(plan)
	plan = plan or G.Plan()
	if #plan.search == 0 then return "" end
	return string.format(L["[%s] LFM %s – /w %s inv + Klasse/Rolle"], RaidName(plan.pool), G.NeedsText(plan.search), RM.Me() or "")
end

-- Gruppensuche posten (muss aus einem Mausklick kommen – öffentliche Kanäle)
function G.PostSearch(plan)
	plan = plan or G.Plan()
	if #plan.search == 0 then RM.Print(L["Es fehlt nichts mehr – keine Gruppensuche nötig."]) return false end
	if not RM.Ad or not RM.Ad.PostText then return false end
	local old, oldUntil, oldAnswered = G.search, G.searchUntil, G.answered
	G.search = Copy(plan.search)
	G.searchUntil = GetTime() + G.SEARCH_TIME
	G.answered = {}
	if RM.Ad.PostText(G.SearchText(plan)) then
		RM.Fire("GAPS_CHANGED")
		return true
	end
	G.search, G.searchUntil, G.answered = old, oldUntil, oldAnswered
	return false
end

function G.StopSearch(msg)
	G.search = nil
	G.searchUntil = 0
	if msg then RM.Print(msg) end
	RM.Fire("GAPS_CHANGED")
end

function G.Searching()
	if not G.search or GetTime() > G.searchUntil then return false end
	for _, n in ipairs(G.search) do if n.n > 0 then return true end end
	return false
end

-- alles auf einmal: Angemeldete + passende Ersatzbank einladen, passende Gilde fragen
function G.DoAll()
	local plan = G.Plan()
	local n = 0
	if #plan.signed > 0 then n = n + (RM.Signup.InviteNames(plan.signed) or 0) end
	if #plan.bench > 0 then n = n + (G.InviteBench(plan) or 0) end
	if #plan.guild > 0 then G.AskGuild(plan) end
	if plan.fillerAllowed and #plan.filler > 0 then n = n + (RM.Signup.InviteNames(Names(plan.filler)) or 0) end
	if n == 0 and #plan.guild == 0 then
		if #plan.search > 0 then
			RM.Print(L["Ersatzbank und Gilde reichen nicht – jetzt \"Gruppensuche posten\"."])
		else
			RM.Print(L["Es fehlt nichts mehr."])
		end
	end
	return plan
end

---------------------------------------------------------------------------
-- Antworten (Flüstern)
---------------------------------------------------------------------------
local YES = { "inv", "ja", "yes", "klar", "gern", "komme", "bin dabei", "ok", "+", "1", "jo", "y" }
local NO = { "nein", "no", "sorry", "keine zeit", "heute nicht", "kann nicht", "nö", "noe", "leider" }

local function Has(msg, words, exact)
	msg = msg:lower():gsub("^%s+", ""):gsub("%s+$", "")
	for _, w in ipairs(words) do
		if msg == w then return true end
		if not exact and #w > 1 and msg:find("%f[%w]" .. w:gsub("([%+%-%.])", "%%%1") .. "%f[%W]") then return true end
	end
	return false
end

function G.HandlesWhisper(sender)
	local name = RM.Short(sender)
	local a = G.asked[name]
	if a and a.state == "pending" and GetTime() - a.t < G.ASK_TIMEOUT then return true end
	return G.Searching()
end

function G.OnWhisper(msg, sender, guid)
	if not RM.db or type(msg) ~= "string" or not sender then return end
	local name = RM.Short(sender)
	if name == RM.Me() then return end
	local a = G.asked[name]
	if a and a.state == "pending" and GetTime() - a.t < G.ASK_TIMEOUT then
		if Has(msg, NO) then
			a.state = "no"
			RM.Print(string.format(L["%s hat keine Zeit."], name))
			RM.Fire("GAPS_CHANGED")
		elseif Has(msg, YES) then
			if RM.Signup.Capacity() <= 0 then
				a.state = "no"
				RM.Whisper(L["Danke! Leider ist der Raid inzwischen voll."], name)
				RM.Print(string.format(L["%s würde kommen, aber der Raid ist voll."], name))
				RM.Fire("GAPS_CHANGED")
				return
			end
			a.state = "yes"
			RM.Print(string.format(L["%s kommt – wird eingeladen (%s)."], name, a.label or "?"))
			RM.Signup.InviteNames({ name })
			RM.Fire("GAPS_CHANGED")
		end
		return
	end
	if not G.Searching() then return end
	local m = msg:lower()
	if not m:find("inv", 1, true) and not Has(msg, YES, true) then return end
	if G.answered[name] or RM.IsInMyRaid(name) then return end
	if RM.Signup.Capacity() <= 0 then
		G.answered[name] = true
		RM.Whisper(L["Danke! Leider ist der Raid inzwischen voll."], name)
		G.StopSearch(string.format(L["Gruppensuche beendet – der Raid ist voll (%d/%d)."], RM.Signup.MemberCount(), RM.Signup.RaidSize()))
		return
	end
	local class = G.ClassOf(name, guid, msg)
	if not class then
		RM.Whisper(L["Welche Klasse und Rolle? Schreib z. B. 'inv heal priest'."], name)
		return
	end
	G.knownClass[name] = class
	local hint = G.RoleHint(msg)
	local ask
	for _, need in ipairs(G.search) do
		if need.n > 0 and (not need.classes or need.classes[class]) then
			local ok = false
			if not need.role then
				ok = true
			elseif hint == need.role then
				ok = true
			elseif not hint or hint == "dps" then
				if DEFAULT_ROLE[class] == need.role and hint ~= "dps" then ok = true
				elseif G.CanDo(class, need.role) and not hint then ask = ask or need end
			end
			if ok then
				need.n = need.n - 1
				G.answered[name] = true
				local label = G.NeedLabel(need, 1):gsub("^1 ", "")
				RM.Whisper(string.format(L["Danke! Du wirst eingeladen (%s)."], label), name)
				RM.Print(string.format(L["Gruppensuche: %s (%s) wird eingeladen als %s."], name, ClassName(class), label))
				RM.Signup.InviteNames({ name })
				if not G.Searching() then G.StopSearch(L["Gruppensuche: alle Lücken gefüllt."]) end
				RM.Fire("GAPS_CHANGED")
				return
			end
		end
	end
	if ask then
		RM.Whisper(string.format(L["Wir suchen %s – kannst du das spielen? Dann schreib 'inv %s'."], G.NeedLabel(ask, 1):gsub("^1 ", ""), ask.role), name)
		return
	end
	G.answered[name] = true
	RM.Whisper(string.format(L["Danke! Gerade suchen wir nur: %s."], G.NeedsText(G.search)), name)
end

RM.On("CHAT_MSG_WHISPER", function(msg, sender, ...)
	local guid = select(10, ...)
	G.OnWhisper(msg, sender, guid)
end)

---------------------------------------------------------------------------
-- Fenster
---------------------------------------------------------------------------
local win

local function Create()
	local UI = RM.UI
	local COLORS = UI.COLORS
	local W = 540
	local f = UI.Frame(UIParent, W, 470)
	UI.Skin(f)
	f:SetFrameStrata("HIGH")
	f:SetClampedToScreen(true)
	UI.MakeMovable(f, "gaps", "CENTER", 0, 40)
	_G.RaidMasterGapsFrame = f
	if UISpecialFrames then tinsert(UISpecialFrames, "RaidMasterGapsFrame") end
	local title = UI.Header(f, L["Lücken füllen"])
	title:SetPoint("TOPLEFT", 14, -12)
	local close = UI.CloseButton(f, function() f:Hide() end)
	close:SetPoint("TOPRIGHT", -8, -8)
	f.need = UI.Text(f, "", 12)
	f.need:SetPoint("TOPLEFT", 14, -40)
	f.need:SetWidth(W - 28)

	local rows = {}
	local function Row(y, text, tip, onClick)
		local b = UI.Button(f, text, 190, 28, function() onClick(); G.Refresh() end, tip)
		b:SetPoint("TOPLEFT", 14, y)
		local t = UI.Text(f, "", 11, COLORS.muted[1], COLORS.muted[2], COLORS.muted[3])
		t:SetPoint("TOPLEFT", b, "TOPRIGHT", 10, -2)
		t:SetWidth(W - 230)
		rows[#rows + 1] = { b = b, t = t }
		return b, t
	end
	f.signedBtn, f.signedText = Row(-104, L["Angemeldete einladen"], L["Angemeldete, die noch fehlen (ohne 'nicht gefunden'/'abgelehnt')."], function() G.InviteSigned() end)
	f.benchBtn, f.benchText = Row(-150, L["Ersatzbank einladen"], L["Nur wer von der Ersatzbank (oder 'vielleicht') eine Lücke füllt."], function() G.InviteBench() end)
	f.guildBtn, f.guildText = Row(-196, L["Gilde fragen"], L["Passende Gildenmitglieder, die online sind, werden angeflüstert. Antwort 'inv' = Einladung."], function() G.AskGuild() end)
	f.searchBtn, f.searchText = Row(-242, L["Gruppensuche posten"], L["Postet ein Gesuch im Werbekanal (Seite PUG/Werbung). Wer flüstert, wird nach Klasse und Rolle geprüft."], function() G.PostSearch() end)
	f.fillerBtn, f.fillerText = Row(-288, L["Platzfüller einladen"], L["Kurz vor Raidbeginn: freie Plätze mit der übrigen Ersatzbank füllen – besser als leere Plätze."], function() G.InviteFiller() end)

	f.status = UI.Text(f, "", 11)
	f.status:SetPoint("TOPLEFT", 14, -340)
	f.status:SetWidth(W - 28)

	local all = UI.Button(f, L["Alles auf einmal"], 240, 32, function() G.DoAll(); G.Refresh() end,
		L["Angemeldete und passende Ersatzbank einladen, passende Gilde fragen (und kurz vor Beginn Platzfüller).\nDie Gruppensuche postest du selbst, wenn das nicht reicht."])
	all:SetPoint("BOTTOMLEFT", 14, 14)
	all:SetAccent(true)
	local stop = UI.Button(f, L["Suche beenden"], 140, 32, function() G.StopSearch(L["Gruppensuche beendet."]); G.Refresh() end)
	stop:SetPoint("LEFT", all, "RIGHT", 8, 0)
	f.stopBtn = stop
	f:SetScript("OnShow", function() G.Refresh() end)
	local acc = 0
	f:SetScript("OnUpdate", function(_, el)
		acc = acc + el
		if acc > 1 then acc = 0; G.Refresh() end
	end)
	f:Hide()
	return f
end

local function ListText(list)
	local parts = {}
	for _, c in ipairs(list) do
		parts[#parts + 1] = RM.ClassColor(c.class, c.name) .. " (" .. (c.label or "?") .. (c.maybe and (", " .. L["Skillung unbekannt"]) or "") .. ")"
	end
	return table.concat(parts, ", ")
end

function G.Refresh()
	if not win or not win:IsShown() then return end
	local p = G.Plan()
	local head = string.format(L["%s: %d/%d im Raid, %d kommen noch · frei: %d"], RaidName(p.pool), p.have, p.size, p.expected, p.free)
		.. "\n" .. RM.Signup.CapacityText()
	if p.complete then
		head = head .. "\n|cff66ff66" .. L["Aufstellung komplett – Tanks, Heiler und wichtige Klassen sind da."] .. "|r"
	else
		head = head .. "\n|cffffcc00" .. L["Fehlt:"] .. "|r " .. G.NeedsText(p.needs)
	end
	if RM.Test and RM.Test.active then head = head .. "  |cffff8c1a(" .. L["TEST"] .. ")|r" end
	win.need:SetText(head)
	local function Set(btn, txt, list, text)
		btn:SetText(txt .. (#list > 0 and (" (" .. #list .. ")") or ""))
		if #list > 0 then btn:Enable() else btn:Disable() end
	end
	Set(win.signedBtn, L["Angemeldete einladen"], p.signed)
	win.signedText:SetText(#p.signed > 0 and table.concat(p.signed, ", ") or L["alle da oder eingeladen"])
	Set(win.benchBtn, L["Ersatzbank einladen"], p.bench)
	win.benchText:SetText(#p.bench > 0 and ListText(p.bench) or L["niemand auf der Bank füllt eine Lücke"])
	Set(win.guildBtn, L["Gilde fragen"], p.guild)
	win.guildText:SetText(#p.guild > 0 and ListText(p.guild) or L["niemand Passendes online"])
	win.searchBtn:SetText(L["Gruppensuche posten"])
	if #p.search > 0 then win.searchBtn:Enable() else win.searchBtn:Disable() end
	win.searchText:SetText(#p.search > 0 and G.SearchText(p) or L["nicht nötig"])
	Set(win.fillerBtn, L["Platzfüller einladen"], p.filler)
	if not p.fillerAllowed then win.fillerBtn:Disable() end
	if p.fillerAllowed then
		win.fillerText:SetText(#p.filler > 0 and ListText(p.filler) or L["keine freien Plätze oder niemand übrig"])
	else
		win.fillerText:SetText(p.fillerAt and string.format(L["erst ab %s (%d Min. vor Beginn) oder nach dem Raidstart"], date("%H:%M", p.fillerAt), G.FILLER_MINUTES)
			or L["erst nach dem Raidstart"])
	end
	local st = {}
	if G.Searching() then
		st[#st + 1] = string.format(L["Gruppensuche läuft noch %d Min. – gesucht: %s"], math.ceil((G.searchUntil - GetTime()) / 60), G.NeedsText(G.search))
		win.stopBtn:Enable()
	else
		win.stopBtn:Disable()
	end
	local pending = {}
	for name, a in pairs(G.asked) do
		if a.state == "pending" and GetTime() - a.t < G.ASK_TIMEOUT then pending[#pending + 1] = name end
	end
	if #pending > 0 then table.sort(pending); st[#st + 1] = L["Warte auf Antwort: "] .. table.concat(pending, ", ") end
	win.status:SetText(table.concat(st, "\n"))
end

function G.Toggle()
	win = win or Create()
	if win:IsShown() then win:Hide() else win:Show() end
end

function G.Open()
	win = win or Create()
	win:Show()
	G.Refresh()
end

RM.Listen("SIGNUP_CHANGED", function() G.Refresh() end)
RM.Listen("GAPS_CHANGED", function() G.Refresh() end)
RM.On("GROUP_ROSTER_UPDATE", function() G.Refresh() end)
