📦 **AHSentinel 0.65.317** – Testroutine ohne „script ran too long“ 🛠️

• **Behoben für Tester:** Bei `/ahs testroutine alles` konnte „script ran too long“ kommen. Das Testbericht-Fenster wird jetzt höchstens alle halbe Sekunde neu gezeichnet, jede Prüfung ist ein eigener kleiner Schritt (höchstens 5 ms je Bild), und das Aufräumen des Speichers läuft in Portionen. Lange einzelne Prüfungen stehen mit Namen und Zeit in der Zusammenfassung.

**Installation:** ZIP unten herunterladen, entpacken und den Ordner `AHSentinel` in `Interface/AddOns` ersetzen. Deine Daten und Einstellungen bleiben erhalten.
