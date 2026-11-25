"""T-D-CI2: Bot stösst den Workflow "Testberichte" an (Auftrag Supervisor 25.11.2026 14:28) – Nachbau ohne echten Aufruf.

POST …/actions/workflows/testberichte.yml/dispatches {"ref":"main"}, höchstens alle 5 Min. (zusammenfassen), 401/403/404 einmal melden
und nicht wiederholen (bis anderer Token), Token frisch aus config.json, nie in Meldungen; save_config behält vom Nutzer neu
eingetragene Schlüssel.
"""
import asyncio
import json
import os
import shutil
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

GEHEIM = "github_pat_NURTEST000000000000000000000000"


class Basis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.b, _ = load_bot()
        cls.m = sys.modules["ci_anstoss"]
        cls.kern = sys.modules["kern"]

    def setUp(self):
        m = self.m
        self.dir = tempfile.mkdtemp()
        self.conf = os.path.join(self.dir, "config.json")
        self.write_conf({"token": "x", "github_actions_token": GEHEIM})
        self.saved = {k: getattr(m, k) for k in ("CONFIG_PATH", "_post", "_bot_log", "SPERRE")}
        self.saved_state = m.state.data.get("ci_anstoss_fehler")
        m.state.data.pop("ci_anstoss_fehler", None)
        self.saved_save = m.state.save
        m.state.save = lambda: None
        self.saved_repo = m.cfg.get("update_repo")
        m.cfg["update_repo"] = "andreasuhlmann78-create/raidmaster"
        m.CONFIG_PATH = self.conf
        m._last, m._pending, m._missing_told = 0.0, None, False
        self.posts, self.logs, self.status = [], [], 204

        async def post(url, token):
            self.posts.append((url, token))
            return self.status

        async def blog(t):
            self.logs.append(t)
        m._post, m._bot_log = post, blog

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        if self.saved_state is None:
            m.state.data.pop("ci_anstoss_fehler", None)
        else:
            m.state.data["ci_anstoss_fehler"] = self.saved_state
        m.state.save = self.saved_save
        m.cfg["update_repo"] = self.saved_repo
        m._last, m._pending, m._missing_told = 0.0, None, False
        shutil.rmtree(self.dir)

    def write_conf(self, d):
        with open(self.conf, "w", encoding="utf-8") as f:
            json.dump(d, f)


class Anstoss(Basis):
    def test_aufruf_richtig(self):
        self.assertEqual(asyncio.run(self.m.dispatch()), "ok")
        self.assertEqual(self.posts, [("https://api.github.com/repos/andreasuhlmann78-create/raidmaster/actions/workflows/"
                                       "testberichte.yml/dispatches", GEHEIM)])
        self.assertEqual(self.logs, [])

    def test_kein_token_einmal_melden(self):
        self.write_conf({"token": "x"})
        self.assertEqual(asyncio.run(self.m.dispatch()), "kein_token")
        self.assertEqual(asyncio.run(self.m.dispatch()), "kein_token")
        self.assertEqual(len(self.logs), 1)
        self.assertEqual(self.posts, [])
        self.write_conf({"token": "x", "github_actions_token": GEHEIM})   # bei laufendem Bot eingetragen -> wirkt sofort
        self.assertEqual(asyncio.run(self.m.dispatch()), "ok")

    def test_401_einmal_melden_nicht_wiederholen(self):
        for code in (401, 403, 404):
            with self.subTest(code=code):
                self.m.state.data.pop("ci_anstoss_fehler", None)
                self.posts.clear()
                self.logs.clear()
                self.status = code
                self.assertEqual(asyncio.run(self.m.dispatch()), f"fehler_{code}")
                self.assertEqual(asyncio.run(self.m.dispatch()), "gesperrt")
                self.assertEqual((len(self.posts), len(self.logs)), (1, 1))
                self.assertIn(f"Antwort {code}", self.logs[0])
        self.write_conf({"token": "x", "github_actions_token": GEHEIM + "neu"})   # anderer Token -> wieder versuchen
        self.status = 204
        self.assertEqual(asyncio.run(self.m.dispatch()), "ok")

    def test_500_und_netz_ohne_meldung_naechstes_mal_wieder(self):
        self.status = 502
        self.assertEqual(asyncio.run(self.m.dispatch()), "fehler_502")
        self.assertEqual(asyncio.run(self.m.dispatch()), "fehler_502")
        self.assertEqual((len(self.posts), self.logs), (2, []))

        async def boom(url, token):
            raise OSError("weg")
        self.m._post = boom
        self.assertEqual(asyncio.run(self.m.dispatch()), "netz")
        self.assertNotIn("ci_anstoss_fehler", self.m.state.data)

    def test_token_nie_in_meldungen_oder_state(self):
        self.status = 401
        asyncio.run(self.m.dispatch())
        self.write_conf({"token": "x"})
        self.m._missing_told = False
        asyncio.run(self.m.dispatch())
        for t in self.logs:
            self.assertNotIn(GEHEIM, t)
        self.assertNotIn(GEHEIM, json.dumps(self.m.state.data.get("ci_anstoss_fehler")))
        self.assertEqual(len(self.m.state.data["ci_anstoss_fehler"]["token"]), 12)


