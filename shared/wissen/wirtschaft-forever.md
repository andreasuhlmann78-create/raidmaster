# Wirtschaft und Auktionshaus in WoW Forever – verbindliches Regelwerk

Gilt für ALLE GoldSentinel-Addons und Sitzungen (AHSentinel, ProfessionSentinel, GuildSentinel, LevelPilot …) und für
die Prüf-Sitzung. Wer Preise, Gebühren, Gewinne oder Werte berechnet oder beauftragt, liest diese Datei vorher.
Stand: 9. November 2026. Gepflegt von der Prüf-Sitzung. Änderungen nur mit Beleg (Abschnitt 0).

Anlass: Am 9.11. hat die Prüf-Sitzung zweimal eine falsche Gebührenregel und eine falsche Deutung der Verkaufs-Post
weitergegeben. Die Addons haben danach falsche Werte angezeigt. Das darf nicht wieder passieren.

---

## 0. Methode – zuerst messen, dann Regel

1. **Keine Regel aus einer einzelnen Beobachtung.** Eine Regel gilt erst als *belegt*, wenn mindestens **drei
   unabhängige Messungen** sie exakt bestätigen (auf den Kupfer genau) und **keine** ihr widerspricht.
2. **Gegenprobe:** Jede Regel muss eine Messung vorhersagen, die noch nicht gemacht wurde – und die Messung muss
   stimmen. Beispiel: Händlerwert-Regel sagt für Seltsamer Staub bei 24 Std. 1s voraus (Minimum) -> gemessen 1s.
3. **Zahlen müssen aufgehen.** Eine Deutung, bei der die Summe nicht exakt aufgeht, ist falsch – nicht "ungefähr
   richtig". Prüfen: Gesamt = Post-Gold + Auktionshausgebühr − Einzahlung; 5 % vom Gesamt = Gebühr (± 1c).
4. **Plausibilität am Markt:** Ein abgeleiteter Stückpreis muss zum Marktpreis des Items passen. 47c für Staub bei
   87c Markt ist ein Warnsignal für eine falsche Deutung, nicht ein billiger Verkauf.
5. **Aussagen des Spielers sind Beobachtungen, keine Formeln.** "Die Gebühr kommt nie zurück" ist eine Wahrnehmung;
   die Post (Rechnung) und Blizzards "Einzahlen" sind die Messung. Bei Widerspruch: messen und dem Spieler die
   Zahlen zeigen.
6. **Kennzeichnen:** In Anweisungen jede Regel als **belegt** (mit Messungen) oder **vermutet** (mit Messauftrag).
   Vermutetes nie als Rechengrundlage für Anzeigen verwenden, ohne "unsicher" anzuzeigen.
7. **Blizzard rechnen lassen, wo möglich:** Einzahlung über die Blizzard-API bzw. das Feld "Einzahlen"; eigene
   Formel nur als Rückfall und mit Testfall gegen gemessene Werte.

---

## 1. Auktionshaus-Mechanik in WoW Forever (Client 1.60.1, Fraktions-AH)

