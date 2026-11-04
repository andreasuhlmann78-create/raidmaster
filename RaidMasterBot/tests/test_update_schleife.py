"""Offline-Test (Bot 1.5.108): dieselbe Version zweimal einspielen darf den Bot NICHT neu starten.
Bis 1.5.107 galt jeder Ordner (z. B. tests/) immer als geändert. Folge am 3./4.11.2026: Neustart alle ~70 s,
über 1000 Anmeldungen, Discord setzte den Bot-Token zurück.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import updater  # noqa: E402


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class CopyNew(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = os.path.join(self.tmp.name, "src")
        self.base = os.path.join(self.tmp.name, "base")
        write(os.path.join(self.src, "bot.py"), "print(1)\n")
        write(os.path.join(self.src, "VERSION"), "1.5.108\n")
        write(os.path.join(self.src, "tests", "test_a.py"), "x = 1\n")
        write(os.path.join(self.src, "tests", "sub", "b.txt"), "b\n")
        os.makedirs(self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def test_gleiche_version_zweimal_nichts_geaendert(self):
        first = updater._copy_new(self.src, self.base)
        self.assertEqual(sorted(first), ["VERSION", "bot.py", "tests"])
        self.assertEqual(updater._copy_new(self.src, self.base), [])        # früher: ["tests"] -> Neustart

    def test_pycache_auf_dem_server_zaehlt_nicht(self):
        updater._copy_new(self.src, self.base)
        write(os.path.join(self.base, "tests", "__pycache__", "x.pyc"), "zz")
        self.assertEqual(updater._copy_new(self.src, self.base), [])

    def test_geaenderte_datei_im_ordner_zaehlt(self):
        updater._copy_new(self.src, self.base)
        write(os.path.join(self.src, "tests", "sub", "b.txt"), "neu\n")
        self.assertEqual(updater._copy_new(self.src, self.base), ["tests"])
        with open(os.path.join(self.base, "tests", "sub", "b.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "neu\n")

    def test_neue_und_geloeschte_datei_im_ordner_zaehlen(self):
        updater._copy_new(self.src, self.base)
        write(os.path.join(self.src, "tests", "neu.py"), "y = 2\n")
        self.assertEqual(updater._copy_new(self.src, self.base), ["tests"])
        os.remove(os.path.join(self.src, "tests", "neu.py"))
        self.assertEqual(updater._copy_new(self.src, self.base), ["tests"])
        self.assertFalse(os.path.exists(os.path.join(self.base, "tests", "neu.py")))


class BotPruefung(unittest.TestCase):
    def test_eben_installiert_wird_nicht_nochmal_eingespielt(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        block = src[src.index("async def _check_github("):]
        block = block[:block.index("github_zip(")]
        self.assertIn('pending.get("ref")', block)                        # Prüfung VOR dem Herunterladen


if __name__ == "__main__":
    unittest.main()
