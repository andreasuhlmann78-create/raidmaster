# Strassen aus den Spieldateien (WoW Forever) – eigenes Werkzeug

Stand 16.11.2026, Supervisor (Auftrag des Nutzers 08:01: "nimm Zugriff auf die Spieldateien und fange an").
Eigenes Verfahren, kein fremder Code (Mapzeroth-Lizenz ungeklärt). Formatbeschreibung: wowdev.wiki (CASC, BLTE, ADT, WDT).

## Ablauf
1. `casc_lesen.py` – kleiner CASC-Leser (nur lesen) für die lokale Installation (`.build.info`, Produkt `wowf`).
2. `kacheln.py <WoW-Ordner> textur_nutzung.json` – zählt Bodentexturen je Kartenstück (Karte 0 und 1).
3. `strassen_texturen.json` – 34 Strassen-Texturen (Namen aus wowdev/wow-listfile, von Hand geprüft;
   Fussspuren/allgemeiner Boden bewusst NICHT).
4. `strassen_maske.py <WoW-Ordner> strassen_texturen.json strassen_maske.json` – Alpha-Karten (MCAL) der Strassen-Schichten,
   16×16 Zellen je Kartenstück (1 Zelle = 2,083 Yards), Schwelle 128. Läuft auf dem Rechner des Nutzers (18 s).
5. `strassen_netz.py strassen_maske.json <ordner>` (Cloud, numpy/scipy/scikit-image) – Lücken bis ~8 yd schliessen,
   Flecken < 60 Zellen weg, Skelett, Graph, Douglas-Peucker 4 yd, Stummel < 15 yd weg.

   Danach (ST-1, LevelPilot 16.11.2026) `verdichten()`: Skelett-Haufen (Kanten < 6 yd zwischen Knoten) zu einem Knoten,
   doppelte Spuren weg, Brücken bis 30 yd nur zwischen GETRENNTEN Teilen (loses Ende -> nächste Kante), Teile < 200 yd weg,
   Stummel < 15 yd weg, Ketten über Knoten mit Grad 2 zu einer Kante. Länge je Schritt in `stat.verdichten` (geht auf).

## Ergebnis (`daten/`, Client 1.60.1.70938, nach ST-1)
| Karte | Punkte | Kanten | Knoten | Teile | Länge (yd) | vorher (Rohnetz) |
|---|---|---|---|---|---|---|
| 0 Östliche Königreiche | 3383 | 1249 | 1104 | 95 | 126749 | 8833 Punkte, 9708 Kanten, 146918 yd |
| 1 Kalimdor | 1637 | 325 | 358 | 61 | 70791 | 3519 Punkte, 2681 Kanten, 80283 yd |
Lua-Datei 434 KB -> 122 KB (Lua 5.1: Laden 6 ms, ~0,7 MB). Vergleichsbilder: berichte/LevelPilot/strassen/.

- `GoldSentinelStrassen.lua` – Lua-Datendatei (Welt-Yards x nach Norden, y nach Westen; `p` flach, `e` Linienzüge 1-basiert).
- `strassen_netz.json` – dasselbe zum Prüfen, `strassen_maske.json` – Rohmaske (zum erneuten Bauen ohne Spieldateien).
- `vorschau-kalimdor.png` – Bild des Netzes.

## Geprüft (Stichproben Welt-Koordinaten)
Goldshire 8 yd neben der Strasse, Crossroads 34 yd (Strasse führt am Ort vorbei), Orgrimmar-Tor 28 yd. Achsen stimmen.

## Bekannte Grenzen (Verdacht, zu messen)
- Wege aus allgemeinem Boden (z. B. Desolace, Teile Tausend Nadeln, Ödland) erkennt das Verfahren nicht – dort Luftlinie.
- Durotar/Dörfer: Strassen-Textur auch als Bodenflecken -> viele kleine Teile (Filter MIN_TEIL ggf. höher).
- Brücken/Tunnel: Textur ist unter WMO-Brücken oft unterbrochen -> Lücken über Flüsse (Verbinden bis ~30 yd prüfen).
- Kleine Kanten (Ö. Königreiche 9708) – erledigt mit ST-1 (verdichten), siehe oben.
