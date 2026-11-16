"""Strassen-Masken aus den Forever-Geländekacheln – Supervisor GoldSentinel, 16.11.2026 (Auftrag des Nutzers 08:01).

Schritt 2: Für jede tex0-Kachel jedes Kartenstück (MCNK) mit einer Strassen-Textur (strassen_texturen.json) lesen, die
Alpha-Karte (MCAL) der Strassen-Schicht entpacken und auf ein Raster von 4×4 Bildpunkten verdichten (16×16 Zellen je
Kartenstück, 1 Zelle = 33,333/16 = 2,083 Yards). Eine Zelle gilt als Strasse, wenn der Mittelwert der Alpha-Werte
>= SCHWELLE ist. Liegt die Strasse in Schicht 0 (ohne Alpha), gilt 255 minus die Summe der übrigen Schichten.

Ausgabe (JSON): {"karten": {"0": {"y_x": {"c": {"<Stück 0..255>": "<64 Hex-Zeichen = 256 Bit, Zeile für Zeile>"}}}}}
Weltkoordinaten (WoW): X = 17066,666 − (ty·533,333 + zeile·33,333 + zy·2,083 + 1,042)
                        Y = 17066,666 − (tx·533,333 + spalte·33,333 + zx·2,083 + 1,042)
Nur lesen; nichts an der Installation ändern.
"""
import json
import sys
import time

import casc_lesen
import kacheln

SCHWELLE = 128
ZELLE = 4                 # Bildpunkte je Zellenseite (64/4 = 16 Zellen)


def alpha_entpacken(mcal, off, flags, gross):
    """-> 4096 Werte (0..255) einer Schicht."""
    if flags & 0x200:                                   # komprimiert (RLE), immer 4096 Werte
        out = bytearray()
        p = off
        while len(out) < 4096 and p < len(mcal):
            b = mcal[p]
            p += 1
            n = b & 0x7F
            if b & 0x80:                                # füllen
                out += bytes([mcal[p]]) * n
                p += 1
            else:                                       # kopieren
                out += mcal[p:p + n]
                p += n
        return bytes(out[:4096]).ljust(4096, b"\0")
    if gross:
        return bytes(mcal[off:off + 4096]).ljust(4096, b"\0")
    raw = mcal[off:off + 2048]                          # 4 Bit je Wert
    out = bytearray(4096)
    for i, b in enumerate(raw):
        out[2 * i] = (b & 0x0F) * 17
        out[2 * i + 1] = (b >> 4) * 17
    return bytes(out)


def verdichten(a):
    """4096 Alpha-Werte -> 256 Bit (16×16 Zellen) als int."""
    bits = 0
    for zy in range(16):
        for zx in range(16):
            s = 0
            for dy in range(ZELLE):
                row = (zy * ZELLE + dy) * 64 + zx * ZELLE
                s += a[row] + a[row + 1] + a[row + 2] + a[row + 3]
            if s >= SCHWELLE * ZELLE * ZELLE:
                bits |= 1 << (zy * 16 + zx)
    return bits


def main(wow_dir, texturen, out):
    strasse = set(e["fdid"] for e in json.load(open(texturen, encoding="utf-8"))["strasse"])
    c = casc_lesen.Casc(wow_dir)
    t0 = time.time()
    res, info = {}, {}
    for m, fid in kacheln.WDT.items():
        flags, tiles = kacheln.wdt_tiles(c, fid)
        gross = bool(flags & 0x84)                      # 0x4 grosse Alpha-Karten, 0x80 Höhen-Texturierung
        karte, n_st, n_z = {}, 0, 0
        for (ty, tx), tfid in sorted(tiles.items()):
            try:
                d = c.read_fdid(tfid)
            except casc_lesen.CascFehler:
                continue
            mdid, mcnks = kacheln.tex0_layers(d)
            st = {}
            for i, (layers, mcal) in enumerate(mcnks):
                ist = [k for k, (tid, fl, off) in enumerate(layers) if tid < len(mdid) and mdid[tid] in strasse]
                if not ist:
                    continue
                alphas = [None] * len(layers)
                for k, (tid, fl, off) in enumerate(layers):
                    if k > 0 and fl & 0x100:
                        alphas[k] = alpha_entpacken(mcal, off, fl, gross)
                summe = None
                for k in ist:
                    if k == 0:
                        rest = bytearray(4096)
                        for j in range(4096):
                            v = 255 - sum(alphas[q][j] for q in range(1, len(layers)) if alphas[q])
                            rest[j] = v if v > 0 else 0
                        a = rest
                    else:
                        a = alphas[k]
                    if a is None:
                        continue
                    summe = bytearray(a) if summe is None else bytearray(min(255, x + y) for x, y in zip(summe, a))
                if summe is None:
                    continue
                bits = verdichten(summe)
                if bits:
                    st[str(i)] = "%064x" % bits
                    n_st += 1
                    n_z += bin(bits).count("1")
            if st:
                karte["%d_%d" % (ty, tx)] = {"c": st}
        res[str(m)] = karte
        info[str(m)] = {"kacheln_mit_strasse": len(karte), "stuecke": n_st, "zellen": n_z}
    json.dump({"version": 1, "zelle_yd": 33.3333 / 16, "schwelle": SCHWELLE, "client": c.version,
               "info": info, "karten": res}, open(out, "w"), separators=(",", ":"))
    print("fertig %.1fs" % (time.time() - t0), info)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
