-- Simulation mit Kartenrahmen, die das Addon IM SPIEL gemessen hat (/lp kartenrahmen, C_Map.GetWorldPosFromMapPos – Laufzeit-API,
-- keine Spieldateien; EULA-Entscheid des Nutzers 17.11.2026). Ersetzt die Test-Karten des Nachbaus.
-- Aufruf: WORLDHOOK=<dieser Pfad> KARTENRAHMEN=<Datei> – die Datei ist entweder die SavedVariables-Datei LevelPilot.lua
-- (LevelPilotDB.kartenrahmen) oder eine Datei mit "KARTENRAHMEN = { maps = {...} }".
-- Je Karte: { inst, n0, w0, n1, w1, Kartentyp, Elternkarte } = Weltlage der Kartenecken (0,0) und (1,1).
local file = os.getenv("KARTENRAHMEN")
assert(file and file ~= "", "KARTENRAHMEN=<Datei> fehlt")
local env = {}
local chunk = assert(loadfile(file))
setfenv(chunk, env)
chunk()
local kr = env.KARTENRAHMEN or (env.LevelPilotDB and env.LevelPilotDB.kartenrahmen)
assert(kr and kr.maps, "keine Kartenrahmen in " .. file)
local M = {}
for id, r in pairs(kr.maps) do
    M[tonumber(id)] = { inst = r[1], top = r[2], left = r[3], bottom = r[4], right = r[5], mapType = r[6], parent = r[7] }
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
    return { mapID = map, name = "Karte " .. map, mapType = b.mapType, parentMapID = b.parent }
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
