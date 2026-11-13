"""Tests für shared/GoldSentinelCmdHint.lua (gemeinsame Befehlsliste) in Lua 5.1 mit nachgebautem Client.
Läuft mit: python3 -I shared/tests/test_goldsentinelcmdhint.py

Geprüft wird: zwei Addons teilen EINE Liste und EINEN Satz Hooks, längster Präfix gewinnt, Filter beim Weitertippen,
meistbenutzte oben, Entwickler-Befehle nur mit dev, deutsche/englische Wörter, Klick wählt / Enter (Resolve) führt
die Auswahl aus, Auswahl gilt nur für das eigene Addon und 10 s, Tab/Shift+Tab, im Kampf keine Liste, abgeschaltet
keine Liste, Eingabefeld wird nie beschrieben (kein SetText/Insert/SetScript), geheime Werte nie gelesen,
Übernahme durch eine neuere Fassung, ältere Fassung überschreibt keine neuere."""
import sys
from pathlib import Path

from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
SRC = (ROOT / "shared/GoldSentinelCmdHint.lua").read_text(encoding="utf-8")

MOCK = r"""
NOW = 100
WRITES = 0
COMBAT = false
SHIFT = false
function GetTime() return NOW end
function time() return 1794580000 end
function InCombatLockdown() return COMBAT end
function IsShiftKeyDown() return SHIFT end
UIParent = {}
BackdropTemplateMixin = {}
local function obj()
  local o = { shown = false, scripts = {} }
  local mt = { __index = function(t, k) return function() end end }
  setmetatable(o, mt)
  o.Show = function(self) self.shown = true end
  o.Hide = function(self) self.shown = false end
  o.IsShown = function(self) return self.shown end
  o.SetScript = function(self, k, fn) self.scripts[k] = fn end
  o.SetText = function(self, t) self.text = t end
  o.GetText = function(self) return self.text end
  o.CreateTexture = function() return obj() end
  o.CreateFontString = function() return obj() end
  o.RegisterEvent = function() end
  return o
end
FRAMES = 0
function CreateFrame() FRAMES = FRAMES + 1; return obj() end
-- Chat-Eingabefeld: zählt jede schreibende Methode
local function box()
  local b = { text = "", hooks = {}, shown = true }
  b.GetText = function(self) return self.text end
  b.HookScript = function(self, k, fn) self.hooks[k] = self.hooks[k] or {}; table.insert(self.hooks[k], fn) end
  b.SetText = function() WRITES = WRITES + 1 end
  b.Insert = function() WRITES = WRITES + 1 end
  b.SetScript = function() WRITES = WRITES + 1 end
  b.SetFocus = function() end
  b.IsShown = function() return true end
  b.GetWidth = function() return 300 end
  return b
end
NUM_CHAT_WINDOWS = 2
ChatFrame1EditBox = box()
ChatFrame2EditBox = box()
function TYPE(b, t) b.text = t; for _, fn in ipairs(b.hooks.OnTextChanged or {}) do fn(b) end end
function TAB(b) for _, fn in ipairs(b.hooks.OnTabPressed or {}) do fn(b) end end
function NHOOKS(b) return #(b.hooks.OnTextChanged or {}) end
GoldSentinelGame = { AnySecret = function(v) return v == "GEHEIM" end }
"""

checks = []
def ok(name, cond):
    checks.append((name, bool(cond)))
    print(("OK    " if cond else "FEHLER ") + name)

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(MOCK)
lua.execute(SRC)
CH = lua.eval("GoldSentinelCmdHint")
ok("Version 1 geladen", CH is not None and CH.VERSION == 1)

