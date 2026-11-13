-- ============================================================
-- GoldSentinelCmdHint.lua – gemeinsame Befehlsliste beim Tippen (alle GoldSentinel-Addons)
-- Version 1 (13.11.2026) · gebaut von der Prüf-Sitzung aus AHSentinel/CmdHint.lua (0.65.119) · nur unverändert kopieren
--
-- Tippt man im Chat den Befehl eines Addons (z. B. "/ahs", "/lp"), erscheint über dem Eingabefeld eine Liste seiner
-- Befehle mit Beschreibung. Weitertippen filtert, meistbenutzte oben (Zähler je Befehlswort im Speicher des Addons).
-- Mausklick WÄHLT einen Eintrag, Tab wählt den nächsten (Shift+Tab den vorigen), Enter führt aus: Der Slash-Handler
-- des Addons ruft h:Resolve(msg) und bekommt die frische Auswahl statt des unvollständigen Worts.
--
-- EINE Liste und EIN Satz Hooks für alle Addons: Jedes Addon meldet sich mit Register an; die gemeinsame Datei
-- entscheidet anhand des getippten Präfixes, welches Addon gemeint ist (längster Präfix gewinnt). Die neueste
-- geladene Fassung übernimmt die Anmeldungen der älteren (wie GoldSentinelMarkt).
--
-- SICHERHEIT (Taint): Das Chat-Eingabefeld wird NIE beschrieben – kein SetText, kein Insert, kein SetScript, keine
-- ersetzte Blizzard-Funktion. Nur HookScript (lesen): OnTextChanged, OnEditFocusLost, OnTabPressed, OnHide.
-- Im Kampf keine Liste. Geheime Werte (GoldSentinelGame.AnySecret) werden nie gelesen.
--
-- Anbindung im Addon (Beispiel):
--   local h = GoldSentinelCmdHint.Register({
--       id = "AHSentinel",                                   -- eindeutig, Pflicht
--       prefixes = { "/ahsentinel", "/ahs" },                -- alle Slash-Befehle des Addons, Pflicht
--       display = "/ahs",                                    -- so wird der Befehl in der Liste gezeigt (sonst prefixes[1])
--       commands = { { "hilfe", "help", "Hilfe anzeigen" }, { "test daten", "test data", "…", dev = true }, … },
--       store = function() return MyDB.cmdUse end,           -- Tabelle für die Zähler (oder nil)
--       enabled = function() return MyDB.cmdHint ~= false end,
--       L = L,                                               -- Übersetzungen für die Beschreibung (Spalte 3)
--       german = function() return GetLocale() == "deDE" end,-- deutsches (Spalte 1) oder englisches Wort (Spalte 2)
--       dev = function() return false end,                   -- Entwickler-Befehle (dev = true oder "test…") zeigen
--       noMatch = L["Kein Befehl – /ahs hilfe"], enterText = L["Enter = %s"],
--   })
--   Im eigenen Slash-Handler (nie in einer Blizzard-Funktion):
--       msg = h:Resolve(msg); h:Count(msg)
-- ============================================================

local VERSION = 1

local old = _G.GoldSentinelCmdHint
if type(old) == "table" and (tonumber(old.VERSION) or 0) >= VERSION then return end

local CH = { VERSION = VERSION, MAX_ROWS = 10, ROW_H = 18, WIDTH = 420, SELECT_SECONDS = 10 }
CH.addons = {}          -- id -> Anmeldung (Handle)
CH.order = {}           -- ids in Anmelde-Reihenfolge
CH.hooked = {}          -- Eingabefelder mit Hooks (nur einmal je Feld, für alle Addons)

local function AnySecret(...)
    local G = _G.GoldSentinelGame
    return G and G.AnySecret and G.AnySecret(...) or false
end
local function Now() return (_G.GetTime and _G.GetTime()) or (_G.time and _G.time()) or 0 end

