"""Abgleich der Addon-Daten zwischen zwei Rechnern (PC und Laptop) – ab Uploader 2.1.0, sofort und ohne Klick ab 2.2.0.

Auftrag: auftraege/RaidMaster/anweisung-uploader-sync-rechner.txt (Entscheid des Nutzers 11.11.2026, Lösung 2;
Nachtrag S8 "sofort und ohne Klick", 20:05).

Speicher (S1): ein PRIVATER Discord-Kanal #sync-daten, den nur du und der Bot sehen. Der Bot legt ihn bei /uploader an,
dazu einen Webhook und eine "Index"-Nachricht; beides steht in sync_config.json (neben dem Uploader, geheim wie
uploader_config.json). Der Uploader schickt den Stand als Anhang über den Webhook und trägt im Index ein, welche
Nachrichten der neueste Stand sind. Ein Webhook darf seine eigenen Nachrichten lesen, ändern und löschen – darum braucht
der Uploader keinen Bot-Token und der Bot liest #sync-daten nie. Höchstens 10 Fassungen je Spielversion/Konto bleiben,
ältere löscht der Uploader. Übertragung nur über HTTPS; die Daten liegen nur in diesem privaten Kanal, nie im Repo, nie in
#testberichte.

Was (S2): alle *.lua in WTF/Account/<KONTO>/SavedVariables und WTF/Account/<KONTO>/<Realm>/<Charakter>/SavedVariables
(nicht *.lua.bak, nicht Config.wtf, Makros oder Tastenbelegungen), aller Spielversionen und Konten des Rechners.

Ab 2.2.0 (S8 e): je Spielversion/Konto ein eigenes Paket. Hochgeladen wird nur, was sich geändert hat. Spielversionen,
deren Dateien seit 14 Tagen unverändert sind, gehen nur einmal als Grundstand hoch; Retail (und PTR/Beta) nur, wenn
dort gespielt wird. Geholt wird nur, was auf diesem Rechner installiert ist.
Index (v2): {"v":2, "seq", "machine", "time", "off", "r": {"<Spielversion>/<KONTO>": [rev, [Nachrichten], Rechner,
Zeit]}, "h": [[Nachrichten einer älteren Fassung], …]}. Ein Index v1 (Uploader 2.1.x, ein Paket für alles) wird gelesen
und beim nächsten Hochladen umgestellt.

Ablauf (S3/S8): WoW darf beim Schreiben NIE laufen – mit einer Ausnahme (S8 c, siehe unten).
  - Hochladen: WoW beendet und die SavedVariables seit 10 s unverändert (≤ 15 s nach WoW-Ende). Läuft WoW noch, ab 2.3.0
    nach JEDEM /reload und Ausloggen ebenso nach 10 s Ruhe, höchstens 1× je Minute (nur lesen, nichts schreiben).
  - Ältere Fassungen in #sync-daten werden wirklich gelöscht (Nachricht samt Anhang); klappt das Löschen nicht, merkt
    sich der Uploader die Nachricht und versucht es später erneut (ab 2.3.0).
  - Ein offener AHSentinelMerge-Block geht nicht mit hoch (ab 2.3.0): Er gehört nur dem Rechner, auf dem der Konflikt
    gelöst wurde; der andere Rechner bekommt den Stand ohne Block und führt nichts doppelt zusammen. Übernimmt dieser
    Rechner später einen neueren Stand, bleibt sein offener Block erhalten.
  - Holen: bei geschlossenem WoW den Index alle 30 s prüfen (nur die kleine Index-Nachricht; Pakete nur, wenn neuer).
    Discord-Grenzen: Antwort 429 bzw. "X-RateLimit-Remaining: 0" -> so lange warten, wie Discord sagt.
    Vorher Sicherung der lokalen Dateien in _sync_backup/<Zeit> (gewöhnliche: höchstens 5; aus Konflikten und
    Übernahmen: 30 Tage).
  - Läuft WoW und es gibt einen neueren Stand: nichts überschreiben, nur melden.
  - S8 c: WoW ohne Starter geöffnet. WoW liest SavedVariables erst beim Betreten der Welt. Sieht der Uploader einen NEUEN
    WoW-Prozess (kurz vorher lief keiner), prüft er sofort den Index und übernimmt einen neueren Stand noch im Anmelde-/
    Charakterbildschirm – nur wenn seit dem Prozessstart keine SavedVariables-Datei geschrieben wurde und höchstens 45 s
    nach dem Start. Solange das nicht belegt ist, mit Windows-Meldung "bitte noch nicht einloggen …" / "fertig – du
    kannst einloggen". Beleg: der Uploader schreibt einen Prüfblock "RaidMasterSyncProbe" in RaidMaster.lua; RaidMaster
    (ab 3.0.23) merkt beim Laden RaidMasterDB.syncProbe {seq, von, t, geladen}. Steht nach dem nächsten Speichern genau
    diese seq drin, hat WoW den übernommenen Stand gelesen (Messung: Sekunden vom WoW-Start bis zum Lesen). Nach 2
    Belegen still; schlägt ein Beleg fehl, nie wieder übernehmen, solange WoW läuft (übernommene Dateien bleiben
    gesichert, AHSentinel bekommt sie als AHSentinelMerge).
Konflikte (S4/S8 f): je Datei gilt "geändert" gegenüber dem zuletzt abgeglichenen Stand (Upload-Reihenfolge, nicht
  Uhrzeit). An beiden Rechnern geändert (oder noch nie abgeglichen und verschieden) -> Konflikt: die Zeiten beider Rechner
  werden auf die Discord-Uhr umgerechnet (Abweichung der Rechner-Uhr wird bei jeder Antwort gemessen); die neuere
  gewinnt; liegen beide weniger als 10 Min. auseinander, gewinnt der schon hochgeladene Stand. Die andere Fassung bleibt
  30 Tage in _sync_backup und wird gemeldet. AHSentinel.lua: die andere Fassung IMMER zusätzlich als eigener Block
  "AHSentinelMerge = { v, von, zeit, grund, db }" (Feldnamen bleiben so; AHSentinel liest von/zeit und from/t) in die
  Datei; AHSentinelDB selbst wird nie verändert.

Alles Netz und alle Prozessabfragen laufen über austauschbare Funktionen (Store, wow_running) – offline testbar.
"""
from __future__ import annotations

import email.utils
import glob
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import uuid

SYNC_CONFIG = "sync_config.json"
BACKUP_DIR = "_sync_backup"
LOCK_FILE = "_sync.lock"
BACKUPS_KEEP = 5                 # gewöhnliche Sicherungen ("vor-abgleich")
LONG_KEEP_DAYS = 30              # Sicherungen aus Konflikten und Übernahmen
LONG_TAGS = ("konflikt", "uebernahme", "uebernommen", "zusammenfuehren")
VERSIONS_KEEP = 10
QUIET_SECONDS = 10               # WoW beendet: SavedVariables so lange unverändert -> hochladen
QUIET_RUNNING_SECONDS = 10       # WoW läuft (/reload, Ausloggen ins Charakter-Menü): so lange Ruhe -> hochladen
PUSH_GAP_RUNNING = 60            # ... aber höchstens 1 Upload je Minute, solange WoW läuft (die letzte Fassung gewinnt)
DELETE_PER_TICK = 5              # alte Fassungen in #sync-daten: so viele Löschversuche je Durchgang
CHECK_REMOTE_SECONDS = 30        # WoW geschlossen: so oft den Index prüfen
CHECK_REMOTE_RUNNING = 120       # WoW läuft: so oft (nur für den Hinweis)
STALE_DAYS = 14                  # so lange unverändert -> nur einmal als Grundstand
# UP-S1 (ab 2.3.8): ein Stand eines anderen Rechners, der so oft hintereinander und so lange nicht lesbar ist, gilt als
# DEFEKT – er blockiert dann nicht mehr das Hochladen dieses Rechners (lokale Dateien bleiben unverändert)
DEFECT_TRIES = 3
DEFECT_SECONDS = 30 * 60
BLOCKED_WARN = 60 * 60          # Selbstkontrolle: so lange kein Upload trotz geänderter Dateien -> "Abgleich blockiert seit …"
CONFLICT_WINDOW = 600            # weniger als 10 Min. auseinander -> Konflikt, schon hochgeladener Stand gewinnt
TAKEOVER_MAX_AGE = 45            # S8 c: nur so kurz nach dem WoW-Start übernehmen
TRANSITION_MAX_GAP = 30          # ... und nur, wenn kurz vorher noch kein WoW lief
PROOFS_NEEDED = 2
PROBE_MAX_AGE = 3 * 86400
LOCK_FRESH = 90
PART_BYTES = 9 * 1024 * 1024     # Discord: höchstens 10 MB je Anhang
INDEX_MAX = 1900                 # Discord: Nachricht höchstens 2000 Zeichen
MERGE_VAR = "AHSentinelMerge"
MERGE_ADDON_FILE = "AHSentinel.lua"
PROBE_VAR = "RaidMasterSyncProbe"
PROBE_FILE = "RaidMaster.lua"
INDEX_MARK = "GSSYNC-INDEX"
RETAIL_LIKE = ("_retail_", "_ptr_", "_xptr_", "_beta_")


