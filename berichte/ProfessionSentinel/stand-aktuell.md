# Stand 25.11.2026 09:04 · Version 0.9.83

## Gerade in Arbeit
- Nichts. 0.9.83 vom Supervisor 20:09 angenommen (PS-I5-a erledigt; im Ingametest zu zeigen: T297 "behalten" > 0).
- 0.9.82 vom Supervisor 18:34 angenommen (im Spiel zu zeigen). 0.9.83: PS-I5-a (verschiedene Funktionen = verschieden, Alarm-Zeilen
  mit fester Funktion UI.AlarmRowClick, onClick/onRightClick bekommen die Zeilendaten), T219 gapHold bei zurückgesprungener Uhr,
  T269-Übernahme genauer geprüft.

## Nächste Schritte (Reihenfolge)
1. Ingametest 0.9.83 lesen (goldsentinel-daten, ProfessionSentinel.lua.gz, ["last"]): PS-I1 je Fall (Etikett + "gehalten"-Stelle),
   T255 (GC 135 MB im Teil), T189 59 ms, T140/T219 knapp über 16 ms, T85.
2. PS-UMG1 (Umgebung/Bedienung erkennen) VORGEZOGEN: Ingametests laufen immer im Hintergrund (Entscheid Nutzer 25.11. 09:03).
   Ohne UMG1 meldet jeder Ingametest Zeitüberschreitungen aus dem Hintergrund als FEHLER. Klarstellung 20:50 beachten
   (HINWEIS nur bei Hintergrund-Zeitraum, Ladebildschirm, Speicherbereinigung im Bild; "Rest grösser" allein nie).
3. PS-I8: T269 Aufruf <= 2 ms (TD.Candidates rechnet Taschen/Gold je Aufruf neu) umsetzen. T139 19,8 ms / "Aufgabe heute" 23,3 ms
   nur ändern, wenn der Nachbau sie nachstellt (Supervisor 20:01: Ingametest 0.9.81 lief im Hintergrund, Bild in Ruhe 33 ms).
4. Trefferquote (PM6) nach Entscheid des Nutzers (A/B/C).
5. Gilden-Rezepte ohne Realm (Guild.lua; Sicherung, Zahlen vorher/nachher, Sync-Tag ohne Realm).
6. MITTEL 2 (T192 Zwischenspeicher 2×, T259), MITTEL 4 (Prüfliste TR, T285).
7. Entwickler-Befehle nur im Entwicklermodus; Hinweis "Test ändert nie Livedaten"; Testort-Hinweis; Lesbarkeit L1–L8.
8. Taschen-Rezepte zeigen "AH ~Preis" – prüfen gegen Direktive "keine geschätzte Zahl".

## Offen beim Nutzer
- ENTSCHEID Trefferquote (Schneiderei 0/186 zählt Skill-/Zwischenprodukte als Fehlschlag): A nicht verkauft = nicht zählen ·
  B nur Herstellungen ohne Skillpunkt · C wie bisher.
- Frage: welches Berufsfenster war bei T85 offen (0.9.80 Krieger ohne Beruf, 0.9.81 Priester mit VZ/Schneiderei/Kochen)?
- Ingametest 0.9.83 "/ps testroutine alles" (läuft im Hintergrund, siehe Entscheid 25.11. 09:03). Messung Lua-Fehler SetCraftableCount (nur PS / nur AHS).

## Entscheide des Nutzers seit letztem Stand
- 25.11. 09:03: "ich lasse das wow fenster nicht offen ich bin am arbeiten" – Ingametests laufen im Hintergrund; kein Test darf
  Vordergrund voraussetzen. Folge: PS-UMG1 vorgezogen.
- Weiter gültig: 23.11. 11:36 announce/ nichts löschen; 12:03 keine alten Versionen neu posten; 07:50 Nutzung sparen; 08:13 diese
  Datei; Supervisor 23.11.: Skillweg-Sortierung eigene Liste, gelb/grün "n Punkte"/"mindestens" ohne "~", Formel-Chance intern, PS-TAKT3.

## Wichtig zu wissen
- Repos: /home/claude/professionsentinel (Remote andreasuhlmann78-create/ProfessionSentinel; Push mit TOC-Sprung baut Release;
  Prüfung `git ls-remote origin refs/heads/main`), /home/claude/raidmaster (öffentlich; auftraege/ nur Supervisor).
- Ingametest-Bericht: goldsentinel-daten/aktuell/AUSPLUSLAPTOP/forever/<konto>/ProfessionSentinel.lua.gz, Zeile ["last"] (unicode_escape).
- Release-Asset: `gh api repos/<R>/releases/tags/vX --jq '.assets[0].id'`, dann mit Accept octet-stream laden.
- Veröffentlichen: download/ProfessionSentinel-<V>.zip (alte entfernen), announce/…-<V>.md + <V>.ProfessionSentinel.zip NEU dazu. addon_check vorher.
- Nachbau echt: `tests/nachbau_echt.py ProfessionSentinel /home/claude/ahanalyzerpro <sv> --mb 150 --area b` (~10 min); --profile zu langsam.
  Offline-Profil je Fall: scratchpad prof.py (debug.sethook, nur während des Falls).
- Zeitmessungen offline unter Last unzuverlässig – allein wiederholen. Smoketest ~20 min, FEHLER 29/26/26 = Mock-Grenzen.
- Keine geschätzte Zahl auf dem Bildschirm. Nur Windows-1252-Zeichen. Zeiten aus `TZ=Europe/Zurich date`. Alles Sichtbare Deutsch.
