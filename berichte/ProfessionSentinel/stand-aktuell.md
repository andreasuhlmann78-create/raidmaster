# Stand 28.11.2026 05:16 · Version 0.9.99 (announce), 0.9.98 (download)

## Gerade in Arbeit
- 0.9.99 NUR announce/ (Release v0.9.99, Repo 9939fd5), Bericht 2026-11-28-0516-version-0.9.99.txt – zur Prüfung: PS-P3 (PS.OnMerchant,
  vergessen nur bei Goldänderung), PS-SK2-b (Lehrer-Zeile immer "ohne Lernstufe z: Namen").
- PS-SK2 im Spiel sichtbar behoben (Supervisor 05:05). download/ = 0.9.98.

## Nächste Schritte (Reihenfolge)
1. Tooltip/Anzeige (Supervisor 28.11.): PS-TT-RECH (Verkaufen − Material ≠ "lohnt sich": Abzüge in einer Zeile nennen; Spinnenseidenstiefel,
   Graue Wollrobe), PS-TT-EINH ("je Herstellung" -> "je Skillpunkt"), Einheit /Herst. vs /Pkt in Leveln-Liste vereinheitlichen, "Jetzt"-Text
   nicht abschneiden.
2. PS-AHS-EIG1 MITTEL: Sniper-Ziele mit Zweck "eigenbedarf" sobald AHS das Feld kennt; Chat "im Sniper noch das Budget einstellen" belegen/
   anpassen; vor dem Anlegen die Summe nennen.
3. Neue Version erst nach "ANGENOMMEN" nach download/ (DL-ABN).
4. PS-TQ1 Abnahme a) mit echten Daten; Gilden-Sync-Tag ohne Realm; MITTEL 2/4; Entwickler-Befehle; Lesbarkeit L1–L8; "AH ~Preis".

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
