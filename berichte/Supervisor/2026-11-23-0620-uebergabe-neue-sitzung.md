# Übergabe Prüf-Sitzung (Supervisor) – 23.11.2026 06:20

Für die neue Sitzung im Projekt «Addonprüfer». Alles Massgebliche steht im Repo; diese Datei ist der Einstieg.

## Zuerst lesen
1. `CLAUDE.md` (Direktiven: Perfektion, alles ins Repo + Ankunft prüfen, nicht warten, nur Deutsch, Referenzseite goldgoblin).
2. `shared/wissen/entscheide.md` (neueste oben, viele vom 21./22.11.).
3. `shared/wissen/pruef-ablauf.md` Abschnitt A, `wirtschaft-forever.md`, `buchhaltung.md` (Dauerregel Post-Scan), `referenz-goldgoblin.md`.
4. `auftraege/AHSentinel/offen-ahsentinel.txt` ab "GESAMTÜBERSICHT AHSentinel 21.11.2026 16:05" bis Ende.

## Stand der Versionen
- AHSentinel 0.65.382 (nur Discord; CurseForge zuletzt 0.65.354 – Nutzer 21.11.: "Curse nicht" bis auf Weiteres).
- LevelPilot 3.13.6. Laptop des Nutzers hat noch AHS 0.65.355 (er ist nicht am Laptop). Offiziere: AHS 0.65.354 / 0.65.360 (sollten aktualisieren).

## Offen bei der Prüf-Sitzung
- Vollständige Prüfung AHS 0.65.376–0.65.382 (Prüf-Ablauf A): PM1, ST1–ST6, CF1–CF3, BH1–BH3, VK1/VK2, N1–N3, VS1, PP1 (+Nachtrag Waren),
  SN-T/SN-Z, G1–G17, S1–S6, B1–B9. Danach CurseForge-Entscheid beim Nutzer und Antwort an Spieler A (CF-AHS-5).
- Offene AHS-Punkte: Z1 (Gewinnzeile +2s41 vs. 2s49), VL2 (wartet auf Messung VERKAUFEN-LISTE aus Upload), "/ahs stapel" Belege.
- Montag-Aufträge stehen in den offen-Dateien: AHS (BK-ESS/ESS2, R1–R7, Lua-Fehler RecipeList mit PS, P3/P6/P7/P12, Verkaufsschutz-Rest,
  Scan-Warnung, Lesbarkeit), LevelPilot (ENTSCHEID 22.11. 16:57 Sperren + Nachtrag gegnerische Orte, Berufe prüfen, Routenpause,
  Lücken/Wegqualität, 3 Bilder `auftraege/LevelPilot/bilder/2026-11-21-1253-montag-*.jpg` erst heute ansehen), ProfessionSentinel
  (Lehrer-Ränge Snarl/Saru, Sortierung Skill-Weg, Viereck, Gilde ohne Realm, Lua-Fehler), GuildSentinel (Gilde ohne Realm),
  BuffSentinel/ThreatSentinel/RaidMaster (Prüfauftrag Realm).
- Eigenes Werkzeug: `addon-check/marktanalyse/de_ketten_lehrer.py` sucht den Markt fest unter "CAMWOW EU4 Realm 6 PvP|Horde" –
  nach G1 (ein Markt je Fraktion) anpassen.
- Entwurf `berichte/Supervisor/2026-11-20-1540-entwurf-tooltips-und-messungen.txt`: T4, M5, M6 noch Entwurf.

## Offene Entscheide des Nutzers
- Rückfrage bei hoher Einstellgebühr auch in den anderen Verkaufswegen weg?
- Post-Chat: gleiche Items zusammenfassen (W3)?

## Arbeitsweise (vom Nutzer gewünscht)
- Kurz antworten, Guthaben sparen. Screenshots mit Namen nie ins Repo (verwischen oder weglassen).
- Jede Zahl nachrechnen; Vermutungen als "Verdacht, zu messen". Nie schätzen.
- Zu jedem Auftrag ein kurzer Text zum Einfügen für die Projekt-Sitzung.
- Daten-Repo `goldsentinel-daten` (Uploads: AUSPLUSLAPTOP, DESKTOP-NVITMSE = Nutzer; DESKTOP-JD5SLR5, MININT-M6UO3AL = Offiziere).
  Alle spielen auf demselben Server, das AH ist für alle dasselbe (Entscheid 21.11. 16:08).

## Ergänzung des Nutzers 23.11. 06:31 (vom alten Supervisor) – mit Prüfung durch die neue Sitzung (06:32)
1. **Geplante Aufgaben:** seit 18.11. ALLE pausiert (Guthaben). Geprüft 23.11. (list_triggers): pausiert sind Nachprüfung neuer Versionen,
   Markt-Tabellen täglich, Markt-Überwachung wöchentlich, Blueposts, ProfessionSentinel Rezeptdaten-Update, Raids und Taktiken,
   Discord und Zenial Betreuung, Gmail Werbung aufräumen. Wieder einschalten NUR auf Entscheid des Nutzers. Vorher Anleitung gegen
   die neuen Regeln prüfen. Bereits gefunden:
   - Markt-Tabellen: `addon-check/marktanalyse/markt_tabellen.py` (series_of) liest ALLE Märkte. Seit G1 (0.65.36x) heisst der Markt
     `Alle|Horde`; die alten Märkte (`CAMWOW … Realm n|Horde`, `|Horde`) liegen in den Daten noch daneben -> Doppelzählung.
     Vor dem Einschalten: nur `Alle|<Fraktion>` lesen (bzw. alte nur, wo `Alle|…` fehlt), Daten der Offiziere einbeziehen
     (Anleitung spricht noch von "beide Rechner"; es sind 4: AUSPLUSLAPTOP, DESKTOP-NVITMSE, DESKTOP-JD5SLR5, MININT-M6UO3AL).
   - `de_ketten_lehrer.py` Zeile 6 fest auf `CAMWOW EU4 Realm 6 PvP|Horde` -> auf `Alle|Horde` umstellen.
   - Nachprüfung: Anleitung nennt GuildSentinel/ProfessionSentinel-Repos mit Schreibzugriff-Wegen; Code-Repos sind nur zum Lesen.
2. **Code-Repos zum Lesen** (access "read"): ahanalyzerpro, professionsentinel, guildsentinel – nur lesen, nie ändern. ERLEDIGT 23.11.
3. **Installieren** geprüfter Versionen in den AddOns-Ordner des Nutzers nur, wenn die Sitzung mit seinem Computer verbunden ist
   (Desktop-App).
4. **CurseForge-Antworten** an Spieler gingen bisher über Claude in Chrome. Nichts posten ohne OK des Nutzers.
5. **SavedVariables auswerten:** Dateien sind Lua; mit `lua5.1` laden (`dofile`) und `AHSentinelDB` bzw. `LevelPilotDB` lesen – schneller
   als Python-Parser. (In dieser Sitzung ist lua5.1 nicht installierbar; Ersatz: lupa = Lua 5.1 in Python, gleiche Wirkung.)
