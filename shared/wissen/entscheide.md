# Entscheide des Nutzers – vollständiges Protokoll (Gehirn der Prüf-Sitzung)

Auftrag des Nutzers (14.11. 00:16): "Es darf nicht verloren gehen von dem, was wir entscheiden."
REGEL: Jeder Entscheid des Nutzers kommt SOFORT (im selben Schritt wie der Auftrag) hier hinein – mit Datum/Uhrzeit,
Wortlaut kurz, Wirkung und wo er umgesetzt wird (Auftrag/Kürzel). Spätere Änderungen eines Entscheids: alten Eintrag als
"ÜBERHOLT durch <Datum>" markieren, nie löschen. Neueste oben je Tag. Vor jeder Arbeit lesen (pruef-ablauf.md Abschnitt 0).
Ältere Entscheide (vor 13.11. abends) stehen in wirtschaft-forever.md (Abschnitte "Entscheid des Nutzers …"),
markt-strategie.md, buchhaltung.md, projekte.md und in den offen-*.txt; sie gelten weiter.

## 14.11.2026

| Zeit | Entscheid | Wirkung / Auftrag |
|---|---|---|
| 14:46 | "Ich will, dass solche Sachen verhindert werden – von dir!" (schiefe Einstand-Verteilung beim Entzaubern, meine falschen Aussagen dazu) | pruef-ablauf.md 0d; Werkzeug addon-check/marktanalyse/buchhaltung_plausi.py bei jedem Daten-Abbild; Auftrag AHSentinel SK1-j. |
| 14:15 | Entzauber-Fenster ohne Befehl: gewählt NUR "Knopf am Berufsfenster" (nicht automatisch, nicht Minikarte, nicht Taste). | offen-ahsentinel.txt DW-K1 |
| 14:09 | "Ich will, dass alles 3 mal geprüft wird, bevor es live geht." (zu den Herstellen-Ketten; bestätigt Grundsatz 11:24) | Neue Anzeigen erst nach Test + Selbstkontrolle + Supervisor-Prüfung live; vorher nur im Testbericht. S3-2 FREIGABE. |
| 14:08 | "Es gibt mehr Möglichkeiten für ein Geschäft mit Marge 20–30 %" (Beispiel: Leinenstoff 25c -> Ballen -> Braune Leinenhose -> Entzaubern, ≈ +22c je Hose) – Ketten Kaufen -> Herstellen -> Entzaubern/Verkaufen systematisch finden. | offen-ahsentinel.txt S3-2 (RK1/RK3, S3b/S5). "Die Masse macht das Gold" (14:06) – mit Grenze je Zutat (lohnt bis) und Absatz-Prüfung. |
| 13:44 | LevelPilot: Schalter "Meldungen" in den Optionen schaltet ALLE Ingame-Meldungen ab (z. B. "Hier ist der Erste-Hilfe-Lehrer") | offen-levelpilot.txt ML1 SOFORT; Ausnahmen (Supervisor 13:50): Antworten auf eigene Befehle, Fehler auf eigene Handlung, Guide selbst |
| 08:55 | "Bevor die pusht, bitte alles mit dem Projekt Addonprüfer bzw. Supervisor prüfen lassen … Repo zurücknehmen" und "sag das auch den anderen Routinen via Repo". Geplante Aufgaben (Routinen) schreiben ihre Ergebnisse nicht mehr selbst in auftraege/ und schicken keine Nachrichten zum Einfügen mehr, bevor der Supervisor (Prüf-Sitzung im Projekt Addonprüfer) sie geprüft hat. | Nachprüfung 08:35 (Commit 506ae8c3) zurückgenommen; Entwurf liegt im Projekt Addonprüfer. Regel für alle Routinen: auftraege/hinweis-routinen-supervisor-2026-11-14.txt |
| 11:24 | GRUNDSATZ, gilt IMMER: "Wenn etwas eingebaut wird, muss es streng geprüft werden." Jede neue Funktion in jedem Addon kommt mit (1) Test in der Testroutine (mit erfundenen Fällen, auch absichtlich falschen), (2) Selbstkontrolle im Spiel, wo messbar (wie SK1), (3) strenger Prüfung durch den Supervisor (dreifach). Ohne diese drei gilt nichts als fertig. | pruef-ablauf.md 0c; auftraege/README.md; alle offen-*.txt (Grundsatz). |
| 11:23 | "AHS soll selbst prüfen, ob es stimmt – in die Testroutine einbauen." Statt Handtests des Nutzers (Gold vorher/nachher) laufende Selbstkontrollen im Spiel. | offen-ahsentinel.txt SK1 (a–i), vor Rechenkern S1. Gilt sinngemäss für alle Addons (später). |
| 09:01 | Schwere Rechnung ausserhalb öfter als wöchentlich: Tabellen TÄGLICH neu (Montag zusätzlich grosse Nachrechnung). | anweisung-rechenkern-066.txt A1 (täglich), A2 vorgezogen in S2; Prüf-Sitzung baut Rechenwerkzeug + tägliche geplante Aufgabe. |
| 08:51 | SELBSTSTÄNDIG: "Wenn du Fragen hast – prüfe alle sauber und 3-fach und lass es ausführen. Du musst selbstständiger werden. Nur bei ganz wichtigen Sachen Rücksprache. Du hast vieles im Gehirn und weisst, was ich will und was nicht." -> Prüf-Sitzung entscheidet selbst (aus Entscheiden/Gehirn, dreifach geprüft) und gibt Aufträge frei; Rückfrage nur bei: Gold-/Datenverlust-Risiko, Widerspruch zu einem Entscheid, neue Richtung/Grundsatz, Kosten (Nutzung). Danach dem Nutzer kurz sagen, was entschieden wurde. | pruef-ablauf.md 0. Rechenkern-Bauplan 0.66 wird nach dreifacher Prüfung freigegeben (Leitlinie: lernende Statistik im Spiel, Rechnung ausserhalb, Modell nur wenn messbar besser). |
| 08:47 | "Alle 30 Min. ins Repo schauen und die Fragen bzw. Bemerkungen der Testroutinen/Projekt-Sitzungen beantworten – alles 3 mal prüfen." | Prüfrunde alle 30 Min. (geplante Aufgabe in dieser Sitzung), Antworten in offen-ahsentinel.txt "ANTWORTEN DER PRÜF-SITZUNG". |
| 08:42 | Verkaufen: Das gewählte Item muss rechts sofort erscheinen UND dem jetzigen Stand im AH entsprechen – "1:1 gleich wie im AH" (keine 5 Min. alten Angebote). | offen-ahsentinel.txt UI-V1/UI-V1b. |
| 08:30 | "Konzentrier dich auf AHS, der Rest kommt step by step später." Prüf-Sitzung arbeitet nur an AHSentinel; andere Projekte nur lesen/vermerken, wenn etwas brennt (Sicherheit, Datenverlust). | projekte.md Fokus. |
| 08:29 | "Du hast gesehen, was die dreifache Prüfung bewirkt hat – ich will, dass du immer effizient, aber genau deine Aufgaben ausführst." Gilt für jede Arbeit der Prüf-Sitzung. | pruef-ablauf.md 0 und E. |
| 08:18 | Händler: "Geld geht raus und Ware kommt rein – das ist ganz einfach messbar. Keine Fehler, lieber alles 3 mal prüfen." -> Händler-Geschäfte aus Gold- und Taschen-Unterschied buchen, nicht aus Listenpreisen. | offen-ahsentinel.txt HB1. |
| 08:17 | Der Briefkasten wird nicht immer über AHSentinel geöffnet – auch von Hand abgeholte Post muss voll gezählt werden (Verkäufe, Käufe, Ablauf, Abbruch). | offen-ahsentinel.txt BR1 (BR1-1 bis -3). |
| 08:07 | "Ich will, dass du alles nochmals genau prüfst – und vergiss nicht dein Gehirn." Gilt für Vorschläge zum Rechenkern: erst an den Daten prüfen, dann vorschlagen. | markt-strategie.md 8g GEMESSEN 08:20, pruef-ablauf.md E (14.11.). |
| 08:02 | Frage des Nutzers: aus dem Rechenkern eine kleine KI basteln? -> noch OFFEN (Vorschlag der Prüf-Sitzung: lernende Statistik im Spiel, schwere Rechnung ausserhalb, Modell erst bei vielen Fällen und nur wenn nachweislich besser). | Entscheid ausstehend. |
| 01:38 | Gute Nacht – "wenn ich morgen hi sage, nehmen wir den Faden genau hier wieder auf". | auftraege/morgen-uebersicht-2026-11-14.txt (Einstieg bei "hi"). |
| 01:23 | Sparsam (Wochen-Nutzung ca. 32 %), aber es darf nicht zum Stillstand kommen. | AHSentinel: weiterarbeiten, Weck-Runde 30 Min., kurze Berichte, kleine abgeschlossene Versionen; Prüf-Sitzung nachts alle 30 Min. |
| 01:19 | AHSentinel die Nacht durcharbeiten lassen – morgen früh soll alles fertig sein. | offen-ahsentinel.txt zuoberst NACHT-ARBEIT; Prüf-Sitzung prüft die Nacht durch (5-Min.-Runden). |
| 01:15 | Anzeige in ZAHLEN statt Worten: grün = lohnt sich (+x), rot = lohnt sich nicht (−x) – "ich finde Zahlen besser als Buchstaben". | Rechenkern-Regeln, DE30b, PR1: überall Zahlen grün/rot (wie LT). |
| 01:06 | Bestand des Nutzers: 19g 89s Gold, acht 10er-Taschen, Kleinkram auf der Bank – keine Astralessenzen/Seelenstaub. | AHSentinel BH-AUS-3 (Phantom-Ware umbuchen, Lager-Abgleich mit Taschen/Bank). |
| 00:53 | Korrektur: "verkauft sich schnell oder gar nicht" stimmt nicht – wird er unterboten, nimmt er das Angebot heraus, statt es ablaufen zu lassen. | PR1: Abbruch-Grund "unterboten" messen, Abbruch = Teil der Kette; markt-strategie.md berichtigt. |
| 00:50 | ThreatSentinel bekommt den gemeinsamen Sync ("kann natürlich umgesetzt werden"). | offen-threatsentinel.txt SYNC (HOCH). |
| 00:50 | Prognose: Abbruch durch den Spieler und echten Ablauf unterscheiden; Händler stellen nie länger als 2 Std. ein (entzaubern und gleich verkaufen). | AHSentinel PR1. |
| 00:38 | "Sehr gut, so stelle ich mir das vor – klar und sachlich, immer auf das Wohl des Spielers bezogen." (zur Wellen-/Zyklen-Auswertung) | So berichten: Messwert, belegt/nicht belegt, was es für den Spieler heisst; projekte.md "So denkt der Nutzer". |
| 00:30 | Diese Definition (nie Ruhemodus, nicht stören) hat OBERSTE PRIO für die Umsetzung – sofort pushen. | offen-ahsentinel.txt Prio 0. |
| 00:29 | Die Weck-Runde darf das Projekt bei der Arbeit nicht unnötig stören. | Nur eine Runde offen, unterbricht nie, still weiterarbeiten, nur Neues melden. |
| 00:28 | AHSentinel-Projekt darf nie in den Ruhemodus fallen; Weck-Runde alle 5 Minuten (Antwort 00:30). | offen-ahsentinel.txt zuoberst "NIE IM RUHEMODUS" (send_later an sich selbst). |
| 00:22 | Nach jeder Version prüfen, ob das Addon mit dem letzten Punkt fertig ist, und es dann gleich mit dem nächsten Punkt weitermachen lassen – ab jetzt immer, für jedes Addon. | pruef-ablauf.md 0 "WEITERMACHEN"; Nachricht "weiter mit …" nach jeder Prüfung. |
| 00:19 | Zyklen messen: Tages-, Wochen- und Monatszyklen. | AHSentinel Prio 6 (Zyklen mit JK1–JK4), Discord-Sammelstelle (hour_of_week, Monat mit KEEP90), markt-strategie.md. |
| 00:18 | "Nur wer den Markt vorausahnen kann, macht richtig Gold – aber immer fundiert und belegbar." Markt-Wellen messen gehört dazu. | Grundsatz markt-strategie.md; AHSentinel Prio 6 (0.66 Rechenkern mit MA4/M-Welle/MA6, Trefferquoten). |
| 00:12 | (an AHSentinel-Sitzung) Die Prüf-Sitzung bestimmt die Reihenfolge; Bedenken meldet die Projekt-Sitzung im Bericht, die Prüf-Sitzung gibt sie an den Nutzer weiter. | Bericht 0.65.123; gilt sinngemäss für alle Projekte. |
| 00:10 | (an AHSentinel-Sitzung) Kompakter Preisverlauf im Spiel: "ja machen". | RF-M1 (2): drei Zahlenlisten je Item im Spiel, gespeichertes Format bleibt. |
| 00:16 | Nichts von dem, was wir entscheiden, darf verloren gehen. | Diese Datei; Regel in pruef-ablauf.md 0. |
| 00:15 | Alle Themen/Änderungen im Repo immer nach Priorität ordnen. | Block "PRIORITÄTEN" zuoberst in jeder offen-*.txt (auftraege/README.md). |
| 00:11 | Buchhaltung mit echten Daten durchrechnen ("go"). | Befund BH-AUS (Gewinn falsch, Gold-Abstimmung leer). |
| 00:05 | AHSentinel-Prioritäten der Reihe nach abarbeiten. | Liste in offen-ahsentinel.txt. |
| 00:02 | Gehirn beim Arbeiten immer aktiv halten und nutzen ("sehr, sehr wichtig"). | pruef-ablauf.md Abschnitt 0. |

