-- GoldSentinelDev - Testmodus-Erkennung fuer alle Addons von GoldSentinel
-- Copyright (C) 2026 GoldSentinel
--
-- Diese Datei in jedes Addon kopieren und in der .toc VOR den eigenen Dateien eintragen.
-- Mehrere Addons duerfen sie gleichzeitig mitbringen: die neueste Version gewinnt, alle teilen dieselbe Pruefung.
--
-- Erkennung:
--   1) BattleTag des Battle.net-Kontos (gespeichert nur als Pruefsumme, nicht als Klartext).
--   2) Liefert das Spiel keinen BattleTag (Battle.net nicht verfuegbar), gilt die Liste der Charaktere als Ersatz.
--      Liefert das Spiel einen fremden BattleTag, hilft der Charaktername nicht.
--
-- Benutzung im Addon:
--   if GoldSentinelDev:IsDev() then ... end                 -- nur pruefen
--   if GoldSentinelDev:Require("MeinAddon") then ... end    -- pruefen und sonst einen Hinweis im Chat zeigen
--   GoldSentinelDev:Status()                                -- Text fuer Diagnose ("Testmodus: an · BattleTag: ja")
--   /gsdev                                                  -- zeigt im Chat, ob der Testmodus erkannt wird
--
-- Hinweis: Addons sind offener Lua-Code. Das ist keine Sicherung gegen Leute, die den Code aendern, sondern haelt
-- Test- und Entwicklerfunktionen fuer alle anderen Spieler unsichtbar.

local VERSION = 1

local existing = _G.GoldSentinelDev
if type(existing) == "table" and (existing.version or 0) >= VERSION then return end

local Dev = type(existing) == "table" and existing or {}
_G.GoldSentinelDev = Dev
Dev.version = VERSION

-- Pruefsummen erlaubter BattleTags (Kleinbuchstaben, ohne Leerzeichen; siehe Dev.Hash)
Dev.TAGS = { [1913314458] = true }
-- Ersatz, wenn das Spiel keinen BattleTag liefert: Charakternamen (Kleinbuchstaben)
Dev.CHARS = { dontdiems = true }

-- Pruefsumme eines BattleTags (djb2, 32 Bit)
function Dev.Hash(tag)
    local t = tostring(tag or ""):gsub("%s", ""):lower()
    local h = 5381
    for i = 1, #t do h = (h * 33 + t:byte(i)) % 4294967296 end
    return h
end

local known = false        -- einmal erkannt, bleibt erkannt (Battle.net ist beim Laden manchmal noch nicht bereit)
Dev.tagSeen = false

local function BattleTag()
    if not BNGetInfo then return nil end
    local ok, _, tag = pcall(BNGetInfo)
    if ok and type(tag) == "string" and tag ~= "" then return tag end
    return nil
end

function Dev:IsDev()
    if known then return true end
    local tag = BattleTag()
    local ok = false
    self.tagSeen = tag ~= nil
    if tag then
        ok = self.TAGS[self.Hash(tag)] == true
    else
        local name = UnitName and UnitName("player")
        ok = type(name) == "string" and self.CHARS[name:lower()] == true
    end
    if ok then known = true end
    return ok
end

-- Pruefen und bei Bedarf einen Hinweis zeigen (addon = Name fuer die Meldung)
function Dev:Require(addon)
    if self:IsDev() then return true end
    if DEFAULT_CHAT_FRAME then
        DEFAULT_CHAT_FRAME:AddMessage((addon and ("|cffffb238" .. addon .. "|r: ") or "")
            .. self:Text("blocked"))
    end
    return false
end

-- kurze Texte in der Sprache des Spiels
local TEXTS = {
    deDE = { blocked = "Diese Funktion gehört zum Testmodus und ist nur für den Entwickler freigeschaltet.",
             on = "an", off = "aus", yes = "ja", no = "nein", mode = "Testmodus", tag = "BattleTag vom Spiel geliefert" },
    enUS = { blocked = "This function belongs to test mode and is only unlocked for the developer.",
             on = "on", off = "off", yes = "yes", no = "no", mode = "Test mode", tag = "BattleTag provided by the game" },
    frFR = { blocked = "Cette fonction fait partie du mode test et n'est disponible que pour le développeur.",
             on = "activé", off = "désactivé", yes = "oui", no = "non", mode = "Mode test", tag = "BattleTag fourni par le jeu" },
    esES = { blocked = "Esta función pertenece al modo de prueba y solo está disponible para el desarrollador.",
             on = "activado", off = "desactivado", yes = "sí", no = "no", mode = "Modo de prueba", tag = "BattleTag entregado por el juego" },
    ptBR = { blocked = "Esta função faz parte do modo de teste e só está liberada para o desenvolvedor.",
             on = "ligado", off = "desligado", yes = "sim", no = "não", mode = "Modo de teste", tag = "BattleTag fornecido pelo jogo" },
    itIT = { blocked = "Questa funzione fa parte della modalità test ed è disponibile solo per lo sviluppatore.",
             on = "attiva", off = "disattiva", yes = "sì", no = "no", mode = "Modalità test", tag = "BattleTag fornito dal gioco" },
    ruRU = { blocked = "Эта функция относится к тестовому режиму и доступна только разработчику.",
             on = "вкл.", off = "выкл.", yes = "да", no = "нет", mode = "Тестовый режим", tag = "BattleTag от игры" },
    koKR = { blocked = "이 기능은 테스트 모드에 속하며 개발자만 사용할 수 있습니다.",
             on = "켜짐", off = "꺼짐", yes = "예", no = "아니요", mode = "테스트 모드", tag = "게임이 제공한 BattleTag" },
    zhCN = { blocked = "此功能属于测试模式，仅对开发者开放。",
             on = "开", off = "关", yes = "是", no = "否", mode = "测试模式", tag = "游戏提供的BattleTag" },
    zhTW = { blocked = "此功能屬於測試模式，僅對開發者開放。",
             on = "開", off = "關", yes = "是", no = "否", mode = "測試模式", tag = "遊戲提供的BattleTag" },
}
TEXTS.esMX = TEXTS.esES
TEXTS.enGB = TEXTS.enUS

function Dev:Text(key)
    local loc = GetLocale and GetLocale() or "enUS"
    local t = TEXTS[loc] or TEXTS.enUS
    return t[key] or TEXTS.enUS[key] or key
end

-- Diagnose-Zeile (ohne den BattleTag selbst)
function Dev:Status()
    local on = self:IsDev()
    return string.format("%s: %s · %s: %s", self:Text("mode"), self:Text(on and "on" or "off"),
        self:Text("tag"), self:Text(self.tagSeen and "yes" or "no"))
end

-- /gsdev: Status im Chat (zeigt nur an, ob erkannt - nie den BattleTag)
if SlashCmdList and not SlashCmdList.GOLDSENTINELDEV then
    SLASH_GOLDSENTINELDEV1 = "/gsdev"
    SlashCmdList.GOLDSENTINELDEV = function()
        if DEFAULT_CHAT_FRAME then DEFAULT_CHAT_FRAME:AddMessage("|cffffb238GoldSentinel|r: " .. Dev:Status()) end
    end
end
