"""Offline-Tests Bot 1.5.110: dauerhafte Einladung für #willkommen (/einladung, einmalige Meldung in #befehlsliste).
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import os
import re
import sys
import unittest

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BOT_DIR)
import discord  # noqa: E402
import invites  # noqa: E402


def src(name):
    with open(os.path.join(BOT_DIR, name), encoding="utf-8") as f:
        return f.read()


class Perms:
    def __init__(self, manage_guild=True, create_instant_invite=True):
        self.manage_guild = manage_guild
        self.create_instant_invite = create_instant_invite


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class Invite:
    def __init__(self, code, channel, max_age=0):
        self.code, self.url, self.channel, self.max_age = code, f"https://discord.gg/{code}", channel, max_age
        self.deleted = False

    async def delete(self, reason=None):        # darf nie aufgerufen werden
        self.deleted = True
        raise AssertionError("Einladung gelöscht")

    async def edit(self, **kw):                  # gibt es bei Einladungen nicht – trotzdem nie aufrufen
        raise AssertionError("Einladung geändert")


class Channel:
    def __init__(self, name, guild, can_invite=True):
        self.name, self.guild, self.can_invite = name, guild, can_invite
        self.created = []
        self.sent = []

    def permissions_for(self, member):
        return Perms(create_instant_invite=self.can_invite)

    async def create_invite(self, **kw):
        if not self.can_invite:
            raise discord.Forbidden(Obj(status=403, reason="Forbidden"), "Missing Permissions")
        self.created.append(kw)
        inv = Invite(f"neu{len(self.created)}", self, kw.get("max_age"))
        self.guild.invite_list.append(inv)
        return inv

    async def send(self, *a, **kw):
        self.sent.append(a)


class Guild:
    def __init__(self, names=("willkommen", "befehlsliste", "pug-anmeldung"), manage_guild=True, can_invite=True):
        self.name = "Testgilde"
        self.text_channels = [Channel(n, self, can_invite) for n in names]
        self.invite_list = []
        self.me = Obj(guild_permissions=Perms(manage_guild=manage_guild))
        self.invites_calls = 0

    async def invites(self):
        self.invites_calls += 1
        return list(self.invite_list)


def fetcher(guild, expires=None):
    calls = []

    async def fetch_invite(code, with_expiration=True):
        calls.append((code, with_expiration))
        inv = next((i for i in guild.invite_list if i.code == code), None)
        if inv is None:
            raise discord.NotFound(Obj(status=404, reason="Not Found"), "Unknown Invite")
        return Obj(code=code, guild=Obj(name=guild.name), channel=Obj(name=inv.channel.name), expires_at=expires)
    fetch_invite.calls = calls
    return fetch_invite


def run(c):
    return asyncio.run(c)


class Einladung(unittest.TestCase):
    def test_e01_neu_dauerhaft(self):
        g = Guild()
        data = {}
        res = run(invites.ensure_welcome_invite(g, data, fetcher(g), "Andreas"))
        ch = g.text_channels[0]
        self.assertEqual(len(ch.created), 1)
        kw = ch.created[0]
        self.assertEqual((kw["max_age"], kw["max_uses"], kw["temporary"], kw["unique"]), (0, 0, False, True))
        self.assertIn("Dauerhafte Einladung #willkommen (Andreas)", kw["reason"])
        self.assertEqual(data["welcome_invite_code"], "neu1")
        self.assertEqual(data["welcome_invite_url"], "https://discord.gg/neu1")
        self.assertTrue(res["ok"] and res["created"])
        self.assertIn("läuft ab: **nie**", res["lines"][0])
        self.assertIn("Kanal **#willkommen**", res["lines"][0])
        self.assertEqual([c.created for c in g.text_channels[1:]], [[], []])   # nur #willkommen

    def test_e02_gespeichert_kein_neuer(self):
        g = Guild()
        data = {}
        run(invites.ensure_welcome_invite(g, data, fetcher(g), "A"))
        res = run(invites.ensure_welcome_invite(g, data, fetcher(g), "B"))
        self.assertEqual(len(g.text_channels[0].created), 1)
        self.assertFalse(res["created"])
        self.assertTrue(res["ok"])
        self.assertIn("kein neuer Link", invites.invite_text(res))
        # ohne "Server verwalten": gespeicherter Code über fetch_invite geprüft, auch dann kein neuer
        g.me.guild_permissions.manage_guild = False
        res = run(invites.ensure_welcome_invite(g, data, fetcher(g), "C"))
        self.assertEqual(len(g.text_channels[0].created), 1)
        self.assertFalse(res["created"])

    def test_e03_gespeicherter_weg_neu(self):
        g = Guild()
        data = {"welcome_invite_code": "alt", "welcome_invite_url": "https://discord.gg/alt"}
        res = run(invites.ensure_welcome_invite(g, data, fetcher(g), "A"))
        self.assertTrue(res["created"])
        self.assertEqual(data["welcome_invite_code"], "neu1")

    def test_e04_kein_kanal(self):
        g = Guild(names=("allgemein", "befehlsliste"))
        data = {}
        res = run(invites.ensure_welcome_invite(g, data, fetcher(g), "A"))
        self.assertFalse(res["ok"])
        self.assertIn("nicht gefunden", res["lines"][0])
        self.assertEqual(data, {})
        self.assertEqual(sum(len(c.created) for c in g.text_channels), 0)

    def test_e05_ohne_recht(self):
        g = Guild(can_invite=False)
        res = run(invites.ensure_welcome_invite(g, {}, fetcher(g), "A"))
        self.assertFalse(res["ok"])
        self.assertIn("Einladung erstellen", res["lines"][0])

    def test_e06_ablauf_erkannt(self):
        g = Guild()
        res = run(invites.ensure_welcome_invite(g, {}, fetcher(g, expires="2026-11-16"), "A"))
        self.assertFalse(res["ok"])
        self.assertIn("bitte ansehen", res["lines"][0])

    def test_e07_nie_loeschen_oder_aendern(self):
        g = Guild()
        other = Invite("fremd", g.text_channels[2])
        g.invite_list.append(other)
        run(invites.ensure_welcome_invite(g, {}, fetcher(g), "A"))
        self.assertFalse(other.deleted)
        for name in ("invites.py",):
            code = src(name)
            self.assertNotIn(".delete(", code, name)
            self.assertNotIn(".edit(", code, name)
            self.assertNotIn("config", re.sub(r'"""[\s\S]*?"""', "", code).replace("cfg", ""), name)
        bot = src("bot.py")
        body = bot[bot.index("async def welcome_invite_cmd"):bot.index("OLD_WELCOME_START = ")]
        for bad in (".delete(", ".edit(", "save_config(", "create_text_channel", "create_role", "welcome_channel_id"):
            self.assertNotIn(bad, body, bad)
        self.assertIn('state.data["welcome_invite_posted"] = True', body)
        self.assertIn("befehlsliste", body)
        self.assertEqual(body.count("channel.send("), 1)

    def test_e08_befehl_und_start(self):
        bot = src("bot.py")
        self.assertIn('@bot.tree.command(name="einladung"', bot)
        body = bot[bot.index("async def welcome_invite_cmd"):bot.index("async def post_welcome_invite_once")]
        self.assertLess(body.index("if not is_creator(inter.user)"), body.index("ensure_welcome_invite"))
        self.assertIn("ephemeral=True", body)
        self.assertIn('"einladung": ("Gildenleitung", "Server")', bot)
        self.assertIn("await post_welcome_invite_once()", bot)
        self.assertIn("'invites'", src(os.path.join("..", ".github", "workflows", "bot-tests.yml")))


if __name__ == "__main__":
    unittest.main()
