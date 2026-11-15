"""T-D3-EINRICHTEN: einrichten_bot.py (D-3 Schritt 35, ab Bot 1.5.182) – /raidmaster-einrichten ohne Netz.

Bis 1.5.181 gab es für den Befehl selbst keinen Ablauf-Test (test_setup_aliases prüft nur server_setup). Hier:
der Befehl ist am Bot angemeldet; nur Gildenchef/Offiziere; fehlen dem Bot Rechte, werden genau diese genannt und
nichts eingerichtet; verweigert Discord eine Aktion, kommt der Hinweis zur Rollen-Reihenfolge; sonst laufen
Einrichtung, Addon-Version, Willkommen, Befehlsliste und DKP-Regeln, und der Bericht kommt in Teilen zu
höchstens 1900 Zeichen.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Antwort:
    def __init__(self):
        self.messages, self.deferred = [], False

    async def send_message(self, text, **kw):
        self.messages.append(text)

    async def defer(self, **kw):
        self.deferred = True


class Folge:
    def __init__(self):
        self.messages = []

    async def send(self, text, **kw):
        self.messages.append(text)


def inter(channels=True, roles=True):
    perms = types.SimpleNamespace(manage_channels=channels, manage_roles=roles)
    guild = types.SimpleNamespace(me=types.SimpleNamespace(guild_permissions=perms))
    return types.SimpleNamespace(user="Chef", guild=guild, response=Antwort(), followup=Folge())


class Einrichten(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["einrichten_bot"]

    def setUp(self):
        m = self.m
        names = ("is_admin", "save_config", "check_addon_release", "ensure_welcome", "ensure_command_list",
                 "ensure_dkp_rules")
        self.saved = {k: getattr(m, k) for k in names}
        self.saved_run, self.saved_cfg, self.saved_dkp = m.server_setup.run_setup, dict(m.cfg), m.bot.dkp_data
        self.calls = []
        m.is_admin = lambda u: True
        m.save_config = lambda: self.calls.append("save")

        async def rel():
            self.calls.append("addon")

        async def welcome(update=False):
            self.calls.append(("welcome", update))
            return "Willkommen ok"

        async def cmdlist():
            self.calls.append("befehle")
            return "Befehle ok"

        async def rules():
            self.calls.append("regeln")
            return ["Regeln ok"]

        async def run_setup(guild, member, cfg, settings, extra):
            self.calls.append(("setup", settings, extra))
            return ["x" * 1000, "y" * 1500]
        m.check_addon_release, m.ensure_welcome, m.ensure_command_list, m.ensure_dkp_rules = rel, welcome, cmdlist, rules
        m.server_setup.run_setup = run_setup
        m.bot.dkp_data = None

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        m.server_setup.run_setup, m.bot.dkp_data = self.saved_run, self.saved_dkp
        m.cfg.clear()
        m.cfg.update(self.saved_cfg)

    def run_cmd(self, i):
        asyncio.run(self.m.setup_cmd.callback(i))
        return i

    def test_am_bot_angemeldet(self):
        self.assertIs(self.bot.bot.tree.get_command("raidmaster-einrichten").callback, self.m.setup_cmd.callback)

    def test_nur_gildenleitung(self):
        self.m.is_admin = lambda u: False
        i = self.run_cmd(inter())
        self.assertIn("nur der Gildenchef und die Offiziere", i.response.messages[0])
        self.assertEqual(self.calls, [])

    def test_fehlende_rechte_genannt(self):
        i = self.run_cmd(inter(channels=False))
        self.assertIn("**Kanäle verwalten**", i.response.messages[0])
        self.assertNotIn("Rollen verwalten", i.response.messages[0])
        self.assertFalse(i.response.deferred)
        self.assertEqual(self.calls, [])

    def test_ablauf_und_bericht_in_teilen(self):
        i = self.run_cmd(inter())
        self.assertTrue(i.response.deferred)
        self.assertEqual([c if isinstance(c, str) else c[0] for c in self.calls],
                         ["setup", "save", "addon", "welcome", "befehle", "regeln"])
        self.assertEqual(self.calls[3], ("welcome", True))
        text = "\n".join(["x" * 1000, "y" * 1500, "Willkommen ok", "Befehle ok", "Regeln ok"])
        self.assertEqual("".join(i.followup.messages), text)
        self.assertTrue(all(len(p) <= 1900 for p in i.followup.messages))
        self.assertEqual(len(i.followup.messages), 2)
        self.assertIn("raid_names", self.m.cfg)

    def test_discord_verweigert(self):
        import discord

        async def verboten(*a):
            raise discord.Forbidden(types.SimpleNamespace(status=403, reason="x"), "nein")
        self.m.server_setup.run_setup = verboten
        i = self.run_cmd(inter())
        self.assertIn("möglichst weit oben", i.followup.messages[0])
        self.assertEqual(len(i.followup.messages), 1)
        self.assertNotIn("save", self.calls)


if __name__ == "__main__":
    unittest.main()
