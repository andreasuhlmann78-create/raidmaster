#!/usr/bin/env python3
"""Prüft Addon-ZIPs von GoldSentinel, BEVOR sie veröffentlicht werden.

Warum: Im November 2026 wurden mehrere Addons mit eigenen, untereinander unverträglichen Fassungen der gemeinsamen
Datei GoldSentinelGame.lua veröffentlicht (eine davon auf CurseForge). Dieses Skript verhindert solche Fehler:

  FEHLER (Veröffentlichung wird gestoppt)
  - gemeinsame Datei GoldSentinelGame.lua weicht von shared/GoldSentinelGame.lua ab (oder wird nachgebaut)
  - gemeinsame Datei GoldSentinelDev.lua: Kopie mit gleicher Version, aber anderem Inhalt
  - Versionsnummer nicht höher als eine schon veröffentlichte (Discord-ZIPs, CurseForge) bzw. ZIP-Name passt nicht
  - gleiche Versionsnummer schon einmal mit ANDEREM Inhalt veröffentlicht (Spieler bekämen das Update nie)
  - .toc-Dateien eines Addons mit unterschiedlicher Version; in der .toc genannte Datei fehlt in der ZIP
  - Lua-Syntaxfehler (geprüft mit Lua 5.1 wie im Spiel)
  - GoldSentinelGame.lua steht in der .toc nicht vor den eigenen Dateien des Addons

  WARNUNG (Veröffentlichung geht, aber bitte prüfen)
  - bekannte Fallen der modernen API (Forever/Retail): alte Funktion ohne Ersatz, z. B. UnitAura ohne C_UnitAuras
  - .lua-Datei liegt im Addon, steht aber in keiner .toc; Interface 16001 (WoW Forever) fehlt
  - GoldSentinelGame.lua fehlt im Addon; GoldSentinelDev.lua veraltet (eine andere Kopie hat eine höhere Version)

Aufruf:
  python3 addon-check/addon_check.py                 alle ZIPs in download/ prüfen
  python3 addon-check/addon_check.py a.zip b.zip     nur diese ZIPs
  python3 addon-check/addon_check.py --report r.md   zusätzlich Bericht als Markdown schreiben
Rückgabe: 0 = keine Fehler, 1 = mindestens ein Fehler.
Als Modul (z. B. aus curseforge/upload.py): check_zip(path) -> Liste von Befunden (level, text).

Neue Fallen ergänzen: Liste TRAPS unten. Neue gemeinsame Datei: Liste SHARED unten.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD = ROOT / "download"
ANNOUNCE = ROOT / "announce"
SHARED_DIR = ROOT / "shared"
UPLOADED = ROOT / "curseforge" / "uploaded.json"
# Weitere Ordner mit schon veröffentlichten ZIPs (z. B. setzt der Discord-Bot hier seine Ordner addon/ und announce/
# ein – dort hat er keine Git-Geschichte, kennt aber alles, was er schon gepostet hat)
EXTRA_DIRS = []

# Gemeinsame Dateien: Name -> Regel
#   "exact"   : jede Kopie muss Byte für Byte der Vorlage in shared/ entsprechen
#   "version" : Kopien mit gleicher VERSION müssen gleich sein; ältere Kopien nur Warnung
SHARED = {
    "GoldSentinelGame.lua": "exact",
    "GoldSentinelTest.lua": "exact",
    "GoldSentinelSync.lua": "exact",
    "GoldSentinelDev.lua": "version",
}
# Wer GoldSentinelGame selbst nachbaut (statt die Datei zu kopieren), schreibt das hier:
REIMPL = re.compile(r"_G\.GoldSentinel(?:Game|Test)\s*=|^\s*GoldSentinel(?:Game|Test)\s*=", re.M)

# Bekannte Fallen der modernen API. Jede Regel: Muster im Code, Ersatz, der in DERSELBEN Datei vorkommen muss
# (sonst Warnung), und eine kurze Erklärung. Kommentarzeilen werden vorher entfernt.
TRAPS = [
    (r"\bUnitAura\s*\(", r"C_UnitAuras", "UnitAura fehlt im modernen Client -> C_UnitAuras (sonst liefert die Funktion still nichts)"),
    (r"\bUnitBuff\s*\(|\bUnitDebuff\s*\(", r"C_UnitAuras", "UnitBuff/UnitDebuff fehlen im modernen Client -> C_UnitAuras"),
    (r"\bGetSpellInfo\s*\(", r"C_Spell", "GetSpellInfo fehlt im modernen Client -> C_Spell.GetSpellInfo/GetSpellName"),
    (r"\bGetSpellCooldown\s*\(", r"C_Spell", "GetSpellCooldown fehlt im modernen Client -> C_Spell.GetSpellCooldown"),
    (r"\bGetContainer(?:NumSlots|ItemInfo|ItemLink|ItemID)\s*\(", r"C_Container", "GetContainer* fehlt im modernen Client -> C_Container"),
    (r"\bGetMerchantNumItems\b", r"C_MerchantFrame", "GetMerchantNumItems ohne C_MerchantFrame.GetNumItems als Ersatz"),
    (r"\bGetMerchantItemInfo\b", r"C_MerchantFrame", "GetMerchantItemInfo ohne C_MerchantFrame.GetItemInfo als Ersatz"),
    (r"\bGetAddOnMetadata\s*\(|\bIsAddOnLoaded\s*\(", r"C_AddOns", "GetAddOnMetadata/IsAddOnLoaded fehlen im modernen Client -> C_AddOns"),
    (r"\bInterfaceOptions_AddCategory\b", r"Settings", "InterfaceOptions_AddCategory fehlt im modernen Client -> Settings-API"),
    (r"\bEasyMenu\s*\(", r"MenuUtil|Settings", "EasyMenu fehlt im modernen Client"),
    (r"\bGetNumTradeSkills\s*\(|\bGetTradeSkillInfo\s*\(", r"C_TradeSkillUI", "alte Berufe-API ohne C_TradeSkillUI (Berufsfenster bleibt in Forever leer)"),
    (r"\bGetQuestLogTitle\s*\(", r"C_QuestLog", "GetQuestLogTitle fehlt im modernen Client -> C_QuestLog"),
    (r"\bGetPlayerMapPosition\s*\(", r"C_Map", "GetPlayerMapPosition fehlt im modernen Client -> C_Map.GetPlayerMapPosition"),
    (r"RegisterEvent[^\n]*COMBAT_LOG_EVENT_UNFILTERED|\bOn\(\s*[\"']COMBAT_LOG_EVENT_UNFILTERED",
     r"IsModern|IsOldAPI|isModern|restricted|[Cc]ombatLog\b|hasCombatLog|< *16000",
     "Kampflog wird ohne erkennbare Sperre registriert – in Forever/Retail für Addons zu, nur für die alte API registrieren"),
    (r"\bissecretvalue\s*\(", r"GoldSentinelGame|function\s+\w*[Ii]s[Ss]ecret", "issecretvalue direkt benutzt -> GoldSentinelGame.IsSecret (sicher, auch wenn die Funktion fehlt)"),
]

# Blizzard-Funktionen, die ein Addon nie ersetzen darf. Wer sie überschreibt (auch nur im Test und danach
# zurückgesetzt), "taintet" sie bis zum /reload: Blizzard-Code, der sie danach aufruft, wird blockiert.
# Dazu gilt jede Zuweisung an C_<Namensraum>.<Funktion>. Lokale Kopien (local UnitName = UnitName) sind erlaubt.
BLIZZ_GLOBALS = set("""
UnitName UnitFullName GetUnitName UnitGUID UnitClass UnitClassBase UnitLevel UnitRace UnitSex UnitFactionGroup UnitExists
UnitIsPlayer UnitIsUnit UnitIsDead UnitIsDeadOrGhost UnitIsConnected UnitIsFriend UnitIsEnemy UnitCanAttack UnitReaction
UnitHealth UnitHealthMax UnitPower UnitPowerMax UnitPowerType UnitAffectingCombat UnitInRaid UnitInParty UnitIsGroupLeader
UnitIsGroupAssistant UnitGroupRolesAssigned UnitDetailedThreatSituation UnitThreatSituation UnitCastingInfo UnitChannelInfo
UnitAura UnitBuff UnitDebuff UnitCreatureType UnitClassification UnitPosition
GetServerTime GetTime GetGameTime GetRealmName GetNormalizedRealmName GetBuildInfo GetLocale GetGuildInfo
GetNumGroupMembers GetNumSubgroupMembers GetRaidRosterInfo IsInGroup IsInRaid IsInGuild IsInInstance GetInstanceInfo
GetZoneText GetRealZoneText GetSubZoneText GetMinimapZoneText InCombatLockdown GetMoney GetItemInfo GetItemCount
GetSpellInfo GetSpellCooldown IsSpellKnown GetNumGuildMembers GetGuildRosterInfo GuildRoster
SendChatMessage SendAddonMessage BuyMerchantItem RepairAllItems GetRepairAllCost CanMerchantRepair TakeTaxiNode
SelectGossipOption AcceptQuest CompleteQuest GetQuestReward PlaySound PlaySoundFile CreateFrame
GetAddOnMetadata IsAddOnLoaded LoadAddOn GetCursorPosition IsShiftKeyDown IsControlKeyDown IsAltKeyDown
GetMerchantNumItems GetMerchantItemInfo GetMerchantItemLink GetMerchantItemID GetMerchantItemCostInfo
GetMerchantItemCostItem GetFactionInfoByID GetFactionInfo GetContainerNumSlots GetContainerItemID GetContainerItemInfo
GetContainerItemLink GetTradeSkillInfo GetNumTradeSkills GetProfessions GetProfessionInfo GetSkillLineInfo GetNumSkillLines
""".split())
_TARGET = r"(?:_G\s*\.\s*\w+|_G\s*\[\s*[\"']\w+[\"']\s*\]|C_\w+\s*[.:]\s*\w+|[A-Za-z_]\w*)"
# Anweisungsanfang: Zeilenanfang, ; oder nach then/do/else/repeat (auch mehrere Ziele: A, B = …)
BLIZZ_ASSIGN = re.compile(
    r"(?:^|;|\bthen\b|\bdo\b|\belse\b|\brepeat\b)[ \t]*(?P<a>" + _TARGET + r"(?:\s*,\s*" + _TARGET + r")*)\s*=(?!=)"
    r"|(?:^|;|\bthen\b|\bdo\b|\belse\b|\brepeat\b)[ \t]*function\s+(?P<f>" + _TARGET + r")\s*\("
    r"|\brawset\s*\(\s*_G\s*,\s*[\"'](?P<r>\w+)[\"']", re.M)
_LUA_KEYWORDS = set("and break do else elseif end false for function goto if in local nil not or repeat return then true "
                    "until while".split())
# Ereignisse für die Bereichs-Verfolgung (auf Code ohne Strings/Kommentare)
_SCOPE_TOKENS = re.compile(
    r"\blocal\s+(?=function\s+(?P<lf>\w+))"
    r"|\blocal\s+(?P<lv>\w+(?:\s*,\s*\w+)*)(?=(?P<lrhs>\s*=[^\n;]*)|)"
    r"|\bfunction\b[^(\n]*\((?P<params>[^)]*)\)"
    r"|\bfor\s+(?P<fv>\w+(?:\s*,\s*\w+)*)\s*(?:=|\bin\b)"
    r"|(?P<open>\b(?:do|if|repeat)\b)|(?P<close>\b(?:end|until)\b)|(?P<lb>\{)|(?P<rb>\})")

# Schon veröffentlichte Versionen, die eine neue FEHLER-Regel verletzen: Dort nur Warnung, damit nicht jeder Push rot wird.
# Die nächste Version muss es beheben. Eintrag entfernen, sobald die Version aus download/ verschwunden ist.
ALTLAST = set()   # zurzeit keine Altlasten; Einträge: ("addon", "x.y.z")

# Testdateien (eigene Testroutinen der Addons, nicht shared/GoldSentinelTest.lua)
# Gross geschriebenes "Test" (SelfTest, TestMode, Test.lua) oder ein Ordner Test/ bzw. Tests/; nicht Latest.lua, Contest.lua
TEST_FILE = re.compile(r"(?:^|/)(?:Tests?/[^/]+\.lua|\w*Test\w*\.lua|test\w*\.lua)$")
# Aktionen mit Folgen: im Test nur mitschreiben, nie wirklich auslösen (nachtrag-testroutinen.txt)
TEST_ACTIONS = re.compile(
    r"(?<![\w.:])(?:C_ChatInfo\s*\.\s*)?(?:SendChatMessage|SendAddonMessage)\s*\("
    r"|(?<![\w.:])(?:BuyMerchantItem|RepairAllItems|PickupMerchantItem|DoTradeSkill|DoCraft|TakeTaxiNode"
    r"|PlaceAuctionBid|PostAuction|StartAuction|GuildInvite|GuildUninvite|GuildPromote|GuildDemote|InviteUnit"
    r"|UninviteUnit|SetLootMethod|ConvertToRaid|DeleteCursorItem|SellCursorItem|AcceptQuest|CompleteQuest|GetQuestReward)\s*\("
    r"|\bC_TradeSkillUI\s*\.\s*Craft\w*\s*\("
    r"|\bC_AuctionHouse\s*\.\s*(?:PostItem|PostCommodity|PlaceBid|StartCommoditiesPurchase|ConfirmCommoditiesPurchase)\s*\("
    r"|\bC_PartyInfo\s*\.\s*(?:InviteUnit|ConvertToRaid|LeaveParty)\s*\("
    r"|\bC_GuildInfo\s*\.\s*(?:Invite|Uninvite|Promote|Demote|RemoveFromGuild)\w*\s*\("
    r"|\bC_MerchantFrame\s*\.\s*(?:BuyItem|SellItem)\w*\s*\(")
# Namen von Ziel, Boss, Fokus … sind in Forever im Kampf "secret": :lower(), Vergleiche und Tabellenschlüssel brechen dann
# (Zusammensetzen mit .. und Weitergeben sind erlaubt, das Ergebnis bleibt geheim)
SECRET_UNIT = r"[\"'](?:target|focus|mouseover|boss\d?|targettarget|arena\d|nameplate\d+)[\"']"
SECRET_USE = re.compile(
    r"\b(?:UnitName|GetUnitName|UnitFullName)\s*\(\s*" + SECRET_UNIT + r"[^()]*\)\s*(?::\s*\w+\s*\(|[=~]=\s*[\"']|\])"
    r"|\[\s*(?:UnitName|GetUnitName|UnitFullName)\s*\(\s*" + SECRET_UNIT
    + r"|\b(?:strlower|string\.lower|strupper|string\.upper|strsub|string\.sub|string\.find|strfind|string\.match|strmatch|gsub|string\.gsub)"
    r"\s*\(\s*(?:UnitName|GetUnitName|UnitFullName)\s*\(\s*" + SECRET_UNIT)
SECRET_LOCAL = re.compile(r"\blocal\s+(\w+(?:\s*,\s*\w+)*)\s*=\s*(?:UnitName|GetUnitName|UnitFullName)\s*\(\s*" + SECRET_UNIT)


def secret_name_uses(code):
    """Stellen, an denen der Name von Ziel/Boss/Fokus ungeschützt zerlegt, verglichen oder als Schlüssel benutzt wird.
    Direkt (UnitName("target"):lower()) und über eine lokale Variable in den nächsten 8 Zeilen."""
    hits = {code.count("\n", 0, m.start()) + 1 for m in SECRET_USE.finditer(code)}
    lines = code.split("\n")
    for m in SECRET_LOCAL.finditer(code):
        start = code.count("\n", 0, m.start())
        for v in re.split(r"\s*,\s*", m.group(1)):
            use = re.compile(r"\b" + v + r"\s*(?::\s*\w+\s*\(|[=~]=\s*[\"']|\])|\[\s*" + v + r"\s*\]"
                             r"|\b(?:strlower|string\.lower|strupper|string\.upper|strsub|string\.sub|string\.find|strfind"
                             r"|string\.match|strmatch|gsub|string\.gsub)\s*\(\s*" + v + r"\b")
            for k in range(start + 1, min(start + 9, len(lines))):
                if re.search(r"\blocal\s+" + v + r"\b", lines[k]):
                    break               # Variable neu belegt
                if use.search(lines[k]):
                    hits.add(k + 1)
                    break
    return sorted(hits)


# Addon-Kommunikation (shared/wissen/kommunikation-forever.md): Addon-Nachrichten über eigene Chat-Kanäle kommen in
# WoW Forever nicht an; eigene Kanäle belegen knappe Kanalplätze (max. 10). Nur WARNUNG, bis alle umgestellt haben.
ADDON_SEND = re.compile(r"\bSendAddonMessage(?:Logged)?\b")
CHANNEL_LIT = re.compile(r"[\"']CHANNEL[\"']")
CHANNEL_JOIN = re.compile(r"\b(?:JoinTemporaryChannel|JoinChannelByName|JoinPermanentChannel)\b")


def addon_channel_uses(blank):
    """Zeilen, an denen Addon-Nachrichten über "CHANNEL" laufen (nur in Dateien mit SendAddonMessage; Zeilen mit
    SendChatMessage – normaler Chat, z. B. Gildenwerbung – zählen nicht). Rückgabe: Liste Zeilennummern."""
    if not ADDON_SEND.search(blank):
        return []
    out = set()
    for m in CHANNEL_LIT.finditer(blank):
        ls = blank.rfind("\n", 0, m.start()) + 1
        le = blank.find("\n", m.end())
        line_txt = blank[ls:le if le >= 0 else len(blank)]
        if "SendChatMessage" in line_txt:
            continue
        out.add(blank.count("\n", 0, m.start()) + 1)
    return sorted(out)


def channel_joins(blank):
    return sorted({blank.count("\n", 0, m.start()) + 1 for m in CHANNEL_JOIN.finditer(blank)})


SECRET_GUARD = re.compile(r"IsSecret|issecretvalue|canaccessvalue|GoldSentinelGame\s*\.\s*Safe|InCombatLockdown")

GAME_TESTS = SHARED_DIR / "tests" / "test_goldsentinelgame.py"
# alle Tests der gemeinsamen Dateien und des Prüfsystems (shared/tests/test_*.py, addon-check/test_*.py)
ALL_TESTS = sorted((SHARED_DIR / "tests").glob("test_*.py")) + sorted(Path(__file__).resolve().parent.glob("test_*.py"))


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------
def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or "")) or (0,)


def version_key(addon, v):
    """AHSentinel (früher AH Analyzer Pro): 5.9.x wurde zu 0.59.x – alte Nummern umrechnen (wie curseforge/upload.py)."""
    t = vtuple(v)
    if addon.lower() in ("ahanalyzerpro", "ahsentinel") and t and t[0] >= 1:
        return (0, t[0] * 10 + (t[1] if len(t) > 1 else 0)) + t[2:]
    return t


def norm(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def sha(data: bytes) -> str:
    return hashlib.sha256(norm(data)).hexdigest()[:12]


def lua_version_const(text):
    m = re.search(r"^\s*local\s+VERSION\s*=\s*(\d+)", text, re.M)
    return int(m.group(1)) if m else None


def strip_lua_comments(text):
    text = re.sub(r"--\[(=*)\[.*?\]\1\]", "", text, flags=re.S)
    return re.sub(r"--[^\n]*", "", text)


_LONG_COMMENT = re.compile(r"--\[(=*)\[")
_LONG_OPEN = re.compile(r"\[(=*)\[")


def lua_blank(text):
    """Entfernt Kommentare und leert den Inhalt von Strings (Anführungszeichen bleiben, Zeilenumbrüche auch).
    So stimmen die Zeilennummern, und Text in Strings löst keine Regel aus. Strings aus nur einem Wort ("target")
    bleiben stehen, weil die Regeln sie brauchen."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "-" and text.startswith("--", i):
            m = _LONG_COMMENT.match(text, i)
            if m:
                end = text.find("]" + m.group(1) + "]", m.end())
                end = n if end < 0 else end + len(m.group(1)) + 2
            else:
                end = text.find("\n", i)
                end = n if end < 0 else end
            out.append(re.sub(r"[^\n]", " ", text[i:end]))
            i = end
        elif c in "\"'":
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            body = text[i + 1:j]
            body = body if re.fullmatch(r"\w+", body) else re.sub(r"[^\n]", " ", body)   # "target", "UnitName" bleiben
            out.append(c + body + (c if j < n and text[j] == c else ""))
            i = j + 1 if j < n and text[j] == c else j
        elif c == "[" and _LONG_OPEN.match(text, i):
            m = _LONG_OPEN.match(text, i)
            end = text.find("]" + m.group(1) + "]", m.end())
            end = n if end < 0 else end + len(m.group(1)) + 2
            out.append('""' + re.sub(r"[^\n]", " ", text[i + 2:end]))
            i = end
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _norm_target(t):
    t = re.sub(r"\s+", "", t)
    m = re.fullmatch(r"_G(?:\.(\w+)|\[[\"'](\w+)[\"']\])", t)
    if m:
        return "_G", m.group(1) or m.group(2)
    if t.startswith("C_") and re.search(r"[.:]", t):
        ns_, fn = re.split(r"[.:]", t, 1)
        return ns_, f"{ns_}.{fn}"
    return None, t


