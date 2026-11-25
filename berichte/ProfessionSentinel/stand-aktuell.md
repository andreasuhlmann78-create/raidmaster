# Stand 25.11.2026 16:18 · Version 0.9.86

## Gerade in Arbeit
- Nichts. 0.9.86 veröffentlicht (Discord, Release v0.9.86, Repo 3775878), Bericht 2026-11-25-1618-version-0.9.86.txt – zur Prüfung.
- 0.9.85 angenommen und im Spiel BESTANDEN (Supervisor 16:06: OK 257/FEHLER 0, 214 s, UMG1 im Spiel belegt). 0.9.86: PS-TQ1 (Weg je
  Stück: entzaubert über AHSentinel.API.Disenchanted ab 0.65.402, verkauft, Zwischenprodukt z, ohne Weg u; MK.MigrateHits beim Login
  sichert die alte Regel in pmHits.old; T299).

## Nächste Schritte (Reihenfolge)
1. PS-P1 MITTEL (Supervisor 16:06): Aufgabe "heute" Teil 27,2 ms ×13 (Ziel 16) – mit UMG1 prüfen, ob Hintergrund; sonst Stück belegen
   (Stelle) und teilen; Gegenprobe im Nachbau mit echten Daten. Dazu Spielwege in Testschritten (Panel-Aufbau, Ansicht recipes T123/T126/
   T130/T133/T134) belegen, ob beim Spielen auch so lang; Testhilfen im Bericht als Testhilfe kennzeichnen.
2. PS-TQ1 Abnahme a) mit echten Daten, sobald Herstellen+Entzaubern im Spiel (Bericht "Trefferquote je Beruf").
3. Gilden-Rezepte ohne Realm (Guild.lua; Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
4. MITTEL 2 (T192 Zwischenspeicher 2×, T259), MITTEL 4 (Prüfliste TR, T285).
5. Entwickler-Befehle nur im Entwicklermodus; Hinweis "Test ändert nie Livedaten"; Testort-Hinweis; Lesbarkeit L1–L8.
6. Taschen-Rezepte zeigen "AH ~Preis" – prüfen gegen Direktive "keine geschätzte Zahl".

## Offen beim Nutzer
- Ingametest 0.9.86 "/ps testroutine alles" (darf im Hintergrund laufen). Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

## Entscheide des Nutzers seit letztem Stand
- 25.11. 13:47 (über Supervisor, PS-TQ1): Trefferquote "echten Weg verfolgen" – siehe Schritt 3.
- 25.11. 09:03: Ingametests laufen im Hintergrund ("ich lasse das wow fenster nicht offen ich bin am arbeiten") -> UMG1 vorgezogen (umgesetzt 0.9.84).
- Weiter gültig: 23.11. 11:36 announce/ nichts löschen; 12:03 keine alten Versionen neu posten; 07:50 Nutzung sparen; 08:13 diese
  Datei; Supervisor 23.11.: Skillweg-Sortierung eigene Liste, gelb/grün "n Punkte"/"mindestens" ohne "~", Formel-Chance intern, PS-TAKT3.

## Wichtig zu wissen
- Repos: /home/claude/professionsentinel (Remote andreasuhlmann78-create/ProfessionSentinel; Push mit TOC-Sprung baut Release;
  Prüfung `git ls-remote origin refs/heads/main`), /home/claude/raidmaster (öffentlich; auftraege/ nur Supervisor).
- Ingametest-Bericht: goldsentinel-daten/aktuell/<PC>/forever/<konto>/ProfessionSentinel.lua.gz, Zeile ["last"] (unicode_escape).
- Release-Asset: `gh api repos/<R>/releases/tags/vX --jq '.assets[0].id'`, dann mit Accept octet-stream laden.
- Veröffentlichen: download/ProfessionSentinel-<V>.zip (alte entfernen), announce/…-<V>.md + <V>.ProfessionSentinel.zip NEU dazu. addon_check vorher.
- Nachbau echt: `tests/nachbau_echt.py ProfessionSentinel /home/claude/ahanalyzerpro <sv> --mb 150 --area b` (~10 min).
- Testmeldungen nie mit Cache-Schlüssel/CharKey (T158 Namen). Zeitmessungen offline unter Last unzuverlässig – allein wiederholen.
- Keine geschätzte Zahl auf dem Bildschirm. Nur Windows-1252-Zeichen. Zeiten aus `TZ=Europe/Zurich date`. Alles Sichtbare Deutsch.
