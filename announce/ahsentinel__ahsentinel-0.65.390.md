## AHSentinel 0.65.390

**Deutsch**
- **Vollscan braucht weniger Speicher:** die Preisleitern des letzten Scans werden ab dem zweiten Scan nach dem Einloggen wiederverwendet (vorher erst ab dem dritten, und ein unvollständiger Scan löschte den Vorrat). Ein unvollständiger Scan wird jetzt vor dem Verdichten erkannt und ändert wie bisher nichts.
- **Vollscan-Messung (nur Testroutine):** die Messung des Speichers je Addon gehört jetzt zum längsten Bild; der Bericht zeigt, wie viele Preisleitern wiederverwendet wurden.

**English**
- **Full scan uses less memory:** the price ladders of the last scan are reused from the second scan after login on (before: only from the third, and an incomplete scan lost them). An incomplete scan is now detected before the ladders are built and changes nothing, as before.
- **Full scan measurement (test routine only):** the per-addon memory measurement now belongs to the longest frame; the report shows how many ladders were reused.
