-- ============================================================
-- RaidMaster - Donate.lua – Spenden-Knopf (PayPal) von GoldSentinel
-- Funktioniert in jeder WoW-Version (Retail, Classic, Anniversary, Era, WoW Forever),
-- ohne fremde Bibliotheken. WoW kann keine Webseiten öffnen: das Fenster zeigt den
-- Link markiert zum Kopieren (Strg+C), dann im Browser einfügen.
-- Nicht aufdringlich: öffnet sich nur per Klick („Unterstützen“) oder /rm spenden.
--
-- Nutzung:
--   RM.Donate.Show()                              Fenster öffnen
--   RM.Donate.CreateButton(parent, breite, höhe)  Knopf „Unterstützen“ (öffnet das Fenster)
-- Aussehen kommt aus RM.UI (wird erst beim ersten Öffnen gebraucht, deshalb darf diese Datei
-- vor UI.lua geladen werden). Texte über L[...] in Locales\*.lua.
-- ============================================================

local ADDON_NAME, ns = ...
ns = ns or {}
local L = ns.L or setmetatable({}, { __index = function(_, k) return k end })
local D = {}
ns.Donate = D

D.URL = "https://www.paypal.com/ncp/payment/46R68N2BF7BTY"
D.SIGN = "- GoldSentinel"
D.NAME = "RaidMaster"
D.ICON = "Interface\\Icons\\Spell_Fire_Incinerate"   -- dasselbe Symbol wie oben im RaidMaster-Fenster

-- die vier Texte (deutsche Schlüssel, Übersetzungen in Locales\*.lua; %s = Name des Addons)
local KEYS = {
	title = "%s unterstützen",
	button = "Unterstützen",
	thanks = "Danke, dass du %s unterstützt! Jede Spende hilft mir, mehr Zeit in neue Funktionen und schnelle Fehlerbehebungen zu stecken.",
	hint = "Strg+C kopiert den PayPal-Link - dann im Browser einfügen.",
}
local function T(key) return L[KEYS[key]] end
D.Text = T

local frame

local function Build()
	local UI = ns.UI
	local C = UI.COLORS
	local f = UI.Frame(UIParent, 470, 220)
	f:SetFrameStrata("DIALOG")
	f:SetToplevel(true)
	f:SetClampedToScreen(true)
	UI.Skin(f)
	UI.MakeMovable(f, "donate", "CENTER", 0, 60)
	_G["RaidMasterDonate"] = f
	if UISpecialFrames then tinsert(UISpecialFrames, "RaidMasterDonate") end   -- Esc schließt

	f.title = UI.Text(f, "", 15, C.accent[1], C.accent[2], C.accent[3], "CENTER")
	f.title:SetPoint("TOP", 0, -14)
	f.title:SetWordWrap(false)

	local close = UI.CloseButton(f, function() f:Hide() end)
	close:SetPoint("TOPRIGHT", -6, -6)
	f.close = close

	local icon = f:CreateTexture(nil, "ARTWORK")
	icon:SetSize(36, 36)
	icon:SetPoint("TOPLEFT", 22, -46)
	icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	f.icon = icon

	f.text = UI.Text(f, "", 12)
	f.text:SetPoint("TOPLEFT", icon, "TOPRIGHT", 12, 0)
	f.text:SetPoint("RIGHT", f, "RIGHT", -22, 0)

	local eb = UI.EditBox(f, 426, 26)
	eb:SetPoint("TOPLEFT", 22, -126)
	-- nur zum Kopieren: Änderungen sofort zurücknehmen
	eb:SetScript("OnTextChanged", function(self, user)
		if user and self:GetText() ~= D.URL then self:SetText(D.URL); self:HighlightText() end
	end)
	eb:SetScript("OnEditFocusGained", function(self)
		self:SetBackdropBorderColor(C.accent[1], C.accent[2], C.accent[3], 1)
		self:HighlightText()
	end)
	eb:SetScript("OnEscapePressed", function() f:Hide() end)
	eb:SetScript("OnEnterPressed", function() f:Hide() end)
	f.edit = eb

	f.hint = UI.Text(f, "", 11, unpack(C.muted))
	f.hint:SetPoint("TOPLEFT", eb, "BOTTOMLEFT", 2, -8)
	f.hint:SetPoint("RIGHT", f, "RIGHT", -22, 0)

	f.sign = UI.Text(f, D.SIGN, 12, C.accent[1], C.accent[2], C.accent[3], "RIGHT")
	f.sign:SetPoint("BOTTOMRIGHT", -22, 16)
	f:Hide()
	return f
end

function D.Show()
	frame = frame or Build()
	frame.title:SetText(string.format(T("title"), D.NAME))
	frame.text:SetText(string.format(T("thanks"), D.NAME))
	frame.hint:SetText(T("hint"))
	frame.icon:SetTexture(D.ICON or "Interface\\Icons\\INV_Misc_Coin_01")
	frame:Show()
	frame.edit:SetText(D.URL)
	frame.edit:SetFocus()
	frame.edit:HighlightText()
	return frame
end

function D.Hide()
	if frame then frame:Hide() end
end

function D.Toggle()
	if frame and frame:IsShown() then frame:Hide() else D.Show() end
end

function D.Frame() return frame end

-- Knopf „Unterstützen“ für Titelleiste, Einstellungen o. Ä. (im RaidMaster-Design)
function D.CreateButton(parent, width, height)
	local b = ns.UI.Button(parent, T("button"), width or 100, height or 22, function() D.Show() end,
		string.format(T("title"), D.NAME) .. "\nPayPal")
	return b
end
