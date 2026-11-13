"""T-MN7: Sammelstelle für Marktdaten (market.py) mit nachgebauten GSMARKT1-Zeilen."""
import gzip
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import market  # noqa: E402

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
        self.assertEqual(market.ingest_text(self.st, line("H", NOW - 40 * 86400, {}), "pc", NOW)["abgelehnt"], 1)

    def test_persist_and_prune(self):
        market.ingest_text(self.st, line("H", NOW - 30 * 86400, {1: (5, 1, 1, 0, 0)}), "pc", NOW)
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
        self.assertEqual(market.report_name(mon), "GSMARKTW1-2026-W47.md")

    def test_realm_fingerprint(self):
        a = "Zugangstoken: Antwortcode 200\n- dynamic-classic1x-eu: 2 Gruppen: A (1), B (2)\n\nFOREVER gefunden in: keinem Namespace\n"
        b = a.replace("Antwortcode 200", "Antwortcode 201")
        c = a.replace("B (2)", "B (2), Forever (3)")
        self.assertEqual(market.realm_fingerprint(a), market.realm_fingerprint(b))
        self.assertNotEqual(market.realm_fingerprint(a), market.realm_fingerprint(c))
        self.assertEqual(market.realm_fingerprint("Zugangstoken: Antwortcode 401\n"), "")


class BotCode(unittest.TestCase):
    """Verdrahtung in bot.py (Text, bot.py ist nicht importierbar)."""
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(os.path.dirname(__file__), "..", "bot.py"), encoding="utf-8") as f:
            cls.src = f.read()

    def test_T_MN7_upload_und_testberichte_lesen(self):
        up = self.src[self.src.index("async def receive_upload"):]
        self.assertLess(up.index("await market_intake(message)"), up.index("await message.delete()"))
        ign = self.src[self.src.index('if route == "ignore":'):][:500]
        self.assertIn("uploader_setup.market_source(cfg, message.channel.id, message.webhook_id)", ign)
        self.assertLess(ign.index("await market_intake_safe(message)"), ign.index("return"))
        import uploader_setup
        cfg = {"data_channel_id": 10, "testberichte_channel_id": 20, "sync": {}}
        self.assertTrue(uploader_setup.market_source(cfg, 20, 999))
        self.assertFalse(uploader_setup.market_source(cfg, 20, None))      # Personen nie
        self.assertFalse(uploader_setup.market_source(cfg, 10, 999))
        self.assertFalse(uploader_setup.market_source({}, 20, 999))

    def test_intake_antwortet_nicht(self):
        fn = self.src[self.src.index("async def market_intake("):self.src.index("async def post_market_report")]
        for verboten in (".send(", ".delete(", ".reply("):
            self.assertNotIn(verboten, fn)

    def test_wochenbericht_und_blizzard_im_loop(self):
        loop = self.src[self.src.index("async def monthly_loop"):][:900]
        self.assertIn("await post_market_report()", loop)
        self.assertIn("await blizzard_monthly()", loop)
        bl = self.src[self.src.index("async def blizzard_monthly"):self.src.index("async def monthly_loop")]
        self.assertIn("if not old or old == fp", bl)           # nur bei Änderung berichten
        self.assertIn("blizzard_api_check.redact(out, cid, sec)", bl)


if __name__ == "__main__":
    unittest.main()
