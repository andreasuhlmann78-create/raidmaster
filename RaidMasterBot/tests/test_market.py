"""T-MN7: Sammelstelle für Marktdaten (market.py) mit nachgebauten GSMARKT1-Zeilen."""
import asyncio
import gzip
import json
import os
import shutil
import sys
import tempfile
import types
import time
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import market  # noqa: E402
sys.path.insert(0, os.path.dirname(__file__))
from bot_harness import FakeAttachment, FakeChannel, FakeMessage  # noqa: E402

DIG = "0123456789abcdefghijklmnopqrstuvwxyz"


def enc(n):
    """wie Enc() in shared/GoldSentinelMarkt.lua"""
    n = int(n)
    if n <= 0:
        return "0"
    s = ""
    while n > 0:
        s = DIG[n % 36] + s
        n //= 36
    return s


def line(f, t, entries, cmp_=0, ver=1):
    """entries: {id: (preis, menge, auktionen, abgaenge, abgaengeVorsichtig)}"""
    parts = [",".join(enc(x) for x in (iid,) + tuple(v)) for iid, v in entries.items()]
    auk = sum(v[2] for v in entries.values())
    return "GSMARKT1|%d|%s|%d|%d|%d|%d|%s" % (ver, f, t, auk, len(entries), cmp_, ";".join(parts))


NOW = datetime(2026, 11, 16, 9, 0).timestamp()      # Montag
H = 3600


class ParseTest(unittest.TestCase):
    def test_roundtrip(self):
        ln = line("H", 1763000000, {2589: (1234, 200, 10, 4, 2), 14047: (99999, 3, 1, 0, 0)}, cmp_=1200)
        s = market.parse_line(ln)
        self.assertEqual(s["f"], "H")
        self.assertEqual(s["t"], 1763000000)
        self.assertEqual(s["cmp"], 1200)
        self.assertEqual(s["e"][2589], [1234, 200, 10, 4, 2])
        self.assertEqual(s["e"][14047], [99999, 3, 1, 0, 0])

    def test_empty_entries(self):
        s = market.parse_line("GSMARKT1|1|A|1763000000|0|0|0|")
        self.assertEqual(s["e"], {})

    def test_invalid(self):
        for bad in ("GSMARKT1|1|X|1|0|0|0|", "GSMARKT1|1|H|x|0|0|0|", "GSMARKT1|1|H|1|0|0|0|1,2,3",
                    "GSMARKT1|1|H|1|0|0|0|1,2,3,4,5,!", "GSMARKT1|1|H|0|0|0|0|", "GSTEST1|x", None,
                    "GSMARKT1|1|H|1|0|0|0|0,1,1,1,0,0"):
            self.assertIsNone(market.parse_line(bad), bad)

    def test_lower_never_above_upper(self):
        s = market.parse_line(line("H", 5, {7: (1, 1, 1, 2, 9)}))
        self.assertEqual(s["e"][7][4], 2)

    def test_find_in_savedvariables_and_package(self):
        l1 = line("H", 1763000000, {1: (5, 1, 1, 0, 0)})
        l2 = line("A", 1763000100, {2: (6, 1, 1, 0, 0)})
        lua = 'AHSentinelDB = {\n ["gsMarkt"] = {\n  ["export"] = {\n   "%s", -- [1]\n   "%s", -- [2]\n  },\n },\n}\n' % (l1, l2)
        self.assertEqual(market.find_lines(lua), [l1, l2])
        pkg = json.dumps({"items": ["GSTEST1{}", l1]})
        self.assertEqual(market.find_lines(pkg), [l1])
        gz = gzip.compress(pkg.encode())
        self.assertEqual(market.find_lines(market.text_from_bytes("paket-1.json.gz", gz)), [l1])

    def test_no_names_in_source(self):
        k = market.source_key(123456789)
        self.assertEqual(len(k), 10)
        self.assertNotIn("123456789", k)


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.st = market.Store(self.dir)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_dedup_same_faction_and_time(self):
        ln = line("H", NOW - H, {1: (5, 1, 1, 0, 0)})
        r1 = market.ingest_text(self.st, ln, "pc", NOW)
        r2 = market.ingest_text(self.st, ln, "laptop", NOW)
        r3 = market.ingest_text(self.st, ln, "pc", NOW)
        self.assertEqual((r1["neu"], r2["doppelt"], r3["doppelt"]), (1, 1, 1))
        self.assertEqual(len(self.st.index["scans"]), 1)
        self.assertEqual(sorted(self.st.index["scans"]["H-%d" % (NOW - H)]["q"]), ["laptop", "pc"])
        # andere Fraktion, gleiche Zeit = eigener Scan
        self.assertEqual(market.ingest_text(self.st, line("A", NOW - H, {1: (5, 1, 1, 0, 0)}), "pc", NOW)["neu"], 1)

    def test_reject_future_and_old(self):
        self.assertEqual(market.ingest_text(self.st, line("H", NOW + 2 * H, {}), "pc", NOW)["abgelehnt"], 1)
        self.assertEqual(market.ingest_text(self.st, line("H", NOW - 95 * 86400, {}), "pc", NOW)["abgelehnt"], 1)

    def test_persist_and_prune(self):
        market.ingest_text(self.st, line("H", NOW - 85 * 86400, {1: (5, 1, 1, 0, 0)}), "pc", NOW)
        self.st.save()
        st2 = market.Store(self.dir)
        self.assertEqual(len(st2.index["scans"]), 1)
        self.assertEqual(st2.prune(NOW + 10 * 86400), 1)
        self.assertEqual(os.listdir(os.path.join(self.dir, "scans")), [])

    def test_aggregate_and_report(self):
        # 3 Scans Horde im Abstand von 1 h; Item 2589: 10 Auktionen, je Vergleich 6 Abgänge (davon 2 sicher)
        for i in range(3):
            t = NOW - (3 - i) * H
            ents = {2589: (1000 + i * 100, 200, 10, 6 if i else 0, 2 if i else 0), 14047: (50000, 2, 1, 0, 0)}
            market.ingest_text(self.st, line("H", t, ents, cmp_=H if i else 0), "pc", NOW)
        market.ingest_text(self.st, line("H", NOW - 2 * H, {2589: (1, 1, 1, 0, 0)}, cmp_=H), "laptop", NOW)  # doppelt
        ag = market.aggregate(self.st, "H", NOW - market.WEEK, NOW)
        self.assertEqual(ag["scans"], 3)
        self.assertEqual(ag["quellen"], 2)
        self.assertEqual(ag["abdeckung"], 3)
        it = ag["items"][2589]
        # 2 Vergleiche à 1 h = 2 h: Untergrenze 4 Abgänge / 2 h = 48 je Tag, Obergrenze 12 / 2 h = 144 je Tag
        self.assertAlmostEqual(it["absatz_min"], 48)
        self.assertAlmostEqual(it["absatz_max"], 144)
        self.assertAlmostEqual(it["umschlag"], 4.8)
        self.assertEqual((it["preis_min"], it["preis_max"], it["preis_letzt"]), (1000, 1200, 1200))
        self.assertEqual(it["abdeckung"], 3)
        self.assertEqual(ag["items"][14047]["absatz_min"], 0)
        rep = market.report(self.st, NOW)
        self.assertIn("## Horde", rep)
        self.assertIn("Scans: 3 · Quellen: 2 · Abdeckung: 3/168", rep)
        self.assertIn("item=2589) | 48,0 – 144,0 | 4,80 | 12s 00c", rep)
        self.assertLess(rep.index("item=2589"), rep.index("item=14047"))
        self.assertNotIn("## Allianz", rep)
        self.assertIn("verworfen: 1", rep)

    def test_report_without_data(self):
        self.assertIn("keine Marktdaten", market.report(self.st, NOW))

    def test_report_without_comparison(self):
        market.ingest_text(self.st, line("A", NOW - H, {1: (5, 1, 1, 0, 0)}), "pc", NOW)
        self.assertIn("Noch keine Vergleichsscans", market.report(self.st, NOW))


