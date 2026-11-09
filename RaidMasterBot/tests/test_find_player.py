"""Offline-Test für raidmaster_data.find_player (Befund K13 Punkt 3, Bot-Teil, Test B09).
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import raidmaster_data as rmd  # noqa: E402


def rows(*names):
    return [{"name": n, "dkp": 10 * (i + 1)} for i, n in enumerate(names)]


class FindPlayer(unittest.TestCase):
    def test_exakt(self):
        r = rows("Tank1", "Testa Beispiel")
        self.assertEqual(rmd.find_player(r, "Testa Beispiel"), (2, r[1]))
        self.assertEqual(rmd.find_player(r, "testa beispiel"), (2, r[1]))

    def test_vorname_eindeutig(self):
        r = rows("Tank1", "Testa Beispiel")
        self.assertEqual(rmd.find_player(r, "Testa"), (2, r[1]))
        self.assertEqual(rmd.find_player(r, " testa "), (2, r[1]))

    def test_vorname_mehrdeutig(self):
        r = rows("Testa Beispiel", "Testa Eisen")
        self.assertIsNone(rmd.find_player(r, "Testa"))

    def test_exakt_geht_vor(self):
        r = rows("Testa Beispiel", "Testa")
        self.assertEqual(rmd.find_player(r, "Testa"), (2, r[1]))

    def test_era_wie_bisher(self):
        r = rows("Tank1", "Testa")
        self.assertEqual(rmd.find_player(r, "testa"), (2, r[1]))
        self.assertIsNone(rmd.find_player(r, "Roka"))
        self.assertIsNone(rmd.find_player(r, ""))
        self.assertIsNone(rmd.find_player(r, None))

    def test_voller_name_ohne_treffer(self):
        r = rows("Testa Beispiel")
        self.assertIsNone(rmd.find_player(r, "Testa Eisen"))


if __name__ == "__main__":
    unittest.main()
