# Stand 25.11.2026 15:08 · Version 0.9.85

## Gerade in Arbeit
- Nichts. 0.9.85 veröffentlicht (Discord, Release v0.9.85, Repo c69e9a9), Bericht 2026-11-25-1508-version-0.9.85.txt – zur Prüfung.
- 0.9.84 vom Supervisor 14:48 angenommen (Abnahme im Spiel offen). 0.9.85: SHARED-T4 (GoldSentinelTest v4), PS-I8 T269 (Auswahl in
  TD.Candidates je Sammlung+Gold gemerkt, TD.ForgetChoice für Tests).
- 0.9.84: PS-UMG1 (Hintergrund 30–37 ms ab 60 % der Bilder eines Schritts, Ladebildschirm, Speicherbereinigung -> HINWEIS über Perf(); T298).

## Nächste Schritte (Reihenfolge)
1. PS-TQ1 MITTEL (Entscheid Nutzer 25.11. 13:47 "echten Weg verfolgen"): Trefferquote je Weg – entzaubert (auch nach Versand an eigenen
   Charakter; Wert der Materialien >= Kosten), AH verkauft (wie bisher), Zwischenprodukt zählt nicht (Kosten ins Endprodukt), Skillpunkt-Fälle
   zählen mit, Weg unbekannt nach 7 Tagen = offen. Daten aus AHSentinel (SK1-l Ketten, Entzauber-Verlauf; nur lesen, API.lua). Alte 186:
   neu bewerten oder mit Sicherung zurücksetzen, Zahlen vorher/nachher. Tests a–e + Gegenprobe. Erst Nachbau mit echten Daten.
   STAND: alte 186 nicht neu bewertbar (nur Summen in pmHits) -> Sicherung + zurücksetzen. Weg a) braucht AHSentinel-API (Vorschlag
   API.Disenchanted(itemID, since), im Bericht 15:08 an die Prüf-Sitzung) – bis dahin b), c), e) vorbereiten.
2. Gilden-Rezepte ohne Realm (Guild.lua; Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
3. MITTEL 2 (T192 Zwischenspeicher 2×, T259), MITTEL 4 (Prüfliste TR, T285).
4. Entwickler-Befehle nur im Entwicklermodus; Hinweis "Test ändert nie Livedaten"; Testort-Hinweis; Lesbarkeit L1–L8.
5. Taschen-Rezepte zeigen "AH ~Preis" – prüfen gegen Direktive "keine geschätzte Zahl".

## Offen beim Nutzer
- Ingametest 0.9.85 "/ps testroutine alles" (darf im Hintergrund laufen). Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

## Entscheide des Nutzers seit letztem Stand
- 25.11. 13:47 (über Supervisor, PS-TQ1): Trefferquote "echten Weg verfolgen" – siehe Schritt 3.
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
- Testmeldungen nie mit Cache-Schlüssel/CharKey (T158 Namen). Zeitmessungen offline unter Last unzuverlässig – allein wiederholen.
- Keine geschätzte Zahl auf dem Bildschirm. Nur Windows-1252-Zeichen. Zeiten aus `TZ=Europe/Zurich date`. Alles Sichtbare Deutsch.
