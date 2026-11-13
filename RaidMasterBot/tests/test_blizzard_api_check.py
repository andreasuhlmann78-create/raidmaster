"""T-MN8 (Bot 1.5.129): Messung Blizzard-API – Geheimnisse nie in der Ausgabe, ohne Zugang sauberer Abbruch.
Netz wird nicht benutzt (http ist ersetzt). Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import blizzard_api_check as bac  # noqa: E402

CID, SEC, TOK = "client-id-123456", "sehr-geheim-987654", "token-abcdef"


class Fake:
    def __init__(self, auctions=True):
        self.auctions = auctions

    def __call__(self, url, headers, data=None, timeout=60):
        if "oauth.battle.net" in url:
            return 200, json.dumps({"access_token": TOK}).encode(), {}
        if "dynamic-classic1x" not in url:
            return 404, b"{}", {}
        if url.split("?")[0].endswith("/connected-realm/index"):
            return 200, json.dumps({"connected_realms": [{"href": "https://eu.api.blizzard.com/data/wow/connected-realm/5?x"}]}).encode(), {}
        if url.split("?")[0].endswith("/connected-realm/5"):
            return 200, json.dumps({"realms": [{"name": "Forever"}]}).encode(), {}
        if url.split("?")[0].endswith("/auctions/index"):
            return 200, json.dumps({"auctions": [{"id": 6, "name": "Horde"}]}).encode(), {}
        if url.split("?")[0].endswith("/auctions/6"):
            return (200, json.dumps({"auctions": [{"id": 1}, {"id": 2}]}).encode(), {"Last-Modified": "x"}) \
                if self.auctions else (404, b"", {})
        return 404, b"", {}


class MN8(unittest.TestCase):
    def run_measure(self, fake):
        orig = bac.http
        bac.http = fake
        try:
            buf = io.StringIO()
            rc = bac.measure("eu", "forever", CID, SEC, buf)
        finally:
            bac.http = orig
        return rc, buf.getvalue()

    def test_T_MN8_keine_geheimnisse_und_ergebnis(self):
        rc, out = self.run_measure(Fake())
        for s in (CID, SEC, TOK):
            self.assertNotIn(s, out)
        self.assertEqual(rc, 0)
        self.assertIn("2 Auktionen", out)
        self.assertIn("dynamic-classic-eu: connected-realm/index -> 404", out)

    def test_liste_findet_forever(self):
        orig = bac.http
        bac.http = Fake()
        try:
            buf = io.StringIO()
            found = bac.list_realms("eu", CID, SEC, buf)
        finally:
            bac.http = orig
        self.assertEqual(found["dynamic-classic1x"], ["5"])
        self.assertIn("Forever (5)", buf.getvalue())
        self.assertNotIn(SEC, buf.getvalue())

    def test_keine_daten(self):
        rc, out = self.run_measure(Fake(auctions=False))
        self.assertEqual(rc, 1)
        self.assertIn("keine Auktionsdaten", out)

    def test_redact(self):
        self.assertEqual(bac.redact(f"x {SEC} y {CID}", CID, SEC), "x *** y ***")

    def test_ohne_zugang(self):
        self.assertEqual(bac.credentials("/gibt/es/nicht.json")[0] if "BLIZZARD_CLIENT_ID" not in os.environ else None,
                         None)


if __name__ == "__main__":
    unittest.main()
