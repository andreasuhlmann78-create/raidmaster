"""Addon-Daten für die Prüf-Sitzung in ein PRIVATES GitHub-Repo liefern – ab Uploader 2.3.0.

Auftrag: auftraege/RaidMaster/anweisung-uploader-daten-pruefung.txt (Entscheid des Nutzers 11.11.2026, mit den
Nachträgen 20:30 "bei jedem /reload" und 20:35 "kein endloser Datenschrott"); 2.3.1: offen-raidmaster.txt T-DU7–T-DU10.

DU1 Ziel: ein privates Repo des Nutzers (z. B. <Besitzer>/goldsentinel-daten). Zugang über einen Fine-grained-Token NUR
    für dieses Repo (Contents: Read and write). Repo und Token stehen in daten_config.json neben dem Uploader (geheim, nie
    im Log, nie im öffentlichen raidmaster-Repo). Meldet GitHub das Repo nicht als privat, wird nichts geliefert.
    Einrichten: Daten-Repo-einrichten.bat (fragt Repo und Token ab, prüft und schreibt daten_config.json).
    Testen: Daten-Verbindung-testen.bat (ab 2.3.1).
DU2 Was: nur die SavedVariables der GoldSentinel-Addons auf Kontoebene (AHSentinel zuerst, dann GuildSentinel,
    ProfessionSentinel, LevelPilot, ThreatSentinel, BuffSentinel, RaidMaster) aller Spielversionen. Keine fremden Addons,
    keine .bak, keine Config.wtf, keine Charakter-Ordner.
    Ab 2.3.1 (T-DU10): Ablage <rechner>/<spielversion>/<konto-xxxxxxxx>/<Datei>.lua. Jeder Rechner hat seinen eigenen
    Ordner und überschreibt nur den; die Konto-Kennung ist ein Prüfwert des Konto-Ordnernamens (auf jedem Rechner
    gleich, der Name selbst steht nie im Repo).
DU3 Wann: nach JEDEM Schreiben durch WoW (/reload, Ausloggen, Beenden): Änderung erkannt -> warten, bis Grösse und Zeit
    10 s stabil sind -> liefern. Höchstens 1 Commit je Minute (die letzte Fassung gewinnt). Nichts geändert -> nie ein
    Commit. Dateien über 50 MB werden übersprungen und einmal gemeldet.
DU4 Weg: GitHub-API (Git Data) mit urllib, keine Pflicht-Pakete. Fehler -> Meldung mit der ECHTEN Ursache (ab 2.3.1,
    T-DU9: Zertifikat, Namensauflösung, Zeitüberschreitung, Verbindung, ungültiger Token …; nie der Token), nichts kaputt,
    neuer Versuch bei der nächsten Änderung (spätestens nach 5 Min.).
    Zertifikate (T-DU9): Windows-Zertifikatsablage PLUS certifi. Fehlt certifi unter Windows, installiert der Uploader es
    einmal selbst ("py -m pip install --user certifi", Hinweis im Fenster). Keine Prüfung wird abgeschaltet.
DU5 Anzeige: "Prüfung: zuletzt geliefert 19:36 (3 Dateien) · Repo 12,3 MB".
DU6 Kein endloser Verlauf: Das Repo enthält immer nur
      aktuell/<rechner>/…            – den neuesten Stand je Rechner,
      tage/<JJJJ-MM-TT>/<rechner>/…  – höchstens 7 Tages-Stände (letzter Stand jedes Tages je Rechner),
      stand.json                     – je Rechner: Zeit und Dateien mit Grösse und Prüfwert.
    Jede Lieferung ersetzt den Zweig durch EINEN Commit ohne Vorgänger (Orphan-Commit + Force-Push), damit ältere
    Fassungen wirklich aus dem Repo verschwinden. Über 200 MB werden die ältesten Tages-Stände früher gelöscht.

Unabhängig vom Abgleich PC/Laptop (sync.py) und vom Daten-Upload an den Bot: Fehler hier stören die anderen nie.
Offline testbar: alle Netzaufrufe laufen über urllib.request.urlopen (im Test ersetzt).
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

DATEN_CONFIG = "daten_config.json"
API = "https://api.github.com"
ADDONS = ("AHSentinel", "GuildSentinel", "ProfessionSentinel", "LevelPilot", "ThreatSentinel", "BuffSentinel",
          "RaidMaster")
MAX_FILE = 50 * 1024 * 1024          # GitHub-Grenze 100 MB je Datei; darüber überspringen
STABLE_SECONDS = 10                  # Grösse/Zeit so lange unverändert -> WoW hat fertig geschrieben
MIN_GAP = 60                         # höchstens 1 Commit je Minute
RETRY_SECONDS = 300                  # nach einem Fehler spätestens dann neu (oder bei der nächsten Änderung)
DAYS_KEEP = 7
REPO_MAX = 200 * 1024 * 1024
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
TOKEN_RE = re.compile(r"^(github_pat_|ghp_)[A-Za-z0-9_]+$")
LIESMICH = ("# GoldSentinel-Daten (privat)\n\n"
            "Wird vom RaidMaster-Uploader geschrieben. Nur für die Prüf-Sitzung. Nicht von Hand ändern.\n\n"
            "- `aktuell/<rechner>/` – neuester Stand der Addon-Daten je Rechner (Spielversion, Konto-Kennung)\n"
            "- `tage/<Datum>/<rechner>/` – letzter Stand der letzten 7 Spieltage je Rechner\n"
            "- `stand.json` – je Rechner: Zeit und Dateien\n\n"
            "Die Konto-Kennung (konto-xxxxxxxx) ist auf allen Rechnern gleich; der Kontoname steht hier nie.\n"
            "Jede Lieferung ersetzt den Verlauf (ein einziger Commit) – ältere Fassungen gibt es hier nicht.\n")
QUOTES = str.maketrans({"„": '"', "“": '"', "”": '"', "«": '"', "»": '"', "‘": "'",
                        "’": "'"})


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def konto_id(account_folder: str) -> str:
    """Gleiche Kennung für dasselbe Konto auf jedem Rechner, ohne den Namen (T-DU10)."""
    return "konto-" + hashlib.sha256(account_folder.strip().lower().encode("utf-8")).hexdigest()[:8]


def path_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(name)).strip("._") or "rechner"


def fmt_time(t: float | None) -> str:
    return time.strftime("%d.%m. %H:%M", time.localtime(t)) if t else "–"


def fmt_mb(n: int) -> str:
    return f"{n / 1024 / 1024:.1f}".replace(".", ",") + " MB"


def token_problem(token: str) -> str | None:
    """T-DU7: Token vor jedem Aufruf prüfen. None = Form stimmt."""
    if not token:
        return "token fehlt"
    if any(ord(c) < 32 for c in token):
        return ("Token enthält ungültige Zeichen (Strg+V eingefügt?) – mit RECHTSKLICK einfügen, Eingabe bleibt "
                "unsichtbar")
    if not TOKEN_RE.match(token):
        return ("Token hat nicht die erwartete Form (beginnt mit github_pat_ oder ghp_, nur Buchstaben, Ziffern, _) – "
                "vollständig kopiert?")
    return None


# ---------------------------------------------------------------------------
# daten_config.json (T-DU8)
# ---------------------------------------------------------------------------
def read_config(here: str) -> tuple[dict | None, str | None]:
    """(Konfiguration, None) oder (None, Grund). Grund None + Konfiguration None = Datei fehlt (freiwillig).
    Liest auch Dateien mit BOM (Windows-Editor) und ersetzt typografische Anführungszeichen. Nie den Token melden."""
    path = os.path.join(here, DATEN_CONFIG)
    if not os.path.exists(path):
        return None, None
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        return None, f"{DATEN_CONFIG} nicht lesbar ({type(e).__name__})"
    try:
        conf = json.loads(text.translate(QUOTES))
    except ValueError as e:
        line = getattr(e, "lineno", "?")
        return None, f"{DATEN_CONFIG} nicht lesbar (Zeile {line}: kein gültiges JSON)"
    if not isinstance(conf, dict):
        return None, f"{DATEN_CONFIG} nicht lesbar (erwartet {{\"repo\": …, \"token\": …}})"
    repo, token = str(conf.get("repo") or "").strip(), str(conf.get("token") or "").strip()
    if not repo:
        return None, "repo fehlt in " + DATEN_CONFIG
    if not REPO_RE.match(repo):
        return None, "repo falsch in " + DATEN_CONFIG + " (Form: Besitzer/Name)"
    problem = token_problem(token)
    if problem:
        return None, problem + " (" + DATEN_CONFIG + ")"
    return {"repo": repo, "token": token}, None


def load_config(here: str) -> dict | None:
    return read_config(here)[0]


def save_config(here: str, repo: str, token: str):
    path = os.path.join(here, DATEN_CONFIG)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"repo": repo, "token": token}, f, indent=2)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Zertifikate (T-DU9)
# ---------------------------------------------------------------------------
_CERTIFI_TRIED = {"done": False}


def certifi_file() -> str | None:
    try:
        import certifi  # type: ignore
        return certifi.where()
    except Exception:  # noqa: BLE001
        return None


def ssl_context() -> ssl.SSLContext:
    """Windows-/System-Zertifikatsablage PLUS certifi (falls vorhanden). Prüfung bleibt immer an."""
    ctx = ssl.create_default_context()
    extra = certifi_file()
    if extra:
        try:
            ctx.load_verify_locations(cafile=extra)
        except (OSError, ssl.SSLError):
            pass
    return ctx


def ensure_certifi(log, run=subprocess.run, background: bool = True) -> bool | None:
    """Windows: fehlt certifi, einmal "python -m pip install --user certifi" (gleiches Python wie der Uploader).
    True = vorhanden/installiert, False = ging nicht, None = läuft im Hintergrund."""
    if certifi_file():
        return True
    if _CERTIFI_TRIED["done"]:
        return False
    _CERTIFI_TRIED["done"] = True

    def work():
        log("Prüfung: installiere die Zertifikate für GitHub (certifi) – einmalig ...")
        try:
            res = run([sys.executable, "-m", "pip", "install", "--user", "--disable-pip-version-check", "-q",
                       "certifi"], capture_output=True, text=True, timeout=300,
                      creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            ok = getattr(res, "returncode", 1) == 0
        except Exception:  # noqa: BLE001
            ok = False
        if ok:
            import importlib
            import site
            try:
                site.addsitedir(site.getusersitepackages())
            except Exception:  # noqa: BLE001
                pass
            importlib.invalidate_caches()
        if ok and certifi_file():
            log("Prüfung: Zertifikate installiert (certifi).")
            return True
        log("Prüfung: certifi liess sich nicht installieren – von Hand: py -m pip install certifi")
        return False
    if background:
        threading.Thread(target=work, daemon=True).start()
        return None
    return work()


def describe_error(e: BaseException) -> str:
    """T-DU9: die echte Ursache verständlich, ohne Token."""
    reason = getattr(e, "reason", e)
    text = f"{type(reason).__name__}: {reason}"
    low = text.lower()
    if isinstance(reason, ssl.SSLCertVerificationError) or "certificate_verify_failed" in low:
        return ("Zertifikat für GitHub fehlt in Windows (CERTIFICATE_VERIFY_FAILED) – der Uploader installiert "
                "certifi selbst; sonst von Hand: py -m pip install certifi, dann Uploader neu starten")
    if isinstance(reason, ssl.SSLError):
        return f"SSL-Fehler bei GitHub ({getattr(reason, 'reason', None) or type(reason).__name__})"
    if isinstance(reason, socket.gaierror) or "getaddrinfo" in low or "name or service not known" in low:
        return "api.github.com nicht auflösbar (kein Netz oder DNS-Problem)"
    if isinstance(reason, (socket.timeout, TimeoutError)) or "timed out" in low:
        return "GitHub antwortet nicht (Zeitüberschreitung)"
    if isinstance(reason, ConnectionRefusedError):
        return "Verbindung zu GitHub abgelehnt (Firewall oder Proxy?)"
    if isinstance(reason, (ConnectionResetError, ConnectionAbortedError)):
        return "Verbindung zu GitHub abgebrochen (Firewall, Virenschutz oder Proxy?)"
    if isinstance(e, ValueError) and "header" in low:
        return "Token enthält ungültige Zeichen – mit RECHTSKLICK einfügen (nicht Strg+V)"
    short = re.sub(r"(github_pat_|ghp_)[A-Za-z0-9_]+", "***", text)[:160]
    return f"Netzfehler: {short}"


class GitHubError(Exception):
    pass


class GitHubAPI:
    """Nur die paar Aufrufe, die die Lieferung braucht. Der Token steht nie in einer Meldung."""

    def __init__(self, repo: str, token: str, timeout: int = 180):
        self.repo, self._token, self.timeout = repo, token, timeout
        self._ctx = None

    def _req(self, method: str, path: str, body: dict | None = None, ok404: bool = False):
        problem = token_problem(self._token)
        if problem:
            raise GitHubError(problem)
        if self._ctx is None:
            self._ctx = ssl_context()
        req = urllib.request.Request(API + path, method=method,
                                     data=json.dumps(body).encode("utf-8") if body is not None else None)
        req.add_header("Authorization", "Bearer " + self._token)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "GoldSentinel-Uploader")
        if body is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as resp:
                raw = resp.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except urllib.error.HTTPError as e:
            code = e.code
            remaining = str((getattr(e, "headers", None) or {}).get("X-RateLimit-Remaining") or "")
            if ok404 and code in (404, 409):
                return None
            if code == 401:
                raise GitHubError("Token falsch oder abgelaufen – Daten-Repo-einrichten.bat erneut ausführen") from None
            if code in (403, 429) and remaining == "0":
                raise GitHubError("GitHub-Grenze erreicht – später erneut") from None
            if code in (403, 404):
                raise GitHubError(f"kein Zugriff auf {self.repo} (Token nur für dieses Repo, Contents: Read and "
                                  "write)") from None
            if code == 409:
                raise GitHubError("Repo ist leer") from None
            raise GitHubError(f"GitHub antwortet {code}") from None
        except (urllib.error.URLError, OSError, ValueError, ssl.SSLError) as e:
            if "certificate_verify_failed" in str(getattr(e, "reason", e)).lower():
                self._ctx = None                       # nach einer certifi-Installation neu aufbauen
            raise GitHubError(describe_error(e)) from None

    def repo_info(self) -> dict:
        return self._req("GET", f"/repos/{self.repo}") or {}

    def head(self, branch: str) -> str | None:
        ref = self._req("GET", f"/repos/{self.repo}/git/ref/heads/{branch}", ok404=True)
        return ((ref or {}).get("object") or {}).get("sha")

    def init_empty(self, branch: str):
        """Leeres Repo: Git-Data-API geht erst, wenn es einen ersten Commit gibt."""
        self._req("PUT", f"/repos/{self.repo}/contents/LIESMICH.md",
                  {"message": "Daten-Repo eingerichtet", "branch": branch,
                   "content": base64.b64encode(LIESMICH.encode("utf-8")).decode("ascii")})

    def tree(self, commit_sha: str) -> list[dict]:
        commit = self._req("GET", f"/repos/{self.repo}/git/commits/{commit_sha}") or {}
        tsha = (commit.get("tree") or {}).get("sha")
        if not tsha:
            return []
        tree = self._req("GET", f"/repos/{self.repo}/git/trees/{tsha}?recursive=1") or {}
        return [e for e in tree.get("tree") or [] if e.get("type") == "blob"]

    def blob_text(self, sha: str) -> bytes:
        res = self._req("GET", f"/repos/{self.repo}/git/blobs/{sha}") or {}
        try:
            return base64.b64decode(res.get("content") or "")
        except ValueError:
            return b""

    def blob(self, data: bytes) -> str:
        res = self._req("POST", f"/repos/{self.repo}/git/blobs",
                        {"content": base64.b64encode(data).decode("ascii"), "encoding": "base64"}) or {}
        return str(res.get("sha") or "")

    def make_tree(self, entries: dict[str, str]) -> str:
        body = {"tree": [{"path": p, "mode": "100644", "type": "blob", "sha": s} for p, s in sorted(entries.items())]}
        return str((self._req("POST", f"/repos/{self.repo}/git/trees", body) or {}).get("sha") or "")

    def commit(self, message: str, tree: str) -> str:
        res = self._req("POST", f"/repos/{self.repo}/git/commits", {"message": message, "tree": tree, "parents": []})
        return str((res or {}).get("sha") or "")

    def set_ref(self, branch: str, sha: str):
        self._req("PATCH", f"/repos/{self.repo}/git/refs/heads/{branch}", {"sha": sha, "force": True})


def test_connection(conf: dict, log=print) -> bool:
    """Daten-Verbindung-testen.bat (T-DU9 c): GET /repos/<repo>, Ergebnis verständlich."""
    api = GitHubAPI(conf["repo"], conf["token"], timeout=60)
    try:
        info = api.repo_info()
    except GitHubError as e:
        log(f"Verbindung zu {conf['repo']}: FEHLER – {e}")
        return False
    if info.get("private") is not True:
        log(f"Verbindung zu {conf['repo']}: erreichbar, aber NICHT privat – der Uploader liefert nichts.")
        return False
    log(f"Verbindung zu {conf['repo']}: OK (privat, Zugriff vorhanden).")
    return True


class Daten:
    """Lieferung an das private Daten-Repo. Zustand in st["daten"] (uploader_state.json)."""

    def __init__(self, api: GitHubAPI, roots: dict[str, str], st: dict, save, machine: str, log):
        self.api, self.roots, self.save, self.log = api, dict(roots), save, log
        self.me = machine
        self.folder = path_name(machine)
        d = st.setdefault("daten", {})
        self.d = d
        self.sig = None
        self.changed_at = 0.0
        self.retry_at = 0.0
        self.last_error = ""
        self.warned_big: set[str] = set()

    # -- welche Dateien (DU2, T-DU10)
    def files(self) -> dict[str, str]:
        """rel. Pfad unterhalb des Rechner-Ordners -> voller Pfad."""
        out = {}
        for key, acc in sorted(self.roots.items()):
            flavor = (key.split("/")[0] if key else "wow").strip("_") or "wow"
            konto = konto_id(os.path.basename(os.path.normpath(acc)))
            for addon in ADDONS:
                fn = os.path.join(acc, "SavedVariables", addon + ".lua")
                if os.path.isfile(fn):
                    out[f"{flavor}/{konto}/{addon}.lua"] = fn
        return out

    @staticmethod
    def signature(files: dict[str, str]) -> list:
        sig = []
        for rel, fn in sorted(files.items()):
            try:
                stt = os.stat(fn)
                sig.append([rel, stt.st_size, stt.st_mtime])
            except OSError:
                continue
        return sig

    # -- Anzeige (DU5)
    def status_line(self) -> str:
        if self.d.get("last"):
            line = (f"Prüfung: zuletzt geliefert {fmt_time(self.d['last'])} ({self.d.get('n', 0)} Dateien)"
                    f" · Repo {fmt_mb(int(self.d.get('size') or 0))}")
        else:
            line = "Prüfung: noch nichts geliefert"
        if self.last_error:
            line += f" · FEHLER: {self.last_error}"
        return line

    # -- regelmässig (alle paar Sekunden aus der Hauptschleife)
    def tick(self, now: float | None = None) -> bool | None:
        now = time.time() if now is None else now
        files = self.files()
        sig = self.signature(files)
        if sig != self.sig:
            if self.sig is not None:
                self.retry_at = 0.0                  # neue Änderung = neuer Auslöser
            self.sig, self.changed_at = sig, now
            return None
        if sig == self.d.get("sig_done") or not sig:
            return None
        if now - self.changed_at < STABLE_SECONDS or now < self.retry_at:
            return None
        if now - float(self.d.get("last_try") or 0) < MIN_GAP:
            return None
        return self.deliver(now, files, sig)

    def _read_files(self, files: dict[str, str]) -> dict[str, tuple[bytes, str]]:
        cur: dict[str, tuple[bytes, str]] = {}
        for rel, fn in files.items():
            try:
                size = os.path.getsize(fn)
                if size > MAX_FILE:
                    if f"{rel}:{size}" not in self.warned_big:
                        self.warned_big.add(f"{rel}:{size}")
                        self.log(f"Prüfung: {rel.split('/')[-1]} ist {fmt_mb(size)} gross (über "
                                 f"{fmt_mb(MAX_FILE)}) – übersprungen.")
                    continue
                with open(fn, "rb") as f:
                    data = f.read()
            except OSError:
                continue
            cur[rel] = (data, git_blob_sha(data))
        return cur

    def _build(self, now: float, old: dict[str, dict], cur: dict[str, tuple[bytes, str]], stand_old: dict):
        """Neuer Baum: eigener Rechner neu, andere Rechner unverändert, 7 Tage, höchstens 200 MB."""
        me = self.folder
        today = time.strftime("%Y-%m-%d", time.localtime(now))
        entries: dict[str, str] = {}
        sizes: dict[str, int] = {}
        for rel, (data, s) in cur.items():
            entries[f"aktuell/{me}/{rel}"] = s
            entries[f"tage/{today}/{me}/{rel}"] = s
            sizes[s] = len(data)
        # andere Rechner (Form 2.3.1: aktuell/<rechner>/<spielversion>/<konto>/<Datei>)
        for p, e in old.items():
            parts = p.split("/")
            if parts[0] == "aktuell" and len(parts) == 5 and parts[1] != me:
                entries[p] = e["sha"]
                sizes.setdefault(e["sha"], int(e.get("size") or 0))
        days = sorted({p.split("/")[1] for p in old if p.startswith("tage/") and len(p.split("/")) == 6})
        keep = [d for d in days if d != today][-(DAYS_KEEP - 1):] if DAYS_KEEP > 1 else []
        for p, e in old.items():
            parts = p.split("/")
            if parts[0] != "tage" or len(parts) != 6:
                continue                              # Form von 2.3.0 fällt weg
            if parts[1] in keep or (parts[1] == today and parts[2] != me):
                entries[p] = e["sha"]
                sizes.setdefault(e["sha"], int(e.get("size") or 0))
        dropped = []
        while sum(sizes.get(s, 0) for s in set(entries.values())) > REPO_MAX and keep:
            gone = keep.pop(0)
            dropped.append(gone)
            entries = {p: s for p, s in entries.items() if not p.startswith(f"tage/{gone}/")}
        stand = {k: v for k, v in stand_old.items() if isinstance(v, dict) and k != me
                 and any(p.startswith(f"aktuell/{k}/") for p in entries)}
        stand[me] = {"zeit": int(now), "dateien": {rel: {"bytes": len(d), "sha": s} for rel, (d, s) in cur.items()}}
        extra = {"LIESMICH.md": LIESMICH.encode("utf-8"),
                 "stand.json": json.dumps(stand, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8")}
        for p, data in extra.items():
            entries[p] = git_blob_sha(data)
            sizes[entries[p]] = len(data)
        return entries, sizes, extra, dropped

    def deliver(self, now: float, files: dict[str, str], sig: list) -> bool:
        self.d["last_try"] = now
        try:
            info = self.api.repo_info()
            if info.get("private") is not True:
                raise GitHubError(f"{self.api.repo} ist nicht privat – aus Sicherheitsgründen nichts geliefert")
            branch = str(info.get("default_branch") or "main")
            cur = self._read_files(files)
            for attempt in range(2):
                head = self.api.head(branch)
                if head is None:
                    self.api.init_empty(branch)
                    head = self.api.head(branch)
                old = {e["path"]: e for e in self.api.tree(head)} if head else {}
                mine = {p: e.get("sha") for p, e in old.items() if p.startswith(f"aktuell/{self.folder}/")}
                if mine == {f"aktuell/{self.folder}/{rel}": s for rel, (_, s) in cur.items()}:
                    self.d["sig_done"] = sig                 # nichts geändert -> nie ein Commit
                    self.last_error = ""
                    self.save()
                    return True
                stand_old = {}
                if "stand.json" in old:
                    try:
                        stand_old = json.loads(self.api.blob_text(old["stand.json"]["sha"]).decode("utf-8"))
                    except (ValueError, UnicodeDecodeError):
                        stand_old = {}
                entries, sizes, extra, dropped = self._build(now, old, cur, stand_old)
                have = {e.get("sha") for e in old.values()}
                blobs = {s: d for d, s in cur.values()}
                blobs.update({git_blob_sha(d): d for d in extra.values()})
                order = sorted(blobs, key=lambda s: 0 if any(s == cs and r.endswith("/AHSentinel.lua")
                                                              for r, (_, cs) in cur.items()) else 1)
                for s in order:                              # AHSentinel zuerst
                    if s in have:
                        continue
                    if self.api.blob(blobs[s]) != s:
                        raise GitHubError("GitHub hat eine Datei nicht richtig angenommen")
                tree = self.api.make_tree(entries)
                commit = self.api.commit(f"Daten {self.me} {fmt_time(now)}", tree)
                if not tree or not commit:
                    raise GitHubError("GitHub hat den Stand nicht bestätigt")
                # hat der andere Rechner inzwischen geliefert? Dann seinen Stand einbeziehen (einmal neu)
                if attempt == 0 and self.api.head(branch) != head:
                    continue
                self.api.set_ref(branch, commit)
                break
        except GitHubError as e:
            self.last_error = str(e)
            self.retry_at = now + RETRY_SECONDS
            self.log(f"Prüfung: {e} – nichts geliefert, neuer Versuch bei der nächsten Änderung.")
            if "certifi" in str(e) and sys.platform == "win32":
                ensure_certifi(self.log)
            return False
        total = sum(sizes.get(s, 0) for s in set(entries.values()))
        self.last_error = ""
        self.d.update({"last": now, "n": len(cur), "sig_done": sig, "size": total})
        self.save()
        if dropped:
            self.log(f"Prüfung: Repo über {fmt_mb(REPO_MAX)} – ältere Tages-Stände gelöscht ({', '.join(dropped)}).")
        self.log(f"Prüfung: geliefert ({len(cur)} Dateien, Repo {fmt_mb(total)}).")
        return True


def read_secret(prompt: str) -> str:
    """Token-Eingabe (T-DU7/T-DU8 d): unter Windows mit Sternchen; Rechtsklick UND Strg+V fügen ein."""
    if sys.platform != "win32":
        import getpass
        return getpass.getpass(prompt)
    import msvcrt
    sys.stdout.write(prompt)
    sys.stdout.flush()
    chars: list[str] = []
    while True:
        c = msvcrt.getwch()
        if c in ("\r", "\n"):
            sys.stdout.write("\n")
            return "".join(chars)
        if c == "\x03":
            raise KeyboardInterrupt
        if c == "\x08":
            if chars:
                chars.pop()
                sys.stdout.write("\b \b")
        elif c == "\x16":                                   # Strg+V: Zwischenablage über PowerShell
            try:
                clip = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard"], capture_output=True,
                                      text=True, timeout=10,
                                      creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout.strip()
            except Exception:  # noqa: BLE001
                clip = ""
            chars.extend(clip)
            sys.stdout.write("*" * len(clip))
        elif c in ("\x00", "\xe0"):
            msvcrt.getwch()                                  # Pfeiltasten u. ä. überspringen
        elif ord(c) >= 32:
            chars.append(c)
            sys.stdout.write("*")
        sys.stdout.flush()


def setup_interactive(here: str, ask=input, ask_secret=None, log=print) -> bool:
    """Daten-Repo-einrichten.bat: Repo und Token abfragen, prüfen (Form, privat, Zugriff), daten_config.json schreiben."""
    ask_secret = ask_secret or read_secret
    log("Daten für die Prüf-Sitzung – einmal einrichten")
    log("Vorher auf github.com: ein PRIVATES Repo anlegen (z. B. goldsentinel-daten) und einen Fine-grained-Token NUR")
    log("für dieses Repo mit 'Contents: Read and write' (Anleitung in LIESMICH.txt).")
    repo = ask("Repo (Besitzer/Name, z. B. meinname/goldsentinel-daten): ").strip()
    if not REPO_RE.match(repo):
        log("Das ist kein Repo-Name in der Form Besitzer/Name – nichts gespeichert.")
        return False
    token = ask_secret("Token einfügen (Rechtsklick oder Strg+V, Enter; es erscheinen nur Sternchen): ").strip()
    problem = token_problem(token)
    if problem:
        log(f"{problem} – nichts gespeichert.")
        return False
    api = GitHubAPI(repo, token, timeout=60)
    try:
        info = api.repo_info()
    except GitHubError as e:
        if "certifi" in str(e) and sys.platform == "win32" and ensure_certifi(log, background=False):
            try:
                info = GitHubAPI(repo, token, timeout=60).repo_info()
            except GitHubError as e2:
                log(f"Prüfung fehlgeschlagen: {e2} – nichts gespeichert.")
                return False
        else:
            log(f"Prüfung fehlgeschlagen: {e} – nichts gespeichert.")
            return False
    if info.get("private") is not True:
        log(f"{repo} ist NICHT privat – aus Sicherheitsgründen nichts gespeichert. Repo auf privat stellen.")
        return False
    save_config(here, repo, token)
    log(f"Gespeichert in {DATEN_CONFIG}. Der Uploader liefert ab jetzt nach jedem /reload und Ausloggen.")
    log(f"Bitte der Prüf-Sitzung den Repo-Namen melden: {repo}")
    return True
