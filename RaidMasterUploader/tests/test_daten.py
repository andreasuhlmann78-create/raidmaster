"""Offline-Tests Uploader 2.3.0: Addon-Daten für die Prüf-Sitzung in ein privates GitHub-Repo (T-DU1 … T-DU6).
Eine nachgebildete GitHub-API (Git Data) im Speicher, kein Netz.
Start: python3 -I RaidMasterUploader/tests/test_daten.py"""
import base64
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import daten  # noqa: E402
import sync  # noqa: E402

TOKEN = "testtoken-GEHEIM-1234567890"
T0 = 1794380000.0


class Resp:
    def __init__(self, data):
        self.data = json.dumps(data).encode() if data is not None else b""

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeGitHub:
    """Nachbildung von api.github.com für ein Repo: Blobs, Trees, Commits, Refs, Contents (erster Commit)."""

    def __init__(self, repo="ich/goldsentinel-daten", private=True):
        self.repo, self.private, self.online = repo, private, True
        self.blobs, self.trees, self.commits, self.ref = {}, {}, {}, None
        self.calls, self.n = [], 0
        self.token_ok = True

    def _id(self):
        self.n += 1
        return f"{self.n:040x}"

    def err(self, url, code):
        return daten.urllib.error.HTTPError(url, code, "x", {}, io.BytesIO(b"{}"))

    def __call__(self, req, timeout=None):
        url, method = req.full_url, req.get_method()
        self.calls.append((method, url, dict(req.header_items())))
        if not self.online:
            raise daten.urllib.error.URLError("offline")
        if req.get_header("Authorization") != "Bearer " + TOKEN or not self.token_ok:
            raise self.err(url, 401)
        body = json.loads(req.data) if req.data else None
        base = f"https://api.github.com/repos/{self.repo}"
        if not url.startswith(base):
            raise self.err(url, 404)
        path = url[len(base):]
        if path == "" and method == "GET":
            return Resp({"private": self.private, "default_branch": "main"})
        if path == "/git/ref/heads/main":
            if self.ref is None:
                raise self.err(url, 409)
            return Resp({"object": {"sha": self.ref}})
        if path.startswith("/contents/") and method == "PUT":
            data = base64.b64decode(body["content"])
            sha = daten.git_blob_sha(data)
            self.blobs[sha] = data
            tree = self._id()
            self.trees[tree] = {path[len("/contents/"):]: sha}
            c = self._id()
            self.commits[c] = {"tree": tree, "parents": []}
            self.ref = c
            return Resp({"commit": {"sha": c}})
        m = re.match(r"/git/commits/(\w+)$", path)
        if m and method == "GET":
            return Resp({"tree": {"sha": self.commits[m.group(1)]["tree"]}})
        m = re.match(r"/git/trees/(\w+)\?recursive=1$", path)
        if m:
            return Resp({"tree": [{"path": p, "type": "blob", "sha": s, "size": len(self.blobs[s])}
                                  for p, s in self.trees[m.group(1)].items()]})
        if path == "/git/blobs" and method == "POST":
            data = base64.b64decode(body["content"])
            sha = daten.git_blob_sha(data)
            self.blobs[sha] = data
            return Resp({"sha": sha})
        if path == "/git/trees" and method == "POST":
            assert "base_tree" not in body
            for e in body["tree"]:
                assert e["sha"] in self.blobs, e["path"]
            t = self._id()
            self.trees[t] = {e["path"]: e["sha"] for e in body["tree"]}
            return Resp({"sha": t})
        if path == "/git/commits" and method == "POST":
            c = self._id()
            self.commits[c] = {"tree": body["tree"], "parents": body["parents"], "message": body["message"]}
            return Resp({"sha": c})
        if path == "/git/refs/heads/main" and method == "PATCH":
            assert body["force"] is True
            self.ref = body["sha"]
            return Resp({"object": {"sha": self.ref}})
        raise AssertionError((method, path))

    # Sicht der Prüf-Sitzung
    def files(self):
        return {p: self.blobs[s] for p, s in self.trees[self.commits[self.ref]["tree"]].items()}

    def history(self):
        """Commits, die vom Zweig aus erreichbar sind."""
        out, c = [], self.ref
        while c:
            out.append(c)
            ps = self.commits[c]["parents"]
            c = ps[0] if ps else None
        return out

    def commit_count(self):
        return sum(1 for m, u, _ in self.calls if m == "POST" and u.endswith("/git/commits"))


