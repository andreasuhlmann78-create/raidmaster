# Stand 24.11.2026 08:48 · Version 0.9.80

## Gerade in Arbeit
- Nichts. 0.9.80 veröffentlicht (Discord, Release v0.9.80, Repo 7b504b4), Bericht 2026-11-24-0848-version-0.9.80.txt – zur Prüfung.
- Umgesetzt: SH-V3/PS-V3 (GoldSentinelTest v3, Prüfung >= 2), PS-I2 (Test-Protokollfehler, Zeitgeber T214/T215, 2-s-Abstand auch
  nach dem Herstellen), PS-I3 T236 + T198 belegt und behoben, PS-I4 Dauer (T219/T275 Bildgrenze), PS-I1 nur Messung (Zerlegung).

## Nächste Schritte (Reihenfolge)
1. Nach Ingametest 0.9.80: PS-I1/HOCH 3 je Fall lösen (Zeile "Längster Teil … zerlegt": unser Code / Blizzard-Liste / Bereinigung).
   T85 mit neuer Meldung zuordnen; T219-Anlässe prüfen; Dauer gegen 300 s.
2. Trefferquote (PM6) nach Entscheid des Nutzers umbauen (A/B/C, alte 186 mit Sicherung zurücksetzen).
3. Gilden-Rezepte ohne Realm (Guild.lua "Realm|Gilde" -> Gilde+Fraktion; Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
4. MITTEL 2 (T192 Zwischenspeicher 2×, T259), MITTEL 4 (Prüfliste TR im Spiel nicht erneuert, warum T285 es nicht fängt).
5. Entwickler-Befehle nur im Entwicklermodus (19.11.); Hinweis "Test ändert nie Livedaten" (20.11.); Testort-Hinweis; Lesbarkeit L1–L8.
6. Falls T145 andere Reiter als Speicher-Täter zeigt: UI.Recorder/CommitList dort.

## Offen beim Nutzer
- ENTSCHEID Trefferquote: Schneiderei 0/186 zählt Herstellungen zum Skillen/Zwischenprodukte als Fehlschlag -> "Unsicher" in jedem
  Schneiderei-Tooltip. A nicht verkauft = nicht zählen · B nur Herstellungen ohne Skillpunkt · C wie bisher.
- Ingametest 0.9.80 "/ps testroutine alles" (auch T145 "Liste behalten x, neu y").
- Lua-Fehler SetCraftableCount: Messung (nur PS aktiv, /reload, Berufsfenster, Rezept wählen; dann nur AHS). Bis dahin Verdacht.

## Entscheide des Nutzers seit letztem Stand
- keine neuen.
- Weiter gültig: 23.11. 11:36 announce/ nichts löschen; 12:03 keine alten Versionen neu posten; 07:50 Nutzung sparen; 08:13 diese
  Datei; Supervisor 23.11.: 0.9.75–0.9.78 angenommen, Skillweg-Sortierung eigene Liste, gelb/grün "n Punkte"/"mindestens" ohne "~",
  Formel-Chance nur intern, PS-TAKT3.

## Wichtig zu wissen
- Repos: /home/claude/professionsentinel (Remote jetzt andreasuhlmann78-create/ProfessionSentinel; Push mit TOC-Sprung baut Release;
  Prüfung `git ls-remote origin refs/heads/main`), /home/claude/raidmaster (öffentlich; auftraege/ nur Supervisor).
- Release-Asset: `gh api repos/<R>/releases/tags/vX --jq '.assets[0].id'`, dann `gh api -H "Accept: application/octet-stream" …/releases/assets/<id>`.
- Veröffentlichen: download/ProfessionSentinel-<V>.zip (alte entfernen), announce/…-<V>.md + <V>.ProfessionSentinel.zip NEU dazu. addon_check vorher.
- Tests: run_offline.py ProfessionSentinel [forever era retail] [--lua51]; run_smoketest.py ProfessionSentinel [Flavor…] (dauert ~15 min,
  FEHLER 29/26/26 = Mock-Grenzen); yield_check, check_actions, gen_locale_keys; nachbau_testroutine.py (--runs 1 --mb 250).
- Zeitmessungen offline bei parallel laufendem Smoketest unzuverlässig (T257 9,6 ms) – allein wiederholen.
- Neu: UI SetDP misst SetDataProvider (ns.listMs); Core ns.TaktPortionStart/End; Diagnose D.ErrorStore(); T219 zählt Aufbauten nach gen.
- Keine geschätzte Zahl auf dem Bildschirm. Nur Windows-1252-Zeichen in Texten. Zeiten aus `TZ=Europe/Zurich date`. Alles Sichtbare Deutsch.
