# Stand AHSentinel (Projekt-Sitzung)

## Stand 27.11.2026 21:15 · Version 0.65.424 (Discord, AHS-SN-CAN1); CurseForge 0.65.423 (Hotfix 21:03, Datei 9854852)
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz – Testberichte "GSTEST1{…}", UI-Befunde db.uiFindingsLast).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion (listN.txt).
Nachbau: cd /home/claude/ahanalyzerpro && bash tests/run_offline.sh /home/claude/AHSentinel; FULL=1 nur auf Kopie und ALLEIN (vorher pgrep run_all.sh leer).
 FULL 0.65.416: 356 PASS / 67 FAIL, keine neuen. Eigene Szenarien /tmp/claude-0/sim2/wowsim/scenarios_new.lua (zz_st1 Chat-Inventar, TR_TEXT=1).

## Gerade in Arbeit
- SN-Z4 ERLEDIGT (Supervisor 21:16, Nutzer "ja sieht gut aus"). 0.65.423 Hotfix auf CurseForge (Entscheid Nutzer 21:00 + Bestätigung im Chat).
- AHS-SN-CAN1 in 0.65.424: AUCTION_CANCELED mit eigener Sniper-auctionID = "eigener Kauf" (T1042).
- AHS-API1: 0.65.422+ auf CurseForge; Ingametest API-LANGSAM offen.

## Nächste Schritte
1. FULL 0.65.424 allein (Vergleich mit fail423.txt). Neues string.format -> immer s341 mitlaufen. Danach AHS-API1 nach Ingametest (Zeile API-LANGSAM).
2. AHS-BP1 MITTEL (bindType: Schurkengifte/Blendungspulver BoP nicht als AH-Ware), AHS-S216, AHS-MK1 (nach Ingametest).
3. Weitere T459-Posten messen (je Massnahme mit Messung).
4. Regel CF 18:00: CF-Entscheid im Repo -> sofort Auswahl-Frage im Chat; bis 17:30 Stand melden.

## Offen beim Nutzer
- Ingametest W1: Öffnen kalt und vorgebaut mit 0.65.415+ (Zeile UI-PREBUILD). API1: WorthUpTo ≤ 2 ms mit 0.65.416+.
- Ingametest ST1: Einloggen ohne Testmodus = 1 Zeile.
- Ingametest AHS-API1 mit 0.65.418: Schneider-Figur, Berufsfenster, /ahs protokoll -> API-LANGSAM.

## Entscheide des Nutzers seit letztem Stand
- 27.11. 21:00: 0.65.423 sofort als Hotfix auf CurseForge (im Chat bestätigt). 16:56: 0.65.422 auf CurseForge statt 0.65.421.
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
