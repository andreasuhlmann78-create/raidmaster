# Stand 24.11.2026 12:01 · Version 0.9.81

## Gerade in Arbeit
- Nichts. 0.9.81 veröffentlicht (Discord, Release v0.9.81, Repo 9664ced), Bericht 2026-11-24-1201-version-0.9.81.txt – zur Prüfung.
- Umgesetzt aus Ingametest 0.9.80: PS-I2 (kein Aufbau ohne Anlass, gapHold nach Schluss-Aufbau), PS-I6 (T33 ohne Preis-Addon, belegt),
  PS-I7 (T243/T276 ohne Alarm-/Taschen-Blöcke, im Nachbau belegt), PS-I3 (T85: Krieger ohne Beruf). PS-I5/PS-I1: nur Messung
  (T297-Meldung mit allen Teilen, Etikett je Stück in "zerlegt").

## Nächste Schritte (Reihenfolge)
1. Nach Ingametest 0.9.81: PS-I5 (T297-Meldung lesen), PS-I1 je Fall (Etikett zeigt das Stück) – lösen.
2. PS-I8: T269 Aufruf <= 2 ms (TD.Candidates rechnet Taschen/Gold je Aufruf neu -> Zwischenspeicher mit Taschen-Stempel),
   T139 recipes 19,8 ms (Portion), WEGE "Aufgabe heute" 23,3 ms.
3. Trefferquote (PM6) nach Entscheid des Nutzers (A/B/C).
4. Gilden-Rezepte ohne Realm (Guild.lua; Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
5. MITTEL 2 (T192 Zwischenspeicher 2×, T259), MITTEL 4 (Prüfliste TR, T285).
6. Entwickler-Befehle nur im Entwicklermodus; Hinweis "Test ändert nie Livedaten"; Testort-Hinweis; Lesbarkeit L1–L8.
7. Aufgefallen: Taschen-Rezepte zeigen "AH ~Preis" (Zeichen "~" = geschätzt?) – prüfen gegen Direktive "keine geschätzte Zahl".

## Offen beim Nutzer
- ENTSCHEID Trefferquote (Schneiderei 0/186 zählt Skill-/Zwischenprodukte als Fehlschlag): A nicht verkauft = nicht zählen ·
  B nur Herstellungen ohne Skillpunkt · C wie bisher.
- Frage: welches Fenster war bei T85 offen (Krieger ohne Beruf)?
- Ingametest 0.9.81 "/ps testroutine alles". Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

## Entscheide des Nutzers seit letztem Stand
- keine neuen.
- Weiter gültig: 23.11. 11:36 announce/ nichts löschen; 12:03 keine alten Versionen neu posten; 07:50 Nutzung sparen; 08:13 diese
  Datei; Supervisor 23.11.: Skillweg-Sortierung eigene Liste, gelb/grün "n Punkte"/"mindestens" ohne "~", Formel-Chance intern, PS-TAKT3.

## Wichtig zu wissen
- Repos: /home/claude/professionsentinel (Remote andreasuhlmann78-create/ProfessionSentinel; Push mit TOC-Sprung baut Release;
  Prüfung `git ls-remote origin refs/heads/main`), /home/claude/raidmaster (öffentlich; auftraege/ nur Supervisor).
- Release-Asset: `gh api repos/<R>/releases/tags/vX --jq '.assets[0].id'`, dann mit Accept octet-stream laden.
- Veröffentlichen: download/ProfessionSentinel-<V>.zip (alte entfernen), announce/…-<V>.md + <V>.ProfessionSentinel.zip NEU dazu. addon_check vorher.
- Nachbau echt: SV aus goldsentinel-daten (jetzt .lua.gz -> entpacken nach scratchpad/sv), AHS aus /home/claude/ahanalyzerpro;
  `tests/nachbau_echt.py ProfessionSentinel <AHS> <sv> --mb 150 --area b [--show T297] [--overrun 30]` (~10 min je Bereich;
  --profile ist zu langsam). Bereich allein gibt andere Zeiten als der volle Lauf (T134 16 statt 76 ms).
- Zeitmessungen offline unter Last unzuverlässig (T257, T269) – allein wiederholen. Smoketest ~20 min, FEHLER 29/26/26 = Mock-Grenzen.
- Keine geschätzte Zahl auf dem Bildschirm. Nur Windows-1252-Zeichen. Zeiten aus `TZ=Europe/Zurich date`. Alles Sichtbare Deutsch.
