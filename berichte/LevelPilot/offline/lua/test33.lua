-- Test 3.11: Dropraten lernen, echte Mob-Level, Austausch der Lernwerte, Buendeln, Sicherung, keine Taschen-Upgrades
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local Ca, P = LP.Calib, LP.Planner
Advance(1, 0.1)

-- 1) Upgrade-Vorschlaege: nicht fuer Gegenstaende, die beim Einloggen schon in der Tasche sind
check(LP.db.advUpgrades == true, "Upgrade-Vorschläge sind standardmässig an")
local A = LP.Advisor
local bag = { "item:7001", "item:7002" }
C_Container.GetContainerItemLink = function(b, sl) if b == 0 then return bag[sl] end return nil end
local origUV, origEq = A.UpgradeValue, LP.API.IsEquippable
A.UpgradeValue = function() return 10, {} end
LP.API.IsEquippable = function() return true end
local function Ups()
    local t = {}
    for _, h in ipairs(A.hints or {}) do if h.key:find("^up:") then t[#t + 1] = h.key:sub(4) end end
    return t
end
A:ResetLogin()
FireEvent("PLAYER_ENTERING_WORLD", true, false)
Advance(4, 0.5)
A:Run()
check(#Ups() == 0, "beim Einloggen: keine Vorschläge für Gegenstände aus der Tasche (" .. #Ups() .. ")")
Advance(30, 1)
A:Run()
check(#Ups() == 0, "auch später nicht für diese Gegenstände")
bag[3] = "item:7003"            -- neue Beute
A:Run()
local u = Ups()
check(#u == 1 and u[1] == "item:7003", "neue Beute wird vorgeschlagen (" .. table.concat(u, ",") .. ")")
A.UpgradeValue, LP.API.IsEquippable = origUV, origEq
C_Container.GetContainerItemLink = function() return nil end
A:Run()

-- 2) Quest mit Gegenstand von Gegnern suchen (keine Objekte)
local I = LevelPilotData.I
local qid, obj, oi0
for _, id in ipairs(LP.QuestDB:AllIds()) do
    local q = LP.QuestDB:Get(id)
    if q and q.level and q.level <= 10 and not q.dungeon then
        for oi, o in ipairs(q.objectives or {}) do
            local it = o.kind == "item" and o.item and I[o.item]
            if it and it.dn and #it.dn > 0 and not (it.dob and #it.dob > 0) then qid, obj, oi0 = id, o, oi break end
        end
    end
    if qid then break end
end
check(qid ~= nil, "Testquest mit Gegenstands-Ziel gefunden (" .. tostring(qid) .. ", Gegenstand " .. tostring(obj and obj.item) .. ")")
local npc = I[obj.item].dn[1]
-- in den Questlog: Ziel 0/6
local q = LP.QuestDB:Get(qid)
LOG[#LOG + 1] = { id = qid, title = q.name or "Test", level = q.level, objs = {} }
for i, o in ipairs(q.objectives) do LOG[#LOG].objs[i] = { (o.kind == "item" and "Gegenstand: 0/6" or "Ziel: 0/1"), false } end
local kills0 = P:ItemKills(obj)
-- Kampf: 20 Gegner getroffen und getoetet, 5 Stueck Beute
local cle = {}
CombatLogGetCurrentEventInfo = function() return unpack(cle) end
UnitGUID = function(u) if u == "player" then return "Player-1-00000001" end return nil end
for k = 1, 20 do
    local g = string.format("Creature-0-1-2-3-%d-%08d", npc, k)
    cle = { 0, "SWING_DAMAGE", false, "Player-1-00000001", "Ich", 0, 0, g }
    FireEvent("COMBAT_LOG_EVENT_UNFILTERED")
    cle = { 0, "UNIT_DIED", false, "", "", 0, 0, g }
    FireEvent("COMBAT_LOG_EVENT_UNFILTERED")
    if k % 4 == 0 then FireEvent("CHAT_MSG_LOOT", "Ihr bekommt Beute: |cffffffff|Hitem:" .. obj.item .. "::::::::|h[Teil]|h|r") end
end
local d = LevelPilotDB.calib.drops and LevelPilotDB.calib.drops[obj.item]
check(d and d.k == 20 and d.g == 5, "Kills und Beute gezählt (" .. tostring(d and d.k) .. "/" .. tostring(d and d.g) .. ")")
local rate = Ca:DropRate(obj.item)
check(rate and math.abs(rate - 0.25) < 0.01, "Droprate 25 % (" .. tostring(rate) .. ")")
check(Ca:Need(obj.item) == 6, "benötigte Anzahl aus dem Questlog: " .. tostring(Ca:Need(obj.item)))
local k1 = P:ItemKills(obj)
check(math.abs(k1 - 24) < 0.5, string.format("erwartete Kills 6 / 0,25 = 24 (%.1f, vorher Annahme %.1f)", k1, kills0))
-- fremde Kills ohne eigenen Treffer zaehlen nicht
local g = string.format("Creature-0-1-2-3-%d-%08d", npc, 999)
cle = { 0, "UNIT_DIED", false, "", "", 0, 0, g } FireEvent("COMBAT_LOG_EVENT_UNFILTERED")
check(LevelPilotDB.calib.drops[obj.item].k == 20, "Kill ohne eigenen Treffer zählt nicht")
-- seltene Drops: Speedrun-Regel
LevelPilotDB.calib.drops[obj.item] = { k = 100, g = 5 }
local slow, sk = P:SlowDrop(q)
check(slow, string.format("selten fallend erkannt (%.0f Kills)", sk or 0))
LevelPilotDB.calib.drops[obj.item] = { k = 20, g = 5 }

-- 3) virtuelle Reise misst nichts
LP.Virtual:Start("start") for _ = 1, 20 do Advance(0.05, 0.05) end
cle = { 0, "SWING_DAMAGE", false, "Player-1-00000001", "Ich", 0, 0, g } FireEvent("COMBAT_LOG_EVENT_UNFILTERED")
cle = { 0, "UNIT_DIED", false, "", "", 0, 0, g } FireEvent("COMBAT_LOG_EVENT_UNFILTERED")
LP.Virtual:Stop() Advance(0.2, 0.05)
check(LevelPilotDB.calib.drops[obj.item].k == 20, "während der virtuellen Reise wird nichts gemessen")

-- 4) echte Mob-Level: hoeher als im Datenpaket
local N = LevelPilotData.N
local mid = npc
local packLo = N[mid].lo
local TL = packLo + 3
UnitExists = function(u) return u == "target" end
UnitIsPlayer = function() return false end
UnitLevel = function(u) if u == "target" then return TL end return P and 6 end
UnitGUID = function(u) if u == "target" then return string.format("Creature-0-1-2-3-%d-00000077", mid) end if u == "player" then return "Player-1-00000001" end end
FireEvent("PLAYER_TARGET_CHANGED")
check(LevelPilotDB.calib.mobs and LevelPilotDB.calib.mobs[mid], "abweichendes Mob-Level gemerkt")
check(Ca:MobLo(mid, packLo) == TL, "Planung nimmt das höhere echte Level (" .. tostring(Ca:MobLo(mid, packLo)) .. ")")
check(LP.Danger:MobLevel(N[mid], mid) >= TL, "Gefahrenkarte nimmt das echte Level")
LevelPilotDB.calib.mobs[mid] = { packLo - 2, packLo - 2 }
check(Ca:MobLo(mid, packLo) == packLo, "tieferes echtes Level senkt nichts (Pflichtregel vorsichtig)")
LevelPilotDB.calib.mobs[mid] = nil

-- 5) Austausch
local sent0 = #SENT
LevelPilotDB.calib.drops[obj.item] = { k = 20, g = 5 }
local msgs = LP.Comm:EncodeDrop(obj.item)
check(msgs and msgs[1]:find("^D\t" .. obj.item .. "\t20\t5\t6"), "Droprate wird geteilt: " .. tostring(msgs and msgs[1]):gsub("\t", " "))
-- fremde Daten fuer einen anderen Gegenstand
local other
for id, it in pairs(I) do if id ~= obj.item and it.dn and #it.dn > 0 then other = id break end end
LP.Comm:Receive("D\t" .. other .. "\t30\t6\t8", "Freund-Server")
LP.Comm:Receive("D\t" .. other .. "\t30\t6\t8", "Freund-Server")     -- doppelt: zaehlt nicht doppelt
check(math.abs((Ca:DropRate(other) or 0) - 0.2) < 0.01, "fremde Droprate übernommen, Wiederholung zählt nicht doppelt")
LP.Comm:Receive("D\t" .. other .. "\t10\t90\t8", "Spassvogel")         -- unplausibel
check(math.abs((Ca:DropRate(other) or 0) - 0.2) < 0.01, "unplausible Meldung abgelehnt")
local keys = 0
for k in pairs(LevelPilotDB.calib.netDrops[other]) do keys = keys + 1 check(not k:find("Freund"), "Absender ohne Namen gespeichert (" .. k .. ")") end
LP.Comm:Receive("M\t" .. mid .. "\t" .. (packLo + 2) .. "\t" .. (packLo + 2), "A-Server")
check(Ca:MobLo(mid, packLo) == packLo, "fremdes Mob-Level erst ab zwei Meldungen")
LP.Comm:Receive("M\t" .. mid .. "\t" .. (packLo + 2) .. "\t" .. (packLo + 2), "B-Server")
check(Ca:MobLo(mid, packLo) == packLo + 2, "nach zwei Meldungen benutzt")
LP.Comm:Receive("F\t5\t20000\t800", "C-Server")
check(LevelPilotDB.calib.netFlights and next(LevelPilotDB.calib.netFlights), "fremde Flugzeiten gespeichert")
LP.Comm:Receive("F\t5\t20000\t99999", "D-Server")
local nf = 0 for _ in pairs(LevelPilotDB.calib.netFlights) do nf = nf + 1 end
check(nf == 1, "unplausible Flugzeit abgelehnt")

-- 6) Sicherung enthaelt die Lernwerte, Heilung bringt sie zurueck
LevelPilotDB.qdb[424242] = LevelPilotDB.qdb[424242] or { n = "Sicherungstest", t = 1 }
LP.Backup:SaveCopy()
local bk = LevelPilotCharDB.backup and LevelPilotCharDB.backup.data
check(bk and bk.calib and bk.calib.drops and bk.calib.drops[obj.item], "Lernwerte in der Sicherung")
check(bk.calib ~= LevelPilotDB.calib, "eigene Kopie, nicht dieselbe Tabelle")
LevelPilotDB.calib.drops = nil
LP.Backup:SaveCopy()
check(LevelPilotDB.calib.drops and LevelPilotDB.calib.drops[obj.item], "verlorene Dropraten aus der Sicherung zurückgeholt")

-- 7) Buendeln: zwei Quests mit Zielen am selben Ort
local fake1 = { id = 900001, objectives = { { kind = "kill", spots = { { 1411, 50, 50 } } } } }
local fake2 = { id = 900002, objectives = { { kind = "kill", spots = { { 1411, 50.5, 50.2 } } } } }
local fake3 = { id = 900003, objectives = { { kind = "kill", spots = { { 1411, 80, 20 } } } } }
local idx = P:BundleIndex({ { q = fake1 }, { q = fake2 }, { q = fake3 } }, 10)
local c1 = P:BundlePartners(idx, fake1)
local c3 = P:BundlePartners(idx, fake3)
check(c1 == 1 and c3 == 0, "Ziele nebeneinander werden gebündelt (" .. c1 .. "), weit weg nicht (" .. c3 .. ")")
local qa = LP.QuestDB:Get(qid)
check(P.QuestSeconds(qa, 2) < P.QuestSeconds(qa, 0), "gebündelt: geteilte Suchzeit macht die Quest schneller")
local fakeE = { id = 900004, objectives = { { kind = "kill", elite = true, spots = { { 1411, 50, 50 } } } } }
local idx2 = P:BundleIndex({ { q = fake1 }, { q = fakeE } }, 10)
check(P:BundlePartners(idx2, fake1) == 0, "Elite-Ziele werden nicht gebündelt")
local fakeH = { id = 900005, objectives = { { kind = "kill", mobLevel = 20, spots = { { 1411, 50, 50 } } } } }
local idx3 = P:BundleIndex({ { q = fake1 }, { q = fakeH } }, 10)
check(P:BundlePartners(idx3, fake1) == 0, "Ziele mit zu starken Mobs werden nicht gebündelt (Pflichtregel)")

-- 8) Bericht der Messung zeigt die Lernwerte
dofile(dir .. "/m_stub.lua")
local mt = LP.Measure:Text()
check(mt:find("Dropraten:", 1, true), "Messung zeigt Dropraten und Mob-Level")
for _, m in ipairs(CHAT) do if m:find("attempt") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
