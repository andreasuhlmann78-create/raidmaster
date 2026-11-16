# LevelPilot – Laufwege zu den Quests: Aufbau, Prüfung, Weg zur optimalen Führung (Supervisor, 16.11.2026)

Auftrag des Nutzers (16.11. 07:30): "Schaue mit LevelPilot zusammen, wie im Moment die Laufwege zu den Quests aufgebaut sind, prüfe, ob es
Sinn macht. Mein Wunsch: der Spieler wird optimal durch die Welt von WoW Forever und natürlich auch Classic Era geleitet."

Geprüft: LevelPilot 3.12.46 + LevelPilot_Data 1.6.x (announce-Zip, Code gelesen: Planner.lua, Graph.lua, Terrain.lua, Navigation.lua,
Data/Wege.lua, Data/Gateways.lua), echte Daten des Nutzers (LevelPilot.lua im privaten Daten-Repo, Stand 16.11. 07:06), QuestieDB
(Questie/QuestieDB, Stand 16.11. 04:47, data/Forever). Kennzeichnung: **belegt** (Code/Messung), **Verdacht** (zu messen).

## 1. Wie die Laufwege heute entstehen (belegt, Code)

| Stufe | Wie | Datei |
|---|---|---|
| 1 Kandidaten | alle Quests im Levelbereich für Volk/Klasse | Planner.lua 67 BuildCandidates |
| 2 Aufgaben | annehmen / Ziel erledigen / abgeben; Zielort = nächster Fundort (ein Punkt); Quests mit gleichem Gebiet werden gebündelt | Planner.lua 701 CollectTasks, 430 BundleIndex |
| 3 Fokus-Zone | Zone mit bestem Wert / (1 + Entfernung/Skala); offene Quests in der eigenen Zone zuerst; Kontinentwechsel nur mit grossem Paket | Planner.lua 1097 ChooseFocus |
| 4 Reihenfolge | nächster Nachbar (Annehmen/Abgeben leicht bevorzugt, erst alle Questgeber im Umkreis 250 yd einsammeln), höchstens 12 Schritte, danach 2-opt + Or-opt | Planner.lua 1186 Order, 1262 TwoOpt |
| 5 Reise | Flug, wenn Fussweg zum/vom Flugmeister × 1,25 + 300 < direkte Strecke (ab 2000 yd); Ruhestein, wenn Bindeort nahe am Ziel; binden in neuen Hauptzonen | Planner.lua 1431 TravelSteps, 1376 HearthStep, 1390 BindStep |
| 6 Weg (Pfeil) | A* über gelaufene Wege (eigene + Mitspieler), 54 Zonenübergänge/Schiffe, Startwegnetz, sonst Luftlinie innerhalb der Zone, über eine Geländekarte geführt (Strassen 0,45 · begehbar 1,0 · unbekannt 3,5) | Graph.lua, Terrain.lua, Navigation.lua 201 |
| 7 Gefahr | erster Schritt: kurzer Weg geprüft, zu starke Mobs auf dem Weg -> Aufgabe übersprungen | Planner.lua 1406 CheckFirstPath |

Das Gerüst ist gut durchdacht (Bündeln, Sammelpunkt Questgeber, Log-Platz, 2-opt mit Bedingungen, Ruhestein/Binden, Gefahr,
Geländekarte aus Kreaturen-Positionen statt Kartenbildern). Die Schwächen liegen darin, WOMIT gerechnet wird.

## 2. Befunde

### LW-1 Reihenfolge, Fokus-Zone und Flugentscheid rechnen mit LUFTLINIE (belegt, Code) – Wirkung gemessen (Obergrenze)
`Order`, `LegCost` (2-opt), `ChooseFocus` (z.near) und `TravelSteps` nutzen `LP.Geo:Dist` = Luftlinie. Der echte Weg (Graph/Terrain)
wird nur für den Pfeil und die Gefahrprüfung des ersten Schritts gesucht.
Messung (die vom Nutzer gelaufenen Wege, 4 449 Knoten / 4 943 Kanten, Paare 300–2000 yd Luftlinie in derselben Zone; Weg über das
gelaufene Netz = Obergrenze des echten Wegs, weil nicht jede Abkürzung gelaufen ist):

