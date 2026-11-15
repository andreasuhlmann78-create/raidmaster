"""T-D3-ANMELDUNG: anmeldung_bot.py (D-3 Schritt 33, ab Bot 1.5.180) – Knopf-Verteilung ohne Netz.

Bis 1.5.179 gab es für on_interaction keinen Ablauf-Test. Hier: der Bot hat genau diese on_interaction (beim
Import am selben Bot-Objekt angemeldet); Knöpfe werden an die richtige Stelle verteilt (Tooltip, Gildenname,
Bewerbung, Export, Ersatz); andere Interaktionen (Befehle) und fremde Knöpfe werden ignoriert; ein unbekannter
Raid wird gemeldet; ein Fehler im Gildennamen-Knopf führt zu einer freundlichen Meldung statt Absturz.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Resp:
    def __init__(self):
        self.messages, self.done = [], False

    def is_done(self):
        return self.done

    async def send_message(self, text, **kw):
        self.messages.append(text)
        self.done = True


class Anmeldung(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["anmeldung_bot"]

    def setUp(self):
        m = self.m
        names = ("show_tip", "handle_name_button", "handle_apply_button", "send_export", "accept_substitute")
        self.saved = {k: getattr(m, k) for k in names}
        self.saved_get = m.book.get
        self.calls = []

        def rec(name, fail=False):
            async def f(*a):
                self.calls.append((name, a[1:]))
                if fail:
                    raise RuntimeError("kaputt")
            return f
        m.show_tip = rec("tip")
        m.handle_name_button = rec("name", fail=True)
        m.handle_apply_button = rec("apply")
        m.send_export = rec("export")
        m.accept_substitute = rec("sub")
        m.book.get = lambda rid: {"id": rid} if rid == "5" else None

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(self.m, k, v)
        self.m.book.get = self.saved_get

    def klick(self, cid, typ=None):
        import discord
        inter = types.SimpleNamespace(type=typ or discord.InteractionType.component, data={"custom_id": cid},
                                      response=Resp())
        asyncio.run(self.m.on_interaction(inter))
        return inter.response.messages

    def test_am_bot_angemeldet(self):
        self.assertIs(self.bot.bot.on_interaction, self.m.on_interaction)
        self.assertIs(self.bot.bot.tree.get_command("charakter").callback, self.m.character_cmd.callback)

    def test_verteilung(self):
        import discord
        self.klick("rmtip:123")
        self.klick("rmapply:annehmen:7")
        self.klick("rm:export:5")
        self.klick("rm:sub:5")
        self.assertEqual([c[0] for c in self.calls], ["tip", "apply", "export", "sub"])
        self.assertEqual(self.calls[1][1], ("annehmen", "7"))
        self.calls.clear()
        self.assertEqual(self.klick("fremd:1:x"), [])                     # fremder Knopf: keine Antwort
        self.assertEqual(self.klick("rm:export:5", typ=discord.InteractionType.application_command), [])
        self.assertEqual(self.calls, [])                                    # fremde Knöpfe, Befehle: nichts

    def test_unbekannter_raid_und_fehler(self):
        self.assertIn("gibt es nicht mehr", self.klick("rm:export:99")[0])
        with self.assertLogs("raidmaster", level="ERROR"):
            msg = self.klick("rmname:stimme:3")
        self.assertIn("etwas schiefgelaufen", msg[0])


if __name__ == "__main__":
    unittest.main()
