-- Testroutine im Mock komplett laufen lassen
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
-- Spielversion: FOREVER=1 (WoW Forever 1.60.1), sonst FLAVOR=era (Classic Era 1.15) oder FLAVOR=tbc (TBC Classic 2.5)
if os.getenv("FOREVER") == "1" then
    function GetBuildInfo() return "1.60.1", "60001", "Nov 1 2026", 16001 end
    WOW_PROJECT_ID, WOW_PROJECT_CAMELOT = 99, 99
    IS_SECRET = {}
    function issecretvalue(v) return v ~= nil and IS_SECRET[v] == true end
elseif os.getenv("FLAVOR") == "tbc" then
    function GetBuildInfo() return "2.5.4", "44833", "Jun 1 2024", 20504 end
    WOW_PROJECT_ID, WOW_PROJECT_BURNING_CRUSADE_CLASSIC, WOW_PROJECT_CLASSIC = 5, 5, 2
else
    function GetBuildInfo() return "1.15.7", "61000", "Jun 1 2025", 11507 end
    WOW_PROJECT_ID, WOW_PROJECT_CLASSIC = 2, 2
end
local function tocField(addon, field)
    local root = addon == "LevelPilot" and arg[1] or os.getenv("PACKDIR")
    local f = io.open(root .. "/" .. addon .. ".toc") if not f then return nil end
    local t = f:read("*a") f:close()
    return t:match("## " .. field .. ":%s*([^\r\n]+)")
end
C_AddOns = C_AddOns or {}
C_AddOns.GetAddOnMetadata = tocField
C_AddOns.IsAddOnLoaded = function(a) return a == "LevelPilot" or a == "LevelPilot_Data" end
GetZoneText = GetZoneText or function() return "Durotar" end
GetSubZoneText = GetSubZoneText or function() return "" end
GetRealZoneText = GetRealZoneText or function() return "Durotar" end
GetRealmName = GetRealmName or function() return "Testrealm" end
dofile(dir .. "/mock2.lua")
UnitIsPlayer = UnitIsPlayer or function(u) return u == "player" end
UnitIsDead = UnitIsDead or function() return false end
UnitGUID = UnitGUID or function() return nil end
UnitPlayerControlled = UnitPlayerControlled or function() return false end
UnitClassification = UnitClassification or function() return "normal" end
UnitCanAttack = UnitCanAttack or function() return false end
local LP = NS
LP._dev = true
local nt = C_Timer.NewTicker
C_Timer.NewTicker = function(d, fn) local tk = nt(d, fn) tk.Cancel = function(self) for i, x in ipairs(TICKERS) do if x == self then table.remove(TICKERS, i) break end end end return tk end
local area = os.getenv("AREA")
if area == "" then area = nil end
if PRE_RUN then PRE_RUN(LP) end
LP.TestRoutine:Run(area, os.getenv("LONG") == "1")
local n = 0
while LP.TestRoutine.running and n < 200000 do Advance(0.05, 0.05) n = n + 1 if LP.TestRoutine.lastText then break end end
Advance(6)
local t = LP.TestRoutine.lastText or "KEIN BERICHT"
print(t)
local fe = t:match("FEHLER (%d+)")
for _, m in ipairs(CHAT) do if m:find("Fehler") or m:find("rror") then print("CHAT: " .. m) end end
print((fe == "0" and t:find("echte Daten unverändert: OK", 1, true)) and "== ALLE TESTS OK" or ("== " .. tostring(fe) .. " FEHLER"))
