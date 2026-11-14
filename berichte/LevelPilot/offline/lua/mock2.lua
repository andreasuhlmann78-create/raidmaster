if os.getenv("CJKFONTS") == "1" then MOCK_FONTS = MOCK_FONTS or { ["Fonts\\2002.TTF"] = true, ["Fonts\\ARKai_T.ttf"] = true, ["Fonts\\bLEI00D.ttf"] = true } end
-- WoW-API-Mock fuer LevelPilot 2.x
-- Aufruf: luatex --luaonly <test.lua> <AddonOrdner> [Questie=1/0] [Rasse] [Klasse] [Fraktion]
local ROOT = arg[1]
local WITH_QUESTIE = (arg[2] or "1") == "1"
local RACE, CLASS, FACTION = arg[3] or "Human", arg[4] or "WARRIOR", arg[5] or "Alliance"
local RACE_IDS = { Human = 1, Orc = 2, Dwarf = 3, NightElf = 4, Scourge = 5, Tauren = 6, Gnome = 7, Troll = 8, Skyborne = (os.getenv("SKYFAC") == "Horde" and 96 or 95) }

math.atan2 = math.atan2 or function(y, x) return math.atan(y, x) end
unpack = unpack or table.unpack
loadstring = loadstring or load
function wipe(t) for k in pairs(t) do t[k] = nil end return t end
tinsert, tremove = table.insert, table.remove
function hooksecurefunc() end
function Mixin(o, ...) for _, m in ipairs({ ... }) do for k, v in pairs(m) do o[k] = v end end return o end
BackdropTemplateMixin = {}
UISpecialFrames = {}
CHAT = {}
DEFAULT_CHAT_FRAME = { AddMessage = function(_, m) table.insert(CHAT, (tostring(m):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""))) end }
SlashCmdList = {}
SOUNDKIT = {}
function PlaySound() end

-- Zeit
NOW = 1000
function GetTime() return NOW end
function time() return math.floor(NOW) end
function date(fmt, t) return os.date(fmt, t) end
TIMERS, TICKERS = {}, {}
C_Timer = {
    After = function(d, fn) table.insert(TIMERS, { t = NOW + d, fn = fn }) end,
    NewTicker = function(d, fn) local tk = { d = d, fn = fn, next = NOW + d } table.insert(TICKERS, tk) return tk end,
}
function Advance(secs, step)
    step = step or 0.5
    local target = NOW + secs
    while NOW < target do
        NOW = NOW + step
        for i = #TIMERS, 1, -1 do
            local t = TIMERS[i]
            if t.t <= NOW then table.remove(TIMERS, i) t.fn() end
        end
        for _, tk in ipairs(TICKERS) do
            if tk.next <= NOW then tk.next = NOW + tk.d tk.fn() end
        end
        for f in pairs(UPDATERS) do local sc = rawget(f, "_scripts") if sc and sc.OnUpdate then sc.OnUpdate(f, step) end end
    end
end

-- Spieler
P = { level = tonumber(os.getenv("LVL") or "1"), xp = 0, xpMax = 400, map = tonumber(os.getenv("MAP") or "1429"), x = tonumber(os.getenv("PX") or "48.0"), y = tonumber(os.getenv("PY") or "43.0"), facing = 0, dead = false, taxi = false, swim = false }
function UnitLevel() return P.level end
function UnitXP() return P.xp end
function UnitXPMax() return P.xpMax end
function UnitClass() return "Klasse", CLASS end
function UnitRace() return "Volk", RACE, RACE_IDS[RACE] or 1 end
function UnitFactionGroup() return FACTION end
function UnitName(u) if u == "player" then return "Tester" end return NPCNAME end
function UnitExists(u) return (u == "npc" or u == "questnpc") and NPCNAME ~= nil end
function UnitSex() return 2 end
function UnitOnTaxi() return P.taxi end
function UnitIsDeadOrGhost() return P.dead end
function UnitInVehicle() return false end
function UnitCharacterPoints() return P.talents or 0 end
function IsInInstance() if P.instance then return true, "party" end return false, "none" end
function GetInstanceInfo() if P.instance then return P.instanceName or "Instanz", "party", 1, "Normal", 5, 0, false, P.instanceID or 0 end return "Welt", "none", 0, "", 0, 0, false, 0 end
function IsSwimming() return P.swim end
function IsIndoors() return false end
function IsShiftKeyDown() return false end
function IsControlKeyDown() return CTRL or false end
function IsInRaid() return false end
function IsInGroup() return P.group or false end
function IsInGuild() return true end
function InCombatLockdown() return false end
function GetPlayerFacing() return P.facing end
function GetCVar() return "0" end
function GetCursorPosition() return 0, 0 end
function GetLocale() return os.getenv("LOCALE") or "deDE" end
function ReloadUI() end

