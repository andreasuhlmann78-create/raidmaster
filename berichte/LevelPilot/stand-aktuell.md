# LevelPilot – Stand der Sitzung

## Stand 24.11.2026 11:00 · Version 3.13.12 (veröffentlicht, Discord, md5 a49a693fff74c35d12a7342fdc0a2b0a)

## Gerade in Arbeit
- Nichts angefangen. 3.13.12 gepusht 24.11. 11:00. Bericht: berichte/LevelPilot/2026-11-24-1100-3.13.12-lp-i1.txt (umgesetzt, zur Prüfung).
- Inhalt 3.13.12: LP-I1 (Stücke über 40 ms), Zuordnung der ganzen Bilder (Feld ganzeBilder), SH-V3 kopiert, T353 erklärt (gewollt).

## Nächste Schritte (Reihenfolge)
1. LP-I3 MITTEL: T155 Planung je Reiseschritt Ø 22,16 ms (soll < 16), Median 11,22, längste 97,8 ms (Stufe 10, Zone 1458, +627/+1345/+800 KB),
   552 KB je Planung. Mit den Laptop-Daten nachstellen (m2.sh), nicht schätzen.
2. LP-I1 Rest nach dem nächsten Ingametest: Felder ganzeBilder/stuecke (KB) auswerten. Verdacht, zu messen: Stücke mit viel Anlegen
   zahlen im Spiel die Speicherbereinigung (Nachbau: T32, T144, T268 schwanken mit "Bereinigung").
3. LP-K1 NIEDRIG: Weicht LevelPilot den anderen GoldSentinel-Fenstern aus? (Test mit offenem GuildSentinel-/BuffSentinel-Fenster.)
4. Hinweis Blueposts BP-2026-11-23-4 (kein Auftrag): Leitet LevelPilot das Reittempo aus der Reitfertigkeit ab? Wenn ja, das gemessene Tempo nehmen.
5. Notbremse "Routenberechnung" 22.11. 17:05: beim nächsten Upload des Nutzers auswerten.
6. Zeile "Wegabschnitte": braucht eine Spielsitzung draussen mit Laufen (3.13.11: aufgezeichnet 0, 35 min AFK in Undercity).

## Offen beim Nutzer
- Ingametest 3.13.12 (wichtig: ganzeBilder, taktTeile, stuecke mit KB; T385–T387; die 12 Stücke aus 3.13.11).
- Entscheid T31/T32 (einmal neu planen): gefragt, keine Antwort.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen. Aufträge kamen von der Prüf-Sitzung: SH-V3 (24.11. 07:20) und Auswertung des Ingametests 3.13.11 (24.11. 10:10),
  Reihenfolge LP-I1 -> LP-I3.
- Weiter gültig: immer Deutsch (23.11. 08:36), in announce/ nichts löschen (23.11. 11:36), komplette Dateien bei Code-Änderungen.

## Wichtig zu wissen
- Daten Ingametest 3.13.11: goldsentinel-daten, Zweig origin/sicherung (main ist nur eine Kopie, Verlauf wird bei jeder Lieferung ersetzt),
  aktuell/AUSPLUSLAPTOP/forever/konto-5cb3d536/LevelPilot.lua.gz. Ausgepackt nach /home/claude/lpdaten-2411/LevelPilot.lua.
  Der lokale main-Zweig von goldsentinel-daten weicht ab. Nicht zurücksetzen (das wurde abgelehnt), Dateien mit git show origin/sicherung:<pfad> holen.
- Skripte im Scratchpad (bei Neustart weg):
  - m2.sh: ganze Routine mit Laptop-Daten (Undercity, 1458, L10, PRIEST); m.sh: MININT-Daten (Donnerfels).
  - p2.sh + probe*.lua: Einzelmessungen; ms.sh/prof_seg.lua: Abtastung je Bild; mp.sh/prof_piece.lua: Stapel am Anfang und Ende des längsten Bilds.
  - m2old.sh: dasselbe mit 3.13.11 (ab/).
- Arbeitskopie /home/claude/lp31238/{LevelPilot,LevelPilot_Data} = 3.13.12.
- Nachbau-Rauschen: T261 bei gleichem Code 863–1174 ms (Wanduhr samt Speicherbereinigung). "Bereinigung" im Stück = Speicher fiel > 1 MB.
- 3.13.12 neu:
  - Graph.EachEdge (Neuanfang bei edgeGen); Stats() ohne force rechnet nie am Stück (erster Stand beim Laden, sonst Auftrag "graphstats");
  - MarkOwnInner("yield"); Protokoll-Zeilen gespeichert (Pr.LineCacheClear für T386);
  - TR.WholeTick/WholeLines; LP:Yield -> TR.Safe nur aus einer Coroutine.
- T353 "Abgabe nicht möglich" ist die absichtliche Gegenprobe (genau 1×).
