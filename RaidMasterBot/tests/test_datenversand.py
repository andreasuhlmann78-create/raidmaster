"""T-DATENVERSAND: daten_config.json an die Offiziere (Auftrag 21.11.2026 07:42, ab Bot 1.5.187) – ohne Netz.

Nur der Gildenchef; Datei fehlt / zu gross / kein JSON / ohne repo+token -> nichts senden, Hinweis wohin; BOM wird gelesen.
Empfänger: nur Rolle Offizier, keine Bots, nicht der Absender, schon Belieferte nur mit "erneut". Erst die Liste, gesendet wird
nur auf "Senden" des Gildenchefs (fremder Klick zählt nicht, Abbrechen sendet nichts). Direktnachricht mit Anhang
daten_config.json und Anleitung; geschlossene Direktnachrichten werden genannt, nicht gemerkt. Der Inhalt (Zugangsschlüssel)
steht in KEINER Antwort, keinem Protokoll und keiner #bot-log-Meldung.
"""
import asyncio
import json
import os
import shutil
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

N = types.SimpleNamespace
GEHEIM = "ghp_TESTNURFUERTESTS0000000000000000"


class Mitglied:
    def __init__(self, uid, name, roles=("Offizier",), bot=False, closed=False):
        self.id, self.display_name, self.bot, self.closed = uid, name, bot, closed
        self.roles = [N(name=r) for r in roles]
        self.got = []

    async def send(self, text, file=None):
        if self.closed:
            import discord
            raise discord.Forbidden(N(status=403, reason="x"), "DMs zu")
        self.got.append((text, file.filename, file.fp.read()))


class Antwort:
    def __init__(self):
        self.messages, self.views, self.edits = [], [], []

    async def send_message(self, text, view=None, **kw):
        assert kw.get("ephemeral")
        self.messages.append(text)
        self.views.append(view)

    async def edit_message(self, content=None, view=None):
        self.edits.append(content)

    async def send(self, text, **kw):
        self.messages.append(text)


