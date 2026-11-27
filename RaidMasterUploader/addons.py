"""UP-AUTO1 (ab 2.3.21, Entscheid des Nutzers 24.11.2026 20:28 "ich möchte das für den laptop auch"):
Der Uploader installiert neue Versionen der GoldSentinel-Addons selbst in den Forever-AddOns-Ordner.

Regeln (auftraege/RaidMaster/offen-raidmaster.txt, UP-AUTO1):
1. Quelle nur das öffentliche Repo raidmaster (GitHub-API, HTTPS, ohne Token): je Addon die höchste Version aus announce/
   ("<kanal>__<reihe>-<version>.<Addon>.zip", Discord-Versionen) bzw. download/ ("<Addon>-<version>.zip"). Versionen werden
   wie announce_reihe.announce_series verglichen (Zahlen je Teil, "0.65.9" < "0.65.10"); ein Test prüft die Gleichheit.
   Nur Addons, deren Ordner im AddOns-Ordner schon liegt. Nie fremde Addons (nur Namen aus diesen Zips), nie GSMesstest.
2. Nur wenn neuer als "## Version" der installierten .toc. Vor dem Kopieren: Prüfsumme (Git-Blob-SHA) = die Datei im Repo,
   Zip vollständig (jede Datei mit richtiger CRC), Ordner = Addon-Name, <Addon>/<Addon>.toc mit Version = erwartet.
   Sonst nichts tun und melden. Ausnahme, belegt an den Zips im Repo (24.11.): LevelPilot liefert in DERSELBEN Zip seine
   Daten-Ordner LevelPilot_Data, LevelPilot_Data_deDE … mit. Erlaubt sind darum nur Ordner "<Addon>" und "<Addon>_<…>";
   jeder andere Ordner -> nichts installiert.
3. Nur geänderte Dateien schreiben (über eine Zwischendatei, danach byte-genau zurücklesen). Nur unter <AddOns>/<Addon>/ –
   nie WTF/SavedVariables. NICHTS löschen (Dateien, die die neue Version nicht mehr hat, bleiben; im Log genannt).
   Die .toc wird zuletzt geschrieben: bricht es mittendrin ab, zeigt die .toc noch die alte Version -> nächster Versuch.
4. Meldung je Addon: "<Addon> a -> b installiert – im Spiel /reload" bzw. "– NEUSTART des Spiels nötig (neue Dateien: n)".
   "Die .toc ändert sich" heisst: ausser der Zeile "## Version" (die ändert sich bei jeder Version, dafür reicht /reload).
   Fehler (Datei gesperrt, kein Schreibrecht) klar melden, erneut versuchen nach 1, 2, 4, 8, 16 Min., danach bis zur
   nächsten Version bzw. zum nächsten Start nicht mehr (kein Endlos-Versuch).
5. Schalter "addons_auto_installieren" in uploader_config.json. RM-UPD2 (2.3.29, Entscheid des Nutzers 27.11.2026 07:10 "dass die
   addon versionen automatisch geholt werden und installiert ohne dass man in der uploaderdatei irgendwas anklicken muss"):
   Standard AN. AUS nur, wenn jemand es ausdrücklich gewählt hat (Addons-automatisch-aus.bat setzt dazu den Merker
   "addons_auto_gewaehlt"; ohne Merker gilt AN – auch ein älteres "false"). Pfad: "addons_pfad", sonst <_forever_>/Interface/AddOns.
5a. RM-UPD2 (Entscheid des Nutzers 27.11.2026 07:11 "sie sollen nur die stabilen versionen bekommen"): Kanal "addons_kanal" –
   "stabil" (Standard): NUR download/ ("<Addon>-<version>.zip"), nie announce/ (Discord-/Testversionen); "test": höchste aus
   announce/ und download/ (für die eigenen Rechner des Nutzers; Addons-Testversionen-an.bat / -aus.bat).
6. Höchstens alle 5 Min. (CHECK_SECONDS); läuft im selben Ablauf wie das Hochladen der Daten, also nie gleichzeitig.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import time
import urllib.error
import urllib.request
import zipfile

REPO = "andreasuhlmann78-create/raidmaster"
API = "https://api.github.com"
FOLDERS = ("announce", "download")       # Reihenfolge = Vorrang bei gleicher Version (Discord-Version zuerst)
STABLE_FOLDERS = ("download",)           # RM-UPD2: Kanal "stabil" (Standard) – nur abgenommene Zips
CHECK_SECONDS = 300
RETRY_MINUTES = (1, 2, 4, 8, 16)         # danach Ruhe bis zur nächsten Version bzw. zum Neustart
NEVER = {"gsmesstest"}                   # nie installieren (Messwerkzeuge u. ä.), Kleinschreibung
MAX_ZIP = 60 * 1024 * 1024               # grösste erlaubte Zip (Schutz gegen Fehlgriffe)
CONFIG_KEY = "addons_auto_installieren"
PATH_KEY = "addons_pfad"
CHOSEN_KEY = "addons_auto_gewaehlt"      # RM-UPD2: nur mit diesem Merker gilt ein "aus"
CHANNEL_KEY = "addons_kanal"             # RM-UPD2: "stabil" (Standard) | "test"


def auto_enabled(cfg: dict) -> bool:
    """RM-UPD2: Standard AN; AUS nur bei ausdrücklicher Wahl (Merker)."""
    return not (cfg.get(CONFIG_KEY) is False and cfg.get(CHOSEN_KEY) is True)


def channel_folders(cfg: dict) -> tuple:
    """RM-UPD2: "test" -> announce/ + download/, sonst (auch unbekannte Werte) nur download/."""
    return FOLDERS if str(cfg.get(CHANNEL_KEY) or "").strip().lower() == "test" else STABLE_FOLDERS

ZIP_ANNOUNCE = re.compile(r"^[^/]+__.+?[-_ ]v?(?P<ver>\d+(?:\.\d+)+)\.(?P<addon>[A-Za-z][A-Za-z0-9_]*)\.zip$")
ZIP_DOWNLOAD = re.compile(r"^(?P<addon>[A-Za-z][A-Za-z0-9_]*)-(?P<ver>\d+(?:\.\d+)+)\.zip$")
TOC_VERSION = re.compile(rb"^##\s*Version\s*:\s*(\S+)", re.M)
NAME_OK = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def version_key(v) -> tuple:
    """Wie announce_reihe.announce_series: Zahlen je Teil. Unlesbar -> ()."""
    try:
        return tuple(int(p) for p in str(v).strip().split("."))
    except ValueError:
        return ()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def parse_entry(folder: str, name: str):
    """(Addon, Version-String) einer Zip im Repo, sonst None."""
    m = (ZIP_ANNOUNCE if folder == "announce" else ZIP_DOWNLOAD).match(name)
    if not m:
        return None
    return m.group("addon"), m.group("ver")


def newest(listing: dict[str, list[dict]], folders: tuple = FOLDERS) -> dict[str, dict]:
    """{Addon: {"ver", "key", "folder", "name", "sha", "url", "size"}} – je Addon die höchste Version aus den Ordnern folders."""
    out: dict[str, dict] = {}
    for folder in folders:
        for e in listing.get(folder) or []:
            if e.get("type") not in (None, "file"):
                continue
            got = parse_entry(folder, str(e.get("name") or ""))
            if not got:
                continue
            addon, ver = got
            if addon.lower() in NEVER:
                continue
            key = version_key(ver)
            cur = out.get(addon)
            if cur is None or key > cur["key"]:          # gleiche Version: die zuerst gefundene (announce/) bleibt
                out[addon] = {"ver": ver, "key": key, "folder": folder, "name": e["name"], "sha": e.get("sha"),
                              "url": e.get("download_url"), "size": int(e.get("size") or 0)}
    # Ordner, die mit einem anderen Addon mitkommen (LevelPilot_Data in der LevelPilot-Zip), nie für sich installieren:
    # ihre alten Einzel-Zips tragen die Version von LevelPilot im Namen, in der .toc aber eine eigene (belegt: …-3.5.0.
    # LevelPilot_Data.zip hat "## Version: 1.5.0")
    for name in [n for n in out if any(n != m and n.startswith(m + "_") for m in out)]:
        out.pop(name)
    return out


def installed_version(addons_dir: str, addon: str) -> str | None:
    """"## Version" aus <AddOns>/<Addon>/<Addon>.toc; None, wenn nicht installiert oder unlesbar."""
    toc = os.path.join(addons_dir, addon, addon + ".toc")
    try:
        with open(toc, "rb") as f:
            m = TOC_VERSION.search(f.read(64 * 1024))
    except OSError:
        return None
    return m.group(1).decode("utf-8", "replace") if m else None


def own_folder(addon: str, top: str) -> bool:
    """Ordner, die zu diesem Addon gehören: <Addon> und <Addon>_<…> (z. B. LevelPilot_Data_deDE)."""
    return top == addon or (top.startswith(addon + "_") and bool(NAME_OK.match(top)))


def check_zip(data: bytes, addon: str, ver: str, sha: str | None) -> tuple[dict[str, bytes] | None, str]:
    """Regel 2: (Dateien {Pfad ab AddOns, z. B. "AHSentinel/Core.lua": Inhalt}, "") oder (None, Grund)."""
    if not sha or git_blob_sha(data) != sha:
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
        if info.is_dir() or n.endswith("/"):
            if not own_folder(addon, n.split("/")[0]):
                return None, f"fremder Ordner in der Zip ({n.split('/')[0]})"
            continue
        parts = n.split("/")
        if len(parts) < 2 or not own_folder(addon, parts[0]):
            return None, f"Datei ausserhalb des Ordners {addon} ({parts[0]})"
        if n.startswith("/") or ":" in n or any(p in ("", ".", "..") for p in parts):
            return None, f"unzulässiger Pfad ({n})"
        files[n] = zf.read(info)
    toc = files.get(f"{addon}/{addon}.toc")
    if toc is None:
        return None, f"{addon}.toc fehlt"
    m = TOC_VERSION.search(toc)
    if not m or m.group(1).decode("utf-8", "replace") != ver:
        got = m.group(1).decode("utf-8", "replace") if m else "keine"
        return None, f"Version in der .toc ist {got}, erwartet {ver}"
    return files, ""


def _toc_body(data: bytes | None) -> bytes:
    """.toc ohne die Zeile "## Version" (die ändert sich bei jeder Version)."""
    return re.sub(rb"(?m)^##\s*Version\s*:.*\r?\n?", b"", data or b"")


def install(addons_dir: str, addon: str, files: dict[str, bytes]) -> dict:
    """Regel 3: nur geänderte Dateien, <Addon>.toc zuletzt, je Datei zurücklesen. Wirft OSError bei gesperrter Datei usw."""
    root = os.path.realpath(addons_dir)
    main_toc = f"{addon}/{addon}.toc"
    order = sorted(files, key=lambda p: (p == main_toc, p))                 # Haupt-.toc zuletzt
    written, new, same = [], [], 0
    toc_changed = False
    tops = sorted({p.split("/")[0] for p in files})
    for rel in order:
        data = files[rel]
        top = rel.split("/")[0]
        target = os.path.realpath(os.path.join(root, *rel.split("/")))
        if not own_folder(addon, top) or os.path.commonpath([os.path.join(root, top), target]) != os.path.realpath(
                os.path.join(root, top)):
            raise OSError(f"Pfad ausserhalb von {addon}: {rel}")
        existed = os.path.isfile(target)
        old = None
        if existed:
            with open(target, "rb") as f:
                old = f.read()
            if old == data:
                same += 1
                continue
        if rel.lower().endswith(".toc") and _toc_body(old) != _toc_body(data):
            toc_changed = True                         # mehr als die Version geändert (oder neue .toc) -> Neustart
        os.makedirs(os.path.dirname(target), exist_ok=True)
        tmp = target + ".gsneu"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, target)
        with open(target, "rb") as f:
            if f.read() != data:
                raise OSError(f"{rel}: nach dem Schreiben nicht gleich")
        written.append(rel)
        if not existed:
            new.append(rel)
    kept = []                                          # nichts löschen – nur nennen
    for top in tops:
        base = os.path.join(root, top)
        for dp, _dn, fns in os.walk(base):
            for fn in fns:
                rel = os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, "/")
                if rel not in files and not rel.endswith(".gsneu"):
                    kept.append(rel)
    return {"written": written, "new": new, "same": same, "toc": toc_changed, "kept": sorted(kept)}


def http_get(url: str, headers: dict | None = None, timeout: int = 60, ctx=None):
    """(Status, Kopf, Inhalt). 304 und Fehler als Status, nie eine Ausnahme nach aussen ausser bei Netzfehlern."""
    req = urllib.request.Request(url, headers={"User-Agent": "GoldSentinel-Uploader", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status, dict(r.headers), r.read(MAX_ZIP + 1)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), b""


class AutoInstall:
    def __init__(self, cfg: dict, addons_dir: str | None, log, get=None, ctx=None):
        self.cfg = cfg
        self.dir = addons_dir
        self.log = log
        self.get = get or (lambda url, headers=None: http_get(url, headers, ctx=ctx))
        self.next_at = 0.0
        self.etag: dict[str, str] = {}
        self.listing: dict[str, list] = {}
        self.tree_sha: dict[str, str] = {}
        self.fail: dict[str, tuple[str, int, float]] = {}     # Addon -> (Version, Versuche, nächster Versuch)
        self.warned: set[str] = set()
        self.done: list[str] = []

    def enabled(self) -> bool:
        return auto_enabled(self.cfg)

    def folders(self) -> tuple:
        return channel_folders(self.cfg)

    def _say(self, key: str, msg: str):
        if key not in self.warned:
            self.warned.add(key)
            self.log(msg)

    def _list(self) -> bool:
        """announce/ und download/ lesen. Weg (belegt: GitHubs Ordner-Liste "contents" hört bei 1000 Einträgen auf, announce/
        hat 675 und wächst): 1) Wurzel des Repos (bedingte Anfrage, unverändert = 304 zählt nicht gegen die Grenze) liefert
        die Baum-Kennung (SHA) jedes Ordners, 2) nur wenn sich die Kennung geändert hat, den Baum des Ordners lesen (ohne
        Grenze bei dieser Grösse). Ohne Token höchstens 3 Anfragen je 5 Min. (GitHub erlaubt 60 je Stunde)."""
        url = f"{API}/repos/{REPO}/contents"
        hdr = {"Accept": "application/vnd.github+json"}
        # bedingt nur, wenn jeder Ordner des Kanals schon einmal gelesen ist (sonst fehlte er nach einem Wechsel des Kanals)
        if self.etag.get("/") and all(f in self.tree_sha for f in self.folders()):
            hdr["If-None-Match"] = self.etag["/"]
        status, head, body = self.get(url, hdr)
        if status == 304:
            return True
        if status != 200:
            self._say(f"list{status}", f"Addons: Liste aus dem Repo nicht lesbar (HTTP {status}) – neuer Versuch in "
                                       f"{CHECK_SECONDS // 60} Min.")
            return False
        try:
            root = json.loads(body.decode("utf-8"))
        except ValueError:
            return False
        trees = {e.get("name"): e.get("sha") for e in root if isinstance(e, dict) and e.get("type") == "dir"} \
            if isinstance(root, list) else {}
        for folder in self.folders():
            sha = trees.get(folder)
            if not sha:
                return False
            if self.tree_sha.get(folder) == sha:
                continue
            st, _h, b = self.get(f"{API}/repos/{REPO}/git/trees/{sha}", {"Accept": "application/vnd.github+json"})
            if st != 200:
                self._say(f"tree{st}", f"Addons: Ordner {folder} im Repo nicht lesbar (HTTP {st}) – neuer Versuch in "
                                       f"{CHECK_SECONDS // 60} Min.")
                return False
            try:
                data = json.loads(b.decode("utf-8"))
            except ValueError:
                return False
            if not isinstance(data, dict) or data.get("truncated"):
                self._say("trunc", f"Addons: Ordner {folder} zu gross für eine Liste – nichts installiert.")
                return False
            self.listing[folder] = [{"name": e.get("path"), "type": "file", "sha": e.get("sha"), "size": e.get("size"),
                                     "download_url": f"{API}/repos/{REPO}/git/blobs/{e.get('sha')}"}
                                    for e in data.get("tree") or [] if e.get("type") == "blob"]
            self.tree_sha[folder] = sha
        etag = {k.lower(): v for k, v in head.items()}.get("etag")
        if etag:
            self.etag["/"] = etag
        return True

    def tick(self, now: float | None = None) -> list[str]:
        """Höchstens alle CHECK_SECONDS. Liefert die Meldungen dieses Durchgangs (auch ins Log)."""
        now = time.time() if now is None else now
        if not self.enabled() or now < self.next_at:
            return []
        self.next_at = now + CHECK_SECONDS
        if not self.dir or not os.path.isdir(self.dir):
            self._say("nodir", "Addons: AddOns-Ordner von Forever nicht gefunden – \"addons_pfad\" in uploader_config.json "
                               "eintragen. Nichts installiert.")
            return []
        try:
            if not self._list():
                return []
        except OSError as e:
            self._say("net", f"Addons: Repo nicht erreichbar ({e.__class__.__name__}) – neuer Versuch in "
                             f"{CHECK_SECONDS // 60} Min.")
            return []
        out = []
        for addon, best in sorted(newest(self.listing, self.folders()).items()):
            if not NAME_OK.match(addon) or not os.path.isdir(os.path.join(self.dir, addon)):
                continue                                         # nur Addons, die schon installiert sind
            have = installed_version(self.dir, addon)
            if have is None or not version_key(have) or best["key"] <= version_key(have):
                continue
            f = self.fail.get(addon)
            if f and f[0] == best["ver"] and (f[1] > len(RETRY_MINUTES) or now < f[2]):
                continue
            msg = self._one(addon, have, best, now)
            if msg:
                out.append(msg)
                self.log(msg)
        return out

    def _one(self, addon: str, have: str, best: dict, now: float) -> str | None:
        if best["size"] > MAX_ZIP or not best.get("url"):
            return self._failed(addon, best, now, "Zip zu gross oder ohne Adresse", final=True)
        try:
            # Inhalt genau dieser Datei-Kennung (Git-Blob), nicht "was gerade auf main liegt" – Prüfsumme wird trotzdem geprüft
            status, _h, data = self.get(best["url"], {"Accept": "application/vnd.github.raw"})
        except OSError as e:
            return self._failed(addon, best, now, f"Laden fehlgeschlagen ({e.__class__.__name__})")
        if status != 200:
            return self._failed(addon, best, now, f"Laden fehlgeschlagen (HTTP {status})")
        files, why = check_zip(data, addon, best["ver"], best.get("sha"))
        if files is None:
            # Prüfsumme kann kurz nach einem Push nicht passen (Liste und Datei aus verschiedenen Ständen) -> erneut versuchen
            return self._failed(addon, best, now, why, final="Prüfsumme" not in why)
        try:
            res = install(self.dir, addon, files)
        except OSError as e:
            return self._failed(addon, best, now, f"Schreiben nicht möglich ({e.__class__.__name__}: {e}) – Datei gesperrt "
                                                  f"oder kein Schreibrecht")
        self.fail.pop(addon, None)
        self.done.append(f"{addon} {best['ver']}")
        line = f"Addons: {addon} {have} -> {best['ver']} installiert ({len(res['written'])} Dateien geändert)"
        if res["new"] or res["toc"]:
            line += f" – NEUSTART des Spiels nötig (neue Dateien: {len(res['new'])})"
        else:
            line += " – im Spiel /reload"
        if res["kept"]:
            line += f". Nicht mehr in der neuen Version, bleibt liegen: {len(res['kept'])} Datei(en) ({', '.join(res['kept'][:5])}" \
                    f"{', …' if len(res['kept']) > 5 else ''})"
        return line + "."

    def _failed(self, addon: str, best: dict, now: float, why: str, final: bool = False) -> str | None:
        ver = best["ver"]
        prev = self.fail.get(addon)
        n = (prev[1] + 1) if prev and prev[0] == ver else 1
        if final:
            n = len(RETRY_MINUTES) + 1
        wait = RETRY_MINUTES[n - 1] * 60 if n <= len(RETRY_MINUTES) else 0
        self.fail[addon] = (ver, n, now + wait)
        if n > len(RETRY_MINUTES):
            return f"Addons: {addon} {ver} NICHT installiert – {why}. Kein weiterer Versuch bis zur nächsten Version bzw. zum " \
                   f"Neustart des Uploaders."
        return f"Addons: {addon} {ver} NICHT installiert – {why}. Neuer Versuch in {RETRY_MINUTES[n - 1]} Min. " \
               f"(Versuch {n} von {len(RETRY_MINUTES)})."


def forever_addons_dir(cfg: dict, roots: dict[str, str]) -> str | None:
    """Regel 5: "addons_pfad" aus uploader_config.json, sonst <_forever_>/Interface/AddOns des ersten Forever-Kontos."""
    p = cfg.get(PATH_KEY)
    if isinstance(p, str) and p.strip():
        return os.path.normpath(p.strip())
    for key in sorted(roots):
        if key.startswith("_forever_/"):
            flavor = os.path.dirname(os.path.dirname(os.path.dirname(roots[key])))   # …/_forever_/WTF/Account/<KONTO>
            return os.path.join(flavor, "Interface", "AddOns")
    return None
