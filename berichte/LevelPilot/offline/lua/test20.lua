-- Test: Kopf und Statusleiste des Leitfaden-Fensters (3.4.3) – nichts ueberlappt, nichts wird abgeschnitten
-- Aufruf: PACKDIR=... lua51 test20.lua <Addon> 0 Orc WARRIOR Horde
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end

-- Zeilenumbruch nachbilden: ca. 0.55 × Schriftgroesse pro Zeichen
local fsMT = getmetatable(LevelPilotFrame).__index
local function lines(fs)
    local t = tostring(rawget(fs, "_text") or ""):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
    local w = rawget(fs, "_w") or 300
    local size = rawget(fs, "_size") or 10
    local n = 0
    for part in (t .. "\n"):gmatch("(.-)\n") do
        n = n + math.max(1, math.ceil(#part * size * 0.55 / w))
    end
    return n, size
end

LP.UI:Toggle() if not LP.UI:IsShown() then LP.UI:Toggle() end
local f = LevelPilotFrame
-- Schriftgroessen merken (UI:Text setzt sie ueber SetFont)
for _, fs in ipairs({ f.title, f.xtext, f.status.text }) do rawset(fs, "_size", rawget(fs, "_size") or 10) end
local function relayout()
    for _, fs in ipairs({ f.xtext, f.status.text }) do
        fs.GetStringHeight = function(s) local n, size = lines(s) return n * (size + 3) end
    end
    LP.UI:Refresh()
end
relayout()

local function pt(fr) local p = rawget(fr, "_points") or {} return p end
local W = f:GetWidth()
check(f.title:GetWidth() >= W - 24, "Titel nutzt die ganze Breite (" .. f.title:GetWidth() .. " von " .. W .. ")")
-- Titel steht unter den Knoepfen der ersten Zeile (bis y -26) und ueber der zweiten Zeile (ab y -46)
local function y(fr) for _, p in ipairs(pt(fr)) do if type(p[#p]) == "number" then return p[#p] end end return nil end
print("       Titel y=" .. tostring(y(f.title)) .. "  Spenden-Knopf da: " .. tostring(f.bSupport ~= nil))
-- Neu-planen-Knopf: Grafik statt Zeichen
local planLabel
for _, k in pairs(_G) do end
check(not (f.bMode and f.bMode.label:GetText() == "↻"), "kein ↻-Zeichen mehr")
-- lange EP-Zeile umbrechen
LP.Comfort.TimerText = function() return "Sitzung 1h 23min · 4.2k EP/h · 12g 34s/h · nächstes Level ca. 47 min" end
LP.db.frameW = 260 LP.UI:ApplySettings() relayout()
local xl = lines(f.xtext)
print("       schmal: EP-Zeile " .. xl .. " Zeile(n), Kopf " .. tostring(f.body and pt(f.body)[1] and pt(f.body)[1][#pt(f.body)[1]]))
check(xl >= 2, "lange EP-Zeile wird umgebrochen")
local bodyY = pt(f.body)[1] and pt(f.body)[1][#pt(f.body)[1]]
check(bodyY and bodyY <= -(70 + xl * 12), "Schritte beginnen unter der EP-Zeile (" .. tostring(bodyY) .. ")")
-- Statusleiste mit langem Text
local st = f.status
local sl = lines(st.text)
print("       Statuszeile: " .. sl .. " Zeile(n), Höhe " .. st:GetHeight())
check(st:GetHeight() >= sl * 13, "Statusleiste wächst mit dem Text")
check(st.text:GetWidth() <= f:GetWidth() - 30, "Platz für den Größen-Griff")
LP.db.frameW = nil LP.UI:ApplySettings() relayout()
check(true, "normale Breite ohne Fehler")
for _, m in ipairs(CHAT) do if m:find("attempt") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
