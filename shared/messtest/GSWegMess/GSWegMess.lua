-- GSWegMess 1.0 – passives Messwerkzeug der GoldSentinel-Prüfung (Supervisor, 15.11.2026)
-- Zweck: herausfinden, an welchen Zeichen das Spiel eine EBENE erkennen lässt (Städte mit Stockwerken, Aufzüge, Höhlen),
-- damit LevelPilot Wege in der 3D-Welt richtig findet (Konzept shared/wissen/analysen/levelpilot-wegfuehrung-3d.md).
-- WoW gibt Addons keine Höhe (UnitPosition: Z immer 0). Darum werden alle anderen Zeichen mitgeschrieben:
--   Karte, Kleinkarte an der Stelle, Zone, Unterzone, Minikarten-Zone, drinnen/draussen, fällt, schwimmt, Tempo,
--   Ereignisse ZONE_CHANGED / ZONE_CHANGED_INDOORS / ZONE_CHANGED_NEW_AREA / NEW_WMO_CHUNK.
-- Es kauft nichts, ändert nichts, sendet nichts. Läuft nur nach /wegmess start, endet von selbst nach 30 Minuten.
-- Befehle: /wegmess start · /wegmess stop · /wegmess mark <Text> (z. B. "Aufzug unten") · /wegmess (Stand)
-- Ergebnis: SavedVariables GSWegMessDB (Datei WTF/.../SavedVariables/GSWegMess.lua) – nach /reload an den Supervisor schicken.

local W = {}
_G.GSWegMess = W
W.VERSION = "1.0"
W.STEP = 0.2            -- Sekunden zwischen zwei Abfragen
W.POS_EVERY = 1.0       -- spätestens so oft eine Zeile mit Position (auch ohne Änderung), nur wenn man sich bewegt
W.MAX_LINES = 8000      -- älteste Zeilen fallen weg
W.MAX_RUN = 30 * 60     -- Sekunden: danach endet die Messung von selbst (keine Messung ohne Zeitlimit)

local function Call(fn, ...)
    if type(fn) ~= "function" then return nil end
    local ok, a, b, c, d = pcall(fn, ...)
    if ok then return a, b, c, d end
    return nil
end

-- geschützte Werte (Forever, im Kampf) nie weiterverwenden: nur echte Zahlen/Texte, die sich formatieren lassen
local function Num(v)
    if type(v) ~= "number" then return nil end
    local ok, s = pcall(string.format, "%.2f", v)
    return ok and tonumber(s) or nil
end
local function Txt(v)
    if type(v) ~= "string" then return nil end
    local ok, s = pcall(string.format, "%s", v)
    if not ok then return nil end
    s = s:gsub("|", "/")
    return s
end
local function Flag(v) if v == nil then return "-" end return v and "1" or "0" end

function W.Sample()
    local CM = _G.C_Map
    local map = CM and Call(CM.GetBestMapForUnit, "player")
    map = Num(map)
    local x, y, sub
    if map and CM then
        local pos = Call(CM.GetPlayerMapPosition, map, "player")
        if type(pos) == "table" and pos.GetXY then
            local ok, px, py = pcall(pos.GetXY, pos)
            if ok then x, y = Num(px), Num(py) end
        end
        if x and y and CM.GetMapInfoAtPosition then
            local info = Call(CM.GetMapInfoAtPosition, map, x, y)
            if type(info) == "table" then sub = Num(info.mapID) end
        end
    end
    local s = {
        map = map, x = x and Num(x * 100), y = y and Num(y * 100), sub = sub,
        zone = Txt(Call(_G.GetRealZoneText)) or Txt(Call(_G.GetZoneText)),
        subzone = Txt(Call(_G.GetSubZoneText)),
        mini = Txt(Call(_G.GetMinimapZoneText)),
        indoors = Call(_G.IsIndoors), falling = Call(_G.IsFalling), swimming = Call(_G.IsSwimming),
        speed = Num((Call(_G.GetUnitSpeed, "player"))),
    }
    return s
end

local function Key(s)
    return table.concat({ tostring(s.map), tostring(s.sub), s.zone or "", s.subzone or "", s.mini or "",
        Flag(s.indoors), Flag(s.falling), Flag(s.swimming) }, "|")
end

