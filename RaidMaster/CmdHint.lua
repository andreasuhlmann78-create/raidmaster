-- ============================================================
-- RaidMaster - CmdHint.lua (ab 3.0.24, Auftrag BL – Wunsch des Nutzers 13.11.2026)
-- Befehlsliste beim Tippen. Baustein aus AHSentinel CmdHint.lua (Punkt CH, 0.65.104) übernommen – gleiches Verhalten,
-- gleiche Setup-Schnittstelle; nur die Anbindung (unten in Commands.lua) ist RaidMaster-eigen.
-- Tippt man im Chat "/rm" oder "/raidmaster", erscheint über dem Eingabefeld die Liste SÄMTLICHER Befehle aus
-- RM.COMMANDS (derselben Tabelle, die der Slash-Handler zum Ausführen benutzt) mit Beschreibung. Weitertippen filtert;
-- meistbenutzte oben (Zähler in RaidMasterDB.config.cmdUse). Mausklick oder Tab WÄHLT, Enter FÜHRT AUS (der Slash-
-- Handler nimmt die frische Auswahl, ≤ 10 s, statt des unvollständigen Worts).
--
-- SICHERHEIT (Taint): Das Chat-Eingabefeld wird NIE beschrieben – kein SetText, kein Insert, kein eigenes
-- OnEnterPressed, keine ersetzte Blizzard-Funktion. Nur HookScript (lesen) und SetFocus.
--
-- Schnittstelle:
--   CmdHint.Setup{ commands = {{de, en, beschreibung, dev = bool}, ...}, prefixes = {"/raidmaster", "/rm"},
--                  run = function(wort) end, store = function() return zähler end, enabled = function() return bool end,
--                  L = übersetzungen, german = function() return bool end, dev = function() return bool end,
--                  noMatch = "…", enterText = "Enter = %s", display = "/rm", global = "RaidMasterCmdHint" }
-- ============================================================
local ADDON, RM = ...

local H = { MAX_ROWS = 10, ROW_H = 18, WIDTH = 440, hooked = {} }
RM.CmdHint = H

local function AnySecret(...)
	local G = _G.GoldSentinelGame
	return G and G.AnySecret and G.AnySecret(...) or false
end

