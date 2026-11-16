# LevelPilot: optimale Questroute über die ganze Welt – Quellen, Befund, Plan

Supervisor GoldSentinel, 16.11.2026 18:00. Aufträge des Nutzers:
- 17:35 "Er soll mit den Daten, die ihr habt, die Welt komplett absuchen und so die optimale Questroute erstellen – such bitte in allen Quellen nach Unterstützung."
- 17:38 "Studiere erst alle Hinweise, und mach dann den Plan – du bist hier der Projektverantwortliche."
- 17:41 "Alle Möglichkeiten prüfen, wie wir LevelPilot genauer machen können; nach der Prüfung an LevelPilot weitergeben."

Kennzeichnung: **belegt** = im Code/in der Datei gelesen oder gemessen; **Verdacht, zu messen** = noch nicht gemessen.

## 1. Befund: warum LevelPilot heute falsch führt (belegt)

LevelPilot 3.12.71 plant **kurzsichtig im Spiel**. `Planner.lua` (2481 Zeilen) sammelt die Aufgaben in der Nähe (`P:CollectTasks`). Dann wählt es eine Fokus-Zone (`P:ChooseFocus`), ordnet die nächsten Ziele (`P:Order`, `P:TwoOpt`, `P:ExactOrder`) und fügt Flugpunkt, Binden und Ruhestein ein.

Einen Plan über die ganze Stufe 1–60 gibt es nicht. Jede Entscheidung fällt aus der Sicht "jetzt, hier". Daraus folgen die Fehler, die der Nutzer im Spiel gesehen hat:
- zu früh aus dem Startgebiet heraus (ERA-1),
- Questgeber nicht mitgenommen,
- Sprünge zwischen Zonen.

ERA-1 (3.12.71) und ORT-1 flicken die Startzone. Das Grundproblem bleibt: Ob ein Weg gut ist, zeigt sich erst über Stunden. Wann lohnt sich eine Zone? Was gehört in einen Ort zusammen? Wo bindet man den Ruhestein, und welche Kette zieht man vor? Das entscheidet ein Blick auf die nächsten 10 Ziele nicht.

## 2. Was andere gebaut haben (Quellen, alle gelesen)

