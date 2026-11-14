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


if __name__ == "__main__":
    unittest.main()
