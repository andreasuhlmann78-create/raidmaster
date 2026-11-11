"""Abgleich der Addon-Daten zwischen zwei Rechnern (PC und Laptop) – ab Uploader 2.1.0.

Auftrag: auftraege/RaidMaster/anweisung-uploader-sync-rechner.txt (Entscheid des Nutzers 11.11.2026, Lösung 2).

Speicher (S1): ein PRIVATER Discord-Kanal #sync-daten, den nur du und der Bot sehen. Der Bot legt ihn bei /uploader an,
dazu einen Webhook und eine "Index"-Nachricht; beides steht in sync_config.json (neben dem Uploader, geheim wie
uploader_config.json). Der Uploader schickt den Stand als Anhang über den Webhook und trägt im Index ein, welche
Nachricht der neueste Stand ist. Ein Webhook darf seine eigenen Nachrichten lesen, ändern und löschen – darum braucht der
Uploader keinen Bot-Token und der Bot liest #sync-daten nie. Höchstens 10 Fassungen bleiben, ältere löscht der Uploader.
Übertragung nur über HTTPS; die Daten liegen nur in diesem privaten Kanal, nie im Repo, nie in #testberichte.

Was (S2): alle *.lua in WTF/Account/<KONTO>/SavedVariables und WTF/Account/<KONTO>/<Realm>/<Charakter>/SavedVariables
(nicht *.lua.bak, nicht Config.wtf, Makros oder Tastenbelegungen).

Ablauf (S3): WoW darf beim Schreiben NIE laufen.
  - Hochladen: WoW beendet und 2 Minuten Ruhe nach dem letzten Speichern -> geänderte Daten als ein Paket (tar.gz mit
    manifest.json: je Datei Prüfwert, Zeit, Rechner).
  - Herunterladen: vor dem Start von WoW (GoldSentinel-WoW.bat), beim Start des Uploaders und nach dem Beenden von WoW,
    wenn der andere Rechner einen neueren Stand hat. Vorher Sicherung der lokalen Dateien in _sync_backup/<Zeit>
    (höchstens 5).
  - Läuft WoW und es gibt einen neueren Stand: nichts überschreiben, nur melden.
Konflikte (S4): an beiden Rechnern geändert -> je Datei gewinnt die neuere; die andere bleibt in _sync_backup und wird
  gemeldet. AHSentinel.lua: die ältere Fassung zusätzlich als eigener Block "AHSentinelMerge = {...}" in die Datei
  (AHSentinel liest ihn beim nächsten Login und führt zusammen; AHSentinelDB selbst wird nie verändert).

Alles Netz und alle Prozessabfragen laufen über austauschbare Funktionen (Store, wow_running) – offline testbar.
"""
from __future__ import annotations

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
BACKUPS_KEEP = 5
VERSIONS_KEEP = 10
QUIET_SECONDS = 120            # nach dem letzten Speichern so lange warten
CHECK_REMOTE_SECONDS = 300     # so oft nachsehen, ob der andere Rechner Neues hat
PART_BYTES = 9 * 1024 * 1024   # Discord: höchstens 10 MB je Anhang
MERGE_VAR = "AHSentinelMerge"
MERGE_ADDON_FILE = "AHSentinel.lua"
INDEX_MARK = "GSSYNC-INDEX"


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
# Dateien
# ---------------------------------------------------------------------------
def account_dir(sv_lua_path: str) -> str:
    """…/WTF/Account/<KONTO>/SavedVariables/RaidMaster.lua -> …/WTF/Account/<KONTO>"""
    return os.path.dirname(os.path.dirname(os.path.abspath(sv_lua_path)))


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


def make_package(files: dict[str, dict], machine: str, now: float) -> bytes:
    """files: rel -> {"data": bytes, "mtime": float, "machine": str}. tar.gz mit manifest.json."""
    manifest = {"v": 1, "machine": machine, "time": now,
                "files": {rel: {"sha": sha(f["data"]), "mtime": f["mtime"], "machine": f.get("machine") or machine,
                                "size": len(f["data"])} for rel, f in files.items()}}
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
# AHSentinel: ältere Fassung als eigener Block anhängen (nie in AHSentinelDB hinein)
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


