# Stand GuildSentinel – 23.11.2026 08:43 · Version 0.9.59 (Discord)

## Gerade in Arbeit
- Nichts offen in Arbeit. 0.9.59 veröffentlicht (Discord), Bericht berichte/GuildSentinel/2026-11-23-0842-version-0.9.59-realm-g4a-lesbarkeit.txt.

## Nächste Schritte (Reihenfolge)
1. Prüfung 0.9.59 durch die Prüf-Sitzung abwarten – dabei nicht warten: offen-guildsentinel.txt weiter abarbeiten.
2. Offen aus offen-guildsentinel.txt: RP/RV (im Client bestätigen), CH-G (später, nach AHSentinel).
3. Entscheide offen aus dem Bericht 0.9.59: L5/L7 als "nicht anwendbar" ok?; Schätzwerte (RaidReady "~n Wochen" mit n, First60 kennzeichnen).

## Offen beim Nutzer
- Ingametest 0.9.59: /gs testroutine alles (Zeilen "Umgebung", SHARED, T311–T319); Platzhalter-Knopf und gewählte Zeile am Bild.

## Entscheide des Nutzers seit letztem Stand
- 23.11. 07:50: Pause aufgehoben, Nutzung sparen (bündeln, kurze Berichte, Tests nie auslassen).
- 23.11. 08:13: Stand je Sitzung in dieser Datei sichern.

## Wichtig zu wissen
- Gildenschlüssel ist jetzt "@Fraktion|Gilde" (ohne Realm); alte Daten in GuildSentinelDB.guildsOld.
- Testroutine misst zuerst 10 s Umgebung; Offline-Tests rücken dafür 10 s weiter (wowmock: Umgebungsrahmen im Takt-Bild).
- "return nil, Grund" in einer Prüfung = SKIP (seit 0.9.59), nicht OK.
- Offline: test/run_alle.sh 223 Läufe, 16853 Einzelprüfungen (RO=1 für den Abgleich Lauf für Lauf).
- CurseForge (download/) nur um 18:00 und nur mit OK des Nutzers.
