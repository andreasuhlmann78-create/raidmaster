-- RaidMaster - Boss-Leiste für die Raidleitung
-- Nimmt der Raidleiter (oder ein Assistent) einen Boss ins Ziel, erscheint eine kleine Leiste mit
-- dem Bossnamen und Knöpfen: mit einem Klick die Boss-Ansage als Schlachtzugwarnung (Taktik, Einlull-
-- bzw. Sheep-Rotation) und die Schlachtzugsymbole wie im Automatikmodus setzen (Totenkopf auf den Boss,
-- Adds nach der Vorlage des Bosses). Nichts davon läuft mehr von selbst – die Raidleitung entscheidet.
-- Im Testmodus kann das Test-Tool einen Boss "ins Ziel nehmen" (RM.BossBar.SetTestTarget).

local ADDON, RM = ...
local L = RM.L
local B = {}
RM.BossBar = B

local bar
B.current = nil       -- Encounter-ID des Bosses im Ziel
B.testTarget = nil    -- Encounter-ID, die das Test-Tool als Ziel vorgibt

local function C() return RM.db.config end

-- Bossname -> Boss (alle Sprachen, alle Raids dieser Spielversion)
local byName
local function NameIndex()
	if byName then return byName end
	byName = {}
	for id, b in pairs(RM.Data.Bosses or {}) do
		if id == b.id then
			for _, n in ipairs({ b.name, b.en, b.de }) do if n then byName[n:lower()] = b end end
			for _, n in pairs(b.names or {}) do byName[n:lower()] = b end
		end
	end
	return byName
end
RM.Listen("DB_READY", function() byName = nil end)

-- Welcher Boss ist im Ziel? (Ziel oder boss1–boss5 mit gleichem Namen)
function B.TargetBoss()
	if B.testTarget then return RM.Data.Bosses[B.testTarget] end
	if not UnitExists("target") or UnitIsPlayer("target") then return nil end
	local name = UnitName("target")
	if not name then return nil end
	return NameIndex()[name:lower()]
end

local function CanLead()
	if B.testTarget then return true end
	return RM.Markers and RM.Markers.IsMarkerLead() or false
end

---------------------------------------------------------------------------
-- Aktionen
---------------------------------------------------------------------------
-- Vorlage des Bosses wählen (wie "Vorlage beim Bosskampf automatisch wählen")
local function UseTemplate(boss)
	if boss and boss.template and C().markerTemplate ~= boss.template then
		C().markerTemplate = boss.template
		if RM.Markers then RM.Markers.ResetUsed() end
		RM.Fire("CONFIG_CHANGED")
	end
end