# sieht aus wie eine Blizzard-API-Funktion (für Hilfsfunktionen auf _G; eigene Globals wie AHAnalyzerPro zählen nicht)
_BLIZZ_LIKE = re.compile(r"^(?:Get|Set|Is|Has|Can|Unit|Buy|Sell|Send|Pickup|Use|Cast|Take|Accept|Complete|Repair|Guild|Invite|Create)[A-Z]")
_SETTER_DEF = re.compile(r"\bfunction\s+(?:[\w.]+[.:])?(\w+)\s*\(\s*(\w+)\s*,\s*(\w+)[^)]*\)")


def setter_helpers(code):
    """Eigene Hilfsfunktionen, die ihre ersten zwei Parameter als Tabelle und Schlüssel beschreiben (t[k] = v oder
    rawset(t, k, …)), z. B. Stub(t, k, v). Wird so eine Funktion mit _G oder einer C_-Tabelle aufgerufen, ist das eine
    Ersetzung auf Umweg. -> Menge der Funktionsnamen"""
    names = set()
    for m in _SETTER_DEF.finditer(code):
        name, t, k = m.groups()
        body = code[m.end():m.end() + 1500]
        end = re.search(r"^\s*end\b", body, re.M)    # grob: bis zum ersten "end" am Zeilenanfang
        body = body[:end.start()] if end else body
        if re.search(r"\b" + t + r"\s*\[\s*" + k + r"\s*\]\s*=(?!=)|\brawset\s*\(\s*" + t + r"\s*,\s*" + k + r"\b", body):
            names.add(name)
    return names


