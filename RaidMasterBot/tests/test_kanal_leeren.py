"""Offline-Test (Bot 1.5.102): Kanal einmal leeren (z. B. #mc-dkp vor dem Serverstart), angeheftete bleiben.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server_setup  # noqa: E402


class FakeChannel:
    def __init__(self, msgs):
        self.msgs = list(msgs)
        self.kwargs = None

    async def purge(self, limit=None, check=None, reason=None):
        self.kwargs = {"limit": limit, "reason": reason}
        gone = [m for m in self.msgs if check(m)]
        self.msgs = [m for m in self.msgs if not check(m)]
        return gone


class KanalLeeren(unittest.TestCase):
    def test_alles_ausser_angeheftet(self):
        msgs = [SimpleNamespace(id=i, pinned=(i == 2)) for i in range(5)]
        ch = FakeChannel(msgs)
        n = asyncio.run(server_setup.clear_channel(ch, "test"))
        self.assertEqual(n, 4)
        self.assertEqual([m.id for m in ch.msgs], [2])
        self.assertIsNone(ch.kwargs["limit"])          # ganzer Verlauf, nicht nur die letzten 100

    def test_nur_mc_dkp_und_feste_kennung(self):
        self.assertEqual(list(server_setup.CLEAR_CHANNELS_ONCE), ["mc-dkp"])
        self.assertTrue(all(server_setup.CLEAR_CHANNELS_ONCE.values()))


if __name__ == "__main__":
    unittest.main()
