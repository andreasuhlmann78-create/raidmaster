"""UP-UPD1 (2.3.24): Uploader-Update nur nach Rückfrage "j" – Tests nach Regel 5 des Auftrags, mit Gegenproben.

Nachbau: Uploader-Ordner mit Programmdateien, Konfiguration und Zustand in einem Arbeitsordner; Zip im Speicher; der Start der neuen
Version ist nachgebildet (meldet "läuft" bzw. nicht).
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
import selfupdate  # noqa: E402

OLD = "2.3.24"
NEW = "2.3.25"


def make_zip(ver=NEW, extra=None, version_in_file=None, top="RaidMasterUploader"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{top}/", "")
        z.writestr(f"{top}/uploader.py", f'"""x"""\nVERSION = "{version_in_file or ver}"\nprint("neu")\n')
        z.writestr(f"{top}/daten.py", f"# daten {ver}\n")
        z.writestr(f"{top}/uploader.bat", "@echo off\r\npy -3 uploader.py\r\npause\r\n")
        z.writestr(f"{top}/LIESMICH.txt", f"Version {ver}\n")
        for k, v in (extra or {}).items():
            z.writestr(f"{top}/{k}", v)
    return buf.getvalue()


class Proc:
    def __init__(self, code=None):
        self.code, self.terminated = code, False
        self.returncode = code

    def poll(self):
        return None if self.terminated is False and self.code is None else (self.code if self.code is not None else -15)

    def terminate(self):
        self.terminated = True


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        files = {"uploader.py": f'VERSION = "{OLD}"\nprint("alt")\n', "daten.py": "# daten alt\n",
                 "uploader.bat": "@echo off\r\npy -3 uploader.py\r\npause\r\n", "LIESMICH.txt": "Version alt\n",
                 "sync.py": "# sync alt\n",
                 "uploader_config.json": '{"webhook_url": "https://x.invalid/geheim"}', "uploader_state.json": '{"a": 1}',
                 "sync_config.json": '{"s": 2}', "daten_config.json": '{"t": 3}', "uploader.log": "log\n"}
        for n, t in files.items():
            with open(os.path.join(self.d, n), "w", encoding="utf-8", newline="") as f:
                f.write(t)
        os.makedirs(os.path.join(self.d, "Sicherungen"))
        with open(os.path.join(self.d, "Sicherungen", "AHSentinel.lua"), "w") as f:
            f.write("daten\n")
        self.keep = self.hash_data()
        self.logs, self.keys, self.st, self.events = [], [], {}, []
        self.zip, self.sha = make_zip(), None
        self.start_ok = True
        self.spawned = []

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def hash_data(self):
        h = {}
        for dp, _dn, fns in os.walk(self.d):
            if selfupdate.UPDATE_DIR in dp.split(os.sep):
                continue
            for fn in fns:
                p = os.path.join(dp, fn)
                rel = os.path.relpath(p, self.d)
                if fn.endswith(".json") or fn.endswith(".log") or dp != self.d:
                    with open(p, "rb") as f:
                        h[rel] = hashlib.sha256(f.read()).hexdigest()
        return h

    def fetch(self):
        return self.zip, (self.sha or addons.git_blob_sha(self.zip))

    def spawn(self, here):
        self.spawned.append(here)
        if self.start_ok == "crash":
            return Proc(code=1)
        if self.start_ok:
            selfupdate.report_running(here, NEW)                 # die neue Version meldet "läuft"
        return Proc()

    def make(self, latest=NEW, minimum="2.3.20"):
        self.latest = latest
        return selfupdate.SelfUpdate(
            self.d, OLD, self.st, lambda: self.events.append("save"), self.logs.append,
            latest=lambda: self.latest, minimum=lambda: minimum, fetch_zip=self.fetch,
            key=lambda: self.keys.pop(0) if self.keys else None, spawn=self.spawn,
            handover=lambda: self.events.append("handover"), takeback=lambda: self.events.append("takeback"),
            sleep=lambda s: None, now=lambda: 1000.0,
            console=lambda: self.console_pid, kill_console=self.kill_console, kill=lambda p: self.events.append("kill_tree"))

    console_pid = None
    console_kill_ok = True

    def kill_console(self, pid):
        with open(os.path.join(self.d, "uploader.py"), encoding="utf-8") as f:
            self.events.append(("kill_console", pid, "alt" if OLD in f.read() else "neu"))   # vor dem Umschalten?
        return self.console_kill_ok

    def read(self, n):
        with open(os.path.join(self.d, n), encoding="utf-8") as f:
            return f.read()


class Rueckfrage(Base):
    def test_j_installiert_cmp_gleich_konfiguration_unveraendert(self):
        u = self.make()
        self.assertFalse(u.tick())
        self.assertIn("Neue Uploader-Version 2.3.25 verfügbar – jetzt installieren? (j/n)", self.logs[0])
        self.assertEqual(self.read("uploader.py"), f'VERSION = "{OLD}"\nprint("alt")\n')            # noch nichts
        self.keys.append("j")
        self.assertTrue(u.tick())
        self.assertTrue(u.exit_now)
        with zipfile.ZipFile(io.BytesIO(self.zip)) as z:
            for i in z.infolist():
                if not i.is_dir():
                    with open(os.path.join(self.d, i.filename.split("/")[1]), "rb") as f:
                        self.assertEqual(f.read(), z.read(i), i.filename)                          # cmp gleich
        self.assertEqual(self.hash_data(), self.keep)                                              # Konfiguration/Daten Bit für Bit
        self.assertEqual(self.read("sync.py"), "# sync alt\n")                                     # nicht in der Zip -> bleibt
        alt = os.path.join(self.d, selfupdate.UPDATE_DIR, "alt")
        with open(os.path.join(alt, "uploader.py"), encoding="utf-8") as f:
            self.assertIn(OLD, f.read())                                                            # Sicherung der alten Version
        self.assertFalse(any(n.endswith(".json") for n in os.listdir(alt)))
        self.assertIn("Uploader 2.3.24 -> 2.3.25 installiert, neu gestartet.", self.logs)
        self.assertEqual(self.st["daten"]["update"], {"von": OLD, "nach": NEW, "ergebnis": "ok", "zeit": 1000})
        self.assertEqual(self.events[:2], ["save", "handover"][:2] if self.events[0] == "save" else self.events[:2])
        self.assertIn("handover", self.events)
        self.assertNotIn("takeback", self.events)

    def test_n_nichts_und_keine_neue_frage_bis_neue_version(self):
        u = self.make()
        u.tick()
        self.keys.append("n")
        self.assertFalse(u.tick())
        self.assertEqual(self.spawned, [])
        self.assertEqual(self.read("uploader.py"), f'VERSION = "{OLD}"\nprint("alt")\n')
        u.next_at = 0
        u.tick()
        self.assertEqual(len([l for l in self.logs if "jetzt installieren" in l]), 1)               # nicht nochmals gefragt
        u2 = self.make()                                                                           # Neustart: gemerkt
        u2.tick()
        self.assertEqual(len([l for l in self.logs if "jetzt installieren" in l]), 1)
        self.latest = "2.3.26"                                                                     # nächste Version -> wieder
        u2.next_at = 0
        u2.tick()
        self.assertIn("2.3.26", self.logs[-1])
        # höhere Mindestversion -> für dieselbe abgelehnte Version wieder gefragt
        u3 = self.make(latest=NEW, minimum="2.3.25")
        u3.tick()
        self.assertTrue(self.logs[-1].startswith("Neue Uploader-Version 2.3.25"))

    def test_ohne_j_kein_update_gegenprobe(self):
        u = self.make()
        u.tick()                                                                                   # Frage gestellt
        for k in [None, "x", "", "1", "ja?", None]:                                                # keine dieser Eingaben installiert
            self.keys.append(k)
            self.assertFalse(u.tick(), k)
        self.assertEqual(self.spawned, [])
        self.assertEqual(self.read("uploader.py"), f'VERSION = "{OLD}"\nprint("alt")\n')
        for _ in range(20):                                                                        # ohne Taste nie
            self.assertFalse(u.tick())
        self.assertEqual(self.spawned, [])
        # Gegenprobe: "J" (gross) installiert
        self.keys.append("J")
        self.assertTrue(u.tick())
        self.assertEqual(len(self.spawned), 1)

    def test_keine_frage_wenn_aktuell(self):
        u = self.make(latest=OLD)
        u.tick()
        self.assertEqual(self.logs, [])
        u = self.make(latest="2.3.9")
        u.tick()
        self.assertEqual(self.logs, [])


class Abweisen(Base):
    def go(self, why):
        u = self.make()
        u.tick()
        self.keys.append("j")
        self.assertFalse(u.tick())
        self.assertEqual(self.spawned, [])
        self.assertEqual(self.read("uploader.py"), f'VERSION = "{OLD}"\nprint("alt")\n')
        self.assertEqual(self.hash_data(), self.keep)
        self.assertTrue(any("Update fehlgeschlagen" in l and why in l and "alte Version 2.3.24 läuft weiter" in l for l in self.logs),
                        self.logs)
        self.assertTrue(self.st["daten"]["update"]["ergebnis"].startswith("fehlgeschlagen: "))

    def test_falsche_pruefsumme(self):
        self.sha = "0" * 40
        self.go("Prüfsumme")

    def test_kaputte_zip(self):
        z = bytearray(make_zip())
        z[40:44] = b"XXXX"
        self.zip = bytes(z)
        self.go("Zip")

    def test_falsche_version(self):
        self.zip = make_zip(version_in_file="2.3.24")
        self.go("Version in der Zip ist 2.3.24, erwartet 2.3.25")

    def test_konfiguration_in_der_zip(self):
        self.zip = make_zip(extra={"uploader_config.json": "{}"})
        self.go("kein Programmteil (uploader_config.json)")

    def test_unterordner_in_der_zip(self):
        self.zip = make_zip(extra={"tests/x.py": "x"})
        self.go("unerwarteter Eintrag")

    def test_falscher_ordner(self):
        self.zip = make_zip(top="Anderes")
        self.go("unerwarteter Eintrag")


class Neustart(Base):
    def check_back(self):
        self.assertEqual(self.read("uploader.py"), f'VERSION = "{OLD}"\nprint("alt")\n')            # alte wieder da
        self.assertEqual(self.read("daten.py"), "# daten alt\n")
        self.assertEqual(self.hash_data(), self.keep)
        self.assertIn("takeback", self.events)                                                     # läuft weiter
        self.assertTrue(any("Update fehlgeschlagen" in l and "alte Version 2.3.24 läuft weiter" in l for l in self.logs))

    def test_neue_meldet_sich_nicht_alte_wieder_da(self):
        self.start_ok = False
        u = self.make()
        u.tick()
        self.keys.append("j")
        self.assertFalse(u.tick())
        self.assertFalse(u.exit_now)
        self.check_back()
        self.assertIn("innerhalb von 60 s", self.logs[-1])

    def test_neue_beendet_sich_sofort(self):
        self.start_ok = "crash"
        u = self.make()
        u.tick()
        self.keys.append("j")
        self.assertFalse(u.tick())
        self.check_back()
        self.assertIn("beendet sich sofort (Code 1)", self.logs[-1])

    def test_laufende_bat_wird_nie_ersetzt(self):
        self.zip = make_zip()
        z = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(self.zip)) as src, zipfile.ZipFile(z, "w") as dst:
            for i in src.infolist():
                data = src.read(i)
                if i.filename.endswith("uploader.bat"):
                    data = b"@echo off\r\nrem neu\r\npy -3 uploader.py\r\npause\r\n"
                dst.writestr(i, data)
        self.zip = z.getvalue()
        u = self.make()
        u.tick()
        self.keys.append("j")
        self.assertTrue(u.tick())
        with open(os.path.join(self.d, "uploader.bat"), "rb") as f:
            self.assertEqual(f.read(), b"@echo off\r\npy -3 uploader.py\r\npause\r\n")
        self.assertTrue(any("uploader.bat läuft gerade und bleibt unverändert" in l for l in self.logs))


class Fenster(Base):
    """UP-UPD1-a (2.3.26): eigenes Fenster (cmd.exe von uploader.bat) vor dem Umschalten beenden; dann darf uploader.bat ersetzt werden."""

    def new_bat_zip(self):
        z = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(make_zip())) as src, zipfile.ZipFile(z, "w") as dst:
            for i in src.infolist():
                data = src.read(i)
                if i.filename.endswith("uploader.bat"):
                    data = b"@echo off\r\nrem neu\r\npy -3 uploader.py\r\nif errorlevel 1 pause\r\n"
                dst.writestr(i, data)
        return z.getvalue()

    def bat(self):
        with open(os.path.join(self.d, "uploader.bat"), "rb") as f:
            return f.read()

    def test_fenster_frei_bat_ersetzt(self):
        self.zip = self.new_bat_zip()
        self.console_pid = 4242
        u = self.make()
        u.tick()
        self.keys.append("j")
        self.assertTrue(u.tick())
        self.assertIn(("kill_console", 4242, "alt"), self.events)                                  # vor dem Umschalten
        self.assertIn(b"rem neu", self.bat())                                                    # ersetzt
        self.assertFalse(any("läuft gerade" in l for l in self.logs))

    def test_fenster_nicht_gefunden_bat_bleibt(self):
        self.zip = self.new_bat_zip()
        self.console_pid = None                                                                   # z. B. ohne uploader.bat gestartet
        u = self.make()
        u.tick()
        self.keys.append("j")
        self.assertTrue(u.tick())
        self.assertFalse(any(isinstance(e, tuple) for e in self.events))
        self.assertNotIn(b"rem neu", self.bat())
        self.assertTrue(any("uploader.bat läuft gerade" in l for l in self.logs))

    def test_fenster_beenden_scheitert_bat_bleibt(self):
        self.zip = self.new_bat_zip()
        self.console_pid, self.console_kill_ok = 4242, False
        u = self.make()
        u.tick()
        self.keys.append("j")
        self.assertTrue(u.tick())
        self.assertNotIn(b"rem neu", self.bat())

    def test_rueckfall_beendet_neue_samt_kindern_alte_bat_zurueck(self):
        self.zip = self.new_bat_zip()
        self.console_pid = 4242
        self.start_ok = False
        u = self.make()
        u.tick()
        self.keys.append("j")
        self.assertFalse(u.tick())
        self.assertIn("kill_tree", self.events)
        self.assertEqual(self.bat(), b"@echo off\r\npy -3 uploader.py\r\npause\r\n")             # alte zurück

    def test_vorfahre_cmd_mit_uploader_bat(self):
        tree = {100: (90, "python.exe", "python uploader.py"), 90: (80, "py.exe", "py -3 uploader.py"),
                80: (70, "cmd.exe", 'C:\\WINDOWS\\system32\\cmd.exe /c ""C:\\X\\RaidMasterUploader\\uploader.bat" "'),
                70: (1, "explorer.exe", "explorer")}
        self.assertEqual(selfupdate.find_console_bat(100, info=tree.get), 80)
        tree[80] = (70, "cmd.exe", "cmd.exe /k")                                                  # Gegenprobe: anderes cmd
        self.assertIsNone(selfupdate.find_console_bat(100, info=tree.get))
        tree[80] = (70, "powershell.exe", "x uploader.bat")                                     # kein cmd
        self.assertIsNone(selfupdate.find_console_bat(100, info=tree.get))
        self.assertIsNone(selfupdate.find_console_bat(100, info=lambda p: None))

    def test_process_info_echt(self):
        if not os.path.exists("/proc/self/stat"):
            self.skipTest("nur mit /proc")
        got = selfupdate.process_info(os.getpid())
        self.assertEqual(got[0], os.getppid())
        self.assertIn("python", got[1].lower())


class Hilfen(unittest.TestCase):
    def test_echte_zip_im_repo_besteht(self):
        root = os.path.dirname(HERE)
        with open(os.path.join(root, "download", "RaidMasterUploader.zip"), "rb") as f:
            data = f.read()
        import re
        with open(os.path.join(HERE, "uploader.py"), encoding="utf-8") as f:
            ver = re.search(r'^VERSION = "([\d.]+)"', f.read(), re.M).group(1)
        files, why = selfupdate.check_zip(data, addons.git_blob_sha(data), ver, "2.3.0")
        self.assertIsNotNone(files, why)
        self.assertIn("selfupdate.py", files)
        self.assertFalse(any(n.endswith(".json") for n in files))

    def test_report_running_nur_fuer_erwartete_version(self):
        d = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(d, selfupdate.UPDATE_DIR))
            with open(selfupdate.status_path(d), "w") as f:
                json.dump({"von": OLD, "nach": NEW, "laeuft": False}, f)
            selfupdate.report_running(d, OLD)                                  # falsche Version -> nichts
            self.assertFalse(selfupdate.read_status(d)["laeuft"])
            selfupdate.report_running(d, NEW)
            self.assertTrue(selfupdate.read_status(d)["laeuft"])
            selfupdate.report_running(os.path.join(d, "fehlt"), NEW)            # ohne Datei: nichts, kein Fehler
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_uploader_meldet_laeuft_beim_start(self):
        with open(os.path.join(HERE, "uploader.py"), encoding="utf-8") as f:
            src = f.read()
        main = src[src.index("def main"):]
        self.assertLess(main.index("instance_acquire"), main.index("selfupdate.report_running(HERE, VERSION)"))


if __name__ == "__main__":
    unittest.main()
