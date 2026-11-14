-- Test 3.12.2: Zeitmodell - EP je Kill nach Levelunterschied, Forever-Abschlag, Dungeon-Werte, EP-Messung,
-- beide Modi vergleichen
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local PL, Ca = LP.Planner, LP.Calib
local P = _G.P   -- Spieler im Mock
Advance(1, 0.1)
local function near(a, b, eps) return math.abs(a - b) <= (eps or 0.01) end
-- 1) Formel (Classic)
check(PL:KillXPFormula(20, 20) == 145, "gleich hoch: 45 + 5 x 20 = 145")
check(near(PL:KillXPFormula(20, 22), 145 * 1.10), "2 Level höher: +10 %")
check(near(PL:KillXPFormula(20, 30), 145 * 1.20), "höher: höchstens +20 % (4 Level)")
check(near(PL:KillXPFormula(20, 17), 145 * (1 - 3 / 11)), "3 Level tiefer: x (1 - 3/11)")
check(PL:KillXPFormula(20, 13) == 0 and PL:GreyLevel(20) == 13, "grau (Level 13 bei 20): 0 EP")
check(PL.ZeroDiff(7) == 5 and PL.ZeroDiff(8) == 6 and PL.ZeroDiff(45) == 14 and PL.ZeroDiff(59) == 16, "ZD-Tabelle")
check(PL:GreyLevel(5) == 0 and PL:GreyLevel(45) == 35 and PL:GreyLevel(59) == 47, "Grau-Grenzen")
-- 2) Forever-Abschlag nur fuer gruene Monster
check(LP.API.Forever(), "Forever an (Standard)")
check(near(PL:KillXP(20, 17), 145 * (1 - 3 / 11) * 0.85), "Forever: grün x 0,85 (Schätzung)")
check(PL:KillXP(20, 19) == PL:KillXPFormula(20, 19), "Forever: 1 Level tiefer ohne Abschlag")
check(PL:KillXP(20, 20) == 145, "Forever: gleich hoch ohne Abschlag")
LP.db.forever = false
check(PL:KillXP(20, 17) == PL:KillXPFormula(20, 17), "Classic: grün ohne Forever-Abschlag")
check(PL:DungeonXPFactor() == 1.0 and PL:DungeonQuestFactor() == 1.0, "Classic: Dungeon-Faktoren 1,0")
LP.db.forever = nil
local f, how = PL:DungeonXPFactor()
check(near(f, 0.36) and how == "auto", "Forever: Dungeon-Monster 0,36 (automatisch)")
check(PL:DungeonQuestFactor() == 1.5, "Forever: Dungeon-Quests 1,5")
LP.db.dungeonMobXP = 50
f, how = PL:DungeonXPFactor()
check(f == 0.5 and how == "set", "Einstellung hat Vorrang")
LP.db.dungeonMobXP = 0
-- 3) EP je Kill messen
P.level, P.xp, P.xpMax = 20, 1000, 18000
local tl = 17
UnitExists = function(u) return u == "target" end
UnitIsPlayer = function() return false end
local realLevel = UnitLevel
UnitLevel = function(u) if u == "target" then return tl end return P.level end
GetXPExhaustion = function() return nil end
FireEvent("PLAYER_ENTERING_WORLD") FireEvent("PLAYER_TARGET_CHANGED")
local formula = PL:KillXPFormula(20, 17)
local real = math.floor(formula * 0.8 + 0.5)       -- Forever gibt 80 %
for i = 1, 22 do
    Advance(20)
    FireEvent("PLAYER_TARGET_CHANGED")      -- neuer Gegner angewaehlt
    P.xp = P.xp + real
    if i % 2 == 0 then
        FireEvent("CHAT_MSG_COMBAT_XP_GAIN", "x") FireEvent("PLAYER_XP_UPDATE", "player")   -- Meldung zuerst
    else
        FireEvent("PLAYER_XP_UPDATE", "player") FireEvent("CHAT_MSG_COMBAT_XP_GAIN", "x")   -- EP zuerst
    end
