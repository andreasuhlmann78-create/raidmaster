# Buchhaltung für Auktionshaus-Handel (WoW Forever) – Wissen der Prüf-Sitzung

Stand: 10. November 2026 · Anlass: Der Nutzer macht nach eigenem Empfinden "viel Plus", die AHSentinel-Buchhaltung
zeigt aber "Kasse −6g 32s / Ergebnis mit Lager −2g 43s" (0.65.86, 10.11. 18:32). Auftrag des Nutzers: "mach dich über
Buchhaltung schlau und finde heraus, wie man das löst – im Gedächtnis speichern".

Wer an der Buchhaltung eines GoldSentinel-Addons arbeitet, prüft oder Aufträge dazu schreibt, liest diese Datei und
`wirtschaft-forever.md` (Abschnitt 0: Zahlen müssen exakt aufgehen).

---

## 1. Grundbegriffe (allgemeine Buchhaltung, übertragen)

| Begriff | Bedeutung | Im AH |
|---|---|---|
| **Kasse (Cash-Sicht)** | Geld rein − Geld raus im Zeitraum | Verkäufe − Käufe − Gebühren. Ein Tag mit grossem Einkauf ist immer "im Minus", auch wenn er sehr gewinnbringend ist. Taugt NICHT als Gewinn. |
| **Kostenbasis (Einstandspreis)** | Was eine Einheit im Lager gekostet hat | Jedes gekaufte Stück trägt seinen Kaufpreis; beim Verkauf wird genau dieser abgezogen. |
| **Gleitender Durchschnitt / FIFO** | Wie die Kostenbasis bei mehreren Käufen bestimmt wird | Durchschnitt: einfach und robust (TSM zeigt Ø-Kauf- und Ø-Verkaufspreis je Item). FIFO: genauer, aber aufwendiger. Für uns: gleitender Durchschnitt je Item und Charakter. |
| **Realisierter Gewinn** | Erlös verkaufter Ware − deren Kostenbasis − Gebühren | DAS ist "mein Gewinn". Nur verkaufte Ware zählt. |
| **Unrealisierter Gewinn** | (Marktwert − Kostenbasis) der Ware, die noch im Lager/AH liegt | Nur Zusatzinfo, schwankt mit dem Markt, kann bei Aufkäufen/Preissprüngen täuschen. |
| **Lager zum Einstandspreis** | Unverkaufte Ware bleibt mit ihren Kosten im Lager | Einkauf ist dann ergebnisneutral (Gold wird zu Ware). Kein künstliches Minus am Einkaufstag, kein künstliches Plus bei Preisspitzen. |
| **Kuppelprodukte (joint products)** | Ein Einsatz ergibt mehrere Produkte | Entzaubern: 1 Teil -> Staub + Essenz + Splitter. Die Kosten des Teils werden nach dem **relativen Verkaufswert** zum Zeitpunkt des Entzauberns auf die Materialien verteilt (Standardmethode "relative sales value"). |
| **Abstimmung (Reconciliation)** | Buchhaltung gegen echtes Geld prüfen | Gold jetzt − Gold zu Beginn (alle Charaktere) muss = Kasse + Sonstiges (Quests, Händler, Reparatur, Post) sein. Die Differenz zeigt fehlende Buchungen. |

## 2. Wie es Andere machen (TradeSkillMaster)

- TSM bucht Käufe und Verkäufe beim **Abholen der Post** (Rechnungen). Fehlende Daten entstehen, wenn Post nicht
  abgeholt wird oder ein anderes Addon das Postfach übernimmt; Varianten nur über den Namen erkennbar.
  Quelle: TSM "Why am I missing sales or purchase data" und "TSM Addon: Ledger".
- TSM rechnet Gewinn **je Item** aus Kauf- und Verkaufsdatensätzen (Ø Kauf, Ø Verkauf, Gewinn, Gewinn %), Zeiträume
  7/30 Tage/alles. Lagerwert nach wählbarer Preisquelle, Mengen je Ort (Taschen, Bank, Post, andere Charaktere, AH).
- Lehre: Gewinn kommt aus der **Zuordnung Kauf -> Verkauf**, nicht aus Kasse pro Tag.

## 3. Besonderheiten AH (Classic-Mechanik, in Forever zu messen)

- **Verzögerung beim Verkaufserlös:** Seit Patch 2.2 kommt bei einem Verkauf zuerst eine Post "Verkauf ausstehend",
  das Geld eine Stunde später (Engadget 2007, Blizzard: Prüfung der Transaktionen). Ob Forever das auch so macht:
  **vermutet, nicht belegt** -> messen (Zeit zwischen "Es wurde ein Käufer für Eure Auktion gefunden" und Rechnung mit
  Geld).
