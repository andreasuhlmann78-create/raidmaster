"""Ende-zu-Ende-Test der Testberichte (läuft mit: python3 -I addon-check/test_testberichte.py).
Addon (shared/GoldSentinelTest.lua in Lua 5.1) -> SavedVariables wie WoW sie schreibt -> Import -> status.md/json.
Läuft in einem Temp-Ordner; das echte testberichte/ bleibt unberührt."""
import gzip
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

from lupa.lua51 import LuaRuntime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
spec = importlib.util.spec_from_file_location("tb", HERE / "testberichte.py")
tb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tb)

fails = checks = 0


def check(label, got, want):
    global fails, checks
    checks += 1
    if got != want:
        fails += 1
        print(f"FEHLER [{label}] = {got!r} (erwartet {want!r})")
    elif "-v" in sys.argv:
        print(f"OK [{label}]")


lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute("""
function GetBuildInfo() return '1.60.1','70707','x',16001 end
function UnitClass() return 'Magier','MAGE' end
function UnitLevel() return 12 end
local t = 1793750400
function time() t = t + 1 return t end
""")
lua.execute((ROOT / "shared" / "GoldSentinelGame.lua").read_text(encoding="utf-8"))
lua.execute((ROOT / "shared" / "GoldSentinelTest.lua").read_text(encoding="utf-8"))
lua.execute(r"""
DB = {}
local T = GoldSentinelTest.Begin('BuffSentinel', '0.9.5', DB)
T:Check('T01', 'A', 'Version', function() return true end)
T:Check('T02', 'C', 'Auren geschützt', function() return false, 'Lua-Fehler "x"', 'Hinweis' end)
T:Check('T03', 'C', 'Abklingzeit', function() error('Display.lua:12: attempt to compare secret') end)
T:Client('T04', 'C', 'Dispel im Kampf', 'einen Kampf machen')
GoldSentinelTest.registry.BuffSentinel = { version = '0.9.5', db = DB }
GoldSentinelTest.Error('BuffSentinel', 'UNIT_AURA', 'Core.lua:99: ä ö ü – kaputt')
T:Finish({ sandbox = 'OK' })
GoldSentinelTest.Error('BuffSentinel', 'Lua', 'Display.lua:5: später')
GoldSentinelTest.Flush()
""")


def wow_serialize(v, indent=0):
    """So schreibt WoW SavedVariables (Strings mit \\" \\\\ \\n, Nicht-ASCII als Bytes unverändert)."""
    pad = "\t" * indent
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if hasattr(v, "items"):
        parts = []
        for k, x in v.items():
            key = f'["{k}"]' if isinstance(k, str) else f"[{k}]"
            parts.append(f"{pad}\t{key} = {wow_serialize(x, indent + 1)},")
        return "{\n" + "\n".join(parts) + f"\n{pad}}}"
    return "nil"


sv = "BuffSentinelDB = " + wow_serialize(lua.eval("DB")) + "\n"
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    tb.OUT = tmp / "testberichte"
    tb.STORE = tb.OUT / "berichte"
    (tmp / "BuffSentinel.lua").write_text(sv, encoding="utf-8")

    reps = tb.from_bytes("BuffSentinel.lua", (tmp / "BuffSentinel.lua").read_bytes())
    check("2 Berichte in den SavedVariables", sorted(r["kind"] for r in reps), ["fehler", "test"])
    check("neu gespeichert", tb.store(reps), 2)
    check("doppelt nicht nochmals", tb.store(reps), 0)

    # wie der Uploader sie schickt: JSON-Liste, gzip
    payload = gzip.compress(json.dumps([r for r in reps]).encode())
    check("Uploader-Format gelesen", len(tb.from_bytes("testberichte.json.gz", payload)), 2)
    check("kaputte Datei", tb.from_bytes("x.json.gz", b"\x1f\x8bkaputt"), [])
    check("fremdes JSON verworfen", tb.from_text('[{"f":2,"kind":"test"}]'), [])
    check("Pfad-Angriff entschärft", tb.clean({"f": 1, "kind": "test", "addon": "../../x", "id": "a/b"})["addon"], ".._.._x")

    st = tb.evaluate()
    md = (tb.OUT / "status.md").read_text(encoding="utf-8")
    check("Tabelle", "| BuffSentinel |" in md, True)
    check("FEHLER aufgelistet", ("T02" in md, "T03" in md, "T01" in md), (True, True, False))
    check("Sonderzeichen", "ä ö ü – kaputt" in md, True)
    check("offen: 2 Test-Fehler + 2 Spiel-Fehler",
          (sum(1 for o in st["offen"] if o["art"] == "test"), sum(1 for o in st["offen"] if o["art"] == "spiel")), (2, 2))
    check("Client erkannt", st["offen"][0]["client"].startswith("forever"), True)

print(f"Testberichte-Tests: {'bestanden' if fails == 0 else 'FEHLGESCHLAGEN'} ({checks - fails}/{checks})")
sys.exit(1 if fails else 0)
