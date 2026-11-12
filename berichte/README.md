# Berichte an die Prüf-Sitzung

Entscheid des Nutzers, 12.11.2026: Alle Projekt-Sitzungen und alle anderen Prüf-Sitzungen (z. B. die geplante
Nachprüfung) erstatten der Prüf-Sitzung Bericht – über dieses Repo, in diesem Ordner.
`auftraege/` ist der Weg Prüf-Sitzung -> Projekte, `berichte/` der Weg Projekte -> Prüf-Sitzung.

## Wann

- nach jeder Veröffentlichung (neue Version),
- wenn Aufträge umgesetzt, teilweise umgesetzt oder abgelehnt wurden,
- wenn ein Befund falsch ist (mit Begründung),
- bei Fragen an die Prüf-Sitzung oder wenn etwas blockiert,
- die geplante Nachprüfung: nach jedem Lauf mit Ergebnis (auch "keine neuen Versionen" nur, wenn sich etwas geändert hat).

## Wie

Eine Datei je Bericht: `berichte/<Projekt>/<JJJJ-MM-TT>-<HHMM>-<kurzes-thema>.txt`
(Projekt wie in `auftraege/`, dazu `Nachpruefung/` für die geplante Nachprüfung).

Inhalt (kurz, Deutsch):
```
BERICHT <PROJEKT> AN DIE PRÜF-SITZUNG
Stand: <Datum Uhrzeit> · Sitzung: <Projekt-Sitzung / Nachprüfung> · Version: <x.y.z> · Commit: <hash>
ERLEDIGT: <Punkt-IDs aus offen-*.txt, je eine Zeile, mit Datei:Zeile>
TEILWEISE / OFFEN: <Punkt-ID – warum>
BEFUND FALSCH: <Punkt-ID – Begründung>
FRAGEN: <...>
IM CLIENT GETESTET: <Ergebnis, falls vorhanden>
```

## Regeln

- Nur in den eigenen Unterordner schreiben, Berichte anderer nie ändern oder löschen.
- Vorher `git pull --rebase`, danach committen und pushen.
- Repo ist öffentlich: keine Tokens, Links, Server-IDs, Spielernamen.
- Die Prüf-Sitzung liest `berichte/` bei jeder Arbeit (git log --oneline -- berichte/) und übernimmt das Ergebnis in
  `auftraege/<Projekt>/offen-*.txt`. Gelesene Berichte bleiben liegen (Verlauf); aufräumen nur die Prüf-Sitzung.
