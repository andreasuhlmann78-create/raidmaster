# Stand AHSentinel (Projekt-Sitzung)

## Stand 24.11.2026 20:15 · Version 0.65.392 (Discord; Kandidat für CurseForge – NICHT dort, wartet auf Ingametest + OK des Nutzers)
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz – Testberichte "GSTEST1{…}", UI-Befunde db.uiFindingsLast).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion.
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s); FULL=1 alle 410 (~25 Min.;
 0.65.392: 342 PASS, 68 FAIL – s216/s92 im Gesamtlauf wackelig, einzeln PASS bzw. auch mit 0.65.391 rot). T126 streut 6–10 ms.
 Eigene Szenarien /tmp/claude-0/sim/wowsim/scenarios_new.lua: zz_t459real (echte Daten REAL_SV=/tmp/claude-0/ahs_sv3.lua), zz_tr1 (Wächter-
 Schritt), zz_i6_sniper, zz_ui_buy (Nachbau rechnet Lage relativer Anker NICHT – UI-Geometrie nur im Spiel).

## Gerade in Arbeit
- nichts. 0.65.392 veröffentlicht: AHS-CF1 (1) T750/T191 und (2) AHS-TR1. Bericht 2026-11-24-2015-0.65.392-cf1-t750-t191-tr1.txt.

## Nächste Schritte (AHS-CF1, Entscheid des Nutzers 19:19/19:21)
1. Ingametest 0.65.392 auswerten (Daten-Repo): Rest-Befunde T750/T191 sofort beheben (T191 nennt jetzt Lage/Grösse).
2. CurseForge erst, wenn Supervisor a–e geprüft UND der Nutzer im Spiel freigibt; dann Zip um 18:00 nach download/ (T459-Ausnahme nur 1×).
3. DANACH AHS-SP1 (HOCH, Entscheid 19:56): Speicher-Lösung Vollscan – Zahlen-Listen min/qty/auc (zwei Sätze im Wechsel), Stufen als Text
   (EncodeLadder-Format), VS:Ladder packt bei Bedarf aus. Vorgehen: messen im Nachbau mit echten Daten, Gleichheitstest aller Leser, Bericht
   VOR Einbau, Freigabe Supervisor, dann Einbau.
4. Danach V4-Messung, G14-a, AHS-UMG1 (NIEDRIG: Hintergrund-Erkennung, Bewertung "Umgebung möglich" mit Gegenprobe).

## Offen beim Nutzer
- Ingametest mit 0.65.392 ("testroutine alles") und eigene Durchsicht im Spiel (CF1 e) – ohne sein OK keine CurseForge-Veröffentlichung.
- Gold-Messung Ausrüstung mit Kupfer-Preis (AHS-POST), RecipeList-Fehler mit nur AHS aktiv.

## Entscheide des Nutzers seit letztem Stand
- 19:12 AHS-TR1: Wächter-Schritt 3 Min., Vollscan-Schritt bleibt.
- 19:19/19:21 AHS-CF1: erst gute Version auf CurseForge; T459-Ausnahme mit Bedingungen a–e; Nutzer schaut selbst im Spiel durch.
- 19:56 AHS-SP1: Speicher-Lösung als erster Schritt nach der Veröffentlichung.  20:04 AHS-UMG1 (nach CF1 und SP1).

## Wichtig zu wissen
- TR1: Schritt endete bisher erst mit W.plm.done (300 s); jetzt Ende bei 180 s mit Messung + >= 3 Hürden-Runden. Prüfliste-Punkte WAECHTER-LAST/
  -FUND haken sich so nicht selbst ab (sind nicht mehr einzeln in der Liste) – im Bericht als Frage.
- T750-Regel: Zeilen in uiFindingsLast ohne " – Grund" nach "Text x px)" sind "gekürzt (Tooltip)" = kein FEHLER.
- VS:Finish: Gültigkeit vor dem Verdichten; Vorrat NUR memSpare-Tabellen, die nicht in self.mem stehen (AHS-I3-a).
- Letzter Test T1013. Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "AHS-I3", .
- Nie etwas in announce/ löschen, alte Versionen nicht wiederherstellen. Jede Version: CHANGELOG.de.md-Abschnitt Pflicht (AHS-R1).
