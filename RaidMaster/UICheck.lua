-- RaidMaster - Prüfung der Oberfläche im echten Client (Testroutine, Bereich K, ab 3.0.18)
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- Anlass (Live-Test 5. Nov. 2026): eigene Tooltips verdeckten Knöpfe, Fenster lagen übereinander, Anzeigen rechneten
-- mit falschen Spielwerten, ein Fehler kam 588×. Offline sieht man das nicht – darum prüft die Testroutine es im
-- Spiel selbst. Nur lesen, nichts verändern. Übernommen aus der Vorlage (shared/vorlage/__ADDON__/UICheck.lua).
--
-- Benutzung im eigenen Code:
--   RM.RegisterUI(frame, "Name")       -- eigenes Fenster anmelden (UI.Frame(UIParent, w, h, "Name") macht das selbst)
--   RM.Plausible("Name", function() return gut, wert, erwartet end)   -- Spielwert-Prüfung (Fall T159)
-- Andere GoldSentinel-Addons melden ihre Fenster in der globalen Liste GoldSentinelUIFrames an (T156 prüft gegeneinander).

local ADDON, RM = ...

RM.uiFrames = RM.uiFrames or {}
RM.plausible = RM.plausible or {}
RM.UI_LOOP_LIMIT = 10                      -- dieselbe Fehlermeldung öfter -> Fehlerschleife (T160)

-- Blizzard-Fenster, die GoldSentinel-Fenster nicht überdecken dürfen
RM.UI_BLIZZARD = { "ProfessionsFrame", "TradeSkillFrame", "CraftFrame", "MerchantFrame", "AuctionHouseFrame",
                   "AuctionFrame", "MailFrame", "QuestLogFrame", "WorldMapFrame", "CharacterFrame" }

GoldSentinelUIFrames = GoldSentinelUIFrames or {}

