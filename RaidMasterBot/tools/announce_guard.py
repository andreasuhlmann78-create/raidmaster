"""Wächter für announce/ (D-ANN1 b, Entscheid des Nutzers 23.11.2026 11:36: Ankündigungen im Repo nie mehr löschen).

Liest `git diff --name-status -M <vorher> <nachher>` von stdin (oder die Zeilen als Argument der Funktion) und meldet jede
gelöschte oder umbenannte Datei announce/*.md bzw. announce/*.zip. Ausgabe: Liste; Exit-Code 1, wenn etwas gefunden wurde
(Workflow announce-guard.yml wird rot). Bilder und andere Anhänge zählen nicht (Entscheid nennt .md und .zip).
Aufruf: git diff --name-status -M A B | python3 -I RaidMasterBot/tools/announce_guard.py
"""
import sys

WATCH = (".md", ".zip")


def violations(lines) -> list[str]:
    out = []
    for line in lines:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2 or not parts[0]:
            continue
        kind, path = parts[0][0], parts[1]
        if not (path.startswith("announce/") and path.lower().endswith(WATCH)):
            continue
        if kind == "D":
            out.append(f"{path} (gelöscht)")
        elif kind == "R":
            out.append(f"{path} (umbenannt)")
    return out


def main() -> int:
    found = violations(sys.stdin.read().splitlines())
    if found:
        print("ROT: Ankündigungen dürfen im Repo nicht gelöscht oder umbenannt werden (Entscheid des Nutzers 23.11.2026):")
        for f in found:
            print("  - " + f)
        print("Bitte die Datei(en) wiederherstellen (git checkout <vorher> -- <Datei>). Eine neue Fassung = neue Datei.")
        return 1
    print("OK: keine Ankündigung gelöscht oder umbenannt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
