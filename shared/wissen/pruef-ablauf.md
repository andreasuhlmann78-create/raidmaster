# Prüf-Ablauf der Prüf-Sitzung (verbindlich ab 13.11.2026, 22:08)

Entscheid des Nutzers: "Du bist jetzt alleine für die Prüfungen der Projekte zuständig … sehr genau, akribisch,
intelligent und vorausschauend." Fehler, die der Nutzer im Spiel findet, sind Fehler der Prüfung. Dieser Ablauf gilt
für JEDE neue Version jedes Projekts (auch für die geplante Nachprüfung).

## 0. Gehirn immer aktiv (Nutzer 14.11. 00:02: "halte dein Gehirn immer aktiv und nutze es – sehr, sehr wichtig")
- VOR jeder Antwort, jedem Auftrag und jeder Prüfung: die passenden Gehirn-Dateien lesen und anwenden
  (projekte.md Stand/Prio, pruef-ablauf.md, wirtschaft-forever.md, markt-strategie.md, buchhaltung.md, psychologie.md,
  kommunikation-forever.md). Nichts aus dem Gedächtnis behaupten, was dort genauer steht.
- NACH jeder neuen Erkenntnis, jedem Entscheid und jedem Fehler: sofort ins Gehirn schreiben (mit Datum, belegt vs.
  vermutet), pushen und in die Projekt-Dokumente spiegeln. Überholtes markieren, nicht löschen.
- WEITERMACHEN (Nutzer 14.11. 00:22, gilt für JEDES Addon): Nach jeder Veröffentlichung prüfen, ob das Addon mit dem
  letzten Punkt fertig ist – dann SOFORT den nächsten Punkt der Prio-Liste anstossen: Prio-Liste nachführen, Nachricht
  "weiter mit <Kürzel>" als auftraege/<Projekt>/nachricht-weiter-<datum>-<hhmm>.txt ins Repo und dem Nutzer schicken.
  Nie warten, bis der Nutzer fragt. Nicht fertig: genau sagen, was fehlt, und das zuerst verlangen.
  Hat das Projekt eine laufende Weck-Runde (AHSentinel seit 14.11.), genügt das Repo (Prio-Liste) – keine Einfüge-Nachricht,
  damit der Nutzer nicht unnötig kopieren muss; Nachricht nur, wenn die Sitzung länger als 30 Min. nicht reagiert.
- Entscheide (Nutzer 14.11. 00:16: "es darf nicht verloren gehen"): Jeder Entscheid des Nutzers SOFORT in
  shared/wissen/entscheide.md (Zeit, Wortlaut kurz, Wirkung, Auftrag); Überholtes markieren, nie löschen.
- Prioritäten (Nutzer 14.11. 00:15): Jede Änderung an offen-*.txt führt den Block "PRIORITÄTEN" zuoberst nach – alle
  Themen nach Prio geordnet, nie nur einen neuen Punkt oben anhängen.
- Bei Widerspruch zwischen Gehirn und neuen Daten: nachrechnen (Rohdaten), dann Gehirn berichtigen (wie KF2 13.11.).

## 0c. Alles Eingebaute wird streng geprüft – IMMER (Entscheid des Nutzers 14.11. 11:24)
Jede neue Funktion, in jedem Addon, braucht drei Dinge, sonst gilt sie nicht als fertig:
1. Test in der Testroutine – mit erfundenen Fällen, auch absichtlich falschen (der Test muss den Fehler erkennen).
2. Selbstkontrolle im Spiel, wo es messbar ist (Muster SK1: echte Ereignisse passiv gegen die Buchung/Anzeige prüfen,
   Ergebnis im Testbericht und in der Testroutine).
3. Strenge Prüfung durch den Supervisor (Abschnitt A, dreifach: Entscheide, Code/Daten, Risiko).
Jeder Auftrag nennt diese drei Punkte; fehlt einer im Bericht, ist der Auftrag nicht umgesetzt.

## 0d. Fehler VERHINDERN – Supervisor ist verantwortlich (Entscheid des Nutzers 14.11. 14:46: "ich will, dass solche Sachen verhindert werden – von dir!")
Anlass: AHSentinel verteilte beim Entzaubern den Einstand schief (Seelenstaub Faktor 1,65 statt ~1,1, Essenzen 0,2–0,5) – keine
Prüfung hat es gefunden; ich selbst habe daraus falsche Ursachen und eine falsche Empfehlung gemacht.
1. JEDE Aussage an den Nutzer über Geld, Gewinn, Ursachen oder Empfehlungen ist vorher mit Daten-Abbild oder Code belegt.
   Nicht belegt -> ausdrücklich "Vermutung, prüfe ich" – nie als Tatsache. Verteilte Zahlen (Umbuchung) nie als Realität.
2. Bei JEDEM neuen Daten-Abbild (goldsentinel-daten) und JEDER AHSentinel-Version, die Books/Buchhaltung/Entzaubern/Herstellen
   ändert: `python3 -I addon-check/marktanalyse/buchhaltung_plausi.py <AHSentinel.lua>` laufen lassen. WARNUNG -> Befund an
   AHSentinel (mit Zahlen) BEVOR ich dem Nutzer etwas zu Gewinnen sage. Das Werkzeug wächst: jede neue Fehlerart -> neue Prüfung.