lua.execute(r"""
STORE_A, STORE_B = {}, {}
GERMAN = true
DEV = false
HA = GoldSentinelCmdHint.Register({ id = "AHSentinel", prefixes = { "/ahsentinel", "/ahs" }, display = "/ahs",
  commands = { { "hilfe", "help", "Hilfe" }, { "protokoll", "log", "Protokoll" }, { "preis 100", "price 100", "Preis" },
               { "test daten", "test data", "Test" } },
  store = function() return STORE_A end, german = function() return GERMAN end, dev = function() return DEV end,
  noMatch = "kein Befehl", enterText = "Enter = %s" })
HB = GoldSentinelCmdHint.Register({ id = "Andere", prefixes = { "/a" },
  commands = { { "start", "start", "Start" } }, store = function() return STORE_B end })
""")
ok("Hooks nur einmal je Feld (zwei Addons)", lua.eval("NHOOKS(ChatFrame1EditBox)") == 1)
lua.execute('TYPE(ChatFrame1EditBox, "/ahs")')
ok("/ahs zeigt Liste von AHSentinel", lua.eval("GoldSentinelCmdHint.owner == HA and GoldSentinelCmdHint.frame.shown"))
ok("ohne dev: 3 Einträge, test ausgeblendet", lua.eval("#GoldSentinelCmdHint.items") == 3)
lua.execute('TYPE(ChatFrame1EditBox, "/a st")')
ok("/a gehört dem anderen Addon", lua.eval("GoldSentinelCmdHint.owner == HB and #GoldSentinelCmdHint.items == 1"))
lua.execute('TYPE(ChatFrame1EditBox, "/ahs pro")')
ok("Filter beim Weitertippen", lua.eval("#GoldSentinelCmdHint.items == 1 and GoldSentinelCmdHint.items[1].cmd == '/ahs protokoll'"))
lua.execute('TYPE(ChatFrame1EditBox, "/ahsentinel")')
ok("längster Präfix /ahsentinel -> AHSentinel, Anzeige /ahs", lua.eval("GoldSentinelCmdHint.owner == HA and GoldSentinelCmdHint.items[1].cmd:sub(1,5) == '/ahs '"))
lua.execute('HA:Count("protokoll"); HA:Count("protokoll"); HA:Count("preis 250")')
ok("Zähler: Beispielzahl passt auf jede Zahl", lua.eval("STORE_A['protokoll'] == 2 and STORE_A['preis'] == 1"))
lua.execute('TYPE(ChatFrame1EditBox, "/ahs")')
ok("meistbenutzte oben", lua.eval("GoldSentinelCmdHint.items[1].key == 'protokoll'"))
lua.execute('GERMAN = false; TYPE(ChatFrame1EditBox, "/ahs")')
ok("englisch: englisches Wort", lua.eval("GoldSentinelCmdHint.items[1].cmd == '/ahs log' and GoldSentinelCmdHint.items[1].run == 'log'"))
lua.execute('GERMAN = true; DEV = true; TYPE(ChatFrame1EditBox, "/ahs te")')
ok("dev: Testbefehl sichtbar", lua.eval("#GoldSentinelCmdHint.items == 1"))
lua.execute('DEV = false; TYPE(ChatFrame1EditBox, "/ahs")')
# Klick wählt, Enter führt aus
lua.execute('GoldSentinelCmdHint.frame.rows[2].scripts.OnClick(GoldSentinelCmdHint.frame.rows[2])')
sel = lua.eval("GoldSentinelCmdHint:Selection().item.run")
ok("Klick wählt (nicht ausführen)", sel is not None)
ok("Auswahl gilt nicht für ein anderes Addon", lua.eval('HB:Resolve("")') == "")
ok("Enter mit leerem Rest -> Auswahl", lua.eval('HA:Resolve("")') == sel)
lua.execute('GoldSentinelCmdHint:Select(GoldSentinelCmdHint.items[1], true); NOW = NOW + 11')
ok("Auswahl nach 10 s ungültig", lua.eval('HA:Resolve("hi")') == "hi")
lua.execute('NOW = NOW + 1; GoldSentinelCmdHint:Select(GoldSentinelCmdHint.items[1], true)')
ok("anderer Text -> getippter Text gilt", lua.eval('HA:Resolve("zzz")') == "zzz")
lua.execute('GoldSentinelCmdHint.selected = nil; TAB(ChatFrame1EditBox)')
ok("Tab wählt den ersten", lua.eval("GoldSentinelCmdHint:Selection().item == GoldSentinelCmdHint.items[1]"))
lua.execute('SHIFT = true; TAB(ChatFrame1EditBox); SHIFT = false')
ok("Shift+Tab wählt rückwärts (letzter)", lua.eval("GoldSentinelCmdHint:Selection().item == GoldSentinelCmdHint.items[#GoldSentinelCmdHint.items]"))
lua.execute('COMBAT = true; TYPE(ChatFrame1EditBox, "/ahs")')
ok("im Kampf keine Liste", lua.eval("not GoldSentinelCmdHint.frame.shown"))
lua.execute('COMBAT = false; HA.enabled = function() return false end; TYPE(ChatFrame1EditBox, "/ahs")')
ok("abgeschaltet keine Liste", lua.eval("not GoldSentinelCmdHint.frame.shown"))
lua.execute('HA.enabled = nil; TYPE(ChatFrame1EditBox, "GEHEIM")')
ok("geheimer Wert -> keine Liste, kein Fehler", lua.eval("not GoldSentinelCmdHint.frame.shown"))
lua.execute('TYPE(ChatFrame1EditBox, "hallo welt")')
ok("normaler Chat -> keine Liste", lua.eval("not GoldSentinelCmdHint.frame.shown"))
ok("Eingabefeld nie beschrieben (SetText/Insert/SetScript)", lua.eval("WRITES") == 0)
# ältere Fassung darf nicht überschreiben
older = SRC.replace("local VERSION = 1", "local VERSION = 0", 1)
lua.execute(older)
ok("ältere Fassung überschreibt nicht", lua.eval("GoldSentinelCmdHint.VERSION") == 1)
# neuere Fassung übernimmt
newer = SRC.replace("local VERSION = 1", "local VERSION = 2", 1)
lua.execute("OLDCH = GoldSentinelCmdHint")
lua.execute(newer)
ok("neuere Fassung übernimmt", lua.eval("GoldSentinelCmdHint.VERSION == 2 and GoldSentinelCmdHint ~= OLDCH"))
ok("Anmeldungen übernommen (Handle bleibt gleich)", lua.eval("GoldSentinelCmdHint.Get('AHSentinel') == HA"))
ok("keine doppelten Hooks nach Übernahme", lua.eval("NHOOKS(ChatFrame1EditBox)") == 1)
lua.execute('TYPE(ChatFrame1EditBox, "/ahs")')
ok("alte Hooks rufen neue Fassung", lua.eval("GoldSentinelCmdHint.frame ~= nil and GoldSentinelCmdHint.frame.shown and GoldSentinelCmdHint.owner == HA"))
lua.execute('GoldSentinelCmdHint:Select(GoldSentinelCmdHint.items[1], true)')
ok("Resolve über altes Handle nach Übernahme", lua.eval('HA:Resolve("")') == lua.eval("GoldSentinelCmdHint.items[1].run"))
ok("ungültige Anmeldung -> nil", lua.eval("GoldSentinelCmdHint.Register({ prefixes = {'/x'} }) == nil"))

bad = [n for n, c in checks if not c]
print(f"{len(checks) - len(bad)}/{len(checks)} Prüfungen bestanden")
sys.exit(1 if bad else 0)