| Projekt | Was | Ansatz | Lizenz | Nutzen für uns |
|---|---|---|---|---|
| **Factoruide** (brouznouf/factoruide) | Rechnet je Charakter die schnellste Route 1–60 für Forever, Era/Hardcore und TBC. Das Addon führt sie dann Schritt für Schritt. | **Modell → Simulation → Suche** (ARCHITECTURE.md): ganzes Spiel simuliert (Weg, Kämpfe, Beute, Quest-/Mob-EP, Ausbildung, Ausrüstung). Erste Route gierig oder **nach Orten und Stufenband** (Quest-Hubs als Blöcke). Danach **lokale Suche** (Stopp verschieben, Block oder ganzen Zonenaufenthalt verschieben, Quest einfügen/streichen, Flugpunkt/Binden einfügen, "ruin & recreate"). Simulated Annealing / Late Acceptance, **Turnier aus 8 Suchen mit festen Startwerten** (gleiche Anfrage = gleiche Route). | Code **MIT**, Daten **GPL-3** | Das Vorbild schlechthin: Aufbau, Zugarten und Gewichte übernehmen (mit Namensnennung). Seine Strafwerte: Zonenwechsel 240 s, Quest abbrechen 600 s, Grinden ×1,5 (max. 10 % je Stufe), Flug-Gold 1 h je Gold bis Stufe 30. Weitere Bausteine: Questlog-Grösse, Stufenfenster, Klassenquests als Pflicht. `notes/` hat Hinweise je Quest. |
| **Forever Route Lab** (laurencestokes) | Werkbank im Browser: Route planen, simulieren, prüfen, optimieren | Optimierer für **Abschnitte** zwischen festen Ankern. Start mit nächster Nachbar + günstigstes Einfügen, dann Beam-Suche, lokale Züge (or-opt, Tausch, 2-opt, Streichen), Kicks (iterierte lokale Suche). Gemessen: 1–6 % über einer 10× längeren Referenz. **Laufnetz (Recast-Navmesh) aus dem Forever-Client**: Gelände, Wasser, Gebäude (WMO), Objekte (M2). Beide Kontinente in 5,4 MB, mit Zonen-ID je Polygon und "Verbindern" (Aufzüge, Portale). | **GPL-3** | **Fertiges Laufnetz für Forever** (`public/nav`). Darf nur in LevelPilot_Data (GPL-3), nicht in den Kern. Messmethoden und Prüfregeln (Zählung "jeder Spawn erreichbar") übernehmen. |
| **Questwarden** (GREYsaurus) | Leveling-Addon Era 1–60 (alle 40 Volk-/Klassen-Kombinationen), TBC 1–70, Forever in Arbeit | Handgeschriebene Routen, **offline geprüft und verbessert**: Route-Audit, Ziele bündeln, nächster NPC zuerst, Zeitquests, Kill-Packs, Grind-Stellen an dichten Spawns. Gemessen: Grind-Anteil von 50 auf 49,98 Stufen. | **GPL-3** | **Referenzrouten für Era** zum Vergleich in ROUTE-Q. Seine Prüfwerkzeuge sind gute Vorlagen für unsere Routen-Prüfung. |
| **zugzug_leveler** (0p3nMike/wow-leveler) | Forever-Leveling-Addon mit RestedXP-Routen (1–21), Questlog-Modus | **Im Spiel alle 2 s neu planen:** kürzeste Reihenfolge der nächsten ~10 Stopps (TSP mit Questregeln), Questdaten aus AllTheThings (MIT). | keine Lizenzdatei gesehen | Nur als Idee: lokales Nachplanen der nächsten ~10 Stopps (macht LevelPilot schon ähnlich). Keinen Code übernehmen. |
| **b-errouane/leveling-add-on** | Deutsche Planungsnotizen (10 Dokumente) | `10-routing-konzepte.md`: Konzepte aus echten Guides – Schlenker, Kette fertig vor Hubwechsel, Grinden bis Stufe X, Ruhestein als Zustand, Flugpunkte als Investition, Questlog-Platz, Taschenplatz, Zeitquests, sich ausschliessende Quests | – (Notizen) | Checkliste, was ein Modell können muss (Abschnitt 4). |
| **EG Link output (Forever)** | Quest-Zwischenspeicher aus dem Forever-Client vieler Spieler | – | **CC BY 4.0** | Forever-neue Quests (Daten, EP), erlaubt mit Namensnennung. |
| **AllTheThings, pfQuest** | Quest-, Geber- und Spawn-Daten | – | **MIT** | Forever-Quests (Klassen, Völker, Geber, Vorbedingungen) zum Ergänzen und Gegenprüfen. |
| **Fachliteratur** | – | Orienteering Problem (Route mit Zeitbudget, maximaler Nutzen; Vansteenwegen u. a. 2011). Pickup-and-Delivery-TSP mit Vorrang (annehmen vor abgeben). | – | Unser Problem ist eine Mischung aus beiden, mit EP und Stufe als Zustand. Exakt lösbar ist es in dieser Grösse nicht. Darum Metaheuristik (lokale Suche + Annealing), wie Factoruide und Forever Route Lab. |

