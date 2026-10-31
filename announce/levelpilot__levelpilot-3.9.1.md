📢 **LevelPilot 3.9.1** – wichtiges Sicherheits-Update: Flugpunkte gehen nicht mehr verloren

Bitte **sofort aktualisieren**, besonders wenn ihr die virtuelle Reise benutzt.

**⚠ Behoben: Datenverlust**
Im Spieltest gingen alle aufgezeichneten Flugpunkte verloren. Ursache: „Reise ab hier“ konnte beim Start vom Spiel abgebrochen werden („script ran too long“) – danach hat „Stopp“ die Flugpunkt-Liste geleert, und die Sicherung im Charakter übernahm die leere Liste.
• Die Reise merkt sich jetzt zuerst alle echten Daten und stellt beim Beenden nie etwas auf „leer“
• Die schwere Arbeit beim Start läuft in kleinen Häppchen in der Reise selbst, nicht mehr im Chat-Befehl
• Die Sicherung im Charakter ist jetzt eine eigene Kopie. Fehlt im Konto etwas, das in der Sicherung steht, wird es vor jedem Speichern zurückgeholt
• Die virtuelle Reise schreibt nichts mehr in die echte Questdatenbank

**🖱 Rechtsklick im Leitfaden**
Öffnet jetzt ein Menü (30 Minuten zurückstellen / Quest ignorieren / Abbrechen) statt die Quest sofort zu ignorieren. `/lp zurück` holt die zuletzt ignorierte Quest zurück.

**🛠 Weitere Korrekturen**
• Textfenster (Bericht, Protokoll, Selbsttest) halten die Tastatur nicht mehr fest – Chat-Befehle gehen wieder beim ersten Enter
• Gefahrenkarte genauer: einzelne Questgeber und Schlachtfeld-NPCs der anderen Fraktion zählen nicht mehr als Gefahr
• „Zuschauen“ zeichnet die Spur der letzten Schritte deutlich sichtbar auf die Weltkarte
• Kompakter Guide zeigt nur noch eine Entfernung, überall gilt die Weglänge wie am Pfeil
• `/lp lang` zeigt die aktuelle Sprache, `/lp weg` bestätigt den Wegpunkt
• Chinesisch/Koreanisch ohne Kästchen, kürzere Beschriftungen in Portugiesisch und Russisch

**📦 Aktualisieren**
`LevelPilot.zip` nach `Interface/AddOns` entpacken und **LevelPilot** sowie **LevelPilot_Data** ersetzen, dann `/reload`.

- GoldSentinel
