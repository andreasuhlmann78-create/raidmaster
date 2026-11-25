# Stand 25.11.2026 17:24 · Version 0.9.87

## Gerade in Arbeit
- Nichts. 0.9.87 veröffentlicht (Discord, Release v0.9.87, Repo bb9d455), Bericht …-version-0.9.87.txt – zur Prüfung.
- 0.9.87 = PS-P1 Teil 1: längster Teil jeder Aufgabe zerlegt im Bericht (Stücke/Rezeptpreise, Rest, Bereinigung, Bild davor, Bilder/s;
  Jobs.lua J.Why, Today.lua misst jeden Rezeptpreis; T300). Nachbau --heute: Teile <= 6,7 ms, 27 ms nicht nachgestellt.
- 0.9.86 (PS-TQ1) veröffentlicht 16:18, zur Prüfung.

## Nächste Schritte (Reihenfolge)
1. PS-P1 Teil 2: Nachbau --only-open zeigt 2 Bilder ~405 ms (Timer RunPendingRefresh UI.lua:3195) und "Öffnen gold" 255 ms; Stapel bei
   100 ms 20× ohne Addon-Zeile (Verdacht: Mock/Nachbau), 4× AD.UpdateCached. Klären (Profil mit Zeit je Ebene, Gegenprobe ohne Mock-Zeichnen).
   Danach mit Ingametest-Zerlegung "Aufgabe heute" Stelle belegen und teilen bzw. als Hinweis mit Grund.
2. PS-TQ1 Abnahme a) mit echten Daten, sobald Herstellen+Entzaubern im Spiel (Bericht "Trefferquote je Beruf").
3. Gilden-Rezepte ohne Realm (Guild.lua; Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
4. MITTEL 2 (T192 Zwischenspeicher 2×, T259), MITTEL 4 (Prüfliste TR, T285).
5. Entwickler-Befehle nur im Entwicklermodus; Hinweis "Test ändert nie Livedaten"; Testort-Hinweis; Lesbarkeit L1–L8.
6. Taschen-Rezepte zeigen "AH ~Preis" – prüfen gegen Direktive "keine geschätzte Zahl".

## Offen beim Nutzer
- Ingametest 0.9.87 "/ps testroutine alles", gern nach normalem Spielen (Zerlegung "Aufgabe heute") (darf im Hintergrund laufen). Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

## Entscheide des Nutzers seit letztem Stand
- 25.11. 13:47 (über Supervisor, PS-TQ1): Trefferquote "echten Weg verfolgen" (umgesetzt 0.9.86).
- 25.11. 16:38: Antworten an den Nutzer immer Deutsch (erinnert).
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
- Arbeitsstand ohne Veröffentlichung: in Zweig pushen (Push auf main mit TOC-Sprung = Release). Zweig löschen geht nicht (403); arbeit-0.9.87 = main.
- Testmeldungen nie mit Cache-Schlüssel/CharKey (T158 Namen). Zeitmessungen offline unter Last unzuverlässig – allein wiederholen.
- Keine geschätzte Zahl auf dem Bildschirm. Nur Windows-1252-Zeichen. Zeiten aus `TZ=Europe/Zurich date`. Alles Sichtbare Deutsch.
