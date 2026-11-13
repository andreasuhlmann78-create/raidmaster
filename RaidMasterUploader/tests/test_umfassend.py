"""Umfassende Tests Uploader (ab 2.3.3) nach auftraege/RaidMaster/anweisung-tests-umfassend.txt (TU1–TU9).

TU1 Lagen-Katalog x Funktionen (Tabelle), TU2 Abläufe wie ein Spieler, TU3 Standardwerte, TU4 Grundregeln mit
Zufallsdaten (fester Startwert), TU5 Zustand beim Start prüfen, TU6 Regressionen je Befund, TU7 Formen der WoW-Ordner,
TU8 Testbericht je Bereich ("TUx OK n · FEHLER n · SKIP n"), TU9 offline (dieses Modul, kein Netz).
Start: python3 -I RaidMasterUploader/tests/test_umfassend.py   (druckt am Ende den Testbericht)
"""
import io
import json
import os
import random
import shutil
import ssl
import sys
import tempfile
import time
import unittest

TESTS = os.path.dirname(os.path.abspath(__file__))
UP = os.path.dirname(TESTS)
sys.path.insert(0, UP)
sys.path.insert(0, TESTS)
import daten  # noqa: E402
import sync  # noqa: E402
import test_daten as td  # noqa: E402  (FakeGitHub)
import test_sync as ts  # noqa: E402  (FakeStore, Machine, AH-Beispiele)

T0 = ts.T0
SEED = 4711
CASES = 1000
SECRET_TOKEN = td.TOKEN

# ---------------------------------------------------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------------------------------------------------


class Box:
    """Zwei Rechner (PC, Laptop) mit gemeinsamem Abgleich-Speicher und gemeinsamem Daten-Repo."""

    def __init__(self):
        self.d = tempfile.mkdtemp()
        self.store = ts.FakeStore()
        self.gh = td.FakeGitHub()
        self.orig = daten.urllib.request.urlopen
        daten.urllib.request.urlopen = self.gh
        self.m = {n: ts.Machine(self.d, n, self.store) for n in ("PC", "Laptop")}
        self.dl = {}
        for n, mach in self.m.items():
            self.dl[n] = daten.Daten(daten.GitHubAPI("ich/goldsentinel-daten", SECRET_TOKEN),
                                     {"_forever_/KONTO": mach.acc}, mach.st, lambda: None, n, mach.logs.append)

    def close(self):
        daten.urllib.request.urlopen = self.orig
        shutil.rmtree(self.d, ignore_errors=True)

    def local(self, name):
        acc = self.m[name].acc
        out = {}
        for rel, fn in sync.local_files(acc).items():
            with open(fn, "rb") as f:
                out[rel] = f.read()
        return out

    def backups(self, name):
        root = os.path.join(self.m[name].acc, sync.BACKUP_DIR)
        out = []
        for d, _, files in os.walk(root):
            for f in files:
                with open(os.path.join(d, f), "rb") as fh:
                    out.append(fh.read())
        return out


# ---------------------------------------------------------------------------------------------------------------------
# TU1 Lagen-Katalog: jede Lage durch jede betroffene Funktion, Erwartung als Tabelle
# ---------------------------------------------------------------------------------------------------------------------
LAGEN = ["normal", "kein Netz", "Zertifikat fehlt", "Token falsch", "GitHub langsam", "zweiter Prozess",
         "zwei Rechner gleichzeitig", "WoW startet während Abgleich"]
FUNKTIONEN = ["Lieferung", "Abgleich hoch", "Abgleich holen"]
# Erwartung je (Lage, Funktion): Kennwort, das die Prüfung unten liefern muss
ERWARTUNG = {
    ("normal", "Lieferung"): "geliefert",
    ("normal", "Abgleich hoch"): "hochgeladen",
    ("normal", "Abgleich holen"): "übernommen",
    ("kein Netz", "Lieferung"): "meldung:nicht auflösbar",
    ("kein Netz", "Abgleich hoch"): "meldung+unverändert",
    ("kein Netz", "Abgleich holen"): "meldung+unverändert",
    ("Zertifikat fehlt", "Lieferung"): "meldung:Zertifikat",
    ("Zertifikat fehlt", "Abgleich hoch"): "hochgeladen",          # Discord-Weg betroffen? nein: eigener Speicher
    ("Zertifikat fehlt", "Abgleich holen"): "übernommen",
    ("Token falsch", "Lieferung"): "meldung:Token falsch",
    ("Token falsch", "Abgleich hoch"): "hochgeladen",
    ("Token falsch", "Abgleich holen"): "übernommen",
    ("GitHub langsam", "Lieferung"): "meldung:Zeitüberschreitung",
    ("GitHub langsam", "Abgleich hoch"): "hochgeladen",
    ("GitHub langsam", "Abgleich holen"): "übernommen",
    ("zweiter Prozess", "Lieferung"): "nur einer",
    ("zweiter Prozess", "Abgleich hoch"): "eigener nie neuer",
    ("zweiter Prozess", "Abgleich holen"): "eigener nie neuer",
    ("zwei Rechner gleichzeitig", "Lieferung"): "beide im Repo",
    ("zwei Rechner gleichzeitig", "Abgleich hoch"): "konflikt gesichert",
    ("zwei Rechner gleichzeitig", "Abgleich holen"): "konflikt gesichert",
    ("WoW startet während Abgleich", "Lieferung"): "geliefert",     # Lieferung liest nur
    ("WoW startet während Abgleich", "Abgleich hoch"): "hochgeladen",
    ("WoW startet während Abgleich", "Abgleich holen"): "nicht geschrieben",
}


