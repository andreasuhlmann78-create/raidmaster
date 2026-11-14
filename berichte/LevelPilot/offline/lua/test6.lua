dofile("./mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
-- Kartenfunktion faellt aus, nur UnitPosition liefert die Weltposition
local orig = C_Map.GetPlayerMapPosition
local _, ref = C_Map.GetWorldPosFromMapPos(P.map, CreateVector2D(P.x / 100, P.y / 100))
local rn, rw = ref:GetXY()
C_Map.GetPlayerMapPosition = function() return nil end
UnitPosition = function() return rn, rw, 0, 0 end
NOW = NOW + 1
local inst, n, w, map, x, y = LP.Geo:Player()
check(inst and math.abs(x - P.x) < 0.01 and math.abs(y - P.y) < 0.01, string.format("Position über UnitPosition: %.1f, %.1f", x or -1, y or -1))
C_Map.GetPlayerMapPosition = orig
-- Vorrang der aktuellen Zone: Spieler in Westfall (1436) am Zonenrand
P.map, P.x, P.y, P.level = 1436, 60, 20, 11
NOW = NOW + 1
LP.Planner:BuildCandidates()
LP.Planner:Replan()
check(LP.Planner.focus == 1436, "Fokus auf aktueller Zone Westfall (gewählt: " .. tostring(LP.Planner.focus) .. ")")
LP.UI:Refresh()
print("Kopf: " .. tostring(rawget(LevelPilotFrame.xtext, "_text")):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""))
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
