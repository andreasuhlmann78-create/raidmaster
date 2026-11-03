"""Offline-Tests Bot 1.5.98: Kanäle aus der Discord-Prüfung (anweisung-raidmaster-discord-kanaele.txt).
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import os
import sys
import unittest

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BOT_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server_setup  # noqa: E402
import uploader_setup  # noqa: E402
from test_testberichte import Guild  # noqa: E402  (Attrappen für Guild/Kanal/Webhook)


def src(name="bot.py"):
    with open(os.path.join(BOT_DIR, name), encoding="utf-8") as f:
        return f.read()


class Named:
    def __init__(self, name, cid):
        self.name, self.id = name, cid


class AHSentinelChannel(unittest.TestCase):
    def test_alter_name_aktionshaus_wird_ahsentinel(self):
        # nur #ahsentinel auf dem Server
        self.assertEqual(server_setup.find_channel([Named("ahsentinel", 1), Named("buffsentinel", 2)], "ahsentinel").id, 1)
        # beide da: #ahsentinel hat Vorrang
        self.assertEqual(server_setup.find_channel([Named("aktionshaus", 9), Named("ahsentinel", 1)], "ahsentinel").id, 1)
        # alter Server nur mit #aktionshaus: wird als Alias gefunden
        self.assertEqual(server_setup.find_channel([Named("aktionshaus", 9)], "ahsentinel").id, 9)
        self.assertIsNone(server_setup.find_channel([Named("allgemein", 3)], "ahsentinel"))

    def test_bot_postet_ahsentinel_nach_ahsentinel(self):
        s = src()
        block = s[s.index("EXTRA_ADDONS = {"):s.index("async def extra_channel")]
        self.assertIn('"channel_name": "ahsentinel"', block)
        self.assertNotIn('"channel_name": "aktionshaus"', block)
        rel = s[s.index("async def check_extra_releases"):s.index("async def check_extra_releases") + 2500]
        self.assertEqual(rel.count("await extra_channel(meta)"), 2)          # Aufräumen und Posten
        self.assertNotIn('channel_by_id(cfg.get(meta["channel"]))', rel)

    def test_einrichten_ohne_aktionshaus_und_raid(self):
        names = [(c[0], c[1]) for cat in server_setup.BASE_TOP + server_setup.BASE_BOTTOM for c in cat["channels"]]
        self.assertNotIn(("text", "aktionshaus"), names)
        self.assertNotIn(("voice", "Raid"), names)
        self.assertNotIn('("aktionshaus_channel_id", "aktionshaus")', src("server_setup.py"))

    def test_alte_aktionshaus_dateien_nicht_posten(self):
        s = src()
        line = next(l for l in s.splitlines() if l.startswith("ANNOUNCE_CHANNELS = "))
        self.assertNotIn("aktionshaus", line)

    def test_vorstellung_nie_als_fortsetzung_geloescht(self):
        s = src()
        body = s[s.index("async def remove_old_releases"):s.index("async def remove_old_releases") + 2600]
        self.assertIn("announced_ids", body)
        self.assertIn("m.id in announced_ids", body)
        self.assertIn("async def repair_missing_announcements", s)


class TestChannelAtStart(unittest.TestCase):
    def test_fehlender_kanal_wird_angelegt(self):
        g = Guild()
        ch, note = asyncio.run(uploader_setup.ensure_test_channel(g))
        self.assertIsNotNone(ch)
        self.assertIsNone(note)
        self.assertEqual(ch.name, "testberichte")
        self.assertEqual(ch.category.name, "🔒 OFFIZIERE")
        self.assertIs(ch.overwrites[g.default_role].view_channel, False)
        ch2, _ = asyncio.run(uploader_setup.ensure_test_channel(g))
        self.assertIs(ch2, ch)
        self.assertEqual(len(g.text_channels), 1)

    def test_ohne_recht_hinweis(self):
        ch, note = asyncio.run(uploader_setup.ensure_test_channel(Guild(manage_channels=False)))
        self.assertIsNone(ch)
        self.assertIn("Kanäle verwalten", note)

    def test_bot_legt_beim_start_an(self):
        s = src()
        start = s[s.index("await post_guild_bank()\n            except Exception:"):][:900]
        self.assertIn("await ensure_test_channel()", start)
        body = s[s.index("async def ensure_test_channel"):s.index("async def repair_missing_announcements")]
        self.assertIn("uploader_setup.ensure_test_channel", body)
        self.assertIn('cfg["testberichte_channel_id"] = ch.id', body)


if __name__ == "__main__":
    unittest.main()
