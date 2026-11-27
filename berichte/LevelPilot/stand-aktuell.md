# LevelPilot – Stand der Sitzung

## Stand 27.11.2026 09:37 · Version 3.13.25 (veröffentlicht, Discord; Prüfung offen)

## Gerade in Arbeit
- ST1 Spieler-Texte (MITTEL, auftraege/anweisung-spielertexte-2026-11-27.txt): Bestandsaufnahme der Chat-Ausgaben (39 Stellen) und der
  Zentrale (Daten, Austausch, Extras) gemacht, Änderungen noch nicht angefangen.
- 3.13.25 = Protokoll-Fenster neueste 60 Einträge + „Alles kopieren“ (Entscheid 08:27), Bericht 27.11. 09:37.

## Nächste Schritte (Reihenfolge)
0. LP-DL1: nach jeder Annahme (mit Ingametest ohne offenes HOCH) die angenommene Zip als download/LevelPilot-<Version>.zip, ältere entfernen,
   addon_check, Workflow grün, Bericht.
1. ST1 umsetzen (nur ausserhalb des Testmodus, LP:IsDev()):
   A eine Einlog-Zeile "LevelPilot <Version> – …" (Core.lua Login); Wege-Hinweis und Optionstipp sind schon einmalig.
   B Abschnitt "Mithelfen" in Extras (Fehler-Protokoll mitschreiben, Wegdaten senden, Startdatenbank, Flüster-Netz-Schalter mit neuem Text);
     "GoldSentinelSync, 1 Std." weg; Schlüssel bleiben.
   C LP:Error und Modul-Startfehler: 1 Zeile je Sitzung, Einzelheiten ins Protokoll.
   D Zähler/Technik in Daten/Austausch nur im Testmodus (Diagnose-Knopf, Warteschlange …); Notbremse-Zeile nur ins Protokoll.
   Offene Frage an den Nutzer: "Wo war ich?" beim Einloggen (Spieler-Schalter, ab Werk an) – bleibt oder zählt als zweite Zeile?
2. Ingametest 3.13.24/3.13.25 auswerten: Takt (keine Bilder > 40 ms), reiseBilder, T155/planungen, Protokoll-Fenster.
3. LP-I3 (falls T155 im Spiel > 16 ms), LP-R2, LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse, Wegabschnitte.

## Offen beim Nutzer
- Ingametest (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK), danach /reload für den Upload.
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- 27.11. 08:27: Protokoll-Fenster nur neueste 60 Einträge, ganzer Text bleibt zum Kopieren und für den Uploader (umgesetzt 3.13.25).
- 27.11. 08:27–09:23: ST1-Regeln A–E, nur ausserhalb des Testmodus; Hilfe-Listen, Tooltips, Bildschirmmitte, Töne, Nachrichten an
  andere Spieler nicht anfassen.
- 27.11. ~07:25: LP-DL1 (angenommene Zip nach download/).

## Wichtig zu wissen
- Skripte im Scratchpad: m2c.sh (ganze Routine, Daten 26.11.), msl.sh (lange Reise), r3.lua (Reise am Stück), mcfp.sh (Wegprüfung).
- Offline: python3 berichte/LevelPilot/offline/run_offline.py <zip> (40 Läufe, ~5 Min.).
- Upload 27.11. 06:47 entpackt: /home/claude/lpdaten-2711b (281 Protokolleinträge). Ältere Versionen: /home/claude/lpalt/<Version>.
- Prüfungen speisen über TR.Injecting ein; nur echter Empfang wartet (Comm.routineHeld).
- T261 im Nachbau rauscht (1 000–1 300 ms).
