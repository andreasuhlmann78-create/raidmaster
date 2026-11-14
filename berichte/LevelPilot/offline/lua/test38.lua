-- Test 3.12.4: Dropraten auf dem modernen Client (Beutefenster) und neue Standard-Einstellungen
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
issecretvalue = function(v) return false end          -- moderner Client (kennt geschuetzte Werte)
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
Advance(1, 0.1)
check(LP.Game.IsModern, "moderner Client")
-- neue Standard-Einstellungen (neuer Spieler)
check(LP.db.restock == false and LP.db.autoEquipRewards == false and LP.db.autoRepair == true and LP.db.autoFly == true,
    "Nachkaufen und Belohnung anlegen neu aus, Reparieren und Auto-Flug an (Entscheid 3.12.5)")
-- Quest mit Gegenstand von Gegnern
local I = LevelPilotData.I
local qid, obj
for _, id in ipairs(LP.QuestDB:AllIds()) do
    local q = LP.QuestDB:Get(id)
    if q and q.level and q.level <= 10 and not q.dungeon then
        for _, o in ipairs(q.objectives or {}) do
            local it = o.kind == "item" and o.item and I[o.item]
            if it and it.dn and #it.dn > 0 and not (it.dob and #it.dob > 0) then qid, obj = id, o break end
        end
    end
    if qid then break end
end
local q = LP.QuestDB:Get(qid)
LOG[#LOG + 1] = { id = qid, title = q.name or "Test", level = q.level, objs = {} }
for i, o in ipairs(q.objectives) do LOG[#LOG].objs[i] = { (o.kind == "item" and "Gegenstand: 0/6" or "Ziel: 0/1"), false } end
local npc = I[obj.item].dn[1]
-- Beutefenster nachbilden: 20 Leichen, jede 4. mit dem Gegenstand
local slots = {}
GetNumLootItems = function() return #slots end
GetLootSlotLink = function(i) return slots[i].link end
GetLootSourceInfo = function(i) return slots[i].guid, slots[i].qty end
for k = 1, 20 do
    local g = string.format("Creature-0-1-2-3-%d-%08d", npc, k)
    slots = { { link = nil, guid = g, qty = 1 } }             -- Gold/Plunder
    if k % 4 == 0 then slots[2] = { link = "|cffffffff|Hitem:" .. obj.item .. "::::::::|h[Teil]|h|r", guid = g, qty = 1 } end
    FireEvent("LOOT_OPENED")
    -- 3.12.6: Stueck zaehlen erst, wenn die Beute-Meldung kommt (Gegenstand wirklich in der Tasche)
    if k % 4 == 0 then FireEvent("CHAT_MSG_LOOT", "Ihr bekommt Beute: |cffffffff|Hitem:" .. obj.item .. "::::::::|h[Teil]|h|r") end
    FireEvent("LOOT_CLOSED")
    if k == 5 then FireEvent("LOOT_OPENED") FireEvent("LOOT_CLOSED") end   -- dieselbe Leiche noch einmal: nicht doppelt
    Advance(4, 1)
end
local d = LevelPilotDB.calib.drops and LevelPilotDB.calib.drops[obj.item]
check(d and d.k == 20 and d.g == 5, "beim Plündern gezählt: 20 Kills, 5 Stück (" .. tostring(d and d.k) .. "/" .. tostring(d and d.g) .. ")")
check(math.abs((LP.Calib:DropRate(obj.item) or 0) - 0.25) < 0.01, "Droprate 25 %")
-- Chat-Meldung ausserhalb eines Beutefensters zaehlt auf dem modernen Client nicht zusaetzlich
FireEvent("CHAT_MSG_LOOT", "Ihr bekommt Beute: |cffffffff|Hitem:" .. obj.item .. "::::::::|h[Teil]|h|r")
check(LevelPilotDB.calib.drops[obj.item].g == 5, "Beute-Meldung zählt nicht doppelt")
-- Tasche voll: Gegenstand bleibt liegen (keine Meldung) -> Kill ja, Stueck nein
slots = { { link = "|cffffffff|Hitem:" .. obj.item .. "::::::::|h[Teil]|h|r", guid = string.format("Creature-0-1-2-3-%d-%08d", npc, 77), qty = 1 } }
FireEvent("LOOT_OPENED") FireEvent("LOOT_CLOSED") Advance(4, 1)
check(LevelPilotDB.calib.drops[obj.item].k == 21 and LevelPilotDB.calib.drops[obj.item].g == 5, "liegen gebliebene Beute zählt nicht")
-- spaeter aufgehoben: zaehlt dann
FireEvent("LOOT_OPENED")
FireEvent("CHAT_MSG_LOOT", "Ihr bekommt Beute: |cffffffff|Hitem:" .. obj.item .. "::::::::|h[Teil]|h|r")
FireEvent("LOOT_CLOSED")
check(LevelPilotDB.calib.drops[obj.item].k == 21 and LevelPilotDB.calib.drops[obj.item].g == 6, "später aufgehoben: zählt einmal")
-- geschuetzte Werte im Beutefenster
local SECRET = setmetatable({}, { __eq = function() error("secret") end, __concat = function() error("secret") end, __index = function() error("secret") end })
issecretvalue = function(v) return rawequal(v, SECRET) end
slots = { { link = SECRET, guid = SECRET, qty = SECRET } }
local ok = pcall(FireEvent, "LOOT_OPENED")
local chatErr = false
for _, m in ipairs(CHAT) do if m:find("secret") or m:find("attempt") then chatErr = true end end
check(ok and not chatErr and LevelPilotDB.calib.drops[obj.item].k == 21, "geschützte Werte im Beutefenster: kein Fehler, nicht gezählt")
-- virtuelle Reise zaehlt nichts
issecretvalue = function() return false end
LP.Virtual:Start("start") for _ = 1, 10 do Advance(0.05, 0.05) end
slots = { { link = nil, guid = string.format("Creature-0-1-2-3-%d-%08d", npc, 999), qty = 1 } }
FireEvent("LOOT_OPENED")
LP.Virtual:Stop() Advance(0.2, 0.05)
check(LevelPilotDB.calib.drops[obj.item].k == 21, "während der virtuellen Reise wird nichts gezählt")
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
