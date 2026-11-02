# Testberichte der GoldSentinel-Addons

Hier landen automatisch die Ergebnisse der Testroutinen im Spiel und die Lua-Fehler, die die Addons im normalen Spiel
abfangen. Die Prüf-Sitzung wertet sie aus und schreibt daraus Korrektur-Anweisungen für die Addon-Kollegen.

## Weg eines Berichts

1. **Addon:** Die Testroutine (bzw. der Fehler-Abgriff) schreibt über `GoldSentinelTest.lua` einen Bericht in die
   SavedVariables des Addons (`<AddonDB>.gsTest`). Auf die Festplatte kommt er beim nächsten `/reload` oder Ausloggen.
2. **RaidMasterUploader** auf dem PC: findet neue Berichte (Strings, die mit `GSTEST1` beginnen) in allen
   SavedVariables-Dateien und schickt sie an den Discord-Kanal **#testberichte**.
3. **GitHub-Workflow „Testberichte“** (alle 30 Minuten): holt sie nach `berichte/<Addon>/<id>.json` und schreibt
   `status.md` und `status.json`.

## Dateien

| Datei | Inhalt |
|---|---|
| `status.md` | je Addon der letzte Testlauf (je Client), alle FEHLER, Fehler im Spiel der letzten 7 Tage |
| `status.json` | dasselbe maschinenlesbar; `offen` = alles, was die Prüf-Sitzung ansehen muss |
| `berichte/<Addon>/<id>.json` | jeder Bericht einmal, unverändert |

## Ohne Discord

Die Prüf-Sitzung kann Berichte auch direkt aus einer Datei übernehmen, z. B. wenn der Nutzer die SavedVariables-Datei
(`WTF/Account/<Konto>/SavedVariables/<Addon>.lua`) in den Chat legt:

    python3 addon-check/testberichte.py --import BuffSentinel.lua

Datenschutz: Berichte enthalten keine Spieler-, Gilden- oder Chatnamen – nur Addon, Version, Client, Sprache, Klasse und
Level. Geschützte Werte („secret values“) werden nie gelesen.
