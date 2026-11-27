# Stand Supervisor – 27.11.2026 21:20

## Gerade in Arbeit
- Nichts Laufendes. Warte auf neue Versionen: PS (PS-SK2 Magiestoffballen ohne Stufe im Plan 110–150), LP (T155 16,89 ms / T136 Zentrale),
  AHS-Kleinigkeiten (AHS-SN-CAN1, Wechsel kurz vor Raste, Rest-Speicher AHS-API1).

## Nächste Schritte (Reihenfolge)
1. Bei jedem "repo": pull, Berichte prüfen, addon_check, annehmen/ablehnen, push + nachprüfen, Workflow ansehen.
2. Offizier B: Uploader 2.3.30 am 27.11. 20:54 per Bot + Anleitung bekommen (Log). Sein Rechner lädt seit 22.11. nicht (stand.json uploader leer) –
   nach seinem ersten Upload mit 2.3.30 prüfen. Offizier A seit 15:31 auf 2.3.30. BS-M1-b Messdaten Offizier A auswerten, sobald da.
3. CurseForge: AHS 0.65.423 als Hotfix 21:02 hochgeladen (Entscheid 21:00), GS 0.9.66 18:00. Seiten auf curseforge.com + Kommentare noch nicht gelesen
   (Webzugriff braucht Freigabe/verbundenen Browser) – beim nächsten Mal nachholen.

4. Daten Rechner B (Entscheid 21:47): Daten-Repo-Zweig nachlieferung-rechner-b-2026-11-27 – beim nächsten Markt-Tabellen-Lauf als zusätzliche
   AHSentinel.lua mitgeben (markt_tabellen.py nimmt mehrere Stände, Punkte ohne Doppelte); AHS/LP-Aufträge 21:52.
5. Masterplan AHS v2 freigegeben 21:21 – Inventur-Bericht von AHS prüfen (Stichproben im Code).

## Offen beim Nutzer
- 09.12. 07:00 Erinnerung: Aufgabe "Raids und Taktiken" wieder einschalten.

## Entscheide des Nutzers seit letztem Stand (alle in entscheide.md 27.11.)
- 20:58 announce/: je Addon nur die 3 neuesten ZIPs + stabile Version (DC-ANN2, umgesetzt: 758 -> 50 MB).
- 21:00 AHS 0.65.423 sofort als Hotfix auf CurseForge (Ausnahme DL-ABN Punkt 4).

## Heute Abend erledigt
- DC-UPL1: Bot hing – Ursache Speicher (ganze Repo-ZIP ~900 MB in den Speicher, 1720 MB von 2 GB), DNS-Fehler nur Folge. Bot 1.5.202/1.5.203 angenommen:
  Download auf Platte, nur Nötiges entpacken, Reste weg (UPL2), Netz 45 s statt 300 s (UPL3), ~100 MB statt 0,9 GB je Update (UPL4).
- SN-Z4 (AHS 0.65.423): Fenster wechselt zwischen Zielen (Rotation 3 s), Knopf frei wenn nicht kaufbar; Kauf im Spiel belegt (Kapuze, −12s97,
  Briefkasten). ABGENOMMEN 21:09. AUCTION_CANCELED nach Kauf = eigener Kauf (NIEDRIG).
- PS 0.9.96 PS-SK1: "LEHRER Lernstufen gelesen 28", Plan zeigt Skill 110/120/140 statt "?" – bestätigt; neu PS-SK2.
- AHS 0.65.422 AHS-API1: Ursache (1016× CorrectionFor je Entzauber-Kauf) behoben, Werte gleich; im Spiel 20:55 WorthUpTo 4,7 ms (nur 1 Zeile, cache:warm).
- PC des Nutzers: Uploader 2.3.30, Testversionen an.

## Wichtig zu wissen
- SH-M1 (Entscheid 21:16: B): DiagLines-Verbesserung mit der NÄCHSTEN nötigen shared/-Änderung mitnehmen.
- DL-ABN: download/ nur angenommene Versionen; AHS/GS CurseForge 18:00 (Ausnahme nur auf Entscheid).
- announce/: ZIPs werden automatisch auf 3 + stabile gekürzt (Workflow "Announce aufräumen"), .md bleiben.
- Repo öffentlich: keine Spieler-/PC-Namen (Offizier A/B). Prüfwerkzeuge chatprobe.py/rek1probe.py nur in dieser Sitzung.
