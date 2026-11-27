"""Addon-Daten für die Prüf-Sitzung in ein PRIVATES GitHub-Repo liefern – ab Uploader 2.3.0.

Auftrag: auftraege/RaidMaster/anweisung-uploader-daten-pruefung.txt (Entscheid des Nutzers 11.11.2026, mit den
Nachträgen 20:30 "bei jedem /reload" und 20:35 "kein endloser Datenschrott"); 2.3.1: offen-raidmaster.txt T-DU7–T-DU10;
2.3.2: U1 (gleichzeitige Lieferung zweier Rechner geht nie verloren).

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

UP-ALT (ab 2.3.20, Entscheid des Nutzers 24.11.2026 07:22 "wenn jemand nicht die neuste version drauf hatt die daten nicht
    mehr annehmen!"):
    (1) Gültiger Stand ist der Zweig "sicherung". Ihn schreibt nur ein Uploader ab 2.3.20, und zwar ZUERST (dann main).
        Alle Uploader bis 2.3.19 schreiben nur den Standardzweig (main) – belegt an allen 11 Fassungen von daten.py.
        Ein Uploader ab 2.3.20 baut immer auf "sicherung" auf; eine Lieferung eines alten Uploaders auf main wird nie
        übernommen. Wächter: alle 5 Min. main mit "sicherung" vergleichen, weicht main ab -> main auf "sicherung"
        zurückstellen (nur der Zeiger, kein neuer Commit). Gibt es "sicherung" noch nicht, legt sie der erste aktuelle
        Uploader auf den Stand von main an.
    (2) Neueste Version = VERSION in RaidMasterUploader/uploader.py im öffentlichen raidmaster-Repo (dieselbe Quelle wie der
        Bot, steigt mit jeder Version von selbst), höchstens alle 10 Min. gelesen. Ist der eigene Uploader älter, liefert er
        nichts (auch "sicherung" nicht) und sagt es im Fenster. Nicht lesbar -> zuletzt gelesene Version, sonst die eigene.
    (3) Meldung im Fenster: "Daten nicht angenommen – Uploader x.y.z ist veraltet (neueste a.b.c), bitte /uploader holen."
UP-MIN1 (ab 2.3.23, Entscheid des Nutzers 24.11.2026 21:18 "umsetzten" auf den Vorschlag des Supervisors 21:17): statt "neueste"
    gilt eine MINDESTVERSION – eine Stelle im Repo: RaidMasterUploader/mindestversion.txt (öffentlich, ohne Token gelesen, höchstens
    alle 10 Min.). Sie wird nur erhöht, wenn sich Daten, Format, Prüfung oder Sicherheit ändern (Begründung im LIESMICH und Bericht),
    nie für reine Text-/Anzeige-Änderungen. Unter der Mindestversion: nichts liefern, Meldung "… ist zu alt (Mindestversion x) …".
    Darüber, aber nicht die neueste: liefern wie immer, einmal die Information "neuere Uploader-Version a.b.c verfügbar".
    Nicht lesbar -> zuletzt gelesene, sonst MIN_BUILTIN (Stand beim Bau). Uploader 2.3.20–2.3.22 prüfen noch gegen "neueste" (lässt
    sich bei ihnen nicht mehr ändern) – sie liefern erst wieder ab 2.3.23.

DS1 Datenschutz (ab 2.3.13, Entscheid des Nutzers 16.11.2026 07:10): In GuildSentinel.lua werden vor dem Hochladen die
    Bewerber (apps) und die Sperrliste (ban) jeder Gilde geleert (svfilter.py). Nur die hochgeladene Kopie; die Datei im
    Spiel bleibt unverändert. Kann die Datei nicht sicher gelesen werden, wird sie NICHT geliefert (nie ungefiltert).

Unabhängig vom Abgleich PC/Laptop (sync.py) und vom Daten-Upload an den Bot: Fehler hier stören die anderen nie.
Offline testbar: alle Netzaufrufe laufen über urllib.request.urlopen (im Test ersetzt).
"""
from __future__ import annotations

import base64
import gzip
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

try:
    import svfilter
except ImportError:                      # Start aus einem anderen Ordner
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import svfilter
    except ImportError:                  # svfilter.py fehlt (nur einzelne Dateien ersetzt) -> GuildSentinel.lua nie liefern
        svfilter = None

DATEN_CONFIG = "daten_config.json"
API = "https://api.github.com"
ADDONS = ("AHSentinel", "GuildSentinel", "ProfessionSentinel", "LevelPilot", "ThreatSentinel", "BuffSentinel",
          "RaidMaster")
MAX_FILE = 50 * 1024 * 1024          # gepackt je Datei (GitHub lehnt grosse Dateien ab); darüber überspringen
MAX_RAW = 400 * 1024 * 1024          # UP-TAGE (2.3.19): ungepackt höchstens so viel einlesen (Speicher)
STABLE_SECONDS = 10                  # Grösse/Zeit so lange unverändert -> WoW hat fertig geschrieben
MIN_GAP = 60                         # höchstens 1 Commit je Minute
RETRY_SECONDS = 300                  # nach einem Fehler spätestens dann neu (oder bei der nächsten Änderung)
DAYS_KEEP = 30                        # UP-TAGE (Entscheid des Nutzers 24.11. 06:26): 30 Tage, alles gepackt, 1 GB
REPO_MAX = 1024 * 1024 * 1024        # Summe der (gepackten) Dateien im Daten-Repo
KEEP_OLD_RETRY = 1800                # UP-TAGE: lehnt GitHub eine eigene Datei ab -> spätestens nach 30 Min. neu versuchen
SAFE_BRANCH = "sicherung"            # UP-ALT (2.3.20): gültiger Stand, schreibt nur ein Uploader ab 2.3.20
WATCH_SECONDS = 300                  # UP-ALT: so oft main mit "sicherung" vergleichen
LATEST_SECONDS = 600                 # UP-ALT: so oft die neueste veröffentlichte Version lesen
LATEST_URL = ("https://raw.githubusercontent.com/andreasuhlmann78-create/raidmaster/HEAD/"
              "RaidMasterUploader/uploader.py")   # öffentlich, ohne Token; dieselbe Quelle wie der Bot
