📢 **LevelPilot 3.12.3** – fit für den Forever-Start am 5. November

**🛡 Stabil auf dem modernen Client**
• Geschützte Werte im Kampf werden überall beachtet: Ruhestein-Abklingzeit, Namen von Händlern und Questgebern, Tooltips von Objekten, Beute- und Addon-Nachrichten – keine Lua-Fehler mehr, auch wenn das Spiel im Kampf Werte sperrt
• Fehlt eine alte Spielfunktion, nimmt LevelPilot die neue (Chatfeld für die Gruppensuche, grüner Quest-Bereich, bekannte Zauber). Der Selbsttest `/lp test` zeigt, falls etwas nicht verfügbar ist
• WoW Forever wird über die gemeinsame Versionserkennung aller GoldSentinel-Addons erkannt

**🔧 Behoben**
• `/lp reise bericht` gab einen Lua-Fehler
• Abseits des Weges wird die Route höchstens alle 0,5 Sekunden neu berechnet, auf Flügen gar nicht – weniger Ruckler
• Ein Fehler wiederholt sich nicht mehr jede Sekunde im Chat

**📚 Datenpaket**
LevelPilot braucht mindestens **LevelPilot_Data 1.6.0** (liegt in der ZIP) und meldet sich einmal, wenn ein älteres installiert ist.

**📦 Aktualisieren**
`LevelPilot.zip` nach `Interface/AddOns` entpacken und **LevelPilot** sowie **LevelPilot_Data** ersetzen, dann `/reload`.

- GoldSentinel
