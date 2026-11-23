# LevelPilot – Stand der Sitzung

## Stand 23.11.2026 08:35 · Version 3.13.7 (veröffentlicht, Discord)

## Gerade in Arbeit
- Nichts (3.13.7 gepusht, Bericht berichte/LevelPilot/2026-11-23-0835-3.13.7-montag.txt).

## Nächste Schritte (Reihenfolge)
1. Nächster Upload des Nutzers: die 5 Auffälligkeiten von 22.11. 17:05 (Notbremse "Routenberechnung") auswerten, Ursache belegen
   (Verdacht GC oder nicht abgebbarer Abschnitt; Nachbau mit Offiziersdaten: längste Portion 6,6 ms, nicht nachgestellt).
2. Lesbarkeit L1–L8 (auftraege/hinweis-ui-lesbarkeit-2026-11-20.txt) als Prüfung der Fensterzeilen bauen (Entfernungen grau = L1).
3. Auflage: Zeile "Wegabschnitte" nach echter Spielsitzung im Bericht.
4. Schätzwerte (Liste im Bericht 3.13.7) durch Messungen ersetzen.

## Offen beim Nutzer
- Entscheid T31/T32 (einmal neu planen) – gefragt, keine Antwort.
- Ingametest 3.13.7 (T150, neue Prüfungen T369–T375).

## Entscheide des Nutzers seit letztem Stand
- 22.11. 16:57/16:58 keine Wegsperren, ausser durch Orte der anderen Fraktion (umgesetzt 3.13.7).
- 23.11. 07:50 Pause aufgehoben, Nutzung sparen; 08:13 Stand je Sitzung sichern.

## Wichtig zu wissen
- Arbeitskopie /home/claude/lp31238/{LevelPilot,LevelPilot_Data}; nach Container-Neustart aus dem Zip in announce/ neu aufbauen.
- Lua 5.1 über lupa (pip), Wrapper scratchpad/lua51 -> run_offline.py --lupa. Nachbau: test40n.lua (GSOUT), mess_brake2.lua.
- Ortsliste der anderen Fraktion: berichte/LevelPilot/offline/orte-andere-fraktion-3.13.7.txt (Lücken: Steinkrallengipfel, Thalanaar, Valormok).
- 79007 Abgabe Westfall 37.5/50.7 (QDB.EXTRA_ENDS, Quelle warcraft.wiki.gg).
