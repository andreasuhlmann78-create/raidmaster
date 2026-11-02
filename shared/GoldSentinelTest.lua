--[[
GoldSentinelTest.lua – gemeinsame Testberichte und Fehlermeldungen aller GoldSentinel-Addons
============================================================================================
Gepflegt von der Prüf-Sitzung im raidmaster-Repo (shared/GoldSentinelTest.lua). Unverändert in jedes Addon kopieren,
in der .toc direkt nach GoldSentinelGame.lua. Mehrere Addons dürfen verschiedene Fassungen mitbringen: die höchste
VERSION gewinnt, ältere treten zurück.

Weg der Berichte: Addon -> eigene SavedVariables (db.gsTest) -> RaidMasterUploader auf dem PC (sucht Strings, die mit
"GSTEST1" beginnen) -> Discord #testberichte -> GitHub (testberichte/) -> Prüf-Sitzung.

Benutzung im Addon:
    local GT = GoldSentinelTest
    -- einmal nach ADDON_LOADED, wenn die SavedVariables da sind:
    GT.TrackErrors("MeinAddon", "1.2.3", MeinAddonDB)      -- Lua-Fehler des Addons auch im normalen Spiel zählen
    GT.Error("MeinAddon", "Scan", err)                       -- bei selbst abgefangenen Fehlern (pcall/Safe/Try)
    -- Testroutine:
    local T = GT.Begin("MeinAddon", "1.2.3", MeinAddonDB)
    T:Check("T01", "A", "Version in .toc = Code", function() return toc == code, code, toc end)
    T:Skip("T02", "C", "Kampflog", "nur alter Client")
    T:Client("T03", "C", "Händler-Kosten", "/dump GetMerchantItemCostInfo")
    local text = T:Finish({ sandbox = "OK" })                -- speichert den Bericht, Text fürs Kopierfenster
Check: die Funktion gibt ok, ergebnis, erwartet zurück. Kein Rückgabewert = OK, false = FEHLER, Lua-Fehler = FEHLER.

Datenschutz: Keine Spieler-, Gilden- oder Chatnamen in Berichte schreiben. Geschützte Werte ("secret values") werden
nie gelesen, sondern als "<geschützt>" vermerkt.
]]

local VERSION = 1

local existing = _G.GoldSentinelTest
if type(existing) == "table" and type(existing.version) == "number" and existing.version >= VERSION then return end

local T = {}
T.version = VERSION
T.PREFIX = "GSTEST1"
T.MAX_REPORTS = 10
T.MAX_RESULTS = 400
T.MAX_ERRORS = 50
T.MAX_TEXT = 300
-- Register bleibt über Fassungen hinweg erhalten (eine neuere Fassung übernimmt die Addons der älteren)
T.registry = (type(existing) == "table" and type(existing.registry) == "table") and existing.registry or {}
_G.GoldSentinelTest = T

------------------------------------------------------------------------
-- Hilfen
------------------------------------------------------------------------
local function IsSecret(v)
    local G = _G.GoldSentinelGame
    if G and G.IsSecret then
        local ok, r = pcall(G.IsSecret, v)
        if ok then return r == true end
    end
    if type(issecretvalue) == "function" then
        local ok, r = pcall(issecretvalue, v)
        return ok and r == true
    end
    return false
end
T.IsSecret = IsSecret

-- beliebiger Wert -> kurzer, sicherer Text
local function Str(v, max)
    if v == nil then return nil end
    if IsSecret(v) then return "<geschützt>" end
    local tv = type(v)
    local s
    if tv == "string" then s = v
    elseif tv == "number" or tv == "boolean" then s = tostring(v)
    else
        local ok, r = pcall(tostring, v)
        s = ok and type(r) == "string" and not IsSecret(r) and r or ("<" .. tv .. ">")
    end
    max = max or T.MAX_TEXT
    if #s > max then s = s:sub(1, max) .. "…" end
    return s
end
T.Str = Str

local function Now()
    return (type(time) == "function" and time()) or os.time()
end

local function Ms()
    if type(debugprofilestop) == "function" then return debugprofilestop() end
    if type(GetTime) == "function" then return GetTime() * 1000 end
    return os.clock() * 1000
end

local counter = 0
local function NewId(addon)
    counter = counter + 1
    local r = math.random and math.random(0, 0xFFFFFF) or 0
    return string.format("%s-%d-%06x-%d", tostring(addon), Now(), r, counter)
end

