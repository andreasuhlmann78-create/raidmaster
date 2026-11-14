-- Test: alle grauen Gegenstaende verkaufen, auch Waffen und noch nicht geladene (3.4.4)
-- Aufruf: PACKDIR=... lua51 test21.lua <Addon> 0 Orc WARRIOR Horde
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
C_Container = C_Container or {}
C_Item = C_Item or {}
BAGITEMS = {}      -- [bag] = { [slot] = { id, count, quality, price, cached, link, noValue } }
CACHED = {}
C_Item.GetItemInfo = function(x)
    local id = type(x) == "number" and x or tonumber(tostring(x):match("item:(%d+)"))
    for _, b in pairs(BAGITEMS) do for _, it in pairs(b) do
        if it[1] == id then
            if not it[5] then return nil end           -- noch nicht geladen
            return "Item" .. id, nil, it[3], nil, nil, nil, nil, nil, nil, nil, it[4] or 0
        end
    end end
    return nil
end
C_Item.GetItemQualityByID = function() return nil end   -- auch das liefert das Spiel ungeladen nicht
C_Container.GetContainerItemInfo = function(b, s)
    local it = BAGITEMS[b] and BAGITEMS[b][s]
    if not it then return nil end
    return { itemID = it[1], stackCount = it[2], quality = it[5] and it[3] or -1, hyperlink = it[6] or ("item:" .. it[1]), hasNoValue = it[7] }
end
C_Container.GetContainerNumSlots = function(b) return b <= 1 and 16 or 0 end
USED = {}
MONEY = 1000
function GetMoney() return MONEY end
C_Container.UseContainerItem = function(b, s) local it = BAGITEMS[b][s] USED[#USED + 1] = it[1] MONEY = MONEY + (it[4] or 0) * (it[2] or 1) BAGITEMS[b][s] = nil end
MerchantFrame = setmetatable({}, { __index = function() return function() return true end end })
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local function sold(id) for _, u in ipairs(USED) do if u == id then return true end end return false end
LP.API.BagSlots = function(b) return b <= 1 and 16 or 0 end

-- Startgegenstand fuer eine Quest suchen (darf nie verkauft werden)
local startItem
for it = 1, 30000 do local e = LP.QuestDB:ItemQuests(it) if e and e.starts then startItem = it break end end

BAGITEMS[0] = {
    [1] = { 2777, 1, 0, 37, true },                                       -- graue Waffe, geladen
    [2] = { 2778, 1, 0, 52, false, "|cff9d9d9d|Hitem:2778::|h[Rostiges Schwert]|h|r" },  -- graue Waffe, NICHT geladen
    [3] = { 4865, 5, 0, 5, true },                                        -- grauer Plunder
    [4] = { 2589, 10, 1, 13, true },                                      -- Leinenstoff (weiss)
    [5] = { 1205, 1, 2, 200, true },                                      -- gruen
    [6] = { 9999, 1, 0, 0, true, nil, true },                             -- grau, ohne Wert
}
BAGITEMS[1] = { [1] = { 2779, 1, 0, 80, false }, [3] = { 2781, 1, 0, 20, false, "|cnIQ0:|Hitem:2781::|h[Alt]|h|r" } }                        -- grau, ungeladen, Link ohne Farbe
if startItem then BAGITEMS[1][2] = { startItem, 1, 0, 10, true } end
LP.db.autoRepair = false
FireEvent("MERCHANT_SHOW")
Advance(5)
check(sold(2777), "graue Waffe verkauft")
check(sold(2778), "graue Waffe verkauft, auch wenn das Spiel sie noch nicht geladen hat")
check(sold(4865), "grauer Plunder verkauft")
check(not sold(2589) and not sold(1205), "weisse und grüne Gegenstände bleiben")
check(not sold(9999), "Gegenstand ohne Wert bleibt")
if startItem then check(not sold(startItem), "Gegenstand, der eine Quest startet, bleibt") end
print("       nicht erkennbar (ungeladen, ohne Farbe): " .. (sold(2779) and "verkauft" or "bleibt"))
local msg
for _, m in ipairs(CHAT) do if m:find("graue Gegenst") then msg = m end end
check(sold(2781), "graue Waffe mit neuem Farbformat verkauft")
check(msg and msg:find("4 graue"), "Meldung: " .. tostring(msg))
check(msg and msg:find("1s 34c"), "Erlös nach echtem Goldzuwachs")
LP.db.autoSellGrey = false
USED = {}
BAGITEMS[0][7] = { 2780, 1, 0, 10, true }
FireEvent("MERCHANT_SHOW") Advance(3)
check(#USED == 0, "abschaltbar")
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