def blizz_overrides_indirect(code):
    """Aufrufe einer Setzer-Hilfsfunktion mit _G oder C_X -> Liste (zeile, name, sicher).
    sicher=False: Schlüssel ist eine Variable (Stub(_G, n, nil)) – welche Funktion, sieht die Prüfung nicht."""
    found = []
    helpers = setter_helpers(code)
    if not helpers:
        return found
    call = re.compile(r"(?<![\w.:])(?:[\w.]+[.:])?(" + "|".join(map(re.escape, sorted(helpers))) +
                      r")\s*\(\s*(_G|C_\w+)\s*,\s*(?:[\"'](\w+)[\"']|(\w+))")
    for m in call.finditer(code):
        if re.search(r"\bfunction\s*$", code[code.rfind("\n", 0, m.start()) + 1:m.start()]):
            continue                    # die Definition selbst
        base, lit, var = m.group(2), m.group(3), m.group(4)
        if re.search(r"\blocal\s+" + base + r"\s*=\s*(?!" + base + r"\b)", code):
            continue                    # eigene lokale Tabelle gleichen Namens
        line = code.count("\n", 0, m.start()) + 1
        if lit:
            if base == "_G" and lit not in BLIZZ_GLOBALS and not lit.startswith("C_") and not _BLIZZ_LIKE.match(lit):
                continue                # eigenes Global (z. B. ein anderes Addon) – kein Blizzard-Taint
            found.append((line, f"{lit}" if base == "_G" else f"{base}.{lit}", True))
        elif base.startswith("C_"):
            found.append((line, f"{base}.<{var}>", True))
        else:
            found.append((line, f"_G[{var}]", False))
    return found


