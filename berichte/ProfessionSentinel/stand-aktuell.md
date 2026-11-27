# Stand 27.11.2026 07:35 · Version 0.9.91

## Gerade in Arbeit
- Nichts. 0.9.91 veröffentlicht (Discord, Release v0.9.91, Repo b180313), Bericht 2026-11-27-0735-version-0.9.91.txt – zur Prüfung.
- 0.9.91 = PS-P1 (Ursache im Spiel belegt 27.11. 07:00: AHSentinel.API.WorthUpTo 18,4 ms): P.Worth je Item gemerkt bis PS.OnChanged/
  Händler, in "heute" je neues WorthUpTo allein im Teil (J.Hand davor > 0,5 ms und danach); T302. Nachbau: Teil max 2,1 ms.
- 0.9.90 angenommen (26.11. 13:12), PS-REALM im Spiel BESTANDEN. AHS-API1 (WorthUpTo billiger) liegt bei AHSentinel.

## Nächste Schritte (Reihenfolge)
1. Abnahme PS-P1 aus dem nächsten Diagnose-Export (Schneider-Figur): Teil max ≈ WorthUpTo-Zeit, kein PS-Code dazu.
   Danach Ansicht recipes im Nachbau (2 Bilder ~405 ms, Stapel 20x ohne Addon-Zeile = Verdacht Mock).
2. AHS-BP1 für PS: gebundene Ware (bindType 1) nicht als AH-Ware empfehlen; Test bindType 1/0/2 + Gegenprobe. Daten nicht ändern.
3. PS-TQ1 Abnahme a) mit echten Daten, sobald Herstellen+Entzaubern im Spiel (Bericht "Trefferquote je Beruf").
4. Gilden-Sync-Tag ohne Realm prüfen.
5. MITTEL 2 (T192, T259), MITTEL 4 (T285); Entwickler-Befehle nur im Entwicklermodus; Testort-Hinweis; Lesbarkeit L1–L8; "AH ~Preis".

## Offen beim Nutzer
- Ingametest 0.9.91 "/ps testroutine alles" (darf im Hintergrund laufen); Einloggen mit der Schneider-Figur reicht für PS-P1 (darf im Hintergrund laufen). Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

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
- Nachbau echt: `tests/nachbau_echt.py ProfessionSentinel /home/claude/ahanalyzerpro <sv> --mb 150 [--area b|--heute [--als <Zauber>]|--tq1b|--merge|--only-open]` (~10 min).
- Arbeitsstand ohne Veröffentlichung: in Zweig pushen (Push auf main mit TOC-Sprung = Release). Zweig löschen geht nicht (403); arbeit-0.9.87 = main.
- Testmeldungen nie mit Cache-Schlüssel/CharKey (T158 Namen). Zeitmessungen offline unter Last unzuverlässig – allein wiederholen.
- Keine geschätzte Zahl auf dem Bildschirm. Nur Windows-1252-Zeichen. Zeiten aus `TZ=Europe/Zurich date`. Alles Sichtbare Deutsch.
