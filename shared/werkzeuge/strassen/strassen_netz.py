"""Strassennetz aus den Strassen-Masken bauen – Supervisor GoldSentinel, 16.11.2026 (Auftrag des Nutzers 08:01).

Schritt 3 (läuft in der Cloud, braucht numpy/scipy/scikit-image):
  Maske (strassen_maske.json) -> Raster je Kontinent (1 Zelle = 2,083 Yards) -> kleine Lücken schliessen (Dilatation),
  Kleinteile entfernen -> Mittellinie (Skelett) -> Graph (Knoten = Kreuzungen/Enden, Kanten = Linienzüge)
  -> Linienzüge vereinfachen (Douglas-Peucker) -> Punkte + Kanten in Welt-Yards.
Ausgabe: JSON (zum Prüfen) und Lua-Datendatei für LevelPilot (anonym, keine Namen).
Aufruf: python3 -I strassen_netz.py strassen_maske.json <ausgabe-ordner>
"""
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage
from skimage.morphology import skeletonize

TILE = 533.33333
CELL = TILE / 256.0
ORIGIN = 32 * TILE
MIN_TEIL = 60          # Zellen; kleinere Flecken (Pflaster in Dörfern, Einzelflecken) fallen weg
LUECKE = 2             # Zellen Dilatation, schliesst Lücken bis ~8 Yards
EPS = 4.0              # Yards Toleranz Douglas-Peucker
MIN_KANTE = 15.0       # Yards: kürzere Stummel an Enden fallen weg


def raster(karte):
    ts = [tuple(map(int, k.split("_"))) for k in karte]
    y0, x0 = min(t[0] for t in ts), min(t[1] for t in ts)
    y1, x1 = max(t[0] for t in ts), max(t[1] for t in ts)
    g = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256), dtype=bool)
    for k, v in karte.items():
        ty, tx = map(int, k.split("_"))
        for ci, h in v["c"].items():
            r, c = divmod(int(ci), 16)
            b = int(h, 16)
            for z in range(256):
                if b >> z & 1:
                    zy, zx = divmod(z, 16)
                    g[(ty - y0) * 256 + r * 16 + zy, (tx - x0) * 256 + c * 16 + zx] = True
    return g, y0, x0


def welt(gy, gx, y0, x0):
    """Rasterzelle -> Welt-Yards (X nach Norden, Y nach Westen, wie UnitPosition/C_Map.GetWorldPosFromMapPos)."""
    wx = ORIGIN - (y0 * TILE + (gy + 0.5) * CELL)
    wy = ORIGIN - (x0 * TILE + (gx + 0.5) * CELL)
    return round(wx, 1), round(wy, 1)


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = np.array(pts[0]), np.array(pts[-1])
    ab = b - a
    n = np.hypot(*ab)
    best, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        p = np.array(pts[i])
        d = abs(ab[0] * (a[1] - p[1]) - ab[1] * (a[0] - p[0])) / n if n else np.hypot(*(p - a))
        if d > best:
            best, idx = d, i
    if best > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def graph(sk):
    ys, xs = np.nonzero(sk)
    on = set(zip(ys.tolist(), xs.tolist()))
    deg = {p: sum((p[0] + dy, p[1] + dx) in on for dy, dx in NB) for p in on}
    knoten = {p for p, d in deg.items() if d != 2}
    kanten, besucht = [], set()
    for s in knoten:
        for dy, dx in NB:
            q = (s[0] + dy, s[1] + dx)
            if q not in on or (s, q) in besucht:
                continue
            weg, prev, cur = [s], s, q
            besucht.add((s, q))
            while True:
                weg.append(cur)
                if cur in knoten:
                    besucht.add((cur, prev))
                    break
                nxt = [(cur[0] + a, cur[1] + b) for a, b in NB if (cur[0] + a, cur[1] + b) in on and (cur[0] + a, cur[1] + b) != prev]
                nxt = [n for n in nxt if n not in weg[-3:]]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]
            kanten.append(weg)
    # reine Ringe ohne Knoten
    rest = on - {p for w in kanten for p in w}
    while rest:
        s = rest.pop()
        weg, cur, prev = [s], s, None
        while True:
            nxt = [(cur[0] + a, cur[1] + b) for a, b in NB if (cur[0] + a, cur[1] + b) in rest]
            if not nxt:
                break
            cur = nxt[0]
            rest.discard(cur)
            weg.append(cur)
        if len(weg) > 1:
            weg.append(s)
            kanten.append(weg)
    return kanten


