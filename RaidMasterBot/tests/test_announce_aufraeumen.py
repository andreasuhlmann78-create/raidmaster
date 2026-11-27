"""T-DC-ANN2 (Entscheid des Nutzers 27.11. 20:58 "Nur die letzten 3 behalten"): announce_aufraeumen behält je Addon die 3 neuesten
ZIP-Anhänge + die stabile Version (download/), .md immer; der Wächter lässt genau diese Löschungen zu, alles andere bleibt ROT."""
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

import announce_aufraeumen as a  # noqa: E402
import announce_guard as g  # noqa: E402

ANN = [f"ahs__ahs-0.65.{n}.AHSentinel.zip" for n in (9, 10, 11, 12, 13)] + \
      [f"ahs__ahs-0.65.{n}.md" for n in (9, 10, 11, 12, 13)] + \
      ["lp__lp-3.13.2.LevelPilot.zip", "lore__bild.zip", "x__y-1.0.png"]
DL = ["AHSentinel-0.65.10.zip", "RaidMasterUploader.zip", "RaidMaster-latest.zip"]


class Plan(unittest.TestCase):
    def test_drei_neueste_und_stabile(self):
        keep, remove = a.plan(ANN, DL)
        self.assertEqual(remove, ["ahs__ahs-0.65.9.AHSentinel.zip"])            # 13,12,11 neueste; 10 stabil; 9 weg
        self.assertIn("ahs__ahs-0.65.10.AHSentinel.zip", keep)
        self.assertIn("lore__bild.zip", keep)                                    # unbekannter Name: nie anfassen
        self.assertIn("lp__lp-3.13.2.LevelPilot.zip", keep)
        self.assertFalse(any(n.endswith(".md") for n in remove))                 # .md nie
        self.assertNotIn("x__y-1.0.png", keep + remove)                          # nur ZIPs

    def test_zahl_statt_text(self):
        names = [f"t__t-2.5.{n}.ThreatSentinel.zip" for n in (9, 10, 31, 4)]
        keep, remove = a.plan(names, [])
        self.assertEqual(remove, ["t__t-2.5.4.ThreatSentinel.zip"])             # 2.5.31 > 2.5.10 > 2.5.9 > 2.5.4


class Waechter(unittest.TestCase):
    def head(self):
        keep, _ = a.plan(ANN, DL)
        return [n for n in ANN if not n.endswith(".zip")] + keep

    def test_erlaubt_nur_alte_zip(self):
        lines = ["D\tannounce/ahs__ahs-0.65.9.AHSentinel.zip"]
        self.assertEqual(g.violations(lines, self.head(), DL), [])
        self.assertEqual(g.violations(lines), ["announce/ahs__ahs-0.65.9.AHSentinel.zip (gelöscht)"])   # ohne Stand: wie bisher

    def test_rot_bei_neuester_stabiler_md_und_umbenennen(self):
        head = self.head()
        for line in ("D\tannounce/ahs__ahs-0.65.12.AHSentinel.zip",          # unter den 3 neuesten
                     "D\tannounce/ahs__ahs-0.65.10.AHSentinel.zip",          # stabil
                     "D\tannounce/ahs__ahs-0.65.9.md",                       # .md nie
                     "D\tannounce/lore__bild.zip",                           # unbekannter Name
                     "R100\tannounce/ahs__ahs-0.65.9.AHSentinel.zip\tannounce/x.zip"):
            with self.subTest(line=line):
                self.assertTrue(g.violations([line], [n for n in head if n not in line], DL))

    def test_echtes_repo_plan_und_waechter_passen_zusammen(self):
        ann = os.listdir(os.path.join(ROOT, "announce"))
        dl = os.listdir(os.path.join(ROOT, "download"))
        keep, remove = a.plan(ann, dl)
        head = [n for n in ann if n not in remove]
        lines = [f"D\tannounce/{n}" for n in remove]
        self.assertEqual(g.violations(lines, head, dl), [])                     # alles, was das Skript entfernt, lässt der Wächter zu
        stable = a.stable_versions(dl)
        for addon, vers in stable.items():
            for v in vers:
                for n in remove:
                    av = a.announce_zip(n)
                    self.assertFalse(av and av[0] == addon and av[1] == v, n)


class BotUnberuehrt(unittest.TestCase):
    def test_nur_zip_weg_bot_loescht_nichts(self):
        """Fehlt im Repo nur die ZIP (die .md bleibt), entfernt mirror_announce_removals nichts – keine Datei, kein Discord-Beitrag."""
        import tempfile
        sys.path.insert(0, os.path.join(HERE, ".."))
        import updater
        with tempfile.TemporaryDirectory() as base:
            os.makedirs(os.path.join(base, "announce"))
            for n in ("ahs__ahs-0.65.9.md", "ahs__ahs-0.65.9.AHSentinel.zip", "ahs__ahs-0.65.13.md"):
                open(os.path.join(base, "announce", n), "w").close()
            removed = updater.mirror_announce_removals(["ahs__ahs-0.65.9.md", "ahs__ahs-0.65.13.md"], base)
            self.assertEqual(removed, [])
            self.assertTrue(os.path.isfile(os.path.join(base, "announce", "ahs__ahs-0.65.9.AHSentinel.zip")))
            # Gegenprobe: fehlt die .md, greift die alte Regel (nach announce_entfernt/)
            self.assertEqual(updater.mirror_announce_removals(["ahs__ahs-0.65.13.md"], base), ["ahs__ahs-0.65.9.md"])


if __name__ == "__main__":
    unittest.main()
