"""Offline-Tests Uploader 2.1.0: Abgleich der Addon-Daten zwischen zwei Rechnern (T-SY1 … T-SY5).
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

    def _net(self):
        if not self.online:
            raise sync.StoreError("kein Netz oder Discord nicht erreichbar")

    def read_index(self):
        self._net()
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
        if mid not in self.parts:
            raise sync.StoreError("Paket nicht mehr vorhanden")
        return self.parts[mid]

    def delete_part(self, mid):
        self.deleted.append(mid)
        self.parts.pop(mid, None)


AH_PC = 'AHSentinelDB = {\n\t["deLog"] = {\n\t\t{ ["t"] = 2, ["i"] = 100 },\n\t},\n\t["n"] = 256,\n}\n'
AH_LAPTOP = 'AHSentinelDB = {\n\t["deLog"] = {\n\t\t{ ["t"] = 1, ["i"] = 200 },\n\t},\n\t["n"] = 85,\n}\n'


class Machine:
    def __init__(self, root, name, store):
        self.acc = os.path.join(root, name, "WTF", "Account", "KONTO")
        os.makedirs(os.path.join(self.acc, "SavedVariables"))
        os.makedirs(os.path.join(self.acc, "Realm", "Figur", "SavedVariables"))
        self.st, self.logs, self.notes, self.running = {}, [], [], False
        self.sync = sync.Sync(store, self.acc, self.st, lambda: None, name, self.logs.append,
                              is_wow_running=lambda: self.running, notify=self.notes.append)

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
        # 2 Minuten Ruhe abwarten, dann hoch
        self.pc.sync.tick(now=T0 + 60)
        self.assertEqual(self.store.index, {})
        self.pc.sync.tick(now=T0 + 200)
        self.assertEqual(self.store.index["seq"], 1)
        self.assertEqual(self.store.index["machine"], "PC")
        # Laptop holt vor dem Start; lokale Datei vorher gesichert
        self.assertTrue(self.lap.sync.pull(now=T0 + 300))
        self.assertIn('"v"] = 2', self.lap.read("SavedVariables/RaidMaster.lua"))
        self.assertEqual(self.lap.read("Realm/Figur/SavedVariables/Buff.lua"), "BuffDB = {}\n")
        self.assertTrue(any(b.endswith("SavedVariables/RaidMaster.lua") for b in self.lap.backups()))
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
        self.assertIn("Neuerer Stand vom PC – WoW beenden, dann übernehmen", self.lap.notes[0])
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
        # danach hochladen: der zusammengeführte Stand geht hoch
        self.pc.sync.push(now=T0 + 5400)
        self.lap.sync.pull(now=T0 + 5500)
        self.assertIn("AHSentinelMerge", self.lap.read("SavedVariables/AHSentinel.lua"))

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
        blob = b"".join(self.store.parts[p] for p in self.store.index["parts"])
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
        self.assertEqual(len(self.store.index["history"]), sync.VERSIONS_KEEP)
        self.assertEqual(len(self.store.parts), sync.VERSIONS_KEEP)
        self.assertEqual(len(self.store.deleted), 3)


class FakeDiscord:
    """Ersatz für Discord: Webhook-Nachrichten anlegen, lesen, ändern, löschen; Anhänge über eine CDN-Adresse."""

    def __init__(self):
        self.msgs, self.cdn, self.calls, self.n = {"900": {"id": "900", "content": "GSSYNC-INDEX", "attachments": []}}, {}, [], 900

    def __call__(self, req, timeout=None):
        import re as _re
        url, method = req.full_url, req.get_method()
        self.calls.append((method, url))
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
            return Resp(json.dumps(self.msgs[mid]).encode())
        if method == "PATCH":
            self.msgs[mid]["content"] = json.loads(req.data)["content"]
            return Resp(json.dumps(self.msgs[mid]).encode())
        if method == "DELETE":
            self.msgs.pop(mid, None)
            return Resp(b"")
        raise AssertionError(method)


class Resp:
    def __init__(self, data):
        self.data = data

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
        blob = b"".join(self.store.parts[p] for p in self.store.index["parts"])
        _, files = sync.read_package(blob)
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
        _, files = sync.read_package(b"".join(self.store.parts[p] for p in self.store.index["parts"]))
        self.assertIn("_anniversary_/KONTO/SavedVariables/RaidMaster.lua", files)


if __name__ == "__main__":
    unittest.main()
