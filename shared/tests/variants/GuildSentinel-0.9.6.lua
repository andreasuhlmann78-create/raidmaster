-- GoldSentinelGame - gemeinsame Versionserkennung für alle Addons von GoldSentinel
-- Copyright (C) 2026 GoldSentinel
--
-- Diese Datei in jedes Addon kopieren und in der .toc VOR den eigenen Dateien eintragen (wie GoldSentinelDev.lua).
-- Mehrere Addons dürfen sie gleichzeitig mitbringen: die neueste Version gewinnt, alle teilen dieselbe Erkennung.
--
-- Benutzung im Addon:
--   GoldSentinelGame.flavor          "era" | "forever" | "tbc" | "wrath" | "cata" | "mists" | "retail" | "unknown"
--   GoldSentinelGame.interface       Interface-Nummer des Clients (z. B. 11508, 16001, 20506, 120105)
--   GoldSentinelGame.IsForever       WoW Forever (Interface 16000-16999 oder WOW_PROJECT_CAMELOT)
--   GoldSentinelGame.IsEra / IsTBC / IsRetail
--   GoldSentinelGame.IsModern        moderner Client mit Addon-Sperren (Forever oder Retail; Kern: issecretvalue vorhanden)
--   GoldSentinelGame.IsSecret(v)     true, wenn v ein "secret value" ist (false, wenn es issecretvalue nicht gibt)
--   GoldSentinelGame.Safe(v)         v, oder nil wenn secret
--   GoldSentinelGame.ProperName(n)   "rokan steinwacht" -> "Rokan Steinwacht" (jedes Wort gross, Realm weg)
--   GoldSentinelGame.SameName(a, b, isUnique)
--                                    gleicher Spieler? Forever: Vorname allein passt, wenn eindeutig
--                                    (isUnique(vorname) optional, z. B. Prüfung gegen die Gildenliste)
--
-- Vorbild für die Erkennung: Flavor.lua in ProfessionSentinel.

local VERSION = 1

local existing = _G.GoldSentinelGame
if type(existing) == "table" and (existing.version or 0) >= VERSION then return end

local G = type(existing) == "table" and existing or {}
_G.GoldSentinelGame = G
G.version = VERSION

local _, _, _, interface = GetBuildInfo()
interface = tonumber(interface) or 0
G.interface = interface

local flavor
if (WOW_PROJECT_CAMELOT and WOW_PROJECT_ID == WOW_PROJECT_CAMELOT) or (interface >= 16000 and interface < 17000) then
	flavor = "forever"
elseif interface >= 100000 or (WOW_PROJECT_MAINLINE and WOW_PROJECT_ID == WOW_PROJECT_MAINLINE) then
	flavor = "retail"
elseif interface >= 50000 then
	flavor = "mists"
elseif interface >= 40000 then
	flavor = "cata"
elseif interface >= 30000 then
	flavor = "wrath"
elseif interface >= 20000 then
	flavor = "tbc"
elseif interface >= 10000 then
	flavor = "era"
else
	flavor = "unknown"
end

G.flavor = flavor
G.IsForever = flavor == "forever"
G.IsEra = flavor == "era"
G.IsTBC = flavor == "tbc"
G.IsRetail = flavor == "retail"
-- moderner Client: Forever und Retail laufen mit denselben Addon-Sperren (secret values im Kampf)
G.IsModern = G.IsForever or G.IsRetail or (issecretvalue ~= nil)

-- secret value? (sicher auch auf Clients ohne issecretvalue)
function G.IsSecret(v)
	return issecretvalue ~= nil and issecretvalue(v) and true or false
end

-- v, oder nil wenn secret
function G.Safe(v)
	if G.IsSecret(v) then return nil end
	return v
end

-- Name ohne Realm, jedes Wort mit grossem Anfangsbuchstaben (Umlaute bleiben)
local function CapWord(w)
	local first = w:match("^[%z\1-\127\194-\244][\128-\191]*") or w:sub(1, 1)
	return first:upper() .. w:sub(#first + 1):lower()
end
function G.ProperName(name)
	if type(name) ~= "string" or G.IsSecret(name) then return nil end
	name = name:gsub("%-.*$", ""):gsub("^%s+", ""):gsub("%s+$", ""):gsub("%s+", " ")
	if name == "" then return name end
	return (name:gsub("%S+", CapWord))
end

-- gleicher Spieler? Ohne Realm, ohne Gross-/Kleinschreibung. Auf Forever passt ein Vorname allein zum vollen
-- Namen, wenn einer der beiden nur den Vornamen hat – und (falls isUnique angegeben) der Vorname eindeutig ist.
function G.SameName(a, b, isUnique)
	if type(a) ~= "string" or type(b) ~= "string" or G.IsSecret(a) or G.IsSecret(b) then return false end
	a = a:gsub("%-.*$", ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
	b = b:gsub("%-.*$", ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
	if a == b then return true end
	if not G.IsForever then return false end
	if a:find(" ") and b:find(" ") then return false end
	local fa, fb = a:match("^(%S+)"), b:match("^(%S+)")
	if not fa or fa ~= fb then return false end
	if isUnique then return isUnique(fa) and true or false end
	return true
end
