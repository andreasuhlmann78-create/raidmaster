"""UP-CFG1 (ab 2.3.27, Entscheid des Nutzers 25.11.2026 06:29 "Download-Ordner mit Schutz"): neue Einstellungsdateien aus dem
Download-Ordner übernehmen – nur nach Rückfrage (Taste j), mit Schutz.

Warum mit Schutz (Bewertung 25.11. 06:26): Eine fremde Datei mit gleichem Namen sähe gleich aus; mit ihr gingen Spieldaten an
fremde Kanäle. Darum:
1. Nur die zwei Dateien, die der Bot mit /uploader schickt: uploader_config.json und sync_config.json (auch "… (1).json", wie Browser
   und Discord doppelte Namen ablegen). daten_config.json nie (entsteht nur mit Daten-Repo-einrichten.bat). Höchstens 16 kB.
2. Nur wenn die Datei NEUER ist als der letzte bekannte Stand und inhaltlich etwas ändert. Achtung (belegt): uploader_config.json im
   Uploader-Ordner schreibt der Uploader selbst laufend neu (gesendete Bilder) – ihre Änderungszeit taugt nicht als Vergleich. Darum
   gilt je Datei eine Grundzeit (beim ersten Start: jetzt minus 1 Stunde, danach die Zeit der zuletzt bearbeiteten Datei); bei
   sync_config.json zusätzlich die Änderungszeit der Datei im Ordner (die schreibt nur der Nutzer bzw. diese Übernahme). Eine alte Kopie oder dieselbe Datei wird nie
   angeboten; eine abgelehnte Datei (Prüfsumme) nie wieder.
3. Prüfen: gültiges JSON; jede Webhook-Adresse hat die Form https://discord.com/api/webhooks/<Zahl>/<Schlüssel>; sync_index_id ist eine
   Zahl; bot_id ist eine Zahl und – wenn schon eine uploader_config.json da ist – DIESELBE wie bisher (eine Datei eines anderen Bots
   wird abgewiesen).
4. Fragen: "Neue Einstellungsdatei … im Download-Ordner (Zeit) – übernehmen? (j/n)" mit den Kanal-Kennungen alt -> neu (die Zahl in der
   Webhook-Adresse; der geheime Schlüssel wird nie gezeigt). Ohne j passiert nichts.
5. Bei j: alte Datei nach _update/einstellungen/<Name>-<Zeit>.json sichern (die letzten 5), neue über eine Zwischendatei schreiben und
   zurücklesen. uploader_config.json: NUR webhook_url, test_webhook_url und bot_id übernehmen – alles andere (gesendete Bilder,
   SavedVariables-Pfad, Schalter) bleibt; danach Neustart des Uploaders (wie beim Update, mit Rückfall). sync_config.json: ganz
   übernehmen; der laufende Abgleich wechselt ohne Neustart (wie bisher bei einer neuen sync_config.json im Ordner).
6. Den Download-Ordner liest der Uploader nur (Namen und diese zwei Dateien), er ändert und löscht dort nichts.
7. Schalter "einstellungen_aus_downloads" in uploader_config.json (fehlt = an); eigener Ordner: "downloads_pfad".
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import time

KINDS = ("uploader_config", "sync_config")
FILE_RE = re.compile(r"^(uploader_config|sync_config)(?: ?\(\d{1,3}\))?\.json$", re.I)
HOOK_RE = re.compile(r"^https://(?:(?:ptb|canary)\.)?(?:discord\.com|discordapp\.com)/api/webhooks/(\d{5,25})/[A-Za-z0-9_\-]{20,}$")
MAX_BYTES = 16 * 1024
POLL_SECONDS = 30
KEEP_BACKUPS = 5
SWITCH_KEY = "einstellungen_aus_downloads"
PATH_KEY = "downloads_pfad"
BOT_KEYS = ("webhook_url", "test_webhook_url", "bot_id")      # nur diese kommen aus einer neuen uploader_config.json


def downloads_dir(cfg: dict) -> str | None:
    p = cfg.get(PATH_KEY)
    if isinstance(p, str) and p.strip():
        return os.path.normpath(p.strip())
    if sys.platform == "win32":
        try:                                    # bekannter Ordner "Downloads" (auch wenn umgeleitet, z. B. OneDrive)
            import ctypes
            from ctypes import wintypes
            import uuid

            class GUID(ctypes.Structure):
                _fields_ = [("d1", wintypes.DWORD), ("d2", wintypes.WORD), ("d3", wintypes.WORD), ("d4", ctypes.c_ubyte * 8)]
            u = uuid.UUID("{374DE290-123F-4565-9164-39C4925E467B}")
            g = GUID(u.fields[0], u.fields[1], u.fields[2], (ctypes.c_ubyte * 8)(*u.bytes[8:]))
            out = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(out)) == 0:
                path = out.value
                ctypes.windll.ole32.CoTaskMemFree(out)
                if path:
                    return path
        except Exception:  # noqa: BLE001
            pass
    p = os.path.join(os.path.expanduser("~"), "Downloads")
    return p if os.path.isdir(p) else None


def hook_id(url) -> str | None:
    m = HOOK_RE.match(str(url or ""))
    return m.group(1) if m else None


def check(kind: str, new: dict, current: dict | None) -> str:
    """"" = in Ordnung, sonst Grund."""
    if not isinstance(new, dict):
        return "kein gültiger Inhalt"
    if kind == "sync_config":
        if not hook_id(new.get("sync_webhook_url")):
            return "sync_webhook_url ist keine Discord-Webhook-Adresse"
        if not str(new.get("sync_index_id") or "").isdigit():
            return "sync_index_id fehlt"
        return ""
    if not hook_id(new.get("webhook_url")):
        return "webhook_url ist keine Discord-Webhook-Adresse"
    if new.get("test_webhook_url") and not hook_id(new.get("test_webhook_url")):
        return "test_webhook_url ist keine Discord-Webhook-Adresse"
    if not str(new.get("bot_id") or "").isdigit():
        return "bot_id fehlt"
    if current and str(current.get("bot_id") or "").isdigit() and str(current["bot_id"]) != str(new["bot_id"]):
        return "Datei stammt von einem anderen Bot (bot_id passt nicht)"
    return ""


def merged(kind: str, new: dict, current: dict | None) -> dict:
    """Was geschrieben wird: sync_config ganz; uploader_config = bisherige Datei mit den drei Bot-Schlüsseln aus der neuen."""
    if kind == "sync_config":
        return {"sync_webhook_url": new["sync_webhook_url"], "sync_index_id": str(new["sync_index_id"])}
    out = dict(current or {})
    for k in BOT_KEYS:
        if k in new:
            out[k] = new[k]
        else:
            out.pop(k, None)                    # neue Datei ohne test_webhook_url -> Testberichte-Kanal gibt es nicht mehr
    return out


def relevant(kind: str, d: dict | None) -> dict:
    d = d or {}
    keys = ("sync_webhook_url", "sync_index_id") if kind == "sync_config" else BOT_KEYS
    return {k: str(d.get(k)) for k in keys if d.get(k) not in (None, "")}


def ids(kind: str, d: dict | None) -> str:
    d = d or {}
    if kind == "sync_config":
        return f"#sync-daten {hook_id(d.get('sync_webhook_url')) or '–'}"
    t = f"Daten {hook_id(d.get('webhook_url')) or '–'}"
    if d.get("test_webhook_url"):
        t += f", Testberichte {hook_id(d.get('test_webhook_url')) or '–'}"
    return t


class Pickup:
    def __init__(self, here: str, cfg: dict, st: dict, save, log, *, downloads=None, now=time.time):
        self.here, self.cfg, self.save, self.log, self.now = here, cfg, save, log, now
        self.s = st.setdefault("einstellungen", {})
        self.downloads = downloads if downloads is not None else downloads_dir(cfg)
        self.next_at = 0.0
        self.warned: set[str] = set()

    def enabled(self) -> bool:
        return self.cfg.get(SWITCH_KEY) is not False

    def _current(self, kind: str) -> tuple[dict | None, float]:
        p = os.path.join(self.here, kind + ".json")
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f), os.path.getmtime(p)
        except (OSError, ValueError):
            return None, 0.0

    def poll(self) -> dict | None:
        """Höchstens alle POLL_SECONDS: ein Angebot {"kind", "path", "sha", "data", "mtime", "text"} oder None."""
        t = self.now()
        if not self.enabled() or t < self.next_at or not self.downloads or not os.path.isdir(self.downloads):
            return None
        self.next_at = t + POLL_SECONDS
        newest: dict[str, tuple[float, str]] = {}
        try:
            with os.scandir(self.downloads) as it:
                for e in it:
                    m = FILE_RE.match(e.name)
                    if not m or not e.is_file():
                        continue
                    kind = m.group(1).lower()
                    mt = e.stat().st_mtime
                    if kind not in newest or mt > newest[kind][0]:
                        newest[kind] = (mt, e.path)
        except OSError:
            return None
        for kind in KINDS:
            if kind not in newest:
                continue
            mt, path = newest[kind]
            cur, cur_mt = self._current(kind)
            seen = (self.s.get("gesehen") or {}).get(kind) or {}
            basis = self.s.setdefault("basis", {})
            if kind not in basis:
                basis[kind] = t - 3600                    # erster Start: nur Dateien der letzten Stunde
                self.save()
            limit = max(float(basis[kind]), float(seen.get("mtime") or 0), cur_mt if kind == "sync_config" else 0.0)
            if mt <= limit:
                continue                                  # nicht neuer als der bekannte Stand bzw. schon bearbeitet
            try:
                if os.path.getsize(path) > MAX_BYTES:
                    self._seen(kind, mt, "")
                    self._warn(path, f"Einstellungen: {os.path.basename(path)} im Download-Ordner ist zu gross – nicht angeboten.")
                    continue
                with open(path, "rb") as f:
                    raw = f.read(MAX_BYTES + 1)
                new = json.loads(raw.decode("utf-8-sig"))
            except (OSError, ValueError, UnicodeDecodeError):
                continue                                  # z. B. noch nicht fertig gespeichert -> beim nächsten Mal
            sha = hashlib.sha256(raw).hexdigest()
            if sha in (self.s.get("abgelehnt") or []):
                self._seen(kind, mt, sha)
                continue
            why = check(kind, new, cur)
            if why:
                self._seen(kind, mt, sha)
                self.log(f"Einstellungen: {os.path.basename(path)} im Download-Ordner NICHT angeboten – {why}.")
                continue
            if relevant(kind, new) == relevant(kind, cur):
                self._seen(kind, mt, sha)                 # gleiche Kanäle -> nichts zu tun
                continue
            when = time.strftime("%d.%m. %H:%M", time.localtime(mt))
            text = (f"Neue Einstellungsdatei {kind}.json im Download-Ordner ({os.path.basename(path)}, {when}) – übernehmen? (j/n)  "
                    f"Kanal-Kennung bisher: {ids(kind, cur) if cur else 'keine Datei'} -> neu: {ids(kind, new)}"
                    + ("  [danach startet der Uploader neu]" if kind == "uploader_config" else ""))
            return {"kind": kind, "path": path, "sha": sha, "data": new, "mtime": mt, "text": text}
        return None

    def _seen(self, kind: str, mt: float, sha: str):
        self.s.setdefault("gesehen", {})[kind] = {"mtime": mt, "sha": sha}
        self.save()

    def _warn(self, key: str, msg: str):
        if key not in self.warned:
            self.warned.add(key)
            self.log(msg)

    def decline(self, offer: dict):
        lst = list(self.s.get("abgelehnt") or [])
        lst.append(offer["sha"])
        self.s["abgelehnt"] = lst[-50:]
        self._seen(offer["kind"], offer["mtime"], offer["sha"])
        self.log(f"Einstellungen: {offer['kind']}.json nicht übernommen – diese Datei wird nicht mehr angeboten.")

    def accept(self, offer: dict) -> str:
        """Schreibt die Datei. Liefert "neustart" (uploader_config), "ok" (sync_config) oder "fehler"."""
        kind = offer["kind"]
        target = os.path.join(self.here, kind + ".json")
        cur, _ = self._current(kind)
        why = check(kind, offer["data"], cur)              # nochmals – die Datei im Ordner kann sich geändert haben
        if why:
            self.log(f"Einstellungen: {kind}.json NICHT übernommen – {why}.")
            self._seen(kind, offer["mtime"], offer["sha"])
            return "fehler"
        out = merged(kind, offer["data"], cur)
        data = (json.dumps(out, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        try:
            bdir = os.path.join(self.here, "_update", "einstellungen")
            os.makedirs(bdir, exist_ok=True)
            if os.path.isfile(target):
                shutil.copy2(target, os.path.join(bdir, f"{kind}-{time.strftime('%Y%m%d-%H%M%S', time.localtime(self.now()))}.json"))
                olds = sorted(n for n in os.listdir(bdir) if n.startswith(kind + "-"))
                for n in olds[:-KEEP_BACKUPS]:
                    os.remove(os.path.join(bdir, n))
            tmp = target + ".gsneu"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, target)
            with open(target, "rb") as f:
                if f.read() != data:
                    raise OSError("nach dem Schreiben nicht gleich")
        except OSError as e:
            self.log(f"Einstellungen: {kind}.json NICHT übernommen – Schreiben nicht möglich ({e}).")
            return "fehler"
        self._seen(kind, offer["mtime"], offer["sha"])
        self.log(f"Einstellungen: {kind}.json übernommen (alte Datei gesichert in _update\\einstellungen).")
        return "neustart" if kind == "uploader_config" else "ok"
