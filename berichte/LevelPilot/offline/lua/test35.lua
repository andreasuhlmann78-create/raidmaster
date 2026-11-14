-- Test 3.12: Spielversion (GoldSentinelGame) und geschuetzte Werte ("secret values") ohne Lua-Fehler
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
-- geschuetzte Werte nachbilden: jede Rechnung damit wirft einen Fehler
local SECRET = setmetatable({}, {
    __index = function() error("secret value") end, __concat = function() error("secret value") end,
    __eq = function() error("secret value") end, __lt = function() error("secret value") end,
    __le = function() error("secret value") end, __len = function() error("secret value") end })
issecretvalue = function(v) return rawequal(v, SECRET) end
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
Advance(1, 0.1)
check(GoldSentinelGame and GoldSentinelGame.version >= 2 and LP.Game == GoldSentinelGame, "GoldSentinelGame geladen")
check(GoldSentinelGame.IsModern, "issecretvalue vorhanden: moderne Schnittstelle")
check(LP.SafeValue(SECRET) == nil and LP.SafeValue(7) == 7, "LP.SafeValue")
-- Kampf-Protokoll mit geschuetzten Werten
local cle = { 0, "SWING_DAMAGE", false, SECRET, "", SECRET, 0, SECRET }
CombatLogGetCurrentEventInfo = function() return unpack(cle) end
local ok, err = pcall(FireEvent, "COMBAT_LOG_EVENT_UNFILTERED")
local chatErr = false
for _, m in ipairs(CHAT) do if m:find("secret") then chatErr = true end end
check(ok and not chatErr, "Kampf-Protokoll mit geschuetzten Werten: kein Fehler " .. tostring(err or ""))
-- Ziel/Namensplakette mit geschuetzter GUID und Level
UnitExists = function(u) return u == "target" or u == "nameplate1" end
UnitIsPlayer = function() return false end
UnitGUID = function(u) if u == "player" then return "Player-1-00000001" end return SECRET end
UnitLevel = function(u) if u == "player" then return 10 end return SECRET end
local oldName = UnitName
UnitName = function(u) if u == "player" then return "Tester" end return SECRET end
ok, err = pcall(FireEvent, "PLAYER_TARGET_CHANGED")
chatErr = false
for _, m in ipairs(CHAT) do if m:find("secret") then chatErr = true end end
check(ok and not chatErr, "Mob-Level lernen mit geschuetzten Werten: kein Fehler")
ok, err = pcall(function() return LP.Plates:ForUnit("nameplate1", true) end)
check(ok, "Namensplakette mit geschuetzter GUID: kein Fehler " .. tostring(err or ""))
dofile(dir .. "/m_stub.lua")
UnitGUID = function(u) if u == "player" then return "Player-1-00000001" end return SECRET end
UnitLevel = function(u) if u == "player" then return 10 end return SECRET end
UnitName = function(u) if u == "player" then return "Tester" end return SECRET end
UnitExists = function(u) return u == "target" end
C_NamePlate = { GetNamePlates = function() return { { namePlateUnitToken = "nameplate1" } } end }
ok, err = pcall(LP.Measure.Text, LP.Measure)
check(ok, "Messung mit geschuetzten Werten: kein Fehler " .. (ok and "" or tostring(err)))
check(ok and err:find("Spielversion: ", 1, true) and err:find("API: modern", 1, true), "Messung zeigt die Spielversion")
-- Haendler auf dem modernen Client: alte Globals fehlen, C_MerchantFrame vorhanden
local oldG = { GetMerchantNumItems, GetMerchantItemLink, GetMerchantItemInfo, BuyMerchantItem }
GetMerchantNumItems, GetMerchantItemLink, GetMerchantItemInfo, BuyMerchantItem = nil, nil, nil, nil
local bought = {}
C_MerchantFrame = {
    GetNumItems = function() return 2 end,
    GetItemLink = function(i) return "|cffffffff|Hitem:" .. (i == 1 and 159 or 4540) .. "::::::::|h[x]|h|r" end,
    GetItemInfo = function(i) return { name = "Ware" .. i, price = 25, stackCount = 5, numAvailable = -1 } end,
    BuyItem = function(i, n) bought[#bought + 1] = i end,
}
check(LP.API.MerchantAvailable() and LP.API.MerchantCount() == 2, "Händler: Anzahl über C_MerchantFrame")
check(LP.API.MerchantLink(1):find("item:159"), "Händler: Link über C_MerchantFrame")
local nm, pr, st, av = LP.API.MerchantItem(2)
check(nm == "Ware2" and pr == 25 and st == 5 and av == -1, "Händler: Angebot über C_MerchantFrame")
check(LP.API.MerchantBuy(1, 1) and bought[1] == 1, "Händler: Kauf über C_MerchantFrame")
ok, err = pcall(LP.Supply.Plan, LP.Supply)
check(ok and type(err) == "table", "Einkaufsliste ohne alte Globals: kein stiller Ausfall " .. (ok and "" or tostring(err)))
GetMerchantNumItems, GetMerchantItemLink, GetMerchantItemInfo, BuyMerchantItem = oldG[1], oldG[2], oldG[3], oldG[4]
C_MerchantFrame = nil
-- Namensvergleich (Forever: Vor- und Nachname)
GoldSentinelGame.SetTestFlavor("forever")
check(LP.SameName("Rokan Steinwacht-Server", "Rokan") and not LP.SameName("Rokan Steinwacht", "Rokan Eisenfaust"), "Namensvergleich über GoldSentinelGame")
GoldSentinelGame.SetTestFlavor(nil)
-- aeltere Fassung eines anderen Addons (Version 1 mit Spielversion als Text in "version") verdraengt Version 2 nicht
local keep = GoldSentinelGame
GoldSentinelGame = { version = "1.60.1", apiVersion = 1 }
dofile(arg[1] .. "/GoldSentinelGame.lua")
check(GoldSentinelGame.version >= 2 and GoldSentinelGame.SameName ~= nil, "Version 2 setzt sich gegen frühe Fassung durch")
GoldSentinelGame = keep
-- Selbsttest: Spielversion
local res = LP.SelfTest:Run()
local sv
for _, r in ipairs(res) do if r.area == "Spielversion" then sv = r end end
check(sv and sv.state ~= "FEHLER", "Selbsttest prüft die Spielversion: " .. tostring(sv and sv.text))
check(not GoldSentinelGame.IsSecret(nil) and GoldSentinelGame.flavor ~= nil, "Erkennung nach dem Selbsttest wieder echt")
for _, m in ipairs(CHAT) do if m:find("attempt") or m:find("secret value") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
