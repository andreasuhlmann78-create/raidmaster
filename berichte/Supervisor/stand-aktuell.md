# Stand Supervisor – 27.11.2026 22:45 (Nutzer schläft)

## Gerade in Arbeit
- Nichts Laufendes. Projekte arbeiten: AHSentinel (Masterplan v2 Schritt 2, Befund AHS-BP1-L), LevelPilot (T261 HOCH, LP-ML1, T150, Grundregeln 80 ms).

## Nächste Schritte (Reihenfolge)
1. Bei jedem "repo": pull, Berichte prüfen, addon_check, annehmen/ablehnen, push + nachprüfen, Workflow ansehen.
2. AHSentinel: Masterplan v2 (auftraege/AHSentinel/masterplan-ahsentinel.txt, freigegeben 21:21, Nachtrag 22:00 nach Inventur): Schritt 2 Stabilität
   (API1-Rest-Speicher, Vollscan AHS-I4/VS-121b/SP1, BP1-L Leistung von 0.65.425, S216, W2E-b, MK1, UMG1) -> R1–R7 (Reiter aktualisieren sich selbst,
   NICHT gebaut) -> Abnahme-Runde im Spiel (Prüfliste von AHS) -> 0.66.0. Daten Rechner B im Nachbau mitnutzen (Auftrag 21:52).
3. LevelPilot 3.13.30 (angenommen 22:16): Ingametest 22:11 PC – T261 Einloggen 1810 ms (soll < 1000, HOCH), T150 16,91 ms, längstes Bild 79,8 ms
   Reisen->Grundregeln; MarktLine 34 ms/3,8 MB = SH-M1 belegt -> LP-ML1 freigegeben.
4. ProfessionSentinel 0.9.97 (PS-SK2) angenommen 22:08; Ingametests beim Nutzer (Schneider- + Experten-Lehrer, Gift-Tooltip BoP, SetCraftableCount, WorthUpTo).
5. Offizier B: Uploader 2.3.30 laut Nutzer gestartet, aber KEIN Upload damit (offline seit ~22:07). Verdacht: daten_config.json fehlt im neuen Ordner.
   Nächster Upload von Rechner B: stand.json "uploader" 2.3.30, Addons aktualisiert (B hatte PS 0.9.32, LP 3.12.31, AHS ~0.65.393).
   Sein Upload 21:31 (alter Uploader) gesichert: Daten-Repo Zweig nachlieferung-rechner-b-2026-11-27 (OK Nutzer 21:44).
6. Markt-Tabelle: beim nächsten Lauf die AHSentinel.lua aus dem Zweig nachlieferung-rechner-b als zusätzlichen Stand mitgeben (Entscheid 21:47).
   Bot-Tagesdateien (D-KERN1) zuletzt 21.11. – nach Bot 1.5.203 prüfen, ob sie wieder täglich kommen.
7. CurseForge: Seiten/Kommentare zu AHS 0.65.423 und GS 0.9.66 noch nicht gelesen (braucht Browser/Freigabe).

## Offen beim Nutzer
- Ingametests PS (siehe 4), AHS Abnahme API-LANGSAM, Tooltip Blendungspulver.
- Frage "kleine KI aus dem Rechenkern" (seit 14.11., keine Eile).
- 09.12. 07:00 Erinnerung: Aufgabe "Raids und Taktiken" wieder einschalten. Raid 9.12.: Vorräte-Hinweis ab 4.12.

## Entscheide des Nutzers seit letztem Stand (alle in entscheide.md 27.11.)
- 20:58 announce/ nur 3 neueste ZIPs + stabile · 21:00 AHS 0.65.423 Hotfix CF · 21:16 SH-M1 B · 21:21 Masterplan v2 · 21:44 Daten B sichern ·
  21:47 Daten B überall nutzen · 22:37 SH-M1 bleibt B, LP-ML1.

## Heute erledigt (Abend)
- DC-UPL1–4/DC-ANN2 (Bot hing wegen Speicher; 1.5.202/1.5.203; announce 758 -> 50 MB). SN-Z4 Sniper abgenommen, Kauf belegt. AHS 0.65.423 auf CF.
- PS-SK1 im Spiel bestätigt. AHS-Inventur angenommen (fast alles gebaut, Abnahme im Spiel fehlt).

## Wichtig zu wissen
- DL-ABN: download/ nur angenommene Versionen; AHS/GS CF 18:00 (Ausnahme nur auf Entscheid).
- SH-M1 (B): GoldSentinelMarkt.DiagLines leichter (16–34 ms, 2,8–3,8 MB -> ~6,8 ms/5 KB) mit der NÄCHSTEN nötigen shared/-Änderung mitnehmen.
- Daten-Repo main wird überschrieben (Uploader unter Mindestversion verworfen) – Nachlieferungen nur als eigener Zweig sichern (mit OK des Nutzers).
- Repo öffentlich: keine Spieler-/PC-Namen (Offizier A/B). Prüfwerkzeuge chatprobe.py/rek1probe.py nur in dieser Sitzung.
