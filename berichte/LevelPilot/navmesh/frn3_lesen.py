#!/usr/bin/env python3
"""Eigener Leser fuer FRN3-Bloecke (Forever Route Lab, GPL-3, abgeleitete Daten aus Client 1.60.1.70124).
Nur Messung: Anzahl Ecken, Polygone, Zonen, Bytes je Kontinent. Aufruf: frn3_lesen.py <public/nav>"""
import sys, os, glob

class R:
    def __init__(s, b): s.b, s.p = b, 0
    def byte(s):
        v = s.b[s.p]; s.p += 1; return v
    def u(s):
        v, m = 0, 1
        for i in range(8):
            x = s.byte(); v += (x % 128) * m
            if x < 128:
                if i > 0 and x == 0: raise ValueError("varint")
                return v
            m *= 128
        raise ValueError("varint lang")
    def z(s):
        v = s.u(); return v // 2 if v % 2 == 0 else -(v + 1) // 2

def block(b):
    r = R(b)
    assert b[:4] == b"FRN3" and b[4] == 3; r.p = 5
    mid, row0, col0 = r.u(), r.u(), r.u(); r.z()
    tiles = r.u(); nvs = nps = slots = swim = 0; kmax = 0
    for _ in range(tiles):
        r.u(); r.u(); r.z(); nv, np_ = r.u(), r.u()
        for _ in range(nv): r.z(); r.z(); r.z()
        for _ in range(np_):
            h = r.byte(); k = h // 2 + 3; swim += h % 2; kmax = max(kmax, k)
            for _ in range(k): r.z()
            slots += k
        nvs += nv; nps += np_
    assert r.byte() == 3
    zc = r.u(); zones = [r.u() for _ in range(zc)]
    for _ in range(tiles):
        n = r.u(); [r.u() for _ in range(n)]
    # Polygon-Zonen-Indizes folgen; Rest nicht gebraucht fuer die Zaehlung
    return dict(map=mid, tiles=tiles, verts=nvs, polys=nps, slots=slots, swim=swim, kmax=kmax, zones=zones)

if __name__ == "__main__":
    root = sys.argv[1]
    for m in ("0", "1"):
        T = dict(files=0, bytes=0, tiles=0, verts=0, polys=0, slots=0, swim=0, kmax=0); Z = set()
        for f in sorted(glob.glob(os.path.join(root, m, "*_*.bin"))):
            b = open(f, "rb").read(); d = block(b)
            T["files"] += 1; T["bytes"] += len(b)
            for k in ("tiles", "verts", "polys", "slots", "swim"): T[k] += d[k]
            T["kmax"] = max(T["kmax"], d["kmax"]); Z.update(d["zones"])
        mb = os.path.getsize(os.path.join(root, m, "map.bin"))
        print(f"Karte {m}: Bloecke {T['files']} Bytes {T['bytes']} (+map.bin {mb}) Kacheln {T['tiles']} Ecken {T['verts']} "
              f"Polygone {T['polys']} Eckplaetze {T['slots']} Schwimm {T['swim']} max.Ecken/Poly {T['kmax']} Zonen {len(Z)}")
