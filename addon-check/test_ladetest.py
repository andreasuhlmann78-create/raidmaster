#!/usr/bin/env python3
"""Tests für den Ladetest (addon-check/ladetest.py). Aufruf: python3 addon-check/test_ladetest.py
Läuft auch über addon_check.py mit (ALL_TESTS). Je Fall eine kleine Addon-ZIP: was im Spiel lädt, darf keinen FEHLER
geben; was im Spiel beim Laden abbricht, muss ein FEHLER sein."""
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ladetest  # noqa: E402

ok = fail = 0


def check(name, cond, info=""):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
        print("FEHLT:", name, info)


TMP = Path(tempfile.mkdtemp())


def make(name, files, toc_extra="", interface="11508, 16001", tocname=None):
    p = TMP / f"{name}-{len(list(TMP.iterdir()))}.zip"
    lua_files = [f for f in files if f.endswith((".lua", ".xml"))]
    toc = f"## Interface: {interface}\n## Version: 1.0.0\n{toc_extra}" + "\n".join(lua_files) + "\n"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr(f"{name}/{tocname or name}.toc", toc)
        for f, body in files.items():
            z.writestr(f"{name}/{f}", body)
    return p


def levels(res):
    return [l for l, _ in res]


GOOD = {
    "Core.lua": "local ADDON, ns = ...\nfunction ns:On(e, f) ns.f = ns.f or CreateFrame('Frame'); ns.f:RegisterEvent(e) end\n"
                "ns:On('PLAYER_LOGIN', function() end)\nSLASH_PROBE1 = '/probe'\nSlashCmdList.PROBE = function() end\n",
    "Mod.lua": "local _, ns = ...\nns:On('ADDON_LOADED', function() end)\n",
}

# --- sauberes Addon -----------------------------------------------------------------------------------------------
r = ladetest.load_test(make("Probe", GOOD))
check("sauberes Addon ohne Meldung", r == [], r)

# --- der ThreatSentinel-Fehler: Methode benutzt, bevor sie definiert ist --------------------------------------------
bad = {"Core.lua": "local _, ns = ...\nns:On('PLAYER_LOGIN', function() end)\nfunction ns:On(e, f) end\n",
       "Mod.lua": "local _, ns = ...\nns:On('X', function() end)\n"}
r = ladetest.load_test(make("Probe", bad))
check("Methode vor Definition -> FEHLER je Client", levels(r).count("FEHLER") == 2, r)
check("FEHLER nennt Datei und Zeile", all("Core.lua:2" in t for l, t in r if l == "FEHLER"), r)
check("Folgefehler zusammengefasst", any("1 weitere Dateien" in t and "Mod.lua" in t for _, t in r), r)

# --- falsche Reihenfolge in der .toc ------------------------------------------------------------------------------
r = ladetest.load_test(make("Probe", {"Mod.lua": GOOD["Mod.lua"], "Core.lua": GOOD["Core.lua"]}))
check("Datei vor der Grundlage -> FEHLER", "FEHLER" in levels(r), r)

# --- eigene Tabelle/Local nil ------------------------------------------------------------------------------------
r = ladetest.load_test(make("Probe", {"Core.lua": "local _, ns = ...\nlocal L = ns.L\nprint(L.TITLE)\n"}))
check("eigene Tabelle fehlt -> FEHLER", "FEHLER" in levels(r), r)

# --- SavedVariables sind beim Laden noch nil (wie im Spiel) --------------------------------------------------------
r = ladetest.load_test(make("Probe", {"Core.lua": "ProbeDB.x = 1\n"}, "## SavedVariables: ProbeDB\n"))
check("SavedVariables beim Laden benutzt -> FEHLER", "FEHLER" in levels(r), r)
r = ladetest.load_test(make("Probe", {"Core.lua": "ProbeDB = ProbeDB or {}\nProbeDB.x = 1\n"}, "## SavedVariables: ProbeDB\n"))
check("SavedVariables mit 'or {}' -> keine Meldung", r == [], r)