def blizz_overrides(code):
    """Zeilen, in denen eine Blizzard-Funktion ersetzt wird -> Liste (zeile, name).
    Verfolgt die Lua-Bereiche (function/do/if/repeat … end/until, Tabellen { }): lokale Variablen, Parameter und
    for-Variablen gelten nur in ihrem Bereich; ein Feld direkt in einer Tabelle ist kein Global, Code in einer Funktion
    in einer Tabelle schon. Eigene lokale Tabellen namens _G oder C_… (local C_Helper = {}) zählen nicht."""
    events = [(m.start(), 0, m) for m in _SCOPE_TOKENS.finditer(code)]
    events += [(m.start(m.lastgroup), 1, m) for m in BLIZZ_ASSIGN.finditer(code)]
    events.sort(key=lambda e: (e[0], e[1]))
    stack = [("block", {})]             # (art, {name: eigene_tabelle?}); art: block | func | table
    pending = None                      # Namen (Parameter/for), die mit dem nächsten Block-Öffner gelten
    found = []

    def local_info(name):
        for kind, names in reversed(stack):
            if name in names:
                return names[name]
        return None

    for pos, typ, m in events:
        if typ == 0:
            g = m.lastgroup if m.lastgroup in ("open", "close", "lb", "rb") else None
            if m.group("lf"):
                stack[-1][1][m.group("lf")] = True   # das folgende "function" öffnet den Bereich
            elif m.group("lv"):
                rhs = (m.group("lrhs") or "").lstrip(" \t=").strip()
                for v in re.split(r"\s*,\s*", m.group("lv")):
                    if v not in _LUA_KEYWORDS:
                        # local _G = _G / local C_Timer = C_Timer -> echte Tabelle; local C_X = {} -> eigene
                        stack[-1][1][v] = not re.match(re.escape(v) + r"\b", rhs)
            elif m.group("params") is not None:
                params = [x for x in re.split(r"[\s,]+", m.group("params")) if re.fullmatch(r"\w+", x)]
                stack.append(("func", {x: True for x in params}))
            elif m.group("fv"):
                pending = ("for", {x for x in re.split(r"\s*,\s*", m.group("fv"))})
            elif g == "open":
                names = {}
                if pending and pending[0] == "for" and m.group("open") == "do":
                    names = {x: True for x in pending[1]}
                    pending = None
                stack.append(("block", names))
            elif g == "close":
                while len(stack) > 1 and stack[-1][0] == "table":
                    stack.pop()         # unvollständige Tabelle: nicht hängen bleiben
                if len(stack) > 1:
                    stack.pop()
            elif g == "lb":
                stack.append(("table", {}))
            elif g == "rb":
                while len(stack) > 1 and stack[-1][0] != "table":
                    stack.pop()
                if len(stack) > 1:
                    stack.pop()
            continue
        # Treffer einer Zuweisung
        if stack[-1][0] == "table" and m.group("a"):
            continue                    # Feld in einer Tabelle ({ UnitName = … }), kein Global
        raw = m.group("a") or m.group("f") or m.group("r")
        targets = re.split(r"\s*,\s*", raw) if m.group("a") else [raw]
        if m.group("r"):
            targets = [f'_G["{raw}"]']
        line = code.count("\n", 0, m.start(m.lastgroup)) + 1
        for t in targets:
            base, name = _norm_target(t)
            if base is not None:        # _G.X oder C_X.Y
                if local_info(base):    # eigene lokale Tabelle gleichen Namens
                    continue
                if base == "C_" or base.startswith("C_"):
                    found.append((line, name))
                    continue
            if name in _LUA_KEYWORDS or name not in BLIZZ_GLOBALS:
                continue
            if base is None and local_info(name) is not None:
                continue                # lokale Variable, Parameter oder for-Variable in diesem Bereich
            found.append((line, name))
    return found


def zip_name_version(path: Path):
    """download/<Addon>-<Version>.zip oder announce/<kanal>__<reihe>-<Version>.<Addon>.zip -> (Addon, Version)"""
    m = re.match(r"^[^_]+__.+?-(\d+(?:\.\d+)+)\.([A-Za-z0-9_]+)$", path.stem)
    if m:
        return m.group(2), m.group(1)
    m = re.match(r"^(.+?)-(\d+(?:\.\d+)*)$", path.stem)
    return (m.group(1), m.group(2)) if m else (path.stem, None)


_LUA = None
SYNTAX_TOOL = None      # womit die Syntax geprüft wird: "lupa (Lua 5.1)", "luac5.1" … oder None = gar nicht


