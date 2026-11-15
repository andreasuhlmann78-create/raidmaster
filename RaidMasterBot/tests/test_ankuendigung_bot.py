"""T-D3-ANKUENDIGUNG: Addon-Versionen und Ankündigungen aus ankuendigung_bot.py (D-3 Schritt 18, ab Bot 1.5.164).

Bis 1.5.163 gab es dafür nur Text-Prüfungen. Hier laufen die Regeln selbst: Versionsvergleich (AH Analyzer Pro
5.9.x -> 0.59.x), Versionsreihen der Ankündigungen, welche Reihen bearbeitet statt neu gepostet werden, was als
eigener RaidMaster-Beitrag gilt; /addon und /addon-hochladen sind angemeldet; die Merker (global) liegen im Modul
bei den Funktionen, die sie setzen.
"""
import inspect
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Ankuendigung(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["ankuendigung_bot"]

    def test_angemeldet_und_gleiche_objekte(self):
        tree = self.bot.bot.tree
        self.assertIs(tree.get_command("addon").callback, self.m.addon_cmd.callback)
        self.assertIs(tree.get_command("addon-hochladen").callback, self.m.addon_upload_cmd.callback)
        self.assertIs(self.bot.check_addon_release, self.m.check_addon_release)
        self.assertEqual(self.bot.ANNOUNCE_DIR, self.m.ANNOUNCE_DIR)

    def test_versionsvergleich(self):
        k = self.m.addon_version_key
        self.assertGreater(k("ahsentinel", "0.59.14"), k("ahsentinel", "5.9.12"))   # 5.9.12 = 0.59.12
        self.assertEqual(k("ahsentinel", "5.9.13"), k("ahsentinel", "0.59.13"))
        self.assertGreater(k("levelpilot", "3.12.10"), k("levelpilot", "3.9.99"))
        self.assertEqual(k("levelpilot", "5.9.1"), (5, 9, 1))                       # nur AH-Addons umgerechnet

    def test_versionsreihen(self):
        s = self.m.announce_series
        self.assertEqual(s("levelpilot__levelpilot-3.3.0.md"), ("levelpilot__levelpilot", (3, 3, 0)))
        self.assertEqual(s("projekte__version-1.2.png"), ("projekte__version", (1, 2)))
        self.assertEqual(s("raid-addon-info.md"), (None, None))                        # ohne "__" keine Reihe
        self.assertEqual(s("projekte__ohne-nummer.md"), (None, None))

    def test_bearbeiten_statt_neu(self):
        e = self.m.announce_editable
        for series in ("ahsentinel__vorstellung", "levelpilot__funktionen", "x__hilfe", "y__UEBERSICHT"):
            self.assertTrue(e(series), series)
        for series in ("levelpilot__levelpilot", "", None):
            self.assertFalse(e(series), series)

    def test_eigener_raidmaster_beitrag(self):
        def msg(text, files=()):
            return types.SimpleNamespace(content=text, attachments=[types.SimpleNamespace(filename=f) for f in files])
        self.assertTrue(self.m._is_rm_post(msg("🛡️ **RaidMaster** – Vorstellung")))
        self.assertTrue(self.m._is_rm_post(msg("📜 **Updates** …")))
        self.assertFalse(self.m._is_rm_post(msg("Hallo zusammen")))

    def test_merker_im_modul(self):
        import ast
        tree = ast.parse(inspect.getsource(self.m))
        merker = {name for node in ast.walk(tree) if isinstance(node, ast.Global) for name in node.names}
        self.assertEqual(merker, {"_announce_cleaned", "_rm_cleaned"})          # _releases_cleaned: set, ohne global
        for name in merker | {"_releases_cleaned"}:
            self.assertTrue(hasattr(self.m, name), name)
            self.assertFalse(hasattr(self.bot, name), name)                         # nicht doppelt in bot.py


if __name__ == "__main__":
    unittest.main()
