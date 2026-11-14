-- Test: Upgrade-Vorschlaege passen zur Klasse
-- Aufruf: lua51 test12.lua <Addon> 0 <Volk> <KLASSE> <Fraktion>
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local A = LP.Advisor
local _, cls = UnitClass("player")
P.level = 40

-- Gegenstaende: [link] = { info, stats, tooltip }
ITEMS = {
    ["item:1"] = { { "Plattenhelm der Stärke", nil, 2, 20, 15, nil, nil, 1, "INVTYPE_HEAD", nil, 100, 4, 4 },
                   { ITEM_MOD_STRENGTH_SHORT = 8, ITEM_MOD_STAMINA_SHORT = 6, RESISTANCE0_NAME = 40 }, {} },
    ["item:2"] = { { "Stoffkappe der Intelligenz", nil, 2, 20, 15, nil, nil, 1, "INVTYPE_HEAD", nil, 100, 4, 1 },
                   { ITEM_MOD_INTELLECT_SHORT = 8, ITEM_MOD_SPIRIT_SHORT = 6, RESISTANCE0_NAME = 15 }, {} },
    ["item:3"] = { { "Robe des Magiers", nil, 3, 22, 15, nil, nil, 1, "INVTYPE_CHEST", nil, 300, 4, 1 },
                   { ITEM_MOD_INTELLECT_SHORT = 10, ITEM_MOD_STAMINA_SHORT = 4 },
                   { { "Robe des Magiers", 1, 1, 1 }, { "Klassen: Magier", 1, 1, 1 } } },
    ["item:4"] = { { "Bogen", nil, 2, 22, 15, nil, nil, 1, "INVTYPE_RANGED", nil, 300, 2, 2 },
                   { ITEM_MOD_AGILITY_SHORT = 5, ITEM_MOD_DAMAGE_PER_SECOND_SHORT = 12 },
                   { { "Bogen", 1, 1, 1 }, { "Bögen", 1, 0.1, 0.1 } } },
    ["cur:head"] = { { "Alter Hut", nil, 1, 10, 5, nil, nil, 1, "INVTYPE_HEAD", nil, 10, 4, 1 },
                     { ITEM_MOD_STAMINA_SHORT = 1, RESISTANCE0_NAME = 5 }, {} },
}
ITEM_CLASSES_ALLOWED = "Klassen: %s"
ITEM_MOD_STRENGTH_SHORT, ITEM_MOD_INTELLECT_SHORT, ITEM_MOD_STAMINA_SHORT = "Stärke", "Intelligenz", "Ausdauer"
ITEM_MOD_AGILITY_SHORT, ITEM_MOD_SPIRIT_SHORT = "Beweglichkeit", "Willenskraft"
local CLASSNAME = { WARRIOR = "Krieger", MAGE = "Magier", HUNTER = "Jäger", PRIEST = "Priester", ROGUE = "Schurke" }
UnitClass = function() return CLASSNAME[cls] or cls, cls, 1 end
C_Item = C_Item or {}
C_Item.GetItemInfo = function(l) local e = ITEMS[l] if e then return unpack(e[1]) end end
C_Item.GetItemStats = function(l) local e = ITEMS[l] return e and e[2] or {} end
C_TooltipInfo = { GetHyperlink = function(l)
    local e = ITEMS[l]
    local lines = {}
    for _, t in ipairs(e and e[3] or {}) do lines[#lines + 1] = { leftText = t[1], leftColor = { r = t[2], g = t[3], b = t[4] } } end
    return { lines = lines }
end }
GetInventoryItemLink = function(_, slot) if slot == 1 then return "cur:head" end return nil end

local plate = A:UpgradeValue("item:1")
local cloth = A:UpgradeValue("item:2")
local robe = A:UpgradeValue("item:3")
local bow = A:UpgradeValue("item:4")
print(string.format("       %s: Stärke-Platte=%s  Int-Stoff=%s  Magier-Robe=%s  Bogen(rot)=%s", cls,
    tostring(plate), tostring(cloth), tostring(robe), tostring(bow)))
if cls == "WARRIOR" then
    check(plate and plate > 0, "Krieger: Stärke-Helm ist ein Upgrade")
    check(not cloth, "Krieger: Intelligenz-Kappe wird nicht vorgeschlagen")
    check(not robe, "Krieger: Magier-Klassenrobe wird nicht vorgeschlagen")
elseif cls == "MAGE" then
    check(not plate, "Magier: Platte/Stärke wird nicht vorgeschlagen")
    check(cloth and cloth > 0, "Magier: Intelligenz-Kappe ist ein Upgrade")
    check(robe and robe > 0, "Magier: eigene Klassenrobe wird vorgeschlagen")
elseif cls == "ROGUE" then
    check(not plate and not cloth, "Schurke: weder Platte noch Intelligenz")
end
check(not bow, "rote Tooltipzeile (Waffenart nicht erlernt) blockiert")
local sum = A:StatSummary(select(2, A:UpgradeValue(cls == "MAGE" and "item:2" or "item:1")) or {})
print("       Hinweis zeigt: " .. tostring(sum))
if cls == "WARRIOR" or cls == "MAGE" then check(sum ~= "" and not (cls == "WARRIOR" and sum:find("Intelligenz")) and not (cls == "MAGE" and sum:find("Stärke")), "Hinweis nennt nur Werte, die der Klasse helfen") end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