# Probetest für luac: korrekter Code muss durchgehen, kaputter Code und Code, den es erst ab Lua 5.2 gibt
# (goto/Labels), müssen abgelehnt werden. So fällt ein Ersatz auf, der alles durchwinkt, nicht läuft oder
# eine andere Lua-Version ist – die Selbstauskunft "-v" allein reicht nicht.
_PROBE = {
    "gut": ("local a = { 1, 2 }\nfor i, v in ipairs(a) do a[i] = v * 2 end\nreturn a\n", True),
    "kaputt": ("local x = \nfunction\n", False),
    "lua52": ("goto ende\n::ende::\n", False),
}


def _luac_passes_probe(path):
    import os
    import tempfile
    d = tempfile.mkdtemp(prefix="luacprobe")
    try:
        for name, (code, should_pass) in _PROBE.items():
            f = os.path.join(d, name + ".lua")
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(code)
            try:
                r = subprocess.run([path, "-p", f], capture_output=True, text=True, timeout=20)
            except Exception:
                return False
            if (r.returncode == 0) != should_pass:
                return False
        return True
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


LUAC_REJECTED = []      # gefundene luac, die den Probetest nicht bestanden haben (für den Bericht)


def _find_luac():
    import shutil
    for name in ("luac5.1", "luac51", "luac"):
        path = shutil.which(name)
        if not path:
            continue
        try:
            out = subprocess.run([path, "-v"], capture_output=True, text=True, timeout=10)
            claims_51 = "5.1" in (out.stdout + out.stderr)
        except Exception:
            claims_51 = False
        if claims_51 and _luac_passes_probe(path):
            return path
        LUAC_REJECTED.append(path)
    return None


def syntax_tool():
    """Lua 5.1 wie im Spiel: zuerst lupa, sonst luac 5.1. Ergebnis merkt sich SYNTAX_TOOL."""
    global _LUA, SYNTAX_TOOL
    if _LUA is None:
        try:
            if os.environ.get("ADDON_CHECK_NO_LUPA"):      # nur für Tests: lupa ignorieren, luac-Weg prüfen
                raise ImportError("lupa abgeschaltet")
            import lupa.lua51 as lupa51
            rt = lupa51.LuaRuntime(unpack_returned_tuples=True)
            fn = rt.eval("function(s, n) local f, e = loadstring(s, n) return e end")
            _LUA, SYNTAX_TOOL = ("lupa", fn), "lupa (Lua 5.1)"
        except Exception:
            luac = _find_luac()
            _LUA, SYNTAX_TOOL = (("luac", luac), Path(luac).name + " (Lua 5.1)") if luac else (False, None)
    return _LUA


def lua_syntax_error(src: str, name: str):
    """Fehlertext oder None. Ist weder lupa noch luac 5.1 da, wird NICHT geprüft – das meldet check_zip
    ausdrücklich ("Lua-Syntax NICHT geprüft"), damit ein OK nie fälschlich eine geprüfte Syntax bedeutet."""
    tool = syntax_tool()
    if not tool:
        return None
    kind, impl = tool
    if kind == "lupa":
        err = impl(src, "@" + name)
        return str(err) if err else None
    import tempfile, os
    fd, tmp = tempfile.mkstemp(suffix=".lua")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(src)
        r = subprocess.run([impl, "-p", tmp], capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return None
        return (r.stderr or r.stdout).strip().replace(tmp, name)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# bekannte veröffentlichte Versionen (Discord-ZIPs in der Git-Geschichte, CurseForge)
# ---------------------------------------------------------------------------
_PUBLISHED = None


def published_versions():
    global _PUBLISHED
    if _PUBLISHED is not None:
        return _PUBLISHED
    pub = {}

    def add(addon, ver, where):
        if ver:
            pub.setdefault(addon.lower(), {}).setdefault(ver, set()).add(where)

    try:
        out = subprocess.run(["git", "-C", str(ROOT), "log", "--all", "--name-only", "--format="],
                             capture_output=True, text=True, timeout=120).stdout
    except Exception:
        out = ""
    for line in out.splitlines():
        base = line.strip().rsplit("/", 1)[-1]
        if not base.endswith(".zip"):
            continue
        if line.startswith("download/"):
            addon, ver = zip_name_version(Path(base))
            add(addon, ver, "download/ (Git-Geschichte)")
        elif line.startswith("announce/") and "__" in base:
            # announce/<kanal>__<reihe>-<version>.<Addon>.zip
            m = re.match(r"^[^_]+__.+?-(\d+(?:\.\d+)+)\.([A-Za-z0-9_]+)\.zip$", base)
            if m:
                add(m.group(2), m.group(1), "Discord (announce/)")
    # ohne Git (z. B. im Discord-Bot): Dateinamen in download/, announce/ und EXTRA_DIRS
    for d in [DOWNLOAD, ANNOUNCE] + [Path(x) for x in EXTRA_DIRS]:
        try:
            files = list(Path(d).glob("*.zip"))
        except OSError:
            files = []
        for f in files:
            if f.stem.endswith("-latest"):
                continue
            addon, ver = zip_name_version(f)
            if "__" in f.stem:
                add(addon, ver, "Discord (announce/)")
            else:
                add(addon, ver, f"{Path(d).name}/")
    try:
        for addon, vers in json.loads(UPLOADED.read_text(encoding="utf-8")).items():
            for v in vers:
                add(addon, v, "CurseForge")
    except (OSError, ValueError):
        pass
    _PUBLISHED = pub
    return pub


# ---------------------------------------------------------------------------
# gleiche Version schon einmal mit anderem Inhalt veröffentlicht?
# Verglichen werden die Dateien IN der ZIP (nicht die ZIP selbst): neu packen mit gleichem Inhalt ist kein Fehler.
# ---------------------------------------------------------------------------
def zip_fingerprint(data):
    import io
    try:
        z = zipfile.ZipFile(io.BytesIO(data) if isinstance(data, bytes) else data)
        return {n: sha(z.read(n)) for n in z.namelist() if not n.endswith("/")}
    except Exception:
        return None


def earlier_copies(path: Path):
    """Früher veröffentlichte Fassungen derselben ZIP (gleicher Dateiname): Git-Geschichte von download/ und
    announce/ sowie EXTRA_DIRS (z. B. die schon geposteten ZIPs des Discord-Bots). -> [(wo, fingerprint)]"""
    out = []
    for rel in (f"download/{path.name}", f"announce/{path.name}"):
        try:
            commits = subprocess.run(["git", "-C", str(ROOT), "log", "--all", "--format=%H", "--", rel],
                                     capture_output=True, text=True, timeout=60).stdout.split()
        except Exception:
            commits = []
        seen = set()
        for c in commits:
            try:
                blob = subprocess.run(["git", "-C", str(ROOT), "rev-parse", f"{c}:{rel}"],
                                      capture_output=True, text=True, timeout=30).stdout.strip()
            except Exception:
                blob = ""
            if not blob or blob in seen:
                continue
            seen.add(blob)
            data = subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", blob],
                                  capture_output=True, timeout=60).stdout
            fp = zip_fingerprint(data)
            if fp is not None:
                out.append((f"{rel} in Commit {c[:7]}", fp))
    for d in EXTRA_DIRS:
        f = Path(d) / path.name
        try:
            if f.exists() and f.resolve() != path.resolve():
                fp = zip_fingerprint(f.read_bytes())
                if fp is not None:
                    out.append((f"{Path(d).name}/{path.name}", fp))
        except OSError:
            pass
    return out


