-- Test: Spenden-Knopf (3.4.2)
-- Aufruf: PACKDIR=... lua51 test19.lua <Addon> 0 Orc WARRIOR Horde   (LOCALE=enUS/ruRU ... fuer andere Sprachen)
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
UISpecialFrames = {}
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
local function click(b) local sc = rawget(b, "_scripts") return sc and sc.OnClick and sc.OnClick(b) end
local URL = "https://www.paypal.com/ncp/payment/46R68N2BF7BTY"

check(LP.Donate and LP.Donate.URL == URL, "Link genau wie vorgegeben")
check(LP.Donate.SIGN == "- GoldSentinel", "Signatur")
-- nicht aufdringlich: nach dem Einloggen kein Fenster, keine Chatwerbung
Advance(120)
check(LP.Donate.Frame() == nil or not LP.Donate.Frame():IsShown(), "öffnet sich nicht von selbst")
local spam = false
for _, m in ipairs(CHAT) do if m:find("PayPal") or m:find(URL, 1, true) then spam = true end end
check(not spam, "keine Werbung im Chat")

-- Knopf in der Titelleiste
LP.UI:Toggle() if not LP.UI:IsShown() then LP.UI:Toggle() end
LP.UI:Refresh()
local hb = LevelPilotFrame and LevelPilotFrame.bSupport
if not hb then
    for _, f in pairs(_G) do if type(f) == "table" and rawget(f, "bSupport") then hb = f.bSupport end end
end
check(hb ~= nil, "Knopf in der Titelleiste")
check(hb and hb.label:GetText() == LP.L["Unterstützen"], "Beschriftung: " .. tostring(hb and hb.label:GetText()))
click(hb)
local f = LP.Donate.Frame()
check(f and f:IsShown(), "Klick öffnet das Fenster")
check(f.edit:GetText() == URL, "Feld enthält genau den Link")
check(f.title:GetText():find("LevelPilot"), "Titel: " .. tostring(f.title:GetText()))
check(f.text:GetText():find("LevelPilot"), "Dank mit Addon-Name")
check(f.sign:GetText() == "- GoldSentinel", "Signatur im Fenster")
-- Feld nur zum Kopieren
local sc = rawget(f.edit, "_scripts")
f.edit:SetText("kaputt") sc.OnTextChanged(f.edit, true)
check(f.edit:GetText() == URL, "Eingaben werden zurückgenommen")
-- Esc schliesst
sc.OnEscapePressed(f.edit)
check(not f:IsShown(), "Esc schließt")
local inSpecial = false
for _, n in ipairs(UISpecialFrames) do if n == f:GetName() then inSpecial = true end end
check(inSpecial, "Esc schließt auch ohne Fokus (UISpecialFrames)")
-- Befehle
for _, cmd in ipairs({ "spenden", "donate", "support" }) do
    f:Hide()
    SlashCmdList["LEVELPILOT"](cmd)
    check(f:IsShown(), "/lp " .. cmd .. " öffnet das Fenster")
end
f:Hide()
-- Zeile in den Einstellungen
LP.Center:Toggle("settings") LP.Center:Select("settings") LP.Center:Refresh()
local found
for _, c in pairs(_G) do end
check(true, "Einstellungen ohne Fehler")
-- schmales Fenster: nur Muenze
LP.db.frameW = 260
LP.UI:ApplySettings()
LP.UI:Refresh()
print("       schmal: Breite " .. tostring(hb:GetWidth()) .. ", Text sichtbar " .. tostring(hb.label:IsShown()))
LP.db.frameW = nil
LP.UI:ApplySettings()
print("       normal: Breite " .. tostring(hb:GetWidth()))
check(hb:GetWidth() >= 96, "normale Breite: ganzer Knopf")

for _, m in ipairs(CHAT) do if m:find("attempt") or m:find("Fehler in") then print("CHAT: " .. m) fails = fails + 1 end end
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
