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
-- Version 3 (13. November 2026, 23:40, Entscheid des Nutzers): Export haelt 6 statt 2 Scans fuer den Uploader (Scans
--   eines Abends ohne laufenden Uploader gehen nicht verloren), hoechstens 1,5 MB zusammen (aelteste fallen weg) –
--   damit Speichern/Laden der SavedVariables klein bleibt (Ruckeln vermeiden). Sonst unveraendert.

-- Version 4 (14. November 2026, Befund MN-S2 der BuffSentinel-Sitzung): Schalter aus stoppt auch eine schon geplante
--   Antwort "A:" (Tick prueft IsShareOn, SetShare(false) verwirft answerAt und askAt). Sonst unveraendert.

-- Version 5 (15. November 2026, Bitte der AHSentinel-Sitzung, Bericht 0.65.199): Feed laeuft in Portionen (hoechstens
--   BUDGET_MS je Bild, im Tick; M.Feed nimmt nur an und kehrt sofort zurueck) – vorher alle Items eines Scans in EINEM
--   Aufruf (54–62 ms, +22 MB). Abgaenge beim Feed nur fuer die Items, zu denen das Host-Addon Abgaenge liefert (abg):
--   nur dort zaehlen Abgaenge und Vergleichszeit; Items ohne abg behalten ihren Absatz (vorher: Abgang 0 + Zeit = falsch
--   kleiner Absatz). Export: Items mit Abgaengen in der Zeile mit Vergleich (dt), Items ohne in einer zweiten Zeile ohne
--   Vergleich (Zeit t+1, damit die Sammelstelle sie nicht als doppelt verwirft). Ein neuer Feed, waehrend ein alter laeuft:
--   der alte wird zuerst fertig gerechnet (nichts geht verloren).

-- Version 6 (15. November 2026, Bitte der AHSentinel-Sitzung, Bericht 0.65.202: Feed legte +7 bis +10 MB an, s92 rot):
--   weniger Speicher-Muell beim Feed, gemessen 6000 Items: Enc baut die Zahl in einem wiederverwendeten Puffer (eine
--   Zeichenkette statt eine je Stelle), Feed liest/schreibt die Item-Eintraege ohne Hilfstabellen (UnpackVals/PackVals),
--   die Base36-Texte von Preis/Menge/Auktionen/Abgaengen werden fuer Speicher und Export nur einmal gebaut. Sonst unveraendert.

-- Version 7 (15. November 2026, Messung AHSentinel s216: Feed-Anteil 6,3 MB, Grenze 4 MB): der grosse Anteil kam aus dem
--   vollen Teilen an die Gilde (QueueScan mit full, hoechstens 1x je Stunde): je Item eine Hilfstabelle (Unpack) und vier neu
--   gebaute Base36-Texte. Jetzt liest QueueScan die schon gespeicherten Base36-Texte direkt aus dem Item-Eintrag (keine Tabelle,
--   kein Enc), UnpackVals faengt nur die noetigen Felder, und die Export-Zeile wird ohne zweite Kopie gebaut. Ergebnis und
--   Nachrichten unveraendert (gleiche Zeichen).

-- Version 8 (17. November 2026, Befund SANDBOX-2 der AHSentinel-Sitzung, Bericht 2026-11-17 08:51): Test-IDs der
--   Testroutinen (itemID ab 990000000, nie ein echtes Item) kamen am 16.11. ueber einen Feed der Testroutine in den echten
--   Speicher (1050 Items, Preis 1) und in den Export. Jetzt: Test-IDs werden nie angenommen, gespeichert, exportiert oder
--   gesendet (Feed, eigenes Lesen, Empfang), und beim Anmelden jedes Addons (Attach) einmal aus dessen Speicher entfernt:
--   Items aller Fraktionen; Export-Zeilen nur aus Test-Items fallen weg, gemischte Zeilen verlieren nur die Test-Items
--   (Kopf: Anzahl Items und Auktionen angepasst). Zaehler M.stats.testIds, Diagnose-Zeile "MARKT-NETZ Test-IDs entfernt".

