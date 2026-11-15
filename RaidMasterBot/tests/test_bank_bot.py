"""T-D3-BANK: Raidfähigkeit und Gildenbank aus bank_bot.py (D-3 Schritt 10, ab Bot 1.5.155) – Ablauf ohne Netz.

Bis 1.5.154 gab es für post_raid_ready nur eine Text-Prüfung des Quelltexts. Hier läuft die Funktion selbst:
nur #offiziere, Vorschlag einmal, Wochenmeldung montags einmal, alter Stand (> 14 Tage) nicht als aktuell.
"""
import asyncio
import os
import sys
import types
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

RR = {"raid": "onyxia", "phase": "aufbau", "aktiv": 23, "groesse": 40, "tanks": 2, "tanksSoll": 4, "heiler": 5,
      "heilerSoll": 10, "pct": 58, "wochen": 3, "t": 1794470000}


class Ch:
    def __init__(self, name):
        self.name = name
        self.sent = []

    async def send(self, text, **kw):
        self.sent.append(text)


def monday_after(ts: int) -> datetime:
    d = datetime.fromtimestamp(ts, ZoneInfo("Europe/Zurich")) + timedelta(days=1)
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d


class Raidfaehigkeit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["bank_bot"]

    def setUp(self):
        m = self.m
        self.saved = (m.guildsentinel_db, m.GS_READY_PATH, m.bot_guild, m.state.save, dict(m.state.data))
        self.db = {"raidReady": dict(RR, vorschlag="Übergang")}
        m.guildsentinel_db = lambda: self.db
        m.GS_READY_PATH = os.path.join(os.path.dirname(__file__), "gibt-es-nicht.lua")
        self.allgemein, self.offiziere = Ch("allgemein"), Ch("offiziere")
        m.bot_guild = lambda: types.SimpleNamespace(text_channels=[self.allgemein, self.offiziere])
        m.state.save = lambda: None
        m.state.data.pop("raidready_suggestion", None)
        m.state.data.pop("raidready_week", None)

    def tearDown(self):
        m = self.m
        m.guildsentinel_db, m.GS_READY_PATH, m.bot_guild, m.state.save = self.saved[:4]
        m.state.data.clear()
        m.state.data.update(self.saved[4])

    def test_gleiche_funktionen_in_bot(self):
        self.assertIs(self.bot.post_raid_ready, self.m.post_raid_ready)
        self.assertIs(self.bot.post_guild_bank, self.m.post_guild_bank)
        self.assertEqual(self.bot.BANK_CHANNEL, self.m.BANK_CHANNEL)

    def test_nur_offiziere_und_je_einmal(self):
        now = monday_after(RR["t"])
        self.assertEqual(asyncio.run(self.m.post_raid_ready(now)), ["vorschlag", "woche"])
        self.assertEqual(self.allgemein.sent, [])
        self.assertEqual(len(self.offiziere.sent), 2)
        self.assertIn("Raidfähig (Onyxia)", self.offiziere.sent[1])
        self.assertEqual(asyncio.run(self.m.post_raid_ready(now + timedelta(hours=1))), [])   # nie doppelt
        self.assertEqual(len(self.offiziere.sent), 2)

    def test_nicht_montag_keine_wochenmeldung(self):
        self.db = {"raidReady": dict(RR)}                       # ohne Vorschlag
        now = monday_after(RR["t"]) + timedelta(days=1)
        self.assertEqual(asyncio.run(self.m.post_raid_ready(now)), [])
        self.assertEqual(self.offiziere.sent, [])

    def test_alter_stand_nicht_als_aktuell(self):
        self.db = {"raidReady": dict(RR)}
        now = monday_after(RR["t"] + 21 * 86400)               # Stand drei Wochen alt
        self.assertEqual(asyncio.run(self.m.post_raid_ready(now)), [])
        self.assertEqual(self.offiziere.sent, [])
        self.assertEqual(self.m.state.data.get("raidready_week"), now.strftime("%G-W%V"))   # Woche trotzdem gemerkt

    def test_ohne_daten_oder_ohne_kanal_nichts(self):
        self.db = None
        self.assertEqual(asyncio.run(self.m.post_raid_ready(monday_after(RR["t"]))), [])
        self.db = {"raidReady": dict(RR, vorschlag="Übergang")}
        self.m.bot_guild = lambda: types.SimpleNamespace(text_channels=[self.allgemein])
        self.assertEqual(asyncio.run(self.m.post_raid_ready(monday_after(RR["t"]))), [])
        self.assertEqual(self.allgemein.sent, [])


if __name__ == "__main__":
    unittest.main()