- **Folge der Asymmetrie:** Käufe werden in AHSentinel sofort gebucht (Kauf-Ereignis), Verkäufe erst, wenn die Rechnung
  im Postfach gelesen wird. Ein verkaufter Stapel ist sofort aus "meine Auktionen" verschwunden, das Geld aber noch nicht
  gebucht -> er fehlt im Lager UND in der Kasse -> scheinbarer Verlust, bis die Post geöffnet und das Geld da ist.
- Ein Verkauf ist schon beim Chat-/Systemhinweis "Es wurde ein Käufer für Eure Auktion gefunden: X" sicher; der Preis
  ist aus der eigenen Auktionsliste bekannt. Richtig: sofort als **"ausstehend"** buchen (Erlös = Sofortkauf × Menge −
  5 %), bei der Rechnung bestätigen (nicht doppelt).

## 4. Diagnose AHSentinel 0.65.86 (Code-Prüfung 10.11., Ledger.lua)

1. **Kasse = Verkäufe − Käufe − Gebühren** (Le:Summary) -> reine Cash-Sicht. Entzauber-Handel kauft viel auf einmal
   und verkauft über Stunden -> Kasse am Einkaufstag stark negativ. Erwartet, kein Fehler, aber als "Ergebnis" irreführend.
2. **Ergebnis mit Lager = Kasse + Lager jetzt − Lager zu Beginn** (Le:StockChange) -> bewertet das Lager zum
   heutigen Verkaufswert, nicht zum Einstandspreis. Damit hängt das Ergebnis am Markt (Aufkauf, Preissturz).
3. **Verkäufe erst ab Rechnung, Käufe sofort** (Abschnitt 3) -> Lücke für alles, was seit dem letzten Öffnen der Post
   (und in der Verzögerung) verkauft wurde. Bei schnellen Materialien (Median 0,1 Std.) laufend viele Stapel.
4. **Lager zu Beginn umfasst alle Charaktere** (for char in pairs(first)), "jetzt" nur für den aktuellen exakt ->
   Beiträge anderer Charaktere aus gespeicherten Ständen; erklärt vermutlich die 65s 68c, die in der Anzeige nicht
   aufgehen (vermutet).
5. Entzaubern: Kauf des Teils ist eine Ausgabe, die Materialien kommen ohne Kostenbasis ins Lager -> Gewinn je Material
   nicht messbar; Le:DisenchantCharges rechnet je Einkauf, aber nicht in die Tageszahl.

## 5. Lösung (Empfehlung der Prüf-Sitzung)

1. **Haupt-Zahl = realisierter Gewinn** im Zeitraum: Σ (Erlös nach 5 % − Kostenbasis der verkauften Stücke) −
   Einstellgebühren (abzüglich Erstattungen). Einkauf ist ergebnisneutral. Ein Endergebnis, Rechnung im Tooltip.
2. **Kostenbasis je Item und Charakter** (gleitender Durchschnitt): Kauf erhöht Menge und Kosten; Verkauf entnimmt zum
   Durchschnitt; Händlerverkauf ebenso. Unbekannte Herkunft (alter Bestand, Farm, Beute): Kostenbasis 0, im Tooltip
   als "ohne Einkauf" ausgewiesen.
3. **Entzaubern als Umbuchung:** Kostenbasis des Teils -> auf die erhaltenen Materialien nach relativem Verkaufswert im
   Moment des Entzauberns. Herstellen analog (Zutaten -> Produkt).
4. **Verkauf sofort als "ausstehend"** beim Hinweis "Käufer gefunden", mit Rechnung abgleichen (auctionID/Item+Menge+
   Preis), nie doppelt.
5. **Abstimmung mit dem Gold:** Gold aller Charaktere zu Beginn/jetzt mitschreiben; Differenz zur Buchhaltung im
   Tooltip ("nicht gebucht: X" – Quests, Händler, Reparatur, Post). So sieht der Spieler sofort, ob die Zahl stimmt.
6. **Unrealisierter Gewinn** (Ware im Lager/AH zum aktuellen Wert − Kostenbasis) nur im Tooltip, mit Aufkauf-Schutz (D6).
7. Messauftrag B1: Verzögerung Verkauf -> Geld in Forever messen (Abschnitt 3).

## 5b. Plausibilitäts-Prüfung (Pflicht für jede Prüfung einer Gewinn-Anzeige)

