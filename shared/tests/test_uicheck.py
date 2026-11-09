"""Test der Oberflächen-Prüfung der Vorlage (UICheck.lua, Testfälle T18–T23) mit nachgebauten Fenstern in Lua 5.1.
Läuft mit: python3 -I shared/tests/test_uicheck.py"""
import sys
from pathlib import Path

from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
SRC = (ROOT / "shared/vorlage/__ADDON__/UICheck.lua").read_text(encoding="utf-8")

MOCK = r"""
local function Frame(name, l, b, w, h, kind)
  local f = { _name = name, _rect = { l, b, w, h }, _shown = true, _kids = {}, _scripts = {}, _kind = kind or "Frame" }
  function f:GetName() return self._name end
  function f:GetRect() return self._rect[1], self._rect[2], self._rect[3], self._rect[4] end
  function f:GetEffectiveScale() return 1 end
  function f:IsVisible() return self._shown end
  function f:IsShown() return self._shown end
  function f:Show() self._shown = true end
  function f:Hide() self._shown = false end
  function f:GetChildren() return unpack(self._kids) end
  function f:GetScript(s) return self._scripts[s] end
  function f:SetScript(s, fn) self._scripts[s] = fn end
  function f:IsObjectType(t) return t == self._kind end
  function f:GetObjectType() return self._kind end
  function f:GetRegions() return end
  return f
end
_G.Frame = Frame
UIParent = Frame("UIParent", 0, 0, 1000, 800)
GameTooltip = Frame("GameTooltip", 0, 0, 0, 0)
GameTooltip._shown = false
function GameTooltip:Hide() self._shown = false end
UnitLevel = function() return 11 end
"""


def run(setup):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    ns = lua.table()
    lua.execute("ADDON_NS = ...", ns)
    fn = lua.execute("return function(src, ns) local chunk = assert(loadstring(src)); chunk('Probe', ns) end")
    fn(SRC, ns)
    lua.globals().NS = ns
    return lua, lua.execute(setup)


fails = checks = 0


def check(label, got, want):
    global fails, checks
    checks += 1
    if got != want:
        fails += 1
        print(f"FEHLER [{label}] = {got!r} (erwartet {want!r})")


# T18: Tooltip über einem Knopf -> Befund; Tooltip daneben -> keiner
for label, tip, want in (("Tooltip verdeckt Knopf", (110, 110, 100, 40), 1), ("Tooltip daneben", (400, 400, 100, 40), 0)):
    lua, n = run(f"""
      local win = Frame("Win", 100, 100, 300, 200)
      local a = Frame("KnopfA", 110, 250, 80, 20, "Button")
      local b = Frame("KnopfB", 110, 110, 80, 20, "Button")
      win._kids = {{ a, b }}
      a:SetScript("OnEnter", function() GameTooltip._rect = {{ {tip[0]}, {tip[1]}, {tip[2]}, {tip[3]} }}; GameTooltip._shown = true end)
      NS.RegisterUI(win, "Win")
      local p = NS.UICheck.TooltipsCoverNothing()
      return #p
    """)
    check(label, n, want)

# T19: Fenster über ProfessionsFrame -> Befund; angedockt (Kante an Kante) -> keiner
for label, x, want in (("überdeckt Berufsfenster", 250, 1), ("angedockt", 400, 0)):
    lua, n = run(f"""
      ProfessionsFrame = Frame("ProfessionsFrame", 0, 100, 400, 500)
      local win = Frame("Win", {x}, 100, 300, 500)
      NS.RegisterUI(win, "Win")
      return #NS.UICheck.WindowsOverlapNothing()
    """)
    check(label, n, want)

# T19: Fenster eines anderen GoldSentinel-Addons
lua, n = run("""
  GoldSentinelUIFrames = { { frame = Frame("Fremd", 500, 100, 200, 200), name = "Fremd", addon = "AnderesAddon" } }
  local win = Frame("Win", 450, 150, 200, 100)
  NS.RegisterUI(win, "Win")
  return #NS.UICheck.WindowsOverlapNothing()
""")
check("überdeckt anderes GoldSentinel-Fenster", n, 1)

# T20: aus dem Bildschirm
lua, n = run("""
  NS.RegisterUI(Frame("Win", 900, 100, 300, 100), "Win")
  return #NS.UICheck.InsideScreen()
""")
check("ragt aus dem Bildschirm", n, 1)

# T22: Plausibilität (Stufe 11 ok; eigene Prüfung schlägt fehl)
lua, n = run("""
  NS.Plausible("Fertigkeit", function() return false, 0, "> 0" end)
  return #NS.UICheck.ValuesPlausible()
""")
check("unplausibler Wert erkannt", n, 1)

# T23: Fehlerschleife
lua, n = run("""
  NS.db = { diag = { entries = { { k = "FEHLER", t = "x", n = 588 }, { k = "FEHLER", t = "y", n = 3 } } } }
  return #NS.UICheck.NoErrorLoops()
""")
check("Fehlerschleife erkannt", n, 1)

# Verfügbarkeit
lua, ok = run("""NS.RegisterUI(Frame("Win", 0, 0, 10, 10), "Win"); return NS.UICheck.Available()""")
check("echter Client erkannt", ok, True)

print(f"UICheck-Tests: {'bestanden' if fails == 0 else 'FEHLGESCHLAGEN'} ({checks - fails}/{checks})")
sys.exit(1 if fails else 0)
