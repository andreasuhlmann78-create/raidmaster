"""T-D-ANN2 / T-D-LOG1 / T-D-ANN1B (ab Bot 1.5.192) – ohne Netz.

D-ANN2 (Entscheid des Nutzers 23.11. 12:03 "alte Addon-Versionen auf keinen Fall wieder posten"): Eine Ankündigung, deren Version
älter oder gleich der neuesten schon geposteten derselben Reihe ist, wird nie gepostet, auch wenn ihre Datei neu in announce/
auftaucht – nur einmal in #bot-log gemeldet. Eine neuere wird gepostet; Dateien ohne Versionsnummer wie bisher.
D-LOG1: lange #bot-log-Meldungen werden in Teile <= 1990 Zeichen geteilt, nichts geht verloren.
D-ANN1 b: announce_guard meldet gelöschte/umbenannte announce/*.md und *.zip (Workflow wird rot).
"""
import asyncio
import os
import shutil
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Kanal:
    def __init__(self):
        self.sent, self.id = [], 5

    async def send(self, text=None, **kw):
        self.sent.append(text)
        return types.SimpleNamespace(id=1000 + len(self.sent))


class AlteVersionen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["ankuendigung_bot"]

    def setUp(self):
        m = self.m
        self.dir = tempfile.mkdtemp()
        names = ("ANNOUNCE_DIR", "announce_target", "cleanup_announcements_once", "remove_deleted_announcements",
                 "resolve_announce_text", "remove_old_announcements", "remove_same_title", "post_bot_log")
        self.saved = {k: getattr(m, k) for k in names}
        self.saved_state = {k: m.state.data.get(k) for k in ("announced", "announce_msgs", "announce_old_skipped")}
        self.saved_save = m.state.save
        m.ANNOUNCE_DIR = self.dir
        self.ch, self.logs = Kanal(), []

        async def target(fn):
            return self.ch

        async def noop(*a, **k):
            return 0

        async def resolve(text):
            return text, []

        async def blog(t):
            self.logs.append(t)
        m.announce_target, m.cleanup_announcements_once, m.remove_deleted_announcements = target, noop, noop
        m.resolve_announce_text, m.remove_old_announcements, m.remove_same_title, m.post_bot_log = resolve, noop, noop, blog
        m.state.save = lambda: None
        m.state.data["announced"] = ["ahsentinel__ahsentinel-0.65.384.md", "x__neu.md"]
        m.state.data["announce_msgs"] = {}
        m.state.data.pop("announce_old_skipped", None)

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        for k, v in self.saved_state.items():
            if v is None:
                m.state.data.pop(k, None)
            else:
                m.state.data[k] = v
        m.state.save = self.saved_save
        shutil.rmtree(self.dir)

    def datei(self, name, text="📢 Titel der Ankündigung\nInhalt"):
        with open(os.path.join(self.dir, name), "w", encoding="utf-8") as f:
            f.write(text)

    def run_(self):
        asyncio.run(self.m.check_announcements())

    def test_aelter_und_gleich_nie(self):
        self.datei("ahsentinel__ahsentinel-0.65.383.md")                  # älter (z. B. wiederhergestellt)
        self.datei("ahsentinel__ahsentinel-0.65.384-neu.md")              # gleiche Version, anderer Name
        self.run_()
        self.assertEqual(self.ch.sent, [])
        self.assertEqual(len(self.logs), 1)                                 # ab 1.5.194: eine Meldung für alle
        self.assertIn("NICHT gepostet", self.logs[0])
        self.assertIn("• `ahsentinel__ahsentinel-0.65.383.md`: Fassung 0.65.383 ist nicht neuer als die schon gepostete 0.65.384",
                      self.logs[0])
        self.assertIn("• `ahsentinel__ahsentinel-0.65.384-neu.md`:", self.logs[0])
        self.assertNotIn("ahsentinel__ahsentinel-0.65.383.md", self.m.state.data["announced"])
        self.run_()
        self.assertEqual(len(self.logs), 1)                                 # nur einmal melden
        self.assertEqual(self.ch.sent, [])

    def test_neuer_und_ohne_version(self):
        self.datei("ahsentinel__ahsentinel-0.65.385.md")
        self.datei("y__ohne-version.md")
        self.run_()
        self.assertEqual(len(self.ch.sent), 2)
        self.assertIn("ahsentinel__ahsentinel-0.65.385.md", self.m.state.data["announced"])
        self.datei("ahsentinel__ahsentinel-0.65.384-b.md")                # jetzt älter als 385
        self.run_()
        self.assertEqual(len(self.ch.sent), 2)
        self.assertIn("schon gepostete 0.65.385", self.logs[-1])

    def test_neueste_im_selben_lauf(self):
        self.datei("ahsentinel__ahsentinel-0.65.386.md")
        self.datei("ahsentinel__ahsentinel-0.65.390.md")                  # sortiert: 386 vor 390 -> beide neuer
        self.run_()
        self.assertEqual(len(self.ch.sent), 2)

    def test_aelter_nach_neuer_im_selben_lauf(self):
        self.m.state.data["announced"] = ["ahsentinel__ahsentinel-0.65.30.md"]   # beide neuer als das schon Gepostete
        self.datei("ahsentinel__ahsentinel-0.65.385.md")                  # Text-Sortierung: 0.65.385 vor 0.65.39
        self.datei("ahsentinel__ahsentinel-0.65.39.md")                   # 0.65.39 ist älter als 0.65.385
        self.run_()
        self.assertEqual(len(self.ch.sent), 1)
        self.assertIn("• `ahsentinel__ahsentinel-0.65.39.md`: Fassung 0.65.39 ist nicht neuer", self.logs[-1])