class GrenzenTest(unittest.TestCase):
    """T-D-MN7a/c/f und D-MN7b: Quellen, Grenzen, ausverkaufte Items, Speicher."""
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.st = market.Store(self.dir)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_T_D_MN7a_quelle_aus_paket(self):
        ln = line("H", NOW - H, {1: (5, 1, 1, 0, 0)})
        pc = json.dumps({"items": [ln], "quelle": "0123456789abcdef"})
        laptop = json.dumps({"items": [ln], "quelle": "fedcba9876543210"})
        alt = json.dumps({"items": [ln]})                                   # Uploader vor 2.3.7: ohne Feld
        q1, q2 = market.source_from_text(pc), market.source_from_text(laptop)
        self.assertNotEqual(q1, q2)
        self.assertIsNone(market.source_from_text(alt))
        self.assertIsNone(market.source_from_text('{"quelle": "Spielername"}'))   # nur 16 Hex
        self.assertNotIn("0123456789abcdef", q1)                              # nie im Klartext abgelegt
        market.ingest_text(self.st, pc, q1, NOW)
        market.ingest_text(self.st, laptop, q2, NOW)
        market.ingest_text(self.st, alt, market.source_key(42), NOW)
        self.assertEqual(len(market.aggregate(self.st, "H", NOW - market.WEEK, NOW)["items"]), 1)
        self.assertEqual(market.aggregate(self.st, "H", NOW - market.WEEK, NOW)["quellen"], 3)

    def test_T_D_MN7c_kopf_gegen_eintraege(self):
        ln = line("H", NOW - H, {1: (5, 1, 1, 0, 0), 2: (6, 1, 1, 0, 0)})
        cut = ln.rsplit(";", 1)[0]                                           # abgeschnitten: Kopf sagt 2 Items
        self.assertIsNone(market.parse_line(cut))
        self.assertIsNotNone(market.parse_line(ln))

    def test_T_D_MN7c_grenze_je_quelle_und_gesamt(self):
        for i in range(market.MAX_NEW_PER_SOURCE_HOUR + 3):
            market.ingest_text(self.st, line("H", NOW - 2 * H + i, {1: (5, 1, 1, 0, 0)}), "pc", NOW)
        self.assertEqual(len(self.st.index["scans"]), market.MAX_NEW_PER_SOURCE_HOUR)
        self.assertEqual(self.st.index["begrenzt"], 3)
        # andere Quelle geht weiter, eine Stunde später auch dieselbe
        self.assertEqual(market.ingest_text(self.st, line("A", NOW - H, {}), "laptop", NOW)["neu"], 1)
        self.assertEqual(market.ingest_text(self.st, line("H", NOW, {}), "pc", NOW + 3700)["neu"], 1)
        old = market.MAX_SCANS
        try:                                    # KEEP90: voll -> ältester Scan weg, der neue wird abgelegt
            market.MAX_SCANS = len(self.st.index["scans"])
            oldest = min(self.st.index["scans"].values(), key=lambda h: h["t"])["t"]
            self.assertEqual(market.ingest_text(self.st, line("N", NOW - H, {}), "dritte", NOW)["neu"], 1)
            self.assertEqual(len(self.st.index["scans"]), market.MAX_SCANS)
            self.assertNotIn(oldest, [h["t"] for h in self.st.index["scans"].values() if h["f"] == "H"])
            self.assertEqual(self.st.index["verdraengt"], 1)
        finally:
            market.MAX_SCANS = old
        self.assertGreater(self.st.bytes_total(), 0)

    def test_D_MN7b_ausverkauft_menge_0(self):
        # Scan 1: Item 7 im Angebot; Scan 2: ganz ausverkauft -> Eintrag 7,0,0,0,3,2 (Absatz zählt, kein Preis)
        market.ingest_text(self.st, line("H", NOW - 2 * H, {7: (900, 3, 3, 0, 0)}), "pc", NOW)
        l2 = "GSMARKT1|1|H|%d|0|0|%d|%s" % (NOW - H, H, ",".join(enc(x) for x in (7, 0, 0, 0, 3, 2)))
        self.assertIsNotNone(market.parse_line(l2))                          # Kopf 0 Items, 1 Eintrag: gültig
        market.ingest_text(self.st, l2, "pc", NOW)
        it = market.aggregate(self.st, "H", NOW - market.WEEK, NOW)["items"][7]
        self.assertAlmostEqual(it["absatz_min"], 48)                          # 2 in 1 h
        self.assertAlmostEqual(it["absatz_max"], 72)
        self.assertEqual((it["preis_min"], it["preis_max"], it["preis_letzt"]), (900, 900, 900))
        self.assertEqual(it["menge"], 3)

    def test_T_D_MN7f_grenze_und_kein_verlauf(self):
        self.assertEqual(market.MAX_LINE, 3 * 1024 * 1024)
        big = line("H", NOW - H, {i: (i, 1, 1, 0, 0) for i in range(1, 40001)})
        self.assertGreater(len(big), 512 * 1024)
        self.assertIsNotNone(market.parse_line(big))
        market.ingest_text(self.st, line("H", NOW - H, {1: (5, 1, 1, 0, 0)}), "pc", NOW)
        it = market.aggregate(self.st, "H", NOW - market.WEEK, NOW)["items"][1]
        self.assertNotIn("verlauf", it)


