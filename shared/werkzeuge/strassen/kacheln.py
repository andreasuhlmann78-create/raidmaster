"""Geländekacheln (ADT tex0) von WoW Forever lesen – Supervisor GoldSentinel, 16.11.2026 (Auftrag des Nutzers 08:01).

Schritt 1 (dieses Skript, Modus "zaehlen"): je Kontinent (Karte 0 Östliche Königreiche, 1 Kalimdor) die WDT lesen, alle tex0-Kacheln
öffnen und zählen, wie oft jede Bodentextur (FileDataID aus MDID) in einem Kartenstück (MCNK) als Schicht vorkommt.
Ausgabe: textur_nutzung.json – daraus werden die Strassen-Texturen ausgewählt (Namen aus der Community-Listfile, geprüft).
Nur lesen; nichts an der Installation ändern.
"""
import json
import struct
import sys
import time

import casc_lesen

WDT = {0: 775971, 1: 782779}     # Map.db2 (wago.tools, Zweig wowf): Azeroth, Kalimdor


def chunks(d, start=0, end=None):
    end = len(d) if end is None else end
    p = start
    while p + 8 <= end:
        tag = d[p:p + 4][::-1].decode("latin-1")
        size = struct.unpack("<I", d[p + 4:p + 8])[0]
        yield tag, p + 8, size
        p += 8 + size


def wdt_tiles(c, fid):
    d = c.read_fdid(fid)
    flags, tiles = 0, {}
    for tag, p, size in chunks(d):
        if tag == "MPHD":
            flags = struct.unpack("<I", d[p:p + 4])[0]
        elif tag == "MAID":
            for i in range(4096):
                vals = struct.unpack("<8I", d[p + i * 32:p + i * 32 + 32])
                if vals[3]:
                    tiles[(i // 64, i % 64)] = vals[3]          # (y, x) -> tex0
    return flags, tiles


def tex0_layers(d):
    """-> (Liste MDID-FileDataIDs, Liste je MCNK: [(textureIndex, flags, alphaOffset)], Liste MCAL-Bytes je MCNK)"""
    mdid, mcnks = [], []
    for tag, p, size in chunks(d):
        if tag == "MDID":
            mdid = list(struct.unpack("<%dI" % (size // 4), d[p:p + size]))
        elif tag == "MCNK":
            layers, mcal = [], b""
            for st, sp, ss in chunks(d, p, p + size):
                if st == "MCLY":
                    for i in range(ss // 16):
                        tid, fl, off, eff = struct.unpack("<IIIi", d[sp + 16 * i:sp + 16 * i + 16])
                        layers.append((tid, fl, off))
                elif st == "MCAL":
                    mcal = d[sp:sp + ss]
            mcnks.append((layers, mcal))
    return mdid, mcnks


def main(wow_dir, out):
    c = casc_lesen.Casc(wow_dir)
    t0 = time.time()
    use = {}
    info = {}
    for m, fid in WDT.items():
        flags, tiles = wdt_tiles(c, fid)
        info[m] = {"mphd": flags, "kacheln": len(tiles)}
        miss = 0
        for (ty, tx), tfid in tiles.items():
            try:
                d = c.read_fdid(tfid)
            except casc_lesen.CascFehler:
                miss += 1
                continue
            mdid, mcnks = tex0_layers(d)
            for layers, _ in mcnks:
                for tid, fl, off in layers:
                    if tid < len(mdid):
                        k = mdid[tid]
                        use[k] = use.get(k, 0) + 1
        info[m]["fehlend"] = miss
    json.dump({"info": info, "nutzung": use}, open(out, "w"))
    print("fertig %.1fs" % (time.time() - t0), info, "Texturen", len(use))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
