# BuffSentinel – Stand der Sitzung

## Stand 23.11.2026 12:45 · Version 0.9.61
Veröffentlicht (download/, announce/, Discord). Bericht: berichte/BuffSentinel/2026-11-23-0843-0.9.61-livedaten-lesbarkeit.txt

## Gerade in Arbeit
Nichts. Alle offenen Punkte aus offen-buffsentinel.txt bis 23.11. 08:14 sind in 0.9.61 umgesetzt, zur Prüfung.

## Nächste Schritte (Reihenfolge)
1. Ingametest 0.9.61 abwarten (Prüf-Sitzung): T149 zeigt je Anker Grösse/Ankerpunkte/Skalierung -> Ursache "leere Anker klein: nein"
   (PC zu Hause) belegen und beheben, mit Test für genau diese Lage (TU1).
2. T266 (Lesbarkeit) Ergebnisse aus dem Spiel auswerten (im Nachbau nicht prüfbar).
3. T264 (Livedaten) Ergebnis aus dem Spiel prüfen.
4. T249: Zeilenzahl der Prüfliste im Spiel messen (GetNumLines) statt Annahme 95 Zeichen/Zeile.

## Offen beim Nutzer
- Zugriff auf das Daten-Repo (Desktop-Stand) wurde dieser Sitzung verweigert – für T149 nötig, falls der nächste Lauf nicht reicht.
- Prüfliste von Hand (JAEGER, ENTZ, OPT u. a.); T247 Händler läuft von selbst.

## Entscheide des Nutzers seit letztem Stand
- 23.11. 07:50: Pause aufgehoben, Nutzung sparen ohne Qualitätsverlust.
- 23.11. 08:13: Stand je Sitzung in dieser Datei sichern.
- 23.11. 11:36: in announce/ nie etwas löschen (Skript angepasst, bricht bei Löschung ab); 12:03: alte nicht wiederherstellen.

## Wichtig zu wissen
- Quelle: /home/claude/BuffSentinel (kein Git), Veröffentlichung über raidmaster (Skripte rel.sh/rep.sh im Arbeitsordner der Sitzung).
- Offline-Nachbau: berichte/BuffSentinel/offline/run_offline.lua, erwartete Nachbau-Abweichungen T13 T23 T28 T45 T51 T95 T266.
- Locales werden mit einem Generator erzeugt (keys/manual/extra.json im Arbeitsordner), 1232 Schlüssel je Sprache.
- Shared-Dateien nur unverändert kopieren (Sync 3, Markt v10, Dev v2); GoldSentinelTakt nutzt BuffSentinel nicht.
- Marktspeicher kann BuffSentinelDB.gsMarkt sein (echte Daten, nicht in der Sandbox) – T264 sichert und vergleicht ihn.
