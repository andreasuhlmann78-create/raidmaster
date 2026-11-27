# LevelPilot – Stand der Sitzung

## Stand 27.11.2026 10:29 · Version 3.13.26 (veröffentlicht, Discord; ST1 angenommen 10:30, Abnahme im Spiel offen)

## Gerade in Arbeit
- In der Arbeitskopie (für die nächste Version, nicht veröffentlicht): Einlog-Zeile "LevelPilot 3.13.x – …" ohne Doppelpunkt
  (Supervisor 10:30 NIEDRIG, LP:Print(msg, plain)); im Nachbau geprüft.
- DL-ABN (HOCH, 10:30): download/ nur mit angenommener Version – LevelPilot liegt dort nicht; wird so eingehalten (= LP-DL1).

## Nächste Schritte (Reihenfolge)
0. LP-DL1: nach jeder Annahme (mit Ingametest ohne offenes HOCH) die angenommene Zip als download/LevelPilot-<Version>.zip, ältere entfernen,
   addon_check, Workflow grün, Bericht.
1. Entscheid "Wo war ich?" beim Einloggen (Frage im ST1-Bericht Punkt 4) umsetzen, sobald er da ist.
2. Ingametest 3.13.24–3.13.26 auswerten: Takt (keine Bilder > 40 ms), reiseBilder, T155/planungen, Protokoll-Fenster, T399, Einloggen.
3. LP-I3 (falls T155 im Spiel > 16 ms), LP-R2, LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse, Wegabschnitte.

## Offen beim Nutzer
- Frage: "Wo war ich?" beim Einloggen (eigener Schalter, ab Werk an, 2–5 Zeilen) – bleiben oder ab Werk aus?
- Ingametest (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK), danach /reload für den Upload.
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen seit 09:37. Gültig: ST1-Regeln A–E (27.11. 08:27–09:23), Protokoll 60 Einträge (08:27), LP-DL1 (~07:25).

## Wichtig zu wissen
- ST1 gilt nur ausserhalb des Testmodus (LP:IsDev()): LP:LoginLine, LP:ErrorNotice (LP.errorNoticeShown), Se:CorpseTip (db.corpseTipShown),
  Ce.ChannelLabel/ProtocolLabel; Mithelfen-Abschnitt unten in Austausch (shareSeed, protocol).
- Skripte im Scratchpad: m2c.sh (ganze Routine), login.lua (Einloggen, Chat zählen; BRAKE=1 SVACC=… für Notbremse), msl.sh, r3.lua, mcfp.sh.
- Offline: python3 berichte/LevelPilot/offline/run_offline.py <zip> (40 Läufe).
- Upload 27.11. 06:47: /home/claude/lpdaten-2711b. Ältere Versionen: /home/claude/lpalt/<Version>.
- T261 im Nachbau rauscht (1 000–1 300 ms).
