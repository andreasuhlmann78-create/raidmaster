dofile("./mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local f = LevelPilotFrame
local function sc(frame, ev, ...) local t = rawget(frame, "_scripts") return t and t[ev] and t[ev](frame, ...) end
local function visibleRows()
    local n = 0
    for _, r in ipairs({ f.body }) do end
    local count = 0
    -- Zeilen sind Kinder von body; wir zaehlen ueber UI-internes Verhalten: sichtbare Zeilen mit Schritt
    return count
end
for _, m in ipairs(CHAT) do if m:find("Fehler") or m:find("konnte nicht") then print("CHAT: " .. m) fails = fails + 1 end end
LP.Planner:Replan()
LP.UI:Refresh()
local autoH = f:GetHeight()
check(f:GetWidth() == 350, "Standardbreite 350 (" .. f:GetWidth() .. ")")
-- Ziehen am Griff: breiter und hoeher
local g = f.grip
sc(g, "OnMouseDown", "LeftButton")
f:SetWidth(520) f:SetHeight(600)
sc(f, "OnSizeChanged")
sc(g, "OnMouseUp")
check(LP.db.frameW == 520 and LP.db.frameH == 600, "Grösse gespeichert: " .. tostring(LP.db.frameW) .. " x " .. tostring(LP.db.frameH))
LP.UI:Refresh()
check(f:GetWidth() == 520 and f:GetHeight() == 600, "Fenster behält Grösse nach Aktualisierung (" .. f:GetWidth() .. " x " .. f:GetHeight() .. ")")
check(rawget(f.title, "_w") == 496, "Titelbreite passt sich an (" .. tostring(rawget(f.title, "_w")) .. ")")
-- kleiner ziehen
sc(g, "OnMouseDown", "LeftButton")
f:SetWidth(280) f:SetHeight(150)
sc(f, "OnSizeChanged")
sc(g, "OnMouseUp")
LP.UI:Refresh()
check(f:GetHeight() == 150, "kleine feste Höhe bleibt (" .. f:GetHeight() .. ")")
-- Doppelklick: zurueck auf automatisch
sc(g, "OnDoubleClick")
check(LP.db.frameW == nil and LP.db.frameH == nil and f:GetWidth() == 350, "Doppelklick setzt zurück")
check(math.abs(f:GetHeight() - autoH) < 1, "automatische Höhe wieder aktiv (" .. f:GetHeight() .. " / " .. autoH .. ")")
-- Strg + Mausrad
CTRL = true
sc(f, "OnMouseWheel", 1) sc(f, "OnMouseWheel", 1)
check(LP.db.scale == 1.1, "Strg+Mausrad vergrössert (" .. LP.db.scale .. ")")
CTRL = false
sc(f, "OnMouseWheel", 1)
check(LP.db.scale == 1.1, "ohne Strg keine Änderung")
-- eingeklappt ignoriert feste Hoehe
LP.db.frameH = 600
LP.char.collapsed = true
LP.UI:ApplySettings()
check(f:GetHeight() < 200, "eingeklappt: nur eine Zeile (" .. f:GetHeight() .. ")")
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
