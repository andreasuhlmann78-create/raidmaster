# Stand 26.11.2026 12:14 · Version 0.9.90

## Gerade in Arbeit
- Nichts. 0.9.90 veröffentlicht (Discord, Release v0.9.90, Repo 72ac6e2), Bericht 2026-11-26-1212-version-0.9.90.txt – zur Prüfung.
- 0.9.90 = Gilde: Mitglied mit/ohne Realm einmal (GU Index); PS-P1 Teil 2 Schritt 1: fremde Aufrufe im längsten Stück (J.PieceCall
  aus PriceSource CallRaw, Bericht "[fremd x ms: …; eigener Code y ms]"). Rückfrage 0.9.89 beantwortet: PS liest keine AHS-Daten je Figur.
- 0.9.89 angenommen (26.11. 10:32); Merge im Spiel belegt (Laptop 11:16 charsMerged 2).

## Nächste Schritte (Reihenfolge)
1. PS-P1 Teil 2 Schritt 2 (0.9.91): Diagnose-Export nach dem nächsten Einloggen lesen (goldsentinel-daten, Zeile "Hintergrund-Aufgaben":
   Wollcape 20 ms = fremd oder eigener Code). Eigener Code -> Rezeptpreis teilen (Abgabe zwischen Zutaten, nur in der Aufgabe; --lua51);
   fremd -> Befund an AHSentinel über Bericht. Nachbau stellt die 20 ms nicht nach (Wollcape <= 2 ms, auch --als 2402).
   Danach Ansicht recipes im Nachbau (2 Bilder ~405 ms, Stapel 20x ohne Addon-Zeile = Verdacht Mock).
2. AHS-BP1 für PS: gebundene Ware (bindType 1) nicht als AH-Ware empfehlen; Test bindType 1/0/2 + Gegenprobe. Daten nicht ändern.
3. PS-TQ1 Abnahme a) mit echten Daten, sobald Herstellen+Entzaubern im Spiel (Bericht "Trefferquote je Beruf").
4. Gilden-Sync-Tag ohne Realm prüfen (Lesen GU.FindGuild 0.9.89, Mitglieder einmal 0.9.90 – umgesetzt, zur Prüfung).
5. MITTEL 2 (T192, T259), MITTEL 4 (T285); Entwickler-Befehle nur im Entwicklermodus; Testort-Hinweis; Lesbarkeit L1–L8; "AH ~Preis".

## Offen beim Nutzer
- Ingametest 0.9.90 "/ps testroutine alles" (darf im Hintergrund laufen); schon einmal Einloggen reicht für die Wollcape-Zerlegung (darf im Hintergrund laufen). Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

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