class Keep90Test(unittest.TestCase):
    """T-KEEP90a/b/c und T-D-MN7c2 (Bot 1.5.142)."""
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.st = market.Store(self.dir)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_T_KEEP90a_90_tage(self):
        self.assertEqual(market.KEEP_DAYS, 90)
        self.assertEqual(market.ingest_text(self.st, line("H", NOW - 80 * 86400, {1: (5, 1, 1, 0, 0)}), "pc", NOW)["neu"], 1)
        self.assertEqual(market.ingest_text(self.st, line("H", NOW - 91 * 86400, {}), "pc", NOW)["abgelehnt"], 1)
        self.assertEqual(self.st.prune(NOW), 0)                       # 80 Tage bleiben
        self.assertEqual(self.st.prune(NOW + 11 * 86400), 1)          # danach 91 Tage alt -> weg

    def test_T_KEEP90b_grenze_und_aelteste_weg(self):
        self.assertEqual(market.MAX_STORE_BYTES, 1024 ** 3)
        self.st.disk_free = lambda: 10 * 1024 ** 3                    # viel frei -> 1 GB gilt
        self.assertEqual(self.st.budget(), 1024 ** 3)
        self.st.disk_free = lambda: 1000                              # wenig frei -> 50 % von (frei + belegt)
        self.assertEqual(self.st.budget(), 500)
        big = {i: (i, 1, 1, 0, 0) for i in range(1, 400)}
        self.st.disk_free = lambda: 10 * 1024 ** 3
        for i in range(4):
            self.assertEqual(market.ingest_text(self.st, line("H", NOW - (10 - i) * H, big), f"q{i}", NOW)["neu"], 1)
        one = max(h["b"] for h in self.st.index["scans"].values())
        total = self.st.bytes_total()
        # jetzt ist nur Platz für 2,5 Scans (Budget = 50 % von frei + belegt): die ältesten gehen, der neue bleibt
        free = max(0, 5 * one - total - one)
        self.st.disk_free = lambda: free
        r = market.ingest_text(self.st, line("H", NOW - 1 * H, big), "q9", NOW)
        new = self.st.index["scans"][f"H-{int(NOW - H)}"]["b"]
        budget = min(market.MAX_STORE_BYTES, int(0.5 * (free + total + new)))    # vor dem Löschen bestimmt
        self.assertEqual(r["neu"], 1)
        ts = sorted(h["t"] for h in self.st.index["scans"].values())
        self.assertEqual(ts[-1], NOW - H)                             # der neue ist da
        self.assertNotIn(NOW - 10 * H, ts)                            # der älteste ist weg
        self.assertLessEqual(self.st.bytes_total(), budget)
        self.assertGreater(self.st.bytes_total() + one, budget)                  # nur so viel gelöscht wie nötig
        self.assertGreater(self.st.index["verdraengt"], 0)
        # leere Ablage, Festplatte voll: nicht einmal ein Scan passt -> nicht ablegen ("begrenzt"), Datei wieder weg
        st = market.Store(tempfile.mkdtemp())
        try:
            st.disk_free = lambda: 0
            r = market.ingest_text(st, line("A", NOW - 2 * H, big), "q9", NOW)
            self.assertEqual(r["begrenzt"], 1)
            self.assertEqual(st.index["scans"], {})
            self.assertEqual(os.listdir(os.path.join(st.base, "scans")), [])
        finally:
            shutil.rmtree(st.base)

    def test_T_KEEP90c_messung(self):
        m = market.measure(self.st)
        for k in ("disk_free", "disk_total", "store", "budget", "scans", "ram_bot", "ram_total"):
            self.assertIn(k, m)
        self.assertGreater(m["disk_total"], 0)
        t = market.measure_line({"store": 12 * 1024 ** 2, "scans": 340, "budget": 1024 ** 3, "disk_free": 1288490189,
                                 "disk_total": 2 * 1024 ** 3, "ram_bot": 85 * 1024 ** 2, "ram_total": None})
        self.assertEqual(t, "Speicher: Marktdaten 12,0 MB (340 Scans), Grenze 1,0 GB (höchstens 1 GB und die Hälfte "
                            "des freien Platzes) · Festplatte frei 1,2 GB von 2,0 GB · Arbeitsspeicher Bot 85,0 MB von "
                            "nicht messbar")

    def test_T_D_MN7c2_neue_kennung_je_paket(self):
        r = [market.ingest_text(self.st, line("H", NOW - 2 * H + i, {1: (5, 1, 1, 0, 0)}), f"k{i:02d}", NOW)
             for i in range(31)]
        self.assertEqual(sum(x["neu"] for x in r), market.MAX_NEW_SOURCES_DAY)      # 20 neue Kennungen je 24 h
        self.assertEqual(sum(x["begrenzt"] for x in r), 31 - market.MAX_NEW_SOURCES_DAY)
        # bekannte Kennung geht weiter
        self.assertEqual(market.ingest_text(self.st, line("H", NOW - H, {}), "k00", NOW)["neu"], 1)
        # Gesamtgrenze je Stunde über bekannte Quellen
        st = market.Store(tempfile.mkdtemp())
        try:
            n = 0
            for q in range(5):
                for i in range(30):
                    n += market.ingest_text(st, line("H", NOW - 3 * H + q * 100 + i, {}), f"p{q}", NOW)["neu"]
            self.assertEqual(n, market.MAX_NEW_TOTAL_HOUR)
        finally:
            shutil.rmtree(st.base)


