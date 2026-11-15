"""T-D3-GILDENNAME: Gildennamen-Abstimmung aus gildenname_bot.py (D-3 Schritt 15, ab Bot 1.5.160) – ohne Netz.

Bis 1.5.159 gab es für die Abstimmung nur eine Text-Prüfung (name_channel). Hier laufen die Kernregeln selbst:
Namensprüfung (Länge, nur Buchstaben, doppelte Vorschläge), was als Vorschlag-Beitrag zählt, und dass ein
Vorschlag mit Karte angelegt und gemerkt wird; nach Ende der Abstimmung wird #gildenname nicht neu angelegt.
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
        self.name, self.id = "gildenname", 60
        self.sent = []

    async def send(self, content=None, **kw):
        self.sent.append((content, kw))
        return types.SimpleNamespace(id=700 + len(self.sent), jump_url=f"https://x/{700 + len(self.sent)}")


class Gildenname(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["gildenname_bot"]

    def setUp(self):
        m = self.m
        self.saved = {k: getattr(m, k) for k in ("channel_by_id", "bot_guild", "refresh_name_overview", "save_config")}
        self.saved_state, self.saved_cfg, self.saved_save = dict(m.state.data), dict(m.cfg), m.state.save
        self.saved_user = m.bot._connection.user
        m.bot._connection.user = types.SimpleNamespace(id=1)
        m.state.save = lambda: None
        m.save_config = lambda: None
        m.state.data.pop("name_poll", None)

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        m.state.save = self.saved_save
        m.state.data.clear()
        m.state.data.update(self.saved_state)
        m.cfg.clear()
        m.cfg.update(self.saved_cfg)
        m.bot._connection.user = self.saved_user

    def test_gleiche_funktionen_in_bot(self):
        self.assertIs(self.bot.handle_name_post, self.m.handle_name_post)
        self.assertIs(self.bot.apply_fixed_guild_name, self.m.apply_fixed_guild_name)

    def test_namenspruefung(self):
        c = self.m.check_guild_name
        self.assertEqual(c('  "Alpine   Vanguard" '), ("Alpine Vanguard", None))
        self.assertIsNone(c("A")[0])                                    # zu kurz
        self.assertIsNone(c("X" * 25)[0])                               # WoW: höchstens 24 Zeichen
        self.assertIn("keine Zahlen", c("Gilde 42")[1])
        self.m.name_poll()["proposals"]["1"] = {"name": "Alpine Vanguard"}
        self.m.name_poll()["order"].append("1")
        self.assertIn("schon vorgeschlagen", c("alpine vanguard")[1])   # doppelt, egal wie geschrieben

    def test_was_als_vorschlag_zaehlt(self):
        def post(text):
            return types.SimpleNamespace(content=text)
        f = self.m.name_from_post
        self.assertEqual(f(post("Eisenwacht")), "Eisenwacht")
        self.assertEqual(f(post("<@1> Eisenwacht!")), "Eisenwacht")    # Erwähnung des Bots stört nicht
        for text in ("ja", "Eisenwacht?", "ich bin dafür", "zwei\nZeilen", "https://x.y", "Abc",
                     "Das ist ein langer Satz"):
            self.assertIsNone(f(post(text)), text)

    def test_vorschlag_mit_karte_angelegt(self):
        ch = Ch()

        async def by_id(cid):
            return ch

        async def overview(repost=False):
            self.overview = repost
        self.m.channel_by_id, self.m.refresh_name_overview = by_id, overview
        prop = asyncio.run(self.m.add_name_proposal("Eisenwacht", 5, "Thrall", "Lore"))
        self.assertEqual((prop["id"], prop["name"], prop["votes"], prop["msg"]), ("1", "Eisenwacht", [], 701))
        self.assertEqual(self.m.name_poll()["order"], ["1"])
        self.assertIn("embed", ch.sent[0][1])
        self.assertTrue(self.overview)                                   # Übersicht nach unten geschoben
        self.assertEqual(self.m.name_poll()["next_id"], 2)

    def test_nach_ende_kanal_nicht_neu(self):
        async def none(cid):
            return None
        self.m.channel_by_id = none
        self.m.cfg.pop("name_poll_channel_id", None)
        self.m.name_poll()["closed"] = True
        created = []

        async def create(*a, **k):
            created.append(a)
        g = types.SimpleNamespace(text_channels=[], create_text_channel=create,
                                  me=types.SimpleNamespace(guild_permissions=types.SimpleNamespace(manage_channels=True)))
        self.m.bot_guild = lambda: g
        self.assertIsNone(asyncio.run(self.m.name_channel()))
        self.assertEqual(created, [])


if __name__ == "__main__":
    unittest.main()
