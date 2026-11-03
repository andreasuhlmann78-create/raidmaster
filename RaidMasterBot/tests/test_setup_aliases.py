"""Offline-Test für /raidmaster-einrichten mit umbenannten Kanälen (Bot 1.5.95, CHANNEL_ALIASES).
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server_setup  # noqa: E402


class FakeChannel:
    def __init__(self, name, category_id, cid):
        self.name, self.category_id, self.id = name, category_id, cid
        self.edits = []

    async def edit(self, **kw):
        self.edits.append(kw)
        if "category" in kw:
            self.category_id = kw["category"].id


class FakeGuild:
    def __init__(self, categories, text):
        self.categories, self.text_channels, self.voice_channels = categories, text, []
        self.created = []

    async def create_category(self, name, **kw):
        c = FakeChannel(name, None, 900 + len(self.categories))
        self.categories.append(c)
        return c

    async def create_text_channel(self, name, **kw):
        c = FakeChannel(name, kw["category"].id, 800 + len(self.created))
        self.created.append(name)
        self.text_channels.append(c)
        return c


def run(guild, cat_def):
    report, created = [], {}
    asyncio.run(server_setup._ensure_category(guild, cat_def, {}, report, created, set(), "test"))
    return report, created


class SetupAliases(unittest.TestCase):
    CAT = {"name": "📌 INFO", "mode": None,
           "channels": [("text", "willkommen", None, None), ("text", "regeln", None, None)]}

    def test_umbenannt_bleibt_wo_er_ist(self):
        info = FakeChannel("📌 INFO", None, 1)
        dkp = FakeChannel("dkp-regeln", 2, 20)            # liegt bewusst in einer anderen Kategorie
        guild = FakeGuild([info, FakeChannel("⚔️ RAID", None, 2)], [FakeChannel("willkommen", 1, 10), dkp])
        report, created = run(guild, self.CAT)
        self.assertEqual(guild.created, [])               # kein zweites #regeln
        self.assertEqual(dkp.edits, [])                   # nicht verschoben, Rechte unverändert
        self.assertEqual(dkp.category_id, 2)
        self.assertIs(created["regeln"], dkp)             # unter dem ursprünglichen Namen gespeichert
        self.assertTrue(any("dkp-regeln" in r for r in report))

    def test_original_wie_bisher(self):
        info = FakeChannel("📌 INFO", None, 1)
        regeln = FakeChannel("regeln", 2, 21)
        guild = FakeGuild([info, FakeChannel("⚔️ RAID", None, 2)], [FakeChannel("willkommen", 1, 10), regeln])
        run(guild, self.CAT)
        self.assertEqual(guild.created, [])
        self.assertEqual(regeln.category_id, 1)           # Originalname: wird wie bisher einsortiert

    def test_fehlt_wird_angelegt(self):
        guild = FakeGuild([FakeChannel("📌 INFO", None, 1)], [FakeChannel("willkommen", 1, 10)])
        run(guild, self.CAT)
        self.assertEqual(guild.created, ["regeln"])

    def test_allgemein_nicht_mehr_in_struktur(self):
        names = [n for cat in server_setup.BASE_TOP + server_setup.BASE_BOTTOM for _, n, _, _ in cat["channels"]]
        self.assertNotIn("allgemein", names)
        self.assertIn("gruppensuche", names)
        self.assertIn("regeln", names)


if __name__ == "__main__":
    unittest.main()
