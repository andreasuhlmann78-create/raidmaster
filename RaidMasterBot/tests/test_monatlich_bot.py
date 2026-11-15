"""T-D3-MONATLICH: monatlich_bot.py (D-3 Schritt 28, ab Bot 1.5.175) – stündliche Schleife ohne Netz.

Bis 1.5.174 prüfte nur ein Text-Test, dass die Schleife Wochenbericht und Blizzard-Prüfung aufruft. Hier läuft sie
selbst (Uhr ersetzt): Raidfähigkeit, Marktberichte und Blizzard-Prüfung bei jedem Lauf, ein Fehler in einem davon
stoppt die anderen nicht; Raider des Monats nur in den ersten 7 Tagen, einmal je Monat, beim allerersten Start nicht
rückwirkend.
"""
import asyncio
import os
import sys
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Monatlich(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["monatlich_bot"]

    def setUp(self):
        m = self.m
        names = ("post_raid_ready", "post_market_report", "post_market_daily", "blizzard_monthly",
                 "announce_raider_of_month", "datetime")
        self.saved = {k: getattr(m, k) for k in names}
        self.saved_state, self.saved_save = dict(m.state.data), m.state.save
        m.state.save = lambda: None
        self.calls = []

        def rec(name, fail=False):
            async def f(*a, **k):
                self.calls.append(name)
                if fail:
                    raise RuntimeError("kaputt")
            return f
        m.post_raid_ready = rec("raidready", fail=True)                 # Fehler darf die anderen nicht stoppen
        m.post_market_report = rec("woche")
        m.post_market_daily = rec("tag")
        m.blizzard_monthly = rec("blizzard")
        m.announce_raider_of_month = rec("rdm")

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        m.state.save = self.saved_save
        m.state.data.clear()
        m.state.data.update(self.saved_state)

    def lauf(self, y, mo, d):
        fixed = datetime(y, mo, d, 12, 0, tzinfo=ZoneInfo("Europe/Zurich"))

        class Uhr(datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed
        self.m.datetime = Uhr
        self.calls.clear()
        with self.assertLogs("raidmaster", level="ERROR"):
            asyncio.run(self.m.monthly_loop.coro())
        return list(self.calls)

    def test_gleiche_schleife_in_bot(self):
        self.assertIs(self.bot.monthly_loop, self.m.monthly_loop)
        self.assertIs(self.bot.bot.tree.get_command("raider-des-monats").callback, self.m.rdm_cmd.callback)

    def test_ablauf(self):
        self.m.state.data.pop("rdm_done", None)
        self.assertEqual(self.lauf(2026, 12, 2), ["raidready", "woche", "tag", "blizzard"])   # erster Start
        self.assertEqual(self.m.state.data["rdm_done"], "2026-11")                         # gemerkt, nicht gekürt
        self.assertNotIn("rdm", self.lauf(2026, 12, 3))                                      # schon erledigt
        self.assertNotIn("rdm", self.lauf(2027, 1, 9))                                       # nach dem 7. nicht
        self.assertEqual(self.lauf(2027, 1, 2)[-1], "rdm")                                   # Dezember küren
        self.assertEqual(self.m.state.data["rdm_done"], "2026-12")
        self.assertNotIn("rdm", self.lauf(2027, 1, 3))                                       # nur einmal


if __name__ == "__main__":
    unittest.main()
