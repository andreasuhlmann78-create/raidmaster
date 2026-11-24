-- __ADDON__ – Prüfung der Oberfläche im echten Client (Testfälle TK18–TK28), Ausweichen und Lesbarkeit
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Anlass (Live-Test 5. Nov. 2026): eigene Tooltips verdeckten Knöpfe, Fenster lagen übereinander, Anzeigen rechneten
-- mit falschen Spielwerten (Fertigkeit 0), ein Fehler kam 588×. Offline sieht man das nicht – darum prüft die
-- Testroutine es im Spiel selbst. Nur lesen, nichts verändern.
--
-- Benutzung im eigenen Code:
--   ns.RegisterUI(frame, "Name")                 -- jedes eigene Fenster anmelden (UI.lua macht das für Haupt-/Kopierfenster)
--   ns.RegisterUI(frame, "Name", "hud")          -- frei verschiebbare Kampfanzeige (Leisten, Symbole, Anker): wird
--                                                   selbst geprüft, kommt aber NICHT in die gemeinsame Liste – andere
--                                                   Addons sollen sich nicht an Kampfanzeigen stossen (wie ThreatSentinel)
--   ns.Plausible("Fertigkeit", function() return skill > 0, skill, "> 0" end)   -- Spielwert-Prüfung für TK22
-- Andere GoldSentinel-Addons melden ihre Fenster in der globalen Liste GoldSentinelUIFrames an (TK19 prüft gegeneinander).

local ADDON, ns = ...

ns.uiFrames = ns.uiFrames or {}
ns.plausible = ns.plausible or {}
ns.UI_LOOP_LIMIT = 10                       -- dieselbe Fehlermeldung öfter -> Fehlerschleife (TK23)

-- Blizzard-Fenster, an die GoldSentinel-Addons andocken (dürfen nicht überdeckt werden)
ns.UI_BLIZZARD = { "ProfessionsFrame", "TradeSkillFrame", "CraftFrame", "MerchantFrame", "AuctionHouseFrame",
                   "AuctionFrame", "MailFrame", "QuestLogFrame", "WorldMapFrame", "CharacterFrame" }

GoldSentinelUIFrames = GoldSentinelUIFrames or {}