class Sperre(Basis):
    def test_fuenf_minuten_zusammenfassen(self):
        self.m.SPERRE = 0.2

        async def lauf():
            r = [await self.m.on_testbericht()]
            r.append(await self.m.on_testbericht())      # in der Sperre -> einmal vormerken
            r.append(await self.m.on_testbericht())      # weitere Pakete: zusammengefasst
            r.append(await self.m.on_testbericht())
            await asyncio.sleep(0.35)
            r.append(await self.m.on_testbericht())      # nach dem vorgemerkten Anstoss: wieder in der Sperre
            await asyncio.sleep(0.35)
            return r
        r = asyncio.run(lauf())
        self.assertEqual(r, ["jetzt", "vorgemerkt", "schon_vorgemerkt", "schon_vorgemerkt", "vorgemerkt"])
        self.assertEqual(len(self.posts), 3)              # 1 sofort + 2 vorgemerkte, nicht 5

    def test_nach_der_sperre_sofort(self):
        self.m.SPERRE = 0.05

        async def lauf():
            a = await self.m.on_testbericht()
            await asyncio.sleep(0.1)
            return a, await self.m.on_testbericht()
        self.assertEqual(asyncio.run(lauf()), ("jetzt", "jetzt"))
        self.assertEqual(len(self.posts), 2)


class Weg(Basis):
    def test_nachricht_in_testberichte_stoesst_an(self):
        b, m = self.b, self.m
        calls = []

        async def fake():
            calls.append(1)
        saved = b.ci_testbericht_safe
        old_tb = b.cfg.get("testberichte_channel_id")
        b.cfg["testberichte_channel_id"] = 4242
        b.ci_testbericht_safe = fake
        try:
            async def lauf():
                msg = types.SimpleNamespace(channel=types.SimpleNamespace(id=4242), webhook_id=None,
                                            author=types.SimpleNamespace(bot=False), type=None)
                await type(b.bot).on_message(b.bot, msg)
                other = types.SimpleNamespace(channel=types.SimpleNamespace(id=1), webhook_id=None,
                                              author=types.SimpleNamespace(bot=True), type=None)
                await type(b.bot).on_message(b.bot, other)
                await asyncio.sleep(0)
            asyncio.run(lauf())
        finally:
            b.ci_testbericht_safe = saved
            if old_tb is None:
                b.cfg.pop("testberichte_channel_id", None)
            else:
                b.cfg["testberichte_channel_id"] = old_tb
        self.assertEqual(calls, [1])

    def test_save_config_behaelt_neue_schluessel(self):
        k = self.kern
        saved_path = k.CONFIG_PATH
        snapshot = dict(k.cfg)
        try:
            k.CONFIG_PATH = self.conf
            self.write_conf({"token": "x", "github_actions_token": GEHEIM, "neu_vom_nutzer": 1})
            k.cfg.pop("github_actions_token", None)
            k.save_config()
            with open(self.conf, encoding="utf-8") as f:
                disk = json.load(f)
            self.assertEqual(disk["github_actions_token"], GEHEIM)
            self.assertEqual(disk["neu_vom_nutzer"], 1)
            self.assertEqual(disk["token"], snapshot["token"])        # vorhandene Werte: wie bisher aus dem Bot
        finally:
            k.CONFIG_PATH = saved_path
            k.cfg.clear()
            k.cfg.update(snapshot)


if __name__ == "__main__":
    unittest.main()
