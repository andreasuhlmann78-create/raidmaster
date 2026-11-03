#!/usr/bin/env python3
"""Tests für die Regeln der Addon-Prüfung gegen Taint, Aktionen in Testdateien und geheime Namen.

Aufruf: python3 addon-check/test_addon_check_regeln.py   (läuft auch über addon_check.py mit, siehe ALL_TESTS)
Jede Regel wird mit einem Treffer und mit den typischen Fehlalarm-Fällen geprüft.
"""
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import addon_check as a  # noqa: E402

ok = fail = 0


def check(name, cond):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
        print("FEHLT:", name)


def taint(src):
    return [n for _, n in a.blizz_overrides(a.lua_blank(src))]


def secret(src):
    b = a.lua_blank(src)
    return [] if a.SECRET_GUARD.search(b) else a.secret_name_uses(b)


def actions(src):
    return [m.group(0) for m in a.TEST_ACTIONS.finditer(a.lua_blank(src))]


# --- lua_blank ---------------------------------------------------------------------------------------------------
src = 'local x = "a -- b" -- UnitName = 1\n--[==[\nUnitName = f\n]==]\nlocal s = [[\nUnitName = f\n]]\ny = "target"\n'
b = a.lua_blank(src)
check("Zeilenzahl bleibt", b.count("\n") == src.count("\n"))
check("Kommentar weg", "UnitName" not in b)
check("Wort-String bleibt", '"target"' in b)
check("String mit -- bricht nicht ab", b.startswith('local x = "'))
check("grosse Datei schnell", len(a.lua_blank("x = 1 -- k\n" * 200000)) > 0)

# --- Taint -------------------------------------------------------------------------------------------------------
check("UnitName = function", taint("UnitName = function() return 'x' end") == ["UnitName"])
check("Einrückung und Semikolon", taint("\t ;GetServerTime = f") == ["GetServerTime"])
check("_G.Name", taint("_G.GetTime = f") == ["GetTime"])
check('_G["Name"]', taint('_G["UnitExists"] = f') == ["UnitExists"])
check("rawset", taint('rawset(_G, "UnitIsPlayer", f)') == ["UnitIsPlayer"])
check("function Name()", taint("function GetRealmName() end") == ["GetRealmName"])
check("C_-Namensraum", taint("C_ChatInfo.SendChatMessage = f") == ["C_ChatInfo.SendChatMessage"])
check("function C_X.Y()", taint("function C_Timer.After(s, f) end") == ["C_Timer.After"])
check("Zurücksetzen zählt auch", taint("local o = UnitName\nUnitName = f\nUnitName = o") == ["UnitName", "UnitName"])
check("lokale Kopie erlaubt", taint("local UnitName = UnitName") == [])
check("lokale Variable danach erlaubt", taint("local UnitName = UnitName\nUnitName = f") == [])
check("lokale Funktion erlaubt", taint("local function GetTime() return 1 end") == [])
check("Parameter erlaubt", taint("local function f(GetMoney) GetMoney = 1 end") == [])
check("for-Variable erlaubt", taint("for UnitName, v in pairs(t) do UnitName = 1 end") == [])
check("Tabellenfeld einzeilig erlaubt", taint("local t = { UnitName = function() end }") == [])
check("Tabellenfeld mehrzeilig erlaubt", taint("local mock = {\n  UnitName = function() end,\n  GetTime = 1,\n}") == [])
check("Feld eines eigenen Objekts erlaubt", taint("RM.UnitName = f\nself.GetTime = g") == [])
check("Vergleich ist keine Zuweisung", taint("if UnitName == nil then end") == [])
check("eigene Globale erlaubt", taint("RaidMasterDB = RaidMasterDB or {}\nSLASH_RM1 = '/rm'") == [])
check("in Kommentar erlaubt", taint("-- UnitName = f\n--[[ GetTime = f ]]") == [])
check("in String erlaubt", taint('print("UnitName = f")\nlocal h = [[\nGetTime = f\n]]') == [])
check("hooksecurefunc erlaubt", taint('hooksecurefunc("UnitName", f)') == [])
# Fälle aus der Gegenprüfung vom 3. November
check("local über zwei Zeilen erlaubt", taint("local frame,\n      GetTime = CreateFrame('Frame'), 0") == [])
check("eigene Tabelle C_Helper erlaubt", taint("local C_Helper = {}\nC_Helper.Get = function() end") == [])
check("eigene Tabelle _G erlaubt", taint("local _G = {}\n_G.UnitName = 1") == [])
check("local _G = _G bleibt echt", taint("local _G = _G\n_G.UnitName = f") == ["UnitName"])
check("local C_Timer = C_Timer bleibt echt", taint("local C_Timer = C_Timer\nC_Timer.After = f") == ["C_Timer.After"])
check("Kompat-Ersatz taintet auch", taint("GetAddOnMetadata = GetAddOnMetadata or C_AddOns.GetAddOnMetadata") == ["GetAddOnMetadata"])
check("local in anderem Bereich zählt nicht", taint("do local UnitName = 1 end\nUnitName = function() end") == ["UnitName"])
check("Parameter anderer Funktion zählt nicht", taint("local function f(GetTime) end\nGetTime = function() end") == ["GetTime"])
check("Parameter in eigener Funktion erlaubt", taint("local function f(GetTime)\n  GetTime = GetTime or 0\nend") == [])
check("for-Variable nur in der Schleife", taint("for UnitName in pairs(t) do end\nUnitName = f") == ["UnitName"])
check("Funktion in Testtabelle", taint("ns.tests = {\n run = function()\n  UnitName = fake\n end }") == ["UnitName"])
check("function _G.X()", taint("function _G.GetTime() return 0 end") == ["GetTime"])
check("_G['X'] einfach", taint("_G['GetTime'] = f") == ["GetTime"])
check("rawset einfach", taint("rawset(_G, 'UnitName', f)") == ["UnitName"])
check("mehrere Ziele", taint("UnitName, GetTime = 1, 2") == ["UnitName", "GetTime"])
check("nach then", taint("if x then UnitName = f end") == ["UnitName"])
check("Methode auf C_-Namensraum", taint("function C_Map:GetBestMapForUnit() end") == ["C_Map.GetBestMapForUnit"])
check("if/elseif/else ohne Durcheinander",
      taint("if a then\n local UnitName = 1\nelseif b then\nelse\nend\nUnitName = f") == ["UnitName"])
