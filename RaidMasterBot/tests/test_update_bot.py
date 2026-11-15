"""T-D3-UPDATE: Selbst-Update aus update_bot.py (D-3 Schritt 20, ab Bot 1.5.167) – ohne Netz, ohne Dateien.

Bis 1.5.166 gab es dafür nur eine Text-Prüfung. Hier läuft das Einspielen selbst (updater ersetzt):
Bot-Änderung -> Neustart angestossen und danach nichts mehr eingespielt (auch keine GitHub-Prüfung); ohne
Bot-Änderung -> Version gemerkt und Addon-Veröffentlichung geprüft; Fehler -> Version als fehlgeschlagen gemerkt;
/update nur für die Gildenleitung.
"""
import asyncio
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))


class Update(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["update_bot"]

    def setUp(self):
        m = self.m
        self.saved = {k: getattr(m, k) for k in ("updater", "restart_soon", "check_addon_release", "post_bot_log",
                                                 "is_admin", "_restart_pending")}
        self.saved_state, self.saved_save = dict(m.state.data), m.state.save
        m.state.save = lambda: None
        self.calls, self.result = [], {"bot_changed": [], "version": "1.5.200", "old_version": "1.5.199"}
        test = self

        class UpdateError(Exception):
            pass

        def install_zip(data, base, source, ref):
            test.calls.append("install")
            if test.result == "fehler":
                raise UpdateError("kaputte ZIP")
            return dict(test.result)
        m.updater = types.SimpleNamespace(install_zip=install_zip, UpdateError=UpdateError)

        async def restart():
            self.calls.append("restart")

        async def release():
            self.calls.append("release")

        async def log(text):
            self.calls.append("log")
        m.restart_soon, m.check_addon_release, m.post_bot_log = restart, release, log
        m._restart_pending = False

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        m.state.save = self.saved_save
        m.state.data.clear()
        m.state.data.update(self.saved_state)

    def run_async(self, coro):
        async def main():
            r = await coro
            await asyncio.sleep(0)                      # angestossene Aufgaben (create_task) laufen lassen
            return r
        return asyncio.run(main())

    def test_gleiche_objekte_in_bot(self):
        self.assertIs(self.bot.update_loop, self.m.update_loop)
        self.assertIs(self.bot.report_update_result, self.m.report_update_result)
        self.assertIs(self.bot.bot.tree.get_command("update").callback, self.m.update_cmd.callback)

    def test_bot_aenderung_neustart_und_danach_nichts(self):
        self.result = dict(self.result, bot_changed=["bot.py"])
        text = self.run_async(self.m.apply_update(b"zip", "Test", "abc1234"))
        self.assertIn("startet in wenigen Sekunden neu", text)
        self.assertEqual(self.calls, ["install", "log", "restart"])
        self.assertTrue(self.m._restart_pending)
        self.assertIn("schon installiert", self.run_async(self.m.apply_update(b"zip", "Test", "def5678")))
        self.assertIn("schon installiert", self.run_async(self.m.check_github()))
        self.assertEqual(self.calls.count("install"), 1)               # nichts mehr eingespielt

    def test_ohne_bot_aenderung_version_gemerkt(self):
        text = self.run_async(self.m.apply_update(b"zip", "GitHub", "abc1234"))
        self.assertIn("Bot unverändert", text)
        self.assertEqual(self.m.state.data["installed_sha"], "abc1234")
        self.assertEqual(self.calls, ["install", "log", "release"])
        self.assertFalse(self.m._restart_pending)

    def test_fehler_version_gemerkt(self):
        self.result = "fehler"
        text = self.run_async(self.m.apply_update(b"zip", "GitHub", "bad0000"))
        self.assertIn("nicht installiert: kaputte ZIP", text)
        self.assertEqual(self.m.state.data["failed_sha"], "bad0000")
        self.assertNotIn("restart", self.calls)

    def test_update_nur_gildenleitung(self):
        self.m.is_admin = lambda u: False
        msgs = []

        class R:
            async def send_message(self_, text, **kw):
                msgs.append(text)
        asyncio.run(self.m.update_cmd.callback(types.SimpleNamespace(user=1, response=R()), None))
        self.assertIn("nur der Gildenchef und die Offiziere", msgs[0])
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