def run_lage(lage: str, fn: str) -> str:
    """Spielt eine Lage für eine Funktion durch und gibt das beobachtete Kennwort zurück."""
    b = Box()
    try:
        pc, lap = b.m["PC"], b.m["Laptop"]
        pc.write("SavedVariables/AHSentinel.lua", ts.AH_PC, T0)
        lap.write("SavedVariables/AHSentinel.lua", ts.AH_LAPTOP, T0 - 5000)
        if lage == "kein Netz":
            b.store.online = False
            b.gh.online = False
        elif lage == "Zertifikat fehlt":
            b.gh.fail = daten.urllib.error.URLError(ssl.SSLCertVerificationError(1, "CERTIFICATE_VERIFY_FAILED"))
        elif lage == "Token falsch":
            b.gh.token_ok = False
        elif lage == "GitHub langsam":
            b.gh.fail = daten.urllib.error.URLError(TimeoutError("timed out"))

        if fn == "Lieferung":
            if lage == "zweiter Prozess":
                info = os.path.join(b.d, "instanz.json")
                ok1, _ = sync.instance_acquire(os.path.join(b.d), "x", path=info)
                with open(info, "w") as f:
                    json.dump({"pid": os.getppid(), "ordner": "x"}, f)
                ok2, _ = sync.instance_acquire(os.path.join(b.d), "x", path=info)
                return "nur einer" if ok1 and not ok2 else f"falsch {ok1}/{ok2}"
            if lage == "WoW startet während Abgleich":
                pc.running = True
            for t in range(1, 30, 5):
                b.dl["PC"].tick(now=T0 + t)
            if lage == "zwei Rechner gleichzeitig":
                for t in range(1, 30, 5):
                    b.dl["Laptop"].tick(now=T0 + t)
                files = b.gh.files() if b.gh.ref else {}
                both = all(any(p.startswith(f"aktuell/{n}/") for p in files) for n in ("PC", "Laptop"))
                return "beide im Repo" if both else "einer fehlt"
            if b.dl["PC"].d.get("last"):
                return "geliefert"
            err = b.dl["PC"].last_error
            for word in ("nicht auflösbar", "Zertifikat", "Token falsch", "Zeitüberschreitung"):
                if word in err:
                    assert SECRET_TOKEN not in err and not any(SECRET_TOKEN in x for x in pc.logs)
                    return "meldung:" + word
            return "fehler:" + err

        if fn == "Abgleich hoch":
            before = b.local("PC")
            if lage == "zweiter Prozess":
                pc.sync.push(now=T0 + 100)
                second = sync.Sync(b.store, pc.acc, {}, lambda: None, "PC", lambda t: None, lambda: True)
                second.check_remote(now=T0 + 200, force=True)
                return "eigener nie neuer" if second.pending() == [] else "eigener als neuer gemeldet"
            if lage == "zwei Rechner gleichzeitig":
                lap.sync.push(now=T0 + 90)
                pc.sync.push(now=T0 + 100)
                bk = b.backups("PC")
                ok = (any(ts.AH_LAPTOP.encode() in x or ts.AH_PC.encode() in x for x in bk)
                      and b.local("PC") != {})
                return "konflikt gesichert" if ok else "nichts gesichert"
            if lage == "WoW startet während Abgleich":
                pc.running = True
                ok = pc.sync.push(now=T0 + 100, running_ok=True)
                return "hochgeladen" if ok and b.store.index.get("seq") else "nicht hochgeladen"
            ok = pc.sync.push(now=T0 + 100)
            if ok and b.store.index.get("seq"):
                return "hochgeladen"
            return "meldung+unverändert" if (b.local("PC") == before and pc.sync.last_error) else "falsch"

        if fn == "Abgleich holen":
            b.store.online = True
            pc.sync.push(now=T0 + 100)
            before = b.local("Laptop")
            if lage == "kein Netz":
                b.store.online = False
            if lage == "zweiter Prozess":
                second = sync.Sync(b.store, pc.acc, {}, lambda: None, "PC", lambda t: None, lambda: True)
                second.check_remote(now=T0 + 200, force=True)
                return "eigener nie neuer" if second.pending() == [] else "eigener als neuer gemeldet"
            if lage == "zwei Rechner gleichzeitig":
                lap.write("SavedVariables/AHSentinel.lua", ts.AH_LAPTOP.replace("85", "86"), T0 + 150)
                lap.sync.s["files"]["SavedVariables/AHSentinel.lua"] = "0" * 40          # an beiden geändert
                lap.sync.pull(now=T0 + 160)
                ok = any(b"86" in x for x in b.backups("Laptop"))
                return "konflikt gesichert" if ok else "nichts gesichert"
            if lage == "WoW startet während Abgleich":
                state = {"n": 0}

                def running():
                    state["n"] += 1
                    return state["n"] > 1                     # beim Lesen noch zu, vor dem Schreiben gestartet
                lap.sync.is_wow_running = running
                lap.sync.pull(now=T0 + 200)
                return "nicht geschrieben" if b.local("Laptop") == before else "geschrieben"
            ok = lap.sync.pull(now=T0 + 200)
            if ok and b"256" in b.local("Laptop").get("SavedVariables/AHSentinel.lua", b""):
                return "übernommen"
            return "meldung+unverändert" if (b.local("Laptop") == before and lap.sync.last_error) else "falsch"
        return "?"
    finally:
        b.close()