check("repeat/until", taint("repeat local GetTime = 1 until true\nGetTime = f") == ["GetTime"])
check("while do", taint("while x do local GetTime = 1 end\nGetTime = f") == ["GetTime"])
check("{ in String stört nicht", taint('local s = "{"\nUnitName = f') == ["UnitName"])
check("viele Zeilen schnell", len(taint("GetTime = i\n" * 20000)) == 20000)

# --- Aktionen in Testdateien -------------------------------------------------------------------------------------
check("Testdatei Test.lua", a.TEST_FILE.search("GuildSentinel/Test.lua"))
check("Testdatei SelfTest.lua", a.TEST_FILE.search("AHSentinel/SelfTest.lua"))
check("Testdatei AutoTest.lua", a.TEST_FILE.search("ProfessionSentinel/AutoTest.lua"))
check("Testdatei TestMode.lua", a.TEST_FILE.search("ThreatSentinel/TestMode.lua"))
check("Testdatei im Ordner Test/", a.TEST_FILE.search("RaidMaster/Test/LootData.lua"))
check("keine Testdatei: Core.lua", not a.TEST_FILE.search("RaidMaster/Core.lua"))
check("keine Testdatei: Diag.lua", not a.TEST_FILE.search("RaidMaster/Diag.lua"))
check("keine Testdatei: Latest.lua", not a.TEST_FILE.search("RaidMaster/Latest.lua"))
check("keine Testdatei: Contest.lua", not a.TEST_FILE.search("Modules/Contest.lua"))
check("keine Testdatei: Attestation.lua", not a.TEST_FILE.search("X/Attestation.lua"))
check("Testdatei im Ordner Tests/", a.TEST_FILE.search("X/Tests/Run.lua"))
check("Testdatei test_util.lua", a.TEST_FILE.search("X/test_util.lua"))
check("SendChatMessage", actions('SendChatMessage("x", "RAID")'))
check("C_ChatInfo.SendChatMessage", actions('C_ChatInfo.SendChatMessage("x", "GUILD")'))
check("BuyMerchantItem", actions("BuyMerchantItem(3, 20)"))
check("RepairAllItems", actions("RepairAllItems()"))
check("CraftRecipe", actions("C_TradeSkillUI.CraftRecipe(123, 1)"))
check("Auktion", actions("C_AuctionHouse.PostItem(loc, 1, 1, 100)"))
check("Gilde einladen", actions('GuildInvite("x")'))
check("eigene Hülle erlaubt", actions('TM:Send("x")\nns.SendChatMessage("x")\nself:BuyMerchantItem(1)') == [])
check("Erwähnung im String erlaubt", actions('log("SendChatMessage(x)")') == [])
check("Prüfen, ob es die Funktion gibt, erlaubt", actions("if SendChatMessage then ok() end") == [])

