# Marktstrategie und Prognose – Wissensbasis für AHSentinel

Gepflegt von der Prüf-Sitzung. Stand: 10. November 2026. Ergänzt `wirtschaft-forever.md` (Gebühren, Regeln) – diese
Datei behandelt **Strategie, Vorhersagen und Lernen**. Wer an Preisen, Absatz, Empfehlungen, "Heute tun", Markt-Reiter
oder Testroutine-Prognosen arbeitet oder Aufträge dazu schreibt, liest sie vorher. Regeln wie in `wirtschaft-forever.md`
Abschnitt 0: **belegt** nur mit Messung, sonst **vermutet** mit Messauftrag.

---

## 0. Ziel und Leitlinien (Entscheide des Nutzers, 10.11.)

- **Ziel:** AHSentinel soll das beste Auktionshaus-Addon werden – "so gut, dass es jeder haben muss" (09:27).
- **Einfachheit:** "so einfach wie möglich zu handhaben und zu verstehen" (09:22). Für den Spieler sichtbar: je Item
  eine Empfehlung und ein Knopf. Alles Lernen läuft unsichtbar im Hintergrund.
- **Ehrlichkeit:** Jede Vorhersage wird nachgeprüft, die Trefferquote gemessen und im Testbericht gezeigt (09:22).
- **Unsichtbare Lern-Datenbank,** die dem Spieler "extrem viel nützt" (09:22).
- **Markt-Reiter:** Die heutige Liste aller Items "braucht kein Mensch" – Daten bleiben im Hintergrund; der Markt-Reiter
  soll "Heute tun" ablösen (09:19). Suche bleibt zum Nachschlagen.
- **Entzauber-Daten des Nutzers nie anfassen** (09:25): kein Zurücksetzen, Umrechnen, Migrieren.
- Stufenplan (Vorschlag der Prüf-Sitzung 09:25): 1 Vorhersagen nachprüfen -> 2 Lern-Datenbank -> 3 neuer Markt-Reiter.

---

**Entscheid des Nutzers 10.11. 15:54:** Gerechnet wird mit dem aktuellen Markt (Kaufpreis jetzt, Verkaufswert aus
aktueller Preisleiter + Absatz). Der Durchschnitt ist nur Warnlampe ("frisch gestiegen" / "eingebrochen").

## 1. Grundsatz: Vorhersage -> Ergebnis -> Korrektur

Ein Addon, das schätzt, aber nie nachprüft, kann nicht besser werden. Darum gilt für jede Zahl, die eine Zukunft
behauptet ("verkauft sich in ~13 Std.", "Absatz 5/Tag", "Entzaubern bringt 12s"):

1. **Aufzeichnen** im Moment der Entscheidung (Einstellen, Kaufen, Entzaubern): was wurde vorhergesagt, mit welchen
   Eingaben.
2. **Ergebnis zuordnen**, wenn es feststeht (Verkaufsrechnung, Rückkehr per Post, Abbruch, Entzauber-Beute).
3. **Güte messen:** Trefferquote, Kalibrierung, mittlerer Fehler – je Warengruppe.
4. **Korrigieren:** systematische Fehler fliessen in die nächste Schätzung (z. B. "Staub: Dauer 40 % zu optimistisch").

**Wahrheit (Ground Truth) sind nur die eigenen Vorgänge:** Rechnungen im Briefkasten, abgelaufene Auktionen,
eigene Entzauber-Beute. Alles aus dem Scan ist indirekt.

---

## 2. Datenlage in WoW Forever (was wir wissen können)

| Punkt | Status |
|---|---|
| Der Scan (SendBrowseQuery) liefert je Item **nur Gesamtmenge und Mindestpreis**, keine Einzelauktionen | belegt (Code AHSentinel, modernes AH) |
| Marktwert = gewichteter Median der **Mindestpreise** (Halbwertszeit 3 Tage) = **Angebotspreis, nicht Verkaufspreis** | belegt (Code). TSM sagt dasselbe über seinen DBMarket: spiegelt Angebote, nicht Verkäufe |
| **"Verschwunden" ist nicht "verkauft":** Bei 24-Std.-Auktionen läuft der ganze Bestand täglich ab | belegt (Befund 10.11. 07:30: Schwere Leinenhandschuhe, S = Deckel) |
| Einzelauktionen mit auctionID/Restzeit gibt es nur bei der **Item-Suche** (Detail), bei Waren nur Menge je Preisstufe | vermutet – Messauftrag M2 |
| Gibt es in Forever `C_AuctionHouse.ReplicateItems` (alle Einzelauktionen auf einmal)? | **belegt 10.11.: 180'368 Auktionen in 14 s, mit Restzeit, ohne Besitzer, ohne auctionID – M1**. Wenn ja: Auktions-Verfolgung möglich (verschwindet eine Auktion lange vor Ablauf -> gekauft oder abgebrochen) |
| Rechnungen: Verkauf, Kauf, abgelaufen/abgebrochen kommen per Post | belegt (Ledger) |

Folge: **Markt-Absatz ist immer eine Schätzung.** Der einzige exakte Absatz ist der eigene. Darum: eigene Daten zuerst,
geteilte Daten anderer Spieler (Sync, ohne Namen) als Zweites, Markt-Schätzung als Letztes – und immer mit Sicherheit.

---

## 3. Was AHSentinel heute vorhersagt (Stand 0.65.68, Code-Prüfung 10.11.)

| Vorhersage | Funktion | Annahmen (Konstanten) | Status |
|---|---|---|---|
| Wert je Stück | `A:PriceInfo/RealPrice` | günstigstes Angebot des letzten Scans, Ausreisser < 10 % Median -> nächstes Angebot | Regel des Nutzers |
| Marktwert | `A:GetMarketValue` | Median der Mindestpreise, Halbwertszeit 3 Tage | Angebotspreis |
| Absatz/Tag (Markt) | `A:GetLiquidity` | 0,5 × Rückgänge der Menge / Tage, höchstens 0,5 × Ø-Menge | **vermutet** ("halb verkauft") |
| Absatz-Deckel | `A:SellOutlook` | höchstens 20 % der aktuellen Menge pro Tag (`SELL_CAP`) | **vermutet** |
| Warteschlange Q, Wartezeit W, Einstellungen N | `A:SellOutlook` | W = (Q + eigene)/S, N = W/Laufzeit, höchstens 7; "kaum" ab 7 Tagen | abgeleitet |
| eigene Verkaufsquote | `Ledger:PostRate`, `Comfort:SellChance` | ab 3 Einstellungen, 30 Tage | gemessen (eigen) |
| Gewinn pro Tag | `A:ProfitPerDay` | eigener Marktanteil 25 % (`MARKET_SHARE`), höchstens 20 % des Golds | **vermutet** |
| Preissturz | `A:IsCrashed` | 2 Preise < 60 % Median, ≥ 6 Std. auseinander | Faustregel |
| Entzauberwert | `Disenchant` | Tabelle (Forever: 75/20/5) + eigene/geteilte Ergebnisse, Gewicht 10 | Tabelle vermutet, Lernen richtig |

**Keine dieser Vorhersagen wird heute nachgeprüft.** Das ist die grösste Lücke.

---

## 4. Erkenntnisse aus dem Spiel (Messungen des Nutzers)

- **Absatz überschätzt (10.11.):** Schwere Leinenhandschuhe Q 222, S 293,8 = Deckel 0,5 × Ø-Menge 588 – sah aus wie
  "verkauft sich", 552 im AH verkaufen sich nie. Lehre: Rückgang der Menge ≠ Verkauf.
- **Entzaubern 10.11.:** 70× grün Itemstufe 26–30 Rüstung -> 73 Seelenstaub, 13 Grosse Astralessenz, **9 Grosse
  gleissende Splitter** (≈ 13 % der Entzauberungen). Forever-Leitfaden sagt 3–5 % -> bei 5 % wären ≥ 9 Splitter sehr
  unwahrscheinlich (≈ 1 %). Vorläufig: Splitter-Rate eher ~10 %. Weiter beobachten (Testbericht E13).
- **Entzauber-Einkauf mit Verlust (10.11., Nachrechnung 13:15):** mit den erzielten Preisen (Seelenstaub 6s 77c,
  Astralessenz 13s 69c, Splitter 37s 47c) ist ein grünes 26–30-Teil netto ≈ 12,9s wert – Kauf zu 14s war schon vorher
  Verlust; der Tooltip zeigte +30 %. Lehre: Materialwert immer zum erzielbaren Preis und mit der eigenen Menge rechnen.
- **Entzauber-Einkauf mit Verlust (10.11.):** 70 Teile für 9g 82s (Ø 14s), Material ≈ 8g 72s (Ø 12,5s) -> Verlust vor
  Gebühren. Die Kaufgrenze war zu optimistisch -> Sicherheitsmarge nötig (Abschnitt 6.6).
- **Gesamtprüfung 0.65.76 (10.11. 13:35):** Vollscan 224'659 Auktionen / 4'952 Items in ~2,2 s Lesezeit; ReplicateItems
  lieferte nach 23–24 Min. jeweils eine neue Liste. Entzaubern grün 26–30 Rüstung, 142 eigene: Staub 67,6 % /
  Essenz 21,8 % / Splitter 10,6 % (Ø-Menge 1,46 / 1,52 / 1,0) – Splitter klar über den 3–5 % des Forever-Leitfadens.
  Entzauber-Käufe (72): 68 % mit Gewinn, Beute im Median 10 % unter der Vorhersage. Erste "gemessene" Absätze waren
  10–20× zu hoch (Teilkäufe von Waren, Hochrechnung aus 23 Min.) – Messmethode für Waren: Menge je Preisstufe.
- **Beobachtung des Nutzers 10.11. 16:16 (vermutet, Messung läuft):** Entzauber-Materialien (Staub, Essenzen, Splitter)
  verkaufen sich in Forever gewöhnlich innert Minuten – Absatz-Grenzen beim Entzaubern nur als Sicherheitsnetz.
- **Schein-Flip 10.11. 12:41 (0.65.76):** Heute empfahl "Instabiles Magiepartikel kaufen bis 45s 97c, wieder
  einstellen um 2g 3s" – Marktwert (Median 14 Tage) 2g 3s, aber 855 Stück im AH zu 46–50s. Lehre: Wiederverkaufspreis
  nie aus dem Marktwert allein, sondern aus Preisleiter + Absatz (wo komme ich in der Laufzeit dran?).
- **Buchhaltung 10.11.:** Menge = Preis in Kupfer bei Einzelteilen (Feld 5); Erstattung ohne gebuchte Einzahlung
  (Einstellen über Blizzard-Fenster) -> positive Gebühren. Befund befund-buchhaltung-menge-und-gebuehren.txt.

---

