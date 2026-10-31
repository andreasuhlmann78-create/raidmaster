"""
RaidMaster-Bot – Selbst-Update.

Neue Versionen kommen aus einem GitHub-Repository (automatisch) oder als ZIP über /update.
Aufbau des Repositorys bzw. der ZIP:

    RaidMasterBot/   (bot.py, raidmaster_data.py, ...)
    RaidMaster/      (das Addon mit RaidMaster.toc)   – optional

Ablauf: ZIP entpacken -> prüfen (alle .py-Dateien müssen sich übersetzen lassen) -> aktuelle Dateien
sichern -> neue Dateien kopieren -> Addon-ZIP für #raid-addon bauen -> Bot mit Code 42 beenden.
launcher.py startet den Bot neu und stellt die Sicherung wieder her, falls die neue Version abstürzt.
config.json, data/, addon/ und backup/ werden nie überschrieben.
"""

from __future__ import annotations

import io
import json
import os
import py_compile
import re
import shutil
import tempfile
import time
import zipfile

RESTART_CODE = 42
KEEP = {"config.json", "data", "addon", "backup", "update", "venv", ".venv", "logs", "__pycache__", ".git"}
REQUIRED = ("bot.py", "raidmaster_data.py", "server_setup.py", "updater.py", "launcher.py")
USER_AGENT = "RaidMasterBot-Updater (https://github.com, 1.0)"


class UpdateError(Exception):
    pass


def update_dir(base: str) -> str:
    return os.path.join(base, "update")


def pending_path(base: str) -> str:
    return os.path.join(update_dir(base), "pending.json")


def failed_path(base: str) -> str:
    return os.path.join(update_dir(base), "failed.json")


def read_json(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write_json(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def bot_version(base: str) -> str:
    try:
        with open(os.path.join(base, "VERSION"), "r", encoding="utf-8") as f:
            return f.read().strip() or "?"
    except OSError:
        return "?"


def toc_version(addon_dir: str) -> str | None:
    toc = os.path.join(addon_dir, "RaidMaster.toc")
    try:
        with open(toc, "r", encoding="utf-8-sig") as f:
            for line in f:
                m = re.match(r"##\s*Version:\s*([\d.]+)", line)
                if m:
                    return m.group(1)
    except OSError:
        pass
    return None


# ---------------------------------------------------------------------------
# ZIP prüfen
# ---------------------------------------------------------------------------

def _safe_extract(zf: zipfile.ZipFile, target: str):
    root = os.path.realpath(target)
    for member in zf.infolist():
        dest = os.path.realpath(os.path.join(target, member.filename))
        if not (dest == root or dest.startswith(root + os.sep)):
            raise UpdateError(f"Ungültiger Pfad in der ZIP: {member.filename}")
    zf.extractall(target)


def find_roots(folder: str) -> tuple[str | None, str | None]:
    """Sucht den Bot-Ordner (mit bot.py) und den Addon-Ordner (mit RaidMaster.toc)."""
    bot_dir = addon_dir = None
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git", "data", "venv", ".venv")]
        if bot_dir is None and "bot.py" in filenames and "raidmaster_data.py" in filenames:
            bot_dir = dirpath
        if addon_dir is None and "RaidMaster.toc" in filenames:
            addon_dir = dirpath
    return bot_dir, addon_dir


def validate_bot_dir(bot_dir: str):
    missing = [f for f in REQUIRED if not os.path.isfile(os.path.join(bot_dir, f))]
    if missing:
        raise UpdateError("In der neuen Version fehlen Dateien: " + ", ".join(missing))
    out = tempfile.mkdtemp(prefix="rm-check-")
    try:
        for name in os.listdir(bot_dir):
            if name.endswith(".py"):
                try:
                    py_compile.compile(os.path.join(bot_dir, name), doraise=True, cfile=os.path.join(out, name + "c"))
                except py_compile.PyCompileError as e:
                    raise UpdateError(f"Fehler in {name}: {e.msg.strip()[:300]}")
    finally:
        shutil.rmtree(out, ignore_errors=True)


# ---------------------------------------------------------------------------
# Installieren / Zurücksetzen
# ---------------------------------------------------------------------------

def _bot_files(base: str) -> list[str]:
    return [n for n in os.listdir(base) if n not in KEEP and not n.startswith(".")]


def backup_current(base: str) -> str:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = os.path.join(base, "backup", "code-" + stamp)
    os.makedirs(target, exist_ok=True)
    for name in _bot_files(base):
        src = os.path.join(base, name)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(target, name))
        else:
            shutil.copy2(src, os.path.join(target, name))
    # nur die letzten 5 Sicherungen behalten
    folder = os.path.join(base, "backup")
    old = sorted(d for d in os.listdir(folder) if d.startswith("code-"))
    for d in old[:-5]:
        shutil.rmtree(os.path.join(folder, d), ignore_errors=True)
    return target


def _copy_new(src_dir: str, base: str) -> list[str]:
    changed = []
    for name in os.listdir(src_dir):
        if name in KEEP or name.startswith("."):
            continue
        src = os.path.join(src_dir, name)
        dst = os.path.join(base, name)
        if os.path.isdir(src):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            if os.path.isfile(dst):
                with open(src, "rb") as a, open(dst, "rb") as b:
                    if a.read() == b.read():
                        continue
            shutil.copy2(src, dst)
        changed.append(name)
    return changed


def build_addon_zip(addon_dir: str, base: str) -> str | None:
    """Packt das Addon als RaidMaster-<Version>.zip in den Ordner addon/ (für #raid-addon)."""
    version = toc_version(addon_dir)
    if not version:
        return None
    out_dir = os.path.join(base, "addon")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"RaidMaster-{version}.zip")
    if os.path.isfile(out):
        return out
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(addon_dir):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in sorted(filenames):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, addon_dir)
                zf.write(full, os.path.join("RaidMaster", rel))
    return out