function RM.RegisterUI(frame, name)
	if not frame then return end
	for _, e in ipairs(RM.uiFrames) do if e.frame == frame then return end end
	local e = { frame = frame, name = name or (frame.GetName and frame:GetName()) or ADDON }
	RM.uiFrames[#RM.uiFrames + 1] = e
	GoldSentinelUIFrames[#GoldSentinelUIFrames + 1] = { frame = frame, name = e.name, addon = ADDON }
end

function RM.Plausible(name, fn) RM.plausible[#RM.plausible + 1] = { name = name, fn = fn } end

local U = {}
RM.UICheck = U

-- Ist der echte Client da (Rechtecke, Kinder, Tooltip)? Sonst werden die Fälle ehrlich übersprungen.
function U.Available()
	local f = RM.uiFrames[1] and RM.uiFrames[1].frame
	return f and type(f.GetRect) == "function" and type(f.GetChildren) == "function" and type(f.IsVisible) == "function"
		and type(GameTooltip) == "table" and type(GameTooltip.GetRect) == "function"
		and type(UIParent) == "table" and type(UIParent.GetRect) == "function" and true or false
end

function U.Rect(f)
	if not (f and f.GetRect) then return nil end
	local ok, l, b, w, h = pcall(f.GetRect, f)
	if not ok or type(l) ~= "number" or type(w) ~= "number" or w <= 0 or h <= 0 then return nil end
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

local function Shown(f) return f and f.IsVisible and f:IsVisible() and true or false end

local function Name(f)
	local n = f and f.GetName and f:GetName()
	if n then return n end
	local t = f and f.label and f.label.GetText and f.label:GetText()
	if not t and f and f.GetText then t = f:GetText() end
	if type(t) == "string" and t ~= "" then return "'" .. t:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "") .. "'" end
	return tostring(f and f.GetObjectType and f:GetObjectType() or "?")
end
U.Name = Name

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

-- Fall 1 (T155): kein eigener Tooltip verdeckt einen Knopf oder ein Eingabefeld desselben Fensters
function U.TooltipsCoverNothing()
	local problems, tested = {}, 0
	for _, e in ipairs(RM.uiFrames) do
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
								problems[#problems + 1] = e.name .. ": " .. Name(el) .. " verdeckt " .. Name(other)
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

-- Fall 2 (T156): eigene sichtbare Fenster überdecken weder Blizzard-Fenster noch Fenster anderer GoldSentinel-Addons
function U.WindowsOverlapNothing()
	local problems, tested = {}, 0
	for _, e in ipairs(RM.uiFrames) do
		local mine = Shown(e.frame) and U.Rect(e.frame)
		if mine then
			for _, bn in ipairs(RM.UI_BLIZZARD) do
				local bf = _G[bn]
				if type(bf) == "table" and Shown(bf) then
					tested = tested + 1
					if U.Overlap(mine, U.Rect(bf)) > 0 then problems[#problems + 1] = e.name .. " überdeckt " .. bn end
				end
			end
			for _, o in ipairs(GoldSentinelUIFrames) do
				if o.addon ~= ADDON and Shown(o.frame) then
					tested = tested + 1
					if U.Overlap(mine, U.Rect(o.frame)) > 0 then
						problems[#problems + 1] = e.name .. " überdeckt " .. tostring(o.name) .. " (" .. tostring(o.addon) .. ")"
					end
				end
			end
		end
	end
	return problems, tested
end

-- Fall 3 (T157): sichtbare Fenster und eigene Tooltips liegen ganz im Bildschirm
function U.InsideScreen()
	local problems, tested, screen = {}, 0, U.Rect(UIParent)
	local function Inside(r) return r.l >= screen.l - 1 and r.b >= screen.b - 1 and r.r <= screen.r + 1 and r.t <= screen.t + 1 end
	if not screen then return problems, tested end
	for _, e in ipairs(RM.uiFrames) do
		local r = Shown(e.frame) and U.Rect(e.frame)
		if r then
			tested = tested + 1
			if not Inside(r) then problems[#problems + 1] = e.name .. " ragt aus dem Bildschirm" end
			-- Tooltips der Knöpfe dieses Fensters (Stichprobe: die ersten 40)
			local n = 0
			for _, el in ipairs(U.Descendants(e.frame)) do
				local enter = n < 40 and el.GetScript and el:GetScript("OnEnter")
				if enter then
					n = n + 1
					pcall(enter, el)
					local tip = Shown(GameTooltip) and U.Rect(GameTooltip)
					if tip then
						tested = tested + 1
						if not Inside(tip) then problems[#problems + 1] = e.name .. ": Tooltip von " .. Name(el) .. " ragt aus dem Bildschirm" end
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

-- Fall 4 (T158): Beschriftungen von Knöpfen nicht abgeschnitten (andere Texte nur als Hinweis)
function U.TextFits()
	local problems, hints, tested = {}, {}, 0
	local function Truncated(fs)
		if not (fs and fs.IsTruncated and Shown(fs)) then return nil end
		local ok, cut = pcall(fs.IsTruncated, fs)
		return ok and cut and true or false
	end
	for _, e in ipairs(RM.uiFrames) do
		if Shown(e.frame) then
			for _, el in ipairs(U.Descendants(e.frame)) do
				local label = el.label or (el.GetFontString and el:GetFontString())
				if IsControl(el) and label then
					local cut = Truncated(label)
					if cut ~= nil then
						tested = tested + 1
						if cut then problems[#problems + 1] = e.name .. ": " .. Name(el) .. " Beschriftung abgeschnitten" end
					end
				end
				for _, region in ipairs(el.GetRegions and { el:GetRegions() } or {}) do
					if region ~= label and region.IsObjectType and region:IsObjectType("FontString") then
						local cut = Truncated(region)
						if cut ~= nil then
							tested = tested + 1
							if cut and #hints < 15 then hints[#hints + 1] = e.name .. ": Text gekürzt bei " .. Name(el) end
						end
					end
				end
			end
		end
	end
	return problems, tested, hints
end

-- Fall 5 (T159): angezeigte Spielwerte plausibel (Prüfungen meldet das Addon mit RM.Plausible an)
function U.ValuesPlausible()
	local problems, infos = {}, {}
	for _, p in ipairs(RM.plausible) do
		local ok, good, got, want = pcall(p.fn)
		if not ok then problems[#problems + 1] = p.name .. ": Lua-Fehler " .. tostring(good)
		elseif good == false then problems[#problems + 1] = p.name .. ": " .. tostring(got) .. " (erwartet " .. tostring(want) .. ")"
		elseif got ~= nil then infos[#infos + 1] = p.name .. " " .. tostring(got) end
	end
	return problems, #RM.plausible, infos
end

-- Fall 6 (T160): keine Fehlerschleife – dieselbe Meldung höchstens UI_LOOP_LIMIT× in der Sitzung
-- (Diagnose von RaidMaster und Fehler-Abgriff von GoldSentinelTest; absichtliche Testfehler zählen nicht)
function U.NoErrorLoops()
	local problems, n = {}, 0
	local function Check(msg, count)
		n = n + 1
		msg = tostring(msg)
		if (tonumber(count) or 1) > RM.UI_LOOP_LIMIT and not msg:find("RaidMaster-Testfehler", 1, true) then
			problems[#problems + 1] = tostring(count) .. "× " .. msg:sub(1, 120)
		end
	end
	for _, e in ipairs(RM.Diag and RM.Diag.errors or {}) do Check(e.msg, e.n) end
	local s = type(RaidMasterDB) == "table" and RaidMasterDB.gsTest
	for _, e in pairs(type(s) == "table" and type(s.errors) == "table" and s.errors or {}) do
		if type(e) == "table" then Check(e.msg, e.count) end
	end
	return problems, n
end

---------------------------------------------------------------------------
-- Spielwerte, die RaidMaster liest und anzeigt (Fall 5)
---------------------------------------------------------------------------
local function Secret(v) return RM.IsSecret and RM.IsSecret(v) end

RM.Plausible("Stufe des Charakters", function()
	local lvl = UnitLevel and UnitLevel("player")
	if type(lvl) ~= "number" or Secret(lvl) then return true, "nicht lesbar" end
	return lvl >= 1 and lvl <= 100, lvl, "1–100"
end)

RM.Plausible("Eigener Name (ohne Realm)", function()
	local me = RM.Me and RM.Me()
	if me == nil then return true, "nicht lesbar" end
	return type(me) == "string" and me ~= "" and not me:find("-", 1, true), me ~= "" and "ok" or "leer", "Name ohne Realm"
end)

RM.Plausible("Gilde wie im Spiel", function()
	if not (IsInGuild and GetGuildInfo and RM.MyGuild) then return true, "nicht lesbar" end
	local g = IsInGuild() and GetGuildInfo("player") or nil
	if g == nil or Secret(g) then return true, "keine Gilde" end
	return RM.MyGuild() == g, RM.MyGuild() == g and "ok" or "anders", "gleich wie GetGuildInfo"
end)

-- gespeicherte Berufsfertigkeit (Seite Berufe) gegen die Fertigkeit im Spiel: gelernt -> nicht 0
RM.Plausible("Berufsfertigkeit", function()
	local P = RM.Prof
	if not (P and P.ReadSkillLines and RM.db and type(RM.db.prof) == "table") then return true, "nicht lesbar" end
	local me = RM.Me and RM.Me()
	local mine = me and RM.db.prof[me]
	if type(mine) ~= "table" or type(mine.p) ~= "table" then return true, "noch nicht eingelesen" end
	local live = P.ReadSkillLines()
	local checked, bad = 0, {}
	for name, l in pairs(live) do
		local stored = mine.p[name]
		local r = tonumber(l.r) or 0
		if r > 0 and type(stored) == "table" and stored.r ~= nil then
			checked = checked + 1
			local sr = tonumber(stored.r) or 0
			local max = tonumber(l.m) or 0
			if sr <= 0 or (max > 0 and sr > max) then
				bad[#bad + 1] = name .. " " .. sr .. " statt " .. r
			end
		end
	end
	if #bad > 0 then return false, table.concat(bad, ", "), "> 0 und höchstens Maximum" end
	return true, checked .. " Berufe"
end)

RM.Plausible("Raidmitglieder", function()
	if not (GetNumGroupMembers and IsInRaid) then return true, "nicht lesbar" end
	if RM.Test and RM.Test.active then return true, "Testmodus (Testraid)" end
	local n = IsInRaid() and GetNumGroupMembers() or 0
	if Secret(n) then return true, "nicht lesbar" end
	local mine = RM.RaidMembers and #RM.RaidMembers() or 0
	if n == 0 then return true, "kein Raid" end
	return mine == n, mine, n
end)
