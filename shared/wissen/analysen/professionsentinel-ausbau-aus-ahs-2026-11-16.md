ANALYSE – NUR FESTGEHALTEN, KEIN AUFTRAG – Fehler werden erst nach Freigabe des Nutzers behoben

# ProfessionSentinel (PS): Was aus AHSentinel (AHS) übernommen werden kann
Auftrag des Nutzers 15.11.2026 19:25: "Nimm dir ProfessionSentinel vor und schaue, was wir bzw. du in PS einbauen könntest von AHS
… ich denke, das gibt es einiges." Supervisor, Stand AHS 0.65.211, PS 0.9.45.

## 0. Ausgangslage
- PS nutzt AHS schon über die öffentliche API (AHSentinel.API: Price, NetSale, Deposit, MaterialCost, DisenchantValue, BestWay,
  SellSpeed, WorthUpTo, MarketState, LastScan, Subscribe) und alte Methoden (GetCurrent, RealPrice, On("SCAN_FINISHED")).
  Also: PS rechnet mit AHS-Preisen. Was fehlt, sind vor allem AHS' **Technik** (Tempo, Ruhe, Messung, Tests) und AHS' **Wissen
  aus echten Ergebnissen** (Buchhaltung, gelernte Quoten). Dazu gibt es Doppelungen (zwei Fenster mit "besten Rezepten").
- Gemessen 15.11.: PS ruckelt (Spitze 921 ms, > 100 Bilder über 50 ms) – siehe professionsentinel-2026-11-16.md P-1.

## 1. Technik aus AHS (grösster Nutzen zuerst)

### A1 Hintergrund-Aufgaben mit Zeitbudget (AHS A.jobs / RunJobs) – HOCH
AHS: jede schwere Rechnung ist eine Aufgabe (coroutine), die je Bild höchstens ein Budget (ms) rechnet, dazu LANGSAM-Diagnose
"längster Schritt bis Datei:Zeile". PS hat Portionen nur für den Neuaufbau des Panels; am Stück laufen AL.OnScan (Rezept-Alarm
über alle Figuren × Berufe × Rezepte), API.TodayCrafts (153 ms gemessen, PS-TC1), ns.RefreshAll / UI:Refresh (101–131 ms),
Item-Info-Nachladen. Übernahme: dieselbe Aufgaben-Schicht (oder AHS-Muster nachbauen), alle diese Wege als Aufgaben mit
≤ 4–8 ms je Bild, Ergebnis aus dem Zwischenspeicher. Wirkung: P-1 (921 ms) und PS-TC1 verschwinden.

### A2 Ruhemodus beim Snipen (AHS SN-RUHE1, A:SnipeDefer, Sn:QuietOn) – HOCH
Solange der AHS-Sniper scharf ist und das AH offen, pausiert AHS alles Unnötige (höchstens 30 Min., Zeitlimit). PS rechnet
genau dann am meisten (SCAN_FINISHED nach dem Vollscan -> Rezept-Alarm, Neuaufbau). Übernahme: PS fragt AHS (neu in der API:
API.QuietOn() -> true/false, Ende-Ereignis) und schiebt Rezept-Alarm/Neuaufbau bis nach dem Snipen auf. Das ist ein Gewinn
direkt für den Sniper (jedes Bild zählt im Wettlauf).

### A3 Item-Info-Tor (AHS GSL8-1, s214_iteminfo_gate) – MITTEL
Nach einem Vollscan kommen bis 9 400 GET_ITEM_INFO_RECEIVED je 2 s. PS-Disenchant.lua löst darauf jede Sekunde einen vollen
Neuaufbau aus. Übernahme: nur für selbst angefragte Items, gesammelt, höchstens einmal je n Sekunden ein LEICHTER Neuaufbau.

### A4 Messen wie AHS (Spiel-Profiler + Diagnose-Zeilen mit Ursache) – MITTEL
AHS-Zeilen LANGSAM/BILD mit Aufgabe und Datei:Zeile machen jede Spitze erklärbar. PS hat GSDIAG1, aber keine Zeile, die sagt,
WELCHER Weg 921 ms brauchte. Übernahme: Zeitmessung je Weg (OnScan, TodayCrafts, RefreshAll-Auslöser, Neuaufbau), Höchstwert je
Minute, rot > 16 ms. Lehre aus LevelPilot LP-D1: Rechenzeit OHNE Pausen messen. Lehre aus AHS TB168-1: kein
UpdateAddOnMemoryUsage im Betrieb.

### A5 Tests wie AHS (Szenario + Gegenprobe "mit alter Version rot") – MITTEL
AHS: 266 Szenarien in einer Nachbildung, jedes neue mit Gegenprobe. PS hat eine starke Testroutine; der Smoketest zeigt aber
FEHLER ohne zu zählen (P-3). Übernahme: Regel "jeder Befund ein bleibender Test mit Gegenprobe", Smoketest zählt FEHLER.

