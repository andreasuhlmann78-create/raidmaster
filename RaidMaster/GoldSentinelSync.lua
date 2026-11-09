-- GoldSentinelSync - gemeinsame Addon-Kommunikation fuer alle Addons von GoldSentinel
-- Copyright (C) 2026 GoldSentinel
--
-- Diese Datei UNVERAENDERT in jedes Addon kopieren, das Daten mit anderen Spielern austauscht, und in der .toc nach
-- GoldSentinelGame.lua und VOR den eigenen Dateien eintragen. Mehrere Addons duerfen sie gleichzeitig mitbringen:
-- die neueste Version gewinnt und uebernimmt alle Anmeldungen der aelteren.
--
-- Warum? (shared/wissen/kommunikation-forever.md im raidmaster-Repo)
--   - In WoW Forever kommen Addon-Nachrichten ueber EIGENE Chat-Kanaele nicht an (Server: NOT_ALLOWED_IN_CHANNEL),
--     obwohl SendAddonMessage 0 zurueckgibt. Eigene Kanaele belegen ausserdem knappe Kanalplaetze (max. 10).
--   - GUILD, PARTY/RAID und WHISPER gehen in ALLEN Spielversionen (Era, TBC/Anniversary, Mists, Retail, Forever).
--   Darum sendet diese Datei nie ueber einen eigenen Kanal und tritt keinem bei.
--
-- Benutzung im Addon:
--   local Sync = GoldSentinelSync
--   local ep = Sync.Register("MeinAddon", "MEINPRF1", "1.2.3")      -- Addon-Name, Nachrichten-Kennung (<= 16 Zeichen), Version
--   ep:OnMessage(function(msg, sender, dist) ... end)                 -- sender = Name oder nil (geschuetzt/unbekannt)
--   ep:Send("text")                      -- an Gilde, Gruppe und das Fluester-Netz (was es gerade gibt)
--   ep:Send("text", { net = false })     -- nur Gilde und Gruppe, nicht ins Netz
--   ep:Send("text", { scope = "guild" }) -- nur Gilde ("group" = nur Gruppe/Raid)
--   ep:Send("text", { target = name })   -- an einen Spieler (WHISPER)
--   ep:Peers(3600)                       -- Mitspieler mit diesem Addon, die sich in der letzten Stunde gemeldet haben
--   ep:Stats()                           -- Zaehler: sent, received, dropped (Tabelle mit Gruenden)
--   Sync.Ping("MeinAddon", function(r) ... end)   -- Test: wer antwortet? r = { guild = n, group = n, total = n }
--   Sync.DiagLines()                     -- Zeilen fuer das Diagnose-Protokoll (ohne Spielernamen)
--   Sync.MAX_PAYLOAD                     -- so viele Zeichen darf eine Nachricht haben (laengere selbst teilen)
--   ep:UseStorage(MeinAddonDB)           -- bekannte Mitspieler des Netzes ueber /reload merken (in MeinAddonDB.gsSync;
--                                           nur Namen und Zeiten, nur lokal; das erste Addon, das es anbietet, speichert)
--
-- Fluester-Netz (Version 2): Eigene Kanaele gehen in Forever nicht, darum erreicht der Sync Spieler ausserhalb von
-- Gilde und Gruppe per Fluestern. Jeder Client merkt sich, wer GoldSentinelSync 2 hat (aus Gilde, Gruppe, Fluestern
-- und aus den Listen anderer Clients), schickt eine Nachricht an wenige dieser Spieler, und die geben sie weiter (und in
-- ihre Gilde/Gruppe). Gedrosselt, mit Dublettenschutz und Weitergabe-Zaehler; Offline-Spieler werden pausiert und die
-- Meldung "kein Spieler ... online" ausgeblendet. Gemessen am 9.11.2026: shared/wissen/kommunikation-forever.md.
--
-- Nachrichten von alten Versionen eines Addons (ohne Kopf dieser Datei) werden weiter zugestellt (sender wie gemeldet).
-- Alles laeuft ueber S.api (Testroutinen ersetzen nur diese Tabelle, nie Blizzard-Funktionen).
--
-- Version 1: erste Fassung (9. November 2026)
-- Version 2: Fluester-Netz; Zaehler und Dubletten bei der Uebernahme mitnehmen (9. November 2026)

local VERSION = 2

local existing = _G.GoldSentinelSync
if type(existing) == "table" and (tonumber(existing.VERSION) or 0) >= VERSION then return end

