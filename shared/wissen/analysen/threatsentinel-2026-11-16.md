ANALYSE – NUR FESTGEHALTEN, KEIN AUFTRAG – Fehler werden erst nach Freigabe des Nutzers behoben

# ThreatSentinel – Nacht-Analyse (Supervisor, 15.11.2026 abends)

Geprüfte Version: 2.5.13 (download/ThreatSentinel-2.5.13.zip, 14.11.). Kein Quell-Repo in dieser Sitzung; Geschichte aus
raidmaster (announce/ 2.5.8–2.5.13, berichte/ThreatSentinel/, auftraege/ThreatSentinel/). Letzte Arbeit 14.11. 09:00 (Sync).

## 1. Geschichte (kurz)
Bedrohungs-Anzeige für Tanks (alle Versionen: Interface 11507 … 120107), Spott-Knopf (sicherer Knopf, Makro), Namensplaketten,
Schadensmesser, Tank-Sync über GoldSentinelSync (2.5.13), Testroutine + TU-Tests im Addon.
Offen laut offen-threatsentinel.txt: TS-T1 (Test lässt erfundenen Mitspieler im Sync zurück), Sync mit zwei Spielern im Client.

## 2. Was ich gemacht habe
- addon_check: OK, 1 Warnung "GoldSentinelMarkt.lua veraltete offizielle Fassung (Version 3) – Version 6".
- Code gelesen: Alerts.lua (Chat-Meldungen, Abfrage 10×/s), TauntButton.lua (SetAttribute nur ausserhalb der Kampfsperre,
  sonst "pending"), Ticker/OnUpdate aller Dateien, Umgang mit geschützten Werten (163 Stellen mit IsSecret/secret).
- Messdaten (GSSniperLog 15.11., Spiel-Profiler, ausserhalb von Kämpfen): Ø 0,00–0,02 ms, Spitze 4 ms, 0 Bilder > 50 ms.

## 3. Befunde
### T-1 GoldSentinelMarkt v3 statt v6 (MITTEL) – wie bei allen anderen Addons.

### T-2 Leistung im Kampf NICHT gemessen (Hinweis)
Alle Messungen stammen aus dem Auktionshaus (kein Kampf). ThreatSentinel arbeitet vor allem im Kampf: Abfrage CheckCC 10×/s
(Alerts.lua 177), Log/Schadensmesser-Ticker 0,5 s, Namensplaketten-OnUpdate. Messvorschlag: ein GSSniperLog-Protokoll aus einem
Dungeon/Raid (Zeilen ADDONS/BILD) – Ziel: kein Bild > 16 ms durch ThreatSentinel.

### T-3 Automatische Chat-Meldungen an Gruppe/Raid (Hinweis)
Alerts.lua 220 ff.: bei Aggro-Verlust u. ä. SendChatMessage an PARTY/RAID (einstellbar: GROUP/BOSS/TANKS/SELF/OFF), in
Forever-Instanzen gesperrt -> pcall + Ausweich auf Tank-Sync. Sauber gelöst. Prüfen (im Client): keine Wiederholungs-Flut, wenn
die Aggro schnell hin und her springt (Grenze je Zeit?).

### T-4 TS-T1 (aus der Prüfung, NIEDRIG) – Test hinterlässt erfundenen Mitspieler im Sync. Weiter offen.

## 4. Was gut ist
- Sichere Knöpfe korrekt (Kampfsperre -> "pending", nachholen), geschützte Werte überall geprüft, Testmodus spricht nur zu dir.
