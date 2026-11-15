# LevelPilot – Wegführung in einer 3D-Welt (Konzept des Supervisors, 15.11.2026 abends)

Auftrag des Nutzers 19:59: "Bei LevelPilot darfst du dir so lange Gedanken machen, wie du willst, wie wir das Problem mit der
Wegführung lösen können – in einer dreidimensionalen Welt." Freigabe, Aufträge zu schreiben: Nutzer 19:58.
Grundsatz (19:58): Nutzen für den Spieler, einfach zu verstehen, maximaler Nutzen.

## 1. Das Problem, belegt
- Auslöser: Bildschirmfotos des Nutzers 19:00–19:10 am Auktionshaus in Unterstadt: "313 Yards (Weg unbekannt) – Der abtrünnige
  Lich" (NPC im Magieviertel, gleiche Stadt, andere Ebene). LevelPilot-Bericht 17:30: "Seit 4 min nicht näher (noch 131 Yards)".
- Ursache im Code (LevelPilot 3.12.35, Graph.lua):
  1. Knoten sind 2D: { Instanz, Nord, West, Zone } – keine Ebene. Unterstadt hat Ring, Viertel, Kanäle und darüber die Ruinen von
     Lordaeron: viele Punkte liegen in 2D übereinander.
  2. SNAP = 10 Yards: zwei gelaufene Punkte, die in 2D näher als 10 Yards liegen, werden EIN Knoten – auch wenn einer 20 m tiefer
     liegt. Damit entstehen "Teleporter" durch Decken und Böden.
  3. Luftlinien-Kanten (VIRT_RANGE 260 Yards, ×1,45) innerhalb einer Zone verbinden Punkte quer durch Wände und Ebenen.
  4. 3.12.35 (UC-W1) bevorzugt schon Wege nur über gelaufene Kanten – hilft, löst aber 2. nicht.
- Was WoW Addons NICHT gibt (belegt): Höhe. UnitPosition liefert für Z "immer 0, Platzhalter" und ist in Instanzen gesperrt
  (warcraft.wiki.gg API:UnitPosition; Blizzard-Forum "Altitude addon"). Eine echte 3D-Navigation mit Höhe ist also unmöglich –
  die Ebene muss aus anderen Zeichen erschlossen werden.

## 2. Idee in einem Satz
Nicht die Höhe messen, sondern die EBENE erkennen – aus Zeichen, die das Spiel liefert – und Wege nur dort verbinden, wo jemand
wirklich gegangen ist; Übergänge zwischen Ebenen (Rampe, Treppe, Aufzug, Sprung nach unten) werden als eigene, gelernte Tore
gespeichert.

## 3. Zeichen, aus denen die Ebene erschlossen werden kann (VERDACHT – zuerst messen)
| Zeichen | API | Erwartung |
|---|---|---|
| Karte unter dem Spieler | C_Map.GetBestMapForUnit, C_Map.GetMapInfoAtPosition | Unterstadt (eigene Karte) vs. Tirisfal/Ruinen; Höhlen/Kleinkarten |
| Unterzone | GetSubZoneText, GetMinimapZoneText | "Magieviertel", "Handelsbezirk", "Der Ring", "Kanäle" … |
| Drinnen/draussen | IsIndoors / IsOutdoors | Gebäude, Höhlen, Unterstadt |
| Raum-Wechsel | Ereignisse ZONE_CHANGED, ZONE_CHANGED_INDOORS, ZONE_CHANGED_NEW_AREA, NEW_WMO_CHUNK (falls im Client) | jeder Wechsel = möglicher Ebenenwechsel |
| Fallen | IsFalling | Sprung/Sturz = Einbahn nach unten |
| Bewegung ohne 2D-Weg | GetUnitSpeed + 2D-Position steht | Aufzug (steht in 2D, Unterzone/Karte wechselt) |
| Schwimmen | IsSwimming | Kanäle (Unterstadt), Wasser |
Messauftrag (Abschnitt 6) klärt, welche davon in Forever wirklich zuverlässig sind.

## 3b. Was die Spieldaten schon verraten (wago.tools, Zweig wowf = WoW Forever, abgerufen 15.11.2026 20:0x)
- UiMap (60 Karten): Unterstadt hat EINE Karte (1458) ohne Stockwerk-Karten -> C_Map.GetBestMapForUnit trennt die Ebenen in
  Unterstadt NICHT. Kleinkarten gibt es in Forever kaum.
- WMOAreaTable: Unterstadt besteht aus WMO-Gruppen (Räumen) mit eigenem Namen: Canals (90), Magic Quarter (12), Rogues' Quarter (12),
  Royal Quarter (7–14), Ruins of Lordaeron (95–106), Sewers (26–28), The Apothecarium (28), Trade Quarter (44), War Quarter (8),
  Undercity (82–92 = Ring/Gänge). Genau diese Namen liefert das Spiel als Unterzone (GetSubZoneText) – sehr wahrscheinlich das
  zuverlässigste Ebenen-Zeichen in Städten (zu belegen mit GSWegMess).
- TransportAnimation (49 Transporte): Fahrbahn und Takt jedes Aufzugs, z. B. die Unterstadt-Aufzüge (Einträge 20649–20657: Hub
  ~96,5 Yards, Takt 16,7 s), Donnerfels (4170–4173: ~61 Yards, 30 s). -> Wartezeit eines Aufzugs = halber Takt im Mittel
  (Unterstadt ~8 s, Donnerfels ~15 s), Fahrzeit aus der Bahn. Wo die Aufzüge stehen, steht nicht in den Spieldaten (Server) –
  aus Wowhead (Objekt-Ort) oder aus dem ersten gelaufenen Weg (B3).
