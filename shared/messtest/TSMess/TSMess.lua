-- TSMess 1.1 – passives Messwerkzeug für ThreatSentinel (N4-MESS, 16.11.2026)
-- Frage: Liefert WoW Forever im Kampf lesbare Bedrohungswerte? Nur dann kann ThreatSentinel einem DD sagen,
-- WIE BALD er Aggro zieht ("Zeit bis Pull", Bedrohung je Sekunde) – Wunsch N4 aus dem Nutzen-Ausbau TS-N1.
-- Gemessen wird je Sekunde im Kampf, für das aktuelle Ziel:
--   UnitDetailedThreatSituation(Einheit, "target") -> isTanking, status, scaledPercent, rawPercent, threatValue
--   UnitThreatSituation(Einheit, "target") und UnitThreatSituation(Einheit)
-- Einheiten: player, pet, party1–party4 (nur Kennungen, KEINE Namen). Im Schlachtzug zusätzlich raid1–raid40, aber nur
-- die Einheiten, die das Ziel gerade tanken (isTanking wahr oder geschützt) – sonst wären es bis zu 40 Zeilen je Sekunde.
-- Dazu Kampf-Beginn/-Ende und Zielwechsel.
-- Jeder Wert wird nur als Art + Zahl gespeichert:  -  = nil · G = geschützt (secret) · 1/0 = wahr/falsch ·
--   Zahl mit 2 Nachkommastellen (zeigt, ob gerundet geliefert wird).
-- Es kauft nichts, ändert nichts, sendet nichts. Läuft nach /tsmess start, endet von selbst nach 60 Minuten.
-- Befehle: /tsmess start · /tsmess stop · /tsmess (Stand)
-- Ergebnis: SavedVariables TSMessDB (WTF/.../SavedVariables/TSMess.lua) – nach /reload hochladen oder schicken.
-- Auswertung: python3 -I shared/messtest/TSMess/auswerten.py <TSMess.lua>

local M = {}
_G.TSMess = M
M.VERSION = "1.1"
M.STEP = 1.0            -- Sekunden zwischen zwei Messungen im Kampf
M.MAX_LINES = 6000      -- älteste Zeilen fallen weg
M.MAX_RUN = 60 * 60     -- Sekunden: danach endet die Messung von selbst (keine Messung ohne Zeitlimit)
M.UNITS = { "player", "pet", "party1", "party2", "party3", "party4" }

local function Call(fn, ...)
    if type(fn) ~= "function" then return false end
    return pcall(fn, ...)
end

-- Art eines Werts, ohne einen geschützten Wert je zu benutzen
local function IsSecret(v)
    local f = _G.issecretvalue
    if type(f) == "function" then
        local ok, r = pcall(f, v)
        if ok and r then return true end
    end
    return false
end
-- Reihenfolge wichtig (Hinweis Prüf-Sitzung 16.11.): ZUERST auf "geschützt" prüfen – in Clients mit geschützten Werten
-- darf ein geschützter Wert nicht verglichen werden (auch nicht mit nil), sonst ginge die ganze Messung verloren.
function M.Enc(v)
    if IsSecret(v) then return "G" end
    if v == nil then return "-" end
    if type(v) == "boolean" then return v and "1" or "0" end
    if type(v) == "number" then
        local ok, s = pcall(string.format, "%.2f", v)
        return ok and s or "G"
    end
    return "?"
end

