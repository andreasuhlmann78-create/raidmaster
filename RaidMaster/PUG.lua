-- RaidMaster - PUG-Raids
-- Kein DKP und keine Versteigerung. Soft Reserve und Würfeln laufen über softres.it;
-- RaidMaster schaltet nur die DKP-Funktionen für diesen Raid ab und verteilt den softres.it-Link.

local ADDON, RM = ...
local L = RM.L
local P = {}
RM.PUG = P

P.view = { active = false, leader = nil }   -- Ansicht für alle

local function DB()
	RM.db.pug = RM.db.pug or { active = false }
	RM.db.pug.reserves = nil   -- Altlasten früherer Versionen
	return RM.db.pug
end

---------------------------------------------------------------------------
-- Hilfen
---------------------------------------------------------------------------
function P.IsLeader()
	local d = DB()
	return d.active and d.leader == RM.Me()
end

function P.IsActive()
	return P.view.active
end

function P.CanLead()
	return RM.InRaid() and (RM.IsLeader() or RM.IsAssist() or RM.IAmMasterLooter())
end

function P.SoftresLink()
	local link = RM.db and RM.db.config.softresLink or ""
	if link == "" and P.view.softres then link = P.view.softres end
	return link
end

-- Link im Raid posten
function P.AnnounceSoftres(asWarning)
	local link = P.SoftresLink()
	if link == "" then
		RM.Print(L["Kein softres.it-Link eingetragen (Seite PUG-Raid)."])
		return false
	end
	RM.Announce(L["[RaidMaster] Soft Reserve und Loot über softres.it: "] .. link, asWarning)
	return true
end

---------------------------------------------------------------------------
-- Leiter: PUG-Raid starten / beenden
---------------------------------------------------------------------------
function P.SyncView()
	local d = DB()
	if d.active and d.leader == RM.Me() then
		P.view = { active = true, leader = RM.Me(), title = d.title, softres = RM.db.config.softresLink }
	end
	RM.Fire("PUG_CHANGED")
end

function P.Start(title)
	if not P.CanLead() then RM.Print(L["PUG-Raids kann der Raidleiter, ein Assistent oder der Plündermeister starten."]) return end
	local d = DB()
	d.active = true
	d.leader = RM.Me()
	d.title = (type(title) == "string" and title) or (RM.db.signup and RM.db.signup.title) or L["PUG-Raid"]
	RM.Comm.Send("PS", { t = d.title, s = RM.db.config.softresLink }, "RAID", nil, true)
	P.SyncView()
	if not P.AnnounceSoftres(true) then
		RM.Announce(L["[RaidMaster] PUG-Raid gestartet – kein DKP, Loot nach Ansage des Plündermeisters."], true)
	end
	if RM.InRaid() and RM.IsLeader() and RM.db.config.setLootOnStart then RM.Loot.ApplySettings() end
	RM.Fire("PUG_CHANGED")
end

function P.Stop()
	local d = DB()
	if not d.active then return end
	d.active = false
	RM.Comm.Send("PE", {}, "RAID", nil, true)
	P.view = { active = false }
	RM.Announce(L["[RaidMaster] PUG-Raid beendet. Danke fürs Mitspielen!"], false)
	RM.Fire("PUG_CHANGED")
end

---------------------------------------------------------------------------
-- Nachrichten
---------------------------------------------------------------------------
RM.Comm.Register("PS", function(sender, d)
	P.view = { active = true, leader = sender, title = d.t, softres = d.s }
	local link = (d.s and d.s ~= "") and (L[" Soft Reserve und Loot: "] .. d.s) or ""
	RM.Print(string.format(L["PUG-Raid gestartet von %s – kein DKP.%s"], sender, link))
	RM.Fire("PUG_CHANGED")
end)

RM.Comm.Register("PE", function(sender)
	if P.view.leader == sender then
		P.view = { active = false }
		RM.Fire("PUG_CHANGED")
	end
end)

RM.Listen("LOGIN", function()
	-- Nach /reload den eigenen PUG-Raid wieder aufnehmen
	local d = DB()
	if d.active and d.leader == RM.Me() then
		if RM.InRaid() then P.SyncView() else d.active = false end
	end
end)