def lua_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def add_merge_block(winner: bytes, older: bytes, machine: str, when: float) -> bytes | None:
    """AHSentinelMerge = { v, von, zeit, grund, db = <ältere AHSentinelDB> } an die Gewinner-Datei hängen.
    None, wenn die ältere keine AHSentinelDB hat oder die Gewinner-Datei schon einen offenen Block hat."""
    old = top_blocks(older.decode("utf-8", errors="surrogateescape"))
    db = old.get("AHSentinelDB")
    text = winner.decode("utf-8", errors="surrogateescape")
    if not db or MERGE_VAR in top_blocks(text):
        return None
    block = (f"{MERGE_VAR} = {{\n\t[\"v\"] = 1,\n\t[\"von\"] = {lua_quote(machine)},\n\t[\"zeit\"] = {int(when)},\n"
             f"\t[\"grund\"] = \"konflikt\",\n\t[\"db\"] = {db},\n}}\n")
    if not text.endswith("\n"):
        text += "\n"
    return (text + block).encode("utf-8", errors="surrogateescape")


# ---------------------------------------------------------------------------
# Speicher: Webhook in #sync-daten
# ---------------------------------------------------------------------------
class StoreError(Exception):
    pass


class WebhookStore:
    """Eine Index-Nachricht (Inhalt JSON) + je Fassung eine oder mehrere Nachrichten mit Anhang."""

    def __init__(self, webhook_url: str, index_id: str, timeout: int = 60):
        self.url = webhook_url.rstrip("/")
        self.index_id = str(index_id)
        self.timeout = timeout

    def _req(self, method: str, path: str = "", data: bytes | None = None, ctype: str | None = None, query: str = ""):
        url = self.url + path + query
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("User-Agent", "GoldSentinel-Uploader")
        if ctype:
            req.add_header("Content-Type", ctype)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
                return json.loads(body.decode("utf-8")) if body else None
        except urllib.error.HTTPError as e:
            raise StoreError(f"Discord antwortet {e.code}") from None
        except (urllib.error.URLError, OSError, ValueError) as e:
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
        msg = self._req("GET", f"/messages/{msg_id}")
        att = ((msg or {}).get("attachments") or [None])[0]
        if not att or not att.get("url"):
            raise StoreError("Paket nicht mehr vorhanden")
        req = urllib.request.Request(att["url"], headers={"User-Agent": "GoldSentinel-Uploader"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, OSError) as e:
            raise StoreError("Paket konnte nicht geladen werden") from None

    def delete_part(self, msg_id: str):
        try:
            self._req("DELETE", f"/messages/{msg_id}")
        except StoreError:
            pass


def load_sync_config(here: str) -> dict | None:
    try:
        with open(os.path.join(here, SYNC_CONFIG), "r", encoding="utf-8") as f:
            conf = json.load(f)
    except (OSError, ValueError):
        return None
    if not str(conf.get("sync_webhook_url") or "").startswith("https://") or not conf.get("sync_index_id"):
        return None
    return conf


# ---------------------------------------------------------------------------
# Abgleich
# ---------------------------------------------------------------------------
class Sync:
    """Hält den Stand dieses Rechners in st["sync"] (uploader_state.json):
    seq (zuletzt übernommene Fassung), files {rel: sha} (Stand nach dem letzten Abgleich), Anzeige-Daten."""

    def __init__(self, store, acc: str, st: dict, save, machine: str, log, is_wow_running=wow_running,
                 notify=None):
        self.store, self.acc, self.st, self.save, self.me = store, acc, st, save, machine
        self.log, self.is_wow_running = log, is_wow_running
        self.notify = notify or (lambda text: None)
        s = st.setdefault("sync", {})
        s.setdefault("seq", 0)
        s.setdefault("files", {})
        self.s = s
        self.next_remote = 0.0
        self.remote: dict | None = None       # zuletzt gelesener Index
        self.warned_seq = 0
        self.last_error = ""
        self.messages: list[str] = []

    # -- Anzeige (S5)
    def status_line(self) -> str:
        r = self.remote or {}
        up = self.s.get("last_upload")
        newest = f"{r.get('machine', '?')} {fmt_time(r.get('time'))}" if r.get("seq") else "–"
        here = "aktuell" if not r.get("seq") or int(r.get("seq") or 0) <= int(self.s.get("seq") or 0) else "NICHT aktuell"
        line = (f"Abgleich: zuletzt hochgeladen {fmt_time(up)} ({self.s.get('last_upload_machine') or self.me})"
                if up else "Abgleich: noch nichts hochgeladen")
        line += f" · neuester Stand: {newest} · dieser Rechner {here}"
        if self.last_error:
            line += f" · FEHLER: {self.last_error}"
        return line

    def _say(self, text: str):
        self.messages.append(text)
        self.log(text)

    # -- Dateien
    def _local(self) -> dict[str, dict]:
        out = {}
        for rel, fn in local_files(self.acc).items():
            try:
                data = read(fn)
                out[rel] = {"data": data, "mtime": os.path.getmtime(fn), "path": fn}
            except OSError:
                continue
        return out

    def local_changes(self) -> tuple[list[str], float]:
        """(geänderte Dateien gegenüber dem letzten Abgleich, jüngste Änderungszeit)"""
        changed, newest = [], 0.0
        for rel, f in self._local().items():
            newest = max(newest, f["mtime"])
            if self.s["files"].get(rel) != sha(f["data"]):
                changed.append(rel)
        return sorted(changed), newest

    def _backup(self, files: dict[str, bytes], now: float, tag: str) -> str:
        root = os.path.join(self.acc, BACKUP_DIR)
        dest = os.path.join(root, time.strftime("%Y%m%d-%H%M%S", time.localtime(now)) + "-" + tag)
        for rel, data in files.items():
            write_atomic(os.path.join(dest, *rel.split("/")), data)
        dirs = sorted(d for d in glob.glob(os.path.join(root, "*")) if os.path.isdir(d))
        for old in dirs[:-BACKUPS_KEEP]:
            shutil.rmtree(old, ignore_errors=True)
        return dest

    # -- Index
    def check_remote(self, now: float | None = None, force: bool = False) -> dict | None:
        now = time.time() if now is None else now
        if not force and now < self.next_remote:
            return self.remote
        self.next_remote = now + CHECK_REMOTE_SECONDS
        try:
            self.remote = self.store.read_index()
            self.last_error = ""
        except StoreError as e:
            self.last_error = str(e)
            self._say(f"Abgleich: {e} – lokale Dateien bleiben unverändert, neuer Versuch später.")
            return None
        return self.remote

    def remote_newer(self) -> bool:
        r = self.remote or {}
        return int(r.get("seq") or 0) > int(self.s.get("seq") or 0)

    # -- Herunterladen
    def pull(self, now: float | None = None) -> bool:
        """Neueren Stand übernehmen (nur wenn WoW nicht läuft). True = nichts mehr offen."""
        now = time.time() if now is None else now
        if self.check_remote(now, force=True) is None:
            return False
        if not self.remote_newer():
            return True
        r = self.remote
        if self.is_wow_running():
            if self.warned_seq != r.get("seq"):
                self.warned_seq = r.get("seq")
                text = f"Neuerer Stand vom {r.get('machine', 'anderen Rechner')} – WoW beenden, dann übernehmen."
                self._say("Abgleich: " + text)
                self.notify(text)
            return False
        try:
            blob = b"".join(self.store.get_part(p) for p in r.get("parts") or [])
            manifest, remote_files = read_package(blob)
        except (StoreError, ValueError, tarfile.TarError, OSError) as e:
            self.last_error = str(e)
            self._say(f"Abgleich: neuer Stand nicht lesbar ({e}) – lokale Dateien unverändert.")
            return False
        local = self._local()
        meta = manifest.get("files") or {}
        take, backup, conflicts = {}, {}, []
        for rel, data in remote_files.items():
            if not self._safe_rel(rel):
                continue
            rsha = sha(data)
            base = self.s["files"].get(rel)
            cur = local.get(rel)
            if cur is None:
                take[rel] = data
                continue
            lsha = sha(cur["data"])
            if lsha == rsha:
                continue
            if lsha == base or base is None and cur["mtime"] <= float((meta.get(rel) or {}).get("mtime") or 0):
                take[rel] = data                           # hier nicht geändert -> neueren Stand übernehmen
                backup[rel] = cur["data"]
                continue
            if rsha == base:
                continue                                    # nur hier geändert -> bleibt, wird hochgeladen
            # an beiden Rechnern geändert (S4): neuere gewinnt, ältere gesichert
            rmt = float((meta.get(rel) or {}).get("mtime") or 0)
            rmach = (meta.get(rel) or {}).get("machine") or r.get("machine") or "anderer Rechner"
            if rmt > cur["mtime"]:
                winner, older, wname, oname = data, cur["data"], rmach, self.me
                take[rel] = data
            else:
                winner, older, wname, oname = cur["data"], data, self.me, rmach
            backup[rel + (".lokal" if winner is data else f".{rmach}")] = older
            if rel.split("/")[-1] == MERGE_ADDON_FILE:
                merged = add_merge_block(winner, older, oname, now)
                if merged is not None:
                    take[rel] = merged
            conflicts.append(f"{rel.split('/')[-1]}: {oname} {fmt_time(cur['mtime'] if older is cur['data'] else rmt)}"
                             f" und {wname} {fmt_time(rmt if winner is data else cur['mtime'])} beide geändert – "
                             f"{wname}-Stand übernommen, {oname}-Stand gesichert"
                             + (" (AHSentinel führt ihn beim nächsten Login zusammen)"
                                if rel.split("/")[-1] == MERGE_ADDON_FILE else ""))
        if self.is_wow_running():                           # nochmals: WoW darf beim Schreiben nie laufen
            return False
        if backup or take:
            to_save = dict(backup)
            for rel in take:
                if rel in local and rel not in to_save:
                    to_save[rel] = local[rel]["data"]
            if to_save:
                self._backup(to_save, now, "vor-abgleich")
        for rel, data in take.items():
            mt = float((meta.get(rel) or {}).get("mtime") or now)
            write_atomic(os.path.join(self.acc, *rel.split("/")), data, None if rel in backup else mt)
        # Stand nach dem Abgleich: was jetzt lokal liegt
        new = {rel: sha(f["data"]) for rel, f in self._local().items()}
        for rel, data in remote_files.items():
            if self._safe_rel(rel) and new.get(rel) != sha(data):
                # lokal anders als der andere Rechner (nur hier geändert, Gewinner oder mit AHSentinelMerge):
                # Basis = Stand des anderen Rechners, damit es beim nächsten Hochladen mitgeht
                new[rel] = sha(data)
        self.s["files"] = new
        self.s["seq"] = int(r.get("seq") or 0)
        self.s["last_pull"] = now
        self.save()
        if take:
            self._say(f"Abgleich: {len(take)} Datei(en) vom {r.get('machine', 'anderen Rechner')} übernommen "
                      f"(Sicherung in {BACKUP_DIR}).")
        for c in conflicts:
            self._say("Abgleich: " + c)
        return True

    @staticmethod
    def _safe_rel(rel: str) -> bool:
        parts = rel.split("/")
        return (rel.endswith(".lua") and ".." not in parts and not rel.startswith("/") and
                (len(parts) == 2 and parts[0] == "SavedVariables" or len(parts) == 4 and parts[3 - 1] == "SavedVariables"))

    # -- Hochladen
    def push(self, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        if self.is_wow_running():
            return False
        if not self.pull(now):
            return False
        changed, _ = self.local_changes()
        if not changed and self.s.get("seq"):
            return True
        local = self._local()
        files = {rel: {"data": f["data"], "mtime": f["mtime"], "machine": self.me} for rel, f in local.items()}
        blob = make_package(files, self.me, now)
        seq = int((self.remote or {}).get("seq") or 0) + 1
        parts = []
        try:
            for i in range(0, len(blob), PART_BYTES):
                n = i // PART_BYTES + 1
                parts.append(self.store.put_part(f"stand-{seq}-{n}.bin", blob[i:i + PART_BYTES],
                                                 f"Stand {seq} · {self.me} · {fmt_time(now)} · Teil {n}"))
            history = list((self.remote or {}).get("history") or [])
            history.append([seq, parts])
            drop, history = history[:-VERSIONS_KEEP], history[-VERSIONS_KEEP:]
            index = {"v": 1, "seq": seq, "machine": self.me, "time": now, "parts": parts, "history": history}
            self.store.write_index(index)
        except StoreError as e:
            for p in parts:
                self.store.delete_part(p)
            self.last_error = str(e)
            self._say(f"Abgleich: Hochladen nicht möglich ({e}) – neuer Versuch später.")
            return False
        for _, old in drop:
            for p in old:
                self.store.delete_part(p)
        self.remote = index
        self.last_error = ""
        self.s["seq"] = seq
        self.s["files"] = {rel: sha(f["data"]) for rel, f in local.items()}
        self.s["last_upload"] = now
        self.s["last_upload_machine"] = self.me
        self.save()
        self._say(f"Abgleich: Stand {seq} hochgeladen ({len(changed)} geänderte Datei(en), {len(files)} insgesamt).")
        return True

    # -- regelmässig (aus der Hauptschleife)
    def tick(self, now: float | None = None):
        now = time.time() if now is None else now
        running = self.is_wow_running()
        self.check_remote(now)
        if running:
            if self.remote_newer():
                self.pull(now)                       # meldet nur, schreibt nichts
            self.s["wow_seen"] = now
            return
        if self.remote_newer():
            self.pull(now)
        changed, newest = self.local_changes()
        if changed and now - newest >= QUIET_SECONDS:
            self.push(now)


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