## 13.11.2026 (Abend)

| Zeit | Entscheid | Wirkung / Auftrag |
|---|---|---|
| 23:58 | Spieler denken selten rational (Gier, Gefühle, Ärger bei Fehlkauf); jedes Addon braucht echten Nutzen; Prüf-Sitzung soll in Psychologie stark werden. | psychologie.md, Pflicht in CLAUDE.md; EB-DET Entzaubern als Summe. |
| 23:57 | Spieler sehen die Addons als Werkzeug für mehr Gold, oft Casual – bei jedem Addon im Hinterkopf. | projekte.md "Spieler-Bild", pruef-ablauf.md A1b. |
| 23:51 | Entzaubern: im Spiel nur "lohnt / lohnt nicht", kein Schnickschnack. | DE30b. |
| 23:49–23:51 | Kein Budget-Deckel je Gruppe; stimmt die Tabelle (Chance/Menge ±10 %) in gemessenen Gruppen, gelten für neue Gruppen auch 20 % (voller Vorteil). | DE30b endgültig (0.65.122). ÜBERHOLT: 23:47 (25 % + Lern-Budget). |
| 23:47 | Solange nur der Tabellenwert bekannt ist: vorsichtig, aber nicht defensiv. | ÜBERHOLT durch 23:49/23:51. |
| 23:46 | Gruppen = welche Materialien beim Entzaubern herauskommen (Stufenband, Qualität; Rüstung+Waffe zusammen). | DE30b. |
| 23:45 | Mindestgewinn Entzaubern je Gruppe ("beides, je nach Itemgruppe"): 20 % / 30 %. | DE30b; ersetzt die feste 30-%-Regel. |
| 23:41 | Faktor ×0,57 "jetzt genau dem Thema annehmen" – "verdammt wichtig". | KF2 (Median-Fehler belegt, Summe/Summe), 0.65.121. |
| 23:35 | Bot-Marktdaten 90 statt 35 Tage behalten ("der Server hat 2 GB"). | Discord KEEP90 (Grenze ≤ 1 GB, ≤ 50 % frei, Bot misst selbst). |
| 23:33 | GoldSentinelMarkt: 6 statt 2 Scans für den Uploader – Ruckeln nicht vergessen. | GoldSentinelMarkt v3 (≤ 1,5 MB). |
| 23:27 | Alles über alle Addons merken, nichts vergessen, immer nach Prio handeln. | projekte.md nach Prio. |
| 23:26 | Gemeinsame Befehlsliste für alle Addons bauen; AHSentinel zuerst, andere später. Bald Addon für Addon perfektionieren. | shared/GoldSentinelCmdHint.lua v1, CH-G. |
| 23:25 | Details-Fenster: zusätzlich Rendite je Weg, Anzahlung verfallen, Verkaufsquote (nicht "gebundenes Gold"). | EB-DET. |
| 23:23 | Ideen: I2 "bester Verkauf des Tages" NEIN; I3 Vermögensverlauf SPÄTER; I4 Plan fürs Offline-Sein SPÄTER; I6 Nachfrage-Wellen nur MESSEN. | projekte.md Ideen; I6-M. |
| 23:20 | Discord-Sitzung fragen: Bot-Datenvolumen grösser, Einflüsse? | Bericht Discord 23:45 (Grenzen weit weg). |
| 23:19 | Client-Tests aller Addons zurückstellen, aber nicht vergessen. | weckliste.txt "Für den Nutzer" (ZURÜCKGESTELLT). |
| 23:02 | Keine Zwischenstände melden, die nichts sagen. | Prüf-Runden melden nur Neues. |
| 23:00 | Bei "go" sofort handeln und pushen, nicht erst erklären. Dringendes zuoberst ins Repo. | pruef-ablauf.md E. |
| 22:57 | Entzaubern mindestens 30 % Gewinn (sehr dringend). | DE30 (0.65.119). ÜBERHOLT durch 23:45 (je Gruppe). |
| 22:47 | AH-Gebühren beim Namen nennen (Wort des Spiels) und aus Sicht eines Buchhalters betrachten. | EB-NAME, BH-ANZ, buchhaltung.md 5d. |
| 22:36 | Prüf-Runde alle 5 Minuten während intensiver Zusammenarbeit; Abstände nie selbst festlegen. | pruef-ablauf.md A3. |
| 22:29 | Sitzungen sind selten alle aktiv (1–3) -> Weckliste. | auftraege/weckliste.txt. |
| 22:28 | Projekte prüfen sich nicht selbst: nur testen und Fehler melden, "umgesetzt, zur Prüfung". | CLAUDE.md, auftraege/README.md. |
| 22:2x | Ideen I5 Schnäppchen-Alarm JA (im Spiel, nur Gesichertes, Daten ≤ 60 s); I7 Herstellungs-Kette JA (simpel); I1, I8 NEIN. | SA, HK. |
| 22:20 | Nur Gesichertes anzeigen ("nicht gesichert darf es eigentlich gar nicht geben"). | alle Empfehlungen. |
| 22:13 | Zweck AHSentinel: Spass am Gold verdienen – aber nicht nur. Neue Ideen entwickeln, offen für alles. | projekte.md, Ideen-Pflicht. |
| 22:09 | Wichtiges und weniger Wichtiges über alle Projekte im Gehirn ablegen. | projekte.md. |
| 22:08 | AHSentinel "pfeilschnell" in allem; Prüf-Sitzung allein für Prüfungen zuständig, akribisch, vorausschauend; Infos selbst holen. | PS, pruef-ablauf.md. |
| 21:xx | Ruckelfrei als Freigabe-Bedingung (RF); Zahlen müssen stimmen und geprüft sein (ZN); Recherche PX a–e freigegeben. | RF, ZN, PX. |
| 21:xx | Jeden Goldfluss erfassen (Händler, Handel, Post, Reparatur …), Eigenbedarf; Buchhaltung optisch gleich, ein Knopf "Details" (Standard Gesamt, Gold pro Stunde = Handelsgewinn ÷ Online-Zeit ohne AFK). | EB. |
| 20:xx | Tooltip: eine Zeile "Gewinn: ±x / Stück" (grün/rot) statt "Entzaubern lohnt …" und "Lohnt bis"; "Materialpreise korrigiert" nicht anzeigen; nirgends Rechenwege. | LT, LT3, OR. |
| 20:xx | Preise: "Jetzt im AH" (ein echtes Angebot, nie Durchschnitt, Frische sichtbar) + "Median" (14 Tage, anpassend, junge Wirtschaft, keine Pfeile – Trend nur im Hintergrund). | TP. |
| abends | Marktdaten anderer Spieler still mitlesen (mit Schalter zum Ausschalten), gildenübergreifend; "komplette Marktanalysen". | GoldSentinelMarkt, MN, GSMesstest. |

