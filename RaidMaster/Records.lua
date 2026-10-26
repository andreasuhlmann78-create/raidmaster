-- RaidMaster - Erstkills, Bestzeiten und Kill-Protokoll
--   * Erstkill-Feier: tötet die Gilde einen Boss zum ersten Mal, gibt es eine Schlachtzugwarnung mit Fanfare und
--     das Spiel macht einen Screenshot. Der Uploader schickt den Screenshot mit, der Bot postet ihn mit Boss,
--     Datum, Versuchen und allen Teilnehmern in #ruhmeshalle.
--   * Bestzeiten: das Addon misst jeden Bosskampf. Schneller als der Gilden-Rekord -> "Neuer Rekord!" im Raid
--     (und im Discord). Rekorde gehen an die Gilde (Addon-Nachricht), damit alle denselben Stand haben.
--   * Kill-Protokoll (RaidMasterDB.killlog) für Discord: Boss, Raid, Zeit, Dauer, Versuche, Teilnehmer.
-- Im Testmodus wird nichts gespeichert und nichts gefeiert.

local ADDON, RM = ...
local L = RM.L
local R = {}
RM.Records = R

R.MAX_LOG = 400
R.MIN_DURATION = 10        -- kürzere Kämpfe zählen nicht als Rekord (z. B. Fehler beim Erkennen)

local fight = {}           -- [Encounter-ID] = { start = GetTime(), first = bool }
local wipes = {}           -- [Encounter-ID] = Fehlversuche seit dem letzten Kill

local function C() return RM.db.config end
local function Active()
	return RM.db and not (RM.Test and RM.Test.active) and C().records ~= false
end

function R.FormatTime(sec)
	sec = math.floor((sec or 0) + 0.5)
	return string.format("%d:%02d", math.floor(sec / 60), sec % 60)
end

local function Store()
	RM.db.records = RM.db.records or {}
	return RM.db.records
end

