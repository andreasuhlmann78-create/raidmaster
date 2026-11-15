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

## GSSniperLog (15. Nov. 2026) – alles rund um den AHSentinel-Sniper mitschreiben

Auftrag des Nutzers 14:03/14:04: "ein Mini-Addon, das ich laufen lassen kann und alles im Hintergrund live testet, ohne dass
ich etwas machen muss … es soll alles rund um den Sniper testen, wirklich ALLES, mit dem Ziel, dass er perfekt funktioniert".

**Passiv:** kauft nichts, verkauft nichts, ruft keine geschützte Funktion auf, ändert AHSentinel nicht (nur lesen und
`hooksecurefunc` = nachher mithören). Keine Spielernamen (Systemmeldungen nur als Art, z. B. "gewonnen").

Installieren: `GSSniperLog.zip` entpacken nach `Interface/AddOns` (Ordner `GSSniperLog`). Danach normal spielen (snipen,
entzaubern, verkaufen, Post holen). `/gssl` zeigt den Stand, `/gssl aus|an|leeren`. Beim Ausloggen oder `/reload` geht das
Ergebnis (`GSDIAG1|GSSniperLog|…`) mit dem Uploader nach `testberichte/diagnose/GSSniperLog/`.

Schreibt mit (je Zeile Uhrzeit auf 0,1 s):
- SUCHE/ERGEBNIS: jede Suche, Antwortzeit des Servers, Angebote unter dem Max-Preis des Ziels, günstigstes Angebot
- WEG: Angebot unter Max verschwand ohne unseren Kauf (erst nach 2 vollständigen Ergebnissen, Teilergebnisse zählen nicht),
  wie lange es sichtbar war
- KAUF-GESENDET / KAUF-OK / KAUF-OFFEN: jeder gesendete Kauf (PlaceBid, Waren), offene Käufe beim Senden, doppelt gesendet,
  Reaktion seit erstem Sehen, Antwortzeit, keine Bestätigung in 30 s, späte Bestätigung
- FEHLER / AH-FEHLER / DROSSEL: "Interner Auktion-Fehler", AH-Fehlercodes, Drossel-Ereignisse des Servers
- GOLD: jeder Gold-Abgang/-Zugang mit Zusammenhang (AH Kauf, Einstellgebühr, Post, Händler, sonst)
- AHS-ZÄHLER / AHS-STATUS / PAUSE: Zähler von AHSentinel je Ziel, jeder Statuswechsel mit Dauer, Lücken ohne Sniper-Suche
- BILD: Frames > 100 ms bei offenem AH; MINUTE: Zusammenfassung je Minute
- Zusammenfassung: Erfolg je "offene Käufe beim Senden" (0/1/≥2), Gold bestätigt gegen Gold-Abgang, AHSentinel-Zähler

Test: `lua5.1 shared/messtest/GSSniperLog/test_gssniperlog.lua shared/messtest/GSSniperLog/GSSniperLog.lua` – 5 Szenario-Läufe
(normaler Ablauf, doppelt/ohne Antwort/spät/Waren, weggeschnappt/Teilergebnisse, Pausen/Status/Gold-Zusammenhang/Vollscan,
Robustheit ohne AHSentinel/AH-API, Begrenzungen, Befehle, globale Namen) + 5 Zufallsläufe à 20000 Ereignisse:
92/92 OK, 0,03 ms je Ereignis. addon_check: OK (nur Hinweise Sprache/GoldSentinelGame – Messwerkzeug, nicht veröffentlicht).

### GSSniperLog 1.1 (15.11. 14:40, nach dem ersten echten Protokoll)
Korrigiert: Uhrzeit monoton (Zehntel passten nicht zur Sekunde), Pausen nur bei offenem AH (Briefkasten-Gang zählte als 31 s
Pause), Gold bei offenem AH vor "Post" (MAIL_CLOSED fehlt manchmal), offene Käufe ohne die nach 30 s unbeantworteten,
AUCTION_CANCELED als Server-Ereignis (kommt bei jedem eigenen Kauf). Neu: Drossel-Ereignisse und AH-Fehler nennen die letzte
Anfrage (Suche/Kauf) und wie lange her; AH-Fehlercodes mit Wort (10 = Datenbankfehler = "Interner Auktion-Fehler").
Tests: 6 Szenario-Läufe + 5 Zufallsläufe, 100/100 OK, 5× wiederholt.
