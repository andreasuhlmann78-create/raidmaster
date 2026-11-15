"""T-D3-BEUTE: Beute-Datenbank aus beute_bot.py (D-3 Schritt 12, ab Bot 1.5.157) – Ablauf ohne Netz.

Bis 1.5.156 gab es für die Beute-Befehle und die Beutetabellen keinen Ablauf-Test. Hier laufen sie selbst:
/beute ist mit vier Unterbefehlen angemeldet, Offiziers-Befehle sind gesperrt, die Beutetabelle ersetzt die alten
Nachrichten, update_lootdb zieht die Regeln nach und postet nur die verlangten Tabellen.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Ch:
    def __init__(self):
        self.sent, self.deleted = [], []

    async def send(self, text, **kw):
        self.sent.append(text)
        return types.SimpleNamespace(id=500 + len(self.sent))

    def get_partial_message(self, mid):
        ch = self

        class M:
            async def delete(self_):
                ch.deleted.append(mid)
        return M()


class Resp:
    def __init__(self):
        self.messages = []

    async def send_message(self, text, **kw):
        self.messages.append(text)

    async def defer(self, **kw):
        pass


class Beute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["beute_bot"]

    def setUp(self):
        m = self.m
        self.saved = {k: getattr(m, k) for k in ("channel_by_id", "lootdb_text", "is_creator", "ensure_dkp_rules",
                                                 "ensure_guild_rules", "post_loot_table")}
        self.saved_state = dict(m.state.data)
        self.saved_cfg = dict(m.cfg)
        self.saved_save = m.state.save
        m.state.save = lambda: None

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        m.state.save = self.saved_save
        m.state.data.clear()
        m.state.data.update(self.saved_state)
        m.cfg.clear()
        m.cfg.update(self.saved_cfg)

    def test_angemeldet_mit_vier_unterbefehlen(self):
        g = self.bot.bot.tree.get_command("beute")
        self.assertIs(g, self.m.beute_group)
        self.assertEqual(sorted(c.name for c in g.commands), ["boss", "entfernen", "export", "tabellen"])
        self.assertIs(sys.modules["upload_bot"].update_lootdb, self.m.update_lootdb)          # ab 1.5.181 dort benutzt

    def test_offiziers_befehle_gesperrt(self):
        self.m.is_creator = lambda u: False
        for cmd, args in ((self.m.beute_export, ()), (self.m.beute_tabellen, ()),
                          (self.m.beute_entfernen, ("Ragnaros", "1"))):
            r = Resp()
            asyncio.run(cmd.callback(types.SimpleNamespace(user=1, response=r), *args))
            self.assertIn("nur der Gildenchef und die Offiziere", r.messages[0], cmd.name)

    def test_beutetabelle_ersetzt_alte_nachrichten(self):
        ch = Ch()

        async def by_id(cid):
            return ch if str(cid) == "77" else None

        async def text(pool):
            return ["Teil 1", "Teil 2"]
        self.m.channel_by_id, self.m.lootdb_text = by_id, text
        self.m.cfg["raid_channels"] = {"mc": {"loot": 77}}
        self.m.state.data["lootdb_messages"] = {"mc": [11, 12, 13]}
        asyncio.run(self.m.post_loot_table("mc"))
        self.assertEqual(ch.deleted, [11, 12, 13])
        self.assertEqual(ch.sent, ["Teil 1", "Teil 2"])
        self.assertEqual(self.m.state.data["lootdb_messages"]["mc"], [501, 502])
        asyncio.run(self.m.post_loot_table("bwl"))                   # kein Loot-Kanal: nichts
        self.assertEqual(len(ch.sent), 2)

    def test_update_lootdb_regeln_und_nur_verlangte_tabellen(self):
        calls = []

        async def rec(name):
            calls.append(name)

        async def dkp():
            calls.append("dkp_rules")

        async def guild():
            calls.append("guild_rules")
        self.m.ensure_dkp_rules, self.m.ensure_guild_rules, self.m.post_loot_table = dkp, guild, rec
        self.m.cfg["loot_tables"] = True
        asyncio.run(self.m.update_lootdb(["mc", "mc", "", "bwl"]))
        self.assertEqual(calls, ["dkp_rules", "guild_rules", "mc", "bwl"])     # doppelt/leer nur einmal bzw. nie
        calls.clear()
        self.m.cfg["loot_tables"] = False
        asyncio.run(self.m.update_lootdb(["mc"]))
        self.assertEqual(calls, ["dkp_rules", "guild_rules"])                 # Tabellen abgeschaltet


if __name__ == "__main__":
    unittest.main()
