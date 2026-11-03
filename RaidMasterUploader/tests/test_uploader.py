"""Offline-Tests für den RaidMaster-Uploader (1.7.0 / 1.8.0). Keine Verbindung nach aussen: urlopen ist nachgebaut.
Start: python3 -I RaidMasterUploader/tests/test_uploader.py"""
import gzip
import io
import json
import os
import re
import sys
import tempfile
import time
import unittest
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "addon-check"))
sys.path.insert(0, os.path.join(REPO, "RaidMasterBot"))
import uploader as up  # noqa: E402
import testberichte  # noqa: E402
import raidmaster_data as rmd  # noqa: E402


def lua_str(s: str) -> str:
    """Python-Text wie WoW als Lua-String schreiben (\\ " \\n und Bytes >= 128 als \\ddd)."""
    out = []
    for b in s.encode("utf-8"):
        c = chr(b)
        if c == "\\":
            out.append("\\\\")
        elif c == '"':
            out.append('\\"')
        elif c == "\n":
            out.append("\\n")
        elif b >= 128:
            out.append("\\%d" % b)
        else:
            out.append(c)
    return '"' + "".join(out) + '"'


def report(rid, addon="RaidMaster", kind="test", extra=""):
    return {"f": 1, "kind": kind, "id": rid, "addon": addon, "text": "Bericht " + rid + extra}


def sv_with(var, reports, junk=()):
    lines = [f"{var} = {{", '\t["gsTest"] = {', '\t\t["reports"] = {']
    for r in reports:
        lines.append("\t\t\t" + lua_str("GSTEST1" + json.dumps(r, ensure_ascii=False)) + ",")
    for j in junk:
        lines.append("\t\t\t" + lua_str(j) + ",")
    lines += ["\t\t},", "\t},", "}"]
    return "\n".join(lines) + "\n"


class FakeResp:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def read(self):
        return b"{}"