def install_zip(data: bytes, base: str, source: str, ref: str = "") -> dict:
    """Installiert eine Update-ZIP. Liefert Infos fürs Protokoll; wirft UpdateError bei Problemen."""
    tmp = os.path.join(update_dir(base), "tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    try:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                _safe_extract(zf, tmp)
        except zipfile.BadZipFile:
            raise UpdateError("Die Datei ist keine gültige ZIP.")
        bot_dir, addon_dir = find_roots(tmp)
        if not bot_dir and not addon_dir:
            raise UpdateError("In der ZIP wurde weder der Bot (bot.py) noch das Addon (RaidMaster.toc) gefunden.")
        result = {"source": source, "ref": ref, "at": int(time.time()), "bot_changed": [], "addon_zip": None,
                  "old_version": bot_version(base), "version": bot_version(base), "requirements": False}
        # Ankündigungen (Ordner announce) übernehmen - der Bot postet jede Datei einmal
        for dirpath, _, filenames in os.walk(tmp):
            if os.path.basename(dirpath) == "announce":
                os.makedirs(os.path.join(base, "announce"), exist_ok=True)
                for fn in filenames:
                    # Text (.md) und Anhänge dazu (Bilder, ZIP, PDF) – siehe check_announcements im Bot
                    if fn.lower().endswith((".md", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".pdf", ".txt")):
                        shutil.copy2(os.path.join(dirpath, fn), os.path.join(base, "announce", fn))
        # fertige Addon-ZIPs aus dem Ordner download (z. B. AHSentinel) übernehmen
        for dirpath, _, filenames in os.walk(tmp):
            if os.path.basename(dirpath) == "download":
                os.makedirs(os.path.join(base, "addon"), exist_ok=True)
                for fn in filenames:
                    if fn.lower().endswith(".zip") and "latest" not in fn.lower():
                        dst = os.path.join(base, "addon", fn)
                        # der Uploader hat keine Versionsnummer im Namen: immer die neueste Fassung übernehmen
                        if not os.path.isfile(dst) or fn.lower().startswith("raidmasteruploader"):
                            shutil.copy2(os.path.join(dirpath, fn), dst)
        if addon_dir:
            z = build_addon_zip(addon_dir, base)
            result["addon_zip"] = os.path.basename(z) if z else None
            result["addon_version"] = toc_version(addon_dir)
        if bot_dir:
            validate_bot_dir(bot_dir)
            req_old = _read(os.path.join(base, "requirements.txt"))
            backup = backup_current(base)
            try:
                changed = _copy_new(bot_dir, base)
            except OSError as e:
                restore(base, backup)
                raise UpdateError(f"Kopieren fehlgeschlagen ({e}) – alte Version wiederhergestellt.")
            result["bot_changed"] = changed
            result["backup"] = backup
            result["version"] = bot_version(base)
            result["requirements"] = _read(os.path.join(base, "requirements.txt")) != req_old
            if changed:
                write_json(pending_path(base), result)
        return result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def restore(base: str, backup: str):
    """Stellt die gesicherten Bot-Dateien wieder her."""
    if not backup or not os.path.isdir(backup):
        raise UpdateError("Keine Sicherung gefunden.")
    for name in _bot_files(base):
        path = os.path.join(base, name)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            os.remove(path)
    for name in os.listdir(backup):
        src = os.path.join(backup, name)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(base, name))
        else:
            shutil.copy2(src, os.path.join(base, name))


def rollback_pending(base: str, reason: str) -> dict | None:
    """Vom Launcher aufgerufen, wenn die neue Version gleich nach dem Start abstürzt."""
    pending = read_json(pending_path(base))
    if not pending:
        return None
    try:
        restore(base, pending.get("backup"))
    finally:
        os.remove(pending_path(base))
    pending["reason"] = reason
    write_json(failed_path(base), pending)
    return pending


def confirm_pending(base: str) -> dict | None:
    """Neue Version läuft stabil -> Markierung entfernen. Liefert die Update-Infos."""
    pending = read_json(pending_path(base))
    if pending:
        os.remove(pending_path(base))
    return pending


def take_failed(base: str) -> dict | None:
    failed = read_json(failed_path(base))
    if failed:
        os.remove(failed_path(base))
    return failed


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

def _headers(token: str | None) -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT, "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


async def github_latest(session, repo: str, branch: str, token: str | None) -> dict:
    """Letzter Commit: {'sha', 'message', 'date'}"""
    url = f"https://api.github.com/repos/{repo}/commits/{branch}"
    async with session.get(url, headers=_headers(token)) as r:
        if r.status == 404:
            raise UpdateError(f"Repository {repo} (Zweig {branch}) nicht gefunden – bei privatem Repository fehlt der Token.")
        if r.status in (401, 403):
            raise UpdateError(f"GitHub verweigert den Zugriff ({r.status}) – Token prüfen.")
        if r.status != 200:
            raise UpdateError(f"GitHub antwortet mit {r.status}.")
        data = await r.json()
    commit = data.get("commit") or {}
    return {"sha": data.get("sha", ""), "message": (commit.get("message") or "").strip(),
            "date": ((commit.get("committer") or {}).get("date") or "")}


async def github_zip(session, repo: str, sha: str, token: str | None) -> bytes:
    url = f"https://api.github.com/repos/{repo}/zipball/{sha}"
    async with session.get(url, headers=_headers(token)) as r:
        if r.status != 200:
            raise UpdateError(f"Download von GitHub fehlgeschlagen ({r.status}).")
        return await r.read()
