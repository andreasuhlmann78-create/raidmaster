"""T-D3-WILLKOMMEN: Willkommen aus willkommen_bot.py (D-3 Schritt 14, ab Bot 1.5.159) – Ablauf ohne Netz.

Bis 1.5.158 gab es für ensure_welcome und /willkommen keinen Ablauf-Test. Hier laufen sie selbst:
Text einmal posten, beim Start unverändert nichts, geändert bearbeiten statt neu posten, alte kurze Begrüßung
entfernen; /willkommen nur Gildenleitung, Gildenname nur Gildenchef.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Msg:
    def __init__(self, mid, content, author_id, ch):
        self.id, self.content, self.ch = mid, content, ch
        self.author = types.SimpleNamespace(id=author_id)

    async def delete(self):
        self.ch.deleted.append(self.id)


class Ch:
    def __init__(self, old=()):
        self.name, self.id, self.mention = "willkommen", 40, "<#40>"
        self.sent, self.edited, self.deleted = [], [], []
        self.old = list(old)

    async def send(self, text, **kw):
        self.sent.append(text)
        return types.SimpleNamespace(id=900 + len(self.sent))

    def get_partial_message(self, mid):
        ch = self

        class P:
            async def edit(self_, content=None, **kw):
                ch.edited.append((mid, content))
        return P()

    def history(self, limit=30):
        msgs = self.old

        async def gen():
            for m in msgs:
                yield m
        return gen()


class Resp:
    def __init__(self):
        self.messages = []

    async def send_message(self, text, **kw):
        self.messages.append(text)


class Willkommen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["willkommen_bot"]

    def setUp(self):
        m = self.m
        self.saved = {k: getattr(m, k) for k in ("bot_guild", "channel_by_id", "is_admin", "is_chef", "save_config")}
        self.saved_state, self.saved_cfg, self.saved_save = dict(m.state.data), dict(m.cfg), m.state.save
        self.saved_user = m.bot._connection.user
        m.bot._connection.user = types.SimpleNamespace(id=1)
        m.state.save = lambda: None
        m.save_config = lambda: None
        for k in ("welcome_message", "welcome_hash"):
            m.state.data.pop(k, None)
        self.ch = Ch(old=[Msg(5, self.m.OLD_WELCOME_START + " Hallo", 1, None), Msg(6, "von jemand anderem", 2, None)])
        for o in self.ch.old:
            o.ch = self.ch

        async def by_id(cid):
            return self.ch
        m.channel_by_id = by_id
        m.bot_guild = lambda: types.SimpleNamespace(name="Gilde", text_channels=[self.ch], roles=[])

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
        self.assertIs(self.bot.ensure_welcome, self.m.ensure_welcome)
        self.assertIs(self.bot.post_welcome_invite_once, self.m.post_welcome_invite_once)

    def test_einmal_posten_dann_nur_bei_aenderung(self):
        r = asyncio.run(self.m.ensure_welcome(update=False))
        self.assertIn("eingetragen", r)
        self.assertEqual(len(self.ch.sent), 1)
        self.assertEqual(self.ch.deleted, [5])                        # nur die alte Bot-Begrüßung
        self.assertEqual(asyncio.run(self.m.ensure_welcome(update=False)), "Willkommenstext ist bereits eingetragen.")
        self.assertEqual((len(self.ch.sent), self.ch.edited), (1, []))
        self.m.state.data["welcome_hash"] = "alt"                    # neue Fassung des Texts
        self.assertIn("aktualisiert", asyncio.run(self.m.ensure_welcome(update=False)))
        self.assertEqual(len(self.ch.sent), 1)                        # bearbeitet, nicht neu gepostet
        self.assertEqual(self.ch.edited[0][0], 901)

    def test_ohne_kanal_meldung(self):
        async def none(cid):
            return None
        self.m.channel_by_id = none
        self.m.bot_guild = lambda: types.SimpleNamespace(name="Gilde", text_channels=[], roles=[])
        self.assertIn("nicht gefunden", asyncio.run(self.m.ensure_welcome()))

    def test_willkommen_rechte(self):
        self.m.is_admin = lambda u: False
        r = Resp()
        asyncio.run(self.m.welcome_cmd.callback(types.SimpleNamespace(user=1, response=r), None))
        self.assertIn("nur der Gildenchef und die Offiziere", r.messages[0])
        self.m.is_admin, self.m.is_chef = (lambda u: True), (lambda u: False)
        r = Resp()
        self.m.cfg["guild_name"] = "Alt"
        asyncio.run(self.m.welcome_cmd.callback(types.SimpleNamespace(user=1, response=r), "Neu"))
        self.assertIn("nur der Gildenchef", r.messages[0])
        self.assertEqual(self.m.cfg["guild_name"], "Alt")              # Offizier ändert den Namen nicht


if __name__ == "__main__":
    unittest.main()
