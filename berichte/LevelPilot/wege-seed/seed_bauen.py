#!/usr/bin/env python3
"""LevelPilot – eigene Koordinatenlisten (Startwegnetz) aus den eingesandten Wegdaten (GSWEGE1).

Auftrag: anweisung-wegpunkte-strassen.txt Punkt 1/6 (Mulgore, Brachland, Donnerfels), Supervisor 15.11. 20:15.
Quelle: nur selbst gelaufene bzw. geteilte Wege aus testberichte/wege/LevelPilot/*.json (keine Spieldateien,
keine Kartenbilder, keine Namen). Ergebnis: Data/Wege.lua im Addon (Kartenkoordinaten, Umrechnung im Spiel).

Ablauf je Zone (Standard SEED_ART=skelett, so erzeugt für 3.12.37):
 1. Alle Wegstücke lesen. Schritte über SPRUNG Yards sind kein durchgehender Weg (Lücke, Ladebildschirm, Sturz).
 2. Spuren in ein Raster (ZELLE Yards) einzeichnen, 1 Zelle verbreitern (legt parallele Spuren derselben Strasse
    zusammen, schliesst Lücken einer Zelle), Zhang-Suen-Ausdünnung zur Mittellinie, kurze Sporne entfernen.
 3. Linien zwischen Kreuzungen/Enden verfolgen, Treppenstufen glätten (5 Zellen), Douglas-Peucker (TOLERANZ Yards).
 4. Prüfung: Abdeckung der gelaufenen Punkte und Startnetz-Punkte ohne gelaufenen Punkt in 15 Yards.
 SEED_ART=bauen: ältere Variante (Punkte in RADIUS zusammenlegen, alle Kanten) – genauer, aber viermal mehr Knoten.
Zonengrössen (Yards) nur für die Schwellen: Verdacht, zu messen (Werte wie HereBeDragons-Classic, Forever unbestätigt).

Aufruf: python3 seed_bauen.py <wege-ordner> <ausgabe Wege.lua> [--plot ordner]
"""
import json, glob, math, os, sys, collections

ZONEN = {  # map: (Name, Breite yd, Höhe yd)
    1412: ("Mulgore", 5137.5, 3425.0),
    1413: ("Brachland", 10133.3, 6756.2),
    1456: ("Donnerfels", 1043.7, 695.8),
    # 3.12.68 LW-4 (Supervisor 14:14: Strassennetz + vorhandene Wegdaten): weitere Aussenzonen mit genug Wegdaten.
    # Städte mit Ebenen (Orgrimmar 1454, Unterstadt 1458) bewusst nicht – W3D-Schalter aus bis zur Messung.
    1411: ("Durotar", 5287.5, 3525.0),
    1420: ("Tirisfal", 4518.75, 3012.5),
    1421: ("Silberwald", 4200.0, 2800.0),
    1424: ("Vorgebirge des Hügellands", 4850.0, 3233.3),
    1441: ("Tausend Nadeln", 4400.0, 2933.3),
    1442: ("Steinkrallengebirge", 4883.3, 3256.2),
}
SPRUNG = 80.0     # yd: längerer Schritt = kein durchgehender Weg
RADIUS = float(os.environ.get("SEED_RADIUS", "8.0"))   # yd: Punkte so nah = derselbe Knoten (Graph SNAP 10)
TOLERANZ = float(os.environ.get("SEED_TOLERANZ", "4.0"))  # yd: Vereinfachung
MIN_LAEUFE = int(os.environ.get("SEED_MIN", "1"))
JOIN = 10.0        # yd: loses Ende so nah neben einem Weg = angehängt (Graph.JOIN)


STAT_LESEN = collections.Counter()


