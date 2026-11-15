"""T-D3-UPLOAD: upload_bot.py (D-3 Schritt 34, ab Bot 1.5.181) – Daten-Upload und Verarbeitung ohne Netz.

Bis 1.5.180 gab es für process_new_data keinen Ablauf-Test und für receive_upload nur den Fall "GuildSentinel-Datei
zu gross" (test_market). Hier: process_new_data arbeitet nur bei neuen Daten und ruft alle Schritte in der
bisherigen Reihenfolge auf, ein Fehler bei Klassenfarben hält den Rest nicht auf, ein Discord-Fehler wird nur
protokolliert; receive_upload ignoriert fremde Webhooks, übernimmt keinen älteren DKP-Stand eines anderen
Uploaders, lässt im Testmodus die echten Daten unberührt und legt echte Daten ab, löscht die Nachricht und
verarbeitet sie; dkp_loop läuft alle 30 Sekunden und wartet vorher auf die Anmeldung.
"""
import asyncio
import os
import shutil
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

SCHRITTE = ["sync_specs", "sync_class_roles", "ensure_new_raid_categories", "sync_raid_visibility",
            "maintain_member_area", "post_raid_summaries", "post_dkp_tables", "remove_overall", "post_new_loot",
            "update_lootdb", "update_hall_of_fame", "post_guild_bank", "send_raid_dms", "process_assignment"]


class Anhang:
    def __init__(self, filename, data=b"x"):
        self.filename, self.data, self.size = filename, data, len(data)

    async def read(self):
        return self.data


class Nachricht:
    def __init__(self, files, webhook_id=5, author="Raidleiter"):
        self.attachments = [Anhang(f) for f in files]
        self.webhook_id = webhook_id
        self.author = types.SimpleNamespace(name=author)
        self.deleted = False

    async def delete(self):
        self.deleted = True


