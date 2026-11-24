# LevelPilot – Stand der Sitzung

## Stand 24.11.2026 18:55 · Version 3.13.13 (veröffentlicht, Discord, md5 e129bd88c92c04c33ba229f3cc494008)

## Gerade in Arbeit
- Nichts angefangen. 3.13.13 gepusht. Bericht: berichte/LevelPilot/2026-11-24-1357-3.13.13-lp-i1-i8.txt (umgesetzt, zur Prüfung).
- Inhalt:
  - Reise-Bilder bis 867 ms: Jobs.JourneyPCall, Freigabe über Pausen, Zeitgeber jedes Bild, SLICE_CALLS 32.
  - T144 kalte Neuplanung als Coop.
  - T386 Coop.
  - Feld langeStuecke.
  - LP-I8: questRate zur Reise; T381 mit festem Erholungsbonus.

## Nächste Schritte (Reihenfolge, Auftrag 24.11. 13:04: LP-I1 -> LP-I6 -> LP-I7 -> LP-I8)
1. Datei der Figur abwarten (Nutzer gefragt 13:35), dann mit ihr nachbauen. Der Nachbau braucht dafür LevelPilotCharDB (Harness
   erweitern: Datei laden).
2. LP-I6 HOCH: Einloggen 1255 ms (nav/navplan 521 ms/133×, route 367, graph 222) – Ursache "nav" belegen.
3. LP-I7: T150 Median 17,99 ms (ersterweg 7,82), T263 längste Portion 46,5 ms.
4. LP-I1 Rest: T128 97, T136 59, T355 45, T29/T28 43, T251 39 – nach Ingametest 3.13.13 über langeStuecke bzw. mit den Daten der Figur.
5. LP-K1 geprüft (Bericht 18:55: LevelPilot weicht nicht aus, Vorschlag: so lassen – Entscheid offen). Blueposts Reittempo geprüft:
   gemessen, kein Handlungsbedarf. Offen: Notbremse "Routenberechnung", Wegabschnitte.

## Offen beim Nutzer
- Datei der Testfigur: WTF\Account\<Konto>\<Realm>\<Figur>\SavedVariables\LevelPilot.lua (nur lokal, nie ins Repo).
- Ingametest 3.13.13 (langeStuecke, ganzeBilder bei Reisen, T381 Bonus, T388, Dauer).
- Entscheid T31/T32 (einmal neu planen): keine Antwort.

## Entscheide des Nutzers seit letztem Stand
- 24.11. 18:51: "bitte immer auf deutsch" (Antworten an den Nutzer immer Deutsch – Bestätigung des Entscheids 23.11. 08:36).
- Prüf-Sitzung 24.11. 14:10: 3.13.13 angenommen, Abnahme im Spiel offen; Weg für die Daten der Figur klärt der Supervisor mit dem Nutzer.
- Auftrag der Prüf-Sitzung 24.11. 13:04 (Ingametest 3.13.12): Reihenfolge LP-I1 -> LP-I6 -> LP-I7 -> LP-I8.

## Wichtig zu wissen
- Daten Ingametest 3.13.12: goldsentinel-daten origin/sicherung, aktuell/AUSPLUSLAPTOP/forever/konto-5cb3d536/LevelPilot.lua.gz
  -> /home/claude/lpdaten-2411b/ (bericht.json = GSTEST1 3.13.12). Den lokalen main von goldsentinel-daten nicht zurücksetzen.
- Skripte im Scratchpad:
  - Ganze Routine: m3.sh (Stufe 30 Laptop), m.sh (MININT), m2.sh (Priester 10).
  - mj1/mj3.sh + prof_journey.lua: Reise-Portionen (SLICEN=…).
  - md3.sh + prof_det.lua: Spur je Reiseschritt (zeichnet mitten im Schritt auf, nur grob).
  - mp3.sh: Stapel längstes Bild.
  - p3w.sh + probe_144*.lua: Einzelmessungen.
- Nachbau-Rauschen: T261 schwankt um 1000 ms. Zwei Läufe gleichzeitig verfälschen Zeiten und T381 (Zeitbudgets der Planung).
- 3.13.13 neu:
  - Jobs.JourneyPCall; V.pausedYieldOK; Ticker 0.001; V.SLICE_CALLS 32; NoReplan(body, clean).
  - TR.GapNote/langeStuecke; opts.rested; saved.questRate.
- Verdacht, zu messen: Routine im Spiel länger (Reisen in kleinen Portionen). Nachbau 827–930 s statt 200 s.