3. Neue Buchungs-/Rechen-Funktionen gibt der Supervisor erst frei, wenn eine Plausibilitäts-Selbstkontrolle im Spiel (SK1-Muster)
   dieselbe Fehlerart erkennt (hier SK1-j Verteilung).

## 0e. Nachvollziehbar (Nutzer 14.11. 15:18)
Bei jeder sichtbaren Funktion prüfen: Gibt es den einen Satz "was/wie" (≤ 20 Wörter, Alltagssprache)? Fehlt er -> Befund.

## 0b. Selbstständig handeln (Entscheid des Nutzers 14.11. 08:51)
Fragen der Projekt-Sitzungen und eigene offene Fragen selbst entscheiden: aus entscheide.md, Gehirn und Code/Daten, dreifach
geprüft (1. passt es zu allen Entscheiden? 2. stimmt es mit Daten/Code? 3. was kann schiefgehen – Gold, Daten, Ruckeln,
Spieler-Verständnis?). Dann als Auftrag freigeben und dem Nutzer kurz melden. Rückfrage NUR bei: Risiko für Gold oder Daten,
Widerspruch zu einem Entscheid, neuer Grundsatz/neue Richtung, spürbare Kosten (Nutzung). Nie raten, wo eine Messung fehlt:
dann Messauftrag statt Regel.

## A. Bei jeder neuen Version (Pflicht, in dieser Reihenfolge)
1. `git pull --rebase`; Bericht des Projekts (Projekte prüfen sich nicht selbst – "erledigt" setzt nur die Prüf-Sitzung) in `berichte/<Projekt>/` ganz lesen; Behauptungen nicht glauben, prüfen.
2. `python3 addon-check/addon_check.py download/<Addon>-<Version>.zip` -> kein FEHLER, Warnungen begründet.
3. Änderungen im Code ansehen (Diff zur Vorversion im Projekt-Repo, sofern lesbar) – passt die Umsetzung zum Auftrag
   UND zu allen Entscheiden des Nutzers (Optik-Regel OR, LT, TP, EB, PS, RF …)?
4. Zahlen unabhängig nachrechnen (ZN/`addon-check/nachrechnung.py`, sonst von Hand aus Testbericht/Diagnose):
   jede angezeigte Zahl muss aus ihren Rohdaten folgen; Widersprüche zwischen Zeilen = Fehler.
5. Tempo/Ruckeln aus dem letzten Client-Bericht: PS-Ziele (Tooltip ≤ 5 ms, Reiter ≤ 50 ms, Sniper ≤ 2 s, kein Bild
   > 16 ms, Start ≤ 100 ms, Vollscan ≤ 10 MB/≤ 1 Bereinigung). Verfehlt -> Befund, neue Funktionen warten.
6. Gold-Sicherheit: Kann die Änderung Gold kosten (Kauf, Budget, Preisgrenzen, Einstellen, Abbruch)? Dann gezielt
   die Grenzfälle durchdenken (Doppelzählung, Verdopplung, Rundung, alter Wert nach Zurücksetzen, fremde Addons).
7. Zusammenspiel: gemeinsame Dateien (exact), Sync-Warteschlange, andere GoldSentinel-Addons im selben Client.
8. `shared/wissen/projekte.md` nachführen (Stand, Wichtiges, Weniger wichtiges, offene Entscheide).
9. `auftraege/weckliste.txt` nachführen (welche Sitzung der Nutzer anstossen soll, nach Dringlichkeit) – die
   Sitzungen sind meist nicht aktiv und sehen das Repo erst nach einem Anstoss.
10. Ergebnis IMMER ins Repo (`offen-*.txt`, Befund/Anweisung, Nachricht-Datei, Log), dann dem Nutzer melden.

## A1b. Spieler-Bild (Nutzer 13.11. 23:57, bei JEDER Prüfung)
- Die Spieler wollen mit den Addons einfach mehr Gold machen; sie sind oft Casual und nicht tief im Thema. Jede sichtbare
  Änderung prüfen: Versteht ein Casual-Spieler sie ohne Erklärung? Sonst Befund (vereinfachen, nur Ergebnis zeigen).
- Psychologie (Nutzer 23:58): shared/wissen/psychologie.md Abschnitt 4 (Prüffragen) bei jeder sichtbaren Änderung anwenden –
  Nutzen, Gefühl bei Fehlschlag, Einzelfall statt Summe, Gier, Casual-Verständnis.

## A2. Spielgefühl (Zweck, projekte.md)
- Zusätzlich zu A: Fühlt sich die Änderung im Spiel gut an? Schnell, schlicht, verlässlich, wenig Klicks, Erfolg
  sichtbar, kein Frust. Bei AHSentinel ist das der Zweck ("Spass am Gold verdienen – aber nicht nur").

## A3. Takt der Prüfung (Nutzer 13.11. 22:33)
- Bei jeder Nachricht des Nutzers zuerst kurz `git pull` und nach neuen Versionen/Berichten sehen (kostet Sekunden).
- Während intensiver Zusammenarbeit zusätzlich alle 5 Min. eine kurze Prüf-Runde (Entscheid des Nutzers 22:36;
  Erinnerung in dieser Sitzung);
  nur melden, wenn es Neues gibt. Ruhige Zeiten: die geplante Nachprüfung genügt.