| Regel | Status | Beleg |
|---|---|---|
| Laufzeiten **2 / 8 / 24 Std.** | belegt | Einstellen-Fenster 9.11. 13:28 (Beta zeigte 12/24/48 – im Live-Spiel gemessen 2/8/24) |
| **Einzahlung** beim Einstellen = Händlerpreis (Verkaufspreis an Händler) × Menge × **5 % je 2 Std.** → 2 Std. 5 %, 8 Std. 20 %, 24 Std. 60 % | belegt | Leinenstoffballen (Händler 40c, 20 Stk.): 1s / 1s 60c / 4s 80c; Seltsamer Staub (Händler 1c, 20 Stk.): 1s / 1s / 1s; Schwarzmaulöl 18 Stk. 2 Std.: 1s |
| **Mindest-Einzahlung 1s je Auktion** (Stand 9.11.) | belegt | alle obigen Fälle unter 1s -> 1s; Wowhead 5.11.: "always incurs a deposit of at least 1 silver" |
| **Angekündigt: Mindest-Einzahlung wird auf 1c gesenkt** (Rückkehr zur Klassik-Formel) | **angekündigt für 17.11.2026 (US) bzw. 18.11.2026 (EU), mit der Wochenwartung; Stand 13.11. noch NICHT aktiv** | Blizzard-Hotfixes 10.11.2026: "minimum auction deposit is 1 copper (was 1 silver), with the realm restarts", danach verschoben – Kaivax 12.11. (Post #7, https://us.forums.blizzard.com/en/wow/t/wow-forever-hotfixes-november-11-2026/2403040/7): Auktionshaus-Änderungen aus dem Hotfix 10.11. herausgenommen, kommen mit der Wochenwartung 17.11. (EU laut Zweitquellen 18.11.). Laut Zweitquelle (timesaver.gg) gehören dazu auch: Auktions-Post nicht mehr für alle als "Stormwind Auction House" und eine Korrektur der Lieferzeit der Auktions-Post (2 bzw. 60 Min., Richtung in der Zweitquelle unklar) – **nur Zweitquelle, nach dem 17./18.11. messen** (Icy Veins "deposit cost change delayed"; foreverchanges.pro: "announced for November 17"; ForeverWisp, Wowhead Blue Tracker). **Gemessen 13.11. 06:42 (AHSentinel EINSTELLEN):** 8 Einstellungen, alle "abgezogen 100" (z. B. 36 Seelenstaub 2 Std., 8 Astralessenz 2 Std.) -> 1s gilt noch. AHSentinel misst das Minimum selbst (MINDESTEINZAHLUNG, db.minDeposit) – nach dem 17.11. nachmessen. |
| **Händlerpreise gesenkt (Hotfix 10.11.2026)** | belegt (Blizzard) | Eisengranate 1s25 (war 5s), Schwaches arkanes Elixier 5c (war 25c), einige hergestellte Rüstung (Leder, Schneiderei, Schmied) gesenkt – Quellen: Blizzard-Forum Kaivax 11.11. 03:27, ForeverWisp. Folge: Händler-Tabellen in Addons veralten -> Händlerpreis immer aus dem Client (GetItemInfo) bzw. gemessen (AHSentinel MA3); Befund 13.11. "Eisengranate 1s83 < Händler 5s" war genau das. |
| **Mehr Gold aus Quests ab ca. Stufe 48 (Hotfix 10.11.2026)** | belegt (Blizzard), Höhe nicht genannt | Kaivax, Hotfixes 10.11. (https://us.forums.blizzard.com/en/wow/t/wow-forever-hotfixes-november-11-2026/2403040/6): die meisten Quests ab Stufe 48 geben zusätzliches Gold. Folge: Gold-Quellen (Buchhaltung "Quest-Gold") steigen; Höhe nur messen, nicht schätzen. |
| Einzahlung hängt **nicht** vom AH-Preis ab | belegt | Staub 17s 80c vs. Ballen 11s: Staub billiger in der Einzahlung |
| **Beim Verkauf: 5 % vom Verkaufspreis ab** (Auktionshausgebühr, "consignment") | belegt | 3 Rechnungen: 202 = 5 % von 4042, 837 = 5 % von 16744, 313 = 5 % von 6279 |
| **Beim Verkauf: Einzahlung kommt zurück** (mit der Post) | belegt | Post-Gold = Gesamt − Gebühr + Einzahlung, 4× exakt |
| **Gebühr wird ABGERUNDET** (5 % auf ganze Kupfer nach unten) | belegt mit 1 unterscheidenden Fall, 3 verträglich | 6279 × 5 % = 313,95 -> 313 (gerundet wären 314); 4042 -> 202, 16744 -> 837, 8082 -> 404 |
| Höhe der zurückerstatteten Einzahlung bei Waren (Teilverkäufe, Minimum 1s) – **etwa anteilig nach verkaufter Menge** (gezahlte Einzahlung × verkauft / eingestellt, gerundet) | **vermutet / offen** | Protokoll 9./10.11. (Staub/Essenzen, gezahlt je 100c): 4 von 36 -> 11c, 25 von 25 -> 100c, 49 von 149 -> 33c; ungeklärt: 88 von 88 -> 97c, 149 -> 96c; früher 38c, 200c, 296c |
| Abgelaufene Auktion: Einzahlung verloren | bestätigt durch Quellen | Spielerberichte 6.11. (timesaver.gg), Hearthproof |
| **Abgebrochene Auktion: Einzahlung verloren** (nichts zurück) | **belegt** | AHSentinel-Protokoll 10.11. 07:12 "ABBRUCH Item 10938 · Menge 43 · Erstattung 0" (gezahlt 1s); dazu Hearthproof, Spielerberichte 6.11. |
| Neutrales AH (Beutebucht, Gadgetzan, Ewige Warte): 15 % Gebühr, höhere Einzahlung | vermutet (klassisch) | Wiki; in Forever nicht gemessen |
| **Ausrüstung (Einzelstücke): Preis nur in ganzen Silbern.** 199c -> "Interner Auktion-Fehler" (2×, AHSentinel); 200c -> erstellt (Blizzard-Fenster UND AHSentinel, gleicher Aufruf `PostItem(loc, dauer, 1, nil, 200)`). Waren (stapelbar) gehen mit Kupfer (83c, 84c, 97c). | **fast belegt** (Bestätigung: 1s 99c mit AHSentinel 0.65.63 -> Fehler im Protokoll). **Entscheid des Nutzers 10.11.: AHSentinel bleibt bei ganzen Silbern und "−1 Silber"; die Testroutine misst die genaue Regel (Sofortkauf/Gebot/über 1 Gold).** | Nutzer 9.11. 22:25, 10.11. 06:04–07:00, Protokoll BLIZZARD-POST/AHS-POST |

**Wichtig wegen der angekündigten Änderung:** Das Minimum NIE fest einbauen. Einzahlung immer zuerst über Blizzard
(API / "Einzahlen"), Formel nur als Rückfall; das Minimum aus Messungen erkennen (z. B. Einstellung, bei der die
Formel < 1s ergibt: abgezogen 1s oder weniger?) und im Protokoll melden. Sobald 1c gilt, fällt der Vorteil
"24 Std. kostet gleich viel" bei billigen Waren weg (dann kostet 24 Std. 12× so viel wie 2 Std., aber auf
Kupfer-Niveau).

**Folgerungen für die Rechnung**
- Kosten eines **erfolgreichen** Verkaufs = 5 % vom Verkaufspreis (die Einzahlung kommt zurück).
- Kosten eines **nicht** erfolgreichen Einstellens = die Einzahlung (verloren).
- Erwartete Kosten je Verkauf = 5 % × Preis + Einzahlung × (1 − p) / p, p = Verkaufschance je Einstellung.
- Bei Waren mit tiefem Händlerpreis (Staub, Stoff, Kräuter, Essenzen) kostet 24 Std. gleich viel wie 2 Std.
  (Minimum 1s) -> immer 24 Std.
- Die Mindest-Einzahlung 1s je Auktion trifft Einzelstücke hart: Stapel einstellen, wo möglich.

## 2. Die Verkaufs-Post (Rechnung) in Forever

`GetInboxInvoiceInfo` liefert laut Doku: invoiceType, itemName, playerName, bid, buyout, deposit, consignment,
moneyDelay, etaHour, etaMin, count, commerceAuction. **In Forever (1.60.1) belegt:** buyout enthält bei Warenverkäufen
die **Menge**, bid den **Gesamtpreis** (Rohzeile unten), `count` ist die Menge oder 0.

- Gesamt = Post-Gold (GetInboxHeaderInfo money) + consignment − deposit
- Menge = das "Preis"-Feld; Stückpreis = Gesamt / Menge
- Kontrolle: consignment ≈ 5 % von Gesamt (± 1c je Auktion), Stückpreis ≈ Marktpreis
- Belegt mit: 47 × 86c = 4042 · 184 × 91c = 16744 · 69 × 91c = 6279 (alle exakt)
- **RECHNUNG-ROH (1. Rohzeile, 9.11. 15:28, Schwarzmaulöl, 18 Stück zu 449c):** 4 (bid) = 8082 = **Gesamtpreis**,
  5 (buyout) = 18 = **Menge**, 6 = 100 Einzahlung, 7 = 404 Gebühr (5 %), 11 (count) = 18 = Menge, Post-Gold 7778 =
  8082 − 404 + 100. Also: bid = Gesamt, buyout = Menge, count = Menge oder 0. Gesamt aus bid ist auch dann bekannt,
  wenn das Gold schon aus der Post genommen ist (Post-Gold dann 0). Feldlage bid = Gesamt: 1 Rohbeleg, mit den 3
  abgeleiteten Fällen verträglich – weitere Rohzeilen sammeln.
- Rohwerte (RECHNUNG-ROH) im Diagnose-Protokoll behalten, bis die Feldlage für alle Fälle (Einzelstücke, Gebote,
  Käufe) belegt ist.

## 3. Welcher Preis gilt (Entscheide des Spielers)

- **Rechenwert = günstigstes Angebot aus dem letzten Scan** (bzw. der letzten Suche, wenn neuer). Kein Abzug, keine
  Deckelung auf den Median. Der Spieler scannt bewusst oft, damit die Preise aktuell sind.
- Schutz: offensichtlicher Ausreisser (z. B. 1 Stück zu 1c) -> nächstes Angebot. Item nicht im Scan -> Median.
- **Eigener Ø-Verkaufspreis = nur Statistik**, nie Rechenwert (Buchhaltung, Tooltip mit Shift).
- **Händlerpreis = Untergrenze** dessen, was ein Item sicher wert ist.
- Anzeigen sagen immer, woher ein Preis kommt ("Scan", "Markt"), wenn er von anderen Stellen abweichen kann.

- **Entzauber-Chancen grüner Rüstung (vermutet, nicht in Forever gemessen):** warcraft.wiki.gg (Classic, nach Itemstufe): 5–15 Staub 80 % / Essenz 20 %; 16–20 75/20/Splitter 5; 21–25 75/15/Splitter 10; 26–30 75/20/5. Ein Forever-Leitfaden (wow-professions.com/forever) nennt allgemein 75/20/3–5. **Entscheid des Nutzers 10.11. 09:25: gesammelte Entzauber-Ergebnisse (deStats/deLog) werden nie zurückgesetzt, umgerechnet oder migriert.** **Entscheid des Nutzers 10.11. 14:18: Startwerte bleiben trotz eigener Messung (142 Entzauberungen grün 26–30 Rüstung: 67,6/21,8/10,6 %) – die eigenen Ergebnisse wirken über das Lernen.** **Entscheid des Nutzers 10.11.: Forever-Leitfaden gilt als Startwert – Rüstung 75/20/5, Waffe 20/75/5 (bis Itemstufe 15: 80/20 ohne Splitter).** Belegen über die eigenen Entzauber-Ergebnisse (AHSentinel "echt aus N").
- **Absatz schätzen (vermutet):** "Verschwunden zwischen zwei Scans" ist in Forever KEIN Verkaufsmass – Auktionen laufen höchstens 24 Std., der ganze Bestand verschwindet täglich (Handschuhe 10.11.: 222 im AH, 294 "verschwunden"/Tag). Eigene Verkaufsquote (verkauft/eingestellt) zuerst; sonst Markt-Absatz deckeln (Annahme: <= 20 % des Bestands pro Tag).

## 4. Formeln

- **Netto beim Verkauf je Stück** = P − 0,05 × P − Einzahlungsrisiko je Stück (Abschnitt 1).
- **Herstellen:** Materialkosten je Zutat über den günstigsten Weg: AH (Scan), Händler, selbst herstellen aus einem
  bekannten Rezept (höchstens 2 Stufen). Wert des Ergebnisses = das Bessere aus Verkaufen (netto) und Entzaubern.
  Gewinn = Wert − Materialkosten.
- **Entzauberungswert** = Σ Chance × Ø-Menge × Netto-Preis des Materials (Stapelverkauf). Chancen: eigene Zählung,
  mit der Tabelle (Disenchantry, MIT) gewichtet, solange wenige eigene Daten.
- **Kaufen zum Entzaubern lohnt bis** = Entzauberungswert / (1 + Mindestgewinn %), auf Kupfer abwärts.
- **Kaufen zum Weiterverkaufen** lohnt, wenn Netto-Verkauf − Kaufpreis ≥ Mindestgewinn UND die Menge in etwa
  2 Tagen verkauft wird (Absatz).

## 5. Markt-Grundsätze (Wirtschaftswissen)

- **Liquidität vor Marge:** Ein hoher Gewinn auf dem Papier ist wertlos, wenn sich das Item nicht verkauft. Absatz
  pro Tag und eigene Verkaufsdauer immer mitbeachten.
- **Eigener Einfluss auf den Preis:** Grosse Mengen auf einmal einstellen drückt den Preis (Angebot > Nachfrage).
  Nur einstellen, was der Markt in vernünftiger Zeit aufnimmt.
- **Unterbieten** um 1c ist üblich; tiefer unterbieten verschenkt Geld, ausser der Markt ist überfüllt.
- **Opportunitätskosten:** Gold, das in Ware steckt, fehlt für bessere Geschäfte; Zeit (Herstellen, Entzaubern) hat
  auch einen Wert.
- **Schwankungen und Zeitpunkt:** Preise schwanken nach Tageszeit, Wochentag, Patch, Server-Alter. Darum: aktueller
  Scan statt alter Durchschnitt.
- **Konkurrenz:** Sehr billige Angebote (Schnäppchen) werden oft in Sekunden von anderen gekauft – "Treffer weg" ist
  normal, kein Fehler.
- **Sichere Untergrenze:** Händlerpreis. Nie im AH unter dem Händlerpreis verkaufen (abzüglich Kosten).
- **Kosten realistisch:** Jede Rechnung enthält alle Kosten (5 %, Einzahlungsrisiko, Händlerware, Zwischenprodukte),
  sonst ist der Gewinn zu hoch.

## 6. Fehler, die passiert sind (nicht wiederholen)

| Datum | Fehler | Richtig |
|---|---|---|
| 9.11. | Gebühr = max(5 % vom AH-Preis, 1s) beim Einstellen, nie erstattet – aus Spieler-Aussagen und einem Screenshot abgeleitet | Einzahlung nach Händlerpreis × Laufzeit, 5 % beim Verkauf, Einzahlung zurück (Abschnitt 1) |
| 9.11. | Laufzeit nicht berücksichtigt | 2 / 8 / 24 Std. mit 5 / 20 / 60 % |
| 9.11. | Rechnungsfeld "Preis" als Stückpreis gedeutet (47c Staub) – Plausibilität nicht geprüft | Feld = Menge (Abschnitt 2), Stückpreis gegen Markt prüfen |
| 9.11. | Negative Einnahmen als "doppelte Gebühr" erklärt und Reparatur beauftragt | Ursache war die Feldlage; erst Zahlen exakt aufgehen lassen, dann Ursache benennen |
| 9.11. | Eigener Ø-Verkaufspreis als Rechenwert | nur Statistik; Rechenwert = letzter Scan |

## 7. Pflicht-Checkliste vor jeder Anweisung mit Geld

- [ ] Steht die Regel in diesem Dokument als **belegt**? Wenn nein: Messauftrag statt Regel.
- [ ] Gehen alle Beispielzahlen in der Anweisung **exakt** auf?
- [ ] Passt jeder abgeleitete Stückpreis zum Markt?
- [ ] Sind alle Kosten drin (5 %, Einzahlungsrisiko, Händlerware)?
- [ ] Ist die Preisquelle der Letzte Scan (Abschnitt 3)?
- [ ] Gibt es Testfälle mit **gemessenen** Werten aus dem Spiel?
- [ ] Wird Neues, Unsicheres im Protokoll gemessen (ohne Spielernamen)?

## 8. Marktstrategien (womit Gold verdient wird)

Grundlage: bewährte Klassik-Strategien (Quellen unten) übertragen auf WoW Forever (Server seit 4.11.2026, die meisten
Spieler leveln noch). Jede Strategie mit der Frage: Was muss AHSentinel/ProfessionSentinel dafür können?

### 8.1 Die fünf Geldquellen
1. **Flippen (billig kaufen, teurer einstellen):** nur Items mit gutem Absatz (≥ 1/Tag) und klarer Preisspanne;
   Kaufschwelle z. B. ≤ 70 % des Medians, Verkaufsziel nahe Median; Menge ≤ Absatz von ~2 Tagen. Risiko: Preis fällt,
   Einzahlung verloren bei Ablauf. Addon: Schnäppchen/Sniper mit Kaufgrenze = Netto-Verkauf − Mindestgewinn.
2. **Herstellen mit Gewinn:** Materialien über den günstigsten Weg, Ergebnis verkaufen oder entzaubern (Abschnitt 4).
   Nur was sich verkauft. Addon: Gewinn-Fenster, "Beste Rezepte" nach echtem Gewinn.
3. **Entzauber-Handel:** grüne Rüstung/Waffen unter "Lohnt bis" kaufen, entzaubern, Materialien im Stapel verkaufen.
   Am stärksten, wenn viele Leveler grüne Teile billig einstellen (jetzt). Addon: Entzauber-Urteil, Sammelkauf,
   Entzauber-Fenster, Abrechnung Vorhersage gegen Wirklichkeit.
4. **Sammeln und Grundstoffe:** Kräuter, Erz, Stoff, Leder – sichere Nachfrage, weil Leveler Berufe hochziehen.
   Verkaufen in Stapeln, 24 Std. (Einzahlung meist Minimum).
5. **Seltenes und Dienste:** seltene Rezepte/Muster (wenige Hersteller), Verzauberungen als Dienst (nicht über AH
   verkaufbar – im Handelschannel anbieten; GuildSentinel/Gilde nutzen).

### 8.2 Zeitpunkt
- **Wochenzyklus:** Verbrauchsgüter (Tränke, Elixiere, Flasks, Schleifsteine, Buff-Essen) sind vor den Raid-Abenden
  am teuersten (Raid-ID-Reset in der Woche): unter der Woche günstig einkaufen/herstellen, vor Raid-Abenden mit langer
  Laufzeit einstellen.
- **Tageszeit:** abends viele Käufer, morgens wenig Angebot. Verkaufsdauer messen (AHSentinel F) und daraus lernen.
- **Phasen/Patches:** Vor neuen Inhalten steigen die Preise der dafür nötigen Waren (Spieler legen Vorräte an).
  Früh kaufen, zum Start verkaufen. Nach dem Start fallen sie.
- **Frischer Server (jetzt):** Leveling-Bedarf hoch (Taschen, Stoff, Leder, Erze, niedrige Tränke, grüne Ausrüstung),
  Preise schwanken stark und fallen mit der Zeit für niedrige Waren. Lieber schnell drehen als lagern.

### 8.3 Preisstrategie beim Verkaufen
- **Untergrenze (Minimum):** nie unter Netto-Händlerwert bzw. Herstellkosten + Mindestgewinn. Liegt die Konkurrenz
  darunter: nicht einstellen und warten (Markt erholt sich) statt Preiskampf.
- **Normalpreis:** ohne Konkurrenz am Median (oder etwas darüber), nicht ins Blaue.
- **Unterbieten um 1c**, nie tiefer (verhindert Preiskrieg und verschenkt nichts).
- **Höchstpreis:** Konkurrenz weit über Median -> zum Normalpreis einstellen, nicht hinterherziehen.
- **Ablaufgrenze:** Nach mehreren Abläufen ohne Verkauf nicht stur neu einstellen (Einzahlung wird verbrannt) –
  billiger einstellen, liegen lassen oder an den Händler.
- **Neu einstellen höher:** Ist die billige Konkurrenz weg, Auktion abbrechen und höher einstellen nur, wenn der
  Mehrerlös die verlorene Einzahlung deutlich übersteigt.
- **Menge pro Auktion:** Waren im Stapel (Minimum 1s verteilt sich), nicht den ganzen Bestand auf einmal (drückt den
  Preis und bindet Gold).
- **Teures direkt verkaufen:** Bei sehr teuren Items spart Handel im Chat die 5 % – aber Risiko und Aufwand.

### 8.4 Einkaufsstrategie
- Kaufgrenze immer aus dem **Netto-Verkaufswert** (nach 5 % und Einzahlungsrisiko) minus Mindestgewinn rechnen,
  nie aus dem Bruttopreis.
- Menge begrenzen auf das, was in ~2 Tagen verkauft wird.
- Preisverlauf/Trend prüfen: fallender Trend -> weniger kaufen.
- Konkurrenz bei Schnäppchen ist hoch -> schnell sein (Sniper), aber nie über die Grenze.

### 8.5 Risiko und Kapital
- **Streuen:** nicht das ganze Gold in ein Item.
- **Gold bindet:** Lagerbestand kostet Gelegenheiten. Kapital im Umlauf halten.
- **Erfolg messen:** Buchhaltung je Geschäftsart (Flip, Herstellen, Entzaubern) mit Rendite % – was nicht verdient,
  wird gestoppt. Vorhersage gegen Wirklichkeit prüfen und die Rechnung nachschärfen.
- **Ehrlich rechnen:** Gewinn = Erlös − alle Kosten (Abschnitt 1 und 4), Zeit nicht vergessen.

### 8.6 Was die Addons daraus können sollen (Ausbau, nach und nach)
- AHSentinel: Kaufgrenzen netto; Ablaufgrenze und Untergrenze beim Einstellen; "Neu einstellen höher" nur mit
  Einzahlungsrechnung; Verbrauchsgüter-Hinweis vor Raid-Abenden; Rendite je Geschäftsart in der Buchhaltung.
- ProfessionSentinel: Herstellen nach echtem Gewinn (Werte aus AHSentinel, letzter Scan), Hinweis auf gefragte
  Leveling-Waren.
- Alles mit Belegen nach Abschnitt 0 – keine Strategie-Regel ohne Messung im Spiel.

## 9. Der Forever-Markt (aus Quellen, mit Datum)

- **Start 4.11.2026**, Client 1.60.1 (Build 70862). Onyxia, Hyjal-Gipfel und Barrow Deeps öffnen am **9.12.2026**
  (Hearthproof) -> Vorräte für Raid-Verbrauchsgüter vorher anlegen.
- **Ein Markt je Regelwerk und Region** (Normal / PvP / RP / RP-PvP), realmlos; jede Fraktion hat ihr AH, dazu
  neutrale AHs (Gadgetzan, Beutebucht, Ewige Warte) mit höherem Anteil (Blizzard-Q&A, AH Ledger).
- **Waren (stapelbar) werden je Stück gehandelt**: Käufer gibt eine Menge ein und bekommt die billigsten Stücke zuerst,
  auch von mehreren Verkäufern (wie Retail). Ausrüstung: ein Stück je Angebot.
- **Suchgrenze: 100 Suchen pro Minute** (Beta) -> Scans und Sniper müssen darunter bleiben.
- **Vollscan höchstens alle 15 Minuten** (Angabe auxForever auf CurseForge, Stand 19.10.2026; vermutlich die
  Blizzard-Grenze für den Gesamtscan) – vermutet, im Spiel bestätigen.
- **Andere AH-Addons für Forever auf CurseForge (Stand 9.11.2026):** Auctionator (Forever-Variante, 12.1.5 vom
  13.10.), Auctioneer (Forever) 4.0.x von crediar (mit Enchantrix für Entzauberwerte), auxForever 0.7.1.1 (Beta, mit
  dokumentierter Schnittstelle AuxForeverAPI: GetLatestPrice, GetUsualPrice), AHledger 0.9.6 (Preise aus Datei bzw.
  ahledger.com, keine Schnittstelle). TradeSkillMaster: keine Forever-Version.
- **Kaufen, Bieten, Einstellen, Abbrechen sind für Addons geschützt** (nur mit Klick/Taste) – deckt sich mit dem
  Sniper-Befund (zwei Rasten).
- **AH-Störungen** in der ersten Woche ("The item was not found" bei Sofortkäufen, 6./7.11.) – Fehlkäufe können am
  Server liegen, nicht am Addon.
- **Preise Startwoche (Medianwerte US/EU, 7.11., timesaver.gg/AH Ledger):** Leinenstoff ~29c, Wollstoff ~1s 30–61c,
  Seidenstoff ~3s 40–90c, Magiestoff ~10–13s (Startwoche 32s, −64 %), Kupfererz ~71–86c, Eisenerz ~6–9s (−48 %),
  Seltsamer Staub ~97c, Geringe Magieessenz ~1s 42–58c, Grosse Magieessenz ~3s 35–78c,
  Visionenstaub ~14–24s (Startwoche 57s, −67 %).
- **Beobachtetes Muster (wichtig für Strategie):** Waren für Stufe 1–20 blieben stabil; Waren der Stufen 30–45 fielen
  in wenigen Tagen um 50–67 %, sobald mehr Spieler dort ankamen (Knappheitsprämie verschwindet). Kupfer und
  Friedensblume stiegen (+38–55 %). Kleinere Regelwerke (RP, RP-PvP) haben 1,6–1,9× höhere Preise (weniger Verkäufer).

## 10. Gelernte Strategien für Forever (aus den Abschnitten 8 und 9)

1. **Knappheit früh verkaufen, nicht lagern:** Waren einer Stufe, die gerade erst erreicht wird, sind am Anfang teuer
   und fallen rasch. Eigene Funde der nächsten Stufe sofort verkaufen; für Eigenbedarf später kaufen.
2. **Billige Grundwaren (Kupfer, Leinen, Kräuter Stufe 1–20) sind stabil und dauernd gefragt** (Berufe-Leveling,
   immer neue Charaktere) -> sicheres Volumen, kleine Marge, Stapel, 24 Std.
3. **Entzauber-Handel jetzt besonders gut:** viele Leveler verkaufen grüne Teile; Staub/Essenzen halten den Preis
   (Staub −3 %), während die Ausrüstung billig ist.
4. **Vor dem 9.12. (Onyxia/Hyjal/Barrow Deeps):** Raid-Verbrauchsgüter und ihre Kräuter rechtzeitig günstig kaufen
   bzw. herstellen, zum Start verkaufen.
5. **Nach dem 1c-Minimum-Patch:** Einzelstücke und kleine Mengen werden billiger einzustellen; Stapel-Vorteil und
   "24 Std. gratis" fallen weg -> Laufzeit wieder nach Verkaufsdauer wählen.
6. **Konkurrenz und Server-Störungen einrechnen:** Sniper-Treffer verschwinden oft; nie mehr als das Budget, Käufe
   erst nach Server-Bestätigung zählen.
7. **Messen statt glauben:** jede Strategie in der Buchhaltung je Geschäftsart mit Rendite prüfen.

## Quellen

- Messungen im Spiel (Screenshots und Diagnose-Protokolle 9.11.2026, testberichte/diagnose/AHSentinel)
- WoWWiki-Archiv, Formulas:Auction House: https://wowwiki-archive.fandom.com/wiki/Formulas:Auction_House
- Vanilla-WoW-Archiv, Auction House: https://vanilla-wow-archive.fandom.com/wiki/Auction_House
- WoWWiki, Auction House: https://wowwiki.fandom.com/el/wiki/Auction_House
- warcraft.wiki.gg, API GetInboxInvoiceInfo: https://warcraft.wiki.gg/wiki/API_GetInboxInvoiceInfo
- Blizzard-Support, Auktionshausgebühr: https://eu.battle.net/support/en/article/180541
- Icy Veins, WoW Classic Goldmaking Guide: https://www.icy-veins.com/wow-classic/goldmaking-guide-the-best-ways-to-make-gold
- Warcraft Tavern, Gold and Trading Guide: https://www.warcrafttavern.com/wow-classic/guides/gold-and-trading-guide/
- Seramate (nach Wowhead), Minimum Deposit 1 Copper, 6.11.2026: https://seramate.com/news/forever/2026/11/06/forever-ah-minimum-deposit-copper-11353d96
- Blizzard-Forum, "AH deposit fix when?": https://us.forums.blizzard.com/en/wow/t/ah-deposit-fix-when/2405657
- timesaver.gg, WoW Forever AH Prices Week 1 (7.11.2026): https://timesaver.gg/blog/wow-forever-auction-house-prices-week-1
- Hearthproof, WoW Forever Auction House: https://hearthproof.com/economy/auction-house/
- AH Ledger, WoW Forever: https://ahledger.com/wow-forever
- TradeSkillMaster, Auctioning Operations: https://support.tradeskillmaster.com/tsm-addon-documentation/1072146-tsm-addon-auctioning-operations

## Entscheid des Nutzers 10.11.2026 15:54: Gerechnet wird mit dem aktuellen Markt

Kaufen: echter Preis jetzt. Verkaufswert: aus der aktuellen Preisleiter und dem Absatz (wo komme ich in der Laufzeit dran).
Der Durchschnitt (Marktwert) wird nicht mehr für Werte gerechnet, nur als Hinweis "frisch gestiegen" (> 150 %, < 24 Std.)
bzw. "eingebrochen" (< 60 %). Auftrag: auftraege/AHSentinel/anweisung-aktueller-markt-entscheid.txt.

## Entscheid des Nutzers 10.11.2026 15:59: Markt rechnet mit höchstens 25 % des Goldes

Alle Kaufvorschläge im Markt zusammen höchstens 25 % des aktuellen Golds (Option, nie über 50 %).
Auftrag: auftraege/AHSentinel/anweisung-markt-kapital-25.txt.

## Entscheid des Nutzers 13.11.2026 23:45: Mindestgewinn Entzaubern JE GRUPPE (ersetzt die feste 30-%-Regel)

20 % für belegte Gruppen (≥ 30 eigene Entzauberungen mit Kauf, Gewinn gesamt ≥ 20 %, Summe/Summe), sonst 30 %.
Grund: Die Begründung der 30 % (42 % / 55 %) war ein Median-Fehler (KF2); echt +35 % (26–30) und +20 % (36–40).
Auftrag DE30b.

## (überholt 23:45) Entscheid des Nutzers 13.11.2026 22:57: Entzauber-Käufe mit mindestens 30 % Gewinn (ersetzt 20 %)

Grund (gemessen, Testbericht 0.65.118 vom 13.11. 22:54): Sniper-Entzauber-Käufe 447, nur 42 % mit Gewinn; 55 % (512)
mit Beute unter dem Kaufpreis; Beute/Vorhersage 2:4:a 0.60. Gilt überall gleich (Sniper, Markt "Entzaubern",
Tooltip-Gewinn-Zeile, Heute tun): Weg Entzaubern nur, wenn Gewinn nach 5 % Gebühr ≥ 30 % des Kaufpreises.
Auftrag: offen-ahsentinel.txt Punkt DE30 (SEHR DRINGEND).

## Entscheid des Nutzers 10.11.2026 16:15: Entzauber-Käufe mit mindestens 20 % Gewinn (ÜBERHOLT 13.11.: 30 %)

Die Markt-Ansicht "Entzaubern" schlägt nur Teile mit mindestens 20 % Gewinn nach Gebühren vor (zum aktuellen Markt).
Auftrag: auftraege/AHSentinel/anweisung-markt-entzaubern.txt.

## Beobachtung des Nutzers 10.11.2026 16:44: Zauberstäbe nicht entzauberbar (Forever)

Zauberstäbe lassen sich in WoW Forever nicht entzaubern (vom Nutzer beobachtet, Beleg über Protokoll DE-NICHT-MOEGLICH).

