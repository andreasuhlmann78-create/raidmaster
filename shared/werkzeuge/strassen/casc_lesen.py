"""Eigener, kleiner CASC-Leser (nur lesen) für die lokale WoW-Installation – Supervisor GoldSentinel, 16.11.2026.

Zweck: Geländedaten (WDT/ADT) von WoW Forever lesen, um daraus Strassen für LevelPilot zu gewinnen
(Auftrag des Nutzers 16.11. 08:01). Formatbeschreibung: wowdev.wiki (CASC, BLTE, Encoding, Root, Index).
Ändert NICHTS an der Installation (öffnet alle Dateien nur zum Lesen).

Aufbau: .build.info -> Build-Config -> Encoding (CKey -> EKey) und Root (FileDataID -> CKey) ->
lokale Indexe (EKey[0:9] -> data.NNN, Offset, Grösse) -> BLTE entpacken.
"""
import bisect
import os
import struct
import zlib


class CascFehler(Exception):
    pass


def blte(data):
    """BLTE-Block entpacken (N = roh, Z = zlib, F = verschachtelt; E = verschlüsselt -> Fehler)."""
    if data[:4] != b"BLTE":
        raise CascFehler("kein BLTE")
    hsize = struct.unpack(">I", data[4:8])[0]
    out = []
    if hsize == 0:
        chunks = [(len(data) - 8, None)]
        pos = 8
    else:
        cnt = int.from_bytes(data[9:12], "big")
        chunks = []
        p = 12
        for _ in range(cnt):
            csize, dsize = struct.unpack(">II", data[p:p + 8])
            chunks.append((csize, dsize))
            p += 24
        pos = hsize                 # Kopfgrösse schliesst Magic und Grösse ein
    for csize, _ in chunks:
        c = data[pos:pos + csize]
        pos += csize
        mode = c[:1]
        if mode == b"N":
            out.append(c[1:])
        elif mode == b"Z":
            out.append(zlib.decompress(c[1:]))
        elif mode == b"F":
            out.append(blte(c[1:]))
        elif mode == b"E":
            raise CascFehler("verschlüsselter Block")
        else:
            raise CascFehler("unbekannter Block " + repr(mode))
    return b"".join(out)


