"""T-D3-DKP / T-D3-TESTDATEN: dkp_tafel_bot.py und testdaten_bot.py (D-3 Schritt 26, ab Bot 1.5.173) – ohne Netz.

Bis 1.5.172 gab es dafür keine Ablauf-Tests. DKP: Kanal je Pool (Raid-Kanal vor dkp_channels, mc fällt auf
dkp_channel_id zurück); während eines laufenden Raids keine neue Tabelle; Pools ohne DKP und ohne Kanal werden
übersprungen; #dkp-gesamt wird genau einmal entfernt. Testdaten: jede Testnachricht wird zum Löschen vorgemerkt
(TEST_TTL), lange Texte geteilt.
"""
import asyncio
import os
import sys
import time
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Dkp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["dkp_tafel_bot"]

    def setUp(self):
        m = self.m
        self.saved_cfg, self.saved_state = dict(m.cfg), dict(m.state.data)
        self.saved = {k: getattr(m, k) for k in ("post_dkp_table", "channel_by_id", "bot_guild", "save_config")}
        self.saved_rmd = {k: getattr(m.rmd, k) for k in ("session_active", "raid_summaries", "pool_list", "standings",
                                                          "add_raid_columns", "pool_name")}
        self.saved_save = m.state.save
        m.state.save = lambda: None
        m.save_config = lambda: None

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        for k, v in self.saved_rmd.items():
            setattr(m.rmd, k, v)
        m.state.save = self.saved_save
        m.cfg.clear()
        m.cfg.update(self.saved_cfg)
        m.state.data.clear()
        m.state.data.update(self.saved_state)

    def test_gleiche_funktionen_in_bot(self):
        for name in ("dkp_channel_for", "dkp_list_messages", "post_dkp_tables", "post_raid_summaries", "remove_overall"):
            self.assertIs(getattr(self.bot, name), getattr(self.m, name), name)
        self.assertIs(sys.modules["testupload_bot"].send_test, sys.modules["testdaten_bot"].send_test)

    def test_kanal_je_pool(self):
        c = self.m.cfg
        c["raid_channels"] = {"bwl": {"dkp": 11}}
        c["dkp_channels"] = {"bwl": 22, "aq": 33}
        c["dkp_channel_id"] = 44
        self.assertEqual(self.m.dkp_channel_for("bwl"), 11)          # Raid-Kanal zuerst
        self.assertEqual(self.m.dkp_channel_for("aq"), 33)
        self.assertEqual(self.m.dkp_channel_for("mc"), 44)           # alter Eintrag nur für mc
        self.assertEqual(self.m.dkp_channel_for("zg"), 0)

    def test_tabellen_nicht_waehrend_raid_und_nur_mit_dkp_und_kanal(self):
        m, posted = self.m, []

        async def post(pool, cid, rows):
            posted.append((pool, cid))
        m.post_dkp_table = post
        m.rmd.raid_summaries = lambda data: []
        m.rmd.pool_list = lambda data: ["mc", "bwl", "aq"]
        m.rmd.standings = lambda data, pool: [{"dkp": 0 if pool == "aq" else 5}]
        m.rmd.add_raid_columns = lambda rows, s, pool: None
        m.rmd.pool_name = lambda pool, data: pool
        m.cfg["raid_channels"] = {"mc": {"dkp": 1}, "aq": {"dkp": 3}}      # aq hat Kanal, aber keine DKP
        m.cfg.pop("dkp_channels", None)
        m.cfg.pop("dkp_channel_id", None)
        m.state.data["dkp_messages"] = {"mc": [1]}
        m.rmd.session_active = lambda db: True
        asyncio.run(m.post_dkp_tables())
        self.assertEqual(posted, [])                                 # Raid läuft: Tabelle bleibt
        m.rmd.session_active = lambda db: False
        asyncio.run(m.post_dkp_tables())
        self.assertEqual(posted, [("mc", 1)])                        # bwl ohne Kanal, aq ohne DKP

    def test_dkp_gesamt_einmal_entfernt(self):
        m, deleted = self.m, []

        class Ch:
            name = "dkp-gesamt"

            async def delete(self_, reason=None):
                deleted.append(reason)

        async def by_id(cid):
            return Ch()
        m.channel_by_id = by_id
        m.state.data.pop("dkp_total_removed", None)
        m.cfg["dkp_total_channel_id"] = 5
        asyncio.run(m.remove_overall())
        asyncio.run(m.remove_overall())
        self.assertEqual(len(deleted), 1)
        self.assertNotIn("dkp_total_channel_id", m.cfg)
        self.assertTrue(m.state.data["dkp_total_removed"])


class Testdaten(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["testdaten_bot"]

    def test_vorgemerkt_und_geteilt(self):
        m = self.m
        saved = (dict(m.state.data), m.state.save)
        m.state.save = lambda: None
        m.state.data["test_messages"] = []
        sent = []

        class Ch:
            id = 9

            async def send(self_, content=None, **kw):
                sent.append(content)
                return types.SimpleNamespace(id=len(sent))
        try:
            now = int(time.time())
            asyncio.run(m.send_test(Ch(), "x" * 4500))
            marks = list(m.state.data["test_messages"])
        finally:
            m.state.data.clear()
            m.state.data.update(saved[0])
            m.state.save = saved[1]
        self.assertEqual(len(sent), 3)
        self.assertTrue(all(len(s) <= 2000 for s in sent))
        self.assertEqual([x[:2] for x in marks], [[9, 1], [9, 2], [9, 3]])
        self.assertTrue(all(now + m.TEST_TTL <= x[2] <= now + m.TEST_TTL + 5 for x in marks))


if __name__ == "__main__":
    unittest.main()
