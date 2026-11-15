"""T-D3-DKPBEFEHLE: dkp_befehle_bot.py (D-3 Schritt 31, ab Bot 1.5.178) – ohne Netz.

Bis 1.5.177 gab es dafür keine Ablauf-Tests. reload_dkp_if_needed lädt die RaidMaster-Datei nur, wenn sie da ist
und sich geändert hat (Änderungszeit), und setzt dann dkp_db/dkp_data/dkp_mtime am Bot; /dkp ohne Daten meldet
das, ohne Profil und Namen bittet es um /charakter.
"""
import asyncio
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class DkpBefehle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["dkp_befehle_bot"]

    def setUp(self):
        m = self.m
        b = m.bot
        self.saved_bot = {k: getattr(b, k, None) for k in ("dkp_db", "dkp_data", "dkp_rows", "dkp_mtime")}
        self.saved = (m.data_path, m.rmd.load_raidmaster_db, m.book.profile)
        fd, self.path = tempfile.mkstemp(suffix=".lua")
        os.close(fd)
        self.loads = 0

        def load(path):
            self.loads += 1
            return {"data": {"players": {}}}
        m.rmd.load_raidmaster_db = load
        m.data_path = lambda: self.path

    def tearDown(self):
        m = self.m
        for k, v in self.saved_bot.items():
            setattr(m.bot, k, v)
        m.data_path, m.rmd.load_raidmaster_db, m.book.profile = self.saved
        os.remove(self.path)

    def test_gleiche_funktion_in_bot(self):
        self.assertIs(sys.modules["upload_bot"].reload_dkp_if_needed, self.m.reload_dkp_if_needed)   # ab 1.5.181 dort benutzt
        self.assertIs(sys.modules["raid_bot"].reload_dkp_if_needed, self.m.reload_dkp_if_needed)
        for name in ("dkp", "dkpliste", "raidmaster-status"):
            self.assertIsNotNone(self.bot.bot.tree.get_command(name), name)

    def test_nur_bei_aenderung_laden(self):
        b = self.m.bot
        b.dkp_data, b.dkp_mtime = None, None
        self.assertTrue(self.m.reload_dkp_if_needed())
        self.assertEqual(b.dkp_data, {"players": {}})
        self.assertEqual(b.dkp_mtime, os.path.getmtime(self.path))
        self.assertFalse(self.m.reload_dkp_if_needed())                    # unverändert: nicht neu laden
        self.assertEqual(self.loads, 1)
        os.utime(self.path, (1, 1))                                         # Datei geändert
        self.assertTrue(self.m.reload_dkp_if_needed())
        self.assertEqual(self.loads, 2)
        self.m.data_path = lambda: self.path + ".fehlt"
        self.assertFalse(self.m.reload_dkp_if_needed())

    def antwort(self, name=None):
        msgs = []

        class R:
            async def send_message(self_, text, **kw):
                msgs.append(text)
        asyncio.run(self.m.dkp_cmd.callback(types.SimpleNamespace(user=types.SimpleNamespace(id=5), response=R()), name))
        return msgs[0]

    def test_dkp_ohne_daten_und_ohne_profil(self):
        self.m.data_path = lambda: None
        self.m.bot.dkp_data = None
        self.assertIn("Noch keine DKP-Daten", self.antwort())
        self.m.bot.dkp_data, self.m.bot.dkp_mtime = {"players": {}}, 1
        self.m.book.profile = lambda uid: None
        self.assertIn("/charakter", self.antwort())


if __name__ == "__main__":
    unittest.main()
