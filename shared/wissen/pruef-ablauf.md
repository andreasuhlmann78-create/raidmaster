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