| Zone | Paare | Umweg-Faktor Median | 90 % | Anteil > 1,5 |
|---|---:|---:|---:|---:|
| Tausend Nadeln | 835 | 1,36 | 1,79 | 30 % |
| Tirisfal | 401 | 1,27 | 2,77 | 41 % |
| Alteracgebirge | 658 | 1,27 | 2,92 | 34 % |
| Silberwald | 671 | 1,35 | 1,66 | 27 % |
| Unterstadt | 73 | 1,31 | 1,63 | 23 % |
| Brachland | 673 | 1,13 | 1,75 | 21 % |
| Hügelland | 476 | 1,22 | 1,60 | 15 % |
| Durotar | 469 | 1,17 | 1,42 | 6 % |
| Eschental | 784 | 1,15 | 1,24 | 1 % |
| Steinkrallen | 207 | 1,19 | 1,25 | 0 % |

Folge: In Zonen mit Felsen, Tafelbergen, Schluchten (Tausend Nadeln, Alterac) ist die Luftlinie für ein Drittel der Paare um mehr als
50 % zu kurz – die Reihenfolge kann zu einem "nahen" Ziel hinter der Felswand führen, die Fokus-Zone kann falsch gewählt werden.
**Verdacht, zu messen:** wie oft das die Reihenfolge wirklich ändert (siehe LW-6).

### LW-2 Reihenfolge nach Strecke, nicht nach Zeit (belegt, Code)
Die Reihenfolge minimiert Yards (gewichtet mit Wert), nicht die Zeit. Die Dauer eines Ziels (töten/sammeln; das Addon schätzt sie
schon: QuestSeconds, ObjectiveCost, KillsPerMin) und die Abgabe-Freischaltung (Folgequests) gehen nicht in die Reihenfolge ein.
Optimal fürs Leveln ist die höchste Erfahrung je Stunde über den Plan-Horizont (Orientierungslauf-Problem), nicht die kürzeste Strecke.

### LW-3 Flugentscheid ohne Flugzeit (belegt, Code)
`TravelSteps` vergleicht nur Fusswege (Yards). Flugdauer (Flugroute über Zwischenknoten), Wartezeit am Zeppelin und Reittier-Tempo
fehlen. Bei mittleren Strecken (2000–4000 yd) kann Laufen/Reiten schneller sein als Hinlaufen + Flug über einen Umweg-Knoten.

### LW-4 Startwegnetz nur für 3 Horde-Gebiete (belegt, Daten)
Data/Wege.lua: Mulgore, Brachland, Donnerfels. Überall sonst (alle Allianz-Gebiete) hängt die Wegqualität an den selbst gelaufenen
Wegen und der Geländekarte. Der Nutzer hat bereits ein grosses Netz gelaufen (Tirisfal, Silberwald, Hügelland, Alterac, Tausend
Nadeln, Eschental, Steinkrallen, Unterstadt) – es ist nicht im Startnetz.

### LW-5 Classic Era wird nicht unterstützt (belegt, .toc)
LevelPilot.toc und LevelPilot_Data.toc: nur `## Interface: 16001` (Forever). Für Era fehlen: .toc-Zeile(n) für 1.15.x, die Quest-Daten
mit Era-Koordinaten (QuestieDB hat sie nativ: data/Era), die Forever-Eigenheiten abschalten (neue Forever-Quests, Skyborne,
Kartenumrechnung), Flug- und Übergangsdaten prüfen (gleiche Welt, Forever-Koordinaten umgerechnet).

### LW-6 Es fehlt eine Messgrösse für "optimal geführt" (belegt: keine Zeile im Protokoll)
Gespeichert sind Sekunden je Level (bestLevel) und Kalibrierungen (Kills, EP). Es fehlt: geplante Luftlinie vs. tatsächlich gelaufene
Strecke je Schritt, Zeit je Schritt (Weg / Ziel), Neuplanungen, die die Richtung umkehren, Leerlauf (kein Schritt), EP/Stunde je Level
gegen einen Richtwert. Ohne diese Zahlen lässt sich "optimal" weder belegen noch verbessern.

### Hinweis Datenqualität (gemessen, gut)
31 vom Spiel gesehene NPC-Positionen (npcPos) gegen die Datenbank: Abweichung 0,0–0,3 % der Karte – die Umrechnung der Classic-Daten
auf Forever-Karten ist genau. QuestieDB/Forever nutzt dieselbe Methode (Weltposition erhalten, Kartenmassstab umgerechnet) und
enthält **keine** neuen Forever-Quests ("does not discover new or relocated content") – LevelPilot lernt sie selbst (qdb, 88 gelernte
Quests beim Nutzer, IDs 9xxxx). Kein Wechsel der Datenquelle nötig.

