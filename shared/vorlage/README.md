# Vorlage für neue GoldSentinel-Addons

Grundlage für jedes neue Addon der GoldSentinel-Familie. Sie enthält alles, was die Prüf-Sitzung bei jedem Addon
verlangt. So besteht ein neues Addon die Addon-Prüfung vom ersten Tag an ohne FEHLER und ohne WARNUNG.

## Neues Addon erstellen

Im raidmaster-Repo:

```
python3 shared/vorlage/neues_addon.py LootSentinel --slash ls \
    --en "Loot helper for raids" --de "Loot-Helfer für Raids" \
    --farbe 3fc7eb --icon "Interface\Icons\INV_Misc_Bag_10" --kategorie Inventory \
    --ziel ~/addons --zip
python3 addon-check/addon_check.py ~/addons/LootSentinel-0.1.0.zip        # -> kein FEHLER
```

Das Skript:
- prüft Name, Befehl und Farbe
- lehnt einen Namen ab, der schon in `download/` oder `announce/` veröffentlicht ist
- kopiert die Vorlage und ersetzt alle Platzhalter (und bricht ab, wenn einer übrig bleibt)
- legt `GoldSentinelGame.lua` und `GoldSentinelTest.lua` unverändert aus `shared/` dazu
- baut mit `--zip` die ZIP im Aufbau von `download/`

Das fertige Addon lädt sofort im Spiel. Mit `/ls test` läuft die eingebaute Testroutine.

## Was drin ist

| Datei | Inhalt |
|---|---|
| `<Name>.toc` | alle Clients (Era, Forever 16001, TBC, Wrath, Titan, Cata, Mists, Retail), gemeinsame Dateien zuerst, SavedVariables `<Name>DB`, Beschreibung EN/DE |
| `Locales.lua` | Texte als Schlüssel (`L.TITEL`): Englisch als Standard, Deutsch Pflicht, Blöcke für alle weiteren Sprachen |
| `Core.lua` | Namensraum, Version aus der .toc, Einstellungen mit Standardwerten und Migrationen, Ereignisse (`ns:On`), Fehler abfangen und melden (`ns.Try`), Kampfsperre (`ns.WhenOutOfCombat`), Befehl `/<befehl>` mit `help`, `config`, `status`, `test` |
| `API.lua` | `ns.API`: jede Blizzard-Funktion einmal ausgewählt (modern zuerst, alt als Rückfall), `ns.SafeUnitName` (geschützte Namen), `ns.Act`: einzige Stelle für Aktionen mit Folgen |
| `Options.lua` | Seite im Einstellungsfenster (Settings-API, Rückfall InterfaceOptions), Beispiel-Optionen |
| `UI.lua` | Hauptfenster (verschiebbar, Position gespeichert, Esc schliesst, Inhaltsbereich `ns.content`), Kopierfenster |
| `TestRoutine.lua` | Testroutine nach der Vorgabe der Prüf-Sitzung (Bereiche A–J), Sandbox, Bericht über GoldSentinelTest |
| `CHANGELOG.md`, `CHANGELOG.de.md`, `LICENSE.txt` | Änderungen Englisch und Deutsch, Lizenz «All Rights Reserved (c) GoldSentinel» |

## Regeln, die die Vorlage schon einhält, und die beim Ausbauen gelten

- **Spielversion** nur über `GoldSentinelGame` (`G.IsModern`, `G.IsForever` …). WoW Forever ist der moderne Client und
  darf nie wie Classic Era behandelt werden.
- **Nie eine Blizzard-Funktion ersetzen.** Das gilt auch im Test und auch über eine Hilfsfunktion wie
  `Stub(_G, …)`. Blizzard-Funktionen nur über `ns.API` aufrufen. Im Test nur `ns.API`-Einträge oder eigene Tabellen
  ersetzen. Die Addon-Prüfung meldet sonst einen FEHLER.
- **Aktionen mit Folgen** (Chat, Kaufen, Herstellen, Einladen, Wegpunkte …) nur über `ns.Act`. Im Test werden sie nur
  mitgeschrieben.
- **Geschützte Werte:** Namen von Ziel, Boss oder Fokus und andere Kampfwerte vor dem Vergleichen, Zerlegen oder Benutzen
  als Schlüssel mit `G.IsSecret` prüfen, oder gleich `ns.SafeUnitName` benutzen.
- **Kampflog** nur auf der alten API registrieren (`if G.IsOldAPI then …`). Im modernen Client ist es für Addons zu.
- **Fehler** mit `ns.Try` abfangen. Sie werden gezählt und über GoldSentinelTest an die Prüf-Sitzung gemeldet.
- **Texte** nur über `L`. Jeden neuen Schlüssel in Englisch und Deutsch anlegen, die Testroutine (Bereich F) prüft das.
- **Einstellungen:** Neue Felder in `ns.DEFAULTS` anlegen. Umbauten über `ns.MIGRATIONS` mit höherer `ns.DB_VERSION`,
  nie Daten wegwerfen.
- **Testroutine:** Jede neue Funktion bekommt Fälle in Bereich B, jeder Befund der Prüf-Sitzung einen Fall in Bereich J.
- **Veröffentlichen** wie die anderen Addons: Version in der `.toc` erhöhen, CHANGELOG EN/DE, ZIP nach `download/` bzw.
  `announce/`, vorher `addon_check.py` -> kein FEHLER.
- Neue Addons kommen vor dem Start von WoW Forever nicht auf CurseForge (Entscheid vom 3. November 2026).

## Pflege der Vorlage

Die Vorlage pflegt die Prüf-Sitzung. Die Tests liegen in `shared/tests/test_vorlage.py` und laufen bei jeder
Addon-Prüfung mit:
- Sie erzeugen ein Probe-Addon und prüfen es mit der Addon-Prüfung.
- Sie laden es im nachgebauten Spiel als WoW Forever und als Classic Era, jeweils auf Deutsch und Englisch.
- Sie starten die Testroutine und erwarten 0 FEHLER, Sandbox OK und keine echte Aktion.

Platzhalter in den Vorlagedateien: `__ADDON__`, `__ADDON_KLEIN__`, `__SLASH__`, `__SLASH_GROSS__`, `__FARBE__`, `__ICON__`,
`__KATEGORIE__`, `__BESCHREIBUNG_EN__`, `__BESCHREIBUNG_DE__`.
