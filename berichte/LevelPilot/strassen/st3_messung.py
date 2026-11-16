"""ST-3 (LevelPilot, 16.11.2026): Strassennetz gegen die gelaufenen Wege der Spieler messen.

Eingaben (alles im Repo, keine Spieldateien):
  - testberichte/wege/LevelPilot/*.json  (GSWEGE1: Kanten in Kartenkoordinaten 0-100 je uiMap, ohne Namen)
  - berichte/LevelPilot/strassen/UiMapAssignment-wowf-1.60.1.csv  (Weltgrenzen je uiMap, wago.tools, Zweig wowf)
  - shared/werkzeuge/strassen/daten/strassen_netz.json  (Strassen nach ST-1, Welt-Yards; Brückenliste in stat)
Umrechnung Karte -> Welt wie C_Map.GetWorldPosFromMapPos: X(Nord) = maxX - y·(maxX-minX), Y(West) = maxY - x·(maxY-minY).

Messungen (je Zone, Paare gelaufener Knoten mit 300–2000 yd Luftlinie, feste Auswahl, höchstens 300 je Zone):
  gelaufen  = kürzester Weg im gelaufenen Netz (Obergrenze des echten Wegs, wie Analyse 07:34)
  strasse   = Luftlinie zum nächsten Strassenpunkt + kürzester Weg auf den Strassen + Luftlinie vom Strassenpunkt
  wegsuche  = was LevelPilot ohne gelaufene Wege wählt: Luftlinie (Kosten 1,45) oder Strasse (Anschlüsse 1,45, Strasse ROAD_COST)
Ausgabe: Mediane der Umweg-Faktoren, Fehler der Schätzungen gegen "gelaufen", Anteil gelaufener Wege auf Strassen,
Brücken (aus ST-1) gegen gelaufene Wege. Aufruf: python3 -I st3_messung.py <raidmaster-Ordner> [ROAD_COST]
"""
import csv
import glob
import json
import math
import os
import random
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
ROAD_COST = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
VIRT = 1.45
SNAP = 2.0        # yd: gelaufene Punkte so nah = ein Knoten
NAH = 15.0        # yd: gelaufener Punkt "auf der Strasse"
PAARE = 300

NAMEN = {1411: "Durotar", 1412: "Mulgore", 1413: "Brachland", 1414: "Kalimdor", 1416: "Alteracgebirge", 1417: "Arathihochland",
         1420: "Tirisfal", 1421: "Silberwald", 1424: "Hügelland", 1437: "Sumpfland", 1440: "Eschental", 1441: "Tausend Nadeln",
         1442: "Steinkrallen", 1443: "Desolace", 1445: "Düstermarschen", 1446: "Tanaris", 1454: "Orgrimmar", 1456: "Donnerfels",
         1458: "Unterstadt"}


def grenzen(pfad):
    g = {}
    for r in csv.DictReader(open(pfad, encoding="utf-8")):
        m = int(r["UiMapID"])
        if m in g or r["WMOGroupID"] not in ("0", ""):
            continue
        g[m] = (int(r["MapID"]), float(r["Region_0"]), float(r["Region_1"]), float(r["Region_3"]), float(r["Region_4"]))
    return g


def welt(gz, x, y):
    inst, minx, miny, maxx, maxy = gz
    return inst, maxx - (y / 100.0) * (maxx - minx), maxy - (x / 100.0) * (maxy - miny)


