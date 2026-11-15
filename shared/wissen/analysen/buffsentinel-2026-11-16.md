ANALYSE – NUR FESTGEHALTEN, KEIN AUFTRAG – Fehler werden erst nach Freigabe des Nutzers behoben

# BuffSentinel – Nacht-Analyse (Supervisor, 15.11.2026 abends)

Geprüfte Version: 0.9.21 (download/BuffSentinel-0.9.21.zip, 14.11.). Kein eigenes Quell-Repo in dieser Sitzung; Geschichte aus
raidmaster (announce/, berichte/BuffSentinel/, auftraege/BuffSentinel/). Letzte Arbeit 14.11. 08:01 (0.9.21 MN-S).

## 1. Geschichte (kurz)
0.9.7 (4.11.): Sprachen nach Client. Bis 0.9.21: Klassen-Helfer für alle WoW-Versionen (Interface 11509 … 120105), Buff-/Proc-/
Cooldown-Knöpfe als sichere Knöpfe, Entfluchen-Raster, AutoLearn, Sync, Marktdaten-Netz (GoldSentinelMarkt v3).
Offen laut offen-buffsentinel.txt: BP-2026-11-13-1 Teil 2 (Schamane: Imbue + Waffen-Totem, nach Client-Messung), MN-S2
(GoldSentinelMarkt v4 kopieren), Client-Tests des Nutzers.

## 2. Was ich gemacht habe
- addon_check: OK, 1 Warnung "GoldSentinelMarkt.lua veraltete offizielle Fassung (Version 3) – Version 6". Die Ladetests in
  addon_check (alle Spielversionen) laufen ohne Fehler.
- Code gelesen: Core.lua (Ereignisse, OnUpdate, Kampfsperre BS:Lockdown), Display.lua (ConfigureButton, SetAttribute),
  Dispel.lua (LayoutDispel), Ticker/OnUpdate in allen Dateien.
- Messdaten aus dem Spiel (GSSniperLog 15.11., Spiel-Profiler): BuffSentinel Ø 0,01–0,02 ms je Bild, Spitze 4 ms, 0 Bilder > 50 ms.

## 3. Befunde
### B-1 GoldSentinelMarkt v3 statt v6 (MITTEL)
Wie bei den anderen Addons: ohne AHSentinel läuft die alte Fassung (Feed in einem Stück, viel Speicher; MN-S2 offen).

### B-2 Aktualisierung 10× je Sekunde (Hinweis, unkritisch – GEMESSEN)
Core.lua 1364: OnUpdate ruft alle 0,1 s BS.Refresh (alle Knöpfe neu bewerten), alle 0,5 s RefreshGroup. Gemessen im Spiel nur
Ø 0,01–0,02 ms, Spitze 4 ms: das ist gut. Bleibt so, solange die Messung so aussieht.

### B-3 Sichere Knöpfe korrekt geschützt (gut)
SetAttribute nur ausserhalb der Kampfsperre (LayoutDispel bricht bei BS:Lockdown() ab; Display holt verpasste Änderungen bei
PLAYER_REGEN_ENABLED nach, Display.lua 691). Kein Befund.

### B-4 Keine eigene Offline-Testroutine im Repo sichtbar (NIEDRIG)
Die Selbsttests liegen im Addon (SelfTest.lua, im Spiel). Ein Offline-Lauf wie bei GuildSentinel/ProfessionSentinel fehlt in
raidmaster; ohne Quell-Repo in dieser Sitzung konnte ich die Selbsttests nicht ausserhalb des Spiels laufen lassen.

## 4. Offene Fragen an den Nutzer
- BP-2026-11-13-1 Teil 2 wartet auf deine Messung als Schamane (Imbue + Waffen-Totem gleichzeitig).
