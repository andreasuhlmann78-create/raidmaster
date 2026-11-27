"""UP-UPD1 (ab 2.3.24, Entscheid des Nutzers 24.11.2026 21:36 "ok lass die befehle raus"): Uploader-Update auf Knopfdruck mit
Rückfrage – KEIN automatisches Selbst-Update.

1. Ist eine neuere Uploader-Version veröffentlicht (VERSION in RaidMasterUploader/uploader.py im Repo raidmaster), fragt der Uploader
   im Fenster: "Neue Uploader-Version x verfügbar – jetzt installieren? (j/n)". Ohne "j" passiert nichts (Daten werden nach UP-MIN1
   weiter geliefert, solange nicht unter der Mindestversion). "n" = für diese Version nicht mehr fragen – bis zur nächsten Version oder
   bis die Mindestversion steigt (uploader_state.json "selbstupdate"). Gilt für alle gleich. Die Frage blockiert nie: der Uploader
   liefert weiter, eine Taste wird bei jedem Durchgang abgefragt.
2. Nach "j": nur aus raidmaster (GitHub-API, HTTPS, ohne Token), download/RaidMasterUploader.zip über ihre Blob-Kennung, Prüfsumme
   (Git-Blob-SHA) = Repo, jede Datei mit richtiger CRC, nur Dateien direkt in RaidMasterUploader/ und nur .py/.bat/.txt (nie .json –
   so kann eine Zip die Konfiguration gar nicht berühren), VERSION in uploader.py der Zip = erwartet und neuer als die eigene.
   Neue Dateien zuerst in den Nebenordner _update/neu, die bisherigen Programmdateien als Sicherung nach _update/alt (eine Generation),
   dann umschalten (nur Programmdateien; uploader_config.json, uploader_state.json, sync_config.json, daten_config.json, Logs, Daten
   bleiben unberührt).
3. Neustart: Der alte Uploader gibt Sperre und Instanz frei, startet die neue Version mit demselben Aufruf in einem neuen Fenster und
   wartet bis FRIST Sekunden, bis sie sich in _update/status.json als "läuft" meldet. Dann beendet er sich. Meldet sie sich nicht,
   beendet er sie, stellt die alte Version aus _update/alt wieder her und läuft selbst weiter (Meldung im Fenster).
3a. UP-UPD1-a (2.3.26, Nutzer 22:00 "das alte fenster bleibt offen stehen", 22:01 "wir updaten über den uploader selber"): vor dem
   Umschalten beendet der alte Uploader NUR das cmd.exe seines eigenen Fensters (Vorfahre, führt uploader.bat aus; nicht dessen
   Kinder). Python läuft im Fenster weiter; endet es nach der Übergabe, schliesst Windows das Fenster. Bei Fehler/Rückfall läuft die
   alte Version im Fenster weiter. Weil danach niemand mehr die laufende uploader.bat liest, wird sie in diesem Fall mit ersetzt
   (sonst wie bisher nicht). Die neue Version startet über uploader.bat in einem neuen Fenster: stürzt sie ab, bleibt dort "pause".
4. Meldungen: "Uploader x -> y installiert, neu gestartet" bzw. "Update fehlgeschlagen (<Grund>) – alte Version x läuft weiter".
   stand.json je Rechner (über den Zustand "daten"): "update": {"von", "nach", "ergebnis", "zeit"} – ohne Namen (für D-UPD1).
4a. UP-UPD1-c (2.3.28, Frage Supervisor 25.11. 06:34 "Feld update erscheint nicht"): Bis 2.3.27 schrieb bei Erfolg der ALTE Prozess
   "update" in seinen Zustand – erst nachdem die neue Version ihren Zustand schon gelesen hatte. Die neue Version kannte das Feld nie
   und überschrieb die Datei beim nächsten Speichern: ein gelungenes Update erschien nie in stand.json (nur Fehlschläge). Jetzt
   trägt die NEUE Version es ein, wenn sie "läuft" meldet (Angaben aus _update/status.json; auch nach einem Update durch eine alte
   Version). Der alte Prozess schreibt nach der Übergabe nichts mehr (kein Zustand, kein Senden beim Beenden).
5. RM-UPD2 (2.3.29, Entscheid des Nutzers 27.11.2026 07:08/07:10 "dass man im uploader nicht mehr mit j bestätigen muss sondern dass es
   automatisch läuft" – nur die neue Uploader-Version; ÜBERHOLT Punkt 1): eine neuere Version wird OHNE Frage installiert, mit allen
   Schutzmassnahmen aus 2.–4a. unverändert. Nie während ein Abgleich beim Spielstart (GoldSentinel-WoW, Rolle "starter") läuft – dann
   wird gewartet. Höchstens 1 Versuch je Version und Stunde (uploader_state.json "selbstupdate"."versuch"; über einen Neustart hinweg,
   keine Schleife). Der frühere "n"-Merker ("abgelehnt") wird nicht mehr beachtet. Meldung "Uploader x -> y automatisch installiert,
   neu gestartet". UNVERÄNDERT mit j/n: neue Einstellungsdatei (UP-CFG1).
6. RM-UPD3 (2.3.30, Entscheid des Nutzers 27.11.2026 07:46 "ich will das alles vollautomatisch passiert"; ÜBERHOLT den j/n-Teil von 5.):
   auch eine neue Einstellungsdatei wird ohne Frage übernommen – nur wenn einstellungen.Pickup sie geprüft hat (gleicher Bot, gleicher
   Discord-Server, gültig); sonst verwirft Pickup sie selbst. Der Uploader stellt keine j/n-Frage mehr.
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile

import addons

ZIP_PATH = "RaidMasterUploader.zip"            # in download/
UPDATE_DIR = "_update"
STATUS_FILE = "status.json"
FRIST = 60                                       # Sekunden, bis die neue Version "läuft" melden muss
CHECK_SECONDS = 600                              # so oft nach einer neueren Version sehen
PROGRAM_EXT = (".py", ".bat", ".txt")
NEVER_TOUCH = {"uploader_config.json", "uploader_state.json", "sync_config.json", "daten_config.json"}
VERSION_RE = re.compile(rb'^VERSION\s*=\s*["\'](\d+(?:\.\d+){1,3})["\']', re.M)


def version_key(v) -> tuple:
    return addons.version_key(v)


def is_older(have, want) -> bool:
    return bool(version_key(want)) and version_key(have) < version_key(want)


def check_zip(data: bytes, sha: str | None, expected: str, own: str) -> tuple[dict[str, bytes] | None, str]:
    """Regel 2: ({Dateiname: Inhalt}, "") oder (None, Grund)."""
    if not sha or addons.git_blob_sha(data) != sha:
        return None, "Prüfsumme passt nicht zur Datei im Repo"
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
        bad = zf.testzip()
    except (zipfile.BadZipFile, OSError, RuntimeError, ValueError) as e:
        return None, f"Zip nicht lesbar ({e.__class__.__name__})"
    if bad:
        return None, f"Zip beschädigt ({bad})"
    files: dict[str, bytes] = {}
    for info in zf.infolist():
        n = info.filename.replace("\\", "/")
        if n == "RaidMasterUploader/":
            continue
        parts = n.split("/")
        if len(parts) != 2 or parts[0] != "RaidMasterUploader" or not parts[1] or parts[1] in (".", ".."):
            return None, f"unerwarteter Eintrag in der Zip ({n})"
        name = parts[1]
        if name in NEVER_TOUCH or not name.lower().endswith(PROGRAM_EXT):
            return None, f"Datei ist kein Programmteil ({name})"
        files[name] = zf.read(info)
    up = files.get("uploader.py")
    if up is None:
        return None, "uploader.py fehlt"
    m = VERSION_RE.search(up)
    got = m.group(1).decode() if m else "keine"
    if got != expected:
        return None, f"Version in der Zip ist {got}, erwartet {expected}"
    if not is_older(own, got):
        return None, f"Version {got} ist nicht neuer als {own}"
    return files, ""


def stage(here: str, files: dict[str, bytes]) -> list[str]:
    """Neue Dateien nach _update/neu, bisherige Programmdateien nach _update/alt (eine Generation). Liefert die Namen der Programmdateien."""
    base = os.path.join(here, UPDATE_DIR)
    neu, alt = os.path.join(base, "neu"), os.path.join(base, "alt")
    for d in (neu, alt):
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
    for name, data in files.items():
        with open(os.path.join(neu, name), "wb") as f:
            f.write(data)
        with open(os.path.join(neu, name), "rb") as f:
            if f.read() != data:
                raise OSError(f"{name}: im Nebenordner nicht gleich")
    names = sorted(set(files) | {n for n in os.listdir(here) if os.path.isfile(os.path.join(here, n))
                                 and n.lower().endswith(PROGRAM_EXT) and n not in NEVER_TOUCH})
    for n in names:
        src = os.path.join(here, n)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(alt, n))
    return names


RUNNING_BAT = "uploader.bat"         # läuft gerade (cmd liest eine .bat beim Ausführen Zeile für Zeile nach) -> nie ersetzen


def switch(here: str, files: dict[str, bytes], bat_free: bool = False) -> list[str]:
    """Umschalten: Programmdateien aus _update/neu über die bisherigen (je Datei über eine Zwischendatei, danach zurückgelesen).
    Gleiche Dateien bleiben unberührt. uploader.bat wird nie ersetzt, solange sie läuft (Windows liest eine laufende .bat Stück für
    Stück nach – eine ersetzte Datei würde mitten im Text weitergelesen); sie kommt mit dem nächsten /uploader. Liefert die
    übergangenen Dateien."""
    neu = os.path.join(here, UPDATE_DIR, "neu")
    skipped = []
    for name in sorted(files, key=lambda n: n == "uploader.py"):          # uploader.py zuletzt
        target = os.path.join(here, name)
        if os.path.isfile(target):
            with open(target, "rb") as f:
                if f.read() == files[name]:
                    continue
            if name == RUNNING_BAT and not bat_free:
                skipped.append(name)
                continue
        tmp = target + ".gsneu"
        shutil.copyfile(os.path.join(neu, name), tmp)
        os.replace(tmp, target)
        with open(target, "rb") as f:
            if f.read() != files[name]:
                raise OSError(f"{name}: nach dem Umschalten nicht gleich")
    return skipped


def restore(here: str) -> int:
    """Alte Version aus _update/alt zurück (nur Programmdateien). Liefert die Zahl der Dateien."""
    alt = os.path.join(here, UPDATE_DIR, "alt")
    n = 0
    for name in sorted(os.listdir(alt)):
        if name in NEVER_TOUCH:
            continue
        tmp = os.path.join(here, name + ".gsalt")
        shutil.copyfile(os.path.join(alt, name), tmp)
        os.replace(tmp, os.path.join(here, name))
        n += 1
    return n


def status_path(here: str) -> str:
    return os.path.join(here, UPDATE_DIR, STATUS_FILE)


def report_running(here: str, version: str, state: dict | None = None, now=time.time) -> bool:
    """Die (neue) Version meldet "läuft" – aufgerufen beim Start, sobald sie die Instanz hat und die Konfiguration gelesen ist.
    UP-UPD1-c: war es ein Update (von != nach) und ist die Übergabe frisch (höchstens FRIST + 60 s alt), trägt die neue Version
    "update" in ihren eigenen Zustand state["daten"] ein. True = "läuft" gemeldet (dann soll der Aufrufer den Zustand speichern)."""
    p = status_path(here)
    try:
        with open(p, encoding="utf-8") as f:
            st = json.load(f)
    except (OSError, ValueError):
        return False
    if not isinstance(st, dict) or st.get("nach") != version or st.get("laeuft"):
        return False
    st["laeuft"], st["pid"] = True, os.getpid()
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump(st, f)
    os.replace(p + ".tmp", p)
    try:
        zeit = int(st.get("zeit") or 0)
    except (TypeError, ValueError):
        zeit = 0
    if state is not None and st.get("von") and st.get("von") != version and 0 <= now() - zeit <= FRIST + 60:
        state.setdefault("daten", {})["update"] = {"von": st["von"], "nach": version, "ergebnis": "ok", "zeit": zeit}
    return True


def read_status(here: str) -> dict:
    try:
        with open(status_path(here), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def read_key() -> str | None:
    """Eine gedrückte Taste ohne zu warten (Windows-Konsole); sonst None. Andere Systeme: nur Zeilen aus einer Konsole."""
    try:
        if sys.platform == "win32":
            import msvcrt
            if msvcrt.kbhit():
                return msvcrt.getwch()
            return None
        import select
        if sys.stdin and sys.stdin.isatty():
            r, _, _ = select.select([sys.stdin], [], [], 0)
            if r:
                return sys.stdin.readline().strip() or None
    except Exception:  # noqa: BLE001
        return None
    return None


def spawn_same(here: str):
    """Die neue Version starten: unter Windows über uploader.bat in einem neuen Fenster (wie Autostart/Doppelklick – stürzt sie ab,
    bleibt dort "pause" mit der Meldung stehen), sonst derselbe Aufruf."""
    bat = os.path.join(here, RUNNING_BAT)
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    if sys.platform == "win32" and os.path.isfile(bat):
        return subprocess.Popen([os.environ.get("COMSPEC") or "cmd.exe", "/c", bat], cwd=here, creationflags=flags)
    args = [sys.executable, os.path.join(here, "uploader.py")] + [a for a in sys.argv[1:]]
    return subprocess.Popen(args, cwd=here, creationflags=flags)


# -- UP-UPD1-a (2.3.26): eigenes Fenster nach der Übergabe schliessen ------------------------------------------------------------
# Das Fenster gehört dem cmd.exe, das uploader.bat ausführt (Autostart-Verknüpfung bzw. Doppelklick); Kette python.exe <- py.exe <-
# cmd.exe. Wird NUR dieser cmd.exe (ohne seine Kinder) beendet, läuft Python im Fenster weiter; endet Python danach, schliesst
# Windows das Fenster (kein Prozess mehr daran). Bei Fehler/Rückfall läuft die alte Version im Fenster weiter.
# Zugleich liest danach niemand mehr die laufende uploader.bat -> sie darf beim Update ersetzt werden (bisher nie ersetzt).

def process_info(pid: int) -> tuple[int, str, str] | None:
    """(Eltern-PID, Name, Kommandozeile) oder None."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return None
    if pid <= 0:
        return None
    if sys.platform == "win32":
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command",
                                  f"$p = Get-CimInstance Win32_Process -Filter 'ProcessId={pid}'; "
                                  f"if ($p) {{ \"$($p.ParentProcessId)|$($p.Name)|$($p.CommandLine)\" }}"],
                                 capture_output=True, text=True, timeout=15,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout.strip()
        except Exception:  # noqa: BLE001
            return None
        parts = out.split("|", 2)
        if len(parts) != 3 or not parts[0].strip().isdigit():
            return None
        return int(parts[0]), parts[1].strip(), parts[2].strip()
    try:
        with open(f"/proc/{pid}/stat", "rb") as f:
            stat = f.read().decode("utf-8", "replace")
        name = stat[stat.index("(") + 1:stat.rindex(")")]
        ppid = int(stat[stat.rindex(")") + 2:].split()[1])
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmd = f.read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
        return ppid, name, cmd
    except (OSError, ValueError, IndexError):
        return None