class Versand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["datenversand_bot"]

    def setUp(self):
        m = self.m
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "daten_config.json")
        self.write({"repo": "owner/daten", "token": GEHEIM})
        self.saved = (m.is_chef, m.post_bot_log, m.state.save, dict(m.cfg), m.state.data.get("daten_config_sent"),
                      m.bot._connection._intents)
        m.cfg["daten_config_path"] = self.path
        m.is_chef = lambda u: True
        m.state.save = lambda: None
        m.state.data.pop("daten_config_sent", None)
        m.bot._connection._intents = m.discord.Intents.default()
        m.bot._connection._intents.members = True
        self.blog = []

        async def blog(t):
            self.blog.append(t)
        m.post_bot_log = blog
        self.chef = Mitglied(1, "Chef")
        self.members = [self.chef, Mitglied(2, "Zora"), Mitglied(3, "anna"), Mitglied(4, "Raider", ("Raider",)),
                        Mitglied(5, "Botto", bot=True), Mitglied(6, "Zu", closed=True)]

    def tearDown(self):
        m = self.m
        m.is_chef, m.post_bot_log, m.state.save = self.saved[:3]
        m.cfg.clear()
        m.cfg.update(self.saved[3])
        m.state.data.pop("daten_config_sent", None)
        if self.saved[4] is not None:
            m.state.data["daten_config_sent"] = self.saved[4]
        m.bot._connection._intents = self.saved[5]
        shutil.rmtree(self.dir)

    def write(self, data, raw=None):
        with open(self.path, "wb") as f:
            f.write(raw if raw is not None else json.dumps(data).encode())

    def befehl(self, erneut=False, user=None, datei=None):
        i = N(user=user or self.chef, guild=N(members=self.members), response=Antwort())
        asyncio.run(self.m.send_daten_config.callback(i, datei, erneut))
        return i.response

    def klick(self, view, which="confirm", user=None):
        r = Antwort()
        i = N(user=user or self.chef, response=r, followup=r)
        if not asyncio.run(view.interaction_check(i)):
            return None
        asyncio.run(getattr(view, which).callback(i))
        return r

    def assertGeheim(self, *texts):
        for t in texts:
            self.assertNotIn(GEHEIM, str(t))

    def test_angemeldet(self):
        cmd = self.bot.bot.tree.get_command("uploader-daten-senden")
        self.assertIs(cmd.callback, self.m.send_daten_config.callback)

    def test_nur_gildenchef(self):
        self.m.is_chef = lambda u: False
        r = self.befehl()
        self.assertIn("nur der Gildenchef", r.messages[0])
        self.assertIsNone(r.views[0])

    def test_datei_pruefungen(self):
        os.remove(self.path)
        self.assertIn("noch keine daten_config.json", self.befehl().messages[0])
        self.write(None, raw=b"{kaputt")
        self.assertIn("kein gültiges JSON", self.befehl().messages[0])
        self.write({"repo": "owner/daten"})
        self.assertIn("fehlen \"repo\" oder \"token\"", self.befehl().messages[0])
        self.write(None, raw=b"x" * (self.m.MAX_BYTES + 1))
        self.assertIn("zu gross", self.befehl().messages[0])
        self.write(None, raw=b"\xef\xbb\xbf" + json.dumps({"repo": "o/d", "token": GEHEIM}).encode())   # mit BOM
        self.assertIsNotNone(self.befehl().views[0])

    def test_liste_dann_senden(self):
        r = self.befehl()
        text, view = r.messages[0], r.views[0]
        self.assertIn("an diese 3 Offiziere", text)
        self.assertIn("• anna\n• Zora\n• Zu", text)
        for n in ("Chef", "Raider", "Botto"):
            self.assertNotIn(n, text)
        self.assertEqual([m.got for m in self.members], [[]] * 6)            # vor dem Klick nichts gesendet
        self.assertIsNone(self.klick(view, user=self.members[1]))            # fremder Klick zählt nicht
        r2 = self.klick(view)
        got = self.members[2].got[0]
        self.assertIn("nicht weitergeben", got[0])
        self.assertEqual(got[1], "daten_config.json")
        self.assertEqual(json.loads(got[2])["token"], GEHEIM)                # Inhalt nur im Anhang
        self.assertEqual(len(self.members[1].got), 1)
        self.assertIn("an 2 von 3 Offizieren gesendet", r2.messages[0])
        self.assertIn("Nicht zustellbar (Direktnachrichten geschlossen): Zu", r2.messages[0])
        self.assertEqual(self.blog, ["📦 daten_config.json an 2 Offiziere gesendet, 1 nicht zustellbar."])
        self.assertEqual(sorted(self.m.state.data["daten_config_sent"]), ["2", "3"])
        self.klick(view)                                                     # Doppelklick: nicht nochmals
        self.assertEqual(len(self.members[1].got), 1)
        self.assertGeheim(text, *r2.messages, *r2.edits, *self.blog)

    def test_einmalig_und_erneut(self):
        self.m.state.data["daten_config_sent"] = ["2", "3"]
        self.assertIn("an diese 1 Offiziere", self.befehl().messages[0])     # nur Zu fehlt noch
        self.members[5].closed = False
        self.m.state.data["daten_config_sent"] = ["2", "3", "6"]
        self.assertIn("Keine Empfänger", self.befehl().messages[0])
        self.assertIn("an diese 3 Offiziere", self.befehl(erneut=True).messages[0])

    def test_abbrechen_und_datei_weg_beim_klick(self):
        view = self.befehl().views[0]
        r = self.klick(view, "cancel")
        self.assertIn("nichts gesendet", r.edits[0])
        self.assertEqual(sum(len(m.got) for m in self.members), 0)
        view = self.befehl().views[0]
        os.remove(self.path)
        r = self.klick(view)
        self.assertIn("Nicht gesendet: Ich habe noch keine daten_config.json", r.edits[0])
        self.assertEqual(sum(len(m.got) for m in self.members), 0)

    def test_datei_im_befehl(self):
        """ab 1.5.188: Bot läuft auf einem Server – der Gildenchef hängt die Datei im Befehl an."""
        os.remove(self.path)

        class Anhang:
            def __init__(self, raw):
                self.raw, self.size = raw, len(raw)

            async def read(self):
                return self.raw
        for raw, text in ((b"{kaputt", "kein gültiges JSON"), (json.dumps({"repo": "o/d"}).encode(), "fehlen"),
                          (b"x" * (self.m.MAX_BYTES + 1), "zu gross")):
            self.assertIn(text, self.befehl(datei=Anhang(raw)).messages[0])
            self.assertFalse(os.path.exists(self.path))                  # Ungültiges wird nie abgelegt
        gut = json.dumps({"repo": "o/d", "token": GEHEIM}).encode()
        r = self.befehl(datei=Anhang(gut))
        self.assertIn("an diese 3 Offiziere", r.messages[0])
        with open(self.path, "rb") as f:
            self.assertEqual(f.read(), gut)                               # abgelegt für spätere Aufrufe
        self.klick(r.views[0])
        self.assertEqual(json.loads(self.members[1].got[0][2])["token"], GEHEIM)
        self.assertGeheim(*r.messages, *self.blog)
        self.m.is_chef = lambda u: False
        os.remove(self.path)
        self.assertIn("nur der Gildenchef", self.befehl(datei=Anhang(gut)).messages[0])
        self.assertFalse(os.path.exists(self.path))                      # Fremde legen nichts ab

    def test_ohne_mitgliederliste(self):
        self.m.bot._connection._intents.members = False
        self.assertIn("Mitgliederliste", self.befehl().messages[0])


if __name__ == "__main__":
    unittest.main()