## 3. Plan zur optimalen Führung (Reihenfolge = Nutzen je Aufwand)

1. **LW-6 Messen zuerst** (klein): je Schritt Luftlinie, gelaufene Strecke, Zeit Weg / Zeit Ziel, Neuplanung mit Richtungswechsel,
   Leerlauf; je Level EP/h. Zeilen im Testbericht/Protokoll. Daraus der Kennwert "Umweg je Zone" und "Zeit-Anteil Weg".
2. **LW-1 Wegkosten statt Luftlinie** (mittel): Kosten = Luftlinie × Umwegfaktor der Zellenpaare (aus gelaufenem Netz + Geländekarte,
   einmal je Zone vorberechnet, klein) für Order/2-opt/ChooseFocus; für die nächsten 3 Schritte die echte Weglänge (Graph, in Portionen,
   wie heute für den Pfeil). Tempo-Grenze wie bisher (keine Spitze > 16 ms, Portionen).
3. **LW-2 Zeitmodell** (mittel): Ziel der Reihenfolge = EP je Sekunde über den Horizont (Wegzeit aus LW-1 + Zieldauer aus
   QuestSeconds/ObjectiveCost), Abgaben mit Folgequest höher. 2-opt/Or-opt bleiben als Verbesserer mit Zeitkosten.
4. **LW-3 Flug nach Zeit** (klein): Flugzeit aus den Flugknoten (Strecke über die bekannte Route / Fluggeschwindigkeit), Warten an
   Zeppelin/Schiff aus Gateways, Reittier-Tempo; fliegen nur, wenn schneller.
5. **LW-4 Startwegnetz aus allen gelaufenen Wegen** (klein bis mittel): Das Netz des Nutzers (und weiterer Einsender, ohne Namen)
   mit dem vorhandenen Werkzeug seed_bauen.py in Data/Wege.lua übernehmen – Speichergrenze beachten (in Portionen laden, wie heute).
6. **LW-5 Classic Era** (gross, Wunsch des Nutzers): eigener Plan zuerst (Datenquelle QuestieDB data/Era nativ, .toc, Abschalten der
   Forever-Teile, Testroutine je Spielversion), dann in Stufen bauen.

Jede Stufe mit Vorher/Nachher-Messung aus LW-6 (gleiche Strecke in der Nachbildung, und im Spiel).

## 4. Zusammenarbeit
LevelPilot gibt zuerst eine Stellungnahme (siehe offen-levelpilot.txt LW-0): was es schon misst, ob die Befunde stimmen, welche
Grenzen es sieht (Tempo, Speicher), und eigene Zahlen. Danach Umsetzung in der Reihenfolge oben, je Version "umgesetzt, zur Prüfung".

## 5. Vergleich: RestedXP (Auftrag des Nutzers 07:51 "hol alle Daten über RestedXP und untersuche, wie sie es mit den Wegen machen")

Quellen (gelesen 07:53): CurseForge-Seite "RestedXP Guide" (30,7 Mio. Downloads, letztes Update 15.11.2026) und der öffentliche Quellcode
github.com/RestedXP/RXPGuides (Stand 14.11.2026, Commit 22e6ce2). .toc: Interface 11509 (Era), 20506, 38002, 50504, 120x – UND 16001
(WoW Forever). **Lizenz: Creative Commons BY-NC-SA 4.0** (nicht kommerziell, gleiche Lizenz, Namensnennung) – LevelPilot darf von dort
KEINE Routen, Texte oder Code übernehmen (LevelPilot steht nicht unter dieser Lizenz). Erlaubt ist, die Ideen zu verstehen.

### Wie RestedXP Wege macht (belegt, Code und Leitfäden)
- **Keine Wegsuche.** Es gibt keinen Algorithmus (kein A*, kein Wegnetz). Die Route ist ein von Speedrunnern **von Hand geschriebener
  Leitfaden**: eine feste Folge von Schritten je Volk/Fraktion/Stufenbereich, mit Bedingungen je Klasse/Volk (`<< Warrior/Mage`),
  Stufen-Prüfungen (`.xp <2`), Sprüngen (`#completewith`, `#requires`, `#sticky`).