-- Questlog
LOG = {}
FLAGGED = {}
function GetNumQuestLogEntries() return #LOG end
function GetQuestLogTitle(i)
    local q = LOG[i]
    if not q then return nil end
    return q.title, q.level or 1, nil, false, false, q.complete and 1 or nil, 0, q.id
end
function GetNumQuestLeaderBoards(i) return LOG[i] and #(LOG[i].objs or {}) or 0 end
function GetQuestLogLeaderBoard(o, i) local ob = LOG[i].objs[o] return ob[1], "monster", ob[2] end
function GetQuestGreenRange() return 5 end
function GetQuestDifficultyColor() return { r = 1, g = 1, b = 0 } end
C_QuestLog = { IsQuestFlaggedCompleted = function(id) return FLAGGED[id] or false end }
CUR_QUEST = 0
function GetQuestID() return CUR_QUEST end
function GetTitleText() return "Titel" .. CUR_QUEST end
ACCEPTED = {}
function AcceptQuest() table.insert(ACCEPTED, CUR_QUEST) end
function CompleteQuest() end
function GetNumQuestChoices() return 0 end
function GetQuestReward() end
function IsQuestCompletable() return true end
function GetNumActiveQuests() return 0 end
function GetNumAvailableQuests() return 0 end
C_GossipInfo = { GetActiveQuests = function() return {} end, GetAvailableQuests = function() return {} end, GetOptions = function() return {} end }

-- Inventar
DUR = {}
function GetInventoryItemDurability(slot) local d = DUR[slot] if d then return d[1], d[2] end return nil end
function GetInventoryItemLink() return nil end
function GetInventoryItemCount() return P.ammo or 0 end
BAGS = { [0] = { 16, 10 }, [1] = { 6, 2 }, [2] = { 6, 6 } }
C_Container = {
    GetContainerNumSlots = function(b) return BAGS[b] and BAGS[b][1] or 0 end,
    GetContainerNumFreeSlots = function(b) return BAGS[b] and BAGS[b][2] or 0, 0 end,
    GetContainerItemLink = function() return nil end,
}
function GetItemInfo() return nil end
function IsEquippableItem() return false end
function EquipItemByName() end

-- Chat / Austausch
SENT = {}
C_ChatInfo = {
    RegisterAddonMessagePrefix = function() return true end,
    SendAddonMessage = function(prefix, msg, chan, target) table.insert(SENT, { prefix, msg, chan, target }) return true end,
}
function JoinTemporaryChannel() end
function GetChannelName() return 5 end
function ChatFrame_RemoveChannel() end

-- Karten: Kontinent 0, jede Zone 2000x2000 Yards, nebeneinander im Raster
local ZONEPOS = { [1429] = { 0, 0 }, [1436] = { 0, 1 }, [1453] = { -1, 0 }, [1431] = { 1, 0 }, [1433] = { 0, -1 } }
local function origin(map)
    local z = ZONEPOS[map] or { 10 + (map % 37) * 3, 10 + math.floor(map / 37) % 37 * 3 }
    return -z[1] * 2000, -z[2] * 2000
