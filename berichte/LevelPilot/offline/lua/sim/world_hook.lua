-- Ersetzt die Test-Karten durch echte WoW-Forever-Kartengrenzen
dofile(os.getenv("SIMDIR") .. "/worlddata.lua")
local M = WORLD.maps
-- Kontinente als Huelle ihrer Zonen
for _, cont in ipairs({ { 1414, 1, "Kalimdor" }, { 1415, 0, "Östliche Königreiche" } }) do
    local b = { name = cont[3], inst = cont[2], continent = true }
    for _, z in pairs(M) do
        if z.inst == cont[2] then
            b.left = math.max(b.left or -1e9, z.left)
            b.right = math.min(b.right or 1e9, z.right)
            b.top = math.max(b.top or -1e9, z.top)
            b.bottom = math.min(b.bottom or 1e9, z.bottom)
        end
    end
    M[cont[1]] = b
end
C_Map.GetWorldPosFromMapPos = function(map, v)
    local b = M[map]
    if not b then return nil end
    return b.inst, CreateVector2D(b.top + (b.bottom - b.top) * v.y, b.left + (b.right - b.left) * v.x)
end
C_Map.GetBestMapForUnit = function() return P.map end
C_Map.GetPlayerMapPosition = function(map)
    if map == P.map then return CreateVector2D(P.x / 100, P.y / 100) end
    return nil
end
C_Map.GetMapInfo = function(map)
    local b = M[map]
    if not b then return nil end
    if b.continent then return { mapID = map, name = b.name, mapType = 2, parentMapID = 947 } end
    return { mapID = map, name = b.name, mapType = 3, parentMapID = b.parent }
end
C_Map.GetMapRectOnMap = function(map, onto)
    local z, c = M[map], M[onto]
    if not z or not c or z.inst ~= c.inst then return nil end
    local l = (z.left - c.left) / (c.right - c.left)
    local r = (z.right - c.left) / (c.right - c.left)
    local t = (z.top - c.top) / (c.bottom - c.top)
    local bt = (z.bottom - c.top) / (c.bottom - c.top)
    return l, r, t, bt
end
UnitPosition = function()
    local b = M[P.map]
    return b.top + (b.bottom - b.top) * P.y / 100, b.left + (b.right - b.left) * P.x / 100, 0, b.inst
end
