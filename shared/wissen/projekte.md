# Projekte – Gehirn der Prüf-Sitzung (Stand 13.11.2026, 23:35)

Auf Wunsch des Nutzers (13.11. 22:09, nochmals 23:27: "merke dir alles über die anderen Addons, damit du nichts vergisst
oder übersiehst – immer nach Prio handeln"): alle Projekte an einem Ort, je Projekt der Stand und die offenen Punkte
NACH PRIORITÄT. Bei jeder Prüfung nachführen (pruef-ablauf.md A Schritt 8). Einzelheiten: `auftraege/<Projekt>/offen-*.txt`,
`berichte/<Projekt>/`, `testberichte/`. Was der Nutzer im Spiel tun muss: `auftraege/weckliste.txt`.

## Für alle Projekte gleich (WICHTIG)

- Eine Sitzung je Addon; die Prüf-Sitzung ändert keine Addons, sie prüft, beauftragt (Repo `auftraege/`) und pflegt
  `addon-check/`, `shared/`, `testberichte/`, `shared/wissen/`. Projekte prüfen sich nicht selbst ("umgesetzt, zur Prüfung").
- Gemeinsame Dateien in `shared/` byte-gleich kopieren (Prüfung "exact"): GoldSentinelGame (v3), Test (v2), Sync, Markt (v2,
  Stand 22:20), NEU CmdHint (v1, 13.11. 23:35, Befehlsliste beim Tippen). Alte Fassungen = Warnung "veraltet".
- Grundsätze des Nutzers: nur Ergebnisse, nie Rechenwege (OR); Einzelheiten hinter einem Knopf; ruckelfrei und
  "pfeilschnell" sind Freigabe-Bedingung (RF/PS); jede Zahl nachgerechnet (ZN); jeder Befund bekommt einen Test; nur
  Gesichertes anzeigen; Begriffe wie im Spiel (EB-NAME); alles ins Repo; bei "go" sofort handeln und pushen.
- Plan des Nutzers (23:26): "Wir werden bald Addon für Addon auseinandernehmen und perfektionieren" – AHSentinel zuerst.
- Client-Tests aller Addons ZURÜCKGESTELLT (23:19), nicht vergessen: Liste in weckliste.txt "Für den Nutzer".
- In Forever kommen Addon-Nachrichten über eigene Chat-Kanäle nicht an; GUILD und WHISPER gehen.
- Nutzer: Horde auf WoW Forever (Start 04.11.), unter der Woche selten, Wochenende mehr; PC und Laptop, Uploader auf beiden.

## AHSentinel (Auktionshaus) – WICHTIGSTES PROJEKT, wird als Erstes perfektioniert

**Zweck (Nutzer 13.11. 22:13): Spass am Gold verdienen – aber nicht nur.** Erfolgserlebnis sichtbar, Kontrolle und Können
("ein Instrument, eine Waffe"), kein Frust (falsche Zahlen, Ruckeln, Fehlkäufe), wenig Aufwand, Dazulernen ohne Rechenwege,
etwas für die Gilde. Prüffrage: schnell, schlicht, verlässlich – und macht ein Erfolg sichtbar Freude?

- Stand: 0.65.119 (DE30 Entzaubern ≥ 30 %, im Code geprüft; Client offen). Repo AHAnalyzerPro (privat).
- PRIO (Reihenfolge laut offen-ahsentinel.txt Kopf):
  1. TB119 Sniper-Test 23:06: 278 echte Addon-Nachrichten im Test / Sync-Warteschlange 278 (Ursache je Präfix zeigen),
     Sniper 164 ms, T613 zu streng, Speicher AHSentinel 240 MB Grundstand (GC-Ruckler), Vollscan-Einlesen 159 ms.
  2. TB118 Tempo-Lauf: Markt-Reiter 1083 ms (Ziel 50), Laden 494 ms (Ziel 100), Vollscan-Messung über Reload.
  3. RF/PS Rest (ruckelfrei, pfeilschnell), SN2115/TS116 im Client bestätigen.
  4. CH-G gemeinsame Befehlsliste (shared/GoldSentinelCmdHint.lua v1) – AHSentinel als ERSTES Addon (Nutzer 23:26).
  5. EB Goldflüsse + Details-Fenster (Gesamt, Handel pro Stunde, EB-DET: Rendite je Weg, Anzahlung verfallen,
     Verkaufsquote), BH-ANZ (Anzahlung erst beim Verfallen Aufwand), EB-NAME (Client-Wort DEPOSIT).
  6. Entscheide des Abends: LT Gewinn-Zeile, OR, TP Jetzt im AH + Median, ZN, PX, SA Schnäppchen-Alarm, HK Kette.
  7. Später: I3 Vermögensverlauf, I4 Offline-Plan; I6-M nur messen. NEIN: I1, I2, I8.
- Messwerte: Vollscan ~305k Auktionen, ~6'200 Items, Drossel ~15–20 Min.; Restzeit-Stufen 1 <30 Min., 2 30 Min.–2 Std.,
  3 2–12 Std., 4 >12 Std.; Prognose 32 % zutreffend (98 % vorhergesagt); Entzauber-Käufe 42 % mit Gewinn, 55 % Beute
  unter Kaufpreis (-> DE30); Absatz-Schätzung bis ×5 zu hoch; Index 7 Tage −27 bis −32 %.
- Bleibt offen (weniger wichtig): UI1509/UI1510, SN-T, KF/LB-Fragen, Tooltip.lua:600 Kommentar.

## GuildSentinel (Gilde)

- Stand: 0.9.38 (Markt v2 byte-gleich, geprüft).
- PRIO: 1. GA Altersfrage + Werbetext im Client bestätigen (Nutzer). 2. RP Rekrutierung in Phasen, RV Rechtsklick-Menü.
  3. MN2b Schalter-Anzeige. 4. Später: CH-G gemeinsame Befehlsliste (nach AHSentinel). GV1 Einladen gesperrt = Absicht.

## ProfessionSentinel (Berufe)

- Stand: 0.9.45 (Markt v2 byte-gleich, An/Aus, TodayCrafts "safe"). Rezeptdaten-Update täglich (nur Daten).
- PRIO: 1. HK-P Herstellungs-Kette (nur Gesichertes, Feld "safe"). 2. PM1–PM7 Marktwissen. 3. BL3/BL4 Befehlsliste:
  ENTSCHIEDEN 23:26 -> gemeinsame Datei, aber erst NACH AHSentinel (CH-G). Analyse: professionsentinel-analyse.md.
- Weniger wichtig: Neuaufbau im Client, Speicher nahe Grenze (T145), An/Aus-Meldung ohne Sprachtabelle.

## BuffSentinel (Buffs)

- Stand: 0.9.20 (Markt v2, BP-2026-11-13-1 Messung vorbereitet, TU1-Rest, MN3a).
- PRIO: 1. MN-S T178 erweitern -> 0.9.21 (Korrektur in v2 belegt). 2. BP-2026-11-13-1 Teil 2 nach Client-Messung
  (Schamane Waffe). 3. Später: CH-G. Client-Tests: weckliste.

## ThreatSentinel (Bedrohung)

- Stand: 2.5.12 (Markt v2 byte-gleich). Ohne eigenes GoldSentinelSync: Marktdaten nur mitlesen, nicht teilen.
- WARTET AUF ENTSCHEID DES NUTZERS: gemeinsamer Sync ja/nein (Empfehlung ja).
- Später: CH-G (hat eigene CmdHint.lua, nur HookScript).

## LevelPilot (Leveln/Wegführung)

- Stand: 3.12.29 (Markt v2, MK1). Wartet nicht mehr: Anweisung 23:25 -> 3.12.30 = GR1 (a)+(b), SP1 messen, TU9.
- Danach wartend: Wegpunkte (Wegdaten-Exporte), Punkt 15 nur auf Kommando. Später: CH-G.

## RaidMaster (Raid-Addon + Uploader)

- Stand: Addon 3.0.26 (Markt v2 byte-gleich), Uploader 2.3.7 (MN6b anonyme Quelle, U3).
- PRIO: 1. T90 unter enUS in der eigenen Nachbildung klären. 2. Client-Test durch den Nutzer (weckliste). 3. Später: CH-G.

## Discord (Bot + Gilden-Discord)

- Stand: Bot 1.5.131; Testberichte-Abholung per GitHub-Workflow (~30 Min., manuell anstossbar).
- PRIO: 1. FRAGE DES NUTZERS 23:20: Datenvolumen des Bots grösser? Grenzen, Einflüsse, Empfehlung (nur Bericht).
  2. D-MN7a Feld "quelle" lesen (Uploader 2.3.7 liefert es), D-UP1 /update. 3. D-MN7c–f, D-T1.
- MN8: Blizzard-API kennt Forever nicht -> Spieler-Scans sind die einzige Marktquelle.

## Prüf-Sitzung selbst

- Takt: bei jeder Nachricht des Nutzers + alle 5 Min. bei intensiver Arbeit (Nutzer 22:36); nur Neues melden.
- Geplante Aufgaben: Nachprüfung (5× täglich), AHSentinel Markt-Überwachung (Mo 05:47), Blueposts (07:38/21:38),
  Rezeptdaten-Update, Raids und Taktiken.
- Gebaut: GSMesstest 5.1, GoldSentinelMarkt v2, GoldSentinelCmdHint v1 (Test 30/30).
- Termine: ab 17./18.11. Mindest-Einzahlung 1c (Bluepost) prüfen. Später: nachrechnung.py (ZN), sobald AHS GSZAHL1 liefert.
- Offen beim Nutzer: ThreatSentinel gemeinsamer Sync (ja/nein).

## Ideen-Speicher (offen für alles – Nutzer 13.11. 22:13: "versuche neue Ideen zu entwickeln")

Noch nicht beauftragt; dem Nutzer vorgelegt am 13.11. 22:15. Neue Ideen hier sammeln, Entscheide nachtragen.
- I1 Tagesziel: Spieler setzt "heute 2g", schmaler Balken füllt sich mit dem Handelsgewinn (Erfolgserlebnis).
- I2 Fang des Tages: kurze, schöne Meldung beim besten Kauf/Verkauf des Tages ("+1g 20s – bester Fang heute").
- I3 Vermögensverlauf: Gold + Lager + laufende Auktionen über Wochen als Kurve im Details-Fenster.
- I4 Wochenplan fürs Offline-Sein: vor dem Ausloggen schlägt AHS vor, was mit langer Laufzeit eingestellt werden soll
  (Preise, die 48 Std. halten; keine Flips offen lassen) – passt zum Spielrhythmus des Nutzers.
- I5 Schnäppchen-Alarm aufs Handy: Taucht ein Sniper-Ziel im Scan eines Gildenmitglieds (Marktdaten-Netz) unter dem
  Max auf, schickt der Discord-Bot eine Direktnachricht – auch wenn man selbst nicht im AH steht.
- I6 Nachfrage-Wellen: aus Serveralter und Stufenverteilung der Gilde/des Netzes vorhersehen, wann Leveling-Güter
  gefragt sind (z. B. Stufe-40-Reittier-Welle -> Gold knapp, Taschen/Tränke gefragt).
- I7 Herstellungs-Kette mit ProfessionSentinel: "Material kaufen -> herstellen -> verkaufen" als ein Vorschlag mit
  Gewinn/Stunde, nur wenn alle Teile geprüft lohnen.
- I8 Gilden-Bestenliste (freiwillig): Handelsgewinn der Woche im Gilden-Discord (Erfolge teilen).

Entscheide 13.11. 22:20: I1 nein · I2 eher "bester VERKAUF des Tages" (Rückfrage beantwortet, Entscheid offen) ·
I5 JA, aber IM SPIEL statt aufs Handy und nur GESICHERTE Treffer (Daten ≤ 60 s alt, 22:22) ("nicht irgendein Mist") -> Auftrag SA · I7 JA,
"simpel und einfach, ohne grossen Schnickschnack" -> Auftrag HK · I8 nein ("bringt nur Neid").
Entscheide 13.11. 23:23: I2 NEIN · I3 SPÄTER (nach EB/BH-ANZ) · I4 SPÄTER (erst wenn die Verkaufs-Prognose stimmt) ·
I6 ERST MESSEN (nur Daten sammeln, nichts anzeigen, bis belegt) -> Auftrag I6-M.
