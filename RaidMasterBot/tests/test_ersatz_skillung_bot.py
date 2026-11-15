"""T-D3-ERSATZ / T-D3-SKILLUNG: ersatz_bot.py und skillung_bot.py (D-3 Schritt 25, ab Bot 1.5.172) – ohne Netz.

Bis 1.5.171 gab es für die Ersatzbank keinen Ablauf-Test. Hier läuft er selbst: gefragt wird nur innerhalb von
48 Stunden vor dem Raid, nicht bei Testraids, geschlossenen oder vollen Raids; der erste passende Kandidat bekommt
eine PN mit Knopf und wird gemerkt. Zusage: angemeldet, Offiziere informiert; voller Raid -> bleibt auf der Bank.
"""
import asyncio
import os
import sys
import time
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Member:
    def __init__(self):
        self.dms = []

    async def send(self, text, view=None, **kw):
        self.dms.append((text, view))


class Ersatz(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["ersatz_bot"]

    def setUp(self):
        m = self.m
        self.saved = {k: getattr(m, k) for k in ("sub_candidates", "bot_guild", "update_raid_message", "channel_by_id")}
        self.saved_book = (m.book.save, m.book.count_status, m.book.profile, m.book.signup)
        self.saved_cfg = dict(m.cfg)
        m.book.save = lambda: None
        m.book.count_status = lambda raid, st: sum(1 for s in raid["signups"].values() if s["status"] == st)
        self.member = Member()
        m.bot_guild = lambda: types.SimpleNamespace(get_member=lambda uid: self.member)
        m.sub_candidates = lambda raid, leaver: [("42", {"name": "Bankdrücker"})]
        m.cfg["auto_substitute"] = True

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        m.book.save, m.book.count_status, m.book.profile, m.book.signup = self.saved_book
        m.cfg.clear()
        m.cfg.update(self.saved_cfg)

    def raid(self, **kw):
        return dict({"id": 8, "title": "MC", "start": int(time.time()) + 3600, "signups": {}, "max": 2}, **kw)

    def test_gleiche_funktionen_in_bot(self):
        self.assertIs(self.bot.offer_substitute, self.m.offer_substitute)
        self.assertIs(self.bot.accept_substitute, self.m.accept_substitute)
        self.assertIs(self.bot.sync_specs, sys.modules["skillung_bot"].sync_specs)

    def test_fragt_ersten_kandidaten(self):
        r = self.raid()
        asyncio.run(self.m.offer_substitute(r, {"role": "heal"}))
        self.assertEqual(r["subs_asked"], ["42"])
        text, view = self.member.dms[0]
        self.assertIn("Ein Platz ist frei", text)
        self.assertEqual(view.children[0].custom_id, "rm:sub:8")

    def test_fragt_nicht(self):
        for r in (self.raid(start=int(time.time()) + 49 * 3600), self.raid(test=True), self.raid(closed=True),
                  self.raid(signups={"1": {"status": "an"}, "2": {"status": "an"}})):
            asyncio.run(self.m.offer_substitute(r, {"role": "tank"}))
            self.assertNotIn("subs_asked", r)
        self.m.cfg["auto_substitute"] = False
        asyncio.run(self.m.offer_substitute(self.raid(), {"role": "tank"}))
        self.assertEqual(self.member.dms, [])

    def zusage(self, raid):
        msgs, officer = [], []

        class R:
            async def send_message(self_, text, **kw):
                msgs.append(text)

        class Off:
            async def send(self_, text, **kw):
                officer.append(text)

        async def upd(r):
            pass

        async def by_id(cid):
            return Off()
        self.m.update_raid_message, self.m.channel_by_id = upd, by_id
        self.m.book.profile = lambda uid: {"name": "Bankdrücker"}
        signed = []
        self.m.book.signup = lambda raid, uid, st, prof, t: signed.append((uid, st))
        asyncio.run(self.m.accept_substitute(types.SimpleNamespace(user=types.SimpleNamespace(id=42), response=R()), raid))
        return msgs, officer, signed

    def test_zusage(self):
        msgs, officer, signed = self.zusage(self.raid())
        self.assertEqual(signed, [(42, "an")])
        self.assertIn("du bist für **MC** angemeldet", msgs[0])
        self.assertIn("springt bei **MC**", officer[0])
        msgs, officer, signed = self.zusage(self.raid(signups={"1": {"status": "an"}, "2": {"status": "an"}}))
        self.assertEqual(signed, [])
        self.assertIn("schon wieder besetzt", msgs[0])



class Skillung(unittest.TestCase):
    """sync_specs: nur Raids des Mitglieds aktualisieren, PN nur bei geänderter Rolle (nicht beim ersten Einlesen)."""
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["skillung_bot"]

    def test_raids_und_pn_nur_bei_rollenwechsel(self):
        m = self.m
        spec = {"label": "Heilig", "points": "31/20/0"}
        changes = [{"user_id": 5, "name": "Anduin", "spec": spec, "role": "heal", "old_role": "ranged"},
                   {"user_id": 6, "name": "Neu", "spec": spec, "role": "heal", "old_role": None}]
        saved = (m.book.apply_specs, m.book.open_raids, m.update_raid_message, m.bot.get_user, dict(m.cfg),
                 m.rmd.spec_short)
        updated, dms = [], []

        async def upd(r):
            updated.append(r["id"])

        class U:
            def __init__(self, uid):
                self.uid = uid

            async def send(self, text):
                dms.append((self.uid, text))
        m.book.apply_specs = lambda specs: changes
        m.book.open_raids = lambda: [{"id": 1, "signups": {"5": {}}}, {"id": 2, "signups": {"9": {}}}]
        m.update_raid_message = upd
        m.bot.get_user = lambda uid: U(uid)
        m.rmd.spec_short = lambda s: "H"
        m.cfg["notify_spec_changes"] = True
        try:
            asyncio.run(m.sync_specs())
        finally:
            (m.book.apply_specs, m.book.open_raids, m.update_raid_message, m.bot.get_user) = saved[:4]
            m.cfg.clear()
            m.cfg.update(saved[4])
            m.rmd.spec_short = saved[5]
        self.assertEqual(updated, [1])
        self.assertEqual([u for u, _ in dms], [5])                     # nur der Rollenwechsel bekommt eine PN
        self.assertIn("Heiler", dms[0][1])


if __name__ == "__main__":
    unittest.main()