-- Symbole wie im Automatikmodus: Totenkopf auf den Boss (wenn die Vorlage ihn nicht für Adds braucht),
-- dann alle sichtbaren Adds nach der Vorlage
function B.MarkBoss(boss)
	boss = boss or B.TargetBoss()
	if not boss then return end
	UseTemplate(boss)
	local template = RM.Data.GetTemplate(C().markerTemplate)
	if B.testTarget then
		-- Testmodus: nichts im Spiel setzen, nur zeigen, was passieren würde
		local names = {}
		for _, i in ipairs(template.order or {}) do names[#names + 1] = RM.Data.MarkerNames[i] end
		RM.Print(string.format(L["Test: Symbole für %s – Vorlage '%s': %s"], boss.name, template.name, table.concat(names, ", ")))
		if template.note then RM.Print("  " .. template.note) end
		RM.Fire("BOSSBAR_ACTION", "mark", boss.id)
		return
	end
	if not (RM.Markers and RM.Markers.CanMark()) then return end
	local skullForAdds = false
	for _, i in ipairs(template.order or {}) do if i == 8 then skullForAdds = true end end
	if not skullForAdds and UnitExists("target") and not GetRaidTargetIndex("target") then
		SetRaidTarget("target", 8)
	end
	RM.Markers.MarkAdds()
	RM.Fire("BOSSBAR_ACTION", "mark", boss.id)
end

-- Boss-Ansage als Schlachtzugwarnung (Kurzinfo, Rotationen)
function B.Announce(boss)
	boss = boss or B.TargetBoss()
	if not boss then return end
	local info = RM.Data.BossInfo[boss.id]
	if not info then
		RM.Print(string.format(L["Für %s ist keine Kurzinfo hinterlegt."], boss.name))
		return
	end
	RM.Markers.PostBossInfo(boss.id, info)
	RM.Fire("BOSSBAR_ACTION", "announce", boss.id)
end

-- Ein Klick: Ansage + Symbole
function B.AnnounceAndMark(boss)
	boss = boss or B.TargetBoss()
	if not boss then return end
	B.Announce(boss)
	B.MarkBoss(boss)
end

-- Einteilung für diesen Boss (falls erstellt) im Raid ansagen
function B.PostAssignment(boss)
	boss = boss or B.TargetBoss()
	if not boss or not RM.Assign then return end
	for _, c in ipairs(RM.Assign.Contexts) do
		if c.enc == boss.id and RM.db.assign and RM.db.assign.ctx and RM.db.assign.ctx[c.key] then
			RM.Assign.Post(c.key)
			RM.Fire("BOSSBAR_ACTION", "assign", boss.id)
			return
		end
	end
	RM.Print(string.format(L["Für %s gibt es keine Einteilung (Seite Raidleiter > Einteilung)."], boss.name))
end

---------------------------------------------------------------------------
-- Leiste
---------------------------------------------------------------------------
local function Create()
	local UI = RM.UI
	local f = UI.Frame(UIParent, 330, 96)
	f:SetFrameStrata("MEDIUM")
	f:SetClampedToScreen(true)
	UI.Skin(f, nil, UI.COLORS.accent)
	UI.MakeMovable(f, "bossBar", "CENTER", 0, -170)
	f.title = UI.Text(f, "", 13, UI.COLORS.accent[1], UI.COLORS.accent[2], UI.COLORS.accent[3])
	f.title:SetPoint("TOPLEFT", 10, -7)
	f.sub = UI.Text(f, "", 10, unpack(UI.COLORS.muted))
	f.sub:SetPoint("TOPRIGHT", -10, -9)
	local one = UI.Button(f, L["Ansage + Symbole"], 132, 26, function() B.AnnounceAndMark() end,
		L["Ein Klick: Boss-Ansage als Schlachtzugwarnung (Taktik, Rotationen) und Schlachtzugsymbole wie im Automatikmodus (Totenkopf auf den Boss, Adds nach Vorlage)."])
	one:SetPoint("BOTTOMLEFT", 8, 40)
	one:SetAccent(true)
	local ann = UI.Button(f, L["Ansage"], 58, 26, function() B.Announce() end, L["Nur die Boss-Ansage als Schlachtzugwarnung."])
	ann:SetPoint("LEFT", one, "RIGHT", 4, 0)
	local mark = UI.Button(f, L["Symbole"], 62, 26, function() B.MarkBoss() end, L["Nur die Schlachtzugsymbole nach der Vorlage des Bosses setzen."])
	mark:SetPoint("LEFT", ann, "RIGHT", 4, 0)
	local asg = UI.Button(f, L["Einteil."], 56, 26, function() B.PostAssignment() end, L["Einteilung für diesen Boss im Raid ansagen (falls erstellt)."])
	asg:SetPoint("LEFT", mark, "RIGHT", 4, 0)
	-- zweite Reihe: Pull- und Pausen-Timer (auch für DBM/BigWigs), Bereitschafts-Check
	local pull = UI.Button(f, L["Pull"], 70, 26, function()
		if RM.Timer.Running("pull") then RM.Timer.Cancel() else RM.Timer.Pull() end
	end, L["Pull-Timer starten (Sekunden: Seite Raidleiter > Raid). Nochmal klicken bricht ab.\nGeht auch an Deadly Boss Mods und BigWigs."])
	pull:SetPoint("BOTTOMLEFT", 8, 8)
	f.pull = pull
	local brk = UI.Button(f, L["Pause"], 70, 26, function()
		if RM.Timer.Running("break") then RM.Timer.Cancel() else RM.Timer.Break() end
	end, L["Pausen-Timer starten (Minuten: Seite Raidleiter > Raid). Nochmal klicken beendet die Pause."])
	brk:SetPoint("LEFT", pull, "RIGHT", 4, 0)
	f.brk = brk
	local rdy = UI.Button(f, L["Bereitschaft"], 166, 26, function() RM.Ready.Start() end,
		L["Bereitschafts-Check: Fläschchen, Elixiere, Feuerwiderstand, Reagenzien, Haltbarkeit."])
	rdy:SetPoint("LEFT", brk, "RIGHT", 4, 0)
	f:Hide()
	return f
end

function B.Update()
	if not RM.db then return end
	local boss = (C().bossBar ~= false) and CanLead() and B.TargetBoss() or nil
	B.current = boss and boss.id or nil
	if not boss then
		if bar then bar:Hide() end
		return
	end
	bar = bar or Create()
	bar.title:SetText(boss.name)
	local template = RM.Data.GetTemplate(boss.template or C().markerTemplate)
	bar.sub:SetText((B.testTarget and (L["TEST"] .. " · ") or "") .. (template and template.name or ""))
	local secs = tonumber(C().pullSeconds) or 10
	bar.pull:SetText(RM.Timer.Running("pull") and L["Abbrechen"] or (L["Pull"] .. " " .. secs))
	bar.brk:SetText(RM.Timer.Running("break") and L["Pause aus"] or (L["Pause"] .. " " .. (tonumber(C().breakMinutes) or 5)))
	bar:Show()
end

function B.SetTestTarget(encounterID)
	B.testTarget = encounterID
	B.Update()
end

RM.On("PLAYER_TARGET_CHANGED", function() B.Update() end)
RM.On("GROUP_ROSTER_UPDATE", function() B.Update() end)
RM.Listen("CONFIG_CHANGED", function() B.Update() end)
RM.Listen("LOGIN", function() B.Update() end)
RM.Listen("TIMER_CHANGED", function() B.Update() end)