def same_version_changed(path: Path):
    """Text des Befunds, wenn dieselbe ZIP (Name = Version) früher mit anderem Inhalt veröffentlicht wurde."""
    cur = zip_fingerprint(path.read_bytes())
    if cur is None:
        return None
    for where, fp in earlier_copies(path):
        if fp != cur:
            changed = sorted(n for n in set(fp) | set(cur) if fp.get(n) != cur.get(n))
            sample = ", ".join(n.rsplit("/", 1)[-1] for n in changed[:4]) + (" …" if len(changed) > 4 else "")
            return (f"diese Version wurde schon mit ANDEREM Inhalt veröffentlicht ({where}; geändert: {sample}). "
                    f"Wer sie schon hat, bekommt das Update nie – geänderten Inhalt immer als neue, höhere Version "
                    f"veröffentlichen.")
    return None


# ---------------------------------------------------------------------------
# Prüfung einer ZIP
# ---------------------------------------------------------------------------
# Offizielle ältere Fassungen der "exact"-Dateien (shared/tests/variants/<Name ohne .lua>-v<N>.lua):
# eine Kopie davon ist kein Nachbau, sondern nur veraltet -> Warnung statt Fehler
def official_old(name):
    out = {}
    stem = name[:-4]
    for p in (SHARED_DIR / "tests" / "variants").glob(f"{stem}-v*.lua"):
        m = re.search(r"-v(\d+)\.lua$", p.name)
        if m:
            out[sha(p.read_bytes())] = int(m.group(1))
    # zusätzlich nur als Prüfsumme festgehaltene Fassungen (Datei geändert, z. B. Namen entfernt)
    hp = SHARED_DIR / "tests" / "variants" / "hashes.txt"
    if hp.exists():
        for line in hp.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 3 and not line.startswith("#") and parts[0] == stem and parts[1].isdigit():
                out.setdefault(parts[2], int(parts[1]))
    return out


def load_shared():
    ref = {}
    for name in SHARED:
        p = SHARED_DIR / name
        if p.exists():
            data = p.read_bytes()
            ref[name] = {"sha": sha(data), "version": lua_version_const(data.decode("utf-8", "replace")),
                         "old": official_old(name)}
    return ref


def parse_toc(text):
    meta, files = {}, []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^##\s*([^:]+):\s*(.*)$", line)
        if m:
            meta[m.group(1).strip()] = m.group(2).strip()
        elif not line.startswith("#"):
            files.append(line.replace("\\", "/"))
    return meta, files


_LADETEST = None


def _ladetest():
    """ladetest.py aus demselben Ordner laden – auch wenn addon_check als Modul von woanders geladen wird (Bot, CurseForge)."""
    global _LADETEST
    if _LADETEST is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("gs_ladetest", Path(__file__).resolve().with_name("ladetest.py"))
        _LADETEST = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_LADETEST)
    return _LADETEST


