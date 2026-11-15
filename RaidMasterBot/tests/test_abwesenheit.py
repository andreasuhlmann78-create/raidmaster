"""T-D-N1-ABW: Abwesenheit melden (D-N1 Wunsch 1, ab Bot 1.5.184) – ohne Netz.

abwesenheit.py: Datum lesen (ohne Jahr, über den Jahreswechsel, ungültig), Prüfungen beim Anlegen (Ende vor
Beginn, vergangen, zu lang, zu weit voraus, doppelt, zu viele), Grund bereinigt (eine Zeile, ohne @, kurz),
Ablauf (Ende vor heute), Entfernen nach Nummer, Abfrage je Tag (Grenzen inklusive), Anzeige des Zeitraums.
abwesend_bot.py: /abwesend melden speichert und aktualisiert nur Raids im Zeitraum; falsches Datum -> deutsche
Meldung; /abwesend liste zeigt Mitgliedern nur die eigenen, der Gildenleitung alle mit Grund; /abwesend entfernen.
Anzeige: Raid-Anmeldung nur mit Namen (nie der Grund), Angemeldete nicht, PUG- und Testraids nichts; Aufstellung
mit derselben Zeile; /raid fehlend markiert Abwesende.
"""
import asyncio
import os
import sys
import types
import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import abwesenheit as ab  # noqa: E402

N = types.SimpleNamespace
TZ = "Europe/Zurich"
HEUTE = date(2026, 11, 16)
JETZT = datetime(2026, 11, 16, 0, 30, tzinfo=ZoneInfo(TZ))


def ts(y, m, d, h=20):
    return int(datetime(y, m, d, h, tzinfo=ZoneInfo(TZ)).timestamp())


class Rein(unittest.TestCase):
    def test_datum_lesen(self):
        self.assertEqual(ab.parse_range("20.11.", "27.11.", TZ, JETZT), (date(2026, 11, 20), date(2026, 11, 27)))
        self.assertEqual(ab.parse_range("28.12.", "03.01.", TZ, JETZT), (date(2026, 12, 28), date(2027, 1, 3)))
        self.assertEqual(ab.parse_range("20.12.2027", "05.01.", TZ, JETZT), (date(2027, 12, 20), date(2028, 1, 5)))
        self.assertEqual(ab.parse_range("16.11.", "16.11.", TZ, JETZT), (HEUTE, HEUTE))        # heute bleibt heute
        self.assertEqual(ab.parse_range("10.11.", "12.11.", TZ, JETZT)[0], date(2027, 11, 10))   # schon vorbei
        self.assertEqual(ab.parse_range("1.12.2026", "2.12.26", TZ, JETZT), (date(2026, 12, 1), date(2026, 12, 2)))
        for von, bis in (("32.13.", "1.1."), ("x", "1.1."), ("1.12.", "")):
            with self.assertRaises(ValueError):
                ab.parse_range(von, bis, TZ, JETZT)

    def test_anlegen_pruefungen(self):
        d = {}
        e = ab.add(d, 7, date(2026, 11, 20), date(2026, 11, 27), " Urlaub\n@everyone  am Meer ", HEUTE)
        self.assertEqual(e, {"von": "2026-11-20", "bis": "2026-11-27", "grund": "Urlaub everyone am Meer"})
        self.assertEqual(list(d), ["7"])
        fehler = [(date(2026, 11, 27), date(2026, 11, 20), "vor dem Beginn"),
                  (date(2026, 11, 1), date(2026, 11, 15), "Vergangenheit"),
                  (date(2026, 11, 20), date(2027, 3, 20), "120 Tage"),
                  (date(2027, 12, 1), date(2027, 12, 2), "Jahr in der Zukunft"),
                  (date(2026, 11, 20), date(2026, 11, 27), "schon eingetragen")]
        for a, b, text in fehler:
            with self.assertRaises(ValueError) as cm:
                ab.add(d, 7, a, b, None, HEUTE)
            self.assertIn(text, str(cm.exception))
        ab.add(d, 7, date(2026, 11, 20), date(2027, 3, 19), None, HEUTE)          # genau 120 Tage geht
        for i in range(3):
            ab.add(d, 7, date(2026, 12, 1 + i), date(2026, 12, 1 + i), None, HEUTE)
        with self.assertRaises(ValueError) as cm:
            ab.add(d, 7, date(2026, 12, 9), date(2026, 12, 9), None, HEUTE)
        self.assertIn("Höchstens 5", str(cm.exception))
        self.assertEqual(len(ab.clean_reason("x" * 200)), ab.GRUND_MAX)

    def test_ablauf_entfernen_abfrage(self):
        d = {"1": [{"von": "2026-11-01", "bis": "2026-11-15", "grund": ""},
                   {"von": "2026-11-10", "bis": "2026-11-16", "grund": ""}],
             "2": [{"von": "2026-11-01", "bis": "2026-11-02", "grund": ""}]}
        self.assertEqual(ab.prune(d, HEUTE), 2)
        self.assertEqual(d, {"1": [{"von": "2026-11-10", "bis": "2026-11-16", "grund": ""}]})   # endet heute: bleibt
        self.assertEqual(ab.absent_on(d, HEUTE), {"1"})
        self.assertEqual(ab.absent_on(d, date(2026, 11, 10)), {"1"})
        self.assertEqual(ab.absent_on(d, date(2026, 11, 17)), set())
        self.assertIsNone(ab.remove(d, 1, 2))
        self.assertIsNone(ab.remove(d, 1, 0))
        self.assertEqual(ab.remove(d, 1, 1)["bis"], "2026-11-16")
        self.assertEqual(d, {})

    def test_zeitraum_text(self):
        self.assertEqual(ab.span_text({"von": "2026-11-20", "bis": "2026-11-27"}), "20.11.–27.11.2026")
        self.assertEqual(ab.span_text({"von": "2026-12-28", "bis": "2027-01-03"}), "28.12.2026–03.01.2027")
        self.assertEqual(ab.span_text({"von": "2026-11-20", "bis": "2026-11-20"}), "20.11.2026")


