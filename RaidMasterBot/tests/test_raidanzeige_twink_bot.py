"""T-D3-RAIDANZEIGE / T-D3-TWINK: raidanzeige_bot.py und twink_bot.py (D-3 Schritt 24, ab Bot 1.5.171) – ohne Netz.

Bis 1.5.170 gab es dafür keine Ablauf-Tests. Raid-Anzeige: Titel bei Absage/geschlossen, PUG-Hinweis mit Soft
Reserve, Zahl der Angemeldeten; Aktualisieren bearbeitet die Anmelde-Nachricht, ein Discord-Fehler wird nur
protokolliert. Twinks: /twink ist mit vier Unterbefehlen angemeldet, ohne Main kein Twink, nur Buchstaben,
nach dem Entfernen werden nur Raids aktualisiert, in denen das Mitglied angemeldet ist.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Raidanzeige(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["raidanzeige_bot"]

    def raid(self, **kw):
        return dict({"id": 3, "title": "MC", "start": 1794470000, "signups": {}, "pool_name": "Molten Core"}, **kw)

    def test_gleiche_funktionen_in_bot(self):
        self.assertIs(sys.modules["anmeldung_bot"].raid_embed, self.m.raid_embed)   # ab 1.5.180 dort benutzt
        self.assertIs(self.bot.update_raid_message, self.m.update_raid_message)
        self.assertIs(sys.modules["twink_bot"].update_raid_message, self.m.update_raid_message)

    def test_kaertchen(self):
        e = self.m.raid_embed(self.raid())
        self.assertEqual(e.title, "MC")
        self.assertIn("**Angemeldet: 0**", e.description)
        self.assertEqual(e.footer.text, "Raid-ID 3 · RaidMaster")
        self.assertEqual(self.m.raid_embed(self.raid(cancelled=True)).title, "MC – ABGESAGT")
        closed = self.m.raid_embed(self.raid(closed=True))
        self.assertEqual(closed.title, "MC (Anmeldung geschlossen)")
        self.assertEqual(closed.color.value, self.m.GREY)
        pug = self.m.raid_embed(self.raid(mode="pug", softres="https://softres.it/raid/x"))
        self.assertIn("PUG-Raid", pug.description)
        self.assertIn("https://softres.it/raid/x", pug.description)

    def test_aktualisieren_und_fehler_nur_protokoll(self):
        import discord
        edits = []

        class Part:
            async def edit(self_, **kw):
                edits.append(kw)
        ch = types.SimpleNamespace(get_partial_message=lambda mid: Part())
        saved = (self.m.bot.get_channel, self.m.raid_view)
        self.m.bot.get_channel = lambda cid: ch
        self.m.raid_view = lambda raid: "VIEW"
        try:
            asyncio.run(self.m.update_raid_message(self.raid(message_id=9, channel_id=5)))
            self.assertEqual(edits[0]["view"], "VIEW")
            asyncio.run(self.m.update_raid_message(self.raid()))           # ohne Nachricht: nichts
            self.assertEqual(len(edits), 1)

            class Kaputt:
                async def edit(self_, **kw):
                    raise discord.HTTPException(types.SimpleNamespace(status=404, reason="x"), "weg")
            ch.get_partial_message = lambda mid: Kaputt()
            with self.assertLogs("raidmaster", level="WARNING"):
                asyncio.run(self.m.update_raid_message(self.raid(message_id=9, channel_id=5)))
        finally:
            self.m.bot.get_channel, self.m.raid_view = saved


class Twink(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["twink_bot"]

    def test_angemeldet(self):
        g = self.bot.bot.tree.get_command("twink")
        self.assertIs(g, self.m.twink_group)
        self.assertEqual(sorted(c.name for c in g.commands), ["entfernen", "hinzufügen", "liste", "wechseln"])

    def antwort(self, cmd, *args, user=5):
        msgs = []

        class R:
            async def send_message(self_, text, **kw):
                msgs.append(text)
        asyncio.run(cmd.callback(types.SimpleNamespace(user=types.SimpleNamespace(id=user), response=R()), *args))
        return msgs

    def test_ohne_main_und_nur_buchstaben(self):
        saved = (self.m.book.profile, self.m.book.add_alt)
        added = []
        self.m.book.add_alt = lambda *a: added.append(a) or {"main": "Thrall"}
        choice = types.SimpleNamespace
        try:
            self.m.book.profile = lambda uid: None
            msg = self.antwort(self.m.twink_add, "Jaina", choice(value="MAGE", name="Magier"), choice(value="ranged", name="Fernkampf"))
            self.assertIn("zuerst deinen Main", msg[0])
            self.m.book.profile = lambda uid: {"name": "Thrall"}
            msg = self.antwort(self.m.twink_add, "Jaina2", choice(value="MAGE", name="Magier"), choice(value="ranged", name="Fernkampf"))
            self.assertIn("nur Buchstaben", msg[0])
            self.assertEqual(added, [])
            msg = self.antwort(self.m.twink_add, "Jaina", choice(value="MAGE", name="Magier"), choice(value="ranged", name="Fernkampf"))
            self.assertIn("Twink **Jaina**", msg[0])
            self.assertEqual(len(added), 1)
        finally:
            self.m.book.profile, self.m.book.add_alt = saved

    def test_nur_eigene_raids_aktualisiert(self):
        done = []

        async def upd(r):
            done.append(r["id"])
        saved = (self.m.update_raid_message, self.m.book.open_raids)
        self.m.update_raid_message = upd
        self.m.book.open_raids = lambda: [{"id": 1, "signups": {"5": {}}}, {"id": 2, "signups": {"6": {}}}]
        try:
            asyncio.run(self.m.refresh_signups_of(5))
        finally:
            self.m.update_raid_message, self.m.book.open_raids = saved
        self.assertEqual(done, [1])


if __name__ == "__main__":
    unittest.main()