class Casc:
    def __init__(self, wow_dir, product="wowf"):
        self.dir = wow_dir
        self.data_dir = os.path.join(wow_dir, "Data")
        self.build_key = self._build_key(product)
        self.build = self._config(self.build_key)
        self.index = self._load_index()
        self._files = {}
        enc_ekey = bytes.fromhex(self.build["encoding"].split()[1])
        self._enc = self._read_ekey(enc_ekey)
        self._parse_encoding_header()
        self.root_ckey = bytes.fromhex(self.build["root"].split()[0])
        self._root = None

    # --- Konfiguration
    def _build_key(self, product):
        with open(os.path.join(self.dir, ".build.info"), encoding="utf-8") as f:
            lines = [l.rstrip("\n") for l in f if l.strip()]
        head = [h.split("!")[0] for h in lines[0].split("|")]
        for l in lines[1:]:
            row = dict(zip(head, l.split("|")))
            if row.get("Product") == product:
                self.version = row.get("Version")
                return row["Build Key"]
        raise CascFehler("Produkt nicht gefunden: " + product)

    def _config(self, key):
        p = os.path.join(self.data_dir, "config", key[0:2], key[2:4], key)
        out = {}
        with open(p, encoding="utf-8") as f:
            for l in f:
                if " = " in l:
                    k, v = l.rstrip("\n").split(" = ", 1)
                    out[k] = v
        return out

    # --- lokale Indexe: je Bucket die neueste .idx
    def _load_index(self):
        ddir = os.path.join(self.data_dir, "data")
        newest = {}
        for n in os.listdir(ddir):
            if n.endswith(".idx") and len(n) == 14:
                b, v = n[:2], int(n[2:10], 16)
                if b not in newest or v > newest[b][0]:
                    newest[b] = (v, n)
        idx = {}
        for _, n in newest.values():
            with open(os.path.join(ddir, n), "rb") as f:
                d = f.read()
            hsize = struct.unpack("<I", d[0:4])[0]
            key_len = d[8 + 6]           # Kopf: Version(2) Bucket(1) Extra(1) Grösse(1) Offset(1) Schlüssel(1) Bits(1)
            p = (8 + hsize + 15) & ~15
            esize = struct.unpack("<I", d[p:p + 4])[0]
            p += 8
            rec = key_len + 5 + 4
            for i in range(esize // rec):
                q = p + i * rec
                k = d[q:q + key_len]
                v = int.from_bytes(d[q + key_len:q + key_len + 5], "big")
                size = struct.unpack("<I", d[q + key_len + 5:q + rec])[0]
                if k not in idx:
                    idx[k] = (v >> 30, v & 0x3FFFFFFF, size)
        return idx

    def _read_ekey(self, ekey):
        e = self.index.get(ekey[:9])
        if not e:
            raise CascFehler("EKey nicht im lokalen Speicher: " + ekey.hex())
        arch, off, size = e
        fh = self._files.get(arch)
        if fh is None:
            fh = open(os.path.join(self.data_dir, "data", "data.%03d" % arch), "rb")
            self._files[arch] = fh
        fh.seek(off + 30)
        return blte(fh.read(size - 30))

    # --- Encoding: CKey -> EKey (seitenweise, mit Seitenindex)
    def _parse_encoding_header(self):
        d = self._enc
        if d[:2] != b"EN":
            raise CascFehler("kein Encoding")
        self._ck_len, self._ek_len = d[3], d[4]
        ce_page_kb = struct.unpack(">H", d[5:7])[0]
        ce_pages = struct.unpack(">I", d[9:13])[0]
        espec_size = struct.unpack(">I", d[18:22])[0]
        p = 22 + espec_size
        self._pages_first = []
        for i in range(ce_pages):
            self._pages_first.append(d[p:p + self._ck_len])
            p += self._ck_len + 16
        self._pages_start = p
        self._page_size = ce_page_kb * 1024

    def ekey_of(self, ckey):
        i = bisect.bisect_right(self._pages_first, ckey) - 1
        if i < 0:
            return None
        d = self._enc
        p = self._pages_start + i * self._page_size
        end = p + self._page_size
        while p < end:
            n = d[p]
            if n == 0:
                break
            ck = d[p + 6:p + 6 + self._ck_len]
            if ck == ckey:
                return d[p + 6 + self._ck_len:p + 6 + self._ck_len + self._ek_len]
            p += 6 + self._ck_len + n * self._ek_len
        return None

    def read_ckey(self, ckey):
        ek = self.ekey_of(ckey)
        if ek is None:
            raise CascFehler("CKey nicht im Encoding: " + ckey.hex())
        return self._read_ekey(ek)

    # --- Root: FileDataID -> CKey (TSFM)
    def root(self):
        if self._root is not None:
            return self._root
        d = self.read_ckey(self.root_ckey)
        out = {}
        if d[:4] != b"TSFM":
            raise CascFehler("Root-Format unbekannt: " + repr(d[:4]))
        a, b = struct.unpack("<II", d[4:12])
        if a in (0x18, 0x14) and b in (1, 2, 3):
            hsize, version = a, b
            p = hsize
        else:
            version = 0
            p = 12
        while p + 12 <= len(d):
            n = struct.unpack("<I", d[p:p + 4])[0]
            if version >= 2:
                locale, f1, f2 = struct.unpack("<III", d[p + 4:p + 16])
                f3 = d[p + 16]
                content = f1 | f2 | (f3 << 17)
                p += 17
            else:
                content, locale = struct.unpack("<II", d[p + 4:p + 12])
                p += 12
            deltas = struct.unpack("<%di" % n, d[p:p + 4 * n])
            p += 4 * n
            ck_start = p
            p += 16 * n
            if not (content & 0x10000000):
                p += 8 * n
            # nur Englisch/alle Sprachen (enUS 0x2, alle 0xFFFFFFFF) und nicht "LowViolence"
            if not (locale & 0x2 or locale == 0xFFFFFFFF):
                continue
            fid = -1
            for i, dl in enumerate(deltas):
                fid = fid + 1 + dl
                if fid not in out:
                    out[fid] = d[ck_start + 16 * i:ck_start + 16 * i + 16]
        self._root = out
        return out

    def read_fdid(self, fdid):
        ck = self.root().get(fdid)
        if ck is None:
            raise CascFehler("FileDataID nicht im Root: %d" % fdid)
        return self.read_ckey(ck)


if __name__ == "__main__":
    import sys, time
    t = time.time()
    c = Casc(sys.argv[1])
    print("Version", c.version, "Index-Einträge", len(c.index), "Encoding-Seiten", len(c._pages_first), "%.1fs" % (time.time() - t))
    r = c.root()
    print("Root FileDataIDs (enUS/alle)", len(r), "%.1fs" % (time.time() - t))
    for fid in sys.argv[2:]:
        b = c.read_fdid(int(fid))
        print(fid, len(b), b[:12])
