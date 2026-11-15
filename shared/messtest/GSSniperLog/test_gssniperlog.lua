-- Tests für GSSniperLog (lua5.1, ohne Spiel): nachgebaute WoW-Umgebung, 5 Läufe mit je eigenem Szenario.
-- Aufruf: lua5.1 test_gssniperlog.lua [Pfad zu GSSniperLog.lua]

local FILE = arg and arg[1] or "GSSniperLog.lua"
local pass, fail = 0, 0
local function check(cond, name)
    if cond then pass = pass + 1 else fail = fail + 1; print("FEHLER: " .. name) end
end

-- Neue Umgebung je Lauf
local function NewWorld(opts)
    opts = opts or {}
    local W = { t = 1000, money = 100000, frames = {}, chat = {}, hooks = 0 }
    local env = {}
    setmetatable(env, { __index = _G })
    env._G = env
    env.GetTime = function() return W.t end
    env.date = function(fmt, sec) if fmt == "%H:%M:%S" then return os.date("!%H:%M:%S", sec or 50400) end return "15.11.2026 14:00" end
    env.time = function() return 50400 + math.floor(W.t) end
    env.GetMoney = function() return W.money end
    env.debugprofilestop = function() return W.t * 1000 + (W.cpu or 0) end
    W.mem = 300000
    env.collectgarbage = function(k) if k == "count" then return W.mem end return 0 end
    env.InCombatLockdown = function() return W.combat or false end
    env.GetBuildInfo = function() return "1.60.1", "70938", "Nov", 16001 end
    env.DEFAULT_CHAT_FRAME = { AddMessage = function(_, s) W.chat[#W.chat + 1] = s end }
    env.SlashCmdList = {}
    env.CreateFrame = function()
        local fr = { events = {}, scripts = {} }
        function fr:RegisterEvent(e) self.events[e] = true end
        function fr:RegisterAllEvents() self.all = true end
        function fr:HookScript(k, fn) local old = self.scripts[k]; self.scripts[k] = function(...) if old then old(...) end fn(...) end end
        function fr:SetScript(k, fn) self.scripts[k] = fn end
        W.frames[#W.frames + 1] = fr
        return fr
    end
    env.hooksecurefunc = function(tbl, name, post)
        local orig = tbl[name]
        tbl[name] = function(...)
            local r = { orig(...) }
            post(...)
            return unpack(r)
        end
        W.hooks = W.hooks + 1
    end
    env.ERR_AUCTION_WON_S = "Ihr habt eine Auktion gewonnen für: %s"
    env.ERR_AUCTION_BID_PLACED = "Gebot akzeptiert."
    env.ERR_AUCTION_STARTED = "Auktion erstellt."
    env.ERR_AUCTION_REMOVED = "Auktion abgebrochen."
    env.ERR_AUCTION_SOLD_S = "Ein Käufer wurde für Eure Auktion gefunden: %s"
    -- Auktionshaus
    W.results = {}        -- itemID -> Liste { auctionID, buyoutAmount, quantity, containsOwnerItem }
    W.full = {}           -- itemID -> false = Teilergebnis
    if not opts.noAH then
        env.C_AuctionHouse = {
            SendSearchQuery = function() end, ReplicateItems = function() end, PlaceBid = function() end,
            StartCommoditiesPurchase = function() end, ConfirmCommoditiesPurchase = function() end,
            CancelAuction = function() end, PostItem = function() end, PostCommodity = function() end,
            GetNumItemSearchResults = function(k) return #(W.results[k.itemID] or {}) end,
            GetItemSearchResultInfo = function(k, i) return (W.results[k.itemID] or {})[i] end,
            HasFullItemSearchResults = function(k) return W.full[k.itemID] ~= false end,
            GetNumCommoditySearchResults = function(id) return #(W.results[id] or {}) end,
            GetCommoditySearchResultInfo = function(id, i) return (W.results[id] or {})[i] end,
        }
    end
    -- AHSentinel (nur gelesen)
    if not opts.noAHS then
        W.status = "wartet: nichts"
        env.AHAnalyzerPro = {
            version = "0.65.189",
            db = { sniper = { armed = true, targets = {
                ["i:4251"] = { itemID = 4251, maxPrice = 914, qty = 1000, budget = 50000, bought = 0, spent = 0 },
                ["c:2589"] = { itemID = 2589, maxPrice = 15, qty = 100, budget = 10000, bought = 0, spent = 0 } } } },
            Sniper = { GetStatusText = function()
                if opts.statusThrows then error("absichtlicher Fehler") end
                return "|cffffcc33" .. W.status .. "|r" end },
        }
    end
    local chunk = assert(loadfile(FILE))
    setfenv(chunk, env)
    chunk()
    local f = W.frames[1]
    function W.fire(ev, ...)
        for _, fr in ipairs(W.frames) do
            if (fr.events[ev] or fr.all) and fr.scripts.OnEvent then fr.scripts.OnEvent(fr, ev, ...) end
        end
    end
    function W.tick(sec, step)
        step = step or 0.1
        local n = math.floor(sec / step + 0.5)
        for _ = 1, n do W.t = W.t + step; f.scripts.OnUpdate(f, step) end
    end
    function W.frame(ms) W.t = W.t + ms / 1000; f.scripts.OnUpdate(f, ms / 1000) end
    W.env, W.f = env, f
    W.B = env.GSSniperLog
    function W.log() return (env.GSSniperLogDB and env.GSSniperLogDB.log) or {} end
    function W.find(pat)
        local n = 0
        for _, s in ipairs(W.log()) do if s:find(pat) then n = n + 1 end end
        return n
    end
    function W.search(id) env.C_AuctionHouse.SendSearchQuery({ itemID = id }, {}, false) end
    function W.pay(d) W.money = W.money + d; W.fire("PLAYER_MONEY") end
    return W
end

local function offer(aid, price, own) return { auctionID = aid, buyoutAmount = price, quantity = 1, containsOwnerItem = own or false } end

---------------------------------------------------------------------------
-- Lauf 1: normaler Sniper-Ablauf, parallel gesendet, Gold = bestätigt, AHS-Zähler
---------------------------------------------------------------------------
do
    local W = NewWorld()
    W.fire("PLAYER_LOGIN")
    check(W.hooks == 8, "Lauf 1: 8 Hooks (alle vorhandenen) gesetzt (ist " .. W.hooks .. ")")
    W.fire("AUCTION_HOUSE_SHOW")
    W.search(4251); W.tick(0.3)
    W.results[4251] = { offer(1, 900), offer(2, 905), offer(3, 914), offer(4, 1000) }
    W.fire("ITEM_SEARCH_RESULTS_UPDATED", { itemID = 4251 })
    check(W.find("ERGEBNIS Item 4251 · 4 Angebote · 3 unter Max 9s14") == 1, "Lauf 1: Ergebnis mit 3 unter Max")
    check(W.find("Antwort nach 0.30 s") == 1, "Lauf 1: Antwortzeit der Suche 0.30 s")
    W.env.C_AuctionHouse.PlaceBid(1, 900); W.tick(0.1)
    W.env.C_AuctionHouse.PlaceBid(2, 905); W.tick(0.1)
    W.env.C_AuctionHouse.PlaceBid(3, 914); W.tick(0.1)
    check(W.find("offen beim Senden 2") == 1, "Lauf 1: dritter Kauf mit 2 offenen gesendet")
    W.fire("AUCTION_HOUSE_PURCHASE_COMPLETED", 1); W.pay(-900)
    W.fire("CHAT_MSG_SYSTEM", "Ihr habt eine Auktion gewonnen für: Schultern des Hügelwächters")
    W.fire("AUCTION_HOUSE_PURCHASE_COMPLETED", 2); W.pay(-905)
    W.fire("UI_ERROR_MESSAGE", 1, "Interner Auktion-Fehler")
    W.env.AHAnalyzerPro.db.sniper.targets["i:4251"].bought = 2
    W.env.AHAnalyzerPro.db.sniper.targets["i:4251"].spent = 1805
    W.tick(1.1)
    check(W.find("KAUF%-OK Angebot 1 · 9s00c · Antwort nach") == 1, "Lauf 1: Kauf 1 bestätigt")
    check(W.find("SYSTEM gewonnen") == 1, "Lauf 1: Systemmeldung als 'gewonnen' eingeordnet")
    check(W.find("Hügelwächter") == 0, "Lauf 1: Itemname aus der Systemmeldung NICHT im Protokoll")
    check(W.find("FEHLER Interner Auktion%-Fehler · offene Käufe 1") == 1, "Lauf 1: Fehler mit offenen Käufen")
    check(W.find("GOLD %-9s00c · AH Kauf") == 1, "Lauf 1: Gold-Abgang als AH Kauf")
    check(W.find("AHS%-ZÄHLER Item 4251 · gekauft 0 %-> 2") == 1, "Lauf 1: AHS-Zähler geändert")
    local sum = table.concat(W.B.SummaryLines(), "\n")
    check(sum:find("gesendet 3 · gekauft 2", 1, true) ~= nil, "Lauf 1: Zusammenfassung gesendet 3, gekauft 2")
    check(sum:find("Differenz 0c", 1, true) ~= nil, "Lauf 1: Gold-Differenz 0")
    check(sum:find("offen 0: 1/1", 1, true) and sum:find("offen 1: 1/1", 1, true) and sum:find("offen ≥2: 0/1", 1, true), "Lauf 1: Erfolg je offene Käufe")
    W.tick(60)
    check(W.find("MINUTE Suchen 1") == 1, "Lauf 1: Minuten-Zusammenfassung")
    W.fire("PLAYER_LOGOUT")
    local ex = W.env.GSSniperLogDB.export
    check(type(ex) == "string" and ex:find("^GSDIAG1|GSSniperLog|1.2|") ~= nil, "Lauf 1: Export beginnt mit GSDIAG1|GSSniperLog|1.2|")
    check(ex:find("== Einträge (", 1, true) ~= nil, "Lauf 1: Export hat '== Einträge'")
    check(W.B.tot.eigeneFehler == nil, "Lauf 1: keine eigenen Fehler")
end

---------------------------------------------------------------------------
-- Lauf 2: doppelt gesendet, keine Antwort in 30 s, späte Bestätigung, AH-Fehlercode, Drossel
---------------------------------------------------------------------------
do
    local W = NewWorld()
    W.fire("PLAYER_LOGIN"); W.fire("AUCTION_HOUSE_SHOW")
    W.env.C_AuctionHouse.PlaceBid(7, 914); W.tick(0.2)
    W.env.C_AuctionHouse.PlaceBid(7, 914); W.tick(0.2)
    check(W.find("DOPPELT GESENDET") == 1, "Lauf 2: Doppel-Sendung erkannt")
    W.fire("AUCTION_HOUSE_SHOW_ERROR", 3)
    check(W.find("AH%-FEHLER Code 3 eigenes Gebot · letzte Anfrage Kauf vor 2%d%d ms · offene Käufe 1") + W.find("AH%-FEHLER Code 3 eigenes Gebot · letzte Anfrage Kauf vor 199 ms · offene Käufe 1") == 1, "Lauf 2: AH-Fehlercode mit letzter Anfrage und offenen Käufen")
    W.fire("AUCTION_HOUSE_THROTTLED_MESSAGE_DROPPED")
    check(W.find("DROSSEL VERWORFEN · letzte Anfrage Kauf vor 2%d%d ms") + W.find("DROSSEL VERWORFEN · letzte Anfrage Kauf vor 199 ms") == 1, "Lauf 2: Drossel verworfen mit Zuordnung")
    W.tick(31)
    check(W.find("KAUF%-OFFEN Angebot 7 · 9s14c · keine Bestätigung in 30 s %(Fehler gesehen: Code 3%)") == 1, "Lauf 2: ohne Antwort nach 30 s")
    W.fire("AUCTION_HOUSE_PURCHASE_COMPLETED", 7)
    check(W.find("SPÄT, nach der Frist") == 1, "Lauf 2: späte Bestätigung")
    W.fire("AUCTION_HOUSE_PURCHASE_COMPLETED", 7)
    check(W.find("zweite Bestätigung") == 1, "Lauf 2: zweite Bestätigung erkannt, nicht doppelt gezählt")
    W.fire("AUCTION_HOUSE_PURCHASE_COMPLETED", 999)
    check(W.find("Bestätigung ohne eigenen Sendevorgang") == 1, "Lauf 2: fremde Bestätigung")
    check(W.B.tot.gekauft == 1 and W.B.tot.spaet == 1 and W.B.tot.doppelt == 1 and W.B.tot.ohneAntwort == 1, "Lauf 2: Zähler gekauft 1/spät 1/doppelt 1/ohne Antwort 1")
    -- Waren
    W.env.C_AuctionHouse.StartCommoditiesPurchase(2589, 20)
    W.env.C_AuctionHouse.ConfirmCommoditiesPurchase(2589, 20); W.tick(0.5)
    W.fire("COMMODITY_PURCHASE_SUCCEEDED")
    check(W.find("WARE%-OK Item 2589 · 20 Stück · Antwort nach 0.50 s") == 1, "Lauf 2: Warenkauf bestätigt")
    W.env.C_AuctionHouse.ConfirmCommoditiesPurchase(2589, 5)
    W.fire("COMMODITY_PURCHASE_FAILED")
    check(W.find("WARE%-FEHLER Item 2589 · 5 Stück") == 1, "Lauf 2: Warenkauf gescheitert")
    check(W.B.tot.eigeneFehler == nil, "Lauf 2: keine eigenen Fehler")
end

---------------------------------------------------------------------------
-- Lauf 3: weggeschnappt, Teilergebnisse, eigene Angebote, Waren-Ergebnis
---------------------------------------------------------------------------
do
    local W = NewWorld()
    W.fire("PLAYER_LOGIN"); W.fire("AUCTION_HOUSE_SHOW")
    W.results[4251] = { offer(11, 800), offer(12, 850), offer(13, 860, true) }
    W.search(4251); W.tick(0.2); W.fire("ITEM_SEARCH_RESULTS_UPDATED", { itemID = 4251 })
    check(W.find("2 unter Max") == 1, "Lauf 3: eigenes Angebot zählt nicht")
    -- Angebot 11 von uns gesendet, Angebot 12 verschwindet ohne uns
    W.env.C_AuctionHouse.PlaceBid(11, 800)
    W.results[4251] = { offer(13, 860, true) }
    W.full[4251] = false                                  -- Teilergebnis: nichts als "weg" werten
    W.search(4251); W.tick(0.5); W.fire("ITEM_SEARCH_RESULTS_UPDATED", { itemID = 4251 })
    check(W.find("^.-WEG") == 0, "Lauf 3: Teilergebnis meldet nichts als weg")
    W.full[4251] = nil
    W.search(4251); W.tick(0.5); W.fire("ITEM_SEARCH_RESULTS_UPDATED", { itemID = 4251 })
    check(W.find("WEG") == 0, "Lauf 3: einmal fehlen reicht nicht")
    W.search(4251); W.tick(0.5); W.fire("ITEM_SEARCH_RESULTS_UPDATED", { itemID = 4251 })
    check(W.find("WEG Item 4251 · Angebot zu 8s50c") == 1, "Lauf 3: Angebot 12 weggeschnappt")
    check(W.find("WEG Item 4251 · Angebot zu 8s00c") == 0, "Lauf 3: eigener gesendeter Kauf zählt nicht als weg")
    -- Wiederholte gleiche Ergebnisse ohne Angebot unter Max: nur einmal im Protokoll
    local before = W.find("ERGEBNIS Item 4251")
    for _ = 1, 5 do W.search(4251); W.tick(0.2); W.fire("ITEM_SEARCH_RESULTS_UPDATED", { itemID = 4251 }) end
    check(W.find("ERGEBNIS Item 4251") == before, "Lauf 3: gleiche leere Ergebnisse nicht wiederholt")
    -- Ware
    W.results[2589] = { { unitPrice = 12, quantity = 40 }, { unitPrice = 15, quantity = 10 }, { unitPrice = 20, quantity = 99 } }
    W.search(2589); W.tick(0.4); W.fire("COMMODITY_SEARCH_RESULTS_UPDATED", 2589)
    check(W.find("ERGEBNIS Ware 2589 · 3 Preisstufen · 50 Stück unter Max 15c · günstigstes 12c · Antwort nach 0.40 s") == 1, "Lauf 3: Waren-Ergebnis")
    -- Item, das kein Ziel ist: kein Protokoll
    W.results[777] = { offer(31, 5) }
    W.fire("ITEM_SEARCH_RESULTS_UPDATED", { itemID = 777 })
    check(W.find("Item 777") == 0, "Lauf 3: fremdes Item nicht protokolliert")
    check(W.B.tot.eigeneFehler == nil, "Lauf 3: keine eigenen Fehler")
end

---------------------------------------------------------------------------
-- Lauf 4: Pausen, Status-Dauer, Bildaussetzer, Gold-Zusammenhang Post/Händler/Einstellen
---------------------------------------------------------------------------
do
    local W = NewWorld()
    W.fire("PLAYER_LOGIN"); W.fire("AUCTION_HOUSE_SHOW")
    W.tick(1.1)
    W.search(4251); W.tick(1.0)
    W.status = "wartet: Vollscan läuft"
    W.tick(8.5)
    W.status = "sucht"
    W.search(4251); W.tick(1.1)
    check(W.find("PAUSE 9%.%d s keine Sniper%-Suche") == 1, "Lauf 4: Pause von ~9.5 s erkannt")
    check(W.find("AHS%-STATUS %d+%.%d s: wartet: Vollscan läuft") == 1, "Lauf 4: Status-Dauer protokolliert (ohne Farbcodes)")
    W.frame(250)
    check(W.find("BILD 250 ms") == 1, "Lauf 4: Bildaussetzer 250 ms")
    W.fire("AUCTION_HOUSE_CLOSED"); W.fire("MAIL_SHOW"); W.pay(50000); W.fire("MAIL_CLOSED"); W.fire("AUCTION_HOUSE_SHOW")
    check(W.find("GOLD %+5g00s00c · Post") == 1, "Lauf 4: Post-Gold")
    W.fire("MERCHANT_SHOW"); W.pay(1234); W.fire("MERCHANT_CLOSED")
    check(W.find("GOLD %+12s34c · Händler") == 1, "Lauf 4: Händler-Gold")
    W.env.C_AuctionHouse.PostItem(); W.pay(-60)
    check(W.find("AH Einstellgebühr") == 1, "Lauf 4: Einstellgebühr erkannt")
    W.tick(70)
    W.pay(-500)
    check(W.find("AH %(ohne Kauf in den letzten 60 s%)") == 1, "Lauf 4: AH-Abgang ohne Kauf")
    W.fire("AUCTION_HOUSE_CLOSED"); W.pay(-1)
    check(W.find("· sonst ·") == 1, "Lauf 4: Gold ausserhalb")
    -- Vollscan
    W.fire("AUCTION_HOUSE_SHOW")
    W.env.C_AuctionHouse.ReplicateItems(); W.tick(14.9); W.fire("REPLICATE_ITEM_LIST_UPDATE")
    check(W.find("VOLLSCAN Antwort nach 14%.9 s") == 1, "Lauf 4: Vollscan-Antwortzeit")
    check(W.B.tot.eigeneFehler == nil, "Lauf 4: keine eigenen Fehler")
end

---------------------------------------------------------------------------
-- Lauf 5: Robustheit – kein AHSentinel, kein Auktionshaus-API, Status wirft Fehler, kaputte Argumente,
-- Begrenzungen, Befehle, keine globalen Lecks
---------------------------------------------------------------------------
do
    -- a) ohne AHSentinel und ohne C_AuctionHouse
    local W = NewWorld({ noAHS = true, noAH = true })
    W.fire("PLAYER_LOGIN"); W.fire("AUCTION_HOUSE_SHOW")
    W.tick(65); W.pay(-100)
    W.fire("ITEM_SEARCH_RESULTS_UPDATED", nil)
    W.fire("COMMODITY_SEARCH_RESULTS_UPDATED", "x")
    W.fire("UI_ERROR_MESSAGE", nil, nil)
    W.fire("CHAT_MSG_SYSTEM", nil)
    W.fire("AUCTION_HOUSE_PURCHASE_COMPLETED", nil)
    W.fire("PLAYER_LOGOUT")
    check(W.B.tot.eigeneFehler == nil, "Lauf 5a: ohne AHS/AH-API keine eigenen Fehler")
    check(W.env.GSSniperLogDB.export:find("AHSentinel%-Version: nicht geladen") ~= nil, "Lauf 5a: Export nennt 'nicht geladen'")
    -- b) Status wirft Fehler
    local W2 = NewWorld({ statusThrows = true })
    W2.fire("PLAYER_LOGIN"); W2.fire("AUCTION_HOUSE_SHOW"); W2.tick(5)
    check(W2.B.tot.eigeneFehler == nil and W2.find("GSSL%-FEHLER") == 0, "Lauf 5b: Fehler in AHS-Status wird abgefangen")
    -- c) Begrenzung 6000 Zeilen und Export-Grösse
    for i = 1, 6100 do W2.env.C_AuctionHouse.CancelAuction(i) end
    check(#W2.log() >= 6000 and #W2.log() <= 6500, "Lauf 5c: 6000–6500 Zeilen (ist " .. #W2.log() .. ")")
    check(W2.log()[#W2.log()]:find("Auktion 6100") ~= nil, "Lauf 5c: neueste Zeile bleibt")
    W2.fire("PLAYER_LOGOUT")
    local ex = W2.env.GSSniperLogDB.export
    check(#ex <= 400000 + 200, "Lauf 5c: Export höchstens 400000 Zeichen")
    local firstEntry = ex:match("== Einträge %(%d+, neueste zuerst%)\n([^\n]*)")
    check(firstEntry and firstEntry:find("Auktion 6100") ~= nil, "Lauf 5c: Export beginnt mit dem neuesten Eintrag")
    -- d) Befehle
    local W3 = NewWorld()
    W3.fire("PLAYER_LOGIN")
    W3.env.SlashCmdList.GSSNIPERLOG("aus")
    W3.env.C_AuctionHouse.CancelAuction(1)
    check(W3.find("ABBRUCH") == 0, "Lauf 5d: aus = nichts mitschreiben")
    check(W3.env.GSSniperLogDB.off == true, "Lauf 5d: aus bleibt gespeichert")
    W3.env.SlashCmdList.GSSNIPERLOG("an")
    W3.env.C_AuctionHouse.CancelAuction(2)
    check(W3.find("ABBRUCH Auktion 2") == 1, "Lauf 5d: an = mitschreiben")
    W3.env.SlashCmdList.GSSNIPERLOG("leeren")
    check(#W3.log() == 0, "Lauf 5d: leeren")
    W3.env.SlashCmdList.GSSNIPERLOG("")
    check(#W3.chat >= 3, "Lauf 5d: Stand im Chat")
    -- e) Gespeichertes 'aus' wirkt nach dem Einloggen
    local W4 = NewWorld()
    W4.env.GSSniperLogDB = { off = true, log = {} }
    W4.fire("PLAYER_LOGIN")
    W4.env.C_AuctionHouse.CancelAuction(3)
    check(W4.find("ABBRUCH") == 0, "Lauf 5e: gespeichertes 'aus' wirkt")
    -- f) keine unerwarteten globalen Namen
    local W5 = NewWorld()
    local allowed = { GSSniperLog = true, GSSniperLogDB = true, SLASH_GSSNIPERLOG1 = true }
    for k in pairs(W5.env) do
        local base = { GetTime=1,date=1,time=1,GetMoney=1,GetBuildInfo=1,DEFAULT_CHAT_FRAME=1,SlashCmdList=1,CreateFrame=1,
            hooksecurefunc=1,debugprofilestop=1,collectgarbage=1,InCombatLockdown=1,ERR_AUCTION_WON_S=1,ERR_AUCTION_BID_PLACED=1,ERR_AUCTION_STARTED=1,ERR_AUCTION_REMOVED=1,
            ERR_AUCTION_SOLD_S=1,C_AuctionHouse=1,AHAnalyzerPro=1,_G=1 }
        if not base[k] and not allowed[k] then check(false, "Lauf 5f: unerwarteter globaler Name " .. tostring(k)) end
    end
    check(true, "Lauf 5f: globale Namen geprüft")
    -- g) Geld-Formatierung
    check(W5.find("x") == 0, "Lauf 5g: vor dem Einloggen kein Protokoll")
end

---------------------------------------------------------------------------
-- Lauf 6 (1.1): Befunde aus dem ersten echten Protokoll 15.11. 14:24
---------------------------------------------------------------------------
do
    local W = NewWorld()
    W.fire("PLAYER_LOGIN"); W.fire("AUCTION_HOUSE_SHOW")
    W.search(4251); W.tick(1.0)
    W.fire("AUCTION_HOUSE_CLOSED"); W.tick(30)
    W.fire("AUCTION_HOUSE_SHOW"); W.tick(1.2); W.search(4251); W.tick(1.1)
    check(W.find("PAUSE") == 0, "Lauf 6: Zeit mit geschlossenem AH ist keine Pause")
    -- Briefkasten blieb "offen" (MAIL_CLOSED fehlte), dann AH auf: Kauf ist AH, nicht Post
    W.fire("AUCTION_HOUSE_CLOSED"); W.fire("MAIL_SHOW"); W.fire("AUCTION_HOUSE_SHOW")
    W.env.C_AuctionHouse.PlaceBid(55, 899); W.tick(0.3)
    W.fire("AUCTION_HOUSE_PURCHASE_COMPLETED", 55); W.pay(-899)
    W.fire("AUCTION_CANCELED", 55)
    check(W.find("GOLD %-8s99c · AH Kauf") == 1, "Lauf 6: Kauf trotz vorher offenem Briefkasten als AH Kauf")
    check(W.find("AUCTION_CANCELED Auktion 55 %(unser Kauf%)") == 1, "Lauf 6: AUCTION_CANCELED bei eigenem Kauf richtig benannt")
    -- verspätete Käufe zählen nicht mehr als offen
    for i = 100, 104 do W.env.C_AuctionHouse.PlaceBid(i, 900) end
    W.tick(31)
    W.env.C_AuctionHouse.PlaceBid(200, 900)
    check(W.find("KAUF%-GESENDET Angebot 200 · 9s00c · offen beim Senden 0") == 1, "Lauf 6: nach Frist offene Käufe = 0")
    -- Fehlercode 10 als Wort
    W.fire("AUCTION_HOUSE_SHOW_ERROR", 10)
    check(W.find("Code 10 Datenbankfehler %(Interner Auktion%-Fehler%)") == 1, "Lauf 6: Code 10 benannt")
    -- Drossel nach einer Suche
    W.search(4251); W.fire("AUCTION_HOUSE_THROTTLED_MESSAGE_DROPPED")
    check(W.find("DROSSEL VERWORFEN · letzte Anfrage Suche vor 0 ms") == 1, "Lauf 6: Drossel nach Suche zugeordnet")
    -- Uhrzeit: Zehntel laufen gleichmässig
    local lines = W.log()
    local ok = true
    for i = 2, #lines do if lines[i]:sub(1, 10) < lines[i - 1]:sub(1, 10) then ok = false end end
    check(ok, "Lauf 6: Uhrzeiten im Protokoll nie rückwärts")
    check(W.B.tot.eigeneFehler == nil, "Lauf 6: keine eigenen Fehler")
end

---------------------------------------------------------------------------
-- Lauf 7 (1.2): Ruckler-Ursachen, Addon-Zeit, Rasten, Server-Bereitschaft
---------------------------------------------------------------------------
do
    -- a) mit Spiel-Profiler
    local W = NewWorld()
    W.env.Enum = { AddOnProfilerMetric = { RecentAverageTime = 1, PeakTime = 4, CountTimeOver50Ms = 8 } }
    local vals = { AHSentinel = { 2.5, 180, 4 }, GuildSentinel = { 0.4, 30, 0 }, LevelPilot = { 1.1, 60, 1 } }
    W.env.C_AddOnProfiler = { GetAddOnMetric = function(n, m)
        local v = vals[n]; if not v then return 0 end
        if m == 1 then return v[1] elseif m == 4 then return v[2] else return v[3] end end }
    W.env.C_AddOns = { GetNumAddOns = function() return 4 end,
        GetAddOnInfo = function(i) return ({ "AHSentinel", "GuildSentinel", "LevelPilot", "NichtGeladen" })[i] end,
        IsAddOnLoaded = function(n) return n ~= "NichtGeladen" end }
    W.env.AHAnalyzerPro.jobs = { { name = "kern:backfill", started = true }, { name = "cache:today" } }
    W.env.AHAnalyzerProWindow = { IsShown = function() return true end }
    local snipe = W.env.CreateFrame("Button")
    W.env.AHAnalyzerProSnipeButton = snipe
    snipe.scripts.OnClick = function() end
    W.fire("PLAYER_LOGIN"); W.fire("AUCTION_HOUSE_SHOW")
    check(W.B.rastenHooked == true, "Lauf 7a: Rasten-Knopf von AHSentinel mitgehört")
    -- Ereignis-Sturm + Ruckler mit Speicherbereinigung
    for _ = 1, 400 do W.fire("UNIT_AURA", "player") end
    for _ = 1, 50 do W.fire("BAG_UPDATE", 0) end
    W.tick(0.1)
    W.mem = 250000
    W.frame(320)
    local bild = nil
    for _, l in ipairs(W.log()) do if l:find("BILD 320 ms") then bild = l end end
    check(bild ~= nil, "Lauf 7a: Ruckler 320 ms festgehalten")
    check(bild and bild:find("AHS%-Aufgaben: kern:backfill%*, cache:today") ~= nil, "Lauf 7a: laufende AHS-Aufgaben genannt")
    check(bild and bild:find("Speicherbereinigung %(−48%.8 MB%)") ~= nil, "Lauf 7a: Speicherbereinigung erkannt")
    check(bild and bild:find("UNIT_AURA 400") ~= nil, "Lauf 7a: Ereignis-Sturm UNIT_AURA genannt")
    check(bild and bild:find("AHS%-Fenster offen") ~= nil, "Lauf 7a: AHS-Fenster offen genannt")
    -- Raste -> Senden, Server nicht bereit
    W.env.C_AuctionHouse.IsThrottledMessageSystemReady = function() return W.ready end
    W.ready = false
    snipe.scripts.OnClick(snipe); W.tick(0.12, 0.12)
    W.env.C_AuctionHouse.PlaceBid(901, 900)
    check(W.find("KAUF%-GESENDET Angebot 901 · 9s00c · offen beim Senden 0 · Server bereit NEIN · 120 ms nach der Raste") == 1, "Lauf 7a: Raste->Senden und Server nicht bereit")
    snipe.scripts.OnClick(snipe); W.tick(1.2)
    check(W.find("RASTE ohne Kauf") == 1, "Lauf 7a: Raste ohne Kauf")
    W.tick(60)
    check(W.find("ADDONS Zeit je Addon %(Spiel%-Profiler%): AHSentinel Ø 2%.50 ms, Spitze 180 ms, >50 ms 4×") == 1, "Lauf 7a: Profiler-Zeile, AHSentinel zuerst")
    check(W.find("NichtGeladen") == 0, "Lauf 7a: nicht geladene Addons fehlen")
    check(W.find("BILDER %d+ Bilder") == 1, "Lauf 7a: Bilder-Zeile je Minute")
    check(W.find("über 100 ms 2 · längstes 320 ms") == 1, "Lauf 7a: Bilder über 100 ms gezählt (320 + 120 ms), längstes 320 ms")
    check(W.find("Rasten 2 %(ohne Kauf 1, Raste%->Senden Ø 120 ms%) · gesendet bei Server nicht bereit: Käufe 1") == 1, "Lauf 7a: Minuten-Zeile Rasten/Server")
    check(W.B.tot.eigeneFehler == nil, "Lauf 7a: keine eigenen Fehler")
    -- b) ohne Profiler: Speicher je Addon, teure Messung schaltet sich ab
    local W2 = NewWorld()
    W2.env.C_AddOns = W.env.C_AddOns
    local mem = { AHSentinel = 40000, GuildSentinel = 3000, LevelPilot = 9000 }
    W2.env.UpdateAddOnMemoryUsage = function() W2.cpu = (W2.cpu or 0) + 45 end      -- kostet 45 ms
    W2.env.GetAddOnMemoryUsage = function(n) return mem[n] or 0 end
    W2.fire("PLAYER_LOGIN"); W2.fire("AUCTION_HOUSE_SHOW")
    W2.tick(60.1)
    check(W2.find("ADDONS Speicher je Addon %(Messung kostete 45 ms, ab jetzt aus%): AHSentinel 39%.1 MB") == 1, "Lauf 7b: Speicher je Addon, teure Messung abgeschaltet")
    W2.tick(60.1)
    check(W2.find("ADDONS Speicher") == 1, "Lauf 7b: danach keine weitere Speichermessung")
    check(W2.B.tot.eigeneFehler == nil, "Lauf 7b: keine eigenen Fehler")
    -- c) ohne alles (kein C_AddOns, kein Profiler, kein Speicher): keine Fehler
    local W3 = NewWorld({ noAHS = true })
    W3.fire("PLAYER_LOGIN"); W3.tick(130); W3.frame(500); W3.fire("PLAYER_LOGOUT")
    check(W3.B.tot.eigeneFehler == nil and W3.find("GSSL%-FEHLER") == 0, "Lauf 7c: ohne Profiler/Addon-Liste keine Fehler")
    check(W3.find("BILD 500 ms · AH zu") == 1, "Lauf 7c: Ruckler auch bei geschlossenem AH festgehalten")