local S = {}
S.VERSION = VERSION
S.MAX_PAYLOAD = 230          -- 255 minus Kopf
S.INTERVAL = 0.2             -- Sekunden zwischen zwei gesendeten Nachrichten (alle Addons zusammen)
S.QUEUE_MAX = 300            -- volle Warteschlange: aelteste Nachricht faellt weg (gezaehlt)
S.HELLO_EVERY = 900          -- Sekunden zwischen zwei eigenen Lebenszeichen
S.PING_WAIT = 5              -- Sekunden, die Sync.Ping auf Antworten wartet
S.CTRL = "GSSYNC1"           -- eigene Kennung fuer Lebenszeichen und Ping
S.NET = true                 -- Fluester-Netz an (Addons koennen es mit Sync.NET = false fuer alle abschalten)
S.NET_FANOUT = 3             -- so viele Netz-Mitspieler bekommen eine Nachricht von einem Client
S.NET_TTL = 2                -- so oft wird eine Netz-Nachricht weitergegeben (3 + 9 + 27 Clients)
S.NET_PER_MIN = 40           -- hoechstens so viele Netz-Fluesternachrichten pro Minute (je Client)
S.NET_QUEUE_MAX = 120        -- volle Netz-Warteschlange: aelteste faellt weg (gezaehlt)
S.GOSSIP_EVERY = 600         -- Sekunden zwischen zwei Listen bekannter Mitspieler
S.GOSSIP_NAMES = 8           -- hoechstens so viele Namen je Liste
S.OFFLINE_PAUSE = 900        -- Sekunden Pause fuer einen Spieler, der offline war
S.BOOK_MAX = 400             -- hoechstens so viele bekannte Mitspieler
S.BOOK_DAYS = 30             -- nach so vielen Tagen ohne Lebenszeichen vergessen

---------------------------------------------------------------------------
-- Schnittstelle zum Spiel (nur ueber diese Tabelle; Tests ersetzen Eintraege hier)
---------------------------------------------------------------------------
local function G() return _G.GoldSentinelGame end

local function AnySecret(...)
    local g = G()
    if g and g.AnySecret then return g.AnySecret(...) end
    local f = _G.issecretvalue
    if not f then return false end
    for i = 1, select("#", ...) do
        local ok, r = pcall(f, (select(i, ...)))
        if ok and r then return true end
    end
    return false
end

S.api = {
    send = function(prefix, msg, dist, target)
        local CI = _G.C_ChatInfo
        local f = (CI and CI.SendAddonMessage) or _G.SendAddonMessage
        if not f then return false end
        local ok, r = pcall(f, prefix, msg, dist, target)
        return ok and r ~= false
    end,
    register = function(prefix)
        local CI = _G.C_ChatInfo
        local f = (CI and CI.RegisterAddonMessagePrefix) or _G.RegisterAddonMessagePrefix
        if f then pcall(f, prefix) end
    end,
    inGuild = function() local f = _G.IsInGuild; return f and f() and true or false end,
    inRaid = function() local f = _G.IsInRaid; return f and f() and true or false end,
    inGroup = function()
        local f = _G.IsInGroup
        if f then return f() and true or false end
        local n = _G.GetNumPartyMembers
        return n and n() > 0 or false
    end,
    now = function() return (_G.GetTime and _G.GetTime()) or 0 end,
    time = function() return (_G.time and _G.time()) or 0 end,
    inCombat = function() local f = _G.InCombatLockdown; return f and f() and true or false end,
    notFound = function() return _G.ERR_CHAT_PLAYER_NOT_FOUND_S end,
    random = function(n) return math.random(n) end,
    playerName = function()
        local f = _G.UnitName
        local n = f and f("player")
        if AnySecret(n) then return nil end
        return n
    end,
}

---------------------------------------------------------------------------
-- Zustand (bei Uebernahme einer aelteren Fassung mitnehmen)
---------------------------------------------------------------------------
local B36 = "0123456789abcdefghijklmnopqrstuvwxyz"
local function Enc(n)
    n = math.floor(tonumber(n) or 0)
    if n <= 0 then return "0" end
    local out = ""
    while n > 0 do
        local r = n % 36
        out = B36:sub(r + 1, r + 1) .. out
        n = math.floor(n / 36)
    end
    return out
end
S.Enc = Enc

local function NewSid()
    local t = {}
    for i = 1, 5 do local r = S.api.random(36); t[i] = B36:sub(r, r) end
    return table.concat(t)
end

S.endpoints = {}             -- [prefix] = ep
S.byAddon = {}               -- [addon]  = ep
S.peers = {}                 -- [sid] = { t = Zeit, addons = { [addon] = version } }
S.queue = {}
S.seen = {}                  -- [sid:n] = true (Dubletten ueber Gilde und Gruppe)
S.seenList = {}
S.counter = 0
S.stats = { sent = 0, received = 0, dropped = {}, channelRefused = 0 }
S.lastSend = -100
S.lastHello = -10000
S.pings = {}
S.book = {}                  -- [Name] = { seen = Zeit (time()), v = Sync-Version, src = guild/group/whisper/net/gossip,
                             --            fail = Offline-Zaehler, pause = bis GetTime(), intro = vorstellen }
