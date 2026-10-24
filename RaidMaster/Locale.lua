-- RaidMaster - Sprache
-- Erkennt die im Spiel eingestellte Sprache. Grundsprache ist Deutsch; die Dateien im Ordner
-- Locales liefern die Übersetzungen. Fehlt eine Übersetzung, wird der deutsche Text angezeigt.

local ADDON, RM = ...

RM.LANGUAGES = {
	deDE = "Deutsch", enUS = "English", frFR = "Français", esES = "Español (España)", esMX = "Español (México)",
	itIT = "Italiano", ptBR = "Português (Brasil)", ruRU = "Русский", koKR = "한국어", zhCN = "简体中文", zhTW = "繁體中文",
}

local locale = (GetLocale and GetLocale()) or "enUS"
if locale == "enGB" then locale = "enUS" end
-- Sprachen, die es nicht gibt, bekommen Englisch
if not RM.LANGUAGES[locale] then locale = "enUS" end
RM.LOCALE = locale
RM.GAME_LOCALE = (GetLocale and GetLocale()) or "?"

-- L["deutscher Text"] liefert die Übersetzung oder den deutschen Text
RM.L = setmetatable({}, { __index = function(_, key) return key end })
