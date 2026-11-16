"""Auswertung einer TSMess-Messung (ThreatSentinel N4-MESS, 16.11.2026).

Aufruf:  python3 -I shared/messtest/TSMess/auswerten.py <SavedVariables/TSMess.lua>

Liest TSMessDB.lines (Spalten: Zeit|Art|Einheit|isTanking|status|scaled|raw|value|uts_ziel|uts|Fehler) und beantwortet:
"Liefert das Spiel im Kampf lesbare Bedrohungswerte – reicht es für N4 (Abstand/Zeit bis zum Aggro-Ziehen)?"
Ausgabe:
  1. Zeilen, Kämpfe, Messungen im Kampf, Messungen ohne Ziel.
  2. Je Einheit und Feld: wie oft nil (-), geschützt (G), Zahl (davon ganzzahlig), wahr/falsch, Fehler (F).
  3. Urteil N4: lesbarer Anteil (Zahl / (Zahl + geschützt)) für Prozent (scaled) und Rohwert (value) des Spielers
     und des Tanks (Einheit mit isTanking = 1). N4 "möglich" nur, wenn beide Rohwerte in mindestens 90 % lesbar sind.
Die Datei enthält keine Namen (nur Kennungen player, pet, party1–4).
"""
import re
import sys
from collections import defaultdict

FIELDS = ["isTanking", "status", "scaled", "raw", "value", "uts_ziel", "uts"]
SCHWELLE = 0.90


def read_lines(text):
    """Die Einträge aus TSMessDB.lines (Lua-Zeichenketten) lesen – ohne Lua, nur die Liste."""
    m = re.search(r'\["lines"\]\s*=\s*\{(.*?)\n\s*\}', text, re.S)
    if not m:
        return []
    out = []
    for s in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)):
        if "\\" in s:
            s = s.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")
        out.append(s)
    return out


def kind(v):
    if v == "-":
        return "nil"
    if v == "G":
        return "geschützt"
    if v == "F":
        return "Fehler"
    if v in ("0", "1"):
        return "wahr/falsch"
    try:
        x = float(v)
    except ValueError:
        return "?"
    return "Zahl"


def is_int(v):
    try:
        return float(v) == int(float(v))
    except ValueError:
        return False


def auswerten(lines):
    out = []
    fights, in_fight, samples, no_target = 0, False, 0, 0
    stats = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))   # unit -> field -> kind -> n
    ints = defaultdict(lambda: defaultdict(int))                          # unit -> field -> ganzzahlige Zahlen
    tank_value = defaultdict(int)                                         # Zahl / geschützt beim Tank (isTanking = 1)
    n = 0
    for ln in lines:
        if ln.startswith("#"):
            continue
        n += 1
        p = ln.split("|")
        if len(p) < 4:
            continue
        art = p[1]
        if art == "E":
            if p[3].startswith("KAMPF Beginn"):
                fights += 1
                in_fight = True
            elif p[3].startswith("KAMPF Ende"):
                in_fight = False
            continue
        if art == "Z":
            no_target += 1
            continue
        if art != "U" or len(p) < 10:
            continue
        samples += 1
        unit = p[2]
        vals = p[3:10]
        for f, v in zip(FIELDS, vals):
            k = kind(v)
            stats[unit][f][k] += 1
            if k == "Zahl" and is_int(v):
                ints[unit][f] += 1
        if vals[0] == "1":
            tank_value[kind(vals[4])] += 1
    out.append("Zeilen: %d · Kämpfe: %d · Messungen je Einheit im Kampf: %d · ohne Ziel: %d" % (n, fights, samples, no_target))
    out.append("")
    out.append("Je Einheit und Feld (nil / geschützt / Zahl (ganzzahlig) / wahr-falsch / Fehler):")
    for unit in sorted(stats):
        out.append("  %s:" % unit)
        for f in FIELDS:
            s = stats[unit][f]
            out.append("    %-9s nil %d · geschützt %d · Zahl %d (ganzzahlig %d) · wahr/falsch %d · Fehler %d" % (
                f, s["nil"], s["geschützt"], s["Zahl"], ints[unit][f], s["wahr/falsch"], s["Fehler"]))

    def share(d):
        z, g = d.get("Zahl", 0), d.get("geschützt", 0)
        return (z / (z + g)) if (z + g) else None

    p_scaled = share(stats["player"]["scaled"]) if "player" in stats else None
    p_value = share(stats["player"]["value"]) if "player" in stats else None
    t_value = share(tank_value)

    def pct(x):
        return "keine Werte" if x is None else "%.0f %%" % (x * 100)

    out.append("")
    out.append("Lesbar im Kampf: Prozent Spieler %s · Rohwert Spieler %s · Rohwert Tank %s" % (pct(p_scaled), pct(p_value), pct(t_value)))
    if p_value is None or t_value is None:
        verdict = "NICHT ENTSCHIEDEN – zu wenig Werte (als DD in einer Gruppe mit Tank kämpfen, Ziel anwählen)"
    elif p_value >= SCHWELLE and t_value >= SCHWELLE:
        verdict = "MÖGLICH – Rohwerte von Spieler und Tank lesbar (Abstand und Bedrohung je Sekunde berechenbar)"
    elif p_scaled is not None and p_scaled >= SCHWELLE:
        verdict = "NUR PROZENT – Rohwerte geschützt; Zeit bis Pull nur grob aus dem Prozent-Verlauf (Verdacht, zu messen)"
    else:
        verdict = "NICHT MÖGLICH – im Kampf geschützt"
    out.append("Urteil N4: " + verdict)
    return "\n".join(out), verdict


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    text = open(argv[1], encoding="utf-8").read()
    report, _ = auswerten(read_lines(text))
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
