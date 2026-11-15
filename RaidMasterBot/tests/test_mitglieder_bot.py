"""T-D3-MITGLIEDER: Mitglieder-Bereich aus mitglieder_bot.py (D-3 Schritt 17, ab Bot 1.5.163) – ohne Netz.

Bis 1.5.162 gab es dafür nur Text-Prüfungen. Hier laufen die Befehle selbst: /mitgliederbereich und /mitglied
sind angemeldet, /mitglied nur für die Gildenleitung, Aufnehmen gibt Mitglied und nimmt Gast weg (PN gesperrt
stört nicht), ohne eingerichteten Mitglieder-Bereich hält der Bot nichts dicht.
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
    def __init__(self, roles=(), dm_ok=True):
        self.roles, self.display_name, self.dm_ok = list(roles), "Neu", dm_ok
        self.dms = []

    async def add_roles(self, *roles, reason=None):
        self.roles.extend(roles)

    async def remove_roles(self, *roles, reason=None):
        self.roles = [r for r in self.roles if r not in roles]

    async def send(self, text, **kw):
        import discord
        if not self.dm_ok:
            raise discord.HTTPException(types.SimpleNamespace(status=403, reason="x"), "gesperrt")
        self.dms.append(text)


class Resp:
    def __init__(self):
        self.messages = []

    async def send_message(self, text, **kw):
        self.messages.append(text)


class Mitglieder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["mitglieder_bot"]

    def setUp(self):
        m = self.m
        self.saved = {k: getattr(m, k) for k in ("is_admin", "ensure_member_role", "bot_guild")}
        self.saved_cfg = dict(m.cfg)
        self.mitglied, self.gast = Role(m.member_area.MEMBER_ROLE), Role(m.member_area.GUEST_ROLE)

        async def role(guild):
            return self.mitglied
        m.ensure_member_role = role

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        m.cfg.clear()
        m.cfg.update(self.saved_cfg)

    def test_angemeldet(self):
        tree = self.bot.bot.tree
        self.assertIs(tree.get_command("mitgliederbereich"), self.m.mitgliederbereich_group)
        self.assertIs(tree.get_command("mitglied"), self.m.mitglied_group)
        self.assertEqual(sorted(c.name for c in self.m.mitglied_group.commands), ["aufnehmen", "entfernen"])
        self.assertIs(sys.modules["anmeldung_bot"].handle_apply_button, self.m.handle_apply_button)

    def test_nur_gildenleitung(self):
        self.m.is_admin = lambda u: False
        for cmd, arg in ((self.m.member_add_cmd, Member()), (self.m.member_remove_cmd, Member()),
                         (self.m.member_area_cmd, True)):
            r = Resp()
            asyncio.run(cmd.callback(types.SimpleNamespace(user=1, response=r), arg))
            self.assertIn("nur der Gildenchef und die Offiziere", r.messages[0], cmd.name)

    def test_aufnehmen_mitglied_statt_gast(self):
        guild = types.SimpleNamespace(roles=[self.mitglied, self.gast], name="Gilde")
        for dm_ok in (True, False):
            wer = Member(roles=[self.gast], dm_ok=dm_ok)
            r = asyncio.run(self.m.admit_member(guild, wer, "Chef"))
            self.assertEqual(wer.roles, [self.mitglied])
            self.assertIn("ist jetzt **Mitglied**", r)
            self.assertEqual(len(wer.dms), 1 if dm_ok else 0)            # gesperrte PN stört nicht

    def test_ohne_bereich_nichts_dicht(self):
        self.m.cfg["member_area"] = False
        self.m.bot_guild = lambda: object()
        self.assertEqual(asyncio.run(self.m.maintain_member_area()), [])
        self.m.cfg["member_area"] = True
        self.m.bot_guild = lambda: types.SimpleNamespace(me=types.SimpleNamespace(
            guild_permissions=types.SimpleNamespace(manage_roles=False, manage_channels=True)))
        self.assertEqual(asyncio.run(self.m.maintain_member_area()), [])    # ohne Rechte nichts versuchen


if __name__ == "__main__":
    unittest.main()
