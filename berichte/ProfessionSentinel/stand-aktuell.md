# Stand 23.11.2026 09:50 · Version 0.9.76

## Gerade in Arbeit
- 0.9.76 veröffentlicht (Release v0.9.76, download/, announce/), Bericht 2026-11-23-0950-version-0.9.76.txt – zur Prüfung.

## Nächste Schritte (Reihenfolge)
1. HOCH 1: Speicher "Liste recipes" (offline ~4,7 MB / 20 Refreshes, Spiel 53 MB) – Tabellen in RefreshRecipes wiederverwenden, Ziel ~0 KB, Test mit Gegenprobe.
2. HOCH 3: Bilder > 40 ms (T38 541, T292 283, T46 222, T240 103, T243 97, T246 78, T210 75, T255 65, T192 61, T258 52, T256 43) – Ursache je Fall belegen.
3. Gilden-Rezepte ohne Realm (Guild.lua "Realm|Gilde" -> Gilde+Fraktion; Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
4. MITTEL 2 (T192 Zwischenspeicher 2×, T259), MITTEL 4 (Prüfliste TR nicht erneuert, T285).
5. Entwickler-Befehle nur im Entwicklermodus; Hinweis Livedaten/Testort (Rechenzeit je langem Bild, FEHLER nur eigene Arbeit); Lesbarkeit L1–L8.

## Offen beim Nutzer
- Lua-Fehler SetCraftableCount: Messung (nur PS aktiv, /reload, Berufsfenster scrollen/Rezept wählen; dann nur AHS).
- Frage im Bericht 0.9.76: Einkaufsmenge des Plans bei gelb/grün als "mindestens" kennzeichnen?

## Entscheide des Nutzers seit letztem Stand
- Supervisor 23.11. 09:30: Sortierung in die eigene Liste (umgesetzt), Planschritte "n Punkte" (umgesetzt), PS-TAKT3 Pflicht (umgesetzt).

## Wichtig zu wissen
- PS-Repo: Push mit TOC-Versionssprung baut das Release; Asset per REST (gh api …/releases/assets/<id>, Accept octet-stream).
- PS-Remote ohne origin/main-Ref: Push mit `git ls-remote origin refs/heads/main` prüfen.
- Veröffentlichen: download/ProfessionSentinel-<V>.zip, announce/professionsentinel__professionsentinel-<V>.md + .ProfessionSentinel.zip (git mv), alte entfernen.
- Tests: run_offline.py ProfessionSentinel [Versionen] [--lua51], run_smoketest.py (FEHLER 29/26/26 = Mock-Grenzen), yield_check.py ProfessionSentinel, check_actions.py, gen_locale_keys.py.
- Testroutine misst zuerst 10 s Umgebung (TR.ENV_SEC); Lifeline-Zeilenzustand in LL.rows (schwache Schlüssel), Overlay statt Felder.
- Nur Zeichen aus Windows-1252 in Texten (T295). Skillweg: UI.SkillPath (T296).
