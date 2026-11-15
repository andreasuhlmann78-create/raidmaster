ANALYSE – NUR FESTGEHALTEN, KEIN AUFTRAG – Fehler werden erst nach Freigabe des Nutzers behoben

# LevelPilot – Nacht-Analyse (Supervisor, 15.11.2026 abends)

Geprüfte Version: 3.12.33 (announce/levelpilot__levelpilot-3.12.33.LevelPilot.zip, 15.11. 19:00) mit LevelPilot_Data 1.6.1.
LevelPilot wird gerade aktiv von seiner eigenen Sitzung bearbeitet (Berichte 3.12.30–3.12.33 heute). Kein Quell-Repo hier.

## 1. Geschichte (kurz, aus berichte/LevelPilot/ und auftraege/LevelPilot/)
Levelhilfe für WoW Forever (nur Interface 16001): Planer, Navigation/Wegpunkte, Quest-DB, Gruppen/Soziales, Protokoll, Speicher-
und Leistungsmessung. Offen laut offen-levelpilot.txt: PF-A (Planung Allianz über 16 ms: T150 Median 26 ms, T155 30 ms), GR1-K,
SP1-M (Speicher im Spiel messen), Wegpunkte/Strassen wartend.

## 2. Was ich gemacht habe
- Zip entpackt (LevelPilot 2,2 MB, LevelPilot_Data 5,5 MB), Ticker/OnUpdate aller Dateien, Protocol.lua (Speicher-Messung) gelesen.
- Messdaten aus dem Spiel (GSSniperLog 15.11., Spiel-Profiler je Minute, ~18:15–19:03, Spieler steht im AH, kein Leveln).

## 3. Befunde
### L-1 Wiederkehrende Ruckler alle ~5 Minuten – GEMESSEN, Ursache im Code sehr wahrscheinlich (HOCH für das Spielgefühl)
Gemessen: LevelPilot Spitze 167 -> 179 ms, Bilder über 50 ms 53 -> 63 in ~45 Min., obwohl der Spieler nur im AH steht. Minuten
mit Ø ≈ 0,85–1,14 ms (sonst 0,04–0,3 ms): 18:19, 18:24, 18:29, 18:37, 18:47, 18:52, 19:01 – also etwa alle 5 Minuten.
Code: Protocol.lua 670 LP:Ticker("protocol_memory", 300, Memory) -> Memory() ruft UpdateAddOnMemoryUsage() (Protocol.lua 388).
Aus AHSentinel belegt (Vollscan.lua 182 ff., Testbericht 0.65.168, TB168-1): UpdateAddOnMemoryUsage misst den Speicher ALLER
Addons und braucht bei grossen Daten "mehrere 100 ms" (gemessen 829 ms). Im Client des Nutzers liegt der Lua-Speicher bei
400–510 MB (vor allem AHSentinel). Die 5-Minuten-Ruckler passen genau dazu. Verdacht -> fast belegt; zu messen mit einer
Zeitmessung um Memory() oder einem Protokoll ohne den Ticker.
FREIGEGEBEN vom Nutzer 19:22 -> Auftrag L-1 in offen-levelpilot.txt. Lösungsidee: collectgarbage("count") statt UpdateAddOnMemoryUsage (wie AHSentinel), oder nur auf Befehl.

### L-2 Viele schnelle Ticker (Hinweis)
Ticker 0,05 s (Virtual "journey", nur bei Reise), 0,5 s (steps), 1 s (caves, session, ui), Navigation-/Pins-OnUpdate. Im AH
gemessen Ø meist < 0,3 ms – in Ordnung; im Gelände (Leveln) nicht gemessen.

### L-3 PF-A (aus der Prüfung): Planung Allianz über 16 ms – weiter offen.

### L-4 GoldSentinelMarkt
Version in der Zip prüfen (addon_check lief hier nicht auf die announce-Zip); siehe die anderen Addons.

## 4. Offene Fragen an den Nutzer
- Ein GSSniperLog-Protokoll beim Leveln (draussen, mit Navigation) würde zeigen, wie LevelPilot im echten Einsatz läuft.
