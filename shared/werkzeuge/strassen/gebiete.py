"""Gebiets-Karte (Unterzonen) aus den Geländekacheln – Supervisor GoldSentinel, 16.11.2026 (Auftrag des Nutzers 17:30/17:31:
"Städte und Dörfer, wo man Quests annehmen kann, Stück für Stück beurteilen – nicht einfach 1760 Yards").

Liest je Kontinent (Karte 0/1) die ROOT-ADT jeder Kachel (MAID Index 0) und daraus je Kartenstück (MCNK, 33,3 yd) die AreaTable-ID
(MCNK-Kopf Offset 0x34). Ergebnis: 16×16 Gebiets-IDs je Kachel – damit lässt sich für jeden Punkt (NPC, Questziel) exakt sagen, in
welchem Ort/Unterzone er liegt (z. B. Nordhain-Tal vs. Goldhain), ganz ohne Radius-Schätzung.
Ausgabe JSON: {"client":..., "karten": {"0": {"y_x": [256 Area-IDs, Zeile für Zeile]}}}
Aufruf: python3 gebiete.py <WoW-Ordner> <ausgabe.json> [produkt]   (produkt: wowf | wow_classic_era | wow_anniversary)
Nur lesen; nichts an der Installation ändern.
"""
import json
import struct
import sys
import time

import casc_lesen
import kacheln


def wdt_roots(c, fid):
    d = c.read_fdid(fid)
    roots = {}
    for tag, p, size in kacheln.chunks(d):
        if tag == "MAID":
            for i in range(4096):
                vals = struct.unpack("<8I", d[p + i * 32:p + i * 32 + 32])
                if vals[0]:
                    roots[(i // 64, i % 64)] = vals[0]          # (y, x) -> root ADT
    return roots


def areas(d):
    out = []
    for tag, p, size in kacheln.chunks(d):
        if tag == "MCNK":
            out.append(struct.unpack("<I", d[p + 0x34:p + 0x38])[0])
    return out


def main(wow_dir, out, product="wowf"):
    c = casc_lesen.Casc(wow_dir, product)
    t0 = time.time()
    res, info = {}, {}
    for m, fid in kacheln.WDT.items():
        roots = wdt_roots(c, fid)
        karte, fehl = {}, 0
        for (ty, tx), rfid in sorted(roots.items()):
            try:
                a = areas(c.read_fdid(rfid))
            except casc_lesen.CascFehler:
                fehl += 1
                continue
            if len(a) == 256:
                karte["%d_%d" % (ty, tx)] = a
        res[str(m)] = karte
        info[str(m)] = {"kacheln": len(karte), "fehlend": fehl, "gebiete": len({x for v in karte.values() for x in v})}
    json.dump({"version": 1, "client": c.version, "info": info, "karten": res}, open(out, "w"), separators=(",", ":"))
    print("fertig %.1fs" % (time.time() - t0), info)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "wowf")
