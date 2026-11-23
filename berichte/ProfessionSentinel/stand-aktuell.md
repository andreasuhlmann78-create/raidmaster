# Stand 23.11.2026 08:57 · Version 0.9.75

## Gerade in Arbeit
- 0.9.75 veröffentlicht (Release v0.9.75, download/, announce/), Bericht 2026-11-23-0857-version-0.9.75.txt – zur Prüfung.

## Nächste Schritte (Reihenfolge)
1. HOCH 1: Speicher "Liste recipes" (20 Refreshes ~4,7 MB offline, Spiel 53 MB) – Tabellen in RefreshRecipes wiederverwenden, Ziel ~0 KB, Test mit Gegenprobe.
2. HOCH 3: Bilder > 40 ms (T38 541, T292 283, T46 222, T240 103, T243 97, T246 78, T210 75, T255 65, T192 61, T258 52, T256 43) – Ursache je Fall belegen.
3. Gilden-Rezepte ohne Realm (Guild.lua Schlüssel "Realm|Gilde" -> Gilde+Fraktion, alte Einträge einmal zusammenführen, Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
4. MITTEL 2 (T192 Zwischenspeicher 2× gerechnet, T259), MITTEL 4 (Prüfliste TR im Spiel nicht erneuert, warum T285 es nicht fängt).
5. Entwickler-Befehle nur im Entwicklermodus (19.11.), Hinweis "Test ändert nie Livedaten" (20.11.), Lesbarkeit L1–L8 (20.11.).
6. GoldSentinelTakt 2 unverändert aus shared/, Testroutine mit env = 10, EnvLine() im Bericht; Testort-Hinweis.
7. Planschritte gelb/grün ohne Schätzung ("n Punkte" statt "n×") – im Bericht 0.9.75 Punkt 5 vorgeschlagen.

## Offen beim Nutzer
- Frage Handwerksbuch Punkt 1: Sortierung der Blizzard-Liste geht nicht ohne Änderung an Blizzard-Rahmen – stattdessen in der eigenen PS-Liste?
- Lua-Fehler SetCraftableCount: Messung (nur PS aktiv, /reload, Berufsfenster scrollen; dann nur AHS).

## Entscheide des Nutzers seit letztem Stand
- 23.11. 07:50 Nutzung sparen (nur Nötiges lesen, Punkte bündeln, kurze Berichte).
- 23.11. 08:13 diese Datei führen.

## Wichtig zu wissen
- PS-Repo: Push mit TOC-Versionssprung baut das GitHub-Release; Asset per REST laden (gh release download geht nicht: GraphQL gesperrt).
- Remote PS hat keinen origin/main-Fetch-Ref: Push mit `git ls-remote origin refs/heads/main` prüfen.
- Veröffentlichen: download/ProfessionSentinel-<V>.zip, announce/professionsentinel__professionsentinel-<V>.md + .ProfessionSentinel.zip, alte entfernen.
- Tests: `python3 tests/run_offline.py ProfessionSentinel [forever era retail tbc] [--lua51]`, run_smoketest.py, `yield_check.py ProfessionSentinel`, check_actions.py, gen_locale_keys.py.
- Smoketest-FEHLER 29/26/26 sind Mock-Grenzen (gleich wie 0.9.74).
- Lehrer-Referenz: pipeline/lehrer_forever.json -> lehrer_ref.py -> Data_TrainerRef.lua; Farbstufen: farbstufen.py (alle Versionen).
- Nur Zeichen aus Windows-1252 in Texten (T295).
