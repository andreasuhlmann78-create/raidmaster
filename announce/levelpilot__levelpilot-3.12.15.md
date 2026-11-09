📢 **LevelPilot 3.12.15** – Testroutine prüft die Oberfläche

**🧪 Neu in der Testroutine**
`/lp testroutine` hat einen neuen Bereich **K** (T224–T229). Er prüft im Spiel:
• Eigene Infofenster verdecken keine Knöpfe
• Kein Überlappen mit Blizzard- oder anderen GoldSentinel-Fenstern
• Alle LevelPilot-Fenster ganz im Bildschirm, Knopfbeschriftungen nicht abgeschnitten
• Werte plausibel: die Anzahl **fertiger** Quests im Questlog stimmt mit der Anzahl **Abgeben**-Schritte in der Liste überein, dazu Questanzahl, Stufe und Kartenposition
• Keine Fehlerschleifen: kein Lua-Fehler öfter als 10-mal je Sitzung

**📦 Aktualisieren**
`LevelPilot.zip` nach `Interface/AddOns` entpacken und **LevelPilot** sowie **LevelPilot_Data** ersetzen, dann `/reload`.

- GoldSentinel
