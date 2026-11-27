"""T-DC-ANN1 (ab Bot 1.5.201, Auftrag Supervisor 27.11. 10:45): RaidMaster nur über announce/ ankündigen. Wechselt die stabile
Version in download/ (Paket im Bot), wird die Vorstellung in #raid-addon BEARBEITET (Text + ZIP am ersten Beitrag) – kein zweiter
Beitrag. Eine Version -> genau ein Beitrag (die Ankündigung aus announce/). Gegenprobe: ohne Vorstellung wird sie gepostet.
Der Ersatz-Weg (Neu-Posten) löscht nie Ankündigungen aus announce/."""
import asyncio
import os
import shutil
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)


class Msg:
    def __init__(self, mid, content="", author=None):
        self.id, self.content, self.author, self.attachments = mid, content, author, []
        self.jump_url = f"https://discord.com/channels/1/77/{mid}"
        self.deleted = False

    async def delete(self):
        self.deleted = True


class Partial:
    def __init__(self, ch, mid):
        self.ch, self.id = ch, mid

    async def edit(self, content=None, attachments=None, **kw):
        self.ch.edits.append((self.id, content, [getattr(a, "filename", None) for a in (attachments or [])]))


class Kanal:
    def __init__(self, me, history=()):
        self.id, self.me = 77, me
        self.sent, self.edits, self.hist = [], [], list(history)

    async def send(self, text=None, file=None, files=None, **kw):
        m = Msg(5000 + len(self.sent), text, self.me)
        self.sent.append((text, getattr(file, "filename", None)))
        self.hist.append(m)
        return m

    def get_partial_message(self, mid):
        return Partial(self, mid)

    async def history(self, limit=None):
        for m in list(self.hist):
            yield m


class DcAnn1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        load_bot()
        cls.m = sys.modules["ankuendigung_bot"]

    def setUp(self):
        m = self.m
        self.dir = tempfile.mkdtemp()
        self.zip = os.path.join(self.dir, "RaidMaster-3.0.53.zip")
        with open(self.zip, "wb") as f:
            f.write(b"PK\x05\x06" + b"\0" * 18)
        keys = ("addon_intro", "addon_message", "announce_msgs", "announced", "announce_old_skipped")
        self.saved_state = {k: m.state.data.get(k) for k in keys}
        self.saved_save = m.state.save
        m.state.save = lambda: None
        self.saved_sleep = m.asyncio.sleep

        async def nosleep(_):
            return None
        m.asyncio.sleep = nosleep
        self.me = object()
        self.saved_user = m.bot.__dict__.get("_test_user")
        self.saved_intro = m.ADDON_INTRO
        m.ADDON_INTRO = os.path.join(HERE, "..", "raid_addon_intro.md")
        self.posts = m.addon_intro_posts("3.0.53")
        self.assertTrue(self.posts, "raid_addon_intro.md fehlt")

    def tearDown(self):
        m = self.m
        for k, v in self.saved_state.items():
            if v is None:
                m.state.data.pop(k, None)
            else:
                m.state.data[k] = v
        m.state.save = self.saved_save
        m.asyncio.sleep = self.saved_sleep
        m.ADDON_INTRO = self.saved_intro
        shutil.rmtree(self.dir)

    def run_(self, coro):
        return asyncio.run(coro)

    def test_neue_stabile_version_bearbeitet_statt_neu(self):
        m = self.m
        ch = Kanal(self.me)
        ids = list(range(100, 100 + len(self.posts)))
        m.state.data["addon_intro"] = {"ch": ch.id, "ids": ids, "hash": "x", "version": "3.0.52"}
        self.assertTrue(self.run_(m.ensure_addon_intro(ch, self.zip, "3.0.53")))   # Version gewechselt -> True (PN folgt)
        self.assertEqual(ch.sent, [])                                             # KEIN neuer Beitrag
        self.assertEqual([e[0] for e in ch.edits], ids)
        self.assertEqual(ch.edits[0][2], ["RaidMaster-3.0.53.zip"])               # ZIP am ersten Beitrag ersetzt
        self.assertTrue(all(e[2] == [] for e in ch.edits[1:]))
        self.assertEqual(m.state.data["addon_intro"]["version"], "3.0.53")
        self.assertEqual(m.state.data["addon_intro"]["ids"], ids)
        ch.edits.clear()
        self.assertFalse(self.run_(m.ensure_addon_intro(ch, self.zip, "3.0.53")))  # gleiche Version: nichts
        self.assertEqual((ch.sent, ch.edits), ([], []))

    def test_eine_version_genau_ein_beitrag(self):
        """announce/raid-addon__raidmaster-3.0.53.md wird gepostet (1 Beitrag); danach wechselt download/ auf 3.0.53 -> 0 Beiträge."""
        m = self.m
        ch = Kanal(self.me)
        saved = {k: getattr(m, k) for k in ("ANNOUNCE_DIR", "announce_target", "cleanup_announcements_once",
                                            "remove_deleted_announcements", "resolve_announce_text",
                                            "remove_old_announcements", "remove_same_title", "post_bot_log")}
        adir = os.path.join(self.dir, "announce")
        os.makedirs(adir)
        with open(os.path.join(adir, "raid-addon__raidmaster-3.0.53.md"), "w", encoding="utf-8") as f:
            f.write("🛠️ **RaidMaster 3.0.53**\n• Testversion")

        async def target(fn):
            return ch

        async def noop(*a, **k):
            return 0

        async def resolve(t):
            return t, []
        try:
            m.ANNOUNCE_DIR, m.announce_target = adir, target
            m.cleanup_announcements_once = m.remove_deleted_announcements = noop
            m.remove_old_announcements = m.remove_same_title = m.post_bot_log = noop
            m.resolve_announce_text = resolve
            m.state.data["announced"], m.state.data["announce_msgs"] = [], {}
            ids = list(range(100, 100 + len(self.posts)))
            m.state.data["addon_intro"] = {"ch": ch.id, "ids": ids, "hash": "x", "version": "3.0.52"}
            self.run_(m.check_announcements())
            self.assertEqual(len(ch.sent), 1)
            self.run_(m.ensure_addon_intro(ch, self.zip, "3.0.53"))
            self.assertEqual(len(ch.sent), 1)                                    # genau ein Beitrag je Version
        finally:
            for k, v in saved.items():
                setattr(m, k, v)

    def test_gegenprobe_ohne_vorstellung_wird_gepostet_ohne_ankuendigung_zu_loeschen(self):
        m = self.m
        ann = Msg(42, "🛠️ **RaidMaster 3.0.53**", self.me)
        ann.attachments = [types.SimpleNamespace(filename="RaidMaster-3.0.53.zip")]   # sähe wie ein alter Versions-Post aus
        ch = Kanal(self.me, history=[ann])
        m.state.data.pop("addon_intro", None)
        m.state.data["announce_msgs"] = {"raid-addon__raidmaster-3.0.53.md": {"ch": ch.id, "ids": [42]}}
        saved_user = m.bot._connection.user if hasattr(m.bot, "_connection") else None
        try:
            if hasattr(m.bot, "_connection"):
                m.bot._connection.user = self.me
            self.assertTrue(self.run_(m.ensure_addon_intro(ch, self.zip, "3.0.53")))
        finally:
            if hasattr(m.bot, "_connection"):
                m.bot._connection.user = saved_user
        self.assertEqual(len(ch.sent), len(self.posts))                          # ohne Vorstellung: gepostet
        self.assertFalse(ann.deleted)                                            # Ankündigung aus announce/ bleibt


if __name__ == "__main__":
    unittest.main()
