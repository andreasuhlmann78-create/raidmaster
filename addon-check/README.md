# Addon-Prüfung

Prüft jede Addon-ZIP von GoldSentinel, bevor sie veröffentlicht wird. Entstanden am 2. November 2026, nachdem
mehrere Addons mit eigenen, untereinander unverträglichen Fassungen der gemeinsamen Datei `GoldSentinelGame.lua`
veröffentlicht wurden (eine davon auf CurseForge).

## Was geprüft wird

**Fehler** – das Addon wird **nicht** auf CurseForge hochgeladen, der Lauf wird rot:

| Prüfung | Warum |
|---|---|
| `GoldSentinelGame.lua` weicht von `shared/GoldSentinelGame.lua` ab oder wird im Code nachgebaut | Verschiedene Fassungen mit gleicher Nummer: zufällig gewinnt eine, die anderen Addons bekommen Lua-Fehler |
| `GoldSentinelDev.lua`: gleiche Version, anderer Inhalt | gleiches Problem |
| Versionsnummer nicht höher als eine schon veröffentlichte (Discord, CurseForge) | Spieler mit der höheren Nummer bekommen das Update nie |
| ZIP-Name und `.toc` passen nicht zusammen; `.toc`-Dateien eines Addons mit verschiedener Version | falsche Versionsanzeige, falscher Upload |
| Datei steht in der `.toc`, fehlt aber in der ZIP | Lua-Fehler beim Laden |
| Lua-Syntaxfehler in einer geladenen Datei (geprüft mit Lua 5.1 wie im Spiel) | Addon lädt nicht |
| `GoldSentinelGame.lua` steht in der `.toc` nicht vor den eigenen Dateien | eigene Dateien finden die Erkennung nicht |
| Code ersetzt eine Blizzard-Funktion (`UnitName = …`, `_G.GetServerTime = …`, `C_ChatInfo.SendChatMessage = …`, `function GetRealmName()`), auch nur im Test und auch mit Zurücksetzen (ab 3. November) | "Taint": Die Funktion bleibt bis zum /reload verseucht, Blizzard-Code, der sie danach aufruft, wird blockiert |
| Dasselbe über eine eigene Hilfsfunktion, die `t[k] = v` macht (`Stub(_G, "GetItemInfo", nil)`, `Stub(C_TradeSkillUI, "GetRecipeInfo", f)`); mit einer Variable als Name nur Warnung | wie oben |

**Warnungen** – Upload geht, aber bitte ansehen:

- bekannte Fallen der modernen API (WoW Forever, Retail): alte Funktion ohne Ersatz in derselben Datei, z. B.
  `UnitAura` ohne `C_UnitAuras`, `GetMerchantNumItems` ohne `C_MerchantFrame`, Kampflog ohne Sperre
- Testdatei (`Test.lua`, `SelfTest.lua`, `AutoTest.lua`, `TestMode.lua`, Ordner `Test/`) ruft eine Aktion mit
  Folgen direkt auf: `SendChatMessage`, `BuyMerchantItem`, `RepairAllItems`, `C_TradeSkillUI.Craft…`, Auktionen,
  Gilden- und Gruppen-Einladungen, Quests annehmen/abgeben. Im Test nur mitschreiben (`nachtrag-testroutinen.txt`).
- Name von Ziel, Boss, Fokus oder Mouseover (`UnitName("target")` …) wird ohne Schutzprüfung zerlegt (`:lower()`,
  `strlower`), verglichen (`== "…"`) oder als Tabellenschlüssel benutzt – direkt oder über eine lokale Variable in
  den nächsten 8 Zeilen. In Forever ist er im Kampf geheim. Kein Alarm, wenn die Datei `IsSecret`, `issecretvalue`
  oder `InCombatLockdown` benutzt. Zusammensetzen mit `..` und Weitergeben sind erlaubt.
- `.lua`-Datei liegt in der ZIP, wird aber nie geladen (Werkzeug?) – Syntaxfehler dort nur als Warnung
- keine Interface-Nummer für WoW Forever; `GoldSentinelGame.lua` fehlt oder ist veraltet

## Wann es läuft

