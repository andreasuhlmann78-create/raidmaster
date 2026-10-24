#!/usr/bin/env python3
"""Lädt die neueste Addon-Zip aus download/ automatisch auf CurseForge hoch.

Wird von .github/workflows/curseforge.yml gestartet, sobald eine neue Zip in
download/ liegt (oder curseforge/projects.json geändert wurde).

- Projekt-ID, Release-Typ und auszulassende Spielversionen: curseforge/projects.json
- API-Token: GitHub-Secret CF_API_KEY (steht nie im Code)
- Version, Interface-Nummern: aus der .toc in der Zip
- Changelog: Abschnitt "## <Version>" aus CHANGELOG.md in der Zip
- Hochgeladene Versionen stehen in curseforge/uploaded.json (der Workflow
  speichert die Datei zurück ins Repo), so wird nichts doppelt hochgeladen.

Aufruf:  python3 curseforge/upload.py [Addon-Name ...] [--dry-run]
"""
import json
import os
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD = ROOT / "download"
CONFIG = Path(__file__).resolve().parent / "projects.json"
API = "https://wow.curseforge.com/api"


def version_tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or "")) or (0,)


def addon_version_key(addon, v):
    """AH Analyzer Pro: 5.9.x wurde zu 0.59.x umbenannt - alte Nummern umrechnen."""
    t = version_tuple(v)
    if addon.lower() == "ahanalyzerpro" and t and t[0] >= 1:
        return (0, t[0] * 10 + (t[1] if len(t) > 1 else 0)) + t[2:]
    return t


def newest_zip(addon):
    zips = []
    for p in DOWNLOAD.glob(f"{addon}-*.zip"):
        ver = p.stem[len(addon) + 1:]
        if ver == "latest":
            continue
        zips.append((addon_version_key(addon, ver), p))
    if not zips:
        return None
    zips.sort()
    return zips[-1][1]


def read_zip_info(path, addon):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        toc_name = next((n for n in names if n.lower() == f"{addon}/{addon}.toc".lower()), None)
        if not toc_name:
            toc_name = next((n for n in names if n.lower().endswith(".toc")), None)
        if not toc_name:
            raise SystemExit(f"{path.name}: keine .toc gefunden")
        toc = z.read(toc_name).decode("utf-8", "replace")
        changelog = ""
        ch_name = next((n for n in names if n.lower() == f"{addon}/changelog.md".lower()), None)
        if ch_name:
            changelog = z.read(ch_name).decode("utf-8", "replace")
    meta = {}
    for line in toc.splitlines():
        m = re.match(r"^##\s*([^:]+):\s*(.*)$", line.strip())
        if m:
            meta[m.group(1).strip()] = m.group(2).strip()
    version = meta.get("Version", "")
    interfaces = [int(x) for x in re.findall(r"\d+", meta.get("Interface", ""))]
    return version, interfaces, changelog_section(changelog, version)


def changelog_section(text, version):
    lines = text.splitlines()
    out, inside = [], False
    for line in lines:
        if line.startswith("## "):
            if inside:
                break
            head = line[3:].strip()
            if head == version or head.split()[0] == version:
                inside = True
                out.append(f"## {version}")
                continue
        elif inside:
            out.append(line)
    return "\n".join(out).strip() or f"Version {version}"


def changelog_since(path, addon, since, upto):
    """Alle Changelog-Abschnitte nach `since` bis einschließlich `upto` (Markdown)."""
    with zipfile.ZipFile(path) as z:
        name = next((n for n in z.namelist() if n.lower() == f"{addon}/changelog.md".lower()), None)
        if not name:
            return ""
        text = z.read(name).decode("utf-8", "replace")
    lo, hi = addon_version_key(addon, since), addon_version_key(addon, upto)
    out, keep, sections = [], False, 0
    for line in text.splitlines():
        m = re.match(r"^##\s+v?([\d.]+)", line)
        if m:
            v = addon_version_key(addon, m.group(1))
            keep = lo < v <= hi
            if keep:
                sections += 1
                out.append(line)
            continue
        if keep:
            if line.startswith(">") and sections > 1:
                continue              # Beta-Hinweis nur beim obersten Abschnitt
            out.append(line)
    return "\n".join(out).strip()


def interface_to_version(n):
    """11509 -> '1.15.9', 120105 -> '12.1.5'"""
    major, rest = divmod(n, 10000)
    minor, patch = divmod(rest, 100)
    return f"{major}.{minor}.{patch}"


