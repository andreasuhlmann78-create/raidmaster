"""
RaidMaster-Uploader – läuft auf dem PC, auf dem WoW gespielt wird.

Sobald WoW die Datei RaidMaster.lua speichert (nach /reload oder beim Ausloggen), wird sie gepackt
und über einen geheimen Discord-Webhook in den Kanal #bot-daten geschickt. Der Bot auf dem Server
liest sie dort und aktualisiert DKP, Loot, Einteilung und Skillungen.

Start: uploader.bat (Doppelklick). Einrichtung: in Discord /uploader ausführen und die Datei
uploader_config.json in diesen Ordner legen. Nur Python 3 nötig, keine weiteren Pakete.

GuildSentinel (ab 1.7.0): Liegt neben RaidMaster.lua auch GuildSentinel.lua (Gildentool: Wunschliste, Spenden,
Bankbestand, Gildenverlauf), geht sie mit. Eine Änderung an einer der beiden Dateien löst den Upload aus.

Erstkill-Screenshots (ab 1.6.0): RaidMaster macht beim Erstkill einen Screenshot und merkt sich die Zeit
(RaidMasterDB.shotList). Der Uploader sucht im Screenshots-Ordner von WoW das passende Bild und schickt es
beim nächsten Upload mit. Andere Screenshots werden nie hochgeladen.
"""

from __future__ import annotations

import glob
import gzip
import json
import os
import re
import socket
import string
import sys
import time
import urllib.error
import urllib.request
import uuid

VERSION = "1.7.0"
EXTRA_FILES = ("GuildSentinel.lua",)   # weitere SavedVariables im selben Ordner, die mitgehen
SHOT_WINDOW = (-30, 180)          # Bild darf so viele Sekunden vor/nach der gemerkten Zeit entstanden sein
SHOT_MAX_BYTES = 9 * 1024 * 1024
SHOT_MAX_AGE = 14 * 86400
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "uploader_config.json")
USER_AGENT = f"RaidMasterUploader (https://github.com, {VERSION})"


def log(msg: str):
    print(time.strftime("%H:%M:%S") + "  " + msg, flush=True)


def load_config() -> dict:
    if not os.path.isfile(CONFIG):
        log("uploader_config.json fehlt. In Discord /uploader ausführen und die Datei in diesen Ordner legen:")
        log("  " + HERE)
        input("Enter zum Beenden ...")
        sys.exit(1)
    with open(CONFIG, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if not cfg.get("webhook_url", "").startswith("https://"):
        log("In uploader_config.json fehlt der Webhook-Link – /uploader in Discord erneut ausführen.")
        input("Enter zum Beenden ...")
        sys.exit(1)
    return cfg


def save_config(cfg: dict):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def find_saved_variables() -> list[str]:
    """Sucht RaidMaster.lua in typischen WoW-Ordnern auf allen Laufwerken."""
    pattern_tail = os.path.join("WTF", "Account", "*", "SavedVariables", "RaidMaster.lua")
    roots = []
    if os.name == "nt":
        roots = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    else:
        roots = [os.path.expanduser("~")]
    found = set()
    for root in roots:
        for depth in range(0, 4):
            middle = [root] + ["*"] * depth
            for path in glob.glob(os.path.join(*middle, pattern_tail)):
                found.add(os.path.normpath(path))
    return sorted(found, key=lambda p: os.path.getmtime(p), reverse=True)


def choose_path(cfg: dict) -> str:
    path = cfg.get("savedvariables_path") or ""
    if path and os.path.isfile(path):
        return path
    log("Suche die RaidMaster-Datei von WoW ... (kann eine Minute dauern)")
    found = find_saved_variables()
    if not found:
        log("Nicht gefunden. Bitte in uploader_config.json bei \"savedvariables_path\" den Pfad eintragen, z. B.")
        log('  "C:/Games/WoW Forever/WTF/Account/ANDI/SavedVariables/RaidMaster.lua"')
        log("Die Datei entsteht erst, wenn RaidMaster installiert ist und du einmal eingeloggt warst.")
        input("Enter zum Beenden ...")
        sys.exit(1)
    if len(found) > 1:
        log("Mehrere gefunden – nehme die zuletzt geänderte:")
        for p in found:
            log("  " + p)
    path = found[0].replace("\\", "/")
    cfg["savedvariables_path"] = path
    save_config(cfg)
    return path


def screenshots_dir(path: str) -> str:
    """.../<WoW>/WTF/Account/<X>/SavedVariables/RaidMaster.lua -> .../<WoW>/Screenshots"""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(path))))))
    return os.path.join(root, "Screenshots")


def find_shots(cfg: dict, path: str, raw: bytes) -> list[tuple[str, str]]:
    """Erstkill-Screenshots, die noch nicht geschickt wurden: [(Dateipfad, Name im Upload)]."""
    m = re.search(rb'\["shotList"\]\s*=\s*"([0-9:;]*)"', raw)
    if not m:
        return []
    folder = cfg.get("screenshots_path") or screenshots_dir(path)
    if not os.path.isdir(folder):
        return []
    files = []
    for fn in os.listdir(folder):
        if fn.lower().endswith((".jpg", ".jpeg", ".png")):
            full = os.path.join(folder, fn)
            try:
                files.append((os.path.getmtime(full), full))
            except OSError:
                pass
    sent = set(cfg.get("sent_shots") or [])
    out = []
    now = time.time()
    for part in m.group(1).decode().split(";"):
        t, _, enc = part.partition(":")
        if not t.isdigit() or part in sent or now - int(t) > SHOT_MAX_AGE:
            continue
        t = int(t)
        cands = [(abs(mt - t), full) for mt, full in files if SHOT_WINDOW[0] <= mt - t <= SHOT_WINDOW[1]]
        if not cands:
            continue
        full = min(cands)[1]
        if os.path.getsize(full) > SHOT_MAX_BYTES:
            continue
        ext = os.path.splitext(full)[1].lower()
        out.append((full, f"shot_{enc}_{t}{ext}", part))
    return out