class Kern1Test(unittest.TestCase):
    """T-D-KERN1: anonyme Tages-Zusammenfassung (Bot 1.5.142)."""
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.st = market.Store(self.dir)
        self.day = datetime.fromtimestamp(NOW - 86400, market.TZ).strftime("%Y-%m-%d")    # So 15.11.

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_leer(self):
        d = market.daily_summary(self.st, self.day)
        self.assertEqual(d["fraktionen"], {})
        self.assertEqual((d["format"], d["tag"]), ("GSMARKTT1", "2026-11-15"))

    def test_eine_quelle_und_werte(self):
        t0 = market.day_window(self.day)[0]
        market.ingest_text(self.st, line("H", t0 + 3600, {2589: (100, 10, 4, 0, 0)}), "a" * 10, NOW)
        market.ingest_text(self.st, line("H", t0 + 7200, {2589: (120, 8, 3, 2, 1)}, cmp_=3600), "a" * 10, NOW)
        market.ingest_text(self.st, line("H", t0 + 86400 + 60, {2589: (999, 1, 1, 0, 0)}), "a" * 10, NOW)   # Folgetag
        d = market.daily_summary(self.st, self.day)
        h = d["fraktionen"]["H"]
        self.assertEqual((h["scans"], h["quellen"], h["vergleich_h"]), (2, 1, 1.0))
        self.assertEqual(h["items"]["2589"], [2, 1, 110, 100, 120, 9, 24.0, 48.0])   # 1 bzw. 2 Abgänge in 1 h
        self.assertEqual(d["felder"][6:], ["absatz_min_tag", "absatz_max_tag"])
        raw = market.dump_summary(d).decode()
        self.assertNotIn("a" * 10, raw)                              # keine Quellen-Kennung
        for word in ("Spieler", "name", "quelle\""):
            self.assertNotIn(word, raw)

    def test_grenze_1_mb(self):
        t0 = market.day_window(self.day)[0]
        many = {i: (i, 1, 1, 0, 0) for i in range(1, 3001)}
        market.ingest_text(self.st, line("H", t0 + 60, many), "q1", NOW)
        market.ingest_text(self.st, line("H", t0 + 120, {i: (i, 1, 1, 0, 0) for i in range(1, 101)}), "q2", NOW)
        old = market.DAY_MAX_BYTES
        try:
            market.DAY_MAX_BYTES = 20_000
            d = market.daily_summary(self.st, self.day)
            self.assertLessEqual(len(market.dump_summary(d)), 20_000)
            self.assertTrue(d["nur_ab_2_quellen"])
            self.assertEqual(len(d["fraktionen"]["H"]["items"]) + d["weggelassen"], 3000)   # nichts still verloren
            self.assertTrue(all(r[1] >= 2 for r in d["fraktionen"]["H"]["items"].values()))
            market.DAY_MAX_BYTES = 2_000
            d = market.daily_summary(self.st, self.day)
            self.assertLessEqual(len(market.dump_summary(d)), 2_000)
            self.assertEqual(len(d["fraktionen"]["H"]["items"]) + d["weggelassen"], 3000)
        finally:
            market.DAY_MAX_BYTES = old

    def test_echte_v7_exportzeile(self):
        with open(os.path.join(os.path.dirname(__file__), "data", "gsmarkt_v7_export.txt"), encoding="utf-8") as f:
            ln = f.read().strip()
        self.assertTrue(ln.startswith("GSMARKT1|1|H|"))
        self.assertLess(len(ln), market.MAX_LINE)
        s = market.parse_line(ln)
        self.assertEqual((s["items"], len(s["e"])), (3054, 3054))
        when = s["t"] + 60
        self.assertEqual(market.ingest_text(self.st, ln, "v7", when)["neu"], 1)
        day = datetime.fromtimestamp(s["t"], market.TZ).strftime("%Y-%m-%d")
        d = market.daily_summary(self.st, day)
        self.assertEqual(len(d["fraktionen"]["H"]["items"]), 3054)
        self.assertLessEqual(len(market.dump_summary(d)), market.DAY_MAX_BYTES)

    def test_faellig(self):
        tz = market.TZ
        now = datetime(2026, 11, 16, 0, 30, tzinfo=tz)
        self.assertEqual(market.daily_due(now, None), "2026-11-15")
        self.assertIsNone(market.daily_due(now, "2026-11-15"))
        self.assertEqual(market.day_name("2026-11-15"), "GSMARKTT1-2026-11-15.json")
        a, b = market.day_window("2026-10-25")                         # Zeitumstellung: 25 h
        self.assertEqual(b - a, 25 * 3600)

    def test_sammler(self):
        import types as _t
        sys.modules.setdefault("requests", _t.ModuleType("requests"))
        import markt_bericht_holen as mbh
        self.assertTrue(str(mbh.target("GSMARKTT1-2026-11-15.json")).endswith("markt/tages/2026-11-15.json"))
        for bad in ("GSMARKTT1-2026-11-15.json/../x", "GSMARKTT1-15.11.2026.json"):
            self.assertIsNone(mbh.target(bad))