local function Members()
	local out = {}
	for _, m in ipairs(RM.RaidMembers()) do out[#out + 1] = m.name end
	table.sort(out)
	return out
end

local function PoolFor(id)
	local boss = RM.Data.Bosses[id]
	return (boss and boss.pool) or (RM.DKP.CurrentInstancePool and RM.DKP.CurrentInstancePool()) or RM.db.session.pool
end

---------------------------------------------------------------------------
-- Kampf
---------------------------------------------------------------------------
function R.OnStart(id)
	if not RM.db then return end
	-- Erstkill: noch kein Kill in den DKP-Daten der Gilde, in den Rekorden und im eigenen Protokoll
	local first = not RM.db.data.firstKills[id] and not (RM.db.records and RM.db.records[id])
	if first then
		for _, k in ipairs(RM.db.killlog or {}) do if k.e == id then first = false break end end
	end
	fight[id] = { start = GetTime(), first = first }
end

function R.OnEnd(id, name, difficulty, size, success)
	if not Active() then fight[id] = nil return end
	local f = fight[id]
	fight[id] = nil
	if not (success == 1 or success == true) then
		wipes[id] = (wipes[id] or 0) + 1
		return
	end
	local boss = RM.Data.Bosses[id]
	local bossName = (boss and boss.name) or name or L["Boss"]
	local duration = f and (GetTime() - f.start) or nil
	local first = f and f.first or false
	local tries = (wipes[id] or 0) + 1
	wipes[id] = nil
	local now = GetServerTime()
	-- Kill-Protokoll
	RM.db.killlog = RM.db.killlog or {}
	table.insert(RM.db.killlog, { e = id, n = bossName, p = PoolFor(id), t = now, d = duration and math.floor(duration + 0.5) or nil,
		w = tries - 1, f = first or nil, m = table.concat(Members(), ",") })
	while #RM.db.killlog > R.MAX_LOG do table.remove(RM.db.killlog, 1) end
	if first and RM.InRaid() then R.Celebrate(id, bossName, tries, now) end
	if duration and duration >= R.MIN_DURATION then R.CheckRecord(id, bossName, duration, now) end
end

---------------------------------------------------------------------------
-- Erstkill
---------------------------------------------------------------------------
function R.Celebrate(id, bossName, tries, t)
	-- Fanfare bei allen mit RaidMaster
	if PlaySound then
		local kit = SOUNDKIT and (SOUNDKIT.UI_RAID_BOSS_WHISPER_WARNING or SOUNDKIT.LEVEL_UP or SOUNDKIT.READY_CHECK)
		pcall(PlaySound, kit or 888, "Master")
	end
	-- Screenshot (nach einer Sekunde, wenn der Boss sicher liegt) – der Uploader schickt ihn an Discord
	if C().firstKillScreenshot ~= false and Screenshot then
		C_Timer.After(1.5, function() pcall(Screenshot) end)
		RM.db.shots = RM.db.shots or {}
		table.insert(RM.db.shots, { t = t, e = id, n = bossName })
		while #RM.db.shots > 50 do table.remove(RM.db.shots, 1) end
		-- einfache Liste für den Uploader: "Zeit:Boss-ID;..."
		local parts = {}
		for _, s in ipairs(RM.db.shots) do parts[#parts + 1] = s.t .. ":" .. s.e end
		RM.db.shotList = table.concat(parts, ";")
	end
	-- Ansage nur durch die Raidleitung (sonst käme sie von jedem Addon-Nutzer)
	if RM.IsLeader() or (RM.IsAssist() and RM.CanEdit()) then
		RM.Announce(string.format(L["[RaidMaster] ERSTKILL! %s liegt zum ersten Mal – nach %d %s. Großartig, Leute!"], bossName, tries,
			tries == 1 and L["Versuch"] or L["Versuchen"]), true)
	end
	RM.Print(string.format(L["Erstkill %s – Screenshot gemacht, er kommt mit dem nächsten Upload in den Discord."], bossName))
end

---------------------------------------------------------------------------
-- Bestzeiten
---------------------------------------------------------------------------
function R.Best(id)
	return Store()[id]
end

function R.CheckRecord(id, bossName, duration, t)
	local s = Store()
	local old = s[id]
	if old and old.d and duration >= old.d - 0.5 then return false end
	s[id] = { d = math.floor(duration + 0.5), t = t, n = bossName }
	RM.Comm.Send("REC", { e = id, d = s[id].d, t = t, n = bossName }, "GUILD")
	if old and old.d and RM.InRaid() and (RM.IsLeader() or (RM.IsAssist() and RM.CanEdit())) then
		RM.Announce(string.format(L["[RaidMaster] NEUER REKORD: %s in %s (vorher %s)!"], bossName, R.FormatTime(duration), R.FormatTime(old.d)), true)
	elseif old and old.d then
		RM.Print(string.format(L["Neuer Gilden-Rekord: %s in %s (vorher %s)."], bossName, R.FormatTime(duration), R.FormatTime(old.d)))
	end
	RM.Fire("RECORDS_CHANGED", id)
	return old ~= nil
end

RM.Comm.Register("REC", function(sender, d, channel)
	if channel ~= "GUILD" or not d.e or not d.d then return end
	local s = Store()
	local cur = s[d.e]
	if not cur or d.d < cur.d then s[d.e] = { d = tonumber(d.d), t = tonumber(d.t) or GetServerTime(), n = d.n } RM.Fire("RECORDS_CHANGED", d.e) end
end)

RM.On("ENCOUNTER_START", function(id) R.OnStart(id) end)
RM.On("ENCOUNTER_END", function(id, name, difficulty, size, success) R.OnEnd(id, name, difficulty, size, success) end)

-- /rm rekorde
function R.Print()
	local s = Store()
	local list = {}
	for id, r in pairs(s) do list[#list + 1] = { id = id, r = r } end
	if #list == 0 then RM.Print(L["Noch keine Bestzeiten."]) return end
	table.sort(list, function(a, b) return (a.r.n or "") < (b.r.n or "") end)
	for _, x in ipairs(list) do
		RM.Print(string.format("%s – %s (%s)", x.r.n or ("Boss " .. x.id), R.FormatTime(x.r.d), date("%d.%m.%Y", x.r.t or 0)))
	end
end
