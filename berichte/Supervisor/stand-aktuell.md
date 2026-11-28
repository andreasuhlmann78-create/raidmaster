# Stand Supervisor – 28.11.2026 05:36 (alle 3 Projekte arbeiten)

## Gerade in Arbeit
- Nichts Laufendes. AHS, LP, PS um 05:31 am Arbeiten.
- Angenommen heute: AHS 0.65.428 (UI-DD1), 0.65.429 (SN-DEL1 a, PS-EIG1 AHS-Seite, CHAT-PROFIT, TXT-CUT); PS 0.9.99 (P3, SK2-b, darf nach download/).
- LP Ingametest 3.13.31 05:11: T261 699 ms aber WARM (Ablage) -> kalt belegen; NEU T155 FEHLER 18,4 ms/Planung HOCH; längstes Bild 91 ms T401.

## Nächste Schritte (Reihenfolge)
1. Bei jedem "repo": pull, Berichte prüfen, addon_check, annehmen/ablehnen, push + nachprüfen, Workflow ansehen.
2. LP: T155 HOCH, T261 kalt, T401 91 ms; dann Wegnetz mit Zonen von B (Entscheid 05:35); LP-UI-AC1 NIEDRIG.
3. AHSentinel 0.65.428 (AHS-UI-DD1) angenommen 05:08 – Spieltest beim Nutzer offen (Seltenheit über Liste, schliesst, Restzeit gefüllt; Sniper/Preisverlauf).
   Offen bei AHS: AHS-BH-REN2 HOCH (Rendite: Entzauber-Kosten 0), AHS-SN-DEL1 MITTEL (nur a: Löschen verwirft offene Treffer/"1 offen"),
   AHS-SN-LB1 NIEDRIG (Text "+60 %"), Masterplan v2 Schritt 2 (Stabilität/Vollscan) -> 2b (Anzeige) -> R1–R7 -> Abnahme -> 0.66.0.
4. ProfessionSentinel 0.9.98 angenommen + in download/. Befunde PS-P3, PS-UI-REZ1, PS-GOLD-WID, PS-LVL-EINH, PS-TT-RECH, PS-TT-EINH, PS-AHS-EIG1, PS-SK2-b offen.
5. Offizier B: noch kein Upload mit Uploader 2.3.30 (stand.json DESKTOP-… prüfen). Verdacht: daten_config.json fehlt im neuen Ordner.
   Upload 27.11. 21:31 gesichert im Daten-Repo-Zweig nachlieferung-rechner-b-2026-11-27.
6. Markt-Tabelle: AHSentinel.lua aus Zweig nachlieferung-rechner-b mitgeben (Entscheid 27.11. 21:47); Bot-Tagesdateien D-KERN1 prüfen.
7. CurseForge-Seiten/Kommentare AHS 0.65.423 / GS 0.9.66 noch nicht gelesen.

## Offen beim Nutzer
- Spieltest AHS 0.65.428 (Seltenheit); LP-Protokoll; PS-Ingametests.
- Frage "kleine KI aus dem Rechenkern" (seit 14.11., keine Eile). 09.12. 07:00: Aufgabe "Raids und Taktiken" wieder einschalten.

## Entscheide des Nutzers seit letztem Stand
- 28.11. 05:35 LP-Startwegnetz: erst Haralds Zonen (B) ins Werkzeug, neu messen, dann EINE Version (Route ALT/NEU: Konto +0,2 %, neuer Spieler −2 %).
- 28.11. 04:55 Anzeige-Befunde AHS als Schritt 2b im Masterplan (nichts vergessen).
- 28.11. 05:03 Sniper: eine Raste kauft ALLE Angebote des Treffers, solange Gold reicht – gewollt (in entscheide.md).
- Nutzer 05:01: Treffer Wollstoff/Öl kamen VOR dem Löschen -> AHS-SN-DEL1 von SEHR HOCH auf MITTEL korrigiert.

## Wichtig zu wissen
- LP erkennt den Nutzer per BattleTag als Entwickler (LP:IsDev) – /lp testroutine ohne Dev-Schalter.
- Balken "Distanzwaffe/Waffenhand 0.0" im Bild stammen aus keinem GoldSentinel-Addon (alle announce-ZIPs durchsucht).
- Entzauber-Tabelle AHS (Disenchant.lua:47, iLvl 26–30 Seelenstaub/Gr. Astralessenz/Gr. gleissender Splitter) nachgerechnet, stimmt.
- DL-ABN: download/ nur angenommene Versionen; AHS/GS CF 18:00. SH-M1 (B) mit nächster shared/-Änderung.
- Daten-Repo main wird überschrieben – Nachlieferungen nur als eigener Zweig (mit OK des Nutzers).
- Repo öffentlich: keine Spieler-/PC-Namen (Offizier A/B).
