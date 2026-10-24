-- RaidMaster - Kommunikation
-- Serializer, gedrosselte Sendewarteschlange, Mehrteil-Nachrichten, Daten-Sync, Versionsprüfung

local ADDON, RM = ...
local Comm = {}
RM.Comm = Comm

Comm.handlers = {}
Comm.versions = {}   -- [name] = { num=, text=, t= }
Comm.skinners = {}   -- [name] = Kürschnerei-Skill

---------------------------------------------------------------------------
-- Serializer (ohne loadstring, nur Strings/Zahlen/Booleans/Tabellen)
---------------------------------------------------------------------------
local function esc(s)
	s = s:gsub("~", "~0"):gsub("%^", "~1"):gsub("|", "~2"):gsub("\n", "~3"):gsub("\t", "~4"):gsub("\r", "")
	return s
end

local UNESC = { ["0"] = "~", ["1"] = "^", ["2"] = "|", ["3"] = "\n", ["4"] = "\t" }
local function unesc(s)
	return (s:gsub("~(%d)", UNESC))
end

local function encode(v, out)
	local t = type(v)
	if t == "string" then
		out[#out + 1] = "s" .. esc(v) .. "^"
	elseif t == "number" then
		out[#out + 1] = "n" .. tostring(v) .. "^"
	elseif t == "boolean" then
		out[#out + 1] = v and "T" or "F"
	elseif t == "table" then
		out[#out + 1] = "{"
		for k, val in pairs(v) do
			local kt, vt = type(k), type(val)
			if (kt == "string" or kt == "number") and (vt == "string" or vt == "number" or vt == "boolean" or vt == "table") then
				encode(k, out)
				encode(val, out)
			end
		end
		out[#out + 1] = "}"
	end
end

function Comm.Serialize(v)
	local out = {}
	encode(v, out)
	return table.concat(out)
end

local function decode(s, pos)
	local c = s:sub(pos, pos)
	if c == "s" then
		local e = s:find("^", pos + 1, true)
		if not e then error("bad string") end
		return unesc(s:sub(pos + 1, e - 1)), e + 1
	elseif c == "n" then
		local e = s:find("^", pos + 1, true)
		if not e then error("bad number") end
		return tonumber(s:sub(pos + 1, e - 1)), e + 1
	elseif c == "T" then
		return true, pos + 1
	elseif c == "F" then
		return false, pos + 1
	elseif c == "{" then
		local t = {}
		pos = pos + 1
		while true do
			local nc = s:sub(pos, pos)
			if nc == "}" then return t, pos + 1 end
			if nc == "" then error("unterminated table") end
			local k, v
			k, pos = decode(s, pos)
			v, pos = decode(s, pos)
			if k ~= nil then t[k] = v end
		end
	end
	error("bad token " .. tostring(c))
end

function Comm.Deserialize(s)
	if not s or s == "" then return nil end
	local ok, v = pcall(decode, s, 1)
	if ok then return v end
	return nil
end

---------------------------------------------------------------------------
-- Sendewarteschlange (gedrosselt, wichtige Nachrichten zuerst)
---------------------------------------------------------------------------
local queueHigh, queueLow = {}, {}
local ticker
local MAX_LEN = 250
local CHUNK = 220
local msgCounter = 0

local function SendNext()
	local item = table.remove(queueHigh, 1) or table.remove(queueLow, 1)
	if not item then
		if ticker then ticker:Cancel(); ticker = nil end
		return
	end
	if item.channel == "RAID" and not RM.InRaid() then return end
	if item.channel == "GUILD" and not IsInGuild() then return end
	RM.SendAddonMessage(RM.PREFIX, item.msg, item.channel, item.target)
end

local function Enqueue(msg, channel, target, high)
	local q = high and queueHigh or queueLow
	q[#q + 1] = { msg = msg, channel = channel, target = target }
	if not ticker then
		SendNext()
		ticker = C_Timer.NewTicker(0.12, SendNext)
	end
end

-- Nachricht senden: Typ, Datentabelle, Kanal (RAID/GUILD/WHISPER), Ziel, hohe Priorität
function Comm.Send(msgType, data, channel, target, high)
	if channel == "WHISPER" and (not target or target == "") then return end
	local payload = msgType .. "\t" .. Comm.Serialize(data or {})
	if #payload <= MAX_LEN then
		Enqueue(payload, channel, target, high)
		return
	end
	msgCounter = msgCounter + 1
	local id = tostring(msgCounter) .. tostring(math.random(100, 999))
	local total = math.ceil(#payload / CHUNK)
	for i = 1, total do
		local part = payload:sub((i - 1) * CHUNK + 1, i * CHUNK)
		Enqueue("~M\t" .. id .. "\t" .. i .. "\t" .. total .. "\t" .. part, channel, target, high)
	end
end

function Comm.Register(msgType, fn)
	Comm.handlers[msgType] = fn
end

---------------------------------------------------------------------------
-- Empfang
---------------------------------------------------------------------------
local buffers = {}

local function Dispatch(sender, msg, channel)
	local msgType, rest = msg:match("^(%w+)\t(.*)$")
	if not msgType then return end
	local fn = Comm.handlers[msgType]
	if not fn then return end
	local data = Comm.Deserialize(rest)
	if type(data) ~= "table" then return end
	fn(sender, data, channel)
end

RM.On("CHAT_MSG_ADDON", function(prefix, msg, channel, sender)
	if prefix ~= RM.PREFIX or not msg then return end
	sender = RM.Short(sender)
	if sender == RM.Me() then return end
	if msg:sub(1, 3) == "~M\t" then
		local id, i, total, part = msg:match("^~M\t(%d+)\t(%d+)\t(%d+)\t(.*)$")
		if not id then return end
		i, total = tonumber(i), tonumber(total)
		local key = sender .. ":" .. id
		local b = buffers[key]
		if not b then
			b = { parts = {}, count = 0, total = total, t = GetTime() }
			buffers[key] = b
		end
		if not b.parts[i] then
			b.parts[i] = part
			b.count = b.count + 1
		end
		if b.count >= b.total then
			buffers[key] = nil
			Dispatch(sender, table.concat(b.parts), channel)
		end
		-- alte, unvollständige Puffer aufräumen
		local now = GetTime()
		for k, v in pairs(buffers) do
			if now - v.t > 120 then buffers[k] = nil end
		end
		return
	end
	Dispatch(sender, msg, channel)
end)

---------------------------------------------------------------------------
-- Eigener Kürschnerei-Skill (für die Kernhunde-Hilfe)
---------------------------------------------------------------------------
function Comm.MySkinning()
	if not GetNumSkillLines then return 0 end
	for i = 1, GetNumSkillLines() do
		local name, isHeader, _, rank = GetSkillLineInfo(i)
		if not isHeader and name and (name == "Kürschnerei" or name == "Skinning" or name == "Kürschner") then
			return rank or 0
		end
	end
	return 0
end

local function HelloData()
	return { av = RM.VERSION_NUM, at = RM.VERSION, dv = RM.db.data.version, sk = Comm.MySkinning() }
end

function Comm.SendHello(channel)
	Comm.Send("HELLO", HelloData(), channel)
end

local versionNotified = false

local function StoreHello(sender, d)
	Comm.versions[sender] = { num = d.av or 0, text = d.at or "?", t = GetTime() }
	Comm.skinners[sender] = d.sk or 0
	-- Hinweis, wenn jemand eine neuere Addon-Version hat
	if not versionNotified and (d.av or 0) > RM.VERSION_NUM then
		versionNotified = true
		local msg = string.format("Neue RaidMaster-Version %s verfügbar (du hast %s). Download im Discord unter #raid-addon.", d.at or "?", RM.VERSION)
		RM.Print("|cffffcc00" .. msg .. "|r")
		RaidNotice_AddMessage(RaidWarningFrame, "RaidMaster: " .. msg, ChatTypeInfo["RAID_WARNING"])
	end
end

---------------------------------------------------------------------------
-- Daten-Sync
-- Offiziere sind die Quelle. Jede Änderung wird als Eintrag (ENTRY) mit
-- Vorgänger- und neuer Version gesendet. Wer eine Lücke hat, fordert einen
-- kompletten Datenstand (SNAP) an.
---------------------------------------------------------------------------
local best = { version = 0, sender = nil, timer = nil }
local lastReplyTo = {}
local lastSnapTo = {}

local function RequestFrom(sender)
	if not sender then return end
	Comm.Send("REQ", { dv = RM.db.data.version }, "WHISPER", sender)
end

function Comm.Consider(sender, version)
	if not version or version <= RM.db.data.version then return end
	if version > best.version then
		best.version = version
		best.sender = sender
	end
	if best.timer then return end
	best.timer = C_Timer.NewTimer(2, function()
		best.timer = nil
		if best.version > RM.db.data.version then
			RequestFrom(best.sender)
		end
		best.version = 0
		best.sender = nil
	end)
end

function Comm.RequestSync()
	RM.Print("Datenabgleich angefordert ...")
	Comm.SendHello("GUILD")
end

function Comm.BroadcastSnapshot()
	if not RM.CanEdit() then return end
	Comm.Send("SNAP", RM.DKP.MakeSnapshot(), "GUILD")
end

local lastRaidSnapTo = {}

-- Gildenfremden Raidmitgliedern den eigenen Stand schicken
local function OfferToOutsider(sender)
	if not RM.CanEdit() or not RM.InRaid() then return end
	if RM.guild.rank[sender] then return end              -- gehört zur eigenen Gilde
	if not (RM.db.session.active or RM.IAmMasterLooter()) then return end
	if not RM.IsInMyRaid(sender) then return end
	local now = GetTime()
	if lastRaidSnapTo[sender] and now - lastRaidSnapTo[sender] < 300 then return end
	lastRaidSnapTo[sender] = now
	Comm.Send("SNAP", RM.DKP.MakeSnapshot(20), "WHISPER", sender)
end

Comm.Register("HELLO", function(sender, d, channel)
	StoreHello(sender, d)
	if channel == "RAID" then
		OfferToOutsider(sender)
		return
	end
	if channel ~= "GUILD" then return end
	local myVersion = RM.db.data.version
	if RM.IsOfficer(sender) and (d.dv or 0) > myVersion then
		Comm.Consider(sender, d.dv)
	end
	-- Als Offizier mit neuerem Stand antworten (gedrosselt, zufällige Verzögerung)
	if RM.CanEdit() and (d.dv or 0) < myVersion then
		local now = GetTime()
		if lastReplyTo[sender] and now - lastReplyTo[sender] < 60 then return end
		lastReplyTo[sender] = now
		C_Timer.After(math.random(5, 30) / 10, function()
			Comm.Send("HI", { dv = RM.db.data.version }, "WHISPER", sender)
		end)
	end
end)

Comm.Register("HI", function(sender, d)
	if RM.IsOfficer(sender) then
		Comm.Consider(sender, d.dv)
	end
end)

Comm.Register("REQ", function(sender, d)
	if not RM.CanEdit() then return end
	if (d.dv or 0) >= RM.db.data.version then return end
	local now = GetTime()
	if lastSnapTo[sender] and now - lastSnapTo[sender] < 20 then return end
	lastSnapTo[sender] = now
	-- Gildenfremde bekommen einen kleineren Stand (weniger Log)
	local outsider = not RM.guild.rank[sender]
	Comm.Send("SNAP", RM.DKP.MakeSnapshot(outsider and 20 or nil), "WHISPER", sender)
end)

Comm.Register("SNAP", function(sender, d)
	if d.g and d.g ~= "" and d.g ~= RM.MyGuild() then
		-- Daten einer fremden Raid-Gilde: nur von Raidleitung annehmen, nur zur Ansicht
		if not RM.IsRaidAuthority(sender) then return end
		local store = RM.db.foreign[d.g]
		if store and (d.v or 0) <= (store.version or 0) then return end
		RM.DKP.ImportForeign(d, sender)
		return
	end
	if not RM.IsOfficer(sender) then return end
	if (d.v or 0) <= RM.db.data.version then return end
	RM.DKP.ImportSnapshot(d)
	RM.Print("Datenstand von " .. sender .. " übernommen.")
end)

local lastForeignReq = 0

Comm.Register("ENTRY", function(sender, d)
	if type(d.e) ~= "table" then return end
	if d.g and d.g ~= "" and d.g ~= RM.MyGuild() then
		if not RM.IsRaidAuthority(sender) then return end
		local store = RM.db.foreign[d.g]
		if store and store.version == d.pv then
			RM.DKP.ApplyEntryTo(store, d.e, false)
			store.version = d.v
			store.received = GetServerTime()
			RM.Fire("DATA_CHANGED")
		elseif not store or (d.v or 0) > (store.version or 0) then
			local now = GetTime()
			if now - lastForeignReq > 10 then
				lastForeignReq = now
				Comm.Send("REQ", { dv = store and store.version or 0 }, "WHISPER", sender)
			end
		end
		return
	end
	if not RM.IsOfficer(sender) then return end
	local data = RM.db.data
	if data.version == d.pv then
		RM.DKP.ApplyEntry(d.e)
		data.version = d.v
		RM.Fire("DATA_CHANGED")
	elseif (d.v or 0) > data.version then
		Comm.Consider(sender, d.v)
	end
end)

---------------------------------------------------------------------------
-- Versionsprüfung im Raid
---------------------------------------------------------------------------
Comm.Register("PING", function(sender)
	Comm.Send("PONG", HelloData(), "WHISPER", sender)
end)

-- Fremde Gilde? (Daten gehören nicht zur eigenen Gilde)
local function IsForeign(g)
	return g and g ~= "" and g ~= RM.MyGuild()
end
Comm.IsForeign = IsForeign

Comm.Register("PONG", function(sender, d)
	StoreHello(sender, d)
end)

function Comm.PingRaid()
	Comm.Send("PING", {}, "RAID", nil, true)
end

---------------------------------------------------------------------------
-- Start
---------------------------------------------------------------------------
local wasInRaid = false

RM.Listen("LOGIN", function()
	C_Timer.After(8, function()
		RM.RequestGuildRoster()
		Comm.SendHello("GUILD")
		if RM.InRaid() then Comm.SendHello("RAID") end
	end)
	wasInRaid = RM.InRaid()
end)

RM.On("GROUP_ROSTER_UPDATE", function()
	local inRaid = RM.InRaid()
	if inRaid and not wasInRaid then
		C_Timer.After(2, function() Comm.SendHello("RAID") end)
	end
	wasInRaid = inRaid
end)
