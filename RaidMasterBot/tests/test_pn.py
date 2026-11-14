"""T-PN: /pn – Privatnachricht der Gildenleitung über den Bot (ab Bot 1.5.133)."""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import pn  # noqa: E402


class PnText(unittest.TestCase):
    def test_vorlage_uploader(self):
        t = pn.vorlage("uploader")
        self.assertIn("RaidMasterUploader.zip", t)
        self.assertIn("Autostart-einrichten.bat", t)
        self.assertIn("Nie weitergeben", t)
        self.assertLessEqual(len(t), pn.MAX_LEN)
        self.assertNotIn("discord.com/api/webhooks", t)                  # nie ein geheimer Link in der Vorlage

    def test_unbekannte_vorlage_leer(self):
        self.assertEqual(pn.vorlage("gibtsnicht"), "")
        self.assertEqual(pn.vorlage(None), "")

    def test_nachricht(self):
        m = pn.nachricht("Chef", "Hallo", "Alpine Vanguard")
        self.assertTrue(m.startswith("✉️ Nachricht von **Chef** (Gildenleitung Alpine Vanguard):"))
        self.assertTrue(m.endswith("Hallo"))
        self.assertIsNone(pn.nachricht("Chef", "   "))                  # leer -> nichts schicken
        self.assertLessEqual(len(pn.nachricht("Chef", "x" * 5000)), 2000)

    def test_log_ohne_inhalt(self):
        line = pn.log_line(123, "geheimer Text")
        self.assertNotIn("geheim", line)
        self.assertIn("123", line)


class Member:
    def __init__(self, mid=5, bot=False, forbid=False):
        self.id, self.bot, self.display_name, self.mention = mid, bot, "Empfaenger", f"<@{mid}>"
        self.forbid, self.sent = forbid, []

    async def send(self, text, **kw):
        if self.forbid:
            import discord
            raise discord.Forbidden(types.SimpleNamespace(status=403, reason="x"), "dm closed")
        self.sent.append((text, kw))


class Response:
    def __init__(self):
        self.messages, self.modal = [], None

    async def send_message(self, text, **kw):
        self.messages.append(text)

    async def send_modal(self, modal):
        self.modal = modal


class Inter:
    def __init__(self, admin=True):
        self.user = types.SimpleNamespace(display_name="Chef", admin=admin)
        self.response = Response()


class PnAblauf(unittest.TestCase):
    """Mit dem echten bot.py (tests/bot_harness.py)."""
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.orig = cls.bot.is_creator
        cls.bot.is_creator = lambda u: getattr(u, "admin", False)

    @classmethod
    def tearDownClass(cls):
        cls.bot.is_creator = cls.orig

    def run_cmd(self, inter, member, vorlage=None):
        return asyncio.run(self.bot.pn_cmd.callback(inter, member, vorlage))

    def test_nur_gildenleitung(self):
        i, m = Inter(admin=False), Member()
        self.run_cmd(i, m)
        self.assertIsNone(i.response.modal)
        self.assertIn("Nur für", i.response.messages[0])
        self.assertEqual(m.sent, [])

    def test_nie_an_bots(self):
        i = Inter()
        self.run_cmd(i, Member(bot=True))
        self.assertIsNone(i.response.modal)

    def test_vorlage_im_formular_und_senden(self):
        i, m = Inter(), Member()
        self.run_cmd(i, m, types.SimpleNamespace(value="uploader"))
        modal = i.response.modal
        self.assertIsNotNone(modal)
        self.assertEqual(modal.text.default, pn.vorlage("uploader"))
        modal.text._value = modal.text.default                           # wie abgeschickt
        i2 = Inter()
        with self.assertLogs("raidmaster", level="INFO") as cm:
            asyncio.run(modal.on_submit(i2))
        self.assertEqual(len(m.sent), 1)
        self.assertIn("Autostart-einrichten.bat", m.sent[0][0])
        self.assertTrue(i2.response.messages[0].startswith("✅"))
        self.assertFalse(any("Autostart" in r for r in cm.output))      # Inhalt nie im Protokoll

    def test_leer_und_gesperrt(self):
        i, m = Inter(), Member()
        self.run_cmd(i, m)
        modal = i.response.modal
        modal.text._value = "   "
        i2 = Inter()
        asyncio.run(modal.on_submit(i2))
        self.assertEqual(m.sent, [])
        self.assertIn("Leere Nachricht", i2.response.messages[0])
        m2 = Member(forbid=True)
        i3 = Inter()
        self.run_cmd(i3, m2)
        i3.response.modal.text._value = "Hallo"
        i4 = Inter()
        asyncio.run(i3.response.modal.on_submit(i4))
        self.assertIn("keine Privatnachrichten", i4.response.messages[0])


