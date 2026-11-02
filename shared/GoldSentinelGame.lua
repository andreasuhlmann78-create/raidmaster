-- GoldSentinelGame - gemeinsame Spielversions-Erkennung fuer alle Addons von GoldSentinel
-- Copyright (C) 2026 GoldSentinel
--
-- Diese Datei in jedes Addon kopieren und in der .toc VOR den eigenen Dateien eintragen
-- (direkt nach GoldSentinelDev.lua). Mehrere Addons duerfen sie gleichzeitig mitbringen:
-- die neueste Version gewinnt, alle teilen dieselbe Erkennung.
-- Referenzkopie: raidmaster-Repo, shared/GoldSentinelGame.lua (dort zuerst aendern, VERSION erhoehen).
--
-- WICHTIG: WoW Forever sieht aus wie Classic, laeuft technisch aber auf dem MODERNEN Client
-- (C_TradeSkillUI, C_Container, Retail-Berufsfenster, Secret Values). Forever ist also NIE "Classic".
--
-- Benutzung im Addon:
--   local G = GoldSentinelGame
--   G.flavor        "era" | "forever" | "tbc" | "wrath" | "cata" | "mists" | "retail" | nil (unbekannt)
--   G.IsForever     WoW Forever (Interface 16000-19999 oder WOW_PROJECT_CAMELOT)
--   G.IsEra         Classic Era / Hardcore / Season (Interface 11400-11599)
--   G.IsRetail      Retail (Interface 100000+ oder WOW_PROJECT_MAINLINE)
--   G.IsClassic     Era, TBC, Wrath, Cata, MoP Classic - NICHT Forever
--   G.IsModern      Forever oder Retail (moderne API; auch wenn das Spiel issecretvalue kennt)
--   G.interface     Interface-Nummer (z. B. 16001), G.version ("1.60.1"), G.build ("70707")
--   G.IsSecret(v)   true, wenn v ein Secret Value ist (false, wenn das Spiel keine kennt)
--   G.Safe(v)       v, oder nil wenn v ein Secret Value ist (zum gefahrlosen Rechnen/Vergleichen)
--   G:Status()      Diagnose-Text, /gsgame zeigt ihn im Chat

local VERSION = 1

local existing = _G.GoldSentinelGame
if type(existing) == "table" and (existing.version or 0) >= VERSION then return end

local G = type(existing) == "table" and existing or {}
_G.GoldSentinelGame = G
G.version = VERSION                 -- Version dieser Datei (nicht des Spiels: G.gameVersion)

local version, build, _, interface = "", "", nil, 0
if GetBuildInfo then
    local ok, v, b, _, i = pcall(GetBuildInfo)
    if ok then version, build, interface = v or "", b or "", tonumber(i) or 0 end
end
G.interface = interface
G.gameVersion = version
G.build = build

local function project(name)
    local p = _G[name]
    return p ~= nil and WOW_PROJECT_ID ~= nil and WOW_PROJECT_ID == p
end

-- Projekt-Konstanten zuerst (eindeutig), dann die Interface-Nummer
local flavor
if project("WOW_PROJECT_CAMELOT") or (interface >= 16000 and interface < 20000) then
    flavor = "forever"
elseif project("WOW_PROJECT_MAINLINE") or interface >= 100000 then
    flavor = "retail"
elseif interface >= 11400 and interface < 11600 then
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
G.IsForever = flavor == "forever"
G.IsRetail = flavor == "retail"
G.IsEra = flavor == "era"
G.IsClassic = flavor == "era" or flavor == "tbc" or flavor == "wrath" or flavor == "cata" or flavor == "mists"
G.HasSecrets = type(issecretvalue) == "function"
G.IsModern = G.IsForever or G.IsRetail or (G.HasSecrets and not G.IsClassic)

-- Secret Values (Addon-Sperren im Kampf): sicher pruefen, nie selbst einen Fehler ausloesen
function G.IsSecret(v)
    local f = issecretvalue
    if type(f) ~= "function" then return false end
    local ok, res = pcall(f, v)
    return ok and res == true
end

function G.Safe(v)
    if G.IsSecret(v) then return nil end
    return v
end

function G:Status()
    return string.format("Spiel: %s · Interface %s · %s.%s · moderne API: %s · Secret Values: %s · GoldSentinelGame v%d",
        tostring(self.flavor or "unbekannt"), tostring(self.interface), tostring(self.gameVersion), tostring(self.build),
        self.IsModern and "ja" or "nein", self.HasSecrets and "ja" or "nein", self.version)
end

-- /gsgame: Diagnose im Chat
if SlashCmdList and not SlashCmdList.GOLDSENTINELGAME then
    SLASH_GOLDSENTINELGAME1 = "/gsgame"
    SlashCmdList.GOLDSENTINELGAME = function()
        if DEFAULT_CHAT_FRAME then DEFAULT_CHAT_FRAME:AddMessage("|cffffb238GoldSentinel|r: " .. G:Status()) end
    end
end