------------------------------------------------------------------------
-- JSON (klein, Lua 5.1)
------------------------------------------------------------------------
local ESC = { ['"'] = '\\"', ["\\"] = "\\\\", ["\b"] = "\\b", ["\f"] = "\\f", ["\n"] = "\\n", ["\r"] = "\\r", ["\t"] = "\\t" }
local function JStr(s)
    return '"' .. s:gsub('[%c"\\]', function(c) return ESC[c] or string.format("\\u%04x", c:byte()) end) .. '"'
end

local function IsArray(t)
    local n = 0
    for k in pairs(t) do
        if type(k) ~= "number" or k < 1 or k % 1 ~= 0 then return false end
        n = n + 1
    end
    for i = 1, n do if t[i] == nil then return false end end
    return true, n
end

local function Encode(v, depth)
    depth = depth or 0
    if depth > 8 then return '"<zu tief>"' end
    if IsSecret(v) then return '"<geschützt>"' end
    local tv = type(v)
    if v == nil then return "null"
    elseif tv == "boolean" then return v and "true" or "false"
    elseif tv == "number" then
        if v ~= v or v == math.huge or v == -math.huge then return "null" end
        if v % 1 == 0 and v > -1e15 and v < 1e15 then return string.format("%d", v) end
        return string.format("%.6g", v)
    elseif tv == "string" then return JStr(v)
    elseif tv == "table" then
        local arr, n = IsArray(v)
        local out = {}
        if arr then
            for i = 1, n do out[i] = Encode(v[i], depth + 1) end
            return "[" .. table.concat(out, ",") .. "]"
        end
        local keys = {}
        for k in pairs(v) do if type(k) == "string" or type(k) == "number" then keys[#keys + 1] = k end end
        table.sort(keys, function(a, b) return tostring(a) < tostring(b) end)
        for _, k in ipairs(keys) do
            if not IsSecret(k) then out[#out + 1] = JStr(tostring(k)) .. ":" .. Encode(v[k], depth + 1) end
        end
        return "{" .. table.concat(out, ",") .. "}"
    end
    return JStr("<" .. tv .. ">")
end
T.Encode = Encode

------------------------------------------------------------------------
-- Umgebung (ohne Namen)
------------------------------------------------------------------------
local function Env()
    local e = {}
    if type(GetBuildInfo) == "function" then
        local ok, ver, build, _, iface = pcall(GetBuildInfo)
        if ok then e.client, e.build, e.interface = Str(ver), Str(build), tonumber(iface) end
    end
    e.project = tonumber(_G.WOW_PROJECT_ID)
    local G = _G.GoldSentinelGame
    if G then
        e.flavor = Str(G.flavor)
        e.gsgame = tonumber(G.version) or tonumber(G.apiVersion)
        if type(G.Status) == "function" then
            local ok, s = pcall(G.Status)
            if ok then e.status = Str(s, 400) end
        end
    end
    if type(GetLocale) == "function" then e.locale = Str(GetLocale()) end
    if type(UnitClass) == "function" then
        local ok, _, class = pcall(UnitClass, "player")
        if ok then e.class = Str(class) end
    end
    if type(UnitLevel) == "function" then
        local ok, lv = pcall(UnitLevel, "player")
        if ok and not IsSecret(lv) then e.level = tonumber(lv) end
    end
    -- ein simulierter Client (G.SetTestFlavor) steht in e.status als "[Test]"
    return e
end
T.Env = Env

------------------------------------------------------------------------
-- Speichern in den SavedVariables des Addons
------------------------------------------------------------------------
local function Store(db)
    if type(db) ~= "table" then return nil end
    if type(db.gsTest) ~= "table" then db.gsTest = {} end
    local s = db.gsTest
    if type(s.reports) ~= "table" then s.reports = {} end
    if type(s.errors) ~= "table" then s.errors = {} end
    return s
end

local function Save(db, report)
    local s = Store(db)
    if not s then return false end
    s.reports[#s.reports + 1] = T.PREFIX .. Encode(report)
    while #s.reports > T.MAX_REPORTS do table.remove(s.reports, 1) end
    return true
end
T.Save = Save

------------------------------------------------------------------------
-- Testlauf
------------------------------------------------------------------------
local Run = {}
Run.__index = Run

function T.Begin(addon, version, db)
    local r = setmetatable({}, Run)
    r.addon, r.version, r.db = Str(addon), Str(version), db
    r.results, r.counts = {}, { ok = 0, fehler = 0, uebersprungen = 0, client = 0 }
    r.t0, r.started = Ms(), Now()
    return r
end

function Run:Add(status, id, area, name, extra)
    local key = ({ OK = "ok", FEHLER = "fehler", SKIP = "uebersprungen", CLIENT = "client" })[status]
    self.counts[key] = self.counts[key] + 1
    if #self.results >= T.MAX_RESULTS and status == "OK" then return end   -- bei sehr vielen Prüfungen nur OK weglassen
    local e = { id = Str(id, 20), bereich = Str(area, 20), name = Str(name, 120), status = status }
    if extra then for k, v in pairs(extra) do e[k] = Str(v) end end
    self.results[#self.results + 1] = e
end

function Run:Check(id, area, name, fn)
    local t = Ms()
    local ok, a, b, c = pcall(fn)
    local ms = Ms() - t
    local extra = { ms = string.format("%.1f", ms) }
    if not ok then
        extra.lua = a
        self:Add("FEHLER", id, area, name, extra)
        return false
    end
    if a == false then
        extra.ergebnis, extra.erwartet = b, c
        self:Add("FEHLER", id, area, name, extra)
        return false
    end
    if b ~= nil then extra.ergebnis = b end
    self:Add("OK", id, area, name, extra)
    return true
end

function Run:Skip(id, area, name, reason) self:Add("SKIP", id, area, name, { grund = reason }) end
function Run:Client(id, area, name, how) self:Add("CLIENT", id, area, name, { anleitung = how }) end

function Run:Report(extra)
    local rep = {
        f = 1, id = NewId(self.addon), kind = "test", addon = self.addon, version = self.version,
        time = self.started, dur_ms = math.floor(Ms() - self.t0 + 0.5), env = Env(),
        counts = self.counts, results = self.results,
    }
    if type(extra) == "table" then
        for k, v in pairs(extra) do if rep[k] == nil then rep[k] = (type(v) == "table") and v or Str(v) end end
    end
    -- laufende Fehler dieses Addons mitschicken
    local s = Store(self.db)
    if s then rep.errors = T.ErrorList(s) end
    return rep
end

function Run:Text(rep)
    rep = rep or self:Report()
    local c = rep.counts
    local out = {
        string.format("%s %s – Testroutine · %s", tostring(rep.addon), tostring(rep.version),
            type(date) == "function" and date("%d.%m.%Y %H:%M", rep.time) or tostring(rep.time)),
        string.format("Client %s (%s) · Interface %s · %s · %s %s · Sprache %s",
            tostring(rep.env.client), tostring(rep.env.build), tostring(rep.env.interface), tostring(rep.env.flavor),
            tostring(rep.env.class), tostring(rep.env.level), tostring(rep.env.locale)),
    }
    if rep.env.status then out[#out + 1] = "GoldSentinelGame: " .. rep.env.status end
    out[#out + 1] = string.format("OK %d · FEHLER %d · übersprungen %d · im Client prüfen %d · %d ms",
        c.ok, c.fehler, c.uebersprungen, c.client, rep.dur_ms)
    if rep.sandbox then out[#out + 1] = "Sandbox (echte Daten unverändert): " .. tostring(rep.sandbox) end
    for _, e in ipairs(rep.results) do
        if e.status ~= "OK" then
            out[#out + 1] = string.format("  [%s] %s %s – %s%s%s%s", e.status, tostring(e.id), tostring(e.bereich),
                tostring(e.name),
                e.lua and (" | Lua: " .. e.lua) or "",
                e.ergebnis and (" | ist: " .. e.ergebnis) or "",
                (e.erwartet and (" | soll: " .. e.erwartet)) or (e.grund and (" | " .. e.grund)) or
                (e.anleitung and (" | " .. e.anleitung)) or "")
        end
    end
    if rep.errors and #rep.errors > 0 then
        out[#out + 1] = string.format("Fehler im Spiel seit dem letzten Bericht: %d", #rep.errors)
        for _, e in ipairs(rep.errors) do
            out[#out + 1] = string.format("  %d× %s: %s", e.count or 1, tostring(e.wo), tostring(e.msg))
        end
    end
    return table.concat(out, "\n")
end

-- speichert den Bericht und gibt den Text zurück
function Run:Finish(extra)
    local rep = self:Report(extra)
    local saved = Save(self.db, rep)
    local s = Store(self.db)
    if saved and s then s.errors, s.lastFlush = {}, Now() end          -- mitgeschickt
    self.report = rep
    local text = self:Text(rep)
    if not saved then text = text .. "\n(Bericht konnte nicht gespeichert werden – keine SavedVariables)" end
    return text, rep
end

------------------------------------------------------------------------
-- Fehler im normalen Spiel
------------------------------------------------------------------------
function T.ErrorList(s)
    local list = {}
    for _, e in pairs(s.errors or {}) do if type(e) == "table" then list[#list + 1] = e end end
    table.sort(list, function(a, b) return (a.count or 0) > (b.count or 0) end)
    return list
end

local function Record(addon, where, msg, stack)
    local reg = T.registry[addon]
    if not reg then return end
    local s = Store(reg.db)
    if not s then return end
    where, msg = Str(where, 60) or "?", Str(msg) or "?"
    local key = where .. "|" .. msg
    local e = s.errors[key]
    if not e then
        local n = 0
        for _ in pairs(s.errors) do n = n + 1 end
        if n >= T.MAX_ERRORS then return end
        e = { wo = where, msg = msg, count = 0, first = Now(), version = reg.version }
        if stack then e.stack = Str(stack, 600) end
        s.errors[key] = e
    end
    e.count = (e.count or 0) + 1
    e.last = Now()
end

function T.Error(addon, where, msg)
    local ok = pcall(Record, addon, where, msg, type(debugstack) == "function" and debugstack(2, 6, 0) or nil)
    return ok
end

-- ein gemeinsamer Fehler-Abgriff für alle Addons; ruft danach den bisherigen Handler (BugSack usw.)
local function InstallHook()
    if _G.GoldSentinelTestHooked or type(geterrorhandler) ~= "function" or type(seterrorhandler) ~= "function" then return end
    _G.GoldSentinelTestHooked = true
    local prev = geterrorhandler()
    seterrorhandler(function(msg, ...)
        pcall(function()
            local m = Str(msg) or ""
            for addon in pairs(_G.GoldSentinelTest.registry) do
                if m:find("AddOns[\\/]" .. addon:gsub("%p", "%%%0") .. "[\\/_]") then
                    Record(addon, "Lua", m, type(debugstack) == "function" and debugstack(3, 6, 0) or nil)
                    break
                end
            end
        end)
        if prev then return prev(msg, ...) end
    end)
end

-- beim Ausloggen / /reload: neue Fehler als eigener Bericht ablegen
local function Flush()
    for addon, reg in pairs(T.registry) do
        local s = Store(reg.db)
        if s and next(s.errors) then
            local rep = { f = 1, id = NewId(addon), kind = "fehler", addon = addon, version = reg.version,
                          time = Now(), env = Env(), errors = T.ErrorList(s) }
            if Save(reg.db, rep) then s.errors, s.lastFlush = {}, Now() end
        end
    end
end
T.Flush = Flush

-- BugGrabber (BugSack) übernimmt den Fehler-Handler selbst und lässt andere nicht dazwischen: dort mithören
local function InstallBugGrabber()
    local BG = _G.BugGrabber
    if _G.GoldSentinelTestBG or type(BG) ~= "table" or type(BG.RegisterCallback) ~= "function" then return end
    _G.GoldSentinelTestBG = {}
    BG.RegisterCallback(_G.GoldSentinelTestBG, "BugGrabber_BugGrabbed", function(_, err)
        pcall(function()
            local m = Str(type(err) == "table" and err.message or err) or ""
            for addon in pairs(_G.GoldSentinelTest.registry) do
                if m:find("AddOns[\\/]" .. addon:gsub("%p", "%%%0") .. "[\\/_]") then
                    Record(addon, "Lua", m, type(err) == "table" and err.stack or nil)
                    break
                end
            end
        end)
    end)
end

local function OnEvent(_, event, a, b)
    local GT = _G.GoldSentinelTest
    if event == "PLAYER_LOGOUT" then
        pcall(GT.Flush)
    elseif event == "ADDON_ACTION_BLOCKED" or event == "ADDON_ACTION_FORBIDDEN" then
        -- geschützte Aktion im Kampf / Taint: für Forever besonders wichtig
        if type(a) == "string" and not IsSecret(a) and GT.registry[a] then
            pcall(GT.Error, a, event, Str(b) or "?")
        end
    end
end

function T.TrackErrors(addon, version, db)
    if type(addon) ~= "string" or type(db) ~= "table" then return false end
    T.registry[addon] = { version = Str(version), db = db }
    Store(db)
    pcall(InstallHook)
    pcall(InstallBugGrabber)
    if not _G.GoldSentinelTestFrame and type(CreateFrame) == "function" then
        local f = CreateFrame("Frame")
        _G.GoldSentinelTestFrame = f
        for _, ev in ipairs({ "PLAYER_LOGOUT", "ADDON_ACTION_BLOCKED", "ADDON_ACTION_FORBIDDEN" }) do
            pcall(f.RegisterEvent, f, ev)
        end
        f:SetScript("OnEvent", OnEvent)
    end
    return true
end

-- Anzahl offener Berichte (für die Anzeige im Addon)
function T.Pending(db)
    local s = Store(db)
    return s and #s.reports or 0
end