- Takt, Abstände und ähnliche Einstellungen, die den Nutzer betreffen, nie selbst festlegen: zuerst fragen.

## B. Bei jedem Bild, Bericht oder jeder Datei des Nutzers
- Alles auf dem Bild lesen, nicht nur das, wonach gefragt wurde: Version im Titel, Statuszeile (Sync-Warteschlange,
  Scan-Alter), Chatzeilen, jede Zahl im Tooltip nachrechnen, Widersprüche zu früheren Bildern suchen.
- Testberichte: jede FEHLER-, SKIP- und CLIENT-Zeile, dazu Vergleich mit dem Vorlauf (behoben/neu/weiter).

## B2. Informationen selbst holen (Nutzer 22:08: "wenn du für ein Thema Infos brauchst, holst du sie dir")
- Erst selbst suchen: Repo (auftraege/, berichte/, testberichte/, shared/wissen/), Code der Projekt-Repos, Diagnosen,
  SavedVariables-Dateien des Nutzers, Web (Blizzard-Foren, TSM-Doku, Wowhead). Den Nutzer nur fragen, was nur er
  wissen kann (Entscheide, was er im Spiel getan hat).

## C. Vorausschauend (Ideen-Pflicht, markt-strategie.md §9)
- Zu jedem Thema fragen: Was würde ein erfahrener Händler/Buchhalter/Spieler zusätzlich erwarten? 1–3 Vorschläge.
- Folgen einer Änderung für andere Teile und Projekte vorher durchdenken (z. B. gemeinsame Datei -> Ruckeln in AHS).
- Bewährte Werkzeuge (TSM, Auctionator) und Messdaten als Massstab; Zahlen nur "belegt" oder "geschätzt" nennen.

## D. Aus Fehlern lernen
- Findet der Nutzer einen Fehler, den die Prüfung hätte finden müssen: Ursache benennen und hier eine Prüfregel
  ergänzen (Abschnitt E), damit er nicht wieder durchrutscht.

## E. Prüfregeln aus Fehlern (fortlaufend)
- 23.11. Lua-Fehler "Märkte vereinen" (G2) lief seit 21.11. 34× im Protokoll, ohne dass eine Prüfung ihn meldete. REGEL: bei JEDER Prüfung
  alle FEHLER-Zeilen aller Diagnosen seit der letzten geprüften Version zählen (grep " FEHLER "), jede Art einem Auftrag zuordnen.
  Testdaten müssen die echte Form der Daten haben (hier lastOwnScan = Tabelle, nicht Zahl) – im Bericht prüfen, womit getestet wurde.
- 23.11. Eigenes Werkzeug buchhaltung_plausi.py P1 verglich ALLE Verkäufe mit Einstand (auch billig gekauften Fisch/Leder/Stoff) mit dem
  Entzauber-Tagesmittel -> falsche Warnungen. Behoben (nur bt = "de"). REGEL: Jede Prüfung eines Werkzeugs auf genau den Gegenstand
  beschränken, den sie prüfen soll (Herkunftsfeld), und vor dem Weitergeben einer WARNUNG drei Fälle von Hand gegen die Rohdaten prüfen.
  Und: Supervisor-Aufträge zu Anzeigen vor dem Schreiben gegen die Anzeige-Entscheide prüfen (BH3 verlangte eine verbotene Tooltip-Zeile).

E-Regel (18.11.2026 19:30, Hinweis des Nutzers "ich stehe in Undercity, da hat es viele Leute und der Server laggt zum Teil auch von
ganz alleine"): Die Ingametests laufen meist in Unterstadt, also mit vielen Spielern und mit Server-Lag. Ganze Bildzeiten (Bilder über 40 ms,
längstes Bild, Lücken) enthalten dort Last des Spiels und anderer Addons. Darum bei der Bewertung IMMER die EIGENE Rechenzeit des Addons
(Takt "eigene Rechenzeit", Teil max, eigene Arbeit je Bild) vom ganzen Bild trennen.
- FEHLER des Addons nur, wenn die eigene Arbeit die Grenze reisst.
- Ist nur das ganze Bild lang, gilt: "Spiel/Umgebung, Verdacht, zu messen". Gegenprobe an einem ruhigen Ort, nicht als FEHLER.
- Vergleiche zwischen Läufen nur mit gleichem Ort und gleichem Rechner, sonst ausdrücklich als "nicht vergleichbar" kennzeichnen.
- Jeder Testbericht muss den Ort (Zone) ausweisen, und die Zahl der Spieler in der Nähe, wenn sie lesbar ist.
- 15.11. 18:01 Nutzer: "Bei Addon-Kontrollen jeweils das ganze Repo anschauen, damit du verstehst, wie es zu dem Aufbau kam; falls du etwas nicht verstehst, bitte prüfen." REGEL: Vor jeder grösseren Addon-Prüfung Quell-Repo (git log, Struktur, README/CHANGELOG), berichte/<Addon>/, auftraege/<Addon>/ und entscheide.md lesen; jede Auffälligkeit erst gegen diese Geschichte prüfen (Absicht/Entscheid?), dann als Befund festhalten.
- 15.11. 16:45 Uhrzeiten in Blöcken/Nachrichten waren vorausgeschätzt (z. B. "17:00" um 16:31 geschrieben) -> berichtigt. REGEL: Uhrzeit nie schätzen, immer `date +%H:%M` (Europe/Zurich) bzw. Commit-Zeit verwenden.
- 15.11. 16:00 Messwerkzeug-Fehler: GSSniperLog 1.2 las "Server bereit" im Nach-Hook (hooksecurefunc = nach dem Aufruf) -> Zahl wertlos, war aber als "belegt" an AHS gegangen. REGEL: Bei jedem Messwert eines Mini-Addons klären, WANN gemessen wird (vor/nach dem Aufruf, Ereignis-Reihenfolge); unplausible Quoten (z. B. 1207/1211) erst prüfen, dann melden.
- 15.11. 14:57 Nutzer: "Direktive – nie wieder vergessen ins Repo zu laden". Anlass: GSL1-1..5 nur im Chat; das Einfüge-Skript fand seinen Anker nicht, der Commit 14:48 enthielt nur die Log-Zeile. REGEL: Einfügen nur mit assert auf den Anker; nach dem Push `git show origin/main:<Datei> | grep -c <Kürzel>` > 0 prüfen, erst dann melden.
- 15.11. 14:35 Nutzer: "von jetzt an immer Mini-Addons basteln – viel effektiver als einzelne Tests". REGEL: Was im Spiel gemessen
  werden muss, misst die Prüf-Sitzung mit einem eigenen passiven Mini-Addon (shared/messtest/, nicht veröffentlicht, ändert
  kein anderes Addon, keine Namen, Ergebnis als GSDIAG1 über den Uploader). Jedes Werkzeug vor der Abgabe mit nachgebauter
  WoW-Umgebung und Zufallsläufen testen (mehrfach), addon_check ohne FEHLER. Befunde daraus nur als "belegt" weitergeben,
  wenn das Protokoll sie zeigt.