- **Vor jedem CurseForge-Upload** (`curseforge/upload.py`): pro Addon – ein fehlerhaftes Addon wird übersprungen,
  die anderen laufen weiter.
- **Bei jedem Push** von ZIPs, `shared/` oder dem Skript (`.github/workflows/addon-check.yml`): prüft alle Addons,
  auch die nur über Discord verteilten (z. B. LevelPilot). Bericht: `addon-check/bericht.md`.
  Von Discord-ZIPs zählt je Addon nur die neueste. Steckt ein Addon inzwischen in einer neueren ZIP derselben
  Reihe (z. B. das frühere Datenpaket `LevelPilot_Data` seit 3.8 in der LevelPilot-ZIP), wird die alte Einzel-ZIP
  nicht mehr geprüft – sie ist nur noch Archiv. Von Hand mit Pfad aufgerufen wird sie trotzdem geprüft.
- **Im Discord-Bot** (`RaidMasterBot/updater.py`, ab Bot 1.5.92): Beim Übernehmen eines Updates wird jede NEUE
  Addon-ZIP geprüft – aus `download/`, die neueste ZIP je Addon in `announce/` und die gebaute RaidMaster-ZIP.
  Mit Fehlern wird sie nicht übernommen und nicht gepostet (bei Ankündigungen samt Text und Anhängen); im
  Bot-Kanal erscheint "🛑 Addon-Prüfung: … NICHT veröffentlicht" mit den Fehlern. Die Regeln kommen immer aus
  derselben Repo-Version (`addon-check/addon_check.py`).
- **Von Hand**: `pip install lupa`, dann `python3 addon-check/addon_check.py` (alle) oder mit ZIP-Pfaden.
  Am besten vor jedem Push: `python3 addon-check/addon_check.py download/MeinAddon-x.y.z.zip`.

## Gemeinsame Dateien (`shared/`)

- `shared/GoldSentinelGame.lua` ist die **einzige** Vorlage. Addons kopieren sie unverändert.
- Ändern nur hier, mit höherer `VERSION`, dann `python3 -I shared/tests/test_goldsentinelgame.py`
  (muss "bestanden" melden) und die neue Fassung in alle Addons kopieren.
- Die bisherige Fassung als `shared/tests/variants/GoldSentinelGame-v<N>.lua` ablegen. Kopien davon gelten dann
  als "veraltet" (Warnung) statt als "abweichend" (Fehler), und die Tests prüfen das Zusammenspiel.

## Erweitern

Neue Falle: Liste `TRAPS` in `addon_check.py` (Muster, Ersatz in derselben Datei, Erklärung).
Weitere geschützte Blizzard-Funktion: Liste `BLIZZ_GLOBALS`. Weitere Aktion für Testdateien: `TEST_ACTIONS`.
Strings und Kommentare blendet `lua_blank()` vorher aus, damit Hilfetexte keinen Alarm auslösen.
Schon veröffentlichte Version, die eine neue FEHLER-Regel verletzt: in `ALTLAST` eintragen (dort nur Warnung, die
nächste Version bekommt den Fehler). Eintrag entfernen, sobald die Version aus `download/` verschwunden ist.
Tests der Regeln: `python3 addon-check/test_addon_check_regeln.py` (Treffer und Fehlalarm-Fälle je Regel).
Neue gemeinsame Datei: Liste `SHARED` (Regel `exact` oder `version`).

## Testberichte aus dem Spiel (`shared/GoldSentinelTest.lua`)

Jedes Addon kopiert `shared/GoldSentinelTest.lua` unverändert (Regel `exact`, in der `.toc` direkt nach
`GoldSentinelGame.lua`). Damit schreiben die Testroutinen im Spiel ihre Ergebnisse und die abgefangenen Lua-Fehler in
die SavedVariables. Der RaidMasterUploader schickt sie an Discord #testberichte, der Workflow `testberichte.yml` holt
sie nach `testberichte/` (Skript `addon-check/testberichte.py`, Tests `addon-check/test_testberichte.py`).
Fehlt die Datei in einem Addon, meldet die Prüfung eine Warnung. Ändern nur hier, mit höherer `VERSION`, danach
`python3 -I shared/tests/test_goldsentineltest.py`.

