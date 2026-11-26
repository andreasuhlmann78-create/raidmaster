# Stand 26.11.2026 09:04 · Version 0.9.88

## Gerade in Arbeit
- Nichts. 0.9.88 veröffentlicht (Discord, Release v0.9.88, Repo 222360f), Bericht 2026-11-26-0904-version-0.9.88.txt – zur Prüfung.
- 0.9.88 = PS-RD1 (Rezeptdaten-Entwurf 26.11. übernommen) + PS-TQ1-b (pending offen lassen, nach "ledger" neu fragen, MK.CheckLater:
  Login / MAIL_CLOSED / ledger, höchstens alle 60 s, Aufgabe "treffer") + Namenkarte MK.ItemByName (50 Rechnungen 7,15 -> 0,41 ms).
- 0.9.87 angenommen (Supervisor 25.11. 18:18). Arbeitszweige arbeit-0.9.87/-0.9.88 = Stand von main (löschen nicht erlaubt, 403).

## Nächste Schritte (Reihenfolge)
1. PS-P1 Teil 2 (0.9.89): Beleg aus dem Spiel 26.11. 06:50 (0.9.87): "heute" Teil 22,7 ms = 5 Rezeptpreise 22,6 ms, längstes 18,3 ms Wollcape,
   übrig 0,2, Speicher +1,1 MB, 35 Bilder/s. -> einen Rezeptpreis teilbar machen (Abgabe zwischen Zutaten, nur in der Aufgabe; Lua 5.1
   kein yield über pcall: --lua51). Nachbau sv4: Teil "übrig 16,2 ms" bei 1 Rezept (Figur 49 Rezepte, erster Teil) belegen.
   Danach Ansicht recipes im Nachbau (2 Bilder ~405 ms, Stapel 20x ohne Addon-Zeile = Verdacht Mock).
2. AHS-BP1 für PS: gebundene Ware (bindType 1) nicht als AH-Ware empfehlen; Test bindType 1/0/2 + Gegenprobe. Daten nicht ändern.
3. PS-TQ1 Abnahme a) mit echten Daten, sobald Herstellen+Entzaubern im Spiel (Bericht "Trefferquote je Beruf").
4. Gilden-Rezepte ohne Realm (Guild.lua; Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
5. MITTEL 2 (T192, T259), MITTEL 4 (T285); Entwickler-Befehle nur im Entwicklermodus; Testort-Hinweis; Lesbarkeit L1–L8; "AH ~Preis".

## Offen beim Nutzer
- Ingametest 0.9.88 "/ps testroutine alles" (darf im Hintergrund laufen) (darf im Hintergrund laufen). Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

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
- Nachbau echt: `tests/nachbau_echt.py ProfessionSentinel /home/claude/ahanalyzerpro <sv> --mb 150 [--area b|--heute|--tq1b|--only-open]` (~10 min).
- Arbeitsstand ohne Veröffentlichung: in Zweig pushen (Push auf main mit TOC-Sprung = Release). Zweig löschen geht nicht (403); arbeit-0.9.87 = main.
- Testmeldungen nie mit Cache-Schlüssel/CharKey (T158 Namen). Zeitmessungen offline unter Last unzuverlässig – allein wiederholen.
- Keine geschätzte Zahl auf dem Bildschirm. Nur Windows-1252-Zeichen. Zeiten aus `TZ=Europe/Zurich date`. Alles Sichtbare Deutsch.