def laenge(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


def netz(karte):
    g, y0, x0 = raster(karte)
    g = ndimage.binary_dilation(g, iterations=LUECKE)
    lab, n = ndimage.label(g, structure=np.ones((3, 3)))
    sizes = ndimage.sum(g, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= MIN_TEIL])
    sk = skeletonize(keep)
    kanten = graph(sk)
    pkt, idx, out = [], {}, []

    def pid(p):
        if p not in idx:
            idx[p] = len(pkt)
            pkt.append(p)
        return idx[p]

    for w in kanten:
        wp = [welt(y, x, y0, x0) for y, x in w]
        if laenge(wp) < MIN_KANTE and (len(w) < 2):
            continue
        s = rdp(wp, EPS)
        out.append([pid(p) for p in s])
    # Endstummel (ein Ende frei, kurz) entfernen
    grad = {}
    for e in out:
        grad[e[0]] = grad.get(e[0], 0) + 1
        grad[e[-1]] = grad.get(e[-1], 0) + 1
    out = [e for e in out if not ((grad[e[0]] == 1 or grad[e[-1]] == 1) and laenge([pkt[i] for i in e]) < MIN_KANTE)]
    return pkt, out, int(keep.sum())


def lua(netze, info):
    z = ["-- GoldSentinel Strassennetz WoW Forever (automatisch erzeugt, nicht von Hand ändern)",
         "-- Quelle: Bodentexturen der Spieldateien (ADT tex0, Strassen-Texturen), Werkzeug raidmaster/shared/werkzeuge/strassen",
         "-- Koordinaten: Welt-Yards (x nach Norden, y nach Westen) wie C_Map.GetWorldPosFromMapPos; je Karte (0 = Östl. Königreiche,",
         "-- 1 = Kalimdor) Punkte p = {x1,y1, x2,y2, ...} und Kanten e = { {i1,i2,...}, ... } als Linienzüge über Punkt-Nummern (1-basiert).",
         "GoldSentinelStrassen = GoldSentinelStrassen or {}",
         "GoldSentinelStrassen.version = 1",
         "GoldSentinelStrassen.client = %s" % json.dumps(info["client"]),
         "GoldSentinelStrassen.karten = {"]
    for m, (pkt, kan) in netze.items():
        z.append("  [%s] = {" % m)
        flat = []
        for x, y in pkt:
            flat += ["%g" % x, "%g" % y]
        z.append("    p = {")
        for i in range(0, len(flat), 20):
            z.append("      " + ",".join(flat[i:i + 20]) + ",")
        z.append("    },")
        z.append("    e = {")
        for e in kan:
            z.append("      {" + ",".join(str(i + 1) for i in e) + "},")
        z.append("    },")
        z.append("  },")
    z.append("}")
    return "\n".join(z) + "\n"


def main(src, outdir):
    d = json.load(open(src))
    netze, stat = {}, {}
    for m, karte in d["karten"].items():
        pkt, kan, zellen = netz(karte)
        netze[m] = (pkt, kan)
        stat[m] = {"punkte": len(pkt), "kanten": len(kan),
                   "km_yards": round(sum(laenge([pkt[i] for i in e]) for e in kan)), "zellen_nach_filter": zellen}
    os.makedirs(outdir, exist_ok=True)
    json.dump({"client": d["client"], "stat": stat, "karten": {m: {"p": p, "e": e} for m, (p, e) in netze.items()}},
              open(os.path.join(outdir, "strassen_netz.json"), "w"), separators=(",", ":"))
    open(os.path.join(outdir, "GoldSentinelStrassen.lua"), "w", encoding="utf-8").write(lua(netze, d))
    print(json.dumps(stat))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