Entscheid des Nutzers 11.11.: Zahlen nicht nur nachrechnen, sondern prüfen, ob sie überhaupt stimmen KÖNNEN.
Lehre vom 11.11. 22:15: "Heute 8g57, Rendite 253 %" ging auf den Kupfer auf – war aber falsch, weil der Neustart der
Buchhaltung die Kostenbasis des Bestands verloren hatte (43 von 57 Entzauberungen mit Kosten 0 = genau die 6g77
"nicht gebucht").

1. **Rendite gegen die Strategie:** Entzaubern kauft bis zur Grenze (Wert − 20 %). Kostenbasis der Materialien muss
   dann grob 70–90 % des Verkaufserlöses sein, Rendite um 10–40 %. Über 100 % an einem Tag = Kostenbasis prüfen.
2. **"Ohne Einkauf" gegen die Herkunft:** Material aus Entzaubern hat fast immer eine Kostenbasis. Hoher Anteil
   "ohne Einkauf" = Kosten verloren (Neustart, Zusammenführen, Kauf nicht erkannt).
3. **Gold-Abstimmung:** Gold-Veränderung + ausstehende Post muss ≈ Kasse sein, im GLEICHEN Zeitraum. Ein grosses
   "nicht gebucht" ist ein Fehlerhinweis, kein Rundungsrest – Betrag mit Einzelposten vergleichen (hier exakt 6g77).
4. **Je Item:** Kostenbasis pro Stück gegen den Kaufpreis der Teile und den Materialanteil vergleichen.
5. **Ergebnis an den Nutzer** erst nach 1–4; sonst ausdrücklich "rechnerisch ok, Plausibilität offen".
6. **Neustart der Buchhaltung = Eröffnungsbilanz:** Bestand behält seine Einstandspreise, nur die Gewinn-Zähler
   beginnen bei 0.

## 5c. Jeder Goldfluss wird erfasst (Lehre vom 13.11., Hinweis des Nutzers)

Eine Buchhaltung stimmt nur, wenn JEDER Gold-Abgang und -Zugang eine Buchung hat – sonst bleibt eine Lücke, die als
"Verlust", "ohne Einkauf" (37 % des Erlöses, BH1307) oder falscher Lagerwert sichtbar wird. Die Prüf-Sitzung hat das
bisher nur für das AH gedacht; der Nutzer musste darauf hinweisen. Ab jetzt bei JEDER Prüfung/Auftrag zur Buchhaltung
diese Liste durchgehen (Checkliste, auch in der Pflicht-Checkliste wirtschaft-forever.md Abschnitt 7 anwenden):

| Goldfluss | Ereignis im Spiel | Buchung |
|---|---|---|
| AH-Kauf / -Verkauf, Einzahlung, Gebühr | AH-Ereignisse, Rechnungs-Post | Einkauf / Erlös / Kosten |
| Händler-Kauf (Taschen, Reagenzien, Munition) | MERCHANT_*, Gold-Abgang + Item | Einkauf (meist Eigenbedarf) |
| Händler-Verkauf (Grau, Müll, Handelsware) | MERCHANT_*, Gold-Zugang | Erlös (mit Einstand, falls gekauft) |
| Handel mit Spielern (Handelsfenster) | TRADE_* Gold/Items beider Seiten | Einkauf oder Erlös |
| Nachnahme-Post (COD), Gold per Post | MAIL_* | Einkauf / Zugang / Überweisung an Twink |
| Reparatur, Training, Flug, Stall, Bank-Fach | Gold-Abgang ohne Item | Spielkosten (nicht Handel) |
| Questbelohnung, Beute, Gold von Mobs | Gold-Zugang ohne Kauf | Einnahme (nicht Handel) |
| Gildenbank ein/aus | GUILDBANK_* | Überweisung |

Grundsätze: (1) Jede Buchung trägt die HERKUNFT (AH/Händler/Spieler/Post/Quest …). (2) Was die eigenen Figuren
anlegen, als Tasche einsetzen, verbrauchen oder an Twinks schicken = EIGENBEDARF (nicht Handelsgewinn). (3) Am Tagesende
muss "Gold vorher + Zugänge − Abgänge = Gold nachher" aufgehen; der Rest steht sichtbar als "nicht zugeordnet".
(4) Beim Prüfen einer Gewinn-Anzeige immer fragen: Welcher Goldfluss fehlt noch?

## 5d. AH-Gebühren aus Sicht eines Buchhalters (Nutzer 13.11. 22:47: "sieh es aus der Sicht eines Buchhalters")

Begriffe: im Addon immer das Wort des Spiels (Anzahlung = Blizzard-Zeichenkette DEPOSIT), nie selbst erfundene Wörter.