-- ------------------------------------------------------------
-- Logik (ohne Fenster – prüfbar)
-- ------------------------------------------------------------
-- Text des Eingabefelds -> Rest nach dem Befehl ("" = nur "/rm"), nil = kein RaidMaster-Befehl
function H:Match(text)
	if type(text) ~= "string" or AnySecret(text) then return nil end
	local t = text:lower()
	for _, p in ipairs(self.prefixes or {}) do
		if t == p then return "" end
		if t:sub(1, #p + 1) == p .. " " then return (t:sub(#p + 2):gsub("^%s+", "")) end
	end
	return nil
end

local function Words(s)
	local out = {}
	for w in tostring(s or ""):lower():gmatch("%S+") do out[#out + 1] = w end
	return out
end

-- Ausführbares Wort eines Eintrags: ohne Platzhalter ("<Boss>") und ohne Beispielzahlen
local function RunWords(form)
	local out = {}
	for _, w in ipairs(Words(form)) do
		if not w:match("^%d+$") and not w:match("^<") then out[#out + 1] = w end
	end
	return table.concat(out, " ")
end
H.RunWords = RunWords

-- Schlüssel für den Zähler: das deutsche Wort des Eintrags
local function Base(entry) return RunWords(entry[1]) end
H.Base = Base

function H:KeyFor(msg)
	local words = Words(msg)
	if #words == 0 then return nil end
	local best, bestN
	for _, c in ipairs(self.commands or {}) do
		for _, form in ipairs({ c[1], c[2] }) do
			local fw = Words(RunWords(form))
			local n = 0
			for i = 1, math.min(#fw, #words) do
				if fw[i] == words[i] then n = n + 1 else break end
			end
			if #fw > 0 and n >= 1 and (not bestN or n > bestN) then best, bestN = c, n end
		end
	end
	return best and Base(best) or nil
end

function H:Count(msg)
	local key = self:KeyFor(msg)
	if not key or key == "" then return nil end
	local st = self.store and self.store()
	if type(st) ~= "table" then return nil end
	st[key] = (st[key] or 0) + 1
	return key
end

-- Liste für den getippten Rest: { { cmd = "/rm beute <Boss>", run = "beute", text = "…", uses = n, order = i } }
function H:List(rest)
	rest = (rest or ""):lower()
	local german = self.german and self.german()
	local dev = self.dev and self.dev()
	local st = (self.store and self.store()) or {}
	local out = {}
	for i, c in ipairs(self.commands or {}) do
		if c[1] ~= "" and (dev or not c.dev) then
			local hit = rest == "" or c[1]:lower():sub(1, #rest) == rest or c[2]:lower():sub(1, #rest) == rest
			if hit then
				local word = german and c[1] or c[2]
				out[#out + 1] = { cmd = (self.display or (self.prefixes and self.prefixes[1]) or "/rm") .. " " .. word,
					run = RunWords(word), text = (self.L and self.L[c[3]]) or c[3], uses = st[Base(c)] or 0, order = i,
					key = Base(c), entry = c }
			end
		end
	end
	table.sort(out, function(a, b)
		if a.uses ~= b.uses then return a.uses > b.uses end
		return a.order < b.order
	end)
	return out
end

function H:Allowed()
	if self.enabled and not self.enabled() then return false end
	if InCombatLockdown and InCombatLockdown() then return false end
	return true
end

-- ------------------------------------------------------------
-- Fenster
-- ------------------------------------------------------------
function H:EnsureFrame()
	if self.frame then return self.frame end
	local f = CreateFrame("Frame", self.global, UIParent, BackdropTemplateMixin and "BackdropTemplate" or nil)
	f:SetFrameStrata("DIALOG")
	f:SetClampedToScreen(true)
	if f.SetBackdrop then
		f:SetBackdrop({ bgFile = "Interface\\Buttons\\WHITE8X8", edgeFile = "Interface\\Buttons\\WHITE8X8", edgeSize = 1 })
		f:SetBackdropColor(0.06, 0.07, 0.09, 0.95)
		f:SetBackdropBorderColor(1, 0.55, 0.1, 0.8)
	end
	f:EnableMouseWheel(true)
	f:SetScript("OnMouseWheel", function(_, delta)
		H.offset = math.max(0, math.min((H.offset or 0) - delta, math.max(0, #(H.items or {}) - H.MAX_ROWS)))
		H:Draw()
	end)
	f.rows = {}
	for i = 1, self.MAX_ROWS do
		local b = CreateFrame("Button", nil, f)
		b:SetHeight(self.ROW_H)
		b:SetPoint("TOPLEFT", 4, -4 - (i - 1) * self.ROW_H)
		b:SetPoint("TOPRIGHT", -4, -4 - (i - 1) * self.ROW_H)
		local hl = b:CreateTexture(nil, "HIGHLIGHT")
		hl:SetAllPoints()
		hl:SetColorTexture(1, 0.55, 0.1, 0.15)
		b.cmd = b:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
		b.cmd:SetPoint("LEFT", 4, 0)
		b.cmd:SetWidth(170)
		b.cmd:SetJustifyH("LEFT")
		b.desc = b:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
		b.desc:SetPoint("LEFT", b.cmd, "RIGHT", 6, 0)
		b.desc:SetPoint("RIGHT", -4, 0)
		b.desc:SetJustifyH("LEFT")
		if b.desc.SetWordWrap then b.desc:SetWordWrap(false) end
		b.sel = b:CreateTexture(nil, "BACKGROUND")
		b.sel:SetAllPoints()
		b.sel:SetColorTexture(1, 0.55, 0.1, 0.30)
		b.sel:Hide()
		-- Klick = auswählen (nicht ausführen); Enter im Chat führt aus
		b:SetScript("OnClick", function(self) if self.item then H:Select(self.item, true) end end)
		f.rows[i] = b
	end
	f.empty = f:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
	f.empty:SetPoint("TOPLEFT", 8, -6)
	f.head = f:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
	f.head:SetPoint("BOTTOMLEFT", f, "TOPLEFT", 4, 2)
	f.head:SetText("")
	f:Hide()
	self.frame = f
	return f
end

function H:Draw()
	local f = self.frame
	if not f then return end
	local items = self.items or {}
	local n = math.min(#items, self.MAX_ROWS)
	for i, b in ipairs(f.rows) do
		local it = items[i + (self.offset or 0)]
		if i <= n and it then
			b.item = it
			b.cmd:SetText("|cffff8c1a" .. it.cmd .. "|r")
			b.desc:SetText(it.text)
			if self.selected and self.selected.item == it then b.sel:Show() else b.sel:Hide() end
			b:Show()
		else
			b.item = nil
			b:Hide()
		end
	end
	if f.head then
		local s = self:Selection()
		f.head:SetText(s and string.format(self.enterText or "Enter = %s", s.item.cmd) or "")
	end
	if #items == 0 then
		f.empty:SetText(self.noMatch or "")
		f.empty:Show()
		f:SetHeight(self.ROW_H + 8)
	else
		f.empty:Hide()
		f:SetHeight(n * self.ROW_H + 8)
	end
end

function H:Show(editBox, rest)
	local f = self:EnsureFrame()
	self.items = self:List(rest)
	self.offset = 0
	self.editBox = editBox
	self.lastBox = editBox or self.lastBox
	f:ClearAllPoints()
	local w = math.max(self.WIDTH, (editBox and editBox.GetWidth and editBox:GetWidth()) or 0)
	f:SetWidth(w)
	if editBox then f:SetPoint("BOTTOMLEFT", editBox, "TOPLEFT", 0, 2)
	else f:SetPoint("BOTTOM", UIParent, "BOTTOM", 0, 120) end
	self:Draw()
	f:Show()
end

function H:Hide()
	if self.frame then self.frame:Hide() end
	self.editBox = nil
end

-- Auswahl (10 s gültig). Danach den Fokus zurück ins Chatfeld (nur SetFocus, nie SetText/Insert).
H.SELECT_SECONDS = 10
local function Now() return (GetTime and GetTime()) or time() end
function H:Select(item, byMouse)
	if not item then return end
	self.selected = { item = item, t = Now() }
	self.clickAt = byMouse and Now() or self.clickAt
	self:Draw()
	local box = self.editBox or self.lastBox
	if box and box.SetFocus and box.IsShown and box:IsShown() then pcall(box.SetFocus, box) end
end
function H:Selection()
	local s = self.selected
	if s and Now() - s.t <= self.SELECT_SECONDS then return s end
	return nil
end
-- Enter schickt den getippten Text an den Slash-Handler – passt er zum Anfang der frischen Auswahl, gilt die Auswahl
function H:Resolve(msg)
	local s = self:Selection()
	if not s then return msg end
	local typed = tostring(msg or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
	local run = tostring(s.item.run or ""):lower()
	self.selected = nil
	if typed == "" or run:sub(1, #typed) == typed then return s.item.run end
	return msg
end
-- Tab / Pfeiltasten wählen den nächsten Eintrag (nur gelesen über HookScript)
function H:SelectNext(step)
	local items = self.items or {}
	if #items == 0 then return end
	local cur = 0
	local s = self:Selection()
	for i, it in ipairs(items) do if s and s.item == it then cur = i end end
	local nx = ((cur - 1 + (step or 1)) % #items) + 1
	self:Select(items[nx], false)
end
-- Fokusverlust schliesst erst verzögert und nicht, wenn gerade in der Liste geklickt wurde
function H:OnFocusLost(box)
	if self.editBox ~= box then return end
	local function close()
		if self.clickAt and Now() - self.clickAt < 0.5 then return end
		if self.frame and self.frame.IsMouseOver and self.frame:IsShown() and self.frame:IsMouseOver() then return end
		if self.editBox == box then self:Hide() end
	end
	if C_Timer and C_Timer.After and not self.instantClose then C_Timer.After(0.3, close) else close() end
end

-- Eingabefeld hat sich geändert (nur lesen)
function H:OnText(editBox)
	if not self:Allowed() then return self:Hide() end
	local ok, text = pcall(editBox.GetText, editBox)
	if not ok then return self:Hide() end
	local rest = self:Match(text)
	if not rest then return self:Hide() end
	self:Show(editBox, rest)
end

-- ------------------------------------------------------------
-- Einhaken (nur HookScript, nie SetText/Insert/SetScript)
-- ------------------------------------------------------------
function H:HookBox(box)
	if type(box) ~= "table" or not box.HookScript or self.hooked[box] then return end
	self.hooked[box] = true
	box:HookScript("OnTextChanged", function(b) H:OnText(b) end)
	box:HookScript("OnEditFocusLost", function(b) H:OnFocusLost(b) end)
	box:HookScript("OnTabPressed", function(b)
		if H.editBox == b and H.frame and H.frame:IsShown() then H:SelectNext(IsShiftKeyDown and IsShiftKeyDown() and -1 or 1) end
	end)
	box:HookScript("OnArrowPressed", function(b, key)
		if H.editBox == b and H.frame and H.frame:IsShown() and (key == "UP" or key == "DOWN") then
			H:SelectNext(key == "UP" and -1 or 1)
		end
	end)
	box:HookScript("OnHide", function(b) if H.editBox == b then H:Hide() end end)
end

function H:HookAll()
	self.hooked = self.hooked or {}
	for i = 1, (NUM_CHAT_WINDOWS or 10) do self:HookBox(_G["ChatFrame" .. i .. "EditBox"]) end
	self:HookBox(_G.ChatFrameEditBox)            -- sehr alte Clients: ein gemeinsames Eingabefeld
end

function H.Setup(cfg)
	for k, v in pairs(cfg) do H[k] = v end
	local ok = pcall(H.HookAll, H)
	if not H.combatFrame then
		local ev = CreateFrame("Frame")
		ev:RegisterEvent("PLAYER_REGEN_DISABLED")
		ev:SetScript("OnEvent", function() H:Hide() end)
		H.combatFrame = ev
	end
	return ok
end