class Lieferung(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.gh = FakeGitHub()
        self.orig = daten.urllib.request.urlopen
        daten.urllib.request.urlopen = self.gh
        self.acc = os.path.join(self.d, "WoW", "_forever_", "WTF", "Account", "123456789#1")
        os.makedirs(os.path.join(self.acc, "SavedVariables"))
        os.makedirs(os.path.join(self.acc, "Realm", "Figur", "SavedVariables"))
        self.logs, self.st = [], {}
        self.dl = self.make()

    def make(self, repo="ich/goldsentinel-daten"):
        return daten.Daten(daten.GitHubAPI(repo, TOKEN), {"_forever_/123456789#1": self.acc}, self.st,
                           lambda: None, "PC", self.logs.append)

    def tearDown(self):
        daten.urllib.request.urlopen = self.orig
        shutil.rmtree(self.d, ignore_errors=True)

    def write(self, name, text, mtime, char=False):
        sub = ("Realm", "Figur", "SavedVariables") if char else ("SavedVariables",)
        fn = os.path.join(self.acc, *sub, name)
        with open(fn, "w", encoding="utf-8") as f:
            f.write(text)
        os.utime(fn, (mtime, mtime))
        return fn

    def run_until(self, start, end, step=5):
        for t in range(int(start), int(end), step):
            self.dl.tick(now=t)

    def test_du1_geaendert_ein_commit_unveraendert_keiner(self):
        self.write("AHSentinel.lua", "AHSentinelDB = { 1 }\n", T0)
        self.write("RaidMaster.lua", "RaidMasterDB = {}\n", T0)
        self.write("FremdesAddon.lua", "X = 1\n", T0)                         # kein GoldSentinel-Addon
        self.write("AHSentinel.lua.bak", "alt\n", T0)
        self.write("AHSentinel.lua", "AHSentinelDB = { pro_figur }\n", T0, char=True)
        self.run_until(T0 + 1, T0 + 20)
        files = self.gh.files()
        self.assertEqual(files["aktuell/forever/konto1/AHSentinel.lua"], b"AHSentinelDB = { 1 }\n")
        self.assertIn("aktuell/forever/konto1/RaidMaster.lua", files)
        self.assertFalse(any("Fremdes" in p or ".bak" in p or "Figur" in p or "123456789" in p for p in files))
        self.assertEqual(self.gh.commit_count(), 1)
        msg = self.gh.commits[self.gh.ref]["message"]
        self.assertIn("PC", msg)
        stand = json.loads(files["stand.json"])
        self.assertEqual(stand["rechner"], "PC")
        posted = [u for m, u, _ in self.gh.calls if m == "POST" and u.endswith("/git/blobs")]
        self.assertGreaterEqual(len(posted), 2)
        # unverändert: kein Commit, kein Netz
        n = len(self.gh.calls)
        self.run_until(T0 + 100, T0 + 300)
        self.assertEqual(len(self.gh.calls), n)
        # /reload mit gleichem Inhalt (neue Zeit): kein Commit
        self.write("AHSentinel.lua", "AHSentinelDB = { 1 }\n", T0 + 400)
        self.run_until(T0 + 401, T0 + 430)
        self.assertEqual(self.gh.commit_count(), 1)
        self.assertIn("Prüfung: zuletzt geliefert", self.dl.status_line())
        self.assertIn("(2 Dateien)", self.dl.status_line())

    def test_du2_token_nie_im_log_oeffentlich_verweigert(self):
        self.write("AHSentinel.lua", "AHSentinelDB = { 1 }\n", T0)
        self.gh.private = False
        self.run_until(T0 + 1, T0 + 20)
        self.assertIsNone(self.gh.ref)
        self.assertEqual(self.gh.commit_count(), 0)
        self.assertTrue(any("nicht privat" in l for l in self.logs))
        self.assertIn("FEHLER", self.dl.status_line())
        # falscher Token: klare Meldung, Token nirgends
        self.gh.private, self.gh.token_ok = True, False
        self.write("AHSentinel.lua", "AHSentinelDB = { 2 }\n", T0 + 100)
        self.run_until(T0 + 101, T0 + 200)
        self.assertTrue(any("Token falsch" in l for l in self.logs))
        text = "\n".join(self.logs + [self.dl.status_line(), json.dumps(self.st)])
        self.assertNotIn(TOKEN, text)
        self.assertNotIn("GEHEIM", text)
        # Token nur im Kopf der Anfrage, nie in einer Adresse
        self.assertFalse(any(TOKEN in u for _, u, _ in self.gh.calls))
        # daten_config.json ist in .gitignore
        with open(os.path.join(os.path.dirname(HERE), ".gitignore"), encoding="utf-8") as f:
            self.assertIn("RaidMasterUploader/daten_config.json", f.read())
        # Einrichtung verweigert ein öffentliches Repo
        self.gh.token_ok, self.gh.private = True, False
        out = []
        ok = daten.setup_interactive(self.d, ask=lambda q: "ich/goldsentinel-daten", ask_secret=lambda q: TOKEN,
                                     log=out.append)
        self.assertFalse(ok)
        self.assertFalse(os.path.exists(os.path.join(self.d, daten.DATEN_CONFIG)))
        self.gh.private = True
        self.assertTrue(daten.setup_interactive(self.d, ask=lambda q: "ich/goldsentinel-daten",
                                                ask_secret=lambda q: TOKEN, log=out.append))
        self.assertEqual(daten.load_config(self.d)["repo"], "ich/goldsentinel-daten")
        self.assertNotIn(TOKEN, "\n".join(out))

    def test_du3_ueber_50_mb_uebersprungen(self):
        self.write("AHSentinel.lua", "AHSentinelDB = { 1 }\n", T0)
        big = self.write("GuildSentinel.lua", "x", T0)
        with open(big, "wb") as f:
            f.truncate(daten.MAX_FILE + 1)
        os.utime(big, (T0, T0))
        self.run_until(T0 + 1, T0 + 20)
        files = self.gh.files()
        self.assertIn("aktuell/forever/konto1/AHSentinel.lua", files)
        self.assertNotIn("aktuell/forever/konto1/GuildSentinel.lua", files)
        self.assertEqual(sum("GuildSentinel.lua ist" in l and "übersprungen" in l for l in self.logs), 1)

    def test_du4_kein_netz_kein_absturz_abgleich_unabhaengig(self):
        self.write("AHSentinel.lua", "AHSentinelDB = { 1 }\n", T0)
        self.gh.online = False
        self.run_until(T0 + 1, T0 + 20)
        self.assertTrue(any("kein Netz" in l for l in self.logs))
        self.assertIn("FEHLER: kein Netz", self.dl.status_line())
        # nächste Änderung = nächster Versuch
        self.gh.online = True
        self.write("AHSentinel.lua", "AHSentinelDB = { 2 }\n", T0 + 100)
        self.run_until(T0 + 101, T0 + 130)
        self.assertEqual(self.gh.files()["aktuell/forever/konto1/AHSentinel.lua"], b"AHSentinelDB = { 2 }\n")
        self.assertNotIn("FEHLER", self.dl.status_line())
        # Abgleich PC/Laptop nutzt einen eigenen Weg (Discord-Webhook) – die Lieferung fasst ihn nie an
        import uploader
        with open(uploader.__file__, encoding="utf-8") as f:
            src = f.read()
        loop = src[src.index("# Daten für die Prüf-Sitzung (ab 2.3.0)"):]
        self.assertIn("except Exception", loop.split("time.sleep")[0])
        with open(sync.__file__, encoding="utf-8") as f:
            self.assertNotIn("import daten", f.read())

    def test_du5_jeder_reload_hoechstens_1_je_minute(self):
        self.write("AHSentinel.lua", "AHSentinelDB = { 1 }\n", T0)
        self.run_until(T0 + 1, T0 + 20)
        self.assertEqual(self.gh.commit_count(), 1)
        # zwei /reload im Abstand von 2 Min. -> zwei Commits
        self.write("AHSentinel.lua", "AHSentinelDB = { 2 }\n", T0 + 120)
        self.run_until(T0 + 121, T0 + 140)
        self.write("AHSentinel.lua", "AHSentinelDB = { 3 }\n", T0 + 240)
        self.run_until(T0 + 241, T0 + 260)
        self.assertEqual(self.gh.commit_count(), 3)
        # vor dem stabilen Schreiben (10 s) nichts
        self.write("AHSentinel.lua", "AHSentinelDB = { 4 }\n", T0 + 400)
        self.run_until(T0 + 401, T0 + 406)
        self.assertEqual(self.gh.commit_count(), 3)
        # zwei /reload innerhalb einer Minute -> ein Commit je Minute, die letzte gewinnt
        self.run_until(T0 + 406, T0 + 415)
        self.write("AHSentinel.lua", "AHSentinelDB = { 5 }\n", T0 + 420)
        self.run_until(T0 + 421, T0 + 470)
        self.assertEqual(self.gh.commit_count(), 4)
        self.run_until(T0 + 470, T0 + 500)
        self.assertEqual(self.gh.commit_count(), 5)
        self.assertEqual(self.gh.files()["aktuell/forever/konto1/AHSentinel.lua"], b"AHSentinelDB = { 5 }\n")
        # /reload ohne Änderung -> kein Commit
        self.write("AHSentinel.lua", "AHSentinelDB = { 5 }\n", T0 + 600)
        self.run_until(T0 + 601, T0 + 700)
        self.assertEqual(self.gh.commit_count(), 5)

    def test_du6_nur_neuester_und_7_tage_ohne_verlauf(self):
        # 20 Läufe über 9 Tage
        t = T0
        for i in range(20):
            day = i * 9 // 20
            now = T0 + day * 86400 + (i % 3) * 3600
            self.write("AHSentinel.lua", f"AHSentinelDB = {{ {i} }}\n", now)
            self.run_until(now + 1, now + 20)
            t = now
        files = self.gh.files()
        days = sorted({p.split("/")[1] for p in files if p.startswith("tage/")})
        self.assertEqual(len(days), daten.DAYS_KEEP)
        self.assertEqual(files["aktuell/forever/konto1/AHSentinel.lua"], b"AHSentinelDB = { 19 }\n")
        last_day = days[-1]
        self.assertEqual(files[f"tage/{last_day}/forever/konto1/AHSentinel.lua"], b"AHSentinelDB = { 19 }\n")
        self.assertEqual(self.gh.history(), [self.gh.ref])                  # ein Commit, kein Verlauf
        self.assertEqual(self.gh.commits[self.gh.ref]["parents"], [])
        self.assertIn("Repo ", self.dl.status_line())
        # über 200 MB: älteste Tages-Stände früher löschen
        old_max = daten.REPO_MAX
        daten.REPO_MAX = 3 * 40
        try:
            self.write("AHSentinel.lua", "AHSentinelDB = { 'gross' }\n" + "-- " * 10, t + 86400)
            self.run_until(t + 86401, t + 86420)
        finally:
            daten.REPO_MAX = old_max
        self.assertTrue(any("ältere Tages-Stände gelöscht" in l for l in self.logs))
        days = sorted({p.split("/")[1] for p in self.gh.files() if p.startswith("tage/")})
        self.assertLess(len(days), daten.DAYS_KEEP)


if __name__ == "__main__":
    unittest.main()
