# Stand 24.11.2026 06:40 · Version 0.9.79

## Gerade in Arbeit
- Nichts angefangen. 0.9.79 veröffentlicht (HOCH 1: Rezeptliste nur bei Änderung neu), Bericht 2026-11-23-1357-version-0.9.79.txt – zur Prüfung.
- NEU im Repo, noch NICHT gelesen/umgesetzt: Ingametest 0.9.78 (Commit 1cc023cb) in auftraege/ProfessionSentinel/offen-professionsentinel.txt:
  PS-I1 HOCH (Bilder > 40 ms: T81 53, T260 52, T43 49 ms), PS-I2 MITTEL (T219 4 Aufbauten beim Herstellen, soll <= 1 je 2 s),
  PS-I3 MITTEL (T85 Hinweis "keine Zeilen"; T236 Tooltip ohne Shift 15 Zeilen, Regel T-TT1), PS-I4 NIEDRIG (Dauer 333 s > 300 s;
  "Trefferquote Schneiderei 0/186" erklären).

## Nächste Schritte (Reihenfolge)
1. git pull --rebase, offen-professionsentinel.txt ganz lesen (PS-I1..I4 genau), dann PS-I1 zusammen mit HOCH 3 (Bilder > 40 ms:
   T38 541, T292 283, T46 222, T240 103, T243 97, T246 78, T210 75, T255 65, T192 61, T258 52, T256 43) – Ursache je Fall belegen.
2. PS-I2, PS-I3, PS-I4 (in eine Version bündeln).
3. Gilden-Rezepte ohne Realm (Guild.lua "Realm|Gilde" -> Gilde+Fraktion; Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
4. MITTEL 2 (T192 Zwischenspeicher 2×, T259), MITTEL 4 (Prüfliste TR im Spiel nicht erneuert, warum T285 es nicht fängt).
5. Entwickler-Befehle nur im Entwicklermodus (19.11., Liste im Bericht); Hinweis "Test ändert nie Livedaten" (20.11.); Testort-Hinweis
   (Rechenzeit je langem Bild, FEHLER nur eigene Arbeit über Grenze); Lesbarkeit L1–L8 (20.11.).
6. Falls Ingametest T145 andere Reiter als Speicher-Täter zeigt: gleiche Technik (UI.Recorder/CommitList) dort.

## Offen beim Nutzer
- Lua-Fehler RecipeList SetCraftableCount: Messung (nur PS aktiv, /reload, Berufsfenster, Rezept wählen; dann nur AHS). Bis dahin Verdacht.
- Ingametest 0.9.79 mit "/ps testroutine alles": T145 zeigt "Liste behalten x, neu y" und "angelegt je Teil" (sind die 53 MB weg?).

## Entscheide des Nutzers seit letztem Stand
- 23.11. 11:36: in announce/ NICHTS löschen oder umbenennen – neue Version = neue Dateien dazu, alte bleiben.
- 23.11. 12:03: keine alten Versionen neu posten.
- 23.11. 07:50: Nutzung sparen (nur Nötiges lesen, Punkte bündeln, kurze Berichte, keine Zwischenmeldungen ohne Neues).
- 23.11. 08:13: diese Datei führen (nach jedem erledigten Schritt ganz neu, <= 60 Zeilen).
- Supervisor 23.11.: 0.9.75–0.9.78 angenommen; Sortierung nur in eigener Liste (Skillweg); Planschritte gelb/grün "n Punkte";
  Einkaufsmenge gelb/grün "mindestens" (ohne "~"); Formel-Chance nur intern zum Sortieren; PS-TAKT3 (Takt v3, Umgebung 10 s).

## Wichtig zu wissen
- Repos: /home/claude/professionsentinel (Push mit TOC-Versionssprung baut Release; kein origin/main-Ref -> `git ls-remote origin refs/heads/main`),
  /home/claude/raidmaster (öffentlich; auftraege/ nur Supervisor; Berichte berichte/ProfessionSentinel/<JJJJ-MM-TT>-<HHMM>-<thema>.txt).
- Release-Asset per REST: `gh api …/releases/tags/vX --jq '.assets[0].id'`, dann `gh api -H "Accept: application/octet-stream" …/releases/assets/<id>`.
- Veröffentlichen: download/ProfessionSentinel-<V>.zip (alte Zip in download/ entfernen), announce/professionsentinel__professionsentinel-<V>.md
  + <V>.ProfessionSentinel.zip NEU dazu. addon_check vor dem Push: kein FEHLER.
- Tests: run_offline.py ProfessionSentinel [forever era retail] [--lua51] (TBC nicht unterstützt -> "KEIN ERGEBNIS", nur auf Aufruf),
  run_smoketest.py (FEHLER 29/26/26 = Mock-Grenzen, Liste EXPECTED_FAIL), yield_check.py ProfessionSentinel, check_actions.py, gen_locale_keys.py.
- Nachbau echt: tests/nachbau_echt.py ProfessionSentinel <AHS-Ordner> /home/claude/goldsentinel-daten/aktuell/DESKTOP-NVITMSE/forever/konto-5cb3d536
  --only-open --mb 0 (misst 20 Refreshes je Teil; AHS-Zip aus raidmaster/download entpacken).
- Keine geschätzte Zahl auf dem Bildschirm: Zahl je Punkt nur orange (e.exact/e.matExact), Plan gelb/grün Punkte/"mindestens", Chance nur gemessen.
- Rezeptliste: UI.Recorder + UI.CommitList (T297); Lifeline-Zeilenzustand in LL.rows + Overlay (keine Felder an Blizzard-Zeilen).
- Nur Zeichen aus Windows-1252 in Texten (T295). Skillweg UI.SkillPath (T296). Lehrer-Ränge: lehrer_ref.py -> Data_TrainerRef.lua (T294).
- Testroutine misst zuerst 10 s Umgebung (TR.ENV_SEC, Smoketest 0). Zeiten immer aus `TZ=Europe/Zurich date`. Alles Sichtbare Deutsch.
