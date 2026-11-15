"""T-D3-REGELN: Regeln aus regeln_bot.py (D-3 Schritt 11, ab Bot 1.5.156) – Ablauf ohne Netz.

Bis 1.5.155 gab es für channel_links und ensure_dkp_rules keinen Test. Hier laufen beide selbst:
Kanal-Links in Regeltexten, #regeln einmal posten, unverändert nichts, geändert bearbeiten statt neu posten.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Msg:
    def __init__(self, mid, ch):
        self.id, self.ch = mid, ch

    async def edit(self, content=None, **kw):
        self.ch.edited.append((self.id, content))

    async def delete(self):
        self.ch.deleted.append(self.id)


class Ch:
    def __init__(self, name, cid):
        self.name, self.id = name, cid
        self.mention = f"<#{cid}>"
        self.sent, self.edited, self.deleted = [], [], []

    async def send(self, text, **kw):
        self.sent.append(text)
        return types.SimpleNamespace(id=1000 + len(self.sent))

    def get_partial_message(self, mid):
        return Msg(mid, self)

    def history(self, **kw):
        async def gen():
            return
            yield
        return gen()


class Regeln(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["regeln_bot"]

    def setUp(self):
        m = self.m
        self.regeln, self.bank = Ch("regeln", 5), Ch("gildenbank", 6)
        self.saved = (m.bot_guild, m.state.save, dict(m.state.data), m.asyncio.sleep)
        m.bot_guild = lambda: types.SimpleNamespace(text_channels=[self.regeln, self.bank])
        m.state.save = lambda: None
        m.state.data.pop("dkp_rules", None)

        async def nosleep(_):
            return None
        m.asyncio.sleep = nosleep

    def tearDown(self):
        m = self.m
        m.bot_guild, m.state.save = self.saved[:2]
        m.state.data.clear()
        m.state.data.update(self.saved[2])
        m.asyncio.sleep = self.saved[3]

    def test_gleiche_funktionen_in_bot(self):
        self.assertIs(self.bot.ensure_guild_rules, self.m.ensure_guild_rules)
        self.assertIs(self.bot.ensure_dkp_rules, self.m.ensure_dkp_rules)

    def test_kanal_links(self):
        self.assertEqual(self.m.channel_links("Siehe {#gildenbank} und {#gibtsnicht}."),
                         "Siehe <#6> und **#gibtsnicht**.")
        self.m.bot_guild = lambda: None
        self.assertEqual(self.m.channel_links("{#gildenbank}"), "**#gildenbank**")

    def test_dkp_regeln_einmal_dann_bearbeiten(self):
        r = asyncio.run(self.m.ensure_dkp_rules())
        self.assertEqual(r, ["#regeln: DKP- und Raid-Regeln gepostet"])
        n = len(self.regeln.sent)
        self.assertGreater(n, 0)
        rec = self.m.state.data["dkp_rules"]
        self.assertEqual((rec["ch"], len(rec["ids"])), (5, n))
        self.assertEqual(asyncio.run(self.m.ensure_dkp_rules()), [])            # unverändert: nichts
        self.assertEqual(len(self.regeln.sent), n)
        self.m.state.data["dkp_rules"]["hash"] = "alt"                           # Text geändert
        r = asyncio.run(self.m.ensure_dkp_rules())
        self.assertEqual(r, ["#regeln: DKP- und Raid-Regeln aktualisiert"])
        self.assertEqual(len(self.regeln.sent), n)                               # bearbeitet, nicht neu gepostet
        self.assertEqual([i for i, _ in self.regeln.edited], rec["ids"])

    def test_ohne_regelkanal_nichts(self):
        self.m.bot_guild = lambda: types.SimpleNamespace(text_channels=[self.bank])
        self.assertEqual(asyncio.run(self.m.ensure_dkp_rules()), [])
        self.assertEqual(self.bank.sent, [])


if __name__ == "__main__":
    unittest.main()
