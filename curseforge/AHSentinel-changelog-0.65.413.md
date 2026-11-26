## ⚠️ WICHTIGES UPDATE – bitte aktualisieren / IMPORTANT UPDATE – please update

> Beta-Version. Bitte melde Fehler in den Kommentaren auf CurseForge, am besten mit der Lua-Fehlermeldung und der WoW-Version.
> Beta version. Please report errors in the comments on CurseForge, ideally with the Lua error message and your WoW version.

### Deutsch – das Wichtigste seit 0.65.400

- **Tagesbilanz berichtigt:** „seit gestern" zeigte nach dem Ausloggen ins Charakter-Menü oder dem Beenden das ganze Gold einer Figur als Zuwachs (das Spiel meldet beim Ausloggen 0 Gold). Diese 0 zählt nicht mehr; vorhandene Daten werden richtig gelesen, nichts wird gelöscht.
- **Figuren nicht mehr doppelt:** WoW Forever meldet seit etwa 21.11. keinen Realm-Namen mehr. Dadurch stand jede Figur zweimal in den Daten und „Gold (alle Figuren)" zählte doppelt. Die Doppel werden einmal zusammengeführt (Goldverlauf, Einstand, Geldfluss, Buchungen, Rezepte), mit Sicherung der alten Einträge.
- **Wächter flüssiger:** bei vielen Angeboten holte der Wächter bei jeder neuen Ergebnisseite die ganze Liste neu (bei 4 500 Angeboten je ~9 ms und 3,7 MB) – jetzt nur noch einmal je Runde.
- **Auktionshaus öffnen schneller:** der Reiter wird nach dem Einloggen im Hintergrund vorgebaut (erstes Öffnen im Spiel gemessen 5,7 ms statt 10–18 ms).
- Etwas weniger Speicherabfall je Vollscan, kleinere Ruckler beim Aufbau der Namensliste, mehr Diagnose-Zeilen für die Fehlersuche.

### English – the most important changes since 0.65.400

- **Daily summary fixed:** "since yesterday" showed a character's whole gold as a gain after logging out to the character screen or quitting (the game reports 0 gold while logging out). This 0 no longer counts; existing data is read correctly, nothing is deleted.
- **Characters no longer counted twice:** WoW Forever no longer reports a realm name (since about 21 Nov), so every character was stored twice and "Gold (all characters)" counted double. The duplicates are merged once (gold history, cost basis, money flow, bookings, recipes), with a backup of the old entries.
- **Smoother watcher:** with many offers the watcher fetched the whole list again for every new result page (about 9 ms and 3.7 MB each with 4,500 offers) – now only once per round.
- **Faster auction-house opening:** the tab is pre-built in the background after logging in (first opening measured in game: 5.7 ms instead of 10–18 ms).
- Slightly less memory garbage per full scan, smaller hitches while building the name list, more diagnostic lines for troubleshooting.
