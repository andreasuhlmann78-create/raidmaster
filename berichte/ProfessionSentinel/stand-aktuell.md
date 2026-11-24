# Stand 24.11.2026 14:44 · Version 0.9.82

## Gerade in Arbeit
- Nichts. 0.9.82 veröffentlicht (Discord, Release v0.9.82, Repo 0a9ee07), Bericht 2026-11-24-1444-version-0.9.82.txt – zur Prüfung.
- Umgesetzt: PS-I5 (Rezeptliste nach Inhalt vergleichen, SAME_DEPTH 6; T297 mit Preisen stellt den Ingame-Fehler nach), PS-I1
  (ns.TaktCheck liest die Uhr VOR GoldSentinelTakt.Check – falsch "gehaltene" Teile), T88 (echte Verzauberer-Wahl), T85 Fensterantwort.

## Nächste Schritte (Reihenfolge)
1. Ingametest 0.9.82 lesen (goldsentinel-daten, ProfessionSentinel.lua.gz, ["last"]): PS-I1 je Fall (Etikett + "gehalten"-Stelle),
   T255 (GC 135 MB im Teil), T189 59 ms, T140/T219 knapp über 16 ms, T85.
2. PS-I8: T269 Aufruf <= 2 ms (TD.Candidates rechnet Taschen/Gold je Aufruf neu), T139 19,8 ms, WEGE "Aufgabe heute" 23,3 ms.
3. Trefferquote (PM6) nach Entscheid des Nutzers (A/B/C).
4. Gilden-Rezepte ohne Realm (Guild.lua; Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
5. MITTEL 2 (T192 Zwischenspeicher 2×, T259), MITTEL 4 (Prüfliste TR, T285).
6. Entwickler-Befehle nur im Entwicklermodus; Hinweis "Test ändert nie Livedaten"; Testort-Hinweis; Lesbarkeit L1–L8.
7. Taschen-Rezepte zeigen "AH ~Preis" – prüfen gegen Direktive "keine geschätzte Zahl".

## Offen beim Nutzer
- ENTSCHEID Trefferquote (Schneiderei 0/186 zählt Skill-/Zwischenprodukte als Fehlschlag): A nicht verkauft = nicht zählen ·
  B nur Herstellungen ohne Skillpunkt · C wie bisher.
- Frage: welches Berufsfenster war bei T85 offen (0.9.80 Krieger ohne Beruf, 0.9.81 Priester mit VZ/Schneiderei/Kochen)?
- Ingametest 0.9.82 "/ps testroutine alles". Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

## Entscheide des Nutzers seit letztem Stand
- keine neuen.
- Weiter gültig: 23.11. 11:36 announce/ nichts löschen; 12:03 keine alten Versionen neu posten; 07:50 Nutzung sparen; 08:13 diese
  Datei; Supervisor 23.11.: Skillweg-Sortierung eigene Liste, gelb/grün "n Punkte"/"mindestens" ohne "~", Formel-Chance intern, PS-TAKT3.

## Wichtig zu wissen
- Repos: /home/claude/professionsentinel (Remote andreasuhlmann78-create/ProfessionSentinel; Push mit TOC-Sprung baut Release;
  Prüfung `git ls-remote origin refs/heads/main`), /home/claude/raidmaster (öffentlich; auftraege/ nur Supervisor).
- Ingametest-Bericht: goldsentinel-daten/aktuell/AUSPLUSLAPTOP/forever/<konto>/ProfessionSentinel.lua.gz, Zeile ["last"] (unicode_escape).
- Release-Asset: `gh api repos/<R>/releases/tags/vX --jq '.assets[0].id'`, dann mit Accept octet-stream laden.
- Veröffentlichen: download/ProfessionSentinel-<V>.zip (alte entfernen), announce/…-<V>.md + <V>.ProfessionSentinel.zip NEU dazu. addon_check vorher.
- Nachbau echt: `tests/nachbau_echt.py ProfessionSentinel /home/claude/ahanalyzerpro <sv> --mb 150 --area b` (~10 min); --profile zu langsam.
  Offline-Profil je Fall: scratchpad prof.py (debug.sethook, nur während des Falls).
- Zeitmessungen offline unter Last unzuverlässig – allein wiederholen. Smoketest ~20 min, FEHLER 29/26/26 = Mock-Grenzen.
- Keine geschätzte Zahl auf dem Bildschirm. Nur Windows-1252-Zeichen. Zeiten aus `TZ=Europe/Zurich date`. Alles Sichtbare Deutsch.
