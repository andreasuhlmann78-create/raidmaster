# Stand 28.11.2026 08:19 · Version 0.9.101 (announce), 0.9.100 (download)

## Gerade in Arbeit
- 0.9.101 NUR announce/ (Release v0.9.101, Repo ef0416f, md5 a8594018…), Bericht 2026-11-28-0819-version-0.9.101.txt – zur Prüfung:
  Einzel-Einkauf Eigenbedarf (Entscheid 06:43), PS-PERF-TSU1 (Protokoll: seit/diese Sitzung, Summe getrennt vom längsten Bild; Sturm-Lesart
  widerlegt, Senken erst nach Messung), PS-UI-OVL1, PS-UI-REZ1 (368 = Rezept-Alarm), PS-GOLD-WID; PS-LVL-EINH begründet.
- 0.9.100 nach download/ (PS-DL frei 07:20, md5 573df5a7…), 0.9.99 entfernt. PS-P3, PS-SK2-b im Spiel bestanden, erledigt.

## Nächste Schritte (Reihenfolge)
1. Antwort Supervisor zu 0.9.101; Vorschlag Lehrername je Besuch (Magiestoffballen "lernbar bei …") wartet auf Supervisor.
2. PS-PERF-TSU1 b): nach dem nächsten Protokoll ("diese Sitzung k") entscheiden, ob Aufbauten ohne Änderung wegfallen.
3. PS-TQ1 Abnahme a) mit echten Daten; Gilden-Sync-Tag ohne Realm; MITTEL 2/4; Entwickler-Befehle; Lesbarkeit L1–L8; "AH ~Preis".
4. Neue Version erst nach "ANGENOMMEN"/"PS-DL frei" nach download/ (DL-ABN).

## Offen beim Nutzer
- Ingametest 0.9.101: Plan-Kopf/Fusszeile ohne Überlappung, Filterzeile Rezepte, Reiter "Rezepte !n", Flut-Tooltip; /reload + 2 Min. Berufsfenster -> /ps protokoll (AUFBAU "diese Sitzung k").
- Offen aus 0.9.100: Klick Sniper -> AHS-Hinweis "Eigenbedarf" ohne Verlust-Warnung.
- Messung im Spiel (AHS-BP1): Tooltip der Gifte/Blendungspulver "Wird beim Aufheben gebunden"?
- Schneiderlehrer + Experten-Lehrer Schneiderei öffnen (Filter alle) -> Protokoll "Lernstufen gelesen n (neu, geändert); im Plan ohne Lernstufe z". (darf im Hintergrund laufen). Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

## Entscheide des Nutzers seit letztem Stand
- 28.11. 06:43 (über Supervisor): Einzel-Einkauf aus der Rezeptansicht = Eigenbedarf (umgesetzt 0.9.101).
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