def extra_paths(path: str) -> list[str]:
    """Weitere Dateien aus demselben SavedVariables-Ordner (z. B. GuildSentinel.lua), sofern vorhanden."""
    folder = os.path.dirname(os.path.abspath(path))
    return [p for p in (os.path.join(folder, n) for n in EXTRA_FILES) if os.path.isfile(p)]


def watch_stamp(path: str) -> tuple:
    """Änderungszeiten aller überwachten Dateien (RaidMaster.lua zuerst)."""
    out = []
    for p in [path] + extra_paths(path):
        try:
            out.append((p, os.path.getmtime(p)))
        except OSError:
            out.append((p, 0))
    return tuple(out)


def upload(cfg: dict, path: str) -> bool:
    with open(path, "rb") as f:
        raw = f.read()
    packed = gzip.compress(raw, 9)
    extras = []
    for p in extra_paths(path):
        try:
            with open(p, "rb") as f:
                extras.append((os.path.basename(p) + ".gz", gzip.compress(f.read(), 9)))
        except OSError:
            pass
    shots = []
    try:
        # Discord nimmt pro Nachricht nur ca. 10 MB an: Bilder nur, solange alles zusammen darunter bleibt
        total = len(packed) + sum(len(b) for _, b in extras)
        for shot in find_shots(cfg, path, raw):
            size = os.path.getsize(shot[0])
            if total + size <= SHOT_MAX_BYTES:
                shots.append(shot)
                total += size
    except OSError:
        shots = []
    bot_id = str(cfg.get("bot_id") or "")
    payload = {
        "content": (f"<@{bot_id}> " if bot_id else "") + "RaidMaster-Daten",
        "username": f"RaidMaster-Uploader ({socket.gethostname()[:20]})",
        "allowed_mentions": {"parse": [], "users": [bot_id] if bot_id else []},
    }
    boundary = "----RaidMaster" + uuid.uuid4().hex
    parts = [
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="payload_json"\r\nContent-Type: application/json\r\n\r\n',
        json.dumps(payload).encode("utf-8"), b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="files[0]"; filename="RaidMaster.lua.gz"\r\n'
        b"Content-Type: application/gzip\r\n\r\n",
        packed, b"\r\n",
    ]
    for i, (name, data) in enumerate(extras, 1):
        parts += [f"--{boundary}\r\n".encode(),
                  f'Content-Disposition: form-data; name="files[{i}]"; filename="{name}"\r\nContent-Type: application/gzip\r\n\r\n'.encode(),
                  data, b"\r\n"]
    for i, (full, name, _) in enumerate(shots, 1 + len(extras)):
        with open(full, "rb") as f:
            img = f.read()
        ctype = "image/png" if name.endswith(".png") else "image/jpeg"
        parts += [f"--{boundary}\r\n".encode(),
                  f'Content-Disposition: form-data; name="files[{i}]"; filename="{name}"\r\nContent-Type: {ctype}\r\n\r\n'.encode(),
                  img, b"\r\n"]
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    url = cfg["webhook_url"] + ("&" if "?" in cfg["webhook_url"] else "?") + "wait=true"
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                r.read()
            log(f"Hochgeladen ({len(raw) // 1024} KB, gepackt {len(packed) // 1024} KB)."
                + (" Dazu " + ", ".join(n[:-3] for n, _ in extras) + "." if extras else "")
                + (f" Dazu {len(shots)} Erstkill-Screenshot(s)." if shots else ""))
            if shots:
                cfg["sent_shots"] = (list(cfg.get("sent_shots") or []) + [p for _, _, p in shots])[-200:]
                save_config(cfg)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 429:
                try:
                    wait = float(json.loads(e.read().decode()).get("retry_after", 5))
                except ValueError:
                    wait = 5
                time.sleep(min(wait, 60) + 0.5)
                continue
            if e.code in (401, 404):
                log("Der Webhook-Link ist ungültig (gelöscht?). In Discord /uploader erneut ausführen.")
                return False
            log(f"Discord antwortet mit Fehler {e.code}.")
            return False
        except (urllib.error.URLError, OSError) as e:
            log(f"Keine Verbindung ({e}). Neuer Versuch später.")
            return False
    return False


def main():
    log(f"RaidMaster-Uploader {VERSION}")
    cfg = load_config()
    path = choose_path(cfg)
    log("Überwache: " + path)
    for p in extra_paths(path):
        log("Und: " + p)
    log("Fenster offen lassen. Nach /reload oder Ausloggen werden die Daten automatisch hochgeladen.")
    interval = max(3, int(cfg.get("check_seconds") or 10))
    last_sent: tuple = ()
    failures = 0
    next_try = 0.0
    while True:
        stamp = watch_stamp(path)
        if stamp[0][1] and stamp != last_sent and time.time() >= next_try:
            # warten, bis WoW fertig geschrieben hat
            time.sleep(2)
            if watch_stamp(path) != stamp:
                continue
            if upload(cfg, path):
                last_sent = stamp
                failures = 0
            else:
                failures += 1
                next_try = time.time() + min(600, 30 * failures)
        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
