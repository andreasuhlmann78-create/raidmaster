-- __ADDON__ – Zugriff auf die Spiel-API und Aktionen mit Folgen
-- Copyright (c) 2026 GoldSentinel. All Rights Reserved.
--
-- ns.API: Jede Blizzard-Funktion, die das Addon braucht, wird HIER einmal beim Laden ausgewählt (moderne C_*-Funktion
-- zuerst, alte Funktion als Rückfall für Classic Era/TBC). Der übrige Code ruft nur ns.API.X auf.
-- Vorteile: kein "taint" (wir ersetzen nie eine Blizzard-Funktion), und die Testroutine kann ns.API-Einträge
-- gefahrlos durch Attrappen ersetzen und alte/moderne Clients nachstellen.
--
-- ns.Act: Jede Aktion mit Folgen (Chat-Nachricht, Kauf, Herstellen, Einladen, Wegpunkt …) läuft über diese eine
-- Stelle. Im Testmodus (ns.testing) wird sie nur mitgeschrieben (ns.actLog), nie ausgeführt.

local ADDON, ns = ...
local G = ns.G

local API = {}
ns.API = API

local function pick(...)
    for i = 1, select("#", ...) do
        local f = select(i, ...)
        if type(f) == "function" then return f end
    end
    return nil
end

-- Beispiele – nur aufnehmen, was das Addon wirklich braucht ---------------------------------------------------------
API.GetItemInfo   = pick(C_Item and C_Item.GetItemInfo, GetItemInfo)
API.GetSpellName  = pick(C_Spell and C_Spell.GetSpellName,
                         GetSpellInfo and function(id) return (GetSpellInfo(id)) end)
API.GetNumSlots   = pick(C_Container and C_Container.GetContainerNumSlots, GetContainerNumSlots)
API.GetItemID     = pick(C_Container and C_Container.GetContainerItemID, GetContainerItemID)
API.GetAddOnMeta  = pick(C_AddOns and C_AddOns.GetAddOnMetadata, GetAddOnMetadata)
API.UnitName      = pick(UnitName)
API.SendChat      = pick(C_ChatInfo and C_ChatInfo.SendChatMessage, SendChatMessage)

-- Auren: modern über C_UnitAuras, alt über UnitAura (in Forever gibt es UnitAura nicht mehr)
function API.GetAura(unit, index, filter)
    if C_UnitAuras and C_UnitAuras.GetAuraDataByIndex then
        return C_UnitAuras.GetAuraDataByIndex(unit, index, filter)
    elseif UnitAura then
        local name, icon, count, _, duration, expires, _, _, _, spellId = UnitAura(unit, index, filter)
        if name then return { name = name, icon = icon, applications = count, duration = duration,
                              expirationTime = expires, spellId = spellId } end
    end
    return nil
end

-- Name einer Einheit, sicher: nil, wenn er geschützt ist (Ziel/Boss im Kampf in Forever) – nie vergleichen,
-- zerlegen oder als Schlüssel benutzen, ohne vorher so zu prüfen.
function ns.SafeUnitName(unit)
    if not API.UnitName then return nil end
    local name = API.UnitName(unit)
    if name == nil or G.IsSecret(name) then return nil end
    return name
end

---------------------------------------------------------------------------------------------------------------------
-- Aktionen mit Folgen
---------------------------------------------------------------------------------------------------------------------
ns.actLog = {}

-- ns.Act("chat", fn, ...) -> true, wenn ausgeführt; im Test false (nur mitgeschrieben)
function ns.Act(kind, fn, ...)
    if ns.testing then
        table.insert(ns.actLog, { kind = kind, n = select("#", ...) })
        return false
    end
    if type(fn) ~= "function" then return false end
    return ns.Try("Aktion " .. tostring(kind), fn, ...)
end

-- Beispiel: Chat-Nachricht senden (nur über ns.Act)
function ns.SendChat(msg, channel, target)
    return ns.Act("chat", API.SendChat, msg, channel, nil, target)
end