end

---------------------------------------------------------------------------
-- Zufallsläufe (5 Seeds): wilde Ereignisfolgen, Invarianten müssen halten, Zeit je Ereignis messen
---------------------------------------------------------------------------
for seed = 1, 5 do
    math.randomseed(seed * 7919)
    local W = NewWorld()
    W.fire("PLAYER_LOGIN")
    local evs = { "AUCTION_HOUSE_SHOW", "AUCTION_HOUSE_CLOSED", "MAIL_SHOW", "MAIL_CLOSED", "MERCHANT_SHOW", "MERCHANT_CLOSED",
        "AUCTION_HOUSE_SHOW_ERROR", "COMMODITY_PURCHASE_SUCCEEDED", "COMMODITY_PURCHASE_FAILED", "COMMODITY_PRICE_UPDATED",
        "COMMODITY_PRICE_UNAVAILABLE", "AUCTION_CANCELED", "AUCTION_HOUSE_AUCTION_CREATED", "REPLICATE_ITEM_LIST_UPDATE",
        "AUCTION_HOUSE_THROTTLED_MESSAGE_DROPPED", "AUCTION_HOUSE_THROTTLED_MESSAGE_QUEUED", "AUCTION_HOUSE_THROTTLED_SYSTEM_READY" }
    local junk = { nil, 0, -1, "x", {}, { itemID = "a" }, 4251, 2589, 1e12, true }
    local c0 = os.clock()
    local nEv = 0
    for i = 1, 20000 do
        local r = math.random(1, 12)
        if r == 1 then W.search(math.random(1, 2) == 1 and 4251 or 2589)
        elseif r == 2 then
            local L = {}
            for k = 1, math.random(0, 80) do L[k] = offer(math.random(1, 300), math.random(700, 1100), math.random(1, 20) == 1) end
            W.results[4251] = L
            W.full[4251] = (math.random(1, 4) == 1) and false or nil
            W.fire("ITEM_SEARCH_RESULTS_UPDATED", { itemID = 4251 })
        elseif r == 3 then W.env.C_AuctionHouse.PlaceBid(math.random(1, 300), math.random(700, 1000))
        elseif r == 4 then W.fire("AUCTION_HOUSE_PURCHASE_COMPLETED", math.random(1, 320))
        elseif r == 5 then W.pay(math.random(-2000, 2000))
        elseif r == 6 then W.fire("UI_ERROR_MESSAGE", math.random(1, 900), math.random(1, 2) == 1 and "Interner Auktion-Fehler" or nil)
        elseif r == 7 then W.fire("CHAT_MSG_SYSTEM", ({ "Ihr habt eine Auktion gewonnen für: X", "Gebot akzeptiert.", "Hallo Welt", nil })[math.random(1, 4)])
        elseif r == 8 then W.fire(evs[math.random(1, #evs)], junk[math.random(1, #junk)], junk[math.random(1, #junk)])
        elseif r == 9 then W.fire("ITEM_SEARCH_RESULTS_UPDATED", junk[math.random(1, #junk)])
        elseif r == 10 then W.fire("COMMODITY_SEARCH_RESULTS_UPDATED", junk[math.random(1, #junk)])
        elseif r == 11 then
            local t = W.env.AHAnalyzerPro.db.sniper.targets["i:4251"]
            t.bought = t.bought + math.random(0, 1); t.spent = t.spent + math.random(0, 914)
            W.env.AHAnalyzerPro.db.sniper.armed = math.random(1, 5) ~= 1
            W.status = "s" .. math.random(1, 4)
        else W.tick(math.random(1, 30) / 10) end
        nEv = nEv + 1
    end
    local dt = os.clock() - c0
    W.fire("PLAYER_LOGOUT")
    local T = W.B.tot
    check(T.eigeneFehler == nil, "Zufall " .. seed .. ": keine eigenen Fehler (" .. tostring(W.B.lastError) .. ")")
    check((T.gekauft or 0) <= (T.gesendet or 0) + 1, "Zufall " .. seed .. ": gekauft (ohne fremde) nie mehr als gesendet")
    check(#W.log() <= 6500, "Zufall " .. seed .. ": höchstens 6500 Zeilen")
    local ex = W.env.GSSniperLogDB.export
    check(ex:find("^GSDIAG1|GSSniperLog|1.2|") and #ex <= 400200, "Zufall " .. seed .. ": Export gültig")
    check(not ex:find("\0"), "Zufall " .. seed .. ": Export ohne Nullzeichen")
    check(dt / nEv < 0.0005, string.format("Zufall %d: schnell genug (%.3f ms je Ereignis)", seed, dt / nEv * 1000))
    print(string.format("Zufall %d: %d Ereignisse, %.3f ms je Ereignis, %d Zeilen, gesendet %d, gekauft %d, weg %d",
        seed, nEv, dt / nEv * 1000, #W.log(), T.gesendet or 0, T.gekauft or 0, T.weg or 0))
end

print(string.format("Ergebnis: %d OK, %d FEHLER", pass, fail))
os.exit(fail == 0 and 0 or 1)