class LogTeilen(unittest.TestCase):
    def test_teilen(self):
        import grund
        text = "Kopf\n" + "\n".join(f"• zeile-{i:04d}-" + "x" * 40 for i in range(200))
        parts = grund.split_log(text)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(p) <= 1990 for p in parts))
        self.assertEqual("\n".join(parts), text)                            # nichts verloren
        lang = "y" * 5000
        self.assertEqual("".join(grund.split_log(lang)), lang)
        self.assertEqual(grund.split_log("kurz"), ["kurz"])
        self.assertEqual(grund.split_log(""), [""])

    def test_post_bot_log_sendet_alle_teile(self):
        import grund
        sent = []

        class Ch:
            async def send(self_, t):
                sent.append(t)

        async def by_id(cid):
            return Ch()
        saved = grund.channel_by_id
        grund.channel_by_id = by_id
        try:
            text = "\n".join("z" * 100 for _ in range(50))
            asyncio.run(grund.post_bot_log(text))
        finally:
            grund.channel_by_id = saved
        self.assertGreater(len(sent), 1)
        self.assertEqual("\n".join(sent), text)


class Waechter(unittest.TestCase):
    def test_geloescht_und_umbenannt(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
        import announce_guard as g
        lines = ["D\tannounce/a__x-1.0.md", "R100\tannounce/b__y.md\tannounce/b__z.md", "M\tannounce/c.md",
                 "A\tannounce/d.md", "D\tannounce/bild.png", "D\tannounce/paket.zip", "D\tRaidMasterBot/bot.py",
                 "R090\tannounce/e.zip\tdownload/e.zip"]
        self.assertEqual(g.violations(lines), ["announce/a__x-1.0.md (gelöscht)", "announce/b__y.md (umbenannt)",
                                               "announce/paket.zip (gelöscht)", "announce/e.zip (umbenannt)"])
        self.assertEqual(g.violations(["M\tannounce/c.md", "A\tannounce/neu.md", ""]), [])


if __name__ == "__main__":
    unittest.main()