def find_console_bat(start: int | None = None, info=process_info, depth: int = 4) -> int | None:
    """PID des cmd.exe, das uploader.bat ausführt und unser Vorfahre ist (höchstens 4 Stufen), sonst None."""
    pid = os.getpid() if start is None else start
    for _ in range(depth):
        got = info(pid)
        if not got:
            return None
        ppid = got[0]
        if ppid <= 1:
            return None
        parent = info(ppid)
        if not parent:
            return None
        if parent[1].lower() == "cmd.exe" and RUNNING_BAT in parent[2].lower():
            return ppid
        pid = ppid
    return None


def kill_one(pid: int) -> bool:
    """Genau diesen Prozess beenden (NICHT seine Kinder – sonst endete auch dieser Uploader)."""
    try:
        if sys.platform == "win32":
            r = subprocess.run(["taskkill", "/PID", str(int(pid)), "/F"], capture_output=True, timeout=20,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return r.returncode == 0
        import signal
        os.kill(int(pid), signal.SIGTERM)
        return True
    except Exception:  # noqa: BLE001
        return False


def kill_tree(proc) -> None:
    """Neue Version samt Kindern beenden (Rückfall): unter Windows cmd.exe -> py.exe -> python.exe."""
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(int(proc.pid)), "/T", "/F"], capture_output=True, timeout=20,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        else:
            proc.terminate()
    except Exception:  # noqa: BLE001
        pass


