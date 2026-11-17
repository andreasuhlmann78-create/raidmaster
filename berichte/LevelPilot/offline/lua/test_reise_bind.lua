-- 3.12.90 (Ingametest 3.12.89 T83/T85): virtuelle Reise "ab hier" mit gesetztem Bindeort (LP.char.bind ist eine Tabelle).
-- 3.12.89 brach beim Einrichten ab ("Virtual.lua:135 indexed assignment on field '?' (a boolean value)"), richtete im zweiten
-- Anlauf nochmals ein und merkte sich dabei die schon umgeleiteten Funktionen als echt -> nach der Reise blieb alles umgeleitet.
-- Prüft: 1. kein Fehler in der Reise, Schritte > 0  2. alle Umleitungen zurück (API.Quests …, LP.char)  3. Sandbox meldet nichts
-- 4. Abbruch mitten in der Reise: ebenfalls alles zurück. Gegenprobe: 3.12.89 schlägt bei 1 fehl.
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
PRE_RUN = function(LP)
  local V, API, Geo = LP.Virtual, LP.API, LP.Geo
  local fails = 0
  local function check(ok, text) print((ok and "OK   " or "[FEHLER] ") .. text) if not ok then fails = fails + 1 end end
  LP.char.bind = { map = 1411, x = 52, y = 41, name = "Testort" }
  local orig = { API.Quests, API.Objectives, API.IsQuestDone, Geo.Player, API.HearthReady }
  local function back()
    local left = {}
    for i, n in ipairs({ "API.Quests", "API.Objectives", "API.IsQuestDone", "Geo.Player", "API.HearthReady" }) do
      local cur = ({ API.Quests, API.Objectives, API.IsQuestDone, Geo.Player, API.HearthReady })[i]
      if cur ~= orig[i] then left[#left + 1] = n end
    end
    if LP.char ~= LevelPilotCharDB then left[#left + 1] = "LP.char" end
    return left
  end
  local okRun, err = pcall(V.RunAll, V, "here", (LP:PlayerLevel() or 10) + 1)
  local errs = 0
  for _, p in ipairs(V.s and V.s.problems or {}) do
    if tostring(p.text or ""):find("Fehler in der Reise", 1, true) then errs = errs + 1 end
  end
  check(okRun and errs == 0 and (V.s.steps or 0) > 0, ("Reise ab hier mit Bindeort: läuft (%s), Fehler in der Reise %d, Schritte %d %s")
    :format(tostring(okRun), errs, V.s and V.s.steps or 0, okRun and "" or tostring(err)))
  local left = back()
  check(#left == 0, "nach der Reise alles zurück: " .. (#left == 0 and "ja" or table.concat(left, ", ")))
  check(type(V.s.sandboxDiff) == "table" and #V.s.sandboxDiff == 0, "Sandbox ohne Befund: " .. table.concat(V.s.sandboxDiff or { "?" }, "; "))
  -- Abbruch mitten in der Reise
  V:Start("here", { silent = true, maxLevel = (LP:PlayerLevel() or 10) + 2 })
  if V.active then
    for _ = 1, 3 do if TICKERS then for _, t in ipairs(TICKERS) do pcall(t.fn) end end end
    V:Abort()
  end
  left = back()
  check(#left == 0 and V.lastLeft == nil, "nach Abbruch alles zurück: " .. (#left == 0 and "ja" or table.concat(left, ", ")))
  print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
  os.exit(fails == 0 and 0 or 1)
end
dofile(dir .. "/test40.lua")
