-- RM-TAINT1 (3.0.48, Supervisor 25.11. 08:59): Addon- und Testcode ruft nie Funktionen, die Blizzard-Fenster öffnen oder schliessen.
-- Anlass: die Testroutine öffnete das Charakterfenster selbst (ToggleCharacter) -> Lua-Fehler "execution tainted by 'RaidMaster'".
-- Prüft alle .lua-Dateien unter ADDONDIR (auch Test/), Kommentare ausgenommen. Rückgabe: Liste "Datei:Zeile: Name".
local M = {}
M.NAMES = { "ToggleCharacter", "ShowUIPanel", "HideUIPanel", "ToggleFrame", "ToggleSpellBook", "ToggleFriendsFrame",
	"ToggleGuildFrame", "ToggleWorldMap", "ToggleQuestLog", "ToggleTalentFrame", "ToggleGameMenu", "OpenAllBags",
	"ToggleBackpack", "ToggleBag", "CloseAllWindows", "ShowFriends", "ToggleAchievementFrame", "ToggleCollectionsJournal" }

-- eine Zeile ohne Kommentar (nicht in Zeichenketten) -> gefundene Namen (Aufruf, Übergabe an pcall, Zuweisung)
local function Strip(line)
	local out, i, q = {}, 1, nil
	while i <= #line do
		local c = line:sub(i, i)
		if q then
			if c == "\\" then i = i + 1 elseif c == q then q = nil end
			out[#out + 1] = " "
		elseif c == '"' or c == "'" then q = c; out[#out + 1] = " "
		elseif line:sub(i, i + 1) == "--" then break
		else out[#out + 1] = c end
		i = i + 1
	end
	return table.concat(out)
end
M.Strip = Strip

function M.ScanText(text, file)
	local hits, n, inBlock = {}, 0, false
	for line in (text .. "\n"):gmatch("([^\n]*)\n") do
		n = n + 1
		if inBlock then
			if line:find("%]%]") then inBlock = false end
		elseif line:match("^%s*%-%-%[%[") then
			inBlock = not line:find("%]%]")
		else
			local code = " " .. Strip(line)
			for _, name in ipairs(M.NAMES) do
				for pre in code:gmatch("(.)" .. name .. "%f[^%w_]") do
					if pre ~= "." and pre ~= ":" and not pre:match("[%w_]") then hits[#hits + 1] = file .. ":" .. n .. ": " .. name end
				end
			end
		end
	end
	return hits
end

function M.ScanDir(dir)
	local hits, files = {}, 0
	local p = io.popen('find "' .. dir .. '" -name "*.lua" | sort')
	for f in p:lines() do
		local h = io.open(f, "rb")
		local text = h:read("*a"); h:close()
		files = files + 1
		for _, x in ipairs(M.ScanText(text, f:sub(#dir + 2))) do hits[#hits + 1] = x end
	end
	p:close()
	return hits, files
end
return M
