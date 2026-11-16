"""Test: Kurzfassung des CurseForge-Changelogs (upload.py changelog_override). Aufruf: python3 -I curseforge/test_changelog_override.py"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import upload  # noqa: E402
ok = fail = 0
def check(n, c):
    global ok, fail
    ok, fail = (ok + 1, fail) if c else (ok, fail + 1)
    if not c: print("FEHLT:", n)
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    check("keine Datei -> None", upload.changelog_override("AHSentinel", "0.65.260", d) is None)
    (d / "AHSentinel-changelog-0.65.260.md").write_text("  \n", encoding="utf-8")
    check("leere Datei zählt nicht", upload.changelog_override("AHSentinel", "0.65.260", d) is None)
    (d / "AHSentinel-changelog-0.65.260.md").write_text("## What's new\n- Posting works again\n", encoding="utf-8")
    check("Datei -> genau dieser Text", upload.changelog_override("AHSentinel", "0.65.260", d) == "## What's new\n- Posting works again")
    check("andere Version -> None", upload.changelog_override("AHSentinel", "0.65.261", d) is None)
    check("anderes Addon -> None", upload.changelog_override("GuildSentinel", "0.65.260", d) is None)
print(f"{ok}/{ok + fail} Prüfungen bestanden"); sys.exit(1 if fail else 0)
