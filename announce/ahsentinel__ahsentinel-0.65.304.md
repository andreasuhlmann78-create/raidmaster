📦 **AHSentinel 0.65.304** – Testdaten aufgeräumt 🧹

• **Testdaten aufgeräumt:** Zwei Prüfungen der Testroutine liessen Testdaten zurück (14 erfundene Händlerpreise und über die gemeinsamen Marktdaten einen nachgespielten Scan mit 1050 erfundenen Items). Beides ist behoben, und beim Laden entfernt AHSentinel solche Testdaten jetzt selbst aus deinen Daten – echte Daten bleiben unberührt.
• **Testroutine:** Die Sicherungs-Prüfung („nichts Echtes geändert“) ist strenger und meldet jetzt auch kleinste Abweichungen.
• **Für Tester – `/ahs testroutine alles`:** misst jetzt auch den Schnell-Vollscan selbst (zwei Scans mit Abstand, bleibender Speicher und längste Lücke). Du musst nur das Auktionshaus offen lassen. (0.65.303 kommt mit dieser Version.)

**Installation:** ZIP unten herunterladen, entpacken und den Ordner `AHSentinel` in `Interface/AddOns` ersetzen. Deine Daten und Einstellungen bleiben erhalten.
