-- GoldSentinelGame - gemeinsame Spielversions-Erkennung fuer alle Addons von GoldSentinel
-- Copyright (C) 2026 GoldSentinel
--
-- Diese Datei in jedes Addon kopieren und in der .toc VOR den eigenen Dateien eintragen
-- (am besten direkt nach GoldSentinelDev.lua). Mehrere Addons duerfen sie gleichzeitig mitbringen:
-- die neueste Version gewinnt, alle teilen dieselbe Erkennung.
--
-- Warum? Es gibt zwei API-Welten in einem Code:
--   ALTE API    : Classic Era, TBC, Wrath (auch Titan Reforged), Cataclysm Classic, Mists of Pandaria Classic
--   MODERNE API : WoW Forever und Retail
-- WoW Forever sieht aus wie Classic, laeuft aber auf dem modernen Client mit denselben Addon-Sperren wie Retail:
-- Kampflog fuer Addons zu, im Kampf kommen manche Werte als "secret values" (anzeigen geht; rechnen, vergleichen,
-- verketten oder als Tabellenschluessel benutzen gibt einen Lua-Fehler). Forever darf deshalb NIE wie Classic Era
-- behandelt werden, wenn es um die API geht.
--
-- Benutzung im Addon:
--   local G = GoldSentinelGame
--   G.flavor                 -- "era" | "forever" | "tbc" | "wrath" | "titan" | "cata" | "mists" | "retail" | "unknown"
--   G.IsForever, G.IsRetail, G.IsEra ...   -- true/false
--   G.IsModern               -- moderner Client (Forever oder Retail) -> moderne API, Kampf-Sperren beachten
--   G.HasSecrets             -- der Client kennt secret values (issecretvalue vorhanden)
--   G.IsSecret(v)            -- true, wenn v ein geschuetzter Wert ist (sicher, auch ohne issecretvalue)
--   G.AnySecret(a, b, ...)   -- true, wenn einer der Werte geschuetzt ist
--   G.Safe(v)                -- v, oder nil wenn geschuetzt
--   G.InCombat()             -- InCombatLockdown(), sicher
--   G.Short(name)            -- Name ohne Realm ("Testa-Server" -> "Testa"), nil bei geschuetztem Namen
--   G.CleanName(name)        -- Name saeubern und gross schreiben (Forever: Vor- und Nachname behalten)
--   G.SameName(a, b)         -- gleicher Charakter? (Forever: Vorname allein passt, wenn eine Seite nur ihn kennt)
--   G.Status()               -- Text fuer die Diagnose
--   /gsgame                  -- zeigt im Chat, was erkannt wurde
--
-- Fuer Selbsttests: G.SetTestFlavor("forever") erzwingt eine Version, G.SetTestFlavor(nil) hebt das wieder auf.
--
-- Version 3: nur Kommentare/Beispiele geändert (keine Spielernamen im öffentlichen Repo), Code wie Version 2
-- Version 2: setzt sich gegen fruehe, zurueckgenommene Fassungen durch, die ebenfalls "Version 1" hiessen
-- (GuildSentinel 0.9.6, ThreatSentinel 2.3.0, BuffSentinel 0.9.2, ProfessionSentinel 0.9.3), und bringt deren
-- Funktionsnamen als Ersatz mit (G.ProperName, G.ShortName, G.NormName, G.IsClassic, G.interface, G.apiVersion,
-- G.SameName mit drittem Parameter isUnique), damit Addons mit so einer Fassung keine Lua-Fehler bekommen.
-- Fuer neuen Code bitte nur die oben beschriebenen Namen benutzen.

local VERSION = 3

-- Vorhandene Fassung pruefen. "version" ist hier die Dateiversion (Zahl). Eine fruehe Fassung nutzte dafuer
-- "apiVersion" und speicherte in "version" die Spielversion als Text ("1.60.1") - beides beachten und nie
-- Text mit Zahl vergleichen (das waere ein Lua-Fehler beim Laden).
local existing = _G.GoldSentinelGame
if type(existing) == "table" then
    local have = math.max(tonumber(existing.apiVersion) or 0,
        type(existing.version) == "number" and existing.version or 0)
    if have >= VERSION then return end
