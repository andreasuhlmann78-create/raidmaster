-- RaidMaster - Bereitschafts-Check mit Vorbereitung
-- Die Raidleitung klickt "Bereitschaft prüfen" (Boss-Leiste oder Seite Raid). RaidMaster prüft:
--   * bei allen (auch ohne Addon, über die Buffs im Raid): Fläschchen und Elixiere
--   * bei Addon-Nutzern zusätzlich: Feuerwiderstand, Klassen-Reagenzien (Ankh, Seelensplitter, Kerzen,
--     Arkanes Pulver, Wildwurzel, Symbol der Könige, Munition) und die Haltbarkeit der Ausrüstung
-- Weltbuffs werden bewusst nicht geprüft (in WoW Forever im Raid nicht nutzbar).
-- Ergebnis: Fenster mit allen Spielern; "Fehlendes ansagen" schreibt die Lücken in den Raidchat.
-- Auf Wunsch startet gleichzeitig der Bereitschaftscheck des Spiels.

local ADDON, RM = ...
local L = RM.L
local R = {}
RM.Ready = R

R.WAIT = 5                -- so lange auf Antworten warten (Sek.)
R.DURABILITY_WARN = 30    -- unter diesem Wert (%) gilt die Ausrüstung als kaputt

-- Fläschchen und Elixiere (Classic-Zauber-IDs der Buffs); dazu zählt jeder Buff mit "Fläschchen"/"Flask" im Namen
R.FLASKS = { [17626] = true, [17627] = true, [17628] = true, [17629] = true, [17624] = true }
R.ELIXIRS = {
	[17538] = true, [11405] = true, [17539] = true, [11474] = true, [26276] = true, [11390] = true, [3593] = true,
	[11348] = true, [24363] = true, [11334] = true, [17535] = true, [21920] = true, [7844] = true, [24361] = true,
	[11396] = true, [17537] = true, [11371] = true, [16323] = true, [16329] = true,
}
-- Klassen-Reagenzien: Item-ID, Name (Fallback), Mindestanzahl
R.REAGENTS = {
	PRIEST  = { { 17029, "Heilige Kerze", 5 } },
	MAGE    = { { 17020, "Arkanes Pulver", 20 } },
	DRUID   = { { 17026, "Wilder Dornwurz", 10 }, { 17038, "Eisenholzsamen", 1 } },
	PALADIN = { { 21177, "Symbol der Könige", 20 } },
	SHAMAN  = { { 17030, "Ankh", 1 } },
	WARLOCK = { { 6265, "Seelensplitter", 5 } },
	HUNTER  = { { 0, "Munition", 1000 } },      -- 0 = Munitionsplatz
}

R.results = {}            -- Name -> { flask, elixirs, fr, reagents = { {name, have, need} }, dur, addon, at }
R.checkId = nil
R.started = 0

local function C() return RM.db.config end

---------------------------------------------------------------------------
-- Eigener Stand (für die Antwort)
---------------------------------------------------------------------------
local function AuraInfo(unit)
	local flask, elixirs = nil, 0
	if not UnitAura then return flask, elixirs end
	for i = 1, 40 do
		local name, _, _, _, _, _, _, _, _, spellId = UnitAura(unit, i, "HELPFUL")
		if not name then break end
		local lname = name:lower()
		if R.FLASKS[spellId] or lname:find("flask", 1, true) or lname:find((L["Fläschchen"]):lower(), 1, true) then
			flask = name
		elseif R.ELIXIRS[spellId] or lname:find("elixir", 1, true) or lname:find((L["Elixier"]):lower(), 1, true) then
			elixirs = elixirs + 1
		end
	end
	return flask, elixirs
end
R.AuraInfo = AuraInfo

