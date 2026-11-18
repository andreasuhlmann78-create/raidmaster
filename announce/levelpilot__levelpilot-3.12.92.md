📢 **LevelPilot 3.12.92** – weniger Ruckeln beim Einloggen und bei der Wegsuche

• Beim Einloggen lädt LevelPilot das Wegnetz jetzt in kleinen Portionen (höchstens 4 ms pro Bild). Solange das läuft (Bruchteil einer Sekunde), zeigt die Navigation ehrlich die Luftlinie.
• Die Wegsuche der Navigation läuft über denselben gemeinsamen Takt aller GoldSentinel-Addons; lange eigene Wege werden beim ersten Mal ebenfalls in Portionen berechnet.
• Testdaten bleiben bei LevelPilot: Während eines Tests teilt LevelPilot keine eigenen Aufzeichnungen mit Gilde, Gruppe oder Netz. Andere Addons können das über `LevelPilotAPI.TestRunning()` abfragen.
• Testmodus: T151 misst die Wegsuche in Portionen, neue Tests T351 und T352.

**📦 Aktualisieren**
`LevelPilot.zip` nach `Interface/AddOns` entpacken und **LevelPilot** sowie **LevelPilot_Data** ersetzen, dann `/reload`.

- GoldSentinel