def check_zip(path, shared_ref=None, dev_max=None):
    """Prüft eine Addon-ZIP. Rückgabe: Liste (level, text) mit level 'FEHLER' | 'WARNUNG' | 'OK'."""
    path = Path(path)
    shared_ref = shared_ref if shared_ref is not None else load_shared()
    res = []
    err = lambda t: res.append(("FEHLER", t))
    warn = lambda t: res.append(("WARNUNG", t))

    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return [("FEHLER", "keine gültige ZIP-Datei")]
    names = [n for n in z.namelist() if not n.endswith("/")]
    lower = {n.lower(): n for n in names}
    tocs = [n for n in names if n.lower().endswith(".toc")]
    if not tocs:
        return [("FEHLER", "keine .toc in der ZIP")]

    zaddon, zver = zip_name_version(path)
    from_announce = "__" in path.stem
    folders = sorted({n.split("/", 1)[0] for n in tocs if "/" in n})
    main_versions = set()
    folder_versions = {}                # Ordner -> Versionen aus seinen .toc
    loaded = set()                      # Dateien, die das Spiel lädt (in einer .toc oder über eine geladene .xml)

    for folder in folders:
        ftocs = [n for n in tocs if n.startswith(folder + "/") and n.count("/") == 1]
        listed, versions, interfaces = set(), {}, set()
        for t in ftocs:
            meta, files = parse_toc(z.read(t).decode("utf-8", "replace"))
            versions[t] = meta.get("Version", "")
            interfaces.update(int(x) for x in re.findall(r"\d+", meta.get("Interface", "")))
            for f in files:
                full = f"{folder}/{f}"
                listed.add(full.lower())
                loaded.add(full.lower())
                if full.lower() not in lower:
                    err(f"{t}: Datei {f} steht in der .toc, fehlt aber in der ZIP (Lua-Fehler beim Laden)")
            # Reihenfolge: GoldSentinelGame.lua vor allen eigenen Dateien
            own = [f for f in files if f.rsplit("/", 1)[-1] not in SHARED]
            if "GoldSentinelGame.lua" in files and own:
                if files.index("GoldSentinelGame.lua") > files.index(own[0]):
                    err(f"{t}: GoldSentinelGame.lua muss vor den eigenen Dateien stehen (vor {own[0]})")
            if "GoldSentinelTest.lua" in files and own and files.index("GoldSentinelTest.lua") > files.index(own[0]):
                err(f"{t}: GoldSentinelTest.lua muss vor den eigenen Dateien stehen (vor {own[0]})")
        vs = {v for v in versions.values() if v}
        if len(vs) > 1:
            err(f"{folder}: .toc-Dateien mit unterschiedlicher Version: " +
                ", ".join(f"{k.split('/')[-1]}={v}" for k, v in sorted(versions.items())))
        if folder.lower() == zaddon.lower():
            main_versions |= vs
        folder_versions[folder.lower()] = vs
        if 16001 not in interfaces and not any(16000 <= i <= 19999 for i in interfaces):
            warn(f"{folder}: keine Interface-Nummer für WoW Forever (16001) in der .toc")
    # .xml-Dateien, die geladen werden, laden ihrerseits <Script file="…"/> und <Include file="…"/>
    todo = [n for n in names if n.lower() in loaded and n.lower().endswith(".xml")]
    while todo:
        x = todo.pop()
        base_dir = x.rsplit("/", 1)[0]
        for f in re.findall(r'file\s*=\s*"([^"]+)"', z.read(x).decode("utf-8", "replace")):
            full = f"{base_dir}/{f.replace(chr(92), '/')}".lower()
            if full not in loaded:
                loaded.add(full)
                if full.endswith(".xml") and full in lower:
                    todo.append(lower[full])
    for n in names:
        if n.lower().endswith(".lua") and "/" in n and n.lower() not in loaded:
            warn(f"{n}: liegt im Addon, wird aber nicht geladen (in keiner .toc/.xml) – gehört nicht in die ZIP?")
    # Liegengebliebene Sicherungs- und Patch-Dateien (ab 9. November, AHSentinel 0.65.22: TestRoutine.lua.orig)
    for n in names:
        if re.search(r"(\.(orig|rej|bak|tmp|swp)|~)$", n.lower()):
            warn(f"{n}: Sicherungs-/Patch-Rest (.orig/.rej/.bak/~) – gehört nicht in die ZIP")

    # Version: ZIP-Name, .toc, schon veröffentlicht
    if zver and main_versions and zver not in main_versions and not from_announce:
        err(f"ZIP-Name sagt {zver}, die .toc sagt {', '.join(sorted(main_versions))}")
    if from_announce:
        ver = zver if zver in main_versions else None     # Discord-Anhang eines anderen Addons: nicht vergleichen
    else:
        ver = zver or (sorted(main_versions)[0] if main_versions else None)
    if ver:
        known = published_versions().get(zaddon.lower(), {})
        higher = sorted((v for v in known if version_key(zaddon, v) > version_key(zaddon, ver)),
                        key=lambda v: version_key(zaddon, v))
        if higher:
            top = higher[-1]
            err(f"Version {ver} ist NIEDRIGER als schon veröffentlichte {top} ({', '.join(sorted(known[top]))}). "
                f"Neue Version muss höher sein als {top}, sonst bekommen Spieler das Update nicht.")

    # gleiche Version, anderer Inhalt?
    if ver or zver:
        msg = same_version_changed(path)
        if msg:
            err(msg)

    # gemeinsame Dateien
    has_game = has_test = False
    for n in names:
        base = n.rsplit("/", 1)[-1]
        data = z.read(n)
        if base in SHARED:
            rule = SHARED[base]
            ref = shared_ref.get(base)
            v = lua_version_const(data.decode("utf-8", "replace"))
            if base == "GoldSentinelGame.lua":
                has_game = True
            if base == "GoldSentinelTest.lua":
                has_test = True
            if rule == "exact":
                if not ref:
                    warn(f"{n}: Vorlage shared/{base} fehlt im Repo – Vergleich übersprungen")
                elif sha(data) in ref.get("old", {}):
                    warn(f"{n}: veraltete offizielle Fassung (Version {ref['old'][sha(data)]}) – "
                         f"auf shared/{base} Version {ref['version']} aktualisieren")
                elif sha(data) != ref["sha"]:
                    err(f"{n}: weicht von shared/{base} ab (Version {v}, Vorlage Version {ref['version']}). "
                        f"Gemeinsame Datei nie selbst ändern – die Vorlage unverändert kopieren.")
            elif rule == "version" and dev_max and base in dev_max:
                top_v, top_sha = dev_max[base]
                if v is not None and v == top_v and sha(data) != top_sha:
                    err(f"{n}: gleiche Version {v} wie eine andere Kopie, aber anderer Inhalt")
                elif v is not None and v < top_v:
                    warn(f"{n}: veraltet (Version {v}, eine andere Kopie hat {top_v})")
        elif n.lower().endswith(".lua"):
            text = data.decode("utf-8", "replace")
            if REIMPL.search(text):
                err(f"{n}: baut GoldSentinelGame selbst nach – stattdessen shared/GoldSentinelGame.lua kopieren")
            e = lua_syntax_error(text, n)
            if e:
                if n.lower() in loaded:
                    err(f"Lua-Syntaxfehler: {e}")
                else:
                    warn(f"Lua-Syntaxfehler in einer Datei, die das Spiel nicht lädt (Werkzeug?): {e} – "
                         f"am besten nicht in die ZIP packen")
            blank = lua_blank(text)
            base_addon = re.sub(r"-latest$", "", zaddon.lower())
            old_release = (base_addon, ver or zver or "") in ALTLAST or any(
                (base_addon, v) in ALTLAST for v in folder_versions.get(base_addon, ()))
            say = err if n.lower() in loaded and not old_release else warn
            for line, name in blizz_overrides(blank):
                say(f"{n}:{line}: ersetzt die Blizzard-Funktion {name} – das taintet sie bis zum /reload "
                    f"(auch im Test und auch wenn sie danach zurückgesetzt wird). Eigene Funktion oder Ersatzwert verwenden."
                    + (" Schon veröffentlicht: in der nächsten Version beheben, sonst FEHLER." if old_release else ""))
            for line, name, sure in blizz_overrides_indirect(blank):
                (say if sure else warn)(
                    f"{n}:{line}: ersetzt über eine Hilfsfunktion {'die Blizzard-Funktion ' + name if sure else name + ' (Name als Variable)'}"
                    f" – das taintet sie bis zum /reload, auch mit Zurücksetzen. Nur eigene Tabellen ersetzen (z. B. ns.API)."
                    + (" Schon veröffentlicht: in der nächsten Version beheben, sonst FEHLER." if old_release and sure else ""))
            if TEST_FILE.search(n):
                for m in TEST_ACTIONS.finditer(blank):
                    if re.search(r"\bfunction\s*$", blank[blank.rfind("\n", 0, m.start()) + 1:m.start()]):
                        continue        # Definition einer Ersatz-Funktion (local function SendChatMessage …), kein Aufruf
                    fname = re.match(r"[\w.]+", re.sub(r"\s+", "", m.group(0))).group(0)
                    if re.search(r"\bfunction\s+" + re.escape(fname) + r"\s*\(|\blocal\s+" + re.escape(fname) + r"\s*=", blank):
                        continue        # die Datei definiert die Funktion selbst (Ersatz) – Aufruf ist harmlos
                    line = blank.count("\n", 0, m.start()) + 1
                    warn(f"{n}:{line}: Testdatei ruft {re.sub(chr(92) + 's+', '', m.group(0)).rstrip('(')} direkt auf – "
                         f"Aktionen mit Folgen im Test nur mitschreiben, nie auslösen (nachtrag-testroutinen.txt)")
            for line in addon_channel_uses(blank)[:3]:
                warn(f"{n}:{line}: Addon-Nachricht über einen eigenen Kanal (\"CHANNEL\") – kommt in WoW Forever nicht an "
                     f"(Server: NOT_ALLOWED_IN_CHANNEL). Über GUILD/PARTY/RAID/WHISPER senden "
                     f"(shared/wissen/kommunikation-forever.md, hinweis-sync-kanal.txt).")
            for line in channel_joins(blank)[:2]:
                warn(f"{n}:{line}: tritt einem eigenen Chat-Kanal bei – belegt einen der 10 Kanalplätze des Spielers. "
                     f"Künftig nur der gemeinsame GoldSentinel-Kanal (shared/GoldSentinelSync.lua), nur zum Finden von Mitspielern.")
            if not SECRET_GUARD.search(blank):
                for line in secret_name_uses(blank):
                    warn(f"{n}:{line}: Name von Ziel/Boss/Fokus wird ohne Schutzprüfung weiterverarbeitet – in Forever ist er im "
                         f"Kampf geheim (Lua-Fehler bei :lower(), Vergleich oder als Schlüssel). Vorher GoldSentinelGame.IsSecret prüfen.")
            code = strip_lua_comments(text)
            for pat, fallback, why in TRAPS:
                # Fallen für alte Blizzard-Funktionen (Muster beginnt mit \b): ein Feld einer eigenen Tabelle
                # (ns.API.GetMerchantNumItems, A:GetSpellInfo) ist kein Aufruf der alten Funktion -> nicht zählen
                hits = [m for m in re.finditer(pat, code)
                        if not (pat.startswith(r"\b") and re.search(r"[.:]\s*$", code[max(0, m.start() - 40):m.start()]))]
                if hits and not re.search(fallback, code):
                    line = code.count("\n", 0, hits[0].start()) + 1
                    warn(f"{n}:{line}: {why}")
    # Ladetest: das Addon im nachgebauten Spiel wirklich laden (Forever und Classic Era) – nur ohne Syntaxfehler sinnvoll
    if not any(l == "FEHLER" and t.startswith("Lua-Syntaxfehler") for l, t in res) and not os.environ.get("ADDON_CHECK_NO_LOADTEST"):
        try:
            for level, text in _ladetest().load_test(path):
                if level == "FEHLER":
                    err(text)
                elif level == "WARNUNG":
                    warn(text)
        except Exception as e:        # der Ladetest darf die Prüfung nie selbst zum Absturz bringen
            warn(f"Ladetest konnte nicht laufen: {e}")
    if not syntax_tool():
        # streng (GitHub-Lauf, CurseForge-Upload): ohne Syntaxprüfung kein OK
        (err if os.environ.get("ADDON_CHECK_STRICT") else warn)("Lua-Syntax NICHT geprüft: weder lupa noch luac 5.1 vorhanden (pip install lupa). "
             "Die Prüfung beim CurseForge-Upload bzw. im GitHub-Lauf prüft sie vollständig.")
    if not has_game and any(f.lower() != "raidmasteruploader" for f in folders):
        warn("GoldSentinelGame.lua fehlt (gemeinsame Versionserkennung noch nicht eingebaut)")
    if not has_test and any(f.lower() != "raidmasteruploader" for f in folders) and not all(
            f.lower().endswith("_data") for f in folders):
        warn("GoldSentinelTest.lua fehlt (Testberichte und Fehlermeldungen an die Prüfung noch nicht eingebaut)")
    if not any(l == "FEHLER" for l, _ in res):
        res.insert(0, ("OK", "keine Fehler"))
    return res