def pick_game_versions(interfaces, cf_versions, skip):
    """Ordnet jede Interface-Nummer einer CurseForge-Spielversion zu.
    Exakter Treffer, sonst die höchste CurseForge-Version mit gleichem Major.Minor.
    Interface-Nummern ohne Gegenstück (z. B. WoW Forever) werden übersprungen."""
    by_name = {}
    for v in cf_versions:
        name = str(v.get("name", "")).strip()
        if re.fullmatch(r"\d+\.\d+\.\d+", name):
            by_name.setdefault(name, v["id"])
    ids, report = [], []
    for n in interfaces:
        want = interface_to_version(n)
        if want in skip or str(n) in skip:
            report.append(f"  {n} -> {want}: übersprungen (projects.json)")
            continue
        if want in by_name:
            ids.append(by_name[want])
            report.append(f"  {n} -> {want}")
            continue
        prefix = ".".join(want.split(".")[:2]) + "."
        cands = sorted((version_tuple(k), k) for k in by_name if k.startswith(prefix))
        if cands:
            k = cands[-1][1]
            ids.append(by_name[k])
            report.append(f"  {n} -> {want} nicht auf CurseForge, nehme {k}")
        else:
            report.append(f"  {n} -> {want}: auf CurseForge nicht vorhanden, ausgelassen")
    return sorted(set(ids)), report


def api_get(session, path):
    r = session.get(API + path, timeout=60)
    r.raise_for_status()
    return r.json()


STATE = Path(__file__).resolve().parent / "uploaded.json"


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    dry = "--dry-run" in sys.argv
    wanted = [a for a in sys.argv[1:] if not a.startswith("--")]
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    token = os.environ.get("CF_API_KEY", "").strip()
    import requests
    session = requests.Session()
    session.headers["X-Api-Token"] = token
    cf_versions = None
    failed = False
    state = load_state()

    for addon, cfg in config.items():
        if wanted and addon not in wanted:
            continue
        pid = cfg.get("project_id")
        if not pid:
            print(f"{addon}: keine project_id in curseforge/projects.json - übersprungen")
            continue
        if not token and not dry:
            print("::error::GitHub-Secret CF_API_KEY fehlt (Settings -> Secrets and variables -> Actions).")
            return 1
        zp = newest_zip(addon)
        if not zp:
            print(f"{addon}: keine Zip in download/ - übersprungen")
            continue
        version, interfaces, changelog = read_zip_info(zp, addon)
        # alle Neuerungen seit der zuletzt hochgeladenen Version (nicht nur diese eine)
        done = state.get(addon, [])
        if done:
            last = max(done, key=lambda v: addon_version_key(addon, v))
            full = changelog_since(zp, addon, last, version)
            if full:
                changelog = full
        display = f"{addon}-{version}"
        print(f"{addon}: {zp.name}, Version {version}, Interface {interfaces}")

        if version in state.get(addon, []):
            print(f"{addon}: {display} wurde schon hochgeladen - nichts zu tun")
            continue

        if cf_versions is None:
            cf_versions = [] if dry and not token else api_get(session, "/game/versions")
        ids, report = pick_game_versions(interfaces, cf_versions, set(cfg.get("skip_game_versions", [])))
        print("\n".join(report))
        if not ids and not dry:
            print(f"::error::{addon}: keine passende CurseForge-Spielversion gefunden")
            failed = True
            continue

        metadata = {
            "changelog": changelog,
            "changelogType": "markdown",
            "displayName": display,
            "gameVersions": ids,
            "releaseType": cfg.get("release_type", "release"),
        }
        print("Changelog:\n" + changelog)
        if dry:
            print(f"{addon}: dry-run, nicht hochgeladen. Metadaten: {json.dumps(metadata)[:300]}")
            continue
        with open(zp, "rb") as fh:
            r = session.post(
                f"{API}/projects/{pid}/upload-file",
                data={"metadata": json.dumps(metadata)},
                files={"file": (zp.name, fh, "application/zip")},
                timeout=300,
            )
        if r.ok:
            print(f"{addon}: {display} hochgeladen (Datei-ID {r.json().get('id')})")
            state.setdefault(addon, []).append(version)
            save_state(state)
        else:
            print(f"::error::{addon}: Upload fehlgeschlagen ({r.status_code}): {r.text[:500]}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
