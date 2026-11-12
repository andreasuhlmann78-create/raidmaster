"""Offline-Tests Uploader 2.3.0/2.3.1: Addon-Daten für die Prüf-Sitzung in ein privates GitHub-Repo (T-DU1 … T-DU10).
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

TOKEN = "github_pat_TESTGEHEIM_1234567890abc"
KONTO = daten.konto_id("123456789#1")
AKT = "aktuell/PC/forever/" + KONTO + "/"
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
        self.fail, self.contexts, self.before_patch = None, [], None

    def _id(self):
        self.n += 1
        return f"{self.n:040x}"

    def err(self, url, code):
        return daten.urllib.error.HTTPError(url, code, "x", {}, io.BytesIO(b"{}"))

    def __call__(self, req, timeout=None, context=None):
        url, method = req.full_url, req.get_method()
        self.calls.append((method, url, dict(req.header_items())))
        self.contexts.append(context)
        if self.fail is not None:
            raise self.fail
        if not self.online:
            raise daten.urllib.error.URLError(daten.socket.gaierror(11001, "getaddrinfo failed"))
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
        m = re.match(r"/git/blobs/(\w+)$", path)
        if m and method == "GET":
            return Resp({"content": base64.b64encode(self.blobs[m.group(1)]).decode(), "encoding": "base64"})
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
            if self.before_patch:
                f, self.before_patch = self.before_patch, None
                f()
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
        self.assertEqual(files[AKT + "AHSentinel.lua"], b"AHSentinelDB = { 1 }\n")
        self.assertIn(AKT + "RaidMaster.lua", files)
        self.assertFalse(any("Fremdes" in p or ".bak" in p or "Figur" in p or "123456789" in p for p in files))
        self.assertTrue(all(c is not None for c in self.gh.contexts))          # immer mit Zertifikats-Kontext
        self.assertEqual(self.gh.commit_count(), 1)
        msg = self.gh.commits[self.gh.ref]["message"]
        self.assertIn("PC", msg)
        stand = json.loads(files["stand.json"])
        self.assertIn("PC", stand)
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
        self.assertIn(AKT + "AHSentinel.lua", files)
        self.assertNotIn(AKT + "GuildSentinel.lua", files)
        self.assertEqual(sum("GuildSentinel.lua ist" in l and "übersprungen" in l for l in self.logs), 1)

    def test_du4_kein_netz_kein_absturz_abgleich_unabhaengig(self):
        self.write("AHSentinel.lua", "AHSentinelDB = { 1 }\n", T0)
        self.gh.online = False
        self.run_until(T0 + 1, T0 + 20)
        self.assertTrue(any("nicht auflösbar" in l for l in self.logs))
        self.assertIn("FEHLER: api.github.com nicht auflösbar", self.dl.status_line())
        # nächste Änderung = nächster Versuch
        self.gh.online = True
        self.write("AHSentinel.lua", "AHSentinelDB = { 2 }\n", T0 + 100)
        self.run_until(T0 + 101, T0 + 130)
        self.assertEqual(self.gh.files()[AKT + "AHSentinel.lua"], b"AHSentinelDB = { 2 }\n")
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
        self.assertEqual(self.gh.files()[AKT + "AHSentinel.lua"], b"AHSentinelDB = { 5 }\n")
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
        self.assertEqual(files[AKT + "AHSentinel.lua"], b"AHSentinelDB = { 19 }\n")
        last_day = days[-1]
        self.assertEqual(files[f"tage/{last_day}/PC/forever/{KONTO}/AHSentinel.lua"], b"AHSentinelDB = { 19 }\n")
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


class Einrichten(unittest.TestCase):
    """2.3.1: T-DU7 (Token mit Strg+V), T-DU8 (daten_config.json mit BOM), T-DU9 (echte Ursache, Zertifikate)."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.gh = FakeGitHub()
        self.orig = daten.urllib.request.urlopen
        daten.urllib.request.urlopen = self.gh

    def tearDown(self):
        daten.urllib.request.urlopen = self.orig
        shutil.rmtree(self.d, ignore_errors=True)

    def test_du7_token_mit_strg_v(self):
        out = []
        ok = daten.setup_interactive(self.d, ask=lambda q: "ich/goldsentinel-daten", ask_secret=lambda q: "\x16",
                                     log=out.append)
        self.assertFalse(ok)
        text = "\n".join(out)
        self.assertIn("ungültige Zeichen", text)
        self.assertIn("RECHTSKLICK", text)
        self.assertNotIn("kein Netz", text)
        self.assertEqual(self.gh.calls, [])                                     # gar nicht erst gesendet
        for bad in ("ghp_abc def", "abc123", "github_pat_ä"):
            self.assertIsNotNone(daten.token_problem(bad))
        self.assertIsNone(daten.token_problem(TOKEN))
        # auch der Uploader sendet einen kaputten Token nie
        with self.assertRaises(daten.GitHubError) as cm:
            daten.GitHubAPI("ich/goldsentinel-daten", "github_pat_x\x16").repo_info()
        self.assertIn("ungültige Zeichen", str(cm.exception))
        # ValueError aus http.client (ungültiger Kopf) wird nicht als "kein Netz" gemeldet
        self.assertIn("ungültige Zeichen", daten.describe_error(ValueError("Invalid header value b'Bearer x'")))
        # die Abfrage nennt Rechtsklick
        asked = []
        daten.setup_interactive(self.d, ask=lambda q: "ich/goldsentinel-daten",
                                ask_secret=lambda q: asked.append(q) or "", log=lambda t: None)
        self.assertIn("Rechtsklick", asked[0])

    def test_du8_config_mit_bom_und_gruende(self):
        path = os.path.join(self.d, daten.DATEN_CONFIG)

        def put(raw):
            with open(path, "wb") as f:
                f.write(raw)
        put(b"\xef\xbb\xbf" + json.dumps({"repo": "ich/goldsentinel-daten", "token": TOKEN}).encode())
        self.assertEqual(daten.load_config(self.d)["repo"], "ich/goldsentinel-daten")
        put(('{\n  \u201erepo\u201c: \u201eich/goldsentinel-daten\u201c,\n  \u201etoken\u201c: \u201c' + TOKEN +
             '\u201d\n}').encode("utf-8"))                                    # typografische Anführungszeichen
        self.assertEqual(daten.load_config(self.d)["token"], TOKEN)
        cases = [(json.dumps({"repo": "ich/goldsentinel-daten"}).encode(), "token fehlt"),
                 (json.dumps({"token": TOKEN}).encode(), "repo fehlt"),
                 (json.dumps({"repo": "goldsentinel-daten", "token": TOKEN}).encode(), "repo falsch"),
                 (b'{"repo": "ich/x",\n "token": ', "Zeile 2"),
                 (json.dumps({"repo": "ich/x", "token": "github_pat_a\u0016"}).encode(), "ungültige Zeichen")]
        for raw, want in cases:
            put(raw)
            conf, why = daten.read_config(self.d)
            self.assertIsNone(conf)
            self.assertIn(want, why)
            self.assertNotIn("TESTGEHEIM", why)
        os.remove(path)
        self.assertEqual(daten.read_config(self.d), (None, None))               # fehlt: freiwillig, kein Fehler
        import uploader
        with open(uploader.__file__, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("daten.read_config(HERE)", src[src.index("def make_daten"):])

    def test_du9_echte_ursache_und_zertifikate(self):
        import ssl as _ssl
        cert = daten.urllib.error.URLError(_ssl.SSLCertVerificationError(
            1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate"))
        cases = [(cert, "Zertifikat für GitHub fehlt"),
                 (daten.urllib.error.URLError(daten.socket.gaierror(11001, "getaddrinfo failed")), "nicht auflösbar"),
                 (daten.urllib.error.URLError(daten.socket.timeout("timed out")), "Zeitüberschreitung"),
                 (daten.urllib.error.URLError(ConnectionRefusedError(10061, "refused")), "abgelehnt"),
                 (ConnectionResetError(10054, "reset"), "abgebrochen"),
                 (ValueError("Invalid header value"), "ungültige Zeichen"),
                 (daten.urllib.error.URLError(OSError("Tunnel connection failed: 407")), "Netzfehler: OSError")]
        api = daten.GitHubAPI("ich/goldsentinel-daten", TOKEN)
        seen = set()
        for exc, want in cases:
            self.gh.fail = exc
            with self.assertRaises(daten.GitHubError) as cm:
                api.repo_info()
            msg = str(cm.exception)
            self.assertIn(want, msg)
            self.assertNotIn(TOKEN, msg)
            self.assertNotIn("kein Netz oder GitHub nicht erreichbar", msg)
            seen.add(msg)
        self.assertEqual(len(seen), len(cases))                                 # jede Art eigene Meldung
        self.assertIn("certifi", describe := daten.describe_error(cert))        # noqa: F841
        # Zertifikats-Kontext: Windows-/System-Ablage plus certifi, Prüfung an
        ctx = daten.ssl_context()
        self.assertEqual(ctx.verify_mode, _ssl.CERT_REQUIRED)
        self.assertTrue(ctx.check_hostname)
        # certifi fehlt -> einmal selbst installieren (gleiches Python), mit Hinweis
        calls, logs = [], []
        orig_cf = daten.certifi_file
        daten.certifi_file = lambda: None
        daten._CERTIFI_TRIED["done"] = False
        try:
            res = daten.ensure_certifi(logs.append, run=lambda cmd, **kw: calls.append(cmd) or
                                       type("R", (), {"returncode": 1})(), background=False)
            self.assertFalse(res)
            self.assertEqual(calls[0][1:5], ["-m", "pip", "install", "--user"])
            self.assertEqual(calls[0][-1], "certifi")
            self.assertTrue(any("installiere" in l for l in logs))
            self.assertTrue(any("py -m pip install certifi" in l for l in logs))
            self.assertIsNone(daten.ensure_certifi(logs.append, run=lambda *a, **k: 1 / 0, background=False) or None)
            self.assertEqual(len(calls), 1)                                     # nur einmal je Lauf
        finally:
            daten.certifi_file = orig_cf
            daten._CERTIFI_TRIED["done"] = False
        # Startdateien rufen zuerst py auf (keine Store-Alias-Zeile)
        for bat in ("uploader.bat", "GoldSentinel-WoW.bat", "Daten-Repo-einrichten.bat", "Daten-Verbindung-testen.bat"):
            with open(os.path.join(HERE, bat), encoding="utf-8") as f:
                text = f.read()
            self.assertLess(text.index("where py"), text.index("python uploader.py"), bat)
        # Verbindung testen
        self.gh.fail = None
        out = []
        self.assertTrue(daten.test_connection({"repo": "ich/goldsentinel-daten", "token": TOKEN}, out.append))
        self.assertIn("OK", out[0])


class ZweiRechner(unittest.TestCase):
    """2.3.1: T-DU10 – PC und Laptop liefern ins selbe Repo, keiner löscht den Stand des anderen."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.gh = FakeGitHub()
        self.orig = daten.urllib.request.urlopen
        daten.urllib.request.urlopen = self.gh

    def tearDown(self):
        daten.urllib.request.urlopen = self.orig
        shutil.rmtree(self.d, ignore_errors=True)

    def machine(self, name, konten):
        roots = {}
        for i, k in enumerate(konten):
            acc = os.path.join(self.d, name, "_forever_", "WTF", "Account", k)
            os.makedirs(os.path.join(acc, "SavedVariables"))
            roots["_forever_/" + k] = acc
        return daten.Daten(daten.GitHubAPI("ich/goldsentinel-daten", TOKEN), roots, {}, lambda: None, name,
                           lambda t: None), roots

    @staticmethod
    def put(acc, name, text, mtime):
        fn = os.path.join(acc, "SavedVariables", name)
        with open(fn, "w", encoding="utf-8") as f:
            f.write(text)
        os.utime(fn, (mtime, mtime))

    @staticmethod
    def drive(dl, a, b):
        for t in range(int(a), int(b), 5):
            dl.tick(now=t)

    def test_du10_zwei_rechner(self):
        pc, pr = self.machine("PC", ["ANDERES", "123456789#1"])                   # andere Reihenfolge der Konten
        lap, lr = self.machine("Laptop", ["123456789#1"])
        self.put(pr["_forever_/123456789#1"], "AHSentinel.lua", "AHSentinelDB = { 'pc' }\n", T0)
        self.put(lr["_forever_/123456789#1"], "AHSentinel.lua", "AHSentinelDB = { 'laptop' }\n", T0 + 1000)
        self.drive(lap, T0 + 1, T0 + 20)                                          # Laptop morgens
        self.drive(pc, T0 + 3600, T0 + 3620)                                      # PC am selben Tag später
        files = self.gh.files()
        k = daten.konto_id("123456789#1")
        self.assertEqual(files[f"aktuell/PC/forever/{k}/AHSentinel.lua"], b"AHSentinelDB = { 'pc' }\n")
        self.assertEqual(files[f"aktuell/Laptop/forever/{k}/AHSentinel.lua"], b"AHSentinelDB = { 'laptop' }\n")
        day = [p for p in files if p.startswith("tage/")]
        self.assertTrue(any(f"/Laptop/forever/{k}/" in p for p in day))      # Tages-Stand des Laptops bleibt
        self.assertTrue(any(f"/PC/forever/{k}/" in p for p in day))
        self.assertFalse(any("123456789" in p or "ANDERES" in p for p in files))
        stand = json.loads(files["stand.json"])
        self.assertEqual(sorted(stand), ["Laptop", "PC"])
        self.assertEqual(self.gh.history(), [self.gh.ref])
        # Form von 2.3.0 (aktuell/forever/konto1/…) verschwindet beim nächsten Liefern
        # gleichzeitige Lieferung: der Laptop liefert zwischen Lesen und Ersetzen -> PC bezieht ihn ein
        self.put(pr["_forever_/123456789#1"], "AHSentinel.lua", "AHSentinelDB = { 'pc2' }\n", T0 + 7200)

        def other():
            self.put(lr["_forever_/123456789#1"], "AHSentinel.lua", "AHSentinelDB = { 'laptop2' }\n", T0 + 7201)
            self.drive(lap, T0 + 7202, T0 + 7230)
        self.drive(pc, T0 + 7201, T0 + 7205)
        self.gh.before_patch = None
        orig_head = pc.api.head
        state = {"n": 0}

        def head(branch):
            state["n"] += 1
            if state["n"] == 2:
                other()                                                         # zwischen Lesen und Ersetzen
            return orig_head(branch)
        pc.api.head = head
        self.drive(pc, T0 + 7212, T0 + 7230)
        files = self.gh.files()
        self.assertEqual(files[f"aktuell/PC/forever/{k}/AHSentinel.lua"], b"AHSentinelDB = { 'pc2' }\n")
        self.assertEqual(files[f"aktuell/Laptop/forever/{k}/AHSentinel.lua"], b"AHSentinelDB = { 'laptop2' }\n")


if __name__ == "__main__":
    unittest.main()