- **Der Laufweg sind Zwischenpunkte von Hand:** `.goto Karte/0,x,y,Radius,0` – Weltkoordinaten (robust gegen Kartenänderungen, darum
  laufen die Leitfäden in Forever), Radius = wann der Pfeil zum nächsten Punkt springt; `,0` = Zwischenpunkt ohne eigenen Pin. Beispiel
  Undead-Start: drei Punkte führen aus der Gruft hinaus (Treppe), bevor der Questgeber kommt. In den freien Forever-Leitfäden (Stufe 1–22,
  13 Dateien): 12 278 `.goto`, davon 2 851 reine Weg-Zwischenpunkte, 374 Schleifen (Kreise zum Grinden/Sammeln).
- **Reise-Tricks als Schritte:** 78× `.deathskip` (absichtlich sterben, beim Geisterheiler auferstehen = schnelle Reise), 66× `.hs`
  Ruhestein, 44× `.bindlocation`/41× `.home` (Binden), 88× `.fly`, 60× `.fp` (Flugpunkt holen), 233× `.zoneskip`. Dazu "HS-Batching":
  Binden im selben Augenblick wie das Ende des Ruhestein-Wirkens, so landet man am alten Ort und ist trotzdem neu gebunden.
- `flygoto`/`groundgoto`: Punkte gelten nur mit/ohne Flugfähigkeit.
- Pfeil + Linien auf Weltkarte und Minikarte zwischen den nächsten Punkten.

### Was das für LevelPilot heisst
- RestedXP ist **optimal, wo ein Speedrunner die Strecke abgelaufen hat** (Stufe 1–22 frei, Rest bezahlt), aber **starr**: weicht der
  Spieler ab (andere Klasse, Gruppe, verpasste Quest, späterer Einstieg), passt die Route nicht mehr. LevelPilot plant **dynamisch** für
  jeden Zustand – das ist der grössere Nutzen, wenn die Kosten stimmen (LW-1/LW-2).
- Die Handarbeit von RestedXP an Engstellen (Gruft, Treppe, Felswand) entspricht bei LevelPilot dem **gelaufenen Wegnetz** (LW-4) –
  nur dass LevelPilot sie aus echten Läufen lernt statt von Hand. Darum ist LW-4 wichtig: ohne gelaufenes Netz fehlt genau das.
- Neu für LevelPilot (LW-7, Ideen): (a) **Tod als Reise** (deathskip) im Speedrun-Modus, nur wenn Geisterheiler nahe am Ziel, kein
  Ehre-/Haltbarkeitsproblem (Haltbarkeit −10 % beim Geisterheiler!) – nur mit Entscheid des Nutzers (riskant/ungewohnt);
  (b) **Ruhestein + Binden zusammen** (HS-Batching) als Option; (c) **Schleifen** für Sammel-/Grind-Ziele (Kreis über die Fundorte statt
  ein Punkt); (d) **Radius je Punkt** (enge Stellen kleiner Radius); (e) **Weltkoordinaten** für alle gespeicherten Wege (schon so:
  Graph-Knoten sind Weltpunkte – gut).
- **Messlatte:** Die Zeiten der Speedrunner je Stufe sind öffentlich (RestedXP-Leitfäden geben Stufenbereiche je Abschnitt). LevelPilot
  kann seine EP/Stunde (LW-6) gegen solche Richtwerte stellen – als Zahl, nicht als kopierte Route.

## 6. Weitere ähnliche Addons (Auftrag des Nutzers 07:56 "suche nach weiteren Addons und zieh raus, was wir brauchen können") – 07:57

| Addon | Spiel | Art | Lizenz | Für uns |
|---|---|---|---|---|
| **Mapzeroth** (Quellcode gelesen, github.com/tr0tsky0/Mapzeroth, Stand 15.11.2026) | Forever + Retail | Navi: schnellster Weg zu jedem Ziel, Dijkstra über Reise-Graph | **MIT laut CurseForge** – im Repo KEINE Lizenzdatei (vor jeder Übernahme klären) | SEHR VIEL – siehe unten |
| **Jazkyr's Northstar** (CurseForge-Beschreibung) | nur Forever | Navi + "alle Quests einer Zone der Reihe nach", echte Flugzeiten und Preise, Flugpunkt holen, Gruppenmitglied folgen | Alle Rechte vorbehalten | nur Ideen |
| **Well Trodden** (CurseForge-Beschreibung) | Forever | zeichnet gelaufene Wege auf, Netz aus Kreuzungen, oft gelaufene Wege zählen als kürzer, Rest Luftlinie (orange) | MIT | bestätigt LevelPilots Ansatz; Idee "oft gelaufen = billiger" |
| **FarstriderLib** (CurseForge) | Retail/Classic/TBC/MoP, nicht Forever | Bibliothek: Reise-Graph mit Flug, Portal, Schiff, Zeppelin, Gegenstände, Zauber | GPL v3 | nur Ideen (GPL passt nicht zu LevelPilots Lizenz) |
| **Zygor Travel System** (Handbuch) | alle | "GPS": schnellster Weg mit Reittier, Flug, Portal, Ruhestein, Zaubern; Optionen: Ruhestein ausschliessen, Flug bevorzugen, Flug automatisch nehmen | kommerziell | nur Ideen |
| QuickRoute (CurseForge) | nur Retail | Dijkstra, Teleport-Abklingzeiten | MIT | nur Ideen |
| Guidelime, RestedXP, Azeroth Pilot | Classic/Retail | Leitfäden von Hand (keine Wegsuche) | verschieden | siehe Abschnitt 5 |

