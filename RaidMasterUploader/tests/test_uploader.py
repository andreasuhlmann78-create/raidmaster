"""Offline-Tests für den RaidMaster-Uploader (1.7.0 und 2.0.0). Keine Verbindung nach aussen: urlopen ist nachgebaut.
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

    def test_rp_u_nur_bank_und_raidready(self):
        # 2.3.3 (RP-U): nur GuildSentinelDB.bank und .raidReady gehen an den Bot – keine Mitglieder, Notizen o. Ä.
        rm = self.write("RaidMaster.lua", "RaidMasterDB = {}")
        gs = os.path.join(self.sv, "GuildSentinel.lua")
        full = ('GuildSentinelDB = {\n'
                '\t["members"] = {\n\t\t["Testa-Beispiel"] = {\n\t\t\t["note"] = "geheim } { ]",\n\t\t},\n\t},\n'
                '\t["bank"] = {\n\t\t["c"] = "Bankfigur",\n\t\t["t"] = 5,\n\t\t["i"] = {\n\t\t\t[2589] = 40,\n\t\t},\n\t},\n'
                '\t["notes"] = "-- kein Kommentar { ",\n'
                '\t["raidReady"] = {\n\t\t["raid"] = "Onyxia",\n\t\t["phase"] = "Aufbau",\n\t\t["aktiv"] = 23,\n'
                '\t\t["groesse"] = 40,\n\t\t["tanks"] = 2,\n\t\t["tanksSoll"] = 4,\n\t\t["heiler"] = 5,\n'
                '\t\t["heilerSoll"] = 10,\n\t\t["pct"] = 58,\n\t\t["wochen"] = 3,\n\t\t["t"] = 1794380000,\n\t},\n'
                '\t["sub"] = {\n\t\t["raidReady"] = "nicht dieses",\n\t},\n'
                '}\nGuildSentinelOther = {\n\t["bank"] = "nein",\n}\n')
        self.write("GuildSentinel.lua", full)
        out = up.read_guildsentinel(gs).decode("utf-8")
        self.assertNotIn("members", out)
        self.assertNotIn("Testa", out)
        self.assertNotIn("geheim", out)
        self.assertNotIn("notes", out)
        self.assertNotIn("nicht dieses", out)
        self.assertNotIn("GuildSentinelOther", out)
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "RaidMasterBot"))
        try:
            import raidmaster_data as rmd
            import raid_ready
        except ImportError:                                  # Bot-Abhängigkeiten fehlen: nur den Text prüfen
            self.assertIn('["raidReady"] = {', out)
            self.skipTest("Bot-Parser nicht importierbar")
        db = rmd.parse_saved_variables(out)["GuildSentinelDB"]
        self.assertEqual(db["bank"]["i"][2589], 40)
        rr = raid_ready.parse(db)
        self.assertEqual((rr["aktiv"], rr["groesse"], rr["tanks"], rr["heilerSoll"], rr["wochen"]), (23, 40, 2, 10, 3))
        text, _ = rmd.check_guildsentinel_upload(out.encode("utf-8"), "GuildSentinel.lua")   # Bot nimmt es an
        # nur raidReady ohne Bank: wird trotzdem geliefert (Bot entscheidet; Hinweis im Bericht an Discord)
        self.write("GuildSentinel.lua", 'GuildSentinelDB = {\n\t["raidReady"] = {\n\t\t["aktiv"] = 1,\n'
                                        '\t\t["groesse"] = 10,\n\t},\n\t["members"] = {},\n}\n')
        out = up.read_guildsentinel(gs).decode("utf-8")
        self.assertIn("raidReady", out)
        self.assertNotIn("members", out)

    def test_anhaenge_reihenfolge_und_bot(self):
        b, body = up.build_body({"content": "x"}, gzip.compress(b"R"), gzip.compress(b"G"), [("shot_1_2.jpg", "image/jpeg", b"J")])
        names = [n.decode() for n in re.findall(rb'filename="([^"]+)"', body)]
        self.assertEqual(names, ["RaidMaster.lua.gz", "GuildSentinel.lua.gz", "shot_1_2.jpg"])
        self.assertEqual(rmd.pick_upload_files(names), (0, 1))


# --- 1.8.0: Testberichte ---------------------------------------------------------------------------------
# --- 2.0.0: nur noch Neues, ein Paket, höchstens alle 15 Minuten ----------------------------------------------
def diag_text(addon, entries, stamp="09.11. 10:01", sessions=1):
    head = [f"{addon}-Protokoll v1.0 · {stamp}", "Client deDE · Spielversion: WoW Forever", f"Sitzungen: {sessions}"]
    head += [f"  09.11. 0{i}:00 L10 PRIEST forever v1.0" for i in range(sessions)]
    body = ["", "== Diagnose", "  Fehler in dieser Sitzung: 0", "", f"== Einträge ({len(entries)}, neueste zuerst)"]
    return f"GSDIAG1|{addon}|1.0|" + "\n".join(head + body + list(entries))


def sv_all(var, reports=(), diag=None, wege=(), secret=True):
    lines = [f"{var} = {{"]
    if secret:
        lines.append('\t["chars"] = { ["Testa Beispiel-Realm"] = { ["gold"] = 12345 } },')
    lines += ['\t["gsTest"] = {', '\t\t["reports"] = {']
    lines += ["\t\t\t" + lua_str("GSTEST1" + json.dumps(r, ensure_ascii=False)) + "," for r in reports]
    lines += ["\t\t},", "\t},"]
    if diag:
        lines.append('\t["diagExport"] = ' + lua_str(diag) + ",")
    if wege:
        lines.append('\t["wegeExport"] = {')
        lines += ["\t\t" + lua_str(w) + "," for w in wege]
        lines.append("\t},")
    lines.append("}")
    return "\n".join(lines) + "\n"


def fehler(rid, msg="x.lua:1: kaputt", count=1, addon="RaidMaster", t=100):
    return {"f": 1, "kind": "fehler", "id": rid, "addon": addon, "version": "1.0", "time": t, "env": {},
            "errors": [{"msg": msg, "count": count, "wo": "Lua", "stack": "a.lua:1\nb.lua:2", "version": "1.0"}]}


WEG = 'GSWEGE1' + json.dumps({"f": 1, "kind": "wege", "id": "w-1", "addon": "LevelPilot",
                              "zones": [{"map": 1412, "pts": [[1, 2]]}]})


class Paket(Base):
    def setUp(self):
        super().setUp()
        up.STATE = os.path.join(self.d, "uploader_state.json")
        self.net = Net()
        up.urllib.request.urlopen = self.net

    def items(self, call=0):
        name = re.search(rb'filename="(paket-[^"]+)"', self.net.calls[call].data).group(1).decode()
        return name, json.loads(gzip.decompress(attachment(self.net.calls[call].data, name)))["items"]

    def reporter(self, st=None):
        return up.Reporter(self.cfg(), self.sv, st if st is not None else up.load_state({}), sleep=lambda s: None)

    def test_p01_gleicher_bericht_zweimal_einmal_gesendet(self):
        self.write("RaidMaster.lua", sv_all("RaidMasterDB", [report("t-1")]))
        r = self.reporter()
        r.tick(now=1000)
        self.assertEqual(r.flush(now=2000), "ok")
        self.assertEqual(len(self.net.calls), 1)
        # /reload: dieselbe Datei neu geschrieben, Bericht noch drin; auch nach Neustart (Stand aus Datei)
        self.write("RaidMaster.lua", sv_all("RaidMasterDB", [report("t-1")]) + "-- neu\n", age=5)
        r2 = up.Reporter(self.cfg(), self.sv, up.load_state({}), sleep=lambda s: None)
        self.assertEqual(r2.flush(now=5000), "leer")
        self.assertEqual(len(self.net.calls), 1)
        self.assertIn("t-1", json.load(open(up.STATE, encoding="utf-8"))["sent_test_ids"])

    def test_p02_protokoll_ohne_neue_eintraege_nichts(self):
        d1 = diag_text("AHSentinel", ["[09.11. 06:33] AUFBAU ×3 Liste · 2 ms"])
        self.write("AHSentinel.lua", sv_all("AHSentinelDB", diag=d1))
        r = self.reporter()
        self.assertEqual(r.flush(now=1000), "ok")
        # nur Kopfzeile/Uhrzeit/Sitzungen anders -> nichts
        d2 = diag_text("AHSentinel", ["[09.11. 06:33] AUFBAU ×3 Liste · 2 ms"], stamp="09.11. 11:45", sessions=3)
        self.write("AHSentinel.lua", sv_all("AHSentinelDB", diag=d2), age=5)
        self.assertEqual(r.flush(now=2000), "leer")
        self.assertEqual(len(self.net.calls), 1)

    def test_p03_neuer_eintrag_ein_paket(self):
        d1 = diag_text("AHSentinel", ["[09.11. 06:33] AUFBAU ×3 Liste · 2 ms"])
        self.write("AHSentinel.lua", sv_all("AHSentinelDB", diag=d1))
        r = self.reporter()
        r.flush(now=1000)
        d2 = diag_text("AHSentinel", ["[09.11. 06:40] LANGSAM scan · 29 ms", "[09.11. 06:33] AUFBAU ×3 Liste · 2 ms"])
        self.write("AHSentinel.lua", sv_all("AHSentinelDB", diag=d2), age=5)
        self.assertEqual(r.flush(now=2000), "ok")
        name, items = self.items(1)
        self.assertTrue(name.startswith("paket-") and name.endswith(".json.gz"))
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0].startswith("GSDIAG1|AHSentinel|"))
        # gestiegener Zähler gilt auch als neu
        d3 = d2.replace("AUFBAU ×3", "AUFBAU ×4")
        self.write("AHSentinel.lua", sv_all("AHSentinelDB", diag=d3), age=3)
        self.assertEqual(r.flush(now=3000), "ok")

    def test_p04_drei_reload_ein_paket_nach_15_minuten(self):
        r = self.reporter()
        t0 = 100000.0
        for i in range(3):                                    # drei /reload in 5 Minuten, jedes Mal etwas Neues
            self.write("RaidMaster.lua", sv_all("RaidMasterDB", [report(f"t-{j}") for j in range(i + 1)]), age=0)
            os.utime(os.path.join(self.sv, "RaidMaster.lua"), (t0 + i * 120 - 10 + i, t0 + i * 120 - 10 + i))
            self.assertIsNone(r.tick(now=t0 + i * 120))
        self.assertEqual(self.net.calls, [])
        self.assertIsNone(r.tick(now=t0 + 14 * 60))         # Frist noch nicht um
        self.assertEqual(r.tick(now=t0 + 15 * 60 + 1), "ok")
        self.assertEqual(len(self.net.calls), 1)
        _, items = self.items(0)
        self.assertEqual(len(items), 3)                      # alle drei Berichte in EINEM Paket
        self.assertIsNone(r.tick(now=t0 + 16 * 60))

    def test_p05_gleicher_fehler_dreimal_eine_meldung_mit_zaehler(self):
        reps = [fehler("f-1", t=1), fehler("f-2", t=2), fehler("f-3", t=3)]
        self.write("RaidMaster.lua", sv_all("RaidMasterDB", reps))
        r = self.reporter()
        r.flush(now=1000)
        _, items = self.items(0)
        self.assertEqual(len(items), 1)
        rep = json.loads(items[0][len("GSTEST1"):])
        self.assertEqual(len(rep["errors"]), 1)
        self.assertEqual(rep["errors"][0]["count"], 3)
        self.assertNotIn("nur_zaehler", rep["errors"][0])
        # nächstes Mal derselbe Fehler (neuer Bericht): nur noch Zähler, ohne Stapel
        self.write("RaidMaster.lua", sv_all("RaidMasterDB", reps + [fehler("f-4", count=9, t=4)]), age=5)
        r.flush(now=2000)
        _, items = self.items(1)
        e = json.loads(items[0][len("GSTEST1"):])["errors"][0]
        self.assertEqual((e["count"], e["nur_zaehler"], e["vorher"]), (12, True, 3))
        self.assertNotIn("stack", e)
        # Gegenprobe: die Abholung liest das Paket
        name, _ = self.items(1)
        back = testberichte.from_bytes(name, attachment(self.net.calls[1].data, name))
        self.assertEqual([x["id"] for x in back], ["f-4"])

    def test_p06_alles_in_einer_nachricht_und_keine_namen(self):
        self.write("RaidMaster.lua", sv_all("RaidMasterDB", [report("t-1", extra=' "Zitat" äö\nzwei')]))
        self.write("ThreatSentinel.lua", sv_all("ThreatSentinelDB", [fehler("f-1", addon="ThreatSentinel")]))
        self.write("AHSentinel.lua", sv_all("AHSentinelDB", diag=diag_text("AHSentinel", ["[09.11.] X a"])))
        self.write("LevelPilot.lua", sv_all("LevelPilotDB", wege=[WEG]))
        r = self.reporter()
        self.assertEqual(r.flush(now=1000), "ok")
        self.assertEqual(len(self.net.calls), 1)
        req = self.net.calls[0]
        self.assertTrue(req.full_url.startswith("https://discord.invalid/test"))
        self.assertEqual(len(re.findall(rb'filename="', req.data)), 1)
        name, items = self.items(0)
        self.assertEqual(len(items), 4)
        self.assertNotIn(b"Testa Beispiel", req.data)
        self.assertNotIn("Testa", json.dumps(items))
        packed = attachment(req.data, name)
        self.assertEqual(sorted(x["id"] for x in testberichte.from_bytes(name, packed)), ["f-1", "t-1"])
        d, w = testberichte.extras_from_text(gzip.decompress(packed).decode("utf-8"))
        self.assertEqual([x["addon"] for x in d], ["AHSentinel"])
        self.assertEqual([x["id"] for x in w], ["w-1"])
        self.assertIn("Zitat", json.loads(items[[i for i, x in enumerate(items) if "t-1" in x][0]][7:])["text"])
        payload = json.loads(req.data.split(b"\r\n\r\n", 1)[1].split(b"\r\n--", 1)[0])
        self.assertEqual(payload["allowed_mentions"], {"parse": []})
        self.assertIn("GoldSentinel-Paket", payload["content"])
        # Wegdaten nur einmal
        self.write("LevelPilot.lua", sv_all("LevelPilotDB", wege=[WEG]) + "--\n", age=5)
        self.assertEqual(r.flush(now=2000), "leer")

    def test_p07_fehler_beim_senden_spaeter_ohne_doppelt(self):
        self.write("RaidMaster.lua", sv_all("RaidMasterDB", [report("t-1")]))
        r = self.reporter()
        up.urllib.request.urlopen = Net(500)
        self.assertEqual(r.flush(now=1000), "error")
        self.assertFalse(os.path.exists(up.STATE) and "t-1" in open(up.STATE).read())
        up.urllib.request.urlopen = self.net
        self.assertEqual(r.flush(now=2000), "ok")
        self.assertEqual(r.flush(now=3000), "leer")
        self.assertEqual(len(self.net.calls), 1)

    def test_p08_stand_nie_in_config(self):
        cfg_path = up.CONFIG
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(self.cfg(sent_test_ids=["alt-1"]), f)
        before = open(cfg_path, "rb").read()
        self.write("RaidMaster.lua", sv_all("RaidMasterDB", [report("alt-1"), report("neu-1")]))
        cfg = up.load_config()
        st = up.load_state(cfg)                               # Übernahme der alten Kennungen (nur lesen)
        r = up.Reporter(cfg, self.sv, st, sleep=lambda s: None)
        r.flush(now=1000)
        _, items = self.items(0)
        self.assertEqual([json.loads(x[7:])["id"] for x in items], ["neu-1"])
        self.assertEqual(open(cfg_path, "rb").read(), before)
        self.assertTrue(os.path.exists(up.STATE))

    def test_p09_zu_gross_uebersprungen_ohne_test_webhook_nichts(self):
        big = diag_text("AHSentinel", ["[x] " + "y" * (600 * 1024)])
        self.write("AHSentinel.lua", sv_all("AHSentinelDB", diag=big))
        r = self.reporter()
        self.assertEqual(r.flush(now=1000), "leer")
        self.assertTrue(any("zu gross" in l for l in self.logs))
        # 2.0.1: zweite Änderung (und neuer Start) -> keine zweite Meldung
        self.write("AHSentinel.lua", sv_all("AHSentinelDB", diag=big) + "-- neu\n", age=5)
        r.tick(now=1100)
        r.flush(now=1200)
        up.Reporter(self.cfg(), self.sv, up.load_state({}), sleep=lambda s: None).flush(now=1300)
        self.assertEqual(sum("zu gross" in l for l in self.logs), 1)
        r2 = up.Reporter(self.cfg(test_webhook_url=""), self.sv, up.load_state({}))
        self.assertIsNone(r2.flush(now=1000))
        self.assertIsNone(r2.tick(now=1000))

    def test_p13_zu_gross_neue_uhrzeit_keine_zweite_meldung(self):
        # 2.2.0 (offen 6): dasselbe zu grosse Protokoll, neu ausgegeben mit anderer Uhrzeit -> keine zweite Meldung
        entries = ["[x] " + "y" * (600 * 1024)]
        self.write("AHSentinel.lua", sv_all("AHSentinelDB", diag=diag_text("AHSentinel", entries, "09.11. 10:01")))
        r = self.reporter()
        r.flush(now=1000)
        self.write("AHSentinel.lua", sv_all("AHSentinelDB", diag=diag_text("AHSentinel", entries, "11.11. 21:30",
                                                                          sessions=2)), age=5)
        r.tick(now=1100)
        r.flush(now=1200)
        self.assertEqual(sum("zu gross" in l for l in self.logs), 1)
        # ein neuer Eintrag ist ein anderes Protokoll -> wieder eine Meldung
        self.write("AHSentinel.lua", sv_all("AHSentinelDB", diag=diag_text("AHSentinel", entries + ["[z] neu"])),
                   age=3)
        r.tick(now=1300)
        r.flush(now=1400)
        self.assertEqual(sum("zu gross" in l for l in self.logs), 2)

    def test_p10_daten_upload_unveraendert(self):
        rm = self.write("RaidMaster.lua", sv_all("RaidMasterDB", [report("r-1")]))
        self.assertTrue(up.upload(self.cfg(), rm))
        req = self.net.calls[0]
        self.assertTrue(req.full_url.startswith("https://discord.invalid/data"))
        names = [n.decode() for n in re.findall(rb'filename="([^"]+)"', req.data)]
        self.assertEqual(names, ["RaidMaster.lua.gz"])

    def test_p11_escapes_und_kaputte(self):
        vectors = [r'a\"b', r'x\\y', r'z\nq', 'zeile\\\nzwei', r'\195\164\195\182', r'\9tab\13', r'Ende\\']
        for v in vectors:
            self.assertEqual(up.lua_unescape(v), testberichte.lua_unescape(v), v)
        text = sv_with("RaidMasterDB", [report("ok-1")], junk=['GSTEST1{"f":1,"id":"kaputt"'])
        self.assertEqual([x["id"] for x in up.reports_in_text(text)], ["ok-1"])
        self.assertTrue(any("nicht lesbar" in l for l in self.logs))

    def test_p12_teil_zwei_fehlgeschlagen_teil_eins_nicht_nochmals(self):
        old = up.TEST_MAX_JSON
        up.TEST_MAX_JSON = 200                                # jeder Bericht ein eigener Teil
        try:
            self.write("RaidMaster.lua", sv_all("RaidMasterDB", [report("a-1", extra="x" * 150),
                                                                 report("a-2", extra="y" * 150)]))
            r = self.reporter()
            up.urllib.request.urlopen = Net(204, *([500] * 10))
            self.assertEqual(r.flush(now=1000), "error")
            st = json.load(open(up.STATE, encoding="utf-8"))
            self.assertEqual(st["sent_test_ids"], ["a-1"])     # Teil 1 gemerkt, Teil 2 nicht
            up.urllib.request.urlopen = self.net
            self.assertEqual(r.flush(now=2000), "ok")
            _, items = self.items(0)
            self.assertEqual([json.loads(x[7:])["id"] for x in items], ["a-2"])   # nur Teil 2 nochmals
        finally:
            up.TEST_MAX_JSON = old


if __name__ == "__main__":
    unittest.main()
