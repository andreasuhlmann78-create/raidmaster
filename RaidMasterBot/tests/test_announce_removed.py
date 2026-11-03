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


if __name__ == "__main__":
    unittest.main()