- 15.11. 12:18 Nutzer "du arbeitest schlampig": Supervisor schloss aus EINEM Gold-Stand (12:03), "nur 5 von 67 Käufen kamen an",
  und gab das als Ursache an AHS weiter – um 12:16 waren 70 gekauft (Bestätigungen kamen spät). REGEL (Perfektion, Nutzer
  12:20): Schlüsse über Käufe/Gold nur aus ZWEI Ständen mit genug Abstand (offene Vorgänge abgeschlossen) oder aus dem
  Protokoll; bis dahin als "Verdacht, zu messen" kennzeichnen, nie als Ursache. Code-Befunde erst als Ursache, wenn sie die
  beobachteten Zahlen erklären. Jede Zahl in einer Nachricht an den Nutzer vorher gegenrechnen.
- 14.11. 08:35 ThreatSentinel 2.5.13/BuffSentinel 0.9.21 ein zweites Mal geprüft, obwohl die geplante Nachprüfung es gerade
  tat (Konflikt beim Push, doppelte Arbeit verworfen). REGEL (effizient UND genau, Nutzer 08:29): vor jeder Prüfung
  `git pull` + addon-check/nachpruefung-stand.json + nachrichten-log.txt ansehen; schon geprüft -> nur deren Ergebnis lesen.
  Code-Stellen, die eine Buchung/Anzeige betreffen, dreifach lesen (Ereignis -> Rechnung -> Speicher), bevor ein Befund rausgeht.
- 14.11. Trefferquote "69 %" für die Preisstufen genannt – mit denselben Fällen gelernt und geprüft (zu optimistisch, ohne
  eigenen Fall 66 % bei Grundlinie 58 %). Und ein Schlangen-Modell vorgeschlagen, ohne es vorher an den Daten zu prüfen
  (widerlegt). REGEL: Jede Vorhersage-Güte nur OHNE den eigenen Fall (leave-one-out oder zeitlich getrennt) nennen, immer
  mit Grundlinie ("immer nein sagen") daneben. Jede Modell-Idee erst an den Daten prüfen, dann vorschlagen.
- 13.11. Sniper zählte gescheiterte Käufe, Budget verdoppelt nach Zurücksetzen -> bei jeder Sniper-Änderung Zähler und
  Budget über Fehlkauf, Zurücksetzen und Nachfüllen nachrechnen.
- 13.11. Tooltip-Zeilen widersprachen sich (8s 46c vs. 3s 73c) -> alle Zeilen eines Tooltips gegeneinander prüfen.
- 13.11. Gemeinsame Datei las den Vollscan doppelt (Ruckeln) -> neue gemeinsame Dateien vor der Verteilung im Zusammen-
  spiel mit AHSentinel prüfen (Speicher, Bilder, Sync-Warteschlange).
- 13.11. Sniper sucht nur beim Scrollen, für den Nutzer unsichtbar -> Bedienung jeder Funktion aus Sicht des Spielers
  prüfen: Was muss er tun, steht es auf dem Bildschirm?
- 13.11. Buchhaltung nur vom AH her gedacht -> jeder Goldfluss (buchhaltung.md §5c).
- 13.11. 23:00 Nutzer sagt "go" -> ich habe erklärt statt gehandelt; er musste "push es" nachschieben. Regel: Bei "go",
  "ja", "mach" sofort alles tun, was ich selbst kann (Repo: Auftrag ganz oben als SEHR DRINGEND, Weckliste, Log,
  committen, pushen), DANACH kurz sagen, was er noch tun muss. Dringendes immer zusätzlich zuoberst in offen-*.txt.
