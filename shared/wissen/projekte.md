# Projekte – Gehirn der Prüf-Sitzung (Stand 13.11.2026, 22:25)

Auf Wunsch des Nutzers (13.11. 22:09): wichtige und weniger wichtige Dinge über alle Projekte an einem Ort.
Wird bei jeder Prüfung nachgeführt (pruef-ablauf.md). Quelle für Einzelheiten: `auftraege/<Projekt>/offen-*.txt`,
`berichte/<Projekt>/`, `testberichte/`.

## Für alle Projekte gleich (WICHTIG)

- Eine Sitzung je Addon; die Prüf-Sitzung ändert keine Addons, sie prüft, beauftragt (Repo `auftraege/`) und pflegt
  `addon-check/`, `shared/`, `testberichte/`, `shared/wissen/`.
- Gemeinsame Dateien in `shared/` werden byte-gleich kopiert (Prüfung "exact"): GoldSentinelGame (v3), Test (v2), Sync,
  Markt (v2, Stand 22:20). Alte Fassungen = Warnung "veraltet".
- Grundsätze des Nutzers (13.11.): nur Ergebnisse anzeigen, nie Rechenwege (OR); Einzelheiten hinter einem Knopf statt
  in Tooltips; ruckelfrei und "pfeilschnell" sind Freigabe-Bedingung (RF/PS); jede Zahl unabhängig nachgerechnet (ZN);
  jeder Befund bekommt einen bleibenden Test; alles ins Repo.
- In Forever kommen Addon-Nachrichten über eigene Chat-Kanäle nicht an; GUILD und WHISPER gehen.
- Der Nutzer spielt Horde auf WoW Forever (Start 04.11.), unter der Woche selten, am Wochenende mehr; zwei Rechner (PC und
  Laptop), Uploader auf beiden.

## AHSentinel (Auktionshaus) – WICHTIGSTES PROJEKT

**Zweck von AHSentinel (Nutzer 13.11. 22:13): Spass am Gold verdienen – aber nicht nur.** Jede Prüfung und jeder
Auftrag wird daran gemessen, ob sich AHSentinel im Spiel gut anfühlt:
- Erfolgserlebnis: sichtbar machen, dass es sich gelohnt hat (heute verdient, Gold pro Stunde, guter Fang).
- Kontrolle und Können: den Markt verstehen, schneller und klüger sein als andere ("ein Instrument, eine Waffe").
- Kein Frust: keine falschen Zahlen, kein Ruckeln, keine Verluste durch Fehler des Addons – ein falscher Kauf verdirbt
  mehr Spass als zehn gute bringen.
- Wenig Aufwand: schnell entscheiden, wenige Klicks, Zeit fürs eigentliche Spielen (Nutzer unter der Woche wenig Zeit).
- Dazulernen: Gespür für den Markt durch klare Ergebnisse, nicht durch Rechenwege.
- Mit anderen: etwas für die Gilde tun (Marktdaten-Netz), zeigen können, was man erreicht hat.
Prüffrage bei jeder Änderung: Ist sie schnell, schlicht, verlässlich – und macht ein Erfolg sichtbar Freude?

- Stand: 0.65.116 (13.11. abends). Repo AHAnalyzerPro (privat). Nur die AHSentinel-Sitzung ändert es.
- Oberste Priorität jetzt: SN2115a Budget-Verdopplung nach "Zähler zurücksetzen"; SN2115b EINE Funktion "bester Weg"
  (Tooltip-Zeilen widersprachen sich); TS116 Sniper sucht nur beim Scrollen (belegt 21:58) -> selbsttätig suchen oder
  deutlich anzeigen; RF ruckelfrei; PS Leistungsziele (Testteil "tempo").
- Dann (dringend, nicht oberste Prio, anweisung-entscheide-13-11-abend.txt): LT Gewinn-Zeile, OR, TP "Jetzt im AH" +
  anpassender Median, PX a–e, EB Goldflüsse/Eigenbedarf/Details-Knopf, ZN Nachrechnung.
- Releaseplan danach: 0.66 Rechenkern (inkl. PX-a/b, MN1–MN5 Marktnetz mit Feed), 0.67 Rhythmus, 0.68 Markt-Reiter.
- Bekannte Messwerte: Vollscan ~250–300k Auktionen, ~6'200 Items; ReplicateItems-Drossel ~15–20 Min. je Client;
  Restzeit-Stufen 1 < 30 Min., 2 30 Min.–2 Std., 3 2–12 Std., 4 > 12 Std.; Entzauber-Chancen grün 26–30 gemessen
  (Staub 72,7 %, Essenz 21,2 %, Splitter 6,1 %); Prognose schlecht kalibriert (98 % vorhergesagt, 31 % verkauft);
  Absatz-Schätzung ×3–×4,5 zu hoch (gemessen gilt); Entzauber-Materialpreis-Korrektur ×0,57 (Frage KF: evtl. zu streng).
- Offene Fragen an AHS: KF, LB (Lohnt-bis 0,59), Entzauber-Marge 10 % statt 41 %.
- Weniger wichtig: UI1509/UI1510 (Leer-Hinweis, leeres Testbericht-Fenster), SN-T (Testteil "sniper" fehlt in der
  Liste), EB-Kennzahlen im Details-Fenster (Rendite je Weg, gebundenes Gold, verlorene Einzahlungen, Verkaufsquote –
  Entscheid des Nutzers offen).
