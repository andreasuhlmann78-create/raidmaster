-- RaidMaster - Versteigerung
-- Plündermeister-Seite (Warteschlange, Gebote prüfen, Vergabe) und
-- Spieler-Seite (Gebotsfenster mit Enter, Passen, Ausrüstungsvergleich)

local ADDON, RM = ...
local L = RM.L
local A = {}
RM.Auction = A

A.queue = {}        -- { {link=} }
A.current = nil     -- laufende Versteigerung (nur beim Plündermeister)
A.client = nil      -- Ansicht für alle Spieler
local aidCounter = 0
local ticker

local function S() return RM.db.data.settings end
local function C() return RM.db.config end

---------------------------------------------------------------------------
-- Warteschlange
---------------------------------------------------------------------------
function A.Enqueue(link)
	if not link then return end
	A.queue[#A.queue + 1] = { link = link }
	A.SendQueue()
	RM.Fire("AUCTION_CHANGED")
end

function A.Remove(index)
	table.remove(A.queue, index)
	A.SendQueue()
	RM.Fire("AUCTION_CHANGED")
end

-- Die Warteschlange liegt beim Plündermeister. Damit Raidleitung und Raid sie auch sehen,
-- schickt er sie bei jeder Änderung an den Raid (kurz gebündelt).
A.remote = nil          -- { from = Name, list = { {link=...}, ... } }
local queueSendPending = false
function A.SendQueue()
	if not RM.InRaid() or queueSendPending then return end
	queueSendPending = true
	C_Timer.After(0.5, function()
		queueSendPending = false
		local q = {}
		for _, item in ipairs(A.queue) do q[#q + 1] = item.link end
		RM.Comm.Send("AQ", { q = q }, "RAID")
	end)
end

RM.Comm.Register("AQ", function(sender, d)
	if sender == RM.Me() then return end
	local list = {}
	for _, l in ipairs(d.q or {}) do list[#list + 1] = { link = l } end
	if #list == 0 and A.remote and A.remote.from ~= sender then return end
	A.remote = { from = sender, list = list }
	RM.Fire("AUCTION_CHANGED")
end)

-- Was die Seite zeigt: die eigene Warteschlange oder die des Plündermeisters
function A.ViewQueue()
	if #A.queue > 0 or not A.remote or #A.remote.list == 0 then return A.queue, nil end
	return A.remote.list, A.remote.from
end

-- Versteigerungen startet nur der Plündermeister, jedes Item einzeln von Hand (nie automatisch).
-- In Spielversionen ohne Plündermeister (Retail) übernimmt das die Raidleitung/ein Offizier.
function A.CanRun()
	if not RM.InRaid() then return false, L["Du bist in keinem Schlachtzug."] end
	if RM.Caps.masterLoot and not RM.IAmMasterLooter() then
		return false, string.format(L["Versteigerungen startet nur der Plündermeister (%s)."], RM.MasterLooterName() or "?")
	end
	if not RM.CanLoot() then return false, L["Versteigerungen führt nur der Plündermeister oder der Raidleiter durch."] end
	return true
end

---------------------------------------------------------------------------
-- Plündermeister: Versteigerung starten
---------------------------------------------------------------------------
function A.Start(indexOrLink)
	local ok, err = A.CanRun()
	if not ok then RM.Print(err) return end
	if A.AwaitingAward() then
		RM.Print(L["Erst die letzte Versteigerung vergeben oder nicht vergeben."])
		A.AskAward()
		return
	end
	if A.current then RM.Print(L["Es läuft bereits eine Versteigerung."]) return end
	local link
	if type(indexOrLink) == "number" then
		local item = table.remove(A.queue, indexOrLink)
		link = item and item.link
		A.SendQueue()
	else
		link = indexOrLink
	end
	if not link or not link:find("item:") then RM.Print(L["Kein gültiger Itemlink."]) return end

	local s = S()
	local pool = RM.DKP.ActivePool()
	local poolName = RM.DKP.PoolName(pool)
	aidCounter = aidCounter + 1
	local aid = RM.Me() .. "-" .. GetServerTime() .. "-" .. aidCounter
	A.current = {
		aid = aid, link = link, min = s.minBid, inc = s.bidIncrement, pool = pool,
		endsAt = GetTime() + s.auctionTime, bids = {}, passes = {}, high = 0, highName = nil,
	}
	local as = { a = aid, l = link, m = s.minBid, i = s.bidIncrement, d = s.auctionTime, g = RM.MyGuild(), p = pool, pn = poolName }
	RM.Comm.Send("AS", as, "RAID", nil, true)
	A.OnStart(RM.Me(), as)
	RM.Announce(string.format(L["Gebot (%s-DKP): %s – Mindestgebot %d, %d Sek. Addon nutzen oder /w %s !bid <Zahl>"],
		RM.DKP.PoolShort(pool), link, s.minBid, s.auctionTime, RM.Me()), true)
	if ticker then ticker:Cancel() end
	ticker = C_Timer.NewTicker(0.25, A.Tick)
	RM.Fire("AUCTION_CHANGED")
end

local ANNOUNCE_AT = { [10] = true, [5] = true, [3] = true, [2] = true, [1] = true }

function A.Tick()
	local c = A.current
	if not c or c.finished then
		if ticker then ticker:Cancel(); ticker = nil end
		return
	end
	local rem = math.ceil(c.endsAt - GetTime())
	if rem <= 0 then
		A.Finish()
		return
	end
	if ANNOUNCE_AT[rem] and c.lastAnn ~= rem then
		c.lastAnn = rem
		local high = c.highName and string.format("%d DKP (%s)", c.high, c.highName) or "keins"
		RM.RaidChat(string.format(L["%s – noch %d Sek. Höchstgebot: %s"], c.link, rem, high), "RAID")
	end
end

function A.AddTime(sec)
	local c = A.current
	if not c or c.finished then return end
	c.endsAt = c.endsAt + sec
	RM.Comm.Send("AB", { a = c.aid, n = c.highName or "", v = c.high, r = c.endsAt - GetTime() }, "RAID", nil, true)
	A.OnBid(RM.Me(), { a = c.aid, n = c.highName or "", v = c.high, r = c.endsAt - GetTime() })
	RM.Fire("AUCTION_CHANGED")
end

function A.FinishNow()
	if A.current and not A.current.finished then A.Finish() end
end

---------------------------------------------------------------------------
-- Plündermeister: Gebote prüfen
---------------------------------------------------------------------------
function A.ReceiveBid(name, amount, gear)
	local c = A.current
	if not c or c.finished then return false, L["Es läuft keine Versteigerung."] end
	name = RM.Short(name)
	amount = math.floor(tonumber(amount) or 0)
	local s = S()
	if not RM.IsInMyRaid(name) then return false, L["Nur Raidmitglieder können bieten."] end
	local minNeeded = c.highName and (c.high + c.inc) or c.min
	if amount < minNeeded then
		return false, string.format("Gebot zu niedrig – mindestens %d DKP.", minNeeded)
	end
	local have = RM.DKP.Get(name, c.pool)
	if not s.allowNegative and amount > have then
		return false, string.format(L["Nicht genug DKP – du hast %d."], have)
	end
	c.bids[name] = { amount = amount, gear = gear or (c.bids[name] and c.bids[name].gear) or "", t = GetTime() }
	c.passes[name] = nil
	c.high = amount
	c.highName = name
	if s.antiSnipe and c.endsAt - GetTime() < 5 then
		c.endsAt = GetTime() + 5
	end
	local d = { a = c.aid, n = name, v = amount, r = c.endsAt - GetTime() }
	RM.Comm.Send("AB", d, "RAID", nil, true)
	A.OnBid(RM.Me(), d)
	if C().announceBids then
		RM.RaidChat(string.format("%s bietet %d DKP auf %s", name, amount, c.link), "RAID")
	end
	RM.Fire("AUCTION_CHANGED")
	return true
end

function A.Finish()
	local c = A.current
	if not c then return end
	c.finished = true
	if ticker then ticker:Cancel(); ticker = nil end
	if c.highName then
		RM.Comm.Send("AE", { a = c.aid, n = c.highName, v = c.high }, "RAID", nil, true)
		A.OnEnd(RM.Me(), { a = c.aid, n = c.highName, v = c.high })
		A.AskAward()
	else
		RM.Comm.Send("AE", { a = c.aid }, "RAID", nil, true)
		A.OnEnd(RM.Me(), { a = c.aid })
		A.current = nil
		RM.Loot.ApplyFallback(c.link)
	end
	RM.Fire("AUCTION_CHANGED")
end

-- Vergabe-Fenster: eigenes, immer sichtbares Fenster (kein Blizzard-Popup), damit es weder durch Seitenwechsel,
-- Schließen anderer Fenster noch durch Escape verschwindet. Solange eine Vergabe offen ist, bleibt es stehen.
local awardFrame
local function AwardFrame()
	if awardFrame then return awardFrame end
	local UI = RM.UI
	local COLORS = UI.COLORS
	local f = UI.Frame(UIParent, 440, 120)
	f:SetFrameStrata("FULLSCREEN_DIALOG")
	f:SetToplevel(true)
	f:SetClampedToScreen(true)
	UI.Skin(f, nil, COLORS.accent)
	UI.MakeMovable(f, "awardFrame", "TOP", 0, -150)
	f.title = UI.Text(f, L["Versteigerung beendet"], 14, COLORS.accent[1], COLORS.accent[2], COLORS.accent[3])
	f.title:SetPoint("TOPLEFT", 14, -12)
	f.text = UI.Text(f, "", 13)
	f.text:SetPoint("TOPLEFT", 14, -36)
	f.text:SetWidth(412)
	f.text:SetJustifyH("LEFT")
	local award = UI.Button(f, L["Vergeben"], 130, 28, function() A.Award() end)
	award:SetPoint("BOTTOMLEFT", 14, 12)
	award:SetAccent(true)
	local no = UI.Button(f, L["Nicht vergeben"], 130, 28, function() A.NoAward() end,
		L["Geht wie bei keinen Geboten an Entzauberer bzw. Gildenbank (Einstellung auf der Seite Loot)."])
	no:SetPoint("LEFT", award, "RIGHT", 8, 0)
	local again = UI.Button(f, L["Neu versteigern"], 130, 28, function() A.CancelAward() end,
		L["Das Item kommt wieder vorne in die Warteschlange."])
	again:SetPoint("LEFT", no, "RIGHT", 8, 0)
	f:Hide()
	awardFrame = f
	return f
end

function A.AwaitingAward()
	local c = A.current
	return c and c.finished and c.highName and true or false
end

function A.AwardShown()
	return awardFrame and awardFrame:IsShown() and true or false
end

function A.HideAward()
	if awardFrame then awardFrame:Hide() end
end

function A.AskAward()
	local c = A.current
	if not (c and c.finished and c.highName) then return end
	local f = AwardFrame()
	f.text:SetText(string.format(L["%s an %s für %d DKP vergeben?"], c.link, c.highName, c.high))
	f:Show()
	f:Raise()
end

-- offene Vergabe nie aus den Augen verlieren
RM.Listen("AUCTION_CHANGED", function()
	if A.AwaitingAward() then
		if not (awardFrame and awardFrame:IsShown()) then A.AskAward() end
	else
		A.HideAward()
	end
end)

function A.Award()
	local c = A.current
	if not c or not c.highName then return end
	A.HideAward()
	local e = RM.DKP.ChargeItem(c.highName, c.high, c.link, c.pool)
	if e then
		RM.Announce(string.format(L["[RaidMaster] %s erhält %s für %d DKP."], c.highName, c.link, c.high), true)
		RM.Loot.Deliver(c.link, c.highName)
	end
	A.current = nil
	RM.Fire("AUCTION_CHANGED")
end

-- Nicht vergeben: wie "keine Gebote" – geht an Entzauberer/Gildenbank (Einstellung "Keine Gebote") oder bleibt liegen
function A.NoAward()
	local c = A.current
	if not c then return end
	A.HideAward()
	A.current = nil
	RM.Print(c.link .. L[" wurde nicht vergeben."])
	RM.Loot.ApplyFallback(c.link)
	RM.Fire("AUCTION_CHANGED")
end

-- Neu versteigern: Item kommt wieder vorne in die Warteschlange
function A.CancelAward()
	local c = A.current
	if not c then return end
	A.HideAward()
	A.current = nil
	table.insert(A.queue, 1, { link = c.link })
	RM.Print(c.link .. L[" wurde nicht vergeben und liegt wieder vorne in der Warteschlange."])
	RM.Fire("AUCTION_CHANGED")
end

function A.Cancel()
	local c = A.current
	if not c then return end
	if ticker then ticker:Cancel(); ticker = nil end
	RM.Comm.Send("AX", { a = c.aid }, "RAID", nil, true)
	A.OnCancel(RM.Me(), { a = c.aid })
	A.current = nil
	table.insert(A.queue, 1, { link = c.link })
	RM.Announce(L["[RaidMaster] Versteigerung von "] .. c.link .. L[" abgebrochen."], false)
	RM.Fire("AUCTION_CHANGED")
end

-- Sortierte Gebotsliste für die Anzeige
function A.BidList()
	local c = A.current
	local list = {}
	if not c then return list end
	for name, b in pairs(c.bids) do
		list[#list + 1] = { name = name, amount = b.amount, gear = b.gear, t = b.t }
	end
	table.sort(list, function(x, y)
		if x.amount == y.amount then return x.t < y.t end
		return x.amount > y.amount
	end)
	for name in pairs(c.passes) do
		list[#list + 1] = { name = name, amount = nil, pass = true }
	end
	return list
end

---------------------------------------------------------------------------
-- Nachrichten von Spielern an den Plündermeister
---------------------------------------------------------------------------
RM.Comm.Register("BID", function(sender, d)
	local c = A.current
	if not c or d.a ~= c.aid then return end
	local ok, err = A.ReceiveBid(sender, d.v, d.g)
	if not ok then RM.Comm.Send("BERR", { a = d.a, m = err }, "WHISPER", sender, true) end
end)

RM.Comm.Register("PASS", function(sender, d)
	local c = A.current
	if not c or d.a ~= c.aid then return end
	if not c.bids[sender] then c.passes[sender] = true end
	RM.Fire("AUCTION_CHANGED")
end)

-- Gebote per Flüstern (für Spieler ohne Addon)
RM.On("CHAT_MSG_WHISPER", function(msg, sender)
	local c = A.current
	if not c or c.finished then return end
	local m = (msg or ""):lower()
	local amount = m:match("^%s*!?bid%s+(%d+)") or m:match("^%s*!?gebot%s+(%d+)")
	if not amount then return end
	local ok, err = A.ReceiveBid(sender, amount, nil)
	if ok then
		SendChatMessage(string.format(L["[RaidMaster] Gebot angenommen: %s DKP auf %s"], amount, c.link), "WHISPER", nil, sender)
	else
		SendChatMessage(L["[RaidMaster] "] .. err, "WHISPER", nil, sender)
	end
end)

---------------------------------------------------------------------------
-- Spieler-Seite
---------------------------------------------------------------------------
function A.OnStart(sender, d)
	A.client = {
		aid = d.a, link = d.l, min = d.m or 0, inc = d.i or 1, ml = sender, g = d.g, pool = d.p or "mc", poolName = d.pn,
		endsAt = GetTime() + (d.d or 30), high = 0, highName = nil, ended = false, passed = false,
	}
	A.ShowBidFrame()
	RM.Fire("AUCTION_CHANGED")
end

function A.OnBid(sender, d)
	local cl = A.client
	if not cl or cl.aid ~= d.a then return end
	if d.n and d.n ~= "" then
		cl.high = d.v or 0
		cl.highName = d.n
	end
	cl.endsAt = GetTime() + (d.r or 0)
	A.UpdateBidFrame()
	RM.Fire("AUCTION_CHANGED")
end

function A.OnEnd(sender, d)
	local cl = A.client
	if not cl or cl.aid ~= d.a then return end
	cl.ended = true
	cl.winner = d.n
	cl.winAmount = d.v
	A.UpdateBidFrame()
	C_Timer.After(6, function()
		if A.client == cl then A.HideBidFrame() end
	end)
	RM.Fire("AUCTION_CHANGED")
end

function A.OnCancel(sender, d)
	local cl = A.client
	if not cl or cl.aid ~= d.a then return end
	A.client = nil
	A.HideBidFrame()
	RM.Fire("AUCTION_CHANGED")
end

RM.Comm.Register("AS", function(sender, d) A.OnStart(sender, d) end)
RM.Comm.Register("AB", function(sender, d) A.OnBid(sender, d) end)
RM.Comm.Register("AE", function(sender, d) A.OnEnd(sender, d) end)
RM.Comm.Register("AX", function(sender, d) A.OnCancel(sender, d) end)
RM.Comm.Register("BERR", function(sender, d)
	if A.client and A.client.aid == d.a then A.ShowBidError(d.m) end
end)

function A.SendBid(amount)
	local cl = A.client
	if not cl or cl.ended then return end
	amount = math.floor(tonumber(amount) or 0)
	if amount <= 0 then A.ShowBidError(L["Bitte eine Zahl eingeben."]) return end
	local gear = RM.Data.EquippedFor(cl.link)
	if cl.ml == RM.Me() then
		local ok, err = A.ReceiveBid(RM.Me(), amount, gear)
		if not ok then A.ShowBidError(err) end
	else
		RM.Comm.Send("BID", { a = cl.aid, v = amount, g = gear }, "WHISPER", cl.ml, true)
	end
end

function A.SendPass()
	local cl = A.client
	if not cl or cl.ended then return end
	cl.passed = true
	if cl.ml == RM.Me() then
		if A.current then A.current.passes[RM.Me()] = true; RM.Fire("AUCTION_CHANGED") end
	else
		RM.Comm.Send("PASS", { a = cl.aid }, "WHISPER", cl.ml, true)
	end
	A.HideBidFrame()
end

---------------------------------------------------------------------------
-- Gebotsfenster
---------------------------------------------------------------------------
local bidFrame

local function MyClass()
	local _, class = UnitClass("player")
	return class
end

local function TryBid()
	local amount = tonumber(bidFrame.input:GetText())
	local cl = A.client
	if not cl then return end
	local function go()
		A.SendBid(amount)
		bidFrame.input:SetText("")
	end
	if not RM.Data.CanEquip(MyClass(), cl.link) then
		RM.UI.Confirm(L["Deine Klasse kann dieses Item nicht tragen. Trotzdem bieten?"], go, nil, L["Bieten"], L["Abbrechen"])
	else
		go()
	end
end

local function CreateBidFrame()
	local UI = RM.UI
	local f = UI.Frame(UIParent, 340, 196)
	f:SetFrameStrata("DIALOG")
	UI.Skin(f)
	UI.MakeMovable(f, "bidFrame", "TOP", 0, -180)
	f:SetClampedToScreen(true)

	local title = UI.Text(f, L["Versteigerung"], 13, 1, 0.55, 0.1)
	title:SetPoint("TOPLEFT", 12, -10)
	f.title = title

	local close = UI.CloseButton(f, function() A.HideBidFrame() end)
	close:SetPoint("TOPRIGHT", -6, -6)

	local icon = CreateFrame("Button", nil, f)
	icon:SetSize(40, 40)
	icon:SetPoint("TOPLEFT", 12, -32)
	icon.tex = icon:CreateTexture(nil, "ARTWORK")
	icon.tex:SetAllPoints()
	icon:SetScript("OnEnter", function(self)
		if A.client and A.client.link then
			GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
			GameTooltip:SetHyperlink(RM.ItemString(A.client.link) or A.client.link)
			GameTooltip:Show()
		end
	end)
	icon:SetScript("OnLeave", function() GameTooltip:Hide() end)
	f.icon = icon

	local name = UI.Text(f, "", 13)
	name:SetPoint("TOPLEFT", icon, "TOPRIGHT", 10, -2)
	name:SetPoint("RIGHT", f, "RIGHT", -12, 0)
	f.name = name

	local info = UI.Text(f, "", 11, 0.85, 0.85, 0.85)
	info:SetPoint("TOPLEFT", name, "BOTTOMLEFT", 0, -4)
	info:SetPoint("RIGHT", f, "RIGHT", -12, 0)
	f.info = info

	local warn = UI.Text(f, "", 11, 1, 0.3, 0.3)
	warn:SetPoint("TOPLEFT", 12, -78)
	warn:SetPoint("RIGHT", f, "RIGHT", -12, 0)
	f.warn = warn

	local bar = CreateFrame("StatusBar", nil, f)
	bar:SetPoint("TOPLEFT", 12, -96)
	bar:SetPoint("RIGHT", f, "RIGHT", -12, 0)
	bar:SetHeight(14)
	bar:SetStatusBarTexture("Interface\\Buttons\\WHITE8x8")
	bar:SetStatusBarColor(1, 0.55, 0.1, 0.8)
	local barBg = bar:CreateTexture(nil, "BACKGROUND")
	barBg:SetAllPoints()
	barBg:SetColorTexture(1, 1, 1, 0.08)
	bar.text = bar:CreateFontString(nil, "OVERLAY")
	bar.text:SetFont(STANDARD_TEXT_FONT, 10, "OUTLINE")
	bar.text:SetPoint("CENTER")
	f.bar = bar

	local input = UI.EditBox(f, 90, 24, true)
	input:SetPoint("TOPLEFT", 12, -122)
	input:SetScript("OnEnterPressed", function() TryBid() end)
	f.input = input

	local bidBtn = UI.Button(f, L["Bieten"], 80, 24, TryBid)
	bidBtn:SetPoint("LEFT", input, "RIGHT", 6, 0)
	bidBtn:SetAccent(true)

	local plusBtn = UI.Button(f, L["Mindest"], 70, 24, function()
		local cl = A.client
		if not cl then return end
		local v = cl.highName and (cl.high + cl.inc) or cl.min
		input:SetText(tostring(v))
		input:SetFocus()
	end, L["Trägt das kleinste gültige Gebot ein."])
	plusBtn:SetPoint("LEFT", bidBtn, "RIGHT", 6, 0)

	local passBtn = UI.Button(f, L["Passen"], 64, 24, function() A.SendPass() end)
	passBtn:SetPoint("LEFT", plusBtn, "RIGHT", 6, 0)

	local status = UI.Text(f, "", 11, 0.7, 0.9, 1)
	status:SetPoint("TOPLEFT", 12, -156)
	status:SetPoint("RIGHT", f, "RIGHT", -12, 0)
	f.status = status

	f.elapsed = 0
	f:SetScript("OnUpdate", function(self, el)
		self.elapsed = self.elapsed + el
		if self.elapsed < 0.1 then return end
		self.elapsed = 0
		local cl = A.client
		if not cl then return end
		if cl.ended then
			bar:SetValue(0)
			bar.text:SetText(L["Beendet"])
			return
		end
		local rem = math.max(0, cl.endsAt - GetTime())
		local total = math.max(rem, cl.total or rem)
		cl.total = total
		bar:SetMinMaxValues(0, total)
		bar:SetValue(rem)
		bar.text:SetText(string.format(L["%.0f Sek."], rem))
	end)
	f:Hide()
	return f
end

function A.ShowBidFrame()
	bidFrame = bidFrame or CreateBidFrame()
	local cl = A.client
	if not cl then return end
	local _, _, _, _, _, _, _, _, _, tex = RM.GetItemInfo(cl.link)
	if not tex then
		local _, _, _, _, t = RM.GetItemInfoInstant(cl.link)
		tex = t
	end
	bidFrame.icon.tex:SetTexture(tex or "Interface\\Icons\\INV_Misc_QuestionMark")
	bidFrame.name:SetText(cl.link)
	bidFrame.status:SetText("")
	bidFrame.input:SetText("")
	if RM.Data.CanEquip(MyClass(), cl.link) then
		bidFrame.warn:SetText("")
	else
		bidFrame.warn:SetText(L["Achtung: Deine Klasse kann dieses Item nicht tragen."])
	end
	A.UpdateBidFrame()
	bidFrame:Show()
	PlaySound(SOUNDKIT and SOUNDKIT.IG_MAINMENU_OPEN or 850)
end

function A.UpdateBidFrame()
	if not bidFrame or not A.client then return end
	local cl = A.client
	local high = cl.highName and string.format("%d DKP (%s)", cl.high, cl.highName) or L["noch keins"]
	local myDKP = RM.DKP.GetFor(cl.g, RM.Me(), cl.pool)
	local foreign = RM.Comm.IsForeign(cl.g)
	local poolName = cl.poolName or RM.DKP.PoolName(cl.pool)
	bidFrame.title:SetText(L["Versteigerung · "] .. poolName .. L["-DKP"])
	bidFrame.info:SetText(string.format(L["Mindestgebot: %d  ·  Höchstgebot: %s\nDeine %s-DKP: %d%s"], cl.min, high, poolName, myDKP,
		foreign and (L["  (Gilde "] .. cl.g .. ")") or ""))
	if cl.ended then
		if cl.winner then
			bidFrame.status:SetText(string.format("Gewinner: %s mit %d DKP", cl.winner, cl.winAmount or 0))
		else
			bidFrame.status:SetText(L["Keine Gebote."])
		end
	elseif cl.highName == RM.Me() then
		bidFrame.status:SetText(L["|cff40ff40Du bist Höchstbietender.|r"])
	elseif cl.highName then
		bidFrame.status:SetText("")
	end
end

function A.ShowBidError(msg)
	if bidFrame then bidFrame.status:SetText("|cffff5050" .. tostring(msg) .. "|r") end
end

function A.HideBidFrame()
	if bidFrame then bidFrame:Hide() end
end

RM.Listen("DATA_CHANGED", function() A.UpdateBidFrame() end)
