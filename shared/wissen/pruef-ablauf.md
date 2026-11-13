# Prüf-Ablauf der Prüf-Sitzung (verbindlich ab 13.11.2026, 22:08)

Entscheid des Nutzers: "Du bist jetzt alleine für die Prüfungen der Projekte zuständig … sehr genau, akribisch,
intelligent und vorausschauend." Fehler, die der Nutzer im Spiel findet, sind Fehler der Prüfung. Dieser Ablauf gilt
für JEDE neue Version jedes Projekts (auch für die geplante Nachprüfung).

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
