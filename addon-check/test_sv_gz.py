"""Test UP-422b (23.11.2026): Die Markt-Werkzeuge lesen SavedVariables auch gepackt (.lua.gz, Uploader 2.3.18).
Aufruf: python3 -I addon-check/test_sv_gz.py  -> 'n/n Prüfungen bestanden', Exit 0."""
import gzip, os, sys, tempfile, importlib
HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "marktanalyse"))
ok = fehl = 0
def pruef(name, bed):
    global ok, fehl
    if bed: ok += 1
    else: fehl += 1; print("FEHLER", name)
inhalt = 'AHSentinelDB = { markets = { ["Alle|Horde"] = { data = { [2589] = { history = { {1, 2, 3} } } } } } }\n-- Umlaut: ä ö ü\n'
d = tempfile.mkdtemp()
roh = os.path.join(d, "AHSentinel.lua"); gz = roh + ".gz"
open(roh, "w", encoding="utf-8").write(inhalt)
with gzip.open(gz, "wt", encoding="utf-8") as fh: fh.write(inhalt)
for modul in ("markt_tabellen", "buchhaltung_plausi"):
    m = importlib.import_module(modul)
    pruef(modul + " hat sv_lesen", hasattr(m, "sv_lesen"))
    if hasattr(m, "sv_lesen"):
        pruef(modul + " .lua.gz = .lua", m.sv_lesen(gz) == m.sv_lesen(roh) == inhalt)
mt = importlib.import_module("markt_tabellen")
db = mt.load(gz)
pruef("markt_tabellen.load(.lua.gz) liest die Tabelle", db.markets["Alle|Horde"].data[2589].history[1][3] == 3)
# Gegenprobe: altes Lesen (open().read()) liefert bei .gz kein Lua
try:
    alt = open(gz, encoding="utf-8", errors="replace").read()
    pruef("Gegenprobe: altes Lesen erkennt .gz nicht", "AHSentinelDB" not in alt)
except Exception:
    pruef("Gegenprobe: altes Lesen erkennt .gz nicht", True)
print(f"{ok}/{ok + fehl} Prüfungen bestanden")
sys.exit(1 if fehl else 0)