function ns.RegisterUI(frame, name, kind)
    if not frame then return end
    for _, e in ipairs(ns.uiFrames) do if e.frame == frame then return end end
    local e = { frame = frame, name = name or (frame.GetName and frame:GetName()) or ADDON, hud = (kind == "hud") }
    ns.uiFrames[#ns.uiFrames + 1] = e
    -- Kampfanzeigen nicht in die gemeinsame Liste (Befund 10.11.: BuffSentinel-Anker galten bei anderen als "überdeckt")
    if not e.hud then
        GoldSentinelUIFrames[#GoldSentinelUIFrames + 1] = { frame = frame, name = e.name, addon = ADDON }
    end
end

function ns.Plausible(name, fn) ns.plausible[#ns.plausible + 1] = { name = name, fn = fn } end

local U = {}
ns.UICheck = U

-- Ist der echte Client da (Rechtecke, Kinder, Tooltip)? Sonst werden die Fälle ehrlich übersprungen.
function U.Available()
    local f = ns.uiFrames[1] and ns.uiFrames[1].frame
    return f and type(f.GetRect) == "function" and type(f.GetChildren) == "function"
        and type(GameTooltip) == "table" and type(GameTooltip.GetRect) == "function"
        and type(UIParent) == "table" and type(UIParent.GetRect) == "function" and true or false
end

function U.Rect(f)
    if not (f and f.GetRect) then return nil end
    local ok, l, b, w, h = pcall(f.GetRect, f)
    if not ok or not l or not w or w <= 0 or h <= 0 then return nil end
    local s = f.GetEffectiveScale and f:GetEffectiveScale() or 1
    return { l = l * s, b = b * s, r = (l + w) * s, t = (b + h) * s }
end

-- Fläche der Überschneidung (0 = keine). Ein Pixel Rand gilt als "angedockt", nicht als Überlappen.
function U.Overlap(a, c)
    if not (a and c) then return 0 end
    local w = math.min(a.r, c.r) - math.max(a.l, c.l) - 1
    local h = math.min(a.t, c.t) - math.max(a.b, c.b) - 1
    return (w > 0 and h > 0) and w * h or 0
end

local function Shown(f) return f and f.IsVisible and f:IsVisible() end

local function Name(f)
    local n = f and f.GetName and f:GetName()
    if n then return n end
    local t = f and f.GetText and f:GetText()
    return t and ("'" .. tostring(t) .. "'") or tostring(f and f.GetObjectType and f:GetObjectType() or "?")
end

-- alle sichtbaren Nachfahren eines Fensters
function U.Descendants(f, out)
    out = out or {}
    if not (f and f.GetChildren) then return out end
    for _, c in ipairs({ f:GetChildren() }) do
        if Shown(c) then out[#out + 1] = c; U.Descendants(c, out) end
    end
    return out
end

local function IsControl(f)
    return f.IsObjectType and (f:IsObjectType("Button") or f:IsObjectType("EditBox") or f:IsObjectType("CheckButton")
        or f:IsObjectType("Slider")) and true or false
end

-- TK18: kein eigener Tooltip verdeckt einen Knopf desselben Fensters
function U.TooltipsCoverNothing()
    local problems, tested = {}, 0
    for _, e in ipairs(ns.uiFrames) do
        if Shown(e.frame) then
            local all = U.Descendants(e.frame)
            for _, el in ipairs(all) do
                local enter = el.GetScript and el:GetScript("OnEnter")
                if enter then
                    tested = tested + 1
                    pcall(enter, el)
                    local tip = Shown(GameTooltip) and U.Rect(GameTooltip)
                    if tip then
                        for _, other in ipairs(all) do
                            if other ~= el and IsControl(other) and U.Overlap(tip, U.Rect(other)) > 0 then
                                problems[#problems + 1] = Name(el) .. " verdeckt " .. Name(other)
                                break
                            end
                        end
                    end
                    local leave = el:GetScript("OnLeave")
                    if leave then pcall(leave, el) end
                    if GameTooltip.Hide then GameTooltip:Hide() end
                end
            end
        end
    end
    return problems, tested
end

-- TK19: eigene sichtbare Fenster überdecken weder Blizzard-Fenster noch Fenster anderer GoldSentinel-Addons
function U.WindowsOverlapNothing()
    local problems, tested = {}, 0
    for _, e in ipairs(ns.uiFrames) do
        local mine = not e.hud and Shown(e.frame) and U.Rect(e.frame)   -- Kampfanzeigen werden frei platziert
        if mine then
            for _, bn in ipairs(ns.UI_BLIZZARD) do
                local bf = _G[bn]
                if Shown(bf) then
                    tested = tested + 1
                    if U.Overlap(mine, U.Rect(bf)) > 0 then problems[#problems + 1] = e.name .. " überdeckt " .. bn end
                end
            end
            for _, o in ipairs(GoldSentinelUIFrames) do
                if o.addon ~= ADDON and Shown(o.frame) then
                    tested = tested + 1
                    if U.Overlap(mine, U.Rect(o.frame)) > 0 then
                        problems[#problems + 1] = e.name .. " überdeckt " .. o.name .. " (" .. o.addon .. ")"
                    end
                end
            end
        end
    end
    return problems, tested
end

-- TK20: sichtbare Fenster liegen ganz im Bildschirm
function U.InsideScreen()
    local problems, tested, screen = {}, 0, U.Rect(UIParent)
    for _, e in ipairs(ns.uiFrames) do
        local r = Shown(e.frame) and U.Rect(e.frame)
        if r and screen then
            tested = tested + 1
            if r.l < screen.l - 1 or r.b < screen.b - 1 or r.r > screen.r + 1 or r.t > screen.t + 1 then
                problems[#problems + 1] = e.name .. " ragt aus dem Bildschirm"
            end
        end
    end
    return problems, tested
end

-- TK21: Beschriftungen von Knöpfen sind nicht abgeschnitten (andere Texte nur als Hinweis)
function U.TextFits()
    local problems, hints, tested = {}, {}, 0
    for _, e in ipairs(ns.uiFrames) do
        if Shown(e.frame) then
            for _, el in ipairs(U.Descendants(e.frame)) do
                local fs = el.GetFontString and el:GetFontString()
                if fs and fs.IsTruncated then
                    tested = tested + 1
                    if fs:IsTruncated() then problems[#problems + 1] = Name(el) .. " Beschriftung abgeschnitten" end
                end
                for _, region in ipairs(el.GetRegions and { el:GetRegions() } or {}) do
                    if region.IsObjectType and region:IsObjectType("FontString") and region.IsTruncated and Shown(region) then
                        tested = tested + 1
                        if region:IsTruncated() then hints[#hints + 1] = Name(el) .. ": Text gekürzt" end
                    end
                end
            end
        end
    end
    return problems, tested, hints
end

-- TK22: angezeigte Spielwerte plausibel (Prüfungen meldet das Addon mit ns.Plausible an)
function U.ValuesPlausible()
    local problems = {}
    for _, p in ipairs(ns.plausible) do
        local ok, good, got, want = pcall(p.fn)
        if not ok then problems[#problems + 1] = p.name .. ": Lua-Fehler " .. tostring(good)
        elseif good == false then problems[#problems + 1] = p.name .. ": " .. tostring(got) .. " (erwartet " .. tostring(want) .. ")" end
    end
    return problems, #ns.plausible
end

-- TK23: keine Fehlerschleife – dieselbe Meldung höchstens UI_LOOP_LIMIT× (Diagnose-Protokoll der echten Daten)
function U.NoErrorLoops()
    local problems = {}
    local db = ns.realDB or ns.db
    local entries = db and db.diag and db.diag.entries or {}
    for _, en in ipairs(entries) do
        if en.k == "FEHLER" and (en.n or 1) > ns.UI_LOOP_LIMIT then
            problems[#problems + 1] = (en.n or 1) .. "× " .. tostring(en.t)
        end
    end
    return problems, #entries
end

---------------------------------------------------------------------------------------------------------------------
-- Ausweichen / Andocken (Befunde GS-K1, BS-K1 vom 24.11.2026; Vorbild ThreatSentinel 2.5.17 T-K2)
-- Ein eigenes Fenster legt sich beim Zeigen nicht über offene Blizzard-Fenster oder sichtbare Fenster anderer
-- GoldSentinel-Addons. Geprüft werden alle Lagen neben jedem Hindernis (rechts, links, darüber, darunter, im Bildschirm);
-- gewählt wird die mit der kleinsten Überdeckung, bei Gleichstand die nächste zur bisherigen Lage. Findet sich mit 8 Pixel
-- Abstand nichts Freies, wird bündig angedockt (Kante an Kante, 1 Pixel gilt als angedockt). Nur für diese Anzeige, die
-- gespeicherte Lage bleibt. HUD-Anzeigen anderer Addons (Entscheid Supervisor 17.11.2026 17:10) sind keine Fenster.
---------------------------------------------------------------------------------------------------------------------
ns.UI_FOREIGN_HUD = ns.UI_FOREIGN_HUD or {
    LevelPilotArrow = true,            -- LevelPilot-Pfeil (Wegweiser)
    ["LevelPilot:Pfeil"] = true,
}
local function ForeignHUD(o)
    if not o then return false end
    local f = o.frame
    local gn = f and f.GetName and f:GetName()
    if gn and ns.UI_FOREIGN_HUD[gn] then return true end
    return ns.UI_FOREIGN_HUD[tostring(o.addon) .. ":" .. tostring(o.name)] == true
end
U.ForeignHUD = ForeignHUD

-- Ist ein Rahmen wirklich zu sehen? Sichtbar, nicht durchsichtig, mit Inhalt (Fläche, Text oder sichtbares Kind).
-- Leere Ankerrahmen anderer Addons zählen nicht.
local function HasContent(f, depth)
    if f.GetRegions then
        for _, r in ipairs({ f:GetRegions() }) do
            if r.IsShown and r:IsShown() and (not r.GetAlpha or r:GetAlpha() > 0.05) then
                local kind = r.GetObjectType and r:GetObjectType()
                if kind == "Texture" then return true end
                if kind == "FontString" and r:GetText() and r:GetText() ~= "" then return true end
            end
        end
    end
    if f.GetBackdrop and f:GetBackdrop() then return true end
    if depth < 3 and f.GetChildren then
        for _, c in ipairs({ f:GetChildren() }) do
            if c.IsShown and c:IsShown() and HasContent(c, depth + 1) then return true end
        end
    end
    return false
end
function U.ReallyVisible(f)
    if not (f and f.IsVisible and f:IsVisible()) then return false end
    local a = f.GetEffectiveAlpha and f:GetEffectiveAlpha() or 1
    if a <= 0.05 then return false end
    return HasContent(f, 0)
end

function U.Obstacles(frame)
    local list = {}
    for _, bn in ipairs(ns.UI_BLIZZARD) do
        local bf = _G[bn]
        if bf and bf ~= frame and bf.IsVisible and bf:IsVisible() then
            local r = U.Rect(bf)
            if r then r.name = bn; list[#list + 1] = r end
        end
    end
    for _, o in ipairs(GoldSentinelUIFrames or {}) do
        if o.addon ~= ADDON and o.frame ~= frame and not ForeignHUD(o) and U.ReallyVisible(o.frame) then
            local r = U.Rect(o.frame)
            if r then r.name = tostring(o.name) .. " (" .. tostring(o.addon) .. ")"; list[#list + 1] = r end
        end
    end
    return list
end

local function Covered(rect, list)
    local sum = 0
    for _, r in ipairs(list) do sum = sum + U.Overlap(rect, r) end
    return sum
end
U.Covered = Covered

-- beste Lage für ein Rechteck (l, t, w, h) im Bildschirm (sw, sh) zwischen den Hindernissen – reine Rechnung (Test TK26)
-- Stufe 1: 8 Pixel Abstand neben jedem Hindernis, erst waagrecht, dann auch senkrecht.
-- Stufe 2 (nur ohne freien Platz in Stufe 1): bündig. Jede freie Lage lässt sich nach links und unten schieben, bis sie an den
-- Bildschirmrand oder ein Hindernis stösst; alle diese Paare werden geprüft. Findet Stufe 2 nichts, gibt es beweisbar keinen
-- freien Platz im Bildschirm (Rückgabe Überdeckung > 0).
function U.BestPlace(l, t, w, h, sw, sh, list)
    local function clampX(x) return math.max(0, math.min(x, sw - w)) end
    local function clampT(y) return math.max(h, math.min(y, sh)) end
    local best, bestCover, bestDist
    local function try(x, y)
        local c = Covered({ l = x, r = x + w, t = y, b = y - h }, list)
        local d = math.abs(x - l) + math.abs(y - t)
        if not best or c < bestCover or (c == bestCover and d < bestDist) then best, bestCover, bestDist = { l = x, t = y }, c, d end
    end
    local function uniq(a) local seen, out = {}, {} for _, v in ipairs(a) do if not seen[v] then seen[v] = true; out[#out + 1] = v end end return out end
    local xs, ts = { clampX(l) }, { clampT(t) }
    for _, r in ipairs(list) do
        xs[#xs + 1] = clampX(r.r + 8); xs[#xs + 1] = clampX(r.l - 8 - w)
        ts[#ts + 1] = clampT(r.b - 8); ts[#ts + 1] = clampT(r.t + 8 + h)
    end
    xs, ts = uniq(xs), uniq(ts)
    for _, x in ipairs(xs) do try(x, ts[1]) end
    if bestCover > 0 then
        for _, x in ipairs(xs) do for _, y in ipairs(ts) do try(x, y) end end
    end
    if bestCover > 0 then
        local xs2, ts2 = { 0 }, { h }
        for _, r in ipairs(list) do
            if r.r + w <= sw then xs2[#xs2 + 1] = r.r end
            if r.t + h <= sh then ts2[#ts2 + 1] = r.t + h end
        end
        xs2, ts2 = uniq(xs2), uniq(ts2)
        for _, x in ipairs(xs2) do for _, y in ipairs(ts2) do try(x, y) end end
    end
    return best, bestCover
end

-- Namen der Hindernisse, die ein Rechteck überdecken (für ehrliche Meldungen)
function U.CoveredBy(rect, list)
    local names = {}
    for _, r in ipairs(list) do
        local a = U.Overlap(rect, r)
        if a > 0 then names[#names + 1] = string.format("%s %d", tostring(r.name or "?"), a) end
    end
    return names
end

-- eigenes Fenster beim Zeigen ausweichen lassen. Rückgabe true = verschoben.
-- ns.UIAvoidLast = { covered = Rest-Überdeckung, free = freier Platz gefunden, by = wer noch überdeckt }
function ns.UIAvoidOthers(frame)
    ns.UIAvoidLast = nil
    if not (frame and frame.IsVisible and frame:IsVisible() and frame.GetRect and UIParent and UIParent.GetWidth) then return false end
    local mine = U.Rect(frame)
    if not mine then return false end
    local list = U.Obstacles(frame)
    local covered = Covered(mine, list)
    ns.UIAvoidLast = { covered = covered, free = covered == 0 }
    if covered == 0 then return false end
    local us = UIParent.GetEffectiveScale and UIParent:GetEffectiveScale() or 1
    local sw = (UIParent:GetWidth() or 0) * us
    local sh = (UIParent:GetHeight() or 0) * us
    local w, h = mine.r - mine.l, mine.t - mine.b
    local best, bestCover = U.BestPlace(mine.l, mine.t, w, h, sw, sh, list)
    ns.UIAvoidLast = { covered = bestCover, free = bestCover == 0,
        by = U.CoveredBy({ l = best.l, r = best.l + w, t = best.t, b = best.t - h }, list) }
    local fs = frame:GetEffectiveScale() or 1
    frame:ClearAllPoints()
    frame:SetPoint("TOPLEFT", UIParent, "BOTTOMLEFT", best.l / fs, best.t / fs)
    return true
end

---------------------------------------------------------------------------------------------------------------------
-- Lesbarkeit L1–L8 (Entscheid des Nutzers 20.11.2026 13:44, auftraege/hinweis-ui-lesbarkeit-2026-11-20.txt;
-- Vorbild ThreatSentinel UICheck). Nur lesen. Grenzen mit Quelle:
--   L1 Kontrast >= 4,5:1 = WCAG 2.1, Erfolgskriterium 1.4.3 (Stufe AA, normaler Text), Leuchtdichte nach WCAG 2.1.
--      Hintergrund = eigene Hintergründe (Backdrop) von aussen nach innen gemischt. Die Spielwelt dahinter ist nicht messbar:
--      deckende Fenster (Deckkraft >= 0,9) werden über Schwarz UND Weiss gerechnet (der schlechtere Wert zählt), durchsichtige
--      Anzeigen brauchen eine Kontur oder einen Schatten an der Schrift. Darum jedem Fenster eine Hintergrundfarbe geben
--      (SetBackdropColor), sonst rechnet die Prüfung mit Weiss. Graue Zahl = Kanäle höchstens U.GREY_SPREAD auseinander und
--      hellster Kanal unter U.GREY_MAX: Zahlen, nach denen man entscheidet, nie grau.
--   L2 Geldbeträge rechtsbündig.   L6 keine Zahl in Klammern ohne Wort ("bei dir (765 Mal)" statt "(765)").
--   L8 Schrift mindestens GameFontNormalSmall (Skalierung des Fensters herausgerechnet: die stellt der Spieler ein).
--   L3 gleiche Zahl überall, L4 Summen gehen auf, L5 eine Hauptzahl, L7 unsicher/alt -> keine Empfehlung: hängen am Inhalt.
--      Das Addon meldet dafür Prüfungen mit ns.ReadCheck("L3 Gewinn Liste = Tooltip", fn) an (fn -> ok, ist, soll); TK28.
---------------------------------------------------------------------------------------------------------------------
ns.readChecks = ns.readChecks or {}
function ns.ReadCheck(name, fn) ns.readChecks[#ns.readChecks + 1] = { name = name, fn = fn } end

local function secret(v) return ns.G and ns.G.IsSecret and ns.G.IsSecret(v) end
U.CONTRAST_MIN = 4.5
U.GREY_SPREAD = 0.10
U.GREY_MAX = 0.75
U.OPAQUE = 0.9

local function Lin(c)
    c = math.max(0, math.min(1, tonumber(c) or 0))
    if c <= 0.03928 then return c / 12.92 end
    return ((c + 0.055) / 1.055) ^ 2.4
end
function U.Luminance(c) return 0.2126 * Lin(c[1]) + 0.7152 * Lin(c[2]) + 0.0722 * Lin(c[3]) end
function U.Contrast(a, b)
    local la, lb = U.Luminance(a), U.Luminance(b)
    if la < lb then la, lb = lb, la end
    return (la + 0.05) / (lb + 0.05)
end
function U.IsGrey(c)
    local mx = math.max(c[1], c[2], c[3])
    local mn = math.min(c[1], c[2], c[3])
    return mx - mn <= U.GREY_SPREAD and mx < U.GREY_MAX
end
local function Mix(bg, c, a)
    a = math.max(0, math.min(1, tonumber(a) or 1))
    return { bg[1] * (1 - a) + c[1] * a, bg[2] * (1 - a) + c[2] * a, bg[3] * (1 - a) + c[3] * a }
end
U.Mix = Mix

-- sichtbare Textstücke mit ihrer Farbe (|cAARRGGBB … |r; dazwischen die Grundfarbe). Symbole und Verweise entfernt.
function U.Segments(text, base)
    local out = {}
    text = tostring(text or ""):gsub("|T.-|t", " "):gsub("|H.-|h(.-)|h", "%1"):gsub("|n", "\n")
    local cur, i, n = base, 1, #text
    local buf = {}
    local function flush()
        local t = table.concat(buf)
        if t:find("%S") then out[#out + 1] = { text = t, color = cur } end
        buf = {}
    end
    while i <= n do
        local hex = text:match("^|c(%x%x%x%x%x%x%x%x)", i)
        if hex then
            flush()
            cur = { tonumber(hex:sub(3, 4), 16) / 255, tonumber(hex:sub(5, 6), 16) / 255, tonumber(hex:sub(7, 8), 16) / 255 }
            i = i + 10
        elseif text:sub(i, i + 1) == "|r" then
            flush(); cur = base; i = i + 2
        elseif text:sub(i, i + 1) == "||" then
            buf[#buf + 1] = "|"; i = i + 2
        else
            buf[#buf + 1] = text:sub(i, i); i = i + 1
        end
    end
    flush()
    return out
end

-- Regeln auf einen Text anwenden (ohne Fenster – auch für die Gegenproben im Nachbau, TK27)
-- t = { text, color, bg, bgWhite, edge (Kontur/Schatten), opaque, size, ref, justify }
function U.ReadRules(t)
    local found = {}
    for _, seg in ipairs(U.Segments(t.text, t.color)) do
        local c = U.Contrast(seg.color, t.bg)
        if t.opaque and t.bgWhite then c = math.min(c, U.Contrast(seg.color, t.bgWhite)) end
        if c < U.CONTRAST_MIN then
            found[#found + 1] = string.format("L1 Kontrast %.1f:1 < %.1f:1 '%s'", c, U.CONTRAST_MIN, seg.text:sub(1, 30))
        end
        if seg.text:find("%d") and U.IsGrey(seg.color) then
            found[#found + 1] = string.format("L1 graue Zahl '%s'", seg.text:sub(1, 30))
        end
    end
    if not t.opaque and not t.edge then found[#found + 1] = "L1 ohne Kontur/Schatten auf durchsichtigem Hintergrund" end
    local plain = tostring(t.text or ""):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
    if plain:find("%(%s*[%d%.,]+%s*[kKM%%]?%s*%)") then
        found[#found + 1] = string.format("L6 Zahl in Klammern ohne Wort '%s'", plain:sub(1, 30))
    end
    if (plain:find("|TInterface\\MoneyFrame", 1, true) or plain:find("%d+g %d+s") or plain:find("%d+s %d+k")) and t.justify ~= "RIGHT" then
        found[#found + 1] = "L2 Geldbetrag nicht rechtsbündig"
    end
    if t.size and t.ref and t.size < t.ref - 0.05 then
        found[#found + 1] = string.format("L8 Schrift %.1f < %.1f (GameFontNormalSmall)", t.size, t.ref)
    end
    return found
end

local function FontRef()
    local o = rawget(_G, "GameFontNormalSmall")
    if o and o.GetFont then
        local _, size = o:GetFont()
        if type(size) == "number" and size > 0 then return size end
    end
end

-- Hintergrund unter einem Text: Backdrops der Vorfahren bis zum Fenster (von aussen nach innen)
local function Background(fs, root, edge)
    local chain, p = {}, fs:GetParent()
    for _ = 1, 15 do
        if not p then break end
        table.insert(chain, 1, p)
        if p == root then break end
        p = p.GetParent and p:GetParent()
    end
    local black, white, cover = { 0, 0, 0 }, { 1, 1, 1 }, 0
    for _, f in ipairs(chain) do
        if f.GetBackdrop and f.GetBackdropColor and f:GetBackdrop() then
            local r, g, b, a = f:GetBackdropColor()
            if type(r) == "number" and not secret(r) then
                a = a or 1
                black, white = Mix(black, { r, g, b }, a), Mix(white, { r, g, b }, a)
                cover = 1 - (1 - cover) * (1 - a)
            end
        end
        if not edge and f.IsObjectType and f:IsObjectType("StatusBar") and f.GetStatusBarColor then
            local r, g, b, a = f:GetStatusBarColor()
            if type(r) == "number" and not secret(r) then
                black, white = Mix(black, { r, g, b }, a or 1), Mix(white, { r, g, b }, a or 1)
            end
        end
    end
    return black, white, cover
end

-- TK24: alle sichtbaren eigenen Texte nach L1/L2/L6/L8
function U.Readable()
    local problems, tested = {}, 0
    local ref = FontRef()
    for _, e in ipairs(ns.uiFrames) do
        if U.ReallyVisible(e.frame) then
            local list = { e.frame }
            for _, d in ipairs(U.Descendants(e.frame)) do list[#list + 1] = d end
            local rootScale = e.frame.GetEffectiveScale and e.frame:GetEffectiveScale() or 1
            for _, f in ipairs(list) do
                for _, r in ipairs(f.GetRegions and { f:GetRegions() } or {}) do
                    if r.IsObjectType and r:IsObjectType("FontString") and r.IsVisible and r:IsVisible()
                        and (not r.GetEffectiveAlpha or r:GetEffectiveAlpha() > 0.05) then
                        local text = r:GetText()
                        if text and not secret(text) and text ~= "" then
                            tested = tested + 1
                            local cr, cg, cb = r:GetTextColor()
                            local _, size, flags = r:GetFont()
                            local sx, sy = 0, 0
                            if r.GetShadowOffset then sx, sy = r:GetShadowOffset() end
                            local sa = 0
                            if r.GetShadowColor then sa = select(4, r:GetShadowColor()) or 0 end
                            local edge = (type(flags) == "string" and flags:find("OUTLINE") ~= nil)
                                or ((sx or 0) ~= 0 or (sy or 0) ~= 0) and sa > 0
                            local black, white, cover = Background(r, e.frame, edge)
                            local scale = (r.GetEffectiveScale and r:GetEffectiveScale() or rootScale) / rootScale
                            local found = U.ReadRules({
                                text = text, color = { cr or 1, cg or 1, cb or 1 }, bg = black, bgWhite = white,
                                opaque = cover >= U.OPAQUE, edge = edge, size = size and size * scale or nil, ref = ref,
                                justify = r.GetJustifyH and r:GetJustifyH() or nil })
                            for _, msg in ipairs(found) do problems[#problems + 1] = e.name .. ": " .. msg end
                        end
                    end
                end
            end
        end
    end
    return problems, tested
end

-- TK25: jedes sichtbare eigene Fenster hat beim Zeigen einen freien Platz gefunden (oder es gab beweisbar keinen)
function U.AvoidWorks()
    local problems, tested = {}, 0
    for _, e in ipairs(ns.uiFrames) do
        if not e.hud and Shown(e.frame) then
            tested = tested + 1
            ns.UIAvoidOthers(e.frame)
            local last = ns.UIAvoidLast
            if last and not last.free then
                problems[#problems + 1] = e.name .. " kein freier Platz (" .. table.concat(last.by or {}, ", ") .. ")"
            end
        end
    end
    return problems, tested
end

-- TK28: Inhalts-Regeln L3/L4/L5/L7, vom Addon mit ns.ReadCheck angemeldet
function U.ContentRules()
    local problems = {}
    for _, p in ipairs(ns.readChecks) do
        local ok, good, got, want = pcall(p.fn)
        if not ok then problems[#problems + 1] = p.name .. ": Lua-Fehler " .. tostring(good)
        elseif good ~= true then problems[#problems + 1] = p.name .. ": " .. tostring(got) .. " (erwartet " .. tostring(want) .. ")" end
    end
    return problems, #ns.readChecks
end

-- Beispiel für TK22 (ein Wert, den jedes Addon hat): Stufe des Charakters
ns.Plausible("Stufe des Charakters", function()
    local lvl = UnitLevel and UnitLevel("player")
    if type(lvl) ~= "number" or (ns.G and ns.G.IsSecret and ns.G.IsSecret(lvl)) then return true, "nicht lesbar" end
    return lvl >= 1 and lvl <= 100, lvl, "1–100"
end)
