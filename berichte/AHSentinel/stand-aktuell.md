# Stand AHSentinel (Projekt-Sitzung)

## Stand 27.11.2026 11:53 · Version 0.65.419 (Discord, OVF1-Korrektur API.lua; 0.65.418 AHS-API1 Messung); CurseForge 0.65.413; ST1 (0.65.417) angenommen 10:30
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz – Testberichte "GSTEST1{…}", UI-Befunde db.uiFindingsLast).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion (listN.txt).
Nachbau: cd /home/claude/ahanalyzerpro && bash tests/run_offline.sh /home/claude/AHSentinel; FULL=1 nur auf Kopie und ALLEIN (vorher pgrep run_all.sh leer).
 FULL 0.65.416: 356 PASS / 67 FAIL, keine neuen. Eigene Szenarien /tmp/claude-0/sim2/wowsim/scenarios_new.lua (zz_st1 Chat-Inventar, TR_TEXT=1).

## Gerade in Arbeit
- AHS-API1 HOCH (11:05): WorthUpTo im Spiel 23,3 ms/+0,9 MB je kaltem Aufruf; Nachbau (Laptop 27.11. 10:59, zz_api2, TAILOR=1) nur 0,2–2,8 ms.
  0.65.418 = Messzeile API-LANGSAM (Teile, Zustand, Testroutine). Warte auf Ingametest -> dann Ursache belegen, Massnahme.
- Befund: Laptop-Daten haben "berufe"/"haendler" vorgemerkt (24.11.) -> Testroutine startet beim Öffnen des Berufsfensters.
- FULL 0.65.417: 356/67, keine neuen. DL-ABN: download/ nur angenommene Version + CF 18:00 + OK Nutzer.

## Nächste Schritte
1. FULL 0.65.419 allein (Vergleich mit fail417.txt; 418 hatte s341 neu rot -> in 419 behoben). Neues string.format -> immer s341 mitlaufen. Danach AHS-API1 nach Ingametest (Zeile API-LANGSAM).
2. AHS-BP1 MITTEL (bindType: Schurkengifte/Blendungspulver BoP nicht als AH-Ware), AHS-S216, AHS-MK1 (nach Ingametest).
3. Weitere T459-Posten messen (je Massnahme mit Messung).
4. Regel CF 18:00: CF-Entscheid im Repo -> sofort Auswahl-Frage im Chat; bis 17:30 Stand melden.

## Offen beim Nutzer
- Ingametest W1: Öffnen kalt und vorgebaut mit 0.65.415+ (Zeile UI-PREBUILD). API1: WorthUpTo ≤ 2 ms mit 0.65.416+.
- Ingametest ST1: Einloggen ohne Testmodus = 1 Zeile.
- Ingametest AHS-API1 mit 0.65.418: Schneider-Figur, Berufsfenster, /ahs protokoll -> API-LANGSAM.

## Entscheide des Nutzers seit letztem Stand
- 27.11. 10:30 (Supervisor): DL-ABN – download/ nur mit angenommener Version.
- 27.11. 08:27–09:23 (über Supervisor 09:25): ST1 Spieler-Texte A–E, nur ausserhalb Testmodus.
- 26.11. ~17:19 im Chat: "Ja, 0.65.413 hochladen" (CurseForge, erledigt).

## Wichtig zu wissen
- A:PrintError(where, text, reported): ohne Testmodus 1 Zeile je Sitzung; A:PrintOnce(key, msg): tipsShown[key]; im Testmodus immer.
- Laptop-Daten haben db.entwickler = true -> dort gilt die alte volle Einlog-Zeile (Testmodus). Ohne: /tmp/claude-0/tb1/laptop_nodev.lua.
- Wächter-Prüfziele "w:<id>" nur in Sn.extra; Kopfzeile "Sniper: an/aus" = db.sniper.armed.
- T750-Regel: Zeilen ohne " – Grund" nach "Text x px)" sind "gekürzt (Tooltip)" = kein FEHLER.
- Letzter Test T1039 (ST1); T1038 API1, T1037 W1, T1036 TB1-b, T1035 M3, T1034 TB1. Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …".
- Nie Blizzard-Globale in Tests ersetzen (Taint) – Nähte Ch.GameMoney, BK.GameMoney, A.Global.
- Nie etwas in announce/ löschen. Jede Version: CHANGELOG.de.md-Abschnitt Pflicht (AHS-R1).
