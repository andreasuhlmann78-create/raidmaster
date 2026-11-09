"""
RaidMaster-Uploader – läuft auf dem PC, auf dem WoW gespielt wird.

Sobald WoW die Datei RaidMaster.lua speichert (nach /reload oder beim Ausloggen), wird sie gepackt
und über einen geheimen Discord-Webhook in den Kanal #bot-daten geschickt. Der Bot auf dem Server
liest sie dort und aktualisiert DKP, Loot, Einteilung und Skillungen.

Start: uploader.bat (Doppelklick). Einrichtung: in Discord /uploader ausführen und die Datei
uploader_config.json in diesen Ordner legen. Nur Python 3 nötig, keine weiteren Pakete.

Erstkill-Screenshots (ab 1.6.0): RaidMaster macht beim Erstkill einen Screenshot und merkt sich die Zeit
(RaidMasterDB.shotList). Der Uploader sucht im Screenshots-Ordner von WoW das passende Bild und schickt es
beim nächsten Upload mit. Andere Screenshots werden nie hochgeladen.

Ab 1.7.0:
- Sucht bei jedem Start und danach alle paar Minuten nach einer neueren RaidMaster.lua (z. B. nach dem Wechsel vom
  Anniversary- in den Forever-Client) und wechselt mit Meldung im Fenster dorthin.
- Gildenbank auch von GuildSentinel: GuildSentinel.lua aus demselben SavedVariables-Ordner geht als zweiter Anhang mit,
  wenn sie sich geändert hat und einen Gildenbank-Bestand enthält (["bank"]). Sonst wird sie nie geschickt.
  Pfad überschreiben: "guildsentinel_path" in uploader_config.json.

Ab 1.8.0 – Testberichte der GoldSentinel-Addons (#testberichte):
- Durchsucht alle *.lua im SavedVariables-Ordner nach Berichten ("GSTEST1…", geschrieben von GoldSentinelTest in
  RaidMaster, ThreatSentinel, BuffSentinel …) und schickt neue gesammelt an den zweiten Webhook "test_webhook_url"
  (Kanal #testberichte, liest die Addon-Prüfung). Nur diese Berichte, sonst nichts aus fremden SavedVariables.
- Unabhängig vom Daten-Upload: ein Fehler beim einen verhindert das andere nie.
- Fehlt test_webhook_url (ältere uploader_config.json): einmal Hinweis "/uploader erneut ausführen", sonst wie bisher.

Ab 1.9.0 – Diagnose-Protokolle und Wegdaten (gleicher Weg, gleicher Kanal #testberichte):
- "GSDIAG1|…"-Diagnoseprotokolle (z. B. AHSentinelDB.diagExport, ProfessionSentinelDB.diagExport) und
  "GSWEGE1{…}"-Wegdaten (LevelPilotDB.wegeExport) aus den SavedVariables nach /reload oder Ausloggen mitschicken.
- Nur diese Zeichenketten, genau so wie sie in den SavedVariables stehen (Anhang gsextras.lua.gz), nichts sonst.
- Nur wenn neu: gemerkt wird ein Prüfwert des Inhalts (sent_extra_ids, höchstens 500). Grössenregeln wie bei
  den Testberichten (je Nachricht höchstens 4 MB entpackt, einzelne über 512 KB werden übersprungen).
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

VERSION = "1.9.0"
SHOT_WINDOW = (-30, 180)          # Bild darf so viele Sekunden vor/nach der gemerkten Zeit entstanden sein
SHOT_MAX_BYTES = 9 * 1024 * 1024
SHOT_MAX_AGE = 14 * 86400
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "uploader_config.json")
USER_AGENT = f"RaidMasterUploader (https://github.com, {VERSION})"
RESCAN_SECONDS = 300              # so oft nach einer neueren RaidMaster.lua suchen (Wechsel in den Forever-Ordner)
NEWER_BY_SECONDS = 60             # erst wechseln, wenn die gefundene Datei so viel neuer ist
GS_BANK = re.compile(rb'\["bank"\]\s*=\s*\{')

# Testberichte (GoldSentinelTest): gleiche Regeln wie addon-check/testberichte.py (Gegenstelle der Addon-Prüfung)
TEST_PREFIX = "GSTEST1"
TEST_STR = re.compile(r'"(' + TEST_PREFIX + r'(?:[^"\\]|\\.)*)"', re.S)
TEST_MAX_JSON = 4 * 1024 * 1024        # entpackt höchstens so viel je Nachricht
TEST_MAX_SENT_IDS = 500
TEST_USERNAME = "GoldSentinel-Testberichte"
TEST_STABLE_SECONDS = 2
EXTRA_PREFIXES = ("GSDIAG1", "GSWEGE1")
EXTRA_STR = re.compile(r'"((?:GSDIAG1\||GSWEGE1\{)(?:[^"\\]|\\.)*)"', re.S)
EXTRA_MAX_ONE = 512 * 1024              # so wertet die Addon-Prüfung höchstens aus (testberichte.MAX_EXTRA)
EXTRA_MAX_SENT_IDS = 500


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


def newer_saved_variables(path: str, found: list[str] | None = None) -> str | None:
    """Gibt es eine deutlich neuere RaidMaster.lua als die überwachte (z. B. im Forever-Ordner)? Dann ihr Pfad."""
    if found is None:
        found = find_saved_variables()
    try:
        current = os.path.getmtime(path) if path and os.path.isfile(path) else 0
    except OSError:
        current = 0
    for cand in found:
        if os.path.normpath(cand) == os.path.normpath(path or ""):
            continue
        try:
            if os.path.getmtime(cand) > current + NEWER_BY_SECONDS:
                return cand.replace("\\", "/")
        except OSError:
            pass
        break                                   # found ist nach Datum sortiert: nur die neueste zählt
    return None


def switch_if_newer(cfg: dict, path: str, found: list[str] | None = None) -> str:
    new = newer_saved_variables(path, found)
    if not new:
        return path
    log("Neuere RaidMaster-Datei gefunden (z. B. nach dem Wechsel in einen anderen WoW-Client).")
    log("Wechsle zu: " + new)
    cfg["savedvariables_path"] = new
    save_config(cfg)
    return new


def guildsentinel_path(cfg: dict, path: str) -> str:
    """GuildSentinel.lua liegt im selben SavedVariables-Ordner wie RaidMaster.lua."""
    return cfg.get("guildsentinel_path") or os.path.join(os.path.dirname(os.path.abspath(path)), "GuildSentinel.lua")


def read_guildsentinel(gs_path: str) -> bytes | None:
    """GuildSentinel.lua nur mit Gildenbank-Bestand – sonst nichts schicken (keine fremden Daten)."""
    try:
        with open(gs_path, "rb") as f:
            raw = f.read()
    except OSError:
        return None
    return raw if GS_BANK.search(raw) else None


def build_body(payload: dict, packed: bytes, gs_packed: bytes | None, shots: list[tuple[str, str, bytes]]) -> tuple[str, bytes]:
    """Multipart-Inhalt: files[0] = RaidMaster.lua.gz (immer zuerst), files[1] = GuildSentinel.lua.gz (falls dabei),
    danach die Screenshots. shots = [(Name, Content-Type, Daten)]."""
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
    n = 1
    if gs_packed is not None:
        parts += [f"--{boundary}\r\n".encode(),
                  b'Content-Disposition: form-data; name="files[1]"; filename="GuildSentinel.lua.gz"\r\n'
                  b"Content-Type: application/gzip\r\n\r\n",
                  gs_packed, b"\r\n"]
        n = 2
    for i, (name, ctype, data) in enumerate(shots, n):
        parts += [f"--{boundary}\r\n".encode(),
                  f'Content-Disposition: form-data; name="files[{i}]"; filename="{name}"\r\nContent-Type: {ctype}\r\n\r\n'.encode(),
                  data, b"\r\n"]
    parts.append(f"--{boundary}--\r\n".encode())
    return boundary, b"".join(parts)


# ---------------------------------------------------------------------------
# Testberichte (#testberichte)
# ---------------------------------------------------------------------------
def lua_unescape(s: str) -> str:
    """Lua-String aus SavedVariables zurückwandeln (wie testberichte.lua_unescape): \\" \\\\ \\n \\t \\r,
    Backslash + Zeilenumbruch, \\ddd (Bytes, danach latin-1 -> UTF-8)."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            if n.isdigit():
                m = re.match(r"\d{1,3}", s[i + 1:])
                out.append(chr(int(m.group(0))))
                i += 1 + len(m.group(0))
                continue
            out.append({"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'", "\n": "\n"}.get(n, n))
            i += 2
            continue
        out.append(c)
        i += 1
    text = "".join(out)
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def reports_in_text(text: str, source: str = "") -> list[dict]:
    """Alle GSTEST1-Berichte in einem SavedVariables-Text. Kaputte werden mit Log-Zeile übersprungen."""
    found = []
    for m in TEST_STR.finditer(text):
        raw = lua_unescape(m.group(1))[len(TEST_PREFIX):]
        try:
            rep = json.loads(raw)
        except ValueError:
            log(f"Testbericht in {source or 'Datei'} nicht lesbar – übersprungen.")
            continue
        if isinstance(rep, dict) and rep.get("id"):
            found.append(rep)
    return found


