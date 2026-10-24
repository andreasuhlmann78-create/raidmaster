"""
RaidMaster-Uploader – läuft auf dem PC, auf dem WoW gespielt wird.

Sobald WoW die Datei RaidMaster.lua speichert (nach /reload oder beim Ausloggen), wird sie gepackt
und über einen geheimen Discord-Webhook in den Kanal #bot-daten geschickt. Der Bot auf dem Server
liest sie dort und aktualisiert DKP, Loot, Einteilung und Skillungen.

Start: uploader.bat (Doppelklick). Einrichtung: in Discord /uploader ausführen und die Datei
uploader_config.json in diesen Ordner legen. Nur Python 3 nötig, keine weiteren Pakete.
"""

from __future__ import annotations

import glob
import gzip
import json
import os
import socket
import string
import sys
import time
import urllib.error
import urllib.request
import uuid

VERSION = "1.5.0"
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


def upload(cfg: dict, path: str) -> bool:
    with open(path, "rb") as f:
        raw = f.read()
    packed = gzip.compress(raw, 9)
    bot_id = str(cfg.get("bot_id") or "")
    payload = {
        "content": (f"<@{bot_id}> " if bot_id else "") + "RaidMaster-Daten",
        "username": f"RaidMaster-Uploader ({socket.gethostname()[:20]})",
        "allowed_mentions": {"parse": [], "users": [bot_id] if bot_id else []},
    }
    boundary = "----RaidMaster" + uuid.uuid4().hex
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="payload_json"\r\nContent-Type: application/json\r\n\r\n',
        json.dumps(payload).encode("utf-8"), b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="files[0]"; filename="RaidMaster.lua.gz"\r\n'
        b"Content-Type: application/gzip\r\n\r\n",
        packed, b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])
    url = cfg["webhook_url"] + ("&" if "?" in cfg["webhook_url"] else "?") + "wait=true"
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                r.read()
            log(f"Hochgeladen ({len(raw) // 1024} KB, gepackt {len(packed) // 1024} KB).")
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
    log("Fenster offen lassen. Nach /reload oder Ausloggen werden die Daten automatisch hochgeladen.")
    interval = max(3, int(cfg.get("check_seconds") or 10))
    last_sent = 0.0
    failures = 0
    next_try = 0.0
    while True:
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0
        if mtime and mtime != last_sent and time.time() >= next_try:
            # warten, bis WoW fertig geschrieben hat
            time.sleep(2)
            try:
                if os.path.getmtime(path) != mtime:
                    continue
            except OSError:
                continue
            if upload(cfg, path):
                last_sent = mtime
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
