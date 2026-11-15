"""T-D3-PUG: PUG-Einladung aus pug_bot.py (D-3 Schritt 22, ab Bot 1.5.169) – ohne Netz.

Bis 1.5.168 gab es dafür keinen Ablauf-Test. Hier läuft handle_member_join selbst: nur wer über den PUG-Link
beitritt, bekommt die Rolle Gast (und eine PN); andere Links, Bots und fremde Server nicht; der Zähler der
Einladungen wird nachgeführt.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Role:
    def __init__(self, name):
        self.name = name


class Member:
    def __init__(self, guild, bot=False):
        self.guild, self.bot, self.roles, self.dms = guild, bot, [], []

    async def add_roles(self, *roles, reason=None):
        self.roles.extend(roles)

    async def send(self, text, **kw):
        self.dms.append(text)


class Pug(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["pug_bot"]

    def setUp(self):
        m = self.m
        self.saved = (m.fetch_invite_uses, dict(m.cfg), getattr(m.bot, "invite_uses", None))
        m.cfg.update({"guild_id": "7", "pug_invite_code": "PUG1"})
        m.cfg.pop("pug_channel_id", None)
        self.guild = types.SimpleNamespace(id=7, roles=[Role("Gast")], name="Gilde")
        self.after = {}

        async def uses(guild):
            return dict(self.after)
        m.fetch_invite_uses = uses

    def tearDown(self):
        m = self.m
        m.fetch_invite_uses = self.saved[0]
        m.cfg.clear()
        m.cfg.update(self.saved[1])
        m.bot.invite_uses = self.saved[2]

    def join(self, before, after, member):
        self.m.bot.invite_uses = dict(before)
        self.after = after
        asyncio.run(self.m.handle_member_join(member))

    def test_gleiche_funktionen_in_bot(self):
        self.assertIs(self.bot.handle_member_join, self.m.handle_member_join)
        self.assertIs(self.bot.refresh_invite_cache, self.m.refresh_invite_cache)

    def test_ueber_pug_link_gast(self):
        mem = Member(self.guild)
        self.join({"PUG1": 3, "ALLG": 5}, {"PUG1": 4, "ALLG": 5}, mem)
        self.assertEqual([r.name for r in mem.roles], ["Gast"])
        self.assertEqual(len(mem.dms), 1)
        self.assertEqual(self.m.bot.invite_uses, {"PUG1": 4, "ALLG": 5})       # Zähler nachgeführt

    def test_anderer_link_bot_fremder_server_nichts(self):
        mem = Member(self.guild)
        self.join({"PUG1": 3, "ALLG": 5}, {"PUG1": 3, "ALLG": 6}, mem)        # normaler Link
        self.assertEqual((mem.roles, mem.dms), ([], []))
        b = Member(self.guild, bot=True)
        self.join({"PUG1": 3}, {"PUG1": 4}, b)
        self.assertEqual(b.roles, [])
        fremd = Member(types.SimpleNamespace(id=99, roles=[Role("Gast")], name="X"))
        self.join({"PUG1": 3}, {"PUG1": 4}, fremd)
        self.assertEqual(fremd.roles, [])

    def test_zwei_links_gleichzeitig_nicht_raten(self):
        mem = Member(self.guild)
        self.join({"PUG1": 3, "ALLG": 5}, {"PUG1": 4, "ALLG": 6}, mem)        # nicht eindeutig: keine Rolle
        self.assertEqual(mem.roles, [])


if __name__ == "__main__":
    unittest.main()
