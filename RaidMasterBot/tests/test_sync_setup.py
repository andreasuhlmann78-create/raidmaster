"""Offline-Tests Bot 1.5.113: /uploader legt für den Abgleich PC/Laptop einen privaten Kanal, einen Webhook und eine
Index-Nachricht an und liefert sync_config.json. Der Bot liest #sync-daten nie.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import os
import sys
import unittest

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BOT_DIR)
import discord  # noqa: E402
import uploader_setup as us  # noqa: E402


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class Hook:
    n = 700

    def __init__(self, name):
        Hook.n += 1
        self.id, self.name, self.token = Hook.n, name, "tok"
        self.url = f"https://discord.invalid/api/webhooks/{self.id}/tok"
        self.sent = []

    async def send(self, content, wait=False, **kw):
        Hook.n += 1
        self.sent.append(content)
        return Obj(id=Hook.n)

    async def fetch_message(self, mid):
        if mid not in [x for x in getattr(self, "known", [])]:
            raise discord.NotFound(Obj(status=404, reason="Not Found"), "Unknown Message")
        return Obj(id=mid)


class Channel:
    n = 300

    def __init__(self, name, overwrites=None, category=None):
        Channel.n += 1
        self.id, self.name, self.overwrites, self.category, self.hooks = Channel.n, name, overwrites, category, []
        self.read = 0

    async def webhooks(self):
        return list(self.hooks)

    async def create_webhook(self, name, reason=None):
        h = Hook(name)
        self.hooks.append(h)
        return h

    def permissions_for(self, m):
        return Obj(manage_webhooks=True)

    def history(self, *a, **k):                       # darf nie aufgerufen werden
        raise AssertionError("Bot liest #sync-daten")


class Guild:
    def __init__(self):
        self.text_channels = [Channel("sync-daten")]       # schon vergeben (z. B. von Hand angelegt)
        self.categories = [Obj(name="🔒 OFFIZIERE", id=1)]
        self.default_role = Obj(name="@everyone", id=0)
        self.me = Obj(name="Bot", id=1, guild_permissions=Obj(manage_channels=True))

    async def create_text_channel(self, name, category=None, overwrites=None, topic=None, reason=None):
        ch = Channel(name, overwrites, category)
        self.text_channels.append(ch)
        return ch


def run(c):
    return asyncio.run(c)


class SyncSetup(unittest.TestCase):
    def test_s1_privater_kanal_webhook_index(self):
        g, user, cfg = Guild(), Obj(name="Spieler", id=42), {}
        conf, notes = run(us.setup_sync(g, user, cfg))
        self.assertEqual(notes, [])
        ch = g.text_channels[-1]
        self.assertEqual(ch.name, "sync-daten-2")
        ow = ch.overwrites
        self.assertIs(ow[g.default_role].view_channel, False)
        self.assertIs(ow[user].view_channel, True)
        self.assertIs(ow[g.me].view_channel, True)
        self.assertEqual([h.name for h in ch.hooks], ["GoldSentinel-Sync"])
        self.assertTrue(ch.hooks[0].sent[0].startswith("GSSYNC-INDEX"))
        self.assertEqual(conf["sync_webhook_url"], ch.hooks[0].url)
        self.assertEqual(cfg["sync"]["42"]["index_id"], int(conf["sync_index_id"]))
        self.assertEqual(us.route_message(cfg, ch.id, 999), "ignore")
        self.assertEqual(us.route_message(cfg, ch.id, None), "ignore")

    def test_s2_zweimal_derselbe_kanal_und_index(self):
        g, user, cfg = Guild(), Obj(name="Spieler", id=42), {}
        conf1, _ = run(us.setup_sync(g, user, cfg))
        ch = g.text_channels[-1]
        ch.hooks[0].known = [int(conf1["sync_index_id"])]
        conf2, _ = run(us.setup_sync(g, user, cfg))
        self.assertEqual(conf1, conf2)
        self.assertEqual(len(g.text_channels), 2)
        self.assertEqual(len(ch.hooks[0].sent), 1)

    def test_s3_ohne_recht(self):
        g = Guild()
        g.me.guild_permissions.manage_channels = False
        conf, notes = run(us.setup_sync(g, Obj(name="X", id=1), {}))
        self.assertIsNone(conf)
        self.assertIn("Kanäle verwalten", notes[0])

    def test_s4_bot_schickt_sync_config(self):
        with open(os.path.join(BOT_DIR, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("async def uploader_cmd"):src.index("# Server-Betrieb: Selbst-Update")]
        self.assertIn("uploader_setup.setup_sync(", body)
        self.assertIn('filename="sync_config.json"', body)
        self.assertIn("GoldSentinel-WoW.bat", body)


if __name__ == "__main__":
    unittest.main()
