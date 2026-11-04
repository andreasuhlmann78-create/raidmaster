"""Offline-Test (Bot 1.5.107): keine endlose Sofort-Neustart-Schleife mehr.
Am 4.11.2026 setzte Discord den Bot-Token zurück, weil sich der Bot über 1000-mal in kurzer Zeit angemeldet hatte.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import launcher  # noqa: E402


class Starter(unittest.TestCase):
    def test_einzelne_neustarts_ohne_pause(self):
        h = []
        self.assertEqual([launcher.restart_pause(h, t) for t in (0, 100, 200, 300, 400)], [0] * 5)

    def test_schleife_bekommt_pause(self):
        h = []
        pauses = [launcher.restart_pause(h, t) for t in range(0, 60, 5)]       # 12 Neustarts in einer Minute
        self.assertEqual(pauses[:5], [0] * 5)
        self.assertTrue(all(p == launcher.FAST_RESTARTS_PAUSE for p in pauses[5:]))
        # höchstens ~ (Fenster / Pause + Max) Anmeldungen pro 10 Minuten statt Hunderte
        self.assertLessEqual(launcher.FAST_RESTARTS_MAX + launcher.FAST_RESTARTS_WINDOW // launcher.FAST_RESTARTS_PAUSE, 10)

    def test_nach_ruhe_wieder_ohne_pause(self):
        h = []
        for t in range(0, 60, 5):
            launcher.restart_pause(h, t)
        self.assertEqual(launcher.restart_pause(h, 60 + launcher.FAST_RESTARTS_WINDOW + 1), 0)


class BotIntents(unittest.TestCase):
    """bot.py als Text: bei verweigerten Intents höchstens zwei Neustarts, danach CONFIG_ERROR (kein Neustart)."""

    def setUp(self):
        with open(os.path.join(HERE, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        self.block = src[src.index("except discord.PrivilegedIntentsRequired:"):]
        self.block = self.block[:self.block.index("sys.exit(EXIT_CODE)")]

    def test_drei_stufen_und_ende(self):
        self.assertEqual(self.block.count("sys.exit(updater.RESTART_CODE)"), 2)
        self.assertIn("sys.exit(CONFIG_ERROR)", self.block)
        self.assertLess(self.block.index("bot.intents.members"), self.block.index("bot.intents.message_content"))
        # jede Neustart-Stufe schaltet ihren Intent beim nächsten Start ab (sonst wieder Schleife)
        self.assertIn('state.data["members_intent_missing"] = True', self.block)
        self.assertIn('state.data["message_content_intent_missing"] = time.time()', self.block)

    def test_message_content_wird_beim_start_abgeschaltet(self):
        with open(os.path.join(HERE, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertTrue(re.search(r"intents\.message_content = .*and not message_content_blocked\(\)", src))


if __name__ == "__main__":
    unittest.main()
