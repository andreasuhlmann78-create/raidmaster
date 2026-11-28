# Stand 28.11.2026 04:29 · Version 0.9.98 (announce + download)

## Gerade in Arbeit
- Nichts. 0.9.98 angenommen (28.11. 04:35) und nach download/ gelegt (gleiche Zip wie announce/, md5 dbe05b13…), 0.9.93 entfernt.
- Offen im Spiel: PS-SK2 (Schneider- + Experten-Lehrer, Tooltip Magiestoffballen), PS-P2-Abnahme (WorthUpTo je Lauf, Vergessen mit Grund).

## Nächste Schritte (Reihenfolge)
1. Neue Version erst nach "ANGENOMMEN" nach download/ (DL-ABN).
2. Ansicht recipes im Nachbau (2 Bilder ~405 ms, Stapel 20x ohne Addon-Zeile = Verdacht Mock) belegen.
3. PS-TQ1 Abnahme a) mit echten Daten, sobald Herstellen+Entzaubern im Spiel (Bericht "Trefferquote je Beruf").
4. Gilden-Sync-Tag ohne Realm prüfen.
5. MITTEL 2 (T192, T259), MITTEL 4 (T285); Entwickler-Befehle nur im Entwicklermodus; Testort-Hinweis; Lesbarkeit L1–L8; "AH ~Preis".

## Offen beim Nutzer
- Ingametest 0.9.95 (Schneider-Figur, Berufsfenster offen, /ps protokoll): "WorthUpTo je Lauf" ab Lauf 2 "0 neu", "WorthUpTo vergessen" mit Grund.
- Messung im Spiel (AHS-BP1): Tooltip der Gifte/Blendungspulver "Wird beim Aufheben gebunden"?
- Schneiderlehrer + Experten-Lehrer Schneiderei öffnen (Filter alle) -> Protokoll "Lernstufen gelesen n (neu, geändert); im Plan ohne Lernstufe z". (darf im Hintergrund laufen). Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

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