- AreaTable/UiMapAssignment liefern Zonen- und Kartengrenzen (heute schon in LevelPilot genutzt).
Folge für B1: In Städten/Gebäuden ist der Ebenen-Schlüssel = Unterzone (WMO-Raumname) + drinnen; draussen bleibt ein Schlüssel je Zone.

## 4. Lösung in fünf Bausteinen
**B1 Ebenen-Schlüssel je Knoten.** Jeder aufgezeichnete Punkt bekommt einen Schlüssel aus den Zeichen, die sich als zuverlässig
erweisen (z. B. Karte + drinnen/draussen + Unterzone). Zusammenlegen (SNAP) und Raster-Suche NUR innerhalb desselben Schlüssels.
Draussen ohne Gebäude bleibt alles wie heute (ein Schlüssel "draussen" je Zone) – kein Verlust für das offene Gelände.

**B2 Luftlinien nur, wo sie sicher sind.** Luftlinien-Kanten nur draussen und nur innerhalb desselben Schlüssels; drinnen (Städte
mit Ebenen, Höhlen, Gebäude) ausschliesslich gelaufene oder geteilte Kanten. Lieber "Weg wird noch gelernt" als ein Pfeil durch die
Wand.

**B3 Tore zwischen Ebenen, aus echten Wegen gelernt.** Wechselt der Schlüssel zwischen zwei Aufzeichnungspunkten, die in 2D nah sind
(≤ 15 Yards), entsteht ein TOR mit Ort, Richtung und Art:
- Rampe/Treppe/Tür: beide Richtungen;
- Sprung/Sturz (IsFalling dazwischen): nur nach unten (Einbahn);
- Aufzug (2D steht ≥ 3 s, Schlüssel wechselt): beide Richtungen, Kosten = Wartezeit (gemessen, Start 15 s), Text "Aufzug".
Tore werden wie Wege geteilt (Gilde/Netz, GSWEGE1) – ein Spieler läuft es einmal, alle profitieren.

**B4 Startwissen für die Hauptstädte.** Für die Orte mit Ebenen (Unterstadt, Donnerfels, Orgrimmar, Eisenschmiede, Sturmwind,
Höhlen der Startgebiete) einmal sauber aufzeichnen (Aufnahme-Lauf mit dem Messwerkzeug, Abschnitt 6) und als Startdaten in
LevelPilot_Data mitliefern. Unterstadt zuerst: drei Aufzüge Ruinen↔Stadt, Ring, alle Viertel, Kanäle, Königsviertel.

**B5 Führung, die man versteht.** Der Weg wird in Abschnitte je Ebene geteilt; zwischen zwei Abschnitten steht ein Schritt mit
Klartext: "Aufzug nach unten (Ruinen → Unterstadt)", "Rampe hinunter ins Magieviertel", "Hier hinunterspringen". Der Pfeil zeigt
immer auf das nächste Tor, nicht auf das Ziel durch den Boden. Ist der Spieler auf der falschen Ebene (Schlüssel passt nicht zum
Abschnitt): "Du bist eine Ebene zu tief – zurück zur Rampe (40 Yards)". Kennt LevelPilot keinen Weg: ehrlich "Weg in Unterstadt
noch nicht gelernt – das Ziel ist im Magieviertel" (Unterzone des Ziels aus C_Map/Karte), statt eines falschen Pfeils.

## 5. Nutzen für den Spieler (Grundsatz 19:58)
- Frage, die es beantwortet: "Wie komme ich da hin?" – auch in Städten mit Stockwerken und in Höhlen.
- Auf den ersten Blick verständlich: Pfeil + ein Satz pro Tor ("Aufzug nach unten").
- Spart: Minuten Suchen in Unterstadt/Donnerfels/Höhlen, Frust bei "Seit 4 min nicht näher".

## 6. Zuerst messen (Messauftrag, bevor gebaut wird)
Mess-Werkzeug (passiv, nur aufzeichnen): je 0,2 s und bei jedem Ereignis eine Zeile mit Zeit, 2D-Position, Karte, Kleinkarte an der
Position, Unterzone, Minikarten-Zone, drinnen, fällt, schwimmt, Tempo, und die Ereignisse ZONE_CHANGED*/NEW_WMO_CHUNK. Nur
Änderungen speichern (klein). Testläufe des Nutzers (je 2–3 Minuten):
1. Unterstadt: Auktionshaus -> Bethor Iceshard (Magieviertel) und zurück.
2. Ruinen von Lordaeron -> Aufzug -> Unterstadt -> anderer Aufzug -> hinauf.
3. Donnerfels: Aufzug unten -> oben; eine Höhle in einem Startgebiet hinein und hinaus.
Ergebnis: Tabelle "welches Zeichen trennt welche Ebene" -> danach B1 festlegen. Ohne diese Messung kein Umbau (Perfektion:
Ursache belegt statt vermutet).

## 7. Tests (Nachbau)
- Zwei Ebenen mit GLEICHEN 2D-Koordinaten (Schlüssel A/B), Tor an einer Stelle: Weg führt immer über das Tor, nie direkt.
- SNAP legt Punkte verschiedener Schlüssel nie zusammen.
- Sturz-Tor nur nach unten; Aufzug mit Wartezeit in den Kosten.
- Falsche Ebene erkannt -> Hinweis; kein Weg -> ehrliche Meldung mit Unterzone.
- Regression: offenes Gelände (ein Schlüssel) liefert dieselben Wege wie 3.12.35.
- Leistung: Wegsuche weiter in Portionen ≤ 4 ms je Bild.

Quellen: warcraft.wiki.gg API:UnitPosition (Z immer 0, in Instanzen gesperrt); Blizzard-Forum "Altitude addon" (kein Z für Addons).
