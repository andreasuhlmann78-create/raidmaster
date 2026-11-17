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
-- Testmodus-Erkennung (GoldSentinelDev): nur ob erkannt – nie der BattleTag
table.insert(D.providers, function()
	if GoldSentinelDev and GoldSentinelDev.Status then return { GoldSentinelDev:Status() } end
	return {}
end)
-- Erkannte Spielversion und API (GoldSentinelGame)
table.insert(D.providers, function()
	if GoldSentinelGame and GoldSentinelGame.Status then return { GoldSentinelGame.Status() } end
	return {}
end)
D.fixers = {}          -- weitere Reparaturen: function() return { "erledigt: ..." } end

---------------------------------------------------------------------------
-- Fehler sammeln: alles, was aus RaidMaster-Dateien kommt (auch aus Timern und Fenstern)
---------------------------------------------------------------------------
-- RM-DIAG-1 (3.0.29): Im Spiel des Nutzers "Diag.lua:-1: insecure scripts exceeded execution limit for addon RaidMaster",
-- jedes Bild. Bis 3.0.28 baute D.Record bei JEDEM Fehler das ganze Diagnose-Fenster neu auf (D.Text + EditBox:SetText –
-- ":-1" = in einer C-Funktion, die Diag.lua aufrief), sobald das Fenster offen war. Die Meldung über die Ausführungsgrenze
-- enthält selbst "RaidMaster" -> wurde wieder erfasst -> wieder neu aufgebaut -> wieder zu lang: eine Schleife jedes Bild.
-- Jetzt: Erfassen ist billig und begrenzt; das Fenster wird höchstens einmal pro Sekunde und nur bei Änderung neu gesetzt.
D.MAX_MSG = 400        -- Zeichen je Fehlertext (mehr braucht die Anzeige nicht)
D.MAX_PER_SEC = 20     -- mehr neue Erfassungen pro Sekunde -> nur noch gezählt (Fehlerflut)
D.dropped = 0          -- in der Flut nicht mehr einzeln erfasst
D.dirty = false        -- Fenster muss neu aufgebaut werden
local secNow, secCount = 0, 0

function D.Record(msg)
	msg = tostring(msg or "?")
	if #msg > D.MAX_MSG then msg = msg:sub(1, D.MAX_MSG) .. " …" end
	local now = time()
	for _, e in ipairs(D.errors) do
		if e.msg == msg then e.n = e.n + 1; e.t = now; D.dirty = true return end
	end
	if now ~= secNow then secNow, secCount = now, 0 end
	secCount = secCount + 1
	if secCount > D.MAX_PER_SEC then D.dropped = D.dropped + 1; D.dirty = true return end
	table.insert(D.errors, 1, { t = now, msg = msg, n = 1 })
	while #D.errors > 20 do table.remove(D.errors) end
	D.dirty = true                          -- kein Neuaufbau hier: das macht das Fenster selbst, höchstens 1x pro Sekunde
end

-- Zähler der laufenden Sekunde zurücksetzen (Testroutine, "Fehler leeren")
function D.ResetRate() secNow, secCount = 0, 0 end

-- RM-DIAG-1 Messung (3.0.30, Auftrag des Supervisors 16.11.): Wie viele Fehler gehen durch unseren Handler, und aus
-- welchem Addon? Nur Zahlen je Quelle (kein Fehlertext – könnte Namen enthalten). Klärt, ob eine Fehlerflut aus einem
-- anderen Addon kam und WoW sie RaidMaster nur zurechnete, weil unser Handler zuoberst in der Kette liegt.
D.sources = {}         -- [Addon] = Anzahl
D.sourcesTotal = 0
D.firstSource = nil    -- { src = Addon, t = Zeit } – erste Meldung seit dem Laden
local MAX_SOURCES = 30

-- Quelle aus dem Text: "… for addon 'X'" (Ausführungsgrenze, Aktion blockiert) gewinnt, sonst der erste Pfad AddOns\X\
function D.SourceOf(text)
	local a = text:match("[Ff]or [Aa]dd[Oo]n '?\"?([%w_%-]+)")
	if not a then a = text:match("[Aa]dd[Oo]ns[/\\]([%w_%-]+)") end
	return a or "?"
end

