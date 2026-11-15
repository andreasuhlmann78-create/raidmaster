"""T-D3-EREIGNIS / T-D3-HANDWERK: ereignis_bot.py und handwerk_bot.py (D-3 Schritt 23, ab Bot 1.5.170) – ohne Netz.

Bis 1.5.169 gab es dafür keine Ablauf-Tests. Ereignisse: angelegt nur für echte, künftige Raids mit Recht
"Events verwalten", nie doppelt, 3 Stunden lang, Absage löscht das Ereignis. Handwerk: ohne eingelesene Berufe
der Hinweis aufs Addon, sonst Treffer nach Rezept gruppiert.
"""
import asyncio
import os
import sys
import time
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Guild:
    def __init__(self, manage_events=True):
        self.id = 7
        self.me = types.SimpleNamespace(guild_permissions=types.SimpleNamespace(manage_events=manage_events))
        self.created, self.events = [], {}

    async def create_scheduled_event(self, **kw):
        self.created.append(kw)
        ev = types.SimpleNamespace(id=500 + len(self.created))
        g = self

        async def delete():
            g.events.pop(ev.id, None)
        ev.delete = delete
        self.events[ev.id] = ev
        return ev

    def get_scheduled_event(self, eid):
        return self.events.get(eid)


class Ereignis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["ereignis_bot"]

    def setUp(self):
        m = self.m
        self.saved = (m.bot_guild, m.channel_by_id, m.book.save, dict(m.cfg))
        m.book.save = lambda: None
        m.cfg["raid_events"] = True

        async def none(cid):
            return None
        m.channel_by_id = none

    def tearDown(self):
        m = self.m
        m.bot_guild, m.channel_by_id, m.book.save = self.saved[:3]
        m.cfg.clear()
        m.cfg.update(self.saved[3])

    def raid(self, **kw):
        return dict({"id": 1, "title": "MC", "start": int(time.time()) + 86400, "channel_id": 5, "message_id": 9}, **kw)

    def test_gleiche_funktionen_in_bot(self):
        rb = sys.modules["raid_bot"]                                     # ab 1.5.179 benutzt raid_bot die Ereignisse
        self.assertIs(rb.create_raid_event, self.m.create_raid_event)
        self.assertIs(rb.delete_raid_event, self.m.delete_raid_event)

    def test_anlegen_einmal_und_absage_loescht(self):
        g = Guild()
        self.m.bot_guild = lambda: g
        r = self.raid()
        asyncio.run(self.m.create_raid_event(r))
        self.assertEqual(r["event_id"], 501)
        kw = g.created[0]
        self.assertEqual((kw["end_time"] - kw["start_time"]).total_seconds(), 3 * 3600)
        self.assertIn("https://discord.com/channels/7/5/9", kw["description"])
        asyncio.run(self.m.create_raid_event(r))                       # schon da: nicht doppelt
        self.assertEqual(len(g.created), 1)
        asyncio.run(self.m.delete_raid_event(r))
        self.assertNotIn("event_id", r)
        self.assertEqual(g.events, {})

    def test_nicht_fuer_test_vergangen_ohne_recht(self):
        g = Guild()
        self.m.bot_guild = lambda: g
        for r in (self.raid(test=True), self.raid(start=int(time.time()) - 10)):
            asyncio.run(self.m.create_raid_event(r))
        self.m.bot_guild = lambda: Guild(manage_events=False)
        asyncio.run(self.m.create_raid_event(self.raid()))
        self.m.cfg["raid_events"] = False
        self.m.bot_guild = lambda: g
        asyncio.run(self.m.create_raid_event(self.raid()))
        self.assertEqual(g.created, [])


class Handwerk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["handwerk_bot"]

    def test_angemeldet(self):
        tree = self.bot.bot.tree
        self.assertIs(tree.get_command("handwerk").callback, self.m.handwerk_cmd.callback)
        self.assertIs(tree.get_command("berufe").callback, self.m.berufe_cmd.callback)

    def test_ohne_berufe_hinweis(self):
        saved = self.m.rmd.professions
        self.m.rmd.professions = lambda db: {}
        msgs = []

        class R:
            async def send_message(self_, text, **kw):
                msgs.append(text)
        try:
            asyncio.run(self.m.handwerk_cmd.callback(types.SimpleNamespace(response=R()), "Feuerschutz"))
        finally:
            self.m.rmd.professions = saved
        self.assertIn("Meine Berufe einlesen", msgs[0])


if __name__ == "__main__":
    unittest.main()
