-- Test: kein Sprachgemisch im Fenster (3.5.2) – deutsches Spiel, jede andere Sprache eingestellt
-- Aufruf: PACKDIR=... NAMESDIR=... FOREVER=1 LVL=12 MAP=1413 PX=51.5 PY=30.3 lua51 test24.lua <Addon> 0 Orc WARRIOR Horde
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
local NAMESDIR = os.getenv("NAMESDIR")
local function load(name)
    local f = loadfile(NAMESDIR .. "/" .. name .. "/Names.lua")
    if not f then return false, "MISSING" end
    f(name, {}) return true
end
C_AddOns = { LoadAddOn = load }
dofile(dir .. "/mock2.lua")
C_AddOns.LoadAddOn = load
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
-- Questlog wie auf dem Bildschirmfoto: deutsche Titel und Ziele vom Spiel
LOG[#LOG + 1] = { title = "Die Ebenenschreiterbedrohung", id = 844, level = 12, complete = false,
                  objs = { { "Ebenenschreiter-Schnabel: 3/7", false, type = "item" } } }
FireAccepted(#LOG, 844)
LOG[#LOG + 1] = { title = "Zähne zeigen", id = 788, level = 5, complete = false,
                  objs = { { "Scheckiger Eber getötet: 2/10", false, type = "monster" } } }
FireAccepted(#LOG, 788)
Advance(3)
local TABS = { "route", "dungeons", "data", "share", "assist", "comfort", "extras", "settings" }
local function openAll()
    LP.UI:Toggle() if not LP.UI:IsShown() then LP.UI:Toggle() end
    LP.Planner:Replan() LP.UI:Refresh()
    for _, t in ipairs(TABS) do LP.Center:Toggle(t) LP.Center:Select(t) LP.Center:Refresh() end
end
-- deutsche Merkmale (Woerter, die in keiner anderen Sprache so vorkommen)
local GERMAN = { "ä", "ö", "ü", "ß", "getötet", "Ebenenschreiter", "Scheckig", " der ", " und ", "Brachland", "Zähne",
                 "Questlog", "Erledigen", "Annehmen", "Abgeben" }
for _, lang in ipairs({ "fr", "en", "es", "ru", "ko", "cn", "pt" }) do
    LP:SetLanguage(lang)
    openAll()
    local bad = {}
    local all = {}
    for fs in pairs(LP.UI.texts) do
        local t = fs:GetText()
        if type(t) == "string" and t ~= "" then all[#all + 1] = t end
    end
    -- Schritte im Leitfaden
    for _, s in ipairs(LP.Engine:Steps()) do all[#all + 1] = LP.UI:StepText(s, true) end
    for _, t in ipairs(all) do
        local plain = t:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
        for _, w in ipairs(GERMAN) do
            -- Eigennamen aus dem Spiel ohne Uebersetzung duerfen bleiben (z. B. Flugpunkte), Sprachnamen auch
            if plain:find(w, 1, true) and not plain:find("Deutsch", 1, true) then bad[#bad + 1] = plain:gsub("\n", " / "):sub(1, 110) break end
        end
        if lang == "ru" and plain:find("·", 1, true) then bad[#bad + 1] = "· in: " .. plain:sub(1, 80) end
    end
    if os.getenv("SHOW") == lang then for _, s in ipairs(LP.Engine:Steps()) do print("       > " .. LP.UI:StepText(s, true):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("\n", " / ")) end print("       > " .. LevelPilotFrame.xtext:GetText()) end
    for i = 1, math.min(6, #bad) do print("         " .. lang .. ": " .. bad[i]) end
    check(#bad == 0, lang .. ": nichts Deutsches mehr im Fenster (" .. #bad .. ")")
end
-- Russisch: Mittelpunkt ersetzt
LP:SetLanguage("ru") openAll()
check(not LevelPilotFrame.xtext:GetText():find("·", 1, true), "Russisch: kein „·“ (fehlt in der Schrift)")
-- Sprachpaket fehlt: klare Meldung
C_AddOns.LoadAddOn = function() return false, "MISSING" end
LevelPilotNames.ptBR = nil
CHAT = {}
LP.Names.status.ptBR = nil
LP:SetLanguage("pt")
local msg = false for _, m in ipairs(CHAT) do if m:find("ptBR") then msg = true end end
check(true, "fehlendes Paket ohne Fehler")
local diag = table.concat(LP.Planner:DiagLines(), "\n")
check(diag:find("ptBR"), "Diagnose zeigt die Sprachpakete")
for _, m in ipairs(CHAT) do if m:find("attempt") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
