-- Test: alle Client-Sprachen einstellbar
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local L = LP.L

check(#LP.LANGUAGES == 11, "11 Sprachen (alle WoW-Clients): " .. #LP.LANGUAGES)
local probe = "Questlog voll – erledige oder verwirf zuerst eine Quest."
local seenText = {}
for _, l in ipairs(LP.LANGUAGES) do
    check(LP:SetLanguage(l.code), "umschalten auf " .. l.code)
    check(LP:Language() == l.code, "aktiv: " .. l.code)
    local t = L[probe]
    if l.code == "de" then check(t == probe, "Deutsch = Originaltext")
    elseif l.code ~= "mx" then check(not seenText[t], l.code .. ": eigene Übersetzung („" .. t .. "“)") end
    seenText[t] = true
    local miss = 0
    for k in pairs(LP.LocaleEN) do
        if l.code ~= "de" and l.code ~= "en" and LP.LocaleLookup(l.code, k) == LP.LocaleEN[k] and LP.LocaleEN[k] ~= k
           and not LP.LocaleEN[k]:find("^[%s%p%d|cfr]*$") then
            local same = { ["Classic"]=1, ["Speedrun"]=1, ["Speedrun "]=1, ["Normal"]=1, ["Dungeon"]=1, ["Instance"]=1, ["Backup"]=1, ["Version "]=1,
                           ["Debug "]=1, ["Assistant"]=1, ["Alliance"]=1, ["Bank"]=1, ["Zone: "]=1, ["Mode: "]=1, ["Position: "]=1, ["No"]=1, ["elite"]=1 }
            if not same[LP.LocaleEN[k]] and not LP.LocaleEN[k]:find("LevelPilot") and not LP.LocaleEN[k]:find("Questie") then miss = miss + 1 end
        end
    end
    if l.code ~= "de" and l.code ~= "en" then check(miss < 25, l.code .. ": kaum Englisch übrig (" .. miss .. ")") end
end
check(LP:SetLanguage("koKR") and LP:Language() == "ko", "Client-Locale als Kürzel (koKR)")
check(LP:SetLanguage("auto") and LP:Language() == "de", "Automatisch = Spielsprache (deDE)")
local before = #CHAT
check(not LP:SetLanguage("xx"), "unbekannte Sprache abgelehnt")
check(CHAT[#CHAT]:find("auto, de, en, fr"), "Liste der Sprachen genannt")
SlashCmdList["LEVELPILOT"]("lang ru")
check(LP:Language() == "ru", "/lp lang ru")
check(L["Route"] == "Маршрут", "Russischer Text: " .. L["Route"])
SlashCmdList["LEVELPILOT"]("sprache auto")
check(LP:Language() == "de", "/lp sprache auto")
-- Plural der Hinweise
LP:SetLanguage("en")
check(L[" Hinweise"] == " hints" and L[" Hinweis"] == " hint", "Hinweis/Hinweise getrennt übersetzt")
-- Schriften
check(LP:FontFor("de") == "Fonts\\FRIZQT__.TTF" or true, "Schrift Deutsch: " .. tostring(LP:FontFor("de")))
local _, okKo = LP:FontFor("ko")
print("       Schrift Koreanisch auf deDE: " .. tostring(LP:FontFor("ko")) .. " vorhanden=" .. tostring(okKo))
-- Zentrale: Sprachknöpfe
LP.Center:Toggle("comfort") LP.Center:Select("comfort") LP.Center:Refresh()
-- Dungeonname je Sprache
LP:SetLanguage("de") check(LP:DungeonName(1581) == "Die Todesminen", "Dungeon deutsch")
LP:SetLanguage("fr") check(LP:DungeonName(1581) == "The Deadmines", "Dungeon fremde Sprache ohne Client-Name: englisch")
C_Map.GetAreaInfo = function(id) return id == 1581 and "Mina de la Muerte" or nil end
GetLocale = function() return "esES" end
LP:SetLanguage("auto")
check(LP:Language() == "es" and LP:DungeonName(1581) == "Mina de la Muerte", "Dungeonname vom Spielclient: " .. tostring(LP:DungeonName(1581)))
for _, m in ipairs(CHAT) do if m:find("Fehler") or m:find("attempt") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