MIN_URL = ("https://raw.githubusercontent.com/andreasuhlmann78-create/raidmaster/HEAD/"
           "RaidMasterUploader/mindestversion.txt")      # UP-MIN1: die eine Stelle der Mindestversion
MIN_BUILTIN = "2.3.20"                # UP-MIN1: Mindestversion beim Bau dieser Version (nur Notfall, wenn nie gelesen)
MIN_RE = re.compile(r"^\s*(\d+(?:\.\d+){1,3})\s*$", re.M)
VERSION_RE = re.compile(r'^VERSION\s*=\s*["\'](\d+(?:\.\d+){1,3})["\']', re.M)
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
TOKEN_RE = re.compile(r"^(github_pat_|ghp_)[A-Za-z0-9_]+$")
LIESMICH = ("# GoldSentinel-Daten (privat)\n\n"
            "Wird vom RaidMaster-Uploader geschrieben. Nur für die Prüf-Sitzung. Nicht von Hand ändern.\n\n"
            "- `aktuell/<rechner>/` – neuester Stand der Addon-Daten je Rechner (Spielversion, Konto-Kennung)\n"
            "- `tage/<Datum>/<rechner>/` – letzter Stand je Spieltag und Rechner, die letzten 30 Tage (höchstens 1 GB)\n"
            "- `stand.json` – je Rechner: Zeit, Dateien, Uploader-Version, Tage\n\n"
            "Die Konto-Kennung (konto-xxxxxxxx) ist auf allen Rechnern gleich; der Kontoname steht hier nie.\n"
            "Ab Uploader 2.3.19 liegt jede Datei gepackt als `<Datei>.lua.gz` da (gzip, z. B. `gzip.open(pfad, 'rt')`); "
            "ältere Stände anderer Rechner und Tage können noch ungepackt (`.lua`) sein – Leser nehmen beides.\n"
            "Jede Lieferung ersetzt den Verlauf (ein einziger Commit) – ältere Fassungen gibt es hier nicht.\n\n"
            "Ab Uploader 2.3.20 gilt der Zweig `sicherung` (schreibt nur ein aktueller Uploader). `main` ist nur eine Kopie und "
            "kann kurz eine nicht angenommene Lieferung eines alten Uploaders zeigen. Leser nehmen `sicherung` und nur Rechner, "
            "deren `uploader` in `stand.json` mindestens die Mindestversion ist (RaidMasterUploader/mindestversion.txt im "
            "raidmaster-Repo, ab Uploader 2.3.23).\n")
QUOTES = str.maketrans({"„": '"', "“": '"', "”": '"', "«": '"', "»": '"', "‘": "'",
                        "’": "'"})


def version_key(v) -> tuple:
    try:
        return tuple(int(p) for p in str(v).split("."))
    except ValueError:
        return ()


def is_older(have, want) -> bool:
    """UP-ALT: ist "have" älter als "want"? Unbekannte eigene Version gilt als älter, unbekannte neueste nie."""
    return bool(version_key(want)) and version_key(have) < version_key(want)


