"""Rohauszug aus dem WoW-Client – Supervisor GoldSentinel, 16.11.2026 17:40 (Auftrag des Nutzers: "hol dir alles raus, und zwar
jetzt – nachher steht dir der Ordner nicht mehr zur Verfügung; lieber zu viel als zu wenig").

Liest aus dem CASC-Speicher (nur lesen) und legt die entpackten Dateien als <out>/<produkt>/f/<FileDataID> ab:
  1. WDT der Kontinente (Karte 0 Östliche Königreiche, 1 Kalimdor) und je Kachel ALLE Dateien aus MAID
     (root-ADT mit Höhen/Wasser/Gebieten, obj0/obj1 mit Gebäuden und Objekten, tex0, lod, Kartentexturen, Minikarte).
  2. Alle Gebäude (WMO, aus MODF in obj0/obj1 bzw. root) samt Gruppen-Dateien (GFID) – Wände, Böden, Höhlen.
  3. Alle Objekte (M2, aus MDDF) – Kollision (Bäume, Felsen, Zäune).
  4. Alle Spieldaten-Tabellen (DB2) laut Community-Listfile.
Namen (MWMO/MMDX) werden über die Listfile auf FileDataIDs abgebildet. Ein Index (index.json) hält fest, was gelesen wurde und
was fehlte. Ein Lauf kann abbrechen und neu starten: schon vorhandene Dateien werden übersprungen.
Aufruf: python3 rohauszug.py <WoW-Ordner> <ausgabe> <produkt> <listfile.csv>
"""
import json
import os
import struct
import sys
import time

import casc_lesen
import kacheln

KARTEN = {0: 775971, 1: 782779}


def lade_listfile(pfad):
    name2id, db2 = {}, []
    with open(pfad, encoding="utf-8", errors="replace") as f:
        for z in f:
            z = z.strip()
            if ";" not in z:
                continue
            i, n = z.split(";", 1)
            try:
                i = int(i)
            except ValueError:
                continue
            n = n.lower().replace("\\", "/")
            if n.endswith((".wmo", ".m2", ".mdx", ".mdl")):
                name2id[n] = i
                if n.endswith((".mdx", ".mdl")):
                    name2id[n[:-4] + ".m2"] = i
            elif n.startswith("dbfilesclient/") and n.endswith(".db2"):
                db2.append(i)
    return name2id, db2