def extras_in_text(text: str) -> list[dict]:
    """GSDIAG1-/GSWEGE1-Zeichenketten in einem SavedVariables-Text, unverändert (noch Lua-escaped).
    id = Prüfwert des Inhalts, kind = "diag" oder "wege"."""
    import hashlib
    out = []
    for m in EXTRA_STR.finditer(text):
        raw = m.group(1)
        out.append({"id": "x-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16],
                    "kind": "diag" if raw.startswith("GSDIAG1") else "wege", "raw": raw})
    return out


class TestReportScanner:
    """Merkt sich je *.lua im SavedVariables-Ordner die mtime und liest nur geänderte Dateien neu.
    scan() liefert neue Testberichte; neue Diagnose-/Wegdaten (ab 1.9.0) landen beim selben Durchgang in .extras."""

    def __init__(self, folder: str):
        self.folder = folder
        self.mtimes: dict[str, float] = {}
        self.extras: list[dict] = []

    def scan(self, cfg: dict, now: float | None = None) -> list[dict]:
        """Neue Berichte (id nicht in sent_test_ids), nach id entdoppelt."""
        now = time.time() if now is None else now
        sent = set(cfg.get("sent_test_ids") or [])
        sent_x = set(cfg.get("sent_extra_ids") or []) | {x["id"] for x in self.extras}
        out, seen = [], set()
        try:
            names = sorted(fn for fn in os.listdir(self.folder) if fn.lower().endswith(".lua"))
        except OSError:
            return []
        for fn in names:
            full = os.path.join(self.folder, fn)
            try:
                mt = os.path.getmtime(full)
            except OSError:
                continue
            if self.mtimes.get(fn) == mt or now - mt < TEST_STABLE_SECONDS:
                continue                    # unverändert oder WoW schreibt noch
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            self.mtimes[fn] = mt
            if any(p in text for p in EXTRA_PREFIXES):
                for x in extras_in_text(text):
                    if x["id"] not in sent_x:
                        sent_x.add(x["id"])
                        self.extras.append(x)
            if TEST_PREFIX not in text:
                continue
            for rep in reports_in_text(text, fn):
                rid = str(rep.get("id"))
                if rid in sent or rid in seen:
                    continue
                seen.add(rid)
                out.append(rep)
        return out