def fetch_latest_version(timeout: int = 30) -> str | None:
    """UP-ALT (2): VERSION des veröffentlichten Uploaders (raidmaster-Repo, öffentlich, ohne Token). None bei jedem Fehler."""
    req = urllib.request.Request(LATEST_URL, headers={"User-Agent": "GoldSentinel-Uploader", "Range": "bytes=0-16383"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
            text = resp.read().decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 – nie abstürzen; dann gilt die zuletzt gelesene Version
        return None
    m = VERSION_RE.search(text)
    return m.group(1) if m else None


def fetch_min_version(timeout: int = 30) -> str | None:
    """UP-MIN1: erste Zeile mit einer Versionsnummer in mindestversion.txt (Zeilen mit # sind Erklärung). None bei jedem Fehler."""
    req = urllib.request.Request(MIN_URL, headers={"User-Agent": "GoldSentinel-Uploader"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
            text = resp.read(16384).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 – nie abstürzen; dann gilt die zuletzt gelesene Mindestversion
        return None
    return parse_min(text)


def parse_min(text: str) -> str | None:
    for line in str(text or "").splitlines():
        if line.strip().startswith("#") or not line.strip():
            continue
        m = MIN_RE.match(line)
        return m.group(1) if m else None
    return None


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
    """code = HTTP-Status (oder None), call = welcher Aufruf (Datei/Baum/Stand/Zweig/Abfrage), detail = Text von GitHub."""

    def __init__(self, text: str, code: int | None = None, call: str = "", detail: str = ""):
        super().__init__(text)
        self.code, self.call, self.detail = code, call, detail


def _call_name(method: str, path: str) -> str:
    """UP-422 (2): welcher Aufruf – für die Meldung im Fenster."""
    if "/git/blobs" in path:
        return "Datei anlegen" if method == "POST" else "Datei lesen"
    if "/git/trees" in path:
        return "Baum anlegen" if method == "POST" else "Baum lesen"
    if "/git/commits" in path:
        return "Stand anlegen" if method == "POST" else "Stand lesen"
    if "/git/ref" in path:
        return {"PATCH": "Zweig setzen", "POST": "Zweig anlegen"}.get(method, "Zweig lesen")
    return "Abfrage"


def github_detail(raw: bytes, token: str = "") -> str:
    """UP-422 (2): Meldungstext aus der Fehlerantwort von GitHub ("message" + "errors"), ohne Token, höchstens 200 Zeichen."""
    try:
        res = json.loads((raw or b"").decode("utf-8", "replace"))
    except ValueError:
        res = {}
    parts = []
    if isinstance(res, dict):
        if res.get("message"):
            parts.append(str(res["message"]))
        for e in res.get("errors") or []:
            if isinstance(e, dict):
                parts.append(" ".join(str(e.get(k)) for k in ("resource", "field", "code", "message") if e.get(k)))
            else:
                parts.append(str(e))
    text = " – ".join(p for p in parts if p)
    if token:
        text = text.replace(token, "***")
    text = re.sub(r"(github_pat_|ghp_)[A-Za-z0-9_]+", "***", text)
    return re.sub(r"\s+", " ", text).strip()[:200]


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
            try:
                detail = github_detail(e.read(), self._token)
            except Exception:  # noqa: BLE001
                detail = ""
            call = _call_name(method, path)
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
            # UP-422 (2): Status, Aufruf und Text von GitHub (ohne Token) – statt nur "GitHub antwortet 422"
            raise GitHubError(f"GitHub antwortet {code} ({call}" + (f": {detail}" if detail else "") + ")",
                              code=code, call=call, detail=detail) from None
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

    def create_ref(self, branch: str, sha: str) -> bool:
        """UP-ALT: Zweig neu anlegen. False, wenn es ihn schon gibt (ein anderer Rechner war schneller)."""
        try:
            self._req("POST", f"/repos/{self.repo}/git/refs", {"ref": f"refs/heads/{branch}", "sha": sha})
        except GitHubError as e:
            if e.code == 422:
                return False
            raise
        return True


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

    def __init__(self, api: GitHubAPI, roots: dict[str, str], st: dict, save, machine: str, log, version: str = ""):
        self.api, self.roots, self.save, self.log = api, dict(roots), save, log
        self.version = str(version or "")             # UP-DS2 (1): steht je Rechner in stand.json ("uploader")
        self.me = machine
        self.folder = path_name(machine)
        d = st.setdefault("daten", {})
        self.d = d
        self.sig = None
        self.changed_at = 0.0
        self.retry_at = 0.0
        self.last_error = ""
        self.warned_big: set[str] = set()
        self.warned_filter: set[str] = set()       # DS1: "nicht geliefert" je Datei-Stand nur einmal melden
        self.warned_old = None                     # UP-DS2 (3): Hinweis "anderer Rechner mit altem Uploader" je Anzahl einmal
        self._too_big: set[str] = set()
        self.legacy = False                        # nur Tests: Verhalten bis 2.3.19 (kein "sicherung", keine Mindestversion)
        self.latest_fetch = fetch_latest_version   # UP-ALT (2), im Test ersetzbar – ab 2.3.23 nur noch Information
        self.min_fetch = fetch_min_version         # UP-MIN1, im Test ersetzbar
        self.min_at = -1e18
        self._latest = ""
        self.told_newer = ""                       # UP-MIN1: Information "neuere Version" je Version einmal
        self.latest_at = -1e18                     # wann zuletzt gelesen (Prozess)
        self.watch_at = -1e18                      # UP-ALT (1): wann zuletzt main mit "sicherung" verglichen
        self.warned_outdated = ""                  # UP-ALT (3): Meldung je Versionspaar einmal
        self.warned_restore: set[str] = set()      # UP-ALT: Rückstellung je fremdem Commit einmal melden
        self.restored = 0
        self.watch_error = ""
        self._want = ""

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
                    f" · Repo {fmt_mb(int(self.d.get('size') or 0))}"
                    + (f" · {self.d['tage']} Tage" if self.d.get("tage") else ""))
        else:
            line = "Prüfung: noch nichts geliefert"
        if self.last_error:
            line += f" · FEHLER: {self.last_error}"
        return line

    # -- UP-ALT (2): neueste veröffentlichte Version
    def latest(self, now: float) -> str:
        """Neueste veröffentlichte Uploader-Version; höchstens alle LATEST_SECONDS gelesen, sonst die gemerkte. Nicht
        lesbar -> zuletzt gelesene (uploader_state.json), sonst die eigene (dann wird nie fälschlich abgewiesen)."""
        if now - self.latest_at >= LATEST_SECONDS:
            self.latest_at = now
            v = self.latest_fetch()
            if v and version_key(v):
                if v != (self.d.get("neueste") or {}).get("v"):
                    self.d["neueste"] = {"v": v, "zeit": int(now)}
                    self.save()
        v = str((self.d.get("neueste") or {}).get("v") or "")
        if not version_key(v) or version_key(v) < version_key(self.version):
            v = self.version                       # eigene ist neuer (z. B. gerade erst veröffentlicht) -> die eigene
        return v

    def minimum(self, now: float) -> str:
        """UP-MIN1: Mindestversion aus mindestversion.txt; höchstens alle LATEST_SECONDS gelesen. Nicht lesbar -> zuletzt gelesene
        (uploader_state.json), sonst MIN_BUILTIN. Darf auch sinken (der Supervisor kann sie zurücknehmen)."""
        if now - self.min_at >= LATEST_SECONDS:
            self.min_at = now
            v = self.min_fetch()
            if v and version_key(v) and v != (self.d.get("mindest") or {}).get("v"):
                self.d["mindest"] = {"v": v, "zeit": int(now)}
                self.save()
        v = str((self.d.get("mindest") or {}).get("v") or "")
        return v if version_key(v) else MIN_BUILTIN

    def outdated(self, now: float) -> str | None:
        """UP-MIN1: Text, wenn dieser Uploader unter der Mindestversion liegt, sonst None."""
        if self.legacy:
            return None
        want = self.minimum(now)
        if not is_older(self.version, want):
            return None
        return (f"Daten nicht angenommen – Uploader {self.version or 'unbekannt'} ist zu alt (Mindestversion {want}), "
                f"bitte /uploader holen")

    # -- UP-ALT (1): Wächter – main nie länger als WATCH_SECONDS anders als "sicherung"
    @staticmethod
    def _deliverer(stand: dict) -> str:
        """Uploader-Version des Rechners, der zuletzt geliefert hat (grösste "zeit" in stand.json)."""
        best, ver = -1, ""
        for v in stand.values() if isinstance(stand, dict) else []:
            if isinstance(v, dict) and int(v.get("zeit") or 0) > best:
                best, ver = int(v.get("zeit") or 0), str(v.get("uploader") or "")
        return ver

    def _restore_note(self, sha: str):
        if sha in self.warned_restore:
            return
        self.warned_restore.add(sha)
        ver = ""
        try:
            tree = {e["path"]: e for e in self.api.tree(sha)}
            if "stand.json" in tree:
                ver = self._deliverer(json.loads(self.api.blob_text(tree["stand.json"]["sha"]).decode("utf-8")))
        except (GitHubError, ValueError, UnicodeDecodeError, KeyError, TypeError):
            ver = ""
        if ver and ver != "unbekannt" and not is_older(ver, self._want or MIN_BUILTIN):
            return                                   # ein aktueller Rechner war mitten im Liefern (sicherung vor main) – kein Fund
        who = f"Uploader {ver}" if ver and ver != "unbekannt" else "Uploader vor 2.3.15"
        self.log(f"Prüfung: Lieferung eines alten Uploaders ({who}) nicht angenommen – Daten-Repo auf den gesicherten "
                 f"Stand zurückgestellt (Zweig {SAFE_BRANCH}).")

    def watch(self, now: float) -> bool | None:
        """Alle WATCH_SECONDS: weicht main von "sicherung" ab (Lieferung eines alten Uploaders), main zurückstellen.
        Gibt es "sicherung" noch nicht und ist dieser Uploader aktuell: anlegen. True = zurückgestellt/angelegt."""
        if self.legacy or now - self.watch_at < WATCH_SECONDS:
            return None
        self.watch_at = now
        try:
            branch = self.d.get("branch")
            if not branch:
                info = self.api.repo_info()
                if info.get("private") is not True:
                    return None                                   # nicht privat: nichts anfassen (wie deliver)
                branch = self.d["branch"] = str(info.get("default_branch") or "main")
            safe = self.api.head(SAFE_BRANCH)
            main = self.api.head(branch)
            if not main:
                return None
            if not safe:
                if self.outdated(now):
                    return None
                if self.api.create_ref(SAFE_BRANCH, main):
                    self.log(f"Prüfung: Zweig {SAFE_BRANCH} angelegt – ab jetzt werden Lieferungen alter Uploader nicht "
                             f"mehr angenommen.")
                    return True
                return None
            if main == safe:
                self.watch_error = ""
                return None
            for _ in range(3):                                    # liefert ein aktueller Rechner gerade, folgt main ihm
                self.api.set_ref(branch, safe)
                again = self.api.head(SAFE_BRANCH)
                if again == safe:
                    break
                safe = again
            self._restore_note(main)
            self.restored += 1
            self.watch_error = ""
            return True
        except GitHubError as e:
            if str(e) != self.watch_error:
                self.watch_error = str(e)
                self.log(f"Prüfung: Abgleich mit Zweig {SAFE_BRANCH} nicht möglich – {e} (neuer Versuch in 5 Min.).")
            return False

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
            return self.watch(now)
        if now - self.changed_at < STABLE_SECONDS or now < self.retry_at:
            return self.watch(now)
        if now - float(self.d.get("last_try") or 0) < MIN_GAP:
            return self.watch(now)
        return self.deliver(now, files, sig)

    def _read_files(self, files: dict[str, str]) -> dict[str, tuple[bytes, str]]:
        cur: dict[str, tuple[bytes, str]] = {}
        for rel, fn in files.items():
            try:
                size = os.path.getsize(fn)
                if size > MAX_RAW:
                    self._too_big.add(rel + ".gz")          # 2.3.19: vorige Fassung im Repo bleibt stehen
                    if f"{rel}:{size}" not in self.warned_big:
                        self.warned_big.add(f"{rel}:{size}")
                        self.log(f"Prüfung: {rel.split('/')[-1]} ist {fmt_mb(size)} gross (über "
                                 f"{fmt_mb(MAX_RAW)}) – übersprungen.")
                    continue
                with open(fn, "rb") as f:
                    data = f.read()
            except OSError:
                continue
            if rel.endswith("/GuildSentinel.lua"):
                # DS1: Bewerber und Sperrliste nie ins Daten-Repo; nicht sicher lesbar -> gar nicht liefern
                if svfilter is None:
                    if "svfilter" not in self.warned_filter:
                        self.warned_filter.add("svfilter")
                        self.log("Prüfung: GuildSentinel-Daten nicht geliefert: svfilter.py fehlt im Uploader-Ordner – "
                                 "ganze RaidMasterUploader.zip entpacken.")
                    continue
                try:
                    data, _n = svfilter.filter_guildsentinel(data)
                except Exception as e:               # NP-UP13-1: JEDER Fehler im Filter wie FilterError -> nie ungefiltert
                    if not isinstance(e, svfilter.FilterError):
                        e = f"{type(e).__name__}"    # kein Text der Ausnahme (könnte Dateiinhalt enthalten)
                    key = f"{rel}:{git_blob_sha(data)}"
                    if key not in self.warned_filter:
                        self.warned_filter.add(key)
                        self.log(f"Prüfung: GuildSentinel-Daten nicht geliefert: Datei nicht sicher lesbar ({e}).")
                    continue
            cur[rel] = (data, git_blob_sha(data))
        return cur

    def _clean_guildsentinel(self, sha: str, fetch, fblobs: dict[str, bytes], packed: bool = False) -> str | None:
        """UP-DS2: Datei mit Prüfwert sha filtern. Rückgabe neuer Prüfwert (gleich = war schon sauber) oder None (nicht lesbar).
        Merkt sich das Ergebnis je Prüfwert in st["daten"]["ds2"], damit jede Datei nur einmal geladen wird.
        packed (UP-TAGE 2.3.19): GuildSentinel.lua.gz – entpacken, filtern, geändert wieder gepackt (nicht entpackbar = nicht lesbar)."""
        memo = self.d.setdefault("ds2", {})
        if sha in memo:
            ns = memo[sha]
            if ns == "":
                return None
            if ns == sha or ns in fblobs or ns in self._have:
                return ns
        if svfilter is None:                           # svfilter.py fehlt -> weglassen, aber nicht merken (später wieder prüfen)
            return None
        # UP-DS2-a: Ladefehler (Netz/GitHub) NICHT merken – Ausnahme geht an deliver, diese Lieferung bricht ab und wird später
        # wiederholt; die Datei des anderen Rechners bleibt so lange unverändert im Repo (kein dauerhaftes Weglassen).
        data = fetch(sha)
        try:
            raw = gzip.decompress(data) if packed else data
            new, _n = svfilter.filter_guildsentinel(raw)
        except Exception:                            # nicht sicher lesbar -> weglassen und merken, nie ungefiltert
            memo[sha] = ""
            return None
        if packed:
            new = data if new == raw else gzip.compress(new, compresslevel=9, mtime=0)
        ns = git_blob_sha(new)
        if ns != sha:
            fblobs[ns] = new
            memo[ns] = ns                              # das gefilterte Ergebnis ist sauber (Filter ändert es nicht mehr)
        memo[sha] = ns
        return ns

    def _build(self, now: float, old: dict[str, dict], cur: dict[str, tuple[bytes, str]], stand_old: dict, fetch=None):
        """Neuer Baum: eigener Rechner neu, andere Rechner unverändert (GuildSentinel.lua gefiltert), DAYS_KEEP Tage, höchstens
        REPO_MAX. fetch(sha) -> bytes lädt eine Datei aus dem Repo (UP-DS2); ohne fetch kein Nachfiltern."""
        self._have = {e.get("sha") for e in old.values()}
        me = self.folder
        today = time.strftime("%Y-%m-%d", time.localtime(now))
        entries: dict[str, str] = {}
        sizes: dict[str, int] = {}
        for rel, (data, s) in cur.items():
            entries[f"aktuell/{me}/{rel}"] = s
            entries[f"tage/{today}/{me}/{rel}"] = s
            sizes[s] = len(data)
        for rel in set(getattr(self, "_keep_old", {})) | set(getattr(self, "_too_big", set())):
            # UP-422: von GitHub abgelehnte eigene Datei, 2.3.19: zu grosse eigene Datei -> vorige Fassung bleibt
            for r in {rel, rel[:-3] if rel.endswith(".lua.gz") else rel + ".gz"}:   # gepackt oder ungepackt, was da ist
                p = f"aktuell/{me}/{r}"
                if p in old and p not in entries:
                    entries[p] = old[p]["sha"]
                    sizes.setdefault(old[p]["sha"], int(old[p].get("size") or 0))
        # andere Rechner (Form 2.3.1: aktuell/<rechner>/<spielversion>/<konto>/<Datei>)
        for p, e in old.items():
            parts = p.split("/")
            if parts[0] == "aktuell" and len(parts) == 5 and parts[1] != me:
                entries[p] = e["sha"]
                sizes.setdefault(e["sha"], int(e.get("size") or 0))
        days = sorted({p.split("/")[1] for p in old if p.startswith("tage/") and len(p.split("/")) == 6})
        keep = [d for d in days if d != today][-(DAYS_KEEP - 1):] if DAYS_KEEP > 1 else []
        # UP-TAGE: es bleiben die letzten DAYS_KEEP GESPEICHERTEN Tage (heute + DAYS_KEEP-1 frühere), nicht "Tage jünger als …"
        self.days_aged = [d for d in days if d != today and d not in keep]
        for p, e in old.items():
            parts = p.split("/")
            if parts[0] != "tage" or len(parts) != 6:
                continue                              # Form von 2.3.0 fällt weg
            if parts[1] in keep or (parts[1] == today and parts[2] != me):
                entries[p] = e["sha"]
                sizes.setdefault(e["sha"], int(e.get("size") or 0))
        missing = getattr(self, "_missing", set())         # UP-422: Prüfwerte, die GitHub als fehlend meldet, nie wieder verwenden
        self.missing_dropped = 0
        if missing:
            mine_s = {cs for _, cs in cur.values()}           # eigene werden ja neu geschickt – nur fremde fallen weg
            for p in [p for p, s in entries.items() if s in missing and s not in mine_s]:
                del entries[p]
                self.missing_dropped += 1
        dropped = []
        while sum(sizes.get(s, 0) for s in set(entries.values())) > REPO_MAX and keep:
            gone = keep.pop(0)
            dropped.append(gone)
            entries = {p: s for p, s in entries.items() if not p.startswith(f"tage/{gone}/")}
        # UP-DS2 (2): JEDE GuildSentinel.lua im neuen Baum (andere Rechner, ältere Tage, aktuell/ und tage/) durch den Filter;
        # nicht sicher lesbar -> weglassen (nie ungefiltert). Eigene neue Dateien sind schon in _read_files gefiltert.
        fblobs: dict[str, bytes] = {}
        own = {s for _, s in cur.values()}
        gone_ds2 = 0
        if fetch is not None:
            for p in sorted(entries):
                if not p.endswith(("/GuildSentinel.lua", "/GuildSentinel.lua.gz")) or entries[p] in own:
                    continue
                ns = self._clean_guildsentinel(entries[p], fetch, fblobs, packed=p.endswith(".gz"))
                if ns is None:
                    del entries[p]
                    gone_ds2 += 1
                else:
                    if ns != entries[p]:
                        sizes.setdefault(ns, len(fblobs.get(ns, b"")))
                    entries[p] = ns
        self.ds2_dropped = gone_ds2
        stand = {k: v for k, v in stand_old.items() if isinstance(v, dict) and k != me
                 and any(p.startswith(f"aktuell/{k}/") for p in entries)}
        raw = getattr(self, "_raw_sizes", {})
        files = {}
        for rel, (d, s) in cur.items():
            files[rel] = {"bytes": len(d), "sha": s}
            if rel.endswith(".lua.gz"):
                files[rel]["gepackt"] = True                # gzip; ungepackte Grösse dazu
                files[rel]["bytes_ungepackt"] = int(raw.get(rel, 0))
        tage = sorted({p.split("/")[1] for p in entries if p.startswith("tage/") and len(p.split("/")) == 6})
        stand[me] = {"zeit": int(now), "dateien": files,
                     "grundregeln": list(self.d.get("grundregeln") or []),      # TU5: Verletzungen (ohne Namen)
                     "uploader": self.version or "unbekannt",                   # UP-DS2 (1)
                     "neueste": self._latest or self.version or "",        # UP-ALT: neueste veröffentlichte beim Liefern (Info)
                     "mindestversion": self._want or MIN_BUILTIN,            # UP-MIN1: galt beim Liefern
                     **({"update": dict(self.d["update"])} if isinstance(self.d.get("update"), dict) else {}),   # UP-UPD1
                     **({"einstellungen": dict(self.d["einstellungen"])}                                     # RM-UPD3
                        if isinstance(self.d.get("einstellungen"), dict) else {}),
                     "tage": {"anzahl": len(tage), "von": tage[0] if tage else "", "bis": tage[-1] if tage else "",
                              "grenze_tage": DAYS_KEEP, "grenze_mb": REPO_MAX // (1024 * 1024)}}   # UP-TAGE
        self.days_now = tage
        extra = {"LIESMICH.md": LIESMICH.encode("utf-8"),
                 "stand.json": json.dumps(stand, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8")}
        for p, data in extra.items():
            entries[p] = git_blob_sha(data)
            sizes[entries[p]] = len(data)
        for ns, data in fblobs.items():
            sizes[ns] = len(data)
        self.fblobs = fblobs
        return entries, sizes, extra, dropped

    def _pack_all(self, cur: dict[str, tuple[bytes, str]]) -> dict[str, tuple[bytes, str]]:
        """UP-TAGE (2.3.19, Entscheid des Nutzers 24.11. 06:26): JEDE eigene Datei gepackt liefern (<Datei>.lua.gz, gzip
        Stufe 9, mtime=0 -> gleiche Datei = gleicher Prüfwert, kein Commit ohne Änderung). Gepackt über MAX_FILE -> übersprungen."""
        self._raw_sizes = {}
        self.d.pop("gz", None)                         # Merkliste von 2.3.18 (nur zu grosse gepackt) nicht mehr nötig
        out = {}
        for rel in sorted(cur):
            data = cur[rel][0]
            packed = gzip.compress(data, compresslevel=9, mtime=0)
            if len(packed) > MAX_FILE:
                self._too_big.add(rel + ".gz")              # vorige Fassung im Repo bleibt stehen
                if f"{rel}:gz:{len(data)}" not in self.warned_big:
                    self.warned_big.add(f"{rel}:gz:{len(data)}")
                    self.log(f"Prüfung: {rel.split('/')[-1]} ist gepackt {fmt_mb(len(packed))} gross (über "
                             f"{fmt_mb(MAX_FILE)}) – übersprungen.")
                continue
            out[rel + ".gz"] = (packed, git_blob_sha(packed))
            self._raw_sizes[rel + ".gz"] = len(data)
        return out

    @staticmethod
    def _older(v: str, mine: str) -> bool:
        return is_older(v, mine)

    def _hint_old_uploaders(self, stand_old: dict):
        """UP-DS2 (3): liefert ein anderer Rechner ohne Versionsangabe oder mit älterem Uploader? Einmal melden, ohne Namen."""
        n = 0
        for k, v in stand_old.items():
            if k == self.me or k == self.folder or not isinstance(v, dict):
                continue
            ver = v.get("uploader")
            if not ver or ver == "unbekannt" or self._older(ver, self._want or MIN_BUILTIN):
                n += 1
        if n and n != self.warned_old:
            # UP-MSG1 (2.3.22): Einzahl/Mehrzahl je nach Zahl; UP-MIN1 (2.3.23): "zu alt (unter x)"
            who = "1 anderer Rechner liefert" if n == 1 else f"{n} andere Rechner liefern"
            whose = "seine" if n == 1 else "ihre"
            self.log(f"Prüfung: {who} noch mit einem zu alten Uploader (unter {self._want or MIN_BUILTIN}) – {whose} Daten "
                     f"werden nicht angenommen; dort /uploader holen.")
        self.warned_old = n
        self.old_uploaders = n

    def deliver(self, now: float, files: dict[str, str], sig: list) -> bool:
        """UP-422 (ab 2.3.17): lehnt GitHub einen Aufruf mit 422 ab, baut der Uploader EINMAL vom aktuellen main neu auf
        (gemerkte Prüfwerte verworfen, alle Dateien neu geschickt, Prüfwerte, die GitHub als fehlend nennt, nicht mehr
        verwendet); lehnt GitHub eine eigene Datei ab, bleibt deren vorige Fassung und der Rest wird geliefert."""
        self.d["last_try"] = now
        self._keep_old: dict[str, str] = {}          # eigene Dateien, die GitHub ablehnt -> vorige Fassung bleibt
        self._missing: set[str] = set()              # Prüfwerte, die GitHub als fehlend meldet
        self._too_big: set[str] = set()              # 2.3.19: eigene Dateien über MAX_RAW / gepackt über MAX_FILE
        self._want = "" if self.legacy else self.minimum(now)
        self._latest = "" if self.legacy else self.latest(now)
        why = self.outdated(now)
        if not why and not self.legacy and is_older(self.version, self._latest) and self._latest != self.told_newer:
            self.told_newer = self._latest                 # UP-MIN1 (4): nur Information, kein Abweisen
            self.log(f"Prüfung: neuere Uploader-Version {self._latest} verfügbar (/uploader) – die Daten werden weiter angenommen "
                     f"(Mindestversion {self._want}).")
        if why:                                      # UP-ALT (2)/(3): veraltet -> nichts liefern, auch "sicherung" nicht
            self.last_error = why
            self.retry_at = now + LATEST_SECONDS
            if why != self.warned_outdated:
                self.warned_outdated = why
                self.log(f"Prüfung: {why}.")
            self.save()
            return False
        self.warned_outdated = ""
        safe = None if self.legacy else SAFE_BRANCH    # UP-ALT (1): gültiger Stand
        try:
            info = self.api.repo_info()
            if info.get("private") is not True:
                raise GitHubError(f"{self.api.repo} ist nicht privat – aus Sicherheitsgründen nichts geliefert")
            branch = str(info.get("default_branch") or "main")
            self.d["branch"] = branch
            cur_all = self._pack_all(self._read_files(files))
            strict, head_retried, rounds = False, False, 0
            while True:
                rounds += 1
                if rounds > 12:
                    raise GitHubError("Daten-Repo änderte sich bei jedem Versuch")
                cur = {rel: v for rel, v in cur_all.items() if rel not in self._keep_old}
                try:
                    main_head = self.api.head(branch)
                    if main_head is None:
                        self.api.init_empty(branch)
                        main_head = self.api.head(branch)
                    safe_head = self.api.head(safe) if safe else None
                    # UP-ALT (1): Grundlage ist "sicherung" (nie, was ein alter Uploader auf main gelegt hat); gibt es sie noch
                    # nicht, main (einmalig, beim ersten aktuellen Uploader)
                    head = safe_head or main_head
                    old = {e["path"]: e for e in self.api.tree(head)} if head else {}
                    mine = {p: e.get("sha") for p, e in old.items() if p.startswith(f"aktuell/{self.folder}/")}
                    memo = self.d.get("ds2") or {}
                    dirty = any(p.endswith(("/GuildSentinel.lua", "/GuildSentinel.lua.gz"))
                                and memo.get(e.get("sha")) != e.get("sha")
                                for p, e in old.items() if not p.startswith(f"aktuell/{self.folder}/"))
                    want = {f"aktuell/{self.folder}/{rel}": s for rel, (_, s) in cur.items()}
                    for r in self._too_big:                      # zu grosse eigene Datei: vorige Fassung bleibt ohnehin
                        for v in (r, r[:-3]):
                            if f"aktuell/{self.folder}/{v}" in mine:
                                want[f"aktuell/{self.folder}/{v}"] = mine[f"aktuell/{self.folder}/{v}"]
                    if not strict and not dirty and not self._keep_old and mine == want:
                        if safe and main_head:                   # UP-ALT: auch ohne eigene Änderung main = "sicherung"
                            if not safe_head:
                                if self.api.create_ref(safe, main_head):
                                    self.log(f"Prüfung: Zweig {safe} angelegt – ab jetzt werden Lieferungen alter Uploader "
                                             f"nicht mehr angenommen.")
                            elif main_head != safe_head:
                                self.api.set_ref(branch, safe_head)
                                self._restore_note(main_head)
                                self.restored += 1
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
                    self._hint_old_uploaders(stand_old)
                    entries, sizes, extra, dropped = self._build(now, old, cur, stand_old, fetch=self.api.blob_text)
                    # Prüfwerte merken, die nicht mehr im Repo stehen, vergessen (Zustand klein halten)
                    live = {e.get("sha") for e in old.values()} | set(entries.values())
                    self.d["ds2"] = {k: v for k, v in (self.d.get("ds2") or {}).items() if k in live}
                    have = set() if strict else {e.get("sha") for e in old.values()}   # strikt: alles neu schicken
                    blobs = {s: d for d, s in cur.values()}
                    blobs.update({git_blob_sha(d): d for d in extra.values()})
                    blobs.update(self.fblobs)
                    own_rel = {}
                    for r, (_, cs) in cur.items():
                        own_rel.setdefault(cs, []).append(r)
                    order = sorted(blobs, key=lambda s: 0 if any(r.endswith("/AHSentinel.lua.gz") for r in own_rel.get(s, []))
                                   else 1)
                    for s in order:                              # AHSentinel zuerst
                        if s in have:
                            continue
                        try:
                            got = self.api.blob(blobs[s])
                        except GitHubError as e:
                            if e.code == 422 and s in own_rel:   # eigene Datei abgelehnt -> ohne sie neu bauen
                                for r in own_rel[s]:             # (ab 2.3.19 ist jede eigene Datei schon gepackt)
                                    self._keep_old[r] = e.detail or "abgelehnt"
                                continue_outer = True
                                break
                            raise
                        if got != s:
                            raise GitHubError("GitHub hat eine Datei nicht richtig angenommen")
                    else:
                        continue_outer = False
                    if continue_outer:
                        continue
                    tree = self.api.make_tree(entries)
                    commit = self.api.commit(f"Daten {self.me} {fmt_time(now)}", tree)
                    if not tree or not commit:
                        raise GitHubError("GitHub hat den Stand nicht bestätigt")
                    # hat der andere Rechner inzwischen geliefert? Dann seinen Stand einbeziehen (einmal neu)
                    if not head_retried and self.api.head(safe or branch) != (safe_head if safe else head):
                        head_retried = True
                        continue
                    if safe:                                     # UP-ALT: ZUERST "sicherung", dann main
                        if safe_head:
                            self.api.set_ref(safe, commit)
                        elif not self.api.create_ref(safe, commit):
                            head_retried = True                  # ein anderer Rechner legte sie gerade an -> auf ihr neu
                            continue
                        if main_head and main_head != safe_head and safe_head:
                            self._restore_note(main_head)        # main zeigte eine nicht angenommene Lieferung
                            self.restored += 1
                    self.api.set_ref(branch, commit)
                except GitHubError as e:
                    named = set(re.findall(r"\b[0-9a-f]{40}\b", e.detail or ""))
                    if e.code == 422 and not strict:
                        # UP-422 (3): einmal vom AKTUELLEN main neu aufbauen – nichts Gemerktes mehr verwenden
                        strict = True
                        self.d["ds2"] = {}
                        self._missing |= named
                        self.log(f"Prüfung: {e} – baue vom aktuellen Stand im Daten-Repo neu auf und versuche es sofort erneut.")
                        continue
                    if e.code == 422 and e.call == "Baum anlegen" and named - self._missing:
                        # GitHub nennt je Antwort nur EIN fehlendes Objekt -> so lange weiter, wie neue genannt werden
                        self._missing |= named
                        continue
                    raise
                # U1 (ab 2.3.2): nur "geliefert", wenn der Kopf danach wirklich unser Commit ist – sonst hat der andere
                # Rechner gleichzeitig ersetzt; dann gilt nichts als erledigt und es folgt ein neuer Versuch
                if self.api.head(safe or branch) != commit:
                    self.last_error = "anderer Rechner lieferte gleichzeitig – neuer Versuch in 1 Min."
                    self.retry_at = now + MIN_GAP
                    self.log("Prüfung: anderer Rechner lieferte gleichzeitig – neuer Versuch in 1 Minute.")
                    return False
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
        self.d.update({"last": now, "n": len(cur), "size": total, "tage": len(self.days_now)})
        if self._keep_old:
            # UP-TAGE (2.3.19): eine eigene Datei fehlt noch -> NICHT als erledigt merken, später von selbst neu versuchen
            self.retry_at = now + KEEP_OLD_RETRY
        else:
            self.d["sig_done"] = sig
        self.save()
        if self.days_aged:
            # UP-TAGE-a (Supervisor 24.11. 07:40): Text passt zur Regel (Anzahl gespeicherter Tage, nicht Alter)
            self.log(f"Prüfung: mehr als {DAYS_KEEP} Tages-Stände – älteste gelöscht: {', '.join(self.days_aged)}.")
        if dropped:
            self.log(f"Prüfung: Repo über {fmt_mb(REPO_MAX)} – ältere Tages-Stände gelöscht ({', '.join(dropped)}).")
        if self.fblobs or self.ds2_dropped:
            self.log(f"Prüfung: Datenschutz – {len(self.fblobs)} ältere GuildSentinel-Datei(en) bereinigt"
                     + (f", {self.ds2_dropped} nicht lesbare weggelassen" if self.ds2_dropped else "") + ".")
        for rel, why in sorted(self._keep_old.items()):
            self.log(f"Prüfung: GitHub lehnt {rel} ab ({why}) – dort bleibt die vorige Fassung, der Rest ist geliefert; "
                     f"neuer Versuch in {KEEP_OLD_RETRY // 60} Min. oder bei der nächsten Änderung.")
        if self.missing_dropped:
            self.log(f"Prüfung: {self.missing_dropped} Eintrag/Einträge, deren Datei bei GitHub fehlt, nicht mehr übernommen.")
        raw = getattr(self, "_raw_sizes", {})
        unp = sum(int(raw.get(r, 0)) for r in cur)
        packed = f", gepackt {fmt_mb(sum(len(d) for d, _ in cur.values()))} statt {fmt_mb(unp)}" if unp else ""
        self.log(f"Prüfung: geliefert ({len(cur)} Dateien{packed}, Repo {fmt_mb(total)}, "
                 f"{len(self.days_now)} Tag(e) von höchstens {DAYS_KEEP}).")
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
