"""DC-ANN2 (Entscheid des Nutzers 27.11.2026 20:58 "Nur die letzten 3 behalten"; Auftrag Supervisor 21:00): alte Addon-ZIPs in announce/.

Je Addon bleiben in announce/ die 3 neuesten ZIP-Anhänge und die stabile Version (gleiche Version wie download/<Addon>-<Version>.zip).
Ältere ZIP-Anhänge werden entfernt. Die .md-Dateien bleiben IMMER (der Bot löscht im Discord nichts, wenn nur eine ZIP fehlt: Er reagiert
nur auf eine fehlende .md – updater.mirror_announce_removals –, und eine gepostete .md wird nie neu gepostet).

Grund: Das Repo war durch announce/*.zip auf ~0,9 GB gewachsen (319 ZIPs, 755 MB); jedes Bot-Update lädt die ganze Repo-ZIP
(DC-UPL1, 27.11.). Die Git-Geschichte bleibt – addon_check kennt alte Versionen weiter aus `git log --all`.

Namen: announce/<kanal>__<reihe>-<Version>.<Addon>.zip (wie addon_check). Andere ZIP-Namen werden nie angefasst.
Aufruf:  python3 -I RaidMasterBot/tools/announce_aufraeumen.py            -> Trockenlauf (Liste, nichts gelöscht)
         python3 -I RaidMasterBot/tools/announce_aufraeumen.py --ausfuehren -> löschen
Exit-Code 0. Ausgabe: je Addon behalten/entfernt, MB vorher/nachher.
"""
from __future__ import annotations

import os
import re
import sys

KEEP = 3
ANN_ZIP = re.compile(r"^[^_]+__.+?-(\d+(?:\.\d+)+)\.([A-Za-z0-9_]+)\.zip$")
DL_ZIP = re.compile(r"^([A-Za-z0-9_]+)-(\d+(?:\.\d+)+)\.zip$")


def vkey(v: str) -> tuple:
    return tuple(int(x) for x in v.split("."))


def announce_zip(name: str):
    """(addon klein, Version) oder None."""
    m = ANN_ZIP.match(name)
    return (m.group(2).lower(), m.group(1)) if m else None


def stable_versions(download_names) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for n in download_names:
        m = DL_ZIP.match(n)
        if m:
            out.setdefault(m.group(1).lower(), set()).add(m.group(2))
    return out


def plan(announce_names, download_names, keep: int = KEEP) -> tuple[list[str], list[str]]:
    """(behalten, entfernen) – nur ZIPs mit erkanntem Namen kommen in "entfernen"."""
    stable = stable_versions(download_names)
    by_addon: dict[str, list[tuple[tuple, str]]] = {}
    keep_list, remove = [], []
    for n in announce_names:
        if not n.lower().endswith(".zip"):
            continue
        av = announce_zip(n)
        if not av:
            keep_list.append(n)
            continue
        by_addon.setdefault(av[0], []).append((vkey(av[1]), n))
    for addon, items in by_addon.items():
        items.sort(reverse=True)
        top = {v for v, _ in items[:keep]}
        st = {vkey(v) for v in stable.get(addon, set())}
        for v, n in items:
            (keep_list if (v in top or v in st) else remove).append(n)
    return sorted(keep_list), sorted(remove)


def removable(deleted_name: str, head_announce_names, head_download_names, keep: int = KEEP) -> bool:
    """Für den Wächter: Darf diese (im Repo gelöschte) ZIP fehlen? Ja, wenn es im Stand danach je Addon schon `keep` neuere
    ZIPs gibt und sie nicht die stabile Version ist."""
    av = announce_zip(deleted_name)
    if not av:
        return False
    addon, ver = av
    if ver in stable_versions(head_download_names).get(addon, set()):
        return False
    newer = [n for n in head_announce_names
             if (x := announce_zip(n)) and x[0] == addon and vkey(x[1]) > vkey(ver)]
    return len(newer) >= keep


def main(argv) -> int:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ann, dl = os.path.join(root, "announce"), os.path.join(root, "download")
    names = sorted(os.listdir(ann))
    keep_list, remove = plan(names, os.listdir(dl) if os.path.isdir(dl) else [])
    size = {n: os.path.getsize(os.path.join(ann, n)) for n in names if n.lower().endswith(".zip")}
    before = sum(size.values())
    gone = sum(size[n] for n in remove)
    per: dict[str, list[int]] = {}
    for n in keep_list:
        a = (announce_zip(n) or ("(anderer Name)",))[0]
        per.setdefault(a, [0, 0])[0] += 1
    for n in remove:
        per.setdefault(announce_zip(n)[0], [0, 0])[1] += 1
    run = "--ausfuehren" in argv
    print(("AUSGEFÜHRT" if run else "TROCKENLAUF (nichts gelöscht)") + f" – je Addon die {KEEP} neuesten + stabile Version")
    for a in sorted(per):
        print(f"  {a}: behalten {per[a][0]}, entfernen {per[a][1]}")
    print(f"ZIPs in announce/: {len(size)} -> {len(size) - len(remove)}; "
          f"{before / 1e6:.1f} MB -> {(before - gone) / 1e6:.1f} MB")
    for n in remove:
        print("  - " + n)
        if run:
            os.remove(os.path.join(ann, n))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
