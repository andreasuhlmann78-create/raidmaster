# Stand GuildSentinel – 23.11.2026 09:41 · Version 0.9.60 (Discord)

## Gerade in Arbeit
- Nichts. 0.9.60 veröffentlicht (Discord), Bericht berichte/GuildSentinel/2026-11-23-0940-version-0.9.60-schaetzwerte-l5-belege.txt.

## Nächste Schritte (Reihenfolge)
1. Prüfung 0.9.60 durch die Prüf-Sitzung; nicht warten: offen-guildsentinel.txt weiter abarbeiten.
2. Offen: RP/RV (im Client bestätigen), CH-G (später, nach AHSentinel).
3. G-4a gilt erst als erledigt, wenn im Spiel keine "LANGSAM Seite members" > 16 ms mehr kommt.

## Offen beim Nutzer
- Ingametest 0.9.59/0.9.60: /gs testroutine alles (Umgebung, SHARED, T311–T319); Platzhalter-Knopf, gewählte Zeile am Bild.
- CurseForge 0.9.59+ erst nach diesem Ingametest (Supervisor 09:27), nicht automatisch um 18:00.

## Entscheide des Nutzers seit letztem Stand
- 23.11. 09:27 (Supervisor): L7 nicht anwendbar angenommen; L5 für jeden Tooltip mit Zahlen; GS-S1/GS-S2 freigegeben (umgesetzt in 0.9.60).

## Wichtig zu wissen
- Gildenschlüssel "@Fraktion|Gilde"; alte Daten in guildsOld; Protokoll nennt Einträge je altem Schlüssel.
- RaidReady: unter 3 Spielern oder 7 Tagen keine Wochenzahl; Race:Gain zählt die Beitritts-Stufe nicht.
- "return nil, Grund" in einer Prüfung = SKIP. Testroutine misst zuerst 10 s Umgebung.
- Offline: test/run_alle.sh 229 Läufe, 16947 Einzelprüfungen (RO=1 für den Abgleich).
