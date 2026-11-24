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
- legt alle gemeinsamen Bausteine unverändert aus `shared/` dazu: `GoldSentinelDev`, `GoldSentinelPruefliste`,
  `GoldSentinelGame`, `GoldSentinelSync`, `GoldSentinelTest`, `GoldSentinelMarkt`, `GoldSentinelTakt`, `GoldSentinelCmdHint`
- baut mit `--zip` die ZIP im Aufbau von `download/`

Das fertige Addon lädt sofort im Spiel. Mit `/ls test` läuft die eingebaute Testroutine (in Portionen, ohne Ruckeln).

## Was drin ist

| Datei | Inhalt |
|---|---|
| `<Name>.toc` | alle Clients (Era, Forever 16001, TBC, Wrath, Titan, Cata, Mists, Retail), gemeinsame Dateien zuerst (Dev, Prüfliste, Game, Sync, Test, Markt, Takt, CmdHint), SavedVariables `<Name>DB`, Beschreibung EN/DE |
| `Locales.lua` | Texte als Schlüssel (`L.TITEL`): Englisch als Standard, Deutsch Pflicht, Blöcke für alle weiteren Sprachen |
| `Core.lua` | Namensraum, Version aus der .toc, Einstellungen mit Standardwerten und Migrationen, Ereignisse (`ns:On`), Fehler abfangen und melden (`ns.Try`), Kampfsperre (`ns.WhenOutOfCombat`), schwere Arbeit in Portionen (`ns.Job`, `ns.Check`, `ns.PCall` über GoldSentinelTakt), Testdaten-Regel (`<Name>API.TestRunning()`, `ns.ForeignTestRunning(addon)`), Marktdaten-Netz (`ns.AttachMarket`, Schalter „Marktdaten teilen“), Entwicklermodus (`ns.IsDev`), Prüfliste im Spiel (`/<befehl> prüfliste`, nur Entwickler; Punkte OPT und TEST), Befehlsliste beim Tippen (`ns.CMD_LIST`), Befehl `/<befehl>` mit `help`, `config`, `status`, `minimap`, `protokoll`, `test` |
| `API.lua` | `ns.API`: jede Blizzard-Funktion einmal ausgewählt (modern zuerst, alt als Rückfall), `ns.SafeUnitName` (geschützte Namen), `ns.Act`: einzige Stelle für Aktionen mit Folgen |
| `Options.lua` | Optionen nach Vorbild AHSentinel OPT-1 (Entscheid 18.11.2026 10:27): eigenes Fenster, links Bereiche, rechts eine Spalte (höchstens 12 Zeilen), Suchfeld über alle Bereiche, „Weitere“ eingeklappt, „Standard“ je Bereich, Erklärung im Tooltip. Alles aus einer Liste `ns.OPTIONS` (jede Option genau einmal) und `ns.OPTION_SECTIONS`. Im Einstellungsfenster des Spiels nur ein Knopf „Optionen öffnen“ |
| `UI.lua` | Hauptfenster (verschiebbar, Position gespeichert, Esc schliesst, Inhaltsbereich `ns.content`), Kopierfenster |
| `Minimap.lua` | Button an der Minimap wie bei allen GoldSentinel-Addons: Linksklick Fenster, Rechtsklick Optionen, Ziehen verschiebt; Option und `/<befehl> minimap` zum Ausblenden |
| `Diag.lua` | Diagnose-Protokoll wie bei LevelPilot: `ns.Diag(Art, Text, ms)`, `ns.Timed(Name, fn)` (über 16 ms -> LANGSAM), Fehler aus `ns.Try` automatisch als FEHLER (gleiche nur gezählt); `/<befehl> protokoll` zum Kopieren; beim Ausloggen `GSDIAG1`-Zeichenkette in `<Addon>DB.diagExport` für den Uploader; keine Namen. Testfälle T16/T17 |
| `UICheck.lua` | Oberfläche im echten Client prüfen (Testfälle TK18–TK28, Bereich K; Ausweichen `ns.UIAvoidOthers` und Lesbarkeit L1–L8 siehe unten; eigene Kennungen, damit sie nicht mit T20–T23 aus Bereich C zusammenfallen): eigene Tooltips verdecken keine Knöpfe, kein Überlappen mit Blizzard- oder anderen GoldSentinel-Fenstern, Fenster im Bildschirm, Knopf-Beschriftungen nicht abgeschnitten, Spielwerte plausibel (`ns.Plausible(Name, fn)`), keine Fehlerschleife (> 10×). Eigene Fenster mit `ns.RegisterUI(frame, Name)` anmelden. Ohne echten Client ehrlich übersprungen. Test: `shared/tests/test_uicheck.py` |
| `TestRoutine.lua` | Testroutine nach der Vorgabe der Prüf-Sitzung (Bereiche A–K), läuft als Takt-Aufgabe in Portionen (Testdaten nur während der eigenen Portionen, `Takt.Sliced`), Sandbox (ohne sich selbst ändernde Felder `ns.VOLATILE_KEYS`), Bericht über GoldSentinelTest mit Zeile „Takt“ (Bilder, längstes Bild, über 5/16/40 ms). Optionen-Prüfungen T12, T24–T26, Testdaten-Regel T61, Bausteine T62, Livedaten T63 (jeder Lauf) mit Gegenprobe T64, Aufgabe T71/T72 |
| `CHANGELOG.md`, `CHANGELOG.de.md`, `LICENSE.txt` | Änderungen Englisch und Deutsch, Lizenz «All Rights Reserved (c) GoldSentinel» |