local function Add(db, line)
    db.lines[#db.lines + 1] = line
    while #db.lines > M.MAX_LINES do table.remove(db.lines, 1) end
end

local function Now() return (_G.GetTime and _G.GetTime()) or 0 end

local function DB()
    _G.TSMessDB = type(_G.TSMessDB) == "table" and _G.TSMessDB or {}
    local db = _G.TSMessDB
    if type(db.lines) ~= "table" then db.lines = {} end
    return db
end

M.running, M.t0, M.acc, M.inFight = false, 0, 0, false

local function T() return string.format("%.1f", Now() - M.t0) end

local function InCombat()
    local ok, r = Call(_G.UnitAffectingCombat, "player")
    return ok and r == true
end

-- eine Messung je Einheit: Zeit|U|Einheit|isTanking|status|scaled|raw|value|uts_ziel|uts_allein
local function SampleUnit(db, u, onlyTank)
    local okU, ex = Call(_G.UnitExists, u)
    if not (okU and ex == true) then return end
    local ok, a, b, c, d, e = Call(_G.UnitDetailedThreatSituation, u, "target")
    if not ok then a, b, c, d, e = nil, nil, nil, nil, nil end
    if onlyTank then
        -- Schlachtzug: nur wer das Ziel tankt (oder geschützt ist) – zuerst geschützt prüfen, dann vergleichen
        if not (IsSecret(a) or (ok and a == true)) then return end
    end
    local ok2, s1 = Call(_G.UnitThreatSituation, u, "target")
    local ok3, s2 = Call(_G.UnitThreatSituation, u)
    Add(db, table.concat({ T(), "U", u, M.Enc(a), M.Enc(b), M.Enc(c), M.Enc(d), M.Enc(e),
        ok2 and M.Enc(s1) or "F", ok3 and M.Enc(s2) or "F", ok and "" or "F" }, "|"))
end

function M.Sample()
    local db = DB()
    local okE, hasTarget = Call(_G.UnitExists, "target")
    if not (okE and hasTarget == true) then
        Add(db, T() .. "|Z|-|kein Ziel")
        return
    end
    local okR, inRaid = Call(_G.IsInRaid)
    inRaid = okR and inRaid == true
    for _, u in ipairs(M.UNITS) do
        if not (inRaid and u:find("^party")) then SampleUnit(db, u, false) end
    end
    if inRaid then
        for i = 1, 40 do SampleUnit(db, "raid" .. i, true) end
    end
end

function M.Start()
    local db = DB()
    M.running, M.t0, M.acc, M.inFight = true, Now(), 0, InCombat()
    local stamp = (_G.date and _G.date("%d.%m.%Y %H:%M:%S")) or "?"
    local build = (_G.GetBuildInfo and select(4, _G.GetBuildInfo())) or "?"
    Add(db, string.format("# TSMess %s Start %s · Interface %s · Spalten: Zeit|Art|Einheit|isTanking|status|scaled|raw|value|uts_ziel|uts|Fehler",
        M.VERSION, stamp, tostring(build)))
    Add(db, T() .. "|E|-|START" .. (M.inFight and " im Kampf" or ""))
end

function M.Stop(why)
    if not M.running then return end
    Add(DB(), T() .. "|E|-|STOP " .. (why or "Befehl"))
    M.running = false
end

function M.Running() return M.running end

function M.OnUpdate(_, dt)
    if not M.running then return end
    if Now() - M.t0 > M.MAX_RUN then M.Stop("Zeitlimit") return end
    if not M.inFight then return end
    M.acc = M.acc + (dt or 0)
    if M.acc < M.STEP then return end
    M.acc = 0
    local ok = pcall(M.Sample)
    if not ok then Add(DB(), T() .. "|E|-|FEHLER Messung") end
end

function M.OnEvent(_, event)
    if not M.running then return end
    if event == "PLAYER_REGEN_DISABLED" then
        M.inFight, M.acc = true, M.STEP      -- gleich die erste Messung
        Add(DB(), T() .. "|E|-|KAMPF Beginn")
    elseif event == "PLAYER_REGEN_ENABLED" then
        M.inFight = false
        Add(DB(), T() .. "|E|-|KAMPF Ende")
    elseif event == "PLAYER_TARGET_CHANGED" and M.inFight then
        Add(DB(), T() .. "|E|-|Zielwechsel")
    end
end

local frame = _G.CreateFrame and _G.CreateFrame("Frame") or nil
if frame then
    for _, e in ipairs({ "PLAYER_REGEN_DISABLED", "PLAYER_REGEN_ENABLED", "PLAYER_TARGET_CHANGED" }) do
        pcall(frame.RegisterEvent, frame, e)
    end
    frame:SetScript("OnEvent", M.OnEvent)
    frame:SetScript("OnUpdate", M.OnUpdate)
end

local function Say(s) if _G.print then _G.print("|cff33ccffTSMess|r " .. s) end end

_G.SLASH_TSMESS1 = "/tsmess"
_G.SlashCmdList = _G.SlashCmdList or {}
_G.SlashCmdList.TSMESS = function(arg)
    arg = tostring(arg or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
    if arg == "start" then
        M.Start()
        Say("Messung läuft (höchstens 60 Minuten). Jetzt als Tank oder DD kämpfen, danach /tsmess stop und /reload.")
    elseif arg == "stop" then
        M.Stop("Befehl")
        Say("Messung beendet. /reload schreibt TSMessDB in die SavedVariables.")
    else
        Say(string.format("%s · %d Zeilen · /tsmess start | stop", M.running and "läuft" or "steht", #DB().lines))
    end
end