class SelfUpdate:
    def __init__(self, here: str, version: str, st: dict, save, log, *, latest=None, minimum=None, fetch_zip=None,
                 key=read_key, spawn=spawn_same, handover=None, takeback=None, sleep=time.sleep, now=time.time,
                 console=find_console_bat, kill_console=kill_one, kill=kill_tree, pickup=None, busy=None):
        self.here, self.version, self.log, self.save = here, version, log, save
        self.s = st.setdefault("selbstupdate", {})
        self.d = st.setdefault("daten", {})
        self.latest, self.minimum, self.fetch_zip = latest, minimum, fetch_zip
        self.key, self.spawn, self.handover, self.takeback = key, spawn, handover, takeback
        self.sleep, self.now = sleep, now
        self.console, self.kill_console, self.kill = console, kill_console, kill
        self.pickup = pickup            # UP-CFG1: Einstellungsdateien aus dem Download-Ordner (eine Frage zur Zeit)
        self.busy = busy                # RM-UPD2: True = Abgleich beim Spielstart läuft gerade -> nicht umschalten
        self.next_at = 0.0
        self.exit_now = False           # True: neue Version läuft – dieser Prozess soll sich beenden

    RETRY_SECONDS = 3600                 # RM-UPD2: höchstens 1 Versuch je Version und Stunde

    def _tried_recently(self, ver: str, t: float) -> bool:
        v = self.s.get("versuch") or {}
        try:
            return v.get("version") == ver and 0 <= t - float(v.get("zeit") or 0) < self.RETRY_SECONDS
        except (TypeError, ValueError):
            return False

    def tick(self) -> bool:
        """Liefert True, wenn sich dieser Prozess beenden soll (neue Version läuft)."""
        t = self.now()
        if t >= self.next_at:
            self.next_at = t + CHECK_SECONDS
            ver = self.latest() if self.latest else None
            if ver and is_older(self.version, ver) and not self._tried_recently(ver, t):
                if self.busy is not None and self.busy():
                    if self.s.get("wartet") != ver:
                        self.s["wartet"] = ver
                        self.log(f"Neue Uploader-Version {ver} – wird automatisch installiert, sobald der Abgleich beim Spielstart fertig ist.")
                    self.next_at = t + 30
                else:
                    self.s.pop("wartet", None)
                    self.s["versuch"] = {"version": ver, "zeit": int(t)}
                    self.save()
                    self.log(f"Neue Uploader-Version {ver} – wird automatisch installiert ...")
                    return self.install(ver)
        if self.pickup is not None:                 # RM-UPD3: geprüfte Einstellungsdatei automatisch übernehmen
            o = self.pickup.poll()
            if o and self.pickup.accept(o) == "neustart":
                return self.restart("neue Einstellungen")
        return False

    def _record(self, nach: str, ergebnis: str):
        self.d["update"] = {"von": self.version, "nach": nach, "ergebnis": ergebnis, "zeit": int(self.now())}
        self.save()

    def _fail(self, nach: str, why: str) -> bool:
        self.log(f"Update fehlgeschlagen ({why}) – alte Version {self.version} läuft weiter.")
        self._record(nach, "fehlgeschlagen: " + why)
        return False

    def install(self, ver: str) -> bool:
        try:
            data, sha = self.fetch_zip()
        except Exception as e:  # noqa: BLE001
            return self._fail(ver, f"Laden nicht möglich ({e.__class__.__name__})")
        files, why = check_zip(data, sha, ver, self.version)
        if files is None:
            return self._fail(ver, why)
        try:
            stage(self.here, files)
            # UP-UPD1-a: das cmd.exe dieses Fensters beenden (Python läuft weiter) -> Fenster schliesst sich nach der Übergabe,
            # und die laufende uploader.bat liest niemand mehr, darf also ersetzt werden
            cmd = None
            try:
                cmd = self.console() if self.console else None
            except Exception:  # noqa: BLE001
                cmd = None
            freed = bool(cmd) and bool(self.kill_console(cmd))
            skipped = switch(self.here, files, bat_free=freed)
            if skipped:
                self.log(f"Hinweis: {', '.join(skipped)} läuft gerade und bleibt unverändert (kommt mit dem nächsten /uploader).")
        except OSError as e:
            try:
                restore(self.here)
            except OSError:
                pass
            return self._fail(ver, f"Schreiben nicht möglich ({e.__class__.__name__}: {e})")
        st = {"von": self.version, "nach": ver, "zeit": int(self.now()), "laeuft": False}
        with open(status_path(self.here), "w", encoding="utf-8") as f:
            json.dump(st, f)
        if self.handover:
            self.handover()                          # Sperre und Instanz freigeben, damit die neue Version starten kann
        proc = None
        try:
            proc = self.spawn(self.here)
        except Exception as e:  # noqa: BLE001
            return self._rollback(ver, f"Start nicht möglich ({e.__class__.__name__})", proc)
        waited = 0.0
        while waited < FRIST:
            if read_status(self.here).get("laeuft"):
                self.log(f"Uploader {self.version} -> {ver} automatisch installiert, neu gestartet.")
                self.exit_now = True                 # UP-UPD1-c: "update" trägt die neue Version ein, hier nichts mehr speichern
                return True
            if proc is not None and proc.poll() is not None:
                return self._rollback(ver, f"neue Version beendet sich sofort (Code {proc.returncode})", proc)
            self.sleep(1)
            waited += 1
        return self._rollback(ver, f"neue Version meldet sich nicht innerhalb von {FRIST} s", proc)

    def restart(self, why: str) -> bool:
        """UP-CFG1: dieselbe Version neu starten (wie beim Update: Fenster übergeben, neue meldet "läuft", sonst weiterlaufen)."""
        st = {"von": self.version, "nach": self.version, "zeit": int(self.now()), "laeuft": False, "grund": why}
        os.makedirs(os.path.join(self.here, UPDATE_DIR), exist_ok=True)
        with open(status_path(self.here), "w", encoding="utf-8") as f:
            json.dump(st, f)
        try:
            cmd = self.console() if self.console else None
        except Exception:  # noqa: BLE001
            cmd = None
        if cmd:
            self.kill_console(cmd)
        if self.handover:
            self.handover()
        proc = None
        try:
            proc = self.spawn(self.here)
        except Exception as e:  # noqa: BLE001
            return self._restart_failed(f"Start nicht möglich ({e.__class__.__name__})", proc)
        waited = 0.0
        while waited < FRIST:
            if read_status(self.here).get("laeuft"):
                self.log(f"Uploader neu gestartet ({why}).")
                self.exit_now = True
                return True
            if proc is not None and proc.poll() is not None:
                return self._restart_failed(f"neuer Start beendet sich sofort (Code {proc.returncode})", proc)
            self.sleep(1)
            waited += 1
        return self._restart_failed(f"neuer Start meldet sich nicht innerhalb von {FRIST} s", proc)

    def _restart_failed(self, why: str, proc) -> bool:
        if proc is not None and proc.poll() is None:
            self.kill(proc)
        if self.takeback:
            self.takeback()
        self.log(f"Neustart nicht gelungen ({why}) – der Uploader läuft weiter; die neuen Einstellungen gelten nach dem nächsten Start.")
        return False

    def _rollback(self, ver: str, why: str, proc) -> bool:
        if proc is not None and proc.poll() is None:
            self.kill(proc)                          # neue Version samt Kindern beenden
        try:
            restore(self.here)
        except OSError as e:
            why += f"; alte Dateien nicht wiederhergestellt ({e})"
        if self.takeback:
            self.takeback()                          # Instanz und Sperre wieder übernehmen
        return self._fail(ver, why)


