"""Gelände-Karte aus den Rohdaten des Clients – Supervisor GoldSentinel, 16.11.2026 (Auftrag des Nutzers 17:35/17:40: optimale
Questroute über die ganze Welt; dafür muss bekannt sein, wo man laufen kann).

Liest die mit rohauszug.py ausgezogenen Dateien (<roh>/<produkt>/f/<FileDataID> + index.json) und schreibt kleine, abgeleitete
Daten (KEINE Spieldateien):
  gelaende_<produkt>_<karte>.bin.gz – je Kachel 256 Kartenstücke × 64 Zellen (4,17 yd) je 1 Byte:
      Bit 0–4  Steigung in 3°-Stufen (0 = flach … 30 = 90°), grösste Steigung der Zelle (Ecken gegen Mitte, MCVT)
      Bit 5    Loch im Boden (Höhlen-/Gebäudeeingang; MCNK holes, hoch- oder niedrig aufgelöst)
      Bit 6–7  Wasser (MH2O): 0 keins, 1 seicht (< 1,5 yd über Boden), 2 tief (schwimmen), 3 Lava/Schleim (Gefahr)
    Aufbau: Kopf "GSG1", uint16 Anzahl Kacheln, dann je Kachel uint8 ty, uint8 tx, 16384 Byte Zellen, 256 × int16 Bodenhöhe
    (Mittel des Kartenstücks, gerundet auf 1 yd).
  objekte_<produkt>_<karte>.json.gz – Gebäude (WMO: FileDataID, Weltpunkt, Hülle min/max) und Objekte (M2: FileDataID, Weltpunkt,
    Massstab) aus obj0/obj1 (MODF/MDDF), doppelte (gleiche uniqueId) nur einmal.
Weltkoordinaten wie im Spiel: X = Nord, Y = West, Z = Höhe (17066,67 − Kachel × 533,33 …).
Aufruf: python3 gelaende.py <roh> <ausgabe-ordner> [produkt ...]     (Standard: wowf wow_classic_era)
Prüfungen beim Lauf: Zellen gezählt je Kachel, fehlende Kacheln je Karte (aus index.json) – Ausgabe als Zusammenfassung.
"""
import gzip
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kacheln                                     # noqa: E402

O = 17066.666666
T = 533.333333
STUECK = T / 16
ZELLE = STUECK / 8
GEFAHR = {3, 4, 7, 8, 11, 12, 19, 20, 21}         # Lava/Schleim-Arten (LiquidType ≥ 3 und Abarten; Verdacht, gegen LiquidType.db2 prüfen)


def vertex(h, r, c, innen=False):
    return h[r * 17 + 9 + c] if innen else h[r * 17 + c]