### Mapzeroth im Detail (belegt, Code) – das Wertvollste
- **Strassennetz aus den Spieldateien von Forever:** tools/roads/gen_roads.py liest die Gelände-Texturen (ADT, Strassen-Texturen) aus dem
  Forever-Client, macht daraus Mittellinien je Kontinent (Data/Forever/Roads.lua, 124 KB, alle Kontinente) und Stadtwege (CityPaths).
  Das ist genau die Lücke von LW-1/LW-4: LevelPilot hat Strassen nur, wo Spieler gelaufen sind (+ Geländekarte aus Kreaturen-Positionen).
- **Gehweg-Wahl:** Strasse kostet 1, offenes Gelände 1,8 (einstellbar 1,25–3,5); Zeit = echte Länge. Zonengrenzen nur über von Hand
  geprüfte Übergänge ("Luftlinie ist kein sicherer Ersatz für Begehbarkeit" – gleiche Regel wie LevelPilot).
- **Flüge mit echten Zeiten und Preisen** (Flights.lua aus gen_flights.py), mit Ticket-Logik (direkte Strecke wird immer verkauft).
- **Reise-Graph:** Dijkstra über Knoten mit Flug, Schiff, Zeppelin, Ruhestein, Klassenzaubern, Gegenständen; Ladebildschirm-Zeit.
- **Tempo:** Reittier nach Reitfertigkeit, drinnen ohne Reittier (MovementSpeed.lua). Gemessene Umweg-Faktoren je Stadt (PathFactors).
- **Mehrere Ziele:** beste Reihenfolge EXAKT bis 12 Stopps (Held-Karp), darüber "nächster zuerst + Verbesserung" (MultiRoute.lua) –
  LevelPilots Horizont ist ebenfalls 12; exakt bis ~8 Stopps ist im Spiel billig (2^8 × 64 ≈ 16 000 Schritte).
- Forever lernt Flugpunkte beim Öffnen des Flugmeisters.

### Was LevelPilot daraus nehmen soll (LW-8, Vorschlag)
1. **Strassen aus den Spieldateien** – entweder Mapzeroths Roads.lua übernehmen (NUR wenn die MIT-Lizenz bestätigt ist: Lizenzdatei im
   Repo oder schriftlich vom Autor; dann mit Namensnennung und Lizenztext) ODER mit eigenem Werkzeug aus dem Forever-Client erzeugen
   (gleiches Verfahren, eigene Umsetzung; braucht den Client des Nutzers – Verdacht, Aufwand zu klären). Damit: Wegkosten (LW-1) aus Strassen
   + Geländekarte + gelaufenem Netz, und ein Startnetz für ALLE Zonen (LW-4) ohne dass jemand alles ablaufen muss.
2. **Flugdaten mit Zeit und Preis** (LW-3/NAV-2): eigene Messung (Calib) + Flugnetz; Ticket-Regel übernehmen (Idee).
3. **Exakte Reihenfolge** für kleine Horizonte (LW-2): bis 8 Ziele exakt, darüber 2-opt wie heute.
4. **Reittier/drinnen** im Tempo (NAV-2), **Ladebildschirm-Zeit** für Schiff/Zeppelin.
5. **Oft gelaufene Wege billiger** (Well Trodden; LevelPilot hat die Zahl "Läufe" schon im Startnetz).
6. Northstar-Ideen: Flugpreise anzeigen, "Flugpunkt holen" als Schritt (hat LevelPilot schon), Gruppenmitglied folgen (NAV-4).