def fetch_zip_from_repo(get=None) -> tuple[bytes, str]:
    """download/RaidMasterUploader.zip über die GitHub-API: Wurzel -> Baum download/ -> Blob (genau diese Kennung)."""
    get = get or (lambda url, headers=None: addons.http_get(url, headers))
    api = f"{addons.API}/repos/{addons.REPO}"
    st, _h, body = get(f"{api}/contents", {"Accept": "application/vnd.github+json"})
    if st != 200:
        raise OSError(f"HTTP {st}")
    root = json.loads(body.decode("utf-8"))
    tree = next((e.get("sha") for e in root if e.get("name") == "download" and e.get("type") == "dir"), None)
    st, _h, body = get(f"{api}/git/trees/{tree}", {"Accept": "application/vnd.github+json"})
    if st != 200:
        raise OSError(f"HTTP {st}")
    entry = next((e for e in json.loads(body.decode("utf-8")).get("tree") or [] if e.get("path") == ZIP_PATH), None)
    if not entry:
        raise OSError("RaidMasterUploader.zip fehlt im Repo")
    st, _h, data = get(f"{api}/git/blobs/{entry['sha']}", {"Accept": "application/vnd.github.raw"})
    if st != 200:
        raise OSError(f"HTTP {st}")
    return data, entry["sha"]