# --- unbekannte Blizzard-API: keine Fehlalarme --------------------------------------------------------------------
api = {"Core.lua": "local _, ns = ...\n"
       "local t = C_Something.GetInfo(1)\nlocal n = (C_Container.GetContainerNumSlots(0) or 0) + 1\n"
       "for i = 1, C_Container.GetContainerNumSlots(0) do end\n"
       "local x = math.max(SomeBlizzardFrame:GetHeight(), 10)\nif IsSomething() then error('nein') end\n"
       "hooksecurefunc('UnitName', function() end)\nhooksecurefunc(GameTooltip, 'SetUnit', function() end)\n"
       "local s = 'a' .. UnknownGlobalString\nEnum.Foo.Bar = nil\nlocal f = CreateFrame('Frame', nil, UIParent, 'BackdropTemplate')\n"
       "f:SetPoint('CENTER'); f:SetSize(10, 10); f:CreateFontString(nil, 'ARTWORK', 'GameFontNormal'):SetText('x')\n"}
r = ladetest.load_test(make("Probe", api))
check("unbekannte Blizzard-API -> kein FEHLER", "FEHLER" not in levels(r), r)
check("unbekannte Blizzard-API -> keine Warnung", r == [], r)

# --- gemeinsame GoldSentinel-Dateien sind beim ersten Laden leer -------------------------------------------------
r = ladetest.load_test(make("Probe", {"Dev.lua": "local e = _G.GoldSentinelDev\nif type(e) == 'table' and (e.version or 0) >= 1 then return end\nGoldSentinelDev = { version = 1 }\n"}))
check("GoldSentinel-Global zuerst nil", r == [], r)

# --- in XML angelegte Frames gibt es schon -----------------------------------------------------------------------
xml = '<Ui><Frame name="ProbeMainFrame"/><Script file="Core.lua"/></Ui>'
r = ladetest.load_test(make("Probe", {"UI.xml": xml, "Core.lua": "ProbeMainFrame:SetScript('OnShow', function() end)\n"}))
check("Frame aus XML -> kein FEHLER", "FEHLER" not in levels(r), r)
xml2 = '<Ui><Script file="Core.lua"/></Ui>'
r = ladetest.load_test(make("Probe", {"UI.xml": xml2, "Core.lua": "local _, ns = ...\nns:Missing()\n"}))
check("Lua über XML geladen und geprüft", "FEHLER" in levels(r), r)

# --- Clients nach der .toc -----------------------------------------------------------------------------------------
r = ladetest.load_test(make("Probe", bad, interface="16001"))
check("nur Forever in der .toc -> nur Forever geprüft", len(r) == 1 and "WoW Forever" in r[0][1], r)
r = ladetest.load_test(make("Probe", bad, interface="120105"))
check("nur Retail -> nichts geprüft", r == [], r)
r = ladetest.load_test(make("Probe", bad, "## Dependencies: Ace3\n"))
check("braucht anderes Addon -> übersprungen", r == [], r)

# --- Weichen nach Client ------------------------------------------------------------------------------------------
flavor = {"Core.lua": "local _, ns = ...\nif select(4, GetBuildInfo()) >= 16000 then ns:OnlyForever() end\n"}
r = ladetest.load_test(make("Probe", flavor))
check("Fehler nur auf Forever -> nur dort gemeldet", len(r) == 1 and "WoW Forever" in r[0][1], r)

# --- Fehler in Start-Ereignissen: nur Warnung ---------------------------------------------------------------------
ev = {"Core.lua": "local f = CreateFrame('Frame')\nf:RegisterEvent('PLAYER_LOGIN')\n"
                  "f:SetScript('OnEvent', function() local x = nil; x.y = 1 end)\n"}
r = ladetest.load_test(make("Probe", ev))
check("Fehler bei PLAYER_LOGIN -> Warnung", levels(r) == ["WARNUNG", "WARNUNG"] and "PLAYER_LOGIN" in r[0][1], r)

# --- anderer Laufzeitfehler beim Laden: Warnung -------------------------------------------------------------------
r = ladetest.load_test(make("Probe", {"Core.lua": "local x = 1 + {}\n"}))
check("anderer Fehler beim Laden -> Warnung", levels(r) == ["WARNUNG", "WARNUNG"], r)

# --- Endlosschleife ----------------------------------------------------------------------------------------------
r = ladetest.load_test(make("Probe", {"Core.lua": "while true do end\n"}, interface="16001"))
check("Endlosschleife -> Warnung Zeitlimit", len(r) == 1 and r[0][0] == "WARNUNG" and "Zeitlimit" in r[0][1], r)

