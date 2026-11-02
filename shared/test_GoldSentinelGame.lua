-- Test für GoldSentinelGame.lua (gemeinsame Versionserkennung aller GoldSentinel-Addons)
local pass, fail = 0, 0
local function check(c, m) if c then pass = pass + 1 else fail = fail + 1; print("FAIL: " .. m) end end
local function Load(toc, opts)
	opts = opts or {}
	_G.GoldSentinelGame = opts.keep and _G.GoldSentinelGame or nil
	GetBuildInfo = function() return "x", "1", "d", toc end
	issecretvalue = opts.secret
	WOW_PROJECT_ID, WOW_PROJECT_CAMELOT, WOW_PROJECT_MAINLINE = opts.pid, opts.camelot, opts.mainline
	assert(loadfile("GoldSentinelGame.lua"))()
	return _G.GoldSentinelGame
end
local cases = {
	{ 11508, "era" }, { 11509, "era" }, { 16001, "forever" }, { 16002, "forever" }, { 20505, "tbc" }, { 20506, "tbc" },
	{ 30403, "wrath" }, { 40402, "cata" }, { 50500, "mists" }, { 120105, "retail" },
}
for _, c in ipairs(cases) do
	local G = Load(c[1])
	check(G.flavor == c[2], c[1] .. " -> " .. c[2] .. " (ist " .. tostring(G.flavor) .. ")")
end
local G = Load(16001)
check(G.IsForever and G.IsModern and not G.IsEra and not G.IsTBC, "Forever: IsForever und IsModern")
G = Load(11508)
check(not G.IsModern and G.IsEra, "Era: nicht modern")
G = Load(99999, { pid = 7, camelot = 7 })
check(G.flavor == "forever", "WOW_PROJECT_CAMELOT erkennt Forever auch bei unbekannter Nummer")
G = Load(11508, { secret = function(v) return v == "geheim" end })
check(G.IsModern, "issecretvalue vorhanden -> modern")
check(G.IsSecret("geheim") and not G.IsSecret("offen"), "IsSecret")
check(G.Safe("geheim") == nil and G.Safe("offen") == "offen", "Safe")
G = Load(11508)
check(G.IsSecret("x") == false, "ohne issecretvalue: nie secret")
check(G.ProperName("rokan steinwacht-WoWForever") == "Rokan Steinwacht", "ProperName: jedes Wort, ohne Realm")
check(G.ProperName("aRTHAS") == "Arthas", "ProperName einfach")
check(G.SameName("Rokan-Realm", "rokan"), "SameName ohne Realm")
check(not G.SameName("Rokan", "Rokan Steinwacht"), "Era: Vorname allein passt nicht")
G = Load(16001)
check(G.SameName("Rokan", "Rokan Steinwacht"), "Forever: Vorname allein passt")
check(not G.SameName("Mira", "Mira Sonne", function() return false end), "Forever: nicht eindeutig -> kein Treffer")
check(not G.SameName("Rokan Steinwacht", "Rokan Felsbart"), "zwei volle Namen verschieden")
-- neueste Version gewinnt
_G.GoldSentinelGame = { version = 99, flavor = "fremd" }
GetBuildInfo = function() return "x", "1", "d", 11508 end
assert(loadfile("GoldSentinelGame.lua"))()
check(_G.GoldSentinelGame.flavor == "fremd", "neuere Version eines anderen Addons bleibt")
print(string.format("\n%d bestanden, %d fehlgeschlagen, 0 Fehlermeldungen", pass, fail))
os.exit(fail == 0 and 0 or 1)
