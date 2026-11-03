"""Tests für die Addon-Vorlage (shared/vorlage/). Läuft mit: python3 -I shared/tests/test_vorlage.py

1. Erzeugt mit shared/vorlage/neues_addon.py ein Probe-Addon samt ZIP.
2. Die Addon-Prüfung (addon-check/addon_check.py) muss es ohne FEHLER und ohne WARNUNG durchlassen.
3. Lädt das Addon in einem nachgebauten WoW (Lua 5.1 über lupa) – als WoW Forever (moderner Client, secret values,
   Settings-API) und als Classic Era (alte API, InterfaceOptions) – jeweils auf Deutsch und Englisch, startet die
   eingebaute Testroutine (/<befehl> test) und erwartet 0 FEHLER, Sandbox OK, einen gespeicherten GSTEST1-Bericht,
   unveränderte echte Daten und keine echte Aktion (kein Chat)."""
import contextlib
import io
import json
import re
import sys
import tempfile
from pathlib import Path

from lupa.lua51 import LuaRuntime

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent
ROOT = SHARED.parent
sys.path.insert(0, str(SHARED / "vorlage"))
sys.path.insert(0, str(ROOT / "addon-check"))
import neues_addon  # noqa: E402
import addon_check  # noqa: E402

fails = checks = 0


def check(label, cond, info=""):
    global fails, checks
    checks += 1
    if not cond:
        fails += 1
        print(f"FEHLT: {label} {info}")


# ------------------------------------------------------------------------------------------------------------------
# nachgebautes WoW
# ------------------------------------------------------------------------------------------------------------------
MOCK = r"""
local function noop() end
-- Dummy: jedes unbekannte Feld ist wieder ein Dummy, Aufrufen gibt einen Dummy zurück
local DummyMT = {}
DummyMT.__index = function() return setmetatable({}, DummyMT) end
DummyMT.__call = function() return setmetatable({}, DummyMT) end
function Dummy() return setmetatable({}, DummyMT) end

FRAMES, CHAT, SENT = {}, {}, {}
local FrameMT = {}
FrameMT.__index = function(t, k)
  local m = rawget(FrameMT, k)
  if m then return m end
  return setmetatable({}, DummyMT)
end
function FrameMT:RegisterEvent(e) self._events[e] = true end
function FrameMT:UnregisterEvent(e) self._events[e] = nil end
function FrameMT:IsEventRegistered(e) return self._events[e] == true end
function FrameMT:SetScript(s, fn) self._scripts[s] = fn end
function FrameMT:GetScript(s) return self._scripts[s] end
function FrameMT:HookScript(s, fn) local old = self._scripts[s]; self._scripts[s] = function(...) if old then old(...) end fn(...) end end
function FrameMT:Show() if not self._shown then self._shown = true; local f = self._scripts.OnShow; if f then f(self) end end end
function FrameMT:Hide() if self._shown then self._shown = false; local f = self._scripts.OnHide; if f then f(self) end end end
function FrameMT:IsShown() return self._shown end
function FrameMT:SetChecked(v) self._checked = v and true or false end
function FrameMT:GetChecked() return self._checked end
function FrameMT:GetName() return self._name end
function FrameMT:GetPoint() return "CENTER", nil, "CENTER", 0, 0 end
function FrameMT:SetText(t) self._text = t end
function FrameMT:GetText() return self._text end
function FrameMT:CreateFontString() return CreateFrame("FontString") end

function CreateFrame(kind, name, parent, template)
  local f = setmetatable({ _events = {}, _scripts = {}, _shown = true, _name = name, _kind = kind }, FrameMT)
  if kind == "CheckButton" then f.Text = CreateFrame("FontString") end
  if name then _G[name] = f end
  FRAMES[#FRAMES + 1] = f
  return f
end
function Fire(ev, ...)
  for _, f in ipairs(FRAMES) do
    if f._events[ev] and f._scripts.OnEvent then f._scripts.OnEvent(f, ev, ...) end
  end
end

UIParent = CreateFrame("Frame", "UIParent")
Minimap = CreateFrame("Frame", "Minimap")
UISpecialFrames = {}
ChatFontNormal = Dummy()
SlashCmdList = {}
DEFAULT_CHAT_FRAME = { AddMessage = function(_, m) CHAT[#CHAT + 1] = m end }
time = os.time
date = os.date
local clock = 0
function debugprofilestop() clock = clock + 0.01; return clock end
function debugstack() return "Interface/AddOns/X/Core.lua:1" end
local handler = function() end
function geterrorhandler() return handler end
function seterrorhandler(f) handler = f end
function InCombatLockdown() return false end
function UnitName(u) return "Tester", nil end
function UnitClass() return "Krieger", "WARRIOR" end
function UnitLevel() return 23 end
function GetItemInfo(id) return "Item" .. tostring(id) end
"""

