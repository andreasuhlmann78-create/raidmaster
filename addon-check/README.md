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

**Warnungen** – Upload geht, aber bitte ansehen:

- bekannte Fallen der modernen API (WoW Forever, Retail): alte Funktion ohne Ersatz in derselben Datei, z. B.
  `UnitAura` ohne `C_UnitAuras`, `GetMerchantNumItems` ohne `C_MerchantFrame`, Kampflog ohne Sperre
- `.lua`-Datei liegt in der ZIP, wird aber nie geladen (Werkzeug?) – Syntaxfehler dort nur als Warnung
- keine Interface-Nummer für WoW Forever; `GoldSentinelGame.lua` fehlt oder ist veraltet

## Wann es läuft

- **Vor jedem CurseForge-Upload** (`curseforge/upload.py`): pro Addon – ein fehlerhaftes Addon wird übersprungen,
  die anderen laufen weiter.
- **Bei jedem Push** von ZIPs, `shared/` oder dem Skript (`.github/workflows/addon-check.yml`): prüft alle Addons,
  auch die nur über Discord verteilten (z. B. LevelPilot). Bericht: `addon-check/bericht.md`.
- **Von Hand**: `pip install lupa`, dann `python3 addon-check/addon_check.py` (alle) oder mit ZIP-Pfaden.

**Wichtig:** Der Discord-Bot holt neue ZIPs selbst aus dem Repo und wartet nicht auf die Prüfung.
Deshalb vor dem Push selbst prüfen: `python3 addon-check/addon_check.py download/MeinAddon-x.y.z.zip`.

## Gemeinsame Dateien (`shared/`)

- `shared/GoldSentinelGame.lua` ist die **einzige** Vorlage. Addons kopieren sie unverändert.
- Ändern nur hier, mit höherer `VERSION`, dann `python3 -I shared/tests/test_goldsentinelgame.py`
  (muss "bestanden" melden) und die neue Fassung in alle Addons kopieren.
- Die bisherige Fassung als `shared/tests/variants/GoldSentinelGame-v<N>.lua` ablegen. Kopien davon gelten dann
  als "veraltet" (Warnung) statt als "abweichend" (Fehler), und die Tests prüfen das Zusammenspiel.

## Erweitern

Neue Falle: Liste `TRAPS` in `addon_check.py` (Muster, Ersatz in derselben Datei, Erklärung).
Neue gemeinsame Datei: Liste `SHARED` (Regel `exact` oder `version`).
