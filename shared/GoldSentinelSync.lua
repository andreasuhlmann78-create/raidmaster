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
--   ep:Send("text")                      -- an Gilde und Gruppe (was es gerade gibt)
--   ep:Send("text", { scope = "guild" }) -- nur Gilde ("group" = nur Gruppe/Raid)
--   ep:Send("text", { target = name })   -- an einen Spieler (WHISPER)
--   ep:Peers(3600)                       -- Mitspieler mit diesem Addon, die sich in der letzten Stunde gemeldet haben
--   ep:Stats()                           -- Zaehler: sent, received, dropped (Tabelle mit Gruenden)
--   Sync.Ping("MeinAddon", function(r) ... end)   -- Test: wer antwortet? r = { guild = n, group = n, total = n }
--   Sync.DiagLines()                     -- Zeilen fuer das Diagnose-Protokoll (ohne Spielernamen)
--   Sync.MAX_PAYLOAD                     -- so viele Zeichen darf eine Nachricht haben (laengere selbst teilen)
--
-- Nachrichten von alten Versionen eines Addons (ohne Kopf dieser Datei) werden weiter zugestellt (sender wie gemeldet).
-- Alles laeuft ueber S.api (Testroutinen ersetzen nur diese Tabelle, nie Blizzard-Funktionen).
--
-- Version 1: erste Fassung (9. November 2026)

local VERSION = 1

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

if type(existing) == "table" then
    -- aeltere Fassung uebernehmen: Anmeldungen, Mitspieler, Zaehler; ihren Frame stilllegen
    S.sid = existing.sid
    S.endpoints = existing.endpoints or S.endpoints
    S.byAddon = existing.byAddon or S.byAddon
    S.peers = existing.peers or S.peers
    S.queue = existing.queue or S.queue
    S.stats = existing.stats or S.stats
    if existing.frame then
        pcall(existing.frame.UnregisterAllEvents, existing.frame)
        pcall(existing.frame.SetScript, existing.frame, "OnUpdate", nil)
        pcall(existing.frame.SetScript, existing.frame, "OnEvent", nil)
    end
end
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
    if not q then return false end
    S.lastSend = now
    if S.api.send(q.prefix, q.msg, q.dist, q.target) then
        S.stats.sent = S.stats.sent + 1
        if q.ep then q.ep.stats.sent = q.ep.stats.sent + 1 end
    else
        Drop("sendfail", q.ep)
    end
    return true
end

local function Header()
    S.counter = S.counter + 1
    return "#S1:" .. S.sid .. ":" .. Enc(S.counter) .. ":"
end

local function SendRaw(prefix, body, opts, ep)
    local paths = S.Paths(opts)
    if #paths == 0 then
        Drop("nopath", ep)
        return 0
    end
    local msg = Header() .. body           -- derselbe Kopf auf allen Wegen -> Empfaenger erkennen Dubletten
    for _, p in ipairs(paths) do Enqueue(prefix, msg, p[1], p[2], ep) end
    return #paths
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
    return SendRaw(S.CTRL, "H:" .. AddonList(), nil, nil)
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
        S.peers[sid] = { t = S.api.now(), addons = ParseAddons(rest) }
        -- neuer Mitspieler: mit eigenem Lebenszeichen antworten (Antworten hoechstens alle 30 Sekunden)
        if not known and S.api.now() - (S.lastReply or -100) > 30 then
            S.lastReply = S.api.now()
            S.Hello()
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
    if sid then
        if sid == S.sid then return end                      -- eigene Nachricht (Gilde/Gruppe senden zurueck)
        if not Remember(sid .. ":" .. n .. ":" .. prefix) then Drop("duplicate", ep); return end
        local peer = S.peers[sid]
        if peer then peer.t = S.api.now() end
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
    local dr = {}
    for k, v in pairs(S.stats.dropped) do dr[#dr + 1] = k .. " " .. v end
    table.sort(dr)
    return {
        string.format("SYNC GoldSentinelSync %d · Wege: %s · Mitspieler (1 Std.): %s", S.VERSION,
            #paths > 0 and table.concat(paths, "+") or "keiner", #per > 0 and table.concat(per, ", ") or "-"),
        string.format("SYNC gesendet %d · empfangen %d · verworfen: %s · Warteschlange %d · Kanal verweigert %d",
            S.stats.sent, S.stats.received, #dr > 0 and table.concat(dr, ", ") or "0", #S.queue, S.stats.channelRefused),
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
    S.Pump()
    FinishPings(false)
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
    f:SetScript("OnEvent", function(_, event, a1, a2, a3, a4)
        local s = _G.GoldSentinelSync
        if event == "CHAT_MSG_ADDON" then pcall(s.OnAddonMessage, a1, a2, a3, a4)
        elseif event == "CHAT_MSG_CHANNEL_NOTICE" then pcall(s.OnChannelNotice, a1) end
    end)
    local acc = 0
    f:SetScript("OnUpdate", function(_, dt)
        acc = acc + (dt or 0)
        if acc < 0.1 then return end
        acc = 0
        pcall(_G.GoldSentinelSync.Tick)
    end)
end
