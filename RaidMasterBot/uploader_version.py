"""Version des verteilten Uploaders prüfen (ab Bot 1.5.128, Befund D-UP1).

/uploader schickte die RaidMasterUploader.zip aus dem Ordner addon – bis zum nächsten Selbst-Update (höchstens 30 Min)
eine alte Fassung (13.11.: Bot-Update 12:15, Uploader 2.3.5 erst 12:47). Jetzt:
- Version der ZIP lesen (VERSION = "x.y.z" in RaidMasterUploader/uploader.py),
- Version im Repo lesen (RaidMasterUploader/uploader.py) und vergleichen,
- ist das Repo neuer: nur die Uploader-ZIP aus download/ holen (prüfen, dann ersetzen) – kein ganzes Update,
- /uploader nennt die Version und warnt, wenn die ZIP trotzdem älter ist.
"""
from __future__ import annotations

import io
import re
import zipfile

VERSION_RE = re.compile(r'^VERSION\s*=\s*["\'](\d+(?:\.\d+){1,3})["\']', re.M)


def parse_version(text: str) -> str | None:
    m = VERSION_RE.search(text or "")
    return m.group(1) if m else None


def key(v: str | None) -> tuple:
    if not v:
        return ()
    return tuple(int(x) for x in v.split("."))


def is_older(have: str | None, want: str | None) -> bool:
    """have älter als want? Unbekannte Version gilt als älter, wenn want bekannt ist."""
    if not want:
        return False
    return key(have) < key(want)


def zip_version(data: bytes) -> str | None:
    """VERSION aus RaidMasterUploader/uploader.py in der ZIP (Bytes). None, wenn keine gültige ZIP oder keine Version."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            name = next((n for n in zf.namelist() if n.replace("\\", "/").endswith("uploader.py")), None)
            if not name:
                return None
            return parse_version(zf.read(name).decode("utf-8", errors="replace"))
    except (zipfile.BadZipFile, OSError, KeyError):
        return None


def file_version(path: str | None) -> str | None:
    if not path:
        return None
    try:
        with open(path, "rb") as f:
            return zip_version(f.read())
    except OSError:
        return None


def raw_url(repo: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/HEAD/{path}"


def note(have: str | None, want: str | None) -> str:
    """Zeile für die /uploader-Antwort."""
    if have and want and is_older(have, want):
        return (f"⚠️ Diese Uploader-ZIP ist **{have}**, im Repo gibt es schon **{want}**. Bitte in ein paar Minuten "
                "`/uploader nur_programm:True` erneut – nicht über eine neuere Fassung entpacken.")
    return f"Uploader-Version **{have or '?'}**."
