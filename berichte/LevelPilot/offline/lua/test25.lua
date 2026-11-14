-- Test: nur lesbare Sprachen in der Auswahl (3.5.3)
-- Aufruf: [CJK=1] LOCALE=.. PACKDIR=... lua51 test25.lua <Addon> 0 Orc WARRIOR Horde
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
if os.getenv("CJK") == "1" then MOCK_FONTS = { ["Fonts\\2002.TTF"] = true, ["Fonts\\ARKai_T.ttf"] = true, ["Fonts\\bLEI00D.ttf"] = true } end
if os.getenv("PRESET") then LevelPilotDB = { language = os.getenv("PRESET") } end
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local shown = {}
for _, l in ipairs(LP.LANGUAGES) do if LP:CanDisplay(l.code) then shown[#shown + 1] = l.code end end
print("       lesbar: " .. table.concat(shown, " "))
local cjk = os.getenv("CJK") == "1"
local client = LP:ClientLanguage()
for _, c in ipairs({ "ko", "cn", "tw" }) do
    if c ~= client then check(LP:CanDisplay(c) == cjk, c .. (cjk and " lesbar (Schrift da)" or " ausgeblendet (Schrift fehlt)")) end
end
for _, c in ipairs({ "de", "en", "fr", "es", "mx", "pt", "it", "ru" }) do check(LP:CanDisplay(c), c .. " lesbar") end
check(LP:CanDisplay(client), "Sprache des Spiels immer lesbar")
-- Auswahl in der Zentrale
LP.Center:Toggle("comfort") LP.Center:Select("comfort") LP.Center:Refresh()
local labels = {}
for b in pairs(LP.UI.buttons) do local t = b.label and b.label:GetText() if t then labels[t] = true end end
if not cjk and client ~= "ko" then check(not labels["한국어"], "kein Knopf für Koreanisch") end
if not cjk and client ~= "cn" then check(not labels["简体中文"], "kein Knopf für Chinesisch (vereinfacht)") end
check(labels["Русский"] and labels["Français"], "lesbare Sprachen haben ihren Knopf")
-- Befehl verweigert
if not cjk and client ~= "tw" then
    CHAT = {}
    check(LP:SetLanguage("tw") == false and LP:Language() ~= "tw", "/lp lang tw wird abgelehnt")
    local said = false for _, m in ipairs(CHAT) do if m:find("Schrift") or m:find("font") then said = true end end
    check(said, "mit Begründung im Chat")
end
if os.getenv("PRESET") then check(LP:Language() ~= os.getenv("PRESET") or cjk, "gespeicherte unlesbare Sprache → Automatisch (" .. LP:Language() .. ")") end
for _, m in ipairs(CHAT) do if m:find("attempt") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
