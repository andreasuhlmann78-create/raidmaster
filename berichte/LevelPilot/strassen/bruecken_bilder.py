"""ST-3 Nachtrag (LevelPilot, 16.11.2026, Prüfung 09:18): je verdächtiger Brücke ein Bild.

Verdächtig = Lücke, die ST-1 bis 30 yd überbrückt hat, wo Spieler in der Gegend waren (gelaufener Punkt <= 150 yd), aber nie
über die Brücke gelaufen sind (kein gelaufener Punkt <= 15 yd an ihrer Mitte). Bild: Strassen grau, Brücke rot, gelaufene
Wege blau, Ausschnitt 400 × 400 yd. Dazu eine Liste mit Zone und Kartenkoordinaten (zum Nachsehen im Spiel).
Aufruf: python3 -I bruecken_bilder.py <raidmaster-Ordner>
"""
import importlib.util
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
HIER = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("st3", os.path.join(HIER, "st3_messung.py"))
st3 = importlib.util.module_from_spec(spec)
sys.argv = [sys.argv[0], ROOT]
spec.loader.exec_module(st3)


def zone_von(g, inst, x, y):
    """kleinste Karte (uiMap) dieses Kontinents, deren Grenzen den Weltpunkt enthalten -> (uiMap, Karte-x, Karte-y)."""
    best = None
    for m, (mi, minx, miny, maxx, maxy) in g.items():
        if mi != inst or not (minx <= x <= maxx and miny <= y <= maxy) or m in (1414, 1415):
            continue
        flaeche = (maxx - minx) * (maxy - miny)
        if best is None or flaeche < best[0]:
            best = (flaeche, m, (maxy - y) / (maxy - miny) * 100, (maxx - x) / (maxx - minx) * 100)
    return best[1:] if best else (None, None, None)


def main():
    g = st3.grenzen(os.path.join(ROOT, "berichte/LevelPilot/strassen/UiMapAssignment-wowf-1.60.1.csv"))
    sn = json.load(open(os.path.join(ROOT, "shared/werkzeuge/strassen/daten/strassen_netz.json"), encoding="utf-8"))
    wege = st3.lade_wege(ROOT, g)
    lin = {0: [], 1: []}
    for m, ls in wege.items():
        for ln in ls:
            if ln and ln[0][0] in lin:
                lin[ln[0][0]].append(np.array([(p[1], p[2]) for p in ln]))
    out = os.path.join(ROOT, "berichte/LevelPilot/strassen/bruecken")
    os.makedirs(out, exist_ok=True)
    liste = ["Verdächtige Brücken (ST-1, Gegend besucht, Brücke nie gelaufen) – Prüfung 09:18",
             "Nr  Kontinent  Zone (uiMap)  Karte x/y   Länge  nächster gelaufener Punkt   Bild"]
    nr = 0
    for m, st in sorted(sn["stat"].items()):
        inst = int(m)
        alle = np.vstack(lin[inst]) if lin[inst] else np.array([[1e9, 1e9]])
        baum = cKDTree(alle)
        p = np.array(sn["karten"][m]["p"])
        for x1, y1, x2, y2 in st["verdichten"]["bruecken_liste"]:
            mid = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
            d, _ = baum.query(mid)
            if not (15 < d <= 150):
                continue
            nr += 1
            fig, ax = plt.subplots(figsize=(4, 4))
            R = 200
            for e in sn["karten"][m]["e"]:
                q = p[e]
                if np.min(np.hypot(q[:, 0] - mid[0], q[:, 1] - mid[1])) < 2 * R:
                    ax.plot(-q[:, 1], q[:, 0], "-", color="0.6", lw=1.2)
            for ln in lin[inst]:
                if np.min(np.hypot(ln[:, 0] - mid[0], ln[:, 1] - mid[1])) < 2 * R:
                    ax.plot(-ln[:, 1], ln[:, 0], "-", color="tab:blue", lw=0.8)
            ax.plot([-y1, -y2], [x1, x2], "-", color="tab:red", lw=3)
            ax.set_xlim(-mid[1] - R, -mid[1] + R)
            ax.set_ylim(mid[0] - R, mid[0] + R)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
            zm, zx, zy = zone_von(g, inst, mid[0], mid[1])
            name = st3.NAMEN.get(zm, str(zm))
            ax.set_title("Brücke %d: %s %.1f/%.1f\nLänge %.0f yd, gelaufen %.0f yd daneben" % (
                nr, name, zx or 0, zy or 0, np.hypot(x2 - x1, y2 - y1), d), fontsize=8)
            datei = "bruecke-%02d.png" % nr
            plt.tight_layout()
            plt.savefig(os.path.join(out, datei), dpi=70)
            plt.close()
            liste.append("%2d  %d          %-22s %5.1f/%5.1f  %4.0f yd  %5.0f yd                    %s" % (
                nr, inst, "%s (%s)" % (name, zm), zx or 0, zy or 0, np.hypot(x2 - x1, y2 - y1), d, datei))
    open(os.path.join(out, "liste.txt"), "w", encoding="utf-8").write("\n".join(liste) + "\n")
    print("\n".join(liste))


if __name__ == "__main__":
    main()