## Regeln, die die Vorlage schon einhält, und die beim Ausbauen gelten

- **Optionen (OPT-ALLE):** Jede neue Einstellung: Standardwert in `ns.DEFAULTS`, EINE Zeile in `ns.OPTIONS` (Bereich, Art
  toggle/choice/number, `advanced = true` für Seltenes), Texte `OPT_<NAME>` (höchstens 28 Zeichen, jede Sprache) und
  `OPT_<NAME>_TIP` (Englisch + Deutsch). Mehr als 11 Optionen in einem Bereich -> neuen Bereich anlegen. Gespeicherte
  Schlüssel nie umbenennen (sonst Migration). T24 prüft das alles.
- **Leistung (shared/wissen/leistung.md):** kein Bild über 40 ms, Ziel ≤ 5 ms. Alles, was über viele Einträge läuft,
  als `ns.Job("Name", fn)` mit `ns.Check("Etikett")` in der Schleife; statt `pcall` in einer Aufgabe `ns.PCall`. Nie
  abgeben in `sort`/`gsub`-Funktionen, Metamethoden, for-in-Iteratoren. Fenster und Bereiche erst beim Zeigen bauen.
- **Testroutine:** schwere Fälle in mehrere Fälle teilen (ein Fall läuft am Stück). Absichtliche Testfehler nur über
  `ns.Try`, NIE über `geterrorhandler()` (öffnet beim Spieler das Fehlerfenster) – der Vorlage-Test zählt das (0 verlangt).
- **Testdaten-Regel (18.11.):** Daten eines anderen GoldSentinel-Addons nie lesen, speichern oder melden, solange
  `ns.ForeignTestRunning("<Addon>")` true ist. Der eigene Test ist über `<Name>API.TestRunning()` sichtbar.
