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
</content>
</invoke>

---

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
8. **Verlustgrenze:** Fällt der Markt eines gekauften Items deutlich, nüchtern rechnen: jetzt billiger verkaufen vs.
   warten (Zeit × Risiko × Einzahlungen). Kein "es kommt schon zurück".

## 9. Pflege dieser Datei

- Neue Messung oder Entscheid des Nutzers -> hier eintragen (mit Datum), Status belegt/vermutet.
- Abschnitt 3 nach jeder grösseren AHSentinel-Version mit dem Code abgleichen.
- Spiegel im claude.ai-Projekt "Addonprüfer": `claude/markt-strategie.md`.
