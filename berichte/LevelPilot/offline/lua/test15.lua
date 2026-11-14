-- Test: Hoehlen, Tunnel und gelaufene Wege in der Wegfuehrung
-- Aufruf: PACKDIR=... lua51 test15.lua <Addon>
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
INDOORS, RESTING = false, false
dofile(dir .. "/mock2.lua")
function IsIndoors() return INDOORS end
function IsResting() return RESTING end
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local Geo, G, Ca = LP.Geo, LP.Graph, LP.Caves
local function W(map, x, y) local i, n, w = Geo:ToWorld(map, x, y) return i, n, w end
local function D(a, b) return Geo:Dist(a[2], a[3], b[2], b[3]) end
local function path(m1, x1, y1, m2, x2, y2)
    local i1, n1, w1 = W(m1, x1, y1)
    local i2, n2, w2 = W(m2, x2, y2)
    local p, kind = G:Path(i1, n1, w1, m1, i2, n2, w2, m2)
    local rp = LP.Terrain:Refine(p)
    return p, kind, rp
end

-- 1) Startwerte
local total = Ca:Count()
check(total >= 3, "Höhlen-Startwerte geladen: " .. total)

-- 2) Ziel in der Mine (Echo-Kamm), Spieler draussen an der Abtei
local ei, en, ew = W(1429, 47.5, 31.9)
local E = { ei, en, ew }
local p, kind, rp = path(1429, 48.2, 42.9, 1429, 49.5, 27.6)
check(kind == "cave", "Ziel in der Höhle: Weg über den Eingang (" .. tostring(kind) .. ")")
local nearE, idxE = 1e9, nil
for i, pt in ipairs(rp) do local d = D(pt, E) if d < nearE then nearE, idxE = d, i end end
check(nearE < 5, string.format("Weg führt durch den Eingang (%.1f Yards)", nearE))
local innerOK = true
for i = idxE + 1, #rp do if not rp[i].cave then innerOK = false end end
check(innerOK, "nach dem Eingang nur Höhlen-Punkte (keine Geländeführung im Berg)")
-- ohne Hoehlenwissen ginge es direkt
local i1, n1, w1 = W(1429, 48.2, 42.9)
local i2, n2, w2 = W(1429, 49.5, 27.6)
local raw = G:PathRaw(i1, n1, w1, 1429, i2, n2, w2, 1429)
local rawNear = 1e9
for _, pt in ipairs(LP.Terrain:Refine(raw)) do rawNear = math.min(rawNear, D(pt, E)) end
print(string.format("       ohne Höhlenwissen: nächster Punkt %.0f Yards vom Eingang", rawNear))

-- 3) Spieler in der Mine, Ziel draussen
INDOORS = true
P.map, P.x, P.y = 1429, 49.4, 28.0
local p3, k3 = path(1429, 49.4, 28.0, 1429, 48.2, 42.9)
local first = 1e9
for i = 1, math.min(#p3, 4) do first = math.min(first, D(p3[i], E)) end
check(k3 == "cave" and first < 5, "aus der Höhle: zuerst zum Eingang (" .. tostring(k3) .. ")")
INDOORS = false
local _, k4 = path(1429, 49.4, 28.0, 1429, 48.2, 42.9)
check(k4 ~= "cave", "oben auf dem Berg (draussen): kein Umweg über den Eingang")

-- 4) Tunnel Dun Morogh -> Loch Modan: Tunnelstrecke bleibt gerade
local p5, k5, r5 = path(1426, 70.0, 50.0, 1432, 30.0, 70.0)
local gwPair, bent = false, false
for i = 2, #r5 do
    if r5[i - 1].gw and r5[i].gw then gwPair = true end
end
for i = 2, #p5 do
    if p5[i - 1].gw and p5[i].gw then
        -- zwischen den beiden Tunnelenden darf nach der Verfeinerung nichts eingefuegt sein
        for j = 2, #r5 do
            if r5[j - 1][2] == p5[i - 1][2] and r5[j - 1][3] == p5[i - 1][3] and not (r5[j][2] == p5[i][2] and r5[j][3] == p5[i][3]) then bent = true end
        end
    end
