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

## Berichte anderer Spieler (ab GoldSentinelTest 2, 9. Nov. 2026)

Nur auf dem PC des Nutzers läuft der Uploader. Damit auch Fehler von Gildenmitgliedern und anderen Spielern ankommen:

1. Der Nutzer schaltet auf seinem Charakter `/gstest sammler an` ein. Der Sammler meldet sich alle 30 Minuten über
   GoldSentinelSync 2 (Gilde, Gruppe, Flüster-Netz).
2. Andere Spieler werden einmal gefragt (oder `/gstest teilen an|aus`). Nur mit Zustimmung schicken ihre Clients kurze
   Zusammenfassungen per Flüstern an den Sammler: Fehler im Spiel und FEHLER-Zeilen von Testläufen, keine Namen,
   höchstens 3 je Addon und Tag, gleiche Fehler höchstens einmal in 7 Tagen.
3. Der Sammler legt sie als `GSTEST1`-Bericht mit `"fremd": true` in `<AddonDB>.gsTest.fremd` ab -> Uploader -> hier.
   In `status.md` stehen sie mit „fremder Spieler“ beim Client; sie zählen nie als „letzter Testlauf“.

Fremde Berichte sind Hinweise, keine Belege: Jeder könnte sich als Sammler melden oder Berichte erfinden.

## Ohne Discord

Die Prüf-Sitzung kann Berichte auch direkt aus einer Datei übernehmen, z. B. wenn der Nutzer die SavedVariables-Datei
(`WTF/Account/<Konto>/SavedVariables/<Addon>.lua`) in den Chat legt:

    python3 addon-check/testberichte.py --import BuffSentinel.lua

Datenschutz: Berichte enthalten keine Spieler-, Gilden- oder Chatnamen – nur Addon, Version, Client, Sprache, Klasse und
Level. Geschützte Werte („secret values“) werden nie gelesen.

## Diagnose-Protokolle und Wegdaten (seit 9. Nov. 2026)

Auf demselben Weg (SavedVariables -> Uploader -> #testberichte -> hier) kommen auch:

- `GSDIAG1|<Addon>|<Version>|…|<Text>` – Diagnose-Protokoll (Vorlage `Diag.lua`, `/<befehl> protokoll`).
  Ablage: `testberichte/diagnose/<Addon>/<Version>-<Prüfsumme>.txt` (gleicher Inhalt nur einmal).
- `GSWEGE1{JSON}` – Wegdaten von LevelPilot (`kind = "wege"`). Ablage: `testberichte/wege/<Addon>/<id>.json`.

`status.md` zeigt je Addon die Anzahl und die neueste Datei. Keine Namen in den Daten – die Addons ersetzen sie.
Der RaidMasterUploader muss die beiden Kennungen mitschicken (Auftrag an RaidMaster).
