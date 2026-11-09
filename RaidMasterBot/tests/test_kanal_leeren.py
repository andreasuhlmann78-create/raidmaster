"""Offline-Test (Bot 1.5.103, ab 1.5.109 ohne aktiven Eintrag): Kanal STRENG EINMALIG leeren.
- nur einmal je Kennung, nur bis "until" (auch wenn die Bot-Daten verloren gehen), nur Nachrichten vor "before"
- angeheftete Nachrichten bleiben
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import os
import sys
import unittest
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server_setup  # noqa: E402

ZH = ZoneInfo("Europe/Zurich")
# Muster-Eintrag wie der frühere "mc-dkp" (Bot 1.5.103–1.5.108); im Code ist seit 1.5.109 kein Eintrag mehr aktiv
SPEC = {"tag": "start-wow-forever-2026-11-04",
        "before": datetime(2026, 11, 4, 7, 0, tzinfo=ZH),
        "until": datetime(2026, 11, 4, 12, 0, tzinfo=ZH)}


def at(h, m=0, day=4):
    return datetime(2026, 11, day, h, m, tzinfo=ZH)


class FakeChannel:
    def __init__(self, msgs):
        self.msgs = list(msgs)
        self.kwargs = None

    async def purge(self, limit=None, before=None, check=None, reason=None):
        self.kwargs = {"limit": limit, "before": before}
        hit = lambda m: (before is None or m.created_at < before) and check(m)  # noqa: E731
        gone = [m for m in self.msgs if hit(m)]
        self.msgs = [m for m in self.msgs if not hit(m)]
        return gone


class StrengEinmalig(unittest.TestCase):
    def test_kein_eintrag_mehr_aktiv(self):
        # "mc-dkp" galt nur bis 04.11.2026 12:00 und ist entfernt (offen-raidmaster.txt Punkt 1)
        self.assertEqual(server_setup.CLEAR_CHANNELS_ONCE, {})

    def test_zeitfenster(self):
        self.assertTrue(server_setup.clear_allowed(SPEC, at(7, 20), None))
        self.assertTrue(server_setup.clear_allowed(SPEC, at(11, 59), None))
        self.assertFalse(server_setup.clear_allowed(SPEC, at(12, 0), None))
        self.assertFalse(server_setup.clear_allowed(SPEC, at(9, 0, day=5), None))     # morgen: nie mehr
        self.assertFalse(server_setup.clear_allowed(SPEC, at(9, 0, day=11), None))    # nächste Woche: nie mehr

    def test_bot_daten_verloren_nach_frist(self):
        # state.json weg (z. B. /daten-import, Neuinstallation): nach der Frist trotzdem nichts löschen
        self.assertFalse(server_setup.clear_allowed(SPEC, at(18, 0), None))

    def test_schon_erledigt(self):
        self.assertFalse(server_setup.clear_allowed(SPEC, at(8, 0), SPEC["tag"]))

    def test_unvollstaendiger_eintrag_loescht_nie(self):
        self.assertFalse(server_setup.clear_allowed({"tag": "x"}, at(8, 0), None))
        self.assertFalse(server_setup.clear_allowed("x", at(8, 0), None))

    def test_nur_alte_nachrichten_und_nicht_angeheftet(self):
        msgs = [SimpleNamespace(id=1, pinned=False, created_at=at(6, 0)),
                SimpleNamespace(id=2, pinned=True, created_at=at(6, 10)),     # angeheftet: bleibt
                SimpleNamespace(id=3, pinned=False, created_at=at(7, 30))]    # nach 07:00: bleibt
        ch = FakeChannel(msgs)
        n = asyncio.run(server_setup.clear_channel(ch, SPEC["before"], "test"))
        self.assertEqual(n, 1)
        self.assertEqual([m.id for m in ch.msgs], [2, 3])
        self.assertIsNone(ch.kwargs["limit"])
        self.assertEqual(ch.kwargs["before"], at(7, 0))


if __name__ == "__main__":
    unittest.main()