def chunk_reports(reports: list[dict]) -> list[list[dict]]:
    """In Gruppen aufteilen, die entpackt höchstens TEST_MAX_JSON gross sind. Einzelne zu grosse überspringen."""
    chunks, cur, size = [], [], 2
    for rep in reports:
        n = len(json.dumps(rep, ensure_ascii=False).encode("utf-8")) + 2
        if n + 2 > TEST_MAX_JSON:
            log(f"Testbericht {rep.get('id')} ist zu gross ({n // 1024} KB) – übersprungen.")
            continue
        if cur and size + n > TEST_MAX_JSON:
            chunks.append(cur)
            cur, size = [], 2
        cur.append(rep)
        size += n
    if cur:
        chunks.append(cur)
    return chunks


def report_body(reports: list[dict]) -> tuple[str, bytes]:
    payload = {"content": f"GoldSentinel-Testberichte: {len(reports)} neu", "username": TEST_USERNAME,
               "allowed_mentions": {"parse": []}}
    packed = gzip.compress(json.dumps(reports, ensure_ascii=False).encode("utf-8"), 9)
    boundary = "----GSTest" + uuid.uuid4().hex
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="payload_json"\r\nContent-Type: application/json\r\n\r\n',
        json.dumps(payload).encode("utf-8"), b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="files[0]"; filename="testberichte.json.gz"\r\n'
        b"Content-Type: application/gzip\r\n\r\n",
        packed, b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])
    return boundary, body