| Vorgang | Was ein Buchhalter daraus macht | Gewinn? |
|---|---|---|
| Einstellen: **Anzahlung** wird bezahlt | Gold ist nicht weg, sondern **hinterlegt** (Guthaben beim AH, "gebundenes Gold"). Kein Aufwand. | nein |
| Verkauf: Anzahlung kommt mit der Rechnung zurück | Guthaben aufgelöst. Kein Ertrag. | nein |
| Verkauf: **Auktionsgebühr** (5 % im Fraktions-AH) | Verkaufsprovision, mindert den Erlös. Aufwand im Zeitraum des Verkaufs. | ja, Aufwand |
| Ablauf oder Abbruch: Anzahlung **verfällt** | Erst JETZT Aufwand ("verfallene Anzahlung"), im Zeitraum des Ablaufs, dem Item zugeordnet. | ja, Aufwand |

Folgen: (1) Laufende Auktionen dürfen den Gewinn NICHT drücken; ihre Anzahlungen gehören zum gebundenen Gold
(neben dem Lagerwert). (2) Eine Erstattung darf nicht als "negative Gebühr" in einem anderen Zeitraum landen
(sonst ist der eine Tag zu schlecht, der andere zu gut). (3) Verfallene Anzahlungen je Item zeigen, wo man zu teuer
oder zu lange einstellt – im Details-Fenster als "Anzahlung verfallen" (mit Client-Wort).
(4) Abstimmung: Gold vorher + Zugänge − Abgänge = Gold nachher gilt weiter; die hinterlegten Anzahlungen erscheinen
dabei als eigener Posten "hinterlegt", nicht als Verlust.
Befund am Code 0.65.118 (Ledger.lua Le:Add -> Books.lua BK:OnFee, Summe Z. 410–417): Anzahlung wird beim Einstellen
sofort als Gebühr gebucht und beim Verkauf mit einer negativen Gebühr ausgeglichen -> verletzt (1) und (2). Auftrag BH-ANZ.
Offen (messen): Gibt Forever beim Abbrechen die Anzahlung zurück? (Ledger kennt "refund" beim Abbrechen, L2; in Classic
verfällt sie.)

## 5e. Nachrechnung 14.11. (Prüf-Sitzung, Daten PC 13.11. 23:41) – Befund BH-AUS

Bücher (books.log) und Kassenbuch (ledger) widersprechen sich: Bücher = Kassenbuch + alle 53 "ausstehenden" Verkäufe
(340 Stück, 11.11.–13.11., keine mit Rechnung). Gezeigter Gewinn 43 g 49 s, ohne die ausstehenden ≈ 20 g 53 s. Die
Warnung "ohne Einkauf" kommt grösstenteils davon. books.gold und books.cb leer -> Gold-Abstimmung läuft nicht.
Nachtrag 14.11. 01:05 (Daten 00:43): bestätigte Verkäufe = Kassenbuch exakt; aber ihr Einstand fehlt (63 % ohne Einkauf),
weil die ausstehenden Doppel ihn schon verbraucht haben. Eine Reparatur darf den Einstand NICHT ins Lager zurücklegen
(Phantom-Ware, Gewinn zu hoch), sondern muss ihn auf die Rechnung umbuchen (BH-AUS-2).
Nachtrag 14.11. 01:10: Nach 0.65.125 Gewinn 24g01 statt 20g53 – Rest-Einstand 34'802c lag als Phantom-Ware im Lager
(19 × 11082, 36 × 11083; der Nutzer hat sie nicht). REGEL: Jede Reparatur und jede Prüfung gleicht das Lager mit dem
wirklichen Bestand (Taschen/Bank/AH/Post) ab; Lager > Bestand = Befund.
REGEL: Ausstehend ist kein Erlös. Gewinn nur aus bestätigten Verkäufen; jede Buchhaltungs-Prüfung gleicht Bücher und
Kassenbuch je Item ab (Stück und Erlös) – Unterschied = Befund.

## 6. Quellen

- [TSM: Why am I missing sales or purchase data on my items?](https://support.tradeskillmaster.com/en_US/addon/why-am-i-missing-sales-or-purchase-data-on-my-items)
- [TSM Addon: Ledger](https://support.tradeskillmaster.com/tsm-addon-documentation/tsm-addon-ledger)
- [Engadget: A one-hour delay on AH winnings in 2.2](https://www.engadget.com/2007/09/25/a-one-hour-delay-on-ah-winnings-in-2-2/)
- [Joint and by-product costing (relative sales value method)](https://app.achievable.me/study/cma-part-1/learn/cost-management-measurement-concepts-joint-and-by-product-costing-2)