- **12.11. – Levelwelle (Beobachtung des Nutzers + Daten):** "Die Leute leveln höher, entsprechend viele verkaufen ihr
  Zeug im AH." Daten bestätigen fallende Preise in den Bändern, durch die die Masse gerade levelt: Seelenstaub (26–35)
  6s88 -> 3s99 in ~6 Tagen, Goldene Schuppenarmschienen (iLvl 37) über 1g am 7.11. -> 17–18s am 12.11. (340 Angebote,
  zusätzlich ein Hersteller, der flutet). Leinenstoff dagegen stabil 17–25c (Startgebiet-Stoff, ständiges Angebot).
  Folgerung (vermutet, zu messen M-Welle): Ware eines Stufenbands verliert an Wert, sobald die Masse durch das Band ist
  -> eigenen Bestand dieser Bänder zügig verkaufen statt halten; Entzauber-Grenzen fallen mit; Nachfrage wandert nach
  oben (Material/Ausrüstung 40–60, ab 9.12. Raid-Verbrauchsgüter).
  Ergänzung Nutzer 12.11. 07:02: "Es wird auch Items mit höherem Item-Level betreffen." -> Die Welle wandert mit:
  höhere Bänder sind JETZT knapp und teuer und fallen, sobald die Masse dort ankommt. Also höherstufige Ware verkaufen,
  solange sie knapp ist (jetzt), nicht auf Vorrat kaufen und halten. Ausnahme vermutlich Stufe-60-/Raid-Bedarf
  (Nachfrage bleibt). Messbar mit M-Welle: Band 41–50 und 51–60 jetzt als Referenz festhalten.
- **M-Welle (neu 12.11.):** je Stufenband (Staub/Essenz/Splitter-Bänder) Tagesmittel der Material- und Grün-Preise aus
  den Tages-Ständen im Daten-Repo; sagt, wann ein Band "durch" ist und wo die Nachfrage als Nächstes steigt.

**GRUNDSATZ (Nutzer 14.11. 00:18):** "Nur wer den Markt vorausahnen kann, macht richtig Gold – aber immer fundiert und
belegbar." -> Jede Vorhersage (Welle, Trend, Absatz, Preis) wird gemessen, mit Trefferquote nachgeprüft und erst
angezeigt, wenn sie belegt ist. Markt-Wellen (M-Welle, MA4, MA6) sind Pflicht-Messungen, dazu ZYKLEN (Nutzer 00:19):
Tageszyklus (Stunde), Wochenzyklus (Wochentag, Wochenende, Raidtage ab 9.12.), Monatszyklus (ab ≥ 2 Monaten Daten,
Bot 90 Tage) – je Warengruppe/Stufenband; erst nach belegter Trefferquote als Rat ("heute Abend teurer verkaufen").

## 5. Strategien im Auktionshaus (allgemein + Forever)

| Strategie | Kern | Forever-Besonderheit |
|---|---|---|
| **Flippen** | unter dem üblichen Preis kaufen, zum üblichen Preis einstellen | Gewinn erst nach 5 % + erwartetem Einzahlungsverlust; Kapital ist gebunden |
| **Händler-Arbitrage** | Sofortkauf unter dem Händlerpreis | sicher, kein Einstellen nötig |
| **Umwandeln** | Entzaubern / Herstellen, wenn Ergebnis mehr wert | Material verkauft man wieder über das AH -> dessen Absatz zählt |
| **Lücken füllen** | wenig Angebot, stetige Nachfrage -> höher einstellen | bei Mindest-Einzahlung 1s: 24 Std. kostet oft gleich viel wie 2 Std. |
| **Überfüllung meiden** | Angebot ≫ Tagesabsatz -> nicht einstellen | jede Rückkehr kostet die Einzahlung |
| **Rhythmus** | Wochentag/Tageszeit, Raidtage, neue Inhalte (Icy Veins: Verbrauchsgüter Do–Mo kaufen, Di/Mi verkaufen) | Forever ist frisch: Leveling-Nachfrage (Stoffe, Leder, Erz für Berufe 1–150) läuft ab -> fallende Trends früh melden. Muster erst nach 2–3 Wochen Scans messbar (vermutet) |

### Konzepte aus TradeSkillMaster (TSM)
- **Drei Preisgrenzen je Item:** Minimum (darunter nicht einstellen/warten), Normal (ohne Konkurrenz), Maximum.
  Konkurrenz zwischen Min und Max -> knapp unterbieten. -> AHSentinel soll sie **selbst lernen** statt einstellen lassen.
- **Post-Cap** (höchstens so viele auf einmal) und **"nicht mehr einstellen nach N Ablauf"** -> in Forever doppelt
  wichtig (Einzahlung).
- **Abbrechen und teurer neu einstellen**, wenn die Konkurrenz weg ist – nur ab Mindestdifferenz; in Forever kostet
  Abbrechen die Einzahlung.
- **Angebotspreis ≠ Verkaufspreis:** TSM nutzt für Verkaufspreise Abrechnungsdaten vieler Spieler -> bei uns:
  Lern-Datenbank + Sync.
- **Nicht übernehmen:** Gruppen, Operationen, Formel-Sprache – zu kompliziert.

---

## 6. Methoden ausserhalb von WoW (übertragbar)

