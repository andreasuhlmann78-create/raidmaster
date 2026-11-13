"""Offline-Tests Uploader 2.1.0–2.2.0: Abgleich der Addon-Daten zwischen zwei Rechnern (T-SY1 … T-SY16).
Zwei Ordner spielen PC und Laptop, ein Ersatz-Speicher spielt #sync-daten. Kein Netz.
Start: python3 -I RaidMasterUploader/tests/test_sync.py"""
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import sync  # noqa: E402


class FakeStore:
    """Wie WebhookStore, aber im Speicher. online=False -> kein Netz."""

    def __init__(self):
        self.index, self.parts, self.next, self.online, self.deleted = {}, {}, 1000, True, []
        self.reads, self.gets = 0, 0

    def _net(self):
        if not self.online:
            raise sync.StoreError("kein Netz oder Discord nicht erreichbar")

    def read_index(self):
        self._net()
        self.reads += 1
        return json.loads(json.dumps(self.index))

    def write_index(self, index):
        self._net()
        self.index = json.loads(json.dumps(index))

    def put_part(self, name, blob, note):
        self._net()
        self.next += 1
        self.parts[str(self.next)] = blob
        return str(self.next)

    def get_part(self, mid):
        self._net()
        self.gets += 1
        if mid not in self.parts:
            raise sync.StoreError("Paket nicht mehr vorhanden")
        return self.parts[mid]

    def delete_part(self, mid):
        self.deleted.append(mid)
        self.parts.pop(mid, None)


AH_PC = 'AHSentinelDB = {\n\t["deLog"] = {\n\t\t{ ["t"] = 2, ["i"] = 100 },\n\t},\n\t["n"] = 256,\n}\n'
AH_LAPTOP = 'AHSentinelDB = {\n\t["deLog"] = {\n\t\t{ ["t"] = 1, ["i"] = 200 },\n\t},\n\t["n"] = 85,\n}\n'


