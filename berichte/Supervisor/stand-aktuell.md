# Stand Supervisor (Prüf-Sitzung, Projekt «Addonprüfer»)

## Stand 24.11.2026 20:13 · Versionen geprüft: AHS 0.65.391 · PS 0.9.83 · BS 0.9.64 · TS 2.5.30 · LP 3.13.13 · RM 3.0.43 · GS 0.9.61 · Uploader 2.3.20
Sitzung seit 23.11. 06:18. Repos: raidmaster, goldsentinel-daten (schreiben); ahanalyzerpro, professionsentinel, guildsentinel (lesen).

## Gerade in Arbeit
- AUFTRAG des Nutzers 20:32: Skelett (shared/vorlage) nachführen – Stand 18.11., fehlt: (1) Test ändert nie Livedaten (hinweis-test-keine-
  livedaten-2026-11-20, Vorbild ThreatSentinel "Livedaten (Sync-Adressbuch, Markt, gs*) unverändert"), (2) Lesbarkeit L1–L8 (hinweis-ui-lesbarkeit-
  2026-11-20), (3) Fenster ausweichen/andocken (GS-K1/BS-K1), (4) README-Regeln: Schätzen verboten, Gemeinschaftsdaten nie nach Realm, Dev-Befehle
  nur im Dev-Modus, Spieler-Funktionen nur über normale Wege. Danach Vorlage-Tests + Probe-Addon (Forever/Era, deDE/enUS) 0 FEHLER.
- Davor unterbrochen (weiter danach): Runde 20:46 (geplante Erinnerung): GS 0.9.61 auf curseforge.com sichtbar?; AHS-Ingametest 0.65.392 (PC)
  auswerten gegen AHS-CF1 a)–c); neue Versionen BS (BS-M1-b), RM (UP-AUTO1); ThreatSentinelDB.m1 (noch keine Kampfdaten, 20:30).

## Nächste Schritte (Reihenfolge)
1. AHS: Rest des Ingametests 0.65.391 (PC, Vollscan OHNE GSMesstest – entfernt 19:52): T458, T459 (wiederverwendet/neu), Vollscan zweimal, Berufe, Händler.
   Danach nächste AHS-Version (AHS-CF1: T750/T191, AHS-TR1). CurseForge AHS nur mit allen Bedingungen a)–e) inkl. Freigabe des Nutzers im Spiel.
2. BS-M1-b (Messung für alle, Uploader): Version steht aus. TS-M1-b: Kampfdaten (ThreatSentinelDB.m1) nach Instanz/Gruppe + /reload auswerten.
3. PS 0.9.83 Ingametest (Nutzer, Spiel im Vordergrund, Berufsfenster nennen -> T85). PS-I8 T269 als Nächstes bei PS.
4. UMG1 bei PS/LP/RM/GS, AHS-UMG1 nach CF1+SP1; danach (bewährt) in shared/vorlage (Entscheid 20:06).
5. AHS-SP1 Speicher-Lösung sofort nach der CurseForge-Veröffentlichung (Entscheid 19:56).
6. Markt-Tabellen: Lauf 24.11. 05:41 nicht committet (Stände 14.–20.11. fehlen, Fallzahlen fallen). Entscheid 06:17 "warten auf UP-TAGE, höchstens
   1 Tag" läuft 25.11. ~06:17 ab -> dann Nutzer fragen (Fallzahl-Regel aussetzen oder alte Tabelle behalten). Daten-Repo hält jetzt 21.–24.11.
7. Laptop (nicht verbunden): AHS 0.65.391, PS 0.9.83, TS 2.5.30 installieren, sobald verbunden (Entscheid 10:48); GSMesstest dort prüfen.

## Offen beim Nutzer
- GuildSentinel CurseForge: dort seit 15.11. nur 0.9.39 (geprüft auf curseforge.com 24.11.); 0.9.52 war für 18:00 freigegeben, kam aber nie in
  download/. 0.9.61 Ingametest 24.11. 12:48 ohne FEHLER -> OK des Nutzers für 0.9.61 um 18:00 nötig (GS-Stand: "nur mit OK").
- Offiziere: Uploader alt (keine Version in stand.json; Lieferung 22.11. 20:25 bzw. 23.11. 23:50), Addons alt (AHS 0.65.188/0.65.360, TS ?/2.5.23,
  BS 0.9.21/0.9.60). Erinnerung über den Bot? (Nutzer noch nicht geantwortet). UP-ALT-Abnahme hängt daran.
- Discord Bot 1.5.194: Abnahme im Betrieb (1)/(3) – Bericht der Discord-Sitzung fehlt; discord-check 24.11. 18:27Z grün.
- CurseForge-Kommentare: CF1–CF3-Zwischenstand und Antworten A/B/C nicht gepostet (nicht angemeldet). Keine neuen Kommentare seit 22.11. (Gmail).
- PS: Entscheid Trefferquote A/B/C; T85 Berufsfenster; Messung SetCraftableCount (Wochenende). LP: Charakterdatei in den LP-Chat ziehen; Ingametest 3.13.13.
- AHS Wochenende: Kupfer-Preis-Test. LP: Laufen-Sitzung. BS: Liste "was sonst noch möglich wäre" nach Kampfmessung.
- Alte Ordner auf dem Laptop löschen (kein Löschrecht).

## Entscheide des Nutzers seit letztem Stand (alle in shared/wissen/entscheide.md)
- 24.11.: 20:06 Skelett erst nach Bewährung · 20:04 UMG1 alle ausser Kampf-Addons · 19:56 AHS-SP1 · 19:47 Ausreisser/Bedienung (E-Regel)
  · 19:21 AHS-CF1 (T459-Ausnahme mit Bedingungen, Freigabe im Spiel) · 19:12 AHS-TR1 · 14:09 TS/BS-Messung für alle über den Uploader.

## Wichtig zu wissen
- Gemeinsame Dateien: in allen neuesten Zips byte-gleich mit shared/ (GoldSentinelTest 3 u. a.), geprüft 24.11. 20:15. Vorlage kopiert sie beim Erstellen.
- E-Regeln neu 24.11.: Ausreisser zuerst gegen Bedienung/Windows/Server; Zeile "je Addon" lesen, Messwerkzeuge nach Messung sofort entfernen lassen.
- PC (DESKTOP-NVITMSE) hat Uploader 2.3.20 und jetzt die neuesten Addons (Tests 19:39/19:41). Laptop: WoW meist im Hintergrund (Entscheid 19.11.).
- Laptop = AUSPLUSLAPTOP (Forever-AddOns via device_bash $HOME/mnt/AddOns), zurzeit nicht verbunden.
- Uploader liefert ThreatSentinel.lua/BuffSentinel.lua von allen 4 Rechnern; Charakter-SV kommen nicht an.
- AHS CurseForge: 0.65.354 (19.11.). Geplante Aufgaben AN: Markt-Tabellen, Markt-Überwachung, Blueposts, Rezeptdaten, Raids, Discord-Betreuung, Gmail.
