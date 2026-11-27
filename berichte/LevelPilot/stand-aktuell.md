# LevelPilot – Stand der Sitzung

## Stand 27.11.2026 11:18 · Version 3.13.27 (veröffentlicht, Discord; Messversion, Prüfung offen)

## Gerade in Arbeit
- Nichts angefangen. 3.13.27 = Messung T217 (Teile, Bildwechsel, Hintergrund-Aufgaben) und T136 (Protokoll Text/Fenster), Einlog-Zeile ohne
  Doppelpunkt (Bericht 27.11. 11:18).

## Nächste Schritte (Reihenfolge)
1. HOCH T215–T217 143,5 ms (Ingametest 3.13.26): mit den Messzeilen aus dem nächsten Ingametest die Ursache belegen, dann beheben (Ziel ≤ 16 ms).
   Belegt bisher: im 157-ms-Bild rechnete die Routine nur 6,8 ms, 150 ms "Spiel/Umgebung" (+2,3 MB). Widerlegt: Stufenbänder (Nachbau),
   Wegfaktor-Messung (läuft als eigene Aufgabe).
2. MITTEL T136 (Protokoll öffnen 48,6 ms), T355 40 ms, T244, T386, T285 (~33 ms); T155 Ø 21,2 ms (Ausreisser 68 ms, Zone 1458).
3. LP-DL1 / DL-ABN: download/ erst, wenn T215–T217 ≤ 40 ms belegt und der Supervisor die Version angenommen hat.
4. Entscheid "Wo war ich?" beim Einloggen (Frage ST1-Bericht Punkt 4).
5. LP-R2, LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse, Wegabschnitte. Auffällig: Bereich J allein im Nachbau T298–T300 474–512 ms (ganze Routine nicht) – prüfen.

## Offen beim Nutzer
- Ingametest 3.13.27 (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK), danach /reload für den Upload.
- Frage: "Wo war ich?" beim Einloggen (eigener Schalter, ab Werk an, 2–5 Zeilen) – bleiben oder ab Werk aus?
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen. Gültig: ST1-Regeln A–E, Protokoll 60 Einträge, LP-DL1/DL-ABN (download/ nur angenommen).

## Wichtig zu wissen
- Uploads: goldsentinel-daten origin/sicherung, aktuell/AUSPLUSLAPTOP/forever/konto-5cb3d536/LevelPilot.lua.gz; Bericht mit lupa aus
  LevelPilotDB.gsTest.reports (GSTEST1-Text, Bereich "alle"). Upload 11:10 entpackt: /home/claude/lpdaten-2711c (bericht.json = 3.13.26).
- Skripte im Scratchpad: m2c.sh (ganze Routine), login.lua (Einloggen), lpdbg/ + m2dbg.sh (Messkopie), msl.sh, r3.lua, mcfp.sh.
- Offline: python3 berichte/LevelPilot/offline/run_offline.py <zip> (40 Läufe).
- T261 im Nachbau rauscht (1 000–1 300 ms).
