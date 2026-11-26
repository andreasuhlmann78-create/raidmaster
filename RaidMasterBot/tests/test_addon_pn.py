"""T-D-ADDONPN (ab Bot 1.5.198, Wunsch des Nutzers 26.11. 12:59 "der dc bot braucht mir die neuste version vom raidmaster addon
nicht mehr zu senden via pm"): /addon-pn an:False schaltet die PN "Neue RaidMaster-Version" für sich selbst aus; die anderen
registrierten Spieler bekommen sie weiter; an:True schaltet wieder ein. Nur IDs in state.json, nichts im Repo."""
import asyncio
import os
import sys
import types
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)


class AddonPn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        load_bot()
        cls.m = sys.modules["ankuendigung_bot"]

    def setUp(self):
        m = self.m
        self.saved_state = m.state.data.get("addon_pn_aus")
        m.state.data.pop("addon_pn_aus", None)
        self.saved_save = m.state.save
        m.state.save = lambda: None
        self.saved_profiles = dict(m.book.profiles.data)
        m.book.profiles.data.clear()
        m.book.profiles.data.update({"101": {}, "102": {}, "103": {}})
        self.got = {}
        self.saved_get, self.saved_sleep = m.bot.get_user, m.asyncio.sleep

        def get_user(uid):
            async def send(text):
                self.got.setdefault(uid, []).append(text)
            return types.SimpleNamespace(send=send)
        m.bot.get_user = get_user

        async def nosleep(_):
            return None
        m.asyncio.sleep = nosleep

    def tearDown(self):
        m = self.m
        m.state.save = self.saved_save
        if self.saved_state is None:
            m.state.data.pop("addon_pn_aus", None)
        else:
            m.state.data["addon_pn_aus"] = self.saved_state
        m.book.profiles.data.clear()
        m.book.profiles.data.update(self.saved_profiles)
        m.bot.get_user, m.asyncio.sleep = self.saved_get, self.saved_sleep

    def cmd(self, uid, an):
        replies = []

        async def send_message(text, ephemeral=False):
            replies.append((text, ephemeral))
        inter = types.SimpleNamespace(user=types.SimpleNamespace(id=uid),
                                      response=types.SimpleNamespace(send_message=send_message))
        asyncio.run(self.m.addon_pn_cmd.callback(inter, an))
        return replies[0]

    def test_aus_nur_fuer_sich_und_wieder_an(self):
        text, eph = self.cmd(102, False)
        self.assertTrue(eph)
        self.assertIn("keine PN mehr", text)
        self.cmd(102, False)                                     # doppelt: kein doppelter Eintrag
        self.assertEqual(self.m.state.data["addon_pn_aus"], ["102"])
        asyncio.run(self.m.notify_registered("🆕 Neue RaidMaster-Version"))
        self.assertEqual(sorted(self.got), [101, 103])           # 102 bekommt nichts, die anderen weiter
        self.got.clear()
        self.assertIn("wieder eine PN", self.cmd(102, True)[0])
        asyncio.run(self.m.notify_registered("🆕 Neue RaidMaster-Version"))
        self.assertEqual(sorted(self.got), [101, 102, 103])


if __name__ == "__main__":
    unittest.main()
