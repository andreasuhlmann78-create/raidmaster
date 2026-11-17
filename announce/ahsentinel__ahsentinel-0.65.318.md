📦 **AHSentinel 0.65.318** – viel weniger Ruckeln nach dem Vollscan 🚀

• **Weniger Ruckeln nach dem Vollscan:** Die gelernte Kauf-Marge las nach jedem Scan das ganze Kauf-Journal neu – für jedes Item der Liste „Heute“ und der Preisprüfung. Mit grossen Daten gab das viele Bilder von 20–60 ms hintereinander. Jetzt wird das Journal nur gelesen, wenn es sich geändert hat. Alle Zahlen bleiben genau gleich.
• **Absatz-Faktor je Warengruppe:** in einem Durchlauf für alle Gruppen und im Hintergrund vorgerechnet (vorher ein Durchlauf je Gruppe am Stück).
• **Für Tester:** Die Vollscan-Messung zerlegt das längste Bild in eigene Arbeit von AHSentinel, Rest (Spiel, andere Addons) und Antworten des Servers auf Item-Daten. Neue Prüfung in der Testroutine für das Kauf-Journal.

**Installation:** ZIP unten herunterladen, entpacken und den Ordner `AHSentinel` in `Interface/AddOns` ersetzen. Deine Daten und Einstellungen bleiben erhalten.