def zellen_eines_stuecks(d, p, size, wasser):
    hdr = d[p:p + 128]
    flags = struct.unpack("<I", hdr[0:4])[0]
    basis = struct.unpack("<3f", hdr[0x68:0x74])[2]
    if flags & 0x10000:
        loch = struct.unpack("<Q", hdr[0x14:0x1C])[0]
        loecher = [(loch >> i) & 1 for i in range(64)]
    else:
        l16 = struct.unpack("<H", hdr[0x3C:0x3E])[0]
        loecher = [(l16 >> ((r // 2) * 4 + (c // 2))) & 1 for r in range(8) for c in range(8)]
    h = None
    for tag, q, s in kacheln.chunks(d, p + 128, p + size):
        if tag == "MCVT" and s >= 580:
            h = struct.unpack("<145f", d[q:q + 580])
    out = bytearray(64)
    if h is None:
        return out, int(round(basis))
    halb = ZELLE * math.sqrt(0.5)
    for r in range(8):
        for c in range(8):
            m = vertex(h, r, c, True)
            st = 0.0
            for (rr, cc) in ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)):
                st = max(st, abs(vertex(h, rr, cc) - m) / halb)
            stufe = min(30, int(round(math.degrees(math.atan(st)) / 3)))
            b = stufe | (loecher[r * 8 + c] << 5)
            w = wasser.get((r, c))
            if w:
                art, oben = w
                if art in GEFAHR:
                    b |= 3 << 6
                else:
                    b |= (2 if oben - (basis + m) >= 1.5 else 1) << 6
            out[r * 8 + c] = b
    mittel = basis + sum(h) / 145.0
    return out, int(round(mittel))


def wasser_der_kachel(d):
    res = {}
    for tag, p, size in kacheln.chunks(d):
        if tag != "MH2O":
            continue
        for i in range(256):
            oi, n, _oa = struct.unpack("<3I", d[p + i * 12:p + i * 12 + 12])
            if not n or not oi:
                continue
            zellen = {}
            for k in range(n):
                q = p + oi + k * 24
                art, _lvf, lo, hi, xo, yo, w, hgt, oex, _ov = struct.unpack("<HHffBBBBII", d[q:q + 24])
                bits = None
                if oex:
                    nb = (w * hgt + 7) // 8
                    bits = int.from_bytes(d[p + oex:p + oex + nb], "little")
                for yy in range(hgt):
                    for xx in range(w):
                        j = yy * w + xx
                        if bits is not None and not (bits >> j) & 1:
                            continue
                        key = (yo + yy, xo + xx)
                        alt = zellen.get(key)
                        if alt is None or hi > alt[1]:
                            zellen[key] = (art, hi)
            res[i] = zellen
    return res


def objekte(d, wmo, m2):
    for tag, p, size in kacheln.chunks(d):
        if tag == "MODF":
            for i in range(size // 64):
                q = p + i * 64
                nid, uid = struct.unpack("<II", d[q:q + 8])
                px, py, pz = struct.unpack("<3f", d[q + 8:q + 20])
                lo = struct.unpack("<3f", d[q + 32:q + 44])
                hi = struct.unpack("<3f", d[q + 44:q + 56])
                if uid not in wmo:
                    wmo[uid] = [nid, round(O - pz, 1), round(O - px, 1), round(py, 1),
                                [round(O - hi[2], 1), round(O - hi[0], 1), round(lo[1], 1)],
                                [round(O - lo[2], 1), round(O - lo[0], 1), round(hi[1], 1)]]
        elif tag == "MDDF":
            for i in range(size // 36):
                q = p + i * 36
                nid, uid = struct.unpack("<II", d[q:q + 8])
                px, py, pz = struct.unpack("<3f", d[q + 8:q + 20])
                sc = struct.unpack("<H", d[q + 32:q + 34])[0]
                if uid not in m2:
                    m2[uid] = [nid, round(O - pz, 1), round(O - px, 1), round(py, 1), sc]


def lies(pfad):
    try:
        with open(pfad, "rb") as f:
            return f.read()
    except OSError:
        return None


def main(roh, aus, produkte):
    os.makedirs(aus, exist_ok=True)
    zusammen = {}
    for prod in produkte:
        basis = os.path.join(roh, prod)
        ix = json.load(open(os.path.join(basis, "index.json")))
        for m, kd in ix["karten"].items():
            kach = kd["kacheln"]
            blob = bytearray(b"GSG1")
            teile, fehlend, zaehler = [], [], {"steil": 0, "loch": 0, "wasser_tief": 0, "gefahr": 0, "zellen": 0}
            wmo, m2 = {}, {}
            for k, vals in sorted(kach.items(), key=lambda kv: tuple(map(int, kv[0].split("_")))):
                ty, tx = map(int, k.split("_"))
                d = lies(os.path.join(basis, "f", str(vals[0])))
                if d is None:
                    fehlend.append(k)
                    continue
                wasser = wasser_der_kachel(d)
                zell, hoehen = bytearray(), []
                n = 0
                for tag, p, size in kacheln.chunks(d):
                    if tag == "MCNK":
                        z, hm = zellen_eines_stuecks(d, p, size, wasser.get(n, {}))
                        zell += z
                        hoehen.append(max(-32768, min(32767, hm)))
                        n += 1
                if n != 256:
                    fehlend.append(k + ":mcnk%d" % n)
                    continue
                for b in zell:
                    zaehler["zellen"] += 1
                    zaehler["steil"] += (b & 31) >= 17          # ≥ 51°
                    zaehler["loch"] += (b >> 5) & 1
                    zaehler["wasser_tief"] += (b >> 6) == 2
                    zaehler["gefahr"] += (b >> 6) == 3
                teile.append(struct.pack("<BB", ty, tx) + bytes(zell) + struct.pack("<256h", *hoehen))
                for slot in (1, 2):
                    dd = lies(os.path.join(basis, "f", str(vals[slot]))) if vals[slot] else None
                    if dd:
                        objekte(dd, wmo, m2)
            blob += struct.pack("<H", len(teile)) + b"".join(teile)
            with gzip.open(os.path.join(aus, "gelaende_%s_%s.bin.gz" % (prod, m)), "wb", 9) as f:
                f.write(blob)
            with gzip.open(os.path.join(aus, "objekte_%s_%s.json.gz" % (prod, m)), "wt", 9) as f:
                json.dump({"client": ix.get("client"), "karte": int(m), "wmo": list(wmo.values()), "m2": list(m2.values())},
                          f, separators=(",", ":"))
            zusammen["%s/%s" % (prod, m)] = {"kacheln_gesamt": len(kach), "kacheln_fertig": len(teile),
                                             "fehlend": len(fehlend), "wmo": len(wmo), "m2": len(m2), **zaehler}
            print(prod, m, zusammen["%s/%s" % (prod, m)], flush=True)
    with open(os.path.join(aus, "gelaende_stand.json"), "w") as f:
        json.dump(zusammen, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:] or ["wowf", "wow_classic_era"])
