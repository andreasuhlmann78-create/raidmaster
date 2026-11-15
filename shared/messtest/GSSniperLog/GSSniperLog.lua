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
-- Ergebnis: beim Ausloggen oder /reload als "GSDIAG1|GSSniperLog|…" in GSSniperLogDB.export -> der RaidMasterUploader
-- bringt es nach testberichte/diagnose/GSSniperLog/. Befehl: /gssl (Stand), /gssl aus|an, /gssl leeren.

local ADDON, VERSION = "GSSniperLog", "1.0"
local MAXLOG = 6000            -- Zeilen im Speicher (älteste fallen weg)
local EXPORT_MAX = 400000      -- Zeichen in der Ausgabe für den Uploader
local CONFIRM_MAX = 30         -- Sekunden: ohne Antwort gilt ein Kauf als "keine Bestätigung"
local PAUSE_LOG = 3            -- Sekunden ohne Sniper-Suche (Sniper an, AH offen) -> als Pause festhalten
local SPIKE_MS = 100           -- längere Frames werden einzeln festgehalten
local RESULT_MAX = 60          -- so viele Angebote je Ergebnis werden gelesen

local B = { on = true, bids = {}, sent = {}, searches = {}, offers = {}, tot = {}, min = {}, buckets = {},
            ah = false, mail = false, merchant = false, lastMoney = nil, status = nil, statusT = nil,
            ahsCount = {}, lastSearchT = nil, maxFrame = 0, maxFrameMin = 0, spikes = 0 }
_G.GSSniperLog = B