- **Nachbau wie Forever (E-Regel 18.11. 10:30):** Im Forever-Client gibt es die alten globalen Funktionen (GetItemInfo,
  UnitAura, GetSpellInfo, GetAddOnMetadata …) nicht – immer über `ns.API`/C_*. Der Vorlage-Test bildet Forever genau so nach.

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
- **Addon-Kommunikation (Sync) – für ALLE Spielversionen** (Era, TBC/Anniversary, Mists, Retail, Forever), siehe
  `shared/wissen/kommunikation-forever.md`:
  - Nie Daten über einen eigenen Chat-Kanal (`"CHANNEL"`) senden – in WoW Forever kommen sie nicht an.
  - Standardweg überall: `GUILD`, `PARTY`/`RAID`, `WHISPER` an bekannte Mitspieler (gedrosselt).
  - Keinem eigenen Kanal beitreten (max. 10 Kanalplätze). Für Sync nur die gemeinsame Datei `GoldSentinelSync.lua`
    benutzen (liegt in jedem neuen Addon, unverändert aus `shared/`): `local ep = GoldSentinelSync.Register(ADDON,
    "PRAEFIX1", Version)`, `ep:OnMessage(fn)`, `ep:Send(text[, { scope = "guild"|"group" } | { target = Name }])`,
    `ep:Peers(3600)`, `GoldSentinelSync.Ping(ADDON, fn)`, `GoldSentinelSync.DiagLines()` ins Diagnose-Protokoll.
  - **Flüster-Netz (ab GoldSentinelSync 2):** `ep:Send(text)` erreicht auch Spieler ausserhalb von Gilde und Gruppe
    (über bekannte Mitspieler, die weitergeben). Nach dem Laden der SavedVariables einmal `ep:UseStorage(<AddonDB>)`
    aufrufen, damit die bekannten Mitspieler ein `/reload` überstehen. Nachrichten, die nur Gilde/Gruppe betreffen:
    `ep:Send(text, { net = false })`.
  - Fähigkeiten zur Laufzeit erkennen (C_ChatInfo oder alte Funktionen, Kanal verweigert?), nicht nach Version raten;
    Absender mit `G.IsSecret`/`AnySecret` prüfen; was gesendet, empfangen, verworfen wurde ins Diagnose-Protokoll.
  - Die Addon-Prüfung warnt bei `"CHANNEL"`-Addon-Nachrichten und beim Beitreten eigener Kanäle.
- **Fehler** mit `ns.Try` abfangen. Sie werden gezählt und über GoldSentinelTest an die Prüf-Sitzung gemeldet.
- **Texte** nur über `L`. Jeden neuen Schlüssel in Englisch und Deutsch anlegen, die Testroutine (Bereich F) prüft das.
- **Einstellungen:** Neue Felder in `ns.DEFAULTS` anlegen. Umbauten über `ns.MIGRATIONS` mit höherer `ns.DB_VERSION`,
  nie Daten wegwerfen.
- **Testroutine:** Jede neue Funktion bekommt Fälle in Bereich B, jeder Befund der Prüf-Sitzung einen Fall in Bereich J.
- **Veröffentlichen** wie die anderen Addons: Version in der `.toc` erhöhen, CHANGELOG EN/DE, ZIP nach `download/` bzw.
  `announce/`, vorher `addon_check.py` -> kein FEHLER.
- Neue Addons kommen vor dem Start von WoW Forever nicht auf CurseForge (Entscheid vom 3. November 2026).

## Regeln seit 20.11.2026 (in der Vorlage eingebaut bzw. beim Ausbauen einhalten)

- **Test ändert nie Livedaten** (Entscheid des Nutzers 20.11. 08:39, `auftraege/hinweis-test-keine-livedaten-2026-11-20.txt`):
  Vor dem Lauf eine Kopie der eigenen Daten UND der gemeinsamen Tabellen (Sync-Adressbuch `GoldSentinelSync.book`,
  Marktspeicher `GoldSentinelMarkt.store`, jeder `gs*`-Schlüssel der eigenen Datenbank ausser `gsTest`), danach Vergleich.
  Jede Abweichung = FEHLER mit Tabelle und Feld (Spielernamen als `<Name>`), die Daten werden zurückgesetzt (T63, Zeile
  „Livedaten“ im Bericht). Echter Marktempfang während des Laufs ist ein Hinweis, kein FEHLER. Gegenprobe T64 ändert
  absichtlich echte Felder. Netz/Sync im Test nur über Ersatz (Sync 3 hält das Lernen während eines Tests an).
- **Lesbarkeit L1–L8** (Entscheid 20.11. 13:44, `auftraege/hinweis-ui-lesbarkeit-2026-11-20.txt`): TK24 misst im Client
  Kontrast (>= 4,5:1, WCAG 2.1 AA), graue Zahlen, Geldbeträge rechtsbündig, Klammerzahlen ohne Wort, Schrift >= GameFontNormalSmall;
  TK27 rechnet die Gegenproben überall. Jedem Fenster eine feste Hintergrundfarbe geben (`SetBackdropColor`), sonst rechnet
  die Prüfung mit Weiss. Keine grauen „Disable“-Schriften für Texte, die man lesen soll. L3 (gleiche Zahl überall), L4 (Summen
  gehen auf), L5 (eine Hauptzahl), L7 (Unsicheres erzeugt keine Empfehlung) hängen am Inhalt: dafür `ns.ReadCheck(name, fn)`
  anmelden (fn -> ok, ist, soll), TK28 prüft sie.