class Verarbeitung(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["upload_bot"]

    def setUp(self):
        m = self.m
        self.saved = {k: getattr(m, k) for k in SCHRITTE + ["reload_dkp_if_needed", "post_bot_log"]}
        self.calls, self.logs = [], []
        for k in SCHRITTE:
            async def f(_k=k):
                self.calls.append(_k)
            setattr(m, k, f)

        async def blog(text):
            self.logs.append(text)
        m.post_bot_log = blog

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(self.m, k, v)

    def test_am_bot_angemeldet(self):
        self.assertIs(self.bot.dkp_loop, self.m.dkp_loop)
        self.assertIs(self.bot.receive_upload, self.m.receive_upload)
        self.assertEqual(self.m.dkp_loop.seconds, 30)
        self.assertIs(self.m.dkp_loop._before_loop, self.m.before_dkp)

    def test_nur_bei_neuen_daten_alle_schritte(self):
        self.m.reload_dkp_if_needed = lambda: False
        asyncio.run(self.m.process_new_data())
        self.assertEqual(self.calls, [])

        def kaputt():
            raise OSError("wird gerade geschrieben")
        self.m.reload_dkp_if_needed = kaputt
        with self.assertLogs("raidmaster", level="WARNING"):
            asyncio.run(self.m.process_new_data())
        self.assertEqual(self.calls, [])
        self.m.reload_dkp_if_needed = lambda: True
        asyncio.run(self.m.process_new_data())
        self.assertEqual(self.calls, SCHRITTE)

    def test_fehler_klassenfarben_und_discord(self):
        import discord
        self.m.reload_dkp_if_needed = lambda: True

        async def kaputt():
            raise RuntimeError("Klassenfarben")
        self.m.sync_class_roles = kaputt
        with self.assertLogs("raidmaster", level="ERROR"):
            asyncio.run(self.m.process_new_data())
        self.assertEqual(self.calls, [s for s in SCHRITTE if s != "sync_class_roles"])   # Rest läuft weiter
        self.calls.clear()

        async def http():
            raise discord.HTTPException(types.SimpleNamespace(status=500, reason="x"), "weg")
        self.m.post_dkp_tables = http
        with self.assertLogs("raidmaster", level="WARNING") as cm:
            asyncio.run(self.m.process_new_data())
        self.assertTrue(any("Posten fehlgeschlagen" in r for r in cm.output))
        self.assertEqual(self.calls[-1], "post_raid_summaries")                      # danach nichts mehr


class Empfang(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["upload_bot"]

    def setUp(self):
        m = self.m
        self.dir = tempfile.mkdtemp()
        self.saved = {k: getattr(m, k) for k in ("check_upload", "test_info", "process_new_data", "post_bot_log",
                                                 "market_intake", "handle_test_upload", "DATA_DIR", "UPLOAD_PATH")}
        self.saved_cfg, self.saved_state = dict(m.cfg), dict(m.state.data)
        self.saved_save, self.saved_dkp = m.state.save, m.bot.dkp_data
        m.state.save = lambda: None
        m.DATA_DIR = self.dir
        m.UPLOAD_PATH = os.path.join(self.dir, "RaidMaster.lua")
        m.cfg["uploader_webhooks"] = [5]
        self.processed, self.logs, self.tests = [], [], []

        async def proc():
            self.processed.append(1)

        async def blog(text):
            self.logs.append(text)

        async def intake(msg):
            return None

        async def test_up(db, who):
            self.tests.append(who)
            return 2
        m.process_new_data, m.post_bot_log, m.market_intake, m.handle_test_upload = proc, blog, intake, test_up
        self.version = 7
        m.check_upload = lambda raw, fn: ("DATEN", {"data": {"version": self.version, "players": {"a": 1, "b": 2}}})
        m.test_info = lambda db: None

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        m.cfg.clear()
        m.cfg.update(self.saved_cfg)
        m.state.data.clear()
        m.state.data.update(self.saved_state)
        m.state.save, m.bot.dkp_data = self.saved_save, self.saved_dkp
        shutil.rmtree(self.dir)

    def test_fremder_webhook(self):
        msg = Nachricht(["RaidMaster.lua.gz"], webhook_id=99)
        with self.assertLogs("raidmaster", level="WARNING"):
            asyncio.run(self.m.receive_upload(msg))
        self.assertFalse(msg.deleted)
        self.assertFalse(os.path.exists(self.m.UPLOAD_PATH))
        self.assertEqual(self.processed, [])

    def test_echte_daten_abgelegt_und_verarbeitet(self):
        msg = Nachricht(["RaidMaster.lua.gz"])
        asyncio.run(self.m.receive_upload(msg))
        with open(self.m.UPLOAD_PATH, encoding="utf-8") as f:
            self.assertEqual(f.read(), "DATEN")
        self.assertEqual(self.m.state.data["last_upload_by"], "Raidleiter")
        self.assertTrue(msg.deleted)
        self.assertEqual(self.processed, [1])
        self.assertIn("(2 Spieler)", self.logs[-1])

    def test_aelterer_stand_anderer_uploader(self):
        self.m.bot.dkp_data = {"version": 9}
        self.m.state.data["last_upload_by"] = "Jemand"
        msg = Nachricht(["RaidMaster.lua.gz"], author="Anderer")
        asyncio.run(self.m.receive_upload(msg))
        self.assertFalse(os.path.exists(self.m.UPLOAD_PATH))
        self.assertIn("älterer DKP-Stand", self.logs[-1])
        self.assertEqual(self.processed, [])
        self.m.state.data["last_upload_by"] = "Anderer"                   # derselbe Uploader darf zurücksetzen
        asyncio.run(self.m.receive_upload(Nachricht(["RaidMaster.lua.gz"], author="Anderer")))
        self.assertTrue(os.path.exists(self.m.UPLOAD_PATH))

    def test_testmodus_laesst_echte_daten(self):
        self.m.test_info = lambda db: {"post": True}
        msg = Nachricht(["RaidMaster.lua.gz"])
        asyncio.run(self.m.receive_upload(msg))
        self.assertFalse(os.path.exists(self.m.UPLOAD_PATH))
        self.assertEqual(self.tests, ["Raidleiter"])
        self.assertTrue(msg.deleted)
        self.assertEqual(self.processed, [])
        self.assertIn("2 Nachrichten gepostet", self.logs[-1])


if __name__ == "__main__":
    unittest.main()
