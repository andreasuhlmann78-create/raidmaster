# LevelPilot – Stand der Sitzung

## Stand 23.11.2026 09:53 · Version 3.13.8 (veröffentlicht, Discord)

## Gerade in Arbeit
- Nichts (3.13.8 gepusht, Bericht berichte/LevelPilot/2026-11-23-0953-3.13.8-pruefung-3.13.7.txt).

## Nächste Schritte (Reihenfolge)
1. Auf die Prüfung von 3.13.8 durch die Prüf-Sitzung achten (offen-levelpilot.txt).
2. Nächster Upload des Nutzers: Notbremse "Routenberechnung" 22.11. 17:05 (5 Auffälligkeiten) auswerten, Ursache belegen.
3. Rest der Nicht-Wiederholbarkeit mit Nutzerdaten (0,003 %, Normal 3171856/3171965 s, erste Abweichung PRIO:TRAIN:12) weiter messen.
4. Zeit je Annahme/Abgabe messen (ersetzt die 30-s-Vorgabe der Zonenzeit).
5. Auflage: Zeile "Wegabschnitte" nach echter Spielsitzung.

## Offen beim Nutzer
- Ingametest 3.13.8 (T376–T382, T84 mit echter Welt).
- Entscheid T31/T32 (einmal neu planen) – gefragt, keine Antwort.

## Entscheide des Nutzers seit letztem Stand
- 23.11. 08:36: "immer auf Deutsch" (Erinnerung an die Regel, eingehalten).

## Wichtig zu wissen
- Arbeitskopie /home/claude/lp31238/{LevelPilot,LevelPilot_Data}; nach Container-Neustart aus dem Zip in announce/ neu aufbauen.
- Lua 5.1 über lupa (pip), Wrapper scratchpad/lua51 -> run_offline.py --lupa. Nachbau test40n.lua immer mit BRAKE=1 (sonst T262/T268 rot).
- Nachbau-Ersatzwelt gibt falsche Reisezeiten (T84 743 h); mit echten Kartenrahmen (WORLDHOOK/KARTENRAHMEN aus offline/lua/sim) 185 h.
- mock2.lua (offline/lua) ruft OnUpdate/Ereignisse jetzt in fester Reihenfolge (Wiederholbarkeit).
- Ortsliste: berichte/LevelPilot/offline/orte-andere-fraktion-3.13.8.txt. 79007 Abgabe Westfall 37.5/50.7.