class Machine:
    def __init__(self, root, name, store, clock=None):
        self.acc = os.path.join(root, name, "WTF", "Account", "KONTO")
        os.makedirs(os.path.join(self.acc, "SavedVariables"))
        os.makedirs(os.path.join(self.acc, "Realm", "Figur", "SavedVariables"))
        self.st, self.logs, self.notes, self.running = {}, [], [], False
        self.sync = sync.Sync(store, self.acc, self.st, lambda: None, name, self.logs.append,
                              is_wow_running=lambda: self.running, notify=self.notes.append,
                              clock_offset=(lambda: clock) if clock is not None else None)

    def write(self, rel, text, mtime):
        fn = os.path.join(self.acc, *rel.split("/"))
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        with open(fn, "w", encoding="utf-8") as f:
            f.write(text)
        os.utime(fn, (mtime, mtime))
        return fn

    def read(self, rel):
        with open(os.path.join(self.acc, *rel.split("/")), encoding="utf-8") as f:
            return f.read()

    def backups(self):
        root = os.path.join(self.acc, sync.BACKUP_DIR)
        out = []
        for d, _, files in os.walk(root):
            out += [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/") for f in files]
        return sorted(out)


T0 = 1794380000.0


class Abgleich(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.store = FakeStore()
        self.pc = Machine(self.d, "PC", self.store)
        self.lap = Machine(self.d, "Laptop", self.store)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_sy1_pc_hoch_laptop_holt_mit_sicherung(self):
        self.pc.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { [\"v\"] = 2 }\n", T0)
        self.pc.write("Realm/Figur/SavedVariables/Buff.lua", "BuffDB = {}\n", T0)
        self.lap.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { [\"v\"] = 1 }\n", T0 - 3600)
        self.lap.sync.s["seq"] = 0
        # 2.2.0: 10 s Ruhe abwarten, dann hoch
        self.pc.sync.tick(now=T0 + 5)
        self.assertEqual(self.store.index, {})
        self.pc.sync.tick(now=T0 + 15)
        self.assertEqual(self.store.index["seq"], 1)
        self.assertEqual(self.store.index["machine"], "PC")
        # Laptop holt vor dem Start; lokale Datei vorher gesichert
        self.assertTrue(self.lap.sync.pull(now=T0 + 300))
        self.assertIn('"v"] = 2', self.lap.read("SavedVariables/RaidMaster.lua"))
        self.assertEqual(self.lap.read("Realm/Figur/SavedVariables/Buff.lua"), "BuffDB = {}\n")
        # noch nie abgeglichen und verschieden: Konflikt (offen 1 a) – Laptop-Stand gesichert
        self.assertTrue(any(b.endswith("SavedVariables/RaidMaster.lua.lokal") for b in self.lap.backups()))
        self.assertIn("aktuell", self.lap.sync.status_line())
        self.assertNotIn("NICHT", self.lap.sync.status_line())
        # Laptop ändert etwas -> nach Ruhe hoch, PC holt es
        self.lap.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { [\"v\"] = 3 }\n", T0 + 400)
        self.lap.sync.tick(now=T0 + 600)
        self.assertEqual(self.store.index["seq"], 2)
        self.pc.sync.pull(now=T0 + 700)
        self.assertIn('"v"] = 3', self.pc.read("SavedVariables/RaidMaster.lua"))

    def test_sy2_wow_laeuft_nichts_ueberschreiben(self):
        self.pc.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { [\"v\"] = 2 }\n", T0)
        self.pc.sync.push(now=T0 + 200)
        self.lap.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { [\"v\"] = 1 }\n", T0 - 50)
        self.lap.running = True
        self.assertFalse(self.lap.sync.pull(now=T0 + 300))
        self.assertIn('"v"] = 1', self.lap.read("SavedVariables/RaidMaster.lua"))
        self.assertEqual(self.lap.backups(), [])
        self.assertEqual(len(self.lap.notes), 1)
        self.assertIn("Neuerer Stand vom PC (", self.lap.notes[0])               # 2.3.2: mit Zeit und Spielversion
        self.assertIn("WoW beenden, dann übernehmen", self.lap.notes[0])
        self.lap.sync.tick(now=T0 + 900)                       # nicht jedes Mal neu melden
        self.assertEqual(len(self.lap.notes), 1)
        self.assertIn("NICHT aktuell", self.lap.sync.status_line())
        # WoW läuft: auch nicht hochladen
        self.lap.write("SavedVariables/X.lua", "X = {}\n", T0)
        self.assertFalse(self.lap.sync.push(now=T0 + 1000))
        self.assertEqual(self.store.index["seq"], 1)
        # WoW beendet -> übernehmen
        self.lap.running = False
        self.assertTrue(self.lap.sync.pull(now=T0 + 1100))
        self.assertIn('"v"] = 2', self.lap.read("SavedVariables/RaidMaster.lua"))

    def test_sy3_konflikt_neuere_gewinnt_ahsentinel_paket(self):
        # gemeinsamer Ausgangsstand
        self.pc.write("SavedVariables/AHSentinel.lua", AH_PC.replace("256", "1"), T0)
        self.pc.write("SavedVariables/Other.lua", "OtherDB = { 1 }\n", T0)
        self.pc.sync.push(now=T0 + 200)
        self.lap.sync.pull(now=T0 + 250)
        # an beiden Rechnern gespielt, ohne Abgleich dazwischen: Laptop 15:43, PC 18:10
        self.lap.write("SavedVariables/AHSentinel.lua", AH_LAPTOP, T0 + 1000)
        self.lap.write("SavedVariables/Other.lua", "OtherDB = { 2 }\n", T0 + 1000)
        self.lap.sync.push(now=T0 + 1200)
        self.pc.write("SavedVariables/AHSentinel.lua", AH_PC, T0 + 5000)
        self.pc.sync.pull(now=T0 + 5200)
        text = self.pc.read("SavedVariables/AHSentinel.lua")
        blocks = sync.top_blocks(text)
        self.assertIn('["n"] = 256', blocks["AHSentinelDB"])          # neuere (PC) gewinnt
        self.assertIn("AHSentinelMerge", blocks)                      # ältere (Laptop) als Zusammenführungs-Paket
        self.assertIn('["n"] = 85', blocks["AHSentinelMerge"])
        self.assertIn('["von"] = "Laptop"', blocks["AHSentinelMerge"])
        self.assertNotIn("AHSentinelMerge", blocks["AHSentinelDB"])
        # Other.lua nur am Laptop geändert -> übernommen, kein Konflikt
        self.assertEqual(self.pc.read("SavedVariables/Other.lua"), "OtherDB = { 2 }\n")
        self.assertTrue(any(b.endswith("AHSentinel.lua.Laptop") for b in self.pc.backups()))
        msg = [l for l in self.pc.logs if "beide geändert" in l]
        self.assertEqual(len(msg), 1)
        self.assertIn("AHSentinel.lua: Laptop", msg[0])
        self.assertIn("PC-Stand übernommen, Laptop-Stand gesichert", msg[0])
        # danach hochladen: ab 2.3.0 OHNE den offenen Block (offen 3) – der Laptop führt nichts doppelt zusammen
        self.pc.sync.push(now=T0 + 5400)
        self.lap.sync.pull(now=T0 + 5500)
        self.assertNotIn("AHSentinelMerge", self.lap.read("SavedVariables/AHSentinel.lua"))
        self.assertIn('["n"] = 256', self.lap.read("SavedVariables/AHSentinel.lua"))
        self.assertIn("AHSentinelMerge", self.pc.read("SavedVariables/AHSentinel.lua"))

    def test_sy3b_konflikt_lokal_neuer(self):
        self.pc.write("SavedVariables/A.lua", "A = 1\n", T0)
        self.pc.sync.push(now=T0 + 200)
        self.lap.sync.pull(now=T0 + 250)
        self.pc.write("SavedVariables/A.lua", "A = 2\n", T0 + 1000)
        self.pc.sync.push(now=T0 + 1200)
        self.lap.write("SavedVariables/A.lua", "A = 3\n", T0 + 3000)
        self.lap.sync.pull(now=T0 + 3200)
        self.assertEqual(self.lap.read("SavedVariables/A.lua"), "A = 3\n")     # Laptop neuer: bleibt
        self.assertTrue(any(b.endswith("A.lua.PC") for b in self.lap.backups()))
        self.lap.sync.push(now=T0 + 3400)
        self.assertEqual(self.store.index["machine"], "Laptop")

    def test_sy4_nur_lua_keine_namen_im_log(self):
        self.pc.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = {}\n", T0)
        self.pc.write("SavedVariables/RaidMaster.lua.bak", "alt\n", T0)
        self.pc.write("Config.wtf", "SET x 1\n", T0)
        self.pc.write("Realm/Figur/macros-cache.txt", "x\n", T0)
        self.pc.write("Realm/Figur/bindings-cache.wtf", "x\n", T0)
        self.pc.sync.push(now=T0 + 200)
        blob = b"".join(self.store.parts[p] for p in sync.index_parts(self.store.index))
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
            names = sorted(m.name for m in tar.getmembers())
        self.assertEqual(names, ["files/SavedVariables/RaidMaster.lua", "manifest.json"])
        log = "\n".join(self.pc.logs + [self.pc.sync.status_line()])
        self.assertNotIn("Figur", log)
        self.assertNotIn("KONTO", log)
        self.assertNotIn("https://", log)
        # ein bösartiges Paket schreibt nie ausserhalb
        evil = sync.make_package({"../../evil.lua": {"data": b"x", "mtime": T0}}, "X", T0)
        _, files = sync.read_package(evil)
        self.assertEqual(files, {})

    def test_sy5_kein_netz(self):
        self.pc.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { 1 }\n", T0)
        self.pc.sync.push(now=T0 + 200)
        self.lap.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { 0 }\n", T0 - 10)
        self.store.online = False
        self.assertFalse(self.lap.sync.pull(now=T0 + 300))
        self.assertEqual(self.lap.read("SavedVariables/RaidMaster.lua"), "RaidMasterDB = { 0 }\n")
        self.assertTrue(any("kein Netz" in l and "unverändert" in l for l in self.lap.logs))
        self.assertIn("FEHLER", self.lap.sync.status_line())
        self.assertFalse(self.lap.sync.push(now=T0 + 400))
        self.store.online = True
        self.assertTrue(self.lap.sync.pull(now=T0 + 500))
        self.assertNotIn("FEHLER", self.lap.sync.status_line())

    def test_sy6_hoechstens_10_fassungen(self):
        for i in range(13):
            self.pc.write("SavedVariables/A.lua", f"A = {i}\n", T0 + i * 1000)
            self.assertTrue(self.pc.sync.push(now=T0 + i * 1000 + 200))
        self.assertEqual(len(self.store.index["h"]) + 1, sync.VERSIONS_KEEP)     # aktueller Stand + 9 ältere
        self.assertEqual(len(self.store.parts), sync.VERSIONS_KEEP)
        self.assertEqual(len(self.store.deleted), 3)


class Sofort(unittest.TestCase):
    """2.2.0 (S8): sofort und ohne Klick – T-SY7 … T-SY10; offene Punkte 1, 2, 5 – T-SY11 … T-SY13."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.store = FakeStore()
        self.pc = Machine(self.d, "PC", self.store)
        self.lap = Machine(self.d, "Laptop", self.store)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_sy7_wow_beendet_hoch_in_15s(self):
        pc = self.pc
        pc.running = True
        pc.sync.tick(now=T0)                                    # WoW läuft
        pc.write("SavedVariables/AHSentinel.lua", AH_PC, T0 + 100)  # beim Beenden geschrieben
        pc.running = False                                      # Prozess weg bei T0+101
        done = None
        for t in range(101, 140, 5):                            # Hauptschleife alle 5 s
            pc.sync.tick(now=T0 + t)
            if self.store.index.get("seq"):
                done = t
                break
        self.assertIsNotNone(done)
        self.assertLessEqual(done - 101, 15)
        # Ausloggen ins Charakter-Menü / /reload (WoW bleibt offen): ab 2.3.0 nach 10 s Ruhe hoch, nichts geschrieben
        pc.running = True
        pc.sync.tick(now=T0 + 300)
        fn = pc.write("SavedVariables/AHSentinel.lua", AH_PC.replace("256", "257"), T0 + 310)
        before = os.path.getmtime(fn)
        pc.sync.tick(now=T0 + 315)
        self.assertEqual(self.store.index["seq"], 1)
        pc.sync.tick(now=T0 + 325)
        self.assertEqual(self.store.index["seq"], 2)
        self.assertEqual(os.path.getmtime(fn), before)

    def test_sy8_anderer_rechner_holt_in_45s_nur_index(self):
        lap = self.lap
        for t in range(0, 61, 5):
            lap.sync.tick(now=T0 + t)
        self.assertEqual(self.store.gets, 0)                    # nichts Neues: nur die Index-Nachricht
        self.assertLessEqual(self.store.reads, 3)               # alle 30 s, nicht alle 5 s
        self.pc.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { 9 }\n", T0 + 50)
        self.assertTrue(self.pc.sync.push(now=T0 + 62))
        got = None
        for t in range(65, 130, 5):
            lap.sync.tick(now=T0 + t)
            if os.path.exists(os.path.join(lap.acc, "SavedVariables", "RaidMaster.lua")):
                got = t
                break
        self.assertIsNotNone(got)
        self.assertLessEqual(got - 62, 45)

    def _start_wow_lap(self, t):
        self.lap.running = False
        self.lap.sync.tick(now=T0 + t)                          # kurz vorher: kein WoW
        self.pc.sync.push(now=T0 + t + 2)
        self.lap.running = True
        self.lap.sync.tick(now=T0 + t + 5)                      # neuer WoW-Prozess

    def test_sy9_wow_ohne_starter_uebernahme_vor_dem_einloggen(self):
        self.pc.write("SavedVariables/RaidMaster.lua", 'RaidMasterDB = {\n\t["v"] = 2,\n}\n', T0)
        self.pc.write("SavedVariables/AHSentinel.lua", AH_PC, T0)
        self.lap.write("SavedVariables/RaidMaster.lua", 'RaidMasterDB = {\n\t["v"] = 1,\n}\n', T0 - 900)
        self._start_wow_lap(90)
        text = self.lap.read("SavedVariables/RaidMaster.lua")
        self.assertIn('["v"] = 2', text)
        self.assertIn("RaidMasterSyncProbe", text)              # Prüfblock für den Beleg
        self.assertIn(AH_PC, self.lap.read("SavedVariables/AHSentinel.lua"))
        self.assertIn("bitte noch nicht einloggen", self.lap.notes[0])
        self.assertIn("du kannst einloggen", self.lap.notes[-1])
        self.assertTrue(any(b.endswith("RaidMaster.lua") for b in self.lap.backups()))
        # Prüfblock zählt nicht als Änderung (nicht hochladen)
        self.assertEqual(self.lap.sync.local_changes(now=T0 + 200)[0], [])
        # RaidMaster 3.0.23 merkt beim Einloggen den Prüfblock, WoW speichert beim Beenden
        seq = self.lap.sync.s["probe"]["seq"]
        self.lap.write("SavedVariables/RaidMaster.lua", 'RaidMasterDB = {\n\t["v"] = 2,\n\t["syncProbe"] = {\n'
                       '\t\t["seq"] = %d,\n\t\t["von"] = "Laptop",\n\t\t["geladen"] = %d,\n\t},\n}\n'
                       % (seq, T0 + 120), T0 + 400)
        self.lap.running = False
        self.lap.sync.tick(now=T0 + 405)
        msg = [l for l in self.lap.logs if "Messung" in l]
        self.assertEqual(len(msg), 1)
        self.assertIn("25 s nach dem WoW-Start", msg[0])
        self.assertIn("Beleg 1/2", msg[0])
        self.assertNotIn("probe", self.lap.sync.s)
        # nach 2 Belegen still
        self.lap.sync.s["proofs"], self.lap.sync.s["takeover_armed"] = 2, True
        self.pc.write("SavedVariables/RaidMaster.lua", 'RaidMasterDB = {\n\t["v"] = 3,\n}\n', T0 + 1500)
        n = len(self.lap.notes)
        self._start_wow_lap(1600)
        self.assertIn('["v"] = 3', self.lap.read("SavedVariables/RaidMaster.lua"))
        self.assertEqual(len(self.lap.notes), n)

    def test_sy9b_nicht_sicher_nur_hinweis(self):
        self.pc.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { 2 }\n", T0)
        self.lap.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { 1 }\n", T0 - 900)
        # Uploader startet, während WoW schon läuft (Start unbekannt): nichts überschreiben
        self.pc.sync.push(now=T0 + 10)
        self.lap.running = True
        self.lap.sync.tick(now=T0 + 20)
        self.lap.sync.tick(now=T0 + 200)
        self.assertEqual(self.lap.read("SavedVariables/RaidMaster.lua"), "RaidMasterDB = { 1 }\n")
        self.assertIn("WoW beenden, dann übernehmen", self.lap.notes[-1])
        # neuer Start, aber seit dem Start schon gespeichert (z. B. Ausloggen): nichts überschreiben
        store2 = FakeStore()
        pc2 = Machine(os.path.join(self.d, "2"), "PC", store2)
        lap2 = Machine(os.path.join(self.d, "2"), "Laptop", store2)
        lap2.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { 1 }\n", T0 - 900)
        lap2.sync.tick(now=T0 + 300)
        lap2.running = True
        lap2.sync.tick(now=T0 + 305)
        lap2.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { 5 }\n", T0 + 310)
        pc2.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { 2 }\n", T0 + 311)
        pc2.sync.push(now=T0 + 312)
        lap2.sync.next_remote = 0
        lap2.sync.tick(now=T0 + 315)
        self.assertEqual(lap2.read("SavedVariables/RaidMaster.lua"), "RaidMasterDB = { 5 }\n")
        self.assertIn("WoW beenden", lap2.notes[-1])

    def test_sy9c_beleg_fehlgeschlagen(self):
        self.pc.write("SavedVariables/RaidMaster.lua", 'RaidMasterDB = {\n\t["v"] = 2,\n}\n', T0)
        self.pc.write("SavedVariables/AHSentinel.lua", AH_PC, T0)
        self.lap.write("SavedVariables/RaidMaster.lua", 'RaidMasterDB = {\n\t["v"] = 1,\n}\n', T0 - 900)
        self.lap.write("SavedVariables/AHSentinel.lua", AH_LAPTOP, T0 - 900)
        self._start_wow_lap(90)
        # WoW hatte den alten Stand schon gelesen und schreibt ihn beim Beenden zurück
        self.lap.write("SavedVariables/RaidMaster.lua", 'RaidMasterDB = {\n\t["v"] = 1,\n}\n', T0 + 400)
        self.lap.write("SavedVariables/AHSentinel.lua", AH_LAPTOP, T0 + 400)
        self.lap.running = False
        self.lap.sync.tick(now=T0 + 405)
        self.assertTrue(self.lap.sync.s.get("takeover_failed"))
        self.assertIn("zu spät", self.lap.notes[-1])
        blocks = sync.top_blocks(self.lap.read("SavedVariables/AHSentinel.lua"))
        self.assertIn('["n"] = 256', blocks.get("AHSentinelMerge", ""))      # PC-Stand wird zusammengeführt
        # nie wieder bei laufendem WoW übernehmen
        self.pc.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { 7 }\n", T0 + 500)
        self._start_wow_lap(600)
        self.assertNotIn("{ 7 }", self.lap.read("SavedVariables/RaidMaster.lua"))

    def test_sy10_uhr_20_min_falsch(self):
        store = FakeStore()
        pc = Machine(os.path.join(self.d, "u"), "PC", store)
        lap = Machine(os.path.join(self.d, "u"), "Laptop", store, clock=-1200)   # Laptop-Uhr 20 Min. vor
        pc.write("SavedVariables/A.lua", "A = 1\n", T0)
        pc.write("SavedVariables/AHSentinel.lua", AH_PC.replace("256", "1"), T0)
        pc.sync.push(now=T0 + 200)
        lap.sync.pull(now=T0 + 1450)
        # Laptop ändert um echte T0+1000 (seine Uhr: T0+2200), PC um echte T0+2000
        lap.write("SavedVariables/A.lua", "A = 2\n", T0 + 2200)
        lap.sync.push(now=T0 + 2300)
        pc.write("SavedVariables/A.lua", "A = 3\n", T0 + 2000)
        pc.sync.pull(now=T0 + 2100)
        self.assertEqual(pc.read("SavedVariables/A.lua"), "A = 3\n")          # nach Datei-Zeit hätte der Laptop gewonnen
        self.assertTrue(any(b.endswith("A.lua.Laptop") for b in pc.backups()))
        pc.sync.push(now=T0 + 2150)
        lap.sync.pull(now=T0 + 3400)
        # weniger als 10 Min. auseinander -> Konflikt: schon hochgeladener Stand gewinnt, AHSentinel führt zusammen
        lap.write("SavedVariables/AHSentinel.lua", AH_LAPTOP, T0 + 4200)       # echte T0+3000
        lap.sync.push(now=T0 + 4300)
        pc.write("SavedVariables/AHSentinel.lua", AH_PC, T0 + 3300)
        pc.sync.pull(now=T0 + 3400)
        blocks = sync.top_blocks(pc.read("SavedVariables/AHSentinel.lua"))
        self.assertIn('["n"] = 85', blocks["AHSentinelDB"])
        self.assertIn('["n"] = 256', blocks["AHSentinelMerge"])
        self.assertTrue(any("innerhalb von 10 Min." in l for l in pc.logs))

    def test_sy11_erster_abgleich_beide_mit_daten(self):
        self.pc.write("SavedVariables/AHSentinel.lua", AH_PC, T0 + 5000)
        self.lap.write("SavedVariables/AHSentinel.lua", AH_LAPTOP, T0 + 1000)
        self.pc.sync.push(now=T0 + 5200)
        self.assertTrue(self.lap.sync.pull(now=T0 + 5300))
        blocks = sync.top_blocks(self.lap.read("SavedVariables/AHSentinel.lua"))
        self.assertIn('["n"] = 256', blocks["AHSentinelDB"])
        self.assertIn('["n"] = 85', blocks["AHSentinelMerge"])
        self.assertTrue(any("beide geändert (noch nie abgeglichen)" in l for l in self.lap.logs))
        # Konflikt-Sicherung bleibt, auch nach vielen gewöhnlichen Sicherungen – aber nicht länger als 30 Tage
        for i in range(7):
            self.lap.sync._backup({"SavedVariables/X.lua": b"x"}, T0 + 6000 + i, "vor-abgleich")
        root = os.path.join(self.lap.acc, sync.BACKUP_DIR)
        dirs = os.listdir(root)
        self.assertEqual(sum(d.endswith("vor-abgleich") for d in dirs), sync.BACKUPS_KEEP)
        self.assertEqual(sum(d.endswith("konflikt") for d in dirs), 1)
        self.lap.sync._backup({"SavedVariables/X.lua": b"x"}, T0 + 31 * 86400, "vor-abgleich")
        self.assertFalse(any(d.endswith("konflikt") for d in os.listdir(root)))

    def test_sy11b_alte_sicherung_einmal_zusammenfuehren(self):
        self.lap.write("SavedVariables/AHSentinel.lua", AH_PC, T0)
        old = os.path.join(self.lap.acc, sync.BACKUP_DIR, "20261111-150000-vor-abgleich", "SavedVariables")
        os.makedirs(old)
        with open(os.path.join(old, "AHSentinel.lua"), "w", encoding="utf-8") as f:
            f.write(AH_LAPTOP)
        self.assertEqual(self.lap.sync.merge_old_backups(now=T0 + 10), 1)
        self.assertIn('["n"] = 85', sync.top_blocks(self.lap.read("SavedVariables/AHSentinel.lua"))["AHSentinelMerge"])
        self.assertEqual(self.lap.sync.merge_old_backups(now=T0 + 20), 0)

    def test_sy12_nur_ein_prozess_gleicht_ab(self):
        here = os.path.join(self.d, "uploader")
        os.makedirs(here)
        self.assertFalse(sync.lock_active(here, T0))
        with open(os.path.join(here, sync.LOCK_FILE), "w") as f:
            json.dump({"pid": -1, "t": T0}, f)                         # laufender Uploader (anderer Prozess)
        self.assertTrue(sync.lock_active(here, T0 + 30))
        self.assertFalse(sync.lock_active(here, T0 + 300))              # Uploader abgestürzt: Sperre alt
        sync.write_lock(here, T0)
        self.assertFalse(sync.lock_active(here, T0 + 1))                # eigene Sperre zählt nicht
        sync.remove_lock(here)
        self.assertFalse(os.path.exists(os.path.join(here, sync.LOCK_FILE)))
        import uploader                                                 # Starter fragt die Sperre ab
        with open(uploader.__file__, encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("def wow_start"):src.index("def main")]
        self.assertLess(body.index("instance_running"), body.index("sy.pull()"))   # ab 2.3.2 (prüft auch die Sperre)

    def test_sy13_unveraenderte_dateien_nicht_neu_lesen(self):
        self.pc.write("SavedVariables/AHSentinel.lua", AH_PC, T0)
        calls = []
        orig = sync.read
        sync.read = lambda fn: calls.append(fn) or orig(fn)
        try:
            self.pc.sync.local_changes()
            n = len(calls)
            self.pc.sync.local_changes()
            self.pc.sync.local_changes()
            self.assertEqual(len(calls), n)
            self.pc.write("SavedVariables/AHSentinel.lua", AH_PC + "-- x\n", T0 + 5)
            self.pc.sync.local_changes()
            self.assertEqual(len(calls), n + 1)
        finally:
            sync.read = orig


class Reload(unittest.TestCase):
    """2.3.0: Abgleich-Upload bei jedem /reload (T-DU5), alte Fassungen wirklich löschen (T-DU6), offene Punkte 1–3."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.store = FakeStore()
        self.pc = Machine(self.d, "PC", self.store)
        self.lap = Machine(self.d, "Laptop", self.store)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_du5_sync_jeder_reload(self):
        pc = self.pc
        pc.running = True
        pc.sync.tick(now=T0)
        for i, t in enumerate((100, 220)):                      # zwei /reload im Abstand von 2 Min.
            pc.write("SavedVariables/AHSentinel.lua", AH_PC.replace("256", str(300 + i)), T0 + t)
            for dt in range(0, 20, 5):
                pc.sync.tick(now=T0 + t + dt)
            self.assertEqual(self.store.index["seq"], i + 1)
        # /reload ohne Änderung (Datei neu geschrieben, gleicher Inhalt) -> nichts hoch
        pc.write("SavedVariables/AHSentinel.lua", AH_PC.replace("256", "301"), T0 + 400)
        for dt in range(0, 30, 5):
            pc.sync.tick(now=T0 + 400 + dt)
        self.assertEqual(self.store.index["seq"], 2)
        # zwei /reload innerhalb einer Minute -> höchstens 1 Upload je Minute, die letzte Fassung gewinnt
        pc.write("SavedVariables/AHSentinel.lua", AH_PC.replace("256", "310"), T0 + 500)
        pc.sync.tick(now=T0 + 511)
        pc.write("SavedVariables/AHSentinel.lua", AH_PC.replace("256", "311"), T0 + 520)
        for dt in range(531, 600, 5):
            pc.sync.tick(now=T0 + dt)
        self.assertEqual(self.store.index["seq"], 4)
        files = sync.read_package(b"".join(self.store.parts[p] for p in sync.index_parts(self.store.index)))[1]
        self.assertIn(b'["n"] = 311', files["SavedVariables/AHSentinel.lua"])

    def test_du6_alte_fassungen_wirklich_loeschen(self):
        fail = {"on": True}
        orig = self.store.delete_part

        def delete(mid):
            if fail["on"]:
                return False                                    # Discord nicht erreichbar
            orig(mid)
            return True
        self.store.delete_part = delete
        for i in range(12):
            self.pc.write("SavedVariables/A.lua", f"A = {i}\n", T0 + i * 1000)
            self.assertTrue(self.pc.sync.push(now=T0 + i * 1000 + 200))
        self.assertEqual(len(self.pc.sync.s["to_delete"]), 2)  # gemerkt, nicht vergessen
        self.assertEqual(len(self.store.parts), 12)
        fail["on"] = False
        self.pc.sync.tick(now=T0 + 20000)
        self.assertEqual(self.pc.sync.s["to_delete"], [])
        self.assertEqual(len(self.store.parts), sync.VERSIONS_KEEP)
        kept = set(sync.index_parts(self.store.index)) | {p for h in self.store.index["h"] for p in h}
        self.assertEqual(set(self.store.parts), kept)

    def test_sy11c_sicherung_am_ort_von_2_1_0(self):
        roots = {"_forever_/KONTO": self.lap.acc}
        st = {}
        logs = []
        lap = sync.Sync(self.store, roots, st, lambda: None, "Laptop", logs.append, lambda: False,
                        backup_dir=os.path.join(self.d, "uploader", sync.BACKUP_DIR))
        lap.s["merge_cutoff"] = T0 + 10 ** 6
        self.lap.write("SavedVariables/AHSentinel.lua", AH_PC, T0)
        for name, text in (("20261111-150000-vor-abgleich", AH_LAPTOP),
                           ("20261110-120000-vor-abgleich", AH_LAPTOP.replace("85", "40")),
                           ("20261111-160000-vor-abgleich", AH_PC)):     # gleich wie jetzt -> nichts
            d = os.path.join(self.lap.acc, sync.BACKUP_DIR, name, "SavedVariables")
            os.makedirs(d)
            with open(os.path.join(d, "AHSentinel.lua"), "w", encoding="utf-8") as f:
                f.write(text)
        self.assertEqual(lap.merge_old_backups(now=T0 + 10), 1)
        merged = sync.top_blocks(self.lap.read("SavedVariables/AHSentinel.lua"))["AHSentinelMerge"]
        self.assertIn('["n"] = 85', merged)
        self.assertTrue(any("folgen nach dem nächsten Login" in l for l in logs))
        # AHSentinel hat den Block eingelesen -> beim nächsten Lauf die zweite Sicherung
        self.lap.write("SavedVariables/AHSentinel.lua", AH_PC.replace("256", "341"), T0 + 100)
        self.assertEqual(lap.merge_old_backups(now=T0 + 200), 1)
        self.assertIn('["n"] = 40', sync.top_blocks(self.lap.read("SavedVariables/AHSentinel.lua"))["AHSentinelMerge"])
        self.lap.write("SavedVariables/AHSentinel.lua", AH_PC.replace("256", "381"), T0 + 300)
        self.assertEqual(lap.merge_old_backups(now=T0 + 400), 0)       # alles erledigt, nie doppelt
        # Sicherungen nach dem ersten Lauf von 2.3.0 werden nie so angehängt
        lap.s["merge_cutoff"] = T0 - 10 * 86400
        lap.s["merged_backups"] = []
        self.assertEqual(lap.merge_old_backups(now=T0 + 500), 0)

    def test_offen2_uploader_wartet_auf_sperre(self):
        here = os.path.join(self.d, "u")
        os.makedirs(here)
        clock = {"t": T0}
        with open(os.path.join(here, sync.LOCK_FILE), "w") as f:
            json.dump({"pid": -1, "t": T0}, f)                     # Starter gleicht gerade ab
        sleeps = []

        def sleep(n):
            sleeps.append(n)
            clock["t"] += n
            if clock["t"] >= T0 + 6:
                os.remove(os.path.join(here, sync.LOCK_FILE))   # Starter fertig
        logs = []
        self.assertTrue(sync.wait_for_lock(here, sleep=sleep, now=lambda: clock["t"], log=logs.append))
        self.assertEqual(len(sleeps), 3)
        self.assertEqual(len(logs), 1)
        import uploader
        with open(uploader.__file__, encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("def main"):]
        self.assertLess(body.index("wait_for_lock"), body.index("syncer.pull()"))

    def test_offen3_offener_block_bleibt_bei_uebernahme(self):
        self.pc.write("SavedVariables/AHSentinel.lua", AH_PC, T0)
        self.pc.sync.push(now=T0 + 100)
        self.lap.sync.pull(now=T0 + 200)
        # Laptop hat einen offenen Block (noch nicht eingelesen), PC spielt weiter
        self.lap.write("SavedVariables/AHSentinel.lua", AH_PC + 'AHSentinelMerge = {\n\t["db"] = { ["n"] = 85 },\n}\n',
                       T0 + 300)
        self.lap.sync.tick(now=T0 + 400)
        self.assertEqual(self.store.index["seq"], 1)                  # Block allein ist keine Änderung
        self.pc.write("SavedVariables/AHSentinel.lua", AH_PC.replace("256", "300"), T0 + 500)
        self.pc.sync.push(now=T0 + 600)
        self.lap.sync.pull(now=T0 + 700)
        text = self.lap.read("SavedVariables/AHSentinel.lua")
        self.assertIn('["n"] = 300', sync.top_blocks(text)["AHSentinelDB"])
        self.assertIn('["n"] = 85', sync.top_blocks(text)["AHSentinelMerge"])


class ZweiterProzess(unittest.TestCase):
    """2.3.2: T-DU11 – Meldung "Neuerer Stand vom <eigener Rechner>" durch einen zweiten Uploader-Prozess."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.store = FakeStore()
        self.pc = Machine(self.d, "PC", self.store)
        self.lap = Machine(self.d, "Laptop", self.store)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def second_process(self, st):
        """Zweiter Prozess am selben Rechner (gleicher Name, gleicher Ordner) mit älterem Zustand."""
        notes, logs = [], []
        sy = sync.Sync(self.store, self.pc.acc, json.loads(json.dumps(st)), lambda: None, "PC", logs.append,
                       is_wow_running=lambda: True, notify=notes.append)
        return sy, notes, logs

    def test_du11_eigener_upload_nie_neuer(self):
        # Ablauf vom 13.11.: Laptop-Stand übernehmen, eigenen Stand hochladen, WoW starten
        self.lap.write("SavedVariables/AHSentinel.lua", AH_LAPTOP, T0)
        self.lap.sync.push(now=T0 + 100)
        self.assertTrue(self.pc.sync.pull(now=T0 + 200))
        old_state = json.loads(json.dumps(self.pc.st))                     # Zustand des zweiten Prozesses
        self.pc.write("SavedVariables/AHSentinel.lua", AH_PC, T0 + 300)
        self.assertTrue(self.pc.sync.push(now=T0 + 400))
        self.assertEqual(self.pc.sync.pending(), [])                     # pull, push -> nichts offen
        b, notes, logs = self.second_process(old_state)
        for t in range(500, 1500, 30):                                    # WoW läuft, Uploader prüft weiter
            b.next_remote = 0
            b.tick(now=T0 + t)
        self.assertEqual(b.pending(), [])
        self.assertEqual(notes, [])
        self.assertFalse(any("Neuerer Stand" in l for l in logs))
        self.assertIn("dieser Rechner aktuell", b.status_line())

    def test_du11_meldung_nennt_anderen_rechner_einmal(self):
        self.pc.sync.tick(now=T0)
        self.pc.running = True
        self.pc.sync.tick(now=T0 + 200)                                   # WoW läuft schon (kein frischer Start)
        self.lap.write("SavedVariables/AHSentinel.lua", AH_LAPTOP, T0 + 300)
        self.lap.sync.push(now=T0 + 400)
        for t in range(500, 1200, 30):
            self.pc.sync.next_remote = 0
            self.pc.sync.tick(now=T0 + t)
        self.assertEqual(len(self.pc.notes), 1)
        self.assertIn("vom Laptop", self.pc.notes[0])
        self.assertIn("Konto", self.pc.notes[0])                          # Spielversion/Konto genannt
        self.assertNotIn("vom PC", self.pc.notes[0])
        # der PC lädt selbst etwas hoch (anderes Konto) -> keine neue Meldung
        # neuer Stand des Laptops -> genau eine weitere Meldung
        self.lap.write("SavedVariables/AHSentinel.lua", AH_LAPTOP.replace("85", "86"), T0 + 1300)
        self.lap.sync.push(now=T0 + 1400)
        for t in range(1500, 1800, 30):
            self.pc.sync.next_remote = 0
            self.pc.sync.tick(now=T0 + t)
        self.assertEqual(len(self.pc.notes), 2)
        # Neustart des Uploaders (gleicher Zustand) -> derselbe Stand wird nicht nochmals gemeldet
        b, notes, _ = self.second_process(self.pc.st)
        b.next_remote = 0
        b.tick(now=T0 + 1900)
        b.next_remote = 0
        b.tick(now=T0 + 1950)
        self.assertEqual(notes, [])

    def test_du11_nur_ein_uploader(self):
        info = os.path.join(self.d, "instanz.json")
        here = os.path.join(self.d, "u")
        os.makedirs(here)
        ok, other = sync.instance_acquire(here, "2.3.2", path=info)
        self.assertTrue(ok)
        self.assertEqual(sync.instance_info(info)["pid"], os.getpid())
        # ein anderer, laufender Prozess hält die Instanz (hier: der Elternprozess dieses Tests)
        with open(info, "w") as f:
            json.dump({"pid": os.getppid(), "ordner": "C:/alt/RaidMasterUploader", "version": "2.3.0"}, f)
        ok, other = sync.instance_acquire(here, "2.3.2", path=info)
        self.assertFalse(ok)
        self.assertEqual(other["ordner"], "C:/alt/RaidMasterUploader")
        self.assertTrue(sync.instance_running(here, path=info))
        # beendeter Prozess -> frei
        with open(info, "w") as f:
            json.dump({"pid": 999999, "ordner": "x"}, f)
        self.assertIsNone(sync.instance_running(here, path=info))
        # Uploader vor 2.3.2 im selben Ordner (frische Abgleich-Sperre eines anderen Prozesses)
        with open(os.path.join(here, sync.LOCK_FILE), "w") as f:
            json.dump({"pid": -1, "t": __import__("time").time()}, f)
        self.assertTrue(sync.instance_running(here, path=info))
        import uploader
        with open(uploader.__file__, encoding="utf-8") as f:
            src = f.read()
        main = src[src.index("def main"):]
        self.assertLess(main.index("instance_acquire"), main.index("load_config()"))
        self.assertIn("PID {os.getpid()}", main)
        starter = src[src.index("def wow_start"):src.index("def main")]
        self.assertLess(starter.index("instance_running"), starter.index("sy.pull()"))
        self.assertIn("notify=notify_logged", src)                         # jeder Hinweis steht im Fenster
        with open(os.path.join(os.path.dirname(uploader.__file__), "Autostart-einrichten.bat"), encoding="utf-8") as f:
            bat = f.read()
        self.assertIn("Remove-Item", bat)                                   # alte/doppelte Einträge ersetzen


class Groesse(unittest.TestCase):
    """2.2.0 (S8 e) und Index v1 von 2.1.x – T-SY14, T-SY15."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.store = FakeStore()
        self.puts = []
        orig = self.store.put_part
        self.store.put_part = lambda name, blob, note: self.puts.append(note) or orig(name, blob, note)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def acc(self, flavor, machine="PC"):
        a = os.path.join(self.d, machine, flavor, "WTF", "Account", "KONTO")
        os.makedirs(os.path.join(a, "SavedVariables"))
        return a

    def put(self, acc, name, text, mtime):
        fn = os.path.join(acc, "SavedVariables", name)
        with open(fn, "w", encoding="utf-8") as f:
            f.write(text)
        os.utime(fn, (mtime, mtime))

    def test_sy14_nur_geaenderte_spielversion_retail_nur_wenn_gespielt(self):
        f, e, r = self.acc("_forever_"), self.acc("_classic_era_"), self.acc("_retail_")
        self.put(f, "A.lua", "A = 1\n", T0)
        self.put(e, "B.lua", "B = 1\n", T0 - 20 * 86400)                   # seit 20 Tagen unverändert
        self.put(r, "C.lua", "C = 1\n", T0 - 20 * 86400)                   # Retail, nicht gespielt
        logs = []
        pc = sync.Sync(self.store, sync.find_roots([os.path.join(self.d, "PC")]), {}, lambda: None, "PC", logs.append,
                       lambda: False, backup_dir=os.path.join(self.d, "bk"))
        self.assertEqual(pc.local_changes(now=T0 + 100)[0], ["_classic_era_/KONTO/SavedVariables/B.lua",
                                                              "_forever_/KONTO/SavedVariables/A.lua"])
        self.assertTrue(pc.push(now=T0 + 100))
        self.assertEqual(sorted(self.store.index["r"]), ["_classic_era_/KONTO", "_forever_/KONTO"])  # Grundstand
        self.assertTrue(any("_retail_" in l and "nicht gespielt" in l for l in logs))
        self.assertFalse(any("KONTO" in l for l in logs))
        n = len(self.puts)
        self.put(f, "A.lua", "A = 2\n", T0 + 200)
        self.assertTrue(pc.push(now=T0 + 300))
        self.assertEqual(len(self.puts), n + 1)                                # nur _forever_ neu
        self.assertIn("_forever_", self.puts[-1])
        self.assertTrue(pc.push(now=T0 + 400))                                 # nichts geändert: nichts hoch
        self.assertEqual(len(self.puts), n + 1)
        self.put(r, "C.lua", "C = 2\n", T0 + 500)                              # jetzt in Retail gespielt
        self.assertTrue(pc.push(now=T0 + 600))
        self.assertIn("_retail_/KONTO", self.store.index["r"])

    def test_sy15_index_von_2_1_x(self):
        files = {"_forever_/KONTO/SavedVariables/A.lua": {"data": b"A = 1\n", "mtime": T0, "machine": "Laptop"},
                 "_anniversary_/KONTO/SavedVariables/R.lua": {"data": b"R = 1\n", "mtime": T0, "machine": "Laptop"}}
        blob = sync.make_package(files, "Laptop", T0)
        mid = self.store.put_part("stand-3-1.bin", blob, "alt")
        self.store.index = {"v": 1, "seq": 3, "machine": "Laptop", "time": T0, "parts": [mid], "history": [[3, [mid]]]}
        f = self.acc("_forever_")
        pc = sync.Sync(self.store, sync.find_roots([os.path.join(self.d, "PC")]), {}, lambda: None, "PC",
                       lambda t: None, lambda: False, backup_dir=os.path.join(self.d, "bk"))
        pc.check_remote(now=T0 + 50)
        self.assertTrue(pc.remote_newer())
        self.assertTrue(pc.pull(now=T0 + 100))
        with open(os.path.join(f, "SavedVariables", "A.lua")) as fh:
            self.assertEqual(fh.read(), "A = 1\n")
        self.put(f, "A.lua", "A = 2\n", T0 + 200)
        self.assertTrue(pc.push(now=T0 + 300))
        self.assertEqual(self.store.index["v"], 2)
        self.assertEqual(sorted(self.store.index["r"]), ["_anniversary_/KONTO", "_forever_/KONTO"])
        got = {}
        for e in sync.index_roots(self.store.index).values():
            got.update(sync.read_package(b"".join(self.store.parts[p] for p in e["parts"]))[1])
        self.assertEqual(got["_anniversary_/KONTO/SavedVariables/R.lua"], b"R = 1\n")   # weitergetragen
        self.assertEqual(got["_forever_/KONTO/SavedVariables/A.lua"], b"A = 2\n")


class FakeDiscord:
    """Ersatz für Discord: Webhook-Nachrichten anlegen, lesen, ändern, löschen; Anhänge über eine CDN-Adresse."""

    def __init__(self):
        self.msgs, self.cdn, self.calls, self.n = {"900": {"id": "900", "content": "GSSYNC-INDEX", "attachments": []}}, {}, [], 900
        self.busy, self.date = 0, None

    def __call__(self, req, timeout=None):
        import re as _re
        url, method = req.full_url, req.get_method()
        self.calls.append((method, url))
        if self.busy:
            self.busy -= 1
            raise sync.urllib.error.HTTPError(url, 429, "Too Many Requests", {}, io.BytesIO(b'{"retry_after": 2.5}'))
        if url.startswith("https://cdn.invalid/"):
            return Resp(self.cdn[url])
        m = _re.match(r"https://discord.invalid/api/webhooks/1/geheim(/messages/(\d+))?(\?wait=true)?$", url)
        assert m, url
        mid = m.group(2)
        if method == "POST":
            body = req.data
            name = _re.search(rb'filename="([^"]+)"', body).group(1).decode()
            data = body.split(b"Content-Type: application/octet-stream\r\n\r\n", 1)[1].rsplit(b"\r\n--", 1)[0]
            self.n += 1
            cdn = f"https://cdn.invalid/{self.n}/{name}?ex=signiert"
            self.cdn[cdn] = data
            self.msgs[str(self.n)] = {"id": str(self.n), "content": "", "attachments": [{"url": cdn}]}
            return Resp(json.dumps(self.msgs[str(self.n)]).encode())
        if method == "GET":
            if mid not in self.msgs:
                raise sync.urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            return Resp(json.dumps(self.msgs[mid]).encode(), {"Date": self.date} if self.date else None)
        if method == "PATCH":
            self.msgs[mid]["content"] = json.loads(req.data)["content"]
            return Resp(json.dumps(self.msgs[mid]).encode())
        if method == "DELETE":
            self.msgs.pop(mid, None)
            return Resp(b"")
        raise AssertionError(method)


class Resp:
    def __init__(self, data, headers=None):
        self.data, self.headers = data, headers

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Webhook(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.fake = FakeDiscord()
        self.orig = sync.urllib.request.urlopen
        sync.urllib.request.urlopen = self.fake

    def tearDown(self):
        sync.urllib.request.urlopen = self.orig
        shutil.rmtree(self.d, ignore_errors=True)

    def test_w1_echter_weg_ueber_webhook(self):
        store = sync.WebhookStore("https://discord.invalid/api/webhooks/1/geheim", "900")
        pc = Machine(self.d, "PC", store)
        lap = Machine(self.d, "Laptop", store)
        pc.write("SavedVariables/RaidMaster.lua", "RaidMasterDB = { 7 }\n", T0)
        self.assertTrue(pc.sync.push(now=T0 + 200))
        self.assertTrue(self.fake.msgs["900"]["content"].startswith("GSSYNC-INDEX"))
        self.assertEqual(store.read_index()["seq"], 1)
        self.assertTrue(lap.sync.pull(now=T0 + 300))
        self.assertEqual(lap.read("SavedVariables/RaidMaster.lua"), "RaidMasterDB = { 7 }\n")
        methods = [m for m, _ in self.fake.calls]
        self.assertIn("PATCH", methods)
        self.assertTrue(all(u.startswith("https://") for _, u in self.fake.calls))
        self.assertFalse(any("geheim" in l for l in pc.logs + lap.logs))

    def test_sy16_discord_bremst_und_uhr(self):
        import email.utils as eu
        import time as _t
        store = sync.WebhookStore("https://discord.invalid/api/webhooks/1/geheim", "900")
        lap = Machine(self.d, "Laptop", store)
        self.fake.busy = 1
        self.assertIsNone(lap.sync.check_remote(now=T0, force=True))
        self.assertTrue(any("Discord bremst" in l for l in lap.logs))
        self.assertGreater(store.wait_until, _t.time() + 1)
        n = len(self.fake.calls)
        lap.sync.next_remote = 0
        lap.sync.tick(now=T0 + 40)                              # wartet, ohne Discord zu fragen
        self.assertEqual(len(self.fake.calls), n)
        store.wait_until = 0
        self.fake.date = eu.formatdate(_t.time() + 1200, usegmt=True)   # Rechner-Uhr 20 Min. nach
        store.read_index()
        self.assertAlmostEqual(store.clock_offset, 1200, delta=5)
        self.assertAlmostEqual(lap.sync.clock_offset(), 1200, delta=5)


class Spielversionen(unittest.TestCase):
    """2.1.1: alle Spielversionen und Konten; was hier nicht installiert ist, wird weitergetragen, nicht gelöscht."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.store = FakeStore()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def acc(self, machine, flavor, base="WoW"):
        a = os.path.join(self.d, machine, base, flavor, "WTF", "Account", "KONTO")
        os.makedirs(os.path.join(a, "SavedVariables"))
        return a

    def put(self, acc, name, text, mtime):
        fn = os.path.join(acc, "SavedVariables", name)
        with open(fn, "w", encoding="utf-8") as f:
            f.write(text)
        os.utime(fn, (mtime, mtime))

    def test_v1_find_roots_und_weitertragen(self):
        pc_f, pc_a = self.acc("PC", "_forever_"), self.acc("PC", "_anniversary_")
        lap_f = self.acc("Laptop", "_forever_", base="Spiele")          # anderer Installationsort
        roots_pc = sync.find_roots([os.path.join(self.d, "PC")])
        self.assertEqual(sorted(roots_pc), ["_anniversary_/KONTO", "_forever_/KONTO"])
        roots_lap = sync.find_roots([os.path.join(self.d, "Laptop")])
        self.assertEqual(sorted(roots_lap), ["_forever_/KONTO"])
        self.put(pc_f, "AHSentinel.lua", "AHSentinelDB = { 256 }\n", T0)
        self.put(pc_a, "RaidMaster.lua", "RaidMasterDB = { alt }\n", T0)
        logs = []
        pc = sync.Sync(self.store, roots_pc, {}, lambda: None, "PC", logs.append, lambda: False,
                       backup_dir=os.path.join(self.d, "bk-pc"))
        lap = sync.Sync(self.store, roots_lap, {}, lambda: None, "Laptop", logs.append, lambda: False,
                        backup_dir=os.path.join(self.d, "bk-lap"))
        self.assertTrue(pc.push(now=T0 + 200))
        self.assertTrue(lap.pull(now=T0 + 300))
        with open(os.path.join(lap_f, "SavedVariables", "AHSentinel.lua"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "AHSentinelDB = { 256 }\n")
        # Anniversary gibt es am Laptop nicht: kein Ordner angelegt
        self.assertFalse(os.path.exists(os.path.join(self.d, "Laptop", "Spiele", "_anniversary_")))
        # Laptop lädt hoch: die Anniversary-Datei des PCs bleibt im Stand
        self.put(lap_f, "AHSentinel.lua", "AHSentinelDB = { 257 }\n", T0 + 1000)
        self.assertTrue(lap.push(now=T0 + 1200))
        files = {}
        for e in sync.index_roots(self.store.index).values():
            files.update(sync.read_package(b"".join(self.store.parts[p] for p in e["parts"]))[1])
        self.assertEqual(sorted(files), ["_anniversary_/KONTO/SavedVariables/RaidMaster.lua",
                                         "_forever_/KONTO/SavedVariables/AHSentinel.lua"])
        self.assertEqual(files["_anniversary_/KONTO/SavedVariables/RaidMaster.lua"], b"RaidMasterDB = { alt }\n")
        # Sicherungen nie im WoW-Ordner (sondern im Uploader-Ordner)
        self.assertFalse(os.path.exists(os.path.join(lap_f, sync.BACKUP_DIR)))
        # neuer Laptop-Prozess (ohne geladenen Stand) verliert die fremde Spielversion ebenfalls nicht
        lap2 = sync.Sync(self.store, roots_lap, json.loads(json.dumps(lap.st)), lambda: None, "Laptop", logs.append,
                         lambda: False, backup_dir=os.path.join(self.d, "bk-lap"))
        self.put(lap_f, "AHSentinel.lua", "AHSentinelDB = { 258 }\n", T0 + 3000)
        self.assertTrue(lap2.push(now=T0 + 3200))
        files = {}
        for e in sync.index_roots(self.store.index).values():
            files.update(sync.read_package(b"".join(self.store.parts[p] for p in e["parts"]))[1])
        self.assertIn("_anniversary_/KONTO/SavedVariables/RaidMaster.lua", files)


if __name__ == "__main__":
    unittest.main()