end
CreateVector2D = function(x, y) return { x = x, y = y, GetXY = function(s) return s.x, s.y end } end
C_Map = {
    GetWorldPosFromMapPos = function(map, v)
        local on, ow = origin(map)
        return 0, CreateVector2D(on - v.y * 2000, ow - v.x * 2000)
    end,
    GetBestMapForUnit = function() return P.map end,
    GetPlayerMapPosition = function(map) if map == P.map then return CreateVector2D(P.x / 100, P.y / 100) end end,
    GetMapInfo = function(map) return { mapID = map, mapType = 3, parentMapID = 0, name = "Zone" .. map } end,
    GetMapRectOnMap = function() return nil end,
}
Enum = { UIMapType = { Continent = 2 }, FlightPathState = { Current = 0, Reachable = 1, Unreachable = 2 } }

-- Frames
UPDATERS = {}
local frameMT = {}
frameMT.__index = function(self, k)
    if k == "GetHeight" then return function(s) return rawget(s, "_h") or 300 end end
    if k == "GetWidth" then return function(s) return rawget(s, "_w") or 300 end end
    if k == "SetHeight" then return function(s, h) rawset(s, "_h", h) end end
    if k == "SetWidth" then return function(s, w) rawset(s, "_w", w) end end
    if k == "SetSize" then return function(s, w, h) rawset(s, "_w", w) rawset(s, "_h", h) end end
    if k == "SetPoint" then return function(s, ...) local p = rawget(s, "_points") or {} p[#p + 1] = { ... } rawset(s, "_points", p) end end
    if k == "ClearAllPoints" then return function(s) rawset(s, "_points", {}) end end
    if k == "SetFont" then return function(s, path, size) rawset(s, "_size", size) rawset(s, "_font", path) return true end end
    if k == "GetFont" then return function(s) return rawget(s, "_font") or "Fonts\\FRIZQT__.TTF", rawget(s, "_size") or 12, "" end end
    -- Breite: fehlende Zeichen (Hangul/Han ohne passende Schrift, U+E000) sind 5 breit wie ein Kaestchen
    if k == "GetStringWidth" then return function(s)
        local t = tostring(rawget(s, "_text") or ""):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
        local w, size = 0, (rawget(s, "_size") or 12) / 12
        for ch in t:gmatch("[%z\1-\127\194-\244][\128-\191]*") do
            if #ch == 1 then w = w + 6
            elseif #ch == 2 then w = w + 7
            elseif ch == "\238\128\128" then w = w + 5
            elseif (MOCK_FONTS or {})[rawget(s, "_font") or ""] then w = w + 12
            else w = w + 5 end
        end
        return w * size
    end end
    if k == "GetStringHeight" then return function(s) local _, n = tostring(rawget(s, "_text") or ""):gsub("\n", "") return 14 * (n + 1) end end
    if k == "GetName" then return function(s) return rawget(s, "_name") end end
    if k == "SetText" then return function(s, t) rawset(s, "_text", t) if ALLTEXT then ALLTEXT[#ALLTEXT + 1] = t end end end
    if k == "GetText" then return function(s) return rawget(s, "_text") end end
    if k == "IsShown" then return function(s) return rawget(s, "_shown") ~= false end end
    if k == "Show" then return function(s) local was = rawget(s, "_shown") rawset(s, "_shown", true) local sc = rawget(s, "_scripts") if was == false and sc and sc.OnShow then sc.OnShow(s) end end end
    if k == "Hide" then return function(s) rawset(s, "_shown", false) end end
    if k == "SetShown" then return function(s, v) local was = rawget(s, "_shown") rawset(s, "_shown", v and true or false) local sc = rawget(s, "_scripts") if v and was == false and sc and sc.OnShow then sc.OnShow(s) end end end
    if k == "GetPoint" then return function() return "CENTER", nil, "CENTER", 0, 0 end end
    if k == "GetCenter" then return function() return 0, 0 end end
    if k == "GetEffectiveScale" or k == "GetCanvasScale" then return function() return 1 end end
    if k == "GetZoom" or k == "GetFrameLevel" then return function() return 1 end end
    if k == "GetParent" then return function(s) return rawget(s, "_parent") end end
    if k == "GetMapID" then return function() return P.map end end
    if k == "SetScript" then return function(s, ev, fn)
        local sc = rawget(s, "_scripts") or {} sc[ev] = fn rawset(s, "_scripts", sc)
        if ev == "OnUpdate" then UPDATERS[s] = fn and true or nil end
    end end
    if k == "GetScript" then return function(s, ev) local sc = rawget(s, "_scripts") return sc and sc[ev] end end
    if k == "Click" then return function(s, ...) local sc = rawget(s, "_scripts") if sc and sc.OnClick then sc.OnClick(s, "LeftButton") end end end
    if k == "HookScript" then return function(s, ev, fn) local sc = rawget(s, "_scripts") or {} sc[ev] = fn rawset(s, "_scripts", sc) if ev == "OnUpdate" then UPDATERS[s] = true end end end
    if k == "RegisterEvent" then return function(s, ev) EVENTFRAMES = EVENTFRAMES or {} EVENTFRAMES[s] = true
        local r = rawget(s, "_events") or {} if ev then r[ev] = true end rawset(s, "_events", r) end end
    if k == "UnregisterEvent" then return function(s, ev) local r = rawget(s, "_events") if r and ev then r[ev] = nil end end end
    if k == "IsEventRegistered" then return function(s, ev) local r = rawget(s, "_events") return r and r[ev] or false end end
    if k == "SetStartPoint" then return function(s, _, _, x, y) rawset(s, "_sx", x) rawset(s, "_sy", y) LINES_DRAWN = (LINES_DRAWN or 0) + 1 end end
    if k == "GetChildren" then return function(s) return unpack(rawget(s, "_children") or {}) end end
    if k == "GetRegions" then return function(s) return unpack(rawget(s, "_regions") or {}) end end
    if k:match("^Create") then return function(s) local r = setmetatable({ _parent = s }, frameMT) local l = rawget(s, "_regions") or {} l[#l + 1] = r rawset(s, "_regions", l) return r end end
    return function() end
end
function CreateFrame(_, name, parent)
    local f = setmetatable({ _parent = parent, _name = name }, frameMT)
    if type(parent) == "table" then local l = rawget(parent, "_children") or {} l[#l + 1] = f rawset(parent, "_children", l) end
    if name then _G[name] = f end
    return f
end
Minimap = CreateFrame("Frame")
UIParent = CreateFrame("Frame")
GameTooltip = CreateFrame("Frame")
WorldMapFrame = CreateFrame("Frame")
WorldMapFrame.ScrollContainer = CreateFrame("Frame")
WorldMapFrame.ScrollContainer.Child = CreateFrame("Frame")
WorldMapFrame:Hide()

function FireEvent(ev, ...)
    for f in pairs(EVENTFRAMES or {}) do
        local sc = rawget(f, "_scripts")
        if sc and sc.OnEvent then sc.OnEvent(f, ev, ...) end
    end
end

------------------------------------------------------------------------
-- Test-QuestieDB (wenige Quests, Format wie die oeffentliche Schnittstelle)
------------------------------------------------------------------------
if WITH_QUESTIE then
    local quests = {
        [783]  = { name = "A Threat Within", questLevel = 1, requiredLevel = 1, requiredRaces = 77, startedBy = { { 823 } }, finishedBy = { { 197 } }, objectives = {} },
        [7]    = { name = "Kobold Camp Cleanup", questLevel = 2, requiredLevel = 1, requiredRaces = 77, startedBy = { { 197 } }, finishedBy = { { 197 } }, objectives = { { { 6 } } }, preQuestSingle = { 783 } },
        [5261] = { name = "Eagan Peltskinner", questLevel = 2, requiredLevel = 1, requiredRaces = 77, startedBy = { { 823 } }, finishedBy = { { 196 } }, objectives = {} },
        [4641] = { name = "Your Place In The World", questLevel = 1, requiredLevel = 1, requiredRaces = 178, startedBy = { { 10176 } }, finishedBy = { { 3143 } }, objectives = {} },
        [9000] = { name = "Hohes Level", questLevel = 30, requiredLevel = 25, requiredRaces = 77, startedBy = { { 823 } }, finishedBy = { { 197 } }, objectives = {} },
        [9001] = { name = "Westfall-Quest", questLevel = 3, requiredLevel = 1, requiredRaces = 0, startedBy = { { 900 } }, finishedBy = { { 900 } }, objectives = {} },
        [9002] = { name = "Nur Magier", questLevel = 1, requiredLevel = 1, requiredRaces = 77, requiredClasses = 128, startedBy = { { 823 } }, finishedBy = { { 197 } }, objectives = {} },
    }
    local npcs = {
        [823] = { name = "Deputy Willem", spawns = { [12] = { { 48.2, 42.9 } } } },
        [197] = { name = "Marshal McBride", spawns = { [12] = { { 48.9, 41.6 } } } },
        [196] = { name = "Eagan Peltskinner", spawns = { [12] = { { 48.0, 40.0 } } } },
        [6]   = { name = "Kobold Vermin", spawns = { [12] = { { 47.0, 35.0 }, { 48.0, 33.0 } } } },
        [900] = { name = "Bauer", spawns = { [40] = { { 56.0, 31.0 } } } },
        [1000] = { name = "Schmied", spawns = { [12] = { { 41.7, 65.5 } } }, npcFlags = 4096 + 128, friendlyToFaction = "A" },
    }
    local function entity(tbl)
        local e = {}
        e.Get = function(id, key) local r = tbl[id] if not r then return nil end local v = r[key] if v == nil and (key:find("Level") or key:find("Races") or key:find("Classes") or key:find("Flags")) then return 0 end return v end
        e.GetAllIds = function() local ids = {} for id in pairs(tbl) do ids[#ids + 1] = id end table.sort(ids) return ids end
        setmetatable(e, { __index = function(_, k) return function(id) return e.Get(id, k) end end })
        return e
    end
    LibQuestieDB = {
        contractVersion = 4,
        RequireContract = function() return true end,
        Quest = entity(quests), Npc = entity(npcs), Object = entity({}), Item = entity({}),
        Support = { Get = function() return { private = { areaIdToUiMapId = "return {[12]=1429,[40]=1436}" } } end },
        Enum = {
            classKeys = { WARRIOR = 1, PALADIN = 2, HUNTER = 4, ROGUE = 8, PRIEST = 16, SHAMAN = 64, MAGE = 128, WARLOCK = 256, DRUID = 1024 },
            raceMaskById = { [1] = 1, [2] = 2, [3] = 4, [4] = 8, [5] = 16, [6] = 32, [7] = 64, [8] = 128 },
            factionRaceMasks = { Alliance = 77, Horde = 178 },
            npcFlags = { VENDOR = 128, REPAIR = 4096, FLIGHT_MASTER = 8192, INNKEEPER = 65536 },
        },
    }
end

------------------------------------------------------------------------
-- Forever-Modus: moderne Schnittstelle, alte globale Funktionen fehlen
------------------------------------------------------------------------
FOREVER = os.getenv("FOREVER") == "1"
if FOREVER then
    local logLB = GetQuestLogLeaderBoard
    C_QuestLog.GetNumQuestLogEntries = function() return #LOG end
    C_QuestLog.GetInfo = function(i)
        local q = LOG[i]
        if not q then return nil end
        return { title = q.title, level = q.level or 1, isHeader = false, questID = q.id }
    end
    C_QuestLog.IsComplete = function(id) for _, q in ipairs(LOG) do if q.id == id then return q.complete and true or false end end return false end
    C_QuestLog.IsFailed = function() return false end
    C_QuestLog.GetLogIndexForQuestID = function(id) for i, q in ipairs(LOG) do if q.id == id then return i end end return nil end
    C_QuestLog.GetQuestObjectives = function(id)
        for _, q in ipairs(LOG) do
            if q.id == id then
                local out = {}
                for _, ob in ipairs(q.objs or {}) do
                    local have, need = ob[1]:match("(%d+)%s*/%s*(%d+)")
                    out[#out + 1] = { text = ob[1], finished = ob[2], numFulfilled = tonumber(have) or 0, numRequired = tonumber(need) or 1 }
                end
                return out
            end
        end
        return {}
    end
    C_QuestLog.GetTrivialRange = function() return 5 end
    C_Item = { GetItemInfo = function() return nil end, IsEquippableItem = function() return false end, EquipItemByName = function() end }
    GetNumQuestLogEntries, GetQuestLogTitle, GetNumQuestLeaderBoards, GetQuestLogLeaderBoard = nil, nil, nil, nil
    UnitCharacterPoints, GetItemInfo, IsEquippableItem, EquipItemByName, GetQuestGreenRange = nil, nil, nil, nil, nil
end
function FireAccepted(idx, id)
    if FOREVER then FireEvent("QUEST_ACCEPTED", id) else FireEvent("QUEST_ACCEPTED", idx, id) end
end

debugprofilestop = debugprofilestop or function() return os.clock() * 1000 end

-- optional: echte Weltgeometrie (Simulation)
if os.getenv("WORLDHOOK") and os.getenv("WORLDHOOK") ~= "" then dofile(os.getenv("WORLDHOOK")) end

-- optional: Datenpaket "LevelPilot Data" laden
PACKDIR = os.getenv("PACKDIR")
if PACKDIR and PACKDIR ~= "" then
    WITH_QUESTIE_SAVED = LibQuestieDB
    LibQuestieDB = nil
    for line in io.open(PACKDIR .. "/LevelPilot_Data.toc"):read("*a"):gmatch("[^\r\n]+") do
        if line:match("%.lua$") then
            local chunk, err = loadfile(PACKDIR .. "/" .. line:gsub("\\", "/"))
            if not chunk then error("PACK SYNTAX " .. err) end
            chunk("LevelPilot_Data", {})
        end
    end
end

-- optional: echte SavedVariables aus dem Spiel (WTF\Account\<Konto>\SavedVariables\LevelPilot.lua
-- und WTF\Account\<Konto>\<Realm>\<Charakter>\SavedVariables\LevelPilot.lua) - wie im Spiel vor dem Addon geladen
for _, var in ipairs({ "SVACC", "SVCHAR" }) do
    local f = os.getenv(var)
    if f and f ~= "" then
        local chunk, err = loadfile(f)
        if not chunk then error("SAVEDVARIABLES " .. tostring(err)) end
        chunk()
        print("       SavedVariables geladen: " .. f)
    end
end

-- Addon laden
local ns = {}
for line in io.open(ROOT .. "/LevelPilot.toc"):read("*a"):gmatch("[^\r\n]+") do
    if line:match("%.lua$") then
        local chunk, err = loadfile(ROOT .. "/" .. line:gsub("\\", "/"))
        if not chunk then error("SYNTAX " .. err) end
        chunk("LevelPilot", ns)
    end
end
NS = ns
ns.debug = true
if ns.Jobs and os.getenv("ASYNC") ~= "1" then ns.Jobs.sync = true end
if ns.Perf and os.getenv("BRAKE") ~= "1" then ns.Perf.BRAKE_MS, ns.Perf.BRAKE_SUM_MS = 1e9, 1e9 end
FireEvent("ADDON_LOADED", "LevelPilot")
FireEvent("PLAYER_LOGIN")
FireEvent("PLAYER_ENTERING_WORLD")
Advance(3)