class HelperTest(unittest.TestCase):
    def test_gold(self):
        self.assertEqual(market.gold(123456), "12g 34s")
        self.assertEqual(market.gold(1234), "12s 34c")
        self.assertEqual(market.gold(7), "7c")
        self.assertEqual(market.gold(None), "–")

    def test_weekly_due(self):
        mon = datetime(2026, 11, 16, 9)
        self.assertTrue(market.weekly_due(mon, None))
        self.assertFalse(market.weekly_due(mon, market.week_key(mon)))
        self.assertFalse(market.weekly_due(datetime(2026, 11, 17, 9), None))

    def test_T_D_MN7d_name_und_zeitraum(self):
        tz = ZoneInfo("Europe/Zurich")
        mon = datetime(2026, 11, 16, 9, tzinfo=tz)
        self.assertEqual(market.report_name(mon), "GSMARKTW1-2026-W46.md")     # abgeschlossene Woche
        since, until, wk = market.last_week_window(mon)
        self.assertEqual(wk, "2026-W46")
        self.assertEqual(datetime.fromtimestamp(since, tz), datetime(2026, 11, 9, 0, 0, tzinfo=tz))
        self.assertEqual(datetime.fromtimestamp(until, tz), datetime(2026, 11, 16, 0, 0, tzinfo=tz))
        z = market.report_name(mon, zwischen=True)
        self.assertEqual(z, "GSMARKTW1-2026-W47-zwischen-1116-0900.md")
        self.assertNotEqual(z, market.report_name(mon))                        # überschreibt nie den Wochenbericht
        # Zeitumstellung (letzter Sonntag im Oktober): Woche beginnt trotzdem um 00:00 Ortszeit
        s2, u2, _ = market.last_week_window(datetime(2026, 10, 26, 9, tzinfo=tz))   # Umstellung am 25.10.
        self.assertEqual(datetime.fromtimestamp(s2, tz).hour, 0)
        self.assertEqual(u2 - s2, 7 * 86400 + 3600)

    def test_T_D_MN7d_eine_zone(self):
        old = market.TZ
        try:
            market.set_tz("UTC")
            t = datetime(2026, 11, 16, 0, 30, tzinfo=ZoneInfo("UTC")).timestamp()   # Mo 00:30 UTC
            self.assertEqual(market.hour_of_week(t), 0)
            market.set_tz("Europe/Zurich")
            self.assertEqual(market.hour_of_week(t), 1)                              # Mo 01:30 MEZ
        finally:
            market.TZ = old

    def test_wochenbericht_nur_alte_woche(self):
        d = tempfile.mkdtemp()
        try:
            st = market.Store(d)
            tz = ZoneInfo("Europe/Zurich")
            mon = datetime(2026, 11, 16, 9, tzinfo=tz)
            market.ingest_text(st, line("H", datetime(2026, 11, 15, 12, tzinfo=tz).timestamp(), {1: (5, 1, 1, 0, 0)}),
                               "pc", mon.timestamp())
            market.ingest_text(st, line("A", datetime(2026, 11, 16, 8, tzinfo=tz).timestamp(), {1: (5, 1, 1, 0, 0)}),
                               "pc", mon.timestamp())
            name, text = market.weekly_report(st, mon)
            self.assertEqual(name, "GSMARKTW1-2026-W46.md")
            self.assertIn("## Horde", text)
            self.assertNotIn("## Allianz", text)                                     # gehört schon zur neuen Woche
            self.assertIn("Woche 2026-W46", text)
            zname, ztext = market.interim_report(st, mon)
            self.assertIn("## Allianz", ztext)
        finally:
            shutil.rmtree(d)

    def test_realm_fingerprint(self):
        a = "Zugangstoken: Antwortcode 200\n- dynamic-classic1x-eu: 2 Gruppen: A (1), B (2)\n\nFOREVER gefunden in: keinem Namespace\n"
        b = a.replace("Antwortcode 200", "Antwortcode 201")
        c = a.replace("B (2)", "B (2), Forever (3)")
        self.assertEqual(market.realm_fingerprint(a), market.realm_fingerprint(b))
        self.assertNotEqual(market.realm_fingerprint(a), market.realm_fingerprint(c))
        self.assertEqual(market.realm_fingerprint("Zugangstoken: Antwortcode 401\n"), "")

    def test_sammler_dateinamen(self):
        import types as _t
        sys.modules.setdefault("requests", _t.ModuleType("requests"))
        import markt_bericht_holen as mbh
        self.assertTrue(str(mbh.target("GSMARKTW1-2026-W46.md")).endswith("markt/2026-W46.md"))
        self.assertTrue(str(mbh.target("GSMARKTW1-2026-W47-zwischen-1116-0900.md"))
                        .endswith("markt/2026-W47-zwischen-1116-0900.md"))
        self.assertTrue(str(mbh.target("GSBLIZZ1-2026-12-01.txt")).endswith("markt/blizzard-2026-12-01.txt"))
        for bad in ("../x.md", "GSMARKTW1-2026-W46.md/../a", "GSMARKTW1-x.md"):
            self.assertIsNone(mbh.target(bad))


