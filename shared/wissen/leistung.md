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

## 6. Bewährte Bausteine – von den Projekten, die es im Spiel schon gut machen (Nutzer 17.11. 20:40: "allen zur Verfügung stellen")
Belegt = im Spiel gemessen. Die Fundstellen sind in den veröffentlichten Zips; jedes Projekt darf das Muster übernehmen (eigener Code,
gleiche Idee) – gemeinsame Dateien bleiben unverändert aus shared/.

B1 ThreatSentinel 2.5.18 – Testroutine in einer Coroutine mit Zeitbudget (BESTER Spielwert: ganze Routine 3,5 s, 28 Pausen, jede ≤ 5 ms,
   langsamste Portion 3,6 ms; Ingametest 17.11. 17:00). TestRoutine.lua ~Z. 280–300 und 3785–3840:
   - Jeder Bereich läuft in coroutine.create; MaybeYield() gibt VOR jeder Prüfung ab, sobald R.FRAME_MS = 2 ms im Bild verbraucht sind
     (Budget ab Beginn des Bildes, nicht ab Beginn der Prüfung). Ziel R.FRAME_LIMIT = 5 ms wird gemessen und berichtet.
   - R.noYield > 0 innerhalb von Ersatz-Umgebungen (WithAPI/Scene.Run): dort nie abgeben (Lua 5.1: kein yield über pcall, und ersetzte
     Einträge dürfen nicht in ein fremdes Bild "auslaufen").
   - Jede Prüfung wird einzeln gemessen (Timed); allein über 5 ms -> mit Namen in die Zusammenfassung.
B2 BuffSentinel 0.9.52 – Treiber mit Portions-Messung und Lua-5.1-Regel. SelfTest.lua ~Z. 120–160 und 410–440:
   - BUDGET_MS = 1,5 ms, danach abgeben – der Rest bis 5 ms bleibt Puffer für den nächsten Schritt.
   - Sliced(fn, enter, leave): Unter-Abschnitt in eigener Coroutine; enter/leave stellen den Ersatz-Zustand VOR jedem Abschnitt her und
     danach zurück – so kann auch in Ersatz-Umgebungen abgegeben werden, ohne dass Ersatz-Werte in andere Bilder auslaufen.
   - Drive(): misst jede Portion (frames, maxMs, maxAt = laufende Prüfung, Zählung über 5 ms mit Namen).
   - Offline-Prüfung "yield nie über pcall": mit Abgabe an JEDER Stelle (48 812 Abgaben, 0 Verletzungen) – findet Fehler wie PS
     "attempt to yield across metamethod/C-call boundary" vor dem Spiel.
B3 GoldSentinelMarkt v9/v10 (shared/, Prüf-Sitzung) – schwere Arbeit als Job mit Phasen. Muster:
   - Aufgabe = Tabelle mit Phase und Fortsetzungs-Zeiger (keys -> filter -> sort -> send; cmp1/cmp2/apply/gone/finish), je Bild ein Stück.
   - Schlüssel sammeln fortsetzbar über next(t, k) (KeysStep) – auch das Einsammeln einer grossen Tabelle wird portioniert.
   - Uhr nur alle N Einträge lesen (CHECK_EVERY 20; v9 hatte 100 -> Überschreitung, v10 behoben – Zahl messen, nicht raten).
   - Höchstens EINE schwere Aufgabe je Bild (Tick); OnUpdate nur wach, solange Arbeit da ist.
   - Tests: Zeit über echte Uhr = Median aus 3 Läufen (Rauschen), Grenze Budget + 2 ms; Ergebnis byte-gleich zur Fassung am Stück.
B4 AHSentinel – Vollscan lesen in Portionen (Spiel 17.11. 19:08: 889 Portionen, längste eigene Lese-Portion 3,4 ms bei 305 930
   Auktionen). Das Lesen ist gut; Verdichtung/V4/Preisverlauf danach noch nicht (bis 106 ms, Fall in Abschnitt 2) – Gegenbeispiel:
   ein Teil gut portioniert reicht nicht, JEDER Schritt eines Ablaufs braucht es.
B5 RaidMaster 3.0.31 – von 41,6 ms auf 21,6 ms längste Portion (Spiel 19:38); jede Portion mit Prüfungsnamen im Bericht.
Gegen-Beispiele (was schiefging – damit es keiner wiederholt):
G1 GuildSentinel 0.9.51: ein Test setzte einen Merker (ns.testSecret) und leerte ihn nie -> MaybeYield gab nie mehr ab -> 750–844 ms.
   Lehre: Abgabe-Sperren immer mit Gegenstück (Ende der Prüfung) und mit Zähler im Bericht ("nicht angehalten seit …").
G2 ProfessionSentinel 0.9.64: collectgarbage("collect") 31× im Lauf -> Einfrieren. Lehre: Regel 2 (Abschnitt 4).
G3 Mehrere: Nachbau ohne echte Datenmenge und ohne echte andere Addons -> Faktor 20–30 zu optimistisch. Lehre: Regel 7.
ERLEDIGT (Entscheid 20:42, siehe B6): ein gemeinsamer Baustein shared/GoldSentinelTakt.lua (Job mit Phasen, Budget, Messung je
Portion, noYield/Sliced, Zeitlimit) aus B1–B3 – dann baut jedes Addon auf demselben geprüften Takt statt jedes seinen eigenen.

B6 shared/GoldSentinelTakt.lua Version 1 (Prüf-Sitzung, 17.11.2026, Entscheid des Nutzers 20:42) – der gemeinsame Takt aus B1–B3:
   - GoldSentinelTakt.Start({name, owner, fn, args, budget=2, timeout=300, pauseInCombat, onDone, onPortion}); in der Arbeit
     Check(etikett) / Label / NoYield / PCall / Sliced(f, enter, leave) / Sleep / WaitFor; danach Summary(job) und job.stats.
   - Je Bild höchstens EINE Aufgabe (reihum), Budget 0,5–8 ms, Zeitlimit höchstens 3600 s (keine Sperre ohne Zeitlimit),
     Treiber schläft ohne Aufgaben, neuere Fassung übernimmt laufende Aufgaben (gleiche Tabelle).
   - Lua 5.1: erkennt pcall/xpcall/sort/gsub im Stapel und gibt dort nicht ab (gezählt "Abgabe nicht möglich" mit Etikett);
     zweite Sicherung meldet eine gescheiterte Abgabe ("Abgabe gescheitert"); Check in Metamethode/Iterator endet laut.
     Eichung je Coroutine: Zeilen, die das Spiel unter der Coroutine anhängt, zählen nicht.
   - Messwerte je Aufgabe: Bilder, längstes Bild mit Etikett (Beginn–Ende), Bilder über 5/16/40 ms, 10 längste, eigene
     Rechenzeit, Dauer.
   - Tests: shared/tests/test_goldsentineltakt.py, 70 Prüfungen in Lua 5.1, mit Gegenproben (Stapel-Erkennung aus -> stille
     Abgabe in pcall; ohne Eichung -> nie abgegeben; Arbeit am Stück echte Uhr ~60–97 ms gegen Takt ~2,3 ms, Median aus 3).
   - Verdacht, zu messen (im Spiel): Format von debugstack in Forever (Eichung deckt angehängte Zeilen ab). Erster Ingametest
     eines Addons mit dem Takt: "Abgabe nicht möglich" muss auf normalen Wegen 0 sein.
