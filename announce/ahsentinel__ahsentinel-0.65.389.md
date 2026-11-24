## AHSentinel 0.65.389

**Deutsch**
- **Testroutine, Sniper-Ruckeln (S13):** Antworten auf Item-Daten wurden als Millisekunden eigener Arbeit gezählt ("105 ms" waren 105 Antworten). Jetzt zählen nur Aufgaben, Ereignisse und Skripte; dazu nennt der Bericht die Stelle (Datei:Zeile) des langsamsten eigenen Skripts je Bild.
- **Testroutine, Sandbox:** Diagnose-Einträge aus dem Abschluss der Routine landen nicht mehr im echten Protokoll.
- **Testroutine, Sniper-Prüfungen:** ein echter Treffer oder ein Wächter-Ziel beeinflusst die Prüfungen von Knopf und Mausrad nicht mehr.
- **Vollscan-Messung (nur Testroutine):** Kosten der Messung je Bild und als Summe.

**English**
- **Test routine, Sniper smoothness (S13):** item-info answers were counted as milliseconds of own work ("105 ms" were 105 answers). Now only jobs, events and scripts count; the report names the location (file:line) of the slowest own script per frame.
- **Test routine, sandbox:** diagnostic entries written while the routine finishes no longer reach the real log.
- **Test routine, Sniper checks:** a real hit or watcher target no longer affects the button and mouse-wheel checks.
- **Full scan measurement (test routine only):** cost of the measurement per frame and as a total.