end

local G = type(existing) == "table" and existing or {}
_G.GoldSentinelGame = G
G.version = VERSION
G.apiVersion = VERSION   -- gleicher Wert unter dem Namen der fruehen Fassung (damit auch sie zurueckweicht)

---------------------------------------------------------------------------
-- Spielversion erkennen
---------------------------------------------------------------------------
-- TOC-Bereiche (Reihenfolge wichtig: Titan vor Wrath)
G.RANGES = {
    { key = "retail",  from = 100000, to = 999999 },
    { key = "mists",   from = 50000,  to = 59999 },
    { key = "cata",    from = 40000,  to = 49999 },
    { key = "titan",   from = 38000,  to = 38999 },
    { key = "wrath",   from = 30000,  to = 37999 },
    { key = "tbc",     from = 20000,  to = 29999 },
    { key = "forever", from = 16000,  to = 19999 },
    { key = "era",     from = 10000,  to = 15999 },
}

-- Versionen mit moderner API (moderner Client, Kampf-Sperren)
G.MODERN = { forever = true, retail = true }

local function ReadBuild()
    local version, build, date, toc
    if GetBuildInfo then
        local ok, v, b, d, t = pcall(GetBuildInfo)
        if ok then version, build, date, toc = v, b, d, t end
    end
    G.gameVersion = version or "?"
    G.build = build or "?"
    G.buildDate = date or "?"
    G.toc = tonumber(toc) or 0
    G.interface = G.toc   -- Ersatzname aus frueher Fassung
end

local function DetectFlavor()
    -- 1) WoW Forever meldet sich mit eigenem Projekt (WOW_PROJECT_CAMELOT)
    if WOW_PROJECT_ID and WOW_PROJECT_CAMELOT and WOW_PROJECT_ID == WOW_PROJECT_CAMELOT then return "forever" end
    if WOW_PROJECT_ID and WOW_PROJECT_MAINLINE and WOW_PROJECT_ID == WOW_PROJECT_MAINLINE then return "retail" end
    -- 2) sonst ueber die Interface-Nummer
    for _, r in ipairs(G.RANGES) do
        if G.toc >= r.from and G.toc <= r.to then return r.key end
    end
    return "unknown"
end

local testFlavor = nil

function G.Recalc()
    ReadBuild()
    G.HasSecrets = type(issecretvalue) == "function"
    G.flavor = testFlavor or DetectFlavor()
    G.IsEra     = G.flavor == "era"
    G.IsForever = G.flavor == "forever"
    G.IsTBC     = G.flavor == "tbc"
    G.IsWrath   = G.flavor == "wrath" or G.flavor == "titan"
    G.IsTitan   = G.flavor == "titan"
    G.IsCata    = G.flavor == "cata"
    G.IsMists   = G.flavor == "mists"
    G.IsRetail  = G.flavor == "retail"
    -- Moderne API: nach Version ODER weil der Client secret values kennt (dann gelten die Sperren sicher)
    G.IsModern = G.MODERN[G.flavor] == true or (testFlavor == nil and G.HasSecrets) or false
    -- Alte Classic-API (Classic Era, TBC, Wrath, Cata, MoP Classic) - Forever gehoert NICHT dazu
    G.IsOldAPI = not G.IsModern
    -- Ersatzname aus frueher Fassung: Classic-Versionen mit alter API (ohne "unknown")
    G.IsClassic = G.IsOldAPI and G.flavor ~= "unknown"
end

-- Nur fuer Selbsttests: eine Version erzwingen (nil = wieder echt erkennen)
function G.SetTestFlavor(flavor)
    testFlavor = flavor
    G.Recalc()
end

G.Recalc()