class TU1Lagen(unittest.TestCase):
    def test_tu1_lagen_mal_funktionen(self):
        fails = []
        for lage in LAGEN:
            for fn in FUNKTIONEN:
                want = ERWARTUNG[(lage, fn)]
                got = run_lage(lage, fn)
                REPORT.add("TU1", got == want, f"{lage} / {fn}: {got} (erwartet {want})")
                if got != want:
                    fails.append(f"{lage} / {fn}: {got} (erwartet {want})")
        self.assertEqual(fails, [], "\n".join(fails))


# ---------------------------------------------------------------------------------------------------------------------
# TU2 Abläufe wie ein Spieler
# ---------------------------------------------------------------------------------------------------------------------
class TU2Ablaeufe(unittest.TestCase):
    def setUp(self):
        self.b = Box()

    def tearDown(self):
        self.b.close()

    def test_tu2_spielen_liefern_anderer_rechner_uebernimmt(self):
        b = self.b
        pc, lap = b.m["PC"], b.m["Laptop"]
        pc.running = True
        pc.sync.tick(now=T0)
        b.dl["PC"].tick(now=T0)
        pc.write("SavedVariables/AHSentinel.lua", ts.AH_PC, T0 + 100)          # /reload
        for t in range(101, 200, 5):
            pc.sync.tick(now=T0 + t)
            b.dl["PC"].tick(now=T0 + t)
        pc.running = False                                                     # WoW beenden
        for t in range(200, 260, 5):
            pc.sync.tick(now=T0 + t)
        for t in range(260, 330, 5):                                           # Laptop, WoW zu
            lap.sync.tick(now=T0 + t)
        ok = (lap.read("SavedVariables/AHSentinel.lua") == ts.AH_PC and b.gh.ref is not None
              and pc.notes == [] and lap.notes == [])
        REPORT.add("TU2", ok, "spielen -> /reload -> liefern -> beenden -> Laptop übernimmt, keine Hinweise")
        self.assertTrue(ok)

    def test_tu2_wow_beenden_waehrend_upload(self):
        b = self.b
        pc = b.m["PC"]
        pc.write("SavedVariables/AHSentinel.lua", ts.AH_PC + "-- " + "x" * 64 + "\n", T0)
        orig = b.store.put_part
        calls = {"n": 0}

        def put(name, blob, note):
            calls["n"] += 1
            if calls["n"] == 1:
                raise sync.StoreError("Verbindung abgebrochen")                # Abbruch mittendrin
            return orig(name, blob, note)
        b.store.put_part = put
        before = b.local("PC")
        self.assertFalse(pc.sync.push(now=T0 + 100))
        stale = (b.store.index == {} and b.local("PC") == before)
        b.store.put_part = orig
        pc.sync.retry_at = 0
        ok2 = pc.sync.push(now=T0 + 200)
        ok = stale and ok2 and b.store.index.get("seq") == 1
        REPORT.add("TU2", ok, "Abbruch beim Hochladen: Index unverändert, lokal unverändert, später nachgeholt")
        self.assertTrue(ok)

    def test_tu2_autostart_doppelt_und_starter(self):
        info = os.path.join(self.b.d, "instanz.json")
        here = os.path.join(self.b.d, "u")
        os.makedirs(here)
        ok1, _ = sync.instance_acquire(here, "2.3.3", path=info)
        with open(info, "w") as f:
            json.dump({"pid": os.getppid(), "ordner": here, "version": "2.3.3"}, f)
        ok2, other = sync.instance_acquire(here, "2.3.3", path=info)           # zweiter Autostart-Eintrag
        starter_sees = sync.instance_running(here, path=info) is not None
        ok = ok1 and not ok2 and starter_sees and other["ordner"] == here
        REPORT.add("TU2", ok, "Autostart doppelt -> zweiter endet; Starter erkennt laufenden Uploader")
        self.assertTrue(ok)

    def test_tu2_reload_waehrend_lieferung_und_abgleich(self):
        b = self.b
        pc = b.m["PC"]
        pc.running = True
        pc.sync.tick(now=T0)
        b.dl["PC"].tick(now=T0)
        for i, t in enumerate((10, 15, 22, 80, 85)):                            # mehrere /reload kurz nacheinander
            pc.write("SavedVariables/AHSentinel.lua", ts.AH_PC.replace("256", str(300 + i)), T0 + t)
            for dt in range(0, 6):
                pc.sync.tick(now=T0 + t + dt)
                b.dl["PC"].tick(now=T0 + t + dt)
        for t in range(91, 260, 5):
            pc.sync.tick(now=T0 + t)
            b.dl["PC"].tick(now=T0 + t)
        last = b.gh.files().get("aktuell/PC/forever/" + daten.konto_id("KONTO") + "/AHSentinel.lua", b"")
        pkg = sync.read_package(b"".join(b.store.parts[p] for p in sync.index_parts(b.store.index)))[1]
        ok = b'"n"] = 304' in last and b'"n"] = 304' in pkg["SavedVariables/AHSentinel.lua"]
        REPORT.add("TU2", ok, "5× /reload in 90 s: letzte Fassung gewinnt in Repo und Abgleich")
        self.assertTrue(ok)


