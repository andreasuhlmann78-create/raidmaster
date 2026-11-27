# LevelPilot – Stand der Sitzung

## Stand 27.11.2026 07:55 · Version 3.13.24 (veröffentlicht, Discord; Annahme offen)

## Gerade in Arbeit
- Nichts angefangen. Neu: Bericht 3.13.24 (T397 in Portionen, Gefahrenkarte vor der Prüfung bauen, NearSparse alle 64 Knoten, PlaceHit).
- 3.13.23 angenommen 27.11. 06:47; Ingametest 3.13.23: Takt-Rückschritt T217/T397 (HOCH) -> 3.13.24.

## Nächste Schritte (Reihenfolge)
0. LP-DL1 (Entscheid 27.11. ~07:25): nach jeder Annahme die angenommene Zip als download/LevelPilot-<Version>.zip, ältere entfernen, addon_check,
   Workflow grün, Bericht. Erste Ablage nach Annahme von 3.13.24.
1. Ingametest 3.13.24 auswerten: Takt (keine Bilder > 40 ms ohne Bereinigung), reiseBilder (Überschreitung), T155/planungen.
2. LP-I3: falls T155 im Spiel weiter > 16 ms – Speicher je Knoten senken (segCache-Teiltabellen), Grundregeln-Stück (Nachbau 30–141 ms) prüfen.
3. Anzeige-Texte: Protokolltext 100 KB / ~1 MB (gemessen, Bericht 27.11. 07:55); Vorschlag "neueste 60 Einträge im Fenster" wartet auf Entscheid.
4. LP-R2: lange Luftlinien über Orte meiden. 5. LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse, Wegabschnitte.

## Offen beim Nutzer
- Ingametest 3.13.24 (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK), danach /reload für den Upload.
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen. Gültig: Dauer der Routine nur ohne Nachteile verkürzen (25.11. 09:40); immer Deutsch (24.11. 18:51).

## Wichtig zu wissen
- Skripte im Scratchpad: m2c.sh (Daten 26.11. 11:16), m2.sh (ganze Routine Priester 10), msl.sh (lange Reise ohne Hülle, SLICE=…), msl16alt.sh (3.13.16 als Bezug),
  mres.sh/mypc.sh (mit Messhülle – Kosten wachsen mit Portionen, nicht für Dauervergleiche), r3.lua (Reise am Stück, MAXL, NOCFP, COMODE),
  mcfp.sh/mcfpp.sh (Wegprüfung CheckFirstPath), lo395.lua (Empfang + Ausloggen in der Routine).
- Upload 26.11. 09:33 entpackt: /home/claude/lpdaten-2711 (Upload 27.11. 06:47, bericht.json = 3.13.23 voll). Ältere Versionen: /home/claude/lpalt/<Version>.
- Prüfungen speisen über TR.Injecting ein; nur echter Empfang wartet (Comm.routineHeld).
- Den lokalen main von goldsentinel-daten nicht zurücksetzen.
- T261 im Nachbau: auf der neu gestarteten Arbeitsmaschine 1 100–1 300 ms auch mit 3.13.19 – Rauschen.