---------------------------------------------------------------------------
-- Geschuetzte Werte ("secret values")
---------------------------------------------------------------------------
function G.IsSecret(v)
    if v == nil or type(issecretvalue) ~= "function" then return false end
    local ok, res = pcall(issecretvalue, v)
    return ok and res == true
end

function G.AnySecret(...)
    for i = 1, select("#", ...) do
        if G.IsSecret((select(i, ...))) then return true end
    end
    return false
end

function G.Safe(v)
    if G.IsSecret(v) then return nil end
    return v
end

function G.InCombat()
    return InCombatLockdown and InCombatLockdown() and true or false
end

---------------------------------------------------------------------------
-- Namen (WoW Forever: Charaktere haben Vor- und Nachnamen, z. B. "Testa Beispiel")
---------------------------------------------------------------------------
-- Name ohne Realm. Geschuetzte oder ungueltige Namen -> nil (nie mit ihnen rechnen!)
function G.Short(name)
    if G.IsSecret(name) or type(name) ~= "string" then return nil end
    return (name:gsub("%-.*$", ""))
end

-- Name saeubern: Leerraum, Realm weg, jedes Wort gross. In Forever bleibt das Leerzeichen zwischen Vor- und
-- Nachname erhalten, sonst werden Leerzeichen entfernt. (Wie CapName in RaidMaster.)
function G.CleanName(name)
    name = G.Short(name)
    if not name then return nil end
    if G.IsForever then
        name = name:gsub("^%s+", ""):gsub("%s+$", ""):gsub("%s+", " ")
    else
        name = name:gsub("%s", "")
    end
    if name == "" then return "" end
    return (name:gsub("(%S)(%S*)", function(a, b) return a:upper() .. b:lower() end))
end

-- Gleicher Charakter? Gross/klein und Realm egal. In Forever passt auch der Vorname allein, wenn eine Seite
-- nur den Vornamen kennt ("Testa" = "Testa Beispiel"). Zwei verschiedene volle Namen passen nie.
-- (Wie RM.SameName in RaidMaster.)
function G.SameName(a, b, isUnique)
    a, b = G.Short(a), G.Short(b)
    if not a or not b then return false end
    a = a:lower():gsub("^%s+", ""):gsub("%s+$", "")
    b = b:lower():gsub("^%s+", ""):gsub("%s+$", "")
    if a == "" or b == "" then return false end
    if a == b then return true end
    if not G.IsForever then return false end
    local fa, fb = a:match("^(%S+)"), b:match("^(%S+)")
    if (not a:find(" ") or not b:find(" ")) and fa == fb then
        -- optional (aus frueher Fassung): isUnique(vorname) prueft, ob der Vorname eindeutig ist
        if type(isUnique) == "function" then
            local ok, res = pcall(isUnique, fa)
            return ok and res and true or false
        end
        return true
    end
    return false
end

---------------------------------------------------------------------------
-- Ersatznamen aus frueheren Fassungen (nur damit alter Code weiterlaeuft - fuer neuen Code nicht benutzen)
---------------------------------------------------------------------------
-- Name ohne Realm, Leerraum gekuerzt (Leerzeichen zwischen Vor- und Nachname bleibt)
function G.ShortName(name)
    local s = G.Short(name)
    if not s then return nil end
    return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

-- Name ohne Realm, Leerraum zusammengefasst, klein geschrieben (zum Vergleichen)
function G.NormName(name)
    local s = G.ShortName(name)
    if not s then return nil end
    return (s:gsub("%s+", " "):lower())
end

