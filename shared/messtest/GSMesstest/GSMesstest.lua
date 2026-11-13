-- GSMesstest – Messwerkzeug der Prüf-Sitzung (kein Addon zum Veröffentlichen)
--
-- Misst in WoW Forever, was das geplante Flüster-Netz von GoldSentinelSync braucht:
--   T1 Grundweg   – kommen Addon-Flüsternachrichten an, in beide Richtungen?
--   T2 Drossel    – wie viele pro Sekunde, bevor Nachrichten verloren gehen oder sich verspäten?
--   T3 Offline    – welche Meldung kommt beim Flüstern an einen Offline- bzw. unbekannten Spieler, und lässt sie sich
--                   ausblenden?
--   T4 Realm      – ist der Partner auf demselben internen Realm (gemeinsamer Kanal)? Zusammen mit T1: geht Flüstern
--                   zwischen den internen Realms?
--   A1 Auktionen  – (ohne Partner, am offenen Auktionshaus) gibt es C_AuctionHouse.ReplicateItems (alle Einzelauktionen
--                   auf einmal)? "/gsmess auktionen" prüft nur, ob es die Funktionen gibt; "/gsmess auktionen holen" ruft
--                   ReplicateItems EINMAL auf (nur lesen) und misst Anzahl, Felder und Restzeit. Keine Namen.
--   A2 Rufen      – (ohne festen Partner) kommen Addon-Nachrichten über "YELL" und "SAY" an Spieler in der Nähe an?
--                   "/gsmess rufen" sendet je eine unsichtbare Addon-Nachricht über YELL und SAY. Jeder Client in der Nähe
--                   mit GSMesstest antwortet per Addon-Flüstern. Gezählt werden: Rückgabewerte, eigenes Echo, Antworten je
--                   Weg, und nebenbei fremde Addon-Nachrichten über YELL/SAY (nur Präfix, keine Namen). Für die
--                   Entdeckung von AHSentinel-Nutzern ausserhalb von Gilde und Gruppe (z. B. am Auktionshaus).
--   A3 Markt      – (ohne Partner, Auktionshaus offen) kann man den Markt KOMPLETT messen? "/gsmess markt" holt alle
--                   Einzelauktionen (ReplicateItems), liest sie ohne Stocken über mehrere Frames, misst Lesezeit und
--                   Speicher, Grösse einer Zusammenfassung je Item (wie viele Addon-Nachrichten für Gilde/Flüstern?),
--                   und vergleicht mit dem letzten Scan: geblieben, verschwunden (je Restzeit-Stufe), neu, Wechsel der
--                   Restzeit-Stufen (Bedeutung der Stufen, M1b), wie oft ein Abruf erlaubt ist (M1c). PASSIV: holt ein
--                   ANDERES Addon (z. B. AHSentinel-Vollscan) die Liste, liest GSMesstest still mit – zeigt, ob fremde
--                   Scans mitgelesen werden können. Keine Namen (Besitzer wird nie gelesen), nur ItemIDs.
--
-- Beide Spieler brauchen dieses Addon. Ablauf: /gsmess partner <Name>, dann /gsmess alle (nur einer der beiden).
-- Das Ergebnis steht danach im Chat und als "GSDIAG1"-Zeichenkette in den SavedVariables (GSMesstestDB). Nach /reload
-- oder Ausloggen holt der RaidMasterUploader es nach #testberichte -> testberichte/diagnose/GSMesstest/.
--
-- Regeln: Keine Spieler-, Gilden- oder Realmnamen im Ergebnis (das Repo ist öffentlich): Namen werden durch
-- <Ich>, <Partner>, <Offline>, <Unbekannt> ersetzt. Keine geschützten Aktionen, kein Kauf, kein Chat-Text an andere.

local ADDON = "GSMesstest"
local VERSION = "5"
local PREFIX = "GSMESS"
local CHANNEL = "GSMessRealm"
local FAKE = "Gsmesszqxv"          -- gibt es sehr wahrscheinlich nicht (Test "unbekannter Spieler")
local PAD = string.rep("x", 200)

GSMesstestDB = GSMesstestDB or {}

local M = { partner = nil, runs = {}, recv = {}, log = {}, sys = {}, tasks = {}, busy = false,
            filterHits = 0, listText = nil, realm = {} }
_G.GSMesstest = M

---------------------------------------------------------------------------
-- Hilfen
---------------------------------------------------------------------------
local function Now() return GetTime and GetTime() or 0 end
local function Print(s) DEFAULT_CHAT_FRAME:AddMessage("|cff33ccff[GSMesstest]|r " .. tostring(s)) end

local function Short(name)
    if type(name) ~= "string" then return "" end
    return (name:gsub("%-.*$", ""))
end

local function MyName()
    local n = UnitName and UnitName("player")
    return type(n) == "string" and n or "?"
end

local OFFLINE_NAME
-- Namen durch Platzhalter ersetzen (vor dem Speichern und vor der Ausgabe)
local function Anon(s)
    s = tostring(s or ""):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("|H.-|h(.-)|h", "%1"):gsub("[\r\n|]", " ")
    local function rep(name, tag)
        if type(name) == "string" and #name >= 2 then
            s = s:gsub(name:gsub("(%W)", "%%%1"), tag)
        end
    end
    rep(M.partner, "<Partner>")
    rep(OFFLINE_NAME, "<Offline>")
    rep(FAKE, "<Unbekannt>")
    rep(MyName(), "<Ich>")
    return s
end

