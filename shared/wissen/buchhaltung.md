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

## 6. Quellen

- [TSM: Why am I missing sales or purchase data on my items?](https://support.tradeskillmaster.com/en_US/addon/why-am-i-missing-sales-or-purchase-data-on-my-items)
- [TSM Addon: Ledger](https://support.tradeskillmaster.com/tsm-addon-documentation/tsm-addon-ledger)
- [Engadget: A one-hour delay on AH winnings in 2.2](https://www.engadget.com/2007/09/25/a-one-hour-delay-on-ah-winnings-in-2-2/)
- [Joint and by-product costing (relative sales value method)](https://app.achievable.me/study/cma-part-1/learn/cost-management-measurement-concepts-joint-and-by-product-costing-2)