- **Fenster weichen aus / docken an** (Befunde GS-K1, BS-K1): `ns.UIAvoidOthers(frame)` beim Zeigen jedes eigenen Fensters
  (Haupt-, Kopier- und Optionen-Fenster machen das schon). Hindernisse: offene Blizzard-Fenster (`ns.UI_BLIZZARD`) und sichtbare
  Fenster anderer GoldSentinel-Addons; HUD-Anzeigen (`ns.UI_FOREIGN_HUD`, z. B. LevelPilot-Pfeil) zählen nicht. Erst 8 Pixel
  Abstand, sonst bündig angedockt; nur für die Anzeige, die gespeicherte Lage bleibt. TK25 im Client, TK26 rechnet überall.
- **Schätzen verboten** (Entscheid 21.11. 06:47): keine geschätzte Zahl in Code, Anzeige oder Bericht; jede Zahl mit Quelle
  und Anzahl Fälle. Fehlt eine Messung, im Spiel „noch nicht gemessen“ zeigen.
- **Gemeinschaftsdaten nie nach Realm trennen** (Entscheid 21.11. 16:21): Gilden-, Server- und Marktdaten unter einem
  gemeinsamen Schlüssel; nur Charakter-Daten bleiben je Charakter.
- **Entwickler-Befehle nur im Entwicklermodus** sichtbar und ausführbar (Befehlsliste, Hilfe, Minimap-Tipp; `ns.IsDev`).
- **Spieler-Funktionen nur über normale Wege** (Entscheid 18.11. 11:10): Minimap-Knopf, Hauptfenster, `/<befehl>` und
  `/<befehl> config`, Knopf im Einstellungsfenster des Spiels – nie nur über Testroutine oder Prüfliste.
- **Noch nicht in der Vorlage:** die Unterscheidung „eigene Arbeit / äussere Einflüsse“ (UMG1) kommt erst, wenn sie sich in
  den Addons bewährt hat (Entscheid des Nutzers 24.11. 20:06).

## Pflege der Vorlage

Die Vorlage pflegt die Prüf-Sitzung. Die Tests liegen in `shared/tests/test_vorlage.py` und laufen bei jeder
Addon-Prüfung mit:
- Sie erzeugen ein Probe-Addon und prüfen es mit der Addon-Prüfung.
- Sie laden es im nachgebauten Spiel als WoW Forever und als Classic Era, jeweils auf Deutsch und Englisch.
- Sie starten die Testroutine und erwarten 0 FEHLER, Sandbox OK und keine echte Aktion.

Platzhalter in den Vorlagedateien: `__ADDON__`, `__ADDON_KLEIN__`, `__SLASH__`, `__SLASH_GROSS__`, `__FARBE__`, `__ICON__`,
`__KATEGORIE__`, `__BESCHREIBUNG_EN__`, `__BESCHREIBUNG_DE__`.

## Befehlsliste beim Tippen (CmdHint) – Verhalten (Entscheid des Nutzers, 13.11.2026)

Hat ein Addon eine Befehlsliste über dem Chat-Eingabefeld (Vorbild AHSentinel CmdHint.lua): Ein **Mausklick wählt** einen
Eintrag aus (hervorgehoben, Hinweis "Enter = /befehl …"), **Enter führt aus**. Das Chatfeld wird dabei nie beschrieben
(kein SetText/Insert, nur HookScript lesen, Fokus zurück mit SetFocus); der eigene Slash-Handler führt bei einer frischen
Auswahl (≤ 10 s) den ausgewählten Befehl statt des unvollständigen Worts aus. Die Liste darf sich beim Fokusverlust nicht
schliessen, bevor der Klick ankommt. Einzelheiten und Tests: auftraege/AHSentinel/offen-ahsentinel.txt Punkt CH.