- 13.11. 23:50 Faktor ×0,57 war ein Median über Zufallsbeute (Mittel 0,97) – ich habe ihn heute als "belegt" weitergegeben
  und darauf DE30 begründet. Regel: Jede Kennzahl über Zufallsergebnisse prüfen: Median vs. Mittel vs. Summe/Summe
  nebeneinander nachrechnen (aus den Rohdaten im Daten-Repo), bevor sie als Erkenntnis ins Gehirn oder in einen Auftrag geht.
- (14.11. 14:40, Nutzer) Verteilte Zahlen (Umbuchung beim Entzaubern/Herstellen, Kosten-Anteile) nie als Realität deuten und nie
  daraus eine Empfehlung ableiten. Vor jeder Aussage zu Gewinn: Gold rein/raus der ganzen Sache prüfen. Meine Empfehlung "26–35 nicht
  mehr kaufen" war aus einer Material-Zeile abgeleitet – falsch.

E-Regel (14.11. 17:14, Buchhaltungs-Tooltip "schlimmer geht es nicht mehr"): Jede neue oder geänderte ANZEIGE (Tooltip, Kopfzeile,
Spalte) vor der Freigabe gegen die Anzeige-Entscheide prüfen: nur Ergebnisse, nie Rechenweg; höchstens 4–5 Zeilen; nur was der
Spieler selbst ändern kann; Gewinn und % nie mit verschiedenem Vorzeichen; keine Prüf-Diagnose (Abstimmung, "nicht gebucht",
Kostenbasis) für den Spieler – die gehört in den Testbericht. Aufträge des Supervisors, die Diagnosen verlangen, immer mit
"NUR Testbericht" kennzeichnen, sonst baut das Projekt sie in die Anzeige ein.

E-Regel (16.11.2026 00:33, Befund PS58-1 – vom Supervisor selbst gefunden): Nutzt ein Addon die Schnittstelle eines ANDEREN Addons, die Nachbildung
im Test (Dummy/Mock) gegen die Beschreibung des anderen Addons prüfen (z. B. AHSentinel API.md: Reihenfolge und Art ALLER Rückgabewerte).
Ein Test, der mit einer falschen Nachbildung grün ist, belegt nichts. Bei jeder Prüfung einer Version, die eine fremde API neu oder anders nutzt:
Aufrufstelle im Code lesen und Wert für Wert mit der Beschreibung vergleichen.

E-Regel (16.11.2026 05:09, Befund KERN-S1 – beim Kern-Abgleich vom Supervisor gefunden, hätte bei der Prüfung von 0.65.153 auffallen müssen):
Bekommt eine Lern- oder Zählschicht (Kern, Fc-Zähler, Buchhaltung) ihre Fälle aus EINEM Aufruf an EINER Stelle, ALLE Stellen suchen, die das
Ergebnis eines Falls setzen (grep auf die Ergebnis-Zuweisung, z. B. 'e.r = '), und für jede belegen, dass der Fall danach auch gezählt wird.
Mit echten Daten nachweisen: Fälle im Journal seit Start der Schicht = Fälle in der Schicht, je Zelle (Werkzeug für den Kern:
addon-check/marktanalyse/kern_abgleich.py, Abschnitt "Harte Prüfung"). Eine Lernschicht, deren Quote weit von der Journal-Quote liegt,
ist nicht "lernt noch", sondern ein Zählfehler, bis das Gegenteil belegt ist. Ebenso P2/Grundlinien-Regeln: bei seltenen Ereignissen
(Quote < 20 %) taugt ein Treffer-Vergleich bei 0,5 nicht – Güte über Brier prüfen (Befund KERN-P2-1).

E-Regel (16.11.2026 14:45, eigener Fehler des Supervisors beim Kern-Abgleich): Eigene Nachbildungen von Addon-Regeln (kern_daten.show =
K:Show) bei JEDER Prüfung einer Version, die diese Regel ändert, mitziehen und mit einem Test belegen – sonst zeigt der Bericht den
alten Stand ("Rückfall" statt P2). Und: Wählt ein Werkzeug "den neuesten Stand", muss es bei Gleichstand eindeutig entscheiden
(jüngster Journal-Eintrag), nicht nach Dateireihenfolge – Test mit beiden Reihenfolgen.

### E-Regel 17.11.2026 00:30 – Rechtsprüfungen gelten weiter, bis der Nutzer sie aufhebt
Anlass: F-OPT-2 (Navmesh) und das Strassennetz/die Orte aus den Spieldateien (16.11.) wurden beauftragt, ohne die Rechtsprüfung vom
9.11. (EULA 1.C.01/1.C.06/1.C.02.ii, anweisung-wegpunkte-strassen.txt Punkt 12) zu beachten; LevelPilot hat den Widerspruch gefunden.
Regel: Vor jedem Auftrag, der Daten aus Spieldateien, fremden Daten oder Lizenzen betrifft, nach früheren Rechtsprüfungen suchen
(grep "Rechtsprüfung\|EULA\|Lizenz" in auftraege/ und shared/wissen/). Ein "Ja" des Nutzers gilt nur für das, was ihm dabei vorlag;
widerspricht es einer Rechtsprüfung, dem Nutzer die Prüfung vorlegen und ausdrücklich entscheiden lassen.

