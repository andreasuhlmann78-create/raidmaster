# Stand Supervisor (Prüf-Sitzung, Projekt «Addonprüfer»)

## Stand 24.11.2026 06:27 · Versionen geprüft: AHS 0.65.385 · LP 3.13.10 · PS 0.9.78 · TS 2.5.26 (Ingame) · GS 0.9.60 · BS 0.9.61 · Uploader 2.3.18 · Bot 1.5.192
Sitzung seit 23.11. 06:18. Repos: raidmaster, goldsentinel-daten (schreiben); ahanalyzerpro, professionsentinel, guildsentinel (lesen).

## Gerade in Arbeit
- nichts Laufendes. Ingametests 23.11. alle ausgewertet (TS, BS, GS, AHS PM1-a, PS, LP) – Befunde in den offen-*.txt.

## Nächste Schritte (Reihenfolge)
1. Prüfen: AHSentinel 0.65.386 + 0.65.387 + Bericht AHS-I4 (712 ms: "eigene Arbeit 2 ms, Spiel 710 ms" – nachprüfen).
2. Prüfen: LevelPilot 3.13.11 (LP-I1, LP-I2, LP-I4, LP-I5). ProfessionSentinel 0.9.79 (liegt im Repo, noch nicht geprüft).
3. Testberichte 23.11. 23:50 (neu im Repo) gegen die Chat-Berichte abgleichen.
4. Warten auf: RaidMaster UP-TAGE (Tage 14.–20.11. im Daten-Repo weg) -> dann Markt-Tabellen-Entscheid (siehe unten).
5. SH-UTF8 NIEDRIG (eigene Aufgabe): shared/GoldSentinelTest.lua:83 kürzt nach Bytes – mit nächster Änderung an der Datei bündeln.
6. Prompt "Markt-Überwachung (wöchentlich)" (nächster Lauf 30.11.) auf .lua.gz hinweisen (Markt-Tabellen ist angepasst).

## Offen beim Nutzer
- CurseForge-Zwischenstand CF1–CF3 (Entwurf berichte/Supervisor/2026-11-23-1605-…): OK gegeben 24.11. 06:17, Posten scheiterte – in Chrome
  NICHT bei CurseForge angemeldet. Nutzer meldet sich an, sagt "angemeldet", dann posten (Claude in Chrome) und Erscheinen prüfen.
- PS-Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS, Rezept wählen + herstellen; Anleitung im Chat 23.11. 16:02).
- LevelPilot "Wegabschnitte": eine Sitzung draussen mit Laufen.
- Uploader 2.3.18 auf PC (DESKTOP-NVITMSE) und bei beiden Offizieren (stand.json "uploader" dort leer = alt).
- Alte Addon-Ordner auf dem Laptop löschen: AddOns/_GoldSentinel_Update_2026-11-23 (kein Löschrecht für Claude).
- Offen alt: "kleine KI" AHS (14.11.), Erstkill-Meldungen unter Rekord-Tafeln.

## Entscheide des Nutzers seit letztem Stand (alle in shared/wissen/entscheide.md)
- 24.11. 06:17 "ok": CF-Zwischenstand posten; Markt-Tabellen warten auf UP-TAGE (höchstens 1 Tag) statt Fallzahl-Regel aussetzen.
- 23.11.: 09:59 Bot-Rolle (Discord-Sitzung, vorsichtig) -> 10:32 so belassen; 10:16 Gäste in Mitglieder-Kanäle; 10:49 Doppel der geplanten
  Aufgaben aus (Nachprüfung AUS); 11:36 announce/ nichts löschen; 11:45 gelöschte Ankündigungen wiederherstellen; 12:03 alte Versionen nie
  wieder posten; 12:48 neue Version ersetzt alten Discord-Beitrag (wie bisher); 14:04 Laptop unter der Woche, PC am Wochenende.

## Wichtig zu wissen
- Laptop = AUSPLUSLAPTOP (Forever: C:\Program Files (x86)\World of Warcraft\_forever_\Interface\AddOns, Zugriff am 23.11. erteilt).
  Am 23.11. alle neuen Versionen dort installiert und gegen die Zips geprüft (441 Dateien).
- Daten-Repo: jede Lieferung = 1 Commit ohne Vorgänger (DU6, so gewollt); höchstens 7 Tage + 200 MB (ältere Tage fallen weg).
  Uploader 2.3.18 packt grosse Dateien (.lua.gz). Markt-Werkzeuge lesen .gz (sv_lesen, Test addon-check/test_sv_gz.py).
- Testberichte kommen über Discord #testberichte; Abholung per Workflow testberichte.yml (:17/:47 UTC; von Hand: gh api … dispatches).
- Ingametests in der Hauptstadt: "Umgebung" (Bild in Ruhe) lesen, bevor Ruckeln einem Addon angerechnet wird. Harte Grenze 40 ms (leistung.md).
- Geplante Aufgaben AN: Markt-Tabellen, Markt-Überwachung, Blueposts, Rezeptdaten, Raids, Discord-Betreuung, Gmail. AUS: Nachprüfung (doppelt).
- CurseForge-Kommentare: Kommentarseite nur angemeldet lesbar -> Gmail-Benachrichtigungen (noreply@curseforge.com) lesen. Neueste: 22.11.
- AHS CurseForge-Upload gesperrt (Ingametest 0.65.385: 54 FEHLER, AHS-I1 Sandbox HOCH).
