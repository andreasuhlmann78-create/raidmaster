"""T-D3-BEFEHLSLISTE: Befehlslisten aus befehlsliste_bot.py (D-3 Schritt 16, ab Bot 1.5.161) – ohne Netz.

Bis 1.5.160 gab es nur Text-Prüfungen von COMMAND_INFO (test_befehle). Hier laufen die Listen selbst mit dem
echten Befehlsbaum des Bots: die Offiziersliste nennt jeden Befehl, die Mitgliederliste nur Befehle "für alle"
(keine Offiziersbefehle), nach Ende der Abstimmung ohne /gildenname; _post_list bearbeitet statt neu zu posten.
"""
import asyncio
import os
import re
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Ch:
    def __init__(self):
        self.sent, self.edited, self.deleted = [], [], []

    async def send(self, text, **kw):
        self.sent.append(text)
        return types.SimpleNamespace(id=300 + len(self.sent))

    def get_partial_message(self, mid):
        ch = self

        class P:
            async def edit(self_, content=None, **kw):
                ch.edited.append(mid)

            async def delete(self_):
                ch.deleted.append(mid)
        return P()


class Befehlsliste(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["befehlsliste_bot"]

    def setUp(self):
        m = self.m
        self.saved_state, self.saved_save = dict(m.state.data), m.state.save
        m.state.save = lambda: None

    def tearDown(self):
        m = self.m
        m.state.save = self.saved_save
        m.state.data.clear()
        m.state.data.update(self.saved_state)

    def names(self, parts):
        """Slash-Befehle des Bots in der Liste (ohne die Befehle im Spiel aus ADDON_COMMAND_BLOCKS, z. B. /rm)."""
        found = set(re.findall(r"\*\*`/([^`]+)`\*\*", "\n".join(parts)))
        return found - set(re.findall(r"\*\*`/([^`]+)`\*\*", "\n".join(self.m.ADDON_COMMAND_BLOCKS)))

    def test_offiziersliste_alle_befehle(self):
        alle = {n for n, _, _ in self.m._command_entries()}
        self.assertGreaterEqual(len(alle), 49)
        self.assertEqual(self.names(self.m.command_list_text()), alle)

    def test_keine_nachricht_ueber_2000(self):
        # 1.5.162 (T-CHUNK): bis 1.5.161 hatte Teil 3 der Offiziersliste 2022 Zeichen (seit 1.5.141)
        self.m.state.data["name_poll"] = {"closed": False}
        for parts in (self.m.command_list_text(), self.m.member_command_list_text()):
            self.assertTrue(all(len(p) <= 2000 for p in parts), [len(p) for p in parts])

    def test_mitgliederliste_nur_fuer_alle(self):
        self.m.state.data["name_poll"] = {"closed": False}
        got = self.names(self.m.member_command_list_text())
        self.assertTrue(got)
        for n in got:
            self.assertEqual(self.m.COMMAND_INFO[n][0], "alle", n)
        for n in ("uploader", "pn", "update", "raid erstellen", "beute entfernen"):
            self.assertNotIn(n, got)
        self.assertIn("gildenname vorschlagen", got)
        self.m.state.data["name_poll"] = {"closed": True}
        self.assertFalse([n for n in self.names(self.m.member_command_list_text()) if n.startswith("gildenname ")])

    def test_liste_bearbeiten_statt_neu(self):
        ch = Ch()
        self.m.state.data["liste_test"] = [11, 12, 13]
        asyncio.run(self.m._post_list(ch, ["a", "b"], "liste_test"))
        self.assertEqual((ch.edited, ch.sent, ch.deleted), ([11, 12], [], [13]))
        self.assertEqual(self.m.state.data["liste_test"], [11, 12])
        asyncio.run(self.m._post_list(ch, ["a", "b", "c"], "liste_test"))
        self.assertEqual(ch.sent, ["c"])
        self.assertEqual(self.m.state.data["liste_test"], [11, 12, 301])


    def test_abgelehnter_teil_bricht_nicht_ab(self):
        # 1.5.166 (Frage Prüf-Sitzung 22:18): Senden eines Teils scheitert -> Rest wird trotzdem gepostet
        import discord
        ch = Ch()
        orig = ch.send

        async def send(text, **kw):
            if text == "b":
                raise discord.HTTPException(types.SimpleNamespace(status=400, reason="Bad Request"), "zu lang")
            return await orig(text, **kw)
        ch.send = send
        self.m.state.data["liste_test"] = []
        with self.assertLogs("raidmaster", level="WARNING") as cm:
            asyncio.run(self.m._post_list(ch, ["a", "b", "c"], "liste_test"))
        self.assertEqual(ch.sent, ["a", "c"])
        self.assertEqual(self.m.state.data["liste_test"], [301, 302])
        self.assertTrue(any("Teil 2 von 3 nicht gepostet" in x for x in cm.output))
        ch.send = orig                                                   # nächster Lauf: fehlender Teil kommt nach
        asyncio.run(self.m._post_list(ch, ["a", "b", "c"], "liste_test"))
        self.assertEqual(ch.edited, [301, 302])
        self.assertEqual(ch.sent[-1], "c")
        self.assertEqual(len(self.m.state.data["liste_test"]), 3)

    def test_offiziersliste_ueber_post_list(self):
        # 1.5.166: #befehlsliste nutzt _post_list (bis 1.5.165 eine eigene Kopie ohne Fehlerbehandlung)
        m, ch, calls = self.m, Ch(), []
        saved = (m.bot_guild, m.channel_by_id, m.ensure_member_command_list, m._post_list)

        async def by_id(cid):
            return ch

        async def members():
            return "ok"

        async def post(channel, parts, key):
            calls.append((channel, len(parts), key))
        ch.mention = "#befehlsliste"
        m.bot_guild = lambda: types.SimpleNamespace(text_channels=[], me=None)
        m.channel_by_id, m.ensure_member_command_list, m._post_list = by_id, members, post
        try:
            r = asyncio.run(m.ensure_command_list())
        finally:
            m.bot_guild, m.channel_by_id, m.ensure_member_command_list, m._post_list = saved
        self.assertEqual(calls, [(ch, len(m.command_list_text()), "command_list_messages")])
        self.assertIn("aktuell", r)


if __name__ == "__main__":
    unittest.main()