### E-Regel 17.11.2026 06:30 – Keine Spieldateien auslesen
Entscheid des Nutzers 06:22 ("an die EULA halten"): Aufträge, Werkzeuge oder Daten, die Spieldateien des Clients auslesen oder daraus
abgeleitet sind (Gelände, Texturen, Kartendateien, Navmesh, Gebiets-IDs aus ADT), sind gesperrt – auch offline. Prüfung jeder neuen Version:
keine solchen Daten im Addon (Herkunft im Bericht belegen).

### E-Regel 17.11.2026 07:40 – Prüflisten müssen ohne Vorwissen verständlich sein
Anlass: Nutzer verstand AHS-Prüflistenpunkte am 16.11. teils nicht. Jede Version mit Prüfliste: alles Automatische in '/<addon> testroutine alles';
jeder Handpunkt mit Wo / nummerierten Schritten (genaue Knopfnamen) / wörtlich erwartetem Ergebnis / Kosten / OK-Nicht OK. Sonst nicht annehmen.

### E-Regel 17.11.2026 12:40 – Testroutine selbst auf Ruckeln prüfen (mit offenem Fenster, voller Lauf)
Anlass: AHSentinel 0.65.315, Ingametest des Nutzers: "/ahs testroutine alles" brach mit "script ran too long" ab (TR-RUN-1): das
Testbericht-Fenster wurde nach JEDER Prüfung ganz neu aufgebaut (quadratisch), die Zeitscheibe SLICE_MS war 40 ms statt ≤ 5 ms.
Die Prüfung hatte nur die Ergebnisse der Nachbauten gelesen, nicht die Laufzeit der Routine im vollen Lauf mit offenem Fenster.
Regel: Bei jeder Version, die "testroutine alles" ändert oder einführt, im Code prüfen: (1) Zeitscheibe/Budget je Bild ≤ 5 ms
EINSCHLIESSLICH Anzeige-Aktualisierung; (2) keine Arbeit je Zeile, die mit der Zahl der Zeilen wächst (Fenster/Listen nur gedrosselt
und nur sichtbare Zeilen); (3) Fehler im Fehlerweg (Check "T000", Anzeige) gefangen; (4) Nachbau mit voller Prüfungszahl und offenem
Fenster misst das längste Bild. Fehlt eines davon: Befund, bevor der Nutzer den Lauf im Spiel startet.

### E-Regel 17.11.2026 22:45 – Schnittstellen-Änderungen beim Abnehmer prüfen (API-TAB-1)
AHSentinel 0.65.334 gab zum Sparen eine wiederverwendete Rückgabe-Tabelle zurück; ProfessionSentinel behält Antworten roh -> falsche
Zutaten eines anderen Items. Regel: Ändert ein Addon an einer Schnittstelle (API.lua, Rückgabewerte, Tabellen, Zeitpunkt), prüft die
Prüf-Sitzung im Code JEDES Abnehmers (grep nach dem Funktionsnamen in allen Addon-Repos), wie er die Rückgabe benutzt (behält er sie?
ändert er sie? kopiert er?). Rückgabe-Tabellen sind unveränderlich (Vertrag schnittstelle-ahsentinel-api.md). Bedeutungsänderung = Bruch.

### E-Regel 18.11.2026 06:40 – Nachbau braucht die Spiel-Funktionen, die der Code im Spiel-Zweig benutzt (AHS 0.65.341 Ladefehler)
AHSentinel 0.65.341 warf beim Laden im Spiel ("line" nil nach "a and b and string.match" – Lua 5.1 nimmt nur den ersten Wert). Der
Zweig lief nur, wenn debugstack existiert – die Nachbildung hatte keins, also nie getestet. Regel: Bei jeder neuen Stelle mit
"if _G.<Spiel-Funktion> then …" prüft die Prüf-Sitzung, ob die Nachbildung diese Funktion im Spiel-Format hat und der Zweig im Test
läuft. Zusätzlich im Code suchen: Mehrfach-Zuweisung aus einem and/or-Ausdruck mit Funktionsaufruf (local a, b = x and f()) = Fehler.

### E-Regel 18.11.2026 06:50 – Version im Bericht/Stack zuerst prüfen
Befund an RaidMaster gegen 3.0.33 geschrieben, obwohl der Nutzer noch 3.0.30 installiert hatte (Kopfzeile "RaidMaster 3.0.30"). Regel: Vor
jedem Befund aus einem Ingametest oder einer Lua-Meldung die installierte Version belegen (Kopfzeile des Testberichts, Version in
Locals/Diagnose, Upload). Fehlt sie (reine Lua-Meldung): erst nachfragen oder als "Version unbekannt" kennzeichnen.

### E-Regel 18.11.2026 10:30 – Nachbau darf NICHT mehr können als das Spiel (RaidMaster 3.0.36 T43)
RaidMaster 3.0.36 rief in der Testroutine das globale GetItemInfo – im Forever-Client 1.60.1 gibt es nur C_Item.GetItemInfo; im Spiel
"attempt to call a nil value". Die Nachbildung definierte ein globales GetItemInfo, darum grün. Regel: Bei jeder Prüfung neuer Code-Stellen
nach nackten Aufrufen alter globaler Spiel-Funktionen suchen (GetItemInfo, GetItemInfoInstant, UnitBuff, GetSpellInfo …) und gegen die
Weiche des Addons (RM.GetItemInfo, C_Item …) prüfen. Die Nachbildungen der Projekte bilden den Forever-Client nach: nur die Funktionen,
die es dort gibt.

