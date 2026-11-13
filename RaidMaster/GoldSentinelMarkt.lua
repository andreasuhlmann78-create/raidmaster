-- GoldSentinelMarkt - gemeinsames Marktdaten-Netz fuer alle Addons von GoldSentinel
-- Copyright (C) 2026 GoldSentinel
--
-- Diese Datei UNVERAENDERT in jedes GoldSentinel-Addon kopieren und in der .toc NACH GoldSentinelSync.lua und VOR den
-- eigenen Dateien eintragen. Mehrere Addons duerfen sie gleichzeitig mitbringen: sie laeuft je Client nur EINMAL
-- (die neueste Version gewinnt und uebernimmt Daten und Anmeldungen der aelteren).
--
-- Was sie tut (Anweisung MN, auftraege/*/anweisung-marktdaten-netz.txt im raidmaster-Repo):
--   - Sie LIEST jeden Vollscan MIT, den irgendein Addon (oder der Spieler) im Auktionshaus ausloest
--     (C_AuctionHouse.ReplicateItems -> REPLICATE_ITEM_LIST_UPDATE). Sie ruft ReplicateItems NIE selbst auf
--     (keine Last fuer den Server, keine Drossel fuer andere Addons). Gelesen wird in Portionen (Zeitbudget je Bild),
--     nie im Kampf.
--   - Je Item: tiefster Stueckpreis, Menge, Anzahl Auktionen, Zeit. Zwei Scans derselben Sitzung (10 Min. bis 6 Std.
--     auseinander) ergeben den GEMESSENEN Absatz: Auktionen, die mit langer Restzeit (Stufe 3/4) verschwinden, wurden
--     gekauft oder abgebrochen (vorsichtig gezaehlt: kuerzeste Restzeiten zuerst als "abgelaufen").
--   - KEINE NAMEN: Besitzer, Bieter und Itemnamen werden nie gelesen, nie gespeichert, nie gesendet.
--   - Teilen ueber GoldSentinelSync (Kennung GSMARKT1): Zusammenfassung des eigenen Scans an die Gilde (gedrosselt),
--     Aenderungen ins Fluester-Netz; "Speichern und Weitergeben": nach dem Einloggen fragt der Client die Gilde nach
--     neueren Daten. Nur die eigene Fraktion.
--   - Fremde Werte ueberschreiben nie einen eigenen frischeren Scan, Ausreisser (x3 / :3 zum eigenen Wert) werden
--     verworfen; die Quelle steht in jedem Ergebnis ("eigen" oder "netz").
--   - Keine Abfrage beim Spieler; Standard AN; jedes Addon bietet einen Schalter zum Ausschalten (GSMarkt.SetShare).
--     Ist er in EINEM Addon aus, liest und teilt die Datei nichts.
--
-- Benutzung im Addon:
--   local GM = GoldSentinelMarkt
--   GM.Attach("MeinAddon", MeinAddonDB)        -- beim Laden (ADDON_LOADED); Daten in MeinAddonDB.gsMarkt
--   GM.SetShare("MeinAddon", false)            -- Schalter "Marktdaten teilen" (true/false), bleibt gespeichert
--   GM.IsShareOn()                             -- true/false (alle Schalter zusammen)
--   GM.Get(itemID)                             -- { preis, menge, n, t, quelle = "eigen"/"netz", absatz, abdeckung } oder nil
--                                                 preis = tiefster Stueckpreis (Kupfer), t = time() des Scans,
--                                                 absatz = gemessener Absatz je Tag, vorsichtig: Abgaenge aus langer
--                                                 Restzeit minus neue Auktionen desselben Items (Abbrechen und neu
--                                                 Einstellen zaehlt so nicht als Verkauf); absatzMax = ohne diesen Abzug
--                                                 (nil = noch nicht gemessen),
--                                                 abdeckung = gemessene Stunden
--   GM.DiagLines()                             -- Zeilen fuer Diagnose/Testbericht (ohne Namen)
--   GM.Stats()                                 -- Zaehler (scans, gelesen, gesendet, empfangen, verworfen ...)
--   GM.FeedStart(addon) / GM.Feed(addon, t, n, items, dt) -- Addons mit eigenem Vollscan (AHSentinel) geben ihr
--                                                 Ergebnis weiter, statt dass der Scan zweimal gelesen wird (s. u.)
-- Fuer den Uploader stehen die letzten Scans als Zeilen "GSMARKT1|..." in MeinAddonDB.gsMarkt.export (Liste).
--
-- Alles laeuft ueber M.api (Tests ersetzen nur diese Tabelle, nie Blizzard-Funktionen).
--
-- Version 1: erste Fassung (13. November 2026)
-- Version 2 (13. November 2026, 20 Uhr): ist AHSentinel im Client geladen, liest diese Datei NICHTS selbst (AHSentinel
--   liest seine Vollscans selbst und gibt sie mit Feed weiter – doppeltes Lesen machte das Spiel ruckelig); Lesebudget
--   4 ms; Schalter aus leert die Warteschlange; ganzer Scan an die Gilde hoechstens einmal je Stunde, sonst nur
--   Aenderungen; Sync-Warteschlange wird nur bis 10 Nachrichten gefuellt (Platz fuer die Nachrichten der Addons);
--   Export enthaelt auch ganz verschwundene Items ("id,0,0,0,abgaenge,abgaengeVorsichtig", Befund D-MN7b).

local VERSION = 2

local existing = _G.GoldSentinelMarkt
if type(existing) == "table" and (tonumber(existing.VERSION) or 0) >= VERSION then return end

local M = {}
M.VERSION = VERSION
M.PREFIX = "GSMARKT1"
M.BUDGET_MS = 4              -- Rechenzeit je Bild beim Lesen
M.CHECK_EVERY = 100          -- so oft wird die Zeit innerhalb einer Portion geprueft
M.BURST_GAP = 30             -- Sekunden ohne Ereignis = naechstes Ereignis ist ein neuer Scan
M.READ_DELAY = 2             -- Sekunden nach dem ersten Ereignis bis zum Lesen
M.CMP_MIN, M.CMP_MAX = 600, 6 * 3600   -- Abstand zweier Scans fuer den Absatz-Vergleich
M.ITEMS_PER_MSG = 9          -- Eintraege je Nachricht (Base36, passt in 230 Zeichen)
M.QUEUE_HIGH = 10            -- nur nachschieben, solange die Sync-Warteschlange kuerzer ist
M.NET_MAX = 60               -- hoechstens so viele geaenderte Items ins Netz je Scan
M.NET_CHANGE = 0.05          -- Preis-Aenderung, ab der ein Item als geaendert gilt
M.OUTLIER = 3                -- fremder Preis x3 oder :3 zum eigenen (juenger als 6 Std.) = verworfen
M.MAX_AGE = 7 * 86400        -- aeltere Daten werden nicht angenommen
M.EXPORT_KEEP = 2            -- so viele Scans fuer den Uploader
M.ASK_DELAY = 60             -- Sekunden nach dem Laden bis zur Frage "wer hat Neueres?"
M.FULL_EVERY = 3600          -- ganzer Scan an die Gilde hoechstens so oft (Sekunden), sonst nur Aenderungen
M.OUTBOX_MAX = 1500          -- volle eigene Warteschlange: aelteste Nachricht faellt weg (gezaehlt)

---------------------------------------------------------------------------
-- Schnittstelle zum Spiel
---------------------------------------------------------------------------
M.api = {
    now = function() return (_G.GetTime and _G.GetTime()) or 0 end,
    time = function() return (_G.time and _G.time()) or 0 end,
    ms = function()
        if _G.debugprofilestop then return _G.debugprofilestop() end
        return ((_G.GetTime and _G.GetTime()) or 0) * 1000
    end,
    inCombat = function() local f = _G.InCombatLockdown; return f and f() and true or false end,
    ah = function()
        local C = _G.C_AuctionHouse
        if type(C) ~= "table" or type(C.GetNumReplicateItems) ~= "function"
            or type(C.GetReplicateItemInfo) ~= "function" then return nil end
        return C
    end,
    faction = function()
        local f = _G.UnitFactionGroup and _G.UnitFactionGroup("player")
        if f == "Horde" then return "H" elseif f == "Alliance" then return "A" end
        return "N"
    end,
    random = function(n) return math.random(n) end,
    -- ist AHSentinel geladen? (liest seine Vollscans selbst)
    ahs = function()
        local C = _G.C_AddOns
        local f = (C and C.IsAddOnLoaded) or _G.IsAddOnLoaded
        if not f then return false end
        local ok, loaded = pcall(f, "AHSentinel")
        return ok and loaded and true or false
    end,
}

---------------------------------------------------------------------------
-- Zustand (bei Uebernahme von der aelteren Fassung)
---------------------------------------------------------------------------
M.hosts = {}                 -- [addon] = db
M.stats = { scans = 0, read = 0, aborted = 0, compared = 0, sent = 0, received = 0, accepted = 0, dropped = {} }
M.reader = nil
M.prev = nil                 -- { t, sigs } letzter eigener Scan dieser Sitzung (nur im Speicher)
M.outbox = {}
if type(existing) == "table" then
    M.hosts = existing.hosts or M.hosts
    M.stats = existing.stats or M.stats
    M.store = existing.store
    M.prev = existing.prev
    M.ep = existing.ep
    M.outbox = existing.outbox or M.outbox
    if existing.frame then
        pcall(existing.frame.UnregisterAllEvents, existing.frame)
        pcall(existing.frame.SetScript, existing.frame, "OnUpdate", nil)
        pcall(existing.frame.SetScript, existing.frame, "OnEvent", nil)
    end
end
_G.GoldSentinelMarkt = M
_G.GSMarkt = M

local function Drop(reason) M.stats.dropped[reason] = (M.stats.dropped[reason] or 0) + 1 end

-- Base36 fuer ganze Zahlen >= 0
local DIG = "0123456789abcdefghijklmnopqrstuvwxyz"
local function Enc(n)
    n = math.floor(tonumber(n) or 0)
    if n <= 0 then return "0" end
    local s = ""
    while n > 0 do
        local r = n % 36
        s = DIG:sub(r + 1, r + 1) .. s
        n = (n - r) / 36
    end
    return s
end
local function Dec(s) return tonumber(s or "", 36) end
M.Enc, M.Dec = Enc, Dec

---------------------------------------------------------------------------
-- Speicher: store.f[Fraktion].i[itemID] = "p,q,n,t,o,g,h" (Base36)
--   p Stueckpreis, q Menge, n Auktionen, t Zeit, o Quelle (0 eigen, 1 netz), g Abgaenge gesamt, h gemessene Sekunden
---------------------------------------------------------------------------
local function Fac()
    local s = M.store
    if not s then return nil end
    local k = M.api.faction()
    s.f = s.f or {}
    s.f[k] = s.f[k] or { i = {}, t = 0 }
    return s.f[k], k
end

local function Unpack(v)
    if type(v) ~= "string" then return nil end
    local p, q, n, t, o, g, h, l = v:match("^(%w+),(%w+),(%w+),(%w+),(%w+),(%w+),(%w+),?(%w*)$")
    if not p then return nil end
    return { p = Dec(p), q = Dec(q), n = Dec(n), t = Dec(t), o = Dec(o), g = Dec(g), h = Dec(h), l = Dec(l) or 0 }
end
local function Pack(e)
    return Enc(e.p) .. "," .. Enc(e.q) .. "," .. Enc(e.n) .. "," .. Enc(e.t) .. "," .. Enc(e.o) .. "," ..
        Enc(e.g) .. "," .. Enc(e.h) .. "," .. Enc(e.l)
end
M.Unpack, M.Pack = Unpack, Pack

function M.Attach(addon, db)
    if type(addon) ~= "string" or type(db) ~= "table" then return end
    M.hosts[addon] = db
    db.gsMarkt = db.gsMarkt or {}
    local g = db.gsMarkt
    g.v = VERSION
    -- Speicher: der Host mit den neuesten Daten
    local function newest(s)
        local best = 0
        for _, f in pairs((s and s.f) or {}) do best = math.max(best, tonumber(f.t) or 0) end
        return best
    end
    if not M.store or newest(g) > newest(M.store) then M.store = g end
    M.askAt = M.askAt or (M.api.now() + M.ASK_DELAY)
end

function M.SetShare(addon, on)
    local db = M.hosts[addon]
    if not db then return end
    db.gsMarktAus = (on == false) or nil
end

function M.IsShareOn()
    if not next(M.hosts) then return false end
    for _, db in pairs(M.hosts) do if db.gsMarktAus then return false end end
    return true
end

function M.Stats() return M.stats end

function M.Get(itemID)
    local f = Fac()
    itemID = tonumber(itemID)
    if not f or not itemID then return nil end
    local e = Unpack(f.i[itemID])
    if not e then return nil end
    local absatz
    local absatzMax
    if (e.h or 0) >= 1800 then
        absatz = (e.l or 0) * 86400 / e.h
        absatzMax = (e.g or 0) * 86400 / e.h
    end
    return { preis = e.p, menge = e.q, n = e.n, t = e.t, quelle = (e.o == 0) and "eigen" or "netz",
             absatz = absatz, absatzMax = absatzMax, abdeckung = (e.h or 0) / 3600 }
end

---------------------------------------------------------------------------
-- Mitlesen
---------------------------------------------------------------------------
function M.OnReplicate()
    local now = M.api.now()
    local newBurst = not M.lastEv or now - M.lastEv > M.BURST_GAP
    M.lastEv = now
    if not newBurst then return end
    if not M.IsShareOn() then Drop("aus"); return end
    if M.feedUntil and now < M.feedUntil then return end      -- ein Host liest diesen Scan selbst und gibt ihn weiter
    if M.api.ahs() then Drop("ahsentinel liest selbst"); return end
    if M.reader then return end
    M.readAt = now + M.READ_DELAY
end

local function StartRead()
    M.readAt = nil
    if not M.IsShareOn() then return end
    local C = M.api.ah()
    if not C or not M.store then return end
    local ok, n = pcall(C.GetNumReplicateItems)
    n = ok and tonumber(n) or 0
    if n <= 0 then Drop("leer"); return end
    M.reader = { n = n, i = 0, sigs = {}, items = {}, cnt = 0, t = M.api.time(), ms = 0, frames = 0 }
end

-- eine Portion lesen; true = fertig
local function ReadPortion(r)
    local C = M.api.ah()
    local okN, n2 = pcall(C.GetNumReplicateItems)
    if not okN or n2 ~= r.n then return "abbruch" end
    local t0, ms = M.api.ms(), M.api.ms
    local info, tlf = C.GetReplicateItemInfo, C.GetReplicateItemTimeLeft
    local sigs, items = r.sigs, r.items
    local ok, err = pcall(function()
        local k = 0
        while r.i < r.n do
            local i = r.i
            r.i = i + 1
            local _, _, count, _, _, _, _, _, _, buyout, _, _, _, _, _, _, itemID = info(i)
            itemID = tonumber(itemID)
            if itemID then
                count, buyout = tonumber(count) or 0, tonumber(buyout) or 0
                local b = tonumber(tlf and tlf(i)) or 0
                if b < 0 or b > 4 then b = 0 end
                r.cnt = r.cnt + 1
                local sig = itemID .. ":" .. count .. ":" .. buyout
                local e, p = sigs[sig] or 0, 1000 ^ b
                if math.floor(e / p) % 1000 < 999 then sigs[sig] = e + p end
                local it = items[itemID]
                if not it then it = { 0, 0, 0 }; items[itemID] = it end
                if buyout > 0 and count > 0 then
                    local u = math.floor(buyout / count)
                    if it[1] == 0 or u < it[1] then it[1] = u end
                end
                it[2], it[3] = it[2] + count, it[3] + 1
            end
            k = k + 1
            if k >= M.CHECK_EVERY then
                k = 0
                if ms() - t0 >= M.BUDGET_MS then return end
            end
        end
    end)
    r.ms, r.frames = r.ms + (M.api.ms() - t0), r.frames + 1
    if not ok then return "fehler", err end
    return r.i >= r.n
end

local function DecB(e)
    local t = {}
    for b = 0, 4 do t[b] = math.floor(e / 1000 ^ b) % 1000 end
    return t
end

-- Abgaenge aus langer Restzeit je Item gegenueber dem letzten Scan
local function Compare(prev, cur)
    local gone, new = {}, {}
    for sig, e2 in pairs(cur) do
        local b2 = DecB(e2)
        local c2 = b2[0] + b2[1] + b2[2] + b2[3] + b2[4]
        local c1 = 0
        if prev[sig] then local b1 = DecB(prev[sig]); c1 = b1[0] + b1[1] + b1[2] + b1[3] + b1[4] end
        if c2 > c1 then
            local id = tonumber(sig:match("^(%d+):"))
            if id then new[id] = (new[id] or 0) + (c2 - c1) end
        end
    end
    for sig, e1 in pairs(prev) do
        local b1 = DecB(e1)
        local c1 = b1[0] + b1[1] + b1[2] + b1[3] + b1[4]
        local c2 = 0
        local e2 = cur[sig]
        if e2 then local b2 = DecB(e2); c2 = b2[0] + b2[1] + b2[2] + b2[3] + b2[4] end
        local g = c1 - c2
        if g > 0 then
            for _, b in ipairs({ 1, 2, 3, 4, 0 }) do
                local take = math.min(g, b1[b])
                if take > 0 then
                    if b == 3 or b == 4 then
                        local id = tonumber(sig:match("^(%d+):"))
                        if id then gone[id] = (gone[id] or 0) + take end
                    end
                    g = g - take
                end
                if g <= 0 then break end
            end
        end
    end
    -- vorsichtig: neue Auktionen desselben Items gelten als "abgebrochen und neu eingestellt"
    local low = {}
    for id, g in pairs(gone) do low[id] = math.max(0, g - (new[id] or 0)) end
    return gone, low
end
M.Compare = Compare

local QueueScan     -- weiter unten

-- Ergebnis eines Scans uebernehmen (eigenes Lesen oder Feed eines Host-Addons)
--   items[id] = { Stueckpreis, Menge, Auktionen }; cmp/low[id] = Abgaenge (Ober-/Untergrenze) oder nil; dt = Sekunden
local function Apply(t, cnt, items, cmp, low, dt, prevItems)
    local f = Fac()
    if not f then return end
    local changed = {}
    for id, it in pairs(items) do
        local old = Unpack(f.i[id])
        local e = { p = it[1], q = it[2], n = it[3], t = t, o = 0, g = old and old.g or 0, h = old and old.h or 0,
                    l = old and old.l or 0 }
        if cmp then
            e.g = e.g + (cmp[id] or 0)
            e.l = e.l + (low and low[id] or 0)
            e.h = e.h + dt
        end
        if not old or old.o ~= 0 or (old.p or 0) == 0
            or math.abs((e.p or 0) - old.p) / old.p >= M.NET_CHANGE then
            changed[#changed + 1] = id
        end
        f.i[id] = Pack(e)
    end
    -- Items, die seit dem letzten Scan ganz verschwunden sind: Abgaenge zaehlen, Angebot jetzt 0
    if cmp and prevItems then
        for id in pairs(prevItems) do
            if not items[id] then
                local old = Unpack(f.i[id])
                if old then
                    old.g, old.h = (old.g or 0) + (cmp[id] or 0), (old.h or 0) + dt
                    old.l = (old.l or 0) + (low and low[id] or 0)
                    old.q, old.n, old.t, old.o = 0, 0, t, 0
                    f.i[id] = Pack(old)
                end
            end
        end
    end
    f.t = t
    M.stats.scans = M.stats.scans + 1
    M.stats.read = cnt
    M.stats.lastT = t
    -- fuer den Uploader
    local parts, nItems = {}, 0
    for id, it in pairs(items) do
        nItems = nItems + 1
        parts[#parts + 1] = Enc(id) .. "," .. Enc(it[1]) .. "," .. Enc(it[2]) .. "," .. Enc(it[3]) .. "," ..
            Enc(cmp and cmp[id] or 0) .. "," .. Enc(low and low[id] or 0)
    end
    -- ganz verschwundene Items (ausverkauft/abgelaufen): Eintrag mit Menge 0, damit der Absatz nicht verloren geht
    if cmp and prevItems then
        for id in pairs(prevItems) do
            if not items[id] and ((cmp[id] or 0) > 0) then
                parts[#parts + 1] = Enc(id) .. ",0,0,0," .. Enc(cmp[id] or 0) .. "," .. Enc(low and low[id] or 0)
            end
        end
    end
    M.stats.items = nItems
    local s = M.store
    s.export = s.export or {}
    table.insert(s.export, string.format("GSMARKT1|%d|%s|%d|%d|%d|%d|%s", 1,          -- Export-Format 1 (unabhaengig von der Dateiversion)
        select(2, Fac()), t, cnt,
        nItems, cmp and dt or 0, table.concat(parts, ";")))
    while #s.export > M.EXPORT_KEEP do table.remove(s.export, 1) end
    QueueScan(t, changed)
end

local function FinishRead(r)
    if not Fac() then return end
    local cmp, low
    if M.prev and M.prev.sigs and r.t - M.prev.t >= M.CMP_MIN and r.t - M.prev.t <= M.CMP_MAX then
        cmp, low = Compare(M.prev.sigs, r.sigs)
        M.stats.compared = M.stats.compared + 1
    end
    local dt = M.prev and (r.t - M.prev.t) or 0
    M.stats.lastMs, M.stats.lastFrames = r.ms, r.frames
    Apply(r.t, r.cnt, r.items, cmp, low, dt, M.prev and M.prev.items)
    M.prev = { t = r.t, sigs = r.sigs, items = r.items }
end

-- Feed: ein Host-Addon, das selbst einen Vollscan liest (z. B. AHSentinel), gibt sein Ergebnis weiter, damit der
-- Scan im selben Client NICHT zweimal gelesen wird (Speicher, Ruckeln).
--   GSMarkt.FeedStart("AHSentinel")  -- direkt VOR dem eigenen ReplicateItems: GSMarkt liest diesen Scan nicht selbst
--   GSMarkt.Feed("AHSentinel", t, n, items, dt)
--      t = time() des Scans, n = Anzahl Auktionen, dt = Sekunden seit dem Scan, mit dem die Abgaenge gemessen wurden
--      (0 = kein Vergleich), items[itemID] = { preis = Stueckpreis, menge = Menge, n = Auktionen,
--      abg = Abgaenge aus Stufe 3/4 (Obergrenze) oder nil, abgV = vorsichtige Abgaenge (Untergrenze) oder nil }
function M.FeedStart(addon)
    if not M.hosts[addon] then return end
    M.feedUntil = M.api.now() + 300
    M.readAt = nil
    if M.reader then M.reader = nil; M.stats.aborted = M.stats.aborted + 1; Drop("feed statt lesen") end
end

function M.Feed(addon, t, n, items, dt)
    M.feedUntil = nil
    if not M.hosts[addon] or type(items) ~= "table" or not M.IsShareOn() then return end
    t, dt = tonumber(t) or M.api.time(), tonumber(dt) or 0
    local conv, cmp, low = {}, nil, nil
    if dt > 0 then cmp, low = {}, {} end
    for id, it in pairs(items) do
        id = tonumber(id)
        if id and type(it) == "table" then
            conv[id] = { math.floor(tonumber(it.preis) or 0), math.floor(tonumber(it.menge) or 0),
                         math.floor(tonumber(it.n) or 0) }
            if cmp then
                local g = math.floor(tonumber(it.abg) or 0)
                cmp[id] = g
                low[id] = math.min(g, math.floor(tonumber(it.abgV) or g))
            end
        end
    end
    M.stats.fed = (M.stats.fed or 0) + 1
    if cmp then M.stats.compared = M.stats.compared + 1 end
    M.prev = nil                -- naechstes eigenes Lesen vergleicht nicht mit einem Feed (keine Signaturen)
    Apply(t, tonumber(n) or 0, conv, cmp, low, dt, nil)
end

---------------------------------------------------------------------------
-- Teilen
---------------------------------------------------------------------------
local function Entry(id, e)
    return Enc(id) .. "," .. Enc(e.p) .. "," .. Enc(e.q) .. "," .. Enc(e.n)
end

-- alle eigenen Items eines Scans an die Gilde, die geaenderten (hoechstens NET_MAX) auch ins Netz
QueueScan = function(t, changed, full)
    local f, fac = Fac()
    if not f or not M.ep or not M.IsShareOn() then return end
    local now = M.api.now()
    if not full and (not M.lastFull or now - M.lastFull >= M.FULL_EVERY) then full = true end
    local all = {}
    if full then
        M.lastFull = now
        for id, v in pairs(f.i) do
            local e = Unpack(v)
            if e and e.o == 0 and e.t == t then all[#all + 1] = id end
        end
    else
        for i = 1, math.min(#changed, M.NET_MAX) do all[i] = changed[i] end
    end
    table.sort(all)
    local head = "S:" .. fac .. ":" .. Enc(t) .. ":"
    local S = _G.GoldSentinelSync
    local max = (S and S.MAX_PAYLOAD) or 230
    local function batches(list, opts)
        local cur, len = {}, #head
        for _, id in ipairs(list) do
            local e = Entry(id, Unpack(f.i[id]))
            if #cur > 0 and (#cur >= M.ITEMS_PER_MSG or len + 1 + #e > max) then
                M.outbox[#M.outbox + 1] = { head .. table.concat(cur, ";"), opts }
                cur, len = {}, #head
            end
            cur[#cur + 1] = e
            len = len + #e + 1
        end
        if #cur > 0 then M.outbox[#M.outbox + 1] = { head .. table.concat(cur, ";"), opts } end
        while #M.outbox > M.OUTBOX_MAX do table.remove(M.outbox, 1); Drop("warteschlange voll") end
    end
    batches(all, { scope = "guild" })
    local net = {}
    for i = 1, math.min(#changed, M.NET_MAX) do net[i] = changed[i] end
    table.sort(net)
    if #net > 0 and S and S.NET then batches(net, { net = true }) end
end

local function SyncQueueLen()
    local S = _G.GoldSentinelSync
    return (S and S.queue and #S.queue) or 0
end

function M.Pump()
    if not M.ep or #M.outbox == 0 then return end
    if not M.IsShareOn() then
        for _ = 1, #M.outbox do Drop("aus") end
        M.outbox = {}
        return
    end
    if M.api.inCombat() then return end
    local sent = 0
    while #M.outbox > 0 and SyncQueueLen() < M.QUEUE_HIGH and sent < 5 do
        local m = table.remove(M.outbox, 1)
        local opts = m[2] or {}
        if opts.net then
            -- nur ins Fluester-Netz (die Gilde hat den ganzen Scan schon); Empfaenger bringen es in ihre Gilde
            local S = _G.GoldSentinelSync
            if S and S.NET and S.NetSend and S.Enc and S.sid then
                S.counter = (tonumber(S.counter) or 0) + 1
                pcall(S.NetSend, M.PREFIX, S.sid, S.Enc(S.counter), S.NET_TTL, m[1], nil, M.ep)
            end
        else
            M.ep:Send(m[1], { scope = "guild", net = false }) -- ganzer Scan nur an die Gilde
        end
        M.stats.sent = M.stats.sent + 1
        sent = sent + 1
    end
end

-- empfangene Nachricht
function M.OnMessage(msg, sender)
    if type(msg) ~= "string" then return end
    local f, fac = Fac()
    if not f then return end
    local kind, mfac, rest = msg:match("^(%u):(%u):(.*)$")
    if not kind then Drop("format"); return end
    if mfac ~= fac then Drop("fraktion"); return end
    if kind == "S" then
        if not M.IsShareOn() then Drop("aus"); return end
        local ts, body = rest:match("^(%w+):(.*)$")
        local t = Dec(ts)
        local now = M.api.time()
        if not t or t > now + 300 or t < now - M.MAX_AGE then Drop("zeit"); return end
        M.stats.received = M.stats.received + 1
        for item in body:gmatch("[^;]+") do
            local a, b, c, d = item:match("^(%w+),(%w+),(%w+),(%w+)$")
            local id, p, q, n = Dec(a), Dec(b), Dec(c), Dec(d)
            if id and p and q and n then
                local old = Unpack(f.i[id])
                if old and old.t >= t then
                    Drop("aelter")
                elseif old and old.o == 0 and old.p and old.p > 0 and p > 0 and t - old.t < 6 * 3600
                    and (p > old.p * M.OUTLIER or p * M.OUTLIER < old.p) then
                    Drop("ausreisser")
                else
                    local e = { p = p, q = q, n = n, t = t, o = 1, g = old and old.g or 0, h = old and old.h or 0,
                                l = old and old.l or 0 }
                    f.i[id] = Pack(e)
                    M.stats.accepted = M.stats.accepted + 1
                    if t > (f.tn or 0) then f.tn = t end
                end
            else
                Drop("format")
            end
        end
    elseif kind == "Q" then
        -- Frage "wer hat Neueres als t?": antworten, wenn der eigene Scan mind. 10 Min. neuer ist (nach Zufallspause)
        local t = Dec(rest) or 0
        if (f.t or 0) > t + 600 and M.IsShareOn() then
            M.answerAt = M.api.now() + 5 + M.api.random(15)
            M.answerT = f.t
        end
    elseif kind == "A" then
        -- jemand anderes beantwortet die Frage schon mit einem mindestens so neuen Scan
        local t = Dec(rest) or 0
        if M.answerAt and t >= (M.answerT or 0) then M.answerAt = nil end
    end
end

---------------------------------------------------------------------------
-- Takt und Ereignisse
---------------------------------------------------------------------------
local function Register()
    if M.ep then return end
    local S = _G.GoldSentinelSync
    if not S or not S.Register then return end
    local ok, ep = pcall(S.Register, "GoldSentinelMarkt", M.PREFIX, tostring(VERSION))
    if ok and ep then
        M.ep = ep
        ep:OnMessage(function(msg, sender) pcall(_G.GoldSentinelMarkt.OnMessage, msg, sender) end)
    end
end
M.Register = Register

function M.Tick()
    Register()
    local now = M.api.now()
    if M.readAt and now >= M.readAt and not M.api.inCombat() then StartRead() end
    local r = M.reader
    if r and not M.api.inCombat() then
        local done, err = ReadPortion(r)
        if done == "abbruch" or done == "fehler" then
            M.reader = nil
            M.stats.aborted = M.stats.aborted + 1
            Drop(done == "fehler" and ("lesefehler " .. tostring(err)):sub(1, 60) or "liste geaendert")
        elseif done then
            M.reader = nil
            local ok, e2 = pcall(FinishRead, r)
            if not ok then Drop(("auswertung " .. tostring(e2)):sub(1, 60)) end
        end
    end
    -- Speichern und Weitergeben
    if M.ep and M.askAt and now >= M.askAt and M.IsShareOn() then
        M.askAt = nil
        local f, fac = Fac()
        if f then M.ep:Send("Q:" .. fac .. ":" .. Enc(math.max(f.t or 0, f.tn or 0)), { scope = "guild", net = false }) end
    end
    if M.answerAt and now >= M.answerAt then
        M.answerAt = nil
        local f, fac = Fac()
        if f and M.ep then
            M.ep:Send("A:" .. fac .. ":" .. Enc(f.t), { scope = "guild", net = false })
            QueueScan(f.t, {}, true)
        end
    end
    M.Pump()
end

function M.DiagLines()
    local s = M.stats
    local f = Fac()
    local n, own, net, meas = 0, 0, 0, 0
    for _, v in pairs((f and f.i) or {}) do
        local e = Unpack(v)
        if e then
            n = n + 1
            if e.o == 0 then own = own + 1 else net = net + 1 end
            if (e.h or 0) >= 1800 then meas = meas + 1 end
        end
    end
    local drops = {}
    for k, v in pairs(s.dropped) do drops[#drops + 1] = k .. " " .. v end
    table.sort(drops)
    local hosts = {}
    for k in pairs(M.hosts) do hosts[#hosts + 1] = k end
    table.sort(hosts)
    return {
        string.format("MARKT-NETZ v%d · %s · Addons: %s", VERSION, M.IsShareOn() and "an" or "AUS",
            #hosts > 0 and table.concat(hosts, ", ") or "keins"),
        string.format("MARKT-NETZ Scans %d (davon vom Host übergeben %d; zuletzt %d Auktionen, %d Items, %.0f ms in %d Bildern) · Vergleiche %d · abgebrochen %d",
            s.scans, s.fed or 0, s.read or 0, s.items or 0, s.lastMs or 0, s.lastFrames or 0, s.compared, s.aborted),
        string.format("MARKT-NETZ Items %d (eigen %d, Netz %d, Absatz gemessen %d) · gesendet %d · empfangen %d · angenommen %d · Warteschlange %d",
            n, own, net, meas, s.sent, s.received, s.accepted, #M.outbox),
        "MARKT-NETZ verworfen: " .. (#drops > 0 and table.concat(drops, ", ") or "nichts"),
    }
end

local CF = _G.CreateFrame
if CF then
    local fr = CF("Frame")
    M.frame = fr
    pcall(fr.RegisterEvent, fr, "REPLICATE_ITEM_LIST_UPDATE")
    fr:SetScript("OnEvent", function(_, event)
        if event == "REPLICATE_ITEM_LIST_UPDATE" then pcall(_G.GoldSentinelMarkt.OnReplicate) end
    end)
    local acc = 0
    fr:SetScript("OnUpdate", function(_, dt)
        acc = acc + (dt or 0)
        if acc < 0.05 and not _G.GoldSentinelMarkt.reader then return end
        acc = 0
        pcall(_G.GoldSentinelMarkt.Tick)
    end)
end
