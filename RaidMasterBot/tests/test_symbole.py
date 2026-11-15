"""T-D3-SYMBOLE: Symbole/Emojis aus symbole_bot.py (D-3 Schritt 7, ab Bot 1.5.152) – ohne Netz, ohne Discord.

Prüft das Verhalten von class_emoji und item_emoji im neuen Modul: Merker im state, Ersatz-Emoji, wenn Discord
kein App-Emoji liefert, und dass bot.py dieselben Funktionen benutzt.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Symbole(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["symbole_bot"]
        import render
        cls.rimg = render

    def setUp(self):
        self.saved_state = dict(self.m.state.data)
        self.saved_save = self.m.state.save
        self.saves = 0

        def save():
            self.saves += 1
        self.m.state.save = save
        self.saved_bot = self.m.bot

    def tearDown(self):
        self.m.state.data.clear()
        self.m.state.data.update(self.saved_state)
        self.m.state.save = self.saved_save
        self.m.bot = self.saved_bot

    def test_gleiche_funktionen_in_bot(self):
        # ab 1.5.174 benutzt bot.py die Symbole nicht mehr selbst; die Module, die sie brauchen, holen sie hier
        bp = sys.modules["beutepost_bot"]
        self.assertIs(bp.class_emoji, self.m.class_emoji)
        self.assertIs(bp.item_emoji, self.m.item_emoji)
        self.assertIs(bp.wowhead_tip, self.m.wowhead_tip)
        self.assertEqual(bp.WOWHEAD_FLAVOR, self.m.WOWHEAD_FLAVOR)

    def test_unbekannte_klasse_leer(self):
        self.assertEqual(asyncio.run(self.m.class_emoji("KEINE")), "")
        self.assertEqual(asyncio.run(self.m.class_emoji(None)), "")

    def test_merker_wird_benutzt(self):
        self.m.state.data["class_emojis"] = {"MAGE": "<:rm_mage:1>"}
        self.assertEqual(asyncio.run(self.m.class_emoji("mage")), "<:rm_mage:1>")
        self.assertEqual(self.saves, 0)                        # aus dem Merker: nichts gespeichert

    def test_ersatz_wenn_discord_nichts_liefert(self):
        self.m.state.data["class_emojis"] = {}

        async def kaputt():
            raise RuntimeError("kein Netz")
        self.m.bot = types.SimpleNamespace(fetch_application_emojis=kaputt)
        r = asyncio.run(self.m.class_emoji("WARRIOR"))
        self.assertEqual(r, self.rimg.CLASS_FALLBACK_EMOJI.get("WARRIOR", ""))
        self.assertIsNone(self.m.state.data["class_emojis"]["WARRIOR"])   # gemerkt: nicht bei jedem Aufruf neu
        self.assertEqual(self.saves, 1)

    def test_item_ohne_symbol_qualitaetsquadrat(self):
        async def kein_name(link, tip):
            return None
        orig = self.m.item_icon_name
        self.m.item_icon_name = kein_name
        try:
            self.assertEqual(asyncio.run(self.m.item_emoji(None, {"q": 3})), "🟦")
            self.assertEqual(asyncio.run(self.m.item_emoji(None, {"q": 5})), "🟧")
        finally:
            self.m.item_icon_name = orig


if __name__ == "__main__":
    unittest.main()
