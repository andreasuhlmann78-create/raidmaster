# Psychologie der Spieler – Wissen der Prüf-Sitzung (Stand 14.11.2026, 00:05)

Auftrag des Nutzers (13.11. 23:58): "Sie wollen nur etwas im AH kaufen oder es leichter haben, etwas zu kaufen – es muss
einen Nutzen haben. Menschen denken selten rational oder logisch. Es gibt Gier, echte Gefühle, Leid, wenn ein Deal in
die Hose geht. Ich möchte, dass du in Psychologie stark wirst."
Gilt für JEDES Addon, zusammen mit dem Spieler-Bild (projekte.md: Werkzeug für mehr Gold, oft Casual).
Pflicht: Bei jeder Prüfung einer sichtbaren Änderung und bei jedem Auftrag mit Anzeige diese Datei anwenden (Abschnitt 4).

## 0. Grundhaltung

- Wir nutzen Psychologie, um dem Spieler zu HELFEN (weniger Frust, bessere Entscheidungen, echter Nutzen), nie um ihn zu
  manipulieren (keine Glücksspiel-Mechaniken, kein künstliches Dranbleiben, keine Angstmacherei). Ein Addon, das den Spieler
  ausnutzt, verliert sein Vertrauen – und Vertrauen ist bei einem Gold-Werkzeug alles.
- Belegt vs. umstritten trennen: Zahlen aus der Forschung nur mit Quelle; wo die Forschung streitet, steht es dabei.

## 1. Wie Menschen wirklich entscheiden (Verhaltensökonomie)

| Effekt | Was er bedeutet | Stand der Forschung |
|---|---|---|
| **Verlustaversion** (Kahneman/Tversky, Prospect Theory) | Ein Verlust schmerzt stärker, als ein gleich grosser Gewinn freut; oft genannt "etwa doppelt so stark" (λ ≈ 2). | Effekt gut belegt; die Grösse ist umstritten – neuere Arbeiten finden bei kleinen Beträgen oft weniger als 2 oder gar keinen Unterschied. Für uns: ein Fehlkauf verdirbt spürbar mehr Spass, als ein guter Kauf bringt. |
| **Dispositionseffekt** | Gewinner zu früh verkaufen, Verlierer zu lange halten (Hoffnung, Reue vermeiden). | Bei Anlegern breit belegt. Im AH: Ware, die "zu teuer gekauft" wurde, liegt ewig im Lager statt mit kleinem Verlust raus. |
| **Reue-Aversion** | Menschen meiden Entscheidungen, die sie später bereuen könnten; Untätigkeit fühlt sich sicherer an. | belegt. Im AH: lieber nicht kaufen als falsch kaufen – klare, gesicherte Empfehlungen nehmen die Angst. |
| **Anker** | Die erste gesehene Zahl prägt das Urteil ("früher kostete das 5g"). | belegt. Im AH: welcher Preis zuerst steht, prägt das Gefühl "teuer/billig" – darum zuerst "Jetzt im AH", ehrlich. |
| **Gier / FOMO** | Angst, ein Schnäppchen zu verpassen, treibt zu schnellen, schlechten Käufen. | belegt (Herdenverhalten, Knappheit). Im AH: Sniper-Treffer verleiten; darum nur gesicherte Treffer zeigen. |
| **Versunkene Kosten** | "Ich habe schon so viel bezahlt/gewartet, jetzt muss es sich lohnen." | belegt. Im AH: alte Einkaufspreise dürfen den Verkauf nicht blockieren – es zählt, was jetzt am meisten bringt. |
| **Einzelfall statt Summe** | Menschen bewerten jedes Ereignis einzeln (enge Rahmung), nicht das Ganze. | belegt ("narrow framing"). Im AH: jede Entzauberung mit nur Staub fühlt sich wie Verlust an, obwohl die Summe +35 % bringt (KF2, 13.11.). |
| **Variable Belohnung / Beinahe-Gewinn** | Zufällige Belohnungen und "fast gewonnen" halten Menschen am Spiel (Spielautomaten). | gut belegt – WIR NUTZEN DAS NICHT zum Festhalten. Wichtig nur zum Verstehen: Entzaubern IST Zufall, der Spieler erlebt Staub als "Pech". |
| **Kontrolle und Können** | Gefühl, etwas im Griff zu haben und besser zu werden, motiviert nachhaltig. | belegt (Selbstbestimmungstheorie: Kompetenz, Autonomie). Zweck von AHSentinel: "ein Instrument, eine Waffe". |

