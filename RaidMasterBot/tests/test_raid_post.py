"""T-R1 (Bot 1.5.126): Funktionstest für das Posten eines neuen Raids (raid_post.py, aus bot.py raid_create).
Scheitert target.send (403), bleibt kein Raid im Buch und der Ersteller bekommt eine klare Meldung.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace as N
from zoneinfo import ZoneInfo

import discord

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import raid_post  # noqa: E402
import raidmaster_data as rmd  # noqa: E402


class Target:
    def __init__(self, fail=False):
        self.fail, self.sent = fail, []
        self.mention, self.name = "#barrow-anmeldung", "barrow-anmeldung"

    async def send(self, embed=None, view=None):
        if self.fail:
            raise discord.Forbidden(N(status=403, reason="Forbidden"), {"code": 50013, "message": "Missing Permissions"})
        self.sent.append(embed)
        return N(id=4242)


def run(fail):
    replies = []

    async def reply(t):
        replies.append(t)
    d = tempfile.TemporaryDirectory()
    book = rmd.RaidBook(d.name)
    raid = book.create("T", datetime.now(ZoneInfo("Europe/Zurich")) + timedelta(days=1), "", 0, 1, 81)
    msg = asyncio.run(raid_post.post_new_raid(book, raid, Target(fail), "embed", None, reply))
    reloaded = rmd.RaidBook(d.name)                               # wie nach einem Neustart
    return d, msg, raid, replies, reloaded


class PostNewRaid(unittest.TestCase):
    def test_T_R1_posten_scheitert(self):
        d, msg, raid, replies, reloaded = run(fail=True)
        self.addCleanup(d.cleanup)
        self.assertIsNone(msg)
        self.assertIsNone(reloaded.get(raid["id"]))                 # kein Raid ohne Nachricht im gespeicherten Buch
        self.assertFalse([r for r in reloaded.all() if not r.get("message_id")])
        self.assertEqual(len(replies), 1)
        self.assertIn("Nachrichten senden", replies[0])
        self.assertIn("403", replies[0])

    def test_erfolg_message_id_gesetzt(self):
        d, msg, raid, replies, reloaded = run(fail=False)
        self.addCleanup(d.cleanup)
        self.assertEqual(msg.id, 4242)
        self.assertEqual(reloaded.get(raid["id"])["message_id"], 4242)
        self.assertEqual(replies, ["Raid erstellt in #barrow-anmeldung."])


if __name__ == "__main__":
    unittest.main()
