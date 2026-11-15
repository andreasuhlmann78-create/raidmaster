"""T-D3-BEUTEPOST / T-D3-DKPNACHRICHT: beutepost_bot.py und dkp_nachricht_bot.py (D-3 Schritt 27, ab Bot 1.5.174).

Bis 1.5.173 gab es dafür keine Ablauf-Tests. Beute-Posts: der Tooltip-Speicher behält höchstens 400 Items (die
ältesten fallen weg). DKP-Nachricht: je Raid genau einmal, alte Raids beim ersten Start nicht nachgeschickt,
nur an Anwesende/Verdienende, nie an Bots oder wer abbestellt hat; /dkp-nachricht an|aus schaltet um.
"""
import asyncio
import os
import sys
import time
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Beutepost(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["beutepost_bot"]

    def test_gleiche_funktionen_in_bot(self):
        self.assertIs(self.bot.post_new_loot, self.m.post_new_loot)
        self.assertIs(sys.modules["anmeldung_bot"].show_tip, self.m.show_tip)            # ab 1.5.180 dort benutzt
        self.assertIs(sys.modules["testupload_bot"].send_loot_list, self.m.send_loot_list)   # ab 1.5.176 dort benutzt

    def test_tooltip_speicher_hoechstens_400(self):
        m = self.m
        saved = dict(m.state.data)
        try:
            m.state.data["tip_cache"] = {str(i): {"t": i} for i in range(1, 401)}
            m.remember_tip("|cffa335ee|Hitem:19019::::::::60:::::|h[Donnerzorn]|h|r", {"n": "Donnerzorn"}, None)
            store = m.state.data["tip_cache"]
            self.assertEqual(len(store), 400)
            self.assertNotIn("1", store)                                  # ältester Eintrag weg
            self.assertIn("19019", store)
            m.remember_tip(None, None, None)                              # ohne Item: nichts
            self.assertEqual(len(store), 400)
        finally:
            m.state.data.clear()
            m.state.data.update(saved)


class Member:
    def __init__(self, mid, bot=False):
        self.id, self.bot, self.dms = mid, bot, []

    async def send(self, text):
        self.dms.append(text)


class DkpNachricht(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["dkp_nachricht_bot"]

    def setUp(self):
        m = self.m
        self.saved = {k: getattr(m, k) for k in ("find_member_for_char", "test_info")}
        self.saved_rmd = (m.rmd.raid_summaries, m.rmd.raid_dm_text)
        self.saved_book = (m.book.alt_links, m.book.profile)
        self.saved_state, self.saved_save, self.saved_cfg = dict(m.state.data), m.state.save, dict(m.cfg)
        self.saved_sleep, self.saved_data = m.asyncio.sleep, m.bot.dkp_data
        m.state.save = lambda: None
        m.state.data["dm_sent"] = []
        m.cfg["raid_dms"] = True
        m.test_info = lambda db: None
        m.bot.dkp_data = {"players": {}}
        m.book.alt_links = lambda: {}
        self.members = {"Thrall": Member(1), "Jaina": Member(2), "Botty": Member(3, bot=True), "Ruhig": Member(4)}
        m.book.profile = lambda uid: {"no_dm": True} if uid == 4 else {}

        async def find(name):
            return self.members.get(name)
        m.find_member_for_char = find
        m.rmd.raid_dm_text = lambda summ, row, data, main: f"DKP {row['name']}"

        async def nosleep(_):
            return None
        m.asyncio.sleep = nosleep

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        m.rmd.raid_summaries, m.rmd.raid_dm_text = self.saved_rmd
        m.book.alt_links, m.book.profile = self.saved_book
        m.state.save = self.saved_save
        m.state.data.clear()
        m.state.data.update(self.saved_state)
        m.cfg.clear()
        m.cfg.update(self.saved_cfg)
        m.asyncio.sleep, m.bot.dkp_data = self.saved_sleep, self.saved_data

    def test_gleiche_funktionen_in_bot(self):
        self.assertIs(self.bot.send_raid_dms, self.m.send_raid_dms)
        self.assertIs(sys.modules["monatlich_bot"].find_member_for_char, self.saved["find_member_for_char"])

    def test_einmal_nur_an_teilnehmer(self):
        rows = [{"name": "Thrall", "present": True}, {"name": "Jaina", "earned": 5}, {"name": "Weg"},
                {"name": "Botty", "present": True}, {"name": "Ruhig", "present": True}]
        self.m.rmd.raid_summaries = lambda data: [{"id": "r1", "t": time.time() - 600, "rows": rows},
                                                  {"id": "alt", "t": time.time() - 3 * 86400, "rows": rows}]
        asyncio.run(self.m.send_raid_dms())
        self.assertEqual(self.members["Thrall"].dms, ["DKP Thrall"])
        self.assertEqual(self.members["Jaina"].dms, ["DKP Jaina"])
        self.assertEqual((self.members["Botty"].dms, self.members["Ruhig"].dms), ([], []))
        self.assertEqual(sorted(self.m.state.data["dm_sent"]), ["alt", "r1"])    # alter Raid gemerkt, nicht geschickt
        asyncio.run(self.m.send_raid_dms())                                       # nie doppelt
        self.assertEqual(len(self.members["Thrall"].dms), 1)

    def test_an_aus(self):
        prof = {"name": "Thrall"}
        saved = (self.m.book.profile, self.m.book.profiles.save)
        self.m.book.profile = lambda uid: prof
        self.m.book.profiles.save = lambda: None
        msgs = []

        class R:
            async def send_message(self_, text, **kw):
                msgs.append(text)
        try:
            inter = types.SimpleNamespace(user=types.SimpleNamespace(id=1), response=R())
            asyncio.run(self.m.dkp_dm_cmd.callback(inter, types.SimpleNamespace(value="aus")))
            self.assertTrue(prof["no_dm"])
            asyncio.run(self.m.dkp_dm_cmd.callback(inter, types.SimpleNamespace(value="an")))
            self.assertNotIn("no_dm", prof)
        finally:
            self.m.book.profile, self.m.book.profiles.save = saved
        self.assertIn("Keine DKP-Nachrichten mehr", msgs[0])


if __name__ == "__main__":
    unittest.main()
