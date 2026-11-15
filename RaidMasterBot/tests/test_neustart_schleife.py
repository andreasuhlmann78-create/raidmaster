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
        self.block = self.block[:self.block.index("sys.exit(grund.EXIT_CODE)")]   # D-3 Schritt 19 (1.5.165)

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



class Neustart(unittest.TestCase):
    """T-D3-NEUSTART (1.5.165): restart_soon und EXIT_CODE stehen in grund.py. Nach einem Update muss sich der Bot mit
    updater.RESTART_CODE beenden, sonst startet launcher.py ihn nicht neu (Update käme nie an)."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        import grund
        cls.g = grund

    def test_restart_soon_setzt_exit_code(self):
        import asyncio
        import updater
        g = self.g
        closed = []
        saved = (g.EXIT_CODE, g.asyncio.sleep, g.bot.close)

        async def nosleep(_):
            return None

        async def close():
            closed.append(True)
        g.asyncio.sleep, g.bot.close = nosleep, close
        try:
            g.EXIT_CODE = 0
            asyncio.run(g.restart_soon())
            self.assertEqual(g.EXIT_CODE, updater.RESTART_CODE)
            self.assertEqual(closed, [True])
        finally:
            g.EXIT_CODE, g.asyncio.sleep, g.bot.close = saved
        for name in ("pug_bot", "betrieb_bot", "update_bot"):       # alle Aufrufer nutzen grund.restart_soon
            self.assertIs(sys.modules[name].restart_soon, g.restart_soon, name)

    def test_bot_beendet_sich_mit_grund_exit_code(self):
        import ast
        with open(os.path.join(HERE, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertTrue(src.rstrip().endswith("sys.exit(grund.EXIT_CODE)          # D-3 Schritt 19 (1.5.165): "
                                              "restart_soon setzt grund.EXIT_CODE"))
        tree = ast.parse(src)
        top = [n.targets[0].id for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)]
        self.assertNotIn("EXIT_CODE", top)                      # keine zweite, nie gesetzte Kopie in bot.py
        import bot_quelle
        for p in bot_quelle.dateien():
            with open(p, encoding="utf-8") as f:
                code = f.read()
            if "global EXIT_CODE" in code:
                self.assertEqual(os.path.basename(p), "grund.py")


if __name__ == "__main__":
    unittest.main()