# --- geheime Namen -----------------------------------------------------------------------------------------------
check("UnitName(target):lower()", secret('local n = UnitName("target"):lower()'))
check("als Schlüssel", secret('local b = Bosses[UnitName("boss1")]'))
check("Vergleich", secret('if UnitName("target") == "Ragnaros" then end'))
check("strlower()", secret('local n = strlower(UnitName("focus"))'))
check("Zweischritt :lower()", secret('local name = UnitName("target")\nif not name then return end\nreturn idx[name:lower()]'))
check("Zweischritt Schlüssel", secret('local name, realm = UnitName("target")\nreturn idx[name]'))
check("Zweischritt zweite Variable", secret('local n, r = UnitName("target")\nif r == "Realm" then end'))
check("Zweischritt Vergleich", secret('local n = UnitName("target")\nif n ~= "" then end'))
check("mit Schutz erlaubt", secret('local n = UnitName("target")\nif G.IsSecret(n) then return end\nreturn idx[n:lower()]') == [])
check("Zusammensetzen erlaubt", secret('local n, r = UnitName("target")\nif n then return n .. "-" .. r end') == [])
check("Weitergeben erlaubt", secret('self:Render(list, UnitName("target"))') == [])
check("Spieler-Name erlaubt", secret('local me = UnitName("player"):lower()') == [])
check("neu belegt bricht ab", secret('local n = UnitName("target")\nlocal n = "x"\nreturn n:lower()') == [])
check("weit weg nicht mehr zugeordnet", secret('local n = UnitName("target")\n' + "x()\n" * 12 + "return n:lower()") == [])


# --- check_zip: FEHLER, Warnung, Altlast ---------------------------------------------------------------------------
def make_zip(d, addon, ver, files):
    p = Path(d) / f"{addon}-{ver}.zip"
    toc = f"## Interface: 11508, 16001\n## Version: {ver}\n" + "\n".join(files) + "\n"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr(f"{addon}/{addon}.toc", toc)
        for f, body in files.items():
            z.writestr(f"{addon}/{f}", body)
    return p


with tempfile.TemporaryDirectory() as d:
    mock = "local o = UnitName\nUnitName = function() return 'Boss' end\nUnitName = o\n"
    r = a.check_zip(make_zip(d, "ProbeAddon", "9.9.1", {"Core.lua": "local x = 1\n", "Test.lua": mock}))
    check("geladene Datei mit Taint -> FEHLER", any(l == "FEHLER" and "Test.lua:2" in t and "UnitName" in t for l, t in r))
    r = a.check_zip(make_zip(d, "ProbeAddon", "9.9.2", {"Core.lua": 'SendChatMessage("x")\n',
                                                       "Test.lua": 'SendChatMessage("x", "RAID")\n'}))
    acts = [t for l, t in r if "direkt auf" in t]
    check("Aktion in Testdatei -> Warnung", len(acts) == 1 and "Test.lua:1" in acts[0])
    check("Aktion ausserhalb von Testdateien bleibt erlaubt", not any("Core.lua" in t and "direkt auf" in t for t in acts))
    check("Aktion ist kein FEHLER", not any(l == "FEHLER" for l, t in r))
    r = a.check_zip(make_zip(d, "ProbeAddon", "9.9.6", {"Test.lua": "local function SendChatMessage(m) log(m) end\n"
                                                                    "function BuyMerchantItem(i) end\nSendChatMessage('x')\n"}))
    check("Ersatz-Funktion im Test erlaubt", not any("direkt auf" in t for l, t in r))
    r = a.check_zip(make_zip(d, "ProbeAddon", "9.9.3", {"Core.lua": 'local n = UnitName("target")\nreturn t[n]\n'}))
    check("geheimer Name -> Warnung", any(l == "WARNUNG" and "Core.lua:2" in t and "geheim" in t for l, t in r))
    a.ALTLAST.add(("probeaddon", "9.9.4"))
    r = a.check_zip(make_zip(d, "ProbeAddon", "9.9.4", {"Test.lua": mock}))
    check("Altlast -> nur Warnung", not any(l == "FEHLER" and "UnitName" in t for l, t in r)
          and any(l == "WARNUNG" and "nächsten Version" in t for l, t in r))
    r = a.check_zip(make_zip(d, "ProbeAddon", "9.9.5", {"Test.lua": mock}))
    check("nächste Version nach Altlast -> wieder FEHLER", any(l == "FEHLER" and "UnitName" in t for l, t in r))

print(f"{ok}/{ok + fail} Prüfungen bestanden")
sys.exit(1 if fail else 0)
