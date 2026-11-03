"""Offline-Tests #testberichte (Bot 1.5.97): /uploader mit zwei Webhooks, Kanal anlegen, Bot liest dort nichts.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import json
import os
import sys
import unittest

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BOT_DIR)
import discord  # noqa: E402
import raidmaster_data as rmd  # noqa: E402
import server_setup  # noqa: E402
import uploader_setup  # noqa: E402


class Perms:
    def __init__(self, **kw):
        self.manage_channels = kw.get("manage_channels", True)
        self.manage_webhooks = kw.get("manage_webhooks", True)


class Hook:
    _next = 500

    def __init__(self, name):
        Hook._next += 1
        self.id, self.name, self.token = Hook._next, name, "tok"
        self.url = f"https://discord.invalid/api/webhooks/{self.id}/tok"


class Channel:
    _next = 100

    def __init__(self, name, guild, category=None, overwrites=None, topic=None, webhook_perm=True):
        Channel._next += 1
        self.id, self.name, self.guild, self.category = Channel._next, name, guild, category
        self.overwrites, self.topic, self.hooks, self.webhook_perm = overwrites, topic, [], webhook_perm

    async def webhooks(self):
        return list(self.hooks)

    async def create_webhook(self, name, reason=None):
        h = Hook(name)
        self.hooks.append(h)
        return h

    def permissions_for(self, member):
        return Perms(manage_webhooks=self.webhook_perm)


class Obj:
    """hashbar (Rollen und Mitglieder sind Schlüssel in den Rechte-Überschreibungen)"""

    def __init__(self, **kw):
        self.__dict__.update(kw)


class Guild:
    def __init__(self, manage_channels=True):
        self.text_channels, self.roles = [], []
        self.categories = [Obj(name="🔒 OFFIZIERE", id=1)]
        self.default_role = Obj(name="@everyone", id=0)
        self.me = Obj(name="Bot", id=1, guild_permissions=Perms(manage_channels=manage_channels))

    def add(self, name, **kw):
        ch = Channel(name, self, **kw)
        self.text_channels.append(ch)
        return ch

    async def create_text_channel(self, name, category=None, overwrites=None, topic=None, reason=None):
        return self.add(name, category=category, overwrites=overwrites, topic=topic)


def run(c):
    return asyncio.run(c)


class Uploader(unittest.TestCase):
    def test_b01_kanal_anlegen_oder_wiederverwenden(self):
        g = Guild()
        data = g.add("bot-daten")
        cfg = {}
        run(uploader_setup.setup_uploader_hooks(g, data, cfg))
        tb = [c for c in g.text_channels if c.name == "testberichte"]
        self.assertEqual(len(tb), 1)
        self.assertEqual(tb[0].category.name, "🔒 OFFIZIERE")
        ow = tb[0].overwrites
        self.assertIs(ow[g.default_role].view_channel, False)        # "hidden": nur Bot und Admins
        self.assertIs(ow[g.me].view_channel, True)
        run(uploader_setup.setup_uploader_hooks(g, data, cfg))
        self.assertEqual(len([c for c in g.text_channels if c.name == "testberichte"]), 1)

    def test_b02_webhooks(self):
        g = Guild()
        data = g.add("bot-daten")
        cfg = {"uploader_webhooks": []}
        d1, t1, _ = run(uploader_setup.setup_uploader_hooks(g, data, cfg))
        d2, t2, _ = run(uploader_setup.setup_uploader_hooks(g, data, cfg))
        self.assertEqual((d1, t1), (d2, t2))
        tb = next(c for c in g.text_channels if c.name == "testberichte")
        self.assertEqual([h.name for h in tb.hooks], ["GoldSentinel-Testberichte"])
        self.assertEqual([h.name for h in data.hooks], ["RaidMaster-Uploader"])
        self.assertEqual(cfg["testberichte_channel_id"], tb.id)
        self.assertEqual(cfg["testberichte_webhook_id"], tb.hooks[0].id)
        self.assertEqual(cfg["uploader_webhooks"], [data.hooks[0].id])

    def test_b03_konfiguration(self):
        conf = uploader_setup.uploader_config("https://d", "https://t", 42)
        self.assertEqual(conf, {"webhook_url": "https://d", "test_webhook_url": "https://t", "bot_id": 42,
                                "savedvariables_path": "", "check_seconds": 10})
        self.assertEqual(list(conf)[:2], ["webhook_url", "test_webhook_url"])
        self.assertNotIn("test_webhook_url", uploader_setup.uploader_config("https://d", None, 42))
        json.dumps(conf)

    def test_b04_fehlende_rechte(self):
        g = Guild(manage_channels=False)
        data = g.add("bot-daten")
        cfg = {}
        d, t, notes = run(uploader_setup.setup_uploader_hooks(g, data, cfg))
        self.assertTrue(d.startswith("https://") and t is None)
        self.assertIn("Kanäle verwalten", " ".join(notes))
        g2 = Guild()
        data2 = g2.add("bot-daten")
        g2.add("testberichte", webhook_perm=False)
        d, t, notes = run(uploader_setup.setup_uploader_hooks(g2, data2, {}))
        self.assertTrue(d.startswith("https://") and t is None)
        self.assertIn("Webhooks verwalten", " ".join(notes))

    def test_b05_on_message(self):
        cfg = {"data_channel_id": 10, "testberichte_channel_id": 20}
        self.assertEqual(uploader_setup.route_message(cfg, 20, 999), "ignore")
        self.assertEqual(uploader_setup.route_message(cfg, 20, None), "ignore")
        self.assertEqual(uploader_setup.route_message(cfg, 10, 999), "upload")
        self.assertIsNone(uploader_setup.route_message(cfg, 10, None))
        self.assertIsNone(uploader_setup.route_message(cfg, 30, 999))
        with open(os.path.join(BOT_DIR, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        on_msg = src[src.index("async def on_message"):src.index("async def on_message") + 600]
        self.assertLess(on_msg.index('route == "ignore"'), on_msg.index("receive_upload"))

    def test_b06_einrichten(self):
        cats = {c["name"]: c for c in server_setup.BASE_TOP + server_setup.BASE_BOTTOM}
        chans = {ch[1]: ch for ch in cats["🔒 OFFIZIERE"]["channels"]}
        self.assertIn("testberichte", chans)
        self.assertEqual(chans["testberichte"][3], "hidden")
        with open(os.path.join(BOT_DIR, "server_setup.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn('("testberichte_channel_id", "testberichte")', src)
        for line in src.splitlines():
            if "löschen" in line and "testberichte" in line:
                self.assertIn("nichts löschen", line)                 # nur das Thema "Bitte nichts löschen"

    def test_b07_gstest_in_savedvariables(self):
        text = ('RaidMasterDB = {\n\t["data"] = {\n\t\t["version"] = 7,\n\t\t["players"] = {\n'
                '\t\t\t["Tank1"] = { ["c"] = "WARRIOR", ["d"] = { ["mc"] = 120 } },\n\t\t},\n\t},\n'
                '\t["gsTest"] = {\n\t\t["reports"] = {\n'
                '\t\t\t"GSTEST1{\\"f\\":1,\\"id\\":\\"x\\",\\"text\\":\\"a\\\\\\\\b\\"}",\n'
                '\t\t},\n\t\t["errors"] = {},\n\t},\n}\n')
        db = rmd.parse_saved_variables(text)["RaidMasterDB"]
        self.assertEqual(db["data"]["version"], 7)
        self.assertEqual(db["data"]["players"]["Tank1"]["d"]["mc"], 120)
        rows = rmd.standings(db["data"], "mc")
        self.assertEqual([r["name"] for r in rows], ["Tank1"])
        rep = rmd.lua_list(db["gsTest"]["reports"])[0]
        self.assertTrue(rep.startswith('GSTEST1{"f":1'))

    def test_b08_bot_wertet_nicht_aus(self):
        for fn in ("bot.py", "uploader_setup.py", "raidmaster_data.py"):
            with open(os.path.join(BOT_DIR, fn), encoding="utf-8") as f:
                src = f.read()
            self.assertNotIn("import testberichte", src, fn)
            self.assertNotIn("from testberichte", src, fn)
        with open(os.path.join(BOT_DIR, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        # bot.py merkt sich nur die Kanal-ID (beim Start angelegt); gelesen, beantwortet oder gepostet wird dort nichts
        body = src[src.index("async def ensure_test_channel"):src.index("async def repair_missing_announcements")]
        rest = src.replace(body, "")
        self.assertNotIn("testberichte_channel_id", rest.replace('route_message(cfg', ''))
        self.assertNotIn("ch.send", body)

    def test_b09_find_player(self):
        r = [{"name": "Tank1", "dkp": 1}, {"name": "Rokan Steinwacht", "dkp": 2}]
        self.assertEqual(rmd.find_player(r, "Rokan Steinwacht")[1]["name"], "Rokan Steinwacht")
        self.assertEqual(rmd.find_player(r, "Rokan")[1]["name"], "Rokan Steinwacht")
        self.assertIsNone(rmd.find_player(r + [{"name": "Rokan Eisen", "dkp": 3}], "Rokan"))
        self.assertEqual(rmd.find_player([{"name": "Rokan", "dkp": 1}], "rokan")[1]["name"], "Rokan")


if __name__ == "__main__":
    unittest.main()