## 2. Was das für den Spieler im AH heisst

- Er will einen NUTZEN: schneller, leichter, sicherer etwas kaufen/verkaufen, mit dem Gefühl "das hat sich gelohnt".
- Ein misslungener Deal tut weh – stärker als ein guter Deal freut. Ein einziger falscher Rat des Addons kann das
  Vertrauen in alle weiteren Ratschläge zerstören.
- Er denkt in Einzelfällen ("dieses Teil hat mir Verlust gebracht"), nicht in Summen.
- Er ist ungeduldig (Casual, wenig Zeit): Er will eine Antwort, keine Erklärung.

## 3. Folgen für das Design (Grundsätze)

1. **Nur Gesichertes empfehlen.** Lieber eine Empfehlung weniger als ein Fehlkauf (Verlustaversion, Vertrauen).
2. **Ergebnis statt Rechenweg:** "lohnt / lohnt nicht", "+1g 20s" – kein Jargon, keine Faktoren.
3. **Erfolg in Summen sichtbar machen, Einzel-"Pech" einordnen:** Bei Zufallswegen (Entzaubern) nicht jeden Einzelfall als
   Verlust zeigen, sondern das Ergebnis über mehrere Fälle ("Entzaubern diese Woche: +35 %"). So erlebt der Spieler den
   echten Gewinn statt gefühlter Verluste. (Im Details-Fenster, nicht im Tooltip.)
4. **Verluste ehrlich, aber mit Ausweg zeigen:** Liegt Ware mit Verlust im Lager, nicht nur "−2g" zeigen, sondern was jetzt
   am meisten bringt (verkaufen, entzaubern, Händler) – gegen Dispositionseffekt und versunkene Kosten.
5. **Gier bremsen, wo sie schadet:** Schnäppchen-Alarm und Sniper nur bei gesicherten Treffern; keine Dringlichkeit
   vortäuschen ("nur noch 10 s!"), kein Blinken ohne echten Grund.
6. **Den ersten Eindruck richtig setzen (Anker):** Der ehrlichste Preis zuerst ("Jetzt im AH"), dann der Median.
7. **Kontrolle geben:** Der Spieler entscheidet, das Addon rät; Käufe immer per eigener Taste/Bestätigung.
8. **Erfolgserlebnis:** Gewinne sichtbar und freundlich (grün, kurz), ohne Prahlerei; Fehler des Addons sofort beheben.
9. **Ruhe statt Stress:** Kein Ruckeln, keine Flut von Meldungen – beides erzeugt Frust, der nichts mit Gold zu tun hat.

## 4. Prüffragen (bei jeder sichtbaren Änderung)

- Welchen NUTZEN hat der Spieler davon – in einem Satz, ohne Fachwort?
- Wie fühlt es sich an, wenn es schiefgeht? Kann das Addon einen Fehlkauf verursachen? Wie wird das verhindert?
- Zeigt es ein Einzelfall-"Pech" als Verlust, obwohl die Summe gewinnt (enge Rahmung)?
- Verleitet es zu Gier (Dringlichkeit, Blinken, ungesicherte Treffer)?
- Versteht ein Casual-Spieler es ohne Erklärung?

## 5. Erste Anwendung (14.11.)

- KF2/DE30b: Entzaubern lohnt in Summe (+35 % / +20 %), fühlt sich aber im Einzelfall oft wie Verlust an. Vorschlag für
  das Details-Fenster (EB-DET "Rendite je Weg"): Entzaubern als Summe zeigen – genau das wirkt der engen Rahmung entgegen.

## Quellen

- Kahneman & Tversky, Prospect Theory (1979); Überblick: [Yu-kai Chou – Prospect Theory and Loss Aversion](https://yukaichou.com/behavioral-analysis/prospect-theory-loss-aversion-kahneman-tversky/)
- Kritik an der Grösse der Verlustaversion: [Yechiam (2018), Acceptable losses](https://www.Gwern.net/doc/statistics/bias/2018-yechiam.pdf); [Money on the Mind – Controversies surrounding loss aversion](https://www.moneyonthemind.org/amp/controversies-surrounding-loss-aversion)
- Dispositionseffekt: [The Decision Lab – Disposition Effect](https://thedecisionlab.com/biases/disposition-effect)
- Variable Belohnung / Beinahe-Gewinn: [Springer – Near-miss effect (2019)](https://link.springer.com/article/10.1007/s11469-019-00070-9)
