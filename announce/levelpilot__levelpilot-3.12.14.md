📢 **LevelPilot 3.12.14** – Lua-Fehler behoben

**🛠 Fehler behoben**
In WoW Forever lieferte das Spiel beim AFK-Status zeitweise einen geschützten Wert – das führte zu hunderten Lua-Fehlern („secret boolean value“). LevelPilot prüft diesen und alle ähnlichen Werte jetzt vor der Benutzung; die aktive Spielzeit zählt dann über den eigenen Leerlauf-Zähler.

**📦 Aktualisieren**
`LevelPilot.zip` nach `Interface/AddOns` entpacken und **LevelPilot** sowie **LevelPilot_Data** ersetzen, dann `/reload`.

- GoldSentinel
