-- GoldSentinelPruefliste - Prüfliste im Spiel für alle Addons von GoldSentinel (nur Entwicklermodus)
-- Copyright (C) 2026 GoldSentinel
--
-- Entscheid des Nutzers 16.11.2026 06:47: "Erstelle mir für AHS und alle anderen Addons, wenn etwas getestet werden muss, eine
-- Checkliste im Spiel, die merkt, wenn ein Punkt bearbeitet ist – nur im Entwicklermodus aufrufbar."
--
-- Diese Datei UNVERÄNDERT aus shared/ in jedes Addon kopieren und in der .toc NACH GoldSentinelDev.lua und VOR den eigenen
-- Dateien eintragen. Mehrere Addons dürfen sie mitbringen: die neueste Version gewinnt, jede Liste gehört ihrem Addon.
--
-- Benutzung im Addon (Beispiel AHSentinel):
--   local PL = GoldSentinelPruefliste and GoldSentinelPruefliste:Register("AHSentinel", {
--       db = function() return AHSentinelDB end,            -- eigene SavedVariables-Tabelle (Feld "pruefliste" wird angelegt)
--       version = "0.65.259",
--       points = {
--         { id = "SN-BTN1", title = "Kauf-Knopf: ein Klick = ein Kauf", since = "0.65.208",
--           todo = "Sniper-Ziel mit Treffer, einmal auf Kaufen klicken.", expect = "Genau ein Kauf, Knopf danach grau.",
--           auto = function() return nil end },               -- optional: true = erledigt, false = Fehler, nil = noch nicht
--       } })
--   Im Code dort, wo die Funktion wirklich benutzt wurde:  if PL then PL:Hit("SN-BTN1", "1 Kauf 8s50") end
--   Slash-Befehl des Addons (nur im Entwicklermodus):      if PL then PL:Open() end   ("/ahs prüfliste")
--   Testbericht:                                           if PL then for _, l in ipairs(PL:ReportLines()) do ... end end
--
-- Zustände je Punkt: offen · auto (vom Addon selbst erkannt) · ok (vom Spieler bestätigt) · nok (vom Spieler als Fehler markiert,
-- mit Notiz) · fehler (auto() meldet false). Ein Punkt mit neuer "since"-Version ist wieder offen.
-- Alles ist ohne Entwicklermodus wirkungslos (Register gibt eine Liste zurück, deren Funktionen nichts tun) – Spieler sehen nichts.
-- Kein Senden, kein Ändern fremder Daten, keine Rechnung im Kampf (auto() läuft nur bei offenem Fenster und ausserhalb des Kampfs).

local VERSION = 1

local existing = _G.GoldSentinelPruefliste
if type(existing) == "table" and (existing.version or 0) >= VERSION then return end

local PL = type(existing) == "table" and existing or {}
_G.GoldSentinelPruefliste = PL
PL.version = VERSION
PL.lists = PL.lists or {}

local GREEN, RED, GOLD, GRAY, WHITE = "|cff40d860", "|cffff6060", "|cffffd100", "|cff8a8f99", "|cffffffff"
local STATE_TEXT = { offen = GRAY .. "offen|r", auto = GREEN .. "erledigt (erkannt)|r", ok = GREEN .. "OK|r",
    nok = RED .. "nicht OK|r", fehler = RED .. "Fehler (erkannt)|r" }

local function IsDev()
    local D = _G.GoldSentinelDev
    if type(D) ~= "table" or type(D.IsDev) ~= "function" then return false end
    local ok, r = pcall(D.IsDev, D)
    return ok and r == true
end
PL.IsDev = IsDev

local function Now() return (_G.time and _G.time()) or 0 end
local function InCombat()
    local f = _G.InCombatLockdown
    if type(f) ~= "function" then return false end
    local ok, r = pcall(f)
    return ok and r == true
end
local function Say(list, text)
    local cf = _G.DEFAULT_CHAT_FRAME
    if cf and cf.AddMessage then cf:AddMessage(GOLD .. "Prüfliste " .. list.addon .. ":|r " .. text) end
end

-- ------------------------------------------------------------
-- Liste
-- ------------------------------------------------------------
local List = {}
List.__index = List

local NOOP = setmetatable({}, { __index = function() return function() return nil end end })
NOOP.ReportLines = function() return {} end
NOOP.Count = function() return 0, 0 end

