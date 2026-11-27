"""UP-CFG1 (2.3.27) / RM-UPD3 (2.3.30): Einstellungsdateien aus dem Download-Ordner – automatisch, nur mit geprüfter Herkunft
(gleicher Bot, gleicher Discord-Server). Tests mit Gegenproben.

Nachbau: Uploader-Ordner und Download-Ordner in einem Arbeitsordner; Zeit und Tasten nachgebildet. Keine echten Webhook-Adressen.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import einstellungen  # noqa: E402
import selfupdate  # noqa: E402

T0 = 1_800_000_000.0


def hook(n, key="A" * 30):
    return f"https://discord.com/api/webhooks/{n}/{key}"


BOT = 111111111111111111
OLD_UP = {"webhook_url": hook(1000001), "test_webhook_url": hook(1000002), "bot_id": BOT, "savedvariables_path": "C:/WoW/SV",
          "check_seconds": 10, "sent_shots": ["a.jpg", "b.jpg"], "addons_auto_installieren": True}
NEW_UP = {"webhook_url": hook(2000001), "test_webhook_url": hook(2000002), "bot_id": BOT, "savedvariables_path": "", "check_seconds": 10}
OLD_SY = {"sync_webhook_url": hook(3000001), "sync_index_id": "4000001"}
NEW_SY = {"sync_webhook_url": hook(3000009), "sync_index_id": "4000009"}


GUILD, OTHER = "900000000000000001", "900000000000000002"


class FakeDiscord:
    """GET einer Webhook-Adresse -> {"id", "guild_id"}; …/messages/<id> -> Nachricht, wenn sie diesem Webhook gehört."""

    def __init__(self):
        self.hooks = {}            # Kennung -> Server
        self.msgs = {}             # Kennung -> {Nachricht-Kennung}
        self.down = False
        self.calls = []

    def add(self, n, guild=GUILD, msgs=()):
        self.hooks[str(n)] = guild
        self.msgs[str(n)] = {str(m) for m in msgs}

    def __call__(self, url):
        self.calls.append(url)
        if self.down:
            return 0, None
        m = einstellungen.HOOK_RE.match(url.split("/messages/")[0])
        if not m or m.group(1) not in self.hooks:
            return 404, None
        hid = m.group(1)
        if "/messages/" in url:
            mid = url.rsplit("/", 1)[1]
            return (200, {"id": mid}) if mid in self.msgs[hid] else (404, None)
        return 200, {"id": hid, "guild_id": self.hooks[hid], "token": "geheim"}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.here = os.path.join(self.tmp, "RaidMasterUploader")
        self.dl = os.path.join(self.tmp, "Downloads")
        os.makedirs(self.here)
        os.makedirs(self.dl)
        self.write(self.here, "uploader_config.json", OLD_UP, T0 - 86400)
        self.write(self.here, "sync_config.json", OLD_SY, T0 - 86400)
        self.t = [T0]
        self.logs, self.st = [], {}
        self.dc = FakeDiscord()
        for n in (1000001, 1000002, 2000001, 2000002, 3000001):
            self.dc.add(n)
        self.dc.add(3000009, msgs=[4000009])
        self.p = self.make()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make(self, cfg=None):
        return einstellungen.Pickup(self.here, cfg if cfg is not None else {}, self.st, lambda: None, self.logs.append,
                                    downloads=self.dl, now=lambda: self.t[0], fetch=self.dc)

    def write(self, d, name, data, mt, raw=None):
        p = os.path.join(d, name)
        with open(p, "wb") as f:
            f.write(raw if raw is not None else json.dumps(data).encode())
        os.utime(p, (mt, mt))
        return p

    def read(self, name):
        with open(os.path.join(self.here, name), encoding="utf-8") as f:
            return json.load(f)

    def poll(self, dt=einstellungen.POLL_SECONDS):
        self.t[0] += dt
        return self.p.poll()


class Automatisch(Base):
    def test_uploader_config_ohne_eingabe_nur_bot_schluessel(self):
        self.write(self.dl, "uploader_config.json", NEW_UP, T0 + 5)
        o = self.poll()
        self.assertIsNotNone(o)
        self.assertIn("Daten 1000001, Testberichte 1000002 -> Daten 2000001, Testberichte 2000002", o["text"])
        self.assertNotIn("A" * 30, o["text"])                                         # geheimer Schlüssel nie gezeigt
        self.assertNotIn("(j/n)", o["text"])
        self.assertEqual(self.p.accept(o), "neustart")
        got = self.read("uploader_config.json")
        self.assertEqual(got["webhook_url"], NEW_UP["webhook_url"])
        self.assertEqual(got["test_webhook_url"], NEW_UP["test_webhook_url"])
        for k in ("savedvariables_path", "sent_shots", "addons_auto_installieren", "check_seconds"):
            self.assertEqual(got[k], OLD_UP[k], k)                                   # alles andere bleibt
        bdir = os.path.join(self.here, "_update", "einstellungen")
        backups = os.listdir(bdir)
        self.assertEqual(len(backups), 1)
        with open(os.path.join(bdir, backups[0]), encoding="utf-8") as f:
            self.assertEqual(json.load(f), OLD_UP)                                   # alte gesichert
        self.assertTrue(os.path.isfile(os.path.join(self.dl, "uploader_config.json")))   # im Download-Ordner nichts gelöscht
        self.assertTrue(any(l.startswith("Neue Einstellungen übernommen (uploader_config: Kanal-Kennung") for l in self.logs))
        self.assertEqual(self.st["daten"]["einstellungen"]["ergebnis"], "übernommen")   # stand.json
        self.assertNotIn("A" * 30, json.dumps(self.st))                              # kein Schlüssel im Zustand
        self.assertIsNone(self.poll())                                               # nicht nochmals

    def test_sync_config_ganz_ohne_neustart_index_gehoert_zum_webhook(self):
        self.write(self.dl, "sync_config (1).json", NEW_SY, T0 + 5)                  # so legt Discord/Browser Doppelte ab
        o = self.poll()
        self.assertIn("#sync-daten 3000001 -> #sync-daten 3000009", o["text"])
        self.assertEqual(self.p.accept(o), "ok")
        self.assertEqual(self.read("sync_config.json"), NEW_SY)
        self.assertTrue(any("/messages/4000009" in c for c in self.dc.calls))        # Index-Nachricht geprüft

    def test_neueste_kopie_gewinnt(self):
        self.dc.add(3000005, msgs=[4000005])
        self.write(self.dl, "sync_config.json", {"sync_webhook_url": hook(3000005), "sync_index_id": "4000005"}, T0 + 1)
        self.write(self.dl, "sync_config (2).json", NEW_SY, T0 + 9)
        o = self.poll()
        self.assertTrue(o["path"].endswith("sync_config (2).json"))

    def test_erste_einrichtung(self):
        os.remove(os.path.join(self.here, "uploader_config.json"))
        self.write(self.dl, "uploader_config (3).json", NEW_UP, T0)
        self.assertTrue(einstellungen.first_setup(self.here, self.logs.append, downloads=self.dl, fetch=self.dc))
        self.assertEqual(self.read("uploader_config.json"), NEW_UP)
        self.assertFalse(einstellungen.first_setup(self.here, self.logs.append, downloads=self.dl, fetch=self.dc))  # nur einmal
        # Gegenprobe: Adresse bei Discord unbekannt -> nicht übernommen
        os.remove(os.path.join(self.here, "uploader_config.json"))
        self.write(self.dl, "uploader_config (3).json", dict(NEW_UP, webhook_url=hook(7777777)), T0)
        self.assertFalse(einstellungen.first_setup(self.here, self.logs.append, downloads=self.dl, fetch=self.dc))
        self.assertFalse(os.path.exists(os.path.join(self.here, "uploader_config.json")))


class Schutz(Base):
    def none(self, name, data, why=None, mt=T0 + 5, raw=None):
        self.write(self.dl, name, data, mt, raw=raw)
        self.assertIsNone(self.poll())
        if why:
            self.assertTrue(any(why in l for l in self.logs), self.logs)
        self.assertEqual(self.read("uploader_config.json"), OLD_UP)
        self.assertEqual(self.read("sync_config.json"), OLD_SY)

    def test_anderer_bot_verworfen_ohne_frage(self):
        self.none("uploader_config.json", dict(NEW_UP, bot_id=222222222222222222), "anderen Bot")
        self.assertEqual(self.st["daten"]["einstellungen"]["ergebnis"], "verworfen")
        self.assertIn("anderen Bot", self.st["daten"]["einstellungen"]["grund"])
        self.assertFalse(any("(j/n)" in l for l in self.logs))

    def test_anderer_server_verworfen_gegenprobe(self):
        self.dc.add(2000001, guild=OTHER)                                            # fremder Discord-Server
        self.none("uploader_config.json", NEW_UP, "anderen Discord-Server")
        self.dc.add(3000009, guild=OTHER, msgs=[4000009])
        self.t[0] += 3600
        self.none("sync_config.json", NEW_SY, "anderen Discord-Server", mt=T0 + 3700)
        # Gegenprobe: gleicher Server -> übernommen (neuer Lauf: der Server einer Adresse wird je Lauf gemerkt)
        self.dc.add(2000001)
        self.p = self.make()
        self.write(self.dl, "uploader_config (1).json", dict(NEW_UP, test_webhook_url=hook(2000003)), T0 + 7300)
        self.dc.add(2000003)
        self.t[0] += 7300
        self.assertIsNotNone(self.p.poll())

    def test_geloeschte_adresse_und_fremder_index(self):
        self.none("uploader_config.json", dict(NEW_UP, webhook_url=hook(6666666)), "ungültig oder gelöscht")
        self.t[0] += 3600
        self.none("sync_config.json", dict(NEW_SY, sync_index_id="4999999"), "keine Nachricht dieses Webhooks", mt=T0 + 3700)

    def test_netzfehler_spaeter_nicht_uebernommen(self):
        self.dc.down = True
        self.write(self.dl, "uploader_config.json", NEW_UP, T0 + 5)
        self.assertIsNone(self.poll())
        self.assertTrue(any("nicht prüfbar" in l for l in self.logs))
        self.assertEqual(self.read("uploader_config.json"), OLD_UP)
        n = len(self.dc.calls)
        self.assertIsNone(self.poll(300))                                            # innerhalb 10 Min. kein neuer Versuch
        self.assertEqual(len(self.dc.calls), n)
        self.dc.down = False
        self.assertIsNotNone(self.poll(einstellungen.NET_RETRY))                     # danach: geprüft und übernehmbar
        self.assertNotIn("einstellungen", self.st.get("daten", {}))                  # Netzfehler ist kein Verwerfen

    def test_ohne_bisherige_adresse_nicht_pruefbar(self):
        self.write(self.here, "uploader_config.json", dict(OLD_UP, webhook_url=""), T0 - 86400)
        self.write(self.dl, "sync_config.json", NEW_SY, T0 + 5)
        self.assertIsNone(self.poll())
        self.assertTrue(any("bisheriger Server nicht prüfbar" in l for l in self.logs))
        self.assertEqual(self.read("sync_config.json"), OLD_SY)

    def test_keine_discord_adresse(self):
        self.none("uploader_config.json", dict(NEW_UP, webhook_url="https://evil.example/api/webhooks/1/xxxxxxxxxxxxxxxxxxxxxxx"),
                  "keine Discord-Webhook-Adresse")
        self.t[0] += 3600
        self.none("sync_config.json", dict(NEW_SY, sync_webhook_url="http://discord.com/api/webhooks/12345/" + "B" * 30),
                  "keine Discord-Webhook-Adresse", mt=T0 + 3700)
        self.assertEqual(self.dc.calls, [])                                          # ungültige Form: Discord nicht gefragt

    def test_alte_kopie_nicht_angeboten(self):
        self.none("uploader_config.json", NEW_UP, mt=T0 - 2 * 3600)                   # älter als die Grundzeit
        self.none("sync_config.json", NEW_SY, mt=T0 - 86400 - 10)                    # älter als die Datei im Ordner

    def test_gleiche_kanaele_nicht_angeboten(self):
        self.none("uploader_config.json", dict(OLD_UP, sent_shots=[]))

    def test_verworfene_nie_wieder(self):
        self.none("uploader_config.json", dict(NEW_UP, bot_id=222222222222222222), "anderen Bot")
        os.utime(os.path.join(self.dl, "uploader_config.json"), (T0 + 600, T0 + 600))   # gleicher Inhalt, neue Zeit
        n = len(self.logs)
        self.assertIsNone(self.poll(700))
        self.assertEqual(len(self.logs), n)                                          # nicht einmal mehr gemeldet

    def test_kaputt_zu_gross_falscher_name(self):
        self.none("uploader_config.json", None, raw=b"{kein json")
        self.none("sync_config.json", None, "zu gross", raw=b" " * (einstellungen.MAX_BYTES + 10) + b"{}", mt=T0 + 6)
        self.none("daten_config.json", {"repo": "a/b", "token": "x"}, mt=T0 + 7)       # nie
        self.none("uploader_config_alt.json", NEW_UP, mt=T0 + 8)

    def test_schalter_aus(self):
        self.p = self.make({einstellungen.SWITCH_KEY: False})
        self.none("uploader_config.json", NEW_UP)
        self.p = self.make({})                                                       # Gegenprobe: fehlt = an
        self.t[0] += 60
        self.assertIsNotNone(self.p.poll())

    def test_takt(self):
        self.write(self.dl, "sync_config.json", NEW_SY, T0 + 5)
        self.t[0] += 1
        self.p.next_at = self.t[0] + 10
        self.assertIsNone(self.p.poll())
        self.t[0] += 10
        self.assertIsNotNone(self.p.poll())

    def test_laufender_uploader_ueberschreibt_adressen_nie(self):
        import uploader
        old = uploader.CONFIG
        uploader.CONFIG = os.path.join(self.here, "uploader_config.json")
        try:
            self.write(self.dl, "uploader_config.json", NEW_UP, T0 + 5)
            self.p.accept(self.poll())
            running = dict(OLD_UP, sent_shots=OLD_UP["sent_shots"] + ["c.jpg"])     # Stand vom Start (alte Adressen)
            uploader.save_config(running)
            got = self.read("uploader_config.json")
            self.assertEqual(got["webhook_url"], NEW_UP["webhook_url"])             # neue Adresse bleibt
            self.assertEqual(got["sent_shots"], ["a.jpg", "b.jpg", "c.jpg"])        # sein eigener Teil schon
        finally:
            uploader.CONFIG = old


class Ablauf(Base):
    """Zusammenspiel mit dem Uploader (keine Frage mehr) und dem Neustart."""

    def su(self, start_ok=True):
        self.events = []

        class Proc:
            returncode = None

            def poll(self):
                return None

        def spawn(here):
            if start_ok:
                selfupdate.report_running(here, "2.3.30")
            return Proc()
        return selfupdate.SelfUpdate(self.here, "2.3.30", self.st, lambda: None, self.logs.append, latest=lambda: "2.3.30",
                                     minimum=lambda: "2.3.20", fetch_zip=None, key=lambda: None,
                                     spawn=spawn, handover=lambda: self.events.append("handover"),
                                     takeback=lambda: self.events.append("takeback"), sleep=lambda s: None,
                                     now=lambda: self.t[0], console=lambda: None, kill_console=lambda p: True,
                                     kill=lambda p: self.events.append("kill"), pickup=self.p)

    def test_uploader_config_ohne_taste_neustart(self):
        self.write(self.dl, "uploader_config.json", NEW_UP, T0 + 5)
        u = self.su()
        self.t[0] += 60
        self.assertTrue(u.tick())                                                    # übernommen + neu gestartet, ohne Taste
        self.assertIn("Uploader neu gestartet (neue Einstellungen).", self.logs)
        self.assertEqual(self.read("uploader_config.json")["webhook_url"], NEW_UP["webhook_url"])
        self.assertFalse(any("(j/n)" in l for l in self.logs))

    def test_neustart_scheitert_laeuft_weiter(self):
        self.write(self.dl, "uploader_config.json", NEW_UP, T0 + 5)
        u = self.su(start_ok=False)
        self.t[0] += 60
        self.assertFalse(u.tick())
        self.assertIn("takeback", self.events)
        self.assertTrue(any("Neustart nicht gelungen" in l for l in self.logs))

    def test_verworfen_kein_neustart_gegenprobe(self):
        self.write(self.dl, "uploader_config.json", dict(NEW_UP, bot_id=222222222222222222), T0 + 5)
        u = self.su()
        self.t[0] += 60
        for _ in range(5):
            self.assertFalse(u.tick())
        self.assertEqual(self.events, [])
        self.assertEqual(self.read("uploader_config.json"), OLD_UP)


if __name__ == "__main__":
    unittest.main()