function D.CountSource(text)
	local src = D.SourceOf(text)
	if D.sources[src] == nil then
		local n = 0
		for _ in pairs(D.sources) do n = n + 1 end
		if n >= MAX_SOURCES then src = "andere" end
	end
	D.sources[src] = (D.sources[src] or 0) + 1
	D.sourcesTotal = D.sourcesTotal + 1
	if not D.firstSource then D.firstSource = { src = src, t = time() } end
end

-- Eine Zeile für Testbericht und Diagnose-Fenster: "FEHLERQUELLEN: 1142 · AHSentinel 1100, RaidMaster 42 · zuerst AHSentinel 09:30:12"
function D.SourcesLine()
	if D.sourcesTotal == 0 then return "FEHLERQUELLEN: 0" end
	local list = {}
	for k, v in pairs(D.sources) do list[#list + 1] = { k = k, v = v } end
	table.sort(list, function(a, b) if a.v ~= b.v then return a.v > b.v end return a.k < b.k end)
	local parts = {}
	for i = 1, math.min(8, #list) do parts[i] = list[i].k .. " " .. list[i].v end
	local first = D.firstSource and (" · zuerst " .. D.firstSource.src .. " " .. date("%H:%M:%S", D.firstSource.t)) or ""
	return "FEHLERQUELLEN: " .. D.sourcesTotal .. " · " .. table.concat(parts, ", ") .. first
end

-- Fehler-Handler: Zähler je Quelle und ein Textvergleich, sonst nichts (läuft bei JEDEM Fehler jedes Addons)
function D.OnError(msg)
	local text = type(msg) == "string" and msg or tostring(msg)
	pcall(D.CountSource, text)
	if text:find("RaidMaster", 1, true) then D.Record(text) end
end

-- in den Fehler-Handler des Spiels einklinken (nach dem Einloggen noch einmal, falls ein
-- Fehler-Addon wie BugGrabber den Handler danach ersetzt hat)
-- Ab 3.0.18: Hängt ein anderes Addon (z. B. der gemeinsame Abgriff von GoldSentinelTest aus einem anderen
-- GoldSentinel-Addon) seinen Handler davor und reicht an unseren alten weiter, läge RaidMaster nach dem zweiten
-- Einklinken zweimal in der Kette – jeder Fehler wurde doppelt gezählt (Testroutine T122: n = 6 statt 3).
-- Darum zählt nur der zuletzt eingeklinkte Handler; ältere reichen nur noch weiter.
local ours, generation = nil, 0
local function Hook()
	if not (seterrorhandler and geterrorhandler) then return end
	local previous = geterrorhandler()
	if previous == ours then return end
	generation = generation + 1
	local mine = generation
	ours = function(msg, ...)
		if mine == generation then pcall(D.OnError, msg) end
		if previous then return previous(msg, ...) end
	end
	seterrorhandler(ours)
end
D.Hook = Hook
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
		add("  " .. L["Plündermeister: "] .. yes(ri.looter) .. "   " .. L["Assistent: "] .. yes(ri.assist))
		if not RM.CanEdit() then
			add("  |cffffaa33" .. L["Volle Rechte hat der Raidleiter des aktuellen Raids. Der Plündermeister darf versteigern, Assistenten z. B. markieren."] .. "|r")
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
		if not okp then RM.ReportError("Diag.provider", lines) end
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
			add("  |cffff5544" .. date("%H:%M:%S", e.t) .. (e.n > 1 and (" (" .. e.n .. "x)") or "") .. "|r " .. (e.msg:gsub("Interface\\AddOns\\", "")))
		end
	end
	add("  " .. D.SourcesLine())
	if D.dropped > 0 then add("  |cffff5544" .. string.format(L["… und %d weitere Fehler in kurzer Zeit (nicht einzeln erfasst)"], D.dropped) .. "|r") end
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
		if not okf then RM.ReportError("Diag.fixer", lines) end
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
-- Nur setzen, wenn sich der Text geändert hat (SetText einer grossen EditBox ist teuer)
function D.Refresh()
	if not D.window then return end
	D.dirty = false
	local text = D.Text()
	if text == D.window.box.text then return end
	D.window.box:SetText(text)
end

function D.Show()
	if not D.window then
		local f = UI.Frame(UIParent, 640, 500, "Diagnose")
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
		local clear = UI.Button(f, L["Fehler leeren"], 130, 26, function() wipe(D.errors); D.dropped = 0; D.ResetRate(); D.Refresh() end)
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
