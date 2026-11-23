# Stand 23.11.2026 13:57 · Version 0.9.79

## Gerade in Arbeit
- 0.9.79 veröffentlicht (HOCH 1 Speicher: Liste nur bei Änderung neu), Bericht 2026-11-23-1357-version-0.9.79.txt – zur Prüfung.

## Nächste Schritte (Reihenfolge)
1. HOCH 3: Bilder > 40 ms (T38 541, T292 283, T46 222, T240 103, T243 97, T246 78, T210 75, T255 65, T192 61, T258 52, T256 43) – Ursache je Fall belegen.
2. Gilden-Rezepte ohne Realm (Guild.lua "Realm|Gilde" -> Gilde+Fraktion; Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
3. MITTEL 2 (T192 Zwischenspeicher 2×, T259), MITTEL 4 (Prüfliste TR nicht erneuert, T285).
4. Entwickler-Befehle nur im Entwicklermodus; Hinweis Livedaten/Testort (Rechenzeit je langem Bild, FEHLER nur eigene Arbeit); Lesbarkeit L1–L8.

## Offen beim Nutzer
- Lua-Fehler SetCraftableCount: Messung (nur PS aktiv, /reload, Berufsfenster, Rezept wählen; dann nur AHS).

## Entscheide des Nutzers seit letztem Stand
- Nutzer 23.11. 11:36: in announce/ NICHTS löschen (neue Datei dazu, alte bleibt); 12:03: keine alten Versionen neu posten.
- Supervisor 23.11. 11:40: 0.9.78 angenommen.
- Supervisor 23.11. 10:42: 0.9.77 angenommen, Befunde PS-TBC/PS-L9 (umgesetzt in 0.9.78).
- Supervisor 23.11. 10:22: 0.9.76 angenommen; Einkaufsmenge gelb/grün "mindestens" erlaubt (umgesetzt in 0.9.77); Formel-Chance nur zum Sortieren.

## Wichtig zu wissen
- PS-Repo: Push mit TOC-Versionssprung baut das Release; Asset per REST (gh api …/releases/assets/<id>, Accept octet-stream).
- PS-Remote ohne origin/main-Ref: Push mit `git ls-remote origin refs/heads/main` prüfen.
- Veröffentlichen: download/ProfessionSentinel-<V>.zip (alte Zip in download/ entfernen), announce/professionsentinel__professionsentinel-<V>.md + .ProfessionSentinel.zip NEU dazu – in announce/ NIE löschen/umbenennen.
- Tests: run_offline.py ProfessionSentinel [Versionen] [--lua51] (Standard forever/era/retail; TBC = nicht unterstützt, kein Lauf -> "KEIN ERGEBNIS"), run_smoketest.py (FEHLER 29/26/26 = Mock-Grenzen), yield_check.py ProfessionSentinel, check_actions.py, gen_locale_keys.py.
- Keine geschätzte Zahl auf dem Bildschirm: Zahl je Punkt nur orange (e.exact / e.matExact), Plan gelb/grün = Punkte / "mindestens".
- Rezeptliste: UI.Recorder + UI.CommitList (neuer DataProvider nur bei Änderung, T297); Nachbau echt --only-open misst 20 Refreshes je Teil.
- Testroutine misst zuerst 10 s Umgebung (TR.ENV_SEC); Lifeline-Zeilenzustand in LL.rows, Overlay statt Felder.
- Nur Zeichen aus Windows-1252 in Texten (T295). Skillweg: UI.SkillPath (T296).
