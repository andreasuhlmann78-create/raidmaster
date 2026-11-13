-- BuffSentinel – Testroutine offline im nachgebauten Spiel (TU9)
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Startet die ganze Testroutine (/bsen testroutine) ausserhalb von WoW: alle Klassen und Skillungen aus Data/*.lua,
-- alle Lagen (TU1), Abläufe (TU2), Standardwerte (TU3), Grundregeln mit Zufallsdaten (TU4), Regressionen (TU6) und
-- Formen des Spiels (TU7). Wird nicht vom Spiel geladen (steht nicht in der .toc).
--
-- Liegt im raidmaster-Repo (berichte/BuffSentinel/offline/), nicht in der Addon-ZIP. BS_ROOT = entpackter Ordner
-- BuffSentinel (Standard: download/BuffSentinel-*.zip entpackt nach /tmp/BuffSentinel/ – siehe run_offline.sh).
-- Start mit Lua 5.1 bis 5.4:
--   BS_ROOT=/pfad/BuffSentinel/ lua run_offline.lua [forever|era|tbc] [deDE|enUS]
--   sh run_offline.sh [pfad/zur/BuffSentinel-x.y.z.zip]   -> alle Kombinationen (Forever/Era/TBC × deDE/enUS)
--   python3 run_offline.py [zip]                           -> dasselbe mit lupa
-- Ohne Kommandozeile (z. B. aus Python mit lupa): Umgebungsvariablen BS_FLAVOR, BS_LOCALE, BS_ROOT.
--
-- Ausgabe: je Bereich TU1–TU7 eine Zeile "OK n · FEHLER n · SKIP n", danach alle FEHLER-Zeilen, am Ende
-- "RESULT PASS" oder "RESULT FAIL". Massgeblich sind die Bereiche TU1–TU7 (L, M, N, O, P, Q, S): Die übrigen
-- Bereiche brauchen Teile des echten Clients (Fenster, Talente, Ereignisse), die der Nachbau nur grob kennt –
-- ihre Abweichungen stehen als "nur Nachbau" darunter und zählen nicht.

local args = arg or {}
local FLAVORS = { forever = 16001, era = 11508, tbc = 20506 }
local flavor = args[1] or (os.getenv and os.getenv("BS_FLAVOR")) or "forever"
LOCALE = args[2] or (os.getenv and os.getenv("BS_LOCALE")) or "deDE"
BUILD = FLAVORS[flavor] or 16001

local function dirOf(p) return (p and p:match("^(.*)[/\\]")) or "." end
local here = dirOf(args[0] or (debug and debug.getinfo and debug.getinfo(1, "S").source:gsub("^@", "")))
local HERE = (os.getenv and os.getenv("BS_TESTS")) or here
local ROOT = (os.getenv and os.getenv("BS_ROOT")) or "/tmp/BuffSentinel/"
if ROOT:sub(-1) ~= "/" then ROOT = ROOT .. "/" end

local unpack = table.unpack or unpack
dofile(HERE .. "/mock_wow.lua")

-- Ergänzungen für die ganze Routine
M_SetText = function(self, t) self._text = t end
M_GetText = function(self) return self._text or "" end
M_GetStringWidth = function(self) return #(self._text or "") * 7 end
M_SetFont = function(self, f, size) self._size = size end
function M_SetSize(self, w, h) self._w, self._h = w, h end
function M_GetWidth(self) return self._w or 140 end
function M_GetHeight(self) return self._h or 40 end
function GetSpellInfo(s) if type(s) == "number" then return "Z" .. s, nil, "I" .. s, 0, 0, 0, s end end
function GetNumSpellTabs() return 0 end
function GetWeaponEnchantInfo() return true, 0, 0, 0, true end
function UnitDebuff() return nil end
GetChannelName = function() return 0 end
function GetBuildInfo() return "x", "y", "z", BUILD end
function UnitFactionGroup() return "Horde" end
BuffSentinelDB = nil
TALENTS = { { { "A", 11, 15, 1, 1 } }, { { "B", 40, 45, 1, 2 } }, {} }   -- 51 Punkte auf Stufe 60
GoldSentinelGame = nil
function hooksecurefunc(a, b, c)
    if type(a) == "table" then
        local o = a[b]; a[b] = function(...) local r = { o(...) }; c(...); return unpack(r) end
    else
        local o = _G[a]; _G[a] = function(...) local r = { o(...) }; b(...); return unpack(r) end
    end
end
function debugprofilestop() return os.clock() * 1000 end
function UpdateAddOnMemoryUsage() end
function GetAddOnMemoryUsage() return 500 end
function IsShiftKeyDown() return false end
function IsControlKeyDown() return false end
function GetCursorPosition() return 0, 0 end
ChatFontNormal = {}
function GetNumGroupMembers() return GROUP end
function UnitIsUnit(a, b) return a == b end
function GetRaidRosterInfo() return nil end

-- Dateien in der Reihenfolge der .toc laden
local f = assert(io.open(ROOT .. "BuffSentinel.toc", "r"))
local toc = f:read("*a"); f:close()
local FILES = {}
for line in toc:gmatch("[^\r\n]+") do
    if not line:match("^#") and line:match("%S") then FILES[#FILES + 1] = (line:gsub("\\", "/"):gsub("%s+$", "")) end
end
local tocVersion = toc:match("## Version:%s*([^\r\n]+)")
function GetAddOnMetadata(_, field) if field == "Version" then return tocVersion end end
C_AddOns = { GetAddOnMetadata = GetAddOnMetadata }
local BS = {}
for _, file in ipairs(FILES) do
    local fn, err = loadfile(ROOT .. file)
    if not fn then print("LADEFEHLER", file, err); os.exit(2) end
    local ok, e = pcall(fn, "BuffSentinel", BS)
    if not ok then print("LAUFZEITFEHLER beim Laden", file, e); os.exit(2) end
end

-- Ergebnisse mitschreiben (alle, auch OK)
local results = {}
do
    local begin = GoldSentinelTest.Begin
    GoldSentinelTest.Begin = function(...)
        local r = begin(...)
        local add = r.Add
        r.Add = function(self, st, id, area, name, extra)
            results[#results + 1] = { st = st, id = id, area = area, name = name,
                info = extra and (extra.ergebnis or extra.lua or extra.grund) or "" }
            return add(self, st, id, area, name, extra)
        end
        return r
    end
end

local chat = {}
DEFAULT_CHAT_FRAME = { AddMessage = function(_, m) chat[#chat + 1] = m end }
BS.frame._scripts.OnEvent(BS.frame, "PLAYER_LOGIN")
local ok, err = pcall(function() BS:RunTestRoutine("") end)
if not ok then print("LAUFZEITFEHLER", err); os.exit(2) end

local TU = { L = "TU1", M = "TU2", N = "TU3", O = "TU4", P = "TU5", Q = "TU6", S = "TU7" }
local count = {}
for _, r in ipairs(results) do
    local c = count[r.area] or { OK = 0, FEHLER = 0, SKIP = 0, CLIENT = 0 }
    count[r.area] = c
    c[r.st] = (c[r.st] or 0) + 1
end
print(string.format("BuffSentinel %s offline · %s (%d) · %s", tostring(BS.version), flavor, BUILD, LOCALE))
local tuFail = 0
for _, a in ipairs({ "L", "M", "N", "O", "P", "Q", "S" }) do
    local c = count[a] or { OK = 0, FEHLER = 0, SKIP = 0 }
    print(string.format("%s (%s): OK %d · FEHLER %d · SKIP %d", TU[a], a, c.OK, c.FEHLER, c.SKIP))
    tuFail = tuFail + c.FEHLER
end
for _, r in ipairs(results) do
    if r.st == "FEHLER" and TU[r.area] then print(string.format("FAIL %s %s – %s | %s", r.id, r.area, r.name, tostring(r.info):sub(1, 400))) end
end
local mock = 0
for _, r in ipairs(results) do
    if r.st == "FEHLER" and not TU[r.area] then
        mock = mock + 1
        print(string.format("nur Nachbau: %s %s – %s", r.id, r.area, r.name))
    end
end
print(string.format("Gesamt %d Prüfungen · TU-FEHLER %d · Nachbau-Abweichungen ausserhalb TU %d", #results, tuFail, mock))
print(tuFail == 0 and "RESULT PASS" or "RESULT FAIL")
if os.exit and tuFail > 0 and args[0] then os.exit(1) end
