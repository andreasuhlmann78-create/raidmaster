-- GSSniperLog – passives Messwerkzeug der Prüf-Sitzung (15.11.2026, Auftrag des Nutzers 14:03/14:04)
--
-- Läuft unsichtbar im Hintergrund, während der Spieler ganz normal spielt (snipen, entzaubern, verkaufen, Post holen).
-- Es schreibt ALLES rund um den AHSentinel-Sniper mit, um ihn perfekt zu machen:
--   * jede Suche (SendSearchQuery) und wie lange der Server bis zum Ergebnis braucht
--   * jedes Ergebnis des Sniper-Items: wie viele Angebote unter dem Max-Preis des Ziels lagen
--   * Angebote unter Max, die verschwanden, bevor wir sie gekauft haben ("von anderen weggeschnappt", mit Zeit)
--   * jeden gesendeten Kauf (PlaceBid / Waren-Kauf), wie viele Käufe beim Senden offen waren, doppelt gesendet?
--   * jede Antwort des Servers (gekauft, Fehler-Code, "Interner Auktion-Fehler", Drossel-Ereignisse) und die Zeit bis dahin
--   * jeden Gold-Abgang/-Zugang mit Zusammenhang (Auktionshaus, Post, Händler)
--   * die Zähler von AHSentinel (gekauft/ausgegeben je Ziel) gegen das, was wirklich passiert ist
--   * jede Wartezeit des Sniper-Status (z. B. "wartet: …") mit Dauer, Lücken zwischen zwei Suchen
--   * Bildaussetzer (längster Frame) während der Sniper läuft
--
-- Es kauft nichts, verkauft nichts, ruft keine geschützte Funktion auf und ändert kein anderes Addon (nur lesen und
-- hooksecurefunc = nachher mithören). Keine Spielernamen im Ergebnis (nur ItemIDs, Zahlen, Systemtexte ohne Namen).
--
-- 1.3 (Nutzer 15:59 "Messtool den neuen Gegebenheiten anpassen"):
--   * "Server bereit" wird VOR der Anfrage gemessen (Stand am Ende des vorigen Bildes + Drossel-Ereignis SYSTEM_READY);
--     1.2 las den Wert im Nach-Hook, also nach der eigenen Anfrage -> Zahl war wertlos. Dazu: "n. Anfrage im selben Bild".
--   * Doppelt gesendet getrennt: DOPPELT (erster Kauf noch offen / schon gekauft) gegen WIEDERHOLT (nach Fehler oder ohne Antwort)
--   * Vollscan-Antworten zusammengefasst (eine Zeile je Scan statt tausender), Zusammenfassungen getrennt aufbewahrt
--   * Ruhemodus: Sekunden mit Sniper an, laufende AHS-Aufgaben in dieser Zeit, Anfragen ans AH nach Quelle (Addon/Datei)
--   * Rasten ohne Kauf nach Sniper-Status, Suchen je Ziel-Item mit/ohne Treffer
--
-- 1.4 (Protokoll 15.11. 16:45: "Rasten 0" trotz 14 Käufen): Mausrad über AHSentinel-Fenstern zählt als Raste, wenn ein
--   Treffer wartet (AHSentinel kauft dort über Sn:WheelBuy statt über die Knöpfe); Minuten-Zeile "Rasten über: …".
--
-- Ergebnis: beim Ausloggen oder /reload als "GSDIAG1|GSSniperLog|…" in GSSniperLogDB.export -> der RaidMasterUploader
-- bringt es nach testberichte/diagnose/GSSniperLog/. Befehl: /gssl (Stand), /gssl aus|an, /gssl leeren.

local ADDON, VERSION = "GSSniperLog", "1.4"
local MAXLOG = 6000            -- Zeilen im Speicher (älteste fallen weg)
local EXPORT_MAX = 400000      -- Zeichen in der Ausgabe für den Uploader
local CONFIRM_MAX = 30         -- Sekunden: ohne Antwort gilt ein Kauf als "keine Bestätigung"
local PAUSE_LOG = 3            -- Sekunden ohne Sniper-Suche (Sniper an, AH offen) -> als Pause festhalten
local SPIKE_MS = 100           -- längere Frames werden einzeln festgehalten
local RESULT_MAX = 60          -- so viele Angebote je Ergebnis werden gelesen
local SUMMAX = 800             -- 1.3: Zusammenfassungs-Zeilen (Minute, Bilder, Addons, Pausen, Ruhe) getrennt aufbewahren
local SUM_EXPORT = 120000      -- 1.3: davon höchstens so viele Zeichen in der Ausgabe
local SUMCAT = { MINUTE = true, BILDER = true, ADDONS = true, PAUSE = true, SITZUNG = true, AH = true, RUHE = true, VOLLSCAN = true }

local B = { on = true, bids = {}, sent = {}, searches = {}, offers = {}, tot = {}, min = {}, buckets = {},
            ah = false, mail = false, merchant = false, lastMoney = nil, status = nil, statusT = nil,
            ahsCount = {}, lastSearchT = nil, maxFrame = 0, maxFrameMin = 0, spikes = 0 }
_G.GSSniperLog = B

---------------------------------------------------------------------------
-- Hilfen
---------------------------------------------------------------------------
local function Now() return (GetTime and GetTime()) or 0 end
-- Uhrzeit auf 0,1 s: Sekunden aus der Spielzeit (GetTime) ab dem Start, damit die Zehntel zur Sekunde passen
local clockBase, getBase
local function Clock()
    local t = Now()
    if not clockBase then clockBase, getBase = (time and time()) or 0, t end
    local el = t - getBase
    local sec = clockBase + math.floor(el)
    return string.format("%s.%d", (date and date("%H:%M:%S", sec)) or "?", math.floor((el * 10) % 10))
end
local function Print(s)
    if DEFAULT_CHAT_FRAME and DEFAULT_CHAT_FRAME.AddMessage then
        DEFAULT_CHAT_FRAME:AddMessage("|cff33ccff[GSSniperLog]|r " .. tostring(s))
    end
end
local function Clean(s)
    s = tostring(s or "")
    s = s:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("|H.-|h(.-)|h", "%1"):gsub("|T.-|t", ""):gsub("|A.-|a", "")
    s = s:gsub("[\r\n]", " "):gsub("|", "/")
    return s
end
local function Money(c)
    c = math.floor(tonumber(c) or 0)
    local neg = c < 0
    if neg then c = -c end
    local g, s, k = math.floor(c / 10000), math.floor((c % 10000) / 100), c % 100
    local out
    if g > 0 then out = string.format("%dg%02ds%02dc", g, s, k)
    elseif s > 0 then out = string.format("%ds%02dc", s, k)
    else out = string.format("%dc", k) end
    return (neg and "-" or "") .. out
end
local function Inc(t, k, n) t[k] = (t[k] or 0) + (n or 1) end
local function DB()
    GSSniperLogDB = type(GSSniperLogDB) == "table" and GSSniperLogDB or {}
    local d = GSSniperLogDB
    if type(d.log) ~= "table" then d.log = {} end
    return d
