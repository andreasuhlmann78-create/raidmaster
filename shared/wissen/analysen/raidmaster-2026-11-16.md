ANALYSE – NUR FESTGEHALTEN, KEIN AUFTRAG – Fehler werden erst nach Freigabe des Nutzers behoben

# RaidMaster (Addon) + Uploader – Nacht-Analyse (Supervisor, 15.11.2026 abends)

Geprüft: RaidMaster 3.0.26 (download/RaidMaster-3.0.26.zip), RaidMasterUploader (Ordner RaidMasterUploader/ im raidmaster-Repo).
Geschichte: das raidmaster-Repo selbst (2268 Commits), auftraege/RaidMaster/, berichte/RaidMaster/.

## Was ich gemacht habe
- addon_check RaidMaster 3.0.26: OK, 1 Warnung "GoldSentinelMarkt.lua veraltete offizielle Fassung (Version 2) – Version 6".
- Uploader-Tests (RaidMasterUploader/tests/test_daten.py): 12/12 OK.
- Geheimnisse: RaidMasterBot/config.json und RaidMasterUploader/uploader_config.json stehen in .gitignore und waren NIE im
  Repo (git log --all leer) – gut, keine Tokens im öffentlichen Repo.
- Spiel-Profiler (GSSniperLog 15.11.): RaidMaster Ø 0,00 ms, Spitze 3 ms – unauffällig.

## Befunde
### R-1 GoldSentinelMarkt v2 (MITTEL) – älteste Fassung aller Addons (Feed in einem Stück, viel Speicher, MN-S2 offen).
### R-2 Offene Prüfpunkte (aus offen-raidmaster.txt, unverändert): UP-S1 / UP-S1-2 HOCH (Uploader: unlesbarer bzw. älterer
    Stand eines anderen Rechners kann den gemeinsamen Stand überschreiben – Daten-Sicherheit), T90 (Fehler unter enUS in der
    Nachbildung), UP-v3 Test. Diese HOCH-Punkte sind die wichtigsten Risiken dieses Projekts (Datenverlust).
### R-3 Im Raid nicht gemessen (Hinweis): Leistung nur im AH gemessen. Ein Protokoll aus einem Raidabend fehlt.
