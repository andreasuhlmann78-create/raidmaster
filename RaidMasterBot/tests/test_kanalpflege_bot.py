"""T-D3-KANALPFLEGE: kanalpflege_bot.py (D-3 Schritt 30, ab Bot 1.5.177) – ohne Netz.

Bis 1.5.176 gab es dafür keine Ablauf-Tests. Wichtig (Entscheid des Nutzers): ein einmal geleerter Kanal (z. B.
#mc-dkp) wird NIE wieder geleert – der Merker im state verhindert es, auch nach dem Verschieben in ein Modul.
Sprachkanäle: Grenze wird nur gesetzt, wenn sie abweicht; ohne Recht "Kanäle verwalten" nichts.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Kanalpflege(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["kanalpflege_bot"]

    def setUp(self):
        m = self.m
        self.saved = (m.bot_guild, dict(m.state.data), m.state.save, m.server_setup.clear_channel, dict(m.cfg))
        m.state.save = lambda: None
        self.cleared = []

        async def clear(ch, before, reason):
            self.cleared.append(ch.name)
            return 3
        m.server_setup.clear_channel = clear

    def tearDown(self):
        m = self.m
        m.bot_guild = self.saved[0]
        m.state.data.clear()
        m.state.data.update(self.saved[1])
        m.state.save, m.server_setup.clear_channel = self.saved[2], self.saved[3]
        m.cfg.clear()
        m.cfg.update(self.saved[4])

    def test_gleiche_funktionen_in_bot(self):
        for name in ("clear_channels_once", "ensure_channel_texts", "ensure_listed_raid_categories",
                     "ensure_new_raid_categories", "ensure_voice_limits", "remove_unused_channels_once",
                     "sync_raid_visibility"):
            self.assertIs(getattr(self.bot, name), getattr(self.m, name), name)

    def test_heute_nichts_zu_leeren(self):
        # Stand 1.5.177: CLEAR_CHANNELS_ONCE ist leer (#mc-dkp erledigt, seit Bot 1.5.109) – es wird nichts geleert
        self.assertEqual(self.m.server_setup.CLEAR_CHANNELS_ONCE, {})
        perms = types.SimpleNamespace(manage_messages=True, read_message_history=True)
        chans = [types.SimpleNamespace(name="mc-dkp", id=1, permissions_for=lambda me: perms)]
        self.m.bot_guild = lambda: types.SimpleNamespace(text_channels=chans, me=object())
        self.assertEqual(asyncio.run(self.m.clear_channels_once()), [])
        self.assertEqual(self.cleared, [])

    def test_einmal_geleert_nie_wieder(self):
        # mit einem Test-Eintrag: einmal geleert, Merker gesetzt, zweiter Lauf leert NICHT
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Europe/Zurich"))
        saved = self.m.server_setup.CLEAR_CHANNELS_ONCE
        self.m.server_setup.CLEAR_CHANNELS_ONCE = {"test-kanal": {"tag": "t1", "before": now,
                                                                  "until": now + timedelta(hours=1)}}
        perms = types.SimpleNamespace(manage_messages=True, read_message_history=True)
        chans = [types.SimpleNamespace(name="Test-Kanal", id=1, permissions_for=lambda me: perms)]
        self.m.bot_guild = lambda: types.SimpleNamespace(text_channels=chans, me=object())
        self.m.state.data["cleared_channels"] = {}
        try:
            first = asyncio.run(self.m.clear_channels_once())
            second = asyncio.run(self.m.clear_channels_once())
        finally:
            self.m.server_setup.CLEAR_CHANNELS_ONCE = saved
        self.assertEqual(self.cleared, ["Test-Kanal"])
        self.assertIn("Das passiert nie wieder", first[0])
        self.assertEqual(second, [])
        self.assertEqual(self.m.state.data["cleared_channels"], {"test-kanal": "t1"})

    def test_sprachkanal_grenze(self):
        import discord
        edits = []

        class Voice(discord.VoiceChannel):
            def __init__(self, name, limit):
                self._name, self.user_limit = name, limit

            @property
            def name(self):
                return self._name

            async def edit(self, user_limit=None, reason=None):
                edits.append((self._name, user_limit))
        mc, bwl = Voice("MC", 40), Voice("BWL", 10)
        chans = {1: mc, 2: bwl}
        self.m.cfg["raid_channels"] = {"mc": {"voice": 1}, "bwl": {"voice": 2}}
        perms = types.SimpleNamespace(manage_channels=True)
        self.m.bot_guild = lambda: types.SimpleNamespace(me=types.SimpleNamespace(guild_permissions=perms),
                                                         get_channel=lambda cid: chans.get(cid))
        out = asyncio.run(self.m.ensure_voice_limits())
        size = self.m.server_setup.raid_size
        expected = [(n, size(k, self.m.cfg)) for n, k, cur in (("MC", "mc", 40), ("BWL", "bwl", 10))
                    if size(k, self.m.cfg) != cur]
        self.assertEqual(edits, expected)
        self.assertEqual(len(out), len(expected))
        perms.manage_channels = False
        edits.clear()
        self.assertEqual(asyncio.run(self.m.ensure_voice_limits()), [])
        self.assertEqual(edits, [])


if __name__ == "__main__":
    unittest.main()