function PL:Register(addon, opts)
    if not IsDev() then return NOOP end
    opts = type(opts) == "table" and opts or {}
    local l = setmetatable({ addon = tostring(addon or "?"), opts = opts, points = {}, byId = {} }, List)
    for _, p in ipairs(type(opts.points) == "table" and opts.points or {}) do
        if type(p) == "table" and p.id and not l.byId[p.id] then
            l.points[#l.points + 1] = p
            l.byId[p.id] = p
        end
    end
    self.lists[l.addon] = l
    return l
end
function PL:Get(addon) return self.lists[tostring(addon or "")] end

-- gespeicherter Zustand: db().pruefliste = { p = { [id] = { s, t, n, v } } }
function List:Store()
    local get = self.opts.db
    local db = type(get) == "function" and select(2, pcall(get)) or nil
    if type(db) ~= "table" then return nil end
    if type(db.pruefliste) ~= "table" then db.pruefliste = { p = {} } end
    if type(db.pruefliste.p) ~= "table" then db.pruefliste.p = {} end
    return db.pruefliste.p
end
function List:State(id)
    local p = self.byId[id]
    local st = self:Store()
    local e = st and st[id]
    if not p or type(e) ~= "table" then return "offen", nil end
    if p.since and e.v ~= p.since then return "offen", nil end          -- neue Fassung des Punkts -> wieder offen
    return e.s or "offen", e
end
function List:Set(id, state, note)
    local p = self.byId[id]
    local st = self:Store()
    if not (p and st and STATE_TEXT[state]) then return false end
    if state == "offen" then st[id] = nil; return true end
    st[id] = { s = state, t = Now(), n = note and tostring(note):sub(1, 200) or nil, v = p.since }
    return true
end
-- vom Addon gemeldet: die Funktion wurde wirklich benutzt -> erledigt (nur wenn noch offen; ok/nok des Spielers bleiben)
function List:Hit(id, note)
    local s = self:State(id)
    if s ~= "offen" and s ~= "fehler" then return false end
    if not self:Set(id, "auto", note) then return false end
    self.pin = nil                                                  -- erledigt -> Anzeige springt zum nächsten offenen Punkt
    Say(self, string.format("%s erledigt (erkannt)%s", id, note and (" – " .. tostring(note)) or ""))
    if self.frame and self.frame:IsShown() then self:Refresh() end
    return true
end
-- auto()-Prüfungen der offenen Punkte (nur ausserhalb des Kampfs); Fehler in einer Prüfung = "fehler" für diesen Punkt
function List:RunAuto()
    if InCombat() then return 0 end
    local n = 0
    for _, p in ipairs(self.points) do
        local s = self:State(p.id)
        if (s == "offen" or s == "fehler") and type(p.auto) == "function" then
            local ok, r, info = pcall(p.auto)
            if not ok then
                self:Set(p.id, "fehler", "Lua: " .. tostring(r)); n = n + 1
            elseif r == true then
                self:Hit(p.id, info); n = n + 1
            elseif r == false and s ~= "fehler" then
                self:Set(p.id, "fehler", info); n = n + 1
            end
        end
    end
    return n
end
-- erster Punkt, der noch nicht erledigt ist (offen, Fehler oder nicht OK – in der Reihenfolge der Liste)
function List:NextOpen()
    for _, p in ipairs(self.points) do
        local s = self:State(p.id)
        if s ~= "auto" and s ~= "ok" then return p.id end
    end
    return nil
end
function List:Count()
    local done = 0
    for _, p in ipairs(self.points) do
        local s = self:State(p.id)
        if s == "auto" or s == "ok" then done = done + 1 end
    end
    return done, #self.points
end
-- Zeilen für den Testbericht (nur Zahlen/Kürzel, keine Namen)
function List:ReportLines()
    local done, all = self:Count()
    local out = { string.format("PRÜFLISTE %s: %d von %d erledigt", self.addon, done, all) }
    for _, p in ipairs(self.points) do
        local s, e = self:State(p.id)
        out[#out + 1] = string.format("  %s %s%s%s", p.id, s,
            e and e.t and _G.date and (" " .. _G.date("%d.%m. %H:%M", e.t)) or "",
            e and e.n and (" – " .. e.n) or "")
    end
    return out
end

-- ------------------------------------------------------------
-- Fenster (schlicht, nur Blizzard-Vorlagen)
-- ------------------------------------------------------------
local ROWS = 14
function List:Build()
    if self.frame or not _G.CreateFrame then return self.frame end
    local f = _G.CreateFrame("Frame", nil, _G.UIParent, _G.BackdropTemplateMixin and "BackdropTemplate" or nil)
    f:SetSize(560, 480)
    f:SetPoint("CENTER")
    f:SetFrameStrata("DIALOG")
    f:EnableMouse(true)
    f:SetMovable(true)
    f:RegisterForDrag("LeftButton")
    f:SetScript("OnDragStart", f.StartMoving)
    f:SetScript("OnDragStop", f.StopMovingOrSizing)
    if f.SetBackdrop then
        f:SetBackdrop({ bgFile = "Interface\\Tooltips\\UI-Tooltip-Background", edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
            edgeSize = 14, insets = { left = 3, right = 3, top = 3, bottom = 3 } })
        f:SetBackdropColor(0.06, 0.06, 0.08, 0.95)
    end
    f.title = f:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    f.title:SetPoint("TOPLEFT", 12, -10)
    local close = _G.CreateFrame("Button", nil, f, "UIPanelCloseButton")
    close:SetPoint("TOPRIGHT", -2, -2)
    f.rows = {}
    for i = 1, ROWS do
        local b = _G.CreateFrame("Button", nil, f)
        b:SetSize(536, 18)
        b:SetPoint("TOPLEFT", 12, -36 - (i - 1) * 18)
        b.text = b:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
        b.text:SetPoint("LEFT")
        b.text:SetJustifyH("LEFT")
        b.text:SetWidth(536)
        b:SetScript("OnClick", function() self.sel, self.pin = b.id, true; self:Refresh() end)   -- angeklickt = bleibt gewählt
        f.rows[i] = b
    end
    f.detail = f:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    f.detail:SetPoint("TOPLEFT", 12, -36 - ROWS * 18 - 8)
    f.detail:SetWidth(536)
    f.detail:SetJustifyH("LEFT")
    local function Btn(label, x, fn)
        local b = _G.CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
        b:SetSize(120, 22)
        b:SetPoint("BOTTOMLEFT", x, 10)
        b:SetText(label)
        b:SetScript("OnClick", fn)
        return b
    end
    Btn("OK", 12, function() if self.sel then self:Set(self.sel, "ok"); self.pin = nil; self:Refresh() end end)
    Btn("Nicht OK", 140, function() if self.sel then self:Set(self.sel, "nok", "vom Spieler markiert"); self:Refresh() end end)
    Btn("Zurücksetzen", 268, function() if self.sel then self:Set(self.sel, "offen"); self:Refresh() end end)
    Btn("Jetzt prüfen", 396, function() self:RunAuto(); self:Refresh() end)
    f.elapsed = 0
    f:SetScript("OnUpdate", function(fr, dt)                          -- nur bei offenem Fenster: alle 2 s die offenen Punkte prüfen
        fr.elapsed = fr.elapsed + (dt or 0)
        if fr.elapsed < 2 then return end
        fr.elapsed = 0
        if self:RunAuto() > 0 then self:Refresh() end
    end)
    f:Hide()
    self.frame = f
    return f
end
function List:Refresh()
    local f = self.frame
    if not f then return end
    local done, all = self:Count()
    f.title:SetText(string.format("Prüfliste %s %s – %d von %d erledigt", self.addon, tostring(self.opts.version or ""), done, all))
    -- Anweisung immer sichtbar (Nutzer 06:47 "damit ich immer genau weiss, was zu tun ist"): ist nichts gewählt oder der gewählte
    -- Punkt erledigt, springt die Auswahl von selbst auf den nächsten offenen Punkt
    local cur = self.sel and self:State(self.sel)
    if not self.pin and (not self.sel or cur == "auto" or cur == "ok") then self.sel = self:NextOpen() end   -- nil = alles erledigt
    for i = 1, ROWS do
        local p, b = self.points[i], f.rows[i]
        if p then
            b.id = p.id
            b.text:SetText(string.format("%s%s|r  %s  %s", p.id == self.sel and WHITE or GRAY, p.id, tostring(p.title or ""),
                STATE_TEXT[(self:State(p.id))] or ""))
            b:Show()
        else
            b.id = nil
            b:Hide()
        end
    end
    local p = self.sel and self.byId[self.sel]
    if p then
        local s, e = self:State(p.id)
        local nr = 0
        for i, q in ipairs(self.points) do if q.id == p.id then nr = i end end
        f.detail:SetText(string.format("%sSchritt %d von %d: %s|r  (%s)\n%sDas tust du:|r %s\n%sDas musst du sehen:|r %s\n%s%s",
            WHITE, nr, #self.points, tostring(p.title or p.id), STATE_TEXT[s] or s, GOLD, tostring(p.todo or "-"), GOLD,
            tostring(p.expect or "-"),
            GRAY .. "Stimmt es: nichts tun, das Addon merkt es selbst (sonst \"OK\"). Stimmt es nicht: \"Nicht OK\" und dem Supervisor sagen.|r",
            e and e.n and ("\n" .. GOLD .. "Notiz:|r " .. e.n) or ""))
    elseif all > 0 then
        f.detail:SetText(GREEN .. "Alle Punkte erledigt. Danke! Jetzt /reload, damit das Ergebnis hochgeladen wird.|r")
    else
        f.detail:SetText(GRAY .. "Zurzeit gibt es nichts zu prüfen.|r")
    end
end
function List:Open()
    if not IsDev() then return false end
    local f = self:Build()
    if not f then return false end
    self:RunAuto()
    self:Refresh()
    f:Show()
    return true
end