-- Version 9 (17. November 2026, Messung AHSentinel 0.65.312 s216: OnUpdate des Bausteins 19–21 ms in einem Bild bei 6000 Items;
--   im Baustein nachgemessen: die Feed-Portionen halten 4 ms, aber der LETZTE Schritt (volles Teilen an die Gilde: alle Items
--   suchen, sortieren, Nachrichten bauen) lief am Stueck 15–17 ms). Jetzt ist Teilen ein Auftrag, der im Takt in Portionen
--   (BUDGET_MS) gerechnet wird, nie im selben Bild wie eine Feed-Portion; der Feed gibt seine Item-Liste mit (kein Durchlauf ueber
--   den ganzen Speicher); ohne Liste werden zuerst nur die Schluessel kopiert und dann in Portionen geprueft. Nachrichten und
--   Reihenfolge unveraendert (gleiche Zeichen); Eintraege, die inzwischen ein neuerer Scan ueberschrieben hat, schickt der neuere.
--   Ebenso die Auswertung eines SELBST gelesenen Scans (Addons ohne AHSentinel): Vergleich, Items, verschwundene Items und Export
--   jetzt als Auftrag in Portionen (vorher am Stueck: gemessen 60–180 ms in einem Bild bei 20000 Auktionen). Hoechstens EINE
--   Rechen-Portion je Bild (Feed, Auswertung, Teilen, Lesen). Speicher, Export und Nachrichten byte-gleich wie v8 (Test).

-- Version 10 (17. November 2026, Messung AHSentinel 0.65.318, Nachbau mit echten Daten: Feed-Portion bis 7,2 ms bei Budget 4 ms):
--   die Zeit wurde nur alle 100 Eintraege geprueft (die Tests liefen mit 10 und sahen es nicht). Jetzt alle 20 (Lesen und Feed).
--   Sonst unveraendert.

local VERSION = 10

local existing = _G.GoldSentinelMarkt
if type(existing) == "table" and (tonumber(existing.VERSION) or 0) >= VERSION then return end

local M = {}
M.VERSION = VERSION
M.PREFIX = "GSMARKT1"
M.BUDGET_MS = 4              -- Rechenzeit je Bild beim Lesen
M.CHECK_EVERY = 20           -- so oft wird die Zeit innerhalb einer Portion geprueft (v10: 20 statt 100 – Messung AHS 0.65.318: Feed-Portion bis 7,2 ms bei Budget 4)
M.BURST_GAP = 30             -- Sekunden ohne Ereignis = naechstes Ereignis ist ein neuer Scan
M.READ_DELAY = 2             -- Sekunden nach dem ersten Ereignis bis zum Lesen
M.CMP_MIN, M.CMP_MAX = 600, 6 * 3600   -- Abstand zweier Scans fuer den Absatz-Vergleich
M.ITEMS_PER_MSG = 9          -- Eintraege je Nachricht (Base36, passt in 230 Zeichen)
M.QUEUE_HIGH = 10            -- nur nachschieben, solange die Sync-Warteschlange kuerzer ist
M.NET_MAX = 60               -- hoechstens so viele geaenderte Items ins Netz je Scan
M.NET_CHANGE = 0.05          -- Preis-Aenderung, ab der ein Item als geaendert gilt
M.OUTLIER = 3                -- fremder Preis x3 oder :3 zum eigenen (juenger als 6 Std.) = verworfen
M.MAX_AGE = 7 * 86400        -- aeltere Daten werden nicht angenommen
M.EXPORT_KEEP = 6            -- so viele Scans fuer den Uploader (v3: 6 statt 2)
M.EXPORT_MAX_BYTES = 1536 * 1024  -- alle Export-Zeilen zusammen hoechstens so gross (aelteste fallen zuerst weg)
M.ASK_DELAY = 60             -- Sekunden nach dem Laden bis zur Frage "wer hat Neueres?"
M.FULL_EVERY = 3600          -- ganzer Scan an die Gilde hoechstens so oft (Sekunden), sonst nur Aenderungen
M.OUTBOX_MAX = 1500          -- volle eigene Warteschlange: aelteste Nachricht faellt weg (gezaehlt)
M.TEST_ID_MIN = 990000000    -- v8: ab hier Test-IDs der Testroutinen (nie ein echtes Item): nie annehmen/speichern/senden

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
M.queueJobs = {}             -- v9: Teilen in Portionen
if type(existing) == "table" then
    M.hosts = existing.hosts or M.hosts
    M.stats = existing.stats or M.stats
    M.store = existing.store
    M.prev = existing.prev
    M.ep = existing.ep
    M.outbox = existing.outbox or M.outbox
    M.queueJobs = existing.queueJobs or M.queueJobs
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
-- v6: Ziffern in einen wiederverwendeten Puffer (rueckwaerts), dann EINE Zeichenkette (vorher eine je Stelle)
local DIGB = { DIG:byte(1, -1) }
local EBUF, EOUT = {}, {}
local schar, unpk = string.char, unpack
local function Enc(n)
    n = math.floor(tonumber(n) or 0)
    if n <= 0 then return "0" end
    local k = 0
    while n > 0 do
        local r = n % 36
        k = k + 1
        EBUF[k] = DIGB[r + 1]
        n = (n - r) / 36
    end
    for i = 1, k do EOUT[i] = EBUF[k - i + 1] end
    return schar(unpk(EOUT, 1, k))
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
-- v6: ohne Hilfstabelle (fuer den Feed): nur die Werte, die der Feed braucht
local function UnpackVals(v)
    if type(v) ~= "string" then return nil end
    local p, o, g, h, l = v:match("^(%w+),%w+,%w+,%w+,(%w+),(%w+),(%w+),?(%w*)$")
    if not p then return nil end
    return Dec(p), Dec(o), Dec(g), Dec(h), Dec(l) or 0