end
check(gwPair and not bent, "Tunnel Nordtorposten: Strecke durch den Tunnel unverändert (" .. tostring(k5) .. ")")

-- 5) gelaufene Wege werden nicht verbogen
local poly = {}
for k = 0, 10 do
    local x = 30 + k * 1.2
    local y = 60 + math.sin(k / 10 * math.pi) * 3
    local i, n, w = W(1436, x, y)
    poly[#poly + 1] = { i, n, w, 1436 }
end
G:AddPolyline(poly, "r", false)
local p6, k6, r6 = path(1436, 30.0, 60.0, 1436, 42.0, 60.0)
local onWalk = 0
for i = 2, #p6 do if p6[i].via == "r" then onWalk = onWalk + 1 end end
check(onWalk >= 5, "Weg nutzt den gelaufenen Weg (" .. onWalk .. " Abschnitte)")
check(#r6 == #p6, "gelaufener Weg bleibt wie gelaufen (" .. #p6 .. " → " .. #r6 .. " Punkte)")

-- 6) Gelaende-Kosten: gelaufener Umweg schlaegt die Luftlinie quer ueber den Berg
local function walkable(map, x, y)
    local a = { W(map, x, y) }
    return LP.Terrain:Unknown(map, a, a) == 0
end
local pick
for y = 30, 70, 1 do
    for x = 25, 75, 1 do
        if not pick and walkable(1426, x, y) and walkable(1426, x + 8, y) then
            local a, b = { W(1426, x, y) }, { W(1426, x + 8, y) }
            if LP.Terrain:Unknown(1426, a, b) >= 0.6 then pick = { x, y } end
        end
    end
end
check(pick ~= nil, "Dun Morogh: Strecke mit Berg dazwischen gefunden" .. (pick and (" (" .. pick[1] .. ", " .. pick[2] .. ")") or ""))
if pick then
    local x, y = pick[1], pick[2]
    -- gelaufener Umweg in einem Bogen (ca. 1,9-fache Strecke)
    local arc = {}
    for k = 0, 12 do
        local t = k / 12
        local i, n, w = W(1426, x + 8 * t, y - math.sin(t * math.pi) * 6)
        arc[#arc + 1] = { i, n, w, 1426 }
    end
    G:AddPolyline(arc, "r", false)
    local len = 0
    for k = 2, #arc do len = len + D(arc[k - 1], arc[k]) end
    local direct = D(arc[1], arc[#arc])
    local p7 = path(1426, x, y, 1426, x + 8, y)
    local used = 0
    for i = 2, #p7 do if p7[i].via == "r" then used = used + 1 end end
    check(used >= 6, string.format("Umweg (%.1f-fach) über gelaufenen Weg statt über den Berg (%d Abschnitte)", len / direct, used))
end

-- 7) Lernen: hinein, 50 Yards tief, wieder heraus
local function at(map, x, y) P.map, P.x, P.y = map, x, y NOW = NOW + 1 Ca:Tick() end
INDOORS = false
at(1436, 60.0, 30.0) at(1436, 60.3, 30.0)
INDOORS = true
for k = 1, 8 do at(1436, 60.3 + k * 0.35, 30.0 + k * 0.1) end
INDOORS = false
at(1436, 60.4, 30.0)
local c1 = 0 for _, c in pairs(LP.db.caves) do if not c.net then c1 = c1 + 1 end end
check(c1 == 1, "Höhle gelernt (" .. c1 .. ")")
local _, cn, cw = W(1436, 61.7, 30.4)
local cave = Ca:At(select(1, W(1436, 61.7, 30.4)), cn, cw)
check(cave ~= nil, "gelernter Innenraum wird erkannt")
-- zweiter Besuch: kein Duplikat
at(1436, 60.1, 30.0)
INDOORS = true
for k = 1, 8 do at(1436, 60.3 + k * 0.35, 30.0 + k * 0.1) end
INDOORS = false
at(1436, 60.3, 30.1)
local c2 = 0 for _ in pairs(LP.db.caves) do c2 = c2 + 1 end
check(c2 == 1, "zweiter Besuch: zusammengelegt, kein doppelter Eingang")
-- Tunnel mit zwei Ausgaengen
at(1436, 50.0, 50.0)
INDOORS = true
for k = 1, 10 do at(1436, 50.0 + k * 0.6, 50.0) end
INDOORS = false
at(1436, 56.5, 50.0)
local c3 = 0 for _ in pairs(LP.db.caves) do c3 = c3 + 1 end
check(c3 == 3, "Tunnel: beide Enden als Eingang gespeichert (" .. c3 .. ")")
-- Gasthaus: nichts lernen
RESTING = true
at(1429, 43.0, 65.0)
INDOORS = true
for k = 1, 8 do at(1429, 43.0 + k * 0.4, 65.0) end
INDOORS = false RESTING = false
at(1429, 43.1, 65.0)
local c4 = 0 for _ in pairs(LP.db.caves) do c4 = c4 + 1 end
check(c4 == 3, "Gasthaus/Stadt wird nicht als Höhle gelernt")
-- kurzes Gebaeude: nichts lernen
at(1429, 30.0, 30.0)
INDOORS = true at(1429, 30.3, 30.0) at(1429, 30.5, 30.0) at(1429, 30.6, 30.1)
INDOORS = false at(1429, 30.1, 30.0)
local c5 = 0 for _ in pairs(LP.db.caves) do c5 = c5 + 1 end
check(c5 == 3, "kleines Gebäude wird nicht als Höhle gelernt")

-- 8) Austausch: senden und empfangen
local key, own
for k, c in pairs(LP.db.caves) do key, own = k, c break end
local msg = LP.Comm:EncodeCave(own)[1]
check(msg:sub(1, 2) == "C\t", "Höhle wird als Nachricht kodiert")
local saved = LP.db.caves
LP.db.caves = {}
LP.Comm:Receive(msg, "Anderer-Server")
local recv
for _, c in pairs(LP.db.caves) do recv = c end
check(recv and recv.net and math.abs(recv.en - own.en) < 1, "empfangene Höhle gespeichert (von anderen)")
LP.Caves:Store({ i = own.i, en = own.en, ew = own.ew, m = own.m, cn = own.cn, cw = own.cw, r = own.r }, false)
local afterOwn
for _, c in pairs(LP.db.caves) do afterOwn = c end
check(afterOwn and not afterOwn.net, "eigene Beobachtung ersetzt die empfangene")
LP.Comm:Receive("C\t1\t0\t0\t0\t9000\t9000\t50\t0", "Spassvogel")
local n8 = 0 for _ in pairs(LP.db.caves) do n8 = n8 + 1 end
check(n8 == 1, "unplausible Höhle abgelehnt")
LP.db.caves = saved

-- 9) Sicherung: Export/Import enthaelt Hoehlen
local text = LP.Backup:Export()
local keep = LP.db.caves
LP.db.caves = {}
local ok, info = LP.Backup:Import(text)
local n9 = 0 for _ in pairs(LP.db.caves) do n9 = n9 + 1 end
check(ok and n9 == 3, "Sicherungstext stellt Höhlen wieder her (" .. n9 .. ") – " .. tostring(info))
LP.Backup:SaveCopy()
local n10 = 0 for _ in pairs(LevelPilotCharDB.backup and LevelPilotCharDB.backup.data.caves or {}) do n10 = n10 + 1 end
check(n10 == 3 and LevelPilotCharDB.backup.data.caves ~= LP.db.caves, "Charakter-Kopie enthält die Höhlen als eigene Kopie (" .. n10 .. ")")

for _, m in ipairs(CHAT) do if m:find("Fehler") and not m:find("keiner") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
