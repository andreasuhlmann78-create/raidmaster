-- GSMesstest – Messwerkzeug der Prüf-Sitzung (kein Addon zum Veröffentlichen)
--
-- Misst in WoW Forever, was das geplante Flüster-Netz von GoldSentinelSync braucht:
--   T1 Grundweg   – kommen Addon-Flüsternachrichten an, in beide Richtungen?
--   T2 Drossel    – wie viele pro Sekunde, bevor Nachrichten verloren gehen oder sich verspäten?
--   T3 Offline    – welche Meldung kommt beim Flüstern an einen Offline- bzw. unbekannten Spieler, und lässt sie sich
--                   ausblenden?
--   T4 Realm      – ist der Partner auf demselben internen Realm (gemeinsamer Kanal)? Zusammen mit T1: geht Flüstern
--                   zwischen den internen Realms?
--
-- Beide Spieler brauchen dieses Addon. Ablauf: /gsmess partner <Name>, dann /gsmess alle (nur einer der beiden).
-- Das Ergebnis steht danach im Chat und als "GSDIAG1"-Zeichenkette in den SavedVariables (GSMesstestDB). Nach /reload
-- oder Ausloggen holt der RaidMasterUploader es nach #testberichte -> testberichte/diagnose/GSMesstest/.
--
-- Regeln: Keine Spieler-, Gilden- oder Realmnamen im Ergebnis (das Repo ist öffentlich): Namen werden durch
-- <Ich>, <Partner>, <Offline>, <Unbekannt> ersetzt. Keine geschützten Aktionen, kein Kauf, kein Chat-Text an andere.

local ADDON = "GSMesstest"
local VERSION = "2"
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

local function Report()
    local lines = { "GSMesstest " .. VERSION .. ", Client " .. tostring((GetBuildInfo and select(1, GetBuildInfo())) or "?") ..
        " (" .. tostring((GetBuildInfo and select(4, GetBuildInfo())) or "?") .. ")" }
    for _, id in ipairs({ "a", "b", "c", "d" }) do
        local r = M.runs[id .. (M.nonce or "")]
        if r then lines[#lines + 1] = Anon(RunText(r)) end
    end
    for _, s in ipairs(M.log) do lines[#lines + 1] = s end
    for _, s in ipairs(lines) do Print(s) end
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
    if prefix ~= PREFIX or type(msg) ~= "string" then return end
    local who = Short(sender)
    local kind, id, a, b = msg:match("^(%u):?([^:]*):?([^:]*):?([^:]*)")
    if kind == "M" then
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
    elseif ev == "CHAT_MSG_CHANNEL_LIST" then
        if M.busy and IsOurChannel(a2, a3, a4, ...) then
            M.listText = (M.listText or "") .. " " .. tostring(a1)
        end
    end
end)
f:SetScript("OnUpdate", function()
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
    elseif cmd == "alle" then RunAll({ "t1", "t2", "t3", "t4" })
    elseif T[cmd] then RunAll({ cmd })
    elseif cmd == "bericht" then Report()
    else
        Print("/gsmess partner <Name> – zweiter Spieler mit diesem Addon (online)")
        Print("/gsmess alle – alle vier Messungen (ca. 1 Minute), danach Ergebnis")
        Print("/gsmess t1 | t2 | t3 | t4 – einzeln; /gsmess bericht – Ergebnis nochmals zeigen")
    end
end