function R.MyStatus()
	local _, class = UnitClass("player")
	local flask, elixirs = AuraInfo("player")
	local fr
	if UnitResistance then fr = select(2, UnitResistance("player", 2)) end
	local reagents = {}
	for _, r in ipairs(R.REAGENTS[class] or {}) do
		local have
		if r[1] == 0 then
			have = GetInventoryItemCount and GetInventoryItemCount("player", 0) or 0
		else
			have = GetItemCount and GetItemCount(r[1]) or 0
		end
		local name = (r[1] > 0 and (RM.GetItemInfo or GetItemInfo)(r[1])) or L[r[2]]
		reagents[#reagents + 1] = { name, have or 0, r[3] }
	end
	local dur = 100
	if GetInventoryItemDurability then
		for slot = 1, 18 do
			local cur, max = GetInventoryItemDurability(slot)
			if cur and max and max > 0 then dur = math.min(dur, math.floor(cur / max * 100)) end
		end
	end
	return { f = flask, e = elixirs, fr = fr, rg = reagents, du = dur }
end

---------------------------------------------------------------------------
-- Abfrage
---------------------------------------------------------------------------
local function UnitFor(name)
	for _, m in ipairs(RM.RaidMembers()) do
		if m.name == name then return "raid" .. m.index end
	end
end

function R.Start()
	if not RM.InRaid() then RM.Print(L["Der Bereitschafts-Check geht nur im Raid."]) return end
	if not (RM.IsAssist() or RM.CanEdit()) then RM.Print(L["Den Bereitschafts-Check starten Raidleiter und Assistenten."]) return end
	R.checkId = tostring(GetServerTime()) .. math.random(100, 999)
	R.started = GetTime()
	wipe(R.results)
	-- alle Raidmitglieder: Buffs selbst prüfen (geht auch ohne Addon)
	for _, m in ipairs(RM.RaidMembers()) do
		local unit = (m.name == RM.Me()) and "player" or ("raid" .. m.index)
		local flask, elixirs = AuraInfo(unit)
		R.results[m.name] = { class = m.class, flask = flask, elixirs = elixirs, addon = false, online = m.online }
	end
	-- eigener vollständiger Stand
	R.OnAnswer(RM.Me(), { id = R.checkId, s = R.MyStatus() })
	RM.Comm.Send("RDYQ", { id = R.checkId }, "RAID", nil, true)
	if C().readyCheckGame ~= false and DoReadyCheck and (RM.IsLeader() or RM.IsAssist()) and not (RM.Test and RM.Test.active) then
		pcall(DoReadyCheck)
	end
	if R.SimulateAnswers then R.SimulateAnswers(R.checkId) end
	RM.Print(L["Bereitschafts-Check läuft – Ergebnis in wenigen Sekunden."])
	C_Timer.After(R.WAIT, function() R.Show() end)
	RM.Fire("READY_CHANGED")
end

function R.OnAnswer(sender, d)
	if not d or d.id ~= R.checkId or type(d.s) ~= "table" then return end
	local name = RM.Short(sender)
	local r = R.results[name] or {}
	local s = d.s
	r.addon = true
	r.flask = s.f or r.flask
	r.elixirs = math.max(r.elixirs or 0, tonumber(s.e) or 0)
	r.fr = tonumber(s.fr)
	r.dur = tonumber(s.du)
	r.reagents = {}
	for _, x in ipairs(type(s.rg) == "table" and s.rg or {}) do
		if type(x) == "table" then r.reagents[#r.reagents + 1] = { tostring(x[1]), tonumber(x[2]) or 0, tonumber(x[3]) or 0 } end
	end
	R.results[name] = r
	RM.Fire("READY_CHANGED")
end

RM.Comm.Register("RDYQ", function(sender, d, channel)
	if not d.id then return end
	RM.Comm.Send("RDYA", { id = d.id, s = R.MyStatus() }, "WHISPER", sender)
end)
RM.Comm.Register("RDYA", function(sender, d) R.OnAnswer(sender, d) end)

---------------------------------------------------------------------------
-- Auswertung
---------------------------------------------------------------------------
-- Probleme eines Spielers: Liste kurzer Texte
function R.Problems(name, r)
	local out = {}
	if r.online == false then out[#out + 1] = L["offline"] return out end
	if not r.flask then out[#out + 1] = L["kein Fläschchen"] end
	if (r.elixirs or 0) == 0 then out[#out + 1] = L["keine Elixiere"] end
	local frMin = tonumber(C().fireResMin) or 0
	if frMin > 0 and r.fr and r.fr < frMin then out[#out + 1] = string.format(L["Feuerwid. %d"], r.fr) end
	for _, x in ipairs(r.reagents or {}) do
		if x[2] < x[3] then out[#out + 1] = string.format("%s %d/%d", x[1], x[2], x[3]) end
	end
	if r.dur and r.dur < R.DURABILITY_WARN then out[#out + 1] = string.format(L["Haltbarkeit %d %%"], r.dur) end
	return out
end

-- Zusammenfassung für den Raidchat: { "Ohne Fläschchen: A, B", ... }
function R.Summary()
	local groups = {}
	local order = {}
	local function add(key, name)
		if not groups[key] then groups[key] = {}; order[#order + 1] = key end
		table.insert(groups[key], name)
	end
	local names = {}
	for n in pairs(R.results) do names[#names + 1] = n end
	table.sort(names)
	local frMin = tonumber(C().fireResMin) or 0
	for _, n in ipairs(names) do
		local r = R.results[n]
		if r.online ~= false then
			if not r.flask then add(L["Ohne Fläschchen"], n) end
			if (r.elixirs or 0) == 0 then add(L["Ohne Elixiere"], n) end
			if frMin > 0 and r.fr and r.fr < frMin then add(string.format(L["Feuerwiderstand unter %d"], frMin), n .. " (" .. r.fr .. ")") end
			local miss = {}
			for _, x in ipairs(r.reagents or {}) do
				if x[2] < x[3] then miss[#miss + 1] = x[1] end
			end
			if #miss > 0 then add(L["Reagenzien fehlen"], n .. " (" .. table.concat(miss, ", ") .. ")") end
			if r.dur and r.dur < R.DURABILITY_WARN then add(L["Ausrüstung reparieren"], n .. " (" .. r.dur .. " %)") end
			if not r.addon then add(L["Ohne RaidMaster (nur Buffs geprüft)"], n) end
		end
	end
	local lines = {}
	for _, k in ipairs(order) do lines[#lines + 1] = k .. ": " .. table.concat(groups[k], ", ") end
	return lines
end

function R.Announce()
	local lines = R.Summary()
	if #lines == 0 then
		RM.RaidChat(L["[RaidMaster] Bereitschaft: alle vorbereitet. Viel Erfolg!"], "RAID")
		return
	end
	RM.RaidChat(L["[RaidMaster] Bereitschafts-Check:"], "RAID")
	for i, l in ipairs(lines) do
		if #l > 250 then l = l:sub(1, 247) .. "..." end
		C_Timer.After(i * 0.3, function() RM.RaidChat(l, "RAID") end)
	end
end

---------------------------------------------------------------------------
-- Fenster
---------------------------------------------------------------------------
local win

local function Create()
	local UI = RM.UI
	local W = 620
	local f = UI.Frame(UIParent, W, 470)
	UI.Skin(f)
	f:SetFrameStrata("HIGH")
	f:SetClampedToScreen(true)
	UI.MakeMovable(f, "ready", "CENTER", 0, 60)
	_G.RaidMasterReadyFrame = f
	if UISpecialFrames then tinsert(UISpecialFrames, "RaidMasterReadyFrame") end
	local title = UI.Header(f, L["Bereitschafts-Check"])
	title:SetPoint("TOPLEFT", 14, -12)
	local close = UI.CloseButton(f, function() f:Hide() end)
	close:SetPoint("TOPRIGHT", -8, -8)
	f.info = UI.Text(f, "", 11)
	f.info:SetPoint("TOPLEFT", 14, -38)
	f.info:SetWidth(W - 28)
	f.list = UI.List(f, W - 28, 330, {
		{ title = L["Name"], width = 120 },
		{ title = L["Fläschchen"], width = 90 },
		{ title = L["Elixiere"], width = 55, justify = "CENTER" },
		{ title = L["Feuerwid."], width = 65, justify = "CENTER" },
		{ title = L["Haltbarkeit"], width = 70, justify = "CENTER" },
		{ title = L["Fehlt"], width = 170 },
	}, { emptyText = L["Noch kein Check gelaufen."] })
	f.list:SetPoint("TOPLEFT", 14, -60)
	local again = UI.Button(f, L["Erneut prüfen"], 150, 28, function() R.Start() end)
	again:SetPoint("BOTTOMLEFT", 14, 14)
	local ann = UI.Button(f, L["Fehlendes ansagen"], 170, 28, function() R.Announce() end,
		L["Schreibt die Lücken in den Raidchat (z. B. 'Ohne Fläschchen: A, B')."])
	ann:SetPoint("LEFT", again, "RIGHT", 8, 0)
	ann:SetAccent(true)
	f:Hide()
	return f
end

function R.Refresh()
	if not win or not win:IsShown() then return end
	local names = {}
	for n in pairs(R.results) do names[#names + 1] = n end
	table.sort(names, function(a, b)
		local pa, pb = #R.Problems(a, R.results[a]), #R.Problems(b, R.results[b])
		if pa ~= pb then return pa > pb end
		return a < b
	end)
	local data, ok, withAddon = {}, 0, 0
	for _, n in ipairs(names) do
		local r = R.results[n]
		local probs = R.Problems(n, r)
		if #probs == 0 then ok = ok + 1 end
		if r.addon then withAddon = withAddon + 1 end
		data[#data + 1] = {
			key = n,
			cells = { RM.ClassColor(r.class, n), r.flask or "–", tostring(r.elixirs or 0), r.fr and tostring(r.fr) or "?",
				r.dur and (r.dur .. " %") or "?", #probs > 0 and table.concat(probs, ", ") or L["alles da"] },
			colors = { nil, r.flask and { 0.4, 1, 0.4 } or { 1, 0.4, 0.4 }, (r.elixirs or 0) > 0 and { 0.4, 1, 0.4 } or { 1, 0.6, 0.3 },
				nil, (r.dur and r.dur < R.DURABILITY_WARN) and { 1, 0.4, 0.4 } or nil, #probs > 0 and { 1, 0.8, 0.3 } or { 0.4, 1, 0.4 } },
		}
	end
	win.list:SetData(data)
	win.info:SetText(string.format(L["%d Spieler · %d vollständig vorbereitet · %d mit RaidMaster (Feuerwiderstand, Reagenzien, Haltbarkeit). Weltbuffs werden nicht geprüft."],
		#names, ok, withAddon))
end

function R.Show()
	win = win or Create()
	win:Show()
	R.Refresh()
end

RM.Listen("READY_CHANGED", function() R.Refresh() end)
