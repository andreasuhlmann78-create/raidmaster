"""Test der Auswertung mit erfundener Messung (zwei Ebenen an derselben 2D-Stelle, nur die Unterzone trennt). python3 -I test_auswerten.py"""
import os, sys, tempfile, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
L = [
 "# GSWegMess 1.0 Start 16.11.2026 10:00:00 · Spalten: …",
 "0.0|64.30|35.90|1458|-|Unterstadt|Handwerksviertel|Handwerksviertel|1|0|0|7.0|START",
 "5.0|64.31|35.91|1458|-|Unterstadt|Handwerksviertel|Handwerksviertel|1|0|0|7.0|MARK Aufzug unten",
 "21.0|64.31|35.91|1458|-|Unterstadt|Ruinen von Lordaeron|Ruinen von Lordaeron|0|0|0|0.0|ZONE_CHANGED",
 "25.0|64.40|35.95|1458|-|Unterstadt|Ruinen von Lordaeron|Ruinen von Lordaeron|0|0|0|7.0|MARK Aufzug oben",
 "30.0|70.00|30.00|1458|-|Unterstadt|Die Kanäle|Die Kanäle|1|1|0|7.0|",
 "31.0|70.01|30.00|1458|-|Unterstadt|Die Kanäle|Die Kanäle|1|0|1|5.0|STOP Befehl",
]
body = "GSWegMessDB = {\n[\"lines\"] = {\n" + "\n".join('"' + s.replace('"', '\\"') + '", -- [%d]' % (i + 1) for i, s in enumerate(L)) + "\n},\n}\n"
ok = fail = 0
def check(n, c):
    global ok, fail
    if c: ok += 1
    else: fail += 1; print("FEHLT:", n)
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "GSWegMess.lua"); open(p, "w", encoding="utf-8").write(body)
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "auswerten.py"), p], capture_output=True, text=True)
    out = r.stdout
    check("läuft ohne Fehler", r.returncode == 0)
    check("Zeilen gelesen (6)", "Zeilen: 6" in out)
    check("Abschnitte nach Notizen", "- Aufzug unten:" in out and "- Aufzug oben:" in out)
    check("Umlaut korrekt gelesen", "Die Kanäle" in out)
    check("Unterzone trennt allein an derselben Stelle", "subzone:" in out and "trennt 0" not in out.split("- subzone:")[1].split("\n")[0])
    check("Karte trennt nicht", "trennt 0" in out.split("- map:")[1].split("\n")[0])
    check("Wechsel ohne Bewegung erkannt (Aufzug)", "davon 1 fast ohne 2D-Bewegung" in out.split("- subzone:")[1].split("\n")[0])
    check("Sturz gezählt", "Stürze (fällt 0 -> 1): 1" in out)
    check("Ereignis gezählt", "ZONE_CHANGED 1" in out)
    open(p, "w").write("GSWegMessDB = {}\n")
    r2 = subprocess.run([sys.executable, "-I", os.path.join(HERE, "auswerten.py"), p], capture_output=True, text=True)
    check("leere Datei -> klare Meldung, Ausgang 2", r2.returncode == 2 and "Keine Messzeilen" in r2.stdout)
print(f"{ok}/{ok + fail} Prüfungen bestanden"); sys.exit(1 if fail else 0)
