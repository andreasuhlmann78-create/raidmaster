# Stand Supervisor (Prüf-Sitzung, Projekt «Addonprüfer»)

## Stand 24.11.2026 18:56 · Versionen geprüft: AHS 0.65.391 · PS 0.9.82 · BS 0.9.64 · TS 2.5.30 · LP 3.13.13 · RM 3.0.43 · GS 0.9.61 · Uploader 2.3.20
Sitzung seit 23.11. 06:18. Repos: raidmaster, goldsentinel-daten (schreiben); ahanalyzerpro, professionsentinel, guildsentinel (lesen).

## Gerade in Arbeit
- PAUSE auf Wunsch des Nutzers 20:07. Unterbrochen mitten in: "Lückenprüfung der letzten 24–48 Std." (Nutzer 20:07) + Prüfung PS 0.9.83.
  Gefunden bisher (noch NICHT gemeldet, noch nichts eingetragen):
  1. GuildSentinel: auf CurseForge noch 0.9.39 (download/, uploaded.json, seit 15.11.); 0.9.61 Ingametest 24.11. 12:48 ohne FEHLER –
     CurseForge braucht OK des Nutzers (GS-Stand) -> Nutzer fragen.
  2. AHSentinel CurseForge: 0.65.354 (19.11.) – AHS-CF1 läuft.
  3. UP-ALT: PC hat Uploader 2.3.20 (stand.json), Offiziere nicht (alt, Lieferung 22.11./23.11.) -> Erinnerung über Bot? Nutzer fragen.
  4. Discord Bot 1.5.194: Abnahme im Betrieb (1)-(3) offen, letzter Discord-Bericht 24.11. 10:39.
  5. CurseForge-Zwischenstand CF1–CF3 / Antworten an Spieler A/B/C: Posten scheiterte (nicht angemeldet) – offen.
  6. Laptop: AHS 0.65.390/391, PS 0.9.82/0.9.83, TS 2.5.30 nicht installiert (Laptop nicht verbunden).
  7. Skelett: shared-Dateien kopiert neues_addon.py (COMMON) aus shared/ – ok; UMG1 später (Entscheid 20:06).
  Noch zu prüfen: Rest der Entscheide 23./24.11. (D-MITGL1-R, W3/W2-E bei AHS, LP-Wegsperren 22.11.), BS-M1-b Version ausstehend.
  PS 0.9.83 (Bericht 20:06, PS-I5-a): Bericht gelesen, md5 download=announce 2f7f4d5b… gleich; addon_check-Ausgabe NICHT gesehen -> erneut
  laufen lassen; Code von SameValue/UI.AlarmRowClick lesen; dann in offen-professionsentinel eintragen.

## Nächste Schritte (Reihenfolge)
1. Neueste Versionen hat der Nutzer 18:55 selbst installiert (Fernzugriff auf den PC) – "alles gut". Laptop erst wieder, wenn verbunden.
2. TS-M1-b / BS-M1-b (Messung für alle Spieler, Daten über den Uploader, Entscheid 14:09): neue Versionen von TS und BS prüfen.
   Prüfen: läuft ohne Entwicklermodus, Ablage in account-weiter SV (kommt mit dem Uploader), keine Namen, Ringpuffer 20, ≤ 1 ms/Bild.
3. Ingametests auswerten: AHS 0.65.390 (T459 "wiederverwendet x, neu y", vollscan_luecke Bild-Bezug), PS 0.9.82 (T297/T140/T219/T243),
   TS-M1 Kampfmessung, BS T270 (Raster), LP 3.13.13 ("Dauer").
4. Antworten der Projekte auf AHS-I3-a (Verdichtung überschreibt sichtbare Tabellen) und PS-I5-a (Funktionen gelten in SameValue als gleich).
5. LevelPilot: sicherer Weg für die Charakterdatei (LevelPilotCharDB) mit dem Nutzer klären – nicht übers öffentliche Repo.

6. SKELETT (Entscheid 20:06): UMG1 in shared/vorlage übernehmen, sobald es in PS/LP/RM/GS im Spiel belegt funktioniert. Ebenso spätere Anpassungen für alle Addons.

## Offen beim Nutzer
- BS-M1-b: BuffSentinel angestossen 18:42, Version steht aus. TS-M1-b angenommen (2.5.30) – echte Daten mit der nächsten Uploader-Lieferung.
- Wochenende (PC): AHS Kupfer-Preis-Test; PS Herstellen/SetCraftableCount-Messung; LP Sitzung mit Laufen; PS T85: welches Berufsfenster offen war.
- Uploader 2.3.20 auf PC und bei Offizieren (Abnahme UP-ALT).
- BS "was sonst noch möglich wäre" (Liste 1–6 im Bericht 0.9.64): Entscheid nach den Kampfmessungen.
- CurseForge-Zwischenstand CF1–CF3: Posten scheiterte (nicht angemeldet). Alte Ordner auf dem Laptop löschen (kein Löschrecht).

## Entscheide des Nutzers seit letztem Stand (alle in shared/wissen/entscheide.md)
- 24.11. 14:09 TS-M1/BS-M1: Messung bei allen Spielern (auch Offiziere), Daten über den Uploader.
- 24.11. 13:52 BS-M1 bauen (Reinigen wie Decursive, Klick-Raster); 13:33–13:35 TS-M1 messen, automatisch, nur lesen.
- 24.11. 10:48 jede neue Version sofort auf dem Laptop installieren; 07:22 Daten alter Versionen nicht annehmen;
  07:09 Supervisor korrigiert shared/GoldSentinelTest.lua; 07:04 Supervisor nur prüfen.

## Wichtig zu wissen
- Laptop = AUSPLUSLAPTOP (Forever-AddOns: C:\Program Files (x86)\World of Warcraft\_forever_\Interface\AddOns; device_bash $HOME/mnt/AddOns).
  Installiert Stand 14:15: AHS 0.65.389, RM 3.0.43, TS 2.5.29, BS 0.9.64, PS 0.9.81, LP 3.13.13, GS 0.9.61 (cmp ok).
- Uploader liefert ThreatSentinel.lua und BuffSentinel.lua von allen 4 Rechnern (daten.py ADDONS Zeile 82); Charakter-SV kommen nicht an.
- Daten-Repo goldsentinel-daten: Branch "sicherung" massgebend, Dateien .lua.gz; GSTEST1-Berichte per Regex aus den SV.
- AHS CurseForge GESPERRT: T459 > 10 240 KB (Nachbau 11 650), T750/T191 offen. GS ist für CurseForge 18:00 frei.
- Testberichte kommen über Discord #testberichte (Workflow testberichte.yml :17/:47 UTC).
- Geplante Aufgaben AN: Markt-Tabellen, Markt-Überwachung, Blueposts, Rezeptdaten, Raids, Discord-Betreuung, Gmail. AUS: Nachprüfung.
