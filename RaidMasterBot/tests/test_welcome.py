"""Offline-Test für server_setup.welcome_text und die Kanal-Aliase (Bot 1.5.95).
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server_setup  # noqa: E402

# alle Kanäle unter den ursprünglichen Namen (neu eingerichteter Server)
ORIGINAL = {"gruppensuche": 1, "handwerk-und-handel": 2, "ruhmeshalle": 3, "raid-addon": 4, "regeln": 5,
            "verhaltensregeln": 6, "addon-hilfe": 7, "befehle": 8}
# Server mit von Hand umbenannten Kanälen
RENAMED = {"gruppensuche-für-dungeons": 11, "handwerk-und-handel": 2, "ruhmeshalle": 3, "raid-addon": 4,
           "dkp-regeln": 15, "verhaltensregeln": 6, "addon-hilfe": 7, "befehle": 8}


class Welcome(unittest.TestCase):
    def test_unter_discord_limit(self):
        for chans in ({}, ORIGINAL, RENAMED):
            for name in ("Alpine Vanguard", "", "Ein ganz besonders langer Gildenname"):
                text = server_setup.welcome_text(name, chans, 123456789012345678)
                self.assertLess(len(text), 2000, f"{len(text)} Zeichen")

    def test_alle_links_original(self):
        text = server_setup.welcome_text("Alpine Vanguard", ORIGINAL, 42)
        for cid in ORIGINAL.values():
            self.assertIn(f"<#{cid}>", text)
        self.assertNotIn("**#", text)

    def test_alle_links_umbenannt(self):
        text = server_setup.welcome_text("Alpine Vanguard", RENAMED, 42)
        for cid in RENAMED.values():
            self.assertIn(f"<#{cid}>", text)
        self.assertNotIn("**#", text)

    def test_ohne_kanaele_fetter_text(self):
        text = server_setup.welcome_text("Alpine Vanguard", {}, None)
        self.assertIn("**#regeln**", text)
        self.assertIn("**Offizier**", text)

    def test_inhalt(self):
        text = server_setup.welcome_text("Alpine Vanguard", ORIGINAL, 42)
        self.assertIn("Welt-PvP", text)
        self.assertIn("deutschsprachige", text)
        self.assertIn("Charakternamen", text)
        self.assertNotIn("allgemein", text)


class Aliases(unittest.TestCase):
    def test_original_geht_vor(self):
        self.assertEqual(server_setup.channel_id({"regeln": 1, "dkp-regeln": 2}, "regeln"), 1)

    def test_alias_und_gross_klein(self):
        self.assertEqual(server_setup.channel_id({"DKP-Regeln": 2}, "regeln"), 2)
        self.assertIsNone(server_setup.channel_id({"allgemein": 3}, "regeln"))

    def test_find_channel(self):
        items = [SimpleNamespace(name="gruppensuche-für-dungeons"), SimpleNamespace(name="dkp-regeln")]
        self.assertEqual(server_setup.find_channel(items, "regeln").name, "dkp-regeln")
        self.assertEqual(server_setup.find_channel(items, "gruppensuche").name, "gruppensuche-für-dungeons")
        self.assertIsNone(server_setup.find_channel(items, "allgemein"))


if __name__ == "__main__":
    unittest.main()
