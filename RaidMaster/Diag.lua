-- RaidMaster - Diagnose: zeigt Fehler und Hänger auf einen Blick und kann typische Hänger lösen
-- Öffnen: Knopf "Diagnose" oben im Hauptfenster, /rm diagnose (oder /rm diag), Knopf im Test-Tool.

local ADDON, RM = ...
local L = RM.L
local UI = RM.UI
local COLORS = UI.COLORS
local D = {}
RM.Diag = D

D.errors = {}          -- { {t=Zeit, msg=Text, n=Anzahl} }
D.providers = {}       -- weitere Zeilen, z. B. vom Test-Tool: function() return { "Zeile", ... } end
D.fixers = {}          -- weitere Reparaturen: function() return { "erledigt: ..." } end

---------------------------------------------------------------------------
-- Fehler sammeln: alles, was aus RaidMaster-Dateien kommt (auch aus Timern und Fenstern)
---------------------------------------------------------------------------
function D.Record(msg)
	msg = tostring(msg or "?")
	for _, e in ipairs(D.errors) do
		if e.msg == msg then e.n = e.n + 1; e.t = time() return end
	end
	table.insert(D.errors, 1, { t = time(), msg = msg, n = 1 })
	while #D.errors > 20 do table.remove(D.errors) end
	if D.window and D.window:IsShown() then D.Refresh() end
end

-- in den Fehler-Handler des Spiels einklinken (nach dem Einloggen noch einmal, falls ein
-- Fehler-Addon wie BugGrabber den Handler danach ersetzt hat)
local ours
local function Hook()
	if not (seterrorhandler and geterrorhandler) then return end
	local previous = geterrorhandler()
	if previous == ours then return end
	ours = function(msg, ...)
		local text = tostring(msg)
		if text:find("RaidMaster", 1, true) then D.Record(text) end
		if previous then return previous(msg, ...) end
	end
	seterrorhandler(ours)
end
Hook()
RM.On("PLAYER_LOGIN", function() if C_Timer then C_Timer.After(5, Hook) end end)

---------------------------------------------------------------------------
-- Zustand als Text
---------------------------------------------------------------------------
local function yes(b) return b and "|cff40ff40" .. L["ja"] .. "|r" or "|cffff5544" .. L["nein"] .. "|r" end