end
local function Log(kat, text)
    if not B.on then return end
    local d = DB()
    local line = Clock() .. " " .. kat .. " " .. Clean(text)
    d.log[#d.log + 1] = line
    if SUMCAT[kat] then
        if type(d.sum) ~= "table" then d.sum = {} end
        d.sum[#d.sum + 1] = line
        if #d.sum > SUMMAX + 100 then
            local keep = {}
            for i = #d.sum - SUMMAX + 1, #d.sum do keep[#keep + 1] = d.sum[i] end
            d.sum = keep
        end
    end
    -- in Blöcken kürzen (nicht bei jeder Zeile die ganze Liste umkopieren)
    if #d.log > MAXLOG + 500 then
        local keep = {}
        for i = #d.log - MAXLOG + 1, #d.log do keep[#keep + 1] = d.log[i] end
        d.log = keep
    end
end
local function GetMoneyNow() return (GetMoney and GetMoney()) or 0 end
local function ItemIDOfKey(k)
    if type(k) == "table" then return tonumber(k.itemID) end
    return tonumber(k)
end
local function AHOpen()
    if B.ah then return true end
    local f = _G.AuctionHouseFrame or _G.AuctionFrame
    return (f and f.IsShown and f:IsShown()) and true or false
end

---------------------------------------------------------------------------
-- AHSentinel nur LESEN (nie ändern)
---------------------------------------------------------------------------
local function AHS()
    local A = _G.AHAnalyzerPro
    if type(A) ~= "table" then return nil end
    return A
end
local function SniperDB()
    local A = AHS()
    return A and type(A.db) == "table" and type(A.db.sniper) == "table" and A.db.sniper or nil
end
local function SniperArmed()
    local s = SniperDB()
    return s and s.armed and true or false
end
-- Ziele: itemID -> { max, bought, spent, budget, qty }
local function Targets()
    local out = {}
    local s = SniperDB()
    if not (s and type(s.targets) == "table") then return out end
    for key, t in pairs(s.targets) do
        if type(t) == "table" then
            local id = tonumber(t.itemID) or (type(key) == "string" and tonumber(key:match("(%d+)")))
            if id then
                out[id] = { key = tostring(key), max = tonumber(t.maxPrice) or 0, bought = tonumber(t.bought) or 0,
                            spent = tonumber(t.spent) or 0, budget = tonumber(t.budget) or 0, qty = tonumber(t.qty) or 0 }
            end
        end
    end
    return out
end
local function StatusText()
    local A = AHS()
    local Sn = A and A.Sniper
    if not (Sn and type(Sn.GetStatusText) == "function") then return nil end
    local ok, s = pcall(Sn.GetStatusText, Sn)
    if not ok then return nil end
    return Clean(s)
end

---------------------------------------------------------------------------
-- Suchen und Ergebnisse
---------------------------------------------------------------------------
local function NoteCall(kind)
    B.lastCall, B.lastCallT = kind, Now()
    B.callsInFrame = (B.callsInFrame or 0) + 1
end
-- Ist die Drossel des Auktionshauses gerade bereit? (nil = unbekannt)
local function ServerReady()
    local C = _G.C_AuctionHouse
    if not (C and C.IsThrottledMessageSystemReady) then return nil end
    local ok, r = pcall(C.IsThrottledMessageSystemReady)
    if not ok then return nil end
    return r and true or false
end
B.ServerReady = ServerReady
-- 1.3: Bereitschaft VOR der Anfrage = Stand am Ende des vorigen Bildes (bzw. SYSTEM_READY danach). Zweiter Wert: wie viele
-- Anfragen in diesem Bild schon vorher gingen (dann ist der Stand für diese Anfrage nicht mehr sicher).
local function ReadyBefore()
    return B.readyFrame, (B.callsInFrame or 0)
end
B.ReadyBefore = ReadyBefore
-- 1.3: Wer hat die Anfrage gestellt? Aus dem Aufrufstapel das erste Addon (ohne GSSniperLog); bei AHSentinel die erste Datei,
-- die nicht nur Weiterleitung ist (API.lua). Blizzard-Oberfläche = "Blizzard". Unbekannt = "?".
local PASS = { ["API.lua"] = true, ["LegacyAH.lua"] = true }
local function Source()
    local ds = _G.debugstack
    if type(ds) ~= "function" then return "?" end
    local ok, st = pcall(ds, 3, 14, 0)
    if not ok or type(st) ~= "string" then return "?" end
    local first, firstAddon
    for addon, file in st:gmatch("AddOns[/\\]([%w_%-%.]+)[/\\]([%w_%-%./\\]-%.lua)") do
        if addon ~= ADDON then
            if addon:find("^Blizzard_") then
                if not first then return "Blizzard" end
            else
                local base = file:match("([^/\\]+)$") or file
                if not first then first, firstAddon = addon .. "/" .. base, addon end
                if addon == firstAddon and not PASS[base] then return addon .. "/" .. base end
            end
        end
    end
    if first then return first end
    if st:find("Blizzard_", 1, true) or st:find("FrameXML", 1, true) then return "Blizzard" end
    return "?"
end
B.Source = Source
local function NoteSource(kind)
    local src = Source()
    B.min.src = B.min.src or {}
    Inc(B.min.src, kind .. " " .. src)
    B.tot.src = B.tot.src or {}
    Inc(B.tot.src, kind .. " " .. src)
    -- beim Snipen: alles, was nicht der Sniper von AHSentinel ist, ist "fremd" (Ruhemodus-Messung)
    if B.snipingNow and not src:find("^AHSentinel/Sniper") then
        Inc(B.min, "fremdBeimSnipen"); Inc(B.tot, "fremdBeimSnipen")
        if (B.min.fremdLog or 0) < 5 then
            Inc(B.min, "fremdLog")
            Log("ANFRAGE-FREMD", kind .. " von " .. src .. " während Sniper an")
        end
    end
    return src
end
B.NoteSource = NoteSource
B.NoteCall = NoteCall
local function NoteSearch(kind, itemID)
    local now = Now()
    local ready, before = ReadyBefore()
    NoteCall("Suche")
    if ready == false then Inc(B.tot, "sucheNichtBereit"); Inc(B.min, "sucheNichtBereit") end
    if before > 0 then Inc(B.tot, "sucheGleichesBild"); Inc(B.min, "sucheGleichesBild") end
    Inc(B.tot, "suchen"); Inc(B.min, "suchen")
    if itemID then
        B.searches[itemID] = now
        B.min.sItem = B.min.sItem or {}
        Inc(B.min.sItem, itemID)
    end
    if B.lastSearchT and SniperArmed() and AHOpen() then
        local gap = now - B.lastSearchT
        if gap > (B.min.gapMax or 0) then B.min.gapMax = gap end
    end
    B.lastSearchT = now
end

-- Angebote unter Max, die wir gesehen haben: auctionID -> { t (zuerst gesehen), price, item }
local function ReadItemResults(itemKey)
    local C = _G.C_AuctionHouse
    local id = ItemIDOfKey(itemKey)
    if not (C and id and C.GetNumItemSearchResults and C.GetItemSearchResultInfo) then return end
    local now = Now()
    local t0 = B.searches[id]
    B.searches[id] = nil                         -- nur die ERSTE Antwort auf eine Suche zählt als Antwortzeit
    local lat = t0 and (now - t0) or nil
    if lat then Inc(B.min, "latSum", lat); Inc(B.min, "latN"); if lat > (B.min.latMax or 0) then B.min.latMax = lat end end
    local tg = Targets()[id]
    -- Ergebnis vollständig? (Teil-Ergebnisse würden sonst fälschlich "verschwunden" melden)
    local full = true
    if C.HasFullItemSearchResults then
        local okF, v = pcall(C.HasFullItemSearchResults, itemKey)
        if okF and v == false then full = false end
    end
    local ok, n = pcall(C.GetNumItemSearchResults, itemKey)
    n = ok and tonumber(n) or 0
    local seen, under, cheapest = {}, 0, nil
    for i = 1, math.min(n, RESULT_MAX) do
        local ok2, info = pcall(C.GetItemSearchResultInfo, itemKey, i)
        if ok2 and type(info) == "table" and info.auctionID and info.buyoutAmount and info.buyoutAmount > 0 then
            local unit = math.floor(info.buyoutAmount / math.max(1, info.quantity or 1))
            if not cheapest or unit < cheapest then cheapest = unit end
            if tg and tg.max > 0 and unit <= tg.max and not info.containsOwnerItem then
                under = under + 1
                local aid = info.auctionID
                seen[aid] = true
                if not B.offers[aid] then B.offers[aid] = { t = now, price = unit, item = id } end
            end
        end
    end
    -- Angebote unter Max, die beim letzten Ergebnis dieses Items da waren und jetzt fehlen, ohne dass wir sie gesendet haben
    if tg then
        -- Verschwunden erst, wenn ein Angebot in ZWEI vollständigen Ergebnissen hintereinander fehlt
        if full then
            for aid, o in pairs(B.offers) do
                if o.item == id then
                    if seen[aid] then
                        o.miss = 0
                    else
                        o.miss = (o.miss or 0) + 1
                        if o.miss >= 2 then
                            if not B.sent[aid] then
                                Inc(B.tot, "weg"); Inc(B.min, "weg")
                                Log("WEG", string.format("Item %d · Angebot zu %s unter Max (%s) verschwand ohne unseren Kauf · war %.1f s sichtbar",
                                    id, Money(o.price), Money(tg.max), (o.last or now) - o.t))
                            end
                            B.offers[aid] = nil
                        end
                    end
                end
            end
        end
        for aid in pairs(seen) do if B.offers[aid] then B.offers[aid].last = now end end
        Inc(B.min, "unterMax", under)
        if under > 0 and lat then B.min.hItem = B.min.hItem or {}; Inc(B.min.hItem, id) end
        -- nur festhalten, wenn sich etwas ändert oder Angebote unter Max da sind (sonst 70 gleiche Zeilen je Minute)
        B.lastRes = B.lastRes or {}
        local sig = tostring(n) .. ":" .. tostring(under) .. ":" .. tostring(cheapest)
        if under > 0 or B.lastRes[id] ~= sig then
            Log("ERGEBNIS", string.format("Item %d · %d Angebote%s · %d unter Max %s · günstigstes %s · Antwort nach %s",
                id, n, full and "" or " (Teil)", under, Money(tg.max), cheapest and Money(cheapest) or "-",
                lat and string.format("%.2f s", lat) or "-"))
        end
        B.lastRes[id] = sig
    end
end

local function ReadCommodityResults(itemID)
    local C = _G.C_AuctionHouse
    local id = tonumber(itemID)
    if not (C and id and C.GetNumCommoditySearchResults and C.GetCommoditySearchResultInfo) then return end
    local now = Now()
    local t0 = B.searches[id]
    B.searches[id] = nil
    local lat = t0 and (now - t0) or nil
    if lat then Inc(B.min, "latSum", lat); Inc(B.min, "latN"); if lat > (B.min.latMax or 0) then B.min.latMax = lat end end
    local tg = Targets()[id]
    if not tg then return end
    local ok, n = pcall(C.GetNumCommoditySearchResults, id)
    n = ok and tonumber(n) or 0
    local qty, cheapest = 0, nil
    for i = 1, math.min(n, RESULT_MAX) do
        local ok2, info = pcall(C.GetCommoditySearchResultInfo, id, i)
        if ok2 and type(info) == "table" and info.unitPrice then
            if not cheapest or info.unitPrice < cheapest then cheapest = info.unitPrice end
            if tg.max > 0 and info.unitPrice <= tg.max and not info.containsOwnerItem then qty = qty + (info.quantity or 0) end
        end
    end
    Inc(B.min, "unterMax", qty > 0 and 1 or 0)
    B.lastRes = B.lastRes or {}
    local sig = tostring(n) .. ":" .. tostring(qty) .. ":" .. tostring(cheapest)
    if qty > 0 or B.lastRes[id] ~= sig then
        Log("ERGEBNIS", string.format("Ware %d · %d Preisstufen · %d Stück unter Max %s · günstigstes %s · Antwort nach %s",
            id, n, qty, Money(tg.max), cheapest and Money(cheapest) or "-", lat and string.format("%.2f s", lat) or "-"))
    end
    B.lastRes[id] = sig
end

---------------------------------------------------------------------------
-- Käufe senden und Antworten
---------------------------------------------------------------------------
local function OpenCount()
    local n = 0
    for _, b in pairs(B.bids) do if not b.done and not b.late then n = n + 1 end end
    return n
end
local function Bucket(open) return open >= 2 and "≥2" or tostring(open) end

local function NoteBid(auctionID, amount, src)
    local now = Now()
    local ready, before = ReadyBefore()
    NoteCall("Kauf")
    local open = OpenCount()
    if ready == false then Inc(B.tot, "kaufNichtBereit"); Inc(B.min, "kaufNichtBereit") end
    if before > 0 then Inc(B.tot, "kaufGleichesBild"); Inc(B.min, "kaufGleichesBild") end
    -- Raste -> Senden (Mausrad/Taste von AHSentinel)
    local raste
    if B.rasteT and now - B.rasteT < 1 then
        raste = now - B.rasteT
        B.rasteT, B.rasteSt = nil, nil
        Inc(B.min, "rasteSum", raste); Inc(B.min, "rasteN")
    end
    -- 1.3: doppelt = derselbe Kauf, während der erste noch offen ist oder schon gekauft wurde; wiederholt = nach Fehler/ohne Antwort
    local prior = B.bids[auctionID]
    local dup, rep
    if B.sent[auctionID] then
        if prior and prior.ok then dup = "schon gekauft"
        elseif prior and not prior.done and not prior.late and not prior.err then dup = "erster Kauf noch offen"
        else rep = prior and (prior.err and ("nach " .. tostring(prior.err)) or (prior.late and "nach keiner Antwort") or "nach Fehler") or "nach Fehler" end
    end
    B.sent[auctionID] = now
    local o = B.offers[auctionID]
    local seen = o and (now - o.t) or nil
    B.bids[auctionID] = { t = now, amount = tonumber(amount) or 0, open = open, dup = dup, money = GetMoneyNow(),
                          item = o and o.item or nil }
    Inc(B.tot, "gesendet"); Inc(B.min, "gesendet")
    if dup then Inc(B.tot, "doppelt"); Inc(B.min, "doppelt") end
    if rep then Inc(B.tot, "wiederholt"); Inc(B.min, "wiederholt") end
    local bk = B.buckets[Bucket(open)] or { n = 0, ok = 0 }
    B.buckets[Bucket(open)] = bk
    bk.n = bk.n + 1
    Log("KAUF-GESENDET", string.format("Angebot %s · %s · offen beim Senden %d · Server bereit (vorher) %s%s%s%s%s%s%s", tostring(auctionID), Money(amount), open,
        ready == nil and "?" or (ready and "ja" or "NEIN"), before > 0 and string.format(" · %d. Anfrage im selben Bild", before + 1) or "",
        src and (" · von " .. src) or "", dup and (" · DOPPELT GESENDET (" .. dup .. ")") or "", rep and (" · WIEDERHOLT (" .. rep .. ")") or "",
        seen and string.format(" · %.2f s nach erstem Sehen", seen) or "", raste and string.format(" · %d ms nach der Raste", math.floor(raste * 1000)) or ""))
end

local function ResolveBid(auctionID, how)
    local b = auctionID and B.bids[auctionID]
    local now = Now()
    if not b then
        Log("KAUF-OK", string.format("Angebot %s · Bestätigung ohne eigenen Sendevorgang (%s)", tostring(auctionID), how))
        Inc(B.tot, "okFremd")
        return
    end
    if b.done then
        Log("KAUF-OK", string.format("Angebot %s · zweite Bestätigung (%s)", tostring(auctionID), how))
        return
    end
    b.done, b.ok = true, true
    local lat = now - b.t
    Inc(B.tot, "gekauft"); Inc(B.min, "gekauft")
    Inc(B.tot, "summe", b.amount); Inc(B.min, "summe", b.amount)
    if b.late then Inc(B.tot, "spaet") end
    local bk = B.buckets[Bucket(b.open)]
    if bk then bk.ok = bk.ok + 1 end
    Inc(B.min, "antwortSum", lat); Inc(B.min, "antwortN")
    if lat > (B.min.antwortMax or 0) then B.min.antwortMax = lat end
    Log("KAUF-OK", string.format("Angebot %s · %s · Antwort nach %.2f s%s", tostring(auctionID), Money(b.amount), lat,
        b.late and " (SPÄT, nach der Frist)" or ""))
end

local function OldestOpen()
    local best, bid
    for aid, b in pairs(B.bids) do
        if not b.done and not b.late and (not best or b.t < best.t) then best, bid = b, aid end
    end
    return bid, best
end

local function CheckTimeouts()
    local now = Now()
    for aid, b in pairs(B.bids) do
        if not b.done and not b.late and now - b.t > CONFIRM_MAX then
            b.late = true
            Inc(B.tot, "ohneAntwort"); Inc(B.min, "ohneAntwort")
            Log("KAUF-OFFEN", string.format("Angebot %s · %s · keine Bestätigung in %d s (Fehler gesehen: %s)", tostring(aid),
                Money(b.amount), CONFIRM_MAX, b.err and tostring(b.err) or "nein"))
        end
        -- nach 10 Min. aus dem Speicher
        if now - b.t > 600 then B.bids[aid] = nil end
    end
    for aid, t in pairs(B.sent) do if now - t > 600 then B.sent[aid] = nil end end
    for aid, o in pairs(B.offers) do if now - o.t > 600 then B.offers[aid] = nil end end
end

---------------------------------------------------------------------------
-- Gold
---------------------------------------------------------------------------
local function NoteMoney()
    local m = GetMoneyNow()
    if B.lastMoney == nil then B.lastMoney = m; return end
    local d = m - B.lastMoney
    B.lastMoney = m
    if d == 0 then return end
    local ctx
    if B.merchant then ctx = "Händler"
    elseif AHOpen() then
        local recentBid = false
        for _, b in pairs(B.bids) do if Now() - b.t < 60 then recentBid = true break end end
        if d < 0 and B.lastPost and Now() - B.lastPost < 5 then ctx = "AH Einstellgebühr"
        elseif d < 0 and recentBid then ctx = "AH Kauf"
        elseif d < 0 then ctx = "AH (ohne Kauf in den letzten 60 s)"
        else ctx = "AH Eingang" end
    elseif B.mail then ctx = "Post"
    else ctx = "sonst" end
    if ctx == "AH Kauf" then Inc(B.tot, "goldKauf", -d); Inc(B.min, "goldKauf", -d) end
    Inc(B.tot, "gold " .. ctx, d)
    Log("GOLD", string.format("%s%s · %s · jetzt %s", d > 0 and "+" or "", Money(d), ctx, Money(m)))
end

---------------------------------------------------------------------------
-- AHSentinel-Zähler und Status beobachten
---------------------------------------------------------------------------
local function WatchAHS()
    local tg = Targets()
    for id, t in pairs(tg) do
        local prev = B.ahsCount[id]
        if prev and (prev.bought ~= t.bought or prev.spent ~= t.spent) then
            local db, ds = t.bought - prev.bought, t.spent - prev.spent
            Inc(B.tot, "ahsGekauft", db); Inc(B.min, "ahsGekauft", db)
            Inc(B.tot, "ahsAusgegeben", ds); Inc(B.min, "ahsAusgegeben", ds)
            Log("AHS-ZÄHLER", string.format("Item %d · gekauft %d -> %d (%+d) · ausgegeben %s -> %s (%s)", id, prev.bought, t.bought, db,
                Money(prev.spent), Money(t.spent), Money(ds)))
        elseif not prev then
            Log("AHS-ZIEL", string.format("Item %d · Max %s · Menge %d · Budget %s · gekauft %d · ausgegeben %s", id, Money(t.max), t.qty,
                Money(t.budget), t.bought, Money(t.spent)))
        end
        B.ahsCount[id] = { bought = t.bought, spent = t.spent }
    end
    local st = StatusText()
    if st and st ~= B.status then
        local now = Now()
        if B.status and B.statusT then
            Log("AHS-STATUS", string.format("%.1f s: %s", now - B.statusT, B.status))
        end
        B.status, B.statusT = st, now
    end
    -- Pause: Sniper an, AH offen, länger keine Suche
    if SniperArmed() and AHOpen() and B.lastSearchT then
        local gap = Now() - B.lastSearchT
        if gap >= PAUSE_LOG and not B.pauseOpen then
            B.pauseOpen = true
            B.pauseStart = B.lastSearchT
        end
    end
end

---------------------------------------------------------------------------
-- Minuten-Zusammenfassung
---------------------------------------------------------------------------
local function RuheMinute(m)
    if (m.snipeSec or 0) == 0 and not m.src then return end
    local function List(t, fmt)
        local arr = {}
        for k, v in pairs(t or {}) do arr[#arr + 1] = { k, v } end
        table.sort(arr, function(a, b) if a[2] ~= b[2] then return a[2] > b[2] end return tostring(a[1]) < tostring(b[1]) end)
        local out = {}
        for i = 1, math.min(10, #arr) do out[#out + 1] = fmt(arr[i][1], arr[i][2]) end
        return #out > 0 and table.concat(out, ", ") or "keine"
    end
    Log("RUHE", string.format("Sniper an (AH offen) %d s · AHS-Aufgaben liefen dabei: %s · Anfragen nach Quelle: %s · fremd beim Snipen %d",
        m.snipeSec or 0, List(m.jobSec, function(k, v) return k .. " " .. v .. " s" end),
        List(m.src, function(k, v) return k .. " " .. v end), m.fremdBeimSnipen or 0))
end
local function MinuteSummary()
    local m = B.min
    pcall(RuheMinute, m)
    if (m.suchen or 0) == 0 and (m.gesendet or 0) == 0 and (m.weg or 0) == 0 then
        B.min = {}
        B.maxFrameMin = 0
        return
    end
    local parts = {}
    parts[#parts + 1] = string.format("Suchen %d (Ø Antwort %s, längste %s, längste Lücke %s)", m.suchen or 0,
        (m.latN or 0) > 0 and string.format("%.2f s", m.latSum / m.latN) or "-",
        m.latMax and string.format("%.2f s", m.latMax) or "-", m.gapMax and string.format("%.1f s", m.gapMax) or "-")
    parts[#parts + 1] = string.format("gesendet %d · gekauft %d · ohne Antwort %d · doppelt %d · wiederholt %d · Fehler %d · weggeschnappt %d",
        m.gesendet or 0, m.gekauft or 0, m.ohneAntwort or 0, m.doppelt or 0, m.wiederholt or 0, m.fehler or 0, m.weg or 0)
    parts[#parts + 1] = string.format("Antwortzeit Ø %s, längste %s",
        (m.antwortN or 0) > 0 and string.format("%.2f s", m.antwortSum / m.antwortN) or "-",
        m.antwortMax and string.format("%.2f s", m.antwortMax) or "-")
    parts[#parts + 1] = string.format("Summe bestätigt %s · Gold-Abgang AH-Kauf %s · AHSentinel gezählt +%d / %s",
        Money(m.summe or 0), Money(m.goldKauf or 0), m.ahsGekauft or 0, Money(m.ahsAusgegeben or 0))
    parts[#parts + 1] = string.format("Rasten %d (ohne Kauf %d, Raste->Senden Ø %s) · Server nicht bereit (vorher): Käufe %d, Suchen %d · im selben Bild wie eine andere Anfrage: Käufe %d, Suchen %d",
        m.rasten or 0, m.rasteOhne or 0, (m.rasteN or 0) > 0 and string.format("%d ms", math.floor(m.rasteSum / m.rasteN * 1000)) or "-",
        m.kaufNichtBereit or 0, m.sucheNichtBereit or 0, m.kaufGleichesBild or 0, m.sucheGleichesBild or 0)
    local function List(t, fmt)
        local arr = {}
        for k, v in pairs(t or {}) do arr[#arr + 1] = { k, v } end
        table.sort(arr, function(a, b) if a[2] ~= b[2] then return a[2] > b[2] end return tostring(a[1]) < tostring(b[1]) end)
        local out = {}
        for i = 1, math.min(8, #arr) do out[#out + 1] = fmt(arr[i][1], arr[i][2]) end
        return table.concat(out, ", ")
    end
    if m.rasteSrc then
        parts[#parts + 1] = "Rasten über: " .. List(m.rasteSrc, function(k, v) return k .. " " .. v end)
    end
    if m.rasteOhneSt then
        parts[#parts + 1] = "ohne Kauf nach Status: " .. List(m.rasteOhneSt, function(k, v) return k .. " " .. v end)
    end
    if m.sItem then
        parts[#parts + 1] = "Suchen je Item: " .. List(m.sItem, function(k, v) return string.format("%s %d (mit Treffer %d)", tostring(k), v, (m.hItem and m.hItem[k]) or 0) end)
    end
    Log("MINUTE", table.concat(parts, " · "))
    B.min = {}
    B.maxFrameMin = 0
end

---------------------------------------------------------------------------
-- Ausgabe für den Uploader
---------------------------------------------------------------------------
local function SummaryLines()
    local t = B.tot
    local out = {}
    out[#out + 1] = string.format("Sitzung seit %s · Suchen %d · gesendet %d · gekauft %d (davon spät %d) · ohne Antwort %d · doppelt gesendet %d · wiederholt nach Fehler/ohne Antwort %d · Fehler %d",
        B.startClock or "?", t.suchen or 0, t.gesendet or 0, t.gekauft or 0, t.spaet or 0, t.ohneAntwort or 0, t.doppelt or 0, t.wiederholt or 0, t.fehler or 0)
    out[#out + 1] = string.format("Weggeschnappt (Angebot unter Max verschwand ohne unseren Kauf): %d", t.weg or 0)
    local bk = {}
    for _, k in ipairs({ "0", "1", "≥2" }) do
        local x = B.buckets[k]
        if x then bk[#bk + 1] = string.format("offen %s: %d/%d gekauft (%d %%)", k, x.ok, x.n, math.floor(x.ok / math.max(1, x.n) * 100 + 0.5)) end
    end
    out[#out + 1] = "Erfolg nach offenen Käufen beim Senden: " .. (#bk > 0 and table.concat(bk, " · ") or "keine Käufe")
    out[#out + 1] = string.format("Gold: bestätigte Käufe %s · Gold-Abgang bei AH-Kauf %s · Differenz %s · AHSentinel gezählt %d Stück / %s",
        Money(t.summe or 0), Money(t.goldKauf or 0), Money((t.goldKauf or 0) - (t.summe or 0)), t.ahsGekauft or 0, Money(t.ahsAusgegeben or 0))
    local g = {}
    for k, v in pairs(t) do if type(k) == "string" and k:find("^gold ") then g[#g + 1] = k:sub(6) .. " " .. Money(v) end end
    table.sort(g)
    out[#out + 1] = "Gold je Zusammenhang: " .. (#g > 0 and table.concat(g, " · ") or "-")
    local e = {}
    for k, v in pairs(B.errs or {}) do e[#e + 1] = k .. " ×" .. v end
    table.sort(e)
    out[#out + 1] = "Fehler/Server-Meldungen: " .. (#e > 0 and table.concat(e, " · ") or "keine")
    out[#out + 1] = string.format("Bildaussetzer > %d ms: %d · längster Frame %d ms (Ursachen je Aussetzer in den Zeilen BILD, je Minute BILDER und ADDONS)",
        SPIKE_MS, B.spikes or 0, math.floor((B.maxFrame or 0) * 1000))
    out[#out + 1] = string.format("Rasten %d (ohne Kauf %d) · Server nicht bereit (Stand VOR der Anfrage): Käufe %d, Suchen %d · im selben Bild wie eine andere Anfrage: Käufe %d, Suchen %d",
        t.rasten or 0, t.rasteOhne or 0, t.kaufNichtBereit or 0, t.sucheNichtBereit or 0, t.kaufGleichesBild or 0, t.sucheGleichesBild or 0)
    local src = {}
    for k, v in pairs(t.src or {}) do src[#src + 1] = { k, v } end
    table.sort(src, function(a, b) if a[2] ~= b[2] then return a[2] > b[2] end return a[1] < b[1] end)
    local sp = {}
    for i = 1, math.min(10, #src) do sp[#sp + 1] = src[i][1] .. " " .. src[i][2] end
    out[#out + 1] = string.format("Anfragen ans AH nach Quelle: %s · davon fremd während Sniper an: %d · Sniper an (AH offen) %d s",
        #sp > 0 and table.concat(sp, ", ") or "-", t.fremdBeimSnipen or 0, t.snipeSec or 0)
    out[#out + 1] = string.format("Vollscan-Antworten: %d (in %d Schüben)", t.vsAntworten or 0, t.vsSchuebe or 0)
    local A = AHS()
    out[#out + 1] = "AHSentinel-Version: " .. tostring(A and A.version or "nicht geladen")
    return out
end

local function BuildExport()
    local d = DB()
    local lines = {}
    lines[#lines + 1] = string.format("GSSniperLog %s · %s · Client %s (%s)", VERSION, (date and date("%d.%m.%Y %H:%M")) or "?",
        tostring((GetBuildInfo and select(1, GetBuildInfo())) or "?"), tostring((GetBuildInfo and select(4, GetBuildInfo())) or "?"))
    lines[#lines + 1] = ""
    lines[#lines + 1] = "== Zusammenfassung (diese Sitzung)"
    for _, s in ipairs(SummaryLines()) do lines[#lines + 1] = "  " .. s end
    lines[#lines + 1] = ""
    -- 1.3: Zusammenfassungen (Minute, Bilder, Addons, Pausen, Ruhe, Vollscan) gehen nie verloren
    local sum = type(d.sum) == "table" and d.sum or {}
    lines[#lines + 1] = string.format("== Minuten, Pausen, Ruhe (%d, neueste zuerst)", #sum)
    local ssize = 0
    for i = #sum, 1, -1 do
        local s = sum[i]
        if ssize + #s + 1 > SUM_EXPORT then break end
        lines[#lines + 1] = s
        ssize = ssize + #s + 1
    end
    lines[#lines + 1] = ""
    lines[#lines + 1] = string.format("== Einträge (%d, neueste zuerst)", #d.log)
    local size = 0
    for _, s in ipairs(lines) do size = size + #s + 1 end
    for i = #d.log, 1, -1 do
        local s = d.log[i]
        if size + #s + 1 > EXPORT_MAX then break end
        lines[#lines + 1] = s
        size = size + #s + 1
    end
    d.export = "GSDIAG1|" .. ADDON .. "|" .. VERSION .. "|" .. table.concat(lines, "\n")
    return d.export
end
B.BuildExport = BuildExport
B.SummaryLines = SummaryLines

---------------------------------------------------------------------------
-- Systemmeldungen einordnen (nur die Art, nie der Text mit Namen)
---------------------------------------------------------------------------
local SYS = {}
local function Pattern(gs)
    if type(gs) ~= "string" or gs == "" then return nil end
    local p = gs:gsub("([%(%)%.%+%-%*%?%[%]%^%$])", "%%%1"):gsub("%%%%s", ".-"):gsub("%%%%d", "%%d+")
    p = p:gsub("%%s", ".-"):gsub("%%d", "%%d+")
    return "^" .. p .. "$"
end
local function BuildSys()
    SYS = {}
    for _, e in ipairs({ { "ERR_AUCTION_WON_S", "gewonnen" }, { "ERR_AUCTION_BID_PLACED", "Gebot akzeptiert" },
        { "ERR_AUCTION_STARTED", "Auktion erstellt" }, { "ERR_AUCTION_REMOVED", "Auktion abgebrochen" },
        { "ERR_AUCTION_SOLD_S", "verkauft" }, { "ERR_AUCTION_EXPIRED_S", "abgelaufen" },
        { "ERR_AUCTION_OUTBID_S", "überboten" }, { "ERR_AUCTION_REMOVED_S", "entfernt" } }) do
        local p = Pattern(_G[e[1]])
        if p then SYS[#SYS + 1] = { p = p, k = e[2] } end
    end
end
local function ClassifySystem(msg)
    if type(msg) ~= "string" then return nil end
    for _, e in ipairs(SYS) do
        local ok, hit = pcall(string.find, msg, e.p)
        if ok and hit then return e.k end
    end
    return nil
end

---------------------------------------------------------------------------
-- Hooks (nur nachher mithören)
---------------------------------------------------------------------------
local hooked = false
local function Hook()
    if hooked then return end
    local C = _G.C_AuctionHouse
    if type(C) ~= "table" or type(hooksecurefunc) ~= "function" then return end
    hooked = true
    local function H(name, fn)
        if type(C[name]) == "function" then pcall(hooksecurefunc, C, name, function(...) if B.on then pcall(fn, ...) end end) end
    end
    H("SendSearchQuery", function(itemKey) NoteSource("Suche"); NoteSearch("Einzel", ItemIDOfKey(itemKey)) end)
    H("SendSellSearchQuery", function(itemKey) NoteSource("Verkaufssuche"); NoteSearch("Verkauf", ItemIDOfKey(itemKey)) end)
    H("SendBrowseQuery", function() NoteSource("Durchsuchen"); NoteSearch("Durchsuchen", nil) end)
    H("ReplicateItems", function() local src = NoteSource("Vollscan"); B.vollscanT = Now(); Inc(B.tot, "vollscans"); Log("VOLLSCAN", "gestartet von " .. src) end)
    H("PlaceBid", function(auctionID, amount) local src = NoteSource("Kauf"); NoteBid(auctionID, amount, src) end)
    H("QueryOwnedAuctions", function() NoteSource("Eigene Auktionen"); NoteCall("Eigene Auktionen") end)
    H("QueryBids", function() NoteSource("Gebote"); NoteCall("Gebote") end)
    H("StartCommoditiesPurchase", function(itemID, qty)
        NoteSource("Warenkauf")
        Inc(B.tot, "warenStart")
        B.comm = { t = Now(), item = tonumber(itemID), qty = tonumber(qty) or 0 }
        Log("WARE-START", string.format("Item %s · %s Stück", tostring(itemID), tostring(qty)))
    end)
    H("ConfirmCommoditiesPurchase", function(itemID, qty)
        Inc(B.tot, "gesendet"); Inc(B.min, "gesendet")
        NoteCall("Warenkauf")
        B.comm = { t = Now(), item = tonumber(itemID), qty = tonumber(qty) or 0, money = GetMoneyNow() }
        Log("WARE-GESENDET", string.format("Item %s · %s Stück", tostring(itemID), tostring(qty)))
    end)
    H("CancelAuction", function(auctionID) Log("ABBRUCH", "Auktion " .. tostring(auctionID)) end)
    H("PostItem", function() B.lastPost = Now(); Log("EINSTELLEN", "Ausrüstung") end)
    H("PostCommodity", function() B.lastPost = Now(); Log("EINSTELLEN", "Ware") end)
end

---------------------------------------------------------------------------
-- Ereignisse
---------------------------------------------------------------------------
local f = CreateFrame("Frame")
-- Fehlercodes des modernen Auktionshauses (Enum.AuctionHouseError) als Wort
local AHERR = { [0] = "nicht genug Gold", [1] = "höheres Gebot", [3] = "eigenes Gebot", [4] = "Angebot nicht gefunden (schon weg)",
    [7] = "beschäftigt", [8] = "nicht verfügbar", [10] = "Datenbankfehler (Interner Auktion-Fehler)", [23] = "doppeltes Gebot",
    [25] = "Angebot nicht verfügbar" }
B.frame = f
local EVENTS = { "PLAYER_LOGIN", "PLAYER_LOGOUT", "PLAYER_MONEY", "AUCTION_HOUSE_SHOW", "AUCTION_HOUSE_CLOSED",
    "MAIL_SHOW", "MAIL_CLOSED", "MERCHANT_SHOW", "MERCHANT_CLOSED", "CHAT_MSG_SYSTEM", "UI_ERROR_MESSAGE",
    "ITEM_SEARCH_RESULTS_UPDATED", "COMMODITY_SEARCH_RESULTS_UPDATED", "AUCTION_HOUSE_PURCHASE_COMPLETED",
    "AUCTION_HOUSE_SHOW_ERROR", "COMMODITY_PURCHASE_SUCCEEDED", "COMMODITY_PURCHASE_FAILED", "COMMODITY_PRICE_UPDATED",
    "COMMODITY_PRICE_UNAVAILABLE", "AUCTION_CANCELED", "AUCTION_HOUSE_AUCTION_CREATED", "REPLICATE_ITEM_LIST_UPDATE",
    "AUCTION_HOUSE_THROTTLED_MESSAGE_DROPPED", "AUCTION_HOUSE_THROTTLED_MESSAGE_QUEUED",
    "AUCTION_HOUSE_THROTTLED_MESSAGE_SENT", "AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED",
    "AUCTION_HOUSE_THROTTLED_SYSTEM_READY" }
for _, e in ipairs(EVENTS) do pcall(f.RegisterEvent, f, e) end

local function Err(key)
    B.errs = B.errs or {}
    Inc(B.errs, key)
end

local handlers = {}
handlers.PLAYER_LOGIN = function()
    local d = DB()
    if d.off then B.on = false end
    B.startClock = (date and date("%d.%m. %H:%M")) or "?"
    B.lastMoney = GetMoneyNow()
    BuildSys()
    Hook()
    Log("SITZUNG", string.format("Start · GSSniperLog %s · Gold %s · AHSentinel %s", VERSION, Money(B.lastMoney),
        tostring(AHS() and AHS().version or "nicht geladen")))
    Print("läuft im Hintergrund (nur mitschreiben). /gssl = Stand")
    pcall(WatchAHS)                               -- Ausgangsstand der AHSentinel-Zähler sofort festhalten
end
handlers.PLAYER_LOGOUT = function()
    pcall(VollscanEnd, true)
    pcall(MinuteSummary)
    pcall(BuildExport)
end
handlers.PLAYER_MONEY = function() NoteMoney() end
handlers.AUCTION_HOUSE_SHOW = function()
    B.ah = true
    B.mail = false                     -- Briefkasten ist zu, wenn das AH aufgeht (MAIL_CLOSED kommt nicht immer)
    B.lastSearchT = nil
    Hook()
    Log("AH", "geöffnet · Sniper " .. (SniperArmed() and "an" or "aus"))
    pcall(WatchAHS)
    if B.HookRasten then pcall(B.HookRasten) end
end
handlers.AUCTION_HOUSE_CLOSED = function()
    B.ah = false
    B.lastSearchT = nil                -- Zeit mit geschlossenem AH ist keine Sniper-Pause
    B.pauseOpen = false
    Log("AH", "geschlossen")
end
handlers.MAIL_SHOW = function() B.mail = true end
handlers.MAIL_CLOSED = function() B.mail = false end
handlers.MERCHANT_SHOW = function() B.merchant = true end
handlers.MERCHANT_CLOSED = function() B.merchant = false end
handlers.CHAT_MSG_SYSTEM = function(msg)
    local k = ClassifySystem(msg)
    if k then
        Inc(B.tot, "sys " .. k)
        if k == "gewonnen" or k == "Gebot akzeptiert" then Inc(B.min, "sys " .. k) end
        Log("SYSTEM", k)
    end
end
handlers.UI_ERROR_MESSAGE = function(a1, a2)
    local text = type(a2) == "string" and a2 or (type(a1) == "string" and a1 or nil)
    if not text then return end
    if not AHOpen() then return end
    text = Clean(text)
    Err("Meldung: " .. text)
    Inc(B.min, "fehler")
    Inc(B.tot, "fehler")
    local aid, b = OldestOpen()
    Log("FEHLER", text .. string.format(" · offene Käufe %d%s", OpenCount(), b and string.format(" · ältester seit %.2f s", Now() - b.t) or ""))
    if b then b.err = text end
end
handlers.ITEM_SEARCH_RESULTS_UPDATED = function(itemKey) ReadItemResults(itemKey) end
handlers.COMMODITY_SEARCH_RESULTS_UPDATED = function(itemID) ReadCommodityResults(itemID) end
handlers.AUCTION_HOUSE_PURCHASE_COMPLETED = function(auctionID) ResolveBid(auctionID, "Server: gekauft") end
handlers.AUCTION_HOUSE_SHOW_ERROR = function(code)
    local word = AHERR[tonumber(code) or -1]
    Err("AH-Fehlercode " .. tostring(code) .. (word and (" " .. word) or ""))
    local aid, b = OldestOpen()
    Log("AH-FEHLER", string.format("Code %s%s · letzte Anfrage %s vor %d ms · offene Käufe %d%s", tostring(code), word and (" " .. word) or "",
        tostring(B.lastCall or "?"), math.floor((Now() - (B.lastCallT or Now())) * 1000), OpenCount(),
        b and string.format(" · ältester seit %.2f s", Now() - b.t) or ""))
    if b and not b.err then b.err = "Code " .. tostring(code) end
end
handlers.COMMODITY_PURCHASE_SUCCEEDED = function()
    local c = B.comm
    Inc(B.tot, "gekauft"); Inc(B.min, "gekauft")
    Log("WARE-OK", c and string.format("Item %s · %d Stück · Antwort nach %.2f s", tostring(c.item), c.qty or 0, Now() - c.t) or "ohne Sendevorgang")
    B.comm = nil
end
handlers.COMMODITY_PURCHASE_FAILED = function()
    local c = B.comm
    Err("Ware gescheitert")
    Inc(B.tot, "fehler"); Inc(B.min, "fehler")
    Log("WARE-FEHLER", c and string.format("Item %s · %d Stück · nach %.2f s", tostring(c.item), c.qty or 0, Now() - c.t) or "ohne Sendevorgang")
    B.comm = nil
end
handlers.COMMODITY_PRICE_UPDATED = function(unit, total)
    Log("WARE-PREIS", string.format("Server-Preis %s/Stück, gesamt %s", Money(unit), Money(total)))
end
handlers.COMMODITY_PRICE_UNAVAILABLE = function() Err("Ware Preis nicht verfügbar"); Log("WARE-PREIS", "nicht verfügbar") end
handlers.AUCTION_CANCELED = function(auctionID)
    -- kommt auch bei einem EIGENEN KAUF (Server entfernt die gekaufte Auktion) – darum nur als Server-Ereignis
    local b = auctionID and B.bids[auctionID]
    Log("AUCTION_CANCELED", "Auktion " .. tostring(auctionID) .. (b and " (unser Kauf)" or " (eigene Auktion oder fremd)"))
end
handlers.AUCTION_HOUSE_AUCTION_CREATED = function() Log("EINSTELLEN-OK", "Auktion erstellt") end
-- 1.3: ein Vollscan liefert tausende Antworten -> eine Zeile am Anfang, eine Zusammenfassung am Ende (5 s Ruhe)
handlers.REPLICATE_ITEM_LIST_UPDATE = function()
    local now = Now()
    Inc(B.tot, "vsAntworten")
    local v = B.vs
    if not v then
        v = { t0 = now, n = 0, own = B.vollscanT ~= nil }
        B.vs = v
        Inc(B.tot, "vsSchuebe")
        Log("VOLLSCAN", B.vollscanT and string.format("Antwort nach %.1f s", now - B.vollscanT) or "Antwort (fremd ausgelöst)")
    end
    v.n, v.last = v.n + 1, now
    B.vollscanT = nil
end
local function VollscanEnd(force)
    local v = B.vs
    if not v then return end
    if force or Now() - (v.last or v.t0) >= 5 then
        Log("VOLLSCAN", string.format("%d Antworten in %.1f s (%s)", v.n, (v.last or v.t0) - v.t0, v.own and "selbst gestartet" or "fremd ausgelöst"))
        B.vs = nil
    end
end
B.VollscanEnd = VollscanEnd
for _, e in ipairs({ "AUCTION_HOUSE_THROTTLED_MESSAGE_DROPPED", "AUCTION_HOUSE_THROTTLED_MESSAGE_QUEUED",
    "AUCTION_HOUSE_THROTTLED_MESSAGE_SENT", "AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED",
    "AUCTION_HOUSE_THROTTLED_SYSTEM_READY" }) do
    local short = e:gsub("AUCTION_HOUSE_THROTTLED_", "")
    handlers[e] = function()
        Inc(B.tot, "drossel " .. short); Inc(B.min, "drossel " .. short)
        -- Zuordnung: letzte Anfrage an den Server (Suche oder Kauf) und wie lange her
        local last = B.lastCall and string.format("letzte Anfrage %s vor %d ms", B.lastCall, math.floor((Now() - (B.lastCallT or Now())) * 1000)) or "keine Anfrage bekannt"
        if short == "MESSAGE_DROPPED" then
            Err("Drossel: Nachricht verworfen (nach " .. tostring(B.lastCall or "?") .. ")")
            Log("DROSSEL", "VERWORFEN · " .. last .. " · offene Käufe " .. OpenCount())
        elseif short == "MESSAGE_QUEUED" then
            Log("DROSSEL", "in Warteschlange · " .. last)
        elseif short == "SYSTEM_READY" then
            B.readyFrame = true                          -- 1.3: ab jetzt bereit (gilt für die nächste Anfrage)
            Log("DROSSEL", "Server wieder bereit")
        end
    end
end

f:SetScript("OnEvent", function(_, ev, ...)
    local h = handlers[ev]
    if not h then return end
    if not B.on and ev ~= "PLAYER_LOGIN" and ev ~= "PLAYER_LOGOUT" then return end
    local ok, err = pcall(h, ...)
    if not ok then
        B.lastError = tostring(err)
        Inc(B.tot, "eigeneFehler")
        pcall(Log, "GSSL-FEHLER", ev .. ": " .. tostring(err))
    end
end)

---------------------------------------------------------------------------
-- Ruckler (1.2, Nutzer 14:35): Bildzeiten, Speicher und Speicherbereinigung, Ereignis-Stürme, laufende AHSentinel-Aufgaben,
-- Zeit je Addon (C_AddOnProfiler, wenn das Spiel ihn hat; sonst Speicher je Addon), eigene Kosten von GSSniperLog
---------------------------------------------------------------------------
local R = { frames = 0, f33 = 0, f50 = 0, f100 = 0, evSec = {}, evPrev = {}, evSecT = 0, evMax = 0, mem = nil,
            memMin = nil, gc = 0, own = 0, ownMax = 0, maxEl = 0 }
B.R = R
local function Ms() return (debugprofilestop and debugprofilestop()) or (Now() * 1000) end
local function LuaMemKB()
    local ok, v = pcall(collectgarbage, "count")
    return ok and tonumber(v) or nil
end
-- alle Ereignisse je Sekunde zählen (nur zählen, sonst nichts)
local ef = CreateFrame("Frame")
B.eventFrame = ef
if ef.RegisterAllEvents then pcall(ef.RegisterAllEvents, ef) end
ef:SetScript("OnEvent", function(_, ev)
    if B.on and ev then local c = R.evSec; c[ev] = (c[ev] or 0) + 1 end
end)
local function TopEvents(n)
    local merged, total = {}, 0
    for k, v in pairs(R.evPrev) do merged[k] = (merged[k] or 0) + v end
    for k, v in pairs(R.evSec) do merged[k] = (merged[k] or 0) + v end
    local arr = {}
    for k, v in pairs(merged) do arr[#arr + 1] = { k, v }; total = total + v end
    table.sort(arr, function(a, b) return a[2] > b[2] end)
    local out = {}
    for i = 1, math.min(n, #arr) do out[#out + 1] = arr[i][1] .. " " .. arr[i][2] end
    return table.concat(out, ", "), total
end
local function AHSJobs()
    local A = AHS()
    if not (A and type(A.jobs) == "table") then return nil end
    local names = {}
    for _, j in ipairs(A.jobs) do
        if type(j) == "table" and j.name then names[#names + 1] = tostring(j.name) .. (j.started and "*" or "") end
        if #names >= 6 then break end
    end
    return #names > 0 and table.concat(names, ", ") or "keine"
end
local function AHSWindowShown()
    local w = _G.AHAnalyzerProWindow
    return (w and w.IsShown and w:IsShown()) and true or false
end
local function SpikeContext(el, memDelta)
    local top, total = TopEvents(3)
    local parts = { string.format("%d ms", math.floor(el * 1000)), AHOpen() and "AH offen" or "AH zu",
        "Sniper " .. (SniperArmed() and "an" or "aus"), "AHS-Fenster " .. (AHSWindowShown() and "offen" or "zu") }
    local jobs = AHSJobs()
    if jobs then parts[#parts + 1] = "AHS-Aufgaben: " .. jobs end
    if memDelta then
        if memDelta < -1024 then parts[#parts + 1] = string.format("Speicherbereinigung (−%.1f MB)", -memDelta / 1024)
        elseif memDelta > 512 then parts[#parts + 1] = string.format("Speicher +%.1f MB in diesem Bild", memDelta / 1024) end
    end
    if B.lastCallT and Now() - B.lastCallT < 0.5 then
        parts[#parts + 1] = string.format("letzte Anfrage %s vor %d ms", tostring(B.lastCall), math.floor((Now() - B.lastCallT) * 1000))
    end
    if InCombatLockdown and InCombatLockdown() then parts[#parts + 1] = "Kampf" end
    parts[#parts + 1] = "Ereignisse (2 s, " .. total .. "): " .. (top ~= "" and top or "-")
    return table.concat(parts, " · ")
end
B.SpikeContext = SpikeContext

-- Zeit je Addon
local PROF
local function ProfilerInit()
    local P = _G.C_AddOnProfiler
    if type(P) ~= "table" or type(P.GetAddOnMetric) ~= "function" then return nil end
    local E = _G.Enum and _G.Enum.AddOnProfilerMetric
    if type(E) ~= "table" or E.RecentAverageTime == nil then return nil end
    return { P = P, recent = E.RecentAverageTime, peak = E.PeakTime, over50 = E.CountTimeOver50Ms }
end
local function AddonNames()
    local names = {}
    local CA = _G.C_AddOns
    local num = (CA and CA.GetNumAddOns) or _G.GetNumAddOns
    local info = (CA and CA.GetAddOnInfo) or _G.GetAddOnInfo
    local loaded = (CA and CA.IsAddOnLoaded) or _G.IsAddOnLoaded
    if not (num and info and loaded) then return names end
    local okN, n = pcall(num)
    n = okN and tonumber(n) or 0
    for i = 1, math.min(n, 300) do
        local ok, name = pcall(info, i)
        if ok and type(name) == "string" then
            local ok2, l = pcall(loaded, name)
            if ok2 and l then names[#names + 1] = name end
        end
    end
    return names
end
local function AddonMinute()
    if PROF == nil then PROF = ProfilerInit() or false end
    local parts = {}
    if PROF then
        local rows = {}
        for _, name in ipairs(AddonNames()) do
            local ok1, rec = pcall(PROF.P.GetAddOnMetric, name, PROF.recent)
            local ok2, peak, ok3, o50 = false, nil, false, nil
            if PROF.peak ~= nil then ok2, peak = pcall(PROF.P.GetAddOnMetric, name, PROF.peak) end
            if PROF.over50 ~= nil then ok3, o50 = pcall(PROF.P.GetAddOnMetric, name, PROF.over50) end
            if ok1 and tonumber(rec) then
                rows[#rows + 1] = { name, tonumber(rec) or 0, ok2 and tonumber(peak) or 0, ok3 and tonumber(o50) or 0 }
            end
        end
        table.sort(rows, function(a, b) return a[2] > b[2] end)
        for i = 1, math.min(8, #rows) do
            local r = rows[i]
            parts[#parts + 1] = string.format("%s Ø %.2f ms, Spitze %.0f ms, >50 ms %d×", r[1], r[2], r[3], r[4])
        end
        Log("ADDONS", "Zeit je Addon (Spiel-Profiler): " .. (#parts > 0 and table.concat(parts, " · ") or "keine Werte"))
    else
        -- ohne Profiler: Speicher je Addon. UpdateAddOnMemoryUsage kann selbst ruckeln -> Kosten messen, über 30 ms abschalten.
        if R.memOff then return end
        local upd, get = _G.UpdateAddOnMemoryUsage, _G.GetAddOnMemoryUsage
        if not (upd and get) then return end
        local t0 = Ms()
        pcall(upd)
        local cost = Ms() - t0
        if cost > 30 then R.memOff = true end
        local rows = {}
        for _, name in ipairs(AddonNames()) do
            local ok, kb = pcall(get, name)
            if ok and tonumber(kb) then rows[#rows + 1] = { name, tonumber(kb) } end
        end
        table.sort(rows, function(a, b) return a[2] > b[2] end)
        R.addonMem = R.addonMem or {}
        for i = 1, math.min(8, #rows) do
            local prev = R.addonMem[rows[i][1]]
            parts[#parts + 1] = string.format("%s %.1f MB%s", rows[i][1], rows[i][2] / 1024,
                prev and string.format(" (%+.1f)", (rows[i][2] - prev) / 1024) or "")
        end
        for _, r in ipairs(rows) do R.addonMem[r[1]] = r[2] end
        Log("ADDONS", string.format("Speicher je Addon (Messung kostete %d ms%s): ", math.floor(cost), R.memOff and ", ab jetzt aus" or "") ..
            table.concat(parts, " · "))
    end
end
B.AddonMinute = AddonMinute

local function FrameMinute()
    local memNow = LuaMemKB()
    Log("BILDER", string.format("%d Bilder (Ø %d/s) · über 33 ms %d · über 50 ms %d · über 100 ms %d · längstes %d ms · Ereignisse max %d/s · Lua-Speicher %s%s · Speicherbereinigungen %d · eigene Zeit %d ms (Spitze %.1f ms)",
        R.frames, math.floor(R.frames / 60 + 0.5), R.f33, R.f50, R.f100, math.floor((R.maxEl or 0) * 1000), R.evMax,
        memNow and string.format("%.1f MB", memNow / 1024) or "?",
        (memNow and R.memMin) and string.format(" (%+.1f MB)", (memNow - R.memMin) / 1024) or "", R.gc, math.floor(R.own), R.ownMax))
    R.frames, R.f33, R.f50, R.f100, R.evMax, R.gc, R.own, R.ownMax, R.maxEl = 0, 0, 0, 0, 0, 0, 0, 0, 0
    R.memMin = memNow
end

-- Rasten von AHSentinel (Mausrad/Taste) mithören: HookScript auf seine Knöpfe, ändert nichts
-- Raste ohne Kauf zählen, mit dem Sniper-Status zur Zeit der Raste
local function RasteOhne()
    Inc(B.min, "rasteOhne"); Inc(B.tot, "rasteOhne")
    local st = tostring(B.rasteSt or B.status or "-")
    if #st > 60 then st = st:sub(1, 60) end
    B.min.rasteOhneSt = B.min.rasteOhneSt or {}
    Inc(B.min.rasteOhneSt, st)
    if (B.min.rasteOhneLog or 0) < 3 then
        Inc(B.min, "rasteOhneLog")
        pcall(Log, "RASTE", "ohne Kauf (Status bei der Raste: " .. st .. ")")
    end
    B.rasteT, B.rasteSt = nil, nil
end
B.RasteOhne = RasteOhne
-- 1.4: Eine Raste ist (a) ein Klick auf einen Auslöse-Knopf von AHSentinel (Mausrad/Taste über der Spielwelt) oder
-- (b) ein Mausrad über einem AHSentinel-Fenster, während ein Treffer wartet (AHSentinel kauft dann über Sn:WheelBuy,
-- nicht über die Knöpfe – das fehlte in 1.2/1.3: "Rasten 0" trotz 14 Käufen). Nur HookScript (nachher mithören).
local function NoteRaste(src)
    if not B.on then return end
    if B.rasteT then B.RasteOhne() end            -- vorige Raste ohne Kauf
    B.rasteT = Now()
    local okS, st = pcall(StatusText)
    B.rasteSt = (okS and st) or B.status or "-"
    Inc(B.min, "rasten"); Inc(B.tot, "rasten")
    B.min.rasteSrc = B.min.rasteSrc or {}
    Inc(B.min.rasteSrc, src)
end
B.NoteRaste = NoteRaste
local function HitWaiting()
    local A = AHS()
    local Sn = A and A.Sniper
    if not (Sn and type(Sn.HitWaiting) == "function") then return false end
    local ok, v = pcall(Sn.HitWaiting, Sn)
    return ok and v and true or false
end
B.hooked = B.hooked or setmetatable({}, { __mode = "k" })
local function HookWheel(fr, depth)
    if type(fr) ~= "table" or depth > 7 then return end
    if not B.hooked[fr] and fr.GetScript and fr.HookScript then
        local okG, sc = pcall(fr.GetScript, fr, "OnMouseWheel")
        if okG and sc then
            B.hooked[fr] = true
            pcall(fr.HookScript, fr, "OnMouseWheel", function()
                if B.on and AHOpen() and HitWaiting() then NoteRaste("Mausrad über AHS-Fenster") end
            end)
        end
    end
    if fr.GetChildren then
        local okC, kids = pcall(function() return { fr:GetChildren() } end)
        if okC then for _, k in ipairs(kids) do HookWheel(k, depth + 1) end end
    end
end
local function HookRasten()
    for _, n in ipairs({ "AHAnalyzerProSnipeButton", "AHAnalyzerProSnipeOnlyButton" }) do
        local b = _G[n]
        if b and b.HookScript and not B.hooked[b] then
            B.hooked[b] = true
            B.rastenHooked = true
            pcall(b.HookScript, b, "OnClick", function() NoteRaste("Taste/Mausrad Spielwelt") end)
        end
    end
    -- Fenster von AHSentinel (auch die Tabellen darin) – neu entstandene werden beim nächsten Durchlauf erfasst
    for _, n in ipairs({ "AHAnalyzerProWindow", "AHAnalyzerProAHPanel" }) do
        local w = _G[n]
        if w then pcall(HookWheel, w, 0) end
    end
end
B.HookRasten = HookRasten

-- Takt: jede Sekunde AHSentinel lesen und Fristen prüfen, jede Minute zusammenfassen; jedes Bild die Bildzeit
local acc, minAcc = 0, 0
f:SetScript("OnUpdate", function(_, el)
    if not B.on then return end
    local t0 = Ms()
    el = tonumber(el) or 0
    if el > (B.maxFrame or 0) then B.maxFrame = el end
    if el > (B.maxFrameMin or 0) then B.maxFrameMin = el end
    R.frames = R.frames + 1
    if el > R.maxEl then R.maxEl = el end
    if el > 0.033 then R.f33 = R.f33 + 1 end
    if el > 0.050 then R.f50 = R.f50 + 1 end
    if el > 0.100 then R.f100 = R.f100 + 1 end
    local mem = LuaMemKB()
    local memDelta = (mem and R.mem) and (mem - R.mem) or nil
    if memDelta and memDelta < -1024 then R.gc = R.gc + 1 end
    R.mem = mem
    -- Ereignisse je Sekunde weiterschalten
    local now = Now()
    if now - R.evSecT >= 1 then
        local n = 0
        for _, v in pairs(R.evSec) do n = n + v end
        if n > R.evMax then R.evMax = n end
        R.evPrev, R.evSec, R.evSecT = R.evSec, {}, now
    end
    if el * 1000 > SPIKE_MS then
        B.spikes = (B.spikes or 0) + 1
        if B.spikes <= 300 then
            local ok, txt = pcall(SpikeContext, el, memDelta)
            pcall(Log, "BILD", ok and txt or (math.floor(el * 1000) .. " ms"))
        end
    end
    -- Raste ohne Kauf nach 1 s
    if B.rasteT and now - B.rasteT >= 1 then pcall(RasteOhne) end
    acc = acc + el
    minAcc = minAcc + el
    if acc >= 1 then
        acc = 0
        local ok, err = pcall(WatchAHS)
        if not ok then pcall(Log, "GSSL-FEHLER", "Lesen: " .. tostring(err)) end
        pcall(CheckTimeouts)
        pcall(VollscanEnd, false)
        -- Ruhemodus-Messung: Sekunden mit Sniper an und AH offen, und welche AHS-Aufgaben dabei liefen
        B.snipingNow = SniperArmed() and AHOpen()
        if B.snipingNow then
            Inc(B.min, "snipeSec"); Inc(B.tot, "snipeSec")
            local A = AHS()
            if A and type(A.jobs) == "table" then
                B.min.jobSec = B.min.jobSec or {}
                local seen = {}
                for _, j in ipairs(A.jobs) do
                    if type(j) == "table" and j.name then
                        local n = tostring(j.name):gsub(":%d+$", "")
                        if not seen[n] then seen[n] = true; Inc(B.min.jobSec, n) end
                    end
                end
            end
        end
        -- Pause beenden, sobald wieder gesucht wird
        if B.pauseOpen and B.lastSearchT and B.lastSearchT > (B.pauseStart or 0) then
            B.pauseOpen = false
            local dur = B.lastSearchT - (B.pauseStart or B.lastSearchT)
            Inc(B.tot, "pausen")
            pcall(Log, "PAUSE", string.format("%.1f s keine Sniper-Suche (Status: %s)", dur, tostring(B.status or "-")))
        end
    end
    if minAcc >= 60 then
        minAcc = 0
        local ok, err = pcall(MinuteSummary)
        if not ok then pcall(Log, "GSSL-FEHLER", "Minute: " .. tostring(err)) end
        ok, err = pcall(FrameMinute)
        if not ok then pcall(Log, "GSSL-FEHLER", "Bilder: " .. tostring(err)) end
        ok, err = pcall(AddonMinute)
        if not ok then pcall(Log, "GSSL-FEHLER", "Addons: " .. tostring(err)) end
        pcall(HookRasten)                    -- 1.4: neue Fenster/Tabellen von AHSentinel mit erfassen
    end
    -- 1.3: Stand der Drossel am Ende dieses Bildes = "vorher" für die Anfragen im nächsten Bild
    B.readyFrame = ServerReady()
    B.callsInFrame = 0
    local d = Ms() - t0
    R.own = R.own + d
    if d > R.ownMax then R.ownMax = d end
end)

---------------------------------------------------------------------------
-- Befehl
---------------------------------------------------------------------------
SLASH_GSSNIPERLOG1 = "/gssl"
SlashCmdList.GSSNIPERLOG = function(arg)
    local a = tostring(arg or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
    if a == "aus" then
        B.on = false; DB().off = true; Print("aus (schreibt nichts mehr mit)")
    elseif a == "an" then
        B.on = true; DB().off = nil; Print("an")
    elseif a == "leeren" then
        local d = DB(); d.log = {}; d.sum = {}; d.export = nil; B.tot, B.min, B.buckets, B.errs = {}, {}, {}, {}
        Print("Mitschrift geleert.")
    else
        Print(string.format("%s · %d Zeilen · /gssl aus|an|leeren · Ergebnis geht beim Ausloggen oder /reload an den Uploader",
            B.on and "läuft" or "AUS", #DB().log))
        for _, s in ipairs(SummaryLines()) do Print(s) end
    end
end