-- Name ohne Realm, jedes Wort gross (in allen Versionen mit Leerzeichen; Umlaute am Wortanfang bleiben ganz)
local function CapWord(w)
    local first = w:match("^[%z\1-\127\194-\244][\128-\191]*") or w:sub(1, 1)
    return first:upper() .. w:sub(#first + 1):lower()
end
function G.ProperName(name)
    local s = G.ShortName(name)
    if not s then return nil end
    s = s:gsub("%s+", " ")
    if s == "" then return s end
    return (s:gsub("%S+", CapWord))
end

---------------------------------------------------------------------------
-- Texte und Diagnose
---------------------------------------------------------------------------
local NAMES = {
    era = "Classic Era", forever = "WoW Forever", tbc = "The Burning Crusade Classic",
    wrath = "Wrath of the Lich King Classic", titan = "Wrath of the Lich King (Titan Reforged)",
    cata = "Cataclysm Classic", mists = "Mists of Pandaria Classic", retail = "Retail", unknown = "?",
}

local TEXTS = {
    deDE = { game = "Spielversion", api = "API", modern = "modern (Kampf-Sperren)", old = "alt",
             secrets = "Geschützte Werte", yes = "ja", no = "nein", test = "Test" },
    enUS = { game = "Game version", api = "API", modern = "modern (combat restrictions)", old = "old",
             secrets = "Secret values", yes = "yes", no = "no", test = "test" },
    frFR = { game = "Version du jeu", api = "API", modern = "moderne (restrictions en combat)", old = "ancienne",
             secrets = "Valeurs protégées", yes = "oui", no = "non", test = "test" },
    esES = { game = "Versión del juego", api = "API", modern = "moderna (restricciones en combate)", old = "antigua",
             secrets = "Valores protegidos", yes = "sí", no = "no", test = "prueba" },
    ptBR = { game = "Versão do jogo", api = "API", modern = "moderna (restrições em combate)", old = "antiga",
             secrets = "Valores protegidos", yes = "sim", no = "não", test = "teste" },
    itIT = { game = "Versione del gioco", api = "API", modern = "moderna (restrizioni in combattimento)", old = "vecchia",
             secrets = "Valori protetti", yes = "sì", no = "no", test = "test" },
    ruRU = { game = "Версия игры", api = "API", modern = "новый (ограничения в бою)", old = "старый",
             secrets = "Защищённые значения", yes = "да", no = "нет", test = "тест" },
    koKR = { game = "게임 버전", api = "API", modern = "최신 (전투 중 제한)", old = "구버전",
             secrets = "보호된 값", yes = "예", no = "아니요", test = "테스트" },
    zhCN = { game = "游戏版本", api = "API", modern = "新版（战斗限制）", old = "旧版",
             secrets = "受保护的值", yes = "是", no = "否", test = "测试" },
    zhTW = { game = "遊戲版本", api = "API", modern = "新版（戰鬥限制）", old = "舊版",
             secrets = "受保護的值", yes = "是", no = "否", test = "測試" },
}
TEXTS.esMX = TEXTS.esES
TEXTS.enGB = TEXTS.enUS

function G.Text(key)
    local loc = GetLocale and GetLocale() or "enUS"
    local t = TEXTS[loc] or TEXTS.enUS
    return t[key] or TEXTS.enUS[key] or key
end

function G.FlavorName(flavor)
    return NAMES[flavor or G.flavor] or NAMES.unknown
end

-- Diagnose-Zeile, z. B. "Spielversion: WoW Forever (1.60.1, 16001) · API: modern (Kampf-Sperren) · Geschützte Werte: ja"
function G.Status()
    local name = G.FlavorName() .. (testFlavor and (" [" .. G.Text("test") .. "]") or "")
    return string.format("%s: %s (%s, %d) · %s: %s · %s: %s",
        G.Text("game"), name, tostring(G.gameVersion), G.toc,
        G.Text("api"), G.Text(G.IsModern and "modern" or "old"),
        G.Text("secrets"), G.Text(G.HasSecrets and "yes" or "no"))
end

-- /gsgame: Erkennung im Chat zeigen
if SlashCmdList and not SlashCmdList.GOLDSENTINELGAME then
    SLASH_GOLDSENTINELGAME1 = "/gsgame"
    SlashCmdList.GOLDSENTINELGAME = function()
        if DEFAULT_CHAT_FRAME then DEFAULT_CHAT_FRAME:AddMessage("|cffffb238GoldSentinel|r: " .. G.Status()) end
    end
end
