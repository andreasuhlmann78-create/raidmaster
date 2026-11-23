"""T-ANN-RESTORE: wiederhergestellte Ankündigungen (Entscheid des Nutzers 23.11. 11:36/11:45, ab Bot 1.5.191) – ohne Netz.

Liegt eine im Repo gelöschte Ankündigung wieder in announce/, entfernt der Bot ihre Kopie aus announce_entfernt/, löscht im
Discord nichts und lässt "announced"/Beiträge stehen (kein neues Posten). Die Warnung bei zu vielen Löschungen nennt ALLE
Dateinamen (roh), verteilt auf Nachrichten unter 2000 Zeichen; wiederhergestellte zählen nicht mehr mit.
"""
import asyncio
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Wiederherstellen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["ankuendigung_bot"]

    def setUp(self):
        m = self.m
        self.dir = tempfile.mkdtemp()
        self.ann, self.rem = os.path.join(self.dir, "announce"), os.path.join(self.dir, "announce_entfernt")
        os.makedirs(self.ann)
        os.makedirs(self.rem)
        self.saved = (m.ANNOUNCE_DIR, m.ANNOUNCE_REMOVED_DIR, m.bot_guild, m.post_bot_log, m.state.save,
                      {k: m.state.data.get(k) for k in ("announced", "announce_msgs", "announce_delete_warned")},
                      m.channel_by_id)
        m.ANNOUNCE_DIR, m.ANNOUNCE_REMOVED_DIR = self.ann, self.rem
        m.bot_guild = lambda: object()
        m.state.save = lambda: None
        self.logs, self.fetched = [], []

        async def blog(t):
            self.logs.append(t)

        async def ch(cid):
            self.fetched.append(cid)
            return None
        m.post_bot_log, m.channel_by_id = blog, ch
        self.names = [f"guildsentinel__guildsentinel-0-vorstellung-{i}.md" for i in range(2, 36)]   # 34 Dateien
        for n in self.names:
            for d in (self.rem,):
                with open(os.path.join(d, n), "w", encoding="utf-8") as f:
                    f.write("x")
        m.state.data["announced"] = list(self.names)
        m.state.data["announce_msgs"] = {n: {"ch": 5, "ids": [100 + i]} for i, n in enumerate(self.names)}
        m.state.data.pop("announce_delete_warned", None)

    def tearDown(self):
        m = self.m
        m.ANNOUNCE_DIR, m.ANNOUNCE_REMOVED_DIR, m.bot_guild, m.post_bot_log, m.state.save = self.saved[:5]
        for k, v in self.saved[5].items():
            if v is None:
                m.state.data.pop(k, None)
            else:
                m.state.data[k] = v
        m.channel_by_id = self.saved[6]
        shutil.rmtree(self.dir)

    def restore(self, names):
        for n in names:
            with open(os.path.join(self.ann, n), "w", encoding="utf-8") as f:
                f.write("x")

    def run_(self):
        asyncio.run(self.m.remove_deleted_announcements())

    def test_warnung_nennt_alle(self):
        self.run_()
        text = "\n".join(self.logs)
        self.assertIn("**34 Ankündigungen**", self.logs[0])
        for n in self.names:
            self.assertIn(f"`{n}`", text)                                   # alle, roh (keine __-Formatierung)
        self.assertTrue(all(len(p) <= 2000 for p in self.logs))
        self.assertGreater(len(self.logs), 1)
        self.assertEqual(self.fetched, [])                                  # nichts gelöscht

    def test_einmal_auch_nach_alter_fassung(self):
        self.m.state.data["announce_delete_warned"] = sorted(self.names)      # Merker von 1.5.190 (nur Liste)
        self.run_()
        n = len(self.logs)
        self.assertGreater(n, 0)                                            # neue Fassung -> einmal melden
        self.run_()
        self.assertEqual(len(self.logs), n)                                 # danach nicht wiederholen

    def test_teilweise_wiederhergestellt(self):
        self.restore(self.names[:2])
        self.run_()
        self.assertIn("**32 Ankündigungen**", self.logs[0])
        self.assertEqual(sorted(os.listdir(self.rem)), sorted(self.names[2:]))
        self.assertEqual(self.m.state.data["announced"], self.names)        # bleiben angekündigt -> kein neues Posten
        self.assertEqual(self.fetched, [])

    def test_alle_wiederhergestellt(self):
        self.m.state.data["announce_delete_warned"] = sorted(self.names)
        self.restore(self.names)
        self.run_()
        self.assertEqual(os.listdir(self.rem), [])
        self.assertEqual(self.logs, [])
        self.assertNotIn("announce_delete_warned", self.m.state.data)
        self.assertEqual(self.m.state.data["announced"], self.names)
        self.assertEqual(len(self.m.state.data["announce_msgs"]), 34)        # Beiträge bleiben gemerkt
        self.assertEqual(self.fetched, [])


if __name__ == "__main__":
    unittest.main()
