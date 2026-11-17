# Leistung im Spiel – Ruckeln von Anfang an verhindern (Wissen aller GoldSentinel-Addons)

Auftrag des Nutzers (17.11.2026 20:39): "Wir sammeln die Daten und stellen im Detail fest, wie man es von Anfang an verhindern kann."
Wer Code baut, prüft oder beauftragt, der im Spiel rechnet (Scan, Route, Panel, Testroutine, Sync, Laden), liest diese Datei vorher.
Regeln hier nur als "belegt" (gemessen im Spiel, mit Zahl) – sonst als "Verdacht, zu messen".

## 0. Grenzen (Entscheide des Nutzers)
- Hart: kein Schritt / kein Bild über 40 ms eigene Rechenzeit. Ziel: ≤ 5 ms je Bild (Testroutine) bzw. ≤ 2–4 ms (laufende Arbeit).
- T126-Regel: Median der 3 längsten Portionen; längste > 2× = FEHLER.
- Keine Sperre ohne Zeitlimit. Lieber später fertig als ein stehendes Bild.

## 1. Grundsatz: Warum WoW ruckelt
Addon-Lua läuft im selben Ablauf wie das Zeichnen. Rechnet ein Addon X ms am Stück, steht das Bild X ms. Dazu kommt die Lua-
Speicherbereinigung (Lua 5.1): wer viel Speicher anlegt und wegwirft, löst Bereinigungen aus; deren Abschluss-Schritt ist unteilbar.

## 2. Fälle (gesammelt – je Fall: Addon, Version, Stelle, Spiel-Messwert, Nachbau-Messwert, Ursache, Behebung, Messwert danach)
| Datum | Addon/Version | Stelle | Spiel | Nachbau | Ursache (belegt/Verdacht) | Behebung | danach (Spiel) |
|---|---|---|---|---|---|---|---|
| 17.11. | ProfessionSentinel 0.9.64 | Testroutine | Spiel eingefroren, Bild 2608 ms | – | 31 ganze collectgarbage("collect") am Stück (belegt im Nachbau) | 0.9.66 Bereinigung in Portionen | 0.9.66: "mehrfach extrem geruckelt" |
| 17.11. | ProfessionSentinel 0.9.66 | Panel-Aufbau T139 / UpdateBest T140 | 1267 / 1307 ms | 39–48 ms | Verdacht: Preisabfragen an echtes AHSentinel/TSM je Rezept; Nachbau ohne echte Addons | offen | – |
| 17.11. | LevelPilot 3.12.89 | Graph:Path lange Route T151 | Median 502, max 2109 ms | – | Verdacht: Wegnetz aus gelaufenen Wegen (seit 3.12.88) gross, Suche ohne Grenze | offen | – |
| 17.11. | LevelPilot 3.12.89 | Einloggen T261 | 4348 ms in 60 s, längster 90 ms | – | Verdacht: dieselbe Wegnetz-Arbeit | offen | – |
| 17.11. | AHSentinel 0.65.328 | Vollscan T458/T459 | Bild 106 ms, +48 MB, 3 Bereinigungen | im Nachbau "umgesetzt" | Verdacht: Preisverlauf-Neuaufbau legt Tabellen neu an | offen | – |
| 17.11. | AHSentinel 0.65.328 | Testschritte S28/T21/T72 … | 648/546/405 ms | S28 14 ms | Verdacht: Server-Wartezeit mitgezählt oder Nachbau zu klein | offen | – |
| 17.11. | GuildSentinel 0.9.51/0.9.53 | Testroutine Bereich K / B | 844 / 356 ms | 82,8 ms | belegt: ns.testSecret nie geleert -> Routine hielt nie an (0.9.53 behoben); 356 ms T269 offen | teilweise | 0.9.53: 356 ms |
| 17.11. | RaidMaster 3.0.30 -> 3.0.31 | Testroutine | Spiel abgestürzt/geruckelt, 41,6 ms | – | – | Portionen | 3.0.31: 21,6 ms |

## 3. Muster (was die Fälle gemeinsam haben) – wird mit jedem Fall ergänzt
M1 (belegt, 4 Addons): Der Nachbau war viel kleiner/leichter als das Spiel -> "im Nachbau OK", im Spiel 20–30× langsamer.
M2 (belegt, PS/GS): Testroutine-eigene Arbeit (ganze Bereinigungen, nie anhalten) erzeugt Ruckler, die das Addon selbst nicht hat.
M3 (Verdacht, PS/LP/AHS): Datenmengen wachsen mit dem Spielen (Wegnetz, Preisverlauf, Rezepte) – was am ersten Tag schnell ist,
   ist nach einer Woche langsam. Grenzen und Verdichtung von Anfang an.
M4 (Verdacht, PS): Aufrufe in andere Addons (AHSentinel, TSM) sind im Spiel teuer und werden je Zeile wiederholt.

## 4. Bau-Regeln von Anfang an (Vorlage, jedes neue Addon, jede neue Funktion)
1. Jede Arbeit, die mit der Datenmenge wächst, läuft als Aufgabe in Portionen mit Zeitbudget (Uhr: debugprofilestop) und
   Zeitlimit – nie als Schleife am Stück. Auch beim Laden/Einloggen.
2. Keine ganze Speicherbereinigung (collectgarbage("collect")) im Spiel – nie, auch nicht in Tests. Speicher messen über
   GetAddOnMemoryUsage bzw. collectgarbage("count").
3. Tabellen wiederverwenden statt je Durchlauf neu anlegen (wipe statt {}), keine Zeichenketten-Verkettung in Schleifen.
4. Ergebnisse zwischenspeichern; Aufrufe in andere Addons je Durchlauf höchstens einmal je Wert.
5. Jede wachsende Datenmenge hat eine Obergrenze und eine Verdichtung, beide getestet.
6. Jede Aufgabe meldet ihre längste Portion im Protokoll ("LANGSAM"-Zeile) – im Spiel, nicht nur im Test.
7. Nachbau-Pflicht: Leistung wird mit ECHTEN Daten in echter Grösse gemessen (Uploads in goldsentinel-daten, nur lokal), mit den
   echten anderen Addons bzw. ihrem gemessenen Aufwand, Lua 5.1, Ballast im Speicher. Ein Nachbau-Wert gilt erst, wenn er an
   einem Spielwert geeicht ist (gleicher Fall, Abweichung genannt).
8. Testroutine: Ergebnis-Zeile "Portionen: n Bilder, längstes Bild x ms (Schritt) · Schritte über 16 ms mit Namen" –
   längstes BILD und Gesamtdauer eines Schritts getrennt.

## 5. Daten sammeln (wie)
- Jeder Ingametest liefert über den Uploader die Portionen-Zeilen (GSTEST). Die Prüf-Sitzung trägt jeden Ruckler über 40 ms
  als Fall in Abschnitt 2 ein; das Projekt liefert Ursache (belegt) und Messwert danach.
- Geplant (Prüf-Sitzung): Auswertung aller GSTEST-Berichte je Addon/Version (längstes Bild, Schritte über 16/40 ms) als Tabelle
  in testberichte/ – damit sieht man Verlauf und Rückschritte.
