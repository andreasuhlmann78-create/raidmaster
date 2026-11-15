"""T-D3-BETRIEB: Server-Betrieb aus betrieb_bot.py (D-3 Schritt 21, ab Bot 1.5.168) – ohne Netz.

Bis 1.5.167 gab es dafür nur eine Text-Prüfung (tb_cleanup_loop postet nichts). Hier läuft die Datensicherung
selbst (nur .json/.lua, alte Sicherungen über backup_days hinaus gelöscht), /daten-import ist angemeldet und nur
für die Gildenleitung, und die drei Schleifen sind dieselben Objekte, die RaidBot startet.
"""
import os
import shutil
import sys
import tempfile
import types
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Betrieb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["betrieb_bot"]

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.saved = (self.m.DATA_DIR, self.m.BASE, self.m.is_admin, dict(self.m.cfg))
        self.m.DATA_DIR = os.path.join(self.tmp, "data")
        self.m.BASE = self.tmp
        os.makedirs(self.m.DATA_DIR)
        for fn in ("state.json", "RaidMaster.lua", "notiz.txt"):
            with open(os.path.join(self.m.DATA_DIR, fn), "w") as f:
                f.write("x")

    def tearDown(self):
        self.m.DATA_DIR, self.m.BASE, self.m.is_admin = self.saved[:3]
        self.m.cfg.clear()
        self.m.cfg.update(self.saved[3])
        shutil.rmtree(self.tmp)

    def test_schleifen_und_befehl(self):
        for name in ("backup_loop", "icon_map_loop", "tb_cleanup_loop"):
            self.assertIs(getattr(self.bot, name), getattr(self.m, name), name)
        self.assertIs(self.bot.bot.tree.get_command("daten-import").callback, self.m.import_cmd.callback)

    def test_sicherung_nur_daten_und_alte_weg(self):
        backup = os.path.join(self.tmp, "backup")
        os.makedirs(backup)
        for d in ("2026-11-01", "2026-11-02", "2026-11-03"):
            open(os.path.join(backup, f"daten-{d}.zip"), "wb").close()
        self.m.cfg["backup_days"] = 2
        path = self.m.make_data_backup()
        with zipfile.ZipFile(path) as zf:
            self.assertEqual(sorted(zf.namelist()), ["RaidMaster.lua", "state.json"])     # keine .txt
        self.assertEqual(len([f for f in os.listdir(backup) if f.startswith("daten-")]), 2)
        self.assertIn(os.path.basename(path), os.listdir(backup))

    def test_ohne_datenordner_nichts(self):
        shutil.rmtree(self.m.DATA_DIR)
        self.assertIsNone(self.m.make_data_backup())

    def test_import_nur_gildenleitung(self):
        import asyncio
        self.m.is_admin = lambda u: False
        msgs = []

        class R:
            async def send_message(self_, text, **kw):
                msgs.append(text)
        asyncio.run(self.m.import_cmd.callback(types.SimpleNamespace(user=1, response=R()),
                                               types.SimpleNamespace(filename="daten.zip", size=10)))
        self.assertIn("nur der Gildenchef und die Offiziere", msgs[0])


if __name__ == "__main__":
    unittest.main()
