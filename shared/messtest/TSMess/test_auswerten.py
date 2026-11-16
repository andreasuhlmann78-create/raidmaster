"""Test der Auswertung mit erfundenen Messungen (Era: alles lesbar; Forever: im Kampf geschützt). python3 -I test_auswerten.py"""
import os, sys, tempfile, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))

ERA = [
 "# TSMess 1.0 Start 16.11.2026 10:00:00 · Interface 11508 · Spalten: …",
 "0.0|E|-|START",
 "1.0|E|-|KAMPF Beginn",
 "1.0|U|player|0|1|85.00|93.50|12000.00|1|1|",
 "1.0|U|party1|1|3|100.00|100.00|14000.00|3|3|",
 "2.0|U|player|0|1|87.00|95.70|12500.00|1|1|",
 "2.0|U|party1|1|3|100.00|100.00|14300.00|3|3|",
 "3.0|Z|-|kein Ziel",
 "4.0|E|-|KAMPF Ende",
 "5.0|E|-|STOP Befehl",
]
FOREVER = [
 "# TSMess 1.0 Start 16.11.2026 10:00:00 · Interface 16001 · Spalten: …",
 "0.0|E|-|START",
 "1.0|E|-|KAMPF Beginn",
 "1.0|U|player|0|G|G|G|G|G|1|",
 "1.0|U|party1|1|3|G|G|G|3|3|",
 "2.0|U|player|0|G|G|G|G|G|1|",
 "2.0|U|party1|1|3|G|G|G|3|3|",
 "2.0|U|pet|-|-|-|-|-|F|-|F",
 "3.0|E|-|KAMPF Ende",
]
PROZENT = [
 "1.0|E|-|KAMPF Beginn",
 "1.0|U|player|0|1|85.00|G|G|1|1|",
 "1.0|U|party1|1|3|100.00|G|G|3|3|",
]


def body(lines):
    return "TSMessDB = {\n[\"lines\"] = {\n" + "\n".join('"' + s.replace('"', '\\"') + '", -- [%d]' % (i + 1) for i, s in enumerate(lines)) + "\n},\n}\n"


ok = fail = 0
def check(n, c):
    global ok, fail
    if c:
        ok += 1
    else:
        fail += 1
        print("FEHLT:", n)


def run(lines):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "TSMess.lua")
        open(p, "w", encoding="utf-8").write(body(lines))
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "auswerten.py"), p], capture_output=True, text=True)
        return r.returncode, r.stdout


rc, out = run(ERA)
check("Era: läuft ohne Fehler", rc == 0)
check("Era: Zähler", "Kämpfe: 1 · Messungen je Einheit im Kampf: 4 · ohne Ziel: 1" in out)
check("Era: ganzzahlige Prozent erkannt", "scaled    nil 0 · geschützt 0 · Zahl 2 (ganzzahlig 2)" in out)
check("Era: Rohwert nicht ganzzahlig", "raw       nil 0 · geschützt 0 · Zahl 2 (ganzzahlig 0)" in out)
check("Era: Urteil möglich", "Urteil N4: MÖGLICH" in out)
check("Era: Anteile 100 %", "Prozent Spieler 100 % · Rohwert Spieler 100 % · Rohwert Tank 100 %" in out)
rc, out = run(FOREVER)
check("Forever: läuft", rc == 0)
check("Forever: geschützt gezählt", "value     nil 0 · geschützt 2 · Zahl 0" in out)
check("Forever: Fehler-Spalte (pet)", "uts_ziel  nil 0 · geschützt 0 · Zahl 0 (ganzzahlig 0) · wahr/falsch 0 · Fehler 1" in out)
check("Forever: Urteil nicht möglich", "Urteil N4: NICHT MÖGLICH" in out)
rc, out = run(PROZENT)
check("nur Prozent lesbar", "Urteil N4: NUR PROZENT" in out)
rc, out = run(["# leer"])
check("ohne Messung: nicht entschieden", "Urteil N4: NICHT ENTSCHIEDEN" in out)
print("Auswertung: %d OK, %d FEHLER" % (ok, fail))
sys.exit(1 if fail else 0)
