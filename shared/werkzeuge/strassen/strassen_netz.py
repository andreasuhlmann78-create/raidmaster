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
# ST-1 (LevelPilot, 16.11.2026): Verdichten nach dem Skelett
KNOTEN_R = 6.0         # Yards: Kreuzungs-Knoten, die über so kurze Kanten verbunden sind, werden ein Knoten (Skelett-Haufen)
BRUECKE = 30.0         # Yards: loses Ende so nah an einem ANDEREN Teil = verbinden (Strasse unter Brücke/Tunnel unterbrochen)
MIN_NETZ = 200.0       # Yards: Teile mit weniger Gesamtlänge fallen weg (Pflasterflecken in Dörfern, Durotar)


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
    pkt, out, st = verdichten(pkt, out)
    return pkt, out, int(keep.sum()), st


class _UF:
    def __init__(self):
        self.p = {}

    def f(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def u(self, a, b):
        self.p[self.f(a)] = self.f(b)


def _grade(kan):
    g = {}
    for e in kan:
        g[e[0]] = g.get(e[0], 0) + 1
        g[e[-1]] = g.get(e[-1], 0) + 1
    return g


def _laenge_e(pkt, e):
    return laenge([pkt[i] for i in e])


def verdichten(pkt, kan):
    """ST-1: Skelett-Haufen zusammenlegen, Lücken bis BRUECKE zwischen getrennten Teilen schliessen, kleine Teile weg,
    Knoten mit Grad 2 zusammenlegen, kurze Endstummel weg. pkt = [(x, y)], kan = [[Punkt-Nummern]]; Ergebnis neu nummeriert.
    Liefert (pkt, kan, stat)."""
    pkt = [tuple(p) for p in pkt]
    st = {}
    L = lambda ks: round(sum(_laenge_e(pkt, e) for e in ks))
    st["yards_0_start"] = L(kan)
    # 1) Kreuzungs-Haufen: Kanten kürzer als KNOTEN_R zwischen zwei Knoten -> ein Knoten (Mittelpunkt)
    uf = _UF()
    kurz = 0
    for e in kan:
        if _laenge_e(pkt, e) < KNOTEN_R:
            uf.u(e[0], e[-1])
            kurz += 1
    grp = {}
    for e in kan:
        for i in (e[0], e[-1]):
            grp.setdefault(uf.f(i), set()).add(i)
    rep = {}
    for r, mem in grp.items():
        if len(mem) == 1:
            rep[next(iter(mem))] = next(iter(mem))
            continue
        x = sum(pkt[i][0] for i in mem) / len(mem)
        y = sum(pkt[i][1] for i in mem) / len(mem)
        pkt.append((round(x, 1), round(y, 1)))
        for i in mem:
            rep[i] = len(pkt) - 1
    neu = []
    for e in kan:
        if _laenge_e(pkt, e) < KNOTEN_R:
            continue
        e = [rep[e[0]]] + e[1:-1] + [rep[e[-1]]]
        if e[0] == e[-1] and len(e) <= 3:
            continue                                      # winzige Schleife am Knoten
        neu.append(e)
    # doppelte Kanten zwischen denselben zwei Knoten mit fast gleicher Länge: nur eine behalten
    best, extra = {}, []
    doppelt = 0
    for e in neu:
        k = (min(e[0], e[-1]), max(e[0], e[-1]))
        l = _laenge_e(pkt, e)
        if k not in best:
            best[k] = (l, e)
        elif abs(best[k][0] - l) <= max(5.0, 0.2 * max(l, best[k][0])):
            doppelt += 1                                 # zweite Spur derselben Strasse
            if l < best[k][0]:
                best[k] = (l, e)
        else:
            extra.append(e)                              # echte zweite Strasse zwischen denselben Knoten
    st["yards_1a_ohne_kurze_kanten"] = L([e for e in kan if _laenge_e(pkt, e) >= KNOTEN_R])
    st["yards_1b_enden_zum_haufen_mitte"] = L(neu)
    kan = [v[1] for v in best.values()] + extra
    st["doppelte_spuren_weg"] = doppelt
    st["yards_1c_ohne_doppelte_spuren"] = L(kan)
    st["kurze_kanten_zusammengelegt"] = kurz
    # 2) Brücken: loses Ende (Grad 1) -> nächster Punkt auf einer Kante eines ANDEREN Teils, höchstens BRUECKE Yards
    uf = _UF()
    for e in kan:
        for a, b in zip(e, e[1:]):
            uf.u(a, b)
    g = _grade(kan)
    enden = [i for i, d in g.items() if d == 1]
    segs = []   # (Kante, Position, a, b)
    for ei, e in enumerate(kan):
        for j in range(len(e) - 1):
            segs.append((ei, j, e[j], e[j + 1]))
    # Raster für die Suche
    zell = {}
    Z = BRUECKE
    for si, (ei, j, a, b) in enumerate(segs):
        xa, ya = pkt[a]
        xb, yb = pkt[b]
        for cx in range(int(math.floor(min(xa, xb) / Z)), int(math.floor(max(xa, xb) / Z)) + 1):
            for cy in range(int(math.floor(min(ya, yb) / Z)), int(math.floor(max(ya, yb) / Z)) + 1):
                zell.setdefault((cx, cy), []).append(si)
    vorschlag = []
    for i in enden:
        x, y = pkt[i]
        cx, cy = int(math.floor(x / Z)), int(math.floor(y / Z))
        bd, bs, bp = None, None, None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for si in zell.get((cx + dx, cy + dy), ()):
                    ei, j, a, b = segs[si]
                    if uf.f(a) == uf.f(i):
                        continue
                    xa, ya = pkt[a]
                    xb, yb = pkt[b]
                    vx, vy = xb - xa, yb - ya
                    ll = vx * vx + vy * vy
                    t = 0.0 if ll == 0 else max(0.0, min(1.0, ((x - xa) * vx + (y - ya) * vy) / ll))
                    px, py = xa + t * vx, ya + t * vy
                    d = math.hypot(px - x, py - y)
                    if d <= BRUECKE and (bd is None or d < bd):
                        bd, bs, bp = d, si, (round(px, 1), round(py, 1), t)
        if bd is not None:
            vorschlag.append((bd, i, bs, bp))
    vorschlag.sort()
    teil = {}   # Kante -> Liste (j, t, Punkt) zum Teilen
    bruecken = []
    for d, i, si, (px, py, t) in vorschlag:
        ei, j, a, b = segs[si]
        if uf.f(a) == uf.f(i):
            continue                                       # inzwischen schon verbunden
        if t <= 0.0 or (t < 1.0 and math.hypot(px - pkt[a][0], py - pkt[a][1]) < 2.0):
            tp = a
        elif t >= 1.0 or math.hypot(px - pkt[b][0], py - pkt[b][1]) < 2.0:
            tp = b
        else:
            pkt.append((px, py))
            tp = len(pkt) - 1
            teil.setdefault(ei, []).append((j, t, tp))
        bruecken.append([i, tp])
        uf.u(i, tp)
    if teil:
        neu = []
        for ei, e in enumerate(kan):
            if ei not in teil:
                neu.append(e)
                continue
            # Kante an den neuen Punkten teilen (nach Lage sortiert)
            ins = sorted(teil[ei])
            punkte = []
            k = 0
            for j in range(len(e)):
                punkte.append(e[j])
                while k < len(ins) and ins[k][0] == j:
                    punkte.append(ins[k][2])
                    k += 1
            schnitte = {tp for _, _, tp in ins}
            cur = [punkte[0]]
            for q in punkte[1:]:
                cur.append(q)
                if q in schnitte:
                    neu.append(cur)
                    cur = [q]
            if len(cur) > 1:
                neu.append(cur)
        kan = neu
    kan += bruecken
    st["bruecken"] = len(bruecken)
    bl = [_laenge_e(pkt, e) for e in bruecken]
    st["bruecken_yards_summe"] = round(sum(bl))
    st["bruecken_yards_max"] = round(max(bl or [0]), 1)
    st["yards_2_mit_bruecken"] = L(kan)
    # 3) kleine Teile weg
    uf = _UF()
    for e in kan:
        for a, b in zip(e, e[1:]):
            uf.u(a, b)
    teil_l = {}
    for e in kan:
        r = uf.f(e[0])
        teil_l[r] = teil_l.get(r, 0.0) + _laenge_e(pkt, e)
    weg = {r for r, l in teil_l.items() if l < MIN_NETZ}
    st["teile_vorher"] = len(teil_l)
    st["kleine_teile_weg"] = len(weg)
    st["kleine_teile_yards"] = round(sum(teil_l[r] for r in weg))
    kan = [e for e in kan if uf.f(e[0]) not in weg]
    st["yards_3_ohne_kleine_teile"] = L(kan)
    # 4) kurze Endstummel weg, dann Grad 2 zusammenlegen (bis nichts mehr geht)
    for _ in range(3):
        g = _grade(kan)
        kan = [e for e in kan if not ((g[e[0]] == 1 or g[e[-1]] == 1) and not (g[e[0]] == 1 and g[e[-1]] == 1)
                                      and _laenge_e(pkt, e) < MIN_KANTE)]
    st["yards_4_ohne_stummel"] = L(kan)
    # Ketten über Knoten mit Grad 2 zu einer Kante zusammenlegen
    g = _grade(kan)
    an = {}
    for ei, e in enumerate(kan):
        an.setdefault(e[0], []).append(ei)
        if e[-1] != e[0]:
            an.setdefault(e[-1], []).append(ei)
        else:
            an[e[0]].append(ei)
    benutzt = [False] * len(kan)
    neu = []
    zusammen = 0

    def weiter(v, ei):
        e = kan[ei]
        return e if e[0] == v else e[::-1]

    for v, liste in an.items():
        if g.get(v) == 2:
            continue
        for ei in liste:
            if benutzt[ei]:
                continue
            benutzt[ei] = True
            kette = weiter(v, ei)
            while g.get(kette[-1]) == 2 and kette[-1] != v:
                n = [x for x in an[kette[-1]] if not benutzt[x]]
                if not n:
                    break
                benutzt[n[0]] = True
                kette = kette + weiter(kette[-1], n[0])[1:]
                zusammen += 1
            neu.append(kette)
    for ei, e in enumerate(kan):                         # Ringe nur aus Grad-2-Knoten
        if not benutzt[ei]:
            benutzt[ei] = True
            v = e[0]
            kette = list(e)
            while kette[-1] != v:
                n = [x for x in an[kette[-1]] if not benutzt[x]]
                if not n:
                    break
                benutzt[n[0]] = True
                kette = kette + weiter(kette[-1], n[0])[1:]
                zusammen += 1
            neu.append(kette)
    kan = neu
    st["grad2_zusammengelegt"] = zusammen
    # neu nummerieren (nur benutzte Punkte)
    idx, pk2 = {}, []
    kan2 = []
    for e in kan:
        r = []
        for i in e:
            if i not in idx:
                idx[i] = len(pk2)
                pk2.append(pkt[i])
            r.append(idx[i])
        kan2.append(r)
    g = _grade(kan2)
    st["knoten"] = len(g)
    st["grad1"] = sum(1 for d in g.values() if d == 1)
    st["grad2_rest"] = sum(1 for d in g.values() if d == 2)
    uf = _UF()
    for e in kan2:
        for a, b in zip(e, e[1:]):
            uf.u(a, b)
    st["teile"] = len({uf.f(e[0]) for e in kan2})
    return pk2, kan2, st


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
        pkt, kan, zellen, st = netz(karte)
        netze[m] = (pkt, kan)
        stat[m] = {"punkte": len(pkt), "kanten": len(kan),
                   "km_yards": round(sum(laenge([pkt[i] for i in e]) for e in kan)), "zellen_nach_filter": zellen, "verdichten": st}
    os.makedirs(outdir, exist_ok=True)
    json.dump({"client": d["client"], "stat": stat, "karten": {m: {"p": p, "e": e} for m, (p, e) in netze.items()}},
              open(os.path.join(outdir, "strassen_netz.json"), "w"), separators=(",", ":"))
    open(os.path.join(outdir, "GoldSentinelStrassen.lua"), "w", encoding="utf-8").write(lua(netze, d))
    print(json.dumps(stat))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
