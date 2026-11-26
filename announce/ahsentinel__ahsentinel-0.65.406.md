## AHSentinel 0.65.406

**Deutsch**
- **Figuren doppelt gezählt – behoben:** WoW Forever meldet seit etwa 21.11. keinen Realm-Namen mehr. Dadurch stand jede Figur ein zweites Mal in den Daten, und "Gold (alle Figuren)" zählte ihr Gold doppelt. AHSentinel behält jetzt den bekannten Realm und führt die Doppel einmal zusammen (Goldverlauf, Einstand, Geldfluss, Buchungen, Rezepte); eine Sicherung der alten Einträge bleibt erhalten.
- Eine Figur ohne bekannten Goldstand (z. B. Bank-Figur) nimmt jetzt den letzten Goldstand aus der Buchhaltung.
- Etwas weniger Speicherabfall je Vollscan (intern).

**English**
- **Characters counted twice – fixed:** WoW Forever no longer reports a realm name (since about 21 Nov). Every character was therefore stored a second time, and "Gold (all characters)" counted their gold twice. AHSentinel now keeps the realm it knew and merges the duplicates once (gold history, cost basis, money flow, bookings, recipes); a backup of the old entries is kept.
- A character without a known gold value (e.g. a bank character) now uses the last gold value from the accounting.
- Slightly less memory garbage per full scan (internal).
