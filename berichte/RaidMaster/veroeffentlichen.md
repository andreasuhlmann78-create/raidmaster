# Veröffentlichen – Ablauf der RaidMaster-Sitzung (RM-CI1 25.11., DL-ABN 27.11.2026)

Gilt für jede neue Addon-Version (RaidMaster) und jeden neuen Uploader (RaidMasterUploader).
DL-ABN: download/ enthält NUR vom Supervisor angenommene Versionen – der Uploader installiert jede Zip dort bei allen Mitspielern.

## Addon RaidMaster
1. `git pull --rebase`, `git log --oneline -5 -- auftraege/RaidMaster/` – höchste veröffentlichte Version prüfen.
2. Zip bauen (= Ordner RaidMaster/); `python3 addon-check/addon_check.py <zip>` -> kein FEHLER.
3. ZUERST NUR announce/ (Discord-Testversion, Kanal "test" des Nutzers, Prüfung):
   `announce/raid-addon__raidmaster-<Version>.RaidMaster.zip` + `announce/raid-addon__raidmaster-<Version>.md` (kurzer deutscher Text:
   was neu ist, Installation). announce/ nie löschen (announce-guard).
4. NICHT nach download/, README "Aktuelle Version" noch nicht ändern. Bericht mit md5 der Zip.
5. Erst wenn in offen-raidmaster.txt "ANGENOMMEN" für GENAU diese Version steht: dieselbe Zip (md5 gleich) als
   `download/RaidMaster-<Version>.zip` + `download/RaidMaster-latest.zip`, vorige `download/RaidMaster-*.zip` entfernen (git rm),
   README-Link nachführen.
6. Ganze Prüfung wie der Workflow: `python3 addon-check/addon_check.py --report <Arbeitsordner>/b.md` -> Exit 0, kein FEHLER.
7. Nach `git pull --rebase` und VOR dem Push nochmals `git log -3 -- auftraege/RaidMaster/` lesen – kam ein neuer Auftrag/Entscheid,
   erst prüfen, ob er der Veröffentlichung widerspricht (25.11.: 3.0.46 trotz Entscheid 08:24 gepusht).
8. Commit, push, `git fetch -q && git status -sb` (kein "ahead"), `git show origin/main:<Datei>` prüfen.
9. Workflow: `gh run list --workflow "Addon-Prüfung" -L 3` – Lauf zum eigenen Commit "success" ("cancelled" durch neueren Commit zählt nicht).
10. Bericht in berichte/RaidMaster/, stand-aktuell.md neu schreiben.

## Uploader (RaidMasterUploader)
Jeder Uploader liest die neueste Version aus `RaidMasterUploader/uploader.py` auf main (raw HEAD) und die Zip aus download/.
Darum darf KEINE ungeprüfte Uploader-Änderung auf main: weder Ordner noch Zip.
1. Arbeit auf einem Zweig `pruefung/uploader-<Version>` (Ordner RaidMasterUploader/ + download/RaidMasterUploader.zip, Tests grün),
   pushen, Bericht auf main mit Zweigname, Commit und md5 der Zip.
2. Erst nach "ANGENOMMEN" für genau diese Version: Zweig in main übernehmen (fast-forward bzw. merge), push, prüfen.
3. Ausnahme nur auf ausdrücklichen Entscheid des Nutzers (im Bericht nennen).
