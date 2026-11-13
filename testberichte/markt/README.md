# Marktdaten WoW Forever (MN7)

Wochenberichte der Sammelstelle auf dem Bot-Server (RaidMasterBot/market.py). Quelle: Vollscans der Spieler
(Zeilen `GSMARKT1|…` aus shared/GoldSentinelMarkt.lua, geschickt vom Uploader). Keine Namen.

- `<JJJJ>-W<KW>.md` – Wochenbericht (montags): je Fraktion Scans, Quellen, Abdeckung (Stunden der Woche),
  Top-Items nach Absatz-Untergrenze mit Spanne, Umschlag, Preis und Angebot.
- `blizzard-<JJJJ-MM-TT>.txt` – nur wenn sich die Realm-Listen der Blizzard-API geändert haben (MN8, monatlich).

Abgeholt vom Workflow `.github/workflows/markt-bericht.yml` (alle 6 Stunden) aus dem Bot-Kanal.
