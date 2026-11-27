"""Wächter für announce/ (D-ANN1 b, Entscheid des Nutzers 23.11.2026 11:36: Ankündigungen im Repo nie mehr löschen).

Liest `git diff --name-status -M <vorher> <nachher>` von stdin (oder die Zeilen als Argument der Funktion) und meldet jede
gelöschte oder umbenannte Datei announce/*.md bzw. announce/*.zip. Ausgabe: Liste; Exit-Code 1, wenn etwas gefunden wurde
(Workflow announce-guard.yml wird rot). Bilder und andere Anhänge zählen nicht (Entscheid nennt .md und .zip).
Aufruf: git diff --name-status -M A B | python3 -I RaidMasterBot/tools/announce_guard.py
"""
import os
import sys

WATCH = (".md", ".zip")


def violations(lines, head_announce=None, head_download=None) -> list[str]:
    """Ab DC-ANN2 (Entscheid des Nutzers 27.11. 20:58 "Nur die letzten 3 behalten"): Eine gelöschte announce/*.zip ist erlaubt,
    wenn sie nach announce_aufraeumen.removable entfernt werden darf (im Stand danach je Addon 3 neuere ZIPs, nicht die stabile
    Version). .md bleibt immer verboten. Ohne head_* (alte Aufrufe/Tests): jede Löschung ist ROT wie bisher."""
    out = []
    for line in lines:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2 or not parts[0]:
            continue
        kind, path = parts[0][0], parts[1]
        if not (path.startswith("announce/") and path.lower().endswith(WATCH)):
            continue
        if kind == "D":
            if (path.lower().endswith(".zip") and head_announce is not None
                    and _removable(path.rsplit("/", 1)[-1], head_announce, head_download or [])):
                continue
            out.append(f"{path} (gelöscht)")
        elif kind == "R":
            out.append(f"{path} (umbenannt)")
    return out


def _removable(name, head_announce, head_download) -> bool:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import announce_aufraeumen
    return announce_aufraeumen.removable(name, head_announce, head_download)


def main() -> int:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    try:
        head_ann = os.listdir(os.path.join(root, "announce"))
        head_dl = os.listdir(os.path.join(root, "download"))
    except OSError:
        head_ann = head_dl = None
    found = violations(sys.stdin.read().splitlines(), head_ann, head_dl)
    if found:
        print("ROT: Ankündigungen dürfen im Repo nicht gelöscht oder umbenannt werden (Entscheid des Nutzers 23.11.2026; ausser alten "
              "ZIP-Anhängen nach DC-ANN2 – je Addon 3 neueste + stabile bleiben):")
        for f in found:
            print("  - " + f)
        print("Bitte die Datei(en) wiederherstellen (git checkout <vorher> -- <Datei>). Eine neue Fassung = neue Datei.")
        return 1
    print("OK: keine Ankündigung gelöscht oder umbenannt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