local function Log(s)
    s = Anon(s)
    M.log[#M.log + 1] = s
    Print(s)
end

local function Send(msg, target)
    local CI = _G.C_ChatInfo
    local f = (CI and CI.SendAddonMessage) or _G.SendAddonMessage
    if not f then return false, "keine Funktion" end
    local ok, r = pcall(f, PREFIX, msg, "WHISPER", target)
    if not ok then return false, "Lua-Fehler: " .. tostring(r) end
    return true, tostring(r)
end

local function After(sec, fn) M.tasks[#M.tasks + 1] = { at = Now() + sec, fn = fn } end

---------------------------------------------------------------------------
-- Sender: Messläufe
---------------------------------------------------------------------------
-- Lauf: n Nachrichten im Abstand gap (0 = alle im selben Frame), danach "E" und Warten auf "R"
local function Run(id, label, n, gap, reverse)
    id = id .. (M.nonce or "")
    local r = { id = id, label = label, n = n, gap = gap, sent = 0, ret = {}, t0 = Now(), back = 0, reverse = reverse }
    M.runs[id] = r
    local function one(i)
        local ok, ret = Send("M:" .. id .. ":" .. i .. ":" .. PAD, M.partner)
        r.sent = r.sent + 1
        local k = ok and ("ret " .. ret) or ret
        r.ret[k] = (r.ret[k] or 0) + 1
    end
    if gap <= 0 then
        for i = 1, n do one(i) end
        r.tSend = 0
    else
        for i = 1, n do After((i - 1) * gap, function() one(i); if i == n then r.tSend = Now() - r.t0 end end) end
    end
    After(math.max(0, (n - 1) * gap) + 2, function()
        Send("E:" .. id .. ":" .. n .. ":" .. (reverse and "B" or "-"), M.partner)
    end)
end

local function RunText(r)
    local rets = {}
    for k, v in pairs(r.ret) do rets[#rets + 1] = k .. " ×" .. v end
    table.sort(rets)
    local s = string.format("%s: gesendet %d (Rückgabe %s)", r.label, r.sent, table.concat(rets, ", "))
    if r.report then
        s = s .. string.format(" -> angekommen %d/%d, Ankunft über %.1f s", r.report.count, r.n, r.report.spread)
    else
        s = s .. " -> KEINE Antwort vom Partner"
    end
    if r.reverse then s = s .. string.format("; Rückweg angekommen %d/%d", r.back, r.n) end
    return s
end

local T = {}
local Report          -- weiter unten

function T.t1()
    Log("T1 Grundweg: 10 Nachrichten zu je 200 Zeichen, 4 pro Sekunde, danach 10 zurück")
    Run("a", "T1 hin", 10, 0.25, true)
    return 12
end

function T.t2()
    Log("T2 Drossel: 20 mit 10/s, 50 mit 20/s, 30 im selben Frame")
    Run("b", "T2 10/s", 20, 0.1)
    After(8, function() Run("c", "T2 20/s", 50, 0.05) end)
    After(17, function() Run("d", "T2 Stoss 30", 30, 0) end)
    return 26
end

-- Systemmeldungen beim Flüstern an Offline- und unbekannte Spieler
local function FindOffline()
    if not (IsInGuild and IsInGuild()) then return nil end
    local num = GetNumGuildMembers and GetNumGuildMembers() or 0
    for i = 1, num do
        local name, _, _, _, _, _, _, _, online = GetGuildRosterInfo(i)
        if name and not online and Short(name) ~= MyName() then return Short(name) end
    end
end

function T.t3()
    OFFLINE_NAME = FindOffline()
    M.sysOn = true
    M.filterHits = 0
    M.sys = {}
    if OFFLINE_NAME then
        Log("T3 Offline: 1 Nachricht an ein Offline-Gildenmitglied, dann an einen unbekannten Namen")
        local ok, ret = Send("M:o:1:x", OFFLINE_NAME)
        Log("T3 an <Offline>: Rückgabe " .. tostring(ok and ret or ret))
    else
        Log("T3 Offline: kein Offline-Gildenmitglied gefunden, nur unbekannter Name")
    end
    After(4, function()
        local ok, ret = Send("M:u:1:x", FAKE)
        Log("T3 an <Unbekannt>: Rückgabe " .. tostring(ok and ret or ret))
    end)
    After(8, function()
        M.sysOn = false
        if #M.sys == 0 then
            Log("T3 Ergebnis: KEINE Systemmeldung (Flüstern an Offline-Spieler bleibt still)")
        else
            for _, s in ipairs(M.sys) do Log("T3 Systemmeldung: " .. s) end
            Log("T3 Chat-Filter hat die Meldung abgefangen (ausblendbar): " .. (M.filterHits > 0 and "ja" or "nein"))
        end
    end)
    return 10
end

-- Kanal-Probe: Beide treten demselben Kanal bei; steht der Partner in der Mitgliederliste, ist er auf demselben
-- internen Realm.
local function ListChannel()
    M.listText = nil
    if ListChannelByName then pcall(ListChannelByName, CHANNEL) end
end

function T.t4()
    Log("T4 Realm: beide treten Kanal " .. CHANNEL .. " bei, dann Mitgliederliste")
    Send("J", M.partner)
    local ok = pcall(JoinTemporaryChannel or JoinChannelByName, CHANNEL)
    if not ok then Log("T4: Beitritt fehlgeschlagen") end
    After(5, ListChannel)
    After(9, ListChannel)
    After(12, function()
        local txt = M.listText
        if not txt then
            Log("T4 Ergebnis: keine Mitgliederliste erhalten (Kanal voll belegt? Max. 10 Kanäle) – bitte /chatlist " ..
                CHANNEL .. " von Hand und melden")
        else
            local me = txt:find(MyName(), 1, true) ~= nil
            local pa = M.partner and txt:find(Short(M.partner), 1, true) ~= nil
            Log("T4 Liste enthält <Ich>: " .. (me and "ja" or "nein") .. ", <Partner>: " .. (pa and "ja" or "nein"))
            if me and pa then
                Log("T4 Ergebnis: gleicher interner Realm")
            elseif me then
                Log("T4 Ergebnis: ANDERER interner Realm (oder Partner nicht beigetreten) – T1 zeigt dann, ob Flüstern " ..
                    "zwischen den Realms geht")
            end
        end
        Send("L", M.partner)
        if LeaveChannelByName then pcall(LeaveChannelByName, CHANNEL) end
    end)
    return 14
end


---------------------------------------------------------------------------
-- A1 Auktionen (Messauftrag M1, shared/wissen/markt-strategie.md): alle Einzelauktionen auf einmal?
---------------------------------------------------------------------------
local AH_FUNCS = { "ReplicateItems", "GetNumReplicateItems", "GetReplicateItemInfo", "GetReplicateItemLink",
    "GetReplicateItemTimeLeft", "GetReplicateItemBattlePetInfo", "SendBrowseQuery", "SendSearchQuery",
    "GetItemSearchResultInfo", "GetCommoditySearchResultInfo", "GetNumItemSearchResults" }

local function AHOpen()
    if AuctionHouseFrame and AuctionHouseFrame.IsShown and AuctionHouseFrame:IsShown() then return true end
    if AuctionFrame and AuctionFrame.IsShown and AuctionFrame:IsShown() then return true end
    return false
end

local function AuctionCheck()
    M.log, M.runs = {}, {}
    local C = _G.C_AuctionHouse
    Log("A1 Auktionen: Auktionshaus offen: " .. (AHOpen() and "ja" or "NEIN (bitte am Auktionator öffnen)"))
    Log("A1 C_AuctionHouse: " .. type(C))
    if type(C) == "table" then
        local have = {}
        for _, k in ipairs(AH_FUNCS) do have[#have + 1] = k .. "=" .. (type(C[k]) == "function" and "ja" or "nein") end
        Log("A1 Funktionen: " .. table.concat(have, ", "))
    end
    return C
end

-- Felder von GetReplicateItemInfo (Retail-Reihenfolge): 1 Name, 2 Symbol, 3 Menge, 4 Qualität, 5 benutzbar, 6 Stufe,
-- 7 Stufenart, 8 Mindestgebot, 9 Erhöhung, 10 Sofortkauf, 11 Gebot, 12 Höchstbieter?, 13 Bieter, 14 Besitzer,
-- 15 Besitzer voll, 16 Verkaufsstatus, 17 ItemID, 18 alle Infos. Namen (1, 13, 14, 15) werden NIE ausgegeben.
local function ReplicateResult(reason)
    if not M.replWait then return end
    M.replWait = nil
    local C = _G.C_AuctionHouse
    local n = 0
    local okN, rn = pcall(C.GetNumReplicateItems)
    if okN and type(rn) == "number" then n = rn end
    Log(string.format("A1 Ergebnis (%s, nach %.1f s): Einzelauktionen %d", reason, Now() - (M.replT0 or Now()), n))
    if n > 0 then
        local items, qty, withBuyout, withTime, allInfo = {}, 0, 0, 0, 0
        local tl = {}
        local step = math.max(1, math.floor(n / 2000))       -- höchstens ~2000 ansehen (kein Stocken)
        local seen = 0
        for i = 0, n - 1, step do
            local ok, t = pcall(function() return { C.GetReplicateItemInfo(i) } end)
            if ok and t then
                seen = seen + 1
                if t[17] then items[t[17]] = true end
                qty = qty + (tonumber(t[3]) or 0)
                if (tonumber(t[10]) or 0) > 0 then withBuyout = withBuyout + 1 end
                if t[18] then allInfo = allInfo + 1 end
                if C.GetReplicateItemTimeLeft then
                    local okT, v = pcall(C.GetReplicateItemTimeLeft, i)
                    if okT and v ~= nil then withTime = withTime + 1; tl[tostring(v)] = (tl[tostring(v)] or 0) + 1 end
                end
            end
        end
        local ni = 0
        for _ in pairs(items) do ni = ni + 1 end
        local tls = {}
        for k, v in pairs(tl) do tls[#tls + 1] = k .. ":" .. v end
        table.sort(tls)
        Log(string.format("A1 angesehen %d (jede %d.), verschiedene Items %d, Menge Summe %d, mit Sofortkauf %d, alle Infos %d",
            seen, step, ni, qty, withBuyout, allInfo))
        Log("A1 Restzeit-Stufen (Wert:Anzahl): " .. (#tls > 0 and table.concat(tls, ", ") or "keine Restzeit geliefert"))
        for _, i in ipairs({ 0, math.floor(n / 2), n - 1 }) do
            local ok, t = pcall(function() return { C.GetReplicateItemInfo(i) } end)
            if ok and t then
                local okT, v = pcall(function() return C.GetReplicateItemTimeLeft and C.GetReplicateItemTimeLeft(i) end)
                Log(string.format("A1 Beispiel %d: Felder %d, Menge %s, Mindestgebot %s, Sofortkauf %s, Gebot %s, Status %s, ItemID %s, alle Infos %s, Restzeit %s, Besitzer bekannt %s",
                    i, #t, tostring(t[3]), tostring(t[8]), tostring(t[10]), tostring(t[11]), tostring(t[16]), tostring(t[17]),
                    tostring(t[18]), okT and tostring(v) or "Fehler", (type(t[14]) == "string" and t[14] ~= "") and "ja" or "nein"))
            end
        end
    else
        Log("A1: keine Einzelauktionen – Funktion gesperrt, gedrosselt (bei Blizzard etwa alle 15 Min.) oder ohne Wirkung")
    end
    Report()
end

local function AuctionFetch()
    local C = AuctionCheck()
    if type(C) ~= "table" or type(C.ReplicateItems) ~= "function" then
        Log("A1: ReplicateItems gibt es nicht – nichts abgerufen")
        Report()
        return
    end
    if not AHOpen() then Log("A1: Auktionshaus ist zu – bitte öffnen und nochmals"); Report(); return end
    if InCombatLockdown and InCombatLockdown() then Print("Nicht im Kampf."); return end
    M.busy = true
    M.replWait, M.replT0 = true, Now()
    local ok, err = pcall(C.ReplicateItems)
    Log("A1 ReplicateItems aufgerufen: " .. (ok and "ohne Fehler" or ("Lua-Fehler " .. tostring(err))))
    Print("Warte bis 60 s auf die Liste (das Spiel kann kurz stocken) ...")
    After(60, function() ReplicateResult("Zeitlimit 60 s") end)
end

---------------------------------------------------------------------------
-- A2 Rufen (Messauftrag M5, shared/wissen/kommunikation-forever.md): Addon-Nachrichten über YELL/SAY?
---------------------------------------------------------------------------
-- Passiv: fremde Addon-Nachrichten über SAY/YELL zählen (nur Weg und Präfix, nie Namen)
M.heard = { SAY = 0, YELL = 0, prefixes = {} }
local function Heard(prefix, dist)
    if dist ~= "SAY" and dist ~= "YELL" then return end
    M.heard[dist] = (M.heard[dist] or 0) + 1
    if type(prefix) == "string" and prefix ~= PREFIX then M.heard.prefixes[prefix] = true end
end

local function SendDist(msg, dist)
    local CI = _G.C_ChatInfo
    local f = (CI and CI.SendAddonMessage) or _G.SendAddonMessage
    if not f then return "keine Funktion" end
    local ok, r = pcall(f, PREFIX, msg, dist)
    if not ok then return "Lua-Fehler: " .. tostring(r) end
    return "Rückgabe " .. tostring(r)
end

local function YellResult()
    local y = M.yell
    if not y then return end
    for _, dist in ipairs({ "YELL", "SAY" }) do
        local n = 0
        for _ in pairs(y.answers[dist]) do n = n + 1 end
        Log(string.format("A2 %s: gesendet (%s), eigenes Echo: %s, Antworten von %d Spieler(n) in 30 s",
            dist, y.ret[dist] or "?", y.echo[dist] and "ja" or "nein", n))
    end
    local pre = {}
    for k in pairs(M.heard.prefixes) do pre[#pre + 1] = k end
    table.sort(pre)
    Log(string.format("A2 fremde Addon-Nachrichten seit dem Einloggen: SAY %d, YELL %d, Präfixe: %s",
        M.heard.SAY or 0, M.heard.YELL or 0, #pre > 0 and table.concat(pre, ", ") or "keine"))
    local any = false
    for _, dist in ipairs({ "YELL", "SAY" }) do if next(y.answers[dist]) then any = true end end
    if any then
        Log("A2 Ergebnis: Addon-Nachrichten über YELL/SAY kommen bei anderen an (belegt)")
    elseif y.echo.YELL or y.echo.SAY or (M.heard.SAY or 0) + (M.heard.YELL or 0) > 0 then
        Log("A2 Ergebnis: der Weg geht (Echo bzw. fremde Nachrichten), aber niemand mit GSMesstest hat geantwortet")
    else
        Log("A2 Ergebnis: kein Echo, keine Antwort, keine fremden Nachrichten – YELL/SAY trägt vermutlich keine Addon-Nachrichten")
    end
    M.yell = nil
    Report()
end

local function Rufen()
    if M.busy then Print("Läuft schon.") return end
    if InCombatLockdown and InCombatLockdown() then Print("Nicht im Kampf.") return end
    M.busy, M.runs, M.log = true, {}, {}
    local nonce = string.format("%x", math.floor(Now() * 10) % 65536)
    M.yell = { nonce = nonce, ret = {}, echo = {}, answers = { YELL = {}, SAY = {} } }
    Log("A2 Rufen: sende je eine unsichtbare Addon-Nachricht über YELL und SAY, warte 30 s auf Antworten")
    M.yell.ret.YELL = SendDist("Y:" .. nonce .. ":YELL", "YELL")
    After(1, function() if M.yell then M.yell.ret.SAY = SendDist("Y:" .. nonce .. ":SAY", "SAY") end end)
    After(31, YellResult)
end


---------------------------------------------------------------------------
-- A3 Markt komplett messen (Messauftrag M-KOMPLETT, shared/wissen/markt-strategie.md)
---------------------------------------------------------------------------
-- Signatur einer Auktion = ItemID:Menge:Sofortkauf (es gibt keine auctionID, die Restzeit ändert sich zwischen Scans).
-- Je Signatur wird die Anzahl je Restzeit-Stufe 0..4 in EINER Zahl gespeichert (Basis 1000, exakt bis 2^53).
local MARKT_CHUNK = 3000          -- Auktionen je Frame (kein Stocken)
local function Epoch() return (time and time()) or math.floor(Now()) end
local function Ms() return (debugprofilestop and debugprofilestop()) or (Now() * 1000) end
local function Dec(e)
    local t, n = {}, 0
    for b = 0, 4 do t[b] = math.floor(e / 1000 ^ b) % 1000; n = n + t[b] end
    return t, n
end
local function Since(sec)
    return sec and string.format("%.0f Min. seit letztem Abruf", sec / 60) or "erster Abruf"
end
local function Gold(c) return string.format("%.1fg", (tonumber(c) or 0) / 10000) end

M.ev = {}                         -- Such-Ereignisse zählen (kann man Suchen anderer Addons/von Hand mitlesen?)
M.passiv = 0

local MarktFertig                 -- weiter unten

local function MarktStart(reason)
    local C = _G.C_AuctionHouse
    if M.reader then return end
    local ok, n = pcall(C.GetNumReplicateItems)
    n = ok and tonumber(n) or 0
    if n <= 0 then
        Log("A3 keine Auktionen in der Liste (" .. reason .. ")")
        M.busy = false
        return
    end
    M.busy, M.log, M.runs = true, {}, {}
    collectgarbage("collect")
    M.reader = { n = n, i = 0, reason = reason, wall = Now(), cpu = 0, frames = 0, mem0 = collectgarbage("count"),
                 sigs = {}, items = {}, auctions = 0, noBuyout = 0, noInfo = 0, tl = {}, capped = 0 }
    Print("A3 lese " .. n .. " Auktionen (" .. reason .. ") ...")
end

local function MarktStep()
    local r, C = M.reader, _G.C_AuctionHouse
    local okN, n2 = pcall(C.GetNumReplicateItems)
    if not okN or n2 ~= r.n then
        M.reader = nil
        Log("A3 Liste hat sich während des Lesens geändert (neu geholt?) – abgebrochen, bitte nochmals")
        Report()
        return
    end
    local t0 = Ms()
    local last = math.min(r.n - 1, r.i + MARKT_CHUNK - 1)
    local ok, err = pcall(function()
        local info, tlf = C.GetReplicateItemInfo, C.GetReplicateItemTimeLeft
        local sigs, items, tl = r.sigs, r.items, r.tl
        for i = r.i, last do
            local _, _, count, _, _, _, _, _, _, buyout, _, _, _, _, _, _, itemID = info(i)
            if itemID then
                count, buyout = tonumber(count) or 0, tonumber(buyout) or 0
                local b = tonumber(tlf and tlf(i)) or 0
                if b < 0 or b > 4 then b = 0 end
                r.auctions = r.auctions + 1
                tl[b] = (tl[b] or 0) + 1
                if buyout <= 0 then r.noBuyout = r.noBuyout + 1 end
                local sig = itemID .. ":" .. count .. ":" .. buyout
                local e, p = sigs[sig] or 0, 1000 ^ b
                if math.floor(e / p) % 1000 < 999 then sigs[sig] = e + p else r.capped = r.capped + 1 end
                local it = items[itemID]
                if not it then it = { 0, 0, 0 }; items[itemID] = it end      -- tiefster Stückpreis, Menge, Auktionen
                if buyout > 0 and count > 0 then
                    local u = math.floor(buyout / count)
                    if it[1] == 0 or u < it[1] then it[1] = u end
                end
                it[2], it[3] = it[2] + count, it[3] + 1
            else
                r.noInfo = r.noInfo + 1
            end
        end
    end)
    r.cpu, r.frames = r.cpu + (Ms() - t0), r.frames + 1
    if not ok then
        M.reader = nil
        Log("A3 Lua-Fehler beim Lesen: " .. tostring(err))
        Report()
        return
    end
    r.i = last + 1
    if r.i >= r.n then
        M.reader = nil
        MarktFertig(r)
    end
end

MarktFertig = function(r)
    local L = {}
    local function add(s) L[#L + 1] = s end
    local db = GSMesstestDB
    local now = Epoch()
    local nSig, nAmb, aAmb, nItems = 0, 0, 0, 0
    for _, e in pairs(r.sigs) do
        local _, c = Dec(e)
        nSig = nSig + 1
        if c > 1 then nAmb = nAmb + 1; aAmb = aAmb + c end
    end
    -- Zusammenfassung je Item: so gross wäre ein Vollscan für Gilde/Flüstern/Uploader
    local sumLen = 0
    for id, it in pairs(r.items) do
        nItems = nItems + 1
        sumLen = sumLen + #string.format("%d,%d,%d,%d;", id, it[1], it[2], it[3])
    end
    local msgs = math.ceil(sumLen / 240)
    local mem = collectgarbage("count") - r.mem0
    add(string.format("A3 Scan (%s): Einzelauktionen %d, gelesen %d, ohne Infos %d, ohne Sofortkauf %d, Items %d",
        r.reason, r.n, r.auctions, r.noInfo, r.noBuyout, nItems))
    local tls = {}
    for b = 0, 4 do if r.tl[b] then tls[#tls + 1] = b .. ":" .. r.tl[b] end end
    add("A3 Restzeit-Stufen (Stufe:Anzahl): " .. table.concat(tls, ", "))
    add(string.format("A3 M1d Lesen: %.0f ms Rechenzeit in %d Frames (%d je Frame), %.1f s Gesamtdauer, Speicher +%.1f MB",
        r.cpu, r.frames, MARKT_CHUNK, Now() - r.wall, mem / 1024))
    add(string.format("A3 Wiedererkennung: %d Signaturen (Item:Menge:Sofortkauf), davon %d mehrdeutig mit %d Auktionen (%.1f %%), gekappt %d",
        nSig, nAmb, aAmb, r.auctions > 0 and aAmb * 100 / r.auctions or 0, r.capped))
    add(string.format("A3 Zusammenfassung je Item: %d Zeichen = %d Addon-Nachrichten; Gilde 5/s: %.0f s; Flüstern 40/Min.: %.1f Min. je Empfänger",
        sumLen, msgs, msgs / 5, msgs / 40))
    -- Scans zählen (wie oft wird gescannt, eigen/fremd?)
    db.scans = db.scans or {}
    table.insert(db.scans, { t = now, n = r.auctions, w = r.reason })
    while #db.scans > 50 do table.remove(db.scans, 1) end
    -- Vergleich mit dem letzten Scan
    local base = db.markt
    if base and base.sigs and base.t then
        local dt = now - base.t
        local stay, newc, gone = 0, 0, 0
        local goneB, goneVal = { [0] = 0, 0, 0, 0, 0 }, { [0] = 0, 0, 0, 0, 0 }
        local trans, goneItem = {}, {}
        for sig, e1 in pairs(base.sigs) do
            local b1, c1 = Dec(e1)
            local e2 = r.sigs[sig]
            local b2, c2 = { [0] = 0, 0, 0, 0, 0 }, 0
            if e2 then b2, c2 = Dec(e2) end
            stay = stay + math.min(c1, c2)
            local g = c1 - c2
            if g > 0 then
                gone = gone + g
                local id, _, buy = sig:match("^(%d+):(%d+):(%d+)$")
                -- vorsichtig: die kürzesten Restzeiten zuerst als "abgelaufen" zählen, Stufe 0 (unbekannt) zuletzt
                for _, b in ipairs({ 1, 2, 3, 4, 0 }) do
                    local take = math.min(g, b1[b])
                    if take > 0 then
                        goneB[b] = goneB[b] + take
                        goneVal[b] = goneVal[b] + take * (tonumber(buy) or 0)
                        if (b == 3 or b == 4) and id then goneItem[id] = (goneItem[id] or 0) + take end
                        g = g - take
                    end
                    if g <= 0 then break end
                end
            end
            if c1 == 1 and c2 == 1 then
                local f1, f2
                for b = 0, 4 do
                    if b1[b] == 1 then f1 = b end
                    if b2[b] == 1 then f2 = b end
                end
                local k = tostring(f1) .. ">" .. tostring(f2)
                trans[k] = (trans[k] or 0) + 1
            end
        end
        for sig, e2 in pairs(r.sigs) do
            local _, c2 = Dec(e2)
            local c1 = 0
            if base.sigs[sig] then _, c1 = Dec(base.sigs[sig]) end
            if c2 > c1 then newc = newc + (c2 - c1) end
        end
        add(string.format("A3 Vergleich mit Scan vor %.0f Min. (%d Auktionen, %s): geblieben %d, verschwunden %d, neu %d",
            dt / 60, base.n or 0, tostring(base.w or "?"), stay, gone, newc))
        add(string.format("A3 verschwunden nach Restzeit-Stufe beim letzten Scan: 1: %d, 2: %d, 3: %d, 4: %d, unbekannt: %d",
            goneB[1], goneB[2], goneB[3], goneB[4], goneB[0]))
        add(string.format("A3 verschwunden aus Stufe 3+4 (konnte in %.0f Min. kaum ablaufen -> gekauft oder abgebrochen): %d Auktionen, Sofortkaufwert %s",
            dt / 60, goneB[3] + goneB[4], Gold(goneVal[3] + goneVal[4])))
        local tr = {}
        for k, v in pairs(trans) do tr[#tr + 1] = k .. " " .. v end
        table.sort(tr)
        add("A3 M1b Stufenwechsel eindeutiger Auktionen (vorher>nachher Anzahl): " .. table.concat(tr, ", "))
        local top = {}
        for id, c in pairs(goneItem) do top[#top + 1] = { id, c } end
        table.sort(top, function(x, y) return x[2] > y[2] end)
        local ts = {}
        for i = 1, math.min(10, #top) do ts[#ts + 1] = top[i][1] .. "×" .. top[i][2] end
        add("A3 meiste Abgänge aus Stufe 3+4 (ItemID×Anzahl): " .. (#ts > 0 and table.concat(ts, ", ") or "keine"))
        if dt < 600 then add("A3 Hinweis: Abstand unter 10 Min. – für den Absatz besser 30–60 Min. warten") end
    else
        add("A3 kein früherer Scan gespeichert – in 30–60 Min. nochmals /gsmess markt (oder Vollscan mit AHSentinel)")
    end
    -- neuer Vergleichsstand (wird beim nächsten Scan ersetzt; /gsmess markt löschen entfernt ihn)
    db.markt = { t = now, n = r.auctions, w = r.reason, sigs = r.sigs }
    -- Verlauf aller A3-Ergebnisse (für den Uploader), höchstens 300 Zeilen
    db.hist = db.hist or {}
    table.insert(db.hist, "--- " .. date("%d.%m.%Y %H:%M"))
    for _, s in ipairs(L) do table.insert(db.hist, s) end
    while #db.hist > 300 do table.remove(db.hist, 1) end
    for _, s in ipairs(L) do M.log[#M.log + 1] = s end
    Print(L[1])
    Print(L[#L])
    M.quiet = true
    Report()
    M.quiet = nil
end

local function MarktHolen()
    local C = _G.C_AuctionHouse
    if type(C) ~= "table" or type(C.ReplicateItems) ~= "function" then Print("ReplicateItems gibt es nicht."); return end
    if not AHOpen() then Print("Auktionshaus ist zu – bitte öffnen und nochmals /gsmess markt"); return end
    if M.busy or M.reader or M.marktWait then Print("Läuft schon.") return end
    if InCombatLockdown and InCombatLockdown() then Print("Nicht im Kampf.") return end
    local db = GSMesstestDB
    local since = db.lastCall and (Epoch() - db.lastCall) or nil
    db.lastCall = Epoch()
    M.busy = true
    local wait = { t0 = Now(), since = since }
    M.marktWait = wait
    local ok, err = pcall(C.ReplicateItems)
    if not ok then
        M.marktWait, M.busy = nil, false
        Print("ReplicateItems: Lua-Fehler " .. tostring(err))
        return
    end
    Print("Alle Auktionen angefordert – warte bis 60 s (" .. Since(since) .. ")")
    After(60, function()
        local w = M.marktWait
        if w ~= wait then return end            -- schon beantwortet (oder ein neuerer Abruf wartet)
        M.marktWait = nil
        db.calls = db.calls or {}
        table.insert(db.calls, string.format("%s: KEINE Daten nach 60 s, %s", date("%d.%m. %H:%M"), Since(w.since)))
        M.log, M.runs = {}, {}
        Log("A3 M1c: keine Daten nach 60 s (" .. Since(w.since) .. ") – vermutlich gedrosselt")
        Report()
    end)
end

local function MarktAntwort()
    local w = M.marktWait
    M.marktWait = nil
    local db = GSMesstestDB
    db.calls = db.calls or {}
    table.insert(db.calls, string.format("%s: Daten nach %.1f s, %s", date("%d.%m. %H:%M"), Now() - w.t0, Since(w.since)))
    while #db.calls > 30 do table.remove(db.calls, 1) end
    After(1, function() MarktStart("eigener Abruf") end)
end

local function MarktPassiv()
    M.passiv = M.passiv + 1
    if GSMesstestDB.passivAus or M.reader or M.busy then return end
    if M.lastPassive and Now() - M.lastPassive < 60 then return end
    M.lastPassive = Now()
    Print("A3 fremder Vollscan erkannt (anderes Addon) – lese still mit")
    After(3, function() MarktStart("fremd ausgelöst") end)
end

local function MarktStatus()
    local db = GSMesstestDB
    Print(string.format("A3 fremd ausgelöste Vollscans seit dem Einloggen: %d (Mitlesen %s)", M.passiv,
        db.passivAus and "AUS" or "an"))
    local ev = {}
    for k, v in pairs(M.ev) do ev[#ev + 1] = k .. " " .. v end
    table.sort(ev)
    Print("A3 Such-Ereignisse seit dem Einloggen: " .. (#ev > 0 and table.concat(ev, ", ") or "keine"))
    Print("A3 letzter Vergleichsstand: " .. (db.markt and string.format("vor %.0f Min., %d Auktionen",
        (Epoch() - db.markt.t) / 60, db.markt.n or 0) or "keiner"))
    for _, s in ipairs(db.calls or {}) do Print("A3 M1c " .. s) end
end

Report = function()
    local lines = { "GSMesstest " .. VERSION .. ", Client " .. tostring((GetBuildInfo and select(1, GetBuildInfo())) or "?") ..
        " (" .. tostring((GetBuildInfo and select(4, GetBuildInfo())) or "?") .. ")" }
    for _, id in ipairs({ "a", "b", "c", "d" }) do
        local r = M.runs[id .. (M.nonce or "")]
        if r then lines[#lines + 1] = Anon(RunText(r)) end
    end
    for _, s in ipairs(M.log) do lines[#lines + 1] = s end
    if not M.quiet then for _, s in ipairs(lines) do Print(s) end end
    -- A3: Verlauf aller Markt-Messungen und der Abruf-Versuche (M1c) immer mitgeben
    local db = GSMesstestDB
    if db.hist and #db.hist > 0 then
        lines[#lines + 1] = "A3 Verlauf:"
        for _, s in ipairs(db.hist) do lines[#lines + 1] = s end
    end
    if db.calls and #db.calls > 0 then
        for _, s in ipairs(db.calls) do lines[#lines + 1] = "A3 M1c " .. s end
    end
    local ev = {}
    for k, v in pairs(M.ev or {}) do ev[#ev + 1] = k .. " " .. v end
    table.sort(ev)
    lines[#lines + 1] = string.format("A3 fremd ausgelöste Vollscans in dieser Sitzung: %d; Such-Ereignisse: %s",
        M.passiv or 0, #ev > 0 and table.concat(ev, ", ") or "keine")
    GSMesstestDB.export = "GSDIAG1|" .. ADDON .. "|" .. VERSION .. "|" .. date("%d.%m.%Y %H:%M") .. "\n" ..
        table.concat(lines, "\n")
    Print("Gespeichert. Nach /reload oder Ausloggen holt der Uploader das Ergebnis ab.")
    M.busy = false
end

local function RunAll(which)
    if not M.partner then Print("Zuerst: /gsmess partner <Name> (der zweite Spieler braucht das Addon auch)"); return end
    if M.busy then Print("Läuft schon.") return end
    if InCombatLockdown and InCombatLockdown() then Print("Nicht im Kampf.") return end
    M.busy, M.runs, M.log = true, {}, {}
    M.nonce = string.format("%x", math.floor(Now() * 10) % 65536)   -- neue Lauf-Kennung: Empfänger zählt je Lauf neu
    Log("Start mit <Partner>. Bitte nichts anderes tun, ca. 1 Minute.")
    local t = 0
    for _, k in ipairs(which) do
        After(t, function() T[k]() end)
        t = t + ({ t1 = 12, t2 = 26, t3 = 10, t4 = 14 })[k]
    end
    After(t + 1, Report)
end

---------------------------------------------------------------------------
-- Empfänger (läuft bei beiden Spielern)
---------------------------------------------------------------------------
local function OnAddon(prefix, msg, dist, sender)
    if dist == "SAY" or dist == "YELL" then
        if prefix ~= PREFIX then Heard(prefix, dist); return end
    end
    if prefix ~= PREFIX or type(msg) ~= "string" then return end
    local who = Short(sender)
    local kind, id, a, b = msg:match("^(%u):?([^:]*):?([^:]*):?([^:]*)")
    if kind == "Y" then
        -- A2: Ruf über YELL/SAY empfangen
        if who == MyName() then
            if M.yell and M.yell.nonce == id then M.yell.echo[dist] = true end
            return
        end
        M.yellSeen = M.yellSeen or {}
        local key = who .. ":" .. id .. ":" .. tostring(dist)
        if M.yellSeen[key] then return end
        M.yellSeen[key] = true
        Send("Z:" .. id .. ":" .. tostring(dist), sender)
        Print("Ruf eines anderen Messtests über " .. tostring(dist) .. " empfangen – Antwort gesendet")
        return
    elseif kind == "Z" then
        local y = M.yell
        if y and y.nonce == id and y.answers[a] then y.answers[a][who] = true end
        return
    elseif kind == "M" then
        local key = who .. ":" .. id
        local r = M.recv[key] or { count = 0, first = Now() }
        r.count, r.last = r.count + 1, Now()
        M.recv[key] = r
        local run = id:sub(1, 1) == "r" and M.runs[id:sub(2)]
        if run then run.back = run.back + 1 end
    elseif kind == "E" then
        local r = M.recv[who .. ":" .. id] or { count = 0, first = Now(), last = Now() }
        Send(string.format("R:%s:%d:%d", id, r.count, math.floor(((r.last or r.first) - r.first) * 1000)), sender)
        if b == "B" then
            local n = tonumber(a) or 0
            for i = 1, n do After((i - 1) * 0.25, function() Send("M:r" .. id .. ":" .. i .. ":" .. PAD, sender) end) end
        end
        if not M.busy then Print("Messung von " .. who .. ": Lauf " .. id .. " – " .. r.count .. " angekommen") end
    elseif kind == "R" then
        local run = M.runs[id]
        if run then run.report = { count = tonumber(a) or 0, spread = (tonumber(b) or 0) / 1000 } end
    elseif kind == "J" then
        pcall(JoinTemporaryChannel or JoinChannelByName, CHANNEL)
        Print(who .. " misst den Realm: Kanal " .. CHANNEL .. " kurz beigetreten")
        After(30, function() if LeaveChannelByName then pcall(LeaveChannelByName, CHANNEL) end end)
    elseif kind == "L" then
        if LeaveChannelByName then pcall(LeaveChannelByName, CHANNEL) end
    end
end

-- Systemmeldungen während T3 sammeln und den Filter testen
local function SysFilter(_, _, msg)
    if M.sysOn and type(msg) == "string" then
        if (OFFLINE_NAME and msg:find(OFFLINE_NAME, 1, true)) or msg:find(FAKE, 1, true) then
            M.filterHits = M.filterHits + 1
            return true      -- ausblenden
        end
    end
    return false
end
if ChatFrame_AddMessageEventFilter then ChatFrame_AddMessageEventFilter("CHAT_MSG_SYSTEM", SysFilter) end

-- Kanal-Mitgliederliste aus /chatlist bzw. ListChannelByName während T4 abfangen (nicht im Chat zeigen)
-- (nur ausblenden; gesammelt wird im Ereignis unten – Filter laufen je Chatfenster einmal)
local function IsOurChannel(...)
    for i = 1, select("#", ...) do
        local v = select(i, ...)
        if type(v) == "string" and v:lower():find(CHANNEL:lower(), 1, true) then return true end
    end
    return false
end
local function ListFilter(_, _, msg, ...)
    return M.busy and IsOurChannel(...) or false
end
if ChatFrame_AddMessageEventFilter then ChatFrame_AddMessageEventFilter("CHAT_MSG_CHANNEL_LIST", ListFilter) end

---------------------------------------------------------------------------
-- Rahmen, Ereignisse, Befehl
---------------------------------------------------------------------------
local f = CreateFrame("Frame")
f:RegisterEvent("PLAYER_LOGIN")
f:RegisterEvent("CHAT_MSG_ADDON")
f:RegisterEvent("CHAT_MSG_SYSTEM")
f:RegisterEvent("CHAT_MSG_CHANNEL_LIST")
pcall(f.RegisterEvent, f, "REPLICATE_ITEM_LIST_UPDATE")
local SEARCH_EVENTS = { "AUCTION_HOUSE_BROWSE_RESULTS_UPDATED", "ITEM_SEARCH_RESULTS_UPDATED",
    "COMMODITY_SEARCH_RESULTS_UPDATED", "AUCTION_ITEM_LIST_UPDATE" }
for _, e in ipairs(SEARCH_EVENTS) do pcall(f.RegisterEvent, f, e) end
f:SetScript("OnEvent", function(_, ev, a1, a2, a3, a4, ...)
    if ev == "PLAYER_LOGIN" then
        local CI = _G.C_ChatInfo
        local reg = (CI and CI.RegisterAddonMessagePrefix) or _G.RegisterAddonMessagePrefix
        if reg then pcall(reg, PREFIX) end
        if GuildRoster then pcall(GuildRoster) elseif C_GuildInfo and C_GuildInfo.GuildRoster then pcall(C_GuildInfo.GuildRoster) end
    elseif ev == "CHAT_MSG_ADDON" then
        OnAddon(a1, a2, a3, a4)
    elseif ev == "CHAT_MSG_SYSTEM" then
        if M.sysOn and #M.sys < 10 then M.sys[#M.sys + 1] = Anon(a1) end
    elseif ev == "REPLICATE_ITEM_LIST_UPDATE" then
        if M.replWait then After(2, function() ReplicateResult("Ereignis REPLICATE_ITEM_LIST_UPDATE") end)
        elseif M.marktWait then MarktAntwort()
        elseif AHOpen() then MarktPassiv() end
    elseif ev == "AUCTION_HOUSE_BROWSE_RESULTS_UPDATED" or ev == "ITEM_SEARCH_RESULTS_UPDATED"
        or ev == "COMMODITY_SEARCH_RESULTS_UPDATED" or ev == "AUCTION_ITEM_LIST_UPDATE" then
        M.ev[ev] = (M.ev[ev] or 0) + 1
    elseif ev == "CHAT_MSG_CHANNEL_LIST" then
        if M.busy and IsOurChannel(a2, a3, a4, ...) then
            M.listText = (M.listText or "") .. " " .. tostring(a1)
        end
    end
end)
f:SetScript("OnUpdate", function()
    if M.reader then
        local ok, err = pcall(MarktStep)
        if not ok then M.reader = nil; M.busy = false; Log("Lua-Fehler: " .. tostring(err)) end
    end
    if #M.tasks == 0 then return end
    local now, keep = Now(), {}
    local due = {}
    for _, t in ipairs(M.tasks) do
        if t.at <= now then due[#due + 1] = t else keep[#keep + 1] = t end
    end
    M.tasks = keep
    table.sort(due, function(x, y) return x.at < y.at end)
    for _, t in ipairs(due) do
        local ok, err = pcall(t.fn)
        if not ok then Log("Lua-Fehler: " .. tostring(err)) end
    end
end)

SLASH_GSMESSTEST1 = "/gsmess"
SlashCmdList.GSMESSTEST = function(arg)
    local cmd, rest = tostring(arg or ""):match("^%s*(%S*)%s*(.-)%s*$")
    cmd = cmd:lower()
    if cmd == "partner" and rest ~= "" then
        M.partner = Short(rest)
        Print("Partner gesetzt. Der Partner braucht GSMesstest auch. Dann: /gsmess alle")
    elseif cmd == "auktionen" then
        if rest:lower() == "holen" then AuctionFetch() else AuctionCheck(); Report() end
    elseif cmd == "rufen" then Rufen()
    elseif cmd == "markt" then
        local r = rest:lower()
        if r == "status" then MarktStatus()
        elseif r == "löschen" or r == "loeschen" then
            GSMesstestDB.markt, GSMesstestDB.hist, GSMesstestDB.calls, GSMesstestDB.scans = nil, nil, nil, nil
            Print("Markt-Messdaten gelöscht.")
        elseif r == "mitlesen aus" then GSMesstestDB.passivAus = true; Print("Mitlesen fremder Vollscans: aus")
        elseif r == "mitlesen an" then GSMesstestDB.passivAus = nil; Print("Mitlesen fremder Vollscans: an")
        else MarktHolen() end
    elseif cmd == "alle" then RunAll({ "t1", "t2", "t3", "t4" })
    elseif T[cmd] then RunAll({ cmd })
    elseif cmd == "bericht" then Report()
    else
        Print("/gsmess partner <Name> – zweiter Spieler mit diesem Addon (online)")
        Print("/gsmess alle – alle vier Messungen (ca. 1 Minute), danach Ergebnis")
        Print("/gsmess t1 | t2 | t3 | t4 – einzeln; /gsmess bericht – Ergebnis nochmals zeigen")
        Print("/gsmess auktionen – gibt es alle Einzelauktionen? (ohne Partner, Auktionshaus offen); dann /gsmess auktionen holen")
        Print("/gsmess rufen – kommen Addon-Nachrichten über YELL/SAY bei Spielern in der Nähe an? (30 s, ohne Partner)")
        Print("/gsmess markt – ganzen Markt messen (Auktionshaus offen); nach 30–60 Min. nochmals = Absatz-Vergleich")
        Print("/gsmess markt status | löschen | mitlesen an | mitlesen aus – fremde Vollscans (z. B. AHSentinel) liest es still mit")
    end
end
