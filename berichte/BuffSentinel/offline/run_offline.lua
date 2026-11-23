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
--   BS_ROOT=/pfad/BuffSentinel/ lua run_offline.lua [forever|era|tbc|retail] [deDE|enUS]
--   sh run_offline.sh [pfad/zur/BuffSentinel-x.y.z.zip]   -> alle Kombinationen (Forever/Era/TBC/Retail × deDE/enUS)
-- Unbekannte Spielversion -> FEHLER und Abbruch (BS-OFF1), nie stiller Rückfall auf eine andere Version.
--   python3 run_offline.py [zip]                           -> dasselbe mit lupa
-- Ohne Kommandozeile (z. B. aus Python mit lupa): Umgebungsvariablen BS_FLAVOR, BS_LOCALE, BS_ROOT.
--
-- Ausgabe: je Bereich TU1–TU7 eine Zeile "OK n · FEHLER n · SKIP n", danach alle FEHLER-Zeilen, am Ende
-- "RESULT PASS" oder "RESULT FAIL". Massgeblich sind die Bereiche TU1–TU7 (L, M, N, O, P, Q, S): Die übrigen
-- Bereiche brauchen Teile des echten Clients (Fenster, Talente, Ereignisse), die der Nachbau nur grob kennt –
-- ihre Abweichungen stehen als "nur Nachbau" darunter und zählen nicht.