# --- eigene .toc je Client ---------------------------------------------------------------------------------------
p = TMP / "multi.zip"
with zipfile.ZipFile(p, "w") as z:
    z.writestr("Multi/Multi.toc", "## Interface: 120105\nRetail.lua\n")
    z.writestr("Multi/Multi_Camelot.toc", "## Interface: 16001\nForever.lua\n")
    z.writestr("Multi/Multi_Vanilla.toc", "## Interface: 11508\nEra.lua\n")
    z.writestr("Multi/Retail.lua", "local _, ns = ...\nns:X()\n")
    z.writestr("Multi/Forever.lua", "local _, ns = ...\nns:Y()\n")
    z.writestr("Multi/Era.lua", "local x = 1\n")
r = ladetest.load_test(p)
check("Name_Camelot.toc für Forever, Name_Vanilla.toc für Era", len(r) == 1 and "Forever.lua" in r[0][1], r)

# --- echte Fälle aus der Geschichte (wenn das Repo da ist) ---------------------------------------------------------
root = HERE.parent
try:
    blob = subprocess.run(["git", "-C", str(root), "show", "774c36b:download/ThreatSentinel-2.4.3.zip"],
                          capture_output=True, timeout=60).stdout
except Exception:
    blob = b""
if blob[:2] == b"PK":
    p = TMP / "ThreatSentinel-2.4.3.zip"
    p.write_bytes(blob)
    r = ladetest.load_test(p)
    check("ThreatSentinel 2.4.3 (lud im Spiel nicht) -> FEHLER", levels(r).count("FEHLER") == 2 and "Core.lua:702" in r[0][1], r)
# --- Sprachtest (nur WoW Forever): Sprache nach GetLocale(), ohne Test-/Entwicklermodus -----------------------------
HELP = ("local de = GetLocale() == 'deDE'\n"
        "local T = de and {a='Befehle für das Fenster und die Einstellungen', b='Das Fenster wird mit diesem Befehl geöffnet', "
        "c='Die Hilfe ist nicht mehr nötig und wird ausgeblendet'} or {a='Commands for the window and the settings', "
        "b='The window is opened with this command', c='The help is not needed and you can hide it'}\n"
        "SLASH_LANG1 = '/lang'\nSlashCmdList.LANG = function() print(T.a); print(T.b); print(T.c) end\n")
r = ladetest.load_test(make("Lang", {"Core.lua": HELP}, interface="16001"))
check("Sprache nach GetLocale -> keine Meldung", r == [], r)
DE_ONLY = HELP.replace("local de = GetLocale() == 'deDE'", "local de = true")
r = ladetest.load_test(make("Lang", {"Core.lua": DE_ONLY}, interface="16001"))
check("nur Deutsch -> WARNUNG im englischen Client", any("Sprachtest" in t and "enUS" in t for _, t in r) and "FEHLER" not in levels(r), r)
DEV_ONLY = HELP.replace("local de = GetLocale() == 'deDE'", "local dev = false\nlocal de = not dev or GetLocale() == 'deDE'")
r = ladetest.load_test(make("Lang", {"Core.lua": DEV_ONLY}, interface="16001"))
check("Englisch nur im Entwicklermodus -> WARNUNG", any("Sprachtest" in t and "enUS" in t for _, t in r), r)
EN_ONLY = HELP.replace("local de = GetLocale() == 'deDE'", "local de = false")
r = ladetest.load_test(make("Lang", {"Core.lua": EN_ONLY}, interface="16001"))
check("nur Englisch -> WARNUNG im deutschen Client", any("Sprachtest" in t and "deDE" in t for _, t in r), r)
r = ladetest.load_test(make("Lang", {"Core.lua": DE_ONLY}, interface="11508"))
check("Sprachtest nur für WoW Forever", r == [], r)
NAMES = HELP.replace("print(T.a); print(T.b); print(T.c)", "print('Defias-Schläger'); print('Höhlenspinne'); print('Murloc-Jäger'); print(T.a)")
r = ladetest.load_test(make("Lang", {"Core.lua": NAMES}, interface="16001"))
check("einzelne Namen mit Umlaut -> keine Meldung", r == [], r)

for z in sorted((root / "download").glob("*.zip")):
    if "Uploader" in z.name:
        continue
    r = ladetest.load_test(z)
    check(f"veröffentlicht {z.name} lädt ohne FEHLER", "FEHLER" not in levels(r), r)

print(f"Ladetest-Tests: {ok}/{ok + fail} bestanden")
sys.exit(1 if fail else 0)