class Antwort:
    def __init__(self):
        self.messages = []

    async def send_message(self, text, **kw):
        assert kw.get("ephemeral"), "Antwort muss privat sein"
        self.messages.append(text)


class Befehle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["abwesend_bot"]

    def setUp(self):
        m = self.m
        self.saved = (m.today, m.state.save, m.book.open_raids, m.update_raid_message, m.is_creator, m.book.profile,
                      m.abwesenheit.parse_range)
        self.saved_abs = m.state.data.pop("absences", None)
        self.saves, self.updated = [], []
        m.today = lambda: HEUTE
        m.state.save = lambda: self.saves.append(1)
        m.book.open_raids = lambda: [{"id": 1, "start": ts(2026, 11, 18)}, {"id": 2, "start": ts(2026, 11, 25)}]

        async def upd(r):
            self.updated.append(r["id"])
        m.update_raid_message = upd
        m.is_creator = lambda u: False
        m.book.profile = lambda uid: {"name": {"5": "Thrall", "6": "Jaina"}.get(str(uid), "")} if str(uid) in "56" else None
        orig = self.saved[6]
        m.abwesenheit.parse_range = lambda a, b, tz: orig(a, b, tz, JETZT)

    def tearDown(self):
        m = self.m
        (m.today, m.state.save, m.book.open_raids, m.update_raid_message, m.is_creator, m.book.profile,
         m.abwesenheit.parse_range) = self.saved
        m.state.data.pop("absences", None)
        if self.saved_abs is not None:
            m.state.data["absences"] = self.saved_abs

    def inter(self, uid=5):
        return N(user=N(id=uid), guild=N(get_member=lambda i: N(display_name=f"Discord{i}")), response=Antwort())

    def melden(self, von, bis, grund=None, uid=5):
        i = self.inter(uid)
        asyncio.run(self.m.absent_add.callback(i, von, bis, grund))
        return i.response.messages[0]

    def liste(self, uid=5):
        i = self.inter(uid)
        asyncio.run(self.m.absent_list.callback(i))
        return i.response.messages[0]

    def test_angemeldet(self):
        g = self.bot.bot.tree.get_command("abwesend")
        self.assertIs(g, self.m.abwesend_group)
        self.assertEqual(sorted(c.name for c in g.commands), ["entfernen", "liste", "melden"])

    def test_melden_speichert_und_aktualisiert_nur_im_zeitraum(self):
        text = self.melden("20.11.", "27.11.", "Urlaub")
        self.assertIn("Eingetragen: **20.11.–27.11.2026** (Urlaub)", text)
        self.assertEqual(self.m.state.data["absences"]["5"][0]["bis"], "2026-11-27")
        self.assertEqual(self.saves, [1])
        self.assertEqual(self.updated, [2])                                  # 18.11. liegt ausserhalb

    def test_falsches_datum_und_ende_vor_beginn(self):
        self.assertIn("TT.MM.", self.melden("32.13.", "1.1."))
        self.assertIn("vor dem Beginn", self.melden("27.11.2026", "20.11.2026"))
        self.assertEqual(self.saves, [])
        self.assertNotIn("5", self.m.state.data.get("absences", {}))

    def test_liste_eigene_und_gildenleitung(self):
        self.melden("20.11.", "27.11.", "Urlaub", uid=5)
        self.melden("01.12.", "02.12.", "Arbeit", uid=6)
        self.melden("03.12.", "03.12.", None, uid=9)
        mine = self.liste(5)
        self.assertIn("1. 20.11.–27.11.2026 – Urlaub", mine)
        self.assertNotIn("Arbeit", mine)                                     # Mitglied sieht nur die eigenen
        self.m.is_creator = lambda u: True
        alle = self.liste(5)
        self.assertIn("• Jaina: 01.12.–02.12.2026 – Arbeit", alle)
        self.assertIn("• Discord9: 03.12.2026", alle)                        # ohne Charakter: Discord-Name
        self.assertLess(alle.index("Jaina"), alle.index("Discord9"))         # nach Datum

    def test_entfernen(self):
        self.melden("20.11.", "27.11.")
        self.updated.clear()
        i = self.inter()
        asyncio.run(self.m.absent_remove.callback(i, 2))
        self.assertIn("gibt es nicht", i.response.messages[0])
        i = self.inter()
        asyncio.run(self.m.absent_remove.callback(i, 1))
        self.assertIn("gelöscht", i.response.messages[0])
        self.assertNotIn("5", self.m.state.data["absences"])
        self.assertEqual(self.updated, [2])


