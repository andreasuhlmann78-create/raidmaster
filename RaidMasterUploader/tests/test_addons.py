"""UP-AUTO1 (2.3.21): Uploader installiert neue Addon-Versionen selbst – Tests nach Regel 7 des Auftrags, mit Gegenproben.

Nachbau: Repo-Liste (announce/, download/) und Zips im Speicher, AddOns- und WTF-Ordner in einem Arbeitsordner.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import addons  # noqa: E402

ROOT = os.path.dirname(HERE)


def make_zip(addon, ver, extra=None, top=None, toc_ver=None, stored=False, toc_extra=""):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED) as z:
        t = top or addon
        z.writestr(f"{t}/", "")
        z.writestr(f"{t}/{addon}.toc", f"## Interface: 11508\n## Title: {addon}\n## Version: {toc_ver or ver}\nCore.lua\n{toc_extra}")
        z.writestr(f"{t}/Core.lua", f"-- {addon} {ver}\n")
        for k, v in (extra or {}).items():
            z.writestr(f"{t}/{k}", v)
    return buf.getvalue()


class FakeRepo:
    def __init__(self):
        self.files = {"announce": {}, "download": {}}
        self.calls = []
        self.etag_hits = 0
        self.tamper = set()

    def put(self, folder, name, data):
        self.files[folder][name] = data

    def blobs(self):
        out = {}
        for folder in addons.FOLDERS:
            for n, d in self.files[folder].items():
                out[addons.git_blob_sha(d)] = (n, d)
        return out

    def tree_of(self, folder):
        body = {"sha": "t-" + folder, "truncated": False,
                "tree": [{"path": n, "type": "blob", "size": len(d), "sha": addons.git_blob_sha(d)}
                         for n, d in sorted(self.files[folder].items())]}
        raw = json.dumps(body).encode()
        return hashlib.sha1(raw).hexdigest(), raw

    def __call__(self, url, headers=None):
        self.calls.append(url)
        if url == f"{addons.API}/repos/{addons.REPO}/contents":
            root = [{"name": f, "type": "dir", "sha": self.tree_of(f)[0]} for f in addons.FOLDERS]
            root.append({"name": "RaidMaster", "type": "dir", "sha": "x"})
            raw = json.dumps(root).encode()
            etag = '"' + hashlib.sha1(raw).hexdigest() + '"'
            if (headers or {}).get("If-None-Match") == etag:
                self.etag_hits += 1
                return 304, {"ETag": etag}, b""
            return 200, {"ETag": etag}, raw
        for folder in addons.FOLDERS:
            sha, raw = self.tree_of(folder)
            if url == f"{addons.API}/repos/{addons.REPO}/git/trees/{sha}":
                return 200, {}, raw
        pre = f"{addons.API}/repos/{addons.REPO}/git/blobs/"
        if url.startswith(pre):
            assert (headers or {}).get("Accept") == "application/vnd.github.raw"
            got = self.blobs().get(url[len(pre):])
            if not got:
                return 404, {}, b""
            n, d = got
            return 200, {}, (d + b"x" if n in self.tamper else d)
        return 404, {}, b""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addons_dir = os.path.join(self.tmp, "_forever_", "Interface", "AddOns")
        self.sv = os.path.join(self.tmp, "_forever_", "WTF", "Account", "KONTO", "SavedVariables")
        os.makedirs(self.sv)
        with open(os.path.join(self.sv, "AHSentinel.lua"), "w") as f:
            f.write("AHSentinelDB = { 1 }\n")
        self.repo = FakeRepo()
        self.logs = []
        # bisherige Tests prüfen beide Ordner -> Kanal "test"; der Kanal "stabil" (Standard) hat eigene Tests (RM-UPD2)
        self.cfg = {addons.CONFIG_KEY: True, addons.CHANNEL_KEY: "test"}
        self.ai = addons.AutoInstall(self.cfg, self.addons_dir, self.logs.append, get=self.repo)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def install_local(self, addon, ver, extra=None):
        d = os.path.join(self.addons_dir, addon)
        os.makedirs(d, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(make_zip(addon, ver, extra))) as z:
            for i in z.infolist():
                if not i.is_dir():
                    p = os.path.join(self.addons_dir, *i.filename.split("/"))
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    with open(p, "wb") as f:
                        f.write(z.read(i))

    def tree_hash(self, top):
        h = hashlib.sha256()
        for dp, dn, fns in sorted(os.walk(top)):
            dn.sort()
            for fn in sorted(fns):
                p = os.path.join(dp, fn)
                h.update(p.encode())
                with open(p, "rb") as f:
                    h.update(f.read())
        return h.hexdigest()


class Installieren(Base):
    def test_neuere_version_installiert_cmp_gleich(self):
        self.install_local("AHSentinel", "0.65.391")
        z = make_zip("AHSentinel", "0.65.392")
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.392.AHSentinel.zip", z)
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.391.AHSentinel.zip", make_zip("AHSentinel", "0.65.391"))
        sv = self.tree_hash(os.path.join(self.tmp, "_forever_", "WTF"))
        out = self.ai.tick(now=1000)
        self.assertEqual(len(out), 1, out)
        self.assertIn("AHSentinel 0.65.391 -> 0.65.392 installiert", out[0])
        self.assertIn("im Spiel /reload", out[0])
        self.assertEqual(addons.installed_version(self.addons_dir, "AHSentinel"), "0.65.392")
        with zipfile.ZipFile(io.BytesIO(z)) as zz:
            for i in zz.infolist():
                if not i.is_dir():
                    with open(os.path.join(self.addons_dir, *i.filename.split("/")), "rb") as f:
                        self.assertEqual(f.read(), zz.read(i), i.filename)                  # cmp gleich
        self.assertEqual(self.tree_hash(os.path.join(self.tmp, "_forever_", "WTF")), sv)    # SavedVariables Bit für Bit
        self.assertFalse([p for p in os.listdir(os.path.join(self.addons_dir, "AHSentinel")) if p.endswith(".gsneu")])
        # danach: gleiche Version -> nichts (auch nach 5 Min.), Liste unverändert = 304
        self.assertEqual(self.ai.tick(now=1000 + addons.CHECK_SECONDS), [])
        self.assertEqual(self.repo.etag_hits, 1)                                # Wurzel unverändert = 304
        n = len(self.repo.calls)
        self.repo.put("download", "Anderes.txt", b"x")                         # announce/ unverändert -> nur download/ neu gelesen
        self.ai.tick(now=1000 + 2 * addons.CHECK_SECONDS)
        self.assertEqual([u.split("/repos/")[1].split("/")[2] for u in self.repo.calls[n:]], ["contents", "git"])
        self.assertIn("/git/trees/", self.repo.calls[-1])

    def test_gleiche_und_aeltere_nichts(self):
        self.install_local("AHSentinel", "0.65.392")
        self.install_local("BuffSentinel", "0.9.70")
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.392.AHSentinel.zip", make_zip("AHSentinel", "0.65.392"))
        self.repo.put("announce", "buffsentinel__buffsentinel-0.9.61.BuffSentinel.zip", make_zip("BuffSentinel", "0.9.61"))
        before = self.tree_hash(self.addons_dir)
        self.assertEqual(self.ai.tick(now=1000), [])
        self.assertEqual(self.tree_hash(self.addons_dir), before)
        self.assertFalse([u for u in self.repo.calls if "/git/blobs/" in u])            # nicht einmal geladen

    def test_zahlenvergleich_nicht_text(self):
        self.install_local("ThreatSentinel", "2.5.9")
        self.repo.put("announce", "threatsentinel__threatsentinel-2.5.30.ThreatSentinel.zip", make_zip("ThreatSentinel", "2.5.30"))
        out = self.ai.tick(now=1000)
        self.assertIn("2.5.9 -> 2.5.30", out[0])

    def test_hoechste_aus_announce_und_download(self):
        self.install_local("RaidMaster", "3.0.42")
        self.repo.put("download", "RaidMaster-3.0.43.zip", make_zip("RaidMaster", "3.0.43"))
        self.repo.put("download", "RaidMaster-3.0.9.zip", make_zip("RaidMaster", "3.0.9"))
        self.repo.put("download", "RaidMaster-latest.zip", make_zip("RaidMaster", "3.0.43"))      # ohne Version: nie
        self.repo.put("download", "RaidMasterUploader.zip", make_zip("RaidMasterUploader", "2.3.21"))
        out = self.ai.tick(now=1000)
        self.assertEqual(len(out), 1, out)
        self.assertIn("RaidMaster 3.0.42 -> 3.0.43", out[0])

    def test_nicht_installiert_nichts(self):
        self.repo.put("announce", "levelpilot__levelpilot-3.12.99.LevelPilot.zip", make_zip("LevelPilot", "3.12.99"))
        self.assertEqual(self.ai.tick(now=1000), [])
        self.assertFalse(os.path.exists(os.path.join(self.addons_dir, "LevelPilot")))

    def test_nie_gsmesstest(self):
        self.install_local("GSMesstest", "1.0")
        self.repo.put("download", "GSMesstest-1.1.zip", make_zip("GSMesstest", "1.1"))
        self.assertEqual(self.ai.tick(now=1000), [])
        self.assertEqual(addons.installed_version(self.addons_dir, "GSMesstest"), "1.0")

    def test_schalter_aus_nur_ausdruecklich(self):
        # RM-UPD2: Standard AN; AUS nur mit Merker "addons_auto_gewaehlt" (Addons-automatisch-aus.bat)
        self.install_local("AHSentinel", "0.65.391")
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.392.AHSentinel.zip", make_zip("AHSentinel", "0.65.392"))
        self.cfg[addons.CONFIG_KEY] = False
        self.cfg[addons.CHOSEN_KEY] = True                                       # ausdrücklich aus
        self.assertEqual(self.ai.tick(now=1000), [])
        self.assertEqual(self.repo.calls, [])                                    # nicht einmal das Repo gefragt
        self.assertEqual(addons.installed_version(self.addons_dir, "AHSentinel"), "0.65.391")
        # Gegenprobe: altes "false" ohne Merker (Standard früher AUS) -> gilt AN
        self.cfg.pop(addons.CHOSEN_KEY)
        self.assertEqual(len(self.ai.tick(now=2000)), 1)
        self.assertEqual(addons.installed_version(self.addons_dir, "AHSentinel"), "0.65.392")

    def test_standard_an_frisch_und_alt(self):
        self.assertTrue(addons.auto_enabled({}))                                 # frische Konfiguration
        self.assertTrue(addons.auto_enabled({"webhook_url": "x"}))              # alte ohne Schalter
        self.assertTrue(addons.auto_enabled({addons.CONFIG_KEY: False}))        # altes "aus" ohne Merker
        self.assertTrue(addons.auto_enabled({addons.CONFIG_KEY: "ja", addons.CHOSEN_KEY: True}))
        self.assertFalse(addons.auto_enabled({addons.CONFIG_KEY: False, addons.CHOSEN_KEY: True}))   # ausdrücklich aus

    def test_kanal_stabil_nur_download(self):
        # RM-UPD2 (Nutzer 27.11. 07:11 "nur die stabilen versionen"): Standard -> nur download/, nie announce/
        self.cfg.pop(addons.CHANNEL_KEY)
        self.ai = addons.AutoInstall(self.cfg, self.addons_dir, self.logs.append, get=self.repo)
        self.install_local("AHSentinel", "0.65.391")
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.399.AHSentinel.zip", make_zip("AHSentinel", "0.65.399"))
        self.repo.put("download", "AHSentinel-0.65.395.zip", make_zip("AHSentinel", "0.65.395"))
        out = self.ai.tick(now=1000)
        self.assertEqual(len(out), 1)
        self.assertEqual(addons.installed_version(self.addons_dir, "AHSentinel"), "0.65.395")   # nicht die Testversion 0.65.399
        self.assertFalse(any("announce" in str(c) for c in self.repo.calls))    # announce/ nicht einmal gelesen
        # nur in announce/ -> für "stabil" nichts
        self.install_local("ThreatSentinel", "2.5.1")
        self.repo.put("announce", "threatsentinel__threatsentinel-2.5.9.ThreatSentinel.zip", make_zip("ThreatSentinel", "2.5.9"))
        self.ai.tick(now=2000)
        self.assertEqual(addons.installed_version(self.addons_dir, "ThreatSentinel"), "2.5.1")
        # unbekannter Kanalwert -> wie stabil
        self.assertEqual(addons.channel_folders({addons.CHANNEL_KEY: "beta"}), addons.STABLE_FOLDERS)
        # Gegenprobe Kanal "test": höchste aus beiden
        self.cfg[addons.CHANNEL_KEY] = "test"
        self.ai.tick(now=3000)
        self.assertEqual(addons.installed_version(self.addons_dir, "AHSentinel"), "0.65.399")
        self.assertEqual(addons.installed_version(self.addons_dir, "ThreatSentinel"), "2.5.9")

    def test_toc_mit_neuer_datei_meldet_neustart(self):
        self.install_local("ProfessionSentinel", "0.9.83")
        self.repo.put("announce", "professionsentinel__professionsentinel-0.9.84.ProfessionSentinel.zip",
                      make_zip("ProfessionSentinel", "0.9.84", toc_extra="Core.lua\n"))     # Dateiliste in der .toc geändert
        out = self.ai.tick(now=1000)
        self.assertIn("NEUSTART des Spiels nötig (neue Dateien: 0)", out[0])

    def test_daten_ordner_wie_levelpilot(self):
        self.install_local("LevelPilot", "3.13.12")
        buf = io.BytesIO(make_zip("LevelPilot", "3.13.13"))
        with zipfile.ZipFile(buf, "a") as zz:
            zz.writestr("LevelPilot_Data/LevelPilot_Data.toc", "## Version: 3.13.13\n")
            zz.writestr("LevelPilot_Data_deDE/Daten.lua", "-- de\n")
        self.repo.put("announce", "levelpilot__levelpilot-3.13.13.LevelPilot.zip", buf.getvalue())
        out = self.ai.tick(now=1000)
        self.assertIn("LevelPilot 3.13.12 -> 3.13.13 installiert", out[0])
        self.assertIn("NEUSTART", out[0])                                         # neue Ordner/Dateien
        self.assertTrue(os.path.isfile(os.path.join(self.addons_dir, "LevelPilot_Data_deDE", "Daten.lua")))
        # Gegenprobe: ein Ordner, der nicht mit "LevelPilot_" beginnt -> nichts
        self.install_local("BuffSentinel", "0.9.60")
        buf = io.BytesIO(make_zip("BuffSentinel", "0.9.61"))
        with zipfile.ZipFile(buf, "a") as zz:
            zz.writestr("BuffSentinelX/a.lua", "x")
        self.repo.put("announce", "buffsentinel__buffsentinel-0.9.61.BuffSentinel.zip", buf.getvalue())
        out = self.ai.tick(now=1000 + addons.CHECK_SECONDS)
        self.assertIn("NICHT installiert", out[0])
        self.assertFalse(os.path.exists(os.path.join(self.addons_dir, "BuffSentinelX")))

    def test_neue_datei_meldet_neustart_und_loescht_nichts(self):
        self.install_local("BuffSentinel", "0.9.60", extra={"Alt.lua": "-- alt\n"})
        self.repo.put("announce", "buffsentinel__buffsentinel-0.9.61.BuffSentinel.zip",
                      make_zip("BuffSentinel", "0.9.61", extra={"Neu.lua": "-- neu\n"}))
        out = self.ai.tick(now=1000)
        self.assertIn("NEUSTART des Spiels nötig (neue Dateien: 1)", out[0])
        self.assertIn("bleibt liegen: 1 Datei(en) (BuffSentinel/Alt.lua)", out[0])
        self.assertTrue(os.path.isfile(os.path.join(self.addons_dir, "BuffSentinel", "Alt.lua")))       # nichts gelöscht
        self.assertTrue(os.path.isfile(os.path.join(self.addons_dir, "BuffSentinel", "Neu.lua")))

    def test_takt_hoechstens_alle_5_min(self):
        os.makedirs(self.addons_dir)
        self.ai.tick(now=1000)
        n = len(self.repo.calls)
        self.ai.tick(now=1000 + addons.CHECK_SECONDS - 1)
        self.assertEqual(len(self.repo.calls), n)
        self.ai.tick(now=1000 + addons.CHECK_SECONDS)
        self.assertGreater(len(self.repo.calls), n)


class Abweisen(Base):
    def setUp(self):
        super().setUp()
        self.install_local("AHSentinel", "0.65.391")
        self.before = self.tree_hash(self.addons_dir)

    def check_rejected(self, why_part, retry=True):
        out = self.ai.tick(now=1000)
        self.assertEqual(len(out), 1, out)
        self.assertIn("NICHT installiert", out[0])
        self.assertIn(why_part, out[0])
        self.assertEqual(self.tree_hash(self.addons_dir), self.before)              # nichts geschrieben
        return out[0]

    def test_kaputte_zip(self):
        z = bytearray(make_zip("AHSentinel", "0.65.392", stored=True))
        i = z.find(b"-- AHSentinel")
        self.assertGreater(i, 0)
        z[i:i + 4] = b"XXXX"                                                     # CRC passt nicht mehr
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.392.AHSentinel.zip", bytes(z))
        self.check_rejected("beschädigt")
        self.repo.files["announce"]["ahsentinel__ahsentinel-0.65.392.AHSentinel.zip"] = b"keine zip"
        self.ai.fail.clear()
        self.ai.next_at = 0
        self.check_rejected("nicht lesbar")

    def test_falscher_ordner(self):
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.392.AHSentinel.zip", make_zip("AHSentinel", "0.65.392", top="Anderes"))
        self.check_rejected("fremder Ordner in der Zip (Anderes)")

    def test_zweiter_ordner_in_der_zip(self):
        z = make_zip("AHSentinel", "0.65.392")
        buf = io.BytesIO(z)
        with zipfile.ZipFile(buf, "a") as zz:
            zz.writestr("Fremd/Fremd.toc", "## Version: 1\n")
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.392.AHSentinel.zip", buf.getvalue())
        self.check_rejected("ausserhalb des Ordners")

    def test_pfad_mit_punkt_punkt(self):
        buf = io.BytesIO(make_zip("AHSentinel", "0.65.392"))
        with zipfile.ZipFile(buf, "a") as zz:
            zz.writestr("AHSentinel/../../../WTF/x.lua", "boese")
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.392.AHSentinel.zip", buf.getvalue())
        self.check_rejected("unzulässiger Pfad")
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "_forever_", "WTF", "x.lua")))

    def test_falsche_version_in_toc(self):
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.392.AHSentinel.zip", make_zip("AHSentinel", "0.65.392", toc_ver="0.65.391"))
        self.check_rejected("Version in der .toc ist 0.65.391, erwartet 0.65.392")

    def test_falsche_pruefsumme_mit_wiederholung_und_zeitlimit(self):
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.392.AHSentinel.zip", make_zip("AHSentinel", "0.65.392"))
        self.repo.tamper.add("ahsentinel__ahsentinel-0.65.392.AHSentinel.zip")
        line = self.check_rejected("Prüfsumme passt nicht")
        self.assertIn("Neuer Versuch in 1 Min. (Versuch 1 von 5)", line)
        t, n_tries = 1000, 1
        for _ in range(40):                                                     # 40 × 5 Min. = über 3 Std.
            t += addons.CHECK_SECONDS
            n_tries += len(self.ai.tick(now=t))
        self.assertEqual(n_tries, 6)                                             # 5 Wiederholungen, dann Ruhe
        self.assertIn("Kein weiterer Versuch", self.logs[-1])
        self.assertEqual(self.tree_hash(self.addons_dir), self.before)
        # neue Version -> wieder versucht (und richtig installiert)
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.393.AHSentinel.zip", make_zip("AHSentinel", "0.65.393"))
        out = self.ai.tick(now=t + addons.CHECK_SECONDS)
        self.assertIn("0.65.391 -> 0.65.393 installiert", out[0])

    def test_gesperrte_datei_wird_gemeldet_und_spaeter_installiert(self):
        self.repo.put("announce", "ahsentinel__ahsentinel-0.65.392.AHSentinel.zip", make_zip("AHSentinel", "0.65.392"))
        orig = addons.os.replace
        state = {"n": 0}

        def locked(a, b):
            state["n"] += 1
            raise PermissionError(13, "Zugriff verweigert")
        addons.os.replace = locked
        try:
            out = self.ai.tick(now=1000)
        finally:
            addons.os.replace = orig
        self.assertIn("Schreiben nicht möglich (PermissionError", out[0])
        self.assertIn("Datei gesperrt oder kein Schreibrecht", out[0])
        self.assertEqual(addons.installed_version(self.addons_dir, "AHSentinel"), "0.65.391")
        out = self.ai.tick(now=1000 + addons.CHECK_SECONDS)
        self.assertIn("installiert", out[0])

    def test_repo_nicht_erreichbar(self):
        def down(url, headers=None):
            raise OSError("kein Netz")
        self.ai.get = down
        self.assertEqual(self.ai.tick(now=1000), [])
        self.assertIn("Repo nicht erreichbar", self.logs[0])
        self.assertEqual(self.ai.tick(now=1000 + addons.CHECK_SECONDS), [])
        self.assertEqual(len(self.logs), 1)                                     # einmal gemeldet, nicht jede Runde


class Schalter(unittest.TestCase):
    """Regel 5: Standard aus; nur der Nutzer schaltet; ein laufender Uploader überschreibt den Schalter nie."""

    def test_schalter_bleibt_beim_speichern_des_laufenden_uploaders(self):
        import uploader
        tmp = tempfile.mkdtemp()
        old = uploader.CONFIG
        uploader.CONFIG = os.path.join(tmp, "uploader_config.json")
        try:
            running = {"webhook_url": "https://example.invalid/x", "sent_shots": []}       # Stand beim Start: kein Schalter
            with open(uploader.CONFIG, "w", encoding="utf-8") as f:
                json.dump(running, f)
            uploader.input = lambda *a: ""
            uploader.addons_toggle("an")                                        # Nutzer schaltet ein (.bat)
            with open(uploader.CONFIG, encoding="utf-8") as f:
                self.assertIs(json.load(f)[addons.CONFIG_KEY], True)
            running["sent_shots"] = ["a.jpg"]
            uploader.save_config(running)                                       # laufender Uploader speichert seinen Stand
            with open(uploader.CONFIG, encoding="utf-8") as f:
                disk = json.load(f)
            self.assertIs(disk[addons.CONFIG_KEY], True)                        # Schalter nicht überschrieben
            self.assertEqual(disk["sent_shots"], ["a.jpg"])                     # sein eigener Teil schon
            uploader.addons_toggle("aus")
            uploader.save_config(dict(running, **{addons.CONFIG_KEY: True}))    # auch ein alter Wert im Speicher gilt nicht
            with open(uploader.CONFIG, encoding="utf-8") as f:
                disk = json.load(f)
            self.assertIs(disk[addons.CONFIG_KEY], False)
            self.assertIs(disk[addons.CHOSEN_KEY], True)                        # RM-UPD2: ausdrücklich gewählt
            self.assertFalse(addons.auto_enabled(disk))
            uploader.addons_channel("an")                                       # RM-UPD2: Testversionen
            uploader.save_config(dict(running))                                 # laufender Uploader überschreibt den Kanal nicht
            with open(uploader.CONFIG, encoding="utf-8") as f:
                self.assertEqual(json.load(f)[addons.CHANNEL_KEY], "test")
            uploader.addons_channel("aus")
            with open(uploader.CONFIG, encoding="utf-8") as f:
                self.assertEqual(json.load(f)[addons.CHANNEL_KEY], "stabil")
            uploader.addons_toggle("vielleicht")                                # falscher Wert -> nichts geändert
            with open(uploader.CONFIG, encoding="utf-8") as f:
                self.assertIs(json.load(f)[addons.CONFIG_KEY], False)
        finally:
            uploader.CONFIG = old
            shutil.rmtree(tmp, ignore_errors=True)

    def test_bat_dateien(self):
        for n in ("an", "aus"):
            for name, arg in ((f"Addons-automatisch-{n}.bat", f"--addons-auto {n}"), (f"Addons-Testversionen-{n}.bat", f"--addons-test {n}")):
                with open(os.path.join(HERE, name), "rb") as f:
                    b = f.read()
                self.assertIn(arg.encode(), b)
                self.assertTrue(b.isascii())
                self.assertIn(b"\r\n", b)


class Hilfen(unittest.TestCase):
    def test_versionen_wie_announce_reihe(self):
        sys.path.insert(0, os.path.join(ROOT, "RaidMasterBot"))
        import announce_reihe
        names = sorted(n for n in os.listdir(os.path.join(ROOT, "announce")) if n.endswith(".zip"))
        self.assertGreater(len(names), 10)
        for n in names:
            got = addons.parse_entry("announce", n)
            self.assertTrue(got, n)
            _series, ver = announce_reihe.announce_series(n)
            self.assertEqual(addons.version_key(got[1]), ver, n)                 # gleiche Reihenfolge wie der Bot

    def test_echte_repo_zips_bestehen_die_pruefung(self):
        listing = {}
        for folder in addons.FOLDERS:
            d = os.path.join(ROOT, folder)
            listing[folder] = []
            for n in os.listdir(d):
                if n.endswith(".zip"):
                    with open(os.path.join(d, n), "rb") as f:
                        data = f.read()
                    listing[folder].append({"name": n, "sha": addons.git_blob_sha(data), "size": len(data), "path": os.path.join(d, n)})
        best = addons.newest(listing)
        self.assertIn("RaidMaster", best)
        self.assertNotIn("RaidMasterUploader", best)
        self.assertNotIn("LevelPilot_Data", best)                                 # kommt mit LevelPilot
        checked = 0
        for addon, b in best.items():
            path = os.path.join(ROOT, b["folder"], b["name"])
            with open(path, "rb") as f:
                files, why = addons.check_zip(f.read(), addon, b["ver"], b["sha"])
            self.assertIsNotNone(files, f"{b['name']}: {why}")
            checked += 1
        self.assertGreaterEqual(checked, 5)

    def test_forever_ordner(self):
        roots = {"_anniversary_/K": os.path.join("C:", "WoW", "_anniversary_", "WTF", "Account", "K"),
                 "_forever_/K": os.path.join("C:", "WoW", "_forever_", "WTF", "Account", "K")}
        self.assertEqual(addons.forever_addons_dir({}, roots), os.path.join("C:", "WoW", "_forever_", "Interface", "AddOns"))
        self.assertEqual(addons.forever_addons_dir({addons.PATH_KEY: "D:/X/AddOns"}, roots), os.path.normpath("D:/X/AddOns"))
        self.assertIsNone(addons.forever_addons_dir({}, {"_anniversary_/K": roots["_anniversary_/K"]}))

    def test_git_blob_sha(self):
        self.assertEqual(addons.git_blob_sha(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")


if __name__ == "__main__":
    unittest.main()
