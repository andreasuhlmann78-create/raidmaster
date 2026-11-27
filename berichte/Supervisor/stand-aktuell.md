# Stand Supervisor – 27.11.2026 07:08

## Gerade in Arbeit
- Warte auf Berichte AHS (AHS-W1 Teil 2: AH-STATE Rest 3,4 ms, Frames vorbauen) und LP (LP-I3: 189 µs je Knoten in Zone 1458) – beide angestossen 16:08.

## Nächste Schritte (Reihenfolge)
1. Bei jedem "repo": pull, neue berichte/ prüfen, annehmen/ablehnen in offen-*.txt, push + nachprüfen.
2. AHS: W1 Teil 2 (≥ 90 % zugeordnet, erstes Öffnen ≤ 6 ms), cache:warm mit "davon Bereinigung", T459 zwei Werte, AHS-BP1, AHS-S216, AHS-MK1, SK1-e/f.
3. LP: LP-I3 (T155 Ø 19,9 ms, Ziel < 16), LP-R2 lange Luftlinien über Orte meiden; Virtual.lua:545 (niedrig).
4. PS 0.9.91 nach Diagnose "fremd/eigener Code" (Wollcape), dann BP1. GS: Abnahme 0.9.64/65 im Spiel, CF erst danach. BS: Abnahme 0.9.68.
5. SH-M1 (eigene Aufgabe): GoldSentinelMarkt.DiagLines leicht parsen (16,4 -> 6,8 ms, 2,8 MB -> 5 KB, gleiche Zahlen gemessen) – Entscheid Nutzer offen (A jetzt / B gebündelt, empfohlen B).
6. CF: Kommentare bei jeder CF-Version und täglich lesen und beantworten (ohne Vorzeigen, danach loggen und melden). 18:00-Upload weiterer Versionen: vorher fragen.

## Offen beim Nutzer
- Offizier B (alter Uploader < 2.3.15, letzte Daten 22.11., wird seit Mindestversion 2.3.20 nicht mehr angenommen): einmal von Hand auf 2.3.28 bringen nötig (alter Uploader kann sich nicht selbst aktualisieren; kein heimlicher Weg). Kurzanleitung vorbereiten und dem Nutzer zeigen – ERST auf sein Zeichen (Nutzer 27.11. 07:08 "halte das fest aber mache noch nichts"). Offizier A ist auf 2.3.28 (liefert).
- Entscheid SH-M1 (A/B).
- Offiziere: alter Uploader – warten (nicht erinnern).
- 09.12. 07:00 Erinnerung: Aufgabe "Raids und Taktiken" wieder einschalten.

## Entscheide des Nutzers seit letztem Stand
- 26.11. 11:57: BuffSentinel darf goldsentinel-daten lesen (im BS-Chat erteilt).
- 26.11. 12:59: Discord-Bot soll ihm keine PN zu neuen RaidMaster-Versionen mehr schicken (/addon-pn, Bot 1.5.198).

## Wichtig zu wissen (belegt 26.11.)
- GetRealmName()/GetNormalizedRealmName() in Forever seit ~21.11. leer -> Figuren-Doppel; AHS/PS/BS/GS haben zusammengeführt.
- GetMoney beim Ausloggen: /reload = echt, Charakter-Menü/Beenden = 0 (wirtschaft-forever.md 1a).
- AHS-TB1/TB1-b, AHS-DL1, LP-TR3, LP-I7, PS-REALM, BS-B1 erledigt. Gold alle Figuren 60g 49s 77c im Spiel bestätigt.
- Laptop: Bild in Ruhe ~33 ms (30 Bilder/s). LP Reisen 860 s (3.13.21).
- Nutzer unter der Woche tagsüber am Laptop. AHS-Testroutine: Vollscan starten, dann /ahs testroutine während er läuft.