def post_webhook(url: str, boundary: str, body: bytes, sleep=time.sleep) -> str:
    """"ok", "invalid" (401/404), "error" (5xx, Verbindung, sonst). 429 wird abgewartet und wiederholt."""
    full = url + ("&" if "?" in url else "?") + "wait=true"
    req = urllib.request.Request(full, data=body, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": USER_AGENT})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                r.read()
            return "ok"
        except urllib.error.HTTPError as e:
            if e.code == 429:
                try:
                    wait = float(json.loads(e.read().decode()).get("retry_after", 5))
                except (ValueError, AttributeError):
                    wait = 5
                sleep(min(wait, 60) + 0.5)
                continue
            if e.code in (401, 404):
                return "invalid"
            return "error"
        except (urllib.error.URLError, OSError):
            return "error"
    return "error"


def send_reports(cfg: dict, reports: list[dict], sleep=time.sleep) -> bool:
    """Neue Berichte gesammelt an #testberichte. Erst nach Erfolg als gesendet merken. True = alles gesendet."""
    url = cfg.get("test_webhook_url") or ""
    if not url.startswith("https://") or not reports:
        return not reports
    all_ok = True
    for chunk in chunk_reports(reports):
        boundary, body = report_body(chunk)
        result = post_webhook(url, boundary, body, sleep)
        if result == "ok":
            ids = list(cfg.get("sent_test_ids") or []) + [str(r.get("id")) for r in chunk]
            cfg["sent_test_ids"] = ids[-TEST_MAX_SENT_IDS:]
            save_config(cfg)
            log(f"{len(chunk)} Testbericht(e) an #testberichte geschickt.")
        else:
            all_ok = False
            if result == "invalid":
                log("Webhook für #testberichte ungültig – /uploader erneut ausführen.")
            else:
                log("Testberichte konnten nicht geschickt werden – neuer Versuch später.")
            break
    return all_ok


def extras_body(extras: list[dict]) -> tuple[str, bytes]:
    """Eine Nachricht mit Anhang gsextras.lua.gz: je Zeile eine Zeichenkette wie in den SavedVariables ("…")."""
    nd = sum(1 for x in extras if x["kind"] == "diag")
    payload = {"content": f"GoldSentinel-Diagnose/Wegdaten: {nd} Diagnose, {len(extras) - nd} Wegdaten",
               "username": TEST_USERNAME, "allowed_mentions": {"parse": []}}
    text = "".join('"' + x["raw"] + '"\n' for x in extras)
    packed = gzip.compress(text.encode("utf-8"), 9)
    boundary = "----GSExtra" + uuid.uuid4().hex
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="payload_json"\r\nContent-Type: application/json\r\n\r\n',
        json.dumps(payload).encode("utf-8"), b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="files[0]"; filename="gsextras.lua.gz"\r\n'
        b"Content-Type: application/gzip\r\n\r\n",
        packed, b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])
    return boundary, body


def chunk_extras(extras: list[dict]) -> list[list[dict]]:
    chunks, cur, size = [], [], 0
    for x in extras:
        n = len(x["raw"].encode("utf-8")) + 3
        if n > EXTRA_MAX_ONE:
            log(f"{'Diagnose' if x['kind'] == 'diag' else 'Wegdaten'} zu gross ({n // 1024} KB) – übersprungen.")
            continue
        if cur and size + n > TEST_MAX_JSON:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(x)
        size += n
    if cur:
        chunks.append(cur)
    return chunks


def send_extras(cfg: dict, extras: list[dict], sleep=time.sleep) -> bool:
    """Neue Diagnose-/Wegdaten an #testberichte. Erst nach Erfolg merken. True = alles gesendet."""
    url = cfg.get("test_webhook_url") or ""
    if not url.startswith("https://") or not extras:
        return not extras
    for chunk in chunk_extras(extras):
        boundary, body = extras_body(chunk)
        result = post_webhook(url, boundary, body, sleep)
        if result != "ok":
            log("Webhook für #testberichte ungültig – /uploader erneut ausführen." if result == "invalid"
                else "Diagnose/Wegdaten konnten nicht geschickt werden – neuer Versuch später.")
            return False
        ids = list(cfg.get("sent_extra_ids") or []) + [x["id"] for x in chunk]
        cfg["sent_extra_ids"] = ids[-EXTRA_MAX_SENT_IDS:]
        save_config(cfg)
        log(f"{len(chunk)} Diagnose-/Wegdaten an #testberichte geschickt.")
    return True


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


