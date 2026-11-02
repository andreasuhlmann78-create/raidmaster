-- GoldSentinelGame - einheitliche Spielversion-Erkennung für alle Addons von GoldSentinel
-- Copyright (C) 2026 GoldSentinel
--
-- Diese Datei in jedes Addon kopieren und in der .toc VOR den eigenen Dateien eintragen
-- (zusammen mit GoldSentinelDev.lua). Mehrere Addons dürfen sie gleichzeitig mitbringen:
-- die neueste Version gewinnt, alle teilen dieselbe Erkennung.
--
-- Inhalt:
--   GoldSentinelGame.flavor     "era" | "forever" | "tbc" | "wrath" | "cata" | "mists" | "retail" (nil = unbekannt)
--   GoldSentinelGame.interface  Interface-Nummer (z. B. 11509, 20506, 16001, 120105)
--   GoldSentinelGame.version    Spielversion als Text (z. B. "1.60.1"), build = Build-Nummer
--   GoldSentinelGame.IsEra / IsTBC / IsForever / IsRetail   (true/false)
--   GoldSentinelGame.IsModern   Forever oder Retail: moderne API mit Addon-Sperren (Kampflog zu,
--                               im Kampf geschützte Werte möglich)
--   GoldSentinelGame.HasSecrets issecretvalue ist vorhanden (sagt nichts über die Spielversion)
--   GoldSentinelGame.IsSecret(v)  sicherer Test: false, wenn issecretvalue fehlt
--   GoldSentinelGame.Safe(v)      v, oder nil wenn v geschützt ist
--   GoldSentinelGame.ShortName(n) Name ohne Realm ("Vor Nach-Realm" -> "Vor Nach"); nil wenn geschützt
--   GoldSentinelGame.SameName(a, b) gleicher Charakter? (ohne Realm, ohne Gross/Klein, Leerzeichen
--                                 zusammengefasst - auch für Vor- und Nachnamen in Forever)
--
-- Erkennung (Vorbild: Flavor.lua aus ProfessionSentinel):
--   forever = WOW_PROJECT_CAMELOT oder Interface 16000-16999 (vor allen anderen Bereichen geprüft)
--   era = 10000-19999 (ohne Forever), tbc = 2xxxx, wrath = 3xxxx, cata = 4xxxx, mists = 5xxxx,
--   retail = ab 100000 oder WOW_PROJECT_MAINLINE

local VERSION = 1

local existing = _G.GoldSentinelGame
if type(existing) == "table" and (existing.apiVersion or 0) >= VERSION then return end

local G = type(existing) == "table" and existing or {}
_G.GoldSentinelGame = G
G.apiVersion = VERSION

local version, build, _, interface = GetBuildInfo()
interface = tonumber(interface) or 0
G.version, G.build, G.interface = version, build, interface

local function project(name)
	local id = _G[name]
	return id ~= nil and WOW_PROJECT_ID ~= nil and WOW_PROJECT_ID == id
end

local flavor
if project("WOW_PROJECT_CAMELOT") or (interface >= 16000 and interface < 17000) then
	flavor = "forever"
elseif interface >= 100000 or project("WOW_PROJECT_MAINLINE") then
	flavor = "retail"
elseif interface >= 10000 and interface < 20000 then
	flavor = "era"
elseif interface >= 20000 and interface < 30000 then
	flavor = "tbc"
elseif interface >= 30000 and interface < 40000 then
	flavor = "wrath"
elseif interface >= 40000 and interface < 50000 then
	flavor = "cata"
elseif interface >= 50000 and interface < 60000 then
	flavor = "mists"
end

G.flavor = flavor
G.IsEra = flavor == "era"
G.IsTBC = flavor == "tbc"
G.IsForever = flavor == "forever"
G.IsRetail = flavor == "retail"
G.IsModern = G.IsForever or G.IsRetail
G.HasSecrets = issecretvalue ~= nil

function G.IsSecret(v)
	if issecretvalue then return issecretvalue(v) and true or false end
	return false
end

function G.Safe(v)
	if G.IsSecret(v) then return nil end
	return v
end

------------------------------------------------------------
-- Namen (Forever: Vor- und Nachnamen mit Leerzeichen möglich)
------------------------------------------------------------
-- Charakternamen enthalten keinen Bindestrich: der erste trennt den Realm ab
function G.ShortName(name)
	if name == nil or G.IsSecret(name) or type(name) ~= "string" then return nil end
	local short = name:match("^([^%-]+)") or name
	short = short:gsub("^%s+", ""):gsub("%s+$", "")
	return short
end

local function Norm(name)
	local s = G.ShortName(name)
	if not s then return nil end
	s = s:gsub("%s+", " ")
	return (string.lower and s:lower()) or s
end
G.NormName = Norm

function G.SameName(a, b)
	local na, nb = Norm(a), Norm(b)
	return na ~= nil and na == nb
end