local args = arg or {}
local FLAVORS = { forever = 16001, era = 11508, tbc = 20506, retail = 120105 }
local flavor = args[1] or (os.getenv and os.getenv("BS_FLAVOR")) or "forever"
LOCALE = args[2] or (os.getenv and os.getenv("BS_LOCALE")) or "deDE"
BUILD = FLAVORS[flavor]
-- BS-OFF1 (Nachprüfung 15.11. 22:18): unbekannte Spielversion bricht mit FEHLER ab – nie still auf eine andere zurückfallen
if not BUILD then
    local known = {}
    for k in pairs(FLAVORS) do known[#known + 1] = k end
    table.sort(known)
    print(string.format("FEHLER unbekannte Spielversion '%s' (bekannt: %s)", tostring(flavor), table.concat(known, ", ")))
    print("RESULT FAIL")
    if os.exit then os.exit(2) end
    return
end

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
-- 0.9.57 (Hinweis 18.11. 10:30 "Nachbau darf nicht mehr können als der Forever-Client"): im Forever-Lauf die alten globalen
-- Funktionen entfernen, die der Forever-Client 1.60.1 NICHT hat, und die modernen C_-Wege anbieten.
--   Belegt im Spiel (BuffSentinel T74, Ingametest 18.11. 08:11/09:43): GetNumTalentTabs, GetTalentInfo, UnitBuff, GetSpellInfo = nein;
--   C_SpellBook = ja. Belegt durch T80–T87 ("kein UnitBuff – moderner Client") und RaidMaster 3.0.36 (GetItemInfo fehlt).
--   Verdacht, mit der erweiterten T74-Liste zu messen: UnitDebuff, GetNumTalents, GetSpellCooldown, IsUsableSpell, IsSpellInRange,
--   GetNumSpellTabs, GetSpellTabInfo, GetSpellBookItemName (gleiche Familie wie oben) – im Nachbau ebenfalls entfernt (lieber weniger).
if BUILD == 16001 then
    local oldInfo, oldCd, oldUsable, oldBuff = GetSpellInfo, GetSpellCooldown, IsUsableSpell, UnitBuff
    C_Spell = {
        GetSpellInfo = function(s)
            local name, _, icon, _, _, _, id = oldInfo(s)
            if not name then return nil end
            return { name = name, iconID = icon, spellID = id, castTime = 0, minRange = 0, maxRange = 0, originalIconID = icon }
        end,
        GetSpellCooldown = function(s) local st, d = oldCd(s); return { startTime = st or 0, duration = d or 0, isEnabled = true, modRate = 1 } end,
        IsSpellUsable = function(s) return oldUsable(s) end,
        IsSpellInRange = function() return true end,
        IsSpellPassive = function() return false end,
    }
    C_SpellBook = {
        GetNumSpellBookSkillLines = function() return 1 end,
        GetSpellBookSkillLineInfo = function() return { name = "Allgemein", itemIndexOffset = 0, numSpellBookItems = #KNOWN, shouldHide = false } end,
        GetSpellBookItemName = function(i) return KNOWN[i] end,
        GetSpellBookItemInfo = function(i) local n = KNOWN[i]; if not n then return nil end
            local _, _, _, _, _, _, id = oldInfo(n); return { name = n, itemType = 1, spellID = id, isPassive = false } end,
    }
    C_UnitAuras = {
        GetAuraDataByIndex = function(u, i, filter)
            if filter == "HARMFUL" then return nil end
            local n, icon, count, _, dur, exp, src, _, _, sid = oldBuff(u, i)
            if not n then return nil end
            return { name = n, icon = icon, applications = count, duration = dur, expirationTime = exp, sourceUnit = src, spellId = sid,
                     isHelpful = true, isHarmful = false, isStealable = false, auraInstanceID = i }
        end,
    }
    for _, k in ipairs({ "GetSpellInfo", "UnitBuff", "UnitDebuff", "GetNumTalentTabs", "GetTalentInfo", "GetNumTalents", "GetSpellCooldown",
                         "IsUsableSpell", "IsSpellInRange", "GetNumSpellTabs", "GetSpellTabInfo", "GetSpellBookItemName", "GetItemInfo" }) do
        _G[k] = nil
    end
end
BuffSentinelDB = nil
TALENTS = { { { "A", 11, 15, 1, 1 } }, { { "B", 40, 45, 1, 2 } }, {} }   -- 51 Punkte auf Stufe 60
GoldSentinelGame = nil
function hooksecurefunc(a, b, c)
    if type(a) == "table" then
        -- ohne Tabelle je Aufruf (im Spiel macht der Haken keinen Müll; sonst verfälscht es T110)
        local o = a[b]; a[b] = function(...) local r1, r2, r3, r4 = o(...); c(...); return r1, r2, r3, r4 end
    else
        local o = _G[a]; _G[a] = function(...) local r1, r2, r3, r4 = o(...); b(...); return r1, r2, r3, r4 end
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
-- Retail-Lücken in TU1–TU7 als feste Liste (Test-ID -> Grund); zählen in Retail nicht als FEHLER. Zurzeit keine (0.9.33).
local RETAIL_TU_LUECKEN = {}
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
    if r.st == "FEHLER" and TU[r.area] then
        if flavor == "retail" and RETAIL_TU_LUECKEN[r.id] then
            tuFail = tuFail - 1
            print(string.format("Retail-Lücke (fest, zählt nicht): %s – %s", r.id, RETAIL_TU_LUECKEN[r.id]))
        else
            print(string.format("FAIL %s %s – %s | %s", r.id, r.area, r.name, tostring(r.info):sub(1, 400)))
        end
    end
end
-- BS-OFF1: feste Liste der Abweichungen, die nur vom Nachbau kommen (brauchen den echten Client: Zauberbuch, Fenster,
-- Tooltips, Töne, Optionen-Fenster, Minimap, Texte der gemeinsamen Dateien, Lua-Fehler-Zähler). Für ALLE Spielversionen
-- gleich (gemessen 0.9.33: forever/era/tbc/retail × deDE/enUS). Neue Abweichung oder fehlende erwartete -> FEHLER, damit
-- nichts still dazukommt oder die Liste veraltet. Retail-Lücken in TU1–TU7: RETAIL_TU_LUECKEN (zurzeit keine).
local NACHBAU_ERWARTET = { T13 = true, T23 = true, T28 = true, T45 = true, T51 = true, T95 = true, T266 = true }   -- 0.9.61: T266 Lesbarkeit braucht echte Schriften/Regionen (Nachbau hat keine)   -- 0.9.58: T48 (neue Optionen-Zeilen) grün   -- 0.9.55: T100/T116 laufen mit der Fehler-Handler-Attrappe
local mock, seen, extra = 0, {}, 0
for _, r in ipairs(results) do
    if r.st == "FEHLER" and not TU[r.area] then
        mock = mock + 1
        seen[r.id] = true
        local known = NACHBAU_ERWARTET[r.id]
        if not known then extra = extra + 1 end
        print(string.format("%s: %s %s – %s | %s", known and "nur Nachbau" or "NEU (nicht erwartet)", r.id, r.area, r.name,
            tostring(r.info):sub(1, 160)))
    end
end
local stale = {}
for id in pairs(NACHBAU_ERWARTET) do if not seen[id] then stale[#stale + 1] = id end end
table.sort(stale)
if #stale > 0 then print("ERWARTETE Nachbau-Abweichung nicht mehr da (Liste anpassen): " .. table.concat(stale, ", ")) end
print(string.format("Gesamt %d Prüfungen · TU-FEHLER %d · Nachbau-Abweichungen %d (davon nicht erwartet %d, veraltet %d) · Build %d",
    #results, tuFail, mock, extra, #stale, BUILD))
-- Befund 18.11.: kein Testfehler darf über den Fehler-Handler des Spiels gehen (sonst Fehlerfenster beim Nutzer)
print(string.format("Fehlerfenster (Aufrufe des Spiel-Handlers): %d", ERRWIN_CALLS or 0))
local pass = tuFail == 0 and extra == 0 and #stale == 0 and (ERRWIN_CALLS or 0) == 0
print(pass and "RESULT PASS" or "RESULT FAIL")
if os.exit and not pass and args[0] then os.exit(1) end