Lizenzlage LevelPilot: Der Kern ist "alle Rechte vorbehalten". **LevelPilot_Data steht unter GPL-3** und stammt schon aus Questie.
- GPL-3-Daten (Laufnetz von Forever Route Lab, Factoruide-Daten, Questwarden-Routen) dürfen nur ins **Datenpaket** und nur mit Quellenangabe.
- MIT-Code (Factoruide) darf auch in die Werkzeuge, mit Namensnennung.
- Questie selbst: "all rights reserved" (Questie#4447). LevelPilot_Data nutzt Questie schon. Das Risiko ist bekannt, nichts Neues.

## 3. Was wir selbst haben (belegt)

- **Strassennetz** Forever und Era aus den Geländetexturen (shared/werkzeuge/strassen/daten, LevelPilot ST-1..ST-5).
- **Gebiets-ID je Kartenstück (33,3 yd)**, Forever und Era: Ort/Unterzone für jeden Punkt exakt (`daten/gebiete/`).
- **Flugrouten mit Preisen und Wegpunkten** Forever und Era (TaxiNodes/TaxiPath/TaxiPathNode).
- **Questdaten**: LevelPilot_Data aus Questie (Quests, Geber, Ziele, Spawns, Händler, Flugmeister, Friedhöfe).
- **Rohdaten aus dem Client** (16.11. 17:40–17:50): root/obj/tex-Kacheln. Forever: 117 von 736 Kacheln der Östlichen Königreiche. Era: 196 von 687. Kalimdor fehlt noch. Fortsetzung, sobald der Nutzer den PC freigibt (`rohauszug.py`, setzt dort fort, wo er stand). Liegt beim Supervisor, nicht im öffentlichen Repo (Spieldateien).
- **LevelPilot-Messungen im Spiel**: Kill-Zeiten, Laufzeiten (Measure/Calib). Dazu die **virtuelle Reise** (Virtual.lua: Simulation 1–60 je Volk).

## 4. Alle Möglichkeiten, LevelPilot genauer zu machen (Prüfung des Supervisors)

| # | Möglichkeit | Wirkung | Aufwand | Bewertung |
|---|---|---|---|---|
| G1 | **Globale Route offline** (Modell → Simulation → Suche über 1–60, wie Factoruide) statt Planung im Spiel | Behebt die Ursache: Zonenreihenfolge, Hubs als Blöcke, Ketten, Binden/Flug als Investition | gross | **Kern des Plans** |
| G2 | **Orte = Gebiets-ID aus den Spieldateien** (ORT-1) + Häufung der Questgeber, auch einzelne in der Wildnis (Nutzer 17:34) | Kein "1760 yd"-Radius mehr. Ein Ort wird erst verlassen, wenn dort nichts Lohnendes offen ist | mittel | läuft (ORT-1) |
| G3 | **Laufnetz statt Luftlinie × Faktor**. Forever: Navmesh von Forever Route Lab (GPL-3, ins Datenpaket). Era: eigenes aus den Rohdaten (wenn vollständig), bis dahin Strassennetz + Gefahren-Zellen | Laufzeiten stimmen. Klippen, Wasser, Berge und Höhlen werden umgangen | mittel–gross | ja, in Stufen |
| G4 | **Flugzeiten aus den Flugpfad-Wegpunkten** (Länge ÷ Fluggeschwindigkeit) und **echte Preise** (TaxiPath.Cost) | Flug lohnt oder nicht: richtig gerechnet | klein | ja |
| G5 | **Simulation mit gemessenen Werten** (Kill-Zeiten, Laufgeschwindigkeit, Rast) aus LevelPilots Messungen statt Schätzungen | Zeiten realistisch, Route passt zum Spieler | mittel | ja |
| G6 | **Start aus dem echten Charakter** (erledigte Quests, Log, Ort, Ruhestein, Flugpunkte) | Route passt auch mitten im Spiel | mittel | ja (Stufe 2) |
| G7 | **Im Spiel nachführen statt neu erfinden**: der globalen Route folgen. Nur die nächsten ~10–15 Stopps lokal ordnen (TwoOpt/ExactOrder gibt es schon). Weicht der Spieler ab: zum nächsten passenden Punkt der Route zurückfinden | Kein Pfeil-Springen, keine Zonensprünge | mittel | ja |
| G8 | **Prüfung gegen Referenzen**: ROUTE-Q R1–R5 + Vergleich mit Questwarden-Routen (Era) und, wenn LevelPilot es laufen lassen darf, mit Factoruides Ergebnis je Volk (Gesamtzeit, Zonenfolge) | Beleg statt Behauptung | mittel | ja |
| G9 | **Hinweise je Quest** (Factoruide `notes/`, in eigenen Worten, wie dort verlangt) | weniger Suchen im Spiel | klein | später |
| G10 | **Forever-neue Quests** aus EG Link (CC BY 4.0) und AllTheThings (MIT) ergänzen | vollständige Route in Forever | mittel | ja |

Nicht gemacht: Factoruides Programm (Rust) hier selbst bauen und laufen lassen. Die Sicherheitsprüfung hat das Bauen fremden Codes in der Prüf-Sitzung abgelehnt. Ob LevelPilot es als Vergleich laufen lässt, entscheidet der Nutzer (Frage F-OPT-1 unten).

## 5. Plan (Auftrag an LevelPilot: OPT-ROUTE)

Reihenfolge: **ORT-1 und ROUTE-Q zuerst** (laufen). OPT-ROUTE baut darauf auf. Die automatische Routen-Prüfung aus ROUTE-Q ist der Massstab für jede Stufe.

**Stufe 1 – Modell und Simulation offline (Tools/, Python oder Lua):**
- Welt: Orte (G2), Laufnetz (G3, zuerst Strassennetz + Gefahren-Zellen, Forever dann Navmesh), Flug/Schiff/Zeppelin (G4), Ruhestein.
- Quests: Geber, Abgabe, Ziele mit Spawns, Vorbedingungen, sich ausschliessende Quests, Stufe, EP. Questlog-Grösse je Spiel aus den Spieldaten belegen, nicht raten.
- Simulation: Weg + Kampf + Beute + EP (gleiche Formeln wie Virtual.lua, ein Code für beide). Ausgabe Gesamtzeit und Zeit je Abschnitt.
- Abnahme: Simulation der bisherigen LevelPilot-Route = virtuelle Reise (gleiche Zahlen ±2 %).

**Stufe 2 – Suche über die ganze Welt:**
- Erste Route nach Orten und Stufenband (Hub-Blöcke), dazu gierig. Die bessere gewinnt.
- Verbesserung durch lokale Suche: Stopp und Block verschieben, ganzen Ortsaufenthalt verschieben, Quest einfügen/streichen, Binden/Flugpunkt einfügen, ruin & recreate. Annealing oder Late Acceptance. Mehrere Suchen mit festen Startwerten (gleiche Eingabe = gleiche Route, prüfbar).
- Bewertung: simulierte Zeit + Strafen. Startwerte wie Factoruide (Zonenwechsel 240 s, Quest abbrechen 600 s, Grinden ×1,5 und max. 10 %), als Einstellung, im Bericht begründet.
- Je Volk × Spiel (Forever, Era) × Modus (normal/speed). Klasse zuerst nur über Klassenquests.

**Stufe 3 – Ins Datenpaket und ins Spiel:**
- Ergebnis: Schrittliste je Volk/Spiel/Modus in LevelPilot_Data (GPL-3, Quellen in README/NOTICE). Grösse und Ladezeit messen (kein Ruckeln: PS/RF).
- Im Spiel: der Route folgen (G7). Nur die nächsten 10–15 Stopps lokal ordnen. Bei Abweichung zurückfinden, nie quer durch die Welt.
- Alte Clients nicht brechen. Ohne Datenpaket bleibt der heutige Planer als Rückfall.

**Stufe 4 – Prüfung:**
- ROUTE-Q R1–R5 für alle Völker, Era und Forever.
- Vergleich mit Questwarden-Routen (Era): Gesamtzeit, Zonenfolge, Grind-Anteil.
- Gegenprobe mit der alten Fassung. Der Nutzer testet im Spiel: Startgebiet und erste Zone je Volk.

**Fragen an den Nutzer** (bis zur Antwort am Rest weiter):
- F-OPT-1: Darf LevelPilot Factoruide (MIT-Code, GPL-Daten) offline als Vergleich laufen lassen und daraus lernen? Übernommen würde nichts ausser mit Namensnennung.
- F-OPT-2: Darf das Forever-Laufnetz von Forever Route Lab (GPL-3) ins Datenpaket LevelPilot_Data (auch GPL-3), mit Quellenangabe?

## Quellen
- Factoruide: https://github.com/brouznouf/factoruide (ARCHITECTURE.md, NOTICE.md)
- Forever Route Lab: https://github.com/laurencestokes/forever-route-lab (docs/ARCHITECTURE.md §11, docs/research/terrain-navigation.md, public/nav/NOTICE.md)
- Questwarden: https://github.com/GREYsaurus/Questwarden (docs/ROUTE_OPTIMIZATION.md)
- zugzug_leveler: https://github.com/0p3nMike/wow-leveler (README)
- b-errouane/leveling-add-on: https://github.com/b-errouane/leveling-add-on (10-routing-konzepte.md)
- EG Link output Forever: https://github.com/JIVESCORP/eg-link-output-wowf
- Vansteenwegen, Souffriau, Van Oudheusden: The orienteering problem: a survey, EJOR 209 (2011): https://econpapers.repec.org/RePEc:eee:ejores:v:209:y:2011:i:1:p:1-10
- Berbeglia u. a.: Static pickup and delivery problems (Survey): https://biblos.hec.ca/biblio/libreacces/33481133.pdf