local function Line(t, s, ev)
    return string.format("%.1f|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s", t,
        s.x and string.format("%.2f", s.x) or "-", s.y and string.format("%.2f", s.y) or "-",
        tostring(s.map or "-"), tostring(s.sub or "-"), s.zone or "-", s.subzone or "-", s.mini or "-",
        Flag(s.indoors), Flag(s.falling), Flag(s.swimming), s.speed and string.format("%.1f", s.speed) or "-", ev or "")
end

local run              -- laufende Messung: { t0, last, lastKey, lastPosT, n }
local function DB()
    _G.GSWegMessDB = type(_G.GSWegMessDB) == "table" and _G.GSWegMessDB or {}
    local db = _G.GSWegMessDB
    db.lines = type(db.lines) == "table" and db.lines or {}
    return db
end
local function Add(text)
    local db = DB()
    local l = db.lines
    l[#l + 1] = text
    while #l > W.MAX_LINES do table.remove(l, 1) end
end
local function Now() return (_G.GetTime and _G.GetTime()) or 0 end

function W.Record(ev)
    if not run then return end
    local ok, s = pcall(W.Sample)
    if not ok or type(s) ~= "table" then return end
    local t = Now() - run.t0
    local k = Key(s)
    local moving = (s.speed or 0) > 0
    if ev or k ~= run.lastKey or (moving and t - (run.lastPosT or -99) >= W.POS_EVERY) then
        Add(Line(t, s, ev))
        run.lastKey, run.lastPosT, run.n = k, t, run.n + 1
    end
end

function W.Start()
    local db = DB()
    db.version, db.started = W.VERSION, (_G.date and _G.date("%d.%m.%Y %H:%M:%S")) or "?"
    Add("# GSWegMess " .. W.VERSION .. " Start " .. db.started .. " · Spalten: Zeit|x|y|Karte|Kleinkarte|Zone|Unterzone|Minikarte|drinnen|fällt|schwimmt|Tempo|Ereignis/Notiz")
    run = { t0 = Now(), acc = 0, lastKey = nil, lastPosT = nil, n = 0 }
    W.Record("START")
end
function W.Stop(why)
    if not run then return end
    W.Record("STOP " .. (why or ""))
    run = nil
end
function W.Mark(text)
    if not run then return false end
    W.Record("MARK " .. (Txt(text) or ""))
    return true
end
function W.Running() return run ~= nil end

local frame = _G.CreateFrame and _G.CreateFrame("Frame") or nil
W.frame = frame
if frame then
    for _, e in ipairs({ "ZONE_CHANGED", "ZONE_CHANGED_INDOORS", "ZONE_CHANGED_NEW_AREA", "NEW_WMO_CHUNK" }) do
        pcall(frame.RegisterEvent, frame, e)          -- NEW_WMO_CHUNK gibt es nicht in jedem Client
    end
    frame:SetScript("OnEvent", function(_, e) if run then W.Record(e) end end)
    frame:SetScript("OnUpdate", function(_, dt)
        if not run then return end
        run.acc = run.acc + (dt or 0)
        if run.acc < W.STEP then return end
        run.acc = 0
        if Now() - run.t0 > W.MAX_RUN then W.Stop("Zeitlimit 30 Min."); return end
        W.Record(nil)
    end)
end

local function Print(msg) if _G.print then _G.print("|cff33ccffGSWegMess|r " .. msg) end end
_G.SLASH_GSWEGMESS1 = "/wegmess"
_G.SlashCmdList = _G.SlashCmdList or {}
_G.SlashCmdList.GSWEGMESS = function(arg)
    arg = Txt(arg) or ""
    local cmd, rest = arg:match("^(%S*)%s*(.*)$")
    cmd = (cmd or ""):lower()
    if cmd == "start" then W.Start(); Print("Messung läuft (höchstens 30 Min.). /wegmess mark <Text> setzt eine Notiz, /wegmess stop beendet.")
    elseif cmd == "stop" then W.Stop("Befehl"); Print("Messung beendet. Nach /reload liegt alles in SavedVariables/GSWegMess.lua.")
    elseif cmd == "mark" then Print(W.Mark(rest) and ("Notiz: " .. rest) or "Erst /wegmess start.")
    else Print((run and "läuft" or "aus") .. " · " .. #DB().lines .. " Zeilen gespeichert.") end
end