def run(coro):
    return asyncio.run(coro)


class BotAblauf(unittest.TestCase):
    """D-T1: Ablauf-Tests mit dem echten bot.py (Kopie im temporären Ordner, Attrappen, kein Netz)."""
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, cls.tmp = load_bot()
        cls.m = sys.modules["markt_bot"]     # D-3 Schritt 4: die Marktdaten-Funktionen liegen in markt_bot – dort patchen

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.m._market_store = market.Store(self.dir)
        self.m._market_lock = asyncio.Lock()
        self.cfg_backup = dict(self.bot.cfg)
        self.state_backup = dict(self.bot.state.data)

    def tearDown(self):
        self.bot.cfg.clear()
        self.bot.cfg.update(self.cfg_backup)
        self.bot.state.data.clear()
        self.bot.state.data.update(self.state_backup)
        shutil.rmtree(self.dir)

    def paket(self, quelle=None, t=None, faction="H"):
        doc = {"items": ["GSTEST1{}", line(faction, t or time.time() - H, {2589: (100, 5, 2, 1, 1)}, cmp_=600)]}
        if quelle:
            doc["quelle"] = quelle
        return FakeAttachment("paket-1.json.gz", gzip.compress(json.dumps(doc).encode()))

    def test_T_D_MN7a_zwei_rechner_zwei_quellen(self):
        t = time.time() - H
        r1 = run(self.bot.market_intake(FakeMessage([self.paket("0123456789abcdef", t)], webhook_id=5)))
        r2 = run(self.bot.market_intake(FakeMessage([self.paket("fedcba9876543210", t)], webhook_id=5)))
        self.assertEqual((r1["neu"], r2["doppelt"]), (1, 1))
        head = next(iter(self.m._market_store.index["scans"].values()))
        self.assertEqual(len(head["q"]), 2)                                  # gleicher Webhook, zwei Quellen
        r3 = run(self.bot.market_intake(FakeMessage([self.paket(None, t)], webhook_id=5)))   # alter Uploader
        self.assertEqual(r3["doppelt"], 1)
        self.assertEqual(len(head["q"]), 3)
        with open(os.path.join(self.dir, "index.json"), encoding="utf-8") as f:
            self.assertNotIn("0123456789abcdef", f.read())

    def test_T_D_MN7c_nur_eigener_webhook(self):
        import uploader_setup
        cfg = {"testberichte_channel_id": 20, "testberichte_webhook_id": 777}
        self.assertTrue(uploader_setup.market_source(cfg, 20, 777))
        self.assertFalse(uploader_setup.market_source(cfg, 20, 778))          # fremder Webhook
        self.assertFalse(uploader_setup.market_source(cfg, 20, None))         # Personen nie
        self.assertFalse(uploader_setup.market_source(cfg, 21, 777))
        self.assertFalse(uploader_setup.market_source({"testberichte_channel_id": 20}, 20, 777))

    def test_T_D_MN7e_nachlesen_nach_start(self):
        self.bot.cfg.update({"testberichte_channel_id": 20, "testberichte_webhook_id": 777})
        own = FakeMessage([self.paket("0123456789abcdef")], webhook_id=777, channel_id=20)
        other = FakeMessage([self.paket("fedcba9876543210", faction="A")], webhook_id=778, channel_id=20)
        person = FakeMessage([self.paket(faction="N")], webhook_id=None, channel_id=20)
        ch = FakeChannel(20, [own, other, person, own])

        async def by_id(cid):
            return ch if cid == 20 else None
        orig = self.m.channel_by_id
        self.m.channel_by_id = by_id
        try:
            n = run(self.bot.market_catchup())
        finally:
            self.m.channel_by_id = orig
        self.assertEqual(n, 2)
        self.assertEqual([h["f"] for h in self.m._market_store.index["scans"].values()], ["H"])   # einmal abgelegt
        self.assertEqual(ch.sent, [])                                        # nie antworten
        self.assertFalse(own.deleted or other.deleted or person.deleted)    # nie löschen

    def test_T_D_MN8b_aenderung_erst_nach_senden_merken(self):
        self.bot.cfg.update({"blizzard_client_id": "id", "blizzard_client_secret": "geheim", "botcmd_channel_id": 30})
        outputs = ["- dynamic-classic1x-eu: 1 Gruppen: A (1)\n", "- dynamic-classic1x-eu: 2 Gruppen: A (1), B (2)\n"]

        def fake_list(region, cid, sec, out, *a, **k):
            out.write(outputs[0])
        ch = FakeChannel(30)
        chans = {"x": None}

        async def by_id(cid):
            return chans["x"]
        orig_l, orig_c = self.m.blizzard_api_check.list_realms, self.m.channel_by_id
        self.m.blizzard_api_check.list_realms = fake_list
        self.m.channel_by_id = by_id
        try:
            tz = ZoneInfo("Europe/Zurich")
            self.bot.state.data.pop("blizzard_fp", None)
            self.bot.state.data.pop("blizzard_month", None)
            self.assertIsNone(run(self.m.blizzard_monthly(datetime(2026, 11, 20, tzinfo=tz))))   # Ausgangsstand
            fp0 = self.bot.state.data["blizzard_fp"]
            outputs[0] = outputs[1]
            self.assertIsNone(run(self.m.blizzard_monthly(datetime(2026, 12, 1, tzinfo=tz))))    # kein Kanal
            self.assertEqual(self.bot.state.data["blizzard_fp"], fp0)                              # nicht verloren
            chans["x"] = ch
            name = run(self.m.blizzard_monthly(datetime(2027, 1, 1, tzinfo=tz)))
            self.assertEqual(name, "GSBLIZZ1-2027-01-01.txt")
            self.assertNotEqual(self.bot.state.data["blizzard_fp"], fp0)
            self.assertEqual(len(ch.sent), 1)
        finally:
            self.m.blizzard_api_check.list_realms = orig_l
            self.m.channel_by_id = orig_c

    def test_T_D_MN7d_bot_berichte(self):
        self.bot.cfg.update({"botcmd_channel_id": 30})
        ch = FakeChannel(30)

        async def by_id(cid):
            return ch
        orig = self.m.channel_by_id
        self.m.channel_by_id = by_id
        try:
            tz = ZoneInfo(self.bot.TZ)
            mon = datetime(2026, 11, 16, 9, tzinfo=tz)
            self.bot.state.data.pop("market_week", None)
            z = run(self.m.post_market_report(mon, force=True))
            self.assertIn("-zwischen-", z)
            self.assertNotIn("market_week", self.bot.state.data)              # Montags-Merker bleibt frei
            w = run(self.m.post_market_report(mon))
            self.assertEqual(w, "GSMARKTW1-2026-W46.md")
            self.assertIsNone(run(self.m.post_market_report(mon)))          # nie doppelt
            self.assertEqual([kw["file"].filename for _, kw in ch.sent], [z, w])
        finally:
            self.m.channel_by_id = orig

    def test_T_D_KERN1_tagesbericht_posten(self):
        self.bot.cfg.update({"botcmd_channel_id": 30})
        ch = FakeChannel(30)

        async def by_id(cid):
            return ch
        orig = self.m.channel_by_id
        self.m.channel_by_id = by_id
        try:
            tz = market.TZ
            now = datetime(2026, 11, 16, 0, 30, tzinfo=tz)
            self.bot.state.data.pop("market_day", None)
            self.assertIsNone(run(self.m.post_market_daily(now)))             # keine Scans: nichts posten
            self.assertEqual(self.bot.state.data["market_day"], "2026-11-15")
            self.bot.state.data.pop("market_day")
            t0 = market.day_window("2026-11-15")[0]
            market.ingest_text(self.m._market_store, line("H", t0 + 60, {2589: (100, 5, 2, 0, 0)}), "x", now.timestamp())
            name = run(self.m.post_market_daily(now))
            self.assertEqual(name, "GSMARKTT1-2026-11-15.json")
            self.assertIsNone(run(self.m.post_market_daily(now)))             # nie doppelt
            self.assertEqual(len(ch.sent), 1)
        finally:
            self.m.channel_by_id = orig

    def test_T_D_MN7e2_nachlesen_ohne_recht(self):
        import discord
        self.bot.cfg.update({"testberichte_channel_id": 20, "testberichte_webhook_id": 777})

        class Gesperrt(FakeChannel):
            def history(self, **kw):
                async def gen():
                    raise discord.Forbidden(types.SimpleNamespace(status=403, reason="x"), "kein Leserecht")
                    yield
                return gen()
        ch = Gesperrt(20)

        async def by_id(cid):
            return ch
        orig = self.m.channel_by_id
        self.m.channel_by_id = by_id
        try:
            with self.assertLogs("raidmaster", level="WARNING") as cm:
                self.assertEqual(run(self.bot.market_catchup()), 0)
            self.assertTrue(any("Nachlesen in #testberichte nicht möglich (403" in r for r in cm.output))
        finally:
            self.m.channel_by_id = orig

    def test_T_D_GS1b_grosse_guildsentinel_datei(self):
        self.bot.cfg["uploader_webhooks"] = [5]
        big = FakeAttachment("GuildSentinel.lua", b"", size=26 * 1024 * 1024)
        msg = FakeMessage([big], webhook_id=5)
        with self.assertLogs("raidmaster", level="WARNING") as cm:
            run(self.bot.receive_upload(msg))                                # früher: UnboundLocalError
        self.assertTrue(any("zu gross" in r for r in cm.output))
        self.assertEqual(big.reads, 0)

    def test_intake_antwortet_und_loescht_nie(self):
        msg = FakeMessage([self.paket("0123456789abcdef")], webhook_id=5)
        run(self.bot.market_intake(msg))
        self.assertFalse(msg.deleted)


class BotCode(unittest.TestCase):
    """Verdrahtung, die sich nur im Quelltext zeigt (on_message, Loop)."""
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import bot_quelle                      # D-3 Schritt 28: monthly_loop steht in monatlich_bot.py
        cls.src = bot_quelle.alle()

    def test_T_MN7_upload_und_testberichte_lesen(self):
        up = self.src[self.src.index("async def receive_upload"):]
        self.assertLess(up.index("await market_intake(message)"), up.index("await message.delete()"))
        ign = self.src[self.src.index('if route == "ignore":'):][:500]
        self.assertIn("uploader_setup.market_source(cfg, message.channel.id, message.webhook_id)", ign)
        self.assertLess(ign.index("await market_intake_safe(message)"), ign.index("return"))
        self.assertIn("asyncio.create_task(market_catchup())", self.src[self.src.index("async def on_ready"):][:2500])

    def test_wochenbericht_und_blizzard_im_loop(self):
        loop = self.src[self.src.index("async def monthly_loop"):][:900]
        self.assertIn("await post_market_report()", loop)
        self.assertIn("await blizzard_monthly()", loop)


if __name__ == "__main__":
    unittest.main()