FOREVER = r"""
function GetBuildInfo() return "1.60.1", "70753", "Nov 3 2026", 16001 end
WOW_PROJECT_CAMELOT = 99; WOW_PROJECT_ID = 99; WOW_PROJECT_MAINLINE = 1
function issecretvalue(v) return false end
C_AddOns = { GetAddOnMetadata = function(a, k) return TOC_META[k] end }
C_Item = { GetItemInfo = GetItemInfo }
C_UnitAuras = { GetAuraDataByIndex = function() return nil end }
C_ChatInfo = { SendChatMessage = function(...) SENT[#SENT + 1] = {...} end }
Settings = { RegisterCanvasLayoutCategory = function(p, n) return { ID = 7, GetID = function() return 7 end } end,
             RegisterAddOnCategory = function() end, OpenToCategory = function() end }
"""

ERA = r"""
function GetBuildInfo() return "1.15.8", "65000", "Oct 1 2026", 11508 end
WOW_PROJECT_CLASSIC = 2; WOW_PROJECT_ID = 2; WOW_PROJECT_MAINLINE = 1
function GetAddOnMetadata(a, k) return TOC_META[k] end
function UnitAura() return nil end
function SendChatMessage(...) SENT[#SENT + 1] = {...} end
function InterfaceOptions_AddCategory() end
function InterfaceOptionsFrame_OpenToCategory() end
"""


def load_addon(folder: Path, client: str, locale: str, saved=None):
    name = folder.name
    toc = (folder / f"{name}.toc").read_text(encoding="utf-8")
    meta = dict(re.findall(r"^## ([\w-]+):\s*(.*)$", toc, re.M))
    files = [l.strip() for l in toc.splitlines() if l.strip() and not l.startswith("#")]
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    lua.execute(FOREVER if client == "forever" else ERA)
    lua.execute(f'function GetLocale() return "{locale}" end')
    g = lua.globals()
    g.TOC_META = lua.table_from({k: v for k, v in meta.items()})
    if saved is not None:
        lua.execute(saved)
    ns = lua.table()
    runner = lua.eval('function(src, file, a, ns) local f = assert(loadstring(src, "@" .. file)); return f(a, ns) end')
    for f in files:
        runner((folder / f).read_text(encoding="utf-8"), f, name, ns)
    lua.execute(f'Fire("ADDON_LOADED", "{name}"); Fire("PLAYER_LOGIN")')
    return lua, ns


def dump(lua, value):
    """Lua-Tabelle -> Python (für Vergleiche)"""
    f = lua.eval("""function(v)
      local function ser(x, seen)
        if type(x) ~= "table" then return x end
        local o = {}
        for k, y in pairs(x) do if k ~= "gsTest" then o[tostring(k)] = ser(y) end end
        return o
      end
      return ser(v)
    end""")

    def conv(x):
        if hasattr(x, "items"):
            return {k: conv(v) for k, v in x.items()}
        return x
    return conv(f(value))


