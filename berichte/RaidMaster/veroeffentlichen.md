# Veröffentlichen – Ablauf der RaidMaster-Sitzung (RM-CI1, 25.11.2026)

Gilt für jede neue Addon-Version (RaidMaster-<Version>.zip) und jeden neuen Uploader (RaidMasterUploader.zip).

1. `git pull --rebase`, `git log --oneline -5 -- auftraege/RaidMaster/` – höchste veröffentlichte Version prüfen.
2. Neue Zip bauen; `python3 addon-check/addon_check.py download/RaidMaster-<Version>.zip` -> kein FEHLER.
3. **Vorige Zip entfernen:** `git rm download/RaidMaster-<vorige>.zip` – in download/ liegt je Addon nur die neueste
   (sonst meldet die Prüfung "Version … ist NIEDRIGER als schon veröffentlichte …" und jeder Lauf ist rot).
   RaidMaster-latest.zip = Kopie der neuesten (Inhalt gleich), announce/ bleibt.
4. README.md "Aktuelle Version" auf die neue Zip setzen (der Link der alten führt sonst ins Leere).
5. Ganze Prüfung wie der Workflow: `python3 addon-check/addon_check.py --report <Arbeitsordner>/b.md` -> Exit 0, kein FEHLER.
6. Nach `git pull --rebase` und VOR dem Push nochmals `git log -3 -- auftraege/RaidMaster/` lesen – kam ein neuer Auftrag, erst
   prüfen, ob er der Veröffentlichung widerspricht (25.11.: 3.0.46 trotz Entscheid 08:24 gepusht).
   Commit, push, `git fetch -q && git status -sb` (kein "ahead"), `git show origin/main:<Datei>` prüfen.
7. **Workflow-Status prüfen:** `gh run list --workflow "Addon-Prüfung" -L 3` – der Lauf zum eigenen Commit muss "success" sein
   (ein "cancelled" wegen eines neueren Commits zählt nicht; dann den neueren abwarten). Bei "failure": sofort Ursache in
   addon-check/bericht.md suchen und beheben.
8. Discord: announce/ (sofort). Bericht in berichte/RaidMaster/, stand-aktuell.md neu schreiben.