- E-Regel 20.11.2026 13:44 (Nutzer): Bei jeder Abnahme Screenshots/Berichte auch auf Lesbarkeit prüfen (L1–L8 aus auftraege/hinweis-ui-lesbarkeit-2026-11-20.txt). Fehlt eine dieser Prüfungen in der Testroutine eines Projekts: Befund.

- E-Regel 20.11.2026 14:05 (aus eigenem Fehler der Prüf-Sitzung): Aufträge zu Preisen/Kauf/Verkauf vor dem Eintragen prüfen, nicht danach.
  Am 20.11. wurden 13:25–13:55 Aufträge Stück für Stück aus dem Gespräch eingetragen; drei Prüfrunden fanden danach 19 Lücken (u. a.
  Sniper wäre gesperrt worden, zwei Kaufwerte je Item, Verkaufen ohne Vollscan unmöglich). Pflicht-Check vor jedem solchen Auftrag:
  1. Wirkung auf ALLE Wege (Sniper, Wächter, Liste, Tooltip, Chat, Heute tun, Verkaufen) – wer liest diesen Wert noch?
  2. Gegen bestehende Regeln: S3/L3 "ein Wert überall", WarnRule, FixConfirmed, Kaufgrenze, wirtschaft-forever.
  3. Alle Clients (Forever, Era, TBC, altes AH ohne Vollscan) und Gebühren aus A:CutPct.
  4. Datenlage: auf wie vielen Fällen beruht die Annahme? Unter Mindestzahl -> Messauftrag statt Regel.
  5. Widerspruch zu früheren Aufträgen? Dann den alten Auftrag ausdrücklich ersetzen, nicht anhängen.
  Erst Entwurf, dann diesen Check, dann eintragen – nicht während des Gesprächs Stück für Stück.

- E-Regel 20.11.2026 17:02 (Nutzer: "du stellst sicher, dass es auch eingehalten wird") – GRUNDZIEL Markt (markt-strategie.md):
  Bei jeder Abnahme von AHSentinel (und jedem Addon mit Preisen/Absatz/Prognosen) für jede Zahl, die eine Kauf-, Verkaufs- oder
  Mengenentscheidung beeinflusst, prüfen: Woher stammt sie (gemessen/geschätzt/Annahme)? Auf wie vielen Fällen beruht sie (n)? Ist
  sie im Spiel sichtbar so gekennzeichnet? Geschätzte Werte ohne laufende Messung = Befund. Neue Rechenregel ohne Messbeleg an echten
  Daten = keine Freigabe. Im Prüfbericht eine Zeile "Grundziel Markt: geprüft – gemessen x / geschätzt y / Befunde z".
- E-Regel 23.11.2026 09:57 (Fehler Supervisor, D-MITGL1): Discord-Sichtprüfung nur mit AUFGEKLAPPTEN Kategorien. Eine zugeklappte Kategorie zeigt
  nur den gewählten Kanal – daraus "Kanal fehlt" zu schliessen ist falsch. Vor jedem Befund "fehlt": Kategorie aufklappen (aria-expanded=true)
  oder Kanalliste über die Kanal-Einstellungen/Bot-Log belegen; danach den alten Zustand wiederherstellen.
- E-Regel 23.11.2026 10:42 (Fehler Supervisor, PS 0.9.76): Bei eigenen Nachläufen der Offline-Tests JEDE Lage (forever/era/retail/tbc …) bis zur
  Ergebniszeile lesen – nie mit head abschneiden. Eine Lage ohne Ergebniszeile/Bericht ist kein OK, sondern ein Befund ("kein Lauf"); Zahlen im
  Bericht des Projekts für diese Lage dann als falsch melden. (0.9.76 hatte ich TBC abgeschnitten und den falschen Wert "tbc 251/0" übersehen.)
- E-Regel 23.11.2026 11:38 (Entscheid 11:36): Bei JEDER Version prüfen, ob announce/-Dateien gelöscht/umbenannt wurden
  (git show --stat --diff-filter=DR <commit> -- announce/). Jede Löschung = Befund HOCH an das Projekt.
- E-Regel 23.11.2026 15:36 (UP-422b): Daten-Repo-Dateien können als <Addon>.lua.gz liegen (Uploader 2.3.18). Jedes Werkzeug, das SavedVariables
  liest, nutzt sv_lesen bzw. gzip; bei fehlender .lua eines Rechners zuerst nach .lua.gz suchen, nie "Daten fehlen" melden ohne diesen Blick.
- E-Regel 24.11.2026 07:08 (AHS-R1): Bei JEDER Version den GitHub-Release-Text ansehen (gh api repos/<owner>/<repo>/releases/tags/v<Version> -q .body):
  Deutsch muss drin sein (Entscheid 15.11. 12:38). AHSentinel hatte seit Wochen nur Englisch, keine Prüfung hat es gemeldet.
- E-Regel 24.11.2026 07:08 (AHS-I4-a): Folgert ein Bericht aus Messfeldern eine Ursache, ALLE Zahlen desselben Felds gegeneinander rechnen
  (hier: +104 907 KB im Bild gegen "ohne Addon −378 KB seit Scan-Beginn"). Widerspruch = Befund, Schluss nur als Verdacht.