function D.Text()
	local out = {}
	local function add(s) out[#out + 1] = s end
	local A = RM.Auction
	add("|cffff8c1aRaidMaster " .. RM.VERSION .. "|r – " .. RM.GameInfoText())
	add("")
	add("|cffffd200" .. L["Versteigerung"] .. "|r")
	local c = A.current
	if c then
		local state
		if A.AwaitingAward() then
			state = "|cffffaa33" .. L["fertig – wartet auf Vergeben / Nicht vergeben"] .. "|r"
		elseif c.finished then
			state = L["fertig"]
		else
			local rem = math.ceil((c.endsAt or 0) - GetTime())
			state = rem >= 0 and string.format(L["läuft, noch %d Sek."], rem) or ("|cffff5544" .. string.format(L["Zeit seit %d Sek. abgelaufen – hängt"], -rem) .. "|r")
		end
		add("  " .. L["Aktuell: "] .. tostring(c.link) .. " – " .. state)
		add("  " .. L["Höchstgebot: "] .. (c.highName and (c.high .. " DKP (" .. c.highName .. ")") or "–"))
	else
		add("  " .. L["Keine laufende Versteigerung."])
	end
	local list, from = A.ViewQueue()
	add("  " .. string.format(L["Warteschlange: %d Item(s)"], #A.queue) .. (from and (" · " .. string.format(L["angezeigt wird die vom Plündermeister %s (%d)"], from, #list)) or ""))
	for i, q in ipairs(A.queue) do if i <= 8 then add("    " .. i .. ". " .. tostring(q.link)) end end
	local ok, why = A.CanRun()
	add("  " .. L["Darf ich versteigern: "] .. yes(ok) .. (why and (" – " .. why) or ""))
	if A.client and not A.client.ended then
		add("  " .. L["Gebotsfenster offen für: "] .. tostring(A.client.link))
	end
	add("")
	add("|cffffd200" .. L["Loot und Raid"] .. "|r")
	add("  " .. L["Im Schlachtzug: "] .. yes(RM.InRaid()) .. "   " .. L["Raidleiter: "] .. yes(RM.IsLeader()) .. "   " .. L["Volle Rechte: "] .. yes(RM.CanEdit()))
	if RM.RightsInfo then
		local ri = RM.RightsInfo()
		add("  " .. string.format(L["Rechte: %s · Raidleiter im Raid: %s · Gildenrang %s (%s)"],
			ri.me or "?", ri.leader or "–", ri.rank ~= nil and tostring(ri.rank) or "?", ri.rankName or (ri.inGuild and "?" or L["keine Gilde"])))
		if ri.owner then add("  |cff40ff40" .. L["Eigentümer: immer alle Rechte."] .. "|r") end
		if not RM.CanEdit() then
			add("  |cffffaa33" .. L["Volle Rechte hat der Raidleiter des aktuellen Raids (und der Eigentümer). Assistenten und Raidmitglieder haben keine."] .. "|r")
		end
		if RM.Test and RM.Test.active then
			add("  |cffff5544" .. string.format(L["Testmodus läuft – Ansicht als %s."], RM.Test.RoleName()) .. "|r")
		end
	end
	add("  " .. L["Plündermethode: "] .. tostring(RM.GetLootMethod() or "?") .. "   " .. L["Plündermeister: "] .. tostring(RM.MasterLooterName() or "–")
		.. "   " .. L["Ich bin Plündermeister: "] .. yes(RM.IAmMasterLooter()))
	if RM.Loot.Problems then
		for _, p in ipairs(RM.Loot.Problems()) do add("  |cffff5544! " .. p .. "|r") end
	end
	local s = RM.db.session
	add("  " .. L["Raid-Sitzung: "] .. (s.active and (string.format(L["aktiv seit %s"], date("%H:%M", s.started)) .. " (" .. RM.DKP.PoolName(s.pool or "mc") .. ")") or L["keine"]))
	for _, fn in ipairs(D.providers) do
		local okp, lines = pcall(fn)
		if okp and type(lines) == "table" and #lines > 0 then
			add("")
			for _, l in ipairs(lines) do add(l) end
		end
	end
	add("")
	add("|cffffd200" .. string.format(L["Fehler (%d)"], #D.errors) .. "|r")
	if #D.errors == 0 then
		add("  |cff40ff40" .. L["Keine Fehler seit dem Einloggen."] .. "|r")
	else
		for _, e in ipairs(D.errors) do
			add("  |cffff5544" .. date("%H:%M:%S", e.t) .. (e.n > 1 and (" (" .. e.n .. "x)") or "") .. "|r " .. e.msg:gsub("Interface\\AddOns\\", ""))
		end
	end
	return table.concat(out, "\n")
end

---------------------------------------------------------------------------
-- Typische Hänger lösen
---------------------------------------------------------------------------
function D.Fix()
	local done = {}
	local A = RM.Auction
	local c = A.current
	if A.AwaitingAward() then
		A.AskAward()
		done[#done + 1] = L["Vergabe-Fenster wieder angezeigt (Vergeben / Nicht vergeben / Neu versteigern)."]
	elseif c and not c.finished and (c.endsAt or 0) + 3 < GetTime() then
		A.Finish()
		done[#done + 1] = L["Abgelaufene Versteigerung beendet."]
	elseif c and c.finished and not c.highName then
		A.current = nil
		done[#done + 1] = L["Beendete Versteigerung ohne Gebote aufgeräumt."]
	end
	if A.client and A.client.ended then
		A.client = nil
		if A.HideBidFrame then A.HideBidFrame() end
		done[#done + 1] = L["Altes Gebotsfenster geschlossen."]
	end
	for _, fn in ipairs(D.fixers) do
		local okf, lines = pcall(fn)
		if okf and type(lines) == "table" then for _, l in ipairs(lines) do done[#done + 1] = l end end
	end
	RM.Fire("AUCTION_CHANGED")
	if #done == 0 then done[1] = L["Kein Hänger gefunden."] end
	for _, l in ipairs(done) do RM.Print(l) end
	return done
end

---------------------------------------------------------------------------
-- Fenster
---------------------------------------------------------------------------
function D.Refresh()
	if D.window then D.window.box:SetText(D.Text()) end
end

function D.Show()
	if not D.window then
		local f = UI.Frame(UIParent, 640, 500)
		f:SetFrameStrata("DIALOG")
		f:SetClampedToScreen(true)
		UI.Skin(f)
		UI.MakeMovable(f, "diag", "CENTER", 0, 0)
		_G["RaidMasterDiag"] = f
		tinsert(UISpecialFrames, "RaidMasterDiag")
		local title = UI.Header(f, L["Diagnose"])
		title:SetPoint("TOPLEFT", 12, -10)
		local hint = UI.Text(f, L["Zeigt, ob etwas hängt oder ein Fehler aufgetreten ist. Bei Problemen einen Screenshot davon weitergeben."], 11, unpack(COLORS.muted))
		hint:SetPoint("TOPLEFT", 12, -32)
		hint:SetWidth(600)
		local close = UI.CloseButton(f, function() f:Hide() end)
		close:SetPoint("TOPRIGHT", -6, -6)
		f.box = UI.Multiline(f, 616, 380, true)
		f.box:SetPoint("TOPLEFT", 12, -56)
		local fix = UI.Button(f, L["Hänger lösen"], 150, 26, function() D.Fix(); D.Refresh() end,
			L["Zeigt eine offene Vergabe wieder an, beendet abgelaufene Versteigerungen und räumt alte Fenster auf."])
		fix:SetPoint("BOTTOMLEFT", 12, 12)
		fix:SetAccent(true)
		local refresh = UI.Button(f, L["Aktualisieren"], 130, 26, function() D.Refresh() end)
		refresh:SetPoint("LEFT", fix, "RIGHT", 8, 0)
		local clear = UI.Button(f, L["Fehler leeren"], 130, 26, function() wipe(D.errors); D.Refresh() end)
		clear:SetPoint("LEFT", refresh, "RIGHT", 8, 0)
		f.elapsed = 0
		f:SetScript("OnUpdate", function(self, el)
			self.elapsed = self.elapsed + el
			if self.elapsed > 1 and not self.box.edit:HasFocus() and not (self.box.IsMouseOver and self.box:IsMouseOver()) then
				self.elapsed = 0
				D.Refresh()
			end
		end)
		D.window = f
	end
	D.window:Show()
	D.Refresh()
end

function D.Toggle()
	if D.window and D.window:IsShown() then D.window:Hide() else D.Show() end
end
