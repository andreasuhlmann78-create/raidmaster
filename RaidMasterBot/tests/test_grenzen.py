"""T-D-N1-GRENZEN: Plätze je Rolle (D-N1 Wunsch 4, ab Bot 1.5.185) – ohne Netz.

RaidBook.signup mit echter Datei im Temp-Ordner: über der Grenze einer Rolle -> Ersatzbank; wer mit derselben
Rolle schon angemeldet ist, bleibt es (auch nach Senken der Grenze); Rollenwechsel in eine volle Rolle -> Ersatzbank;
ohne Grenze unverändert; die Höchstzahl des Raids gilt weiter. Anzeige "Plätze je Rolle", Meldung "Für Heiler sind
alle Plätze belegt" nur wenn der Raid sonst Platz hat. /raid grenzen: nur Gildenleitung, setzen/entfernen/anzeigen,
Hinweis bei schon zu vielen Angemeldeten (niemand wird verschoben).
"""
import asyncio
import os
import shutil
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import raidmaster_data as rmd  # noqa: E402
from bot_hilfen import status_text  # noqa: E402

N = types.SimpleNamespace


def prof(name, role):
    return {"name": name, "cls": "PRIEST" if role == "heal" else "WARRIOR", "role": role}


class Buch(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.book = rmd.RaidBook(self.dir)
        self.raid = self.book.create("MC", datetime.now() + timedelta(days=2), "", 0, 1, 1)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def an(self, uid, role, status="an"):
        return self.book.signup(self.raid, uid, status, prof(f"P{uid}", role), 1)

    def test_grenze_je_rolle(self):
        self.raid["limits"] = {"heal": 2}
        self.assertEqual([self.an(1, "heal"), self.an(2, "heal"), self.an(3, "heal")], ["an", "an", "ersatz"])
        self.assertEqual(self.an(4, "melee"), "an")                                 # andere Rolle ohne Grenze
        self.assertEqual(self.an(1, "heal"), "an")                                  # schon drin: bleibt
        self.raid["limits"] = {"heal": 1}
        self.assertEqual(self.an(2, "heal"), "an")                                  # Grenze gesenkt: bleibt
        self.assertEqual(self.an(4, "heal"), "ersatz")                              # Wechsel in volle Rolle
        self.an(1, "heal", "ab")
        self.assertEqual(self.an(3, "heal"), "ersatz")                              # P2 noch drin: 1 von 1
        self.an(2, "heal", "ab")
        self.assertEqual(self.an(3, "heal"), "an")                                  # Platz frei
        self.assertEqual(self.an(5, "tank", "vielleicht"), "vielleicht")           # andere Status unberührt
        saved = rmd.RaidBook(self.dir).get(self.raid["id"])                         # gespeichert
        self.assertEqual(saved["signups"]["3"]["status"], "an")

    def test_hoechstzahl_gilt_weiter(self):
        self.raid["max"], self.raid["limits"] = 2, {"melee": 5}
        self.assertEqual([self.an(1, "melee"), self.an(2, "melee"), self.an(3, "melee")], ["an", "an", "ersatz"])

    def test_role_full_und_anzeige(self):
        self.assertFalse(rmd.role_full(self.raid, "heal"))
        self.assertEqual(rmd.limits_text(self.raid), "")
        self.raid["limits"] = {"tank": 2, "heal": 1}
        self.an(1, "heal")
        self.an(2, "tank")
        self.assertTrue(rmd.role_full(self.raid, "heal"))
        self.assertFalse(rmd.role_full(self.raid, "heal", "1"))                     # sich selbst nicht zählen
        self.assertEqual(rmd.limits_text(self.raid), "🎯 Plätze je Rolle: Tank 1/2 · Heiler 1/1 ✅")

    def test_meldung(self):
        self.raid["limits"] = {"heal": 1}
        self.an(1, "heal")
        self.assertIn("Für **Heiler** sind alle Plätze belegt", status_text("ersatz", "an", self.raid, "heal"))
        self.raid["max"] = 1
        self.assertIn("Der Raid ist voll", status_text("ersatz", "an", self.raid, "heal"))
        self.assertIn("Der Raid ist voll", status_text("ersatz", "an"))             # alte Aufrufe unverändert
        self.assertIn("angemeldet", status_text("an", "an", self.raid, "heal"))


class Antwort:
    def __init__(self):
        self.messages = []

    async def send_message(self, text, **kw):
        assert kw.get("ephemeral")
        self.messages.append(text)


class Befehl(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["raid_bot"]

    def setUp(self):
        m = self.m
        self.saved = (m.is_creator, m.book.get, m.book.save, m.update_raid_message)
        self.raid = {"id": 4, "title": "MC", "start": 1794470000,
                     "signups": {str(i): {"status": "an", "role": "heal", "cls": "PRIEST", "name": f"P{i}", "t": i} for i in range(3)}}
        self.updated = []
        m.is_creator = lambda u: True
        m.book.get = lambda rid: self.raid if rid == "4" else None
        m.book.save = lambda: None

        async def upd(r):
            self.updated.append(r["id"])
        m.update_raid_message = upd

    def tearDown(self):
        self.m.is_creator, self.m.book.get, self.m.book.save, self.m.update_raid_message = self.saved

    def frage(self, raid="4", **kw):
        args = {k: kw.get(k) for k in ("tanks", "heiler", "nahkampf", "fernkampf")}
        i = N(user=1, response=Antwort())
        asyncio.run(self.m.raid_limits.callback(i, raid, **args))
        return i.response.messages[0]

    def test_angemeldet(self):
        self.assertIs(self.bot.bot.tree.get_command("raid").get_command("grenzen"), self.m.raid_limits)

    def test_setzen_anzeigen_entfernen(self):
        self.assertIn("Keine Grenzen", self.frage())
        self.assertEqual(self.updated, [])                                          # nur anzeigen
        text = self.frage(heiler=2, tanks=4)
        self.assertEqual(self.raid["limits"], {"heal": 2, "tank": 4})
        self.assertIn("Tank 0/4 · Heiler 3/2 ✅", text)
        self.assertIn("Schon mehr angemeldet als erlaubt: Heiler", text)
        self.assertEqual(self.raid["signups"]["2"]["status"], "an")                # niemand verschoben
        self.frage(tanks=0)
        self.assertEqual(self.raid["limits"], {"heal": 2})
        self.frage(heiler=0)
        self.assertNotIn("limits", self.raid)
        self.assertEqual(self.updated, [4, 4, 4])

    def test_rechte_und_unbekannt(self):
        self.assertEqual(self.frage("9", heiler=1), "Raid nicht gefunden.")
        self.m.is_creator = lambda u: False
        self.assertIn("nur der Gildenchef", self.frage(heiler=1))
        self.assertNotIn("limits", self.raid)

    def test_karte_zeigt_plaetze(self):
        self.raid["limits"] = {"heal": 2}
        e = sys.modules["raidanzeige_bot"].raid_embed(self.raid)
        self.assertIn("🎯 Plätze je Rolle: Heiler 3/2 ✅", e.description)


if __name__ == "__main__":
    unittest.main()
