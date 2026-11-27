# Stand 27.11.2026 11:34 · Version 0.9.94 (announce), 0.9.93 (download)

## Gerade in Arbeit
- Nichts. 0.9.94 NUR announce/ (Release v0.9.94, Repo a15097a), Bericht 2026-11-27-1134-version-0.9.94.txt – zur Prüfung:
  Zähler je Lauf "heute" (TD.runs, Protokoll "WorthUpTo je Lauf").
- 0.9.93 angenommen (11:15) und nach download/ gelegt (md5 4b0c22a4…), 0.9.92 entfernt.

## Nächste Schritte (Reihenfolge)
1. Nach "ANGENOMMEN 0.9.94": dieselbe Zip nach download/ (md5 im Bericht), 0.9.93 entfernen, Workflow grün.
2. Ansicht recipes im Nachbau (2 Bilder ~405 ms, Stapel 20x ohne Addon-Zeile = Verdacht Mock) belegen.
3. PS-TQ1 Abnahme a) mit echten Daten, sobald Herstellen+Entzaubern im Spiel (Bericht "Trefferquote je Beruf").
4. Gilden-Sync-Tag ohne Realm prüfen.
5. MITTEL 2 (T192, T259), MITTEL 4 (T285); Entwickler-Befehle nur im Entwicklermodus; Testort-Hinweis; Lesbarkeit L1–L8; "AH ~Preis".

## Offen beim Nutzer
- Ingametest 0.9.94 "/ps testroutine alles" (darf im Hintergrund laufen); /ps protokoll -> "WorthUpTo je Lauf" (Lauf 2: 0 neu).
- Messung im Spiel (AHS-BP1): Tooltip der Gifte/Blendungspulver "Wird beim Aufheben gebunden"? (darf im Hintergrund laufen). Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

## Entscheide des Nutzers seit letztem Stand
- 25.11. 13:47 (über Supervisor, PS-TQ1): Trefferquote "echten Weg verfolgen" (umgesetzt 0.9.86).
- 27.11. 08:27–09:23 (über Supervisor, ST1): nur nützliche Spieler-Texte; Testmodus behält alles.
- 25.11. 16:38: Antworten an den Nutzer immer Deutsch (erinnert).
- 25.11. 09:03: Ingametests laufen im Hintergrund ("ich lasse das wow fenster nicht offen ich bin am arbeiten") -> UMG1 vorgezogen (umgesetzt 0.9.84).
- Weiter gültig: 23.11. 11:36 announce/ nichts löschen; 12:03 keine alten Versionen neu posten; 07:50 Nutzung sparen; 08:13 diese
  Datei; Supervisor 23.11.: Skillweg-Sortierung eigene Liste, gelb/grün "n Punkte"/"mindestens" ohne "~", Formel-Chance intern, PS-TAKT3.

## Wichtig zu wissen
- Repos: /home/claude/professionsentinel (Remote andreasuhlmann78-create/ProfessionSentinel; Push mit TOC-Sprung baut Release;
  Prüfung `git ls-remote origin refs/heads/main`), /home/claude/raidmaster (öffentlich; auftraege/ nur Supervisor).
- Ingametest-Bericht: goldsentinel-daten/aktuell/<PC>/forever/<konto>/ProfessionSentinel.lua.gz, Zeile ["last"] (unicode_escape).
- Release-Asset: `gh api repos/<R>/releases/tags/vX --jq '.assets[0].id'`, dann mit Accept octet-stream laden.
- Veröffentlichen (DL-ABN 27.11. 10:30, HOCH): neue Version NUR announce/…-<V>.md + <V>.ProfessionSentinel.zip. download/ erst, wenn in
  offen-professionsentinel.txt "ANGENOMMEN" für genau diese Version steht: gleiche Zip (md5), alte entfernen, Workflow Addon-Prüfung grün.
- Nachbau echt: `tests/nachbau_echt.py ProfessionSentinel /home/claude/ahanalyzerpro <sv> --mb 150 [--area b|--heute [--als <Zauber>]|--tq1b|--merge|--only-open]` (~10 min).
- Arbeitsstand ohne Veröffentlichung: in Zweig pushen (Push auf main mit TOC-Sprung = Release). Zweig löschen geht nicht (403); arbeit-0.9.87 = main.
- Testmeldungen nie mit Cache-Schlüssel/CharKey (T158 Namen). Zeitmessungen offline unter Last unzuverlässig – allein wiederholen.
- Keine geschätzte Zahl auf dem Bildschirm. Nur Windows-1252-Zeichen. Zeiten aus `TZ=Europe/Zurich date`. Alles Sichtbare Deutsch.