S.netQueue = {}
S.netWin = { start = -1000, n = 0 }
S.whispered = {}             -- [Name] = GetTime() des letzten Fluesterns (Offline-Meldung zuordnen)
S.hideUntil = {}             -- [Name] = GetTime(), bis zu der die Offline-Meldung ausgeblendet wird
S.lastGossip = nil

if type(existing) == "table" then
    -- aeltere Fassung uebernehmen: Anmeldungen, Mitspieler, Zaehler; ihren Frame stilllegen
    S.sid = existing.sid
    S.endpoints = existing.endpoints or S.endpoints
    S.byAddon = existing.byAddon or S.byAddon
    S.peers = existing.peers or S.peers
    S.queue = existing.queue or S.queue
    S.stats = existing.stats or S.stats
    S.counter = tonumber(existing.counter) or S.counter     -- sonst gelten neue Nachrichten als Dubletten
    S.seen = existing.seen or S.seen
    S.seenList = existing.seenList or S.seenList
    S.pings = existing.pings or S.pings
    S.book = existing.book or S.book
    S.store = existing.store
    S.netQueue = existing.netQueue or S.netQueue
    S.lastHello = existing.lastHello or S.lastHello
    S.lastReply = existing.lastReply
    if existing.frame then
        pcall(existing.frame.UnregisterAllEvents, existing.frame)
        pcall(existing.frame.SetScript, existing.frame, "OnUpdate", nil)
        pcall(existing.frame.SetScript, existing.frame, "OnEvent", nil)
    end
end
S.stats.net = S.stats.net or {}
for _, k in ipairs({ "sent", "relayed", "offline", "learned", "gossip" }) do S.stats.net[k] = S.stats.net[k] or 0 end
_G.GoldSentinelSync = S

local function Drop(reason, ep)
    S.stats.dropped[reason] = (S.stats.dropped[reason] or 0) + 1
    if ep then ep.stats.dropped[reason] = (ep.stats.dropped[reason] or 0) + 1 end
end
S.Drop = Drop

