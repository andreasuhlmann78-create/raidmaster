"""T-D-N1: zwei Wünsche von Gildenleitungen/Mitgliedern (ab Bot 1.5.183) – ohne Netz.

/raid fehlend (Gildenleitung): wer aus der Gilde (Rolle Mitglied/Raider/Raidleitung/Offizier, keine Bots) hat zu
einem Raid noch gar nicht reagiert – jede Rückmeldung (auch "abgemeldet") zählt als Rückmeldung, Gäste zählen nicht;
nur für die Gildenleitung sichtbar, ohne Mitgliederliste (Intent aus) ein klarer Hinweis, lange Listen gekürzt
unter 2000 Zeichen.
/anwesenheit (alle): Teilnahme an den letzten Raids, dieselbe Zählung wie für die Aufstellung.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

N = types.SimpleNamespace


def mitglied(uid, name, *roles, bot=False):
    return N(id=uid, display_name=name, bot=bot, roles=[N(name=r) for r in roles])


class Antwort:
    def __init__(self):
        self.messages, self.kw = [], []

    async def send_message(self, text, **kw):
        self.messages.append(text)
        self.kw.append(kw)


class Fehlend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["raid_bot"]

    def setUp(self):
        m = self.m
        self.saved = (m.is_creator, m.book.get, m.bot_guild, m.bot._connection._intents)
        m.is_creator = lambda u: True
        self.raid = {"id": 4, "title": "MC", "start": 1794470000, "signups": {"1": {"status": "an"}, "2": {"status": "ab"}}}
        m.book.get = lambda rid: self.raid if rid == "4" else None
        self.members = [mitglied(1, "Ana", "Raider"), mitglied(2, "Bert", "Mitglied"),
                        mitglied(3, "dora", "Mitglied"), mitglied(4, "Carl", "Offizier"), mitglied(5, "Gast1", "Gast"),
                        mitglied(6, "Botti", "Mitglied", bot=True), mitglied(7, "Ohne")]
        m.bot._connection._intents = m.discord.Intents.default()
        m.bot._connection._intents.members = True

    def tearDown(self):
        m = self.m
        m.is_creator, m.book.get, m.bot_guild, m.bot._connection._intents = self.saved

    def frage(self, raid="4"):
        i = N(user=1, guild=N(members=self.members), response=Antwort())
        asyncio.run(self.m.raid_missing.callback(i, raid))
        self.assertTrue(all(k.get("ephemeral") for k in i.response.kw))
        return i.response.messages[0]

    def test_am_bot_angemeldet(self):
        g = self.bot.bot.tree.get_command("raid")
        self.assertIs(g.get_command("fehlend"), self.m.raid_missing)

    def test_nur_ohne_rueckmeldung(self):
        self.assertEqual(self.m.missing_members(self.members, self.raid["signups"]), ["Carl", "dora"])
        text = self.frage()
        self.assertIn("noch keine Rückmeldung von 2 Mitgliedern", text)
        self.assertIn("• Carl\n• dora", text)
        for n in ("Ana", "Bert", "Gast1", "Botti", "Ohne"):
            self.assertNotIn(n, text)

    def test_alle_gemeldet_und_unbekannt(self):
        self.raid["signups"].update({"3": {"status": "vielleicht"}, "4": {"status": "ersatz"}})
        self.assertIn("alle Gildenmitglieder gemeldet", self.frage())
        self.assertEqual(self.frage("99"), "Raid nicht gefunden.")

    def test_nur_gildenleitung(self):
        self.m.is_creator = lambda u: False
        self.assertIn("nur der Gildenchef", self.frage())

    def test_ohne_mitgliederliste(self):
        self.m.bot._connection._intents.members = False
        self.assertIn("Server Members Intent", self.frage())

    def test_lange_liste_gekuerzt(self):
        self.members = [mitglied(100 + i, f"Spieler{i:03d}" + "x" * 20, "Mitglied") for i in range(150)]
        text = self.frage()
        self.assertLessEqual(len(text), 2000)
        self.assertIn("von 150 Mitgliedern", text)
        shown = text.count("• ")
        self.assertIn(f"… und {150 - shown} weitere.", text)


class Anwesenheit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["dkp_befehle_bot"]

    def setUp(self):
        m = self.m
        self.saved = (m.reload_dkp_if_needed, m.rmd.attendance, m.book.profile)
        m.reload_dkp_if_needed = lambda: False
        self.att = ({"thrall": 0.8}, 10, "Addon")
        m.rmd.attendance = lambda data, book: self.att
        m.book.profile = lambda uid: {"name": "Thrall"}

    def tearDown(self):
        self.m.reload_dkp_if_needed, self.m.rmd.attendance, self.m.book.profile = self.saved

    def frage(self, name=None):
        i = N(user=N(id=5), response=Antwort())
        asyncio.run(self.m.attendance_cmd.callback(i, name))
        self.assertTrue(i.response.kw[0].get("ephemeral"))
        return i.response.messages[0]

    def test_am_bot_angemeldet(self):
        self.assertIs(self.bot.bot.tree.get_command("anwesenheit").callback, self.m.attendance_cmd.callback)

    def test_eigener_und_fremder(self):
        self.assertIn("**Thrall** war bei **8 von 10** der letzten Raidtagen dabei (80 %)", self.frage())
        self.assertIn("RaidMaster-Addon", self.frage())
        self.assertIn("**Jaina** war bei **0 von 10**", self.frage("jaina"))

    def test_discord_quelle_und_ohne_daten(self):
        self.att = ({"thrall": 1 / 3}, 3, "Discord")
        self.assertIn("**1 von 3** der letzten Raids dabei (33 %). Quelle: Discord-Anmeldungen", self.frage())
        self.att = ({}, 0, "Discord")
        self.assertIn("Noch keine vergangenen Raids", self.frage())
        self.m.book.profile = lambda uid: None
        self.assertIn("/charakter", self.frage())


if __name__ == "__main__":
    unittest.main()
