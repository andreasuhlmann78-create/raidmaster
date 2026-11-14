-- Test: Sprachwechsel ohne /reload, hin und zurueck (3.4.5)
-- Aufruf: PACKDIR=... lua51 test22.lua <Addon> 0 Orc WARRIOR Horde
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local TABS = { "route", "dungeons", "data", "share", "assist", "comfort", "extras", "settings" }
local function openAll()
    LP.UI:Toggle() if not LP.UI:IsShown() then LP.UI:Toggle() end
    LP.UI:Refresh()
    for _, t in ipairs(TABS) do LP.Center:Toggle(t) LP.Center:Select(t) LP.Center:Refresh() end
end
-- feste Texte: alles, was beim Aufbau gesetzt wurde (Momentaufnahme)
local function snapshot()
    local s, tips = {}, {}
    for fs in pairs(LP.UI.texts) do s[fs] = fs:GetText() end
    for b in pairs(LP.UI.buttons) do tips[b] = b.tip end
    return s, tips
end
openAll()
local de, deTips = snapshot()
-- Texte, die sich von selbst aendern (Zeit, Status, Hinweise), nicht vergleichen
Advance(5) openAll()
local again, againTips = snapshot()
for fs, t in pairs(de) do if again[fs] ~= t then de[fs] = nil end end
for b, t in pairs(deTips) do if againTips[b] ~= t then deTips[b] = nil end end
local n = 0 for _ in pairs(de) do n = n + 1 end
print("       Texte im Fenster: " .. n)
local function compare(ref, refTips, label)
    local bad, shown = 0, 0
    local cur, curTips = snapshot()
    for fs, t in pairs(ref) do
        if cur[fs] ~= t then
            bad = bad + 1
            if shown < 8 then shown = shown + 1 print("         " .. label .. ": „" .. tostring(t):gsub("\n", " / "):sub(1, 70) .. "“ -> „" .. tostring(cur[fs]):gsub("\n", " / "):sub(1, 70) .. "“") end
        end
    end
    local tbad = 0
    for b, t in pairs(refTips) do if curTips[b] ~= t then tbad = tbad + 1 end end
    return bad, tbad
end

for _, lang in ipairs({ "es", "mx", "en", "fr", "ru", "ko", "cn" }) do
    LP:SetLanguage(lang)
    openAll()
    -- noch deutsche Texte?
    local german = 0
    for fs in pairs(LP.UI.texts) do
        local t = fs:GetText()
        if type(t) == "string" and t ~= "" and de[fs] == t then
            -- unveraendert: nur ok, wenn die Uebersetzung gleich lautet (z. B. "Dungeons", Zahlen)
            local rev = t
            if LP.LocaleLookup(lang, t) ~= t and t:find("%a%a%a") then german = german + 1 if german <= 5 then print("         noch deutsch (" .. lang .. "): " .. t:gsub("\n", " / "):sub(1, 80)) end end
        end
    end
    check(german == 0, lang .. ": keine deutschen Beschriftungen mehr (" .. german .. ")")
    LP:SetLanguage(os.getenv("BACK") or "de")
    openAll()
    local bad, tbad = compare(de, deTips, "zurück von " .. lang)
    check(bad == 0 and tbad == 0, "zurück auf Deutsch von " .. lang .. ": alles wie vorher (" .. bad .. " Texte, " .. tbad .. " Tooltips anders)")
end
-- Kette ohne Zwischenstopp: es -> fr -> ru -> de
LP:SetLanguage("es") openAll() LP:SetLanguage("fr") openAll() LP:SetLanguage("ru") openAll() LP:SetLanguage(os.getenv("BACK") or "de") openAll()
local bad, tbad = compare(de, deTips, "Kette")
check(bad == 0 and tbad == 0, "Kette es » fr » ru » de: alles wie vorher (" .. bad .. "/" .. tbad .. ")")
-- automatisch (Spielsprache) wieder
LP:SetLanguage("auto") openAll()
local bad2 = compare(de, deTips, "auto")
check(bad2 == 0, "„Automatisch“ auf deutschem Spiel = Deutsch")
for _, m in ipairs(CHAT) do if m:find("attempt") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