local function Words(s)
    local out = {}
    for w in tostring(s or ""):lower():gmatch("%S+") do out[#out + 1] = w end
    return out
end
local function BaseOf(form)
    local out = {}
    for _, w in ipairs(Words(form)) do if not w:match("^%d+$") then out[#out + 1] = w end end
    return table.concat(out, " ")
end
CH.Words, CH.BaseOf = Words, BaseOf

-- ------------------------------------------------------------
-- Handle je Addon (Logik ohne Fenster – prüfbar)
-- ------------------------------------------------------------
local Handle = {}
Handle.__index = Handle

-- Text des Eingabefelds -> Rest nach dem Befehl ("" = nur der Befehl), nil = nicht dieses Addon.
-- Liefert zusätzlich die Länge des passenden Präfixes (längster gewinnt über alle Addons).
function Handle:Match(text)
    if type(text) ~= "string" or AnySecret(text) then return nil end
    local t = text:lower()
    local best, bestLen
    for _, p in ipairs(self.prefixes or {}) do
        p = tostring(p):lower()
        if t == p and (not bestLen or #p > bestLen) then best, bestLen = "", #p
        elseif t:sub(1, #p + 1) == p .. " " and (not bestLen or #p > bestLen) then
            best, bestLen = (t:sub(#p + 2):gsub("^%s+", "")), #p
        end
    end
    return best, bestLen
end

-- Schlüssel für den Zähler: das deutsche Wort des passenden Eintrags ohne Beispielzahlen; nil = kein Befehl
function Handle:KeyFor(msg)
    local words = Words(msg)
    if #words == 0 then return nil end
    local best, bestN
    for _, c in ipairs(self.commands or {}) do
        for _, form in ipairs({ c[1], c[2] }) do
            local fw = Words(form)
            local n = 0
            for i = 1, math.min(#fw, #words) do
                if fw[i] == words[i] or fw[i]:match("^%d+$") then n = n + 1 else break end
            end
            if #fw > 0 and n >= 1 and (not bestN or n > bestN) then best, bestN = c, n end
        end
    end
    return best and BaseOf(best[1]) or nil
end

function Handle:Count(msg)
    local key = self:KeyFor(msg)
    if not key or key == "" then return nil end
    local st = self.store and self.store()
    if type(st) ~= "table" then return nil end
    st[key] = (st[key] or 0) + 1
    return key
end

-- Liste für den getippten Rest: { { cmd = "/ahs protokoll", run = "protokoll", text = "…", uses = n, order = i } }
function Handle:List(rest)
    rest = (rest or ""):lower()
    local german = self.german and self.german()
    local dev = self.dev and self.dev()
    local st = (self.store and self.store()) or {}
    local shown = self.display or (self.prefixes and self.prefixes[1]) or ""
    local out = {}
    for i, c in ipairs(self.commands or {}) do
        local isDev = c.dev or tostring(c[1] or ""):find("^test") ~= nil
        if (c[1] or "") ~= "" and (dev or not isDev) then
            local de, en = tostring(c[1]), tostring(c[2] or c[1])
            local hit = rest == "" or de:lower():sub(1, #rest) == rest or en:lower():sub(1, #rest) == rest
            if hit then
                local key = BaseOf(de)
                out[#out + 1] = { cmd = shown .. " " .. (german and de or en), run = german and key or BaseOf(en),
                    text = (self.L and self.L[c[3]]) or c[3] or "", uses = st[key] or 0, order = i, key = key }
            end
        end
    end
    table.sort(out, function(a, b)
        if a.uses ~= b.uses then return a.uses > b.uses end
        return a.order < b.order
    end)
    return out
end

-- CH3: Enter schickt den getippten Text an den Slash-Handler – passt er zum Anfang der frischen Auswahl dieses
-- Addons, gilt die Auswahl. Eine Auswahl gilt nur für das Addon, in dessen Liste sie getroffen wurde.
function Handle:Resolve(msg)
    local s = CH:Selection()
    if not s or s.owner ~= self then return msg end
    local typed = tostring(msg or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
    local run = tostring(s.item.run or ""):lower()
    CH.selected = nil
    if typed == "" or run:sub(1, #typed) == typed then return s.item.run end
    return msg
end

function Handle:Allowed()
    if self.enabled and not self.enabled() then return false end
    local inCombat = _G.InCombatLockdown
    if inCombat and inCombat() then return false end
    return true
end

-- ------------------------------------------------------------
-- Anmelden
-- ------------------------------------------------------------
function CH.Register(cfg)
    if type(cfg) ~= "table" or type(cfg.id) ~= "string" or cfg.id == "" or type(cfg.prefixes) ~= "table" then
        return nil
    end
    local h = CH.addons[cfg.id]
    if not h then
        h = setmetatable({}, Handle)
        CH.addons[cfg.id] = h
        CH.order[#CH.order + 1] = cfg.id
    end
    for k, v in pairs(cfg) do h[k] = v end
    CH:Start()
    return h
end
function CH.Get(id) return CH.addons[id] end

-- Welches Addon ist gemeint? (längster passender Präfix; bei Gleichstand das zuerst angemeldete)
function CH:Find(text)
    local bestH, bestRest, bestLen
    for _, id in ipairs(self.order) do
        local h = self.addons[id]
        local rest, len = h:Match(text)
        if rest and (not bestLen or len > bestLen) then bestH, bestRest, bestLen = h, rest, len end
    end
    return bestH, bestRest
end

-- ------------------------------------------------------------
-- Auswahl
-- ------------------------------------------------------------
function CH:Select(item, byMouse)
    if not item then return end
    self.selected = { item = item, owner = self.owner, t = Now() }
    if byMouse then self.clickAt = Now() end
    self:Draw()
    local box = self.editBox or self.lastBox
    if box and box.SetFocus and box.IsShown and box:IsShown() then pcall(box.SetFocus, box) end   -- nur Fokus
end
function CH:Selection()
    local s = self.selected
    if s and Now() - s.t <= self.SELECT_SECONDS then return s end
    return nil
end
function CH:SelectNext(step)
    local items = self.items or {}
    if #items == 0 then return end
    local cur = 0
    local s = self:Selection()
    for i, it in ipairs(items) do if s and s.item == it then cur = i end end
    self:Select(items[((cur - 1 + (step or 1)) % #items) + 1], false)
end

-- ------------------------------------------------------------
-- Fenster (eins für alle Addons)
-- ------------------------------------------------------------
function CH:EnsureFrame()
    if self.frame then return self.frame end
    local f = CreateFrame("Frame", "GoldSentinelCmdHintFrame", UIParent, BackdropTemplateMixin and "BackdropTemplate" or nil)
    f:SetFrameStrata("DIALOG")
    if f.SetClampedToScreen then f:SetClampedToScreen(true) end
    if f.SetBackdrop then
        f:SetBackdrop({ bgFile = "Interface\\Buttons\\WHITE8X8", edgeFile = "Interface\\Buttons\\WHITE8X8", edgeSize = 1 })
        f:SetBackdropColor(0.06, 0.07, 0.09, 0.95)
        f:SetBackdropBorderColor(0, 0.82, 0.82, 0.8)
    end
    if f.EnableMouseWheel then f:EnableMouseWheel(true) end
    f:SetScript("OnMouseWheel", function(_, delta)
        CH.offset = math.max(0, math.min((CH.offset or 0) - delta, math.max(0, #(CH.items or {}) - CH.MAX_ROWS)))
        CH:Draw()
    end)
    f.rows = {}
    for i = 1, self.MAX_ROWS do
        local b = CreateFrame("Button", nil, f)
        b:SetHeight(self.ROW_H)
        b:SetPoint("TOPLEFT", 4, -4 - (i - 1) * self.ROW_H)
        b:SetPoint("TOPRIGHT", -4, -4 - (i - 1) * self.ROW_H)
        local hl = b:CreateTexture(nil, "HIGHLIGHT")
        hl:SetAllPoints()
        hl:SetColorTexture(0, 0.82, 0.82, 0.15)
        b.cmd = b:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
        b.cmd:SetPoint("LEFT", 4, 0)
        b.cmd:SetWidth(150)
        b.cmd:SetJustifyH("LEFT")
        b.desc = b:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
        b.desc:SetPoint("LEFT", b.cmd, "RIGHT", 6, 0)
        b.desc:SetPoint("RIGHT", -4, 0)
        b.desc:SetJustifyH("LEFT")
        if b.desc.SetWordWrap then b.desc:SetWordWrap(false) end
        b.sel = b:CreateTexture(nil, "BACKGROUND")
        b.sel:SetAllPoints()
        b.sel:SetColorTexture(0, 0.82, 0.82, 0.30)
        b.sel:Hide()
        b:SetScript("OnClick", function(btn) if btn.item then CH:Select(btn.item, true) end end)  -- Klick = wählen
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

function CH:Draw()
    local f = self.frame
    if not f then return end
    local items = self.items or {}
    local n = math.min(#items, self.MAX_ROWS)
    for i, b in ipairs(f.rows) do
        local it = items[i + (self.offset or 0)]
        if i <= n and it then
            b.item = it
            b.cmd:SetText("|cff33dd55" .. it.cmd .. "|r")
            b.desc:SetText(it.text)
            local s = self:Selection()
            if s and s.item == it then b.sel:Show() else b.sel:Hide() end
            b:Show()
        else
            b.item = nil
            b:Hide()
        end
    end
    local owner = self.owner
    local s = self:Selection()
    f.head:SetText(s and string.format((owner and owner.enterText) or "Enter = %s", s.item.cmd) or "")
    if #items == 0 then
        f.empty:SetText((owner and owner.noMatch) or "")
        f.empty:Show()
        f:SetHeight(self.ROW_H + 8)
    else
        f.empty:Hide()
        f:SetHeight(n * self.ROW_H + 8)
    end
end

function CH:Show(owner, editBox, rest)
    local f = self:EnsureFrame()
    if self.owner ~= owner then self.selected = nil end
    self.owner = owner
    self.items = owner:List(rest)
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

function CH:Hide()
    if self.frame then self.frame:Hide() end
    self.editBox = nil
end

-- Eingabefeld hat sich geändert (nur lesen)
function CH:OnText(editBox)
    local ok, text = pcall(editBox.GetText, editBox)
    if not ok then return self:Hide() end
    local h, rest = self:Find(text)
    if not h or not h:Allowed() then return self:Hide() end
    self:Show(h, editBox, rest)
end

-- Fokusverlust schliesst erst verzögert und nicht, wenn gerade in der Liste geklickt wurde
function CH:OnFocusLost(box)
    if self.editBox ~= box then return end
    local function close()
        if self.clickAt and Now() - self.clickAt < 0.5 then return end
        if self.frame and self.frame.IsMouseOver and self.frame:IsShown() and self.frame:IsMouseOver() then return end
        if self.editBox == box then self:Hide() end
    end
    if _G.C_Timer and _G.C_Timer.After and not self.instantClose then _G.C_Timer.After(0.3, close) else close() end
end

-- ------------------------------------------------------------
-- Einhaken (nur HookScript, je Feld einmal für alle Addons)
-- ------------------------------------------------------------
function CH:HookBox(box)
    if type(box) ~= "table" or not box.HookScript or self.hooked[box] then return end
    self.hooked[box] = true
    -- Die Hooks rufen immer die aktuelle Fassung (_G.GoldSentinelCmdHint), damit eine neuere Datei sie übernimmt.
    box:HookScript("OnTextChanged", function(b) local C = _G.GoldSentinelCmdHint; if C then C:OnText(b) end end)
    box:HookScript("OnEditFocusLost", function(b) local C = _G.GoldSentinelCmdHint; if C then C:OnFocusLost(b) end end)
    box:HookScript("OnTabPressed", function(b)
        local C = _G.GoldSentinelCmdHint
        if C and C.editBox == b and C.frame and C.frame:IsShown() then
            C:SelectNext(_G.IsShiftKeyDown and _G.IsShiftKeyDown() and -1 or 1)
        end
    end)
    box:HookScript("OnHide", function(b) local C = _G.GoldSentinelCmdHint; if C and C.editBox == b then C:Hide() end end)
end

function CH:HookAll()
    for i = 1, (_G.NUM_CHAT_WINDOWS or 10) do self:HookBox(_G["ChatFrame" .. i .. "EditBox"]) end
    self:HookBox(_G.ChatFrameEditBox)            -- sehr alte Clients: ein gemeinsames Eingabefeld
end

function CH:Start()
    if self.started then return end
    self.started = true
    pcall(self.HookAll, self)
    local ev = CreateFrame("Frame")
    ev:RegisterEvent("PLAYER_REGEN_DISABLED")
    ev:SetScript("OnEvent", function() local C = _G.GoldSentinelCmdHint; if C then C:Hide() end end)
    self.combatFrame = ev
end

-- ------------------------------------------------------------
-- Übernahme einer älteren Fassung (Anmeldungen, Hooks, Fenster)
-- ------------------------------------------------------------
if type(old) == "table" then
    for _, id in ipairs(old.order or {}) do
        local oh = old.addons and old.addons[id]
        if oh then
            setmetatable(oh, Handle)              -- alte Handles bekommen die neuen Funktionen (Addons behalten sie)
            CH.addons[id] = oh
            CH.order[#CH.order + 1] = id
        end
    end
    CH.hooked = old.hooked or CH.hooked       -- Hooks rufen _G.GoldSentinelCmdHint, also gelten sie weiter
    CH.frame = nil                            -- eigenes Fenster neu bauen; altes verstecken
    if old.frame and old.frame.Hide then old.frame:Hide() end
    CH.started = old.started
    if old.combatFrame and old.combatFrame.SetScript then
        old.combatFrame:SetScript("OnEvent", function() local C = _G.GoldSentinelCmdHint; if C then C:Hide() end end)
        CH.combatFrame = old.combatFrame
    end
end

_G.GoldSentinelCmdHint = CH