class Net:
    """Nachgebautes urlopen: Antworten der Reihe nach (204 = ok, Zahl = HTTPError, "conn" = URLError)."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def __call__(self, req, timeout=0):
        self.calls.append(req)
        a = self.answers.pop(0) if self.answers else 204
        if a == 204:
            return FakeResp()
        if a == "conn":
            raise urllib.error.URLError("keine Verbindung")
        body = io.BytesIO(json.dumps({"retry_after": 1}).encode()) if a == 429 else io.BytesIO(b"{}")
        raise urllib.error.HTTPError(req.full_url, a, "x", {}, body)


def attachment(body: bytes, name: str) -> bytes:
    part = body.split(f'filename="{name}"'.encode(), 1)[1]
    part = part.split(b"\r\n\r\n", 1)[1]
    return part.rsplit(b"\r\n--", 1)[0]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.sv = os.path.join(self.d, "WTF", "Account", "A", "SavedVariables")
        os.makedirs(self.sv)
        up.CONFIG = os.path.join(self.d, "uploader_config.json")
        self.logs = []
        up.log = self.logs.append
        self.orig_urlopen = up.urllib.request.urlopen

    def tearDown(self):
        up.urllib.request.urlopen = self.orig_urlopen
        self.tmp.cleanup()

    def write(self, name, text, age=10, folder=None):
        p = os.path.join(folder or self.sv, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        t = time.time() - age
        os.utime(p, (t, t))
        return p

    def cfg(self, **kw):
        c = {"webhook_url": "https://discord.invalid/data", "test_webhook_url": "https://discord.invalid/test",
             "bot_id": 42, "savedvariables_path": "x", "check_seconds": 10}
        c.update(kw)
        return c


# --- 1.7.0: Forever-Ordner, GuildSentinel, Anhänge -----------------------------------------------------------
class Uploader17(Base):
    def test_wechsel_in_forever_ordner(self):
        now = time.time()
        ann = self.write("RaidMaster.lua", "RaidMasterDB = {}", 86400, os.path.join(self.d, "_anniversary_/SV"))
        fov = self.write("RaidMaster.lua", "RaidMasterDB = {}", 10, os.path.join(self.d, "_forever_/SV"))
        cfg = {"savedvariables_path": ann}
        new = up.switch_if_newer(cfg, ann, sorted([ann, fov], key=os.path.getmtime, reverse=True))
        self.assertEqual(os.path.normpath(new), os.path.normpath(fov))
        self.assertTrue(any(l.startswith("Wechsle zu:") for l in self.logs))
        os.utime(ann, (now - 20, now - 20))
        self.assertEqual(up.switch_if_newer({}, ann, [fov, ann]), ann)      # nicht deutlich neuer
        self.assertEqual(up.switch_if_newer({}, fov, [fov, ann]), fov)      # gleiche Datei

    def test_guildsentinel_nur_mit_bank(self):
        rm = self.write("RaidMaster.lua", "RaidMasterDB = {}")
        gs = os.path.join(self.sv, "GuildSentinel.lua")
        self.assertEqual(os.path.normpath(up.guildsentinel_path({}, rm)), os.path.normpath(gs))
        self.assertIsNone(up.read_guildsentinel(gs))
        self.write("GuildSentinel.lua", 'GuildSentinelDB = {\n["members"] = {},\n}')
        self.assertIsNone(up.read_guildsentinel(gs))
        self.write("GuildSentinel.lua", 'GuildSentinelDB = {\n["bank"] = {\n["c"] = "B", ["t"] = 5, ["i"] = {},\n},\n}')
        self.assertIsNotNone(up.read_guildsentinel(gs))

    def test_anhaenge_reihenfolge_und_bot(self):
        b, body = up.build_body({"content": "x"}, gzip.compress(b"R"), gzip.compress(b"G"), [("shot_1_2.jpg", "image/jpeg", b"J")])
        names = [n.decode() for n in re.findall(rb'filename="([^"]+)"', body)]
        self.assertEqual(names, ["RaidMaster.lua.gz", "GuildSentinel.lua.gz", "shot_1_2.jpg"])
        self.assertEqual(rmd.pick_upload_files(names), (0, 1))


# --- 1.8.0: Testberichte ---------------------------------------------------------------------------------
class TestReports(Base):
    def test_u01_findet_berichte_in_allen_lua(self):
        self.write("RaidMaster.lua", sv_with("RaidMasterDB", [report("rm-1")], junk=["kein Präfix"]))
        self.write("ThreatSentinel.lua", sv_with("ThreatSentinelDB", [report("ts-1", "ThreatSentinel")]))
        self.write("BuffSentinel.lua", sv_with("BuffSentinelDB", [report("bs-1", "BuffSentinel")]))
        self.write("RaidMaster.lua.bak", sv_with("RaidMasterDB", [report("bak-1")]))
        self.write("RaidMaster.lua", sv_with("RaidMasterDB", [report("fremd-1")]), folder=os.path.join(self.d, "anders"))
        ids = sorted(r["id"] for r in up.TestReportScanner(self.sv).scan(self.cfg()))
        self.assertEqual(ids, ["bs-1", "rm-1", "ts-1"])

    def test_u02_escapes_wie_testberichte(self):
        vectors = [r'a\"b', r'x\\y', r'z\nq', 'zeile\\\nzwei', r'\195\164\195\182', r'\9tab\13', r'Ende\\']
        for v in vectors:
            self.assertEqual(up.lua_unescape(v), testberichte.lua_unescape(v), v)
        self.assertEqual(up.lua_unescape(r'\195\164'), "ä")
        rep = report("u-1", extra=' mit "Zitat", Backslash \\ und Zeile\nzwei, Umlaut äöü')
        text = sv_with("RaidMasterDB", [rep])
        self.assertEqual(up.reports_in_text(text), [rep])
        self.assertEqual([r["id"] for r in testberichte.from_text(text)], ["u-1"])

    def test_u03_kaputter_bericht_uebersprungen(self):
        text = sv_with("RaidMasterDB", [report("ok-1"), report("ok-2")], junk=['GSTEST1{"f":1,"id":"kaputt"'])
        self.write("RaidMaster.lua", text)
        ids = [r["id"] for r in up.TestReportScanner(self.sv).scan(self.cfg())]
        self.assertEqual(sorted(ids), ["ok-1", "ok-2"])
        self.assertTrue(any("nicht lesbar" in l for l in self.logs))

    def test_u04_doppelte_ids(self):
        self.write("RaidMaster.lua", sv_with("RaidMasterDB", [report("d-1"), report("d-1"), report("d-2")]))
        self.write("ThreatSentinel.lua", sv_with("ThreatSentinelDB", [report("d-1")]))
        cfg = self.cfg(sent_test_ids=["d-2"])
        self.assertEqual([r["id"] for r in up.TestReportScanner(self.sv).scan(cfg)], ["d-1"])

    def test_u05_sent_ids_begrenzt_andere_schluessel_bleiben(self):
        up.urllib.request.urlopen = Net(204)
        cfg = self.cfg(sent_test_ids=[f"alt-{i}" for i in range(499)], sent_shots=["s1"], savedvariables_path="P")
        self.assertTrue(up.send_reports(cfg, [report("n-1"), report("n-2")]))
        saved = json.load(open(up.CONFIG, encoding="utf-8"))
        self.assertEqual(len(saved["sent_test_ids"]), 500)
        self.assertEqual(saved["sent_test_ids"][-2:], ["n-1", "n-2"])
        self.assertNotIn("alt-0", saved["sent_test_ids"])
        for k in ("webhook_url", "bot_id", "savedvariables_path", "sent_shots", "test_webhook_url"):
            self.assertEqual(saved[k], cfg[k])

    def test_u06_nachricht(self):
        net = Net(204)
        up.urllib.request.urlopen = net
        self.assertTrue(up.send_reports(self.cfg(), [report("a"), report("b"), report("c")]))
        req = net.calls[0]
        self.assertTrue(req.full_url.startswith("https://discord.invalid/test"))
        payload = json.loads(req.data.split(b"\r\n\r\n", 1)[1].split(b"\r\n--", 1)[0])
        self.assertEqual(payload["content"], "GoldSentinel-Testberichte: 3 neu")
        self.assertEqual(payload["username"], "GoldSentinel-Testberichte")
        self.assertEqual(payload["allowed_mentions"], {"parse": []})
        data = json.loads(gzip.decompress(attachment(req.data, "testberichte.json.gz")))
        self.assertEqual([r["id"] for r in data], ["a", "b", "c"])

    def test_u07_aufteilen(self):
        net = Net()
        up.urllib.request.urlopen = net
        big = "x" * (1024 * 1024 + 300 * 1024)               # ca. 1,3 MB je Bericht
        reps = [report(f"g-{i}", extra=big) for i in range(5)]
        reps.append(report("zu-gross", extra="y" * (5 * 1024 * 1024)))
        self.assertTrue(up.send_reports(self.cfg(), reps))
        self.assertGreaterEqual(len(net.calls), 2)
        ids = []
        for req in net.calls:
            packed = attachment(req.data, "testberichte.json.gz")
            raw = gzip.decompress(packed)
            self.assertLessEqual(len(raw), up.TEST_MAX_JSON)
            self.assertLess(len(packed), 5 * 1024 * 1024)
            ids += [r["id"] for r in json.loads(raw)]
        self.assertEqual(ids, [f"g-{i}" for i in range(5)])
        self.assertTrue(any("zu gross" in l for l in self.logs))

    def test_u08_http(self):
        sleeps = []
        cfg = self.cfg()
        up.urllib.request.urlopen = Net(204)
        self.assertTrue(up.send_reports(cfg, [report("h-1")], sleeps.append))
        up.urllib.request.urlopen = Net(429, 204)
        self.assertTrue(up.send_reports(cfg, [report("h-2")], sleeps.append))
        self.assertEqual(len(sleeps), 1)
        for answer in (500, "conn", 404):
            up.urllib.request.urlopen = Net(answer)
            self.assertFalse(up.send_reports(cfg, [report(f"h-{answer}")], sleeps.append))
        self.assertEqual(cfg["sent_test_ids"], ["h-1", "h-2"])
        self.assertTrue(any("ungültig" in l for l in self.logs))
        # nächster Durchgang schickt die nicht gemerkten erneut
        up.urllib.request.urlopen = Net(204)
        self.assertTrue(up.send_reports(cfg, [report("h-500")], sleeps.append))
        self.assertIn("h-500", cfg["sent_test_ids"])

    def test_u09_alte_konfiguration(self):
        cfg = self.cfg()
        del cfg["test_webhook_url"]
        net = Net()
        up.urllib.request.urlopen = net
        self.assertFalse(up.send_reports(cfg, [report("o-1")]))
        self.assertEqual(net.calls, [])
        rm = self.write("RaidMaster.lua", "RaidMasterDB = {}")
        self.assertTrue(up.upload(cfg, rm))                  # Daten-Upload wie bisher
        self.assertEqual(len(net.calls), 1)

    def test_u10_nur_threatsentinel_geaendert(self):
        self.write("RaidMaster.lua", "RaidMasterDB = {}")
        sc = up.TestReportScanner(self.sv)
        self.assertEqual(sc.scan(self.cfg()), [])
        self.write("ThreatSentinel.lua", sv_with("ThreatSentinelDB", [report("t-1", "ThreatSentinel")]))
        self.assertEqual([r["id"] for r in sc.scan(self.cfg())], ["t-1"])
        # RaidMaster.lua unverändert -> wird nicht neu gelesen (mtime)
        self.assertNotIn("RaidMaster.lua", [k for k, v in sc.mtimes.items() if v is None])
        self.assertEqual(sc.scan(self.cfg()), [])
        # gerade geschrieben (jünger als 2 s) -> noch nicht lesen
        self.write("BuffSentinel.lua", sv_with("BuffSentinelDB", [report("b-1", "BuffSentinel")]), age=0)
        self.assertEqual(sc.scan(self.cfg()), [])

    def test_u11_daten_upload_unveraendert(self):
        net = Net()
        up.urllib.request.urlopen = net
        rm = self.write("RaidMaster.lua", sv_with("RaidMasterDB", [report("r-1")]))
        self.assertTrue(up.upload(self.cfg(), rm))
        req = net.calls[0]
        self.assertTrue(req.full_url.startswith("https://discord.invalid/data"))
        names = [n.decode() for n in re.findall(rb'filename="([^"]+)"', req.data)]
        self.assertEqual(names, ["RaidMaster.lua.gz"])
        self.assertIn(b"RaidMaster-Daten", req.data)
        net2 = Net()
        up.urllib.request.urlopen = net2
        up.send_reports(self.cfg(), [report("r-1")])
        self.assertTrue(net2.calls[0].full_url.startswith("https://discord.invalid/test"))

    def test_u12_nur_berichte(self):
        secret = 'ThreatSentinelDB = {\n["geheim"] = "Spielername Gildenname",\n'
        self.write("ThreatSentinel.lua", secret + sv_with("X", [report("p-1", "ThreatSentinel")]).split("\n", 1)[1])
        net = Net()
        up.urllib.request.urlopen = net
        up.send_reports(self.cfg(), up.TestReportScanner(self.sv).scan(self.cfg()))
        raw = gzip.decompress(attachment(net.calls[0].data, "testberichte.json.gz"))
        self.assertNotIn(b"Spielername", raw)
        self.assertNotIn(b"Spielername", net.calls[0].data)
        self.assertEqual([r["id"] for r in json.loads(raw)], ["p-1"])

    def test_u13_gegenprobe_auswertung(self):
        net = Net()
        up.urllib.request.urlopen = net
        reps = [report("x-1"), report("x-2", "ThreatSentinel", kind="fehler")]
        up.send_reports(self.cfg(), reps)
        packed = attachment(net.calls[0].data, "testberichte.json.gz")
        back = testberichte.from_bytes("testberichte.json.gz", packed)
        self.assertEqual(sorted(r["id"] for r in back), ["x-1", "x-2"])


if __name__ == "__main__":
    unittest.main()