class Auszug:
    def __init__(self, wow, out, produkt, listfile):
        self.c = casc_lesen.Casc(wow, produkt)
        self.dir = os.path.join(out, produkt, "f")
        os.makedirs(self.dir, exist_ok=True)
        self.idx_pfad = os.path.join(out, produkt, "index.json")
        self.idx = {"client": self.c.version, "produkt": produkt, "gelesen": 0, "fehlend": [], "namen_ohne_id": [],
                    "karten": {}, "wmo": [], "m2": [], "db2": []}
        self.name2id, self.db2 = lade_listfile(listfile)
        self.t0 = time.time()

    def hole(self, fid):
        if not fid:
            return None
        p = os.path.join(self.dir, str(fid))
        if os.path.exists(p):
            with open(p, "rb") as f:
                return f.read()
        try:
            d = self.c.read_fdid(fid)
        except Exception as e:                       # CascFehler, fehlende Archive, verschlüsselte Dateien
            self.idx["fehlend"].append([fid, str(e)[:80]])
            return None
        with open(p + ".tmp", "wb") as f:
            f.write(d)
        os.replace(p + ".tmp", p)
        self.idx["gelesen"] += 1
        if self.idx["gelesen"] % 500 == 0:
            self.speichern()
            print("…", self.idx["gelesen"], "Dateien, %.0fs" % (time.time() - self.t0), flush=True)
        return d

    def speichern(self):
        with open(self.idx_pfad + ".tmp", "w") as f:
            json.dump(self.idx, f)
        os.replace(self.idx_pfad + ".tmp", self.idx_pfad)

    @staticmethod
    def namen(d, p, size):
        out, roh = {}, d[p:p + size]
        s = 0
        while s < len(roh):
            e = roh.find(b"\0", s)
            if e < 0:
                e = len(roh)
            out[s] = roh[s:e].decode("latin-1").lower().replace("\\", "/")
            s = e + 1
        return out

    def platzierungen(self, d, wmos, m2s):
        mwmo = mmdx = {}
        mwid, mmid = [], []
        for tag, p, size in kacheln.chunks(d):
            if tag == "MWMO":
                mwmo = self.namen(d, p, size)
            elif tag == "MMDX":
                mmdx = self.namen(d, p, size)
            elif tag == "MWID":
                mwid = list(struct.unpack("<%dI" % (size // 4), d[p:p + size]))
            elif tag == "MMID":
                mmid = list(struct.unpack("<%dI" % (size // 4), d[p:p + size]))
        for tag, p, size in kacheln.chunks(d):
            if tag == "MODF":
                for i in range(size // 64):
                    nid = struct.unpack("<I", d[p + i * 64:p + i * 64 + 4])[0]
                    flags = struct.unpack("<H", d[p + i * 64 + 56:p + i * 64 + 58])[0]
                    self.ziel(nid, flags & 0x8, mwid, mwmo, wmos)
            elif tag == "MDDF":
                for i in range(size // 36):
                    nid = struct.unpack("<I", d[p + i * 36:p + i * 36 + 4])[0]
                    flags = struct.unpack("<H", d[p + i * 36 + 34:p + i * 36 + 36])[0]
                    self.ziel(nid, flags & 0x40, mmid, mmdx, m2s)

    def ziel(self, nid, ist_fdid, ids, namen, menge):
        if ist_fdid:
            menge.add(nid)
            return
        if nid < len(ids) and ids[nid] in namen:
            n = namen[ids[nid]]
            fid = self.name2id.get(n)
            if fid:
                menge.add(fid)
            elif len(self.idx["namen_ohne_id"]) < 5000:
                self.idx["namen_ohne_id"].append(n)

    def lauf(self):
        wmos, m2s = set(), set()
        for m, wdt in KARTEN.items():
            d = self.hole(wdt)
            kachel = {}
            for tag, p, size in kacheln.chunks(d):
                if tag == "MAID":
                    for i in range(4096):
                        vals = struct.unpack("<8I", d[p + i * 32:p + i * 32 + 32])
                        if any(vals):
                            kachel["%d_%d" % (i // 64, i % 64)] = list(vals)
                elif tag == "MODF":                   # WMO-only-Karte (hier nicht der Fall, aber vollständig)
                    pass
            self.idx["karten"][str(m)] = {"wdt": wdt, "kacheln": kachel}
            for k, vals in sorted(kachel.items()):
                for slot, fid in enumerate(vals):
                    dd = self.hole(fid)
                    if dd is not None and slot in (0, 1, 2):          # root, obj0, obj1 -> Platzierungen
                        try:
                            self.platzierungen(dd, wmos, m2s)
                        except Exception as e:
                            self.idx["fehlend"].append([fid, "platz " + str(e)[:60]])
            self.speichern()
            print("Karte", m, "fertig:", len(kachel), "Kacheln, WMO", len(wmos), "M2", len(m2s), flush=True)
        # Gebäude samt Gruppen
        for w in sorted(wmos):
            d = self.hole(w)
            if d is None:
                continue
            for tag, p, size in kacheln.chunks(d):
                if tag == "GFID":
                    for g in struct.unpack("<%dI" % (size // 4), d[p:p + size]):
                        self.hole(g)
        self.idx["wmo"] = sorted(wmos)
        self.speichern()
        print("WMO fertig", len(wmos), flush=True)
        for m in sorted(m2s):
            self.hole(m)
        self.idx["m2"] = sorted(m2s)
        self.speichern()
        print("M2 fertig", len(m2s), flush=True)
        ok = []
        for fid in self.db2:
            if self.hole(fid) is not None:
                ok.append(fid)
        self.idx["db2"] = ok
        self.speichern()
        print("FERTIG %.0fs" % (time.time() - self.t0), "gelesen", self.idx["gelesen"], "fehlend", len(self.idx["fehlend"]),
              flush=True)


if __name__ == "__main__":
    Auszug(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]).lauf()
