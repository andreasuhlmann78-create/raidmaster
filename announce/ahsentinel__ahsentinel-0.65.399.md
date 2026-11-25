## AHSentinel 0.65.399

**Deutsch**
- **Kein Lua-Fehler "integer overflow" mehr:** sehr grosse Beträge (über 214 748 Gold in Kupfer) werden überall ohne Fehler angezeigt und gespeichert – bisher nur beim CSV-Export behoben. Normale Beträge erscheinen genau wie bisher.
- **Testroutine:** Fehler im Ablauf nennen die Stelle; die Vollscan-Selbstkontrolle nennt die Nummer des Vollscans seit dem Laden.

**English**
- **No more "integer overflow" Lua error:** very large amounts (above 214,748 gold in copper) are shown and saved everywhere without an error – before only fixed for the CSV export. Normal amounts look exactly as before.
- **Test routine:** errors in the run name the place; the full-scan self-check names which full scan since loading it was.
