"""Test für addon-check/wege_check.py (läuft mit: python3 -I addon-check/test_wege_check.py)."""
import importlib.util
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("wc", HERE / "wege_check.py")
wc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wc)

fails = checks = 0


def check(label, got, want):
    global fails, checks
    checks += 1
    if got != want:
        fails += 1
        print(f"FEHLER [{label}] = {got!r} (erwartet {want!r})")


exports = [{
    "f": 1, "kind": "wege", "id": "w1", "addon": "LevelPilot",
    "zones": [{"map": 1412, "name": "Mulgore", "edges": [
        {"p": [40.0, 60.0, 41.0, 60.5, 42.0, 61.0], "src": "selbst", "n": 5},     # Teil A
        {"p": [42.0, 61.0, 43.0, 61.5], "src": "geteilt", "n": 1},                # hängt an A
        {"p": [70.0, 20.0, 71.0, 21.0], "src": "selbst", "n": 1},                 # Teil B (Lücke)
        {"p": [50.0, 50.0, 58.0, 50.0], "src": "selbst", "n": 1},                 # Sprung 8 %
        {"p": [101.0, 5.0, 100.5, 5.5], "src": "selbst", "n": 1},                 # ausserhalb
    ]}],
    "blocked": [{"map": 1412, "p": [41.0, 60.5], "why": "FEST", "t": 1}],          # gesperrt, aber 5× gelaufen
    "npc": [{"id": 3233, "map": 1412, "old": [62.0, 58.0], "new": [47.5, 58.4], "t": 1},
            {"id": 9999, "map": 1412, "old": [10.0, 10.0], "new": None, "t": 1},
            {"id": 2995, "map": 1456, "new": [46.8, 50.1], "old": [1456, 47, 49.8], "t": 1},
            {"id": 246152, "map": 1420, "new": [61.5, 53.4], "nopack": True, "t": 1},
            {"id": 3370, "map": 1454, "new": [43.8, 74.7], "t": 1}],
}]

rep, npc = wc.analyse(exports)
m = rep[1412]
check("Wegstücke", m["edges"], 5)
check("Lücke erkannt (mehr als 1 Teil)", len(m["parts"]) > 1, True)
check("Sprung erkannt", any("Sprung 8.0" in o for o in m["outliers"]), True)
check("ausserhalb erkannt", any("ausserhalb" in o for o in m["outliers"]), True)
check("Widerspruch gesperrt/gelaufen", len(m["conflicts"]), 1)
check("NPC deutlich falsch", npc[0][4], "deutlich falsch")
check("NPC nicht da", npc[1][2], "nicht da (Nutzer)")
check("NPC ohne Ort im Datenpaket (nopack)", npc[3][4], "fehlt im Datenpaket")
check("NPC ohne old, mit new", npc[4][4], "fehlt im Datenpaket")
check("NPC mit Karte im alten Ort", (npc[2][3], npc[2][4]), ("0.4 %", "klein"))

with tempfile.TemporaryDirectory() as tmp:
    out = wc.write(rep, npc, Path(tmp) / "auswertung.md")
    md = out.read_text(encoding="utf-8")
    check("Bericht: Zone", "## Mulgore (1412)" in md, True)
    check("Bericht: Lücken", "**Lücken:**" in md, True)
    check("Bericht: NPC-Tabelle", "| 3233 | 1412 |" in md, True)
    out2 = wc.write({}, [], Path(tmp) / "leer.md")
    check("leer", "Noch keine Wegdaten." in out2.read_text(encoding="utf-8"), True)

print(f"Wegdaten-Tests: {'bestanden' if fails == 0 else 'FEHLGESCHLAGEN'} ({checks - fails}/{checks})")
sys.exit(1 if fails else 0)
