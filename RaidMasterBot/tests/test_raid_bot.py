"""T-D3-RAID: raid_bot.py (D-3 Schritt 32, ab Bot 1.5.179) – ohne Netz.

Bis 1.5.178 gab es für die Raid-Befehle nur Text-Prüfungen. Hier: /raid ist mit allen zehn Unterbefehlen
angemeldet, /rekorde ebenso; die Taktiken werden aus raid_tactics.json neben dem Modul geladen (gleicher Ordner wie
bot.py) und jede Taktik-Nachricht bleibt unter 2000 Zeichen; Schliessen/Öffnen nur für die Gildenleitung,
Schliessen setzt den Raid auf geschlossen und aktualisiert die Anmeldung.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Raid(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, cls.tmp = load_bot()
        cls.m = sys.modules["raid_bot"]

    def test_angemeldet_und_gleiche_objekte(self):
        g = self.bot.bot.tree.get_command("raid")
        self.assertIs(g, self.m.raid_group)
        self.assertEqual(sorted(c.name for c in g.commands),
                         sorted(["erstellen", "testraid", "absagen", "softres", "schliessen", "oeffnen", "export",
                                 "liste", "aufstellung", "taktik", "fehlend", "grenzen"]))          # fehlend ab 1.5.183 (D-N1)
        self.assertIs(self.bot.bot.tree.get_command("rekorde").callback, self.m.rekorde_cmd.callback)
        self.assertIs(sys.modules["anmeldung_bot"].send_export, self.m.send_export)     # ab 1.5.180 dort benutzt
        for name in ("post_all_tactics", "reminder_loop"):
            self.assertIs(getattr(self.bot, name), getattr(self.m, name), name)
        self.assertIs(sys.modules["upload_bot"].process_assignment, self.m.process_assignment)   # ab 1.5.181 dort

    def test_taktiken_geladen_und_kurz(self):
        self.assertTrue(os.path.isfile(os.path.join(os.path.dirname(self.m.__file__), "raid_tactics.json")))
        self.assertTrue(self.m.RAID_TACTICS, "raid_tactics.json nicht geladen")
        for pool in ["mc"] + list(self.m.RAID_TACTICS):
            for p in self.m.tactics_posts(pool):
                self.assertLessEqual(len(p), 2000, pool)
        self.assertEqual(self.m.tactics_posts("gibt-es-nicht"), [])

    def antwort(self, cmd, *args):
        msgs = []

        class R:
            async def send_message(self_, text, **kw):
                msgs.append(text)
        asyncio.run(cmd.callback(types.SimpleNamespace(user=1, response=R()), *args))
        return msgs

    def test_schliessen_nur_gildenleitung(self):
        m = self.m
        saved = (m.is_creator, m.book.get, m.book.save, m.update_raid_message)
        raid = {"id": 4, "title": "MC"}
        updated = []

        async def upd(r):
            updated.append(r["id"])
        m.book.get = lambda rid: raid
        m.book.save = lambda: None
        m.update_raid_message = upd
        try:
            m.is_creator = lambda u: False
            for cmd in (m.raid_close, m.raid_open):
                self.assertIn("nur der Gildenchef", self.antwort(cmd, "4")[0])
            self.assertNotIn("closed", raid)
            m.is_creator = lambda u: True
            self.assertIn("geschlossen", self.antwort(m.raid_close, "4")[0])
        finally:
            m.is_creator, m.book.get, m.book.save, m.update_raid_message = saved
        self.assertTrue(raid["closed"])
        self.assertEqual(updated, [4])


if __name__ == "__main__":
    unittest.main()
