"""T-D3-TESTMODUS: testupload_bot.py (D-3 Schritt 29, ab Bot 1.5.176) – Aufräumen ohne Netz.

Bis 1.5.175 gab es dafür keinen Ablauf-Test. Hier läuft das Aufräumen selbst: fällige Testnachrichten werden
gelöscht, noch nicht fällige bleiben; scheitert das Löschen, wird es eine Stunde lang erneut versucht, danach
aufgegeben; schon gelöschte (NotFound) sind erledigt; abgelaufene Testraids werden samt Nachricht entfernt.
"""
import asyncio
import os
import sys
import time
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Testmodus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["testupload_bot"]

    def setUp(self):
        m = self.m
        self.saved = (m.channel_by_id, dict(m.state.data), m.state.save, m.book.save)
        m.state.save = lambda: None
        m.book.save = lambda: None
        self.deleted = []
        import discord

        class Part:
            def __init__(self_, mid):
                self_.mid = mid

            async def delete(self_):
                if self_.mid == 13:
                    raise discord.NotFound(types.SimpleNamespace(status=404, reason="weg"), "weg")
                if self_.mid in (14, 15):
                    raise discord.HTTPException(types.SimpleNamespace(status=500, reason="x"), "kaputt")
                self.deleted.append(self_.mid)

        async def by_id(cid):
            return types.SimpleNamespace(get_partial_message=lambda mid: Part(mid))
        m.channel_by_id = by_id

    def tearDown(self):
        m = self.m
        m.channel_by_id = self.saved[0]
        m.state.data.clear()
        m.state.data.update(self.saved[1])
        m.state.save, m.book.save = self.saved[2], self.saved[3]

    def test_gleiche_objekte_in_bot(self):
        self.assertIs(sys.modules["upload_bot"].handle_test_upload, self.m.handle_test_upload)   # ab 1.5.181 dort benutzt
        self.assertIs(self.bot.test_cleanup_loop, self.m.test_cleanup_loop)

    def test_aufraeumen(self):
        now = int(time.time())
        self.m.state.data["test_messages"] = [[1, 11, now - 5], [1, 12, now + 300], [1, 13, now - 5],
                                              [1, 14, now - 60], [1, 15, now - 7200]]
        saved_all = self.m.book.all
        self.m.book.all = lambda: []
        try:
            with self.assertLogs("raidmaster", level="WARNING"):
                asyncio.run(self.m.test_cleanup_loop.coro())
        finally:
            self.m.book.all = saved_all
        self.assertEqual(self.deleted, [11])
        rest = sorted(x[1] for x in self.m.state.data["test_messages"])
        self.assertEqual(rest, [12, 14])            # 12 noch nicht fällig, 14 erneut versuchen; 13 weg, 15 aufgegeben

    def test_abgelaufene_testraids(self):
        raids = {"7": {"id": 7, "test": True, "expires": time.time() - 1, "message_id": 70, "channel_id": 1},
                 "8": {"id": 8, "test": True, "expires": time.time() + 600},
                 "9": {"id": 9}}
        saved = (self.m.book.all, self.m.book.raids.data.get("raids"))
        self.m.book.raids.data["raids"] = raids
        self.m.book.all = lambda: list(raids.values())
        try:
            asyncio.run(self.m.remove_expired_test_raids())
        finally:
            self.m.book.all = saved[0]
            self.m.book.raids.data["raids"] = saved[1]
        self.assertEqual(sorted(raids), ["8", "9"])
        self.assertEqual(self.deleted, [70])


if __name__ == "__main__":
    unittest.main()
