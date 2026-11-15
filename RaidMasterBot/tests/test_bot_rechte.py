"""T-UP404: Bot meldet fehlenden Server/Rechte, meldet Befehle nach Einladung an, Rolle ohne Administrator (Bot 1.5.143)."""
import asyncio
import os
import sys
import types
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import discord  # noqa: E402
import bot_rechte as br  # noqa: E402


def perms(**kw):
    return discord.Permissions(**kw)


ALL = {n: True for n in br.NEEDED}


class Pruefung(unittest.TestCase):
    def test_kein_server(self):
        r = br.start_check([], "1", lambda g: perms())
        self.assertEqual(r[0][0], "fehler")
        self.assertTrue(r[0][1].startswith("Bot nicht auf dem Server"))

    def test_falscher_server(self):
        g = types.SimpleNamespace(id=2)
        r = br.start_check([g], "1", lambda g: perms(**ALL))
        self.assertEqual(r[0][0], "fehler")
        self.assertIn("eingestellten Gilden-Server", r[0][1])

    def test_alles_da_ohne_admin(self):
        g = types.SimpleNamespace(id=1)
        self.assertEqual(br.start_check([g], "1", lambda g: perms(**ALL)), [])
        self.assertEqual(br.start_check([g], None, lambda g: perms(**ALL)), [])

    def test_fehlende_rechte(self):
        g = types.SimpleNamespace(id=1)
        p = dict(ALL, manage_webhooks=False, attach_files=False)
        r = br.start_check([g], "1", lambda g: perms(**p))
        self.assertEqual(r[0][0], "warnung")
        self.assertIn("attach_files (Dateien anhängen", r[0][1])
        self.assertIn("manage_webhooks (Uploader-Webhooks anlegen)", r[0][1])

    def test_admin_hinweis(self):
        g = types.SimpleNamespace(id=1)
        r = br.start_check([g], "1", lambda g: perms(administrator=True))
        self.assertEqual([x[0] for x in r], ["hinweis"])               # mit Admin fehlt nichts, aber zu viel
        self.assertIn("Administrator", r[0][1])

    def test_einladungszahl_ohne_admin(self):
        v = br.permissions_value()
        p = discord.Permissions(v)
        self.assertFalse(p.administrator)
        for n in br.NEEDED:
            self.assertTrue(getattr(p, n), n)
        self.assertFalse(p.ban_members or p.kick_members)

    def test_audit(self):
        role_hi = types.SimpleNamespace(name="Gildenchef", position=10)
        role_lo = types.SimpleNamespace(name="Offizier", position=5)
        everyone = types.SimpleNamespace(name="@everyone", position=0)
        t = datetime(2026, 11, 15, 0, 20, tzinfo=timezone.utc)
        def e(action, target, reason=None, roles=(role_lo,)):
            return types.SimpleNamespace(action=types.SimpleNamespace(name=action),
                                         target=types.SimpleNamespace(id=target),
                                         user=types.SimpleNamespace(roles=[everyone, *roles]), reason=reason, created_at=t)
        lines = br.audit_summary([e("kick", 99, roles=(role_lo, role_hi)), e("bot_add", 99, "zurück"),
                                  e("kick", 5), e("message_delete", 99)], 99)
        self.assertEqual(lines, ["15.11.2026 00:20 UTC – vom Server entfernt – durch Rolle „Gildenchef“ – Grund: "
                                 "keiner angegeben",
                                 "15.11.2026 00:20 UTC – eingeladen – durch Rolle „Offizier“ – Grund: zurück"])

    def test_privat_ohne_freigabe(self):
        everyone, botrole, me = object(), object(), types.SimpleNamespace()
        me.roles = [everyone, botrole]
        def ch(ev=None, mev=None, rev=None):
            ow = {id(everyone): ev, id(me): mev, id(botrole): rev}
            return types.SimpleNamespace(overwrites_for=lambda x: types.SimpleNamespace(view_channel=ow.get(id(x))))
        self.assertFalse(br.needs_explicit(ch(), me, everyone))                       # öffentlich
        self.assertTrue(br.needs_explicit(ch(ev=False), me, everyone))                # privat, Bot nur über Admin
        self.assertFalse(br.needs_explicit(ch(ev=False, mev=True), me, everyone))     # Bot freigegeben
        self.assertFalse(br.needs_explicit(ch(ev=False, rev=True), me, everyone))     # Bot-Rolle freigegeben


