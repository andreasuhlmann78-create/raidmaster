# Aufträge der Prüf-Sitzung

Hier legt die Prüf-Sitzung alle Anweisungen, Korrekturen und Hinweise für die Addon-Projekte ab.
Ein Ordner pro Addon: `RaidMaster/`, `ThreatSentinel/`, `AHSentinel/`, `BuffSentinel/`, `GuildSentinel/`,
`ProfessionSentinel/`, `LevelPilot/`, `Discord/`.

## Für jedes Projekt, vor jeder Arbeit

1. `git pull --rebase` im raidmaster-Repo.
2. Alle Dateien im eigenen Ordner lesen. Jede Datei nennt oben ihren Stand (Datum, Uhrzeit).
   - `offen-<addon>.txt` ist immer vollständig: Sie enthält alles, was noch offen ist. Ältere Korrekturen sind darin enthalten.
   - `testroutine-<addon>.txt` und `nachtrag-testroutinen.txt` beschreiben die Testroutine.
   - Weitere Dateien (`anweisung-…`, `hinweis-…`, `abgleich-…`) gelten zusätzlich.
3. Umsetzen wie immer: komplette Dateien, alte Clients nie brechen, vor dem Push
   `python3 addon-check/addon_check.py download/<Addon>-<Version>.zip` -> kein FEHLER.
4. Ist ein Befund falsch, dem Nutzer begründet zurückmelden.

## Regeln für diesen Ordner

- Nur die Prüf-Sitzung ändert, ergänzt oder entfernt Dateien hier. Die Projekte lesen nur.
- Ist ein Punkt in einer veröffentlichten Version nachgeprüft, entfernt die Prüf-Sitzung ihn bzw. die Datei.
- Neue oder geänderte Aufträge erkennt man am Git-Log: `git log --oneline -- auftraege/<Addon>/`.
- Das Repo ist öffentlich: Hier stehen nie Tokens, Webhook-URLs, Passwörter oder Namen von Spielern.

## Ergebnisse immer hier (Entscheid des Nutzers, 12.11.2026)

Für alle Prüf-Sitzungen: Jedes Prüfergebnis (auch "freigegeben, keine Befunde") steht in
`<Projekt>/offen-<projekt>.txt`. Nur was hier steht, gilt als an das Projekt weitergeleitet; die Nachricht an den
Nutzer ist zusätzlich. Bot und Gilden-Discord: `Discord/`. Uploader: `RaidMaster/`.
Keine Überschneidungen: vorher `git pull --rebase`, in `nachrichten-log.txt` (und `addon-check/nachpruefung-stand.json`)
nachsehen, ob es schon erledigt bzw. die Nachricht schon raus ist; sonst Zeile anhängen, pushen, dann schicken.

## Regelmässig nachsehen (12.11.2026)

Projekt-Sitzungen prüfen `auftraege/<Projekt>/` bei jeder neuen Nachricht des Nutzers, während längerer Arbeit
spätestens alle 15 Minuten und direkt vor jedem Push (Einzelheiten in CLAUDE.md).

## Jeder Befund bekommt einen bleibenden Test (Entscheid des Nutzers, 13.11.2026)

"Ich will, dass solche Fehler nicht wieder passieren." Gilt für alle Projekte und alle Prüf-Sitzungen:
- Jeder Befund (z. B. AB4c, SM1) wird mit einem **Regressionstest** behoben, der den echten Fall mit den echten Zahlen
  nachstellt (Name `T-<Befund-ID>`). Der Test muss vor der Korrektur scheitern und danach bestehen; er bleibt für immer.
- **Nachprüfung:** Befund ohne passenden Test, oder Test nur als Skip = **nicht erledigt** (bleibt offen, Schwere wie vorher).
- Tests prüfen nicht nur Funktionen einzeln, sondern **Abläufe wie ein Spieler** (klicken, tippen, Daten kommen später)
  und **echte Marktlagen** (Aufkauf, Flut, dünner Markt, alte Preise). Einzelheiten je Addon in `<Addon>/testroutine-*.txt`
  bzw. für AHSentinel in `AHSentinel/anweisung-tests-umfassend.txt`.


## Projekte prüfen sich nicht selbst (Entscheid des Nutzers, 13.11.2026, 22:28)
Berichte melden "umgesetzt, zur Prüfung" mit Belegen und gefundene Fehler – nie "erledigt/freigegeben/bestanden".
Erledigt setzt nur die Prüf-Sitzung in `offen-*.txt`, nach ihrer eigenen Prüfung.

## Prioritäten-Liste zuoberst (Entscheid des Nutzers 14.11. 00:15: "reihe alle Themen bzw. Änderungen immer nach Prio ins Repo")
Jede offen-*.txt beginnt mit dem Block "PRIORITÄTEN – vollständige Reihenfolge": alle offenen Punkte mit Kürzel und
Schwere, von oben nach unten abzuarbeiten. Die Prüf-Sitzung führt ihn bei JEDER Änderung nach (neuer Punkt, erledigt,
umsortiert). Projekte arbeiten strikt in dieser Reihenfolge.


GRUNDSATZ (Entscheid des Nutzers 14.11.2026 11:24, gilt IMMER und für alle Projekte): Alles, was eingebaut wird, wird streng
geprüft. Jede neue Funktion kommt mit (1) Test in der Testroutine (auch absichtlich falsche Fälle), (2) Selbstkontrolle im
Spiel, wo messbar (passiv gegen echte Ereignisse, Ergebnis im Testbericht), (3) Prüfung durch den Supervisor. Fehlt einer der
drei Punkte im Bericht, gilt der Auftrag als nicht umgesetzt.