class UploaderFuer(unittest.TestCase):
    """T-UP-FUER (1.5.134): /uploader fuer:@Mitglied – Dateien direkt an das Mitglied, eigener #sync-daten."""
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()

    def setUp(self):
        b = self.bot
        self.saved = {k: getattr(b, k) for k in ("is_admin", "channel_by_id", "ensure_fresh_uploader",
                                                   "uploader_package", "save_config")}
        self.saved_setup = (b.uploader_setup.setup_uploader_hooks, b.uploader_setup.setup_sync,
                            b.uploader_setup.uploader_config)
        import discord
        self.sync_for = []
        TC = type("TC", (discord.TextChannel,), {
            "__init__": lambda self: None,
            "guild": types.SimpleNamespace(me=1),
            "permissions_for": lambda self, me: types.SimpleNamespace(manage_webhooks=True)})
        ch = TC()

        async def by_id(cid):
            return ch

        async def hooks(*a, **k):
            return "D", "T", []

        async def sync(guild, user, cfg, reason=""):
            self.sync_for.append(user.id)
            return {"sync": user.id}, []

        async def fresh():
            return "2.3.7", "2.3.7"
        b.is_admin = lambda u: getattr(u, "admin", False)
        b.channel_by_id = by_id
        b.ensure_fresh_uploader = fresh
        b.uploader_package = lambda: None
        b.save_config = lambda: None
        b.uploader_setup.setup_uploader_hooks = hooks
        b.uploader_setup.setup_sync = sync
        b.uploader_setup.uploader_config = lambda d, t, uid: {"d": d}
        self._user = b.bot._connection.user if hasattr(b.bot, "_connection") else None
        b.bot._connection.user = types.SimpleNamespace(id=1)

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(self.bot, k, v)
        (self.bot.uploader_setup.setup_uploader_hooks, self.bot.uploader_setup.setup_sync,
         self.bot.uploader_setup.uploader_config) = self.saved_setup
        self.bot.bot._connection.user = self._user

    def inter(self, admin=True, uid=1000):
        sent = []

        class R:
            async def send_message(self_, t, **kw):
                sent.append(t)

            async def defer(self_, **kw):
                pass

        class F:
            async def send(self_, t, **kw):
                sent.append(t)
        user = Member(uid)
        user.admin, user.display_name = admin, "Chef"
        return types.SimpleNamespace(user=user, response=R(), followup=F()), sent

    def test_an_mitglied_mit_eigenem_sync(self):
        i, sent = self.inter()
        m = Member(5)
        asyncio.run(self.bot.uploader_cmd.callback(i, False, m))
        self.assertEqual(self.sync_for, [5])                       # eigener Kanal für das Mitglied
        self.assertEqual(len(m.sent), 1)
        names = [f.filename for f in m.sent[0][1]["files"]]
        self.assertEqual(names, ["uploader_config.json", "sync_config.json"])
        self.assertIn("Chef", m.sent[0][0])
        self.assertEqual(i.user.sent, [])                          # nichts an den Absender
        self.assertIn("Direktnachricht", sent[-1])

    def test_pn_gesperrt_nichts_umleiten(self):
        i, sent = self.inter()
        m = Member(5, forbid=True)
        asyncio.run(self.bot.uploader_cmd.callback(i, False, m))
        self.assertIn("Nichts geschickt", sent[-1])
        self.assertFalse(any("uploader_config" in str(x) for x in sent[:-1]))

    def test_nur_gildenleitung_und_nie_bots(self):
        i, sent = self.inter(admin=False)
        m = Member(5)
        asyncio.run(self.bot.uploader_cmd.callback(i, False, m))
        self.assertEqual(m.sent, [])
        i, sent = self.inter()
        b = Member(6, bot=True)
        asyncio.run(self.bot.uploader_cmd.callback(i, False, b))
        self.assertEqual(b.sent, [])
        self.assertEqual(self.sync_for, [])

    def test_ohne_fuer_wie_bisher(self):
        i, sent = self.inter()
        asyncio.run(self.bot.uploader_cmd.callback(i, False, None))
        self.assertEqual(self.sync_for, [1000])
        self.assertEqual(len(i.user.sent), 1)


if __name__ == "__main__":
    unittest.main()