class BotAblauf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["rechte_bot"]      # D-3 Schritt 5: check_bot_rights steht in rechte_bot.py – dort patchen

    def setUp(self):
        b, m = self.bot, self.m
        self.saved = (m.post_bot_log, m.bot_guild, dict(b.state.data), dict(b.cfg))
        self.posts = []

        async def post(t):
            self.posts.append(t)
        m.post_bot_log = post

    def tearDown(self):
        b, m = self.bot, self.m
        m.post_bot_log, m.bot_guild = self.saved[:2]
        b.state.data.clear()
        b.state.data.update(self.saved[2])
        b.cfg.clear()
        b.cfg.update(self.saved[3])
        b.bot._connection._guilds = {}

    def guild(self, p, channels=()):
        me = types.SimpleNamespace(guild_permissions=p, roles=[], id=1)
        g = types.SimpleNamespace(id=7, me=me, default_role=object(), categories=[], channels=list(channels))
        return g

    def test_meldet_einmal(self):
        b = self.bot
        g = self.guild(perms(**dict(ALL, manage_webhooks=False)))
        b.bot._connection._guilds = {7: g}
        b.cfg["guild_id"] = "7"
        self.m.bot_guild = lambda: g
        b.state.data.pop("rechte_meldung", None)
        with self.assertLogs("raidmaster", level="WARNING"):
            asyncio.run(b.check_bot_rights("Start"))
        self.assertEqual(len(self.posts), 1)
        self.assertIn("manage_webhooks", self.posts[0])
        asyncio.run(b.check_bot_rights("Start"))                         # unverändert: kein zweiter Beitrag
        self.assertEqual(len(self.posts), 1)

    def test_kein_server_nur_protokoll(self):
        b = self.bot
        b.bot._connection._guilds = {}
        with self.assertLogs("raidmaster", level="ERROR") as cm:
            r = asyncio.run(b.check_bot_rights("Start"))
        self.assertEqual(r[0][0], "fehler")
        self.assertTrue(any("Bot nicht auf dem Server" in x for x in cm.output))
        self.assertEqual(self.posts, [])

    def test_einladung_meldet_befehle_an(self):
        b = self.bot
        calls = []
        orig_copy, orig_sync = b.bot.tree.copy_global_to, b.bot.tree.sync
        b.bot.tree.copy_global_to = lambda guild: calls.append(("copy", guild.id))

        async def sync(guild=None):
            calls.append(("sync", guild.id))
        b.bot.tree.sync = sync
        g = self.guild(perms(**ALL))
        b.bot._connection._guilds = {7: g}
        b.cfg["guild_id"] = "7"
        self.m.bot_guild = lambda: g
        try:
            asyncio.run(b.bot.on_guild_join(g))
        finally:
            b.bot.tree.copy_global_to, b.bot.tree.sync = orig_copy, orig_sync
        self.assertEqual(calls, [("copy", 7), ("sync", 7)])

    def test_private_kanaele_freigeben(self):
        b = self.bot
        everyone = object()
        set_calls = []

        class Ch:
            def __init__(self, name, private):
                self.name, self.private = name, private

            def overwrites_for(self, x):
                return types.SimpleNamespace(view_channel=False if (self.private and x is everyone) else None)

            async def set_permissions(self, target, reason=None, **kw):
                set_calls.append((self.name, kw.get("view_channel")))
        g = self.guild(perms(administrator=True), [Ch("offiziere", True), Ch("allgemein", False)])
        g.default_role = everyone
        g.me.roles = [everyone]
        g.me.guild_permissions = perms(administrator=True, view_audit_log=False)
        b.bot._connection._guilds = {7: g}
        b.cfg["guild_id"] = "7"
        self.m.bot_guild = lambda: g
        b.state.data.pop("bot_private_granted", None)
        asyncio.run(b.check_bot_rights("Start"))
        self.assertEqual(set_calls, [("offiziere", True)])
        asyncio.run(b.check_bot_rights("Start"))                         # nur einmal
        self.assertEqual(len(set_calls), 1)
        self.assertTrue(any("Administrator“ bei der Rolle des Bots aus" in p for p in self.posts))


if __name__ == "__main__":
    unittest.main()