with tempfile.TemporaryDirectory() as d:
    # 1. erzeugen
    with contextlib.redirect_stdout(io.StringIO()):
        out, zp = neues_addon.build(type("A", (), dict(
            name="ProbeSentinel", slash="ps2", en="Probe addon", de="Probe-Addon", farbe="3fc7eb",
            icon="Interface\\Icons\\INV_Misc_QuestionMark", kategorie="Miscellaneous", ziel=d, zip=True, force=True))())
    check("Ordner erzeugt", out.is_dir())
    check("ZIP erzeugt", zp and zp.is_file())
    left = [f.name for f in out.rglob("*") if f.is_file() and neues_addon.LEFTOVER.search(f.read_text("utf-8", "replace"))]
    check("keine Platzhalter übrig", not left, left)
    for f in neues_addon.COMMON:
        check(f"{f} gleich wie shared/", (out / f).read_bytes() == (SHARED / f).read_bytes())

    # 2. Addon-Prüfung
    res = addon_check.check_zip(zp)
    check("Addon-Prüfung ohne FEHLER", not any(l == "FEHLER" for l, _ in res), res)
    check("Addon-Prüfung ohne WARNUNG", not any(l == "WARNUNG" for l, _ in res), res)

    # 3. im nachgebauten Spiel
    key = "PROBESENTINELPS2"
    for client in ("forever", "era"):
        for locale in ("deDE", "enUS"):
            tag = f"{client}/{locale}"
            lua, ns = load_addon(out, client, locale)
            g = lua.globals()
            check(f"{tag}: Version aus .toc", ns.VERSION == "0.1.0", ns.VERSION)
            check(f"{tag}: Einstellungen angelegt", g.ProbeSentinelDB is not None and g.ProbeSentinelDB.enabled is True)
            check(f"{tag}: keine Fehler beim Laden", ns.errorCount == 0, ns.errorCount)
            check(f"{tag}: Ladehinweis im Chat", any("0.1.0" in str(m) for m in g.CHAT.values()))
            before = dump(lua, g.ProbeSentinelDB)
            g.SlashCmdList[key]("test")
            rep = ns.lastReport
            check(f"{tag}: Bericht erstellt", rep is not None)
            if rep is None:
                continue
            c = rep.counts
            fehler = [f"{e.id} {e.name}: {e.lua or ''} {e.ergebnis or ''}" for e in rep.results.values()
                      if e.status == "FEHLER"]
            check(f"{tag}: 0 FEHLER in der Testroutine", c.fehler == 0, fehler)
            check(f"{tag}: Testfälle gelaufen", c.ok >= 20, c.ok)
            check(f"{tag}: Sandbox OK", rep.sandbox == "OK", rep.sandbox)
            reports = list(g.ProbeSentinelDB.gsTest.reports.values())
            check(f"{tag}: GSTEST1-Bericht gespeichert", len(reports) == 1 and reports[0].startswith("GSTEST1"))
            if reports:
                data = json.loads(reports[0][len("GSTEST1"):])
                check(f"{tag}: Bericht lesbar (JSON)", data.get("addon") == "ProbeSentinel" and data["counts"]["fehler"] == 0)
                check(f"{tag}: absichtlicher Testfehler nicht im Bericht", not data.get("errors"), data.get("errors"))
            check(f"{tag}: echte Daten unverändert", dump(lua, g.ProbeSentinelDB) == before)
            check(f"{tag}: keine echte Chat-Nachricht", len(g.SENT) == 0, len(g.SENT))
            check(f"{tag}: Testmodus wieder aus", not ns.testing)
            check(f"{tag}: Kopierfenster gezeigt", g.ProbeSentinelCopyFrame is not None and g.ProbeSentinelCopyFrame.IsShown(g.ProbeSentinelCopyFrame))
            # Einzelbereich
            g.SlashCmdList[key]("test f")
            check(f"{tag}: Einzelbereich F", ns.lastReport.counts.fehler == 0 and ns.lastReport.counts.ok == 3,
                  ns.lastReport.counts.ok)

    # alte Einstellungen (Migration, beschädigte Werte)
    lua, ns = load_addon(out, "forever", "deDE",
                         saved='ProbeSentinelDB = { dbVersion = 0, chat = false, window = "kaputt" }')
    db = lua.globals().ProbeSentinelDB
    check("alte Einstellungen: Wert bleibt", db.chat is False)
    check("alte Einstellungen: kaputtes Feld repariert", lua.eval("type")(db.window) == "table")
    check("alte Einstellungen: dbVersion gesetzt", db.dbVersion == 1)

    # Name schon veröffentlicht -> Abbruch
    try:
        with contextlib.redirect_stderr(io.StringIO()):    # erwartete Meldung nicht in den Prüfbericht schreiben
            neues_addon.build(type("A", (), dict(name="RaidMaster", slash="rmx", en="x", de="x", farbe="ffffff",
                                                 icon="x", kategorie="x", ziel=d, zip=False, force=False))())
        check("veröffentlichter Name wird abgelehnt", False)
    except SystemExit:
        check("veröffentlichter Name wird abgelehnt", True)

print(f"Vorlage-Tests: {'bestanden' if not fails else 'FEHLGESCHLAGEN'} ({checks - fails}/{checks})")
sys.exit(1 if fails else 0)