def dev_versions(zips):
    """Höchste Version je 'version'-Datei über alle ZIPs: {name: (version, sha)}."""
    best = {}
    for p in zips:
        try:
            z = zipfile.ZipFile(p)
        except zipfile.BadZipFile:
            continue
        for n in z.namelist():
            base = n.rsplit("/", 1)[-1]
            if SHARED.get(base) == "version":
                data = z.read(n)
                v = lua_version_const(data.decode("utf-8", "replace"))
                if v is not None and (base not in best or v > best[base][0]):
                    best[base] = (v, sha(data))
    return best


def default_zips():
    """Alle ZIPs in download/ plus die neueste Discord-ZIP je Addon, das nicht in download/ liegt (z. B. LevelPilot).
    Einzel-ZIPs, deren Addon inzwischen in einer neueren ZIP derselben Reihe steckt, zählen nicht mehr."""
    out, have = [], set()
    for p in sorted(DOWNLOAD.glob("*.zip")):
        if p.stem.endswith("-latest") or p.stem.lower().startswith("raidmasteruploader"):
            continue
        out.append(p)
        have.add(zip_name_version(p)[0].lower())
    newest = {}
    for p in ANNOUNCE.glob("*__*.zip"):
        addon, ver = zip_name_version(p)
        if not ver or addon.lower() in have:
            continue
        if addon not in newest or version_key(addon, ver) > version_key(addon, newest[addon][0]):
            newest[addon] = (ver, p)
    # Abgelöste Einzel-ZIPs weglassen: Steckt das Addon in einer neueren ZIP derselben Reihe (z. B. das frühere
    # Datenpaket LevelPilot_Data seit 3.8 in der LevelPilot-ZIP), ist die alte Einzel-ZIP nur noch Archiv.
    series = {}
    for p in ANNOUNCE.glob("*__*.zip"):
        m = re.match(r"^([^_]+__.+?)-(\d+(?:\.\d+)+)\.", p.name)
        if m:
            series.setdefault(m.group(1), []).append((tuple(int(x) for x in m.group(2).split(".")), p))
    for addon, (ver, p) in list(newest.items()):
        m = re.match(r"^([^_]+__.+?)-(\d+(?:\.\d+)+)\.", p.name)
        if not m:
            continue
        mine = tuple(int(x) for x in m.group(2).split("."))
        for sv, q in series.get(m.group(1), []):
            if sv > mine and q != p and addon.lower() in zip_top_folders(q):
                del newest[addon]
                break
    out += [p for _, p in sorted(newest.values(), key=lambda x: x[1].name)]
    return out


def zip_top_folders(path: Path):
    """Namen der obersten Ordner einer ZIP (klein geschrieben)."""
    try:
        with zipfile.ZipFile(path) as z:
            return {n.split("/", 1)[0].lower() for n in z.namelist() if "/" in n}
    except (zipfile.BadZipFile, OSError):
        return set()


def run_game_tests():
    if not ALL_TESTS:
        return None
    try:
        import lupa.lua51  # noqa: F401  (die Tests brauchen Lua 5.1 über lupa)
    except Exception:
        return "skip", ["nicht ausgeführt – lupa fehlt (pip install lupa); im GitHub-Lauf werden sie ausgeführt"]
    code, tails = 0, []
    for t in ALL_TESTS:
        r = subprocess.run([sys.executable, "-I", str(t)], capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip().splitlines()
        tails.append(out[-1] if out else f"{t.name}: keine Ausgabe")
        code = code or r.returncode
    return code, ["; ".join(tails)]


def main(argv):
    report = None
    if "--report" in argv:
        i = argv.index("--report")
        report = Path(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    zips = [Path(a) for a in argv if not a.startswith("--")] or default_zips()
    shared_ref = load_shared()
    dev_max = dev_versions(default_zips() + zips)
    lines, failed = ["# Addon-Prüfung", ""], False

    if "GoldSentinelGame.lua" in shared_ref:
        lines.append(f"Vorlage shared/GoldSentinelGame.lua: Version {shared_ref['GoldSentinelGame.lua']['version']}")
    if "GoldSentinelTest.lua" in shared_ref:
        lines.append(f"Vorlage shared/GoldSentinelTest.lua: Version {shared_ref['GoldSentinelTest.lua']['version']}")
    t = run_game_tests()
    if t is not None:
        code, tail = t
        if code == "skip":
            lines.append("Tests der gemeinsamen Datei: " + " ".join(tail))
        else:
            lines.append(f"Tests der gemeinsamen Datei: {'bestanden' if code == 0 else 'FEHLGESCHLAGEN'} {' '.join(tail)}")
            failed |= code != 0
    syntax_tool()
    lines.append(f"Lua-Syntaxprüfung mit: {SYNTAX_TOOL or 'NICHTS – Syntax wird NICHT geprüft (pip install lupa)'}")
    for p in LUAC_REJECTED:
        lines.append(f"Hinweis: {p} meldet sich als luac, hat den Probetest aber nicht bestanden und wird nicht benutzt")
    lines.append("")

    for p in zips:
        res = check_zip(p, shared_ref, dev_max)
        bad = any(l == "FEHLER" for l, _ in res)
        failed |= bad
        n_warn = sum(1 for l, _ in res if l == "WARNUNG")
        lines.append(f"## {p.name}: {'FEHLER' if bad else 'OK'}" + (f" ({n_warn} Warnungen)" if n_warn else ""))
        for level, text in res:
            if level != "OK":
                lines.append(f"- **{level}** {text}")
        lines.append("")
    text = "\n".join(lines)
    print(text)
    if report:
        report.write_text(text + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