def lesen(ordner):
    """27.11.2026 (Entscheid des Nutzers 21:47 "alles Nützliche verwenden", Wegdaten Rechner B): nichts doppelt zählen.
    - Nur Kanten mit src "selbst" (selbst gelaufen). "geteilt" = von einem anderen Spieler empfangen – die stehen schon in DESSEN
      Paketen als "selbst" (belegt 27.11.: 128 von 873 geteilten Kanten von B = Kanten des Nutzers, 341 umgekehrt).
    - Dieselbe Kante (Karte + gleiche Punkte) aus mehreren Paketen nur einmal (Pakete enthalten Wiederholungen: B 149).
    - Format 3.12.31 und 3.13.x: gleiche Felder für Wege (map, edges: n, p, src); 3.13.x hat zusätzlich lv (Ebene), qo, lu – hier
      nicht gebraucht. Koordinaten in beiden 0–100 mit 1 Nachkommastelle."""
    daten = collections.defaultdict(list)   # map -> [(datei, n, [(x,y),...])]
    gesehen = set()
    for f in sorted(glob.glob(os.path.join(ordner, "*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for z in d.get("zones", []):
            m = z.get("map")
            if m not in ZONEN:
                continue
            for e in z.get("edges", []):
                p = e.get("p") or []
                if e.get("src", "selbst") != "selbst":
                    STAT_LESEN["geteilt weggelassen"] += 1
                    continue
                key = (m, tuple(p))
                if key in gesehen:
                    STAT_LESEN["doppelt weggelassen"] += 1
                    continue
                gesehen.add(key)
                pts = [(float(p[i]), float(p[i + 1])) for i in range(0, len(p) - 1, 2)]
                if len(pts) >= 2:
                    STAT_LESEN["genommen"] += 1
                    daten[m].append((os.path.basename(f), int(e.get("n") or 1), pts))
    return daten


def bauen(m, stuecke, stat):
    _, W, H = ZONEN[m]
    yd = lambda a, b: math.hypot((a[0] - b[0]) * W / 100, (a[1] - b[1]) * H / 100)
    zelle = RADIUS / W * 100, RADIUS / H * 100
    grid = collections.defaultdict(list)
    knoten = []          # [sx, sy, anzahl]

    def knoten_fuer(p):
        cx, cy = int(p[0] / zelle[0]), int(p[1] / zelle[1])
        best, bd = None, None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for k in grid[(cx + dx, cy + dy)]:
                    q = (knoten[k][0] / knoten[k][2], knoten[k][1] / knoten[k][2])
                    d = yd(p, q)
                    if d <= RADIUS and (bd is None or d < bd):
                        best, bd = k, d
        if best is None:
            knoten.append([p[0], p[1], 1])
            best = len(knoten) - 1
            grid[(cx, cy)].append(best)
        else:
            knoten[best][0] += p[0]; knoten[best][1] += p[1]; knoten[best][2] += 1
        return best

    kanten = {}          # (a,b) -> [laeufe, dateien]
    for datei, n, pts in stuecke:
        prev = None
        for i, p in enumerate(pts):
            if i > 0 and yd(pts[i - 1], p) > SPRUNG:
                stat["sprung"] += 1
                prev = None
            k = knoten_fuer(p)
            if prev is not None and prev != k:
                key = (min(prev, k), max(prev, k))
                e = kanten.setdefault(key, [0, set()])
                e[0] = max(e[0], n)      # n zählt im Spiel weiter; dieselbe Kante in mehreren Exporten nicht addieren
                e[1].add(datei)
            prev = k
    pos = [(k[0] / k[2], k[1] / k[2]) for k in knoten]
    # Nach dem Mitteln können Kanten länger als SPRUNG geworden sein: verwerfen
    behalten = {}
    for (a, b), (l, ds) in kanten.items():
        if l < MIN_LAEUFE:
            stat["selten"] += 1
            continue
        if yd(pos[a], pos[b]) > SPRUNG:
            stat["lang"] += 1
            continue
        behalten[(a, b)] = (l, len(ds))
    # Lose Enden an die nächste Kante hängen (wie Graph:Join im Spiel, JOIN Yards): Ende liegt neben einem Weg
    behalten = einhaengen(pos, behalten, yd, stat)
    nach = collections.defaultdict(set)
    for a, b in behalten:
        nach[a].add(b); nach[b].add(a)
    # Ketten
    benutzt, ketten = set(), []
    def kette(start, nxt):
        ids = [start, nxt]
        benutzt.add((min(start, nxt), max(start, nxt)))
        while len(nach[ids[-1]]) == 2:
            a, b = nach[ids[-1]]
            n2 = b if a == ids[-2] else a
            key = (min(ids[-1], n2), max(ids[-1], n2))
            if key in benutzt:
                break
            benutzt.add(key)
            ids.append(n2)
        return ids
    for k in sorted(nach):
        if len(nach[k]) != 2:
            for n2 in sorted(nach[k]):
                if (min(k, n2), max(k, n2)) not in benutzt:
                    ketten.append(kette(k, n2))
    for (a, b) in sorted(behalten):        # reine Ringe
        if (a, b) not in benutzt:
            ketten.append(kette(a, b))
    aus = []
    for ids in ketten:
        laeufe = max(behalten[(min(x, y), max(x, y))][0] for x, y in zip(ids, ids[1:]))
        pts = dp([pos[i] for i in ids], yd)
        aus.append((laeufe, pts))
    stat["knoten"] = len(pos); stat["kanten"] = len(behalten); stat["ketten"] = len(aus)
    stat["punkte"] = sum(len(p) for _, p in aus)
    stat["laenge_km"] = round(sum(yd(a, b) for _, p in aus for a, b in zip(p, p[1:])) / 1093.6, 1)
    return aus


ZELLE = float(os.environ.get("SEED_ZELLE", "8.0"))      # yd: Rasterzelle für das Skelett
SPORN = 3                                                # Zellen: kürzere lose Enden (Rauschen der Ausdünnung) weg


def duennen(img):
    """Zhang-Suen-Ausdünnung (numpy): breite Spuren -> 1 Zelle breite Mittellinie."""
    import numpy as np
    img = img.copy().astype(np.uint8)
    while True:
        geaendert = False
        for schritt in (0, 1):
            P = np.pad(img, 1)
            p2, p3, p4 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:]
            p5, p6, p7 = P[2:, 2:], P[2:, 1:-1], P[2:, :-2]
            p8, p9 = P[1:-1, :-2], P[:-2, :-2]
            nb = [p2, p3, p4, p5, p6, p7, p8, p9]
            B = sum(x.astype(np.int32) for x in nb)
            A = sum(((nb[i] == 0) & (nb[(i + 1) % 8] == 1)).astype(np.int32) for i in range(8))
            if schritt == 0:
                c1, c2 = p2 * p4 * p6, p4 * p6 * p8
            else:
                c1, c2 = p2 * p4 * p8, p2 * p6 * p8
            weg = (img == 1) & (B >= 2) & (B <= 6) & (A == 1) & (c1 == 0) & (c2 == 0)
            if weg.any():
                img[weg] = 0
                geaendert = True
        if not geaendert:
            return img


def skelett(m, stuecke, stat):
    """Startnetz über ein Raster: Spuren einzeichnen, 1 Zelle verbreitern, ausdünnen, Linien verfolgen.
    Legt parallele Spuren derselben Strasse zu einer Linie zusammen (weniger Knoten, saubere Kreuzungen)."""
    import numpy as np
    _, W, H = ZONEN[m]
    nx, ny = int(math.ceil(W / ZELLE)) + 2, int(math.ceil(H / ZELLE)) + 2
    img = np.zeros((ny, nx), dtype=np.uint8)
    laeufe = np.zeros((ny, nx), dtype=np.int32)
    yd = lambda a, b: math.hypot((a[0] - b[0]) * W / 100, (a[1] - b[1]) * H / 100)
    zelle = lambda p: (int(p[1] * H / 100 / ZELLE), int(p[0] * W / 100 / ZELLE))
    for _, n, pts in stuecke:
        for a, b in zip(pts, pts[1:]):
            if yd(a, b) > SPRUNG:
                stat["sprung"] += 1
                continue
            (r0, c0), (r1, c1) = zelle(a), zelle(b)
            k = max(abs(r1 - r0), abs(c1 - c0), 1)
            for i in range(k + 1):
                r, c = round(r0 + (r1 - r0) * i / k), round(c0 + (c1 - c0) * i / k)
                img[r, c] = 1
                laeufe[r, c] = max(laeufe[r, c], n)
    # 1 Zelle verbreitern (schliesst Lücken einer Zelle, legt Spuren bis ~2 Zellen Abstand zusammen)
    P = np.pad(img, 1)
    breit = np.zeros_like(img)
    for dr in (0, 1, 2):
        for dc in (0, 1, 2):
            breit |= P[dr:dr + ny, dc:dc + nx]
    L = np.pad(laeufe, 1)
    lmax = np.zeros_like(laeufe)
    for dr in (0, 1, 2):
        for dc in (0, 1, 2):
            lmax = np.maximum(lmax, L[dr:dr + ny, dc:dc + nx])
    sk = duennen(breit)
    pix = set(zip(*np.nonzero(sk)))
    def nach(q):
        # 8er-Nachbarn, aber eine schräge Nachbarzelle nur, wenn sie nicht schon über eine gerade erreichbar ist
        # (sonst zählen Treppenstufen der Linie als Kreuzung)
        out = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if not (dr or dc):
                    continue
                x = (q[0] + dr, q[1] + dc)
                if x not in pix:
                    continue
                if dr and dc and ((q[0] + dr, q[1]) in pix or (q[0], q[1] + dc) in pix):
                    continue
                out.append(x)
        return out
    # Sporne (kurze lose Enden) wiederholt entfernen
    for _ in range(3):
        weg = set()
        for q in pix:
            if len(nach(q)) == 1:
                kette, cur, prev = [q], q, None
                while True:
                    nb = [x for x in nach(cur) if x != prev]
                    if len(nb) != 1 or len(nach(nb[0])) > 2:
                        break
                    prev, cur = cur, nb[0]
                    kette.append(cur)
                    if len(kette) > SPORN:
                        break
                if len(kette) <= SPORN and len(nb) == 1 and len(nach(nb[0])) > 2:
                    weg.update(kette)
        if not weg:
            break
        stat["sporne"] += len(weg)
        pix -= weg
    # Knoten = Zellen mit != 2 Nachbarn; Ketten dazwischen
    knoten = {q for q in pix if len(nach(q)) != 2}
    benutzt, ketten = set(), []
    def verfolgen(start, nxt):
        weg = [start, nxt]
        benutzt.add(frozenset((start, nxt)))
        while weg[-1] not in knoten:
            nb = [x for x in nach(weg[-1]) if frozenset((weg[-1], x)) not in benutzt]
            if not nb:
                break
            benutzt.add(frozenset((weg[-1], nb[0])))
            weg.append(nb[0])
            if weg[-1] == start:
                break
        return weg
    for q in sorted(knoten):
        for x in sorted(nach(q)):
            if frozenset((q, x)) not in benutzt:
                ketten.append(verfolgen(q, x))
    for q in sorted(pix):                       # Ringe ohne Knoten
        for x in sorted(nach(q)):
            if frozenset((q, x)) not in benutzt:
                ketten.append(verfolgen(q, x))
    zur_karte = lambda q: ((q[1] + 0.5) * ZELLE / W * 100, (q[0] + 0.5) * ZELLE / H * 100)
    aus = []
    for k in ketten:
        if len(k) < 2:
            continue
        lf = int(max(lmax[q] for q in k)) or 1
        pts = [zur_karte(q) for q in k]
        # Treppenstufen glätten (gleitender Mittelwert über 5 Zellen, Enden bleiben fest), dann vereinfachen
        if len(pts) > 4:
            g = [pts[0], pts[1]]
            for i in range(2, len(pts) - 2):
                g.append((sum(p[0] for p in pts[i - 2:i + 3]) / 5, sum(p[1] for p in pts[i - 2:i + 3]) / 5))
            pts = g + [pts[-2], pts[-1]]
        aus.append((lf, dp(pts, yd)))
    stat["zellen"] = len(pix); stat["ketten"] = len(aus)
    stat["zellen_verfolgt"] = len({q for k in ketten for q in k})
    stat["zellen_vorher"] = int(sk.sum()); stat["zellen_breit"] = int(breit.sum()); stat["zellen_spur"] = int(img.sum())
    stat["knoten"] = len(knoten); stat["kanten"] = len(aus)
    stat["punkte"] = sum(len(p) for _, p in aus)
    stat["laenge_km"] = round(sum(yd(a, b) for _, p in aus for a, b in zip(p, p[1:])) / 1093.6, 1)
    return aus


def einhaengen(pos, kanten, yd, stat):
    grad = collections.Counter()
    for a, b in kanten:
        grad[a] += 1; grad[b] += 1
    # Raster der Kanten (Mittelpunkte, grob), Suche im Umkreis
    # Zelle ~ 40 Yards (über yd() bestimmt), Kanten alle <= 20 Yards eingetragen
    ex = yd((0.0, 0.0), (1.0, 0.0)); ey = yd((0.0, 0.0), (0.0, 1.0))      # Yards je 1 % der Karte
    cw, ch = 40.0 / ex, 40.0 / ey
    def zelle(p):
        return (int(p[0] / cw), int(p[1] / ch))
    raster = collections.defaultdict(list)
    def eintragen(a, b):
        schritte = max(1, int(math.ceil(yd(pos[a], pos[b]) / 20.0)))
        for i in range(schritte + 1):
            t = i / schritte
            q = (pos[a][0] + (pos[b][0] - pos[a][0]) * t, pos[a][1] + (pos[b][1] - pos[a][1]) * t)
            if (a, b) not in raster[zelle(q)]:
                raster[zelle(q)].append((a, b))
    for (a, b) in kanten:
        eintragen(a, b)
    kanten = dict(kanten)
    for k in sorted(n for n, g in grad.items() if g == 1):
        p = pos[k]
        cx, cy = zelle(p)
        best = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for (a, b) in raster[(cx + dx, cy + dy)]:
                    if (a, b) not in kanten or k in (a, b):
                        continue
                    x, y, z = yd(pos[a], pos[b]), yd(pos[a], p), yd(pos[b], p)
                    if x <= 0 or y * y > x * x + z * z or z * z > x * x + y * y:
                        continue            # Ende liegt nicht neben der Kante (Projektion ausserhalb)
                    d = abstand(p, pos[a], pos[b], yd)
                    if d <= JOIN and (best is None or d < best[0]):
                        best = (d, a, b)
        if best:
            _, a, b = best
            l, ds = kanten.pop((a, b))
            for u, v in ((a, k), (k, b)):
                key = (min(u, v), max(u, v))
                if key not in kanten:
                    kanten[key] = (l, ds)
                    eintragen(*key)
            stat["eingehaengt"] += 1
    return kanten


def dp(pts, yd):
    if len(pts) <= 2:
        return pts
    a, b = pts[0], pts[-1]
    L = yd(a, b)
    best, bi = -1, 0
    for i in range(1, len(pts) - 1):
        p = pts[i]
        if L == 0:
            d = yd(a, p)
        else:   # Abstand Punkt-Strecke (in Yards über Projektion)
            d = abstand(p, a, b, yd)
        if d > best:
            best, bi = d, i
    if best <= TOLERANZ:
        return [a, b]
    return dp(pts[:bi + 1], yd)[:-1] + dp(pts[bi:], yd)


def abstand(p, a, b, yd):
    # in Yards: einfache Näherung über drei Seitenlängen (Heron)
    x, y, z = yd(a, b), yd(a, p), yd(b, p)
    s = (x + y + z) / 2
    flaeche = math.sqrt(max(0.0, s * (s - x) * (s - y) * (s - z)))
    h = 2 * flaeche / x if x > 0 else y
    # Projektion ausserhalb der Strecke -> Abstand zum näheren Ende
    if y * y > x * x + z * z or z * z > x * x + y * y:
        return min(y, z)
    return h


def pruefen(m, stuecke, wege, stat):
    """Abdeckung: Anteil der gelaufenen Punkte, die höchstens 15 yd neben dem Startnetz liegen.
    Abweichung: Punkte des Startnetzes (alle 5 yd entlang), die weiter als 15 yd von jedem gelaufenen Punkt liegen
    (= erfundene Verbindung). Beides in Yards über die Zonengrösse (Verdacht, s. o.)."""
    _, W, H = ZONEN[m]
    yd = lambda a, b: math.hypot((a[0] - b[0]) * W / 100, (a[1] - b[1]) * H / 100)
    C = 15.0
    cw, ch = C / W * 100, C / H * 100
    def raster(punkte):
        r = collections.defaultdict(list)
        for p in punkte:
            r[(int(p[0] / cw), int(p[1] / ch))].append(p)
        return r
    def nah(r, p):
        cx, cy = int(p[0] / cw), int(p[1] / ch)
        return any(yd(p, q) <= C for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in r[(cx + dx, cy + dy)])
    gelaufen = [p for _, _, pts in stuecke for p in pts]
    netzpunkte = []
    for _, pts in wege:
        for a, b in zip(pts, pts[1:]):
            k = max(1, int(yd(a, b) / 5))
            netzpunkte += [(a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k) for i in range(k + 1)]
    rn, rg = raster(netzpunkte), raster(gelaufen)
    abgedeckt = sum(1 for p in gelaufen if nah(rn, p))
    erfunden = [p for p in netzpunkte if not nah(rg, p)]
    stat["abdeckung"] = round(100.0 * abgedeckt / max(1, len(gelaufen)), 1)
    stat["erfunden"] = len(erfunden)
    stat["erfunden_anteil"] = round(100.0 * len(erfunden) / max(1, len(netzpunkte)), 2)
    return erfunden


def schreiben(pfad, netz, stats):
    with open(pfad, "w", encoding="utf-8", newline="\n") as f:
        f.write("-- LevelPilot - Startwegnetz: eigene Koordinatenlisten aus selbst gelaufenen Wegen von LevelPilot-Spielern\n")
        f.write("-- (eingesandte Wegdaten GSWEGE1, ohne Namen). Erzeugt mit berichte/LevelPilot/wege-seed/seed_bauen.py.\n")
        f.write("-- Keine Spieldateien, keine Kartenbilder. Format: [Karte] = { { Laeufe, x1, y1, x2, y2, ... }, ... }\n")
        f.write("-- (Kartenkoordinaten 0-100, 2 Nachkommastellen). Umrechnung in Weltkoordinaten beim Laden (Graph:LoadStatic).\n")
        for m in sorted(netz):
            s = stats[m]
            f.write(f"-- {ZONEN[m][0]} ({m}): {s['ketten']} Wege, {s['punkte']} Punkte, {s['laenge_km']} km\n")
        f.write("\nlocal _, LP = ...\nLP.SeedWege = {\n")
        for m in sorted(netz):
            f.write(f"    [{m}] = {{\n")
            for laeufe, pts in netz[m]:
                xs = ",".join(f"{x:.2f},{y:.2f}" for x, y in pts)
                f.write(f"        {{ {laeufe},{xs} }},\n")
            f.write("    },\n")
        f.write("}\n")


def plot(ordner, netz):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("(kein matplotlib – keine Bilder)")
        return
    os.makedirs(ordner, exist_ok=True)
    for m, wege in netz.items():
        name, W, H = ZONEN[m]
        fig, ax = plt.subplots(figsize=(10, 10 * H / W))
        for laeufe, pts in wege:
            ax.plot([p[0] for p in pts], [p[1] for p in pts], lw=0.6 + min(laeufe, 6) * 0.3, color="#1f5f9f")
        ax.set_xlim(0, 100); ax.set_ylim(100, 0); ax.set_title(f"{name} ({m}) – Startwegnetz"); ax.grid(alpha=0.3)
        fig.savefig(os.path.join(ordner, f"wegnetz-{m}.png"), dpi=110, bbox_inches="tight")
        plt.close(fig)


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    daten = lesen(sys.argv[1])
    netz, stats = {}, {}
    for m in sorted(ZONEN):
        st = collections.Counter()
        netz[m] = (skelett if os.environ.get("SEED_ART", "skelett") == "skelett" else bauen)(m, daten.get(m, []), st)
        st["stuecke"] = len(daten.get(m, []))
        st["dateien"] = len({d for d, _, _ in daten.get(m, [])})
        stats[m] = st
        pruefen(m, daten.get(m, []), netz[m], st)
        print(f"  Prüfung: Abdeckung {st['abdeckung']} % der gelaufenen Punkte (<= 15 yd), Startnetz-Punkte ohne gelaufenen "
              f"Punkt in 15 yd: {st['erfunden']} ({st['erfunden_anteil']} %)")
        print(f"{ZONEN[m][0]} ({m}): {st['dateien']} Dateien, {st['stuecke']} Wegstücke -> {st['knoten']} Knoten, "
              f"{st['kanten']} Kanten, {st['ketten']} Wege, {st['punkte']} Punkte, {st['laenge_km']} km "
              f"(getrennt an Sprüngen: {st['sprung']}, verworfen lang: {st['lang']}, selten: {st['selten']}, "
              f"lose Enden angehängt: {st['eingehaengt']}, Sporne entfernt: {st['sporne']} Zellen)")
    schreiben(sys.argv[2], netz, stats)
    if "--plot" in sys.argv:
        plot(sys.argv[sys.argv.index("--plot") + 1], netz)


if __name__ == "__main__":
    main()
