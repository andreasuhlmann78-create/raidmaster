# Stand Supervisor (Prüf-Sitzung, Projekt «Addonprüfer»)

## Stand 25.11.2026 13:31 · geprüft: AHS 0.65.398 · LP 3.13.14 · RM 3.0.48 · Uploader 2.3.28 · GS 0.9.62 · BS 0.9.64 · PS 0.9.83 · TS 2.5.30
Repos: raidmaster, goldsentinel-daten (schreiben); ahanalyzerpro, professionsentinel, guildsentinel (lesen). Nutzer tagsüber am Laptop (AUSPLUSLAPTOP).

## Gerade in Arbeit
- Ingametests mit dem Nutzer, eines nach dem anderen (kurz -> lang). Erledigt heute: RM 3.0.48 (11:18), AHS 0.65.398 (13:01). Nächster: LP 3.13.14.

## Nächste Schritte (Reihenfolge)
1. LP 3.13.14 Ingametest auswerten (virtuelle Reise: Sandbox-Zeilen HINWEIS/Schreibzugriffe; ganze Testroutine; Dauer).
2. Berichte der Sitzungen prüfen: AHS-OVF1 (integer overflow, HOCH), AHS-T14, RM-K2 (Ausweichen Charakterfenster), UP-DOC2, RM-CI2, LP-SB1-b, LP-R1/R2.
3. Testberichte bis RM-CI2 von Hand anstossen: gh api POST repos/…/raidmaster/actions/workflows/404904069/dispatches -f ref=main.
4. 18:00 CurseForge: AHS 0.65.398 NICHT (OVF1 offen); GS nur, wenn neue Version geprüft. Danach CF-Kommentare lesen (Regel 25.11. 11:09).
5. Offiziere: Lieferung mit Uploader 2.3.28 beobachten (12:35 noch alter Uploader abgewiesen).
6. 09.12. 07:00 Erinnerung: Raids-Aufgabe wieder einschalten (trig_01RKTpb8qD5PxK8Gb24pHnRK).

## Offen beim Nutzer
- LP 3.13.14 Ingametest (lang, Hintergrund). AHS erneut nach OVF1-Fix: Vollscan starten, währenddessen /ahs testroutine mit offenem AH.
- RM nach K2-Fix: Charakterfenster + /rm, Einstellungen + Esc. TS-Messung in Gruppe.
- Discord: Nitro-Geschenk-Dialog 11:5x versehentlich geöffnet, sofort geschlossen – Nutzer soll Bestätigungs-Mail NICHT anklicken, Zahlungen prüfen.

## Entscheide des Nutzers seit letztem Stand (in shared/wissen/entscheide.md eingetragen)
- 11:09 Spieler bekommen auf CurseForge immer eine Antwort (Entwurf, Ok, posten; 5 Antworten AHS 11:06 gepostet).
- 11:39 Offiziere schalten Addons-automatisch-an.bat ein (Nachtrag an beide gesendet 11:50/12:06, endo bestätigt 12:54).
- 09:40 LP-Test nur ohne Nachteile verkürzen. 08:24/08:26/08:29 Taktik-Zahlen, Raids ab 09.12., MC forever:true. 06:54/07:56 CF4/CF5.

## Wichtig zu wissen
- Discord im eingebauten Browser: Eingabefeld per JS fokussieren (aria-label "Nachricht an @…"), NIE auf berechnete Koordinaten klicken
  (Geschenk-Knopf daneben); bei schmalem Fenster erst Seite neu laden. Enter sendet, Shift+Enter neue Zeile; vor dem Senden Text per JS prüfen.
- AHS-Testroutine wartet nur auf einen LAUFENDEN Vollscan; für Teil "server"/T459 muss das AH offen sein.
- Uploader sammelt Testberichte bis 15 Min., dann #testberichte; GitHub-Zeitplan lässt Läufe aus (RM-CI2).