- Nutzer-Eigenheiten: will Optik schlicht, Entscheidungen klar; testet abends im Spiel und schickt Bilder/SavedVariables.

## GuildSentinel (Gilde)

- Stand: 0.9.37. Gilde "Glutbrüder" (Horde), im Aufbau.
- Wichtig: GA Altersfrage (5. Frage, ab 16, nette Absage, Alter nie speichern) und Werbetext "im Aufbau, alle Klassen"
  (Bericht 0.9.36 – im Client bestätigen); RP Rekrutierung in Phasen (jetzt alle Klassen, Vorgaben für raidfähig
  behalten); RV Rechtsklick-Menü mit Rängen; GV1 Einladen gesperrt (Absicht).
- Offen: MN1b GoldSentinelMarkt veraltet (v1) -> v2 kopieren; MN2b Schalter zeigt nur den eigenen Wert.
- Weniger wichtig: Befehlsliste (CH/BL) wie bei den anderen.

## ProfessionSentinel (Berufe)

- Stand: 0.9.44. Rezeptdaten-Update läuft täglich als geplante Aufgabe (nur Daten, kein Code).
- Wichtig: GoldSentinelMarkt neu kopieren (v2); PM1–PM7 Marktwissen fürs Herstellen.
- WARTET AUF ENTSCHEID DES NUTZERS: BL3/BL4 – Befehlsliste über dem Chat als gemeinsame Datei
  `shared/GoldSentinelCmdHint.lua` (statt fünf eigener CmdHint.lua)? Empfehlung der Prüf-Sitzung: ja (einheitlich,
  einmal prüfen, weniger Fehler).
- Weniger wichtig: Neuaufbau im Client bestätigen, Speicher nahe an der Grenze (T145), An/Aus-Meldung ohne Sprachtabelle.

## BuffSentinel (Buffs)

- Stand: 0.9.18 (Markt v1 -> v2 kopieren). Offen: BP-2026-11-13-1 Schamane Imbue + Waffen-Totem gleichzeitig (Blizzard-
  Hotfix), TU1-Rest. Weniger wichtig: MN3a Markt-Zeile zeigt nur eigenen Schalter.

## ThreatSentinel (Bedrohung)

- Stand: 2.5.11 (Markt v1 -> v2 kopieren). Ohne eigenes GoldSentinelSync: Marktdaten nur mitlesen, nicht teilen.
- WARTET AUF ENTSCHEID DES NUTZERS: gemeinsamer Sync (GoldSentinelSync) ja/nein – ohne ihn teilt ThreatSentinel weder
  Testberichte noch Marktdaten, wenn kein anderes Addon Sync mitbringt.
- Weniger wichtig: Offline-Routine nimmt keine ZIP; T-MN2 kann echte Marktdaten beschreiben.

## LevelPilot (Leveln/Wegführung)

- Stand: 3.12.28 (Datei in download/ unter anderem Namen). Offen: MK1 Markt v2 kopieren; GR1 Grundregel verletzt
  ("Quest fertig, aber kein Abgabe-Schritt"); SP1 Speicher bis 125 MB (messen); TU9 Offline-Routine fehlt; Wegpunkte und
  Strassen (Anweisung gilt weiter).

## RaidMaster (Raid-Addon + Uploader)

- Stand: 3.0.25, Uploader 2.3.6 (PC teils noch älter – erst aktualisieren, wenn /uploader die neueste nennt).
- Wichtig: Uploader bringt Testberichte, Diagnosen und jetzt Marktdaten (GSMARKT1) ins Repo/zum Bot; MN1-K Markt v2.
- Weniger wichtig: MN-T Testroutine verändert Markt-Zähler; U3 unbekannte Markt-Zeilen still verworfen; TU-Rest.

## Discord (Bot + Gilden-Discord)

- Stand: Bot 1.5.131 auf eigenem Server; Testberichte-Abholung per GitHub-Workflow (alle ~30 Min., manuell anstossbar).
- MN7 Sammelstelle gebaut (Absatz als Spanne, Doppelte je Fraktion+Zeit, Wochenbericht testberichte/markt/).
- MN8: Blizzard-API kennt Forever nicht (gemessen 13.11.) -> Spieler-Scans sind die einzige Marktquelle.
- Weniger wichtig: D-MN7a "Quellen" zählt Webhooks statt Spieler; D-MN7c–f (Fälschung/Masse, Wochenzählung, verlorene
  Scans, Grenzen); D-T1 Tests prüfen Quelltext als Text.

## Prüf-Sitzung selbst

- Geplante Aufgaben: Nachprüfung (trig_01Lt3KGobLke4QRdswTBqFfP), AHSentinel Markt-Überwachung (Mo 05:47), Blueposts
  (07:38/21:38), Rezeptdaten-Update, Raids und Taktiken.
- Messwerkzeug GSMesstest 5.1 (`shared/messtest/`, A3 Markt komplett).
- Termine: ab 17./18.11. Mindest-Einzahlung 1c (Bluepost) prüfen; T240-Rechnung muss dann stimmen.
