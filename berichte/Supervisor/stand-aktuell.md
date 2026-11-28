# Stand Supervisor – 28.11.2026 06:42 (Nutzer testet im Spiel, alle 3 Projekte arbeiten)

## Gerade in Arbeit
- Warte nicht: LP-Ingametest 3.13.33 kalt läuft beim Nutzer (/lp testroutine kalt -> /reload -> 60 s -> alles) -> T261 "erstes" < 1000 ms auswerten.
- Angenommen heute: AHS 0.65.428/429/430; LP 3.13.32/33; PS 0.9.99 (in download/), 0.9.100 (Spieltest offen, dann PS-DL).

## Nächste Schritte (Reihenfolge)
1. Bei jedem "repo": pull, Berichte prüfen, addon_check, annehmen/ablehnen, push + nachprüfen, Workflow ansehen.
2. AHS (HOCH zuerst): AHS-BH-REN2 (Rendite Entzauber-Kosten 0); dann 2b: SN-SORT1 (Sniper-Liste unsortiert nach Varianten), PROF-SP1
   (Gewinn gesamt ≠ Stück×Menge, Seite 2 doppelt), CHAT-PROFIT Zahl 14 vs 22 (nicht bestanden), DE-WID1, MKT-WID2 (Buchband über 25 %-Grenze,
   Schredderanleitung), SN-LB1, CF-1 (CurseForge-Kommentar Preisverlauf-Graph, Antworttext nur mit OK des Nutzers), Eigenbedarf-Buchung.
   Masterplan v2: Schritt 2 (T459 Nachlauf-Speicher, SP1) -> 2b -> R1–R7 -> Abnahme -> 0.66.0.
3. LP: T155 HOCH (16,99 ms im Spiel, Ziel < 16), T261 kalt; dann Wegnetz mit Zonen von B (Entscheid 05:35); LP-UI-AC1.
4. PS: Frage an Nutzer offen: Einzel-Einkauf aus Rezeptansicht (UI.BuyForRecipe) Eigenbedarf ja/nein. Rest-Befunde PS-UI-REZ1, PS-GOLD-WID, PS-LVL-EINH.
5. Offizier B: kein Upload mit 2.3.30 bisher (stand.json prüfen). Markt-Tabelle: Zweig nachlieferung-rechner-b mitgeben.

## Offen beim Nutzer
- Spieltests: AHS Restzeit-Spalte bei Ausrüstung, Gift-Tooltip "ruht · gebunden", API-LANGSAM-Zeilen, Ziel löschen mit offenem Treffer,
  echter Kauf Ältestenhandschuhe (Gold −14s); PS 0.9.99 Händler auf/zu + Lehrerzeile (Magiestoffballen?); PS 0.9.100 Tooltip Wollrobe + Plan->Sniper;
  /lp protokoll (26 Auffälligkeiten).
- Idee für später (Nutzer 28.11. 05:36): Gilden-Homepage (mit Spielernamen nur in eigenem Repo). Nicht begonnen.
- Frage "kleine KI aus dem Rechenkern" (seit 14.11.). 09.12. 07:00: Aufgabe "Raids und Taktiken" wieder einschalten.

## Entscheide des Nutzers seit letztem Stand (in entscheide.md)
- 28.11. 05:03 Sniper: eine Raste kauft alle Angebote einer Ware (Ausrüstung: 1 Stück je Raste). 05:35 LP-Wegnetz erst mit Haralds Zonen.

## Wichtig zu wissen
- CurseForge 06:02 (Homezugriff, berichte/Supervisor/2026-11-28-0602-curseforge-meldungen.txt): AHS 34 Beiträge, 1 offen (CF-1); GS 0 Kommentare.
  Browser für CF: nur über Homezugriff (hier kein Browser verbunden).
- AHS-SN-FIND1 Ursache: MakeItemKey liefert bei Ausrüstung Itemstufe -> 0.65.430 liest alle Varianten-Schlüssel (max 8).
- LP-Ablage (Umweg) gilt je Zone über Wegnetz-Kennung, nicht über Version – richtig so; kalt nur über /lp testroutine kalt.
- DL-ABN: download/ nur angenommene + im Spiel geprüfte Versionen; AHS/GS CF 18:00. SH-M1 (B) mit nächster shared/-Änderung.
- Repo öffentlich: keine Spieler-/PC-Namen (Offizier A/B).