end
M.UnpackVals = UnpackVals

-- v8: Test-IDs (Testroutinen) erkennen und aus einem Speicher entfernen
local function IsTestID(id)
    id = tonumber(id)
    return id ~= nil and id >= M.TEST_ID_MIN
end
M.IsTestID = IsTestID

-- schnelle Vorpruefung einer Export-Zeile ohne Muster (Muster ueber 1,5 MB kosten ~20 ms, das hier ~1 ms):
-- Test-IDs 990000000..999999999 sind in Base36 sechsstellig und beginnen mit gd..gj (989293824..1001051135);
-- echte Items (< 60 Mio.) haben hoechstens 5 Stellen. Eine Item-ID steht immer direkt nach "|" (erstes Item) oder ";".
local TEST_PREFIX = { ";gd", ";ge", ";gf", ";gg", ";gh", ";gi", ";gj", "|gd", "|ge", "|gf", "|gg", "|gh", "|gi", "|gj" }
local function HasTestPrefix(line)
    for k = 1, #TEST_PREFIX do
        local pre, init = TEST_PREFIX[k], 1
        while true do
            local a = line:find(pre, init, true)
            if not a then break end
            -- nur sechsstellige IDs (Test-ID), nicht kurze echte IDs wie "gd5"
            if line:find("^%w%w%w%w%w%w,", a + 1) and IsTestID(tonumber(line:sub(a + 1, a + 6), 36)) then return true end
            init = a + 3
        end
    end
    return false
end

