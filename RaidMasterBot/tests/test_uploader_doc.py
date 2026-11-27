"""T-D-UPDOC2 / T-D-UPCFG1 (ab Bot 1.5.197): /uploader-Nachricht und ANLEITUNG.md

- D-UPDOC2 (Entscheid des Nutzers 25.11. 11:39): Schritt "Addons-automatisch-an.bat doppelklicken, Uploader neu starten" in
  Deutsch und Englisch – in der Einrichtungs-Nachricht, bei nur_programm und an_offiziere, und in ANLEITUNG.md.
- D-UPCFG1: Kanal-Kennungen (nur die Zahl der Webhook-Adresse, nie der Schlüssel) wie im Uploader-Fenster (UP-CFG1).
- Lange Nachricht: in Teilen <= 1900 Zeichen, nichts verloren, Dateien am ersten Teil.
"""
import asyncio
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

SCHLUESSEL = "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789_-geheim"
CONF = {"webhook_url": f"https://discord.com/api/webhooks/111111111111111111/{SCHLUESSEL}",
        "test_webhook_url": f"https://discord.com/api/webhooks/222222222222222222/{SCHLUESSEL}x", "bot_id": 1}
SYNC = {"sync_webhook_url": f"https://discord.com/api/webhooks/333333333333333333/{SCHLUESSEL}y", "sync_index_id": "9"}


class Text(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        load_bot()
        cls.m = sys.modules["uploader_bot"]

    def test_kennungen_ohne_schluessel(self):
        ids = self.m.hook_ids(CONF, SYNC)
        self.assertEqual(ids, "Daten 111111111111111111, Testberichte 222222222222222222, #sync-daten 333333333333333333")
        self.assertNotIn("geheim", ids)
        self.assertEqual(self.m.hook_ids({"webhook_url": "kaputt"}, None), "")
        self.assertEqual(self.m.hook_ids(CONF, None), "Daten 111111111111111111, Testberichte 222222222222222222")

    def test_gleiche_form_wie_im_uploader_fenster(self):
        sys.path.insert(0, os.path.join(HERE, "..", "..", "RaidMasterUploader"))
        try:
            import einstellungen
        except ImportError:
            self.skipTest("RaidMasterUploader fehlt")
        self.assertIn(einstellungen.ids("uploader_config", CONF), self.m.hook_ids(CONF, SYNC))
        self.assertIn(einstellungen.ids("sync_config", SYNC), self.m.hook_ids(CONF, SYNC))

    def test_einrichtungstext(self):
        t = self.m.setup_text("zip", CONF, SYNC, ["Uploader-Version **2.3.28**."])
        self.assertIn("Uploader und Addons aktualisieren sich selbst** (ab Uploader 2.3.29, nur stabile Versionen)", t)   # DC-UPD1
        self.assertIn("Addons-automatisch-aus.bat", t)
        self.assertIn("The uploader and add-ons update themselves (from uploader 2.3.29, stable versions only)", t)
        self.assertNotIn("Addons-automatisch-an.bat", t)                 # überholt (Entscheid 27.11. 07:10)
        self.assertIn("Datei herunterladen – fertig.** Der Uploader übernimmt neue Einstellungen aus dem Download-Ordner selbst", t)
        self.assertIn("Download the file – done. The uploader takes over new settings from the Downloads folder by itself", t)
        self.assertNotIn("Frage im Uploader-Fenster", t)                  # keine j/n-Frage mehr (RM-UPD3)
        self.assertIn("Kanal-Kennungen (zum Vergleich mit der Meldung „Neue Einstellungen übernommen“ im Uploader-Fenster): "
                      "Daten 111111111111111111", t)
        self.assertNotIn(SCHLUESSEL, t)
        ohne_zip = self.m.setup_text(None, CONF, None, [])
        self.assertNotIn("aktualisieren sich selbst", ohne_zip)        # ohne ZIP: kein Uploader-Hinweis

    def test_lange_nachricht_in_teilen(self):
        notes = [f"Hinweis {i}: " + "z" * 150 for i in range(12)]
        t = self.m.setup_text("zip", CONF, SYNC, notes)
        self.assertGreater(len(t), 2000)
        sent = []

        async def send(content, files=None):
            sent.append((content, files))
        asyncio.run(self.m.send_parts(send, t, ["datei"]))
        self.assertGreater(len(sent), 1)
        self.assertTrue(all(len(c) <= 1900 for c, _ in sent))
        self.assertEqual(sent[0][1], ["datei"])
        self.assertTrue(all(f is None for _, f in sent[1:]))
        joined = "\n".join(c for c, _ in sent)
        for ln in t.splitlines():
            self.assertIn(ln, joined)
        sent.clear()
        asyncio.run(self.m.send_parts(send, "kurz", ["d"]))
        self.assertEqual(sent, [("kurz", ["d"])])

    def test_alle_drei_wege_mit_tipp(self):
        import bot_quelle
        self.assertIn("ADDONS_AUTO_TIPP", bot_quelle.funktion("uploader_cmd"))          # nur_programm
        self.assertIn("setup_text(", bot_quelle.funktion("uploader_cmd"))               # Einrichtung
        self.assertIn("ADDONS_AUTO_TIPP", bot_quelle.funktion("uploader_to_officers"))  # an_offiziere
        self.assertIn("send_parts(target.send", bot_quelle.funktion("uploader_cmd"))

    def test_anleitung(self):
        with open(os.path.join(HERE, "..", "ANLEITUNG.md"), encoding="utf-8") as f:
            a = f.read()
        self.assertIn("Uploader und Addons aktualisieren sich selbst (ab Uploader 2.3.29, nur stabile Versionen)", a)
        self.assertIn("the uploader and add-ons update themselves", a)
        self.assertNotIn("Addons-automatisch-an.bat", a)
        self.assertIn("Einstellungsdateien automatisch (ab Uploader 2.3.30)", a)
        self.assertIn("The uploader takes over new settings from the Downloads folder by itself", a)
        self.assertIn("Kanal-Kennungen", a)


if __name__ == "__main__":
    unittest.main()
