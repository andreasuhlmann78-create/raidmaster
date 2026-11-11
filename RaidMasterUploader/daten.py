"""Addon-Daten für die Prüf-Sitzung in ein PRIVATES GitHub-Repo liefern – ab Uploader 2.3.0.

Auftrag: auftraege/RaidMaster/anweisung-uploader-daten-pruefung.txt (Entscheid des Nutzers 11.11.2026, mit den
Nachträgen 20:30 "bei jedem /reload" und 20:35 "kein endloser Datenschrott").

DU1 Ziel: ein privates Repo des Nutzers (z. B. <Besitzer>/goldsentinel-daten). Zugang über einen Fine-grained-Token NUR
    für dieses Repo (Contents: Read and write). Repo und Token stehen in daten_config.json neben dem Uploader (geheim, nie
    im Log, nie im öffentlichen raidmaster-Repo). Meldet GitHub das Repo nicht als privat, wird nichts geliefert.
    Einrichten: Daten-Repo-einrichten.bat (fragt Repo und Token ab, prüft und schreibt daten_config.json).
DU2 Was: nur die SavedVariables der GoldSentinel-Addons auf Kontoebene (AHSentinel zuerst, dann GuildSentinel,
    ProfessionSentinel, LevelPilot, ThreatSentinel, BuffSentinel, RaidMaster) aller Spielversionen. Keine fremden Addons,
    keine .bak, keine Config.wtf, keine Charakter-Ordner. Ablage <spielversion>/<kontoN>/<Datei>.lua – der Konto-Ordner
    heisst im Repo nur "konto1", "konto2" …; der Rechnername steht im Commit-Text.
DU3 Wann: nach JEDEM Schreiben durch WoW (/reload, Ausloggen, Beenden): Änderung erkannt -> warten, bis Grösse und Zeit
    10 s stabil sind -> liefern. Höchstens 1 Commit je Minute (die letzte Fassung gewinnt). Nichts geändert -> nie ein
    Commit. Dateien über 50 MB werden übersprungen und einmal gemeldet.
DU4 Weg: GitHub-API (Git Data) mit urllib, keine weiteren Pakete. Fehler (kein Netz, Token falsch, kein Zugriff) ->
    klare Meldung im Fenster, nichts kaputt, neuer Versuch bei der nächsten Änderung (spätestens nach 5 Min.).
DU5 Anzeige: "Prüfung: zuletzt geliefert 19:36 (3 Dateien) · Repo 12,3 MB".
DU6 Kein endloser Verlauf: Das Repo enthält immer nur
      aktuell/<spielversion>/<kontoN>/<Datei>.lua  – den neuesten Stand,
      tage/<JJJJ-MM-TT>/…                          – höchstens 7 Tages-Stände (letzter Stand jedes Tages),
      stand.json                                   – Rechner, Zeit, Dateien mit Grösse und Prüfwert.
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
LIESMICH = ("# GoldSentinel-Daten (privat)\n\n"
            "Wird vom RaidMaster-Uploader geschrieben. Nur für die Prüf-Sitzung. Nicht von Hand ändern.\n\n"
            "- `aktuell/` – neuester Stand der Addon-Daten (je Spielversion und Konto)\n"
            "- `tage/<Datum>/` – letzter Stand der letzten 7 Spieltage\n"
            "- `stand.json` – Rechner, Zeit, Dateien\n\n"
            "Jede Lieferung ersetzt den Verlauf (ein einziger Commit) – ältere Fassungen gibt es hier nicht.\n")


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def fmt_time(t: float | None) -> str:
    return time.strftime("%d.%m. %H:%M", time.localtime(t)) if t else "–"


def fmt_mb(n: int) -> str:
    return f"{n / 1024 / 1024:.1f}".replace(".", ",") + " MB"


def load_config(here: str) -> dict | None:
    try:
        with open(os.path.join(here, DATEN_CONFIG), "r", encoding="utf-8") as f:
            conf = json.load(f)
    except (OSError, ValueError):
        return None
    repo, token = str(conf.get("repo") or "").strip(), str(conf.get("token") or "").strip()
    if not REPO_RE.match(repo) or not token:
        return None
    return {"repo": repo, "token": token}


def save_config(here: str, repo: str, token: str):
    path = os.path.join(here, DATEN_CONFIG)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"repo": repo, "token": token}, f, indent=2)
    os.replace(tmp, path)


class GitHubError(Exception):
    pass


class GitHubAPI:
    """Nur die paar Aufrufe, die die Lieferung braucht. Der Token steht nie in einer Meldung."""

    def __init__(self, repo: str, token: str, timeout: int = 180):
        self.repo, self._token, self.timeout = repo, token, timeout

    def _req(self, method: str, path: str, body: dict | None = None, ok404: bool = False):
        req = urllib.request.Request(API + path, method=method,
                                     data=json.dumps(body).encode("utf-8") if body is not None else None)
        req.add_header("Authorization", "Bearer " + self._token)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "GoldSentinel-Uploader")
        if body is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
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
        except (urllib.error.URLError, OSError, ValueError):
            raise GitHubError("kein Netz oder GitHub nicht erreichbar") from None

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


class Daten:
    """Lieferung an das private Daten-Repo. Zustand in st["daten"] (uploader_state.json)."""

    def __init__(self, api: GitHubAPI, roots: dict[str, str], st: dict, save, machine: str, log):
        self.api, self.roots, self.save, self.me, self.log = api, dict(roots), save, machine, log
        d = st.setdefault("daten", {})
        d.setdefault("konten", {})
        self.d = d
        self.sig = None
        self.changed_at = 0.0
        self.retry_at = 0.0
        self.last_error = ""
        self.warned_big: set[str] = set()

    # -- welche Dateien (DU2)
    def _alias(self, key: str) -> str:
        k = self.d["konten"]
        if key not in k:
            k[key] = f"konto{len(k) + 1}"
        return k[key]

    def files(self) -> dict[str, str]:
        out = {}
        for key, acc in sorted(self.roots.items()):
            flavor = (key.split("/")[0] if key else "wow").strip("_") or "wow"
            for addon in ADDONS:
                fn = os.path.join(acc, "SavedVariables", addon + ".lua")
                if os.path.isfile(fn):
                    out[f"{flavor}/{self._alias(key)}/{addon}.lua"] = fn
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

    def deliver(self, now: float, files: dict[str, str], sig: list) -> bool:
        self.d["last_try"] = now
        try:
            info = self.api.repo_info()
            if info.get("private") is not True:
                raise GitHubError(f"{self.api.repo} ist nicht privat – aus Sicherheitsgründen nichts geliefert")
            branch = str(info.get("default_branch") or "main")
            head = self.api.head(branch)
            if head is None:
                self.api.init_empty(branch)
                head = self.api.head(branch)
            old = {e["path"]: e for e in self.api.tree(head)} if head else {}
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
            aktuell = {"aktuell/" + rel: s for rel, (_, s) in cur.items()}
            old_akt = {p: e.get("sha") for p, e in old.items() if p.startswith("aktuell/")}
            if aktuell == old_akt:
                self.d["sig_done"] = sig                 # nichts geändert -> nie ein Commit
                self.last_error = ""
                self.save()
                return True
            today = time.strftime("%Y-%m-%d", time.localtime(now))
            entries = dict(aktuell)
            sizes = {s: len(data) for data, s in cur.values()}
            days = sorted({p.split("/")[1] for p in old if p.startswith("tage/") and p.count("/") >= 2} - {today})
            keep = days[-(DAYS_KEEP - 1):] if DAYS_KEEP > 1 else []
            for p, e in old.items():
                if p.startswith("tage/") and p.split("/")[1] in keep:
                    entries[p] = e["sha"]
                    sizes.setdefault(e["sha"], int(e.get("size") or 0))
            for rel, (_, s) in cur.items():
                entries[f"tage/{today}/{rel}"] = s
            dropped = []
            while sum(sizes.get(s, 0) for s in set(entries.values())) > REPO_MAX and keep:
                gone = keep.pop(0)
                dropped.append(gone)
                entries = {p: s for p, s in entries.items() if not p.startswith(f"tage/{gone}/")}
            extra = {
                "LIESMICH.md": LIESMICH.encode("utf-8"),
                "stand.json": json.dumps({"rechner": self.me, "zeit": int(now),
                                          "dateien": {rel: {"bytes": len(d), "sha": s} for rel, (d, s) in cur.items()}},
                                         ensure_ascii=False, indent=1).encode("utf-8"),
            }
            for p, data in extra.items():
                entries[p] = git_blob_sha(data)
                sizes[entries[p]] = len(data)
            have = {e.get("sha") for e in old.values()}
            blobs = {s: d for d, s in cur.values()}
            blobs.update({git_blob_sha(d): d for d in extra.values()})
            # AHSentinel zuerst hochladen (ADDONS-Reihenfolge)
            order = sorted(blobs, key=lambda s: 0 if any(s == cs and r.endswith("/AHSentinel.lua")
                                                          for r, (_, cs) in cur.items()) else 1)
            for s in order:
                if s in have:
                    continue
                got = self.api.blob(blobs[s])
                if got != s:
                    raise GitHubError("GitHub hat eine Datei nicht richtig angenommen")
            tree = self.api.make_tree(entries)
            commit = self.api.commit(f"Daten {self.me} {fmt_time(now)}", tree)
            if not tree or not commit:
                raise GitHubError("GitHub hat den Stand nicht bestätigt")
            self.api.set_ref(branch, commit)
        except GitHubError as e:
            self.last_error = str(e)
            self.retry_at = now + RETRY_SECONDS
            self.log(f"Prüfung: {e} – nichts geliefert, neuer Versuch bei der nächsten Änderung.")
            return False
        total = sum(sizes.get(s, 0) for s in set(entries.values()))
        self.last_error = ""
        self.d.update({"last": now, "n": len(cur), "sig_done": sig, "size": total})
        self.save()
        if dropped:
            self.log(f"Prüfung: Repo über {fmt_mb(REPO_MAX)} – ältere Tages-Stände gelöscht ({', '.join(dropped)}).")
        self.log(f"Prüfung: geliefert ({len(cur)} Dateien, Repo {fmt_mb(total)}).")
        return True


def setup_interactive(here: str, ask=input, ask_secret=None, log=print) -> bool:
    """Daten-Repo-einrichten.bat: Repo und Token abfragen, prüfen (privat, Zugriff), daten_config.json schreiben."""
    import getpass
    ask_secret = ask_secret or getpass.getpass
    log("Daten für die Prüf-Sitzung – einmal einrichten")
    log("Vorher auf github.com: ein PRIVATES Repo anlegen (z. B. goldsentinel-daten) und einen Fine-grained-Token NUR")
    log("für dieses Repo mit 'Contents: Read and write' (Anleitung in LIESMICH.txt).")
    repo = ask("Repo (Besitzer/Name, z. B. meinname/goldsentinel-daten): ").strip()
    if not REPO_RE.match(repo):
        log("Das ist kein Repo-Name in der Form Besitzer/Name – nichts gespeichert.")
        return False
    token = ask_secret("Token einfügen (wird nicht angezeigt): ").strip()
    if not token:
        log("Kein Token – nichts gespeichert.")
        return False
    api = GitHubAPI(repo, token, timeout=60)
    try:
        info = api.repo_info()
    except GitHubError as e:
        log(f"Prüfung fehlgeschlagen: {e} – nichts gespeichert.")
        return False
    if info.get("private") is not True:
        log(f"{repo} ist NICHT privat – aus Sicherheitsgründen nichts gespeichert. Repo auf privat stellen.")
        return False
    save_config(here, repo, token)
    log(f"Gespeichert in {DATEN_CONFIG}. Der Uploader liefert ab jetzt nach jedem /reload und Ausloggen.")
    log(f"Bitte der Prüf-Sitzung den Repo-Namen melden: {repo}")
    return True
