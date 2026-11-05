📢 **LevelPilot 3.12.7** – Route in Mulgore korrigiert, Lua-Fehler behoben

**🧭 Route**
Quests, die du ganz in der Nähe abgeben kannst, kommen jetzt **immer zuerst** – vor Flugmeister, Ruhestein und weiten Zielen. In Mulgore führte die Route sonst an Camp Narache bzw. Bloodhoof vorbei.
Aufgezeichnete Orte, die weit neben den Daten des Datenpakets liegen, werden nicht mehr bevorzugt; Händler oder Gastwirte mitten im Gebirge werden nicht mehr angeboten.
Würde der Weg als Luftlinie über Gebirge führen, zeichnet LevelPilot keine Linie mehr – der Pfeil zeigt dann direkt zum Ziel.

**🛠 Fehler behoben**
Kein Lua-Fehler mehr im Fehler-Protokoll („attempt to compare a secret number value“).

**📦 Aktualisieren**
`LevelPilot.zip` nach `Interface/AddOns` entpacken und **LevelPilot** sowie **LevelPilot_Data** ersetzen, dann `/reload`.

- GoldSentinel