- E-Regel 24.11.2026 10:40 (D-ANN): Bevor dem Nutzer ein Punkt als "offen" gemeldet wird, den LETZTEN Eintrag dazu in offen-*.txt lesen
  (grep Kürzel | tail). D-ANN1/D-ANN2 waren seit 23.11. 12:43 erledigt, wurden aber aus dem eigenen Stand als offen gemeldet.
- E-Regel 25.11.2026 08:59 (RM-TAINT1, Lua-Fehler im Ingametest): Bei jeder Code-Prüfung grep nach ToggleCharacter/ShowUIPanel/HideUIPanel/Toggle*Frame
  in Addon- UND Testcode. Ein Addon (vor allem eine Testroutine) öffnet nie selbst ein Blizzard-Fenster: der Blizzard-Code läuft dann "tainted"
  und scheitert in Forever an geschützten Werten (secret values). Ausnahme nur nach Klick des Spielers und im Spiel belegt ohne Fehler.
- E-Regel 25.11.2026 06:53 (sicherung "hinkt nach" – war falsch): Daten-Repo-Zweige vor jeder Aussage mit `git ls-remote origin` bzw.
  `git fetch origin '+refs/heads/*:refs/remotes/origin/*'` frisch holen; nie aus einem alten lokalen Zweig-Zeiger auf Rückstand schliessen.
- E-Regel 25.11.2026 06:41 (CI rot seit 24.11. 06:57, vom Nutzer an ~40 Mails entdeckt): Bei JEDER Prüfung und bei jedem Sitzungsstart
  `gh run list --workflow "Addon-Prüfung" -L 5` ansehen. Ist der letzte abgeschlossene Lauf "failure": Ursache in addon-check/bericht.md lesen und
  sofort als HOCH-Auftrag an das verursachende Projekt. "cancelled" = von einem neueren Lauf abgelöst, kein Befund. Ursache diesmal: RaidMaster hat
  ab 3.0.40 die alten Zips in download/ nicht mehr entfernt -> "Version NIEDRIGER als veröffentlicht" für 3.0.40–3.0.43.
- E-Regel 24.11.2026 21:32 (UP-MIN1): Ob ein Rechner liefert, gegen RaidMasterUploader/mindestversion.txt prüfen (stand.json "uploader" nicht
  darunter), nicht mehr gegen die neueste Uploader-Version. Ausnahme bis zum Wechsel: 2.3.20–2.3.22 liefern erst mit 2.3.23.
- E-Regel 24.11.2026 19:50 (GSMesstest): Bei jeder Leistungs-/Speicher-Auswertung die Zeile "je Addon" lesen. Steht dort ein Messwerkzeug
  (GSMesstest o. ä.) oder ein fremdes Addon mit grossem Anteil, gelten die Werte als verfälscht – kein Befund ans Projekt. Messwerkzeuge des
  Supervisors nach der Messung SOFORT beim Nutzer entfernen lassen und das im Stand vermerken (GSMesstest blieb vom 13. bis 24.11. aktiv).
- E-Regel 24.11.2026 19:48 (T458, Info des Nutzers 19:47 "sowas darf nie mehr passieren...auffällig keine bzw. Unregelmässigkeiten könnten auch
  durch mich durch solche deine verursache...wir brauchen da für keine Prüfung ingame"): Ein einzelner Ausreisser (ein Bild, eine Portion, ein
  Messwert) in einem Ingametest, bei dem der Code an dieser Stelle unverändert ist, wird ZUERST gegen die Bedienung des Nutzers gehalten
  (Fensterwechsel/Alt-Tab, Spiel im Hintergrund oder minimiert, Zuschauen, Laden, andere Programme). Vor der Bewertung fragen bzw. aus dem
  Bericht lesen, ob der Nutzer eingegriffen hat. Solange das nicht ausgeschlossen ist: kein FEHLER-Befund an das Projekt, kein Blocker,
  keine Code-Arbeit und KEINE zusätzliche Ingame-Prüfung dafür verlangen – nur als "Ausreisser, Bedienung möglich" vermerken; bewertet
  wird der nächste reguläre Lauf. Erst wenn der Wert in einem Lauf ohne Eingriff wiederkommt, ist es ein Befund.
- (25.11.) Sandbox-/Livedaten-Prüfungen, die nur Anzahlen vor/nach vergleichen, auf Wege von AUSSEN prüfen (Empfang über Comm/Sync, Hintergrund-Jobs, Recorder): Code lesen, ob jeder Schreibweg während des Laufs gesperrt oder mit Herkunft gezählt ist. Ein Unterschied ist erst ein Leck, wenn die Quelle belegt ist (Befund LP-SB1).
- (25.11.) CurseForge-Kommentare bei JEDER Prüfung einer CF-Version und täglich lesen (Seite comments, alle Seiten, Antworten aufklappen). Jeder Kommentar ohne passende Antwort zur aktuellen Version -> Antwort-Entwurf (am CHANGELOG belegt, nie mehr versprechen als belegt), posten (seit 25.11. 15:23 ohne Vorzeigen, Entscheid des Nutzers), im nachrichten-log eintragen, dem Nutzer danach melden (Entscheid Nutzer 25.11. 11:09: "die Leute erhalten immer eine Antwort").