## 13.11.2026 (tagsüber, nachgetragen 14.11. 00:20 – Hinweis des Nutzers "da war noch mehr")

| Zeit | Entscheid | Wirkung / Auftrag |
|---|---|---|
| 15:2x | Verfälschung durch eigene Scans sofort korrigieren ("diese Fehler vor allem mit der Verfälschung sofort"). | 0.65.111 SOFORT (S1–S4). |
| 14:34–15:28 | "Wir brauchen komplette Marktanalysen, um den Markt komplett zu messen." Marktdaten anderer Spieler STILL mitlesen (keine Abfrage, aber Schalter zum Ausschalten), auch gildenübergreifend; kleines Mess-Addon bauen. | GSMesstest 5/5.1 (M-KOMPLETT), GoldSentinelMarkt (MN1–MN8), Discord-Sammelstelle MN7. |
| 14:35 | GuildSentinel: 5. Bewerbungsfrage "Wie alt bist du?", Mindestalter 16, nette Absage, Alter nie speichern; Werbetext "im Aufbau, alle Klassen". | GA1/GA2. |
| 14:08 | Preisverlauf älter als 48 Std. in kompaktem Format (mit Sicherung und Prüfung vor/nach). | PD7. |
| 13:15 | Verbindlicher Releaseplan AHSentinel: 0.65.109 falsche Zahlen, 0.65.110 Ruckeln, 0.66 Rechenkern, 0.67 Rhythmus, 0.68 Markt-Reiter. | offen-ahsentinel.txt. |
| 13:12 | Immer alles ins Repo, auch jede Nachricht zum Einfügen (nachricht-*.txt). | CLAUDE.md. |
| 08:25 | Sniper: Budget aufgebraucht -> Abfrage, Enter = auffüllen um den ursprünglichen Betrag, Esc = nein. | SB. |
| 08:05 | Warnschutz bei zu billigem Verkauf / zu teurem Kauf (Raidwarnung-Ton, Blinken, Bestätigung). | WS. |
| 07:40 | Befehlsliste beim Tippen in ALLEN Addons, alle Befehle; Mausklick wählt, Enter führt aus (Variante b). | BL, CH; seit 23:26 gemeinsame Datei (CH-G). |
| 07:12 | GuildSentinel: Rekrutierung in Phasen (jetzt alle Klassen suchen, Vorgaben für Raidfähigkeit behalten); Rechtsklick-Menü auf Mitglieder (Ränge, Befördern, Twink). | RP1–RP9, RV1–RV9. |
| 07:10 | ProfessionSentinel: Marktwissen fürs Herstellen und Gold-Rangliste (Werte nur über AHSentinel.API). | PM1–PM7, API-PM. |
| 06:55 | Fehler dürfen nicht wieder passieren: umfassende Tests in allen Projekten; jeder Befund bekommt einen bleibenden Test. | TU1–TU9. |
| 06:47 | Verkaufte Auktionen nach Aktualisieren ausblenden. | MV1. |
| 06:42 | Sniper hält mehrere Treffer; leere Menge = 1. | SM. |
| 06:18 | Markt-Reiter neu: ein Addon für JEDEN Spieler (Wege statt Spielstile), Spielrhythmus "seit deinem letzten Besuch", Kacheln je Stufenband statt Index über alle Waren; nur Belegtes, sonst grau "lernt noch"; "es muss streng überwacht und wenn nötig verbessert werden". | anweisung-markt-reiter.txt (RK1–RK8, MR1–MR11, MA1–MA6, Ü1–Ü4); wöchentliche Markt-Überwachung (geplante Aufgabe). |
| 06:18 | MARKT-WELLEN MESSEN: je Stufenband (1–25, 26–45, 46–60 bzw. Staub/Essenz/Splitter-Bänder) Tagesmedian und Richtung; Trend-Rückblick wöchentlich wiederholen. | MA4 (Stufenbänder), MA6 (Trend-Regel), M-Welle (markt-strategie.md 4). |
| morgens | Blizzard-Foren regelmässig auf Blueposts prüfen, die die Projekte betreffen, und handeln. | geplante Aufgabe Blueposts (07:38/21:38). |
| 05:44 | GuildSentinel: Einladen in die Gilde bleibt gesperrt (vom Spiel in Forever verboten). | GV1 = Absicht. |

## 12.11.2026 (aus dem Gehirn, zur Vollständigkeit)

| Zeit | Entscheid / Beobachtung des Nutzers | Wirkung / Auftrag |
|---|---|---|
| 07:02 | Levelwelle: "Die Leute leveln höher, viele verkaufen ihr Zeug im AH" – "es wird auch Items mit höherem Item-Level betreffen" (die Welle wandert mit). | M-Welle: je Stufenband Tagesmittel aus den Tages-Ständen messen; Band 41–50 und 51–60 als Referenz festhalten (markt-strategie.md 4). |