def lade_wege(root, g):
    """gelaufenes Netz je Zone: Knoten (Welt), Kanten (Länge); doppelte Kanten aus mehreren Einsendungen nur einmal."""
    zonen = {}
    gesehen = set()
    for f in sorted(glob.glob(os.path.join(root, "testberichte/wege/LevelPilot/*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        for z in d.get("zones", []):
            m = z["map"]
            if m not in g:
                continue
            for e in z.get("edges", []):
                key = (m, tuple(round(v, 1) for v in e["p"]))
                if key in gesehen:
                    continue
                gesehen.add(key)
                pts = [welt(g[m], e["p"][i], e["p"][i + 1]) for i in range(0, len(e["p"]) - 1, 2)]
                zonen.setdefault(m, []).append(pts)
    return zonen


def netz_aus_linien(linien):
    """Knoten zusammenlegen (SNAP), Kanten mit Länge; liefert Punkte (N×2), Kanten (i, j, l)."""
    idx, pts, kan = {}, [], []

    def nid(p):
        k = (round(p[1] / SNAP), round(p[2] / SNAP))
        if k not in idx:
            idx[k] = len(pts)
            pts.append((p[1], p[2]))
        return idx[k]

    for ln in linien:
        for a, b in zip(ln, ln[1:]):
            i, j = nid(a), nid(b)
            if i != j:
                kan.append((i, j, math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])))
    return np.array(pts), kan


def graph(n, kan):
    if not kan:
        return None
    i = [k[0] for k in kan] + [k[1] for k in kan]
    j = [k[1] for k in kan] + [k[0] for k in kan]
    w = [k[2] for k in kan] * 2
    return coo_matrix((w, (i, j)), shape=(n, n)).tocsr()


def main():
    g = grenzen(os.path.join(ROOT, "berichte/LevelPilot/strassen/UiMapAssignment-wowf-1.60.1.csv"))
    sn = json.load(open(os.path.join(ROOT, "shared/werkzeuge/strassen/daten/strassen_netz.json"), encoding="utf-8"))
    strassen = {}
    for m, k in sn["karten"].items():
        p = np.array(k["p"], dtype=float)
        kan = []
        for e in k["e"]:
            for a, b in zip(e, e[1:]):
                kan.append((a, b, float(np.hypot(*(p[a] - p[b])))))
        # dichte Punkte (alle 5 yd) für "liegt auf der Strasse"
        dicht = []
        for e in k["e"]:
            for a, b in zip(e, e[1:]):
                l = float(np.hypot(*(p[a] - p[b])))
                for t in np.linspace(0, 1, max(2, int(l / 5) + 1)):
                    dicht.append(p[a] + (p[b] - p[a]) * t)
        strassen[int(m)] = {"p": p, "G": graph(len(p), kan), "baum": cKDTree(p), "dicht": cKDTree(np.array(dicht))}
    wege = lade_wege(ROOT, g)
    rnd = random.Random(20261116)
    zeilen, alle = [], {"gl": [], "st": [], "ws": [], "f_luft": [], "f_str": [], "f_ws": []}
    auf_str_ges, len_ges = 0.0, 0.0
    walked_pts = {0: [], 1: []}
    for m in sorted(wege, key=lambda z: -len(wege[z])):
        inst = g[m][0]
        if inst not in strassen:
            continue
        S = strassen[inst]
        P, K = netz_aus_linien(wege[m])
        if len(P) < 10:
            continue
        walked_pts[inst].extend(P.tolist())
        # Anteil gelaufener Strecke auf Strassen (Mitte jeder Kante <= NAH yd)
        auf, ges = 0.0, 0.0
        for i, j, l in K:
            mid = (P[i] + P[j]) / 2
            d, _ = S["dicht"].query(mid)
            ges += l
            if d <= NAH:
                auf += l
        auf_str_ges += auf
        len_ges += ges
        GW = graph(len(P), K)
        # Paare
        res = {"gl": [], "st": [], "ws": [], "f_luft": [], "f_str": [], "f_ws": []}
        versuche = 0
        while len(res["gl"]) < PAARE and versuche < PAARE * 40:
            versuche += 1
            a, b = rnd.randrange(len(P)), rnd.randrange(len(P))
            luft = float(np.hypot(*(P[a] - P[b])))
            if not (300 <= luft <= 2000):
                continue
            dg = dijkstra(GW, indices=a, limit=luft * 4)[b]
            if not np.isfinite(dg):
                continue
            # Strasse: nächster Strassenpunkt an Start und Ziel, Weg auf den Strassen
            da, ia = S["baum"].query(P[a])
            db, ib = S["baum"].query(P[b])
            dr = dijkstra(S["G"], indices=ia, limit=luft * 4)[ib] if S["G"] is not None else np.inf
            strasse = da + dr + db
            # Wahl der Wegsuche (ohne gelaufene Wege): nach Kosten, gemessen wird die Länge
            kost_luft = VIRT * luft
            kost_str = VIRT * (da + db) + ROAD_COST * dr
            ws = luft if (not np.isfinite(kost_str) or kost_luft <= kost_str) else strasse
            res["gl"].append(dg / luft)
            res["st"].append(strasse / luft if np.isfinite(strasse) else np.nan)
            res["ws"].append(ws / luft)
            res["f_luft"].append(abs(luft * 1.25 - dg) / dg)
            res["f_str"].append(abs(strasse - dg) / dg if np.isfinite(strasse) else np.nan)
            res["f_ws"].append(abs(ws - dg) / dg)
        if len(res["gl"]) < 20:
            continue
        for k in alle:
            alle[k] += res[k]
        md = lambda v: float(np.nanmedian(v)) if len(v) else float("nan")
        zeilen.append((NAMEN.get(m, str(m)), m, len(res["gl"]), md(res["gl"]), md(res["st"]), md(res["ws"]),
                       md(res["f_luft"]), md(res["f_str"]), md(res["f_ws"]), auf / ges if ges else 0, ges))
    print("ST-3 Messung · ROAD_COST %.2f · Luftlinie-Kosten %.2f · Paare 300–2000 yd je Zone (höchstens %d)" % (ROAD_COST, VIRT, PAARE))
    print("%-16s %5s %6s | %-24s | %-30s | %s" % ("Zone", "Karte", "Paare", "Umweg gel./str./suche", "Fehler Luft×1,25 / Strasse / Suche", "auf Strasse"))
    for z in zeilen:
        print("%-16s %5d %6d | %5.2f  %5.2f  %5.2f      | %5.0f %%   %5.0f %%   %5.0f %%       | %3.0f %% von %6.0f yd" % (
            z[0], z[1], z[2], z[3], z[4], z[5], z[6] * 100, z[7] * 100, z[8] * 100, z[9] * 100, z[10]))
    md = lambda v: float(np.nanmedian(v))
    print("ALLE %d Paare: Umweg gelaufen %.2f · über Strasse %.2f · Wegsuche %.2f · Fehler Luft×1,25 %.0f %% · Strasse %.0f %% · Wegsuche %.0f %% · gelaufen auf Strasse %.0f %% von %.0f yd" % (
        len(alle["gl"]), md(alle["gl"]), md(alle["st"]), md(alle["ws"]), md(alle["f_luft"]) * 100, md(alle["f_str"]) * 100,
        md(alle["f_ws"]) * 100, auf_str_ges * 100 / len_ges, len_ges))
    # Brücken
    print("BRÜCKEN (ST-1, Lücken bis 30 yd zwischen getrennten Teilen) gegen gelaufene Wege:")
    for m, st in sn["stat"].items():
        inst = int(m)
        wp = np.array(walked_pts.get(inst) or [[1e9, 1e9]])
        baum = cKDTree(wp)
        begangen = besucht = fremd = 0
        for x1, y1, x2, y2 in st["verdichten"]["bruecken_liste"]:
            mid = ((x1 + x2) / 2, (y1 + y2) / 2)
            d, _ = baum.query(mid)
            if d <= NAH:
                begangen += 1
            elif d <= 150:
                besucht += 1
            else:
                fremd += 1
        print("  Kontinent %d: %d Brücken · gelaufen über die Brücke (<= %d yd) %d · Gegend besucht, Brücke nicht gelaufen %d · Gegend nie gelaufen %d"
              % (inst, len(st["verdichten"]["bruecken_liste"]), NAH, begangen, besucht, fremd))


if __name__ == "__main__":
    main()