end
local r, n = Ca:KillXPRatio(-3)
check(r and near(r, real / formula, 0.01) and n == 22, string.format("gemessen: %.2f aus %d Kills (Ziel 0,80, beide Reihenfolgen)", r or 0, n or 0))
check(near(PL:KillXP(20, 17), formula * r, 0.5), "Messung ersetzt die Schätzung")
check(Ca:KillXPText():find("gemessen 22", 1, true) and Ca:KillXPText():find("80 %%"), "Statuszeile: " .. Ca:KillXPText())
-- Erholt-Bonus, Gruppe, geschuetztes Ziel: nicht zaehlen
GetXPExhaustion = function() return 5000 end
P.xp = P.xp + real * 2 FireEvent("PLAYER_XP_UPDATE", "player") FireEvent("CHAT_MSG_COMBAT_XP_GAIN", "x")
GetXPExhaustion = function() return nil end
check(select(2, Ca:KillXPRatio(-3)) == 22, "mit Erholt-Bonus: nicht gezählt")
P.group = true
P.xp = P.xp + 10 FireEvent("PLAYER_XP_UPDATE", "player") FireEvent("CHAT_MSG_COMBAT_XP_GAIN", "x")
P.group = false
check(select(2, Ca:KillXPRatio(-3)) == 22, "in der Gruppe: nicht gezählt")
local SECRET = setmetatable({}, { __eq = function() error("secret") end, __lt = function() error("secret") end,
    __le = function() error("secret") end, __concat = function() error("secret") end })
issecretvalue = function(v) return rawequal(v, SECRET) end
UnitLevel = function(u) if u == "target" then return SECRET end return P.level end
local ok = pcall(FireEvent, "PLAYER_TARGET_CHANGED")
P.xp = P.xp + real
local ok2 = pcall(function() FireEvent("PLAYER_XP_UPDATE", "player") FireEvent("CHAT_MSG_COMBAT_XP_GAIN", "x") end)
local chatErr = false
for _, m in ipairs(CHAT) do if m:find("secret") then chatErr = true end end
check(ok and ok2 and not chatErr and select(2, Ca:KillXPRatio(-3)) == 22, "geschütztes Ziel-Level: kein Fehler, nicht gezählt")
issecretvalue = nil
-- Levelaufstieg: alte EP bis zum Maximum dazurechnen
UnitLevel = function(u) if u == "target" then return 20 end return P.level end
FireEvent("PLAYER_TARGET_CHANGED")
P.xp = P.xpMax - 50 FireEvent("PLAYER_XP_UPDATE", "player")
P.level, P.xp = 21, 95                      -- 50 + 95 = 145 = Formel L20
FireEvent("PLAYER_XP_UPDATE", "player") FireEvent("CHAT_MSG_COMBAT_XP_GAIN", "x")
local k0 = LevelPilotDB.calib.killxp[-1]       -- Level 21 gegen Monster 20
check(k0 and k0.n == 1 and near(k0.sum, 145 / PL:KillXPFormula(21, 20), 0.01), "Levelaufstieg: EP richtig zusammengezählt")
P.level = 20 FireEvent("PLAYER_XP_UPDATE", "player")
-- Dungeon getrennt
P.instance = true
UnitLevel = function(u) if u == "target" then return 20 end return P.level end
FireEvent("PLAYER_TARGET_CHANGED")
for i = 1, 21 do P.xp = P.xp + 52 FireEvent("PLAYER_XP_UPDATE", "player") FireEvent("CHAT_MSG_COMBAT_XP_GAIN", "x") end
P.instance = false
local dr = Ca:DungeonXPRatio()
f, how = PL:DungeonXPFactor()
check(dr and near(dr, 52 / 145, 0.01) and how == "measured", string.format("im Dungeon gemessen: %.2f", dr or 0))
check(LevelPilotDB.calib.killxp[0] == nil, "Dungeon-Kills zählen nicht für die Welt")
UnitLevel = realLevel
-- 4) Reise: Werte-Zeile, beide Modi vergleichen, echter Modus bleibt
local mode0 = LP.char.mode
local text
LP.Virtual:CompareModes(function(a, b, t) text = t end, 4)
for _ = 1, 600 do Advance(0.05, 0.05) if text then break end end
check(text and text:find("Normal", 1, true) and text:find("Speedrun", 1, true), "beide Modi verglichen: " .. tostring(text))
check(LP.char.mode == mode0, "echter Modus unverändert (" .. tostring(mode0) .. ")")
local rep = LP.Virtual.lastReport or ""
check(rep:find("Werte: Kills/Min", 1, true), "Bericht nennt die Herkunft der Werte")
check(rep:find("echte Daten unverändert (OK)", 1, true), "Sandbox OK")
for _, m in ipairs(CHAT) do if m:find("attempt") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