def sha(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def machine_name(conf: dict | None = None) -> str:
    name = (conf or {}).get("machine_name") or os.environ.get("COMPUTERNAME") or socket.gethostname() or "Rechner"
    return re.sub(r"[^\w .-]", "", str(name))[:40] or "Rechner"


def fmt_time(t: float | None) -> str:
    return time.strftime("%d.%m. %H:%M", time.localtime(t)) if t else "–"


# ---------------------------------------------------------------------------
# WoW läuft?
# ---------------------------------------------------------------------------
WOW_EXE = re.compile(r"^wow[\w-]*\.exe$", re.I)


def wow_running() -> bool:
    """Windows: tasklist; sonst ps. Im Zweifel True (dann wird nichts geschrieben)."""
    try:
        if sys.platform == "win32":
            out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=15,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
            names = [ln.split('","')[0].strip('"') for ln in out.splitlines() if ln.strip()]
        else:
            out = subprocess.run(["ps", "-A", "-o", "comm="], capture_output=True, text=True, timeout=15).stdout
            names = [os.path.basename(ln.strip()) for ln in out.splitlines()]
        return any(WOW_EXE.match(n) for n in names)
    except Exception:  # noqa: BLE001
        return True


# ---------------------------------------------------------------------------
# Sperre: nur EIN Prozess gleicht ab (laufender Uploader oder Starter) – offen 2
# ---------------------------------------------------------------------------
def write_lock(here: str, now: float | None = None, role: str = "uploader"):
    """role: "uploader" (läuft dauernd) oder "starter" (GoldSentinel-WoW.bat, nur kurz) – ab 2.3.3 (U2)."""
    now = time.time() if now is None else now
    try:
        with open(os.path.join(here, LOCK_FILE), "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "t": now, "rolle": role}, f)
    except OSError:
        pass


def remove_lock(here: str):
    try:
        with open(os.path.join(here, LOCK_FILE), "r", encoding="utf-8") as f:
            if json.load(f).get("pid") != os.getpid():
                return
        os.remove(os.path.join(here, LOCK_FILE))
    except (OSError, ValueError, AttributeError):
        pass


def lock_owner(here: str) -> dict:
    try:
        with open(os.path.join(here, LOCK_FILE), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def lock_active(here: str, now: float | None = None) -> bool:
    """True, wenn ein ANDERER Prozess (der laufende Uploader) in den letzten 90 s abgeglichen hat."""
    now = time.time() if now is None else now
    try:
        with open(os.path.join(here, LOCK_FILE), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("pid") != os.getpid() and now - float(data.get("t") or 0) <= LOCK_FRESH
    except (OSError, ValueError, AttributeError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Nur EIN Uploader je Rechner (ab 2.3.2, T-DU11 a) – auch aus verschiedenen Ordnern
# ---------------------------------------------------------------------------
MUTEX_NAME = "Local\\GoldSentinel-RaidMasterUploader"
_MUTEX = {"handle": None}


def instance_file() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "GoldSentinel", "uploader-instanz.json")


def pid_alive(pid: int) -> bool:
    if not pid or pid == os.getpid():
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            h = k32.OpenProcess(0x1000, False, int(pid))         # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return False
            code = ctypes.c_ulong()
            ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
            k32.CloseHandle(h)
            return bool(ok) and code.value == 259                 # STILL_ACTIVE
        except Exception:  # noqa: BLE001
            return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def instance_info(path: str | None = None) -> dict:
    try:
        with open(path or instance_file(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def pid_cmdline(pid: int) -> str | None:
    """Kommandozeile eines Prozesses (T-DU12): Windows über Win32_Process, sonst /proc. None = unbekannt/kein Prozess."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return None
    if pid <= 0:
        return None
    if sys.platform == "win32":
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command",
                                  f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}').CommandLine"],
                                 capture_output=True, text=True, timeout=15,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout.strip()
            return out or None
        except Exception:  # noqa: BLE001
            return None
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().replace(b"\0", b" ").decode("utf-8", "replace").strip() or None
    except OSError:
        return None


def is_uploader_process(pid) -> bool:
    """T-DU12: lebt der Prozess UND führt er den Uploader aus (uploader.py, nicht der Starter --wow-start)?
    Eine wiederverwendete PID (anderes Programm) zählt nicht."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if not pid_alive(pid):
        return False
    cmd = (pid_cmdline(pid) or "").lower()
    return "uploader.py" in cmd and "--wow-start" not in cmd and "--daten-" not in cmd


def _stale(what: dict, reason: str) -> dict:
    return dict(what, stale=reason)


def instance_running(here: str, path: str | None = None, stale: list | None = None) -> dict | None:
    """Läuft schon ein Uploader? -> {"pid", "ordner", "version"}, sonst None.
    Ab 2.3.3 (T-DU12): Eine Sperre gilt NUR, wenn ihre PID lebt und dieser Prozess uploader.py ausführt. Sperre ohne
    PID, mit totem oder fremdem Prozess (wiederverwendete PID) oder vom Starter ist veraltet -> wird in stale gemeldet
    und übernommen. Windows-Mutex: hält ihn ein Prozess, läuft sicher ein Uploader ab 2.3.2."""
    stale = stale if stale is not None else []
    if sys.platform == "win32" and _MUTEX["handle"] is None:
        try:
            import ctypes
            h = ctypes.windll.kernel32.OpenMutexW(0x00100000, False, MUTEX_NAME)   # SYNCHRONIZE
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                info = instance_info(path)
                return info if info else {"pid": "?", "ordner": "?", "version": "ab 2.3.2"}
        except Exception:  # noqa: BLE001
            pass
    info = instance_info(path)
    if info and info.get("pid") != os.getpid():
        if is_uploader_process(info.get("pid")):
            return info
        stale.append(_stale(info, "Instanz-Datei"))
    owner = lock_owner(here)
    if owner and lock_active(here):
        if owner.get("rolle") == "starter":
            return None                                   # Starter: kurz, wait_for_lock wartet darauf (U2)
        if is_uploader_process(owner.get("pid")):
            return {"pid": int(owner["pid"]), "ordner": here, "version": owner.get("version") or "vor 2.3.2"}
        stale.append(_stale({"pid": owner.get("pid", "?"), "ordner": here,
                             "version": owner.get("version") or "vor 2.3.2"}, "_sync.lock"))
    return None


def instance_acquire(here: str, version: str, path: str | None = None,
                     log=None) -> tuple[bool, dict | None]:
    """Uploader-Start: (True, None) = dieser Prozess ist der einzige; (False, Info) = es läuft wirklich schon einer.
    Veraltete Sperren werden übernommen (Zeile "alte Sperre von <Version> entfernt")."""
    if sys.platform == "win32":
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            h = k32.CreateMutexW(None, False, MUTEX_NAME)
            if h and k32.GetLastError() == 183:                   # ERROR_ALREADY_EXISTS
                k32.CloseHandle(h)
                info = instance_info(path)
                return False, info if info else {"pid": "?", "ordner": "?", "version": "ab 2.3.2"}
            _MUTEX["handle"] = h
        except Exception:  # noqa: BLE001
            pass
    stale: list = []
    other = instance_running(here, path, stale)
    if other:
        return False, other
    for st in stale:
        if st.get("stale") == "_sync.lock":
            try:
                os.remove(os.path.join(here, LOCK_FILE))
            except OSError:
                pass
        if log:
            log(f"Abgleich: alte Sperre von {st.get('version') or '?'} entfernt (PID {st.get('pid', '?')} läuft nicht "
                f"mehr als Uploader).")
    path = path or instance_file()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "ordner": here, "version": version, "t": time.time()}, f)
    except OSError:
        pass
    return True, None


def offer_stop_other(other: dict, ask=None, kill=None, log=None) -> bool:
    """T-DU12: Läuft wirklich ein (alter) Uploader: anbieten, ihn zu beenden. True = beendet, dieser Start darf weiter.
    ask: Frage -> Antwort ("j"/"n"); ohne Antwort in 60 s gilt Nein. kill: PID -> bool."""
    try:
        pid = int(other.get("pid"))
    except (TypeError, ValueError):
        return False
    ask = ask or ask_timeout
    kill = kill or kill_pid
    answer = (ask(f"Alte Version {other.get('version') or '?'} (PID {pid}) beenden und diese starten? (J/N) ") or "").strip()
    if answer.lower() not in ("j", "ja", "y", "yes"):
        return False
    ok = kill(pid)
    if log:
        log(f"Alte Version (PID {pid}) beendet." if ok else f"Alte Version (PID {pid}) liess sich nicht beenden.")
    return bool(ok)


def ask_timeout(prompt: str, seconds: int = 60) -> str:
    """Frage im Fenster; ohne Antwort nach seconds Sekunden: "" (= Nein). Windows ohne Enter nötig für J/N."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    if sys.platform == "win32":
        try:
            import msvcrt
            end = time.time() + seconds
            while time.time() < end:
                if msvcrt.kbhit():
                    c = msvcrt.getwch()
                    sys.stdout.write(c + "\n")
                    return c
                time.sleep(0.1)
        except Exception:  # noqa: BLE001
            pass
        sys.stdout.write("\n")
        return ""
    try:
        import select
        r, _, _ = select.select([sys.stdin], [], [], seconds)
        return sys.stdin.readline() if r else ""
    except Exception:  # noqa: BLE001
        return ""


def kill_pid(pid: int) -> bool:
    try:
        if sys.platform == "win32":
            r = subprocess.run(["taskkill", "/PID", str(int(pid)), "/T", "/F"], capture_output=True, timeout=20,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            ok = r.returncode == 0
        else:
            import signal
            os.kill(int(pid), signal.SIGTERM)
            ok = True
    except Exception:  # noqa: BLE001
        return False
    for _ in range(20):
        if not pid_alive(int(pid)):
            return ok
        time.sleep(0.25)
    return False


def instance_release(path: str | None = None):
    info = instance_info(path)
    if info.get("pid") == os.getpid():
        try:
            os.remove(path or instance_file())
        except OSError:
            pass


def startup_entries() -> list[str]:
    """Autostart-Einträge, die nach dem Uploader aussehen (Windows-Autostart-Ordner) – für den Hinweis "doppelt"."""
    folder = os.path.join(os.environ.get("APPDATA") or "", "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    try:
        return sorted(n for n in os.listdir(folder) if "uploader" in n.lower() or "goldsentinel" in n.lower())
    except OSError:
        return []


def wait_for_lock(here: str, sleep=time.sleep, now=time.time, log=None, max_wait: float = LOCK_FRESH + 30) -> bool:
    """Uploader-Start (offen 2): gleicht gerade ein anderer Prozess ab (Starter), erst warten, bis er fertig ist.
    True = frei. Nach max_wait wird nicht länger gewartet (Sperre gilt dann ohnehin als alt)."""
    start, said = now(), False

    def busy() -> bool:
        if not lock_active(here, now()):
            return False
        owner = lock_owner(here)
        try:
            pid = int(owner.get("pid") or 0)
        except (TypeError, ValueError):
            return False
        if owner.get("rolle") == "starter":
            return pid_alive(pid)               # Starter gleicht kurz ab: warten, solange er lebt
        return is_uploader_process(pid)         # tot oder fremder Prozess: nicht warten (U2, T-DU12)
    while busy():
        if not said and log:
            log("Abgleich: GoldSentinel-WoW.bat gleicht gerade ab – warte, bis sie fertig ist ...")
            said = True
        if now() - start >= max_wait:
            return False
        sleep(2)
    return True


# ---------------------------------------------------------------------------
# Dateien
# ---------------------------------------------------------------------------
def account_dir(sv_lua_path: str) -> str:
    """…/WTF/Account/<KONTO>/SavedVariables/RaidMaster.lua -> …/WTF/Account/<KONTO>"""
    return os.path.dirname(os.path.dirname(os.path.abspath(sv_lua_path)))


def find_roots(search_roots: list[str] | None = None) -> dict[str, str]:
    """Alle WoW-Konten auf diesem Rechner: "<Spielversion-Ordner>/<KONTO>" -> …/WTF/Account/<KONTO>.
    Spielversion-Ordner = der Ordner, in dem WTF liegt (z. B. _forever_, _anniversary_). So gleicht der Abgleich jede
    Spielversion für sich ab, egal wo WoW auf dem anderen Rechner installiert ist (ab 2.1.1)."""
    import string
    if search_roots is None:
        if os.name == "nt":
            search_roots = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
        else:
            search_roots = [os.path.expanduser("~")]
    out = {}
    for root in search_roots:
        for depth in range(0, 4):
            pat = os.path.join(root, *(["*"] * depth), "WTF", "Account", "*", "SavedVariables")
            for sv in glob.glob(pat):
                acc = os.path.dirname(sv)
                flavor = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(acc))))
                name = re.sub(r"[^\w#.-]", "_", flavor) or "wow"
                key = name + "/" + os.path.basename(acc)
                out.setdefault(key, os.path.normpath(acc))
    return out


def local_files(acc: str) -> dict[str, str]:
    """rel. Pfad (mit /) -> voller Pfad. Nur *.lua in den SavedVariables (Konto und Charaktere)."""
    out = {}
    pats = [os.path.join(acc, "SavedVariables", "*.lua"), os.path.join(acc, "*", "*", "SavedVariables", "*.lua")]
    for pat in pats:
        for fn in glob.glob(pat):
            if not os.path.isfile(fn) or not fn.lower().endswith(".lua"):
                continue
            rel = os.path.relpath(fn, acc).replace(os.sep, "/")
            if rel.split("/")[0] == BACKUP_DIR:
                continue
            out[rel] = fn
    return out


def read(fn: str) -> bytes:
    with open(fn, "rb") as f:
        return f.read()


def write_atomic(fn: str, data: bytes, mtime: float | None = None):
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    tmp = fn + ".gssync.tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, fn)
    if mtime:
        try:
            os.utime(fn, (mtime, mtime))
        except OSError:
            pass


def make_package(files: dict[str, dict], machine: str, now: float, off: float = 0.0) -> bytes:
    """files: rel -> {"data": bytes, "mtime": float, "machine": str, "off": float}. tar.gz mit manifest.json.
    off = Abweichung der Uhr des Rechners gegenüber Discord (Sekunden; Discord-Zeit = mtime + off)."""
    manifest = {"v": 2, "machine": machine, "time": now, "off": round(off, 1),
                "files": {rel: {"sha": sha(f["data"]), "mtime": f["mtime"], "machine": f.get("machine") or machine,
                                "off": round(float(f.get("off", off) or 0.0), 1), "size": len(f["data"])}
                          for rel, f in files.items()}}
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=9) as tar:
        def add(name, data):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = int(now)
            tar.addfile(info, io.BytesIO(data))
        add("manifest.json", json.dumps(manifest, ensure_ascii=False).encode("utf-8"))
        for rel, f in sorted(files.items()):
            add("files/" + rel, f["data"])
    return buf.getvalue()


def read_package(blob: bytes) -> tuple[dict, dict[str, bytes]]:
    manifest, data = None, {}
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            name = m.name
            if name.startswith("/") or ".." in name.split("/"):
                continue                   # nie ausserhalb schreiben
            raw = tar.extractfile(m).read()
            if name == "manifest.json":
                manifest = json.loads(raw.decode("utf-8"))
            elif name.startswith("files/") and name.endswith(".lua"):
                data[name[len("files/"):]] = raw
    if not isinstance(manifest, dict):
        raise ValueError("Paket ohne manifest.json")
    return manifest, data


# ---------------------------------------------------------------------------
# Oberste Blöcke einer SavedVariables-Datei (AHSentinelMerge, RaidMasterSyncProbe)
# ---------------------------------------------------------------------------
TOP_ASSIGN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*) = ", re.M)


def top_blocks(text: str) -> dict[str, str]:
    """Oberste Zuweisungen einer SavedVariables-Datei: Name -> Wert-Text."""
    ms = list(TOP_ASSIGN.finditer(text))
    out = {}
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out[m.group(1)] = text[m.end():end].rstrip()
    return out


def remove_block(data: bytes, var: str) -> bytes:
    """Obersten Block "var = …" entfernen (sonst unverändert)."""
    text = data.decode("utf-8", errors="surrogateescape")
    ms = list(TOP_ASSIGN.finditer(text))
    for i, m in enumerate(ms):
        if m.group(1) == var:
            end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
            return (text[:m.start()] + text[end:]).encode("utf-8", errors="surrogateescape")
    return data


def lua_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def add_merge_block(winner: bytes, older: bytes, machine: str, when: float) -> bytes | None:
    """AHSentinelMerge = { v, von, zeit, grund, db = <andere AHSentinelDB> } an die Gewinner-Datei hängen.
    Feldnamen: v, von (Rechner), zeit (Unix-Zeit), grund ("konflikt"), db (vollständige andere AHSentinelDB).
    None, wenn die andere keine AHSentinelDB hat, beide gleich sind oder die Gewinner-Datei schon einen offenen Block
    hat."""
    old = top_blocks(older.decode("utf-8", errors="surrogateescape"))
    db = old.get("AHSentinelDB")
    text = winner.decode("utf-8", errors="surrogateescape")
    blocks = top_blocks(text)
    if not db or MERGE_VAR in blocks or blocks.get("AHSentinelDB") == db:
        return None
    block = (f"{MERGE_VAR} = {{\n\t[\"v\"] = 1,\n\t[\"von\"] = {lua_quote(machine)},\n\t[\"zeit\"] = {int(when)},\n"
             f"\t[\"grund\"] = \"konflikt\",\n\t[\"db\"] = {db},\n}}\n")
    if not text.endswith("\n"):
        text += "\n"
    return (text + block).encode("utf-8", errors="surrogateescape")


def add_probe(data: bytes, seq: int, machine: str, when: float) -> bytes:
    """Prüfblock für den Beleg S8 c an RaidMaster.lua hängen (einen alten ersetzen)."""
    text = remove_block(data, PROBE_VAR).decode("utf-8", errors="surrogateescape")
    if text and not text.endswith("\n"):
        text += "\n"
    text += (f"{PROBE_VAR} = {{\n\t[\"seq\"] = {int(seq)},\n\t[\"von\"] = {lua_quote(machine)},\n"
             f"\t[\"t\"] = {int(when)},\n}}\n")
    return text.encode("utf-8", errors="surrogateescape")


PROBE_SEEN = re.compile(r'\["syncProbe"\]\s*=\s*\{(.*?)\}', re.S)


def probe_seen(data: bytes) -> dict | None:
    """RaidMasterDB.syncProbe aus RaidMaster.lua: {"seq", "von", "geladen"} oder None."""
    text = data.decode("utf-8", errors="replace")
    db = top_blocks(text).get("RaidMasterDB") or ""
    m = PROBE_SEEN.search(db)
    if not m:
        return None
    body = m.group(1)

    def num(key):
        x = re.search(r'\["' + key + r'"\]\s*=\s*(-?[\d.]+)', body)
        return float(x.group(1)) if x else 0.0
    von = re.search(r'\["von"\]\s*=\s*"((?:[^"\\]|\\.)*)"', body)
    return {"seq": int(num("seq")), "von": von.group(1) if von else "", "geladen": num("geladen")}


# ---------------------------------------------------------------------------
# Speicher: Webhook in #sync-daten
# ---------------------------------------------------------------------------
class StoreError(Exception):
    pass


class WebhookStore:
    """Eine Index-Nachricht (Inhalt JSON) + je Paket eine oder mehrere Nachrichten mit Anhang.
    Misst bei jeder Antwort die Abweichung der eigenen Uhr gegenüber Discord (clock_offset) und hält Discords
    Grenzen ein (wait_until)."""

    def __init__(self, webhook_url: str, index_id: str, timeout: int = 60):
        self.url = webhook_url.rstrip("/")
        self.index_id = str(index_id)
        self.timeout = timeout
        self.clock_offset = 0.0
        self.wait_until = 0.0

    def _limits(self, headers):
        if headers is None:
            return
        try:
            date = headers.get("Date")
            if date:
                self.clock_offset = email.utils.parsedate_to_datetime(date).timestamp() - time.time()
        except (TypeError, ValueError, OverflowError):
            pass
        try:
            if str(headers.get("X-RateLimit-Remaining") or "") == "0":
                self.wait_until = max(self.wait_until,
                                      time.time() + float(headers.get("X-RateLimit-Reset-After") or 1))
        except (TypeError, ValueError):
            pass

    def _req(self, method: str, path: str = "", data: bytes | None = None, ctype: str | None = None, query: str = ""):
        wait = self.wait_until - time.time()
        if wait > 0:
            raise StoreError(f"Discord bremst – nächster Versuch in {int(wait) + 1} s")
        url = self.url + path + query
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("User-Agent", "GoldSentinel-Uploader")
        if ctype:
            req.add_header("Content-Type", ctype)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                self._limits(getattr(resp, "headers", None))
                body = resp.read()
                return json.loads(body.decode("utf-8")) if body else None
        except urllib.error.HTTPError as e:
            self._limits(getattr(e, "headers", None))
            if e.code == 429:
                retry = 5.0
                try:
                    retry = float(json.loads(e.read().decode("utf-8")).get("retry_after") or retry)
                except (ValueError, AttributeError, OSError, TypeError):
                    try:
                        retry = float((e.headers or {}).get("Retry-After") or retry)
                    except (TypeError, ValueError):
                        pass
                self.wait_until = max(self.wait_until, time.time() + retry)
                raise StoreError(f"Discord bremst – nächster Versuch in {int(retry) + 1} s") from None
            raise StoreError(f"Discord antwortet {e.code}") from None
        except (urllib.error.URLError, OSError, ValueError):
            raise StoreError("kein Netz oder Discord nicht erreichbar") from None

    def read_index(self) -> dict:
        msg = self._req("GET", f"/messages/{self.index_id}")
        content = (msg or {}).get("content") or ""
        m = re.search(r"\{.*\}", content, re.S)
        if not m:
            return {}
        try:
            return json.loads(m.group(0))
        except ValueError:
            return {}

    def write_index(self, index: dict):
        content = INDEX_MARK + " – nicht ändern\n" + json.dumps(index, separators=(",", ":"))
        if len(content) > 1990:
            raise StoreError("Index zu lang")
        self._req("PATCH", f"/messages/{self.index_id}", json.dumps({"content": content}).encode("utf-8"),
                  "application/json")

    def put_part(self, name: str, blob: bytes, note: str) -> str:
        boundary = "----GSSync" + uuid.uuid4().hex
        payload = {"content": note, "allowed_mentions": {"parse": []}}
        body = b"".join([
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="payload_json"\r\nContent-Type: application/json\r\n\r\n',
            json.dumps(payload).encode("utf-8"), b"\r\n",
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="files[0]"; filename="{name}"\r\n'.encode(),
            b"Content-Type: application/octet-stream\r\n\r\n", blob, b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ])
        msg = self._req("POST", "", body, f"multipart/form-data; boundary={boundary}", "?wait=true")
        if not msg or not msg.get("id"):
            raise StoreError("Discord hat das Paket nicht bestätigt")
        return str(msg["id"])

    def get_part(self, msg_id: str) -> bytes:
        """Anhang einer Nachricht laden. UP-S1 (ab 2.3.8): kommt er leer (0 Byte) oder mit HTTP-Fehler, wird die Nachricht
        EINMAL neu gelesen (frische, signierte CDN-Adresse) und der Anhang neu geholt; erst dann aufgeben – mit Grund
        (HTTP-Status, Länge) für die Diagnose."""
        why = ""
        for _ in range(2):
            msg = self._req("GET", f"/messages/{msg_id}")
            att = ((msg or {}).get("attachments") or [None])[0]
            if not att or not att.get("url"):
                raise StoreError("Paket nicht mehr vorhanden")
            req = urllib.request.Request(att["url"], headers={"User-Agent": "GoldSentinel-Uploader"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = resp.read()
                    status = getattr(resp, "status", None) or 200
            except urllib.error.HTTPError as e:
                why = f"HTTP {e.code}"
                continue
            except (urllib.error.URLError, OSError):
                why = "kein Netz"
                continue
            if data:
                return data
            size = att.get("size")
            why = f"0 Byte, HTTP {status}" + (f", laut Discord {size} Byte" if size is not None else "")
        raise StoreError(f"Paket nicht ladbar ({why})")

    def delete_part(self, msg_id: str) -> bool:
        """Nachricht samt Anhang löschen. True = weg (auch: war schon weg), False = später erneut versuchen."""
        try:
            self._req("DELETE", f"/messages/{msg_id}")
            return True
        except StoreError as e:
            return "404" in str(e)


def load_sync_config(here: str) -> dict | None:
    try:
        with open(os.path.join(here, SYNC_CONFIG), "r", encoding="utf-8") as f:
            conf = json.load(f)
    except (OSError, ValueError):
        return None
    if not str(conf.get("sync_webhook_url") or "").startswith("https://") or not conf.get("sync_index_id"):
        return None
    return conf


def index_roots(idx: dict | None) -> dict[str, dict]:
    """Einträge des Index: v2 je Spielversion/Konto; v1 (Uploader 2.1.x) als ein Eintrag "*" für alles."""
    if not isinstance(idx, dict):
        return {}
    if isinstance(idx.get("r"), dict):
        out = {}
        for k, e in idx["r"].items():
            if isinstance(e, list) and len(e) >= 4 and isinstance(e[1], list):
                out[str(k)] = {"rev": int(e[0] or 0), "parts": [str(p) for p in e[1]], "machine": e[2],
                               "time": e[3]}
        return out
    if idx.get("parts"):
        return {"*": {"rev": int(idx.get("seq") or 0), "parts": [str(p) for p in idx["parts"]],
                      "machine": idx.get("machine"), "time": idx.get("time")}}
    return {}


def index_over_defect(idx: dict | None) -> dict[str, list]:
    """UP-S1-2 (ab 2.3.9): Index-Feld "ud" = {Spielversion/Konto: [rev des defekten Stands, Rechner des defekten Stands]}.
    Steht dort, dass über den Stand DIESES Rechners hinweggeschrieben wurde, gilt beim Übernehmen jede abweichende Datei
    als Konflikt (nie still ersetzen). Alte Uploader ignorieren das Feld."""
    ud = (idx or {}).get("ud") if isinstance(idx, dict) else None
    out = {}
    if isinstance(ud, dict):
        for k, v in ud.items():
            if isinstance(v, list) and len(v) >= 2:
                try:
                    out[str(k)] = [int(v[0] or 0), str(v[1] or "")]
                except (TypeError, ValueError):
                    pass
    return out


def index_parts(idx: dict | None) -> list[str]:
    """Alle Nachrichten des aktuellen Stands (für Tests und Aufräumen)."""
    return [p for e in index_roots(idx).values() for p in e["parts"]]


def flavor_label(key: str) -> str:
    """"_forever_/KONTO" -> "_forever_" (Kontoname nie ins Protokoll)."""
    return key.split("/")[0] if key and key != "*" else "Konto"


# ---------------------------------------------------------------------------
# Abgleich
# ---------------------------------------------------------------------------
class Sync:
    """Hält den Stand dieses Rechners in st["sync"] (uploader_state.json):
    seq (zuletzt gesehener Index), revs {Spielversion/Konto: rev} (zuletzt übernommene/hochgeladene Pakete),
    files {rel: sha} (Stand nach dem letzten Abgleich = "Basis"), Anzeige-Daten, Beleg S8 c."""

    def __init__(self, store, acc, st: dict, save, machine: str, log, is_wow_running=wow_running,
                 notify=None, backup_dir: str | None = None, clock_offset=None):
        """acc: ein Konto-Ordner (str) oder {"<Spielversion>/<KONTO>": Konto-Ordner} (ab 2.1.1: alle Spielversionen).
        clock_offset: Funktion -> Sekunden, um die Discord-Zeit vor der Uhr dieses Rechners liegt."""
        self.store, self.st, self.save, self.me = store, st, save, machine
        self.roots = dict(acc) if isinstance(acc, dict) else {"": acc}
        self.backup_dir = backup_dir
        self.log, self.is_wow_running = log, is_wow_running
        self.notify = notify or (lambda text: None)
        self.clock_offset = clock_offset or (lambda: float(getattr(store, "clock_offset", 0.0) or 0.0))
        s = st.setdefault("sync", {})
        s.setdefault("seq", 0)
        s.setdefault("files", {})
        s.setdefault("revs", {})
        self.s = s
        self.next_remote = 0.0
        self.remote: dict | None = None       # zuletzt gelesener Index
        self.warned_seq = 0
        self.last_error = ""
        self.messages: list[str] = []
        self._cache: dict[str, tuple] = {}    # Pfad -> (Grösse, mtime, sha) – offen 5
        self.wow = {"running": None, "first_seen": 0.0, "last_off": 0.0, "sv_newest": 0.0, "transition": False,
                    "takeover_done": False}
        self.skipped_logged: set[str] = set()
        self.last_taken: list[str] = []
        self.retry_at = 0.0                   # nach einem Fehler nicht alle 5 s erneut übers Netz

    # -- Anzeige (S5)
    def status_line(self) -> str:
        r = self.remote or {}
        up = self.s.get("last_upload")
        newest = f"{r.get('machine', '?')} {fmt_time(r.get('time'))}" if r.get("seq") else "–"
        here = "NICHT aktuell" if self.remote_newer() else "aktuell"
        line = (f"Abgleich: zuletzt hochgeladen {fmt_time(up)} ({self.s.get('last_upload_machine') or self.me})"
                if up else "Abgleich: noch nichts hochgeladen")
        line += f" · neuester Stand: {newest} · dieser Rechner {here}"
        if self.last_error:
            line += f" · FEHLER: {self.last_error}"
        bad = set(self.s.get("defekt") or [])
        if any(f"{k}:{e['rev']}" in bad for k, e in index_roots(self.remote).items()):
            line += " · defekter Stand des anderen Rechners übergangen (dort einmal WoW beenden)"
        since = self.s.get("blocked_since")
        if since and time.time() - float(since) >= BLOCKED_WARN:
            line += " · " + self.blocked_text()
        return line

    def _say(self, text: str):
        self.messages.append(text)
        self.log(text)

    # -- Dateien
    @property
    def acc(self) -> str:
        return next(iter(self.roots.values()))

    def root_of(self, rel: str) -> str:
        return "" if "" in self.roots else "/".join(rel.split("/")[:2])

    def installed(self, key: str) -> bool:
        return key == "*" or key in self.roots

    def _path(self, rel: str) -> str | None:
        """Voller Pfad für rel. Pfad, oder None, wenn die Spielversion hier nicht installiert ist."""
        if "" in self.roots:
            return os.path.join(self.roots[""], *rel.split("/"))
        parts = rel.split("/")
        root = self.roots.get("/".join(parts[:2]))
        return os.path.join(root, *parts[2:]) if root else None

    @staticmethod
    def _clean(rel: str, data: bytes) -> bytes:
        """Was abgeglichen wird: RaidMaster.lua ohne den eigenen Prüfblock (S8 c), AHSentinel.lua ohne einen offenen
        AHSentinelMerge-Block (ab 2.3.0, offen 3 – der Block bleibt nur auf diesem Rechner)."""
        name = rel.split("/")[-1]
        if name == PROBE_FILE and PROBE_VAR.encode() in data:
            return remove_block(data, PROBE_VAR)
        if name == MERGE_ADDON_FILE and MERGE_VAR.encode() in data and MERGE_VAR in top_blocks(
                data.decode("utf-8", errors="surrogateescape")):
            return remove_block(data, MERGE_VAR)
        return data

    def _scan(self) -> dict[str, dict]:
        """rel -> {path, mtime, size, sha}. Gelesen und gehasht wird nur, was sich seit dem letzten Blick geändert hat
        (Grösse oder Zeit) – offen 5."""
        out = {}
        for prefix, acc in self.roots.items():
            for rel, fn in local_files(acc).items():
                key = f"{prefix}/{rel}" if prefix else rel
                try:
                    stt = os.stat(fn)
                except OSError:
                    continue
                c = self._cache.get(fn)
                if c and c[0] == stt.st_size and c[1] == stt.st_mtime:
                    h = c[2]
                else:
                    try:
                        h = sha(self._clean(key, read(fn)))
                    except OSError:
                        continue
                    self._cache[fn] = (stt.st_size, stt.st_mtime, h)
                out[key] = {"path": fn, "mtime": stt.st_mtime, "size": stt.st_size, "sha": h}
        return out

    def _newest(self, scan: dict | None = None) -> float:
        scan = self._scan() if scan is None else scan
        return max([f["mtime"] for f in scan.values()] or [0.0])

    def _skip_root(self, key: str, files: dict[str, dict], now: float) -> bool:
        """S8 e: Retail (PTR, Beta) seit 14 Tagen nicht gespielt und noch nie im Speicher -> gar nicht abgleichen."""
        if not key.split("/")[0].lower().startswith(RETAIL_LIKE) or key in index_roots(self.remote):
            return False
        return now - self._newest(files) > STALE_DAYS * 86400

    def local_changes(self, now: float | None = None) -> tuple[list[str], float]:
        """(geänderte Dateien gegenüber dem letzten Abgleich, jüngste Änderungszeit)"""
        now = time.time() if now is None else now
        scan = self._scan()
        groups: dict[str, dict] = {}
        for rel, f in scan.items():
            groups.setdefault(self.root_of(rel), {})[rel] = f
        changed = sorted(rel for key, files in groups.items() if not self._skip_root(key, files, now)
                         for rel, f in files.items() if self.s["files"].get(rel) != f["sha"])
        return changed, self._newest(scan)

    def _backup(self, files: dict[str, bytes], now: float, tag: str) -> str:
        root = self.backup_dir or os.path.join(self.acc, BACKUP_DIR)
        dest = os.path.join(root, time.strftime("%Y%m%d-%H%M%S", time.localtime(now)) + "-" + tag)
        n = 2
        while os.path.exists(dest):
            dest = os.path.join(root, time.strftime("%Y%m%d-%H%M%S", time.localtime(now)) + f"-{n}-" + tag)
            n += 1
        for rel, data in files.items():
            write_atomic(os.path.join(dest, *rel.split("/")), data)
        dirs = sorted(d for d in glob.glob(os.path.join(root, "*")) if os.path.isdir(d))
        short = [d for d in dirs if not d.endswith(LONG_TAGS)]
        for old in short[:-BACKUPS_KEEP]:
            shutil.rmtree(old, ignore_errors=True)
        for d in dirs:
            if d.endswith(LONG_TAGS) and d != dest:
                try:
                    made = time.mktime(time.strptime(os.path.basename(d)[:15], "%Y%m%d-%H%M%S"))
                except ValueError:
                    continue
                if now - made > LONG_KEEP_DAYS * 86400:
                    shutil.rmtree(d, ignore_errors=True)
        return dest

    # -- Index
    def check_remote(self, now: float | None = None, force: bool = False,
                     every: float = CHECK_REMOTE_SECONDS) -> dict | None:
        now = time.time() if now is None else now
        if not force and now < self.next_remote:
            return self.remote
        if float(getattr(self.store, "wait_until", 0.0) or 0.0) > time.time():
            return self.remote if not force else None        # Discord bremst: still warten (S8 b)
        self.next_remote = now + every
        try:
            self.remote = self.store.read_index()
            self.last_error = ""
        except StoreError as e:
            self.last_error = str(e)
            self._say(f"Abgleich: {e} – lokale Dateien bleiben unverändert, neuer Versuch später.")
            return None
        if int((self.remote or {}).get("seq") or 0) > int(self.s.get("seq") or 0) and not self.pending():
            self.s["seq"] = int(self.remote.get("seq") or 0)   # nur Spielversionen, die es hier nicht gibt
        return self.remote

    def pending(self) -> list[str]:
        """Spielversionen/Konten mit neuerem Stand eines ANDEREN Rechners, die hier installiert sind.
        Ab 2.3.2 (T-DU11): Was dieser Rechner selbst hochgeladen hat, ist nie "neuer" – auch nicht, wenn ein zweiter
        Prozess mit älterem Zustand nachsieht."""
        out = []
        for key, e in index_roots(self.remote).items():
            if str(e.get("machine") or "") == self.me:
                continue
            if f"{key}:{e['rev']}" in (self.s.get("defekt") or []):
                continue                                    # UP-S1: als defekt erkannt -> blockiert nicht mehr
            if self.installed(key) and e["rev"] > int(self.s["revs"].get(key) or 0):
                out.append(key)
        return sorted(out)

    def pending_text(self) -> str:
        """Wer, wann, was: "vom Laptop (12.11. 20:15, _forever_)" – je offenem Stand der richtige Rechner."""
        entries = index_roots(self.remote)
        by: dict[str, list] = {}
        for key in self.pending():
            e = entries[key]
            by.setdefault(str(e.get("machine") or "anderen Rechner"), []).append(e)
        parts = []
        for machine, es in sorted(by.items()):
            labels = ", ".join(sorted({flavor_label(k) for k, e in entries.items() if e in es}))
            newest = max(float(e.get("time") or 0) for e in es)
            parts.append(f"vom {machine} ({fmt_time(newest)}, {labels})")
        return " und ".join(parts) or "vom anderen Rechner"

    # -- UP-S1 (ab 2.3.8): unlesbarer Stand eines anderen Rechners
    def _unreadable(self, key, e: dict, now: float, err) -> None:
        """Zählt Fehlversuche je Stand (Spielversion/Konto + rev). Meldung nur EINMAL je Stand. Nach DEFECT_TRIES
        Versuchen über mindestens DEFECT_SECONDS gilt er als defekt: er blockiert nicht mehr, dieser Rechner lädt seinen
        Stand normal hoch (lokale Fassung vorher gesichert). Lokale Dateien werden nie überschrieben."""
        if key is None or "rev" not in e:
            self._say(f"Abgleich: neuer Stand nicht lesbar ({err}) – lokale Dateien unverändert.")
            return
        mark = f"{key}:{e['rev']}"
        alive = {f"{k}:{x['rev']}" for k, x in index_roots(self.remote).items()}
        unl = {m: v for m, v in (self.s.get("unlesbar") or {}).items() if m in alive}
        n, first = (unl.get(mark) or [0, now])[:2]
        n += 1
        unl[mark] = [n, first]
        self.s["unlesbar"] = unl
        if n == 1:
            self._say(f"Abgleich: neuer Stand nicht lesbar ({err}) – lokale Dateien unverändert, "
                      "neuer Versuch jede Minute.")
        if n >= DEFECT_TRIES and now - float(first) >= DEFECT_SECONDS:
            unl.pop(mark, None)
            self.s["defekt"] = (list(self.s.get("defekt") or []) + [mark])[-50:]
            local = {rel: f for rel, f in self._scan().items() if self.root_of(rel) == key}
            if local:
                try:
                    self._backup({rel: read(f["path"]) for rel, f in local.items()}, now, "vor-defektem-stand")
                except OSError:
                    pass
            who = str(e.get("machine") or "anderen Rechner")
            text = (f"Stand des anderen Rechners ({who}, {fmt_time(e.get('time'))}) defekt – hier wird weiter "
                    "hochgeladen, dort bitte einmal WoW beenden.")
            self._say("Abgleich: " + text)
            self.notify(text)
            self.last_error = ""
            self.retry_at = now
        self.save()

    def _note_blocked(self, now: float, uploaded: bool = False) -> None:
        """Selbstkontrolle (UP-S1): geänderte Dateien, aber seit über BLOCKED_WARN kein Upload -> einmal melden und in der
        Statuszeile "Abgleich blockiert seit … (Grund)" zeigen. uploaded=True setzt zurück."""
        if uploaded:
            if self.s.pop("blocked_since", None) is not None:
                self.s.pop("blocked_why", None)
                self.s.pop("blocked_told", None)
            return
        try:
            changed, _ = self.local_changes(now)
        except OSError:
            return
        if not changed:
            if self.s.pop("blocked_since", None) is not None:
                self.s.pop("blocked_why", None)
                self.s.pop("blocked_told", None)
                self.save()
            return
        if not self.s.get("blocked_since"):
            self.s["blocked_since"] = now
            self.save()
        pend = self.pending()
        self.s["blocked_why"] = (self.last_error or
                                 (f"neuerer Stand {self.pending_text()} noch nicht übernommen" if pend else
                                  "wartet auf WoW-Ende"))
        if now - float(self.s["blocked_since"]) >= BLOCKED_WARN and not self.s.get("blocked_told"):
            self.s["blocked_told"] = True
            self._say(self.blocked_text())
            self.save()

    def blocked_text(self) -> str:
        since = self.s.get("blocked_since")
        return f"Abgleich blockiert seit {fmt_time(since)} ({self.s.get('blocked_why') or '?'})" if since else ""

    def remote_newer(self) -> bool:
        return bool(self.pending())

    # -- Herunterladen
    def pull(self, now: float | None = None, takeover: bool = False) -> bool:
        """Neueren Stand übernehmen (nur wenn WoW nicht läuft; takeover=True nur für S8 c). True = nichts mehr offen."""
        now = time.time() if now is None else now
        self.last_taken = []
        if self.check_remote(now, force=True) is None:
            return False
        pend = self.pending()
        if not pend:
            return True
        r = self.remote
        if not takeover and self.is_wow_running():
            # höchstens EIN Hinweis je echtem neuem Stand eines anderen Rechners (auch über einen Neustart hinweg)
            entries_now = index_roots(r)
            marks = [f"{k}:{entries_now[k]['rev']}" for k in pend]
            warned = list(self.s.get("warned") or [])
            if any(m not in warned for m in marks):
                text = f"Neuerer Stand {self.pending_text()} – WoW beenden, dann übernehmen."
                self._say("Abgleich: " + text)
                self.notify(text)
                self.s["warned"] = (warned + [m for m in marks if m not in warned])[-50:]
                self.save()
            return False
        entries = index_roots(r)
        packages = []
        cur = None
        try:
            for key in pend:
                cur = key
                e = entries[key]
                manifest, files = read_package(b"".join(self.store.get_part(p) for p in e["parts"]))
                packages.append((key, e, manifest, files))
        except (StoreError, ValueError, tarfile.TarError, OSError) as e:
            self.last_error = str(e)
            self.retry_at = now + 60
            self._unreadable(cur, entries.get(cur) or {}, now, e)
            return False
        unl = self.s.get("unlesbar") or {}
        for key, e, _, _ in packages:
            unl.pop(f"{key}:{e['rev']}", None)
        local = self._scan()
        take, plain, conf, conflicts, base_new, crels = {}, {}, {}, [], {}, set()
        over = index_over_defect(r)
        for key, e, manifest, files in packages:
            meta = manifest.get("files") or {}
            # UP-S1-2: über den (defekten) Stand DIESES Rechners hinweggeschrieben -> jede abweichende Datei ist Konflikt
            ov = over.get(key) or [0, ""]
            forced = ov[1] == self.me and f"{key}:{ov[0]}" not in (self.s.get("ud_done") or [])
            moff = float(manifest.get("off") or 0.0)
            for rel, data in files.items():
                if not self._safe_rel(rel) or (key != "*" and self.root_of(rel) != key) or self._path(rel) is None:
                    continue
                rsha = sha(data)
                base_new[rel] = rsha
                cur = local.get(rel)
                if cur is None:
                    take[rel] = data
                    continue
                if cur["sha"] == rsha:
                    continue
                base = self.s["files"].get(rel)
                if cur["sha"] == base and not forced:
                    take[rel] = data                                # hier nicht geändert -> übernehmen
                    plain[rel] = read(cur["path"])
                    continue
                if rsha == base and not forced:
                    continue                                        # nur hier geändert -> bleibt, geht hoch
                # an beiden Rechnern geändert – oder noch nie abgeglichen und verschieden (offen 1 a): Konflikt
                m = meta.get(rel) or {}
                ldata = read(cur["path"])
                rmach = re.sub(r"[^\w .-]", "", str(m.get("machine") or e.get("machine") or "")) or "anderer Rechner"
                rt = float(m.get("mtime") or 0) + float(m.get("off", moff) or 0.0)      # Discord-Zeit
                lt = cur["mtime"] + self.clock_offset()
                close = abs(rt - lt) < CONFLICT_WINDOW
                crels.add(rel)
                if close or rt > lt:
                    winner, older, wname, oname, wt, ot = data, ldata, rmach, self.me, rt, lt
                    take[rel] = data
                    conf[rel + ".lokal"] = ldata
                else:
                    winner, older, wname, oname, wt, ot = ldata, data, self.me, rmach, lt, rt
                    conf[rel + "." + rmach] = data
                is_ah = rel.split("/")[-1] == MERGE_ADDON_FILE
                merged = add_merge_block(winner, older, oname, now) if is_ah else None
                if merged is not None:
                    take[rel] = merged
                how = ("innerhalb von 10 Min." if close else "beide") + " geändert"
                if base is None:
                    how += " (noch nie abgeglichen)"
                note = ""
                if is_ah:
                    note = (" (AHSentinel führt ihn beim nächsten Login zusammen)" if merged is not None else
                            " (offene Zusammenführung vorhanden – Stand nur gesichert)")
                conflicts.append(f"{rel.split('/')[-1]}: {oname} {fmt_time(ot)} und {wname} {fmt_time(wt)} {how} – "
                                 f"{wname}-Stand übernommen, {oname}-Stand gesichert{note}")
        if not takeover and self.is_wow_running():          # nochmals: WoW darf beim Schreiben nie laufen
            return False
        before = {rel: read(local[rel]["path"]) for rel in take if rel in local and rel not in plain}
        before.update(plain)
        if takeover and (take or before):
            # S8 c: alter Stand und übernommener Stand 30 Tage aufheben (falls WoW doch schon gelesen hat)
            if before:
                self._backup(before, now, "uebernahme")
            self.s["takeover_copy"] = self._backup(dict(take), now, "uebernommen")
        elif before:
            self._backup(before, now, "vor-abgleich")
        if conf:
            self._backup(conf, now, "konflikt")
        for rel, data in take.items():
            m = {}
            for _, _, manifest, files in packages:
                if rel in files:
                    m = (manifest.get("files") or {}).get(rel) or {}
            mt = float(m.get("mtime") or 0) or None
            if rel.split("/")[-1] == MERGE_ADDON_FILE and rel in local:
                data = self._keep_open_merge(read(local[rel]["path"]), data)
            write_atomic(self._path(rel), data, None if rel in crels else mt)
        self.s["files"].update(base_new)
        for key, e, _, _ in packages:
            self.s["revs"][key] = e["rev"]
            ov = over.get(key) or [0, ""]
            if ov[1] == self.me:            # UP-S1-2: nur EINMAL als Konflikt behandeln, nicht bei jedem neuen Stand
                done = list(self.s.get("ud_done") or [])
                if f"{key}:{ov[0]}" not in done:
                    self.s["ud_done"] = (done + [f"{key}:{ov[0]}"])[-50:]
        self.s["seq"] = max(int(self.s.get("seq") or 0), int(r.get("seq") or 0))
        self.s["last_pull"] = now
        self.last_taken = sorted(take)
        self.save()
        if take:
            self._say(f"Abgleich: {len(take)} Datei(en) vom {r.get('machine', 'anderen Rechner')} übernommen "
                      f"(Sicherung in {BACKUP_DIR}).")
        for c in conflicts:
            self._say("Abgleich: " + c)
        return True

    @staticmethod
    def _keep_open_merge(old: bytes, new: bytes) -> bytes:
        """Hatte die lokale AHSentinel.lua einen noch nicht eingelesenen AHSentinelMerge-Block und hat der neue Stand
        keinen, den Block an den neuen Stand hängen (er wurde nie hochgeladen und ginge sonst verloren)."""
        ob = top_blocks(old.decode("utf-8", errors="surrogateescape")).get(MERGE_VAR)
        text = new.decode("utf-8", errors="surrogateescape")
        if not ob or MERGE_VAR in top_blocks(text):
            return new
        if not text.endswith("\n"):
            text += "\n"
        return (text + f"{MERGE_VAR} = {ob}\n").encode("utf-8", errors="surrogateescape")

    def _safe_rel(self, rel: str) -> bool:
        parts = rel.split("/")
        if not rel.endswith(".lua") or ".." in parts or rel.startswith("/") or any(not p for p in parts):
            return False
        if "" not in self.roots:
            parts = parts[2:]                    # "<Spielversion>/<KONTO>/" davor
        return len(parts) == 2 and parts[0] == "SavedVariables" or len(parts) == 4 and parts[2] == "SavedVariables"

    # -- Hochladen
    def _wanted(self, key: str, files: dict[str, dict], entries: dict, now: float) -> bool:
        """S8 e: geändert -> ja; noch nie im Speicher -> einmal als Grundstand, ausser Retail ohne Spiel."""
        changed = any(self.s["files"].get(rel) != f["sha"] for rel, f in files.items())
        if key in entries:
            return changed
        if self._skip_root(key, files, now):
            if key not in self.skipped_logged:
                self.skipped_logged.add(key)
                self.log(f"Abgleich: {flavor_label(key)} seit {STALE_DAYS} Tagen nicht gespielt – nicht abgeglichen.")
            return False
        return True

    def push(self, now: float | None = None, running_ok: bool = False) -> bool:
        now = time.time() if now is None else now
        if not running_ok and self.is_wow_running():
            return False
        if not self.pull(now):
            return False
        scan = self._scan()
        entries = index_roots(self.remote)
        legacy = entries.get("*")
        groups: dict[str, dict] = {}
        for rel, f in scan.items():
            groups.setdefault(self.root_of(rel), {})[rel] = f
        keys = sorted(k for k, files in groups.items() if legacy or self._wanted(k, files, entries, now))
        carry: dict[str, dict] = {}
        if legacy:
            # Index von Uploader 2.1.x: einmal alles neu, Spielversionen anderer Rechner weitertragen
            try:
                manifest, files = read_package(b"".join(self.store.get_part(p) for p in legacy["parts"]))
            except (StoreError, ValueError, tarfile.TarError, OSError) as e:
                self.last_error = str(e)
                self.retry_at = now + 60
                self._say(f"Abgleich: neuester Stand nicht lesbar ({e}) – Hochladen später.")
                return False
            meta = manifest.get("files") or {}
            for rel, data in files.items():
                if self._safe_rel(rel) and self._path(rel) is None and "" not in self.roots:
                    m = meta.get(rel) or {}
                    carry.setdefault(self.root_of(rel), {})[rel] = {
                        "data": data, "mtime": float(m.get("mtime") or now), "machine": m.get("machine") or "?",
                        "off": float(m.get("off", manifest.get("off", 0.0)) or 0.0)}
        if not keys and not carry:
            return True
        off = self.clock_offset()
        seq = int((self.remote or {}).get("seq") or 0) + 1
        packs = {}
        changed_n = 0
        for key in keys:
            files = {}
            for rel, f in groups[key].items():
                data = self._clean(rel, read(f["path"]))
                files[rel] = {"data": data, "mtime": f["mtime"], "machine": self.me, "off": off}
                changed_n += self.s["files"].get(rel) != f["sha"]
            packs[key] = files
        for key, files in carry.items():
            packs[key] = files
        new_parts: dict[str, list[str]] = {}
        try:
            for key, files in sorted(packs.items()):
                blob = make_package(files, self.me, now, off)
                parts = []
                new_parts[key] = parts
                for i in range(0, len(blob), PART_BYTES):
                    n = i // PART_BYTES + 1
                    parts.append(self.store.put_part(f"stand-{seq}-{n}.bin", blob[i:i + PART_BYTES],
                                                     f"Stand {seq} · {flavor_label(key)} · {self.me} · "
                                                     f"{fmt_time(now)} · Teil {n}"))
            r_new = {} if legacy else {k: [e["rev"], e["parts"], e["machine"], e["time"]] for k, e in entries.items()}
            history = [] if legacy else [list(h) for h in (self.remote or {}).get("h") or [] if isinstance(h, list)]
            if legacy:
                history.append(list(legacy["parts"]))
                history += [list(p) for _, p in (self.remote or {}).get("history") or []
                            if isinstance(p, list) and p != legacy["parts"]]
            # UP-S1-2: Über einen defekten Stand eines anderen Rechners hinweg hochladen -> im Index vermerken ("ud"), bis
            # jener Rechner selbst wieder hochlädt (dann hat er den Konflikt beim Übernehmen schon aufgelöst)
            ud = {} if legacy else index_over_defect(self.remote)
            bad = set(self.s.get("defekt") or [])
            for key in new_parts:
                old = entries.get(key)
                if ud.get(key) and ud[key][1] == self.me:
                    ud.pop(key)
                if old and f"{key}:{old['rev']}" in bad and str(old.get("machine") or "") != self.me:
                    ud[key] = [int(old["rev"]), str(old.get("machine") or "")]
            for key, parts in new_parts.items():
                if key in r_new:
                    history.append(list(r_new[key][1]))
                r_new[key] = [seq, parts, self.me, round(now)]
            drop = history[:-(VERSIONS_KEEP - 1)] if len(history) > VERSIONS_KEEP - 1 else []
            history = history[len(drop):]
            index = {"v": 2, "seq": seq, "machine": self.me, "time": round(now), "off": round(off), "r": r_new,
                     "h": history}
            if ud:
                index["ud"] = ud
            while len(json.dumps(index, separators=(",", ":"))) > INDEX_MAX and index["h"]:
                drop.append(index["h"].pop(0))
            self.store.write_index(index)
        except StoreError as e:
            for parts in new_parts.values():
                for p in parts:
                    self.store.delete_part(p)
            self.last_error = str(e)
            self.retry_at = now + 60
            self._say(f"Abgleich: Hochladen nicht möglich ({e}) – neuer Versuch später.")
            return False
        self.s.setdefault("to_delete", [])
        for old in drop:
            self.s["to_delete"] += [str(p) for p in old]
        self.remote = index
        self.last_error = ""
        self.s["seq"] = seq
        if legacy:
            self.s["revs"].pop("*", None)
        for key in new_parts:
            self.s["revs"][key] = seq
        for key in keys:
            for rel, f in groups[key].items():
                self.s["files"][rel] = f["sha"]
        self.s["last_upload"] = now
        self.s["last_upload_machine"] = self.me
        self._note_blocked(now, uploaded=True)
        self.save()
        self.delete_old(limit=len(self.s.get("to_delete") or []))
        labels = ", ".join(sorted({flavor_label(k) for k in keys})) or "–"
        self._say(f"Abgleich: Stand {seq} hochgeladen ({labels}; {changed_n} geänderte Datei(en)).")
        return True

    # -- ältere Fassungen wirklich löschen (DU6): Nachricht samt Anhang; Fehlschläge später erneut
    def delete_old(self, limit: int = DELETE_PER_TICK) -> int:
        todo = list(self.s.get("to_delete") or [])
        if not todo:
            return 0
        if float(getattr(self.store, "wait_until", 0.0) or 0.0) > time.time():
            return 0
        done, left = 0, []
        for i, mid in enumerate(todo):
            if i >= max(1, limit):
                left += todo[i:]
                break
            ok = self.store.delete_part(mid)
            if ok is False:
                left.append(mid)
            else:
                done += 1
        self.s["to_delete"] = left[-500:]
        if done or left != todo:
            self.save()
        return done

    # -- S8 c: neuer WoW-Prozess -> neueren Stand noch vor dem Einloggen übernehmen
    def _try_takeover(self, now: float) -> bool:
        w = self.wow
        if not self.remote_newer():
            return True
        r = self.remote or {}
        who = self.pending_text()[4:] if self.pending_text().startswith("vom ") else "anderen Rechner"
        unsafe = (not w["transition"] or w["takeover_done"] or now - w["first_seen"] > TAKEOVER_MAX_AGE
                  or self._newest() > w["sv_newest"] + 1 or self.s.get("takeover_failed"))
        if unsafe:
            return self.pull(now)                    # nur melden: "WoW beenden, dann übernehmen"
        armed = bool(self.s.get("takeover_armed"))
        w["takeover_done"] = True
        if not armed:
            self.notify(f"Neuer Stand vom {who} – bitte noch nicht einloggen, wird übernommen …")
        self._say(f"Abgleich: neuer WoW-Start, neuerer Stand vom {who} – wird vor dem Einloggen übernommen.")
        ok = self.pull(now, takeover=True)
        if not ok:
            if not armed:
                self.notify("Übernahme nicht möglich – bitte WoW beenden, dann wird übernommen.")
            return False
        self.warned_seq = r.get("seq")
        # Beleg vorbereiten: Prüfblock in RaidMaster.lua jeder betroffenen Spielversion
        probe_files = []
        if not armed or self.s.get("proofs", 0) < PROOFS_NEEDED:
            for key in sorted({self.root_of(rel) for rel in self.last_taken}):
                rel = f"{key}/SavedVariables/{PROBE_FILE}" if key else f"SavedVariables/{PROBE_FILE}"
                path = self._path(rel)
                if path and os.path.isfile(path):
                    write_atomic(path, add_probe(read(path), int(r.get("seq") or 0), self.me, now))
                    probe_files.append(rel)
        if probe_files:
            self.s["probe"] = {"seq": int(r.get("seq") or 0), "t": now, "first_seen": w["first_seen"], "from": who,
                               "files": probe_files, "taken": list(self.last_taken),
                               "copy": self.s.get("takeover_copy")}
        self.save()
        if armed:
            self._say("Abgleich: übernommen – WoW liest ihn beim Einloggen.")
        else:
            self.notify("Fertig – du kannst einloggen.")
            self._say("Abgleich: fertig – du kannst einloggen.")
        return True

    def check_probe(self, now: float) -> None:
        """Nach dem nächsten Speichern: hat WoW den übernommenen Stand gelesen? (Messung und Beleg S8 c)"""
        p = self.s.get("probe")
        if not p:
            return
        seen, rewritten = None, False
        for rel in p.get("files") or []:
            path = self._path(rel)
            if not path or not os.path.isfile(path) or os.path.getmtime(path) <= float(p.get("t") or 0) + 1:
                continue
            data = read(path)
            if PROBE_VAR.encode() in data:
                continue                              # Prüfblock noch da: RaidMaster hat (noch) nicht gespeichert
            rewritten = True
            got = probe_seen(data)
            if got and got["seq"] == int(p.get("seq") or 0) and got["von"] == self.me:
                seen = got
                break
        if not rewritten:
            if now - float(p.get("t") or 0) > PROBE_MAX_AGE:
                self.s.pop("probe", None)
                self.save()
            return
        self.s.pop("probe", None)
        if seen:
            self.s["proofs"] = int(self.s.get("proofs") or 0) + 1
            secs = seen["geladen"] - float(p.get("first_seen") or 0) if seen["geladen"] else 0
            self._say(f"Abgleich – Messung: übernommener Stand {p.get('seq')} wurde beim Einloggen gelesen "
                      f"({int(secs)} s nach dem WoW-Start). Beleg {self.s['proofs']}/{PROOFS_NEEDED}.")
            if self.s["proofs"] >= PROOFS_NEEDED and not self.s.get("takeover_armed"):
                self.s["takeover_armed"] = True
                self._say("Abgleich: Übernahme vor dem Einloggen belegt – ab jetzt ohne Hinweis.")
        else:
            # WoW hatte den alten Stand schon gelesen: nie wieder bei laufendem WoW übernehmen
            self.s["takeover_failed"] = True
            self.s["takeover_armed"] = False
            text = ("Übernahme vor dem Einloggen kam zu spät (WoW hatte schon gelesen). Ab jetzt wird erst nach dem "
                    "Beenden von WoW übernommen.")
            self._say("Abgleich: " + text)
            self.notify(text)
            copy = p.get("copy")
            for rel in p.get("taken") or []:
                if rel.split("/")[-1] != MERGE_ADDON_FILE or not copy:
                    continue
                src = os.path.join(copy, *rel.split("/"))
                path = self._path(rel)
                if not path or not os.path.isfile(src) or not os.path.isfile(path):
                    continue
                merged = add_merge_block(read(path), read(src), str(p.get("from") or "Abgleich"), now)
                if merged is not None and not self.is_wow_running():
                    write_atomic(path, merged)
                    self._say("Abgleich: übernommener AHSentinel-Stand wird beim nächsten Login zusammengeführt.")
        self.save()

    # -- alte Sicherungen zusammenführen (offen 1 c; ab 2.3.0 auch der 2.1.0-Ort und JEDE Sicherung)
    def _old_backups(self) -> list[tuple[str, str, float]]:
        """(rel, Datei, Zeit) aller AHSentinel.lua in Sicherungen "vor-abgleich"/"uebernahme", neueste zuerst:
        im Uploader-Ordner (ab 2.1.1, rel mit "<Spielversion>/<KONTO>/") und in WTF/Account/<Konto>/_sync_backup
        (Uploader 2.1.0, rel ohne Spielversion -> dem Konto des Ordners zugeordnet)."""
        out = []
        # nur Sicherungen von 2.1.x/2.2.0 (vor dem ersten Lauf von 2.3.0) – spätere Konflikte führt der Abgleich selbst
        cutoff = float(self.s.setdefault("merge_cutoff", time.time()))
        places = [(self.backup_dir or os.path.join(self.acc, BACKUP_DIR), None)]
        for key, acc in self.roots.items():
            old = os.path.join(acc, BACKUP_DIR)
            if os.path.normpath(old) != os.path.normpath(places[0][0]):
                places.append((old, key))
        for root, key in places:
            for d in glob.glob(os.path.join(root, "*")):
                if not os.path.isdir(d) or not d.endswith(("-vor-abgleich", "-uebernahme")):
                    continue
                try:
                    made = time.mktime(time.strptime(os.path.basename(d)[:15], "%Y%m%d-%H%M%S"))
                except ValueError:
                    continue
                if made >= cutoff:
                    continue
                for fn in glob.glob(os.path.join(d, "**", MERGE_ADDON_FILE), recursive=True):
                    rel = os.path.relpath(fn, d).replace(os.sep, "/")
                    if key is not None and key != "" and not self._safe_rel(rel):
                        rel = f"{key}/{rel}"                       # 2.1.0: "SavedVariables/AHSentinel.lua"
                    if not self._safe_rel(rel) or self._path(rel) is None:
                        continue
                    out.append((rel, fn, made))                  # Zeit der Sicherung (aus dem Ordnernamen)
        return sorted(out, key=lambda x: -x[2])

    def merge_old_backups(self, now: float | None = None) -> int:
        """Jede gesicherte AHSentinel-Fassung, deren AHSentinelDB sich vom aktuellen Stand unterscheidet, wird
        AHSentinel zum Zusammenführen gegeben – je Login eine (es gibt nur einen offenen Block); die übrigen warten und
        werden beim nächsten Lauf angehängt, sobald AHSentinel den Block eingelesen hat. Gleiche Fassungen nur einmal."""
        now = time.time() if now is None else now
        if self.is_wow_running():
            return 0
        done = set(self.s.get("merged_backups") or [])
        n, waiting = 0, 0
        busy = set()
        for rel, fn, mt in self._old_backups():
            try:
                old = read(fn)
            except OSError:
                continue
            db = top_blocks(old.decode("utf-8", errors="surrogateescape")).get("AHSentinelDB")
            if not db:
                continue
            key = sha(db.encode("utf-8", errors="surrogateescape"))
            if key in done:
                continue
            path = self._path(rel)
            if not path or not os.path.isfile(path):
                continue
            cur = read(path)
            blocks = top_blocks(cur.decode("utf-8", errors="surrogateescape"))
            if blocks.get("AHSentinelDB") == db:
                done.add(key)                                   # schon derselbe Stand
                continue
            if rel in busy or MERGE_VAR in blocks:
                waiting += 1                                    # nächster Login
                continue
            merged = add_merge_block(cur, old, "Sicherung", mt)
            if merged is None:
                continue
            self._backup({rel: cur}, now, "zusammenfuehren")
            write_atomic(path, merged)
            done.add(key)
            busy.add(rel)
            n += 1
            self._say(f"Abgleich: gesicherter AHSentinel-Stand vom {fmt_time(mt)} wird beim nächsten Login "
                      "zusammengeführt.")
        if waiting:
            self._say(f"Abgleich: {waiting} weitere gesicherte AHSentinel-Stände folgen nach dem nächsten Login.")
        self.s["merged_backups"] = sorted(done)[-500:]
        self.save()
        return n

    # -- regelmässig (aus der Hauptschleife, alle 5 s)
    def tick(self, now: float | None = None):
        now = time.time() if now is None else now
        running = self.is_wow_running()
        w = self.wow
        if running:
            if not w["running"]:
                # WoW ist (neu) da. Übergang nur, wenn kurz vorher sicher keins lief (sonst unbekannt).
                w["transition"] = w["running"] is False and now - w["last_off"] <= TRANSITION_MAX_GAP
                w["first_seen"], w["running"], w["takeover_done"] = now, True, False
                w["sv_newest"] = self._newest()
                if w["transition"]:
                    if self.check_remote(now, force=True, every=CHECK_REMOTE_RUNNING) is not None:
                        self._try_takeover(now)
            else:
                self.check_remote(now, every=CHECK_REMOTE_RUNNING)
                if self.remote_newer() and now >= self.retry_at:
                    self._try_takeover(now)
            if self.remote_newer() or now < self.retry_at:
                self._note_blocked(now)
                return                                  # erst nach WoW-Ende übernehmen, dann hochladen
            changed, newest = self.local_changes(now)
            if (changed and now - newest >= QUIET_RUNNING_SECONDS
                    and now - float(self.s.get("last_upload") or 0) >= PUSH_GAP_RUNNING):
                self.push(now, running_ok=True)         # /reload, Ausloggen: nur lesen (S8 a, ab 2.3.0 je /reload)
            return
        if w["running"]:
            self.merge_old_backups(now)             # nach dem Spielen: nächste wartende Sicherung anhängen
        w["running"], w["last_off"], w["transition"] = False, now, False
        self.check_probe(now)
        self.check_remote(now)
        if now < self.retry_at:
            self._note_blocked(now)
            return
        if self.remote_newer():
            self.pull(now)
        changed, newest = self.local_changes(now)
        if changed and now - newest >= QUIET_SECONDS and not self.remote_newer():
            self.push(now)
        if changed and self.remote_newer():
            self._note_blocked(now)
        elif self.s.get("to_delete"):
            self.delete_old()


def check_state(st: dict) -> list[str]:
    """TU5 (ab 2.3.3): Grundregeln des gespeicherten Abgleich-Zustands (uploader_state.json) – nur lesen.
    Liefert die Verletzungen als Text OHNE Namen (Konto-/Rechnernamen werden nie genannt)."""
    out = []
    s = (st or {}).get("sync") or {}
    if not isinstance(s, dict):
        return ["sync ist keine Tabelle"]
    try:
        seq = int(s.get("seq") or 0)
    except (TypeError, ValueError):
        return ["seq ist keine Zahl"]
    if seq < 0:
        out.append(f"seq negativ ({seq})")
    for i, (k, v) in enumerate(sorted((s.get("revs") or {}).items())):
        if not isinstance(v, int) or v < 0:
            out.append(f"rev Nr. {i + 1} ungültig")
        elif v > seq:
            out.append(f"rev Nr. {i + 1} ({v}) grösser als seq ({seq})")
    bad = sum(1 for v in (s.get("files") or {}).values() if not re.fullmatch(r"[0-9a-f]{40}", str(v or "")))
    if bad:
        out.append(f"{bad} Prüfwert(e) der Basis ungültig")
    td = s.get("to_delete") or []
    if not isinstance(td, list) or any(not re.fullmatch(r"\d{1,25}", str(m)) for m in td):
        out.append("to_delete enthält ungültige Einträge")
    if len(td) > 500:
        out.append(f"to_delete zu lang ({len(td)})")
    return out


def notify_windows(text: str):
    """Windows-Hinweis (nicht blockierend). Anderswo nur Text."""
    if sys.platform != "win32":
        return
    import threading

    def show():
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, text, "GoldSentinel-Abgleich", 0x40 | 0x1000 | 0x10000)
        except Exception:  # noqa: BLE001
            pass
    threading.Thread(target=show, daemon=True).start()


def find_wow_exe(acc: str) -> str | None:
    """…/<WoW-Ordner>/WTF/Account/<KONTO> -> …/<WoW-Ordner>/Wow*.exe"""
    root = os.path.dirname(os.path.dirname(os.path.dirname(acc)))
    for pat in ("Wow.exe", "WowClassic.exe", "Wow*.exe"):
        hits = sorted(glob.glob(os.path.join(root, pat)))
        if hits:
            return hits[0]
    return None