def upload(cfg: dict, path: str, gs_raw: bytes | None = None) -> bool:
    with open(path, "rb") as f:
        raw = f.read()
    packed = gzip.compress(raw, 9)
    gs_packed = gzip.compress(gs_raw, 9) if gs_raw else None
    shots = []
    try:
        # Discord nimmt pro Nachricht nur ca. 10 MB an: Bilder nur, solange alles zusammen darunter bleibt
        total = len(packed) + len(gs_packed or b"")
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
    shot_data = []
    for full, name, _ in shots:
        with open(full, "rb") as f:
            shot_data.append((name, "image/png" if name.endswith(".png") else "image/jpeg", f.read()))
    boundary, body = build_body(payload, packed, gs_packed, shot_data)
    url = cfg["webhook_url"] + ("&" if "?" in cfg["webhook_url"] else "?") + "wait=true"
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                r.read()
            log(f"Hochgeladen ({len(raw) // 1024} KB, gepackt {len(packed) // 1024} KB)."
                + (" Dazu der Gildenbank-Bestand aus GuildSentinel." if gs_packed else "")
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


def gs_mtime(gs_path: str) -> float:
    try:
        return os.path.getmtime(gs_path)
    except OSError:
        return 0


def main():
    log(f"RaidMaster-Uploader {VERSION}")
    cfg = load_config()
    stored = cfg.get("savedvariables_path") or ""
    had_stored = bool(stored) and os.path.isfile(stored)
    path = choose_path(cfg)
    if had_stored:
        # gespeicherter Pfad: trotzdem suchen – nach dem Forever-Start liegt die aktuelle Datei woanders
        log("Prüfe, ob es eine neuere RaidMaster-Datei gibt (z. B. im Forever-Ordner) ...")
        path = switch_if_newer(cfg, path)
    log("Überwache: " + path)
    log("Fenster offen lassen. Nach /reload oder Ausloggen werden die Daten automatisch hochgeladen.")
    interval = max(3, int(cfg.get("check_seconds") or 10))
    test_scanner = TestReportScanner(os.path.dirname(os.path.abspath(path)))
    test_pending: list[dict] = []
    test_failures = 0
    test_next_try = 0.0
    if not (cfg.get("test_webhook_url") or "").startswith("https://"):
        log("Hinweis: Für Testberichte (#testberichte) in Discord /uploader erneut ausführen und die neue "
            "uploader_config.json hineinlegen. Der Daten-Upload läuft trotzdem wie bisher.")
    last_sent = 0.0
    last_gs_seen = 0.0          # zuletzt gesehene Änderung von GuildSentinel.lua
    pending_gs = None           # GuildSentinel.lua mit Bestand, die noch mitgeschickt werden muss
    failures = 0
    next_try = 0.0
    next_scan = time.time() + RESCAN_SECONDS
    while True:
        if time.time() >= next_scan:
            next_scan = time.time() + RESCAN_SECONDS
            new = switch_if_newer(cfg, path)
            if new != path:
                path = new
                last_sent = 0.0
                test_scanner = TestReportScanner(os.path.dirname(os.path.abspath(path)))
                log("Überwache: " + path)
        gs_file = guildsentinel_path(cfg, path)
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0
        gmt = gs_mtime(gs_file)
        if gmt and gmt != last_gs_seen:
            time.sleep(2)                       # warten, bis WoW fertig geschrieben hat
            if gs_mtime(gs_file) != gmt:
                continue
            last_gs_seen = gmt
            # nur mit Gildenbank-Bestand – sonst löst GuildSentinel.lua keinen Upload aus
            pending_gs = read_guildsentinel(gs_file) or pending_gs
        if mtime and (mtime != last_sent or pending_gs) and time.time() >= next_try:
            # warten, bis WoW fertig geschrieben hat
            time.sleep(2)
            try:
                if os.path.getmtime(path) != mtime:
                    continue
            except OSError:
                continue
            if upload(cfg, path, pending_gs):
                last_sent = mtime
                pending_gs = None
                failures = 0
            else:
                failures += 1
                next_try = time.time() + min(600, 30 * failures)
        # Testberichte: eigener Weg, eigene Wartezeit – Fehler hier stören den Daten-Upload nie
        try:
            if (cfg.get("test_webhook_url") or "").startswith("https://"):
                known = {str(r.get("id")) for r in test_pending}
                test_pending += [r for r in test_scanner.scan(cfg) if str(r.get("id")) not in known]
                if test_pending and time.time() >= test_next_try:
                    if send_reports(cfg, test_pending):
                        test_pending, test_failures = [], 0
                    else:
                        sent = set(cfg.get("sent_test_ids") or [])
                        test_pending = [r for r in test_pending if str(r.get("id")) not in sent]
                        test_failures += 1
                        test_next_try = time.time() + min(600, 30 * test_failures)
                if test_scanner.extras and time.time() >= test_next_try:
                    if send_extras(cfg, test_scanner.extras):
                        test_scanner.extras = []
                    else:
                        sent_x = set(cfg.get("sent_extra_ids") or [])
                        test_scanner.extras = [x for x in test_scanner.extras if x["id"] not in sent_x]
                        test_failures += 1
                        test_next_try = time.time() + min(600, 30 * test_failures)
        except Exception as e:  # noqa: BLE001
            log(f"Testberichte: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
