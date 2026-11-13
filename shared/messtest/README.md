# Messwerkzeuge der Prüf-Sitzung

Kleine Addons, mit denen der Nutzer im Spiel etwas misst, das die Prüf-Sitzung nicht offline prüfen kann. Sie werden
**nicht veröffentlicht** (nicht in `download/`, nicht auf CurseForge) und nach der Messung wieder gelöscht.

## GSMesstest (9. Nov. 2026) – Grundlage für das Flüster-Netz von GoldSentinelSync

Misst in WoW Forever:

| Test | Frage |
|---|---|
| T1 Grundweg | Kommen Addon-Flüsternachrichten an, in beide Richtungen? |
| T2 Drossel | 10/s, 20/s und 30 im selben Frame: geht etwas verloren oder kommt verspätet? |
| T3 Offline | Welche Meldung kommt beim Flüstern an Offline- und unbekannte Spieler, lässt sie sich ausblenden? |
| T4 Realm | Ist der Partner auf demselben internen Realm (gemeinsamer Kanal)? Mit T1: Flüstern zwischen den Realms? |

Ablauf: Beide Spieler installieren `GSMesstest.zip` (Ordner `GSMesstest` nach `Interface/AddOns`). Einer tippt
`/gsmess partner <Name>` und `/gsmess alle` (ca. 1 Minute). Danach `/reload`: der RaidMasterUploader bringt das Ergebnis
als `GSDIAG1` nach `testberichte/diagnose/GSMesstest/`. Ohne Uploader: Ergebnis aus dem Chat kopieren.

Für T4 braucht es einen freien Kanalplatz (max. 10); der Kanal `GSMessRealm` wird danach wieder verlassen.
Am aussagekräftigsten: einmal mit einem Gildenmitglied, einmal mit einem Spieler, der dich in gemeinsamen Kanälen nicht
sieht (anderer interner Realm).

Keine Namen im Ergebnis (`<Ich>`, `<Partner>`, `<Offline>`, `<Unbekannt>`). Offline-Test: `shared/tests/test_gsmesstest.py`.


## A1 Auktionen (Version 3, Messauftrag M1 aus `shared/wissen/markt-strategie.md`)

Ohne Partner, am offenen Auktionshaus:

- `/gsmess auktionen` – prüft nur, ob es `C_AuctionHouse.ReplicateItems` und die zugehörigen Funktionen gibt.
- `/gsmess auktionen holen` – ruft `ReplicateItems` **einmal** auf (nur lesen, kauft nichts), wartet bis 60 s auf
  `REPLICATE_ITEM_LIST_UPDATE` und meldet: Anzahl Einzelauktionen, verschiedene Items, Restzeit-Stufen, drei Beispiele
  (Menge, Gebote, Sofortkauf, Status, ItemID, Restzeit, "Besitzer bekannt ja/nein"). **Keine Namen** (Item-, Spieler-,
  Bieter-Namen werden nie ausgegeben). Bei Blizzard nur etwa alle 15 Min. erlaubt.

## A2 Rufen (Version 4, Messauftrag M5 aus `shared/wissen/kommunikation-forever.md`)

Frage: Kommen Addon-Nachrichten über `YELL` und `SAY` bei Spielern in der Nähe an (auch ausserhalb von Gilde und
Gruppe)? Dann könnten Addons wie AHSentinel andere Nutzer z. B. am Auktionshaus finden.

- `/gsmess rufen` – sendet je eine **unsichtbare** Addon-Nachricht über YELL und SAY (kein Chat-Text, niemand sieht
  etwas). Jeder Client in Rufweite mit GSMesstest antwortet per Addon-Flüstern. Nach 30 s Ergebnis:
  Rückgabewert je Weg, eigenes Echo ja/nein, Anzahl Antworten je Weg, und nebenbei alle fremden Addon-Nachrichten über
  SAY/YELL seit dem Einloggen (nur Präfix, z. B. von anderen Addons – zeigt, ob der Weg überhaupt Nachrichten trägt).
- Geht auch allein: Echo und fremde Präfixe sagen schon viel. Mit zweitem Spieler (beide GSMesstest 4, nahe
  beieinander, nicht in derselben Gruppe nötig) ist es belegt.
- Keine Namen im Ergebnis.

## A3 Markt komplett (Version 5.1, Messauftrag M-KOMPLETT aus `shared/wissen/markt-strategie.md`, 13.11.)

Frage des Nutzers: Können wir den Markt **komplett** messen (Angebot, Absatz, Umschlag rund um die Uhr), und wie
gross sind die Daten, wenn andere Spieler sie mitlesen und weitergeben? Ohne Partner, am offenen Auktionshaus:

- `/gsmess markt` – holt alle Einzelauktionen (`ReplicateItems`), liest sie **über mehrere Frames** (3000 je Frame, kein
  Stocken) und misst: Anzahl, Items, Restzeit-Stufen, Rechenzeit und Speicher (M1d), Wiedererkennung über die Signatur
  ItemID:Menge:Sofortkauf (Anteil mehrdeutig), Grösse einer Zusammenfassung je Item (Anzahl Addon-Nachrichten, Dauer über
  Gilde 5/s und Flüstern 40/Min.).
- **Nach 30–60 Min. nochmals `/gsmess markt`:** Vergleich mit dem letzten Scan – geblieben, verschwunden (je Restzeit-
  Stufe beim letzten Scan, vorsichtig: kürzeste zuerst als abgelaufen gezählt), neu; **verschwunden aus Stufe 3+4 =
  gekauft oder abgebrochen** (mit Sofortkaufwert und den 10 ItemIDs mit den meisten Abgängen); Stufenwechsel eindeutiger
  Auktionen (Bedeutung der Stufen, M1b); Abstand und Erfolg jedes Abrufs (wie oft erlaubt, M1c).
- **Passiv:** Holt ein ANDERES Addon die Liste (z. B. Vollscan in AHSentinel), liest GSMesstest still mit
  ("fremd ausgelöst"). Zeigt, ob fremde Vollscans mitgelesen werden können. Dazu zählt es die Such-Ereignisse
  (Suchen von Hand oder anderer Addons). `/gsmess markt mitlesen aus|an`, `/gsmess markt status`, `/gsmess markt löschen`.
- Der Vergleichsstand bleibt über `/reload` erhalten (SavedVariables, einige MB) und wird beim nächsten Scan ersetzt.
  Alle A3-Ergebnisse (bis 300 Zeilen) gehen mit dem Uploader nach `testberichte/diagnose/GSMesstest/`.
- **Keine Namen:** Besitzer, Bieter und Itemnamen werden nie gelesen, nur ItemIDs und Zahlen.

Am besten über einen Abend: alle 30–60 Min. `/gsmess markt` (oder einfach den AHSentinel-Vollscan – GSMesstest liest mit),
mindestens 3 Scans, danach `/reload`.