### 6.1 Überlebenszeit-Analyse (Survival) für "wann verkauft es sich?"
Aus Immobilien (Opendoor): Jede Einstellung ist ein "Leben"; jede Stunde ohne Verkauf ist ein negativer Datenpunkt,
der Verkauf ein positiver. **Abgelaufene oder abgebrochene Auktionen sind "zensiert"** (nur eine Untergrenze) und
**dürfen nicht weggelassen werden** – sonst wird die Schätzung systematisch zu optimistisch ("die riskantesten Fälle
werden am schlechtesten erklärt"). Ergebnis: Verkaufschance je Stunde ("Hazard") -> P(verkauft innerhalb 2/8/24 Std.)
und erwartete Dauer. Der Preis relativ zum Markt (eigener Preis / Marktwert) ist die wichtigste Eingabe, Konkurrenz
(Warteschlange) die zweite. Auf AH-Ebene: **Räumungsquote = Verkäufe / aktive Angebote.**
-> Für AHSentinel: Verkaufschance je Preislage (z. B. ≤ 95 %, 95–105 %, > 105 % vom Markt) je Warengruppe, mit
abgelaufenen Auktionen als zensierte Fälle.

### 6.2 Kalibrierung (Wettervorhersage, Statistik)
Eine Prognose "70 % Chance" ist gut, wenn von allen 70-%-Fällen etwa 70 % eintreffen. Messen mit
**Zuverlässigkeits-Tabelle** (Fälle nach vorhergesagter Chance in Klassen 0–20/20–40/…, je Klasse tatsächliche Quote)
und **Brier-Score** = Mittel von (Vorhersage − Ergebnis)², 0 = perfekt, 0,25 = Münzwurf bei 50 %.
-> Für AHSentinel: Testbericht-Abschnitt "Prognose-Güte".

### 6.3 Seltene Nachfrage (Croston / SBA, Lagerhaltung)
Bei Items, die nur ab und zu verkauft werden (viele Tage mit 0), unterschätzt ein einfacher Durchschnitt die Lage
falsch. Croston glättet **Menge je Verkauf** und **Abstand zwischen Verkäufen** getrennt; Absatz/Tag = Menge/Abstand;
SBA-Korrektur × (1 − α/2) gegen Überschätzung. Gilt, wenn > 30–40 % der Tage ohne Verkauf sind.
-> Für AHSentinel: eigene Verkäufe seltener Items so schätzen (statt Summe/Tage).

### 6.4 Schrumpfen zum Gruppenwert (empirisches Bayes)
Wenig eigene Daten -> Schätzung zum Gruppenwert ziehen, mit wachsender Zahl eigener Fälle zur eigenen Quote.
Genau so lernt AHSentinel schon beim Entzaubern (Tabelle wiegt wie 10 Entzauberungen). Gleiche Methode für
Verkaufsquote: Item <- Warengruppe <- alle Spieler (Sync) <- Grundwert.

### 6.5 Lagerentscheid (Newsvendor) und Market Making
Wie viel herstellen/kaufen/einstellen? Abwägen: Kosten zu viel (Einzahlungsverlust, gebundenes Gold, Preisdruck)
gegen Kosten zu wenig (entgangener Gewinn). Optimal ist die Menge, bei der die Absatz-Wahrscheinlichkeit dem
Verhältnis Gewinn/(Gewinn + Überschusskosten) entspricht. Market Maker halten **wenig Bestand** und senken den Preis,
wenn der Bestand wächst. -> Post-Cap aus Absatz × Laufzeit; Preis leicht senken bei grossem eigenem Lager.

### 6.6 Einsatzgrösse und Risiko (Kelly, Handel)
Bei kleinem, unsicherem Vorteil nur einen kleinen Teil des Kapitals einsetzen; Vorteil schätzen mit Sicherheitsabzug.
-> Tagesbudget je Strategie, solange ihre Trefferquote nicht belegt ist; Kaufgrenze = geschätzter Wert × (1 − Marge),
Marge aus dem gemessenen Prognosefehler.

### 6.7 Lernen durch Ausprobieren (Bandit)
Um zu erfahren, ob ein höherer Preis noch verkauft, gelegentlich leicht höher einstellen (z. B. 1 von 10 Einstellungen
+5 %) und messen. Nur mit Zustimmung (Option, Standard aus) – sonst verliert der Spieler Verkäufe.

---

## 7. Messaufträge (offen)

- **M1:** Gibt es in WoW Forever `C_AuctionHouse.ReplicateItems` / `GetNumReplicateItems` / `GetReplicateItemInfo`?
  Wie oft erlaubt? Nur Existenz und Grösse ins Protokoll, keine Namen.
  **10.11. 09:44 (GSMesstest 3, Forever 1.60.1): Die Funktionen GIBT ES** – ReplicateItems, GetNumReplicateItems,
  GetReplicateItemInfo, GetReplicateItemLink, GetReplicateItemTimeLeft, dazu SendSearchQuery, GetItemSearchResultInfo,
  GetCommoditySearchResultInfo, GetNumItemSearchResults. Offen: liefert der Aufruf wirklich Daten (Anzahl, Restzeit,
  Drosselung)? -> `/gsmess auktionen holen` am offenen Auktionshaus.
  **10.11. 10:06 GEMESSEN (GSMesstest 3, Undercity, Fraktions-AH): ReplicateItems LIEFERT DATEN.**
  - **180'368 Einzelauktionen**, Antwort nach **14,2 s** (Ereignis REPLICATE_ITEM_LIST_UPDATE), ohne Lua-Fehler.
  - Stichprobe 2005 (jede 90.): 998 verschiedene Items, Ø Menge 8,2 je Auktion (hochgerechnet ≈ 1,5 Mio. Stück),
    alle mit Sofortkauf, Mindestgebot 0 / Gebot 0 (keine Gebote gesehen), "alle Infos" bei 81 % (Rest: Item noch nicht
    im Cache – ItemID trotzdem da).
  - **Restzeit je Auktion vorhanden:** Stufe 1: 4,7 %, 2: 15,5 %, 3: 67,8 %, 4: 12,1 %. Bedeutung der Stufen in Forever
    (2/8/24 Std.) noch nicht belegt -> Messauftrag M1b.
  - **Besitzer wird NICHT geliefert** ("Besitzer bekannt nein") – keine Namen, gut für den Datenschutz.
  - **Keine auctionID** in den Replicate-Daten -> Verfolgung über Signatur (ItemID, Menge, Sofortkauf) und Zählen.
  - Offen: Wie oft erlaubt (Blizzard: ca. alle 15 Min.)? -> M1c. Lesedauer/Speicher im Addon -> M1d.
  **Folge:** Echter Vollscan mit Einzelauktionen und Restzeit ist möglich: Preisleiter je Item (Stück je Preis),
  exakte Warteschlange Q, und **Verschwinden mit langer Restzeit = gekauft oder abgebrochen** -> Markt-Absatz kann
  gemessen statt geschätzt werden (ersetzt "verschwunden = halb verkauft" und den 20-%-Deckel).
- **M2:** Liefert die Item-Suche (Detail) je Auktion auctionID und Restzeit (Ausrüstung) bzw. Menge je Preis (Waren)?
  Dann für die gehandelten Items Auktions-Verfolgung zwischen zwei Suchen.
- **M3:** Wochentag/Tageszeit-Muster: Mindestpreis und Menge je Stunde über 3 Wochen sammeln (kompakt: je Item und
  Stunde des Tages ein gleitender Median).
- **M4:** Splitter-Rate grün 26–30 weiter messen (eigene Entzauberungen), Ziel N ≥ 200.

---

- **M-Woche (neu 11.11.):** Preise und Angebotsmenge der 20 wichtigsten Waren je Wochentag und Tageszeit aus den
  Vollscans (Daten-Repo, 7 Tages-Stände) – prüft 8e Nr. 14 für Forever. Auswertung durch die Prüf-Sitzung.
- **M-Aufkauf (neu 11.11., Teilergebnis 12.11.):** Seelenstaub 22:07 12s98 -> 06:48 3s99: vorbei nach höchstens 8 3/4 Std.
  Genauer erst mit Scans dazwischen. Wie viele Stunden bis unter 6s? Prüft
  8e Nr. 13 und gibt die Zeit, die "Jetzt verkaufen" bei einem Aufkauf hat.

- **M-KOMPLETT (neu 13.11., Ziel des Nutzers: "wir brauchen komplette Marktanalysen um den Markt komplett zu messen"):**
  Ganzen Markt rund um die Uhr erfassen: Vollscans in festen Abständen (Ziel stündlich, mind. alle 2–3 Std.),
  Wiedererkennung der Auktionen über die Signatur ItemID:Menge:Sofortkauf, verschwunden aus langer Restzeit = gekauft
  oder abgebrochen, zentral zusammenführen, Abdeckung (gescannte Stunden der Woche) ausweisen. Werkzeug: GSMesstest 5,
  `/gsmess markt` (A3, `shared/messtest/README.md`). Zu messen: Lesezeit/Speicher (M1d), Bedeutung der Restzeit-Stufen
  (M1b), wie oft ReplicateItems erlaubt ist (M1c), Anteil mehrdeutiger Signaturen, Grösse der Zusammenfassung je Item,
  ob fremde Vollscans (anderes Addon) mitgelesen werden können. **Daraus ergibt sich der Weg** (Entscheid des Nutzers):
  (1) Blizzard-Web-API für Forever – **GEMESSEN 13.11. (Discord MN8, Bot 1.5.130): Forever ist in KEINEM Namespace
  vorhanden** (classic1x/classic/classicann/Retail geprüft, forever-Namespaces 403/404) -> entfällt; Wiederholung mit
  blizzard_api_check.py --list, falls Blizzard Forever aufnimmt,
  (2) Mitlesen fremder Vollscans in allen GoldSentinel-Addons (ohne Abfrage, mit Schalter zum Ausschalten und
  CHANGELOG-Zeile, keine Namen), Weitergabe über Gilde/Flüster-Netz (nur eigene Fraktion), (3) Uploader -> Bot-Server
  sammelt, führt zusammen, wertet aus. Fremde Daten nur mit Plausibilität und mehreren Quellen, nie allein für Kauf/Verkauf.
  **13.11. 14:52 GEMESSEN (GSMesstest 5, Forever 1.60.1, Fraktions-AH):** 243'817 Einzelauktionen, 6'115 Items, Daten
  12,5 s nach dem Abruf. Lesen aller Auktionen: 2,5–2,9 s Rechenzeit (über 82 Frames verteilt, ~35 ms je Frame ->
  5.1 liest 1500 je Frame), Speicher +32–38 MB, Vergleichsstand in den SavedVariables ~2,6 MB. Restzeit-Stufen:
  1: 3,7 %, 2: 14,4 %, 3: 70,6 %, 4: 11,2 %. **REPLICATE_ITEM_LIST_UPDATE kam 70'336 Mal** (eigener Abruf plus ein
  AHSentinel-Vollscan direkt danach, Angabe des Nutzers 15:18) – jedes Addon muss nach dem ersten Ereignis sperren
  (AHSentinel tut das: `run.reading`). Der zweite Lesevorgang "fremd ausgelöst" war der AHSentinel-Vollscan: **fremde
  Vollscans lassen sich mitlesen (erster Hinweis, gleiche 243'817 Auktionen)**; Vergleich 0 Min. -> ohne Aussage. Signaturen 84'737; **78,7 % der
  Auktionen liegen in mehrdeutigen Signaturen** (gleiche Stapel zum gleichen Preis) -> Absatz über die Zählung je
  Signatur (netto) messen; ein Verkauf mit gleichzeitigem Neu-Einstellen zum selben Preis bleibt unsichtbar
  (Absatz eher unterschätzt). Zusammenfassung je Item (ID, tiefster Stückpreis, Menge, Auktionen): 99'505 Zeichen =
  415 Addon-Nachrichten -> Gilde 5/s: 83 s, Flüstern 40/Min.: 10,4 Min. je Empfänger (gildenübergreifend nur Änderungen).
  Offen: Vergleich nach 30–60 Min. (Absatz, M1b), zweiter Abruf vor 15 Min. (M1c), Mitlesen eines AHSentinel-Vollscans.
  **M1c Nachtrag 16:42:** AHSentinel 35 Min. -> keine Antwort; dazwischen hatte GSMesstest um 15:41 abgerufen ->
  Drossel gilt sehr wahrscheinlich je CLIENT (alle Addons zusammen), Abstand ab dem letzten Abruf irgendeines Addons.
  **Vollscan-Ruckeln = Speicherbereinigung (16:42):** AHSentinel eigene Rechenzeit je Portion ≤ 5 ms, aber Lücken bis
  821 ms bei 56 Speicherbereinigungen und +53 MB -> weniger Tabellen/Zeichenketten je Auktion; nie zweimal lesen.
  **M1c belegt (AHSentinel 0.65.110, 13.11. 15:22, 8 Abrufe):** nach 15 Min. KEINE Antwort (90 s), nach 24–291 Min.
  immer neue Liste (9,5–14,9 s). -> Vollscan höchstens alle ~20 Min. je Spieler; für "stündlich" reicht 1 Spieler.
  **13.11. 15:41 GEMESSEN (GSMesstest 5.1, Vergleich über 25 Min., 249'646 -> 257'538 Auktionen, 6'140 Items):**
  geblieben 230'864, verschwunden 18'782, neu 26'674. Verschwunden nach Stufe beim ersten Scan: 1: 6'824 (fast alle
  abgelaufen), 2: 2'826, 3: 8'189, 4: 943 -> **aus Stufe 3+4: 9'132 Auktionen, Sofortkaufwert 11'422 g in 25 Min.** =
  gekauft ODER abgebrochen (Obergrenze; viel Abbrechen/Neu-Einstellen, da gleichzeitig 26'674 neu). Meiste Abgänge:
  3685, 4251, 8153, 7070, 2751, 8150, 4603, 7191, 2770, 211855. **M1b belegt (Stufenwechsel eindeutiger Auktionen in
  25 Min.):** Stufe 2 -> 1: 27 % (2'091 von 7'799) => Stufe 2 dauert ~1,5 Std. (30 Min.–2 Std.); Stufe 3 -> 2: 4,9 %
  (1'583 von 32'360) => Stufe 3 ~8,5 Std. (2–12 Std.); Stufe 4 -> 3: 3 % => Stufe 4 > 12 Std. -> **Stufen wie Retail:
  1 < 30 Min., 2 30 Min.–2 Std., 3 2–12 Std., 4 > 12 Std.** (Rest-Wechsel wie 1>3 sind gleiche Stapel, die ersetzt
  wurden). Lesen 2,9 s in 172 Bildern (1500 je Bild = ~17 ms – GoldSentinelMarkt liest mit 6-ms-Budget).
  Folge: Absatz immer als Spanne – Untergrenze (Abgänge minus neue Auktionen desselben Items) bis Obergrenze;
  Entscheidungen nach der Untergrenze (GoldSentinelMarkt v1: absatz/absatzMax).
  **Absatz geschätzt vs. gemessen (20 meistgehandelte):** Schätzung oft ×3–×4,5 zu hoch (2589: 1764 gemessen / 5216
  geschätzt; 11083: 398 / 1458) -> gemessen vor geschätzt.
  **Entzaubern 26–30 (524 Fälle):** Beute/Vorhersage Median 0,60 = Chance 1,05 × Menge 1,00 × Preis 0,57 – der
  Materialpreis ist das Problem, nicht die Chance; 55 % der 453 Entzauber-Käufe mit Verlust gegenüber dem Kaufpreis.
  **ÜBERHOLT/ZWEIFELHAFT (13.11. 23:40, Nutzer + Prüf-Sitzung):** Derselbe Bericht zeigt "Erlös erzielt/vorhergesagt 1,00
  (N 27)" und Verkauf nach 0,1–0,3 Std. -> Materialien verkaufen zum vorhergesagten Preis. f = 0,57 ist sehr
  wahrscheinlich ein Unterschied zweier Preisquellen im Addon (Vorhersage vs. MatPrice beim Entzaubern), kein echter
  Verlust. Auch 42 %/55 % rechnen mit diesem Wert -> NICHT als belegt verwenden, bis KF2 mit erzielten Preisen nachrechnet.
  **BELEGT 13.11. 23:50 (Prüf-Sitzung, 648 Entzauberungen):** Ursache = MEDIAN über Zufallsbeute. Median lv/ev 0,60,
  aber Mittel 0,97 und Summe/Summe 0,96 (2:4:a); 76 % der Einzelfälle unter 1, weil meist Staub fällt. Echt: Beute =
  1,35 × Einsatz (+35 %) bei 26–30, +20 % bei 36–40. REGEL: Bei Zufallsergebnissen (Entzaubern, Beute, Prozs) nie den
  Median oder Einzel-Verlustquoten, sondern Summe/Summe bzw. Mittel mit genug Fällen.

### 7b. FELDSTUDIE 14.11.2026 (Nutzer, ab ca. 14:11) – Massenverkauf Entzauber-Material
- Ablauf: 50 × Braune Leinenhose (4343) hergestellt (Leinenstoff à 25c, Grober Faden 10c), entzaubert, das ganze Material
  (Seltsamer Staub 10940, Geringe Magieessenz 10938) AUF EINMAL zum aktuellen Preis ins AH ("es ist eine Feldstudie").
- Erwartung Supervisor (Scan 13:48, eigene Quote 2:1:a): ≈ 43 Staub + 17 Essenz, Wert nach Gebühr ≈ 66s, Einsatz ≈ 55s, ≈ +11s.
- Messen: Verkaufsquote/-dauer je Menge, Unterbietungen, Preis vorher (Scan 13:48) und nachher (nächster Vollscan), realer Gewinn.
- NICHT zur Feldstudie (Nutzer 14:22, normal messen): 3 andere Teile entzaubert -> 5 Seelenstaub (11083) + 1 Grosser glänzender
  Splitter (11139). Andere Materialien -> in der Auswertung über die Item-ID getrennt; in der normalen Entzauber-Statistik zählen sie.
- Ergebnis Nutzer: eingestellt ca. 14:23, "alles verkauft" um 14:26 (≈ 3 Min., auch Seelenstaub/Splitter). Deutung offen:
  so schneller Abverkauf spricht für zu tiefen Preis oder Aufkäufer (Flipper/Sniper) -> Preis-Leiter vor/nach prüfen (Daten folgen).
- Dazu (Nutzer 14:27): 3 Auktionen wegen Unterbietung abgebrochen und neu eingestellt -> im Daten-Abbild prüfen: Abbruch-Grund
  "unterboten" (TB138-4) erfasst, PR1-Kette (gleiche Ware neu eingestellt), verlorene Anzahlung gebucht (BH-ANZ).

## 8. Sniping, Flippen, Handel – Grundsätze (Wunsch des Nutzers 10.11. 09:28: "in allen Bereichen der Beste")

Sniper heute (Sniper.lua): Ziele mit Höchstpreis/Menge/Budget, sucht selbst der Reihe nach, kauft nur per Tastendruck
(Mausrad/Taste, WoW verlangt Hardware-Ereignis), Waren mit Reservierung, Lockangebote (1 Stück ganz unten) lösen nicht
aus. Schnäppchen-Wächter legt vorübergehende Ziele an.

1. **Ein Schnäppchen ist erst eins nach dem Wiederverkauf.** Kaufgrenze = erwarteter Netto-Erlös (nach 5 %, nach
   erwartetem Einzahlungsverlust, nach Wartezeit) × (1 − Sicherheitsmarge) − Mindestgewinn. "% vom Marktwert" allein
   reicht nie (Marktwert ist Angebotspreis, Abschnitt 2).
2. **Liquidität vor Rabatt:** 30 % Rabatt auf etwas, das sich 1× pro Woche verkauft, ist schlechter als 10 % auf
   etwas, das sich 50× am Tag verkauft. Massstab: **Gewinn pro Gold Einsatz pro Tag**.
3. **Geschwindigkeit:** Begehrte Schnäppchen (Entzauber-Teile, 90 % Markt) sind in Minuten weg (10.11.: Kapuze und
   Weisenhandschuhe weg, Liste 10–18 Min. alt). Alte Scan-Listen nie als "kaufbar" zeigen; vor dem Kauf frisch
   suchen; die Wartezeit zwischen Suchen nach Treffer-Wahrscheinlichkeit verteilen (oft lohnende Ziele öfter).
4. **Köder und Fallen:** Einzelstück-Lockangebote, Mondpreise, plötzlich riesige Mengen zu Tiefstpreisen (Flutung ->
   Preis fällt weiter), Items mit wenigen Scans. Nur kaufen, wenn die Sicherheit hoch ist.
5. **Bestand begrenzen:** Nie mehr kaufen, als sich in der Laufzeit-Kette absetzen lässt (Absatz × Tage, Abschnitt
   6.5). Budget je Strategie und Tag (6.6).
6. **Nach dem Kauf:** Kauf mit Kaufpreis und geplantem Weg (einstellen/entzaubern/herstellen) im Prognose-Journal
   festhalten -> Ergebnis messen -> Kaufgrenzen je Strategie aus der echten Trefferquote nachstellen.
7. **Konkurrenz:** Wird man laufend unterboten (Unterbietungs-Häufigkeit je Item), lieber seltener und mit mehr
   Abstand einstellen oder das Item meiden; Preiskriege kosten in Forever jedes Mal die Einzahlung.
9. **Aufkauf (Squeeze) – Kaufen und Verkaufen getrennt bewerten (Erkenntnis 10.11. 17:59, belegt im Spiel):**
   Jemand kaufte alle günstigen Großen gleißenden Splitter auf. Danach lag nur noch Teures im AH (1g 15s, "frisch
   gestiegen seit 10 Std."). AHSentinel bewertete Entzauber-Teile mit diesem Preis und zeigte "Azurblaue Seidenkapuze
   +106 %" – ein Schein-Geschäft: Der Aufkäufer stellt selbst zum hohen Preis ein, neue Verkäufer kommen nach, der Preis
   fällt zurück, bevor unsere Ware fertig ist. Regel (asymmetrisch):
   - **Kaufen** (Einkauf, Markt, Sammelkauf, Sniper "lohnt bis"): Material mit Aufkauf-Kennzeichen höchstens zum Preis
     VOR dem Aufkauf bewerten (Marktwert bzw. Preis vor dem Sprung).
   - **Verkaufen** (eigenes Lager): aktueller Preis – jetzt ist die beste Zeit, eigene Bestände dieses Materials zu
     verkaufen (Hinweis "Preis künstlich hoch – jetzt verkaufen").
   - **Erkennen** aus dem Vollscan (alle ~23 Min.): Angebotsmenge in kurzer Zeit stark gesunken UND Mindestpreis stark
     gestiegen. Kennzeichen hält, bis Menge oder Preis wieder normal sind. Schwellen messen (Auftrag D6).
   Das verfeinert den Entscheid "aktueller Markt" nur für Kaufentscheide bei erkanntem Aufkauf; sonst gilt er unverändert.
10. **Verlustgrenze:** Fällt der Markt eines gekauften Items deutlich, nüchtern rechnen: jetzt billiger verkaufen vs.
   warten (Zeit × Risiko × Einzahlungen). Kein "es kommt schon zurück".

## 8b. Was ein Goldmacher wirklich braucht – Leitbild (Prüf-Sitzung, 11.11. 20:10, Auftrag des Nutzers)

Frage des Nutzers: "Mach dir sehr gründlich Gedanken, was ein Spieler, der Gold machen will, wirklich braucht."
Grundlage: zwei Tage Erfahrung des Nutzers (Splitter-Aufkauf, Schein-Gewinne, Buchhaltung im Minus trotz Plus, alte
Preise, Ruckeln, tote Angebote) und die Methoden in Abschnitt 5–8.

**Der Kreislauf eines Goldmachers:** Gelegenheit finden -> richtig kaufen -> umwandeln (entzaubern, herstellen,
liegen lassen) -> richtig verkaufen -> wissen, ob es sich gelohnt hat. Jede Funktion muss einen dieser fünf Schritte
messbar besser machen. Was keinen Schritt besser macht, ist Schnickschnack (Wunsch des Nutzers 11.11.).

**Was er wirklich braucht (Rangfolge):**
1. **Zahlen, denen er trauen kann.** Ein einziger falscher Wert (Aufkauf-Preis, 25 Std. alte Preise, Kosten zum
   günstigsten Preis) kostet Gold UND Vertrauen; danach glaubt der Spieler keiner Empfehlung mehr. Darum: frische
   Preise (≤ 30 Min.) oder klar "veraltet", Aufkauf-Schutz, Ausreisser raus, nie mit Durchschnitt statt Preisleiter.
   Jede Empfehlung wird nachgeprüft; eine Art Empfehlung mit Trefferquote < 60 % (ab 20 Fällen) wird nicht mehr
   gezeigt, bis sie besser ist (Selbstschutz).
2. **Eine Liste "Heute tun" statt vieler Ansichten.** Wenige Handlungen mit Betrag, nach **Gewinn pro Tag je
   eingesetztem Gold** sortiert (Marge × Umschlag, nicht Marge allein): kaufen (mit Höchstpreis), entzaubern,
   einstellen, abbrechen/neu einstellen, zum Händler, liegen lassen. Jede Zeile mit einem Klick ausführbar.
   Kapitalgrenzen eingerechnet (25 % gesamt, höchstens 10 % je Item).
3. **Richtig verkaufen.** Beim Einstellen zählen drei Zahlen: Preis aus der Leiter (nicht in eine Wand hinein
   unterbieten), **Wartezeit bis verkauft** (Menge vor mir ÷ Verkäufe je Std.), **Laufzeit** so kurz wie nötig
   (Forever: Einzahlung je 2 Std.). Neu einstellen/abbrechen nur, wenn der erwartete Mehrerlös die verlorene Einzahlung
   übersteigt.
4. **Verluste früh begrenzen.** Ware, deren Wert > 20 % unter den Einkauf fällt, oder die länger als 3 Laufzeiten
   nicht verkauft: bester Ausweg (verkaufen, entzaubern, Händler) statt hoffen.
5. **Ehrliches Ergebnis.** Gewinn aus Verkauftem (Kostenbasis), Rendite, wo Geld verloren geht (umgesetzt: BP, BE).
6. **Zeitpunkt (erst, wenn belegt).** "Jetzt günstig – kaufen" / "Jetzt teuer – verkaufen" aus Rhythmus (Stunde,
   Wochentag) und Absatz – erst nach 1–3 Wochen Vollscan-Daten, nie bei fallendem Trend als "kaufen", nie mit alten
   Preisen. Der Vorteil liegt typischerweise bei 5–15 % – nützlich, aber kleiner als 1–4.
7. **Ereignisse.** Raid-Start 9.12. (Onyxia, Hyjal, Barrow Deeps): Verbrauchsgüter und ihre Kräuter 2–3 Wochen vorher
   ruhig kaufen, in den ersten Raidwochen verkaufen. Leveling-Welle in Forever: Ware niedriger Stufen eher jetzt
   verkaufen als horten.

**Was er NICHT braucht:** viele Reiter (Überfüllt, Lücken, Trends als eigene Listen ohne Handlung), Statistiken ohne
Handlung, Kurven zum Anschauen, Zahlen ohne Quelle/Alter. Diese Informationen gehören – wenn überhaupt – als Grund in
eine Zeile von "Heute tun" oder in den Tooltip ("überfüllt: ~21 Tage bis verkauft").

**Entscheid des Nutzers 11.11. 20:07:** Zuerst "klar sehen, wann kaufen und wann verkaufen" (Punkt 6, beauftragt:
anweisung-jetzt-kaufen-verkaufen.txt). Punkt 2 ("Heute" fertig machen) im Hinterkopf behalten – später.

**Reihenfolge der Umsetzung (Empfehlung):** A Vertrauen (offene Fehler MP/D6/S8/VF, Trefferquoten-Schutz) -> B "Heute tun"
als Cockpit mit Gewinn/Tag/Gold, Kapital- und Item-Grenze, Einstellen mit Wartezeit/Laufzeit, Verlustgrenze ->
C Zeitpunkt und Ereignisse, sobald die Daten reichen.

## 8c. Der Verbesserungs-Kreislauf (Entscheid des Nutzers 11.11. 20:27)

"Du wertest aus und hast auf alles Zugriff, und wir speisen es wieder in AHSentinel ein, bis es so gut läuft wie es
nur geht." Ablauf, immer gleich:
1. **Daten holen:** Uploader liefert die SavedVariables bei jedem /reload ins private Daten-Repo (Auftrag DU1–DU6);
   bis dahin Datei vom Nutzer oder Gerätezugriff. Dazu Testberichte (#testberichte -> testberichte/).
2. **Auswerten (Prüf-Sitzung):** Rechnungen gegen das Regelwerk, Buchhaltung, Prognose-Treffer, Entzauber-Beute,
   Vollscan, Zeitmuster, Fehler/Diagnosen. Nur Belegtes als FEHLER, sonst VERMUTET mit Messauftrag.
3. **Erkenntnis ins Gehirn:** diese Datei bzw. wirtschaft-forever.md/buchhaltung.md (+ Projekt-Spiegel).
4. **Auftrag an das Projekt:** auftraege/AHSentinel/… + offen-ahsentinel.txt + Nachricht für den Nutzer. Die
   Prüf-Sitzung setzt nie selbst um.
5. **Nachprüfen:** neue Version gegen den Auftrag (Code, addon_check, Tests), dann wieder 1.
Messgrösse "so gut wie es geht": Trefferquoten je Empfehlungsart ≥ 60–70 %, Buchhaltung geht auf den Kupfer auf,
Entzauber-Beute/Vorhersage ≈ 1,0, keine Ruckler > 16 ms, keine Datenverluste.

## 8d. Strategie Entzaubern – genaue Einkaufsgrenzen (Analyse der Prüf-Sitzung, 11.11. 20:35)

Ziel des Nutzers (20:29): "bei jedem Trade oder Entzaubern dick Gold verdienen". Gold beim Entzaubern entsteht beim
EINKAUF: wer nur unter der Grenze kauft, verdient sicher; wer darüber kauft, verliert auch bei guter Beute.
Grundlage: Vollscan Laptop 11.11. ~16:00 (290'738 Auktionen), Preisleiter je Material; Verkauf = günstigstes Angebot
−1c, davon 95 % (AH-Anteil); Chancen/Mengen gemessen (deStats) bzw. Forever-Tabelle (vermutet).

| Material | günstigst | Menge bis +1 % |
|---|---|---|
| Seelenstaub 11083 | 3s 95c | ~570 |
| Große Astralessenz 11082 | 14s 20c | ~120 |
| Großer gleißender Splitter 11084 | 27s 79c | ~150 (der "1g 15s"/"87s" waren Aufkauf bzw. alte Preise) |
| Visionenstaub 11137 | 11s 93c | ~580 |
| Große Mystikeressenz 11135 | 31s 22c | ~130 |
| Großer leuchtender Splitter 11139 | 37s 86c | ~130 |
| Geringe Mystikeressenz 11134 | 9s 22c | – |
| Kleiner leuchtender Splitter 11138 | 12s 54c | – |

| Grüne Rüstung | Wert je Teil (netto) | **Kaufen höchstens (20 % Gewinn)** | Grundlage |
|---|---|---|---|
| Stufe 26–30 | 10s 50c | **8s 75c** | gemessen 71/21/8,5 %, Ø 1,52/1,49/1,0 (N 312) |
| Stufe 31–35 | 13s 05c | **10s 87c** | Tabelle 75/20/5 %, Seelenstaub Ø 3,5 (vermutet) |
| Stufe 36–40 | 22s 75c | **18s 96c** | gemessen 72,9/20/7,1 %, Ø 1,52/1,29/1,0 (N 85) |

**Befund:** AHSentinel zeigte am 11.11. für Stufe 36–40 "Lohnt bis" 25s 42c bzw. 26s 90c (Materialpreise alt: Visionenstaub
16s 56c statt 11s 93c, Mystikeressenz 30s 38c, Splitter 36s 94c) und markierte Teile zu 21–28s als "[Entzaubern lohnt]"
– nach den echten Preisen sind diese Käufe Verlust oder Nullsummen. Für Stufe 26–30 zeigte es 13s 55c (Splitter 87s).
-> Die grösste Goldquelle ist hier nicht eine neue Funktion, sondern KORREKTE Grenzen (Punkt L/MP, PD).
**Regeln:** Grenzen gelten für Rüstung; Waffen haben 20/75/5 (Essenz-lastig) und eigene Grenzen. Grenzen ändern sich
mit den Materialpreisen – immer aus frischer Leiter rechnen; beim Kauf vieler Teile sinkt der Materialpreis (eigene
Menge in die Leiter einrechnen, D3). Bei Aufkauf eines Materials mit dem Preis davor rechnen (D6).

## 8e. Mehrfach geprüfte Strategien (Recherche 11.11. 20:55, Auftrag des Nutzers: "doppelt und dreifach geprüft")

Aufnahmeregel: Eine Regel steht hier nur, wenn mindestens ZWEI unabhängige Quellen sie stützen. Spalte "Forever"
sagt, ob sie in WoW Forever schon gemessen ist (belegt) oder noch zu messen ist (vermutet). Quellen unten (Q1–Q7).

| # | Regel | Quellen | Forever |
|---|---|---|---|
| 1 | **Vor jedem Kauf/Einstellen den Netto-Gewinn rechnen:** Verkauf × (1 − AH-Anteil) − verlorene Einzahlungen − Kauf. Break-even = Kauf ÷ 0,95 (+ Einzahlung). | Q1, Q3, Q4, eigene Messung | **belegt** (5 % Anteil, Einzahlung je 2 Std. 5/20/60 % des Händlerpreises, mind. 1s – wirtschaft-forever.md) |
| 2 | **Nur minimal unterbieten (1c), nie Richtung Händlerwert;** tiefes Unterbieten zerstört den eigenen Preis. | Q1, Q3, Q5 | Ausrüstung: ganze Silber / −1s (Entscheid 10.11.), Waren: −1c |
| 3 | **Händler prüfen:** viele graue/niedrige grüne Teile bringen beim Händler mehr als im AH (nach Gebühren). Am Anfang eines Servers fallen AH-Preise oft unter den Händlerpreis -> dann Händler. | Q1, Q3 | vermutet (Forever-Start 4.11.: Stufe 30–45 fielen −50–67 %) |
| 4 | **Abgelaufene Einstellungen kosten:** jede verlorene Einzahlung in die Marge rechnen; nicht länger einstellen als nötig. | Q3, Q4, eigene Messung | **belegt** (Forever: Einzahlung je 2 Std., Ablauf/Abbruch = weg) |
| 5 | **Ziel-Marge 15–30 %** nach Gebühren; darunter lohnt das Risiko selten. | Q4, Entscheid 10.11. (20 % Entzaubern) | Entzaubern gemessen 16 % (N 146) – unter Ziel -> Grenzen korrigieren (8d) |
| 6 | **Verbrauchsgüter: unter der Woche/Wochenende kaufen (viel Angebot), vor den Raidabenden bzw. zum Raid-Reset verkaufen** (Nachfrage-Spitze, Angebot sinkt nach dem Reset). | Q2, Q4, Icy Veins (Abschnitt 5) | vermutet – ab 9.12. messen (Rhythmus/JK, Raidtage) |
| 7 | **Vor neuen Inhalten/Phasen einkaufen, in der Spitze verkaufen** (Preise steigen in Erwartung). | Q1, Q5 (9.12. als Nachfragepunkt) | vermutet – Raid-Start 9.12. |
| 8 | **Stetige Nachfrage schlägt hohe Einzelmarge:** Raid-Verbrauchsgüter, Entzauber-Material, Berufsmaterial; zufällige grüne Teile sind "laut" (Preis und Absatz schwer vorherzusagen). | Q1, Q4 | teils belegt: Entzauber-Material verkauft sich in Minuten (Nutzer, Messung Median 0,1 Std.) |
| 9 | **Streuen, nicht horten:** nie zu viel Gold in einer Ware; ein Konkurrent oder ein Angebotsschock kann den Preis zerstören. | Q1, Q4 | **belegt** (Splitter-Aufkauf 10.11.) -> 25 % gesamt, Vorschlag 10 % je Item |
| 10 | **Snipen nur unter der eigenen Grenze;** Fehl-Einstellungen und Ausverkäufe sind die besten Käufe. | Q1, Q4, Q6 | belegt (Sniper-Käufe 11.11.), Grenze muss stimmen (8d) |
| 11 | **Kapital und Buchführung sind Pflicht** für Handel im grösseren Stil; mit wenig Gold zuerst sammeln/entzaubern. | Q4, Q5 | – (Buchhaltung neu, BP) |
| 12 | **Grüne zum Entzaubern nur kaufen, wenn Materialwert (nach Gebühren) > Kaufpreis; Obergrenze je Stufenband aus dem aktuellen Staub-/Essenzpreis ableiten**, nicht fest. Ausbeute schwankt (1–2 Staub) – mit Durchschnitt rechnen. | Q7, Q4, eigene Analyse 8d | **belegt** (Entzauber-Ergebnisse N 326, Grenzen 8d) |
| 13 | **Aufkauf von Massenware hält nur kurz:** Konkurrenten stellen knapp darunter ein, bei viel Angebot ist der Preis in Stunden zurück. -> In einen Aufkauf hinein VERKAUFEN, nie dazu kaufen; Entzauber-Rechnung mit dem Preis vor dem Aufkauf. | Q8, eigene Messung | **belegt** (Splitter 10.11.: Spitze 1g15, wenige Messpunkte später 23–24s; Seelenstaub 11.11. 22:07 12s98 statt ~4s, 12.11. 06:48 wieder 3s99 (2744 Stk.) – Aufkauf hielt höchstens 8 3/4 Std.; dazwischen kein Scan) |
| 14 | **Einkauf zum Wochenbeginn, Verkauf gegen das Wochenende bzw. vor den Raidabenden;** Sonntagabend/Montag fallen die Preise (Wochenend-Beute wird eingestellt). | Q9, Q2, Q4 | vermutet – Forever-Rhythmus mit Vollscans je Wochentag messen (Messauftrag M-Woche) |
| 15 | **Gewinn pro Zeit statt Gewinn pro Stück:** jeden Kauf an (Netto-Gewinn ÷ erwartete Haltezeit) messen; schnell drehende Ware mit kleiner Marge schlägt langsame mit grosser. Gebundenes Gold begrenzen. | Q10, Q11, Q1 | teils belegt (Material verkauft in Minuten, grüne Teile langsam) |
| 16 | **Alterung mit Stufen und Boden:** Ware, die nach der erwarteten Zeit nicht verkauft ist, zuerst Preis prüfen (Konkurrenz?), dann stufenweise senken – nie unter den Boden (Break-even nach Gebühren); danach anderer Weg (Händler, Entzaubern, Herstellen). | Q10, Q11 | vermutet – Schwellen für Forever aus Verkaufszeiten ableiten |
| 17 | **Nur abbrechen und neu einstellen, wenn es sich lohnt:** unterbotene Auktion erst abbrechen, wenn der Mehrerlös die verlorene Einzahlung plus eine Schwelle übersteigt; sonst liegen lassen. | Q12 (cancelRepostThreshold), Q3, Q4 (verlorene Einzahlung) | **belegt** (Einzahlung geht beim Abbruch verloren, wirtschaft-forever.md) |
| 18 | **Entzauber-Ausbeute Forever, grüne Rüstung 26–30 und 36–40:** Staub 75 % × Ø 1,47 ≈ 1,10 je Teil, Essenz 20 % × Ø 1,5 ≈ 0,30. Splitter: TSM 5 %, unsere Messung 7–8 % – unsere Messung gilt, weiter zählen. | Q12 (Forever-Tabelle), eigene Messung (N 328 / 85) | **belegt** (Staub/Essenz), Splitter **offen** (Abweichung) |
| 19 | **Spätphase eines Servers: Ware für niedrige Stufen wird wieder teurer.** Wenn die Masse 60 ist, levelt kaum noch jemand durch die tiefen Bänder (wenig Angebot aus Beute), aber 60er mit viel Gold rüsten Twinks/Alts aus (Nachfrage). -> Gute grüne/blaue Teile für Twinks und Leveling-Ausrüstung später teurer verkaufbar; Zeitpunkt: nach der Levelwelle (Nr. 13/M-Welle). | Erfahrung des Nutzers (12.11.), Q13 | vermutet – Forever-Start 4.11., Spätphase noch nicht erreicht; mit M-Welle beobachten |
Nicht aufgenommen (nur eine Quelle oder nicht übertragbar): neutrale AH-Häuser mit 15 % (in Forever nicht geprüft),
"Wettbewerber offline abwarten" (Q2, spätes Spiel), Preis-Wucher durch Aufkauf (ethisch fraglich, Q1 – AHSentinel
macht das nicht). Weiterbildung 11.11. 22:30, nur eine Quelle: kleine Grüne an andere Verzauberer über 1,5 × Staubpreis
verkaufen (Q7); kleinen Vorrat häufig gehandelter Materialien gegen kurze Preisspitzen halten (Q2); Markt selbst
"zurücksetzen" durch Aufkauf (Q8 – Risiko gebundenes Gold, AHSentinel macht das nicht).

Quellen: Q1 [Warcraft Tavern – Gold and Trading Guide](https://www.warcrafttavern.com/wow-classic/guides/gold-and-trading-guide/) ·
Q2 [Engadget – What days should you buy or sell on the AH](https://www.engadget.com/2012/02/07/what-days-should-you-buy-or-sell-on-the-auction-house/) ·
Q3 [AccountShark – WoW Forever gold making guide](https://accountshark.net/blog/wow-forever-gold-making-guide) ·
Q4 [Timesaver – Classic Era AH flipping](https://timesaver.gg/blog/wow-classic-era-auction-house-flipping-gold) ·
Q5 [AccountShark – Forever, Abschnitt Timing (9.12.)](https://accountshark.net/blog/wow-forever-gold-making-guide) ·
Q6 [TSM-Grundlagen (Engadget Gold Capped)](https://www.engadget.com/2011-03-21-gold-capped-tradeskillmaster-advanced-guide.html) ·
Q7 [Engadget – Selling vs. Disenchanting](https://www.engadget.com/2009-03-14-time-is-money-selling-vs-disenchanting.html) ·
Q8 [Dealmaker's Den – Resetting AH prices](https://dealmakers-den.blogspot.com/2011/07/how-to-reset-auction-house-prices.html) ·
Q9 [Almar's Guides – Classic Auction House](https://almarsguides.com/WoW/Farming/Classic/AuctionHouse/) ·
Q10 [Underpriced – Inventory turnover for resellers](https://www.underpriced.app/blog/inventory-turnover-guide-for-resellers-2026) ·
Q11 [Red Stag – Slow-moving inventory](https://redstagfulfillment.com/how-to-identify-slow-moving-inventory) ·
Q13 [Blizzard-Forum – Confused by AH prices on leveling items](https://us.forums.blizzard.com/en/wow/t/confused-by-ah-prices-on-leveling-items/1762624) (weniger Angebot durch weniger Leveln, 60er mit Gold kaufen) ·
Q12 TradeSkillMaster v4.15.6, Quellcode (Laptop des Nutzers, 12.11.; unterstützt Forever, Interface 16001) – siehe 8f ·
dazu Icy Veins (Abschnitt 5 dieser Datei). Hinweis: Q3 und Q5 sind dieselbe Seite – zählen als EINE Quelle.

## 8f. Studium TradeSkillMaster v4.15.6 (Quellcode, 12.11. 06:45, vom Nutzer bereitgestellt)

**Lizenz:** "All rights reserved" (TradeSkillMaster LLC); abgeleitete Werke und Weitergabe verboten, nur einige
Bibliotheken (LibTSMCore/Util/Class/Database/Reactive) sind MIT. -> **Kein TSM-Code in GoldSentinel-Addons.** Nur
Ideen, Spielmechanik-Fakten und Vorgaben als zweite Quelle zum Gegenprüfen. TSM unterstützt Forever ausdrücklich
(eigene Forever-Daten, Changelog: "[Forever] Fixed disenchant values …").

**Entzauber-Tabelle Forever (grüne Rüstung, Erwartung je Teil):** 5–15 Seltsamer Staub 1,2 · 16–20 1,85 ·
**21–25 Seltsamer Staub 4–6 (Ø 3,75!)** · 26–30 Seelenstaub 1,1 + Gr. Astral 0,3 + Gr. gleissender Splitter 0,05 ·
31–35 Seelenstaub 2,55 + Ger. Mystiker 0,3 · 36–40 Visionenstaub 1,1 + Gr. Mystiker 0,3 · 41–45 Visionenstaub 2,55 ·
46–50 Traumstaub 1,1 · 51–55 Traumstaub 2,55 · 56–60 Illusionsstaub 1,1. Waffen: Essenz 75 %, Staub 20 %.
Waffen 21–30 geben in Forever Grosse Magie-Essenz (anders als Vanilla).
Abgleich mit unseren Messungen: Staub und Essenz stimmen (siehe 8e Nr. 18); Splitter bei uns höher (7–8 % statt 5 %).
Band 21–25 mit 4–6 Staub: nur TSM, bei uns nicht gemessen -> Messauftrag M-DE21 (lohnt sich Stufe-21–25-Grün besonders?
  Seltsamer Staub 12.11.: 91c -> 3,75 × 91c ≈ 3s41 je Teil plus Essenz).

**Vorgaben von TSM (Erfahrung tausender Spieler, gelten als EINE Quelle):**
- Einstellen: Boden = max(25 % Marktwert, 1,5 × Händlerpreis), Normal = max(200 % Marktwert, 12 × Händler),
  Decke = max(500 % Marktwert, 30 × Händler). Günstigstes unter dem Boden -> nicht unterbieten (nicht einstellen oder
  zum Rücksetzpreis). Unterbieten 1c. Höchstens 5 Auktionen je Item gleichzeitig (postCap).
- Abbrechen: unterbotene abbrechen nur, wenn der Neupreis mindestens 1g (Schwelle, einstellbar) besser ist.
- Sniper: kaufen unter max(Händlerpreis, Anteil × Regions-Marktwert); Anteil steigt mit dem Wert (5 % bei billigen,
  bis 80 % bei sehr teuren Items) – billige Items nur bei sehr grossem Rabatt.
- Händler: nach 20 Abläufen an den Händler (sellAfterExpired), Mindestgewinn Herstellen 100g (Retail-Massstab).
Übertragbar nach Prüfung: Boden/Abbruch-Schwelle (8e Nr. 16/17). Zahlen sind Retail-geprägt, für Forever neu messen.

## 8g. Markt-Reiter: was zuverlässig ist und wie wir es messen (Prüf-Sitzung 13.11. 06:00, Entscheid des Nutzers)

Entscheid: "Alles was zuverlässig ist, wird so gemacht; halb- und nicht Zuverlässiges braucht bessere Messdaten."
Neuer Reiter: Lage (Bänder) / Mein Lager / Chancen / Trefferzeile – Auftrag anweisung-markt-reiter.txt (MR, MA).
- **Grundsätze von ausserhalb WoW (je 2 Quellen):** GMROI = Bruttogewinn / durchschnittlicher Lagerwert, also Marge
  und Umschlag zusammen (Q14 Shopify, Q15 SPS Commerce). Abschreiben nach Alter, Absatz und Lagerlage, früh und
  laufend statt spät und tief; Rabatt wirkt nicht linear (Q16 o9 Solutions, Q17 invent.ai). -> "Mein Lager" sortiert
  nach Verlust beim Warten, Chancen nach Gold je Tag je eingesetztem Gold.
- **Zuverlässig:** Wert jetzt aus der Preisleiter (frischer Scan). Händler-Rechnung, sofern der Händlerpreis stimmt.
- **Halb:** Bänder (Richtung klar, Zahlen noch je Item, 9 Tage), Entzaubern (68 % von 72, Grenze zu optimistisch).
- **Nicht:** Absatz (Abbruch zählt als Verkauf; Rezept 24/Tag bei 39 Angebot) -> Flippen/Lücken/Überfüllt gesperrt;
  keine Nachprüfung (forecastStats leer); Händlerpreis Eisengranate vermutlich falsch.
- **GEMESSEN 13.11. (Trend-Rückblick, eigene Daten, Tagesmedian Mindestpreis 5.–13.11., ~11'600 Fälle):**
  nach 3 Tagen Fall > 15 %: nächster Tag weiter fallend 47 %, gleich 29 %, Umkehr 24 %.
  nach 3 Tagen Anstieg > 15 %: Umkehr 61 %, weiter steigend 21 %.
  Folge (vorläufig, Startwoche enthalten, wöchentlich wiederholen): fallend -> zügig verkaufen; steigend -> Spitze,
  jetzt verkaufen, nie kaufen/halten.
- **Messaufträge:** MA1 Verkauf vs. Abbruch (Relist-Erkennung, eigene Auktionen als Wahrheit), MA2 Empfehlungs-
  Protokoll, MA3 Händlerpreis, MA4 Bänder, MA5 Entzauber-Nachkalkulation, MA6 Trend-Rückblick (Prüf-Sitzung).
- **Entscheid des Nutzers 13.11. 06:18: Rechenkern statt Spielstile, streng überwacht.** "Das Addon ist nicht nur für
  mich" – keine Stile, sondern Wege (rein -> umwandeln -> halten -> raus), Fähigkeiten automatisch (Berufe, Gold,
  Rhythmus, Risiko-Wahl), EIN "Lohnt bis" für Tooltip/Sniper/Markt/Lager. Haltedauer bis zum nächsten Login.
  Überwachung: Testbericht "MARKT-KERN", Grenzwerte Trefferquote ≥ 60 % je Weg, Fehler "Lohnt bis" ≤ 15 %,
  MA1-Fehler ≤ 20 % (anweisung-markt-reiter.txt Teil E). Prüf-Sitzung prüft jede Version und wöchentlich.
- **GEMESSEN 13.11. Herstellen (Rezepte ProfessionSentinel Data_Forever, Preise 06:40, nach 5 %, günstigstes Angebot):**
  Koch/Alchemie-Rezepte mit > 10 % Gewinn: Stufe 1–124 25/65, 125–224 42/87, 225–300 41/77. Tiefe Kochrezepte
  verlieren 1–2s (rohe Zutat gefragt – Leveler kochen selbst), höhere lohnen (Raptor-Rippchen 5s86 -> 26s99, Golddorntee
  4s11 -> 18s24, Trunk des Wasserwandelns 11s79 -> 2g). Vorbehalt: Absatz unbekannt (MA1), Zutaten zum Einzelpreis,
  dünne Märkte. -> Rechenkern rechnet beide Richtungen (herstellen / roh verkaufen).
- **GEMESSEN 13.11. 08:16 (Buchhaltung "Heute", AHSentinel 0.65.99, Bild des Nutzers – nachgerechnet, geht auf den Kupfer auf):**
  Verkauft 24g17s74, Eingesetzt 20g46s43, Gebühren 13s70, Gewinn 3g57s61, davon Erlös ohne Einkauf 5g02s09 -> mit gekaufter
  Ware −1g44s48 (Rendite −7 %). Seelenstaub 354 Stk.: Erlös 12g59s53, Einsatz 15g74s16 (Kostenanteil aus Entzauber-
  Käufen), −45 % auf den Teil mit Einkauf (ca. 8g66 Erlös); Große Astralessenz +100 % (Verkauf in die Spitze 20–29s),
  Großer gleißender Splitter +219 %. Lehre: Entzauber-Käufe 26–35 wurden mit Staubpreisen vor dem Fall (≈ 4–5s) bewertet;
  Staub ist auf 3s56–3s76 gefallen (Levelwelle) -> der Staub-Anteil macht Verlust, nur die Spitzen-Verkäufe von Essenz/
  Splitter retten den Tag. Bestätigt RK6/WL3 (Einkaufsgrenze um den erwarteten Fall senken) und MA6 (Spitze verkaufen).
- **GEMESSEN 13.11. 12:55 (AHSentinel 0.65.108 Testroutine, echte Daten seit 11.11.):** Verkaufs-Prognose schlecht kalibriert:
  "80–100 %" -> 30 % verkauft (N 57), Brier 0,559 (schlechter als Münzwurf 0,25). Entzauber-Käufe 453: 43 % mit Gewinn,
  Gewinn je Gold 0,35; Beute/Vorhersage 26–30 = 0,60 (Chance 1,06 × Menge 1,00 × Preis 0,57) -> Fehler liegt im Preis
  (Levelwelle), nicht in der Ausbeute. Entzauber-Chancen grün Rüstung gemessen: 26–30 (594): Staub 72,7 / Essenz 21,2 /
  Splitter 6,1 %; 36–40 (124): 72,6 / 20,2 / 7,3 % (Tabelle 75/20/5 bestätigt, Splitter eher 6–7 %). Abbruch-Faktor 0,50.
  Quellen: Q14 https://www.shopify.com/blog/gmroi · Q15 https://www.spscommerce.com/community/articles/gmroii-combining-sales-profitability-and-asset-efficiency
  · Q16 https://o9solutions.com/articles/effective-markdown-optimization · Q17 https://www.invent.ai/blog/markdown-optimization-for-inventory-performance

### BAUPLAN 0.66 RECHENKERN (14.11. 09:10, freigegeben) – auftraege/AHSentinel/anweisung-rechenkern-066.txt
Lernschicht (zählen, Vorsicht bei wenigen Fällen k = 2, Summe/Summe, Alter zählt weniger), ehrliche Prüfung (ohne eigenen
Fall, gegen Grundlinie, Anzeige erst wenn besser, Rückfall), Vorausahnen (Verkaufspreis als Zahl, Kaufgrenze lernt, Welle ->
sofort verkaufen, Zyklen nur messen), Tabellen von aussen (Montag). Reihenfolge S1–S5.

### GEMESSEN 14.11. 08:20 – Welche Prognose trifft? Nachrechnung OHNE den eigenen Fall (Daten PC 14.11. 07:44)
Werkzeug addon-check/marktanalyse/prognose_vergleich.py. 64 abgeschlossene Einstellungen (Abbrüche raus), 27 verkauft (42 %).
Jede Vorhersage nur aus den ANDEREN Fällen gelernt (leave-one-out), sonst schönt sie sich selbst.
- Alte Prognose (fast überall 80–100 %): Brier 0,50, Treffer 44 %. Schlechter als Raten.
- Immer "verkauft sich nicht" sagen: 58 % Treffer (Grundlinie, jede Prognose muss darüber liegen).
- Chance je Preisstufe (Preis/Marktwert): Brier 0,248, Treffer 66 %. Besser als alt, aber nur so gut wie ein Münzwurf beim
  Brier. Meine frühere Zahl "69 %" (08:05 im Chat) war MIT dem eigenen Fall gerechnet und damit zu optimistisch.
- Schlangen-Modell "vor mir liegen Q Stück, Absatz S je Laufzeit": beim Einstellen lag der Nutzer in 60 von 64 Fällen
  GANZ VORNE (Q = 0) – trotzdem nur 26 verkauft. Auch wo der Absatz rechnerisch das Doppelte der Menge war: 8 von 27.
  -> Die Schlange BEIM EINSTELLEN sagt nichts voraus. Entscheidend ist, was DANACH passiert: andere stellen billiger ein
  (Unterbieten), der Nutzer zieht zurück (Abbruch) oder es läuft ab. (Mein Vorschlag 08:05 "Schlange beim Einstellen"
  war damit widerlegt – korrigiert.)
- Folgerung (Hypothese, zu messen): Die Chance ist ein WETTLAUF: kommt ein Käufer, bevor jemand billiger einstellt?
  Braucht je Item: Käufe je Stunde (gemessen) und neue billigere Angebote je Stunde (aus aufeinanderfolgenden Scans).
  Chance in 2 Std. ≈ Käufe / (Käufe + Unterbietungen) über die Laufzeit. Messauftrag M-WL1 (siehe 7).
- Wettlauf geprüft (unterboten.py, 08:35): Laufzeiten mit mindestens einem Scan (45 von 81; schnelle Verkäufe fallen meist
  zwischen zwei Scans und fehlen hier). Unterboten (fremdes Angebot billiger während der Laufzeit): 2 verkauft, 15 abgelaufen,
  5 Abbruch -> 2 von 17 verkauft (12 %). Nicht unterboten: 4 verkauft, 11 abgelaufen, 8 Abbruch -> 4 von 15 (27 %).
  -> Unterbieten halbiert die Chance ungefähr. ABER auch ohne Unterbieten laufen die meisten ab: in der Welle kamen in
  2 Std. schlicht zu wenige Käufer. Beides gehört in die Rechnung: Käufer je Stunde UND Unterbietungen je Stunde.
  Abbrüche: nur 5 von 13 (mit Scan) waren in den Scans als unterboten sichtbar – Scans alle 15–60 Min. sind zu grob;
  der Abbruch-Grund wird im Journal NICHT gespeichert (cr leer bei allen 17, TB138-4) – muss AHSentinel beim Abbruch
  selbst festhalten.
- Datenlage: fast nur Staub/Essenz, eine Figur, 4 Tage, mitten in der Welle. Jede Zahl hier ist Richtung, nicht Gesetz.

### GEMESSEN 14.11. 01:00 – Verkaufs-Prognose (81 Einstellungen, alle 2 Std., fast nur Staub/Essenz)
- Händler stellen nur 2 Std. ein (Nutzer 00:50). Abgebrochene (17) zählen nicht (zensiert, Nutzer 00:50).
- Ohne Abbrüche: vorhergesagt 88 %, verkauft 47 % der Stücke; 37 von 64 abgelaufen ohne Verkauf.
- Erster Verkauf Median 12 Min. (n 27) – ABER (Korrektur des Nutzers 00:53): "schnell oder gar nicht" stimmt NICHT. Wird er
  unterboten, nimmt er das Angebot heraus statt es ablaufen zu lassen -> Abbrüche = meist "unterboten", die Ware wäre evtl.
  später verkauft worden. Abbruch ist darum weder Treffer noch Fehler, sondern Teil der Kette (unterboten -> neu, billiger).
- Preis entscheidet (belegt als Richtung, kleine Fallzahl): Preis/Marktwert ≤ 1,00 -> 59 % (n 30); 1,10–1,25 -> 25 % (n 7);
  > 1,50 -> 15 % (n 9). Die Prognose reagiert kaum darauf (überall 80–100 %).
- Folgerung: Chance je Preisstufe lernen; für 2-Std.-Händler die Kette bis zum endgültigen Verkauf messen (AHSentinel PR1).

### GEMESSEN 14.11. 01:20 – Sniper-/Entzauber-Käufe (462 Käufe mit Ergebnis, Daten PC 14.11. 00:43)
Ergebnis je Kauf = zugeordneter Netto-Erlös (Beute zum Materialpreis beim Entzaubern bzw. Verkauf) gegen Kaufpreis.
- Gesamt: Einsatz 48,59 g -> Netto 65,09 g = +34,0 %. Sniper allein: 447 Käufe, 45,26 g Einsatz, +34,3 %.
- Je Kaufpreis / vorhergesagtem Wert (ev):  ≤ 0,6: +53 % (n 21) · 0,6–0,7: +43 % (n 154) · 0,7–0,8: +33 % (n 234) ·
  0,8–0,9: +18 % (n 42) · über 0,9: etwa 0 % oder Verlust (n 11).
- Folgerung (belegt, n 462, fast nur Entzaubern 26–40): Der Sniper-Höchstpreis von etwa 0,8 × Wert bringt rund +30 %;
  zwischen 0,8 und 0,9 × Wert bleibt der Gewinn unter 20 %. Das passt zu DE30b (20 % Mindestgewinn = höchstens Wert/1,2
  = 0,83 × Wert) – mit einer kleinen Lücke: im Bereich 0,8–0,9 wurden nur +18 % erreicht, die Vorhersage ist dort
  ca. 2 Punkte zu optimistisch. Über 0,9 × Wert nie kaufen.

### GEMESSEN 14.11. 01:15 – Verkaufs-KETTEN (2-Std.-Händler, Daten PC 14.11. 00:43, 81 Einstellungen, 32 Ketten)
Kette = alle Einstellungen eines Items bis zum Verkauf (Ablauf/Abbruch -> neu einstellen gehört dazu).
- 27 von 32 Ketten enden mit Verkauf (84 %); 5 noch offen bzw. aufgegeben.
- Einstellungen bis zum Verkauf: Median 1 (17 Ketten beim ersten Mal, 4 nach 2–3, 6 nach mehr als 3).
- Zeit bis zum Verkauf: Median 0,3 Std.
- Preis beim Verkauf / Preis der ersten Einstellung (Ketten > 1): Median 0,92 – wer neu einstellt, geht ca. 8 % herunter.
- Abbrüche (17): in 6 Fällen zeigt der eigene Scan ein günstigeres fremdes Angebot (unterboten), in 8 nicht, 3 unklar.
  Die Scans sind zu selten, um jedes Unterbieten zu sehen (der Nutzer sieht es direkt im AH-Fenster) -> Abbruch-Grund
  muss das Addon im Moment des Abbruchs festhalten (PR1).
Folgerung für den Spieler: Mit 2-Std.-Einstellungen verkauft sich die Ware fast immer (84 %), meist sofort; sonst nach
etwa 8 % Preissenkung. Die richtige Vorhersage ist "verkauft sich bis wann und zu welchem Preis", nicht "Chance je
einzelner Einstellung".

### GEMESSEN 14.11. 00:45 – Wellen und Zyklen (Prüf-Sitzung, Daten PC 5.–13.11., 336'172 Preispunkte, 6'771 Items)
Werkzeuge: addon-check/marktanalyse/. Gemessen = Mindestpreise aus den eigenen Scans (ohne unbestätigte/Sync-Punkte).

**1. Die Levelwelle – BELEGT (klar, in Folge).** Index je Stufenband (Tagesmedian der Staub/Essenz/Splitter-Preise,
1,00 = erster Tag mit Daten):

| Band | 05.11 | 06. | 07. | 08. | 09. | 10. | 11. | 12. | 13. |
|---|---|---|---|---|---|---|---|---|---|
| 05–20 | 1,00 | 0,60 | 0,83 | 0,67 | 0,63 | 0,61 | 0,62 | 0,64 | 0,72 |
| 21–30 | 1,00 | 0,16 | 0,12 | 0,13 | 0,11 | 0,14 | 0,12 | 0,12 | 0,14 |
| 31–40 | 1,00 | 1,05 | 0,51 | 0,23 | 0,21 | 0,20 | 0,20 | 0,18 | 0,20 |
| 41–50 | – | 1,00 | 0,83 | 0,59 | 0,36 | 0,28 | 0,31 | 0,37 | 0,31 |
| 51–60 | – | – | – | 1,00 | 0,95 | 0,61 | 0,38 | 0,33 | 0,33 |

-> Jedes Band bricht ein, sobald die Masse durchlevelt, und wandert ca. 1 Band je 1–2 Tage nach oben (21–30 am 6.,
31–40 am 7./8., 41–50 am 8.–10., 51–60 am 10.–12.). Danach bleibt das Band auf 12–35 % des Startpreises stehen.
Seit 11./12.11. sind ALLE Bänder durch und seitwärts (±10 %); leichte Erholung in 05–20 (+12 % seit 11.) und 41–50.
Vorsicht: Der erste Tag ist dünn (Startpreise mit wenigen Angeboten) – die Höhe des Einbruchs ist übertrieben,
die REIHENFOLGE und der ZEITPUNKT sind belegt.
Folgerung für die Vorausschau: Ein Band, dessen Index 2 Tage hintereinander > 15 % fällt, ist "in der Welle" – nicht
kaufen/halten, schnell verkaufen; ein Band, das 3 Tage seitwärts liegt, ist "durch". Nächste erwartete Welle (VERMUTET,
nicht belegt): Raid-Öffnung 9.12. (Verbrauchsgüter, Resistenz-Material) – mit M-Welle beobachten.

**2. Tageszyklus – HINWEIS, NOCH NICHT BELEGT.** Bereinigt um Trend (Abweichung vom gleitenden ±12-Std.-Median desselben
Items): Vormittag/Mittag 08–13 Uhr +1,5 bis +4,3 %, Abend 17–19 Uhr −2,0 bis −3,5 %, 22–23 Uhr −1,5 bis −2,3 %
(Spanne ~6–8 %). Bestätigung erste/zweite Hälfte: Korrelation +0,61, gleiche Richtung nur 10/16 Stunden -> zu schwach.
Ungereinigt (+4,6 % morgens, −4,7 % abends) war der Effekt durch den fallenden Markt aufgebläht. Plausibel: abends viele
Spieler online, mehr Angebote, tiefere Mindestpreise. Messfehler möglich: gescannt wird nur, wann der Nutzer spielt.
Brauchbar erst nach ≥ 3 Wochen und gleicher Richtung ≥ 80 %; die Spanne liegt nahe an der Gebühr (5 %).

**3. Wochenzyklus – NICHT BELEGT.** Je Wochentag nur 1–2 Kalendertage, alles überlagert vom Start-Einbruch
(Sa/So 7./8.11. +64/+29 % = Starttage). Frühestens nach 3–4 Wochen messbar. Monatszyklus: frühestens nach 2–3 Monaten.

## 9. Pflege dieser Datei

- Neue Messung oder Entscheid des Nutzers -> hier eintragen (mit Datum), Status belegt/vermutet.
- Abschnitt 3 nach jeder grösseren AHSentinel-Version mit dem Code abgleichen.
- Spiegel im claude.ai-Projekt "Addonprüfer": `claude/markt-strategie.md`.


## 9. Ideen-Pflicht der Prüf-Sitzung (Lehre vom 13.11., Kritik des Nutzers)

Der Nutzer musste Ideen wie "alle Goldflüsse erfassen", "Eigenbedarf" und "Gold pro Stunde" selbst liefern. Die
Prüf-Sitzung hat bisher nur geprüft, was verlangt war. Ab jetzt bei JEDER Prüfung, jedem Auftrag und jeder Antwort zu
einem Thema zuerst die Frage stellen: "Was würde ein erfahrener Händler / Buchhalter / Spieler hier zusätzlich
erwarten?" und dazu 1–3 eigene Vorschläge machen (kurz, mit Nutzen, ohne sie ungefragt zu beauftragen). Vergleich mit
bewährten Werkzeugen (TSM, Auctionator, Buchhaltungs-Kennzahlen) gehört dazu. Bewährte Kennzahlen für Handel:
Gewinn/Stunde, Rendite je eingesetztem Gold je Weg (Flip/Snipe/Entzaubern/Herstellen), Verkaufsquote je Item,
Haltedauer bis Verkauf, gebundenes Kapital (Lager + laufende Auktionen), verlorene Einzahlungen, Preis-Trefferquote.
Optik-Regel des Nutzers: Einzelheiten nie in überladene Tooltips, sondern in ein Detail-Fenster hinter einem Knopf.
Optik-Regel 2 (21:21): "solche Berechnungen will keiner sehen" – Anzeigen zeigen nur Ergebnisse, nie den Rechenweg
(keine Faktoren, keine "Mit X und Y kauft Z"-Sätze, keine Fallzahlen); Rechnungen nur im Testbericht/Details.

**Preis-Begriffe (geprüft 13.11.):** AHSentinel-Marktwert = gewichteter MEDIAN der letzten 14 Tage (A.MARKET_DAYS),
Ausreisser über dem Dreifachen und Lockangebote zählen nicht. TSM zum Vergleich: DBMarket = gewichteter
14-Tage-DURCHSCHNITT der Angebotspreise (letzte 3 Tage stärker gewichtet), DBMinBuyout = günstigstes Angebot des
letzten Datenstands, DBHistorical = 60-Tage-Durchschnitt von DBMarket, DBRecent = nur der letzte Stand. Der Median ist
gegen Ausreisser robuster als TSMs Durchschnitt. Anzeige (Entscheid des Nutzers): "Jetzt im AH" (ein echtes Angebot,
nie ein Durchschnitt, mit Alter) und "Median 14 Tage". Beide messen ANGEBOTS-, nicht Verkaufspreise.
Volatilität (Hinweis des Nutzers 13.11.): Forever-Preise sind sehr beweglich (Index 7 Tage −57 %); ein 14-Tage-Median
hinkt nach. Median nur als Vergleich anzeigen; Trend und Volatilität NUR im Hintergrund (keine Pfeile/Hinweise sichtbar, Entscheid 21:31); Entscheidungen nie allein
auf den Median stützen, sondern auf "Jetzt im AH" und erzielte Verkaufspreise.
Junge Wirtschaft (Hinweis des Nutzers 13.11.): Forever startete am 04.11.; in den ersten Wochen fallen die Preise
stetig (mehr Angebot, mehr Spieler mit Berufen). Lange Zeitfenster (14-Tage-Median) enthalten noch Startpreise und
liegen zu hoch -> in den ersten ~6 Wochen kurze, jüngere Tage stärker gewichtende Fenster (5 Tage); Wirkung messen.
Entscheid 21:32: Der angezeigte Median ist anpassend (Serveralter, Trend, Schwankung bestimmen Zeitraum und
Gewichtung), Beschriftung nur "Median"; Wirkung gegen den erzielten Verkaufspreis messen.


## 10. Lernstand 13.11. abends (Recherche auf Wunsch des Nutzers: "mach dich schlau … deutlich verbessern")

Quellen: TSM-Dokumentation (AuctionDB Market Value, Price/Value Sources), r/woweconomy Flipping-Leitfaden,
CogConnected "Gold in WoW Forever". Was daraus für uns folgt:

1. **Marktwert wie TSM (bewährt):** nur die günstigsten 30 % der Angebote; nach den ersten 15 % bricht ein Preissprung
   von ≥ 20 % die Liste ab (alles darüber zählt nicht = Schutz gegen Mondpreise); Ausreisser ausserhalb ±1,5
   Standardabweichungen weg; Tageswert = Mittel der Scans; über 14 Tage mit HALBWERTSZEIT ~2 Tage gewichtet.
   -> Unser "anpassender Median" (TP) sollte genau so gebaut werden: Gewichtung mit Halbwertszeit statt fester
   5/14-Tage-Fenster; in junger/volatiler Lage Halbwertszeit kürzer (z. B. 1 Tag), im ruhigen Markt ~2 Tage.
   Der 20-%-Sprung-Abbruch ist auch die bessere Lockangebot-/Mondpreis-Regel für "Jetzt im AH".
2. **Verkaufsquote (SaleRate) ist die wichtigste Kennzahl für Prognosen:** TSM misst je Item, wie oft ein eingestelltes
   Angebot wirklich verkauft (0,4 = 40 %), und dazu verkaufte Stück je Tag. Unsere Prognose sagte 98 % voraus, verkauft
   wurden 31 % -> Die eigene Verkaufsquote je Item (und je Item-Gruppe, solange wenig Daten) muss die Grundlage der
   Verkaufschance sein, nicht eine Schätzung. Items ohne/mit sehr tiefer Verkaufsquote nicht (oder nur wenig) einstellen.
3. **Flipping-Regeln der Praxis:** 5 % AH-Anteil immer abziehen; Kauflimit je Item (nie mehr kaufen, als man bei
   Preissturz verkraftet); KEIN "Reset" (Markt aufkaufen) kurz vor dem Ausloggen – wer offline ist, kann nicht
   reagieren (wichtig für den Nutzer: unter der Woche selten online); streuen statt alles auf ein Item; in kleinen
   Blöcken einstellen (das neueste Angebot verkauft zuerst, nachlegen ohne Abbrechen); nicht horten.
4. **Forever-Wirtschaft:** kein WoW-Token, keine GDKP-Raids -> weniger Gold-Nachfrage am oberen Ende; Preise allein aus
   Angebot/Nachfrage im Spiel; in den ersten Wochen schnelle Bewegungen, getrennte Fraktions-AHs eher volatil.
   Grösste Goldausgaben der Spieler: Training, Reittier (Stufe 40), Verbrauchsgüter, Taschen, Reparaturen,
   Raidvorbereitung -> Nachfrage nach Leveling-Gütern (Taschen, Tränke, Stoff/Leder für Berufe) ist verlässlicher als
   nach Luxus.
5. **Daraus neue Vorschläge (noch nicht beauftragt, dem Nutzer vorlegen):** (a) Marktwert nach TSM-Verfahren mit
   Halbwertszeit; (b) Verkaufsquote je Item als Basis der Verkaufschance + Warnung beim Einstellen von Ladenhütern;
   (c) Kauflimit je Item (Anteil am Kapital) im Sniper/Flip; (d) Hinweis vor dem Ausloggen, wenn grosse offene Flips
   im Markt liegen; (e) Einstellen in Blöcken als Standard beim Verkaufen grosser Mengen.

**Grundsatz 13.11. 21:33 (Nutzer): Angaben müssen stimmen und geprüft sein.** Jede Zahl, die ein Addon zeigt, wird von
der Prüf-Sitzung UNABHÄNGIG nachgerechnet (Auftrag ZN, addon-check/nachrechnung.py), nicht nur von den Tests des Addons.
Auch die Prüf-Sitzung selbst nennt dem Nutzer Zahlen nur nachgerechnet oder klar als "geschätzt"/"Messauftrag".

**Grundsatz 13.11. 22:06 (Nutzer): AHSentinel muss "pfeilschnell" sein – ein Instrument.** Leistungsziele (Tooltip ≤ 5 ms,
Reiter ≤ 50 ms, Sniper ≤ 2 s, Kauf sofort, kein Bild > 16 ms, Start ≤ 100 ms am Stück, Vollscan ≤ 10 MB) sind
Freigabe-Bedingung (Auftrag PS, Testteil "tempo"). Die Prüf-Sitzung trägt die Verantwortung, das bei jeder Version
selbst nachzuprüfen – nicht nur den Bericht des Projekts zu glauben.