---------------------------------------------------------------------------
-- Hilfen
---------------------------------------------------------------------------
local function Now() return (GetTime and GetTime()) or 0 end
local function Clock()
    local t = Now()
    return string.format("%s.%d", (date and date("%H:%M:%S")) or "?", math.floor((t * 10) % 10))
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
    d.log[#d.log + 1] = Clock() .. " " .. kat .. " " .. Clean(text)
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
local function NoteSearch(kind, itemID)
    local now = Now()
    Inc(B.tot, "suchen"); Inc(B.min, "suchen")
    if itemID then B.searches[itemID] = now end
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
    for _, b in pairs(B.bids) do if not b.done then n = n + 1 end end
    return n
end
local function Bucket(open) return open >= 2 and "≥2" or tostring(open) end

local function NoteBid(auctionID, amount)
    local now = Now()
    local open = OpenCount()
    local dup = B.sent[auctionID] and true or false
    B.sent[auctionID] = now
    local o = B.offers[auctionID]
    local seen = o and (now - o.t) or nil
    B.bids[auctionID] = { t = now, amount = tonumber(amount) or 0, open = open, dup = dup, money = GetMoneyNow(),
                          item = o and o.item or nil }
    Inc(B.tot, "gesendet"); Inc(B.min, "gesendet")
    if dup then Inc(B.tot, "doppelt"); Inc(B.min, "doppelt") end
    local bk = B.buckets[Bucket(open)] or { n = 0, ok = 0 }
    B.buckets[Bucket(open)] = bk
    bk.n = bk.n + 1
    Log("KAUF-GESENDET", string.format("Angebot %s · %s · offen beim Senden %d%s%s", tostring(auctionID), Money(amount), open,
        dup and " · DOPPELT GESENDET" or "", seen and string.format(" · Reaktion %.2f s nach erstem Sehen", seen) or ""))
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
        if not b.done and (not best or b.t < best.t) then best, bid = b, aid end
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
    if B.mail then ctx = "Post"
    elseif B.merchant then ctx = "Händler"
    elseif AHOpen() then
        local recentBid = false
        for _, b in pairs(B.bids) do if Now() - b.t < 60 then recentBid = true break end end
        if d < 0 and B.lastPost and Now() - B.lastPost < 5 then ctx = "AH Einstellgebühr"
        elseif d < 0 and recentBid then ctx = "AH Kauf"
        elseif d < 0 then ctx = "AH (ohne Kauf in den letzten 60 s)"
        else ctx = "AH Eingang" end
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
local function MinuteSummary()
    local m = B.min
    if (m.suchen or 0) == 0 and (m.gesendet or 0) == 0 and (m.weg or 0) == 0 then
        B.min = {}
        B.maxFrameMin = 0
        return
    end
    local parts = {}
    parts[#parts + 1] = string.format("Suchen %d (Ø Antwort %s, längste %s, längste Lücke %s)", m.suchen or 0,
        (m.latN or 0) > 0 and string.format("%.2f s", m.latSum / m.latN) or "-",
        m.latMax and string.format("%.2f s", m.latMax) or "-", m.gapMax and string.format("%.1f s", m.gapMax) or "-")
    parts[#parts + 1] = string.format("gesendet %d · gekauft %d · ohne Antwort %d · doppelt %d · Fehler %d · weggeschnappt %d",
        m.gesendet or 0, m.gekauft or 0, m.ohneAntwort or 0, m.doppelt or 0, m.fehler or 0, m.weg or 0)
    parts[#parts + 1] = string.format("Antwortzeit Ø %s, längste %s",
        (m.antwortN or 0) > 0 and string.format("%.2f s", m.antwortSum / m.antwortN) or "-",
        m.antwortMax and string.format("%.2f s", m.antwortMax) or "-")
    parts[#parts + 1] = string.format("Summe bestätigt %s · Gold-Abgang AH-Kauf %s · AHSentinel gezählt +%d / %s",
        Money(m.summe or 0), Money(m.goldKauf or 0), m.ahsGekauft or 0, Money(m.ahsAusgegeben or 0))
    parts[#parts + 1] = string.format("längster Frame %d ms", math.floor(B.maxFrameMin * 1000))
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
    out[#out + 1] = string.format("Sitzung seit %s · Suchen %d · gesendet %d · gekauft %d (davon spät %d) · ohne Antwort %d · doppelt gesendet %d · Fehler %d",
        B.startClock or "?", t.suchen or 0, t.gesendet or 0, t.gekauft or 0, t.spaet or 0, t.ohneAntwort or 0, t.doppelt or 0, t.fehler or 0)
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
    out[#out + 1] = string.format("Bildaussetzer > %d ms: %d · längster Frame %d ms", SPIKE_MS, B.spikes or 0, math.floor((B.maxFrame or 0) * 1000))
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
    H("SendSearchQuery", function(itemKey) NoteSearch("Einzel", ItemIDOfKey(itemKey)) end)
    H("SendSellSearchQuery", function(itemKey) NoteSearch("Verkauf", ItemIDOfKey(itemKey)) end)
    H("SendBrowseQuery", function() NoteSearch("Durchsuchen", nil) end)
    H("ReplicateItems", function() B.vollscanT = Now(); Inc(B.tot, "vollscans"); Log("VOLLSCAN", "gestartet") end)
    H("PlaceBid", function(auctionID, amount) NoteBid(auctionID, amount) end)
    H("StartCommoditiesPurchase", function(itemID, qty)
        Inc(B.tot, "warenStart")
        B.comm = { t = Now(), item = tonumber(itemID), qty = tonumber(qty) or 0 }
        Log("WARE-START", string.format("Item %s · %s Stück", tostring(itemID), tostring(qty)))
    end)
    H("ConfirmCommoditiesPurchase", function(itemID, qty)
        Inc(B.tot, "gesendet"); Inc(B.min, "gesendet")
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
    pcall(MinuteSummary)
    pcall(BuildExport)
end
handlers.PLAYER_MONEY = function() NoteMoney() end
handlers.AUCTION_HOUSE_SHOW = function()
    B.ah = true
    Hook()
    Log("AH", "geöffnet · Sniper " .. (SniperArmed() and "an" or "aus"))
    pcall(WatchAHS)
end
handlers.AUCTION_HOUSE_CLOSED = function() B.ah = false; Log("AH", "geschlossen") end
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
    Err("AH-Fehlercode " .. tostring(code))
    local aid, b = OldestOpen()
    Log("AH-FEHLER", string.format("Code %s · offene Käufe %d%s", tostring(code), OpenCount(),
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
handlers.AUCTION_CANCELED = function(auctionID) Log("ABBRUCH-OK", "Auktion " .. tostring(auctionID)) end
handlers.AUCTION_HOUSE_AUCTION_CREATED = function() Log("EINSTELLEN-OK", "Auktion erstellt") end
handlers.REPLICATE_ITEM_LIST_UPDATE = function()
    Log("VOLLSCAN", B.vollscanT and string.format("Antwort nach %.1f s", Now() - B.vollscanT) or "Antwort (fremd ausgelöst)")
    B.vollscanT = nil
end
for _, e in ipairs({ "AUCTION_HOUSE_THROTTLED_MESSAGE_DROPPED", "AUCTION_HOUSE_THROTTLED_MESSAGE_QUEUED",
    "AUCTION_HOUSE_THROTTLED_MESSAGE_SENT", "AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED",
    "AUCTION_HOUSE_THROTTLED_SYSTEM_READY" }) do
    local short = e:gsub("AUCTION_HOUSE_THROTTLED_", "")
    handlers[e] = function()
        Inc(B.tot, "drossel " .. short); Inc(B.min, "drossel " .. short)
        if short == "MESSAGE_DROPPED" then Err("Drossel: Nachricht verworfen"); Log("DROSSEL", "Nachricht VERWORFEN · offene Käufe " .. OpenCount()) end
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

-- Takt: jede Sekunde AHSentinel lesen und Fristen prüfen, jede Minute zusammenfassen; jedes Bild die Bildzeit
local acc, minAcc = 0, 0
f:SetScript("OnUpdate", function(_, el)
    if not B.on then return end
    el = tonumber(el) or 0
    if el > (B.maxFrame or 0) then B.maxFrame = el end
    if el > (B.maxFrameMin or 0) then B.maxFrameMin = el end
    if el * 1000 > SPIKE_MS and AHOpen() then
        B.spikes = (B.spikes or 0) + 1
        if B.spikes <= 200 then pcall(Log, "BILD", string.format("%d ms (Sniper %s, offene Käufe %d)", math.floor(el * 1000),
            SniperArmed() and "an" or "aus", OpenCount())) end
    end
    acc = acc + el
    minAcc = minAcc + el
    if acc >= 1 then
        acc = 0
        local ok, err = pcall(WatchAHS)
        if not ok then pcall(Log, "GSSL-FEHLER", "Lesen: " .. tostring(err)) end
        pcall(CheckTimeouts)
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
    end
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
        local d = DB(); d.log = {}; d.export = nil; B.tot, B.min, B.buckets, B.errs = {}, {}, {}, {}
        Print("Mitschrift geleert.")
    else
        Print(string.format("%s · %d Zeilen · /gssl aus|an|leeren · Ergebnis geht beim Ausloggen oder /reload an den Uploader",
            B.on and "läuft" or "AUS", #DB().log))
        for _, s in ipairs(SummaryLines()) do Print(s) end
    end
end