-- entfernt Test-IDs aus g (= db.gsMarkt): Items aller Fraktionen und Export-Zeilen. Rueckgabe: Items, Export-Eintraege
function M.PurgeTestIDs(g)
    if type(g) ~= "table" then return 0, 0 end
    local nI, nE = 0, 0
    for _, f in pairs(type(g.f) == "table" and g.f or {}) do
        if type(f) == "table" and type(f.i) == "table" then
            local del = {}
            for id in pairs(f.i) do if IsTestID(id) then del[#del + 1] = id end end
            for _, id in ipairs(del) do f.i[id] = nil end
            nI = nI + #del
        end
    end
    if type(g.export) == "table" then
        local out = {}
        for _, line in ipairs(g.export) do
            local keepLine = line
            if type(line) == "string" and HasTestPrefix(line) then
                local head, cnt, _, dt, body = line:match("^(GSMARKT1|%d+|%u|%d+)|(%d+)|(%d+)|(%d+)|(.*)$")
                if head then
                    local kept, removed, auc = {}, 0, 0
                    for part in body:gmatch("[^;]+") do
                        local idE, _, _, nE36 = part:match("^(%w+),(%w+),(%w+),(%w+)")
                        if idE and IsTestID(Dec(idE)) then
                            removed = removed + 1
                            auc = auc + (Dec(nE36) or 0)
                        else
                            kept[#kept + 1] = part
                        end
                    end
                    if removed > 0 then
                        nE = nE + removed
                        if #kept == 0 then
                            keepLine = nil
                        else
                            keepLine = head .. "|" .. math.max(0, tonumber(cnt) - auc) .. "|" .. #kept .. "|" .. dt ..
                                "|" .. table.concat(kept, ";")
                        end
                    end
                end
            end
            if keepLine then out[#out + 1] = keepLine end
        end
        if nE > 0 then
            for k = #g.export, 1, -1 do g.export[k] = nil end
            for k, v in ipairs(out) do g.export[k] = v end
        end
    end
    return nI, nE
end
M.Unpack, M.Pack = Unpack, Pack

function M.Attach(addon, db)
    if type(addon) ~= "string" or type(db) ~= "table" then return end
    M.hosts[addon] = db
    db.gsMarkt = db.gsMarkt or {}
    local g = db.gsMarkt
    g.v = VERSION
    local okP, pI, pE = pcall(M.PurgeTestIDs, g)          -- v8: Test-IDs einmal beim Anmelden entfernen
    if okP and (pI + pE) > 0 then
        M.stats.testIds = (M.stats.testIds or 0) + pI + pE
        M.stats.testIdsAt = M.stats.testIdsAt or {}
        M.stats.testIdsAt[addon] = pI .. " Items, " .. pE .. " Export"
    end
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
    if on == false then M.answerAt, M.askAt = nil, nil end   -- v4 (MN-S2): geplante Frage/Antwort verwerfen
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

-- Ergebnis eines eigenen Scans uebernehmen – v9 als Auftrag in Portionen (M.applyJob, ApplyPortion), vorher am Stueck
-- (gemessen 36 ms in einem Bild bei 20000 Auktionen, mit Vergleich mehr). Phasen: Vergleich (cmp1, cmp2) -> Items (apply) ->
-- verschwundene Items (gone) -> Abschluss (finish: Export, Teilen). Ergebnis, Export und Nachrichten byte-gleich wie v8.
--   items[id] = { Stueckpreis, Menge, Auktionen }; cmp/low[id] = Abgaenge (Ober-/Untergrenze) oder nil; dt = Sekunden
local function KeysOf(t)
    local k = {}
    for x in pairs(t) do k[#k + 1] = x end
    return k
end
-- Schluessel in Portionen sammeln (die Tabelle aendert sich waehrend des Auftrags nicht: next() darf weiterlaufen).
-- Rueckgabe true, wenn fertig; j.kl = Liste, j.kk = letzter Schluessel
local function KeysStep(j, t, budget, t0)
    j.kl = j.kl or {}
    local kl, k, n = j.kl, j.kk, 0
    while true do
        k = next(t, k)
        if k == nil then j.kk = nil; return true end
        kl[#kl + 1] = k
        n = n + 1
        if budget and n % 200 == 0 and M.api.ms() - t0 >= budget then j.kk = k; return false end
    end
end
local function Count5(e)
    local b = DecB(e)
    return b[0] + b[1] + b[2] + b[3] + b[4], b
end

local ApplyPortion
ApplyPortion = function(j, budget)
    local t0 = M.api.ms()
    -- Zeit alle 5 Eintraege pruefen (ein Eintrag kostet bis ~0,1 ms: Ueberschreitung des Budgets hoechstens ~0,5 ms)
    local function over(i) return budget and (i % 5 == 0) and M.api.ms() - t0 >= budget end
    -- Schluessel-Listen werden in einem eigenen Bild angelegt (je ~1–2 ms bei 20000), danach wird in Portionen gerechnet
    local function pause() j.ms, j.frames = j.ms + (M.api.ms() - t0), j.frames + 1; return false end
    while true do
        if j.phase == "cmp1" then             -- neue Auktionen je Item
            if not j.keys then
                if not KeysStep(j, j.curSigs, budget, t0) then return pause() end
                j.keys, j.kl, j.i = j.kl, nil, 0
            end
            local keys, cur, prev, new = j.keys, j.curSigs, j.prevSigs, j.new
            while j.i < #keys do
                j.i = j.i + 1
                local sig = keys[j.i]
                local c2 = Count5(cur[sig])
                local c1 = prev[sig] and Count5(prev[sig]) or 0
                if c2 > c1 then
                    local id = tonumber(sig:match("^(%d+):"))
                    if id then new[id] = (new[id] or 0) + (c2 - c1) end
                end
                if over(j.i) then j.ms, j.frames = j.ms + (M.api.ms() - t0), j.frames + 1; return false end
            end
            j.phase, j.keys = "cmp2", nil
        elseif j.phase == "cmp2" then         -- Abgaenge aus Stufe 3/4 (kuerzeste Restzeiten zuerst als abgelaufen)
            if not j.keys then
                if not KeysStep(j, j.prevSigs, budget, t0) then return pause() end
                j.keys, j.kl, j.i = j.kl, nil, 0
            end
            local keys, cur, prev, gone = j.keys, j.curSigs, j.prevSigs, j.gone
            while j.i < #keys do
                j.i = j.i + 1
                local sig = keys[j.i]
                local c1, b1 = Count5(prev[sig])
                local c2 = cur[sig] and Count5(cur[sig]) or 0
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
                if over(j.i) then j.ms, j.frames = j.ms + (M.api.ms() - t0), j.frames + 1; return false end
            end
            local low = {}           -- vorsichtig: neue Auktionen desselben Items gelten als "abgebrochen und neu eingestellt"
            for id, g in pairs(gone) do low[id] = math.max(0, g - (j.new[id] or 0)) end
            j.cmp, j.low, j.keys, j.new, j.gone = gone, low, nil, nil, nil
            j.curSigs, j.prevSigs = nil, nil
            j.phase = "apply"
        elseif j.phase == "apply" then
            local f = Fac()
            if not f then M.applyJob = nil; return true end
            if not j.ids then
                if not KeysStep(j, j.items, budget, t0) then return pause() end
                local ids = {}
                for _, id in ipairs(j.kl) do      -- v8: Test-IDs nie speichern/exportieren
                    if IsTestID(id) then j.items[id] = nil; Drop("test-id") else ids[#ids + 1] = id end
                end
                j.ids, j.kl, j.i, j.changed, j.parts, j.nItems = ids, nil, 0, {}, {}, 0
                if budget then return pause() end
            end
            local ids, items, cmp, low, t, dt = j.ids, j.items, j.cmp, j.low, j.t, j.dt
            while j.i < #ids do
                j.i = j.i + 1
                local id = ids[j.i]
                local it = items[id]
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
                    j.changed[#j.changed + 1] = id
                end
                f.i[id] = Pack(e)
                j.nItems = j.nItems + 1         -- fuer den Uploader
                j.parts[#j.parts + 1] = Enc(id) .. "," .. Enc(it[1]) .. "," .. Enc(it[2]) .. "," .. Enc(it[3]) .. "," ..
                    Enc(cmp and cmp[id] or 0) .. "," .. Enc(low and low[id] or 0)
                if over(j.i) then j.ms, j.frames = j.ms + (M.api.ms() - t0), j.frames + 1; return false end
            end
            j.phase, j.gids = "gone", nil
        elseif j.phase == "gone" then
            -- Items, die seit dem letzten Scan ganz verschwunden sind: Abgaenge zaehlen, Angebot jetzt 0; Export mit Menge 0
            local f = Fac()
            if not f then M.applyJob = nil; return true end
            local cmp, low, items, t, dt = j.cmp, j.low, j.items, j.t, j.dt
            if cmp and j.prevItems then
                if not j.gids then
                    if not KeysStep(j, j.prevItems, budget, t0) then return pause() end
                    j.gids, j.kl, j.i = j.kl, nil, 0
                end
                local gids = j.gids
                while j.i < #gids do
                    j.i = j.i + 1
                    local id = gids[j.i]
                    if not items[id] then
                        local old = Unpack(f.i[id])
                        if old then
                            old.g, old.h = (old.g or 0) + (cmp[id] or 0), (old.h or 0) + dt
                            old.l = (old.l or 0) + (low and low[id] or 0)
                            old.q, old.n, old.t, old.o = 0, 0, t, 0
                            f.i[id] = Pack(old)
                        end
                        if (cmp[id] or 0) > 0 then
                            j.parts[#j.parts + 1] = Enc(id) .. ",0,0,0," .. Enc(cmp[id] or 0) .. "," .. Enc(low and low[id] or 0)
                        end
                    end
                    if over(j.i) then j.ms, j.frames = j.ms + (M.api.ms() - t0), j.frames + 1; return false end
                end
            end
            j.phase = "finish"
        else                                    -- finish
            M.applyJob = nil
            local f, fac = Fac()
            if not f then return true end
            local t, cmp = j.t, j.cmp
            f.t = t
            M.stats.scans = M.stats.scans + 1
            M.stats.read = j.cnt
            M.stats.lastT = t
            M.stats.items = j.nItems
            M.stats.applyMs, M.stats.applyFrames = j.ms + (M.api.ms() - t0), j.frames + 1
            local s = M.store
            s.export = s.export or {}
            table.insert(s.export, string.format("GSMARKT1|%d|%s|%d|%d|%d|%d|%s", 1,  -- Export-Format 1 (unabhaengig von der Dateiversion)
                fac, t, j.cnt, j.nItems, cmp and j.dt or 0, table.concat(j.parts, ";")))
            j.parts = nil
            M.TrimExport(s.export)
            QueueScan(t, j.changed, nil, j.ids)
            return true
        end
        if budget and M.api.ms() - t0 >= budget then return pause() end
    end
end
M.ApplyPortion = function(budget) if M.applyJob then return ApplyPortion(M.applyJob, budget) end return true end

-- v3: Export kuerzen – hoechstens EXPORT_KEEP Scans und EXPORT_MAX_BYTES zusammen, der neueste bleibt immer
function M.TrimExport(list)
    if type(list) ~= "table" then return end
    while #list > M.EXPORT_KEEP do table.remove(list, 1) end
    local total = 0
    for _, x in ipairs(list) do total = total + #tostring(x) end
    while #list > 1 and total > M.EXPORT_MAX_BYTES do
        total = total - #tostring(list[1])
        table.remove(list, 1)
    end
end

-- v9: legt nur den Auftrag an (gerechnet wird in ApplyPortion im Takt)
local function FinishRead(r)
    if not Fac() then return end
    if M.applyJob then while M.applyJob and not ApplyPortion(M.applyJob, nil) do end end   -- alter Auftrag zuerst ganz
    local j = { t = r.t, cnt = r.cnt, items = r.items, dt = M.prev and (r.t - M.prev.t) or 0,
                prevItems = M.prev and M.prev.items, ms = 0, frames = 0, phase = "apply" }
    if M.prev and M.prev.sigs and r.t - M.prev.t >= M.CMP_MIN and r.t - M.prev.t <= M.CMP_MAX then
        j.phase, j.prevSigs, j.curSigs, j.gone, j.new = "cmp1", M.prev.sigs, r.sigs, {}, {}
        M.stats.compared = M.stats.compared + 1
    end
    M.stats.lastMs, M.stats.lastFrames = r.ms, r.frames
    M.prev = { t = r.t, sigs = r.sigs, items = r.items }
    M.applyJob = j
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

-- v5: Feed nimmt nur an (Liste der Item-IDs) und rechnet im Tick in Portionen (FeedPortion)
local FeedPortion, FeedFinish
function M.Feed(addon, t, n, items, dt)
    M.feedUntil = nil
    if not M.hosts[addon] or type(items) ~= "table" or not M.IsShareOn() then return end
    if M.feedJob then                       -- alter Feed noch nicht fertig: zuerst ganz zu Ende rechnen
        while M.feedJob and not FeedPortion(M.feedJob, nil) do end
    end
    if M.applyJob then                      -- v9: Auswertung eines eigenen Scans zuerst ganz (sonst ueberschreibt sie neuere Werte)
        while M.applyJob and not ApplyPortion(M.applyJob, nil) do end
    end
    t, dt = tonumber(t) or M.api.time(), tonumber(dt) or 0
    local ids = {}
    for id in pairs(items) do ids[#ids + 1] = id end
    M.stats.fed = (M.stats.fed or 0) + 1
    M.prev = nil                -- naechstes eigenes Lesen vergleicht nicht mit einem Feed (keine Signaturen)
    M.feedJob = { t = t, tEnc = Enc(t), cnt = tonumber(n) or 0, dt = dt, src = items, ids = ids, i = 0, changed = {},
                  partsA = {}, partsB = {}, nA = 0, nB = 0, ms = 0, frames = 0 }
end

-- eine Portion rechnen; budget = ms (nil = ohne Grenze). Rueckgabe true, wenn fertig.
FeedPortion = function(j, budget)
    local f = Fac()
    if not f then M.feedJob = nil; return true end
    local t0 = M.api.ms()
    local ids, src = j.ids, j.src
    local cmpOn = j.dt > 0
    while j.i < #ids do
        j.i = j.i + 1
        local id = tonumber(ids[j.i])
        local it = src[ids[j.i]]
        if id and IsTestID(id) then
            Drop("test-id")                  -- v8: Test-IDs der Testroutinen nie annehmen
        elseif id and type(it) == "table" then
            local p, q, a = math.floor(tonumber(it.preis) or 0), math.floor(tonumber(it.menge) or 0), math.floor(tonumber(it.n) or 0)
            local hasAbg = cmpOn and it.abg ~= nil
            local g = hasAbg and math.floor(tonumber(it.abg) or 0) or 0
            local lo = hasAbg and math.min(g, math.floor(tonumber(it.abgV) or g)) or 0
            local op, oo, og, oh, ol = UnpackVals(f.i[id])
            local eg, eh, el = og or 0, oh or 0, ol or 0
            if hasAbg then eg, el, eh = eg + g, el + lo, eh + j.dt end
            if not op or oo ~= 0 or (op or 0) == 0 or math.abs(p - op) / op >= M.NET_CHANGE then
                j.changed[#j.changed + 1] = id
            end
            local sp, sq, sa = Enc(p), Enc(q), Enc(a)
            f.i[id] = sp .. "," .. sq .. "," .. sa .. "," .. j.tEnc .. ",0," .. Enc(eg) .. "," .. Enc(eh) .. "," .. Enc(el)
            local part = Enc(id) .. "," .. sp .. "," .. sq .. "," .. sa .. "," .. Enc(g) .. "," .. Enc(lo)
            if hasAbg or not cmpOn then j.nA = j.nA + 1; j.partsA[j.nA] = part
            else j.nB = j.nB + 1; j.partsB[j.nB] = part end
        end
        if budget and (j.i % M.CHECK_EVERY == 0) and M.api.ms() - t0 >= budget then break end
    end
    j.ms, j.frames = j.ms + (M.api.ms() - t0), j.frames + 1
    if j.i >= #ids then FeedFinish(j); return true end
    return false
end

FeedFinish = function(j)
    M.feedJob = nil
    local f, fac = Fac()
    if not f then return end
    f.t = j.t
    M.stats.scans = M.stats.scans + 1
    M.stats.read = j.cnt
    M.stats.lastT = j.t
    M.stats.items = j.nA + j.nB
    M.stats.lastMs, M.stats.lastFrames = j.ms, j.frames
    if j.dt > 0 then M.stats.compared = M.stats.compared + 1 end
    local s = M.store
    s.export = s.export or {}
    -- v7: Kopf an den ersten Teil haengen und einmal verbinden (keine zweite Kopie der ganzen Zeile durch string.format)
    local function Line(parts, n, t, dt)
        local head = string.format("GSMARKT1|%d|%s|%d|%d|%d|%d|", 1, fac, t, j.cnt, n, dt)
        if n == 0 then return head end
        parts[1] = head .. parts[1]
        return table.concat(parts, ";", 1, n)
    end
    table.insert(s.export, Line(j.partsA, j.nA, j.t, j.dt > 0 and j.dt or 0))
    if j.nB > 0 then           -- Items ohne Abgaenge: eigene Zeile ohne Vergleich (t+1, sonst "doppelt" bei der Sammelstelle)
        table.insert(s.export, Line(j.partsB, j.nB, j.t + 1, 0))
    end
    j.partsA, j.partsB = nil, nil
    M.TrimExport(s.export)
    QueueScan(j.t, j.changed, nil, j.ids)
end
M.FeedPortion = function(budget) if M.feedJob then return FeedPortion(M.feedJob, budget) end return true end

---------------------------------------------------------------------------
-- Teilen
---------------------------------------------------------------------------
local function Entry(id, e)
    return Enc(id) .. "," .. Enc(e.p) .. "," .. Enc(e.q) .. "," .. Enc(e.n)
end
-- v7: Eintrag direkt aus dem gespeicherten Text "p,q,n,t,o,..." (gleiche Base36-Zeichen wie Entry, ohne Hilfstabelle)
local function EntryFromText(id, v)
    local pqn = type(v) == "string" and v:match("^(%w+,%w+,%w+),")
    if pqn then return Enc(id) .. "," .. pqn end
    local e = Unpack(v)
    return e and Entry(id, e) or nil
end
M.EntryFromText = EntryFromText

-- alle eigenen Items eines Scans an die Gilde, die geaenderten (hoechstens NET_MAX) auch ins Netz
-- v9: nur noch ein Auftrag (M.queueJobs); gerechnet wird im Takt in Portionen (QueuePortion, BUDGET_MS je Bild).
--   ids = Liste der Items dieses Scans (vom Feed bekannt) -> kein Durchlauf ueber den ganzen Speicher noetig.
QueueScan = function(t, changed, full, ids)
    local f, fac = Fac()
    if not f or not M.ep or not M.IsShareOn() then return end
    local now = M.api.now()
    if not full and (not M.lastFull or now - M.lastFull >= M.FULL_EVERY) then full = true end
    if full then M.lastFull = now end
    local net = {}
    for i = 1, math.min(#changed, M.NET_MAX) do net[i] = changed[i] end
    local q = { f = f, tEnc = Enc(t), head = "S:" .. fac .. ":" .. Enc(t) .. ":", net = net, i = 0 }
    if full then
        q.step, q.src, q.all = "keys", ids, {}
    else
        local all = {}
        for i = 1, #net do all[i] = net[i] end
        q.step, q.all = "sort", all
    end
    M.queueJobs[#M.queueJobs + 1] = q
end

-- eine Portion Teilen rechnen; budget = ms (nil = ohne Grenze). Rueckgabe true, wenn alle Auftraege fertig.
local function QueueStep(q, budget, t0, first)
    local f = q.f
    local function over(i) return budget and (i % 20 == 0) and M.api.ms() - t0 >= budget end
    if q.step == "keys" then
        -- Schluessel kopieren (billig, ohne Text zu lesen) – danach wird nur noch die Kopie in Portionen geprueft
        if not q.src and budget and not first and M.api.ms() - t0 >= 1 then return "naechstes" end
        if not q.src then
            local keys = {}
            for id in pairs(f.i) do keys[#keys + 1] = id end
            q.src = keys
        end
        q.step, q.i = "filter", 0
        return false
    elseif q.step == "filter" then
        local src, all = q.src, q.all
        while q.i < #src do
            q.i = q.i + 1
            local id = tonumber(src[q.i])
            local v = id and f.i[id]
            if type(v) == "string" and not IsTestID(id) then
                local te, oe = v:match("^%w+,%w+,%w+,(%w+),(%w+),")
                if te == q.tEnc and oe == "0" then all[#all + 1] = id end
            end
            if over(q.i) then return false end
        end
        q.src, q.step = nil, "sort"
        return false
    elseif q.step == "sort" then
        -- Sortieren am Stueck (~1,5 ms bei 6000): nur mit frischem Budget beginnen, sonst im naechsten Bild
        if budget and not first and M.api.ms() - t0 >= 1 then return "naechstes" end
        table.sort(q.all)
        table.sort(q.net)
        q.step, q.list, q.opts, q.i, q.cur, q.len = "send", q.all, { scope = "guild" }, 0, {}, #q.head
        return false
    elseif q.step == "send" then
        local S = _G.GoldSentinelSync
        local max = (S and S.MAX_PAYLOAD) or 230
        local list, head = q.list, q.head
        while q.i < #list do
            q.i = q.i + 1
            local id = list[q.i]
            local v = f.i[id]
            -- nur Eintraege dieses Scans (ein neuerer Scan schickt neuere Werte selbst)
            local te = type(v) == "string" and v:match("^%w+,%w+,%w+,(%w+),")
            local e = (te == q.tEnc) and EntryFromText(id, v) or nil
            if e then
                if #q.cur > 0 and (#q.cur >= M.ITEMS_PER_MSG or q.len + 1 + #e > max) then
                    M.outbox[#M.outbox + 1] = { head .. table.concat(q.cur, ";"), q.opts }
                    q.cur, q.len = {}, #head
                end
                q.cur[#q.cur + 1] = e
                q.len = q.len + #e + 1
            end
            if over(q.i) then return false end
        end
        if #q.cur > 0 then M.outbox[#M.outbox + 1] = { head .. table.concat(q.cur, ";"), q.opts } end
        while #M.outbox > M.OUTBOX_MAX do table.remove(M.outbox, 1); Drop("warteschlange voll") end
        if q.opts.scope == "guild" and #q.net > 0 and S and S.NET then
            q.list, q.opts, q.i, q.cur, q.len = q.net, { net = true }, 0, {}, #head
            return false
        end
        return true
    end
    return true
end

-- Rueckgabe true, wenn nichts mehr zu tun ist
function M.QueuePortion(budget)
    local t0 = M.api.ms()
    local first = true
    while M.queueJobs[1] do
        if not M.IsShareOn() then M.queueJobs = {}; return true end
        local done = QueueStep(M.queueJobs[1], budget, t0, first)
        first = false
        if done == "naechstes" then break end
        if done then table.remove(M.queueJobs, 1) end
        if budget and M.api.ms() - t0 >= budget then break end
    end
    return M.queueJobs[1] == nil
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
            if id and IsTestID(id) then
                Drop("test-id")              -- v8: Test-IDs von anderen (aelteren) Clients nie annehmen
            elseif id and p and q and n then
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
    -- v9: hoechstens EINE Rechen-Portion je Bild (Feed, Auswertung des eigenen Scans, Teilen, Lesen)
    local busy = false
    if M.feedJob and not M.api.inCombat() then
        busy = true
        local ok, e3 = pcall(FeedPortion, M.feedJob, M.BUDGET_MS)
        if not ok then M.feedJob = nil; Drop(("feed " .. tostring(e3)):sub(1, 60)) end
    elseif M.applyJob and not M.api.inCombat() then
        busy = true
        local ok, e5 = pcall(ApplyPortion, M.applyJob, M.BUDGET_MS)
        if not ok then M.applyJob = nil; Drop(("auswertung " .. tostring(e5)):sub(1, 60)) end
    elseif M.queueJobs[1] and not M.api.inCombat() then
        busy = true
        local ok, e4 = pcall(M.QueuePortion, M.BUDGET_MS)
        if not ok then M.queueJobs = {}; Drop(("teilen " .. tostring(e4)):sub(1, 60)) end
    end
    local r = M.reader
    if r and not busy and not M.api.inCombat() then
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
        if not M.IsShareOn() then return M.Pump() end      -- v4 (MN-S2): Schalter aus -> keine Antwort mehr
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
        "MARKT-NETZ Test-IDs entfernt: " .. tostring(s.testIds or 0),
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
        local G = _G.GoldSentinelMarkt
        if acc < 0.05 and not G.reader and not G.feedJob and not G.applyJob and not (G.queueJobs and G.queueJobs[1]) then return end
        acc = 0
        pcall(_G.GoldSentinelMarkt.Tick)
    end)
end