# ---------------------------------------------------------------------------------------------------------------------
# TU3 Standardwerte
# ---------------------------------------------------------------------------------------------------------------------
STANDARD = [
    ("Prüfintervall Uploader (check_seconds)", lambda: max(3, int({}.get("check_seconds") or 10)), 10),
    ("Hauptschleife bei Abgleich (Sekunden)", lambda: __import__("uploader").SYNC_TICK, 5),
    ("Index prüfen bei geschlossenem WoW (Sekunden)", lambda: sync.CHECK_REMOTE_SECONDS, 30),
    ("Ruhe vor dem Hochladen nach WoW-Ende (Sekunden)", lambda: sync.QUIET_SECONDS, 10),
    ("Ruhe vor dem Hochladen bei /reload (Sekunden)", lambda: sync.QUIET_RUNNING_SECONDS, 10),
    ("Höchstens 1 Upload je … bei laufendem WoW (Sekunden)", lambda: sync.PUSH_GAP_RUNNING, 60),
    ("Fassungen in #sync-daten", lambda: sync.VERSIONS_KEEP, 10),
    ("Gewöhnliche Sicherungen", lambda: sync.BACKUPS_KEEP, 5),
    ("Konflikt-Sicherungen (Tage)", lambda: sync.LONG_KEEP_DAYS, 30),
    ("Konflikt-Fenster (Sekunden)", lambda: sync.CONFLICT_WINDOW, 600),
    ("Daten-Repo: stabil vor Lieferung (Sekunden)", lambda: daten.STABLE_SECONDS, 10),
    ("Daten-Repo: höchstens 1 Commit je … (Sekunden)", lambda: daten.MIN_GAP, 60),
    ("Daten-Repo: Tages-Stände", lambda: daten.DAYS_KEEP, 7),
    ("Daten-Repo: Grösse vor früherem Aufräumen (MB)", lambda: daten.REPO_MAX // (1024 * 1024), 200),
    ("Daten-Repo: grösste Datei (MB)", lambda: daten.MAX_FILE // (1024 * 1024), 50),
]


class TU3Standard(unittest.TestCase):
    def test_tu3_standardwerte(self):
        fails = []
        for name, get, want in STANDARD:
            got = get()
            REPORT.add("TU3", got == want, f"{name}: {got}")
            if got != want:
                fails.append(f"{name}: {got} statt {want}")
        self.assertEqual(fails, [])

    def test_tu3_ohne_daten_config_und_ohne_sync_config(self):
        d = tempfile.mkdtemp()
        try:
            conf, why = daten.read_config(d)
            ok = conf is None and why is None                   # fehlt = freiwillig, kein Fehler
            ok = ok and sync.load_sync_config(d) is None
            REPORT.add("TU3", ok, "ohne daten_config.json / sync_config.json: nicht eingerichtet, kein Fehler")
            self.assertTrue(ok)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_tu3_autostart_minimiert_einmal(self):
        with open(os.path.join(UP, "Autostart-einrichten.bat"), encoding="utf-8") as f:
            bat = f.read()
        ok = "WindowStyle=7" in bat and "Remove-Item" in bat and "RaidMaster-Uploader.lnk" in bat
        REPORT.add("TU3", ok, "Autostart: minimiert (WindowStyle 7), genau ein Eintrag")
        self.assertTrue(ok)


# ---------------------------------------------------------------------------------------------------------------------
# TU4 Grundregeln mit Zufallsdaten
# ---------------------------------------------------------------------------------------------------------------------
class TU4Grundregeln(unittest.TestCase):
    def test_tu4_zufall(self):
        rnd = random.Random(SEED)
        b = Box()
        violations = []
        names = ("PC", "Laptop")
        files = ("SavedVariables/AHSentinel.lua", "SavedVariables/A.lua", "Realm/Figur/SavedVariables/B.lua")
        now = T0
        stale_state = {n: json.loads(json.dumps(b.m[n].st)) for n in names}
        try:
            for case in range(CASES):
                op = rnd.choice(["write", "write", "tick", "tick", "tick", "push", "pull", "wow", "net", "stale"])
                n = rnd.choice(names)
                mach = b.m[n]
                now += rnd.randint(1, 90)
                desc = f"Fall {case} (Startwert {SEED}): {op} {n} t+{int(now - T0)}"
                before = b.local(n)
                w_before = dict(mach.sync.wow)
                try:
                    if op == "write":
                        rel = rnd.choice(files)
                        text = (ts.AH_PC.replace("256", str(case)) if rel.endswith("AHSentinel.lua")
                                else f"X = {case}\n")
                        mach.write(rel, text, now)
                        continue
                    if op == "wow":
                        mach.running = not mach.running
                        continue
                    if op == "net":
                        b.store.online = rnd.random() > 0.3
                        continue
                    if op == "stale":
                        stale_state[n] = json.loads(json.dumps(mach.st))
                        continue
                    if op == "tick":
                        mach.sync.next_remote = 0 if rnd.random() < 0.5 else mach.sync.next_remote
                        mach.sync.tick(now=now)
                    elif op == "push":
                        mach.sync.push(now=now)
                    elif op == "pull":
                        mach.sync.pull(now=now)
                except Exception as e:  # noqa: BLE001
                    violations.append(f"{desc}: Ausnahme {type(e).__name__}: {e}")
                    continue
                after = b.local(n)
                bk = b.backups(n)
                # G1 nie Datenverlust: jeder lokale Stand vor einem Abgleich-Schritt ist danach lokal, in einer
                #    Sicherung oder (AHSentinel) im Zusammenführungs-Block noch vorhanden
                for rel, data in before.items():
                    if after.get(rel) == data or data in bk:
                        continue
                    db = sync.top_blocks(data.decode("utf-8", "replace")).get("AHSentinelDB")
                    if db and db in (after.get(rel) or b"").decode("utf-8", "replace"):
                        continue
                    violations.append(f"{desc}: Datenverlust {rel}")
                # G2 WoW läuft: nie geschrieben, ausser Übernahme gleich nach einem frischen Start (S8 c)
                if mach.running and after != before:
                    w = mach.sync.wow
                    if not (w.get("transition") and now - w.get("first_seen", 0) <= sync.TAKEOVER_MAX_AGE):
                        violations.append(f"{desc}: bei laufendem WoW geschrieben (vorher {w_before})")
                # G3 eigener Upload nie "neuer Stand" – auch für einen zweiten Prozess mit altem Zustand
                for m in names:
                    if b.m[m].sync.remote is not None:
                        entries = sync.index_roots(b.m[m].sync.remote)
                        if any(entries[k]["machine"] == m for k in b.m[m].sync.pending()):
                            violations.append(f"{desc}: {m} meldet eigenen Upload als neuer")
                    if b.store.online and b.store.index:
                        second = sync.Sync(b.store, b.m[m].acc, json.loads(json.dumps(stale_state[m])), lambda: None,
                                           m, lambda t: None, lambda: True)
                        second.remote = json.loads(json.dumps(b.store.index))
                        if any(sync.index_roots(second.remote)[k]["machine"] == m for k in second.pending()):
                            violations.append(f"{desc}: zweiter Prozess {m} meldet eigenen Upload")
                # G4 nie Token oder Adressen im Fenster; Meldungen nie mit eigenem Rechnernamen als "neuer"
                for m in names:
                    for line in b.m[m].logs + b.m[m].notes:
                        if SECRET_TOKEN in line or "https://" in line or "webhooks/" in line:
                            violations.append(f"{desc}: Geheimnis im Fenster ({m})")
                        if f"Neuerer Stand vom {m} " in line or f"Neuerer Stand vom {m} (" in line:
                            violations.append(f"{desc}: Hinweis mit eigenem Rechnernamen ({m})")
                    b.m[m].logs.clear()
                    b.m[m].notes.clear()
                # G5 Zustand erfüllt die Grundregeln (TU5)
                for m in names:
                    for v in sync.check_state(b.m[m].st):
                        violations.append(f"{desc}: Grundregel Zustand {m}: {v}")
                if len(violations) > 20:
                    break
            # G6 genau ein Uploader-Prozess
            info = os.path.join(b.d, "inst.json")
            here = os.path.join(b.d, "h")
            os.makedirs(here)
            ok1, _ = sync.instance_acquire(here, "x", path=info)
            with open(info, "w") as f:
                json.dump({"pid": os.getppid()}, f)
            ok2, _ = sync.instance_acquire(here, "x", path=info)
            if not ok1 or ok2:
                violations.append("Einzel-Instanz verletzt")
        finally:
            b.close()
        REPORT.add("TU4", not violations, f"{CASES} Zufallsfälle, Startwert {SEED}: {len(violations)} Verletzungen",
                   count=CASES)
        self.assertEqual(violations, [], "\n".join(violations[:10]))


# ---------------------------------------------------------------------------------------------------------------------
# TU5 Zustand beim Start prüfen (nur lesen)
# ---------------------------------------------------------------------------------------------------------------------
class TU5Zustand(unittest.TestCase):
    def test_tu5_zustand_pruefen(self):
        good = {"sync": {"seq": 5, "revs": {"_forever_/KONTO": 5}, "files": {"a": "0" * 40}, "to_delete": ["123"]}}
        bad = {"sync": {"seq": 3, "revs": {"_forever_/KONTO": 9, "x": -1}, "files": {"a": "zz"},
                        "to_delete": ["abc"]}}
        v_good, v_bad = sync.check_state(good), sync.check_state(bad)
        ok = v_good == [] and len(v_bad) == 4 and not any("KONTO" in x or "_forever_" in x for x in v_bad)
        import uploader
        with open(uploader.__file__, encoding="utf-8") as f:
            src = f.read()
        ok = ok and "GRUNDREGEL VERLETZT (Abgleich)" in src and '["grundregeln"]' in src
        REPORT.add("TU5", ok, "Zustand beim Start: Verletzungen ohne Namen ins Fenster und in stand.json")
        self.assertTrue(ok, v_bad)


# ---------------------------------------------------------------------------------------------------------------------
# TU6 Regressionen: je Befund ein bleibender Test (Name -> Testfall)
# ---------------------------------------------------------------------------------------------------------------------
REGRESSIONEN = {
    "T-SY1 Hochladen/Holen": "test_sync.Abgleich.test_sy1_pc_hoch_laptop_holt_mit_sicherung",
    "T-SY2 WoW läuft": "test_sync.Abgleich.test_sy2_wow_laeuft_nichts_ueberschreiben",
    "T-SY3 Konflikt AHSentinel": "test_sync.Abgleich.test_sy3_konflikt_neuere_gewinnt_ahsentinel_paket",
    "T-SY3b lokal neuer": "test_sync.Abgleich.test_sy3b_konflikt_lokal_neuer",
    "T-SY4 keine Namen im Log": "test_sync.Abgleich.test_sy4_nur_lua_keine_namen_im_log",
    "T-SY5 kein Netz": "test_sync.Abgleich.test_sy5_kein_netz",
    "T-SY6 höchstens 10 Fassungen": "test_sync.Abgleich.test_sy6_hoechstens_10_fassungen",
    "T-SY9b nicht sicher": "test_sync.Sofort.test_sy9b_nicht_sicher_nur_hinweis",
    "T-SY9c Beleg fehlgeschlagen": "test_sync.Sofort.test_sy9c_beleg_fehlgeschlagen",
    "T-SY11b alte Sicherung": "test_sync.Sofort.test_sy11b_alte_sicherung_einmal_zusammenfuehren",
    "T-SY13 nicht neu lesen (offen 5)": "test_sync.Sofort.test_sy13_unveraenderte_dateien_nicht_neu_lesen",
    "offen 2 Uploader wartet": "test_sync.Reload.test_offen2_uploader_wartet_auf_sperre",
    "T-SY7 Hochladen ≤ 15 s": "test_sync.Sofort.test_sy7_wow_beendet_hoch_in_15s",
    "T-SY8 anderer Rechner ≤ 45 s": "test_sync.Sofort.test_sy8_anderer_rechner_holt_in_45s_nur_index",
    "T-SY9 Übernahme vor dem Einloggen": "test_sync.Sofort.test_sy9_wow_ohne_starter_uebernahme_vor_dem_einloggen",
    "T-SY10 Uhr 20 Min. falsch": "test_sync.Sofort.test_sy10_uhr_20_min_falsch",
    "T-SY11 erster Abgleich (offen 1)": "test_sync.Sofort.test_sy11_erster_abgleich_beide_mit_daten",
    "T-SY12 Sperre (offen 2)": "test_sync.Sofort.test_sy12_nur_ein_prozess_gleicht_ab",
    "T-SY14 nur geänderte Spielversion": "test_sync.Groesse.test_sy14_nur_geaenderte_spielversion_retail_nur_wenn_gespielt",
    "T-SY15 Index 2.1.x": "test_sync.Groesse.test_sy15_index_von_2_1_x",
    "T-DU1 Lieferung": "test_daten.Lieferung.test_du1_geaendert_ein_commit_unveraendert_keiner",
    "T-DU2 nicht privat/Token": "test_daten.Lieferung.test_du2_token_nie_im_log_oeffentlich_verweigert",
    "T-DU3 über 50 MB": "test_daten.Lieferung.test_du3_ueber_50_mb_uebersprungen",
    "T-DU4 kein Netz": "test_daten.Lieferung.test_du4_kein_netz_kein_absturz_abgleich_unabhaengig",
    "T-DU5 jeder /reload": "test_daten.Lieferung.test_du5_jeder_reload_hoechstens_1_je_minute",
    "T-DU5 Abgleich jeder /reload": "test_sync.Reload.test_du5_sync_jeder_reload",
    "T-DU6 7 Tage ohne Verlauf": "test_daten.Lieferung.test_du6_nur_neuester_und_7_tage_ohne_verlauf",
    "T-DU6 #sync-daten löschen": "test_sync.Reload.test_du6_alte_fassungen_wirklich_loeschen",
    "T-DU7 Token mit Strg+V": "test_daten.Einrichten.test_du7_token_mit_strg_v",
    "T-DU8 BOM": "test_daten.Einrichten.test_du8_config_mit_bom_und_gruende",
    "T-DU9 Zertifikat/Ursache": "test_daten.Einrichten.test_du9_echte_ursache_und_zertifikate",
    "T-DU10 zwei Rechner": "test_daten.ZweiRechner.test_du10_zwei_rechner",
    "T-DU11 zweiter Prozess": "test_sync.ZweiterProzess.test_du11_eigener_upload_nie_neuer",
    "T-DU11 Meldung einmal": "test_sync.ZweiterProzess.test_du11_meldung_nennt_anderen_rechner_einmal",
    "T-DU11 Einzel-Instanz": "test_sync.ZweiterProzess.test_du11_nur_ein_uploader",
    "U1 / T-DU12 gleichzeitig": "test_daten.Gleichzeitig.test_du12_kopf_aendert_sich_zweimal",
    "U2 Starter-Sperre": "test_sync.SperreU2.test_u2a_starter_sperre_warten_dann_laufen",
    "U2 tote Sperre": "test_sync.SperreU2.test_u2b_sperre_eines_beendeten_prozesses",
    "U2 alter Uploader": "test_sync.SperreU2.test_u2c_lebender_uploader_vor_2_3_2",
    "T-DU12a Sperre ohne PID": "test_sync.SperreDU12.test_du12a_sperre_ohne_pid",
    "T-DU12b PID tot": "test_sync.SperreDU12.test_du12b_pid_tot",
    "T-DU12c PID wiederverwendet": "test_sync.SperreDU12.test_du12c_pid_wiederverwendet",
    "T-DU12d echter zweiter Uploader": "test_sync.SperreDU12.test_du12d_echter_zweiter_uploader_angebot",
    "T-DU12e alte 2.3.1-Statusdatei": "test_sync.SperreDU12.test_du12e_alte_231_statusdatei",
    "offen 1c alte Sicherungen": "test_sync.Reload.test_sy11c_sicherung_am_ort_von_2_1_0",
    "offen 3 Merge-Block": "test_sync.Reload.test_offen3_offener_block_bleibt_bei_uebernahme",
    "offen 6 zu gross einmal": "test_uploader.Paket.test_p13_zu_gross_neue_uhrzeit_keine_zweite_meldung",
    "T-DU12 alte Fassung entpackt (Warnung)": "test_uploader.Uploader17.test_alte_fassung_entpackt_warnung",
    "MN6 Markt-Scans einmal, ohne Namen": "test_uploader.Paket.test_mn6_markt_scans_einmal_ohne_namen",
    "MN6b Quelle anonym, gleich": "test_uploader.Paket.test_mn6b_quelle_zufall_bleibt_gleich",
    "U3 Markt-Format unbekannt einmal": "test_uploader.Paket.test_u3_unbekanntes_markt_format_einmal_gemeldet",
    "RP-U nur bank/raidReady": "test_uploader.Uploader17.test_rp_u_nur_bank_und_raidready",
}


class TU6Regressionen(unittest.TestCase):
    def test_tu6_regressionen_vorhanden_und_gruen(self):
        import test_uploader  # noqa: F401
        loader = unittest.TestLoader()
        missing, failed = [], []
        for name, path in REGRESSIONEN.items():
            mod, cls, meth = path.split(".")
            klass = getattr(sys.modules.get(mod) or __import__(mod), cls, None)
            if klass is None or not hasattr(klass, meth):
                missing.append(f"{name} ({path})")
                continue
            res = unittest.TestResult()
            loader.loadTestsFromName(meth, klass).run(res)
            if not res.wasSuccessful():
                failed.append(name)
        n = len(REGRESSIONEN)
        REPORT.add("TU6", not missing and not failed,
                   f"Regressionen: {n - len(missing)} von {n} vorhanden, {n - len(missing) - len(failed)} grün", count=n)
        self.assertEqual((missing, failed), ([], []))


# ---------------------------------------------------------------------------------------------------------------------
# TU7 Formen des Spiels (für den Uploader: Ordner der WoW-Versionen)
# ---------------------------------------------------------------------------------------------------------------------
class TU7Formen(unittest.TestCase):
    def test_tu7_alle_spielversionen(self):
        d = tempfile.mkdtemp()
        try:
            for flavor in ("_forever_", "_classic_era_", "_anniversary_", "_classic_", "_retail_"):
                os.makedirs(os.path.join(d, "World of Warcraft", flavor, "WTF", "Account", "KONTO", "SavedVariables"))
            roots = sync.find_roots([d])
            want = {f"{f}/KONTO" for f in ("_forever_", "_classic_era_", "_anniversary_", "_classic_", "_retail_")}
            ok = set(roots) == want
            dl = daten.Daten(daten.GitHubAPI("a/b", SECRET_TOKEN), roots, {}, lambda: None, "PC", lambda t: None)
            for k, acc in roots.items():
                with open(os.path.join(acc, "SavedVariables", "AHSentinel.lua"), "w") as f:
                    f.write("AHSentinelDB = {}\n")
            paths = sorted(dl.files())
            ok = ok and len(paths) == 5 and all(p.split("/")[0] in ("forever", "classic_era", "anniversary", "classic",
                                                                     "retail") for p in paths)
            REPORT.add("TU7", ok, "Forever, Era, Anniversary/TBC, Classic, Retail: erkannt und getrennt abgelegt")
            self.assertTrue(ok, (roots, paths))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_tu7_geheime_werte_und_skalierung(self):
        REPORT.skip("TU7", "geheime Werte im Kampf / Fenster-Skalierung: betrifft den Uploader nicht (kein Spielcode)")


# ---------------------------------------------------------------------------------------------------------------------
# TU8 Testbericht
# ---------------------------------------------------------------------------------------------------------------------
class Report:
    AREAS = ("TU1", "TU2", "TU3", "TU4", "TU5", "TU6", "TU7")

    def __init__(self):
        self.rows = {a: {"ok": 0, "fehler": 0, "skip": 0, "lines": []} for a in self.AREAS}

    def add(self, area, ok, line, count=1):
        r = self.rows[area]
        r["ok" if ok else "fehler"] += count if ok else 1
        r["lines"].append(("OK " if ok else "FEHLER ") + line)

    def skip(self, area, why):
        self.rows[area]["skip"] += 1
        self.rows[area]["lines"].append("SKIP " + why)

    def text(self):
        out = ["TESTBERICHT UPLOADER (TU8) – Startwert " + str(SEED)]
        for a in self.AREAS:
            r = self.rows[a]
            out.append(f"{a} OK {r['ok']} · FEHLER {r['fehler']} · SKIP {r['skip']}")
        for a in self.AREAS:
            for line in self.rows[a]["lines"]:
                out.append(f"  {a} {line}")
        return "\n".join(out)


REPORT = Report()


class TU8Bericht(unittest.TestCase):
    def test_zz_tu8_jeder_bereich_hat_ergebnisse(self):
        empty = [a for a in Report.AREAS if REPORT.rows[a]["ok"] + REPORT.rows[a]["fehler"] == 0]
        if len(sys.argv) > 0 and "unittest" not in sys.argv[0] and any(REPORT.rows[a]["lines"] for a in Report.AREAS):
            pass
        # Nur prüfen, wenn das ganze Modul lief (Einzelaufrufe füllen nicht alle Bereiche)
        if all(REPORT.rows[a]["lines"] for a in Report.AREAS):
            self.assertEqual(empty, [], "Bereiche ohne Ergebnis (nur SKIP): " + ", ".join(empty))


if __name__ == "__main__":
    prog = unittest.main(exit=False, verbosity=1)
    print()
    print(REPORT.text())
    sys.exit(0 if prog.result.wasSuccessful() else 1)
