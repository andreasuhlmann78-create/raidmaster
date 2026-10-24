-- RaidMaster - Einlullender Schuss (Magmadar)
-- Fragt alle Jäger im Raid, ob sie Einlullender Schuss (Tranquilizing Shot) haben, und baut daraus
-- die Rotation für Magmadars Raserei.
--   * Jäger mit RaidMaster antworten automatisch (das Addon prüft das Zauberbuch)
--   * Jäger ohne Addon bekommen ein Flüstern und antworten mit "ja" oder "nein"
--   * Rotation: nur Jäger mit dem Schuss, in fester Reihenfolge; jeder bekommt seine Position geflüstert
-- In Classic Era / WoW Forever lernt man den Schuss aus dem Buch "Foliant: Einlullender Schuss"
-- (Beute im Geschmolzenen Kern, u. a. von Lucifron), ab TBC beim Lehrer. Abklingzeit in Classic: 20 Sek.

local ADDON, RM = ...
local L = RM.L
local Q = {}
RM.Tranq = Q

Q.SPELL = 19801          -- Einlullender Schuss
Q.MAGMADAR = 664         -- Encounter Magmadar
Q.answers = {}           -- [Name] = true (hat ihn) / false (hat ihn nicht)
Q.running = false
Q.asked = {}             -- [Name] = "addon" / "whisper"

local YES = { ja = true, j = true, yes = true, y = true, oui = true, si = true, ["sí"] = true, sim = true, da = true, ["да"] = true, ["예"] = true, ["네"] = true, ["是"] = true }
local NO = { nein = true, n = true, no = true, non = true, ["não"] = true, nao = true, net = true, ["нет"] = true, ["아니오"] = true, ["아니요"] = true, ["否"] = true }

-- Habe ich selbst den Schuss?
function Q.HaveIt()
	if IsPlayerSpell and IsPlayerSpell(Q.SPELL) then return true end
	if IsSpellKnown and IsSpellKnown(Q.SPELL) then return true end
	return false
end

-- Jäger im Raid (online), alphabetisch
function Q.Hunters()
	local list = {}
	for _, m in ipairs(RM.RaidMembers()) do
		if m.class == "HUNTER" and m.online ~= false then list[#list + 1] = m.name end
	end
	table.sort(list)
	return list
end

-- Rotation: Jäger mit Schuss; ohne Abfrage alle Jäger
function Q.Rotation()
	local hunters = Q.Hunters()
	if not next(Q.answers) then return hunters, false end
	local list = {}
	for _, h in ipairs(hunters) do
		if Q.answers[h] then list[#list + 1] = h end
	end
	return list, true
end

-- Abfrage starten (Raidleitung)
function Q.Ask()
	if not (RM.InRaid() and (RM.IsAssist() or RM.CanEdit())) then
		RM.Print(L["Die Abfrage können nur Raidleiter und Co-Raidleiter im Raid starten."])
		return
	end
	wipe(Q.answers); wipe(Q.asked)
	local hunters = Q.Hunters()
	if #hunters == 0 then RM.Print(L["Keine Jäger im Raid."]) return end
	Q.running = true
	Q.started = GetTime()
	for _, h in ipairs(hunters) do
		if h == RM.Me() then
			Q.answers[h] = Q.HaveIt()
		else
			Q.asked[h] = "addon"
		end
	end
	RM.Comm.Send("TQ", { q = 1 }, "RAID", nil, true)
	RM.Print(string.format(L["Frage %d Jäger nach Einlullender Schuss ..."], #hunters))
	-- wer nach 4 Sek. nicht über das Addon geantwortet hat, bekommt ein Flüstern
	C_Timer.After(4, function()
		for h, how in pairs(Q.asked) do
			if how == "addon" and Q.answers[h] == nil then
				Q.asked[h] = "whisper"
				RM.Whisper(L["[RaidMaster] Magmadar: Hast du Einlullender Schuss (Buch aus dem Geschmolzenen Kern)? Bitte mit ja oder nein antworten."], h)
			end
		end
		RM.Fire("TRANQ_CHANGED")
	end)
	C_Timer.After(60, function() Q.running = false; RM.Fire("TRANQ_CHANGED") end)
	RM.Fire("TRANQ_CHANGED")
end

-- Antwort über das Addon
RM.Comm.Register("TQ", function(sender, d)
	if d.q then
		local _, class = UnitClass("player")
		if class == "HUNTER" then RM.Comm.Send("TQ", { a = Q.HaveIt() and 1 or 0 }, "WHISPER", sender, true) end
	elseif d.a ~= nil and Q.asked[sender] then
		Q.answers[sender] = (d.a == 1)
		RM.Fire("TRANQ_CHANGED")
	end
end)

-- Antwort per Flüstern (Jäger ohne Addon)
RM.On("CHAT_MSG_WHISPER", function(msg, sender)
	sender = RM.Short(sender)
	if Q.asked[sender] ~= "whisper" or Q.answers[sender] ~= nil then return end
	local w = (msg or ""):lower():gsub("[%p%s]+", " "):match("^%s*(%S+)")
	if not w then return end
	if YES[w] then Q.answers[sender] = true elseif NO[w] then Q.answers[sender] = false else return end
	RM.Fire("TRANQ_CHANGED")
end)

-- Stand der Abfrage als Text
function Q.StatusText()
	local hunters = Q.Hunters()
	if #hunters == 0 then return L["Keine Jäger im Raid."] end
	local parts = {}
	for _, h in ipairs(hunters) do
		local a = Q.answers[h]
		local mark = a == true and "|cff40ff40✔|r" or a == false and "|cffff5544✘|r" or "|cffaaaaaa?|r"
		parts[#parts + 1] = mark .. " " .. h
	end
	return table.concat(parts, "   ")
end

-- Rotation als Schlachtzugwarnung posten und jedem Jäger seine Position flüstern
function Q.Post()
	local list, asked = Q.Rotation()
	if #list == 0 then
		RM.Print(asked and L["Kein Jäger hat Einlullender Schuss – Raserei mit Heilung und Abstand überstehen."] or L["Keine Jäger im Raid."])
		return
	end
	local parts = {}
	for i, h in ipairs(list) do parts[#parts + 1] = i .. ". " .. h end
	RM.RaidWarning({ L["MAGMADAR – Einlull-Rotation: "] .. table.concat(parts, " > ") })
	for i, h in ipairs(list) do
		if h ~= RM.Me() then
			RM.Whisper(string.format(L["[RaidMaster] Einlullender Schuss bei Magmadar: du bist Nr. %d von %d. Bei Raserei sofort schießen, wenn du dran bist."], i, #list), h)
		end
	end
end
