"""Offline-Test für updater.mirror_announce_removals (Bot 1.5.95): im Repo gelöschte Ankündigungen.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import updater  # noqa: E402


class MirrorRemovals(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = self.tmp.name
        self.ann = os.path.join(self.base, "announce")
        os.makedirs(self.ann)

    def tearDown(self):
        self.tmp.cleanup()

    def touch(self, *names):
        for n in names:
            with open(os.path.join(self.ann, n), "w", encoding="utf-8") as f:
                f.write("x")

    def removed_dir(self):
        d = os.path.join(self.base, updater.ANNOUNCE_REMOVED_DIR)
        return sorted(os.listdir(d)) if os.path.isdir(d) else []

    def test_geloeschte_datei_mit_anhang(self):
        self.touch("a__x-1.0.md", "a__x-1.0.png", "b__y.md", "c__z-2.0.md")
        repo = ["b__y.md", "c__z-2.0.md"]
        self.assertEqual(updater.mirror_announce_removals(repo, self.base), ["a__x-1.0.md"])
        self.assertEqual(self.removed_dir(), ["a__x-1.0.md", "a__x-1.0.png"])
        self.assertEqual(sorted(os.listdir(self.ann)), ["b__y.md", "c__z-2.0.md"])

    def test_nichts_geloescht(self):
        self.touch("b__y.md", "c__z-2.0.md")
        self.assertEqual(updater.mirror_announce_removals(["b__y.md", "c__z-2.0.md", "d__neu.md"], self.base), [])
        self.assertEqual(self.removed_dir(), [])

    def test_leeres_repo_schuetzt(self):
        self.touch("b__y.md", "c__z-2.0.md")
        self.assertEqual(updater.mirror_announce_removals([], self.base), [])
        self.assertEqual(updater.mirror_announce_removals(["nur.png"], self.base), [])
        self.assertEqual(len(os.listdir(self.ann)), 2)

    def test_weniger_als_die_haelfte_schuetzt(self):
        self.touch("a.md", "b.md", "c.md", "d.md", "e.md")
        self.assertEqual(updater.mirror_announce_removals(["a.md", "b.md"], self.base), [])
        self.assertEqual(len(os.listdir(self.ann)), 5)

    def test_anhang_noch_im_repo_bleibt(self):
        self.touch("a__x-1.0.md", "a__x-1.0.zip", "b__y.md")
        updater.mirror_announce_removals(["b__y.md", "a__x-1.0.zip"], self.base)
        self.assertEqual(self.removed_dir(), ["a__x-1.0.md"])
        self.assertIn("a__x-1.0.zip", os.listdir(self.ann))

    def test_aehnlicher_name_bleibt(self):
        # a-1.0.1.md beginnt mit "a-1.0." – steht aber noch im Repo und darf nicht mit weg
        self.touch("k__a-1.0.md", "k__a-1.0.1.md", "b.md")
        updater.mirror_announce_removals(["k__a-1.0.1.md", "b.md"], self.base)
        self.assertEqual(self.removed_dir(), ["k__a-1.0.md"])
        self.assertIn("k__a-1.0.1.md", os.listdir(self.ann))

    def test_ohne_ordner(self):
        os.rmdir(self.ann)
        self.assertEqual(updater.mirror_announce_removals(["a.md"], self.base), [])


import re  # noqa: E402

_VER = re.compile(r"^(?P<series>.+?)[-_ ]v?(?P<ver>\d+(?:\.\d+)+)(?P<rest>.*)$")   # wie ANNOUNCE_VER in bot.py


def series_of(fn):
    stem = fn[:-3] if fn.endswith(".md") else fn
    m = _VER.match(stem)
    if "__" not in stem or not m or "__" not in m.group("series"):
        return None, None
    return m.group("series").lower(), tuple(int(x) for x in m.group("ver").split("."))


class Live(unittest.TestCase):
    """Schutz announce_delete_max zählt nur Dateien, die noch Beiträge im Discord haben (Bot 1.5.101)."""
    HILFE = [f"addon-hilfe__ahanalyzerpro-hilfe-{v}.md"
             for v in ("0.60.0", "0.60.1", "0.60.7", "0.60.10", "0.61.0", "0.62.0", "0.65.3")]

    def test_sieben_fassungen_nur_neueste_zaehlt(self):
        rec = {self.HILFE[-1]: {"ch": 1, "ids": [10, 11]}}
        live = updater.announce_live(self.HILFE, self.HILFE, rec, series_of)
        self.assertEqual(live, ["addon-hilfe__ahanalyzerpro-hilfe-0.65.3.md"])

    def test_ohne_gespeicherte_ids_neueste_zaehlt(self):
        # vor Bot 1.5.95 gepostet: keine IDs gespeichert, die neueste Fassung (0.60.10 > 0.60.7!) zählt trotzdem
        files = self.HILFE[:4]
        self.assertEqual(updater.announce_live(files, files, {}, series_of), ["addon-hilfe__ahanalyzerpro-hilfe-0.60.10.md"])

    def test_ohne_version_und_nie_gepostet(self):
        files = ["a__ohne-version.md", "b__nie-gepostet-1.0.md"]
        self.assertEqual(updater.announce_live(files, ["a__ohne-version.md"], {}, series_of), ["a__ohne-version.md"])

    def test_viele_eigene_beitraege_zaehlen_alle(self):
        files = [f"k{i}__x-1.0.md" for i in range(7)]
        rec = {f: {"ids": [i]} for i, f in enumerate(files)}
        self.assertEqual(len(updater.announce_live(files, files, rec, series_of)), 7)


if __name__ == "__main__":
    unittest.main()