---------------------------------------------------------------------------
-- Senden
---------------------------------------------------------------------------
-- Wege fuer einen Umfang: Liste von { dist, target }
function S.Paths(opts)
    opts = opts or {}
    if opts.target then return { { "WHISPER", opts.target } } end
    local scope = opts.scope or "all"
    local out = {}
    if (scope == "all" or scope == "guild") and S.api.inGuild() then out[#out + 1] = { "GUILD" } end
    if scope == "all" or scope == "group" then
        if S.api.inRaid() then out[#out + 1] = { "RAID" }
        elseif S.api.inGroup() then out[#out + 1] = { "PARTY" } end
    end
    return out
end

local function Enqueue(prefix, msg, dist, target, ep)
    if #S.queue >= S.QUEUE_MAX then
        local old = table.remove(S.queue, 1)
        Drop("queue", old and old.ep)
    end
    S.queue[#S.queue + 1] = { prefix = prefix, msg = msg, dist = dist, target = target, ep = ep }
end

-- eine Nachricht aus der Warteschlange senden (vom Frame im Takt S.INTERVAL; Tests rufen es direkt)
function S.Pump(force)
    local now = S.api.now()
    if not force and now - S.lastSend < S.INTERVAL then return false end
    local q = table.remove(S.queue, 1)
    if not q then
        -- Netz nur, wenn Gilde/Gruppe nichts zu senden haben; gedrosselt je Minute; nicht im Kampf
        if #S.netQueue == 0 or S.api.inCombat() then return false end
        if now - S.netWin.start >= 60 then S.netWin.start, S.netWin.n = now, 0 end
        if S.netWin.n >= S.NET_PER_MIN then return false end
        q = table.remove(S.netQueue, 1)
        S.netWin.n = S.netWin.n + 1
        S.stats.net.sent = S.stats.net.sent + 1
    end
    S.lastSend = now
    if q.dist == "WHISPER" and q.target then S.whispered[q.target] = now end
    if S.api.send(q.prefix, q.msg, q.dist, q.target) then
        S.stats.sent = S.stats.sent + 1
        if q.ep then q.ep.stats.sent = q.ep.stats.sent + 1 end
    else
        Drop("sendfail", q.ep)
    end
    return true
end

local function NextId()
    S.counter = S.counter + 1
    return Enc(S.counter)
end

local function Header()
    return "#S1:" .. S.sid .. ":" .. NextId() .. ":"
end

---------------------------------------------------------------------------
-- Fluester-Netz: bekannte Mitspieler
---------------------------------------------------------------------------
local function IsMe(name)
    local me = S.api.playerName()
    return me ~= nil and (name == me or name:match("^([^%-]+)") == me)
end

local function TrimBook()
    local now, n = S.api.time(), 0
    local list = {}
    for name, e in pairs(S.book) do
        if (e.fail or 0) >= 5 or (now > 0 and (e.seen or 0) < now - S.BOOK_DAYS * 86400) then
            S.book[name] = nil
        else
            n = n + 1
            list[#list + 1] = name
        end
    end
    if n > S.BOOK_MAX then
        table.sort(list, function(a, b) return (S.book[a].seen or 0) < (S.book[b].seen or 0) end)
        for i = 1, n - S.BOOK_MAX do S.book[list[i]] = nil end
    end
end
S.TrimBook = TrimBook

-- Spieler merken. src: guild/group/whisper/net/gossip; v: Sync-Version, falls bekannt
local function Learn(name, src, v)
    if type(name) ~= "string" or name == "" or AnySecret(name) or IsMe(name) then return nil end
    if #name > 60 or name:find("[,:|]") then return nil end
    local e = S.book[name]
    if not e then
        e = { seen = 0, v = 0, fail = 0, pause = 0, src = src }
        S.book[name] = e
        S.stats.net.learned = S.stats.net.learned + 1
        if src == "gossip" then e.intro = true end
    end
    if src ~= "gossip" then
        e.seen = S.api.time()
        e.fail = 0
        e.pause = 0
        e.intro = nil
        if src == "guild" or e.src == "gossip" or not e.src then e.src = src end
    elseif (e.seen or 0) == 0 then
        e.seen = S.api.time()
    end
    if v and v > (e.v or 0) then e.v = v end
    return e
end
S.Learn = Learn

-- bis zu count Ziele fuer das Netz (Sync 2, nicht pausiert, nicht ausgeschlossen; Gildenmitglieder nur ohne Gilde)
local function NetTargets(count, exclude, includeGuild)
    local now = S.api.now()
    local inGuild = S.api.inGuild()
    local cand = {}
    for name, e in pairs(S.book) do
        if (e.v or 0) >= 2 and (e.pause or 0) <= now and name ~= exclude
            and (includeGuild or not inGuild or e.src ~= "guild") then
            cand[#cand + 1] = name
        end
    end
    table.sort(cand)                                   -- feste Reihenfolge, dann zufaellig ziehen
    local out = {}
    while #out < count and #cand > 0 do
        out[#out + 1] = table.remove(cand, S.api.random(#cand))
    end
    return out
end
S.NetTargets = NetTargets

local function NetEnqueue(prefix, msg, target, ep)
    if #S.netQueue >= S.NET_QUEUE_MAX then
        local old = table.remove(S.netQueue, 1)
        Drop("netqueue", old and old.ep)
    end
    S.netQueue[#S.netQueue + 1] = { prefix = prefix, msg = msg, dist = "WHISPER", target = target, ep = ep }
end

-- Netz-Nachricht an bis zu NET_FANOUT Mitspieler: "#S2:<sid>:<n>:<ttl>:<text>"
local function NetSend(prefix, sid, n, ttl, body, exclude, ep)
    if not S.NET then return 0 end
    local targets = NetTargets(S.NET_FANOUT, exclude, false)
    local msg = "#S2:" .. sid .. ":" .. n .. ":" .. ttl .. ":" .. body
    for _, t in ipairs(targets) do NetEnqueue(prefix, msg, t, ep) end
    return #targets
end
S.NetSend = NetSend

-- Steuernachricht direkt an einen Netz-Mitspieler (Weitergabe 0)
local function NetCtrl(target, body)
    NetEnqueue(S.CTRL, "#S2:" .. S.sid .. ":" .. NextId() .. ":0:" .. body, target, nil)
end
S.NetCtrl = NetCtrl

local function SendRaw(prefix, body, opts, ep)
    opts = opts or {}
    local paths = S.Paths(opts)
    local n = NextId()
    local msg = "#S1:" .. S.sid .. ":" .. n .. ":" .. body   -- derselbe Kopf auf allen Wegen -> Dubletten erkennbar
    for _, p in ipairs(paths) do Enqueue(prefix, msg, p[1], p[2], ep) end
    local net = 0
    if ep and not opts.target and (opts.scope or "all") == "all" and opts.net ~= false then
        net = NetSend(prefix, S.sid, n, S.NET_TTL, body, nil, ep)
    end
    if #paths + net == 0 then
        Drop("nopath", ep)
        return 0
    end
    return #paths + net
end

---------------------------------------------------------------------------
-- Anmeldung eines Addons
---------------------------------------------------------------------------
local EP = {}
EP.__index = EP
S.EP = EP

function EP:Send(msg, opts)
    local s = _G.GoldSentinelSync
    if type(msg) ~= "string" then return false, "kein Text" end
    if #msg > s.MAX_PAYLOAD then s.Drop("toolong", self); return false, "zu lang" end
    local n = s.SendRaw(self.prefix, msg, opts, self)
    return n > 0, n
end

function EP:OnMessage(fn) self.handlers[#self.handlers + 1] = fn end

function EP:Peers(seconds)
    local s = _G.GoldSentinelSync
    local limit = s.api.now() - (seconds or 3600)
    local n = 0
    for _, p in pairs(s.peers) do
        if p.t >= limit and p.addons and p.addons[self.addon] then n = n + 1 end
    end
    return n
end

function EP:Stats() return self.stats end

function EP:UseStorage(db)
    if type(db) ~= "table" then return end
    db.gsSync = type(db.gsSync) == "table" and db.gsSync or {}
    _G.GoldSentinelSync.UseStorage(db.gsSync)
end

-- bekannte Mitspieler in einer SavedVariables-Tabelle halten (das erste Addon, das eine anbietet; weitere werden
-- eingelesen)
function S.UseStorage(tbl)
    if type(tbl) ~= "table" or tbl == S.store then return end
    local book = type(tbl.book) == "table" and tbl.book or {}
    for name, e in pairs(book) do
        if type(name) == "string" and type(e) == "table" then
            local cur = S.book[name]
            if not cur or (tonumber(e.seen) or 0) > (cur.seen or 0) then
                S.book[name] = { seen = tonumber(e.seen) or 0, v = tonumber(e.v) or 0, src = e.src,
                                 fail = tonumber(e.fail) or 0, pause = 0, intro = cur and cur.intro }
            end
        end
    end
    if not S.store then
        S.store = tbl
        tbl.book = S.book
    end
    TrimBook()
end

S.SendRaw = SendRaw

-- bei Uebernahme: vorhandene Anmeldungen auf die neuen Methoden umstellen
for _, ep in pairs(S.endpoints) do setmetatable(ep, EP) end

function S.Register(addon, prefix, version)
    assert(type(addon) == "string" and type(prefix) == "string" and #prefix <= 16, "GoldSentinelSync.Register(addon, prefix<=16, version)")
    local ep = S.endpoints[prefix]
    if not ep then
        ep = setmetatable({ addon = addon, prefix = prefix, handlers = {}, stats = { sent = 0, received = 0, dropped = {} } }, EP)
        S.endpoints[prefix] = ep
        S.api.register(prefix)
    end
    ep.version = tostring(version or "?")
    S.byAddon[addon] = ep
    S.helloDue = true
    return ep
end

---------------------------------------------------------------------------
-- Lebenszeichen und Ping
---------------------------------------------------------------------------
local function AddonList()
    local t = {}
    for addon, ep in pairs(S.byAddon) do t[#t + 1] = addon .. "=" .. (ep.version or "?") end
    table.sort(t)
    return table.concat(t, ",")
end

local function ParseAddons(text)
    local out = {}
    for item in tostring(text or ""):gmatch("[^,]+") do
        local a, v = item:match("^([^=]+)=(.*)$")
        if a then out[a] = v end
    end
    return out
end

function S.Hello()
    S.lastHello = S.api.now()
    S.helloDue = false
    if next(S.byAddon) == nil then return 0 end
    return SendRaw(S.CTRL, "H:" .. AddonList() .. ",~sync=" .. S.VERSION, nil, nil)
end

-- Test: wer mit diesem Addon antwortet? cb(r) nach S.PING_WAIT Sekunden; r = { guild, group, whisper, total, addons }
function S.Ping(addon, cb)
    local nonce = Enc(S.api.random(1000000))
    S.pings[nonce] = { addon = addon, cb = cb, t = S.api.now(), r = { guild = 0, group = 0, whisper = 0, total = 0 }, from = {} }
    local n = SendRaw(S.CTRL, "P:" .. nonce .. ":" .. tostring(addon or ""), nil, nil)
    if n == 0 then
        S.pings[nonce] = nil
        if cb then cb({ guild = 0, group = 0, whisper = 0, total = 0, nopath = true }) end
    end
    return n
end

local function FinishPings(force)
    local now = S.api.now()
    for nonce, p in pairs(S.pings) do
        if force or now - p.t >= S.PING_WAIT then
            S.pings[nonce] = nil
            if p.cb then pcall(p.cb, p.r) end
        end
    end
end
S.FinishPings = FinishPings

---------------------------------------------------------------------------
-- Empfangen
---------------------------------------------------------------------------
local function Remember(key)
    if S.seen[key] then return false end
    S.seen[key] = true
    S.seenList[#S.seenList + 1] = key
    if #S.seenList > 400 then S.seen[table.remove(S.seenList, 1)] = nil end
    return true
end

local function DistGroup(dist)
    if dist == "GUILD" or dist == "OFFICER" then return "guild" end
    if dist == "PARTY" or dist == "RAID" or dist == "INSTANCE_CHAT" then return "group" end
    if dist == "WHISPER" then return "whisper" end
    return "other"
end

local function HandleControl(sid, body, dist, sender)
    local kind, rest = body:match("^(%a):(.*)$")
    if kind == "H" then
        local known = S.peers[sid]
        local addons = ParseAddons(rest)
        S.peers[sid] = { t = S.api.now(), addons = addons }
        local v = tonumber(addons["~sync"])
        local e = sender and Learn(sender, DistGroup(dist) == "whisper" and "whisper" or DistGroup(dist), v)
        if dist == "WHISPER" then
            -- Vorstellung per Fluestern: einmal je 10 Minuten und Spieler zurueckgruessen
            if e and S.NET and (e.helloBack or -1000) < S.api.now() - 600 and (v or 0) >= 2 then
                e.helloBack = S.api.now()
                NetCtrl(sender, "H:" .. AddonList() .. ",~sync=" .. S.VERSION)
            end
        elseif not known and S.api.now() - (S.lastReply or -100) > 30 then
            -- neuer Mitspieler: mit eigenem Lebenszeichen antworten (Antworten hoechstens alle 30 Sekunden)
            S.lastReply = S.api.now()
            S.Hello()
        end
    elseif kind == "B" then
        -- Liste bekannter Netz-Mitspieler eines anderen Clients (nur Sync 2)
        local n = 0
        for name in rest:gmatch("[^,]+") do
            if n >= S.GOSSIP_NAMES then break end
            n = n + 1
            Learn(name, "gossip", 2)
        end
    elseif kind == "P" then
        local nonce, addon = rest:match("^(%w+):(.*)$")
        if nonce and (addon == "" or S.byAddon[addon]) then
            local peer = S.peers[sid]
            if peer then peer.t = S.api.now() end
            local opts = (dist == "WHISPER" and sender) and { target = sender }
                or { scope = (DistGroup(dist) == "guild") and "guild" or "group" }
            SendRaw(S.CTRL, "O:" .. nonce .. ":" .. AddonList(), opts, nil)
        end
    elseif kind == "O" then
        local nonce, list = rest:match("^(%w+):(.*)$")
        local p = nonce and S.pings[nonce]
        if p and not p.from[sid] then
            local addons = ParseAddons(list)
            if p.addon == nil or p.addon == "" or addons[p.addon] then
                p.from[sid] = true
                local g = DistGroup(dist)
                p.r[g] = (p.r[g] or 0) + 1
                p.r.total = p.r.total + 1
            end
            S.peers[sid] = { t = S.api.now(), addons = addons }
        end
    end
end

function S.OnAddonMessage(prefix, msg, dist, sender)
    if AnySecret(prefix, msg, dist) then Drop("secret"); return end
    if type(prefix) ~= "string" or type(msg) ~= "string" then return end
    local ep = S.endpoints[prefix]
    if prefix ~= S.CTRL and not ep then return end
    if AnySecret(sender) then sender = nil end
    local sid, n, body = msg:match("^#S1:(%w+):(%w+):(.*)$")
    local ttl
    if not sid then
        sid, n, ttl, body = msg:match("^#S2:(%w+):(%w+):(%d):(.*)$")
        ttl = tonumber(ttl)
    end
    if sid then
        if sid == S.sid then return end                      -- eigene Nachricht (Gilde/Gruppe senden zurueck)
        if sender and not IsMe(sender) then
            local src = ttl and "net" or DistGroup(dist)
            Learn(sender, src == "other" and "whisper" or src, ttl and 2 or nil)
        end
        if not Remember(sid .. ":" .. n .. ":" .. prefix) then Drop("duplicate", ep); return end
        local peer = S.peers[sid]
        if peer then peer.t = S.api.now() end
        -- Netz-Nachricht eines Addons: in die eigene Gilde/Gruppe bringen und weitergeben
        if ttl and prefix ~= S.CTRL and S.NET then
            local fwd = "#S1:" .. sid .. ":" .. n .. ":" .. body
            for _, p in ipairs(S.Paths()) do Enqueue(prefix, fwd, p[1], p[2], ep) end
            if ttl > 0 then NetSend(prefix, sid, n, ttl - 1, body, sender, ep) end
            S.stats.net.relayed = S.stats.net.relayed + 1
        end
    else
        -- alte Version eines Addons ohne Kopf: unveraendert zustellen; eigene Nachrichten am Namen erkennen
        local me = S.api.playerName()
        if sender and me and (sender == me or sender:match("^([^%-]+)") == me) then return end
        body = msg
    end
    if prefix == S.CTRL then
        if sid then HandleControl(sid, body, dist, sender) end
        return
    end
    S.stats.received = S.stats.received + 1
    ep.stats.received = ep.stats.received + 1
    if sid then
        local peer = S.peers[sid]
        if not peer then S.peers[sid] = { t = S.api.now(), addons = { [ep.addon] = "?" } }
        elseif not peer.addons[ep.addon] then peer.addons[ep.addon] = "?" end
    end
    for _, fn in ipairs(ep.handlers) do
        local ok = pcall(fn, body, sender, dist)
        if not ok then Drop("handler", ep) end
    end
end

-- "Momentan ist kein Spieler mit dem Namen '%s' online." nach eigenem Fluestern: Spieler pausieren, Meldung ausblenden
local function NotFoundName(text)
    if type(text) ~= "string" or AnySecret(text) then return nil end
    local fmt = S.api.notFound()
    if type(fmt) ~= "string" or not fmt:find("%%s") then fmt = "No player named '%s' is currently playing." end
    if fmt ~= S.nfFmt then
        S.nfFmt = fmt
        local a, b = fmt:find("%s", 1, true)
        local function esc(x) return (x:gsub("([%^%$%(%)%%%.%[%]%*%+%-%?])", "%%%1")) end
        S.nfPat = "^" .. esc(fmt:sub(1, a - 1)) .. "(.+)" .. esc(fmt:sub(b + 1)) .. "$"
    end
    return text:match(S.nfPat)
end

-- true = diese Meldung gehoert zum Netz und wird ausgeblendet
function S.OnSystemMessage(text)
    local name = NotFoundName(text)
    if not name then return false end
    local now = S.api.now()
    local t = S.whispered[name]
    if t and now - t <= 5 then
        S.whispered[name] = nil
        S.hideUntil[name] = now + 2
        local e = S.book[name]
        if e then
            e.fail = (e.fail or 0) + 1
            e.pause = now + S.OFFLINE_PAUSE
        end
        S.stats.net.offline = S.stats.net.offline + 1
        -- wartende Netz-Nachrichten an diesen Spieler fallen weg
        for i = #S.netQueue, 1, -1 do
            if S.netQueue[i].target == name then table.remove(S.netQueue, i) end
        end
        return true
    end
    return S.hideUntil[name] ~= nil and now <= S.hideUntil[name]
end

-- Kanal-Hinweis des Servers (eigene alte Kanaele der Addons): "nicht erlaubt" zaehlen
function S.OnChannelNotice(text)
    if AnySecret(text) then return end
    if text == "NOT_ALLOWED_IN_CHANNEL" then S.stats.channelRefused = S.stats.channelRefused + 1 end
end

---------------------------------------------------------------------------
-- Diagnose (ohne Spielernamen)
---------------------------------------------------------------------------
function S.DiagLines()
    local paths = {}
    for _, p in ipairs(S.Paths()) do paths[#paths + 1] = p[1] end
    local per = {}
    for addon, ep in pairs(S.byAddon) do per[#per + 1] = addon .. " " .. ep:Peers(3600) end
    table.sort(per)
    local known, v2, paused, now = 0, 0, 0, S.api.now()
    for _, e in pairs(S.book) do
        known = known + 1
        if (e.v or 0) >= 2 then v2 = v2 + 1 end
        if (e.pause or 0) > now then paused = paused + 1 end
    end
    local dr = {}
    for k, v in pairs(S.stats.dropped) do dr[#dr + 1] = k .. " " .. v end
    table.sort(dr)
    return {
        string.format("SYNC GoldSentinelSync %d · Wege: %s · Mitspieler (1 Std.): %s", S.VERSION,
            #paths > 0 and table.concat(paths, "+") or "keiner", #per > 0 and table.concat(per, ", ") or "-"),
        string.format("SYNC gesendet %d · empfangen %d · verworfen: %s · Warteschlange %d · Kanal verweigert %d",
            S.stats.sent, S.stats.received, #dr > 0 and table.concat(dr, ", ") or "0", #S.queue, S.stats.channelRefused),
        string.format("NETZ %s · bekannt %d (mit Sync 2: %d, pausiert %d) · gesendet %d · weitergegeben %d · offline %d · " ..
            "Listen %d · Warteschlange %d · gespeichert %s", S.NET and "an" or "aus", known, v2, paused, S.stats.net.sent,
            S.stats.net.relayed, S.stats.net.offline, S.stats.net.gossip, #S.netQueue, S.store and "ja" or "nein"),
    }
end

---------------------------------------------------------------------------
-- Takt und Ereignisse
---------------------------------------------------------------------------
function S.Tick()
    local now = S.api.now()
    if S.helloDue or now - S.lastHello >= S.HELLO_EVERY then
        if now >= (S.helloAt or 0) then S.Hello() end
    end
    if S.NET then S.NetTick(now) end
    S.Pump()
    FinishPings(false)
end

-- Listen austauschen und neue Mitspieler aus Listen vorstellen
function S.NetTick(now)
    S.lastGossip = S.lastGossip or (now - S.GOSSIP_EVERY + 60)      -- erste Liste eine Minute nach dem Laden
    if now - S.lastGossip >= S.GOSSIP_EVERY then
        S.lastGossip = now
        local names = {}
        local limit = S.api.time() - 7 * 86400
        for name, e in pairs(S.book) do
            if (e.v or 0) >= 2 and (e.pause or 0) <= now and (e.seen or 0) >= limit and e.src ~= "gossip" then
                names[#names + 1] = name
            end
        end
        table.sort(names, function(a, b) return (S.book[a].seen or 0) > (S.book[b].seen or 0) end)
        for _, t in ipairs(NetTargets(2, nil, true)) do
            local list, len = {}, 0
            for _, name in ipairs(names) do
                if name ~= t and #list < S.GOSSIP_NAMES and len + #name + 1 <= S.MAX_PAYLOAD - 4 then
                    list[#list + 1] = name
                    len = len + #name + 1
                end
            end
            if #list > 0 then
                NetCtrl(t, "B:" .. table.concat(list, ","))
                S.stats.net.gossip = S.stats.net.gossip + 1
            end
        end
    end
    -- hoechstens 2 Vorstellungen alle 30 Sekunden
    if now - (S.lastIntro or -100) >= 30 and next(S.byAddon) ~= nil then
        S.lastIntro = now
        local n = 0
        for name, e in pairs(S.book) do
            if n >= 2 then break end
            if e.intro and (e.pause or 0) <= now then
                e.intro = nil
                e.helloBack = now
                NetCtrl(name, "H:" .. AddonList() .. ",~sync=" .. S.VERSION)
                n = n + 1
            end
        end
    end
end

S.sid = S.sid or NewSid()
S.helloAt = S.api.now() + 10        -- erstes Lebenszeichen nach dem Laden (Gilde ist oft noch nicht bekannt)
S.api.register(S.CTRL)

local CF = _G.CreateFrame
if CF then
    local f = CF("Frame")
    S.frame = f
    pcall(f.RegisterEvent, f, "CHAT_MSG_ADDON")
    pcall(f.RegisterEvent, f, "CHAT_MSG_CHANNEL_NOTICE")
    pcall(f.RegisterEvent, f, "CHAT_MSG_SYSTEM")
    f:SetScript("OnEvent", function(_, event, a1, a2, a3, a4)
        local s = _G.GoldSentinelSync
        if event == "CHAT_MSG_ADDON" then pcall(s.OnAddonMessage, a1, a2, a3, a4)
        elseif event == "CHAT_MSG_CHANNEL_NOTICE" then pcall(s.OnChannelNotice, a1)
        elseif event == "CHAT_MSG_SYSTEM" and s.OnSystemMessage then pcall(s.OnSystemMessage, a1) end
    end)
    local acc = 0
    f:SetScript("OnUpdate", function(_, dt)
        acc = acc + (dt or 0)
        if acc < 0.1 then return end
        acc = 0
        pcall(_G.GoldSentinelSync.Tick)
    end)
end

-- Offline-Meldungen nach Netz-Fluestern im Chat ausblenden (einmal je Sitzung anmelden; fragt immer die neueste Fassung)
if not _G.GoldSentinelSyncFilter and _G.ChatFrame_AddMessageEventFilter then
    _G.GoldSentinelSyncFilter = true
    pcall(_G.ChatFrame_AddMessageEventFilter, "CHAT_MSG_SYSTEM", function(_, _, msg, ...)
        local s = _G.GoldSentinelSync
        if s and s.OnSystemMessage then
            local ok, hide = pcall(s.OnSystemMessage, msg)
            if ok and hide then return true end
        end
        return false, msg, ...
    end)
end
