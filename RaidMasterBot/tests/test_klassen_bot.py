"""T-D3-KLASSEN: Klassenfarben aus klassen_bot.py (D-3 Schritt 13, ab Bot 1.5.158) – Ablauf ohne Netz.

Bis 1.5.157 gab es für die Klassenrollen keinen Test. Hier laufen member_class und sync_class_roles selbst:
Klasse aus Profil vor Name, Name aus RaidMaster-Daten (auch "Name (Zusatz)"), Rolle anlegen, falsche
Klassenrolle entfernen, Bots nie, ohne Recht "Rollen verwalten" nichts.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Role:
    def __init__(self, rid, name, position=1, colour=None):
        self.id, self.name, self.position, self.colour = rid, name, position, colour

    def __lt__(self, other):
        return self.position < other.position


class Member:
    def __init__(self, mid, name, bot=False, roles=()):
        self.id, self.name, self.nick, self.global_name, self.bot = mid, name, None, None, bot
        self.roles = list(roles)

    async def add_roles(self, *roles, reason=None):
        self.roles.extend(roles)

    async def remove_roles(self, *roles, reason=None):
        self.roles = [r for r in self.roles if r not in roles]


class Guild:
    def __init__(self, members, manage_roles=True):
        self.members = members
        self.roles = []
        self.me = types.SimpleNamespace(guild_permissions=types.SimpleNamespace(manage_roles=manage_roles),
                                        top_role=Role(1, "Bot", position=50))
        self.created = []

    def get_role(self, rid):
        return next((r for r in self.roles if r.id == rid), None)

    async def create_role(self, name, colour=None, **kw):
        r = Role(100 + len(self.roles), name, colour=colour)
        self.roles.append(r)
        self.created.append(name)
        return r

    async def edit_role_positions(self, positions):
        pass


class Klassen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["klassen_bot"]

    def setUp(self):
        m = self.m
        self.saved = (m.bot_guild, m.save_config, dict(m.cfg), m.book.profile)
        self.saved_dkp = getattr(m.bot, "dkp_data", None)
        m.save_config = lambda: None
        m.cfg.pop("class_roles", None)
        m.book.profile = lambda uid: {"cls": "PRIEST"} if uid == 3 else None
        m.bot.dkp_data = {"players": {"Thrall": {"c": "SHAMAN"}, "Jaina": {"c": "mage"}}}

    def tearDown(self):
        m = self.m
        m.bot_guild, m.save_config = self.saved[:2]
        m.cfg.clear()
        m.cfg.update(self.saved[2])
        m.book.profile = self.saved[3]
        m.bot.dkp_data = self.saved_dkp

    def test_gleiche_funktion_in_bot(self):
        self.assertIs(self.bot.sync_class_roles, self.m.sync_class_roles)

    def test_klasse_finden(self):
        players = self.m.bot.dkp_data["players"]
        self.assertEqual(self.m.member_class(Member(1, "thrall"), players), "SHAMAN")
        self.assertEqual(self.m.member_class(Member(2, "Jaina (Twink)"), players), "MAGE")
        self.assertEqual(self.m.member_class(Member(3, "Thrall"), players), "PRIEST")   # Profil zuerst
        self.assertIsNone(self.m.member_class(Member(4, "Unbekannt"), players))

    def test_rollen_vergeben_und_falsche_entfernen(self):
        alt = Role(77, "Krieger")
        self.m.cfg["class_roles"] = {"WARRIOR": 77}
        thrall, jaina, bot = Member(1, "Thrall", roles=[alt]), Member(2, "Jaina"), Member(9, "Thrall", bot=True)
        g = Guild([thrall, jaina, bot])
        g.roles.append(alt)
        self.m.bot_guild = lambda: g
        n = asyncio.run(self.m.sync_class_roles())
        self.assertEqual(n, 3)                               # Thrall: alte weg + neue dazu; Jaina: neue dazu
        self.assertNotIn(alt, thrall.roles)
        self.assertEqual([r.name for r in thrall.roles], [g.get_role(self.m.cfg["class_roles"]["SHAMAN"]).name])
        self.assertEqual(len(jaina.roles), 1)
        self.assertEqual(bot.roles, [])                      # Bots nie
        self.assertEqual(asyncio.run(self.m.sync_class_roles()), 0)   # alles richtig: keine Änderung
        self.assertEqual(len(g.created), 2)                  # je Klasse nur einmal angelegt

    def test_ohne_recht_nichts(self):
        g = Guild([Member(1, "Thrall")], manage_roles=False)
        self.m.bot_guild = lambda: g
        self.assertEqual(asyncio.run(self.m.sync_class_roles()), 0)
        self.assertEqual(g.created, [])


if __name__ == "__main__":
    unittest.main()