## 2. Wissen aus AHS (Gold-Nutzen)

### B1 Echte Herstellungs-Ergebnisse aus der AHS-Buchhaltung – HOCH
AHS Books/Ledger kennt Kostenbasis (was die Materialien WIRKLICH gekostet haben) und realisierten Gewinn je Verkauf. PS zeigt
"Trefferquote je Beruf: noch keine Fälle". Übernahme: neue AHS-API (z. B. API.RealizedCraft(itemID|spellID) -> Fälle, Ø Erlös,
Ø Kosten, Gewinn) – PS zeigt je Rezept "so lief es wirklich: n× hergestellt, Ø +x je Stück" neben der Prognose. Das schliesst
die Lücke zwischen Vorhersage und Ergebnis (markt-strategie.md: zuerst messen).

### B2 Gelernte Quoten statt Annahmen – MITTEL
AHS lernt Verkaufschance je Item ("77 % lernt noch"), Laufzeit und Entzauber-Ergebnisse (1280 eigene Fälle je Gruppe + Netz).
PS bekommt über WorthUpTo schon die Sicherheit (4. Wert), nutzt sie aber für "Heute herstellen" nur als ja/nein. Übernahme:
erwarteter Gewinn = Gewinn × Verkaufschance; Rezepte mit "lernt noch" gekennzeichnet; Gold/Std. mit echter Laufzeit.

### B3 "Kauf bis" je Material -> direkt Sniper-Ziele – HOCH (Komfort + Gold)
AHS rechnet eine Zahl "Lohnt bis" (A.Core:LimitFromNet, Kern.LohntBis). Für ein Rezept heisst das: höchster Preis je Material,
bei dem das Herstellen noch den Mindestgewinn bringt. Übernahme: PS rechnet je Material "Kauf bis" (Restgewinn auf die Zutaten
verteilt) und übergibt sie als Sniper-Ziele mit genau diesem Max (heute: AL.ToSniper nur mit aktuellem Preis). Der Sniper kauft
dann nie über der Gewinnschwelle (Gold-Sicherheit wie AHS SN-B10).

### B4 Warnschutz-Gedanke fürs Herstellen – MITTEL
AHS warnt vor Verlust beim Einstellen (Entscheid des Nutzers 19:15: "die Warnung ist top"). Übernahme in PS: vor "Alle
erstellen" bzw. "Heute herstellen" eine Warnung, wenn der erwartete Erlös nach Gebühr unter den echten Materialkosten liegt
(Kostenbasis aus B1, sonst Marktpreis) – mit Vorschlag, der die Warnung sicher NICHT wieder auslöst (Lehre WS-LOOP1).

### B5 Marktlage und Wellen – NIEDRIG (teilweise da)
AHS MarketState ("aufkauf/flut/dünn/alt") und Stufenband-Wellen. PS hat Levelwelle (0.9.41). Übernahme: im Rezept-Tooltip die
Marktlage des Produkts (Flut = jetzt nicht herstellen), Bandtrend wenn AHS ihn liefert (RK/MA4).

## 3. Doppelungen klären (Entscheid des Nutzers nötig)
### C1 Zwei "Beste Rezepte"-Fenster
Am Berufsfenster stehen heute AHS "Gewinn"-Fenster (Crafting.lua, Liste "Beste Rezepte (Gewinn)", Einkaufsliste-Knöpfe) UND das
PS-Panel. Zwei Listen mit eigenen Rechnungen widersprechen sich leicht (Grundsatz "eine Zahl", TB170-10). Vorschlag zur
Entscheidung: (a) PS ist das Berufs-Addon, AHS liefert nur Zahlen (API) und blendet sein Gewinn-Fenster aus, wenn PS geladen ist;
oder (b) beide bleiben, aber PS zeigt exakt AHS' Zahl (Test: gleiche Zahl je Rezept).

### C2 Rezept-Alarm vs. AHS-Hinweise
PS meldet "340 fehlende Rezepte im AH" (Summe, P-4). AHS kennt dieselben Angebote. Vorschlag: PS liefert die Liste, AHS zeigt
"Heute tun: Rezept X für Figur Y kaufen (Preis)" mit 1–3 Einzelfällen (psychologie.md: Einzelfall statt Summe).

## 4. Reihenfolge-Vorschlag (nach Freigabe)
1. A1 + A2 (Ruckeln weg, Sniper geschützt) – zusammen mit PS-TC1.
2. B3 (Kauf bis je Material -> Sniper) und B1 (echte Ergebnisse) – braucht je eine neue AHS-API (AHS-Sitzung, klein).
3. A3, A4, A5.
4. B2, B4, B5.
5. C1/C2 nach Entscheid des Nutzers.
Neue AHS-APIs dafür: API.QuietOn, API.RealizedCraft, ggf. API.LimitFor(itemID) ("Kauf bis" je Material aus dem Rechenkern).