class Anzeige(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.ra = sys.modules["raidanzeige_bot"]
        cls.rb = sys.modules["raid_bot"]

    def setUp(self):
        self.saved = (self.ra.book.profile, self.ra.state.data.get("absences"))
        self.ra.state.data["absences"] = {
            "5": [{"von": "2026-11-20", "bis": "2026-11-27", "grund": "Geheim"}],
            "6": [{"von": "2026-11-25", "bis": "2026-11-25", "grund": ""}],
            "7": [{"von": "2026-11-24", "bis": "2026-11-26", "grund": ""}],
            "8": [{"von": "2026-11-01", "bis": "2026-11-24", "grund": ""}]}
        self.ra.book.profile = lambda uid: {"5": {"name": "Thrall"}, "6": {"name": "aJaina"}}.get(str(uid))
        self.raid = {"id": 3, "title": "MC", "start": ts(2026, 11, 25), "signups": {}}

    def tearDown(self):
        self.ra.book.profile = self.saved[0]
        if self.saved[1] is None:
            self.ra.state.data.pop("absences", None)
        else:
            self.ra.state.data["absences"] = self.saved[1]

    def test_zeile_nur_namen(self):
        line = self.ra.absence_line(self.raid)
        self.assertEqual(line, "🏖️ Abwesend gemeldet: aJaina, Thrall und 1 weiteres Mitglied")
        self.assertNotIn("Geheim", self.ra.raid_embed(self.raid).description)
        self.assertIn(line, self.ra.raid_embed(self.raid).description)
        self.raid["signups"] = {"5": {"status": "an"}, "6": {"status": "ab"}}
        self.assertEqual(self.ra.absence_line(self.raid), "🏖️ Abwesend gemeldet: aJaina und 1 weiteres Mitglied")

    def test_pug_test_und_leer(self):
        for extra in ({"mode": "pug"}, {"test": True}):
            self.assertEqual(self.ra.absence_line(dict(self.raid, **extra)), "")
        self.assertEqual(self.ra.absence_line(dict(self.raid, start=ts(2026, 12, 20))), "")
        self.assertNotIn("Abwesend", self.ra.raid_embed(dict(self.raid, mode="pug")).description)

    def test_viele_namen_gekuerzt(self):
        self.ra.state.data["absences"] = {str(100 + i): [{"von": "2026-11-25", "bis": "2026-11-25", "grund": ""}]
                                          for i in range(80)}
        self.ra.book.profile = lambda uid: {"name": f"Spieler{uid}"}
        line = self.ra.absence_line(self.raid)
        self.assertLessEqual(len(line), 620)
        shown = line.count("Spieler")
        self.assertTrue(line.endswith(f"und {80 - shown} weitere Mitglieder"))

    def test_aufstellung_und_fehlend(self):
        sent = []

        class Ch:
            async def send(self_, t):
                sent.append(t)
        rb = self.rb
        saved = (rb.assignment_channel, rb.channel_by_id, rb.rmd.attendance)

        async def ch(pool):
            return Ch()

        async def none(cid):
            return None
        rb.assignment_channel, rb.channel_by_id = ch, none
        rb.rmd.attendance = lambda data, book: ({}, 0, "Discord")
        try:
            self.assertEqual(asyncio.run(rb.post_lineup(self.raid)), 1)
        finally:
            rb.assignment_channel, rb.channel_by_id, rb.rmd.attendance = saved
        self.assertIn("🏖️ Abwesend gemeldet: aJaina, Thrall", sent[-1])
        mitglieder = [N(id=5, display_name="T", bot=False, roles=[N(name="Raider")]),
                      N(id=9, display_name="U", bot=False, roles=[N(name="Mitglied")])]
        self.assertEqual(rb.missing_members(mitglieder, {}, {"5"}), ["T (abwesend gemeldet)", "U"])


if __name__ == "__main__":
    unittest.main()
