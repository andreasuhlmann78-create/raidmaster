-- ERA-1 (b) 3.12.71: Laufen entlang des Weges in 30-yd-Schritten mit Neuberechnung; zählt Pfeil-Umkehrungen und Anstiege der Restlänge.
-- Immer Classic Era. Aufruf (aus diesem Ordner): LVL=1 MAP=1429 PX=48.0 PY=42.0 [TX=43.8 TY=65.8] PACKDIR=<LevelPilot_Data> lua51 mess_era1_weg.lua <LevelPilot> 0 Human WARRIOR Alliance
function GetBuildInfo() return "1.15.7", "61000", "Jun 1 2025", 11507 end
WOW_PROJECT_ID, WOW_PROJECT_CLASSIC = 2, 2
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
Advance(3)
LP.Jobs.sync = true
local G = LP.Geo
local tx, ty = tonumber(os.getenv("TX") or 43.8), tonumber(os.getenv("TY") or 65.8)
local sx, sy = tonumber(os.getenv("PX")), tonumber(os.getenv("PY"))
local map = tonumber(os.getenv("MAP"))
local ti, tn, tw = G:ToWorld(map, tx, ty)
local si, pn, pw = G:ToWorld(map, sx, sy)
local function Len(p, i0) local d=0 for i=(i0 or 2),#p do d=d+G:Dist(p[i-1][2],p[i-1][3],p[i][2],p[i][3]) end return d end
local function Calc(n, w)
  local raw = LP.Graph:Path(si, n, w, map, ti, tn, tw, map)
  return LP.Terrain:Refine(raw) or raw
end
local walked, flips, maxRem, prevDir = 0, 0, 0, nil
local path = Calc(pn, pw)
local out = {}
for step = 1, 200 do
  -- naechsten Wegpunkt (wie CurrentWaypoint: < 10 yd erreicht)
  local idx = 2
  while path[idx + 1] and G:Dist(pn, pw, path[idx][2], path[idx][3]) < 10 do idx = idx + 1 end
  local wp = path[idx]
  local rem = G:Dist(pn, pw, wp[2], wp[3]) + Len(path, idx + 1)
  local dn, dw = wp[2] - pn, wp[3] - pw
  local dl = math.sqrt(dn*dn+dw*dw)
  if dl < 1 then break end
  local dir = { dn/dl, dw/dl }
  if prevDir then
    local c = dir[1]*prevDir[1]+dir[2]*prevDir[2]
    if c < 0 then flips = flips + 1 out[#out+1] = string.format("Umkehr bei %.0f yd (Rest %.0f)", walked, rem) end
  end
  if rem > maxRem then maxRem = rem end
  out[#out+1] = string.format("%.0f:%.0f", walked, rem)
  prevDir = dir
  local st = math.min(30, G:Dist(pn, pw, tn, tw))
  if G:Dist(pn, pw, tn, tw) < 15 then break end
  -- 30 yd entlang des Weges laufen
  local left = 30
  local i = idx
  while left > 0 and path[i] do
    local d = G:Dist(pn, pw, path[i][2], path[i][3])
    if d <= left then pn, pw = path[i][2], path[i][3] left = left - d i = i + 1
    else pn, pw = pn + (path[i][2]-pn)*left/d, pw + (path[i][3]-pw)*left/d left = 0 end
  end
  walked = walked + 30 - left
  path = Calc(pn, pw)
end
local rises, prev = 0, nil
for _, o in ipairs(out) do local r = tonumber(o:match(":(%d+)$")) if r and prev and r > prev + 20 then rises = rises + 1 end prev = r or prev end
print(string.format("gelaufen %.0f yd, Umkehrungen %d, Rest steigt %d, Start %s", walked, flips, rises, out[1]))
print(table.concat(out, " "))
os.exit(0)
