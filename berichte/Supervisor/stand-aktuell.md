# Stand Supervisor – 27.11.2026 17:00 (Übergabe für den Abend am PC)

## Gerade in Arbeit
- Wartet auf Uploads um 18:00: GuildSentinel 0.9.66 (GS-CF3) und AHSentinel 0.65.422 (freigegeben 16:58, md5 0acf340e…).
- Erinnerungen dieser Sitzung (gestellt): 18:05 GS download/ + Workflow, 18:10 AHS download/ (0.65.413 weg) + Workflow, 18:20 CurseForge beide + Kommentare.
  Sieht eine neue Sitzung sie nicht: von Hand prüfen (download/, `gh run list --workflow "Addon-Prüfung" -L 3`, curseforge.com/wow/addons/ah-analyzer-pro und /guildsentinel).

## Nächste Schritte (Reihenfolge)
1. Bei jedem "repo": pull, neue Berichte prüfen, addon_check, annehmen/ablehnen, push + nachprüfen, Workflow ansehen (E-Regel 27.11.).
2. 18:05–18:20 Kontrollen oben; Ergebnis in offen-guildsentinel.txt / offen-ahsentinel.txt.
3. Ingametests des Nutzers am PC auswerten (je einer, nacheinander):
   a) PS 0.9.96 PS-SK1: Schneiderei-Lehrer, Filter "alle", /ps protokoll -> "LEHRER Lernstufen gelesen", kein "Skill ?" mehr bei Lehrer-Rezepten.
   b) AHS 0.65.422 AHS-API1: wie 15:44 -> keine Zeile API-LANGSAM über 4 ms, kein "DE Iteminfo ×1000" (bestanden = Abnahme).
   c) Uploader PC: einmal j (2.3.30), Addons-Testversionen-an.bat, Neustart -> stand.json "uploader" 2.3.30 prüfen.
4. Neue Versionen erwarten und prüfen: LP T155 (16,89 ms, Ziel < 16) + T136 Zentrale (57,5 ms mit GC −110 MB); AHS Rest-Speicher ("DE tatsächlich",
   Mat Leiter, ≤ 50 KB); PS-P2/PS-SK1-Folgen.
5. Offiziere: Uploader 2.3.30 (A: j; B: Handinstallation + daten_config.json-Nachtrag). stand.json beobachten; dann BS-M1-b Messdaten Offizier A.

## Offen beim Nutzer
- Ingametests 3a–3c (PC, heute Abend).
- Entscheid SH-M1 (A jetzt / B gebündelt, empfohlen B).
- 09.12. 07:00 Erinnerung: Aufgabe "Raids und Taktiken" wieder einschalten.

## Entscheide des Nutzers seit letztem Stand
- 16:55 Frage "0.65.422 freigegeben für Curse?" -> Supervisor: ja (angenommen = DL-ABN), Upload 18:00, AHS-Sitzung hat die Anweisung (16:57).

## Heute geprüft (Kurz)
- AHS 0.65.422 ANGENOMMEN 16:55: Ursache AHS-API1 = Ln:BuyStats rief D:CorrectionFor je Entzauber-Kauf (1016× für 7 Items) -> jetzt je Item einmal;
  Nachbau 40,6–42,6 ms -> 1,6–2,2 ms, Werte gleich (149 Items), FULL 356/67 wie 0.65.421. NIEDRIG: liegengebliebener D.matCache ohne job schaltet Ersparnis ab.
- LP 3.13.29 Ingametest 15:47: bester Lauf (57,5 ms längstes Bild, ganzes Bild 70 statt 150 ms); offen MITTEL T155, T136.
- GS 0.9.66 + BS 0.9.69 abgenommen 11:18/11:19. PS 0.9.95/0.9.96 angenommen. ST1 (Spieler-Texte) alle 7 angenommen.

## Wichtig zu wissen
- DL-ABN: download/ nur angenommene Versionen (Uploader installiert automatisch bei allen Mitspielern); AHS/GS zusätzlich nur um 18:00 (CurseForge).
- addon_check: download/ < announce/ = WARNUNG (gewollt). Workflow war 11:07–11:39 rot durch neue Regel -> E-Regel: nach jeder neuen Regel Workflow prüfen.
- RM: Uploader-Versionen nur über Zweig pruefung/uploader-<V>. Repo öffentlich: keine Spieler-/PC-Namen (Offizier A/B).
- Prüfwerkzeuge /home/claude/chatprobe.py, rek1probe.py nur in dieser Sitzung (nicht im Repo).
