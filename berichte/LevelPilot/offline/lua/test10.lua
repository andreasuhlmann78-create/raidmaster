-- Test: Datensicherung (Zweitkopie im Charakter, Wiederherstellung, Text sichern/laden)
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local B = LP.Backup
local SETTINGS = {}
for k, v in pairs(LevelPilotDB) do if type(v) ~= "table" then SETTINGS[k] = v end end
local function WithSettings(t) return setmetatable(t, { __index = SETTINGS }) end

-- Testdaten anlegen
for i = 1, 50 do LP.db.qdb[900000 + i] = { n = "Forever-Quest " .. i, l = 10, s = { 1429, 40 + i % 10, 50, "NPC" } } end
LP.db.vendors["Händler|A"] = { name = "Händler|A", map = 1429, x = 41, y = 65, repair = true }
LP.db.taxi["Flug"] = { name = "Flug", map = 1429, x = 50, y = 50 }
local pts = {}
for i = 0, 20 do local inst, n, w = LP.Geo:ToWorld(1429, 40 + i * 0.5, 60) pts[#pts + 1] = { inst, n, w, 1429 } end
LP.Graph:AddPolyline(pts, "r")
local before = B:Count(LP.db)
check(before >= 60, "Testdaten: " .. B.Describe(LP.db))

-- Zweitkopie
B:SaveCopy()
check(LP.char.backup and LP.char.backup.count == before, "Kopie im Charakter angelegt (" .. tostring(LP.char.backup and LP.char.backup.count) .. ")")

-- nie durch einen viel kleineren Stand ersetzen
local realQdb = LP.db.qdb
LP.db.qdb = {}
B:SaveCopy()
check(LP.char.backup.count == before, "kleinerer Stand ersetzt die Kopie nicht")
LP.db.qdb = realQdb

-- Ausloggen simulieren: WoW schreibt beide Dateien getrennt (hier: tiefe Kopie)
local function copy(v) if type(v) ~= "table" then return v end local t = {} for k, x in pairs(v) do t[k] = copy(x) end return t end
local charFile = copy(LevelPilotCharDB)

-- Fall 1: Account-Datei verloren (neu installiert)
LevelPilotDB = { qdb = {}, vendors = {}, taxi = {}, graph = {} }
LevelPilotCharDB = copy(charFile)
B.restored = nil
B:CheckOnLoad()
check(B:Count(LevelPilotDB) >= before, "verlorene Accountdaten wiederhergestellt: " .. B.Describe(LevelPilotDB))
check(LevelPilotDB.qdb[900007] and LevelPilotDB.qdb[900007].n == "Forever-Quest 7", "Questdaten inhaltlich korrekt")
check(B.restored and not B.restored.small, "Meldung über Wiederherstellung vorgesehen")

-- Fall 2: Account-Datei beschaedigt (WoW laedt sie nicht -> nil)
LevelPilotDB = nil
LevelPilotCharDB = copy(charFile)
LevelPilotDB = { qdb = {}, vendors = {}, taxi = {} }  -- so legt das Addon sie neu an
B:CheckOnLoad()
check(B:Count(LevelPilotDB) >= before, "beschädigte Accountdaten wiederhergestellt")

-- Fall 3: Account hat neue Daten, Kopie hat noch andere -> zusammenfuehren, nichts verlieren
LevelPilotDB = copy(charFile.backup.data)
for i = 1, 5 do LevelPilotDB.qdb[910000 + i] = { n = "Neu " .. i } end      -- neuer als die Kopie
LevelPilotDB.qdb[900001] = nil                                                -- fehlt im Account
local cf = copy(charFile)
LevelPilotCharDB = cf
B:CheckOnLoad()
check(LevelPilotDB.qdb[900001] and LevelPilotDB.qdb[910003], "neue und alte Einträge bleiben beide erhalten")

-- Text sichern / laden
LevelPilotDB = WithSettings(copy(charFile.backup.data))
LP.db = LevelPilotDB
LP.Graph:Init()
local text = B:Export()
check(text:match("^LP1:%x+:") and not text:find("|", 1, true) and not text:find("\n", 1, true), "Sicherungstext ohne Zeichen, die WoW verändern würde (" .. #text .. " Zeichen)")
-- auf "anderem PC" laden: leere Daten
LevelPilotDB = WithSettings({ qdb = {}, vendors = {}, taxi = {}, graph = {} })
LP.db = LevelPilotDB
LP.Graph:Init()
local ok, msg = B:Import(text)
check(ok, "Laden: " .. tostring(msg))
check(B:Count(LP.db) >= before - 2, "alle Daten nach dem Laden da: " .. B.Describe(LP.db))
check(LP.db.vendors["Händler|A"] and LP.db.vendors["Händler|A"].repair == true, "Sonderzeichen und Wahrheitswerte korrekt")
-- doppelt laden fuegt nichts doppelt hinzu
local n1 = B:Count(LP.db)
B:Import(text)
check(B:Count(LP.db) == n1, "zweimal laden erzeugt keine Doppelten (" .. n1 .. " / " .. B:Count(LP.db) .. ")")
-- beschaedigter Text wird abgelehnt und aendert nichts
local bad = text:sub(1, #text - 40)
local ok2, msg2 = B:Import(bad)
check(not ok2 and B:Count(LP.db) == n1, "unvollständiger Text wird abgelehnt: " .. tostring(msg2))
local ok3 = B:Import("return os.exit()")
check(not ok3, "fremder Text wird nicht ausgeführt")

-- Anzeige
LP.Center:Toggle("data") LP.Center:Select("data") LP.Center:Refresh()
local okUI = pcall(function() B:ShowExport() B:ShowImport() end)
check(okUI, "Fenster für Sichern/Laden öffnen sich")
print("       " .. B:Info())

for _, m in ipairs(CHAT) do if (m:find("Fehler") and not m:find("Letzter Fehler: keiner")) or m:find("konnte nicht") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
